"""Capítulos `pesquisas` e `noticias` do dossiê do 2º turno (docs/apuracao_2T_2026.html)."""

import json
import re
import shutil
from pathlib import Path

import pytest
from apuracao_2t_2026 import pagina_cap_noticias as CN
from apuracao_2t_2026 import pagina_cap_pesquisas as CP
from apuracao_2t_2026 import pagina_texto_noticias as TN
from apuracao_2t_2026 import pagina_texto_pesquisas as TP
from apuracao_2t_2026.pagina_comum import DADOS, MEMOS, Dados
from apuracao_2026.pagina_comum import Capitulo

ROOT = Path(__file__).resolve().parents[1]
MODULOS = [
    "pagina_cap_pesquisas.py",
    "pagina_cap_noticias.py",
    "pagina_fig_pesquisas.py",
    "pagina_fig_pesquisas_b.py",
    "pagina_fig_noticias.py",
    "pagina_texto_pesquisas.py",
    "pagina_texto_pesquisas_b.py",
    "pagina_texto_noticias.py",
]
PV_ARQ = DADOS / "pesquisas_vs_urna.json"
NT_ARQ = MEMOS / "noticias_noite.json"

precisa_pv = pytest.mark.skipif(
    not PV_ARQ.exists(), reason="pesquisas_vs_urna.json ausente"
)
precisa_nt = pytest.mark.skipif(
    not NT_ARQ.exists(), reason="noticias_noite.json ausente"
)


def cap(ident: str) -> Capitulo:
    return Capitulo(ident, "11", ident, ident, (), None)


def texto_publico(h: str) -> str:
    """HTML sem atributos (URLs ficam fora da regra de escrita)."""
    return re.sub(r"<[^>]+>", " ", h)


def test_modulos_abaixo_de_mil_linhas():
    for nome in MODULOS:
        linhas = (ROOT / "scripts/apuracao_2t_2026" / nome).read_text(encoding="utf-8")
        assert linhas.count("\n") < 1000, nome


@precisa_pv
def test_pesquisas_renderiza_com_numeros_do_json():
    d = Dados(pasta=DADOS)
    h = CP.render(d, cap("pesquisas"))
    PV = json.loads(PV_ARQ.read_text(encoding="utf-8"))
    f = TP.fatos(PV, d.get("projecao_pre_urna.json"), d.get("pesquisas_estaduais.json"))
    assert f["positivos"] == f["n"] and f["negativos"] == 0
    assert (
        abs(f["ancora_pub"] + f["camada_pnad"] + f["camada_presenca"] - f["projecao"])
        < 1e-9
    )
    for k in ("erro", "projecao", "media_arvor", "rep_rep", "t1_erro", "e2022"):
        assert TP.s2(f[k]) in h, k
    for casa in PV["resumo"]["casas_que_acertaram_vencedor"]:
        assert casa in h
    for fig in (
        "p2t_casas_urna",
        "p2t_erro_casas",
        "p2t_tres_eleicoes",
        "p2t_mapa_erro_uf",
    ):
        assert f'id="fig-{fig}"' in h
    assert "Juízo editorial" in h and "pesquisas-hipotese" in h
    # tese editorial de 26/10 (TESE.md): sem confissão, com o que falta explicar
    assert "O que mudou entre sábado e domingo" in h
    assert 'id="pesquisas-falta"' in h and 'id="pesquisas-candidatos"' in h
    for saiu in (
        "errou junto",
        "daqui para frente",
        "nós erramos",
        "Lição, não desculpa",
    ):
        assert saiu not in h
    assert h.index("pesquisas-hipotese") < h.index("p2t_casas_urna")
    pub = texto_publico(h)
    assert "—" not in h
    for proibida in ("fraude", "mentira", "manipula"):
        assert proibida not in pub.lower()
    assert len(h.encode()) < 450_000


@precisa_pv
def test_pesquisas_sem_arquivos_opcionais(tmp_path):
    shutil.copy(PV_ARQ, tmp_path / PV_ARQ.name)
    d = Dados(pasta=tmp_path)
    h = CP.render(d, cap("pesquisas"))
    assert "p2t_casas_urna" in h and "p2t_mapa_erro_uf" not in h
    assert any("projecao_pre_urna" in a for a in d.avisos)


def test_pesquisas_sem_dado_levanta_erro_de_dado(tmp_path):
    with pytest.raises(KeyError):
        CP.render(Dados(pasta=tmp_path), cap("pesquisas"))


def test_tweet_lido_do_memorando():
    tw = TP.tweet()
    if not tw["texto"]:
        pytest.skip("hipotese_autor.md ausente")
    assert tw["texto"][-1].endswith("não saberemos.")
    assert tw["data"] == "25/10/2026" and tw["hora"] == "21:41"


@precisa_nt
def test_noticias_renderiza_tudo_do_json():
    d = Dados(pasta=DADOS)
    h = CN.render(d, cap("noticias"))
    N = json.loads(NT_ARQ.read_text(encoding="utf-8"))
    corpo = h[h.index('id="noticias-tabela"') :]
    assert corpo.count("<tr data-g=") == len(N["itens"])
    for i in N["itens"]:
        assert i["url"].replace("&", "&amp;") in h
    assert 'id="fig-p2t_noticias_linha"' in h
    assert "—" not in h
    assert "fraude" not in texto_publico(h).lower()
    for item in N["nao_encontrado"]:
        assert TN.limpa(item)[:40].replace("'", "&#x27;") in h


@precisa_nt
def test_marcos_em_ordem_e_parada():
    N = json.loads(NT_ARQ.read_text(encoding="utf-8"))
    ms = TN.marcos(N)
    assert [m["min"] for m in ms] == sorted(m["min"] for m in ms)
    chaves = {m["chave"] for m in ms}
    assert {"zanin", "aviso", "retomada", "nunes"} <= chaves
    ini, fim = TN.janela_parada(N)
    assert ini < fim


def test_limpa_regra_de_escrita():
    assert "fraude" not in TN.limpa("gritava 'fraude' e falou em fraude").lower()
    assert TN.minuto_texto("suspensa às 17h06") == 17 * 60 + 6
    assert TN.minuto_texto("sem hora") is None
