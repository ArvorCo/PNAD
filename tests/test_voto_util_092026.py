"""Contratos do mapa do voto util (docs/mapa_do_voto_util.html).

Tres camadas precisam continuar honestas: a transcricao pagina a pagina das
pesquisas estaduais, o motor de cenario e a pagina gerada. Se uma leitura
deixar de fechar 100, se o modelo inventar voto ou se o texto ganhar travessao,
quebra aqui.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
QUAEST = ROOT / "analysis" / "voto_util" / "quaest"
OUTROS = ROOT / "analysis" / "voto_util" / "outros"
DATA_JSON = ROOT / "docs" / "assets" / "voto_util_092026.json"
PAGINA = ROOT / "docs" / "mapa_do_voto_util.html"
UFS: set[str] = {
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA",
    "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
}  # fmt: skip


def load(name: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


M = load("voto_util_modelo")
B = load("voto_util_base")


@pytest.fixture(scope="module")
def data() -> dict:
    if not DATA_JSON.exists():
        pytest.skip("rode scripts/voto-util-092026-data.py antes")
    return json.loads(DATA_JSON.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- modelo
def estado(**kw):
    base = {
        "uf": "XX",
        "peso": 1000.0,
        "F1": 35.0,
        "L1": 40.0,
        "T1": 12.0,
        "I1": 8.0,
        "B1": 5.0,
        "F2": 45.0,
        "L2": 43.0,
    }
    base.update(kw)
    return M.Estado(**base)


def test_cenario_zero_devolve_o_primeiro_turno() -> None:
    e = estado()
    c = M.cenario(e, 0.0, 0.0)
    assert (c["F"], c["L"], c["T"]) == (35.0, 40.0, 12.0)


def test_voto_util_completo_chega_ao_segundo_turno_de_flavio() -> None:
    e = estado()
    c = M.cenario(e, 1.0, 0.0)
    assert c["F"] == pytest.approx(45.0)
    assert c["L"] == pytest.approx(40.0)
    assert 0.0 <= c["T"] <= 12.0


def test_terceira_via_nunca_fica_negativa() -> None:
    e = estado(T1=1.0, fT_flavio=1.0, fT_lula=1.0)
    c = M.cenario(e, 1.0, 1.0)
    assert c["T"] == 0.0


def test_agregado_soma_cem_nos_validos() -> None:
    estados = [
        estado(uf="A"),
        estado(uf="B", peso=500.0, F1=50.0, L1=30.0, F2=58.0, L2=34.0),
    ]
    for lam, theta in ((0, 0), (0.5, 0), (1, 1), (0, 1)):
        a = M.agrega(estados, lam, theta)
        assert a["flavio_validos"] + a["lula_validos"] + a[
            "outros_validos"
        ] == pytest.approx(100.0)


def test_voto_util_da_direita_so_ajuda_flavio() -> None:
    estados = [estado()]
    anterior = M.agrega(estados, 0.0, 0.0)["margem"]
    for lam in (0.25, 0.5, 0.75, 1.0):
        atual = M.agrega(estados, lam, 0.0)["margem"]
        assert atual > anterior
        anterior = atual


def test_limiar_e_consistente_com_a_margem() -> None:
    estados = [estado()]
    lam = M.limiar(estados, "margem", 0.0)
    assert lam is not None and 0 < lam < 1
    assert M.agrega(estados, lam, 0.0)["margem"] >= -1e-9
    assert M.agrega(estados, max(0.0, lam - 0.01), 0.0)["margem"] < 0


def test_eleitor_provavel_pesa_pela_propensao() -> None:
    sempre = {"F": 40.0, "L": 30.0}
    outros = {"F": 20.0, "L": 50.0}
    tudo = M.eleitor_provavel(sempre, outros, 80, 20, 1.0)
    so_fiel = M.eleitor_provavel(sempre, outros, 80, 20, 0.0)
    assert so_fiel == pytest.approx(sempre)
    assert tudo["F"] == pytest.approx(36.0)


# ---------------------------------------------------------------- transcricoes
def test_ha_transcricao_quaest_para_25_estados() -> None:
    ufs = {p.stem for p in QUAEST.glob("*.json")}
    assert ufs == UFS - {"PI", "SE"}


@pytest.mark.parametrize("path", sorted(QUAEST.glob("*.json")), ids=lambda p: p.stem)
def test_primeiro_turno_quaest_fecha_cem(path: Path) -> None:
    d = json.loads(path.read_text(encoding="utf-8"))
    p = B.pres_1t_quaest(d)
    g = p["grupos"]
    soma = g["F"] + g["L"] + g["T"] + g["I"] + g["B"]
    assert 97 <= soma <= 103, (path.stem, soma)
    assert p["pagina"], "todo bloco guarda a pagina de origem"


@pytest.mark.parametrize("path", sorted(OUTROS.glob("*.json")), ids=lambda p: p.stem)
def test_primeiro_turno_real_time_fecha_cem(path: Path) -> None:
    d = json.loads(path.read_text(encoding="utf-8"))
    v = B.normaliza(d["pres_1t"]["valores"])
    assert 97 <= sum(v.values()) <= 103, (path.stem, sum(v.values()))
    assert d["pres_1t"].get("pagina")
    assert d.get("sha256") and d.get("registro_tse")


def test_controle_bahia_pagina_120() -> None:
    """Leitura feita na sessao e conferida pelo agente pela geometria do grafico."""
    d = json.loads((QUAEST / "BA.json").read_text(encoding="utf-8"))
    cols = B.cruzamento(d, "pres_1t_x_comparecimento")["colunas"]
    sempre = next(c for n, c in cols.items() if n.startswith("Sempre"))["valores"]
    assert (sempre["Lula"], sempre["Flávio"], sempre["Cury"], sempre["Caiado"]) == (
        60,
        23,
        3,
        3,
    )


def test_controle_goias_queda_de_caiado() -> None:
    d = json.loads((QUAEST / "GO.json").read_text(encoding="utf-8"))
    serie = B.pres_1t_quaest(d)["serie_valores"]
    assert serie[0]["valores"]["Caiado"] == 32
    assert serie[-1]["valores"]["Caiado"] == 23


# ---------------------------------------------------------------- base e pagina
def test_reserva_cobre_os_27_estados(data: dict) -> None:
    res = data["auxiliar"]["reserva_uf"]
    assert set(res) == UFS
    assert all(r["reserva_eleitores"] >= 0 for r in res.values())


def test_calibracao_reproduz_a_media_nacional(data: dict) -> None:
    alvo = data["auxiliar"]["alvo_nacional"]
    for nome in ("quaest", "realtime"):
        hoje = next(
            c
            for c in data["modelos"][nome]["cenarios"]
            if c["nome"] == "Hoje, todos os entrevistados"
        )
        assert hoje["flavio_validos"] == pytest.approx(alvo["flavio_validos"], abs=0.05)
        assert hoje["lula_validos"] == pytest.approx(alvo["lula_validos"], abs=0.05)


def test_cenarios_ordenados(data: dict) -> None:
    cen = {c["nome"]: c for c in data["modelos"]["media"]["cenarios"]}
    assert (
        cen["Voto útil completo"]["flavio_validos"]
        > cen["Metade do voto útil"]["flavio_validos"]
        > cen["Hoje, eleitor provável"]["flavio_validos"]
    )
    assert (
        cen["Só Lula consolida"]["lula_validos"]
        > cen["Os dois lados consolidam"]["lula_validos"]
    )


def test_matriz_de_transferencia_vem_da_nexus(data: dict) -> None:
    t = data["nacional"]["transferencia"]
    assert t["linhas"]["Renan"]["Flávio"] == 56
    assert 0 < t["terceira_lula"] < t["terceira_flavio"] < 1


def test_pagina_sem_travessao_e_com_todos_os_capitulos() -> None:
    if not PAGINA.exists():
        pytest.skip("rode scripts/voto-util-092026-build.py antes")
    html = PAGINA.read_text(encoding="utf-8")
    assert "—" not in html
    for sid in (
        "tese",
        "fenomeno",
        "matematica",
        "mapa",
        "nacional",
        "terceira",
        "governadores",
        "senado",
        "provavel",
        "resiliente",
        "modelo",
        "argumentos",
        "estados",
        "kit",
        "municipios",
        "lei",
        "limites",
        "fontes",
    ):
        assert f'id="{sid}"' in html, sid
    assert (
        'og:image" content="https://brasil.arvor.co/img/og/mapa_do_voto_util.png"'
        in html
    )
    for uf in UFS:
        assert f'id="uf-{uf}"' in html, uf
