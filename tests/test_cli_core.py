import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from pnadc_cli import compile_row_expr, eval_row_expr, parse_agg  # type: ignore


def test_compile_and_eval_row_expr():
    cols = ["idade", "sexo", "renda"]
    code = compile_row_expr("int(idade) >= 30 and sexo == 'M'", cols)
    row_ok = {"idade": "35", "sexo": "M", "renda": "1000"}
    row_no = {"idade": "25", "sexo": "M", "renda": "800"}
    assert eval_row_expr(code, row_ok) is True
    assert eval_row_expr(code, row_no) is False


def test_parse_agg_specs():
    a = parse_agg("count()")
    assert a.func == "count" and a.column is None
    b = parse_agg("sum(renda)")
    assert b.func == "sum" and b.column == "renda"
    c = parse_agg("mean(idade)")
    assert c.func == "mean" and c.column == "idade"

