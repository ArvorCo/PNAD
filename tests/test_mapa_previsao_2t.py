"""Mapa de previsão por estado: contratos entre motor, JSON publicado e figura."""

import json
from pathlib import Path

from mapa_previsao_2t.figura import DOMINIO, cor, pagina
from mapa_previsao_2t.motor import SNAPSHOT

ROOT = Path(__file__).resolve().parents[1]
JSON = ROOT / "docs/assets/mapa_previsao_2t_2026.json"
HTML = ROOT / "docs/assets/og/mapa_previsao_2t_2026.html"


def _data():
    return json.loads(JSON.read_text(encoding="utf-8"))


def test_ancoras_batem_com_as_centrais_publicadas():
    data = _data()
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert data["fontes"]["snapshot_centrais"] == snapshot["version"]
    for chave, campo in (("media", "central"), ("projecao", "central_projection")):
        c = snapshot[campo]
        esperado = 100 * c["flavio"] / (c["flavio"] + c["lula"])
        assert abs(data["nacional"][chave]["flavio_pct"] - esperado) < 1e-6


def test_estados_somam_o_pais_e_conservam_eleitorado():
    data = _data()
    assert len(data["ufs"]) == 27 and "ZZ" not in {r["uf"] for r in data["ufs"]}
    for chave in ("media", "projecao", "transportado"):
        f = sum(r[chave]["flavio_votos"] for r in data["ufs"])
        validos = sum(r[chave]["validos"] for r in data["ufs"])
        assert abs(100 * f / validos - data["nacional"][chave]["flavio_pct"]) < 1e-6
    aptos = sum(r["aptos"] for r in data["ufs"])
    assert aptos == data["cobertura"]["aptos"]


def test_ordem_entre_ancoras_e_sinal_do_deslocamento():
    data = _data()
    for r in data["ufs"]:
        assert r["media"]["diferenca_pp"] > r["projecao"]["diferenca_pp"]
        assert abs(r["media"]["flavio_pct"] + r["media"]["lula_pct"] - 100) < 1e-9
    assert data["nacional"]["media"]["deslocamento_log_odds"] > 0


def test_figura_sem_travessao_e_com_todas_as_ufs():
    data = _data()
    html = pagina(data)
    assert "—" not in html
    assert HTML.read_text(encoding="utf-8") == html
    for r in data["ufs"]:
        assert f">{r['uf']} " in html
    assert cor(0) != cor(DOMINIO) and cor(-DOMINIO) != cor(DOMINIO)
