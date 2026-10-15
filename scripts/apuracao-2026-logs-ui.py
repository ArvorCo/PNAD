#!/usr/bin/env python3
"""Verifica navegação, filtros, exterior, CSV e apresentação móvel dos logs."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
from pathlib import Path
from urllib.parse import urlencode

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
QA = ROOT / "analysis/apuracao_2026/logs_urnas/qa"


def pronto(page):
    page.wait_for_function(
        "/seções|seção sinalizada/.test(document.querySelector('#status').textContent)"
    )
    page.wait_for_load_state("networkidle")


def corrida_filtros(browser, base, mapa, col, erros):
    """Troca de UF durante desenho nacional não pode deixar pontos do recorte antigo."""
    esperado = len(
        {
            r[col["local_id"]]
            for r in mapa["linhas"]
            if r[col["uf"]] == "SP" and r[col["logs"]] and r[col["lat"]] is not None
        }
    )
    p = browser.new_page(viewport={"width": 1300, "height": 900})
    p.set_default_timeout(60_000)
    p.on("pageerror", lambda err: erros.append(str(err)))
    prefixo = """(function(){const original=L.markerClusterGroup;
L.markerClusterGroup=function(opts){window.qaCluster=original(opts);return window.qaCluster;};})();\n"""

    def observar(route):
        resposta = route.fetch()
        route.fulfill(response=resposta, body=prefixo + resposta.text())

    p.route("**/assets/fiscais_mapa/app.js*", observar)
    p.goto(base + "/fiscais_mapa.html#uf=SP&camada=logs", wait_until="networkidle")
    p.wait_for_selector('#mapa[aria-busy="false"]')
    p.locator("#f-uf").select_option("")
    p.wait_for_selector('#mapa[aria-busy="true"]')
    p.locator("#f-uf").select_option("SP")
    p.wait_for_selector('#mapa[aria-busy="false"]')
    p.wait_for_timeout(1200)  # também cobre lotes antigos que chegariam atrasados
    assert p.evaluate("qaCluster.getLayers().length") == esperado
    p.close()
    return esperado


def lista_sem_biblioteca(browser, base, erros):
    p = browser.new_page(viewport={"width": 1300, "height": 900})
    p.on("pageerror", lambda err: erros.append(str(err)))
    p.route("**/leaflet.markercluster.js", lambda rota: rota.abort())
    p.goto(
        base + "/fiscais_mapa.html#ambito=exterior&camada=logs&modo=lista",
        wait_until="networkidle",
    )
    pronto(p)
    assert "biblioteca do mapa não carregou" in p.locator("#mapa").text_content()
    ufs = p.locator("#tabela tbody tr td:nth-child(2)").all_text_contents()
    assert ufs and set(ufs) == {"ZZ"}
    p.close()
    return True


def padroes_e_catalogo(browser, base, mapa, col, erros):
    """Regressão do relato: todas as camadas e exterior, inclusive após limpar."""
    p = browser.new_page(
        viewport={"width": 1400, "height": 1000}, accept_downloads=True
    )
    p.set_default_timeout(60_000)
    p.on("pageerror", lambda err: erros.append(str(err)))
    p.goto(base + "/fiscais_mapa.html", wait_until="networkidle")
    pronto(p)
    assert p.locator("#f-ambito").input_value() == "todos"
    assert p.locator("#f-camada").input_value() == "todas"
    assert p.locator("#f-uf").input_value() == ""
    assert p.locator("#f-log option").count() == 1 + len(mapa["criterios"]) + len(
        mapa["logs"]["criterios"]
    )
    p.locator("#m-lista").click()
    pronto(p)
    total = len(mapa["linhas"])
    exterior = sum(r[col["uf"]] == "ZZ" for r in mapa["linhas"])

    def conferir_total(n, zz):
        alvo = (
            f"{n:,}".replace(",", ".")
            + " seções nos filtros, "
            + f"{zz:,}".replace(",", ".")
            + " no exterior"
        )
        p.wait_for_function(
            "s => document.querySelector('#recorte-ativo').textContent.includes(s)",
            arg=alvo,
        )

    conferir_total(total, exterior)
    with p.expect_download() as download:
        p.locator("#l-csv").click()
    caminho = QA / "todas.csv"
    download.value.save_as(caminho)
    chaves, zz = set(), 0
    with caminho.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter=";"):
            chave = (r["uf"], int(r["zona"]), int(r["secao"]))
            assert chave not in chaves
            chaves.add(chave)
            zz += r["uf"] == "ZZ"
    assert len(chaves) == total and zz == exterior
    caminho.unlink()  # exportação completa validada, sem reter cópia pesada de QA
    p.locator("#f-uf").select_option("ZZ")
    conferir_total(exterior, exterior)
    p.locator("#f-uf").select_option("")
    conferir_total(total, exterior)
    assert p.locator("#f-ambito").input_value() == "todos"
    p.locator("#f-ambito").select_option("brasil")
    conferir_total(total - exterior, 0)
    p.locator("#b-limpar").click()
    conferir_total(total, exterior)
    p.reload(wait_until="networkidle")
    conferir_total(total, exterior)
    for origem, regras in (
        ("historico:", mapa["criterios"]),
        ("", mapa["logs"]["criterios"]),
    ):
        for k, r in regras.items():
            p.locator("#f-log").select_option(origem + k)
            pronto(p)
            assert p.locator("#criterio-ativo strong").inner_text() == r["nome"]
            esperado = str(f'{r["secoes"]:,}'.replace(",", ".")) + " seções nos filtros"
            assert esperado in p.locator("#recorte-ativo").inner_text()
    p.locator("#f-log").select_option("")
    conferir_total(total, exterior)
    p.screenshot(path=str(QA / "mapa-todas-lista.png"))
    p.close()
    return {
        "total_unico_csv": total,
        "exterior_csv": exterior,
        "criterios_conferidos": len(mapa["criterios"]) + len(mapa["logs"]["criterios"]),
    }


def exploracao_relatorio(browser, base, erros):
    p = browser.new_page(viewport={"width": 1300, "height": 900})
    p.on("pageerror", lambda err: erros.append(str(err)))
    p.goto(base + "/logs_urnas_2026.html", wait_until="networkidle")
    assert p.locator(".tempos .tempo").count() == 6
    assert p.locator("figure").count() == 5
    p.locator('.filtros-criterios button[data-grupo="biometria"]').click()
    assert p.locator(".regra:visible").count() == 2
    p.locator("#busca-criterio").fill("sem biometria")
    assert p.locator(".regra:visible").count() == 1
    p.locator("#busca-criterio").fill("zzzzzzz")
    assert p.locator(".sem-resultados").is_visible()
    p.goto(base + "/logs_urnas_2026.html#texto_malformado", wait_until="networkidle")
    assert p.locator("#texto_malformado details").get_attribute("open") is not None
    assert "0,0004%" in p.locator("#texto_malformado").inner_text()
    p.close()
    for largura in (1300, 390):
        p = browser.new_page(viewport={"width": largura, "height": 900})
        p.on("pageerror", lambda err: erros.append(str(err)))
        p.goto(base + "/apuracao_1o_turno_2026.html#fiscais", wait_until="networkidle")
        assert p.locator("#fiscais .logs-fiscais .regra").count() == 25
        assert p.locator("#fiscais .logs-fiscais").evaluate(
            "e => Boolean(e.compareDocumentPosition(document.querySelector('#fiscais-historico')) & Node.DOCUMENT_POSITION_FOLLOWING)"
        )
        assert p.evaluate("document.documentElement.scrollWidth <= innerWidth+1")
        p.locator("#fiscais").scroll_into_view_if_needed()
        p.screenshot(path=str(QA / f"dossie-logs-{largura}.png"))
        p.close()
    contexto = browser.new_context(java_script_enabled=False)
    p = contexto.new_page()
    p.goto(base + "/logs_urnas_2026.html", wait_until="networkidle")
    assert p.locator(".regra:visible").count() == 25
    assert not p.locator(".filtros-criterios").is_visible()
    contexto.close()
    return "gráficos; busca; grupos; âncoras; casos raros; dossiê desktop/móvel; leitura sem JS"


def executar(base: str):
    QA.mkdir(parents=True, exist_ok=True)
    mapa = json.loads((ROOT / "docs/assets/fiscais_mapa/dados.json").read_text())
    col = {k: i for i, k in enumerate(mapa["colunas"])}
    uf_exemplo = next(
        r[col["uf"]] for r in mapa["linhas"] if "tempo_lento" in r[col["logs"]]
    )
    resultados, erros, pedidos = {}, [], []
    with sync_playwright() as play:
        browser = play.chromium.launch(headless=True)
        resultados["todas_e_37_criterios"] = padroes_e_catalogo(
            browser, base, mapa, col, erros
        )
        resultados["relatorio_e_dossie"] = exploracao_relatorio(browser, base, erros)
        page = browser.new_page(
            viewport={"width": 1300, "height": 900}, accept_downloads=True
        )
        page.set_default_timeout(45_000)
        page.on("pageerror", lambda err: erros.append(str(err)))
        page.on("request", lambda req: pedidos.append(req.url))
        page.goto(
            base + "/fiscais_mapa.html#ambito=exterior&camada=todas&modo=lista",
            wait_until="networkidle",
        )
        pronto(page)
        assert page.locator("#f-uf").input_value() == "ZZ"
        assert page.locator("#q-cep").is_disabled()
        ufs = page.locator("#tabela tbody tr td:nth-child(2)").all_text_contents()
        assert ufs and set(ufs) == {"ZZ"}
        assert any("fiscais_mapa/uf/ZZ.json" in p for p in pedidos)
        assert not any("fiscais_mapa/dados.json" in p for p in pedidos)
        with page.expect_download() as download:
            page.locator("#l-csv").click()
        download.value.save_as(QA / "exterior.csv")
        with (QA / "exterior.csv").open(encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f, delimiter=";"))
        assert rows and all(r["uf"] == "ZZ" for r in rows)
        assert "diagnosticos_log" in rows[0] and "coordenada_fonte" in rows[0]
        resultados["exterior_csv"] = len(rows)
        page.locator("#m-mapa").click()
        page.locator("#f-zona").fill("1")
        page.locator("#f-busca button[type=submit]").click()
        pronto(page)
        assert "a até" not in page.locator("#status").inner_text()
        page.screenshot(path=str(QA / "mapa-exterior.png"))
        for check in page.locator(".niveis input").all():
            check.uncheck()
        assert "nivel=" in page.url
        page.reload(wait_until="networkidle")
        pronto(page)
        assert page.locator(".niveis input:checked").count() == 0
        assert "0 locais" in page.locator("#status").inner_text()
        resultados["filtros_vazios_persistem"] = True
        page.locator("#b-limpar").click()
        pronto(page)
        assert page.locator("#f-camada").input_value() == "todas"
        page.locator("#f-uf").select_option(uf_exemplo)
        page.locator("#f-log").select_option("tempo_lento")
        pronto(page)
        assert page.locator("#f-camada").input_value() == "logs"
        assert "log=tempo_lento" in page.url
        page.locator("#m-lista").click()
        pronto(page)
        textos = page.locator("#tabela tbody tr td:nth-child(10)").all_text_contents()
        assert textos and all("Votação mais lenta" in t for t in textos)
        assert any(f"fiscais_mapa/uf/{uf_exemplo}.json" in p for p in pedidos)
        resultados["filtro_diagnostico"] = len(textos)
        page.close()
        resultados["troca_filtro_durante_desenho"] = corrida_filtros(
            browser, base, mapa, col, erros
        )
        resultados["lista_sem_biblioteca_externa"] = lista_sem_biblioteca(
            browser, base, erros
        )

        for largura in (1300, 390):
            p = browser.new_page(viewport={"width": largura, "height": 900})
            p.on("pageerror", lambda err: erros.append(str(err)))
            p.goto(base + "/logs_urnas_2026.html", wait_until="networkidle")
            assert p.locator(".regra").count() == 25
            assert p.locator(".distribuicao img").evaluate_all(
                "imgs => imgs.length === 2 && imgs.every(e => e.complete && e.naturalWidth > 0)"
            )
            assert p.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
            p.screenshot(path=str(QA / f"relatorio-{largura}.png"))
            if largura == 390:
                p.locator(".distribuicao").first.screenshot(
                    path=str(QA / "figura-mobile.png")
                )
                p.get_by_text(
                    "Ver a distribuição dos intervalos entre cômputos", exact=True
                ).click()
                p.locator(".distribuicao").nth(1).screenshot(
                    path=str(QA / "cadencia-mobile.png")
                )
            resultados[f"relatorio_{largura}"] = (
                "sem transbordamento; 25 regras; figura carregada"
            )
            p.close()

        p = browser.new_page(viewport={"width": 390, "height": 844})
        p.set_default_timeout(45_000)
        p.on("pageerror", lambda err: erros.append(str(err)))
        p.goto(base + "/politizesuavizinhanca.html#s=SP-1-1", wait_until="networkidle")
        p.locator(".fis-logs").wait_for()
        assert "256 comparecimentos" in p.locator(".fis-logs").inner_text()
        assert "54 s" in p.locator(".fis-logs").inner_text()
        assert p.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
        p.locator(".fis-logs").screenshot(path=str(QA / "politize-log-mobile.png"))
        resultados["politize_mobile"] = "fixture real: BU 256, mediana 54 s"
        p.goto(
            base + "/politizesuavizinhanca.html#s=SP-273-214", wait_until="networkidle"
        )
        p.locator(".fis-logs").wait_for()
        texto = p.locator(".fis-logs").inner_text()
        for esperado in (
            "275 comparecimentos",
            "73 s",
            "97 s",
            "7 inspeções",
            "9 retomadas",
            "1 cancelamentos",
        ):
            assert esperado in texto, esperado
        p.get_by_text("Horários operacionais registrados", exact=True).click()
        assert "09:09:26" in p.locator(".fis-logs").inner_text()
        assert "10:43:10" in p.locator(".fis-logs").inner_text()
        assert p.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
        p.locator(".fis-logs").screenshot(path=str(QA / "santos-processo-mobile.png"))
        resultados["santos"] = (
            "Processo 73 s; cadência 97 s; inspeções e cancelamento visíveis"
        )
        for chave in ("MG-319-58", "MG-319-240"):
            p.goto(
                base + f"/politizesuavizinhanca.html#s={chave}",
                wait_until="networkidle",
            )
            p.locator(".fis-logs").wait_for()
            assert (
                "classificação histórica e o perfil de conversa desta seção ainda não foram calculados"
                in p.locator("#resultado").inner_text()
            )
            assert "BU foi recuperado" in p.locator(".fis-logs").text_content()
            assert p.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
        resultados["complementos"] = (
            "seções recuperadas com e sem endereço: logs acessíveis, sem perfil inventado"
        )
        # Uma ausência real deve mostrar o motivo específico, sem zero fictício.
        indice = json.loads(
            (ROOT / "docs/assets/logs_urnas_2026/indice.json").read_text()
        )
        ausente = None
        for uf, zonas in indice["zonas"].items():
            for zona in zonas:
                obj = json.loads(
                    gzip.decompress(
                        (
                            ROOT
                            / f"docs/assets/logs_urnas_2026/zona/{uf}/{zona}.json.gz"
                        ).read_bytes()
                    )
                )
                for row in obj.get("indisponiveis", []):
                    if row["motivo"] in (
                        "sem_nome",
                        "nao_instalada",
                        "apuracao_sem_log",
                    ):
                        ausente = (uf, zona, row)
                        break
                if ausente:
                    break
            if ausente:
                break
        if ausente:
            uf, zona, row = ausente
            p.goto(
                base
                + "/politizesuavizinhanca.html#"
                + urlencode({"s": f'{uf}-{zona}-{row["secao"]}'}),
                wait_until="networkidle",
            )
            p.locator(".fis-logs").wait_for()
            assert (
                indice["situacoes"][row["motivo"]]["nome"]
                in p.locator(".fis-logs").inner_text()
            )
            if row.get("logsa"):
                assert p.locator('.fis-logs a[href$="-logsa.jez"]').count() == 1
                assert (
                    "arquivo de outra categoria" in p.locator(".fis-logs").inner_text()
                )
            resultados["ausencia_explicita"] = f'{uf}-{zona}-{row["secao"]}'
        browser.close()
    assert not erros, erros
    (QA / "ui.json").write_text(json.dumps(resultados, ensure_ascii=False, indent=2))
    print(json.dumps(resultados, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://127.0.0.1:4187")
    executar(parser.parse_args().base.rstrip("/"))
