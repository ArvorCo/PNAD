"""Figuras do catálogo do dossiê da apuração: presença, contrato HTML e fichas."""

import importlib.util
import json
import re
from itertools import pairwise
from pathlib import Path

import pytest
from apuracao_2026 import pagina_comum as C
from apuracao_2026.pagina_fig_base import ADIAR_ACIMA, Tips, figura_html
from apuracao_2026.pagina_figuras import FIGURAS
from apuracao_2026.pagina_interativo import interativo_html

ROOT = Path(__file__).resolve().parents[1]
CATALOGO = ROOT / "analysis/apuracao_2026/CATALOGO_FIGURAS.md"
FIXTURE_SECOES = ROOT / "tests/fixtures/apuracao_2026/secoes_fixture.json"
SECOES = [
    "secoes_90",
    "secoes_excesso",
    "secoes_tamanho_tipo",
    "clusters_secoes",
    "clusters_regiao",
    "modelo_urna_uf",
    "modelo_urna_zona",
    "secoes_outras",
]
NOMES = re.findall(
    r"^\| `([a-z0-9_]+)` \|", CATALOGO.read_text(encoding="utf-8"), re.MULTILINE
)

ABERTURA = r'^<figure class="reveal fig-i( fig-adiada)?" id="fig-{nome}"'

spec = importlib.util.spec_from_file_location(
    "apuracao_build_fig", ROOT / "scripts/apuracao-2026-build.py"
)
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


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
def html(dados):
    return {nome: FIGURAS[nome](dados) for nome in NOMES}


def _tips(h: str) -> dict:
    m = re.search(
        r'<script type="application/json" class="tips">(.*?)</script>', h, re.DOTALL
    )
    assert m, "sem bloco de fichas"
    return json.loads(m.group(1).replace("<\\/", "</"))


def test_catalogo_inteiro_registrado():
    assert len(NOMES) >= 43
    assert len(NOMES) == len(set(NOMES))
    assert set(SECOES) <= set(NOMES)
    assert set(NOMES) <= set(FIGURAS)


@pytest.mark.parametrize("nome", NOMES)
def test_contrato_da_figura(html, nome):
    h = html[nome]
    assert re.match(ABERTURA.format(nome=nome), h)
    assert "pendente" not in h[:80]
    # versão empilhada de celular (`larga_estreita`) é o segundo e último SVG
    assert 1 <= h.count("<svg") <= 1 + h.count('class="fig-estreita"')
    assert "<title>" in h and "<desc>" in h
    assert "<figcaption>" in h
    assert "—" not in h
    _tips(h)


@pytest.mark.parametrize("nome", NOMES)
def test_toda_chave_tem_ficha(html, nome):
    h = html[nome]
    tips = _tips(h)
    linhas = tips.get("_rows", {}).get("linhas", [])
    chaves = re.findall(r'data-k="([^"]+)"', h)
    assert chaves or 'data-near="1"' in h
    for k in chaves:
        if k.startswith("r") and k[1:].isdigit():
            assert int(k[1:]) < len(linhas), k
        else:
            assert k in tips, k
    rows = tips.get("_rows")
    if rows and "xy" in rows:
        assert len(rows["xy"]) == len(rows["linhas"])


ADIADAS_ESPERADAS = (
    "terceira_via_mapa",
    "reguas_divergencia_mapa",
    "nulo_2022_municipios",
    "senado_carregadores_mapa",
)


def _corpo_adiado(h: str) -> str:
    m = re.search(r'<noscript class="fig-src">(.*?)</noscript>', h, re.DOTALL)
    assert m, "figura adiada sem noscript"
    return m.group(1)


@pytest.mark.parametrize("nome", ADIADAS_ESPERADAS)
def test_figura_pesada_sai_adiada(html, nome):
    h = html[nome]
    assert h.startswith(f'<figure class="reveal fig-i fig-adiada" id="fig-{nome}"')
    assert " data-adiada>" in h[:200]
    assert h.count("<noscript") == 1 and h.count("</noscript>") == 1
    corpo = _corpo_adiado(h)
    assert len(corpo.encode("utf-8")) >= ADIAR_ACIMA
    assert "<svg" in corpo and 'class="tips"' in corpo
    # a espera vem antes do bloco cru, com a razão do viewBox; a legenda fica fora
    assert re.search(r'<div class="fig-espera" style="--ar:\d+/\d+"', h)
    assert h.index('class="fig-espera"') < h.index("<noscript")
    assert h.index("</noscript>") < h.index("<figcaption>")


def test_figura_leve_nao_e_adiada(html):
    h = html["placar_candidatos"]
    assert "noscript" not in h and "data-adiada" not in h
    assert len(h.encode("utf-8")) < ADIAR_ACIMA


def test_figura_html_adia_por_tamanho_ou_por_pedido():
    svg = '<svg class="fig" viewBox="0 0 1100 550"><title>t</title><desc>d</desc><rect/></svg>'
    tips = Tips()
    tips.add("<p>ficha</p>")
    leve = figura_html("x", svg, "legenda", tips)
    assert "noscript" not in leve
    forcada = figura_html("x", svg, "legenda", tips, adiar=True)
    assert '<noscript class="fig-src">' in forcada and "--ar:1100/550" in forcada
    assert (
        _corpo_adiado(forcada)
        == leve[
            len('<figure class="reveal fig-i" id="fig-x" data-fig="x" data-dim>') :
        ].split("<figcaption>")[0]
    )
    pesada = figura_html("x", svg + " " * ADIAR_ACIMA, "legenda", tips)
    assert "data-adiada" in pesada
    with pytest.raises(ValueError):
        figura_html("x", svg, "legenda", tips, apos="</noscript>", adiar=True)


def test_dado_ausente_vira_pendente():
    h = FIGURAS["placar_candidatos"]({})
    assert 'class="pendente"' in h and "presidente.json" in h


def test_texto_minimo_13px(html):
    for nome, h in html.items():
        tamanhos = [float(x) for x in re.findall(r'<text[^>]*font-size="([0-9.]+)"', h)]
        assert min(tamanhos, default=13) >= 13, nome


def test_camada_interativa_uma_vez(tmp_path):
    bloco = interativo_html()
    assert bloco.startswith("<style>") and "<script>" in bloco
    saida = tmp_path / "apuracao.html"
    build.construir(C.DADOS, saida)
    pagina = saida.read_text(encoding="utf-8")
    assert pagina.count("function monta(fig)") == 1
    assert pagina.count("function materializa(fig)") == 1
    assert "rootMargin:'1000px 0px 1000px 0px'" in pagina
    assert pagina.count('<figure class="reveal fig-i fig-adiada"') == pagina.count(
        '<noscript class="fig-src">'
    )
    assert pagina.count('<noscript class="fig-src">') >= len(ADIADAS_ESPERADAS)
    assert "—" not in pagina
    tem_secoes = (C.DADOS / "secoes.json").exists()
    for nome in NOMES:
        if nome in SECOES and not tem_secoes:
            continue
        assert f'id="fig-{nome}"' in pagina, nome


# ------------------------------------------------------------------ capítulo 12 por seção


def _fixture() -> dict:
    return json.loads(FIXTURE_SECOES.read_text(encoding="utf-8"))


@pytest.mark.parametrize("nome", SECOES)
def test_secoes_sobre_a_fixture(nome):
    h = FIGURAS[nome]({"secoes": _fixture()})
    assert re.match(ABERTURA.format(nome=nome), h)
    assert h.count("<svg") == 1 and "<title>" in h
    assert "—" not in h
    _tips(h)
    assert "Cobertura parcial: 7 UFs completas" in h
    assert (
        re.search(r'id="[^"]*(chart|map|scatter|legend|readout)"[^>]*>\s*<', h) is None
    )


@pytest.mark.parametrize("nome", SECOES)
def test_secoes_cobertura_completa(nome):
    S = _fixture()
    S["cobertura"]["parcial"] = False
    h = FIGURAS[nome]({"secoes": S})
    assert "Cobertura completa" in h and "parcial" not in h.split("<figcaption>")[1]


def test_secoes_listas_vazias_dizem_que_nao_ha():
    S = _fixture()
    for k in ("tipo_arquivo", "tipo_urna", "cargas"):
        S["outras"][k] = []
    S["outras"]["recebimento"]["por_hora"] = []
    S["outras"]["horarios"]["histograma_encerramento"] = []
    h = FIGURAS["secoes_outras"]({"secoes": S})
    assert h.count("nenhuma seção nesta condição") == 5
    S["urna"]["dentro_local"]["pares"] = []
    h = FIGURAS["modelo_urna_zona"]({"secoes": S})
    assert "nenhuma seção nesta condição" in h


def test_secoes_mapa_agrupa_acima_de_seis_mil():
    S = _fixture()
    base = S["extremos"]["mapa"]["pontos"][0]
    S["extremos"]["mapa"]["pontos"] = [
        [base[0] + (i % 80) * 0.01, base[1] + (i // 80) * 0.01, 1, 0, 2]
        for i in range(6100)
    ]
    h = FIGURAS["secoes_90"]({"secoes": S})
    assert "células de 0,25 grau" in h
    assert len(_tips(h)["_rows"]["linhas"]) < 100


def test_secoes_ausente_vira_pendente():
    h = FIGURAS["secoes_90"]({})
    assert 'class="pendente"' in h and "secoes" in h


def test_clusters_alterna_por_regiao():
    h = FIGURAS["clusters_secoes"]({"secoes": _fixture()})
    assert 'data-as="regiao>' in h and 'data-af="regiao>' in h
    assert 'data-alt="regiao"' in h
    assert h.count("<tr>") >= 21  # cabeçalho e as 20 amostras do grupo mais atípico


def test_clusters_secoes_cores_por_grupo():
    from apuracao_2026.pagina_fig_secoes import CLUSTER_COR, EXTENSO

    fx = _fixture()
    n = len(fx["clusters"]["componentes"])
    h = FIGURAS["clusters_secoes"]({"secoes": fx})
    assert f"{EXTENSO[n].capitalize()} grupos de seções" in h
    assert f"Os {EXTENSO[n]} grupos" in h
    tracos = set(re.findall(r'<path d="[^"]*" stroke="(#[0-9a-f]{6})" data-as=', h))
    assert tracos <= set(CLUSTER_COR)
    assert len(tracos) == n


def test_clusters_regiao_rotulo_curto_e_margem_reservada():
    S = _fixture()
    h = FIGURAS["clusters_regiao"]({"secoes": S})
    svg = h[h.index("<svg") : h.index("</svg>")]
    textos = re.findall(r"<text ([^>]*)>([^<]*)</text>", svg)
    linhas = [(a, s) for a, s in textos if s.startswith("Grupo ")]
    ids = sorted(c["id"] for c in S["clusters"]["componentes"])
    assert [s for _, s in linhas] == [f"Grupo {k + 1}" for k in ids]
    barras = re.findall(
        r'<rect x="([0-9.]+)" y="[0-9.]+" width="[0-9.]+" height="34\.0"', svg
    )
    x0 = min(float(x) for x in barras)
    for attrs, s in linhas:
        x = float(re.search(r'x="([0-9.]+)"', attrs).group(1))
        assert x + 0.6 * 14 * len(s) < x0, s
    # a descrição longa sai do SVG e vai para a ficha e a legenda
    for c in S["clusters"]["componentes"]:
        assert c["rotulo"] not in svg
        assert c["rotulo"] in h.split("</svg>", 1)[1]
    assert 'class="fig-larga"' in h and 'class="fig-estreita"' in h
    estreita = h.split('class="fig-estreita"', 1)[1]
    assert estreita.count('class="clr-g"') == len(ids)
    assert "<svg" not in estreita
    # sem `width` em estilo: escondida na tela larga, não vira área zero no auditor
    assert "width:" not in estreita.split("</style>", 1)[1]


def test_clusters_regiao_texto_cabe_no_segmento():
    h = FIGURAS["clusters_regiao"]({"secoes": _fixture()})
    svg = h[h.index("<svg") : h.index("</svg>")]
    segs = [
        (float(x), float(y), float(w))
        for x, y, w in re.findall(
            r'<rect x="([0-9.]+)" y="([0-9.]+)" width="([0-9.]+)" height="34\.0"', svg
        )
    ]
    achados = re.findall(
        r'<text x="([0-9.]+)" y="([0-9.]+)" font-size="13"[^>]*pointer-events="none">([^<]*)</text>',
        svg,
    )
    assert achados
    for x, y, s in achados:
        xt, yt = float(x), float(y)
        seg = next(
            sg
            for sg in segs
            if abs(sg[0] - (xt - 6)) < 0.2 and abs(sg[1] - (yt - 22)) < 0.2
        )
        assert 6 + 0.6 * 13 * len(s) <= seg[2], s


def test_modelo_urna_zona_sem_registro():
    h = FIGURAS["modelo_urna_zona"]({"secoes": _fixture()})
    assert "Registro" not in h


def test_secoes_outras_horas_continuas_e_eixos():
    S = _fixture()
    h = FIGURAS["secoes_outras"]({"secoes": S})
    svg = h[h.index("<svg") : h.index("</svg>")]
    rec = S["outras"]["recebimento"]["por_hora"]
    if rec:
        # eixo direito da linha de Lula com três valores
        for v in ("0%", "50%", "100%"):
            assert re.search(rf'fill="#b02f21"[^>]*>{v}</text>', svg), v
        # rótulos de hora em passo constante, sem salto escondido
        horas = [
            int(x[:2])
            for x in re.findall(
                r">(\d\dh)</text>", svg[: svg.index("Hora de encerramento")]
            )
        ]
        passos = {(b - a) % 24 for a, b in pairwise(horas)}
        assert len(passos) == 1, horas
    assert " mil</text>" in svg or re.search(r">\d+</text>", svg)


def test_secoes_tamanho_tipo_altura_por_aba_e_margem():
    S = _fixture()
    h = FIGURAS["secoes_tamanho_tipo"]({"secoes": S})
    assert 'preserveAspectRatio="xMidYMin slice"' in h
    E = S["extremos"]
    for aba, n in (
        ("tamanho", len(E["tamanho"]["linhas"])),
        ("tipo", len(E["tipo_local"]["linhas"])),
        ("modelo", len(E["modelo_urna"])),
    ):
        assert (
            f':has(button[data-alt="{aba}"][aria-pressed="true"]) svg.fig'
            f"{{aspect-ratio:1100/{52 + 46 * n + 64}}}"
        ) in h
    svg = h[h.index("<svg") : h.index("</svg>")]
    x0 = min(
        float(x)
        for x in re.findall(
            r'<rect x="([0-9.]+)" y="[0-9.]+" width="[0-9.]+" height="16\.0"', svg
        )
    )
    for s in re.findall(r'<text x="30\.0"[^>]*font-weight="600">([^<]*)</text>', svg):
        assert 30 + 0.6 * 14 * len(s) < x0, s
    legenda = h.split("<figcaption>", 1)[1]
    assert "inferido pelo nome (" not in legenda
    aviso = E["tipo_local"].get("aviso") or ""
    if aviso:
        assert legenda.count(aviso[:40]) == 1


def test_clusters_secoes_elipse_do_proprio_grupo():
    S = _fixture()
    h = FIGURAS["clusters_secoes"]({"secoes": S})
    el = re.search(r"<ellipse [^>]*>", h).group(0)
    assert 'stroke="#5f6773"' in el and 'stroke-dasharray="7 5"' in el
    assert 'fill-opacity="0.06"' in el and "#7d5b00" not in el
    ma = S["clusters"]["mais_anomalo"]["id"]
    assert f"Grupo {ma + 1}, o mais atípico" in h
    # sem `pca.elipses`, a elipse sai da amostra do próprio grupo; com o campo,
    # do centro e da covariância gravados
    S["clusters"]["pca"]["elipses"] = [
        {"cluster": ma, "x": 0.0, "y": 0.0, "cov": [[0.01, 0.0], [0.0, 0.01]]}
    ]
    h2 = FIGURAS["clusters_secoes"]({"secoes": S})
    rx = float(re.search(r'<ellipse [^>]*rx="([0-9.]+)"', h2).group(1))
    assert rx < float(re.search(r'<ellipse [^>]*rx="([0-9.]+)"', h).group(1))


def test_elipse_cov_e_topo():
    from apuracao_2026.pagina_fig_secoes_c import elipse_cov, topo_elipse

    cx, cy, rx, ry, ang = elipse_cov(10, 20, 4.0, 1.0, 0.0)
    assert (rx, ry, ang) == (4.0, 2.0, 0.0)
    assert topo_elipse(cx, cy, rx, ry, ang) == (10, 18.0)
    # girada 90 graus, o topo fica a um semieixo maior acima do centro
    x, y = topo_elipse(0, 0, 4.0, 2.0, 90.0)
    assert abs(x) < 1e-9 and abs(y + 4.0) < 1e-9


@pytest.mark.parametrize("nome", ["voto_por_modelo_nacional", "voto_por_modelo_uf"])
def test_voto_por_modelo_sobre_a_fixture(nome):
    h = FIGURAS[nome]({"secoes": _fixture()})
    assert re.match(ABERTURA.format(nome=nome), h)
    assert h.count("<svg") == 2 and h.count('class="fig-estreita"') == 1
    assert nome in NOMES


def test_voto_por_modelo_nacional_series_e_frase():
    S = _fixture()
    h = FIGURAS["voto_por_modelo_nacional"]({"secoes": S})
    for k in ("cand", "abstencao_pct", "brancos_pct", "nulos_pct"):
        assert f'data-alt="{k}"' in h
        assert f'data-alt-show="{k}"' in h
    assert "Comparação bruta: mistura o modelo com a geografia" in h
    tips = _tips(h)
    n = len(S["urna"]["bruto"])
    # uma ficha por modelo e série (Flávio, Lula, abstenção, brancos, nulos)
    assert len(tips) == 5 * n
    assert "UE2010: Flávio" in json.dumps(tips, ensure_ascii=False)
    assert 'class="fig-estreita"' in h


def test_voto_por_modelo_uf_omite_celulas_pequenas():
    from apuracao_2026.pagina_fig_urna_voto import MINIMO_SECOES, por_uf

    S = _fixture()
    U = S["urna"]
    P = por_uf(U)
    assert len(P) == len({x["uf"] for x in U["voto_por_uf_modelo"]})
    pequenas = [x for x in U["voto_por_uf_modelo"] if x["secoes"] < MINIMO_SECOES]
    assert pequenas
    assert sum(len(o["omitidas"]) for o in P.values()) == len(pequenas)
    h = FIGURAS["voto_por_modelo_uf"]({"secoes": S})
    assert len(_tips(h)) == len(U["voto_por_uf_modelo"]) - len(pequenas)
    assert f"Fora dos painéis: {len(pequenas)} combinações" in h
    assert 'data-alt="flavio"' in h and 'data-alt="lula"' in h
    # um painel por UF em cada versão (larga e empilhada)
    assert h.count('font-weight="700">AC</text>') == 2
    # a parcela da UF soma todas as seções, inclusive as omitidas do painel
    o = P["AC"]
    xs = [x for x in U["voto_por_uf_modelo"] if x["uf"] == "AC"]
    assert o["flavio_pct"] == pytest.approx(
        100 * sum(x["flavio"] for x in xs) / sum(x["validos"] for x in xs)
    )


def test_voto_por_modelo_uf_sem_chave_fica_pendente():
    S = _fixture()
    del S["urna"]["voto_por_uf_modelo"]
    assert 'class="pendente"' in FIGURAS["voto_por_modelo_uf"]({"secoes": S})


def test_texto_voto_por_modelo_sinais_e_frase_responsavel():
    from apuracao_2026 import pagina_texto_c as T

    S = _fixture()
    h = T.urna_voto_nacional(S) + T.urna_voto_uf(S)
    assert "Diferença bruta não é efeito da máquina" in h
    assert "Os extremos vão para os dois lados" in h
    assert "—" not in h
