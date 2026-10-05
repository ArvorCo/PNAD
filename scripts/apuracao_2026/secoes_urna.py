"""Pergunta C: voto por modelo de urna, bruto e dentro da mesma zona e do mesmo local.

Modelos novos vão para capitais e cidades grandes, que votam diferente do
interior. A comparação bruta mistura modelo com geografia; a comparação dentro
da zona (e, mais forte, dentro do mesmo prédio) é a que separa as duas coisas.

Estimador: em cada unidade (zona ou local) com os dois modelos, a diferença entre
o percentual agregado das seções do modelo novo e o das seções do modelo velho;
a média dessas diferenças, ponderada pelos votantes das seções comparadas;
intervalo de 95% por bootstrap de unidades (2.000 reamostras).
"""

from __future__ import annotations

import warnings
from collections.abc import Mapping, Sequence
from itertools import combinations
from typing import Any

import numpy as np
import pandas as pd

from .secoes_2022 import casar
from .secoes_base import FLAVIO, LULA, Base, num, pct, r2

ORDEM_MODELOS = ["UE2009", "UE2010", "UE2011", "UE2013", "UE2015", "UE2020", "UE2022"]
BOOT = 2000
SEMENTE = 20261005
MIN_ZONA = 20
MIN_LOCAL = 1
REGISTRO = {"uf": "sp", "mun": "69531", "nome": "REGISTRO", "ibge": "3542602"}

# métrica: (numerador, denominador) ou, para variação contra 2022,
# (numerador 2026, denominador 2026, numerador 2022, denominador 2022)
Metrica = tuple[str, ...]
METRICAS_2026: dict[str, Metrica] = {
    "flavio_pp": (f"v{FLAVIO}", "validos"),
    "lula_pp": (f"v{LULA}", "validos"),
    "abstencao_pp": ("abstencao", "aptos"),
    "brancos_pp": ("brancos", "comparecimento"),
    "nulos_pp": ("nulos", "comparecimento"),
}
METRICAS_VARIACAO: dict[str, Metrica] = {
    "flavio_var_pp": (f"v{FLAVIO}", "validos", "bolsonaro_1t", "nominais_1t"),
    "lula_var_pp": (f"v{LULA}", "validos", "lula_1t", "nominais_1t"),
}
METRICAS_2022: dict[str, Metrica] = {
    "bolsonaro_pp": (f"v{FLAVIO}", "validos"),
    "lula_pp": (f"v{LULA}", "validos"),
    "abstencao_pp": ("abstencao", "aptos"),
    "brancos_pp": ("brancos", "comparecimento"),
    "nulos_pp": ("nulos", "comparecimento"),
}


def ordenar_modelos(modelos: Sequence[str]) -> list[str]:
    conhecidos = [m for m in ORDEM_MODELOS if m in modelos]
    return conhecidos + sorted(m for m in modelos if m not in ORDEM_MODELOS)


def _colunas(metricas: Mapping[str, Metrica]) -> list[str]:
    cols: list[str] = []
    for m in metricas.values():
        for c in m:
            if c not in cols:
                cols.append(c)
    return cols


def _taxa(larga: pd.DataFrame, m: Metrica, modelo: str) -> np.ndarray:
    """Percentual agregado (fração) do modelo em cada unidade; variação se 4 colunas."""

    def r(nu: str, de: str) -> np.ndarray:
        return larga[(nu, modelo)].to_numpy(float) / larga[(de, modelo)].to_numpy(float)

    with np.errstate(divide="ignore", invalid="ignore"):
        if len(m) == 4:
            return r(m[0], m[1]) - r(m[2], m[3])
        return r(m[0], m[1])


def _taxa_total(larga: pd.DataFrame, m: Metrica, modelo: str) -> float:
    def r(nu: str, de: str) -> float:
        return float(larga[(nu, modelo)].sum() / larga[(de, modelo)].sum())

    if len(m) == 4:
        return r(m[0], m[1]) - r(m[2], m[3])
    return r(m[0], m[1])


def diferenca_dentro(
    df: pd.DataFrame,
    unidade: Sequence[str],
    a: str,
    b: str,
    minimo: int,
    metricas: Mapping[str, Metrica],
    boot: int = BOOT,
    semente: int = SEMENTE,
) -> dict[str, Any] | None:
    """Diferença b − a (pp) dentro de cada unidade, média ponderada e IC por bootstrap.

    `df` tem uma linha por seção, com `modelo_urna`, `votantes` e as colunas das
    métricas. Unidades sem ao menos `minimo` seções de cada modelo ficam fora.
    """
    cols = _colunas(metricas)
    sub = df[df["modelo_urna"].isin([a, b])]
    if sub.empty:
        return None
    g = sub.groupby([*unidade, "modelo_urna"], sort=False)
    soma = g[[*cols, "votantes"]].sum()
    soma["n"] = g.size()
    larga = soma.unstack("modelo_urna")
    try:
        na = larga[("n", a)].fillna(0)
        nb = larga[("n", b)].fillna(0)
    except KeyError:
        return None
    ok = (na >= minimo) & (nb >= minimo)
    larga = larga[ok]
    u = len(larga)
    if u == 0:
        return None
    w = (larga[("votantes", a)] + larga[("votantes", b)]).to_numpy(dtype=float)
    rng = np.random.default_rng(semente)
    contagens = rng.multinomial(u, np.full(u, 1.0 / u), size=boot).astype(float)
    saida: dict[str, Any] = {
        "a": a,
        "b": b,
        "unidades": u,
        "secoes_a": int(larga[("n", a)].sum()),
        "secoes_b": int(larga[("n", b)].sum()),
        "votantes_a": int(larga[("votantes", a)].sum()),
        "votantes_b": int(larga[("votantes", b)].sum()),
    }
    for nome, m in metricas.items():
        d = 100 * (_taxa(larga, m, b) - _taxa(larga, m, a))
        valido = np.isfinite(d)
        ww = np.where(valido, w, 0.0)
        dd = np.where(valido, d, 0.0)
        if ww.sum() == 0:
            saida[nome] = None
            continue
        est = float((ww * dd).sum() / ww.sum())
        with warnings.catch_warnings(), np.errstate(divide="ignore", invalid="ignore"):
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            bs = (contagens @ (ww * dd)) / (contagens @ ww)
        bs = bs[np.isfinite(bs)]
        saida[nome] = {
            "estimativa": r2(est, 3),
            "ic95": [r2(np.percentile(bs, 2.5), 3), r2(np.percentile(bs, 97.5), 3)],
            "bruto": r2(100 * (_taxa_total(larga, m, b) - _taxa_total(larga, m, a)), 3),
        }
    return saida


def estimador(
    df: pd.DataFrame,
    unidade: Sequence[str],
    minimo: int,
    metricas: Mapping[str, Metrica],
    definicao: str,
) -> dict[str, Any]:
    modelos = ordenar_modelos(sorted(df["modelo_urna"].dropna().unique()))
    pares = []
    for a, b in combinations(modelos, 2):
        r = diferenca_dentro(df, unidade, a, b, minimo, metricas)
        if r is not None:
            pares.append(r)
    pares.append(_novo_velho(df, unidade, minimo, metricas, modelos))
    return {
        "definicao": definicao,
        "minimo_secoes_por_modelo": minimo,
        "bootstrap": BOOT,
        "semente": SEMENTE,
        "pares": [p for p in pares if p is not None],
    }


def _novo_velho(
    df: pd.DataFrame,
    unidade: Sequence[str],
    minimo: int,
    metricas: Mapping[str, Metrica],
    modelos: Sequence[str],
) -> dict[str, Any] | None:
    """Em cada unidade, o modelo mais novo contra o mais velho presentes."""
    pos = {m: i for i, m in enumerate(modelos)}
    d = df.dropna(subset=["modelo_urna"]).copy()
    d["_p"] = d["modelo_urna"].map(pos)
    cont = d.groupby([*unidade, "modelo_urna"]).size().rename("n").reset_index()
    cont = cont[cont["n"] >= minimo]
    cont["_p"] = cont["modelo_urna"].map(pos)
    lim = cont.groupby(unidade)["_p"].agg(["min", "max"])
    lim = lim[lim["min"] < lim["max"]].reset_index()
    if lim.empty:
        return None
    d = d.merge(lim, on=list(unidade), how="inner")
    d = d[(d["_p"] == d["min"]) | (d["_p"] == d["max"])].copy()
    d["modelo_urna"] = np.where(d["_p"] == d["max"], "mais nova", "mais velha")
    r = diferenca_dentro(d, unidade, "mais velha", "mais nova", minimo, metricas)
    return r


def _bruto(df: pd.DataFrame, metricas: Mapping[str, Metrica]) -> list[dict]:
    out = []
    modelos = ordenar_modelos(sorted(df["modelo_urna"].dropna().unique()))
    for m in [*modelos, None]:
        g = df[df["modelo_urna"].isna()] if m is None else df[df["modelo_urna"] == m]
        if g.empty:
            continue
        linha: dict[str, Any] = {
            "modelo": m or "sem modelo",
            "secoes": len(g),
            "votantes": int(g["votantes"].sum()),
            "validos": int(g["validos"].sum()),
        }
        for nome, (nu, de, *_) in metricas.items():
            linha[nome.replace("_pp", "_pct")] = pct(int(g[nu].sum()), int(g[de].sum()))
        out.append(linha)
    return out


def _por_uf(df: pd.DataFrame) -> list[dict[str, Any]]:
    tab = pd.crosstab(df["uf"], df["modelo_urna"].fillna("sem modelo"))
    out = []
    for uf in tab.index:
        tot = int(tab.loc[uf].sum())
        reg = df.loc[df["uf"] == uf, "regiao"].iloc[0]
        for m in tab.columns:
            n = int(tab.loc[uf, m])
            if n:
                out.append(
                    {
                        "uf": str(uf).upper(),
                        "regiao": reg,
                        "modelo": m,
                        "secoes": n,
                        "pct_da_uf": pct(n, tot),
                    }
                )
    return out


def _por_zona(
    df: pd.DataFrame, metricas: Mapping[str, Metrica]
) -> list[dict[str, Any]]:
    out = []
    for zona, gz in df.groupby("zona"):
        linhas = []
        for m in ordenar_modelos(sorted(gz["modelo_urna"].dropna().unique())):
            g = gz[gz["modelo_urna"] == m]
            linha: dict[str, Any] = {
                "modelo": m,
                "secoes": len(g),
                "votantes": int(g["votantes"].sum()),
            }
            for nome, (nu, de, *_) in metricas.items():
                linha[nome.replace("_pp", "_pct")] = pct(
                    int(g[nu].sum()), int(g[de].sum())
                )
            linhas.append(linha)
        out.append({"zona": int(zona), "secoes": len(gz), "modelos": linhas})
    return out


def base_2022(s22: pd.DataFrame) -> pd.DataFrame:
    """Seções de 2022 no formato das métricas (Bolsonaro na coluna v22)."""
    d = s22.dropna(subset=["aptos_2022"]).copy()
    d = d[d["aptos_2022"] > 0]
    d["modelo_urna"] = d["modelo_2022"]
    d[f"v{LULA}"] = d["lula_1t"].fillna(0)
    d[f"v{FLAVIO}"] = d["bolsonaro_1t"].fillna(0)
    d["validos"] = d["nominais_1t"].fillna(0)
    d["aptos"] = d["aptos_2022"]
    d["comparecimento"] = d["comparecimento_2022"]
    d["votantes"] = d["comparecimento_2022"]
    d["abstencao"] = d["aptos"] - d["comparecimento"]
    d["brancos"] = d["brancos_2022"]
    d["nulos"] = d["nulos_2022"]
    d["local_nr"] = d["local_nr_2022"]
    return d


def urna(base: Base, s22: pd.DataFrame | None) -> dict[str, Any]:
    df = base.secoes
    modelos = ordenar_modelos(sorted(df["modelo_urna"].dropna().unique()))
    zona = estimador(
        df,
        ["uf", "mun", "zona"],
        MIN_ZONA,
        METRICAS_2026,
        "Diferença (modelo b menos modelo a) dentro do par município e zona com ao "
        f"menos {MIN_ZONA} seções de cada modelo, média ponderada pelos votantes "
        "das seções comparadas; IC por bootstrap de zonas.",
    )
    local = estimador(
        df,
        ["uf", "mun", "zona", "local_nr"],
        MIN_LOCAL,
        METRICAS_2026,
        "Diferença (modelo b menos modelo a) dentro do mesmo local de votação "
        "(mesmo prédio), com ao menos uma seção de cada modelo; IC por bootstrap "
        "de locais.",
    )
    saida: dict[str, Any] = {
        "modelos": modelos,
        "fonte_modelo": [
            {"modelo_fonte": str(k), "secoes": int(v)}
            for k, v in df["modelo_fonte"].fillna("sem").value_counts().items()
        ],
        "por_uf": _por_uf(df),
        "bruto": _bruto(df, METRICAS_2026),
        "dentro_zona": zona,
        "dentro_local": local,
        "registro": _registro(df, s22),
    }
    if s22 is not None:
        casado = casar(df, s22)
        casado = casado[casado["mesma_secao"]]
        saida["dentro_zona_variacao"] = estimador(
            casado,
            ["uf", "mun", "zona"],
            MIN_ZONA,
            METRICAS_VARIACAO,
            "Diferença entre modelos, dentro do par município e zona, da variação "
            "de cada seção contra ela mesma em 2022 (Flávio 2026 menos Bolsonaro "
            "1º turno 2022; Lula 2026 menos Lula 2022, em % dos válidos). A linha "
            "de base de 2022 da mesma seção tira o perfil político do lugar; só "
            "seções casadas pelo número e pelo nome do local.",
        )
        saida["dentro_zona_variacao"]["secoes_casadas"] = len(casado)
        saida["troca_2022_2026"] = troca_de_urna(casado)
        d22 = base_2022(s22)
        saida["ano_2022"] = {
            "fonte": (
                "TSE, detalhe_votacao_secao_2022 (modelo da urna, aptos, "
                "comparecimento, brancos, nulos) e votacao_secao_2022_BR (votos por "
                "candidato), presidente, 1º turno"
            ),
            "metricas": "bolsonaro_pp no lugar de flavio_pp",
            "modelos": ordenar_modelos(sorted(d22["modelo_urna"].dropna().unique())),
            "bruto": _bruto(d22, METRICAS_2022),
            "dentro_zona": estimador(
                d22,
                ["uf", "mun", "zona"],
                MIN_ZONA,
                METRICAS_2022,
                "Mesmo estimador de 2026, sobre 2022 (Bolsonaro e Lula no 1º turno).",
            ),
            "dentro_local": estimador(
                d22,
                ["uf", "mun", "zona", "local_nr"],
                MIN_LOCAL,
                METRICAS_2022,
                "Mesmo estimador de 2026 dentro do local, sobre 2022.",
            ),
        }
    saida["interpretacao"] = interpretar(saida)
    return saida


def troca_de_urna(casado: pd.DataFrame) -> dict[str, Any]:
    """A mesma seção com urna velha em 2022 e nova em 2026, contra a que já era nova.

    Se a urna velha de 2022 tivesse tirado voto de Bolsonaro, as seções que a
    trocaram teriam, de 2022 para 2026, um ganho de Flávio maior que o das seções
    que já tinham a UE2020 em 2022, dentro da mesma zona. O rótulo de cada seção é
    o modelo de 2022; a métrica é a variação da própria seção.
    """
    d = casado.dropna(subset=["modelo_2022"]).copy()
    d["modelo_urna_2026"] = d["modelo_urna"]
    d["modelo_urna"] = d["modelo_2022"]
    est = estimador(
        d,
        ["uf", "mun", "zona"],
        MIN_ZONA,
        METRICAS_VARIACAO,
        "Variação de cada seção de 2022 para 2026 (Flávio 2026 menos Bolsonaro 1º "
        "turno 2022, em % dos válidos), comparada entre seções agrupadas pelo "
        "modelo da urna de 2022 dentro do par município e zona. Diferença b menos "
        "a: se a urna velha (a) de 2022 tivesse tirado voto de Bolsonaro, a "
        "diferença seria negativa.",
    )
    est["secoes_casadas"] = len(d)
    est["modelos_2026_das_velhas"] = [
        {"modelo_2022": str(m22), "modelo_2026": str(m26), "secoes": int(n)}
        for (m22, m26), n in d.groupby(
            [d["modelo_2022"], d["modelo_urna_2026"].fillna("sem modelo")]
        )
        .size()
        .items()
    ]
    return est


def _registro(df: pd.DataFrame, s22: pd.DataFrame | None) -> dict[str, Any]:
    r = df[(df["uf"] == REGISTRO["uf"]) & (df["mun"] == REGISTRO["mun"])]
    saida: dict[str, Any] = {
        "municipio": REGISTRO["nome"],
        "uf": "SP",
        "mun_tse": REGISTRO["mun"],
        "ibge": REGISTRO["ibge"],
        "disponivel_2026": not r.empty,
        "secoes_2026": len(r),
        "zonas_2026": _por_zona(r, METRICAS_2026) if not r.empty else [],
        "dentro_zona_2026": (
            estimador(
                r,
                ["uf", "mun", "zona"],
                1,
                METRICAS_2026,
                "Diferença dentro da zona em Registro, com ao menos uma seção de "
                "cada modelo.",
            )
            if not r.empty
            else None
        ),
        "dentro_local_2026": (
            estimador(
                r,
                ["uf", "mun", "zona", "local_nr"],
                1,
                METRICAS_2026,
                "Diferença dentro do mesmo local de votação em Registro; IC por "
                "bootstrap de locais.",
            )
            if not r.empty
            else None
        ),
    }
    if s22 is not None and not r.empty:
        rc = casar(r, s22)
        rc = rc[rc["mesma_secao"]]
        saida["variacao_2026"] = estimador(
            rc,
            ["uf", "mun", "zona"],
            1,
            METRICAS_VARIACAO,
            "Variação de cada seção de Registro contra ela mesma em 2022, "
            "comparada entre modelos de 2026 dentro da zona.",
        )
        saida["variacao_2026"]["secoes_casadas"] = len(rc)
        saida["mesmas_secoes"] = _mesmas_secoes(rc)
    if s22 is None:
        saida["ano_2022"] = {
            "disponivel": False,
            "motivo": "votacao_secao_2022_BR.zip ausente",
        }
        return saida
    d22 = base_2022(s22)
    r22 = d22[(d22["uf"] == REGISTRO["uf"]) & (d22["mun"] == REGISTRO["mun"])]
    saida["ano_2022"] = {
        "disponivel": not r22.empty,
        "fonte": "TSE, votacao_secao_2022_BR e detalhe_votacao_secao_2022",
        "secoes": len(r22),
        "zonas": _por_zona(r22, METRICAS_2022),
        "dentro_zona": estimador(
            r22,
            ["uf", "mun", "zona"],
            1,
            METRICAS_2022,
            "Diferença dentro da zona em Registro em 2022 (Bolsonaro e Lula, 1º "
            "turno), com ao menos uma seção de cada modelo; uma zona só, então o "
            "intervalo por bootstrap de zonas é degenerado.",
        ),
        "dentro_local": estimador(
            r22,
            ["uf", "mun", "zona", "local_nr"],
            1,
            METRICAS_2022,
            "Diferença dentro do mesmo local de votação em Registro em 2022; IC por "
            "bootstrap de locais.",
        ),
    }
    return saida


def _mesmas_secoes(rc: pd.DataFrame) -> list[dict[str, Any]]:
    """Registro: as seções agrupadas pelo modelo de 2022, com o voto de 2022 e 2026."""
    out = []
    for m22, g in rc.groupby(rc["modelo_2022"].fillna("sem modelo")):
        out.append(
            {
                "modelo_2022": str(m22),
                "secoes": len(g),
                "bolsonaro_2022_pct": pct(
                    int(g["bolsonaro_1t"].sum()), int(g["nominais_1t"].sum())
                ),
                "lula_2022_pct": pct(
                    int(g["lula_1t"].sum()), int(g["nominais_1t"].sum())
                ),
                "flavio_2026_pct": pct(
                    int(g[f"v{FLAVIO}"].sum()), int(g["validos"].sum())
                ),
                "lula_2026_pct": pct(int(g[f"v{LULA}"].sum()), int(g["validos"].sum())),
                "modelos_2026": {
                    str(k): int(v)
                    for k, v in g["modelo_urna"]
                    .fillna("sem modelo")
                    .value_counts()
                    .items()
                },
            }
        )
    return out


def _ic_txt(m: Mapping[str, Any]) -> tuple[str, bool]:
    lo, hi = m["ic95"]
    cruza = lo is not None and hi is not None and lo <= 0 <= hi
    txt = f"IC 95% de {num(lo, 2)} a {num(hi, 2)}"
    return txt + (", contém o zero" if cruza else ", não contém o zero"), cruza


def _frase(
    p: Mapping[str, Any] | None, chave: str, onde: str, quem: str, unidade: str
) -> str | None:
    """Frase do par `mais velha` → `mais nova` (ou de um par nomeado)."""
    if not p or not p.get(chave):
        return None
    m = p[chave]
    ic, _ = _ic_txt(m)
    if p["a"] == "mais velha":
        par = "a urna mais nova dá a {q} {e} ponto em relação à mais velha"
    else:
        par = f"a {p['b']} dá a {{q}} {{e}} ponto em relação à {p['a']}"
    corpo = par.format(q=quem, e=num(m["estimativa"], 2))
    return (
        f"{onde}, {corpo} ({ic}); sem o controle, {num(m['bruto'], 2)}; "
        f"{num(p['unidades'], 0)} {unidade}."
    )


def _mais(pares: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    return next((p for p in pares if p["a"] == "mais velha"), None)


def interpretar(u: Mapping[str, Any]) -> list[str]:
    frases: list[str] = []
    nv = _mais(u["dentro_zona"]["pares"])
    if nv and nv.get("flavio_pp"):
        _, cruza = _ic_txt(nv["flavio_pp"])
        abre = (
            "O modelo da urna não move o voto de forma separável de zero dentro da "
            "zona"
            if cruza
            else "Dentro da zona há diferença entre modelos separável de zero, o que "
            "não é efeito da urna enquanto a alocação dos modelos dentro da zona "
            "não for aleatória"
        )
        frases.append(
            abre
            + ": "
            + (_frase(nv, "flavio_pp", "na mesma zona", "Flávio", "zonas") or "")
        )
    f = _frase(
        _mais(u["dentro_local"]["pares"]),
        "flavio_pp",
        "No mesmo prédio",
        "Flávio",
        "locais",
    )
    if f:
        frases.append(f)
    a22 = u.get("ano_2022")
    if a22:
        p = _par_nomeado(a22["dentro_zona"]["pares"], "UE2015", "UE2020")
        f = _frase(p, "bolsonaro_pp", "Em 2022, na mesma zona", "Bolsonaro", "zonas")
        if f:
            frases.append(f)
        p = _par_nomeado(a22["dentro_local"]["pares"], "UE2015", "UE2020")
        f = _frase(p, "bolsonaro_pp", "Em 2022, no mesmo prédio", "Bolsonaro", "locais")
        if f:
            frases.append(f)
    tr = u.get("troca_2022_2026")
    if tr:
        f = _frase(
            _mais(tr["pares"]),
            "flavio_var_pp",
            "Nas mesmas seções de 2022 para 2026, agrupadas pelo modelo de 2022",
            "Flávio, sobre Bolsonaro,",
            "zonas",
        )
        if f:
            frases.append(f)
    return frases


def _par_nomeado(
    pares: Sequence[Mapping[str, Any]], a: str, b: str
) -> Mapping[str, Any] | None:
    return next((p for p in pares if p["a"] == a and p["b"] == b), None)
