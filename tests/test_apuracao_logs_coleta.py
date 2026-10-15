"""Retomada e integridade dos originais sem depender da rede do TSE."""

import hashlib

import pytest
from apuracao_logs import coleta, complementos


def test_retomada_nao_rebaixa_original_ok_e_repete_erro(tmp_path, monkeypatch):
    db = tmp_path / "logs.sqlite"
    con = coleta.abrir(db)
    for s in (1, 2, 3):
        con.execute(
            "INSERT INTO catalogo VALUES ('sp','71072',1,?,'h','log.jez',NULL,1,'ok')",
            (s,),
        )
    con.execute(
        "INSERT INTO arquivos VALUES ('sp','71072',1,1,'a','ok',200,'data',NULL,?)",
        (b"original",),
    )
    con.execute(
        "INSERT INTO arquivos VALUES ('sp','71072',1,2,NULL,'erro',500,'data','falha',NULL)"
    )
    con.commit()
    con.close()
    pedidos = []

    def obter(self, r):
        pedidos.append(r["secao"])
        return (
            r["uf"],
            r["mun"],
            r["zona"],
            r["secao"],
            "b",
            "ok",
            200,
            "nova",
            None,
            b"novo",
        )

    monkeypatch.setattr(coleta.Cliente, "obter", obter)
    coleta.coletar(db, limite=0, workers=2, rps=1, ufs=[])
    con = coleta.abrir(db)
    assert sorted(pedidos) == [2, 3]
    assert (
        con.execute("SELECT zip FROM arquivos WHERE secao=1").fetchone()[0]
        == b"original"
    )
    assert (
        con.execute("SELECT COUNT(*) FROM arquivos WHERE status='ok'").fetchone()[0]
        == 3
    )
    con.close()


def test_hash_divergente_nao_e_original_validado(monkeypatch):
    corpo = b"PKarquivo-de-teste"

    class Session:
        def __init__(self):
            self.headers = {}

        def get(self, *_args, **_kwargs):
            return type("Response", (), {"status_code": 200, "content": corpo})()

    monkeypatch.setattr(coleta.requests, "Session", Session)
    r = {
        "uf": "sp",
        "mun": "71072",
        "zona": 1,
        "secao": 1,
        "hash": "h",
        "nome": "log.jez",
        "sha256_esperado": "incompativel",
    }
    result = coleta.Cliente(60).obter(r)
    assert result[5] == "hash_divergente" and result[-1] == corpo
    r["sha256_esperado"] = hashlib.sha256(corpo).hexdigest()
    assert coleta.Cliente(60).obter(r)[5] == "ok"
    r["sha256_esperado"] = None
    assert coleta.Cliente(60).obter(r)[5] == "ok"


def test_complemento_preenche_lacuna_sem_substituir_hash_existente(
    tmp_path, monkeypatch
):
    db = tmp_path / "logs.sqlite"
    con = coleta.abrir(db)
    con.execute(
        "INSERT INTO catalogo VALUES ('sp','63134',388,147,NULL,NULL,NULL,NULL,'aux_404')"
    )
    con.commit()
    con.close()
    chave = ("sp", "63134", 388, 147)
    monkeypatch.setattr(complementos, "DESTINO", db)
    monkeypatch.setattr(
        complementos, "carregar", lambda: {chave: {"hash": "novo", "nome": "log.jez"}}
    )
    manifesto = tmp_path / "complementos.json"
    manifesto.write_text("{}")
    monkeypatch.setattr(complementos, "MANIFESTO", manifesto)
    complementos.aplicar()
    complementos.aplicar()  # retomada idempotente
    con = coleta.abrir(db)
    assert tuple(
        con.execute("SELECT hash,nome,status_aux FROM catalogo").fetchone()
    ) == ("novo", "log.jez", "aux_404")
    con.execute("UPDATE catalogo SET hash='anterior-diferente'")
    con.commit()
    with pytest.raises(AssertionError):
        complementos.aplicar()
    assert (
        con.execute("SELECT hash FROM catalogo").fetchone()[0] == "anterior-diferente"
    )
    con.close()
