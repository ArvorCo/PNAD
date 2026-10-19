"""Clima (Open-Meteo) e notas dos TREs, lidos dos arquivos dos outros agentes.

Quando o arquivo ainda não existe, os campos ficam ``null`` e o resumo diz
``pendente``. As notas dos TREs casam por UF e município normalizado; quando a nota
traz número ou nome de local, o casamento sobe de grau. Motivo ausente vira
"não informado", nunca um motivo inventado.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from mudancas_secoes_2t import estatistica as es
from mudancas_secoes_2t.endereco import palavras, semelhanca_nomes

ROOT = Path(__file__).resolve().parents[2]
CLIMA = ROOT / "analysis/mudancas_secoes_2t/clima/open_meteo.json"
TRE = ROOT / "analysis/mudancas_secoes_2t/tre_noticias.json"
FONTES_1T = ROOT / "analysis/mudancas_secoes_2t/fontes_1t.json"
DIA_ELEICAO = "2026-10-04"
PERIODO = ("2026-10-05", "2026-10-18")
CHUVA_CORTES = (20.0, 50.0)
RAJADA_CORTE = 60.0
CALMO_CHUVA, CALMO_RAJADA = 10.0, 50.0
NAO_INFORMADO = "não informado"


def meta_arquivo(caminho: Path) -> dict[str, Any] | None:
    if not caminho.exists():
        return None
    bruto = caminho.read_bytes()
    return {
        "caminho": str(caminho.relative_to(ROOT)),
        "bytes": len(bruto),
        "sha256": hashlib.sha256(bruto).hexdigest(),
    }


def ler_clima() -> dict[str, Any] | None:
    if not CLIMA.exists():
        return None
    return json.loads(CLIMA.read_text(encoding="utf-8"))


def _serie(
    dias: list[dict[str, Any]], var: str, ini: str, fim: str
) -> list[tuple[str, float]]:
    return [
        (d["data"], d[var])
        for d in dias
        if ini <= d["data"] <= fim and d.get(var) is not None
    ]


def clima_local(clima: dict[str, Any] | None, pid: str) -> dict[str, Any] | None:
    """Chuva de 04/10, máximo diário de chuva e de rajada de 05 a 18/10 no ponto."""
    if not clima:
        return None
    p = clima.get("pontos", {}).get(pid)
    if not p:
        return None
    dias = p.get("dias", [])
    d4 = _serie(dias, "precipitation_sum", DIA_ELEICAO, DIA_ELEICAO)
    chuva = _serie(dias, "precipitation_sum", *PERIODO)
    vento = _serie(dias, "wind_gusts_10m_max", *PERIODO)
    fontes = sorted(
        {d.get("fonte") for d in dias if PERIODO[0] <= d["data"] <= PERIODO[1]} - {None}
    )
    cmax = max(chuva, key=lambda x: x[1]) if chuva else None
    vmax = max(vento, key=lambda x: x[1]) if vento else None
    return {
        "chuva_04_10_mm": d4[0][1] if d4 else None,
        "chuva_max_05a18_mm": cmax[1] if cmax else None,
        "dia_chuva_max": cmax[0] if cmax else None,
        "rajada_max_kmh": vmax[1] if vmax else None,
        "dia_rajada_max": vmax[0] if vmax else None,
        "fonte": "Open-Meteo " + "+".join(fontes) if fontes else None,
    }


def _parcela(valores: list[float], corte: float) -> float | None:
    if not valores:
        return None
    return round(sum(1 for v in valores if v > corte) / len(valores) * 100, 1)


def _diferenca_parcela(
    a: list[float], b: list[float], corte: float, reps: int, seed: int
) -> dict:
    """Parcela acima do corte no grupo menos no controle, em pontos, com IC bootstrap."""
    xa = (np.asarray(a, dtype=float) > corte).astype(float)
    xb = (np.asarray(b, dtype=float) > corte).astype(float)
    if not len(xa) or not len(xb):
        return {"valor": None, "ic95": None, "ep": None}

    def dif(u: np.ndarray, v: np.ndarray) -> float:
        return float(u.mean() - v.mean())

    ponto, r = es.bootstrap_estatistica([xa, xb], dif, reps, seed)
    return es.resumo_ic(ponto, r, 100.0, 1)


def clima_resumo(
    clima: dict[str, Any] | None,
    ids_real: set[str],
    ids_todos: set[str],
    reps: int = 2000,
    seed: int = 0,
) -> dict[str, Any]:
    if not clima:
        return {
            "situacao": "pendente",
            "nota": "analysis/mudancas_secoes_2t/clima/open_meteo.json não existia no "
            "momento do build; os campos de clima dos locais ficam null.",
        }
    pontos = clima.get("pontos", {})
    controles = {i for i, p in pontos.items() if p.get("grupo") == "controle"}
    grupos = {
        "origem_mudanca_real": ids_real,
        "origem_qualquer_alteracao": ids_todos,
        "controle": controles,
    }
    out: dict[str, Any] = {
        "situacao": "ok",
        "fonte": clima.get("fonte"),
        "gerado_em": clima.get("gerado_em"),
        "janela": clima.get("janela"),
        "regra": "chuva de 04/10 e máximo diário de 05 a 18/10 por local de origem (coordenada "
        "do 1º turno); rajada máxima de 05 a 18/10; controle = locais sem alteração "
        "sorteados pelo agente de clima",
    }
    series: dict[str, dict[str, list[float]]] = {}
    for nome, ids in grupos.items():
        brutos = [clima_local(clima, i) for i in sorted(ids)]
        lidos: list[dict[str, Any]] = [x for x in brutos if x is not None]
        c4 = [x["chuva_04_10_mm"] for x in lidos if x["chuva_04_10_mm"] is not None]
        cm = [
            x["chuva_max_05a18_mm"]
            for x in lidos
            if x["chuva_max_05a18_mm"] is not None
        ]
        rj = [x["rajada_max_kmh"] for x in lidos if x["rajada_max_kmh"] is not None]
        series[nome] = {"c4": c4, "cm": cm, "rj": rj}
        out[nome] = {
            "locais": len(ids),
            "com_dado": len(lidos),
            "chuva_04_10_acima_20mm_pct": _parcela(c4, CHUVA_CORTES[0]),
            "chuva_04_10_acima_50mm_pct": _parcela(c4, CHUVA_CORTES[1]),
            "chuva_max_05a18_acima_20mm_pct": _parcela(cm, CHUVA_CORTES[0]),
            "chuva_max_05a18_acima_50mm_pct": _parcela(cm, CHUVA_CORTES[1]),
            "rajada_acima_60kmh": sum(1 for v in rj if v > RAJADA_CORTE),
            "rajada_acima_60kmh_pct": _parcela(rj, RAJADA_CORTE),
        }
    a, b = series["origem_mudanca_real"], series["controle"]
    out["origem_mudanca_real_menos_controle_pp"] = {
        "chuva_04_10_acima_20mm": _diferenca_parcela(
            a["c4"], b["c4"], CHUVA_CORTES[0], reps, seed
        ),
        "chuva_max_05a18_acima_20mm": _diferenca_parcela(
            a["cm"], b["cm"], CHUVA_CORTES[0], reps, seed + 1
        ),
        "chuva_max_05a18_acima_50mm": _diferenca_parcela(
            a["cm"], b["cm"], CHUVA_CORTES[1], reps, seed + 2
        ),
        "rajada_acima_60kmh": _diferenca_parcela(
            a["rj"], b["rj"], RAJADA_CORTE, reps, seed + 3
        ),
        "nota": "IC 95% por bootstrap de locais, grupos reamostrados em separado",
    }
    calmos = []
    for i in sorted(ids_real):
        x = clima_local(clima, i)
        if (
            x
            and (x["chuva_max_05a18_mm"] or 0) <= CALMO_CHUVA
            and (x["rajada_max_kmh"] or 0) <= CALMO_RAJADA
        ):
            calmos.append(i)
    out["origem_mudanca_real_sem_chuva_nem_vento"] = {
        "regra": f"máximo diário de chuva até {CALMO_CHUVA:.0f} mm e rajada até "
        f"{CALMO_RAJADA:.0f} km/h de 05 a 18/10",
        "quantidade": len(calmos),
        "ids": calmos,
    }
    return out


def ler_tre() -> list[dict[str, Any]]:
    if not TRE.exists():
        return []
    d = json.loads(TRE.read_text(encoding="utf-8"))
    return d if isinstance(d, list) else d.get("itens", [])


def _mun_norm(texto: str) -> list[str]:
    t = re.sub(r"\([^)]*\)", " ", texto or "")
    partes = re.split(r",|\be\b", t, flags=re.IGNORECASE)
    return [" ".join(palavras(p)) for p in partes if palavras(p)]


def _numeros_local(texto: str) -> set[int]:
    return {int(x) for x in re.findall(r"N[º°o]\s*(\d{4})", texto or "")}


def _texto(v: Any) -> str:
    return v if isinstance(v, str) and v.strip() else NAO_INFORMADO


GRAU = {"local": 3, "zona": 2, "municipio": 1}


def casar_tre(
    itens: list[dict[str, Any]], pares: pd.DataFrame
) -> dict[tuple, dict[str, Any]]:
    """Melhor nota do TRE para cada par (uf, mun, zona, local_1t, local_2t)."""
    saida: dict[tuple, dict[str, Any]] = {}
    mun_norm = {m: " ".join(palavras(m)) for m in pares["municipio"].unique()}
    for item in itens:
        uf = item.get("uf")
        if not uf or uf == "BR":
            continue
        for loc in item.get("locais") or []:
            muns = set(_mun_norm(loc.get("municipio", "")))
            zona_txt = str(loc.get("zona") or "")
            zona = int(zona_txt) if zona_txt.isdigit() else None
            nums = _numeros_local(
                f"{loc.get('local_antigo', '')} {loc.get('local_novo', '')}"
            )
            cand = pares[
                (pares["uf"] == uf) & pares["municipio"].map(mun_norm).isin(muns)
            ]
            for _, p in cand.iterrows():
                if zona is not None and int(p["zona"]) != zona:
                    continue
                grau = "zona" if zona is not None else "municipio"
                nome_ok = max(
                    semelhanca_nomes(loc.get("local_antigo", ""), p["nome_1t"]),
                    semelhanca_nomes(loc.get("local_novo", ""), p["nome_2t"]),
                )
                if nums & {int(p["local_1t"]), int(p["local_2t"])} or nome_ok >= 0.5:
                    grau = "local"
                chave = (
                    p["uf"],
                    p["mun"],
                    int(p["zona"]),
                    int(p["local_1t"]),
                    int(p["local_2t"]),
                )
                novo = {
                    "texto": _texto(loc.get("motivo")),
                    "url": item.get("url"),
                    "veiculo": item.get("veiculo"),
                    "data": item.get("data"),
                    "grau_casamento": grau,
                    "motivos_citados_na_materia": item.get("motivos_citados") or [],
                }
                atual = saida.get(chave)
                if atual is None or GRAU[grau] > GRAU[atual["grau_casamento"]]:
                    saida[chave] = novo
    return saida


def notas_por_uf(itens: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for item in itens:
        uf = item.get("uf")
        if not uf:
            continue
        out.setdefault(uf, []).append(
            {
                "veiculo": item.get("veiculo"),
                "titulo": item.get("titulo"),
                "data": item.get("data"),
                "url": item.get("url"),
                "numero_total_declarado": item.get("numero_total_declarado"),
                "locais_citados": len(item.get("locais") or []),
                "motivos_citados": item.get("motivos_citados") or [],
            }
        )
    return out


def ler_fontes_1t() -> dict[str, Any] | None:
    if not FONTES_1T.exists():
        return None
    return json.loads(FONTES_1T.read_text(encoding="utf-8"))
