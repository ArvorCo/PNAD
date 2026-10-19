"""Coleta clima diario (Open-Meteo e, se responder, INMET) para os pontos do 2T.

Uso:
    python3 scripts/mudancas-secoes-2t-clima.py            # coleta e resume
    python3 scripts/mudancas-secoes-2t-clima.py --resumo   # so refaz o resumo

Entrada: analysis/mudancas_secoes_2t/pontos_clima.json.
Respostas cruas: data/originals/mudancas_secoes_2t/{open_meteo,inmet}/.
Saidas: analysis/mudancas_secoes_2t/clima/{open_meteo.json,inmet_diario.json,
inmet_tentativa.txt}. Retomavel: respostas ja salvas nao sao refeitas.
Dias sem dado no arquivo ERA5 vem da API de previsao com past_days.
"""

import argparse
import json
import math
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
PONTOS = ROOT / "analysis/mudancas_secoes_2t/pontos_clima.json"
CLIMA = ROOT / "analysis/mudancas_secoes_2t/clima"
RAW = ROOT / "data/originals/mudancas_secoes_2t"
INICIO, FIM = "2026-09-28", "2026-10-18"
VARS = [
    "precipitation_sum",
    "precipitation_hours",
    "wind_gusts_10m_max",
    "temperature_2m_max",
]
ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"
FORECAST = "https://api.open-meteo.com/v1/forecast"
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
)
INMET = "https://apitempo.inmet.gov.br"


def agora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_json(url, params, tentativas=6):
    """GET com recuo exponencial em 429 e erros de rede."""
    for n in range(tentativas):
        try:
            r = requests.get(url, params=params, timeout=60, headers={"User-Agent": UA})
            if r.status_code == 200:
                return r.json(), r.url
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(5 * 2**n)
                continue
            r.raise_for_status()
        except requests.RequestException:
            time.sleep(5 * 2**n)
    raise RuntimeError(f"falha em {url}")


def coletar_ponto(p):
    """Baixa archive e, se faltar dia, forecast; grava a resposta crua."""
    destino = RAW / "open_meteo" / f"{p['id']}.json"
    if destino.exists():
        return
    base = {
        "latitude": p["lat"],
        "longitude": p["lon"],
        "daily": ",".join(VARS),
        "timezone": "America/Sao_Paulo",
    }
    arq, url_a = get_json(ARCHIVE, {**base, "start_date": INICIO, "end_date": FIM})
    cru = {"coletado_em": agora(), "archive": {"url": url_a, "resposta": arq}}
    daily = arq.get("daily", {})
    faltam = any(v is None for k in VARS for v in daily.get(k, [None]))
    if faltam:
        prev, url_f = get_json(FORECAST, {**base, "past_days": 21, "forecast_days": 1})
        cru["forecast"] = {"url": url_f, "resposta": prev}
    destino.write_text(json.dumps(cru, ensure_ascii=False))


def dias_do_ponto(cru):
    """Une as duas respostas: archive primeiro, forecast para o que for null."""
    por_data = {}
    for fonte in ("archive", "forecast"):
        if fonte not in cru:
            continue
        d = cru[fonte]["resposta"].get("daily", {})
        for i, dia in enumerate(d.get("time", [])):
            if not INICIO <= dia <= FIM:
                continue
            reg = por_data.setdefault(dia, {})
            for v in VARS:
                valor = d[v][i]
                if valor is not None and reg.get(v) is None:
                    reg[v] = valor
                    reg.setdefault("_f", {})[v] = fonte
    saida = []
    for dia in sorted(por_data):
        reg = por_data[dia]
        origens = set(reg.get("_f", {}).values())
        fonte = "forecast" if "forecast" in origens else "archive"
        item = {"data": dia}
        item.update({v: reg.get(v) for v in VARS})
        item["fonte"] = fonte if origens else "ausente"
        saida.append(item)
    return saida


def percentil(valores, q):
    v = sorted(valores)
    if not v:
        return None
    k = (len(v) - 1) * q
    lo, hi = math.floor(k), math.ceil(k)
    return round(v[lo] + (v[hi] - v[lo]) * (k - lo), 2)


def parcela(valores, corte):
    if not valores:
        return None
    return round(sum(1 for x in valores if x > corte) / len(valores), 4)


def resumir(pontos):
    res = {}
    for grupo in ("mudanca", "controle"):
        ids = [i for i, p in pontos.items() if p["grupo"] == grupo]

        def serie(i, var, ini="2026-09-28", fim=FIM):
            return [
                d[var]
                for d in pontos[i]["dias"]
                if ini <= d["data"] <= fim and d[var] is not None
            ]

        chuva4 = [
            d["precipitation_sum"]
            for i in ids
            for d in pontos[i]["dias"]
            if d["data"] == "2026-10-04" and d["precipitation_sum"] is not None
        ]
        maxd = [
            max(s) for i in ids if (s := serie(i, "precipitation_sum", "2026-10-05"))
        ]
        rajada = [max(s) for i in ids if (s := serie(i, "wind_gusts_10m_max"))]
        res[grupo] = {
            "pontos": len(ids),
            "chuva_04_10": {
                "n": len(chuva4),
                "acima_20mm": parcela(chuva4, 20),
                "acima_50mm": parcela(chuva4, 50),
                "mediana_mm": percentil(chuva4, 0.5),
            },
            "maximo_diario_05_a_18_10": {
                "n": len(maxd),
                "mediana_mm": percentil(maxd, 0.5),
                "p90_mm": percentil(maxd, 0.9),
                "acima_20mm": parcela(maxd, 20),
                "acima_50mm": parcela(maxd, 50),
            },
            "rajada_maxima_periodo": {
                "n": len(rajada),
                "mediana_kmh": percentil(rajada, 0.5),
                "acima_60kmh": parcela(rajada, 60),
            },
        }
    calmos = []
    for i, p in pontos.items():
        if p["grupo"] != "mudanca":
            continue
        chuva = [d["precipitation_sum"] or 0 for d in p["dias"]]
        vento = [d["wind_gusts_10m_max"] or 0 for d in p["dias"]]
        if not any(c > 10 for c in chuva) and not any(w > 50 for w in vento):
            calmos.append(i)
    res["mudanca_sem_chuva_10mm_nem_rajada_50kmh"] = {
        "quantidade": len(calmos),
        "ids": sorted(calmos),
    }
    return res


def montar_open_meteo(pontos_in):
    saida = {}
    for p in pontos_in:
        arq = RAW / "open_meteo" / f"{p['id']}.json"
        if not arq.exists():
            continue
        cru = json.loads(arq.read_text())
        saida[p["id"]] = {
            "lat": p["lat"],
            "lon": p["lon"],
            "grupo": p["grupo"],
            "uf": p["uf"],
            "coletado_em": cru["coletado_em"],
            "dias": dias_do_ponto(cru),
        }
    exemplo = pontos_in[0]
    q = f"latitude={exemplo['lat']}&longitude={exemplo['lon']}&daily={','.join(VARS)}"
    doc = {
        "gerado_em": agora(),
        "janela": {"inicio": INICIO, "fim": FIM},
        "fonte": {
            "nome": "Open-Meteo",
            "modelos": (
                "ERA5 (archive-api, reanalise) e previsao/analise "
                "(api.open-meteo.com, past_days=21) para dias ainda nulos no arquivo"
            ),
            "urls_exemplo": [
                f"{ARCHIVE}?{q}&start_date={INICIO}&end_date={FIM}"
                "&timezone=America/Sao_Paulo",
                f"{FORECAST}?{q}&past_days=21&forecast_days=1"
                "&timezone=America/Sao_Paulo",
            ],
        },
        "resumo": resumir(saida),
        "pontos": saida,
    }
    (CLIMA / "open_meteo.json").write_text(json.dumps(doc, ensure_ascii=False))
    return doc


def tentar_inmet(pontos_in):
    """Testa a API do INMET; grava a tentativa e, se responder JSON, os dados."""
    linhas = [f"tentativa em {agora()} (User-Agent de navegador)"]
    estacoes, diaria_ok = None, False
    sondas = (
        f"{INMET}/estacoes/T",
        f"{INMET}/estacao/diaria/2026-10-01/2026-10-18/A001",
        f"{INMET}/estacao/2026-10-04/2026-10-04/A001",
        f"{INMET}/estacao/2026-10-04/2026-10-04/A701",
    )
    for url in sondas:
        try:
            r = requests.get(url, timeout=60, headers={"User-Agent": UA})
            corpo = r.text[:200].replace("\n", " ")
            linhas.append(
                f"{url} -> HTTP {r.status_code}, {len(r.content)} bytes: {corpo!r}"
            )
            try:
                dados = r.json()
            except ValueError:
                dados = None
            if dados and url.endswith("/T"):
                estacoes = dados
            elif dados and "/diaria/" in url:
                diaria_ok = True
        except requests.RequestException as e:
            linhas.append(f"{url} -> erro de rede: {e}")
    linhas.append(
        "conclusao: "
        + (
            "serie diaria responde"
            if diaria_ok
            else "cadastro de estacoes responde, mas a serie diaria nao (404 E_ROUTE_NOT_FOUND) "
            "e a serie horaria devolve 204 sem corpo; sem dado de estacao, so Open-Meteo"
        )
    )
    (CLIMA / "inmet_tentativa.txt").write_text("\n".join(linhas) + "\n")
    if diaria_ok and estacoes:
        baixar_inmet(pontos_in, estacoes)
    return diaria_ok


def haversine(lat1, lon1, lat2, lon2):
    f1, f2 = math.radians(lat1), math.radians(lat2)
    a = (
        math.sin((f2 - f1) / 2) ** 2
        + math.cos(f1) * math.cos(f2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    )
    return 6371.0 * 2 * math.asin(math.sqrt(a))


def baixar_inmet(pontos_in, estacoes):
    aut = [
        e
        for e in estacoes
        if e.get("TP_ESTACAO") == "Automatica" and e.get("VL_LATITUDE")
    ]
    (RAW / "inmet").mkdir(parents=True, exist_ok=True)
    mapa, usadas = {}, {}
    for p in pontos_in:
        if p["grupo"] != "mudanca":
            continue
        melhor = min(
            aut,
            key=lambda e: haversine(
                p["lat"], p["lon"], float(e["VL_LATITUDE"]), float(e["VL_LONGITUDE"])
            ),
            default=None,
        )
        if melhor is None:
            continue
        dist = haversine(
            p["lat"],
            p["lon"],
            float(melhor["VL_LATITUDE"]),
            float(melhor["VL_LONGITUDE"]),
        )
        if dist <= 50:
            mapa[p["id"]] = {
                "estacao": melhor["CD_ESTACAO"],
                "distancia_km": round(dist, 1),
            }
            usadas[melhor["CD_ESTACAO"]] = melhor
    for cod, est in usadas.items():
        arq = RAW / "inmet" / f"{cod}.json"
        if not arq.exists():
            url = f"{INMET}/estacao/diaria/{INICIO}/{FIM}/{cod}"
            dados, _ = get_json(url, None)
            arq.write_text(json.dumps(dados, ensure_ascii=False))
            time.sleep(0.5)
        est["diaria"] = json.loads(arq.read_text())
    doc = {
        "gerado_em": agora(),
        "janela": {"inicio": INICIO, "fim": FIM},
        "estacoes": usadas,
        "pontos": mapa,
    }
    (CLIMA / "inmet_diario.json").write_text(json.dumps(doc, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--resumo", action="store_true", help="nao baixa, so consolida")
    ap.add_argument("--threads", type=int, default=4)
    args = ap.parse_args()
    pontos_in = json.loads(PONTOS.read_text())["pontos"]
    (RAW / "open_meteo").mkdir(parents=True, exist_ok=True)
    CLIMA.mkdir(parents=True, exist_ok=True)
    if not args.resumo:
        pendentes = [
            p
            for p in pontos_in
            if not (RAW / "open_meteo" / f"{p['id']}.json").exists()
        ]
        print(f"{len(pendentes)} pontos a coletar", file=sys.stderr)
        for i in range(0, len(pendentes), 100):
            lote = pendentes[i : i + 100]
            t0 = time.time()
            with ThreadPoolExecutor(args.threads) as ex:
                list(ex.map(coletar_ponto, lote))
            print(f"  {min(i + 100, len(pendentes))}/{len(pendentes)}", file=sys.stderr)
            time.sleep(max(0, 20 - (time.time() - t0)))
        tentar_inmet(pontos_in)
    doc = montar_open_meteo(pontos_in)
    print(json.dumps(doc["resumo"], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
