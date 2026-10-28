"""Listas municipais do dataset do 2º turno: onde cada finalista teve menos votos.

Dois CSVs em ``docs/assets/apuracao_2t/dataset/`` com o mesmo esquema, uma linha por
município em que o candidato teve menos votos absolutos no 2º turno do que no 1º,
da maior perda para a menor: ``municipios_flavio_menos_votos_2t.csv`` e
``municipios_lula_menos_votos_2t.csv``. Fonte: ``comparacao_1t.json`` e
``governadores.json`` (``scripts/apuracao-2t-2026-dados.py``), lidos por
``turnos_perdas``; nada é digitado aqui. UTF-8, vírgula, fim de linha LF.

Rótulo: votos absolutos, não fatia dos válidos; menos votos não identifica eleitor
nem motivo. As colunas ``perda_*`` repartem a perda sob hipótese declarada.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any

from . import turnos_perdas as TP
from .base import ROOT, SAIDA

ARQUIVOS = {
    "flavio": "municipios_flavio_menos_votos_2t.csv",
    "lula": "municipios_lula_menos_votos_2t.csv",
}
FONTES = ("comparacao_1t.json", "governadores.json")
SECAO = "## Listas municipais: menos votos no 2º turno"
ROTULO = TP.ROTULO[:1].upper() + TP.ROTULO[1:] + "."

# (coluna, definição, unidade); a ordem é a do CSV.
COLUNAS: list[tuple[str, str, str]] = [
    ("uf", "Unidade da federação", "sigla"),
    ("mun_tse", "Código TSE do município, cinco dígitos", "código"),
    ("municipio", "Nome do município como no arquivo do TSE", "texto"),
    (
        "governador_2t",
        "1 quando a UF teve 2º turno de governador (UFs de governadores.json), 0 quando não",
        "0 ou 1",
    ),
    ("aptos_1t", "Eleitorado do município no 1º turno", "pessoas"),
    ("aptos_2t", "Eleitorado do município no 2º turno", "pessoas"),
    ("comparecimento_1t", "Eleitores que compareceram no 1º turno", "pessoas"),
    ("comparecimento_2t", "Eleitores que compareceram no 2º turno", "pessoas"),
    (
        "dif_comparecimento",
        "comparecimento_2t menos comparecimento_1t",
        "pessoas",
    ),
    (
        "pct_comparecimento_1t",
        "comparecimento_1t sobre aptos_1t, duas casas",
        "%",
    ),
    (
        "pct_comparecimento_2t",
        "comparecimento_2t sobre aptos_2t, duas casas",
        "%",
    ),
    (
        "validos_1t",
        "Votos válidos para presidente no 1º turno, todas as candidaturas",
        "votos",
    ),
    ("validos_2t", "Votos válidos para presidente no 2º turno", "votos"),
    (
        "terceiros_1t",
        "Votos válidos do 1º turno em candidaturas que não Flávio e Lula",
        "votos",
    ),
    ("flavio_1t", "Votos em Flávio Bolsonaro no 1º turno", "votos"),
    ("flavio_2t", "Votos em Flávio Bolsonaro no 2º turno", "votos"),
    ("dif_flavio", "flavio_2t menos flavio_1t", "votos"),
    ("lula_1t", "Votos em Lula no 1º turno", "votos"),
    ("lula_2t", "Votos em Lula no 2º turno", "votos"),
    ("dif_lula", "lula_2t menos lula_1t", "votos"),
    (
        "parte_flavio_1t",
        "Flávio sobre Flávio mais Lula no 1º turno, duas casas",
        "%",
    ),
    (
        "parte_flavio_2t",
        "Flávio sobre Flávio mais Lula no 2º turno (os válidos), duas casas",
        "%",
    ),
    (
        "mudanca_parte_flavio_pp",
        "parte_flavio_2t menos parte_flavio_1t",
        "pontos percentuais",
    ),
    (
        "perda",
        "Votos que o candidato da lista perdeu, positivo: flavio_1t menos flavio_2t na "
        "lista de Flávio, lula_1t menos lula_2t na de Lula",
        "votos",
    ),
    (
        "perda_teto_comparecimento",
        "Régua do teto: menor valor entre a perda e a queda do comparecimento (zero "
        "quando o comparecimento não caiu), como se todo eleitor que deixou de votar "
        "fosse do candidato",
        "votos",
    ),
    (
        "perda_fora_teto",
        "perda menos perda_teto_comparecimento: o mínimo que a queda do "
        "comparecimento não cobre",
        "votos",
    ),
    (
        "perda_proporcional_comparecimento",
        "Régua proporcional: menor valor entre a perda e a queda do comparecimento "
        "vezes os votos do candidato no 1º turno sobre comparecimento_1t, como se "
        "quem deixou de votar votasse como o município no 1º turno; uma casa",
        "votos",
    ),
    (
        "perda_fora_proporcional",
        "perda menos perda_proporcional_comparecimento; uma casa",
        "votos",
    ),
]
NOMES = [c[0] for c in COLUNAS]


def _linha(m: dict[str, Any]) -> list[Any]:
    return [
        m["uf"],
        m["cd_tse"],
        m["nome"],
        int(m["governador_2t"]),
        m["t1_aptos"],
        m["aptos"],
        m["t1_comparecimento"],
        m["t2_comparecimento"],
        m["delta_comparecimento_votos"],
        m["t1_pct_comparecimento"],
        m["t2_pct_comparecimento"],
        m["t1_validos"],
        m["t2_validos"],
        m["t1_terceiros"],
        m["t1_flavio"],
        m["t2_flavio"],
        m["delta_votos_flavio"],
        m["t1_lula"],
        m["t2_lula"],
        m["delta_votos_lula"],
        m["t1_h2h_flavio"],
        m["t2_h2h_flavio"],
        m["swing_h2h_flavio_pp"],
        m["perda"],
        m["teto_comparecimento"],
        m["alem_teto"],
        round(m["proporcional_comparecimento"], 1),
        round(m["alem_proporcional"], 1),
    ]


def ler(pasta: Path = SAIDA) -> tuple[dict[str, Any], dict[str, Any] | None] | None:
    """``comparacao_1t.json`` e ``governadores.json``; ``None`` sem o primeiro."""
    c1 = pasta / FONTES[0]
    if not c1.exists():
        return None
    g = pasta / FONTES[1]
    G = json.loads(g.read_text(encoding="utf-8")) if g.exists() else None
    return json.loads(c1.read_text(encoding="utf-8")), G


def linhas(C1: dict[str, Any], G: dict[str, Any] | None, quem: str) -> list[list[Any]]:
    gov = TP.ufs_governador(G)
    return [_linha(m) for m in TP.municipios(C1, quem, gov)]


def csv_bytes(rows: list[list[Any]]) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(NOMES)
    for r in rows:
        w.writerow(["" if v is None else v for v in r])
    return buf.getvalue().encode("utf-8")


def _rel(caminho: Path) -> str:
    return (
        str(caminho.relative_to(ROOT)) if caminho.is_relative_to(ROOT) else str(caminho)
    )


def gravar(destino: Path, dados: Path = SAIDA) -> list[dict[str, Any]] | None:
    """Grava os dois CSVs em ``destino`` e devolve as entradas do manifesto."""
    lidos = ler(dados)
    if lidos is None:
        return None
    C1, G = lidos
    fontes = []
    for nome in FONTES:
        arq = dados / nome
        if arq.exists():
            bruto = arq.read_bytes()
            meta = json.loads(bruto).get("meta", {})
            fontes.append(
                {
                    "caminho": _rel(arq),
                    "gerado_em": meta.get("gerado_em"),
                    "sha256": hashlib.sha256(bruto).hexdigest(),
                }
            )
    destino.mkdir(parents=True, exist_ok=True)
    out = []
    for quem in TP.CANDIDATOS:
        rows = linhas(C1, G, quem)
        corpo = csv_bytes(rows)
        arq = destino / ARQUIVOS[quem]
        arq.write_bytes(corpo)
        out.append(
            {
                "candidato": quem,
                "arquivo": _rel(arq),
                "bytes": len(corpo),
                "sha256": hashlib.sha256(corpo).hexdigest(),
                "n_linhas": len(rows),
                "colunas": NOMES,
                "universo": (
                    f"municípios do Brasil, sem o exterior, em que {TP.NOME[quem]} teve "
                    "menos votos absolutos no 2º turno do que no 1º (arquivo de "
                    "presidente completo nos dois turnos)"
                ),
                "ordem": "maior perda primeiro; empate por UF e nome",
                "rotulo": ROTULO,
                "fontes": fontes,
            }
        )
    return out


def _pt(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def secao_dicionario(entradas: list[dict[str, Any]] | None) -> str:
    """Seção do ``DICIONARIO.md`` com os dois arquivos e as colunas."""
    if not entradas:
        return ""
    arquivos = "\n".join(
        f"- `{Path(e['arquivo']).name}`: {e['universo']}; {_pt(e['n_linhas'])} linhas "
        f"de dados mais o cabeçalho, {_pt(e['bytes'])} bytes, SHA-256 `{e['sha256']}`."
        for e in entradas
    )
    fontes = "; ".join(
        f"`{f['caminho']}` (gerado em {f['gerado_em']})" for f in entradas[0]["fontes"]
    )
    linhas_tab = "\n".join(f"| `{c}` | {d} | {u} |" for c, d, u in COLUNAS)
    return f"""
{SECAO}

Dois arquivos com o mesmo esquema, CSV separado por vírgula, ponto como separador
decimal, UTF-8, sem compressão, ordenados da maior perda para a menor:

{arquivos}

**Fonte.** {fontes}. Municípios com o arquivo de presidente completo nos dois turnos,
sem o exterior; o código TSE casa os dois turnos.

**Rótulo.** {ROTULO} As colunas `perda_*` repartem a perda por duas réguas declaradas,
o teto e a proporcional; são contas sob hipótese, não identificação de eleitor.

| coluna | definição | unidade |
|---|---|---|
{linhas_tab}
"""
