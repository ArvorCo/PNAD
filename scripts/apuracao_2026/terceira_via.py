"""Aritmética de "Onde está o voto da terceira via, cidade por cidade".

Funções puras, sem banco nem disco: recebem números e dicionários já lidos e
devolvem números e dicionários. ``tests/test_apuracao_2026_terceira_via.py``
exercita tudo o que está aqui com dados pequenos.

Convenções:

- margem sempre Flávio menos Lula, em pontos dos válidos do município;
- "terceira via" = todos os votos válidos de presidente fora de Flávio e Lula;
- a matriz de transferência é nacional (Nexus, 18 a 20/09/2026, p. 79; Datafolha
  para Cury e Caiado) e aplicada a cada município: hipótese declarada, nunca
  medição local;
- "vão local" = votos da candidatura do bloco de Flávio (governador ou Senado)
  que mais rendeu no município menos os votos de Flávio no mesmo município;
- nada aqui descreve eleitor individual. Estoque, vão e teto são contas
  agregadas por território.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence

# Candidaturas de terceira via com nome próprio na decomposição, pelo número.
# As demais (Samara, Hertz Dias, Clariana Barao, Edmilson Costa, Veterinário
# Wilson Grassi, Rui Costa Pimenta) somam-se em "outros", mas cada uma recebe
# a própria linha da matriz na conta de votos esperados.
GRUPO_POR_NUMERO = {14: "renan", 30: "zema", 70: "cury", 55: "caiado"}
GRUPOS = ("renan", "zema", "cury", "caiado", "outros")
# Candidaturas menores de direita (DC e Democrata), somadas a Zema no movimento 8
# do capítulo 14; ficam dentro de "outros" na decomposição.
DIREITA_MENOR = (27, 35)
NUM_FLAVIO = 22
NUM_LULA = 13

# Classes de margem de Flávio sobre Lula no 1º turno, em pontos dos válidos.
FOLGA_PP = 10.0
CLASSES = ("venceu_folga", "venceu_apertado", "perdeu_apertado", "perdeu_folga")
ROTULO_CLASSE = {
    "venceu_folga": "Flávio venceu com folga (10 pontos ou mais)",
    "venceu_apertado": "Flávio venceu por menos de 10 pontos",
    "perdeu_apertado": "Flávio perdeu por menos de 10 pontos",
    "perdeu_folga": "Flávio perdeu com folga (10 pontos ou mais)",
}

# Juízo editorial: pesos das quatro variáveis do fator de conversão. Somam 1.
# O vão local pesa mais porque é a única evidência medida no próprio município de
# que há eleitor que vota na direita e não vota em Flávio; a matriz por nome e o
# ambiente de 2022 vêm em seguida; a margem do 1º turno pesa menos porque repete
# em parte o ambiente de 2022 e porque o pedido é não filtrar pela vitória.
PESOS = {"vao_local": 0.35, "matriz": 0.25, "ambiente_2022": 0.25, "margem": 0.15}
SENSIBILIDADES = {
    "volume": {},
    "vao_local": {"vao_local": 1.0},
    "margem": {"margem": 1.0},
}


def pct(parte: float, total: float) -> float | None:
    """Parcela em pontos percentuais; ``None`` quando o total é zero."""
    return 100.0 * parte / total if total else None


def r2(x: float | None, casas: int = 2) -> float | None:
    return None if x is None else round(x, casas)


def grupo(numero: int) -> str:
    return GRUPO_POR_NUMERO.get(numero, "outros")


def classe_margem(margem_pp: float) -> str:
    """Classe da margem de Flávio: folga é 10 pontos ou mais; zero conta como derrota."""
    if margem_pp >= FOLGA_PP:
        return "venceu_folga"
    if margem_pp > 0:
        return "venceu_apertado"
    if margem_pp > -FOLGA_PP:
        return "perdeu_apertado"
    return "perdeu_folga"


# ---------------------------------------------------------------- matriz


def destinos(
    votos_por_numero: Mapping[int, int],
    linha_por_numero: Mapping[int, str],
    linhas: Mapping[str, Mapping[str, float]],
) -> dict[str, float]:
    """Votos esperados para Flávio, para Lula e fora (branco, nulo, indeciso).

    Só a parte medida de cada linha (hipótese "só o medido" do capítulo 14):
    a parcela que não escolheu nenhum dos dois fica fora do voto válido.
    ``linhas`` já normalizadas (``flavio``, ``lula``, ``fora`` somam 1).
    """
    f = lu = fo = 0.0
    for numero, votos in votos_por_numero.items():
        if numero in (NUM_FLAVIO, NUM_LULA) or not votos:
            continue
        linha = linhas[linha_por_numero[numero]]
        f += votos * linha["flavio"]
        lu += votos * linha["lula"]
        fo += votos * linha["fora"]
    return {"para_flavio": f, "para_lula": lu, "fora": fo, "saldo": f - lu}


# ---------------------------------------------------------------- vão local


def indice(
    cand: float,
    base: float,
    cand_uf: float,
    base_uf: float,
    fl: float,
    vv: float,
    fl_uf: float,
    vv_uf: float,
) -> float | None:
    """Índice dos carregadores da casa: 100 = rende ali o mesmo que Flávio.

    ``100 × (cand/base ÷ cand_uf/base_uf) ÷ (fl/vv ÷ fl_uf/vv_uf)``, cada parcela
    sobre a base do próprio cargo (a fórmula de ``senado_x_flavio.py``).
    """
    if not (base and base_uf and vv and vv_uf and cand_uf and fl_uf):
        return None
    rel_cand = (cand / base) / (cand_uf / base_uf)
    rel_fl = (fl / vv) / (fl_uf / vv_uf)
    if rel_fl <= 0:
        return None
    return 100.0 * rel_cand / rel_fl


def vao_local(votos_bloco: Mapping[str, int], flavio: int) -> tuple[str | None, int]:
    """Candidatura do bloco com mais votos no município e o saldo dela sobre Flávio.

    ``votos_bloco``: nome da candidatura para votos no município. Sem candidatura,
    devolve ``(None, -flavio)``: nenhuma direita local a comparar.
    """
    if not votos_bloco:
        return None, -flavio
    nome, votos = max(votos_bloco.items(), key=lambda kv: (kv[1], kv[0]))
    return nome, votos - flavio


def teto(estoque: int, vao_votos: int) -> int:
    """Teto endereçável local: terceira via mais o vão positivo da direita local.

    As duas parcelas podem contar o mesmo eleitor (quem votou no governador e em
    Cury entra nas duas), por isso é teto, nunca soma de eleitores distintos.
    """
    return estoque + max(0, vao_votos)


# ---------------------------------------------------------------- índice de prioridade


def percentis(valores: Sequence[float | None]) -> list[float]:
    """Posição de cada valor entre os demais, de 0 (menor) a 1 (maior).

    Empates recebem a posição média; valor ausente fica em 0,5 (neutro).
    """
    presentes = sorted((v, i) for i, v in enumerate(valores) if v is not None)
    n = len(presentes)
    saida = [0.5] * len(valores)
    if n == 0:
        return saida
    if n == 1:
        saida[presentes[0][1]] = 0.5
        return saida
    k = 0
    while k < n:
        j = k
        while j + 1 < n and presentes[j + 1][0] == presentes[k][0]:
            j += 1
        posicao = ((k + j) / 2) / (n - 1)
        for m in range(k, j + 1):
            saida[presentes[m][1]] = posicao
        k = j + 1
    return saida


def fator(posicoes: Mapping[str, float], pesos: Mapping[str, float]) -> float:
    """Fator de conversão: média ponderada das posições; sem pesos, vale 1 (só volume)."""
    if not pesos:
        return 1.0
    total = sum(pesos.values())
    return sum(posicoes[k] * w for k, w in pesos.items()) / total


def ranking(
    linhas: Sequence[Mapping], chave_valor: str, n: int, desempate: str = "cd"
) -> list[Mapping]:
    """As ``n`` linhas de maior valor, desempate estável pelo código."""
    return sorted(linhas, key=lambda x: (-x[chave_valor], x[desempate]))[:n]


def sobreposicao(a: Iterable[str], b: Iterable[str]) -> int:
    return len(set(a) & set(b))


# ---------------------------------------------------------------- nulo de 2022


def brancos_nulos_pct(brancos: int, nulos: int, comparecimento: int) -> float | None:
    """Brancos e nulos em pontos percentuais dos votantes."""
    return pct(brancos + nulos, comparecimento)


def regressao_ponderada(
    xs: Sequence[float], ys: Sequence[float], ws: Sequence[float]
) -> dict[str, float | None]:
    """Mínimos quadrados ponderados de y sobre x, com a correlação ponderada."""
    sw = sum(ws)
    if sw <= 0 or len(xs) < 2:
        return {
            "inclinacao": None,
            "intercepto": None,
            "correlacao": None,
            "n": len(xs),
        }
    mx = sum(w * x for x, w in zip(xs, ws, strict=True)) / sw
    my = sum(w * y for y, w in zip(ys, ws, strict=True)) / sw
    sxx = sum(w * (x - mx) ** 2 for x, w in zip(xs, ws, strict=True))
    syy = sum(w * (y - my) ** 2 for y, w in zip(ys, ws, strict=True))
    sxy = sum(w * (x - mx) * (y - my) for x, y, w in zip(xs, ys, ws, strict=True))
    if sxx <= 0:
        return {
            "inclinacao": None,
            "intercepto": None,
            "correlacao": None,
            "n": len(xs),
        }
    b = sxy / sxx
    rho = sxy / math.sqrt(sxx * syy) if syy > 0 else None
    return {"inclinacao": b, "intercepto": my - b * mx, "correlacao": rho, "n": len(xs)}


def taxa_nulo(bn_1t: int, bn_2t: int, terceira_via_1t: int) -> float | None:
    """Brancos e nulos acrescentados no 2º turno por voto de terceira via do 1º.

    Leitura agregada: supõe que o branco e nulo novo saiu da terceira via, o que
    o dado não identifica; serve de ordem de grandeza.
    """
    if terceira_via_1t <= 0:
        return None
    return (bn_2t - bn_1t) / terceira_via_1t


def somar(linhas: Iterable[Mapping], campos: Iterable[str]) -> dict[str, float]:
    campos = list(campos)
    saida = dict.fromkeys(campos, 0)
    for linha in linhas:
        for c in campos:
            saida[c] += linha.get(c) or 0
    return saida


def minimos_quadrados(
    linhas_x: Sequence[Sequence[float]], ys: Sequence[float], ws: Sequence[float]
) -> list[float] | None:
    """Coeficientes de mínimos quadrados ponderados (equações normais, eliminação de Gauss).

    Cada linha de ``linhas_x`` já traz a constante, se houver. Devolve ``None``
    quando o sistema é singular.
    """
    k = len(linhas_x[0])
    a = [[0.0] * (k + 1) for _ in range(k)]
    for x, y, w in zip(linhas_x, ys, ws, strict=True):
        for i in range(k):
            a[i][k] += w * x[i] * y
            for j in range(k):
                a[i][j] += w * x[i] * x[j]
    for c in range(k):
        piv = max(range(c, k), key=lambda r: abs(a[r][c]))
        if abs(a[piv][c]) < 1e-12:
            return None
        a[c], a[piv] = a[piv], a[c]
        for r in range(k):
            if r != c:
                f = a[r][c] / a[c][c]
                a[r] = [vr - f * vc for vr, vc in zip(a[r], a[c], strict=True)]
    return [a[i][k] / a[i][i] for i in range(k)]


def conversao(
    ganho_flavio_lado: int, ganho_lula_lado: int, terceira_via: int
) -> dict[str, float | None]:
    """Ganho de cada lado entre os turnos por voto de terceira via do 1º turno.

    Analogia de 2022: inclui mudança de comparecimento e de branco e nulo, e a
    terceira via era outra (Simone Tebet e Ciro Gomes).
    """
    if terceira_via <= 0:
        return {"direita": None, "lula": None, "saldo": None}
    return {
        "direita": ganho_flavio_lado / terceira_via,
        "lula": ganho_lula_lado / terceira_via,
        "saldo": (ganho_flavio_lado - ganho_lula_lado) / terceira_via,
    }


# ---------------------------------------------------------------- duas réguas


def decompor(
    pv_pesquisa: float, pv_pesquisa_nac: float, pv_urna: float, pv_urna_nac: float
) -> dict[str, float]:
    """Diferença pesquisa menos urna, por voto, em três parcelas que somam exato.

    - ``composicao``: quanto a linha da pesquisa rende ali acima da média do país,
      porque o estoque local tem mais ou menos Renan, Zema, Cury ou Caiado;
    - ``nivel``: a distância entre as duas réguas no país, igual em todo lugar;
    - ``classe``: quanto a urna de 2022 converteu ali abaixo da média do país,
      pela classe de margem do município.
    """
    return {
        "composicao": pv_pesquisa - pv_pesquisa_nac,
        "nivel": pv_pesquisa_nac - pv_urna_nac,
        "classe": pv_urna_nac - pv_urna,
        "total": pv_pesquisa - pv_urna,
    }


def motivo(partes: Mapping[str, float]) -> str:
    """A parcela local que mais pesa na diferença: ``composicao`` ou ``classe``."""
    return (
        "composicao" if abs(partes["composicao"]) >= abs(partes["classe"]) else "classe"
    )


def piso_teto(*valores: float) -> tuple[float, float]:
    return min(valores), max(valores)


def situacao(em_pesquisa: bool, em_urna: bool) -> str:
    """Robusto quando as duas réguas põem o município na lista; senão, qual delas."""
    if em_pesquisa and em_urna:
        return "robusto"
    if em_pesquisa:
        return "so_pesquisa"
    if em_urna:
        return "so_urna"
    return "fora"
