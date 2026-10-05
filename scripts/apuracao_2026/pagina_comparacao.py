"""Blocos de 2022 contra 2026 (comparacao_2022.json), encaixados nos capítulos 04, 06 a 09.

Cada bloco é opcional: sem o arquivo, ou com chave ausente, vira bloco pendente
com aviso, e o capítulo segue.
"""

from __future__ import annotations

from html import escape

from .pagina_comum import (
    ERROS_DE_DADO,
    Dados,
    bloco_pendente,
    p,
    sinal_int,
)
from .pagina_texto import lista

ARQ = "comparacao_2022.json"


def _seguro(fn):
    def envolto(d: Dados) -> str:
        comp = d.get(ARQ)
        if comp is None:
            return bloco_pendente(ARQ)
        try:
            return fn(comp)
        except ERROS_DE_DADO as erro:
            d.aviso(f"{ARQ}: bloco {fn.__name__} sem a chave {erro}")
            return bloco_pendente(f"{ARQ} (chave ausente: {erro})")

    return envolto


@_seguro
def regioes(comp: dict) -> str:
    pr = comp["presidente"]
    s2 = pr["saldo_nacional"]["vs_2t"]
    return p(
        f"Contra o 2º turno de 2022, Flávio já supera Bolsonaro em {pr['n_ufs_flavio_acima_bolsonaro_2t']} UFs e tem "
        f"{sinal_int(s2['direita_flavio_menos_bolsonaro'])} votos; Lula, {sinal_int(s2['esquerda_lula_menos_lula'])}. "
        "A diferença para o 2º turno está na terceira via, nos brancos e nulos e na abstenção.",
        "verificado",
    )


@_seguro
def camara(comp: dict) -> str:
    c = comp["camara"]
    a, b = c["por_campo_2022"], c["por_campo_2026"]
    rn = c["renovacao"]
    ganhos = c["maiores_ganhos_cadeiras"][:3]
    perdas = c["maiores_perdas_cadeiras"][:3]
    return p(
        f"Contra a Câmara de 2022, a direita foi de {a['direita']} para {b['direita']} cadeiras "
        f"({sinal_int(b['direita'] - a['direita'])}); o bloco de direita e centro-direita foi de "
        f"{c['por_bloco_2022']['direita + centro-direita']} para {c['por_bloco_2026']['direita + centro-direita']}. "
        "Maiores ganhos: "
        + lista(
            [f"{escape(x['partido'])} {sinal_int(x['delta_cadeiras'])}" for x in ganhos]
        )
        + ". Maiores perdas: "
        + lista(
            [f"{escape(x['partido'])} {sinal_int(x['delta_cadeiras'])}" for x in perdas]
        )
        + f". {rn['reeleitos']} deputados foram reeleitos; {rn['novos']} são novos.",
        "verificado",
    )


@_seguro
def senado(comp: dict) -> str:
    s = comp["senado"]
    c18 = s["classe_2018_composicao"]["por_campo"]
    c26 = s["classe_2026_composicao"]["por_campo"]
    pl = s["delta_2027_2023_partido"].get("PL")
    return p(
        f"As 54 vagas em disputa eram, desde 2018, de {c18.get('direita', 0)} senadores de direita; agora são de "
        f"{c26.get('direita', 0)}. Entre o Senado de 2023 e o de 2027, o PL ganhou {sinal_int(pl)} cadeiras "
        "(eleitos da urna, não titulares atuais).",
        "verificado",
    )


@_seguro
def assembleias(comp: dict) -> str:
    o = comp["assembleias"]["onze_casas"]
    return p(
        f"Nas mesmas {len(comp['assembleias']['casas'])} assembleias, a direita somou "
        f"{sinal_int(o['delta_campo']['direita'])} cadeiras contra 2022; esquerda e centro-esquerda, "
        f"{sinal_int(o['delta_bloco']['esquerda + centro-esquerda'])}.",
        "verificado",
    )


@_seguro
def governadores(comp: dict) -> str:
    g = comp["governadores"]
    mb = g["decididos_mudaram_bloco"]
    return p(
        f"Em 2022, {g['decididos_2022_1t']} estados decidiram o governo no 1º turno; em 2026, {g['decididos_2026']}. "
        f"{len(mb)} dos eleitos agora são de bloco diferente do de 2022 ({lista(mb)}).",
        "verificado",
    )
