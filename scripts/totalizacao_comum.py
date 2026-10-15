"""Leitura das views publicas do Supabase da totalizacao paralela (chave publicavel, sem segredo)."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request

SUPABASE_URL = "https://brvjvizqbyfamtxogvqf.supabase.co"
CHAVE_PUBLICAVEL = "sb_publishable_OdrY6f2C-CdRzkorgyaudQ_taVWSIKw"
PAGINA = 1000


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
