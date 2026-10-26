"""A noite no relógio: linha do tempo, pausas, regressões, latência e cedo × tarde."""

from __future__ import annotations

from collections import defaultdict
from datetime import timedelta
from itertools import pairwise
from typing import Any

from apuracao_2026.dados import utc

from .base import (
    ELE_PRES,
    ROTULO,
    ROTULO_PAUSA,
    SQ_FLAVIO,
    SQ_LULA,
    T0,
    brt,
    colunar,
    d2,
    hhmm,
    mediana,
    minuto,
    p2,
    quantil,
    r2,
    spearman,
    totalizado_corrigido,
)
from .carga import Contexto
from .fontes import zonas_1t

LIMIAR_NACIONAL_MIN = 5.0
LIMIAR_UF_MIN = 10.0
FIM_VOTACAO_MIN = 120.0  # 19:00 de Brasília, depois da prorrogação


def _serie(versoes: list[dict[str, Any]], uf: str) -> list[dict[str, Any]]:
    saida = []
    ant: dict[str, Any] | None = None
    for v in versoes:
        f = v["votos"].get(SQ_FLAVIO, 0)
        l_ = v["votos"].get(SQ_LULA, 0)
        linha = {
            "min": minuto(v["gerado_em"]),
            "gerado_brt": brt(v["gerado_em"]),
            "totalizado_corrigido_brt": brt(
                totalizado_corrigido(uf, v["totalizado_em"], v["gerado_em"])
            ),
            "st": v["st"],
            "pst": r2(v["pst"]),
            "validos": v["vv"],
            "flavio": f,
            "lula": l_,
            "pct_flavio": p2(f, v["vv"]),
            "pct_lula": p2(l_, v["vv"]),
            "comparecimento": v["comparecimento"],
            "abstencao": v["abstencao"],
            "pct_abstencao": p2(
                v["abstencao"], (v["comparecimento"] or 0) + (v["abstencao"] or 0)
            ),
            "lote_st": v["st"] - ant["st"] if ant else v["st"],
            "lote_flavio": f - ant["flavio"] if ant else f,
            "lote_lula": l_ - ant["lula"] if ant else l_,
            "lote_pct_flavio": None,
            "minutos_desde_anterior": (
                round(
                    (utc(v["gerado_em"]) - utc(ant["gerado_em"])).total_seconds() / 60,
                    1,
                )
                if ant
                else None
            ),
            "gerado_em": v["gerado_em"],
        }
        lv = linha["lote_flavio"] + linha["lote_lula"]
        linha["lote_pct_flavio"] = p2(linha["lote_flavio"], lv) if lv > 0 else None
        saida.append(linha)
        ant = linha
    return saida


def _lacunas(
    serie: list[dict[str, Any]], limiar: float, ts: int
) -> list[dict[str, Any]]:
    """Intervalos entre gerações consecutivas maiores que o limiar, com contagem aberta."""
    saida = []
    for a, b in pairwise(serie):
        dur = b["minutos_desde_anterior"]
        if dur is not None and dur > limiar and 0 < a["st"] < ts:
            saida.append(
                {
                    "de_brt": a["gerado_brt"],
                    "ate_brt": b["gerado_brt"],
                    "de_min": a["min"],
                    "ate_min": b["min"],
                    "minutos": dur,
                    "st_antes": a["st"],
                    "st_depois": b["st"],
                }
            )
    return saida


COLUNAS_SERIE = (
    "min",
    "gerado_brt",
    "totalizado_corrigido_brt",
    "st",
    "pst",
    "validos",
    "flavio",
    "lula",
    "pct_flavio",
    "pct_lula",
    "comparecimento",
    "pct_abstencao",
    "lote_st",
    "lote_flavio",
    "lote_lula",
    "lote_pct_flavio",
    "minutos_desde_anterior",
)


def linha_do_tempo(ctx: Contexto) -> dict[str, Any]:
    banco = ctx.banco
    vs_br = banco.versoes(ELE_PRES, "br")
    vs_uf = banco.versoes(ELE_PRES, "uf")
    arq_uf = {a["id"]: a["uf"].upper() for a in banco.arquivos(ELE_PRES, "uf")}
    br_serie = _serie(next(iter(vs_br.values())), "br")
    ts_br = ctx.br["ts"]
    ufs = {}
    fechou_uf = []
    lacunas_uf = []
    marcos = ctx.ref["marcos"]["uf"]
    for arq_id, vs in vs_uf.items():
        uf = arq_uf[arq_id]
        serie = _serie(vs, uf.lower())
        ufs[uf] = colunar(COLUNAS_SERIE, serie)
        ts = vs[-1]["ts"]
        fim = next((s for s in serie if s["st"] >= ts > 0), None)
        ref = marcos.get(uf, {})
        fechou_uf.append(
            {
                "uf": uf,
                "fechou_min": fim["min"] if fim else None,
                "fechou_brt": fim["gerado_brt"] if fim else None,
                "fechou_min_apos_fim_votacao": (
                    r2(fim["min"] - FIM_VOTACAO_MIN) if fim else None
                ),
                "t1_p100_min": ref.get("p100"),
                "t1_p100_hhmm": ref.get("p100_hhmm"),
                "t1_p50_min": ref.get("p50"),
                "atraso_vs_1t_min": (
                    r2(fim["min"] - ref["p100"]) if fim and ref.get("p100") else None
                ),
                "atraso_vs_1t_descontada_prorrogacao_min": (
                    r2(fim["min"] - FIM_VOTACAO_MIN - ref["p100"])
                    if fim and ref.get("p100")
                    else None
                ),
                "versoes": len(serie),
            }
        )
        for lac in _lacunas(serie, LIMIAR_UF_MIN, ts):
            lacunas_uf.append({"uf": uf, **lac})
    fechou_uf.sort(key=lambda r: (r["fechou_min"] is None, r["fechou_min"] or 0))
    pausas_tabela = banco.linhas("SELECT * FROM pausa ORDER BY de")
    for p in pausas_tabela:
        p["de_brt"] = brt(p["de"])
        p["ate_brt"] = brt(p["ate"])
        p["de_min"] = minuto(p["de"])
        p["ate_min"] = minuto(p["ate"])
        if p["uf"]:
            p["uf"] = p["uf"].upper()
    geral = next((p for p in pausas_tabela if p["nivel"] == "geral"), None)
    lac_nac = _lacunas(br_serie, LIMIAR_NACIONAL_MIN, ts_br)
    maior = max(lac_nac, key=lambda x: x["minutos"]) if lac_nac else None
    silencio = None
    if maior:
        meio = (
            T0 + timedelta(minutes=(maior["de_min"] + maior["ate_min"]) / 2)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")
        ultimo = banco.um(
            "SELECT MAX(gerado_em) FROM snapshot WHERE gerado_em < ?", (meio,)
        )
        primeiro = banco.um(
            "SELECT MIN(gerado_em) FROM snapshot WHERE gerado_em > ?", (meio,)
        )
        silencio = {
            "nota": (
                "intervalo em que nenhum arquivo de nenhum tipo (resultado, andamento, "
                "configuração) dos dois pleitos tem hora de geração; as leituras do "
                "coletor no intervalo trouxeram versões geradas antes dele"
            ),
            "ultimo_gerado_antes_brt": brt(ultimo),
            "primeiro_gerado_depois_brt": brt(primeiro),
            "minutos": round((utc(primeiro) - utc(ultimo)).total_seconds() / 60, 1),
            "versoes_geradas_dentro": banco.um(
                "SELECT COUNT(*) FROM snapshot WHERE gerado_em > ? AND gerado_em < ?",
                (ultimo, primeiro),
            ),
            "leituras_no_intervalo": banco.um(
                "SELECT COUNT(*) FROM fetch WHERE iniciado_em > ? AND iniciado_em < ?",
                (ultimo, primeiro),
            ),
            "leituras_por_classe": {
                r["classe"]: r["n"]
                for r in banco.linhas(
                    "SELECT classe, COUNT(*) AS n FROM fetch WHERE iniciado_em > ? "
                    "AND iniciado_em < ? GROUP BY classe",
                    (ultimo, primeiro),
                )
            },
        }
    antes = [s for s in br_serie if maior and s["min"] <= maior["de_min"]]
    depois = [s for s in br_serie if maior and s["min"] >= maior["ate_min"]]
    return {
        "rotulo": ROTULO,
        "rotulo_pausa": ROTULO_PAUSA,
        "relogio": (
            "min = minutos após 17:00 de Brasília (25/10/2026) pela hora de geração "
            "do arquivo (gerado_em); a votação terminou às 19:00 (min 120) depois da "
            "prorrogação; totalizado_corrigido_brt corrige o fuso de AC, AM, RO, RR, "
            "MT e MS"
        ),
        "contexto_externo": {
            "prorrogacao_stf": (
                "decisão do STF (ministro Cristiano Zanin) prorrogou a votação até 19h "
                "em todo o país, informada por volta de 17:03 a 17:08; o horário vem do "
                "noticiário da noite, não do banco"
            ),
            "o_que_o_banco_mostra": (
                "a última versão nacional antes da parada foi gerada às "
                f"{antes[-1]['gerado_brt'] if antes else None} com {antes[-1]['st'] if antes else None} "
                "seções; a seguinte, às "
                f"{depois[0]['gerado_brt'] if depois else None} com {depois[0]['st'] if depois else None}"
            ),
        },
        "nacional": {
            "arquivo": ctx.br["chave"],
            "versoes_genuinas": len(br_serie),
            "serie": colunar(COLUNAS_SERIE, br_serie),
            "primeira_com_secoes": next((s for s in br_serie if s["st"] > 0), None),
            "final": br_serie[-1],
        },
        "ufs": ufs,
        "pausas": {
            "tabela_do_coletor": pausas_tabela,
            "parada_geral": geral,
            "silencio_geral": silencio,
            "maior_lacuna_nacional": maior,
            "lacunas_nacional": lac_nac,
            "lacunas_uf": lacunas_uf,
            "regra": (
                f"lacuna nacional > {LIMIAR_NACIONAL_MIN} min e de UF > {LIMIAR_UF_MIN} min "
                "entre gerações consecutivas de versões novas, com a contagem iniciada e "
                "incompleta"
            ),
        },
        "conclusao_ufs": fechou_uf,
        "regressoes": regressoes(ctx),
        "latencia": latencia(ctx),
        "eventos_por_tipo": banco.linhas(
            "SELECT tipo, severidade, COUNT(*) AS n FROM evento GROUP BY tipo, severidade "
            "ORDER BY tipo"
        ),
    }


def regressoes(ctx: Contexto) -> dict[str, Any]:
    """Versões marcadas regressivas pelo coletor e regressões de contagem."""
    banco = ctx.banco
    saida: dict[str, Any] = {"por_nivel": {}, "contagem_regressiva": []}
    for nivel in ("br", "uf", "mu", "zona"):
        todas = banco.todas_versoes(ELE_PRES, nivel)
        classes = {
            "mais_nova_que_todas_as_anteriores": 0,
            "mesma_geracao": 0,
            "copia_antiga": 0,
        }
        for vs in todas.values():
            maior = None
            for v in vs:
                g = v["gerado_em"]
                if v["regressivo"]:
                    if maior is None or g > maior:
                        classes["mais_nova_que_todas_as_anteriores"] += 1
                    elif g == maior:
                        classes["mesma_geracao"] += 1
                    else:
                        classes["copia_antiga"] += 1
                if g and (maior is None or g > maior):
                    maior = g
        saida["por_nivel"][nivel] = {
            "capturas": sum(len(v) for v in todas.values()),
            "marcadas_regressivas": sum(classes.values()),
            **classes,
        }
        genuinas = banco.versoes(ELE_PRES, nivel, com_votos=False)
        arqs = {a["id"]: a for a in banco.arquivos(ELE_PRES, nivel)}
        for arq_id, vs in genuinas.items():
            for a, b in pairwise(vs):
                if b["st"] < a["st"] or (b["comparecimento"] or 0) < (
                    a["comparecimento"] or 0
                ):
                    arq = arqs[arq_id]
                    saida["contagem_regressiva"].append(
                        {
                            "nivel": nivel,
                            "uf": (arq["uf"] or "").upper(),
                            "municipio_cd": arq["municipio_cd"],
                            "zona_cd": arq["zona_cd"],
                            "de_brt": brt(a["gerado_em"]),
                            "para_brt": brt(b["gerado_em"]),
                            "st_antes": a["st"],
                            "st_depois": b["st"],
                            "comparecimento_antes": a["comparecimento"],
                            "comparecimento_depois": b["comparecimento"],
                        }
                    )
    saida["nota"] = (
        "Marcada regressiva = o contador idg caiu; pela hora de geração, a versão pode "
        "ser mais nova que todas as anteriores. Contagem regressiva = versão genuína "
        "(gerada depois de todas as anteriores) com menos seções ou menos comparecimento "
        "que a anterior."
    )
    return saida


def latencia(ctx: Contexto) -> dict[str, Any]:
    """Segundos entre a geração no TSE e a primeira captura, por nível e por hora."""
    banco = ctx.banco
    linhas = banco.linhas(
        "SELECT a.nivel, s.gerado_em, MIN(s.capturado_em) AS cap FROM snapshot s "
        "JOIN arquivo a ON a.id = s.arquivo_id WHERE a.tipo = 'u' AND a.eleicao_cd = ? "
        "AND s.gerado_em >= '2026-10-25T19:30' GROUP BY s.arquivo_id, s.gerado_em",
        (ELE_PRES,),
    )
    grupos: dict[tuple[str, str], list[float]] = defaultdict(list)
    por_nivel: dict[str, list[float]] = defaultdict(list)
    for r in linhas:
        seg = (utc(r["cap"]) - utc(r["gerado_em"])).total_seconds()
        hora = brt(r["gerado_em"])[:13] + "h"
        grupos[(hora, r["nivel"])].append(seg)
        por_nivel[r["nivel"]].append(seg)

    def est(v: list[float]) -> dict[str, Any]:
        return {
            "n": len(v),
            "p50_s": r2(quantil(v, 0.5)),
            "p95_s": r2(quantil(v, 0.95)),
            "max_s": r2(max(v)),
        }

    return {
        "nota": (
            "Segundos entre a geração do arquivo no TSE (gerado_em) e a primeira captura "
            "pelo coletor. Inclui o intervalo de sondagem (30 s no nacional, mais nos "
            "níveis menores): é teto da demora de publicação, não medida dela. Versões "
            "geradas durante a parada e capturadas só depois inflam o máximo."
        ),
        "por_nivel": {k: est(v) for k, v in por_nivel.items()},
        "por_hora": [
            {"hora_brt": h, "nivel": n, **est(v)}
            for (h, n), v in sorted(grupos.items())
        ],
    }


# ---------------------------------------------------------------- cedo e tarde


def _decis(valores: list[dict[str, Any]], chave: str) -> list[list[dict[str, Any]]]:
    ordem = sorted(valores, key=lambda r: r[chave])
    n = len(ordem)
    return [ordem[i * n // 10 : (i + 1) * n // 10] for i in range(10)]


def _resumo_grupo(lista: list[dict[str, Any]], ctx: Contexto) -> dict[str, Any]:
    f = sum(r["flavio"] for r in lista)
    l_ = sum(r["lula"] for r in lista)
    vv = sum(r["validos"] for r in lista)
    comp = sum(r["comparecimento"] for r in lista)
    abst = sum(r["abstencao"] for r in lista)
    com1 = [ctx.mun_1t[r["cd_tse"]] for r in lista if r["cd_tse"] in ctx.mun_1t]
    f1 = sum(m["flavio"] for m in com1)
    l1 = sum(m["lula"] for m in com1)
    v1 = sum(m["validos"] for m in com1)
    e1 = sum(m["eleitores"] for m in com1)
    a1 = sum(m["abstencao"] for m in com1)
    mins = [r["fechou_min"] for r in lista]
    mins1 = [r["t1_fechou_min"] for r in lista if r.get("t1_fechou_min") is not None]
    h2 = p2(f, f + l_)
    h1 = p2(f1, f1 + l1)
    return {
        "n": len(lista),
        "aptos": sum(r["aptos"] for r in lista),
        "aptos_mediana": mediana([r["aptos"] for r in lista]),
        "fechou_min_de": min(mins) if mins else None,
        "fechou_min_ate": max(mins) if mins else None,
        "fechou_hhmm_de": hhmm(min(mins)) if mins else None,
        "fechou_hhmm_ate": hhmm(max(mins)) if mins else None,
        "flavio": f,
        "lula": l_,
        "validos": vv,
        "pct_flavio": p2(f, vv),
        "pct_lula": p2(l_, vv),
        "h2h_flavio": h2,
        "comparecimento": comp,
        "pct_abstencao": p2(abst, comp + abst),
        "t1_flavio": f1,
        "t1_lula": l1,
        "t1_pct_flavio": p2(f1, v1),
        "t1_pct_lula": p2(l1, v1),
        "t1_h2h_flavio": h1,
        "swing_h2h_flavio_pp": d2(h2, h1),
        "t1_pct_abstencao": p2(a1, e1),
        "delta_abstencao_pp": d2(p2(abst, comp + abst), p2(a1, e1)),
        "t1_fechou_min_mediana": r2(mediana(mins1)),
        "capitais": sum(1 for r in lista if r.get("capital")),
    }


def cedo_tarde(ctx: Contexto, municipios: list[dict[str, Any]]) -> dict[str, Any]:
    base = []
    for m in municipios:
        if m["uf"] == "ZZ" or m["fechou_min"] is None:
            continue
        base.append({**m, "t1_fechou_min": ctx.fechou_1t.get(m["cd_tse"])})
    decis = _decis(base, "fechou_min")
    tabela = []
    for i, d in enumerate(decis, start=1):
        tabela.append({"decil": i, **_resumo_grupo(d, ctx)})
    # mesmo recorte pelo relógio do 1º turno
    com1 = [r for r in base if r["t1_fechou_min"] is not None]
    decis1 = _decis(com1, "t1_fechou_min")
    tabela_1t = []
    for i, d in enumerate(decis1, start=1):
        g = _resumo_grupo(d, ctx)
        g["t1_fechou_min_de"] = min(r["t1_fechou_min"] for r in d)
        g["t1_fechou_min_ate"] = max(r["t1_fechou_min"] for r in d)
        tabela_1t.append({"decil_1t": i, **g})
    # transição entre os decis do 1º e do 2º turno
    pos2 = {r["cd_tse"]: i for i, d in enumerate(decis, start=1) for r in d}
    pos1 = {r["cd_tse"]: i for i, d in enumerate(decis1, start=1) for r in d}
    matriz = [[0] * 10 for _ in range(10)]
    for cd, i1 in pos1.items():
        if cd in pos2:
            matriz[i1 - 1][pos2[cd] - 1] += 1
    rho = spearman(
        [r["t1_fechou_min"] for r in com1],
        [r["fechou_min"] for r in com1],
    )
    rho_tamanho = spearman([r["aptos"] for r in base], [r["fechou_min"] for r in base])
    ultimos = sorted(base, key=lambda r: -r["fechou_min"])[:50]
    lista_ultimos = []
    for r in ultimos:
        m1 = ctx.mun_1t.get(r["cd_tse"], {})
        h1 = (
            p2(m1.get("flavio"), (m1.get("flavio") or 0) + (m1.get("lula") or 0))
            if m1
            else None
        )
        h2 = p2(r["flavio"], r["flavio"] + r["lula"])
        lista_ultimos.append(
            {
                "cd_tse": r["cd_tse"],
                "uf": r["uf"],
                "nome": r["nome"],
                "aptos": r["aptos"],
                "fechou_min": r["fechou_min"],
                "fechou_hhmm": r["fechou_hhmm"],
                "t1_fechou_min": r["t1_fechou_min"],
                "pct_flavio": r["pct_flavio"],
                "pct_lula": r["pct_lula"],
                "t1_pct_flavio": (
                    p2(m1.get("flavio"), m1.get("validos")) if m1 else None
                ),
                "t1_pct_lula": p2(m1.get("lula"), m1.get("validos")) if m1 else None,
                "h2h_flavio": h2,
                "t1_h2h_flavio": h1,
                "swing_h2h_flavio_pp": d2(h2, h1),
                "pct_abstencao": r["pct_abstencao"],
            }
        )
    # zonas
    zonas = []
    z1 = zonas_1t()
    for z in ctx.zonas:
        fe = ctx.fechou_zona.get((z["municipio_cd"], int(z["zona_cd"])))
        if fe is None or (z["uf"] or "").lower() == "zz":
            continue
        f = z["votos"].get(SQ_FLAVIO, 0)
        l_ = z["votos"].get(SQ_LULA, 0)
        r1 = z1.get((z["municipio_cd"], int(z["zona_cd"])))
        zonas.append(
            {
                "fechou_min": fe["min"],
                "aptos": z["te"],
                "flavio": f,
                "lula": l_,
                "validos": z["vv"],
                "comparecimento": z["comparecimento"],
                "abstencao": z["abstencao"],
                "t1": r1,
            }
        )
    tabela_zonas = []
    for i, d in enumerate(_decis(zonas, "fechou_min"), start=1):
        f = sum(r["flavio"] for r in d)
        l_ = sum(r["lula"] for r in d)
        com = [r for r in d if r["t1"]]
        f1 = sum(r["t1"]["flavio"] for r in com)
        l1 = sum(r["t1"]["lula"] for r in com)
        comp = sum(r["comparecimento"] for r in d)
        ab = sum(r["abstencao"] for r in d)
        tabela_zonas.append(
            {
                "decil": i,
                "n": len(d),
                "aptos": sum(r["aptos"] for r in d),
                "fechou_hhmm_de": hhmm(min(r["fechou_min"] for r in d)),
                "fechou_hhmm_ate": hhmm(max(r["fechou_min"] for r in d)),
                "h2h_flavio": p2(f, f + l_),
                "t1_h2h_flavio": p2(f1, f1 + l1),
                "swing_h2h_flavio_pp": d2(p2(f, f + l_), p2(f1, f1 + l1)),
                "pct_abstencao": p2(ab, comp + ab),
                "n_com_1t": len(com),
            }
        )
    return {
        "rotulo": ROTULO,
        "definicoes": {
            "fechou_min": (
                "minutos após 17:00 de Brasília da primeira versão gerada com todas as "
                "seções do município; a votação terminou às 19:00 (min 120)"
            ),
            "decis": "municípios do país (sem exterior) ordenados pelo minuto em que fecharam, em dez grupos de mesmo número de municípios",
            "h2h": "parte de Flávio entre os dois finalistas; no 1º turno, entre Flávio e Lula",
            "leitura": (
                "o nível de h2h_flavio em cada decil mostra a composição de quem entrou "
                "naquela hora; swing_h2h_flavio_pp, a mudança contra o 1º turno nos "
                "mesmos municípios. Decil tardio com nível diferente e swing igual ao "
                "dos demais é efeito de composição (municípios grandes ou remotos), não "
                "mudança de voto"
            ),
            "t1_fechou_min": "minutos após 17:00 de 04/10 (régua referencia_1t.json); no 1º turno a votação terminou às 17:00",
        },
        "decis_2t": tabela,
        "decis_1t_mesmos_municipios": tabela_1t,
        "transicao_decil_1t_para_2t": {
            "linhas": "decil no 1º turno (1 = fechou mais cedo)",
            "colunas": "decil no 2º turno",
            "matriz": matriz,
        },
        "spearman_ordem_1t_x_2t": rho,
        "spearman_tamanho_x_fechamento_2t": rho_tamanho,
        "n_municipios": len(base),
        "ultimos_50": lista_ultimos,
        "zonas": {
            "nota": (
                "zonas eleitorais do país pelo minuto em que fecharam no 2º turno; "
                "1º turno das mesmas zonas por código TSE do município e número da zona "
                "(analysis/apuracao_2026/dados/zonas.json)"
            ),
            "n": len(zonas),
            "decis": tabela_zonas,
        },
    }
