"""Regressão ecológica da variação entre turnos (municípios e seções).

Modelo, por unidade i (município ou seção), com tudo dividido pelo eleitorado
médio dos dois turnos (Ē):

    Δvotos_X,i = a_g + b_X·Δcomparecimento_i + c_X·terceira_via_1T,i
                 + d_X·branco_nulo_1T,i + e_X·Δeleitorado_i + erro

para X em Lula, Flávio e branco/nulo, com efeito fixo do grupo g (UF, região,
município ou zona) e pesos Ē. Como Δlula + Δflávio + Δbranco/nulo =
Δcomparecimento + terceira via, os coeficientes somam 1 em b e em c e 0 em d, sem
restrição imposta: b_X é "de cada eleitor a mais na urna, quanto foi para X".
Erro-padrão robusto por agrupamento em UF (CR1). Inferência de agregado para
agregado: não identifica o voto de nenhum eleitor.

As unidades entram como tabela de colunas (``dict`` de ``numpy.ndarray``), para o
censo de seções (meio milhão de linhas) caber na memória. Casos degenerados não
derrubam a conta e ficam registrados no resultado: linha sem eleitorado ou com
valor não finito, grupo de efeito fixo com uma unidade só (não tem variação
interna), coluna sem variação depois do efeito fixo e matriz de posto incompleto
(resolvida por mínimos quadrados com pseudo-inversa, com o posto anotado).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np

DESTINOS_REG = ("L", "F", "BN")
Z95 = 1.959963984540054
NUMERICAS = ("E1", "E2", "C1", "C2", "L1", "L2", "F1", "F2", "T1", "BN1", "BN2")
TEXTO = ("uf", "regiao", "mun", "cd", "nome")
Tabela = dict[str, np.ndarray]


def _mv(a: np.ndarray, x: np.ndarray) -> np.ndarray:
    """Produto matriz-vetor por einsum: o matmul do numpy com o Accelerate do macOS
    emite avisos espúrios de divisão por zero em dados finitos."""
    return np.einsum("ij,j->i", a, x)


def _mm(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.einsum("ij,jk->ik", a, b)


# ------------------------------------------------------------------ tabela


def tabela(unidades: Sequence[Mapping[str, Any]]) -> Tabela:
    """Lista de dicionários vira tabela de colunas."""
    tab: Tabela = {
        k: np.array([u[k] for u in unidades], dtype=float) for k in NUMERICAS
    }
    for k in TEXTO:
        if unidades and k in unidades[0]:
            tab[k] = np.array([str(u[k]) for u in unidades])
    if unidades and "zona" in unidades[0]:
        tab["zona"] = np.array([str(u["zona"]) for u in unidades])
    if unidades and "capital" in unidades[0]:
        tab["capital"] = np.array([bool(u["capital"]) for u in unidades])
    if unidades and "peso_desenho" in unidades[0]:
        tab["peso_desenho"] = np.array(
            [u["peso_desenho"] for u in unidades], dtype=float
        )
    return tab


def filtra(tab: Tabela, mascara: np.ndarray) -> Tabela:
    return {k: v[mascara] for k, v in tab.items()}


def tamanho(tab: Tabela) -> int:
    return len(tab["E1"])


def codigos(tab: Tabela, cols: Sequence[str]) -> np.ndarray:
    """Código inteiro do grupo formado pelas colunas `cols` (UF; UF e município...)."""
    chave = tab[cols[0]].astype(str)
    for c in cols[1:]:
        chave = np.char.add(np.char.add(chave, "|"), tab[c].astype(str))
    return np.unique(chave, return_inverse=True)[1]


def _demean(v: np.ndarray, w: np.ndarray, cod: np.ndarray | None) -> np.ndarray:
    """Tira a média ponderada de cada grupo (transformação within), por bincount."""
    if cod is None:
        return v.astype(float).copy()
    ws = np.bincount(cod, weights=w)
    if v.ndim == 1:
        return v - (np.bincount(cod, weights=w * v) / ws)[cod]
    out = np.empty_like(v, dtype=float)
    for j in range(v.shape[1]):
        out[:, j] = v[:, j] - (np.bincount(cod, weights=w * v[:, j]) / ws)[cod]
    return out


def wls(
    y: np.ndarray,
    X: np.ndarray,
    w: np.ndarray,
    cod: np.ndarray | None,
    cluster: np.ndarray,
    constante: bool = False,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, int]:
    """Mínimos quadrados ponderados com efeito fixo (transformação within).

    Devolve (beta, erro-padrão CR1 por `cluster`, resíduos, posto). Com posto
    incompleto, a solução é a de norma mínima (pseudo-inversa) e o posto volta
    menor que o número de colunas para quem chamou registrar.
    """
    if constante:
        X = np.column_stack([X, np.ones(len(y))])
    yd = _demean(y, w, cod)
    Xd = _demean(X, w, cod)
    sw = np.sqrt(w)
    A = Xd * sw[:, None]
    beta, _res, posto, _sv = np.linalg.lstsq(A, yd * sw, rcond=None)
    e = yd - _mv(Xd, beta)
    inv = np.linalg.pinv(_mm(A.T, A))
    n, k = Xd.shape
    cl = np.unique(cluster, return_inverse=True)[1]
    G = int(cl.max()) + 1
    S = Xd * (w * e)[:, None]
    soma = np.column_stack(
        [np.bincount(cl, weights=S[:, j], minlength=G) for j in range(k)]
    )
    meat = _mm(soma.T, soma)
    ajuste = G / (G - 1) * (n - 1) / (n - k) if G > 1 and n > k else 1.0
    V = _mm(_mm(inv, meat), inv) * ajuste
    return beta, np.sqrt(np.clip(np.diag(V), 0, None)), e, int(posto)


def wls_hc1(
    y: np.ndarray, X: np.ndarray, w: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """WLS com intercepto e erro-padrão robusto HC1 (regressão dentro de uma UF)."""
    X = np.column_stack([X, np.ones(len(y))])
    sw = np.sqrt(w)
    A = X * sw[:, None]
    beta = np.linalg.lstsq(A, y * sw, rcond=None)[0]
    e = y - _mv(X, beta)
    inv = np.linalg.pinv(_mm(A.T, A))
    S = X * (w * e)[:, None]
    meat = _mm(S.T, S)
    n, k = X.shape
    V = _mm(_mm(inv, meat), inv) * n / (n - k)
    return beta, np.sqrt(np.clip(np.diag(V), 0, None))


def _matriz(
    tab: Tabela,
) -> tuple[np.ndarray, np.ndarray, list[str], dict[str, np.ndarray]]:
    eb = (tab["E1"] + tab["E2"]) / 2
    cols = [
        (tab["C2"] - tab["C1"]) / eb,
        tab["T1"] / eb,
        tab["BN1"] / eb,
        (tab["E2"] - tab["E1"]) / eb,
    ]
    nomes = [
        "delta_comparecimento",
        "terceira_via_1t",
        "branco_nulo_1t",
        "delta_eleitorado",
    ]
    ys = {
        "L": (tab["L2"] - tab["L1"]) / eb,
        "F": (tab["F2"] - tab["F1"]) / eb,
        "BN": (tab["BN2"] - tab["BN1"]) / eb,
    }
    return eb, np.column_stack(cols), nomes, ys


def ajusta(
    tab: Tabela,
    grupo: Sequence[str] | None,
    *,
    peso: np.ndarray | None = None,
    peso_igual: bool = False,
    controles_base: bool = False,
    nome: str = "",
) -> dict[str, Any]:
    """Uma especificação: coeficientes de Lula, Flávio e branco/nulo.

    `grupo`: colunas do efeito fixo (None, sem efeito fixo). `peso`: multiplica o
    eleitorado (peso de desenho); `peso_igual`: cada unidade pesa 1.
    """
    excluidas: dict[str, Any] = {}
    n0 = tamanho(tab)
    eb, X, nomes, ys = _matriz(tab)
    if controles_base:
        X = np.column_stack([X, tab["L1"] / eb, tab["F1"] / eb])
        nomes = [*nomes, "lula_1t", "flavio_1t"]
    w = np.ones(n0) if peso_igual else eb * (peso if peso is not None else 1.0)
    ok = (eb > 0) & np.isfinite(w) & (w > 0) & np.all(np.isfinite(X), axis=1)
    for y in ys.values():
        ok &= np.isfinite(y)
    if not ok.all():
        excluidas["sem_eleitorado_ou_nao_finito"] = int((~ok).sum())
    cod = None
    if grupo is not None:
        c0 = codigos(tab, grupo)
        tam = np.bincount(c0[ok], minlength=int(c0.max()) + 1)
        sozinho = ok & (tam[c0] < 2)
        if sozinho.any():
            nomes_g = _rotulos(tab, grupo, sozinho)
            excluidas["grupos_com_uma_unidade"] = {
                "n": len(nomes_g),
                "exemplos": nomes_g[:20],
            }
            ok &= ~sozinho
    X, w = X[ok], w[ok]
    ys = {k: v[ok] for k, v in ys.items()}
    if grupo is not None:
        cod = np.unique(codigos(tab, grupo)[ok], return_inverse=True)[1]
    cl = tab["uf"][ok]
    # Coluna sem variação depois do efeito fixo não identifica nada: sai e é anotada.
    Xd = _demean(X, w, cod)
    var = np.sqrt(np.average(Xd**2, axis=0, weights=w))
    escala = np.maximum(np.sqrt(np.average(X**2, axis=0, weights=w)), 1e-300)
    viva = var > 1e-9 * escala
    if not viva.all():
        excluidas["colunas_sem_variacao"] = [
            n for n, v in zip(nomes, viva, strict=True) if not v
        ]
        if not viva[0]:
            raise ValueError(
                f"{nome}: Δcomparecimento sem variação depois do efeito fixo"
            )
        X = X[:, viva]
        nomes = [n for n, v in zip(nomes, viva, strict=True) if v]
    n, k = X.shape
    if n < k + 2 + (0 if cod is None else int(cod.max()) + 1):
        raise ValueError(
            f"{nome}: {n} unidades para {k} colunas e os grupos do efeito fixo"
        )
    coef: dict[str, dict[str, dict[str, Any]]] = {}
    posto_min = k + (1 if grupo is None else 0)
    for x, y in ys.items():
        beta, ep, _e, posto = wls(y, X, w, cod, cl, constante=grupo is None)
        posto_min = min(posto_min, posto)
        coef[x] = {
            nm: {
                "b": float(beta[j]),
                "ep": float(ep[j]),
                "ic95": [float(beta[j] - Z95 * ep[j]), float(beta[j] + Z95 * ep[j])],
            }
            for j, nm in enumerate(nomes)
        }
    if posto_min < k + (1 if grupo is None else 0):
        excluidas["posto_incompleto"] = posto_min
    soma_b = sum(coef[x]["delta_comparecimento"]["b"] for x in DESTINOS_REG)
    soma_c = sum(coef[x]["terceira_via_1t"]["b"] for x in DESTINOS_REG)
    return {
        "nome": nome,
        "n": int(n),
        "n_entrada": int(n0),
        "n_grupos": 0 if cod is None else int(cod.max()) + 1,
        "coef": coef,
        "conferencia_soma_b": soma_b,
        "conferencia_soma_c": soma_c,
        "excluidas": excluidas,
    }


def _rotulos(tab: Tabela, grupo: Sequence[str], mascara: np.ndarray) -> list[str]:
    partes = [tab[g][mascara].astype(str) for g in grupo]
    chave = partes[0]
    for p in partes[1:]:
        chave = np.char.add(np.char.add(chave, "/"), p)
    return sorted({str(x) for x in chave})


def resumo(esp: dict[str, Any]) -> dict[str, Any]:
    """Linha curta da tabela de robustez: por 100 eleitores a mais."""
    c = esp["coef"]
    b = {x: c[x]["delta_comparecimento"] for x in DESTINOS_REG}
    t = {x: c[x]["terceira_via_1t"] for x in DESTINOS_REG}
    return {
        "nome": esp["nome"],
        "n": esp["n"],
        "lula": 100 * b["L"]["b"],
        "lula_ic95": [100 * v for v in b["L"]["ic95"]],
        "lula_ep": 100 * b["L"]["ep"],
        "flavio": 100 * b["F"]["b"],
        "flavio_ic95": [100 * v for v in b["F"]["ic95"]],
        "branco_nulo": 100 * b["BN"]["b"],
        "lula_entre_validos": 100 * b["L"]["b"] / (b["L"]["b"] + b["F"]["b"]),
        "terceira_lula": 100 * t["L"]["b"],
        "terceira_flavio": 100 * t["F"]["b"],
        "terceira_bn": 100 * t["BN"]["b"],
    }


def municipais(painel: list[dict[str, Any]]) -> dict[str, Any]:
    """Especificação principal e as trocas pedidas (efeito fixo, capitais, controles)."""
    tab = tabela(painel)
    perde = np.isin(tab["uf"], ["AC", "AP", "RR", "AM"])
    tudo = np.ones(tamanho(tab), dtype=bool)
    specs: list[tuple[str, str, np.ndarray, tuple[str, ...] | None, dict[str, Any]]] = [
        ("principal", "Efeito fixo de UF (principal)", tudo, ("uf",), {}),
        ("regiao", "Efeito fixo de região", tudo, ("regiao",), {}),
        ("sem_efeito", "Sem efeito fixo", tudo, None, {}),
        (
            "sem_capitais",
            "Efeito fixo de UF, sem as capitais",
            ~tab["capital"],
            ("uf",),
            {},
        ),
        (
            "controles_base",
            "Efeito fixo de UF + votos de Lula e Flávio no 1º turno",
            tudo,
            ("uf",),
            {"controles_base": True},
        ),
        (
            "sem_abstencao_subindo",
            "Efeito fixo de UF, sem AC, AP, AM e RR (abstenção subiu)",
            ~perde,
            ("uf",),
            {},
        ),
        (
            "grandes",
            "Efeito fixo de UF, municípios com 50 mil eleitores ou mais",
            tab["E2"] >= 50_000,
            ("uf",),
            {},
        ),
        (
            "sem_peso",
            "Efeito fixo de UF, cada município com o mesmo peso",
            tudo,
            ("uf",),
            {"peso_igual": True},
        ),
    ]
    return {
        chave: ajusta(filtra(tab, m), g, nome=nome, **extra)
        for chave, nome, m, g, extra in specs
    }


def secoes(sec: Mapping[str, Any]) -> dict[str, Any]:
    """As mesmas contas entre seções (amostra sorteada ou censo dos BUs)."""
    tab = sec["tabela"]
    peso = tab["peso_desenho"]
    rot = sec.get("rotulo", "Seções")
    uf = ajusta(tab, ("uf",), peso=peso, nome=f"{rot}, efeito fixo de UF")
    mun = ajusta(tab, ("uf", "mun"), peso=peso, nome=f"{rot}, efeito fixo de município")
    zona = ajusta(
        tab, ("uf", "mun", "zona"), peso=peso, nome=f"{rot}, efeito fixo de zona"
    )
    return {
        "uf": uf,
        "municipio": mun,
        "zona": zona,
        "n_municipios_com_duas_ou_mais": mun["n_grupos"],
    }


def por_uf(painel: list[dict[str, Any]], minimo: int = 15) -> list[dict[str, Any]]:
    """Dentro de cada UF, entre os seus municípios (sem efeito fixo, HC1)."""
    tab = tabela(painel)
    out = []
    for uf in sorted(set(tab["uf"].tolist())):
        sub = filtra(tab, tab["uf"] == uf)
        n = tamanho(sub)
        if n < minimo:
            out.append({"uf": uf, "n": n, "motivo": "menos de 15 municípios"})
            continue
        eb, X, _nomes, ys = _matriz(sub)
        res: dict[str, Any] = {"uf": uf, "n": n}
        for x in DESTINOS_REG:
            beta, ep = wls_hc1(ys[x], X, eb)
            res[x] = {
                "b": float(beta[0]),
                "ep": float(ep[0]),
                "ic95": [float(beta[0] - Z95 * ep[0]), float(beta[0] + Z95 * ep[0])],
            }
        res["aptos"] = int(sub["E2"].sum())
        res["delta_comparecimento"] = int((sub["C2"] - sub["C1"]).sum())
        out.append(res)
    return out


def dispersao(painel: list[dict[str, Any]]) -> dict[str, Any]:
    """Pontos da regressão parcial (Frisch-Waugh) de Lula: x e y já sem UF e estoques.

    A reta pela origem com inclinação b reproduz exatamente o coeficiente principal.
    """
    tab = tabela(painel)
    eb, X, _nomes, ys = _matriz(tab)
    cod = codigos(tab, ("uf",))
    outros = X[:, 1:]
    xc = X[:, 0]
    sw = np.sqrt(eb)
    Od = _demean(outros, eb, cod)
    xd = _demean(xc, eb, cod)
    A = Od * sw[:, None]
    rx = xd - _mv(Od, np.linalg.lstsq(A, xd * sw, rcond=None)[0])
    pontos = {}
    for alvo in ("L", "F"):
        yd = _demean(ys[alvo], eb, cod)
        ry = yd - _mv(Od, np.linalg.lstsq(A, yd * sw, rcond=None)[0])
        pontos[alvo] = {
            "y": ry,
            "b": float((eb * rx * ry).sum() / (eb * rx * rx).sum()),
        }
    lim_x = [float(np.percentile(100 * rx, 0.5)), float(np.percentile(100 * rx, 99.5))]
    yl = 100 * pontos["L"]["y"]
    lim_y = [float(np.percentile(yl, 0.5)), float(np.percentile(yl, 99.5))]
    linhas = [
        [
            u["cd"],
            u["uf"],
            u["regiao"],
            round(100 * float(rx[i]), 3),
            round(100 * float(pontos["L"]["y"][i]), 3),
            round(100 * float(pontos["F"]["y"][i]), 3),
            round(float(eb[i])),
            1 if u["capital"] else 0,
            u["nome"],
        ]
        for i, u in enumerate(painel)
    ]
    return {
        "nota": (
            "x e y em pontos do eleitorado médio, depois de descontar o efeito fixo de UF, "
            "a terceira via e o branco/nulo do 1º turno e a variação do eleitorado; "
            "a inclinação pela origem é o coeficiente principal (Frisch-Waugh)"
        ),
        "b_lula": pontos["L"]["b"],
        "b_flavio": pontos["F"]["b"],
        "janela_x_pp": lim_x,
        "janela_y_pp": lim_y,
        "colunas": [
            "cd",
            "uf",
            "regiao",
            "x_pp",
            "y_lula_pp",
            "y_flavio_pp",
            "eleitores",
            "capital",
            "nome",
        ],
        "linhas": linhas,
    }


def contribuicao_fatia(f2: float, l2: float, df: float, dl: float) -> float:
    """Pontos da parte de Flávio entre os dois que somem sem `df` e `dl` votos."""
    real = 100 * f2 / (f2 + l2)
    sem = 100 * (f2 - df) / ((f2 - df) + (l2 - dl))
    return sem - real


def faixa_ic(esp: dict[str, Any]) -> tuple[float, float]:
    c = esp["coef"]["L"]["delta_comparecimento"]
    return c["ic95"][0], c["ic95"][1]
