#!/usr/bin/env python3
"""Download public PesqEle questionnaire and territory annex for BR-01833/2026."""

import re
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/pesquisas/datafolha/2026-09-11"
ORIGIN = "https://pesqele-divulgacao.tse.jus.br"


def fields(form):
    result = {}
    for tag in form.select("input[name],select[name]"):
        if tag.name == "select":
            option = tag.find("option", selected=True) or tag.find("option")
            result[tag["name"]] = option.get("value", "") if option else ""
        else:
            result[tag["name"]] = tag.get("value", "")
    return result


def main():
    session = requests.Session()
    session.mount(
        "https://",
        HTTPAdapter(
            max_retries=Retry(
                total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504]
            )
        ),
    )
    url = ORIGIN + "/app/pesquisa/listar.xhtml"
    response = session.get(url, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    form = soup.find("form", id="formPesquisa")
    payload = fields(form)
    number = "formPesquisa:j_id_2k"
    payload[number] = "BR018332026"
    source = "formPesquisa:idBtnPesquisar"
    payload.update(
        {
            "javax.faces.partial.ajax": "true",
            "javax.faces.source": source,
            "javax.faces.partial.execute": "@all",
            "javax.faces.partial.render": "formPesquisa",
            source: source,
        }
    )
    response = session.post(
        urljoin(url, form["action"]),
        data=payload,
        headers={"Faces-Request": "partial/ajax"},
        timeout=30,
    )
    response.raise_for_status()
    xml = BeautifulSoup(response.content, "xml")
    fragment = xml.find("update", id="formPesquisa")
    if fragment is None:
        raise RuntimeError(response.text[:500])
    form = BeautifulSoup(fragment.get_text(), "html.parser").find("form")
    payload = fields(form)
    state = xml.find("update", id=re.compile("ViewState"))
    if state:
        payload["javax.faces.ViewState"] = state.get_text()
    link = next(a for a in form.find_all("a") if a.get("id", "").endswith(":detalhar"))
    source = link["id"]
    payload.update(
        {
            "javax.faces.partial.ajax": "true",
            "javax.faces.source": source,
            "javax.faces.partial.execute": "@all",
            source: source,
        }
    )
    response = session.post(
        url, data=payload, headers={"Faces-Request": "partial/ajax"}, timeout=30
    )
    response.raise_for_status()
    xml = BeautifulSoup(response.content, "xml")
    redirect = xml.find("redirect")
    if redirect is None:
        raise RuntimeError(response.text[:500])
    url = urljoin(url, redirect["url"])
    response = session.get(url, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    assert "BR-01833/2026" in soup.get_text()
    (OUT / "registro.txt").write_text(soup.get_text("\n", strip=True))
    form = soup.find("form", id="form")
    for button, name in [
        ("form:arquivoQuestionario", "questionario"),
        ("form:arquivoBairros", "bairros"),
    ]:
        assert form.find(id=button) is not None
        payload = fields(form)
        payload[button] = button
        r = session.post(urljoin(url, form["action"]), data=payload, timeout=60)
        r.raise_for_status()
        if not r.content.startswith(b"%PDF"):
            raise RuntimeError(f'{name}: not PDF {r.headers.get("content-type")}')
        (OUT / f"{name}.pdf").write_bytes(r.content)
        print(name, len(r.content))


if __name__ == "__main__":
    main()
