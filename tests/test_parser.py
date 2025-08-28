import sys
from pathlib import Path

import json

# Add scripts/ to import path
ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from parse_pnadc import sniff_delimiter, summarize_file, write_sample_csv  # type: ignore


def test_sniff_delimiter_semicolon():
    sample = """id;nome;idade\n1;Ana;30\n2;Bruno;41\n"""
    delim, has_header = sniff_delimiter(sample)
    assert delim == ";"
    assert has_header is True


def test_summarize_and_sample(tmp_path: Path):
    content = """id,valor
1,10
2,20
3,30
4,40
"""
    data_file = tmp_path / "sample.csv"
    data_file.write_text(content, encoding="utf-8")

    summary = summarize_file(data_file)
    assert summary["delimiter"] == ","
    assert summary["has_header"] is True
    assert summary["rows"] == 4
    assert summary["columns"] == 2

    out_dir = tmp_path / "out"
    out_path = write_sample_csv(data_file, out_dir, sample_rows=2)
    assert out_path.exists()
    lines = out_path.read_text(encoding="utf-8").strip().splitlines()
    # header + 2 rows
    assert len(lines) == 3

