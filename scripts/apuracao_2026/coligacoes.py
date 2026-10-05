"""Coligações registradas no TSE e a regra de apoio a um finalista presidencial.

Fonte: `data/raw/tse_candidatos_2026/consulta_cand_2026.zip` (consulta de
candidaturas do TSE de 03/10/2026, uma planilha por UF, latin-1, `;`). Só são
lidas as colunas de identificação da candidatura e da coligação; dado pessoal da
planilha (documento, e-mail, título) nunca é carregado.

Regra declarada para dizer de que lado da disputa presidencial está uma
candidatura de governador ou de senador:

1. a coligação inclui o PT (federação Fé Brasil) e não inclui o PL: lado de Lula;
2. a coligação inclui o PL e não inclui o PT: lado de Flávio;
3. as duas siglas na mesma coligação, ou nenhuma delas: a coligação não decide,
   e vale a exceção de campo declarada pela casa (`alinhado_lula`) quando houver.

A regra lê a coligação estadual, não a nacional. Partido coligado no estado não
prova voto do candidato no presidente; prova aliança registrada com o partido do
finalista, que é a evidência documental mais forte disponível em arquivo.
"""

from __future__ import annotations

import csv
import io
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONSULTA_CAND = ROOT / "data/raw/tse_candidatos_2026/consulta_cand_2026.zip"
FONTE = "data/raw/tse_candidatos_2026/consulta_cand_2026.zip (TSE, 03/10/2026)"
COLUNAS = (
    "SG_UF",
    "CD_CARGO",
    "SQ_CANDIDATO",
    "NM_URNA_CANDIDATO",
    "SG_PARTIDO",
    "NM_COLIGACAO",
    "DS_COMPOSICAO_COLIGACAO",
)
_FED = re.compile(r"\(([^)]*)\)")
_ITEM = re.compile(r"^\s*\d+\s*-\s*(.+?)\s*$")


def partidos_da_composicao(composicao: str) -> list[str]:
    """Siglas de uma composição de coligação do TSE, com as federações abertas.

    'PSB / FEDERAÇÃO BRASIL DA ESPERANÇA - FE BRASIL (13-PT / 65-PC do B / 43-PV)'
    vira ['PC do B', 'PSB', 'PT', 'PV'].
    """
    siglas: set[str] = set()
    for dentro in _FED.findall(composicao):
        for item in dentro.split("/"):
            m = _ITEM.match(item)
            if m:
                siglas.add(m.group(1).strip())
    fora = _FED.sub("", composicao)
    for parte in fora.split("/"):
        parte = parte.strip()
        if parte and not parte.upper().startswith("FEDERAÇÃO"):
            siglas.add(parte)
    return sorted(siglas)


def lado_da_coligacao(partidos: list[str] | set[str]) -> str | None:
    """'lula', 'flavio' ou None (a coligação sozinha não decide)."""
    pt, pl = "PT" in partidos, "PL" in partidos
    if pt and not pl:
        return "lula"
    if pl and not pt:
        return "flavio"
    return None


def ler(cargo: int, caminho: Path = CONSULTA_CAND) -> dict[str, dict]:
    """Candidaturas de um cargo por SQ_CANDIDATO; vazio se o arquivo não existe."""
    if not caminho.exists():
        return {}
    saida: dict[str, dict] = {}
    with zipfile.ZipFile(caminho) as z:
        for nome in sorted(z.namelist()):
            if not re.search(r"consulta_cand_2026_[A-Z]{2}\.csv$", nome):
                continue
            if nome.endswith("_BR.csv"):
                continue
            with z.open(nome) as bruto:
                texto = io.TextIOWrapper(bruto, encoding="latin-1")
                for linha in csv.DictReader(texto, delimiter=";"):
                    if linha["CD_CARGO"] != str(cargo):
                        continue
                    r = {c: linha[c] for c in COLUNAS}
                    comp = r["DS_COMPOSICAO_COLIGACAO"]
                    saida[r["SQ_CANDIDATO"]] = {
                        "uf": r["SG_UF"],
                        "nome_urna": r["NM_URNA_CANDIDATO"],
                        "partido": r["SG_PARTIDO"],
                        "coligacao": r["NM_COLIGACAO"],
                        "composicao": comp,
                        "partidos": partidos_da_composicao(comp),
                    }
    return saida


def por_nome(cands: dict[str, dict]) -> dict[tuple[str, str], dict]:
    """Mesma tabela por (UF, nome de urna), para casar com o boletim final."""
    return {(c["uf"], c["nome_urna"]): {**c, "sqcand": sq} for sq, c in cands.items()}
