"""Testes do preparo TSE do Senado 2026: sem rede e sem os zips reais."""

import io

from PIL import Image
from senado_2026 import tse

CABECALHO = (
    "SG_UF;CD_CARGO;SQ_CANDIDATO;NR_CANDIDATO;NM_CANDIDATO;NM_URNA_CANDIDATO;"
    "SG_PARTIDO;NM_FEDERACAO;NM_COLIGACAO;DS_COMPOSICAO_COLIGACAO;DS_GENERO;"
    "DS_OCUPACAO;DS_SITUACAO_CANDIDATURA;DS_SIT_TOT_TURNO"
)


def campo(partido):
    return {"PL": "direita", "PT": "esquerda"}.get(partido or "", "indefinido")


def csv_candidatos() -> io.BytesIO:
    linhas = [
        CABECALHO,
        "AC;5;111;222;MÁRCIO MIGUEL BITTAR;MARCIO BITTAR;PL;#NULO;AVANÇA;PDT / PL;"
        "MASCULINO;SENADOR;#NE;#NULO",
        "AC;5;112;133;JOÃO DA SILVA;JOÃO (PT);PT;FEDERAÇÃO X;#NULO;#NULO;"
        "MASCULINO;MÉDICO;APTO;#NULO",
        "AC;6;113;1234;DEPUTADO FEDERAL;DEP;PL;#NULO;#NULO;#NULO;MASCULINO;X;APTO;#NULO",
    ]
    return io.BytesIO("\n".join(linhas).encode("latin-1"))


def test_normalizar_tira_acento_parenteses_e_caixa():
    assert tse.normalizar("  João  da Silva (PT) ") == "joao da silva"
    assert tse.normalizar("Márcio Bittar") == tse.normalizar("MARCIO BITTAR")
    assert tse.normalizar(None) == ""


def test_leitura_do_csv_em_latin1_filtra_cargo_e_nulos():
    linhas = list(tse.ler_csv(csv_candidatos()))
    regs = [tse.linha_candidato(r, campo) for r in linhas if r["CD_CARGO"] == "5"]
    assert [r["nome_urna"] for r in regs] == ["MARCIO BITTAR", "JOÃO (PT)"]
    assert regs[0]["nome_completo"] == "MÁRCIO MIGUEL BITTAR"
    assert regs[0]["situacao_candidatura"] is None
    assert regs[0]["federacao"] is None
    assert regs[0]["campo"] == "direita"
    assert regs[1]["federacao"] == "FEDERAÇÃO X"
    assert regs[1]["situacao_candidatura"] == "APTO"
    assert regs[1]["foto"] is None


def cands():
    regs = [r for r in tse.ler_csv(csv_candidatos()) if r["CD_CARGO"] == "5"]
    return [tse.linha_candidato(r, campo) for r in regs]


def test_casamento_por_nome_de_urna_e_completo_sem_adivinhar():
    casados, perdidos = tse.casar_nomes(
        cands(),
        [
            ("AC", "Márcio Bittar (PL)"),
            ("AC", "João da Silva"),
            ("AC", "Fulano"),
            ("SP", "Marcio Bittar"),
            ("AC", "Márcio Bittar (PL)"),
        ],
    )
    assert [c["sq_candidato"] for c in casados] == ["111", "112"]
    assert {p["nome_pesquisa"]: p["motivo"] for p in perdidos} == {
        "Fulano": "sem_candidatura_no_tse",
        "Marcio Bittar": "sem_candidatura_no_tse",
    }


def test_casamento_com_apelido_declarado(monkeypatch):
    monkeypatch.setitem(tse.APELIDOS, ("AC", "bittar"), "marcio bittar")
    casados, perdidos = tse.casar_nomes(cands(), [("AC", "Bittar")])
    assert not perdidos
    assert casados[0]["sq_candidato"] == "111"
    assert casados[0]["via_apelido"] is True


def test_casamento_ambiguo_nao_casa():
    dois = [*cands(), {**cands()[0], "sq_candidato": "999"}]
    casados, perdidos = tse.casar_nomes(dois, [("AC", "Marcio Bittar")])
    assert not casados
    assert perdidos[0]["motivo"] == "ambiguo"


def linha_2022(sq, nome, partido, votos, sit, cargo="5", uf="AC"):
    return {
        "CD_CARGO": cargo,
        "SQ_CANDIDATO": sq,
        "SG_UF": uf,
        "NM_URNA_CANDIDATO": nome,
        "NM_CANDIDATO": nome.title(),
        "SG_PARTIDO": partido,
        "QT_VOTOS_NOMINAIS": str(votos),
        "DS_SIT_TOT_TURNO": sit,
    }


def test_eleito_de_2022_soma_zonas_e_ignora_outros_cargos():
    linhas = [
        linha_2022("1", "ALAN", "PL", 100, "ELEITO"),
        linha_2022("1", "ALAN", "PL", 50, "ELEITO"),
        linha_2022("2", "BETO", "PT", 120, "NÃO ELEITO"),
        linha_2022("3", "GOV", "PL", 9999, "ELEITO", cargo="3"),
        linha_2022("4", "CLEI", "PT", 70, "ELEITO POR MÉDIA", uf="MG"),
    ]
    eleitos = tse.eleitos_2022(linhas, campo)
    assert [(e["uf"], e["nome"], e["votos"]) for e in eleitos] == [
        ("AC", "ALAN", 150),
        ("MG", "CLEI", 70),
    ]
    assert eleitos[0]["campo"] == "direita"


def test_sq_do_arquivo_aceita_as_duas_variantes():
    assert tse.sq_do_arquivo("FAC10002544107_div.jpg") == "10002544107"
    assert tse.sq_do_arquivo("F10002544107_div.jpg") == "10002544107"
    assert tse.sq_do_arquivo("leiame.txt") is None


def test_recorte_quadrado_240():
    img = Image.new("RGB", (300, 400), "red")
    out = tse.recorte_quadrado(img)
    assert out.size == (240, 240)
