"""Vão estadual dos governadores nas 27 UFs, com o centro: regra, coligação e figura.

Fixtures pequenas, montadas aqui; nenhum teste lê o banco nem o arquivo do TSE.
"""

import json
import re

import pytest
from apuracao_2026 import coligacoes as COL
from apuracao_2026 import vao_governadores as VG
from apuracao_2026.pagina_figuras import FIGURAS


def _tips(h: str) -> dict:
    m = re.search(
        r'<script type="application/json" class="tips">(.*?)</script>', h, re.DOTALL
    )
    return json.loads(m.group(1).replace("<\\/", "</"))


# ------------------------------------------------------------------ coligações


def test_partidos_da_composicao_abre_federacoes():
    comp = (
        "PSB / FEDERAÇÃO BRASIL DA ESPERANÇA - FE BRASIL (13-PT / 65-PC do B / 43-PV) / "
        "FEDERAÇÃO UNIÃO PROGRESSISTA (44-UNIÃO / 11-PP)"
    )
    assert COL.partidos_da_composicao(comp) == [
        "PC do B",
        "PP",
        "PSB",
        "PT",
        "PV",
        "UNIÃO",
    ]
    assert COL.partidos_da_composicao("AGIR") == ["AGIR"]


def test_lado_da_coligacao():
    assert COL.lado_da_coligacao(["PT", "PSB"]) == "lula"
    assert COL.lado_da_coligacao(["PL", "NOVO"]) == "flavio"
    assert COL.lado_da_coligacao(["PL", "PT"]) is None
    assert COL.lado_da_coligacao(["PSD", "NOVO"]) is None


# ------------------------------------------------------------------ vão dos governadores


def _p(uf, lider, pl, seg, ps):
    return {
        "uf": uf,
        "lider": lider,
        "pct_lider": pl,
        "segundo": seg,
        "pct_segundo": ps,
    }


def _g(nome, partido, campo, pct):
    return {"nome": nome, "partido": partido, "campo": campo, "pct": pct}


FL, LU = "FLAVIO BOLSONARO", "LULA"
FINAL = {
    "presidente": {
        "ufs": [
            _p("PE", LU, 63.45, FL, 31.03),
            _p("RJ", FL, 53.01, LU, 39.41),
            _p("PB", LU, 61.31, FL, 33.07),
            _p("SP", FL, 51.93, LU, 38.2),
        ]
    },
    "governadores": {
        "ufs": [
            {"uf": "PE", "decisao": "eleito", "candidatos": [_g("RAQUEL LYRA", "PSD", "centro", 53.27)]},
            {
                "uf": "RJ",
                "decisao": "segundo_turno",
                "candidatos": [
                    _g("DOUGLAS RUAS", "PL", "direita", 49.27),
                    _g("EDUARDO PAES", "PSD", "centro", 42.76),
                ],
            },
            {"uf": "PB", "decisao": "eleito", "candidatos": [_g("LUCAS RIBEIRO", "PP", "centro-direita", 64.3)]},
            {"uf": "SP", "decisao": "eleito", "candidatos": [_g("TARCÍSIO", "REPUBLICANOS", "direita", 62.65)]},
        ]
    },
}  # fmt: skip


def test_vao_cobre_todas_as_ufs_com_o_centro():
    V = VG.vao_completo(FINAL)
    lin = {x["governador"]: x for x in V["lista"]}
    assert V["n_ufs"] == 4 and V["n_candidaturas"] == 5
    rl = lin["RAQUEL LYRA"]
    assert rl["finalista"] == "flavio" and rl["comparacao"] == VG.SEM_APOIO
    assert rl["vao_pp"] == round(53.27 - 31.03, 2)
    assert rl["vao_lula_pp"] == round(53.27 - 63.45, 2)
    assert lin["EDUARDO PAES"]["finalista"] == "lula"
    assert lin["EDUARDO PAES"]["vao_pp"] == round(42.76 - 39.41, 2)
    assert lin["TARCÍSIO"]["comparacao"] == "mesmo bloco"
    assert lin["DOUGLAS RUAS"]["principal"] and not lin["EDUARDO PAES"]["principal"]
    assert {c["uf"] for c in V["centro"]} == {"PE", "RJ"}


def test_coligacao_com_pt_vira_comparacao_com_lula():
    lr = next(x for x in VG.vao_completo(FINAL)["lista"] if x["uf"] == "pb")
    assert lr["finalista"] == "lula" and lr["comparacao"] == "coligação com o PT"
    assert lr["vao_pp"] == round(64.3 - 61.31, 2)
    assert lr["vao_flavio_pp"] == round(64.3 - 33.07, 2)


def test_centro_sem_linha_na_tabela_falha():
    final = json.loads(json.dumps(FINAL))
    final["presidente"]["ufs"].append(_p("MT", FL, 65.15, LU, 29.18))
    final["governadores"]["ufs"].append(
        {
            "uf": "MT",
            "decisao": "eleito",
            "candidatos": [_g("FULANO", "PSD", "centro", 50.0)],
        }
    )
    with pytest.raises(ValueError, match="COMPARACAO_CENTRO"):
        VG.vao_completo(final)


@pytest.mark.parametrize(
    ("chave", "partidos"),
    [
        (("SP", "TARCÍSIO"), ["PT", "REPUBLICANOS"]),
        (("PE", "RAQUEL LYRA"), ["PL", "PSD"]),
    ],
)
def test_coligacao_que_contraria_a_comparacao_falha(chave, partidos):
    col = {chave: {"coligacao": "X", "partidos": partidos}}
    with pytest.raises(ValueError, match="coligação"):
        VG.vao_completo(FINAL, col)


def test_valores_precisos_do_banco_substituem_o_boletim():
    precisos = {
        "governador": {("SP", "TARCÍSIO"): 62.652626},
        "presidente": {"SP": {"flavio": 51.9312, "lula": 38.2}},
    }
    sp = next(
        x for x in VG.vao_completo(FINAL, None, precisos)["lista"] if x["uf"] == "sp"
    )
    assert sp["vao_pp"] == round(62.652626 - 51.9312, 2)
    with pytest.raises(ValueError, match="no banco"):
        VG.vao_completo(
            FINAL, None, {"governador": {("SP", "TARCÍSIO"): 63.0}, "presidente": {}}
        )


def test_figura_vao_estadual_marca_o_centro():
    G = {
        "vao_estadual": VG.vao_completo(FINAL),
        "rotulo_obrigatorio_vao": "teto endereçável, nunca transferência certa",
    }
    h = FIGURAS["vao_estadual"]({"governadores": G})
    assert h.startswith('<figure class="reveal fig-i" id="fig-vao_estadual"')
    assert "url(#vao-sem-apoio)" in h and "× Lula" in h and "× Flávio" in h
    assert "centro sem apoio declarado" in h
    tips = _tips(h)
    assert any("Contra Lula" in v for k, v in tips.items() if k != "_rows")
    assert "—" not in h
