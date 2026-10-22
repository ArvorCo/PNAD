#!/usr/bin/env bash
# Checagem antes de ligar o coletor (runbook, 16:30). Sai com 1 se algo crítico falhar.
#   scripts/preflight.sh       1º turno
#   scripts/preflight.sh 2t    2º turno: banco data/apuracao-2t.sqlite, régua do 1º turno, -cs.json do
#                              pleito 3221 e leitura das views públicas da totalização paralela
set -u
cd "$(dirname "$0")/.." || exit 1
TURNO2=0
if [ "${1:-}" = "2t" ]; then
  TURNO2=1
  export APURACAO_ELEICOES="${APURACAO_ELEICOES:-6258,6260}"
  export APURACAO_PLEITO="${APURACAO_PLEITO:-3221}"
  export APURACAO_DB="${APURACAO_DB:-data/apuracao-2t.sqlite}"
fi
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

if [ "$TURNO2" = "1" ]; then
  echo "2º turno (eleições $APURACAO_ELEICOES, pleito $APURACAO_PLEITO)"
  UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
  REF="${APURACAO_REFERENCIA_1T:-data/referencia_1t.json}"
  if [ -f "$REF" ]; then
    resumo=$(bun -e "const r = JSON.parse(await Bun.file('$REF').text()); console.log(Object.keys(r.curvas?.uf ?? {}).length + ' UFs, ' + Object.keys(r.secoes_lag?.uf ?? {}).length + ' com lag, gerada em ' + (r.meta?.gerado_em ?? '?'))" 2>&1)
    case "$resumo" in
      28\ UFs*) ok "régua do 1º turno: $resumo" ;;
      *) falha "régua do 1º turno incompleta: $resumo" ;;
    esac
  else
    falha "régua do 1º turno ausente ($REF): rode bun run scripts/referencia-1t.ts"
  fi
  P6=$(printf '%06d' "$APURACAO_PLEITO")
  CS="$BASE/ele2026/arquivo-urna/$APURACAO_PLEITO/config/ac/ac-p${P6}-cs.json"
  cs_status=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 --compressed -H "User-Agent: $UA" "$CS" || true)
  if [ "$cs_status" = "200" ]; then ok "cs.json do pleito $APURACAO_PLEITO (AC) 200"; else falha "cs.json do pleito $APURACAO_PLEITO (AC) status '${cs_status:-sem resposta}'"; fi
  cache=$(ls data/secoes/cs/*-p${P6}-cs.json 2>/dev/null | wc -l | tr -d ' ')
  if [ "${cache:-0}" -ge 27 ]; then ok "cache de -cs.json: $cache UFs"; else aviso "cache de -cs.json com ${cache:-0} UFs (o coletor baixa o resto na partida)"; fi
  SB_URL=$(sed -n 's/^export const SUPABASE_URL = "\(.*\)";$/\1/p' src/paralela/supabase.ts)
  SB_CHAVE=$(sed -n 's/^export const CHAVE_PUBLICAVEL = "\(.*\)";$/\1/p' src/paralela/supabase.ts)
  sb=$(curl -s --max-time 15 -H "apikey: $SB_CHAVE" -H "Authorization: Bearer $SB_CHAVE" "${APURACAO_PARALELA_URL:-$SB_URL}/rest/v1/v_estatisticas" || true)
  case "$sb" in
    \[\{*envios*) ok "totalização paralela (Supabase): $(printf '%s' "$sb" | tr -d '\n' | cut -c1-120)" ;;
    *) falha "totalização paralela (Supabase) sem leitura: $(printf '%s' "$sb" | cut -c1-120)" ;;
  esac
  if [ -f "$DB" ]; then
    tabelas=$(sqlite3 "$DB" "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name IN ('pausa', 'secao_2t', 'paralela_bu', 'paralela_conferencia');" 2>&1)
    if [ "$tabelas" = "4" ]; then ok "tabelas do 2º turno presentes"; else aviso "tabelas do 2º turno ainda não criadas ($tabelas de 4): o coletor cria na partida"; fi
  fi
  echo "  info  amostra ${APURACAO_SECOES:-1} (${APURACAO_SECOES_AMOSTRA_UF:-150}/UF, ${APURACAO_SECOES_AMOSTRA_ESTADUAL:-600} nas 6 UFs com governador, ${APURACAO_SECOES_RPS:-15} req/s), paralela ${APURACAO_PARALELA:-1} (a cada ${APURACAO_PARALELA_INTERVALO_S:-60} s)"
fi

if [ "$falhas" -gt 0 ]; then echo "preflight: $falhas falha(s)"; exit 1; fi
echo "preflight: tudo certo"
