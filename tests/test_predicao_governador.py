"""Motor da predição de governador com dados sintéticos e a página gerada."""

import copy
import importlib.util
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pytest
from governador_2026 import base as B
from governador_2026 import motor as M
from governador_2026 import saida
from senado_2026 import motor as SM

ROOT = Path(__file__).resolve().parents[1]
MALHA = ROOT / "data/originals/ibge_malhas/br_uf/br_uf_minima.geojson"
AGORA = datetime(2026, 10, 3, 23, 0, tzinfo=timezone.utc)
SIM = 3000


def onda(uf, casa, fim, candidatos, *, n=1000, ind=10.0, bn=8.0, pares=(), **kw):
    soma = sum(v for _, _, v in candidatos) + ind + bn
    return {
        "instituto": casa.title(),
        "instituto_slug": casa,
        "uf": uf,
        "cargo": "governador",
        "registro_tse": None,
        "campo": {"inicio": fim, "fim": fim},
        "divulgacao": fim,
        "n": n,
        "fonte": {"tipo": "teste", "url": "https://exemplo.invalid", "sha256": None},
        "pergunta": {
            "codigo": "T",
            "tipo": "estimulada",
            "votos_por_eleitor": 1,
            "soma_total": soma,
        },
        "candidatos": [
            {"nome": nome, "partido": partido, "valor": valor}
            for nome, partido, valor in candidatos
        ],
        "indecisos": ind,
        "branco_nulo": bn,
        "segundo_turno": [
            {
                "codigo": "2T",
                "pagina": 1,
                "candidatos": [
                    {"nome": a, "partido": None, "valor": va},
                    {"nome": b, "partido": None, "valor": vb},
                ],
                "indecisos": 5.0,
                "branco_nulo": 5.0,
                "soma_total": va + vb + 10.0,
            }
            for a, va, b, vb in pares
        ],
        "observacoes": [],
        **kw,
    }


def ondas_sinteticas():
    return [
        # SP: favorita acima de 50% dos válidos, decide no 1º turno.
        onda(
            "SP",
            "quaest",
            "2026-10-02",
            [("Ana", "PL", 52), ("Bia", "PT", 28), ("Caio", "PSD", 4)],
        ),
        # RS: 2º turno medido, par Ana x Bia.
        onda(
            "RS",
            "quaest",
            "2026-10-02",
            [("Ana", "PL", 40), ("Bia", "PT", 32), ("Caio", "MDB", 10)],
            pares=(("Ana", 50, "Bia", 40),),
        ),
        onda(
            "RS",
            "datafolha",
            "2026-10-01",
            [("Ana", "PL", 38), ("Bia", "PT", 34), ("Caio", "MDB", 9)],
            pares=(("Ana", 48, "Bia", 42),),
        ),
        # BA: sem par medido, transferência declarada.
        onda(
            "BA",
            "quaest",
            "2026-10-02",
            [("Dora", "PT", 42), ("Edu", "UNIÃO", 36), ("Fê", "PSOL", 4)],
        ),
        # PR: só pesquisa antiga.
        onda("PR", "quaest", "2026-09-10", [("Gil", "PSD", 45), ("Hugo", "PL", 30)]),
    ]


@pytest.fixture(scope="module")
def ondas():
    n_ausente = 600
    return [
        B.normalizar_onda(
            d, f"{d['instituto_slug']}_{d['uf']}_{d['campo']['fim']}.json", n_ausente
        )
        for d in ondas_sinteticas()
    ]


@pytest.fixture(scope="module")
def tse():
    return B.Tse(pasta=ROOT / "tests" / "fixtures" / "inexistente")


@pytest.fixture(scope="module")
def resultado(ondas, tse):
    return saida.prever(
        ondas, tse, {}, None, simulacoes=SIM, sensibilidades=True, agora=AGORA
    )


def test_soma_p_eleito_e_decomposicao(resultado):
    for uf, e in resultado["estados"].items():
        if e["favorito"] is None:
            continue
        assert abs(sum(p["p_eleito"] for p in e["probabilidades"]) - 1) < 1e-9, uf
        for p in e["probabilidades"]:
            assert abs(p["p_vence_1t"] + p["p_vence_2t"] - p["p_eleito"]) < 1e-9
        assert abs(e["p_decide_1t"] + e["p_segundo_turno"] - 1) < 1e-9
        assert (
            abs(sum(p["p_vence_1t"] for p in e["probabilidades"]) - e["p_decide_1t"])
            < 1e-9
        )


def test_favorita_com_maioria_decide_no_primeiro_turno(resultado):
    sp = resultado["estados"]["SP"]
    assert sp["favorito"] == "Ana"
    assert sp["p_decide_1t"] > 0.8
    assert sp["classe"] == "decidida"


def test_par_medido_entra_e_e_marcado(resultado):
    rs = resultado["estados"]["RS"]
    assert rs["pares_medidos"]
    par = rs["pares_2t"][0]
    assert par["nomes"] == ["Ana", "Bia"]
    assert par["medido"] is True
    assert par["p_par"] > 0.5
    # Fração medida: média por recência de 50/90 e 48/90.
    assert 52 < par["medicao"]["fracao_primeiro_nome"] < 56
    assert par["projecao"]["Ana"] > 50


def test_par_nao_medido_usa_transferencia(resultado):
    ba = resultado["estados"]["BA"]
    assert not ba["pares_medidos"]
    assert ba["pares_2t"][0]["medido"] is False
    assert any("transferência" in n for n in ba["notas"])


def test_cobertura_antiga_e_sem_pesquisa(resultado):
    assert resultado["estados"]["PR"]["cobertura"] == "antiga"
    assert resultado["estados"]["PR"]["incerteza"] == "alta"
    assert resultado["estados"]["AC"]["cobertura"] == "sem_pesquisa"
    assert resultado["estados"]["AC"]["favorito"] is None
    assert "AC" in resultado["nacional"]["sem_pesquisa"]


def test_nacional_fecha(resultado):
    n = resultado["nacional"]
    assert n["ufs_cobertas"] == 4
    esperado = sum(
        e["p_decide_1t"] for e in resultado["estados"].values() if e["favorito"]
    )
    assert abs(n["decididos_1t"]["esperado"] - esperado) < 1e-6
    total = sum(v["esperado"] for v in n["por_campo"].values())
    assert abs(total - 4) < 1e-6


def test_transferencia_fecha_e_respeita_distancia():
    ta, tb = M.transferencia(["direita", "esquerda", "centro-direita", "centro"], 0, 1)
    assert ta[0] == 1 and tb[1] == 1
    for j in (2, 3):
        assert abs(ta[j] + tb[j] - M.TRANSFERENCIA_VALIDA) < 1e-9
    assert ta[2] > tb[2]  # centro-direita vai mais para a direita
    assert abs(ta[3] - tb[3]) < 1e-9  # centro fica equidistante


def test_reprodutivel(ondas, tse):
    a = saida.prever(
        ondas, tse, {}, None, simulacoes=500, sensibilidades=False, agora=AGORA
    )
    b = saida.prever(
        ondas, tse, {}, None, simulacoes=500, sensibilidades=False, agora=AGORA
    )
    a.pop("gerado_em"), b.pop("gerado_em")
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_outros_vira_categoria():
    d = ondas_sinteticas()[0]
    d = copy.deepcopy(d)
    d["candidatos"].append({"nome": "Outros", "partido": None, "valor": 3})
    o = B.normalizar_onda(d, "x.json", 600)
    assert all(c["nome_pesquisa"] != "Outros" for c in o["candidatos"])
    assert o["outros"] == 3.0


def test_erro_dobrado_reduz_decisao_no_primeiro_turno(resultado):
    sens = {s["chave"]: s for s in resultado["validacao"]["sensibilidades"]}
    assert set(sens) == {"erro_dobrado", "indecisos_uniformes", "sem_pares_medidos"}
    sp = resultado["estados"]["SP"]["p_decide_1t"]
    assert sens["erro_dobrado"]["p_decide_1t"]["SP"] < sp


def test_rho_dentro_do_intervalo():
    assert 0 <= M.RHO_TURNOS <= 1
    assert isinstance(SM.erro_de_hipotese(), SM.Erro)


# ----------------------------------------------------------------- página


def _build_module():
    spec = importlib.util.spec_from_file_location(
        "governador_2026_build", ROOT / "scripts/governador-2026-build.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def html(resultado):
    if not MALHA.exists():
        pytest.skip("Malha do IBGE ausente neste ambiente; o mapa não é renderizado")
    mod = _build_module()
    return mod.render(resultado, mod.TEMPLATE.read_text(encoding="utf-8"))


def test_pagina_tem_27_fichas_e_sem_travessao(html):
    assert len(re.findall(r'<details class="sn-ficha"', html)) == 27
    assert "—" not in html
    assert "{{" not in html


def test_pagina_mostra_par_medido_e_corridas(html):
    assert 'class="gv-tag gv-tag-medido"' in html
    assert 'id="corrida-RS"' in html
    assert 'id="par-RS"' in html
    assert "gv-stack" in html


def test_barras_sao_blocos(html):
    for m in re.finditer(r'<(\w+) class="gv-seg[^"]*" style="width:', html):
        assert m.group(1) == "div"
