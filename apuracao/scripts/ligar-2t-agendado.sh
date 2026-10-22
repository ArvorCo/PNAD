#!/usr/bin/env bash
# Guardião do dia 25/10/2026: espera até a hora marcada e liga, nesta ordem, o preflight do 2º turno,
# o coletor (modo 2t), o servidor e a publicação da página pública. Fica rodando desde já, sem sondar
# o TSE antes da hora, para que a apuração entre no ar sozinha.
#
#   nohup scripts/ligar-2t-agendado.sh >/dev/null 2>&1 &     # agenda (padrão: 25/10/2026 16:40 de Brasília)
#   QUANDO="2026-10-25T16:40:00-0300" scripts/ligar-2t-agendado.sh
#   scripts/ligar-2t-agendado.sh --agora                      # liga tudo imediatamente
#   kill "$(cat data/logs/agendado-2t.pid)"                   # cancela o agendamento
# Log: data/logs/agendado-2t.log. Se o preflight reprovar, o guardião ainda liga o coletor e o servidor
# (a noite não pode esperar) e deixa o motivo no log. Variáveis do runbook (APURACAO_*, INTERVALO_S,
# PUSH) passam adiante. Precisa do Mac acordado: `pmset -g` sem sono agendado.
set -u
cd "$(dirname "$0")/.." || exit 1
mkdir -p data/logs
LOG="data/logs/agendado-2t.log"
PIDFILE="data/logs/agendado-2t.pid"
QUANDO="${QUANDO:-2026-10-25T16:40:00-0300}"
echo $$ > "$PIDFILE"
log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" >> "$LOG"; }

alvo=$(date -j -f "%Y-%m-%dT%H:%M:%S%z" "$QUANDO" +%s 2>/dev/null) || { log "hora inválida: $QUANDO"; exit 1; }
if [ "${1:-}" != "--agora" ]; then
  log "agendado para $QUANDO (epoch $alvo); pid $$"
  while :; do
    agora=$(date +%s)
    falta=$((alvo - agora))
    [ "$falta" -le 0 ] && break
    sleep $(( falta > 60 ? 60 : falta ))
  done
fi

log "ligando o 2º turno"
if scripts/preflight.sh 2t >> "$LOG" 2>&1; then
  log "preflight ok"
else
  log "preflight reprovou (ver acima); ligando mesmo assim"
fi
rm -f data/collect.pid
nohup scripts/start-collect.sh 2t >> data/logs/collect-2t.out 2>&1 &
log "coletor ligado (pid $!)"
sleep 3
APURACAO_DB="${APURACAO_DB:-data/apuracao-2t.sqlite}" nohup scripts/start-serve.sh >> data/logs/serve-2t.out 2>&1 &
log "servidor ligado (pid $!)"
sleep 10
if curl -fsS "http://127.0.0.1:${APURACAO_PORT:-4180}/api/config" >/dev/null; then
  log "servidor responde"
else
  log "servidor não respondeu em 10 s (o start-serve.sh religa sozinho)"
fi
nohup scripts/publicar-loop.sh >/dev/null 2>&1 &
log "publicação ligada (pid $!)"
rm -f "$PIDFILE"
log "pronto: telão em http://127.0.0.1:${APURACAO_PORT:-4180}/#v=pres&auto=1&hud=0"
