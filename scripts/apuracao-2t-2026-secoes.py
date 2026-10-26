#!/usr/bin/env python3
"""Análise por seção do 2º turno de 2026: comparecimento, biometria, horário e voto.

Lê, só para leitura, os boletins de urna do 2º turno (amostra em
``apuracao/data/apuracao-2t.sqlite`` ou coleta completa em
``apuracao/data/secoes_2t_2026.sqlite``) e a régua por seção do 1º turno
(``apuracao/data/referencia_1t_secoes.json``). Grava em
``analysis/apuracao_2t_2026/dados/``:

- ``secoes.json``: sinais e escore por seção; agregados por UF e município;
  a questão da prorrogação (encerramento contra recebimento);
- ``secoes_voto.json``: relação de cada sinal com o voto, dentro do município;
- ``secoes_ranking.json``: as 100 seções mais atípicas com a explicação provável;
- ``secoes.md``: memorando (método, números, achados contrários, limites).

Sinal pede explicação, não prova irregularidade. Uso:

    python3 scripts/apuracao-2t-2026-secoes.py                 # auto
    python3 scripts/apuracao-2t-2026-secoes.py --fonte amostra
    python3 scripts/apuracao-2t-2026-secoes.py --fonte completo

``auto`` usa o banco completo quando ele cobre 90% das seções do 1º turno.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from apuracao_2t_2026 import (
    secoes_fonte,
    secoes_linhas,
    secoes_ranking,
    secoes_ref,
    secoes_sinais,
    secoes_texto,
    secoes_voto,
)

ROOT = Path(__file__).resolve().parents[1]
DB_AMOSTRA = ROOT / "apuracao/data/apuracao-2t.sqlite"
DB_COMPLETO = ROOT / "apuracao/data/secoes_2t_2026.sqlite"
REGUA = ROOT / "apuracao/data/referencia_1t_secoes.json"
INDICE = ROOT / "docs/assets/politize/dados/indice.json"
ZONAS = ROOT / "docs/assets/politize/dados/zona"
SAIDA = ROOT / "analysis/apuracao_2t_2026/dados"
MEMO = SAIDA / "secoes.md"

COLS_SECAO = [
    "uf",
    "mun",
    "zona",
    "secao",
    "origem",
    "aptos",
    "comp",
    "taxa2",
    "taxa1",
    "delta_pp",
    "delta_rel_pp",
    "sem_bio_pct",
    "sem_bio_pct1",
    "ano_nasc_pct",
    "ano_nasc_pct1",
    "mun_p50_sem_bio_api",
    "mun_p50_ano_nasc_pct1",
    "enc_min",
    "enc1_min",
    "rec_min",
    "tipo_urna",
    "n_cargas",
    "tipo_arquivo",
    "fl",
    "lu",
    "fl1",
    "lu1",
    "fatia_f",
    "fatia_f1",
    "sinal_delta",
    "sinal_sem_bio",
    "sinal_ano_nasc",
    "sinal_tardia",
    "sinal_papel",
    "sinal_salto_bio",
    "delta_relativo",
    "salto_bio_pp",
    "pianista",
    "apos_19h",
    "contingencia",
    "escore_api",
    "escore",
    "magnitude",
]


def _limpo(v: Any) -> Any:
    if isinstance(v, (np.bool_, bool)):
        return bool(v)
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating, float)):
        if not np.isfinite(v):
            return None
        return int(v) if float(v).is_integer() and abs(v) < 1e15 else round(float(v), 2)
    return v


def tabela_secoes(x: pd.DataFrame) -> dict[str, Any]:
    """Grava as linhas por seção fora do git e devolve o ponteiro para ``secoes.json``."""
    t = x[COLS_SECAO]
    linhas = [[_limpo(v) for v in linha] for linha in t.itertuples(index=False)]
    return secoes_linhas.gravar(COLS_SECAO, linhas)


def sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def gravar(nome: str, obj: dict[str, Any]) -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    tmp = SAIDA / f".{nome}.tmp"
    tmp.write_text(
        json.dumps(obj, ensure_ascii=False, separators=(",", ":"), allow_nan=False),
        encoding="utf-8",
    )
    tmp.replace(SAIDA / nome)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fonte", choices=["auto", "amostra", "completo"], default="auto")
    args = ap.parse_args()

    ref, locais, meta_ref = secoes_ref.ler_regua(REGUA)
    mun_ref = json.loads(REGUA.read_text(encoding="utf-8"))["municipios"]
    n_completo = secoes_fonte.contar_completo(DB_COMPLETO)
    fonte = secoes_fonte.escolher_fonte(
        args.fonte, n_completo, int(meta_ref["n_secoes"])
    )
    df = secoes_fonte.carregar(fonte, DB_AMOSTRA, DB_COMPLETO)
    med_mun, med_zona = secoes_ref.medianas_1t(ref)
    nomes = secoes_ref.nomes_municipios(INDICE)

    x = secoes_sinais.montar(df, ref, mun_ref, med_mun, med_zona)
    x = secoes_sinais.sinais(x)
    corrigidos = (
        x.loc[x["corr_fuso_min"] != 0, ["uf", "mun", "corr_fuso_min"]]
        .drop_duplicates()
        .sort_values(["uf", "mun"])
    )
    agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    fonte_meta = {
        "fonte": fonte,
        "pedido": args.fonte,
        "banco": str(
            (DB_COMPLETO if fonte == "completo" else DB_AMOSTRA).relative_to(ROOT)
        ),
        "n_bus_completo": n_completo,
        "n_universo_1t": int(meta_ref["n_secoes"]),
        "cobertura_completo_pct": round(
            100 * n_completo / int(meta_ref["n_secoes"]), 2
        ),
        "regua_1t": str(REGUA.relative_to(ROOT)),
        "regua_1t_sha256": sha256(REGUA),
        "regua_1t_gerada_em": meta_ref["gerado_em"],
        "max_recebido_hhmm": secoes_sinais.hhmm(float(x["rec_min"].max())),
    }
    base = {"gerado_em": agora, "rotulo": secoes_sinais.ROTULO, **fonte_meta}

    pror = secoes_sinais.prorrogacao(x)
    secoes_obj = {
        **base,
        "regras": secoes_sinais.REGRAS,
        "enc_1t_pct": meta_ref.get("enc_1t_pct"),
        "fuso": {
            "regra": (
                "hora local convertida pelo fuso da UF e corrigida por município pela "
                "abertura modal (08:00 de Brasília); a régua do 1T recebe a mesma correção"
            ),
            "municipios_corrigidos": [
                {"uf": u, "mun": m, "nome": nomes.get((u, m)), "minutos": int(c)}
                for u, m, c in corrigidos.itertuples(index=False)
            ],
        },
        "totais": {
            "secoes": len(x),
            "com_ref_1t": int(x["tem_ref"].sum()),
            "amostra": int((x["origem"] == "amostra").sum()),
            "paralela": int((x["origem"] == "paralela").sum()),
            "completo": int((x["origem"] == "completo").sum()),
        },
        "conferencia_api_fuso_uf": secoes_sinais.conferencia_api(x),
        "agregados": secoes_sinais.agregados(x, nomes),
        "prorrogacao": pror,
        "estimativa_nacional": (
            secoes_sinais.estimativa_nacional(x, ref.groupby("uf").size().to_dict())
            if fonte == "amostra"
            else {"disponivel": False, "motivo": "banco completo: contagem direta"}
        ),
        "secoes": tabela_secoes(x),
        "convencoes": {
            "enc_min": "minutos depois das 17:00 de Brasília do dia do turno",
            "taxa": "comparecimento / aptos x 100",
            "fatia_f": "Flávio / (Flávio + Lula) x 100",
            "fl1_lu1": "votos de Flávio e Lula na seção principal no 1T (Politize)",
        },
    }
    voto = {**base, "n_min": secoes_voto.N_MIN, **secoes_voto.relacao(x)}
    zonas = [(r["uf"], int(r["zona"])) for _, r in x[x["escore"] > 0].iterrows()]
    politize = secoes_ref.locais_politize(ZONAS, zonas[:5000])
    rank = {
        **base,
        "ordem": "escore (0 a 6) e magnitude",
        "regras_explicacao": [t for _, t in secoes_ranking.REGRAS_EXPLICACAO],
        "secoes": secoes_ranking.ranking(x, locais, nomes, politize),
    }
    gravar("secoes.json", secoes_obj)
    gravar("secoes_voto.json", voto)
    gravar("secoes_ranking.json", rank)
    MEMO.write_text(secoes_texto.memorando(secoes_obj, voto, rank), encoding="utf-8")
    print(f"fonte={fonte} secoes={len(x)} escore>=2={int((x['escore'] >= 2).sum())}")


if __name__ == "__main__":
    main()
