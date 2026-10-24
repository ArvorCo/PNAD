"""Janelas de votação: chuva e rajada referem-se à hora anterior ao carimbo."""

from __future__ import annotations

import math
import unicodedata

PERIODOS = {
    "votacao": ("Votação completa", 8, 17),
    "manha": ("Manhã", 8, 12),
    "almoco": ("Almoço", 12, 14),
    "transicao": ("Entre almoço e tarde", 14, 15),
    "tarde": ("Tarde", 15, 17),
}
VARIAVEIS = {
    "chuva_mm": "precipitation",
    "prob_pct": "precipitation_probability",
    "rajada_kmh": "wind_gusts_10m",
}
AM_ACRE = {
    "AMATURA",
    "ATALAIA DO NORTE",
    "BENJAMIN CONSTANT",
    "EIRUNEPE",
    "ENVIRA",
    "GUAJARA",
    "IPIXUNA",
    "ITAMARATI",
    "JUTAI",
    "TABATINGA",
    "SAO PAULO DE OLIVENCA",
}


def fuso_local(uf: str, municipio: str) -> int:
    """Deslocamento UTC oficial, inclusive os 11 municípios do AM e Noronha."""
    nome = "".join(
        c
        for c in unicodedata.normalize("NFD", municipio.upper())
        if not unicodedata.combining(c)
    )
    if uf.upper() == "AC" or (uf.upper() == "AM" and nome in AM_ACRE):
        return -5
    if uf.upper() == "PE" and nome == "FERNANDO DE NORONHA":
        return -2
    return -4 if uf.upper() in {"AM", "MT", "MS", "RO", "RR"} else -3


def janela_local(inicio: int, fim: int, utc: int) -> str:
    return f"{inicio + utc + 3:02d}h–{fim + utc + 3:02d}h"


def extrair(resposta: dict, alvo: str, risco) -> dict:
    h = resposta.get("hourly", {})
    tempos = h.get("time", [])
    serie = []
    for hora in range(9, 18):
        carimbo = f"{alvo}T{hora:02d}:00"
        pos = tempos.index(carimbo) if carimbo in tempos else None
        item = {
            "inicio_brasilia": f"{alvo}T{hora - 1:02d}:00:00-03:00",
            "fim_brasilia": carimbo + ":00-03:00",
        }
        for campo, variavel in VARIAVEIS.items():
            valores = h.get(variavel, [])
            v = valores[pos] if pos is not None and pos < len(valores) else None
            item[campo] = (
                v if isinstance(v, (int, float)) and math.isfinite(v) else None
            )
        serie.append(item)
    periodos = {}
    for chave, (nome, ini, fim) in PERIODOS.items():
        horas = serie[ini - 8 : fim - 8]
        p = {
            "nome": nome,
            "inicio_brasilia": ini,
            "fim_brasilia": fim,
            "duracao_h": fim - ini,
        }
        for campo in VARIAVEIS:
            valores = [v[campo] for v in horas]
            p[campo] = (
                (round(sum(valores), 3) if campo == "chuva_mm" else max(valores))
                if all(v is not None for v in valores)
                else None
            )
        p["completa"] = all(p[k] is not None for k in VARIAVEIS)
        p["risco"] = risco(*(p[k] for k in VARIAVEIS)) if p["completa"] else "sem_dado"
        periodos[chave] = p
    return {"horas": serie, "periodos": periodos}


def resumir(celulas: dict, indice: dict) -> dict:
    """Médias ponderadas pelo cadastro; sem imputar as células não respondidas."""
    saida = {}
    for chave, (nome, ini, fim) in PERIODOS.items():
        grupos = {}
        for c, locais in indice["celulas"].items():
            p = celulas.get(c, {}).get("periodos", {}).get(chave, {})
            for uf, _cod, _nome, _locais, eleitores in locais:
                for grupo in ("BR", uf):
                    g = grupos.setdefault(
                        grupo,
                        {
                            "eleitores": 0,
                            "cobertos": 0,
                            "chuva_ponderada": 0,
                            "eleitores_chuva_1mm": 0,
                            "eleitores_risco_alto": 0,
                        },
                    )
                    g["eleitores"] += eleitores
                    if p.get("completa"):
                        g["cobertos"] += eleitores
                        g["chuva_ponderada"] += p["chuva_mm"] * eleitores
                        g["eleitores_chuva_1mm"] += (
                            eleitores if p["chuva_mm"] >= 1 else 0
                        )
                        g["eleitores_risco_alto"] += (
                            eleitores if p["risco"] == "alto" else 0
                        )
        for g in grupos.values():
            soma = g.pop("chuva_ponderada")
            g["chuva_media_mm"] = (
                round(soma / g["cobertos"], 3) if g["cobertos"] else None
            )
            g["chuva_media_por_hora_mm"] = (
                round(soma / g["cobertos"] / (fim - ini), 3) if g["cobertos"] else None
            )
            g["cadastro_chuva_1mm_pct"] = (
                round(100 * g["eleitores_chuva_1mm"] / g["eleitores"], 2)
                if g["eleitores"]
                else None
            )
        saida[chave] = {
            "nome": nome,
            "inicio_brasilia": ini,
            "fim_brasilia": fim,
            "duracao_h": fim - ini,
            "grupos": grupos,
        }
    return saida
