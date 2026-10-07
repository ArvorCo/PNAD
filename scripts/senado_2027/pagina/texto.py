"""Valores curtos do template e frases geradas a partir dos números do motor.

Nada aqui é digitado: todo número sai de `docs/assets/senado_2027.json`. As
frases nunca presumem gênero; o JSON não traz gênero dos senadores, então o
texto fala de "a candidatura de X", "o mandato de X" ou só do nome.
"""

from __future__ import annotations

import statistics
from html import escape as esc

from governador_2026.pagina.view import _chances
from senado_2026.pagina.comum import data_br, num

QUORUM = {"pec": 49, "imp": 54}
ALVO_DO_QUORUM = {"pec": "C_pec", "imp": "C_imp"}
NOME_ALVO = {"pec": "PEC", "imp": "impeachment"}
CENARIOS = ("flavio", "lula")
NOME_CENARIO = {"flavio": "governo Flávio", "lula": "governo Lula"}

VALORES = (
    "DATE",
    "N_SENADORES",
    "N_COM_CASO",
    "K_MEDIA",
    "K_MEDIANA",
    "ESPERADO_PEC_FLAVIO",
    "ESPERADO_IMP_FLAVIO",
    "ESPERADO_PEC_LULA",
    "ESPERADO_IMP_LULA",
    "P49_FLAVIO",
    "P54_FLAVIO",
    "P49_LULA",
    "P54_LULA",
    "N_ALTA",
    "N_MEDIA",
    "N_BAIXA",
    "N_PIVOS",
    "PIVOS_NOMES",
    "N_PEC8_PRESENTES",
    "N_PEC8_SIM",
    "N_PEC8_NAO",
    "N_PEC8_AUSENTES",
)


# ---------------------------------------------------------------- números


def pct_inteiro(p: float | None) -> str:
    """Percentual de 0 a 100 como inteiro, sem falsa precisão nas pontas."""
    if p is None:
        return "sem estimativa"
    if 0 < p < 1:
        return "menos de 1%"
    if 99 < p < 100:
        return "mais de 99%"
    return f"{round(p)}%"


def chances(p: float | None) -> str:
    """Probabilidade em palavras, de 0 a 100. Acima de 50 usa `_chances` da
    página de governador; abaixo, o espelho ("1 chance em 4")."""
    if p is None:
        return "sem estimativa"
    q = p / 100
    if q >= 0.5:
        return _chances(q)
    r = 1 - q
    if r >= 0.97:
        return "quase nenhuma chance"
    if r >= 0.85:
        return "1 chance em 10"
    if r >= 0.72:
        return "1 chance em 4"
    if r >= 0.6:
        return "1 chance em 3"
    if r >= 0.55:
        return "pouco menos que cara ou coroa"
    return "cara ou coroa"


def lista_nomes(nomes: list[str]) -> str:
    nomes = [n for n in nomes if n]
    if not nomes:
        return "nenhum"
    if len(nomes) == 1:
        return nomes[0]
    return ", ".join(nomes[:-1]) + " e " + nomes[-1]


# ---------------------------------------------------------------- acesso


def base(data: dict, cenario: str) -> dict:
    """Variante base da simulação no cenário pedido."""
    return data["simulacao"]["cenarios"][cenario]["base"]


def pivos(data: dict, cenario: str = "flavio", alvo: str = "imp") -> list[dict]:
    return list(base(data, cenario).get("pivos", {}).get(alvo, []))


def titulares(data: dict) -> list[dict]:
    return [item["titular"] for item in data["elenco"]]


def ks(data: dict) -> list[float]:
    return [t["scores"]["K"] for t in titulares(data)]


def pec8_presentes(data: dict) -> dict:
    return data["contexto"]["pec8"]["elenco_2027_presentes_em_2023"]


# ---------------------------------------------------------------- frases


def frase_hero(esperado: float, quorum: int, p_quorum: float) -> str:
    """'57,9 votos esperados para um quórum de 49: 9 chances em 10.'"""
    return (
        f"{num(esperado)} votos esperados para um quórum de {quorum}: "
        f"{chances(p_quorum)}."
    )


def frase_pivos(data: dict, cenario: str = "flavio", alvo: str = "imp") -> str:
    """Quem decide, com a aritmética do esperado."""
    lista = pivos(data, cenario, alvo)
    sim = base(data, cenario)[alvo]
    quorum = QUORUM[alvo]
    falta = quorum - sim["votos_esperados"]
    if not lista:
        return "A simulação não apontou pivôs neste cenário."
    if falta <= 0:
        return (
            f"Em {NOME_CENARIO[cenario]}, o esperado de {num(sim['votos_esperados'])} "
            f"votos já passa de {quorum}. Os {len(lista)} pivôs decidem se a "
            f"margem se mantém: a chance de chegar a {quorum} é "
            f"{pct_inteiro(sim['P' + str(quorum)])}."
        )
    n, nomes, ganho = pivos_necessarios(data, cenario, alvo)
    if n is None:
        return (
            f"Em {NOME_CENARIO[cenario]}, faltam {num(falta)} votos esperados para "
            f"{quorum}. Mesmo virando todos os {len(lista)} pivôs, a soma do que cada "
            f"um ainda pode acrescentar ({num(ganho)}) não fecha a conta."
        )
    return (
        f"Em {NOME_CENARIO[cenario]}, faltam {num(falta)} votos esperados para chegar "
        f"a {quorum}. Contando o que cada pivô ainda pode acrescentar (100 menos o C), "
        f"são precisos {n} dos {len(lista)} pivôs, na ordem de peso da simulação: "
        f"{esc(lista_nomes(nomes))}."
    )


def pivos_necessarios(
    data: dict,
    cenario: str = "flavio",
    alvo: str = "imp",
    faixa: tuple[float, float] | None = None,
) -> tuple[int | None, list[str], float]:
    """Quantos pivôs, do mais decisivo ao menos, cobrem a falta de votos esperados.

    Cada pivô acrescenta (100 − C) / 100 voto esperado se virar sim. Devolve
    (n, nomes, ganho acumulado); n é None quando nem todos juntos bastam.
    `faixa` restringe a conta aos pivôs com C dentro do intervalo.
    """
    lista = sorted(pivos(data, cenario, alvo), key=lambda p: -p["decisivo_pp"])
    if faixa:
        lista = [p for p in lista if faixa[0] <= p["C"] <= faixa[1]]
    falta = QUORUM[alvo] - base(data, cenario)[alvo]["votos_esperados"]
    ganho, nomes = 0.0, []
    for p in lista:
        if ganho >= falta:
            break
        ganho += (100 - p["C"]) / 100
        nomes.append(p["nome"])
    if ganho < falta:
        return None, nomes, ganho
    return len(nomes), nomes, ganho


def frase_tipos(data: dict, cenario: str = "flavio") -> str:
    """Opinião e 8 de janeiro contra patrimonial, com os C médios do motor."""
    tipos = data["agregados"]["por_tipo_de_caso"][cenario]
    partes = []
    for chave, rotulo in (
        ("opiniao", "de opinião"),
        ("8_de_janeiro", "de 8 de janeiro"),
        ("patrimonial", "patrimoniais"),
        ("eleitoral", "eleitorais"),
    ):
        t = tipos.get(chave)
        if not t:
            continue
        partes.append(
            f"casos {rotulo}: {t['senadores']} senadores, C de impeachment médio "
            f"{num(t['C_imp_medio'])}"
        )
    op = tipos.get("opiniao", {}).get("C_imp_medio")
    pa = tipos.get("patrimonial", {}).get("C_imp_medio")
    if op is not None and pa is not None:
        if op > pa:
            leitura = (
                f" O C médio de quem responde por opinião supera o do patrimonial em "
                f"{num(op - pa)} pontos: quem tem caso de opinião tende a contrapor "
                "mais, e é no patrimonial que a hipótese do post pode valer."
            )
        else:
            leitura = (
                " O C médio do patrimonial não fica abaixo do de opinião: neste "
                "cenário, os números não separam os dois tipos."
            )
    else:
        leitura = ""
    return "Em " + NOME_CENARIO[cenario] + ", " + "; ".join(partes) + "." + leitura


# ---------------------------------------------------------------- valores


def values(data: dict) -> dict[str, str]:
    """Os placeholders curtos do template."""
    tit = titulares(data)
    lista_k = ks(data)
    conf = [t["scores"]["confianca"] for t in tit]
    pres = pec8_presentes(data)
    piv = pivos(data, "flavio", "imp")
    out = {
        "DATE": data_br(data.get("referencia") or data.get("gerado_em")),
        "N_SENADORES": str(len(tit)),
        "N_COM_CASO": str(sum(1 for t in tit if t.get("casos"))),
        "K_MEDIA": num(statistics.fmean(lista_k)),
        "K_MEDIANA": num(statistics.median(lista_k)),
        "N_ALTA": str(conf.count("alta")),
        "N_MEDIA": str(conf.count("media")),
        "N_BAIXA": str(conf.count("baixa")),
        "N_PIVOS": str(len(piv)),
        "PIVOS_NOMES": esc(lista_nomes([p["nome"] for p in piv])),
        "N_PEC8_PRESENTES": str(pres["total"]),
        "N_PEC8_SIM": str(len(pres["sim"])),
        "N_PEC8_NAO": str(len(pres["nao"])),
        "N_PEC8_AUSENTES": str(len(pres["ausente"]) + len(pres["presente_sem_voto"])),
    }
    for cenario in CENARIOS:
        b = base(data, cenario)
        sufixo = cenario.upper()
        out[f"ESPERADO_PEC_{sufixo}"] = num(b["pec"]["votos_esperados"])
        out[f"ESPERADO_IMP_{sufixo}"] = num(b["imp"]["votos_esperados"])
        out[f"P49_{sufixo}"] = pct_inteiro(b["pec"]["P49"])
        out[f"P54_{sufixo}"] = pct_inteiro(b["imp"]["P54"])
    return {k: out[k] for k in VALORES}
