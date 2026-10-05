"""QA das figuras do dossiê da apuração (Playwright).

Servidor: python3 -m http.server 4173 --directory docs

Passa o ponteiro (e toca, no celular) no primeiro, no do meio e no último alvo de
cada figura do catálogo, confere que a ficha aparece e fica dentro da caixa da
figura, exercita alternâncias, abas e filtro, e grava
analysis/apuracao_2026/qa-fig-*.png. Sai com código 1 se algo falhar.
"""

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent
URL = "http://localhost:4173/apuracao_1o_turno_2026.html"
CSS_QA = "html{scroll-behavior:auto!important}.js figure.reveal{opacity:1!important;transform:none!important}"

MEDE = """(fig) => {
  const f = fig.getBoundingClientRect();
  const c = fig.querySelector('.fig-tip');
  if (!c || c.hidden || !c.classList.contains('on')) return {visivel: false};
  const r = c.getBoundingClientRect();
  return {visivel: true, dentro: r.left >= f.left - 0.5 && r.right <= f.right + 0.5
    && r.top >= f.top - 0.5 && r.bottom <= f.bottom + 0.5, texto: c.innerText.slice(0, 80)};
}"""


def prepara(page):
    page.goto(URL, wait_until="load")
    page.add_style_tag(content=CSS_QA)
    page.wait_for_timeout(400)


def alvo_visivel(fig, i):
    hits = [h for h in fig.query_selector_all(".hit") if h.is_visible()]
    if not hits:
        return None
    return hits[min(i, len(hits) - 1)] if i >= 0 else hits[-1]


def passa(page, fig, el):
    el.scroll_into_view_if_needed()
    caixa = el.bounding_box()
    if not caixa:
        return {"visivel": False}
    x = caixa["x"] + min(caixa["width"] / 2, 30)
    y = caixa["y"] + caixa["height"] / 2
    page.mouse.move(x, y)
    page.wait_for_timeout(120)
    return fig.evaluate(MEDE)


def varre(page, falhas):
    figs = page.query_selector_all("figure[data-fig]")
    for fig in figs:
        nome = fig.get_attribute("data-fig")
        n = len(fig.query_selector_all(".hit"))
        if n == 0 and not fig.query_selector("svg[data-near]"):
            falhas.append(f"{nome}: sem alvo interativo")
            continue
        for i in (0, n // 2, -1):
            el = alvo_visivel(fig, i)
            if el is None:
                continue
            m = passa(page, fig, el)
            if not m["visivel"]:
                falhas.append(f"{nome}[{i}]: ficha não apareceu")
            elif not m["dentro"]:
                falhas.append(f"{nome}[{i}]: ficha fora da figura")
        page.mouse.move(2, 2)
    return len(figs)


def foto(page, nome, acao=None, sufixo=""):
    fig = page.query_selector(f"#fig-{nome}")
    fig.scroll_into_view_if_needed()
    if acao:
        acao(page, fig)
    page.wait_for_timeout(150)
    fig.screenshot(path=str(OUT / f"qa-fig-{nome}{sufixo}.png"))
    return fig.evaluate(MEDE)


def hover_idx(i):
    def f(page, fig):
        passa(page, fig, alvo_visivel(fig, i))

    return f


def clica_e_hover(seletor, i):
    def f(page, fig):
        fig.query_selector(seletor).click()
        page.wait_for_timeout(120)
        passa(page, fig, alvo_visivel(fig, i))

    return f


def perto(page, fig):
    fig.query_selector('button[data-filtro="1"]').click()
    svg = fig.query_selector("svg[data-near]")
    svg.evaluate("e => e.scrollIntoView({block: 'center'})")
    page.wait_for_timeout(100)
    b = svg.bounding_box()
    page.mouse.move(b["x"] + b["width"] * 0.30, b["y"] + b["height"] * 0.62)


def run():
    falhas, rel = [], {}
    with sync_playwright() as p:
        nav = p.chromium.launch()
        page = nav.new_page(viewport={"width": 1440, "height": 900})
        erros = []
        page.on("pageerror", lambda e: erros.append(str(e)))
        prepara(page)
        rel["figuras"] = varre(page, falhas)
        rel["fotos"] = {
            "placar_candidatos": foto(page, "placar_candidatos", hover_idx(1)),
            "mapa_vencedor_uf": foto(page, "mapa_vencedor_uf", hover_idx(25)),
            "hemiciclo_camara": foto(
                page,
                "hemiciclo_camara",
                clica_e_hover('button[data-alt="partido"]', 300),
            ),
            "mapa_anomalias": foto(page, "mapa_anomalias", hover_idx(-1)),
            "acumulado_noite": foto(page, "acumulado_noite", hover_idx(-1)),
            "mapa_swing_uf": foto(
                page, "mapa_swing_uf", clica_e_hover('button[data-alt="MG"]', 400)
            ),
            "dispersao_municipios": foto(page, "dispersao_municipios", perto),
            "pesquisas_erro": foto(
                page, "pesquisas_erro", clica_e_hover('button[data-alt="flavio"]', 6)
            ),
            "hemiciclo_senado": foto(page, "hemiciclo_senado", hover_idx(70)),
        }
        mob = nav.new_page(
            viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True
        )
        prepara(mob)
        fig = mob.query_selector("#fig-mapa_vencedor_uf")
        fig.scroll_into_view_if_needed()
        alvo = alvo_visivel(fig, 20)
        b = alvo.bounding_box()
        mob.touchscreen.tap(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)
        mob.wait_for_timeout(150)
        m = fig.evaluate(MEDE)
        fig.screenshot(path=str(OUT / "qa-fig-mapa_vencedor_uf-390.png"))
        mob.touchscreen.tap(5, 5)
        mob.wait_for_timeout(150)
        rel["toque"] = {"abre": m, "fecha_fora": not fig.evaluate(MEDE)["visivel"]}
        largura = mob.evaluate("document.documentElement.scrollWidth")
        rel["rolagem_lateral_390"] = largura > 390
        rel["erros"] = erros
        nav.close()
    for nome, m in rel["fotos"].items():
        if not m.get("visivel") or not m.get("dentro"):
            falhas.append(f"foto {nome}: {m}")
    if not rel["toque"]["abre"].get("dentro") or not rel["toque"]["fecha_fora"]:
        falhas.append(f"toque: {rel['toque']}")
    if rel["rolagem_lateral_390"]:
        falhas.append("página rola de lado em 390 px")
    if erros:
        falhas.append(f"erros de console: {erros}")
    rel["falhas"] = falhas
    print(json.dumps(rel, ensure_ascii=False, indent=1))
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(run())
