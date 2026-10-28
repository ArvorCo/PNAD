"""Capítulo ``logs`` do dossiê do 2º turno: contas, contrato de ``logs.json`` e página."""

import json
from pathlib import Path

import pandas as pd
import pytest
from apuracao_2t_2026 import logs_cadencia as C
from apuracao_2t_2026 import logs_reinicio as R
from apuracao_2t_2026 import pagina_cap_logs as CAP
from apuracao_2t_2026.logs_amostra_1t import sorteada
from apuracao_2t_2026.logs_texto import markdown
from apuracao_2t_2026.pagina_comum import DADOS, dados_2t
from apuracao_2026.pagina_comum import Capitulo

ROOT = Path(__file__).resolve().parents[1]
LOGS = DADOS / "logs.json"


# ------------------------------------------------------------------ contas


def test_sorteio_deterministico_e_proporcao():
    assert sorteada("ac", "01007", 9, 1) == sorteada("AC", "01007", 9, 1)
    n = sum(sorteada("sp", "71072", 1, s) for s in range(1, 5001))
    assert 850 < n < 1150


def test_deslocamento_pela_hora_modal_do_primeiro_voto():
    t2 = pd.DataFrame(
        {
            "uf": ["SP", "SP", "AC", "AC", "AM", "ZZ"],
            "mun": ["1", "1", "2", "2", "3", "4"],
            "primeiro_s": [
                8 * 3600 + 60,
                8 * 3600 + 5,
                6 * 3600 + 9,
                6 * 3600,
                7 * 3600,
                3 * 3600,
            ],
        }
    )
    off = C.deslocamentos(t2).set_index(["uf", "mun"])["off"].to_dict()
    assert off == {("SP", "1"): 0, ("AC", "2"): 2, ("AM", "3"): 1}


def test_perfil_converte_e_soma_cem():
    cph = pd.Series(
        [json.dumps({"6": 10, "14": 10}), json.dumps({"8": 10, "17": 5, "19": 5})]
    )
    off = pd.Series([2, 0])
    p = C.perfil(cph, off)
    assert p["computados"] == 40
    assert p["pct"]["8"] == 50.0  # 6h do Acre + 8h de São Paulo
    assert p["pct"]["16"] == 25.0
    assert p["computados_17_19"] == 5
    assert p["computados_depois_19"] == 5
    horas = sum(v for k, v in p["pct"].items() if k != "19")
    assert horas + p["pct"]["19"] == pytest.approx(100.0)


def test_diferenca_em_diferencas_desconta_o_lugar():
    linhas = []
    for mun, base in (("A", 40.0), ("B", 60.0)):
        for s in range(10):
            linhas.append(
                {
                    "uf": "SP",
                    "mun": mun,
                    "zona": 1,
                    "secao": s,
                    "fatia_f": base - 2,
                    "fatia_f1": base,
                }
            )
    df = pd.DataFrame(linhas)
    marca = pd.Series([False] * len(df))
    # seção marcada em A: nível 5 pontos acima do município, mesma variação de −2
    df.loc[0, ["fatia_f", "fatia_f1"]] = [43.0, 45.0]
    marca[0] = True
    # seção marcada em B: mesma variação do município mais 1 ponto
    df.loc[10, ["fatia_f", "fatia_f1"]] = [59.0, 60.0]
    marca[10] = True
    out = R.comparar_voto(df, marca)
    assert out["secoes_com_sinal"] == 2
    assert out["dif_em_dif_contra_1t"]["n"] == 2
    assert out["dif_em_dif_contra_1t"]["media_pp"] == pytest.approx(0.5)
    assert out["contra_vizinhas_2t"]["media_pp"] == pytest.approx(3.0)


def test_poucas_vizinhas_saem_da_comparacao():
    df = pd.DataFrame(
        {
            "uf": "SP",
            "mun": "A",
            "zona": 1,
            "secao": range(4),
            "fatia_f": 50.0,
            "fatia_f1": 50.0,
        }
    )
    out = R.comparar_voto(df, pd.Series([True, False, False, False]))
    assert out["dif_em_dif_contra_1t"]["n"] == 0


# ------------------------------------------------------------------ contrato de logs.json


@pytest.fixture(scope="module")
def L():
    if not LOGS.exists():
        pytest.skip("logs.json ausente: rode scripts/apuracao-2t-2026-logs.py")
    return json.loads(LOGS.read_text(encoding="utf-8"))


def test_cobertura_fecha(L):
    c = L["cobertura"]
    assert c["contagem_confere"] + len(c["contagem_nao_confere"]) == c["lidos"]
    assert c["biometria_confere"] + c["biometria_nao_conferida"] == c["lidos"]
    assert (
        c["biometria_ausente_bu"] + c["biometria_por_contagem"]
        <= c["biometria_nao_conferida"]
    )
    assert (
        c["lidos"] + sum(c["situacoes"].values()) - c["situacoes"].get("lido", 0)
        == c["catalogadas"]
    )


def test_regra2_fecha(L):
    g = L["regra2"]
    assert (
        g["so_mr_antes_da_zeresima"] + g["erro_tecnico_regra2"] == g["secoes_com_erro"]
    )
    assert (
        g["com_mensagem_alheia_a_mr"] + g["so_mr_depois_da_zeresima"]
        == g["erro_tecnico_regra2"]
    )
    assert g["mudanca"].get("versao") == "2"


def test_matriz_soma_as_secoes_nos_dois(L):
    p = L["persistencia"]
    assert sum(p["matriz"].values()) == p["nos_dois"]


def test_cadencia_soma_cem_e_amostra_de_um_quinto(L):
    c = L["cadencia"]
    for perfil in (
        c["brasil_2t"],
        c["amostra_1t"]["brasil_1t"],
        c["amostra_1t"]["brasil_2t_mesmas"],
    ):
        assert sum(perfil["pct"].values()) == pytest.approx(100.0, abs=0.05)
    assert 0.18 < c["amostra_1t"]["secoes"] / c["secoes_2t"] < 0.22
    assert len(c["lista_depois_19"]) == c["ultimo_voto"]["depois_19"]
    t19 = c["bu_apos_19h"]
    assert (
        t19["ultimo_voto_ate_1715"]
        + t19["ultimo_voto_1715_1900"]
        + t19["ultimo_voto_depois_19"]
        == t19["secoes"]
    )


def test_reinicios_somam(L):
    r = L["reinicios"]
    assert r["mesma_urna"] + r["troca_ou_contingencia"] == r["secoes"]
    assert r["so_2t"] + r["nos_dois"] == r["secoes"]
    for v in r["voto"]:
        lo, hi = v["dif_em_dif_contra_1t"]["ic95_pp"]
        assert lo <= v["dif_em_dif_contra_1t"]["media_pp"] <= hi


def test_integrado_lista_e_links(L):
    ig = L["integrado"]
    assert len(ig["secoes"]) == ig["as_duas"]
    for s in ig["secoes"][:50]:
        assert s["escore_bu"] >= 2 and s["atencao_log"] >= 2
        assert (
            s["politizese"]
            == f"politizese.html#uf={s['uf']}&z={s['zona']}&s={s['secao']}"
        )


def test_serie_mr_grupos_estruturais_numa_zona(L):
    for g in L["metadados"]["serie_mr"]["estruturais"]:
        assert (
            len(g["zonas"]) == 1
            and g["secoes"] >= 2
            and g["tipo_arquivo_urna"] == g["secoes"]
        )


def test_memorando_sem_travessao(L):
    md = markdown(L)
    assert "—" not in md
    assert "fraude" not in md.lower()


# ------------------------------------------------------------------ página


@pytest.fixture(scope="module")
def capitulo(L):
    d = dados_2t()
    cap = Capitulo(
        "logs",
        "10",
        "Logs",
        "O que os logs das 499 mil urnas dizem",
        ("logs.json",),
        lambda d: "",
    )
    return CAP.render(d, cap)


def test_capitulo_regras_de_texto(capitulo):
    assert "—" not in capitulo
    assert "fraude" not in capitulo.lower()
    assert "não prova irregularidade" in capitulo
    for selo in (
        "Verificado",
        "Inferência",
        "Hipótese",
        "Achado contrário",
        "Juízo editorial",
    ):
        assert selo in capitulo, selo


def test_capitulo_tem_as_figuras_dos_sete_blocos(capitulo):
    for nome in (
        "logs_excecoes",
        "logs_regra2",
        "logs_matriz",
        "logs_persistencia",
        "logs_cadencia",
        "logs_cadencia_regioes",
        "logs_reinicio_hora",
        "logs_bateria_chuva",
        "logs_voto",
        "logs_serie_mr",
        "logs_integrado_mapa",
        "logs_rdv_nulos",
    ):
        assert f'id="fig-{nome}"' in capitulo, nome
    assert capitulo.count("politizese.html#uf=") >= 50
    assert "politizese_mapa.html" in capitulo


def test_modulos_abaixo_de_mil_linhas():
    pasta = ROOT / "scripts/apuracao_2t_2026"
    for arq in [*pasta.glob("logs_*.py"), *pasta.glob("pagina_*logs*.py")]:
        assert len(arq.read_text(encoding="utf-8").splitlines()) < 1000, arq.name


def test_voto_ponderado_com_sem_peso():
    linhas = [
        {
            "uf": "SP",
            "mun": "A",
            "zona": 1,
            "secao": s,
            "fatia_f": 48.0,
            "fatia_f1": 50.0,
            "fl": 100,
            "lu": 100,
        }
        for s in range(6)
    ]
    linhas += [
        {
            "uf": "SP",
            "mun": "A",
            "zona": 1,
            "secao": 10,
            "fatia_f": 49.0,
            "fatia_f1": 50.0,
            "fl": 300,
            "lu": 300,
        },
        {
            "uf": "SP",
            "mun": "A",
            "zona": 1,
            "secao": 11,
            "fatia_f": 45.0,
            "fatia_f1": 50.0,
            "fl": 50,
            "lu": 50,
        },
    ]
    df = pd.DataFrame(linhas)
    marca = pd.Series([False] * 6 + [True, True])
    out = R.comparar_voto(df, marca)
    # DiD por seção: +1 (peso 600) e −3 (peso 100)
    assert out["ponderado"] is True
    assert out["dif_em_dif_contra_1t"]["media_pp"] == pytest.approx(
        (600 - 300) / 700, abs=1e-3
    )
    assert out["sem_peso"]["dif_em_dif_contra_1t"]["media_pp"] == pytest.approx(-1.0)


def test_serie_mr_exterior_separado_e_grupos(L):
    s = L["metadados"]["serie_mr"]
    assert all(g["zona"][:2] != "ZZ" for g in s["voto_por_grupo"])
    ext = sum(g["secoes"] for g in s["estruturais"] if g["ufs"] == ["ZZ"])
    assert s["voto_exterior"]["secoes_marcadas"] == ext
    br = s["voto_estruturais_brasil"]
    assert br["ponderado"] and br["secoes_com_sinal"] == sum(
        g["secoes"] for g in s["estruturais"] if g["ufs"] != ["ZZ"]
    )
    M = json.loads((DADOS / "metadados.json").read_text(encoding="utf-8"))
    linha = next(v for v in M["voto"] if v["grupo"] == "mr_mesma_serie_na_zona")
    assert linha["n"] == br["secoes_com_sinal"]  # mesma definição: Brasil sem exterior


def test_rdv_resumo_fecha(L):
    R = L["rdv"]
    assert R["conferem"] == R["com_rdv"] and R["divergencias"] == 0
    assert R["com_rdv"] + R["sem_aux"] + R["aux_sem_rdv"] == R["tentadas"]
    s = R["seis_ufs"]
    assert sum(u["nulos_governador"] for u in R["ufs"]) == s["nulos_governador"]
    assert (
        sum(u["governador_com_13"] + u["governador_com_22"] for u in R["ufs"])
        == s["governador_com_numero_de_presidente"]
    )
    assert (
        sum(u["presidente_com_governador"] for u in R["ufs"])
        == s["presidente_com_numero_de_governador"]
    )
    for u in R["ufs"]:
        for x in u["limites"]:
            assert x["min_pct"] <= x["independencia_pct"] <= x["max_pct"]


def test_certificado_da_urna_nos_dois_turnos(L):
    """Com a coleta completa dos `.vsc` dos dois turnos, o bloco de certificados entra em
    logs.json sem incoerência e o capítulo o publica."""
    e = L["metadados"]["dossie_metadados"]["entre_turnos_vsc"]
    assert e["secoes_com_vsc_nos_dois_turnos"] > 490_000
    assert e["mesma_urna_certificado_diferente"] == 0
    assert e["urna_diferente_mesmo_certificado"] == 0
    assert (
        e["mesma_urna_mesmo_certificado"] + e["urna_trocada_certificado_trocado"]
        == e["secoes_com_vsc_nos_dois_turnos"]
    )
    assert e["outra_secao_mesma_zona"] <= e["outra_secao_mesmo_municipio"]
    assert (
        e["outra_secao_mesmo_municipio"] <= e["certificado_do_1t_em_outra_secao_no_2t"]
    )
    assert e["carga"]["carga_nova_fora_do_intervalo"] == 0
    assert "certificado_do_1t_em_outra_secao_no_2t_casos" not in e


def test_capitulo_publica_certificado_entre_turnos(capitulo):
    assert "Certificado da urna nos dois turnos" in capitulo
    assert "a repetição alegada em 2022 não aparece em 2026" in capitulo


def test_pendencia_tse_usa_numeros_do_banco_e_explica_como_pedir():
    from apuracao_2t_2026 import pagina_texto_logs as T

    L = json.loads((DADOS / "logs.json").read_text(encoding="utf-8"))
    h = T.pendencia_tse(L)
    assert "Pendência documental: como pedir ao TSE" in h
    assert (
        "Lei 12.527/2011" in h and "certificado_do_1t_em_outra_secao_no_2t_casos" in h
    )
    assert "—" not in h and "fraude" not in h.lower()
    e = L["metadados"]["dossie_metadados"]["entre_turnos_vsc"]
    assert str(e["certificado_do_1t_em_outra_secao_no_2t"]) in h
