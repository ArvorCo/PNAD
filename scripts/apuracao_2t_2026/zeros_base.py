"""Base do bloco "Seções com zero voto": regra declarada e leitura das fontes.

Constantes (caminhos, manchete de partida, definição, regra do tipo de local),
utilidades e leitores somente leitura das fontes; as contagens, as fichas e a
conferência ficam em ``zeros_dados``. Fontes:

- bancos de BUs por seção dos dois turnos de 2026
  (``apuracao/data/secoes_2t_2026.sqlite`` e ``secoes_2026.sqlite``, ``mode=ro``): ``bu_cargo`` (cargo 1) dá aptos e
  comparecimento, ``voto_secao`` dá os votos (cargo 1; tipo 1 nominal com ``numero``
  13 Lula e 22 Flávio, 2 branco, 3 nulo) e ``bu`` o modelo da urna;
- 2022 por seção: ``data/outputs/presidente_secao_2022.csv.gz``;
- nome do local e fatia de Bolsonaro no 2º turno de 2022 por seção, pelo cadastro do
  Politize (``docs/assets/politize/dados/zona/<UF>/<zona>.json``), e nome do município
  pelo índice do Politize (``indice.json``);
- grupo da mistura gaussiana por seção (``anomalia_secoes.json.gz``, ponteiro em
  ``anomalia_ml.json``), quando o arquivo pesado existe; sem ele, o cruzamento fica
  marcado como indisponível e o resto não muda.

**Tipo do local**: regra por palavra no nome do prédio, na ordem de ``TIPOS`` (o
primeiro que casa vence), mais três municípios do Maranhão tratados como comunidade
(``MUNICIPIOS_COMUNIDADE``). Nome e palavra são comparados em maiúsculas, sem acento,
com espaços repetidos reduzidos a um e o apóstrofo colado às letras vizinhas; termo
com apóstrofo casa também com o nome sem espaços, porque o mesmo prédio aparece
grafado ``TAPI'ITAWA``, ``TAPI ' ITAWA``, ``TAPIITAWA`` e ``TAPI  ITAWA``. Nome que
não diz o tipo fica como outro local: a regra é conservadora, não adivinha.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import re
import sqlite3
import statistics
import unicodedata
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NamedTuple

from . import anomalia_linhas

ROOT = Path(__file__).resolve().parents[2]
DADOS = ROOT / "analysis/apuracao_2t_2026/dados"
SAIDA = DADOS / "zeros.json"
BANCO_2T = ROOT / "apuracao/data/secoes_2t_2026.sqlite"
BANCO_1T = ROOT / "apuracao/data/secoes_2026.sqlite"
CSV_2022 = ROOT / "data/outputs/presidente_secao_2022.csv.gz"
POLITIZE = ROOT / "docs/assets/politize/dados"
INDICE = POLITIZE / "indice.json"
ANOMALIA = DADOS / "anomalia_ml.json"
REFERENCIA = DADOS / "flavio_zero_2t_2026.csv"
SCRIPT = "scripts/apuracao-2t-2026-zeros.py"
ROTULO = "atipicidade pede explicação, não prova irregularidade"

MANCHETE = {
    "veiculo": "Folha de S.Paulo",
    "coluna": "Painel",
    "autor": "Carlos Petrocilo",
    "data": "2026-10-27",
    "titulo": "Flávio teve zero voto em 106 urnas, nas quais Lula somou quase 15 mil",
    "url": (
        "https://www1.folha.uol.com.br/colunas/painel/2026/10/"
        "flavio-teve-zero-voto-em-106-urnas-nas-quais-somou-quase-15-mil.shtml"
    ),
    "arquivo": "data/originals/folha_102026_27/painel_27102026.html",
    "atribuicao": "levantamento da Paris Group, com mapeamento das seções por inteligência artificial",
    # Números publicados na coluna, conferidos abaixo contra os BUs.
    "por_regiao": {
        "Norte": 65,
        "Nordeste": 29,
        "Centro-Oeste": 6,
        "Sudeste": 3,
        "Sul": 3,
    },
    "amazonas_cidades": 13,
    "nota": (
        "coluna arquivada com SHA-256 em data/originals/folha_102026_27/fonte.json. "
        "O número é refeito abaixo a partir dos bancos de BUs."
    ),
}

DEFINICAO = (
    "Seção com BU do cargo presidente e nenhum voto nominal do candidato (sem "
    "linha em voto_secao). Brasil sem o exterior no número principal; exterior à "
    "parte. Em 2022, "
    "linha do arquivo por seção com votos preenchidos."
)

LULA, FLAVIO = 13, 22
CANDIDATOS = {
    2026: {"direita": "Flávio Bolsonaro", "lula": "Lula"},
    2022: {"direita": "Jair Bolsonaro", "lula": "Lula"},
}

# Ordem de prioridade: o primeiro tipo cujo termo aparece no nome vence.
TIPOS: list[tuple[str, str, list[str]]] = [
    (
        "aldeia_indigena",
        "aldeia ou escola indígena",
        [
            "ALDEIA",
            "INDÍGENA",
            "INDIGENA",
            "TUXAUA",
            "TUCHAUA",
            "MALOCA",
            "TUKUNA",
            "TIKUNA",
            "INGARICÓ",
            "MACUXI",
            "TAPI'ITAWA",
            "NAMUKURA",
            "KARAI",
            "CHERU",
            "TAMÃKÃYÃ",
        ],
    ),
    (
        "prisao",
        "unidade prisional ou socioeducativa",
        ["PRESÍDIO", "PENITENCI", "PRISIONAL", "DETEN", "CADEIA", "SOCIOEDUC"],
    ),
    (
        "comunidade",
        "comunidade, quilombo ou ribeirinha",
        [
            "COMUNIDADE",
            "POVOADO",
            "VILA",
            "SÍTIO",
            "FAZENDA",
            "ASSENTAMENTO",
            "QUILOMB",
            "IGARAP",
        ],
    ),
]
OUTRO = ("outro", "outro local")
# Três municípios do Maranhão que a regra trata como comunidade por decisão
# declarada do autor: o nome da escola não diz, e a regra por nome deixaria
# o local como outro.
MUNICIPIOS_COMUNIDADE = {
    ("MA", "Alcântara"),
    ("MA", "Turiaçu"),
    ("MA", "Serrano do Maranhão"),
}
NOME_TIPO = {k: nome for k, nome, _ in TIPOS} | {OUTRO[0]: OUTRO[1]}
ORDEM_TIPOS = [k for k, _, _ in TIPOS] + [OUTRO[0]]
FAIXAS_APTOS = [(0, 99), (100, 199), (200, 299), (300, 399), (400, None)]

Chave = tuple[
    str, str, int, int
]  # (UF maiúscula, município TSE com 5 dígitos, zona, seção)


class Secao(NamedTuple):
    aptos: int
    comparecimento: int
    lula: int
    flavio: int
    brancos: int
    nulos: int
    modelo: str | None


class Secao22(NamedTuple):
    lula_1t: int | None
    bolsonaro_1t: int | None
    lula_2t: int | None
    bolsonaro_2t: int | None
    aptos: int | None
    comparecimento: int | None
    local: str | None


# ------------------------------------------------------------------ utilidades


def sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def agora_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def rel(caminho: Path) -> str:
    return str(caminho.relative_to(ROOT))


def normalizar(s: str | None) -> str:
    """Maiúsculas, sem acento, espaços simples, apóstrofo colado às letras."""
    t = unicodedata.normalize("NFKD", (s or "").upper())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"\s*['’`]\s*", "'", t)
    return re.sub(r"\s+", " ", t).strip()


def compacto(s: str) -> str:
    """Só letras e algarismos: 'TAPI ' ITAWA' e 'TAPIITAWA' viram o mesmo texto."""
    return re.sub(r"[^A-Z0-9]", "", s)


_TERMOS = [(k, [normalizar(p) for p in termos]) for k, _, termos in TIPOS]
_MUNS = {(uf, normalizar(nome)) for uf, nome in MUNICIPIOS_COMUNIDADE}


def casa(termo: str, nome: str) -> bool:
    """Termo normalizado dentro do nome; com apóstrofo, também sem espaços."""
    if termo in nome:
        return True
    return "'" in termo and compacto(termo) in compacto(nome)


def tipo_e_regra(
    local: str | None, uf: str, municipio: str | None
) -> tuple[str, str | None]:
    """(tipo, 'nome' | 'municipio' | None) pela regra de ``TIPOS``."""
    nome = normalizar(local)
    for k, termos in _TERMOS:
        if k == "comunidade" and (uf, normalizar(municipio)) in _MUNS:
            return k, "municipio"
        if any(casa(t, nome) for t in termos):
            return k, "nome"
    return OUTRO[0], None


def tipo_local(local: str | None, uf: str, municipio: str | None) -> str:
    """Tipo do local pela regra declarada em ``TIPOS`` e ``MUNICIPIOS_COMUNIDADE``."""
    return tipo_e_regra(local, uf, municipio)[0]


def inteiro_ou_nada(s: str | None) -> int | None:
    t = (s or "").strip()
    return None if t == "" else round(float(t))


def mediana(xs: Sequence[float]) -> float | None:
    return None if not xs else float(statistics.median(xs))


def quartis(xs: Sequence[float]) -> tuple[float | None, float | None]:
    if len(xs) < 2:
        return (None, None)
    q = statistics.quantiles(xs, n=4, method="inclusive")
    return float(q[0]), float(q[2])


def pct(a: float, b: float, casas: int = 2) -> float | None:
    return None if not b else round(100 * a / b, casas)


# ------------------------------------------------------------------ leitura


SQL_SECOES = """
SELECT b.uf, b.mun, b.zona, b.secao, b.aptos, b.comparecimento,
       COALESCE(v.lula, 0), COALESCE(v.flavio, 0),
       COALESCE(v.brancos, 0), COALESCE(v.nulos, 0), {modelo}
FROM bu_cargo b
LEFT JOIN (
  SELECT uf, mun, zona, secao,
    SUM(CASE WHEN tipo = 1 AND numero = {lula} THEN votos ELSE 0 END) AS lula,
    SUM(CASE WHEN tipo = 1 AND numero = {flavio} THEN votos ELSE 0 END) AS flavio,
    SUM(CASE WHEN tipo = 2 THEN votos ELSE 0 END) AS brancos,
    SUM(CASE WHEN tipo = 3 THEN votos ELSE 0 END) AS nulos
  FROM voto_secao WHERE cargo = 1 GROUP BY uf, mun, zona, secao
) v USING (uf, mun, zona, secao)
{junta}
WHERE b.cargo = 1
"""


def ler_banco(banco: Path, com_modelo: bool) -> dict[Chave, Secao]:
    """Uma linha por seção com BU do cargo presidente (somente leitura)."""
    sql = SQL_SECOES.format(
        lula=LULA,
        flavio=FLAVIO,
        modelo="u.modelo_urna" if com_modelo else "NULL",
        junta="LEFT JOIN bu u USING (uf, mun, zona, secao)" if com_modelo else "",
    )
    con = sqlite3.connect(f"file:{banco}?mode=ro", uri=True)
    try:
        out: dict[Chave, Secao] = {}
        for uf, mun, zona, secao, ap, comp, lu, fl, br, nu, mod in con.execute(sql):
            out[(uf.upper(), str(mun).zfill(5), int(zona), int(secao))] = Secao(
                int(ap or 0), int(comp or 0), lu, fl, br, nu, mod
            )
        return out
    finally:
        con.close()


def ler_2022(caminho: Path = CSV_2022) -> dict[Chave, Secao22]:
    out: dict[Chave, Secao22] = {}
    with gzip.open(caminho, "rt", encoding="utf-8", newline="") as f:
        for x in csv.DictReader(f):
            ch = (
                x["uf"].strip().upper(),
                x["mun"].strip().zfill(5),
                int(float(x["zona"])),
                int(float(x["secao"])),
            )
            out[ch] = Secao22(
                inteiro_ou_nada(x["lula_1t"]),
                inteiro_ou_nada(x["bolsonaro_1t"]),
                inteiro_ou_nada(x["lula_2t"]),
                inteiro_ou_nada(x["bolsonaro_2t"]),
                inteiro_ou_nada(x["aptos_2022"]),
                inteiro_ou_nada(x["comparecimento_2022"]),
                (x.get("local_2022") or "").strip() or None,
            )
    return out


def nomes_municipios(caminho: Path = INDICE) -> dict[tuple[str, str], str]:
    d = json.loads(caminho.read_text(encoding="utf-8"))
    m = d["municipios"]
    i = {k: m["colunas"].index(k) for k in ("uf", "mun_tse", "nome")}
    return {
        (x[i["uf"]], str(x[i["mun_tse"]]).zfill(5)): x[i["nome"]] for x in m["linhas"]
    }


class Politize:
    """Linhas de seção do cadastro do Politize, lidas por zona sob demanda."""

    def __init__(self, base: Path = POLITIZE / "zona") -> None:
        self.base = base
        self.cache: dict[tuple[str, int], dict[tuple[str, int], dict] | None] = {}
        self.lidos: dict[str, str] = {}

    def secao(self, ch: Chave) -> dict | None:
        uf, mun, zona, secao = ch
        z = self._zona(uf, zona)
        return None if z is None else z.get((mun, secao))

    def _zona(self, uf: str, zona: int) -> dict[tuple[str, int], dict] | None:
        k = (uf, zona)
        if k not in self.cache:
            arq = self.base / uf / f"{zona}.json"
            if not arq.exists():
                self.cache[k] = None
            else:
                self.lidos[rel(arq)] = sha256(arq)
                d = json.loads(arq.read_text(encoding="utf-8"))
                cols = d["secoes"]["colunas"]
                linhas = {}
                for x in d["secoes"]["linhas"]:
                    r = dict(zip(cols, x, strict=False))
                    linhas[(str(r["mun_tse"]).zfill(5), int(r["secao"]))] = r
                self.cache[k] = linhas
        return self.cache[k]


def ler_mistura() -> dict[str, Any]:
    """Grupo de cada seção na mistura gaussiana, quando o arquivo pesado existe."""
    if not ANOMALIA.exists():
        return {"disponivel": False, "motivo": "anomalia_ml.json ausente"}
    A = json.loads(ANOMALIA.read_text(encoding="utf-8"))
    b = anomalia_linhas.bloco(A)
    if not b["disponivel"]:
        return {
            "disponivel": False,
            "motivo": f"arquivo pesado ausente: {b['arquivo']}",
        }
    cols = b["colunas"]
    i = {k: cols.index(k) for k in ("uf", "mun", "zona", "secao", "grupo", "anomalo")}
    grupos = {
        (
            str(x[i["uf"]]).upper(),
            str(x[i["mun"]]).zfill(5),
            int(x[i["zona"]]),
            int(x[i["secao"]]),
        ): (
            int(x[i["grupo"]]),
            int(x[i["anomalo"]] or 0),
        )
        for x in b["linhas"]
    }
    return {
        "disponivel": True,
        "grupos": grupos,
        "atipico": int(A["mais_anomalo"]["id"]),
        "rotulos": {
            int(c["id"]): c.get("rotulo_curto") or c.get("rotulo")
            for c in A["componentes"]
        },
        "arquivo": anomalia_linhas.caminho(A),
        "sha256": A["secoes_arquivo"]["sha256"],
    }


__all__ = [
    "ANOMALIA",
    "BANCO_1T",
    "BANCO_2T",
    "CANDIDATOS",
    "CSV_2022",
    "DADOS",
    "DEFINICAO",
    "FAIXAS_APTOS",
    "INDICE",
    "MANCHETE",
    "MUNICIPIOS_COMUNIDADE",
    "NOME_TIPO",
    "ORDEM_TIPOS",
    "OUTRO",
    "REFERENCIA",
    "ROOT",
    "ROTULO",
    "SAIDA",
    "SCRIPT",
    "TIPOS",
    "Chave",
    "Politize",
    "Secao",
    "Secao22",
    "agora_utc",
    "casa",
    "compacto",
    "ler_2022",
    "ler_banco",
    "ler_mistura",
    "mediana",
    "nomes_municipios",
    "normalizar",
    "pct",
    "quartis",
    "rel",
    "sha256",
    "tipo_e_regra",
    "tipo_local",
]
