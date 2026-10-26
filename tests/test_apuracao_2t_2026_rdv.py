"""RDV do 2º turno: limites de Fréchet, categorias, trânsito e geração a partir de um banco mínimo."""

import sqlite3

import pytest
from apuracao_2t_2026 import rdv as R


def test_frechet_limites_e_independencia():
    f = R.frechet({"13": 6, "22": 4}, {"10": 7, "11": 3}, 10)
    assert f[("13", "10")] == (3, 6, pytest.approx(4.2))
    assert f[("22", "11")] == (0, 3, pytest.approx(1.2))
    # os mínimos nunca excedem os máximos e as linhas do máximo cobrem a margem
    assert all(lo <= hi for lo, hi, _ in f.values())
    with pytest.raises(ValueError):
        R.frechet({"13": 1}, {"10": 2}, 2)


def test_categoria_e_transito():
    assert R.categoria(2, "22") == "22"
    assert R.categoria(3, "") == "branco"
    assert R.categoria(5, "") == "branco"
    assert R.categoria(4, "13") == "nulo"
    assert R.categoria(7, "13") == "nulo"
    p, g = R.completar_transito({"13": 3, "22": 2}, {"10": 4})
    assert g == {"10": 4, "transito": 1}
    assert R.eixos(p, g) == (
        ["13", "22", "branco", "nulo"],
        ["10", "branco", "nulo", "transito"],
    )


ESQ = """
CREATE TABLE rdv (uf TEXT, mun TEXT, zona INT, secao INT, status TEXT, confere INT,
  bu_nome TEXT, divergencias TEXT);
CREATE TABLE rdv_cargo (uf TEXT, mun TEXT, zona INT, secao INT, cargo INT, eleicao INT,
  escolhas INT, votos INT, ordenado INT);
CREATE TABLE rdv_voto (uf TEXT, mun TEXT, zona INT, secao INT, cargo INT, tipo INT,
  digitacao TEXT, votos INT);
"""


def _banco(path):
    db = sqlite3.connect(path)
    db.executescript(ESQ)
    db.execute("INSERT INTO rdv VALUES ('ac','01007',9,1,'ok',1,'x-bu.dat',NULL)")
    db.execute("INSERT INTO rdv VALUES ('ac','01007',9,2,'aux_404',NULL,NULL,NULL)")
    votos = [
        (1, 2, "13", 3),
        (1, 2, "22", 6),
        (1, 4, "11", 1),
        (3, 2, "10", 4),
        (3, 2, "11", 4),
        (3, 4, "22", 1),
    ]
    for cargo, tipo, dig, n in votos:
        db.execute(
            "INSERT INTO rdv_voto VALUES ('ac','01007',9,1,?,?,?,?)",
            (cargo, tipo, dig, n),
        )
    for cargo, n in ((1, 10), (3, 9)):
        db.execute(
            "INSERT INTO rdv_cargo VALUES ('ac','01007',9,1,?,0,1,?,1)", (cargo, n)
        )
    db.commit()
    db.close()


def test_gerar_banco_minimo(tmp_path):
    arq = tmp_path / "rdv.sqlite"
    _banco(arq)
    d = R.gerar(arq, None, tmp_path / "sem_governadores.json")
    assert d["meta"]["parcial"] is True
    cob = d["cobertura"]["ufs"]["ac"]
    assert cob["ok"] == 1 and cob["confere"] == 1 and cob["aux_404"] == 1
    m = d["cruzado_limites"]["ac"]
    assert m["eixo_governador"] == ["10", "11", "branco", "nulo", "transito"]
    assert m["uf"]["n"] == 10
    cel = {(c["presidente"], c["governador"]): c for c in m["uf"]["celulas"]}
    assert (cel[("22", "10")]["min"], cel[("22", "10")]["max"]) == (0, 4)
    assert cel[("13", "transito")]["max"] == 1
    t = d["troca_de_campo"]["ac"]
    assert (
        t["governador_com_22"] == 1 and t["presidente_com_numero_de_governador"] == {}
    )
    assert d["troca_de_campo"]["seis_ufs"]["governador_com_numero_de_presidente"] == 1
    assert "limites" in d["rotulo"]


def test_conferencia_busa_sem_votos(tmp_path):
    arq = tmp_path / "rdv.sqlite"
    _banco(arq)
    db = sqlite3.connect(arq)
    db.execute(
        "INSERT INTO rdv VALUES ('zz','29564',1,91,'ok',1,'o03221zz2956400010091-busa.dat',NULL)"
    )
    db.execute("INSERT INTO rdv_cargo VALUES ('zz','29564',1,91,1,6258,1,0,1)")
    db.commit()
    db.close()
    c = R.conferencia_busa(sqlite3.connect(arq))
    assert c["conferidas_pelo_busa_sem_votos"] == 1
    assert c["conferidas_pelo_busa_com_votos"] == 0
    assert "busa" in c["secoes_sem_votos"][0]["motivo"]
