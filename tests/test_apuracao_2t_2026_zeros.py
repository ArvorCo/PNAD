"""Bloco "Seções com zero voto" do capítulo Grupos (dossiê do 2º turno de 2026).

Regra do tipo de local (sempre), degradação sem ``zeros.json`` (sempre) e, quando o
JSON gerado por ``scripts/apuracao-2t-2026-zeros.py`` existe, o contrato dele e o
bloco renderizado com os números conferidos.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path

import pytest
from apuracao_2t_2026 import pagina_cap_anomalia as CA
from apuracao_2t_2026 import pagina_fig_zeros as FZ
from apuracao_2t_2026 import zeros_base as ZB
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
        "anomalia", "10", "Grupos", "Os grupos de seções nos dois turnos", (), CA.render
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
