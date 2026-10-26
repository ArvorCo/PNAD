"""Textos do capítulo "Totalização paralela"; números de ``paralela.json`` e ``presidente.json``."""

from __future__ import annotations

from apuracao_2026.pagina_comum import cartao, inteiro, nota, num, p

from .pagina_fig_paralela import pares_relogio

ROTULO = "soma dos BUs recebidos, não projeção"


def titulo(P: dict) -> str:
    c = P.get("conferencia") or {}
    div = sum(v for k, v in c.items() if k != "igual")
    if not div:
        return f"Totalização paralela.<br><em>{inteiro(c.get('igual'))} BUs, nenhuma divergência.</em>"
    return "Totalização paralela.<br><em>BU a BU contra o oficial.</em>"


def lead(P: dict) -> str:
    rcb = P["recebidos"]
    return (
        f"{inteiro(rcb['bus'])} boletins de urna lidos pelo QR em {inteiro(rcb['ufs'])} UFs, conferidos "
        "voto a voto contra o arquivo publicado pelo TSE para a mesma seção."
    )


def cartoes(P: dict) -> str:
    c = P.get("conferencia") or {}
    div = sum(v for k, v in c.items() if k != "igual")
    pres = P["placar_bus"]["presidente"]
    return (
        '<div class="finding-grid">'
        + cartao(inteiro(P["recebidos"]["bus"]), "BUs recebidos e verificados")
        + cartao(inteiro(c.get("igual")), "iguais ao oficial, voto a voto")
        + cartao(inteiro(div), "divergentes")
        + cartao(
            f"{num(pres.get('pct_comparecimento'), 2)}%",
            "comparecimento nas seções recebidas",
        )
        + "</div>"
    )


def abre(P: dict, Pres: dict | None) -> str:
    pres = P["placar_bus"]["presidente"]
    abst = 100 - (pres.get("pct_comparecimento") or 0)
    h = p(
        f"A paralela recebeu {inteiro(P['recebidos']['bus'])} BUs de {inteiro(P['recebidos']['secoes'])} "
        f"seções. Cada um teve a assinatura da urna e a cadeia de certificados verificadas antes de "
        f"contar, e foi comparado com o BU que o TSE publicou para a seção: {inteiro((P.get('conferencia') or {}).get('igual'))} "
        f"iguais. Nas seções recebidas, {inteiro(pres.get('aptos'))} aptos, "
        f"{inteiro(pres.get('comparecimento'))} votantes ({num(pres.get('pct_comparecimento'), 2)}%, "
        f"abstenção de {num(abst, 2)}%), {inteiro(pres.get('brancos'))} brancos e "
        f"{inteiro(pres.get('nulos'))} nulos.",
        "verificado",
    )
    if Pres:
        n = Pres["nacional"]
        h += nota(
            "contrario",
            f"A soma dá Flávio {num(pres.get('pct_flavio_nominais'), 2)}% contra "
            f"{num(n.get('pct_flavio'), 2)}% no país. A "
            "diferença não diz nada sobre a urna: a amostra é de quem enviou, concentrada em SP e em "
            "quem baixou o aplicativo, e não representa o eleitorado. É "
            f"{ROTULO}.",
        )
    return h


def relogios(P: dict) -> str:
    pares = pares_relogio(P)
    if not pares:
        return ""
    antes = [(a, c) for a, c, _ in pares if a < c]
    av = sorted(c - a for a, c in antes)
    med = av[len(av) // 2] if av else 0
    ate19 = sum(1 for a, _, _ in pares if a < 120)
    return p(
        f"O relógio confirma o capítulo das seções por outra porta: {inteiro(len(antes))} dos "
        f"{inteiro(len(pares))} BUs chegaram à paralela antes de o TSE registrar o recebimento da mesma "
        f"seção, com vantagem mediana de {num(med, 0)} min; {inteiro(ate19)} chegaram antes das 19:00. "
        "O BU estava impresso e na mão do cidadão enquanto o arquivo oficial esperava a transmissão.",
        "verificado",
    )


def prova() -> str:
    return nota(
        "juizo",
        "BU igual ao oficial prova que o que a urna imprimiu na seção é o que o TSE recebeu e somou. "
        "Não prova o interior da urna, nem quem votou, nem o que aconteceu antes da impressão. A "
        "paralela confere transmissão e totalização, e só das seções que alguém enviou.",
        "O que isso prova.",
    )


def limites_itens(P: dict) -> list[str]:
    return [
        P.get("limite") or "",
        f"Placar da paralela: {ROTULO}.",
        "Hora de recebimento do TSE é a registrada no arquivo oficial da seção; a da paralela é a de chegada ao servidor.",
    ]
