import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from layout_sas import parse_layout, fields_index, extract_line  # type: ignore


def test_positions_for_ano_trimestre_uf_capital(tmp_path: Path):
    sas = tmp_path / "input.sas"
    sas.write_text(
        """
        @0001 Ano   $4.   /* Ano de referência */
        @0005 Trimestre   $1.   /* Trimestre de referência */
        @0006 UF   $2.   /* Unidade da Federação */
        @0008 Capital   $2.   /* Município da Capital */
        """,
        encoding="utf-8",
    )
    fields = parse_layout(sas)
    idx = fields_index(fields)
    assert idx["Ano"].start == 0 and idx["Ano"].width == 4 and idx["Ano"].kind == "char"
    assert idx["Trimestre"].start == 4 and idx["Trimestre"].width == 1 and idx["Trimestre"].kind == "char"
    assert idx["UF"].start == 5 and idx["UF"].width == 2 and idx["UF"].kind == "char"
    assert idx["Capital"].start == 7 and idx["Capital"].width == 2 and idx["Capital"].kind == "char"

    line = "2024" + "1" + "SP" + "35" + "resto"
    vals = extract_line(line, [idx["Ano"], idx["Trimestre"], idx["UF"], idx["Capital"]])
    assert vals == ["2024", "1", "SP", "35"]

    # Labels and slugs
    assert idx["Ano"].label and idx["Ano"].slug
    assert idx["UF"].slug == "unidade_da_federacao"
