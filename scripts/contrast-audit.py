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
import contextlib
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

# Elemento grudado na janela e fotografado uma vez por faixa, e a costura o
# repete a cada 8.000 pixels sobre conteudo que nada tem a ver com ele. Numa
# pagina longa isso pinta a barra de capitulos escura no meio do texto e o
# auditor acusa reprovacao que nao existe. Antes de fotografar, solta todo
# `sticky` e `fixed`.
UNSTICK = """
() => {
  // `scroll-behavior: smooth` transforma cada rolagem em animacao, e a faixa
  // seguinte era fotografada no meio do caminho: a captura do rodape de um
  // dossie de 32 mil pixels voltava em branco e o auditor acusava contraste
  // 1,28 sobre fundo que nao existe.
  document.documentElement.style.setProperty('scroll-behavior', 'auto', 'important');
  document.body.style.setProperty('scroll-behavior', 'auto', 'important');
  // Imagem preguicosa so carrega quando entra na janela, e a pagina cresce no
  // meio da captura em faixas: as faixas ja coladas ficam deslocadas e o
  // auditor le o fundo de outro bloco. Carrega tudo antes de fotografar.
  for (const img of document.querySelectorAll('img[loading="lazy"]')) {
    img.loading = 'eager';
    img.decoding = 'sync';
  }
  for (const el of document.querySelectorAll('*')) {
    const pos = getComputedStyle(el).position;
    if (pos === 'sticky' || pos === 'fixed') {
      el.style.setProperty('position', 'static', 'important');
    }
  }
}
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


def full_page_image(page, Image, faixa: int = 4000):
    """Fotografa a pagina inteira em faixas, rolando a janela.

    O Chromium nao devolve captura acima de aproximadamente 16.384 pixels de
    altura, e `full_page=True` com recorte nao escapa disso: o recorte incide
    sobre uma captura ja truncada e devolve pedaco em branco ou deslocado, o que
    fazia o auditor inventar reprovacao em dossie longo. A saida e nao pedir
    pagina inteira nenhuma: encolhe a janela para a altura da faixa, rola ate
    cada faixa e fotografa so o que esta visivel. A largura nao muda, entao o
    layout e o mesmo.

    A janela fica na altura da faixa ao retornar; quem chama restaura.
    """
    width, height = page.evaluate(
        "() => [document.documentElement.scrollWidth, document.documentElement.scrollHeight]"
    )
    width, height = int(width), int(height)
    if height <= faixa:
        return Image.open(io.BytesIO(page.screenshot(full_page=True))).convert("RGB")
    page.set_viewport_size({"width": width, "height": faixa})
    page.wait_for_timeout(200)
    height = int(page.evaluate("() => document.documentElement.scrollHeight"))
    canvas = Image.new("RGB", (width, height), (255, 255, 255))
    topo = 0
    while topo < height:
        page.evaluate(
            "(y) => { document.documentElement.scrollTop = y; "
            "document.body.scrollTop = y; }",
            topo,
        )
        page.wait_for_timeout(90)
        real = int(page.evaluate("() => window.scrollY"))
        raw = page.screenshot()
        canvas.paste(Image.open(io.BytesIO(raw)).convert("RGB"), (0, real))
        if real < topo:
            break
        topo = real + faixa
    page.evaluate("window.scrollTo(0, 0)")
    return canvas


# A caixa precisa ser absoluta no documento, nao relativa a janela. A captura em
# faixas rola a pagina para fotografar, e `bounding_box()` do Playwright devolve
# coordenada de viewport: depois da rolagem, todo recorte saia deslocado e o
# auditor acusava reprovacao inventada em pagina acima de 8.000 pixels.
ABSOLUTE_BOXES = """
() => {
  const out = {};
  for (const el of document.querySelectorAll('[data-contrast-audit]')) {
    // Texto dentro de <details> fechado tem caixa de layout no Chromium, mas
    // nao e pintado: medir o pixel ali le o que estiver desenhado por baixo e
    // reprova contraste que o leitor nunca ve. So entra o que esta visivel.
    if (el.closest('details:not([open])')) continue;
    if (el.checkVisibility && !el.checkVisibility({
      contentVisibilityAuto: true,
      opacityProperty: false,
      visibilityProperty: true,
    })) continue;
    const r = el.getBoundingClientRect();
    out[el.getAttribute('data-contrast-audit')] = {
      x: r.left + window.scrollX,
      y: r.top + window.scrollY,
      width: r.width,
      height: r.height,
    };
  }
  return out;
}
"""


def exact_background(page, Image, box: dict) -> tuple[int, int, int] | None:
    """Le o fundo de um elemento rolando ate ele e fotografando so a caixa.

    A costura de faixas serve para varrer a pagina inteira rapido, mas qualquer
    deslocamento de um pixel vira reprovacao inventada. Entao ela e so o filtro:
    o que reprova volta para esta medida exata, dentro da janela, sem costura.
    """
    largura = max(int(box["width"]), 1)
    altura = max(int(box["height"]), 1)
    if largura < 2 or altura < 2:
        return None
    alvo = max(int(box["y"]) - 200, 0)
    page.evaluate("(y) => { document.documentElement.scrollTop = y; }", alvo)
    page.wait_for_timeout(60)
    scroll = int(page.evaluate("() => window.scrollY"))
    janela = page.viewport_size or {"width": 1280, "height": 900}
    topo = int(box["y"]) - scroll
    if topo < 0 or topo + altura > janela["height"]:
        return None
    raw = page.screenshot(
        clip={
            "x": max(int(box["x"]), 0),
            "y": topo,
            "width": min(largura, janela["width"] - max(int(box["x"]), 0)),
            "height": altura,
        }
    )
    return dominant_color(Image.open(io.BytesIO(raw)).convert("RGB"))


def audit_page(page, url: str) -> list[dict]:
    from PIL import Image

    page.goto(url, wait_until="networkidle")
    page.wait_for_timeout(1200)
    page.evaluate(REVEAL)
    page.wait_for_timeout(600)
    items = page.evaluate(COLLECT)
    page.evaluate(UNSTICK)
    page.evaluate(HIDE)
    with contextlib.suppress(Exception):
        page.wait_for_load_state("networkidle", timeout=15000)
    page.wait_for_timeout(600)
    janela = page.viewport_size
    shot = full_page_image(page, Image)
    boxes = page.evaluate(ABSOLUTE_BOXES)
    problems: list[dict] = []
    suspeitos: list[tuple] = []
    for item in items:
        box = boxes.get(str(item["id"]))
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
            suspeitos.append((item, box, minimum))

    for item, box, minimum in suspeitos:
        background = exact_background(page, Image, box)
        if background is None:
            continue
        red, green, blue, alpha = parse_rgb(item["color"])
        if alpha < 1:
            red = red * alpha + background[0] * (1 - alpha)
            green = green * alpha + background[1] * (1 - alpha)
            blue = blue * alpha + background[2] * (1 - alpha)
        ratio = contrast((red, green, blue), background)
        if ratio < minimum:
            problems.append(
                {
                    "ratio": round(ratio, 2),
                    "minimum": minimum,
                    "where": f'{item["tag"]}.{item["cls"]}'.strip("."),
                    "color": item["color"],
                    "background": f"rgb{background}",
                    "font_px": item["size"],
                    "text": item["text"],
                }
            )
    if janela:
        page.set_viewport_size(janela)
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
