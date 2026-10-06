"""Registros e agregados do capítulo 13: seção, local, município, zona, UF e mapa.

Recebe a base do universo já com as marcas dos critérios (`fiscais_criterios`) e
devolve os blocos do JSON do contrato `analysis/apuracao_2026/CONTRATO_FISCAIS.md`.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from . import fiscais_criterios as fc
from .fiscais_base import frase_explicacao, grupo_explicacao, normalizar
from .fiscais_regras import POR_ID
from .secoes_base import FLAVIO, LULA, TIPO_ARQUIVO, TIPO_URNA, hora_brasilia, r2

TOP_LOCAIS = 200
TOP_MUNICIPIOS = 100
N_DESTAQUES = 300
APERTADO_PP = 5.0


def _int(v: Any) -> int | None:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    return int(v)


def _txt(v: Any) -> str | None:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    s = str(v).strip()
    return s or None


def links(lat: Any, lon: Any) -> dict[str, str] | None:
    la, lo = r2(lat, 5), r2(lon, 5)
    if la is None or lo is None:
        return None
    return {
        "osm": f"https://www.openstreetmap.org/?mlat={la}&mlon={lo}#map=17/{la}/{lo}",
        "google": f"https://www.google.com/maps?q={la},{lo}",
    }


# ---------------------------------------------------------------- detalhe por critério


def detalhe(
    c: str, g: Callable[[str], Any], extra: Mapping[str, Any]
) -> dict[str, Any]:
    if c == "a":
        return {
            "candidato": g("a_cand"),
            "pct": r2(g("a_pct")),
            "excesso_zona_pp": r2(g("a_exc")),
            "pct_2022": r2(g("a_pct_2022")),
            "enclave_2022": bool(g("enclave_2022")),
        }
    if c == "b":
        return {"zerado": g("b_quem"), "votantes": _int(g("comparecimento"))}
    if c == "c":
        apt, comp = g("aptos"), g("comparecimento")
        return {
            "aptos": _int(apt),
            "comparecimento": _int(comp),
            "comparecimento_pct": r2(100 * comp / apt) if apt else None,
        }
    if c == "d":
        return {
            "encerramento_brasilia": hora_brasilia(g("encerramento"), g("fuso")),
            "excesso_zona_lula_pp": r2(g("d_exc")),
        }
    if c == "e":
        cl = g("_cluster")
        return {
            "posicao": _int(g("e_pos")),
            "loglik": r2(g("_loglik"), 3),
            "grupo": None if cl is None or math.isnan(cl) else int(cl) + 1,
            "grupo_rotulo": extra.get("rotulos_grupo", {}).get(_int(cl)),
        }
    if c == "f":
        ta, tu = _int(g("tipo_arquivo")), _int(g("tipo_urna"))
        return {
            "tipo_arquivo": TIPO_ARQUIVO.get(ta, ta) if ta is not None else None,
            "tipo_urna": TIPO_URNA.get(tu, tu) if tu is not None else None,
            "n_cargas": _int(g("n_cargas")),
            "dif_zona_lula_pp": r2(g("f_dif_lula")),
            "dif_zona_flavio_pp": r2(g("f_dif_flavio")),
        }
    if c == "g":
        return {"recebido_tse": _txt(g("dr_hr"))}
    if c == "h":
        tipo = g("h_tipo")
        out: dict[str, Any] = {"tipo": tipo}
        z = extra.get("congeladas", {}).get((g("uf"), g("mun"), _int(g("zona"))))
        if tipo == "zona_congelada" and z:
            out |= {
                "versao_parada_brasilia": z.get("ultima_incompleta_brasilia"),
                "horas_parada": z.get("horas_parada"),
                "secoes_faltando_na_zona": z.get("secoes_faltando"),
            }
        if tipo == "sem_arquivo":
            out["status_aux"] = g("status_aux")
        return out
    if c == "i":
        z = extra.get("topo", {}).get((g("uf"), g("mun"), _int(g("zona")))) or {}
        return {
            "posicao_zona": z.get("posicao"),
            "escore_zona": z.get("escore"),
            "excesso_uf_lula_pp": r2(g("i_exc_lula")),
            "excesso_uf_flavio_pp": r2(g("i_exc_flavio")),
        }
    if c == "j":
        return {
            "variacao_margem_pp": r2(g("j_swing")),
            "media_uf_pp": r2(g("j_media")),
            "dp_uf_pp": r2(g("j_dp")),
            "z": r2(g("j_z")),
        }
    if c == "k":
        out = {}
        for parte in ("brancos", "nulos"):
            if g(f"k_{parte}"):
                out[parte] = {
                    "pct": r2(g(f"k_{parte}_pct")),
                    "media_zona_pct": r2(g(f"k_{parte}_media")),
                    "z": r2(g(f"k_{parte}_z")),
                }
        return out
    if c == "l":
        return {"secoes_sinalizadas_no_local": _int(g("l_n"))}
    return {}


def o_que_conferir(criterios: Sequence[str]) -> str:
    vistos: list[str] = []
    for c in criterios:
        t = POR_ID[c]["o_que_conferir"]
        if t not in vistos:
            vistos.append(t)
    return "; ".join(vistos)


# ---------------------------------------------------------------- seção


def secao_fiscal(
    linha: Mapping[str, Any], extra: Mapping[str, Any], risco: Mapping[str, Any] | None
) -> dict[str, Any]:
    g = linha.get
    sem = g("h_tipo") == "sem_arquivo"
    crits = list(g("criterios") or [])
    cods = list(g("explicacao_codigos") or [])
    lp, fp = g("lula_pct"), g("flavio_pct")
    lat, lon = g("lat"), g("lon")
    ctx = extra.get("contexto", {}).get(
        (str(g("uf")).upper(), normalizar(g("municipio"))), []
    )
    mesma = bool(g("mesma_secao")) if not sem else False
    return {
        "uf": str(g("uf")).upper(),
        "regiao": g("regiao"),
        "municipio": g("municipio"),
        "mun_tse": g("mun"),
        "ibge": g("ibge") if isinstance(g("ibge"), str) else None,
        "zona": _int(g("zona")),
        "secao": _int(g("secao")),
        "local_id": g("local_id"),
        "local_nr": _int(g("local_nr")),
        "local": _txt(g("local")),
        "endereco": _txt(g("endereco")),
        "bairro": _txt(g("bairro")),
        "cep": _txt(g("cep")),
        "lat": r2(lat, 5),
        "lon": r2(lon, 5),
        "tipo_local_tse": _txt(g("tipo_local")),
        "tipo_local_inferido": g("tipo_inferido"),
        "aptos": _int(g("aptos")),
        "votantes": None if sem else _int(g("comparecimento")),
        "validos": None if sem else _int(g("validos")),
        "brancos": None if sem else _int(g("brancos")),
        "nulos": None if sem else _int(g("nulos")),
        "lula": None if sem else _int(g(f"v{LULA}")),
        "flavio": None if sem else _int(g(f"v{FLAVIO}")),
        "lula_pct": r2(lp),
        "flavio_pct": r2(fp),
        "zona_lula_pct": r2(g("zona_lula_pct")),
        "zona_flavio_pct": r2(g("zona_flavio_pct")),
        "excesso_zona_lula_pp": r2(_menos(lp, g("zona_resto_lula_pct"))),
        "excesso_zona_flavio_pp": r2(_menos(fp, g("zona_resto_flavio_pct"))),
        "uf_lula_pct": r2(g("uf_lula_pct")),
        "uf_flavio_pct": r2(g("uf_flavio_pct")),
        "modelo_urna": _txt(g("modelo_urna")),
        "tipo_urna": _int(g("tipo_urna")),
        "tipo_arquivo": _int(g("tipo_arquivo")),
        "n_cargas": _int(g("n_cargas")),
        "abertura_brasilia": hora_brasilia(g("abertura"), g("fuso")),
        "encerramento_brasilia": hora_brasilia(g("encerramento"), g("fuso")),
        "recebido_tse": _txt(g("dr_hr")),
        "casada_2022": mesma,
        "lula_2022_pct": r2(g("lula22_pct")) if mesma else None,
        "flavio_2022_pct": r2(g("bolso22_pct")) if mesma else None,
        "criterios": crits,
        "detalhe": {c: detalhe(c, g, extra) for c in crits},
        "pontuacao": int(g("pontuacao")),
        "pontuacao_iguais": int(g("pontuacao_iguais")),
        "nivel": g("nivel"),
        "nivel_iguais": g("nivel_iguais"),
        "grupo_explicacao": grupo_explicacao(cods),
        "explicacao_codigos": cods,
        "explicacao_provavel": frase_explicacao(cods),
        "enclave_2022": bool(g("enclave_2022")),
        "sem_boletim": sem,
        "o_que_conferir": o_que_conferir(crits),
        "contexto": [c["id"] for c in ctx],
        "risco": dict(risco) if risco is not None else None,
        "link_mapa": links(lat, lon),
    }


def _menos(a: Any, b: Any) -> float | None:
    if a is None or b is None:
        return None
    try:
        v = float(a) - float(b)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(v) else v


def ordenar(df: pd.DataFrame) -> pd.DataFrame:
    chave = df["nivel"].map(fc.ORDEM_NIVEL).fillna(9)
    return (
        df.assign(_o=chave, _a=-df["aptos"].fillna(0), _p=-df["pontuacao"])
        .sort_values(["_o", "_p", "_a", "uf", "mun", "zona", "secao"], kind="stable")
        .drop(columns=["_o", "_a", "_p"])
    )


# ---------------------------------------------------------------- agregados


def _contar(lista: Sequence[Sequence[str]]) -> dict[str, int]:
    out = dict.fromkeys(fc.IDS, 0)
    for cs in lista:
        for c in cs:
            out[c] += 1
    return {k: v for k, v in out.items() if v}


def _niveis(s: pd.Series) -> dict[str, int]:
    vc = s.value_counts()
    return {n: int(vc.get(n, 0)) for n in fc.NIVEIS}


def por_uf(sin: pd.DataFrame, todos: pd.DataFrame) -> list[dict[str, Any]]:
    tot = todos.groupby("uf").size()
    out = []
    for uf, g in sin.groupby("uf"):
        nv = _niveis(g["nivel"])
        out.append(
            {
                "uf": str(uf).upper(),
                "regiao": (
                    g["regiao"].dropna().iloc[0] if g["regiao"].notna().any() else None
                ),
                "secoes_universo": int(tot.get(uf, 0)),
                "secoes": len(g),
                **nv,
                "locais": int(g["local_id"].nunique()),
                "locais_alta": int(g.loc[g["nivel"] == "alta", "local_id"].nunique()),
                "aptos_secoes": int(g["aptos"].fillna(0).sum()),
                "pontuacao_soma": int(g["pontuacao"].sum()),
                "criterios": _contar(g["criterios"]),
            }
        )
    out.sort(key=lambda r: -r["pontuacao_soma"])
    return out


def municipios_universo(todos: pd.DataFrame) -> pd.DataFrame:
    g = todos.groupby(["uf", "mun"])
    m = g[[f"v{LULA}", f"v{FLAVIO}", "validos"]].sum()
    m["secoes_universo"] = g.size()
    with np.errstate(divide="ignore", invalid="ignore"):
        m["lula_pct"] = 100 * m[f"v{LULA}"] / m["validos"]
        m["flavio_pct"] = 100 * m[f"v{FLAVIO}"] / m["validos"]
    m["margem_flavio_pp"] = m["flavio_pct"] - m["lula_pct"]
    return m


def municipios_sinalizados(
    sin: pd.DataFrame, mun_u: pd.DataFrame, contexto: Mapping[tuple[str, str], list]
) -> list[dict[str, Any]]:
    """Todos os municípios com ao menos uma seção sinalizada."""
    linhas = []
    for (uf, mun), g in sin.groupby(["uf", "mun"]):
        u = mun_u.loc[(uf, mun)] if (uf, mun) in mun_u.index else None
        nome = g["municipio"].dropna().iloc[0] if g["municipio"].notna().any() else None
        ctx = contexto.get((str(uf).upper(), normalizar(nome)), [])
        linhas.append(
            {
                "uf": str(uf).upper(),
                "municipio": nome,
                "mun_tse": mun,
                "ibge": next((x for x in g["ibge"] if isinstance(x, str)), None),
                "secoes_universo": (
                    _int(u["secoes_universo"]) if u is not None else None
                ),
                "secoes": len(g),
                **_niveis(g["nivel"]),
                "locais": int(g["local_id"].nunique()),
                "aptos_secoes": int(g["aptos"].fillna(0).sum()),
                "pontuacao_soma": int(g["pontuacao"].sum()),
                "lula_pct": r2(u["lula_pct"]) if u is not None else None,
                "flavio_pct": r2(u["flavio_pct"]) if u is not None else None,
                "margem_flavio_pp": (
                    r2(u["margem_flavio_pp"]) if u is not None else None
                ),
                "criterios": _contar(g["criterios"]),
                "contexto": [{"id": c["id"], "tema": c["tema"]} for c in ctx],
            }
        )
    return linhas


def por_municipio(linhas: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """União dos 100 primeiros por pontuação somada e por número de seções."""
    por_p = sorted(linhas, key=lambda r: (-r["pontuacao_soma"], -r["secoes"]))
    por_s = sorted(linhas, key=lambda r: (-r["secoes"], -r["pontuacao_soma"]))
    pos_p = {(r["uf"], r["mun_tse"]): i + 1 for i, r in enumerate(por_p)}
    pos_s = {(r["uf"], r["mun_tse"]): i + 1 for i, r in enumerate(por_s)}
    escolhidos = {(r["uf"], r["mun_tse"]) for r in por_p[:TOP_MUNICIPIOS]}
    escolhidos |= {(r["uf"], r["mun_tse"]) for r in por_s[:TOP_MUNICIPIOS]}
    out = []
    for r0 in por_p:
        k = (r0["uf"], r0["mun_tse"])
        if k not in escolhidos:
            continue
        r = dict(r0) | {
            "top_pontuacao": pos_p[k] <= TOP_MUNICIPIOS,
            "top_secoes": pos_s[k] <= TOP_MUNICIPIOS,
            "posicao_pontuacao": pos_p[k],
            "posicao_secoes": pos_s[k],
        }
        out.append(r)
    return out


def por_zona(
    sin: pd.DataFrame,
    todos: pd.DataFrame,
    topo: Mapping[tuple[str, str, int], Any],
    congeladas: Mapping[tuple[str, str, int], Any],
) -> list[dict[str, Any]]:
    tot = todos.groupby(["uf", "mun", "zona"]).size()
    out = []
    for (uf, mun, zona), g in sin.groupby(["uf", "mun", "zona"]):
        k = (uf, mun, int(zona))
        out.append(
            {
                "uf": str(uf).upper(),
                "municipio": (
                    g["municipio"].dropna().iloc[0]
                    if g["municipio"].notna().any()
                    else None
                ),
                "mun_tse": mun,
                "zona": int(zona),
                "secoes_universo": int(tot.get((uf, mun, zona), 0)),
                "secoes": len(g),
                **_niveis(g["nivel"]),
                "pontuacao_soma": int(g["pontuacao"].sum()),
                "aptos_secoes": int(g["aptos"].fillna(0).sum()),
                "posicao_anomalias": (topo.get(k) or {}).get("posicao"),
                "congelada": k in congeladas,
            }
        )
    out.sort(key=lambda r: (-r["pontuacao_soma"], -r["secoes"]))
    return out


def locais_universo(todos: pd.DataFrame) -> pd.DataFrame:
    g = todos.groupby("local_id")
    m = g[[f"v{LULA}", f"v{FLAVIO}", "validos", "aptos"]].sum()
    m["secoes_local"] = g.size()
    with np.errstate(divide="ignore", invalid="ignore"):
        m["lula_pct"] = 100 * m[f"v{LULA}"] / m["validos"]
        m["flavio_pct"] = 100 * m[f"v{FLAVIO}"] / m["validos"]
    return m


def por_local(
    sin: pd.DataFrame,
    loc_u: pd.DataFrame,
    contexto: Mapping[tuple[str, str], list],
    riscos: Mapping[str, Any],
) -> list[dict[str, Any]]:
    out = []
    for lid, g in sin.groupby("local_id", sort=False):
        p = g.iloc[0]
        u = loc_u.loc[lid] if lid in loc_u.index else None
        nv = _niveis(g["nivel"])
        nivel = next((n for n in fc.NIVEIS if nv[n]), None)
        ctx = contexto.get((str(p["uf"]).upper(), normalizar(p["municipio"])), [])
        out.append(
            {
                "local_id": lid,
                "uf": str(p["uf"]).upper(),
                "municipio": p["municipio"],
                "mun_tse": p["mun"],
                "ibge": p["ibge"] if isinstance(p["ibge"], str) else None,
                "zona": int(p["zona"]),
                "local_nr": _int(p["local_nr"]),
                "local": _txt(p["local"]),
                "endereco": _txt(p["endereco"]),
                "bairro": _txt(p["bairro"]),
                "cep": _txt(p["cep"]),
                "lat": r2(p["lat"], 5),
                "lon": r2(p["lon"], 5),
                "tipo_local_inferido": p["tipo_inferido"],
                "secoes_local": _int(u["secoes_local"]) if u is not None else len(g),
                "secoes": len(g),
                "lista_secoes": sorted(int(s) for s in g["secao"]),
                **nv,
                "nivel": nivel,
                "pontuacao_soma": int(g["pontuacao"].sum()),
                "pontuacao_max": int(g["pontuacao"].max()),
                "aptos_local": _int(u["aptos"]) if u is not None else None,
                "aptos_secoes": int(g["aptos"].fillna(0).sum()),
                "lula_pct": r2(u["lula_pct"]) if u is not None else None,
                "flavio_pct": r2(u["flavio_pct"]) if u is not None else None,
                "criterios": _contar(g["criterios"]),
                "contexto": [c["id"] for c in ctx],
                "risco": riscos.get(lid),
                "link_mapa": links(p["lat"], p["lon"]),
            }
        )
    out.sort(
        key=lambda r: (
            fc.ORDEM_NIVEL.get(r["nivel"], 9),
            -r["pontuacao_soma"],
            -r["secoes"],
            r["local_id"],
        )
    )
    return out


# ---------------------------------------------------------------- prioridade do PL


def _local_curto(r: Mapping[str, Any]) -> dict[str, Any]:
    return {
        k: r.get(k)
        for k in (
            "local_id",
            "uf",
            "municipio",
            "zona",
            "local",
            "endereco",
            "bairro",
            "lat",
            "lon",
            "secoes",
            "nivel",
            "pontuacao_soma",
        )
    }


def _mun_curto(r: Mapping[str, Any]) -> dict[str, Any]:
    return {
        k: r.get(k)
        for k in (
            "uf",
            "municipio",
            "mun_tse",
            "secoes",
            "alta",
            "media",
            "pontuacao_soma",
            "flavio_pct",
            "lula_pct",
        )
    }


def prioridade_pl(
    sin: pd.DataFrame,
    locais: Sequence[Mapping[str, Any]],
    municipios_todos: Sequence[Mapping[str, Any]],
    mun_u: pd.DataFrame,
) -> dict[str, Any]:
    idx_local = {r["local_id"]: r for r in locais}
    idx_mun = {(r["uf"], r["mun_tse"]): r for r in municipios_todos}
    geral_l = sorted(
        locais,
        key=lambda r: (
            fc.ORDEM_NIVEL.get(r["nivel"], 9),
            -r["pontuacao_soma"],
            -r["secoes"],
        ),
    )
    geral_m = sorted(
        municipios_todos,
        key=lambda r: (-r["alta"], -r["media"], -r["pontuacao_soma"], -r["secoes"]),
    )

    marg = (
        sin[["uf", "mun"]]
        .merge(mun_u["margem_flavio_pp"].reset_index(), on=["uf", "mun"], how="left")[
            "margem_flavio_pp"
        ]
        .to_numpy()
    )
    elegivel = np.nan_to_num(marg, nan=-999) >= -APERTADO_PP
    pf = sin[elegivel].assign(
        _ind=lambda d: d["pontuacao"].to_numpy(float)
        * d["aptos"].fillna(0).to_numpy(float)
    )
    exc = (
        (sin["lula_pct"] - sin["zona_resto_lula_pct"]) * sin["validos"] / 100
    ).to_numpy(float)
    vl = sin[np.nan_to_num(exc, nan=-1) > 0].assign(
        _exc=exc[np.nan_to_num(exc, nan=-1) > 0]
    )

    def top_local(d: pd.DataFrame, col: str, nome: str) -> list[dict[str, Any]]:
        s = (
            d.groupby("local_id")[col]
            .sum()
            .sort_values(ascending=False)
            .head(TOP_LOCAIS)
        )
        return [
            _local_curto(idx_local[k]) | {nome: r2(v, 1)}
            for k, v in s.items()
            if k in idx_local
        ]

    def top_mun(d: pd.DataFrame, col: str, nome: str) -> list[dict[str, Any]]:
        s = (
            d.groupby(["uf", "mun"])[col]
            .sum()
            .sort_values(ascending=False)
            .head(TOP_MUNICIPIOS)
        )
        out = []
        for (uf, mun), v in s.items():
            r = idx_mun.get((str(uf).upper(), mun))
            if r is not None:
                out.append(_mun_curto(r) | {nome: r2(v, 1)})
        return out

    n_eleg = int(
        (
            np.nan_to_num(mun_u["margem_flavio_pp"].to_numpy(float), nan=-999)
            >= -APERTADO_PP
        ).sum()
    )
    return {
        "leitura": (
            "Fiscal evita erro e intimidação dos dois lados: a mesma presença que protege "
            "o voto de Flávio onde ele é competitivo vigia a seção em que Lula aparece "
            "muito acima das vizinhas. Os três rankings usam as mesmas seções sinalizadas; "
            "mudam só o peso e o recorte. Nenhum deles é acusação."
        ),
        "geral": {
            "criterio": (
                "locais: nível do local (o mais alto entre as seções) e depois pontuação "
                "somada; municípios: seções de nível alta, depois média, depois pontuação "
                "somada"
            ),
            "locais": [_local_curto(r) for r in geral_l[:TOP_LOCAIS]],
            "municipios": [_mun_curto(r) for r in geral_m[:TOP_MUNICIPIOS]],
        },
        "protege_flavio": {
            "criterio": (
                "soma de pontuação × aptos das seções sinalizadas em municípios onde "
                f"Flávio venceu ou perdeu por até {APERTADO_PP:.0f} pontos dos válidos"
            ),
            "regra_municipio": (
                f"Flávio venceu ou perdeu por até {APERTADO_PP:.0f} pp dos válidos no "
                "município (universo do capítulo)"
            ),
            "municipios_elegiveis": n_eleg,
            "secoes": len(pf),
            "aptos": int(pf["aptos"].fillna(0).sum()),
            "locais": top_local(pf, "_ind", "indice"),
            "municipios": top_mun(pf, "_ind", "indice"),
        },
        "vigia_lula": {
            "criterio": (
                "votos de Lula acima do resto da zona: (Lula % na seção menos Lula % no "
                "resto da zona) × válidos / 100, somados nas seções sinalizadas"
            ),
            "secoes": len(vl),
            "excesso_votos_lula": r2(vl["_exc"].sum(), 0),
            "locais": top_local(vl, "_exc", "excesso_votos_lula"),
            "municipios": top_mun(vl, "_exc", "excesso_votos_lula"),
        },
    }


# ---------------------------------------------------------------- sensibilidade


def sensibilidade(
    sin: pd.DataFrame, locais: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    matriz = []
    for a in fc.NIVEIS:
        for b in fc.NIVEIS:
            n = int(((sin["nivel"] == a) & (sin["nivel_iguais"] == b)).sum())
            matriz.append({"nivel_pesos": a, "nivel_iguais": b, "secoes": n})
    muda = int((sin["nivel"] != sin["nivel_iguais"]).sum())
    rho = stats.spearmanr(sin["pontuacao"], sin["pontuacao_iguais"]).statistic
    top_p = {
        r["local_id"] for r in sorted(locais, key=lambda r: -r["pontuacao_soma"])[:100]
    }
    soma_ig = (
        sin.groupby("local_id")["pontuacao_iguais"].sum().sort_values(ascending=False)
    )
    top_i = set(soma_ig.head(100).index)
    mp = sin.groupby(["uf", "mun"])["pontuacao"].sum().sort_values(ascending=False)
    mi = (
        sin.groupby(["uf", "mun"])["pontuacao_iguais"]
        .sum()
        .sort_values(ascending=False)
    )
    comum_m = len(set(mp.head(100).index) & set(mi.head(100).index))
    return {
        "regra": (
            "pesos iguais: cada critério vale 1; alta com "
            f"{fc.CORTE_ALTA_IGUAIS} critérios ou mais, média com {fc.CORTE_MEDIA_IGUAIS}, "
            "mesma regra de explicação comum e de enclave"
        ),
        "matriz": matriz,
        "mudam_nivel": muda,
        "mudam_nivel_pct": r2(100 * muda / len(sin)) if len(sin) else None,
        "spearman_pontuacao": r2(rho, 3),
        "top100_locais_comum": len(top_p & top_i),
        "top100_municipios_comum": comum_m,
    }


# ---------------------------------------------------------------- resumo e mapa


def resumo(
    sin: pd.DataFrame,
    todos: pd.DataFrame,
    loc_u: pd.DataFrame,
    n_universo: int,
) -> dict[str, Any]:
    por_nivel = {}
    for n in fc.NIVEIS:
        g = sin[sin["nivel"] == n]
        ids = g["local_id"].unique()
        por_nivel[n] = {
            "secoes": len(g),
            "locais": len(ids),
            "municipios": int(g[["uf", "mun"]].drop_duplicates().shape[0]),
            "aptos": int(g["aptos"].fillna(0).sum()),
            "aptos_locais": int(loc_u.reindex(ids)["aptos"].fillna(0).sum()),
        }
    am = sin[sin["nivel"].isin(["alta", "media"])]
    locais_todos = sin["local_id"].unique()
    apt_u = int(todos["aptos"].fillna(0).sum())
    apt_s = int(sin["aptos"].fillna(0).sum())
    apt_l = int(loc_u.reindex(locais_todos)["aptos"].fillna(0).sum())
    codigos = pd.Series([c for cs in sin["explicacao_codigos"] for c in cs])
    baixa = sin[sin["nivel"] == "baixa"]
    aldeia_presidio = baixa["explicacao_codigos"].map(
        lambda cs: "aldeia" in cs or "presidio" in cs
    )
    return {
        "secoes_universo": n_universo,
        "secoes_sinalizadas": len(sin),
        "por_nivel": por_nivel,
        "por_criterio": {
            c: int(sum(c in cs for cs in sin["criterios"])) for c in fc.IDS
        },
        "eleitorado": {
            "aptos_universo": apt_u,
            "aptos_sinalizadas": apt_s,
            "pct_sinalizadas": r2(100 * apt_s / apt_u) if apt_u else None,
            "aptos_locais_sinalizados": apt_l,
            "pct_locais": r2(100 * apt_l / apt_u) if apt_u else None,
        },
        "fiscais": {
            "um_por_local": {
                "alta": por_nivel["alta"]["locais"],
                "alta_media": int(am["local_id"].nunique()),
                "todos": len(locais_todos),
            },
            "um_por_secao": {
                "alta": por_nivel["alta"]["secoes"],
                "alta_media": len(am),
                "todos": len(sin),
            },
            "dois_por_secao_maximo_legal": {
                "alta": 2 * por_nivel["alta"]["secoes"],
                "alta_media": 2 * len(am),
                "todos": 2 * len(sin),
            },
            "base_legal": (
                "Lei 9.504/1997, art. 65, § 1º (um fiscal pode cobrir mais de uma seção "
                "no mesmo local) e § 4º (até dois fiscais de cada partido por seção), "
                "como registrado em fechamento.json, fontes_legais"
            ),
        },
        "explicacao_comum": {
            "secoes": int(sin["comum"].sum()),
            "por_codigo": {k: int(v) for k, v in codigos.value_counts().items()},
            "baixa_aldeia_presidio": int(aldeia_presidio.sum()),
            "baixa": len(baixa),
        },
        "enclaves_2022": int(sin["enclave_2022"].sum()),
        "sem_coordenada": {
            "secoes": int(sin["lat"].isna().sum()),
            "locais": int(sin.loc[sin["lat"].isna(), "local_id"].nunique()),
        },
    }


def mapa(locais: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    pontos = []
    sem = 0
    for i, r in enumerate(locais):
        if r["lat"] is None or r["lon"] is None:
            sem += 1
            continue
        risco = (r.get("risco") or {}).get("nivel_risco_fiscal")
        pontos.append(
            [r["lat"], r["lon"], r["nivel"], r["secoes"], r["pontuacao_soma"], i, risco]
        )
    return {
        "colunas": ["lat", "lon", "nivel", "n_secoes", "pontuacao", "local", "risco"],
        "pontos": pontos,
        "n_locais": len(locais),
        "n_sem_coordenada": sem,
        "tiles": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        "zoom_detalhe": 17,
    }
