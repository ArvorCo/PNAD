#!/usr/bin/env python3
"""IDs das urnas por seção no 1º e no 2º turno de 2026: modelos, repetidos, trocas e carga.

Lê `apuracao/data/secoes_2026.sqlite` e `secoes_2t_2026.sqlite` em modo somente
leitura (o coletor do 2º turno pode estar ativo) e grava
`analysis/apuracao_2t_2026/dados/urnas.json` e `urnas.md`. Rótulo: pede
explicação, não prova irregularidade.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from apuracao_2t_2026 import urnas_analise as an
from apuracao_2t_2026.base import SAIDA
from apuracao_2t_2026.urnas_base import BANCO_1T, BANCO_2T, ler, ler_com_cache
from apuracao_2t_2026.urnas_texto import markdown

DIAS = {"1t": "2026-10-04", "2t": "2026-10-25"}


def turno(dados: dict, nome: str, t1=None) -> dict:
    df = dados["bu"]
    rep = an.repetidos(df)
    return {
        "cobertura": {
            "secoes_catalogo": dados["secoes_catalogo"],
            "secoes_principais": dados["secoes_principais"],
            "secoes_com_bu": len(df),
            "pct": (
                round(100 * len(df) / dados["secoes_principais"], 2)
                if dados["secoes_principais"]
                else None
            ),
            "por_uf": {k: int(v) for k, v in df.uf.value_counts().sort_index().items()},
        },
        "modelos": an.modelos(df),
        "repetidos": rep,
        "resultado_repetidos": an.resultado_dos_repetidos(df, rep, t1),
        "codigo_carga": an.codigo_carga_repetido(df),
        "id_no_log": an.id_no_log(df),
        "carga": an.carga(df, DIAS[nome]),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--banco-1t", type=Path, default=BANCO_1T)
    p.add_argument("--banco-2t", type=Path, default=BANCO_2T)
    p.add_argument("--saida", type=Path, default=SAIDA)
    p.add_argument("--sem-cache", action="store_true")
    a = p.parse_args()
    d1 = ler_com_cache(a.banco_1t, "1t", not a.sem_cache)
    d2 = ler(a.banco_2t)
    d1["bu"] = an.preparar(d1["bu"])
    d2["bu"] = an.preparar(d2["bu"])
    t1, t2 = d1["bu"], d2["bu"]
    completa = len(t2) >= d2["secoes_principais"] * 0.99
    out = {
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rotulo": an.ROTULO_URNAS,
        "estado_coleta_2t": (
            "completa"
            if completa
            else f"parcial ({len(t2)} de {d2['secoes_principais']} seções principais)"
        ),
        "fontes_2022": "analysis/apuracao_2t_2026/urnas_fontes/fontes.json",
        "turnos": {"1t": turno(d1, "1t"), "2t": turno(d2, "2t", t1)},
        "entre_turnos": an.entre_turnos(t1, t2),
        "ids_em_outra_secao": an.ids_entre_turnos_em_outra_secao(t1, t2),
    }
    a.saida.mkdir(parents=True, exist_ok=True)
    (a.saida / "urnas.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, default=str) + "\n",
        encoding="utf-8",
    )
    (a.saida / "urnas.md").write_text(markdown(out), encoding="utf-8")
    r1, r2 = out["turnos"]["1t"]["repetidos"], out["turnos"]["2t"]["repetidos"]
    print(
        json.dumps(
            {
                "coleta_2t": out["estado_coleta_2t"],
                "repetidos_1t": [
                    r1["ids_repetidos"],
                    r1["secoes_envolvidas"],
                    r1["sem_explicacao_pela_regra"],
                ],
                "repetidos_2t": [
                    r2["ids_repetidos"],
                    r2["secoes_envolvidas"],
                    r2["sem_explicacao_pela_regra"],
                ],
                "mesma_urna": out["entre_turnos"]["mesma_urna"],
                "urna_diferente": out["entre_turnos"]["urna_diferente"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
