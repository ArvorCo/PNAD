from pathlib import Path

from layout_sas import extract_line, fields_index, parse_layout

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def test_parse_layout_basic(tmp_path: Path):
    sas = tmp_path / "input.sas"
    sas.write_text(
        """
        @0001 UF 2.
        @0003 Capital $1.
        @0270 V4050 $1.   /* renda habitual aux */
        @0273 V405012 8.
        """,
        encoding="utf-8",
    )
    fields = parse_layout(sas)
    idx = fields_index(fields)
    assert idx["UF"].start == 0 and idx["UF"].width == 2 and idx["UF"].kind == "num"
    assert (
        idx["Capital"].start == 2
        and idx["Capital"].width == 1
        and idx["Capital"].kind == "char"
    )
    assert idx["V405012"].start == 272 and idx["V405012"].width == 8

    line = "351" + (" ") * (272 - 3) + "00001234" + " rest"
    vals = extract_line(line, [idx["UF"], idx["Capital"], idx["V405012"]])
    assert vals == ["35", "1", "00001234"]
