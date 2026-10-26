"""Transferência 1º → 2º turno: ajuste IPF, regressão ecológica, transcrições e capítulo."""

import json
import re

import numpy as np
import pytest
from apuracao_2t_2026 import pagina_comum as C
from apuracao_2t_2026 import pagina_view as V
from apuracao_2t_2026 import transferencia_cruzamento as CZ
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


def test_ras_fixas_mantem_as_fixas_e_bate_as_margens():
    prior = np.array([[5.0, 1.0, 2.0], [2.0, 2.0, 2.0], [1.0, 3.0, 4.0]])
    linhas = np.array([10.0, 6.0, 8.0])
    colunas = np.array([9.0, 7.0, 8.0])
    fixa = np.zeros((3, 3))
    livre = np.ones((3, 3), dtype=bool)
    fixa[0, 1], livre[0, 1] = 0.0, False  # zero estrutural
    fixa[1, 0], livre[1, 0] = 0.5, False  # célula fixa positiva
    M, _it, desvio = I.ras_fixas(prior, linhas, colunas, fixa, livre)
    assert desvio < 1e-9
    assert np.allclose(M.sum(1), linhas) and np.allclose(M.sum(0), colunas)
    assert M[0, 1] == 0.0 and M[1, 0] == 0.5


def test_ras_fixas_recusa_fixo_maior_que_a_margem():
    fixa = np.zeros((2, 2))
    fixa[0, 0] = 5.0
    livre = np.ones((2, 2), dtype=bool)
    livre[0, 0] = False
    with pytest.raises(ValueError):
        I.ras_fixas(
            np.ones((2, 2)), np.array([6.0, 2.0]), np.array([4.0, 4.0]), fixa, livre
        )


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
    # O cenário só troca a natureza das duas células de cruzamento.
    assert P.tipo_elo("lula", "flavio", "zero") == "zero"
    assert P.tipo_elo("flavio", "lula", "estimado") == "estimado"
    assert P.tipo_elo("lula", "lula", "zero") == "medido"


def test_cenarios_de_cruzamento_declarados():
    cen = P.cenarios_cruzamento()
    assert tuple(cen) == P.ORDEM_CRUZAMENTO and P.PADRAO_CRUZAMENTO in cen
    assert cen["sem"]["lula_para_flavio"] == cen["sem"]["flavio_para_lula"] == 0
    assert cen["um"]["lula_para_flavio"] == cen["um"]["flavio_para_lula"] == 0.01
    assert cen["dois"]["lula_para_flavio"] == cen["dois"]["flavio_para_lula"] == 0.02
    # O das pesquisas é a média da onda mais recente de cada instituto (Nexus 24/10 e Quaest 21/10).
    nx = P.LINHAS[("nexus_24", 23)]
    qu = P.LINHAS[("quaest_21", 20)]
    lf = (nx["lula"]["F"] / 99.5 + qu["lula"]["F"] / 99) / 2
    fl = (nx["flavio"]["L"] / 99.5 + qu["flavio"]["L"] / 99) / 2
    assert abs(cen["pesquisas"]["lula_para_flavio"] - lf) < 1e-9
    assert abs(cen["pesquisas"]["flavio_para_lula"] - fl) < 1e-9


def test_agrega_junta_brancos_e_nulos_sem_perder_voto():
    rng = np.random.default_rng(5)
    M = rng.uniform(0, 10, size=(len(P.ORIGENS), len(P.DESTINOS)))
    F = CZ.agrega(M)
    assert F.shape == (len(CZ.ORIG_FIG), len(CZ.DEST_FIG))
    assert abs(F.sum() - M.sum()) < 1e-9
    ib = P.ORIGENS.index("brancos"), P.ORIGENS.index("nulos")
    assert abs(F[CZ.ORIG_FIG.index("bn")].sum() - M[list(ib)].sum()) < 1e-9


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
    assert T["ipf"]["central"]["cenario_cruzamento"] == "sem"
    assert (
        n["medido"]["elos"] == 26
        and n["zero"]["elos"] == 2
        and n["regressao"]["elos"] == 4
        and n["estimado"]["elos"] == 18
    )
    assert abs(sum(x["pct_votos"] for x in n.values()) - 100) < 1e-6


# ------------------------------------------------------------------ cenários de cruzamento


def test_cada_cenario_bate_as_duas_urnas_e_fixa_o_cruzamento(T):
    cz = T["cruzamento"]
    o = T["margens"]["nacional"]["origens"]
    dest = T["margens"]["nacional"]["destinos"]
    assert cz["ordem"] == list(P.ORDEM_CRUZAMENTO)
    for k in cz["ordem"]:
        c = cz["cenarios"][k]
        assert c["confere"]["linhas_max_desvio_votos"] < 1, k
        assert c["confere"]["colunas_max_desvio_votos"] < 1, k
        M = c["matriz"]
        # Aptos = válidos + brancos + nulos + abstenção: cada coluna bate a urna do 2º turno.
        for b in P.DESTINOS:
            assert (
                abs(sum(M[a][b] for a in P.ORIGENS) - dest[b])
                <= 1 + len(P.ORIGENS) * 0.5
            )
        # As duas células ficam exatamente na fração da base declarada pelo cenário.
        assert (
            abs(M["lula"]["flavio"] / o["lula"] * 100 - c["lula_para_flavio_pct"])
            < 0.01
        )
        assert (
            abs(M["flavio"]["lula"] / o["flavio"] * 100 - c["flavio_para_lula_pct"])
            < 0.01
        )
        for a in P.ORIGENS:
            assert abs(sum(c["pct_origem"][a].values()) - 100) < 1e-2, (k, a)
        for b in P.DESTINOS:
            assert abs(sum(c["pct_destino"][a][b] for a in P.ORIGENS) - 100) < 1e-2, (
                k,
                b,
            )
        fig = c["figura"]
        tot_fig = sum(sum(fig["votos"][a].values()) for a in fig["origens"])
        assert (
            abs(tot_fig - sum(sum(M[a].values()) for a in P.ORIGENS))
            < len(P.ORIGENS) * 5
        )
    sem = cz["cenarios"]["sem"]["matriz"]
    assert sem["lula"]["flavio"] == 0 and sem["flavio"]["lula"] == 0


def test_padrao_compativel_e_declarado(T):
    cz = T["cruzamento"]
    pc = cz["padrao_compativel"]
    assert cz["padrao"] == "sem"
    assert pc["margens"] and pc["linhas_publicadas"] and pc["ufs_ajustadas"] == 28
    zero = [
        x
        for x in cz["linhas_publicadas"]
        if x["lula_para_flavio_pct"] == 0 and x["flavio_para_lula_pct"] == 0
    ]
    assert [x["instituto"] for x in zero] == ["Quaest"]


def test_o_que_nao_muda_entre_os_cenarios(T):
    cz = T["cruzamento"]
    nm = cz["comparacao"]["nao_muda"]
    # A linha de quem faltou no 1º turno é a mesma em todos.
    assert nm["voltaram"][0] == nm["voltaram"][1]
    assert nm["voltaram_lula_pct"][0] == nm["voltaram_lula_pct"][1]
    assert nm["explica_pp"][0] == nm["explica_pp"][1]
    # Terceira via + branco e nulo + saldo do cruzamento: quase o mesmo (menos de 0,5%).
    lo, hi = nm["lula_de_terceira_bn_e_cruzamento"]
    assert (hi - lo) / lo < 0.005
    mp = cz["comparacao"]["muda_pouco"]["terceira_flavio_pct"]
    assert mp[1] - mp[0] < 2
    for k in cz["ordem"]:
        m = cz["cenarios"][k]["metricas"]
        assert (
            abs(
                m["cruzamento_liquido_para_lula"]
                - (m["flavio_para_lula"] - m["lula_para_flavio"])
            )
            < 1
        )


def test_equilibrio_cresce_com_o_alvo(T):
    eq = [e for e in T["pesquisas"]["terceira_via_2t"]["equilibrio"] if e]
    assert len(eq) == 2
    assert 0 < eq[0]["flavio_para_lula_pct"] < eq[1]["flavio_para_lula_pct"]
    for e in eq:
        assert abs(e["terceira_flavio_pct"] - e["alvo_pct"]) < 0.05
    padrao = T["cruzamento"]["cenarios"]["sem"]["metricas"]["terceira"]["flavio_pct"]
    assert padrao < eq[0]["alvo_pct"]


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
    for nome in ("tr_sankey", "tr_dispersao", "tr_ufs"):
        assert f'id="fig-{nome}"' in html
    assert "fraude" not in html.lower()
    assert "Pede explicação, não prova" in html
    assert "estimativa, não medição" in html.lower()
    assert "Como ler." in html


def test_capitulo_vai_do_simples_ao_tecnico(html):
    ordem = [
        "A conta que as duas urnas fecham",
        "A resposta em três números",
        "Quatro cenários para o cruzamento entre as bases",
        "Quem voltou a votar: a regressão sobre as urnas",
        "Limites do capítulo",
    ]
    pos = [html.index(x) for x in ordem]
    assert pos == sorted(pos)


def test_botoes_trocam_os_quatro_cenarios_e_sem_script_fica_o_padrao(html, T):
    cz = T["cruzamento"]
    i = html.index('id="fig-tr_sankey"')
    fig = html[i : html.index("</figure>", i)]
    for k in cz["ordem"]:
        assert f'data-alt="{k}"' in fig
        blocos = re.findall(rf'<div data-alt-show="{k}"( hidden)?>', fig)
        assert blocos, k
        # O padrão aparece sem script; os outros ficam escondidos.
        assert all((b == "") == (k == cz["padrao"]) for b in blocos), k
    assert "<noscript><p" in html and "cenário padrão" in html
    assert fig.count('class="table-scroll tr-cem"') == len(cz["ordem"])


def test_rotulo_na_fita_para_toda_fita_acima_do_limiar(html, T):
    """No desenho largo do padrão, toda fita de meio milhão ou mais leva rótulo; as outras vão para a lista."""
    cen = T["cruzamento"]["cenarios"]["sem"]
    fig = cen["figura"]
    lim = fig["limiar_rotulo_votos"]
    acima = sum(
        1 for a in fig["origens"] for b in fig["destinos"] if fig["votos"][a][b] >= lim
    )
    i = html.index('<div data-alt-show="sem">')
    larga = html[i : html.index('<div class="fig-estreita">', i)]
    assert larga.count('class="rot-fita"') == acima
    for a in fig["origens"]:
        for b in fig["destinos"]:
            v = fig["votos"][a][b]
            if v >= lim:
                p_ = C.num(
                    fig["pct_origem"][a][b], 0 if fig["pct_origem"][a][b] >= 9.95 else 1
                )
                assert f"{C.num(v / 1e6, 1)} mi · {p_}%" in larga, (a, b)


def test_numeros_do_capitulo_saem_do_json(html, T):
    r = T["resposta"]
    assert C.num(r["liquido_por_100_lula"], 0) + " de 100" in html
    assert C.num(r["explica_pp"], 2) + " pp" in html
    assert C.inteiro(T["contabilidade"]["disponiveis"]) in html


def test_sankey_sem_espessura_minima(html, T):
    i = html.index('id="fig-tr_sankey"')
    corpo = html[i : html.index("</figure>", i)]
    fitas = re.findall(r'data-votos="(\d+)" data-esp="([\d.]+)"', corpo)
    esperado = sum(
        1
        for c in T["cruzamento"]["cenarios"].values()
        for a in c["figura"]["origens"]
        for b in c["figura"]["destinos"]
        if c["figura"]["votos"][a][b] > 0
    )
    assert len(fitas) == esperado
    # Uma escala só: espessura = votos × px por voto, até o arredondamento de 3 casas do atributo.
    v_max, e_max = max(((int(v), float(e)) for v, e in fitas), key=lambda x: x[0])
    escala = e_max / v_max
    assert all(abs(float(e) - int(v) * escala) < 2e-3 for v, e in fitas)
    # Sem espessura mínima: há fita com menos de meio pixel.
    assert min(float(e) for _v, e in fitas) < 0.5
