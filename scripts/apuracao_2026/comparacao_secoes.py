"""Presidente e Câmara: 2022 contra 2026, por UF, região e Brasil."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from .comparacao import (
    CAMPOS,
    CAMPOS_PRES,
    INDEFINIDO,
    agregar,
    campo_historico,
    campo_teto_direita,
    contar,
    diferenca,
    eleito,
    fatia,
    membros_regionais,
    metricas_presidente,
    normalizar_sigla,
    normalizar_texto,
    por_bloco,
    por_campo,
    proporcionalidade,
    sigla_2026,
    trocas_de_bloco,
)
from .comparacao_fontes import Fontes
from .contexto import NOME_UF, UFS
from .dados import grupo_regional, regiao
from .tse_cargos import DEPUTADO_FEDERAL

AGREGADOS = (
    "Nordeste",
    "Norte",
    "Centro-Sul",
    "Centro-Oeste",
    "Sudeste",
    "Sul",
    "Exterior",
    "Brasil sem exterior",
    "Brasil",
)
GRUPOS_DA_SOMA = ("Nordeste", "Norte", "Centro-Sul", "Exterior")
LIMIARES_CAMARA = {"maioria_absoluta": 257, "tres_quintos": 308}
UFS_MAIUSC = [u.upper() for u in UFS]


# ---------------------------------------------------------------- presidente


def _linha_presidente(f: Fontes, uf: str) -> dict[str, int]:
    linha = dict(f.pres26[uf])
    for t in (1, 2):
        a = f.api2022[uf.lower()][t]
        linha[f"e22_{t}"] = a["eleitores"]
        linha[f"c22_{t}"] = a["comparecimento"]
        linha[f"a22_{t}"] = a["abstencao"]
        linha[f"vv22_{t}"] = a["validos"]
        linha[f"vb22_{t}"] = a["brancos"]
        linha[f"vn22_{t}"] = a["nulos"]
        linha[f"bolsonaro_{t}"] = a["votos"].get("22", 0)
        linha[f"lula22_{t}"] = a["votos"].get("13", 0)
    a1 = f.api2022[uf.lower()][1]
    linha["ciro_1"] = a1["votos"].get("12", 0)
    linha["tebet_1"] = a1["votos"].get("15", 0)
    linha["outros22_1"] = (
        a1["validos"]
        - linha["bolsonaro_1"]
        - linha["lula22_1"]
        - linha["ciro_1"]
        - linha["tebet_1"]
    )
    if linha["outros22_1"] < 0:
        raise ValueError(f"{uf}: soma das candidaturas de 2022 acima dos válidos")
    return linha


def _item_2t(x: dict[str, Any]) -> dict[str, Any]:
    return {
        "uf": x["uf"],
        "nome": x["nome"],
        "grupo": x["grupo"],
        "pct_flavio_2026": x["pct_2026"]["flavio"],
        "pct_bolsonaro_2022_2t": x["pct_2022_2t"]["bolsonaro"],
        "pct_bolsonaro_2022_1t": x["pct_2022_1t"]["bolsonaro"],
        "pp": x["flavio_menos_bolsonaro_2t_pp"],
        "votos": x["flavio_menos_bolsonaro_2t_votos"],
        "votos_equivalentes": x["flavio_menos_bolsonaro_2t_votos_equivalentes"],
    }


def _conferencia_presidente(f: Fontes, brasil: dict[str, Any]) -> dict[str, Any]:
    """Soma das 28 UFs contra os arquivos nacionais (2022) e o boletim (2026)."""
    saida: dict[str, Any] = {}
    for t, rotulo in ((1, "votos_2022_1t"), (2, "votos_2022_2t")):
        br = f.api2022["br"][t]
        soma = brasil[rotulo]
        saida[f"soma_ufs_menos_br_2022_{t}t"] = {
            "eleitorado": soma["eleitorado"] - br["eleitores"],
            "comparecimento": soma["comparecimento"] - br["comparecimento"],
            "abstencao": soma["abstencao"] - br["abstencao"],
            "validos": soma["validos"] - br["validos"],
            "bolsonaro": soma["bolsonaro"] - br["votos"].get("22", 0),
            "lula": soma["lula"] - br["votos"].get("13", 0),
        }
    fora = {}
    for uf in [*UFS, "zz", "br"]:
        for t in (1, 2):
            a = f.api2022[uf][t]
            resto = a["eleitores"] - a["comparecimento"] - a["abstencao"]
            if resto:
                fora[f"{uf.upper()}_{t}t"] = resto
    saida["eleitores_2022_fora_de_comparecimento_e_abstencao"] = fora
    saida["nota_abstencao"] = (
        "abstenção é o campo `a` do TSE nos dois anos; onde ele difere de eleitorado "
        "menos comparecimento, a sobra é de eleitores de seções sem votação"
    )
    pres = f.final["presidente"]
    v26 = brasil["votos_2026"]
    saida["soma_ufs_menos_final_json_2026"] = {
        "eleitorado": v26["eleitorado"] - pres["eleitores"],
        "comparecimento": v26["comparecimento"] - pres["comparecimento"],
        "abstencao": v26["abstencao"] - pres["abstencao"],
        "validos": v26["validos"] - pres["validos"],
        "brancos": v26["brancos"] - pres["brancos"],
        "nulos": v26["nulos"] - pres["nulos"],
    }
    return saida


def presidente(f: Fontes) -> dict[str, Any]:
    ufs = [*UFS_MAIUSC, "ZZ"]
    linhas = {uf: _linha_presidente(f, uf) for uf in ufs}
    membros = membros_regionais(ufs)
    somas = agregar(linhas, CAMPOS_PRES, membros)
    por_uf = [
        {
            "uf": uf,
            "nome": NOME_UF[uf.lower()],
            "regiao": regiao(uf),
            "grupo": grupo_regional(uf),
            **metricas_presidente(linhas[uf]),
        }
        for uf in ufs
    ]
    agregados = {
        nome: {"ufs": membros[nome], **metricas_presidente(somas[nome])}
        for nome in AGREGADOS
    }
    brasil = agregados["Brasil"]
    estados = [x for x in por_uf if x["uf"] != "ZZ"]
    acima = sorted(
        (x for x in estados if x["flavio_supera_bolsonaro_2t"]),
        key=lambda x: (-x["flavio_menos_bolsonaro_2t_pp"], x["uf"]),
    )
    abaixo = sorted(
        (x for x in estados if not x["flavio_supera_bolsonaro_2t"]),
        key=lambda x: (x["flavio_menos_bolsonaro_2t_pp"], x["uf"]),
    )
    acima_1t = [x["uf"] for x in estados if x["comparacao"]["vs_1t"]["direita_pp"] > 0]
    saldo: dict[str, Any] = {}
    for base in ("vs_1t", "vs_2t"):
        c = brasil["comparacao"][base]
        saldo[base] = {
            "direita_flavio_menos_bolsonaro": c["direita_votos"],
            "esquerda_lula_menos_lula": c["lula_votos"],
            "terceiros": c.get("terceiros_votos"),
            "brancos": c["brancos_votos"],
            "nulos": c["nulos_votos"],
            "abstencao": c["abstencao_votos"],
            "comparecimento": c["comparecimento_votos"],
            "eleitorado": c["eleitorado_votos"],
            "validos": c["validos_votos"],
            "margem_2022_pp": c["margem_2022_pp"],
            "margem_2026_pp": brasil["margem_2026_pp"],
            "virada_margem_pp": c["virada_margem_pp"],
        }
    contribuicao = {}
    for chave in ("direita_votos", "lula_votos"):
        total = brasil["comparacao"]["vs_1t"][chave]
        contribuicao[chave] = {
            g: {
                "votos": agregados[g]["comparacao"]["vs_1t"][chave],
                "pct_do_saldo_nacional": fatia(
                    agregados[g]["comparacao"]["vs_1t"][chave], total
                ),
            }
            for g in GRUPOS_DA_SOMA
        }
    return {
        "fonte_2026": f.pres26_origem,
        "fonte_2022": "data/raw/tse_resultados/api_2022/{uf}-c0001-e000544-r.json e -e000545-r.json",
        "definicoes": {
            "fatias": "candidaturas sobre os válidos do próprio turno",
            "comparecimento_abstencao": "sobre o eleitorado apto",
            "brancos_nulos": "sobre o comparecimento",
            "terceiros_2026": "Cury + Renan Santos + Caiado + demais",
            "terceiros_2022": "Ciro + Tebet + demais (1º turno)",
            "votos_equivalentes": (
                "(fatia de Flávio em 2026 menos fatia de Bolsonaro no 2º turno de 2022) "
                "vezes os válidos de 2026: o que a diferença de fatia vale no "
                "comparecimento de 2026"
            ),
        },
        "ufs": por_uf,
        "agregados": agregados,
        "flavio_acima_bolsonaro_2t": [_item_2t(x) for x in acima],
        "flavio_abaixo_bolsonaro_2t": [_item_2t(x) for x in abaixo],
        "n_ufs_flavio_acima_bolsonaro_2t": len(acima),
        "n_ufs_flavio_acima_bolsonaro_1t": len(acima_1t),
        "ufs_flavio_acima_bolsonaro_1t": acima_1t,
        "saldo_nacional": saldo,
        "contribuicao_regional_vs_1t": contribuicao,
        "conferencia": _conferencia_presidente(f, brasil),
    }


# ---------------------------------------------------------------- Câmara


def campo_2026(f: Fontes, sigla: str) -> str:
    return f.campos["partidos"].get(normalizar_sigla(sigla), INDEFINIDO)


def nome_completo_2026(
    f: Fontes, cargo: int, uf: str, nome_urna: str, partido: str
) -> str | None:
    """Nome completo normalizado de uma candidatura de 2026 pelo nome de urna."""
    opcoes = f.nomes26.get((cargo, uf, normalizar_texto(nome_urna)), [])
    if len(opcoes) > 1:
        opcoes = [
            o for o in opcoes if normalizar_sigla(o[1]) == normalizar_sigla(partido)
        ]
    return opcoes[0][0] if len(opcoes) == 1 else None


def eleitos_2022(f: Fontes, cargos: set[int]) -> list[dict[str, Any]]:
    """Eleitos da eleição ordinária de 2022 nos cargos pedidos, com campo histórico."""
    saida = []
    for c in f.cand22.values():
        if (
            c.cargo not in cargos
            or c.suplementar
            or c.turno != 1
            or not eleito(c.situacao)
        ):
            continue
        campo, via = campo_historico(c.partido, f.campos)
        saida.append(
            {
                "uf": c.uf,
                "cargo": c.cargo,
                "campo_teto_direita": campo_teto_direita(c.partido, f.campos),
                "nome": c.nome_urna,
                "nome_completo": c.nome,
                "partido": c.partido,
                "partido_2026": sigla_2026(c.partido),
                "federacao": c.federacao,
                "campo": campo,
                "via_campo": via,
                "votos": c.votos,
                "situacao": c.situacao,
            }
        )
    return sorted(saida, key=lambda x: (x["uf"], -x["votos"]))


def _votos_camara_2022(
    f: Fontes,
) -> tuple[dict[str, dict[str, int]], list[str], dict[str, int]]:
    """Votos por partido de 2022 (sigla de 2022) em cada UF, nominais mais legenda.

    UF sem o cargo no pacote de partidos (MA) fica só com os nominais do pacote
    de candidaturas, e entra na lista `sem_legenda`. Nas demais, os nominais dos
    dois pacotes são conferidos partido a partido.
    """
    nominais: dict[str, Counter] = defaultdict(Counter)
    for c in f.cand22.values():
        if c.cargo == DEPUTADO_FEDERAL and not c.suplementar and c.turno == 1:
            nominais[c.uf][c.partido] += c.votos
    votos: dict[str, dict[str, int]] = {}
    sem_legenda: list[str] = []
    divergencia: dict[str, int] = {}
    for uf in UFS_MAIUSC:
        pacote = f.partido22.get(uf) or {}
        if not pacote:
            votos[uf] = dict(nominais[uf])
            sem_legenda.append(uf)
            continue
        votos[uf] = {s: v["total"] for s, v in pacote.items() if v["total"]}
        dif = sum(
            abs(pacote.get(s, {}).get("nominais", 0) - nominais[uf].get(s, 0))
            for s in set(pacote) | set(nominais[uf])
        )
        if dif:
            divergencia[uf] = dif
    return votos, sem_legenda, divergencia


def _por_chave(votos: dict[str, int], mapa) -> dict[str, int]:
    saida: Counter = Counter()
    for s, v in votos.items():
        saida[mapa(s)] += v
    return dict(saida)


def _tabela_partidos(
    votos22: dict[str, int],
    votos26: dict[str, int],
    cad22: dict[str, int],
    cad26: dict[str, int],
    f: Fontes,
) -> list[dict[str, Any]]:
    t22 = sum(votos22.values())
    t26 = sum(votos26.values())
    chaves = set(votos22) | set(votos26) | set(cad22) | set(cad26)
    linhas = []
    for k in chaves:
        p22 = fatia(votos22.get(k, 0), t22)
        p26 = fatia(votos26.get(k, 0), t26)
        linhas.append(
            {
                "partido": k,
                "campo": campo_2026(f, k),
                "cadeiras_2022": cad22.get(k, 0),
                "cadeiras_2026": cad26.get(k, 0),
                "delta_cadeiras": cad26.get(k, 0) - cad22.get(k, 0),
                "votos_2022": votos22.get(k, 0),
                "pct_votos_2022": p22,
                "votos_2026": votos26.get(k, 0),
                "pct_votos_2026": p26,
                "delta_pct_votos_pp": round((p26 or 0) - (p22 or 0), 4),
            }
        )
    return sorted(
        linhas, key=lambda x: (-x["cadeiras_2026"], -x["votos_2026"], x["partido"])
    )


def _campos_votos(votos: dict[str, int], campo_de) -> dict[str, dict[str, Any]]:
    por = _por_chave(votos, campo_de)
    total = sum(por.values())
    return {
        c: {"votos": por.get(c, 0), "pct": fatia(por.get(c, 0), total)} for c in CAMPOS
    }


def camara(f: Fontes) -> dict[str, Any]:
    dep22 = eleitos_2022(f, {DEPUTADO_FEDERAL})
    cam = f.final["camara"]
    dep26 = []
    for u in cam["ufs"]:
        for e in u["eleitos"]:
            dep26.append(
                {
                    "uf": u["uf"],
                    "fonte": u["fonte"],
                    "nome": e["nome"],
                    "nome_completo": nome_completo_2026(
                        f, DEPUTADO_FEDERAL, u["uf"], e["nome"], e["partido"]
                    ),
                    "partido": e["partido"],
                    "campo": e["campo"],
                    "votos": e["votos"],
                }
            )
    votos22_uf, sem_legenda, divergencia = _votos_camara_2022(f)
    votos26_uf = f.camara26_votos

    def campo22(s: str) -> str:
        return campo_historico(s, f.campos)[0]

    def campo26(s: str) -> str:
        return campo_2026(f, s)

    nomes22 = {(d["uf"], normalizar_texto(d["nome_completo"])) for d in dep22}
    for d in dep26:
        d["reeleito"] = (
            d["nome_completo"] is not None and (d["uf"], d["nome_completo"]) in nomes22
        )
    ufs = []
    for uf in UFS_MAIUSC:
        d22 = [d for d in dep22 if d["uf"] == uf]
        d26 = [d for d in dep26 if d["uf"] == uf]
        c22 = por_campo(d["campo"] for d in d22)
        c26 = por_campo(d["campo"] for d in d26)
        p22 = contar(d["partido_2026"] for d in d22)
        p26 = contar(normalizar_sigla(d["partido"]) for d in d26)
        v22 = _por_chave(votos22_uf[uf], sigla_2026)
        v26 = {normalizar_sigla(s): v for s, v in votos26_uf[uf].items()}
        ufs.append(
            {
                "uf": uf,
                "fonte_2026": d26[0]["fonte"] if d26 else None,
                "vagas_2022": len(d22),
                "vagas_2026": len(d26),
                "por_campo_2022": c22,
                "por_campo_2026": c26,
                "delta_campo": diferenca(c26, c22),
                "por_bloco_2022": por_bloco(c22),
                "por_bloco_2026": por_bloco(c26),
                "delta_bloco": diferenca(por_bloco(c26), por_bloco(c22)),
                "por_partido_2022_sigla_original": contar(d["partido"] for d in d22),
                "por_partido_2022": p22,
                "por_partido_2026": p26,
                "votos_por_campo_2022": _campos_votos(votos22_uf[uf], campo22),
                "votos_por_campo_2026": _campos_votos(votos26_uf[uf], campo26),
                "partidos": _tabela_partidos(v22, v26, p22, p26, f),
                "reeleitos": sum(1 for d in d26 if d["reeleito"]),
                "votos_2022_sem_legenda": uf in sem_legenda,
            }
        )
    nac22_votos = Counter()
    nac26_votos = Counter()
    for uf in UFS_MAIUSC:
        nac22_votos.update(votos22_uf[uf])
        nac26_votos.update({normalizar_sigla(s): v for s, v in votos26_uf[uf].items()})
    c22 = por_campo(d["campo"] for d in dep22)
    c26 = por_campo(d["campo"] for d in dep26)
    teto22 = por_campo(d["campo_teto_direita"] for d in dep22)
    cad22_original = contar(d["partido"] for d in dep22)
    cad22 = contar(d["partido_2026"] for d in dep22)
    cad26 = contar(normalizar_sigla(d["partido"]) for d in dep26)
    v22_suc = _por_chave(dict(nac22_votos), sigla_2026)
    tabela = _tabela_partidos(v22_suc, dict(nac26_votos), cad22, cad26, f)
    campo_votos22 = _por_chave(dict(nac22_votos), campo22)
    campo_votos26 = _por_chave(dict(nac26_votos), campo26)
    reeleitos = [d for d in dep26 if d["reeleito"]]
    sem_nome = [d for d in dep26 if d["nome_completo"] is None]
    blocos22, blocos26 = por_bloco(c22), por_bloco(c26)
    limiares = {
        ano: {
            k: blocos.get("direita + centro-direita", 0) >= v
            for k, v in LIMIARES_CAMARA.items()
        }
        for ano, blocos in (("2022", blocos22), ("2026", blocos26))
    }
    return {
        "fontes": {
            "eleitos_2022": "votacao_candidato_munzona_2022.zip, cargo 6, DS_SIT_TOT_TURNO",
            "votos_2022": (
                "votacao_partido_munzona_2022.zip, cargo 6: QT_VOTOS_NOMINAIS_VALIDOS "
                "+ QT_TOTAL_VOTOS_LEG_VALIDOS"
            ),
            "eleitos_2026": "apuracao/data/boletins/final.json (camara.ufs[].eleitos)",
            "votos_2026": f.camara26_origem,
        },
        "ufs_provisorias_2026": cam["ufs_provisorias"],
        "votos_2022_sem_legenda": sem_legenda,
        "nota_sem_legenda": (
            "o pacote de partidos de 2022 não traz linhas de deputado federal nem "
            "estadual para o MA; ali entram só os votos nominais do pacote de "
            "candidaturas, sem a legenda"
        ),
        "divergencia_nominais_pacotes_2022": divergencia,
        "por_campo_2022": c22,
        "por_campo_2026": c26,
        "delta_campo": diferenca(c26, c22),
        "por_bloco_2022": blocos22,
        "por_bloco_2026": blocos26,
        "delta_bloco": diferenca(blocos26, blocos22),
        "sensibilidade_teto_direita_2022": {
            "regra": (
                "sigla extinta que a sucessão leva à centro-direita conta como direita "
                "em 2022 (teto da direita de 2022, piso do crescimento)"
            ),
            "siglas": contar(
                d["partido"] for d in dep22 if d["campo_teto_direita"] != d["campo"]
            ),
            "por_campo_2022": teto22,
            "delta_campo": diferenca(c26, teto22),
        },
        "limiares": LIMIARES_CAMARA,
        "direita_mais_cd_atinge": limiares,
        "trocas_de_bloco": trocas_de_bloco(
            {u["uf"]: u["por_bloco_2022"] for u in ufs},
            {u["uf"]: u["por_bloco_2026"] for u in ufs},
        ),
        "por_partido_2022_sigla_original": cad22_original,
        "por_partido_2022": cad22,
        "por_partido_2026": cad26,
        "partidos": tabela,
        "maiores_ganhos_cadeiras": sorted(
            tabela, key=lambda x: (-x["delta_cadeiras"], x["partido"])
        )[:6],
        "maiores_perdas_cadeiras": sorted(
            tabela, key=lambda x: (x["delta_cadeiras"], x["partido"])
        )[:6],
        "maiores_ganhos_votos": sorted(
            tabela, key=lambda x: (-x["delta_pct_votos_pp"], x["partido"])
        )[:6],
        "maiores_perdas_votos": sorted(
            tabela, key=lambda x: (x["delta_pct_votos_pp"], x["partido"])
        )[:6],
        "votos_por_campo_2022": _campos_votos(dict(nac22_votos), campo22),
        "votos_por_campo_2026": _campos_votos(dict(nac26_votos), campo26),
        "votos_totais_2022": sum(nac22_votos.values()),
        "votos_totais_2026": sum(nac26_votos.values()),
        "proporcionalidade": {
            "nota": (
                "votos somados no país contra cadeiras no país; a distribuição é por UF, "
                "então o índice inclui o efeito da desproporção entre UFs"
            ),
            "partidos_2022": proporcionalidade(dict(nac22_votos), cad22_original),
            "partidos_2026": proporcionalidade(dict(nac26_votos), cad26),
            "campos_2022": proporcionalidade(campo_votos22, c22),
            "campos_2026": proporcionalidade(campo_votos26, c26),
        },
        "renovacao": {
            "regra": "mesmo nome completo (sem acento, caixa alta) na mesma UF",
            "reeleitos": len(reeleitos),
            "novos": len(dep26) - len(reeleitos),
            "sem_nome_completo_2026": len(sem_nome),
            "reeleitos_por_campo_2026": por_campo(d["campo"] for d in reeleitos),
        },
        "ufs": ufs,
        "eleitos_2022": dep22,
        "eleitos_2026": dep26,
    }
