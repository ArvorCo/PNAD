"""Capítulo ``hipoteses`` do dossiê do 2º turno: contrato de ``hipoteses.json``, regras e página."""

import importlib.util
import json
import re

import pytest
from apuracao_2t_2026 import pagina_cap_hipoteses as CAP
from apuracao_2t_2026.pagina_comum import DADOS, ROOT, dados_2t
from apuracao_2026.pagina_comum import Capitulo

ARQ = DADOS / "hipoteses.json"
spec = importlib.util.spec_from_file_location(
    "hip", ROOT / "scripts/apuracao-2t-2026-hipoteses.py"
)
hip = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hip)

pytestmark = pytest.mark.skipif(not ARQ.exists(), reason="hipoteses.json ausente")


@pytest.fixture(scope="module")
def H():
    return json.loads(ARQ.read_text(encoding="utf-8"))


def ler(nome):
    return json.loads((DADOS / nome).read_text(encoding="utf-8"))


def test_seis_hipoteses_com_estado_valido(H):
    ids = [h["id"] for h in H["hipoteses"]]
    assert ids == ["h1", "h2", "h3", "h4", "h5", "h6"]
    for h in H["hipoteses"]:
        assert h["estado"] in hip.ESTADOS
        assert h["regra"] and h["alcance"] and h["curto"]
    assert next(h for h in H["hipoteses"] if h["id"] == "h6")["estado"] == "compativel"


def test_matriz_completa(H):
    for t in H["discriminador"]:
        assert t["resultado"] in hip.RESULTADOS
        assert set(t["celulas"]) == {h["id"] for h in H["hipoteses"]}
        assert set(t["celulas"].values()) <= set(hip.RESULTADOS)


def test_numeros_lidos_dos_outros_jsons(H):
    L, M, R = ler("logs.json"), ler("metadados.json"), ler("rdv.json")
    PV, T = ler("pesquisas_vs_urna.json"), ler("transferencia.json")
    assert H["h1"]["computados_17_19"] == L["cadencia"]["brasil_2t"]["computados_17_19"]
    assert (
        H["h1"]["computados_depois_19"]
        == L["cadencia"]["brasil_2t"]["computados_depois_19"]
    )
    assert (
        H["h1"]["bus_apos_19h_ultimo_voto_ate_1715"]
        == L["cadencia"]["bu_apos_19h"]["ultimo_voto_ate_1715"]
    )
    assert (
        H["h2"]["vsc_bu_igual"]
        == M["turnos"]["2t"]["coerencia_vsc"]["bu_publicado_igual_ao_vsc"]["sim"]
    )
    assert H["h2"]["rdv_confere"] == R["cobertura"]["total"]["confere"]
    assert H["h2"]["log_confere"] == L["cobertura"]["contagem_confere"]
    assert H["h3"]["teto_comparecimento_pp"] == (
        PV["hipoteses"]["contabilidade_entre_turnos"]["limite_comparecimento"][
            "parcela_maxima_explicada_pp"
        ]
    )
    assert H["h6"]["voltaram_milhoes"] == T["resposta"]["voltaram_milhoes"]
    assert (
        H["h6"]["casas_mesmo_sentido"]
        == PV["resumo"]["publicado_validos_do_total"]["positivos"]
    )


def test_fontes_com_hash_atual(H):
    for nome, h in H["fontes"].items():
        if nome.endswith(".json") and (DADOS / nome).exists():
            assert hip.sha(DADOS / nome) == h, nome


def test_cronologia_com_fonte_e_silencio(H):
    c = H["cronologia"]
    assert all(m["url"].startswith("http") for m in c["marcos"])
    assert c["silencio"]["inicio"] < c["silencio"]["fim"]
    assert c["silencio"]["versoes_geradas_dentro"] == 0
    assert c["video"]["copia_recebida"]["conserva_original"] is False
    horas = [r["hora_brt"] for r in c["video"]["republicacoes"]]
    assert horas == sorted(horas)


def test_tercos_tem_mesmo_eleitorado(H):
    e = [t["eleitores"] for t in H["h3"]["tercos"]]
    assert max(e) / min(e) < 1.6


def test_classificar_responde_aos_numeros(H):
    h1 = dict(H["h1"], computados_17_19=H["h1"]["margem_votos"])
    est = {
        h["id"]: h["estado"]
        for h in hip.classificar(h1, H["h2"], H["h3"], H["h4"], H["h5"], H["h6"], None)
    }
    assert est["h1"] == "compativel"
    h2 = dict(H["h2"], zona={"zonas_divergem": 1})
    est = {
        h["id"]: h["estado"]
        for h in hip.classificar(H["h1"], h2, H["h3"], H["h4"], H["h5"], H["h6"], None)
    }
    assert est["h2"] == "pendente"


def test_render_sem_travessao_e_com_rotulos():
    d = dados_2t()
    cap = Capitulo(
        "hipoteses", "14", "Hipóteses", "t", ("hipoteses.json",), lambda d: ""
    )
    html = CAP.render(d, cap)
    assert "—" not in html
    assert "fraude" not in html.lower()
    assert "atipicidade pede explicação, não prova irregularidade" in html
    assert "se foi isso mesmo, não saberemos" in html
    for fig in ("hipoteses_tarde", "hipoteses_matriz", "hipoteses_cadencia"):
        assert f'id="fig-{fig}"' in html
    for i in range(1, 7):
        assert f'id="hip-h{i}"' in html
    assert len(re.findall(r"O que ainda falta", html)) == 6


def test_precedentes_e_video(H):
    P = H["precedentes"]
    assert P and len(P["itens"]) >= 10
    v = H["cronologia"]["video"]
    assert v["publicado_brt_segundos"] == "15:34:58"
    lo, hi = H["h4"]["video_antes_da_peticao_faixa_min"]
    assert lo <= hi
    pge = next(m for m in H["cronologia"]["marcos"] if m["hora"] == "17:01")
    assert "TSE" in pge["rotulo"]
