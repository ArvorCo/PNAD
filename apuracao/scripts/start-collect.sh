#!/usr/bin/env bash
# Liga o coletor sem deixar o Mac dormir e o reinicia se cair. Log JSON em data/logs/.
#   scripts/start-collect.sh        1º turno (padrões do coletor)
#   scripts/start-collect.sh 2t     2º turno: eleições 6258/6260, pleito 3221, banco data/apuracao-2t.sqlite,
#                                   com pausas, régua do 1º turno, amostra de seções e totalização paralela
# Desligáveis por ambiente: APURACAO_SECOES=0 (amostra), APURACAO_PARALELA=0 (paralela). Tetos da
# amostra: APURACAO_SECOES_RPS (15), APURACAO_SECOES_CONCORRENCIA (12), APURACAO_SECOES_INTERVALO_S (900).
set -u
cd "$(dirname "$0")/.." || exit 1
mkdir -p data/logs
SUFIXO=""
if [ "${1:-}" = "2t" ]; then
  export APURACAO_ELEICOES="${APURACAO_ELEICOES:-6258,6260}"
  export APURACAO_PLEITO="${APURACAO_PLEITO:-3221}"
  export APURACAO_DB="${APURACAO_DB:-data/apuracao-2t.sqlite}"
  # Limiar de pausa nacional em 7 min: no replay do 1º turno, 5 min marcava a cadência normal do arquivo.
  export APURACAO_PAUSA_MIN="${APURACAO_PAUSA_MIN:-7}"
  SUFIXO="-2t"
  echo "coletor: 2º turno, eleições $APURACAO_ELEICOES, pleito $APURACAO_PLEITO, banco $APURACAO_DB"
  echo "coletor: amostra de seções ${APURACAO_SECOES:-1}, totalização paralela ${APURACAO_PARALELA:-1}"
fi
LOG="data/logs/collect${SUFIXO}-$(date +%Y%m%d).log"
echo "coletor: log em $LOG"
# Sai do laço quando o coletor devolve 3 (outro coletor já está rodando), para não ficar reiniciando a cada 2 s.
exec caffeinate -dimsu bash -c "while :; do bun run collect >> '$LOG' 2>&1; rc=\$?; if [ \$rc -eq 0 ]; then exit 0; fi; if [ \$rc -eq 3 ]; then echo 'coletor: outro coletor já está rodando (veja data/collect.pid); este laço encerra'; exit 3; fi; echo \"{\\\"t\\\":\\\"reinicio\\\",\\\"em\\\":\\\"\$(date -u +%Y-%m-%dT%H:%M:%SZ)\\\"}\" >> '$LOG'; sleep 2; done"
