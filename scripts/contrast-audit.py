#!/usr/bin/env python3
"""Audita o contraste de texto das páginas publicadas, medindo o pixel.

O método é deliberadamente burro e por isso confiável: coleta cada trecho de
texto, torna o texto transparente, fotografa a página inteira e lê a cor que
está de fato pintada atrás de cada caixa. Isso pega o que a leitura do CSS não
pega, como texto que herda a cor branca de um capítulo escuro e cai sobre um
cartão claro, gradiente, foto de fundo e sobreposição translúcida.

Uso:

    python3 -m http.server 8899 --directory docs &
    python3 scripts/contrast-audit.py http://localhost:8899/quaest_globo_140826.html

Sai com código 1 se alguma medida ficar abaixo do mínimo da WCAG AA, que é
4,5:1 para texto normal e 3:1 para texto grande.
"""

from __future__ import annotations

import argparse
import io
import json
import sys

COLLECT = """
() => {
  const out = [];
  document.querySelectorAll('body *').forEach((el, i) => {
    const direct = Array.from(el.childNodes)
      .filter(n => n.nodeType === 3 && n.textContent.trim().length > 1)
      .map(n => n.textContent.trim()).join(' ');
    if (!direct) return;
    const st = getComputedStyle(el);
    if (st.display === 'none' || st.visibility === 'hidden') return;
    if (parseFloat(st.opacity) === 0 || st.position === 'fixed') return;
    // Opacidade zero herdada apaga o elemento sem zerar a opacidade dele.
    // Sem esta checagem o recorte leria o fundo da seção atrás de um cartão
    // que não foi pintado, e devolveria reprovação inventada.
    for (let up = el.parentElement; up && up !== document.body; up = up.parentElement) {
      if (parseFloat(getComputedStyle(up).opacity) === 0) return;
    }
    const box = el.getBoundingClientRect();
    if (box.width < 4 || box.height < 4) return;
    if (box.top + window.scrollY < 0 || box.left < 0) return;
    if (box.right > document.documentElement.scrollWidth) return;
    const svg = el.namespaceURI === 'http://www.w3.org/2000/svg';
    el.setAttribute('data-contrast-audit', String(i));
    out.push({
      id: String(i),
      color: (svg && st.fill && st.fill !== 'none') ? st.fill : st.color,
      size: parseFloat(st.fontSize),
      weight: st.fontWeight,
      tag: el.tagName.toLowerCase(),
      cls: typeof el.className === 'string' ? el.className : '',
      text: direct.slice(0, 70)
    });
  });
  return out;
}
"""

HIDE = """
() => document.querySelectorAll('[data-contrast-audit]').forEach(node => {
  node.style.setProperty('color', 'transparent', 'important');
  node.style.setProperty('fill', 'transparent', 'important');
})
"""

# O acervo tem três convenções de revelação ao rolar: `.reveal.in`,
# `.reveal.visible` e `.rv.in`. Marcar as classes reproduz o estado de quem
# rolou a página inteira; a folha injetada é a rede de segurança para qualquer
# convenção futura. Sem isso a página é fotografada com os blocos ainda em
# `opacity: 0`, e o recorte lê o fundo da seção em vez do cartão.
REVEAL = """
() => {
  document.querySelectorAll('.reveal, .rv').forEach(node => {
    node.classList.add('in');
    node.classList.add('visible');
  });
  const sheet = document.createElement('style');
  sheet.textContent =
    '.reveal, .rv { opacity: 1 !important; transform: none !important;' +
    ' transition: none !important; animation: none !important }';
  document.head.appendChild(sheet);
}
"""


def parse_rgb(value: str) -> tuple[float, float, float, float]:
    numbers = value[value.index("(") + 1 : value.index(")")].split(",")
    parts = [float(item) for item in numbers]
    alpha = parts[3] if len(parts) > 3 else 1.0
    return parts[0], parts[1], parts[2], alpha


def luminance(rgb: tuple[float, float, float]) -> float:
    def channel(value: float) -> float:
        value /= 255
        return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4

    red, green, blue = rgb
    return 0.2126 * channel(red) + 0.7152 * channel(green) + 0.0722 * channel(blue)


def contrast(
    first: tuple[float, float, float], second: tuple[float, float, float]
) -> float:
    a, b = luminance(first), luminance(second)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


def dominant_color(image) -> tuple[int, int, int]:
    counts: dict[tuple[int, int, int], int] = {}
    for pixel in image.convert("RGB").getdata():
        counts[pixel] = counts.get(pixel, 0) + 1
    return max(counts.items(), key=lambda item: item[1])[0]


def threshold_for(size: float, weight: str) -> float:
    try:
        bold = int(weight) >= 700
    except ValueError:
        bold = weight in {"bold", "bolder"}
    large = size >= 24 or (size >= 18.66 and bold)
    return 3.0 if large else 4.5


def full_page_image(page, Image):
    """Fotografa a pagina inteira em faixas.

    O Chromium nao devolve captura acima de aproximadamente 16.384 pixels de
    altura: o excedente volta branco, o que fazia o auditor acusar contraste
    falso no rodape de dossies longos. Capturar em faixas e costurar resolve.
    """
    width, height = page.evaluate(
        "() => [document.documentElement.scrollWidth, document.documentElement.scrollHeight]"
    )
    width, height = int(width), int(height)
    faixa = 8000
    if height <= faixa:
        return Image.open(io.BytesIO(page.screenshot(full_page=True))).convert("RGB")
    canvas = Image.new("RGB", (width, height), (255, 255, 255))
    topo = 0
    while topo < height:
        altura = min(faixa, height - topo)
        raw = page.screenshot(
            full_page=True,
            clip={"x": 0, "y": topo, "width": width, "height": altura},
        )
        canvas.paste(Image.open(io.BytesIO(raw)).convert("RGB"), (0, topo))
        topo += altura
    return canvas


def audit_page(page, url: str) -> list[dict]:
    from PIL import Image

    page.goto(url, wait_until="networkidle")
    page.wait_for_timeout(1200)
    page.evaluate(REVEAL)
    page.wait_for_timeout(600)
    items = page.evaluate(COLLECT)
    page.evaluate(HIDE)
    page.wait_for_timeout(300)
    shot = full_page_image(page, Image)
    problems = []
    for item in items:
        handle = page.query_selector(f'[data-contrast-audit="{item["id"]}"]')
        if handle is None:
            continue
        box = handle.bounding_box()
        if not box:
            continue
        left, top = int(box["x"]), int(box["y"])
        right = min(shot.width, int(box["x"] + box["width"]))
        bottom = min(shot.height, int(box["y"] + box["height"]))
        if right - left < 2 or bottom - top < 2:
            continue
        background = dominant_color(shot.crop((left, top, right, bottom)))
        red, green, blue, alpha = parse_rgb(item["color"])
        if alpha < 1:
            red = red * alpha + background[0] * (1 - alpha)
            green = green * alpha + background[1] * (1 - alpha)
            blue = blue * alpha + background[2] * (1 - alpha)
        ratio = contrast((red, green, blue), background)
        minimum = threshold_for(item["size"], item["weight"])
        if ratio < minimum:
            problems.append(
                {
                    "ratio": round(ratio, 2),
                    "minimum": minimum,
                    "where": f'{item["tag"]}.{item["cls"]}'.strip("."),
                    "color": item["color"],
                    "background": "rgb%s" % (background,),
                    "font_px": item["size"],
                    "text": item["text"],
                }
            )
    return problems


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urls", nargs="+", help="páginas servidas por HTTP")
    parser.add_argument("--width", type=int, default=1280)
    args = parser.parse_args()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit(
            "instale playwright: pip install playwright && playwright install chromium"
        )

    failures = 0
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": args.width, "height": 1000})
        for url in args.urls:
            problems = audit_page(page, url)
            failures += len(problems)
            print(f"\n=== {url}: {len(problems)} abaixo do mínimo WCAG AA")
            for problem in sorted(problems, key=lambda item: item["ratio"]):
                print(json.dumps(problem, ensure_ascii=False))
        browser.close()
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
