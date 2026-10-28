#!/usr/bin/env python3
"""Conferências no banco somente leitura e triagem entre turnos."""

import json

from analise_realidade_eleicao.auditoria import construir
from analise_realidade_eleicao.dados import OUTPUT, ler

if __name__ == "__main__":
    auditoria = construir(ler(OUTPUT / "dados.json")["municipios"])
    (OUTPUT / "auditoria.json").write_text(
        json.dumps(
            auditoria, ensure_ascii=False, separators=(",", ":"), allow_nan=False
        )
        + "\n"
    )
    print("Municipal:", auditoria["municipal"])
    print(
        "BUs:",
        {
            k: v
            for k, v in auditoria["bus"].items()
            if k not in ("diferencas", "testes")
        },
    )
    print(
        "Testes BUs:",
        {
            k: len(v) if isinstance(v, list) else v
            for k, v in auditoria["bus"]["testes"].items()
        },
    )
    print("Divergências municipais BUs:", len(auditoria["bus"]["diferencas"]))
    print(
        "Triagem MAE:",
        auditoria["triagem"]["mae_perfil"],
        auditoria["triagem"]["mae_com_1t"],
    )
