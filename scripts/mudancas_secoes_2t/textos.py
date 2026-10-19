"""Textos públicos gerados pelos números: categorias, frase de quem perde e limites."""

from __future__ import annotations

from typing import Any

CATEGORIAS_APP = {
    "A": {
        "nome": "Volta ao local de sempre",
        "frase": "No 1º turno sua seção votou em um local provisório. No 2º turno ela volta "
        "ao local original.",
    },
    "B": {
        "nome": "Mudou de local",
        "frase": "No 2º turno sua seção vota em um local provisório, diferente do original.",
    },
    "C": {
        "nome": "Outro local provisório",
        "frase": "Sua seção já votava fora do local original e no 2º turno vai para outro "
        "local provisório.",
    },
    "X": {
        "nome": "Mudou de local",
        "frase": "O número do local de votação da sua seção mudou entre os turnos.",
    },
    "D": {
        "nome": "Mesmo número, outro prédio",
        "frase": "O número do local é o mesmo, mas o nome e o endereço agora são de outro "
        "prédio.",
    },
    "E": {
        "nome": "Endereço em outra rua",
        "frase": "O nome do local é o mesmo, mas o endereço passou para outra rua. Pode ser "
        "outra entrada do mesmo prédio: confira antes de sair.",
    },
    "painel": {
        "nome": "Fontes do TSE divergem",
        "frase": "O painel do TSE e o arquivo de locais divergem sobre esta seção; confira no "
        "e-Título.",
    },
}
FRASE_DIVERGENCIA = CATEGORIAS_APP["painel"]["frase"]


def _mil(n: float) -> str:
    return f"{round(n):,}".replace(",", ".")


def _pp(x: float, casas: int = 3) -> str:
    return f"{x:.{casas}f}".replace(".", ",")


def _sentido(v: float) -> str:
    """Variação assinada da diferença Flávio menos Lula, em palavras."""
    if round(v) > 0:
        return f"{_mil(v)} votos a favor de Flávio"
    if round(v) < 0:
        return f"{_mil(-v)} votos a favor de Lula"
    return "menos de um voto"


def quem_perde(cen: dict[str, Any]) -> dict[str, str]:
    """Frases nas duas direções, geradas dos cenários."""
    comp = cen["composicao_1t"]["mudanca_real"]
    fixo = next(f for f in cen["fixos"] if f["abstencao_extra_pp"] == 2.0)[
        "mudanca_real"
    ]
    perdas = fixo["perdidos"]
    saldo = fixo["variacao_diferenca_flavio_menos_lula_votos"]
    lider = (
        "Flávio" if comp["flavio_validos_pct"] > comp["lula_validos_pct"] else "Lula"
    )
    outro = "Lula" if lider == "Flávio" else "Flávio"
    texto_alta = (
        f"As {_mil(comp['urnas'])} urnas com mudança real deram no 1º turno "
        f"{_pp(comp['flavio_validos_pct'], 2)}% dos válidos a Flávio e "
        f"{_pp(comp['lula_validos_pct'], 2)}% a Lula. Com 2 pontos a mais de abstenção "
        f"nelas, Flávio perderia {_mil(perdas['flavio'])} votos e Lula "
        f"{_mil(perdas['lula'])}; a diferença entre os dois mudaria {_sentido(saldo)} "
        f"({_pp(abs(fixo['variacao_diferenca_pp_validos_nacionais']), 4)} ponto dos válidos "
        f"nacionais do 1º turno). Quem perde mais voto é {lider}, porque teve mais voto "
        f"nessas urnas que {outro}."
    )
    br = cen["estimativa_brasileira"]
    if "saldo_1t_para_2t" in br:
        a = br["categoria_a_ganho"]["central"]
        liq = br["saldo_1t_para_2t"]["central"]
        mag = br["magnitude_pp"]["central"]
        lo, hi = br["magnitude_pp"]["ic95"]
        texto_baixa = (
            f"Na direção contrária, as urnas da categoria A voltam ao prédio original. Se "
            f"recuperarem o comparecimento na magnitude medida no 1º turno "
            f"({_pp(mag, 2)} ponto, IC 95% de {_pp(lo, 2)} a {_pp(hi, 2)}), Flávio "
            f"ganharia {_mil(-a['perdidos']['flavio'])} votos e Lula "
            f"{_mil(-a['perdidos']['lula'])}. Somando a perda das novas realocações e o "
            "ganho da categoria A, a diferença entre os dois varia "
            f"{_sentido(liq['variacao_diferenca_flavio_menos_lula_votos'])} "
            f"({_pp(abs(liq['variacao_diferenca_pp_validos_nacionais']), 4)} ponto dos "
            "válidos nacionais)."
        )
    else:
        texto_baixa = "Sem estimativa brasileira de magnitude, o cenário de ganho não foi calculado."
    return {"abstencao_maior": texto_alta, "comparecimento_recuperado": texto_baixa}


def limites(clima_pendente: bool, tre_vazio: bool) -> list[str]:
    out = [
        "Comparação, não efeito causal: o TRE escolhe quais locais mudar e por quê; "
        "seções com local temporário não são sorteadas.",
        "O cadastro de 18/10 ainda pode mudar até 25/10, e o painel do TSE com o mesmo "
        "carimbo de hora diverge do arquivo de locais em parte das seções.",
        "A distância é em linha reta entre as coordenadas do TSE, não o caminho a pé; "
        "coordenada repetida por três ou mais locais do município é marcador de posição e "
        "fica fora das estatísticas de distância.",
        "Nome e endereço iguais com coordenada diferente (categoria G) e troca só de nome "
        "(F) não contam como mudança real: o eleitor vai ao mesmo prédio. A sensibilidade "
        "está no resumo.",
        "Seção agregada vota na urna da principal e herda a classificação dela.",
        "Os cenários usam a composição do 1º turno de cada urna; no 2º turno o voto das "
        "demais candidaturas se redistribui. É a conta do tamanho, não previsão.",
        "Leitura agregada por seção: o voto é secreto e nada aqui identifica eleitor.",
        "Registro de bateria, reinício ou fila no log é registro operacional, não "
        "irregularidade.",
        "No Rio de Janeiro, as transferências por segurança no 1º turno mantiveram o número "
        "do local e trocaram nome e endereço; a regra local diferente do original não as "
        "enxerga, e o grupo troca desde 2022 também inclui renomeação de escola.",
        "O exterior fica fora das comparações nacionais de comportamento e intercorrências.",
    ]
    if clima_pendente:
        out.append(
            "Clima pendente: o arquivo do Open-Meteo não existia no momento do build."
        )
    if tre_vazio:
        out.append(
            "Notas dos TREs pendentes: o arquivo de notícias não existia no build."
        )
    else:
        out.append(
            "As notas dos TREs casam por UF e município; só o grau local indica a mesma "
            "seção ou o mesmo prédio. Motivo ausente na nota fica como não informado."
        )
    return out
