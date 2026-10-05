"""Leitura das fontes do capítulo "O caminho do 2º turno".

Só leitura, sem conta: banco da apuração (aberto em modo somente leitura,
com o coletor ainda gravando), arquivos do TSE de 2022, a tabela municipal de
2022 e os JSON da casa. A aritmética fica em ``estrategia.py``.

Regra de leitura do banco, a mesma de ``apuracao/src/db/leitura.ts``
(``ultimoSnapshotComCandidatos``): para cada arquivo, a última versão não
regressiva capturada até o corte ``ate`` que tenha votos por candidatura.
"""

from __future__ import annotations

import csv
import json
import sqlite3
import unicodedata
import zipfile
from collections.abc import Iterable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BANCO = ROOT / "apuracao/data/apuracao.sqlite"
CAMPOS = ROOT / "apuracao/public/campos.json"
FINAL = ROOT / "apuracao/data/boletins/final.json"
API_2022 = ROOT / "data/raw/tse_resultados/api_2022"
MUNICIPIOS_2022 = ROOT / "data/outputs/estaduais2026/municipios.csv"
MUNZONA_2022 = ROOT / "data/raw/tse_resultados/votacao_candidato_munzona_2022.zip"
VOTO_UTIL = ROOT / "docs/assets/voto_util_092026.json"
DATAFOLHA_NACIONAL = ROOT / "docs/assets/datafolha_21092026_data.json"
DATAFOLHA_SUDESTE = ROOT / "docs/assets/datafolha_21092026_sudeste.json"
PREDICAO = ROOT / "docs/assets/predicao_2026_1T_presidente.json"
ERRO_2022 = ROOT / "analysis/predicao_2026/erro_2022/erro_2022.json"

ELEICAO_FEDERAL = 6257
ELEICAO_ESTADUAL = 6259
PRESIDENTE = 1
GOVERNADOR = 3
SENADOR = 5
DEPUTADO_FEDERAL = 6

SQL_ULTIMO = """
SELECT a.id, a.nivel, a.uf, a.municipio_cd,
  (SELECT s.id FROM snapshot s
     WHERE s.arquivo_id = a.id AND s.regressivo = 0 AND s.capturado_em <= ?
       AND EXISTS (SELECT 1 FROM voto_candidato vc WHERE vc.snapshot_id = s.id)
     ORDER BY s.id DESC LIMIT 1) AS sid
FROM arquivo a
WHERE a.tipo = 'u' AND a.eleicao_cd = ? AND a.cargo_cd = ? AND a.nivel IN ({niveis})
"""

SQL_TOTAIS = """
SELECT s.id, s.capturado_em, s.gerado_em, s.tf, t.ts, t.st, t.te, t.comparecimento,
       t.abstencao, t.vv, t.vvc, t.vb, t.tvn
FROM snapshot s LEFT JOIN totais t ON t.snapshot_id = s.id
WHERE s.id IN ({ids})
"""

SQL_VOTOS = """
SELECT vc.snapshot_id, vc.sqcand, vc.vap, vc.st, c.nome_urna, c.numero,
       p.sigla, f.sigla
FROM voto_candidato vc
LEFT JOIN candidato c ON c.sqcand = vc.sqcand
LEFT JOIN partido p ON p.n = c.partido_n
LEFT JOIN federacao f ON f.n = c.federacao_n
WHERE vc.snapshot_id IN ({ids})
"""


def sem_acento(texto: str) -> str:
    """Caixa alta sem acento, para casar nomes entre fontes."""
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).upper().strip()


def conectar(caminho: Path = BANCO) -> sqlite3.Connection:
    """Abre o banco só para leitura; o coletor pode continuar gravando no WAL."""
    return sqlite3.connect(f"file:{caminho}?mode=ro", uri=True)


def classificador(caminho: Path = CAMPOS) -> dict:
    """Partido e exceções por candidatura de ``apuracao/public/campos.json``."""
    bruto = json.loads(caminho.read_text(encoding="utf-8"))
    partidos = {k.upper(): v for k, v in bruto.get("partidos", {}).items()}
    return {"partidos": partidos, "excecoes": dict(bruto.get("excecoes", {}))}


def campo_de(cl: dict, sqcand: str | None, *siglas: str | None) -> str:
    """Exceção por candidatura vence; depois o partido; depois a federação."""
    if sqcand and sqcand in cl["excecoes"]:
        return cl["excecoes"][sqcand]
    for sigla in siglas:
        if sigla and sigla.upper() in cl["partidos"]:
            return cl["partidos"][sigla.upper()]
    return "indefinido"


def _em_lotes(ids: list[int], tamanho: int = 900) -> Iterable[list[int]]:
    for i in range(0, len(ids), tamanho):
        yield ids[i : i + tamanho]


def ler_disputas(
    con: sqlite3.Connection,
    eleicao: int,
    cargo: int,
    niveis: tuple[str, ...],
    ate: str,
    cl: dict,
) -> dict[tuple[str, str], dict]:
    """Última versão de cada arquivo do cargo, chave (uf, município).

    Nível ``br`` usa a chave ("BR", ""); nível ``uf``, (UF, ""); nível ``mu``,
    (UF, código TSE do município com cinco dígitos).
    """
    marcas = ",".join("?" for _ in niveis)
    linhas = con.execute(
        SQL_ULTIMO.format(niveis=marcas), (ate, eleicao, cargo, *niveis)
    ).fetchall()
    por_sid: dict[int, tuple[str, str, str]] = {}
    for _id, nivel, uf, mun, sid in linhas:
        if sid is None:
            continue
        chave_uf = "BR" if nivel == "br" else (uf or "").upper()
        por_sid[sid] = (chave_uf, mun or "", nivel)
    ids = sorted(por_sid)
    saida: dict[tuple[str, str], dict] = {}
    for lote in _em_lotes(ids):
        marcas = ",".join("?" for _ in lote)
        for sid, cap, ger, tf, ts, st, te, comp, abst, vv, vvc, vb, tvn in con.execute(
            SQL_TOTAIS.format(ids=marcas), lote
        ):
            uf, mun, nivel = por_sid[sid]
            saida[(uf, mun)] = {
                "uf": uf,
                "municipio_cd": mun,
                "nivel": nivel,
                "snapshot_id": sid,
                "capturado_em": cap,
                "gerado_em": ger,
                "tf": bool(tf),
                "secoes": ts or 0,
                "secoes_totalizadas": st or 0,
                "eleitores": te or 0,
                "comparecimento": comp or 0,
                "abstencao": abst or 0,
                # Base do percentual publicado pelo TSE (pvapn): válidos mais
                # votos anulados sub judice (Garotinho no RJ, por exemplo).
                "validos": vvc or vv or 0,
                "validos_sem_sub_judice": vv or 0,
                "brancos": vb or 0,
                "nulos": tvn or 0,
                "candidatos": [],
            }
        for sid, sq, vap, st, nome, numero, sigla, fed in con.execute(
            SQL_VOTOS.format(ids=marcas), lote
        ):
            uf, mun, _ = por_sid[sid]
            sq_txt = str(sq)
            saida[(uf, mun)]["candidatos"].append(
                {
                    "sqcand": sq_txt,
                    "nome": nome or sq_txt,
                    "numero": numero,
                    "partido": sigla or "?",
                    "campo": campo_de(cl, sq_txt, sigla, fed),
                    "votos": vap or 0,
                    "st": st,
                }
            )
    for disputa in saida.values():
        disputa["candidatos"].sort(key=lambda c: (-c["votos"], c["numero"] or 0))
    return saida


def ler_municipios_meta(con: sqlite3.Connection) -> dict[tuple[str, str], dict]:
    """Nome, código IBGE e marca de capital de cada município do banco."""
    saida = {}
    for cd, uf, ibge, nome, capital in con.execute(
        "SELECT cd, uf, ibge, nome, capital FROM municipio"
    ):
        saida[(uf.upper(), cd)] = {
            "nome": nome,
            "ibge": ibge,
            "capital": bool(capital),
        }
    return saida


def _inteiro(valor: str | None) -> int:
    return int(valor) if valor not in (None, "") else 0


def ler_api_2022(uf: str, turno: int, pasta: Path = API_2022) -> dict:
    """Resultado presidencial de 2022 por UF (ou ``br``/``zz``), arquivo do TSE."""
    eleicao = "000544" if turno == 1 else "000545"
    caminho = pasta / f"{uf.lower()}-c0001-e{eleicao}-r.json"
    bruto = json.loads(caminho.read_text(encoding="utf-8"))
    votos = {c["nm"]: _inteiro(c["vap"]) for c in bruto["cand"]}
    validos = _inteiro(bruto["vv"])
    return {
        "arquivo": str(caminho.relative_to(ROOT)),
        "eleitores": _inteiro(bruto["e"]),
        "comparecimento": _inteiro(bruto["c"]),
        "abstencao": _inteiro(bruto["a"]),
        "validos": validos,
        "brancos": _inteiro(bruto["vb"]),
        "nulos": _inteiro(bruto["tvn"]),
        "lula": votos.get("LULA", 0),
        "bolsonaro": votos.get("JAIR BOLSONARO", 0),
        "terceiros": validos - votos.get("LULA", 0) - votos.get("JAIR BOLSONARO", 0),
    }


def ler_municipios_2022(caminho: Path = MUNICIPIOS_2022) -> dict[tuple[str, str], dict]:
    """Votos presidenciais de 2022 por município, chave (UF, código TSE 5 dígitos)."""
    saida = {}
    with caminho.open(encoding="utf-8") as arq:
        for linha in csv.DictReader(arq):
            chave = (linha["uf"].upper(), linha["codigo_tse"].zfill(5))
            lula_1t = _inteiro(linha["lula_1t"])
            bolsonaro_1t = _inteiro(linha["bolsonaro_1t"])
            validos_1t = _inteiro(linha["validos_1t"])
            saida[chave] = {
                "nome": linha["municipio"],
                "lula_1t": lula_1t,
                "bolsonaro_1t": bolsonaro_1t,
                "validos_1t": validos_1t,
                "terceiros_1t": validos_1t - lula_1t - bolsonaro_1t,
                "lula_2t": _inteiro(linha["lula_2t"]),
                "bolsonaro_2t": _inteiro(linha["bolsonaro_2t"]),
            }
    return saida


def ufs_com_2t_governador_2022(caminho: Path = MUNZONA_2022) -> list[str]:
    """UFs que tiveram 2º turno de governador em 2022.

    Varre os arquivos por UF de ``votacao_candidato_munzona_2022.zip`` e marca
    a UF quando há linha de Governador com ``NR_TURNO`` igual a 2. Só as
    linhas de Governador são quebradas em colunas, para a varredura levar
    segundos e não minutos.
    """
    ufs = []
    with zipfile.ZipFile(caminho) as z:
        for info in z.infolist():
            nome = info.filename
            if not nome.startswith("votacao_candidato_munzona_2022_"):
                continue
            uf = nome.removesuffix(".csv").rsplit("_", 1)[-1]
            if len(uf) != 2 or uf == "BR":
                continue
            with z.open(info) as arq:
                cabecalho = next(arq).decode("latin-1").strip().split(";")
                col_turno = cabecalho.index('"NR_TURNO"')
                for linha in arq:
                    if b'"Governador"' not in linha:
                        continue
                    if linha.split(b";")[col_turno].strip(b'"') == b"2":
                        ufs.append(uf)
                        break
    return sorted(ufs)


def ler_json(caminho: Path) -> dict:
    return json.loads(caminho.read_text(encoding="utf-8"))


def relativo(caminho: Path) -> str:
    """Caminho relativo à raiz do repositório, para citar a fonte."""
    return str(caminho.relative_to(ROOT))
