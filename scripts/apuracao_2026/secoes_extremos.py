"""Perguntas A (seções acima de 90%) e D (outras anomalias de seção).

Tudo aqui recebe a `Base` já filtrada (seções com boletim, zona conferida contra o
arquivo do TSE) e devolve dicionários prontos para o JSON do contrato
`analysis/apuracao_2026/CONTRATO_SECOES.md`.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from .secoes_2022 import casar
from .secoes_base import (
    FLAVIO,
    LULA,
    TIPO_ARQUIVO,
    TIPO_URNA,
    Base,
    amostras,
    pct,
    r2,
    regras_local_json,
)

LIMIARES = (90, 95, 100)
CORTE_TAMANHO = 100
FAIXAS_TAMANHO = [
    ("1–49", 1, 49),
    ("50–99", 50, 99),
    ("100–199", 100, 199),
    ("200–299", 200, 299),
    ("300–399", 300, 399),
    ("400+", 400, 10**9),
]
FAIXAS_ZONA = [
    ("abaixo de 50%", 0, 50),
    ("50% a 70%", 50, 70),
    ("70% a 80%", 70, 80),
    ("80% a 85%", 80, 85),
    ("85% a 90%", 85, 90),
    ("90% ou mais", 90, 100.0001),
]
CANDS = (("lula", LULA), ("flavio", FLAVIO))


def _mascara(df: pd.DataFrame, numero: int, limiar: int) -> pd.Series:
    v = df[f"v{numero}"]
    if limiar >= 100:
        return (df["validos"] > 0) & (v == df["validos"])
    return (df["validos"] > 0) & (100 * v >= limiar * df["validos"])


# ---------------------------------------------------------------- pergunta A


def extremos(
    base: Base, anomalias_topo: Sequence[dict[str, Any]], com_2022: pd.DataFrame | None
) -> dict[str, Any]:
    df = base.secoes
    df = df[df["validos"] > 0]
    total = len(df)
    resumo = []
    por_uf = []
    for chave, num in CANDS:
        for lim in LIMIARES:
            m = _mascara(df, num, lim)
            s = df[m]
            resumo.append(
                {
                    "candidato": chave,
                    "limiar": lim,
                    "secoes": len(s),
                    "secoes_100mais": int((s["votantes"] >= CORTE_TAMANHO).sum()),
                    "aptos": int(s["aptos"].sum()),
                    "votantes": int(s["votantes"].sum()),
                    "validos": int(s["validos"].sum()),
                    "votos_candidato": int(s[f"v{num}"].sum()),
                    "pct_das_secoes": pct(len(s), total),
                }
            )
            tot_uf = df.groupby("uf").size()
            for uf, g in s.groupby("uf"):
                por_uf.append(
                    {
                        "uf": str(uf).upper(),
                        "regiao": g["regiao"].iloc[0],
                        "candidato": chave,
                        "limiar": lim,
                        "secoes": len(g),
                        "secoes_100mais": int((g["votantes"] >= CORTE_TAMANHO).sum()),
                        "aptos": int(g["aptos"].sum()),
                        "pct_das_secoes_uf": pct(len(g), int(tot_uf[uf])),
                    }
                )
    return {
        "definicao": (
            "Percentual dos votos válidos de presidente em cada seção (boletim de "
            "urna): votos do candidato divididos pelos votos nominais nos 12 "
            "candidatos da lista. Seções sem voto válido ficam fora."
        ),
        "limiares": list(LIMIARES),
        "corte_tamanho": CORTE_TAMANHO,
        "secoes_base": total,
        "secoes_sem_validos": int((base.secoes["validos"] == 0).sum()),
        "resumo": resumo,
        "por_uf": por_uf,
        "por_municipio": _por_municipio(df),
        "tamanho": _tamanho(df),
        "histograma": _histograma(df),
        "excesso": _excesso(df),
        "tipo_local": _tipo_local(df),
        "modelo_urna": _modelo(df),
        "cruzamento_anomalias": _cruzamento(df, anomalias_topo),
        "amostras": _amostras_extremos(df),
        "secoes_100pct": _cem(df),
        "mapa": _mapa(df),
        "comparacao_2022": _comparacao_2022(df, com_2022),
    }


def _por_municipio(df: pd.DataFrame) -> list[dict[str, Any]]:
    out = []
    tot = df.groupby(["uf", "mun"]).size()
    for chave, num in CANDS:
        m = _mascara(df, num, 90)
        g = df[m].groupby(["uf", "mun"])
        cont = g.size().sort_values(ascending=False).head(40)
        for (uf, mun), n in cont.items():
            sub = df[(df["uf"] == uf) & (df["mun"] == mun)]
            out.append(
                {
                    "uf": str(uf).upper(),
                    "municipio": sub["municipio"].iloc[0],
                    "mun_tse": mun,
                    "ibge": (
                        sub["ibge"].iloc[0]
                        if isinstance(sub["ibge"].iloc[0], str)
                        else None
                    ),
                    "candidato": chave,
                    "secoes_90": int(n),
                    "secoes_total": int(tot[(uf, mun)]),
                    "aptos_90": int(
                        df[m & (df["uf"] == uf) & (df["mun"] == mun)]["aptos"].sum()
                    ),
                    "mun_pct": r2(sub[f"mun_{chave}_pct"].iloc[0]),
                }
            )
    return out


def _tamanho(df: pd.DataFrame) -> dict[str, Any]:
    linhas = []
    for rot, lo, hi in FAIXAS_TAMANHO:
        s = df[(df["votantes"] >= lo) & (df["votantes"] <= hi)]
        lula = int(_mascara(s, LULA, 90).sum())
        flavio = int(_mascara(s, FLAVIO, 90).sum())
        linhas.append(
            {
                "faixa": rot,
                "todas": len(s),
                "lula_90": lula,
                "flavio_90": flavio,
                "lula_90_pct": pct(lula, len(s)),
                "flavio_90_pct": pct(flavio, len(s)),
            }
        )
    return {
        "base": "votantes (comparecimento) da seção",
        "faixas": [{"rotulo": r, "min": lo, "max": hi} for r, lo, hi in FAIXAS_TAMANHO],
        "linhas": linhas,
        "votantes_mediana": r2(df["votantes"].median()),
    }


def _histograma(df: pd.DataFrame) -> dict[str, Any]:
    bins = np.arange(0, 100.0001, 2.5)
    out: dict[str, Any] = {"bins_pct": [float(b) for b in bins]}
    grande = df["votantes"] >= CORTE_TAMANHO
    for chave, _ in CANDS:
        x = df[f"{chave}_pct"].to_numpy()
        out[chave] = np.histogram(x, bins=bins)[0].astype(int).tolist()
        out[f"{chave}_100mais"] = (
            np.histogram(x[grande], bins=bins)[0].astype(int).tolist()
        )
    return out


def _excesso(df: pd.DataFrame) -> dict[str, Any]:
    saida: dict[str, Any] = {
        "definicao": (
            "Excesso = % do candidato na seção menos % do candidato no resto da zona "
            "(a zona sem a própria seção), em pontos; o mesmo contra o resto do "
            "município. Zona é o par município e zona eleitoral."
        )
    }
    for chave, num in CANDS:
        s = df[_mascara(df, num, 90)]
        ez = s[f"{chave}_pct"] - s[f"zona_resto_{chave}_pct"]
        em = s[f"{chave}_pct"] - s[f"mun_resto_{chave}_pct"]
        faixas = []
        for rot, lo, hi in FAIXAS_ZONA:
            z = s[f"zona_resto_{chave}_pct"]
            faixas.append(
                {
                    "rotulo": rot,
                    "min_pct": lo,
                    "max_pct": min(hi, 100),
                    "secoes": int(((z >= lo) & (z < hi)).sum()),
                }
            )
        saida[chave] = {
            "secoes": len(s),
            "zona_pct_mediana": r2(s[f"zona_resto_{chave}_pct"].median()),
            "mun_pct_mediana": r2(s[f"mun_resto_{chave}_pct"].median()),
            "excesso_zona_pp_mediana": r2(ez.median()),
            "excesso_mun_pp_mediana": r2(em.median()),
            "faixas_zona": faixas,
            "acima_zona_10pp": int((ez >= 10).sum()),
            "acima_zona_20pp": int((ez >= 20).sum()),
            "sem_resto_de_zona": int(s[f"zona_resto_{chave}_pct"].isna().sum()),
        }
    return saida


def _tipo_local(df: pd.DataFrame) -> dict[str, Any]:
    linhas = []
    for tipo, g in df.groupby("tipo_inferido"):
        lula = int(_mascara(g, LULA, 90).sum())
        flavio = int(_mascara(g, FLAVIO, 90).sum())
        linhas.append(
            {
                "tipo": tipo,
                "todas": len(g),
                "lula_90": lula,
                "flavio_90": flavio,
                "lula_90_pct_do_tipo": pct(lula, len(g)),
                "flavio_90_pct_do_tipo": pct(flavio, len(g)),
            }
        )
    linhas.sort(key=lambda r: -r["todas"])
    return {
        "regras": regras_local_json(),
        "linhas": linhas,
        "aviso": (
            "Tipo de local é inferência por palavra-chave no nome, no bairro e no "
            "endereço do cadastro de locais de votação do TSE, na ordem das regras; "
            "só o tipo oficial (Preso provisório, Voto em trânsito) vem do cadastro."
        ),
    }


def _modelo(df: pd.DataFrame) -> list[dict[str, Any]]:
    out = []
    for modelo, g in df.groupby(df["modelo_urna"].fillna("sem modelo")):
        lula = int(_mascara(g, LULA, 90).sum())
        flavio = int(_mascara(g, FLAVIO, 90).sum())
        out.append(
            {
                "modelo": modelo,
                "todas": len(g),
                "lula_90": lula,
                "flavio_90": flavio,
                "lula_90_pct_do_modelo": pct(lula, len(g)),
                "flavio_90_pct_do_modelo": pct(flavio, len(g)),
            }
        )
    return out


def _cruzamento(df: pd.DataFrame, topo: Sequence[dict[str, Any]]) -> dict[str, Any]:
    chaves = {
        (str(z["uf"]).lower(), str(z["municipio_tse"]), int(z["zona"])): z for z in topo
    }
    k = pd.Series(
        list(zip(df["uf"], df["mun"], df["zona"].astype(int), strict=True)),
        index=df.index,
    )
    no_topo = k.isin(set(chaves))
    lula = _mascara(df, LULA, 90)
    flavio = _mascara(df, FLAVIO, 90)
    sub = pd.DataFrame({"k": k[no_topo], "l": lula[no_topo], "f": flavio[no_topo]})
    lista = []
    for c, g in sub.groupby("k"):
        z = chaves[c]
        lista.append(
            {
                "posicao": z.get("posicao"),
                "uf": str(z["uf"]).upper(),
                "municipio": z.get("municipio"),
                "zona": int(z["zona"]),
                "escore": z.get("escore"),
                "secoes": len(g),
                "lula_90": int(g["l"].sum()),
                "flavio_90": int(g["f"].sum()),
            }
        )
    lista.sort(key=lambda r: r["posicao"] or 0)
    nt = int(no_topo.sum())
    nd = len(df) - nt
    return {
        "top_zonas": len(topo),
        "zonas_top_na_base": len(lista),
        "zonas_top_com_secao_90": sum(
            1 for r in lista if r["lula_90"] or r["flavio_90"]
        ),
        "secoes_no_top": nt,
        "secoes_90_no_top": int((no_topo & (lula | flavio)).sum()),
        "taxa_lula_90_top_pct": pct(int((no_topo & lula).sum()), nt),
        "taxa_lula_90_demais_pct": pct(int((~no_topo & lula).sum()), nd),
        "taxa_flavio_90_top_pct": pct(int((no_topo & flavio).sum()), nt),
        "taxa_flavio_90_demais_pct": pct(int((~no_topo & flavio).sum()), nd),
        "lista": lista,
    }


def _amostras_extremos(df: pd.DataFrame) -> dict[str, Any]:
    out = {}
    for chave, num in CANDS:
        s = df[_mascara(df, num, 90) & (df["votantes"] >= CORTE_TAMANHO)].copy()
        s["excesso_zona_pp"] = s[f"{chave}_pct"] - s[f"zona_resto_{chave}_pct"]
        s["excesso_mun_pp"] = s[f"{chave}_pct"] - s[f"mun_resto_{chave}_pct"]
        s = s.sort_values("excesso_zona_pp", ascending=False, na_position="last")
        out[chave] = amostras(s, 25, ("excesso_zona_pp", "excesso_mun_pp"))
    return out


def _cem(df: pd.DataFrame) -> dict[str, Any]:
    out = {}
    for chave, num in CANDS:
        s = df[_mascara(df, num, 100) & (df["validos"] >= 20)]
        s = s.sort_values("validos", ascending=False)
        out[chave] = amostras(s, 60)
        out[f"{chave}_total"] = len(s)
    return out


def _mapa(df: pd.DataFrame) -> dict[str, Any]:
    d = df.assign(
        l90=_mascara(df, LULA, 90).astype(int),
        f90=_mascara(df, FLAVIO, 90).astype(int),
        um=1,
    )
    g = d.groupby(["uf", "mun", "zona", "local_nr"], dropna=False).agg(
        lat=("lat", "first"),
        lon=("lon", "first"),
        l90=("l90", "sum"),
        f90=("f90", "sum"),
        secoes=("um", "sum"),
    )
    g = g[(g["l90"] > 0) | (g["f90"] > 0)]
    com = g.dropna(subset=["lat", "lon"])
    pontos = [
        [
            round(float(r.lat), 3),
            round(float(r.lon), 3),
            int(r.l90),
            int(r.f90),
            int(r.secoes),
        ]
        for r in com.itertuples()
    ]
    return {
        "colunas": ["lat", "lon", "lula_90", "flavio_90", "secoes"],
        "pontos": pontos,
        "n_locais": len(g),
        "n_sem_coordenada": len(g) - len(com),
    }


def _comparacao_2022(df: pd.DataFrame, s22: pd.DataFrame | None) -> dict[str, Any]:
    if s22 is None:
        return {
            "disponivel": False,
            "motivo": "arquivo votacao_secao_2022_BR.zip ausente",
        }
    m = casar(df, s22)
    mesma = m["mesma_secao"]
    out: dict[str, Any] = {
        "disponivel": True,
        "fonte": (
            "TSE, votacao_secao_2022_BR.zip (votos por candidato e seção, presidente, "
            "1º e 2º turnos de 2022)"
        ),
        "criterio_mesma_secao": (
            "mesma UF, município, zona e número de seção, e mesmo nome do local de "
            "votação nos dois cadastros (sem acento e sem espaços repetidos)"
        ),
        "secoes_2026": len(df),
        "secoes_casadas": int(mesma.sum()),
    }
    with np.errstate(divide="ignore", invalid="ignore"):
        m["lula22_pct"] = 100 * m["lula_1t"] / m["nominais_1t"]
        m["bolso22_pct"] = 100 * m["bolsonaro_1t"] / m["nominais_1t"]
        m["lula22_2t_pct"] = 100 * m["lula_2t"] / m["nominais_2t"]
        m["bolso22_2t_pct"] = 100 * m["bolsonaro_2t"] / m["nominais_2t"]
    total_22 = {
        "lula_90_1t": int((mesma & (m["lula22_pct"] >= 90)).sum()),
        "bolsonaro_90_1t": int((mesma & (m["bolso22_pct"] >= 90)).sum()),
        "lula_90_2t": int((mesma & (m["lula22_2t_pct"] >= 90)).sum()),
        "bolsonaro_90_2t": int((mesma & (m["bolso22_2t_pct"] >= 90)).sum()),
    }
    out["secoes_90_em_2022_entre_casadas"] = total_22
    for chave, num, col22, col22b in (
        ("lula", LULA, "lula22_pct", "lula22_2t_pct"),
        ("flavio", FLAVIO, "bolso22_pct", "bolso22_2t_pct"),
    ):
        sel = _mascara(m, num, 90) & mesma
        s = m[sel]
        out[chave] = {
            "secoes_90_2026_casadas": len(s),
            "tambem_90_em_2022_1t": int((s[col22] >= 90).sum()),
            "tambem_90_em_2022_2t": int((s[col22b] >= 90).sum()),
            "acima_80_em_2022_1t": int((s[col22] >= 80).sum()),
            "pct_2022_1t_mediana": r2(s[col22].median()),
            "pct_2022_2t_mediana": r2(s[col22b].median()),
            "variacao_pp_mediana": r2((s[f"{chave}_pct"] - s[col22]).median()),
            "novas_abaixo_70_em_2022": int((s[col22] < 70).sum()),
        }
    return out


# ---------------------------------------------------------------- pergunta D


def _dif_zona(g: pd.DataFrame, chave: str) -> float | None:
    """Média ponderada (válidos) de seção menos resto da zona, em pp."""
    d = g[f"{chave}_pct"] - g[f"zona_resto_{chave}_pct"]
    w = g["validos"].where(d.notna(), 0)
    if w.sum() == 0:
        return None
    return r2((d.fillna(0) * w).sum() / w.sum())


def _linha_grupo(
    rotulo: str, chave: str, valor: Any, g: pd.DataFrame
) -> dict[str, Any]:
    validos = int(g["validos"].sum())
    return {
        chave: valor,
        "descricao": rotulo,
        "secoes": len(g),
        "votantes": int(g["votantes"].sum()),
        "flavio_pct": pct(int(g[f"v{FLAVIO}"].sum()), validos),
        "lula_pct": pct(int(g[f"v{LULA}"].sum()), validos),
        "dif_zona_flavio_pp": _dif_zona(g, "flavio"),
        "dif_zona_lula_pp": _dif_zona(g, "lula"),
    }


def outras(base: Base) -> dict[str, Any]:
    df = base.secoes
    return {
        "comparecimento": _comparecimento(df),
        "zero_votos": _zero_votos(df),
        "tipo_arquivo": [
            _linha_grupo(TIPO_ARQUIVO.get(int(k), str(k)), "tipo_arquivo", int(k), g)
            for k, g in df.groupby("tipo_arquivo")
        ],
        "tipo_urna": [
            _linha_grupo(TIPO_URNA.get(int(k), str(k)), "tipo_urna", int(k), g)
            for k, g in df.groupby("tipo_urna")
        ],
        "cargas": [
            _linha_grupo(rot, "n_cargas", rot, g)
            for rot, g in df.groupby(
                df["n_cargas"].fillna(1).clip(upper=3).map({1: "1", 2: "2", 3: "3+"})
            )
        ],
        "amostras_nao_padrao": amostras(
            df[(df["tipo_arquivo"] != 1) | (df["tipo_urna"] != 1)].sort_values(
                "votantes", ascending=False
            ),
            40,
        ),
        "horarios": _horarios(df),
        "recebimento": _recebimento(df),
        "ultimo_digito": _ultimo_digito(df),
        "benford2": _benford2(df),
        "aviso_benford": (
            "Testes de dígito (último dígito e Benford do segundo dígito) são "
            "curiosidade metodológica: contagens de votos não seguem Benford por "
            "construção, e o teste rejeita ou aceita por motivos que nada têm a ver "
            "com fraude (Deckert, Myagkov e Ordeshook, 2011, Political Analysis 19(3))."
        ),
    }


def _comparecimento(df: pd.DataFrame) -> dict[str, Any]:
    acima = df[df["comparecimento"] > df["aptos"]]
    igual = df[df["comparecimento"] == df["aptos"]]
    alto = df[100 * df["comparecimento"] >= 98 * df["aptos"]]
    return {
        "acima_100": len(acima),
        "igual_100": len(igual),
        "abstencao_zero": len(igual),
        "acima_98": len(alto),
        "igual_100_por_tamanho": {
            "ate_49_aptos": int((igual["aptos"] < 50).sum()),
            "50_a_99": int(((igual["aptos"] >= 50) & (igual["aptos"] < 100)).sum()),
            "100_mais": int((igual["aptos"] >= 100).sum()),
        },
        "amostras": amostras(
            pd.concat([acima, igual]).sort_values("aptos", ascending=False), 30
        ),
        "comparecimento_mediano_pct": r2(
            (100 * df["comparecimento"] / df["aptos"]).median()
        ),
    }


def _zero_votos(df: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {"minimo_votantes": 200}
    grande = df[df["votantes"] >= 200]
    for chave, num in CANDS:
        s = grande[grande[f"v{num}"] == 0]
        out[chave] = {
            "secoes": len(s),
            "secoes_base": len(grande),
            "por_uf": [
                {"uf": str(u).upper(), "secoes": len(g)} for u, g in s.groupby("uf")
            ],
            "amostras": amostras(s.sort_values("votantes", ascending=False), 30),
        }
    return out


def _horarios(df: pd.DataFrame) -> dict[str, Any]:
    br = df[df["uf"] != "zz"]
    fuso = pd.to_timedelta(br["fuso"].fillna(0), unit="h")
    ab = pd.to_datetime(br["abertura"], errors="coerce") + fuso
    en = pd.to_datetime(br["encerramento"], errors="coerce") + fuso
    dia = pd.Timestamp("2026-10-04")

    def h(x: float) -> pd.Timestamp:
        return dia + pd.Timedelta(hours=x)

    hist = en.dt.floor("h").value_counts().sort_index()
    tarde = br.assign(_en=en).sort_values("_en", ascending=False)
    cedo = br.assign(_ab=ab).sort_values("_ab")
    atraso = br.assign(_ab=ab).sort_values("_ab", ascending=False)
    grupos = {
        "encerramento_depois_19h": br[en >= h(19)],
        "abertura_depois_9h": br[ab >= h(9)],
    }
    return {
        "fuso": (
            "O boletim grava a hora local da urna. Conversão para Brasília pela hora "
            "de abertura mais frequente no município (a votação abriu às 8h de "
            "Brasília em todo o país). Exterior fora."
        ),
        "secoes": len(br),
        "sem_hora": int(ab.isna().sum()),
        "abertura": {
            "antes_0730": int((ab < h(7.5)).sum()),
            "depois_0900": int((ab >= h(9)).sum()),
            "depois_1000": int((ab >= h(10)).sum()),
            "depois_1200": int((ab >= h(12)).sum()),
            "amostras_cedo": amostras(cedo, 10),
            "amostras_tarde": amostras(atraso, 15),
        },
        "encerramento": {
            "antes_1700": int((en < h(17)).sum()),
            "depois_1800": int((en >= h(18)).sum()),
            "depois_1900": int((en >= h(19)).sum()),
            "depois_2000": int((en >= h(20)).sum()),
            "amostras": amostras(tarde, 20),
        },
        "histograma_encerramento": [
            {"hora": k.strftime("%Y-%m-%d %H"), "secoes": int(v)}
            for k, v in hist.items()
        ],
        "voto_vs_zona": [
            _linha_grupo(rot, "grupo", rot, g) for rot, g in grupos.items() if len(g)
        ],
    }


def _recebimento(df: pd.DataFrame) -> dict[str, Any]:
    br = df[df["uf"] != "zz"].copy()
    br["_dr"] = pd.to_datetime(br["dr_hr"], errors="coerce")
    br["_h"] = br["_dr"].dt.floor("h")
    por_hora = []
    for hora, g in br.groupby("_h"):
        validos = int(g["validos"].sum())
        por_hora.append(
            {
                "hora": hora.strftime("%Y-%m-%d %H"),
                "secoes": len(g),
                "validos": validos,
                "lula_pct": pct(int(g[f"v{LULA}"].sum()), validos),
                "flavio_pct": pct(int(g[f"v{FLAVIO}"].sum()), validos),
            }
        )

    def bloco(desde: str) -> dict[str, Any]:
        g = br[br["_dr"] >= pd.Timestamp(desde)]
        validos = int(g["validos"].sum())
        munis = []
        for (uf, _mun), gm in g.groupby(["uf", "mun"]):
            vm = int(gm["validos"].sum())
            munis.append(
                {
                    "uf": str(uf).upper(),
                    "municipio": gm["municipio"].iloc[0],
                    "secoes": len(gm),
                    "validos": vm,
                    "lula_pct": pct(int(gm[f"v{LULA}"].sum()), vm),
                    "flavio_pct": pct(int(gm[f"v{FLAVIO}"].sum()), vm),
                    "tipos_local": sorted({str(t) for t in gm["tipo_inferido"]}),
                }
            )
        munis.sort(key=lambda r: -r["secoes"])
        return {
            "secoes": len(g),
            "validos": validos,
            "lula_pct": pct(int(g[f"v{LULA}"].sum()), validos),
            "flavio_pct": pct(int(g[f"v{FLAVIO}"].sum()), validos),
            "dif_zona_lula_pp": _dif_zona(g, "lula"),
            "dif_zona_flavio_pp": _dif_zona(g, "flavio"),
            "municipios": munis,
        }

    tarde = br[br["_dr"] >= pd.Timestamp("2026-10-05 00:00:00")].sort_values("_dr")
    return {
        "fonte": (
            "campo dr/hr do aux.json de cada seção (recebimento do boletim no TSE), "
            "como publicado; exterior fora"
        ),
        "secoes_sem_hora": int(br["_dr"].isna().sum()),
        "por_hora": por_hora,
        "depois_2200": bloco("2026-10-04 22:00:00"),
        "depois_0000": bloco("2026-10-05 00:00:00"),
        "depois_0100": bloco("2026-10-05 01:00:00"),
        "amostras": amostras(tarde, 40),
    }


def _qui2(obs: np.ndarray, esperado_prop: np.ndarray) -> tuple[float, int, float]:
    n = obs.sum()
    esp = esperado_prop * n
    chi2 = float(((obs - esp) ** 2 / esp).sum())
    gl = len(obs) - 1
    return chi2, gl, float(stats.chi2.sf(chi2, gl))


BENFORD2 = np.array(
    [sum(math.log10(1 + 1 / (10 * k + d)) for k in range(1, 10)) for d in range(10)]
)


def _ultimo_digito(df: pd.DataFrame) -> list[dict[str, Any]]:
    out = []
    for uf, g in [("BR", df), *((str(u).upper(), x) for u, x in df.groupby("uf"))]:
        for chave, num in CANDS:
            v = g[f"v{num}"].to_numpy()
            v = v[v >= 10]
            if len(v) < 50:
                continue
            obs = np.bincount(v % 10, minlength=10).astype(float)
            chi2, gl, p = _qui2(obs, np.full(10, 0.1))
            out.append(
                {
                    "uf": uf,
                    "candidato": chave,
                    "n": len(v),
                    "chi2": r2(chi2, 3),
                    "gl": gl,
                    "p": r2(p, 4),
                    "frequencias": [r2(x / len(v), 4) for x in obs],
                }
            )
    return out


def _benford2(df: pd.DataFrame) -> list[dict[str, Any]]:
    out = []
    for uf, g in [("BR", df), *((str(u).upper(), x) for u, x in df.groupby("uf"))]:
        for chave, num in CANDS:
            v = g[f"v{num}"].to_numpy()
            v = v[v >= 10]
            if len(v) < 50:
                continue
            segundo = np.array([int(str(int(x))[1]) for x in v])
            obs = np.bincount(segundo, minlength=10).astype(float)
            chi2, gl, p = _qui2(obs, BENFORD2)
            out.append(
                {
                    "uf": uf,
                    "candidato": chave,
                    "n": len(v),
                    "chi2": r2(chi2, 3),
                    "gl": gl,
                    "p": r2(p, 4),
                    "observado": [r2(x / len(v), 4) for x in obs],
                    "esperado": [r2(x, 4) for x in BENFORD2],
                }
            )
    return out
