import importlib.util
import sys
from pathlib import Path

import pytest


SCRIPT = Path(__file__).parents[1] / "scripts/quaest-territory-audit.py"
SPEC = importlib.util.spec_from_file_location("quaest_territory_audit", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_parse_rows_extracts_sector_and_geography():
    text = "\n".join(
        [
            "Quaest | BR-07181/2026",
            "São Paulo (SP) Barra Funda 355030806000001 6",
            "Brasília (DF) Planaltina 530010805110066 6",
        ]
    )
    rows = MODULE.parse_rows(text, "julho/2026", "BR-07181/2026")

    assert len(rows) == 2
    assert rows[0].municipality_code == "3550308"
    assert rows[0].region == "Sudeste"
    assert rows[1].region == "Centro-Oeste"


def test_parse_rows_rejects_uf_code_mismatch():
    with pytest.raises(ValueError, match="UF incompatible"):
        MODULE.parse_rows(
            "São Paulo (RJ) Barra Funda 355030806000001 6",
            "julho/2026",
            "BR-07181/2026",
        )


def test_comparison_separates_neighborhood_from_exact_sector():
    june = MODULE.parse_rows(
        "São Paulo (SP) Jaragua 355030842000610 6\n"
        "Araraquara (SP) Jardim Arco Iris 350320805000099 6",
        "junho/2026",
        "BR-07661/2026",
    )
    july = MODULE.parse_rows(
        "São Paulo (SP) Jaragua 355030842000191 6\n"
        "Araraquara (SP) Jardim Arco Iris 350320805000099 6",
        "julho/2026",
        "BR-07181/2026",
    )

    comparison = MODULE.compare_rounds(june, july)

    assert comparison["common_municipalities"] == 2
    assert comparison["common_municipality_neighborhoods"] == 2
    assert comparison["common_exact_sectors"] == 1
    assert comparison["same_neighborhood_but_different_sector"] == 1


def test_mesh_codes_reads_topojson_properties():
    payload = {
        "objects": {
            "MU3550308ST": {
                "geometries": [
                    {"properties": {"codarea": "355030806000001"}},
                    {"properties": {"codarea": "355030806000002"}},
                ]
            }
        }
    }

    assert MODULE.mesh_codes(payload) == {
        "355030806000001",
        "355030806000002",
    }
