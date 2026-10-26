"""Capítulos seções, paralela, exterior e governadores do dossiê do 2º turno.

Renderizam a partir dos JSONs de ``analysis/apuracao_2t_2026/dados``; os testes
conferem regras de texto da casa, a base declarada na tela (amostra ou banco
completo), a coerência entre figuras e estimativas e o CSV do ranking.
"""

from __future__ import annotations

import csv
import json
import shutil

import pytest
from apuracao_2t_2026 import pagina_cap_exterior as CE
from apuracao_2t_2026 import pagina_cap_governadores as CG
from apuracao_2t_2026 import pagina_cap_paralela as CP
from apuracao_2t_2026 import pagina_cap_secoes as CS
from apuracao_2t_2026 import pagina_fig_paralela as FP
from apuracao_2t_2026 import pagina_fig_secoes as FS
from apuracao_2t_2026 import pagina_fig_secoes_b as FSB
from apuracao_2t_2026 import pagina_texto_governadores as TG
from apuracao_2t_2026 import secoes_linhas
from apuracao_2t_2026.pagina_comum import DADOS
from apuracao_2t_2026.pagina_fig_secoes_base import indicador, linhas, peso_linha, pesos
from apuracao_2026.pagina_comum import Capitulo, Dados

NECESSARIOS = [
    "secoes.json",
    "secoes_voto.json",
    "secoes_ranking.json",
    "paralela.json",
    "exterior.json",
    "governadores.json",
    "presidente.json",
]


def _faltam() -> bool:
    if any(not (DADOS / n).exists() for n in NECESSARIOS):
        return True
    S = json.loads((DADOS / "secoes.json").read_text(encoding="utf-8"))
    return not secoes_linhas.disponivel(S)


pytestmark = pytest.mark.skipif(
    _faltam(), reason="JSONs do 2º turno ou linhas por seção (fora do git) ausentes"
)


def cap(ident: str) -> Capitulo:
    return Capitulo(ident, "08", ident, ident, (), None)


@pytest.fixture
def sem_escrita(tmp_path, monkeypatch):
    """CSV do ranking e QR vão para a pasta temporária, nunca para docs/."""
    monkeypatch.setattr(FSB, "CSV_DESTINO", tmp_path / "secoes_ranking.csv")
    monkeypatch.setattr(FP, "QR_DOCS", tmp_path / "nao_existe.svg")
    monkeypatch.setattr(FP, "QR_DESTINO", tmp_path / "img" / "qr.svg")
    return tmp_path


def regras_de_texto(h: str) -> None:
    assert "—" not in h
    assert "fraude" not in h.lower()
    assert len(h) > 2000


@pytest.mark.parametrize(
    "mod,ident",
    [(CS, "secoes"), (CP, "paralela"), (CE, "exterior"), (CG, "governadores")],
)
def test_renderiza_sem_travessao(mod, ident, sem_escrita):
    h = mod.render(Dados(pasta=DADOS), cap(ident))
    regras_de_texto(h)
    assert h.startswith('<div class="section-head">')


def test_secoes_rotulos_e_base(sem_escrita):
    d = Dados(pasta=DADOS)
    h = CS.render(d, cap("secoes"))
    S = d.get("secoes.json")
    assert "pede explicação, não prova irregularidade" in h
    assert "Base desta versão" in h
    if S["fonte"] == "amostra":
        assert "IC de 95%" in h
    assert S["prorrogacao"]["brasil"]["encerramento_p50"] in h
    for fig in (
        "secoes_encerramento",
        "secoes_emissao_recebimento",
        "secoes_comparecimento",
        "secoes_did",
        "secoes_mapa",
    ):
        assert f'id="fig-{fig}"' in h
    assert h.count("<tr>") >= len(d.get("secoes_ranking.json")["secoes"])


def test_csv_do_ranking(sem_escrita):
    d = Dados(pasta=DADOS)
    CS.render(d, cap("secoes"))
    R = d.get("secoes_ranking.json")
    with open(sem_escrita / "secoes_ranking.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == len(R["secoes"])
    assert set(FSB.COLUNAS_CSV) == set(rows[0])
    assert rows[0]["uf"] == R["secoes"][0]["uf"]


def test_distribuicao_bate_com_a_estimativa():
    d = Dados(pasta=DADOS)
    S, P = d.get("secoes.json"), d.get("presidente.json")
    dist = FS.distribuicao_encerramento(S, P)
    assert abs(sum(dist["2t"]) - 100) < 1e-6
    i19 = indicador(S, "apos_19h")
    assert abs(dist["2t"][-1] - i19["pct"]) < 0.05


def test_banco_completo_sem_ic(tmp_path, sem_escrita):
    """Com fonte completo e sem estimativa, a tela diz a base e não inventa IC."""
    for n in NECESSARIOS:
        shutil.copy(DADOS / n, tmp_path / n)
    S = json.loads((tmp_path / "secoes.json").read_text(encoding="utf-8"))
    S["fonte"] = "completo"
    S["estimativa_nacional"] = {"disponivel": False}
    (tmp_path / "secoes.json").write_text(json.dumps(S), encoding="utf-8")
    d = Dados(pasta=tmp_path)
    h = CS.render(d, cap("secoes"))
    regras_de_texto(h)
    assert "Base desta versão: banco completo" in h
    assert "IC de 95%" not in h
    i = indicador(d.get("secoes.json"), "delta")
    assert i["ic"] is None and i["pct"] is not None


def test_peso_zero_para_paralela_na_amostra():
    d = Dados(pasta=DADOS)
    S, P = d.get("secoes.json"), d.get("presidente.json")
    if S["fonte"] != "amostra":
        pytest.skip("só vale para a amostra")
    w = pesos(S, P)
    par = [x for x in linhas(S) if x["origem"] == "paralela"]
    assert par and all(peso_linha(x, w) == 0 for x in par)


def test_paralela_rotulo_fixo(sem_escrita):
    h = CP.render(Dados(pasta=DADOS), cap("paralela"))
    assert "soma dos BUs recebidos, não projeção" in h
    assert "brasil.arvor.co/totalizacao" in h
    assert (sem_escrita / "img" / "qr.svg").exists() or "<img" not in h


def test_governadores_detecta_viradas():
    G = Dados(pasta=DADOS).get("governadores.json")
    ufs_vir = {u["uf"] for u in TG.viradas_1t(G)}
    for u in G["ufs"]:
        a = max(u["candidatos"], key=lambda c: c["votos"])
        lider1 = max(u["candidatos"], key=lambda c: c["t1_pct"] or 0)
        assert (u["uf"] in ufs_vir) == (a["sqcand"] != lider1["sqcand"])
    ap = TG.mais_apertada(G)
    assert ap["margem_pp"] == min(u["margem_pp"] for u in G["ufs"])


def test_arquivo_ausente_vira_erro_de_dado(tmp_path):
    with pytest.raises(KeyError):
        CS.render(Dados(pasta=tmp_path), cap("secoes"))
    with pytest.raises(KeyError):
        CG.render(Dados(pasta=tmp_path), cap("governadores"))
