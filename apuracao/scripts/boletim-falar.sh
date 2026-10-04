#!/usr/bin/env bash
# Gera (ElevenLabs v4, por parágrafo, API direta) e toca um boletim na voz do Leonardo.
# Uso: scripts/boletim-falar.sh data/boletins/HHMM.txt
set -euo pipefail
TXT="$1"; MP3="${TXT%.txt}.mp3"
python3 "$(dirname "$0")/boletim-tts.py" "$TXT"
afplay "$MP3"
