"""Leitura dos dados de zona para a camada de anomalias da apuração de 2026.

Fontes, todas locais e lidas sem escrita:
- ``apuracao/data/apuracao.sqlite``: arquivos de zona do TSE (eleição 6257,
  cargo 1), última versão não regressiva com totais e votos por candidato;
- ``data/raw/tse_resultados/votacao_candidato_munzona_2022.zip``: votos de
  presidente em 2022 por município e zona, nos dois turnos;
- ``data/raw/tse_resultados/detalhe_votacao_secao_2022.zip``: aptos,
  comparecimento, brancos, nulos e hora de totalização por seção em 2022;
- ``data/raw/tse_eleitorado/eleitorado_local_votacao_2026.zip``: locais de
  votação de 2026 com latitude e longitude;
- ``apuracao/public/geo/mun/{UF}.geojson``: malha municipal do IBGE.
"""

from __future__ import annotations

import csv
import gzip
import io
import json
import re
import sqlite3
import unicodedata
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ELEICAO = 6257
CARGO = 1
FLAVIO = 22
LULA = 13
BOLSONARO = 22  # número de Jair Bolsonaro em 2022
FECHAMENTO_2026 = datetime(2026, 10, 4, 20, 0, tzinfo=timezone.utc)  # 17h Brasília
FECHAMENTO_2022 = datetime(2022, 10, 2, 17, 0)  # horário de Brasília, sem fuso
TETO_ATRASO_2022 = timedelta(hours=36)

Chave = tuple[str, str, str]  # (uf minúscula, município TSE 5 dígitos, zona 4)


def chave(uf: str, municipio: str | int, zona: str | int) -> Chave:
    return (str(uf).lower(), str(municipio).zfill(5), str(zona).zfill(4))


def iso_utc(texto: str | None) -> datetime | None:
    if not texto:
        return None
    return datetime.fromisoformat(texto.replace("Z", "+00:00"))


def _minutos_entre(inicio: str, fim: str) -> float:
    """Minutos de ``inicio`` a ``fim``, dois carimbos ISO em UTC."""
    a, b = iso_utc(inicio), iso_utc(fim)
    if a is None or b is None:
        raise ValueError("carimbo de hora ausente")
    return (b - a).total_seconds() / 60.0


def _conectar(caminho: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{caminho}?mode=ro", uri=True)


def _em_lotes(ids: list[int], tamanho: int = 900):
    for i in range(0, len(ids), tamanho):
        yield ids[i : i + tamanho]


def ler_zonas_2026(caminho: Path) -> tuple[dict[Chave, dict], dict[int, str]]:
    """Uma linha por par município-zona do Brasil, na versão vigente.

    Versão vigente é a última gerada pelo TSE (maior ``gerado_em``), com totais
    e votos por candidato. A marca ``regressivo`` do coletor não serve de
    filtro: ela dispara quando o contador ``idg`` do TSE cai, e em 30 zonas a
    versão marcada assim é a mais nova, com mais seções apuradas. Cópia antiga
    de verdade tem ``gerado_em`` anterior e perde na ordenação.
    Devolve também o nome de urna de cada número de candidato.
    """
    con = _conectar(caminho)
    sql = """
    WITH z AS (
      SELECT id, uf, municipio_cd, zona_cd FROM arquivo
      WHERE eleicao_cd = ? AND cargo_cd = ? AND nivel = 'zona' AND uf <> 'zz'
    ),
    u AS (
      SELECT z.*, (
        SELECT s.id FROM snapshot s
        WHERE s.arquivo_id = z.id AND s.gerado_em IS NOT NULL
          AND EXISTS (SELECT 1 FROM totais t WHERE t.snapshot_id = s.id)
        ORDER BY s.gerado_em DESC, s.id DESC LIMIT 1
      ) AS sid FROM z
    )
    SELECT u.id, u.uf, u.municipio_cd, u.zona_cd, m.ibge, m.nome, u.sid,
           s.gerado_em, s.totalizado_em, t.ts, t.st, t.te, t.est, t.comparecimento,
           t.tv, t.vvc, t.vb, t.tvn
    FROM u
    JOIN snapshot s ON s.id = u.sid
    JOIN totais t ON t.snapshot_id = u.sid
    LEFT JOIN municipio m ON m.cd = u.municipio_cd
    """
    zonas: dict[Chave, dict] = {}
    por_arquivo: dict[int, Chave] = {}
    por_snapshot: dict[int, Chave] = {}
    for linha in con.execute(sql, (ELEICAO, CARGO)):
        arq, uf, mun, zona, ibge, nome, sid, gerado, totalizado = linha[:9]
        ts, st, te, est, comp, tv, vvc, vb, tvn = linha[9:]
        k = chave(uf, mun, zona)
        zonas[k] = {
            "arquivo_id": arq,
            "snapshot_id": sid,
            "uf": uf.upper(),
            "municipio_tse": mun,
            "zona": zona,
            "ibge": ibge,
            "municipio": nome,
            "gerado_em": gerado,
            "totalizado_em": totalizado,
            "ts": ts,
            "st": st,
            "eleitorado": te,
            "eleitorado_apurado": est,
            "comparecimento": comp,
            "total_votos": tv,
            "validos": vvc,
            "brancos": vb,
            "nulos": tvn,
            "votos": {},
            "n_versoes": 0,
            "n_copias_antigas": 0,
            "n_idg_menor": 0,
            "conclusao_em": None,
            "primeira_em": None,
            "fuso_horas": 0,
        }
        por_arquivo[arq] = k
        por_snapshot[sid] = k
    nomes = dict(
        con.execute(
            "SELECT sqcand, numero FROM candidato WHERE eleicao_cd = ? AND cargo_cd = ?",
            (ELEICAO, CARGO),
        ).fetchall()
    )
    rotulos = dict(
        con.execute(
            "SELECT numero, nome_urna FROM candidato WHERE eleicao_cd = ? "
            "AND cargo_cd = ?",
            (ELEICAO, CARGO),
        ).fetchall()
    )
    for lote in _em_lotes(list(por_snapshot)):
        marcas = ",".join("?" * len(lote))
        for sid, sq, vap in con.execute(
            f"SELECT snapshot_id, sqcand, vap FROM voto_candidato "
            f"WHERE snapshot_id IN ({marcas})",
            lote,
        ):
            zonas[por_snapshot[sid]]["votos"][nomes[sq]] = vap or 0
    for sid, k in por_snapshot.items():
        if not zonas[k]["votos"]:
            zonas[k]["votos"] = {
                nomes[sq]: v for sq, v in _votos_do_corpo(con, sid).items()
            }
            zonas[k]["votos_do_corpo"] = True
    versoes: dict[int, list[tuple]] = defaultdict(list)
    for arq, gerado, totalizado, st, ts in con.execute(
        """SELECT s.arquivo_id, s.gerado_em, s.totalizado_em, t.st, t.ts
        FROM snapshot s JOIN arquivo a ON a.id = s.arquivo_id
        JOIN totais t ON t.snapshot_id = s.id
        WHERE a.eleicao_cd = ? AND a.cargo_cd = ? AND a.nivel = 'zona'
          AND s.gerado_em >= ? AND s.totalizado_em IS NOT NULL""",
        (ELEICAO, CARGO, FECHAMENTO_2026.strftime("%Y-%m-%dT%H:%M")),
    ):
        if arq in por_arquivo:
            versoes[arq].append((gerado, totalizado, st, ts))
    for arq, lista in versoes.items():
        z = zonas[por_arquivo[arq]]
        lista.sort()
        z["n_versoes"] = len({v[0] for v in lista})
        # A geração do arquivo vem um minuto depois da totalização; a menor
        # diferença da zona é o fuso. A mediana erraria em arquivo que parou.
        menor = min(_minutos_entre(t, g) for g, t, _, _ in lista)
        z["fuso_horas"] = round(menor / 60)
        z["primeira_em"] = next((t for _, t, st, _ in lista if st and st > 0), None)
        z["conclusao_em"] = next((t for _, t, st, ts in lista if ts and st == ts), None)
    for arq, detalhe in con.execute(
        "SELECT arquivo_id, detalhe FROM evento WHERE tipo = 'idg_regressivo' "
        "AND nivel = 'zona' AND eleicao_cd = ? AND cargo_cd = ?",
        (ELEICAO, CARGO),
    ):
        if arq not in por_arquivo:
            continue
        info = json.loads(detalhe or "{}")
        if info.get("gerado_em", "") < info.get("gerado_em_anterior", ""):
            zonas[por_arquivo[arq]]["n_copias_antigas"] += 1
        else:
            zonas[por_arquivo[arq]]["n_idg_menor"] += 1
    con.close()
    return zonas, rotulos


def _votos_do_corpo(con: sqlite3.Connection, snapshot_id: int) -> dict[int, int]:
    """Votos por candidatura lidos do JSON original do TSE guardado em ``blob``.

    O coletor não normaliza ``voto_candidato`` das versões que marcou como
    regressivas; o corpo original está guardado e é a mesma fonte.
    """
    (sha,) = con.execute(
        "SELECT sha256 FROM snapshot WHERE id = ?", (snapshot_id,)
    ).fetchone()
    (gz,) = con.execute("SELECT gz FROM blob WHERE sha256 = ?", (sha,)).fetchone()
    documento = json.loads(gzip.decompress(gz))
    votos: dict[int, int] = {}
    for cargo in documento.get("carg") or []:
        for agremiacao in cargo.get("agr") or []:
            for partido in agremiacao.get("par") or []:
                for cand in partido.get("cand") or []:
                    votos[int(cand["sqcand"])] = int(cand.get("vap") or 0)
    return votos


def ler_ufs_2026(caminho: Path) -> dict[str, dict]:
    """Arquivos de UF de presidente: seções e votos de Flávio e Lula."""
    con = _conectar(caminho)
    sql = """
    WITH a AS (
      SELECT id, uf FROM arquivo WHERE eleicao_cd = ? AND cargo_cd = ?
        AND nivel = 'uf' AND tipo = 'u' AND uf <> 'zz'
    ),
    u AS (
      SELECT a.uf, (
        SELECT MAX(s.id) FROM snapshot s WHERE s.arquivo_id = a.id
          AND s.regressivo = 0
          AND EXISTS (SELECT 1 FROM voto_candidato v WHERE v.snapshot_id = s.id)
      ) AS sid FROM a
    )
    SELECT u.uf, u.sid, s.gerado_em, t.ts, t.st, t.te, t.comparecimento, t.vvc,
      (SELECT v.vap FROM voto_candidato v JOIN candidato c USING (sqcand)
        WHERE v.snapshot_id = u.sid AND c.numero = ?),
      (SELECT v.vap FROM voto_candidato v JOIN candidato c USING (sqcand)
        WHERE v.snapshot_id = u.sid AND c.numero = ?)
    FROM u JOIN snapshot s ON s.id = u.sid JOIN totais t ON t.snapshot_id = u.sid
    """
    saida = {}
    for uf, sid, gerado, ts, st, te, comp, vvc, f, lula in con.execute(
        sql, (ELEICAO, CARGO, FLAVIO, LULA)
    ):
        saida[uf.upper()] = {
            "snapshot_id": sid,
            "gerado_em": gerado,
            "ts": ts,
            "st": st,
            "eleitorado": te,
            "comparecimento": comp,
            "validos": vvc,
            "flavio": f,
            "lula": lula,
        }
    con.close()
    return saida


def _leitor(zf: zipfile.ZipFile, nome: str):
    fh = zf.open(nome)
    texto = io.TextIOWrapper(fh, encoding="latin-1", newline="")
    leitor = csv.reader(texto, delimiter=";")
    cabecalho = next(leitor)
    return leitor, {c: i for i, c in enumerate(cabecalho)}


def ler_votos_2022(caminho: Path) -> dict[tuple[Chave, int], Counter]:
    """Votos válidos por candidato, turno e par município-zona em 2022."""
    saida: dict[tuple[Chave, int], Counter] = defaultdict(Counter)
    with zipfile.ZipFile(caminho) as zf:
        leitor, c = _leitor(zf, "votacao_candidato_munzona_2022_BR.csv")
        for row in leitor:
            if row[c["CD_CARGO"]] != "1" or row[c["SG_UF"]] == "ZZ":
                continue
            k = chave(row[c["SG_UF"]], row[c["CD_MUNICIPIO"]], row[c["NR_ZONA"]])
            turno = int(row[c["NR_TURNO"]])
            saida[(k, turno)][int(row[c["NR_CANDIDATO"]])] += int(
                row[c["QT_VOTOS_NOMINAIS_VALIDOS"]]
            )
    return dict(saida)


def _data_br(texto: str) -> datetime | None:
    try:
        return datetime.strptime(texto, "%d/%m/%Y %H:%M:%S")
    except ValueError:
        return None


def ler_secoes_2022(caminho: Path) -> dict[tuple[Chave, int], dict]:
    """Totais de presidente por par município-zona e turno, a partir das seções."""
    saida: dict[tuple[Chave, int], dict] = {}
    with zipfile.ZipFile(caminho) as zf:
        leitor, c = _leitor(zf, "detalhe_votacao_secao_2022_BR.csv")
        for row in leitor:
            if row[c["CD_CARGO"]] != "1" or row[c["SG_UF"]] == "ZZ":
                continue
            k = chave(row[c["SG_UF"]], row[c["CD_MUNICIPIO"]], row[c["NR_ZONA"]])
            turno = int(row[c["NR_TURNO"]])
            a = saida.setdefault(
                (k, turno),
                {
                    "aptos": 0,
                    "comparecimento": 0,
                    "brancos": 0,
                    "nulos": 0,
                    "nominais": 0,
                    "secoes": 0,
                    "contingencia": 0,
                    "fim": None,
                },
            )
            a["aptos"] += int(row[c["QT_APTOS"]])
            a["comparecimento"] += int(row[c["QT_COMPARECIMENTO"]])
            a["brancos"] += int(row[c["QT_VOTOS_BRANCOS"]])
            a["nulos"] += int(row[c["QT_VOTOS_NULOS"]])
            a["nominais"] += int(row[c["QT_VOTOS_NOMINAIS"]])
            a["secoes"] += 1
            if row[c["DS_ORIGEM_VOTO"]] != "Urna Eletrônica":
                a["contingencia"] += 1
            quando = _data_br(row[c["DT_PRIM_TOT_PARCIAL_HOR_TSE"]]) or _data_br(
                row[c["DT_RECEBIMENTO_BU_HOR_TSE"]]
            )
            if quando is not None:
                quando = min(quando, FECHAMENTO_2022 + TETO_ATRASO_2022)
                if a["fim"] is None or quando > a["fim"]:
                    a["fim"] = quando
    return saida


def _sem_acento(texto: str) -> str:
    base = unicodedata.normalize("NFKD", texto.upper())
    return "".join(ch for ch in base if not unicodedata.combining(ch))


PADRAO_INDIGENA = re.compile(r"INDIGENA|POLO BASE")
PADRAO_ALDEIA = re.compile(r"\bALDEIA\b")
PADRAO_RURAL = re.compile(r"RURAL|INDIGENA|\bT\.?\s?I\b")
PADRAO_QUILOMBO = re.compile(r"QUILOMB")


def classificar_local(nome: str, endereco: str, bairro: str) -> tuple[bool, bool]:
    """(indígena, quilombola) pelo texto do local, do endereço e do bairro.

    "Aldeia" sozinha não basta, porque há bairros urbanos com esse nome (Aldeia
    da Serra, em Barueri; Aldeia, em Camaragibe): exige também zona rural ou
    menção a indígena.
    """
    texto = _sem_acento(f"{nome} | {endereco} | {bairro}")
    indigena = bool(PADRAO_INDIGENA.search(texto)) or bool(
        PADRAO_ALDEIA.search(texto) and PADRAO_RURAL.search(texto)
    )
    return indigena, bool(PADRAO_QUILOMBO.search(texto))


def _coord(texto: str) -> float | None:
    try:
        valor = float(texto.replace(",", "."))
    except ValueError:
        return None
    return None if valor in (-1.0, 0.0) else valor


def ler_locais_2026(caminho: Path) -> dict[Chave, list[tuple]]:
    """Seções de 2026 por par município-zona: (eleitores, lat, lon, ind., quil.)."""
    saida: dict[Chave, list[tuple]] = defaultdict(list)
    with zipfile.ZipFile(caminho) as zf:
        nomes = [
            n
            for n in zf.namelist()
            if n.endswith(".csv") and not n.endswith(("_BRASIL.csv", "_ZZ.csv"))
        ]
        for nome in sorted(nomes):
            leitor, c = _leitor(zf, nome)
            for row in leitor:
                k = chave(row[c["SG_UF"]], row[c["CD_MUNICIPIO"]], row[c["NR_ZONA"]])
                indigena, quilombola = classificar_local(
                    row[c["NM_LOCAL_VOTACAO"]],
                    row[c["DS_ENDERECO"]],
                    row[c["NM_BAIRRO"]],
                )
                saida[k].append(
                    (
                        int(row[c["QT_ELEITOR_ELEICAO_FEDERAL"]] or 0),
                        _coord(row[c["NR_LATITUDE"]]),
                        _coord(row[c["NR_LONGITUDE"]]),
                        indigena,
                        quilombola,
                        row[c["DS_TIPO_SECAO_AGREGADA"]] == "Principal",
                    )
                )
    return dict(saida)


def _anel_centroide(anel: list) -> tuple[float, float, float]:
    """Área com sinal e centroide de um anel pela fórmula do laço."""
    area = cx = cy = 0.0
    for (x0, y0), (x1, y1) in zip(anel, anel[1:] + anel[:1], strict=True):
        cruz = x0 * y1 - x1 * y0
        area += cruz
        cx += (x0 + x1) * cruz
        cy += (y0 + y1) * cruz
    area /= 2.0
    if abs(area) < 1e-15:
        xs = [p[0] for p in anel]
        ys = [p[1] for p in anel]
        return 0.0, sum(xs) / len(xs), sum(ys) / len(ys)
    return area, cx / (6.0 * area), cy / (6.0 * area)


def ler_centroides(pasta: Path) -> dict[str, dict]:
    """Centroide de área e retângulo envolvente de cada município (código IBGE)."""
    saida: dict[str, dict] = {}
    for arquivo in sorted(pasta.glob("*.geojson")):
        dados = json.loads(arquivo.read_text(encoding="utf-8"))
        for feature in dados["features"]:
            geo = feature["geometry"]
            poligonos = (
                [geo["coordinates"]] if geo["type"] == "Polygon" else geo["coordinates"]
            )
            area_total = sx = sy = 0.0
            xs: list[float] = []
            ys: list[float] = []
            for poligono in poligonos:
                externo = [tuple(p[:2]) for p in poligono[0]]
                area, cx, cy = _anel_centroide(externo)
                peso = abs(area)
                area_total += peso
                sx += cx * peso
                sy += cy * peso
                xs += [p[0] for p in externo]
                ys += [p[1] for p in externo]
            if area_total > 0:
                lon, lat = sx / area_total, sy / area_total
            else:
                lon, lat = sum(xs) / len(xs), sum(ys) / len(ys)
            saida[str(feature["properties"]["codarea"])] = {
                "lat": lat,
                "lon": lon,
                "bbox": (min(xs), min(ys), max(xs), max(ys)),
            }
    return saida


# Ponte por local de votação, para zonas redesenhadas desde 2022 ----------------

Municipio = tuple[str, str]  # (uf minúscula, código TSE 5 dígitos)


def normalizar_local(texto: str) -> str:
    """Nome ou endereço sem acento, sem pontuação e com espaços simples."""
    base = re.sub(r"[^A-Z0-9 ]+", " ", _sem_acento(texto or ""))
    return re.sub(r"\s+", " ", base).strip()


def ler_locais_2022(caminho: Path, municipios: set[Municipio]) -> dict:
    """Locais de 2022 dos municípios pedidos, com totais de presidente.

    Chave (município, zona de 2022, número do local). Valor: nome, endereço e
    somas do 1º turno (aptos, comparecimento, brancos, nulos, nominais) e os
    nominais do 2º turno.
    """
    saida: dict = {}
    with zipfile.ZipFile(caminho) as zf:
        leitor, c = _leitor(zf, "detalhe_votacao_secao_2022_BR.csv")
        for row in leitor:
            if row[c["CD_CARGO"]] != "1":
                continue
            mun = (row[c["SG_UF"]].lower(), row[c["CD_MUNICIPIO"]].zfill(5))
            if mun not in municipios:
                continue
            k = (mun, row[c["NR_ZONA"]].zfill(4), row[c["NR_LOCAL_VOTACAO"]])
            a = saida.setdefault(
                k,
                {
                    "nome": normalizar_local(row[c["NM_LOCAL_VOTACAO"]]),
                    "endereco": normalizar_local(row[c["DS_LOCAL_VOTACAO_ENDERECO"]]),
                    "aptos": 0,
                    "comparecimento": 0,
                    "brancos": 0,
                    "nulos": 0,
                    "nominais": 0,
                    "nominais_2t": 0,
                },
            )
            if row[c["NR_TURNO"]] == "2":
                a["nominais_2t"] += int(row[c["QT_VOTOS_NOMINAIS"]])
                continue
            a["aptos"] += int(row[c["QT_APTOS"]])
            a["comparecimento"] += int(row[c["QT_COMPARECIMENTO"]])
            a["brancos"] += int(row[c["QT_VOTOS_BRANCOS"]])
            a["nulos"] += int(row[c["QT_VOTOS_NULOS"]])
            a["nominais"] += int(row[c["QT_VOTOS_NOMINAIS"]])
    return saida


def _local_vazio() -> dict[str, Any]:
    return {"eleitores": 0, "nome": "", "nome_original": "", "endereco": ""}


def ler_locais_2026_nomes(caminho: Path, municipios: set[Municipio]) -> dict:
    """Locais de 2026 dos municípios pedidos: zona, nomes, endereço, eleitores."""
    saida: dict[tuple, dict[str, Any]] = defaultdict(_local_vazio)
    with zipfile.ZipFile(caminho) as zf:
        ufs = {uf.upper() for uf, _ in municipios}
        for uf in sorted(ufs):
            leitor, c = _leitor(zf, f"eleitorado_local_votacao_2026_{uf}.csv")
            for row in leitor:
                mun = (row[c["SG_UF"]].lower(), row[c["CD_MUNICIPIO"]].zfill(5))
                if mun not in municipios:
                    continue
                k = (mun, row[c["NR_ZONA"]].zfill(4), row[c["NR_LOCAL_VOTACAO"]])
                a = saida[k]
                a["nome"] = normalizar_local(row[c["NM_LOCAL_VOTACAO"]])
                a["nome_original"] = normalizar_local(
                    row[c["NM_LOCAL_VOTACAO_ORIGINAL"]]
                )
                a["endereco"] = normalizar_local(row[c["DS_ENDERECO"]])
                a["eleitores"] += int(row[c["QT_ELEITOR_ELEICAO_FEDERAL"]] or 0)
    return dict(saida)


def cruzar_locais(locais22: dict, locais26: dict) -> dict:
    """Ponte local de 2026 → local de 2022 dentro do mesmo município.

    Casa pelo nome (atual ou original) e, havendo mais de um local de 2022 com
    o mesmo nome, desempata pelo endereço. Sem nome, tenta o endereço único.
    Devolve {chave do local de 2026: chave do local de 2022}.
    """
    por_nome: dict = defaultdict(list)
    por_endereco: dict = defaultdict(list)
    for k22, a in locais22.items():
        por_nome[(k22[0], a["nome"])].append(k22)
        if a["endereco"]:
            por_endereco[(k22[0], a["endereco"])].append(k22)
    ponte = {}
    for k26, a in locais26.items():
        mun = k26[0]
        candidatos = list(
            dict.fromkeys(
                por_nome.get((mun, a["nome"]), [])
                + por_nome.get((mun, a.get("nome_original", "")), [])
            )
        )
        if len(candidatos) > 1:
            candidatos = [
                k for k in candidatos if locais22[k]["endereco"] == a["endereco"]
            ]
        if not candidatos and a["endereco"]:
            candidatos = por_endereco.get((mun, a["endereco"]), [])
        if len(candidatos) == 1:
            ponte[k26] = candidatos[0]
    return ponte


def referencia_por_locais(
    locais22: dict, locais26: dict, ponte: dict, votos22: dict
) -> dict[Chave, dict]:
    """Referência de 2022 recomposta na geografia das zonas de 2026.

    Cada local de 2022 é repartido entre as zonas de 2026 que o herdaram, na
    proporção do eleitorado de 2026. Aptos, comparecimento, brancos e nulos
    somam exatos por local. Os votos por candidato saem da composição: o
    nominal herdado de cada zona de 2022 vezes a divisão de votos daquela zona
    inteira. É aproximação, e a cobertura (eleitorado de 2026 casado) vai junto.
    """
    eleitores_por_local22: dict = defaultdict(int)
    for k26, k22 in ponte.items():
        eleitores_por_local22[k22] += locais26[k26]["eleitores"]
    saida: dict[Chave, dict] = {}
    for k26, a26 in locais26.items():
        (uf, mun), zona26, _ = k26
        alvo = saida.setdefault(
            (uf, mun, zona26),
            {
                "eleitores_2026": 0,
                "eleitores_casados": 0,
                "aptos": 0.0,
                "comparecimento": 0.0,
                "brancos": 0.0,
                "nulos": 0.0,
                "votos_1t": Counter(),
                "votos_2t": Counter(),
            },
        )
        alvo["eleitores_2026"] += a26["eleitores"]
        k22 = ponte.get(k26)
        if k22 is None or not eleitores_por_local22[k22]:
            continue
        fracao = a26["eleitores"] / eleitores_por_local22[k22]
        a22 = locais22[k22]
        alvo["eleitores_casados"] += a26["eleitores"]
        for campo in ("aptos", "comparecimento", "brancos", "nulos"):
            alvo[campo] += fracao * a22[campo]
        zona22 = (uf, mun, k22[1])
        for turno, campo in ((1, "nominais"), (2, "nominais_2t")):
            total = sum(votos22.get((zona22, turno), Counter()).values())
            if not total:
                continue
            for numero, v in votos22[(zona22, turno)].items():
                alvo[f"votos_{turno}t"][numero] += fracao * a22[campo] * v / total
    for alvo in saida.values():
        alvo["cobertura"] = (
            alvo["eleitores_casados"] / alvo["eleitores_2026"]
            if alvo["eleitores_2026"]
            else 0.0
        )
    return saida
