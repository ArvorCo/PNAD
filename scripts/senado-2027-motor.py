#!/usr/bin/env python3
"""Senado 2027 diante do STF: régua K e C e Monte Carlo dos votos.

Lê analysis/senado_2027/elenco.json e analysis/senado_2027/senadores/*.json
(contrato em analysis/senado_2027/CONTRATO.md), aplica a régua da seção 3 e
grava docs/assets/senado_2027.json e o CSV de mesmo nome. Mesma entrada e
mesma semente, mesma saída (exceto `gerado_em`). Falha com a lista de erros
quando algum arquivo sai do contrato.

Uso:
    python3 scripts/senado-2027-motor.py --somente-validar
    python3 scripts/senado-2027-motor.py
    python3 scripts/senado-2027-motor.py --sorteios 5000 --semente 7 --saida /tmp/x.json
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from senado_2027 import base as B
from senado_2027 import saida
from senado_2027.scores import REGUA, br


def _lista(titulo: str, itens: list[str]) -> None:
    print(f"{titulo} ({len(itens)}):")
    for item in itens:
        print(f"  - {item}")


def _resumo(resultado: dict) -> None:
    sim = resultado["simulacao"]
    lim_pec = REGUA["simulacao"]["limiares"]["C_pec"]
    lim_imp = REGUA["simulacao"]["limiares"]["C_imp"]
    p_pec, p_imp = f"P{lim_pec}", f"P{lim_imp}"
    print(
        f"\nSimulação: {sim['parametros']['sorteios']} sorteios, semente "
        f"{sim['parametros']['semente']}, correlação latente nacional "
        f"{sim['parametros']['correlacao_nacional']} e intrabloco "
        f"{sim['parametros']['correlacao_intrabloco']}."
    )
    for cenario in B.CENARIOS:
        print(f"\nCenário de {B.ROTULO_CENARIO[cenario]}:")
        for variante, dados in sim["cenarios"][cenario].items():
            pec, imp = dados["pec"], dados["imp"]
            print(
                f"  {variante:<26} PEC: {br(pec['votos_esperados'])} votos "
                f"esperados, P(>= {lim_pec}) {br(pec[p_pec])}% | "
                f"impeachment: {br(imp['votos_esperados'])} votos esperados, "
                f"P(>= {lim_imp}) {br(imp[p_imp])}%, "
                f"P(>= {lim_pec}) {br(imp[p_pec])}%"
            )
        pivos = sim["cenarios"][cenario]["base"]["pivos"]["imp"][:8]
        if pivos:
            print(f"  Pivôs do impeachment (P >= {lim_imp}):")
            for p in pivos:
                print(
                    f"    {p['nome']} ({p['uf']}, {p['bloco']}, C_imp {br(p['C'])}): "
                    f"sim certo +{br(p['sobe_pp'])} pp, não certo "
                    f"-{br(p['cai_pp'])} pp"
                )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument(
        "--pasta", type=Path, default=B.PASTA, help="pasta com elenco.json e senadores/"
    )
    parser.add_argument("--semente", type=int, default=REGUA["simulacao"]["semente"])
    parser.add_argument("--sorteios", type=int, default=REGUA["simulacao"]["sorteios"])
    parser.add_argument("--saida", type=Path, default=B.SAIDA_JSON)
    parser.add_argument(
        "--somente-validar",
        action="store_true",
        help="só valida o esquema e o casamento elenco × JSON",
    )
    args = parser.parse_args(argv)

    try:
        dados = B.carregar(args.pasta)
    except B.ErroEsquema as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1
    print(
        f"{len(dados.cadeiras)} cadeiras no elenco, {len(dados.senadores)} JSON de "
        f"senador lidos, {len(dados.substitutos)} substitutos casados."
    )
    if dados.avisos:
        _lista("Avisos", dados.avisos)
    if dados.erros:
        _lista("ERROS de esquema", dados.erros)
        print("\nNada foi gravado: corrija os erros acima.", file=sys.stderr)
        return 1
    if args.somente_validar:
        print("Esquema válido.")
        return 0

    inicio = time.time()
    resultado = saida.montar(dados, sorteios=args.sorteios, semente=args.semente)
    caminho_json, caminho_csv = saida.gravar(resultado, args.saida)
    _resumo(resultado)
    print(f"\nGravado {caminho_json} e {caminho_csv} em {time.time() - inicio:.1f} s.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
