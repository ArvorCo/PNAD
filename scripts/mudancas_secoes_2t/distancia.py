"""Distância entre o local antigo e o novo, e a referência do prédio vizinho.

A distância é a haversine entre a coordenada do cadastro do 1º turno e a do 2º, na
mesma seção. Fica fora das estatísticas quando passa de 50 km (coordenada suspeita) ou
quando um dos lados é coordenada repetida por três ou mais locais do município
(marcador de posição). Os IC das medianas reamostram pares de locais (conglomerados),
porque todas as seções de um mesmo par têm a mesma distância.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote_plus

import numpy as np
import pandas as pd
from mudancas_secoes_2t import endereco as en
from mudancas_secoes_2t import estatistica as es

FAIXAS = [
    (0, 300, "até 300 m"),
    (300, 500, "300 a 500 m"),
    (500, 1000, "500 m a 1 km"),
    (1000, 2000, "1 a 2 km"),
    (2000, 5000, "2 a 5 km"),
    (5000, 20000, "5 a 20 km"),
    (20000, 50000, "20 a 50 km"),
]
GRUPOS_CATEGORIA = {"A": ["A"], "B": ["B"], "C": ["C"], "D/E/G": ["D", "E", "G", "X"]}
VIZINHO_MIN_M = 1.0
REGRA = (
    "Haversine entre a coordenada do cadastro do 1º turno e a do 2º, na mesma seção. "
    "Fora das estatísticas quando passa de 50 km (coordenada suspeita) ou quando um dos "
    "lados é coordenada repetida por três ou mais locais do município (marcador de "
    "posição). Linha reta, não o caminho a pé."
)


def _coord(lat: Any, lon: Any) -> str | None:
    if lat is None or lon is None or pd.isna(lat) or pd.isna(lon):
        return None
    return f"{float(lat):.6f},{float(lon):.6f}"


def maps_novo(lat: Any, lon: Any, consulta: str) -> str:
    c = _coord(lat, lon)
    q = c or quote_plus(consulta)
    return f"https://www.google.com/maps/search/?api=1&query={q}"


def maps_rota(lat1: Any, lon1: Any, lat2: Any, lon2: Any) -> str | None:
    a, b = _coord(lat1, lon1), _coord(lat2, lon2)
    if not a or not b:
        return None
    return (
        "https://www.google.com/maps/dir/?api=1"
        f"&origin={a}&destination={b}&travelmode=walking"
    )


def distancia_valida(df: pd.DataFrame) -> pd.Series:
    """Distância usável nas estatísticas: existe, até 50 km e sem coordenada repetida."""
    d = df["distancia_m"]
    return (
        d.notna()
        & ~df["distancia_suspeita"].astype(bool)
        & ~df["coord_repetida"].astype(bool)
    )


def _faixa(d: float) -> str:
    for lo, hi, nome in FAIXAS:
        if lo <= d < hi:
            return nome
    return FAIXAS[-1][2]


def histograma(secoes: pd.DataFrame) -> dict[str, Any]:
    """Seções e eleitores por faixa, com coordenada suspeita e sem coordenada à parte."""
    ok = distancia_valida(secoes)
    rot = pd.Series("sem coordenada", index=secoes.index, dtype=object)
    rot[secoes["distancia_m"].notna() & secoes["coord_repetida"].astype(bool)] = (
        "coordenada repetida (marcador)"
    )
    rot[secoes["distancia_suspeita"].astype(bool)] = (
        "acima de 50 km (coordenada suspeita)"
    )
    rot[ok] = secoes.loc[ok, "distancia_m"].map(_faixa)
    ordem = [f[2] for f in FAIXAS] + [
        "acima de 50 km (coordenada suspeita)",
        "coordenada repetida (marcador)",
        "sem coordenada",
    ]
    g = secoes.groupby(rot)["eleitores_2t"].agg(["size", "sum"])
    return {
        "faixas": [
            {
                "faixa": f,
                "secoes": int(g["size"].get(f, 0)),
                "eleitores": int(g["sum"].get(f, 0)),
            }
            for f in ordem
        ],
        "mediana_m": _q(secoes.loc[ok, "distancia_m"], 0.5),
        "p90_m": _q(secoes.loc[ok, "distancia_m"], 0.9),
        "secoes_com_distancia": int(ok.sum()),
    }


def _q(s: pd.Series, q: float) -> float | None:
    return None if s.empty else round(float(s.quantile(q)), 0)


def por_categoria(secoes: pd.DataFrame) -> dict[str, Any]:
    return {
        nome: histograma(secoes[secoes["categoria"].isin(cats)])
        for nome, cats in GRUPOS_CATEGORIA.items()
    }


def por_uf(secoes: pd.DataFrame) -> list[dict[str, Any]]:
    ok = distancia_valida(secoes)
    out = []
    for uf, g in secoes.groupby("uf"):
        d = g.loc[ok.loc[g.index], "distancia_m"]
        out.append(
            {
                "uf": uf,
                "secoes": len(g),
                "eleitores": int(g["eleitores_2t"].sum()),
                "secoes_com_distancia": len(d),
                "mediana_m": _q(d, 0.5),
                "p90_m": _q(d, 0.9),
            }
        )
    return sorted(out, key=lambda x: -x["eleitores"])


def vizinho_mais_proximo(cad: pd.DataFrame) -> pd.DataFrame:
    """Para cada local do 1º turno, a distância ao local mais próximo do município.

    Considera coordenadas distintas (prédio com várias zonas conta uma vez) e ignora
    coordenadas repetidas por três ou mais locais (marcador de posição).
    """
    base = cad[
        ["uf", "mun", "zona", "local_1t", "lat_1t", "lon_1t", "coord_repetida_1t"]
    ]
    base = base.drop_duplicates(["uf", "mun", "zona", "local_1t"])
    base = base[base["lat_1t"].notna() & ~base["coord_repetida_1t"].astype(bool)]
    pontos = base.drop_duplicates(["uf", "mun", "lat_1t", "lon_1t"])
    dist: dict[tuple[Any, ...], float] = {}
    for (uf, mun), g in pontos.groupby(["uf", "mun"]):
        lat = g["lat_1t"].to_numpy(float)
        lon = g["lon_1t"].to_numpy(float)
        if len(lat) < 2:
            continue
        m = en.haversine_vetor(lat[:, None], lon[:, None], lat[None, :], lon[None, :])
        m[m < VIZINHO_MIN_M] = np.inf
        mins = m.min(axis=1)
        for a, b, v in zip(lat, lon, mins, strict=True):
            if np.isfinite(v):
                dist[(uf, mun, a, b)] = float(v)
    base = base.copy()
    base["vizinho_m"] = [
        dist.get((u, m, a, b))
        for u, m, a, b in zip(
            base["uf"], base["mun"], base["lat_1t"], base["lon_1t"], strict=True
        )
    ]
    return base[["uf", "mun", "zona", "local_1t", "vizinho_m"]]


def _mediana_ponderada(valores: np.ndarray, pesos: np.ndarray) -> float:
    if not len(valores) or pesos.sum() <= 0:
        return float("nan")
    o = np.argsort(valores)
    v, w = valores[o], pesos[o]
    acum = np.cumsum(w)
    return float(v[np.searchsorted(acum, acum[-1] / 2.0)])


def _conglomerados(
    secoes: pd.DataFrame, valor: str, chave: list[str]
) -> tuple[np.ndarray, np.ndarray]:
    g = secoes.groupby(chave).agg(v=(valor, "first"), w=(valor, "size")).dropna()
    return g["v"].to_numpy(float), g["w"].to_numpy(float)


def _boot_mediana(
    v: np.ndarray, w: np.ndarray, reps: int, seed: int
) -> tuple[float, np.ndarray]:
    rng = np.random.default_rng(seed)
    ponto = _mediana_ponderada(v, w)
    out = np.empty(reps)
    n = len(v)
    for i in range(reps):
        ix = rng.integers(0, n, n)
        out[i] = _mediana_ponderada(v[ix], w[ix])
    return ponto, out


def _boot_parcela(
    v: np.ndarray, w: np.ndarray, corte: float, reps: int, seed: int
) -> tuple[float, np.ndarray]:
    rng = np.random.default_rng(seed)
    acima = (v > corte).astype(float)
    ponto = float((acima * w).sum() / w.sum()) if w.sum() else float("nan")
    out = np.empty(reps)
    n = len(v)
    for i in range(reps):
        ix = rng.integers(0, n, n)
        out[i] = (acima[ix] * w[ix]).sum() / w[ix].sum()
    return ponto, out


def teste_hipotese(
    secoes_mud: pd.DataFrame,
    cad: pd.DataFrame,
    vizinhos: pd.DataFrame,
    reps: int,
    seed: int,
) -> dict[str, Any]:
    """Medianas das novas realocações, da categoria A e do prédio vizinho, com IC."""
    ok = distancia_valida(secoes_mud)
    par = ["uf", "mun", "zona", "local_1t", "local_2t"]
    novas = secoes_mud[ok & (secoes_mud["categoria"] != "A")]
    a = secoes_mud[ok & (secoes_mud["categoria"] == "A")]
    vn, wn = _conglomerados(novas, "distancia_m", par)
    va, wa = _conglomerados(a, "distancia_m", par)
    chave_viz = ["uf", "mun", "zona", "local_1t"]
    todas = cad.merge(vizinhos, on=chave_viz, how="inner")
    vv, wv = _conglomerados(todas.dropna(subset=["vizinho_m"]), "vizinho_m", chave_viz)
    orig = novas.merge(vizinhos, on=chave_viz, how="inner").dropna(subset=["vizinho_m"])
    vo, wo = _conglomerados(orig, "vizinho_m", chave_viz)
    p_n, r_n = _boot_mediana(vn, wn, reps, seed)
    p_a, r_a = _boot_mediana(va, wa, reps, seed + 1)
    p_v, r_v = _boot_mediana(vv, wv, reps, seed + 2)
    p_o, r_o = _boot_mediana(vo, wo, reps, seed + 3)
    acima = {}
    for corte, nome in ((1000, "acima_1km"), (2000, "acima_2km")):
        p, r = _boot_parcela(vn, wn, corte, reps, seed + 4 + corte)
        acima[nome] = es.resumo_ic(p, r, 100.0, 1)
    return {
        "unidade": "seção; IC 95% por reamostragem de pares de locais (conglomerados), "
        f"{reps} réplicas",
        "novas_realocacoes": {
            "categorias": "B, C, X, D e E com mudança real",
            "secoes": int(wn.sum()),
            "pares": len(vn),
            "mediana_m": es.resumo_ic(p_n, r_n, 1.0, 0),
            "parcela_pct": acima,
        },
        "categoria_a_no_1t": {
            "descricao": "distância entre o local temporário do 1º turno e o original, "
            "para onde a seção volta",
            "secoes": int(wa.sum()),
            "pares": len(va),
            "mediana_m": es.resumo_ic(p_a, r_a, 1.0, 0),
        },
        "predio_vizinho": {
            "descricao": "distância de cada local do 1º turno ao local mais próximo do "
            "mesmo município no cadastro (coordenadas distintas, a mais de 1 m)",
            "secoes": int(wv.sum()),
            "locais": len(vv),
            "mediana_m": es.resumo_ic(p_v, r_v, 1.0, 0),
        },
        "predio_vizinho_das_novas": {
            "descricao": "a mesma referência, só para os locais de origem das novas "
            "realocações",
            "secoes": int(wo.sum()),
            "locais": len(vo),
            "mediana_m": es.resumo_ic(p_o, r_o, 1.0, 0),
        },
        "diferencas_m": {
            "novas_menos_a": es.resumo_ic(p_n - p_a, r_n - r_a, 1.0, 0),
            "novas_menos_vizinho": es.resumo_ic(p_n - p_v, r_n - r_v, 1.0, 0),
            "novas_menos_vizinho_da_origem": es.resumo_ic(p_n - p_o, r_n - r_o, 1.0, 0),
        },
        "rotulo": "Medida, sem atribuir intenção: compara a distância das realocações com "
        "a que as seções da categoria A percorreram no 1º turno e com a do prédio "
        "mais próximo no cadastro. Prédio mais próximo não é prédio disponível: pode "
        "não ter sala, acessibilidade ou energia.",
    }
