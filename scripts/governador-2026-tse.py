#!/usr/bin/env python3
"""Prepara candidaturas a governador 2026, fotos oficiais e casamento de nomes.

Saídas em analysis/governador_2026/: tse_candidatos.json, casamento_nomes.json e
eleitorado_uf_2026.json; fotos em docs/img/governador/.
Uso: python3 scripts/governador-2026-tse.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from governador_2026 import tse as G
from senado_2026 import tse as T
from voto_util_base import campo_de


def gravar(nome: str, dados) -> None:
    G.SAIDA.mkdir(parents=True, exist_ok=True)
    (G.SAIDA / nome).write_text(
        json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def eleitorado() -> dict:
    ufs = json.loads(T.ELEITORADO_JSON.read_text(encoding="utf-8"))["ufs"]
    return {
        "fonte": "data/outputs/predicao_2026/tse.json (perfil_eleitorado_2026.zip)",
        "ufs": {uf: ufs[uf]["eleitorado"] for uf in T.UFS},
        "total": sum(ufs[uf]["eleitorado"] for uf in T.UFS),
    }


def main() -> None:
    candidatos = G.ler_candidatos(campo_de)
    gravar("eleitorado_uf_2026.json", eleitorado())
    casados, perdidos = G.casar(candidatos, G.nomes_das_pesquisas())
    gravar("casamento_nomes.json", {"casados": casados, "nao_casados": perdidos})
    alvo = {(c["uf"], c["sq_candidato"]) for c in casados}
    falhas = T.baixar_fotos(sorted({uf for uf, _ in alvo}))
    gravadas, ausentes = T.exportar_fotos(sorted(alvo), destino=G.IMG)
    com_foto = {f"{uf}_{sq}" for uf, sq in gravadas}
    for c in candidatos:
        chave = f"{c['uf']}_{c['sq_candidato']}"
        c["foto"] = f"img/governador/{chave}.jpg" if chave in com_foto else None
    gravar("tse_candidatos.json", candidatos)
    total = sum(f.stat().st_size for f in G.IMG.glob("*.jpg"))
    print(f"candidaturas: {len(candidatos)}; fotos gravadas: {len(gravadas)}")
    print(f"fotos ausentes no zip: {ausentes}; zips com falha: {falhas}")
    print(f"docs/img/governador: {total / 1024:.0f} KB; casados {len(casados)}")
    print(f"nao casados: {len(perdidos)}")
    for p in perdidos:
        print("  ", p["uf"], p["nome_pesquisa"], p["motivo"])


if __name__ == "__main__":
    main()
