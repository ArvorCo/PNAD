"""Adapters das transcrições existentes; nenhum placar é redigitado aqui."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np

from . import dinamico, migracao, tendencia
from .recencia import NATIONAL_HALF_LIFE, age, decay, mean, midpoint, weights
from .tse import ROOT, sha

GROUPS = ("lula", "flavio", "outros", "indecisos", "branco_nulo")
REGIONS = {
    "Norte": "AC AM AP PA RO RR TO",
    "Nordeste": "AL BA CE MA PB PE PI RN SE",
    "Centro-Oeste": "DF GO MS MT",
    "Sudeste": "ES MG RJ SP",
    "Sul": "PR RS SC",
}
UF_REGION = {uf: region for region, ufs in REGIONS.items() for uf in ufs.split()}
UF_REGION["ZZ"] = "Exterior"
ELECTION = date(2026, 10, 4)
SCENARIO = "pessoas16_efetivo"
WINDOW_START = "2026-08-15"


def module(name):
    ident = name.replace("-", "_")
    if ident in sys.modules:
        return sys.modules[ident]
    spec = importlib.util.spec_from_file_location(
        ident, ROOT / "scripts" / f"{name}.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[ident] = mod
    spec.loader.exec_module(mod)
    return mod


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def normalize(vector):
    x = np.array(vector, dtype=float)
    if not np.isfinite(x).all() or (x < 0).any() or x.sum() <= 0:
        raise ValueError(f"Vetor inválido: {vector}")
    return x / x.sum()


def grouped(values, *, adjusted=False):
    aliases = {
        "Lula": "lula",
        "Flávio": "flavio",
        "Indecisos": "indecisos",
        "Branco/nulo": "branco_nulo",
    }
    numeric = {
        aliases.get(k, k): float(v)
        for k, v in values.items()
        if isinstance(v, (int, float))
    }
    if not {"lula", "flavio"}.issubset(numeric):
        raise ValueError("Placar sem os dois candidatos principais")
    if any(v < 0 for v in numeric.values()) and not adjusted:
        raise ValueError("Placar publicado negativo")
    negative = sum(-v for v in numeric.values() if v < 0)
    # Reponderação aditiva pode produzir pequenos negativos em candidaturas
    # arredondadas em zero. Projetar para o simplex, com a alteração registrada.
    numeric = {k: max(0, v) for k, v in numeric.items()}
    out = [
        numeric["lula"],
        numeric["flavio"],
        sum(
            v
            for k, v in numeric.items()
            if k not in ("lula", "flavio", "indecisos", "branco_nulo")
        ),
        numeric.get("indecisos", 0),
        numeric.get("branco_nulo", 0),
    ]
    total = sum(out)
    if not adjusted and abs(total - 100) > 3:
        raise ValueError(f"Partição publicada não fecha: {total}")
    return normalize(out), {
        "soma_original": total,
        "negativos_truncados_pp": negative,
        "normalizacao_pp": 100 - total,
    }


def latest(polls, today, days=7):
    begin = (today - timedelta(days=days - 1)).isoformat()
    selected = {}
    for p in polls:
        if not p.get("divulgacao") or not begin <= p["divulgacao"] <= today.isoformat():
            continue
        if p["campo"]["fim"] > today.isoformat():
            continue
        old = selected.get(p["instituto"])
        if old is None or (p["campo"]["fim"], p["divulgacao"], p["id"]) > (
            old["campo"]["fim"],
            old["divulgacao"],
            old["id"],
        ):
            selected[p["instituto"]] = p
    return [selected[k] for k in sorted(selected)]


def house_effects(polls, today):
    """Desvio relativo nos válidos, pareado por época. Não é erro eleitoral."""
    result = {}
    for p in polls:
        center = midpoint(p["campo"])
        if center < today.toordinal() - 45:
            continue
        peers = {}
        for other in polls:
            if other["instituto"] == p["instituto"]:
                continue
            dist = abs(midpoint(other["campo"]) - center)
            if dist > 7:
                continue
            if other["instituto"] not in peers or dist < peers[other["instituto"]][0]:
                peers[other["instituto"]] = (dist, other)
        if len(peers) < 3:
            continue
        own = normalize(p["publicado_vetor"][:3])
        other = np.median(
            [normalize(x[1]["publicado_vetor"][:3]) for x in peers.values()], axis=0
        )
        # Log-contraste centrado: invariante à escolha de candidato de referência.
        contrast = np.log(np.maximum(own, 0.001)) - np.log(np.maximum(other, 0.001))
        contrast -= contrast.mean()
        row = {
            "id": p["id"],
            "desvio_margem_pp": 100 * ((own[0] - own[1]) - (other[0] - other[1])),
            "log_contraste": contrast.tolist(),
            "pares": [x[1]["id"] for x in peers.values()],
        }
        result.setdefault(p["instituto"], []).append(row)
    return {
        name: {
            "n_ondas": len(waves),
            "desvio_margem_pp": float(
                np.median([w["desvio_margem_pp"] for w in waves])
            ),
            "contraste": (
                np.median([w["log_contraste"] for w in waves], axis=0)
                * len(waves)
                / (len(waves) + 3)
            ).tolist(),
            "ondas": waves,
        }
        for name, waves in sorted(result.items())
    }


def national(today, half_life=NATIONAL_HALF_LIFE, window_start=WINDOW_START):
    path = ROOT / "docs/assets/reponderacao_pnad.json"
    agg = read(path)
    polls, excluded = [], []
    for source in agg["pesquisas"] + agg["nao_reponderaveis"]:
        pub = source.get("publicado", {}).get("1t")
        reason = None
        if not pub or "lula" not in pub or "flavio" not in pub:
            reason = "Sem placar completo de 1º turno"
        elif not source.get("divulgacao"):
            reason = "Divulgação desconhecida"
        elif (
            source["divulgacao"] > today.isoformat()
            or source["campo"]["fim"] > today.isoformat()
        ):
            reason = "Posterior ao corte"
        elif source["campo"]["fim"] < window_start:
            reason = "Anterior à janela de diagnóstico"
        elif any(
            pub.get(k, 0) > 0
            for k in ("marcal", "ciro", "aldo", "daciolo", "aecio", "hero", "joaquim")
        ):
            reason = "Cartão contém candidatura fora do cenário atual"
        elif (source.get("selecao_1t") or {}).get("elegivel") is False:
            reason = "Cenário excluído pelo agregador"
        if reason:
            excluded.append({"id": source["id"], "motivo": reason})
            continue
        vector, audit = grouped(pub)
        turn = source.get("turnos", {}).get("1t", {})
        adj = turn.get("cenarios", {}).get(SCENARIO, {}).get("ajustado")
        # Mantém categorias não cruzadas. Uma ausência não vira zero.
        adj_vector, adj_audit = (
            grouped({**pub, **adj}, adjusted=True) if adj else (None, None)
        )
        polls.append(
            {
                "id": source["id"],
                "instituto": source["instituto"],
                "campo": source["campo"],
                "divulgacao": source["divulgacao"],
                "n": source["n"],
                "registro": source.get("registro_tse"),
                "publicado_vetor": vector.tolist(),
                "pnad_vetor": adj_vector.tolist() if adj is not None else None,
                "opcoes_publicadas": pub,
                "opcoes_pnad": {**pub, **adj} if adj else None,
                "auditoria_publicado": audit,
                "auditoria_pnad": adj_audit,
                "fonte": source.get("fonte"),
                "sem_renda_motivo": source.get("motivo"),
                "renda_nao_publicada_n": source.get("renda", {}).get(
                    "nao_publicada_n", 0
                ),
            }
        )
    # A mesma casa e campo entram uma única vez, mesmo com revisão de documento.
    dedup = {
        (p["instituto"], p["campo"]["inicio"], p["campo"]["fim"]): p
        for p in sorted(polls, key=lambda p: (p["divulgacao"], p["id"]))
    }
    polls = list(dedup.values())
    for p in polls:
        p["idade_campo_dias"] = age(p["campo"], today)
        p["peso_recencia"] = decay(p["idade_campo_dias"], half_life)
        p["previsao_vetor"] = p["pnad_vetor"] or p["publicado_vetor"]
        p["previsao_opcoes"] = p["opcoes_pnad"] or p["opcoes_publicadas"]
    selected = latest(polls, today)
    adjusted = [p for p in selected if p["pnad_vetor"] is not None]
    if len(adjusted) < 3:
        raise ValueError("Menos de três casas reponderáveis nos últimos sete dias")

    for p, w in zip(selected, weights(selected), strict=True):
        p["participacao_central_pct"] = 100 * float(w)
    for p, w in zip(adjusted, weights(adjusted), strict=True):
        p["participacao_pnad_pct"] = 100 * float(w)

    # Âncora dinâmica: mesma série e mesmos vetores da central, sem trocar a
    # central. Variantes ficam registradas para auditoria, fora das âncoras.
    dynamic = dinamico.fit(polls, today, window_start=window_start)
    paired_series = [p for p in polls if p["pnad_vetor"] is not None]
    dynamic["variantes"] = {
        name: {
            k: fitted["estado_final"][k]
            for k in ("vetor", "validos_pct", "margem_flavio_lula_validos_pp")
        }
        | {
            "n_ondas": fitted["n_ondas"],
            "phi": fitted["parametros"]["phi_variancia_nao_amostral"],
        }
        for name, fitted in (
            ("phi_1", dinamico.fit(polls, today, excess=False)),
            ("somente_pnad", dinamico.fit(paired_series, today, "pnad_vetor")),
        )
    }
    # Âncora de tendência: estado projetado para o dia da eleição, com o nível
    # no corte para comparação. Diagnóstico completo em nacional.tendencia.
    trend = tendencia.fit(
        polls, today, ELECTION, window_start=window_start, level_fit=dynamic
    )
    trend["divisao_migracao"] = migracao.estimate(polls, today)
    trend["teto"] = migracao.ceiling(polls, today)
    trend["central_com_inclinacao"] = sloped_central(selected, polls, today)
    projected, at_cut = trend["estado_projetado"], trend["estado_corte"]
    # Desvio da projeção além do nível: para a central com inclinação, o da
    # inclinação × horizonte; para a tendência do DLM, o acréscimo de variância
    # entre o estado no corte e o estado projetado à eleição.
    projection_sd = {
        "central_inclinacao": trend["central_com_inclinacao"]["dp_margem_projecao_pp"],
        "tendencia": float(
            np.sqrt(
                max(0.0, projected["dp_margem_pp"] ** 2 - at_cut["dp_margem_pp"] ** 2)
            )
        ),
    }
    return {
        "referencia_agregador": agg["referencia"],
        "sha256_agregador": sha(path),
        "benchmark": agg["benchmark"],
        "meia_vida_dias": half_life,
        "pesquisas": polls,
        "selecionadas": selected,
        "pareadas": adjusted,
        "alvos": {
            "inclusivo": mean(selected, "previsao_vetor"),
            "sem_recencia": mean(selected, "previsao_vetor", equal=True),
            "pnad": mean(adjusted, "pnad_vetor"),
            "publicado": mean(adjusted, "publicado_vetor"),
            "todas": mean(selected, "publicado_vetor"),
            "dinamico": dynamic["estado_final"]["vetor"],
            "tendencia": trend["estado_projetado"]["vetor"],
            "tendencia_corte": trend["estado_corte"]["vetor"],
            "central_inclinacao": trend["central_com_inclinacao"]["vetor"],
        },
        "incerteza_projecao_pp": projection_sd,
        "dinamico": dynamic,
        "tendencia": trend,
        "efeitos_casa": house_effects(polls, today),
        "excluidas": excluded,
    }


def sloped_central(selected, polls, today, days=28):
    """Central inclusiva deslocada pela inclinação encolhida de `days` dias,
    da data efetiva da central (ponto médio ponderado) até a eleição."""
    w = weights(selected)
    base_vector = np.average([p["previsao_vetor"] for p in selected], axis=0, weights=w)
    start = float(w @ [midpoint(p["campo"]) for p in selected])
    slopes, fitted = tendencia.shrunk_slopes(polls, today, days)
    horizon = ELECTION.toordinal() - start
    vector = tendencia.shift_valid(base_vector, slopes, horizon)
    valid = 100 * vector[:3] / vector[:3].sum()
    # Incerteza da extrapolação na diferença F−L: horizonte × dp(β_F − β_L),
    # com a covariância conjunta das inclinações brutas (sem encolher, o que
    # é conservador). Entra no Monte Carlo como choque comum adicional.
    if fitted is None:
        slope_sd = 0.0
    else:
        c = np.asarray(fitted["cov_inclinacao_lula_flavio"], float)
        slope_sd = float(np.sqrt(max(0.0, c[0, 0] + c[1, 1] - 2 * c[0, 1])))
    return {
        "janela_dias": days,
        "ancora_de_partida": "inclusivo",
        "data_efetiva_central": date.fromordinal(round(start)).isoformat(),
        "horizonte_dias": horizon,
        "dp_inclinacao_margem_pp_dia": slope_sd,
        "dp_margem_projecao_pp": max(0.0, horizon) * slope_sd,
        "inclinacoes_encolhidas_validos_pp_dia": dict(
            zip(GROUPS[:3], slopes.tolist(), strict=True)
        ),
        "inclinacoes_brutas_validos_pp_dia": {
            k: fitted["categorias"][k]["inclinacao_pp_dia"] for k in GROUPS[:3]
        },
        "vetor": vector.tolist(),
        "validos_pct": dict(zip(GROUPS[:3], valid.tolist(), strict=True)),
        "margem_flavio_lula_validos_pp": float(valid[1] - valid[0]),
        "regra": "fator de encolhimento b² / (b² + ep²) em cada categoria dos válidos; massa válida, indecisos e branco/nulo da central preservados",
    }


def field_dates(text):
    iso = re.findall(r"\d{4}-\d{2}-\d{2}", text or "")
    if iso:
        return {"inicio": iso[0], "fim": iso[-1]}
    match = re.search(r"(\d{1,2})\s*a\s*(\d{1,2})/(\d{2})/(\d{4})", text or "")
    if not match:
        raise ValueError(f"Campo estadual não identificado: {text}")
    start, end, month, year = map(int, match.groups())
    return {
        "inicio": date(year, month, start).isoformat(),
        "fim": date(year, month, end).isoformat(),
    }


def turnout_signal(d, B):
    cx, comp = B.cruzamento(d, "pres_1t_x_comparecimento"), B.comparecimento(d)
    if not cx or not comp:
        return None
    cols = cx["colunas"]
    a = next((v for k, v in cols.items() if k.lower().startswith("sempre")), None)
    b = next((v for k, v in cols.items() if not k.lower().startswith("sempre")), None)
    if not a or not b or a["rodada"] != b["rodada"]:
        return None
    v = comp["valores"]
    wa = v.get("Sempre vota e vai votar", 0)
    wb = v.get("Já deixou de votar, mas vai votar", 0)
    na = wa
    nb = sum(
        v.get(k, 0)
        for k in (
            "Já deixou de votar, mas vai votar",
            "Sempre vota, mas não vai votar",
            "Já deixou de votar e não vai votar",
            "Nunca votou e não vai votar",
        )
    )
    if min(wa, wb, na, nb) <= 0:
        return None
    va, _ = grouped(a["valores"])
    vb, _ = grouped(b["valores"])
    allv = normalize((na * va + nb * vb)[:3])
    likely = normalize((wa * va + wb * vb)[:3])
    ratio = likely / np.maximum(allv, 0.001)
    return {
        "fatores": ratio.tolist(),
        "pagina_voto": cx["pagina"],
        "pagina_grupos": comp["pagina"],
        "sempre": wa,
        "outros_que_vao": wb,
        "cobertura_pct": na + nb,
        "rodada": a["rodada"],
        "voto_todos": allv.tolist(),
        "voto_provavel": likely.tolist(),
    }


def rounded_crossbreak_bounds(habit, first, second):
    """Envelope aritmético de percentuais inteiros; não é intervalo amostral.

    Cada número impresso admite ±0,5 pp. Os quatro hábitos do segundo
    grupo fecham com o primeiro e NS/NR. A preferência de NS/NR fica livre.
    """
    a_bounds = (max(0, habit[0] - 0.5), min(100, habit[0] + 0.5))
    m_bounds = (max(0, habit[5] - 0.5), min(100, habit[5] + 0.5))
    b_bounds = (
        sum(max(0, x - 0.5) for x in habit[1:5]),
        sum(min(100, x + 0.5) for x in habit[1:5]),
    )
    vertices = [(a, m) for a in a_bounds for m in m_bounds]
    for total in (100 - b_bounds[0], 100 - b_bounds[1]):
        vertices += [(a, total - a) for a in a_bounds]
        vertices += [(total - m, m) for m in m_bounds]
    vertices = [
        (a, m)
        for a, m in vertices
        if a_bounds[0] - 1e-8 <= a <= a_bounds[1] + 1e-8
        and m_bounds[0] - 1e-8 <= m <= m_bounds[1] + 1e-8
        and b_bounds[0] - 1e-8 <= 100 - a - m <= b_bounds[1] + 1e-8
    ]
    if not vertices:
        raise ValueError("Hábitos incompatíveis com arredondamento e soma 100")
    pa, pb = np.array(first[:2]) / 100, np.array(second[:2]) / 100
    lower = [
        a * np.maximum(0, pa - 0.005) + (100 - a - m) * np.maximum(0, pb - 0.005)
        for a, m in vertices
    ]
    upper = [
        a * np.minimum(1, pa + 0.005) + (100 - a - m) * np.minimum(1, pb + 0.005) + m
        for a, m in vertices
    ]
    return np.min(lower, axis=0), np.max(upper, axis=0)


def compact_turnout(d):
    """Mesmo cálculo, com cruzamento recente conferido e controle de recomposição."""
    source = d.get("comparecimento_compacto")
    if not source:
        return None
    h = source["habito"]
    if len(h) != 6 or not np.isfinite(h).all() or min(h) < 0 or abs(sum(h) - 100) > 1:
        raise ValueError("Partição de hábito inválida")
    if any(
        len(source[k]) != 5 or abs(sum(source[k]) - 100) > 3
        for k in ("sempre_vota", "outros_habitos")
    ):
        raise ValueError("Partição de voto por hábito inválida")
    va = normalize(source["sempre_vota"])
    vb = normalize(source["outros_habitos"])
    wa, wb, nb = h[0], h[2], sum(h[1:5])
    mix = (wa * va + nb * vb) / (wa + nb)
    published, _ = grouped(d["pres_1t"]["valores"])
    residual = 100 * (mix[:2] - published[:2])
    missing = 100 - wa - nb
    unexplained = 100 * published[:2] - (wa * va + nb * vb)[:2]
    lower, upper = rounded_crossbreak_bounds(
        h, source["sempre_vota"], source["outros_habitos"]
    )
    # Testa compatibilidade das duas candidaturas, sem atribuir um voto a NS/NR.
    # Não exige igualdade de números inteiros nem chama esse envelope de IC.
    if (
        (100 * published[:2] + 0.5 < lower) | (100 * published[:2] - 0.5 > upper)
    ).any():
        raise ValueError(f"{d['uf']}: cruzamento incompatível com placar: {residual}")
    allv = normalize(mix[:3])
    likely = normalize((wa * va + wb * vb)[:3])
    return {
        "fatores": (likely / np.maximum(allv, 0.001)).tolist(),
        "pagina_voto": source["pagina_voto"],
        "pagina_grupos": source["pagina_habito"],
        "sempre": wa,
        "outros_que_vao": wb,
        "cobertura_pct": wa + nb,
        "rodada": d["campo"],
        "voto_todos": allv.tolist(),
        "voto_provavel": likely.tolist(),
        "recomposicao_residuo_lula_flavio_pp": residual.tolist(),
        "recomposicao_residuo_massa_pp": unexplained.tolist(),
        "recomposicao_envelope_arredondamento_pct": [lower.tolist(), upper.tolist()],
        "habito_nao_declarado_pct": missing,
        "fonte_sha256": d["sha256_pdf"],
    }


def state_polls(today):
    B = module("voto_util_base")
    rows, excluded = [], []
    paths = (
        sorted((ROOT / "analysis/voto_util/quaest").glob("*.json"))
        + sorted((ROOT / "analysis/voto_util/outros").glob("*.json"))
        + sorted((ROOT / "analysis/predicao_2026/estaduais").glob("*.json"))
    )
    for path in paths:
        if path.name.startswith("_"):
            continue
        d = read(path)
        is_quaest = path.parent.name == "quaest"
        first = B.pres_1t_quaest(d) if is_quaest else d.get("pres_1t")
        if not first:
            excluded.append(
                {"arquivo": str(path.relative_to(ROOT)), "motivo": "Sem presidente"}
            )
            continue
        v = B.normaliza(first["valores"])
        ficha = d.get("ficha") or {}
        field = field_dates(ficha.get("campo") if is_quaest else d.get("campo"))
        release = d.get("divulgacao") or d.get("embargo_divulgacao")
        # Quando a divulgação falta, só afirmar que o documento está no
        # acervo do corte atual. Não usar essas linhas num backtest por data.
        if field["fim"] > today.isoformat() or (
            release and release > today.isoformat()
        ):
            excluded.append(
                {"arquivo": str(path.relative_to(ROOT)), "motivo": "Posterior ao corte"}
            )
            continue
        if v.get("Marçal", 0) > 0:
            excluded.append(
                {"arquivo": str(path.relative_to(ROOT)), "motivo": "Cenário com Marçal"}
            )
            continue
        vector, audit = grouped(v)
        second = B.pres_2t_quaest(d) if is_quaest else None
        if not is_quaest:
            scenarios = (d.get("pres_2t") or {}).get("cenarios") or []
            second = (
                {
                    "valores": B.normaliza(scenarios[0]),
                    "pagina": (d.get("pres_2t") or {}).get("pagina"),
                }
                if scenarios
                else None
            )
        # Reserva é uma diferença de margens, não uma matriz individual.
        sv = (second or {}).get("valores", {})
        reserve = [
            max(0, sv.get(k, v[k]) - v[k])
            / max(
                sum(
                    vv for kk, vv in v.items() if kk not in ("Indecisos", "Branco/nulo")
                ),
                1,
            )
            for k in ("Lula", "Flávio")
        ]
        rows.append(
            {
                "uf": d["uf"],
                "instituto": d.get("instituto", "Quaest"),
                "campo": field,
                "divulgacao": release,
                "disponibilidade": (
                    d.get("divulgacao_tipo", "divulgação documentada")
                    if release
                    else "data de divulgação ausente; documento no acervo atual"
                ),
                "n": ficha.get("n", d.get("n", 800)),
                "registro": ficha.get("registro_tse_nacional")
                or ficha.get("registro_tse")
                or d.get("registro_tse"),
                "pagina": first.get("pagina"),
                "arquivo": str(path.relative_to(ROOT)),
                "sha256": sha(path),
                "fonte": d.get("url") or d.get("url_pdf"),
                "sha256_relatorio": d.get("sha256_pdf") or d.get("sha256"),
                "vetor": vector.tolist(),
                "auditoria": audit,
                "reserva": reserve,
                "reserva_pagina_2t": (second or {}).get("pagina"),
                "comparecimento": compact_turnout(d)
                or (turnout_signal(d, B) if is_quaest else None),
            }
        )
    selected = {}
    for p in sorted(
        rows, key=lambda p: (p["campo"]["fim"], p["divulgacao"] or "", p["arquivo"])
    ):
        ident = (p["uf"], p["instituto"])
        if ident in selected:
            excluded.append(
                {
                    "arquivo": selected[ident]["arquivo"],
                    "motivo": "Onda anterior da mesma casa/UF",
                }
            )
        selected[ident] = p
    return list(selected.values()), excluded
