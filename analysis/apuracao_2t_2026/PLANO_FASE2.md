# Fase 2 do dossiê do 2º turno (decisões do Leonardo, 26/10/2026, 00h10)

Publicação do dossiê `docs/apuracao_2T_2026.html` e do vídeo só depois de três entregas. Tese editorial em `TESE.md`.

## 1. Logs de todas as urnas do 2º turno e os sinais por seção
- Coleta dos BUs (`apuracao/data/secoes_2t_2026.sqlite`, pid em `apuracao/data/secoes-p003221.pid`) termina por volta das 03h50 de 26/10; depois `--refazer-erros` e `--revisitar`.
- Coleta dos logs: `python3 scripts/apuracao-2026-logs-coletar.py --pleito 3221 --origem apuracao/data/secoes_2t_2026.sqlite --db data/raw/tse_logs_2026/logs_2t.sqlite --rps 20 --workers 16` (54 GB no 1T; conferir disco). `scripts/apuracao_logs/processamento.py` e `complementos.py` precisam de parametrização por pleito antes de rodar sobre o 2T; nova `parser.VERSAO` só se a semântica mudar.
- Análises sobre o banco completo de BUs (independem dos logs): `scripts/apuracao-2t-2026-secoes.py --fonte completo`; `scripts/abstencao-lula-secoes.py --turno 2` nos dois eixos; **IDs das urnas**: `numero_interno_urna` e modelo por seção, contagem de IDs que aparecem em mais de uma seção (mesma zona/município, municípios diferentes, mesma hora de abertura), cruzado com `n_cargas`, `tipo_urna` (contingência), `carga_em`, `tipo_arquivo`, hash do BU e com o 1T (`secoes_2026.sqlite`: a mesma urna serviu a mesma seção?); referência explícita ao que se alegou sobre IDs repetidos no 2º turno de 2022 (procurar e arquivar as fontes, com o que o TSE respondeu); o sinal entra no escore por seção e no Politize-se com rótulo "pede explicação, não prova irregularidade" e com as explicações legítimas (troca de urna, seção agregada, contingência) testadas antes.
- Com os logs: as 25 famílias de diagnóstico do 1T recalculadas para o 2T, comparação seção a seção 1T × 2T (atenção 0 a 3), votos por hora dentro da seção (cadência), bateria, biometria no log contra o BU, ID/serial do log contra o BU.

## 2. Politize-se (sucessor do Politize sua vizinhança)
- Pergunta do app: "entenda o que aconteceu no seu local de votação e na sua seção". Entrada UF + zona + seção (como o Politize), CEP, cidade e geolocalização.
- Por seção: 1º × 2º turno (votos, fatia, comparecimento, abstenção, brancos/nulos), biometria (1T e 2T), encerramento e recebimento do BU, urna (modelo, ID, cargas, contingência), sinais dos logs e escore, mudança de local entre turnos, fiscal recomendado no 1T e o que foi conferido, clima do dia. Por local: as seções do prédio lado a lado, e o prédio contra o município. Tudo com rótulos da casa; lado declarado da casa, voto secreto, leitura agregada.
- Reaproveita `docs/assets/politize/` (dados por zona e município, fiscal, mudanças, logs.js, card.js) com camada 2T nova gerada por `scripts/politize-build.py` ou script irmão `politize-se-build.py`; contrato em `analysis/politize/CONTRATO.md` estendido.

## 3. Mapa completo do Brasil
- Mapa navegável de todos os locais de votação (base do `docs/fiscais_mapa.html`, Leaflet + markercluster, formato 2), com busca e cor por resultado do 2T, variação contra o 1T, abstenção ou sinal; cada prédio abre a ficha e leva ao Politize-se da seção (`#uf=&l=&s=`). Entrada a partir do dossiê (capítulo de seções) e da home.

## Ordem
1. Fim da coleta dos BUs → análises do item 1 sem logs (IDs, seções completo, correlação) → republicar rascunho local.
2. Coleta e processamento dos logs → sinais por seção.
3. Politize-se e mapa com as camadas 1 e 2.
4. Dossiê, thread e vídeo revistos com tudo → publicação.

## Decisões de 26/10, 01h
- Encadeamento pós-coleta em `apuracao/scripts/fase2-pos-coleta.sh` (refazer erros, revisitar, conferir; RDV conferir; logs em modo compacto; análises completas; build).
- Logs: modo compacto (`--guardar compacto`, ~29 GB) porque os ZIPs inteiros (~89 GB) não cabem; reconstrução conferida por SHA-256.
- Critério "erro técnico no dia" no 2T: "Problema ao desmontar a MR" antes da zerésima é rotina da urna religada com a mesma carga (2.198 de 2.270 em AC). Fica como versão nova declarada do critério para o 2T: esse evento sai do "erro técnico" e vira contagem à parte; o número bruto continua publicado.
- IDs das urnas (urnas.md): nada parecido com 2022; repetidos no 2T = 0; trocas de urna entre turnos sem efeito no voto.
- RDV: sem ligação entre cargos (listas separadas por cargo); achado novo é o número de presidente digitado no campo de governador (AC: 72,7% dos nulos de governador).

## Pedidos de 26/10, 03h30
- Metadados das urnas (todos, por seção): serial/ID no BU e no log, código de carga, versão do software e hash do sistema (log), mídia de carga, certificado de hardware do `.vsc`, data/hora de carga e de zerésima; procurar repetição e incoerência, comparar com o 1T; vira sinal no escore se houver repetição fora das explicações legítimas. Requer coletar o `.vsc` de cada seção (está no mesmo hash do BU) e os logs.
- Hipóteses adversariais sobre a prorrogação e a ordem de testes em `HIPOTESES_PRORROGACAO.md` (memorando interno).
- Pedir ao Leonardo o vídeo dos artistas (arquivo original ou link da primeira publicação) para os metadados e a cronologia.

## Respostas do Leonardo (26/10, 04h05)
- `.vsc` de cada seção: autorizado (coleta em `apuracao/scripts/vsc-coletar.ts`, banco `apuracao/data/vsc_2t_2026.sqlite`).
- Justificativa da parada 17:07–19:01: a decisão de Zanin, pública; sem pedido por LAI. O dossiê distingue o que foi declarado (a prorrogação) do que não foi (a razão de reter BUs já recebidos).
- Vídeo dos artistas: a enviar como arquivo em `data/originals/prorrogacao_video/` ou link da primeira publicação; a análise de metadados fica pendente até chegar.
