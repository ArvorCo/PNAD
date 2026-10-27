# Ângulo do pianista no 2º turno de 2026: o log da célula

Gerado em 2026-10-27T00:25:44+00:00. Sinal pede explicação, não prova irregularidade.

## Pergunta

A célula comparecimento +5 pp e salto de biometria tem no log a marca que a liberação de eleitor ausente deixaria?

## Resposta

- A marca não aparece. Das 1.324 seções da célula, todas com log relido nos dois turnos, 0 têm a marca completa no 2º turno e 0 no 1º. Nas vizinhas sorteadas do mesmo município, 8 de 12.687; nas seções com salto de biometria sem alta de comparecimento, 5 de 7.628.
- A parcela sem biometria reconhecida sobe +6,85 pp contra a própria seção no 1º turno, porque é assim que a célula foi escolhida. Ela não se concentra no fim do dia: o excesso da última hora nas habilitações sem biometria, em diferença em diferenças contra as vizinhas, é −0,13 (−0,58 a +0,26) pp. A parcela de todos os votos dados na última hora caiu mais na célula do que nas vizinhas, −3,12 (−3,86 a −2,40) pp.
- Há 19 seções da célula com sequência de habilitações sem biometria improvável sob ordem aleatória. Nelas o intervalo entre votos sem biometria é 1,34 vez o da própria seção na mediana (0 com metade ou menos), e a habilitação sem biometria leva 67 s contra 16 s da biométrica: é o ritmo lento de quem tentou a digital e foi liberado pelo documento, o desenho de leitor falhando, não de digitação em série.
- Contra as seções com o mesmo salto de biometria e sem alta de comparecimento, a célula não se distingue no log: habilitação sem biometria −0,77 (−1,66 a +0,11) s, improbabilidade da sequência −0,03 (−0,07 a +0,03).
- O voto já medido na mesma célula: −2,50 pp na fatia de Flávio contra as vizinhas (ep 0,24) e +0,08 pp em diferença em diferenças contra o 1º turno (ep 0,05).

## Método

- Célula: 1.324 seções em 778 municípios (`pianista` de `secoes_linhas`: comparecimento ≥ +5 pp e salto da parcela sem biometria reconhecida contra a própria seção no 1º turno).
- Controles: vizinhas sem sinal do mesmo município (12.687, até 10 por seção da célula, semente 20261026); salto de biometria sem alta de comparecimento (7.628); a própria seção no 1º turno.
- Fonte: logs originais dos dois turnos relidos com o leitor versão 12 (`apuracao_logs.parser`); a lista de ciclos que o leitor monta é capturada e reduzida a agregados por seção. Nenhuma sequência individual é gravada. Hora de Brasília pela regra de `logs_cadencia` (8 menos a hora modal do primeiro cômputo do município).
- Erros de leitura: 2T 0, 1T 0.
- Diferença em diferenças: 2T menos 1T da mesma seção; contra vizinhas, média por município (célula menos vizinhas) ponderada pelo n da célula; contra salto sem alta, média da célula menos média do controle. IC de 95% por bootstrap de municípios (2.000 reamostragens).

### Regras

- `nbio`: habilitação sem biometria reconhecida = ano de nascimento (biometria cadastrada não reconhecida) + sem biometria cadastrada, pelo log
- `ultima_hora`: cômputos a partir das 16:00 de Brasília
- `concentra`: ≥ 5 habilitações sem biometria na última hora e parcela delas na última hora ≥ 20 pp acima da parcela de todos os votos da seção na última hora
- `rajada`: maior sequência de habilitações sem biometria seguidas ≥ 5 e chance dessa sequência sob ordem aleatória < 1% (1 − exp(−n(1−p)p^k))
- `ritmo`: intervalo mediano entre cômputos seguidos sem biometria ≤ metade do intervalo mediano da seção, ou coeficiente de variação ≤ 0,25 com ≥ 8 pares
- `hab_curta`: tempo mediano de habilitação sem biometria ≤ o da biométrica na mesma seção (o fluxo legítimo passa por tentativas de digital antes do ano de nascimento)
- `sem_explicacao`: sem reinício na votação, sem contingência, uma urna no log
- `marca`: (concentra ou rajada) e (ritmo ou hab_curta) e sem_explicacao
- `marca_forte`: concentra e rajada e ritmo e hab_curta e sem_explicacao
- `marca_nova`: marca no 2º turno e não no 1º, na mesma seção
- `forca`: excesso da última hora/10 + min(10, −log10 chance da sequência)/2 + 1 se ritmo + 1 se hab_curta (o comprimento cru da sequência fica fora: seção em que quase ninguém foi reconhecido tem sequência longa e provável)
- `leitor_parado`: parcela sem biometria reconhecida ≥ 50% no 2º turno: assinatura de leitor que não reconhece ninguém, descritiva
- `vizinhas`: escore 0 no mesmo município, até 10 por seção da célula

## Números

| Métrica do log | Célula 2T | Célula 1T | DiD contra vizinhas | DiD contra salto sem alta | Célula 2T menos 1T |
|---|---|---|---|---|---|
| parcela sem biometria reconhecida (%) | 22,90 | 16,05 | +6,74 (+6,50 a +7,05) | +0,30 (+0,05 a +0,62) | +6,85 (+6,59 a +7,13) |
| excesso da última hora nas habilitações sem biometria (pp) | −0,14 | −0,36 | −0,13 (−0,58 a +0,26) | +0,17 (−0,25 a +0,58) | +0,22 (−0,23 a +0,61) |
| parcela de todos os votos na última hora (%) | 4,64 | 15,01 | −3,12 (−3,86 a −2,40) | −4,11 (−4,96 a −3,27) | −10,37 (−11,29 a −9,38) |
| maior sequência sem biometria (votos seguidos) | 4,26 | 2,87 | +1,43 (+0,96 a +2,03) | +0,25 (−0,26 a +0,86) | +1,40 (+0,93 a +1,97) |
| improbabilidade da sequência (−log10 da chance) | 0,34 | 0,28 | +0,08 (+0,03 a +0,13) | −0,03 (−0,07 a +0,03) | +0,07 (+0,02 a +0,12) |
| intervalo sem biometria / intervalo da seção | 1,53 | 1,43 | −0,04 (−0,07 a 0,00) | +0,06 (+0,02 a +0,09) | +0,03 (0,00 a +0,06) |
| habilitação sem biometria, mediana (s) | 56,99 | 57,03 | +3,90 (+2,83 a +4,81) | −0,77 (−1,66 a +0,11) | −0,05 (−1,17 a +0,97) |
| habilitação, mediana de todos (s) | 18,10 | 17,83 | +0,77 (+0,53 a +0,99) | −0,01 (−0,26 a +0,23) | +0,27 (−0,05 a +0,59) |
| reinícios durante a votação | 0,13 | 0,30 | −0,16 (−0,27 a −0,07) | −0,16 (−0,25 a −0,07) | −0,17 (−0,27 a −0,09) |
| seções com a marca (%) | 0,00 | 0,00 | +0,01 (−0,07 a +0,10) | −0,01 (−0,11 a +0,07) | 0,00 (0,00 a 0,00) |

Componentes da marca no 2º turno (seções):

| Grupo | Seções | Concentra | Rajada | Ritmo | Hab. curta | Janela | Marca | Marca nova | Leitor parado |
|---|---|---|---|---|---|---|---|---|---|
| Célula | 1.324 | 1 | 19 | 28 | 23 | 19 | 0 | 0 | 19 |
| Vizinhas | 12.687 | 3 | 49 | 82 | 461 | 52 | 8 | 8 | 36 |
| Salto sem alta | 7.628 | 3 | 116 | 133 | 126 | 117 | 5 | 5 | 86 |

## As 20 seções da célula com a marca mais forte

Seções da célula com a marca completa: 0. A lista ordena pela marca e depois pela força declarada nas regras.

| UF | Município | Zona | Seção | Aptos | Sem biometria 2T (1T) | Na última hora: sem bio / todos | Maior sequência (chance) | Intervalo sem bio / seção (s) | Habilitação sem bio / bio (s) | Componentes | Politize-se |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BA | São Francisco do Conde | 162 | 59 | 394 | 19,4% (11,0%) | 0,0% / 4,4% | 20 (< 1 em 1 milhão) | 119 / 61 | 81 / 18 | rajada, ritmo | politizese.html#uf=BA&zona=162&secao=59 |
| GO | Corumbaíba | 5 | 65 | 343 | 47,0% (23,4%) | 11,1% / 5,2% | 38 (< 1 em 1 milhão) | 108 / 84 | 67 / 18 | rajada | politizese.html#uf=GO&zona=5&secao=65 |
| PE | Agrestina | 86 | 15 | 382 | 22,9% (15,4%) | 8,3% / 3,8% | 21 (< 1 em 1 milhão) | 130 / 50 | 83 / 16 | rajada | politizese.html#uf=PE&zona=86&secao=15 |
| MG | Mariana | 171 | 128 | 317 | 38,0% (24,0%) | 5,0% / 3,0% | 35 (< 1 em 1 milhão) | 106 / 68 | 49 / 17 | rajada | politizese.html#uf=MG&zona=171&secao=128 |
| PR | Iporã | 97 | 102 | 260 | 23,7% (9,9%) | 3,9% / 6,0% | 37 (< 1 em 1 milhão) | 99 / 87 | 71 / 15 | rajada | politizese.html#uf=PR&zona=97&secao=102 |
| BA | Teolândia | 197 | 50 | 347 | 11,5% (5,2%) | 34,3% / 5,6% | 7 (0,01%) | 112 / 60 | 40 / 13 | concentra, rajada | politizese.html#uf=BA&zona=197&secao=50 |
| BA | Lauro de Freitas | 180 | 149 | 391 | 76,2% (22,5%) | 5,3% / 4,1% | 96 (< 1 em 1 milhão) | 88 / 79 | 60 / 19 | rajada | politizese.html#uf=BA&zona=180&secao=149 |
| RJ | Rio de Janeiro | 214 | 325 | 413 | 76,1% (66,4%) | 1,3% / 4,2% | 76 (< 1 em 1 milhão) | 76 / 77 | 54 / 14 | rajada | politizese.html#uf=RJ&zona=214&secao=325 |
| RJ | Rio de Janeiro | 167 | 40 | 411 | 42,2% (26,5%) | 1,6% / 3,6% | 24 (< 1 em 1 milhão) | 87 / 72 | 58 / 16 | rajada | politizese.html#uf=RJ&zona=167&secao=40 |
| RJ | Rio de Janeiro | 9 | 262 | 437 | 68,7% (21,1%) | 1,3% / 2,6% | 39 (0,00%) | 83 / 79 | 61 / 17 | rajada | politizese.html#uf=RJ&zona=9&secao=262 |
| MG | Viçosa | 282 | 305 | 55 | 19,6% (13,0%) | 30,0% / 9,8% | 2 (79,0%) | 373 / 423 | 68 / 25 | nenhum | politizese.html#uf=MG&zona=282&secao=305 |
| SP | Franco da Rocha | 192 | 205 | 395 | 15,8% (10,1%) | 2,2% / 2,8% | 8 (0,01%) | 135 / 67 | 72 / 19 | rajada | politizese.html#uf=SP&zona=192&secao=205 |
| MG | Três Corações | 272 | 52 | 392 | 35,6% (30,3%) | 6,2% / 4,7% | 9 (1,9%) | 73 / 58 | 13 / 13 | hab_curta | politizese.html#uf=MG&zona=272&secao=52 |
| MG | Turmalina | 336 | 26 | 183 | 35,2% (29,3%) | 4,4% / 3,1% | 7 (5,4%) | 156 / 124 | 15 / 15 | hab_curta | politizese.html#uf=MG&zona=336&secao=26 |
| RS | Piratini | 78 | 26 | 81 | 14,9% (6,7%) | 20,0% / 4,5% | 2 (72,0%) | s/d / 132 | 70 / 21 | nenhum | politizese.html#uf=RS&zona=78&secao=26 |
| MG | Monte Carmelo | 181 | 51 | 274 | 42,7% (34,9%) | 5,2% / 4,0% | 8 (13,0%) | 106 / 90 | 14 / 14 | hab_curta | politizese.html#uf=MG&zona=181&secao=51 |
| PR | Cornélio Procópio | 26 | 35 | 261 | 21,9% (15,9%) | 2,2% / 3,8% | 8 (0,09%) | 166 / 96 | 106 / 19 | rajada | politizese.html#uf=PR&zona=26&secao=35 |
| PB | São Sebastião do Umbuzeiro | 29 | 96 | 283 | 15,3% (8,6%) | 5,3% / 11,7% | 4 (11,0%) | 133 / 79 | 77 / 14 | ritmo | politizese.html#uf=PB&zona=29&secao=96 |
| PR | Umuarama | 89 | 335 | 319 | 16,0% (10,9%) | 7,1% / 8,8% | 4 (14,0%) | 120 / 71 | 60 / 13 | ritmo | politizese.html#uf=PR&zona=89&secao=335 |
| MS | Antônio João | 52 | 8 | 311 | 20,7% (12,2%) | 4,1% / 2,5% | 4 (29,0%) | 166 / 88 | 64 / 16 | ritmo | politizese.html#uf=MS&zona=52&secao=8 |

## Limites

- O log registra como cada eleitor foi liberado e quando, não quem votou. Um mesário que digitasse o ano de nascimento no ritmo normal, depois de tentativas simuladas de digital, não deixaria marca no log; a ausência da marca reduz, não elimina, a hipótese.
- A célula foi escolhida pelo salto da parcela sem biometria: métricas de nível dessa parcela crescem por construção. Os testes informativos são os de tempo, ritmo e concentração.
- O que decidiria: a ata da mesa (liberações por ano de nascimento, troca de urna, ocorrência, fila às 17h) e o caderno de votação (assinatura de cada eleitor liberado pelo documento; nome de falecido, de quem estava fora do país ou justificou).
- Bootstrap entre municípios não incorpora o sorteio das vizinhas nem o desenho do pleito. As regras da marca foram declaradas antes da contagem e não foram ajustadas; a fórmula de força, que só ordena a lista, foi revista uma vez para tirar o comprimento cru da sequência (seção em que quase ninguém foi reconhecido liderava por ter sequência longa e provável).
