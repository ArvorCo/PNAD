"""Cobertura pública: indisponível não é zero e recortes preservam o histórico."""

import csv
import gzip
import json
import sqlite3
from collections import Counter

from apuracao_logs import mapa, publicacao
from apuracao_logs.coleta import SCHEMA
from apuracao_logs.mapa import publicar_recortes
from apuracao_logs.parser import VERSAO
from apuracao_logs.resumo import duracoes, situacao
from test_apuracao_logs_criterios import registro


def test_quantil_pondera_ciclos_sem_expandir_microdados():
    d = duracoes(Counter({10: 2, 50: 2}))
    assert d["media_s"] == 30 and d["mediana_s"] == 30
    assert d["p90_s"] == 50
    assert duracoes(Counter())["mediana_s"] is None
    assert duracoes(Counter({9: 100_000_000}))["mediana_s"] == 9


def test_estados_de_ausencia_nao_se_confundem():
    cat = {"nome": "log.jez", "hash": "a"}
    assert situacao(cat, "ok", "ok", True) == "lido"
    assert situacao(cat, "ok", "erro", True) == "erro_leitura"
    assert situacao(cat, "ok", None, True) == "processamento_pendente"
    assert situacao(cat, "ok", None, False) == "sem_bu"
    assert situacao(cat, None, None, True) == "download_pendente"
    assert situacao(cat, "hash_divergente", None, True) == "hash_divergente"
    assert situacao({**cat, "nome": None}, None, None, True) == "sem_nome"
    assert (
        situacao(
            {**cat, "nome": None, "status_aux": "Nao instalada"}, None, None, False
        )
        == "nao_instalada"
    )
    assert situacao({**cat, "nome": None}, None, None, True, 5) == "apuracao_sem_log"


def test_build_publico_fecha_cobertura_e_preserva_null(tmp_path, monkeypatch):
    monkeypatch.setattr(publicacao, "conferir", list)
    raw_path, src_path, met_path = [
        tmp_path / f"{n}.sqlite" for n in ("raw", "bu", "metricas")
    ]
    raw = sqlite3.connect(raw_path)
    raw.executescript(SCHEMA)
    sha = "a" * 64
    for s in range(1, 5):
        raw.execute(
            "INSERT INTO catalogo VALUES (?,?,?,?,?,?,?,?,?)",
            ("zz", "29327", 1, s, "h", "log.jez" if s != 2 else None, None, 1, "ok"),
        )
        if s != 2:
            raw.execute(
                "INSERT INTO arquivos VALUES (?,?,?,?,?,?,?,?,?,?)",
                ("zz", "29327", 1, s, sha, "ok", 200, "2026-10-15", None, b""),
            )
    raw.commit()
    raw.close()
    src = sqlite3.connect(src_path)
    src.execute(
        "CREATE TABLE bu (uf TEXT, mun TEXT, zona INTEGER, secao INTEGER, tipo_arquivo INTEGER)"
    )
    src.executemany("INSERT INTO bu VALUES ('zz','29327',1,?,1)", [(1,), (2,), (3,)])
    src.commit()
    src.close()
    met = sqlite3.connect(met_path)
    met.execute(
        "CREATE TABLE metricas (uf TEXT,mun TEXT,zona INTEGER,secao INTEGER,sha256 TEXT,versao TEXT,status TEXT,resumo TEXT)"
    )
    met.execute(
        "INSERT INTO metricas VALUES ('zz','29327',1,1,?,?,?,?)",
        (sha, VERSAO, "ok", json.dumps(registro())),
    )
    met.commit()
    met.close()
    for nome, valor in {
        "DESTINO": raw_path,
        "ORIGEM": src_path,
        "METRICAS": met_path,
        "PUBLICO": tmp_path / "publico",
        "ANALISE": tmp_path / "analise",
    }.items():
        monkeypatch.setattr(publicacao, nome, valor)
    d = publicacao.montar()
    assert d["cobertura"]["catalogadas"] == 4
    assert d["cobertura"]["lidos"] == 1
    assert sum(v["secoes"] for v in d["situacoes"].values()) == 4
    assert d["situacoes"]["sem_bu"]["secoes"] == 1
    assert d["situacoes"]["processamento_pendente"]["secoes"] == 1
    assert not d["concluido"]
    zone = json.loads(
        gzip.decompress((tmp_path / "publico/zona/ZZ/1.json.gz").read_bytes())
    )
    assert len(zone["linhas"]) == 1 and len(zone["indisponiveis"]) == 3
    row = dict(zip(zone["colunas"], zone["linhas"][0], strict=True))
    assert row["hash_anterior_confere"] is None
    assert "resultados.tse.jus.br" in row["url"] and row["sha256"] == sha
    assert not row["elegivel_tempo"]  # um ciclo não é amostra suficiente
    assert row["referencia_voto"] is None and row["escala_voto"] is None
    assert row["pares_tempo"] == 0
    with gzip.open(tmp_path / "publico/secoes.csv.gz", "rt") as f:
        csv_rows = list(csv.DictReader(f))
    assert len(csv_rows) == 1 and csv_rows[0]["hash_anterior_confere"] == ""


def test_recortes_mantem_historico_e_exterior_separados(tmp_path):
    obj = {
        "colunas": ["uf", "municipio", "nivel", "originais"],
        "linhas": [
            ["SP", "São Paulo", "alta", True],
            ["SP", "São Paulo", "logs", False],
            ["ZZ", "Lisboa", "logs", False],
        ],
    }
    publicar_recortes(obj, tmp_path)
    ind = json.loads((tmp_path / "indice.json").read_text())
    assert "linhas" not in ind and ind["niveis"] == {"alta": 1, "logs": 2}
    assert ind["partes"]["ZZ"]["municipios"] == ["Lisboa"]
    assert json.loads((tmp_path / "originais.json").read_text())["linhas"] == [
        obj["linhas"][0]
    ]
    assert json.loads((tmp_path / "uf/ZZ.json").read_text())["linhas"] == [
        obj["linhas"][2]
    ]


def test_mapa_inclui_suplemento_sem_inventar_coordenada_ou_pontos(
    tmp_path, monkeypatch
):
    politize = tmp_path / "politize"
    (politize / "mun/MG").mkdir(parents=True)
    (politize / "mun/MG/41335.json").write_text(
        json.dumps(
            {
                "nome": "Betim",
                "locais": {"colunas": ["local_id"], "linhas": []},
            }
        )
    )
    sinal = {
        "uf": "MG",
        "mun": "41335",
        "zona": 319,
        "secao": 58,
        "sinais": ["reinicios"],
        "voto_mediana": 60,
        "elegivel_tempo": True,
    }
    (tmp_path / "sinais.json").write_text(json.dumps([sinal]))
    (tmp_path / "indice.json").write_text(
        json.dumps({"criterios": {}, "cobertura": {}, "gerado_em": "agora"})
    )
    (tmp_path / "complementos.json").write_text(
        json.dumps(
            {
                "MG-319-58": {
                    "local_id": "MG-41335-319-1112",
                    "local": None,
                }
            }
        )
    )
    monkeypatch.setattr(mapa, "POLITIZE", politize)
    monkeypatch.setattr(mapa, "LOGS", tmp_path / "sinais.json")
    monkeypatch.setattr(mapa, "INDICE", tmp_path / "indice.json")
    obj = mapa.integrar(
        {
            "colunas": ["uf", "zona", "secao", "lat", "lon", "pontuacao", "nivel"],
            "linhas": [],
            "resumo": {"secoes": 0},
        }
    )
    row = dict(zip(obj["colunas"], obj["linhas"][0], strict=True))
    assert row["secao"] == 58 and row["logs"] == ["reinicios"]
    assert row["lat"] is None and row["lon"] is None and row["pontuacao"] is None
    assert row["nivel"] == "logs" and not row["originais"]
