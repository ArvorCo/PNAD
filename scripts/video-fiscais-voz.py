#!/usr/bin/env python3
"""Narração, efeitos e trilha do vídeo dos fiscais (video/fiscais), pela API do ElevenLabs.

Lê `video/fiscais/roteiro/roteiro.md` (um bloco `## id` por cena), gera cada cena na voz do
Leonardo (modelo eleven_v4, com `previous_text`/`next_text` para a prosódia emendar, como em
`apuracao/scripts/boletim-tts.py`) pelo endpoint com carimbo de tempo por caractere, e grava:

- `video/fiscais/public/voz/<id>.mp3`
- `video/fiscais/src/dados/voz.json`: cena, arquivo, duração em segundos (ffprobe), texto sem
  tags e palavras com início e fim, para as legendas.
- `video/fiscais/public/sfx/*.mp3`: efeitos curtos (sound-generation) e trilha instrumental
  (music), só quando o arquivo ainda não existe.

Chave e voz vêm de `~/arvor/voicer/.env`. Uso:
  python3 scripts/video-fiscais-voz.py            # tudo o que falta
  python3 scripts/video-fiscais-voz.py --so c-a   # regera uma cena
  python3 scripts/video-fiscais-voz.py --forcar   # regera todas as cenas
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIDEO = ROOT / "video" / "fiscais"
ROTEIRO = VIDEO / "roteiro" / "roteiro.md"
VOZ_DIR = VIDEO / "public" / "voz"
SFX_DIR = VIDEO / "public" / "sfx"
VOZ_JSON = VIDEO / "src" / "dados" / "voz.json"
ENV = Path.home() / "arvor" / "voicer" / ".env"

MODELO = "eleven_v4"
AJUSTES = {
    "stability": 0.4,
    "similarity_boost": 0.8,
    "style": 0.3,
    "use_speaker_boost": True,
}
PARALELO = 4
TAG = re.compile(r"\[[a-z ]+\]")

EFEITOS = {
    "whoosh": ("fast cinematic whoosh transition, clean, short", 0.9),
    "blip": ("short digital UI blip, soft synth click, clean", 0.5),
    "stamp": ("heavy stamp impact hit with short low thud, cinematic", 0.8),
    "scan": ("sci-fi radar scanner sweep, soft rising synth, short", 1.6),
    "chime": ("soft success chime, two notes, warm synth", 1.2),
}
TRILHA = (
    "Tense, modern, minimal electronic underscore for a civic data documentary; "
    "pulsing synth bass, soft electronic percussion, subtle strings, hopeful build, "
    "instrumental, no vocals, 110 bpm, loopable"
)
TRILHA_MS = 150_000


def ambiente() -> tuple[str, str]:
    chave = voz = ""
    for linha in ENV.read_text(encoding="utf-8").splitlines():
        if linha.startswith("ELEVENLABS_API_KEY="):
            chave = linha.split("=", 1)[1].strip().strip('"')
        elif linha.startswith("ELEVENLABS_VOICE_ID="):
            voz = linha.split("=", 1)[1].strip().strip('"')
    if not chave or not voz:
        raise SystemExit(f"ELEVENLABS_API_KEY ou ELEVENLABS_VOICE_ID ausentes em {ENV}")
    return chave, voz


def cenas(texto: str) -> list[tuple[str, str]]:
    """Blocos `## id` do roteiro, na ordem, com o texto cru (tags incluídas)."""
    saida: list[tuple[str, str]] = []
    atual: str | None = None
    corpo: list[str] = []
    for linha in texto.splitlines():
        if linha.startswith("## "):
            if atual:
                saida.append((atual, "\n".join(corpo).strip()))
            atual = linha[3:].strip()
            corpo = []
        elif atual is not None:
            corpo.append(linha)
    if atual:
        saida.append((atual, "\n".join(corpo).strip()))
    return saida


def limpar(texto: str) -> str:
    return re.sub(r"\s+", " ", TAG.sub("", texto)).strip()


def pedido(url: str, chave: str, corpo: dict) -> bytes:
    req = urllib.request.Request(
        url,
        data=json.dumps(corpo).encode(),
        headers={"xi-api-key": chave, "Content-Type": "application/json"},
    )
    return urllib.request.urlopen(req, timeout=600).read()


def palavras_do_alinhamento(alinhamento: dict) -> list[dict]:
    """Agrupa caracteres em palavras e descarta as tags entre colchetes."""
    chars = alinhamento["characters"]
    ini = alinhamento["character_start_times_seconds"]
    fim = alinhamento["character_end_times_seconds"]
    palavras: list[dict] = []
    atual = ""
    t0 = 0.0
    t1 = 0.0
    dentro_tag = False
    for c, a, b in zip(chars, ini, fim, strict=True):
        if c == "[":
            dentro_tag = True
        if dentro_tag:
            if c == "]":
                dentro_tag = False
            continue
        if c.isspace():
            if atual:
                palavras.append({"w": atual, "t": round(t0, 3), "f": round(t1, 3)})
                atual = ""
            continue
        if not atual:
            t0 = a
        atual += c
        t1 = b
    if atual:
        palavras.append({"w": atual, "t": round(t0, 3), "f": round(t1, 3)})
    return palavras


def gerar_cena(chave: str, voz: str, lista: list[tuple[str, str]], i: int) -> dict:
    cid, texto = lista[i]
    corpo = {
        "text": texto,
        "model_id": MODELO,
        "voice_settings": AJUSTES,
        "previous_text": lista[i - 1][1] if i > 0 else None,
        "next_text": lista[i + 1][1] if i + 1 < len(lista) else None,
    }
    corpo = {k: v for k, v in corpo.items() if v is not None}
    resposta = json.loads(
        pedido(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voz}/with-timestamps"
            "?output_format=mp3_44100_128",
            chave,
            corpo,
        )
    )
    destino = VOZ_DIR / f"{cid}.mp3"
    destino.write_bytes(base64.b64decode(resposta["audio_base64"]))
    palavras = palavras_do_alinhamento(resposta["alignment"])
    (VOZ_DIR / f"{cid}.palavras.json").write_text(
        json.dumps(palavras, ensure_ascii=False), encoding="utf-8"
    )
    print(f"  voz {cid}: {duracao(destino):.1f} s, {len(palavras)} palavras")
    return {"id": cid}


def duracao(arquivo: Path) -> float:
    saida = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(arquivo),
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return float(saida.strip())


def gerar_efeitos(chave: str) -> None:
    SFX_DIR.mkdir(parents=True, exist_ok=True)
    for nome, (prompt, segundos) in EFEITOS.items():
        destino = SFX_DIR / f"{nome}.mp3"
        if destino.exists():
            continue
        destino.write_bytes(
            pedido(
                "https://api.elevenlabs.io/v1/sound-generation",
                chave,
                {"text": prompt, "duration_seconds": segundos, "prompt_influence": 0.5},
            )
        )
        print(f"  sfx {nome}: {duracao(destino):.2f} s")
    trilha = SFX_DIR / "trilha.mp3"
    if not trilha.exists():
        trilha.write_bytes(
            pedido(
                "https://api.elevenlabs.io/v1/music",
                chave,
                {"prompt": TRILHA, "music_length_ms": TRILHA_MS},
            )
        )
        print(f"  trilha: {duracao(trilha):.1f} s")
    trilha_loop(trilha)


def trilha_loop(trilha: Path) -> None:
    """Versão da trilha para repetir: pula a introdução quase muda, normaliza o volume (-23 LUFS)
    e põe fade nas pontas, para o Remotion repetir sem salto."""
    destino = trilha.with_name("trilha_loop.mp3")
    if destino.exists():
        return
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-ss",
            "24",
            "-i",
            str(trilha),
            "-t",
            "126",
            "-af",
            "loudnorm=I=-23:TP=-2:LRA=9,afade=t=in:d=1.5,afade=t=out:st=124:d=2",
            str(destino),
        ],
        check=True,
    )
    print(f"  trilha_loop: {duracao(destino):.1f} s")


def manifesto(lista: list[tuple[str, str]]) -> None:
    cenas_json = []
    for cid, texto in lista:
        mp3 = VOZ_DIR / f"{cid}.mp3"
        alinhamento = VOZ_DIR / f"{cid}.palavras.json"
        if not alinhamento.exists():
            print(f"  (sem áudio ainda: {cid})")
            continue
        palavras = json.loads(alinhamento.read_text("utf-8"))
        cenas_json.append(
            {
                "id": cid,
                "arquivo": f"voz/{cid}.mp3",
                "segundos": round(duracao(mp3), 3),
                "texto": limpar(texto),
                "palavras": palavras,
            }
        )
    VOZ_JSON.parent.mkdir(parents=True, exist_ok=True)
    VOZ_JSON.write_text(
        json.dumps({"modelo": MODELO, "cenas": cenas_json}, ensure_ascii=False),
        encoding="utf-8",
    )
    total = sum(c["segundos"] for c in cenas_json)
    print(
        f"{VOZ_JSON.relative_to(ROOT)}: {len(cenas_json)} cenas, {total:.0f} s de narração"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n", 1)[0])
    parser.add_argument("--so", help="regera só esta cena")
    parser.add_argument("--forcar", action="store_true", help="regera todas as cenas")
    parser.add_argument("--sem-efeitos", action="store_true")
    args = parser.parse_args(argv)

    lista = cenas(ROTEIRO.read_text(encoding="utf-8"))
    if "—" in ROTEIRO.read_text(encoding="utf-8"):
        raise SystemExit("roteiro com travessão")
    chave, voz = ambiente()
    VOZ_DIR.mkdir(parents=True, exist_ok=True)

    pendentes = [
        i
        for i, (cid, _) in enumerate(lista)
        if args.forcar
        or (args.so and cid == args.so)
        or (not args.so and not (VOZ_DIR / f"{cid}.palavras.json").exists())
    ]
    with ThreadPoolExecutor(max_workers=PARALELO) as ex:
        list(ex.map(lambda i: gerar_cena(chave, voz, lista, i), pendentes))
    if not args.sem_efeitos:
        gerar_efeitos(chave)
    manifesto(lista)
    return 0


if __name__ == "__main__":
    sys.exit(main())
