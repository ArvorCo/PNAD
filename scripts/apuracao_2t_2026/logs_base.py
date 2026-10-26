"""Leitura compacta dos logs das urnas para o capítulo ``logs`` do dossiê do 2º turno.

Fontes, sempre somente leitura:

- ``data/outputs/logs_urnas_2t_2026.sqlite`` e ``logs_urnas_2026.sqlite``: métricas
  por seção (coluna ``resumo``), uma linha por seção, do leitor versão 12;
- ``docs/assets/logs_urnas_{2t_,}2026/zona/<UF>/<zona>.json.gz``: os diagnósticos
  publicados (coluna ``sinais``) de cada turno, de onde sai o nível de atenção;
- ``analysis/apuracao_2t_2026/dados/secoes.json``: BU por seção (voto, escore do BU,
  encerramento) nos dois turnos;
- a amostra do 1º turno relida para a cadência (``logs_amostra_1t``).

Tudo vira tabelas ``pandas`` guardadas em ``data/outputs/logs_2t_capitulo/``
(ignorado pelo Git). ``--refazer`` relê os bancos.
"""

from __future__ import annotations

import gzip
import json
import sqlite3
from pathlib import Path

import pandas as pd

try:  # orjson acelera a leitura dos 499 mil resumos; sem ele vale o json da biblioteca padrão
    import orjson as _orjson

    def _loads(b):
        return _orjson.loads(b)

except ImportError:  # pragma: no cover

    def _loads(b):
        return json.loads(b)


from apuracao_logs.familias import atencao
from apuracao_logs.pleito import PLEITOS, ROOT

from . import secoes_linhas

CACHE = ROOT / "data/outputs/logs_2t_capitulo"
DADOS = ROOT / "analysis/apuracao_2t_2026/dados"
LOGS_2T = ROOT / "analysis/apuracao_2t_2026/logs_urnas"
ROTULO = "pede explicação, não prova irregularidade"

REGIAO = {
    **dict.fromkeys(["AC", "AM", "AP", "PA", "RO", "RR", "TO"], "Norte"),
    **dict.fromkeys(["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"], "Nordeste"),
    **dict.fromkeys(["DF", "GO", "MS", "MT"], "Centro-Oeste"),
    **dict.fromkeys(["ES", "MG", "RJ", "SP"], "Sudeste"),
    **dict.fromkeys(["PR", "RS", "SC"], "Sul"),
    "ZZ": "Exterior",
}
CHAVE = ["uf", "mun", "zona", "secao"]
CATEGORIAS_ERRO = ("outros", "impress", "mídia", "biometr", "assinatura")


def _conectar(caminho: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{caminho}?mode=ro", uri=True)


def _primeiro(m: dict, campo: str):
    v = m.get(campo) or []
    return v[0] if v else None


def linha_2t(uf: str, mun: str, z: int, s: int, r: dict) -> dict:
    """Uma seção do 2º turno: só os campos que o capítulo usa."""
    c = r.get("contagens") or {}
    bu = r.get("bu") or {}
    il = r.get("identidade_log") or {}
    dif = r.get("diferencas_bu") or {}
    cat = r.get("erros_categoria") or {}
    part = [p for p in r.get("partidas_dia") or [] if p.get("fase") == "votacao"]
    sist = [p for p in part if p.get("tipo") == "sistema"]
    vota = [p for p in part if p.get("tipo") == "vota"]
    ep = sist or vota
    meta = r.get("metadados_urna") or {}
    series_dia, series_todas, cargas_em, versoes, midias_em = [], [], [], [], []
    for m in meta.values():
        series_dia += m.get("serie_mr_dia") or []
        series_todas += m.get("serie_mr") or []
        versoes += m.get("versao_aplicacao_dia") or m.get("versao_aplicacao") or []
        midias_em += m.get("midia_votacao_gerada_em_dia") or []
        if m.get("carga_registrada_em"):
            cargas_em.append(m["carga_registrada_em"])
    bat = r.get("bateria_votacao_segundos") or []
    d = {
        "uf": uf.upper(),
        "mun": mun,
        "zona": int(z),
        "secao": int(s),
        "contagem_confere": bool(r.get("contagem_confere")),
        "biometria_confere": bool(r.get("biometria_confere")),
        "bio_ausente_bu": bu.get("hab_biometria") is None,
        "dif_computados": dif.get("computados"),
        "dif_biometrica": dif.get("biometrica"),
        "dif_biografica": dif.get("biografica"),
        "dif_sem_biometria": dif.get("sem_biometria"),
        "computados": c.get("computados"),
        "ciclos": r.get("ciclos"),
        "bu_comp": bu.get("comparecimento"),
        "tipo_urna": bu.get("tipo_urna"),
        "tipo_arquivo": bu.get("tipo_arquivo"),
        "n_cargas": bu.get("n_cargas"),
        "modelo": bu.get("modelo_urna"),
        "n_urnas_log": len(r.get("urnas_log") or []),
        "outras_urnas": len(il.get("outras_urnas_no_log") or []),
        "urna_bu_no_log": il.get("urna_bu_no_log"),
        "carga_bu_no_log": il.get("carga_bu_no_log"),
        "versoes": "|".join(sorted(set(versoes))),
        "erros": c.get("erros", 0),
        "erro_mr": c.get("erro_mr", 0),
        "erro_mr_pre": c.get("erro_mr_pre_zeresima", 0),
        "erros_janela": c.get("erros_na_janela_votacao", 0),
        "relogio_ok": bool(r.get("tempos_validos")),
        "primeiro_s": r.get("primeiro_computo_s"),
        "ultimo_s": r.get("ultimo_computo_s"),
        "zeresima_s": r.get("zeresima_s"),
        "cph": json.dumps(r.get("computados_por_hora") or {}, separators=(",", ":")),
        "cph_ok": bool(r.get("computados_por_hora_confiavel")),
        "reinicios_sist": len(sist),
        "reinicios_vota": len(vota),
        "reinicio_s": ep[0]["segundo"] if ep else None,
        "reinicio_antes": ep[0].get("votos_antes") if ep else None,
        "reinicio_depois": ep[0].get("votos_depois") if ep else None,
        "reinicio_urnas": "|".join(sorted({p.get("urna", "") for p in ep})),
        "bateria_votacao": len(bat),
        "bateria_s": bat[0] if bat else None,
        "series_mr_dia": "|".join(sorted(set(series_dia))),
        "series_mr": "|".join(sorted(set(series_todas))),
        "cargas_em": "|".join(sorted(set(cargas_em))),
        "midias_em": "|".join(sorted(set(midias_em))),
        "n_urnas_meta": len(meta),
    }
    for k in CATEGORIAS_ERRO:
        d[f"ecat_{k}"] = cat.get(k, 0)
    d["ecat_resto"] = sum(v for k, v in cat.items() if k not in CATEGORIAS_ERRO)
    return d


def linha_1t(uf: str, mun: str, z: int, s: int, r: dict) -> dict:
    return {
        "uf": uf.upper(),
        "mun": mun,
        "zona": int(z),
        "secao": int(s),
        "contagem_confere1": bool(r.get("contagem_confere")),
        "primeiro_s1": r.get("primeiro_computo_s"),
        "ultimo_s1": r.get("ultimo_computo_s"),
        "computados1": (r.get("contagens") or {}).get("computados"),
        "erros1": (r.get("contagens") or {}).get("erros", 0),
    }


def _ler_metricas(caminho: Path, fn) -> pd.DataFrame:
    con = _conectar(caminho)
    linhas = [
        fn(uf, mun, z, s, _loads(txt))
        for uf, mun, z, s, txt in con.execute(
            "SELECT uf,mun,zona,secao,resumo FROM metricas WHERE status='ok'"
        )
    ]
    con.close()
    return pd.DataFrame(linhas)


def _ler_sinais(publico: Path) -> pd.DataFrame:
    linhas = []
    for arq in sorted((publico / "zona").glob("*/*.json.gz")):
        d = json.loads(gzip.decompress(arq.read_bytes()))
        col = {c: i for i, c in enumerate(d["colunas"])}
        for ln in d["linhas"]:
            sinais = sorted(ln[col["sinais"]] or [])
            linhas.append(
                {
                    "uf": d["uf"].upper(),
                    "mun": ln[col["mun"]],
                    "zona": int(d["zona"]),
                    "secao": int(ln[col["secao"]]),
                    "sinais": "|".join(sinais),
                    "atencao": atencao(set(sinais)),
                    "bateria_simultaneas": (
                        ln[col["bateria_simultaneas"]]
                        if "bateria_simultaneas" in col
                        else None
                    ),
                }
            )
    return pd.DataFrame(linhas)


def _ler_secoes_bu() -> pd.DataFrame:
    d = _loads((DADOS / "secoes.json").read_bytes())
    s = secoes_linhas.exigir(d)
    df = pd.DataFrame(s["linhas"], columns=s["colunas"])
    df["mun"] = df["mun"].astype(str).str.zfill(5)
    keep = [
        *CHAVE,
        "aptos",
        "comp",
        "taxa2",
        "taxa1",
        "delta_pp",
        "sem_bio_pct",
        "ano_nasc_pct",
        "enc_min",
        "enc1_min",
        "tipo_urna",
        "n_cargas",
        "tipo_arquivo",
        "fl",
        "lu",
        "fl1",
        "lu1",
        "fatia_f",
        "fatia_f1",
        "escore",
        "magnitude",
        "apos_19h",
        "contingencia",
        "sinal_delta",
        "sinal_sem_bio",
        "sinal_ano_nasc",
        "sinal_tardia",
        "sinal_papel",
        "sinal_salto_bio",
    ]
    df = df[keep].rename(
        columns={
            "tipo_urna": "bu_tipo_urna",
            "n_cargas": "bu_n_cargas",
            "tipo_arquivo": "bu_tipo_arquivo",
        }
    )
    return df


def _cache(nome: str, fn, refazer: bool) -> pd.DataFrame:
    arq = CACHE / f"{nome}.parquet"
    if arq.exists() and not refazer:
        return pd.read_parquet(arq)
    CACHE.mkdir(parents=True, exist_ok=True)
    df = fn()
    df.to_parquet(arq, index=False)
    return df


def ler_amostra_1t() -> pd.DataFrame:
    from .logs_amostra_1t import SAIDA

    if not SAIDA.exists():
        return pd.DataFrame(
            columns=[*CHAVE, "cph", "cph_ok", "primeiro_s", "ultimo_s", "partidas"]
        )
    linhas = [json.loads(x) for x in SAIDA.read_text(encoding="utf-8").splitlines()]
    df = pd.DataFrame(linhas)
    df["uf"] = df["uf"].str.upper()
    df["cph"] = df["cph"].map(lambda v: json.dumps(v or {}, separators=(",", ":")))
    return df


def _ler_exterior_bu() -> pd.DataFrame:
    """BU do exterior nos dois turnos, pela mesma leitura do capítulo de metadados
    (``metadados_base.ler_bu`` + ``urnas_analise.preparar``): ``secoes.json`` não traz
    o 1º turno das seções do exterior."""
    from .metadados_base import BANCO_1T, BANCO_2T, ler_bu
    from .urnas_analise import preparar

    b2 = preparar(ler_bu(BANCO_2T, "2t"))
    b1 = preparar(ler_bu(BANCO_1T, "1t", True))
    b2 = b2[b2["uf"].str.upper() == "ZZ"][[*CHAVE, "fatia_flavio", "validos_fl"]]
    b1 = b1[b1["uf"].str.upper() == "ZZ"][[*CHAVE, "fatia_flavio"]]
    j = b2.merge(b1, on=CHAVE, how="left", suffixes=("", "_1t"))
    j["uf"] = j["uf"].str.upper()
    return j.rename(
        columns={
            "fatia_flavio": "fatia_f",
            "fatia_flavio_1t": "fatia_f1",
            "validos_fl": "fl",
        }
    ).assign(lu=0)


def carregar(refazer: bool = False) -> dict[str, pd.DataFrame]:
    """Tabelas do capítulo: ``t2`` (métricas 2T), ``t1`` (métricas 1T), sinais, BU."""
    t2 = _cache(
        "metricas_2t", lambda: _ler_metricas(PLEITOS[3221].metricas, linha_2t), refazer
    )
    t1 = _cache(
        "metricas_1t", lambda: _ler_metricas(PLEITOS[3220].metricas, linha_1t), refazer
    )
    s2 = _cache("sinais_2t", lambda: _ler_sinais(PLEITOS[3221].publico), refazer)
    s1 = _cache("sinais_1t", lambda: _ler_sinais(PLEITOS[3220].publico), refazer)
    bu = _cache("secoes_bu", _ler_secoes_bu, refazer)
    ext = _cache("exterior_bu", _ler_exterior_bu, refazer)
    return {
        "t2": t2,
        "t1": t1,
        "s2": s2,
        "s1": s1,
        "bu": bu,
        "ext": ext,
        "a1": ler_amostra_1t(),
    }


def regiao(uf: pd.Series) -> pd.Series:
    return uf.map(REGIAO).fillna("?")
