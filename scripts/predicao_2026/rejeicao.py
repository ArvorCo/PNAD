"""Rejeição como régua de destino, nunca como subtração de voto já contado.

Quem rejeita Lula e já declara voto em Flávio, em outro nome ou em branco já
está no placar; subtrair a rejeição desses votos seria contar duas vezes. A
rejeição só informa para onde tende a ir quem ainda se move: os indecisos que
escolhem e a migração da terceira via. A disponibilidade de um finalista é
1 menos a rejeição declarada, e a parte de Flávio no destino é

    s = (1 − r_F) / [(1 − r_F) + (1 − r_L)].

A régua nacional é a média com peso temporal (meia-vida nacional, idade pelo
ponto médio do campo, uma onda por casa, divulgação nos últimos 7 dias) das
casas que publicam a pergunta na forma comparável, "não votaria de jeito
nenhum". Escalas de potencial e enunciados não publicados entram como controle,
fora da média. Nenhuma casa publica rejeição dentro do eleitorado de terceira
via nem entre indecisos; os recortes de não alinhados aparecem como proxy.
"""

from __future__ import annotations

from datetime import timedelta
from math import sqrt

from .base import read
from .consolidacao import projection
from .recencia import NATIONAL_HALF_LIFE, age, decay
from .tse import ROOT, sha

SOURCE = ROOT / "analysis/predicao_2026/rejeicao/rejeicao_092026.json"
DEFF = 1.5
WINDOW_DAYS = 7
Z95 = 1.96
FORMATS = ("cartao_multipla", "grade_por_candidato")
NOTA = (
    "A rejeição informa o destino de quem ainda não está no placar e nunca "
    "retira voto já contado. A parte por disponibilidade supõe que quem se "
    "move escolhe entre os finalistas na proporção de quem aceita votar em "
    "cada um no eleitorado total; a rejeição medida no total é régua de "
    "reserva, não medição dentro da terceira via."
)


def availability_share(rej_lula, rej_flavio):
    """Parte de Flávio por disponibilidade, com rejeições em fração de [0, 1]."""
    for r in (rej_lula, rej_flavio):
        if not 0 <= r <= 1:
            raise ValueError("Rejeição fora de [0, 1]")
    a_f, a_l = 1 - rej_flavio, 1 - rej_lula
    if a_f + a_l <= 0:
        raise ValueError("Nenhum finalista disponível")
    return a_f / (a_f + a_l)


def share_se(rej_lula, rej_flavio, var_l, var_f, cov):
    """Erro padrão da parte por disponibilidade, método delta."""
    a_f, a_l = 1 - rej_flavio, 1 - rej_lula
    d2 = (a_f + a_l) ** 2
    g_l, g_f = a_f / d2, -a_l / d2
    return sqrt(max(0.0, g_l**2 * var_l + g_f**2 * var_f + 2 * g_l * g_f * cov))


def sampling(rej_lula, rej_flavio, n, deff=DEFF):
    """Variâncias e covariância das duas rejeições numa mesma amostra.

    A rejeição conjunta quase nunca é publicada. Usamos o limite inferior de
    Fréchet, max(0, r_L + r_F − 1): é a covariância mais negativa possível e,
    como os gradientes da parte têm sinais opostos, dá o maior erro padrão.
    """
    both = max(0.0, rej_lula + rej_flavio - 1)
    return (
        rej_lula * (1 - rej_lula) * deff / n,
        rej_flavio * (1 - rej_flavio) * deff / n,
        (both - rej_lula * rej_flavio) * deff / n,
    )


def _ci(share, se):
    return [share - Z95 * se, share + Z95 * se]


def _eligible(c, today):
    begin = (today - timedelta(days=WINDOW_DAYS - 1)).isoformat()
    if not c["publica"]:
        return False, "não publica rejeição"
    if c["campo"]["fim"] > today.isoformat():
        return False, "campo posterior ao corte"
    if not begin <= c["divulgacao"] <= today.isoformat():
        return False, f"divulgação fora dos {WINDOW_DAYS} dias do corte"
    if not c["comparavel"]:
        return False, "controle: " + c["motivo_controle"]
    return True, None


def _row(c, today, half_life):
    rl, rf = c["lula"] / 100, c["flavio"] / 100
    var_l, var_f, cov = sampling(rl, rf, c["n"])
    s = availability_share(rl, rf)
    se = share_se(rl, rf, var_l, var_f, cov)
    days = age(c["campo"], today)
    ok, motivo = _eligible(c, today)
    return {
        "instituto": c["instituto"],
        "pesquisa": c["pesquisa"],
        "campo": c["campo"],
        "divulgacao": c["divulgacao"],
        "n": c["n"],
        "tipo_pergunta": c["tipo_pergunta"],
        "pagina": c["pagina_principal"],
        "sha256": c["sha256"],
        "lula": c["lula"],
        "flavio": c["flavio"],
        "parte_flavio": s,
        "erro_padrao": se,
        "idade_dias": days,
        "peso_bruto": decay(days, half_life),
        "na_media": ok,
        "motivo_fora": motivo,
        "_var": (var_l, var_f, cov),
    }


def pool(rows):
    """Média temporal das rejeições e erro padrão por amostragem (deff 1,5)."""
    if not rows:
        return None
    total = sum(r["peso_bruto"] for r in rows)
    w = [r["peso_bruto"] / total for r in rows]
    rl = sum(wi * r["lula"] for wi, r in zip(w, rows, strict=True)) / 100
    rf = sum(wi * r["flavio"] for wi, r in zip(w, rows, strict=True)) / 100
    var_l, var_f, cov = (
        sum(wi**2 * r["_var"][k] for wi, r in zip(w, rows, strict=True))
        for k in range(3)
    )
    s = availability_share(rl, rf)
    se = share_se(rl, rf, var_l, var_f, cov)
    spread = [r["parte_flavio"] for r in rows]
    # Dispersão entre casas: inclui formato, desenho e efeito de casa, que a
    # amostragem não cobre.
    between = sqrt(sum(wi * (x - s) ** 2 for wi, x in zip(w, spread, strict=True)))
    return {
        "casas": [r["instituto"] for r in rows],
        "pesos": {r["instituto"]: wi for wi, r in zip(w, rows, strict=True)},
        "lula": 100 * rl,
        "flavio": 100 * rf,
        "erro_padrao_lula": 100 * sqrt(var_l),
        "erro_padrao_flavio": 100 * sqrt(var_f),
        "parte_flavio": s,
        "erro_padrao": se,
        "ic95": _ci(s, se),
        "amplitude_entre_casas": [min(spread), max(spread)],
        "dp_ponderado_entre_casas": between,
    }


def _segment(c, seg):
    rl, rf = seg["lula"] / 100, seg["flavio"] / 100
    s = availability_share(rl, rf)
    out = {
        "instituto": c["instituto"],
        "recorte": seg["recorte"],
        "rotulo": seg["rotulo"],
        "pagina": seg["pagina"],
        "tipo_pergunta": c["tipo_pergunta"],
        "lula": seg["lula"],
        "flavio": seg["flavio"],
        "parte_flavio": s,
        "erro_padrao": None,
        "base": None,
    }
    if "base_ponderada" in seg:
        n, deff, base = seg["base_ponderada"], DEFF, "base ponderada publicada"
    elif "margem_erro_pp" in seg:
        # Margem publicada para p = 0,5: n efetivo, já com o desenho da casa.
        n = (Z95 * 0.5 / (seg["margem_erro_pp"] / 100)) ** 2
        deff, base = 1.0, "n efetivo pela margem publicada do recorte"
    elif "ic95_inferior" in seg:
        half = min((seg[k] - seg["ic95_inferior"][k]) / 100 for k in ("lula", "flavio"))
        p = seg["lula"] / 100
        n = Z95**2 * p * (1 - p) / half**2
        deff, base = 1.0, "n efetivo pelo intervalo publicado do recorte"
    else:
        return out
    var_l, var_f, cov = sampling(rl, rf, n, deff)
    out["erro_padrao"] = share_se(rl, rf, var_l, var_f, cov)
    out["base"] = f"{base}: {n:.0f}"
    return out


def nexus_matrix(m):
    """Parte de Flávio entre quem escolhe um finalista, ponderada pelo 1º turno."""
    weights = {k: v for k, v in m["participacao_1t"].items() if k in m["linhas"]}
    f = sum(w * m["linhas"][k]["flavio"] for k, w in weights.items())
    lula = sum(w * m["linhas"][k]["lula"] for k, w in weights.items())
    mass = sum(weights.values())
    return {
        "pagina": m["pagina"],
        "sha256": m["sha256"],
        "origens": sorted(weights),
        "parte_flavio_entre_finalistas": f / (f + lula),
        "flavio_pct_da_terceira_via": f / mass,
        "lula_pct_da_terceira_via": lula / mass,
        "nota": m["nota"],
    }


def _z(a, se_a, b, se_b):
    if se_b is None:
        return None
    return (a - b) / sqrt(se_a**2 + se_b**2)


def block(consolidacao, today, *, half_life=NATIONAL_HALF_LIFE, source=SOURCE):
    """Bloco "rejeicao" do JSON principal."""
    doc = read(source)
    rows = [_row(c, today, half_life) for c in doc["casas"] if c["publica"]]
    main = [r for r in rows if r["na_media"]]
    pooled = pool(main)
    if pooled is None:
        raise ValueError("Nenhuma casa com rejeição comparável na janela")
    formats = {
        f: pool([r for r in main if r["tipo_pergunta"] == f])
        for f in FORMATS
        if any(r["tipo_pergunta"] == f for r in main)
    }
    controls = [r for r in rows if r["motivo_fora"] and "controle" in r["motivo_fora"]]
    segments = [
        _segment(c, seg)
        for c in doc["casas"]
        if c["publica"]
        for seg in c.get("segmentos", [])
    ]
    s, se = pooled["parte_flavio"], pooled["erro_padrao"]
    comparisons = {}
    for key in ("28", "14"):
        proj = consolidacao["projecao"][key]
        div = consolidacao["janelas"][key]["divisao"]
        comparisons[f"serie_{key}"] = {
            "parte_flavio": proj["parte_flavio_usada"],
            "erro_padrao": div["erro_padrao"],
            "z_disponibilidade_menos_serie": _z(
                s, se, proj["parte_flavio_usada"], div["erro_padrao"]
            ),
        }
    comparisons["nexus_p84"] = nexus_matrix(doc["matriz_nexus"])
    datafolha = next(c for c in doc["casas"] if c["instituto"] == "Datafolha")
    second = datafolha["destino_declarado"]
    comparisons["datafolha_segunda_opcao"] = {
        "pagina": second["pagina"],
        "sha256": datafolha["sha256"],
        **{
            k: {
                **second[k],
                "parte_flavio_entre_finalistas": second[k]["flavio"]
                / (second[k]["flavio"] + second[k]["lula"]),
            }
            for k in ("hesitantes", "nao_alinhados_hesitantes")
        },
    }
    reserve = [
        consolidacao["reserva_nacional_pct"][k] / 100 for k in ("lula", "flavio")
    ]
    migration = {}
    for key in ("28", "14"):
        fit = consolidacao["janelas"][key]
        shifted = {**fit, "divisao": {**fit["divisao"], "flavio": s}}
        migration[key] = projection(shifted, consolidacao["horizonte_dias"], reserve)
    controls_pooled = pool(controls)
    for r in rows:
        r.pop("_var")
    return {
        "natureza": "Régua de destino de quem ainda se move; não subtrai voto contado",
        "nota": NOTA,
        "fonte": {"arquivo": str(source.relative_to(ROOT)), "sha256": sha(source)},
        "janela_divulgacao_dias": WINDOW_DAYS,
        "meia_vida_dias": half_life,
        "deff_assumido": DEFF,
        "covariancia": "limite inferior de Fréchet da rejeição conjunta",
        "rejeicao_conjunta_nexus_p101": next(
            c["conjunta"] for c in doc["casas"] if c["instituto"] == "Nexus"
        ),
        "casas": rows,
        "nao_publicam": [
            {
                "instituto": c["instituto"],
                "pdf": c["pdf"],
                "sha256": c["sha256"],
                "paginas_varridas": c["paginas_varridas"],
                "nota": c["nota"],
            }
            for c in doc["casas"]
            if not c["publica"]
        ],
        "media": pooled,
        "por_formato": formats,
        "controles": controls,
        "controles_media": controls_pooled,
        "segmentos": segments,
        "terceira_via_indecisos": {
            "publicado": False,
            "nota": "Nenhuma casa varrida publica rejeição dentro do eleitorado de "
            "cada candidato de terceira via nem entre indecisos. Os recortes de "
            "não alinhados (independentes, sem partido, centro) são o proxy mais "
            "próximo.",
        },
        "comparacao": comparisons,
        "indecisos_flavio": round(s, 4),
        "consolidacao_disponibilidade": migration,
    }


def resolve(params, rej):
    """Troca o destino "disponibilidade" pelo número; o motor segue numérico."""
    if params.get("indecisos_flavio") == "disponibilidade":
        return {**params, "indecisos_flavio": rej["indecisos_flavio"]}
    return params
