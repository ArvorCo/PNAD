"""Leitura das pesquisas de governador e pares de 2º turno medidos.

Reaproveita a média por recência do Senado (`senado_2026.base`): a diferença
é que cada onda pode trazer uma lista `segundo_turno` com os pares medidos pelo
instituto, que aqui viram médias próprias, uma por par.
"""

from __future__ import annotations

import copy
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

from senado_2026 import base as SB
from senado_2026.base import (
    CAMPOS,
    CORTE_CAMPO,
    DATA_REFERENCIA,
    ELEICAO,
    MEIA_VIDA_DIAS,
    UFS,
    decaimento,
    meio,
)
from senado_2026.tse import normalizar

from .tse import APELIDOS, DESEMPATE, PESQUISAS, SAIDA

__all__ = [
    "CAMPOS",
    "CORTE_CAMPO",
    "DATA_REFERENCIA",
    "ELEICAO",
    "MEIA_VIDA_DIAS",
    "PESQUISAS",
    "SAIDA",
    "UFS",
]

ROOT = SB.ROOT
PASTA = SAIDA
ler_opcional = SB.ler_opcional
# Nenhuma candidatura a governador retirada depois do prazo foi declarada.
RETIRADAS: dict[tuple[str, str], tuple[date, str]] = {}
OUTROS_RE = re.compile(r"^outros?(\s+candidatos?)?$", re.IGNORECASE)


class Tse(SB.Tse):
    """Casamento com as candidaturas a governador e as tabelas deste cargo."""

    def __init__(self, pasta: Path = PASTA, docs: Path = SB.DOCS):
        super().__init__(pasta=pasta, docs=docs)

    def sq(self, uf: str, nome: str) -> str | None:
        norma = normalizar(nome)
        sq = self.casados.get((uf, norma))
        if sq:
            return sq
        alvo = APELIDOS.get((uf, norma), norma)
        if (uf, alvo) in DESEMPATE:
            return DESEMPATE[(uf, alvo)]
        achados = {
            c["sq_candidato"]
            for c in self.candidatos
            if c["uf"] == uf
            and alvo in {normalizar(c["nome_urna"]), normalizar(c["nome_completo"])}
        }
        return next(iter(achados)) if len(achados) == 1 else None


def _separar_outros(dados: dict) -> dict:
    """Candidatura chamada 'Outros' no painel vira a categoria `outros`."""
    d = copy.deepcopy(dados)
    mantidos, soma = [], 0.0
    for c in d.get("candidatos") or []:
        if OUTROS_RE.match((c.get("nome") or "").strip()):
            soma += float(c.get("valor") or 0.0)
        else:
            mantidos.append(c)
    if soma:
        d["candidatos"] = mantidos
        d["outros"] = float(d.get("outros") or 0.0) + soma
    return d


def _par(bloco: dict) -> dict | None:
    cands = [c for c in bloco.get("candidatos") or [] if c.get("valor") is not None]
    if len(cands) != 2:
        return None
    return {
        "codigo": bloco.get("codigo"),
        "pagina": bloco.get("pagina"),
        "candidatos": [
            {
                "nome_pesquisa": c["nome"],
                "partido_pesquisa": SB.sigla(c.get("partido")),
                "valor": float(c["valor"]),
            }
            for c in cands
        ],
        "indecisos": bloco.get("indecisos"),
        "branco_nulo": bloco.get("branco_nulo"),
        "soma_total": bloco.get("soma_total"),
    }


def normalizar_onda(dados: dict, arquivo: str, n_ausente: int) -> dict:
    onda = SB.normalizar_onda(
        _separar_outros(dados), arquivo, n_ausente, retiradas_tabela=RETIRADAS
    )
    pares = [_par(b) for b in dados.get("segundo_turno") or []]
    onda["segundo_turno"] = [p for p in pares if p]
    onda["cenarios_alternativos"] = len(dados.get("cenarios_alternativos") or [])
    onda["pergunta_cenario"] = (dados.get("pergunta") or {}).get("cenario")
    return onda


def ler_pesquisas(pasta: Path = PESQUISAS, n_ausente: int | None = None) -> list[dict]:
    if not pasta.exists():
        return []
    n_ausente = n_ausente or SB.n_minimo(pasta)
    return [
        normalizar_onda(SB.ler_json(arq), arq.name, n_ausente)
        for arq in sorted(pasta.glob("*.json"))
    ]


# ------------------------------------------------------------- 2º turno medido


def pares_medidos(
    ondas: list[dict],
    uf: str,
    pessoas: list[dict],
    tse: Tse,
    *,
    meia_vida: float = MEIA_VIDA_DIAS,
    hoje: date = DATA_REFERENCIA,
) -> tuple[dict[tuple[int, int], dict], list[dict]]:
    """Média por recência de cada par de 2º turno medido no estado.

    Para cada par (índices na lista de pessoas da média do 1º turno), entra a
    onda mais recente de cada casa que mediu o par, com peso por recência e
    peso igual entre casas. A fração publicada é a do primeiro nome do par
    entre os dois (indecisos e branco/nulo fora), como no 2º turno real.
    Devolve (pares, pares cujos nomes não casam com a média do 1º turno).
    """
    por_par: dict[tuple[int, int], dict[str, dict]] = defaultdict(dict)
    nao_casados: list[dict] = []
    for o in ondas:
        if o["uf"] != uf or SB.motivo_descarte(o):
            continue
        for bloco in o["segundo_turno"]:
            idx = [
                SB.localizar_pessoa(uf, c["nome_pesquisa"], pessoas, tse)
                for c in bloco["candidatos"]
            ]
            if None in idx or idx[0] == idx[1]:
                nao_casados.append(
                    {
                        "arquivo": o["arquivo"],
                        "par": [c["nome_pesquisa"] for c in bloco["candidatos"]],
                    }
                )
                continue
            a, b = idx
            va, vb = (c["valor"] for c in bloco["candidatos"])
            if a > b:
                a, b, va, vb = b, a, vb, va
            if va + vb <= 0:
                continue
            chave = (a, b)
            atual = por_par[chave].get(o["casa"])
            ordem = (o["divulgacao"] or o["campo_fim"], o["campo_fim"])
            if atual and atual["ordem"] >= ordem:
                continue
            por_par[chave][o["casa"]] = {
                "ordem": ordem,
                "onda": o,
                "bloco": bloco,
                "fracao_a": va / (va + vb),
                "va": va,
                "vb": vb,
            }
    saida: dict[tuple[int, int], dict] = {}
    for chave, casas in por_par.items():
        itens = list(casas.values())
        pesos = [
            decaimento(
                hoje.toordinal()
                - meio(it["onda"]["campo_inicio"], it["onda"]["campo_fim"]),
                meia_vida,
            )
            for it in itens
        ]
        total = sum(pesos)
        pesos = [w / total for w in pesos]
        fracao = sum(w * it["fracao_a"] for w, it in zip(pesos, itens, strict=True))
        # n efetivo do par: entrevistados que escolheram um dos dois, somados
        # pelas casas com os pesos (precisão combinada, não soma bruta).
        n_par = sum(
            w * it["onda"]["n_usado"] * (it["va"] + it["vb"]) / 100.0
            for w, it in zip(pesos, itens, strict=True)
        )
        saida[chave] = {
            "fracao_a": fracao,
            "n_par": n_par,
            "recente": any(it["onda"]["campo_fim"] >= CORTE_CAMPO for it in itens),
            "dias_ate_eleicao": sum(
                w * (ELEICAO - it["onda"]["campo_fim"]).days
                for w, it in zip(pesos, itens, strict=True)
            ),
            "ondas": [
                {
                    "arquivo": it["onda"]["arquivo"],
                    "instituto": it["onda"]["instituto"],
                    "casa": it["onda"]["casa"],
                    "peso": w,
                    "campo_fim": it["onda"]["campo_fim"].isoformat(),
                    "pagina": it["bloco"]["pagina"],
                    "codigo": it["bloco"]["codigo"],
                    "publicado": {
                        c["nome_pesquisa"]: c["valor"]
                        for c in it["bloco"]["candidatos"]
                    },
                    "indecisos": it["bloco"]["indecisos"],
                    "branco_nulo": it["bloco"]["branco_nulo"],
                }
                for w, it in zip(pesos, itens, strict=True)
            ],
        }
    return saida, nao_casados
