"""Montagem dos pares de locais, resumos e gravação das saídas (JSON, CSV, Politize)."""

from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from mudancas_secoes_2t import distancia as di
from mudancas_secoes_2t import externos as ex
from mudancas_secoes_2t import textos as tx

ROOT = Path(__file__).resolve().parents[2]
ANALISE = ROOT / "analysis/mudancas_secoes_2t"
PUBLICO = ROOT / "docs/assets/mudancas_secoes"
POLITIZE = ROOT / "docs/assets/politize/dados/mudancas"
PAR = ["uf", "mun", "zona", "local_1t", "local_2t"]
VERSAO_POLITIZE = "1.0"
COMPOSICAO = [
    "aptos",
    "comparecimento",
    "flavio",
    "lula",
    "terceira",
    "brancos",
    "nulos",
]


def _f(x: Any, casas: int | None = None) -> Any:
    """Valor JSON: ``NaN`` vira ``None``; numpy vira Python."""
    if x is None:
        return None
    if isinstance(x, (np.floating, float)):
        if not np.isfinite(x):
            return None
        return round(float(x), casas) if casas is not None else float(x)
    if isinstance(x, np.integer):
        return int(x)
    if isinstance(x, np.bool_):
        return bool(x)
    return x


def registros(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Linhas do quadro como dicionários com chave texto (tipagem simples)."""
    return [{str(k): v for k, v in r.items()} for r in df.to_dict("records")]


def id_clima(uf: str, mun: str, zona: int, local: int) -> str:
    return f"{uf}-{mun}-{int(zona)}-{int(local)}"


def _consulta(nome: str, endereco: str, municipio: str, uf: str) -> str:
    return ", ".join(
        x for x in (nome, endereco, municipio, uf) if isinstance(x, str) and x
    )


def coordenada_publicavel(lat: Any, lon: Any, repetida: bool) -> tuple[Any, Any]:
    if repetida or lat is None or pd.isna(lat):
        return None, None
    return lat, lon


def montar_pares(
    cls: pd.DataFrame,
    urnas: pd.DataFrame,
    clima: dict[str, Any] | None,
    tre: dict[tuple, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Um item por par origem→destino, para toda seção com alguma alteração (A a H)."""
    sec = cls[cls["categoria"] != "Z"]
    u = urnas[urnas["categoria"] != "Z"].copy()
    u = u[u["tem_bu"]]
    agg_u = u.groupby(PAR).agg(
        **{c: (c, "sum") for c in COMPOSICAO},
        bateria=("bateria", "sum"),
        bateria_votacao=("bateria_votacao", "sum"),
        reinicios=("reinicio", "sum"),
        atencao_max=("atencao", "max"),
        abertura_min_atrasada=("abertura_atrasada", "sum"),
        fila_fechamento=("fila_fechamento", "sum"),
        codigos=("codigos", lambda s: sorted({c for x in s for c in x})),
    )
    por_par: dict[Any, dict[str, Any]] = {
        k: {str(c): x for c, x in v.items()} for k, v in agg_u.to_dict("index").items()
    }
    pares = []
    for chave, g in sec.groupby(PAR, sort=True):
        r = g.iloc[0]
        cats = g["categoria"].value_counts()
        a = por_par.get(chave)
        lat1, lon1 = coordenada_publicavel(
            r["lat_1t"], r["lon_1t"], r["coord_repetida_1t"]
        )
        lat2, lon2 = coordenada_publicavel(
            r["lat_2t"], r["lon_2t"], r["coord_repetida_2t"]
        )
        rota = None if r["distancia_suspeita"] else di.maps_rota(lat1, lon1, lat2, lon2)
        item: dict[str, Any] = {
            "uf": r["uf"],
            "mun_tse": r["mun"],
            "municipio": r["municipio"],
            "zona": int(r["zona"]),
            "local_1t": int(r["local_1t"]),
            "nome_1t": r["nome_1t"],
            "end_1t": r["endereco_1t"],
            "bairro_1t": r["bairro_1t"],
            "lat_1t": _f(r["lat_1t"]),
            "lon_1t": _f(r["lon_1t"]),
            "local_2t": int(r["local_2t"]),
            "nome_2t": r["nome_2t"],
            "end_2t": r["endereco_2t"],
            "bairro_2t": r["bairro_2t"],
            "cep_2t": r["cep_2t"],
            "lat_2t": _f(r["lat_2t"]),
            "lon_2t": _f(r["lon_2t"]),
            "distancia_m": _f(r["distancia_m"], 0),
            "distancia_suspeita": bool(r["distancia_suspeita"]),
            "coord_repetida": bool(r["coord_repetida"]),
            "coord_suspeita": bool(g["coord_suspeita"].any()),
            "categoria": cats.index[0],
            "mudanca_real": bool(g["mudanca_real"].any()),
            "confianca": r["confianca"],
            "motivo_classificacao": r["motivo_classificacao"],
            "secoes": sorted(int(x) for x in g["secao"]),
            "eleitores": int(g["eleitores_2t"].sum()),
        }
        item.update(_composicao(a))
        item["logs_1t"] = (
            None
            if a is None
            else {
                "bateria": int(a["bateria"]),
                "bateria_votacao": int(a["bateria_votacao"]),
                "reinicios": int(a["reinicios"]),
                "atencao_max": _f(a["atencao_max"]),
                "codigos": list(a["codigos"]),
            }
        )
        item["abertura_min_atrasada"] = (
            None if a is None else int(a["abertura_min_atrasada"])
        )
        item["fila_fechamento"] = None if a is None else int(a["fila_fechamento"])
        item["clima"] = ex.clima_local(
            clima, id_clima(r["uf"], r["mun"], r["zona"], r["local_1t"])
        )
        m = tre.get(
            (r["uf"], r["mun"], int(r["zona"]), int(r["local_1t"]), int(r["local_2t"]))
        )
        item["motivo_tre"] = m
        item["maps_novo"] = di.maps_novo(
            lat2,
            lon2,
            _consulta(r["nome_2t"], r["endereco_2t"], r["municipio"], r["uf"]),
        )
        item["maps_rota"] = rota
        pares.append(item)
    return pares


def _composicao(a: dict[str, Any] | None) -> dict[str, Any]:
    if a is None or not a["aptos"]:
        vazio = dict.fromkeys(
            [
                "aptos_1t",
                "comparecimento_1t",
                "abst_1t_pct",
                "flavio_1t",
                "lula_1t",
                "terceira_1t",
                "brancos",
                "nulos",
                "flavio_v",
                "lula_v",
                "margem_v",
            ]
        )
        return vazio
    val = a["flavio"] + a["lula"] + a["terceira"]
    fv = a["flavio"] / val * 100 if val else None
    lv = a["lula"] / val * 100 if val else None
    return {
        "aptos_1t": int(a["aptos"]),
        "comparecimento_1t": int(a["comparecimento"]),
        "abst_1t_pct": round(float((1 - a["comparecimento"] / a["aptos"]) * 100), 2),
        "flavio_1t": int(a["flavio"]),
        "lula_1t": int(a["lula"]),
        "terceira_1t": int(a["terceira"]),
        "brancos": int(a["brancos"]),
        "nulos": int(a["nulos"]),
        "flavio_v": _f(fv, 2),
        "lula_v": _f(lv, 2),
        "margem_v": _f(None if fv is None else fv - lv, 2),
    }


def resumo(cls: pd.DataFrame, urnas: pd.DataFrame) -> dict[str, Any]:
    por_cad = cls.groupby("categoria_cadastro")["eleitores_2t"].agg(["size", "sum"])
    por_ef = cls.groupby(["categoria", "mudanca_real"])["eleitores_2t"].agg(
        ["size", "sum"]
    )
    mr = cls[cls["mudanca_real"]]
    ok = di.distancia_valida(mr)
    u_mr = urnas[urnas["mudanca_real"] & urnas["tem_bu"]]
    g = cls[(cls["categoria"] == "G")]
    g_sens = g[di.distancia_valida(g)]
    return {
        "secoes_total": len(cls),
        "eleitores_total": int(cls["eleitores_2t"].sum()),
        "por_categoria_cadastro": {
            c: {
                "secoes": int(por_cad.loc[c, "size"]),
                "eleitores": int(por_cad.loc[c, "sum"]),
            }
            for c in por_cad.index
        },
        "por_categoria_efetiva": [
            {
                "categoria": c,
                "mudanca_real": bool(m),
                "secoes": int(v["size"]),
                "eleitores": int(v["sum"]),
            }
            for c, m, v in zip(
                por_ef.index.get_level_values(0),
                por_ef.index.get_level_values(1),
                registros(por_ef),
                strict=True,
            )
        ],
        "mudanca_real": {
            "secoes": len(mr),
            "secoes_principais": int((~mr["agregada"]).sum()),
            "secoes_agregadas": int(mr["agregada"].sum()),
            "locais_origem": int(
                mr[["uf", "mun", "zona", "local_1t"]].drop_duplicates().shape[0]
            ),
            "locais_destino": int(
                mr[["uf", "mun", "zona", "local_2t"]].drop_duplicates().shape[0]
            ),
            "pares": int(mr[PAR].drop_duplicates().shape[0]),
            "municipios": int(mr[["uf", "mun"]].drop_duplicates().shape[0]),
            "ufs": int(mr["uf"].nunique()),
            "eleitores": int(mr["eleitores_2t"].sum()),
            "aptos_1t": int(u_mr["aptos"].sum()),
            "distancia_mediana_m": _f(mr.loc[ok, "distancia_m"].median(), 0),
            "distancia_p90_m": _f(mr.loc[ok, "distancia_m"].quantile(0.9), 0),
            "secoes_com_distancia": int(ok.sum()),
            "por_categoria": {
                c: {
                    "secoes": int((mr["categoria"] == c).sum()),
                    "eleitores": int(
                        mr.loc[mr["categoria"] == c, "eleitores_2t"].sum()
                    ),
                }
                for c in sorted(mr["categoria"].unique())
            },
            "confianca_media": {
                "secoes": int((mr["confianca"] == "media").sum()),
                "eleitores": int(
                    mr.loc[mr["confianca"] == "media", "eleitores_2t"].sum()
                ),
                "nota": "E com outro logradouro e D com endereço igual depois da normalização",
            },
        },
        "fora_do_original": {
            "secoes_1t": int(cls["temp_1t_cadastro"].sum()),
            "eleitores_1t": int(cls.loc[cls["temp_1t_cadastro"], "eleitores_2t"].sum()),
            "secoes_2t": int(cls["temp_2t_cadastro"].sum()),
            "eleitores_2t": int(cls.loc[cls["temp_2t_cadastro"], "eleitores_2t"].sum()),
            "urnas_1t": int((~cls["agregada"] & cls["temp_1t"]).sum()),
            "urnas_2t": int((~cls["agregada"] & cls["temp_2t"]).sum()),
            "nota": "secoes_* contam o registro de cada seção como o TSE publica; urnas_* "
            "contam a seção principal (onde a agregada vota).",
        },
        "sensibilidade": {
            "g_se_contasse": {
                "secoes": len(g_sens),
                "eleitores": int(g_sens["eleitores_2t"].sum()),
                "nota": "G com coordenada nos dois turnos, até 50 km e sem coordenada "
                "repetida; nome e endereço iguais, por isso fora da mudança real",
            },
            "g_coordenada_so_em_um_turno": int((g["distancia_m"].isna()).sum()),
            "f_nome_de_outra_instituicao": {
                "secoes": int((cls["revisar"] & (cls["categoria"] == "F")).sum()),
                "eleitores": int(
                    cls.loc[
                        cls["revisar"] & (cls["categoria"] == "F"), "eleitores_2t"
                    ].sum()
                ),
                "nota": "só o nome mudou, para o de outra instituição, com endereço igual; "
                "fora da mudança real, listado para conferência",
            },
            "abcx_mesmo_predio": {
                "secoes": int(
                    (cls["categoria"].isin(list("ABCX")) & ~cls["mudanca_real"]).sum()
                ),
                "nota": "outro número de local com nome e endereço iguais",
            },
            "agregadas_herdam_mudanca": int(cls["herdada"].sum()),
        },
    }


def por_uf(
    cls: pd.DataFrame, notas: dict[str, list], painel: pd.DataFrame | None
) -> list:
    out = []
    pp = painel["uf"].value_counts() if painel is not None else pd.Series(dtype=int)
    for uf, g in cls.groupby("uf"):
        cad = g.groupby("categoria_cadastro")["eleitores_2t"].agg(["size", "sum"])
        mr = g[g["mudanca_real"]]
        out.append(
            {
                "uf": uf,
                "categorias": {
                    c: {
                        "secoes": int(cad.loc[c, "size"]),
                        "eleitores": int(cad.loc[c, "sum"]),
                    }
                    for c in cad.index
                    if c != "Z"
                },
                "mudanca_real": {
                    "secoes": len(mr),
                    "eleitores": int(mr["eleitores_2t"].sum()),
                    "locais_origem": int(
                        mr[["mun", "zona", "local_1t"]].drop_duplicates().shape[0]
                    ),
                    "municipios": int(mr["mun"].nunique()),
                },
                "fora_do_original_2t": int(g["temp_2t_cadastro"].sum()),
                "painel_tse_secoes": int(pp.get(uf, 0)),
                "notas_tre": notas.get(str(uf), []),
            }
        )
    return sorted(out, key=lambda x: -x["mudanca_real"]["eleitores"])


def por_municipio(cls: pd.DataFrame, n: int = 40) -> list[dict[str, Any]]:
    mr = cls[cls["mudanca_real"]]
    ok = di.distancia_valida(mr)
    out = []
    for (uf, mun), g in mr.groupby(["uf", "mun"]):
        d = g.loc[ok.loc[g.index], "distancia_m"]
        out.append(
            {
                "uf": uf,
                "mun_tse": mun,
                "municipio": g["municipio"].iloc[0],
                "secoes": len(g),
                "eleitores": int(g["eleitores_2t"].sum()),
                "locais_origem": int(
                    g[["zona", "local_1t"]].drop_duplicates().shape[0]
                ),
                "categorias": {
                    k: int(v) for k, v in g["categoria"].value_counts().items()
                },
                "distancia_mediana_m": _f(d.median(), 0) if len(d) else None,
            }
        )
    return sorted(out, key=lambda x: -x["eleitores"])[:n]


def top_deslocamentos(pares: list[dict[str, Any]], n: int = 20) -> list[dict[str, Any]]:
    ok = [
        p
        for p in pares
        if p["mudanca_real"]
        and p["distancia_m"] is not None
        and not p["distancia_suspeita"]
        and not p["coord_repetida"]
    ]
    ok.sort(key=lambda p: -p["distancia_m"])
    campos = [
        "uf",
        "municipio",
        "zona",
        "categoria",
        "nome_1t",
        "end_1t",
        "nome_2t",
        "end_2t",
        "secoes",
        "eleitores",
        "distancia_m",
        "abst_1t_pct",
        "flavio_v",
        "lula_v",
        "maps_rota",
    ]
    return [{c: p[c] for c in campos} for p in ok[:n]]


COLUNAS_CSV = [
    "uf",
    "mun_tse",
    "municipio",
    "zona",
    "secao",
    "urna",
    "agregada",
    "categoria",
    "categoria_cadastro",
    "confianca",
    "motivo_classificacao",
    "local_1t",
    "nome_1t",
    "end_1t",
    "bairro_1t",
    "lat_1t",
    "lon_1t",
    "local_2t",
    "nome_2t",
    "end_2t",
    "bairro_2t",
    "cep_2t",
    "lat_2t",
    "lon_2t",
    "distancia_m",
    "distancia_suspeita",
    "coord_repetida",
    "eleitores",
    "aptos_1t",
    "comparecimento_1t",
    "abst_1t_pct",
    "flavio_1t",
    "lula_1t",
    "terceira_1t",
    "brancos",
    "nulos",
    "flavio_v",
    "lula_v",
    "margem_v",
    "bateria",
    "bateria_votacao",
    "reinicio",
    "atencao",
    "abertura_atrasada",
    "fila_fechamento",
    "fonte_painel",
    "maps_novo",
    "maps_rota",
]


def linhas_csv(
    cls: pd.DataFrame, urnas: pd.DataFrame, painel_chaves: set[tuple]
) -> list[dict[str, Any]]:
    """Uma linha por seção com mudança real; dados de urna só na linha da principal."""
    mr = cls[cls["mudanca_real"]].sort_values(["uf", "mun", "zona", "secao"])
    u = {
        (r["uf"], r["mun"], int(r["zona"]), int(r["secao"])): r
        for r in registros(urnas)
    }
    out = []
    for r in registros(mr):
        k = (r["uf"], r["mun"], int(r["zona"]), int(r["secao"]))
        urna = None if r["agregada"] else u.get(k)
        lat1, lon1 = coordenada_publicavel(
            r["lat_1t"], r["lon_1t"], r["coord_repetida_1t"]
        )
        lat2, lon2 = coordenada_publicavel(
            r["lat_2t"], r["lon_2t"], r["coord_repetida_2t"]
        )
        linha = {
            "uf": r["uf"],
            "mun_tse": r["mun"],
            "municipio": r["municipio"],
            "zona": int(r["zona"]),
            "secao": int(r["secao"]),
            "urna": int(r["urna"]),
            "agregada": bool(r["agregada"]),
            "categoria": r["categoria"],
            "categoria_cadastro": r["categoria_cadastro"],
            "confianca": r["confianca"],
            "motivo_classificacao": r["motivo_classificacao"],
            "local_1t": int(r["local_1t"]),
            "nome_1t": r["nome_1t"],
            "end_1t": r["endereco_1t"],
            "bairro_1t": r["bairro_1t"],
            "lat_1t": _f(r["lat_1t"]),
            "lon_1t": _f(r["lon_1t"]),
            "local_2t": int(r["local_2t"]),
            "nome_2t": r["nome_2t"],
            "end_2t": r["endereco_2t"],
            "bairro_2t": r["bairro_2t"],
            "cep_2t": r["cep_2t"],
            "lat_2t": _f(r["lat_2t"]),
            "lon_2t": _f(r["lon_2t"]),
            "distancia_m": _f(r["distancia_m"], 0),
            "distancia_suspeita": bool(r["distancia_suspeita"]),
            "coord_repetida": bool(r["coord_repetida"]),
            "eleitores": int(r["eleitores_2t"]),
            "fonte_painel": (r["uf"], int(r["zona"]), int(r["secao"])) in painel_chaves,
            "maps_novo": di.maps_novo(
                lat2,
                lon2,
                _consulta(r["nome_2t"], r["endereco_2t"], r["municipio"], r["uf"]),
            ),
            "maps_rota": (
                None
                if r["distancia_suspeita"]
                else di.maps_rota(lat1, lon1, lat2, lon2)
            ),
        }
        linha.update(_urna_csv(urna))
        out.append(linha)
    return out


def _urna_csv(u: dict[str, Any] | None) -> dict[str, Any]:
    chaves = [
        "aptos_1t",
        "comparecimento_1t",
        "abst_1t_pct",
        "flavio_1t",
        "lula_1t",
        "terceira_1t",
        "brancos",
        "nulos",
        "flavio_v",
        "lula_v",
        "margem_v",
        "bateria",
        "bateria_votacao",
        "reinicio",
        "atencao",
        "abertura_atrasada",
        "fila_fechamento",
    ]
    if u is None or not u["tem_bu"]:
        return dict.fromkeys(chaves)
    comp = _composicao(u)
    return {
        **comp,
        "bateria": bool(u["bateria"]),
        "bateria_votacao": bool(u["bateria_votacao"]),
        "reinicio": bool(u["reinicio"]),
        "atencao": _f(u["atencao"]),
        "abertura_atrasada": bool(u["abertura_atrasada"]),
        "fila_fechamento": bool(u["fila_fechamento"]),
    }


def gravar_csv(linhas: list[dict[str, Any]], caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS_CSV, lineterminator="\n")
        w.writeheader()
        for linha in linhas:
            w.writerow(
                {k: "" if linha.get(k) is None else linha[k] for k in COLUNAS_CSV}
            )


def gravar_json(obj: Any, caminho: Path, compacto: bool = False) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(
        obj,
        ensure_ascii=False,
        indent=None if compacto else 1,
        separators=(",", ":") if compacto else None,
        allow_nan=False,
    )
    caminho.write_text(texto + "\n", encoding="utf-8")


def publico(payload: dict[str, Any]) -> dict[str, Any]:
    """Cópia pública: sem chaves internas (prefixo ``_``)."""
    if isinstance(payload, dict):
        return {k: publico(v) for k, v in payload.items() if not str(k).startswith("_")}
    if isinstance(payload, list):
        return [publico(v) for v in payload]
    return payload


def _fonte(no_painel: bool, no_zip: bool) -> str:
    if not no_painel:
        return "so_zip"
    return "ambos" if no_zip else "so_painel"


def politize(
    cls: pd.DataFrame,
    pares: list[dict[str, Any]],
    painel: pd.DataFrame | None,
    gerado_em: str,
    originais: dict[tuple, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Grava ``mudancas/indice.json`` e um arquivo por zona com alguma seção listada.

    Nas seções só do painel em que o painel dá o local original como final,
    ``originais`` traz nome, endereço e, quando há, bairro, CEP e coordenada do local
    original do cadastro (``endereco_fonte``).
    """
    chave = ["uf", "zona", "secao"]
    pinfo: dict[tuple[Any, int, int], dict[str, Any]] = {}
    if painel is not None:
        pinfo = {
            (r["uf"], int(r["zona"]), int(r["secao"])): r for r in registros(painel)
        }
    zip_mudou = cls["mudanca_real"] | cls["categoria_cadastro"].isin(list("ABCX"))
    no_painel = np.array(
        [tuple(k) in pinfo for k in cls[chave].to_numpy().tolist()], dtype=bool
    )
    alvo = cls[cls["mudanca_real"].to_numpy() | no_painel].assign(
        _zip_mudou=zip_mudou[cls["mudanca_real"].to_numpy() | no_painel]
    )
    idx_par = {
        (p["uf"], p["mun_tse"], p["zona"], p["local_1t"], p["local_2t"]): p
        for p in pares
    }
    mesmo = (
        cls[cls["mudanca_real"]]
        .groupby(["uf", "mun", "zona", "local_1t"])["secao"]
        .apply(lambda s: sorted(int(x) for x in s))
        .to_dict()
    )
    if POLITIZE.exists():
        shutil.rmtree(POLITIZE)
    zonas: dict[tuple[str, int], dict[str, Any]] = {}
    contagem = {"ambos": 0, "so_zip": 0, "so_painel": 0}
    for r in registros(alvo):
        k = (r["uf"], int(r["zona"]), int(r["secao"]))
        esta_no_painel = k in pinfo
        no_zip = bool(r["_zip_mudou"])
        fonte = _fonte(esta_no_painel, no_zip)
        contagem[fonte] += 1
        par = idx_par.get(
            (r["uf"], r["mun"], int(r["zona"]), int(r["local_1t"]), int(r["local_2t"]))
        )
        tre = (par or {}).get("motivo_tre")
        lat2, lon2 = coordenada_publicavel(
            r["lat_2t"], r["lon_2t"], r["coord_repetida_2t"]
        )
        item: dict[str, Any] = {
            "categoria": r["categoria"],
            "nome_1t": r["nome_1t"],
            "end_1t": r["endereco_1t"],
            "bairro_1t": r["bairro_1t"],
            "nome_2t": r["nome_2t"],
            "end_2t": r["endereco_2t"],
            "bairro_2t": r["bairro_2t"],
            "cep_2t": r["cep_2t"],
            "lat_2t": _f(lat2),
            "lon_2t": _f(lon2),
            "distancia_m": None if r["distancia_suspeita"] else _f(r["distancia_m"], 0),
            "eleitores": int(r["eleitores_2t"]),
            "motivo_tre": tre["texto"] if tre else None,
            "url_tre": tre["url"] if tre else None,
            "grau_tre": tre["grau_casamento"] if tre else None,
            "mesmo_predio_1t": mesmo.get(
                (r["uf"], r["mun"], int(r["zona"]), int(r["local_1t"])), []
            ),
            "maps_novo": di.maps_novo(
                lat2,
                lon2,
                _consulta(r["nome_2t"], r["endereco_2t"], r["municipio"], r["uf"]),
            ),
            "fonte": fonte,
            "mudanca_real": bool(r["mudanca_real"]),
        }
        if r["agregada"]:
            item["agregada_a"] = int(r["urna"])
        if fonte == "so_painel":
            p = pinfo[k]
            item.update(
                {
                    "categoria": "painel",
                    "nome_1t": p["local_inicial"],
                    "nome_2t": p["local_final"],
                    "end_2t": None,
                    "bairro_2t": None,
                    "cep_2t": None,
                    "lat_2t": None,
                    "lon_2t": None,
                    "distancia_m": None,
                    "eleitores": int(p["eleitorado"]),
                    "categoria_arquivo": r["categoria_cadastro"],
                    "maps_novo": di.maps_novo(
                        None, None, f"{p['local_final']}, {r['municipio']}, {r['uf']}"
                    ),
                    "frase": tx.FRASE_DIVERGENCIA,
                }
            )
            orig = (originais or {}).get(k)
            if orig is not None:
                item.update(orig)
        z = zonas.setdefault(
            (r["uf"], int(r["zona"])),
            {"uf": r["uf"], "zona": int(r["zona"]), "secoes": {}},
        )
        z["secoes"][str(int(r["secao"]))] = item
    por_uf: dict[str, dict[str, int]] = {}
    for (uf, zona), conteudo in sorted(zonas.items()):
        gravar_json(conteudo, POLITIZE / uf / f"{zona}.json", compacto=True)
        d = por_uf.setdefault(uf, {"secoes": 0, "eleitores": 0, "zonas": 0})
        d["secoes"] += len(conteudo["secoes"])
        d["eleitores"] += sum(s["eleitores"] for s in conteudo["secoes"].values())
        d["zonas"] += 1
    indice = {
        "versao": VERSAO_POLITIZE,
        "gerado_em": gerado_em,
        "total_secoes": sum(d["secoes"] for d in por_uf.values()),
        "total_eleitores": sum(d["eleitores"] for d in por_uf.values()),
        "por_fonte": contagem,
        "por_uf": por_uf,
        "categorias": tx.CATEGORIAS_APP,
        "fontes": {
            "ambos": "o arquivo de locais do TSE (18/10) e o painel de seções alteradas "
            "concordam que a seção mudou",
            "so_zip": "só o arquivo de locais mostra a mudança",
            "so_painel": "só o painel do TSE lista a seção; o arquivo de locais diverge",
        },
        "nota": "mesmo_predio_1t inclui a própria seção; seção agregada aparece pelo próprio "
        "número, com agregada_a apontando a principal onde vota. grau_tre diz como a nota "
        "do TRE casou: local (número ou nome do prédio), zona ou só município; no grau "
        "município o motivo é da nota, não necessariamente desta seção.",
        "arquivo": "mudancas/<UF>/<zona>.json",
    }
    gravar_json(indice, POLITIZE / "indice.json")
    return indice
