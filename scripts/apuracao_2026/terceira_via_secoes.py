"""Montagem do JSON "Onde está o voto da terceira via, cidade por cidade".

Recebe as fontes lidas por ``terceira_via_leitura.ler_tudo`` e devolve os blocos
do JSON. Contas elementares em ``terceira_via.py``; aqui só se cruzam fontes.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from . import terceira_via as T
from .dados import REGIAO_UF
from .estrategia_leitura import sem_acento

REGIOES = ("Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul")
GRANDE = 200_000  # eleitores: corte declarado de "cidade grande"
N_TOP = 100
N_UF = 10
N_REGIAO = 10
N_NULO = 15
MIN_COMPARECIMENTO_NULO = 20_000


def _r(x: float | None, casas: int = 2) -> float | None:
    return T.r2(x, casas)


# ---------------------------------------------------------------- matriz


def matrizes(fontes: dict) -> dict[str, Any]:
    """Linhas normalizadas e a linha de cada número, de ``estrategia_2t.json``."""
    ar = fontes["estrategia_2t"]["aritmetica"]
    linha_por_numero = {
        int(c["numero"]): c["linha"] for c in ar["primeiro_turno"]["terceiros"]
    }
    return {
        "linha_por_numero": linha_por_numero,
        "nexus": ar["matrizes"]["nexus"]["linhas"],
        "datafolha": ar["matrizes"]["datafolha"]["linhas"],
        "fonte_nexus": ar["matrizes"]["nexus"]["fonte"],
        "fonte_datafolha": ar["matrizes"]["datafolha"]["fonte"],
        "publicadas_nexus": ar["matrizes"]["nexus"]["linhas_publicadas"],
        "publicadas_datafolha": ar["matrizes"]["datafolha"]["linhas_publicadas"],
    }


# ---------------------------------------------------------------- direita local


def _sq_por_nome(cands: dict[str, dict], uf: str, nome: str) -> str:
    alvo = sem_acento(nome)
    achados = [
        sq
        for sq, c in cands.items()
        if (c.get("uf") or "").upper() == uf
        and sem_acento(c["nome_urna"] or "") == alvo
    ]
    if len(achados) != 1:
        raise ValueError(
            f"governador {nome} ({uf}): {len(achados)} candidaturas no banco"
        )
    return achados[0]


def direita_local(fontes: dict) -> dict[str, dict]:
    """Por UF: o governador do lado de Flávio e as candidaturas do bloco ao Senado.

    Governador: a candidatura mais votada entre as que o vão estadual da casa
    compara com Flávio (``governadores.json → vao_estadual.lista``, finalista
    ``flavio``), com a comparação declarada (mesmo bloco, coligação com o PL ou
    sem apoio declarado). Senado: os eleitos do bloco aliado
    (``senado_x_flavio.json → carregadores``) e a candidatura mais votada do
    bloco, eleita ou não (``ufs[].melhor``).
    """
    gov_cands = fontes["gov"]["candidatos"]
    saida: dict[str, dict] = {}
    for x in fontes["governadores"]["vao_estadual"]["lista"]:
        if x["finalista"] != "flavio":
            continue
        uf = x["uf"].upper()
        atual = saida.setdefault(uf, {"governador": None, "senado": []})
        if atual["governador"] and atual["governador"]["pct_uf"] >= x["pct_governador"]:
            continue
        atual["governador"] = {
            "sqcand": _sq_por_nome(gov_cands, uf, x["governador"]),
            "nome": x["governador"],
            "partido": x["partido"],
            "campo": x["campo"],
            "decisao": x["decisao"],
            "comparacao": x["comparacao"],
            "pct_uf": x["pct_governador"],
        }
    S = fontes["senado_x_flavio"]
    for c in S["carregadores"]["candidatos"]:
        atual = saida.setdefault(c["uf"], {"governador": None, "senado": []})
        atual["senado"].append(
            {
                "sqcand": c["sqcand"],
                "nome": c["nome"],
                "partido": c["partido"],
                "campo": c["campo"],
                "eleito": True,
            }
        )
    for u in S["ufs"]:
        m = u.get("melhor")
        if not m:
            continue
        atual = saida.setdefault(u["uf"], {"governador": None, "senado": []})
        if all(s["sqcand"] != m["sqcand"] for s in atual["senado"]):
            atual["senado"].append(
                {
                    "sqcand": m["sqcand"],
                    "nome": m["nome"],
                    "partido": m["partido"],
                    "campo": m["campo"],
                    "eleito": bool(m["eleito"]),
                }
            )
    return dict(sorted(saida.items()))


def _base(arquivo: dict) -> int:
    return sum(arquivo["votos"].values())


# ---------------------------------------------------------------- municípios


def ufs_2t_governador(fontes: dict) -> dict[str, set[str]]:
    """UFs com 2º turno de governador em 2022 e em 2026.

    2022: ``estrategia_2t.json → riscos.comparecimento.grupos_2022`` (lido de
    ``votacao_candidato_munzona_2022.zip``); 2026: ``governadores.json → ufs``,
    decisão ``segundo_turno``.
    """
    g22 = fontes["estrategia_2t"]["riscos"]["comparecimento"]["grupos_2022"]
    return {
        "2022": set(g22["com_2t_governador_2022"]["ufs"]),
        "2026": {
            u["uf"]
            for u in fontes["governadores"]["ufs"]
            if u["decisao"] == "segundo_turno"
        },
    }


def _votos_por_numero(arquivo: dict, numero_de: dict[str, int]) -> dict[int, int]:
    saida: dict[int, int] = defaultdict(int)
    for sq, v in arquivo["votos"].items():
        saida[numero_de[sq]] += v
    return dict(saida)


def _nulo_2022(det: dict | None) -> dict[str, Any]:
    if not det or 1 not in det or 2 not in det:
        return {}
    a, b = det[1], det[2]
    bn1, bn2 = a["brancos"] + a["nulos"], b["brancos"] + b["nulos"]
    p1 = T.brancos_nulos_pct(a["brancos"], a["nulos"], a["comparecimento"])
    p2 = T.brancos_nulos_pct(b["brancos"], b["nulos"], b["comparecimento"])
    return {
        "bn22_1t": bn1,
        "bn22_2t": bn2,
        "comp22_1t": a["comparecimento"],
        "comp22_2t": b["comparecimento"],
        "bn22_1t_pct": p1,
        "bn22_2t_pct": p2,
        "delta_bn22_pp": None if p1 is None or p2 is None else p2 - p1,
    }


def municipios(fontes: dict, mat: dict, locais: dict) -> tuple[list[dict], list[dict]]:
    """Uma linha por município do Brasil e uma por cidade do exterior."""
    pres, gov, sen = fontes["pres"], fontes["gov"], fontes["sen"]
    numero_de = {sq: int(c["numero"]) for sq, c in pres["candidatos"].items()}
    meta = fontes["municipios"]
    pais = {c["cd_tse"]: c.get("pais_nome") for c in fontes["exterior"]["cidades"]}
    sq_flavio = next(sq for sq, n in numero_de.items() if n == T.NUM_FLAVIO)
    pres_uf = {k: a for k, a in pres["arquivos"].items() if a["nivel"] == "uf"}
    gov_2t = ufs_2t_governador(fontes)
    brasil, exterior = [], []
    for cd, a in pres["arquivos"].items():
        if a["nivel"] != "mu":
            continue
        uf = a["uf"]
        vn = _votos_por_numero(a, numero_de)
        fl, lu = vn.get(T.NUM_FLAVIO, 0), vn.get(T.NUM_LULA, 0)
        por_grupo = dict.fromkeys(T.GRUPOS, 0)
        for numero, v in vn.items():
            if numero not in (T.NUM_FLAVIO, T.NUM_LULA):
                por_grupo[T.grupo(numero)] += v
        estoque = sum(por_grupo.values())
        vv = a["validos"]
        margem = T.pct(fl - lu, vv) or 0.0
        nx = T.destinos(vn, mat["linha_por_numero"], mat["nexus"])
        dfl = T.destinos(vn, mat["linha_por_numero"], mat["datafolha"])
        m = meta[cd]
        linha: dict[str, Any] = {
            "cd": cd,
            "ibge": m["ibge"],
            "uf": uf,
            "nome": m["nome"],
            "regiao": REGIAO_UF[uf.lower()],
            "capital": bool(m["capital"]),
            "eleitores": a["eleitores"],
            "comparecimento": a["comparecimento"],
            "validos": vv,
            "flavio": fl,
            "lula": lu,
            **por_grupo,
            "estoque": estoque,
            "estoque_pct": T.pct(estoque, vv),
            "margem_pp": margem,
            "classe": T.classe_margem(margem),
            "para_flavio": nx["para_flavio"],
            "para_lula": nx["para_lula"],
            "fora": nx["fora"],
            "saldo": nx["saldo"],
            "saldo_df": dfl["saldo"],
            "saldo_por_voto": nx["saldo"] / estoque if estoque else None,
        }
        if uf == "ZZ":
            linha["pais"] = pais.get(cd)
            exterior.append(linha)
            continue
        r22 = fontes["mun22"].get(cd)
        if r22:
            v22 = r22["bolsonaro_2t"] + r22["lula_2t"]
            tv22 = r22["validos_1t"] - r22["lula_1t"] - r22["bolsonaro_1t"]
            linha.update(
                {
                    "ganho_b22": r22["bolsonaro_2t"] - r22["bolsonaro_1t"],
                    "ganho_l22": r22["lula_2t"] - r22["lula_1t"],
                    "b22_2t_pct": T.pct(r22["bolsonaro_2t"], v22),
                    "tv22": tv22,
                    "tv22_pct": T.pct(tv22, r22["validos_1t"]),
                    "ciro22_pct": T.pct(r22["ciro_1t"], r22["validos_1t"]),
                    "tebet22_pct": T.pct(r22["tebet_1t"], r22["validos_1t"]),
                }
            )
        nulo = _nulo_2022(fontes["det22"].get(cd))
        linha.update(nulo)
        linha["gov22_2t"] = uf in gov_2t["2022"]
        linha["gov26_2t"] = uf in gov_2t["2026"]
        if nulo and r22:
            linha["taxa_nulo22"] = T.taxa_nulo(
                nulo["bn22_1t"], nulo["bn22_2t"], linha["tv22"]
            )
        p_uf = pres_uf[uf]
        flavio_uf = (p_uf["votos"].get(sq_flavio, 0), p_uf["validos"])
        _local(linha, cd, uf, locais.get(uf), gov, sen, flavio_uf)
        brasil.append(linha)
    brasil.sort(key=lambda x: (x["uf"], x["nome"]))
    exterior.sort(key=lambda x: -x["estoque"])
    return brasil, exterior


def _local(
    linha: dict,
    cd: str,
    uf: str,
    loc: dict | None,
    gov: dict,
    sen: dict,
    flavio_uf: tuple[int, int],
) -> None:
    """Direita local do município: votos de cada nome, índices e vão sobre Flávio."""
    fl, vv = linha["flavio"], linha["validos"]
    fl_uf, vv_uf = flavio_uf
    votos_bloco: dict[str, int] = {}
    estrito: dict[str, int] = {}
    nomes: list[dict] = []
    if loc:
        g = loc["governador"]
        if g:
            gm, gu = gov["arquivos"][cd], gov["arquivos"][uf]
            v = gm["votos"].get(g["sqcand"], 0)
            votos_bloco[g["nome"]] = v
            if g["comparacao"] != "sem apoio declarado":
                estrito[g["nome"]] = v
            nomes.append(
                {
                    "nome": g["nome"],
                    "cargo": "governador",
                    "votos": v,
                    "indice": T.indice(
                        v,
                        _base(gm),
                        gu["votos"].get(g["sqcand"], 0),
                        _base(gu),
                        fl,
                        vv,
                        fl_uf,
                        vv_uf,
                    ),
                }
            )
        for s in loc["senado"]:
            sm, su = sen["arquivos"][cd], sen["arquivos"][uf]
            v = sm["votos"].get(s["sqcand"], 0)
            votos_bloco[s["nome"]] = max(votos_bloco.get(s["nome"], 0), v)
            estrito[s["nome"]] = votos_bloco[s["nome"]]
            nomes.append(
                {
                    "nome": s["nome"],
                    "cargo": "senado",
                    "eleito": s["eleito"],
                    "votos": v,
                    "indice": T.indice(
                        v,
                        _base(sm),
                        su["votos"].get(s["sqcand"], 0),
                        _base(su),
                        fl,
                        vv,
                        fl_uf,
                        vv_uf,
                    ),
                }
            )
    quem, vao = T.vao_local(votos_bloco, fl)
    linha["vao_votos_estrito"] = T.vao_local(estrito, fl)[1]
    linha["local_nomes"] = nomes
    linha["local_lider"] = quem
    linha["vao_votos"] = vao
    linha["vao_pp"] = T.pct(vao, linha["comparecimento"])
    linha["teto"] = T.teto(linha["estoque"], vao)
