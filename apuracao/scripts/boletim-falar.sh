#!/usr/bin/env bash
# Fala um boletim com a voz do Leonardo (ElevenLabs via sag) e guarda o mp3 ao lado do texto.
# Uso: scripts/boletim-falar.sh data/boletins/HHMM.txt   (chave e voz vêm de ~/arvor/voicer/.env)
# O sag gera o arquivo sem tocar (o player interno dele trava ao fim); quem toca é o afplay.
set -euo pipefail
TXT="$1"; MP3="${TXT%.txt}.mp3"
set -a; . "$HOME/arvor/voicer/.env"; set +a
sag speak -f "$TXT" --model-id "${BOLETIM_MODEL:-eleven_multilingual_v2}" --lang pt --normalize auto \
  --stability 0.5 --similarity 0.8 --speed 1.02 -o "$MP3" --play=false --metrics
afinfo "$MP3" | grep -i "estimated duration"
afplay "$MP3"
