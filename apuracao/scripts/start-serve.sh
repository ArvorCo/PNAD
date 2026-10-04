#!/usr/bin/env bash
# Liga o servidor do telão (leitor do SQLite) e o reinicia se cair.
set -u
cd "$(dirname "$0")/.." || exit 1
mkdir -p data/logs
LOG="data/logs/serve-$(date +%Y%m%d).log"
echo "servidor: log em $LOG"
exec bash -c "until bun run serve >> '$LOG' 2>&1; do sleep 2; done"
