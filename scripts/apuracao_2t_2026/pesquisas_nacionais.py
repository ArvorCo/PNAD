"""Pesquisas nacionais do 2º turno de 2026 contra a urna: aritmética pura.

Convenção desta rodada: erro = pesquisa menos urna, em pontos dos válidos; na
diferença Flávio menos Lula (F−L), positivo quer dizer que a pesquisa pôs
Flávio mais à frente (ou menos atrás) do que a urna. O 1º turno usou L−F; o
campo ``erro_lula_menos_flavio`` traz o mesmo número com o sinal do 1º turno.

Os válidos de cada placar seguem a regra da casa (``apuracao_2026.pesquisas``):
candidaturas renormalizadas para 100, indecisos e branco/nulo fora.
"""

from __future__ import annotations

import math
import statistics
from collections.abc import Iterable, Mapping
from datetime import date, timedelta
from typing import Any

from apuracao_2026 import pesquisas as P

ELEICAO = date(2026, 10, 25)
INICIO_POS_URNA = "2026-10-05"
INICIO_ULTIMA_SEMANA = "2026-10-19"
CENARIO = "pessoas16_efetivo"
DEFF = 1.5


def modo(metodo: str | None) -> str:
    m = (metodo or "").lower()
    if "online" in m or "digital" in m:
        return "online"
    if any(t in m for t in ("presencial", "pessoa", "domiciliar")):
        return "presencial"
    if any(t in m for t in ("telef", "cati", "ura", "ivr")):
        return "telefone"
    return "nao_informado"


def dif_fl(v: Mapping[str, float]) -> float:
    return float(v["flavio"]) - float(v["lula"])


def normalizar_dois(v: Mapping[str, float]) -> dict[str, float]:
    s = float(v["flavio"]) + float(v["lula"])
    return {"flavio": 100 * float(v["flavio"]) / s, "lula": 100 * float(v["lula"]) / s}


def erro(v: Mapping[str, float], urna: Mapping[str, float]) -> dict[str, float]:
    e = dif_fl(v) - dif_fl(urna)
    return {
        "pesquisa_f_menos_l": dif_fl(v),
        "urna_f_menos_l": dif_fl(urna),
        "erro_f_menos_l": e,
        "erro_lula_menos_flavio": -e,
        "erro_flavio": float(v["flavio"]) - float(urna["flavio"]),
        "erro_lula": float(v["lula"]) - float(urna["lula"]),
    }


def meio_do_campo(campo: Mapping[str, str]) -> date:
    a, b = date.fromisoformat(campo["inicio"]), date.fromisoformat(campo["fim"])
    return a + timedelta(days=(b - a).days / 2)


def onda(p: dict[str, Any], pnad: dict[str, dict]) -> dict[str, Any]:
    """Placar publicado, válidos (total e oficial) e reponderado de uma onda.

    ``pnad`` mapeia id para ``{"vetor": placar reponderado, "fonte": origem}``.
    """
    total = {k: float(v) for k, v in p["publicado"]["2t"].items()}
    v_total, aud = P.validos(total)
    oficial = ((p.get("publicado_validos") or {}).get("2t")) or None
    rep = None
    r = pnad.get(p["id"])
    if r:
        v_rep, aud_rep = P.validos(r["vetor"])
        rep = {
            "total": r["vetor"],
            "validos": v_rep,
            "auditoria": aud_rep,
            "fonte": r["fonte"],
            "cenario": CENARIO,
        }
    renda = p.get("renda") or {}
    return {
        "id": p["id"],
        "instituto": p["instituto"],
        "registro_tse": p.get("registro_tse"),
        "campo": p["campo"],
        "meio_do_campo": meio_do_campo(p["campo"]).isoformat(),
        "divulgacao": p.get("divulgacao"),
        "dias_fim_campo_ate_urna": (
            ELEICAO - date.fromisoformat(p["campo"]["fim"])
        ).days,
        "n": p.get("n"),
        "metodo": p.get("metodo"),
        "modo": modo(p.get("metodo")),
        "perfil_renda": renda.get("perfil_tipo"),
        "publicado_total": total,
        "auditoria_total": aud,
        "validos_do_total": v_total,
        "validos_oficiais": oficial,
        "validos_oficiais_normalizados": normalizar_dois(oficial) if oficial else None,
        "reponderado": rep,
        "reponderado_motivo": None if rep else (p.get("motivo") or "sem PNAD"),
        "eleitor_provavel_oficial": p.get("eleitor_provavel_oficial"),
        "eleitor_provavel_documental": p.get("eleitor_provavel_documental"),
        "subconjunto_presenca_publicado": p.get("subconjunto_presenca_publicado"),
    }


def vetores_pnad(
    pnad_json: dict[str, Any], sim: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    """Placar reponderado de cada onda: o do snapshot das centrais quando existe.

    O snapshot aplica a parcela ajustável e a normalização do total que o
    agregador bruto não aplica; é o vetor que entrou na Média e na Projeção.
    """
    out: dict[str, dict[str, Any]] = {}
    for p in pnad_json["pesquisas"]:
        adj = (
            ((p.get("turnos") or {}).get("2t") or {})
            .get("cenarios", {})
            .get(CENARIO, {})
            .get("ajustado")
        )
        if adj:
            out[p["id"]] = {"vetor": adj, "fonte": "reponderacao_pnad.json"}
    for p in sim.get("polls") or []:
        if p.get("pnad"):
            out[p["id"]] = {
                "vetor": p["pnad"],
                "fonte": "reponderacao_simulador.json (polls)",
                "perfil_tipo": p.get("perfil_tipo"),
            }
    return out


def comparar(x: dict[str, Any], urna: Mapping[str, float]) -> dict[str, Any]:
    """Acrescenta à onda os erros contra a urna e o teste da margem."""
    out = dict(x)
    out["erro_validos_do_total"] = erro(x["validos_do_total"], urna)
    out["erro_validos_oficiais"] = (
        erro(x["validos_oficiais_normalizados"], urna)
        if x["validos_oficiais_normalizados"]
        else None
    )
    out["erro_reponderado"] = (
        erro(x["reponderado"]["validos"], urna) if x["reponderado"] else None
    )
    frac = x["auditoria_total"]["soma_candidaturas_pct_total"] / 100
    v = x["validos_do_total"]
    margem = (
        P.margem_diferenca_aas(x["n"], frac, v["lula"], v["flavio"]) if x["n"] else None
    )
    out["margem_95_diferenca_aas_pp"] = margem
    out["margem_95_diferenca_deff_pp"] = margem * math.sqrt(DEFF) if margem else None
    e = out["erro_validos_do_total"]["erro_f_menos_l"]
    out["erro_fora_da_margem_aas"] = abs(e) > margem if margem else None
    out["flavio_a_frente_nos_validos"] = v["flavio"] > v["lula"]
    out["acertou_vencedor"] = (v["lula"] > v["flavio"]) == (
        urna["lula"] > urna["flavio"]
    )
    return out


def ultima_por_casa(
    ondas: Iterable[dict[str, Any]], inicio: str = INICIO_ULTIMA_SEMANA
) -> list[dict[str, Any]]:
    """Última onda de cada casa com campo encerrado a partir de ``inicio``."""
    escolhida: dict[str, dict[str, Any]] = {}
    for x in ondas:
        if x["campo"]["fim"] < inicio:
            continue
        chave = (x["campo"]["fim"], x["divulgacao"] or "", x["id"])
        atual = escolhida.get(x["instituto"])
        if atual is None or chave > (
            atual["campo"]["fim"],
            atual["divulgacao"] or "",
            atual["id"],
        ):
            escolhida[x["instituto"]] = x
    return sorted(escolhida.values(), key=lambda x: x["instituto"])


def resumo(erros: list[float]) -> dict[str, Any]:
    out = P.resumo_erros(erros)
    out["amplitude"] = [min(erros), max(erros)] if erros else None
    return out


def resumo_finais(finais: list[dict[str, Any]], urna: Mapping[str, float]) -> dict:
    pub = [x["erro_validos_do_total"]["erro_f_menos_l"] for x in finais]
    of = [
        x["erro_validos_oficiais"]["erro_f_menos_l"]
        for x in finais
        if x["erro_validos_oficiais"]
    ]
    com_rep = [x for x in finais if x["erro_reponderado"]]
    se = [x["margem_95_diferenca_aas_pp"] / P.Z95 for x in finais if x["n"]]
    amostral = math.sqrt(statistics.fmean(s**2 for s in se))
    media_v = {
        k: statistics.fmean(x["validos_do_total"][k] for x in finais)
        for k in ("flavio", "lula")
    }
    return {
        "n_casas": len(finais),
        "publicado_validos_do_total": resumo(pub),
        "publicado_validos_oficiais": resumo(of),
        "n_com_validos_oficiais": len(of),
        "reponderado": resumo(
            [x["erro_reponderado"]["erro_f_menos_l"] for x in com_rep]
        ),
        "publicado_mesmas_casas_reponderadas": resumo(
            [x["erro_validos_do_total"]["erro_f_menos_l"] for x in com_rep]
        ),
        "n_reponderadas": len(com_rep),
        "desvio_esperado_so_amostragem_aas_pp": amostral,
        "desvio_esperado_so_amostragem_deff_pp": amostral * math.sqrt(DEFF),
        "fora_da_margem_aas": sum(bool(x["erro_fora_da_margem_aas"]) for x in finais),
        "flavio_a_frente_nos_validos": sum(
            x["flavio_a_frente_nos_validos"] for x in finais
        ),
        "lula_a_frente_nos_validos": sum(
            x["validos_do_total"]["lula"] > x["validos_do_total"]["flavio"]
            for x in finais
        ),
        "empates_nos_validos": sum(
            x["validos_do_total"]["lula"] == x["validos_do_total"]["flavio"]
            for x in finais
        ),
        "acertaram_vencedor": sum(x["acertou_vencedor"] for x in finais),
        "casas_que_acertaram_vencedor": [
            x["instituto"] for x in finais if x["acertou_vencedor"]
        ],
        "media_simples_validos": media_v,
        "erro_media_simples": erro(media_v, urna),
    }


def efeito_reponderacao(finais: list[dict[str, Any]]) -> dict[str, Any]:
    linhas = []
    for x in finais:
        if not x["erro_reponderado"]:
            continue
        ep = x["erro_validos_do_total"]["erro_f_menos_l"]
        er = x["erro_reponderado"]["erro_f_menos_l"]
        delta = abs(er) - abs(ep)
        linhas.append(
            {
                "id": x["id"],
                "instituto": x["instituto"],
                "perfil_renda": x["perfil_renda"],
                "erro_publicado_f_menos_l": ep,
                "erro_reponderado_f_menos_l": er,
                "deslocamento_f_menos_l": er - ep,
                "variacao_erro_absoluto": delta,
                "direcao": (
                    "aproximou"
                    if delta < -0.05
                    else "afastou" if delta > 0.05 else "neutro"
                ),
            }
        )
    return {
        "regra": "variação do erro absoluto na diferença F−L; negativa aproxima da urna",
        "por_casa": linhas,
        "n": len(linhas),
        "aproximou": sum(r["direcao"] == "aproximou" for r in linhas),
        "afastou": sum(r["direcao"] == "afastou" for r in linhas),
        "neutro": sum(r["direcao"] == "neutro" for r in linhas),
        "deslocamento_medio_f_menos_l": statistics.fmean(
            r["deslocamento_f_menos_l"] for r in linhas
        ),
        "variacao_media_erro_absoluto": statistics.fmean(
            r["variacao_erro_absoluto"] for r in linhas
        ),
    }


def por_modo(finais: list[dict[str, Any]]) -> dict[str, Any]:
    out = {}
    for m in sorted({x["modo"] for x in finais}):
        sel = [x for x in finais if x["modo"] == m]
        es = [x["erro_validos_do_total"]["erro_f_menos_l"] for x in sel]
        out[m] = {
            "n": len(sel),
            "media": statistics.fmean(es),
            "casas": {
                x["instituto"]: round(e, 3) for x, e in zip(sel, es, strict=True)
            },
        }
    return out


def _ols(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 3:
        return None
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True)) / sxx


def tendencia(ondas: list[dict[str, Any]]) -> dict[str, Any]:
    """Inclinação da diferença F−L publicada (válidos do total) por dia de campo.

    Duas contas: todas as ondas juntas (MQO simples) e dentro de cada casa
    (efeito fixo de casa: desvios em relação à média da própria casa).
    """

    def calcular(sel: list[dict[str, Any]]) -> dict[str, Any]:
        t0 = date(2026, 10, 5)
        xs = [(date.fromisoformat(x["meio_do_campo"]) - t0).days for x in sel]
        ys = [dif_fl(x["validos_do_total"]) for x in sel]
        casas: dict[str, list[int]] = {}
        for i, x in enumerate(sel):
            casas.setdefault(x["instituto"], []).append(i)
        fx, fy = [], []
        for idx in casas.values():
            if len(idx) < 2:
                continue
            mx = statistics.fmean(xs[i] for i in idx)
            my = statistics.fmean(ys[i] for i in idx)
            fx += [xs[i] - mx for i in idx]
            fy += [ys[i] - my for i in idx]
        return {
            "n_ondas": len(sel),
            "n_casas": len(casas),
            "n_casas_com_duas_ou_mais": sum(len(v) >= 2 for v in casas.values()),
            "inclinacao_simples_pp_dia": _ols([float(x) for x in xs], ys),
            "inclinacao_dentro_da_casa_pp_dia": _ols(fx, fy),
            "media_f_menos_l": statistics.fmean(ys) if ys else None,
        }

    pos = [x for x in ondas if x["campo"]["fim"] >= INICIO_POS_URNA]
    ult = [x for x in pos if x["campo"]["fim"] >= INICIO_ULTIMA_SEMANA]
    total = calcular(pos)
    meio_ult = statistics.fmean(
        date.fromisoformat(x["meio_do_campo"]).toordinal() for x in ult
    )
    dias = ELEICAO.toordinal() - meio_ult
    media_ult = statistics.fmean(dif_fl(x["validos_do_total"]) for x in ult)
    inc = total["inclinacao_dentro_da_casa_pp_dia"] or 0.0
    primeira = [x for x in pos if x["campo"]["fim"] <= "2026-10-12"]
    serie = sorted(
        (
            {
                "id": x["id"],
                "instituto": x["instituto"],
                "meio_do_campo": x["meio_do_campo"],
                "f_menos_l_validos": dif_fl(x["validos_do_total"]),
            }
            for x in pos
        ),
        key=lambda r: (r["meio_do_campo"], r["id"]),
    )
    return {
        "regra": (
            "diferença F−L nos válidos do total publicado contra o meio do campo; "
            "positivo na inclinação quer dizer Flávio ganhando terreno"
        ),
        "pos_urna_05_a_24": total,
        "extrapolacao_ate_a_urna": {
            "regra": (
                "média F−L da última semana levada à urna pela inclinação dentro da "
                "casa de 05 a 24/10; ilustração, não previsão"
            ),
            "dias_do_meio_do_campo_ate_a_urna": dias,
            "media_ultima_semana": media_ult,
            "f_menos_l_extrapolado": media_ult + inc * dias,
        },
        "ultima_semana_19_a_24": calcular(ult),
        "media_campo_ate_12_10": statistics.fmean(
            dif_fl(x["validos_do_total"]) for x in primeira
        ),
        "media_campo_desde_19_10": media_ult,
        "serie": serie,
    }


def centrais(sim: dict[str, Any], urna: Mapping[str, float]) -> dict[str, Any]:
    """Média Arvor, Projeção Arvor e âncoras do snapshot publicado."""
    proj = sim["projection"]
    out: dict[str, Any] = {
        "snapshot": sim.get("version"),
        "referencia": sim.get("reference"),
    }
    for chave, rotulo, bloco in (
        ("media_arvor", "Média Arvor", sim["central"]),
        ("projecao_arvor", "Projeção Arvor", sim["central_projection"]),
    ):
        v = {"flavio": bloco["flavio"], "lula": bloco["lula"]}
        out[chave] = {
            "rotulo": rotulo,
            "validos": v,
            "parametros": bloco.get("parametros"),
            **erro(v, urna),
        }
    for nome, vet in proj["anchors"].items():
        v, _ = P.validos(vet)
        tr = proj["trend"].get(nome) or {}
        out[f"ancora_projecao_{nome}"] = {
            "rotulo": (
                f"Âncora da Projeção ({nome}): recência e tendência encolhida, "
                "antes da presença relativa"
            ),
            "inclinacao_lula_validos_pp_dia": (
                tr.get("inclinacoes_encolhidas_validos_pp_dia") or {}
            ).get("lula"),
            "validos": v,
            **erro(v, urna),
        }
    out["presenca_relativa_pct"] = (sim.get("presence_model") or {}).get(
        "central_extra_pct"
    )
    return out


def presenca_declarada(
    finais: list[dict[str, Any]], presenca: dict[str, Any], urna: Mapping[str, float]
) -> list[dict[str, Any]]:
    """Seleção por presença declarada nas ondas que a publicam por voto atual."""
    out = []
    for x in finais:
        taxas = ((presenca.get("ondas") or {}).get(x["id"]) or {}).get("taxas")
        if not taxas:
            continue
        t = x["publicado_total"]
        f, lu = t["flavio"] * taxas["flavio"], t["lula"] * taxas["lula"]
        v = {"flavio": 100 * f / (f + lu), "lula": 100 * lu / (f + lu)}
        out.append(
            {
                "id": x["id"],
                "instituto": x["instituto"],
                "taxas": taxas,
                "validos_amostra_completa": x["validos_do_total"],
                "validos_presenca_declarada": v,
                "deslocamento_f_menos_l": dif_fl(v) - dif_fl(x["validos_do_total"]),
                **erro(v, urna),
            }
        )
    return out


def indecisos_extremo(
    finais: list[dict[str, Any]], urna: Mapping[str, float]
) -> dict[str, Any]:
    """Limite: todo indeciso (e, no segundo cenário, todo branco/nulo) para Lula."""
    linhas = []
    for x in finais:
        t = x["publicado_total"]
        ind = t.get("indecisos", 0.0) + t.get("ns_nr", 0.0) + t.get("nao_sabe", 0.0)
        bn = t.get("branco_nulo", 0.0)
        f, lu = t["flavio"], t["lula"]
        v1 = {
            "flavio": 100 * f / (f + lu + ind),
            "lula": 100 * (lu + ind) / (f + lu + ind),
        }
        tot = f + lu + ind + bn
        v2 = {"flavio": 100 * f / tot, "lula": 100 * (lu + ind + bn) / tot}
        linhas.append(
            {
                "id": x["id"],
                "instituto": x["instituto"],
                "indecisos_pct": ind,
                "branco_nulo_pct": bn,
                "f_menos_l_todos_indecisos_lula": dif_fl(v1),
                "erro_todos_indecisos_lula": dif_fl(v1) - dif_fl(urna),
                "f_menos_l_indecisos_e_bn_lula": dif_fl(v2),
            }
        )
    return {
        "regra": "cenário extremo, não hipótese provável: indecisos inteiros para Lula",
        "por_casa": linhas,
        "flavio_ainda_a_frente": sum(
            r["f_menos_l_todos_indecisos_lula"] > 0 for r in linhas
        ),
        "erro_medio_todos_indecisos_lula": statistics.fmean(
            r["erro_todos_indecisos_lula"] for r in linhas
        ),
        "flavio_ainda_a_frente_com_bn": sum(
            r["f_menos_l_indecisos_e_bn_lula"] > 0 for r in linhas
        ),
    }


def painel_1t(finais: list[dict[str, Any]], pesq_1t: dict[str, Any]) -> dict[str, Any]:
    """Mesma casa nos dois turnos, no sinal L−F do 1º turno."""
    um = {x["instituto"]: x for x in pesq_1t["pesquisas"] if x["ultima_onda_da_casa"]}
    linhas = []
    for x in finais:
        a = um.get(x["instituto"])
        if a is None:
            continue
        linhas.append(
            {
                "instituto": x["instituto"],
                "id_1t": a["id"],
                "id_2t": x["id"],
                "erro_1t_lula_menos_flavio": a["publicado"][
                    "diferenca_lula_menos_flavio"
                ]["erro"],
                "erro_2t_lula_menos_flavio": x["erro_validos_do_total"][
                    "erro_lula_menos_flavio"
                ],
            }
        )
    xs = [r["erro_1t_lula_menos_flavio"] for r in linhas]
    ys = [r["erro_2t_lula_menos_flavio"] for r in linhas]
    return {
        "regra": "última onda de cada casa nos dois turnos; erro L−F, positivo superestima Lula",
        "linhas": linhas,
        "n": len(linhas),
        "correlacao": statistics.correlation(xs, ys) if len(xs) > 2 else None,
        "media_1t": statistics.fmean(xs) if xs else None,
        "media_2t": statistics.fmean(ys) if ys else None,
        "inverteram_sinal": sum(
            (a > 0) != (b > 0) for a, b in zip(xs, ys, strict=True)
        ),
    }


def multiplicador_necessario(
    v: Mapping[str, float], urna: Mapping[str, float]
) -> float:
    """Variação relativa da razão F/L que leva um placar à urna, em %.

    Mesma fórmula da presença relativa da casa: 100 × [(F/L urna) / (F/L placar) − 1].
    A conta não distingue presença diferencial de erro de medição: as duas mudam a
    razão F/L do mesmo jeito.
    """
    return 100 * (
        (urna["flavio"] / urna["lula"]) / (float(v["flavio"]) / float(v["lula"])) - 1
    )


def indecisos_divisao(
    finais: list[dict[str, Any]], urna: Mapping[str, float], parte_flavio: float
) -> dict[str, Any]:
    """Indecisos repartidos numa proporção fixa entre os dois, em cada casa."""
    erros = []
    for x in finais:
        t = x["publicado_total"]
        ind = t.get("indecisos", 0.0) + t.get("ns_nr", 0.0) + t.get("nao_sabe", 0.0)
        f = t["flavio"] + parte_flavio * ind
        lu = t["lula"] + (1 - parte_flavio) * ind
        v = {"flavio": 100 * f / (f + lu), "lula": 100 * lu / (f + lu)}
        erros.append(dif_fl(v) - dif_fl(urna))
    return {
        "parte_flavio": parte_flavio,
        "indecisos_medios_pct": statistics.fmean(
            x["publicado_total"].get("indecisos", 0.0) for x in finais
        ),
        "erro_medio_f_menos_l": statistics.fmean(erros),
        "erro_medio_sem_redistribuir": statistics.fmean(
            x["erro_validos_do_total"]["erro_f_menos_l"] for x in finais
        ),
    }
