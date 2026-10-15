"""Um fragmento de carga com relógio adiantado não reinicia a votação real."""

import io
import zipfile

from apuracao_logs.cronologia import preparacao_anterior
from apuracao_logs.parser import analisar
from test_apuracao_logs import ciclo, pacote

NOME = "0202760101102026120000-01.jez/logd.dat"


def historico(computo=False):
    linhas = [
        "04/10/2026 08:00:15\tINFO\t02027601\tLOGD\tUrna ligada em 04/10/2026 às 08:00:14\tA",
        "04/10/2026 08:00:16\tINFO\t02027601\tSCUE\tData e hora que foi digitada pelo operador: 01/10/2026 - 08:00:00\tB",
        "01/10/2026 08:00:20\tINFO\t02027601\tSCUE\tCarga finalizada\tC",
    ]
    if computo:
        linhas.insert(
            1,
            "04/10/2026 08:00:15\tINFO\t02027601\tVOTA\tO voto do eleitor foi computado\tD",
        )
    return "\n".join(linhas)


def test_fragmento_exige_arquivo_fechado_antes_ajuste_e_termino_anterior():
    texto = historico()
    assert preparacao_anterior(NOME, texto)
    assert not preparacao_anterior("logd.dat", texto)
    assert not preparacao_anterior(NOME.replace("01102026", "04102026"), texto)
    assert not preparacao_anterior(
        NOME, texto.replace("01/10/2026 08:00:20", "04/10/2026 08:00:20")
    )
    assert not preparacao_anterior(
        NOME,
        texto.replace(
            "Data e hora que foi digitada pelo operador:", "Mensagem qualquer:"
        ),
    )
    assert not preparacao_anterior(NOME, historico(computo=True))


def test_partida_historica_nao_corta_ciclo_da_carga_atual():
    b = io.BytesIO()
    with (
        zipfile.ZipFile(b, "w") as z,
        zipfile.ZipFile(io.BytesIO(pacote(ciclo()))) as real,
    ):
        z.writestr(NOME, historico().encode("latin1"))
        z.writestr("logd.dat", real.read("logd.dat"))
    r = analisar(b.getvalue())
    assert r["ciclos"] == r["contagens"]["computados"] == 1
    assert r["contagens"].get("partidas_sistema", 0) == 0
    assert r["contagens"]["eventos_preparacao_excluidos"] == 2
    assert r["processo_observado"]["processo"]["n"] == 1
