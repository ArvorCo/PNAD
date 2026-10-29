#!/usr/bin/env python3
"""Dados do mapa do Brasil do Politize-se (``docs/politizese_mapa.html``).

Lê, só para leitura, os arquivos por município do Politize-se
(``docs/assets/politize_se/dados/indice.json`` e ``mun/<UF>/<mun>.json``, gerados por
``scripts/politize-se-build.py``) e grava em ``docs/assets/politize_se_mapa/`` o formato 3:
um índice, um arquivo de prédios por UF e o índice de CEP dos locais de votação. A ficha
de cada prédio abre as seções direto dos arquivos por zona do Politize-se, sem cópia.

Reexecutável: rodar de novo depois de cada build do Politize-se (a cobertura do 2º turno
vem dele). Uso::

    python3 scripts/politize-se-mapa-build.py            # Brasil e exterior
    python3 scripts/politize-se-mapa-build.py --uf AC    # amostra (mescla no índice)
"""

from __future__ import annotations

import argparse

from politize_se import mapa_dados, mapa_saida


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--uf", action="append", help="só estas UFs (mescla no índice)")
    ap.add_argument(
        "--horarios",
        action="store_true",
        help="reexporta também os horários nacionais dos bancos locais de boletins e logs",
    )
    ap.add_argument(
        "--movimento",
        action="store_true",
        help="atualiza histogramas por hora para os dois aplicativos",
    )
    a = ap.parse_args()
    ufs = {u.upper() for u in a.uf} if a.uf else None
    lido = mapa_dados.ler(ufs=ufs)
    ind = mapa_saida.gravar(lido, mesclar=bool(ufs))
    if a.horarios:
        from politize_se.horarios import publicar

        publicar()
    if a.movimento:
        from politize_se.movimento import publicar as publicar_movimento

        publicar_movimento()
    r = ind["resumo"]
    cob = ind["cobertura"].get("nacional", {})
    print(
        f"{r['locais']} prédios ({r['com_coord']} com coordenada, {r['sem_coord']} só na "
        f"lista); {r['com_bu2']} com boletim do 2º turno; seções {r['secoes_bu2']} de "
        f"{r['secoes']} ({cob.get('pct')}% da coleta); UFs {r['bytes_ufs'] / 1e6:.1f} MB, "
        f"CEP {ind['bytes_cep'] / 1e6:.1f} MB"
    )


if __name__ == "__main__":
    main()
