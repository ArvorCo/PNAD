"""Regressões da varredura visual do dossiê da apuração (qa-visual-relatorio.md).

Cada teste guarda um defeito medido no navegador e corrigido: a espera da figura
adiada com a caixa do gráfico, a ordenação por delegação, siglas e rótulos sem
sobreposição, texto dentro da viewBox, legenda sem lista vazia, versão empilhada
de celular e rolagem que abre no zero do eixo.
"""

import importlib.util
import json
import re
from itertools import combinations
from pathlib import Path

import pytest
from apuracao_2026 import pagina_comum as C
from apuracao_2026.pagina_fig_base import (
    Tips,
    figura_html,
    posiciona_siglas,
    rotulos_com_fio,
)
from apuracao_2026.pagina_figuras import FIGURAS
from apuracao_2026.pagina_interativo import interativo_html

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_SECOES = ROOT / "tests/fixtures/apuracao_2026/secoes_fixture.json"

spec = importlib.util.spec_from_file_location(
    "apuracao_build_qa", ROOT / "scripts/apuracao-2026-build.py"
)
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)

SVG = '<svg class="fig" viewBox="0 0 1100 450"><title>t</title><desc>d</desc><rect/></svg>'


@pytest.fixture(scope="module")
def dados():
    d = C.Dados()
    tudo = {f.stem: d.get(f.name) for f in sorted(C.DADOS.glob("*.json"))}
    agregador = ROOT / "docs/assets/reponderacao_pnad.json"
    tudo["agregador"] = json.loads(agregador.read_text(encoding="utf-8"))
    if not tudo.get("secoes"):
        tudo["secoes"] = json.loads(FIXTURE_SECOES.read_text(encoding="utf-8"))
    return tudo


@pytest.fixture(scope="module")
def pagina(tmp_path_factory):
    saida = tmp_path_factory.mktemp("qa") / "apuracao.html"
    build.construir(C.DADOS, saida)
    return saida.read_text(encoding="utf-8")


def _textos(svg: str) -> list[dict]:
    """Textos de um SVG com posição, tamanho, âncora e conteúdo."""
    out = []
    for m in re.finditer(r"<text ([^>]*)>([^<]*)</text>", svg):
        a = dict(re.findall(r'([a-z-]+)="([^"]*)"', m.group(1)))
        if "transform" in a:
            continue
        out.append(
            {
                "x": float(a["x"]),
                "y": float(a["y"]),
                "size": float(a.get("font-size", 14)),
                "anchor": a.get("text-anchor", "start"),
                "mono": "Mono" in a.get("font-family", ""),
                "s": m.group(2),
            }
        )
    return out


def _caixa(tx: dict) -> tuple[float, float, float, float]:
    """Caixa estimada do texto: largura média por caractere da família usada."""
    w = (0.6 if tx["mono"] else 0.5) * tx["size"] * len(tx["s"])
    x0 = {"start": tx["x"], "middle": tx["x"] - w / 2, "end": tx["x"] - w}[tx["anchor"]]
    return (x0, tx["y"] - 0.75 * tx["size"], x0 + w, tx["y"] + 0.2 * tx["size"])


def _svgs(h: str) -> list[str]:
    return re.findall(r"<svg .*?</svg>", h, re.DOTALL)


# ------------------------------------------------------------------ itens 1 e 24


def test_espera_tem_a_caixa_do_grafico():
    tips = Tips()
    tips.add("<p>ficha</p>")
    h = figura_html(
        "x",
        SVG,
        "legenda",
        tips,
        controles='<div class="fig-ctl">botões</div>',
        apos='<div class="fig-leg">legenda html</div>',
        minw=900,
        adiar=True,
    )
    # controles e legenda HTML ficam fora do bloco cru: já ocupam o lugar certo
    assert h.index('class="fig-ctl"') < h.index("fig-espera") < h.index("<noscript")
    assert h.index("</noscript>") < h.index('class="fig-leg"') < h.index("<figcaption>")
    # a espera usa a mesma classe, a mesma largura mínima e a razão do viewBox
    assert '<div class="chart-scroll fig-espera-c" style="--minw:900px"' in h
    assert 'style="--ar:1100/450"' in h
    cru = re.search(r'<noscript class="fig-src">(.*?)</noscript>', h, re.DOTALL)[1]
    assert cru.startswith(
        '<div class="chart-scroll" tabindex="0" style="--minw:900px">'
    )
    assert "fig-ctl" not in cru and "fig-leg" not in cru


def test_espera_das_adiadas_bate_com_o_grafico(pagina):
    adiadas = re.findall(
        r'<figure class="reveal fig-i fig-adiada" id="fig-([a-z0-9_]+)".*?</figure>',
        pagina,
        re.DOTALL,
    )
    assert len(adiadas) >= 4
    for m in re.finditer(
        r'<figure class="reveal fig-i fig-adiada" id="fig-([a-z0-9_]+)"(.*?)</figure>',
        pagina,
        re.DOTALL,
    ):
        nome, corpo = m.groups()
        espera = re.search(
            r'<div class="(chart-\w+) fig-espera-c"( style="[^"]*")?[^>]*>'
            r'<div class="fig-espera" style="--ar:(\d+)/(\d+)">',
            corpo,
        )
        assert espera, nome
        cru = re.search(
            r'<noscript class="fig-src">(.*?)</noscript>', corpo, re.DOTALL
        )[1]
        graf = re.match(r'<div class="(chart-\w+)" tabindex="0"( style="[^"]*")?', cru)
        assert graf, nome
        assert espera[1] == graf[1], nome
        assert (espera[2] or "") == (graf[2] or ""), nome
        vb = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', cru)
        assert (int(espera[3]), int(espera[4])) == (
            round(float(vb[1])),
            round(float(vb[2])),
        ), nome


def test_ancora_materializa_antes_de_rolar():
    js = interativo_html()
    assert "function prepara_alvo(id)" in js
    assert "compareDocumentPosition(alvo)&4" in js
    assert "addEventListener('load',reancora)" in js
    assert "behavior:'instant'" in js


# ------------------------------------------------------------------ item 2


def test_ordenacao_por_delegacao(pagina):
    js = interativo_html()
    assert "closest('table[data-ordena] thead button.ord')" in js
    assert "table[data-ordena]:not([data-ok])" in js
    # nenhum script executável dentro de figura: só as fichas em JSON
    for fig in re.findall(r"<figure.*?</figure>", pagina, re.DOTALL):
        for tag in re.findall(r"<script[^>]*>", fig):
            assert 'type="application/json"' in tag, tag
    assert pagina.count("data-ordena") >= 2


# ------------------------------------------------------------------ itens 3, 4, 5 e 25


@pytest.mark.parametrize("nome", ["placar_candidatos", "regioes_2022_2026"])
def test_versao_empilhada_no_celular(dados, nome):
    h = FIGURAS[nome](dados)
    assert 'class="fig-larga"' in h and 'class="fig-estreita"' in h
    estreita = h.split('class="fig-estreita"', 1)[1]
    assert 'viewBox="0 0 360 ' in estreita
    assert "chart-scroll" not in h


@pytest.mark.parametrize(
    "nome",
    [
        "capitais_interior",
        "comparecimento_regioes",
        "lentidao_ufs_2022_2026",
        "estoque_uf",
        "vao_estadual",
        "senado_vao_candidatos",
        "pesquisas_erro",
        "central_casa_ufs",
    ],
)
def test_rolagem_abre_no_zero(dados, nome):
    h = FIGURAS[nome](dados)
    m = re.search(r'data-foco="(-?\d+) (-?\d+)(?: (-?\d+))?"', h)
    assert m, nome
    vb = float(re.search(r'viewBox="0 0 ([\d.]+)', h)[1])
    a, b = float(m[1]), float(m[2])
    assert a < b <= vb + 60


def test_pista_de_rolagem():
    js = interativo_html()
    # sombra por dentro da borda, sob o conteúdo: não esmaece texto nenhum
    assert ".chart-scroll.mais-d{box-shadow:inset" in js and "mask-image" not in js
    # a pista fica fora do gráfico, acima dele, e a espera adiada recebe a mesma
    assert "c.parentNode.insertBefore(dica,c)" in js
    assert "classList.contains('fig-espera-c')" in js
    assert "role para o lado" in js


# ------------------------------------------------------------------ item 6


def test_siglas_da_reserva_sem_sobreposicao(dados):
    h = FIGURAS["reserva_vs_urna"](dados)
    caixas = [
        tuple(float(v) for v in m)
        for m in re.findall(
            r'<rect x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)" fill="[^"]+" rx="2"',
            h,
        )
    ]
    pontos = [
        (float(x), float(y))
        for x, y in re.findall(r'<circle cx="([\d.]+)" cy="([\d.]+)" r="7"', h)
    ]
    assert len(caixas) >= 20 and len(caixas) == len(pontos)
    for a, b in combinations(caixas, 2):
        assert not (
            a[0] < b[0] + b[2] - 0.5
            and b[0] < a[0] + a[2] - 0.5
            and a[1] < b[1] + b[3] - 0.5
            and b[1] < a[1] + a[3] - 0.5
        ), (a, b)
    for px, py in pontos:
        for c in caixas:
            dentro = c[0] + 1 < px < c[0] + c[2] - 1 and c[1] + 1 < py < c[1] + c[3] - 1
            assert not dentro, (px, py, c)


def test_posiciona_siglas_em_aglomerado():
    pts = [(100 + 3 * i, 100 + 2 * (i % 3), f"U{i}") for i in range(8)]
    caixas = posiciona_siglas(pts, (0, 0, 400, 300))
    for a, b in combinations(caixas, 2):
        assert not (
            a[0] < b[0] + b[2]
            and b[0] < a[0] + a[2]
            and a[1] < b[1] + b[3]
            and b[1] < a[1] + a[3]
        )


def test_rotulos_com_fio_saem_da_bolha():
    svg = rotulos_com_fio(
        [(200, 200, 30, "São Paulo", "#d9775f"), (240, 210, 12, "Campinas")],
        (0, 0, 600, 400),
    )
    assert svg.count("<line") == 2
    rects = [
        tuple(float(v) for v in m)
        for m in re.findall(
            r'<rect x="([\d.-]+)" y="([\d.-]+)" width="([\d.]+)" height="([\d.]+)"', svg
        )
    ]
    for x, y, w, h in rects:
        nx, ny = min(max(200, x), x + w), min(max(200, y), y + h)
        assert (nx - 200) ** 2 + (ny - 200) ** 2 >= 30**2
    assert 'fill="#d9775f"' in svg


# ------------------------------------------------------------------ itens 28, 29, 12 e 36


@pytest.mark.parametrize(
    "nome",
    [
        "senado_vao_candidatos",
        "hemiciclo_camara",
        "senado_segundas_vagas",
        "placar_candidatos",
        "noite_regioes_lotes",
    ],
)
def test_texto_dentro_da_viewbox(dados, nome):
    h = FIGURAS[nome](dados)
    for svg in _svgs(h):
        vw, vh = (
            float(v)
            for v in re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg).groups()
        )
        for tx in _textos(svg):
            x0, y0, x1, y1 = _caixa(tx)
            assert x0 >= -2 and x1 <= vw + 2 and y0 >= -2 and y1 <= vh + 2, (nome, tx)


def test_nomes_do_senado_depois_dos_valores(dados):
    h = FIGURAS["senado_segundas_vagas"](dados)
    textos = _textos(h)
    valores = [_caixa(x)[2] for x in textos if re.fullmatch(r"\d+,\d\d", x["s"])]
    nomes = [x["x"] for x in textos if " × " in x["s"]]
    assert valores and nomes and max(valores) < min(nomes)


# ------------------------------------------------------------------ itens 7, 31 e 33


def test_legenda_sem_lista_vazia(pagina):
    for cap in re.findall(r"<figcaption>(.*?)</figcaption>", pagina, re.DOTALL):
        assert not re.search(r"\(\s*\)|faltam \)|faltam ,", cap), cap[:120]


@pytest.mark.parametrize(
    "nome", ["acumulado_noite", "lotes_noite", "noite_regioes_lotes"]
)
def test_eixo_da_noite_cortado_as_22h(dados, nome):
    h = FIGURAS[nome](dados)
    assert "Eixo cortado às 22h" in h
    rotulos = re.findall(r">(\d\dh)</text>", h)
    assert "22h" in rotulos and "23h" not in rotulos and "00h" not in rotulos


def test_barra_100_comeca_no_zero(dados):
    h = FIGURAS["transferencia_cenarios"](dados)
    assert ">0%</text>" in h and ">100%</text>" in h and ">40%</text>" not in h
