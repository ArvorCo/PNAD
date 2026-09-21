"""Capítulo do Sudeste no dossiê: âncoras, fitas medidas e regras de escrita."""

import importlib.util
import json
import re
from html import unescape
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs/assets"
PAGINA = ROOT / "docs/datafolha_21092026.html"
JSON_SUDESTE = ASSETS / "datafolha_21092026_sudeste.json"
UFS = ("SP", "RJ", "MG")
ANCORAS = (
    "sudeste-campanha",
    "sudeste-placar",
    "sudeste-transferencia",
    "sudeste-robustez",
    "sudeste-vao",
    "sudeste-senado",
    "sudeste-regua",
    "sudeste-pauta",
    "sudeste-rota",
    "sudeste-contraprova",
    "sudeste-limites",
)

if not (PAGINA.exists() and JSON_SUDESTE.exists()):  # pragma: no cover
    pytest.skip(
        "rode scripts/datafolha-21092026-sudeste.py e o gerador do dossiê antes",
        allow_module_level=True,
    )

HTML = PAGINA.read_text(encoding="utf-8")
D = json.loads(JSON_SUDESTE.read_text(encoding="utf-8"))


def carrega_figuras() -> ModuleType:
    caminho = ROOT / "scripts/datafolha-21092026-sudeste-figuras.py"
    spec = importlib.util.spec_from_file_location("sudeste_figuras", caminho)
    if spec is None or spec.loader is None:
        raise ImportError(f"nao foi possivel carregar {caminho}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


FIG = carrega_figuras()


def svg_do_estado(uf):
    """Recorta o SVG do diagrama daquele estado pelo rótulo acessível."""
    marca = f'aria-label="{uf}: fluxo agregado'
    inicio = HTML.index(marca)
    inicio = HTML.rindex("<svg ", 0, inicio)
    return HTML[inicio : HTML.index("</svg>", inicio)]


def test_secao_presente_e_no_lugar_certo():
    assert 'id="sudeste-campanha"' in HTML
    assert 'href="#sudeste-campanha">02c Campanha</a>' in HTML
    # O capítulo antigo continua funcionando e o novo vem depois dele.
    assert HTML.index('id="sudeste"') < HTML.index('id="governadores"')
    assert HTML.index('id="governadores"') < HTML.index('id="sudeste-campanha"')
    assert HTML.index('id="sudeste-campanha"') < HTML.index('id="documentos"')


def test_todas_as_ancoras_das_subsecoes():
    for ancora in ANCORAS:
        assert f'id="{ancora}"' in HTML, ancora
    # O simulador do capítulo anterior ganhou âncora e é referenciado aqui.
    assert 'id="simulador-es"' in HTML
    assert 'href="#simulador-es"' in HTML


def test_sem_travessao_e_sem_emoji_no_capitulo():
    trecho = HTML[HTML.index('id="sudeste-campanha"') : HTML.index('id="microdados"')]
    assert "—" not in trecho
    # O travessão é proibido; o traço de intervalo numérico continua válido,
    # e só é válido entre dígitos.
    for encontro in re.finditer("–", trecho):
        volta = trecho[encontro.start() - 1 : encontro.start() + 2]
        assert volta[0].isdigit() and volta[2].isdigit(), volta
    # Sem hashtag, emoji ou linguagem de engajamento no texto visível.
    visivel = unescape(re.sub(r"<[^>]+>", " ", trecho))
    assert "#" not in visivel
    assert not re.search(r"[\U0001F300-\U0001FAFF☀-➿]", visivel)


def test_fitas_medidas_batem_com_o_json():
    for uf in UFS:
        variante = D["transferencia"][uf]["gov1_pres2"]["variantes"]["ideologica"]
        medidas_json = sum(
            1
            for c in variante["celulas"]
            if c["estado"] == "medida"
            and variante["matriz_pp"][c["origem"]][c["destino"]] > 0
        )
        svg = svg_do_estado(uf)
        fitas = re.findall(r'<path d="M240[^>]*?fill="([^"]+)"', svg)
        solidas = [f for f in fitas if not f.startswith("url(")]
        hachuradas = [f for f in fitas if f.startswith("url(")]
        assert len(solidas) == medidas_json, (uf, len(solidas), medidas_json)
        assert hachuradas, uf
        assert len(fitas) == len(solidas) + len(hachuradas)


def test_legenda_declara_as_origens_de_cada_tipo():
    for uf in UFS:
        publicadas = len(
            D["transferencia"][uf]["gov1_pres2"]["variantes"]["ideologica"][
                "linhas_medidas"
            ]
        )
        ordem, _, medidas, _ = FIG.celulas_do_diagrama(
            D["transferencia"][uf]["gov1_pres2"]
        )
        assert len(medidas) == publicadas
        svg = svg_do_estado(uf)
        assert f"Fita sólida: {publicadas} origens com linha publicada." in svg
        assert f"Fita hachurada: {len(ordem) - publicadas} origens estimadas." in svg


def test_frechet_da_figura_reproduz_o_json():
    """Fora das origens agrupadas, a faixa desenhada é a do JSON auditado."""
    conferidas = 0
    for uf in UFS:
        variante = D["transferencia"][uf]["gov1_pres2"]["variantes"]["ideologica"]
        publicadas = {(c["origem"], c["destino"]): c for c in variante["celulas"]}
        _, _, _, celulas = FIG.celulas_do_diagrama(D["transferencia"][uf]["gov1_pres2"])
        for celula in celulas:
            chave = (celula["origem"], celula["destino"])
            if chave not in publicadas:
                continue
            alvo = publicadas[chave]
            assert celula["frechet_min_pp"] == pytest.approx(alvo["frechet_min_pp"])
            assert celula["frechet_max_pp"] == pytest.approx(alvo["frechet_max_pp"])
            assert celula["valor_pp"] == pytest.approx(alvo["valor_pp"])
            conferidas += 1
    assert conferidas == 80


def test_massa_de_cada_diagrama_fecha_em_cem():
    for uf in UFS:
        _, _, _, celulas = FIG.celulas_do_diagrama(D["transferencia"][uf]["gov1_pres2"])
        assert sum(c["valor_pp"] for c in celulas) == pytest.approx(100, abs=0.05)


def test_linhas_publicadas_aparecem_na_tabela():
    linhas = sum(len(c["linhas"]) for c in D["cruzamentos_publicados"])
    assert linhas == D["varredura_de_cruzamentos"]["linhas_medidas"]
    assert f"<strong>{linhas} linhas</strong>" in HTML
    for cruzamento in D["cruzamentos_publicados"]:
        assert f'_estaduais.pdf#page={cruzamento["pagina"]}"' in HTML


def test_espirito_santo_fica_fora_da_media():
    trecho = HTML[HTML.index('id="sudeste-campanha"') : HTML.index('id="microdados"')]
    assert "Real Time Big Data" in trecho
    assert "não entra em média" in trecho
    assert "ES-01967/2026" in HTML
    # O ES não pode aparecer na média estadual, que é só dos três do Datafolha.
    media = D["regional_contra_estadual"]["media_estadual"]
    assert set(media["ufs"]) == set(UFS)


def test_rotulo_de_teto_enderecavel_acompanha_o_vao():
    trecho = HTML[HTML.index('id="sudeste-campanha"') : HTML.index('id="microdados"')]
    assert "teto endereçável, não previsão" in trecho
    assert "Ordem de grandeza, não projeção de votos" in trecho
    assert "juízo editorial" in trecho.lower()


def test_figuras_tem_rotulo_acessivel_e_area():
    trecho = HTML[HTML.index('id="sudeste-campanha"') : HTML.index('id="microdados"')]
    svgs = re.findall(r'<svg [^>]*viewBox="0 0 (\d+) (\d+)"[^>]*aria-label="', trecho)
    # Cinco figuras na largura de trabalho, mais a variante estreita do placar.
    assert len(svgs) == 6
    larguras = sorted(int(largura) for largura, _ in svgs)
    assert larguras == [540, 1100, 1100, 1100, 1100, 1100]
    for _, altura in svgs:
        assert int(altura) > 300


def test_placar_tem_variante_para_tela_estreita():
    """Abaixo de 720px o placar empilha e o 2º turno deixa de sair do quadro."""
    trecho = HTML[HTML.index('id="sudeste-campanha"') : HTML.index('id="microdados"')]
    assert trecho.count('<div class="fig-larga">') == 1
    assert trecho.count('<div class="fig-estreita">') == 1
    estreita = trecho[trecho.index('<div class="fig-estreita">') :]
    estreita = estreita[: estreita.index("</div>")]
    assert 'viewBox="0 0 540 ' in estreita
    # As duas colunas viram dois blocos, e o 2º turno de cada estado aparece.
    assert estreita.count(">SEGUNDO TURNO<") == 4
    assert estreita.count(">PRIMEIRO TURNO<") == 4
    # A troca é só de CSS: nenhum script decide qual desenho mostrar.
    css = (ASSETS / "datafolha_21092026.css").read_text(encoding="utf-8")
    assert ".fig-estreita{display:none}" in css
    assert "@media(max-width:719px)" in css
    # As figuras que não empilham avisam que o desenho continua para o lado.
    assert trecho.count('<span class="fig-rolar">') == 4
