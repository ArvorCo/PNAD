"""As seções mais atípicas e a explicação provável de cada uma, por regra.

Ordem: escore (0 a 6) e depois magnitude. A explicação é gerada por regras
declaradas em ``REGRAS_EXPLICACAO``, na ordem; uma seção pode ter várias. Sem
nenhuma, a frase pede conferência na ata e no log da urna. Nunca nomes de
pessoas: só UF, município, zona, seção e o nome do local de votação.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .secoes_sinais import REGRAS, SINAIS, hhmm

N_RANKING = 100
# 18:55 de Brasília, em minutos depois das 17:00
PERTO_19H_MIN = 115

REGRAS_EXPLICACAO = [
    (
        "perto_19h",
        "encerrou perto ou depois das 19:00: compatível com a extensão até 19h",
    ),
    (
        "tardia_fila",
        "encerrou 30 min ou mais depois do 1T, antes das 18:55: fila no fechamento",
    ),
    ("agregada", "seção agregada no cadastro (Politize)"),
    ("aptos_mudaram", "aptos mudaram mais de 10% entre os turnos"),
    ("contingencia", "urna de contingência ou com mais de uma carga"),
    ("papel", "BU do sistema de apuração: votação em cédula"),
    ("pequena", "seção pequena (menos de 100 aptos): um eleitor move mais de 1 pp"),
    (
        "salto_no_local",
        "salto de biometria em outras seções do mesmo local: leitor ou rede",
    ),
    (
        "zona_bio_baixa",
        "zona com biometria baixa também no 1T (mediana ≥ 10%), sem salto",
    ),
    ("secao_bio_baixa_1t", "a própria seção já tinha 10% ou mais sem biometria no 1T"),
    ("comp1_baixo", "comparecimento do 1T 10 pp ou mais abaixo da mediana municipal"),
    (
        "acompanha",
        "alta acompanha a do município ou da UF (menos de 5 pp acima da mediana)",
    ),
]
SEM_EXPLICACAO = "sem explicação provável pela regra: pede conferência na ata e no log"


def _f(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, (np.floating, float)):
        return None if not np.isfinite(v) else float(np.round(v, 2))
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.bool_,)):
        return bool(v)
    return v


def explicar(row: pd.Series, agregadas: list[Any], saltos_local: int) -> list[str]:
    sem_salto = not (pd.notna(row["salto_bio_pp"]) and row["salto_bio_pp"] >= 5)
    cond = {
        "perto_19h": bool(row["tardia"]) and row["enc_min"] >= PERTO_19H_MIN,
        "tardia_fila": bool(row["tardia"]) and row["enc_min"] < PERTO_19H_MIN,
        "agregada": len(agregadas) > 0,
        "aptos_mudaram": pd.notna(row["aptos_var_pct"])
        and abs(row["aptos_var_pct"]) > REGRAS["aptos_mudaram_pct"],
        "contingencia": bool(row["contingencia"]),
        "papel": bool(row["papel"]),
        "pequena": pd.notna(row["aptos"])
        and row["aptos"] < REGRAS["secao_pequena_aptos"],
        "salto_no_local": not sem_salto and saltos_local >= 2,
        "zona_bio_baixa": sem_salto
        and pd.notna(row["zona_p50_nao_bio_pct1"])
        and row["zona_p50_nao_bio_pct1"] >= 10,
        "secao_bio_baixa_1t": sem_salto
        and pd.notna(row["nao_bio_pct1"])
        and row["nao_bio_pct1"] >= 10,
        "comp1_baixo": pd.notna(row["taxa1"])
        and pd.notna(row["mun_p50_taxa1"])
        and row["taxa1"] <= row["mun_p50_taxa1"] - 10,
        "acompanha": bool(row["delta"]) and not bool(row["delta_relativo"]),
    }
    out = [txt for chave, txt in REGRAS_EXPLICACAO if cond[chave]]
    return out or [SEM_EXPLICACAO]


def ranking(
    x: pd.DataFrame,
    locais: list[list[float]],
    nomes: dict[tuple[str, str], str],
    politize: dict[tuple[str, str, int, int], dict[str, Any]],
) -> list[dict[str, Any]]:
    cand = x[x["escore"] > 0].sort_values(
        ["escore", "magnitude", "uf", "mun", "zona", "secao"],
        ascending=[False, False, True, True, True, True],
    )
    top = cand.head(N_RANKING)
    saltos = x[x["sinal_salto_bio"] & x["local"].notna() & (x["local"] >= 0)]
    por_local = saltos.groupby("local").size()
    out = []
    for pos, (_, r) in enumerate(top.iterrows(), start=1):
        k = (r["uf"], r["mun"], int(r["zona"]), int(r["secao"]))
        pol = politize.get(k, {})
        li = r["local"]
        coord = locais[int(li)] if pd.notna(li) and int(li) >= 0 else None
        sl = (
            int(por_local.get(li, 0)) - int(bool(r["sinal_salto_bio"]))
            if pd.notna(li)
            else 0
        )
        exp = explicar(r, pol.get("agregadas", []), sl)
        out.append(
            {
                "posicao": pos,
                "uf": r["uf"],
                "mun": r["mun"],
                "municipio": nomes.get((r["uf"], r["mun"])),
                "zona": int(r["zona"]),
                "secao": int(r["secao"]),
                "local": pol.get("local"),
                "lon": coord[0] if coord else None,
                "lat": coord[1] if coord else None,
                "origem": r["origem"],
                "escore": int(r["escore"]),
                "escore_api": int(r["escore_api"]),
                "magnitude": _f(r["magnitude"]),
                "sinais": [s for s in SINAIS if bool(r[f"sinal_{s}"])],
                "contingencia": bool(r["contingencia"]),
                "aptos_1t": _f(r["aptos1"]),
                "aptos_2t": _f(r["aptos"]),
                "comparecimento_1t": _f(r["comp1"]),
                "comparecimento_2t": _f(r["comp"]),
                "taxa_comp_1t": _f(r["taxa1"]),
                "taxa_comp_2t": _f(r["taxa2"]),
                "delta_comp_pp": _f(r["delta_pp"]),
                "delta_comp_ref_local_pp": _f(r["delta_ref_local_pp"]),
                "delta_comp_relativo_pp": _f(r["delta_rel_pp"]),
                "sem_bio_pct_1t": _f(r["sem_bio_pct1"]),
                "sem_bio_pct_2t": _f(r["sem_bio_pct"]),
                "ano_nasc_pct_1t": _f(r["ano_nasc_pct1"]),
                "ano_nasc_pct_2t": _f(r["ano_nasc_pct"]),
                "sem_bio_mun_p50_1t": _f(r["mun_p50_sem_bio_api"]),
                "ano_nasc_mun_p50_1t": _f(r["mun_p50_ano_nasc_pct1"]),
                "salto_bio_pp": _f(r["salto_bio_pp"]),
                "encerramento_1t": hhmm(r["enc1_min"]),
                "encerramento_2t": hhmm(r["enc_min"]),
                "recebimento_2t": hhmm(r["rec_min"]),
                "tipo_urna": _f(r["tipo_urna"]),
                "n_cargas": _f(r["n_cargas"]),
                "flavio_1t": _f(r["fl1"]),
                "lula_1t": _f(r["lu1"]),
                "flavio_2t": _f(r["fl"]),
                "lula_2t": _f(r["lu"]),
                "fatia_flavio_1t": _f(r["fatia_f1"]),
                "fatia_flavio_2t": _f(r["fatia_f"]),
                "explicacao_provavel": "; ".join(exp),
                "sem_explicacao": exp == [SEM_EXPLICACAO],
            }
        )
    return out
