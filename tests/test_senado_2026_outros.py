"""Validação do esquema de todas as ondas de Senado em analysis/senado_2026/pesquisas."""

import hashlib
import importlib.util
import json
from datetime import date
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
PESQUISAS = RAIZ / "analysis" / "senado_2026" / "pesquisas"
_spec = importlib.util.spec_from_file_location(
    "senado_outros", RAIZ / "scripts" / "senado-2026-outros.py"
)
assert _spec and _spec.loader
outros = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(outros)

ARQUIVOS = sorted(PESQUISAS.glob("*.json"))


def ler(arquivo: Path) -> dict:
    return json.loads(arquivo.read_text(encoding="utf-8"))


def test_ha_pesquisas() -> None:
    assert ARQUIVOS


@pytest.mark.parametrize("arquivo", ARQUIVOS, ids=lambda p: p.name)
def test_esquema_da_onda(arquivo: Path) -> None:
    doc = ler(arquivo)
    assert outros.validar(doc) == []
    assert arquivo.name.startswith(f"{doc['instituto_slug']}_{doc['uf']}_")
    assert doc["cargo"] == "senador"
    if doc["campo"]:
        assert date.fromisoformat(doc["campo"]["fim"]) >= date.fromisoformat(
            doc["campo"]["inicio"]
        )
        assert arquivo.stem.endswith(doc["campo"]["fim"])
    if doc.get("divulgacao"):
        date.fromisoformat(doc["divulgacao"])
    assert all(
        c["partido"] is None or c["partido"] == c["partido"].upper()
        for c in doc["candidatos"]
    )
    assert "\u2014" not in arquivo.read_text(encoding="utf-8")


@pytest.mark.parametrize("arquivo", ARQUIVOS, ids=lambda p: p.name)
def test_soma_coerente(arquivo: Path) -> None:
    doc = ler(arquivo)
    perg = doc["pergunta"]
    if perg.get("base") == "validos" or perg.get("soma_total") is None:
        pytest.skip("sem soma comparável")
    dif = abs(outros.soma_declarada(doc) - perg["soma_total"])
    assert dif <= (3 if perg["votos_por_eleitor"] == 1 else 1)
    if perg["votos_por_eleitor"] == 2:
        assert perg["soma_total"] > 100


@pytest.mark.parametrize(
    "arquivo",
    [a for a in ARQUIVOS if ler(a)["fonte"].get("tipo") == "pdf"],
    ids=lambda p: p.name,
)
def test_pdf_preservado_com_hash(arquivo: Path) -> None:
    fonte = ler(arquivo)["fonte"]
    pdf = RAIZ / fonte["arquivo"]
    if not pdf.exists():
        pytest.skip("PDF não versionado nesta cópia")
    assert hashlib.sha256(pdf.read_bytes()).hexdigest() == fonte["sha256"]
    assert fonte["pagina"] >= 1


def test_cobertura_cobre_as_27_ufs() -> None:
    cob = outros.cobertura(outros.carregar())
    assert sorted(cob) == sorted(outros.UFS)
    for dados in cob.values():
        assert dados["situacao"] in {
            "recente",
            "sem_pesquisa_recente_de_outros_institutos",
        }


def test_validar_detecta_soma_errada() -> None:
    doc = ler(next(a for a in ARQUIVOS if a.name.startswith("realtime_")))
    doc["pergunta"]["soma_total"] = 140.0
    assert outros.validar(doc)
