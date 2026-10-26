"""Fotos agendadas da tabela de acumulados do CEMADEN (rodar com nohup).

Cada foto grava as 27 UFs. ``acc48hr - acc24hr`` às 03h UTC de 27/10 e ``acc72hr - acc48hr``
às 03h UTC de 28/10 dão a chuva de 25/10, das 00h às 24h de Brasília; ``acc24hr`` às 21h UTC
de 26/10 é conferência de latência. Fotos já gravadas não são refeitas.
"""

from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timezone

from clima_2t import estacoes

# Depois destas fotos o script reconsolida e regera as páginas (clima-2t-atualizar.sh).
ATUALIZAR_APOS = {"20261027T0330Z", "20261028T0330Z"}
ALVOS = [
    "2026-10-26T21:00",
    "2026-10-27T03:00",
    "2026-10-27T03:30",
    "2026-10-27T04:30",
    "2026-10-28T03:00",
    "2026-10-28T03:30",
    "2026-10-29T03:00",
]

if __name__ == "__main__":
    for alvo in ALVOS:
        t = datetime.fromisoformat(alvo).replace(tzinfo=timezone.utc)
        rotulo = t.strftime("%Y%m%dT%H%MZ")
        if (estacoes.RAW / "cemaden_acumulados" / rotulo / "resumo.json").exists():
            continue
        falta = (t - datetime.now(timezone.utc)).total_seconds()
        if falta < -1800:
            print(f"{rotulo}: perdida (passou)", flush=True)
            continue
        if falta > 0:
            time.sleep(falta)
        r = estacoes.foto_acumulados(rotulo)
        print(
            json.dumps({rotulo: {k: v["status"] for k, v in r["ufs"].items()}}),
            flush=True,
        )
        if rotulo in ATUALIZAR_APOS:
            fim = subprocess.run(["./clima-2t-atualizar.sh"], check=False)
            print(f"{rotulo}: atualização terminou com {fim.returncode}", flush=True)
