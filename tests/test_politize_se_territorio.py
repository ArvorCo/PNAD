"""Junção territorial: escala municipal, procedência e ausências explícitas."""

import csv
import json
from pathlib import Path

import pytest
from politize_se import territorio

ROOT = Path(__file__).resolve().parents[1]
PUBLICO = ROOT / "docs/assets/politize_se_mapa"


def test_municipios_preserva_zero_nulo_e_codigo(tmp_path):
    p = tmp_path / "municipios.csv"
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["uf", "mun_tse", "homicidios_taxa_100mil", "homicidios_n"])
        w.writerows(
            [
                ["AC", "01007", "0", "0"],
                ["AC", "01015", "", ""],
                ["ZZ", "00001", "9", "3"],
            ]
        )
    m = territorio.municipios(p)
    assert m["AC-01007"]["homicidios_taxa_100mil"] == 0
    assert m["AC-01007"]["homicidios_n"] == 0
    assert m["AC-01015"]["homicidios_taxa_100mil"] is None
    assert "ZZ-00001" not in m
    assert territorio.numero("NaN") is None
    assert territorio.numero("inf") is None


def test_predio_novo_recebe_municipio_sem_imputar_renda():
    contexto = {"locais": {}, "municipios": {"01007": {"homicidios_taxa_100mil": 7.26}}}
    r = territorio.resumo_local("AC-01007-1-novo", contexto)
    assert r["renda_mediana_brl"] is None
    assert r["renda_ate2"] is None
    assert r["homicidios_taxa_100mil"] == 7.26
    assert all(
        v is None for v in territorio.resumo_local("ZZ-01007-1-novo", {}).values()
    )


def test_renda_publicada_reproduz_origem_sem_metricas_de_campanha():
    contexto = territorio.ler_uf("AC", territorio.municipios())
    src = json.loads((territorio.POLITIZE / "mun/AC/01392.json").read_text())["locais"]
    for linha in src["linhas"]:
        r = dict(zip(src["colunas"], linha, strict=True))
        local = contexto["locais"][r["local_id"]]
        for c in (
            "renda_mediana_brl",
            "renda_ate2",
            "renda_de2a5",
            "renda_mais5",
            "superior",
        ):
            assert local[c] == r[c]
        assert "potencial" not in local and "esperado_flavio_v" not in local
    assert territorio.ler_uf("ZZ", territorio.municipios()) == {
        "locais": {},
        "municipios": {},
    }


def test_arquivos_do_mapa_e_detalhe_concordam_no_pais():
    municipios = territorio.municipios()
    for p in sorted((PUBLICO / "uf").glob("*.json")):
        d = json.loads(p.read_text())
        contexto = json.loads((PUBLICO / "contexto" / p.name).read_text())
        loc = contexto["locais"]
        por_id = {
            r[0]: dict(zip(loc["colunas"], r, strict=True)) for r in loc["linhas"]
        }
        for linha in d["locais"]["linhas"]:
            r = dict(zip(d["locais"]["colunas"], linha, strict=True))
            original = por_id.get(r["id"], {})
            for campo in ("renda_mediana_brl", "renda_ate2"):
                assert r[campo] == original.get(campo)
            mun = "-".join(r["id"].split("-")[:2])
            municipal = contexto["municipios"].get(r["id"].split("-")[1], {})
            assert r["homicidios_taxa_100mil"] == municipal.get(
                "homicidios_taxa_100mil"
            )
            if territorio.MUNICIPIOS.exists():
                assert r["homicidios_taxa_100mil"] == municipios.get(mun, {}).get(
                    "homicidios_taxa_100mil"
                )
            if original.get("renda_ate2") is not None:
                assert sum(
                    original[k] for k in ("renda_ate2", "renda_de2a5", "renda_mais5")
                ) == pytest.approx(100, abs=0.2)


def test_camadas_territoriais_independem_do_boletim_e_municipio_nao_duplica():
    assert all(not c["precisa_bu2"] for c in territorio.CAMADAS.values())
    assert territorio.CAMADAS["homicidios"]["agregacao"] == "municipios"
    assert all(
        c["campo"] in territorio.CAMPOS_MAPA for c in territorio.CAMADAS.values()
    )
