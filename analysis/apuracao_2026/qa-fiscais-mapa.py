#!/usr/bin/env python3
"""QA do mapa navegável do capítulo 13 (onde colocar fiscal), com Playwright.

Uso: python3 -m http.server 4173 -d docs, depois
python3 analysis/apuracao_2026/qa-fiscais-mapa.py [url]. Confere: zoom pela roda e
pelos botões, arrasto, malha municipal e rótulos sob demanda, busca que centra e
abre o painel com os dois links, lista de UFs, abas e filtro, abas do mapa por
UF, tabelas ordenáveis, nenhuma rolagem lateral em 390 px e nenhum erro de
console. Grava capturas em `analysis/apuracao_2026/qa-fig-fiscais_*.png`.
"""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = (
    sys.argv[1]
    if len(sys.argv) > 1
    else "http://localhost:4173/apuracao_1o_turno_2026.html"
)
SAIDA = Path(__file__).resolve().parent
FIG = "#fig-fiscais_mapa_navegavel"


def vb(page) -> list[float]:
    return [
        float(v)
        for v in page.eval_on_selector(
            f"{FIG} svg.fz-svg", "s => s.getAttribute('viewBox')"
        ).split()
    ]


def checa(cond: bool, msg: str, falhas: list[str]) -> None:
    print(("ok   " if cond else "FALHA ") + msg)
    if not cond:
        falhas.append(msg)


def main() -> int:
    falhas: list[str] = []
    erros: list[str] = []
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        page = nav.new_page(viewport={"width": 1440, "height": 1000})
        page.on("pageerror", lambda e: erros.append(str(e)))
        page.on(
            "console", lambda m: erros.append(m.text) if m.type == "error" else None
        )
        page.goto(URL + "#fiscais", wait_until="load")
        page.wait_for_timeout(600)
        fig = page.locator(FIG)
        fig.scroll_into_view_if_needed()
        svg = page.locator(f"{FIG} svg.fz-svg")
        checa(svg.count() == 1, "mapa navegável presente", falhas)
        n = page.eval_on_selector(
            f"{FIG} script.fz-dados", "s => JSON.parse(s.textContent).pontos.length"
        )
        checa(n > 0, f"{n} pontos no mapa", falhas)
        v0 = vb(page)
        fig.screenshot(path=str(SAIDA / "qa-fig-fiscais_mapa.png"))
        box = svg.bounding_box()
        cx, cy = box["x"] + box["width"] * 0.62, box["y"] + box["height"] * 0.55
        page.mouse.move(cx, cy)
        for _ in range(4):
            page.mouse.wheel(0, -400)
            page.wait_for_timeout(80)
        v1 = vb(page)
        checa(
            v1[2] < v0[2] / 2,
            f"roda aproxima (largura {v0[2]:.0f} para {v1[2]:.1f})",
            falhas,
        )
        page.mouse.move(cx, cy)
        page.mouse.down()
        page.mouse.move(cx - 120, cy - 60, steps=6)
        page.mouse.up()
        v2 = vb(page)
        checa(abs(v2[0] - v1[0]) > 1, "arrastar move o mapa", falhas)
        page.wait_for_timeout(200)
        malha = page.eval_on_selector(f"{FIG} .fz-mun-g", "g => g.childElementCount")
        checa(malha > 0, f"malha municipal sob demanda ({malha} UFs)", falhas)
        page.click(f"{FIG} [data-fz='mais']")
        page.click(f"{FIG} [data-fz='mais']")
        page.wait_for_timeout(200)
        rot = page.eval_on_selector(f"{FIG} .fz-rot", "g => g.childElementCount")
        checa(rot > 0, f"rótulos de município no zoom alto ({rot})", falhas)
        fig.screenshot(path=str(SAIDA / "qa-fig-fiscais_mapa-zoom.png"))
        page.click(f"{FIG} [data-fz='brasil']")
        checa(abs(vb(page)[2] - v0[2]) < 0.5, "botão BR volta ao Brasil", falhas)
        # busca pelo primeiro município do mapa
        alvo = page.eval_on_selector(
            f"{FIG} script.fz-dados",
            "s => {const d=JSON.parse(s.textContent);return d.pontos[d.pontos.length-1]}",
        )
        mun = alvo[4].split(" (")[0]
        page.fill(f"{FIG} .fz-busca input", mun)
        page.press(f"{FIG} .fz-busca input", "Enter")
        page.wait_for_timeout(250)
        v3 = vb(page)
        centro = (v3[0] + v3[2] / 2, v3[1] + v3[3] / 2)
        checa(v3[2] < v0[2] / 5, f"busca por {mun} aproxima", falhas)
        painel = page.inner_text(f"{FIG} .fz-painel")
        links = page.eval_on_selector_all(
            f"{FIG} .fz-painel a", "as => as.map(a => [a.href, a.target])"
        )
        checa(
            len(links) == 2 and all(t == "_blank" for _, t in links),
            "painel com os dois links em nova aba",
            falhas,
        )
        checa(
            "openstreetmap.org" in links[0][0] and "google.com/maps" in links[1][0],
            "links OSM e Google",
            falhas,
        )
        print(
            "     centro",
            [round(c, 1) for c in centro],
            "painel:",
            painel.splitlines()[0][:70],
        )
        fig.screenshot(path=str(SAIDA / "qa-fig-fiscais_mapa-busca.png"))
        # lista de UFs
        page.click(f"{FIG} .fz-ufs li:first-child button")
        page.wait_for_timeout(150)
        checa(vb(page)[2] < v0[2], "clique na UF centra e aproxima", falhas)
        # abas e filtro de risco, quando existem
        if page.locator(f"{FIG} button[data-alt='risco']").count():
            page.click(f"{FIG} button[data-alt='risco']")
            vis = page.eval_on_selector(
                f"{FIG} g[data-alt-show='risco']", "g => g.getAttribute('display')"
            )
            checa(vis is None, "aba de cor pelo risco", falhas)
            page.click(f"{FIG} button[data-filtro='alto']")
            ap = page.eval_on_selector_all(
                f"{FIG} path[data-g].apagado", "x => x.length"
            )
            checa(ap > 0, "filtro de risco apaga os outros níveis", falhas)
            page.click(f"{FIG} button[data-filtro='']")
            page.click(f"{FIG} button[data-alt='sinal']")
        # mapa por UF: abas
        uf = page.locator("#fig-fiscais_mapa_uf")
        uf.scroll_into_view_if_needed()
        page.wait_for_timeout(400)
        abas = page.locator("#fig-fiscais_mapa_uf button[data-alt]")
        checa(abas.count() >= 2, f"mapa por UF com {abas.count()} abas", falhas)
        if abas.count() >= 2:
            k = abas.nth(1).get_attribute("data-alt")
            abas.nth(1).click()
            vis = page.eval_on_selector(
                f"#fig-fiscais_mapa_uf g[data-alt-show='{k}']",
                "g => g.getAttribute('display')",
            )
            checa(vis is None, f"aba {k} mostra a UF", falhas)
            uf.screenshot(path=str(SAIDA / "qa-fig-fiscais_mapa_uf.png"))
        # tabela ordenável
        tab = page.locator("#fig-fiscais_locais table[data-ordena]")
        tab.scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        b = page.locator("#fig-fiscais_locais thead button.ord").nth(5)
        b.click()
        b.click()
        sort = page.eval_on_selector(
            "#fig-fiscais_locais thead th:nth-child(6)",
            "t => t.getAttribute('aria-sort')",
        )
        checa(sort == "descending", "tabela de locais ordena", falhas)
        for nome in (
            "fiscais_criterios",
            "fiscais_por_uf",
            "fiscais_municipios",
            "fiscais_locais",
            "fiscais_secoes_amostra",
            "fiscais_protege_vigia",
            "fiscais_risco",
        ):
            el = page.locator(f"#fig-{nome}")
            if el.count():
                el.scroll_into_view_if_needed()
                page.wait_for_timeout(250)
                el.screenshot(
                    path=str(
                        SAIDA / f"qa-fig-fiscais_{nome.removeprefix('fiscais_')}.png"
                    )
                )
        # 390 px: nenhuma rolagem lateral, mapa com toque
        cel = nav.new_page(
            viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True
        )
        cel.on("pageerror", lambda e: erros.append(str(e)))
        cel.goto(URL + "#fiscais", wait_until="load")
        cel.wait_for_timeout(600)
        cel.evaluate("document.querySelectorAll('details').forEach(d => d.open = true)")
        cel.wait_for_timeout(300)
        larg = cel.evaluate("[document.documentElement.scrollWidth, window.innerWidth]")
        checa(
            larg[0] <= larg[1],
            f"390 px sem rolagem lateral ({larg[0]} de {larg[1]})",
            falhas,
        )
        sec = cel.locator("#fiscais")
        lado = cel.evaluate(
            "() => [...document.querySelectorAll('#fiscais *')].filter(e => e.getBoundingClientRect().right > window.innerWidth + 1"
            " && !e.closest('.table-scroll,.chart-scroll,.fz-mapa')).length"
        )
        checa(
            lado == 0,
            f"nada do capítulo passa da tela fora das áreas roláveis ({lado})",
            falhas,
        )
        m = cel.locator(FIG)
        m.scroll_into_view_if_needed()
        cel.wait_for_timeout(300)
        touch = cel.eval_on_selector(
            f"{FIG} svg.fz-svg", "s => getComputedStyle(s).touchAction"
        )
        checa(touch == "none", "toque fica com o mapa (pinça e arrasto)", falhas)
        m.screenshot(path=str(SAIDA / "qa-fig-fiscais_mapa-390.png"))
        (
            sec.screenshot(path=str(SAIDA / "qa-fig-fiscais_capitulo-390.png"))
            if False
            else None
        )
        nav.close()
    checa(not erros, f"console sem erro ({erros[:3]})", falhas)
    print(f"{len(falhas)} falha(s)")
    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())
