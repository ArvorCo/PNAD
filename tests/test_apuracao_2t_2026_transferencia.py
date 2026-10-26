"""Transferência 1º → 2º turno: ajuste IPF, regressão ecológica, transcrições e capítulo."""

import json
import re

import numpy as np
import pytest
from apuracao_2t_2026 import pagina_comum as C
from apuracao_2t_2026 import pagina_view as V
from apuracao_2t_2026 import transferencia_dados as D
from apuracao_2t_2026 import transferencia_ipf as I
from apuracao_2t_2026 import transferencia_priors as P
from apuracao_2t_2026 import transferencia_regressao as R

ARQ = C.DADOS / "transferencia.json"
TEM_JSON = ARQ.exists()
TEM_URNAS = D.PRES_2T.exists() and D.PRES_1T.exists() and D.TERCEIRA_1T.exists()


@pytest.fixture(scope="module")
def T():
    if not TEM_JSON:
        pytest.skip("transferencia.json ausente")
    return json.loads(ARQ.read_text(encoding="utf-8"))


# ------------------------------------------------------------------ IPF


def test_ras_bate_as_duas_margens_e_preserva_zero():
    prior = np.array([[5.0, 1.0, 0.0], [2.0, 2.0, 2.0], [1.0, 3.0, 4.0]])
    linhas = np.array([10.0, 6.0, 8.0])
    colunas = np.array([9.0, 7.0, 8.0])
    M, _it, desvio = I.ras(prior, linhas, colunas)
    assert desvio < 1e-9
    assert np.allclose(M.sum(1), linhas) and np.allclose(M.sum(0), colunas)
    assert M[0, 2] == 0.0


def test_ras_recusa_totais_diferentes():
    with pytest.raises(ValueError):
        I.ras(np.ones((2, 2)), np.array([1.0, 1.0]), np.array([1.0, 2.0]))


def test_ras_recupera_matriz_quando_prior_tem_a_mesma_razao_de_chances():
    rng = np.random.default_rng(7)
    verdade = rng.uniform(1, 9, size=(4, 3))
    # Prior com as mesmas razões de chances da verdade (escala por linha e coluna).
    prior = (
        verdade * rng.uniform(0.5, 2, size=(4, 1)) * rng.uniform(0.5, 2, size=(1, 3))
    )
    M, *_ = I.ras(prior, verdade.sum(1), verdade.sum(0))
    assert np.allclose(M, verdade, rtol=1e-8)


# ------------------------------------------------------------------ regressão


def _painel_sintetico(n=600, alfa=(0.62, 0.35, 0.03), semente=3):
    rng = np.random.default_rng(semente)
    uns = []
    for i in range(n):
        e = int(rng.integers(5_000, 200_000))
        c1 = int(e * rng.uniform(0.72, 0.84))
        t1 = int(c1 * rng.uniform(0.03, 0.12))
        bn1 = int(c1 * rng.uniform(0.02, 0.07))
        l1 = int((c1 - t1 - bn1) * rng.uniform(0.3, 0.7))
        f1 = c1 - t1 - bn1 - l1
        dc = int(e * rng.normal(0.018, 0.02))
        uf = f"U{i % 9}"
        a_uf = 0.004 * (i % 9)
        ruido = rng.normal(0, 0.002, 3) * e
        dl = alfa[0] * dc + 0.45 * t1 + 0.3 * bn1 + a_uf * e + ruido[0]
        dbn = alfa[2] * dc + 0.10 * t1 - 0.5 * bn1 + ruido[1]
        df = dc + t1 - dl - dbn
        uns.append(
            {
                "uf": uf,
                "regiao": "R",
                "E1": e,
                "E2": e,
                "C1": c1,
                "C2": c1 + dc,
                "L1": l1,
                "F1": f1,
                "T1": t1,
                "BN1": bn1,
                "L2": l1 + dl,
                "F2": f1 + df,
                "BN2": bn1 + dbn,
            }
        )
    return uns


def test_regressao_recupera_a_composicao_e_soma_um():
    esp = R.ajusta(R.tabela(_painel_sintetico()), ("uf",), nome="sintética")
    b = {x: esp["coef"][x]["delta_comparecimento"]["b"] for x in R.DESTINOS_REG}
    assert abs(b["L"] - 0.62) < 0.02 and abs(b["BN"] - 0.03) < 0.01
    assert abs(sum(b.values()) - 1) < 1e-9
    assert abs(esp["conferencia_soma_c"] - 1) < 1e-9


def test_regressao_registra_casos_degenerados_sem_quebrar():
    uns = _painel_sintetico(n=300)
    # Um grupo com uma unidade só, sem variação interna: sai do efeito fixo e é registrado.
    uns[0] = dict(uns[0], uf="SOZINHO")
    tab = R.tabela(uns)
    esp = R.ajusta(tab, ("uf",), nome="degenerada")
    assert esp["excluidas"]["grupos_com_uma_unidade"]["exemplos"] == ["SOZINHO"]
    assert esp["n"] == 299 and esp["n_entrada"] == 300
    # Eleitorado igual nos dois turnos: a coluna Δeleitorado some e é anotada.
    assert "delta_eleitorado" in esp["excluidas"]["colunas_sem_variacao"]
    assert abs(esp["conferencia_soma_b"] - 1) < 1e-9


def test_regressao_sem_unidades_falha_com_mensagem():
    tab = R.tabela(_painel_sintetico(n=5))
    vazia = R.filtra(tab, np.zeros(5, dtype=bool))
    with pytest.raises(ValueError):
        R.ajusta(vazia, ("uf",), nome="vazia")


def test_demean_por_bincount_igual_ao_laco():
    rng = np.random.default_rng(1)
    v = rng.normal(size=(50, 2))
    w = rng.uniform(1, 3, 50)
    cod = rng.integers(0, 6, 50)
    out = R._demean(v, w, cod)
    for g in range(6):
        m = cod == g
        if m.any():
            assert np.allclose(out[m], v[m] - np.average(v[m], axis=0, weights=w[m]))


def test_regressao_parcial_reproduz_o_coeficiente(T):
    principal = T["regressao"]["principal"]["coef"]["L"]["delta_comparecimento"]["b"]
    assert abs(T["regressao"]["dispersao"]["b_lula"] - principal) < 1e-6


def test_coeficientes_principais_somam_como_a_identidade(T):
    c = T["regressao"]["principal"]["coef"]
    # O JSON guarda seis casas; a identidade vale até esse arredondamento.
    assert (
        abs(sum(c[x]["delta_comparecimento"]["b"] for x in ["L", "F", "BN"]) - 1) < 1e-5
    )
    assert abs(sum(c[x]["terceira_via_1t"]["b"] for x in ["L", "F", "BN"]) - 1) < 1e-5
    assert abs(sum(c[x]["branco_nulo_1t"]["b"] for x in ["L", "F", "BN"])) < 1e-5


# ------------------------------------------------------------------ transcrições e prior


def test_linhas_publicadas_somam_cem_com_arredondamento():
    for (fonte, pagina), grupos in P.LINHAS.items():
        assert fonte in P.FONTES
        for grupo, v in grupos.items():
            assert set(v) == {"F", "L", "BN", "NS"}, (fonte, grupo)
            assert abs(sum(v.values()) - 100) <= 1.5, (fonte, pagina, grupo)


def test_prior_central_cita_paginas_existentes():
    for k, chaves in P.CENTRAL.items():
        for f, pg, g in chaves:
            assert g in P.LINHAS[(f, pg)], (k, f, pg, g)


@pytest.mark.parametrize("origem", P.ORIGENS)
def test_prior_linha_soma_um_sem_zero(origem):
    lin = P.prior_linha(
        origem,
        q=0.006,
        r=0.11,
        alpha={"L": 0.6, "F": 0.38, "BN": 0.02},
        fidelidade=None,
        terceira=P.CENTRAL,
        bn_hipotese=True,
        fracao_brancos=0.34,
    )
    assert set(lin) == set(P.DESTINOS)
    assert abs(sum(lin.values()) - 1) < 1e-12
    assert min(lin.values()) > 0


def test_tipos_de_elo():
    assert P.tipo_elo("abstencao", "lula") == "regressao"
    assert P.tipo_elo("abstencao", "abstencao") == "estimado"
    assert P.tipo_elo("cury", "flavio") == "medido"
    assert P.tipo_elo("lula", "abstencao") == "estimado"
    assert P.tipo_elo("brancos", "lula") == "estimado"


# ------------------------------------------------------------------ margens


@pytest.mark.skipif(not TEM_URNAS, reason="urnas ausentes")
def test_margens_por_uf_preservam_as_identidades():
    m = D.margens_uf()
    nac = D.margens_nacionais(m)
    assert not any(nac["conferencia_soma_ufs_menos_nacional"].values())
    for uf, x in m.items():
        assert sum(x["destinos"].values()) == x["apurado_2t"], uf
        assert sum(x["origens"].values()) == x["apurado_1t"], uf
    assert nac["eleitores_1t"] == nac["aptos_2t"]


def test_matriz_central_bate_as_urnas(T):
    c = T["ipf"]["central"]
    assert c["confere"]["linhas_max_desvio_votos"] < 1
    assert c["confere"]["colunas_max_desvio_votos"] < 1
    M = c["matriz"]
    dest = T["margens"]["nacional"]["destinos"]
    for b in P.DESTINOS:
        assert (
            abs(sum(M[a][b] for a in P.ORIGENS) - dest[b]) <= 1 + len(P.ORIGENS) * 0.5
        )


def test_linha_da_abstencao_fica_fixa_na_regressao(T):
    c = T["ipf"]["central"]
    m = c["metricas"]
    assert abs(m["voltaram_lula_pct"] / 100 - c["alpha"]["L"]) < 0.01
    # O diagnóstico com a linha ajustada se afasta da regressão: é por isso que ela fica fixa.
    diag = T["ipf"]["sensibilidades"]["abstencao_ajustada"]["metricas"][
        "voltaram_lula_pct"
    ]
    assert diag > m["voltaram_lula_pct"]


def test_contagem_dos_elos(T):
    n = T["ipf"]["central"]["contagem_tipos"]
    assert (
        n["medido"]["elos"] == 28
        and n["regressao"]["elos"] == 4
        and n["estimado"]["elos"] == 18
    )
    assert abs(sum(x["pct_votos"] for x in n.values()) - 100) < 1e-6


def test_resposta_dentro_das_faixas(T):
    r = T["resposta"]
    assert (
        r["voltaram_lula_ic"][0] <= r["voltaram_lula_pct"] <= r["voltaram_lula_ic"][1]
    )
    assert r["explica_pp_ic"][0] <= r["explica_pp"] <= r["explica_pp_ic"][1]
    inv = T["ipf"]["invariantes"]
    assert (
        inv["terceira_flavio_pct"][0]
        <= r["terceira_flavio_pct"]
        <= inv["terceira_flavio_pct"][1]
    )
    c = T["contabilidade"]
    assert c["conferencia_disponiveis_menos_ganhos"] == 0


def test_json_e_memorando_sem_travessao(T):
    assert "—" not in ARQ.read_text(encoding="utf-8")
    assert "—" not in (C.DADOS / "transferencia.md").read_text(encoding="utf-8")


# ------------------------------------------------------------------ capítulo


@pytest.fixture(scope="module")
def html(T):
    from apuracao_2t_2026 import pagina_cap_transferencia as cap_mod

    cap = next(c for c in V.capitulos() if c.ident == "transferencia")
    return cap_mod.render(C.Dados(pasta=C.DADOS), cap)


def test_capitulo_registrado_depois_de_turnos():
    ids = [c.ident for c in V.capitulos()]
    assert ids.index("transferencia") == ids.index("turnos") + 1


def test_capitulo_sem_travessao_e_com_figuras(html):
    assert "—" not in html
    for nome in ("tr_sankey", "tr_sankey_mudou", "tr_dispersao", "tr_ufs"):
        assert f'id="fig-{nome}"' in html
    assert "fraude" not in html.lower()
    assert "Pede explicação, não prova" in html


def test_numeros_do_capitulo_saem_do_json(html, T):
    r = T["resposta"]
    assert C.num(r["liquido_por_100_lula"], 0) + " de 100" in html
    assert C.num(r["explica_pp"], 2) + " pp" in html
    assert C.inteiro(T["contabilidade"]["disponiveis"]) in html


def test_sankey_sem_espessura_minima(html):
    i = html.index('id="fig-tr_sankey"')
    corpo = html[i : html.index("</figure>", i)]
    fitas = re.findall(r'data-votos="(\d+)" data-esp="([\d.]+)"', corpo)
    assert len(fitas) == len(P.ORIGENS) * len(P.DESTINOS)
    # Uma escala só: espessura = votos × px por voto, até o arredondamento de 3 casas do atributo.
    v_max, e_max = max(((int(v), float(e)) for v, e in fitas), key=lambda x: x[0])
    escala = e_max / v_max
    assert all(abs(float(e) - int(v) * escala) < 2e-3 for v, e in fitas)
    # Sem espessura mínima: há fita com menos de meio pixel.
    assert min(float(e) for _v, e in fitas) < 0.5
