#!/usr/bin/env python3
"""Audita se os gráficos de uma página publicada realmente pintam alguma coisa.

O método é o mesmo do auditor de contraste: em vez de ler o CSS, mede o que
o navegador desenhou. Pega a classe de defeito que passa despercebida em
revisão de código, que é o elemento com largura correta no atributo e
tamanho zero na tela. O caso real: barra de gráfico marcada como <i>, que é
`display: inline` por padrão e por isso ignora `width` e `height`, ficando
invisível mesmo com a porcentagem certa no style e a cor certa no CSS.

Uso:
    python3 -m http.server 4173 --directory docs &
    python3 scripts/render-audit.py http://localhost:4173/mg_082026.html

Sai com código 1 se algum elemento dimensionado não pintar, se algum
container de gráfico ficar vazio, ou se o console acusar erro.
"""

from __future__ import annotations

import argparse
import json
import sys

SONDA = """
() => {
  const problemas = [];
  const px = el => el.getBoundingClientRect();

  for (const el of document.querySelectorAll('[style*="width"],[style*="height"]')) {
    const cs = getComputedStyle(el);
    const caixa = px(el);
    const pede = el.style.width || el.style.height;
    if (!pede) continue;
    const zero = /^0(px|%|em|rem)?$/.test(pede.trim());
    if (cs.display === 'inline') {
      problemas.push({tipo: 'dimensao em elemento inline', tag: el.tagName.toLowerCase(),
                      classe: el.className, style: el.getAttribute('style').slice(0, 60)});
    } else if (!zero && caixa.width < 1 && caixa.height < 1) {
      problemas.push({tipo: 'elemento dimensionado com area zero', tag: el.tagName.toLowerCase(),
                      classe: el.className, style: el.getAttribute('style').slice(0, 60)});
    }
  }

  const alvo = /(chart|map|scatter|table-body|legend|readout)$/;
  // <defs>, <pattern>, <linearGradient> e afins definem pintura e nao ocupam
  // area por desenho. Medir altura neles produz falso positivo.
  const definicao = new Set(['DEFS', 'PATTERN', 'LINEARGRADIENT', 'RADIALGRADIENT',
                             'CLIPPATH', 'MASK', 'SYMBOL', 'MARKER', 'FILTER']);
  for (const el of document.querySelectorAll('[id]')) {
    if (!alvo.test(el.id)) continue;
    if (definicao.has(el.tagName.toUpperCase())) continue;
    if (el.closest('defs')) continue;
    const caixa = px(el);
    if (el.children.length === 0 || caixa.height < 8) {
      problemas.push({tipo: 'container de grafico vazio', tag: '#' + el.id,
                      classe: '', style: `filhos=${el.children.length} altura=${Math.round(caixa.height)}`});
    }
  }
  return problemas;
}
"""


def audit(page, url: str) -> list[dict]:
    erros: list[str] = []
    page.on("console", lambda m: erros.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: erros.append(str(e)))
    page.goto(url, wait_until="networkidle")
    page.wait_for_timeout(2500)
    page.evaluate(
        "document.querySelectorAll('.reveal').forEach(e => e.classList.add('visible'))"
    )
    page.wait_for_timeout(400)
    problemas = page.evaluate(SONDA)
    for texto in erros:
        problemas.append(
            {"tipo": "erro de console", "tag": "", "classe": "", "style": texto[:160]}
        )
    return problemas


def main() -> int:
    from playwright.sync_api import sync_playwright

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urls", nargs="+", help="páginas servidas por HTTP")
    parser.add_argument("--width", type=int, default=1440)
    args = parser.parse_args()

    total = 0
    with sync_playwright() as play:
        browser = play.chromium.launch()
        page = browser.new_page(viewport={"width": args.width, "height": 1000})
        for url in args.urls:
            problemas = audit(page, url)
            total += len(problemas)
            print(f"\n=== {url}: {len(problemas)} problema(s) de renderização")
            for item in problemas:
                print(json.dumps(item, ensure_ascii=False))
        browser.close()
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
