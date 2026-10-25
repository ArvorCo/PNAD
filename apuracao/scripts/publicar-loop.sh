#!/usr/bin/env bash
# Publica a apuração do 2º turno no GitHub Pages: exporta os JSON públicos e faz commit + push.
#
# Ligar (em segundo plano, a partir da raiz do repositório PNAD ou de apuracao/):
#   nohup apuracao/scripts/publicar-loop.sh >/dev/null 2>&1 &
# Variáveis: INTERVALO_S (padrão 300), APURACAO_PORT (padrão 4180), PUSH=0 para só commitar,
# FORCAR_MIN (padrão 9): commit mesmo sem dado novo quando o último publicado passa disso, para o
# aviso de idade da página (20 min) não disparar com a publicação sadia; PENDENTES_TOLERADOS
# (lista separada por vírgula, padrão vazia): rotas pendentes que não bloqueiam o commit.
# Desligar:
#   kill "$(cat apuracao/data/logs/publicar.pid)"      # ou: pkill -f publicar-loop.sh
# Log do dia: apuracao/data/logs/publicar-AAAAMMDD.log
# Exporta direto no worktree de publicação, reaproveitando dele (o último publicado) as rotas que
# falharem; nunca da main local, que guarda um retrato antigo. Manifesto com `pendentes` não vazio
# não é publicado (loga "pendentes: ..."): a página fica no último retrato bom.
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
  # Publica por um worktree destacado de origin/main, porque a main local carrega commits de outras
  # sessões e arquivos sujos: o push da main é rejeitado desde 24/10. O worktree recebe só esta pasta.
  local wt="$REPO/tmp/apuracao-2t-publicacao"
  if [ ! -d "$wt/.git" ] && [ ! -f "$wt/.git" ]; then
    git -C "$REPO" fetch -q origin || { log "fetch falhou"; return 1; }
    git -C "$REPO" worktree add --detach "$wt" origin/main >>"$LOG" 2>&1 || { log "worktree falhou"; return 1; }
  fi
  git -C "$wt" fetch -q origin || { log "fetch falhou"; return 1; }
  git -C "$wt" reset -q --hard origin/main || { log "reset falhou"; return 1; }
  mkdir -p "$wt/$PASTA"
  # Exporta no worktree: rota que falhar fica com o arquivo do último commit publicado.
  if ! bun run scripts/exportar-publico.ts --saida "$wt/$PASTA" --anterior "$wt/$PASTA" >>"$LOG" 2>&1; then
    log "exportação falhou"
    git -C "$wt" checkout -q -- "$PASTA" 2>/dev/null || true
    return 1
  fi
  # Rota pendente (erro, prazo ou {pendente:true}) bloqueia o commit, salvo as toleradas.
  local pendentes
  pendentes="$(python3 -c 'import json,sys; m=json.load(open(sys.argv[1])); tol={x for x in sys.argv[2].split(",") if x}; print(",".join(p for p in m.get("pendentes", []) if p not in tol))' "$wt/$PASTA/manifest.json" "${PENDENTES_TOLERADOS:-}" 2>/dev/null || echo "manifesto ilegível")"
  if [ -n "$pendentes" ]; then
    log "pendentes: $pendentes (sem commit; a página fica no último retrato publicado)"
    git -C "$wt" checkout -q -- "$PASTA" 2>/dev/null || true
    return 0
  fi
  # Compara o hash de conteúdo (sem carimbos de hora) de cada arquivo com o do último commit publicado.
  local antes depois idade_min ultimo
  antes="$(git -C "$wt" show "HEAD:$PASTA/manifest.json" 2>/dev/null | python3 -c 'import json,sys; m=json.load(sys.stdin); print(json.dumps({k: v.get("conteudo") for k, v in sorted(m.get("arquivos", {}).items())}))' 2>/dev/null || echo "?")"
  depois="$(python3 -c 'import json,sys; m=json.load(open(sys.argv[1])); print(json.dumps({k: v.get("conteudo") for k, v in sorted(m.get("arquivos", {}).items())}))' "$wt/$PASTA/manifest.json" 2>/dev/null || echo "!")"
  # Idade do último retrato publicado (commit que tocou a pasta em origin/main), em minutos.
  ultimo="$(git -C "$wt" log -1 --format=%ct -- "$PASTA" 2>/dev/null)"
  idade_min=$(( ( $(date +%s) - ${ultimo:-0} ) / 60 ))
  local motivo="dados novos"
  if [ "$antes" = "$depois" ]; then
    if [ "$idade_min" -le "${FORCAR_MIN:-9}" ]; then
      log "sem mudança de dados (último publicado há ${idade_min} min)"
      git -C "$wt" checkout -q -- "$PASTA" 2>/dev/null || true
      return 0
    fi
    motivo="sem dado novo, último publicado há ${idade_min} min"
  fi
  local hora
  hora="$(TZ=America/Sao_Paulo date +%H:%M)"
  git -C "$wt" add -- "$PASTA" >>"$LOG" 2>&1 || { log "git add falhou"; return 1; }
  git -C "$wt" commit -q -m "apuração 2T: snapshot $hora BRT" -- "$PASTA" >>"$LOG" 2>&1 || { log "commit falhou"; return 1; }
  log "commit $hora ($motivo)"
  if [ "${PUSH:-1}" = "1" ]; then
    if git -C "$wt" push -q origin HEAD:main >>"$LOG" 2>&1; then log "push ok"; else log "push falhou, tenta no próximo ciclo"; fi
  fi
}

log "iniciado, intervalo ${INTERVALO_S}s"
while true; do
  ciclo || true
  sleep "$INTERVALO_S" &
  wait $!
done
