#!/usr/bin/env python3
"""Dados do mapa de fiscais em tela cheia (``docs/fiscais_mapa.html``).

Lê, só para leitura, o capítulo 13 do dossiê da apuração
(``analysis/apuracao_2026/dados/fiscais.json``: as 13.045 seções sinalizadas, com a
classificação original por nível) e os fragmentos do Politize
(``docs/assets/politize/dados``: coordenada e CEP de todos os locais de votação, para
centrar a busca por CEP, zona ou município mesmo onde não há seção sinalizada).

Grava em ``docs/assets/fiscais_mapa/``:

- ``dados.json``: as seções sinalizadas (uma linha por seção, como a planilha
  ``docs/assets/fiscais_2026.csv``), os critérios, os rótulos e o risco por local;
- ``cep/<2 dígitos>.json``: CEP de local de votação (8 e 5 dígitos) para coordenada;
- ``zonas.json``: centro de cada zona eleitoral (média dos locais);
- ``municipios.json``: centro de cada município (índice do Politize).

Coordenada fora do território (ou ausente) vira ``null``: o mapa não inventa posição e
o modo lista mostra a linha com "sem coordenada". Uso: ``python3 scripts/fiscais-mapa-build.py``.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FISCAIS = ROOT / "analysis/apuracao_2026/dados/fiscais.json"
POLITIZE = ROOT / "docs/assets/politize/dados"
SAIDA = ROOT / "docs/assets/fiscais_mapa"
COLUNAS = [
    "uf",
    "municipio",
    "zona",
    "secao",
    "local_id",
    "local",
    "endereco",
    "bairro",
    "cep",
    "lat",
    "lon",
    "nivel",
    "pontuacao",
    "criterios",
    "explicacao",
    "risco",
    "aptos",
    "flavio_pct",
    "lula_pct",
]
# caixa do território (Brasil, com ilhas oceânicas) para recusar coordenada trocada
LAT_MIN, LAT_MAX, LON_MIN, LON_MAX = -34.0, 5.5, -74.5, -28.5


def ponto(uf: str, lat: Any, lon: Any) -> tuple[float, float] | None:
    """Coordenada como ``(lat, lon)`` quando é número e cai no território; senão ``None``."""
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        return None
    la, lo = float(lat), float(lon)
    if la == 0 and lo == 0:
        return None
    if uf == "ZZ":
        ok = -90 <= la <= 90 and -180 <= lo <= 180
    else:
        ok = LAT_MIN <= la <= LAT_MAX and LON_MIN <= lo <= LON_MAX
    return (la, lo) if ok else None


def coord_valida(uf: str, lat: Any, lon: Any) -> bool:
    return ponto(uf, lat, lon) is not None


def _json(caminho: Path, obj: Any) -> int:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    txt = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    caminho.write_text(txt, encoding="utf-8")
    return len(txt.encode("utf-8"))


def tabela(obj: dict[str, Any]) -> list[dict[str, Any]]:
    cols = obj["colunas"]
    return [dict(zip(cols, ln, strict=True)) for ln in obj["linhas"]]


def dados_fiscais() -> tuple[dict[str, Any], int]:
    d = json.loads(FISCAIS.read_text(encoding="utf-8"))
    linhas = []
    invalidas = 0
    risco_local: dict[str, list[str]] = {}
    for s in d["secoes"]:
        lat, lon = s.get("lat"), s.get("lon")
        if lat is not None and not coord_valida(s["uf"], lat, lon):
            invalidas += 1
        if not coord_valida(s["uf"], lat, lon):
            lat = lon = None
        r = s.get("risco") or {}
        if r.get("motivos_risco"):
            risco_local[s["local_id"]] = list(r["motivos_risco"])
        linhas.append(
            [
                s["uf"],
                s["municipio"],
                int(s["zona"]),
                int(s["secao"]),
                s["local_id"],
                s.get("local"),
                s.get("endereco"),
                s.get("bairro"),
                s.get("cep"),
                lat,
                lon,
                s["nivel"],
                s.get("pontuacao"),
                "".join(s.get("criterios") or []),
                s.get("explicacao_provavel"),
                r.get("nivel_risco_fiscal"),
                s.get("aptos"),
                s.get("flavio_pct"),
                s.get("lula_pct"),
            ]
        )
    criterios = {
        c["id"]: {
            "nome": c["nome"],
            "mede": c.get("mede"),
            "conferir": c.get("o_que_conferir"),
            "explicacao_comum": c.get("explicacao_comum"),
            "secoes": c.get("secoes"),
        }
        for c in d["criterios"]
    }
    obj = {
        "titulo": "Mapa de fiscais: seções sinalizadas no 1º turno de 2026",
        "gerado_em": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "fonte": "analysis/apuracao_2026/dados/fiscais.json (capítulo 13)",
        "fonte_gerado_em": d.get("gerado_em"),
        "rotulos": d["rotulos"],
        "criterios": criterios,
        "risco_validar": "validar com a PM e o TRE local",
        "resumo": {
            "secoes": len(linhas),
            "sem_coordenada": sum(1 for x in linhas if x[9] is None),
            "coordenada_invalida": invalidas,
        },
        "risco_local": risco_local,
        "colunas": COLUNAS,
        "linhas": linhas,
    }
    return obj, invalidas


def indices_politize() -> (
    tuple[dict[str, dict[str, Any]], dict[str, Any], list[list[Any]]]
):
    indice = json.loads((POLITIZE / "indice.json").read_text(encoding="utf-8"))
    muns = tabela(indice["municipios"])
    cep8: dict[str, list[tuple[float, float]]] = defaultdict(list)
    cep5: dict[str, list[tuple[float, float]]] = defaultdict(list)
    zonas: dict[tuple[str, int], list[tuple[float, float]]] = defaultdict(list)
    municipios: list[list[Any]] = []
    for m in muns:
        uf = m["uf"]
        if coord_valida(uf, m.get("lat"), m.get("lon")):
            municipios.append([uf, m["nome"], round(m["lat"], 5), round(m["lon"], 5)])
        arq = POLITIZE / m["arquivo"]
        if not arq.exists():
            continue
        for loc in tabela(json.loads(arq.read_text(encoding="utf-8"))["locais"]):
            pt = ponto(uf, loc.get("lat"), loc.get("lon"))
            if pt is None or loc.get("coord_fonte") not in (None, "cadastro"):
                continue
            zonas[(uf, int(loc["zona"]))].append(pt)
            cep = str(loc.get("cep") or "")
            if uf != "ZZ" and len(cep) == 8 and cep.isdigit():
                cep8[cep].append(pt)
                cep5[cep[:5]].append(pt)

    def media(pts: list[tuple[float, float]]) -> list[float]:
        return [
            round(sum(p[0] for p in pts) / len(pts), 5),
            round(sum(p[1] for p in pts) / len(pts), 5),
            len(pts),
        ]

    por_prefixo: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"exato": {}, "p5": {}}
    )
    for c, pts in cep8.items():
        por_prefixo[c[:2]]["exato"][c] = media(pts)
    for c, pts in cep5.items():
        por_prefixo[c[:2]]["p5"][c] = media(pts)
    zon: dict[str, dict[str, Any]] = defaultdict(dict)
    for (uf, z), pts in zonas.items():
        zon[uf][str(z)] = media(pts)
    return dict(por_prefixo), dict(zon), municipios


def main() -> None:
    obj, invalidas = dados_fiscais()
    tam = _json(SAIDA / "dados.json", obj)
    ceps, zonas, municipios = indices_politize()
    for velho in (SAIDA / "cep").glob("*.json"):
        velho.unlink()
    tam_cep = sum(_json(SAIDA / f"cep/{p}.json", v) for p, v in sorted(ceps.items()))
    _json(SAIDA / "zonas.json", zonas)
    _json(SAIDA / "municipios.json", municipios)
    print(
        f"dados.json {tam / 1e6:.2f} MB, {obj['resumo']['secoes']} seções, "
        f"{obj['resumo']['sem_coordenada']} sem coordenada ({invalidas} inválidas); "
        f"cep {len(ceps)} arquivos {tam_cep / 1e6:.2f} MB; zonas {sum(map(len, zonas.values()))}; "
        f"municípios {len(municipios)}"
    )


if __name__ == "__main__":
    main()
