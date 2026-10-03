"""Divisão da migração da terceira via entre Flávio e Lula, por três fontes.

1. Série nacional: inclinações da regressão de efeitos fixos de casa nos
   válidos; a fração de Flávio é a parte dele no ganho conjunto dos dois, que
   nos válidos é exatamente a queda da terceira via.
2. Declarada pelo eleitor: matriz 1º × 2º turno do eleitorado de cada
   candidatura de terceira via e segunda opção de quem pode mudar (Nexus
   28/09 e Datafolha 01/10), transcritas com página em
   `analysis/predicao_2026/tendencia/migracao_declarada.json`.
3. Estaduais: duas ou mais ondas da mesma casa na mesma UF; variação dos
   válidos entre ondas, agregada pelo eleitorado, com erro amostral.

Nenhum número é digitado aqui: tudo sai dos arquivos citados em cada bloco.
"""

from __future__ import annotations

import json
from datetime import date
from itertools import pairwise

import numpy as np
from scipy.stats import chi2, norm

from . import tendencia
from .recencia import midpoint
from .tse import ROOT, sha

DECLARED = ROOT / "analysis/predicao_2026/tendencia/migracao_declarada.json"
LABELS = ROOT / "analysis/predicao_2026/tendencia/estaduais_rotulos.json"
TSE = ROOT / "data/outputs/predicao_2026/tse.json"
AGGREGATOR = ROOT / "docs/assets/reponderacao_pnad.json"
DEFF = 1.5
THIRD = ("cury", "caiado", "renan", "zema", "samara")
MONTHS = {"Ago": 8, "Set": 9, "Out": 10}
GROUPS = {
    "Brasil": None,
    "Nordeste": ("Nordeste",),
    "Sul e Sudeste": ("Sul", "Sudeste"),
    "Norte e Centro-Oeste": ("Norte", "Centro-Oeste"),
}
NOT_THIRD = {"Lula", "Flávio", "Indecisos", "Branco/nulo"}


def _read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _share(gain_f, gain_l, var_f, var_l, cov):
    """F / (F + L) com erro-padrão pelo método delta."""
    total = gain_f + gain_l
    if total <= 0:
        return None, None
    grad = np.array([gain_l, -gain_f]) / total**2
    cov2 = np.array([[var_f, cov], [cov, var_l]])
    return gain_f / total, float(np.sqrt(max(grad @ cov2 @ grad, 0)))


# 1. Série nacional ------------------------------------------------------


def national_series(polls, today):
    out = {}
    for kind in ("previsao_vetor", "publicado_vetor"):
        for days in (28, 14):
            r = tendencia.fe_regression(polls, today, days, kind)
            c = r["categorias"]
            out[f"{kind}_{days}d"] = {
                "fracao_flavio": r["fracao_flavio_do_ganho"],
                "dp": r["fracao_flavio_dp"],
                "inclinacoes_pp_dia": {
                    k: c[k]["inclinacao_pp_dia"] for k in ("lula", "flavio", "outros")
                },
                "ep_pp_dia": {k: c[k]["ep"] for k in ("lula", "flavio", "outros")},
                "n_ondas": r["n_ondas"],
                "graus_liberdade": r["graus_liberdade"],
            }
    # Sensibilidade da janela curta à data que define a entrada da onda.
    rules = {}
    for rule in tendencia.WINDOW_RULES:
        r = tendencia.fe_regression(polls, today, 14, rule=rule)
        rules[rule] = {
            "n_ondas": r["n_ondas"],
            "graus_liberdade": r["graus_liberdade"],
            "fracao_flavio": r["fracao_flavio_do_ganho"],
            "dp": r["fracao_flavio_dp"],
            "inclinacoes_pp_dia": {
                k: r["categorias"][k]["inclinacao_pp_dia"]
                for k in ("lula", "flavio", "outros")
            },
            "ep_pp_dia": {
                k: r["categorias"][k]["ep"] for k in ("lula", "flavio", "outros")
            },
        }
    return {
        "janela_14d_por_regra": rules,
        "fonte": "docs/assets/reponderacao_pnad.json, via base.national (ondas nacionais da janela, ponto médio do campo)",
        "metodo": "MQP com efeito fixo de casa e tendência linear nos válidos; fração de Flávio = inclinação de Flávio / (inclinação de Flávio + inclinação de Lula); erro-padrão pelo método delta com a covariância residual conjunta",
        "estimativas": out,
        "principal": "previsao_vetor_28d",
    }


# 2. Declarada pelo eleitor ---------------------------------------------


def _matrix_split(src, weights_key):
    """Média ponderada de F/(F+L) entre eleitorados de terceira via."""
    m = src["matriz_2t"]["linhas"]
    first = src["primeiro_turno"]["valores"]
    n = src["n"]
    rows, f_mass, l_mass, var = [], 0.0, 0.0, []
    for c, row in m.items():
        share = first[c]
        if weights_key == "pode_mudar":
            mobile = src.get("pode_mudar_por_candidato", {}).get("valores", {}).get(c)
            if mobile is None:
                decided = src["decididos_por_candidato"]["valores"].get(c)
                if decided is None:
                    continue
                mobile = 100 - decided
            w = share * mobile / 100
        else:
            w = share
        f, lv = row["flavio"], row["lula"]
        # Respondentes do eleitorado c que escolhem um dos dois, efetivos.
        n_eff = n * share / 100 * (f + lv) / 100 / DEFF
        p = f / (f + lv)
        rows.append(
            {
                "candidatura": c,
                "peso_pp": w,
                "flavio": f,
                "lula": lv,
                "fracao_flavio": p,
            }
        )
        f_mass += w * f
        l_mass += w * lv
        var.append((w * (f + lv), p * (1 - p) / max(n_eff, 1)))
    total = sum(a for a, _ in var)
    split = f_mass / (f_mass + l_mass)
    se = float(np.sqrt(sum((a / total) ** 2 * v for a, v in var)))
    return {"fracao_flavio": split, "dp": se, "linhas": rows}


def declared():
    d = _read(DECLARED)
    out = {}
    for key, src in d["fontes"].items():
        entry = {
            "instituto": src["instituto"],
            "registro_tse": src["registro_tse"],
            "campo": src["campo"],
            "arquivo": src["arquivo"],
            "sha256_pdf": src["sha256"],
            "pagina_matriz": src["matriz_2t"]["pagina"],
            "matriz_peso_voto": _matrix_split(src, "voto"),
            "matriz_peso_quem_pode_mudar": _matrix_split(src, "pode_mudar"),
        }
        second = src["segunda_opcao"]
        f, lv = second["valores"]["flavio"], second["valores"]["lula"]
        base = second.get("base_ponderada") or (
            src["n"] * src["pode_mudar_total"]["valor"] / 100
        )
        n_eff = base * (f + lv) / 100 / DEFF
        p = f / (f + lv)
        entry["segunda_opcao"] = {
            "pagina": second["pagina"],
            "flavio": f,
            "lula": lv,
            "fracao_flavio": p,
            "dp": float(np.sqrt(p * (1 - p) / n_eff)),
            "base_aproximada": base,
            "ressalva": "Mistura eleitores de Lula, de Flávio e da terceira via que podem mudar; sem cruzamento pelo voto de 1º turno no relatório, não identifica a divisão só da terceira via.",
        }
        if "pisos_tetos_1t" in src:
            t = src["pisos_tetos_1t"]["valores"]
            entry["teto_1t"] = {
                "pagina": src["pisos_tetos_1t"]["pagina"],
                "lula": t["lula"],
                "flavio": t["flavio"],
                "ganho_teto_lula_pp": t["lula"]["teto"] - t["lula"]["voto"],
                "ganho_teto_flavio_pp": t["flavio"]["teto"] - t["flavio"]["voto"],
                "ressalva": "Números inteiros: cada ganho tem ±1 pp de arredondamento.",
            }
        if "segunda_opcao_nao_alinhados" in src:
            s2 = src["segunda_opcao_nao_alinhados"]
            entry["segunda_opcao_nao_alinhados"] = {
                "pagina": s2["pagina"],
                "flavio": s2["valores"]["flavio"],
                "lula": s2["valores"]["lula"],
                "fracao_flavio": s2["valores"]["flavio"]
                / (s2["valores"]["flavio"] + s2["valores"]["lula"]),
            }
        out[key] = entry
    return {
        "arquivo": str(DECLARED.relative_to(ROOT)),
        "sha256": sha(DECLARED),
        "ausencias": d["varredura"]["ausencias"],
        "fontes": out,
        "metodo": "Matriz: média de F/(F+L) entre os eleitorados de terceira via, ponderada pelo voto de 1º turno ou pelo voto vezes a parcela que diz poder mudar. Erro-padrão amostral com deff 1,5 e base efetiva de cada eleitorado; não inclui erro de arredondamento dos inteiros.",
    }


# 3. Estaduais -----------------------------------------------------------


def _label_date(text):
    day, month = text.split("/")
    return date(2026, MONTHS[month], int(day)).toordinal()


def _valid_from_total(lula, flavio, indecisos, blank):
    other = 100 - lula - flavio - indecisos - blank
    return lula, flavio, other


def _full_list(values):
    lula, flavio = values["Lula"], values["Flávio"]
    other = sum(
        v
        for k, v in values.items()
        if k not in NOT_THIRD and isinstance(v, (int, float))
    )
    return lula, flavio, other


def _quaest_waves(uf, labels, rule):
    path = ROOT / f"analysis/voto_util/quaest/{uf}.json"
    waves = []
    if path.exists():
        d = _read(path)
        rounds = dict(d["pres_1t"]["rodadas"])
        last = list(rounds)[-1]
        # Ondas de agosto: cenário II, sem Marçal, o mais próximo da cédula atual.
        scenario = d.get("pres_1t_cenario_ii") or {}
        rounds.update(scenario.get("rodadas", {}))
        ficha = d["ficha"]
        for label, v in rounds.items():
            if label == last:
                day, rest = ficha["campo"].split(" a ")
                end = date(*map(int, reversed(rest.split("/"))))
                begin = end.replace(day=int(day))
                mid = (begin.toordinal() + end.toordinal()) / 2
                when = "ficha"
            else:
                mid = _label_date(labels[uf][label]) - rule
                when = f"rótulo {labels[uf][label]} menos {rule} dias"
            if (
                v.get("Branco/nulo") is None
                or v.get("Indecisos") is None
                or v.get("Marçal")
            ):
                continue
            lula, flavio, other = _valid_from_total(
                v["Lula"], v["Flávio"], v["Indecisos"], v["Branco/nulo"]
            )
            waves.append(
                {
                    "casa": "Quaest",
                    "rodada": label,
                    "ponto_medio": mid,
                    "data": when,
                    "n": ficha["n"],
                    "valores": (lula, flavio, other),
                    "arquivo": str(path.relative_to(ROOT)),
                    "pagina": (
                        scenario
                        if label in scenario.get("rodadas", {})
                        else d["pres_1t"]
                    )["pagina"],
                }
            )
    for path in sorted(
        (ROOT / "analysis/predicao_2026/estaduais").glob(f"quaest_{uf}_*.json")
    ):
        d = _read(path)
        begin, end = d["campo"].split(" a ")
        mid = (
            date.fromisoformat(begin).toordinal() + date.fromisoformat(end).toordinal()
        ) / 2
        wave = {
            "casa": "Quaest",
            "rodada": end,
            "ponto_medio": mid,
            "data": "campo",
            "n": d["n"],
            "valores": _full_list(d["pres_1t"]["valores"]),
            "arquivo": str(path.relative_to(ROOT)),
            "pagina": d["pres_1t"]["pagina"],
        }
        # A mesma onda pode estar nos dois acervos: fica a lista completa.
        waves = [w for w in waves if abs(w["ponto_medio"] - mid) > 1.5]
        waves.append(wave)
    return waves


def _realtime_waves(uf):
    paths = sorted(
        (ROOT / "analysis/voto_util/outros").glob(f"realtimebigdata_{uf}_*.json")
    ) + sorted(
        (ROOT / "analysis/predicao_2026/estaduais").glob(f"realtime_{uf}_*.json")
    )
    waves = []
    for path in paths:
        d = _read(path)
        begin, end = d["campo"].split(" a ")
        waves.append(
            {
                "casa": "Real Time Big Data",
                "rodada": end,
                "ponto_medio": (
                    date.fromisoformat(begin).toordinal()
                    + date.fromisoformat(end).toordinal()
                )
                / 2,
                "data": "campo",
                "n": int(d["n"]),
                "valores": _full_list(d["pres_1t"]["valores"]),
                "arquivo": str(path.relative_to(ROOT)),
                "pagina": d["pres_1t"]["pagina"],
            }
        )
    return waves


def _variance(values, n):
    """Covariância amostral das parcelas dos válidos (fração), deff incluído."""
    v = np.asarray(values, float)
    p = v / v.sum()
    n_eff = n * v.sum() / 100 / DEFF
    return (np.diag(p) - np.outer(p, p)) / n_eff


def state_pairs():
    from .base import UF_REGION  # importação tardia: base importa este módulo

    rules = _read(LABELS)
    labels, rule = rules["rotulos"], rules["regra_ponto_medio_dias_antes_do_rotulo"]
    weights = {uf: u["eleitorado"] for uf, u in _read(TSE)["ufs"].items()}
    pairs = []
    for uf in sorted(u for u in UF_REGION if u != "ZZ"):
        for waves in (_quaest_waves(uf, labels, rule), _realtime_waves(uf)):
            waves = sorted(waves, key=lambda w: w["ponto_medio"])
            for a, b in pairwise(waves):
                pa = np.asarray(a["valores"], float)
                pb = np.asarray(b["valores"], float)
                va, vb = 100 * pa / pa.sum(), 100 * pb / pb.sum()
                cov = 1e4 * (_variance(pa, a["n"]) + _variance(pb, b["n"]))
                delta = vb - va
                pairs.append(
                    {
                        "uf": uf,
                        "regiao": UF_REGION[uf],
                        "casa": a["casa"],
                        "de": date.fromordinal(int(a["ponto_medio"])).isoformat(),
                        "para": date.fromordinal(int(b["ponto_medio"])).isoformat(),
                        "dias": b["ponto_medio"] - a["ponto_medio"],
                        "validos_antes": va.tolist(),
                        "validos_depois": vb.tolist(),
                        "variacao_pp": dict(
                            zip(
                                ("lula", "flavio", "outros"),
                                delta.tolist(),
                                strict=True,
                            )
                        ),
                        "dp_pp": dict(
                            zip(
                                ("lula", "flavio", "outros"),
                                np.sqrt(np.diag(cov)).tolist(),
                                strict=True,
                            )
                        ),
                        "cov_lula_flavio": float(cov[0, 1]),
                        "eleitorado": weights[uf],
                        "fontes": [
                            {
                                "arquivo": w["arquivo"],
                                "pagina": w["pagina"],
                                "data": w["data"],
                            }
                            for w in (a, b)
                        ],
                        "setembro": a["ponto_medio"] >= date(2026, 9, 1).toordinal(),
                    }
                )
    return pairs


def _aggregate(pairs):
    """Soma das variações ponderada pelo eleitorado (casas da mesma UF dividem o peso)."""
    count = {}
    for p in pairs:
        count[p["uf"]] = count.get(p["uf"], 0) + 1
    w = np.array([p["eleitorado"] / count[p["uf"]] for p in pairs], float)
    w = w / w.sum()
    dl = np.array([p["variacao_pp"]["lula"] for p in pairs])
    df = np.array([p["variacao_pp"]["flavio"] for p in pairs])
    do = np.array([p["variacao_pp"]["outros"] for p in pairs])
    vl = np.array([p["dp_pp"]["lula"] ** 2 for p in pairs])
    vf = np.array([p["dp_pp"]["flavio"] ** 2 for p in pairs])
    c = np.array([p["cov_lula_flavio"] for p in pairs])
    days = np.array([p["dias"] for p in pairs])
    f, lv = float(w @ df), float(w @ dl)
    split, se = _share(f, lv, float(w**2 @ vf), float(w**2 @ vl), float(w**2 @ c))
    # Homogeneidade: resíduo de cada par contra a fração comum, só erro amostral.
    stat, dof = None, None
    if split is not None and len(pairs) > 1:
        r = (1 - split) * df - split * dl
        var = (1 - split) ** 2 * vf + split**2 * vl - 2 * split * (1 - split) * c
        stat, dof = float((r**2 / var).sum()), len(pairs) - 1
    return {
        "n_pares": len(pairs),
        "ufs": sorted({p["uf"] for p in pairs}),
        "variacao_media_pp": {"lula": lv, "flavio": f, "outros": float(w @ do)},
        "dias_medios": float(w @ days),
        "por_dia_pp": {
            "lula": lv / float(w @ days),
            "flavio": f / float(w @ days),
            "outros": float(w @ do) / float(w @ days),
        },
        "fracao_flavio": split,
        "dp": se,
        "homogeneidade_chi2": stat,
        "graus_liberdade": dof,
        "p_homogeneidade": float(chi2.sf(stat, dof)) if stat is not None else None,
    }


def states():
    pairs = state_pairs()
    out = {}
    for period, chosen in (
        ("todos_os_pares", pairs),
        ("pares_de_setembro", [p for p in pairs if p["setembro"]]),
    ):
        groups = {}
        for name, regions in GROUPS.items():
            subset = [p for p in chosen if regions is None or p["regiao"] in regions]
            if subset:
                groups[name] = _aggregate(subset)
        a, b = groups.get("Nordeste"), groups.get("Sul e Sudeste")
        contrast = None
        if a and b and a["dp"] and b["dp"]:
            diff = a["fracao_flavio"] - b["fracao_flavio"]
            se = float(np.hypot(a["dp"], b["dp"]))
            contrast = {
                "nordeste_menos_sul_sudeste": diff,
                "dp": se,
                "z": diff / se,
                "p": float(2 * norm.sf(abs(diff) / se)),
            }
        out[period] = {"grupos": groups, "contraste": contrast}
    return {
        "metodo": "Pares de ondas consecutivas da mesma casa na mesma UF (Quaest: rodadas da série estadual e onda nova de setembro; Real Time Big Data: duas ondas). Variação nos válidos; média ponderada pelo eleitorado de 2026; erro amostral multinomial com deff 1,5 nas duas ondas, independentes. Fração de Flávio = variação de Flávio / (variação de Flávio + de Lula).",
        "ressalvas": [
            "Demais candidaturas das rodadas anteriores da Quaest saem por diferença (100 menos Lula, Flávio, indecisos e branco/nulo); cada número impresso tem ±0,5 pp de arredondamento.",
            "Datas das rodadas anteriores vêm do rótulo impresso, com a regra declarada em analysis/predicao_2026/tendencia/estaduais_rotulos.json.",
            "O teste de homogeneidade usa só erro amostral; com erro não amostral (phi do DLM nacional em torno de 2), rejeição é esperada mesmo sem diferença real entre estados.",
        ],
        "rotulos": str(LABELS.relative_to(ROOT)),
        "pares": pairs,
        **out,
    }


# Teto de Lula -----------------------------------------------------------


def ceiling(polls, today, days=28):
    """Voto de 1º e 2º turno no total, na mesma onda, e a reserva entre eles."""
    agg = _read(AGGREGATOR)
    second = {
        s["id"]: s["publicado"]["2t"]
        for s in agg["pesquisas"] + agg["nao_reponderaveis"]
        if "2t" in s.get("publicado", {})
        and {"lula", "flavio"} <= set(s["publicado"]["2t"])
    }
    cut = today.toordinal()
    rows = [p for p in polls if p["id"] in second and midpoint(p["campo"]) > cut - days]
    houses = sorted({p["instituto"] for p in rows})
    t = np.array([midpoint(p["campo"]) - cut for p in rows])
    tc = t - t.mean()
    X = np.column_stack(
        [tc, *[[1.0 if p["instituto"] == h else 0.0 for p in rows] for h in houses]]
    )
    w = np.array([min(p["n"], 2000) for p in rows], float)
    series = {
        "lula_1t": [100 * p["publicado_vetor"][0] for p in rows],
        "flavio_1t": [100 * p["publicado_vetor"][1] for p in rows],
        "lula_2t": [second[p["id"]]["lula"] for p in rows],
        "flavio_2t": [second[p["id"]]["flavio"] for p in rows],
    }
    series["reserva_lula"] = list(np.subtract(series["lula_2t"], series["lula_1t"]))
    series["reserva_flavio"] = list(
        np.subtract(series["flavio_2t"], series["flavio_1t"])
    )
    dof = len(rows) - X.shape[1]
    out = {}
    with np.errstate(all="ignore"):
        inv = np.linalg.inv(X.T @ (w[:, None] * X))
        for name, y in series.items():
            y = np.asarray(y, float)
            b = inv @ X.T @ (w * y)
            r = y - X @ b
            s2 = float((w * r**2).sum() / dof)
            out[name] = {
                "media_ponderada_pp": float(np.average(y, weights=w)),
                "inclinacao_pp_dia": float(b[0]),
                "ep": float(np.sqrt(s2 * inv[0, 0])),
                # Casa média (média simples dos efeitos fixos) na data do corte.
                "casa_media_no_corte_pp": float(b[1:].mean() - b[0] * t.mean()),
            }
    return {
        "janela_dias": days,
        "n_ondas": len(rows),
        "graus_liberdade": dof,
        "fonte": "Placar publicado de 1º turno (base.national) e de 2º turno Lula × Flávio (docs/assets/reponderacao_pnad.json), mesma onda",
        "metodo": "MQP com efeito fixo de casa; percentuais do total, não dos válidos",
        "series": out,
        "leitura": "Teto operacional de 1º turno numa onda é o voto do candidato no 2º turno da mesma onda: a reserva é o que falta consolidar. Inclinação do 2º turno perto de zero com 1º turno subindo é consolidação de reserva, não expansão.",
    }


def estimate(polls, today):
    """Bloco nacional.tendencia.divisao_migracao."""
    series = national_series(polls, today)
    decl = declared()
    st = states()
    main = series["estimativas"][series["principal"]]
    state_main = st["todos_os_pares"]["grupos"]["Brasil"]
    nexus = decl["fontes"]["nexus_2026-09-27"]["matriz_peso_quem_pode_mudar"]
    datafolha = decl["fontes"]["datafolha_2026-10-01"]["matriz_peso_quem_pode_mudar"]
    rows = [
        ("serie_nacional_28d", main["fracao_flavio"], main["dp"]),
        ("estaduais_todos_os_pares", state_main["fracao_flavio"], state_main["dp"]),
        ("nexus_matriz_quem_pode_mudar", nexus["fracao_flavio"], nexus["dp"]),
        (
            "datafolha_matriz_quem_pode_mudar",
            datafolha["fracao_flavio"],
            datafolha["dp"],
        ),
    ]
    w = np.array([1 / se**2 for _, _, se in rows])
    x = np.array([v for _, v, _ in rows])
    return {
        "pergunta": "Da queda da terceira via nos válidos, que fração reaparece em Flávio (o resto vai para Lula)?",
        "resumo": [
            {"fonte": name, "fracao_flavio": value, "dp": se}
            for name, value, se in rows
        ],
        "sintese": {
            "fracao_flavio": float(w @ x / w.sum()),
            "dp_so_amostral": float(np.sqrt(1 / w.sum())),
            "qui2_concordancia": float(((x - w @ x / w.sum()) ** 2 * w).sum()),
            "graus_liberdade": len(rows) - 1,
            "ressalva": "Média de variância inversa de grandezas diferentes (fluxo líquido nas pesquisas e preferência declarada de 2º turno); o desvio é só amostral e subestima a incerteza real.",
        },
        "serie_nacional": series,
        "declarada": decl,
        "estaduais": st,
    }
