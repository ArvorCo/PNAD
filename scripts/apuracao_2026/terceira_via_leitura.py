"""Leitura das fontes da análise "Onde está o voto da terceira via, cidade por cidade".

Só leitura, sem conta. A aritmética fica em ``terceira_via.py`` e a montagem do
JSON em ``terceira_via_secoes.py``.

Fontes:

- banco da apuração (``apuracao/data/apuracao.sqlite``, somente leitura):
  presidente (eleição 6257, cargo 1), governador (6259, cargo 3) e Senado
  (6259, cargo 5), arquivos de UF e de município. Versão vigente de cada arquivo
  = a última gerada pelo TSE (maior ``gerado_em``), a regra de ``banco.py``;
  versão sem linhas normalizadas é lida do corpo guardado em ``blob``;
- 2022: ``data/outputs/estaduais2026/municipios.csv`` (votos de presidente por
  município nos dois turnos, com Ciro e Tebet) e o membro ``_BR.csv`` de
  ``data/raw/tse_resultados/detalhe_votacao_secao_2022.zip`` (aptos,
  comparecimento, brancos e nulos de presidente por seção, os dois turnos);
- JSON da casa: ``estrategia_2t.json`` (matrizes de transferência e a linha de
  cada candidatura), ``senado_x_flavio.json`` (bloco aliado ao Senado e
  carregadores), ``governadores.json`` (vão estadual e lado de cada governador) e
  ``exterior.json`` (país de cada cidade do exterior).
"""

from __future__ import annotations

import csv
import io
import json
import zipfile
from pathlib import Path
from typing import Any

from .banco import Banco
from .dados import versoes_genuinas

ROOT = Path(__file__).resolve().parents[2]
BANCO = ROOT / "apuracao/data/apuracao.sqlite"
DADOS = ROOT / "analysis/apuracao_2026/dados"
MUNICIPIOS_2022 = ROOT / "data/outputs/estaduais2026/municipios.csv"
DETALHE_2022 = ROOT / "data/raw/tse_resultados/detalhe_votacao_secao_2022.zip"
MEMBRO_DETALHE = "detalhe_votacao_secao_2022_BR.csv"
API_2022 = ROOT / "data/raw/tse_resultados/api_2022"

ELEICAO_FEDERAL = 6257
ELEICAO_ESTADUAL = 6259
PRESIDENTE = 1
GOVERNADOR = 3
SENADOR = 5

CAMPOS_DETALHE = (
    "NR_TURNO",
    "CD_MUNICIPIO",
    "CD_CARGO",
    "QT_APTOS",
    "QT_COMPARECIMENTO",
    "QT_VOTOS_BRANCOS",
    "QT_VOTOS_NULOS",
)
CONTAS_DETALHE = ("aptos", "comparecimento", "brancos", "nulos")


def relativo(caminho: Path) -> str:
    return str(caminho.relative_to(ROOT))


# ---------------------------------------------------------------- banco


def ler_cargo(
    banco: Banco, eleicao: int, cargo: int, niveis: tuple[str, ...]
) -> dict[str, Any]:
    """Versão vigente de cada arquivo do cargo, com totais e votos por candidatura.

    Devolve ``{"candidatos": {sqcand: linha}, "arquivos": {chave: arquivo}}``.
    A chave do arquivo é ``"BR"`` no nível nacional, a UF em caixa alta no nível
    de UF e o código TSE de cinco dígitos no nível de município.
    """
    cands = {str(c["sqcand"]): c for c in banco.candidatos(eleicao, cargo)}
    marcas = ",".join("?" for _ in niveis)
    arqs = banco.arquivos(
        f"tipo = 'u' AND eleicao_cd = ? AND cargo_cd = ? AND nivel IN ({marcas})",
        (eleicao, cargo, *niveis),
    )
    snaps = banco.snapshots([a["id"] for a in arqs])
    vigentes: dict[str, dict[str, Any]] = {}
    for a in arqs:
        versoes = versoes_genuinas(snaps.get(a["id"], []))
        if not versoes:
            continue
        snap = banco.completar_totais(dict(versoes[-1]))
        if a["nivel"] == "br":
            chave = "BR"
        elif a["nivel"] == "uf":
            chave = (a["uf"] or "").upper()
        else:
            chave = a["municipio_cd"]
        vigentes[chave] = {
            "nivel": a["nivel"],
            "uf": (a["uf"] or "").upper(),
            "cd": a["municipio_cd"],
            "snapshot_id": snap["id"],
            "sha256": snap["sha256"],
            "gerado_em": snap["gerado_em"],
            "secoes": snap["st"] or 0,
            "secoes_total": snap["ts"] or 0,
            "eleitores": snap["te"] or 0,
            "comparecimento": snap["comparecimento"] or 0,
            "validos": snap["vv"] or 0,
            "brancos": snap["vb"] or 0,
            "nulos": snap["tvn"] or 0,
        }
    votos = banco.votos(
        [{"id": v["snapshot_id"], "sha256": v["sha256"]} for v in vigentes.values()]
    )
    for v in vigentes.values():
        v["votos"] = {sq: n or 0 for sq, n in votos[v["snapshot_id"]].items()}
    banco.esquecer_documentos()
    return {"candidatos": cands, "arquivos": vigentes}


def ler_banco(caminho: Path = BANCO) -> dict[str, Any]:
    """Presidente (nacional, UF, município e exterior), governador e Senado."""
    banco = Banco(caminho)
    try:
        saida = {
            "pres": ler_cargo(banco, ELEICAO_FEDERAL, PRESIDENTE, ("br", "uf", "mu")),
            "gov": ler_cargo(banco, ELEICAO_ESTADUAL, GOVERNADOR, ("uf", "mu")),
            "sen": ler_cargo(banco, ELEICAO_ESTADUAL, SENADOR, ("uf", "mu")),
            "municipios": {m["cd"]: m for m in banco.municipios()},
        }
    finally:
        banco.fechar()
    return saida


# ---------------------------------------------------------------- 2022


def _inteiro(valor: str | None) -> int:
    return int(valor) if valor not in (None, "") else 0


def ler_municipios_2022(caminho: Path = MUNICIPIOS_2022) -> dict[str, dict]:
    """Presidente 2022 por município, chave = código TSE com cinco dígitos."""
    saida = {}
    with caminho.open(encoding="utf-8") as arq:
        for linha in csv.DictReader(arq):
            cd = linha["codigo_tse"].zfill(5)
            saida[cd] = {
                "uf": linha["uf"].upper(),
                "lula_1t": _inteiro(linha["lula_1t"]),
                "bolsonaro_1t": _inteiro(linha["bolsonaro_1t"]),
                "ciro_1t": _inteiro(linha["ciro_1t"]),
                "tebet_1t": _inteiro(linha["tebet_1t"]),
                "validos_1t": _inteiro(linha["validos_1t"]),
                "lula_2t": _inteiro(linha["lula_2t"]),
                "bolsonaro_2t": _inteiro(linha["bolsonaro_2t"]),
            }
    return saida


def _campo(valor: bytes) -> int:
    return int(valor.strip().strip(b'"'))


def ler_detalhe_2022(
    caminho: Path = DETALHE_2022, membro: str = MEMBRO_DETALHE
) -> dict[str, dict[int, dict[str, int]]]:
    """Aptos, comparecimento, brancos e nulos de presidente em 2022, por município.

    Chave: código TSE com cinco dígitos; valor: ``{turno: contas}``. Lê o CSV
    seção a seção sem descompactar no disco; os campos usados ficam antes dos
    textos livres (local e endereço), o que permite cortar a linha sem o parser
    de CSV.
    """
    saida: dict[str, dict[int, dict[str, int]]] = {}
    with zipfile.ZipFile(caminho) as zf, zf.open(membro) as bruto:
        leitor = io.BufferedReader(bruto, buffer_size=1 << 20)
        cab = [
            c.strip().strip('"') for c in leitor.readline().decode("latin-1").split(";")
        ]
        idx = [cab.index(c) for c in CAMPOS_DETALHE]
        corte = max(idx) + 1
        i_turno, i_cd, i_cargo, *i_contas = idx
        for linha in leitor:
            campos = linha.split(b";", corte)
            if campos[i_cargo].strip(b'"') != b"1":
                continue
            cd = f"{_campo(campos[i_cd]):05d}"
            turno = _campo(campos[i_turno])
            alvo = saida.setdefault(cd, {}).setdefault(
                turno, dict.fromkeys(CONTAS_DETALHE, 0)
            )
            for conta, i in zip(CONTAS_DETALHE, i_contas, strict=True):
                alvo[conta] += _campo(campos[i])
    return saida


def ler_api_2022_br(turno: int, pasta: Path = API_2022) -> dict[str, int]:
    """Totais de presidente de 2022 no arquivo nacional do TSE, para conferência."""
    eleicao = "000544" if turno == 1 else "000545"
    doc = json.loads((pasta / f"br-c0001-e{eleicao}-r.json").read_text("utf-8"))
    return {
        "comparecimento": _inteiro(doc["c"]),
        "brancos": _inteiro(doc["vb"]),
        "nulos": _inteiro(doc["tvn"]),
        "validos": _inteiro(doc["vv"]),
    }


# ---------------------------------------------------------------- JSON da casa


def ler_json(nome: str, pasta: Path = DADOS) -> dict:
    return json.loads((pasta / nome).read_text(encoding="utf-8"))


def ler_tudo() -> dict[str, Any]:
    """Todas as fontes, lidas uma vez."""
    fontes = ler_banco()
    fontes["mun22"] = ler_municipios_2022()
    fontes["det22"] = ler_detalhe_2022()
    fontes["api22"] = {t: ler_api_2022_br(t) for t in (1, 2)}
    for nome in (
        "estrategia_2t.json",
        "senado_x_flavio.json",
        "governadores.json",
        "exterior.json",
        "presidente.json",
    ):
        fontes[nome.removesuffix(".json")] = ler_json(nome)
    return fontes
