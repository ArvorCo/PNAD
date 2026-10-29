#!/usr/bin/env python3
"""Atualiza os horários por seção dos filtros do mapa do Politize-se (2º turno)."""

import json

from politize_se.horarios import publicar

if __name__ == "__main__":
    d = publicar()
    print(
        json.dumps(
            {k: d[k] for k in ("contagens", "motivos_log", "secoes_bu_fora_do_mapa")},
            ensure_ascii=False,
        )
    )
