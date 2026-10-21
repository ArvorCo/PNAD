#!/usr/bin/env python3
"""Narração, efeitos e música por capítulo do vídeo "Sete riscos, um fiscal" (video/sete_riscos).

Usa o núcleo `scripts/video_voz.py` (o mesmo da masterclass) e grava, conforme
`video/sete_riscos/CONTRATO.md`, seção 6:

- `public/voz/<id>.mp3`, `public/voz/<id>.palavras.json` e `src/dados/voz.json`;
- `public/sfx/<nome>.mp3`: o catálogo de efeitos abaixo, só os que ainda não existem;
- `public/musica/<capitulo>.mp3`: uma faixa instrumental por capítulo (`/v1/music`), com a
  extensão do capítulo medida em `voz.json` (mais 12 s de folga), normalizada a -23 LUFS, e
  `src/dados/musica.json`. A música exige `voz.json`: rode a narração antes.

Antes de gastar uma chamada, confere que os blocos `## id` do roteiro são a `ORDEM` de
`src/ordem.ts`. Chave e voz vêm de `~/arvor/voicer/.env` e nunca são impressas. Uso:
  python3 scripts/video-sete-riscos-voz.py                # tudo o que falta
  python3 scripts/video-sete-riscos-voz.py --so tese      # regera uma cena
  python3 scripts/video-sete-riscos-voz.py --so-musica    # só a música por capítulo
  python3 scripts/video-sete-riscos-voz.py --forcar       # regera cenas e música
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
import urllib.error
from concurrent.futures import ThreadPoolExecutor
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

PROJETO = Projeto.padrao(ROOT / "video" / "sete_riscos")
ORDEM_TS = PROJETO.raiz / "src" / "ordem.ts"

# Mesmas pausas de `src/plano.ts`: respiro depois de cada cena e cauda depois da última.
RESPIRO = 0.9
CAUDA = 3.0
FOLGA_MS = 12_000
MUSICA_MIN_MS = 3_000
MUSICA_MAX_MS = 600_000
LOUDNORM = "loudnorm=I=-23:TP=-1.5:LRA=11"
PARALELO_MUSICA = 2
PAUSA_429 = 90
TENTATIVAS_429 = 6

EFEITOS = {
    "whoosh": ("fast cinematic whoosh transition, clean, short", 0.9),
    "blip": ("short digital UI blip, soft synth click, clean", 0.5),
    "stamp": ("heavy stamp impact hit with short low thud, cinematic", 0.8),
    "scan": ("sci-fi radar scanner sweep, soft rising synth, short", 1.6),
    "chime": ("soft success chime, two notes, warm synth", 1.2),
    "concha": (
        "metal ladle dipping into a pot of thick soup, gentle liquid slosh and pour, "
        "close-up kitchen foley, no music",
        1.6,
    ),
    "fervura": (
        "soup simmering in a pot on a stove, soft continuous bubbling, warm kitchen "
        "ambience, seamless loop, no music, no voices",
        6.0,
    ),
    "impressora": (
        "small thermal receipt printer printing a long paper slip, fast mechanical whir "
        "and paper feed, ends with a soft tear, no music",
        2.5,
    ),
    "carimbo": (
        "rubber stamp pressed firmly onto paper on a wooden desk, crisp short thump, "
        "close foley, no music",
        0.7,
    ),
    "qr": (
        "short electronic scanner beep confirming a successful code read, clean single tone",
        0.5,
    ),
    "zoom": (
        "digital zoom into a map interface, short smooth rising synth swoosh ending in a "
        "soft click, clean user interface sound",
        0.9,
    ),
    "tique": ("single mechanical clock tick, crisp and dry, close up", 0.5),
    "alerta": (
        "soft gentle notification alert, two descending warm synth tones, calm, not alarming",
        0.9,
    ),
    "papel": (
        "paper documents being flipped and shuffled on a desk, close foley, no music",
        1.2,
    ),
    "fila": (
        "indoor murmur of a calm queue of people waiting in a school hallway, indistinct "
        "quiet chatter with no clear words, soft footsteps, seamless loop, no music",
        6.0,
    ),
    "riser": (
        "short cinematic riser, swelling airy synth and reversed cymbal building tension, "
        "ends abruptly",
        2.0,
    ),
    "teclado": (
        "generic electronic keypad on a voting machine: a few soft button presses with short "
        "confirmation beeps, clean, no voices",
        1.5,
    ),
    "sirene_longe": (
        "distant police siren passing far away in a city at night, faint, no music",
        2.0,
    ),
    "passos": (
        "footsteps walking down a quiet school corridor, close foley, no music",
        2.0,
    ),
    "caneta": (
        "ballpoint pen writing quickly on a paper form on a desk, close foley",
        1.0,
    ),
}

_COMUM = (
    "Cinematic documentary underscore, instrumental only, no vocals, no lyrics, no choir; "
    "sparse arrangement mixed to sit under spoken narration; steady tempo, no sudden drops."
)
MUSICA = {
    "abertura": (
        "Warm and attentive opening: soft piano motif, warm legato strings, light hand "
        "percussion, a quiet sense of civic duty and hope, 102 bpm. "
    ),
    "lei": (
        "Calm and orderly: piano chords over a light steady pulse, warm cello line, clear "
        "and reassuring, like reading a rulebook with confidence, 100 bpm. "
    ),
    "riscos": (
        "Restrained suspense: low drones and sub bass, dry clock-like percussion, sparse "
        "piano notes, careful tension without drama or horror, 98 bpm. "
    ),
    "fechamento": (
        "Warm resolution at dusk: piano and strings opening up, soft brass pads, gentle "
        "drums, a feeling of a long day ending well, 104 bpm. "
    ),
    "mapa": (
        "Bright electronic pulse: clean plucked synths, steady electronic beat, airy pads, "
        "optimistic and precise, like a map drawing itself, 115 bpm. "
    ),
    "fecho": (
        "Resolute finale: full warm strings, piano and steady drums, confident and "
        "determined, building to a calm, firm resolution, 106 bpm. "
    ),
}


def ordem() -> list[tuple[str, str]]:
    """Pares (cena, capítulo) de `ORDEM` em `src/ordem.ts`, na ordem do vídeo."""
    if not ORDEM_TS.exists():
        raise SystemExit(f"ordem ausente: {ORDEM_TS.relative_to(ROOT)}")
    texto = ORDEM_TS.read_text(encoding="utf-8")
    bloco = texto.split("export const ORDEM", 1)[-1]
    pares = re.findall(r'\{\s*id:\s*"([^"]+)",\s*capitulo:\s*"([^"]+)"\s*\}', bloco)
    if not pares:
        raise SystemExit(f"nenhuma cena em ORDEM de {ORDEM_TS.relative_to(ROOT)}")
    return pares


def conferir_roteiro(lista: list[tuple[str, str]]) -> None:
    roteiro = [cid for cid, _ in lista]
    esperado = [cid for cid, _ in ordem()]
    if roteiro != esperado:
        faltam = [c for c in esperado if c not in roteiro]
        sobram = [c for c in roteiro if c not in esperado]
        raise SystemExit(
            f"roteiro fora da ORDEM de src/ordem.ts (faltam {faltam}, sobram {sobram}, "
            "ou a ordem difere)"
        )


def extensao_capitulos() -> dict[str, float]:
    """Segundos de cada capítulo no vídeo: narração mais respiro, cauda na última cena."""
    if not PROJETO.voz_json.exists():
        raise SystemExit(
            f"a música exige {PROJETO.voz_json.relative_to(ROOT)}: rode a narração antes"
        )
    voz = json.loads(PROJETO.voz_json.read_text(encoding="utf-8"))
    segundos = {c["id"]: c["segundos"] for c in voz["cenas"]}
    pares = ordem()
    faltam = [cid for cid, _ in pares if cid not in segundos]
    if faltam:
        raise SystemExit(f"voz.json sem as cenas {faltam}: rode a narração antes")
    extensao: dict[str, float] = {}
    for i, (cid, cap) in enumerate(pares):
        pausa = CAUDA if i == len(pares) - 1 else RESPIRO
        extensao[cap] = extensao.get(cap, 0.0) + segundos[cid] + pausa
    return extensao


def normalizar(bruto: Path, destino: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(bruto),
            "-af",
            LOUDNORM,
            "-ar",
            "44100",
            "-c:a",
            "libmp3lame",
            "-b:a",
            "192k",
            str(destino),
        ],
        check=True,
    )


def musica_com_espera(chave: str, destino: Path, corpo: dict) -> None:
    """`/v1/music` devolve 429 em rajada; espera e tenta de novo, como na masterclass."""
    for tentativa in range(TENTATIVAS_429):
        try:
            musica(chave, destino, corpo)
            return
        except urllib.error.HTTPError as erro:
            if erro.code != 429 or tentativa == TENTATIVAS_429 - 1:
                raise
            print(f"  música: 429, esperando {PAUSA_429} s ({tentativa + 1})")
            time.sleep(PAUSA_429)


def faixa(chave: str, cap: str, ms: int, forcar: bool) -> dict:
    """Gera (ou reaproveita) a faixa do capítulo e devolve a entrada de `musica.json`."""
    prompt = MUSICA[cap] + _COMUM
    destino = PROJETO.musica_dir / f"{cap}.mp3"
    bruto = PROJETO.musica_dir / f"{cap}.bruto.mp3"
    if forcar or not destino.exists():
        if forcar or not bruto.exists():
            corpo = {
                "prompt": prompt,
                "music_length_ms": ms,
                "force_instrumental": True,
            }
            musica_com_espera(chave, bruto, corpo)
        normalizar(bruto, destino)
        bruto.unlink()
        print(f"  música {cap}: {duracao(destino):.1f} s")
    segundos = round(duracao(destino), 3)
    if segundos * 1000 < ms - FOLGA_MS:
        print(f"  aviso: música {cap} ({segundos:.0f} s) é mais curta que o capítulo")
    return {
        "arquivo": f"musica/{cap}.mp3",
        "segundos": segundos,
        "prompt": prompt,
        "alvo_segundos": ms / 1000,
    }


def gerar_musica(chave: str, forcar: bool) -> None:
    extensao = extensao_capitulos()
    alvos = {
        cap: min(MUSICA_MAX_MS, max(MUSICA_MIN_MS, round(seg * 1000) + FOLGA_MS))
        for cap, seg in extensao.items()
    }
    faltam = [cap for cap in alvos if cap not in MUSICA]
    if faltam:
        raise SystemExit(f"capítulos sem prompt de música: {faltam}")
    PROJETO.musica_dir.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=PARALELO_MUSICA) as ex:
        entradas = dict(
            zip(
                alvos,
                ex.map(lambda cap: faixa(chave, cap, alvos[cap], forcar), alvos),
                strict=True,
            )
        )
    PROJETO.musica_json.parent.mkdir(parents=True, exist_ok=True)
    PROJETO.musica_json.write_text(
        json.dumps(entradas, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    total = sum(e["segundos"] for e in entradas.values())
    print(
        f"{PROJETO.musica_json.relative_to(ROOT)}: {len(entradas)} faixas, "
        f"{total:.0f} s de música"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argumentos((__doc__ or "").split("\n", 1)[0])
    parser.add_argument(
        "--so-musica", action="store_true", help="só a música (exige voz.json)"
    )
    parser.add_argument("--sem-musica", action="store_true")
    args = parser.parse_args(argv)
    if args.so_musica and args.sem_musica:
        parser.error("--so-musica e --sem-musica se excluem")

    if args.so_musica:
        extensao_capitulos()
        chave, _ = ambiente()
    else:
        lista = ler_roteiro(PROJETO)
        conferir_roteiro(lista)
        chave, voz = ambiente()
        narrar(PROJETO, chave, voz, lista, so=args.so, forcar=args.forcar)
        if not args.sem_efeitos:
            efeitos(PROJETO, chave, EFEITOS)
        manifesto(PROJETO, lista)
    if not args.sem_musica:
        gerar_musica(chave, forcar=args.forcar)
    return 0


if __name__ == "__main__":
    sys.exit(main())
