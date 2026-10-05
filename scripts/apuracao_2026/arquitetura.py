"""Dimensionamento da noite de 04/10/2026 para o capítulo de arquitetura.

Partes puras (contagem por minuto, lacunas, taxas, volumes) e leitores locais,
sem rede. Réguas:

- recebimento 2026: `dr_hr` do `aux` de cada seção (`apuracao/data/secoes_2026.sqlite`),
  hora de Brasília (as primeiras seções de AC e DF têm o mesmo carimbo, 17:08);
  coleta parcial, por isso a série vem também extrapolada para o país;
- recebimento 2022: `DT_RECEBIMENTO_BU_HOR_TSE` e `DT_PRIM_TOT_PARCIAL_HOR_TSE`
  de `detalhe_votacao_secao_2022.zip` (presidente, 1º turno, país inteiro);
- publicação 2026: versões novas (arquivo, hora de geração) dos arquivos de
  resultado capturadas pelo coletor (`apuracao/data/apuracao.sqlite`), um piso do
  que o TSE gerou, porque o coletor não lê todo arquivo a cada minuto;
- totalização nacional 2026: seções do arquivo nacional entre versões
  (`linha_do_tempo.json`).
"""

from __future__ import annotations

import io
import sqlite3
import statistics
import zipfile
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime, timedelta
from itertools import pairwise
from pathlib import Path
from typing import Any

SECOES_PAIS = 499_248
INICIO = datetime(2026, 10, 4, 17, 0)
FIM = datetime(2026, 10, 4, 21, 30)
INICIO_2022 = datetime(2022, 10, 2, 17, 0)
FIM_2022 = datetime(2022, 10, 2, 21, 30)
LIMIAR_LACUNA_S = 90
MEMBRO_2022 = "detalhe_votacao_secao_2022_BR.csv"
CARGOS = {
    1: "Presidente",
    3: "Governador",
    5: "Senador",
    6: "Deputado federal",
    7: "Deputado estadual",
    8: "Deputado distrital",
}


# ------------------------------------------------------------------ puras


def minuto(dt: datetime) -> str:
    return dt.strftime("%H:%M")


def por_minuto(
    instantes: Iterable[datetime], ini: datetime, fim: datetime
) -> list[list]:
    """[[HH:MM, contagem]] de ini a fim (exclusive), com zero nos minutos vazios."""
    c = Counter(minuto(t) for t in instantes if ini <= t < fim)
    saida, t = [], ini
    while t < fim:
        saida.append([minuto(t), c.get(minuto(t), 0)])
        t += timedelta(minutes=1)
    return saida


def lacunas(
    instantes: Iterable[datetime],
    ini: datetime,
    fim: datetime,
    limiar_s: float = LIMIAR_LACUNA_S,
) -> list[dict]:
    """Intervalos sem nenhum carimbo, maiores que `limiar_s`, dentro de [ini, fim)."""
    ts = sorted({t for t in instantes if ini <= t < fim})
    out = []
    for a, b in pairwise(ts):
        s = (b - a).total_seconds()
        if s > limiar_s:
            out.append(
                {
                    "de": a.strftime("%Y-%m-%d %H:%M:%S"),
                    "ate": b.strftime("%Y-%m-%d %H:%M:%S"),
                    "minutos": round(s / 60, 2),
                }
            )
    return out


def quantis(valores: Sequence[float], qs: Sequence[float]) -> list[float]:
    v = sorted(valores)
    if not v:
        return [0.0 for _ in qs]
    return [v[min(len(v) - 1, int(q * len(v)))] for q in qs]


def taxas_nacionais(versoes: Sequence[Mapping[str, Any]]) -> list[dict]:
    """Seções por minuto entre versões seguidas do arquivo nacional."""
    out = []
    for a, b in pairwise(versoes):
        ta = datetime.fromisoformat(a["gerado_brt"])
        tb = datetime.fromisoformat(b["gerado_brt"])
        m = (tb - ta).total_seconds() / 60
        if m <= 0:
            continue
        ds = (b["st"] or 0) - (a["st"] or 0)
        out.append(
            {
                "de": a["gerado_brt"],
                "ate": b["gerado_brt"],
                "minutos": round(m, 2),
                "secoes": ds,
                "secoes_por_minuto": round(ds / m, 1),
            }
        )
    return out


def pico_sustentado(taxas: Sequence[Mapping[str, Any]], min_minutos: float = 3) -> dict:
    """A maior taxa entre versões com intervalo de pelo menos `min_minutos`."""
    validas = [t for t in taxas if t["minutos"] >= min_minutos and t["secoes"] > 0]
    return max(validas, key=lambda t: t["secoes_por_minuto"]) if validas else {}


def dimensionar(
    *,
    secoes_amostra: int,
    bu_bytes_medio: float,
    log_bytes_medio: float,
    linhas_por_secao: float,
    pico_secoes_min: float,
    secoes_paradas: int,
    secoes_pais: int = SECOES_PAIS,
) -> dict:
    """Volumes da noite em bytes, linhas e taxas, a partir das médias medidas."""
    fator = secoes_pais / secoes_amostra if secoes_amostra else 0.0
    bu_total = bu_bytes_medio * secoes_pais
    log_total = log_bytes_medio * secoes_pais
    linhas = linhas_por_secao * secoes_pais
    return {
        "fator_extrapolacao": round(fator, 4),
        "bu_total_mb": round(bu_total / 1e6, 1),
        "log_total_mb": round(log_total / 1e6, 1),
        "linhas_voto_total": round(linhas),
        "pico_secoes_por_segundo": round(pico_secoes_min / 60, 1),
        "pico_linhas_por_minuto": round(pico_secoes_min * linhas_por_secao),
        "pico_linhas_por_segundo": round(pico_secoes_min * linhas_por_secao / 60),
        "pico_bu_mb_por_minuto": round(pico_secoes_min * bu_bytes_medio / 1e6, 1),
        "pico_bu_log_mb_por_segundo": round(
            pico_secoes_min * (bu_bytes_medio + log_bytes_medio) / 60 / 1e6, 2
        ),
        "secoes_represadas": secoes_paradas,
        "linhas_represadas": round(secoes_paradas * linhas_por_secao),
        "mb_represados_bu": round(secoes_paradas * bu_bytes_medio / 1e6, 1),
    }


# ------------------------------------------------------------------ leitores


def _dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("T", " ")[:19])


def ler_secoes_2026(caminho: Path) -> dict:
    """Recebimento, tamanho do BU e linhas de voto por seção, da coleta parcial."""
    con = sqlite3.connect(f"file:{caminho}?mode=ro", uri=True)
    try:
        dr = [
            _dt(r[0])
            for r in con.execute(
                "SELECT dr_hr FROM secao WHERE dr_hr IS NOT NULL AND uf <> 'zz'"
            )
        ]
        ufs = [
            r[0].upper()
            for r in con.execute(
                "SELECT uf FROM secao WHERE dr_hr IS NOT NULL AND uf <> 'zz' "
                "GROUP BY uf HAVING COUNT(*) > 100 ORDER BY uf"
            )
        ]
        bu = [
            r[0]
            for r in con.execute(
                "SELECT bu_bytes FROM secao WHERE bu_bytes IS NOT NULL"
            )
        ]
        log = [
            r[0]
            for r in con.execute(
                "SELECT log_bytes FROM secao WHERE log_bytes IS NOT NULL"
            )
        ]
        por_cargo = con.execute(
            "SELECT cargo, COUNT(*), COUNT(DISTINCT uf || '/' || mun || '/' || zona || '/' || secao) "
            "FROM voto_secao GROUP BY cargo ORDER BY cargo"
        ).fetchall()
        n_linhas, n_sec = con.execute(
            "SELECT COUNT(*), COUNT(DISTINCT uf || '/' || mun || '/' || zona || '/' || secao) "
            "FROM voto_secao"
        ).fetchone()
    finally:
        con.close()
    return {
        "recebimentos": dr,
        "ufs_cobertas": ufs,
        "bu_bytes": bu,
        "log_bytes": log,
        "linhas_por_cargo": [
            {
                "cargo": CARGOS.get(c, str(c)),
                "linhas": n,
                "secoes": s,
                "por_secao": round(n / s, 2) if s else 0,
            }
            for c, n, s in por_cargo
        ],
        "linhas_voto": n_linhas,
        "secoes_com_voto": n_sec,
    }


def ler_2022(zip_path: Path, membro: str = MEMBRO_2022) -> dict:
    """Recebimento e primeira totalização por seção, presidente, 1º turno de 2022."""
    receb, atraso = [], []
    with zipfile.ZipFile(zip_path) as zf, zf.open(membro) as bruto:
        f = io.TextIOWrapper(bruto, encoding="latin-1")
        cab = [c.strip().strip('"') for c in next(f).rstrip("\r\n").split(";")]
        i = {c: k for k, c in enumerate(cab)}
        for linha in f:
            c = linha.rstrip("\r\n").split(";")
            if c[i["NR_TURNO"]].strip('"') != "1":
                continue
            r = c[i["DT_RECEBIMENTO_BU_HOR_TSE"]].strip('"')
            if not r or r.startswith("#"):
                continue
            dr = datetime.strptime(r, "%d/%m/%Y %H:%M:%S")
            receb.append(dr)
            t = c[i["DT_PRIM_TOT_PARCIAL_HOR_TSE"]].strip('"')
            if t and not t.startswith("#"):
                tt = datetime.strptime(t, "%d/%m/%Y %H:%M:%S")
                atraso.append((tt - dr).total_seconds())
    return {"recebimentos": receb, "atraso_s": atraso}


def ler_publicacao(caminho: Path, ini_utc: str, fim_utc: str) -> dict:
    """Versões novas de arquivos de resultado por minuto (hora de geração, UTC)."""
    con = sqlite3.connect(f"file:{caminho}?mode=ro", uri=True)
    try:
        linhas = con.execute(
            "SELECT substr(g, 1, 16), COUNT(*), SUM(b) FROM ("
            " SELECT s.arquivo_id, s.gerado_em AS g, MAX(bl.bytes) AS b"
            " FROM snapshot s JOIN arquivo a ON a.id = s.arquivo_id"
            " JOIN blob bl ON bl.sha256 = s.sha256"
            " WHERE a.tipo = 'u' AND s.gerado_em >= ? AND s.gerado_em < ?"
            " GROUP BY s.arquivo_id, s.gerado_em) GROUP BY 1 ORDER BY 1",
            (ini_utc, fim_utc),
        ).fetchall()
        total = con.execute(
            "SELECT COUNT(*) FROM (SELECT DISTINCT arquivo_id, gerado_em FROM snapshot "
            "WHERE gerado_em IS NOT NULL)"
        ).fetchone()[0]
    finally:
        con.close()
    return {
        "minutos": [[m, n, b] for m, n, b in linhas],
        "versoes_total": total,
    }


def publicacao_brt(
    minutos_utc: Sequence[Sequence], ini: datetime, fim: datetime
) -> list[list]:
    """[[HH:MM BRT, versões, MB]] com zero nos minutos sem versão."""
    mapa = {}
    for m, n, b in minutos_utc:
        t = datetime.fromisoformat(m.replace("T", " ")) - timedelta(hours=3)
        mapa[minuto(t)] = (n, (b or 0) / 1e6)
    saida, t = [], ini
    while t < fim:
        n, mb = mapa.get(minuto(t), (0, 0.0))
        saida.append([minuto(t), n, round(mb, 1)])
        t += timedelta(minutes=1)
    return saida


def resumo_bytes(v: Sequence[float]) -> dict:
    if not v:
        return {"n": 0}
    q = quantis(v, (0.5, 0.95))
    return {
        "n": len(v),
        "media": round(statistics.fmean(v)),
        "mediana": q[0],
        "p95": q[1],
        "max": max(v),
    }
