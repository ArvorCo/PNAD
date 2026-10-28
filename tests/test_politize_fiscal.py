"""Camada de fiscalização do Politize e mapa de fiscais em tela cheia."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from politize import fiscal as fz
from politize import fiscal_textos as ft

ROOT = Path(__file__).resolve().parents[1]
DADOS = ROOT / "docs/assets/politize/dados"
FISCAL = DADOS / "fiscal"
MAPA = ROOT / "docs/assets/fiscais_mapa"
DOSSIE_2T = ROOT / "docs/apuracao_2T_2026.html"
TRAVESSAO = "—"
EV = {
    "troca_2013": "8,7",
    "troca_outras": "0,4",
    "ml_k": "8",
    "ml_grupo": "5",
    "ml_universo": "497.796",
    "ml_features": "9",
    "ml_aptos_min": "30",
    "ml_secoes": "10.850",
    "ml_pct": "2,2",
    "ml_bn1": "6,5",
    "ml_bn2": "4,4",
    "ml_bn1_pais": "3,8",
    "ml_bn2_pais": "2,6",
    "ml_aptos": "245",
    "ml_aptos_pais": "317",
}


def _secao(**kw):
    base = {
        "uf": "XX",
        "zona": 1,
        "aptos": 300,
        "comparecimento": 240,
        "ano_nasc": 10,
        "sem_digital": 5,
        "abertura_min": 8 * 60.0,
        "encerramento_min": 17 * 60 + 5.0,
        "tipo_urna": 1,
        "n_cargas": 1,
        "tipo_arquivo": 1,
        "modelo_urna": "UE2020",
        "aptos_tte": 0,
        "abst_a": 20.0,
        "margem_v": 30.0,
        "validos": 220,
        "a60": 20.0,
        "fund_inc": 30.0,
        "perfil_fonte": "secao",
    }
    base.update(kw)
    return base


def _codigos(sinais):
    return [c for c, _ in sinais]


# ---------------------------------------------------------------- regras puras


def test_nivel_cortes():
    assert fz.nivel(0) == "padrao"
    assert fz.nivel(1) == "reforcada"
    assert fz.nivel(fz.CORTES["alta"] - 1) == "reforcada"
    assert fz.nivel(fz.CORTES["alta"]) == "alta"
    assert fz.nivel(fz.CORTES["maxima"]) == "maxima"


def test_z_contra_outras_exclui_a_propria_linha():
    v = np.array([1.0, 2.0, 3.0, 4.0, 100.0])
    z, media = fz.z_contra_outras(v, [["a"] * 5], minimo=3)
    assert media[4] == pytest.approx(2.5)
    assert z[4] == pytest.approx((100 - 2.5) / np.std([1, 2, 3, 4], ddof=1))
    z2, _ = fz.z_contra_outras(v, [["a"] * 5], minimo=8)
    assert all(math.isnan(x) for x in z2)


def test_sinais_secao_limiares():
    linhas = [_secao() for _ in range(12)]
    linhas[0] = _secao(ano_nasc=60)  # 25% liberados pelo ano de nascimento
    linhas[1] = _secao(tipo_urna=3)
    linhas[2] = _secao(abertura_min=8 * 60 + 45.0, encerramento_min=18 * 60 + 20.0)
    linhas[3] = _secao(aptos=420, aptos_tte=25, modelo_urna="UE2013")
    linhas[4] = _secao(margem_v=-3.0, a60=50.0)
    linhas[5] = _secao(a60=50.0, perfil_fonte="zona")
    linhas[6] = _secao(abertura_min=float("nan"), encerramento_min=float("nan"))
    s = fz.sinais_secao(pd.DataFrame(linhas))
    assert "id_ano" in _codigos(s[0])
    assert _codigos(s[1]) == ["urna_troca"]
    assert {"abertura", "fila"} <= set(_codigos(s[2]))
    assert {"grande", "transito", "urna_2013"} <= set(_codigos(s[3]))
    assert {"disputa", "assistido"} <= set(_codigos(s[4]))
    assert "assistido" not in _codigos(s[5])  # perfil da zona não vira sinal da seção
    assert s[6] == []  # exterior: sem hora de Brasília, sem sinal de horário
    assert s[7] == []
    assert "Flávio" not in s[4][0][1] and "Lula à frente" in s[4][0][1]


def test_comparecimento_atipico_contra_a_zona():
    linhas = [_secao(abst_a=20.0 + (i % 3)) for i in range(12)]
    linhas[0] = _secao(abst_a=2.0)
    s = fz.sinais_secao(pd.DataFrame(linhas))
    assert "comparecimento" in _codigos(s[0])
    assert all("comparecimento" not in _codigos(x) for x in s[1:])


def test_pontuar_nao_conta_duas_vezes():
    sec = [["disputa", "x"], ["id_ano", "y"]]
    loc = [["local_c13_alta", "z"], ["disputa", "w"], ["local_grande", "k"]]
    terr = {"nivel": "alto", "pontos": 4, "motivos": []}
    sem_c13 = fz.pontuar(sec, loc, [], None, terr)
    assert sem_c13 == (
        fz.PESOS["disputa"]
        + fz.PESOS["id_ano"]
        + fz.PESOS["local_c13_alta"]
        + fz.PESOS["local_grande"]
        + fz.PESOS["territorio_alto"]
    )
    com_c13 = fz.pontuar(sec, loc, [["zona_atipica", "q"]], "media", terr)
    assert com_c13 == sem_c13 - fz.PESOS["local_c13_alta"] + fz.PESOS["c13_media"] + 1


def test_ml_atipico_vale_um_ponto_e_so_com_linha_na_mistura():
    d = pd.DataFrame(
        [_secao(secao=1), _secao(secao=2), _secao(secao=3), _secao(secao=4)]
    )
    ml = {"XX": {(1, 1): (5, -20.4, 0.005, 1), (1, 2): (2, -9.1, 0.4, 0)}}
    ml["XX"][(1, 4)] = (5, -15.0, 0.08, 1)
    d = fz.colunas_ml(d, ml)
    assert d["ml_anomalo"].tolist() == [1, 0, None, 1]
    assert d["ml_grupo"].tolist() == [5, 2, None, 5]
    s = fz.sinais_secao(d)
    assert _codigos(s[0]) == ["ml_atipico"]
    assert "entre as 1% menos prováveis do país" in s[0][0][1]
    assert s[1] == []  # na mistura, fora do grupo atípico
    assert s[2] == []  # sem linha no arquivo: nem zero nem sinal
    assert _codigos(s[3]) == ["ml_atipico"] and "entre as" not in s[3][0][1]
    assert fz.PESOS["ml_atipico"] == 1
    assert fz.pontuar(s[0], [], [], None, None) == 1
    assert fz.nivel(fz.pontuar(s[0], [], [], None, None)) == "reforcada"
    assert fz.pontuar(s[2], [], [], None, None) == 0
    # Sem as colunas da mistura (versão 1.0), nenhuma seção recebe o critério.
    sem = fz.sinais_secao(pd.DataFrame([_secao(secao=1)]))
    assert sem == [[]]


def test_ml_atipico_texto():
    c = ft.criterios(EV)["ml_atipico"]
    assert c["peso"] == 1 and c["grupo"] == "secao"
    assert c["nome"] == "Grupo atípico nos dois turnos"
    assert "atipicidade estatística não é irregularidade" in c["porque"].lower()
    assert "brancos e nulos" in c["porque"] and "brancos, nulos" in c["conferir"]
    assert "apuracao_2T_2026.html#anomalia" in c["fonte"]
    assert "apuracao_2T_2026.html#anomalia" in c["conferir"]
    assert "grupo 5 de 8" in c["regra"]
    assert not any("{" in v for v in c.values() if isinstance(v, str))
    txt = json.dumps(c, ensure_ascii=False)
    assert TRAVESSAO not in txt and "fraude" not in txt.lower()


@pytest.mark.skipif(not DOSSIE_2T.exists(), reason="dossiê do 2º turno não gerado")
def test_ml_atipico_link_aponta_para_o_capitulo_grupos():
    html = DOSSIE_2T.read_text(encoding="utf-8")
    assert '<section id="anomalia"' in html


def test_territorio_regra_do_capitulo_13():
    mun = {
        "crime_organizado": "mapeamento público",
        "crime_organizado_fontes": "fbsp-x",
        "homicidios_quintil": "5",
        "homicidios_taxa_100mil": "41.2",
        "homicidios_ano": "2024",
        "fronteira": "0",
        "garimpo": "0",
        "sede_lat": "-10.0",
        "sede_lon": "-50.0",
    }
    t = fz.territorio(
        {
            "favela": "0",
            "prisional": "0",
            "terra_indigena": "0",
            "quilombo": "0",
            "fronteira": "0",
            "garimpo": "0",
        },
        mun,
        -10.0,
        -50.0,
    )
    assert t is not None and t["nivel"] == "alto" and t["pontos"] == 4
    sem_fonte = dict(mun, crime_organizado_fontes="", homicidios_quintil="1")
    t2 = fz.territorio(None, sem_fonte, -10.0, -51.0)
    assert t2 is not None and t2["nivel"] == "baixo"
    assert any("sede" in m for m in t2["motivos"])  # 110 km da sede
    assert fz.territorio(None, None) is None


def test_textos_sem_travessao_e_sem_fraude():
    ev = EV
    blocos = [
        ft.criterios(ev),
        ft.NIVEIS,
        ft.CAP13,
        ft.SEMPRE,
        ft.CTA,
        ft.LEGAL,
        ft.ROTULOS,
    ]
    txt = json.dumps(blocos, ensure_ascii=False)
    assert TRAVESSAO not in txt
    assert "fraude" not in txt.lower()
    crit = ft.criterios(ev)
    codigos = {k for k in fz.PESOS if not k.startswith("c13_")}
    assert codigos == set(crit)
    assert ft.CTA["url"] == "https://fiscaisdopl.com.br"


# ---------------------------------------------------------------- arquivos publicados


@pytest.mark.skipif(
    not (FISCAL / "regras.json").exists(), reason="camada fiscal não gerada"
)
def test_regras_publicadas_coerentes():
    r = json.loads((FISCAL / "regras.json").read_text(encoding="utf-8"))
    total = r["resumo"]["secoes"]
    assert sum(r["niveis"][k]["secoes"] for k in fz.NIVEIS) == total
    assert sum(sum(v.values()) for v in r["resumo"]["por_uf"].values()) == total
    assert r["cta"]["url"] == "https://fiscaisdopl.com.br"
    assert r["pesos"] == fz.PESOS
    assert TRAVESSAO not in json.dumps(r, ensure_ascii=False)
    # Versão 1.1 (27/10/2026): grupo atípico da mistura dos dois turnos, 1 ponto.
    assert r["versao"] == "1.1"
    assert (
        "1.1 (27/10/2026): critério ml_atipico, 1 ponto, decisão editorial"
        in r["historico"]
    )
    assert r["criterios"]["ml_atipico"]["peso"] == 1
    fontes = {f["chave"]: f for f in r["fontes"]}
    assert fontes["anomalia_ml"]["sha256"] and fontes["anomalia_ml"]["gerado_em"]
    a = r["anomalia_ml"]
    assert a["secoes_com_criterio"] == r["criterios"]["ml_atipico"]["secoes"]
    assert a["secoes_com_linha"] + a["secoes_sem_linha"] == total
    # O critério só sobe nível: refazer as transições a partir do "sem" dá o publicado.
    refeito = dict(a["niveis_sem_criterio"])
    for t in a["transicoes"]:
        assert fz.NIVEIS.index(t["para"]) == fz.NIVEIS.index(t["de"]) - 1
        refeito[t["de"]] -= t["secoes"]
        refeito[t["para"]] += t["secoes"]
    assert refeito == {k: r["niveis"][k]["secoes"] for k in fz.NIVEIS}
    assert a["mudaram_de_nivel"] == sum(t["secoes"] for t in a["transicoes"])


@pytest.mark.skipif(
    not (FISCAL / "regras.json").exists(), reason="camada fiscal não gerada"
)
def test_um_arquivo_por_zona_e_pontos_coerentes():
    indice = json.loads((DADOS / "indice.json").read_text(encoding="utf-8"))
    for uf, zonas in indice["zonas"].items():
        for z in zonas:
            assert (FISCAL / uf / f"{int(z)}.json").exists(), f"{uf}/{z}"
    o = json.loads((FISCAL / "AC/4.json").read_text(encoding="utf-8"))
    assert o["versao"] == "1.1"
    cols = o["secoes"]["colunas"]
    for ln in o["secoes"]["linhas"]:
        x = dict(zip(cols, ln, strict=True))
        loc = o["locais"][x["local_id"]]
        c13 = x["c13"][0] if x["c13"] else None
        pts = fz.pontuar(
            x["sinais"], loc["sinais"], o["sinais_zona"], c13, loc["territorio"]
        )
        assert pts == x["pontos"]
        assert fz.nivel(pts) == x["nivel"]


# ---------------------------------------------------------------- mapa de fiscais


@pytest.mark.skipif(
    not (MAPA / "dados.json").exists(), reason="mapa de fiscais não gerado"
)
def test_mapa_dados_cobrem_o_capitulo_13():
    d = json.loads((MAPA / "dados.json").read_text(encoding="utf-8"))
    assert d["formato"] == 2
    locais = [dict(zip(d["colunas_locais"], ln, strict=True)) for ln in d["locais"]]
    secoes = []
    for ln in d["secoes"]:
        r = dict(zip(d["colunas_secoes"], ln, strict=True))
        r["local"] = locais[r["li"]]
        secoes.append(r)
    antigas = [r for r in secoes if r["nivel"] not in ("logs", "mudanca")]
    fis = ROOT / "analysis/apuracao_2026/dados/fiscais.json"
    if fis.exists():
        f = json.loads(fis.read_text(encoding="utf-8"))
        assert len(antigas) == len(f["secoes"])
        fonte = {(s["uf"], int(s["zona"]), int(s["secao"])): s for s in f["secoes"]}
        for r in antigas:
            s = fonte[(r["local"]["uf"], r["local"]["zona"], r["secao"])]
            assert r["nivel"] == s["nivel"]
            assert r["pontuacao"] == s["pontuacao"]
    # Nome de município vem do cadastro: nunca duas grafias para o mesmo código.
    nomes = {}
    for loc in locais:
        nomes.setdefault((loc["uf"], loc["mun"]), set()).add(loc["municipio"])
    assert all(len(v) == 1 for v in nomes.values())
    for loc in locais:
        if loc["lat"] is None:
            assert loc["lon"] is None
            continue
        if loc["uf"] != "ZZ":
            assert -34 <= loc["lat"] <= 5.5 and -74.5 <= loc["lon"] <= -28.5
    sem = sum(1 for r in secoes if r["local"]["lat"] is None)
    assert d["resumo"]["sem_coordenada"] == sem
    # Toda seção de log tem nível de atenção; seção pequena não mostra voto.
    for r in secoes:
        if r["logs"]:
            assert r["atencao"] in (0, 1, 2, 3)
        else:
            assert r["atencao"] is None
        if r["aptos"] is not None and r["aptos"] < 30:
            assert r["flavio_pct"] is None and r["lula_pct"] is None
    # Diagnósticos sem nenhuma seção ficam declarados, fora do seletor.
    for k in d["logs"]["sem_ocorrencia"]:
        assert d["logs"]["criterios"][k]["secoes"] == 0
        assert not any(k in r["logs"] for r in secoes)


def test_pagina_do_mapa_contrato():
    html = (ROOT / "docs/fiscais_mapa.html").read_text(encoding="utf-8")
    js = (MAPA / "app.js").read_text(encoding="utf-8")
    assert TRAVESSAO not in html and TRAVESSAO not in js
    for src in re.findall(r'<script[^>]+src="(https://[^"]+)"', html):
        assert "cdnjs.cloudflare.com" in src or "googletagmanager.com" in src
    assert html.count('integrity="sha384-') == 4
    assert "const RAIOS = [1, 2, 5, 10, 15, 20, 30, 50];" in js
    assert "const RAIO_PADRAO = 10;" in js
    assert "location.reload()" not in js
    assert "cep=" not in js.split("function gravarHash")[1].split("function lerHash")[0]
    # Jargão fica no comentário do código e no rodapé do método, nunca em texto da interface.
    interface = "\n".join(
        ln for ln in js.splitlines() if not ln.strip().startswith("//")
    )
    for termo in ("Vincenty", "WGS84", "escalas robustas", "cômputos"):
        assert termo not in interface
    assert "fiscaisdopl.com.br" in html
    assert 'og:image" content="https://brasil.arvor.co/img/og/fiscais_mapa.png"' in html


def test_politize_liga_fiscal():
    html = (ROOT / "docs/politizesuavizinhanca.html").read_text(encoding="utf-8")
    js = (ROOT / "docs/assets/politize/fiscal.js").read_text(encoding="utf-8")
    app = (ROOT / "docs/assets/politize/app.js").read_text(encoding="utf-8")
    assert 'id="fiscalize"' in html and "https://fiscaisdopl.com.br" in html
    assert re.search(
        r"import \{ blocoFiscal, resumoFiscal \} from '\./fiscal\.js(?:\?[^']+)?';", app
    )
    assert TRAVESSAO not in js
