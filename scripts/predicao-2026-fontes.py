#!/usr/bin/env python3
"""Baixa fontes oficiais ausentes; não usa apuração de 2026."""

import argparse
import json
import shutil
import urllib.request
import zipfile

from predicao_2026.tse import ROOT, URL_LOCALS, URL_PROFILE, URL_RESULTS, sha


def download(url, path, refresh=False):
    if path.exists() and not refresh:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Arvor-PNAD/1.0"})
        print(f"Baixando {path.name}", flush=True)
        with (
            urllib.request.urlopen(request, timeout=120) as response,
            temporary.open("wb") as output,
        ):
            shutil.copyfileobj(response, output, length=1 << 20)
        if path.suffix == ".zip":
            with zipfile.ZipFile(temporary) as archive:
                if not archive.namelist():
                    raise ValueError(f"ZIP vazio: {url}")
        else:
            json.loads(temporary.read_text(encoding="utf-8-sig"))
        temporary.replace(path)
        print(f"SHA256 {sha(path)}", flush=True)
    finally:
        temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Substitui o cache pelas versões oficiais atuais",
    )
    args = parser.parse_args()
    sources = [
        (URL_RESULTS, "data/raw/tse_resultados/detalhe_votacao_secao_2022.zip"),
        (
            URL_RESULTS.replace("2022", "2018"),
            "data/raw/tse_resultados/detalhe_votacao_secao_2018.zip",
        ),
        (URL_PROFILE, "data/raw/tse_eleitorado/perfil_eleitorado_2026.zip"),
        (URL_LOCALS, "data/raw/tse_eleitorado/eleitorado_local_votacao_2026.zip"),
    ]
    for url, relative in sources:
        download(url, ROOT / relative, args.refresh)


if __name__ == "__main__":
    main()
