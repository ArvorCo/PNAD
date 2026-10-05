"""Duas réguas para o mesmo estoque: pesquisa (Nexus, Datafolha) contra a urna de 2022.

Recebe as linhas por município já com a régua da urna aplicada
(``terceira_via_regua.aplicar``) e devolve: totais pelas réguas no país, nas
regiões e nas UFs; os 100 municípios e os 10 por UF em três versões (pesquisa,
urna, e a combinação que ordena pelo piso das duas e mostra o teto); a marca de
robusto ou divergente com o motivo; os movimentos do capítulo pelas duas réguas;
e o teste de retrovisão, que depende de pesquisa de 2º turno de 2022 arquivada.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from typing import Any

from . import terceira_via as T

REGIOES = ("Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul")
N_TOP = 100
N_UF = 10
VERSOES = {
    "pesquisa": "saldo",
    "urna": "saldo_urna",
    "combinacao": "piso",
}
# Candidaturas por movimento do capítulo 13 (estrategia_2t.json → movimentos).
MOVIMENTO_COLUNAS = {
    "renan": ("renan",),
    "cury": ("cury",),
    "caiado_go": ("caiado",),
    "direita_menor": ("zema", "direita_menor"),
}
SEM_REGUA = {
    "nao_escolha": "a urna não separa quem não escolheu",
    "sp_tarcisio": "agenda com governador: a régua mede terceira via, não palanque",
    "mg_cleitinho": "agenda com governador: a régua mede terceira via, não palanque",
    "rj_ruas": "agenda com governador: a régua mede terceira via, não palanque",
    "comparecimento": "eleitor novo: a régua mede terceira via, não comparecimento",
}


def _i(x: float | None) -> int | None:
    return None if x is None else round(x)


def _r(x: float | None, casas: int = 4) -> float | None:
    return None if x is None else round(x, casas)


def _soma(linhas: Iterable[dict]) -> dict[str, Any]:
    linhas = list(linhas)
    s = T.somar(
        linhas,
        (
            "estoque",
            "saldo",
            "saldo_df",
            "saldo_urna",
            "saldo_urna_regiao",
            "saldo_razao",
            "para_flavio_urna",
            "para_lula_urna",
        ),
    )
    e = s["estoque"]
    return {
        "municipios": len(linhas),
        "estoque": _i(e),
        "nexus": _i(s["saldo"]),
        "datafolha": _i(s["saldo_df"]),
        "urna": _i(s["saldo_urna"]),
        "urna_regiao": _i(s["saldo_urna_regiao"]),
        "razao_simples": _i(s["saldo_razao"]),
        "urna_para_flavio": _i(s["para_flavio_urna"]),
        "urna_para_lula": _i(s["para_lula_urna"]),
        "pv_nexus": _r(s["saldo"] / e) if e else None,
        "pv_datafolha": _r(s["saldo_df"] / e) if e else None,
        "pv_urna": _r(s["saldo_urna"] / e) if e else None,
        "diferenca_nexus_urna": _i(s["saldo"] - s["saldo_urna"]),
    }


def preparar(brasil: list[dict]) -> dict[str, float]:
    """Piso, teto, decomposição e motivo em cada linha; devolve as médias do país."""
    e = sum(m["estoque"] for m in brasil)
    nac = {
        "pv_nexus": sum(m["saldo"] for m in brasil) / e,
        "pv_urna": sum(m["saldo_urna"] for m in brasil) / e,
    }
    for m in brasil:
        m["piso"], m["teto_reguas"] = T.piso_teto(m["saldo"], m["saldo_urna"])
        pv = m["saldo_por_voto"] if m["saldo_por_voto"] is not None else nac["pv_nexus"]
        partes = T.decompor(pv, nac["pv_nexus"], m["pv_urna"], nac["pv_urna"])
        m["regua_partes"] = partes
        m["regua_motivo"] = T.motivo(partes)
    return nac


def _item(
    m: dict, posicoes: dict[str, dict[str, int]], listas: dict[str, set]
) -> dict[str, Any]:
    cd = m["cd"]
    return {
        "cd": cd,
        "ibge": m["ibge"],
        "uf": m["uf"],
        "nome": m["nome"],
        "regiao": m["regiao"],
        "capital": m["capital"],
        "classe": m["classe"],
        "estoque": m["estoque"],
        **{g: m[g] for g in T.GRUPOS},
        "nexus": _i(m["saldo"]),
        "datafolha": _i(m["saldo_df"]),
        "urna": _i(m["saldo_urna"]),
        "piso": _i(m["piso"]),
        "teto": _i(m["teto_reguas"]),
        "pv_nexus": _r(m["saldo_por_voto"]),
        "pv_urna": _r(m["pv_urna"]),
        "posicao": {v: posicoes[v].get(cd) for v in VERSOES},
        "situacao": T.situacao(cd in listas["pesquisa"], cd in listas["urna"]),
        "motivo": m["regua_motivo"],
        "partes": {k: _r(v) for k, v in m["regua_partes"].items()},
    }


def _ordem(linhas: Sequence[dict], campo: str) -> list[dict]:
    return sorted(linhas, key=lambda m: (-m[campo], m["cd"]))


def rankings(brasil: list[dict]) -> dict[str, Any]:
    """Os 100 e os 10 por UF nas três versões, com robustos e divergentes."""
    ordens = {v: _ordem(brasil, campo) for v, campo in VERSOES.items()}
    posicoes = {
        v: {m["cd"]: k for k, m in enumerate(o, start=1)} for v, o in ordens.items()
    }
    listas = {v: {m["cd"] for m in o[:N_TOP]} for v, o in ordens.items()}
    top = {
        v: [_item(m, posicoes, listas) for m in o[:N_TOP]] for v, o in ordens.items()
    }
    robustos = listas["pesquisa"] & listas["urna"]
    por_uf: dict[str, dict[str, list]] = defaultdict(dict)
    ufs = sorted({m["uf"] for m in brasil})
    for uf in ufs:
        dentro = [m for m in brasil if m["uf"] == uf]
        listas_uf = {}
        for v, campo in VERSOES.items():
            o = _ordem(dentro, campo)[:N_UF]
            listas_uf[v] = {m["cd"] for m in o}
            por_uf[uf][v] = o
        for v in VERSOES:
            por_uf[uf][v] = [
                {
                    "cd": m["cd"],
                    "nome": m["nome"],
                    "nexus": _i(m["saldo"]),
                    "urna": _i(m["saldo_urna"]),
                    "situacao": T.situacao(
                        m["cd"] in listas_uf["pesquisa"], m["cd"] in listas_uf["urna"]
                    ),
                }
                for m in por_uf[uf][v]
            ]
        por_uf[uf]["robustos"] = len(listas_uf["pesquisa"] & listas_uf["urna"])
    divergentes = []
    for v, outra in (("pesquisa", "urna"), ("urna", "pesquisa")):
        for x in top[v]:
            if x["cd"] not in listas[outra]:
                divergentes.append(x)
    motivos = defaultdict(int)
    for x in divergentes:
        motivos[f"{x['situacao']}:{x['motivo']}"] += 1
    return {
        "versoes": {
            "pesquisa": "saldo esperado pela matriz Nexus",
            "urna": "saldo esperado pela régua da urna de 2022 (classe de margem)",
            "combinacao": "ordem pelo piso (menor saldo das duas réguas); o teto é o maior",
        },
        "top": top,
        "robustos": len(robustos),
        "robustos_estoque": sum(m["estoque"] for m in brasil if m["cd"] in robustos),
        "so_pesquisa": len(listas["pesquisa"] - listas["urna"]),
        "so_urna": len(listas["urna"] - listas["pesquisa"]),
        "combinacao_robustos": sum(
            1 for x in top["combinacao"] if x["situacao"] == "robusto"
        ),
        "divergentes": divergentes,
        "motivos_divergencia": dict(sorted(motivos.items())),
        "por_uf": dict(por_uf),
        "por_regiao_top": {
            v: {r: sum(1 for x in top[v] if x["regiao"] == r) for r in REGIOES}
            for v in VERSOES
        },
    }


def totais(brasil: list[dict], ic: list[float | None]) -> dict[str, Any]:
    nac = _soma(brasil)
    nac["urna_ic95"] = ic
    por_regiao = {r: _soma(m for m in brasil if m["regiao"] == r) for r in REGIOES}
    por_classe = {c: _soma(m for m in brasil if m["classe"] == c) for c in T.CLASSES}
    por_uf = {}
    for uf in sorted({m["uf"] for m in brasil}):
        dentro = [m for m in brasil if m["uf"] == uf]
        por_uf[uf] = {**_soma(dentro), "regiao": dentro[0]["regiao"]}
    return {"brasil": nac, "regioes": por_regiao, "classes": por_classe, "ufs": por_uf}


def movimentos(brasil: list[dict], estrategia: dict) -> list[dict]:
    """Os dez movimentos do capítulo 13 com o número de cada régua."""
    saida = []
    for mv in sorted(estrategia["movimentos"], key=lambda x: x.get("ordem", 99)):
        linha = {
            "id": mv["id"],
            "ordem": mv.get("ordem"),
            "titulo": mv["titulo"],
            "pesquisa": mv["votos_esperados"],
            "rotulo_pesquisa": mv.get("rotulo"),
        }
        if mv["id"] in MOVIMENTO_COLUNAS:
            cols = MOVIMENTO_COLUNAS[mv["id"]]
            votos = sum(sum(m[c] for c in cols) for m in brasil)
            urna = sum(sum(m[c] for c in cols) * m["pv_urna"] for m in brasil)
            linha.update(
                {
                    "alvo_brasil": votos,
                    "urna": _i(urna),
                    "pv_urna": _r(urna / votos) if votos else None,
                    "concordam": (urna > 0) == (mv["votos_esperados"] > 0),
                }
            )
        elif mv["id"] == "ne_interior":
            ne = [m for m in brasil if m["regiao"] == "Nordeste"]
            urna = sum(m["saldo_urna"] for m in ne)
            linha.update(
                {
                    "alvo_brasil": sum(m["estoque"] for m in ne),
                    "urna": _i(urna),
                    "concordam": (urna > 0) == (mv["votos_esperados"] > 0),
                    "nota": "a regra do capítulo já é analogia de 2022 (razão simples); aqui, a regressão",
                }
            )
        else:
            linha.update(
                {"urna": None, "concordam": None, "nota": SEM_REGUA.get(mv["id"], "")}
            )
        saida.append(linha)
    return saida
