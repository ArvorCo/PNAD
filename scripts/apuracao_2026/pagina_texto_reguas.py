"""Capítulo 13, bloco "Pesquisa contra urna: duas réguas para o mesmo estoque".

Chamado por `pagina_texto_terceira_via.bloco`. Todo número sai de
`analysis/apuracao_2026/dados/terceira_via.json → reguas` e `→ conversao_2022`.
Figura antes do parágrafo que a lê.
"""

from __future__ import annotations

from collections.abc import Callable
from html import escape

from .pagina_comum import NOME_UF, inteiro, num, p, tabela
from .pagina_fig_base import nome_bonito
from .pagina_fig_terceira_via_b import ORDENA_JS

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
    return (
        "<h3>Pesquisa contra urna: duas réguas para o mesmo estoque</h3>"
        + p(
            "Até aqui, o voto de terceira via virou voto de 2º turno por uma régua só: a das pesquisas de setembro, que "
            "perguntaram ao eleitor de cada candidatura em quem votaria entre Flávio e Lula. Há uma segunda régua, a da "
            "urna de 2022: quanto o saldo de Bolsonaro sobre Lula cresceu entre os turnos onde havia mais voto de terceira "
            "via, município a município. A pesquisa sabe o nome e não sabe o lugar. A urna sabe o lugar, não sabe o nome "
            "e é de outra eleição."
        )
        + '<aside class="analogy"><b>Em linguagem de casa</b>Uma padaria quer saber quanto pão vende amanhã. Uma régua '
        "é perguntar aos fregueses: cada um diz o que pretende levar. A outra é olhar o caixa do mesmo dia no ano passado, "
        "rua por rua: não diz quem comprou, mas diz quanto saiu de verdade em cada rua. Quando as duas batem, dá para assar "
        "sem medo. Quando não batem, a diferença é o tamanho da aposta.</aside>"
    )


def _coeficientes(R: dict, conv: dict) -> str:
    gc = R["modelos"]["classe"]["grupos"]
    un = R["modelos"]["unico"]["grupos"]["todos"]
    sfe = R["modelos"]["sem_efeito_fixo"]
    rc = conv["por_classe"]

    def ic(g: dict) -> str:
        a, b = g["saldo_ic95"]
        return f"{pv(a)} a {pv(b)}"

    h = p(
        "Na urna de 2022, dentro da mesma UF, cada voto de terceira via do 1º turno somou ao saldo de Bolsonaro sobre Lula "
        f"{pv(gc['venceu_folga']['saldo'])} nos municípios onde Flávio venceu com folga em 2026 (intervalo de 95%: "
        f"{ic(gc['venceu_folga'])}), {pv(gc['venceu_apertado']['saldo'])} onde venceu apertado, "
        f"{pv(gc['perdeu_apertado']['saldo'])} onde perdeu apertado e {pv(gc['perdeu_folga']['saldo'])} onde perdeu com "
        f"folga ({ic(gc['perdeu_folga'])}). No país, com uma inclinação só, {pv(un['saldo'])} ({ic(un)}): a terceira via de "
        f"2022 dividiu-se quase ao meio, {num(un['bolsonaro'], 2)} para Bolsonaro e {num(un['lula'], 2)} para Lula por voto.",
        "inferencia",
    )
    h += p(
        f"A razão simples dá muito mais: {pv(rc['venceu_folga']['saldo'])}, {pv(rc['venceu_apertado']['saldo'])}, "
        f"{pv(rc['perdeu_apertado']['saldo'])} e {pv(rc['perdeu_folga']['saldo'])} nas mesmas classes, "
        f"{pv(conv['brasil']['saldo'])} no país. Ela divide todo o ganho entre os turnos pela terceira via e põe na conta "
        "dela o que veio de outro lugar: gente que não tinha votado e voltou, base que se mobilizou. Sem o efeito fixo de "
        f"UF, a regressão dá {pv(sfe['saldo_terceira_via'])} por voto de terceira via e uma parcela de "
        f"{num(100 * sfe['constante'], 2)} pontos dos votantes a favor de Bolsonaro que não depende da terceira via. É essa "
        "parcela que a razão simples atribui à terceira via.",
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
        aviso_regiao = (
            f" Por região, as duas inclinações somam mais de um voto por voto de terceira via em {detalhe}: ali a "
            "regressão capta algo além da terceira via, como comparecimento que anda junto com ela. Por isso a régua "
            "aplicada a 2026 usa a classe de margem, e a região fica como sensibilidade."
        )
    h += (
        '<aside class="hyp"><b>Limite ecológico</b>'
        "A régua da urna é inferência de agregado para agregado: diz quanto o saldo cresceu a mais onde havia mais "
        "terceira via, na mesma UF, e não como votou o eleitor de Tebet ou de Ciro. E a terceira via de 2022 era outra: "
        "Simone Tebet (MDB) e Ciro Gomes (PDT), centro e esquerda pela classificação da casa; a de 2026 tem Augusto Cury "
        f"(Avante) e Ronaldo Caiado (PSD), de centro, e Renan Santos (Missão) e Zema (Novo), de direita.{aviso_regiao}</aside>"
    )
    return h


def _totais(R: dict, diferenca: int) -> str:
    T = R["totais"]
    br, cl, rg = T["brasil"], T["classes"], T["regioes"]
    a, b = br["urna_ic95"]
    pior = min(a, br["urna_regiao"], br["urna"], br["nexus"], br["datafolha"])
    fecho = (
        f"Com as bases do 1º turno fixas, nenhuma das réguas, nem o limite inferior do intervalo da urna, desfaz a "
        f"diferença de {votos(diferenca, False)} do 1º turno."
        if pior > -diferenca
        else f"No pior caso ({votos(pior)}), a terceira via desfaria a diferença de {votos(diferenca, False)} do 1º turno."
    )
    h = p(
        f"Aplicadas ao estoque de 2026, as réguas dão a Flávio saldo de {votos(br['nexus'])} pela matriz Nexus, "
        f"{votos(br['datafolha'])} com as linhas do Datafolha para Cury e Caiado e {votos(br['urna'])} pela urna de 2022 "
        f"(intervalo de 95%: {votos(a)} a {votos(b)}). Pela região em vez da classe, a urna dá {votos(br['urna_regiao'])}; "
        f"pela razão simples, {votos(br['razao_simples'])}, o teto que credita tudo à terceira via. {fecho}",
        "inferencia",
    )
    h += p(
        f"Onde Flávio venceu com folga as duas réguas quase coincidem: a Nexus dá {pv(cl['venceu_folga']['pv_nexus'])} por "
        f"voto e a urna de 2022, {pv(cl['venceu_folga']['pv_urna'])}. Onde Flávio perdeu, a pesquisa promete "
        f"{pv(cl['perdeu_apertado']['pv_nexus'])} e {pv(cl['perdeu_folga']['pv_nexus'])}, e a urna entregou "
        f"{pv(cl['perdeu_apertado']['pv_urna'])} e {pv(cl['perdeu_folga']['pv_urna'])}. No Centro-Oeste é a urna que "
        f"rende mais ({pv(rg['Centro-Oeste']['pv_urna'])} contra {pv(rg['Centro-Oeste']['pv_nexus'])} da Nexus): o estoque "
        "ali é de Caiado, cuja linha Nexus dá mais a Lula, e fica onde Flávio venceu com folga.",
        "inferencia",
    )
    return h


def _por_que(direita_pct: float) -> str:
    return p(
        "Por que divergem: a pesquisa aplica a mesma linha no país inteiro, como se o eleitor de Cury em Salvador votasse "
        "como o de Cury em Joinville. A urna de 2022 mostra que o lugar puxa: onde a direita já ganhava, a terceira via "
        "foi mais para Bolsonaro; onde perdia, foi mais para Lula. E a urna não sabe o nome: em 2022 a terceira via era de "
        f"centro e de esquerda; em 2026, Renan e Zema, de direita, somam {num(direita_pct, 2)}% dela. Por isso a urna "
        "tende a pesar contra Flávio onde ele perdeu, e a pesquisa tende a ignorar o lugar.",
        "inferencia",
    )


def _rankings(R: dict) -> str:
    rk = R["rankings"]
    mot = rk["motivos_divergencia"]
    so_p = [x for x in rk["divergentes"] if x["situacao"] == "so_pesquisa"]
    so_u = [x for x in rk["divergentes"] if x["situacao"] == "so_urna"]
    extremo = max(so_p, key=lambda x: x["teto"] - x["piso"], default=None)
    h = p(
        f"Ordenando os municípios pelo saldo esperado, {rk['robustos']} dos 100 primeiros pela pesquisa também estão "
        f"entre os 100 primeiros pela urna de 2022: são os robustos, com {votos(rk['robustos_estoque'], False)} de "
        f"terceira via. Dos {rk['so_pesquisa']} que só a pesquisa põe na lista, a classe de margem explica "
        f"{mot.get('so_pesquisa:classe', 0)} "
        f"e a composição por nome {mot.get('so_pesquisa:composicao', 0)}; os maiores são "
        f"{_cidades(so_p)}. Dos {rk['so_urna']} que só a urna põe, a classe explica {mot.get('so_urna:classe', 0)} e a "
        f"composição {mot.get('so_urna:composicao', 0)}; os maiores são {_cidades(so_u)}.",
        "inferencia",
    )
    if extremo:
        lado = "perdeu" if extremo["classe"].startswith("perdeu") else "venceu"
        folga = (
            "com folga"
            if extremo["classe"].endswith("folga")
            else "por menos de 10 pontos"
        )
        efeito = (
            "não deu saldo a Bolsonaro"
            if extremo["pv_urna"] <= 0
            else "deu menos saldo a Bolsonaro que a pesquisa promete"
        )
        sai = extremo["posicao"]["combinacao"] > len(rk["top"]["combinacao"])
        h += p(
            f"{nome_bonito(extremo['nome'])} é o caso de maior distância entre as réguas: pela Nexus, "
            f"{votos(extremo['nexus'])}; pela urna de 2022, {votos(extremo['urna'])}, porque o município está na "
            f"classe em que Flávio {lado} {folga}, e ali a terceira via de 2022 {efeito}."
            + (
                " Na lista combinada, que ordena pelo piso das duas réguas, ele sai."
                if sai
                else ""
            ),
            "inferencia",
        )
    return h


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
        + ORDENA_JS
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


def _movimentos(R: dict) -> str:
    linhas = []
    for mv in R["movimentos"]:
        if mv["urna"] is None:
            urna, por, conc = "não se aplica", "", escape(mv.get("nota", ""))
        else:
            urna = pv(mv["urna"], 0)
            por = pv(mv.get("pv_urna"), 3) if mv.get("pv_urna") is not None else ""
            conc = "mesmo sinal" if mv["concordam"] else "sinal oposto"
            if mv.get("nota"):
                conc += f"; {escape(mv['nota'])}"
        linhas.append(
            [
                f"{mv['ordem']}. {escape(mv['titulo'])}",
                pv(mv["pesquisa"], 0),
                urna,
                por,
                conc,
            ]
        )
    return tabela(
        [
            "Movimento do capítulo",
            "Votos esperados (régua do capítulo)",
            "Pela urna de 2022",
            "Por voto (urna)",
            "As duas réguas",
        ],
        linhas,
        "Os dez movimentos com a segunda régua ao lado. A urna de 2022 só se aplica aos movimentos sobre o voto de "
        "terceira via; nos demais, a régua do capítulo é a única.",
    )


def _retrovisao(R: dict) -> str:
    rv = R["retrovisao"]
    if rv["disponivel"]:
        casas = _lista([a["casa"] for a in rv["achados"]])
        return p(
            f"O acervo tem cruzamento de 2º turno de 2022 em {escape(casas)}; o teste de retrovisão ainda não foi feito.",
            "verificado",
        )
    return p(
        "O teste de retrovisão compararia a matriz das pesquisas de 2022 (o voto de 2º turno do eleitor de Tebet e de "
        "Ciro) com o que a urna de 2022 entregou, por região: é ele que diria quanto confiar na matriz de 2026. O acervo "
        f"não tem esse documento: são {rv['casas_no_acervo']} pastas em {escape(rv['procurado_em'][0])}/ e "
        f"{rv['pesquisas_transcritas']} pesquisas transcritas, todas da última onda antes do 1º turno. Para fazer o teste é "
        "preciso arquivar as primeiras ondas nacionais de 2º turno de outubro de 2022 que tenham cruzado o voto de 2º "
        "turno pelo voto em Tebet e Ciro (e, se houver, o mesmo cruzamento por região), com URL, SHA-256 e página, no "
        "formato de pesquisas_2022.json.",
        "verificado",
    )


def _juizo(R: dict) -> str:
    rk = R["rankings"]
    so_p = [x for x in rk["divergentes"] if x["situacao"] == "so_pesquisa"]
    so_u = [x for x in rk["divergentes"] if x["situacao"] == "so_urna"]
    return (
        '<aside class="juizo"><b>Juízo editorial: como usar as duas réguas</b><ul>'
        f"<li>Comece pelos {rk['robustos']} robustos: as duas réguas concordam que ali a terceira via rende saldo a Flávio.</li>"
        f"<li>Onde só a pesquisa promete, como em {escape(_nomes(so_p))}, a urna de 2022 diz que a terceira via se dividiu ou foi "
        "para Lula. Ali o argumento é o palanque local, não a conversão; meça antes de gastar.</li>"
        f"<li>Onde só a urna entrega, como em {escape(_nomes(so_u))}, a conversão aconteceu em 2022 sem depender do nome; o risco "
        "é a linha de Caiado, que as duas pesquisas medem com sinais opostos.</li>"
        "<li>Hipótese: a urna de 2022 é piso provável, porque a terceira via de então era de centro e de esquerda, e a "
        "pesquisa é teto provável, porque ignora o lugar. A distância entre os dois é o tamanho da aposta, não o "
        "resultado.</li></ul></aside>"
    )


def bloco(D: dict, fig: Callable[[str], str]) -> str:
    """Seção "Pesquisa contra urna" completa, na ordem do texto."""
    R, conv = D["reguas"], D["conversao_2022"]
    return (
        _intro()
        + fig("conversao_2022_classes")
        + _coeficientes(R, conv)
        + _totais(R, D["prioridade"]["diferenca_nacional"])
        + _por_que(D["agregados"]["brasil"]["renan_zema_pct"])
        + fig("reguas_divergencia_mapa")
        + _rankings(R)
        + _tabela_100(R)
        + _por_uf(R)
        + _movimentos(R)
        + _retrovisao(R)
        + _juizo(R)
    )
