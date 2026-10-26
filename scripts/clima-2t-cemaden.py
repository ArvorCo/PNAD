"""Coleta retomável das séries horárias do CEMADEN para 25/10/2026 (rodar com nohup)."""

from __future__ import annotations

import json

from clima_2t import estacoes

if __name__ == "__main__":
    print(json.dumps(estacoes.coletar_cemaden(), ensure_ascii=False), flush=True)
