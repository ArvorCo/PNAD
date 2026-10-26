"""Mapa do Brasil do Politize-se: dados do formato 3, regras de exibição e página."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from politize_se import mapa_dados as md
from politize_se import mapa_saida

ROOT = Path(__file__).resolve().parents[1]
SAIDA = ROOT / "docs/assets/politize_se_mapa"
ORIGEM = ROOT / "docs/assets/politize_se/dados"
PAGINA = ROOT / "docs/politizese_mapa.html"
APP = SAIDA / "app.js"
TRAVESSAO = "—"
# Jargão que pode aparecer no comentário do código e no rodapé, nunca na interface.
JARGAO = ("Vincenty", "WGS84", "escore", "fatia", "markercluster", "cluster", "BU")


def _tem(termo: str, texto: str) -> bool:
    return re.search(rf"\b{termo}\b", texto) is not None


def _linhas(t: dict) -> list[dict]:
    return [dict(zip(t["colunas"], x, strict=True)) for x in t["linhas"]]


def _local(**kw) -> dict:
    base = {
        "local_id": "AC-01007-9-1023",
        "nome": "ESCOLA",
        "endereco": "RUA A",
        "bairro": "CENTRO",
        "cep": "69923000",
        "lat": -9.7,
        "lon": -68.1,
        "n_secoes": 2,
        "n_bu2": 2,
        "secao_link": 7,
        "aptos1": 600,
        "aptos2": 600,
        "comp_pct1": 80.0,
        "comp_pct2": 78.0,
        "d_comp_pp": -2.0,
        "abst_pct2": 22.0,
        "bn_pct2": 4.0,
        "fatia_f1_par": 60.0,
        "fatia_f2": 58.0,
        "d_fatia_pp": -2.0,
        "escore_max": 1,
        "secoes_sinal": 1,
        "secoes_mudaram": 0,
        "urnas_trocadas": 0,
    }
    base.update(kw)
    return base


def _como_dict(linha: list) -> dict:
    return dict(zip(md.COLUNAS_LOCAIS, linha, strict=True))


# ------------------------------------------------------------------ regras puras


def test_linha_local_completa():
    r = _como_dict(
        md.linha_local(
            "AC",
            _local(),
            {
                "secoes": [7, 8],
                "modelo": "misto",
                "modelos": [["UE2020", 1], ["UE2015", 1]],
            },
        )
    )
    assert r["id"] == "AC-01007-9-1023" and r["secoes"] == [7, 8]
    assert r["fatia_f2"] == 58.0 and r["aprox"] == 0
    assert r["modelo"] == "misto" and r["modelos"][0] == ["UE2020", 1]
    assert md.zona_de(r["id"]) == 9 and md.mun_de(r["id"]) == "01007"


def test_sem_boletim_do_2o_turno_nao_mostra_variacao():
    r = _como_dict(md.linha_local("AC", _local(n_bu2=0)))
    for c in ("fatia_f2", "d_fatia_pp", "comp_pct2", "d_comp_pp", "abst_pct2"):
        assert r[c] is None
    assert r["secoes"] == [7]  # sem lista da zona, cai na seção do link


def test_predio_pequeno_nao_mostra_voto():
    r = _como_dict(md.linha_local("AC", _local(aptos1=25, aptos2=25)))
    for c in md.CAMPOS_VOTO:
        assert r[c] is None
    assert r["aptos2"] == 25


def test_coordenada_invalida_vira_lista_e_exterior_e_aproximado():
    fora = _como_dict(md.linha_local("AC", _local(lat=48.85, lon=2.35)))
    assert fora["lat"] is None and fora["lon"] is None
    zero = _como_dict(md.linha_local("AC", _local(lat=0, lon=0)))
    assert zero["lat"] is None
    paris = _como_dict(
        md.linha_local("ZZ", _local(local_id="ZZ-29513-1-1015", lat=48.85, lon=2.35))
    )
    assert paris["lat"] == 48.85 and paris["aprox"] == 1


def test_camadas_contrato():
    assert md.CAMADA_PADRAO == "resultado"
    assert set(md.CAMADAS) == {
        "resultado",
        "d_fatia",
        "d_comp",
        "abst",
        "sinal",
        "urna",
        "mudanca",
        "modelo",
        "log2",
        "log_subiu",
    }
    for k, c in md.CAMADAS.items():
        assert c["campo"] in md.COLUNAS_LOCAIS, k
        assert c["tipo"] in ("divergente", "sequencial", "presenca", "categoria")
        texto = " ".join(str(v) for v in c.values())
        assert TRAVESSAO not in texto and "fraude" not in texto.lower()
        for termo in JARGAO:
            assert not _tem(termo, texto), (k, termo)
    assert md.CAMADAS["mudanca"]["precisa_bu2"] is False
    assert "não prova irregularidade" in md.CAMADAS["sinal"]["explica"]


def test_gravar_amostra(tmp_path):
    if not (ORIGEM / "mun/AC").exists():
        pytest.skip("dados do Politize-se ausentes")
    lido = md.ler(ufs={"AC"})
    ind = mapa_saida.gravar(lido, saida=tmp_path)
    assert ind["formato"] == md.FORMATO == 3
    d = json.loads((tmp_path / "uf/AC.json").read_text(encoding="utf-8"))
    assert d["formato"] == 3 and d["locais"]["colunas"] == md.COLUNAS_LOCAIS
    locais = _linhas(d["locais"])
    assert ind["ufs"]["AC"]["locais"] == len(locais) > 0
    assert all(len(r["secoes"]) == r["n_secoes"] for r in locais)
    assert ind["zonas"]["AC"] and (tmp_path / "cep/69.json").exists()


# ------------------------------------------------------------------ dados publicados


@pytest.fixture(scope="module")
def indice() -> dict:
    if not (SAIDA / "indice.json").exists():
        pytest.skip("rode python3 scripts/politize-se-mapa-build.py")
    return json.loads((SAIDA / "indice.json").read_text(encoding="utf-8"))


def test_indice_cobre_todos_os_locais_do_politize_se(indice):
    origem = json.loads((ORIGEM / "indice.json").read_text(encoding="utf-8"))
    n_locais = sum(m["n_locais"] or 0 for m in _linhas(origem["municipios"]))
    r = indice["resumo"]
    assert r["locais"] == n_locais
    assert r["locais"] == r["com_coord"] + r["sem_coord"]
    assert r["secoes"] == origem["cobertura"]["nacional"]["secoes"]
    assert r["secoes_bu2"] == origem["cobertura"]["nacional"]["com_bu_2t"]
    assert indice["fonte_gerado_em"] == origem["gerado_em"]
    assert set(indice["catalogos"]) == {
        "sinais",
        "explicacoes",
        "urna",
        "log",
        "log_familias",
        "log_niveis",
    }


def test_arquivos_por_uf_coerentes(indice):
    for uf, meta in indice["ufs"].items():
        d = json.loads((SAIDA / meta["arquivo"]).read_text(encoding="utf-8"))
        assert d["formato"] == 3 and d["uf"] == uf
        locais = _linhas(d["locais"])
        assert len(locais) == meta["locais"]
        muns = {m["mun"] for m in _linhas(d["municipios"])}
        assert {m[0] for m in meta["municipios"]} == muns
        for r in locais:
            assert r["id"].startswith(uf + "-") and md.mun_de(r["id"]) in muns
            assert len(r["secoes"]) == r["n_secoes"] and r["secao_link"] in r["secoes"]
            if not r["n_bu2"]:
                assert r["fatia_f2"] is None and r["d_fatia_pp"] is None
            if r["lat"] is not None:
                assert md.ponto(uf, r["lat"], r["lon"]) is not None
                assert r["aprox"] == (1 if uf == "ZZ" else 0)


# ------------------------------------------------------------------ página e entradas


def test_pagina_contrato():
    html = PAGINA.read_text(encoding="utf-8")
    js = APP.read_text(encoding="utf-8")
    css = (SAIDA / "app.css").read_text(encoding="utf-8")
    for txt in (html, js, css):
        assert TRAVESSAO not in txt
        assert "fraude" not in txt.lower()
    assert html.count("G-ZPYEE8P9YC") == 2  # uma tag: o script e a configuração
    assert html.count("googletagmanager.com/gtag/js") == 1
    for src in re.findall(r'<script[^>]+src="(https://[^"]+)"', html):
        assert "cdnjs.cloudflare.com" in src or "googletagmanager.com" in src
    assert html.count('integrity="sha384-') == 4
    assert (
        'og:image" content="https://brasil.arvor.co/img/og/politizese_mapa.png"' in html
    )
    assert (
        '<link rel="canonical" href="https://brasil.arvor.co/politizese_mapa.html">'
        in html
    )
    assert "const FORMATO = 3;" in js
    assert "const RAIOS = [1, 2, 5, 10, 15, 20, 30, 50];" in js
    assert "const ZOOM_ROTULOS = 15;" in js
    assert "politizese.html#uf=" in js and "Entenda esta seção no Politize-se" in js
    # O endereço guarda o estado do mapa, nunca o CEP, a localização nem a seção.
    hash_js = js.split("function gravarHash")[1].split("function lerHash")[0]
    assert "cep" not in hash_js and "'s='" not in hash_js and "centro" not in hash_js
    assert "Sinal pede explicação, não prova irregularidade" in html
    assert "O voto é secreto" in html or "o voto é secreto" in html


def test_sem_jargao_na_interface():
    js = APP.read_text(encoding="utf-8")
    interface_js = "\n".join(
        ln for ln in js.splitlines() if not ln.strip().startswith("//")
    )
    # Só os textos entre aspas viram interface; nomes de variáveis ficam fora.
    textos = " ".join(re.findall(r"'([^'\\]*(?:\\.[^'\\]*)*)'", interface_js))
    html = PAGINA.read_text(encoding="utf-8")
    corpo = re.sub(r"<!--.*?-->", "", html.split("<body>")[1], flags=re.DOTALL)
    corpo = re.sub(r"<footer.*?</footer>", "", corpo, flags=re.DOTALL)
    for termo in JARGAO:
        assert not _tem(termo, textos), termo
        assert not _tem(termo, corpo), termo


def test_entradas_para_o_mapa():
    politize = (ROOT / "docs/politizese.html").read_text(encoding="utf-8")
    assert 'href="politizese_mapa.html">Ver no mapa do Brasil</a>' in politize
    app = (ROOT / "docs/assets/politize_se/app.js").read_text(encoding="utf-8")
    assert "Este prédio no mapa" in app and "politizese_mapa.html#uf=" in app
    cap = (ROOT / "scripts/apuracao_2t_2026/pagina_cap_secoes.py").read_text(
        encoding="utf-8"
    )
    assert cap.count('href="politizese_mapa.html"') == 1
    assert "FB.fig_mapa(R) + BOTAO_MAPA" in cap
    home = (ROOT / "docs/index.html").read_text(encoding="utf-8")
    assert home.count('href="politizese_mapa.html"') == 1
    cards = (ROOT / "scripts/social-cards.py").read_text(encoding="utf-8")
    assert '"social-card-politizese-mapa"' in cards


def test_modelo_da_urna_por_secao_e_predio():
    assert (
        md.modelo_secao({"bu2": 1, "modelo1": "UE2015", "modelo2": "UE2022"})
        == "UE2022"
    )
    assert md.modelo_secao({"bu2": 0, "modelo1": "UE2015", "modelo2": None}) == "UE2015"
    assert md.resumo_modelos({}) == (None, [])
    assert md.resumo_modelos({"UE2020": 3}) == ("UE2020", [["UE2020", 3]])
    m, ms = md.resumo_modelos({"UE2015": 1, "UE2022": 4})
    assert m == md.MISTO and ms == [["UE2022", 4], ["UE2015", 1]]
    cat = md.CAMADAS["modelo"]
    assert cat["tipo"] == "categoria" and cat["categorias"][-1] == md.MISTO
    assert all(k in cat["nomes"] for k in cat["categorias"])


def test_contagem_nacional_de_modelos(indice):
    nac = indice["modelos_urna"]["nacional"]
    assert sum(nac["predios"].values()) == indice["resumo"]["locais"]
    assert 0 < sum(nac["secoes"].values()) <= indice["resumo"]["secoes"]
    assert set(nac["secoes"]) <= set(md.MODELOS_URNA)


def test_ficha_da_secao_mostra_modelo_e_veredito_da_urna():
    app = (ROOT / "docs/assets/politize_se/app.js").read_text(encoding="utf-8")
    assert "'Mesma urna nos dois turnos'" in app and "'Urna trocada'" in app
    js = APP.read_text(encoding="utf-8")
    assert "mesma urna nos dois turnos" in js and "'urna trocada'" in js
    assert "'modelo_urna_predominante'" in js


def test_resumo_dos_logs_do_predio():
    secs = [
        {"log1_atencao": 0, "log2_atencao": 2},
        {"log1_atencao": 1, "log2_atencao": 1},
        {"log1_atencao": 3, "log2_atencao": 3},
        {"log1_atencao": None, "log2_atencao": None},
    ]
    assert md.resumo_logs(secs) == {"log1_max": 3, "log2_max": 3, "log_subiu": 1}
    sem = md.resumo_logs([{"log1_atencao": 1, "log2_atencao": None}])
    assert sem == {"log1_max": 1, "log2_max": None, "log_subiu": None}
    nomes = md.CAMADAS["log2"]["nomes"]
    assert [nomes[k] for k in "0123"] == [
        "Registro de rotina",
        "Um sinal no log",
        "Sinais combinados",
        "Conferir o arquivo",
    ]
    assert (
        md.CAMADAS["log2"]["precisa_log2"] and md.CAMADAS["log_subiu"]["precisa_log2"]
    )


def test_lista_e_csv_trazem_o_registro_do_2o_turno():
    js = APP.read_text(encoding="utf-8")
    assert "['log2_max', 'Registro da urna, 2º turno']" in js
    assert "'registro_urna_2t_nivel_max'" in js
    assert "log2: { 0: '#9cb9c2', 1: '#4f8fa0', 2: '#0f5d6e', 3: '#5b2a86' }" in js


def test_amostra_nao_regrava_cep_nem_perde_contagens(tmp_path):
    if not (ORIGEM / "mun/AC").exists():
        pytest.skip("dados do Politize-se ausentes")
    cheio = mapa_saida.gravar(md.ler(ufs={"AC", "RR"}), saida=tmp_path)
    antes = (tmp_path / "cep/69.json").read_bytes()
    amostra = mapa_saida.gravar(md.ler(ufs={"AC"}), saida=tmp_path, mesclar=True)
    assert (tmp_path / "cep/69.json").read_bytes() == antes
    assert amostra["bytes_cep"] == cheio["bytes_cep"]
    assert set(amostra["logs_2t"]["ufs"]) == {"AC", "RR"}
    assert set(amostra["modelos_urna"]["ufs"]) == {"AC", "RR"}
