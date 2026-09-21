#!/usr/bin/env python3
"""Arquiva os registros PesqEle das últimas ondas do comparativo metodológico."""

import argparse
import hashlib
import json
import re
import shutil
from datetime import date
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/originals/reponderacao_metodologias_20260921"
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


def download(registro, poll_id):
    out = OUT / poll_id
    out.mkdir(parents=True, exist_ok=True)
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
    payload[number] = re.sub(r"[^A-Z0-9]", "", registro)
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
    assert registro in soup.get_text()
    (out / "registro.html").write_text(response.text, encoding="utf-8")
    (out / "registro.txt").write_text(soup.get_text("\n", strip=True), encoding="utf-8")
    provenance = {
        "registro": registro,
        "consulta": date.today().isoformat(),
        "origem": ORIGIN + "/app/pesquisa/listar.xhtml",
        "sha256_html": hashlib.sha256((out / "registro.html").read_bytes()).hexdigest(),
    }
    (out / "proveniencia.json").write_text(json.dumps(provenance, indent=2) + "\n")
    form = soup.find("form", id="form")
    for button, name in [
        ("form:arquivoQuestionario", "questionario"),
    ]:
        if form.find(id=button) is None:
            continue
        payload = fields(form)
        payload[button] = button
        r = session.post(urljoin(url, form["action"]), data=payload, timeout=60)
        r.raise_for_status()
        if not r.content.startswith(b"%PDF"):
            raise RuntimeError(f"{name}: not PDF {r.headers.get('content-type')}")
        (out / f"{name}.pdf").write_bytes(r.content)
        print(name, len(r.content))


def export_sources(manifest):
    """Reproduz excertos públicos, preservando o HTML original apenas no acervo."""
    import fitz

    source = OUT / manifest["id"]
    target = ROOT / "docs/fontes/reponderacao_metodologias" / manifest["id"]
    target.mkdir(parents=True, exist_ok=True)
    content = (source / "registro.txt").read_text()
    start = content.index("Metodologia de pesquisa:")
    end = content.index("Dados relativos aos municípios", start)
    stamp = manifest["proveniencia"]["consulta"]
    header = (
        f"EXCERTO DO REGISTRO PESQELE | {manifest['registro_tse']} | "
        f"Consulta: {date.fromisoformat(stamp).strftime('%d/%m/%Y')}\n"
        f"Origem: {ORIGIN}/app/pesquisa/listar.xhtml\n"
        "Seções integrais de metodologia, plano amostral e controle. O plano descreve "
        "procedimentos declarados, não atesta sua execução.\n\n"
    )
    # Do not silently replace the documentary basis of an already-scored snapshot.
    for filename, expected in [
        ("registro.html", manifest["proveniencia"]["registro_html_sha256"]),
        ("questionario.pdf", manifest["proveniencia"]["questionario_sha256"]),
    ]:
        if hashlib.sha256((source / filename).read_bytes()).hexdigest() != expected:
            raise ValueError(
                f"Fonte mudou: {filename}; revisar manifesto antes de exportar"
            )
    (target / "registro-metodologia.txt").write_text(header + content[start:end])
    shutil.copyfile(source / "questionario.pdf", target / "questionario.pdf")
    if manifest.get("relatorio_excerto"):
        with (
            fitz.open(ROOT / manifest["proveniencia"]["relatorio_original"]) as report,
            fitz.open() as excerpt,
        ):
            for page in manifest["paginas"]:
                excerpt.insert_pdf(report, from_page=page - 1, to_page=page - 1)
            excerpt.save(target / "relatorio-metodologia.pdf")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("poll_ids", nargs="*")
    parser.add_argument(
        "--export-only",
        action="store_true",
        help="Exporta fontes já arquivadas, sem rede.",
    )
    args = parser.parse_args()
    manifests = [
        json.loads(p.read_text())
        for p in (ROOT / "analysis/reponderacao/metodologias").glob("*.json")
    ]
    unknown = set(args.poll_ids) - {p["id"] for p in manifests}
    if unknown:
        parser.error("IDs fora do comparativo: " + ", ".join(sorted(unknown)))
    failed = []
    for poll in manifests:
        if args.poll_ids and poll["id"] not in args.poll_ids:
            continue
        try:
            if args.export_only:
                export_sources(poll)
            else:
                download(poll["registro_tse"], poll["id"])
            print(poll["id"], "OK", flush=True)
        except Exception as exc:
            failed.append(poll["id"])
            print(poll["id"], type(exc).__name__, str(exc), flush=True)
    raise SystemExit(bool(failed))
