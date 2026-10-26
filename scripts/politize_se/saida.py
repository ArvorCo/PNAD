"""Escrita dos JSON públicos em ``docs/assets/politize_se/dados/`` (contrato v1).

Listas compactas ``{"colunas": [...], "linhas": [[...], ...]}``; ``null`` para ausência;
taxas com uma casa. Escrita atômica (arquivo temporário e troca).
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any

from .fontes import ROOT

SAIDA = ROOT / "docs/assets/politize_se/dados"
VERSAO = "1.0"

COLS_SECAO = [
    "secao",
    "mun_tse",
    "li",
    "local_nr2",
    "agregadas1",
    "agregadas2",
    "agreg_igual",
    "pequena",
    "aptos1",
    "comp1",
    "flavio1",
    "lula1",
    "terceira1",
    "brancos1",
    "nulos1",
    "sem_bio1",
    "ano_nasc1",
    "hab_bio1",
    "abert1",
    "enc1",
    "rec1",
    "urna1",
    "modelo1",
    "tipo_urna1",
    "cargas1",
    "bu2",
    "aptos2",
    "comp2",
    "flavio2",
    "lula2",
    "brancos2",
    "nulos2",
    "sem_bio2",
    "ano_nasc2",
    "hab_bio2",
    "abert2",
    "enc2",
    "rec2",
    "urna2",
    "modelo2",
    "tipo_urna2",
    "cargas2",
    "tipo_arquivo2",
    "comp_pct1",
    "comp_pct2",
    "d_comp_pp",
    "abst_pct1",
    "abst_pct2",
    "bn_pct1",
    "bn_pct2",
    "flavio_v1",
    "lula_v1",
    "terceira_v1",
    "fatia_f1",
    "fatia_f2",
    "d_fatia_pp",
    "sem_bio_pct1",
    "sem_bio_pct2",
    "ano_nasc_pct1",
    "ano_nasc_pct2",
    "urna_situacao",
    "contingencia2",
    "escore",
    "sinais",
    "explicacoes",
    "fiscal_nivel",
    "fiscal_pontos",
    "fiscal_sinais",
    "c13_nivel",
    "log1_atencao",
    "log1_sinais",
    "log1_familias",
    "log2_atencao",
    "log2_sinais",
    "log2_familias",
    "log2_reinicios",
    "log2_bateria",
    "log2_bateria_simultaneas",
    "log2_erro_mr",
    "log2_meta",
    "ml_grupo",
    "ml_anomalo",
    "ml_p",
    "mudanca",
    "frases",
]

# colunas do prédio no arquivo da zona (tabela; a seção aponta o prédio pela posição ``li``)
CAMPOS_LOCAL = [
    "local_id",
    "mun_tse",
    "nome",
    "endereco",
    "bairro",
    "cep",
    "lat",
    "lon",
    "secoes",
    "secao_link",
    "n_secoes",
    "n_bu2",
    "aptos1",
    "comp1",
    "flavio1",
    "lula1",
    "terceira1",
    "bn1",
    "aptos2",
    "comp2",
    "flavio2",
    "lula2",
    "bn2",
    "comp_pct1",
    "comp_pct2",
    "comp_pct1_par",
    "d_comp_pp",
    "abst_pct1",
    "abst_pct2",
    "bn_pct1",
    "bn_pct2",
    "flavio_v1",
    "lula_v1",
    "terceira_v1",
    "fatia_f1",
    "fatia_f1_par",
    "fatia_f2",
    "d_fatia_pp",
    "escore_max",
    "secoes_sinal",
    "secoes_sinal2",
    "secoes_mudaram",
    "urnas_trocadas",
    "log2_atencao_max",
    "secoes_log_subiu",
    "secoes_log_persiste",
    "secoes_log_reinicio",
    "secoes_log_bateria",
    "secoes_anomalas",
    "clima1",
    "clima2",
    "clima2o",
    "frases",
]

# colunas do prédio no arquivo do município (o que o mapa do Brasil consome)
COLS_LOCAL_MUN = [
    "local_id",
    "zona",
    "nome",
    "endereco",
    "bairro",
    "cep",
    "lat",
    "lon",
    "n_secoes",
    "n_bu2",
    "secao_link",
    "aptos1",
    "aptos2",
    "comp_pct1",
    "comp_pct2",
    "d_comp_pp",
    "abst_pct2",
    "bn_pct2",
    "flavio2",
    "lula2",
    "fatia_f1",
    "fatia_f1_par",
    "fatia_f2",
    "d_fatia_pp",
    "escore_max",
    "secoes_sinal",
    "secoes_sinal2",
    "secoes_mudaram",
    "urnas_trocadas",
    "log2_atencao_max",
    "secoes_log_subiu",
    "secoes_log_persiste",
    "secoes_log_reinicio",
    "secoes_log_bateria",
    "secoes_anomalas",
    "link",
]

CAMPOS_TOTAIS = [
    "n_secoes",
    "n_1t",
    "n_bu2",
    "n_par",
    "aptos1",
    "comp1",
    "flavio1",
    "lula1",
    "terceira1",
    "bn1",
    "aptos2",
    "comp2",
    "flavio2",
    "lula2",
    "bn2",
    "aptos1p",
    "comp1p",
    "flavio1p",
    "lula1p",
    "comp_pct1",
    "comp_pct2",
    "comp_pct1_par",
    "d_comp_pp",
    "abst_pct1",
    "abst_pct2",
    "bn_pct1",
    "bn_pct2",
    "flavio_v1",
    "lula_v1",
    "terceira_v1",
    "fatia_f1",
    "fatia_f1_par",
    "fatia_f2",
    "d_fatia_pp",
    "escore_max",
    "secoes_sinal",
    "secoes_sinal2",
    "secoes_mudaram",
    "urnas_trocadas",
    "log2_atencao_max",
    "secoes_log_subiu",
    "secoes_log_persiste",
    "secoes_log_reinicio",
    "secoes_log_bateria",
    "secoes_anomalas",
]


def link(uf: str, zona: int | None, secao: int) -> str:
    return f"politizese.html#uf={uf}&z={zona}&s={secao}"


BOOLEANOS = frozenset({"bu2", "pequena", "agreg_igual", "contingencia2", "ml_anomalo"})
CLIMA1 = [
    "chuva_mm",
    "chuva_dia_mm",
    "faixa",
    "rajada_kmh",
    "pico",
    "urnas",
    "urnas_bateria_votacao",
]
CLIMA2 = ["chuva_mm", "prob_pct", "rajada_kmh", "risco"]
CLIMA2O = [
    "chuva_mm",
    "fonte_votacao",
    "chuva_dia_mm",
    "fonte_dia",
    "rajada_kmh",
    "n_estacoes",
    "dist_km",
    "fonte",
]


def gravar(caminho: Path, obj: Any) -> int:
    """JSON compacto; ``.json.gz`` sai comprimido com data zerada (bytes reprodutíveis)."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    tmp = caminho.with_name(f".{caminho.name}.tmp")
    texto = json.dumps(obj, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    dados = texto.encode("utf-8")
    if caminho.suffix == ".gz":
        dados = gzip.compress(dados, compresslevel=9, mtime=0)
    tmp.write_bytes(dados)
    tmp.replace(caminho)
    return len(dados)


def _valor(c: str, v: Any) -> Any:
    if c in BOOLEANOS and v is not None:
        return int(bool(v))
    return v


def _frases(fr: list[list[str]], codigo: dict[str, int]) -> list[list[Any]]:
    return [[codigo[f[0]], *f[1:]] for f in fr]


def _local(p: dict[str, Any], codigo: dict[str, int]) -> list[Any]:
    out = []
    for c in CAMPOS_LOCAL:
        v = p.get(c)
        if c == "clima1" and v is not None:
            v = [v.get(k) for k in CLIMA1]
        elif c == "clima2" and v is not None:
            v = [v.get(k) for k in CLIMA2]
        elif c == "clima2o" and v is not None:
            v = [v.get(k) for k in CLIMA2O]
        elif c == "frases":
            v = _frases(v or [], codigo)
        out.append(v)
    return out


def totais(t: dict[str, Any]) -> dict[str, Any]:
    return {c: t.get(c) for c in CAMPOS_TOTAIS}


def escrever_uf(res: Any, gerado_em: str, codigos: list[str]) -> dict[str, int]:
    """Grava ``zona/<UF>/*.json`` e ``mun/<UF>/*.json``; devolve bytes por camada."""
    uf = res.uf
    bytes_ = {"zona": 0, "mun": 0}
    for pasta in ("zona", "mun"):
        d = SAIDA / pasta / uf
        if d.exists():
            for arq in d.glob("*.json*"):
                arq.unlink()
    codigo = {c: i for i, c in enumerate(codigos)}
    for z, rows in sorted(res.secoes.items()):
        rows = sorted(rows, key=lambda r: r["secao"])
        lids = sorted({r["local_id"] for r in rows if r["local_id"] in res.locais})
        posicao = {lid: i for i, lid in enumerate(lids)}
        muns = sorted({r["mun_tse"] for r in rows if r["mun_tse"]})
        n_bu = sum(1 for r in rows if r["bu2"])
        obj = {
            "uf": uf,
            "zona": z,
            "versao": VERSAO,
            "gerado_em": gerado_em,
            "cobertura": {"secoes": len(rows), "com_bu_2t": n_bu},
            "municipios": {
                m: {"nome": res.nomes_mun.get(m, m), **totais(res.municipios[m])}
                for m in muns
            },
            "locais": {
                "colunas": CAMPOS_LOCAL,
                "clima1": CLIMA1,
                "clima2": CLIMA2,
                "clima2o": CLIMA2O,
                "linhas": [_local(res.locais[lid], codigo) for lid in lids],
            },
            "secoes": {
                "colunas": COLS_SECAO,
                "linhas": [
                    [
                        (
                            posicao.get(r["local_id"])
                            if c == "li"
                            else (
                                _frases(r["frases"], codigo)
                                if c == "frases"
                                else _valor(c, r.get(c))
                            )
                        )
                        for c in COLS_SECAO
                    ]
                    for r in rows
                ],
            },
        }
        bytes_["zona"] += gravar(SAIDA / "zona" / uf / f"{z}.json.gz", obj)
    por_mun: dict[str, list[dict[str, Any]]] = {}
    for p in res.locais.values():
        por_mun.setdefault(p["mun_tse"], []).append(p)
    for mun, ps in sorted(por_mun.items()):
        ps = sorted(ps, key=lambda p: (p["zona"] or 0, p["local_id"]))
        linhas = []
        for p in ps:
            q = {**p, "link": link(uf, p["zona"], p["secao_link"])}
            linhas.append([q.get(c) for c in COLS_LOCAL_MUN])
        obj = {
            "uf": uf,
            "mun_tse": mun,
            "nome": res.nomes_mun.get(mun, mun),
            "versao": VERSAO,
            "gerado_em": gerado_em,
            "totais": totais(res.municipios[mun]),
            "locais": {"colunas": COLS_LOCAL_MUN, "linhas": linhas},
        }
        bytes_["mun"] += gravar(SAIDA / "mun" / uf / f"{mun}.json", obj)
    return bytes_
