"""Junção municipal sem aproximação de nomes e preservação da fonte."""

import csv
import hashlib
import json

import pytest
from analise_realidade_eleicao.desenvolvimento import CAMPOS, carregar
from apuracao_2t_2026.pagina_fig_noite_b import faixa_candidato


def fonte(tmp_path, nome="Açu", uf="RN"):
    p = tmp_path / "ips_2026.csv"
    with p.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["Município", "UF", *CAMPOS.values()])
        w.writeheader()
        w.writerow({"Município": nome, "UF": uf, **dict.fromkeys(CAMPOS.values(), 60)})
    (tmp_path / "fontes.json").write_text(
        json.dumps(
            [{"arquivo": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}]
        )
    )
    return tmp_path


def test_equivalencia_explicita_nao_casa_acu_com_macau(tmp_path):
    ms = [
        {"nome": "ASSÚ", "uf": "RN", "ibge": "2400208"},
        {"nome": "MACAU", "uf": "RN", "ibge": "2407203"},
    ]
    r = carregar(ms, fonte(tmp_path))
    assert set(r["dados"]) == {"2400208"}
    assert r["sem_ips"][0]["nome"] == "MACAU"
    assert len(r["equivalencias"]) == 1


def test_sem_correspondencia_nao_aproxima(tmp_path):
    ms = [{"nome": "MACAU", "uf": "RN", "ibge": "2407203"}]
    with pytest.raises(ValueError, match="inequívoco"):
        carregar(ms, fonte(tmp_path, "Macauu"))


def test_hash_divergente_rejeitado(tmp_path):
    fonte(tmp_path)
    with (tmp_path / "ips_2026.csv").open("a") as f:
        f.write("\n")
    with pytest.raises(ValueError, match="alterado"):
        carregar([], tmp_path)


def test_faixa_lula_inverte_extremos():
    assert faixa_candidato([45.72, 48.84], "lula") == pytest.approx((51.16, 54.28))
    assert faixa_candidato([45.72, 48.84], "flavio") == (45.72, 48.84)
