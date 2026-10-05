"""Compacta eleitorado_local_votacao_2026.zip (TSE) num SQLite por seção.

Saída: data/outputs/locais_votacao_2026.sqlite, tabela `secao` com UF, município
(código TSE), zona, seção, agregação, local de votação, endereço, bairro,
coordenadas e eleitorado. Leitura em fluxo, uma UF por vez, sem extrair o ZIP;
o consolidado `_BRASIL.csv` do mesmo pacote repete as UFs e fica de fora.
"""

from __future__ import annotations

import argparse
import csv
import io
import sqlite3
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ZIP = RAIZ / "data/raw/tse_eleitorado/eleitorado_local_votacao_2026.zip"
SAIDA = RAIZ / "data/outputs/locais_votacao_2026.sqlite"

ESQUEMA = """
DROP TABLE IF EXISTS secao;
CREATE TABLE secao (
  uf TEXT NOT NULL,
  municipio_cd TEXT NOT NULL,
  municipio TEXT NOT NULL,
  zona INTEGER NOT NULL,
  secao INTEGER NOT NULL,
  agregada_cd INTEGER,
  agregada TEXT,
  secao_principal INTEGER,
  local_nr INTEGER,
  local TEXT,
  tipo_local_cd INTEGER,
  tipo_local TEXT,
  endereco TEXT,
  bairro TEXT,
  cep TEXT,
  lat REAL,
  lon REAL,
  situacao_secao TEXT,
  acessibilidade TEXT,
  eleitores INTEGER,
  eleitores_federal INTEGER,
  eleitores_estadual INTEGER,
  PRIMARY KEY (uf, municipio_cd, zona, secao)
) WITHOUT ROWID;
"""


def numero(v: str) -> float | None:
    v = v.strip()
    if v in {"", "-1", "#NULO#", "#NE#"}:
        return None
    try:
        return float(v.replace(",", "."))
    except ValueError:
        return None


def inteiro(v: str) -> int | None:
    n = numero(v)
    return int(n) if n is not None else None


def linhas(zf: zipfile.ZipFile, nome: str):
    with zf.open(nome) as bruto:
        texto = io.TextIOWrapper(bruto, encoding="latin-1", newline="")
        for r in csv.DictReader(texto, delimiter=";"):
            lat = numero(r["NR_LATITUDE"])
            lon = numero(r["NR_LONGITUDE"])
            yield (
                r["SG_UF"],
                r["CD_MUNICIPIO"].zfill(5),
                r["NM_MUNICIPIO"],
                int(r["NR_ZONA"]),
                int(r["NR_SECAO"]),
                inteiro(r["CD_TIPO_SECAO_AGREGADA"]),
                r["DS_TIPO_SECAO_AGREGADA"],
                inteiro(r["NR_SECAO_PRINCIPAL"]),
                inteiro(r["NR_LOCAL_VOTACAO"]),
                r["NM_LOCAL_VOTACAO"],
                inteiro(r["CD_TIPO_LOCAL"]),
                r["DS_TIPO_LOCAL"],
                r["DS_ENDERECO"],
                r["NM_BAIRRO"],
                r["NR_CEP"],
                lat,
                lon,
                r["DS_SITU_SECAO"],
                r["DS_SITU_SECAO_ACESSIBILIDADE"],
                inteiro(r["QT_ELEITOR_SECAO"]),
                inteiro(r["QT_ELEITOR_ELEICAO_FEDERAL"]),
                inteiro(r["QT_ELEITOR_ELEICAO_ESTADUAL"]),
            )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--zip", type=Path, default=ZIP)
    ap.add_argument("--saida", type=Path, default=SAIDA)
    args = ap.parse_args()
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(args.saida)
    con.executescript(ESQUEMA)
    total = 0
    with zipfile.ZipFile(args.zip) as zf:
        for nome in sorted(
            n for n in zf.namelist() if n.endswith(".csv") and "_BRASIL" not in n
        ):
            lote = list(linhas(zf, nome))
            con.executemany(
                "INSERT OR REPLACE INTO secao VALUES (" + ",".join("?" * 22) + ")", lote
            )
            con.commit()
            total += len(lote)
            print(f"{nome}: {len(lote)} seções")
    con.execute("CREATE INDEX idx_secao_local ON secao (uf, municipio_cd, local_nr)")
    con.commit()
    n_coord = con.execute(
        "SELECT COUNT(*) FROM secao WHERE lat IS NOT NULL"
    ).fetchone()[0]
    print(f"total {total} seções; {n_coord} com coordenada")
    con.close()


if __name__ == "__main__":
    main()
