"""Relatos de seção do Politize-se: exportação para avaliação interna e troca de status.

Lê a tabela `relato_secao` do projeto Supabase PNAD pela API de gestão, com o token do CLI do
Supabase guardado no keychain do macOS (nunca a chave publicável, que não lê a tabela). O token
não é impresso nem gravado. A saída vai para `analysis/politize_se/relatos/`, ignorada pelo git:
o texto e o contato nunca são publicados. Esquema na migração
`totalizacao/supabase/migrations/0005_relatos_secao.sql`.
"""

from __future__ import annotations

import base64
import csv
import json
import subprocess
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJETO = "brvjvizqbyfamtxogvqf"
API = f"https://api.supabase.com/v1/projects/{PROJETO}/database/query"
SAIDA = ROOT / "analysis/politize_se/relatos"
MIGRACAO = ROOT / "totalizacao/supabase/migrations/0005_relatos_secao.sql"

COLUNAS = [
    "id",
    "criado_em",
    "turno",
    "uf",
    "zona",
    "secao",
    "local_id",
    "secao_no_cadastro",
    "tipo",
    "texto",
    "hora_aproximada",
    "presenciou",
    "contato",
    "ip_hash",
    "user_agent",
    "origem",
    "versao",
    "status",
]
TIPOS = [
    "fila_longa",
    "urna_trocada",
    "biometria_falhou",
    "votou_sem_biometria",
    "mesario_conduta",
    "boca_de_urna",
    "transporte_irregular",
    "local_mudou",
    "secao_fechou_cedo",
    "secao_fechou_tarde",
    "outro",
]
STATUS = ["novo", "lido", "descartado"]


def token_cli() -> str:
    """Token de acesso do CLI do Supabase no keychain (prefixo go-keyring-base64)."""
    bruto = subprocess.run(
        ["security", "find-generic-password", "-s", "Supabase CLI", "-w"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    prefixo = "go-keyring-base64:"
    if bruto.startswith(prefixo):
        bruto = base64.b64decode(bruto[len(prefixo) :]).decode()
    if not bruto:
        raise RuntimeError(
            "token do CLI do Supabase ausente no keychain (rode supabase login)"
        )
    return bruto


def consultar(sql: str, token: str) -> list[dict]:
    corpo = json.dumps({"query": sql}).encode()
    req = urllib.request.Request(
        API,
        data=corpo,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "politize-se-relatos/1",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        # A mensagem do Postgres pode ecoar a linha; mostra só o código HTTP e o começo.
        raise RuntimeError(f"API de gestão respondeu HTTP {e.code}") from None


def sql_exportar(status: str | None = None, desde: int | None = None) -> str:
    filtros = []
    if status is not None:
        if status not in STATUS:
            raise ValueError(f"status inválido: {status}")
        filtros.append(f"status = '{status}'")
    if desde is not None:
        filtros.append(f"id > {int(desde)}")
    onde = f" where {' and '.join(filtros)}" if filtros else ""
    campos = ", ".join(
        (
            f"{c}::text as {c}"
            if c in {"tipo", "status", "criado_em", "hora_aproximada"}
            else c
        )
        for c in COLUNAS
    )
    return f"select {campos} from relato_secao{onde} order by id"


def sql_marcar(ids: list[int], status: str) -> str:
    if status not in STATUS:
        raise ValueError(f"status inválido: {status}")
    if not ids:
        raise ValueError("nenhum id")
    lista = ", ".join(str(int(i)) for i in ids)
    return (
        f"update relato_secao set status = '{status}' where id in ({lista}) "
        "returning id, status::text as status"
    )


def normalizar(linhas: list[dict]) -> list[dict]:
    """Confere o esquema de cada linha e devolve na ordem de COLUNAS."""
    saida = []
    for linha in linhas:
        faltam = set(COLUNAS) - set(linha)
        if faltam:
            raise ValueError(f"colunas ausentes: {sorted(faltam)}")
        if linha["tipo"] not in TIPOS or linha["status"] not in STATUS:
            raise ValueError(f"tipo ou status fora do esquema no relato {linha['id']}")
        hora = linha["hora_aproximada"]
        saida.append(
            {
                c: (hora[:5] if c == "hora_aproximada" and hora else linha[c])
                for c in COLUNAS
            }
        )
    return saida


def resumo(linhas: list[dict]) -> dict:
    return {
        "total": len(linhas),
        "por_status": dict(Counter(x["status"] for x in linhas)),
        "por_tipo": dict(Counter(x["tipo"] for x in linhas)),
        "por_uf": dict(Counter(x["uf"] for x in linhas)),
        "com_contato": sum(1 for x in linhas if x["contato"]),
        "fora_do_cadastro": sum(1 for x in linhas if not x["secao_no_cadastro"]),
    }


def gravar(
    linhas: list[dict],
    pasta: Path = SAIDA,
    agora: datetime | None = None,
    sufixo: str = "",
) -> tuple[Path, Path]:
    pasta.mkdir(parents=True, exist_ok=True)
    carimbo = (agora or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    nome = f"relatos_{carimbo}{f'_{sufixo}' if sufixo else ''}"
    js = pasta / f"{nome}.json"
    cs = pasta / f"{nome}.csv"
    js.write_text(
        json.dumps(
            {"exportado_em": carimbo, "resumo": resumo(linhas), "relatos": linhas},
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    with cs.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS, lineterminator="\n")
        w.writeheader()
        w.writerows(linhas)
    return js, cs
