"""QA de navegador; servidor em 18779, saída em tmp/populacao-eleitorado."""

import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path("tmp/populacao-eleitorado")
BASE = "http://127.0.0.1:18779/"
with sync_playwright() as p:
    b = p.chromium.launch(
        headless=True, executable_path=os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
    )
    page = b.new_page(viewport={"width": 1440, "height": 960}, locale="pt-BR")
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(
        BASE + "politizese_mapa.html#uf=AC&camada=pop_eleitorado",
        wait_until="networkidle",
    )
    page.wait_for_function(
        "window.politizeseMapa?.populacao.layer?.getLayers().length===22",
        timeout=120000,
    )
    for k in [
        "pop_eleitorado",
        "pop_comparecimento1",
        "pop_comparecimento2",
        "pop_mulheres",
        "pop_jovens",
        "pop_idosos",
    ]:
        page.select_option("#camada-seletor", k)
        page.wait_for_function(
            "(k)=>politizeseMapa.estado.camada===k && politizeseMapa.populacao.layer.getLayers().length===22",
            arg=k,
        )
        assert page.evaluate("politizeseMapa.estado.cluster.getLayers().length") == 0
    page.select_option("#camada-seletor", "pop_eleitorado")
    page.wait_for_function("politizeseMapa.populacao.layer.getLayers().length===22")
    assert (
        page.evaluate(
            "new Set(politizeseMapa.populacao.layer.getLayers().map(m=>m.options.popMunicipio)).size"
        )
        == 22
    )
    page.screenshot(path=str(OUT / "mapa-desktop.png"))
    page.evaluate('politizeseMapa.populacao.layer.getLayers()[0].fire("click")')
    page.locator(".leaflet-popup .pop-painel").wait_for()
    page.locator(".leaflet-popup .pop-painel").screenshot(
        path=str(OUT / "municipio-popup.png")
    )
    page.evaluate("politizeseMapa.estado.mapa.closePopup()")
    page.click("#m-lista")
    page.wait_for_selector("#tabela.pop-mapa-lista tbody tr")
    assert page.locator("#tabela tbody tr").count() == 22
    with page.expect_download() as dl:
        page.click("#l-csv")
    dl.value.save_as(OUT / "municipios.csv")
    # Voltar ao prédio, confirmar que população não deixa camada municipal pendurada.
    page.select_option("#camada-seletor", "resultado")
    page.wait_for_function("politizeseMapa.estado.listaAtual.length>0")
    page.click("#m-mapa")
    page.wait_for_function(
        "politizeseMapa.estado.marcadores.size>0 && document.querySelector('#mapa').getAttribute('aria-busy')==='false'"
    )
    page.evaluate(
        """(()=>{const S=politizeseMapa.estado,l=S.locais.find(l=>l.uf==='AC'&&l.n_secoes>2&&l.lat);S.mapa.setView([l.lat,l.lon],17,{animate:false});S.marcadores.get(l.id).openPopup();})()"""
    )
    page.locator(".leaflet-popup .secoes-votos tbody tr").first.wait_for()
    assert page.evaluate("politizeseMapa.populacao.layer.getLayers().length") == 0
    assert page.evaluate(
        "document.querySelector('.leaflet-popup .ficha-secoes').getBoundingClientRect().top < document.querySelector('.leaflet-popup .territorio').getBoundingClientRect().top"
    )
    page.locator(".leaflet-popup .ficha-secoes").screenshot(
        path=str(OUT / "secoes-desktop.png")
    )
    # National coverage: no municipal totals duplicated across schools.
    page.goto(
        BASE + "politizese_mapa.html#camada=pop_eleitorado", wait_until="networkidle"
    )
    page.wait_for_function(
        "window.politizeseMapa?.populacao.layer?.getLayers().length===5571",
        timeout=120000,
    )
    assert (
        page.evaluate(
            "new Set(politizeseMapa.populacao.layer.getLayers().map(m=>m.options.popMunicipio)).size"
        )
        == 5571
    )
    assert page.locator(".placar-chave").is_hidden()
    page.screenshot(path=str(OUT / "mapa-nacional.png"))
    page.select_option("#camada-seletor", "pop_comparecimento2")
    page.wait_for_function("politizeseMapa.populacao.layer.getLayers().length===5571")
    assert (
        page.evaluate(
            "politizeseMapa.populacao.layer.getLayers().filter(m=>m.options.popValor===null).length"
        )
        == 1
    )
    # Municipio and section context in Politize-se.
    page.goto(
        BASE + "politizese.html#uf=AC&mun=01007&visao=municipio",
        wait_until="networkidle",
    )
    page.locator(".pop-painel").wait_for()
    assert "Referência estadual" in page.locator(".pop-painel").inner_text()
    page.locator(".pop-painel").screenshot(path=str(OUT / "politizese-desktop.png"))
    page.goto(BASE + "politizese.html#uf=AC&z=9&s=7", wait_until="networkidle")
    page.locator(".pop-painel").wait_for()
    assert "Bujari" in page.locator(".pop-painel").inner_text()
    # Celular real: load initially at mobile width (separate popup/panel path).
    phone = b.new_page(viewport={"width": 390, "height": 844}, locale="pt-BR")
    phone.on("pageerror", lambda e: errors.append(str(e)))
    phone.goto(
        BASE + "politizese_mapa.html#uf=AC&camada=pop_comparecimento2",
        wait_until="networkidle",
    )
    phone.wait_for_function(
        "window.politizeseMapa?.populacao.layer?.getLayers().length===22"
    )
    phone.evaluate('politizeseMapa.populacao.layer.getLayers()[0].fire("click")')
    phone.locator("#painel .pop-painel").wait_for()
    assert not phone.evaluate("document.documentElement.scrollWidth>innerWidth")
    assert not phone.evaluate(
        "document.querySelector('#painel-corpo').scrollWidth>document.querySelector('#painel-corpo').clientWidth"
    )
    phone.screenshot(path=str(OUT / "mapa-mobile.png"))
    phone.click("#painel-fechar")
    phone.select_option("#camada-seletor", "resultado")
    phone.wait_for_function(
        "politizeseMapa.estado.marcadores.size>0 && document.querySelector('#mapa').getAttribute('aria-busy')==='false'"
    )
    phone.evaluate(
        """(()=>{const S=politizeseMapa.estado,l=S.locais.find(l=>l.uf==='AC'&&l.n_secoes>2&&l.lat);S.mapa.setView([l.lat,l.lon],17,{animate:false});S.marcadores.get(l.id).fire('click');})()"""
    )
    phone.locator("#painel .secoes-votos tbody tr").first.wait_for()
    assert not phone.evaluate(
        "document.querySelector('#painel-corpo').scrollWidth>document.querySelector('#painel-corpo').clientWidth"
    )
    phone.screenshot(path=str(OUT / "secoes-mobile.png"))
    phone.goto(
        BASE + "politizese.html#uf=AC&mun=01007&visao=municipio",
        wait_until="networkidle",
    )
    phone.locator(".pop-painel").wait_for()
    assert not phone.evaluate("document.documentElement.scrollWidth>innerWidth")
    phone.locator(".pop-painel").screenshot(path=str(OUT / "politizese-mobile.png"))
    assert not errors, errors
    (OUT / "qa.json").write_text(
        json.dumps(
            {
                "status": "ok",
                "layers": 6,
                "municipios_nacional": 5571,
                "municipios_ac": 22,
                "errors": errors,
                "mobile_width": 390,
                "screenshots": 8,
            },
            indent=2,
        )
    )
    print("QA OK")
    b.close()
