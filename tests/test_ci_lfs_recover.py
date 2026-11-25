import hashlib
from importlib import import_module

import pytest

recover = import_module("ci-lfs-recover")


def test_unverified_content_cannot_replace_pointer(tmp_path):
    path = tmp_path / "report.pdf"
    path.write_bytes(b"committed pointer")
    other = tmp_path / "other.pdf"
    other.write_bytes(b"wrong")
    oid = hashlib.sha256(b"right").hexdigest()
    with pytest.raises(RuntimeError, match="SHA-256"):
        recover.fetch(path, oid, 5, [other.as_uri()])
    assert path.read_bytes() == b"committed pointer"
    good = tmp_path / "good.pdf"
    good.write_bytes(b"right")
    recover.fetch(path, oid, 5, [other.as_uri(), good.as_uri()])
    assert recover.matches(path, oid, 5)


def test_reuse_verified_duplicate_without_network(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    second.write_bytes(b"evidence")
    oid = hashlib.sha256(second.read_bytes()).hexdigest()
    recover.restore((oid, 8, [first, second]), "unused", "ArvorCo/PNAD")
    assert first.read_bytes() == second.read_bytes()
