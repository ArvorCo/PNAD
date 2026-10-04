#!/usr/bin/env bash
# Fala um boletim com a voz do Leonardo (ElevenLabs via sag) e guarda o mp3 ao lado do texto.
# Uso: scripts/boletim-falar.sh data/boletins/HHMM.txt   (chave e voz vêm de ~/arvor/voicer/.env)
# O texto é um roteiro ElevenLabs: tags de áudio em inglês entre colchetes ([pause], [serious]...),
# reticências para pausas curtas, CAIXA ALTA para ênfase. Modelo padrão eleven_v4 (clones profissionais);
# BOLETIM_MODEL=eleven_v3 troca. Estabilidade 0.4 para as tags terem efeito (acima de 0.8 são achatadas).
# O sag gera o arquivo sem tocar (o player interno dele trava ao fim); quem toca é o afplay.
set -euo pipefail
TXT="$1"; MP3="${TXT%.txt}.mp3"
set -a; . "$HOME/arvor/voicer/.env"; set +a
sag speak -f "$TXT" --model-id "${BOLETIM_MODEL:-eleven_v4}" --lang pt \
  --stability "${BOLETIM_STABILITY:-0.4}" --similarity 0.8 --style "${BOLETIM_STYLE:-0.3}" \
  -o "$MP3" --play=false --metrics
afinfo "$MP3" | grep -i "estimated duration"
afplay "$MP3"
