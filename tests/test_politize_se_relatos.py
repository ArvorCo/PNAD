"""Relatos de seção do Politize-se: esquema igual na migração, no exportador, na função e no app."""

from __future__ import annotations

import csv
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest
from politize_se import relatos

ROOT = Path(__file__).resolve().parents[1]
SQL = (ROOT / "totalizacao/supabase/migrations/0005_relatos_secao.sql").read_text(
    encoding="utf-8"
)
TS = (ROOT / "totalizacao/src/relato/validar.ts").read_text(encoding="utf-8")
APP = (ROOT / "docs/assets/politize_se/relatos.js").read_text(encoding="utf-8")
PAGINA = (ROOT / "docs/politizese.html").read_text(encoding="utf-8")


def _enum(nome: str) -> list[str]:
    bloco = re.search(rf"create type {nome} as enum \(([^)]*)\)", SQL)
    assert bloco
    return re.findall(r"'([a-z_]+)'", bloco.group(1))


def _colunas_tabela() -> list[str]:
    bloco = re.search(
        r"create table if not exists relato_secao \((.*?)\n\);", SQL, re.DOTALL
    )
    assert bloco
    return [
        m.group(1)
        for m in re.finditer(r"^\s{2}([a-z_]+)\s+\S", bloco.group(1), re.MULTILINE)
    ]


def test_colunas_iguais_na_migracao():
    assert _colunas_tabela() == relatos.COLUNAS


def test_tipos_e_status_iguais_em_todo_lugar():
    assert _enum("relato_tipo") == relatos.TIPOS
    assert _enum("relato_status") == relatos.STATUS
    assert re.findall(r'^  "([a-z_]+)",$', TS, re.MULTILINE) == relatos.TIPOS
    assert re.findall(r"^  \['([a-z_]+)', '", APP, re.MULTILINE) == relatos.TIPOS


def test_seguranca_da_migracao():
    assert "enable row level security" in SQL
    assert "create policy" not in SQL.lower()
    assert re.search(r"grant select on v_relatos_resumo, v_relatos_secao to anon;", SQL)
    assert not re.search(r"grant [^;]* on relato_secao[^;]* to anon", SQL)
    for view in ("v_relatos_resumo", "v_relatos_secao"):
        corpo = re.search(
            rf"create or replace view {view} as(.*?);", SQL, re.DOTALL
        ).group(1)
        for proibido in (
            "texto",
            "contato",
            "ip_hash",
            "hora_aproximada",
            "user_agent",
        ):
            assert proibido not in corpo, (view, proibido)
        assert "descartado" in corpo
    assert "interval '1 hour'" in SQL and ">= 5" in SQL
    assert "public, extensions" in SQL
    assert "revoke truncate" in SQL


def test_sql_exportar_e_marcar():
    assert relatos.sql_exportar().endswith("from relato_secao order by id")
    assert "where status = 'novo' and id > 7" in relatos.sql_exportar("novo", 7)
    with pytest.raises(ValueError):
        relatos.sql_exportar("x'; drop table relato_secao; --")
    assert "where id in (3, 4)" in relatos.sql_marcar([3, 4], "lido")
    with pytest.raises(ValueError):
        relatos.sql_marcar([1], "apagado")
    with pytest.raises(ValueError):
        relatos.sql_marcar([], "lido")


def _linha(**kw) -> dict:
    base = dict.fromkeys(relatos.COLUNAS)
    base.update(
        id=1,
        criado_em="2026-10-26 14:00:00+00",
        turno=2,
        uf="SP",
        zona=1,
        secao=12,
        secao_no_cadastro=True,
        tipo="fila_longa",
        texto="Fila de duas horas, com vírgula",
        hora_aproximada="16:45:00",
        presenciou=True,
        ip_hash="a" * 64,
        origem="politize-se",
        status="novo",
    )
    base.update(kw)
    return base


def test_normalizar_resumo_e_gravar(tmp_path):
    linhas = relatos.normalizar(
        [_linha(), _linha(id=2, tipo="outro", contato="+5511987654321", status="lido")]
    )
    assert [x["hora_aproximada"] for x in linhas] == ["16:45", "16:45"]
    r = relatos.resumo(linhas)
    assert (
        r["total"] == 2
        and r["com_contato"] == 1
        and r["por_status"] == {"novo": 1, "lido": 1}
    )
    js, cs = relatos.gravar(
        linhas, tmp_path, datetime(2026, 10, 26, 15, tzinfo=timezone.utc)
    )
    assert json.loads(js.read_text(encoding="utf-8"))["resumo"]["total"] == 2
    with cs.open(encoding="utf-8") as f:
        lidas = list(csv.DictReader(f))
    assert (
        list(lidas[0]) == relatos.COLUNAS
        and lidas[0]["texto"] == "Fila de duas horas, com vírgula"
    )
    with pytest.raises(ValueError):
        relatos.normalizar([_linha(tipo="fraude")])
    with pytest.raises(ValueError):
        relatos.normalizar([{"id": 1}])


def test_saida_ignorada_pelo_git():
    alvo = relatos.SAIDA.relative_to(ROOT) / "relatos_x.json"
    r = subprocess.run(["git", "check-ignore", "-q", str(alvo)], cwd=ROOT, check=False)
    assert r.returncode == 0
    assert not str(relatos.SAIDA.relative_to(ROOT)).startswith("docs")


def test_pagina_e_app():
    assert "assets/totalizacao/config.js" in PAGINA
    assert "/functions/v1/receber-relato" in APP and "v_relatos_secao" in APP
    # contagem por zona inteira: a seção não vai na consulta
    consulta = re.search(r"v_relatos_secao\?[^`]*`", APP).group(0)
    assert "zona=eq." in consulta and "secao=eq." not in consulta
    assert "service_role" not in APP and "sb_secret" not in APP
    # barreiras sem terceiros: armadilha, desafio próprio e prova de trabalho; nada de Cloudflare
    assert "name: 'website'" in APP and "'aria-hidden': 'true'" in APP
    assert "?desafio=1" in APP and "nonce" in APP and "new Worker" in APP
    assert "turnstile" not in APP.lower() and "cloudflare" not in APP.lower()
    funcao = (
        ROOT / "totalizacao/supabase/functions/receber-relato/index.ts"
    ).read_text(encoding="utf-8")
    assert (
        "TURNSTILE" not in funcao
        and "conferirDesafio" in funcao
        and "armadilha" in funcao
    )
    bloco = APP
    assert "—" not in bloco and "fraude" not in bloco.lower()
