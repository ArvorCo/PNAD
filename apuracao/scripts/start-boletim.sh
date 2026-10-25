#!/usr/bin/env bash
# Liga o gerador do boletim falado do 2º turno (bun run boletim) e o religa se cair.
# Relógio: ciclos a cada APURACAO_BOLETIM_INTERVALO_S (600) a partir de APURACAO_BOLETIM_INICIO
# (17:10 de Brasília); APURACAO_BOLETIM=0 deixa só a geração manual pelo diretor.
# Uso: nohup scripts/start-boletim.sh >/dev/null 2>&1 &
set -u
cd "$(dirname "$0")/.." || exit 1
mkdir -p data/logs data/boletins-2t
LOG="data/logs/boletim-2t-$(date +%Y%m%d).log"
export APURACAO_BOLETIM="${APURACAO_BOLETIM:-1}"
# O claude headless do roteiro usa o login próprio (keychain), nunca as variáveis da sessão que lançou o laço.
for v in $(env | grep -E '^(CLAUDE|ANTHROPIC)[A-Z0-9_]*=' | cut -d= -f1); do unset "$v"; done
echo "boletim: log em $LOG"
echo $$ > data/boletins-2t/laco.pid
while :; do
  bun run boletim >> "$LOG" 2>&1
  rc=$?
  if [ $rc -eq 0 ]; then exit 0; fi
  if [ $rc -eq 3 ]; then echo "boletim: outro gerador já está rodando (data/boletins-2t/gerador.pid); este laço encerra" >> "$LOG"; exit 3; fi
  echo "{\"t\":\"reinicio\",\"em\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"rc\":$rc}" >> "$LOG"
  sleep 2
done
