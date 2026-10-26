#!/usr/bin/env python3
"""Narração, efeitos e música por capítulo do vídeo "A noite do 2º turno" (video/apuracao_2t).

Wrapper fino de `scripts/video-sete-riscos-voz.py` (que usa o núcleo `scripts/video_voz.py`):
importa o módulo, aponta `PROJETO` e `ORDEM_TS` para `video/apuracao_2t` e troca o catálogo de
efeitos e os prompts de música pelos deste vídeo. Todo o resto (conferência do roteiro contra
`src/ordem.ts`, narração v4 com carimbo por palavra, normalização a -23 LUFS, espera no 429 da
música) é o mesmo código, sem cópia. Grava, conforme `video/apuracao_2t/CONTRATO.md`:

- `public/voz/<id>.mp3`, `public/voz/<id>.palavras.json` e `src/dados/voz.json`;
- `public/sfx/<nome>.mp3`: só os efeitos abaixo que ainda não existem;
- `public/musica/<capitulo>.mp3` e `src/dados/musica.json`: uma faixa instrumental por capítulo,
  com a extensão do capítulo medida em `voz.json`. A música exige `voz.json`: rode a narração antes.

Chave e voz vêm de `~/arvor/voicer/.env` e nunca são impressas. Uso:
  python3 scripts/video-apuracao-2t-voz.py                # tudo o que falta
  python3 scripts/video-apuracao-2t-voz.py --so tese      # regera uma cena
  python3 scripts/video-apuracao-2t-voz.py --so-musica    # só a música por capítulo
  python3 scripts/video-apuracao-2t-voz.py --forcar       # regera cenas e música
"""

from __future__ import annotations

import importlib
import sys

from video_voz import ROOT, Projeto

base = importlib.import_module("video-sete-riscos-voz")

PROJETO = Projeto.padrao(ROOT / "video" / "apuracao_2t")

EFEITOS = {
    "whoosh": ("fast cinematic whoosh transition, clean, short", 0.9),
    "blip": ("short digital UI blip, soft synth click, clean", 0.5),
    "stamp": ("heavy stamp impact hit with short low thud, cinematic", 0.8),
    "scan": ("sci-fi radar scanner sweep, soft rising synth, short", 1.6),
    "chime": ("soft success chime, two notes, warm synth", 1.2),
    "tique": ("single mechanical clock tick, crisp and dry, close up", 0.5),
    "alerta": (
        "soft gentle notification alert, two descending warm synth tones, calm, not alarming",
        0.9,
    ),
    "papel": (
        "paper documents being flipped and shuffled on a desk, close foley, no music",
        1.2,
    ),
    "riser": (
        "short cinematic riser, swelling airy synth and reversed cymbal building tension, "
        "ends abruptly",
        2.0,
    ),
    "zoom": (
        "digital zoom into a map interface, short smooth rising synth swoosh ending in a "
        "soft click, clean user interface sound",
        0.9,
    ),
    "qr": (
        "short electronic scanner beep confirming a successful code read, clean single tone",
        0.5,
    ),
}

MUSICA = {
    "abertura": (
        "Tense and attentive election-night opening: low sustained strings, soft piano "
        "motif, a quiet pulse like a clock counting, 96 bpm. "
    ),
    "noite": (
        "Election-night newsroom underscore: steady electronic pulse, muted bass, sparse "
        "piano, rising attention without drama, a long wait that turns into movement, 100 bpm. "
    ),
    "projecao": (
        "Analytical and precise: clean plucked synths, light steady beat, airy pads, the "
        "feeling of a model converging on an answer, 108 bpm. "
    ),
    "turnos": (
        "Reflective comparison: piano and warm cello trading a two-note motif, gentle "
        "hand percussion, balanced and fair, 98 bpm. "
    ),
    "secoes": (
        "Careful forensic detail: dry clock-like percussion, low drones, sparse piano "
        "notes, patient scrutiny without horror, 96 bpm. "
    ),
    "pesquisas": (
        "Measured and curious: soft marimba and pizzicato strings, light brushed drums, "
        "the tone of checking a forecast against the result, 104 bpm. "
    ),
    "urnas": (
        "Careful forensic verification turning into calm confidence: dry ticking percussion, "
        "low warm pads, clean plucked synths, steady and precise, nothing alarming, 100 bpm. "
    ),
    "fecho": (
        "Resolute finale: full warm strings, piano and steady drums, confident and calm, "
        "resolving to a firm, quiet ending, 104 bpm. "
    ),
}


base.PROJETO = PROJETO
base.ORDEM_TS = PROJETO.raiz / "src" / "ordem.ts"
base.EFEITOS = EFEITOS
base.MUSICA = MUSICA
base.__doc__ = __doc__

if __name__ == "__main__":
    sys.exit(base.main())
