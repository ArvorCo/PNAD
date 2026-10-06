"""Capítulo 13, bloco "Pesquisa contra urna: duas réguas para o mesmo estoque".

Chamado por `pagina_texto_terceira_via.bloco`. Todo número sai de
`analysis/apuracao_2026/dados/terceira_via.json → reguas` e `→ conversao_2022`.
Figura antes do parágrafo que a lê.
"""

from __future__ import annotations

from collections.abc import Callable
from html import escape

from .pagina_comum import NOME_UF, inteiro, nota, num, p, tabela
from .pagina_fig_base import nome_bonito

CLASSES = ("venceu_folga", "venceu_apertado", "perdeu_apertado", "perdeu_folga")
SITUACAO = {
    "robusto": "robusto",
    "so_pesquisa": "só pesquisa",
    "so_urna": "só urna",
    "fora": "fora das duas listas",
}
MOTIVO = {"composicao": "composição por nome", "classe": "classe de margem"}


def pv(x: float | None, casas: int = 2) -> str:
    if x is None:
        return "s/d"
    return ("+" if x > 0 else "−" if x < 0 else "") + num(abs(x), casas)


def votos(x: float | None, com_sinal: bool = True) -> str:
    """Votos em prosa: milhões com duas casas e "de votos", milhares arredondados e "mil votos"."""
    if x is None:
        return "s/d"
    a = abs(x)
    s = ("+" if x > 0 else "−" if x < 0 else "") if com_sinal else ""
    if a >= 1_000_000:
        return (
            f"{s}{num(a / 1e6, 2)} {'milhão' if a < 2_000_000 else 'milhões'} de votos"
        )
    if a >= 10_000:
        return f"{s}{num(a / 1000, 0)} mil votos"
    return f"{s}{inteiro(a)} votos"


def _lista(itens: list[str]) -> str:
    itens = [i for i in itens if i]
    if len(itens) <= 1:
        return "".join(itens)
    return ", ".join(itens[:-1]) + " e " + itens[-1]


def _cidades(xs: list[dict], n: int = 3) -> str:
    return _lista([f"{nome_bonito(x['nome'])} ({x['uf']})" for x in xs[:n]])


def _nomes(xs: list[dict], n: int = 3) -> str:
    return _lista([nome_bonito(x["nome"]) for x in xs[:n]])


def _intro() -> str:
    return "<h3>Pesquisa contra urna: duas réguas para o mesmo estoque</h3>" + p(
        "A matriz das pesquisas de setembro sabe o nome do eleitor de terceira via e não sabe onde ele mora. A urna de "
        "2022 sabe o lugar, município a município, não sabe o nome e é de outra eleição. Quando as duas batem, a aposta "
        "é segura; quando divergem, a distância é o tamanho dela."
    )


def _coeficientes(R: dict, conv: dict) -> str:
    gc = R["modelos"]["classe"]["grupos"]
    un = R["modelos"]["unico"]["grupos"]["todos"]
    sfe = R["modelos"]["sem_efeito_fixo"]

    def ic(g: dict) -> str:
        a, b = g["saldo_ic95"]
        return f"{pv(a)} a {pv(b)}"

    h = p(
        "Na urna de 2022, dentro da mesma UF, cada voto de terceira via do 1º turno somou ao saldo de Bolsonaro "
        f"{pv(gc['venceu_folga']['saldo'])} onde Flávio venceu com folga em 2026 ({ic(gc['venceu_folga'])}), "
        f"{pv(gc['venceu_apertado']['saldo'])} onde venceu apertado, {pv(gc['perdeu_apertado']['saldo'])} onde perdeu "
        f"apertado e {pv(gc['perdeu_folga']['saldo'])} onde perdeu com folga ({ic(gc['perdeu_folga'])}). No país, "
        f"{pv(un['saldo'])} ({ic(un)}): a terceira via de 2022 dividiu-se quase ao meio, {num(un['bolsonaro'], 2)} para "
        f"Bolsonaro e {num(un['lula'], 2)} para Lula. A razão simples dá mais ({pv(conv['brasil']['saldo'])} no país) porque "
        "credita à terceira via a base que se mobilizou: sem efeito fixo de UF, sobra uma parcela de "
        f"{num(100 * sfe['constante'], 2)} pontos a favor de Bolsonaro que não depende dela.",
        "inferencia",
    )
    fora_neg = [
        r
        for r, g in R["modelos"]["regiao"]["grupos"].items()
        if g["fora"] is not None and g["fora"] < 0
    ]
    aviso_regiao = ""
    if fora_neg:
        gn = R["modelos"]["regiao"]["grupos"]
        detalhe = _lista(
            [
                f"{r} (Bolsonaro {num(gn[r]['bolsonaro'], 2)}, Lula {num(gn[r]['lula'], 2)})"
                for r in fora_neg
            ]
        )
        aviso_regiao = f" Em {detalhe} as duas inclinações somam mais de um voto por voto; por isso a régua usa a classe de margem."
    h += nota(
        "hipotese",
        "A régua da urna é inferência de agregado para agregado, não o voto do eleitor de Tebet ou de Ciro. E a terceira "
        "via de 2022 (Tebet e Ciro, centro e esquerda) não é a de 2026, que tem Renan Santos e Zema, de direita."
        + aviso_regiao,
        "Limite ecológico.",
    )
    return h


def _totais(R: dict, diferenca: int, direita_pct: float) -> str:
    T = R["totais"]
    br, cl, rg = T["brasil"], T["classes"], T["regioes"]
    a, _b = br["urna_ic95"]
    pior = min(a, br["urna_regiao"], br["urna"], br["nexus"], br["datafolha"])
    fecho = (
        f"Com as bases do 1º turno fixas, nenhuma régua, nem o limite inferior da urna, desfaz os "
        f"{votos(diferenca, False)} do 1º turno."
        if pior > -diferenca
        else f"No pior caso ({votos(pior)}), a terceira via desfaria os {votos(diferenca, False)} do 1º turno."
    )
    return p(
        f"{fecho} Onde Flávio venceu com folga as réguas quase coincidem ({pv(cl['venceu_folga']['pv_nexus'])} por voto "
        f"pela Nexus, {pv(cl['venceu_folga']['pv_urna'])} pela urna); onde perdeu, a pesquisa promete "
        f"{pv(cl['perdeu_apertado']['pv_nexus'])} e {pv(cl['perdeu_folga']['pv_nexus'])} e a urna entregou "
        f"{pv(cl['perdeu_apertado']['pv_urna'])} e {pv(cl['perdeu_folga']['pv_urna'])}. A pesquisa ignora o lugar; a urna ignora o "
        f"nome: em 2026, Renan e Zema somam {num(direita_pct, 2)}% da terceira via. No Centro-Oeste, onde o estoque é "
        f"de Caiado, a urna rende mais ({pv(rg['Centro-Oeste']['pv_urna'])} contra {pv(rg['Centro-Oeste']['pv_nexus'])}).",
        "inferencia",
    )


def _rankings(R: dict) -> str:
    rk = R["rankings"]
    mot = rk["motivos_divergencia"]
    so_p = [x for x in rk["divergentes"] if x["situacao"] == "so_pesquisa"]
    so_u = [x for x in rk["divergentes"] if x["situacao"] == "so_urna"]
    extremo = max(so_p, key=lambda x: x["teto"] - x["piso"], default=None)
    texto = (
        f"Dos 100 primeiros municípios pela pesquisa, {rk['robustos']} também estão entre os 100 primeiros pela urna de "
        f"2022: são os robustos, com {votos(rk['robustos_estoque'], False)} de terceira via. Só a pesquisa põe "
        f"{rk['so_pesquisa']} na lista ({_cidades(so_p)} à frente) e só a urna, {rk['so_urna']} ({_cidades(so_u)}); "
        f"a classe de margem explica {mot.get('so_pesquisa:classe', 0) + mot.get('so_urna:classe', 0)} dessas "
        "divergências e a composição por nome, o resto."
    )
    if extremo:
        sai = extremo["posicao"]["combinacao"] > len(rk["top"]["combinacao"])
        texto += (
            f" A maior distância é {nome_bonito(extremo['nome'])}: {votos(extremo['nexus'])} pela Nexus, "
            f"{votos(extremo['urna'])} pela urna de 2022"
            + (
                "; na lista combinada, que ordena pelo piso das duas, ele sai."
                if sai
                else "."
            )
        )
    return p(texto, "inferencia")


def _tabela_100(R: dict) -> str:
    top = R["rankings"]["top"]["combinacao"]
    cab = [
        ("Nº", True),
        ("Município", False),
        ("UF", False),
        ("Terceira via", True),
        ("Saldo Nexus", True),
        ("Saldo Datafolha", True),
        ("Saldo urna de 2022", True),
        ("Piso", True),
        ("Teto", True),
        ("Nº pesquisa", True),
        ("Nº urna", True),
        ("Situação", False),
        ("O que mais pesa", False),
    ]
    num_cls = ' class="num"'
    th = "".join(
        f'<th scope="col"{num_cls if n else ""}>{escape(c)}</th>' for c, n in cab
    )
    corpo = []
    for i, x in enumerate(top, start=1):
        pos = x["posicao"]
        motivo = (
            "as duas concordam" if x["situacao"] == "robusto" else MOTIVO[x["motivo"]]
        )
        valores = [
            (i, str(i)),
            (x["nome"], escape(nome_bonito(x["nome"]))),
            (x["uf"], x["uf"]),
            (x["estoque"], inteiro(x["estoque"])),
            (x["nexus"], pv(x["nexus"], 0)),
            (x["datafolha"], pv(x["datafolha"], 0)),
            (x["urna"], pv(x["urna"], 0)),
            (x["piso"], pv(x["piso"], 0)),
            (x["teto"], pv(x["teto"], 0)),
            (pos["pesquisa"], inteiro(pos["pesquisa"])),
            (pos["urna"], inteiro(pos["urna"])),
            (x["situacao"], SITUACAO[x["situacao"]]),
            (motivo, motivo),
        ]
        cels = []
        for j, (v, txt) in enumerate(valores):
            tag = "th" if j == 1 else "td"
            esc = ' scope="row"' if j == 1 else ""
            cls = ' class="num"' if cab[j][1] else ""
            cels.append(f'<{tag}{esc}{cls} data-v="{escape(str(v))}">{txt}</{tag}>')
        corpo.append("<tr>" + "".join(cels) + "</tr>")
    return (
        '<div class="table-scroll tv-tab" tabindex="0"><table data-ordena="1">'
        "<caption>Os 100 primeiros pela combinação das duas réguas: ordem pelo piso (o menor saldo esperado das duas), "
        "com o teto ao lado e a posição em cada régua. Robusto: entre os 100 primeiros pela pesquisa e pela urna. "
        "Clique no cabeçalho para ordenar.</caption>"
        f"<thead><tr>{th}</tr></thead><tbody>{''.join(corpo)}</tbody></table></div>"
    )


def _por_uf(R: dict) -> str:
    linhas = []
    for uf, x in sorted(R["rankings"]["por_uf"].items()):
        cel = []
        for v in ("pesquisa", "urna", "combinacao"):
            nomes = []
            for y in x[v]:
                n = escape(nome_bonito(y["nome"]))
                nomes.append(
                    f"<strong>{n}</strong>" if y["situacao"] == "robusto" else n
                )
            cel.append(", ".join(nomes))
        linhas.append([escape(NOME_UF[uf]), *cel, str(x["robustos"])])
    tab = tabela(
        [
            "UF",
            "Pela pesquisa (Nexus)",
            "Pela urna de 2022",
            "Pelo piso das duas",
            "Robustos",
        ],
        linhas,
        "Os 10 primeiros de cada UF pelo saldo esperado, nas três versões. Em negrito, os que as duas réguas põem entre "
        "os 10 da UF.",
    )
    return f"<details><summary>Os 10 primeiros de cada UF pelas duas réguas</summary>{tab}</details>"


def movimentos_urna(R: dict) -> dict[int, dict]:
    """A segunda régua de cada movimento do capítulo, pela ordem."""
    return {mv["ordem"]: mv for mv in R["movimentos"]}


def _retrovisao(R: dict) -> str:
    rv = R["retrovisao"]
    if rv["disponivel"]:
        casas = _lista([a["casa"] for a in rv["achados"]])
        return p(
            f"O acervo tem cruzamento de 2º turno de 2022 em {escape(casas)}; o teste de retrovisão ainda não foi feito.",
            "verificado",
        )
    return p(
        "Falta o teste que diria quanto confiar na matriz: o 2º turno do eleitor de Tebet e de Ciro nas pesquisas de "
        f"outubro de 2022 contra a urna. O acervo não tem esse cruzamento ({rv['pesquisas_transcritas']} pesquisas em "
        f"{escape(rv['procurado_em'][0])}/, todas da última onda do 1º turno).",
        "verificado",
    )


def _juizo(R: dict) -> str:
    rk = R["rankings"]
    so_p = [x for x in rk["divergentes"] if x["situacao"] == "so_pesquisa"]
    so_u = [x for x in rk["divergentes"] if x["situacao"] == "so_urna"]
    return nota(
        "juizo",
        "<ul>"
        f"<li>Comece pelos {rk['robustos']} robustos: as duas réguas dizem que ali a terceira via rende a Flávio.</li>"
        f"<li>Onde só a pesquisa promete ({escape(_nomes(so_p))}), o argumento é o palanque local; meça antes de gastar.</li>"
        f"<li>Onde só a urna entrega ({escape(_nomes(so_u))}), o risco é a linha de Caiado, que as pesquisas medem com "
        "sinais opostos.</li></ul>",
        "Como usar as duas réguas.",
    ) + p(
        "A urna de 2022 é piso provável, porque a terceira via de então era de centro e de esquerda, e a pesquisa é teto "
        "provável, porque ignora o lugar. A distância entre os dois é o tamanho da aposta.",
        "hipotese",
    )


def bloco(D: dict, fig: Callable[[str], str]) -> str:
    """Seção "Pesquisa contra urna" completa, na ordem do texto."""
    R, conv = D["reguas"], D["conversao_2022"]
    return (
        _intro()
        + fig("conversao_2022_classes")
        + _coeficientes(R, conv)
        + fig("terceira_via_reguas_totais")
        + _totais(
            R,
            D["prioridade"]["diferenca_nacional"],
            D["agregados"]["brasil"]["renan_zema_pct"],
        )
        + fig("reguas_divergencia_mapa")
        + _rankings(R)
        + _tabela_100(R)
        + _por_uf(R)
        + _retrovisao(R)
        + _juizo(R)
    )
