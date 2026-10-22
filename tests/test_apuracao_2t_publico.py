"""Página pública da apuração do 2º turno: estrutura, GA, card social e contrato dos JSON de exemplo."""

import json
from pathlib import Path

import pytest
from ga_tag import GA_ID

RAIZ = Path(__file__).resolve().parent.parent
PAGINA = RAIZ / "docs" / "apuracao_2t_ao_vivo.html"
ASSETS = RAIZ / "docs" / "assets" / "apuracao_2t"
EXEMPLO = ASSETS / "exemplo"
EXPORTADOR = RAIZ / "apuracao" / "scripts" / "exportar-publico.ts"
LOOP = RAIZ / "apuracao" / "scripts" / "publicar-loop.sh"
TRAVESSAO = "—"

ARQUIVOS = [
    "estado",
    "config",
    "regioes",
    "ufs",
    "abstencao",
    "estaduais",
    "evolucao",
    "pausas",
    "secoes",
    "paralela",
    "anomalias",
    "resultado",
    "mapa",
]

CHAVES = {
    "regioes": {
        "at",
        "min",
        "ele",
        "cargo",
        "turno",
        "referencia_1t",
        "brasil",
        "regioes",
    },
    "ufs": {"at", "min", "ele", "cargo", "limiar_parada_min", "ufs"},
    "abstencao": {
        "at",
        "min",
        "ele",
        "cargo",
        "base",
        "brasil",
        "regioes",
        "ufs",
        "destaques",
    },
    "estaduais": {"at", "min", "ele", "cargo", "ufs"},
    "evolucao": {
        "at",
        "ele",
        "cargo",
        "passo_s",
        "candidatos",
        "series",
        "referencia_1t",
    },
    "pausas": {
        "at",
        "min",
        "limiar_min",
        "nacional",
        "soma_ufs",
        "ufs",
        "referencia_1t",
    },
    "secoes": {
        "at",
        "min",
        "desenho",
        "totais",
        "por_uf",
        "brasil",
        "tardias",
        "ultimas",
    },
    "paralela": {
        "at",
        "fonte",
        "atualizado_em",
        "erro",
        "recebidos",
        "conferencia",
        "cobertura_uf",
        "placar_bus",
        "divergencias",
        "ultimos",
    },
    "estado": {
        "agora",
        "pronto",
        "turno",
        "coletor",
        "db",
        "ultimo_snapshot",
        "br",
        "ufs",
    },
    "config": {"turno", "eleicoes", "ufs"},
    "resultado": {"ele", "cargo", "abr", "cand", "snapshot_id"},
    "mapa": {"nivel", "pai", "gerado_em", "unidades"},
}
AGREGADO = {
    "sigla",
    "nome",
    "ufs",
    "ts",
    "st",
    "snt",
    "pst",
    "te",
    "est",
    "comparecimento",
    "abstencao",
    "pa",
    "votos",
    "vv",
    "vb",
    "vn",
    "tv",
    "lider",
    "margem_pp",
    "vel_10min_spm",
    "eta_100_iso",
    "ref_1t",
    "atualizado_em",
}
UF_LINHA = {
    "uf",
    "nome",
    "regiao",
    "ts",
    "st",
    "snt",
    "pst",
    "te",
    "comparecimento",
    "abstencao",
    "pa",
    "munnr",
    "munpt",
    "munf",
    "votos",
    "lider",
    "margem_pp",
    "ultima_versao_em",
    "idade_s",
    "vel_10min_spm",
    "eta_100_iso",
    "parada",
    "ref_1t",
    "pendentes_maiores",
}
ESTADUAL = {
    "uf",
    "nome",
    "ts",
    "st",
    "pst",
    "te",
    "comparecimento",
    "abstencao",
    "pa",
    "munnr",
    "munpt",
    "munf",
    "cand",
    "lider",
    "margem_pp",
    "viradas",
    "ultima_versao_em",
    "idade_s",
    "ref_1t",
    "pa_final_1t",
}
BLOCO = {
    "n_mun",
    "n_mun_fechados",
    "te_fechado",
    "pct_te_fechado",
    "comparecimento",
    "abstencao",
    "pa_2t",
    "pa_1t_mesmos",
    "delta_pp",
}
ANOMALIA = {
    "id",
    "at",
    "tipo",
    "categoria",
    "severidade",
    "uf",
    "abr",
    "cargo",
    "texto",
    "detalhe",
    "derivado",
}


def carregar(nome: str):
    return json.loads((EXEMPLO / f"{nome}.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def pagina() -> str:
    return PAGINA.read_text(encoding="utf-8")


def test_pagina_existe_e_tem_ga_uma_vez(pagina: str):
    assert pagina.count(GA_ID) == 2
    assert pagina.count("gtag/js?id=") == 1
    assert GA_ID in pagina[: pagina.lower().find("</head>")]


def test_og_image_e_canonica(pagina: str):
    img = "https://brasil.arvor.co/img/og/apuracao_2t_ao_vivo.png"
    assert f'property="og:image" content="{img}"' in pagina
    assert f'name="twitter:image" content="{img}"' in pagina
    assert 'property="og:image:width" content="1200"' in pagina
    assert 'property="og:image:height" content="630"' in pagina
    assert (
        'rel="canonical" href="https://brasil.arvor.co/apuracao_2t_ao_vivo.html"'
        in pagina
    )
    assert (RAIZ / "docs" / "img" / "og" / "apuracao_2t_ao_vivo.png").exists()


def test_sem_travessao_nem_nos_assets():
    for arq in [PAGINA, ASSETS / "ap2t.js", ASSETS / "ap2t.css", EXPORTADOR, LOOP]:
        assert TRAVESSAO not in arq.read_text(encoding="utf-8"), arq.name
    for arq in EXEMPLO.glob("*.json"):
        assert TRAVESSAO not in arq.read_text(encoding="utf-8"), arq.name


def test_noscript_com_link_para_o_painel(pagina: str):
    assert "<noscript>" in pagina
    assert "precisa de JavaScript" in pagina
    assert (
        "totalizacao_painel.html"
        in pagina[pagina.find("<noscript>") : pagina.find("</noscript>")]
    )


def test_rotulos_obrigatorios(pagina: str):
    assert "Soma dos BUs recebidos, não projeção" in pagina
    assert "Base: municípios fechados" in pagina
    assert "pede explicação, não indica irregularidade" in pagina


@pytest.mark.parametrize("nome", ARQUIVOS)
def test_pagina_referencia_cada_json(pagina: str, nome: str):
    assert f"assets/apuracao_2t/{nome}.json" in pagina
    assert f"'{nome}'" in (ASSETS / "ap2t.js").read_text(encoding="utf-8")


def test_manifest_de_exemplo_confere_com_os_arquivos():
    import hashlib

    manifesto = carregar("manifest")
    assert set(manifesto["arquivos"]) == set(ARQUIVOS)
    total = 0
    for nome, info in manifesto["arquivos"].items():
        dados = (EXEMPLO / f"{nome}.json").read_bytes()
        assert hashlib.sha256(dados).hexdigest() == info["sha256"], nome
        assert len(dados) == info["bytes"], nome
        total += len(dados)
    assert total == manifesto["total_bytes"] < 2 * 1024 * 1024
    assert manifesto["pendentes"] == [] and manifesto["turno"] == 2


@pytest.mark.parametrize("nome", sorted(CHAVES))
def test_chaves_do_contrato_nos_exemplos(nome: str):
    assert CHAVES[nome] <= set(carregar(nome))


def test_agregados_ufs_e_estaduais_do_exemplo():
    regioes = carregar("regioes")
    assert [r["sigla"] for r in regioes["regioes"]] == [
        "N",
        "NE",
        "CO",
        "SE",
        "S",
        "ZZ",
    ]
    for agr in [regioes["brasil"], *regioes["regioes"]]:
        assert set(agr) >= AGREGADO
        assert set(agr["ref_1t"]) == {"pst_mesmo_relogio", "atraso_min", "pa_final_1t"}
        assert abs(sum(v["pvapn"] for v in agr["votos"].values()) - 100) < 0.05
    ufs = carregar("ufs")["ufs"]
    assert len(ufs) == 28
    assert [u["pst"] for u in ufs] == sorted(u["pst"] for u in ufs)
    assert all(set(u) >= UF_LINHA for u in ufs)
    estaduais = carregar("estaduais")
    assert [e["uf"] for e in estaduais["ufs"]] == ["AC", "AM", "DF", "ES", "RN", "TO"]
    assert estaduais["ele"] == 6260 and estaduais["cargo"] == 3
    assert all(set(e) >= ESTADUAL for e in estaduais["ufs"])


def test_abstencao_evolucao_pausas_e_alertas_do_exemplo():
    abst = carregar("abstencao")
    assert abst["base"] == "municipios_fechados"
    for bloco in [abst["brasil"], *abst["regioes"], *abst["ufs"]]:
        assert set(bloco) >= BLOCO
    assert all(
        {"uf", "cd", "nm", "te", "pa_2t", "pa_1t", "delta_pp", "fechou_min"} <= set(m)
        for m in abst["destaques"]["subiu"]
    )
    evo = carregar("evolucao")
    assert "BR" in evo["series"]
    assert all(len(p) == 5 for p in evo["series"]["BR"])
    assert set(evo["referencia_1t"]) == set(evo["series"])
    pausas = carregar("pausas")
    assert pausas["referencia_1t"]["pausa_geral"] == {
        "de": "19:32",
        "ate": "20:02",
        "minutos": 29.6,
    }
    anomalias = carregar("anomalias")
    assert len(anomalias) == 60 and all(set(a) >= ANOMALIA for a in anomalias)


def test_paralela_do_exemplo_tem_a_forma_do_contrato():
    par = carregar("paralela")
    assert par["fonte"] == "supabase" and par["erro"] is None
    assert {
        "iguais",
        "divergentes",
        "tse_ainda_nao_publicou",
        "erro",
        "fora_do_oficial",
        "pendentes",
    } <= set(par["conferencia"])
    assert {"presidente", "governador"} <= set(par["placar_bus"])
    assert all(
        {"uf", "mun", "zona", "secao", "recebido_em", "conferido_em", "campos"}
        <= set(d)
        for d in par["divergencias"]
    )


def test_exportador_tem_cabecalho_de_uso_e_cobre_as_rotas():
    texto = EXPORTADOR.read_text(encoding="utf-8")
    assert texto.startswith("// Uso: bun run scripts/exportar-publico.ts")
    for rota in [
        "/api/estado",
        "/api/config",
        "/api/2t/regioes",
        "/api/2t/ufs",
        "/api/2t/abstencao",
        "/api/2t/estaduais",
        "/api/2t/evolucao?nivel=regiao&passo=120",
        "/api/2t/pausas",
        "/api/2t/secoes",
        "/api/2t/paralela",
        "/api/anomalias?limit=60",
        "/api/resultado?ele=6258&cargo=1&abr=br",
        "/api/mapa?ele=6258&cargo=1&nivel=uf",
    ]:
        assert rota in texto, rota
    for nome in ARQUIVOS:
        assert f'arquivo: "{nome}"' in texto, nome
    assert "manifest.json" in texto and "sha256" in texto


def test_loop_documenta_como_ligar_e_desligar():
    texto = LOOP.read_text(encoding="utf-8")
    assert "Ligar" in texto and "Desligar" in texto
    assert "INTERVALO_S" in texto and "300" in texto
    assert "docs/assets/apuracao_2t" in texto
    assert "apuração 2T: snapshot" in texto
    assert "publicar-" in texto
