"""Contexto territorial compartilhado pelo mapa e pelas fichas do Politize-se.

Reutiliza estimativas publicadas, sem recalcular renda nem inferir características
individuais. Segurança permanece municipal; ausências nunca viram zero.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLITIZE = ROOT / "docs/assets/politize/dados"
MUNICIPIOS = ROOT / "data/outputs/fiscais_risco_municipios.csv"
FONTES = ROOT / "analysis/apuracao_2026/dados/fiscais_risco_fontes.json"
COLUNAS = [
    "local_id",
    "renda_mediana_brl",
    "renda_ate2",
    "renda_de2a5",
    "renda_mais5",
    "fund_inc",
    "fund_med",
    "med_sup_inc",
    "superior",
    "setor_situacao",
    "perfil_fonte",
]
CAMPOS_MAPA = ["renda_mediana_brl", "renda_ate2", "homicidios_taxa_100mil"]
CAMADAS = {
    "renda": {
        "nome": "Renda domiciliar estimada",
        "campo": "renda_mediana_brl",
        "tipo": "sequencial",
        "minimo": 0,
        "maximo": 10000,
        "baixo": "R$ 0",
        "alto": "R$ 10 mil ou mais",
        "unidade": "reais",
        "explica": "Estimativa pela PNAD anual 2025, escolaridade do eleitorado e situação urbana/rural. Valores a preços de julho de 2026. Não é renda medida no bairro nem renda de quem vota neste prédio.",
        "precisa_bu2": False,
        "grupo": "Economia e segurança",
    },
    "renda_ate2": {
        "nome": "Renda estimada até 2 salários",
        "campo": "renda_ate2",
        "tipo": "sequencial",
        "minimo": 0,
        "maximo": 100,
        "baixo": "0%",
        "alto": "100%",
        "unidade": "%",
        "explica": "Parcela estimada do perfil com renda domiciliar até R$ 3.242 (dois salários mínimos de 2026), pela PNAD. É renda do domicílio, não por pessoa. Estimativa, não medição local.",
        "precisa_bu2": False,
        "grupo": "Economia e segurança",
    },
    "homicidios": {
        "nome": "Homicídios no município",
        "campo": "homicidios_taxa_100mil",
        "tipo": "sequencial",
        "minimo": 0,
        "maximo": 60,
        "baixo": "0 por 100 mil",
        "alto": "60 ou mais",
        "unidade": "por 100 mil",
        "explica": "Atlas da Violência / SIM, 2024: óbitos por residência, por 100 mil habitantes. Todos os prédios do mesmo município recebem a mesma taxa. Não mede ocorrências na escola, no bairro ou no dia da eleição.",
        "precisa_bu2": False,
        "grupo": "Economia e segurança",
        "agregacao": "municipios",
    },
}


def numero(valor: Any) -> float | None:
    if valor is None or valor == "":
        return None
    try:
        n = float(valor)
    except (ValueError, TypeError):
        return None
    return n if math.isfinite(n) else None


def municipios(caminho: Path = MUNICIPIOS) -> dict[str, dict]:
    """Chave UF-código TSE, preservando zeros à esquerda e origem documental."""
    if not caminho.exists():
        return {}
    out = {}
    with caminho.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["uf"] == "ZZ":
                continue
            m = {
                k: r.get(k) or None
                for k in (
                    "municipio",
                    "ibge",
                    "homicidios_fonte",
                    "crime_organizado",
                    "crime_organizado_fontes",
                )
            }
            for k in (
                "homicidios_taxa_100mil",
                "homicidios_n",
                "homicidios_ano",
                "homicidios_quintil",
            ):
                m[k] = numero(r.get(k))
            out[f"{r['uf']}-{r['mun_tse']}"] = m
    return out


def ler_uf(uf: str, seguranca: dict, origem: Path = POLITIZE) -> dict:
    locais = {}
    muns = {
        k.split("-", 1)[1]: v for k, v in seguranca.items() if k.startswith(uf + "-")
    }
    if uf != "ZZ":
        for p in sorted((origem / "mun" / uf).glob("*.json")):
            d = json.loads(p.read_text(encoding="utf-8"))
            t = d["locais"]
            for linha in t["linhas"]:
                r = dict(zip(t["colunas"], linha, strict=True))
                locais[r["local_id"]] = {
                    k: d.get(k) if k == "perfil_fonte" else r.get(k) for k in COLUNAS
                }
    return {"locais": locais, "municipios": muns}


def resumo_local(id_local: str, contexto: dict) -> dict:
    local = contexto.get("locais", {}).get(id_local, {})
    m = contexto.get("municipios", {}).get(id_local.split("-")[1], {})
    return {
        k: numero(local.get(k) if k.startswith("renda") else m.get(k))
        for k in CAMPOS_MAPA
    }


def metadados(origem: Path = POLITIZE) -> dict:
    pnad = origem / "pnad_renda.json"
    p = json.loads(pnad.read_text(encoding="utf-8")) if pnad.exists() else {}
    fontes = json.loads(FONTES.read_text(encoding="utf-8")) if FONTES.exists() else {}
    return {
        "versao": 1,
        "renda": {
            k: p.get(k)
            for k in (
                "universo",
                "renda",
                "mes_precos",
                "faixas",
                "salario_minimo_2026",
                "regra_substituicao",
            )
        },
        "fontes": [
            f
            for f in fontes.get("fontes", [])
            if f.get("camada") in ("homicidios_municipio", "crime_organizado")
        ],
        "proveniencia": [
            {
                "caminho": str(f.relative_to(ROOT)),
                "sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
            }
            for f in (MUNICIPIOS, pnad, origem / "indice.json")
            if f.exists()
        ],
        "nota": "Renda estimada pelo perfil agregado; escolaridade do cadastro eleitoral (fonte por município). Homicídios e registros de crime organizado são municipais. Nenhuma dessas medidas identifica indivíduos, risco na escola ou causa do voto.",
    }
