#!/usr/bin/env python3
"""Narração, efeitos e trilha do vídeo dos fiscais (video/fiscais), pela API do ElevenLabs.

Lê `video/fiscais/roteiro/roteiro.md` (um bloco `## id` por cena) e grava, pelo núcleo
`scripts/video_voz.py`:

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

import subprocess
import sys
from pathlib import Path

from video_voz import (
    ROOT,
    Projeto,
    ambiente,
    argumentos,
    duracao,
    efeitos,
    ler_roteiro,
    manifesto,
    musica,
    narrar,
)

PROJETO = Projeto.padrao(ROOT / "video" / "fiscais")

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


def gerar_efeitos(chave: str) -> None:
    efeitos(PROJETO, chave, EFEITOS)
    trilha = PROJETO.sfx_dir / "trilha.mp3"
    if not trilha.exists():
        musica(chave, trilha, {"prompt": TRILHA, "music_length_ms": TRILHA_MS})
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


def main(argv: list[str] | None = None) -> int:
    args = argumentos((__doc__ or "").split("\n", 1)[0]).parse_args(argv)
    lista = ler_roteiro(PROJETO)
    chave, voz = ambiente()
    narrar(PROJETO, chave, voz, lista, so=args.so, forcar=args.forcar)
    if not args.sem_efeitos:
        gerar_efeitos(chave)
    manifesto(PROJETO, lista)
    return 0


if __name__ == "__main__":
    sys.exit(main())
