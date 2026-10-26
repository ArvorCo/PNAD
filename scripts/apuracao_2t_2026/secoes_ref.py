"""Régua do 1º turno por seção e cadastro de locais (somente leitura).

``apuracao/data/referencia_1t_secoes.json`` (gerado por
``apuracao/scripts/referencia-1t-secoes.ts``): por seção, aptos, comparecimento,
sem biometria cadastrada, habilitados por ano de nascimento, encerramento em
minutos depois das 17:00 de Brasília de 04/10, índice do local e votos de Flávio
e Lula na seção principal (Politize). Nomes de município e de local vêm do
Politize (``docs/assets/politize/dados``), nunca de pessoa.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

CAMPOS = ["secao", "aptos1", "comp1", "sem_bio1", "ano_nasc1", "enc1_min", "local"]
CAMPOS += ["fl1", "lu1"]


def ler_regua(caminho: Path) -> tuple[pd.DataFrame, list[list[float]], dict[str, Any]]:
    """Universo do 1T como tabela, a lista de coordenadas e o bloco ``meta``."""
    d = json.loads(caminho.read_text(encoding="utf-8"))
    assert d["meta"]["campos_secao"] == CAMPOS, "campos da régua mudaram"
    linhas: list[tuple[Any, ...]] = []
    for uf, muns in d["secoes"].items():
        u = uf.upper()
        for mun, zonas in muns.items():
            for zona, secoes in zonas.items():
                z = int(zona)
                for x in secoes:
                    linhas.append((u, mun, z, *x))
    df = pd.DataFrame(linhas, columns=["uf", "mun", "zona", *CAMPOS])
    df["secao"] = df["secao"].astype(int)
    return df, d["locais"], d["meta"]


def pct(num: Any, den: Any) -> Any:
    """100 × num / den, NaN quando o denominador não é positivo."""
    num = np.asarray(num, dtype=float)
    den = np.asarray(den, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(den > 0, 100 * num / den, np.nan)


def medianas_1t(ref: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Medianas por município e por zona no 1T (todas as seções da régua)."""
    r = ref.assign(
        taxa1=pct(ref["comp1"], ref["aptos1"]),
        sem_bio_pct1=pct(ref["sem_bio1"], ref["comp1"]),
        ano_nasc_pct1=pct(ref["ano_nasc1"], ref["comp1"]),
        nao_bio_pct1=pct(ref["sem_bio1"] + ref["ano_nasc1"], ref["comp1"]),
    )
    cols = ["taxa1", "sem_bio_pct1", "ano_nasc_pct1", "nao_bio_pct1"]
    mun = r.groupby(["uf", "mun"])[cols].median()
    mun.columns = [f"mun_p50_{c}" for c in cols]
    mun["mun_n_1t"] = r.groupby(["uf", "mun"]).size()
    zona = r.groupby(["uf", "zona"])[["nao_bio_pct1"]].median()
    zona.columns = ["zona_p50_nao_bio_pct1"]
    return mun.reset_index(), zona.reset_index()


def nomes_municipios(indice: Path) -> dict[tuple[str, str], str]:
    d = json.loads(indice.read_text(encoding="utf-8"))
    cols = d["municipios"]["colunas"]
    iu, im, inome = cols.index("uf"), cols.index("mun_tse"), cols.index("nome")
    return {(x[iu], x[im]): x[inome] for x in d["municipios"]["linhas"]}


def locais_politize(
    zonas_dir: Path, chaves: list[tuple[str, int]]
) -> dict[tuple[str, str, int, int], dict[str, Any]]:
    """Nome do local e seções agregadas, só para as zonas pedidas."""
    out: dict[tuple[str, str, int, int], dict[str, Any]] = {}
    for uf, zona in sorted(set(chaves)):
        arq = zonas_dir / uf / f"{zona}.json"
        if not arq.exists():
            continue
        d = json.loads(arq.read_text(encoding="utf-8"))
        cols = d["secoes"]["colunas"]
        i = {c: cols.index(c) for c in ("secao", "mun_tse", "local", "agregadas")}
        for x in d["secoes"]["linhas"]:
            out[(uf, x[i["mun_tse"]], zona, int(x[i["secao"]]))] = {
                "local": x[i["local"]],
                "agregadas": list(x[i["agregadas"]] or []),
            }
    return out
