"""Build do dossiê da apuração do 2º turno: esqueleto, capítulos do esqueleto e robustez."""

import importlib.util
import re
from pathlib import Path

import pytest
from apuracao_2t_2026 import pagina_comum as C
from apuracao_2t_2026 import pagina_view as V

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "apuracao_2t_build", ROOT / "scripts/apuracao-2t-2026-build.py"
)
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)

IDS = [c.ident for c in V.capitulos()]
DO_ESQUELETO = [
    "abertura",
    "noite",
    "projecao",
    "boletins",
    "auditoria",
    "video",
    "fontes",
]
TEM_DADOS = (C.DADOS / "presidente.json").exists()


@pytest.fixture(scope="module")
def pagina(tmp_path_factory):
    if not TEM_DADOS:
        pytest.skip("dados do 2º turno ausentes")
    saida = tmp_path_factory.mktemp("pagina") / "apuracao_2t.html"
    _, estado, motivos = build.construir(C.DADOS, saida)
    return saida.read_text(encoding="utf-8"), estado, motivos


def test_registro_dos_vinte():
    assert IDS == [
        "abertura", "noite", "projecao", "boletins", "cedo_tarde", "turnos", "transferencia", "abstencao",
        "secoes", "anomalia", "logs", "exterior", "governadores", "pesquisas", "hipoteses", "paralela", "noticias",
        "auditoria", "video", "fontes",
    ]  # fmt: skip


def test_capitulos_com_id_e_nav(pagina):
    html, estado, _ = pagina
    for ident in IDS:
        assert (
            html.count(f'<section id="{ident}"')
            + html.count(f'<section class="pendente" id="{ident}"')
            == 1
        ), ident
        assert f'href="#{ident}"' in html
    assert set(estado) == set(IDS)


def test_capitulos_do_esqueleto_completos(pagina):
    _, estado, motivos = pagina
    for ident in DO_ESQUELETO:
        assert estado[ident], f"{ident}: {motivos.get(ident)}"


def test_sem_travessao_e_metatags(pagina):
    html = pagina[0]
    assert "—" not in html
    assert html.count("G-ZPYEE8P9YC") >= 1
    assert html.count("googletagmanager.com/gtag/js") == 1
    assert 'content="https://brasil.arvor.co/img/og/apuracao_2T_2026.png"' in html
    assert '<meta property="og:image:width" content="1200">' in html
    assert (
        '<link rel="canonical" href="https://brasil.arvor.co/apuracao_2T_2026.html">'
        in html
    )


def test_audio_sem_autoplay_e_iframes_preguicosos(pagina):
    html = pagina[0]
    audios = re.findall(r"<audio[^>]*>", html)
    assert audios, "nenhum boletim"
    assert all('preload="none"' in a and "autoplay" not in a for a in audios)
    iframes = re.findall(r"<iframe[^>]*>", html)
    assert any("kSELqiCudjU" in i for i in iframes)
    assert all('loading="lazy"' in i for i in iframes)


def test_figuras_do_esqueleto_tem_viewbox(pagina):
    html = pagina[0]
    for nome in ["acumulado_2t", "fatia_2t", "lotes_2t", "regua_1t_2t", "mapa_fechou_2t",
                 "projecao_noite_2t", "mapa_vencedor_2t", "barras_regioes_2t"]:  # fmt: skip
        i = html.find(f'id="fig-{nome}"')
        assert i >= 0, nome
        corpo = html[i : html.find("</figure>", i)]
        assert 'viewBox="0 0 ' in corpo, nome


def test_numeros_da_abertura_saem_do_json(pagina):
    html = pagina[0]
    P = C.Dados(pasta=C.DADOS).get("presidente.json")
    n = P["nacional"]
    assert C.num(n["pct_lula"], 2) in html
    assert C.num(n["pct_flavio"], 2) in html
    assert C.milhoes(n["margem_lula_votos"]) in html


def test_modulo_ausente_vira_pendente():
    cap = C.Capitulo("inexistente_xyz", "99", "Teste", "Teste", (), lambda d: "")
    html, ok, motivo = V.montar(cap, C.Dados(pasta=C.DADOS))
    assert not ok and "ainda não existe" in motivo
    assert 'class="pendente"' in html and 'id="inexistente_xyz"' in html


def test_excecao_no_render_vira_pendente(monkeypatch):
    import types

    mod = types.ModuleType("apuracao_2t_2026.pagina_cap_quebrado")

    def render(d, cap):
        raise RuntimeError("quebrou")

    mod.render = render
    monkeypatch.setitem(__import__("sys").modules, mod.__name__, mod)
    cap = C.Capitulo("quebrado", "98", "Teste", "Teste", (), lambda d: "")
    html, ok, motivo = V.montar(cap, C.Dados(pasta=C.DADOS))
    assert not ok and "RuntimeError" in motivo and "quebrou" in html


def test_envolver_respeita_cabeca_propria():
    cap = C.Capitulo("x", "01", "Curto", "Título", (), lambda d: "")
    proprio = V.envolver(cap, C.cabeca(cap, "Outro") + "<p>a</p>")
    assert proprio.count('class="section-head"') == 1 and "Outro" in proprio
    padrao = V.envolver(cap, "<p>a</p>")
    assert padrao.startswith('<section id="x">') and "Título" in padrao
