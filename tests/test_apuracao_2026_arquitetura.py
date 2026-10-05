"""Bloco de arquitetura do capítulo 3: contas puras, figuras e texto, sobre fixtures pequenas."""

import json
import re
import sqlite3
from datetime import datetime, timedelta

from apuracao_2026 import arquitetura as A
from apuracao_2026 import pagina_texto_arquitetura as TA
from apuracao_2026.pagina_comum import Dados
from apuracao_2026.pagina_figuras import FIGURAS

T0 = datetime(2026, 10, 4, 17, 0)


def _ts(*minutos: float) -> list[datetime]:
    return [T0 + timedelta(minutes=m) for m in minutos]


def test_por_minuto_preenche_zero():
    s = A.por_minuto(_ts(0.1, 0.5, 2.2), T0, T0 + timedelta(minutes=4))
    assert s == [["17:00", 2], ["17:01", 0], ["17:02", 1], ["17:03", 0]]


def test_lacunas_acima_do_limiar():
    lac = A.lacunas(_ts(0, 1, 2, 30, 31), T0, T0 + timedelta(hours=1))
    assert len(lac) == 1
    assert lac[0]["de"].endswith("17:02:00") and lac[0]["ate"].endswith("17:30:00")
    assert lac[0]["minutos"] == 28.0


def test_taxas_e_pico_sustentado():
    vs = [
        {"gerado_brt": "2026-10-04 18:00:00", "st": 1000},
        {"gerado_brt": "2026-10-04 18:01:00", "st": 9000},
        {"gerado_brt": "2026-10-04 18:11:00", "st": 49000},
        {"gerado_brt": "2026-10-04 18:11:00", "st": 49000},
    ]
    tx = A.taxas_nacionais(vs)
    assert [x["secoes_por_minuto"] for x in tx] == [8000.0, 4000.0]
    # A rajada de um minuto não conta como pico sustentado.
    assert A.pico_sustentado(tx)["secoes_por_minuto"] == 4000.0


def test_dimensionar():
    dim = A.dimensionar(
        secoes_amostra=1000,
        bu_bytes_medio=10_000,
        log_bytes_medio=100_000,
        linhas_por_secao=100,
        pico_secoes_min=6000,
        secoes_paradas=50_000,
        secoes_pais=4000,
    )
    assert dim["fator_extrapolacao"] == 4.0
    assert dim["bu_total_mb"] == 40.0
    assert dim["linhas_voto_total"] == 400_000
    assert dim["pico_secoes_por_segundo"] == 100.0
    assert dim["pico_linhas_por_segundo"] == 10_000
    assert dim["linhas_represadas"] == 5_000_000


def test_publicacao_brt_converte_fuso():
    s = A.publicacao_brt(
        [["2026-10-04T20:01", 5, 2_000_000]], T0, T0 + timedelta(minutes=3)
    )
    assert s == [["17:00", 0, 0.0], ["17:01", 5, 2.0], ["17:02", 0, 0.0]]


def test_ler_secoes_2026(tmp_path):
    db = tmp_path / "s.sqlite"
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE secao (uf, mun, zona, secao, dr_hr, bu_bytes, log_bytes)")
    con.execute("CREATE TABLE voto_secao (uf, mun, zona, secao, cargo, votos)")
    for i in range(120):
        con.execute(
            "INSERT INTO secao VALUES ('ac', '1', 1, ?, ?, 1000, 5000)",
            (i, f"2026-10-04 18:{i % 60:02d}:00"),
        )
        con.execute("INSERT INTO voto_secao VALUES ('ac', '1', 1, ?, 1, 3)", (i,))
        con.execute("INSERT INTO voto_secao VALUES ('ac', '1', 1, ?, 6, 3)", (i,))
    con.execute(
        "INSERT INTO secao VALUES ('zz', '9', 1, 1, '2026-10-04 10:00:00', 1, 1)"
    )
    con.commit()
    con.close()
    s = A.ler_secoes_2026(db)
    assert len(s["recebimentos"]) == 120
    assert s["ufs_cobertas"] == ["AC"]
    assert s["linhas_voto"] / s["secoes_com_voto"] == 2


def _fixture() -> dict:
    lin = [[f"17:{m:02d}", m % 7, (m % 7) * 3] for m in range(10)]
    pub = [[f"17:{m:02d}", 10 + m, 1.5] for m in range(10)]
    return {
        "amostra": {
            "secoes_com_recebimento": 40,
            "ufs_cobertas": ["AC", "DF"],
            "ufs_ausentes": ["SP"],
            "fracao_do_pais": 0.33,
            "fator_extrapolacao": 3.0,
            "secoes_pais": 120,
        },
        "recebimento_2026": {
            "colunas": ["minuto", "secoes_amostra", "secoes_extrapoladas"],
            "linhas": lin,
            "lacunas": [
                {
                    "de": "2026-10-04 17:03:00",
                    "ate": "2026-10-04 17:06:00",
                    "minutos": 3.0,
                }
            ],
        },
        "recebimento_2022": {
            "linhas": [[f"17:{m:02d}", m] for m in range(10)],
            "pico": {"minuto": "17:09", "secoes": 9},
            "atraso_recebimento_totalizacao_s": {
                "p50": 45.0,
                "p90": 93.0,
                "p99": 339.0,
            },
        },
        "publicacao_2026": {
            "linhas": pub,
            "pico_versoes": {"minuto": "17:09", "versoes": 19},
            "pico_mb": {"minuto": "17:09", "mb": 1.5},
            "versoes_total_banco": 1000,
        },
        "nacional": {
            "taxas": [
                {
                    "de": "2026-10-04 17:01:00",
                    "ate": "2026-10-04 17:05:00",
                    "minutos": 4,
                    "secoes": 20,
                    "secoes_por_minuto": 5.0,
                }
            ],
            "pico_sustentado": {
                "de": "2026-10-04 17:01:00",
                "ate": "2026-10-04 17:05:00",
                "secoes_por_minuto": 5.0,
            },
            "parada_mais_longa": {"secoes_no_salto": 20, "minutos": 4},
        },
        "volume": {
            "bu_bytes": {"media": 10_000},
            "bu_total_mb": 1.2,
            "log_total_mb": 12.0,
            "linhas_por_secao": 100.0,
            "linhas_voto_total": 12_000,
            "linhas_voto_amostra": 4000,
            "pico_secoes_por_segundo": 0.1,
            "pico_linhas_por_segundo": 8,
            "pico_bu_mb_por_minuto": 0.05,
            "linhas_por_minuto_nota_tse_2020": 1_000_000,
        },
        "fontes": [
            {
                "id": "tse_nota_tecnica_2020",
                "veiculo": "TSE",
                "data": "2020-11-17",
                "url": "https://example.org/nota",
            }
        ],
    }


def _linha_do_tempo() -> dict:
    return {
        "travamentos": {
            "nacional": [
                {
                    "de_brt": "2026-10-04 17:02:00",
                    "ate_brt": "2026-10-04 17:05:00",
                    "minutos": 3,
                    "secoes_no_salto": 2000,
                }
            ]
        },
        "pausa_geral": {
            "lacunas": [
                {"de_brt": "2026-10-04 17:03:00", "ate_brt": "2026-10-04 17:06:00"}
            ]
        },
    }


def _tips(h: str) -> dict:
    m = re.search(
        r'<script type="application/json" class="tips">(.*?)</script>', h, re.DOTALL
    )
    return json.loads(m.group(1).replace("<\\/", "</"))


def test_figuras_sobre_a_fixture():
    d = {"arquitetura": _fixture(), "linha_do_tempo": _linha_do_tempo()}
    for nome in ("volume_noite", "arquitetura_totalizacao"):
        h = FIGURAS[nome](d)
        assert h.startswith(f'<figure class="reveal fig-i" id="fig-{nome}"'), nome
        assert h.count("<svg") == 1 and "<title>" in h and "—" not in h
        tips = _tips(h)
        linhas = tips.get("_rows", {}).get("linhas", [])
        for k in re.findall(r'data-k="([^"]+)"', h):
            if k.startswith("r") and k[1:].isdigit():
                assert int(k[1:]) < len(linhas)
            else:
                assert k in tips, k
        tamanhos = [float(x) for x in re.findall(r'<text[^>]*font-size="([0-9.]+)"', h)]
        assert min(tamanhos) >= 13


def test_versao_empilhada_tem_as_mesmas_fichas():
    h = FIGURAS["arquitetura_totalizacao"]({"arquitetura": _fixture()})
    larga = h.split('<div class="fig-estreita">')[0]
    estreita = h.split('<div class="fig-estreita">')[1]
    chaves_larga = set(re.findall(r'data-k="([^"]+)"', larga))
    chaves_estreita = set(re.findall(r'data-k="([^"]+)"', estreita))
    assert chaves_estreita == chaves_larga
    assert "Hipótese do autor" in estreita


def test_figura_sem_dado_vira_pendente():
    assert 'class="pendente"' in FIGURAS["volume_noite"]({})


def test_bloco_de_texto(tmp_path):
    (tmp_path / "arquitetura.json").write_text(
        json.dumps(_fixture(), ensure_ascii=False), encoding="utf-8"
    )
    (tmp_path / "linha_do_tempo.json").write_text(
        json.dumps(_linha_do_tempo()), encoding="utf-8"
    )
    h = TA.bloco(Dados(pasta=tmp_path))
    assert "Onde um sistema como esse engasga" in h
    assert "O desenho que não engasga" in h
    assert "Hipótese do autor" in h and 'class="analogy"' in h
    assert "a causa é hipótese até o TSE publicar o relatório" in h
    assert "—" not in h


def test_bloco_sem_dado_some(tmp_path):
    assert TA.bloco(Dados(pasta=tmp_path)) == ""
