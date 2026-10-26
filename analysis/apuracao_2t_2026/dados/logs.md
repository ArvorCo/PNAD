# O que os logs das urnas dizem: 1º × 2º turno

Rótulo: pede explicação, não prova irregularidade. Gerado em 2026-10-26T19:49:51+00:00 por `scripts/apuracao-2t-2026-logs.py`.

## 1. Cobertura e integridade

- Logs lidos: 499.176 de 499.248 seções catalogadas.
- Contagem do log igual ao BU: 499.170; não confere: 6 (em todas o log tem menos cômputos que o BU: True).
  - BA 34711 zona 21 seção 178: log 233, BU 234 (-1); sistema religado 1 vez(es) durante a votação.
  - BA 35653 zona 173 seção 235: log 204, BU 217 (-13); urna de contingência ou mais de uma urna no pacote; relógio inconsistente.
  - MA 08893 zona 47 seção 609: log 188, BU 224 (-36); urna de contingência ou mais de uma urna no pacote.
  - PB 21750 zona 2 seção 254: log 303, BU 304 (-1); sistema religado 3 vez(es) durante a votação.
  - PI 11533 zona 3 seção 216: log 258, BU 259 (-1); sistema religado 5 vez(es) durante a votação.
  - RS 89060 zona 17 seção 191: log 90, BU 92 (-2); urna de contingência ou mais de uma urna no pacote; sistema religado 1 vez(es) durante a votação.
- Biometria conferida: 497.889; restantes 1.287: 1.281 sem as categorias no BU (exterior 1.281), 6 pela contagem.
- Versão do software: 10.23.0.0 - Praia da Barra do Cahy (499.176).
- Urna do BU no log: 499.176; código de carga do BU no log: 499.176.

## 2. Regra 2 (erro de desmontar a memória de resultado)

- Seções com ERRO/FATAL no dia: 497.705; só o erro da MR antes da zerésima: 478.127.
- Erro técnico pela regra 2: 19.578 (12.715 com erro dentro da janela de votação). No 1º turno, o critério marcou 5.577.
  - memória de resultado depois da zerésima, com reinício na votação: 12.393 seções.
  - memória de resultado depois da zerésima, sem reinício na votação: 6.097 seções.
  - outras mensagens sem categoria própria: 5.158 seções.
  - impressora: 210 seções.
  - mídia: 187 seções.
  - biometria (leitor): 189 seções.
  - assinatura: 38 seções.
  - demais categorias: 62 seções.

## 3. Persistência 1T × 2T

| 1T \ 2T | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| 0 | 334.082 | 62.757 | 4.013 | 258 |
| 1 | 57.877 | 26.432 | 3.099 | 488 |
| 2 | 3.534 | 3.584 | 968 | 164 |
| 3 | 620 | 844 | 337 | 117 |

| Diagnóstico | nos dois | só 1T | só 2T | persiste |
|---|---|---|---|---|
| Operação com bateria registrada | 38.294 | 78.722 | 66.641 | 32,7% |
| Janela de inspeção de cinco minutos ou mais | 9.101 | 21.402 | 69.337 | 29,8% |
| Passagem para bateria durante a votação, junto com outras urnas do município | 4.888 | 36.923 | 33.506 | 11,7% |
| Intervalo de 30 minutos entre cômputos | 9.122 | 8.228 | 26.553 | 52,6% |
| Aplicação reiniciada durante a votação | 2.377 | 13.301 | 10.001 | 15,2% |
| Sistema ligado novamente durante a votação | 2.344 | 13.116 | 9.927 | 15,2% |
| Erro técnico registrado no dia | 1.755 | 3.822 | 17.823 | 31,5% |
| Passagem para bateria durante a votação, só nesta urna | 1.573 | 11.095 | 10.279 | 12,4% |
| Eleitores sem biometria acima da referência | 5.617 | 301 | 305 | 94,9% |
| Cancelamentos de habilitação acima da referência | 925 | 5.276 | 1.712 | 14,9% |
| Ciclo de votação não reconstruído | 130 | 4.414 | 1.050 | 2,9% |
| Retomadas após inatividade acima da referência | 54 | 5.447 | 94 | 1,0% |
| Suspensões repetidas de votação | 8 | 3.132 | 38 | 0,2% |
| Habilitação biográfica acima da referência | 550 | 956 | 842 | 36,5% |
| Habilitação mais lenta que a referência | 157 | 438 | 238 | 26,4% |
| Votação mais lenta que a referência | 10 | 845 | 33 | 1,2% |
| Sequência temporal inconsistente ou relógio ajustado | 7 | 274 | 162 | 2,5% |
| Falha declarada de verificação de assinatura | 0 | 18 | 8 | 0,0% |
| Identidade ou fase de parte dos registros não confirmada | 0 | 18 | 7 | 0,0% |
| Categorias de habilitação não reconciliadas | 0 | 10 | 6 | 0,0% |
| Contagem do log não reconciliada com o BU | 0 | 10 | 6 | 0,0% |
| Estrutura ou texto crítico malformado | 2 | 0 | 0 | 100,0% |
| Zerésima anterior não localizada no pacote | 0 | 2 | 1 | 0,0% |

## 4. Cadência horária (hora de Brasília)

- 2º turno, 497.754 seções: primeira hora 16,75%, última hora (16h) 5,18%, 17h a 19h 0,027% (34.312 cômputos), depois das 19h 11 cômputos.
- 1º turno, amostra de 99.327 seções: primeira hora 9,47%, última hora 8,95%, 17h a 19h 2,89%.
- Último voto pelo log: depois das 17:30 em 2.480 seções, depois das 19:00 em 11.
- BUs encerrados depois das 19h: 4.468; último voto até 17:15 em 2.705.

| Grupo | seções | 1ª hora | última hora | 17h–19h |
|---|---|---|---|---|
| todas | 497.754 | 16,75% | 5,18% | 0,027% |
| sem nenhum diagnóstico no log | 301.668 | 16,46% | 5,26% | 0,023% |
| sistema religado durante a votação | 12.219 | 16,28% | 5,21% | 0,044% |
| bateria durante a votação | 62.210 | 17,59% | 5,00% | 0,029% |
| liberação sem biometria alta (BU) | 13.225 | 16,35% | 5,88% | 0,039% |
| habilitação por ano de nascimento alta (BU) | 19.303 | 17,05% | 4,63% | 0,022% |
| atenção 2 ou 3 nos logs | 9.241 | 18,28% | 4,60% | 0,085% |
| escore do BU 2 ou mais | 9.275 | 16,79% | 4,78% | 0,074% |

## 5. Reinícios e bateria

- Seções com o sistema religado durante a votação: 12.271 (9.927 só no 2º turno, 2.344 nos dois); mesma urna 11.085, troca ou contingência 1.186.
- Mediana dos votos antes do primeiro reinício: 116 (47,8% da seção); depois: 128.
  - todas com reinício: contra as vizinhas 0,03 pp (IC95 -0,10 a 0,17; n 12.198); diferença em diferenças -0,03 pp (IC95 -0,06 a 0,01; n 12.198).
  - reinício na mesma urna: contra as vizinhas -0,02 pp (IC95 -0,16 a 0,12; n 11.014); diferença em diferenças -0,03 pp (IC95 -0,07 a 0,01; n 11.014).
  - reinício com troca de urna ou urna de contingência: contra as vizinhas 0,49 pp (IC95 0,07 a 0,91; n 1.185); diferença em diferenças -0,03 pp (IC95 -0,15 a 0,09; n 1.185).
  - reinício só no 2º turno: contra as vizinhas -0,03 pp (IC95 -0,18 a 0,12; n 9.860); diferença em diferenças -0,02 pp (IC95 -0,06 a 0,02; n 9.860).
  - reinício nos dois turnos: contra as vizinhas 0,30 pp (IC95 0,00 a 0,60; n 2.341); diferença em diferenças -0,08 pp (IC95 -0,16 a 0,01; n 2.341).
  - troca de urna ou contingência sem reinício: contra as vizinhas 0,10 pp (IC95 -0,12 a 0,33; n 4.483); diferença em diferenças 0,01 pp (IC95 -0,05 a 0,07; n 4.483).
- Bateria durante a votação: junto com o município 38.395 no 2º turno contra 41.811 no 1º; só nesta urna 11.852 contra 12.668.
  - chuva prevista até 1 mm: 214.741 seções, bateria na votação 12,12%.
  - chuva prevista 1 a 5 mm: 132.778 seções, bateria na votação 18,23%.
  - chuva prevista 5 a 20 mm: 74.182 seções, bateria na votação 9,69%.
  - chuva prevista 20 mm ou mais: 76.172 seções, bateria na votação 6,32%.
  - bateria durante a votação junto com o município: diferença em diferenças -0,07 pp (IC95 -0,10 a -0,05; n 31.104).
  - bateria durante a votação só nesta urna: diferença em diferenças -0,00 pp (IC95 -0,04 a 0,04; n 11.839).
- Chuva de 25/10 medida (fonte: analysis/clima_2t_2026/clima.json: estações CEMADEN a até 50 km (1/d²); sem estação, ECMWF IFS (análise operacional, provisória) via Open-Meteo): 0 pluviômetros com o dia e 0 com as horas de votação; 0 de 6.539 células com estação a até 50 km; 0 seções. INMET: sem dado público de 25/10 (ver fontes/inmet_tentativas_25_10.json).
  - bateria, chuva horas de votação, modelo IFS provisório, seca (0 mm): 78.442 seções, 14,50 (IC95 12,17 a 17,15)%; razão contra a seca n/d.
  - bateria, chuva horas de votação, modelo IFS provisório, fraca (até 5 mm): 244.045 seções, 11,83 (IC95 9,97 a 14,62)%; razão contra a seca 0,816 (IC95 0,640 a 1,063).
  - bateria, chuva horas de votação, modelo IFS provisório, moderada (5 a 20 mm): 150.205 seções, 13,04 (IC95 11,09 a 15,91)%; razão contra a seca 0,899 (IC95 0,702 a 1,176).
  - bateria, chuva horas de votação, modelo IFS provisório, forte (20 a 50 mm): 22.760 seções, 9,53 (IC95 6,88 a 13,29)%; razão contra a seca 0,657 (IC95 0,451 a 0,960).
  - bateria, chuva horas de votação, modelo IFS provisório, muito forte (acima de 50 mm): 617 seções, 5,35%; razão contra a seca 0,369.
  - bateria, chuva horas de votação, modelo IFS provisório, 20 mm ou mais: 23.377 seções, 9,42 (IC95 6,85 a 13,28)%; razão contra a seca 0,650 (IC95 0,449 a 0,951).
  - abstenção, chuva horas de votação, modelo IFS provisório, seca (0 mm): 78.442 seções, 17,4 (IC95 17,0 a 17,9)%; contra a UF 0,43 (IC95 0,11 a 0,86) pp; variação 1º→2º contra a UF -0,04 (IC95 -0,25 a 0,19) pp.
  - abstenção, chuva horas de votação, modelo IFS provisório, fraca (até 5 mm): 244.045 seções, 18,9 (IC95 18,4 a 19,4)%; contra a UF 0,07 (IC95 -0,21 a 0,35) pp; variação 1º→2º contra a UF -0,02 (IC95 -0,12 a 0,08) pp.
  - abstenção, chuva horas de votação, modelo IFS provisório, moderada (5 a 20 mm): 150.206 seções, 19,9 (IC95 19,4 a 20,4)%; contra a UF -0,20 (IC95 -0,51 a 0,08) pp; variação 1º→2º contra a UF -0,01 (IC95 -0,17 a 0,14) pp.
  - abstenção, chuva horas de votação, modelo IFS provisório, forte (20 a 50 mm): 22.761 seções, 18,9 (IC95 18,3 a 19,5)%; contra a UF -0,88 (IC95 -1,44 a -0,27) pp; variação 1º→2º contra a UF 0,40 (IC95 0,25 a 0,55) pp.
  - abstenção, chuva horas de votação, modelo IFS provisório, muito forte (acima de 50 mm): 617 seções, 18,4%; contra a UF -1,40 pp; variação 1º→2º contra a UF 0,64 pp.
  - abstenção, chuva horas de votação, modelo IFS provisório, 20 mm ou mais: 23.378 seções, 18,9 (IC95 18,3 a 19,5)%; contra a UF -0,90 (IC95 -1,44 a -0,33) pp; variação 1º→2º contra a UF 0,40 (IC95 0,26 a 0,54) pp.
  - 1º turno (ERA5): razão da chuva forte contra a seca 2,289 nas horas de votação e 1,572 no dia.

## 6. Metadados

- Série da memória de resultado no dia: 496.267 valores, 41 repetidos em 1.591 seções; pares entre lugares distantes 32 contra 28,7 esperados por acaso num número de 32 bits.
  - 019D22EB: 1.212 seções em ZZ-1; só esse valor em todo o log (inclusive o trecho do 1º turno) em 1.188; contagem confere em 1.212.
  - C928805E: 169 seções em RJ-162; só esse valor em todo o log (inclusive o trecho do 1º turno) em 167; contagem confere em 169.
  - 3482056B: 114 seções em RJ-119; só esse valor em todo o log (inclusive o trecho do 1º turno) em 114; contagem confere em 114.
  - EC793229: 9 seções em AP-12; só esse valor em todo o log (inclusive o trecho do 1º turno) em 8; contagem confere em 9.
  - BB499B0C: 6 seções em RJ-23; só esse valor em todo o log (inclusive o trecho do 1º turno) em 6; contagem confere em 6.
  - F425C0EE: 2 seções em MG-187; só esse valor em todo o log (inclusive o trecho do 1º turno) em 0; contagem confere em 2.
  - 2B93C7E3: 2 seções em MG-187; só esse valor em todo o log (inclusive o trecho do 1º turno) em 0; contagem confere em 2.
  - 8DABC2E6: 2 seções em MG-187; só esse valor em todo o log (inclusive o trecho do 1º turno) em 0; contagem confere em 2.
  - BA2409ED: 2 seções em MG-187; só esse valor em todo o log (inclusive o trecho do 1º turno) em 0; contagem confere em 2.
  - Voto nas seções desses grupos (Brasil, sem exterior, ponderado): diferença em diferenças 0,19 pp (IC95 -0,07 a 0,44; n 306); média simples 0,07 pp (IC95 -0,19 a 0,33; n 306).
    - RJ-162: -0,25 pp (IC95 -0,58 a 0,09; n 169).
    - RJ-119: 0,86 pp (IC95 0,48 a 1,24; n 114).
    - AP-12: -1,72 pp (IC95 -3,20 a -0,25; n 9).
    - RJ-23: -0,37 pp (IC95 -0,97 a 0,22; n 6).
    - MG-187: 2,60 pp (IC95 0,28 a 4,92; n 2).
    - MG-187: -1,83 pp (IC95 -7,60 a 3,94; n 2).
    - MG-187: 2,56 pp (IC95 -0,77 a 5,89; n 2).
    - MG-187: -0,59 pp (IC95 -1,75 a 0,57; n 2).
  - Exterior, separado (1.212 seções): cinco vizinhas n/d; três vizinhas (sensibilidade) -1,60 pp (IC95 -2,05 a -1,15; n 123). Exterior separado: a vizinhança é a cidade do consulado e, nos grupos do exterior, quase todas as seções da cidade têm a mesma série, sobrando poucas vizinhas; o 1º turno por seção vem do BU do metadados (secoes.json não cobre o exterior).
- Carga registrada: 498.344 antes do 1º turno, 812 entre os turnos, 6 no dia ou com data posterior.

## 7. Escore integrado

- Escore do BU ≥ 2: 9.275; atenção dos logs ≥ 2: 9.444; as duas: 822 (esperado se fossem independentes: 174,8).
- Voto nessas seções: diferença em diferenças -0,02 pp (IC95 -0,18 a 0,15; n 820).

pede explicação, não prova irregularidade.
