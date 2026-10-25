#!/usr/bin/env bash
# Reserva do boletim falado: toca um boletim pronto pelo afplay no desktop, como no 1º turno.
# Uso: scripts/boletim-tocar.sh HHMM   (sem argumento, o mais recente pronto)
set -euo pipefail
cd "$(dirname "$0")/.." || exit 1
DIR="${APURACAO_BOLETIM_DIR:-data/boletins-2t}"
ID="${1:-}"
if [ -z "$ID" ]; then
  ID=$(ls -t "$DIR"/*.mp3 2>/dev/null | head -1 | xargs -n1 basename | sed 's/\.mp3$//')
fi
MP3="$DIR/$ID.mp3"
[ -f "$MP3" ] || { echo "não achei $MP3"; exit 1; }
echo "tocando $MP3 ($(ffprobe -v error -show_entries format=duration -of csv=p=0 "$MP3" | cut -d. -f1) s)"
afplay "$MP3"
