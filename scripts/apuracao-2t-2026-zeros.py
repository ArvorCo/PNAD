#!/usr/bin/env python3
"""Seções com zero voto num finalista, 2º e 1º turno de 2026 contra 2022.

Refaz seção a seção a conta da manchete da Folha de S.Paulo de 27/10/2026 ("Flávio
teve zero voto em 106 urnas, nas quais Lula somou quase 15 mil") nos bancos de BUs
dos dois turnos (somente leitura) e no arquivo por seção de 2022, classifica o local
pelo nome por regra declarada e grava ``analysis/apuracao_2t_2026/dados/zeros.json``.
Falha com ``AssertionError`` se o resultado divergir dos números conferidos
(``zeros_dados.ESPERADO``). Rótulo: atipicidade pede explicação, não prova
irregularidade.

Depois: ``apuracao-2t-2026-hipoteses.py``, ``video-apuracao-2t-dados.py``,
``apuracao-2t-2026-build.py`` e ``apuracao-2t-2026-thread.py --png``.

Uso:
    python3 scripts/apuracao-2t-2026-zeros.py
"""

from __future__ import annotations

import argparse
import time

from apuracao_2t_2026 import zeros_dados as zd


def _linha(r: dict) -> str:
    return (
        f"{r['ano']} {r['turno']}º turno, zero {r['candidato']}: {r['secoes']} seções "
        f"({r['adversario']} soma {r['votos_adversario']}; universo {r['universo_secoes']})"
    )


def _cauda(c: dict) -> None:
    np_ = c["numero_pequeno"]
    print(
        f"cauda: {np_['com_voto_1t']} das {np_['secoes_zero_2t']} com voto no 1º turno, "
        + ", ".join(f"k={x['k']}: {x['secoes']}" for x in np_["por_k"] if x["k"])
    )
    for x in np_["taxa_base"]:
        if x["k"] and (x["chegaram_a_zero"] or x["k"] <= 6):
            print(
                f"  k={x['k']}: {x['secoes_pais']} seções, {x['chegaram_a_zero']} a zero "
                f"(e^-k {x['chance_aprox_pct']:.3g}%, esperado {x['zeros_esperados']:.2f})"
            )
    ca, es = c["cauda"], c["espelho"]
    print(
        f"  queda até 1: {ca['queda_ate_1']}, queda de 80%: {ca['queda_80']}, "
        f"união {ca['uniao']}; espelho {es['queda_ate_1']} e {es['queda_80']}; "
        f"esperado pela independência {ca['esperado_independencia']}"
    )
    for f in c["fichas"]:
        print(
            f"  {f['uf']} {f['municipio']} {f['zona']}/{f['secao']}: Flávio "
            f"{f['flavio_1t']}→{f['flavio_2t']}, Lula {f['lula_1t']}→{f['lula_2t']}, "
            f"{f['local']}"
        )
    for x in c["por_dentro"]:
        print(f"  por dentro: {x['chave']} ({x['regra_de_escolha']})")


def main() -> None:
    argparse.ArgumentParser(description=__doc__).parse_args()
    t0 = time.time()
    d = zd.montar()
    zd.conferir(d)
    zd.gravar(d)
    print("Brasil sem o exterior:")
    for r in d["recortes"]:
        print("  " + _linha(r))
    ce = d["com_exterior"]
    print(
        f"com o exterior, 2º turno de 2026: zero Flávio {ce['2026_2t_direita']}, "
        f"zero Lula {ce['2026_2t_lula']}"
    )
    zf = d["zero_flavio"]
    p = zf["perfil"]
    print(
        "zero Flávio no 2º turno: "
        + ", ".join(f"{x['uf']} {x['secoes']}" for x in p["ufs"][:6])
        + f"; {p['municipios']} municípios; aptos mediana {p['aptos']['mediana']}, "
        f"soma {p['aptos']['soma']}; comparecimento {p['comparecimento']['soma']}"
    )
    print(
        "tipo do local: "
        + ", ".join(
            f"{x['nome']} {x['secoes']}" for x in d["tipo_local"]["2026_2t_direita"]
        )
    )
    t1, rp = zf["primeiro_turno"], zf["repeticao_2022"]
    print(
        f"1º turno nas mesmas seções: Flávio {t1['votos_soma']} votos, zero em "
        f"{t1['secoes_zero']}, até 5 em {t1['secoes_ate_5']}"
    )
    print(
        f"2022: {rp['chave_presente']} chaves presentes, {rp['zero_2t']} com zero "
        f"Bolsonaro no 2º turno; Politize: {rp['politize']['pareadas']} pareadas, "
        f"mediana {rp['politize']['mediana_pct_validos']}%, "
        f"{rp['politize']['zeros_exatos']} zeros"
    )
    m = zf["mistura"]
    if m["disponivel"]:
        print(
            f"mistura: {m['no_universo']} no universo, {m['no_grupo_atipico']} no grupo "
            f"atípico; por grupo {[(g['id'] + 1, g['secoes']) for g in m['por_grupo']]}"
        )
    else:
        print(f"mistura: indisponível ({m['motivo']})")
    _cauda(d["cauda"])
    print(f"conferência: tudo igual ao esperado; {time.time() - t0:.0f} s")
    print(zd.SAIDA.relative_to(zd.ROOT))


if __name__ == "__main__":
    main()
