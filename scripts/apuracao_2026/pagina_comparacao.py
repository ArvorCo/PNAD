"""Blocos de 2022 contra 2026 (comparacao_2022.json), encaixados nos capítulos 04, 06 a 09.

Cada bloco é opcional: sem o arquivo, ou com chave ausente, vira bloco pendente
com aviso, e o capítulo segue.
"""

from __future__ import annotations

from html import escape

from .pagina_comum import (
    CAMPOS,
    ERROS_DE_DADO,
    ROTULO_CAMPO,
    Dados,
    bloco_pendente,
    num,
    p,
    sinal,
    sinal_int,
    tabela,
)
from .pagina_texto import lista

ARQ = "comparacao_2022.json"
BLOCOS = ["direita + centro-direita", "centro", "esquerda + centro-esquerda"]
ROT_BLOCO = {
    "direita + centro-direita": "Direita e centro-direita",
    "centro": "Centro",
    "esquerda + centro-esquerda": "Esquerda e centro-esquerda",
}


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


def _tabela_blocos(
    antes: dict, depois: dict, rot_a: str, rot_b: str, legenda: str
) -> str:
    return tabela(
        ["Bloco", rot_a, rot_b, "Variação"],
        [
            [
                ROT_BLOCO[b],
                antes.get(b, 0),
                depois.get(b, 0),
                sinal_int(depois.get(b, 0) - antes.get(b, 0)),
            ]
            for b in BLOCOS
        ],
        legenda,
    )


@_seguro
def regioes(comp: dict) -> str:
    pr = comp["presidente"]
    acima = pr["flavio_acima_bolsonaro_2t"]
    s2 = pr["saldo_nacional"]["vs_2t"]
    return "<h3>Contra o 2º turno de 2022</h3>" + p(
        f"Flávio já supera o 2º turno de Bolsonaro em {pr['n_ufs_flavio_acima_bolsonaro_2t']} UFs: "
        + lista([f"{x['uf']} ({sinal(x['pp'], 2)})" for x in acima])
        + f". No país, contra o 2º turno de 2022, Flávio tem {sinal_int(s2['direita_flavio_menos_bolsonaro'])} votos e "
        f"Lula {sinal_int(s2['esquerda_lula_menos_lula'])}. Os dois finalistas de 2026 somam menos que os de 2022 no 2º turno; "
        "a diferença está na terceira via, nos brancos e nulos e na abstenção.",
        "verificado",
    )


@_seguro
def camara(comp: dict) -> str:
    c = comp["camara"]
    a, b = c["por_campo_2022"], c["por_campo_2026"]
    pc = {x["chave"]: x for x in c["proporcionalidade"]["campos_2026"]["linhas"]}
    rn = c["renovacao"]
    ganhos = c["maiores_ganhos_cadeiras"][:3]
    perdas = c["maiores_perdas_cadeiras"][:3]
    h = "<h3>Contra a Câmara eleita em 2022</h3>"
    h += p(
        f"A direita foi de {a['direita']} para {b['direita']} cadeiras ({sinal_int(b['direita'] - a['direita'])}). "
        f"O bloco de direita e centro-direita foi de {c['por_bloco_2022']['direita + centro-direita']} para "
        f"{c['por_bloco_2026']['direita + centro-direita']}; os três quintos ({c['limiares']['tres_quintos']}) seguem fora "
        "de alcance. Maiores ganhos: "
        + lista(
            [f"{escape(x['partido'])} {sinal_int(x['delta_cadeiras'])}" for x in ganhos]
        )
        + ". Maiores perdas: "
        + lista(
            [f"{escape(x['partido'])} {sinal_int(x['delta_cadeiras'])}" for x in perdas]
        )
        + f". Foram reeleitos {rn['reeleitos']} deputados; {rn['novos']} são novos.",
        "verificado",
    )
    h += tabela(
        [
            "Campo",
            "2022",
            "2026",
            "Variação",
            "% dos votos 2026",
            "% das cadeiras 2026",
        ],
        [
            [
                ROTULO_CAMPO[k],
                a.get(k, 0),
                b.get(k, 0),
                sinal_int(b.get(k, 0) - a.get(k, 0)),
                num(pc[k]["pct_votos"], 2) if k in pc else "",
                num(pc[k]["pct_cadeiras"], 2) if k in pc else "",
            ]
            for k in CAMPOS
        ],
        "Cadeiras por campo em 2022 e 2026; partidos extintos somados ao sucessor declarado. Fonte: comparacao_2022.json.",
    )
    return h


@_seguro
def senado(comp: dict) -> str:
    s = comp["senado"]
    a, b = s["senado_2023"]["por_bloco"], s["senado_2027"]["por_bloco"]
    c18 = s["classe_2018_composicao"]["por_campo"]
    c26 = s["classe_2026_composicao"]["por_campo"]
    pl = s["delta_2027_2023_partido"].get("PL")
    h = "<h3>Contra o Senado eleito de 2023</h3>"
    h += p(
        f"As 54 vagas em disputa eram, desde 2018, de {c18.get('direita', 0)} senadores de direita; agora são de "
        f"{c26.get('direita', 0)}. Entre o Senado eleito de 2023 e o de 2027, o PL ganhou {sinal_int(pl)} cadeiras. "
        "Comparação pelos eleitos da urna, não pelos titulares atuais.",
        "verificado",
    )
    h += _tabela_blocos(
        a, b, "2023 (eleitos)", "2027", "Senado por bloco. Fonte: comparacao_2022.json."
    )
    return h


@_seguro
def assembleias(comp: dict) -> str:
    o = comp["assembleias"]["onze_casas"]
    h = p(
        f"Nas mesmas {len(comp['assembleias']['casas'])} assembleias, a direita somou "
        f"{sinal_int(o['delta_campo']['direita'])} cadeiras contra 2022, e o bloco de esquerda e centro-esquerda "
        f"{sinal_int(o['delta_bloco']['esquerda + centro-esquerda'])}.",
        "verificado",
    )
    return h + _tabela_blocos(
        o["por_bloco_2022"],
        o["por_bloco_2026"],
        "2022",
        "2026",
        f"{o['vagas']} cadeiras nas onze casas.",
    )


@_seguro
def governadores(comp: dict) -> str:
    g = comp["governadores"]
    mb = g["decididos_mudaram_bloco"]
    return p(
        f"Em 2022, {g['decididos_2022_1t']} estados decidiram o governo no 1º turno; em 2026, {g['decididos_2026']}. Dos "
        f"eleitos agora, {len(mb)} são de bloco diferente do eleito em 2022 ({lista(mb)}).",
        "verificado",
    )
