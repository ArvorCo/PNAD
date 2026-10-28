#!/usr/bin/env python3
"""Valida e normaliza a base municipal IPS Brasil 2026 arquivada."""

import json

from analise_realidade_eleicao.desenvolvimento import ROOT, carregar


def main():
    p = json.loads(
        (ROOT / "analysis/apuracao_2t_2026/dados/presidente.json").read_text()
    )
    tab = p["municipios"]
    municipios = [dict(zip(tab["colunas"], row, strict=True)) for row in tab["linhas"]]
    dados = carregar(municipios)
    saida = ROOT / "analysis/analise_realidade_eleicao/desenvolvimento.json"
    saida.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n")
    print(
        f"IPS: {dados['n_municipios']} municípios; equivalências: {len(dados['equivalencias'])}"
    )
    print(f"Sem IPS: {dados['sem_ips']}")


if __name__ == "__main__":
    main()
