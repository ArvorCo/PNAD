"""Capítulo 13, bloco "Os cenários que o fiscal existe para impedir" e "O que já aconteceu".

Chamado por `pagina_cap_c.r_fiscais` depois dos rankings (municípios, listas do PL,
seções de nível alta e locais). Lê `analysis/apuracao_2026/fontes_fiscais.json` por
`fiscais_cenarios`. Regra do bloco: cenário é hipótese de risco, caso é passado
verificado com fonte, e nada é atribuído à eleição de 2026. A frase responsável
fecha o bloco. Sem o JSON, o bloco vira aviso e o resto do capítulo segue.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from html import escape

from . import fiscais_cenarios as FC
from .pagina_comum import caixa, inteiro, nota, p
from .pagina_texto import lista

H3 = ["Os cenários que o fiscal existe para impedir", "O que já aconteceu"]


def _link(f: dict) -> str:
    return (
        f'<a href="{escape(f["url"])}" rel="noopener">{escape(f["veiculo"])}, '
        f"{escape(FC.data_br(f['data']))}</a>"
    )


def _base_legal(J: dict, ids: list[str]) -> str:
    leis, fontes = FC.por_id(J["base_legal"]), FC.por_id(J["fontes"])
    itens = []
    for b in ids:
        x = leis[b]
        itens.append(
            f"{escape(x['norma'])}, {escape(x['dispositivo'])} ({escape(x['conteudo'])}; "
            f"{_link(fontes[x['fonte']])})"
        )
    return "; ".join(itens)


def _ficha_cenario(J: dict, c: dict, nomes: dict[str, str]) -> str:
    crit = c["criterios"]
    crit_txt = (
        lista([f"{escape(k)} ({escape(nomes.get(k, k))})" for k in crit])
        if crit
        else "nenhum"
    )
    casos = FC.casos_do_cenario(J, c["id"])
    casos_txt = (
        lista([f"{escape(k['titulo'])} ({k['ano']})" for k in casos])
        if casos
        else "nenhum caso com fonte na base da casa"
    )
    return (
        f'<article class="fs-cen" id="cenario-{escape(c["id"])}">'
        f"<h4>{escape(c['nome'])}</h4>"
        + p(f"<strong>O que é.</strong> {escape(c['o_que_e'])}", "hipotese")
        + f"<p><strong>Como aparece.</strong> {escape(c['como_aparece'])}</p>"
        f"<p><strong>Sinal nos dados ({escape(FC.ROT_SINAL[c['sinal']].lower())}).</strong> "
        f"{escape(c['sinal_texto'])} Critérios: {crit_txt}.</p>"
        f"<p><strong>O que o fiscal confere.</strong> {escape(c['confere'])}</p>"
        f"<p><strong>Base legal.</strong> {_base_legal(J, c['base_legal'])}.</p>"
        f"<p><strong>Casos documentados.</strong> {casos_txt}.</p>"
        + (
            "<p><strong>Referências.</strong> "
            + "; ".join(_link(FC.fonte(J, f)) for f in c["fontes"])
            + ".</p>"
            if c.get("fontes")
            else ""
        )
        + "</article>"
    )


def cenarios(F: dict, J: dict, fig: Callable[[str], str]) -> str:
    nomes = {c["id"]: c["nome"] for c in F["criterios"]}
    n = FC.contagem_sinal(J)
    total = len(J["cenarios"])
    h = "<h3>Os cenários que o fiscal existe para impedir</h3>"
    h += p(
        "Os critérios deste capítulo leem números: votos, horários, tipo de urna, comparecimento. A maior parte das "
        "manipulações clássicas do voto no dia da eleição não deixa número nenhum, e por isso a lei põe uma pessoa "
        "do partido dentro da seção. A tabela abaixo cruza cada cenário com o sinal que ele deixaria nos dados que "
        "medimos e com o que o fiscal confere ali. Cada linha é uma hipótese de risco, um tipo de coisa que já "
        "aconteceu no Brasil e que a fiscalização existe para impedir; nenhuma é descrição desta eleição.",
        "hipotese",
    )
    h += fig("fiscais_cenarios")
    sem = [c["nome"] for c in J["cenarios"] if c["sinal"] == "nenhum"]
    com = [c["nome"] for c in J["cenarios"] if c["sinal"] == "deixa"]
    h += p(
        f"Dos {inteiro(total)} cenários, {inteiro(n['deixa'])} deixam sinal no boletim "
        f"({lista([escape(x) for x in com])}), {inteiro(n['parcial'])} deixam sinal fraco ou indireto e "
        f"{inteiro(n['nenhum'])} não deixam sinal nenhum ({lista([escape(x) for x in sem])}). Os que deixam sinal "
        "são justamente os que têm explicação de procedimento: urna trocada, fila no fim do dia, seção especial. Os "
        "que não deixam são os que dependem de gente: dinheiro, ameaça, propaganda na porta. Uma lista de seções "
        "atípicas ajuda a escolher onde ir; o que acontece fora do boletim só o fiscal vê.",
        "inferencia",
    )
    por_fam: dict[str, list[dict]] = {}
    for c in J["cenarios"]:
        por_fam.setdefault(c["familia"], []).append(c)
    for fam in FC.FAMILIAS:
        itens = "".join(_ficha_cenario(J, c, nomes) for c in por_fam.get(fam, []))
        if itens:
            h += (
                f'<details class="fs-cens"><summary>{escape(FC.ROT_FAMILIA[fam])}: '
                f"{inteiro(len(por_fam[fam]))} cenários, um a um</summary>{itens}</details>"
            )
    h += caixa(
        "io",
        "Levar o eleitor e impedir o eleitor são coisas opostas",
        "<p>Transporte irregular é levar eleitor a votar com o voto como condição: veículo pago por candidato, "
        "partido ou cabo eleitoral, quase sempre com comida. Abstenção induzida é o contrário: impedir o eleitor "
        "de chegar, com ônibus que não sai, estrada bloqueada ou ameaça. Os dois casos estão na tabela em linhas "
        "separadas, com base legal diferente, e o fiscal os registra de forma diferente: no primeiro, placa, hora e "
        "quem paga; no segundo, lugar do bloqueio e hora, comunicados ao juiz eleitoral no mesmo dia.</p>",
    )
    return h


def casos(J: dict, fig: Callable[[str], str]) -> str:
    cs = FC.casos_ordenados(J)
    cens = FC.por_id(J["cenarios"])
    h = "<h3>O que já aconteceu</h3>"
    h += fig("fiscais_casos")
    inst = Counter(c["instancia"] for c in cs)
    fam = Counter(cens[c["cenario"]]["familia"] for c in cs)
    h += p(
        f"{inteiro(len(cs))} casos brasileiros, de {cs[0]['ano']} a {cs[-1]['ano']}, cada um com data, instância, "
        "resultado e uma fonte lida pela casa: decisão de tribunal eleitoral, inquérito ou operação policial, "
        "relatório parlamentar ou reportagem datada. Por onde acontecem: "
        + lista(
            [
                f"{escape(FC.ROT_FAMILIA[f].lower())}, {inteiro(fam[f])}"
                for f in FC.FAMILIAS
                if fam.get(f)
            ]
        )
        + ". As instâncias mais frequentes: "
        + lista([f"{escape(k)} ({inteiro(v)})" for k, v in inst.most_common(4)])
        + ".",
        "verificado",
    )
    itens = "".join(
        f"<li><strong>{escape(FC.data_br(c['data']))}, {escape(c['titulo'])}</strong> ({escape(c['local'])}; "
        f"{escape(c['instancia'])}). {escape(c['resumo'])} Resultado: {escape(c['resultado'])} "
        + " ".join(_link(FC.fonte(J, f)) for f in c["fontes"])
        + "</li>"
        for c in cs
    )
    h += f'<ul class="fs-casos-lista">{itens}</ul>'
    falta = J.get("procurados_sem_fonte") or []
    if falta:
        h += nota(
            "contrario",
            "Procuramos e não encontramos fonte primária que sustentasse: "
            + lista(
                [
                    f"{escape(x['tema'])} ({escape(x.get('nota') or x.get('o_que_procurou', ''))})"
                    for x in falta
                ]
            )
            + ". Ficam fora da página até que um documento apareça.",
        )
    return h


def fontes(J: dict) -> str:
    lis = "".join(
        f"<li>{_link(f)}: {escape(f['titulo'])}. {escape(f['como_conferido'])}"
        + (
            f'<br><span class="hash">{escape(f["arquivo"])} · SHA-256 {escape(f["sha256"])}</span>'
            if f.get("sha256")
            else ""
        )
        + "</li>"
        for f in sorted(J["fontes"], key=lambda f: (f["data"], f["id"]))
    )
    return (
        f"<details><summary>As {inteiro(len(J['fontes']))} fontes dos cenários e dos casos</summary>"
        f'<ul class="fontes">{lis}</ul><p>Arquivo: <code>analysis/apuracao_2026/fontes_fiscais.json</code>, '
        "com URL, veículo ou tribunal, data e como cada fonte foi conferida; o texto bruto das páginas lidas, "
        "com SHA-256, fica em <code>data/originals/apuracao_2026/fiscais/</code>, fora do repositório.</p></details>"
    )


def responsavel(F: dict) -> str:
    rot = F.get("rotulos") or {}
    return nota(
        "juizo",
        "Nenhum cenário desta seção é atribuído à eleição de 2026, e nenhum caso listado é desta eleição. Os casos "
        "mostram que esses mecanismos existiram e que a Justiça Eleitoral os puniu quando houve prova; os cenários "
        "dizem o que o fiscal procura. "
        + escape(
            " ".join(rot.get(k, "") for k in ("atipico", "prioridade", "resolve"))
        ),
        "Frase responsável.",
    )


def bloco(F: dict, fig: Callable[[str], str], d_aviso) -> str:
    J = FC.carregar()
    if J is None:
        d_aviso("fontes_fiscais.json ausente: capítulo 13 sem os cenários de risco")
        return ""
    erros = FC.validar(J, {c["id"] for c in F["criterios"]})
    if erros:
        raise ValueError("fontes_fiscais.json: " + "; ".join(erros[:5]))
    return cenarios(F, J, fig) + casos(J, fig) + fontes(J) + responsavel(F)


__all__ = ["H3", "bloco", "casos", "cenarios", "fontes", "responsavel"]
