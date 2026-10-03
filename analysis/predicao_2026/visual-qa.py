"""QA do simulador e responsividade; requer servidor local na porta 8897."""

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent
URL = "http://127.0.0.1:8897/predicao_2026_1T_presidente.html"


def capture(page, path, selector=None):
    page.evaluate("document.documentElement.style.scrollBehavior='auto'")
    if selector:
        page.locator(selector).scroll_into_view_if_needed()
    else:
        page.evaluate("window.scrollTo(0,0)")
    page.screenshot(path=str(OUT / path))


def run():
    report = {"errors": [], "requests_failed": []}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 1000}, accept_downloads=True
        )
        page = context.new_page()
        page.on("pageerror", lambda e: report["errors"].append(str(e)))
        page.on(
            "response",
            lambda r: (
                report["requests_failed"].append(r.url) if r.status >= 400 else None
            ),
        )
        page.goto(URL, wait_until="networkidle")
        page.evaluate("document.fonts.ready")
        assert page.locator("#sim-label").inner_text().casefold() == "previsão central"
        capture(page, "qa-desktop-hero.png")
        capture(page, "qa-desktop-simulator.png", "#simulador")
        assert page.locator("#param-base").input_value() == "inclusivo"
        table = page.get_by_role("region", name="Ondas nacionais selecionadas").locator("table")
        assert "16,50%" in table.locator("tr", has_text="Vox Brasil").inner_text()
        report["temporal_bases"] = {}
        for anchor in ("sem_recencia", "pnad", "publicado", "todas", "casas"):
            page.locator("#param-base").select_option(anchor)
            report["temporal_bases"][anchor] = page.locator("#sim-gap").inner_text()
        page.locator("#sim-reset").click()
        assert page.locator("#param-base").input_value() == "inclusivo"
        capture(page, "qa-desktop-recency.png", "#metodo")
        page.locator("#uf-useful-flavio").evaluate(
            "el=>{el.closest('details').open=true}"
        )
        page.locator("#uf-select").select_option("SP")
        page.locator("#uf-useful-flavio").fill("100")
        assert "SP" in page.locator("#uf-edits").inner_text()
        local = page.locator("#sim-gap").inner_text()
        page.locator("#uf-select").select_option("BA")
        assert page.locator("#uf-useful-flavio").input_value() == ""
        page.locator("#uf-select").select_option("SP")
        assert page.locator("#uf-useful-flavio").input_value() == "100"
        with page.expect_download() as download:
            page.locator("#sim-export").click()
        path = OUT / "qa-export.json"
        download.value.save_as(path)
        exported = json.loads(path.read_text())
        assert exported["parametros"]["ufs"]["SP"]["voto_flavio"] == 1
        page.locator("#sim-reset").click()
        central = page.locator("#sim-gap").inner_text()
        assert local != central
        assert page.locator("#uf-useful-flavio").input_value() == ""
        page.locator("#param-voto_flavio").fill("100")
        page.locator("#param-voto_flavio").dispatch_event("input")
        page.locator("#sim-montecarlo").click()
        page.wait_for_function(
            "document.getElementById('sim-uncertainty').textContent.startsWith('Faixas condicionais')",
            timeout=60000,
        )
        report["scenario_uncertainty"] = page.locator("#sim-uncertainty").inner_text()
        assert "Faixas condicionais" in report["scenario_uncertainty"]
        page.locator("#param-voto_flavio").fill("50")
        page.locator("#param-voto_flavio").dispatch_event("input")
        assert "ainda não simulados" in page.locator("#sim-uncertainty").inner_text()
        page.locator("#sim-reset").click()
        page.set_viewport_size({"width": 390, "height": 844})
        page.evaluate("document.querySelectorAll('details').forEach(el=>el.open=true)")
        assert page.evaluate("document.documentElement.scrollWidth") == 390
        capture(page, "qa-mobile-hero.png")
        capture(page, "qa-mobile-simulator.png", "#simulador-app")
        capture(page, "qa-mobile-sources.png", "#fontes")
        report["mobile_scroll_width"] = page.evaluate(
            "document.documentElement.scrollWidth"
        )
        nojs = browser.new_context(
            java_script_enabled=False, viewport={"width": 390, "height": 844}
        )
        fallback = nojs.new_page()
        fallback.goto(URL, wait_until="networkidle")
        assert fallback.locator("noscript").is_visible()
        assert fallback.locator("#territorio table tbody tr").count() >= 27
        assert fallback.locator("#previsao").inner_text().find("votos válidos") >= 0
        report["no_javascript"] = "previsão, tabelas, método e aviso disponíveis"
        assert not report["errors"]
        assert not report["requests_failed"]
        browser.close()
    (OUT / "visual-qa.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    run()
