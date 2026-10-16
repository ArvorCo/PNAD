"""Contratos independentes: ZIP, ciclo, biometria, relógio e contagem do BU."""

import io
import zipfile
from pathlib import Path

import asn1tools
import pytest
from apuracao_logs.complementos import SPEC, ler_bu
from apuracao_logs.parser import analisar
from apuracao_logs.processamento import reconciliar

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "apuracao/tests/fixtures/bu/o03220sp7107200010001-log.jez"


def test_bu_suplementar_reproduz_campos_do_boletim_real():
    leitor = asn1tools.compile_files(str(SPEC), codec="ber", numeric_enums=True)
    raw = FIXTURE.with_name("o03220sp7107200010001-bu.dat").read_bytes()
    r = ler_bu(raw, ("sp", "71072", 1, 1), leitor)
    assert (
        r["comparecimento"],
        r["hab_biometria"],
        r["hab_ano_nascimento"],
        r["comp_sem_biometria"],
    ) == (256, 212, 37, 7)
    with pytest.raises(AssertionError):
        ler_bu(raw, ("sp", "71072", 1, 2), leitor)


def pacote(eventos):
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        linhas = [
            f"04/10/2026 {t}\tINFO\t02027601\tVOTA\t{m}\t{i:016X}"
            for i, (t, m) in enumerate(eventos)
        ]
        z.writestr("logd.dat", "\n".join(linhas).encode("latin1"))
    return b.getvalue()


def ciclo():
    return [
        ("08:00:00", "Identificador do eleitor digitado pelo mesário"),
        ("08:00:10", "Tipo de habilitação do eleitor [biométrica]"),
        ("08:00:10", "Eleitor foi habilitado"),
        ("08:00:20", "Voto confirmado para [Presidente]"),
        ("08:00:21", "O voto do eleitor foi computado"),
    ]


def test_real_reconcilia_tres_categorias_e_suspensao():
    r = analisar(
        FIXTURE.read_bytes(),
        {"mun": "71072", "zona": 1, "secao": 1, "numero_interno_urna": 2027601},
    )
    r = reconciliar(
        r,
        {
            "comparecimento": 256,
            "hab_biometria": 212,
            "hab_ano_nascimento": 37,
            "comp_sem_biometria": 7,
            "fase": 2,
            "pleito": 3220,
        },
    )
    assert r["contagem_confere"] and r["biometria_confere"] and r["elegivel_tempo"]
    assert r["contagens"]["habilitacoes"] == 257  # uma suspensão sem voto
    assert r["contagens"]["suspensoes_parciais"] == 2
    assert r["tempo_voto"]["n"] == 254  # ciclos parciais fora do tempo de voto completo
    assert r["tempo_voto"]["p50"] == 54
    assert r["tempo_habilitacao"]["p50"] == 21


def test_separa_identificacao_cabine_e_nao_inventa_preferencia():
    r = analisar(pacote(ciclo()))
    assert r["tempo_voto"]["media"] == 11
    assert r["tempo_habilitacao"]["media"] == 10
    assert r["tempo_por_cargos"]["1"]["n"] == 1
    assert r["tipos_habilitacao_computados"] == {"biometrica": 1}


def test_clock_reversal_invalidates_time_even_if_sorting_repairs_order():
    ev = ciclo()
    ev[3] = ("07:59:59", ev[3][1])
    r = analisar(pacote(ev))
    assert r["contagens"]["recuos_relogio"] == 1
    assert not r["tempos_validos"] and r["tempo_voto"]["media"] is None


def test_computo_sem_habilitacao_nao_vira_ciclo():
    r = analisar(pacote(ciclo()[-2:]))
    assert r["contagens"]["computados_sem_habilitacao"] == 1
    assert r["tempo_voto"]["n"] == 0


def test_ajuste_antes_da_votacao_nao_interrompe_ciclo_posterior():
    # O relógio estava adiantado antes do início. Ordenar pelos carimbos
    # colocaria a partida das 08:00:15 entre habilitação e cômputo do ciclo.
    ev = [
        ("08:00:15", "Iniciando aplicação - 1º turno"),
        ("07:30:00", "Ajuste de relógio confirmado"),
        *ciclo(),
    ]
    r = analisar(pacote(ev))
    assert r["ciclos"] == r["contagens"]["computados"] == 1
    assert r["contagens"].get("computados_sem_habilitacao", 0) == 0
    assert not r["tempos_validos"]


def test_nested_archive_deduplicates_overlap():
    first = pacote(ciclo())
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("anterior.jez", first)
        z.writestr("atual.jez", first)
    r = analisar(b.getvalue())
    assert r["contagens"]["computados"] == 1
    assert r["contagens"]["linhas_duplicadas"] == 5


def test_non_official_or_foreign_section_excluded():
    ev = [("07:00:00", "Fase da UE: Simulado"), *ciclo()]
    r = analisar(pacote(ev))
    assert r["urnas"] == 0 and r["ciclos"] == 0
    ev = [("07:00:00", "Município: 99999"), *ciclo()]
    r = analisar(pacote(ev), {"mun": "71072", "numero_interno_urna": 2027601})
    assert r["urnas"] == 0


def test_bad_zip_is_not_zero_events():
    with pytest.raises(zipfile.BadZipFile):
        analisar(b"not a zip")


def test_cancelamento_que_cruza_com_captura_nao_apaga_tipo_validado():
    ev = [
        ("08:00:00", "Identificador do eleitor digitado pelo mesário"),
        ("08:00:10", "Solicitação de dado pessoal do eleitor para habilitação manual"),
        ("08:00:12", "Dado digitado confere"),
        ("08:00:15", "Habilitação cancelada durante a captura de digital do mesário"),
        ("08:00:16", "Eleitor foi habilitado"),
        *ciclo()[3:],
    ]
    r = analisar(pacote(ev))
    assert r["tipos_habilitacao_computados"] == {"biografica": 1}


def test_encerrar_uma_urna_nao_oculta_reinicio_de_outra():
    a = pacote([*ciclo(), ("08:01:00", "Procedimento de encerramento confirmado")])
    b = pacote(
        [(t.replace("08:", "09:"), m) for t, m in ciclo()]
        + [
            ("09:02:00", "Iniciando aplicação VOTA"),
        ]
    )
    unido = io.BytesIO()
    with zipfile.ZipFile(unido, "w") as out:
        for nome, raw, serial in (("a.dat", a, b"02027601"), ("b.dat", b, b"02027602")):
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                out.writestr(nome, z.read("logd.dat").replace(b"02027601", serial))
    r = analisar(unido.getvalue())
    assert r["urnas"] == 2
    assert r["contagens"]["reinicios_durante_votacao"] == 1


def test_erro_assinatura_com_sucesso_posterior_no_mesmo_arquivo():
    prefixo = "Verificação de assinatura - Etapa [26] - [/arquivo.vsc] - "
    r = analisar(
        pacote(
            [
                ("07:00:00", prefixo + "[ERRO]"),
                ("07:05:00", prefixo + "[SUCESSO]"),
                *ciclo(),
                ("09:00:00", prefixo + "[ERRO]"),
            ]
        )
    )
    c = r["contagens"]
    assert c["falhas_assinatura_declaradas"] == 2
    assert c["falhas_assinatura_com_sucesso_posterior"] == 1
    assert c["falhas_assinatura_sem_sucesso_localizado"] == 1


def test_sucesso_de_outro_arquivo_nao_resolve_falha():
    r = analisar(
        pacote(
            [
                (
                    "07:00:00",
                    "Verificação de assinatura - Etapa [26] - [/a.vsc] - [ERRO]",
                ),
                (
                    "07:05:00",
                    "Verificação de assinatura - Etapa [26] - [/b.vsc] - [SUCESSO]",
                ),
            ]
        )
    )
    assert r["contagens"]["falhas_assinatura_com_sucesso_posterior"] == 0


def test_urna_ligada_desde_vespera_preserva_identidade_da_carga():
    raw = pacote(
        [
            ("07:00:00", "Fase da UE: Oficial"),
            ("07:00:01", "Município: 71072"),
            ("07:00:02", "Zona Eleitoral: 0001"),
            ("07:00:03", "Seção Eleitoral: 0001"),
            *ciclo(),
        ]
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(raw)) as zin, zipfile.ZipFile(buf, "w") as zout:
        txt = zin.read("logd.dat").replace(b"04/10/2026 07:", b"03/10/2026 07:")
        zout.writestr("logd.dat", txt)
    r = analisar(
        buf.getvalue(),
        {"mun": "71072", "zona": 1, "secao": 1, "numero_interno_urna": 999},
    )
    assert r["contagens"]["computados"] == 1 and r["urnas"] == 1


def test_texto_alterado_e_sinalizado_sem_corrigir_evento():
    ev = [(t, m.replace("foi habilitado", "foi ha`ilitado")) for t, m in ciclo()]
    r = analisar(pacote(ev))
    assert r["contagens"]["mensagens_criticas_alteradas"] == 1
    assert r["contagens"]["computados_sem_habilitacao"] == 1
    assert r["ciclos"] == 0


def test_bateria_classifica_fase_pela_zeresima_e_pelos_computos():
    ev = [
        ("07:30:00", "Urna operando na bateria interna"),
        ("07:40:00", "Gerando relatório [ZERÉSIMA] [TÉRMINO]"),
        ("07:50:00", "Urna operando na bateria interna"),
        *ciclo(),
        ("08:00:21", "Urna operando na bateria interna"),
        ("09:00:00", "Urna operando na bateria interna"),
        ("09:00:00", "Carga da [ALIMENTAÇÃO BATERIA INTERNA]: [PLENA]"),
    ]
    r = analisar(pacote(ev))
    assert r["contagens"]["eventos_bateria"] == 4
    assert r["bateria_fases"] == {
        "pre_zeresima": 1,
        "pre_votacao": 1,
        "votacao": 1,
        "pos_votacao": 1,
    }
    assert r["bateria_votacao_segundos"] == [8 * 3600 + 21]
    sem = analisar(pacote([("07:30:00", "Urna operando na bateria interna")]))
    assert sem["bateria_fases"] == {"pre_votacao": 1}
    assert sem["bateria_votacao_segundos"] == []
