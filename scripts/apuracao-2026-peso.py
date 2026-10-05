#!/usr/bin/env python3
"""Mede o peso de uma página no navegador: tempo de carga, nós do DOM e memória.

Serve para comparar a mesma página antes e depois de uma mudança de entrega,
como o carregamento sob demanda das figuras pesadas do dossiê da apuração.
Abre cada arquivo em `file://` (a regra da casa é a página funcionar do disco),
em contexto novo a cada rodada, e lê:

- `domContentLoaded` e `load` pela Navigation Timing;
- nós do DOM, heap de JavaScript e documentos pelo `Performance.getMetrics` do
  protocolo do Chromium;
- RSS do processo renderizador, lido do sistema pelo PID que o
  `SystemInfo.getProcessInfo` devolve.

Com `--materializar`, dispara o evento `beforeprint` depois da carga (é o gatilho
que materializa toda figura adiada, o mesmo que os auditores usam) e mede de novo.

Uso:
    python3 scripts/apuracao-2026-peso.py docs/apuracao_1o_turno_2026.html --rodadas 3
    python3 scripts/apuracao-2026-peso.py antes.html depois.html --materializar --json saida.json
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path

METRICAS = ("Nodes", "JSHeapUsedSize", "JSHeapTotalSize", "Documents", "LayoutCount")

NAVEGACAO = """
() => {
  const n = performance.getEntriesByType('navigation')[0];
  return n ? {dcl: n.domContentLoadedEventEnd, load: n.loadEventEnd,
              interativo: n.domInteractive} : null;
}
"""

ADIADAS = "() => document.querySelectorAll('noscript.fig-src').length"


def rss_kb(pid: int) -> int | None:
    try:
        saida = subprocess.run(
            ["ps", "-o", "rss=", "-p", str(pid)],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
    except OSError:
        return None
    return int(saida) if saida.isdigit() else None


def coleta(page, cdp, navegador_cdp) -> dict:
    page.wait_for_timeout(300)
    metricas = {
        m["name"]: m["value"]
        for m in cdp.send("Performance.getMetrics")["metrics"]
        if m["name"] in METRICAS
    }
    processos = navegador_cdp.send("SystemInfo.getProcessInfo")["processInfo"]
    rss = [rss_kb(p["id"]) for p in processos if p["type"] == "renderer"]
    rss = [r for r in rss if r]
    out = {
        "nos": int(metricas.get("Nodes", 0)),
        "heap_js_mb": round(metricas.get("JSHeapUsedSize", 0) / 1e6, 1),
        "documentos": int(metricas.get("Documents", 0)),
        "layouts": int(metricas.get("LayoutCount", 0)),
        "rss_renderizador_mb": round(max(rss) / 1024, 1) if rss else None,
        "figuras_adiadas": page.evaluate(ADIADAS),
    }
    return out


def rodada(play, url: str, materializar: bool) -> dict:
    browser = play.chromium.launch()
    try:
        navegador_cdp = browser.new_browser_cdp_session()
        contexto = browser.new_context(viewport={"width": 1440, "height": 1000})
        page = contexto.new_page()
        cdp = contexto.new_cdp_session(page)
        cdp.send("Performance.enable")
        t0 = time.perf_counter()
        page.goto(url, wait_until="load")
        tempo_total = round((time.perf_counter() - t0) * 1000)
        nav = page.evaluate(NAVEGACAO) or {}
        out = {
            "dcl_ms": round(nav.get("dcl", 0)),
            "load_ms": round(nav.get("load", 0)),
            "goto_ms": tempo_total,
        }
        out["carga"] = coleta(page, cdp, navegador_cdp)
        if materializar:
            t1 = time.perf_counter()
            page.evaluate("window.dispatchEvent(new Event('beforeprint'))")
            page.wait_for_timeout(800)
            out["materializacao_ms"] = round((time.perf_counter() - t1) * 1000 - 800)
            out["materializada"] = coleta(page, cdp, navegador_cdp)
        return out
    finally:
        browser.close()


def mediana(valores: list) -> float | None:
    v = [x for x in valores if x is not None]
    return round(statistics.median(v), 1) if v else None


def resume(rodadas: list[dict]) -> dict:
    chaves_topo = ("dcl_ms", "load_ms", "goto_ms", "materializacao_ms")
    out: dict = {k: mediana([r.get(k) for r in rodadas]) for k in chaves_topo}
    for bloco in ("carga", "materializada"):
        if any(bloco in r for r in rodadas):
            out[bloco] = {
                k: mediana([r[bloco][k] for r in rodadas if bloco in r])
                for k in rodadas[0].get(bloco, rodadas[-1].get(bloco, {}))
            }
    return {k: v for k, v in out.items() if v is not None}


def main() -> int:
    from playwright.sync_api import sync_playwright

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paginas", nargs="+", type=Path)
    ap.add_argument("--rodadas", type=int, default=3)
    ap.add_argument("--materializar", action="store_true")
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args()
    resultado = {}
    with sync_playwright() as play:
        for caminho in a.paginas:
            url = caminho.resolve().as_uri()
            rodadas = [rodada(play, url, a.materializar) for _ in range(a.rodadas)]
            resultado[str(caminho)] = {
                "bytes": caminho.stat().st_size,
                "rodadas": a.rodadas,
                "mediana": resume(rodadas),
                "detalhe": rodadas,
            }
    for nome, r in resultado.items():
        m = r["mediana"]
        print(f"\n{nome}: {r['bytes']:,} bytes, mediana de {r['rodadas']} rodada(s)")
        print(f"  DOMContentLoaded {m.get('dcl_ms')} ms, load {m.get('load_ms')} ms")
        for bloco in ("carga", "materializada"):
            if bloco in m:
                b = m[bloco]
                print(
                    f"  {bloco}: {b['nos']:,.0f} nós, heap JS {b['heap_js_mb']} MB, "
                    f"RSS {b['rss_renderizador_mb']} MB, figuras adiadas {b['figuras_adiadas']:.0f}"
                )
        if "materializacao_ms" in m:
            print(f"  materialização: {m['materializacao_ms']} ms")
    if a.json:
        a.json.write_text(
            json.dumps(resultado, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
