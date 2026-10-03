#!/usr/bin/env python3
"""Prepara candidaturas ao Senado 2026, fotos oficiais e o Senado que continua.

Saidas em analysis/senado_2026/: tse_candidatos.json, senadores_2022.json,
eleitorado_uf_2026.json e casamento_nomes.json; fotos em docs/img/senado/.
Uso: python3 scripts/senado-2026-tse.py [--todos-aptos]
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from senado_2026 import tse
from voto_util_base import campo_de


def gravar(nome: str, dados) -> None:
    tse.SAIDA.mkdir(parents=True, exist_ok=True)
    (tse.SAIDA / nome).write_text(
        json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def eleitorado() -> dict:
    ufs = json.loads(tse.ELEITORADO_JSON.read_text(encoding="utf-8"))["ufs"]
    return {
        "fonte": "data/outputs/predicao_2026/tse.json (perfil_eleitorado_2026.zip)",
        "ufs": {uf: ufs[uf]["eleitorado"] for uf in tse.UFS},
        "total": sum(ufs[uf]["eleitorado"] for uf in tse.UFS),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--todos-aptos", action="store_true")
    args = ap.parse_args()

    candidatos = tse.ler_candidatos(tse.CAND_ZIP, campo_de)
    gravar("senadores_2022.json", tse.ler_eleitos_2022(tse.RES_2022, campo_de))
    gravar("eleitorado_uf_2026.json", eleitorado())

    pesquisas = tse.ROOT / "analysis/senado_2026/pesquisas"
    casados, perdidos = tse.casar_nomes(candidatos, tse.nomes_das_pesquisas(pesquisas))
    gravar("casamento_nomes.json", {"casados": casados, "nao_casados": perdidos})

    alvo = {(c["uf"], c["sq_candidato"]) for c in candidatos if _apta(c)}
    if not args.todos_aptos:
        alvo = {(c["uf"], c["sq_candidato"]) for c in casados}
    falhas = tse.baixar_fotos(sorted({uf for uf, _ in alvo}))
    gravadas, ausentes = tse.exportar_fotos(sorted(alvo))
    com_foto = {f"{uf}_{sq}" for uf, sq in gravadas}
    for c in candidatos:
        chave = f"{c['uf']}_{c['sq_candidato']}"
        c["foto"] = f"img/senado/{chave}.jpg" if chave in com_foto else None
    gravar("tse_candidatos.json", candidatos)

    total = sum(f.stat().st_size for f in tse.IMG.glob("*.jpg"))
    print(f"candidaturas: {len(candidatos)}; fotos gravadas: {len(gravadas)}")
    print(f"fotos ausentes no zip: {ausentes}; zips com falha: {falhas}")
    print(f"docs/img/senado: {total / 1024:.0f} KB; casados {len(casados)}")
    print(f"nao casados: {len(perdidos)}")


def _apta(c: dict) -> bool:
    """O TSE ainda nao divulga a situacao (#NE): sem situacao, nao exclui."""
    sit = (c["situacao_candidatura"] or "").upper()
    return not sit or sit.startswith(("APTO", "DEFERIDO"))


if __name__ == "__main__":
    main()
