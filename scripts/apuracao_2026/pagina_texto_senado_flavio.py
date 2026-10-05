"""Texto do capítulo 7 sobre o Senado contra Flávio, gerado de `senado_x_flavio.json`.

Nenhum número é digitado: tudo sai do JSON. Cada figura vem antes do parágrafo
que a lê. Limites fixos da casa ao fim: não é transferência, não é pessoa, não é
previsão; dois votos por eleitor.
"""

from __future__ import annotations

from html import escape

from .dados import REGIAO_UF
from .pagina_comum import (
    NOME_UF,
    Dados,
    bloco_pendente,
    checar,
    inteiro,
    milhoes,
    nome_proprio,
    num,
    p,
    sinal,
)
from .pagina_texto import fig, lista, pct

TITULO = "Os senadores que rendem mais que o presidenciável"
# Preposição contraída antes do nome da UF ("no Paraná", "na Bahia", "em Minas Gerais").
NO = {
    "AC",
    "AM",
    "AP",
    "CE",
    "DF",
    "ES",
    "MA",
    "PA",
    "PI",
    "PR",
    "RJ",
    "RN",
    "RS",
    "TO",
}
NA = {"BA", "PB"}


def em_uf(uf: str) -> str:
    """'no Paraná', 'na Bahia', 'em São Paulo'."""
    prep = "no" if uf in NO else "na" if uf in NA else "em"
    return f"{prep} {NOME_UF[uf]}"


CHAVES = [
    "nacional.pl",
    "nacional.aliados",
    "nacional.melhor",
    "ufs",
    "blocos.alinhados_lula",
    "carregadores.candidatos",
    "mapa.ufs",
    "limites",
]


def _uf_val(u: dict, chave: str) -> str:
    return f"{u['uf']} {sinal(u[chave]['div_pp'], 1)}"


def somas(S: dict) -> str:
    n = S["nacional"]
    pl, al, fl = n["pl"], n["aliados"], n["flavio"]
    ufs = [u for u in S["ufs"] if u["aliados"]["div_pp"] is not None]
    ordem = sorted(ufs, key=lambda u: -u["aliados"]["div_pp"])
    acima = [u for u in ordem if u["aliados"]["div_pp"] > 0][:3]
    abaixo = [u for u in ordem if u["aliados"]["div_pp"] < 0][-3:][::-1]
    return p(
        f"Somados, os nomes do PL ao Senado tiveram {milhoes(pl['votos'])} de votos, "
        f"{num(pl['votos_por_voto_flavio'], 2)} voto para cada voto de Flávio. Na base de votos do Senado, "
        f"que conta cada voto uma vez, são {pct(pl['pct'])}, contra {pct(fl['pct'])} de Flávio nos válidos de "
        f"presidente do eleitor residente: {num(abs(pl['div_pp']), 2)} pontos "
        f"{'abaixo' if pl['div_pp'] < 0 else 'acima'}. O bloco aliado, direita e centro-direita, somou "
        f"{milhoes(al['votos'])}, {pct(al['pct'])} da base, {num(abs(al['div_pp']), 2)} pontos "
        f"{'acima' if al['div_pp'] > 0 else 'abaixo'} de Flávio. O bloco passa Flávio em "
        f"{al['ufs_acima_de_flavio']} UFs; as maiores distâncias a favor estão em "
        + lista([_uf_val(u, "aliados") for u in acima])
        + ", e as maiores contra, em "
        + lista([_uf_val(u, "aliados") for u in abaixo])
        + ".",
        "verificado",
    )


def alinhados(S: dict) -> str:
    al = S["blocos"]["alinhados_lula"]
    eleitos = {e["sqcand"] for u in S["ufs"] for e in u["eleitos"]}
    nomes = [
        f"{nome_proprio(a['nome'])} ({a['uf']}{', eleito' if a['sqcand'] in eleitos else ''})"
        for a in al
    ]
    return p(
        f"Ficam fora do bloco {len(al)} candidaturas de direita e centro-direita do lado de Lula: "
        + lista(nomes)
        + ". A regra está declarada no script: aliado de Lula na exceção de campo da casa, ou coligação registrada "
        "no TSE com o PT e sem o PL.",
        "verificado",
    )


def achado_contrario(S: dict) -> str:
    n = S["nacional"]["pl"]
    com = [u for u in S["ufs"] if u["pl"]["n_candidatos"]]
    sem = [u["uf"] for u in S["ufs"] if not u["pl"]["n_candidatos"]]
    acima = [u for u in com if u["pl"]["div_pp"] > 0]
    dois = [u for u in com if u["pl"]["n_candidatos"] >= 2]
    razoes = [u["pl"]["votos_por_voto_flavio"] for u in dois]
    texto = (
        f"O achado contrário vem junto. O PL fica abaixo de Flávio em {n['ufs_abaixo_de_flavio']} das {len(com)} "
        "UFs onde lançou nome, e isso é o normal do Senado: o eleitor dá dois votos, o voto se divide entre "
        f"muitos nomes, e em {n['ufs_com_um_nome']} UFs o PL lançou um nome só, que não passa de metade da base. "
    )
    if acima:
        texto += (
            "Só fica acima em "
            + lista(
                [
                    f"{NOME_UF[u['uf']]} ({sinal(u['pl']['div_pp'], 1)}, {u['pl']['n_candidatos']} nomes)"
                    for u in acima
                ]
            )
            + ". "
        )
    if razoes:
        texto += (
            f"Onde lançou dois nomes ({len(dois)} UFs), a soma vai de {num(min(razoes), 2)} a "
            f"{num(max(razoes), 2)} votos por voto de Flávio. "
        )
    if sem:
        texto += f"Não houve nome do PL em {lista(sem)}."
    return p(texto.strip(), "inferencia")


def melhores(S: dict) -> str:
    ms = [(u, u["melhor"]) for u in S["ufs"] if u["melhor"]]
    base = [x for x in ms if x[1]["vao_pp"] > 0]
    vot = sorted(
        (x for x in ms if x[1]["vao_votantes_pp"] > 0),
        key=lambda x: -x[1]["vao_votantes_pp"],
    )
    nordeste = [u for u, _ in vot if REGIAO_UF[u["uf"].lower()] == "Nordeste"]
    fundo_u, fundo = min(ms, key=lambda x: x[1]["vao_votantes_pp"])

    def nome(u, m):
        return f"{nome_proprio(m['nome'])} ({escape(m['partido'])}-{u['uf']})"

    if base:
        frase_base = (
            "Na base de votos, "
            + (
                "só uma candidatura do bloco passa"
                if len(base) == 1
                else f"{len(base)} candidaturas do bloco passam"
            )
            + " Flávio: "
            + lista(
                [
                    f"{nome(u, m)}, {pct(m['pct'])} contra {pct(u['flavio']['pct'])}"
                    f"{', eleita' if m['eleito'] else ', sem se eleger'}"
                    for u, m in base
                ]
            )
            + ". "
        )
    else:
        frase_base = "Na base de votos, nenhuma candidatura do bloco passa Flávio. "
    texto = p(
        frase_base
        + f"Na régua de eleitores alcançados, a melhor candidatura do bloco chega a mais eleitores que Flávio em "
        f"{len(vot)} UFs, {len(nordeste)} delas no Nordeste: "
        + lista(
            [
                f"{u['uf']} {nome_proprio(m['nome'])} {sinal(m['vao_votantes_pp'], 1)}"
                for u, m in vot
            ]
        )
        + f". O mais fundo do outro lado é {nome(fundo_u, fundo)}, {sinal(fundo['vao_votantes_pp'], 1)} "
        f"em eleitores alcançados{', eleito mesmo assim' if fundo['eleito'] else ''}.",
        "verificado",
    )
    if vot:
        u, m = vot[0]
        texto += p(
            "Onde o senador do bloco alcança mais eleitores que Flávio, a diferença é, aproximadamente, um piso de "
            f"eleitores que escolheram o senador e não escolheram Flávio: {em_uf(u['uf'])}, pelo menos "
            f"{num(m['vao_votantes_pp'], 1)} pontos dos votantes, que votaram em Lula, em outro nome, em branco ou "
            "nulo para presidente. É teto endereçável para o 2º turno, não transferência.",
            "inferencia",
        )
    return texto


def carregadores(S: dict) -> str:
    C = S["carregadores"]["candidatos"]
    mapa = S["mapa"]["ufs"]
    frases = []
    for uf in mapa:
        cs = sorted(
            (c for c in C if c["uf"] == uf), key=lambda c: -c["municipios_acima_de_100"]
        )
        primeiro, resto = cs[0], cs[1:]
        frase = (
            f"{em_uf(uf)[0].upper()}{em_uf(uf)[1:]}, {nome_proprio(primeiro['nome'])} "
            f"({escape(primeiro['partido'])}) rende acima de Flávio em "
            f"{inteiro(primeiro['municipios_acima_de_100'])} de {inteiro(primeiro['municipios'])} municípios"
        )
        for c in resto:
            frase += f"; {nome_proprio(c['nome'])} ({escape(c['partido'])}), em {inteiro(c['municipios_acima_de_100'])}"
        frases.append(frase)
    texto = ". ".join(frases) + ". "
    alerta = next(
        (
            c
            for uf in mapa
            for c in C
            if c["uf"] == uf
            and c["maiores"]
            and c["maiores"][0]["pct_flavio"] < c["flavio_pct_uf"] - 5
        ),
        None,
    )
    if alerta:
        m = alerta["maiores"][0]
        texto += (
            f"O índice mais alto de {nome_proprio(alerta['nome'])} está em {nome_proprio(m['nome'])} "
            f"({num(m['indice'], 1)}), onde Flávio teve {pct(m['pct_flavio'])} contra {pct(alerta['flavio_pct_uf'])} "
            "no estado: índice alto pode ser presidenciável fraco ali, não só senador forte. "
        )
    topo = sorted(
        (c for c in C if c["maiores"] and c["uf"] not in mapa),
        key=lambda c: -c["maiores"][0]["indice"],
    )[:3]
    if topo:
        texto += (
            "Fora dos mapas, os índices mais altos do país são de "
            + lista(
                [
                    f"{nome_proprio(c['nome'])} ({escape(c['partido'])}-{c['uf']}) em "
                    f"{nome_proprio(c['maiores'][0]['nome'])}, {num(c['maiores'][0]['indice'], 1)}"
                    for c in topo
                ]
            )
            + f", todos em municípios com {inteiro(S['carregadores']['min_votantes'])} votantes ou mais."
        )
    return p(texto, "verificado")


def limites(S: dict) -> str:
    return p("<strong>Limites.</strong> " + " ".join(S["limites"]))


def capitulo(d: Dados) -> str:
    """Bloco do capítulo 7: h3, três figuras e os parágrafos que as leem."""
    h = f'<h3 id="senado-x-flavio">{TITULO}</h3>'
    S = d.get("senado_x_flavio.json")
    if not S:
        return h + bloco_pendente("senado_x_flavio.json")
    checar(d, "senado_x_flavio.json", CHAVES)
    h += fig("senado_pl_x_flavio_uf", d) + somas(S) + alinhados(S)
    h += achado_contrario(S)
    h += fig("senado_vao_candidatos", d) + melhores(S)
    h += fig("senado_carregadores_mapa", d) + carregadores(S)
    return h + limites(S)
