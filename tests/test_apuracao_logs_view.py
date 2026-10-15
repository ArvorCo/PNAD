"""Publicação visual: critérios visíveis, taxas raras e atualização sem duplicação."""

import json
from pathlib import Path

from apuracao_logs import painel, view

ROOT = Path(__file__).resolve().parents[1]


def indice():
    return json.loads((ROOT / "docs/assets/logs_urnas_2026/indice.json").read_text())


def test_escala_comum_nao_arredonda_ocorrencia_rara_para_zero():
    d = indice()
    assert painel.teto_percentual(d) >= max(
        100 * r["secoes"] / r["avaliaveis"] for r in d["criterios"].values()
    )
    html = painel.catalogo(d)
    raro = html.split('id="texto_malformado"', 1)[1].split("</article>", 1)[0]
    assert "0,0004%" in raro
    assert html.count('class="regra"') == len(d["criterios"])
    assert 'id="tempo_rapido"' in html  # zero observado continua publicado
    for k in d["criterios"]:
        assert f"&amp;log={k}" in html


def test_publicar_move_criterios_para_abertura_e_e_idempotente(tmp_path, monkeypatch):
    docs = tmp_path / "docs"
    docs.mkdir()
    principal = docs / "apuracao_1o_turno_2026.html"
    principal.write_text(
        '<section id="anterior">preservar</section><section id="fiscais">'
        '<div class="section-head"><h2>Fiscais</h2><p class="lead">Antiga</p></div>'
        "<p>Histórico preservado</p>"
        + view.INICIO
        + "bloco antigo"
        + view.FIM
        + '</section><section id="seguinte">preservar também</section>'
    )
    thread = docs / "fiscais_thread.html"
    thread.write_text(
        '<main class="wrap">cards originais</main><footer>fontes</footer>'
    )
    monkeypatch.setattr(view, "ROOT", tmp_path)
    monkeypatch.setattr(view, "PAGINA", docs / "logs_urnas_2026.html")
    d = indice()
    view.atualizar_paginas(d)
    antes = {p.name: p.read_bytes() for p in docs.iterdir()}
    view.atualizar_paginas(d)
    assert antes == {p.name: p.read_bytes() for p in docs.iterdir()}
    html = principal.read_text()
    assert html.count(view.INICIO) == 1
    assert html.index(view.INICIO) < html.index("Histórico preservado")
    assert html.count('class="regra"') == 18
    assert '<section id="anterior">preservar</section>' in html
    assert '<section id="seguinte">preservar também</section>' in html
    assert thread.read_text().index(view.INICIO) < thread.read_text().index(
        "cards originais"
    )
