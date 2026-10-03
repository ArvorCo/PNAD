"""QA de UX da página de predição (Playwright). Servidor: python3 -m http.server 4173 --directory docs.

Gera analysis/predicao_2026/qa-ux-*.png e imprime as medidas que sustentam o relatório.
"""

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent
URL = "http://localhost:4173/predicao_2026_1T_presidente.html"
FILE = "file://" + str(OUT.parents[1] / "docs/predicao_2026_1T_presidente.html")
SECTIONS = [
    "previsao", "territorio", "simulador", "pesquisa", "metodo", "casas",
    "abstencao", "incerteza", "validacao", "aprendizado", "fontes",
]  # fmt: skip


def jump(page, selector):
    page.evaluate("document.documentElement.style.scrollBehavior='auto'")
    page.evaluate(f"document.querySelector('{selector}').scrollIntoView()")
    page.wait_for_timeout(250)


def run():
    report = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, (w, h) in {"desktop": (1366, 768), "mobile": (390, 844)}.items():
            ctx = browser.new_context(viewport={"width": w, "height": h})
            page = ctx.new_page()
            errors = []
            page.on("pageerror", lambda e, errors=errors: errors.append(str(e)))
            page.on("console", lambda m, errors=errors: errors.append(m.text) if m.type == "error" else None)
            page.goto(URL, wait_until="load")
            page.evaluate("document.fonts.ready")
            page.wait_for_timeout(600)
            r = report[name] = {"erros": errors}
            page.screenshot(path=str(OUT / f"qa-ux-{name}-hero.png"))
            r["hero_placar_fim_y"] = page.evaluate(
                "document.querySelector('.scoreboard').getBoundingClientRect().bottom"
            )
            r["hero_howto_fim_y"] = page.evaluate(
                "document.querySelector('.howto').getBoundingClientRect().bottom"
            )
            r["hero_links_fim_y"] = page.evaluate(
                "document.querySelector('.hero-links').getBoundingClientRect().bottom"
            )
            r["nav_altura"] = page.evaluate("document.querySelector('.chapter-nav').getBoundingClientRect().height")
            r["nav_h_var"] = page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--nav-h')")

            # navegação: clicar em cada capítulo, conferir destaque e que o título não fica sob a nav
            nav = {}
            for sid in SECTIONS:
                page.evaluate("document.documentElement.style.scrollBehavior='auto'")
                page.evaluate("window.scrollTo(0,0)")
                page.click(f'.chapter-nav a[href="#{sid}"]')
                page.wait_for_timeout(350)
                nav[sid] = page.evaluate(
                    """(sid)=>{const s=document.getElementById(sid);const n=document.querySelector('.chapter-nav').getBoundingClientRect();
                    const cur=[...document.querySelectorAll('.chapter-nav a[aria-current]')].map(a=>a.getAttribute('href'));
                    const head=s.querySelector('.chapter-head')||s;
                    return {gapAbaixoDaNav: Math.round(head.getBoundingClientRect().top-n.bottom), atual:cur}}""",
                    sid,
                )
            r["nav"] = nav
            r["nav_ok"] = all(
                v["atual"] == [f"#{k}"] and v["gapAbaixoDaNav"] >= 0 for k, v in nav.items()
            )
            page.evaluate("window.scrollTo(0,0)")
            page.wait_for_timeout(200)

            # progresso e topo
            jump(page, "#metodo")
            r["progresso_scaleX"] = page.evaluate("document.querySelector('.read-progress-bar').style.transform")
            r["topo_visivel"] = page.evaluate("document.querySelector('.to-top').classList.contains('is-on')")
            page.screenshot(path=str(OUT / f"qa-ux-{name}-metodo.png"))

            # mapa
            jump(page, "#mapa-explorador")
            page.screenshot(path=str(OUT / f"qa-ux-{name}-mapa.png"))
            r["mapa_controles_sob_nav"] = page.evaluate(
                """()=>{const n=document.querySelector('.chapter-nav').getBoundingClientRect().bottom;
                return document.querySelector('.mx-controls').getBoundingClientRect().top < n}"""
            )

            # simulador
            jump(page, "#simulador")
            page.screenshot(path=str(OUT / f"qa-ux-{name}-simulador.png"))
            presets = page.locator(".preset")
            presets.nth(1).click()
            page.wait_for_timeout(300)
            r["preset_ativo"] = page.locator('.preset[aria-pressed="true"]').count()
            page.screenshot(path=str(OUT / f"qa-ux-{name}-simulador-ativo.png"))
            page.locator("#sim-reset").click()

            # tabela das UFs: ordenar
            jump(page, 'table[data-sortable]')
            page.evaluate("window.scrollBy(0,-120)")
            before = page.locator("table[data-sortable] tbody tr td:first-child").all_inner_texts()[:3]
            page.locator("table[data-sortable] th .sort-btn").nth(3).click()
            asc = page.locator("table[data-sortable] tbody tr td:first-child").all_inner_texts()[:3]
            page.locator("table[data-sortable] th .sort-btn").nth(3).click()
            desc = page.locator("table[data-sortable] tbody tr td:first-child").all_inner_texts()[:3]
            page.locator("table[data-sortable] th .sort-btn").nth(3).click()
            back = page.locator("table[data-sortable] tbody tr td:first-child").all_inner_texts()[:3]
            r["sort"] = {"original": before, "asc": asc, "desc": desc, "restaura": back == before}
            page.screenshot(path=str(OUT / f"qa-ux-{name}-tabela.png"))

            # método, equação, glossário
            page.evaluate("document.querySelectorAll('details').forEach(d=>d.open=true)")
            page.wait_for_timeout(300)
            r["scrollWidth_detalhes_abertos"] = page.evaluate("document.documentElement.scrollWidth")
            r["viewport"] = w
            culprits = page.evaluate(
                """(w)=>[...document.querySelectorAll('body *')].filter(e=>{const b=e.getBoundingClientRect();
                return b.right>w+1 && !e.closest('.table-scroll,.wide-chart,.equation,pre,.preset-grid,.chapter-nav,.mx-svg,svg,.sim-dock,.mx-sr')
                && getComputedStyle(e).position!=='fixed'}).slice(0,8).map(e=>e.tagName+'.'+e.className+' '+Math.round(e.getBoundingClientRect().right))""",
                w,
            )
            r["estouram_largura"] = culprits
            jump(page, ".method-step:nth-of-type(3)")
            page.evaluate("window.scrollBy(0,-90)")
            page.screenshot(path=str(OUT / f"qa-ux-{name}-passo.png"))
            jump(page, "#incerteza .prose")
            page.screenshot(path=str(OUT / f"qa-ux-{name}-incerteza.png"))
            jump(page, "#aprendizado")
            page.screenshot(path=str(OUT / f"qa-ux-{name}-aprendizado.png"))
            jump(page, "#metodo .glossary")
            page.screenshot(path=str(OUT / f"qa-ux-{name}-glossario.png"))
            jump(page, "#fontes")
            page.screenshot(path=str(OUT / f"qa-ux-{name}-fontes.png"))
            page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
            page.wait_for_timeout(300)
            r["nav_atual_no_fim"] = page.evaluate(
                "[...document.querySelectorAll('.chapter-nav a[aria-current]')].map(a=>a.getAttribute('href'))"
            )
            # teclado: skip link, numa página nova
            page = ctx.new_page()
            page.goto(URL, wait_until="load")
            page.keyboard.press("Tab")
            r["skip_focado"] = page.evaluate("document.activeElement.className")
            page.keyboard.press("Enter")
            r["skip_destino_foco"] = page.evaluate("document.activeElement.id")
            ctx.close()

        # sem JS
        ctx = browser.new_context(viewport={"width": 1366, "height": 768}, java_script_enabled=False)
        page = ctx.new_page()
        page.goto(URL, wait_until="load")
        page.screenshot(path=str(OUT / "qa-ux-desktop-semjs.png"))
        report["semjs"] = {
            "to_top_oculto": not page.locator(".to-top").is_visible(),
            "nav_visivel": page.locator(".chapter-nav").is_visible(),
        }
        ctx.close()
        # file://
        ctx = browser.new_context(viewport={"width": 1366, "height": 768})
        page = ctx.new_page()
        errs = []
        page.on("pageerror", lambda e: errs.append(str(e)))
        page.goto(FILE, wait_until="load")
        page.wait_for_timeout(500)
        report["file"] = {
            "erros": errs,
            "nav_ativo_apos_scroll": (
                page.evaluate("window.scrollTo(0,3000)"),
                page.wait_for_timeout(400),
                page.evaluate("[...document.querySelectorAll('.chapter-nav a[aria-current]')].map(a=>a.textContent)"),
            )[2],
        }
        # impressão
        page.emulate_media(media="print")
        report["print"] = {
            "nav": page.evaluate("getComputedStyle(document.querySelector('.chapter-nav')).display"),
            "simulador": page.evaluate("getComputedStyle(document.querySelector('.simulator')).display"),
        }
        ctx.close()
        browser.close()
    print(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    run()
