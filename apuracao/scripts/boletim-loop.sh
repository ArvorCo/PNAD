#!/usr/bin/env bash
# Laço do locutor automático: a cada INTERVALO segundos gera o resumo, escreve o roteiro com o
# Claude headless (Opus) seguindo data/boletins/ESTILO.md, gera o áudio (ElevenLabs v4) e toca.
# Uso: nohup scripts/boletim-loop.sh > data/logs/boletim-loop.log 2>&1 &
set -u
cd "$(dirname "$0")/.." || exit 1
INTERVALO="${BOLETIM_INTERVALO:-600}"
JANELA_MIN="${BOLETIM_JANELA:-10}"
mkdir -p data/boletins
echo $$ > data/boletins/loop.pid
if [ "${BOLETIM_ESPERAR:-0}" = "1" ]; then
  # Reinício no meio do ciclo: espera o próximo múltiplo do intervalo em vez de falar agora.
  AGORA=$(date +%s); PROXIMO=$(( (AGORA / INTERVALO + 1) * INTERVALO ))
  echo "[$(TZ=America/Sao_Paulo date +%H%M)] esperando até $(TZ=America/Sao_Paulo date -r "$PROXIMO" +%H:%M:%S)"
  sleep $(( PROXIMO - AGORA ))
fi
while :; do
  H=$(TZ=America/Sao_Paulo date +%H%M)
  INICIO=$(date +%s)
  echo "[$H] resumo"
  if ! bun run scripts/boletim-dados.ts "$JANELA_MIN" > "data/boletins/dados-$H.json" 2> "data/boletins/dados-$H.err"; then
    echo "[$H] falha no resumo: $(tail -1 "data/boletins/dados-$H.err")"; sleep 60; continue
  fi
  ANTERIOR=$(ls data/boletins/*.txt 2>/dev/null | grep -v ESTILO | tail -1)
  # Bancadas por espectro (Câmara, Senado 2027, assembleias, governadores): TSE onde fechou, provisório no resto.
  if bun run scripts/final-2026.ts > /dev/null 2> "data/boletins/final-$H.err"; then
    python3 scripts/boletim-bancadas.py > "data/boletins/bancadas-$H.json" 2>> "data/boletins/final-$H.err" || echo "[$H] extrato de bancadas falhou"
  else
    echo "[$H] avaliação final falhou: $(tail -1 "data/boletins/final-$H.err")"
  fi
  BANCADAS=$( [ -s "data/boletins/bancadas-$H.json" ] && cat "data/boletins/bancadas-$H.json" || echo "{}" )
  PROMPT="Você é o analista de dados da Arvor Intelligence na noite da apuração do 1º turno de 2026, falando ao vivo na voz do Leonardo Dias. Escreva o roteiro do boletim das $H para o ElevenLabs seguindo EXATAMENTE o guia abaixo. Responda só com o roteiro, sem título, sem comentários, sem markdown.

GUIA DE ESTILO:
$(cat data/boletins/ESTILO.md)

ESTRUTURA OBRIGATÓRIA (500 a 600 palavras): hora e percentual de seções totalizadas; placar nacional dos cinco primeiros com percentual e votos, diferença entre 1º e 2º em pontos e votos, brancos, nulos e comparecimento; os últimos $JANELA_MIN minutos (atualizações, seções e votos que chegaram, quem levou qual fatia do bloco, se a diferença abriu ou fechou contra o início da janela, último lote); ritmo em seções por minuto e previsão simples de fim rotulada como projeção simples; mapa (UFs mais adiantadas e atrasadas, quem lidera onde e por quanto, disputas apertadas, viradas); governadores (quem o TSE já marcou eleito no 1º turno, quem está acima de 50% com apuração parcial, quem vai ao 2º turno); BANCADAS obrigatório (JSON BANCADAS: Câmara dos Deputados por espectro e por partido, com os blocos direita mais centro-direita, esquerda mais centro-esquerda e centro, dizendo quantas UFs já estão fechadas pelo TSE e quantas são provisórias; Senado de 2027 por espectro, com os 27 que continuam e os 54 novos; assembleias de SP, MG, RJ, BA, RS e PR por espectro; o que esses tamanhos significam para governabilidade e para o segundo turno, sem falar de puxar voto, transferência ou vão estadual); Senado nas UFs com mais de 15% apurado (CADA UF ELEGE DOIS: dizer os dois prováveis eleitos e, quando a segunda vaga está apertada, quem ameaça e por quantos pontos; nunca descrever os dois primeiros como adversários entre si); exterior; fechamentos de UF; NÃO falar de atraso de leitura, de arquivo atrasado nem de CDN (a apuração está acima de 99%: o assunto é resultado); leitura final de analista sobre o quadro que se consolida (segundo turno presidencial, quem foi eleito governador no primeiro turno e quem vai ao segundo, bancadas que se desenham). Não repita frases do boletim anterior.

BOLETIM ANTERIOR (para não repetir):
$( [ -n "$ANTERIOR" ] && cat "$ANTERIOR" | head -60 )

DADOS (JSON):
$(cat "data/boletins/dados-$H.json")

BANCADAS (JSON):
$BANCADAS"
  echo "[$H] roteiro"
  if ! claude -p --model opus --no-session-persistence "$PROMPT" > "data/boletins/$H.txt" 2> "data/boletins/$H.claude.err"; then
    echo "[$H] falha no roteiro: $(tail -2 "data/boletins/$H.claude.err")"; sleep 60; continue
  fi
  PAL=$(wc -w < "data/boletins/$H.txt")
  echo "[$H] $PAL palavras"
  if [ "$PAL" -gt 620 ]; then
    # Segundo passo: enxuga sem perder estrutura nem tags (o v4 fala pausado: 760 palavras dão 4 min 45 s).
    cp "data/boletins/$H.txt" "data/boletins/$H.longo.txt"
    if claude -p --model opus --no-session-persistence "Reescreva o roteiro abaixo com 520 a 560 palavras, cortando repetições e detalhes menores, mantendo a ordem dos blocos, as tags de áudio entre colchetes, os números por extenso e o fecho de analista. Responda só com o roteiro.

$(cat "data/boletins/$H.longo.txt")" > "data/boletins/$H.txt" 2>> "data/boletins/$H.claude.err"; then
      echo "[$H] enxugado para $(wc -w < "data/boletins/$H.txt") palavras"
    else
      cp "data/boletins/$H.longo.txt" "data/boletins/$H.txt"; echo "[$H] enxugar falhou; mantido o longo"
    fi
  fi
  echo "$H" > data/boletins/.ultimo
  while pgrep -x afplay >/dev/null; do sleep 2; done
  echo "[$H] áudio"
  scripts/boletim-falar.sh "data/boletins/$H.txt" > "data/boletins/$H.log" 2>&1 || echo "[$H] falha no áudio: $(tail -2 "data/boletins/$H.log")"
  echo "[$H] fim ($(( $(date +%s) - INICIO )) s)"
  # Alinha ao relógio: próximo ciclo no próximo múltiplo de INTERVALO (18:40, 18:50...),
  # contado a partir do início deste ciclo, nunca menos de 30 s depois do fim do áudio.
  AGORA=$(date +%s)
  PROXIMO=$(( (INICIO / INTERVALO + 1) * INTERVALO ))
  while [ "$PROXIMO" -lt $(( AGORA + 30 )) ]; do PROXIMO=$(( PROXIMO + INTERVALO )); done
  echo "[$H] próximo às $(TZ=America/Sao_Paulo date -r "$PROXIMO" +%H:%M:%S)"
  sleep $(( PROXIMO - AGORA ))
done
