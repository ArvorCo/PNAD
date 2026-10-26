"""Chuva de 25/10/2026 (2º turno) por célula de 0,25°: coleta e consolidação.

Uso:
    python3 scripts/clima-2t.py --inmet               # arquiva catálogo e tenta a rota pública
    python3 scripts/clima-2t.py --foto ROTULO         # foto da tabela de acumulados do CEMADEN
    python3 scripts/clima-2t.py --consolidar          # estações + modelo -> clima.json e mapa
    python3 scripts/clima-2t.py --consolidar --fonte era5   # a partir de 31/10

Coletas longas, com nohup: ``clima-2t-modelo.py --fonte ifs|era5``,
``clima-2t-cemaden.py`` (séries horárias) e ``clima-2t-fotos-cemaden.py`` (fotos agendadas).
Contrato em ``analysis/clima_2t_2026/CONTRATO.md``.
"""

from __future__ import annotations

import argparse
import json

from clima_2t import estacoes, modelo, observado


def main() -> None:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument(
        "--inmet", action="store_true", help="testa a rota pública do INMET"
    )
    ap.add_argument("--foto", help="tira agora uma foto da tabela de acumulados")
    ap.add_argument(
        "--consolidar", action="store_true", help="grava clima.json e o mapa"
    )
    ap.add_argument("--fonte", choices=sorted(modelo.MODELOS), default="ifs")
    a = ap.parse_args()
    if not (a.inmet or a.foto or a.consolidar):
        ap.error("escolha --inmet, --foto ou --consolidar")
    if a.inmet:
        r = estacoes.testar_inmet()
        (estacoes.FONTES / "inmet_tentativas_25_10.json").write_text(
            json.dumps(r, ensure_ascii=False, indent=1)
        )
        print(json.dumps(r, ensure_ascii=False)[:600])
    if a.foto:
        print(
            json.dumps(estacoes.foto_acumulados(a.foto)["ufs"], ensure_ascii=False)[
                :600
            ]
        )
    if a.consolidar:
        doc = observado.consolidar(a.fonte)
        print(
            json.dumps(
                {"cobertura": doc["cobertura"], "estacoes": doc["estacoes"]},
                ensure_ascii=False,
                indent=1,
            )
        )


if __name__ == "__main__":
    main()
