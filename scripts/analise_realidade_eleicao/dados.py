"""Junções territoriais: resultado municipal oficial e BUs agregados nas capitais."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from .desenvolvimento import ROOT, carregar

OUTPUT = ROOT / "analysis/analise_realidade_eleicao"
FIELDS = ("renda_ate2", "renda_mais5", "renda_mediana_brl", "superior")


def ler(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def linhas(tab: dict):
    return [dict(zip(tab["colunas"], row, strict=True)) for row in tab["linhas"]]


def numero(v):
    return float(v) if v not in (None, "") else None


def ponderar(rows, campo, peso="aptos"):
    validos = [r for r in rows if r.get(campo) is not None and (r.get(peso) or 0) > 0]
    w = sum(r[peso] for r in validos)
    return sum(r[campo] * r[peso] for r in validos) / w if w else None


def cortes(rows):
    """Corte estrito em contagens inteiras, antes de qualquer arredondamento."""
    return {
        str(t): [
            m["ibge"]
            for m in rows
            if m["completo"]
            and m["validos"] > 0
            and 100 * m["flavio"] < t * m["validos"]
        ]
        for t in (5, 10, 25, 30)
    }


def renda_locais(m):
    p = ROOT / f"docs/assets/politize/dados/mun/{m['uf']}/{m['cd_tse']}.json"
    if not p.exists():
        return [], None
    j = ler(p)
    return linhas(j["locais"]), j.get("perfil_fonte")


def zonas_capital(m, antigos):
    """Só locais dentro da capital, mesmo quando a zona inclui outro município."""
    path = ROOT / f"docs/assets/politize_se/dados/mun/{m['uf']}/{m['cd_tse']}.json"
    novos = linhas(ler(path)["locais"])
    lookup = {r["local_id"]: r for r in antigos}
    grupos = defaultdict(list)
    for r in novos:
        r = dict(r)
        for f in FIELDS:
            r[f] = lookup.get(r["local_id"], {}).get(f)
        grupos[r["zona"]].append(r)
    saida = []
    for zona, rows in sorted(grupos.items()):
        f, votos_lula = (sum(r[k] or 0 for r in rows) for k in ("flavio2", "lula2"))
        total = sum(r["n_secoes"] for r in rows)
        recebidas = sum(r["n_bu2"] for r in rows)
        aptos = sum(r["aptos2"] or 0 for r in rows)
        n_renda = sum(r["aptos2"] or 0 for r in rows if r["renda_ate2"] is not None)
        saida.append(
            {
                "uf": m["uf"],
                "ibge": m["ibge"],
                "nome": m["nome"],
                "zona": zona,
                "flavio": f,
                "lula": votos_lula,
                "validos": f + votos_lula,
                "pct_lula": (
                    100 * votos_lula / (f + votos_lula) if f + votos_lula else None
                ),
                "aptos": aptos,
                "secoes": total,
                "bus": recebidas,
                "completo": total == recebidas,
                "locais": len(rows),
                "cobertura_renda": 100 * n_renda / aptos if aptos else None,
                **{k: ponderar(rows, k, "aptos2") for k in FIELDS},
                "lat": ponderar(rows, "lat", "aptos2"),
                "lon": ponderar(rows, "lon", "aptos2"),
                "link": f"politizese.html#uf={m['uf']}&z={zona}",
            }
        )
    return saida


def construir():
    p = ROOT / "analysis/apuracao_2t_2026/dados/presidente.json"
    presidente = ler(p)
    ms = [m for m in linhas(presidente["municipios"]) if m["uf"] != "ZZ"]
    ips = carregar(ms)
    seguranca = {
        (r["uf"], r["mun_tse"]): r
        for r in csv.DictReader(
            (ROOT / "data/outputs/fiscais_risco_municipios.csv").open(encoding="utf-8")
        )
    }
    zs, cobertura = [], []
    for m in ms:
        assert m["flavio"] + m["lula"] == m["validos"], m["ibge"]
        m["pct_lula"] = 100 * m["lula"] / m["validos"] if m["validos"] else None
        m["pct_flavio"] = 100 - m["pct_lula"] if m["validos"] else None
        m["diferenca"] = abs(m["lula"] - m["flavio"])
        m["ips"] = ips["dados"].get(m["ibge"], {}).get("ips")
        antigos, fonte = renda_locais(m)
        m.update({k: ponderar(antigos, k) for k in FIELDS})
        m["perfil_fonte"] = fonte
        aptos = sum(r.get("aptos") or 0 for r in antigos)
        com_renda = sum(r["aptos"] for r in antigos if r.get("renda_ate2") is not None)
        m["cobertura_renda"] = 100 * com_renda / aptos if aptos else None
        sec = seguranca.get((m["uf"], m["cd_tse"]), {})
        for k in (
            "homicidios_taxa_100mil",
            "homicidios_n",
            "homicidios_ano",
            "sede_lat",
            "sede_lon",
        ):
            m[k] = numero(sec.get(k))
        # Não codificar falta de documentação como ausência de crime organizado.
        m["crime_documentado"] = sec.get("crime_organizado") == "mapeamento público"
        m["crime_fontes"] = sec.get("crime_organizado_fontes") or None
        m["crime_fbsp"] = "fbsp-cartografias" in (m["crime_fontes"] or "")
        m["rural_pct"] = (
            (
                100
                * sum(r["aptos"] for r in antigos if r.get("setor_situacao") == "rural")
                / aptos
            )
            if aptos
            else None
        )
        if m["capital"]:
            zonas = zonas_capital(m, antigos)
            zs.extend(zonas)
            cobertura.append(
                {
                    "uf": m["uf"],
                    "nome": m["nome"],
                    "zonas": len(zonas),
                    "oficial_validos": m["validos"],
                    "bus_validos": sum(z["validos"] for z in zonas),
                    "oficial_flavio": m["flavio"],
                    "bus_flavio": sum(z["flavio"] for z in zonas),
                    "oficial_lula": m["lula"],
                    "bus_lula": sum(z["lula"] for z in zonas),
                    "secoes": m["secoes_total"],
                    "bus": sum(z["bus"] for z in zonas),
                }
            )
    ms.sort(key=lambda m: m["ibge"])
    return {
        "municipios": ms,
        "zonas": zs,
        "cortes": cortes(ms),
        "cobertura_capitais": cobertura,
        "ips": {k: v for k, v in ips.items() if k != "dados"},
        "meta_tse": presidente["meta"],
        "pnad": {
            k: v
            for k, v in ler(ROOT / "docs/assets/politize/dados/pnad_renda.json").items()
            if k != "linhas"
        },
        "hash_presidente": hashlib.sha256(p.read_bytes()).hexdigest(),
    }
