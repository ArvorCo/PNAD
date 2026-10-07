"""Testes do motor do Politize sua vizinhança (contrato em analysis/politize/CONTRATO.md)."""

from __future__ import annotations

import json
import math
import sqlite3
from pathlib import Path

import numpy as np
import pytest
from politize import arquetipos, fontes, montagem, pnad
from politize import metricas as mt

ROOT = Path(__file__).resolve().parents[1]
DADOS = ROOT / "docs/assets/politize/dados"

# Colunas do local, na ordem do contrato (seção 5, item 2).
COLUNAS_CONTRATO_LOCAL = [
    "local_id", "local_nr", "zona", "nome", "endereco", "bairro", "cep", "lat", "lon",
    "tipo_local", "secoes", "aptos", "comparecimento", "flavio", "lula", "terceira",
    "brancos", "nulos", "flavio_v", "lula_v", "terceira_v", "flavio_a", "lula_a",
    "terceira_a", "bn_a", "abst_a", "margem_v", "cobertura_2022", "bolsonaro22_1t_v",
    "lula22_1t_v", "bolsonaro22_2t_v", "lula22_2t_v", "abst22_2t_a", "reencontro_a",
    "fem", "a16_24", "a25_34", "a35_44", "a45_59", "a60", "fund_inc", "fund_med",
    "med_sup_inc", "superior", "setor_situacao", "setor_tipo", "renda_ate2",
    "renda_de2a5", "renda_mais5", "renda_mediana_brl", "esperado_flavio_v",
    "vao_perfil_pp", "c_terceira", "c_ausentes", "c_reencontro", "c_perfil",
    "potencial", "indice", "arquetipo", "arquetipo_secundario", "flavio_2t", "lula_2t",
    "faltam", "conversas_para_virar", "conversas_para_segurar",
]  # fmt: skip
COLUNAS_CONTRATO_SECAO = [
    "secao", "local_id", "mun_tse", "local", "bairro", "aptos", "comparecimento",
    "flavio", "lula", "terceira", "brancos", "nulos", "flavio_v", "lula_v",
    "terceira_v", "abst_a", "bn_a", "margem_v", "cobertura_2022", "bolsonaro22_1t_v",
    "lula22_1t_v", "bolsonaro22_2t_v", "lula22_2t_v", "reencontro_a", "perfil_fonte",
    "fem", "a16_24", "a25_34", "a35_44", "a45_59", "a60", "fund_inc", "fund_med",
    "med_sup_inc", "superior", "indice", "arquetipo", "faltam", "conversas_para_virar",
    "agregadas",
]  # fmt: skip
COLUNAS_CONTRATO_MUNICIPIO = [
    "uf", "mun_tse", "ibge", "nome", "lat", "lon", "n_locais", "aptos", "flavio_v",
    "lula_v", "arquivo",
]  # fmt: skip
ACRESCIDAS = [
    "em_aberto", "bna", "viravel", "cury", "renan", "caiado", "zema",
    "outros_nominais", "coord_fonte", "percentil", "percentil_uf",
]  # fmt: skip


def contagens(**kw) -> dict:
    base = dict.fromkeys(mt.CONTADORES + mt.CONTADORES_2022, 0)
    base.update(kw)
    return base


# ------------------------------------------------------------------ métricas


def test_pct_e_arredondamento():
    assert mt.pct(1, 4) == 25.0
    assert mt.pct(1, 0) is None
    assert mt.pct(None, 10) is None
    assert mt.r1(47.25) == 47.3
    assert mt.r1(-0.04) == 0.0
    assert math.copysign(1, mt.r1(-0.04)) == 1.0
    assert mt.r1(-2.25) == -2.3
    assert mt.r1(None) is None


def test_metricas_votos_brinquedo():
    c = contagens(
        aptos=200,
        comparecimento=150,
        flavio=60,
        lula=50,
        terceira=30,
        brancos=4,
        nulos=6,
    )
    m = mt.metricas_votos(c)
    assert m["validos"] == 140
    assert m["flavio_v"] == pytest.approx(100 * 60 / 140)
    assert m["lula_v"] == pytest.approx(100 * 50 / 140)
    assert m["terceira_v"] == pytest.approx(100 * 30 / 140)
    assert m["flavio_a"] == 30.0
    assert m["bn_a"] == 5.0
    assert m["abst_a"] == 25.0
    assert m["margem_v"] == pytest.approx(100 * 10 / 140)
    vazio = mt.metricas_votos(contagens(aptos=10, comparecimento=0))
    assert vazio["flavio_v"] is None and vazio["margem_v"] is None


def test_metricas_2022_e_reencontro_nas_secoes_casadas():
    c = contagens(
        aptos=400,
        aptos_casado=200,
        flavio_casado=50,
        aptos22=210,
        b22_1t=84,
        l22_1t=60,
        nom22_1t=160,
        b22_2t=95,
        l22_2t=70,
        nom22_2t=165,
        aptos22_2t=210,
        comp22_2t=168,
    )
    m = mt.metricas_2022(c)
    assert m["cobertura_2022"] == 50.0
    assert m["bolsonaro22_1t_v"] == pytest.approx(52.5)
    assert m["lula22_2t_v"] == pytest.approx(100 * 70 / 165)
    assert m["abst22_2t_a"] == pytest.approx(20.0)
    # Bolsonaro 40% dos aptos de 2022 contra Flávio 25% dos aptos casados de 2026.
    assert m["reencontro_a"] == pytest.approx(15.0)
    assert mt.reencontro(20.0, 30.0) == 0.0
    sem = mt.metricas_2022(contagens(aptos=100))
    assert sem["cobertura_2022"] == 0.0 and sem["reencontro_a"] is None


def test_componentes_indice_e_teto():
    m = {
        "terceira_a": 6.0,
        "bn_a": 4.0,
        "abst_a": 20.0,
        "reencontro_a": 3.0,
        "validos": 150,
        "aptos": 200,
    }
    comp = mt.componentes(m, 4.0)
    assert comp["c_terceira"] == 10.0
    assert comp["c_ausentes"] == 10.0
    assert comp["c_reencontro"] == 3.0
    assert comp["c_perfil"] == pytest.approx(3.0)
    assert comp["potencial"] == pytest.approx(26.0)
    assert mt.indice(26.0) == 65
    assert mt.indice(40.0) == 100
    assert mt.indice(55.0) == 100
    assert mt.indice(None) is None
    # Vão negativo não entra; componente sem dado entra como zero no potencial.
    negativo = mt.componentes({**m, "reencontro_a": None}, -7.0)
    assert negativo["c_perfil"] == 0.0
    assert negativo["c_reencontro"] is None
    assert negativo["potencial"] == pytest.approx(20.0)
    assert mt.componentes(m, None)["c_perfil"] is None


def test_conta_2t():
    assert abs(mt.COEF_FLAVIO_2T - 0.427) < 1e-12
    assert abs(mt.COEF_LULA_2T - 0.273) < 1e-12
    # Flávio 100, Lula 120, terceira 50: 121,35 contra 133,65; faltam 13 votos.
    c = mt.conta_2t(100, 120, 50, 20.0)
    assert c["flavio_2t"] == pytest.approx(121.35)
    assert c["lula_2t"] == pytest.approx(133.65)
    assert c["faltam"] == 13
    assert c["conversas_para_virar"] == math.ceil(13 / 0.35)
    assert c["conversas_para_segurar"] is None
    # Empate exato pede 1 voto.
    assert mt.conta_2t(100, 100, 0, None)["faltam"] == 1
    frente = mt.conta_2t(200, 100, 10, 25.0)
    assert frente["faltam"] == 0
    assert frente["conversas_para_virar"] is None
    assert frente["conversas_para_segurar"] == round((200 + 4.27) * 0.25)


def test_em_aberto_bna_e_viravel():
    c = contagens(aptos=300, comparecimento=240, terceira=20, brancos=5, nulos=7)
    assert mt.em_aberto(c) == 20 + 5 + 7 + 60
    assert mt.bna(c) == 5 + 7 + 60
    assert mt.viravel(100, 150, 50) == "flavio"
    assert mt.viravel(100, 150, 49) is None
    assert mt.viravel(150, 100, 50) == "lula"
    assert mt.viravel(100, 100, 999) is None


def test_voto_por_faixa_e_esperado():
    cruz = {
        "opcoes": ["lula", "flavio", "outro", "branco_nulo", "indecisos"],
        "linhas": [[50, 30, 10, 5, 5], [40, 40, 10, 6, 4], [30, 60, 10, 0, 0]],
    }
    v = mt.voto_valido_faixas(cruz)
    assert v[0]["lula"] == pytest.approx(100 * 50 / 90)
    assert v[2]["flavio"] == pytest.approx(60.0)
    media = mt.media_casas([v, v])
    assert media[1]["flavio"] == pytest.approx(v[1]["flavio"])
    renda = {"ate2": 50.0, "de2a5": 30.0, "mais5": 20.0}
    f, lu = mt.esperado_bruto(renda, v)
    assert f == pytest.approx(0.5 * v[0]["flavio"] + 0.3 * v[1]["flavio"] + 0.2 * 60)
    assert lu == pytest.approx(0.5 * v[0]["lula"] + 0.3 * v[1]["lula"] + 0.2 * 30)
    assert mt.esperado_bruto(None, v) is None
    media_pond, desl = mt.deslocamento([(40.0, 1.0), (50.0, 3.0)], 50.0)
    assert media_pond == pytest.approx(47.5)
    assert desl == pytest.approx(2.5)


def test_posicao_percentil():
    ref = sorted([10.0, 20.0, 20.0, 30.0, 40.0])
    assert mt.posicao_percentil(40.0, ref) == 100
    assert mt.posicao_percentil(10.0, ref) == 0
    assert mt.posicao_percentil(20.0, ref) == 25
    assert mt.posicao_percentil(30.0, ref) == 75
    assert mt.posicao_percentil(None, ref) is None
    assert mt.posicao_percentil(5.0, [5.0]) is None


def test_percentis_iguais_ao_numpy():
    xs = [3.0, 1.0, 4.0, 1.5, 9.0, 2.6, 5.0]
    p = mt.percentis(xs, [10, 50, 99])
    for q in (10, 50, 99):
        assert p[f"p{q}"] == pytest.approx(float(np.percentile(xs, q)))


def test_parcelas_perfil_ignoram_desconhecidos():
    vetor = [60, 40, 10, 20, 30, 20, 20, 25, 25, 25, 25, 110]
    s = mt.parcelas_perfil(vetor, fontes.PERFIL_COLS)
    assert s["fem"] == 60.0
    assert sum(s[k] for k in ("a16_24", "a25_34", "a35_44", "a45_59", "a60")) == 100
    assert s["superior"] == 25.0


# ------------------------------------------------------------------ arquétipos


def _m(**kw) -> dict:
    base = {
        "flavio_v": 45.0,
        "lula_v": 30.0,
        "margem_v": 15.0,
        "reencontro_a": 0.0,
        "terceira_v": 5.0,
        "bn_v": 3.0,
        "abst_a": 20.0,
        "vao_perfil_pp": 0.0,
    }
    base.update(kw)
    return base


def test_ordem_das_regras_de_arquetipo():
    assert arquetipos.CODIGOS == (
        "fortaleza",
        "muro",
        "pendulo",
        "reencontro",
        "fertil",
        "dormindo",
        "abaixo_do_perfil",
        "frente",
        "atras",
    )
    assert arquetipos.classificar(_m(flavio_v=60.0, margem_v=30.0)) == (
        "fortaleza",
        None,
    )
    assert arquetipos.classificar(_m(flavio_v=59.9))[0] == "frente"
    assert arquetipos.classificar(_m(flavio_v=25.0, lula_v=65.0, margem_v=-40.0)) == (
        "muro",
        None,
    )
    # Pêndulo vence reencontro; o reencontro vira secundário.
    assert arquetipos.classificar(_m(margem_v=6.0, reencontro_a=5.0)) == (
        "pendulo",
        "reencontro",
    )
    assert arquetipos.classificar(_m(margem_v=-6.0))[0] == "pendulo"
    assert arquetipos.classificar(_m(margem_v=6.1))[0] == "frente"
    assert arquetipos.classificar(_m(reencontro_a=5.0, abst_a=30.0)) == (
        "reencontro",
        "dormindo",
    )
    assert arquetipos.classificar(_m(terceira_v=9.0, bn_v=3.0)) == ("fertil", None)
    assert arquetipos.classificar(_m(abst_a=28.0, vao_perfil_pp=5.0)) == (
        "dormindo",
        "abaixo_do_perfil",
    )
    assert arquetipos.classificar(_m(vao_perfil_pp=5.0))[0] == "abaixo_do_perfil"
    assert arquetipos.classificar(_m(margem_v=-15.0)) == ("atras", None)
    # Vazio (sem válidos) cai no resto.
    assert arquetipos.classificar({}) == ("atras", None)


# ------------------------------------------------------------------ PNAD e fontes


def test_faixas_de_renda_e_mediana():
    assert pnad.faixa(3242.0, 1621.0) == 0
    assert pnad.faixa(3242.01, 1621.0) == 1
    assert pnad.faixa(8105.0, 1621.0) == 1
    assert pnad.faixa(8105.5, 1621.0) == 2
    cel = pnad.Celula()
    for valor in (1000.0, 2000.0, 3000.0, 9000.0):
        cel.somar(valor, 1.0, 1621.0)
    assert cel.parcelas() == [75.0, 0.0, 25.0]
    mediana = pnad.mediana_cdf(cel.cdf())
    assert 2000.0 <= mediana <= 2010.0


def test_mistura_de_renda_soma_cem():
    celulas = {}
    for i, esc in enumerate(pnad.ESCOLARIDADES):
        for sit in pnad.SITUACOES:
            cel = pnad.Celula()
            for k in range(40):
                cel.somar(500.0 * (i + 1) + 100.0 * k, 1.0, 1621.0)
            celulas[("AC", esc, sit)] = cel
            celulas[("BR", esc, sit)] = cel
    tab = pnad.TabelaRenda(celulas, {})
    r = tab.misturar("AC", None, {"fund_inc": 0.5, "superior": 0.5})
    assert r["ate2"] + r["de2a5"] + r["mais5"] == pytest.approx(100.0)
    assert r["mediana_brl"] > 0
    assert tab.misturar("AC", "urbana", {}) is None


def test_faixa_idade_e_caixa_normal():
    assert fontes.faixa_idade("16 anos") == "a16_24"
    assert fontes.faixa_idade("21 a 24 anos") == "a16_24"
    assert fontes.faixa_idade("25 a 29 anos") == "a25_34"
    assert fontes.faixa_idade("55 a 59 anos") == "a45_59"
    assert fontes.faixa_idade("100 anos ou mais") == "a60"
    assert fontes.faixa_idade("Inválida") is None
    assert fontes.caixa_normal("SÃO JOÃO DEL REI") == "São João del Rei"
    assert fontes.caixa_normal("ABU DHABI") == "Abu Dhabi"
    assert fontes.tipo_setor("1") == "favela"
    assert fontes.tipo_setor("4") == "outro"
    assert fontes.situacao_setor("9") is None
    assert fontes.situacao_setor("8") == "rural"


# ------------------------------------------------------------ arquivos gerados


def _json(caminho: Path):
    return json.loads(caminho.read_text(encoding="utf-8"))


def _exige(caminho: Path) -> None:
    if not caminho.exists():
        pytest.skip(f"rode python3 scripts/politize-build.py --uf AC ({caminho.name})")


def test_contrato_de_colunas():
    _exige(DADOS / "indice.json")
    mun = _json(next((DADOS / "mun/AC").glob("*.json")))
    assert mun["locais"]["colunas"] == COLUNAS_CONTRATO_LOCAL + ACRESCIDAS
    assert list(montagem.COLUNAS_LOCAL) == COLUNAS_CONTRATO_LOCAL + ACRESCIDAS
    zona = _json(next((DADOS / "zona/AC").glob("*.json")))
    assert zona["secoes"]["colunas"] == COLUNAS_CONTRATO_SECAO + ACRESCIDAS
    assert set(zona) == {"uf", "zona", "municipios", "secoes"}
    indice = _json(DADOS / "indice.json")
    for chave in (
        "gerado_em",
        "versao_contrato",
        "fontes",
        "parametros",
        "nacional",
        "ufs",
        "municipios",
        "zonas",
    ):
        assert chave in indice
    assert indice["municipios"]["colunas"][:11] == COLUNAS_CONTRATO_MUNICIPIO
    p = indice["parametros"]
    assert p["transferencia_terceira"]["sem_escolha"] == 0.30
    assert p["transferencia_terceira"]["flavio_entre_escolhem"] == 0.61
    assert p["taxa_conversao"] == 0.35
    for f in indice["fontes"]:
        assert len(f["sha256"]) == 64 and f["bytes"] > 0
    uf = _json(DADOS / "uf/AC.json")
    assert {"uf", "nome", "regiao", "totais", "problemas"} <= set(uf)
    assert len(uf["ranking_indice"]) <= 20
    assert all(r["aptos"] >= 300 for r in uf["ranking_indice"])
    for linha in mun["locais"]["linhas"]:
        reg = dict(zip(mun["locais"]["colunas"], linha, strict=True))
        bna = reg["brancos"] + reg["nulos"] + reg["aptos"] - reg["comparecimento"]
        assert reg["bna"] == bna
        assert reg["em_aberto"] == bna + reg["terceira"]
        assert reg["viravel"] == mt.viravel(reg["flavio"], reg["lula"], bna)
        assert reg["terceira"] == sum(
            reg[k] for k in ("cury", "renan", "caiado", "zema", "outros_nominais")
        )
        assert reg["arquetipo"] in arquetipos.CODIGOS
        assert reg["indice"] is None or 0 <= reg["indice"] <= 100
        assert reg["setor_situacao"] in ("urbana", "rural", None)
        assert reg["setor_tipo"] in (
            "comum",
            "favela",
            "aldeia",
            "quilombo",
            "prisao",
            "militar",
            "outro",
            None,
        )


def test_fragmentos_do_acre_somam_o_banco():
    _exige(DADOS / "mun/AC")
    flavio = lula = aptos = 0
    for arq in (DADOS / "mun/AC").glob("*.json"):
        d = _json(arq)
        cols = d["locais"]["colunas"]
        i_f, i_l, i_a = cols.index("flavio"), cols.index("lula"), cols.index("aptos")
        for linha in d["locais"]["linhas"]:
            flavio += linha[i_f]
            lula += linha[i_l]
            aptos += linha[i_a]
        assert d["totais"]["flavio"] == sum(x[i_f] for x in d["locais"]["linhas"])
    secoes_f = 0
    for arq in (DADOS / "zona/AC").glob("*.json"):
        d = _json(arq)
        cols = d["secoes"]["colunas"]
        i_f, i_a = cols.index("flavio"), cols.index("aptos")
        for linha in d["secoes"]["linhas"]:
            assert linha[i_a] < 30 or linha[i_f] is not None
            secoes_f += linha[i_f] or 0
    con = sqlite3.connect(f"file:{fontes.DB_SECOES}?mode=ro", uri=True)
    try:
        banco = dict(
            con.execute(
                "SELECT numero, SUM(votos) FROM voto_secao WHERE uf = 'ac' "
                "AND cargo = 1 AND tipo = 1 AND numero IN (13, 22) GROUP BY numero"
            ).fetchall()
        )
        aptos_banco = con.execute(
            "SELECT SUM(c.aptos) FROM bu_cargo c JOIN secao s ON s.uf = c.uf "
            "AND s.mun = c.mun AND s.zona = c.zona AND s.secao = c.secao "
            "WHERE c.uf = 'ac' AND c.cargo = 1 AND s.nsp IS NULL"
        ).fetchone()[0]
    finally:
        con.close()
    assert flavio == banco[22]
    assert lula == banco[13]
    assert aptos == aptos_banco
    assert secoes_f <= flavio


def test_cep_aponta_para_locais_existentes():
    _exige(DADOS / "cep/69.json")
    cep = _json(DADOS / "cep/69.json")
    assert set(cep) == {"exato", "prefixo5"}
    ids_ac = set()
    for arq in (DADOS / "mun/AC").glob("*.json"):
        d = _json(arq)
        ids_ac |= {linha[0] for linha in d["locais"]["linhas"]}
    for chave, ids in cep["exato"].items():
        assert len(chave) == 8 and chave.isdigit()
        assert cep["prefixo5"][chave[:5]]
        for i in ids:
            if i.startswith("AC-"):
                assert i in ids_ac
            assert not i.startswith("ZZ-")


def test_sem_travessao():
    alvos = [
        *(ROOT / "scripts/politize").glob("*.py"),
        ROOT / "scripts/politize-build.py",
        ROOT / "tests/test_politize.py",
    ]
    # DECISOES.md e STATUS.md são compartilhados com outros agentes; o motor responde
    # pelo relatório e pelos JSON que ele mesmo grava.
    relatorio = ROOT / "analysis/politize/relatorio_build.md"
    if relatorio.exists():
        alvos.append(relatorio)
    if DADOS.exists():
        alvos += list(DADOS.rglob("*.json"))
    travessao = chr(0x2014)
    for arq in alvos:
        assert travessao not in arq.read_text(encoding="utf-8"), arq
