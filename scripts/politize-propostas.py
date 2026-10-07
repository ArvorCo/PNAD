"""Programa de governo de Flavio Bolsonaro (2026) em citacoes por tema.

Usos:
  python3 scripts/politize-propostas.py                 monta o JSON e verifica
  python3 scripts/politize-propostas.py --verificar     so verifica o JSON existente
  python3 scripts/politize-propostas.py --conferir-tse  baixa o original do TSE e
                                                        compara o SHA-256 com o espelho

A curadoria (analysis/politize/propostas_curadoria.json) guarda, por citacao, so a
pagina e as palavras de abertura e de fecho do trecho. O texto sai do PDF, nunca
digitado: o trecho e o intervalo literal entre as duas ancoras, com os espacos
colapsados, e reticencias so quando o corte cai no meio de uma frase.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import fitz

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "data" / "originals" / "programa_governo_flavio_2026"
PDF = PASTA / "plano-flavio.pdf"
FONTE = PASTA / "fonte.json"
CURADORIA = RAIZ / "analysis" / "politize" / "propostas_curadoria.json"
SAIDA = RAIZ / "docs" / "assets" / "politize" / "propostas.json"

URL_ESPELHO = "https://static.poder360.com.br/uploads/2026/08/plano-flavio.pdf"
URL_TSE_PAGINA = (
    "https://www.tse.jus.br/eleicoes/eleicoes-2026-content/"
    "propostas-de-governo-dos-candidatos-ao-cargo-de-presidente-da-republica-eleicoes-2026"
)
SQ_CANDIDATO = "280002551544"
CD_ELEICAO = "6257"
URL_TSE_API = (
    "https://divulgacandcontas.tse.jus.br/divulga/rest/v1/candidatura/buscar/"
    f"2026/BR/{CD_ELEICAO}/candidato/{SQ_CANDIDATO}"
)
NOTA_ESPELHO = (
    "espelho do PDF registrado no TSE, não conferido contra o original; "
    "comparar o hash quando o TSE voltar a responder"
)
TITULO = "Para o Brasil vencer o atraso: Diretrizes do Plano de Governo 2027-2030"
CANDIDATO = "Flávio Bolsonaro (PL), nº 22"
MIN_CHARS, MAX_CHARS = 120, 450
FIM_DE_FRASE = (".", "!", "?")

TEMAS_OBRIGATORIOS = [
    "Segurança",
    "Saúde",
    "Emprego, salário e trabalho",
    "Custo de vida e comida na mesa",
    "Educação",
    "Economia e impostos",
    "Corrupção e transparência",
    "Infraestrutura e obras",
    "Enchentes, clima e meio ambiente",
    "Moradia e bairro",
    "Aposentados e pessoas idosas",
    "Mulheres",
    "Juventude e infância",
    "Pequenos negócios e quem trabalha por conta",
    "Campo e agronegócio",
    "Liberdade e instituições",
]


def normalizar(texto: str) -> str:
    return re.sub(r"\s+", " ", texto).strip()


def ler_paginas(caminho: Path) -> list[str]:
    with fitz.open(caminho) as doc:
        return [normalizar(p.get_text()) for p in doc]


def sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def registrar_fonte(paginas: list[str]) -> dict:
    baixado = datetime.fromtimestamp(PDF.stat().st_mtime, tz=timezone.utc)
    fonte = {
        "titulo": TITULO,
        "candidato": CANDIDATO,
        "url": URL_ESPELHO,
        "url_tse_pagina": URL_TSE_PAGINA,
        "url_tse_api": URL_TSE_API,
        "sq_candidato": SQ_CANDIDATO,
        "cd_eleicao": CD_ELEICAO,
        "arquivo": PDF.name,
        "bytes": PDF.stat().st_size,
        "sha256": sha256(PDF),
        "paginas": len(paginas),
        "baixado_em": baixado.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ocr": False,
        "metadados_pdf": "criado em 2026-08-18 por PDFium (impressão do original)",
        "espelho": True,
        "conferido_com_tse": False,
        "nota": NOTA_ESPELHO,
    }
    FONTE.write_text(json.dumps(fonte, ensure_ascii=False, indent=2) + "\n")
    return fonte


def extrair(paginas: list[str], c: dict) -> str:
    pag = paginas[c["pagina"] - 1]
    ini = pag.find(c["de"])
    if ini < 0:
        raise SystemExit(f"abertura não achada na p. {c['pagina']}: {c['de']!r}")
    fim = pag.find(c["ate"], ini + len(c["de"]) if c["ate"] != c["de"] else ini)
    if fim < 0:
        raise SystemExit(f"fecho não achado na p. {c['pagina']}: {c['ate']!r}")
    trecho = pag[ini : fim + len(c["ate"])].rstrip(",;: ")
    if not trecho.endswith(FIM_DE_FRASE):
        trecho += "…"
    if trecho[0].islower():
        trecho = "…" + trecho
    return trecho


def montar(paginas: list[str], fonte: dict) -> dict:
    cur = json.loads(CURADORIA.read_text())
    temas = []
    for t in cur["temas"]:
        citacoes = [
            {
                "titulo": c["titulo"],
                "texto": extrair(paginas, c),
                "pagina": c["pagina"],
            }
            for c in t["citacoes"]
        ]
        temas.append(
            {
                "id": t["id"],
                "nome": t["nome"],
                "resumo": t["resumo"],
                "problema_quaest": t["problema_quaest"],
                "citacoes": citacoes,
            }
        )
    presentes = {t["nome"] for t in temas}
    ausentes = [n for n in TEMAS_OBRIGATORIOS if n not in presentes]
    campos = (
        "titulo", "candidato", "url", "url_tse_pagina", "url_tse_api",
        "sha256", "bytes", "paginas", "baixado_em", "ocr", "espelho",
        "conferido_com_tse", "nota",
    )  # fmt: skip
    return {
        "versao": "1.0",
        "fonte": {k: fonte[k] for k in campos},
        "temas": temas,
        "temas_ausentes": ausentes,
    }


def limpar_pontas(texto: str) -> str:
    return texto.removeprefix("…").removesuffix("…").strip()


def verificar(dados: dict, paginas: list[str], fonte: dict) -> list[str]:
    erros: list[str] = []
    if dados["fonte"]["sha256"] != sha256(PDF) or fonte["sha256"] != sha256(PDF):
        erros.append("sha256 do PDF difere do registrado")
    if dados["fonte"]["paginas"] != len(paginas):
        erros.append("número de páginas difere do PDF")
    total = 0
    for t in dados["temas"]:
        n = len(t["citacoes"])
        if not 3 <= n <= 8:
            erros.append(f"{t['id']}: {n} citações (esperado de 3 a 8)")
        for texto in (t["resumo"], *(c["titulo"] for c in t["citacoes"])):
            if "—" in texto:
                erros.append(f"{t['id']}: travessão em texto próprio: {texto!r}")
        for c in t["citacoes"]:
            total += 1
            rot = f"{t['id']} p.{c['pagina']} {c['titulo']!r}"
            if not 4 <= len(c["titulo"].split()) <= 6:
                erros.append(f"{rot}: título deve ter de 4 a 6 palavras")
            corpo = limpar_pontas(c["texto"])
            if not MIN_CHARS <= len(corpo) <= MAX_CHARS:
                erros.append(f"{rot}: {len(corpo)} caracteres fora de 120 a 450")
            if not 1 <= c["pagina"] <= len(paginas):
                erros.append(f"{rot}: página inexistente")
            elif corpo not in paginas[c["pagina"] - 1]:
                erros.append(f"{rot}: trecho não existe literalmente na página")
    print(f"{len(dados['temas'])} temas, {total} citações verificadas")
    return erros


def conferir_tse(fonte: dict) -> int:
    req = urllib.request.Request(
        URL_TSE_API,
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            ficha = json.load(r)
    except urllib.error.HTTPError as e:
        print(
            f"TSE respondeu HTTP {e.code} em {URL_TSE_API}. "
            "O espelho continua sem conferência; tente de novo mais tarde.",
            file=sys.stderr,
        )
        return 2
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        print(f"Falha ao consultar o TSE ({e}). Nada foi comparado.", file=sys.stderr)
        return 2
    alvos = [
        a
        for a in ficha.get("arquivos", [])
        if "propost" in json.dumps(a, ensure_ascii=False).lower()
    ]
    if not alvos:
        print(
            "A resposta do TSE não traz arquivo de proposta em `arquivos`; "
            f"chaves recebidas: {sorted(ficha)}",
            file=sys.stderr,
        )
        return 3
    url = next(
        (v for v in alvos[0].values() if isinstance(v, str) and "http" in v), None
    )
    if url is None:
        print(f"Arquivo de proposta sem URL de download: {alvos[0]}", file=sys.stderr)
        return 3
    destino = PASTA / "original_tse.pdf"
    try:
        urllib.request.urlretrieve(url, destino)
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"Download do original falhou ({e}).", file=sys.stderr)
        return 2
    hash_tse = sha256(destino)
    igual = hash_tse == fonte["sha256"]
    print(f"original TSE {hash_tse} | espelho {fonte['sha256']} | iguais: {igual}")
    fonte.update(conferido_com_tse=igual, sha256_tse=hash_tse, url_tse_download=url)
    if igual:
        fonte["espelho"] = False
        fonte["nota"] = "idêntico ao PDF registrado no TSE (SHA-256 conferido)"
    FONTE.write_text(json.dumps(fonte, ensure_ascii=False, indent=2) + "\n")
    print("fonte.json atualizado; rode o script sem opções para refazer o JSON.")
    return 0 if igual else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--verificar", action="store_true")
    ap.add_argument("--conferir-tse", action="store_true")
    args = ap.parse_args()

    if args.conferir_tse:
        return conferir_tse(json.loads(FONTE.read_text()))

    paginas = ler_paginas(PDF)
    if args.verificar:
        dados = json.loads(SAIDA.read_text())
        fonte = json.loads(FONTE.read_text())
    else:
        if FONTE.exists():
            fonte = json.loads(FONTE.read_text())
        else:
            fonte = registrar_fonte(paginas)
        dados = montar(paginas, fonte)
        SAIDA.parent.mkdir(parents=True, exist_ok=True)
        SAIDA.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n")
        print(f"gravado {SAIDA.relative_to(RAIZ)}")
    erros = verificar(dados, paginas, fonte)
    for e in erros:
        print("ERRO:", e, file=sys.stderr)
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
