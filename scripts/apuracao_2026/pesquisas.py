"""Pesquisas, previsões da casa e voto útil contra a urna do 1º turno de 2026.

Funções puras, sem leitura de arquivo, para que o teste exercite a aritmética
isolada. Convenção de sinal herdada de ``scripts/predicao-2026-erro-2022.py``:
erro = pesquisa menos urna, em pontos percentuais dos votos válidos; na
diferença Lula menos Flávio, positivo quer dizer que a pesquisa pôs Lula mais
à frente (ou menos atrás) do que a urna.

Nada aqui é medição do eleitor individual. A decomposição do erro em
consolidação da terceira via e resíduo é contabilidade sob hipóteses
declaradas (matriz de transferência do 2º turno aplicada ao 1º turno).
"""

from __future__ import annotations

import math
import statistics
from collections.abc import Callable, Iterable, Mapping, Sequence
from itertools import pairwise

# Categorias que não são voto válido no placar publicado. A regra é a da casa
# (``scripts/predicao_2026/base.py::grouped``): tudo o que não é indeciso nem
# branco/nulo é candidatura, e a soma das candidaturas vira 100.
NAO_ESCOLHA = frozenset(
    {"branco_nulo", "indecisos", "ns_nr", "nenhum", "nao_vai_votar", "nao_sabe"}
)
TERCEIROS = ("cury", "renan_santos", "caiado", "zema")
DEMAIS = "demais"
Z95 = 1.959963984540054


# ---------------------------------------------------------------- válidos


def validos(opcoes: Mapping[str, float]) -> tuple[dict[str, float], dict]:
    """Parcelas dos válidos a partir de um placar sobre o total de entrevistados.

    Remove indecisos e branco/nulo, trunca negativos em zero (a reponderação
    aditiva pode produzir resíduo negativo em candidatura arredondada a zero;
    a casa projeta no simplex e registra a alteração) e renormaliza para 100.
    """
    negativos = sum(-float(v) for v in opcoes.values() if float(v) < 0)
    nomeados = {
        k: max(0.0, float(v)) for k, v in opcoes.items() if k not in NAO_ESCOLHA
    }
    if not {"lula", "flavio"} <= nomeados.keys():
        raise ValueError("Placar sem Lula e Flávio")
    soma = sum(nomeados.values())
    if soma <= 0:
        raise ValueError("Placar sem voto válido")
    return {k: 100 * v / soma for k, v in nomeados.items()}, {
        "soma_candidaturas_pct_total": soma,
        "nao_escolha_pct_total": sum(
            max(0.0, float(v)) for k, v in opcoes.items() if k in NAO_ESCOLHA
        ),
        "negativos_truncados_pp": negativos,
    }


def blocos(v: Mapping[str, float]) -> dict[str, float]:
    """Flávio, Lula e terceira via (todo o resto dos válidos)."""
    return {
        "flavio": v["flavio"],
        "lula": v["lula"],
        "terceira_via": 100 - v["flavio"] - v["lula"],
    }


def quebra_terceiros(
    v: Mapping[str, float], terceiros: Sequence[str] = TERCEIROS
) -> dict[str, float] | None:
    """Terceiros nomeados mais o grupo ``demais``; None se algum não foi aberto.

    Uma candidatura ausente do placar não vira zero: quando o instituto agrupa
    nomes em ``outros``, a quebra por candidato não existe naquela onda.
    """
    if any(k not in v for k in terceiros):
        return None
    out = {k: v[k] for k in terceiros}
    out[DEMAIS] = 100 - v["flavio"] - v["lula"] - sum(out.values())
    return out


def vetor_terceiros(v: dict) -> dict | None:
    q = quebra_terceiros(v)
    if q is None:
        return None
    return {"flavio": v["flavio"], "lula": v["lula"], **q}


def media_vetores(vetores: list[dict]) -> dict:
    chaves = set.intersection(*(set(v) for v in vetores))
    return {k: statistics.fmean(v[k] for v in vetores) for k in sorted(chaves)}


# ---------------------------------------------------------------- erros


def erros_vs_urna(
    pesquisa: Mapping[str, float],
    urna: Mapping[str, float],
    candidatos_eam: Sequence[str],
) -> dict:
    """Erro por candidatura, na diferença L−F e erro absoluto médio (EAM).

    O EAM usa só ``candidatos_eam`` e fica None quando o placar não abre um
    deles. O EAM por blocos (Flávio, Lula, terceira via) existe sempre.
    """
    erros = {k: pesquisa[k] - urna[k] for k in urna if k in pesquisa}
    dif_p = pesquisa["lula"] - pesquisa["flavio"]
    dif_u = urna["lula"] - urna["flavio"]
    bp, bu = blocos(pesquisa), blocos(urna)
    erro_blocos = {k: bp[k] - bu[k] for k in bp}
    eam = (
        statistics.fmean(abs(erros[k]) for k in candidatos_eam)
        if all(k in erros for k in candidatos_eam)
        else None
    )
    return {
        "erro_pp": erros,
        "erro_blocos_pp": erro_blocos,
        "diferenca_lula_menos_flavio": {
            "pesquisa": dif_p,
            "urna": dif_u,
            "erro": dif_p - dif_u,
        },
        "eam_candidatos_pp": eam,
        "eam_blocos_pp": statistics.fmean(abs(e) for e in erro_blocos.values()),
    }


def margem_diferenca_aas(
    n: float, fracao_validos: float, lula: float, flavio: float
) -> float:
    """Margem de 95% da diferença L−F nos válidos sob amostragem simples.

    ``n`` é o total de entrevistas e ``fracao_validos`` a parte delas com
    candidatura (0 a 1). Ignora ponderação, desenho e arredondamento, então é
    piso da incerteza, não intervalo da casa. Mesma fórmula do erro de 2022.
    """
    n_ef = n * min(max(fracao_validos, 0.0), 1.0)
    if n_ef <= 0:
        raise ValueError("Amostra efetiva nula")
    pl, pf = lula / 100, flavio / 100
    var = (pl + pf - (pl - pf) ** 2) / n_ef
    return 100 * Z95 * math.sqrt(var)


def ordenar_por_erro(
    linhas: Iterable[dict], chave: Callable[[dict], float | None]
) -> list:
    """Ordena por |erro| crescente; linhas sem valor vão para o fim, estáveis."""
    lista = list(linhas)
    com = [x for x in lista if chave(x) is not None]
    sem = [x for x in lista if chave(x) is None]
    com.sort(key=lambda x: (abs(chave(x)), x.get("id", "")))
    return com + sem


def resumo_erros(valores: Sequence[float]) -> dict:
    """Média (erro comum), mediana, desvio entre casas e contagem por sinal."""
    vals = list(valores)
    return {
        "n": len(vals),
        "media": statistics.fmean(vals),
        "mediana": statistics.median(vals),
        "desvio_padrao": statistics.stdev(vals) if len(vals) > 1 else None,
        "media_absoluta": statistics.fmean(abs(v) for v in vals),
        "positivos": sum(v > 0 for v in vals),
        "negativos": sum(v < 0 for v in vals),
    }


def prob_alguma_perto_de_zero(
    media: float, desvio: float, n: int, raio: float
) -> float:
    """P(ao menos um de n erros normais independentes cair em [−raio, raio])."""
    if desvio <= 0 or n < 1:
        raise ValueError("Desvio e n precisam ser positivos")

    def phi(z: float) -> float:
        return 0.5 * (1 + math.erf(z / math.sqrt(2)))

    p1 = phi((raio - media) / desvio) - phi((-raio - media) / desvio)
    return 1 - (1 - p1) ** n


def percentil_histograma(
    valor: float, contagens: Sequence[float], limites: Sequence[float]
) -> float:
    """Fração (0 a 1) dos sorteios abaixo de ``valor``, por interpolação linear."""
    if len(limites) != len(contagens) + 1:
        raise ValueError("Histograma com limites incompatíveis")
    total = float(sum(contagens))
    if total <= 0:
        raise ValueError("Histograma vazio")
    acumulado = 0.0
    for c, lo, hi in zip(contagens, limites[:-1], limites[1:], strict=True):
        if valor >= hi:
            acumulado += c
            continue
        if valor > lo:
            acumulado += c * (valor - lo) / (hi - lo)
        break
    return acumulado / total


def brier(pares: Iterable[tuple[float, int]]) -> float:
    """Escore de Brier: média de (p − o)², o em {0, 1}."""
    lista = [(float(p), int(o)) for p, o in pares]
    if not lista:
        raise ValueError("Sem pares para o Brier")
    return statistics.fmean((p - o) ** 2 for p, o in lista)


def calibracao_por_faixa(
    pares: Iterable[tuple[float, int]], cortes: Sequence[float]
) -> list[dict]:
    """Probabilidade média e frequência observada em faixas de probabilidade."""
    lista = [(float(p), int(o)) for p, o in pares]
    out = []
    for lo, hi in pairwise(cortes):
        fatia = [
            (p, o) for p, o in lista if lo <= p < hi or (hi == cortes[-1] and p == hi)
        ]
        out.append(
            {
                "faixa": [lo, hi],
                "n": len(fatia),
                "p_media": statistics.fmean(p for p, _ in fatia) if fatia else None,
                "frequencia": statistics.fmean(o for _, o in fatia) if fatia else None,
                "esperados": sum(p for p, _ in fatia),
                "observados": sum(o for _, o in fatia),
            }
        )
    return out


# ---------------------------------------------------------------- consolidação


def partilha(
    linha: Mapping[str, float],
    modo: str,
    flavio_pesquisa: float | None = None,
    lula_pesquisa: float | None = None,
) -> tuple[float, float]:
    """Parcela de cada ponto perdido por uma candidatura que vai a Flávio e a Lula.

    ``linha`` é o 2º turno do eleitorado da candidatura (Flávio, Lula, branco e
    nulo, indecisos), como a Nexus publica. Dois modos, ambos somando 1:

    - ``renormalizada``: quem sai da terceira via e continua votando vai a um
      dos dois na razão Flávio:Lula da linha;
    - ``com_vazamento``: a parte que iria a branco, nulo ou indeciso sai dos
      válidos, e em parcelas dos válidos isso equivale a repartir esse pedaço na
      proporção Flávio:Lula da própria pesquisa.
    """
    f, lu = float(linha["Flávio"]), float(linha["Lula"])
    if f + lu <= 0:
        raise ValueError("Linha sem Flávio nem Lula")
    if modo == "renormalizada":
        return f / (f + lu), lu / (f + lu)
    if modo == "com_vazamento":
        if flavio_pesquisa is None or lula_pesquisa is None:
            raise ValueError("Modo com vazamento precisa do placar da pesquisa")
        total = sum(float(v) for v in linha.values())
        resto = (total - f - lu) / total
        razao_f = flavio_pesquisa / (flavio_pesquisa + lula_pesquisa)
        sf = f / total + resto * razao_f
        return sf, 1 - sf
    raise ValueError(f"Modo desconhecido: {modo}")


def decompor_consolidacao(
    pesquisa: Mapping[str, float],
    urna: Mapping[str, float],
    partilhas: Mapping[str, tuple[float, float]],
) -> dict:
    """Separa o erro da pesquisa em consolidação da terceira via e resíduo.

    Em parcelas dos válidos, o que a terceira via perdeu entre a pesquisa e a
    urna (Δ_c = pesquisa − urna, por candidatura c) reaparece em Flávio e Lula.
    Com a partilha (s_F, s_L) de cada c, a consolidação explica
    E_F = Σ Δ_c s_F e E_L = Σ Δ_c s_L. Como as parcelas somam 100 dos dois
    lados, E_F + E_L = G_F + G_L, com G = urna − pesquisa. O resíduo
    R = G_F − E_F = −(G_L − E_L) é o deslocamento relativo entre os dois
    finalistas que a consolidação não explica: efeito de casa, movimento de
    última hora, comparecimento diferencial ou tudo junto.

    ``partilhas`` precisa cobrir toda candidatura que não é Flávio nem Lula,
    inclusive ``demais`` quando ele existir nos dois placares.
    """
    terceiros = [k for k in pesquisa if k not in ("flavio", "lula")]
    if set(terceiros) != {k for k in urna if k not in ("flavio", "lula")}:
        raise ValueError("Pesquisa e urna com terceiros diferentes")
    faltam = [k for k in terceiros if k not in partilhas]
    if faltam:
        raise ValueError(f"Sem partilha para {faltam}")
    delta = {k: pesquisa[k] - urna[k] for k in terceiros}
    e_f = sum(delta[k] * partilhas[k][0] for k in terceiros)
    e_l = sum(delta[k] * partilhas[k][1] for k in terceiros)
    g_f = urna["flavio"] - pesquisa["flavio"]
    g_l = urna["lula"] - pesquisa["lula"]
    erro_dif = g_f - g_l
    explicado = e_f - e_l
    return {
        "queda_terceiros_pp": delta,
        "queda_terceira_via_pp": sum(delta.values()),
        "ganho_flavio_pp": g_f,
        "ganho_lula_pp": g_l,
        "explicado_flavio_pp": e_f,
        "explicado_lula_pp": e_l,
        "residuo_flavio_pp": g_f - e_f,
        "residuo_lula_pp": g_l - e_l,
        "erro_diferenca_lula_menos_flavio_pp": erro_dif,
        "explicado_diferenca_pp": explicado,
        "residuo_diferenca_pp": erro_dif - explicado,
        "fracao_explicada_diferenca": explicado / erro_dif if erro_dif else None,
    }


# ---------------------------------------------------------------- reserva


def resolver_reserva(
    entrada: Mapping[str, float], flavio_urna: float, lula_urna: float
) -> dict:
    """Quanto de cada reserva de 2º turno a urna revelou no 1º turno.

    Usa a contabilidade de ``scripts/voto_util_modelo.py::cenario``: Flávio
    ganha a, Lula ganha b (pontos dos entrevistados); a terceira via perde
    fT_F·a + fT_L·b e o resto entra nos válidos vindo de indecisos e branco/nulo.
    Resolve exatamente o sistema linear que leva as parcelas dos válidos de
    Flávio e Lula às da urna. λ = a / reserva de Flávio e θ = b / reserva de Lula;
    valores fora de [0, 1] dizem que a urna andou além da reserva medida ou na
    direção contrária. ``entrada`` traz F, L, T, F2, L2, fT_flavio e fT_lula.
    """
    f, lu = flavio_urna / 100, lula_urna / 100
    f1, l1, t1 = entrada["F"], entrada["L"], entrada["T"]
    ftf, ftl = entrada["fT_flavio"], entrada["fT_lula"]
    v0 = f1 + l1 + t1
    a11, a12 = 1 - f * (1 - ftf), -f * (1 - ftl)
    a21, a22 = -lu * (1 - ftf), 1 - lu * (1 - ftl)
    r1, r2 = f * v0 - f1, lu * v0 - l1
    det = a11 * a22 - a12 * a21
    a = (r1 * a22 - a12 * r2) / det
    b = (a11 * r2 - a21 * r1) / det
    res_f = max(0.0, entrada["F2"] - f1)
    res_l = max(0.0, entrada["L2"] - l1)
    terceira = t1 - ftf * a - ftl * b
    return {
        "ganho_flavio_pp_entrevistados": a,
        "ganho_lula_pp_entrevistados": b,
        "reserva_flavio_pp": res_f,
        "reserva_lula_pp": res_l,
        "lambda_flavio": a / res_f if res_f > 0 else None,
        "theta_lula": b / res_l if res_l > 0 else None,
        "terceira_via_restante_pp": terceira,
        "consistente": terceira >= 0,
    }


def fracao_terceira(
    transferencia: Mapping[str, float], grupos: Mapping[str, float]
) -> tuple[float, float]:
    """Parcela da reserva de cada lado que sai da terceira via.

    Mesma regra de ``scripts/voto-util-092026-data.py::fracao_terceira``: as
    taxas nacionais de transferência (terceira via, indecisos, branco/nulo)
    aplicadas à composição do placar.
    """
    t = transferencia
    sf = (
        t["terceira_flavio"] * grupos["T"]
        + t["indecisos_flavio"] * grupos["I"]
        + t["branco_flavio"] * grupos["B"]
    )
    sl = (
        t["terceira_lula"] * grupos["T"]
        + t["indecisos_lula"] * grupos["I"]
        + t["branco_lula"] * grupos["B"]
    )
    return (
        t["terceira_flavio"] * grupos["T"] / sf if sf else 0.5,
        t["terceira_lula"] * grupos["T"] / sl if sl else 0.5,
    )


def resolver_2d(
    funcao: Callable[[float, float], tuple[float, float]],
    alvo: tuple[float, float],
    inicio: tuple[float, float] = (0.5, 0.0),
    passo: float = 1e-4,
    tolerancia: float = 1e-9,
    iteracoes: int = 60,
) -> tuple[float, float]:
    """Newton com jacobiano por diferenças finitas para duas equações."""
    x, y = inicio
    for _ in range(iteracoes):
        f0 = funcao(x, y)
        r = (f0[0] - alvo[0], f0[1] - alvo[1])
        if max(abs(r[0]), abs(r[1])) < tolerancia:
            return x, y
        fx, fy = funcao(x + passo, y), funcao(x, y + passo)
        j11, j21 = (fx[0] - f0[0]) / passo, (fx[1] - f0[1]) / passo
        j12, j22 = (fy[0] - f0[0]) / passo, (fy[1] - f0[1]) / passo
        det = j11 * j22 - j12 * j21
        if abs(det) < 1e-14:
            raise ValueError("Jacobiano singular")
        x -= (r[0] * j22 - j12 * r[1]) / det
        y -= (j11 * r[1] - j21 * r[0]) / det
    raise ValueError("Newton não convergiu")


def interpolar_curva(curva: Sequence[Mapping[str, float]], campo: str, alvo: float):
    """Primeiro λ da curva em que ``campo`` cruza ``alvo``; None se não cruza."""
    for p, q in pairwise(curva):
        a, b = p[campo], q[campo]
        if (a - alvo) * (b - alvo) <= 0 and a != b:
            return p["lam"] + (alvo - a) * (q["lam"] - p["lam"]) / (b - a)
    return None
