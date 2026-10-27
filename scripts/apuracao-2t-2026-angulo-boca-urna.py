#!/usr/bin/env python3
"""Boca de urna e pressão sobre o eleitor no 2º turno de 2026: o que o documento registra.

Conta os relatos do canal da casa no Supabase (só contagens; o token do CLI fica
no keychain e nunca é impresso), separa as ocorrências públicas do dia em registro
oficial, relato de imprensa e relato anônimo, confere a base legal nos arquivos
originais e grava ``analysis/apuracao_2t_2026/dados/angulo_boca_urna.json`` e ``.md``.
Rótulo: relato pede explicação, não prova irregularidade; contagem não é verificação.

Uso:
    python3 scripts/apuracao-2t-2026-angulo-boca-urna.py [--sem-supabase]
"""

from __future__ import annotations

import argparse
import json

from apuracao_2t_2026 import angulo_boca_urna as ab


def _sem_acesso() -> list[dict]:
    raise RuntimeError("consulta ao Supabase desligada por --sem-supabase")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--sem-supabase",
        action="store_true",
        help="não consultar o canal de relatos; registra o motivo no JSON",
    )
    a = ap.parse_args()
    d = ab.montar(_sem_acesso if a.sem_supabase else ab._consultar_supabase)
    ab.SAIDA_JSON.write_text(
        json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    ab.SAIDA_MD.write_text(ab.markdown(d), encoding="utf-8")
    r = d["relatos"]
    if "erro" in r:
        print(f"relatos: acesso falhou ({r['erro']}) em {r['consultado_em']}")
    else:
        print(
            f"relatos: {r['total']} no total, {r['por_status']}, "
            f"pressão sobre o eleitor {r['pressao_sobre_o_eleitor']}, "
            f"consultado em {r['consultado_em']}"
        )
    for b in d["balancos_mjsp"]:
        print(
            f"MJSP {b['id']}: {b['ocorrencias']} ocorrências, boca de urna "
            f"{b['boca_de_urna_pct']}% (~{b['boca_de_urna_n_derivado']}), "
            f"conferido={b['total_conferido_no_arquivo']}"
        )
    o = d["ocorrencias"]
    print(f"ocorrências públicas: {o['n']} itens, {o['por_classe']}")
    for nome, n in d["base_legal"].items():
        falhos = [
            x["dispositivo"] for x in n["dispositivos"] if not x["conferido_no_arquivo"]
        ]
        print(
            f"{nome}: {'tudo conferido' if not falhos else 'não conferido: ' + ', '.join(falhos)}"
        )
    print(ab.SAIDA_JSON.relative_to(ab.ROOT))


if __name__ == "__main__":
    main()
