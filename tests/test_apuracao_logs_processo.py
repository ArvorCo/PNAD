"""Limites do processo observado: ambiguidade, reinício, janela e inatividade."""

from apuracao_logs.parser import analisar
from test_apuracao_logs import ciclo, pacote


def test_processo_comeca_na_digitacao_concluida_nao_na_tela_de_espera():
    r = analisar(
        pacote(
            [("07:30:00", "Aguardando digitação do identificador do eleitor"), *ciclo()]
        )
    )
    p = r["processo_observado"]
    assert p["processo"]["media"] == 21
    assert p["por_tipo"]["biometrica"]["n"] == 1
    assert p["cadencia"]["n"] == 0


def test_identificadores_repetidos_nao_sao_assumidos_como_mesma_pessoa():
    r = analisar(
        pacote(
            [("07:59:50", "Identificador do eleitor digitado pelo mesário"), *ciclo()]
        )
    )
    assert r["ciclos"] == 1
    assert r["processo_observado"]["processo"]["n"] == 0
    assert r["processo_observado"]["excluidos_identificacao"] == 1


def test_janela_exige_onze_computos_contiguos_e_nao_atravessa_reinicio():
    ev = []
    for minuto in range(11):
        ev.extend((t.replace("08:00:", f"08:{minuto:02d}:"), m) for t, m in ciclo())
    r = analisar(pacote(ev))
    assert r["processo_observado"]["cadencia"]["media"] == 60
    assert r["processo_observado"]["rajada10_s"] == 60
    assert r["processo_observado"]["janelas10"] == 1
    ev.insert(25, ("08:04:50", "Iniciando aplicação VOTA"))
    r = analisar(pacote(ev))
    assert r["processo_observado"]["cadencia"]["n"] == 9
    assert r["processo_observado"]["rajada10_s"] is None


def test_inspecao_e_retomada_nao_sao_erros_nem_reinicios():
    r = analisar(
        pacote(
            [
                *ciclo(),
                ("09:09:26", "Inspeção da urna iniciada"),
                ("09:09:41", "Inspeção da urna confirmada"),
                ("09:09:45", "Inspeção da urna terminada"),
                ("10:13:23", "Eleitor sem atividade por 45 segundos"),
                ("10:13:43", "Eleitor voltou a digitar enquanto estava sendo suspenso"),
            ]
        )
    )
    assert r["inspecoes"]["max"] == 19
    assert r["contagens"]["retomadas_inatividade"] == 1
    assert r["contagens"].get("erros", 0) == 0
    assert r["contagens"]["reinicios_durante_votacao"] == 0


def test_cancelamento_nao_vira_processo_com_inicio_inequivoco():
    ev = ciclo()
    ev.insert(
        1, ("08:00:05", "Habilitação cancelada durante a captura de digital do mesário")
    )
    r = analisar(pacote(ev))
    assert r["ciclos"] == 1
    assert r["processo_observado"]["processo"]["n"] == 0


def test_relogio_invalido_elimina_processo_e_janelas():
    r = analisar(pacote([*ciclo(), ("07:59:00", "Ajuste de relógio confirmado")]))
    assert r["processo_observado"]["processo"]["n"] == 0
    assert r["processo_observado"]["rajada10_s"] is None


def test_partida_do_sistema_sem_nova_partida_vota_quebra_cadencia():
    import io
    import zipfile

    ev = [*ciclo(), ("08:01:00", "Urna ligada em 04/10/2026 às 08:00:55")]
    ev += [(t.replace("08:00:", "08:02:"), m) for t, m in ciclo()]
    raw = pacote(ev)
    buf = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(raw)) as src, zipfile.ZipFile(buf, "w") as dst:
        txt = src.read("logd.dat").replace(b"VOTA\tUrna ligada", b"LOGD\tUrna ligada")
        dst.writestr("logd.dat", txt)
    r = analisar(buf.getvalue())
    assert r["contagens"]["reinicios_sistema_em_votacao"] == 1
    assert r["contagens"]["reinicios_durante_votacao"] == 0
    assert r["processo_observado"]["cadencia"]["n"] == 0
    assert r["processo_observado"]["processo"]["n"] == 2


def test_computo_nao_reconstruido_nao_pode_ser_pulado_na_cadencia():
    ev = [*ciclo(), ("08:01:00", "O voto do eleitor foi computado")]
    ev += [(t.replace("08:00:", "08:02:"), m) for t, m in ciclo()]
    r = analisar(pacote(ev))
    assert r["processo_observado"]["cadencia"]["n"] == 0
