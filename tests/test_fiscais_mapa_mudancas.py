"""Camada de mudanças de endereço do 2º turno no mapa de fiscais."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MAPA = ROOT / "docs/assets/fiscais_mapa"
MUDANCAS = ROOT / "docs/assets/politize/dados/mudancas/indice.json"
TRAVESSAO = "—"
pytestmark = pytest.mark.skipif(
    not (MAPA / "dados.json").exists() or not MUDANCAS.exists(),
    reason="mapa ou camada de mudanças não gerados",
)


def _carregar():
    d = json.loads((MAPA / "dados.json").read_text(encoding="utf-8"))
    locais = [dict(zip(d["colunas_locais"], ln, strict=True)) for ln in d["locais"]]
    secoes = []
    for ln in d["secoes"]:
        r = dict(zip(d["colunas_secoes"], ln, strict=True))
        r["local"] = locais[r["li"]]
        secoes.append(r)
    return d, secoes


def test_criterio_no_indice():
    d = json.loads((MAPA / "indice.json").read_text(encoding="utf-8"))
    m = d["mudancas"]
    ref = json.loads(MUDANCAS.read_text(encoding="utf-8"))
    assert m["id"] == "mudanca_endereco"
    assert m["nome"] == "Mudou de endereço para o 2º turno"
    assert m["secoes"] == ref["total_secoes"] == 1362
    assert m["eleitores"] == ref["total_eleitores"]
    assert "união" in m["nota"] and TRAVESSAO not in json.dumps(m, ensure_ascii=False)
    assert "mudanca" in d["colunas_secoes"]


def test_secoes_com_mudanca_tem_os_campos():
    d, secoes = _carregar()
    com = [r for r in secoes if r["mudanca"]]
    assert len(com) == d["mudancas"]["secoes"]
    obrigatorios = {
        "cat", "nome_cat", "fonte", "nome_1t", "end_1t", "nome_2t", "end_2t",
        "bairro_2t", "cep_2t", "lat_2t", "lon_2t", "distancia_m", "maps_novo",
        "motivo_tre", "url_tre", "id_1t", "coord_2t",
    }  # fmt: skip
    for r in com:
        assert obrigatorios <= set(r["mudanca"])
        assert r["mudanca"]["fonte"] in ("ambos", "so_zip", "so_painel")
        if r["mudanca"]["coord_2t"]:
            # o ponto da seção é o prédio novo
            assert r["local"]["lat"] == r["mudanca"]["lat_2t"]
            assert r["local"]["coord_fonte"] == "local_2t"
    novas = [r for r in secoes if r["nivel"] == "mudanca"]
    assert len(novas) == d["mudancas"]["secoes_novas_no_mapa"]
    assert all(r["pontuacao"] is None and not r["logs"] and r["mudanca"] for r in novas)


def test_interface_sem_jargao_e_com_crit():
    js = (MAPA / "app.js").read_text(encoding="utf-8")
    html = (ROOT / "docs/fiscais_mapa.html").read_text(encoding="utf-8")
    assert TRAVESSAO not in js and TRAVESSAO not in html
    assert "fraude" not in html.lower() and "fraude" not in js.lower()
    assert "'crit='" in js and "mudanca_endereco" in js
    assert "20261019-clima" in html and html.count("20261019-clima") == 2
    interface = "\n".join(
        ln for ln in js.splitlines() if not ln.strip().startswith("//")
    )
    for termo in ("Vincenty", "WGS84", "ERA5"):
        assert termo not in interface
    assert "Previsão de modelo global, muda todo dia" in js
