#!/usr/bin/env bash
# Encadeamento da fase 2 depois que a coleta completa dos BUs do 2º turno termina.
# 1. repete seções com erro e revisita as que ficaram sem BU;
# 2. inicia a coleta compacta dos logs das urnas do 2º turno (em segundo plano, nohup);
# 3. reexecuta as análises que dependem do banco completo de BUs.
# Uso: bash apuracao/scripts/fase2-pos-coleta.sh  (a partir da raiz do projeto ou de apuracao/)
set -euo pipefail
RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
AP="$RAIZ/apuracao"
LOG="$AP/data/logs/fase2-$(date +%Y%m%d-%H%M).log"
mkdir -p "$AP/data/logs"
exec > >(tee -a "$LOG") 2>&1
echo "== fase 2, início $(date '+%d/%m %H:%M')"

cd "$AP"
if [ -f data/secoes-p003221.pid ] && kill -0 "$(cat data/secoes-p003221.pid)" 2>/dev/null; then
  echo "coleta de BUs ainda viva; abortando"; exit 1
fi
echo "== refazer erros e revisitar"
APURACAO_PLEITO=003221 bun run scripts/secoes-coletar.ts --rps 60 --concorrencia 24 --refazer-erros || true
APURACAO_PLEITO=003221 bun run scripts/secoes-coletar.ts --rps 60 --concorrencia 24 --revisitar || true
APURACAO_PLEITO=003221 bun run scripts/secoes-coletar.ts --so-conferir || true
echo "== RDV: conferir seções cujo BU chegou depois"
bun run scripts/rdv-coletar.ts --so-conferir || true

cd "$RAIZ"
echo "== coleta dos logs do 2º turno (segundo plano)"
nohup python3 scripts/apuracao-2026-logs-coletar.py --pleito 3221 \
  --origem apuracao/data/secoes_2t_2026.sqlite --db data/raw/tse_logs_2026/logs_2t.sqlite \
  --guardar compacto --rps 30 --workers 16 > "$AP/data/logs/logs-2t-coleta.log" 2>&1 &
echo "logs: pid $!"

echo "== análises sobre o banco completo"
python3 scripts/apuracao-2t-2026-secoes.py --fonte completo
python3 scripts/abstencao-lula-secoes.py --turno 2 --eixo comparecimento
python3 scripts/abstencao-lula-secoes.py --turno 2 --eixo abstencao
python3 scripts/apuracao-2t-2026-urnas.py
python3 scripts/apuracao-2t-2026-rdv.py || true
python3 scripts/apuracao-2t-2026-transferencia.py || true
python3 scripts/politize-se-build.py
python3 scripts/politize-se-mapa-build.py
python3 scripts/social-cards.py --only politizese
python3 scripts/apuracao-2t-2026-build.py
echo "== fase 2, fim $(date '+%d/%m %H:%M')"
