"""Coloca scripts/ no caminho de importação, sem hacks de sys.path em cada teste."""

import sys
from math import isfinite
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


@pytest.fixture
def assert_json_close():
    """Compara snapshots sem exigir os mesmos bits de float entre Pythons."""

    def compare(actual, expected, path="$"):
        assert type(actual) is type(expected), path
        if isinstance(expected, dict):
            assert actual.keys() == expected.keys(), path
            for key in expected:
                compare(actual[key], expected[key], f"{path}.{key}")
        elif isinstance(expected, list):
            assert len(actual) == len(expected), path
            for i, (left, right) in enumerate(zip(actual, expected, strict=True)):
                compare(left, right, f"{path}[{i}]")
        elif isinstance(expected, float):
            assert isfinite(actual) and isfinite(expected), path
            # Tolerância absoluta muito abaixo de qualquer precisão publicada;
            # não cresce com o tamanho do número nem altera os arquivos salvos.
            assert actual == pytest.approx(expected, rel=0, abs=1e-10), path
        else:
            assert actual == expected, path

    return compare
