#!/usr/bin/env python3
"""Capturas de tela do vídeo "A noite do 2º turno" (video/apuracao_2t).

Reaproveita o motor de `scripts/video-sete-riscos-capturas.py` (que por sua vez usa o da
masterclass: servidor local de `docs/` em 4173, Playwright, gravação webm convertida em mp4,
quadros parados conferidos por luminância), apontado para `video/apuracao_2t`. O roteiro fica em
`video/apuracao_2t/capturas/roteiro.json`. Três tipos de item, todos registrados em
`src/dados/capturas.json` com o esquema do contrato (`formatos`, `segundos`, `stills`):

- telão: quadros 1920x1080 do telão (`video/vinheta_2t/public/final/*.png`) copiados para
  `public/midia/cap_<id>_16x9.png`, com SHA-256 da origem. Só 16:9: a cena os mostra em moldura
  16:9 nos dois formatos, nunca recortados ao centro.
- páginas: quadro parado de uma página servida por `docs/` (o dossiê `apuracao_2T_2026.html`,
  a live `apuracao_2t_ao_vivo.html`), 16:9 e 9:16. Página ausente vira `falhou` no registro,
  nunca um quadro inventado.
- tomadas: gravações com o motor da masterclass (vazio por enquanto).

Uso:
    python3 scripts/video-apuracao-2t-capturas.py
    python3 scripts/video-apuracao-2t-capturas.py --so tela_pres
    python3 scripts/video-apuracao-2t-capturas.py --so-telao
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import shutil
import sys

from PIL import Image
from playwright.sync_api import sync_playwright

base = importlib.import_module("video-sete-riscos-capturas")
mc = base.mc

RAIZ = base.RAIZ
VIDEO = RAIZ / "video" / "apuracao_2t"
ROTEIRO = VIDEO / "capturas" / "roteiro.json"
BRUTO = VIDEO / "capturas" / "bruto"
MIDIA = VIDEO / "public" / "midia"
SAIDA_JSON = VIDEO / "src" / "dados" / "capturas.json"
TELAO = RAIZ / "video" / "vinheta_2t" / "public" / "final"
TAMANHO_TELAO = (1920, 1080)

base.MASTER = VIDEO
base.ROTEIRO = ROTEIRO
base.BRUTO = BRUTO
base.MIDIA = MIDIA
base.SAIDA_JSON = SAIDA_JSON
mc.MASTER = VIDEO
mc.ROTEIRO = ROTEIRO
mc.BRUTO = BRUTO
mc.MIDIA = MIDIA
mc.SAIDA_JSON = SAIDA_JSON


def copiar_telao(item: dict) -> dict:
    """Copia um quadro do telão e devolve a entrada de `capturas.json` (ou o motivo da falha)."""
    origem = TELAO / f"{item['quadro']}.png"
    entrada: dict = {
        "formatos": [],
        "segundos": 0,
        "stills": {},
        "tipo": "still",
        "origem": "telao",
    }
    if not origem.exists():
        entrada["falhou"] = f"quadro ausente: {origem.relative_to(RAIZ)}"
        return entrada
    with Image.open(origem) as im:
        if im.size != TAMANHO_TELAO:
            entrada["falhou"] = f"tamanho {im.size[0]}x{im.size[1]}, esperado 1920x1080"
            return entrada
    MIDIA.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(origem, MIDIA / f"cap_{item['id']}_16x9.png")
    entrada["formatos"] = ["16x9"]
    entrada["fonte"] = str(origem.relative_to(RAIZ))
    entrada["sha256"] = hashlib.sha256(origem.read_bytes()).hexdigest()
    return entrada


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    ap.add_argument("--so", action="append", help="id do item (repita para vários)")
    ap.add_argument(
        "--so-telao", action="store_true", help="só copia os quadros do telão"
    )
    ap.add_argument("--porta", type=int, default=4173)
    ap.add_argument("--manter-servidor", action="store_true")
    a = ap.parse_args()

    roteiro = json.loads(ROTEIRO.read_text(encoding="utf-8"))
    conhecidos = {i["id"] for g in ("telao", "paginas", "tomadas") for i in roteiro[g]}
    if a.so and not set(a.so) <= conhecidos:
        raise SystemExit(
            "Id desconhecido em --so: " + ", ".join(set(a.so) - conhecidos)
        )
    saida = {k: v for k, v in base.carregar_saida().items() if k in conhecidos}
    quer = (lambda i: i in a.so) if a.so else (lambda _i: True)

    for item in (i for i in roteiro["telao"] if quer(i["id"])):
        saida[item["id"]] = copiar_telao(item)
        e = saida[item["id"]]
        print(f"[telão] {item['id']}: {e.get('falhou') or 'ok'}")
    base.gravar_saida(saida)
    if a.so_telao:
        return 0

    stills = [p for p in roteiro["paginas"] if quer(p["id"])]
    tomadas = [t for t in roteiro["tomadas"] if quer(t["id"])]
    if stills or tomadas:
        with mc.servidor(a.porta, a.manter_servidor) as url, sync_playwright() as pw:
            for item in stills:
                saida[item["id"]] = base.capturar_still(pw, item, url, saida)
                base.gravar_saida(saida)
                e = saida[item["id"]]
                estado = (
                    "falhou (" + e["falhou"][:160] + ")"
                    if e.get("falhou")
                    else "/".join(e["formatos"])
                )
                print(f"[página] {item['id']}: {estado}")
            for linha in base.gravar_tomadas(pw, tomadas, url, saida):
                print(f"[tomada] {linha}")
    base.gravar_saida(saida)
    print(f"\n{SAIDA_JSON.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
