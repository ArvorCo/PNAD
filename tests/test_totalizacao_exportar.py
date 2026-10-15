"""Conferencia da cadeia de hashes exportada pela totalizacao paralela."""

import hashlib
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "totalizacao_exportar",
    Path(__file__).resolve().parents[1] / "scripts" / "totalizacao-exportar.py",
)
exportar = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(exportar)


def _cadeia(n: int) -> list[dict]:
    anterior = ""
    linhas = []
    for i in range(1, n + 1):
        h = f"{i:0128X}"
        a = f"{i * 7:0264X}"
        cadeia = hashlib.sha256((anterior + h + a).encode()).hexdigest()
        linhas.append(
            {
                "id": i,
                "hash_final": h,
                "assi": a,
                "cadeia_anterior": anterior or None,
                "cadeia": cadeia,
            }
        )
        anterior = cadeia
    return linhas


def test_cadeia_integra_e_ordem_independente():
    linhas = _cadeia(5)
    resultado = exportar.conferir_cadeia(list(reversed(linhas)))
    assert resultado == {
        "bus": 5,
        "cadeia_integra": True,
        "quebras": [],
        "ultimo_elo": linhas[-1]["cadeia"],
    }


def test_cadeia_vazia():
    assert exportar.conferir_cadeia([]) == {
        "bus": 0,
        "cadeia_integra": True,
        "quebras": [],
        "ultimo_elo": None,
    }


def test_alteracao_no_meio_quebra_a_cadeia_dali_em_diante():
    linhas = _cadeia(4)
    linhas[1]["assi"] = linhas[1]["assi"][:-2] + "FF"
    resultado = exportar.conferir_cadeia(linhas)
    assert resultado["cadeia_integra"] is False
    assert resultado["quebras"] == [2]
