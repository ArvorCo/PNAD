"""Subparte "Onde Flávio teve menos votos no 2º turno do que no 1º" do capítulo turnos.

Interface: ``bloco(d, C1) -> str``, com ``d`` o leitor ``Dados`` do dossiê e ``C1`` o
``comparacao_1t.json`` já lido. Todo número sai de ``turnos_perdas`` (que lê
``comparacao_1t.json`` e ``governadores.json``) e do manifesto do dataset; nada é
digitado aqui. Ordem: régua, totais (Verificado), espelho de Lula, figura por UF,
contexto do 2º turno de governador, as quatro situações e a decomposição da perda
(Inferência), as 30 maiores perdas, as duas listas completas e os CSVs.

Rótulo: votos absolutos, não fatia dos válidos; menos votos não identifica eleitor
nem motivo. Sem travessão; nunca "eleitores dele".
"""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any

from apuracao_2026.pagina_comum import (
    NOME_UF,
    caixa,
    cartao,
    inteiro,
    milhoes,
    nota,
    num,
    p,
    sinal_int,
    tabela,
)
from apuracao_2026.pagina_fig_base import FLAVIO, LULA
from apuracao_2026.pagina_texto_terceira_via import NA_UF

from . import pagina_fig_turnos_perdas as F
from . import turnos_perdas as TP
from .dataset import DICIONARIO, MANIFESTO, ler_manifesto
from .pagina_comum import ROOT
from .pagina_fig_turnos_util import municipio

TITULO = "Onde Flávio teve menos votos no 2º turno do que no 1º"
GOV = "governadores.json"


def _e(xs: list[str]) -> str:
    if not xs:
        return ""
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " e " + xs[-1]


def _na(uf: str, inicio: bool = False) -> str:
    """'no Amapá', 'em Roraima', 'na Bahia'; maiúscula no começo da frase."""
    s = f"{NA_UF.get(uf, 'em')} {NOME_UF.get(uf, uf)}"
    return s[:1].upper() + s[1:] if inicio else s


def _pct(parte: float, total: float, casas: int = 1) -> str:
    return f"{num(100 * parte / total, casas)}%" if total else "s/d"


def _saldo(v: int, coisa: str) -> str:
    """'274.667 eleitores a menos' ou 'a mais', pelo sinal."""
    return f"{inteiro(abs(v))} {coisa} {'a menos' if v < 0 else 'a mais'}"


def _categoria(R: dict[str, Any], chave: str) -> dict[str, Any]:
    return next(c for c in R["categorias"] if c["chave"] == chave)


# ------------------------------------------------------------------ textos


def regua() -> str:
    return caixa(
        "io",
        "Régua.",
        f" {TP.ROTULO[:1].upper() + TP.ROTULO[1:]}. A conta compara o número de votos de "
        "cada finalista no mesmo município nos dois turnos; a fatia dos válidos, que tira "
        "os terceiros da comparação, está nas seções anteriores do capítulo.",
    )


def cartoes(RF: dict[str, Any], RL: dict[str, Any]) -> str:
    return (
        '<div class="finding-grid">'
        + cartao(
            f"{inteiro(RF['n'])} de {inteiro(RF['n_universo'])}",
            "municípios em que Flávio teve menos votos no 2º turno",
            FLAVIO,
        )
        + cartao(sinal_int(-RF["perda"]), "votos de Flávio nesses municípios", FLAVIO)
        + cartao(
            sinal_int(RF["delta_adversario"]), "votos de Lula nesses municípios", LULA
        )
        + cartao(
            f"{inteiro(RL['n'])} ({sinal_int(-RL['perda'])})",
            "municípios em que Lula teve menos votos (votos somados)",
            LULA,
        )
        + "</div>"
    )


def abertura(RF: dict[str, Any]) -> str:
    n = RF["n"]
    reg = RF["por_regiao"]
    nne = reg.get("Norte", 0) + reg.get("Nordeste", 0)
    adv = [
        f"ganhou votos em {inteiro(RF['n_adversario_ganhou'])}",
        f"perdeu em {inteiro(RF['n_adversario_perdeu'])}",
    ]
    if RF["n_adversario_igual"]:
        adv.append(f"ficou com o mesmo número em {inteiro(RF['n_adversario_igual'])}")
    return p(
        f"Em {inteiro(n)} dos {inteiro(RF['n_universo'])} municípios, Flávio teve menos votos "
        f"no 2º turno do que no 1º. Somadas, as perdas dão {inteiro(RF['perda'])} votos. "
        f"Esses municípios têm {milhoes(RF['aptos'])} de eleitores, "
        f"{_pct(RF['aptos'], RF['aptos_universo'])} do país. Neles, Lula teve "
        f"{_saldo(RF['delta_adversario'], 'votos')}: {_e(adv)}. O comparecimento caiu em "
        f"{inteiro(RF['n_comparecimento_caiu'])} dos {inteiro(n)}, com "
        f"{_saldo(RF['delta_comparecimento'], 'eleitores')}, somados. Norte e Nordeste "
        f"reúnem {inteiro(nne)} deles.",
        "verificado",
    )


def espelho(RL: dict[str, Any]) -> str:
    n = RL["n"]
    caiu = RL["n_comparecimento_caiu"]
    onde = (
        f"Em todos os {inteiro(n)}"
        if caiu == n
        else f"Em {inteiro(caiu)} dos {inteiro(n)}"
    )
    maior = RL["maior"]
    return p(
        f"O espelho, pela mesma régua: Lula teve menos votos no 2º turno em {inteiro(n)} "
        f"municípios, com {_saldo(-RL['perda'], 'votos')} somados, em "
        f"{milhoes(RL['aptos'])} de eleitores. {onde}, o comparecimento caiu "
        f"({_saldo(RL['delta_comparecimento'], 'eleitores')}); Flávio também perdeu votos "
        f"em {inteiro(RL['n_adversario_perdeu'])} deles e ganhou em "
        f"{inteiro(RL['n_adversario_ganhou'])}. A maior perda de Lula foi em "
        f"{municipio(maior['nome'], maior['uf'])}, {sinal_int(-maior['perda'])} votos.",
        "verificado",
    )


def por_uf(RF: dict[str, Any], RL: dict[str, Any]) -> str:
    pf = sorted((u for u in RF["por_uf"] if u["n"]), key=lambda u: (-u["n"], u["uf"]))
    top = [f"{u['nome']} ({inteiro(u['n'])} de {inteiro(u['n_uf'])})" for u in pf[:5]]
    txt = f"Por UF, as maiores contagens de Flávio são {_e(top)}."
    todos = [u for u in pf if u["n"] == u["n_uf"]]
    if todos:
        lista = _e([_na(u["uf"], i == 0) for i, u in enumerate(todos)])
        conta = _e([f"{inteiro(u['n'])} de {inteiro(u['n_uf'])}" for u in todos])
        txt += f" {lista}, Flávio teve menos votos em todos os municípios ({conta})."
    nenhum = sorted((u for u in RF["por_uf"] if not u["n"]), key=lambda u: u["nome"])
    if nenhum:
        txt += (
            f" {_e([_na(u['uf'], i == 0) for i, u in enumerate(nenhum)])}, em nenhum."
        )
    pl = sorted((u for u in RL["por_uf"] if u["n"]), key=lambda u: (-u["n"], u["uf"]))
    if pl:
        txt += (
            " Lula teve menos votos sobretudo "
            + _e([f"{_na(u['uf'])} ({inteiro(u['n'])})" for u in pl[:5]])
            + f", entre {inteiro(len(pl))} UFs com ao menos um município."
        )
    return p(txt, "verificado")


def governador(C1: dict[str, Any], RF: dict[str, Any], G: dict[str, Any] | None) -> str:
    gov = TP.ufs_governador(G)
    if not gov:
        return ""
    ctx = TP.contexto_governador(C1, gov)
    com, sem = ctx["com"], ctx["sem"]
    n_outras = len(RF["por_uf"]) - len(gov)
    txt = (
        f"Houve 2º turno de governador em {len(gov)} UFs: "
        f"{_e([NOME_UF.get(str(u), str(u)) for u in ctx['ufs']])}. Nelas, o comparecimento caiu contra "
        f"o 1º turno em {inteiro(com['comparecimento_caiu'])} de {inteiro(com['n'])} municípios "
        f"({_pct(com['comparecimento_caiu'], com['n'])}); nas outras {n_outras} UFs, em "
        f"{inteiro(sem['comparecimento_caiu'])} de {inteiro(sem['n'])} "
        f"({_pct(sem['comparecimento_caiu'], sem['n'])})."
    )
    por = sorted(ctx["por_uf"], key=lambda x: (-(x["pct"] or 0), x["uf"]))
    alta = [x for x in por if (x["pct"] or 0) >= 50]
    baixa = [x for x in por if 0 < (x["pct"] or 0) < 50]
    zero = [x for x in por if not x["comparecimento_caiu"]]
    partes = []
    if alta:
        partes.append(
            "a queda se concentra "
            + _e(
                [
                    f"{_na(x['uf'])} ({inteiro(x['comparecimento_caiu'])} de {inteiro(x['n'])})"
                    for x in alta
                ]
            )
        )
    partes += [
        f"{_na(x['uf'])}, {inteiro(x['comparecimento_caiu'])} de {inteiro(x['n'])}"
        for x in baixa
    ]
    if zero:
        partes.append(f"{_e([_na(x['uf']) for x in zero])}, em nenhum município")
    if partes:
        txt += f" Entre as {len(gov)}, " + "; ".join(partes) + "."
    n_gov = RF["n_governador_2t"]
    txt += (
        f" Dos {inteiro(RF['n'])} municípios em que Flávio teve menos votos, {inteiro(n_gov)} "
        f"ficam nessas {len(gov)} UFs e {inteiro(RF['n'] - n_gov)} nas outras."
    )
    regiao_uf = {m["uf"]: m["regiao"] for m in TP.tabela(C1["municipios"])}
    caiu_uf = sorted(
        (u for u in C1["ufs"] if (u["delta_comparecimento_pp"] or 0) < 0),
        key=lambda u: u["nome_uf"],
    )
    por_reg: dict[str, int] = {}
    for u in caiu_uf:
        por_reg[regiao_uf[u["uf"]]] = por_reg.get(regiao_uf[u["uf"]], 0) + 1
    h = p(txt, "verificado")
    if com["comparecimento_caiu"] * sem["n"] > sem["comparecimento_caiu"] * com["n"]:
        inf = (
            "A hipótese de que a falta de disputa estadual reduz o comparecimento não "
            "aparece nesta conta: a queda foi mais frequente nas UFs que tiveram 2º turno "
            "de governador."
        )
    else:
        inf = (
            "A queda foi menos frequente nas UFs que tiveram 2º turno de governador, o que "
            "é compatível com a hipótese de que a falta de disputa estadual reduz o "
            "comparecimento, mas não a identifica."
        )
    if caiu_uf:
        regs = _e(
            [
                f"{inteiro(k)} do {r}"
                for r, k in sorted(por_reg.items(), key=lambda kv: (-kv[1], kv[0]))
            ]
        )
        inf += (
            " No agregado da UF, o comparecimento caiu "
            + _e([_na(u["uf"]) for u in caiu_uf])
            + f" ({regs}): a queda acompanha a geografia."
        )
    inf += " A comparação não controla região nem tamanho do município e não identifica causa."
    return h + p(inf, "inferencia")


SITUACOES = {
    "caiu_sem_ganho": "O comparecimento caiu e o adversário não ganhou votos",
    "caiu_com_ganho": "O comparecimento caiu e o adversário ganhou votos",
    "manteve_com_ganho": "O comparecimento ficou igual ou subiu e o adversário ganhou votos",
    "manteve_sem_ganho": "O comparecimento ficou igual ou subiu e o adversário não ganhou votos",
}


def tabela_situacoes(RF: dict[str, Any], RL: dict[str, Any]) -> str:
    linhas = []
    for chave, rot in SITUACOES.items():
        f, lu = _categoria(RF, chave), _categoria(RL, chave)
        linhas.append(
            [
                rot,
                inteiro(f["n"]),
                sinal_int(-f["perda"]),
                inteiro(lu["n"]),
                sinal_int(-lu["perda"]),
            ]
        )
    linhas.append(
        [
            "Total",
            inteiro(RF["n"]),
            sinal_int(-RF["perda"]),
            inteiro(RL["n"]),
            sinal_int(-RL["perda"]),
        ]
    )
    return tabela(
        [
            "Situação no município",
            "Flávio teve menos votos: municípios",
            "Votos de Flávio",
            "Lula teve menos votos: municípios",
            "Votos de Lula",
        ],
        linhas,
        "As quatro situações possíveis entre comparecimento e votos do adversário (Lula na lista "
        "de Flávio, Flávio na lista de Lula). Votos absolutos, somados. Fonte: comparacao_1t.json.",
    )


def tabela_reguas(RF: dict[str, Any], RL: dict[str, Any]) -> str:
    linhas = []
    for R in (RF, RL):
        nome = TP.NOME[R["quem"]]
        for rot, cabe, fora, n in (
            ("teto", R["teto"], R["alem_teto"], R["n_alem_teto"]),
            (
                "proporcional",
                R["proporcional"],
                R["alem_proporcional"],
                R["n_alem_proporcional"],
            ),
        ):
            linhas.append(
                [
                    f"{nome}, régua {rot}",
                    inteiro(R["perda"]),
                    inteiro(cabe),
                    inteiro(fora),
                    _pct(cabe, R["perda"]),
                    inteiro(n),
                ]
            )
    return tabela(
        [
            "Lista e régua",
            "Votos perdidos",
            "Cabem na queda do comparecimento",
            "Ficam fora dela",
            "Parte que cabe",
            "Municípios com sobra",
        ],
        linhas,
        "Teto: todo eleitor que deixou de votar seria do candidato. Proporcional: quem deixou "
        "de votar votaria como o município votou no 1º turno. Contas sob hipótese, não "
        "identificação de eleitor. Fonte: comparacao_1t.json.",
    )


def decomposicao(RF: dict[str, Any], RL: dict[str, Any]) -> str:
    manteve = [c for c in RF["categorias"] if not c["comparecimento_caiu"]]
    n_man = sum(c["n"] for c in manteve)
    perda_man = sum(c["perda"] for c in manteve)
    adv_man = sum(c["delta_adversario"] for c in manteve)
    cobre_teto = RF["n_alem_teto_adversario_cobre"]
    cobre_txt = (
        f"em todos os {inteiro(RF['n_alem_teto'])}"
        if cobre_teto == RF["n_alem_teto"]
        else f"em {inteiro(cobre_teto)} desses {inteiro(RF['n_alem_teto'])}"
    )
    txt = (
        "Quanto da perda de Flávio cabe em menos gente votando? Duas réguas, as duas com "
        "hipótese declarada. Pelo teto, que trata todo eleitor que deixou de votar como "
        f"eleitor de Flávio, cabem {inteiro(RF['teto'])} dos {inteiro(RF['perda'])} votos; "
        f"ao menos {inteiro(RF['alem_teto'])}, em {inteiro(RF['n_alem_teto'])} municípios, "
        f"ficam fora, e {cobre_txt} Lula ganhou ao menos essa sobra. Pela régua proporcional, "
        "que supõe que quem deixou de votar votava como o município no 1º turno, a queda do "
        f"comparecimento responde por {inteiro(RF['proporcional'])} votos "
        f"({_pct(RF['proporcional'], RF['perda'])}) e {inteiro(RF['alem_proporcional'])} "
        f"ficam fora dela, em {inteiro(RF['n_alem_proporcional'])} municípios; em "
        f"{inteiro(RF['n_alem_proporcional_adversario_cobre'])} desses, o ganho de Lula cobre "
        "a sobra."
    )
    if n_man:
        txt += (
            f" Nos {inteiro(n_man)} municípios em que o comparecimento não caiu, a perda "
            f"inteira ({inteiro(perda_man)} votos) fica fora, e ali Lula teve "
            f"{_saldo(adv_man, 'votos')}."
        )
    txt += (
        f" Para Lula, a queda do comparecimento cobre {_pct(RL['teto'], RL['perda'])} da "
        f"perda pelo teto e {_pct(RL['proporcional'], RL['perda'])} pela régua proporcional."
    )
    return (
        p(
            "As quatro situações dos municípios, contadas linha a linha da lista:",
            "verificado",
        )
        + tabela_situacoes(RF, RL)
        + p(txt, "inferencia")
        + tabela_reguas(RF, RL)
        + nota(
            "inferencia",
            "A sobra é compatível com troca de lado, mas não a identifica. O mesmo saldo "
            "aparece se eleitores de Flávio no 1º turno deixaram de votar e outros, que "
            "faltaram no 1º turno, vieram votar em Lula; ou se votos de Flávio foram para "
            "branco e nulo enquanto eleitores de terceiros foram para Lula. O município "
            "mostra saldos, não pessoas, e o voto é secreto.",
            "Como ler.",
        )
    )


def bloco_csv(RF: dict[str, Any], RL: dict[str, Any], m: dict | None = None) -> str:
    """Links dos dois CSVs; some quando o manifesto não os traz ou não bate com o JSON."""
    m = m or ler_manifesto()
    entradas = {e["candidato"]: e for e in (m or {}).get("listas_municipais") or []}
    n = {"flavio": RF["n"], "lula": RL["n"]}
    if set(entradas) != set(n) or any(entradas[q]["n_linhas"] != n[q] for q in n):
        return ""
    links = []
    for q in TP.CANDIDATOS:
        e = entradas[q]
        kb = num(e["bytes"] / 1000, 0)
        links.append(
            f'<a href="{escape(e["arquivo"].removeprefix("docs/"))}" download>'
            f"<code>{escape(Path(e['arquivo']).name)}</code></a> ({inteiro(e['n_linhas'])} "
            f"municípios em que {TP.NOME[q]} teve menos votos, {kb} KB)"
        )
    docs = ROOT / "docs"
    return (
        f'<p class="dataset"><b>Baixe as duas listas.</b> {_e(links)}. Mesmas colunas nos dois '
        "arquivos, com comparecimento em eleitores, válidos, terceiros e as duas réguas da "
        f'decomposição; colunas no <a href="{DICIONARIO.relative_to(docs)}">dicionário</a> '
        f'e SHA-256 no <a href="{MANIFESTO.relative_to(docs)}">manifesto</a>. '
        f"{TP.ROTULO[:1].upper() + TP.ROTULO[1:]}.</p>"
    )


def bloco(d, C1: dict[str, Any], antes_das_listas: str = "") -> str:
    """Subparte inteira; ``antes_das_listas`` entra entre a decomposição e as listas."""
    G = d.get(GOV)
    gov = TP.ufs_governador(G)
    RF = TP.resumo(C1, "flavio", gov)
    RL = TP.resumo(C1, "lula", gov)
    h = F.ESTILO + f'<h3 id="tu-menos-votos">{TITULO}</h3>'
    h += regua() + cartoes(RF, RL) + abertura(RF) + espelho(RL)
    h += F.fig_perdas_uf(RF, RL, sorted(gov))
    h += por_uf(RF, RL)
    h += governador(C1, RF, G)
    h += decomposicao(RF, RL)
    h += antes_das_listas
    h += F.lista_completa(TP.municipios(C1, "flavio", gov), "flavio")
    h += F.lista_completa(TP.municipios(C1, "lula", gov), "lula")
    h += bloco_csv(RF, RL)
    return h
