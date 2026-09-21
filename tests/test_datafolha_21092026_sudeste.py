"""Camada do Sudeste: recomposicao, limites de Frechet, margens do IPF e cobertura."""

import csv
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs/assets"
JSON_PATH = ASSETS / "datafolha_21092026_sudeste.json"
CSV_PATH = ASSETS / "datafolha_21092026_sudeste.csv"

if not JSON_PATH.exists():  # pragma: no cover - depende do gerador ter rodado
    pytest.skip(
        "rode scripts/datafolha-21092026-sudeste.py antes", allow_module_level=True
    )

D = json.loads(JSON_PATH.read_text(encoding="utf-8"))
ESTADOS = D["estados"]
LULA = "Lula (PT)"
FLAVIO = "Flavio Bolsonaro (PL)"
UFS = ("SP", "RJ", "MG")


def variantes():
    for uf, estado in D["transferencia"].items():
        for cenario, bloco in estado.items():
            if not isinstance(bloco, dict) or "variantes" not in bloco:
                continue
            for prior, matriz in bloco["variantes"].items():
                yield uf, cenario, prior, matriz


def test_tres_estados_com_a_mesma_base_nos_dois_cargos():
    assert set(ESTADOS) == set(UFS)
    for uf in UFS:
        estado = ESTADOS[uf]
        assert estado["campo"] == "08–10/09/2026"
        assert estado["governador"]["turno2"]
        assert estado["presidente"]["turno2"][FLAVIO] > 0
    assert ESTADOS["SP"]["n"] == 1610
    assert ESTADOS["RJ"]["n"] == 1204
    assert ESTADOS["MG"]["n"] == 1204


def test_recomposicao_fica_dentro_de_um_ponto_e_meio():
    provas = D["provas_de_leitura"]
    assert provas["total"] > 2000
    assert provas["pior_residuo_pp"] <= provas["limite_pp"]
    assert provas["acima_de_1_05pp"] == []


def test_particao_fechada_e_medida_nao_declarada():
    # Renda nunca fecha: recusa e nao sabe existem no cartao e nao tem coluna.
    for uf in UFS:
        cobertura = ESTADOS[uf]["cobertura_dos_recortes"]
        assert cobertura["renda"]["particao_fechada"] is False
        assert cobertura["religiao"]["particao_fechada"] is False
        assert "renda" in ESTADOS[uf]["particoes_abertas"]
        for dimensao in ("sexo", "idade", "escolaridade", "ocupacao", "natureza"):
            assert dimensao in ESTADOS[uf]["particoes_fechadas"]
    # O partido de preferencia fecha em SP e MG e nao fecha no Rio.
    assert "partido" in ESTADOS["SP"]["particoes_fechadas"]
    assert "partido" in ESTADOS["MG"]["particoes_fechadas"]
    assert "partido" in ESTADOS["RJ"]["particoes_abertas"]


def test_frechet_envolve_toda_celula_do_ipf():
    conferidas = 0
    for uf, cenario, prior, matriz in variantes():
        for celula in matriz["celulas"]:
            baixo = celula["frechet_min_pp"] - 1e-6
            alto = celula["frechet_max_pp"] + 1e-6
            assert baixo <= celula["valor_pp"] <= alto, (
                uf,
                cenario,
                prior,
                celula,
            )
            conferidas += 1
    assert conferidas > 500


def test_margens_do_ipf_fecham_exatamente():
    for uf, cenario, prior, matriz in variantes():
        assert matriz["residuo_margem_linha_pp"] < 1e-4, (uf, cenario, prior)
        assert matriz["residuo_margem_coluna_pp"] < 1e-4, (uf, cenario, prior)
        for linha, destinos in matriz["matriz_pp"].items():
            soma = sum(destinos.values())
            # As celulas sao gravadas com tres casas; a folga so cobre isso.
            folga = 0.0005 * len(destinos) + 0.005
            assert abs(soma - matriz["origem_pct"][linha]) < folga


def test_linha_publicada_entra_fixa_como_medicao():
    publicados = {
        (item["uf"], item["destino_pergunta"], origem, destino): valor
        for item in D["cruzamentos_publicados"]
        for origem, linha in item["linhas"].items()
        for destino, valor in linha.items()
    }
    assert len(publicados) >= 13
    conferidas = 0
    for uf, cenario, _prior, matriz in variantes():
        pergunta = (
            "presidente, 1o turno"
            if cenario.endswith("pres1")
            else "presidente, 2o turno"
        )
        if not cenario.startswith("gov1"):
            continue
        for (u, p, origem, destino), valor in publicados.items():
            if (u, p) != (uf, pergunta):
                continue
            if destino not in matriz["condicional_pct"].get(origem, {}):
                continue
            assert matriz["condicional_pct"][origem][destino] == pytest.approx(
                valor, abs=0.02
            )
            celula = next(
                c
                for c in matriz["celulas"]
                if c["origem"] == origem and c["destino"] == destino
            )
            assert celula["estado"] == "medida"
            conferidas += 1
    assert conferidas > 0


def test_celula_de_segundo_turno_respeita_o_piso_medido_no_primeiro():
    """A regra nova da casa: estimativa não fica abaixo de medição da mesma amostra.

    Para toda origem com linha publicada de 1º turno para um finalista, o valor
    de 2º turno precisa ficar acima do piso, que é a linha medida multiplicada
    pela retenção declarada. Antes da correção, São Paulo entregava 2,232 pontos
    de Tarcísio para Lula contra 5,88 pontos já medidos no 1º turno.
    """
    conferidas = 0
    for uf, cenario, prior, matriz in variantes():
        if cenario == "gov1_pres1":
            continue
        for celula in matriz["celulas"]:
            piso = celula.get("piso_medido_pp")
            if piso is None:
                continue
            assert celula["estado"] == "ancorada", (uf, cenario, prior, celula)
            assert celula["valor_pp"] >= piso - 1e-6, (uf, cenario, prior, celula)
            assert celula["limite_inferior_informado_pp"] >= piso - 1e-6
            assert celula["limite_inferior_informado_pp"] >= celula["frechet_min_pp"]
            conferidas += 1
    assert conferidas >= 12


def test_sao_paulo_usa_cadeia_e_sai_acima_do_valor_antigo():
    sp = D["transferencia"]["SP"]
    for cenario in ("gov1_pres2", "gov2_pres2"):
        assert sp[cenario]["motor"] == "cadeia_3niveis"
    medido_pp = 49 / 99 * 12  # linha da p. 4 aplicada a massa normalizada
    for cenario in ("gov1_pres2", "gov2_pres2"):
        celula = sp[cenario]["robustez"]["celula_direita_para_lula"]
        assert celula["valor_pp"] > 2.232, cenario
        assert celula["valor_pp"] >= medido_pp * 0.93, cenario
    # O vazamento total subiu porque o piso medido entrou na conta.
    antes = sp["gov2_pres2"]["robustez"]["vazamento_sem_ancoragem_pct"]
    depois = sp["gov2_pres2"]["robustez"]["vazamento_da_direita_pct"]
    assert min(depois.values()) > min(antes.values())


def test_a_cadeia_fecha_nas_margens_do_estagio_e_do_segundo_turno():
    for uf, cenario, prior, matriz in variantes():
        if matriz.get("motor") != "cadeia_3niveis":
            continue
        assert matriz["celulas_do_cubo"] > 0, (uf, cenario, prior)
        assert matriz["residuo_margem_linha_pp"] < 1e-6
        assert matriz["residuo_margem_coluna_pp"] < 1e-6
        for linha, destinos in matriz["matriz_pp"].items():
            assert sum(destinos.values()) == pytest.approx(
                matriz["origem_pct"][linha], abs=0.01
            )


def test_linha_medida_de_dois_turnos_nao_contraria_a_de_um_turno():
    """Onde o instituto mede os dois turnos, o par precisa ser coerente."""
    total = 0
    for uf in UFS:
        linhas = D["transferencia"][uf]["coerencia_das_linhas_medidas"]
        for linha in linhas:
            assert linha["coerente"], (uf, linha)
            total += 1
    assert total == 10
    # A mais apertada de todas: Patrus para Flávio, 3% nos dois turnos.
    apertada = min(
        (
            linha
            for uf in UFS
            for linha in D["transferencia"][uf]["coerencia_das_linhas_medidas"]
        ),
        key=lambda linha: linha["folga_pp"],
    )
    assert apertada["origem"].startswith("Patrus")
    assert apertada["folga_pp"] < 0.1


def test_fidelidade_estadual_tem_a_condicao_necessaria_conferida():
    for uf in UFS:
        bloco = D["transferencia"][uf]["fidelidade_estadual_conferida"]
        assert bloco["linhas"]
        for linha in bloco["linhas"]:
            assert linha["compativel"], (uf, linha)
            assert linha["variacao_pp"] >= 0


def test_linha_publicada_vem_com_base_e_intervalo():
    """Medição em subamostra pequena também tem incerteza, e ela é publicada."""
    ruas = None
    for uf in UFS:
        itens = D["transferencia"][uf]["incerteza_das_linhas_medidas"]
        assert itens
        for item in itens:
            baixo, alto = item["ic95_com_deff_pct"]
            assert baixo <= item["valor_pct"] <= alto
            assert item["ic95_pct"][0] >= baixo
            assert item["ic95_pct"][1] <= alto
            assert item["n_subamostra"] > 50
            assert item["deff"] > 1
            if (
                uf == "RJ"
                and item["origem"].startswith("Douglas Ruas")
                and item["destino"] == LULA
                and item["turno"] == "2º turno"
            ):
                ruas = item
    # A linha que o dono do projeto contestou: o zero fica fora do intervalo.
    assert ruas is not None
    assert ruas["valor_pct"] == 7
    assert ruas["zero_dentro_do_ic"] is False
    assert ruas["pontos_do_eleitorado_pp"] == pytest.approx(1.77, abs=0.01)


def test_a_conta_na_tela_reproduz_a_aritmetica_publicada():
    mg = D["transferencia"]["MG"]["conta_na_tela"]
    assert mg["natureza"] == "medida"
    assert mg["lula_no_estado_pct"] == 46
    assert mg["fora_da_direita_pp"] == 63
    assert mg["medido_pp"] == pytest.approx(28.73, abs=0.01)
    assert mg["exigencia_com_a_direita_pct"] == pytest.approx(44.28, abs=0.05)
    assert mg["exigencia_sem_a_direita_pct"] == pytest.approx(68.0, abs=0.05)
    sp = D["transferencia"]["SP"]["conta_na_tela"]
    assert sp["natureza"].startswith("piso medido")
    assert sp["lula_no_estado_pct"] == 42
    assert sp["fora_da_direita_pp"] == 51
    assert sp["estimativa_ancorada_na_direita_pp"] > sp["medido_na_direita_pp"]
    fracao = D["transferencia"]["MG"]["fracao_do_voto_de_lula_na_direita_estadual"]
    assert fracao["candidatura"].startswith("Cleitinho")
    assert fracao["pontos_pp"] > 10
    assert 20 < fracao["fracao_pct"] < 45


def test_sensibilidade_roda_prior_retencao_e_fidelidade():
    for uf in UFS:
        grade = D["transferencia"][uf]["gov2_pres2"]["sensibilidade"]
        assert len(grade) >= 15
        assert {g["retencao"] for g in grade} >= {0.93, 0.99}
        assert {g["fidelidade"] for g in grade} >= {0.93, 0.99}
        assert {g["prior"] for g in grade} == {"ideologica", "polarizada", "frouxa"}


def test_o_instituto_publica_cruzamento_entre_cargos():
    varredura = D["varredura_de_cruzamentos"]
    assert varredura["linhas_medidas"] >= 13
    paginas = {(c["uf"], c["pagina"]) for c in D["cruzamentos_publicados"]}
    assert ("SP", 4) in paginas
    assert ("RJ", 12) in paginas and ("RJ", 13) in paginas
    assert ("MG", 20) in paginas and ("MG", 21) in paginas


def test_vao_inverte_de_sinal_no_rio():
    assert ESTADOS["RJ"]["vao"]["turno2"]["vao_pp"] < 0
    assert ESTADOS["SP"]["vao"]["turno2"]["vao_pp"] > 0
    assert ESTADOS["MG"]["vao"]["turno2"]["vao_pp"] > 0
    for uf in UFS:
        assert ESTADOS[uf]["vao"]["turno2"]["rotulo"].startswith("teto endereçável")


def test_contraprova_marcada_no_achado():
    contraprovas = [a for a in D["achados"] if a.get("contraprova")]
    assert contraprovas, "o achado que contraria a tese precisa existir"
    assert any(a["id"] == "rj_sinal_invertido" for a in contraprovas)


def test_senado_nao_soma_alcance_como_se_fosse_voto_unico():
    for uf in UFS:
        senado = ESTADOS[uf]["senado"]
        assert senado["soma_alcance_pct"] > 60
        assert senado["soma_combinado_pct"] == pytest.approx(100, abs=2.0)
        assert senado["lider_alcance"]["valor"] >= senado["segunda_vaga"]["valor"]
        assert senado["melhor_da_direita"] is not None


def test_cobertura_do_sudeste_e_a_publicada():
    regional = D["regional_contra_estadual"]
    assert regional["cobertura_do_eleitorado_pct"] == pytest.approx(95.49, abs=0.01)
    assert regional["peso_es_no_sudeste_pct"] == pytest.approx(4.51, abs=0.01)
    assert regional["media_estadual"]["lula"] == pytest.approx(42.83, abs=0.01)
    assert regional["media_estadual"]["flavio"] == pytest.approx(46.89, abs=0.01)
    assert regional["recorte_nacional"]["lula"] == 42
    assert regional["recorte_nacional"]["flavio"] == 46
    assert regional["es_implicado"]["uso"] == "nao_publicavel_como_estimativa_do_es"


def test_o_contraste_regional_vem_com_intervalo():
    contraste = D["regional_contra_estadual"]["contraste"]
    baixo, alto = contraste["ic95"]
    assert baixo < contraste["diferenca_das_diferencas_pp"] < alto
    assert contraste["separa_com_95"] == (abs(baixo) > 0 and baixo * alto > 0)


def test_es_entra_separado_e_com_o_pareamento_conferido():
    es = D["espirito_santo"]
    assert es["ficha"]["instituto"] == "Real Time Big Data"
    assert es["conferencia_turno2"]["confere"] is True
    assert es["registros"]["estadual"] == "ES-01967/2026"
    assert "não entra em média" in es["aviso"].lower()
    assert es["presidente_turno2"]["valores"][FLAVIO] == 47
    assert es["presidente_turno2"]["valores"][LULA] == 42
    # O ES nao aparece em nenhuma media com o Datafolha.
    assert "ES" not in D["regional_contra_estadual"]["media_estadual"]["ufs"]


def test_ordem_de_grandeza_vem_rotulada_como_estimativa():
    for linha in D["ordem_de_grandeza"]:
        assert linha["rotulo"].startswith("estimativa de ordem de grandeza")
        assert linha["eleitorado_tse_2026"] > 0
        assert linha["votos_nominais_presidente_1t_2022"] > 0


def test_csv_resume_quatro_estados():
    with CSV_PATH.open(encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    assert [r["uf"] for r in linhas] == ["SP", "RJ", "MG", "ES"]
    assert {r["instituto"] for r in linhas} == {"Datafolha", "Real Time Big Data"}
    for linha in linhas:
        assert linha["presidente_2t_flavio"]
        assert linha["vao_2t_pp"]


def test_sem_travessao_em_nenhum_texto_publicado():
    # Escrito por codigo de ponto para que o proprio teste nao carregue o
    # caractere proibido e para que o formatador nao o reintroduza.
    travessao = chr(0x2014)
    alvos = [
        JSON_PATH,
        CSV_PATH,
        ROOT / "scripts/datafolha-21092026-sudeste.py",
        Path(__file__),
    ]
    for alvo in alvos:
        assert travessao not in alvo.read_text(encoding="utf-8"), alvo.name


def test_fonte_do_rio_registrada_com_hash_e_registro():
    fonte = D["fontes"]["datafolha_21092026_governador_rj.pdf"]
    assert len(fonte["sha256"]) == 64
    assert fonte["paginas"] == 53
    assert fonte["registros_tse"] == ["RJ-09217/2026", "BR-06361/2026"]
    assert (ROOT / fonte["caminho"]).exists()
