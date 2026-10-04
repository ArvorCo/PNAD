#!/usr/bin/env bash
# Liga o coletor sem deixar o Mac dormir e o reinicia se cair. Log JSON em data/logs/.
set -u
cd "$(dirname "$0")/.." || exit 1
mkdir -p data/logs
LOG="data/logs/collect-$(date +%Y%m%d).log"
echo "coletor: log em $LOG"
# Sai do laço quando o coletor devolve 3 (outro coletor já está rodando), para não ficar reiniciando a cada 2 s.
exec caffeinate -dimsu bash -c "while :; do bun run collect >> '$LOG' 2>&1; rc=\$?; if [ \$rc -eq 0 ]; then exit 0; fi; if [ \$rc -eq 3 ]; then echo 'coletor: outro coletor já está rodando (veja data/collect.pid); este laço encerra'; exit 3; fi; echo \"{\\\"t\\\":\\\"reinicio\\\",\\\"em\\\":\\\"\$(date -u +%Y-%m-%dT%H:%M:%SZ)\\\"}\" >> '$LOG'; sleep 2; done"
