#!/usr/bin/env python3
"""Gera o dossiê no layout Quaest de agosto, com SVGs e texto estáticos."""

import importlib.util
import json
import sys
from html import escape
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
D = json.loads((DOCS / "assets/quaest_140926_data.json").read_text())
AGG = json.loads((DOCS / "assets/reponderacao_pnad.json").read_text())


def module(name):
    s = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


def num(v, digits=2):
    return f"{v:.{digits}f}".replace(".", ",")


def ref(*pages):
    return (
        '<p class="source">Quaest, 14/09: '
        + ", ".join(f'<a href="{D["meta"]["pdf"]}#page={p}">p.{p}</a>' for p in pages)
        + ".</p>"
    )


def oldref(*pages):
    return (
        '<p class="source">Quaest, 07/09: '
        + ", ".join(
            f'<a href="{D["meta"]["old_pdf"]}#page={p}">p.{p}</a>' for p in pages
        )
        + ".</p>"
    )


def questionref(*pages):
    return (
        '<p class="source">Instrumento registrado BR-03607/2026: '
        + ", ".join(
            f'<a href="fontes/quaest_140926/2026-09-14_questionario.pdf#page={p}">p.{p}</a>'
            for p in pages
        )
        + ".</p>"
    )


def table(headers, rows):
    head = "".join(f'<th scope="col">{h}</th>' for h in headers)
    body = "".join(
        "<tr>"
        + "".join(
            f'<th scope="row">{v}</th>' if i == 0 else f"<td>{v}</td>"
            for i, v in enumerate(row)
        )
        + "</tr>"
        for row in rows
    )
    return (
        '<div class="table-scroll" tabindex="0" role="region" aria-label="Tabela: '
        + escape(str(headers[0]))
        + '"><table><thead><tr>'
        + head
        + "</tr></thead><tbody>"
        + body
        + "</tbody></table></div>"
    )


def cards(rows):
    return (
        '<div class="verdict-grid">'
        + "".join(
            f'<article class="card"><span class="stamp">{stamp}</span><strong class="metric">{value}</strong><h3>{title}</h3><p>{body}</p></article>'
            for stamp, value, title, body in rows
        )
        + "</div>"
    )


def figure(svg, caption):
    return (
        f'<figure class="chart-shell" tabindex="0">{svg}<figcaption>{caption}</figcaption></figure>'
    )


NAV = {
    "veredito": "Veredito",
    "renda": "Renda",
    "metodo-renda": "Método de renda",
    "historico": "Histórico",
    "transferencia": "Transferência",
    "voto-util": "Voto útil",
    "adesao": "Adesão",
    "substitutos": "Substitutos",
    "blocos": "Blocos",
    "governo": "Governo",
    "agenda": "Agenda",
    "stf": "STF",
    "perguntas-fantasma": "Perguntas fantasma",
    "instrumento": "Instrumento",
    "territorio": "Território",
    "incerteza": "Incerteza",
    "agregados": "Agregados",
    "diagnostico": "Diagnóstico",
    "cobranca": "Cobrança",
    "fontes": "Fontes",
}
SECTIONS = []


def section(slug, title, lead, body, kind=""):
    SECTIONS.append((slug, title.split("<")[0].strip()))
    return f'<section id="{slug}" class="chapter {kind}"><div class="wrap"><div class="chapter-head"><p class="sec-no">{len(SECTIONS):02d} · {NAV[slug]}</p><div><h2>{title}</h2><p class="lead">{lead}</p></div></div><div class="chapter-content">{body}</div></div></section>'


def aggregate_table():
    rows = []
    for turno, entry in AGG["agregador"]["ultimo"].items():
        for key, label in [
            ("kernel", "Média temporal (meia-vida 14 dias)"),
            ("media_simples", "Última onda por instituto"),
        ]:
            z = entry[key]
            rows.append(
                [
                    turno.upper(),
                    label,
                    len(entry["institutos"]),
                    num(z["publicado"]["lula"]),
                    num(z["publicado"]["flavio"]),
                    num(z["ajustado"]["lula"]),
                    num(z["ajustado"]["flavio"]),
                ]
            )
    return table(
        [
            "Turno",
            "Agregado",
            "Institutos elegíveis",
            "L pub.",
            "F pub.",
            "L PNAD",
            "F PNAD",
        ],
        rows,
    )


def sources():
    gallery_pages = {
        16: "Primeiro turno",
        22: "Renda no primeiro turno",
        27: "Transferência medida",
        28: "Série de segundo turno",
        33: "Renda no segundo turno",
        75: "Potencial e rejeição",
        85: "Voto definitivo",
        94: "Convicção por candidato",
        106: "Melhor resultado",
        115: "Melhor resultado × primeiro turno",
        116: "Melhor resultado × segundo turno",
        144: "Exposição ao horário eleitoral",
        154: "Aprovação",
        159: "Aprovação por renda",
        174: "Preocupação",
        194: "Identificação política",
        199: "Perfil de renda",
    }
    gallery = (
        '<div class="source-gallery">'
        + "".join(
            f'<figure><a href="img/quaest_140926/p{p}.webp"><img loading="lazy" src="img/quaest_140926/p{p}.webp" width="1400" height="788" alt="Página {p} do relatório Quaest: {label}"></a><figcaption>p.{p} · {label}</figcaption></figure>'
            for p, label in gallery_pages.items()
        )
        + "</div>"
    )
    for p in gallery_pages:
        target = DOCS / f"img/quaest_140926/p{p}.webp"
        if not target.exists():
            import fitz
            from PIL import Image

            target.parent.mkdir(exist_ok=True, parents=True)
            doc = fitz.open(ROOT / "data/pesquisas/quaest/2026-09-14/relatorio.pdf")
            page = doc[p - 1]
            pix = page.get_pixmap(
                matrix=fitz.Matrix(1400 / page.rect.width, 1400 / page.rect.width)
            )
            Image.frombytes("RGB", [pix.width, pix.height], pix.samples).save(
                target, quality=88
            )
    return section(
        "fontes",
        "As contas e os documentos <em>ficam abertos.</em>",
        "Campo de 10 a 13/09; divulgação de 14/09; auditoria de 15/09/2026. Valores transcritos visualmente com página identificada e controles de recomposição.",
        '<ol class="sources"><li><a href="'
        + D["meta"]["pdf"]
        + '">Quaest/Globo, relatório de 14/09, 205 páginas</a>.</li><li><a href="'
        + D["meta"]["old_pdf"]
        + '">Quaest/Globo, relatório de 07/09, 221 páginas</a>.</li><li>BR-03607/2026: <a href="fontes/quaest_140926/2026-09-14_questionario.pdf">questionário, 25 páginas</a> e <a href="fontes/quaest_140926/2026-09-14_bairros.pdf">anexo territorial</a>.</li><li>BR-01720/2026: <a href="fontes/quaest_140926/2026-09-07_questionario.pdf">questionário anterior, 22 páginas</a> e <a href="fontes/quaest_140926/2026-09-07_bairros.pdf">anexo territorial anterior</a>.</li><li><a href="https://pesqele-divulgacao.tse.jus.br/app/pesquisa/listar.xhtml">Consulta pública do TSE</a>: buscar os registros acima. Datas, contratantes, valor e plano amostral arquivados na estrutura local de pesquisa.</li><li>Divulgação complementar do g1: <a href="'
        + D["external"]["stf"]
        + '">crise e voto</a>; <a href="'
        + D["external"]["reforms"]
        + '">reformas e confiança</a>.</li><li><a href="assets/quaest_140926_data.json">Dados, cálculos, matriz e inventário JSON</a>; <a href="assets/quaest_140926_territorio.csv">território CSV</a>; <a href="assets/quaest_140926_fontes.json">manifesto de fontes e hashes SHA-256</a>.</li><li><a href="reponderacao_pnad.html#metodo">PNAD: metodologia, fontes IBGE e agregador</a>; <a href="quaest_082026.html">dossiê de agosto, referência de layout</a>.</li></ol>'
        + "<p>Os originais ficam em <code>data/pesquisas/quaest/2026-09-07/</code> e <code>2026-09-14/</code>. As 426 páginas passaram por extração de títulos e OCR para busca; OCR bruto não é tratado como dado validado. As tabelas utilizadas foram conferidas em imagens e gravadas em script com página de origem. Sexo e renda recompõem independentemente os dois placares; a identificação política cobre 98% e não foi usada como partição nacional fechada.</p>"
        + "<details><summary>Ver 17 páginas originais usadas nas contas</summary>"
        + gallery
        + "</details>"
        + "<details><summary>Reprodução técnica</summary><pre><code>python3 scripts/quaest-140926-audit.py\npython3 scripts/reponderacao-pnad.py calcular --hoje 2026-09-15\npython3 scripts/reponderacao-build.py\npython3 scripts/quaest-140926-build.py\npython3 scripts/social-cards.py --only quaest_14092026\npytest -q</code></pre><p>O script de auditoria lê os PDFs arquivados, verifica as duas extrações territoriais, gera a ficha integral de reponderação e valida o Sankey. O módulo de tabelas preserva transcrições e páginas; o inventário mantém os blocos do questionário. O antigo importador parcial do g1 recusa sobrescrever a fonte integral.</p></details>",
    )


def main():
    global SECTIONS
    SECTIONS = []
    b = SimpleNamespace(
        d=D,
        aggregate=AGG,
        table=table,
        ref=ref,
        oldref=oldref,
        questionref=questionref,
        num=num,
        section=section,
        cards=cards,
        figure=figure,
        fig=module("quaest-140926-figures"),
        aggregate_table=aggregate_table,
    )
    body = (
        module("quaest-140926-chapters").chapters(b)
        + module("quaest-140926-chapters-extra").chapters(b)
        + [sources()]
    )
    links = "".join(f'<a href="#{slug}">{NAV[slug]}</a>' for slug, _ in SECTIONS)
    html = (
        """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Quaest 14/09/2026: a renda encurta a vantagem | Arvor</title>
<meta name="description" content="Auditoria completa: Lula 40,66 × Flávio 41,40 na PNAD; quatro origens de transferência medidas; 66 itens registrados; duas ondas, território e limites do avanço de Flávio.">
<meta property="og:type" content="article"><meta property="og:title" content="Quaest: dois pontos viram menos de um com a PNAD"><meta property="og:description" content="Renda, transferência, convicção, perguntas fora do PDF e 334 setores auditados.">
<meta property="og:url" content="https://brasil.arvor.co/quaest_14092026.html"><meta property="og:image" content="https://brasil.arvor.co/img/og/quaest_14092026.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="https://brasil.arvor.co/img/og/quaest_14092026.png"><link rel="canonical" href="https://brasil.arvor.co/quaest_14092026.html">
<link rel="stylesheet" href="assets/quaest_082026.css"><link rel="stylesheet" href="assets/quaest_140926.css"><script defer src="assets/quaest_140926.js"></script></head><body>
<a class="skip" href="#conteudo">Pular para o conteúdo</a>
<header class="hero"><div class="wrap"><div class="brand"><a href="index.html"><img src="img/arvor_logo.png" alt="">Arvor Intelligence · Perícia eleitoral</a><span>14/09/2026 · auditado em 15/09</span></div>
<div class="hero-grid"><div><p class="eyebrow">Quaest / Globo · setembro de 2026</p><h1>Dois pontos.<em>Menos de um com a PNAD.</em></h1><p class="deck">Flávio chega a 42% contra 40% de Lula. Sob a mesma régua de renda usada no acervo, o confronto fica em <strong>41,40% contra 40,66%</strong>. O avanço de Flávio convive com rejeição estável e menor convicção na sua base. Duas ondas completas, transferências medidas, o inventário do questionário e a cobrança que os documentos sustentam.</p>
<div class="hero-stats"><div><b>0,74</b><span>ponto de diferença sob a PNAD, a favor de Flávio</span></div><div><b>4 + 2 + 2</b><span>origens medidas, bases fixadas e resíduos estimados no Sankey</span></div><div><b>66</b><span>itens registrados, com situação documental identificada</span></div></div></div>
<dl class="case-file"><div><dt>Registro TSE</dt><dd>BR-03607/2026</dd></div><div><dt>Campo</dt><dd>10 a 13 de setembro</dd></div><div><dt>Amostra</dt><dd>2.004 entrevistas</dd></div><div><dt>Modo</dt><dd>Presencial domiciliar, 16+</dd></div><div><dt>Contratantes</dt><dd>Globo e Editora Globo</dd></div><div><dt>Valor registrado</dt><dd>R$ 314.628,00</dd></div><div><dt>Território</dt><dd>120 municípios · 334 setores</dd></div><div><dt>Referência de renda declarada</dt><dd>PNAD anual 2025, visita 1</dd></div></dl></div></div></header>
"""
        + f'<nav class="toc" aria-label="Capítulos"><div class="wrap"><b>NO DOSSIÊ</b>{links}</div></nav><main id="conteudo">'
        + "\n".join(body)
        + """</main>
<footer class="report-footer"><div class="wrap"><p><strong>Arvor Intelligence</strong> · Auditoria independente de documentação e sensibilidade estatística.</p><p>Leitura descritiva de pesquisa, não previsão eleitoral. <a href="index.html">Biblioteca</a> · <a href="reponderacao_pnad.html">Agregador PNAD</a> · <a href="#conteudo">Voltar ao início</a></p></div></footer></body></html>"""
    )
    assert "—" not in html
    (DOCS / "quaest_14092026.html").write_text(
        html.replace("<section", "\n<section")
        .replace("<details", "\n<details")
        .replace("<p>", "\n<p>")
        + "\n"
    )
    print("Gerado:", DOCS / "quaest_14092026.html", len(SECTIONS), "capítulos")


if __name__ == "__main__":
    main()
