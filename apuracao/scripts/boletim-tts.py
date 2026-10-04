#!/usr/bin/env python3
"""Gera o áudio de um boletim na voz do Leonardo pela API do ElevenLabs, parágrafo a parágrafo.

Uso: python3 scripts/boletim-tts.py data/boletins/HHMM.txt
Chave e voz vêm de ~/arvor/voicer/.env. Modelo eleven_v4 (tags de áudio entre colchetes; teste
objetivo de 04/10/2026: [whispers] baixa 7,6 dB sem alongar o áudio). Cada parágrafo vira um
pedido com previous_text/next_text para a prosódia emendar; os pedaços são concatenados pelo ffmpeg.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

MODELO = os.environ.get("BOLETIM_MODEL", "eleven_v4")
AJUSTES = {
    "stability": float(os.environ.get("BOLETIM_STABILITY", "0.4")),
    "similarity_boost": 0.8,
    "style": float(os.environ.get("BOLETIM_STYLE", "0.3")),
    "use_speaker_boost": True,
}
PARALELO = 4


def ambiente() -> tuple[str, str]:
    env = Path.home() / "arvor" / "voicer" / ".env"
    chave = voz = ""
    for linha in env.read_text(encoding="utf-8").splitlines():
        if linha.startswith("ELEVENLABS_API_KEY="):
            chave = linha.split("=", 1)[1].strip().strip('"')
        elif linha.startswith("ELEVENLABS_VOICE_ID="):
            voz = linha.split("=", 1)[1].strip().strip('"')
    if not chave or not voz:
        raise SystemExit(
            "ELEVENLABS_API_KEY ou ELEVENLABS_VOICE_ID ausentes em ~/arvor/voicer/.env"
        )
    return chave, voz


def paragrafos(texto: str) -> list[str]:
    blocos = [b.strip() for b in texto.split("\n\n") if b.strip()]
    saida: list[str] = []
    for b in blocos:
        # Junta blocos muito curtos ao anterior para a prosódia não picotar.
        if saida and len(b) < 120:
            saida[-1] = saida[-1] + "\n" + b
        else:
            saida.append(b)
    return saida


def gerar(chave: str, voz: str, partes: list[str], i: int, destino: Path) -> Path:
    corpo = {
        "text": partes[i],
        "model_id": MODELO,
        "voice_settings": AJUSTES,
        "previous_text": partes[i - 1] if i > 0 else None,
        "next_text": partes[i + 1] if i + 1 < len(partes) else None,
    }
    corpo = {k: v for k, v in corpo.items() if v is not None}
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voz}?output_format=mp3_44100_128",
        data=json.dumps(corpo).encode(),
        headers={"xi-api-key": chave, "Content-Type": "application/json"},
    )
    dados = urllib.request.urlopen(req, timeout=300).read()
    destino.write_bytes(dados)
    return destino


def main() -> None:
    txt = Path(sys.argv[1])
    mp3 = txt.with_suffix(".mp3")
    chave, voz = ambiente()
    partes = paragrafos(txt.read_text(encoding="utf-8"))
    pasta = txt.parent / "partes"
    pasta.mkdir(exist_ok=True)
    arquivos = [pasta / f"{txt.stem}-{i:02d}.mp3" for i in range(len(partes))]
    with ThreadPoolExecutor(max_workers=PARALELO) as ex:
        list(
            ex.map(
                lambda i: gerar(chave, voz, partes, i, arquivos[i]), range(len(partes))
            )
        )
    lista = pasta / f"{txt.stem}.txt"
    lista.write_text(
        "".join(f"file '{a.resolve()}'\n" for a in arquivos), encoding="utf-8"
    )
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(lista),
            "-c",
            "copy",
            str(mp3),
        ],
        check=True,
    )
    dur = subprocess.run(
        ["afinfo", str(mp3)], capture_output=True, text=True, check=True
    ).stdout
    segundos = next(
        (
            linha.split(":")[1].strip()
            for linha in dur.splitlines()
            if "estimated duration" in linha
        ),
        "?",
    )
    print(
        f"{mp3}: {len(partes)} partes, {sum(len(p) for p in partes)} caracteres, {segundos} s, modelo {MODELO}"
    )


if __name__ == "__main__":
    main()
