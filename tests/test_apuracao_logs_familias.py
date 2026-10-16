"""Famílias dos diagnósticos dos logs e nível de atenção do mapa de fiscais."""

from apuracao_logs.criterios import CRITERIOS
from apuracao_logs.familias import (
    FAMILIA_DE,
    FAMILIAS,
    NOME_CURTO,
    atencao,
    catalogo,
    familias_de,
)

TRAVESSAO = "\u2014"


def test_toda_regra_tem_familia_e_nome_curto():
    assert set(FAMILIA_DE) == set(CRITERIOS)
    assert set(NOME_CURTO) == set(CRITERIOS)
    todos = [c for f in FAMILIAS.values() for c in f["criterios"]]
    assert len(todos) == len(set(todos))
    txt = str(FAMILIAS) + str(NOME_CURTO)
    assert TRAVESSAO not in txt and "fraude" not in txt.lower()


def test_atencao_e_ordenacao_declarada():
    assert atencao([]) == 0
    assert atencao(["bateria"]) == 0
    assert atencao(["bateria", "bateria_votacao_local"]) == 1
    assert atencao(["bateria", "bateria_votacao_isolada", "suspensoes"]) == 2
    assert atencao(["bateria", "inspecao_prolongada"]) == 0
    assert atencao(["reinicios"]) == 1
    assert atencao(["reinicios", "reinicio_sistema", "bateria"]) == 1
    assert atencao(["reinicios", "sem_biometria_alta"]) == 2
    assert atencao(["bateria", "suspensoes"]) == 1
    assert atencao(["reinicios", "sem_biometria_alta", "tempo_lento"]) == 3
    assert atencao(["contagem_divergente"]) == 3
    # Ciclo não reconstruído acompanha o reinício: mesma família, um só nível.
    assert atencao(["ciclos_incompletos"]) == 1
    assert atencao(["ciclos_incompletos", "reinicios"]) == 1
    assert atencao(["retomadas_inatividade", "tempo_lento"]) == 1
    assert atencao(["inspecao_prolongada", "intervalo_longo"]) == 1
    assert atencao(["desconhecido"]) == 0


def test_familias_de_segue_a_ordem_declarada():
    assert familias_de(["suspensoes", "bateria"]) == ["energia", "ritmo"]
    assert familias_de(["intervalo_longo"]) == ["paradas"]
    assert familias_de([]) == []


def test_catalogo_so_lista_criterios_publicados():
    cat = catalogo({"bateria": {}, "reinicios": {}})
    assert cat["energia"]["criterios"] == ["bateria", "reinicios"]
    assert cat["arquivo"]["criterios"] == []
    assert set(cat) == set(FAMILIAS)
