"""Senado, governadores, assembleias e a tabela de partidos: 2018/2022 contra 2026."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from .comparacao import (
    INDEFINIDO,
    SUCESSORES,
    campo_historico,
    campo_teto_direita,
    contar,
    diferenca,
    eleito,
    fatia,
    fluxo,
    normalizar_sigla,
    normalizar_texto,
    por_bloco,
    por_campo,
    segundo_turno,
    sigla_2026,
    troca_no_segundo_turno,
    trocas_de_bloco,
)
from .comparacao_fontes import ASSEMBLEIAS, Fontes
from .comparacao_secoes import UFS_MAIUSC, eleitos_2022, nome_completo_2026
from .dados import bloco_de
from .tse_cargos import DEPUTADO_DISTRITAL, DEPUTADO_ESTADUAL, GOVERNADOR, SENADOR

# Exceção por candidatura já declarada pela casa para os eleitos de 2022 que
# continuam no Senado (analysis/senado_2026/metodo.md; final.json a aplica).
EXCECOES_SENADO_2022: dict[str, tuple[str, str, str]] = {
    "130001671677": (
        "direita",
        "REPUBLICANOS",
        "Cleitinho (MG), eleito pelo PSC, incorporado ao Podemos; conta como direita "
        "e Republicanos, exceção declarada em analysis/senado_2026/metodo.md",
    ),
}
# Sensibilidade, não regra: em 2018 o PSL era o partido de Jair Bolsonaro, e a
# tabela de sucessão o leva ao União Brasil (centro-direita).
SENSIBILIDADE_2018 = {"PSL": "direita"}
LIMIARES_SENADO = {"maioria": 41, "tres_quintos": 49, "dois_tercos": 54}


# ---------------------------------------------------------------- Senado


def _senador(
    c, f: Fontes, excecao: tuple[str, str, str] | None = None
) -> dict[str, Any]:
    campo, via = campo_historico(c.partido, f.campos)
    item = {
        "uf": c.uf,
        "nome": c.nome_urna,
        "nome_completo": c.nome,
        "partido": c.partido,
        "partido_2026": sigla_2026(c.partido),
        "campo": campo,
        "via_campo": via,
        "votos": c.votos,
        "eleicao": c.ds_eleicao,
        "data_eleicao": c.dt_eleicao,
        "suplementar": c.suplementar,
        "campo_teto_direita": campo_teto_direita(c.partido, f.campos),
    }
    if excecao:
        item["campo"], item["partido_2026"], item["nota"] = excecao
        item["campo_teto_direita"] = item["campo"]
        item["via_campo"] = "exceção declarada"
    return item


def _composicao(
    membros: list[dict[str, Any]], chave_campo: str = "campo"
) -> dict[str, Any]:
    campos = por_campo(m[chave_campo] for m in membros)
    blocos = por_bloco(campos)
    direita = blocos.get("direita + centro-direita", 0)
    return {
        "total": len(membros),
        "por_campo": campos,
        "por_bloco": blocos,
        "por_partido": contar(m["partido_2026"] for m in membros),
        "direita_mais_cd_atinge": {k: direita >= v for k, v in LIMIARES_SENADO.items()},
    }


def senado(f: Fontes) -> dict[str, Any]:
    c18 = sorted(
        (
            _senador(c, f)
            for c in f.cand18.values()
            if c.cargo == SENADOR and c.turno == 1 and eleito(c.situacao)
        ),
        key=lambda x: (x["uf"], -x["votos"]),
    )
    for s in c18:
        s["campo_sensibilidade_psl"] = SENSIBILIDADE_2018.get(
            normalizar_sigla(s["partido"]), s["campo"]
        )
    c22 = sorted(
        (
            _senador(c, f, EXCECOES_SENADO_2022.get(c.sq))
            for c in f.cand22.values()
            if c.cargo == SENADOR
            and not c.suplementar
            and c.turno == 1
            and eleito(c.situacao)
        ),
        key=lambda x: x["uf"],
    )
    sq22 = {
        c.sq
        for c in f.cand22.values()
        if c.cargo == SENADOR and not c.suplementar and eleito(c.situacao)
    }
    ref = {s["sq_candidato"] for s in f.senadores_2022_ref}
    c26 = []
    for u in f.final["senado"]["ufs"]:
        for e in u["eleitos"]:
            c26.append(
                {
                    "uf": u["uf"],
                    "fonte": u["fonte"],
                    "nome": e["nome"],
                    "nome_completo": nome_completo_2026(
                        f, SENADOR, u["uf"], e["nome"], e["partido"]
                    ),
                    "partido": e["partido"],
                    "partido_2026": normalizar_sigla(e["partido"]),
                    "campo": e["campo"],
                    "votos": e["votos"],
                }
            )
    por_uf_18 = defaultdict(list)
    for s in c18:
        por_uf_18[s["uf"]].append(s)
    por_uf_26 = defaultdict(list)
    for s in c26:
        por_uf_26[s["uf"]].append(s)
    erros = [
        uf for uf in UFS_MAIUSC if len(por_uf_18[uf]) != 2 or len(por_uf_26[uf]) != 2
    ]
    if erros or len(c22) != 27:
        raise ValueError(
            f"Senado: UFs sem duas vagas {erros}; classe de 2022 com {len(c22)}"
        )
    ufs = []
    reeleitos = []
    for uf in UFS_MAIUSC:
        antes, depois = por_uf_18[uf], por_uf_26[uf]
        nomes18 = {normalizar_texto(s["nome_completo"]) for s in antes}
        reeleitos_uf = [s["nome"] for s in depois if s["nome_completo"] in nomes18]
        reeleitos += [{"uf": uf, "nome": n} for n in reeleitos_uf]
        b18 = por_bloco(por_campo(s["campo"] for s in antes))
        b26 = por_bloco(por_campo(s["campo"] for s in depois))
        ufs.append(
            {
                "uf": uf,
                "eleitos_2018": [(s["nome"], s["partido"], s["campo"]) for s in antes],
                "eleitos_2026": [(s["nome"], s["partido"], s["campo"]) for s in depois],
                "blocos_2018": b18,
                "blocos_2026": b26,
                "mudou_bloco": b18 != b26,
                "reeleitos": reeleitos_uf,
            }
        )
    s2023 = c18 + c22
    s2027 = c22 + c26
    comp23 = _composicao(s2023)
    comp27 = _composicao(s2027)
    sens23 = _composicao(
        [{**s, "campo": s.get("campo_sensibilidade_psl", s["campo"])} for s in s2023]
    )
    conf_final = diferenca(
        comp27["por_campo"], f.final["senado"]["senado_2027"]["por_campo"]
    )
    return {
        "fontes": {
            "classe_2018": (
                "votacao_candidato_munzona_2018.zip, cargo 5, DS_SIT_TOT_TURNO ELEITO "
                "(ordinária de 07/10/2018 e suplementar de MT de 15/11/2020)"
            ),
            "classe_2022": "votacao_candidato_munzona_2022.zip, cargo 5, ordinária",
            "classe_2026": "apuracao/data/boletins/final.json (senado.ufs[].eleitos)",
        },
        "regra": (
            "eleitos da urna, não titulares atuais: suplência, licença, morte e "
            "migração partidária ficam fora; partido da eleição levado à sigla de "
            "2026 pela tabela de sucessores"
        ),
        "nota_mt": (
            "a eleição ordinária de 2018 em MT só tem um eleito no pacote do TSE; a "
            "segunda vaga daquela classe saiu da eleição suplementar de 15/11/2020, "
            "que o pacote de 2018 traz e que entra aqui"
        ),
        "classe_2018": c18,
        "classe_2022": c22,
        "classe_2026": c26,
        "classe_2018_composicao": _composicao(c18),
        "classe_2022_composicao": _composicao(c22),
        "classe_2026_composicao": _composicao(c26),
        "classe_2022_pct_campo": {
            k: fatia(v, len(c22)) for k, v in por_campo(s["campo"] for s in c22).items()
        },
        "classe_2026_pct_campo": {
            k: fatia(v, len(c26)) for k, v in por_campo(s["campo"] for s in c26).items()
        },
        "classes_54_delta_campo": diferenca(
            por_campo(s["campo"] for s in c26), por_campo(s["campo"] for s in c18)
        ),
        "senado_2023": comp23,
        "senado_2027": comp27,
        "delta_2027_2023_campo": diferenca(comp27["por_campo"], comp23["por_campo"]),
        "delta_2027_2023_bloco": diferenca(comp27["por_bloco"], comp23["por_bloco"]),
        "delta_2027_2023_partido": diferenca(
            comp27["por_partido"], comp23["por_partido"]
        ),
        "sensibilidade_teto_direita": {
            "regra": (
                "sigla extinta que a sucessão leva à centro-direita conta como direita "
                "(teto da direita de 2018 e 2022, piso do crescimento)"
            ),
            "siglas_2018": contar(
                s["partido"] for s in c18 if s["campo_teto_direita"] != s["campo"]
            ),
            "classe_2018": _composicao(
                [{**s, "campo": s["campo_teto_direita"]} for s in c18]
            ),
            "senado_2023": _composicao(
                [{**s, "campo": s["campo_teto_direita"]} for s in s2023]
            ),
        },
        "sensibilidade_psl_2018_direita": {
            "classe_2018": _composicao(
                [{**s, "campo": s["campo_sensibilidade_psl"]} for s in c18]
            ),
            "senado_2023": sens23,
            "delta_2027_2023_campo": diferenca(
                comp27["por_campo"], sens23["por_campo"]
            ),
            "delta_2027_2023_bloco": diferenca(
                comp27["por_bloco"], sens23["por_bloco"]
            ),
        },
        "ufs": ufs,
        "ufs_que_mudaram_bloco": [u["uf"] for u in ufs if u["mudou_bloco"]],
        "trocas_de_bloco_classe_54": trocas_de_bloco(
            {u["uf"]: u["blocos_2018"] for u in ufs},
            {u["uf"]: u["blocos_2026"] for u in ufs},
        ),
        "reeleitos_2018_2026": reeleitos,
        "conferencia": {
            "classe_2022_igual_a_senadores_2022_json": sq22 == ref,
            "senado_2027_menos_final_json_por_campo": conf_final,
        },
    }


# ---------------------------------------------------------------- governadores


def _gov_item(c, total: int, f: Fontes) -> dict[str, Any]:
    campo, via = campo_historico(c.partido, f.campos)
    return {
        "nome": c.nome_urna,
        "nome_completo": c.nome,
        "partido": c.partido,
        "partido_2026": sigla_2026(c.partido),
        "campo": campo,
        "via_campo": via,
        "votos": c.votos,
        "pct": fatia(c.votos, total),
        "situacao": c.situacao,
    }


def _governadores_2022(f: Fontes) -> dict[str, dict[str, Any]]:
    turnos: dict[str, dict[int, list]] = defaultdict(lambda: {1: [], 2: []})
    for c in f.cand22.values():
        if c.cargo == GOVERNADOR and not c.suplementar:
            turnos[c.uf][c.turno].append(c)
    saida = {}
    for uf in UFS_MAIUSC:
        t1 = sorted(turnos[uf][1], key=lambda c: -c.votos)
        t2 = sorted(turnos[uf][2], key=lambda c: -c.votos)
        v1 = sum(c.votos for c in t1)
        v2 = sum(c.votos for c in t2)
        eleitos1 = [c for c in t1 if eleito(c.situacao)]
        eleitos2 = [c for c in t2 if eleito(c.situacao)]
        if len(eleitos1) + len(eleitos2) != 1:
            raise ValueError(
                f"governador 2022 {uf}: {len(eleitos1) + len(eleitos2)} eleitos"
            )
        if eleitos1:
            vencedor, turno = _gov_item(eleitos1[0], v1, f), 1
        else:
            vencedor, turno = _gov_item(eleitos2[0], v2, f), 2
        saida[uf] = {
            "vencedor": vencedor,
            "turno_decisivo": turno,
            "primeiro_turno": [_gov_item(c, v1, f) for c in t1[:3]],
            "foi_ao_segundo_turno": [
                c.nome_urna for c in t1 if segundo_turno(c.situacao)
            ],
            "segundo_turno": [_gov_item(c, v2, f) for c in t2],
        }
    return saida


def _suplementares_governador(f: Fontes) -> list[dict[str, Any]]:
    saida = []
    for c in sorted(f.cand22.values(), key=lambda c: -c.votos_nominais):
        if c.cargo == GOVERNADOR and c.suplementar:
            saida.append(
                {
                    "uf": c.uf,
                    "eleicao": c.ds_eleicao,
                    "data": c.dt_eleicao,
                    "nome": c.nome_urna,
                    "partido": c.partido,
                    "votos_nominais": c.votos_nominais,
                    "votos_validos": c.votos,
                    "situacao": c.situacao,
                }
            )
    return saida


def governadores(f: Fontes) -> dict[str, Any]:
    g22 = _governadores_2022(f)
    ufs = []
    for u in f.final["governadores"]["ufs"]:
        uf = u["uf"]
        antes = g22[uf]
        v22 = antes["vencedor"]
        cands = [
            {
                **c,
                "bloco": bloco_de(c["campo"]),
                "nome_completo": nome_completo_2026(
                    f, GOVERNADOR, uf, c["nome"], c["partido"]
                ),
            }
            for c in u["candidatos"]
        ]
        item: dict[str, Any] = {
            "uf": uf,
            "fonte_2026": u["fonte"],
            "vencedor_2022": v22,
            "turno_decisivo_2022": antes["turno_decisivo"],
            "primeiro_turno_2022": antes["primeiro_turno"],
            "segundo_turno_2022": antes["segundo_turno"],
            "decisao_2026": u["decisao"],
            "candidatos_2026": cands,
            "bloco_2022": bloco_de(v22["campo"]),
        }
        nome22 = normalizar_texto(v22["nome_completo"])
        if u["decisao"] == "eleito":
            e = cands[0]
            item.update(
                {
                    "mudou_campo": e["campo"] != v22["campo"],
                    "mudou_bloco": e["bloco"] != item["bloco_2022"],
                    "mesmo_partido": normalizar_sigla(e["partido"])
                    == v22["partido_2026"],
                    "mesma_pessoa": e["nome_completo"] == nome22,
                }
            )
        else:
            blocos = {c["bloco"] for c in cands}
            item.update(
                {
                    "bloco_2026_definido": blocos.pop() if len(blocos) == 1 else None,
                    "partido_2022_no_2t": any(
                        normalizar_sigla(c["partido"]) == v22["partido_2026"]
                        for c in cands
                    ),
                    "pessoa_2022_no_2t": any(
                        c["nome_completo"] == nome22 for c in cands
                    ),
                }
            )
            item["mudou_bloco"] = troca_no_segundo_turno(
                item["bloco_2022"], (c["bloco"] for c in cands)
            )
        ufs.append(item)
    decididos = [x for x in ufs if x["decisao_2026"] == "eleito"]
    abertos = [x for x in ufs if x["decisao_2026"] != "eleito"]
    vencedores22 = [g22[uf]["vencedor"] for uf in UFS_MAIUSC]
    return {
        "fontes": {
            "2022": "votacao_candidato_munzona_2022.zip, cargo 3, ordinária (turnos 1 e 2)",
            "2026": "apuracao/data/boletins/final.json (governadores.ufs)",
        },
        "nota_pct_2022": "fatias sobre a soma dos votos nominais válidos do turno",
        "por_campo_2022": por_campo(v["campo"] for v in vencedores22),
        "por_bloco_2022": por_bloco(por_campo(v["campo"] for v in vencedores22)),
        "por_partido_2022": contar(v["partido_2026"] for v in vencedores22),
        "decididos_2022_1t": sum(
            1 for uf in UFS_MAIUSC if g22[uf]["turno_decisivo"] == 1
        ),
        "eleitos_2026_1t_por_campo": por_campo(
            x["candidatos_2026"][0]["campo"] for x in decididos
        ),
        "decididos_2026": len(decididos),
        "segundo_turno_2026": len(abertos),
        "decididos_mudaram_campo": [x["uf"] for x in decididos if x["mudou_campo"]],
        "decididos_mudaram_bloco": [x["uf"] for x in decididos if x["mudou_bloco"]],
        "decididos_mesmo_partido": [x["uf"] for x in decididos if x["mesmo_partido"]],
        "decididos_mesma_pessoa": [x["uf"] for x in decididos if x["mesma_pessoa"]],
        "decididos_mudaram_bloco_mesma_pessoa": [
            x["uf"] for x in decididos if x["mudou_bloco"] and x["mesma_pessoa"]
        ],
        "fluxo_bloco_decididos": fluxo(
            (x["bloco_2022"], x["candidatos_2026"][0]["bloco"]) for x in decididos
        ),
        "abertos_bloco_definido": {
            x["uf"]: x["bloco_2026_definido"]
            for x in abertos
            if x["bloco_2026_definido"]
        },
        "abertos_mudam_bloco_com_certeza": [
            x["uf"] for x in abertos if x["mudou_bloco"]
        ],
        "abertos_podem_mudar_bloco": [
            x["uf"] for x in abertos if x["mudou_bloco"] is None
        ],
        "suplementar_governador": _suplementares_governador(f),
        "ufs": ufs,
    }


# ---------------------------------------------------------------- assembleias


def assembleias(f: Fontes) -> dict[str, Any]:
    dep22 = eleitos_2022(f, {DEPUTADO_ESTADUAL, DEPUTADO_DISTRITAL})
    casas_26 = {a["uf"]: a for a in f.final["assembleias"]}
    saida = []
    tot22: list[str] = []
    teto22: list[str] = []
    tot26: dict[str, int] = {}
    for uf in ASSEMBLEIAS:
        d22 = [d for d in dep22 if d["uf"] == uf]
        a26 = casas_26[uf]
        c22 = por_campo(d["campo"] for d in d22)
        c26 = {k: v for k, v in a26["por_campo"].items() if k != INDEFINIDO or v}
        if len(d22) != a26["vagas"]:
            raise ValueError(
                f"assembleia {uf}: {len(d22)} eleitos em 2022 e {a26['vagas']} vagas"
            )
        tot22 += [d["campo"] for d in d22]
        teto22 += [d["campo_teto_direita"] for d in d22]
        for k, v in c26.items():
            tot26[k] = tot26.get(k, 0) + v
        p26 = {normalizar_sigla(k): v for k, v in a26["por_partido"].items()}
        p22 = contar(d["partido_2026"] for d in d22)
        saida.append(
            {
                "uf": uf,
                "fonte_2026": a26["fonte"],
                "vagas": a26["vagas"],
                "por_campo_2022": c22,
                "por_campo_2026": c26,
                "delta_campo": diferenca(c26, c22),
                "por_bloco_2022": por_bloco(c22),
                "por_bloco_2026": por_bloco(c26),
                "delta_bloco": diferenca(por_bloco(c26), por_bloco(c22)),
                "por_partido_2022": p22,
                "por_partido_2026": p26,
                "delta_partido": diferenca(p26, p22),
            }
        )
    t22 = por_campo(tot22)
    trocas = trocas_de_bloco(
        {x["uf"]: x["por_bloco_2022"] for x in saida},
        {x["uf"]: x["por_bloco_2026"] for x in saida},
    )
    return {
        "fontes": {
            "2022": "votacao_candidato_munzona_2022.zip, cargos 7 e 8 (DF), DS_SIT_TOT_TURNO",
            "2026": "apuracao/data/boletins/final.json (assembleias)",
        },
        "casas": saida,
        "onze_casas": {
            "vagas": sum(x["vagas"] for x in saida),
            "por_campo_2022": t22,
            "por_campo_2026": tot26,
            "delta_campo": diferenca(tot26, t22),
            "por_bloco_2022": por_bloco(t22),
            "por_bloco_2026": por_bloco(tot26),
            "delta_bloco": diferenca(por_bloco(tot26), por_bloco(t22)),
            "trocas_de_bloco": trocas,
            "sensibilidade_teto_direita_2022": {
                "siglas": contar(
                    d["partido"] for d in dep22 if d["campo_teto_direita"] != d["campo"]
                ),
                "por_campo_2022": por_campo(teto22),
                "delta_campo": diferenca(tot26, por_campo(teto22)),
            },
        },
    }


# ---------------------------------------------------------------- partidos


def tabela_partidos(f: Fontes) -> list[dict[str, Any]]:
    """Cada sigla de 2018 (Senado) e 2022 (todos os cargos lidos) com campo e sucessor."""
    numeros: dict[str, set[int]] = defaultdict(set)
    anos: dict[str, set[int]] = defaultdict(set)
    for c in [*f.cand22.values(), *f.cand18.values()]:
        sigla = normalizar_sigla(c.partido)
        numeros[sigla].add(int(c.nr_partido))
        anos[sigla].add(c.ano)
    linhas = []
    for sigla in sorted(numeros):
        sucessor = sigla_2026(sigla)
        campo, via = campo_historico(sigla, f.campos)
        linha: dict[str, Any] = {
            "sigla": sigla,
            "anos": sorted(anos[sigla]),
            "numeros": sorted(numeros[sigla]),
            "sigla_2026": sucessor,
            "campo": campo,
            "via_campo": via,
        }
        if sigla in SUCESSORES:
            s = SUCESSORES[sigla]
            no_banco = {n: f.partidos26.get(n) for n in sorted(numeros[sigla])}
            linha.update(
                {
                    "tipo": s.tipo,
                    "descricao": s.descricao,
                    "numero_em_2026": no_banco,
                    "confirmado_pelo_numero": any(
                        v == sucessor for v in no_banco.values()
                    ),
                    "evidencia": (
                        "o número do partido aparece com a sigla sucessora no banco de 2026"
                        if any(v == sucessor for v in no_banco.values())
                        else "fato público de registro partidário, sem documento no repositório"
                    ),
                }
            )
        linhas.append(linha)
    return linhas
