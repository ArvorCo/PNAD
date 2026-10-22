#!/usr/bin/env bash
# Publica a apuração do 2º turno no GitHub Pages: exporta os JSON públicos e faz commit + push.
#
# Ligar (em segundo plano, a partir da raiz do repositório PNAD ou de apuracao/):
#   nohup apuracao/scripts/publicar-loop.sh >/dev/null 2>&1 &
# Variáveis: INTERVALO_S (padrão 300), APURACAO_PORT (padrão 4180), PUSH=0 para só commitar.
# Desligar:
#   kill "$(cat apuracao/data/logs/publicar.pid)"      # ou: pkill -f publicar-loop.sh
# Log do dia: apuracao/data/logs/publicar-AAAAMMDD.log
# Só toca em docs/assets/apuracao_2t: o commit leva exclusivamente essa pasta. Falha de rede ou de
# push não interrompe o laço (loga e tenta de novo no próximo ciclo). Rótulo público: dados do
# telão, soma de arquivos do TSE, sem projeção.
set -u
AQUI="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$AQUI/.." && pwd)"
PASTA="docs/assets/apuracao_2t"
INTERVALO_S="${INTERVALO_S:-300}"
mkdir -p "$AQUI/data/logs"
PIDFILE="$AQUI/data/logs/publicar.pid"
LOG="$AQUI/data/logs/publicar-$(date +%Y%m%d).log"

log() { printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >>"$LOG"; }

if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  echo "publicar-loop já roda (pid $(cat "$PIDFILE"))" >&2
  exit 1
fi
echo $$ >"$PIDFILE"
trap 'rm -f "$PIDFILE"; log "encerrado"; exit 0' INT TERM

ciclo() {
  cd "$AQUI" || return 1
  if ! bun run scripts/exportar-publico.ts >>"$LOG" 2>&1; then
    log "exportação falhou"
    return 1
  fi
  cd "$REPO" || return 1
  # Só commita quando algum dado mudou: estado.json (traz o relógio `agora`) e manifest.json
  # (gerado_em e hashes) mudam em todo ciclo e não justificam commit sozinhos.
  # Compara o hash de conteúdo (sem carimbos de hora) de cada arquivo com o do último commit.
  local antes depois
  antes="$(git show "HEAD:$PASTA/manifest.json" 2>/dev/null | python3 -c 'import json,sys; m=json.load(sys.stdin); print(json.dumps({k: v.get("conteudo") for k, v in sorted(m.get("arquivos", {}).items())}))' 2>/dev/null || echo "?")"
  depois="$(python3 -c 'import json,sys; m=json.load(open(sys.argv[1])); print(json.dumps({k: v.get("conteudo") for k, v in sorted(m.get("arquivos", {}).items())}))' "$PASTA/manifest.json" 2>/dev/null || echo "!")"
  if [ "$antes" = "$depois" ]; then
    log "sem mudança de dados"
    git checkout -q -- "$PASTA" 2>/dev/null || true
    return 0
  fi
  local hora
  hora="$(TZ=America/Sao_Paulo date +%H:%M)"
  git add -- "$PASTA" >>"$LOG" 2>&1 || { log "git add falhou"; return 1; }
  git commit -m "apuração 2T: snapshot $hora BRT" -- "$PASTA" >>"$LOG" 2>&1 || { log "commit falhou"; return 1; }
  log "commit $hora"
  if [ "${PUSH:-1}" = "1" ]; then
    if git push >>"$LOG" 2>&1; then log "push ok"; else log "push falhou, tenta no próximo ciclo"; fi
  fi
}

log "iniciado, intervalo ${INTERVALO_S}s"
while true; do
  ciclo || true
  sleep "$INTERVALO_S" &
  wait $!
done
