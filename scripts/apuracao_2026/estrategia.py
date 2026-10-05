"""Aritmética do capítulo "O caminho do 2º turno" (apuração de 04/10/2026).

Funções puras, sem leitura de arquivo nem de banco: recebem dicionários já
lidos por ``estrategia_leitura.py`` e devolvem dicionários prontos para o JSON.
O teste ``tests/test_apuracao_2026_estrategia.py`` exercita esta aritmética.

Convenções:
- votos em número inteiro de votos; parcelas em fração (0 a 1) nas contas e em
  pontos percentuais (0 a 100) no JSON, com o sufixo ``_pct`` ou ``_pp``;
- margem sempre Flávio menos Lula: positiva favorece Flávio;
- parcela dos válidos do próprio cargo e do próprio turno;
- nada aqui descreve eleitor individual. Matriz de transferência, estoque e
  vão são contas agregadas sob hipótese declarada, nunca percurso de pessoas.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

NORDESTE = frozenset({"MA", "PI", "CE", "RN", "PB", "PE", "AL", "SE", "BA"})
NORTE = frozenset({"AC", "AM", "AP", "PA", "RO", "RR", "TO"})
REGIOES = ("Nordeste", "Norte", "Centro-Sul")

HIPOTESES = {
    "fica_fora": (
        "Só o medido: a parcela da linha que não escolhe Lula nem Flávio "
        "(branco, nulo e indecisos) não vira voto válido no 2º turno."
    ),
    "proporcional": (
        "A parcela sem escolha vota na mesma proporção Flávio:Lula que a "
        "própria linha mediu."
    ),
    "meio_a_meio": ("A parcela sem escolha divide-se meio a meio entre Flávio e Lula."),
}


def regiao_de(uf: str) -> str:
    """Nordeste, Norte ou Centro-Sul (Sudeste, Sul e Centro-Oeste com o DF)."""
    uf = uf.upper()
    if uf == "ZZ":
        return "Exterior"
    if uf in NORDESTE:
        return "Nordeste"
    if uf in NORTE:
        return "Norte"
    return "Centro-Sul"


def pct(parte: float, total: float) -> float:
    """Parcela em pontos percentuais; zero quando o total é zero."""
    return 100.0 * parte / total if total else 0.0


def r2(x: float) -> float:
    return round(x, 2)


# ---------------------------------------------------------------- transferência


def normalizar_linha(linha: Mapping[str, float]) -> dict[str, float]:
    """Linha publicada de uma matriz de transferência em frações que somam 1.

    A linha traz ``Lula``, ``Flávio`` e as demais colunas (branco/nulo,
    indecisos, não escolha). Arredondamento do instituto faz a linha somar 99
    ou 101; dividimos tudo pela soma, para que a linha reparta exatamente o
    eleitorado de origem.
    """
    total = float(sum(linha.values()))
    if total <= 0:
        raise ValueError("linha de transferência sem massa")
    lula = linha.get("Lula", 0.0) / total
    flavio = linha.get("Flávio", 0.0) / total
    return {"flavio": flavio, "lula": lula, "fora": 1.0 - flavio - lula}


def destino(linha: Mapping[str, float], hipotese: str) -> tuple[float, float]:
    """Frações do eleitorado de origem que votam Flávio e Lula no 2º turno.

    ``linha`` já normalizada (``flavio``, ``lula``, ``fora``).
    """
    f, lu, fora = linha["flavio"], linha["lula"], linha["fora"]
    if hipotese == "fica_fora":
        return f, lu
    if hipotese == "proporcional":
        escolha = f + lu
        if escolha <= 0:
            return f + fora / 2, lu + fora / 2
        return f + fora * f / escolha, lu + fora * lu / escolha
    if hipotese == "meio_a_meio":
        return f + fora / 2, lu + fora / 2
    raise ValueError(f"hipótese desconhecida: {hipotese}")


def projetar(
    flavio_1t: int,
    lula_1t: int,
    origens: Mapping[str, int],
    linhas: Mapping[str, Mapping[str, float]],
    hipotese: str,
) -> dict:
    """Placar do 2º turno somando às bases do 1º turno o que cada origem entrega.

    Hipóteses fixas da conta, declaradas no texto: as bases de Flávio e de Lula
    no 1º turno ficam onde estão; branco, nulo e abstenção do 1º turno não
    entram; o comparecimento não muda.
    """
    ganho_f = ganho_l = 0.0
    detalhe = []
    for nome, votos in origens.items():
        df, dl = destino(linhas[nome], hipotese)
        ganho_f += votos * df
        ganho_l += votos * dl
        detalhe.append(
            {
                "origem": nome,
                "votos_1t": votos,
                "para_flavio": round(votos * df),
                "para_lula": round(votos * dl),
                "fora": round(votos * (1 - df - dl)),
                "saldo_flavio": round(votos * (df - dl)),
            }
        )
    flavio = flavio_1t + ganho_f
    lula = lula_1t + ganho_l
    validos = flavio + lula
    return {
        "hipotese": hipotese,
        "flavio": round(flavio),
        "lula": round(lula),
        "validos": round(validos),
        "flavio_pct": r2(pct(flavio, validos)),
        "lula_pct": r2(pct(lula, validos)),
        "margem_votos": round(flavio - lula),
        "margem_pp": r2(pct(flavio - lula, validos)),
        "ganho_flavio": round(ganho_f),
        "ganho_lula": round(ganho_l),
        "detalhe": detalhe,
    }


def equilibrio(diferenca: float, reserva: float) -> float | None:
    """Fração de uma reserva de votos válidos novos que Lula precisa para empatar.

    Se ``reserva`` votos novos entram e Lula leva a fração x, a margem de
    Flávio vira ``diferenca - x*reserva + (1-x)*reserva``; zera em
    x = (1 + diferenca/reserva) / 2. Acima de 1 é inalcançável só com ela.
    """
    if reserva <= 0:
        return None
    return (1.0 + diferenca / reserva) / 2.0


def eleitores_novos_para_empatar(margem: float, parcela_lula: float) -> float | None:
    """Quantos eleitores novos, votando ``parcela_lula`` em Lula, zeram a margem."""
    saldo = 2.0 * parcela_lula - 1.0
    if saldo <= 0:
        return None
    return margem / saldo


def analogo_2022(
    flavio_1t: float,
    lula_1t: float,
    terceiros_2026: float,
    b22: Mapping[str, float],
) -> dict:
    """Aplica a 2026 o que o 2º turno de 2022 acrescentou a cada lado.

    Taxas de 2022: ganho de Bolsonaro e de Lula entre turnos divididos pelo
    voto de terceira via do 1º turno de 2022 (``b22`` com ``bolsonaro_1t``,
    ``bolsonaro_2t``, ``lula_1t``, ``lula_2t``, ``terceiros_1t``). Os ganhos
    incluem mudança de comparecimento e de branco/nulo; é analogia
    histórica, não matriz de transferência.
    """
    base = b22["terceiros_1t"]
    if base <= 0:
        return {
            "taxa_flavio": 0.0,
            "taxa_lula": 0.0,
            "flavio": flavio_1t,
            "lula": lula_1t,
        }
    tb = (b22["bolsonaro_2t"] - b22["bolsonaro_1t"]) / base
    tl = (b22["lula_2t"] - b22["lula_1t"]) / base
    return {
        "taxa_flavio": tb,
        "taxa_lula": tl,
        "flavio": flavio_1t + tb * terceiros_2026,
        "lula": lula_1t + tl * terceiros_2026,
    }


# ---------------------------------------------------------------- estoque e geografia


def estoque(votos_ref: float, parcela_ref: float, parcela_atual: float) -> float:
    """Estoque aritmético: votos de referência ainda não alcançados.

    ``votos_ref * max(0, 1 - parcela_atual / parcela_ref)``. Com Bolsonaro no
    2º turno de 2022 como referência: quantos votos de Bolsonaro, na mesma
    proporção do eleitorado válido, Flávio ainda não tem. Onde Flávio já passou
    de Bolsonaro, o estoque é zero (o excedente não abate outro lugar).
    """
    if parcela_ref <= 0:
        return 0.0
    return votos_ref * max(0.0, 1.0 - parcela_atual / parcela_ref)


def saldo_comparecimento(
    eleitores: float,
    pontos: float,
    validos_por_comparecimento: float,
    parcela_flavio: float,
    parcela_lula: float,
) -> float:
    """Saldo Flávio menos Lula de ``pontos`` adicionais de comparecimento.

    Hipótese declarada: o eleitor adicional vota como a UF votou no 1º turno
    (parcelas dos válidos) e anula ou vota em branco na mesma proporção.
    """
    novos = eleitores * pontos / 100.0
    return novos * validos_por_comparecimento * (parcela_flavio - parcela_lula)


def somar(linhas: Iterable[Mapping[str, float]], campos: Iterable[str]) -> dict:
    """Soma campos numéricos de várias linhas."""
    campos = tuple(campos)
    saida: dict[str, float] = dict.fromkeys(campos, 0)
    for linha in linhas:
        for c in campos:
            saida[c] += linha.get(c, 0) or 0
    return saida


def comparar_uf(uf: str, a26: Mapping, b22_1t: Mapping, b22_2t: Mapping) -> dict:
    """Linha de comparação 2026 × 2022 de uma UF (ou agregado).

    ``a26``: ``flavio``, ``lula``, ``validos``, ``eleitores``,
    ``comparecimento``; ``b22_*``: saída de ``ler_api_2022`` (ou soma).
    """
    f, lu, vv = a26["flavio"], a26["lula"], a26["validos"]
    fp, lp = pct(f, vv), pct(lu, vv)
    b1p = pct(b22_1t["bolsonaro"], b22_1t["validos"])
    l1p = pct(b22_1t["lula"], b22_1t["validos"])
    b2p = pct(b22_2t["bolsonaro"], b22_2t["validos"])
    l2p = pct(b22_2t["lula"], b22_2t["validos"])
    return {
        "uf": uf,
        "regiao": regiao_de(uf) if len(uf) == 2 else uf,
        "eleitores_2026": a26["eleitores"],
        "comparecimento_2026_pct": r2(pct(a26["comparecimento"], a26["eleitores"])),
        "comparecimento_2022_1t_pct": r2(
            pct(b22_1t["comparecimento"], b22_1t["eleitores"])
        ),
        "comparecimento_2022_2t_pct": r2(
            pct(b22_2t["comparecimento"], b22_2t["eleitores"])
        ),
        "validos_2026": vv,
        "flavio": f,
        "flavio_pct": r2(fp),
        "lula": lu,
        "lula_pct": r2(lp),
        "terceiros": vv - f - lu,
        "terceiros_pct": r2(pct(vv - f - lu, vv)),
        "margem_votos": f - lu,
        "margem_pp": r2(fp - lp),
        "bolsonaro_2022_1t": b22_1t["bolsonaro"],
        "bolsonaro_2022_1t_pct": r2(b1p),
        "bolsonaro_2022_2t": b22_2t["bolsonaro"],
        "bolsonaro_2022_2t_pct": r2(b2p),
        "lula_2022_1t": b22_1t["lula"],
        "lula_2022_1t_pct": r2(l1p),
        "lula_2022_2t": b22_2t["lula"],
        "lula_2022_2t_pct": r2(l2p),
        "flavio_menos_bolsonaro_1t_pp": r2(fp - b1p),
        "flavio_menos_bolsonaro_2t_pp": r2(fp - b2p),
        "flavio_menos_bolsonaro_2t_votos": f - b22_2t["bolsonaro"],
        "lula_menos_lula_2022_1t_pp": r2(lp - l1p),
        "lula_menos_lula_2022_1t_votos": lu - b22_1t["lula"],
        "lula_menos_lula_2022_2t_pp": r2(lp - l2p),
        "ja_supera_bolsonaro_2t": fp >= b2p,
        "estoque_flavio": round(estoque(b22_2t["bolsonaro"], b2p, fp)),
        "estoque_lula": round(estoque(b22_2t["lula"], l2p, lp)),
        "deficit_votos_flavio": max(0, b22_2t["bolsonaro"] - f),
    }


def variacao_comparecimento_2022(t1: Mapping, t2: Mapping) -> dict:
    """Mudança de comparecimento do 1º para o 2º turno de 2022 (mesmo eleitorado)."""
    return {
        "comparecimento_1t": t1["comparecimento"],
        "comparecimento_2t": t2["comparecimento"],
        "variacao_votos": t2["comparecimento"] - t1["comparecimento"],
        "variacao_pp": r2(
            pct(t2["comparecimento"], t2["eleitores"])
            - pct(t1["comparecimento"], t1["eleitores"])
        ),
        "ganho_bolsonaro": t2["bolsonaro"] - t1["bolsonaro"],
        "ganho_lula": t2["lula"] - t1["lula"],
    }


def correlacao(xs: list[float], ys: list[float]) -> float | None:
    """Correlação de Pearson; ``None`` com menos de três pontos ou variância zero."""
    n = len(xs)
    if n < 3 or n != len(ys):
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return None
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True))
    return sxy / (sxx * syy) ** 0.5


# ---------------------------------------------------------------- governadores


def vao(gov_votos: int, gov_validos: int, flavio_votos: int, pres_validos: int) -> dict:
    """Vão estadual em pontos e em votos (governador menos Flávio, mesma urna).

    Em votos é a diferença bruta, porque o eleitor é o mesmo e os válidos dos
    dois cargos diferem pouco; em pontos, cada um sobre os válidos do seu cargo.
    """
    return {
        "vao_pp": r2(pct(gov_votos, gov_validos) - pct(flavio_votos, pres_validos)),
        "vao_votos": gov_votos - flavio_votos,
    }


def consolidacao_entre_turnos(
    linha_1t: Mapping[str, float], linha_2t: Mapping[str, float]
) -> float:
    """Saldo líquido para Flávio entre as perguntas de 1º e 2º turno, em fração.

    Mesma amostra, mesmo eleitorado de origem: (F2 - F1) - (L2 - L1), em
    pontos do eleitorado de origem divididos por 100.
    """
    df = linha_2t["Flávio"] - linha_1t["Flávio"]
    dl = linha_2t["Lula"] - linha_1t["Lula"]
    return (df - dl) / 100.0


def ordenar_movimentos(movimentos: list[dict]) -> list[dict]:
    """Ordena por votos esperados (saldo líquido para Flávio), do maior ao menor."""
    ordenados = sorted(movimentos, key=lambda m: -m["votos_esperados"])
    for i, m in enumerate(ordenados, start=1):
        m["ordem"] = i
    return ordenados


def milhar(n: float) -> str:
    """Inteiro com ponto de milhar, como se escreve em português."""
    return f"{round(n):,}".replace(",", ".")


def maioria_absoluta(cadeiras: int) -> int:
    """Primeiro inteiro acima da metade das cadeiras (257 de 513, 41 de 81)."""
    return cadeiras // 2 + 1


def tres_quintos(cadeiras: int) -> int:
    """Menor número de cadeiras que alcança três quintos (308 de 513, 49 de 81)."""
    return -(-3 * cadeiras // 5)
