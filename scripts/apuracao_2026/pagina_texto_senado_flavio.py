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
    limites,
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
    al_lula = S["blocos"]["alinhados_lula"]
    eleitos = {e["sqcand"] for u in S["ufs"] for e in u["eleitos"]}
    nomes = [
        f"{nome_proprio(a['nome'])} ({a['uf']}{', eleito' if a['sqcand'] in eleitos else ''})"
        for a in al_lula
    ]
    return p(
        f"Na base de votos do Senado, os nomes do PL somam {pct(pl['pct'])}, {num(abs(pl['div_pp']), 2)} pontos "
        f"{'abaixo' if pl['div_pp'] < 0 else 'acima'} de Flávio ({pct(fl['pct'])} dos válidos do eleitor residente), "
        f"embora tenham {milhoes(pl['votos'])} de votos, {num(pl['votos_por_voto_flavio'], 2)} para cada voto dele. O "
        f"bloco aliado de direita e centro-direita soma {pct(al['pct'])}, {num(abs(al['div_pp']), 2)} pontos "
        f"{'acima' if al['div_pp'] > 0 else 'abaixo'} de Flávio, e passa dele em {al['ufs_acima_de_flavio']} UFs: mais em "
        + lista([_uf_val(u, "aliados") for u in acima])
        + "; menos em "
        + lista([_uf_val(u, "aliados") for u in abaixo])
        + f". Ficam fora do bloco {len(al_lula)} candidaturas do lado de Lula, pela regra declarada no script: "
        + lista(nomes)
        + ".",
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
        f"O PL fica abaixo de Flávio em {n['ufs_abaixo_de_flavio']} das {len(com)} UFs onde lançou nome, e é o normal "
        f"do Senado: o eleitor dá dois votos, e em {n['ufs_com_um_nome']} UFs o PL lançou um nome só, que não passa de "
        "metade da base. "
    )
    if acima:
        texto += (
            "Fica acima só em "
            + lista([f"{u['uf']} ({sinal(u['pl']['div_pp'], 1)})" for u in acima])
            + ". "
        )
    if razoes:
        texto += (
            f"Onde lançou dois nomes ({len(dois)} UFs), a soma vai de {num(min(razoes), 2)} a "
            f"{num(max(razoes), 2)} votos por voto de Flávio. "
        )
    if sem:
        texto += f"Não houve nome do PL em {lista(sem)}."
    return p(texto.strip(), "contrario")


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
            + lista(
                [
                    f"só {nome(u, m)} passa Flávio, {pct(m['pct'])} contra {pct(u['flavio']['pct'])}"
                    f"{', eleito' if m['eleito'] else ', sem se eleger'}"
                    for u, m in base
                ]
            )
            + ". "
        )
    else:
        frase_base = "Na base de votos, nenhuma candidatura do bloco passa Flávio. "
    texto = p(
        frase_base
        + f"Em eleitores alcançados, a melhor candidatura do bloco passa Flávio em {len(vot)} UFs, {len(nordeste)} no "
        "Nordeste: "
        + lista(
            [
                f"{u['uf']} {nome_proprio(m['nome'])} {sinal(m['vao_votantes_pp'], 1)}"
                for u, m in vot
            ]
        )
        + f". O mais fundo do outro lado é {nome(fundo_u, fundo)}, {sinal(fundo['vao_votantes_pp'], 1)}"
        f"{', eleito mesmo assim' if fundo['eleito'] else ''}.",
        "verificado",
    )
    if vot:
        u, m = vot[0]
        texto += p(
            "Essa distância é, aproximadamente, um piso de eleitores que escolheram o senador e não Flávio "
            f"({em_uf(u['uf'])}, {num(m['vao_votantes_pp'], 1)} pontos dos votantes): teto endereçável para o 2º turno, "
            "não transferência.",
            "inferencia",
        )
    return texto


def carregadores(S: dict) -> str:
    C = S["carregadores"]["candidatos"]
    mapa = S["mapa"]["ufs"]
    texto = ""
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
            f"Índice alto pode ser Flávio fraco, não senador forte: o maior de {nome_proprio(alerta['nome'])} está em "
            f"{nome_proprio(m['nome'])} ({num(m['indice'], 1)}), onde Flávio teve {pct(m['pct_flavio'])} contra "
            f"{pct(alerta['flavio_pct_uf'])} no estado."
        )
    return p(texto, "verificado") if texto else ""


def capitulo(d: Dados) -> str:
    """Bloco do capítulo 7: h3, três figuras e os parágrafos que as leem."""
    h = f'<h3 id="senado-x-flavio">{TITULO}</h3>'
    S = d.get("senado_x_flavio.json")
    if not S:
        return h + bloco_pendente("senado_x_flavio.json")
    checar(d, "senado_x_flavio.json", CHAVES)
    h += fig("senado_pl_x_flavio_uf", d) + somas(S) + achado_contrario(S)
    h += fig("senado_vao_candidatos", d) + melhores(S)
    h += fig("senado_carregadores_mapa", d) + carregadores(S)
    return h + limites(S["limites"])
