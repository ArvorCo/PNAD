"""Bloco "Seções com zero voto" do capítulo Grupos (dossiê do 2º turno de 2026).

Regra do tipo de local (sempre), degradação sem ``zeros.json`` (sempre) e, quando o
JSON gerado por ``scripts/apuracao-2t-2026-zeros.py`` existe, o contrato dele e o
bloco renderizado com os números conferidos.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from pathlib import Path

import pytest
from apuracao_2t_2026 import pagina_cap_anomalia as CA
from apuracao_2t_2026 import pagina_fig_zeros as FZ
from apuracao_2t_2026 import pagina_fig_zeros_cauda as FC
from apuracao_2t_2026 import zeros_base as ZB
from apuracao_2t_2026 import zeros_cauda as ZC
from apuracao_2t_2026 import zeros_dados as ZD
from apuracao_2t_2026.pagina_comum import DADOS, Dados
from apuracao_2026.pagina_comum import Capitulo

ROOT = Path(__file__).resolve().parents[1]
REAL = DADOS / "zeros.json"
TEM_REAL = REAL.exists()
TEM_CAPITULO = TEM_REAL and (DADOS / "anomalia_ml.json").exists()
MODULOS = [
    "scripts/apuracao_2t_2026/zeros_base.py",
    "scripts/apuracao_2t_2026/zeros_dados.py",
    "scripts/apuracao_2t_2026/pagina_fig_zeros.py",
    "scripts/apuracao_2t_2026/zeros_cauda.py",
    "scripts/apuracao_2t_2026/zeros_cauda_secao.py",
    "scripts/apuracao_2t_2026/pagina_fig_zeros_cauda.py",
    "scripts/apuracao-2t-2026-zeros.py",
]
CHAVES_FICHA = {
    "uf",
    "mun",
    "municipio",
    "zona",
    "secao",
    "local",
    "tipo",
    "aptos",
    "comparecimento",
    "lula",
    "flavio",
    "t1",
    "t2022",
    "politize_bolsonaro22_2t_pct_validos",
    "link",
}
SELOS = (
    "Relato da imprensa",
    "Verificado",
    "Inferência",
    "Achado contrário",
    "Juízo editorial",
)


def texto_publico(h: str) -> str:
    return re.sub(r"<[^>]+>", " ", h)


def cap() -> Capitulo:
    return Capitulo(
        "anomalia",
        "10",
        "Grupos",
        "Os grupos de seções nos dois turnos",
        (),
        lambda d: CA.render(d, cap()),
    )


# ------------------------------------------------------------------ regra


@pytest.mark.parametrize(
    ("local", "uf", "municipio", "tipo"),
    [
        ("ALDEIA INDIGENA BOA VISTA", "AC", "Jordão", "aldeia_indigena"),
        (
            "E. M. INDÍGENA TIKUNA DECUNE",
            "AM",
            "São Paulo de Olivença",
            "aldeia_indigena",
        ),
        ("ESCOLA ESTADUAL TAPI ' ITAWA - ANEXO I", "MT", "x", "aldeia_indigena"),
        ("ESCOLA ESTADUAL TAPI  ITAWA - ANEXO I", "MT", "x", "aldeia_indigena"),
        ("ESCOLA ESTADUAL TAPIITAWA", "MT", "x", "aldeia_indigena"),
        ("ESCOLA TAMÃKÃYÃ", "AC", "Cruzeiro do Sul", "aldeia_indigena"),
        ("PRESÍDIO REGIONAL DE SAPÉ", "PB", "Sapé", "prisao"),
        ("CENTRO DE DETENÇÃO PROVISÓRIA - CDP", "CE", "Aquiraz", "prisao"),
        ("ESCOLA DO POVOADO SÃO JOSÉ", "MA", "Bacuri", "comunidade"),
        ("ESCOLA MUNICIPAL CORAÇÃO DE JESUS", "MA", "Alcântara", "comunidade"),
        ("ALDEIA X", "MA", "Alcântara", "aldeia_indigena"),
        ("E. M. LEONEL", "AM", "Juruá", "outro"),
        (None, "PA", "Moju", "outro"),
    ],
)
def test_tipo_local_pela_regra_declarada(local, uf, municipio, tipo):
    assert ZB.tipo_local(local, uf, municipio) == tipo


def test_regra_registra_a_origem_e_a_ordem():
    assert ZB.tipo_e_regra("ESCOLA X", "MA", "Turiaçu") == ("comunidade", "municipio")
    assert ZB.tipo_e_regra("VILA NOVA", "PA", "Moju") == ("comunidade", "nome")
    assert ZB.tipo_e_regra("E. M. LEONEL", "AM", "Juruá") == ("outro", None)
    assert ZB.ORDEM_TIPOS == ["aldeia_indigena", "prisao", "comunidade", "outro"]


def test_modulos_abaixo_de_mil_linhas():
    for m in MODULOS:
        assert (ROOT / m).read_text(encoding="utf-8").count("\n") < 1000, m


# ------------------------------------------------------------------ sem o JSON


def test_sem_json_o_bloco_fica_pendente(tmp_path):
    d = Dados(pasta=tmp_path)
    h = FZ.bloco(d)
    assert "Seções com zero voto" in h
    assert 'class="pendente" id="fig-an_zeros"' in h
    assert FZ.limites_itens(d) == []


# ------------------------------------------------------------------ contrato


@pytest.fixture(scope="module")
def Z():
    if not TEM_REAL:
        pytest.skip("zeros.json ainda não gerado")
    return json.loads(REAL.read_text(encoding="utf-8"))


def test_numeros_conferidos(Z):
    assert ZD.obtido(Z) == ZD.ESPERADO
    ZD.conferir(Z)


def test_recortes_e_exterior(Z):
    r = FZ.recorte(Z, 2026, 2, "direita")
    assert (r["secoes"], r["votos_adversario"]) == (106, 14_860)
    rl = FZ.recorte(Z, 2026, 2, "lula")
    assert (rl["secoes"], rl["votos_adversario"]) == (4, 296)
    assert Z["com_exterior"] == {"2026_2t_direita": 108, "2026_2t_lula": 6}
    assert {(x["ano"], x["turno"], x["lado"]) for x in Z["recortes"]} == {
        (a, t, lado)
        for a in (2022, 2026)
        for t in (1, 2)
        for lado in ("direita", "lula")
    }
    assert len(Z["exterior"]["recortes"]) == 8


def test_classificacoes_somam_a_lista(Z):
    pares = {
        "2026_2t_direita": ("lista_zero_flavio", 106),
        "2026_2t_lula": ("lista_zero_lula", 4),
        "2022_2t_direita": ("lista_zero_bolsonaro_2022_2t", 141),
    }
    for chave, (lista, n) in pares.items():
        tipos = Z["tipo_local"][chave]
        assert [x["tipo"] for x in tipos] == ZB.ORDEM_TIPOS
        assert sum(x["secoes"] for x in tipos) == n == len(Z[lista])
    t26 = Z["tipo_local"]["2026_2t_direita"]
    assert sum(x["votos_adversario"] for x in t26) == 14_860
    assert sum(x["secoes"] for x in Z["tipo_local"]["2026_1t_direita"]) == 79
    assert sum(x["secoes"] for x in Z["tipo_local"]["2022_1t_direita"]) == 160


def test_listas_completas(Z):
    zf, zl = Z["lista_zero_flavio"], Z["lista_zero_lula"]
    assert len(zf) == 106 and len(zl) == 4
    for x in [*zf, *zl]:
        assert set(x) >= CHAVES_FICHA, CHAVES_FICHA - set(x)
        assert x["uf"] != "ZZ" and x["local"]
        assert (
            x["link"]
            == f"politizese.html#uf={x['uf']}&zona={x['zona']}&secao={x['secao']}"
        )
    assert all(x["flavio"] == 0 for x in zf) and all(x["lula"] == 0 for x in zl)
    assert sum(x["lula"] for x in zf) == 14_860
    assert sum(x["flavio"] for x in zl) == 296
    chaves = [(x["uf"], x["mun"], x["zona"], x["secao"]) for x in zf]
    assert chaves == sorted(set(chaves))
    assert sum(1 for x in zf if x["t1"] and x["t1"]["flavio"] == 0) == 50


def test_geografia_soma(Z):
    assert sum(x["zero_direita_2026_2t"] for x in Z["por_uf"]) == 106
    assert sum(x["zero_direita_2022_2t"] for x in Z["por_uf"]) == 141
    assert sum(x["zero_direita_2026_2t"] for x in Z["por_regiao"]) == 106
    assert sum(x["zero_direita_2022_1t"] for x in Z["por_regiao"]) == 160
    pf = Z["zero_flavio"]["perfil"]
    assert sum(x["secoes"] for x in pf["aptos"]["faixas"]) == 106


def test_fontes_com_hash(Z):
    assert all(re.fullmatch(r"[0-9a-f]{64}", h) for h in Z["fontes"].values())
    leves = [
        "data/outputs/presidente_secao_2022.csv.gz",
        "docs/assets/politize/dados/indice.json",
    ]
    for rel in leves + list(Z["fontes_politize_zonas"]):
        arq = ROOT / rel
        if arq.exists():
            esperado = Z["fontes"].get(rel) or Z["fontes_politize_zonas"][rel]
            assert hashlib.sha256(arq.read_bytes()).hexdigest() == esperado, rel
    assert Z["conferencia_csv"].get("divergencias", []) == []
    assert Z["gerado_em"].endswith("Z") and Z["rotulo"]


def test_conferir_acusa_divergencia(Z):
    ruim = copy.deepcopy(Z)
    FZ.recorte(ruim, 2026, 2, "direita")["secoes"] = 105
    with pytest.raises(AssertionError, match="2026_2t_direita"):
        ZD.conferir(ruim)


# ------------------------------------------------------------------ bloco


@pytest.fixture(scope="module")
def bloco(Z):
    return FZ.bloco({"zeros.json": Z})


def test_bloco_traz_os_numeros(bloco):
    for s in ("106", "14.860", "296", "141", "16.418", "18.508", "15.222", "67"):
        assert s in bloco, s
    assert "4 seções sem nenhum voto em Lula" in bloco
    assert "Em 2022 eram 2 seções sem voto em Lula" in bloco
    assert "Com o exterior são 108 sem voto em Flávio e 6 sem voto em Lula" in bloco
    assert "Flávio teve zero voto em 106 urnas" in bloco
    assert 'id="fig-an_zeros"' in bloco and "pendente" not in bloco
    assert bloco.count('viewBox="0 0 ') == 2
    assert bloco.count("politizese.html#uf=") == 110


def test_bloco_regras_de_texto(bloco, Z):
    pub = texto_publico(bloco).lower()
    assert "—" not in bloco
    assert "fraude" not in pub and "eleitores dele" not in pub
    assert "atipicidade pede explicação, não prova irregularidade" in pub
    for selo in SELOS:
        assert selo in bloco, selo
    for item in FZ.limites_itens({"zeros.json": Z}):
        assert "—" not in item and "fraude" not in item.lower()


@pytest.mark.skipif(not TEM_CAPITULO, reason="JSONs do capítulo Grupos ausentes")
def test_capitulo_poe_o_bloco_antes_dos_limites():
    h = CA.render(Dados(pasta=DADOS), cap())
    i_contra = h.index("O que a mistura não separa")
    i_bloco = h.index('id="zeros"')
    i_lim = h.index("Limites do capítulo")
    assert i_contra < i_bloco < i_lim
    assert "Seções com zero voto: seção sem voto" in h[i_lim:]
    assert "—" not in h


def test_coluna_da_folha_arquivada_e_regioes_conferem():
    Z = json.loads((DADOS / "zeros.json").read_text(encoding="utf-8"))
    m = Z["manchete"]
    assert m["url"].startswith("https://www1.folha.uol.com.br/colunas/painel/2026/10/")
    assert Path(m["arquivo"]).name in " ".join(Z["fontes"])
    nossa = {x["regiao"]: x["zero_direita_2026_2t"] for x in Z["por_regiao"]}
    assert all(nossa[r] == n for r, n in m["por_regiao"].items())
    h = FZ.bloco(Dados(pasta=DADOS))
    assert "coincide região a região" in h and "Paris Group" in h and "—" not in h


# ------------------------------------------------------------------ a cauda


def test_regua_binomial_e_cota():
    assert ZC.chance_ate(10, 0.5, 0) == pytest.approx(0.5**10)
    assert ZC.chance_ate(10, 0.5, 10) == 1.0
    exato = sum(math.comb(40, j) * 0.3**j * 0.7 ** (40 - j) for j in range(6))
    assert ZC.chance_ate(40, 0.3, 5) == pytest.approx(exato, rel=1e-12)
    # A aproximação e^-k: k votos em v válidos, n = v nominais no 2º turno.
    assert ZC.chance_ate(330, 1 / 330, 0) == pytest.approx(math.exp(-1), rel=0.01)
    assert ZC.chance_ate(330, 4 / 330, 0) == pytest.approx(math.exp(-4), rel=0.03)
    for n, q, m in [(200, 0.3, 2), (150, 0.1, 1), (300, 0.5, 60)]:
        assert ZC.cota_chernoff(n, q, m) >= ZC.chance_ate(n, q, m)
    assert ZC.cota_chernoff(100, 0.1, 50) == 1.0


def test_regras_da_cauda_declaradas():
    assert ZC.regra_ate_1(6, 1) and ZC.regra_ate_1(16, 0)
    assert not ZC.regra_ate_1(5, 0) and not ZC.regra_ate_1(6, 2)
    assert ZC.regra_queda(10, 2) and ZC.regra_queda(61, 2) and ZC.regra_queda(33, 5)
    assert not ZC.regra_queda(9, 0) and not ZC.regra_queda(10, 3)
    assert [ZC.teto_queda(k) for k in (10, 14, 15, 61)] == [2, 2, 3, 12]
    assert (ZC.PISO_NOMINAL_2T, ZC.ATE_1, ZC.QUEDA) == (30, (6, 1), (10, 80))


def test_formato_das_chances():
    assert [FC.pct_sig(100 * math.exp(-k)) for k in (1, 2, 3, 4, 5)] == [
        "37%",
        "14%",
        "5,0%",
        "1,8%",
        "0,67%",
    ]
    assert FC.um_em(1 / 45) == "1 em 45"
    assert FC.um_em(6.166e-8) == "1 em 16 milhões"
    assert FC.um_em(7.7e-7) == "1 em 1,3 milhão"
    assert FC.um_em(1e-22) == "menos de 1 em 1 trilhão"


@pytest.fixture(scope="module")
def C(Z):
    if "cauda" not in Z:
        pytest.skip("zeros.json sem o bloco cauda")
    return Z["cauda"]


def test_cauda_numeros_conferidos(C):
    assert ZC.falhas(C) == []
    assert ZC.obtido_cauda(C) == ZC.ESPERADO_CAUDA
    np_ = C["numero_pequeno"]
    assert (np_["secoes_zero_2t"], np_["com_voto_1t"], np_["votos_1t"]) == (
        106,
        56,
        118,
    )
    assert {x["k"]: x["secoes"] for x in np_["por_k"]} == {
        0: 50,
        1: 30,
        2: 10,
        3: 9,
        4: 5,
        5: 1,
        16: 1,
    }
    base = {x["k"]: x for x in np_["taxa_base"]}
    pares = {k: (base[k]["secoes_pais"], base[k]["chegaram_a_zero"]) for k in base}
    assert pares[1] == (129, 30) and pares[4] == (241, 5) and pares[16] == (659, 1)
    assert all(pares[k][1] == 0 for k in range(6, 16))
    assert round(base[1]["chance_aprox_pct"]) == 37
    assert round(base[4]["chance_aprox_pct"], 1) == 1.8
    pq, meio, topo = np_["faixas"]
    assert (pq["secoes_pais"], pq["chegaram_a_zero"]) == (984, 55)
    assert pq["zeros_esperados"] > pq["chegaram_a_zero"]
    assert (meio["de"], meio["ate"], meio["chegaram_a_zero"]) == (6, 15, 0)
    assert topo["zeros_esperados"] < 1e-3
    assert len(np_["secoes_com_voto_1t"]) == 56
    assert np_["secoes_com_voto_1t"][0]["chance_zero"] < 1e-7


def test_cauda_regras_espelho_e_calibracao(C):
    ca, es = C["cauda"], C["espelho"]
    assert (ca["queda_ate_1"], ca["queda_80"], ca["uniao"], ca["nas_duas"]) == (
        6,
        6,
        10,
        2,
    )
    assert (es["queda_ate_1"], es["queda_80"], es["secoes"]) == (0, 0, [])
    e = ca["esperado_independencia"]
    # A primeira regra cabe no acaso; a segunda passa dele com folga.
    assert ca["queda_ate_1"] <= e["queda_ate_1"]
    assert ca["queda_80"] > 3 * e["queda_80"]
    assert e["espelho_queda_ate_1"] < 1 and e["espelho_queda_80"] < 1
    assert (ca["sem_piso"]["queda_ate_1"], es["sem_piso"]["queda_80"]) == (7, 1)
    assert all(x["nominal_2t"] < 30 for x in ca["sem_piso"]["extras"])


def test_cauda_fichas(C):
    fichas = C["fichas"]
    assert [(f["uf"], f["municipio"], f["zona"], f["secao"]) for f in fichas] == [
        x[:4] for x in ZC.ESPERADO_CAUDA["cauda"]
    ]
    for f in fichas:
        assert f["urna"]["mesma_urna"] and f["urna"]["mesma_carga"]
        assert f["rdv"]["confere"] == 1 and f["rdv"]["confere_hash"]
        assert f["link"].startswith("politizese.html#uf=")
        g = f["governador"]
        assert (g["t2"] is not None) == g["uf_tem_2t"] == (f["uf"] in {"AM", "AC"})
        assert len(g["t1"]["candidatos"]) <= 4
    novas = {(f["uf"], f["secao"]) for f in fichas if f["secao_nova"]}
    assert novas == {("AM", 176), ("AP", 408)}
    assert "AP" not in C["governador"]["ufs_com_2t"]
    maues = next(f for f in fichas if f["secao"] == 176)
    g = maues["governador"]
    assert [c["nome_urna"] for c in g["t2"]["candidatos"]] == [
        "OMAR AZIZ",
        "PROFESSORA MARIA DO CARMO",
    ]
    assert g["t2"]["candidatos"][0]["comparacao"] == "coligação com o PT"
    assert g["t1"]["candidatos"][1]["campo"] == "centro-direita"
    assert (
        g["t1"]["direita_e_centro_direita"],
        g["t2"]["direita_e_centro_direita"],
    ) == (129, 1)
    assert len(C["governador"]["direita_caiu"]) == 3
    assert [x[0] for x in C["governador"]["direita_subiu"]] == ["AC"]


def test_cauda_nomes_vem_dos_arquivos(C):
    G = json.loads((DADOS / "governadores.json").read_text(encoding="utf-8"))
    finalistas = {
        (u["uf"], c["numero"]): c["nome_urna"]
        for u in G["ufs"]
        for c in u["candidatos"]
    }
    T = json.loads(ZC.CANDIDATOS_GOV.read_text(encoding="utf-8"))
    todos = {(c["uf"], int(c["numero"])): c["nome_urna"] for c in T}
    for f in C["fichas"]:
        for turno in ("t1", "t2"):
            for c in (f["governador"][turno] or {}).get("candidatos", []):
                k = (f["uf"], c["numero"])
                assert c["nome_urna"] == finalistas.get(k, todos.get(k)), k


def test_cauda_por_dentro(C):
    assert [tuple(x["chave"]) for x in C["por_dentro"]] == [
        ZC.ESPERADO_CAUDA["maues"]["chave"],
        ZC.ESPERADO_CAUDA["ipixuna"]["chave"],
    ]
    for x in C["por_dentro"]:
        assert all(x["hashes_conferem"].values()), x["hashes_conferem"]
        for h in (
            x["log_1t"]["log_sha256"],
            x["log_2t"]["log_sha256"],
            x["rdv"]["sha256"],
        ):
            assert re.fullmatch(r"[0-9a-f]{64}", h)
    m = C["por_dentro"][0]
    assert m["rdv"]["presidente"]["nulos_digitados"] == {"55": 4}
    assert m["troca_de_campo_uf"]["presidente_com_numero_de_governador"]["55"] > 0
    assert sum(m["log_2t"]["por_hora"].values()) == m["bu_2t"]["comparecimento"] == 337
    assert sum(m["log_1t"]["por_hora"].values()) == m["bu_1t"]["comparecimento"] == 331
    assert (
        m["log_1t"]["votos_por_eleitor"] == 6 and m["bu_1t"]["votos_por_eleitor"] == 6
    )


@pytest.fixture(scope="module")
def cauda_html(Z, C):
    return FC.bloco(Z)


def test_cauda_texto(cauda_html, bloco):
    h = cauda_html
    pub = texto_publico(h)
    assert 'id="zeros-cauda"' in h and h in bloco
    assert "—" not in h
    baixo = pub.lower()
    assert "fraude" not in baixo
    assert not re.search(r"\bdel[ea]s?\b", baixo)
    assert "atipicidade pede explicação, não prova irregularidade" in baixo
    for selo in ("Verificado", "Inferência", "Hipótese", "Achado contrário"):
        assert selo in h, selo
    for s in (
        "56 tinham voto nele",
        "30 com 1 voto",
        "1 com 16 votos",
        "37% com 1 voto",
        "1,8% com 4 votos",
        "das 129 seções",
        "das 659 com 16, uma",
        "O espelho está vazio",
        "1 em 16 milhões",
        "Omar Aziz (PSD, coligação com o PT) foi de 176 para 328",
        "129 para 1 em Maués",
        "02341225",
        "02018634 e 02018717",
        "7h 47, 8h 56, 9h 58, 10h 62, 11h 60, 12h 49, 13h 4, 15h 1",
        "encerramento às 16:05",
        "das 7h às 19h",
        "Marechal Thaumaturgo (AC)",
        "seção nova",
    ):
        assert s in pub or s in h, s
    assert h.count("<table>") == 2
    assert "politizese.html#uf=" not in h


def test_cauda_selos_coerentes(cauda_html):
    paragrafos = re.findall(r"<p>(.*?)</p>", cauda_html, flags=re.DOTALL)
    for par in paragrafos:
        txt = texto_publico(par)
        if "compatível" in txt or "não separa" in txt:
            assert "selo-inferencia" in par or "selo-hipotese" in par, txt[:80]
        if "orientação de liderança" in txt:
            assert "selo-hipotese" in par
    assert "Hipótese" in cauda_html.split("orientação de liderança")[0][-800:]


def test_cauda_falhas_acusa(C):
    ruim = copy.deepcopy(C)
    ruim["fichas"][4]["flavio_2t"] = 1
    assert any("cauda.cauda" in f for f in ZC.falhas(ruim))
    ruim = copy.deepcopy(C)
    ruim["por_dentro"][0]["log_2t"]["por_hora"]["7"] = 46
    assert any("cauda.maues" in f for f in ZC.falhas(ruim))
    ruim = copy.deepcopy(C)
    ruim["por_dentro"][0]["hashes_conferem"]["rdv"] = False
    assert any("hash" in f for f in ZC.falhas(ruim))


def test_cauda_ausente_nao_quebra_o_bloco(Z):
    sem = {k: v for k, v in Z.items() if k != "cauda"}
    assert FC.bloco(sem) == "" and FC.limites_itens(sem) == []
    h = FZ.bloco({"zeros.json": sem})
    assert "zeros-cauda" not in h and "pendente" not in h
    with pytest.raises(AssertionError, match="cauda"):
        ZD.conferir(sem)
