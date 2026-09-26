#!/usr/bin/env python3
"""Base eleitoral do mapa do voto util (setembro de 2026).

Junta tres materiais oficiais, todos do TSE:

1. O resultado presidencial de 2022 por UF, 1o e 2o turno, lido dos arquivos
   simplificados do portal de resultados (`resultados.tse.jus.br`, eleicoes 544
   e 545). Traz eleitorado apto, comparecimento, abstencao, brancos, nulos e
   votos de cada candidato.
2. O eleitorado de 2026 por UF, do perfil do eleitorado de julho de 2026
   (`data/outputs/tse_eleitorado_perfil.sqlite`).
3. O resultado de 2022 por municipio (`data/outputs/estaduais2026/municipios.csv`,
   gerado por `scripts/estaduais-092026-tse.py`), usado para medir onde a
   direita cresceu entre os dois turnos de 2022: o voto util que chegou tarde.

Escreve `analysis/voto_util/tse_2022_uf.json` e
`analysis/voto_util/reserva_2022_municipios.csv`.

Reproducao:
    python3 scripts/estaduais-092026-tse.py   # se municipios.csv nao existir
    python3 scripts/voto-util-092026-tse.py
"""

from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "data/raw/tse_resultados/api_2022"
PERFIL = ROOT / "data/outputs/tse_eleitorado_perfil.sqlite"
MUNICIPIOS = ROOT / "data/outputs/estaduais2026/municipios.csv"
OUT = ROOT / "analysis/voto_util"
URL = "https://resultados.tse.jus.br/oficial/ele2022/{e}/dados-simplificados/{uf}/{uf}-c0001-e000{e}-r.json"

UFS = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA",
    "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
]  # fmt: skip
REGIAO = {
    "Norte": "AC AM AP PA RO RR TO",
    "Nordeste": "AL BA CE MA PB PE PI RN SE",
    "Centro-Oeste": "DF GO MS MT",
    "Sudeste": "ES MG RJ SP",
    "Sul": "PR RS SC",
}
UF_REGIAO = {uf: reg for reg, ufs in REGIAO.items() for uf in ufs.split()}
NOMES = {
    "JAIR BOLSONARO": "bolsonaro",
    "LULA": "lula",
    "CIRO GOMES": "ciro",
    "SIMONE TEBET": "tebet",
}


def _num(value: str) -> int:
    return int(value)


def ler_turno(uf: str, eleicao: int) -> dict:
    path = API / f"{uf.lower()}-c0001-e000{eleicao}-r.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    out = {
        "aptos": _num(raw["e"]),
        "comparecimento": _num(raw["c"]),
        "abstencao": _num(raw["a"]),
        "brancos": _num(raw["vb"]),
        "nulos": _num(raw["tvn"]),
        "validos": _num(raw["vv"]),
        "fonte": URL.format(e=eleicao, uf=uf.lower()),
    }
    outros = 0
    for cand in raw["cand"]:
        chave = NOMES.get(cand["nm"])
        votos = _num(cand["vap"])
        if chave:
            out[chave] = votos
        else:
            outros += votos
    out["outros"] = outros
    soma = sum(out.get(k, 0) for k in ("bolsonaro", "lula", "ciro", "tebet")) + outros
    if soma != out["validos"]:
        raise ValueError(
            f"{uf} {eleicao}: candidatos somam {soma}, validos {out['validos']}"
        )
    if out["brancos"] + out["nulos"] + out["validos"] != out["comparecimento"]:
        raise ValueError(f"{uf} {eleicao}: brancos+nulos+validos != comparecimento")
    return out


def eleitorado_2026() -> dict[str, int]:
    with sqlite3.connect(PERFIL) as con:
        rows = con.execute(
            "SELECT category, qt_eleitores FROM summary WHERE dimension='uf'"
        ).fetchall()
    return {uf: int(qt) for uf, qt in rows}


def pct(parte: float, todo: float) -> float:
    return round(100 * parte / todo, 3) if todo else 0.0


def resumo_uf(uf: str, eleit26: dict[str, int]) -> dict:
    t1, t2 = ler_turno(uf, 544), ler_turno(uf, 545)
    return {
        "uf": uf,
        "regiao": UF_REGIAO[uf],
        "eleitorado_2026": eleit26[uf],
        "t1": t1,
        "t2": t2,
        "comparecimento_1t_pct": pct(t1["comparecimento"], t1["aptos"]),
        "comparecimento_2t_pct": pct(t2["comparecimento"], t2["aptos"]),
        "branco_nulo_1t_pct_comparecimento": pct(
            t1["brancos"] + t1["nulos"], t1["comparecimento"]
        ),
        "bolsonaro_1t_validos": pct(t1["bolsonaro"], t1["validos"]),
        "bolsonaro_2t_validos": pct(t2["bolsonaro"], t2["validos"]),
        "lula_1t_validos": pct(t1["lula"], t1["validos"]),
        "lula_2t_validos": pct(t2["lula"], t2["validos"]),
        "terceira_via_1t_validos": pct(
            t1["ciro"] + t1["tebet"] + t1["outros"], t1["validos"]
        ),
        # Quanto a direita ganhou entre os turnos, em votos e em pontos do eleitorado apto.
        "ganho_bolsonaro_entre_turnos": t2["bolsonaro"] - t1["bolsonaro"],
        "ganho_lula_entre_turnos": t2["lula"] - t1["lula"],
        "ganho_bolsonaro_pp_aptos": round(
            pct(t2["bolsonaro"], t2["aptos"]) - pct(t1["bolsonaro"], t1["aptos"]), 3
        ),
        "ganho_lula_pp_aptos": round(
            pct(t2["lula"], t2["aptos"]) - pct(t1["lula"], t1["aptos"]), 3
        ),
    }


def reserva_municipal() -> list[dict]:
    """Ganho da direita entre os turnos de 2022, por municipio.

    O ganho de Bolsonaro do 1o para o 2o turno mede o voto que so chegou a ele
    quando a eleicao ficou binaria. E a geografia historica do voto util tardio.
    """
    linhas = []
    with MUNICIPIOS.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["uf"] == "ZZ" or not row["bolsonaro_2t"]:
                continue
            b1, b2 = int(row["bolsonaro_1t"]), int(row["bolsonaro_2t"])
            l1, l2 = int(row["lula_1t"]), int(row["lula_2t"])
            terceira = int(row["ciro_1t"]) + int(row["tebet_1t"])
            eleitores = int(row["eleitores_2026"]) if row["eleitores_2026"] else 0
            linhas.append(
                {
                    "uf": row["uf"],
                    "municipio": row["municipio"],
                    "codigo_tse": row["codigo_tse"],
                    "eleitores_2026": eleitores,
                    "bolsonaro_1t": b1,
                    "bolsonaro_2t": b2,
                    "lula_1t": l1,
                    "lula_2t": l2,
                    "ciro_tebet_1t": terceira,
                    "ganho_bolsonaro": b2 - b1,
                    "ganho_lula": l2 - l1,
                    "ganho_liquido_direita": (b2 - b1) - (l2 - l1),
                    "bolsonaro_2t_pct": float(row["bolsonaro_2t_pct"] or 0),
                }
            )
    linhas.sort(key=lambda r: r["ganho_bolsonaro"], reverse=True)
    return linhas


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    eleit26 = eleitorado_2026()
    ufs = [resumo_uf(uf, eleit26) for uf in UFS]
    br1, br2 = ler_turno("BR", 544), ler_turno("BR", 545)
    zz1 = ler_turno("ZZ", 544)
    total_uf = sum(u["t1"]["aptos"] for u in ufs) + zz1["aptos"]
    if total_uf != br1["aptos"]:
        raise ValueError(f"soma das UFs {total_uf} != Brasil {br1['aptos']}")
    municipios = reserva_municipal()
    payload = {
        "fonte": "TSE, resultados simplificados 2022 (eleicoes 544 e 545) e perfil do eleitorado de julho de 2026",
        "brasil_2022": {"t1": br1, "t2": br2},
        "ufs": ufs,
        "municipios_top_ganho_bolsonaro": municipios[:60],
        "n_municipios": len(municipios),
    }
    (OUT / "tse_2022_uf.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    with (OUT / "reserva_2022_municipios.csv").open(
        "w", encoding="utf-8", newline=""
    ) as fh:
        writer = csv.DictWriter(fh, fieldnames=list(municipios[0]))
        writer.writeheader()
        writer.writerows(municipios)
    print(f"UFs: {len(ufs)}  municipios: {len(municipios)}")
    print(
        "Brasil 2022: comparecimento 1T",
        pct(br1["comparecimento"], br1["aptos"]),
        "brancos+nulos",
        pct(br1["brancos"] + br1["nulos"], br1["comparecimento"]),
    )


if __name__ == "__main__":
    main()
