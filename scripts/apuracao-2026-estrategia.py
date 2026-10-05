#!/usr/bin/env python3
"""Capítulo estratégico "O caminho do 2º turno" do dossiê da apuração de 2026.

Lê o banco da apuração (somente leitura; o coletor pode continuar gravando),
os arquivos do TSE de 2022, a tabela municipal de 2022 e os JSON da casa, e
grava:

- ``analysis/apuracao_2026/dados/estrategia_2t.json``: todos os números;
- ``analysis/apuracao_2026/estrategia_2t.md``: o texto do capítulo.

Uso:
    python3 scripts/apuracao-2026-estrategia.py
    python3 scripts/apuracao-2026-estrategia.py --ate 2026-10-05T06:30:00Z

``--ate`` fixa o corte de captura (UTC) para reproduzir a mesma versão dos
arquivos do TSE; sem ele, vale a última versão gravada.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from apuracao_2026 import estrategia_leitura as L
from apuracao_2026 import estrategia_riscos as R
from apuracao_2026 import estrategia_secoes as S
from apuracao_2026 import estrategia_texto as T

TRAVESSAO = chr(0x2014)  # proibido no texto público da casa
DESCRICAO = 'Capítulo estratégico "O caminho do 2º turno" do dossiê da apuração.'
SAIDA_JSON = L.ROOT / "analysis/apuracao_2026/dados/estrategia_2t.json"
SAIDA_MD = L.ROOT / "analysis/apuracao_2026/estrategia_2t.md"


def carregar(ate: str) -> dict:
    """Lê todas as fontes uma vez."""
    con = L.conectar()
    cl = L.classificador()
    try:
        fontes: dict[str, Any] = {
            "pres": L.ler_disputas(
                con, L.ELEICAO_FEDERAL, L.PRESIDENTE, ("br", "uf"), ate, cl
            ),
            "pres_mu": L.ler_disputas(
                con, L.ELEICAO_FEDERAL, L.PRESIDENTE, ("mu",), ate, cl
            ),
            "gov": L.ler_disputas(
                con, L.ELEICAO_ESTADUAL, L.GOVERNADOR, ("uf",), ate, cl
            ),
            "gov_mu": L.ler_disputas(
                con, L.ELEICAO_ESTADUAL, L.GOVERNADOR, ("mu",), ate, cl
            ),
            "dep": L.ler_disputas(
                con, L.ELEICAO_ESTADUAL, L.DEPUTADO_FEDERAL, ("uf",), ate, cl
            ),
            "meta": L.ler_municipios_meta(con),
        }
    finally:
        con.close()
    ufs = sorted({uf for (uf, _m) in fontes["pres"]} | {"BR"})
    fontes["api22"] = {
        uf: {1: L.ler_api_2022(uf, 1), 2: L.ler_api_2022(uf, 2)} for uf in ufs
    }
    fontes["mun22"] = L.ler_municipios_2022()
    fontes["gov_2t_2022"] = L.ufs_com_2t_governador_2022()
    fontes["voto_util"] = L.ler_json(L.VOTO_UTIL)
    fontes["datafolha"] = L.ler_json(L.DATAFOLHA_NACIONAL)
    fontes["sudeste"] = L.ler_json(L.DATAFOLHA_SUDESTE)
    fontes["final"] = L.ler_json(L.FINAL)
    fontes["predicao"] = L.ler_json(L.PREDICAO)
    fontes["erro_2022"] = L.ler_json(L.ERRO_2022)
    return fontes


def montar(fontes: dict, ate: str) -> dict:
    aritmetica = S.secao_aritmetica(fontes)
    geografia = S.secao_geografia(fontes)
    governadores = S.secao_governadores(fontes)
    congresso = S.secao_congresso(fontes)
    riscos = R.secao_riscos(fontes, aritmetica, geografia, governadores)
    movimentos = R.secao_movimentos(fontes, aritmetica, geografia, governadores)
    geografia.pop("_municipios", None)
    return {
        "titulo": "O caminho do 2º turno",
        "gerado_por": "scripts/apuracao-2026-estrategia.py",
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "corte_captura": ate,
        "fontes": {
            "banco": L.relativo(L.BANCO),
            "classificacao_campo": L.relativo(L.CAMPOS),
            "resultado_2022_uf": L.relativo(L.API_2022),
            "resultado_2022_municipio": L.relativo(L.MUNICIPIOS_2022),
            "governador_2022": L.relativo(L.MUNZONA_2022),
            "matriz_nexus": L.relativo(L.VOTO_UTIL),
            "matriz_datafolha": L.relativo(L.DATAFOLHA_NACIONAL),
            "linhas_governador_datafolha": L.relativo(L.DATAFOLHA_SUDESTE),
            "congresso": L.relativo(L.FINAL),
            "central_da_casa": L.relativo(L.PREDICAO),
            "erro_2022": L.relativo(L.ERRO_2022),
        },
        "aritmetica": aritmetica,
        "geografia": geografia,
        "governadores": governadores,
        "congresso": congresso,
        "riscos": riscos,
        "movimentos": movimentos,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=DESCRICAO)
    ap.add_argument("--ate", default=None, help="corte de captura ISO UTC")
    ap.add_argument("--json", type=Path, default=SAIDA_JSON)
    ap.add_argument("--md", type=Path, default=SAIDA_MD)
    args = ap.parse_args()
    ate = args.ate or "9999"
    fontes = carregar(ate)
    dados = montar(fontes, args.ate or "última versão gravada")
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(
        json.dumps(dados, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    texto = T.capitulo(dados)
    if TRAVESSAO in texto:
        raise SystemExit("travessão no texto do capítulo")
    args.md.write_text(texto, encoding="utf-8")
    print(f"gravado {L.relativo(args.json)} e {L.relativo(args.md)}")


if __name__ == "__main__":
    main()
