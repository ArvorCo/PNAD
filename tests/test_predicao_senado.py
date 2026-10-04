"""Motor da predição do Senado 2027 com dados sintéticos."""

import copy
import hashlib
import json
from datetime import datetime, timezone

import numpy as np
import pytest
from senado_2026 import base as B
from senado_2026 import calibracao as C
from senado_2026 import indeferido as I
from senado_2026 import motor as M
from senado_2026 import saida
from senado_2026 import senado as S

AGORA = datetime(2026, 10, 3, 23, 0, tzinfo=timezone.utc)
SIM = 3000


def onda(
    uf,
    casa,
    fim,
    candidatos,
    *,
    inicio=None,
    n: int | None = 1000,
    ind=10.0,
    bn=8.0,
    **kw,
):
    votos = kw.pop("votos_por_eleitor", 1)
    campo = None if fim is None else {"inicio": inicio or fim, "fim": fim}
    soma = sum(v for _, _, v in candidatos) + (ind or 0) + (bn or 0)
    return {
        "instituto": casa.title(),
        "instituto_slug": casa,
        "uf": uf,
        "cargo": "senador",
        "registro_tse": None,
        "campo": campo,
        "divulgacao": kw.pop("divulgacao", fim),
        "n": n,
        "fonte": {"tipo": "teste", "url": "https://exemplo.invalid", "sha256": None},
        "pergunta": {
            "codigo": "T",
            "tipo": kw.pop("tipo", "estimulada"),
            "votos_por_eleitor": votos,
            "soma_total": soma,
        },
        "candidatos": [
            {"nome": nome, "partido": partido, "valor": valor}
            for nome, partido, valor in candidatos
        ],
        "indecisos": ind,
        "branco_nulo": bn,
        "observacoes": [],
        **kw,
    }


SP = [
    ("Ana Direita", "PL", 30.0),
    ("Bruno Centro", "PSD", 24.0),
    ("Carla Esquerda", "PT", 18.0),
    ("Davi Novo", "NOVO", 8.0),
    ("Eva Psol", "PSOL", 2.0),
]


def escrever(tmp_path, ondas, *, com_tse=True):
    pasta = tmp_path / "senado"
    (pasta / "pesquisas").mkdir(parents=True)
    for i, o in enumerate(ondas):
        nome = f"{o['instituto_slug']}_{o['uf']}_{i}.json"
        (pasta / "pesquisas" / nome).write_text(json.dumps(o), encoding="utf-8")
    if com_tse:
        candidatos = [
            {
                "uf": "SP",
                "sq_candidato": f"25{i}",
                "nome_urna": nome.upper(),
                "nome_completo": nome.upper() + " DA SILVA",
                "partido": partido,
                "foto": None,
            }
            for i, (nome, partido, _) in enumerate(SP)
        ]
        candidatos.append(
            {
                "uf": "MG",
                "sq_candidato": "13001",
                "nome_urna": "ZECA DO POVO",
                "nome_completo": "JOSE CARLOS",
                "partido": "PP",
                "foto": None,
            }
        )
        (pasta / "tse_candidatos.json").write_text(json.dumps(candidatos))
        casamento = {
            "casados": [
                {"uf": "MG", "nome_pesquisa": "Zeca", "sq_candidato": "13001"},
                {"uf": "MG", "nome_pesquisa": "Zeca do Povo", "sq_candidato": "13001"},
            ],
            "nao_casados": [],
        }
        (pasta / "casamento_nomes.json").write_text(json.dumps(casamento))
    return pasta


def senadores_2022():
    partidos = ["PL", "PT", "PSD", "UNIÃO", "MDB", "PSB", "PP", "PSC", "NOVO"]
    return [
        {"uf": uf, "nome": f"S {uf}", "partido": partidos[i % len(partidos)]}
        for i, uf in enumerate(B.UFS)
    ]


def prever(pasta, *, semente=M.SEMENTE, cal=None, **kw):
    kw.setdefault("registro_indeferido", {})
    ondas = B.ler_pesquisas(pasta / "pesquisas")
    tse = B.Tse(pasta, docs=pasta)
    return saida.prever(
        ondas,
        tse,
        senadores_2022(),
        {"SP": 1000},
        cal,
        simulacoes=SIM,
        semente=semente,
        agora=AGORA,
        **kw,
    )


@pytest.fixture(scope="module")
def basico(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("basico")
    ondas = [
        onda("SP", "datafolha", "2026-10-02", SP, inicio="2026-10-01", n=2000),
        onda("SP", "quaest", "2026-10-03", SP, inicio="2026-10-02", n=1500),
        onda("SP", "quaest", "2026-09-20", SP, inicio="2026-09-18"),
        onda(
            "MG",
            "quaest",
            "2026-09-20",
            [("Zeca", "PP", 25.0), ("Lia", "PT", 22.0), ("Rui", "PL", 15.0)],
            inicio="2026-09-18",
        ),
        onda(
            "MG",
            "datafolha",
            "2026-09-21",
            [("Zeca do Povo", "PP", 26.0), ("Lia", "PT", 20.0), ("Rui", "PL", 16.0)],
        ),
    ]
    pasta = escrever(tmp, ondas)
    return pasta, prever(pasta)


def test_esquema(basico):
    _, out = basico
    for chave in (
        "gerado_em",
        "data_referencia",
        "eleicao",
        "parametros",
        "estados",
        "senado_2027",
        "validacao",
        "fontes",
    ):
        assert chave in out
    assert set(out["estados"]) == set(B.UFS)
    sp = out["estados"]["SP"]
    for chave in (
        "uf",
        "nome",
        "eleitorado",
        "pesquisas_usadas",
        "pesquisas_descartadas",
        "cobertura",
        "media",
        "probabilidades",
        "eleitos_provaveis",
        "p_dupla_mais_provavel",
        "incerteza",
        "notas",
    ):
        assert chave in sp
    p = sp["probabilidades"][0]
    for chave in (
        "nome",
        "partido",
        "campo",
        "sq_candidato",
        "foto",
        "p_eleito",
        "p_primeiro",
        "ic90_validos",
    ):
        assert chave in p
    s27 = out["senado_2027"]
    for chave in (
        "continuam",
        "por_campo",
        "por_partido",
        "por_grupo",
        "p_maioria_direita_mais_centro_direita",
        "p_41_direita_centro_direita_centro",
        "p_54_bloco_oposicao",
        "p_49_direita_centro_direita",
        "p_41_esquerda_centro_esquerda",
        "p_49_esquerda_centro_esquerda",
        "p_54_esquerda_centro_esquerda",
    ):
        assert chave in s27
    for g in ("direita", "centro", "esquerda"):
        assert set(s27["por_grupo"][g]) >= {
            "esperado",
            "ic90",
            "continuam",
            "novos_esperado",
        }
    par = out["parametros"]
    assert par["meia_vida_dias"] == 5.0
    assert par["janela_campo_minimo"] == "2026-09-28"
    assert par["escala_erro_pp"] > 0
    assert par["justificativa_erro"]
    val = out["validacao"]
    for chave in ("calibracao_2022", "sensibilidades", "achado_contrario"):
        assert chave in val
    assert {s["rotulo"] for s in val["sensibilidades"]} == {
        "Erro dobrado",
        "Indecisos 100% uniformes",
    }
    texto = json.dumps(out, ensure_ascii=False)
    assert "\u2014" not in texto


def test_soma_de_p_eleito_e_dois(basico):
    _, out = basico
    for e in out["estados"].values():
        if e["probabilidades"]:
            assert sum(p["p_eleito"] for p in e["probabilidades"]) == pytest.approx(
                2.0, abs=1e-9
            )
            assert sum(p["p_primeiro"] for p in e["probabilidades"]) == pytest.approx(
                1.0, abs=1e-9
            )


def test_monotonicidade(basico):
    _, out = basico
    probs = {p["nome"]: p["p_eleito"] for p in out["estados"]["SP"]["probabilidades"]}
    ordem = [B.titulo_urna(n.upper()) for n, _, _ in SP]
    valores = [probs[n] for n in ordem]
    assert valores == sorted(valores, reverse=True)
    assert out["estados"]["SP"]["eleitos_provaveis"] == ordem[:2]


def test_monotonicidade_mesmo_campo(tmp_path):
    cands = [("A", "PL", 26.0), ("B", "PL", 22.0), ("C", "PL", 19.0), ("D", "PL", 9.0)]
    pasta = escrever(tmp_path, [onda("RJ", "quaest", "2026-10-02", cands)])
    out = prever(pasta, sensibilidades=False)
    p = {x["nome"]: x["p_eleito"] for x in out["estados"]["RJ"]["probabilidades"]}
    assert p["A"] >= p["B"] >= p["C"] >= p["D"]


def test_estado_sem_pesquisa(basico):
    _, out = basico
    ba = out["estados"]["BA"]
    assert ba["cobertura"] == "sem_pesquisa"
    assert ba["eleitos_provaveis"] == []
    assert ba["probabilidades"] == []
    assert "BA" in out["parametros"]["estados_sem_pesquisa"]["ufs"]
    dist = out["parametros"]["estados_sem_pesquisa"]["distribuicao_campos"]
    assert sum(dist.values()) == pytest.approx(1.0)


def test_cobertura_antiga_e_onda_anterior(basico):
    _, out = basico
    mg = out["estados"]["MG"]
    assert mg["cobertura"] == "antiga"
    assert mg["incerteza"] == "alta"
    sp = out["estados"]["SP"]
    assert sp["cobertura"] == "recente"
    usadas = {p["arquivo"] for p in sp["pesquisas_usadas"]}
    assert usadas == {"datafolha_SP_0.json", "quaest_SP_1.json"}
    motivos = {d["arquivo"]: d["motivo"] for d in sp["pesquisas_descartadas"]}
    assert motivos["quaest_SP_2.json"] == "onda anterior da mesma casa"
    assert sum(p["peso"] for p in sp["pesquisas_usadas"]) == pytest.approx(1.0)


def test_reprodutibilidade(basico):
    pasta, out = basico
    de_novo = prever(pasta)
    assert de_novo == out
    outra = prever(pasta, semente=1, sensibilidades=False)
    p1 = [p["p_eleito"] for p in out["estados"]["SP"]["probabilidades"]]
    p2 = [p["p_eleito"] for p in outra["estados"]["SP"]["probabilidades"]]
    assert p1 != p2


def test_dois_votos_por_eleitor_divide_por_dois(tmp_path):
    um = onda("SP", "datafolha", "2026-10-02", SP)
    dobro = [(n, p, 2 * v) for n, p, v in SP]
    dois = onda("SP", "parana", "2026-10-02", dobro, ind=20.0, bn=16.0)
    dois["pergunta"]["votos_por_eleitor"] = 2
    a = B.normalizar_onda(um, "a.json", 800)
    b = B.normalizar_onda(dois, "b.json", 800)
    assert [c["valor"] for c in b["candidatos"]] == [
        c["valor"] for c in a["candidatos"]
    ]
    assert b["indecisos"] == a["indecisos"]
    tse = B.Tse(escrever(tmp_path, []), docs=tmp_path)
    ma = B.media_estado([a], "SP", tse)
    mb = B.media_estado([b], "SP", tse)
    assert ma["validos"] == pytest.approx(mb["validos"])


def test_alias_de_nomes(basico):
    _, out = basico
    mg = out["estados"]["MG"]
    zeca = [m for m in mg["media"] if m["sq_candidato"] == "13001"]
    assert len(zeca) == 1
    assert zeca[0]["aliases"] == ["Zeca", "Zeca do Povo"]
    assert zeca[0]["nome"] == "Zeca do Povo"
    aliases = out["validacao"]["aliases"]
    assert any(a["uf"] == "MG" and len(a["variantes"]) == 2 for a in aliases)


def test_normalizacao_sem_acento_une_casas(tmp_path):
    o1 = onda("RJ", "quaest", "2026-10-02", [("André Do Prado", "PL", 30.0), *SP[1:]])
    o2 = onda(
        "RJ", "datafolha", "2026-10-02", [("Andre do Prado", "PL", 28.0), *SP[1:]]
    )
    pasta = escrever(tmp_path, [o1, o2])
    out = prever(pasta, sensibilidades=False)
    nomes = [m["nome"] for m in out["estados"]["RJ"]["media"]]
    assert sum(1 for n in nomes if "Prado" in n) == 1
    assert "André do Prado" in nomes


def test_composicao_fecha_em_81(basico):
    _, out = basico
    s27 = out["senado_2027"]
    assert s27["fecha_em_81_em_todo_sorteio"] is True
    assert s27["total_por_sorteio_min_max"] == [81, 81]
    assert sum(v["esperado"] for v in s27["por_campo"].values()) == pytest.approx(81)
    assert sum(v["esperado"] for v in s27["por_grupo"].values()) == pytest.approx(81)
    assert len(s27["continuam"]) == 27
    mg = next(c for c in s27["continuam"] if c["uf"] == "MG")
    assert mg["campo"] == "direita"
    assert "PSC" in mg["nota"]


def test_composicao_direta_soma_81():
    rng = np.random.default_rng(0)
    campos = rng.integers(0, len(B.CAMPOS), (500, 54))
    partidos = rng.integers(0, 3, (500, 54))
    fixos = S.continuam(senadores_2022())
    comp = S.composicao(campos, partidos, ["PL", "PT", "PSD"], fixos)
    assert comp["fecha_em_81_em_todo_sorteio"]
    total = sum(sum(v["ic90"]) for v in comp["por_campo"].values())
    assert total > 0


def test_retirada_vira_indeciso():
    cands = [("Salles", "NOVO", 4.0), ("Ana", "PL", 30.0)]
    o = B.normalizar_onda(onda("SP", "futura", "2026-10-01", cands), "f.json", 800)
    assert [c["nome_pesquisa"] for c in o["candidatos"]] == ["Ana"]
    assert o["indecisos"] == pytest.approx(14.0)
    assert o["retiradas"][0]["data_retirada"] == "2026-09-28"


def test_campo_inferido_pela_divulgacao(tmp_path):
    recente = onda("PE", "quaest", None, SP, divulgacao="2026-10-03", n=None)
    antiga = onda("RS", "quaest", None, SP, divulgacao="2026-09-29")
    pasta = escrever(tmp_path, [recente, antiga])
    out = prever(pasta, sensibilidades=False)
    pe = out["estados"]["PE"]
    assert pe["cobertura"] == "recente"
    usada = pe["pesquisas_usadas"][0]
    assert usada["campo_inferido"] is True
    assert usada["campo"] == "2026-09-30 a 2026-10-02"
    assert usada["n_assumido"] is True
    assert out["estados"]["RS"]["cobertura"] == "antiga"
    inferidos = {x["arquivo"] for x in out["validacao"]["campo_inferido"]}
    assert "quaest_PE_0.json" in inferidos


def test_espontanea_descartada(tmp_path):
    vazia = onda("GO", "quaest", "2026-10-03", [], tipo="espontanea")
    velha = onda("GO", "quaest", "2026-09-20", SP)
    pasta = escrever(tmp_path, [vazia, velha])
    out = prever(pasta, sensibilidades=False)
    go = out["estados"]["GO"]
    motivos = {d["arquivo"]: d["motivo"] for d in go["pesquisas_descartadas"]}
    assert "espontanea" in motivos["quaest_GO_0.json"]
    assert go["cobertura"] == "antiga"


def test_motor_funciona_sem_arquivos_do_tse(tmp_path):
    pasta = escrever(tmp_path, [onda("SP", "quaest", "2026-10-02", SP)], com_tse=False)
    ondas = B.ler_pesquisas(pasta / "pesquisas")
    out = saida.prever(
        ondas, B.Tse(pasta, docs=pasta), None, {}, None, simulacoes=SIM, agora=AGORA
    )
    sp = out["estados"]["SP"]
    assert all(p["sq_candidato"] is None and p["foto"] is None for p in sp["media"])
    assert out["senado_2027"]["fecha_em_81_em_todo_sorteio"] is False
    assert out["parametros"]["erro"]["fonte"] == "hipotese"


def test_hipotese_reproduz_escala_declarada():
    erro = M.erro_de_hipotese()
    assert M.sd_pp(erro, sorteios=100_000) == pytest.approx(
        C.HIPOTESE["sd_pp_30"], abs=0.15
    )
    assert M.sd_pp(erro.escalado(2.0)) > M.sd_pp(erro)


def test_erro_calibrado_usa_2022():
    cal = {
        "cobertura": {"n_estados_casas_principais": 18},
        "variancia_log": {
            "casas_principais_competitivas": {
                "var_nao_amostral_log": 0.16,
                "var_campo_nacional_log": 0.06,
            }
        },
        "deriva": {"var_por_dia_log": 0.001},
        "dias_ate_eleicao_medio": 4.0,
    }
    erro, detalhe = M.erro_calibrado(cal)
    assert erro.fonte == "wikipedia_2022"
    assert erro.var_estatica == pytest.approx(0.156)
    assert erro.var_nacional == pytest.approx(0.06)
    assert erro.var_estadual == pytest.approx(erro.var_idio)
    assert detalhe["deriva_descontada_log"] == pytest.approx(0.004)
    cal["cobertura"]["n_estados_casas_principais"] = 10
    assert M.erro_calibrado(cal)[0].fonte == "hipotese"


def _datas(texto):
    lidas = C.datas(texto)
    return None if lidas is None else tuple(d.isoformat() for d in lidas)


def test_datas_da_wikipedia():
    assert _datas("27–29 de setembro de 2022") == ("2022-09-27", "2022-09-29")
    assert _datas("30 de setembro a 1.º de outubro de 2022") == (
        "2022-09-30",
        "2022-10-01",
    )
    assert _datas("26-27/9") == ("2022-09-26", "2022-09-27")
    assert _datas("sem data") is None


WIKI = """== Pesquisas de opinião ==
=== Para senador ===
{| class="wikitable"
! rowspan=2|Período !! rowspan=2|Instituto !! rowspan=2|Amostragem !! Ana <br> {{small|(PL)}} !! Beto <br> {{small|(PT)}} !! rowspan=2|Outros !! rowspan=2|Indecisos
|-
! style="background:#000;"|
! style="background:#fff;"|
|-
| 28–30 de setembro || [[Ipec|IPEC]] <br> {{small|[https://exemplo.invalid XX-00001/2022]}} || 1 000 || 40% || 30%<ref>nota</ref> || 10% || 20%
|-
| 20–22 de setembro || IPEC || 800 || 35% || 35% || 10% || 20%
|}
== Resultados ==
"""


def test_tabela_da_wikipedia_e_pares():
    linhas = C.pesquisas_wiki(WIKI)
    assert len(linhas) == 2
    assert linhas[0]["casa"] == "ipec"
    assert linhas[0]["n"] == 1000
    assert [c["valor"] for c in linhas[0]["candidatos"]] == [40.0, 30.0]
    urna = [
        {
            "sq_candidato": "1",
            "nome_urna": "ANA",
            "nome_completo": "ANA SOUZA",
            "partido": "PL",
            "pct_validos": 55.0,
            "destinacao": "Válido",
        },
        {
            "sq_candidato": "2",
            "nome_urna": "BETO",
            "nome_completo": "ROBERTO",
            "partido": "PT",
            "pct_validos": 45.0,
            "destinacao": "Válido",
        },
    ]
    pares = C.pares_estado("XX", linhas, urna)
    assert len(pares) == 1
    ana = pares[0]["candidatos"][0]
    assert ana["pesquisa_pct_validos"] == pytest.approx(50.0)
    assert ana["urna_pct_validos"] == pytest.approx(55.0)
    est = C.estatisticas(pares, lambda p: "direita" if p == "PL" else "esquerda")
    assert est["por_candidatura"]["erro_medio_absoluto"] == pytest.approx(
        (5.0 + (45.0 - 37.5)) / 2
    )


# ------------------------------------------------------- registro indeferido


def _fonte_indeferido(tmp_path, *, adulterar=False):
    """fonte.json sintético com duas matérias arquivadas e seus SHA-256."""
    pasta = tmp_path / "fonte_indeferido"
    pasta.mkdir()
    materias = []
    for i, (veiculo, quando) in enumerate(
        (
            ("Veículo A", "2026-10-03T20:17:38-03:00"),
            ("Veículo B", "2026-10-01T18:05:38-03:00"),
        )
    ):
        arq = pasta / f"materia_{i}.html"
        arq.write_text(f"<p>matéria {i}</p>", encoding="utf-8")
        materias.append(
            {
                "arquivo": str(arq),
                "veiculo": veiculo,
                "publicado_em": quando,
                "url": f"https://exemplo.invalid/{i}",
                "titulo": f"Título {i}",
                "sha256": hashlib.sha256(arq.read_bytes()).hexdigest(),
            }
        )
    if adulterar:
        materias[0]["sha256"] = "0" * 64
    fonte = pasta / "fonte.json"
    fonte.write_text(json.dumps({"fatos": [], "materias": materias}), "utf-8")
    return str(fonte)


def _tabela(fonte, nome="ANA DIREITA"):
    return {
        ("SP", nome): {
            "decisao": "O relator indeferiu o registro de Ana Direita.",
            "data": "2026-10-03",
            "status": "monocrática, pendente de plenário",
            "fonte": fonte,
        }
    }


@pytest.fixture(scope="module")
def indeferido(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("indeferido")
    ondas = [
        onda("SP", "datafolha", "2026-10-02", SP, inicio="2026-10-01", n=2000),
        onda("SP", "quaest", "2026-10-03", SP, inicio="2026-10-02", n=1500),
    ]
    pasta = escrever(tmp, ondas)
    tabela = _tabela(_fonte_indeferido(tmp))
    sem = prever(pasta)
    com = prever(pasta, registro_indeferido=tabela)
    return sem, com


def _probs(lista):
    return {p["nome"]: p["p_eleito"] for p in lista}


def test_registro_indeferido_remove_candidatura(indeferido):
    sem, com = indeferido
    sp = com["estados"]["SP"]
    assert sp["probabilidades"] == sem["estados"]["SP"]["probabilidades"]
    assert [c["chave"] for c in sp["cenarios"]] == [
        "registro_indeferido_ana",
        "registro_indeferido_ana_migracao",
    ]
    central = _probs(sp["probabilidades"])
    nulo, migracao = sp["cenarios"]
    for c in (nulo, migracao):
        nomes = {p["nome"] for p in c["probabilidades"]}
        assert "Ana Direita" not in nomes
        assert nomes == set(central) - {"Ana Direita"}
        assert sum(p["p_eleito"] for p in c["probabilidades"]) == pytest.approx(
            2.0, abs=1e-9
        )
        assert sum(p["p_primeiro"] for p in c["probabilidades"]) == pytest.approx(
            1.0, abs=1e-9
        )
        assert c["soma_p_eleito"] == pytest.approx(2.0, abs=1e-9)
        assert c["eleitos_provaveis"] == c["dupla_mais_provavel"]
        assert "Ana Direita" not in c["eleitos_provaveis"]
        assert sum(p["validos_central"] for p in c["probabilidades"]) <= 100 + 1e-9
    p_nulo, p_mig = _probs(nulo["probabilidades"]), _probs(migracao["probabilidades"])
    # Sem a candidatura, ninguém perde vaga nos mesmos sorteios.
    assert all(p_nulo[n] >= central[n] - 1e-12 for n in p_nulo)
    # Na migração, o mesmo grupo (Davi Novo) ganha e os demais perdem.
    assert migracao["receptores"] == ["Davi Novo"]
    for n in p_mig:
        if n in migracao["receptores"]:
            assert p_mig[n] >= p_nulo[n] - 1e-12
        else:
            assert p_mig[n] <= p_nulo[n] + 1e-12
    assert nulo["hipotese"].startswith("voto da candidatura vira nulo")
    assert nulo["fonte"]["veiculo"] == "Veículo A"


def test_registro_indeferido_alerta_e_fontes(indeferido):
    _, com = indeferido
    sp = com["estados"]["SP"]
    (alerta,) = sp["alertas"]
    assert alerta["titulo"] == "Registro indeferido pelo TSE em 03/10"
    assert alerta["candidato"] == "Ana Direita"
    assert alerta["candidato"] in _probs(sp["probabilidades"])
    assert alerta["marcador"] == "registro indeferido"
    for trecho in ("monocrática, pendente de plenário", "urna", "central"):
        assert trecho in alerta["texto"]
    assert len(alerta["fontes"]) == 2
    for f in alerta["fontes"]:
        assert {"veiculo", "publicado_em", "url", "arquivo", "sha256"} <= set(f)
    (val,) = com["validacao"]["registro_indeferido"]
    assert val["aplicado"] is True
    assert val["p_eleito_central"] == _probs(sp["probabilidades"])["Ana Direita"]
    assert all(m["sha256_conferido"] for m in val["materias_conferidas"])
    assert "\u2014" not in json.dumps(com, ensure_ascii=False)


def test_registro_indeferido_efeito_nacional(indeferido):
    _, com = indeferido
    s27 = com["senado_2027"]
    nulo, migracao = s27["cenarios"]
    assert [nulo["chave"], migracao["chave"]] == [
        "registro_indeferido_ana",
        "registro_indeferido_ana_migracao",
    ]
    for c in (nulo, migracao):
        assert c["ufs"] == ["SP"]
        assert c["fecha_em_81_em_todo_sorteio"] is True
        for g in ("direita", "centro", "esquerda"):
            assert set(c["por_grupo"][g]) == {"esperado", "ic90"}
        assert sum(v["esperado"] for v in c["por_grupo"].values()) == pytest.approx(81)
        for k in I.CHAVES_COMPOSICAO:
            assert 0.0 <= c[k] <= 1.0
    direita = s27["por_grupo"]["direita"]["esperado"]
    assert nulo["por_grupo"]["direita"]["esperado"] <= direita
    assert (
        migracao["por_grupo"]["direita"]["esperado"]
        >= nulo["por_grupo"]["direita"]["esperado"]
    )


def test_sem_tabela_saida_identica(indeferido):
    sem, com = indeferido
    for e in sem["estados"].values():
        assert "alertas" not in e and "cenarios" not in e
    assert "cenarios" not in sem["senado_2027"]
    assert "registro_indeferido" not in sem["validacao"]
    assert "registro_indeferido_regra" not in sem["parametros"]
    limpo = copy.deepcopy(com)
    for e in limpo["estados"].values():
        e.pop("alertas", None)
        e.pop("cenarios", None)
    limpo["senado_2027"].pop("cenarios")
    limpo["validacao"].pop("registro_indeferido")
    limpo["parametros"].pop("registro_indeferido_regra")
    assert limpo == sem


def test_registro_indeferido_nao_encontrado(tmp_path):
    pasta = escrever(tmp_path, [onda("SP", "quaest", "2026-10-02", SP)])
    tabela = _tabela("inexistente/fonte.json", nome="Ninguém Aqui")
    out = prever(pasta, sensibilidades=False, registro_indeferido=tabela)
    assert "alertas" not in out["estados"]["SP"]
    assert "cenarios" not in out["senado_2027"]
    (val,) = out["validacao"]["registro_indeferido"]
    assert val["aplicado"] is False
    assert "não está nas pesquisas" in val["motivo"]


def test_registro_indeferido_hash_divergente_para(tmp_path):
    pasta = escrever(tmp_path, [onda("SP", "quaest", "2026-10-02", SP)])
    tabela = _tabela(_fonte_indeferido(tmp_path, adulterar=True))
    with pytest.raises(ValueError, match="SHA-256"):
        prever(pasta, sensibilidades=False, registro_indeferido=tabela)


def test_sem_candidatura_nulo_e_migracao():
    validos = np.array([[0.40, 0.30, 0.20, 0.05, 0.05], [0.10, 0.35, 0.25, 0.20, 0.10]])
    sorteio = {"validos": validos}
    nulo = M.sem_candidatura(sorteio, 0)
    assert nulo["validos"].sum(axis=1) == pytest.approx([1.0, 1.0])
    assert nulo["eleitos"].tolist() == [[0, 1], [0, 1]]
    mig = M.sem_candidatura(sorteio, 0, [3])
    assert mig["validos"][:, 2] == pytest.approx([0.45, 0.30])
    assert mig["validos"].sum(axis=1) == pytest.approx([1.0, 1.0])
    assert mig["eleitos"].tolist() == [[0, 2], [0, 2]]


def test_tabela_real_bem_formada():
    for (uf, nome), entrada in B.REGISTRO_INDEFERIDO.items():
        assert uf in B.UFS and nome
        assert {"decisao", "data", "status", "fonte"} <= set(entrada)
        assert "\u2014" not in json.dumps(entrada, ensure_ascii=False)
        if not (B.ROOT / entrada["fonte"]).exists():
            pytest.skip("fonte.json do registro indeferido ausente neste checkout")
        fonte = I.ler_fonte(entrada)
        assert fonte["materias"]
        assert all(m["sha256_conferido"] is not False for m in fonte["materias"])
