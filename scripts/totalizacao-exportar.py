#!/usr/bin/env python3
"""Exporta os agregados e o CSV de reproducao da totalizacao paralela por QR do BU.

Le somente as views publicas do Supabase com a chave publicavel (nenhum segredo), grava JSON
para o painel e CSV com todos os BUs aceitos (conteudo, assinatura e certificado), reconfere a
cadeia de hashes e escreve um manifesto com SHA-256 de cada arquivo.

Uso: python3 scripts/totalizacao-exportar.py [--saida docs/assets/totalizacao_dados]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SUPABASE_URL = "https://brvjvizqbyfamtxogvqf.supabase.co"
CHAVE_PUBLICAVEL = "sb_publishable_OdrY6f2C-CdRzkorgyaudQ_taVWSIKw"
PAGINA = 1000
RAIZ = Path(__file__).resolve().parents[1]
SAIDA_PADRAO = RAIZ / "docs" / "assets" / "totalizacao_dados"


def consultar(view: str, params: dict[str, str] | None = None) -> list[dict]:
    """Le uma view inteira pelo PostgREST, paginando por Range."""
    linhas: list[dict] = []
    inicio = 0
    query = urllib.parse.urlencode(params or {})
    while True:
        url = f"{SUPABASE_URL}/rest/v1/{view}" + (f"?{query}" if query else "")
        req = urllib.request.Request(
            url,
            headers={
                "apikey": CHAVE_PUBLICAVEL,
                "Authorization": f"Bearer {CHAVE_PUBLICAVEL}",
                "Range-Unit": "items",
                "Range": f"{inicio}-{inicio + PAGINA - 1}",
                "Prefer": "count=exact",
            },
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            lote = json.loads(resp.read())
            faixa = resp.headers.get("Content-Range", "")
        linhas.extend(lote)
        total = (
            int(faixa.rsplit("/", 1)[-1])
            if "/" in faixa and not faixa.endswith("*")
            else None
        )
        if len(lote) < PAGINA or (total is not None and len(linhas) >= total):
            return linhas
        inicio += PAGINA


def conferir_cadeia(bus: list[dict]) -> dict:
    """Recalcula cadeia_n = sha256(cadeia_(n-1) || hash_final || assi) na ordem de id."""
    anterior = ""
    quebras: list[int] = []
    for b in sorted(bus, key=lambda x: x["id"]):
        esperado = hashlib.sha256(
            (anterior + b["hash_final"] + b["assi"]).encode()
        ).hexdigest()
        if b["cadeia"] != esperado or (b["cadeia_anterior"] or "") != anterior:
            quebras.append(b["id"])
        anterior = b["cadeia"]
    return {
        "bus": len(bus),
        "cadeia_integra": not quebras,
        "quebras": quebras,
        "ultimo_elo": anterior or None,
    }


def gravar_json(caminho: Path, dado: object) -> None:
    caminho.write_text(
        json.dumps(dado, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )


def gravar_csv(caminho: Path, linhas: list[dict], colunas: list[str]) -> None:
    with caminho.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f, fieldnames=colunas, extrasaction="ignore", lineterminator="\n"
        )
        w.writeheader()
        for linha in linhas:
            w.writerow(linha)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    args = ap.parse_args()
    saida: Path = args.saida
    saida.mkdir(parents=True, exist_ok=True)
    agora = datetime.now(timezone.utc).isoformat(timespec="seconds")

    agregados = {
        "totais_br": consultar("v_totais_br", {"order": "candidato"}),
        "totais_uf": consultar("v_totais_uf", {"order": "uf,cargo,candidato"}),
        "totais_muni": consultar("v_totais_muni", {"order": "uf,muni,cargo,candidato"}),
        "resumo_cargo_uf": consultar("v_resumo_cargo_uf", {"order": "uf,cargo"}),
        "cobertura_uf": consultar("v_cobertura_uf", {"order": "uf"}),
        "cobertura_muni": consultar("v_cobertura_muni", {"order": "uf,muni"}),
        "conflitos": consultar("v_conflito", {"order": "uf,muni,zona,secao"}),
        "estatisticas": consultar("v_estatisticas"),
    }
    for nome, dado in agregados.items():
        gravar_json(
            saida / f"{nome}.json",
            {"gerado_em": agora, "fonte": "Supabase, views publicas", "linhas": dado},
        )

    bus = consultar("v_bu_publico", {"order": "id"})
    votos = consultar("v_bu_voto_publico", {"order": "bu_id,idel,cargo,candidato"})
    cargos = consultar("v_bu_cargo_publico", {"order": "bu_id,idel,cargo"})
    envios = consultar("v_envio_publico", {"order": "id"})
    cadeia = conferir_cadeia(bus)

    gravar_csv(
        saida / "bus.csv",
        bus,
        [
            "id",
            "recebido_em",
            "uf",
            "muni",
            "zona",
            "secao",
            "agre",
            "orig",
            "turno",
            "pleito",
            "proc",
            "fase",
            "dtpl",
            "idue",
            "mdue",
            "vers",
            "aptos",
            "comparecimento",
            "faltosos",
            "dtfc",
            "hrfc",
            "hash_final",
            "assi",
            "algoritmo",
            "cert_hex",
            "cert_fingerprint",
            "cert_subject",
            "cert_issuer",
            "conteudo",
            "cadeia_anterior",
            "cadeia",
        ],
    )
    gravar_csv(
        saida / "votos.csv",
        votos,
        ["bu_id", "idel", "cargo", "partido", "candidato", "votos"],
    )
    gravar_csv(
        saida / "cargos.csv",
        cargos,
        [
            "bu_id",
            "idel",
            "cargo",
            "tipo",
            "apta",
            "nomi",
            "legc",
            "bran",
            "nulo",
            "totc",
        ],
    )
    gravar_csv(
        saida / "envios.csv",
        envios,
        ["id", "recebido_em", "status", "motivo", "bu_id", "versao_motor"],
    )

    arquivos = sorted(
        p.name
        for p in saida.iterdir()
        if p.suffix in {".json", ".csv"} and p.name != "manifest.json"
    )
    manifesto = {
        "gerado_em": agora,
        "cadeia": cadeia,
        "arquivos": {
            n: {
                "sha256": hashlib.sha256((saida / n).read_bytes()).hexdigest(),
                "bytes": (saida / n).stat().st_size,
            }
            for n in arquivos
        },
        "como_reproduzir": "Some votos.csv por candidato dentro dos BUs de bus.csv cuja secao tem um unico hash_final e fase O; "
        "reverifique cada BU com totalizacao/ (lerBoletim) a partir de conteudo, assi e cert_hex.",
    }
    gravar_json(saida / "manifest.json", manifesto)
    print(
        json.dumps(
            {
                "bus": len(bus),
                "votos": len(votos),
                "envios": len(envios),
                "cadeia_integra": cadeia["cadeia_integra"],
                "saida": str(saida),
            },
            ensure_ascii=False,
        )
    )
    return 0 if cadeia["cadeia_integra"] else 2


if __name__ == "__main__":
    sys.exit(main())
