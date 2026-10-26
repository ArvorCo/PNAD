"""Chuva de 25/10/2026 por célula de 0,25°: estações primeiro, modelo onde não há estação.

Estações (CEMADEN; INMET quando houver dado público) a até 50 km do centro da célula entram
numa média ponderada pelo inverso do quadrado da distância (distância mínima de 1 km). Cada
célula grava ``n_estacoes``, ``distancia_min_km`` e ``fonte`` (``cemaden``, ``inmet``,
``ambos`` ou ``ifs_provisorio``; ``era5`` quando a coleta da reanálise substituir o modelo).

Duas medidas de estação, com origem declarada por variável:
- ``chuva_dia_mm``: dia 25/10 de 00h a 24h de Brasília. Vem da série horária quando há, ou
  da foto da tabela de acumulados do CEMADEN (``acc48hr - acc24hr`` às 03h UTC de 27/10;
  conferência ``acc72hr - acc48hr`` às 03h UTC de 28/10).
- ``chuva_votacao_mm``: 07h às 18h de Brasília (10h a 21h UTC), só da série horária.
Rajada e temperatura vêm sempre do modelo: pluviômetro não mede vento.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from clima_1t import grade
from clima_1t.coleta import agora
from clima_1t.variaveis import faixa_chuva, faixa_rajada
from clima_2t import estacoes, modelo

ROOT = Path(__file__).resolve().parents[2]
SAIDA = ROOT / "analysis/clima_2t_2026"
PUBLICO = ROOT / "docs/assets/fiscais_mapa/clima/observado_2t.json"
RAIO_KM = 50.0
DIST_MIN_KM = 1.0
CHUVA_FORTE_MM = 20.0
RAJADA_FORTE_KMH = 50.0
JANELA = (7, 18)  # horas cheias de Brasília
BRT = timezone(timedelta(hours=-3))
DIA = datetime(2026, 10, 25, tzinfo=BRT)
FOTOS = [  # (rótulo, coluna maior, coluna menor): a diferença é 25/10 00h a 24h BRT
    ("20261027T0300Z", "acc48hr", "acc24hr"),
    ("20261028T0300Z", "acc72hr", "acc48hr"),
]
TOLERANCIA_FOTO_MIN = 120  # último valor da estação até 2 h antes da foto


def km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(min(1.0, a)))


def _num(v: Any) -> float | None:
    """'-' na tabela do CEMADEN é janela sem acumulado (zero); vazio é falta."""
    if v == "-":
        return 0.0
    if isinstance(v, (int, float)) and math.isfinite(v):
        return float(v)
    return None


def _quando(texto: str | None) -> datetime | None:
    if not texto:
        return None
    try:
        return datetime.strptime(texto, "%d/%m/%y %H:%M").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def diario_das_fotos() -> tuple[dict[int, dict[str, Any]], dict[str, Any]]:
    """Chuva de 25/10 por estação a partir das fotos agendadas da tabela de acumulados."""
    por: dict[int, dict[str, Any]] = {}
    usadas: dict[str, Any] = {}
    for rotulo, maior, menor in FOTOS:
        pasta = estacoes.RAW / "cemaden_acumulados" / rotulo
        if not (pasta / "resumo.json").exists():
            usadas[rotulo] = "ainda não tirada"
            continue
        t = datetime.strptime(rotulo, "%Y%m%dT%H%MZ").replace(tzinfo=timezone.utc)
        n = 0
        for uf in estacoes.UFS:
            arq = pasta / f"{uf}.json"
            try:
                linhas = json.loads(arq.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            for x in linhas:
                ult = _quando(x.get("datahoraUltimovalor"))
                if ult is None or (t - ult).total_seconds() > TOLERANCIA_FOTO_MIN * 60:
                    continue
                a, b = _num(x.get(maior)), _num(x.get(menor))
                if a is None or b is None or a < b:
                    continue
                item = por.setdefault(int(x["idestacao"]), {})
                item.setdefault("dia_mm", round(a - b, 2))
                item.setdefault("dia_fonte", f"foto {rotulo}: {maior} - {menor}")
                item.setdefault("conferencias", []).append(round(a - b, 2))
                n += 1
        usadas[rotulo] = {"estacoes_validas": n, "colunas": f"{maior} - {menor}"}
    return por, usadas


def _hora_utc(data: str, rotulo_hora: str) -> datetime | None:
    hh = rotulo_hora.lower().replace("h", "").strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d/%m/%y"):
        try:
            d = datetime.strptime(data.strip(), fmt)
            return d.replace(hour=int(hh), tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def horario_cemaden() -> dict[int, dict[str, Any]]:
    """Série horária por estação (rótulo ``Hh`` UTC = início da hora, como no gráfico)."""
    por: dict[int, dict[str, Any]] = {}
    for arq in sorted((estacoes.RAW / "cemaden").glob("*.json")):
        doc = json.loads(arq.read_text(encoding="utf-8"))
        r = doc["resposta"]
        horas: dict[datetime, float] = {}
        for i, data in enumerate(r["datas"]):
            linha = r["acumulados"][i] if i < len(r["acumulados"]) else []
            for j, rot in enumerate(r["horarios"]):
                v = linha[j] if j < len(linha) else None
                t = _hora_utc(str(data), str(rot))
                if v is not None and t is not None:
                    horas[t] = float(v)
        dia0 = DIA.astimezone(timezone.utc)
        dia = [dia0 + timedelta(hours=k) for k in range(24)]
        jan = [dia0 + timedelta(hours=k) for k in range(JANELA[0], JANELA[1])]
        item: dict[str, Any] = {}
        if all(t in horas for t in jan):
            item["votacao_mm"] = round(sum(horas[t] for t in jan), 2)
            item["por_hora_brt"] = {
                (t.astimezone(BRT)).strftime("%H"): horas[t] for t in jan
            }
        if all(t in horas for t in dia):
            item["dia_mm"] = round(sum(horas[t] for t in dia), 2)
            item["dia_fonte"] = "série horária"
        if item:
            por[int(doc["estacao"]["idestacao"])] = item
    return por


def estacoes_medidas() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Lista de estações com coordenada e ao menos uma medida de 25/10."""
    catalogo = {int(e["idestacao"]): e for e in estacoes.catalogo_cemaden()}
    fotos, uso_fotos = diario_das_fotos()
    hor = horario_cemaden()
    lista = []
    for idx in sorted(set(fotos) | set(hor)):
        e = catalogo.get(idx)
        if e is None or e.get("latitude") is None:
            continue
        h, f = hor.get(idx, {}), fotos.get(idx, {})
        lista.append(
            {
                "rede": "cemaden",
                "id": idx,
                "codigo": e.get("codestacao"),
                "nome": e.get("nomeestacao"),
                "uf": e.get("uf"),
                "lat": float(e["latitude"]),
                "lon": float(e["longitude"]),
                "dia_mm": h.get("dia_mm", f.get("dia_mm")),
                "dia_fonte": h.get("dia_fonte", f.get("dia_fonte")),
                "votacao_mm": h.get("votacao_mm"),
            }
        )
    resumo = {
        "cemaden_catalogo": len(catalogo),
        "cemaden_com_dia": sum(1 for x in lista if x["dia_mm"] is not None),
        "cemaden_com_votacao": sum(1 for x in lista if x["votacao_mm"] is not None),
        "fotos": uso_fotos,
        "inmet": "sem dado público de 25/10 (ver fontes/inmet_tentativas_25_10.json)",
    }
    return lista, resumo


def interpolar(
    centro: tuple[float, float], lista: list[dict[str, Any]], campo: str
) -> dict[str, Any] | None:
    """Média ponderada por 1/d² das estações a até 50 km com o campo medido."""
    lat, lon = centro
    viz = []
    for s in lista:
        v = s.get(campo)
        if v is None or abs(s["lat"] - lat) > 0.5 or abs(s["lon"] - lon) > 0.6:
            continue
        d = km(lat, lon, s["lat"], s["lon"])
        if d <= RAIO_KM:
            viz.append((max(d, DIST_MIN_KM), v, s["rede"]))
    if not viz:
        return None
    w = [1 / d**2 for d, _, _ in viz]
    redes = {r for _, _, r in viz}
    return {
        "mm": round(
            sum(wi * v for wi, (_, v, _) in zip(w, viz, strict=True)) / sum(w), 1
        ),
        "n": len(viz),
        "dmin": round(min(d for d, _, _ in viz), 1),
        "rede": "ambos" if len(redes) > 1 else next(iter(redes)),
    }


def _janela_modelo(m: dict[str, Any], campo: str, func) -> float | None:
    """Horas 8 a 18 do modelo (valor da hora H = H-1 a H) = 07h às 18h de Brasília."""
    vals = [
        v
        for h, v in zip(m["horas"], m[campo], strict=True)
        if JANELA[0] + 1 <= int(h) <= JANELA[1]
    ]
    if len(vals) != JANELA[1] - JANELA[0] or any(v is None for v in vals):
        return None
    return round(func(vals), 1)


def consolidar(fonte_modelo: str = "ifs") -> dict[str, Any]:
    celulas = modelo.celulas_1t()
    mod = modelo.ler(fonte_modelo)
    lista, resumo_est = estacoes_medidas()
    rotulo_mod = "ifs_provisorio" if fonte_modelo == "ifs" else fonte_modelo
    saida: dict[str, Any] = {}
    for c, centro in celulas.items():
        m = mod.get(c)
        dia = interpolar(centro, lista, "dia_mm")
        vot = interpolar(centro, lista, "votacao_mm")
        mv = _janela_modelo(m, "chuva", sum) if m else None
        md = m["diario"]["precipitation_sum"] if m else None
        raj = _janela_modelo(m, "rajada", max) if m else None
        raj_dia = m["diario"]["wind_gusts_10m_max"] if m else None
        tmax = m["diario"]["temperature_2m_max"] if m else None
        ref = vot or dia
        item = {
            "chuva_votacao_mm": vot["mm"] if vot else mv,
            "fonte_votacao": (
                vot["rede"] if vot else (rotulo_mod if mv is not None else None)
            ),
            "chuva_dia_mm": (
                dia["mm"] if dia else (round(md, 1) if md is not None else None)
            ),
            "fonte_dia": (
                dia["rede"] if dia else (rotulo_mod if md is not None else None)
            ),
            "chuva_votacao_modelo_mm": mv,
            "chuva_dia_modelo_mm": round(md, 1) if md is not None else None,
            "rajada_votacao_kmh": raj,
            "rajada_dia_kmh": round(raj_dia, 1) if raj_dia is not None else None,
            "temperatura_max_c": round(tmax, 1) if tmax is not None else None,
            "n_estacoes": ref["n"] if ref else 0,
            "distancia_min_km": ref["dmin"] if ref else None,
            "fonte": ref["rede"] if ref else (rotulo_mod if m else None),
        }
        base = item["chuva_votacao_mm"]
        item["faixa_chuva"] = faixa_chuva(base)
        item["faixa_rajada"] = faixa_rajada(raj)
        item["chuva_forte"] = None if base is None else int(base >= CHUVA_FORTE_MM)
        cd = item["chuva_dia_mm"]
        item["faixa_chuva_dia"] = faixa_chuva(cd)
        item["chuva_forte_dia"] = None if cd is None else int(cd >= CHUVA_FORTE_MM)
        item["rajada_forte"] = None if raj is None else int(raj >= RAJADA_FORTE_KMH)
        saida[c] = item
    cont: dict[str, int] = {}
    for it in saida.values():
        cont[str(it["fonte"])] = cont.get(str(it["fonte"]), 0) + 1
    doc = {
        "gerado_em": agora(),
        "dia": "2026-10-25",
        "celula_graus": grade.PASSO_ARCHIVE,
        "janela_votacao_brasilia": "07h às 18h (votação oficial 08h às 17h, uma hora de folga)",
        "raio_km": RAIO_KM,
        "peso": "inverso do quadrado da distância ao centro da célula (mínimo 1 km)",
        "modelo": modelo.MODELOS[fonte_modelo]["nome"],
        "cortes": {
            "chuva_forte_mm": CHUVA_FORTE_MM,
            "rajada_forte_kmh": RAJADA_FORTE_KMH,
        },
        "estacoes": resumo_est,
        "cobertura": {
            "celulas": len(celulas),
            "com_modelo": len(mod),
            "por_fonte": cont,
            "com_estacao_dia": sum(
                1
                for it in saida.values()
                if it["fonte_dia"] in ("cemaden", "inmet", "ambos")
            ),
            "com_estacao_votacao": sum(
                1
                for it in saida.values()
                if it["fonte_votacao"] in ("cemaden", "inmet", "ambos")
            ),
        },
        "celulas": saida,
    }
    SAIDA.mkdir(parents=True, exist_ok=True)
    (SAIDA / "clima.json").write_text(
        json.dumps(doc, ensure_ascii=False, separators=(",", ":"))
    )
    (SAIDA / "estacoes.json").write_text(
        json.dumps(
            {"gerado_em": doc["gerado_em"], "estacoes": lista},
            ensure_ascii=False,
            separators=(",", ":"),
        )
    )
    publicar(doc, fonte_modelo)
    return doc


ROTULOS = {
    "cemaden": "chuva medida em estações CEMADEN",
    "inmet": "chuva medida em estações INMET",
    "ambos": "chuva medida em estações INMET e CEMADEN",
    "ifs_provisorio": "modelo meteorológico, provisório",
    "era5": "reanálise ERA5",
}


def publicar(doc: dict[str, Any], fonte_modelo: str) -> None:
    """Arquivo público do mapa: lista compacta por célula de 0,25°."""
    colunas = [
        "chuva_votacao_mm",
        "fonte_votacao",
        "chuva_dia_mm",
        "fonte_dia",
        "rajada_votacao_kmh",
        "rajada_dia_kmh",
        "n_estacoes",
        "distancia_min_km",
        "fonte",
        "faixa_chuva",
        "chuva_forte",
        "faixa_chuva_dia",
        "chuva_forte_dia",
        "rajada_forte",
    ]
    pub = {
        "formato": 1,
        "gerado_em": doc["gerado_em"],
        "dia": doc["dia"],
        "fonte": "estações CEMADEN a até 50 km; sem estação, " + doc["modelo"],
        "rotulos_fonte": ROTULOS,
        "celula_graus": doc["celula_graus"],
        "chave": "floor(lat*4)/4,floor(lon*4)/4 com duas casas (ex.: -23.75,-46.75)",
        "janela_votacao_brasilia": doc["janela_votacao_brasilia"],
        "raio_km": RAIO_KM,
        "peso": doc["peso"],
        "cortes": doc["cortes"],
        "cobertura": doc["cobertura"],
        "estacoes": {k: v for k, v in doc["estacoes"].items() if k != "fotos"},
        "nota": "Chuva medida em pluviômetro a até 50 km é estimativa para a célula, não "
        "medição no prédio. Rajada vem sempre do modelo. Modelo provisório será trocado pela "
        "reanálise ERA5 quando ela cobrir 25/10 (prevista para 31/10).",
        "colunas": colunas,
        "celulas": {c: [it[k] for k in colunas] for c, it in doc["celulas"].items()},
    }
    PUBLICO.write_text(json.dumps(pub, ensure_ascii=False, separators=(",", ":")))
