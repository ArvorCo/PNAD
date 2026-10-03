#!/usr/bin/env python3
"""Calibra o erro de pesquisa de Senado com as pesquisas finais e a urna de 2022.

Grava analysis/senado_2026/calibracao_2022.json com cada par pesquisa x urna,
as estatísticas de erro em pontos dos válidos e a variância não amostral no
log das frações, que o motor da predição usa como escala do erro.

Uso:
    python3 scripts/senado-2026-calibracao.py                  # baixa e calcula
    python3 scripts/senado-2026-calibracao.py --skip-download  # usa o wikitext salvo
    python3 scripts/senado-2026-calibracao.py --refresh-urna   # relê o zip do TSE
"""

from __future__ import annotations

import argparse
import json
import time

from senado_2026 import calibracao as C
from voto_util_base import campo_de


def fontes_salvas() -> dict[str, dict]:
    anterior = C.ler() or {}
    return {f["uf"]: f for f in anterior.get("fontes_wikipedia", [])}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--skip-download", action="store_true")
    ap.add_argument("--refresh-urna", action="store_true")
    args = ap.parse_args()

    anterior = C.ler() or {}
    fontes = fontes_salvas()
    if not args.skip_download:
        for uf in sorted(C.TITULOS):
            try:
                fontes[uf] = C.baixar_wiki(uf)
            except OSError as erro:
                print(f"{uf}: falha ao baixar a Wikipédia ({erro}); mantém o salvo")
            time.sleep(0.3)
    paginas = {}
    for uf in sorted(C.TITULOS):
        arquivo = C.WIKI_DIR / f"{uf}.wiki"
        if arquivo.exists():
            paginas[uf] = arquivo.read_text(encoding="utf-8")
            fontes.setdefault(
                uf,
                {
                    "uf": uf,
                    "titulo": C.TITULOS[uf],
                    "url": C.url_wiki(C.TITULOS[uf], raw=False),
                    "arquivo": str(arquivo.relative_to(C.ROOT)),
                    "acessado_em": None,
                },
            )
            fontes[uf]["sha256"] = C.sha256(arquivo)
    urna = anterior.get("urna")
    if args.refresh_urna or not urna:
        urna = C.urna_2022()
    saida = C.calibrar(urna, paginas, campo_de, fontes)
    saida["fonte_urna"]["sha256"] = C.sha256(C.URNA_ZIP)
    C.SAIDA.write_text(
        json.dumps(saida, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    cob = saida["cobertura"]
    est = saida["estatisticas"]["casas_principais"]
    var = saida["variancia_log"]["casas_principais"]
    print(
        f"estados com Datafolha/Ipec/Quaest finais: {cob['n_estados_casas_principais']}"
        f" ({cob['n_pesquisas_casas_principais']} pesquisas)"
    )
    print(
        "erro por candidatura (pp dos válidos): "
        f"MAE {est['por_candidatura']['erro_medio_absoluto']:.2f}, "
        f"RMSE {est['por_candidatura']['rmse']:.2f}"
    )
    print(
        "diferença 2º-3º: "
        f"MAE {est['diferenca_2o_3o'].get('erro_medio_absoluto') or 0:.2f}, "
        f"DP {est['diferenca_2o_3o'].get('desvio_padrao') or 0:.2f}"
    )
    print(f"variância não amostral no log: {var.get('var_nao_amostral_log')}")
    print(f"deriva por dia no log: {saida['deriva']['var_por_dia_log']}")


if __name__ == "__main__":
    main()
