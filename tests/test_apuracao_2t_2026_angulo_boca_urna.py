"""Ângulo da boca de urna no 2º turno: regras, fontes arquivadas e bloco da página."""

import json
import re

import pytest
from apuracao_2t_2026 import angulo_boca_urna as ab
from apuracao_2t_2026 import pagina_texto_angulo_boca_urna as TX

LINHAS_SUPABASE = [
    {"k": "total", "v": "", "n": 8},
    {"k": "status", "v": "descartado", "n": 6},
    {"k": "status", "v": "novo", "n": 2},
    {"k": "tipo", "v": "outro", "n": 8},
    {"k": "uf", "v": "AC", "n": 6},
    {"k": "uf", "v": "CE", "n": 1},
    {"k": "uf", "v": "DF", "n": 1},
    {"k": "turno", "v": "2", "n": 8},
    {"k": "presenciou", "v": "true", "n": 3},
    {"k": "presenciou", "v": "false", "n": 5},
    {"k": "cadastro", "v": "true", "n": 3},
    {"k": "cadastro", "v": "false", "n": 5},
    {"k": "moderacao", "v": "descartado", "n": 6},
    {"k": "primeiro", "v": "2026-10-26 04h", "n": 0},
    {"k": "ultimo", "v": "2026-10-26 21h", "n": 0},
]


def test_contagens_completas_com_zeros():
    r = ab.organizar_contagens(LINHAS_SUPABASE, "2026-10-27T00:00:00Z")
    assert r["total"] == 8
    assert r["por_status"] == {"novo": 2, "lido": 0, "descartado": 6}
    assert set(r["por_tipo"]) == set(ab.TIPOS_RELATO)
    assert r["por_tipo"]["boca_de_urna"] == 0 and r["por_tipo"]["outro"] == 8
    assert r["pressao_sobre_o_eleitor"] == 0
    assert r["ativos"] == 2
    assert r["por_uf"] == {"AC": 6, "CE": 1, "DF": 1}
    assert r["primeiro_relato_utc_hora"] == "2026-10-26 04h"
    # nada além de contagens e horas truncadas
    assert not any(k in r for k in ("texto", "contato", "ip_hash", "id"))


def test_falha_de_acesso_vira_registro_e_nao_parada():
    def quebrada():
        raise RuntimeError("API de gestão respondeu HTTP 401")

    r = ab.relatos_contagens(quebrada)
    assert "erro" in r and "HTTP 401" in r["erro"]
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", r["consultado_em"])


def test_tipos_e_status_iguais_ao_exportador():
    from politize_se import relatos

    assert ab.TIPOS_RELATO == relatos.TIPOS
    assert ab.STATUS_RELATO == relatos.STATUS


@pytest.mark.parametrize(
    ("quem", "classe"),
    [
        ("Polícia Militar de SP", "registro_oficial"),
        ("Claudio de Mello Tavares (presidente do TRE-RJ)", "registro_oficial"),
        ("Ministério da Justiça (balanço preliminar até 19h) e PF", "registro_oficial"),
        ("Juiz Tiago Ducatti (1ª Zona Eleitoral de SP)", "registro_oficial"),
        ("Poder360; PL diz desconhecer os casos", "relato_imprensa"),
        ("Federação Brasil da Esperança (PT, PCdoB, PV)", "relato_imprensa"),
        ("fonte anônima ouvida pela reportagem", "relato_anonimo"),
        (None, "relato_imprensa"),
    ],
)
def test_classificacao_por_regra(quem, classe):
    assert ab.classificar({"quem_disse": quem}) == classe


def test_pertinencia_e_subtema():
    assert ab.pertinente({"tema": "ocorrencias_policiais", "titulo": "", "resumo": ""})
    assert ab.pertinente(
        {
            "tema": "votacao_prorrogada",
            "titulo": "x",
            "resumo": "fiscal preso por boca de urna",
        }
    )
    assert not ab.pertinente(
        {
            "tema": "votacao_prorrogada",
            "titulo": "x",
            "resumo": "operações da PRF em 2022",
        }
    )
    assert (
        ab.subtema({"titulo": "Fiscais levados à PF", "resumo": "boca de urna"})
        == "boca_de_urna"
    )
    assert ab.subtema({"titulo": "", "resumo": "ônibus parados"}) == "transporte"


def test_derivado_boca_de_urna():
    assert (
        ab.derivado_boca_de_urna({"ocorrencias": 733, "boca_de_urna_pct": 12.8}) == 94
    )
    assert (
        ab.derivado_boca_de_urna({"ocorrencias": 618, "boca_de_urna_pct": 13.3}) == 82
    )
    assert (
        ab.derivado_boca_de_urna({"ocorrencias": 89, "boca_de_urna_pct": None}) is None
    )


@pytest.mark.skipif(not ab.FONTES_NOTICIAS.exists(), reason="noticias_fontes ausente")
def test_balancos_batem_com_as_paginas_arquivadas():
    for b in ab.balancos():
        caminho = ab.ROOT / b["fonte_arquivo"]
        if not caminho.exists():
            pytest.skip(f"{b['arquivo']} ausente")
        texto = ab.texto_html(caminho)
        assert b["total_conferido_no_arquivo"]
        if b["boca_de_urna_pct"] is not None:
            pct = str(b["boca_de_urna_pct"]).replace(".", ",")
            assert f"boca de urna ({pct}%)" in texto
        assert len(b["sha256"]) == 64


@pytest.mark.skipif(not ab.ORIGINAIS_FISCAIS.exists(), reason="originais ausentes")
def test_base_legal_conferida_e_hash_igual_ao_manifesto():
    L = ab.base_legal()
    for nome in ("lei_9504", "res_23751"):
        n = L[nome]
        if not n["existe"]:
            pytest.skip(f"{n['arquivo']} ausente")
        assert (
            n["sha256_manifesto"] is None
            or n["sha256_arquivo"] == n["sha256_manifesto"]
        )
        assert all(d["conferido_no_arquivo"] for d in n["dispositivos"]), nome


@pytest.mark.skipif(not ab.NOTICIAS.exists(), reason="noticias_noite.json ausente")
def test_ocorrencias_do_acervo():
    N = json.loads(ab.NOTICIAS.read_text(encoding="utf-8"))
    oc = ab.ocorrencias_publicas(N)
    assert oc["n"] >= 10
    assert sum(oc["por_classe"].values()) == oc["n"]
    assert oc["por_classe"]["registro_oficial"] >= 1
    assert all(x["sha256"] for x in oc["itens"])
    assert [x["quando"] for x in oc["itens"]] == sorted(
        x["quando"] for x in oc["itens"]
    )
    assert oc["boca_de_urna_nominais"]


def _dados_ficticios():
    return {
        "o_que_a_totalizacao_nao_mede": "nenhum BU registra abordagem",
        "relatos": ab.organizar_contagens(LINHAS_SUPABASE, "2026-10-27T00:18:06Z"),
        "balancos_mjsp": [
            {
                **b,
                "boca_de_urna_n_derivado": ab.derivado_boca_de_urna(b),
                "fonte_arquivo": "x",
                "sha256": "0" * 64,
                "total_conferido_no_arquivo": True,
            }
            for b in ab.BALANCOS_MJSP
        ],
        "ocorrencias": {
            "n": 2,
            "por_classe": {
                "registro_oficial": 1,
                "relato_imprensa": 1,
                "relato_anonimo": 0,
            },
            "por_subtema": {"boca_de_urna": 2},
            "boca_de_urna_nominais": [
                {
                    "quando": "2026-10-25T14:41:01-03:00",
                    "veiculo": "Poder360",
                    "resumo": "Dois fiscais levados à PF.",
                    "classe": "relato_imprensa",
                    "quem_disse": "Poder360",
                    "url": "https://example.org/a",
                }
            ],
            "itens": [],
        },
        "base_legal": {
            "lei_9504": {
                "dispositivos": [
                    {**d, "conferido_no_arquivo": True}
                    for d in ab.LEI_9504["dispositivos"]
                ]
            },
            "res_23751": {
                "dispositivos": [
                    {**d, "conferido_no_arquivo": True}
                    for d in ab.RES_23751["dispositivos"]
                ]
            },
        },
        "caminho_documental": ab.CAMINHO_DOCUMENTAL,
    }


def test_bloco_vazio_sem_json():
    assert TX.bloco({}) == ""
    assert TX.bloco({TX.ARQ: None}) == ""


def test_bloco_com_json_ficticio():
    h = TX.bloco({TX.ARQ: _dados_ficticios()})
    assert h.startswith("<h4>Boca de urna")
    assert "733" in h and "12,8%" in h and "94" in h
    assert "art. 39, § 5º, II" in h and "art. 128, V" in h
    assert "8 relatos" in h and "AC 6" in h
    assert 'class="selo selo-verificado"' in h and 'class="selo selo-juizo"' in h
    assert "—" not in h
    assert "fraude" not in h.lower()


def test_bloco_com_erro_de_acesso():
    d = _dados_ficticios()
    d["relatos"] = {"consultado_em": "2026-10-27T00:00:00Z", "erro": "HTTP 401"}
    h = TX.bloco({TX.ARQ: d})
    assert "não respondeu" in h and "HTTP 401" in h


def test_markdown_e_textos_sem_travessao_nem_fraude():
    d = {
        "gerado_em": "2026-10-27T00:00:00Z",
        "script": "s",
        "rotulo": ab.ROTULO,
        **_dados_ficticios(),
    }
    md = ab.markdown(d)
    assert "| 733 |" in md and "Supabase" not in md.split("## Canal")[0]
    textos = md + json.dumps(
        ab.CAMINHO_DOCUMENTAL + ab.BALANCOS_MJSP, ensure_ascii=False
    )
    textos += json.dumps([ab.LEI_9504, ab.RES_23751], ensure_ascii=False)
    assert "—" not in textos
    assert "fraude" not in textos.lower()
