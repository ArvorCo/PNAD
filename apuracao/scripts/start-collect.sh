#!/usr/bin/env bash
# Liga o coletor sem deixar o Mac dormir e o reinicia se cair. Log JSON em data/logs/.
set -u
cd "$(dirname "$0")/.." || exit 1
mkdir -p data/logs
LOG="data/logs/collect-$(date +%Y%m%d).log"
echo "coletor: log em $LOG"
exec caffeinate -dimsu bash -c "until bun run collect >> '$LOG' 2>&1; do echo \"{\\\"t\\\":\\\"reinicio\\\",\\\"em\\\":\\\"\$(date -u +%Y-%m-%dT%H:%M:%SZ)\\\"}\" >> '$LOG'; sleep 2; done"
