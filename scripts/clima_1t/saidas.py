"""Gravação das saídas: payload, arquivos do mapa por UF, CSV dos locais.

Esquemas fixos no contrato (``analysis/clima_1t_2026/CONTRATO.md``). Campos novos só são
acrescentados no fim das colunas; nenhum nome do contrato muda.
"""

from __future__ import annotations

import gzip
import io
import json
import math
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from clima_1t.variaveis import ROTULO_CHUVA, ROTULO_RAJADA

ROOT = Path(__file__).resolve().parents[2]
PAYLOAD = ROOT / "analysis/clima_1t_2026/clima.json"
PUBLICO = ROOT / "docs/assets/clima_1t/dados.json"
CSV = ROOT / "docs/assets/clima_1t/locais.csv.gz"
MAPA = ROOT / "docs/assets/fiscais_mapa/clima"
TRAVESSAO = chr(0x2014)

COLUNAS_MAPA = [
    "local_id",
    "cel",
    "chuva_04_10_mm",
    "chuva_votacao_mm",
    "hora_pico_chuva",
    "rajada_04_10_kmh",
    "rajada_votacao_kmh",
    "faixa_chuva",
    "faixa_rajada",
    "urnas",
    "urnas_bateria",
    "urnas_bateria_votacao",
    "abst_pct",
    "abst22_pct",
    "dif_abst_pp",
    # acréscimos ao contrato (sempre no fim)
    "urnas_bateria_simultanea",
    "urnas_bateria_isolada",
    "urnas_reinicio",
    "aptos",
    "faixa_chuva_votacao",
]
CASAS = {
    "chuva_04_10_mm": 1,
    "chuva_votacao_mm": 1,
    "chuva_votacao_estrita_mm": 1,
    "chuva_03_10_mm": 1,
    "chuva_02a05_max_mm": 1,
    "rajada_04_10_kmh": 1,
    "rajada_votacao_kmh": 1,
    "abst_pct": 2,
    "abst22_pct": 2,
    "dif_abst_pp": 2,
    "lat": 7,
    "lon": 7,
}
COLUNAS_CSV = [
    "local_id",
    "uf",
    "mun",
    "municipio",
    "zona",
    "local_nr",
    "nome",
    "lat",
    "lon",
    "cel",
    "chuva_04_10_mm",
    "chuva_votacao_mm",
    "chuva_votacao_estrita_mm",
    "hora_pico_chuva",
    "chuva_03_10_mm",
    "chuva_02a05_max_mm",
    "rajada_04_10_kmh",
    "rajada_votacao_kmh",
    "faixa_chuva",
    "faixa_chuva_votacao",
    "faixa_rajada",
    "faixa_rajada_votacao",
    "urnas",
    "urnas_log",
    "urnas_relogio",
    "urnas_bateria",
    "urnas_bateria_votacao",
    "urnas_bateria_simultanea",
    "urnas_bateria_isolada",
    "urnas_reinicio",
    "urnas_abertura_atrasada",
    "aptos",
    "comparecimento",
    "abst_pct",
    "aptos_c",
    "comp_c",
    "aptos22",
    "comp22",
    "abst22_pct",
    "dif_abst_pp",
    "flavio_v",
    "lula_v",
]


def limpo(v: Any) -> Any:
    """Valor serializável: NaN vira null, numpy vira Python."""
    if v is None:
        return None
    if isinstance(v, (np.bool_, bool)):
        return bool(v)
    if isinstance(v, np.integer):
        return int(v)
    if isinstance(v, (float, np.floating)):
        f = float(v)
        return None if math.isnan(f) or math.isinf(f) else f
    if isinstance(v, dict):
        return {str(k): limpo(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [limpo(x) for x in v]
    return v


def _arred(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c, n in CASAS.items():
        if c in out:
            out[c] = out[c].astype(float).round(n)
    return out


def _linha(reg: Mapping[Any, Any], cols: list[str]) -> list[Any]:
    linha = []
    for c in cols:
        v = limpo(reg.get(c))
        if (
            c
            in (
                "urnas",
                "urnas_bateria",
                "urnas_bateria_votacao",
                "aptos",
                "urnas_bateria_simultanea",
                "urnas_bateria_isolada",
                "urnas_reinicio",
                "hora_pico_chuva",
            )
            and v is not None
        ):
            v = int(v)
        linha.append(v)
    return linha


def gravar_json(caminho: Path, doc: dict[str, Any], compacto: bool = True) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(
        limpo(doc),
        ensure_ascii=False,
        separators=(",", ":") if compacto else None,
        indent=None if compacto else 1,
        allow_nan=False,
    )
    caminho.write_text(texto + ("" if compacto else "\n"), encoding="utf-8")


def gravar_mapa(locais: pd.DataFrame, gerado_em: str, fonte: str) -> dict[str, int]:
    """Um arquivo por UF com todos os locais (sem coordenada: clima null)."""
    df = _arred(locais)
    sem_bu = df["urnas"] == 0
    for c in ("abst_pct", "abst22_pct", "dif_abst_pp"):
        df.loc[sem_bu, c] = np.nan
    contagem = {}
    for uf, d in df.groupby("uf"):
        regs = d.sort_values("local_id").to_dict("records")
        doc = {
            "gerado_em": gerado_em,
            "fonte": fonte,
            "celula_graus": 0.25,
            "colunas": COLUNAS_MAPA,
            "linhas": [_linha(r, COLUNAS_MAPA) for r in regs],
            "faixas": {"chuva": ROTULO_CHUVA, "rajada": ROTULO_RAJADA},
            "notas": {
                "faixa_chuva": "pela chuva do dia 04/10 inteiro (chuva_04_10_mm)",
                "faixa_rajada": "pela rajada máxima do dia 04/10 (rajada_04_10_kmh)",
                "chuva_votacao_mm": "soma das 7h às 18h de Brasília (votação das 8h às 17h "
                "de Brasília em todo o país, com uma hora de folga de cada lado)",
                "hora_pico_chuva": "hora local de início do intervalo de uma hora com mais "
                "chuva dentro da janela de votação; null sem chuva na janela",
                "abst22_pct": "2º turno de 2022 nas seções casadas por número",
                "dif_abst_pp": "abstenção de 2026 menos a de 2022 nas mesmas seções",
                "urnas_bateria": "urnas com registro de bateria interna em qualquer momento; "
                "operação prevista da urna, não irregularidade",
            },
        }
        gravar_json(MAPA / f"{uf}.json", doc)
        contagem[uf] = len(regs)
    return contagem


def gravar_csv(locais: pd.DataFrame) -> int:
    df = _arred(locais)[COLUNAS_CSV].sort_values("local_id")
    buf = io.StringIO()
    df.to_csv(buf, index=False, lineterminator="\n")
    CSV.parent.mkdir(parents=True, exist_ok=True)
    with (
        CSV.open("wb") as bruto,
        gzip.GzipFile(filename="locais.csv", mode="wb", fileobj=bruto, mtime=0) as gz,
    ):
        gz.write(buf.getvalue().encode("utf-8"))
    return len(df)


def sem_travessao(caminho: Path) -> bool:
    return TRAVESSAO not in caminho.read_text(encoding="utf-8")
