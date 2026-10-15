"""Conferencia do BU lido do QR com o BU publicado pelo TSE (decodificacao ASN.1 e comparacao)."""

import copy
import importlib.util
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "totalizacao_conferir", RAIZ / "scripts" / "totalizacao-conferir-tse.py"
)
conferir = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(conferir)

FIXTURE = (
    RAIZ / "apuracao" / "tests" / "fixtures" / "bu" / "o03220sp7107200010001-bu.dat"
)


@pytest.fixture(scope="module")
def tse():
    return conferir.tse_comparavel(conferir.decodificar(FIXTURE.read_bytes()))


def _qr_de(tse: dict) -> dict:
    """Monta as linhas publicas do banco a partir do BU do TSE, como se o QR tivesse sido lido."""
    bu = {"comparecimento": tse["comparecimento"]}
    cargos, votos = [], []
    for idel, e in tse["eleicoes"].items():
        for cargo, c in e["cargos"].items():
            nomi = sum(c["nominais"].values())
            legc = sum(c["legenda"].values())
            cargos.append(
                {
                    "idel": idel,
                    "cargo": cargo,
                    "apta": e["aptos"],
                    "nomi": nomi,
                    "legc": legc,
                    "bran": c["branco"],
                    "nulo": c["nulo"],
                    "totc": c["comparecimento"],
                }
            )
            votos += [
                {"idel": idel, "cargo": cargo, "candidato": n, "votos": v}
                for n, v in c["nominais"].items()
            ]
            votos += [
                {"idel": idel, "cargo": cargo, "candidato": f"LEGP{p}", "votos": v}
                for p, v in c["legenda"].items()
            ]
    return conferir.qr_comparavel(bu, cargos, votos)


def test_fixture_decodifica_com_presidente_e_cargos_estaduais(tse):
    assert 6257 in tse["eleicoes"] and 6259 in tse["eleicoes"]
    presidente = tse["eleicoes"][6257]["cargos"][1]
    assert presidente["nominais"]["13"] > 0 and presidente["nominais"]["22"] > 0
    assert tse["comparecimento"] > 0
    assert any(c["legenda"] for c in tse["eleicoes"][6259]["cargos"].values())


def test_qr_identico_ao_tse_nao_tem_diferenca(tse):
    assert conferir.comparar(_qr_de(tse), tse) == []


def test_um_voto_a_mais_vira_divergencia_nominal(tse):
    qr = _qr_de(tse)
    qr["eleicoes"][6257]["cargos"][1]["nominais"]["22"] += 1
    dif = conferir.comparar(qr, tse)
    assert [d["campo"] for d in dif] == ["nominal"]
    assert dif[0]["chave"] == "22" and dif[0]["qr"] == dif[0]["tse"] + 1


def test_cargo_ausente_e_legenda_diferente(tse):
    qr = _qr_de(tse)
    del qr["eleicoes"][6259]["cargos"][5]
    cargo_prop = next(
        c for c in qr["eleicoes"][6259]["cargos"].values() if c["legenda"]
    )
    partido = next(iter(cargo_prop["legenda"]))
    cargo_prop["legenda"][partido] = 0
    campos = {d["campo"] for d in conferir.comparar(qr, tse)}
    assert campos == {"cargo_ausente", "legenda"}


def test_escolher_arquivo_prefere_mais_recente_e_busa():
    aux = {
        "hashes": [
            {
                "hash": "a",
                "dr": "25/10/2026",
                "hr": "18:00:00",
                "arq": [{"nm": "x-bu.dat", "tp": "bu"}],
            },
            {
                "hash": "b",
                "dr": "25/10/2026",
                "hr": "19:00:00",
                "arq": [
                    {"nm": "x-bu.dat", "tp": "bu"},
                    {"nm": "x-busa.dat", "tp": "busa"},
                ],
            },
            {
                "hash": "c",
                "dr": "25/10/2026",
                "hr": "20:00:00",
                "arq": [{"nm": "x-rdv.dat", "tp": "rdv"}],
            },
        ]
    }
    esc = conferir.escolher_arquivo(aux)
    assert (
        esc["hash"] == "b"
        and esc["arquivo"] == "x-busa.dat"
        and esc["recebido"] == "25/10/2026 19:00:00"
    )
    assert conferir.escolher_arquivo({"hashes": []}) is None


def test_url_aux_segue_o_padrao_do_tse():
    assert conferir.url_aux("ac", 1392, 9, 13, 3221) == (
        "https://resultados.tse.jus.br/oficial/ele2026/arquivo-urna/3221/dados/ac/01392/0009/0013/p003221-ac-m01392-z0009-s0013-aux.json"
    )


def test_bu_fora_da_fase_oficial_nao_consulta_o_tse():
    bu = {
        "id": 1,
        "uf": "ac",
        "muni": 1392,
        "zona": 9,
        "secao": 13,
        "hash_final": "A" * 128,
        "fase": "S",
        "pleito": 3221,
    }
    r = conferir.conferir_secao(bu, [], [])
    assert r["situacao"] == "fora_do_oficial" and r["diferencas"] == []


def test_resumo_conta_cada_situacao():
    secoes = [
        {"situacao": s, "diferencas": []}
        for s in [
            "igual",
            "igual",
            "divergente",
            "tse_ainda_nao_publicou",
            "erro",
            "fora_do_oficial",
        ]
    ]
    r = conferir.resumir(copy.deepcopy(secoes))
    assert r == {
        "aceitos": 6,
        "iguais": 2,
        "divergentes": 1,
        "nao_publicados": 1,
        "erros": 1,
        "fora_do_oficial": 1,
        "conferidos": 3,
    }
