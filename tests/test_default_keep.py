import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from pnadc_cli import DEFAULT_KEEP, DEFAULT_KEEP_ANUAL  # type: ignore


def test_default_keep_has_no_duplicates():
    cols = [c.strip() for c in DEFAULT_KEEP.split(",") if c.strip()]
    assert len(cols) == len(set(cols))


def test_default_keep_includes_new_modeling_fields():
    cols = {c.strip() for c in DEFAULT_KEEP.split(",") if c.strip()}
    expected = {
        "Estrato",
        "V1022",
        "V1023",
        "V2001",
        "V2003",
        "V3002",
        "VD3006",
        "VD4001",
        "VD4002",
        "VD4010",
        "VD4012",
        "VD4013",
        "V4012",
        "V4013",
        "V4020",
        "V4025",
        "V4029",
        "V4032",
        "V4033",
        "V403312",
        "V40333",
        "V403331",
        "V4034",
        "V403412",
        "V403422",
        "V4039",
        "V4039C",
        "V4040",
        "V4056",
        "V405921",
        "V405922",
    }
    missing = sorted(expected - cols)
    assert not missing


def test_default_keep_includes_replicate_weights():
    cols = {c.strip() for c in DEFAULT_KEEP.split(",") if c.strip()}
    reps = sorted(c for c in cols if c.startswith("V1028") and len(c) == 8 and c[5:].isdigit())
    assert len(reps) == 200
    assert reps[0] == "V1028001"
    assert reps[-1] == "V1028200"


def test_default_keep_anual_has_no_duplicates():
    cols = [c.strip() for c in DEFAULT_KEEP_ANUAL.split(",") if c.strip()]
    assert len(cols) == len(set(cols))


def test_default_keep_anual_includes_renda_total_variables():
    cols = {c.strip() for c in DEFAULT_KEEP_ANUAL.split(",") if c.strip()}
    expected = {
        "V5001A",
        "V5001A2",
        "V5002A",
        "V5002A2",
        "V5003A",
        "V5003A2",
        "V5004A",
        "V5004A2",
        "V5005A",
        "V5005A2",
        "V5006A",
        "V5006A2",
        "V5007A",
        "V5007A2",
        "V5008A",
        "V5008A2",
        "VD5001",
        "VD5002",
        "VD5003",
        "VD5004",
        "VD5005",
        "VD5006",
        "VD5007",
        "VD5008",
        "VD5009",
        "VD5010",
        "VD5011",
        "VD5012",
    }
    missing = sorted(expected - cols)
    assert not missing
