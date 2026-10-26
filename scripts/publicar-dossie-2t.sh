#!/usr/bin/env bash
# Publica no origin/main só os arquivos do dossiê do 2º turno (e do Politize-se, mapa, relatos,
# coletores e telão), por um worktree destacado de origin/main, sem levar as mudanças alheias
# que estão soltas na main local. Regra da casa: a main local carrega snapshots e trabalho de
# outras sessões não enviados; nunca publicar a partir dela (memória pnad-publicar-via-worktree).
#
# Uso: bash scripts/publicar-dossie-2t.sh [--dry-run] [--mensagem "texto"]
#   --dry-run  só monta o worktree e mostra o git status, sem commit nem push.
set -euo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
WT="$RAIZ/tmp/dossie-2t-publicacao"
DRY=0
MSG="dossiê da apuração do 2º turno: página, thread, Politize-se, mapa do Brasil e fase 2"
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY=1 ;;
    --mensagem) MSG="$2"; shift ;;
    *) echo "argumento desconhecido: $1"; exit 2 ;;
  esac
  shift
done

cd "$RAIZ"
git fetch -q origin
rm -rf "$WT"
git worktree prune
GIT_LFS_SKIP_SMUDGE=1 git worktree add -q --detach "$WT" origin/main

# Lista fechada do que entra. Pastas terminam em barra e são copiadas inteiras (com --delete
# dentro delas, para arquivos regenerados saírem), menos o que o .gitignore já exclui.
CAMINHOS=(
  # dossiê, thread, Politize-se, mapa
  docs/apuracao_2T_2026.html docs/apuracao_2T_2026_thread.html
  docs/politizese.html docs/politizese_mapa.html docs/politize-se/ docs/politizesuavizinhanca.html
  docs/index.html docs/logs_urnas_2026.html docs/apuracao_1o_turno_2026.html docs/fiscais_thread.html
  docs/assets/apuracao_2t/ docs/assets/politize_se/ docs/assets/politize_se_mapa/
  docs/assets/logs_urnas_2t_2026/ docs/assets/logs_urnas_2026/
  docs/img/apuracao_2t/ docs/img/apuracao_2t_thread/
  docs/img/abstencao_lula_secoes_2t.png docs/img/comparecimento_lula_secoes_2t.png docs/img/variacao_comparecimento_lula_secoes_2t.png
  docs/img/og/apuracao_2T_2026.png docs/img/og/apuracao_2T_2026_thread.png docs/img/og/politizese.png docs/img/og/politizese_mapa.png
  docs/assets/og/apuracao_2T_2026.html docs/assets/og/apuracao_2T_2026_thread.html docs/assets/og/politizese.html docs/assets/og/politizese_mapa.html
  # scripts e módulos
  scripts/apuracao_2t_2026/ scripts/politize_se/ scripts/apuracao_logs/
  scripts/social-cards.py scripts/social-card-politizese-mapa.py scripts/abstencao-lula-secoes.py
  scripts/apuracao-2026-logs-coletar.py scripts/apuracao-2026-logs-processar.py scripts/apuracao-2026-logs-build.py
  scripts/video-sete-riscos-capa.py scripts/publicar-dossie-2t.sh
  # testes
  tests/test_apuracao_logs_2t.py tests/test_video_apuracao_2t.py tests/test_video_sete_riscos.py
  # análise (sem os pesados ignorados)
  analysis/apuracao_2t_2026/ analysis/politize_se/ analysis/apuracao_2026/logs_urnas/CONTRATO.md
  # fontes arquivadas
  data/originals/prorrogacao_video/ data/originals/tse_formato_bu_rdv_2026/ data/originals/rdv_2022_alegacoes/
  # coletores, telão e totalização
  apuracao/scripts/ apuracao/src/ apuracao/tests/ apuracao/README.md apuracao/package.json apuracao/bunfig.toml apuracao/public/playlist-2t.json apuracao/public/img/ apuracao/public/boletim.html
  totalizacao/supabase/migrations/ totalizacao/supabase/functions/receber-relato/ totalizacao/supabase/config.toml
  totalizacao/src/relato/ totalizacao/tests/relato.test.ts totalizacao/tests/relato_desafio.test.ts totalizacao/README.md
  video/apuracao_2t/
  # clima do 2º turno (modelo provisório, medição agendada)
  scripts/clima-2t.py scripts/clima-2t-modelo.py scripts/clima-2t-cemaden.py scripts/clima-2t-fotos-cemaden.py scripts/clima-2t-atualizar.sh scripts/clima_2t/ analysis/clima_2t_2026/
  docs/assets/fiscais_mapa/clima/observado_2t.json docs/assets/fiscais_mapa/app.js docs/fiscais_mapa.html tests/test_clima_2t_observado.py tests/test_clima_1t.py tests/test_fiscais_mapa_mudancas.py
  # raiz
  AGENTS.md .gitignore .gitattributes requirements.txt
)
# scripts soltos do dossiê, pelo padrão de nome
for f in scripts/video-masterclass-*.py tests/test_video_masterclass.py scripts/apuracao-2t-2026-*.py scripts/politize-se-*.py scripts/video-apuracao-2t-*.py tests/test_apuracao_2t_*.py tests/test_politize_se*.py; do
  [ -e "$f" ] && CAMINHOS+=("$f")
done

# Pastas regeradas do zero recebem --delete (arquivos velhos saem); as demais só acrescentam,
# porque podem conter arquivos publicados por outro caminho (a exportação ao vivo em docs/assets/apuracao_2t).
COM_DELETE=(docs/assets/politize_se/ docs/assets/politize_se_mapa/ docs/assets/logs_urnas_2t_2026/ docs/assets/logs_urnas_2026/ docs/img/apuracao_2t_thread/ scripts/apuracao_2t_2026/ scripts/politize_se/)
for c in "${CAMINHOS[@]}"; do
  if [ -d "$c" ]; then
    mkdir -p "$WT/$c"
    DEL=""; for d in "${COM_DELETE[@]}"; do [ "$d" = "$c" ] && DEL="--delete"; done
    rsync -a $DEL --exclude 'node_modules/' --exclude 'out/' --exclude 'public/voz/' --exclude 'public/musica/' --exclude 'public/midia/' --exclude 'public/sfx/' --exclude 'public/final/' --exclude 'midia/' --exclude 'capturas/' --exclude '__pycache__/' --exclude '.pytest*' --exclude 'relatos/' --exclude 'sinalizadas.json' --exclude 'data/' --exclude 'qa/*.png' "$c" "$WT/$c"
  elif [ -e "$c" ]; then
    mkdir -p "$WT/$(dirname "$c")"; cp "$c" "$WT/$c"
  else
    echo "aviso: não existe: $c"
  fi
done
# vinhetas e bundle do telão nunca entram (não rastreados); apuracao/data fica como está no origin
rm -rf "$WT/apuracao/public/vinheta" "$WT/apuracao/public/dist"
# symlinks de node_modules nos vídeos ficam fora
find "$WT/video" -maxdepth 2 -name node_modules -type l -delete 2>/dev/null || true

cd "$WT"
git add -A
echo "== arquivos no commit: $(git status --porcelain | wc -l | tr -d ' ')"
git status --porcelain | awk '{print $2}' | sed -E 's#^((docs/assets|docs/img|analysis|scripts|tests|apuracao|totalizacao|video|data)/[^/]+/).*#\1#' | sort | uniq -c | sort -rn | head -40
if [ "$DRY" = 1 ]; then echo "== dry-run: worktree em $WT (sem commit)"; exit 0; fi
git -c user.name="Leonardo Dias" commit -q -F - <<EOF
$MSG

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
EOF
# sitemap só vê arquivos rastreados: regenerar dentro do worktree e emendar
python3 scripts/sitemap-build.py >/dev/null 2>&1 || true
git add docs/sitemap.xml docs/robots.txt 2>/dev/null || true
git -c user.name="Leonardo Dias" commit -q --amend --no-edit || true
for i in 1 2 3; do
  git fetch -q origin && git rebase -q origin/main && git lfs push origin HEAD 2>/dev/null; git push -q origin HEAD:main && echo "PUSH_OK $(git rev-parse --short HEAD)" && break || { echo "tentativa $i falhou"; sleep 10; }
done
cd "$RAIZ" && git worktree remove --force "$WT" && git worktree prune
