"""Formatação e vocabulário do capítulo "O caminho do 2º turno".

Números em grafia brasileira (vírgula decimal, ponto de milhar, sinal de menos
tipográfico), nomes de urna em caixa normal, pequenos números por extenso e
tabelas Markdown. Sem travessão: o caractere não entra em texto público.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .estrategia import milhar

MENOS = "−"
PARTICULAS = {"DE", "DA", "DO", "DOS", "DAS", "E", "DI"}
SIGLAS = {"JHC", "II"}
NOMES = {
    "FLAVIO BOLSONARO": "Flávio Bolsonaro",
    "LULA": "Lula",
    "ESCRITOR AUGUSTO CURY": "Augusto Cury",
    "RENAN SANTOS": "Renan Santos",
    "RONALDO CAIADO": "Ronaldo Caiado",
    "ZEMA": "Romeu Zema",
    "SAMARA": "Samara Martins",
}
UF_NOME = {
    "AC": "Acre",
    "AL": "Alagoas",
    "AP": "Amapá",
    "AM": "Amazonas",
    "BA": "Bahia",
    "CE": "Ceará",
    "DF": "Distrito Federal",
    "ES": "Espírito Santo",
    "GO": "Goiás",
    "MA": "Maranhão",
    "MT": "Mato Grosso",
    "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais",
    "PA": "Pará",
    "PB": "Paraíba",
    "PR": "Paraná",
    "PE": "Pernambuco",
    "PI": "Piauí",
    "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul",
    "RO": "Rondônia",
    "RR": "Roraima",
    "SC": "Santa Catarina",
    "SP": "São Paulo",
    "SE": "Sergipe",
    "TO": "Tocantins",
}
ROTULO_HIPOTESE = {
    "fica_fora": "só o medido",
    "proporcional": "não escolha na proporção da linha",
    "meio_a_meio": "não escolha meio a meio",
}
FRASE_HIPOTESE = {
    "fica_fora": "só com o que foi medido",
    "proporcional": "com a não escolha votando na proporção da própria linha",
    "meio_a_meio": "com a não escolha dividida meio a meio",
}
ROTULO_MATRIZ = {"nexus": "Nexus", "datafolha": "Datafolha em Cury e Caiado"}
FRASE_MATRIZ = {
    "nexus": "com as linhas da Nexus",
    "datafolha": "com as linhas do Datafolha para Cury e Caiado",
}


# ---------------------------------------------------------------- formatação


def nome(txt: str | None) -> str:
    """Nome de urna em caixa alta para a grafia de texto corrido."""
    if not txt:
        return ""
    if txt in NOMES:
        return NOMES[txt]
    partes = []
    for i, p in enumerate(txt.split()):
        if p in SIGLAS:
            partes.append(p)
        elif i > 0 and p in PARTICULAS:
            partes.append(p.lower())
        else:
            partes.append(p[:1] + p[1:].lower())
    return " ".join(partes)


def dec(x: float, casas: int = 2) -> str:
    return f"{x:.{casas}f}".replace(".", ",")


def pc(x: float, casas: int = 2) -> str:
    return f"{dec(x, casas)}%"


def sinal(x: float, casas: int = 2) -> str:
    """Número com sinal explícito; o negativo usa o sinal de menos (U+2212)."""
    if round(x, casas) > 0:
        return f"+{dec(x, casas)}"
    if round(x, casas) < 0:
        return f"{MENOS}{dec(-x, casas)}"
    return dec(0.0, casas)


def sinal_votos(x: float) -> str:
    if x > 0:
        return f"+{milhar(x)}"
    if x < 0:
        return f"{MENOS}{milhar(-x)}"
    return "0"


def qtd(x: float, coisa: str = "votos") -> str:
    """Quantidade em prosa: milhões com duas casas, milhares arredondados."""
    a = abs(x)
    menos = MENOS if x < 0 else ""
    if a >= 1_000_000:
        rotulo = "milhão" if a < 2_000_000 else "milhões"
        return f"{menos}{dec(a / 1_000_000)} {rotulo} de {coisa}"
    if a >= 10_000:
        return f"{menos}{milhar(a / 1000)} mil {coisa}"
    return f"{menos}{milhar(a)} {coisa}"


def faixa_milhoes(a: float, b: float, coisa: str = "votos") -> str:
    return f"de {dec(a / 1_000_000)} a {dec(b / 1_000_000)} milhões de {coisa}"


def pontos(x: float, casas: int = 2) -> str:
    """Valor absoluto em pontos, com singular abaixo de 2."""
    a = abs(x)
    return f"{dec(a, casas)} {'ponto' if a < 2 else 'pontos'}"


def acima_abaixo(x: float) -> str:
    return "acima" if x > 0 else "abaixo"


EXTENSO = {
    1: ("um", "uma"),
    2: ("dois", "duas"),
    3: ("três", "três"),
    4: ("quatro", "quatro"),
    5: ("cinco", "cinco"),
    6: ("seis", "seis"),
    7: ("sete", "sete"),
    8: ("oito", "oito"),
    9: ("nove", "nove"),
    10: ("dez", "dez"),
}


def extenso(n: int, feminino: bool = False) -> str:
    """Número por extenso até dez, como pede a escrita corrida; acima, algarismos."""
    if n in EXTENSO:
        return EXTENSO[n][1 if feminino else 0]
    return milhar(n)


def lista_e(itens: list[str]) -> str:
    itens = [i for i in itens if i]
    if len(itens) <= 1:
        return "".join(itens)
    return ", ".join(itens[:-1]) + " e " + itens[-1]


def numero_alinhado(celula: str) -> bool:
    c = celula.strip("*").strip()
    return bool(c) and (c[0].isdigit() or c[0] in "+" + MENOS)


def tabela(cabecalho: list[str], linhas: list[list[str]]) -> str:
    alinha = []
    for j in range(len(cabecalho)):
        coluna = [linha[j] for linha in linhas if linha[j]]
        numerica = bool(coluna) and all(numero_alinhado(c) for c in coluna)
        alinha.append("---:" if numerica else "---")
    out = ["| " + " | ".join(cabecalho) + " |", "| " + " | ".join(alinha) + " |"]
    out += ["| " + " | ".join(linha) + " |" for linha in linhas]
    return "\n".join(out)


def hora_br(iso: str) -> str:
    """Instante UTC ISO como data e hora de Brasília (UTC−3, sem horário de verão)."""
    instante = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    local = instante.astimezone(timezone(timedelta(hours=-3)))
    return f"{local:%d/%m/%Y}, {local:%H}h{local:%M}"
