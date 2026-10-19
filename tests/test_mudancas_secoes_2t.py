"""Mudanças de local de votação entre os turnos de 2026: motor do laudo."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from mudancas_secoes_2t import analises as an
from mudancas_secoes_2t import cenarios as ce
from mudancas_secoes_2t import classificacao as cl
from mudancas_secoes_2t import distancia as di
from mudancas_secoes_2t import endereco as en
from mudancas_secoes_2t import estatistica as es
from mudancas_secoes_2t import textos as tx

ROOT = Path(__file__).resolve().parents[1]
MUDANCAS = ROOT / "analysis/mudancas_secoes_2t/mudancas.json"
DADOS = ROOT / "docs/assets/mudancas_secoes/dados.json"
CSV = ROOT / "docs/assets/mudancas_secoes/secoes.csv"
POLITIZE = ROOT / "docs/assets/politize/dados/mudancas"
TRAVESSAO = chr(0x2014)


def _linha(
    local=1015,
    original=1015,
    nome="ESCOLA A",
    endereco="RUA X, 10",
    lat=-10.0,
    lon=-40.0,
):
    return {
        "local": local,
        "original": original,
        "nome": nome,
        "endereco": endereco,
        "lat": lat,
        "lon": lon,
    }


def _payload() -> dict:
    if not MUDANCAS.exists():
        pytest.skip("mudancas.json ainda não gerado")
    return json.loads(MUDANCAS.read_text(encoding="utf-8"))


# ------------------------------------------------------------ classificação


@pytest.mark.parametrize(
    ("l1", "l2", "cat", "real"),
    [
        (_linha(1120, 1015), _linha(1015, 1015, "ESCOLA B", "RUA Y, 5"), "A", True),
        (_linha(1015, 1015), _linha(1120, 1015, "ESCOLA B", "RUA Y, 5"), "B", True),
        (_linha(1120, 1015), _linha(1130, 1015, "ESCOLA C", "RUA Z, 1"), "C", True),
        (_linha(1015, 1015), _linha(1120, 1120, "ESCOLA B", "RUA Y, 5"), "X", True),
        (_linha(), _linha(nome="POSTO DE SAUDE", endereco="AV BRASIL, 900"), "D", True),
        (
            _linha(),
            _linha(nome="ESCOLA  A.", endereco="R. X, Nº 10 - CENTRO"),
            "D",
            False,
        ),
        (_linha(), _linha(endereco="RUA W, 10"), "E", True),
        (_linha(), _linha(endereco="R. X, 10 (FUNDOS)"), "E", False),
        (_linha(), _linha(nome="ESCOLA A ANEXO"), "F", False),
        (_linha(), _linha(lat=-10.02), "G", False),
        (_linha(lat=float("nan"), lon=float("nan")), _linha(), "G", False),
        (_linha(), _linha(lat=-10.001), "H", False),
        (_linha(), _linha(), "Z", False),
        (_linha(1120, 1015), _linha(1015, 1015), "A", False),
    ],
)
def test_classificacao_sintetica(l1, l2, cat, real):
    r = cl.classificar_linha(l1, l2)
    assert r.categoria == cat
    assert r.mudanca_real is real
    assert r.motivo and TRAVESSAO not in r.motivo


def test_categoria_cadastro_segue_o_contrato():
    assert cl.categoria_cadastro(_linha(1120, 1015), _linha(1015, 1015), 0.0) == "A"
    assert cl.categoria_cadastro(_linha(), _linha(lat=-10.0035), 390.0) == "G"
    assert cl.categoria_cadastro(_linha(), _linha(lat=-10.002), 222.0) == "H"


def test_g_acima_de_50_km_e_coordenada_suspeita():
    r = cl.classificar_linha(_linha(), _linha(lat=-11.0))
    assert r.categoria == "G" and not r.mudanca_real and r.coord_suspeita


def test_agregada_herda_a_principal():
    def cad(turno: int, local: int) -> pd.DataFrame:
        base = {
            "uf": "XX",
            "mun": "00001",
            "municipio": "TESTE",
            "zona": 1,
            "tipo_local": "Convencional",
            "eleitores_federal": 0,
            "nome_original": "ESCOLA A",
            "endereco_original": "RUA X, 10",
            "bairro": "CENTRO",
            "cep": "00000000",
        }
        principal = {
            **base,
            "secao": 1,
            "tipo_secao": 1,
            "principal": -1,
            "eleitores": 300,
            **_linha(
                local, 1015, "ESCOLA A" if local == 1015 else "ESCOLA B", "RUA X, 10"
            ),
        }
        agregada = {
            **base,
            "secao": 2,
            "tipo_secao": 2,
            "principal": 1,
            "eleitores": 20,
            **_linha(1015, 1015),
        }
        if local != 1015:
            principal["endereco"] = "RUA Y, 5"
            principal["lat"] = -10.01
        return pd.DataFrame([principal, agregada])

    df = cl.classificar(cad(1, 1015), cad(2, 1120))
    agr = df[df["secao"] == 2].iloc[0]
    assert agr["categoria_cadastro"] == "Z"
    assert agr["categoria"] == "B" and agr["mudanca_real"] and agr["herdada"]
    assert int(agr["local_2t"]) == 1120


# ------------------------------------------------------------ endereço e distância


@pytest.mark.parametrize(
    ("a", "b", "mesmo"),
    [
        (
            "PRAÇA DO COMÉRCIO - ZONA RURAL",
            "JATOBA - PRAÇA DO COMÉRCIO - ZONA RURAL",
            True,
        ),
        ("RUA ROGERIO GISSONI", "RUA ROGERIO GISSONI, 352", True),
        (
            "RUA GUATEMALA, N. 346 CEP 87.040-210",
            "RUA GUATEMALA,346 - VILA MORANGUEIRA",
            True,
        ),
        ("RUA MUANÁ, 105", "RUA IRAPUÁ, 243", False),
        ("ESTRADA SAO LOURENCO 5003", "ESTRADA RIO DO PATY 5003", False),
    ],
)
def test_logradouro_normalizado(a, b, mesmo):
    assert en.mesmo_logradouro(a, b) is mesmo


def test_numero_diferente_muda_o_endereco():
    assert en.mesmo_logradouro("PANSKA 12, PRAGA", "PANSKA 5, PRAGA")
    assert not en.mesmo_endereco("PANSKA 12, PRAGA", "PANSKA 5, PRAGA")


def test_haversine_um_grau_de_latitude():
    d = en.haversine_m(0.0, 0.0, 1.0, 0.0)
    assert d == pytest.approx(111_195, rel=1e-3)
    assert en.haversine_m(0.0, 0.0, float("nan"), 0.0) is None


def test_links_do_mapa():
    assert di.maps_rota(-10, -40, None, None) is None
    rota = di.maps_rota(-10, -40, -10.1, -40.2)
    assert rota.startswith(
        "https://www.google.com/maps/dir/?api=1&origin=-10.000000,-40.000000"
    )
    assert rota.endswith("travelmode=walking")
    assert di.maps_novo(None, None, "ESCOLA, CIDADE").endswith("query=ESCOLA%2C+CIDADE")


# ------------------------------------------------------------ estatística


def test_diferenca_dentro_do_municipio_bate_com_a_conta_a_mao():
    # dois municípios; abstenção tratada 30% e 20%, controle 20% e 10%
    linhas = []
    for mun, (at, ac) in {"A": (0.3, 0.2), "B": (0.2, 0.1)}.items():
        for trat, ab, n in ((1, at, 4), (0, ac, 10)):
            for _ in range(n):
                linhas.append(
                    {"mun": mun, "trat": trat, "aptos": 100.0, "abst": 100 * ab}
                )
    d = pd.DataFrame(linhas)
    d["celula"] = d["trat"]
    for c in an.COLUNAS:
        d[c] = 0.0
    d["aptos"] = 100.0
    d["abst_num"] = d["abst"]
    p = an.montar_passada(d, d["mun"], reps=200, seed=1)
    grupos = {"t": np.array([False, True])}
    r = an.rodar(
        p, grupos, [an.Tarefa("x", "t", None, an.METRICAS_VOTO["abstencao"], "aptos")]
    )
    out = an.formatar(r["x"])
    assert out["diferenca_pp"]["valor"] == pytest.approx(10.0)
    lo, hi = out["diferenca_pp"]["ic95"]
    assert lo <= 10.0 <= hi


def test_bootstrap_estratificado_preserva_o_tamanho_do_estrato():
    est = np.array([0, 0, 0, 1, 1])
    y = np.ones((5, 1))
    r = es.Reamostragem(est, y, reps=30, seed=3, bloco=7)
    for somas in r.replicas():
        assert np.allclose(somas[:, 0, 0], 3) and np.allclose(somas[:, 1, 0], 2)


# ------------------------------------------------------------ cenários


def _urnas_sinteticas() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "aptos": [300, 200, 100],
            "comparecimento": [240, 150, 80],
            "flavio": [100, 50, 40],
            "lula": [110, 80, 30],
            "terceira": [20, 10, 5],
            "brancos": [4, 5, 2],
            "nulos": [6, 5, 3],
            "validos": [230, 140, 75],
            "mudanca_real": [True, True, False],
            "categoria": ["A", "B", "Z"],
            "temp_1t": [True, False, False],
            "temp_2t": [False, True, False],
        }
    )


def test_cenarios_fecham():
    u = _urnas_sinteticas()
    for pp in (2.0, 5.0, -1.5):
        v = ce.votos_perdidos(u, pp)
        assert sum(v[c] for c in ce.COMPONENTES) == pytest.approx(v["total"])
        assert v["total"] == pytest.approx(pp / 100 * u["aptos"].sum())
    cen = ce.montar(u, 1000.0, {"valor": 1.0, "ic95": [0.5, 1.5], "fonte": "x"})
    for f in cen["fixos"]:
        tot = f["mudanca_real"]["_exato"]["total"]
        partes = (
            f["categoria_a"]["_exato"]["total"]
            + f["novas_realocacoes"]["_exato"]["total"]
        )
        assert tot == pytest.approx(partes)
    br = cen["estimativa_brasileira"]
    soma = (
        br["novas_realocacoes"]["central"]["variacao_diferenca_flavio_menos_lula_votos"]
        + br["categoria_a_ganho"]["central"][
            "variacao_diferenca_flavio_menos_lula_votos"
        ]
    )
    assert (
        br["saldo_1t_para_2t"]["central"]["variacao_diferenca_flavio_menos_lula_votos"]
        == soma
    )


def test_quem_perde_fala_nas_duas_direcoes():
    u = _urnas_sinteticas()
    cen = ce.montar(u, 1000.0, {"valor": 1.0, "ic95": [0.5, 1.5], "fonte": "x"})
    q = tx.quem_perde(cen)
    assert "Flávio" in q["abstencao_maior"] and "Lula" in q["comparecimento_recuperado"]
    assert all(TRAVESSAO not in t for t in q.values())


# ------------------------------------------------------------ saídas publicadas


def test_soma_das_categorias_e_referencia():
    p = _payload()
    cats = p["resumo"]["por_categoria_cadastro"]
    assert sum(v["secoes"] for v in cats.values()) == 517179
    assert cats["A"] == {"secoes": 754, "eleitores": 222482}
    assert cats["G"]["secoes"] == 575
    assert all(c["passou"] for c in p["controles"]), [
        c["nome"] for c in p["controles"] if not c["passou"]
    ]


def test_caso_de_controle_do_rj():
    arq = POLITIZE / "RJ" / "188.json"
    if not arq.exists():
        pytest.skip("dados do Politize ainda não gerados")
    z = json.loads(arq.read_text(encoding="utf-8"))
    for s in range(123, 128):
        item = z["secoes"][str(s)]
        assert item["categoria"] == "D" and item["mudanca_real"] is True
        assert "IRAPUÁ" in item["end_2t"] and "MUANÁ" in item["end_1t"]
        assert item["maps_novo"].startswith(
            "https://www.google.com/maps/search/?api=1&query="
        )
    par = [
        x
        for x in _payload()["locais"]
        if x["uf"] == "RJ"
        and x["mun_tse"] == "60011"
        and x["zona"] == 188
        and x["local_1t"] == 1295
    ]
    assert (
        len(par) == 1
        and par[0]["mudanca_real"]
        and par[0]["secoes"] == [123, 124, 125, 126, 127]
    )


def test_json_publico_sem_travessao_e_sem_campos_internos():
    if not DADOS.exists():
        pytest.skip("dados.json ainda não gerado")
    texto = DADOS.read_text(encoding="utf-8")
    assert TRAVESSAO not in texto
    assert "fraude" not in texto.lower()
    d = json.loads(texto)
    assert "_interno" not in d
    for arq in POLITIZE.rglob("*.json"):
        assert TRAVESSAO not in arq.read_text(encoding="utf-8"), arq


def test_csv_com_o_mesmo_total():
    if not CSV.exists():
        pytest.skip("secoes.csv ainda não gerado")
    mr = _payload()["resumo"]["mudanca_real"]
    with CSV.open(encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    assert len(linhas) == mr["secoes"]
    assert sum(int(x["eleitores"]) for x in linhas) == mr["eleitores"]
    assert TRAVESSAO not in CSV.read_text(encoding="utf-8")


def test_politize_indice_confere_com_arquivos():
    ind = POLITIZE / "indice.json"
    if not ind.exists():
        pytest.skip("índice do Politize ainda não gerado")
    d = json.loads(ind.read_text(encoding="utf-8"))
    total = 0
    for uf, info in d["por_uf"].items():
        arquivos = list((POLITIZE / uf).glob("*.json"))
        assert len(arquivos) == info["zonas"]
        total += sum(
            len(json.loads(a.read_text(encoding="utf-8"))["secoes"]) for a in arquivos
        )
    assert total == d["total_secoes"] == sum(d["por_fonte"].values())


def test_efeito_e_cenarios_rotulados():
    p = _payload()
    assert "não efeito causal" in p["efeito_1t"]["rotulo"]
    mag = p["efeito_1t"]["magnitude_para_cenarios"]
    assert mag["valor"] is not None and mag["ic95"][0] <= mag["valor"] <= mag["ic95"][1]
    br = p["cenarios_abstencao"]["estimativa_brasileira"]
    assert br["magnitude_pp"]["central"] == mag["valor"]
    assert not math.isnan(p["cenarios_abstencao"]["validos_nacionais_1t"])
