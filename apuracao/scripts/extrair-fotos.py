"""Extrai as fotos oficiais das candidaturas de 2026 para public/fotos/{sq}.jpg.

Lê os zips `foto_cand2026_{UF}_div.zip` do TSE em data/raw/tse_candidatos_2026/
fotos/ (o de presidente, `BR`, é baixado se faltar) e reaproveita o recorte
quadrado central de scripts/senado_2026/tse.py. O cargo de cada SQ_CANDIDATO vem
de consulta_cand_2026.zip: 240x240 para presidente, governador e senador
(cargos 1, 3, 5) e 96x96 para deputados (6, 7, 8). Arquivos já gravados não são
refeitos, a menos que se passe --forcar.
"""

from __future__ import annotations

import argparse
import csv
import importlib
import io
import json
import sys
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PNAD = RAIZ.parent
RAW = PNAD / "data" / "raw" / "tse_candidatos_2026"
FOTOS_ZIP = RAW / "fotos"
CONSULTA = RAW / "consulta_cand_2026.zip"
DESTINO = RAIZ / "public" / "fotos"
FIXTURE_PRES = RAIZ / "tests" / "fixtures" / "br-c0001-e006257-u.json"

URLS_BR = (
    "https://cdn.tse.jus.br/estatistica/sead/odsele/foto_cand/foto_cand2026_BR_div.zip",
    "https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes2026/fotos/foto_cand2026_BR_div.zip",
)
LADO = {"1": 240, "3": 240, "5": 240, "6": 96, "7": 96, "8": 96}
UFS = (
    "BR", "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT",
    "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
)  # fmt: skip


def tse_helpers():
    sys.path.insert(0, str(PNAD / "scripts"))
    return importlib.import_module("senado_2026.tse")


def baixar_br() -> str | None:
    """Baixa o zip de presidente se faltar. Devolve a URL usada, ou None."""
    destino = FOTOS_ZIP / "foto_cand2026_BR_div.zip"
    if destino.exists() and zipfile.is_zipfile(destino):
        return None
    FOTOS_ZIP.mkdir(parents=True, exist_ok=True)
    falhas = []
    for url in URLS_BR:
        try:
            urllib.request.urlretrieve(url, destino)
            if not zipfile.is_zipfile(destino):
                raise ValueError("arquivo baixado não é zip")
            return url
        except Exception as erro:
            destino.unlink(missing_ok=True)
            falhas.append(f"{url}: {erro}")
    raise SystemExit("zip de presidente indisponível:\n" + "\n".join(falhas))


def cargos() -> dict[str, str]:
    """SQ_CANDIDATO -> CD_CARGO, lido do CSV nacional do pacote do TSE."""
    saida: dict[str, str] = {}
    with zipfile.ZipFile(CONSULTA) as z:
        nomes = [n for n in z.namelist() if n.endswith(".csv")]
        nacional = [n for n in nomes if n.endswith("_BRASIL.csv")]
        for nome in nacional or nomes:
            with z.open(nome) as f:
                leitor = csv.DictReader(
                    io.TextIOWrapper(f, encoding="latin-1"), delimiter=";"
                )
                for linha in leitor:
                    saida[linha["SQ_CANDIDATO"]] = linha["CD_CARGO"]
    return saida


def extrair(forcar: bool) -> tuple[Counter, Counter, set[str]]:
    from PIL import Image

    tse = tse_helpers()
    cargo_de = cargos()
    DESTINO.mkdir(parents=True, exist_ok=True)
    gravadas: Counter = Counter()
    puladas: Counter = Counter()
    vistas: set[str] = set()
    for uf in UFS:
        caminho = FOTOS_ZIP / f"foto_cand2026_{uf}_div.zip"
        if not caminho.exists():
            print(f"aviso: falta {caminho.name}")
            continue
        with zipfile.ZipFile(caminho) as z:
            for membro in z.namelist():
                sq = tse.sq_do_arquivo(membro)
                cargo = cargo_de.get(sq or "")
                if sq is None or cargo not in LADO:
                    puladas[cargo or "sem_cadastro"] += 1
                    continue
                vistas.add(sq)
                alvo = DESTINO / f"{sq}.jpg"
                if alvo.exists() and not forcar:
                    gravadas[cargo] += 1
                    continue
                with z.open(membro) as f:
                    img = Image.open(io.BytesIO(f.read()))
                    tse.recorte_quadrado(img, LADO[cargo]).save(
                        alvo, "JPEG", quality=tse.QUALIDADE_JPEG, optimize=True
                    )
                gravadas[cargo] += 1
    return gravadas, puladas, vistas


def presidenciais() -> list[tuple[str, str]]:
    dados = json.loads(FIXTURE_PRES.read_text(encoding="utf-8"))
    return [
        (c["sqcand"], c["nmu"])
        for carg in dados["carg"]
        for agr in carg["agr"]
        for par in agr["par"]
        for c in par["cand"]
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--forcar", action="store_true", help="refaz todas as fotos")
    args = parser.parse_args()

    if not CONSULTA.exists():
        raise SystemExit(
            f"falta {CONSULTA}: baixe o pacote do TSE em https://cdn.tse.jus.br/"
            "estatistica/sead/odsele/consulta_cand/consulta_cand_2026.zip para o"
            " repositório PNAD (data/ fica fora do git). Os zips de fotos por UF"
            f" ficam em {FOTOS_ZIP} e vêm de `python3 scripts/senado-2026-tse.py`."
        )
    url = baixar_br()
    print(f"zip BR: {'baixado de ' + url if url else 'já presente'}")
    gravadas, puladas, vistas = extrair(args.forcar)

    for cargo in sorted(gravadas, key=int):
        print(f"cargo {cargo}: {gravadas[cargo]} fotos ({LADO[cargo]} px)")
    print(f"fora do escopo (vices, suplentes, sem cadastro): {sum(puladas.values())}")
    total = sum(p.stat().st_size for p in DESTINO.glob("*.jpg"))
    n = len(list(DESTINO.glob("*.jpg")))
    print(f"total: {n} arquivos, {total / 1e6:.1f} MB em public/fotos/")

    pres = presidenciais()
    faltam = [(sq, nome) for sq, nome in pres if sq not in vistas]
    print(f"presidenciais da fixture com foto: {len(pres) - len(faltam)}/{len(pres)}")
    for sq, nome in faltam:
        print(f"  sem foto: {sq} {nome}")


if __name__ == "__main__":
    main()
