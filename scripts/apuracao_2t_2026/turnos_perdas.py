"""Municípios em que um finalista teve menos votos absolutos no 2º turno do que no 1º.

Leitura pura de ``comparacao_1t.json`` (listas ``flavio_perdeu_votos`` e
``lula_perdeu_votos``, completadas pela tabela ``municipios`` pela chave ``cd_tse``)
e de ``governadores.json`` (as UFs listadas ali tiveram 2º turno de governador).
Serve ao capítulo "1º turno × 2º turno" do dossiê e às duas listas CSV do dataset;
nada é digitado aqui.

Rótulo: votos absolutos, não fatia dos válidos; menos votos não identifica eleitor
nem motivo.

Decomposição declarada da perda ``P`` de um município (em votos, positiva), com ``Q``
a queda do comparecimento em eleitores (zero quando o comparecimento não caiu):

- teto: ``min(P, Q)``, como se todo eleitor que deixou de votar fosse do candidato;
  ``P`` menos o teto é o mínimo que a queda do comparecimento não cobre;
- proporcional: ``min(P, Q × X1 / C1)``, com ``X1`` os votos do candidato e ``C1``
  o comparecimento do 1º turno no município, como se quem deixou de votar votasse
  como o município votou no 1º turno.

As duas são contas sob hipótese declarada (Inferência), não identificação de eleitor.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

ROTULO = (
    "votos absolutos, não fatia dos válidos; "
    "menos votos não identifica eleitor nem motivo"
)
CANDIDATOS = ("flavio", "lula")
NOME = {"flavio": "Flávio", "lula": "Lula"}
ADVERSARIO = {"flavio": "lula", "lula": "flavio"}
# (chave, comparecimento caiu, adversário ganhou votos)
CATEGORIAS = (
    ("caiu_sem_ganho", True, False),
    ("caiu_com_ganho", True, True),
    ("manteve_com_ganho", False, True),
    ("manteve_sem_ganho", False, False),
)


def tabela(bloco: dict[str, Any]) -> list[dict[str, Any]]:
    """``{'colunas': [...], 'linhas': [[...]]}`` vira lista de dicionários."""
    cols = bloco["colunas"]
    return [dict(zip(cols, r, strict=True)) for r in bloco["linhas"]]


def ufs_governador(G: dict[str, Any] | None) -> set[str]:
    """UFs com 2º turno de governador: as listadas em ``governadores.json``."""
    return {u["uf"] for u in (G or {}).get("ufs", [])}


def municipios(
    C1: dict[str, Any], quem: str, gov: set[str] | frozenset[str] = frozenset()
) -> list[dict[str, Any]]:
    """Linhas completas dos municípios em que ``quem`` perdeu votos, com a decomposição.

    Ordem: maior perda primeiro; empate por UF e nome.
    """
    completos = {m["cd_tse"]: m for m in tabela(C1["municipios"])}
    out = []
    for x in tabela(C1[f"{quem}_perdeu_votos"]["lista"]):
        m = completos[x["cd_tse"]]
        perda = -m[f"delta_votos_{quem}"]
        if perda <= 0:
            raise ValueError(f"{m['cd_tse']}: lista de perda com saldo {perda}")
        queda = max(0, -m["delta_comparecimento_votos"])
        teto = min(perda, queda)
        c1 = m["t1_comparecimento"]
        esperado = queda * m[f"t1_{quem}"] / c1 if c1 else 0.0
        prop = min(float(perda), esperado)
        out.append(
            {
                **m,
                "perda": perda,
                "queda_comparecimento": queda,
                "teto_comparecimento": teto,
                "alem_teto": perda - teto,
                "proporcional_comparecimento": prop,
                "alem_proporcional": perda - prop,
                "governador_2t": m["uf"] in gov,
            }
        )
    out.sort(key=lambda r: (-r["perda"], r["uf"], r["nome"]))
    return out


def _soma(lista: list[dict[str, Any]], chave: str) -> Any:
    return sum(m[chave] for m in lista)


def resumo(
    C1: dict[str, Any], quem: str, gov: set[str] | frozenset[str] = frozenset()
) -> dict[str, Any]:
    """Totais, as quatro situações, a decomposição somada e a contagem por UF."""
    ms = municipios(C1, quem, gov)
    da = f"delta_votos_{ADVERSARIO[quem]}"
    categorias = []
    for chave, caiu, ganhou in CATEGORIAS:
        sel = [
            m
            for m in ms
            if (m["delta_comparecimento_votos"] < 0) == caiu and (m[da] > 0) == ganhou
        ]
        categorias.append(
            {
                "chave": chave,
                "comparecimento_caiu": caiu,
                "adversario_ganhou": ganhou,
                "n": len(sel),
                "perda": _soma(sel, "perda"),
                "delta_adversario": _soma(sel, da),
                "delta_comparecimento": _soma(sel, "delta_comparecimento_votos"),
                "teto": _soma(sel, "teto_comparecimento"),
                "proporcional": _soma(sel, "proporcional_comparecimento"),
            }
        )
    regioes = Counter(m["regiao"] for m in ms)
    alem_teto = [m for m in ms if m["alem_teto"] > 0]
    alem_prop = [m for m in ms if m["alem_proporcional"] > 0]
    cont = Counter(m["uf"] for m in ms)
    perda_uf: Counter[str] = Counter()
    for m in ms:
        perda_uf[m["uf"]] += m["perda"]
    por_uf = [
        {
            "uf": u["uf"],
            "nome": u["nome_uf"],
            "n": cont.get(u["uf"], 0),
            "n_uf": u["n_municipios"],
            "perda": perda_uf.get(u["uf"], 0),
            "governador_2t": u["uf"] in gov,
        }
        for u in C1["ufs"]
    ]
    return {
        "quem": quem,
        "adversario": ADVERSARIO[quem],
        "n": len(ms),
        "n_universo": C1["n_municipios_completos"],
        "aptos": _soma(ms, "aptos"),
        "aptos_universo": C1["brasil"]["aptos"],
        "perda": _soma(ms, "perda"),
        "delta_adversario": _soma(ms, da),
        "n_adversario_ganhou": sum(m[da] > 0 for m in ms),
        "n_adversario_perdeu": sum(m[da] < 0 for m in ms),
        "n_adversario_igual": sum(m[da] == 0 for m in ms),
        "n_comparecimento_caiu": sum(m["delta_comparecimento_votos"] < 0 for m in ms),
        "delta_comparecimento": _soma(ms, "delta_comparecimento_votos"),
        "teto": _soma(ms, "teto_comparecimento"),
        "alem_teto": _soma(ms, "alem_teto"),
        "n_alem_teto": len(alem_teto),
        "n_alem_teto_adversario_cobre": sum(m[da] >= m["alem_teto"] for m in alem_teto),
        "proporcional": _soma(ms, "proporcional_comparecimento"),
        "alem_proporcional": _soma(ms, "alem_proporcional"),
        "n_alem_proporcional": len(alem_prop),
        "n_alem_proporcional_adversario_cobre": sum(
            m[da] >= m["alem_proporcional"] for m in alem_prop
        ),
        "n_governador_2t": sum(m["governador_2t"] for m in ms),
        "categorias": categorias,
        "por_regiao": dict(regioes.most_common()),
        "por_uf": por_uf,
        "maior": ms[0] if ms else None,
    }


def contexto_governador(
    C1: dict[str, Any], gov: set[str] | frozenset[str]
) -> dict[str, Any]:
    """Queda do comparecimento nas UFs com e sem 2º turno de governador, todos os municípios."""
    ms = [m for m in tabela(C1["municipios"]) if m.get("completo", True)]

    def grupo(sel: list[dict[str, Any]]) -> dict[str, Any]:
        caiu = sum(m["delta_comparecimento_votos"] < 0 for m in sel)
        return {
            "n": len(sel),
            "comparecimento_caiu": caiu,
            "pct": 100 * caiu / len(sel) if sel else None,
        }

    return {
        "ufs": sorted(gov),
        "com": grupo([m for m in ms if m["uf"] in gov]),
        "sem": grupo([m for m in ms if m["uf"] not in gov]),
        "por_uf": [
            {"uf": uf, **grupo([m for m in ms if m["uf"] == uf])} for uf in sorted(gov)
        ],
    }
