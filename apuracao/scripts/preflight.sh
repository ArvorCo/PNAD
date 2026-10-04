#!/usr/bin/env bash
# Checagem antes de ligar o coletor (runbook, 16:30). Sai com 1 se algo crítico falhar.
set -u
cd "$(dirname "$0")/.." || exit 1
DB="${APURACAO_DB:-data/apuracao.sqlite}"
BASE="${APURACAO_BASE_URL:-https://resultados.tse.jus.br/oficial}"
falhas=0
ok() { printf '  ok    %s\n' "$1"; }
falha() { printf '  FALHA %s\n' "$1"; falhas=$((falhas + 1)); }
aviso() { printf '  aviso %s\n' "$1"; }

echo "preflight do coletor ($(date '+%Y-%m-%d %H:%M:%S %Z'))"

if command -v bun >/dev/null 2>&1; then ok "bun $(bun --version)"; else falha "bun ausente"; fi

mkdir -p "$(dirname "$DB")"
livre_gib=$(df -k "$(dirname "$DB")" | awk 'NR==2 {printf "%d", $4 / 1048576}')
if [ "${livre_gib:-0}" -ge 40 ]; then ok "disco livre ${livre_gib} GiB"; else falha "disco livre ${livre_gib:-?} GiB (mínimo 40)"; fi

cab=$(curl -sI --max-time 10 -H 'Accept-Encoding: gzip' "$BASE/comum/config/ele-c.json" || true)
status=$(printf '%s' "$cab" | awk 'NR==1 {print $2}')
etag=$(printf '%s' "$cab" | grep -i '^etag:' | tr -d '\r' | cut -d' ' -f2-)
if [ "$status" = "200" ] && [ -n "$etag" ]; then ok "ele-c.json 200, etag $etag"; else falha "ele-c.json status '${status:-sem resposta}' etag '${etag:-}'"; fi

data_srv=$(printf '%s' "$cab" | grep -i '^date:' | tr -d '\r' | cut -d' ' -f2-)
if [ -n "$data_srv" ]; then
  srv=$(date -j -u -f '%a, %d %b %Y %H:%M:%S GMT' "$data_srv" +%s 2>/dev/null || echo 0)
  agora=$(date -u +%s)
  skew=$((agora - srv))
  abs=${skew#-}
  if [ "$srv" -gt 0 ] && [ "$abs" -lt 2 ]; then ok "relógio: desvio ${skew}s"; else falha "relógio: desvio ${skew}s contra Date '$data_srv'"; fi
else
  falha "sem cabeçalho Date para medir o relógio"
fi

pidfile="$(dirname "$DB")/collect.pid"
if [ -f "$pidfile" ]; then
  pid=$(cat "$pidfile")
  if kill -0 "$pid" 2>/dev/null; then falha "coletor já rodando (pid $pid)"; else aviso "pidfile velho (pid $pid), o coletor remove na partida"; fi
else
  ok "sem pidfile"
fi

if [ -f "$DB" ]; then
  qc=$(sqlite3 "$DB" 'PRAGMA quick_check;' 2>&1 | head -1)
  if [ "$qc" = "ok" ]; then ok "quick_check ok ($(du -h "$DB" | cut -f1))"; else falha "quick_check: $qc"; fi
else
  aviso "banco $DB ainda não existe (será criado)"
fi

sono=$(pmset -g 2>/dev/null | awk '$1 == "sleep" {print $2}')
if [ "${sono:-1}" = "0" ]; then ok "pmset sleep 0"; else aviso "pmset sleep ${sono:-?}: start-collect.sh usa caffeinate -dimsu"; fi
agendado=$(pmset -g sched 2>/dev/null | grep -ci 'sleep' || true)
if [ "${agendado:-0}" = "0" ]; then ok "sem sleep agendado"; else falha "há sleep agendado em pmset -g sched"; fi

if [ "$falhas" -gt 0 ]; then echo "preflight: $falhas falha(s)"; exit 1; fi
echo "preflight: tudo certo"
