"""Leitura das bases públicas e cálculo de cada camada, por local e município.

Cada função recebe caminhos já baixados (``fiscais_risco_fontes``) e devolve
dicionários por ``local_id`` ou por código de município. Leitura em fluxo e por
UF onde a base é pesada: a malha de setores (1,4 GB) é consultada pelo índice
R-tree do próprio GeoPackage, ponto a ponto, sem carregar a malha inteira.
"""

from __future__ import annotations

import csv
import json
import re
import shutil
import sqlite3
import subprocess
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import openpyxl
import pandas as pd
import shapely
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry

from . import fiscais_risco as fr

TABELA_SETORES = "BR_setores_CD2022"


@dataclass
class Local:
    """Um local de votação do cadastro do TSE (chave uf, município, zona, nº)."""

    uf: str
    mun_tse: str
    municipio: str
    zona: int
    local_nr: int
    local: str
    tipo_local: str
    endereco: str
    bairro: str
    lat: float | None
    lon: float | None
    eleitores: int
    ibge: str | None = None

    @property
    def id(self) -> str:
        return fr.local_id(self.uf, self.mun_tse, self.zona, self.local_nr)

    @property
    def tem_ponto(self) -> bool:
        return self.lat is not None and self.lon is not None


def abrir_ro(caminho: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{caminho}?mode=ro", uri=True)


def carregar_locais(db: Path, tse_ibge: dict[str, str]) -> list[Local]:
    """Um registro por (uf, município, zona, local_nr), com eleitores somados."""
    sql = """
        SELECT uf, municipio_cd, MAX(municipio), zona, local_nr, MAX(local),
               MAX(tipo_local), MAX(endereco), MAX(bairro), MAX(lat), MAX(lon),
               SUM(COALESCE(eleitores, 0))
        FROM secao
        GROUP BY uf, municipio_cd, zona, local_nr
        ORDER BY uf, municipio_cd, zona, local_nr
    """
    con = abrir_ro(db)
    try:
        linhas = con.execute(sql).fetchall()
    finally:
        con.close()
    locais = []
    for uf, mun, nome, zona, nr, local, tipo, end, bairro, lat, lon, el in linhas:
        ok = lat is not None and lon is not None and uf != "ZZ"
        locais.append(
            Local(
                uf=uf,
                mun_tse=str(mun).zfill(5),
                municipio=nome,
                zona=int(zona),
                local_nr=int(nr),
                local=local or "",
                tipo_local=tipo or "",
                endereco=end or "",
                bairro=bairro or "",
                lat=float(lat) if ok else None,
                lon=float(lon) if ok else None,
                eleitores=int(el),
                ibge=tse_ibge.get(str(mun).zfill(5)),
            )
        )
    return locais


def mapa_tse_ibge(db_apuracao: Path) -> dict[str, str]:
    con = abrir_ro(db_apuracao)
    try:
        rows = con.execute(
            "SELECT cd, ibge FROM municipio WHERE ibge IS NOT NULL AND ibge <> ''"
        ).fetchall()
    finally:
        con.close()
    return {str(cd).zfill(5): str(ibge) for cd, ibge in rows}


# ---------------------------------------------------------------- setores


def rotulos_setor(dicionario: Path) -> dict[str, dict[str, str]]:
    """Rótulos oficiais de CD_SIT e CD_TIPO lidos da aba Setor do dicionário."""
    wb = openpyxl.load_workbook(dicionario, read_only=True)
    ws = wb["Setor"]
    rotulos: dict[str, dict[str, str]] = {"CD_SIT": {}, "CD_TIPO": {}}
    atual: str | None = None
    for var, cat, desc in ws.iter_rows(min_row=2, max_col=3, values_only=True):
        if var is not None:
            nome = str(var).strip()
            atual = "CD_SIT" if nome in ("CD_SIT", "CD_SITUACAO") else nome
            continue
        if atual in rotulos and cat is not None and desc is not None:
            rotulos[atual][str(cat).strip()] = str(desc).strip()
    wb.close()
    if not rotulos["CD_SIT"] or not rotulos["CD_TIPO"]:
        raise ValueError("dicionário do IBGE sem os rótulos de CD_SIT ou CD_TIPO")
    return rotulos


@dataclass
class Setor:
    cd: str
    situacao: str
    cd_sit: str
    cd_tipo: str
    cd_mun: str
    cd_fcu: str
    nm_fcu: str


def setores_dos_pontos(gpkg: Path, locais: list[Local]) -> dict[str, Setor]:
    """Setor censitário que cobre o ponto de cada local (R-tree + shapely).

    Ponto sobre a divisa de dois setores fica com o de menor geocódigo, para o
    resultado não depender da ordem do índice.
    """
    con = abrir_ro(gpkg)
    rtree = f"rtree_{TABELA_SETORES}_geom"
    q_ids = (
        f"SELECT id FROM {rtree} WHERE minx <= ? AND maxx >= ? "
        "AND miny <= ? AND maxy >= ?"
    )
    cache: dict[int, tuple[BaseGeometry, Setor]] = {}
    saida: dict[str, Setor] = {}
    try:
        for loc in locais:
            if not loc.tem_ponto:
                continue
            x, y = loc.lon, loc.lat
            ids = [r[0] for r in con.execute(q_ids, (x, x, y, y))]
            achados = []
            for fid in ids:
                if fid not in cache:
                    cache[fid] = _ler_setor(con, fid)
                geom, setor = cache[fid]
                if shapely.intersects_xy(geom, x, y):
                    achados.append(setor)
            if achados:
                saida[loc.id] = min(achados, key=lambda s: s.cd)
            if len(cache) > 200_000:
                cache.clear()
    finally:
        con.close()
    return saida


def _ler_setor(con: sqlite3.Connection, fid: int) -> tuple[BaseGeometry, Setor]:
    row = con.execute(
        f"SELECT geom, CD_SETOR, SITUACAO, CD_SIT, CD_TIPO, CD_MUN, CD_FCU, NM_FCU "
        f"FROM {TABELA_SETORES} WHERE id = ?",
        (fid,),
    ).fetchone()
    geom = fr.gpkg_para_geom(row[0])
    vals = ["" if v is None else str(v).strip() for v in row[1:]]
    return geom, Setor(*vals)


def distancia_ao_municipio(
    gpkg: Path, locais: list[Local], tolerancia_km: float
) -> dict[str, float]:
    """Distância (km) do ponto ao setor mais próximo do próprio município.

    Só procura até ``tolerancia_km`` (caixa folgada em graus); local sem setor
    do próprio município nesse raio fica fora do dicionário.
    """
    con = abrir_ro(gpkg)
    rtree = f"rtree_{TABELA_SETORES}_geom"
    sql = (
        f"SELECT s.geom FROM {rtree} r JOIN {TABELA_SETORES} s ON s.id = r.id "
        "WHERE r.maxx >= ? AND r.minx <= ? AND r.maxy >= ? AND r.miny <= ? "
        "AND s.CD_MUN = ?"
    )
    folga = tolerancia_km * fr.GRAUS_POR_KM_FOLGADO
    saida: dict[str, float] = {}
    try:
        for loc in locais:
            if not loc.tem_ponto or not loc.ibge:
                continue
            x, y = loc.lon, loc.lat
            rows = con.execute(
                sql, (x - folga, x + folga, y - folga, y + folga, loc.ibge)
            ).fetchall()
            if rows:
                saida[loc.id] = min(
                    fr.distancia_km(y, x, fr.gpkg_para_geom(b)) for (b,) in rows
                )
    finally:
        con.close()
    return saida


def municipios_tocados(gpkg: Path, geoms: list[BaseGeometry]) -> dict[int, set[str]]:
    """Para cada polígono, os municípios (IBGE) cujos setores ele toca."""
    con = abrir_ro(gpkg)
    rtree = f"rtree_{TABELA_SETORES}_geom"
    q_ids = (
        f"SELECT id FROM {rtree} WHERE maxx >= ? AND minx <= ? "
        "AND maxy >= ? AND miny <= ?"
    )
    saida: dict[int, set[str]] = {}
    try:
        for i, g in enumerate(geoms):
            x0, y0, x1, y1 = g.bounds
            ids = [r[0] for r in con.execute(q_ids, (x0, x1, y0, y1))]
            muns: set[str] = set()
            shapely.prepare(g)
            for fid in ids:
                blob, cd_mun = con.execute(
                    f"SELECT geom, CD_MUN FROM {TABELA_SETORES} WHERE id = ?", (fid,)
                ).fetchone()
                if cd_mun in muns:
                    continue
                setor = fr.gpkg_para_geom(blob)
                if g.intersects(setor):
                    muns.add(str(cd_mun))
            saida[i] = muns
    finally:
        con.close()
    return saida


# --------------------------------------------------------- polígonos e pontos


def ler_geojson(caminho: Path) -> list[tuple[dict[str, Any], BaseGeometry]]:
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    saida = []
    for f in dados.get("features", []):
        if not f.get("geometry"):
            continue
        g = shape(f["geometry"])
        if not g.is_valid:
            g = shapely.make_valid(g)
        saida.append((f.get("properties") or {}, g))
    return saida


def vizinho_poligono(
    locais: list[Local],
    poligonos: list[tuple[Any, BaseGeometry]],
    raio_km: float,
) -> dict[str, tuple[Any, float]]:
    """Por local com ponto: o polígono mais próximo a até ``raio_km`` (0 dentro)."""
    com_ponto = [loc for loc in locais if loc.tem_ponto]
    lats = np.array([loc.lat for loc in com_ponto], dtype=float)
    lons = np.array([loc.lon for loc in com_ponto], dtype=float)
    geoms = [g for _, g in poligonos]
    pares = fr.pares_no_raio(lats, lons, geoms, raio_km)
    saida: dict[str, tuple[Any, float]] = {}
    for ip, igs in pares.items():
        loc = com_ponto[ip]
        cands = [(poligonos[g][0], poligonos[g][1]) for g in igs]
        achado = fr.mais_proximo(loc.lat, loc.lon, cands, raio_km)
        if achado is not None:
            saida[loc.id] = achado
    return saida


def vizinho_ponto(
    locais: list[Local],
    pontos: list[tuple[Any, float, float]],
    raio_km: float,
) -> dict[str, tuple[Any, float]]:
    """Por local com ponto: o ponto (chave, lat, lon) mais próximo no raio."""
    com_ponto = [loc for loc in locais if loc.tem_ponto]
    if not pontos or not com_ponto:
        return {}
    lats = np.array([loc.lat for loc in com_ponto], dtype=float)
    lons = np.array([loc.lon for loc in com_ponto], dtype=float)
    geoms = list(shapely.points([p[2] for p in pontos], [p[1] for p in pontos]))
    pares = fr.pares_no_raio(lats, lons, geoms, raio_km)
    saida: dict[str, tuple[Any, float]] = {}
    for ip, igs in pares.items():
        loc = com_ponto[ip]
        melhor = None
        for g in igs:
            chave, plat, plon = pontos[g]
            d = fr.haversine_km(loc.lat, loc.lon, plat, plon)
            if d <= raio_km and (melhor is None or d < melhor[1]):
                melhor = (chave, d)
        if melhor is not None:
            saida[loc.id] = melhor
    return saida


def ler_csv_pontos(caminho: Path, col_lat: str, col_lon: str) -> list[dict[str, Any]]:
    with caminho.open(encoding="utf-8-sig", newline="") as f:
        linhas = list(csv.DictReader(f, delimiter=";"))
    for linha in linhas:
        lat, lon = fr.decimal(linha.get(col_lat)), fr.decimal(linha.get(col_lon))
        if lat is None or lon is None:
            raise ValueError(f"{caminho.name}: linha sem coordenada")
        linha["_lat"], linha["_lon"] = lat, lon
    return linhas


def nome_ti_localidade(linha: dict[str, str]) -> str:
    nm_ti = (linha.get("NM_TI") or "").strip()
    nm_li = (linha.get("NM_LI") or "").strip()
    return f"TI {nm_ti} (localidade {nm_li})" if nm_ti else f"localidade {nm_li}"


def nome_quilombo(linha: dict[str, str]) -> str:
    nm_tq = (linha.get("NM_TQ") or "").strip()
    nm = " ".join(
        x
        for x in ((linha.get("PREFIXO") or "").strip(), (linha.get("NM_CQ") or ""))
        if x
    ).strip()
    return f"território {nm_tq} ({nm})" if nm_tq else nm


# ------------------------------------------------------------- municípios


def faixa_fronteira(xls: Path) -> dict[str, dict[str, Any]]:
    """IBGE 7 dígitos -> {cidade_gemea, faixa_sede, porc_int}."""
    df = pd.read_excel(xls, sheet_name=0, dtype=str)
    df.columns = [str(c).strip() for c in df.columns]
    if "CD_MUN" not in df.columns or "CID_GEMEA" not in df.columns:
        raise ValueError("planilha de fronteira sem CD_MUN ou CID_GEMEA")
    saida = {}
    for _, r in df.iterrows():
        cd = str(r["CD_MUN"]).strip()
        if not cd.isdigit():
            continue
        gemea = r.get("CID_GEMEA")
        saida[cd] = {
            "cidade_gemea": isinstance(gemea, str) and gemea.strip() != "",
            "faixa_sede": str(r.get("FAIXA_SEDE", "")).strip().lower() == "sim",
        }
    return saida


def sedes_municipais(zip_gpkg: Path) -> dict[str, tuple[float, float, str]]:
    """IBGE 7 dígitos -> (lat, lon, categoria) da sede, pela geometria do ponto."""
    prioridade = {
        ("Cidade", "Sede Municipal"): 0,
        ("Cidade", "Capital Federal"): 1,
        ("Distrito Estadual de Fernando de Noronha", ""): 2,
    }
    with zipfile.ZipFile(zip_gpkg) as z:
        nome = next(n for n in z.namelist() if n.endswith(".gpkg"))
        tmp = zip_gpkg.with_name(Path(nome).name)
        if not tmp.exists() or tmp.stat().st_size != z.getinfo(nome).file_size:
            tmp.write_bytes(z.read(nome))
    con = abrir_ro(tmp)
    try:
        rows = con.execute(
            "SELECT CD_MUN, CT_LOCALIDADE, SCT_LOCALIDADE, geom "
            "FROM BR_localidades_2022"
        ).fetchall()
    finally:
        con.close()
    melhor: dict[str, tuple[int, float, float, str]] = {}
    for cd, ct, sct, blob in rows:
        p = prioridade.get((ct, sct or ""))
        if p is None:
            continue
        g = fr.gpkg_para_geom(blob)
        cat = f"{ct}, {sct}" if sct else ct
        if cd not in melhor or p < melhor[cd][0]:
            melhor[cd] = (p, g.y, g.x, cat)
    return {cd: (lat, lon, cat) for cd, (_, lat, lon, cat) in melhor.items()}


def homicidios(
    taxa_json: Path, contagem_json: Path
) -> tuple[int, dict[str, float], dict[str, int]]:
    """Ano mais recente, taxa e contagem por código IBGE de 6 dígitos."""
    taxa = json.loads(taxa_json.read_text(encoding="utf-8"))
    cont = json.loads(contagem_json.read_text(encoding="utf-8"))
    anos = {int(x["periodo"][:4]) for x in taxa if x.get("tipo_regiao") == 4}
    ano = max(anos)
    t = {
        str(x["regiao_id"]).zfill(6): float(x["valor"])
        for x in taxa
        if x.get("tipo_regiao") == 4
        and int(x["periodo"][:4]) == ano
        and x.get("valor") is not None
    }
    c = {
        str(x["regiao_id"]).zfill(6): round(float(x["valor"]))
        for x in cont
        if x.get("tipo_regiao") == 4
        and int(x["periodo"][:4]) == ano
        and x.get("valor") is not None
    }
    return ano, t, c


def contexto_crime(
    contexto_json: Path, nome_para_tse: dict[tuple[str, str], str]
) -> tuple[dict[str, list[dict[str, Any]]], list[str], list[str]]:
    """Itens de imprensa por município TSE, nomes sem casamento e itens só de UF."""
    dados = json.loads(contexto_json.read_text(encoding="utf-8"))
    por_mun: dict[str, list[dict[str, Any]]] = defaultdict(list)
    sem_casamento: list[str] = []
    so_uf: list[str] = []
    for item in dados.get("itens", []):
        if item.get("tema") not in fr.TEMAS_CRIME:
            continue
        muns = item.get("municipios") or []
        if not muns:
            so_uf.append(str(item.get("id")))
            continue
        for m in muns:
            uf = str(m.get("uf", "")).upper()
            cd, metodo = fr.casar_municipio(uf, str(m.get("nome") or ""), nome_para_tse)
            if cd is None or metodo != "exato":
                sem_casamento.append(f"{item.get('id')}: {m.get('nome')}/{uf} {metodo}")
            if cd is None:
                continue
            if all(i.get("id") != item.get("id") for i in por_mun[cd]):
                por_mun[cd].append(item)
    return dict(por_mun), sem_casamento, so_uf


# ------------------------------------------------------- FBSP, Amazônia Legal

UFS_AMAZONIA = {
    "Acre": "AC",
    "Amapá": "AP",
    "Amazonas": "AM",
    "Maranhão": "MA",
    "Mato Grosso": "MT",
    "Pará": "PA",
    "Rondônia": "RO",
    "Roraima": "RR",
    "Tocantins": "TO",
}
_UF_ALT = "|".join(sorted(UFS_AMAZONIA, key=len, reverse=True))
_RE_LINHA_FBSP = re.compile(
    rf"^(\s*)({_UF_ALT})\s{{2,}}(\S.*?)\s{{2,}}(?:(\S.*?)\s{{2,}})?"
    r"(Presença de (?:uma|duas ou mais) facç(?:ão|ões))\s{2,}"
    r"(Rural|Urbano|Interm\w+)\s*$"
)
_RE_TOTAL_FBSP = re.compile(
    rf"^\s*({_UF_ALT})(?: \(parte amazônica\))?\s{{2,}}" r"(\d+) municípios \("
)


def texto_pdf(pdf: Path) -> str:
    """Texto do PDF com o leiaute preservado (pdftotext -layout)."""
    exe = shutil.which("pdftotext")
    if exe is None:
        raise RuntimeError("pdftotext não encontrado no PATH")
    res = subprocess.run(
        [exe, "-layout", str(pdf), "-"], check=True, capture_output=True
    )
    return res.stdout.decode("utf-8")


def fbsp_municipios(texto: str) -> tuple[dict[str, list[str]], dict[str, int]]:
    """Municípios citados nos quadros 3.2 a 3.10 do relatório, por UF.

    Lê só UF e município; a coluna de grupos nunca é guardada. Nome quebrado
    em duas linhas (fragmento à esquerda da coluna capturada) é recomposto.
    Devolve também os totais por UF do quadro 3.1, para conferência.
    """
    linhas = texto.splitlines()
    por_uf: dict[str, list[str]] = defaultdict(list)
    totais: dict[str, int] = {}
    dentro = False
    for i, linha in enumerate(linhas):
        m_total = _RE_TOTAL_FBSP.match(linha)
        if m_total and m_total.group(1) not in totais:
            totais[UFS_AMAZONIA[m_total.group(1)]] = int(m_total.group(2))
        if "Presença de facções em municípios no Estado" in linha:
            dentro = True
            continue
        if dentro and linha.strip().startswith("Fonte:"):
            dentro = False
            continue
        m = _RE_LINHA_FBSP.match(linha) if dentro else None
        if not m:
            continue
        uf = UFS_AMAZONIA[m.group(2)]
        col = m.start(3)
        nome = m.group(3).strip()
        antes = _fragmento(linhas, i, -1)
        depois = _fragmento(linhas, i, +1)
        if antes and depois and antes[0] < col - 5 and depois[0] < col - 5:
            nome = f"{antes[1]} {depois[1]}"
        por_uf[uf].append(nome)
    return dict(por_uf), totais


def _fragmento(linhas: list[str], i: int, passo: int) -> tuple[int, str] | None:
    j = i + passo
    if not 0 <= j < len(linhas):
        return None
    t = linhas[j]
    if not t.strip() or _RE_LINHA_FBSP.match(t):
        return None
    return len(t) - len(t.lstrip()), t.strip()
