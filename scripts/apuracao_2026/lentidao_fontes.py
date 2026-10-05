"""Leitura das réguas de tempo por seção e por município, em 2022 e em 2026.

- 2022: `detalhe_votacao_secao_2022.zip`, membro `_BR.csv` (presidente, os dois
  turnos, latin-1, `;`), lido em fluxo, linha a linha, sem extrair o arquivo. Usa
  o 1º turno e as colunas `DT_RECEBIMENTO_BU_HOR_TSE` e
  `DT_PRIM_TOT_PARCIAL_HOR_TSE` (definições no `leiame.pdf` do mesmo ZIP, p. 5).
- 2026, seção: `apuracao/data/secoes_2026.sqlite` (coleta em andamento), coluna
  `dr_hr` do `aux` de cada seção (carimbo de recebimento do boletim, hora do TSE)
  e `bu.encerramento` (relógio local da urna).
- 2026, município: arquivos de andamento `ab:6257::uf:<uf>::` do banco da
  apuração, que trazem as seções totalizadas de cada município a cada versão; a
  primeira versão com todas as seções marca a hora em que o município fechou.
"""

from __future__ import annotations

import io
import sqlite3
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from .banco import Banco
from .contexto import ELE_FED
from .dados import entradas_ab, utc, versoes_genuinas

MEMBRO_2022 = "detalhe_votacao_secao_2022_BR.csv"
ASPAS = '"'
FECHAMENTO_2022 = datetime(2022, 10, 2, 17, 0, 0)
FECHAMENTO_2026 = datetime(2026, 10, 4, 17, 0, 0)
FECHAMENTO_2026_UTC = "2026-10-04T20:00:00Z"
COLUNAS_2022 = (
    "NR_TURNO",
    "CD_CARGO",
    "SG_UF",
    "CD_MUNICIPIO",
    "NM_MUNICIPIO",
    "DT_RECEBIMENTO_BU_HOR_TSE",
    "DT_PRIM_TOT_PARCIAL_HOR_TSE",
)


def _min_2022(campo: str) -> float | None:
    texto = campo.strip().strip('"')
    if not texto or texto.startswith("#"):
        return None
    dt = datetime.strptime(texto, "%d/%m/%Y %H:%M:%S")
    return (dt - FECHAMENTO_2022).total_seconds() / 60


def ler_2022(linhas, membro: str = MEMBRO_2022) -> dict[str, Any]:
    """Agrega as seções do 1º turno de presidente a partir de linhas de texto do CSV.

    Devolve, por UF, as listas de minutos de recebimento e de primeira
    totalização; por município, o minuto da última seção (nas duas réguas), o
    nome e as seções; e a diferença entre as duas réguas seção a seção.
    """
    cab = [c.strip().strip('"') for c in next(linhas).rstrip("\r\n").split(";")]
    idx = {c: cab.index(c) for c in COLUNAS_2022}
    corte = max(idx.values()) + 1
    rec: dict[str, list[float]] = defaultdict(list)
    tot: dict[str, list[float]] = defaultdict(list)
    mun: dict[str, dict[str, Any]] = {}
    sem: Counter = Counter()
    secoes: Counter = Counter()
    atraso_s: list[float] = []
    for linha in linhas:
        c = linha.rstrip("\r\n").split(";", corte)
        if c[idx["NR_TURNO"]].strip('"') != "1" or c[idx["CD_CARGO"]].strip('"') != "1":
            continue
        uf = c[idx["SG_UF"]].strip('"').lower()
        r = _min_2022(c[idx["DT_RECEBIMENTO_BU_HOR_TSE"]])
        t = _min_2022(c[idx["DT_PRIM_TOT_PARCIAL_HOR_TSE"]])
        if r is None:
            sem[f"{uf}:recebimento"] += 1
        else:
            rec[uf].append(r)
        if t is None:
            sem[f"{uf}:totalizacao"] += 1
        else:
            tot[uf].append(t)
        if r is not None and t is not None:
            atraso_s.append(round((t - r) * 60, 1))
        cd = f"{int(c[idx['CD_MUNICIPIO']].strip(ASPAS)):05d}"
        secoes[uf] += 1
        m = mun.setdefault(
            cd,
            {
                "uf": uf,
                "nome": c[idx["NM_MUNICIPIO"]].strip('"'),
                "secoes": 0,
                "rec": None,
                "tot": None,
            },
        )
        m["secoes"] += 1
        if r is not None and (m["rec"] is None or r > m["rec"]):
            m["rec"] = r
        if t is not None and (m["tot"] is None or t > m["tot"]):
            m["tot"] = t
    return {
        "membro": membro,
        "recebimento": dict(rec),
        "totalizacao": dict(tot),
        "municipios": mun,
        "secoes": dict(secoes),
        "sem_carimbo": dict(sem),
        "atraso_totalizacao_s": atraso_s,
    }


def secoes_2022(zip_path: Path, membro: str = MEMBRO_2022) -> dict[str, Any]:
    """Lê o membro do ZIP em fluxo, latin-1."""
    with zipfile.ZipFile(zip_path) as zf, zf.open(membro) as bruto:
        texto = io.TextIOWrapper(bruto, encoding="latin-1", newline="")
        return ler_2022(iter(texto), membro)


def _min_2026(texto: str) -> float:
    return (datetime.fromisoformat(texto) - FECHAMENTO_2026).total_seconds() / 60


def recebimento_2026(caminho: Path) -> dict[str, Any]:
    """Carimbo de recebimento por seção já coletada, por UF, e o relógio da urna.

    Só entram seções com `status_aux = 'Totalizada'`; as marcadas `Recebida`
    têm um carimbo posterior à totalização (boletim reenviado) e ficam de fora,
    contadas. Seção agregada (`nsp` preenchido) não tem boletim próprio.
    """
    con = sqlite3.connect(f"file:{caminho}?mode=ro", uri=True)
    try:
        con.execute("PRAGMA query_only = 1")
        tempos: dict[str, list[float]] = defaultdict(list)
        cont: dict[str, Counter] = defaultdict(Counter)
        for uf, status, dr, nsp in con.execute(
            "SELECT uf, status_aux, dr_hr, nsp FROM secao"
        ):
            c = cont[uf]
            if nsp is not None:
                c["agregadas"] += 1
                continue
            c["proprias"] += 1
            if status == "Totalizada" and dr:
                tempos[uf].append(_min_2026(dr))
                c["totalizadas_com_carimbo"] += 1
            elif status == "Recebida":
                c["recebidas_depois"] += 1
            else:
                c["sem_carimbo"] += 1
        encerramento = {
            uf: {"primeiro": a, "secoes_com_boletim": n}
            for uf, a, n in con.execute(
                "SELECT uf, MIN(encerramento), COUNT(*) FROM bu GROUP BY uf"
            )
        }
        meta = dict(con.execute("SELECT chave, valor FROM meta").fetchall())
    finally:
        con.close()
    return {
        "tempos": dict(tempos),
        "contagens": {uf: dict(c) for uf, c in cont.items()},
        "encerramento_local": encerramento,
        "meta": meta,
    }


def municipios_ab(banco: Banco) -> dict[str, dict[str, Any]]:
    """Hora (geração) da primeira versão de andamento com o município completo."""
    arqs = banco.arquivos("tipo = 'ab' AND eleicao_cd = ? AND nivel = 'uf'", (ELE_FED,))
    snaps = banco.snapshots([a["id"] for a in arqs])
    nomes = {m["cd"]: m["nome"] for m in banco.municipios()}
    inicio = utc(FECHAMENTO_2026_UTC)
    fim: dict[str, dict[str, Any]] = {}
    for arq in arqs:
        for v in versoes_genuinas(snaps.get(arq["id"], [])):
            if utc(v["gerado_em"]) < inicio:
                continue
            for cd, e in entradas_ab(banco.documento(v["sha256"])).items():
                if e["tpabr"] not in ("mu", "mun") or cd in fim:
                    continue
                if e["ts"] and e["st"] == e["ts"]:
                    fim[cd] = {
                        "uf": arq["uf"],
                        "nome": nomes.get(cd, cd),
                        "secoes": e["ts"],
                        "gerado": v["gerado_em"],
                        "min": round(
                            (utc(v["gerado_em"]) - inicio).total_seconds() / 60, 2
                        ),
                        "hora_impressa_local": e["ht"],
                    }
        banco.esquecer_documentos()
    return fim
