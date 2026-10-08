"""Recorte da auditoria da apuração, sem refazer nem calibrar as pesquisas."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from apuracao_2026.pesquisas import NAO_ESCOLHA, erros_vs_urna, validos

ROOT = Path(__file__).resolve().parents[2]
ELECTION = "2026-10-04"
SOURCE = ROOT / "analysis/apuracao_2026/dados/pesquisas_vs_urna.json"
OFFICIAL = ROOT / "analysis/apuracao_2026/dados/presidente.json"
AUDIT = json.loads(SOURCE.read_text(encoding="utf-8"))
URNA = AUDIT["urna"]["validos"]
RESIDUAL = {"outros", "outros_esquerda", "demais"}


def grouped_urna(keys):
    """Mesma partição da projeção; candidaturas agrupadas contam no denominador."""
    named = {k: URNA[k] for k in keys if k in URNA}
    residual = [k for k in keys if k not in URNA]
    if len(residual) != 1 or residual[0] not in RESIDUAL:
        raise ValueError("A partição precisa de um único grupo residual")
    return {k: named[k] if k in named else 100 - sum(named.values()) for k in keys}


def comparison(poll, scenario="pessoas16_efetivo"):
    """Comparação descritiva de uma onda compatível; anteriores não são ranking."""
    turn = poll.get("turnos", {}).get("1t")
    if (
        not turn
        or poll["divulgacao"] > ELECTION
        or poll["campo"]["fim"] > ELECTION
        or poll.get("substituida")
        or poll.get("primeiro_turno_com_marcal")
    ):
        return None
    pub = poll["publicado"]["1t"]
    if any(
        v > 0 and k not in URNA.keys() | RESIDUAL | NAO_ESCOLHA for k, v in pub.items()
    ):
        return None
    delta = turn["cenarios"][scenario]["ajustado"]
    # Same rule as the apuração audit: retain published shares where there is
    # no income crossing. The attendance projection requires complete vectors.
    adjusted = {**pub, **delta}
    result = {
        "sem_cruzamento": sorted(
            k
            for k, v in pub.items()
            if v > 0 and k not in delta and k not in NAO_ESCOLHA
        )
    }
    for mode, values in (("publicado", pub), ("pnad", adjusted)):
        vector, audit = validos(values)
        result[mode] = {
            "validos": vector,
            "auditoria": audit,
            **erros_vs_urna(vector, URNA, AUDIT["urna"]["candidaturas_eam"]),
        }
    return result


def build():
    official = json.loads(OFFICIAL.read_text(encoding="utf-8"))
    if official["nacional"]["validos"] != AUDIT["urna"]["validos_votos"]:
        raise ValueError("A auditoria das pesquisas não usa o total oficial corrente")
    if (
        official["nacional"]["votos"]["flavio"] != AUDIT["urna"]["votos"]["flavio"]
        or official["nacional"]["votos"]["lula"] != AUDIT["urna"]["votos"]["lula"]
    ):
        raise ValueError(
            "Os votos dos líderes diferem entre as duas fontes da apuração"
        )
    rows = [p for p in AUDIT["pesquisas"] if p["ultima_onda_da_casa"]]
    return {
        "eleicao": ELECTION,
        "regra": "Última onda de cada casa com campo encerrado de 25/09 a 04/10, divulgada até a eleição. Erro = pesquisa menos urna, em pontos dos votos válidos.",
        "urna": AUDIT["urna"],
        "pesquisas": rows,
        "resumo": AUDIT["resumo_ultimas_ondas"],
        "efeito_pareado": AUDIT["efeito_reponderacao"]["ultimas_ondas"],
        "fontes_sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (SOURCE, OFFICIAL)
        },
        "relatorio": "apuracao_1o_turno_2026.html#pesquisas",
    }


def write():
    result = build()
    assets = ROOT / "docs/assets"
    (assets / "reponderacao_urna_1t.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with (assets / "reponderacao_urna_1t.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(
            [
                "id",
                "instituto",
                "modo",
                "candidato",
                "pesquisa_validos",
                "urna_validos",
                "erro_pp",
                "erro_diferenca_lula_flavio_pp",
                "perfil_renda",
            ]
        )
        for p in result["pesquisas"]:
            for mode in ("publicado", "reponderado"):
                row = p[mode]
                if row is None:
                    continue
                for k, error in row["erro_pp"].items():
                    writer.writerow(
                        [
                            p["id"],
                            p["instituto"],
                            mode,
                            k,
                            row["validos"][k],
                            URNA[k],
                            error,
                            row["diferenca_lula_menos_flavio"]["erro"],
                            p["perfil_renda"],
                        ]
                    )
    return result
