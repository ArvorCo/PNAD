"""Mistura gaussiana dos dois turnos: regra de k, convergência, ordem, equivalência afim,
voto contra vizinhas, arquivo pesado e contrato do JSON publicado."""

import gzip
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from apuracao_2t_2026 import anomalia_base as ab
from apuracao_2t_2026 import anomalia_descricao as ad
from apuracao_2t_2026 import anomalia_linhas as al
from apuracao_2t_2026 import anomalia_motor as am
from apuracao_2t_2026 import anomalia_voto as av
from apuracao_2t_2026 import secoes_voto
from sklearn.metrics import adjusted_rand_score

ROOT = Path(__file__).resolve().parents[1]
JSON = ROOT / "analysis/apuracao_2t_2026/dados/anomalia_ml.json"
MEMO = ROOT / "analysis/apuracao_2t_2026/dados/anomalia_ml.md"


def _linhas_bic(bic, icl=None):
    icl = icl or [b + 10 for b in bic]
    return [
        {"k": k, "bic": b, "icl": i}
        for k, b, i in zip(range(2, 2 + len(bic)), bic, icl, strict=True)
    ]


# ---------------------------------------------------------------- regra de k


def test_joelho_do_bic_na_curva_construida():
    # quedas 400, 300, 100, 10, ...: total 821, 5% = 41,05; a primeira abaixo é 5 → 6
    e = am.escolher_k(_linhas_bic([1000, 600, 300, 200, 190, 185, 182, 180, 179]))
    assert e["k_joelho_bic"] == 5
    assert e["k_escolhido"] == 5
    assert e["origem"] == "joelho_bic"
    assert e["queda_total"] == 821


def test_sem_joelho_cai_no_icl():
    bic = [1000 - 100 * i for i in range(9)]  # cada queda é 12,5% da total
    icl = [50, 40, 30, 20, 10, 5, 1, 3, 9]  # mínimo em k = 8
    e = am.escolher_k(_linhas_bic(bic, icl))
    assert e["k_joelho_bic"] is None
    assert e["k_min_icl"] == 8
    assert e["k_escolhido"] == 8
    assert e["origem"] == "min_icl"


def test_k_fica_entre_tres_e_dez():
    # joelho em k = 2 (a primeira queda é 1% da total) sobe para 3
    e = am.escolher_k(_linhas_bic([100, 99, 50, 10, 0, -10, -20, -30, -40]))
    assert e["k_joelho_bic"] == 2
    assert e["k_escolhido"] == 3
    assert "limite declarado" in e["regra"]
    # BIC crescente: sem queda total positiva, vale o ICL, também limitado
    e = am.escolher_k(
        _linhas_bic([1, 2, 3, 4, 5, 6, 7, 8, 9], [0, 1, 2, 3, 4, 5, 6, 7, 8])
    )
    assert e["k_joelho_bic"] is None and e["k_min_icl"] == 2
    assert e["k_escolhido"] == 3


# ---------------------------------------------------------------- dados sintéticos


def _nuvens(n=600, d=4, sep=8.0, semente=1):
    rng = np.random.default_rng(semente)
    centros = rng.normal(0, sep, size=(3, d))
    rot = np.repeat(np.arange(3), n // 3)
    x = centros[rot] + rng.normal(0, 1, size=(len(rot), d))
    return x, rot


def test_convergencia_exigida_e_dobra_do_max_iter():
    x, _ = _nuvens()
    base = am.partida(x, 3, 7, "kmeans")
    assert base["convergiu"] and base["dobras"] == 0
    n = base["iteracoes"]
    assert n >= 2
    meio = math.ceil(n / 2)
    dobrada = am.partida(x, 3, 7, "kmeans", max_iter=meio)
    assert dobrada["convergiu"]
    assert dobrada["dobras"] >= 1
    assert dobrada["max_iter_usado"] >= n
    assert dobrada["iteracoes"] == n
    # nenhuma partida converge: nada é escolhido
    sem = [am.partida(x, 3, s, "kmeans", tol=1e-30, max_iter=1) for s in (1, 2)]
    assert not any(p["convergiu"] for p in sem)
    with pytest.raises(RuntimeError):
        am.melhor(sem, am.INITS)


def test_partida_degenerada_fica_fora_da_escolha():
    rng = np.random.default_rng(2)
    # um grupo com uma coluna exatamente constante (como zero branco no 2T)
    a = np.column_stack([np.zeros(300), rng.normal(5, 1, 300)])
    b = rng.normal(0, 1, size=(300, 2)) + np.array([8.0, -5.0])
    x = np.vstack([a, b])
    p = am.partida(x, 2, 3, "kmeans")
    assert p["convergiu"] and p["degenerada"]
    assert p["min_autovalor"] < am.LIMIAR_DEGENERADA
    with pytest.raises(RuntimeError):
        am.melhor([p], am.INITS)
    ok = am.partida(_nuvens()[0], 3, 3, "kmeans")
    assert not ok["degenerada"]
    assert am.melhor([p, ok], am.INITS) is ok


def test_ajuste_na_base_converge_e_recupera_os_grupos():
    x, rot = _nuvens()
    aj = am.ajustar_base(x, 3, sementes=(1, 2), paralelo=False)
    assert aj.gm.converged_
    assert len(aj.log) == 4 and all(r["convergiu"] for r in aj.log)
    assert adjusted_rand_score(rot, am.prever(aj.gm, x)) == pytest.approx(1.0)


def test_ordem_estavel_por_lula2():
    rot = np.array([0, 0, 1, 1, 2, 2])
    lula2 = np.array([50.0, 52, 10, 12, 30, 31])
    mapa = am.ordem_por_lula2(rot, lula2, 3)
    assert mapa.tolist() == [2, 0, 1]
    # a mesma partição com rótulos trocados dá os mesmos ids finais
    trocado = np.array([2, 2, 0, 0, 1, 1])
    m2 = am.ordem_por_lula2(trocado, lula2, 3)
    assert (m2[trocado] == mapa[rot]).all()


def test_postos_do_atipico_e_segundo_colocado():
    ll = [-5.0, -9.0, -7.0, -3.0]
    dp = [1.0, 4.0, 3.0, 0.5]
    postos = am.postos_anomalo(ll, dp)
    assert postos[0]["id"] == 1 and postos[0]["soma_postos"] == 0
    assert postos[1]["id"] == 2 and postos[1]["soma_postos"] == 2


def _df_sintetico(n=900, semente=3):
    """Seções com votos inteiros nos dois turnos, em três perfis bem separados."""
    rng = np.random.default_rng(semente)
    perfis = np.array(
        [
            [0.55, 0.15, 0.05, 0.02, 0.03, 0.62, 0.20, 0.01, 0.02],
            [0.15, 0.55, 0.05, 0.02, 0.03, 0.20, 0.62, 0.01, 0.02],
            [0.30, 0.30, 0.15, 0.03, 0.04, 0.40, 0.38, 0.02, 0.03],
        ]
    )
    rot = np.repeat(np.arange(3), n // 3)
    aptos = rng.integers(250, 400, size=len(rot))
    linhas = {}
    for j, c in enumerate(ab.COLUNAS):
        p = np.clip(perfis[rot, j] + rng.normal(0, 0.012, len(rot)), 0.001, None)
        linhas[c] = np.round(p * aptos).astype(int)
    df = pd.DataFrame(
        {
            "aptos_1": aptos,
            "aptos_2": aptos,
            **{f"{p}_1": linhas[f"{p}1"] for p in ab.PARTES_1T},
            **{f"{p}_2": linhas[f"{p}2"] for p in ab.PARTES_2T},
        }
    )
    return df, rot


def test_equivalencia_afim_niveis_e_deltas():
    df, rot = _df_sintetico()
    f = ab.fracoes(df)
    xn = ab.matriz(f, ab.COLUNAS)
    xd = ab.matriz(f, ab.COLUNAS_DELTA)
    # deltas em pontos: transformação unitriangular, determinante 1
    for init in ("random", "kmeans"):
        a = am.partida(xn, 3, 11, init)
        b = am.partida(xd, 3, 11, init)
        ra, rb = am.prever(a["gm"], xn), am.prever(b["gm"], xd)
        assert adjusted_rand_score(ra, rb) == pytest.approx(1.0)
        if init == "kmeans":  # a inicialização aleatória pode parar em ótimo local
            assert adjusted_rand_score(rot, ra) == pytest.approx(1.0)
        assert b["loglik_media"] == pytest.approx(a["loglik_media"], abs=1e-4)
    # cada enquadramento padronizado: a diferença é o log do determinante
    zn, _, _ = ab.padronizar(xn)
    zd, _, _ = ab.padronizar(xd)
    a = am.partida(zn, 3, 11, "random")
    b = am.partida(zd, 3, 11, "random")
    assert adjusted_rand_score(am.prever(a["gm"], zn), am.prever(b["gm"], zd)) == 1.0
    logdet = ab.logdet_transformacao(f)
    assert b["loglik_media"] == pytest.approx(a["loglik_media"] - logdet, abs=1e-4)


def test_fracoes_e_comparecimento_implicito():
    df, _ = _df_sintetico(n=30)
    f = ab.fracoes(df)
    soma1 = sum(df[f"{p}_1"] for p in ab.PARTES_1T)
    assert np.allclose(f["comp1"], 100 * soma1 / df["aptos_1"])
    assert np.allclose(f["d_comp"], f["comp2"] - f["comp1"])
    assert np.allclose(f["d_lula"], f["lula2"] - f["lula1"])


def test_unir_conta_exclusoes_por_motivo():
    def t(linhas):
        base = dict.fromkeys(
            (
                "comparecimento",
                "modelo_urna",
                "tipo_arquivo",
                "tipo_urna",
                "n_cargas",
                *ab.VOTOS,
            ),
            0,
        )
        return pd.DataFrame(
            [
                {**base, "uf": u, "mun": "00001", "zona": 1, "secao": s, "aptos": a}
                for u, s, a in linhas
            ]
        )

    t1 = t([("SP", 1, 300), ("SP", 2, 20), ("ZZ", 3, 300), ("SP", 4, 300)])
    t2 = t([("SP", 1, 300), ("SP", 2, 300), ("ZZ", 3, 300), ("SP", 5, 300)])
    df, excl = ab.unir(t1, t2)
    assert len(df) == 1
    assert excl["exterior"] == 1
    assert excl["sem_par"] == 2
    assert excl["sem_par_so_1t"] == 1 and excl["sem_par_so_2t"] == 1
    assert excl["aptos_menor_30"] == 1


def test_pontuar_parcela_abaixo():
    x, _ = _nuvens()
    gm = am.partida(x, 3, 1, "kmeans")["gm"]
    s, p = am.pontuar(gm, x)
    assert p.min() == 0 and p.max() < 1
    ordem = np.argsort(s)
    assert (np.diff(p[ordem]) >= 0).all()


def test_percentuais_somam_cem():
    assert sum(ad.pct_maior_resto([1, 1, 1])) == pytest.approx(100)
    assert sum(ad.pct_maior_resto([497796 - 4200, 3100, 1100])) == pytest.approx(100)


def test_rotulo_sem_travessao_e_com_numeros():
    pais = {c: (10.0, 2.0) for c, _n, _u in ad.DESCRITORES}
    centro = {c: 10.0 for c, _n, _u in ad.DESCRITORES} | {"lula2": 20.0, "d_comp": 5.0}
    r = ad.rotulo(centro, pais)
    assert "—" not in r
    assert r.startswith("Lula no 2º turno: 20,0% do eleitorado")
    assert "variação do comparecimento entre turnos: −5,0" not in r
    assert ad.rotulo(dict.fromkeys(centro, 10.0), pais).startswith("perto da média")
    curto = ad.rotulo_curto(centro, pais)
    assert curto.startswith("Lula no 2º turno muito acima do país")
    assert "muito abaixo do país" in curto
    moderado = dict.fromkeys(centro, 10.0) | {"outros1": 11.5}  # z = 0,75
    assert ad.rotulo_curto(moderado, pais) == "Terceira via no 1º turno acima do país"


def test_descricao_do_grupo_e_leitura_do_atipico():
    df, rot = _df_sintetico(n=900)
    f = ab.fracoes(df)
    d = pd.concat([df, f], axis=1)
    n = len(d)
    d["uf"] = np.where(np.arange(n) % 2, "SP", "BA")
    d["regiao"] = np.where(d["uf"] == "SP", "Sudeste", "Nordeste")
    d["aptos_2"] = np.where(rot == 2, 80, 300)  # o grupo 2 é de seções pequenas
    d["tamanho"] = ab.faixa_aptos(d["aptos_2"])
    d["modelo"] = "UE2020"
    d["grupo"] = rot
    d["score"] = -np.arange(n, dtype=float)
    d["maha"] = 1.0
    d["escore"] = 0
    d["tipo_arquivo_2"] = 1
    d["contingencia"] = pd.array([False] * n, dtype="boolean")
    d["mudanca"] = False
    for col, _ in ad.SINAIS_SEIS:
        d[col] = pd.array([False] * n, dtype="boolean")
    z, media, dp = ab.padronizar(ab.matriz(f, ab.COLUNAS))
    pais = ad.referencia_pais(f)
    c = ad.componente(
        d, 2, np.eye(9), 0.33, z[rot == 2].mean(0), (media, dp), pais, 33.33
    )
    assert c["secoes"] == 300 and c["pequenas_pct"] == 100
    assert c["centro_delta_pp"]["comp"] == pytest.approx(
        c["comp2_pct"] - c["comp1_pct"], abs=0.01
    )
    assert set(c["dispersao_relativa"]) == set(ab.COLUNAS)
    sel = rot == 2
    contra = ad.atipico_contra(d, sel)
    assert contra["tamanho"][0]["tamanho"] == "30 a 99"
    assert contra["tamanho"][0]["pct_da_faixa"] == 100
    assert contra["cramer_v"]["tamanho"] == pytest.approx(1.0)
    assert contra["cramer_v"]["regiao"] < 0.05
    texto = ad.leitura(c, contra)
    assert "—" not in texto and "30 a 99 aptos" in texto
    conc = ad.conclusao(c, contra, {"did_vs_1t_pp": -0.05, "ic95_did": [-0.2, 0.1]})
    assert "não é geografia; é, em boa parte, tamanho de seção" in conc
    assert "com o zero dentro" in conc
    conc = ad.conclusao(c, contra, {"did_vs_1t_pp": 1.0, "ic95_did": [0.5, 1.5]})
    assert "sem o zero" in conc and "não prova nada" in conc
    comps = [{"id": 0, "rotulo_curto": "A"}, {"id": 1, "rotulo_curto": "A"}]
    ad.rotulos_unicos(comps)
    assert [x["rotulo_curto"] for x in comps] == ["A (grupo 0)", "A (grupo 1)"]


# ---------------------------------------------------------------- voto


def _quadro_votos(semente=5):
    rng = np.random.default_rng(semente)
    linhas = []
    for m in range(40):
        for s in range(12):
            fl1, lu1 = rng.integers(60, 140, 2)
            fl2 = fl1 + rng.integers(0, 20)
            lu2 = lu1 + rng.integers(0, 20)
            linhas.append(
                {
                    "uf": "MG",
                    "mun": f"{m:05d}",
                    "zona": 1,
                    "secao": s,
                    "flavio_1": fl1,
                    "lula_1": lu1,
                    "flavio_2": fl2 + (25 if s < 2 else 0),
                    "lula_2": lu2,
                    "comparecimento_2": fl2 + lu2 + 10,
                }
            )
    d = pd.DataFrame(linhas)
    return d, pd.Series(d["secao"] < 2, index=d.index)


def test_voto_confere_com_comparar_e_ic_cobre_a_estimativa():
    d, mask = _quadro_votos()
    v = av.voto(d, mask, reps=500)
    ref = secoes_voto.comparar(av.quadro_voto(d), mask)
    assert v["fatia_f2_vs_vizinhas_pp"] == pytest.approx(
        ref["dif_fatia_flavio_vs_vizinhas_pp"], abs=0.006
    )
    assert v["did_vs_1t_pp"] == pytest.approx(ref["did_fatia_flavio_pp"], abs=0.006)
    lo, hi = v["ic95"]
    assert lo < v["fatia_f2_vs_vizinhas_pp"] < hi
    assert v["fatia_f2_vs_vizinhas_pp"] > 0  # o grupo tem 25 votos a mais de Flávio
    assert v["n"] == 80 and v["n_vizinhas"] == 400 and v["n_municipios"] == 40


# ---------------------------------------------------------------- arquivo pesado


def test_arquivo_pesado_reprodutivel(tmp_path):
    linhas = [
        ["SP", "71072", 1, 10, 0, -3.21, 0.0123, 1],
        ["SP", "71072", 1, 11, 2, 4.5, 0.9, 0],
    ]
    destino = tmp_path / "anomalia_secoes.json.gz"
    p1 = al.gravar(al.COLUNAS, linhas, destino)
    b1 = destino.read_bytes()
    p2 = al.gravar(al.COLUNAS, linhas, destino)
    assert destino.read_bytes() == b1 and p1["sha256"] == p2["sha256"]
    assert gzip.decompress(b1).startswith(b'{"colunas":')
    A = {al.CHAVE: {**p1, "arquivo": str(destino)}}
    b = al.exigir(A)
    assert b["disponivel"] and b["linhas"] == linhas
    A_falta = {al.CHAVE: {**p1, "arquivo": str(tmp_path / "nao_existe.gz")}}
    assert not al.bloco(A_falta)["disponivel"]
    with pytest.raises(FileNotFoundError):
        al.exigir(A_falta)


# ---------------------------------------------------------------- contrato do JSON


@pytest.fixture(scope="module")
def publicado():
    if not JSON.exists():
        pytest.skip("anomalia_ml.json ainda não foi gerado")
    return json.loads(JSON.read_text(encoding="utf-8"))


def test_contrato_do_json(publicado):
    A = publicado
    for chave in (
        "gerado_em",
        "rotulo",
        "fonte",
        "universo",
        "features",
        "bic",
        "k_escolhido",
        "k_joelho_bic",
        "k_min_icl",
        "regra",
        "ajuste",
        "kmeans",
        "componentes",
        "mais_anomalo",
        "menos_provaveis",
        "cluster_regiao",
        "cluster_uf",
        "cluster_modelo",
        "cramer_v_regiao",
        "cramer_v_uf",
        "cramer_v_modelo",
        "pca",
        "secoes_arquivo",
    ):
        assert chave in A, chave
    k = A["k_escolhido"]
    assert 3 <= k <= 10
    assert [b["k"] for b in A["bic"]] == list(range(2, 11))
    assert all(b["convergiu"] for b in A["bic"])
    assert A["ajuste"]["convergiu"] is True
    assert all(
        r["convergiu"] or r["loglik_media"] < A["ajuste"]["loglik_media"]
        for r in A["ajuste"]["sementes"]
    )
    assert A["features"]["colunas"] == list(ab.COLUNAS)
    assert set(A["features"]["padronizacao"]) == set(ab.COLUNAS)
    comps = A["componentes"]
    assert [c["id"] for c in comps] == list(range(k))
    assert sum(c["pct_secoes"] for c in comps) == pytest.approx(100, abs=1e-6)
    assert sum(c["secoes"] for c in comps) == A["universo"]["secoes"]
    lula2 = [c["centro_pct_eleitorado"]["lula2"] for c in comps]
    assert lula2 == sorted(lula2)
    curtos = [c["rotulo_curto"] for c in comps]
    assert len(set(curtos)) == len(curtos)
    assert ma_tem_textos(A)
    for c in comps:
        assert set(c["centro_pct_eleitorado"]) == set(ab.COLUNAS)
        assert {"comp", "lula", "flavio", "brancos", "nulos"} <= set(
            c["centro_delta_pp"]
        )
        assert "—" not in c["rotulo"]
    ma = A["mais_anomalo"]
    assert 0 <= ma["id"] < k and ma["segundo"]["id"] != ma["id"]
    assert ma["segundo"]["diferenca_postos"] >= 0
    assert 0 < len(ma["amostras"]) <= 50
    assert all(s["grupo"] == ma["id"] for s in ma["amostras"])
    assert all(s["link"].startswith("politizese.html#uf=") for s in ma["amostras"])
    assert len(A["menos_provaveis"]) == 50
    assert [r["k"] for r in A["kmeans"]["niveis"]] == list(range(2, 11))
    assert set(A["kmeans"]["ari_com_mistura_k_estrela"]) == {
        "niveis",
        "niveis_e_deltas",
    }
    assert A["pca"]["colunas"][:5] == ["x", "y", "cluster", "top", "uf"]
    assert len(A["pca"]["elipses"]) == k
    ex = A["universo"]["excluidas"]
    assert {"exterior", "sem_par", "aptos_menor_30", "outros"} <= set(ex)


def ma_tem_textos(A):
    ma = A["mais_anomalo"]
    return all(isinstance(ma.get(k), str) and ma[k] for k in ("leitura", "conclusao"))


def test_ponteiro_do_arquivo_pesado(publicado):
    p = publicado["secoes_arquivo"]
    assert p["colunas"] == al.COLUNAS
    assert p["n_linhas"] == publicado["universo"]["secoes"]
    arq = ROOT / p["arquivo"]
    if not arq.exists():
        pytest.skip("arquivo pesado fora desta máquina (fora do git, por desenho)")
    dados = arq.read_bytes()
    assert hashlib.sha256(dados).hexdigest() == p["sha256"]
    assert len(dados) == p["bytes"]
    b = json.loads(gzip.decompress(dados))
    assert len(b["linhas"]) == p["n_linhas"]
    an = [r[7] for r in b["linhas"]]
    ma = publicado["mais_anomalo"]["id"]
    comp = next(c for c in publicado["componentes"] if c["id"] == ma)
    assert sum(an) == comp["secoes"]
    assert all(r[0] == r[0].upper() and len(r[1]) == 5 for r in b["linhas"][:1000])


def test_memorando_sem_travessao(publicado):
    texto = MEMO.read_text(encoding="utf-8")
    assert "—" not in texto
    assert "fraude" not in texto.lower()
    assert "não é irregularidade" in texto
    assert "—" not in json.dumps(publicado, ensure_ascii=False)
