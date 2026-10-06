# Análise por seção (boletins de urna), presidente, 1º turno de 2026

Gerado em 2026-10-06T05:43:06Z por `scripts/apuracao-2026-secoes.py`. Dados em `analysis/apuracao_2026/dados/secoes.json` (contrato em `analysis/apuracao_2026/CONTRATO_SECOES.md`).

> Seção atípica é seção que pede explicação, não indício de irregularidade. O que resolve cada caso é documento: ata da mesa, log da urna e plano de alocação das urnas do TRE.

## Cobertura

- Seções no cadastro do TSE (cs): 517.179, das quais 17.931 agregadas (sem boletim próprio).
- Boletins lidos: 499.187; válidos para a análise: 497.890.
- Fora: 61 seções, seção principal sem boletim de urna no banco (ainda não coletada ou sem arquivo).
- Fora: 1.297 seções, soma das seções diferente do arquivo de zona do TSE.
- Nas seções válidas: Flávio 47,03% e Lula 45,17% dos válidos, 118.978.615 válidos.
- Conferência com o resultado nacional do TSE: soma de todos os boletins menos o arquivo nacional do TSE: comparecimento -5.507; flavio -2.369; lula -2.252.

## A. Seções com 90% ou mais para um candidato

Quem espera achar seções novas de 90% encontra as velhas: 2.021 de 2.441 seções casadas de Lula já estavam acima de 90% em 2022.

| candidato | limiar | seções | com 100+ votantes | aptos | % das seções |
|---|---|---|---|---|---|
| Lula | 90% | 3.686 | 3.281 | 873.711 | 0,74 |
| Lula | 95% | 851 | 716 | 191.500 | 0,17 |
| Lula | 100% | 38 | 14 | 4.577 | 0,01 |
| Flávio | 90% | 186 | 151 | 42.580 | 0,04 |
| Flávio | 95% | 22 | 13 | 3.832 | 0,00 |
| Flávio | 100% | 2 | 0 | 192 | 0,00 |

Por tamanho (votantes da seção):

| faixa | seções | Lula ≥ 90% | % | Flávio ≥ 90% | % |
|---|---|---|---|---|---|
| 1–49 | 599 | 59 | 9,85 | 5 | 0,83 |
| 50–99 | 4.337 | 346 | 7,98 | 30 | 0,69 |
| 100–199 | 71.724 | 1.548 | 2,16 | 70 | 0,10 |
| 200–299 | 342.349 | 1.557 | 0,45 | 68 | 0,02 |
| 300–399 | 78.655 | 174 | 0,22 | 13 | 0,02 |
| 400+ | 225 | 2 | 0,89 | 0 | 0,00 |

- Lula: 3.686 seções em 90% ou mais; o resto da zona dá 76,3% a Lula (mediana) e o excesso da seção sobre a zona é 17,1 pontos (mediana); 1.332 seções ficam 20 pontos ou mais acima da própria zona.
- Flávio: 186 seções em 90% ou mais; o resto da zona dá 70,7% a Flávio (mediana) e o excesso da seção sobre a zona é 21,1 pontos (mediana); 104 seções ficam 20 pontos ou mais acima da própria zona.

Por tipo de local (inferência por palavra-chave; regras no JSON):

| tipo | seções | Lula ≥ 90% | % do tipo | Flávio ≥ 90% | % do tipo |
|---|---|---|---|---|---|
| escola ou universidade | 311.906 | 229 | 0,07 | 48 | 0,02 |
| outro | 119.996 | 85 | 0,07 | 43 | 0,04 |
| zona rural | 61.296 | 2.659 | 4,34 | 78 | 0,13 |
| aldeia ou terra indígena | 1.428 | 565 | 39,57 | 3 | 0,21 |
| exterior | 1.309 | 6 | 0,46 | 7 | 0,53 |
| assentamento | 1.039 | 56 | 5,39 | 4 | 0,38 |
| quilombo | 436 | 62 | 14,22 | 0 | 0,00 |
| unidade prisional ou socioeducativa | 293 | 24 | 8,19 | 3 | 1,02 |
| voto em trânsito | 152 | 0 | 0,00 | 0 | 0,00 |
| hospital ou unidade de saúde | 34 | 0 | 0,00 | 0 | 0,00 |

Cruzamento com as 50 zonas mais atípicas de `anomalias.json`: 50 estão na base, 4 têm ao menos uma seção de 90%. Taxa de seções com Lula em 90% ou mais: 0,63% nessas zonas e 0,74% nas demais; Flávio: 0,00% e 0,04%.

Mesma seção em 2022 (mesma UF, município, zona e número de seção, e mesmo nome do local de votação nos dois cadastros (sem acento e sem espaços repetidos)): 356.245 de 497.889 seções casadas.
- Lula em 90% ou mais em 2026, casadas: 2.441; Lula já tinha 90% ou mais no 1º turno de 2022 em 2.021 e no 2º turno em 2.286; mediana de 2022 93,3% (1º turno); variação mediana -0,3 pontos.
- Flávio em 90% ou mais em 2026, casadas: 124; Bolsonaro já tinha 90% ou mais no 1º turno de 2022 em 27 e no 2º turno em 61; mediana de 2022 85,6% (1º turno); variação mediana 6,2 pontos.

Amostras (as de maior excesso sobre a zona, 100 votantes ou mais):

- GUARANTÃ DO NORTE (MT), zona 44, seção 284, ALDEIA - SANKORASSAN: Lula 144, Flávio 3 de 150 válidos (171 aptos, 150 votantes, UE2020); Lula 96,0% na seção e 15,6% na zona. Aldeia ou terra indígena (inferido pelo cadastro do local).
- MARCELÂNDIA (MT), zona 32, seção 279, ESCOLA ESTADUAL INDÍGENA KAMADU: Lula 184, Flávio 2 de 190 válidos (231 aptos, 190 votantes, UE2020); Lula 96,8% na seção e 18,9% na zona. Aldeia ou terra indígena (inferido pelo cadastro do local).
- CONFRESA (MT), zona 28, seção 200, ESCOLA ESTADUAL TAPI'ITAWA: Lula 296, Flávio 0 de 297 válidos (315 aptos, 297 votantes, UE2022); Lula 99,7% na seção e 21,9% na zona. Aldeia ou terra indígena (inferido pelo cadastro do local).
- CONFRESA (MT), zona 28, seção 158, ESCOLA ESTADUAL TAPI'ITAWA: Lula 119, Flávio 1 de 120 válidos (133 aptos, 120 votantes, UE2022); Lula 99,2% na seção e 21,9% na zona. Aldeia ou terra indígena (inferido pelo cadastro do local).
- QUERÊNCIA (MT), zona 53, seção 163, AUDITÓRIO-SEDE DA ALDEIA KHIKATXI: Lula 247, Flávio 3 de 255 válidos (313 aptos, 259 votantes, UE2022); Lula 96,9% na seção e 21,4% na zona. Aldeia ou terra indígena (inferido pelo cadastro do local).
- ALTO ALEGRE (RR), zona 3, seção 226, POSTO DE SAÚDE DA SESAI - SIKAMABIU: Lula 235, Flávio 3 de 238 válidos (304 aptos, 238 votantes, UE2022); Lula 98,7% na seção e 23,9% na zona. Aldeia ou terra indígena (inferido pelo cadastro do local).
- SÃO FÉLIX DO XINGU (PA), zona 53, seção 218, EM INDIGENA CAPITÃO BEP NOX: Lula 214, Flávio 1 de 216 válidos (318 aptos, 221 votantes, UE2022); Lula 99,1% na seção e 23,6% na zona. Aldeia ou terra indígena (inferido pelo cadastro do local).
- SÃO FÉLIX DO XINGU (PA), zona 53, seção 217, EM INDIGENA KUBENHIKANHTI: Lula 130, Flávio 1 de 131 válidos (203 aptos, 132 votantes, UE2022); Lula 99,2% na seção e 23,6% na zona. Aldeia ou terra indígena (inferido pelo cadastro do local).
- ITAPIPOCA (CE), zona 17, seção 554, SALÃO COMUNITÁRIO DO SÍTIO SÃO JOSÉ: Lula 10, Flávio 150 de 163 válidos (186 aptos, 168 votantes, UE2020); Flávio 92,0% na seção e 24,8% na zona. Sem regra estrutural acionada: comparar com ata e log da seção.
- UIRAMUTÃ (RR), zona 7, seção 56, ESCOLA MUNICIPAL INDÍGENA TANCREDO NEVES: Lula 25, Flávio 293 de 318 válidos (366 aptos, 321 votantes, UE2022); Flávio 92,1% na seção e 29,9% na zona. Aldeia ou terra indígena (inferido pelo cadastro do local).
- URUÇUÍ (PI), zona 14, seção 54, UNIDADE ESCOLAR DA PAZ - NOVA SANTA ROSA: Lula 9, Flávio 157 de 170 válidos (221 aptos, 173 votantes, UE2020); Flávio 92,3% na seção e 35,0% na zona. Zona rural (inferido pelo cadastro do local).
- LÁBREA (AM), zona 12, seção 116, E. M. JULIO RODRIGUES COUTINHO: Lula 3, Flávio 123 de 130 válidos (174 aptos, 130 votantes, UE2020); Flávio 94,6% na seção e 38,6% na zona. Assentamento (inferido pelo cadastro do local).
- PORTEL (PA), zona 44, seção 187, EMEF PAULO DE TARSO: Lula 15, Flávio 162 de 178 válidos (221 aptos, 182 votantes, UE2022); Flávio 91,0% na seção e 35,1% na zona. Zona rural (inferido pelo cadastro do local).
- LÁBREA (AM), zona 12, seção 111, E. M. JULIO RODRIGUES COUTINHO: Lula 15, Flávio 274 de 292 válidos (361 aptos, 295 votantes, UE2020); Flávio 93,8% na seção e 38,6% na zona. Assentamento (inferido pelo cadastro do local).
- MANICORÉ (AM), zona 16, seção 116, E. E. SANTO ANTONIO DO MATUPI: Lula 15, Flávio 238 de 257 válidos (327 aptos, 260 votantes, UE2022); Flávio 92,6% na seção e 38,1% na zona. Zona rural (inferido pelo cadastro do local); urna de reserva (seção).
- MANICORÉ (AM), zona 16, seção 121, E. E. SANTO ANTONIO DO MATUPI: Lula 13, Flávio 213 de 230 válidos (323 aptos, 233 votantes, UE2022); Flávio 92,6% na seção e 38,1% na zona. Zona rural (inferido pelo cadastro do local).

## B. Mistura gaussiana (k = 5), cinco partes

- Com as cinco partes, a associação entre grupo e região sobe pouco (V de Cramér de 0,24, contra 0,21 com as 15 partes; 0,26 com a UF) e fica abaixo de 0,3: cada grupo ainda mistura regiões.
- Cinco partes não bastaram: três dos cinco grupos são artefatos da contagem inteira, não perfil de seção: o 1 (sem voto branco; 24.891 seções), o 3 (mesmo número de brancos e de nulos; 44.447 seções) e o 4 (sem voto nulo; 5.202 seções). Brancos e nulos são poucos votos por seção (mediana de 4 brancos e 7 nulos); no logaritmo, o zero vira um degrau de 3,5 unidades até o primeiro voto e o empate vira uma razão exata de 1, e a mistura gasta um componente em cada padrão. 1,34% das células são zero (5,31% das seções sem voto branco e 1,35% das seções sem voto nulo), e 8,93% das seções têm o mesmo número de brancos e de nulos.
- Os outros dois, com 85,0% das seções, são perfis de voto: o 2 (Lula 52,1% e Flávio 40,9% dos válidos; Nordeste 46% das seções) e o 5 (Lula 37,8% e Flávio 53,4% dos válidos; Sudeste 59% das seções). É a divisão que o mapa por zona já mostra: o grupo em que Lula lidera tem 46% das seções no Nordeste, e o grupo em que Flávio lidera, 59% no Sudeste. Nessa parte, a mistura não acrescenta ao mapa.
- No espaço das log-razões, uma parte pequena pesa tanto quanto uma grande: passar de 4 para 8 brancos afasta a seção tanto quanto passar de 101 para 202 votos em Lula. Por isso o primeiro eixo da projeção é o voto branco (carga 0,89), não a disputa entre os finalistas.
- Grupo 1: sem voto branco; terceiros baixos, Lula alto, Flávio baixo; Nordeste 34% e Norte 28% das seções; 24.891 seções (5,0%). Centro: Lula 51,7% e Flávio 42,3% dos válidos; abstenção 20,6%, brancos 0,0%, nulos 2,1% e terceiros 4,5% do eleitorado.
- Grupo 2: Lula alto, brancos baixos, Flávio baixo; Nordeste 46% e Sudeste 28% das seções; 225.669 seções (45,3%). Centro: Lula 52,1% e Flávio 40,9% dos válidos; abstenção 20,4%, brancos 1,1%, nulos 2,7% e terceiros 5,2% do eleitorado.
- Grupo 3: mesmo número de brancos e de nulos; perto da média nacional; Sudeste 40% e Nordeste 21% das seções; 44.447 seções (8,9%). Centro: Lula 41,3% e Flávio 50,6% dos válidos; abstenção 20,9%, brancos 1,5%, nulos 1,5% e terceiros 6,0% do eleitorado.
- Grupo 4: sem voto nulo; Flávio alto, Lula baixo; Sul 36% e Sudeste 18% das seções; 5.202 seções (1,0%). Centro: Lula 36,4% e Flávio 56,2% dos válidos; abstenção 20,8%, brancos 1,3%, nulos 0,0% e terceiros 5,6% do eleitorado.
- Grupo 5: brancos altos, Lula baixo, Flávio alto; Sudeste 59% das seções; 197.681 seções (39,7%). Centro: Lula 37,8% e Flávio 53,4% dos válidos; abstenção 21,3%, brancos 2,0%, nulos 2,2% e terceiros 6,5% do eleitorado.
- O grupo de menor densidade e maior dispersão é o 4 (sem voto nulo; Flávio alto, Lula baixo; Sul 36% e Sudeste 18% das seções); as 20 seções menos prováveis dele vêm com o que provavelmente as explica.
- Com zero trocado por meio voto, e não por 0,0001, o V de Cramér entre grupo e região é 0,39 e o índice de Rand ajustado contra a partição principal, 0,20.
- Na projeção, o componente 1 (54,5% da variância) opõe brancos (carga 0,89) a Lula (−0,28); o componente 2 (27,5% da variância) opõe nulos (carga 0,79) a Flávio (−0,54). Os centros dos grupos se afastam mais no componente 1 (variância ponderada dos centros 1,01, contra 0,25 no outro). Um corte no componente 1 separa as seções sem voto branco (5,3% do total) com acerto balanceado de 100,0%. Um corte no componente 2 separa as seções sem voto nulo (1,3% do total) com acerto balanceado de 99,7%.
- O EM convergiu nas 32 partidas (16 sementes, inicializações kmeans e k-means++, 10 partidas internas cada; critério do sklearn: variação da log-verossimilhança média abaixo de 0,0001, de 19 a 77 iterações). Refeita com tolerância 0,000001 e até 2.000 iterações, a melhor partida foi de 51 para 105 iterações e a log-verossimilhança média subiu 0,000688 por seção, mas a partição mudou (índice de Rand ajustado de 0,79 entre as duas): pelo critério declarado, o padrão parava cedo, e o ajuste publicado é o apertado. 2 de 32 partidas chegaram ao mesmo máximo, a 0,001 por seção (kmeans: 2 de 16; k-means++: 0 de 16). A partição escolhida é instável: índice de Rand ajustado médio de 0,78 contra as partidas que chegam ao máximo e de 0,18 contra as demais. O V de Cramér entre grupo e região fica entre 0,21 e 0,41 em todas as partidas.

Escolha de k (juízo editorial): k = 5, escolha do autor, mantida quando a mistura passou de 15 para cinco partes (06/10/2026; antes de 06/10, k = 3). O BIC prefere k = 5. A escolha das cinco partes também é do autor.

Partes: votos de Lula, de Flávio, brancos, nulos e abstenções da seção, divididos pelos aptos da eleição federal e renormalizados para somar 1 (composição fechada sobre as cinco partes; o voto em terceiros fica fora). Método: log-razão centrada (CLR) das cinco partes fechadas, com zero trocado por 0,0001 antes do log; a mistura é ajustada nas quatro coordenadas ortonormais do subespaço de soma zero (ILR), rotação que preserva Mahalanobis e densidade relativa.

Zeros: 1,34% das células; 31.688 seções com ao menos uma parte zerada.

| parte | seções com zero | % das seções |
|---|---|---|
| lula | 9 | 0,00 |
| flavio | 82 | 0,02 |
| brancos | 26.460 | 5,31 |
| nulos | 6.713 | 1,35 |
| abstencao | 15 | 0,00 |

Convergência e máximos locais:

O EM convergiu nas 32 partidas (16 sementes, inicializações kmeans e k-means++, 10 partidas internas cada; critério do sklearn: variação da log-verossimilhança média abaixo de 0,0001, de 19 a 77 iterações). Refeita com tolerância 0,000001 e até 2.000 iterações, a melhor partida foi de 51 para 105 iterações e a log-verossimilhança média subiu 0,000688 por seção, mas a partição mudou (índice de Rand ajustado de 0,79 entre as duas): pelo critério declarado, o padrão parava cedo, e o ajuste publicado é o apertado. 2 de 32 partidas chegaram ao mesmo máximo, a 0,001 por seção (kmeans: 2 de 16; k-means++: 0 de 16). A partição escolhida é instável: índice de Rand ajustado médio de 0,78 contra as partidas que chegam ao máximo e de 0,18 contra as demais.

| semente | inicialização | log-veross. média | convergiu | iterações | ARI com a escolhida | V de Cramér (região) |
|---|---|---|---|---|---|---|
| 20261005 | kmeans | -2,7911 | sim | 33 | 0,136 | 0,284 |
| 20261006 | kmeans | -2,7911 | sim | 33 | 0,136 | 0,284 |
| 20261007 | kmeans | -2,7911 | sim | 33 | 0,136 | 0,284 |
| 20261008 | kmeans | -2,7911 | sim | 34 | 0,135 | 0,283 |
| 20261009 | kmeans | -2,5972 | sim | 19 | 0,489 | 0,313 |
| 20261010 | kmeans | -2,7911 | sim | 33 | 0,136 | 0,284 |
| 20261011 | kmeans | -2,7911 | sim | 33 | 0,136 | 0,284 |
| 20261012 | kmeans | -2,7911 | sim | 33 | 0,136 | 0,284 |
| 20261013 | kmeans | -2,7911 | sim | 34 | 0,135 | 0,283 |
| 20261014 | kmeans | -2,7911 | sim | 33 | 0,136 | 0,284 |
| 20261015 | kmeans | -2,7911 | sim | 33 | 0,136 | 0,284 |
| 20261016 | kmeans | -2,5875 | sim | 48 | 0,774 | 0,248 |
| 20261017 | kmeans | -2,5874 | sim | 51 | 0,787 | 0,248 |
| 20261018 | kmeans | -2,7911 | sim | 34 | 0,135 | 0,283 |
| 20261019 | kmeans | -2,7776 | sim | 59 | 0,184 | 0,215 |
| 20261020 | kmeans | -2,7911 | sim | 33 | 0,136 | 0,284 |
| 20261005 | k-means++ | -2,7803 | sim | 67 | 0,174 | 0,378 |
| 20261006 | k-means++ | -2,7803 | sim | 37 | 0,187 | 0,395 |
| 20261007 | k-means++ | -2,7802 | sim | 40 | 0,214 | 0,396 |
| 20261008 | k-means++ | -2,7799 | sim | 33 | 0,186 | 0,388 |
| 20261009 | k-means++ | -2,7827 | sim | 25 | 0,117 | 0,299 |
| 20261010 | k-means++ | -2,7797 | sim | 24 | 0,182 | 0,387 |
| 20261011 | k-means++ | -2,7801 | sim | 38 | 0,179 | 0,387 |
| 20261012 | k-means++ | -2,7804 | sim | 61 | 0,230 | 0,407 |
| 20261013 | k-means++ | -2,7902 | sim | 53 | 0,130 | 0,267 |
| 20261014 | k-means++ | -2,7799 | sim | 29 | 0,180 | 0,387 |
| 20261015 | k-means++ | -2,7795 | sim | 29 | 0,191 | 0,389 |
| 20261016 | k-means++ | -2,7623 | sim | 43 | 0,216 | 0,265 |
| 20261017 | k-means++ | -2,5980 | sim | 24 | 0,441 | 0,313 |
| 20261018 | k-means++ | -2,7623 | sim | 47 | 0,161 | 0,243 |
| 20261019 | k-means++ | -2,7776 | sim | 77 | 0,184 | 0,215 |
| 20261020 | k-means++ | -2,7795 | sim | 28 | 0,179 | 0,383 |

BIC (menor é melhor; cada k com o melhor ajuste das mesmas sementes, inicialização kmeans; k = 5 com as duas inicializações):

- k = 3: BIC 2.877.935,4, log-verossimilhança média -2,8896
- k = 4: BIC 2.804.984,5, log-verossimilhança média -2,8161
- k = 5: BIC 2.576.776,2, log-verossimilhança média -2,5867

| grupo | rótulo | seções | Lula % válidos | Flávio % válidos | abstenção % | brancos % | nulos % | terceiros % | log-veross. média | log det Σ |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | sem voto branco; terceiros baixos, Lula alto, Flávio baixo; Nordeste 34% e Norte 28% das seções | 24.891 | 51,7 | 42,3 | 20,6 | 0,00 | 2,07 | 4,5 | -4,96 | -7,4 |
| 2 | Lula alto, brancos baixos, Flávio baixo; Nordeste 46% e Sudeste 28% das seções | 225.669 | 52,1 | 40,9 | 20,4 | 1,08 | 2,67 | 5,2 | -3,20 | -6,0 |
| 3 | mesmo número de brancos e de nulos; perto da média nacional; Sudeste 40% e Nordeste 21% das seções | 44.447 | 41,3 | 50,6 | 20,9 | 1,50 | 1,50 | 6,0 | 0,75 | -16,6 |
| 4 | sem voto nulo; Flávio alto, Lula baixo; Sul 36% e Sudeste 18% das seções | 5.202 | 36,4 | 56,2 | 20,8 | 1,28 | 0,00 | 5,6 | -6,75 | -7,0 |
| 5 | brancos altos, Lula baixo, Flávio alto; Sudeste 59% das seções | 197.681 | 37,8 | 53,4 | 21,3 | 2,00 | 2,18 | 6,5 | -2,23 | -7,7 |

V de Cramér entre grupo e região: 0,238; entre grupo e UF: 0,256.

Grupo mais anômalo: 4. Critério: soma dos postos de menor log-verossimilhança média e de maior dispersão (log-determinante da covariância); empate decidido pela menor log-verossimilhança média. Amostras: as 20 seções de menor log-verossimilhança dentro do componente.

- POTIM (SP), zona 190, seção 154, PENITENCIÁRIA I DE POTIM: Lula 17, Flávio 3 de 22 válidos (24 aptos, 24 votantes, UE2015). Unidade prisional ou socioeducativa (inferido pelo cadastro do local); seção minúscula (24 votantes); 24 de 24 aptos em trânsito.
- BAIÃO (PA), zona 35, seção 238, EMEF DE NOVO TESOURO: Lula 39, Flávio 10 de 49 válidos (51 aptos, 51 votantes, UE2020). Zona rural (inferido pelo cadastro do local); seção pequena (51 votantes).
- SÃO FÉLIX DO XINGU (PA), zona 53, seção 266, UNIDADE DE CUSTÓDIA E REINSERÇÃO DE SÃO FÉLIX DO XINGU (UCRSFX): Lula 6, Flávio 13 de 20 válidos (21 aptos, 21 votantes, UE2022). Unidade prisional ou socioeducativa (inferido pelo cadastro do local); seção minúscula (21 votantes); 21 de 21 aptos em trânsito.
- ARAÇATUBA (SP), zona 299, seção 229, UI/UIP-ARAÇÁ: Lula 19, Flávio 12 de 32 válidos (34 aptos, 34 votantes, UE2022). Unidade prisional ou socioeducativa (inferido pelo cadastro do local); seção minúscula (34 votantes); 34 de 34 aptos em trânsito.
- MADRI (ZZ), zona 1, seção 1063, COLÉGIO BLANCA DE CASTILLA: Lula 43, Flávio 9 de 57 válidos (797 aptos, 58 votantes, UE2015). Exterior (inferido pelo cadastro do local); seção pequena (58 votantes).
- PORTO SEGURO (BA), zona 121, seção 259, ESCOLA INDÍGENA PATAXÓ BOCA DA MATA: Lula 320, Flávio 1 de 322 válidos (365 aptos, 323 votantes, UE2020). Aldeia ou terra indígena (inferido pelo cadastro do local).
- SÃO GABRIEL DA CACHOEIRA (AM), zona 19, seção 23, E. E. DE PARI-CACHOEIRA (YE PARÃ MAHSÃ BUERI WI): Lula 318, Flávio 2 de 323 válidos (429 aptos, 324 votantes, UE2022). Aldeia ou terra indígena (inferido pelo cadastro do local).
- UIRAMUTÃ (RR), zona 7, seção 108, ESCOLA ESTADUAL JOAQUIM JONES JOSÉ INGARICÓ: Lula 131, Flávio 1 de 132 válidos (146 aptos, 133 votantes, UE2022). Sem regra estrutural acionada: comparar com ata e log da seção.
- ATALAIA DO NORTE (AM), zona 42, seção 28, POLO BASE DE SAÚDE - ALDEIA SÃO SEBASTIÃO: Lula 126, Flávio 1 de 133 válidos (185 aptos, 134 votantes, UE2022). Aldeia ou terra indígena (inferido pelo cadastro do local).
- PARIS (ZZ), zona 1, seção 810, ESPACE VINCI: Lula 123, Flávio 12 de 147 válidos (791 aptos, 148 votantes, UE2013). Exterior (inferido pelo cadastro do local).
- WELLINGTON (ZZ), zona 1, seção 1691, EMBAIXADA DO BRASIL EM WELLINGTON: Lula 50, Flávio 22 de 83 válidos (699 aptos, 85 votantes, UE2013). Exterior (inferido pelo cadastro do local); seção pequena (85 votantes).
- SÃO LUÍS (MA), zona 10, seção 844, PENITENCIÁRIA DE PEDRINHAS - TRIAGEM (ANT. CCPJ ANIL): Lula 150, Flávio 4 de 158 válidos (354 aptos, 163 votantes, UE2015). Unidade prisional ou socioeducativa (inferido pelo cadastro do local); 354 de 354 aptos em trânsito.
- BOSTON (ZZ), zona 1, seção 3466, ST TARCISUS PARISH: Lula 12, Flávio 51 de 71 válidos (398 aptos, 73 votantes, UE2013). Exterior (inferido pelo cadastro do local); seção pequena (73 votantes); a zona inteira vota assim (Flávio 69,8% na zona).
- BOSTON (ZZ), zona 1, seção 1225, ST TARCISUS PARISH: Lula 26, Flávio 103 de 133 válidos (781 aptos, 134 votantes, UE2013). Exterior (inferido pelo cadastro do local).
- PARANATINGA (MT), zona 57, seção 31, ESCOLA MUNICIPAL CEREMECE SEREPSE -MARECHAL RONDON: Lula 186, Flávio 3 de 194 válidos (295 aptos, 196 votantes, UE2020). Aldeia ou terra indígena (inferido pelo cadastro do local).
- BARCELONA (ZZ), zona 1, seção 1570, SEMINARI CONCILIAR DE BARCELONA: Lula 110, Flávio 27 de 151 válidos (797 aptos, 152 votantes, UE2015). Exterior (inferido pelo cadastro do local); a zona inteira vota assim (Lula 73,2% na zona).
- LISBOA (ZZ), zona 1, seção 3457, UNIVERSIDADE DE LISBOA (REITORIA, FAC. DIREITO, FAC. LETRAS): Lula 45, Flávio 56 de 119 válidos (769 aptos, 121 votantes, UE2013). Exterior (inferido pelo cadastro do local).
- SÃO GABRIEL DA CACHOEIRA (AM), zona 19, seção 12, E. E. DE TARACUÁ: Lula 183, Flávio 3 de 187 válidos (268 aptos, 188 votantes, UE2022). Aldeia ou terra indígena (inferido pelo cadastro do local).
- WASHINGTON (ZZ), zona 1, seção 461, CAPITAL HILTON (HOTEL): Lula 53, Flávio 33 de 94 válidos (600 aptos, 95 votantes, UE2013). Exterior (inferido pelo cadastro do local); seção pequena (95 votantes); a zona inteira vota assim (Lula 51,4% na zona).
- BARCELONA (ZZ), zona 1, seção 1566, SEMINARI CONCILIAR DE BARCELONA: Lula 113, Flávio 27 de 148 válidos (795 aptos, 153 votantes, UE2013). Exterior (inferido pelo cadastro do local); a zona inteira vota assim (Lula 73,2% na zona).

### O que não deu certo: a versão de 15 partes

A mesma mistura (k = 5) sobre 15 partes: as 12 candidaturas, brancos, nulos e abstenção, divididos pelos aptos; abandonada em 06/10/2026: os grupos saíram do padrão de zeros das candidaturas nanicas, não da geografia nem do perfil de voto.

- Com as 15 partes, os cinco grupos não são geografia (V de Cramér entre grupo e região 0,21): separam as seções pelo padrão de zeros. 42,7% das células são zero e viram 0,0001; na seção mediana, de 327 aptos, um voto fica a 3,4 unidades de log do zero (de 3,2 a 3,8 entre o primeiro e o último décimo das seções), e a mistura usa esse degrau para separar grupos. O padrão que define cada grupo: grupo 1, sem voto nas cinco candidaturas menos votadas (100,0% das seções do grupo, contra 0,0% no grupo 2); grupo 2, sem voto em Romeu Zema (100,0% das seções do grupo, contra 0,0% no grupo 5); grupo 3, com voto em ao menos uma das sete candidaturas menos votadas (98,8% das seções do grupo, contra 15,1% no grupo 1); grupo 4, com voto em Samara (100,0% das seções do grupo, contra 0,0% no grupo 2); grupo 5, sem voto nas três candidaturas menos votadas (95,2% das seções do grupo, contra 48,2% no grupo 3).
- Na projeção, o componente 1 tem a maior carga em Romeu Zema (0,93) e o componente 2, em Ronaldo Caiado (0,82). As nuvens que se veem no plano são seções com e sem voto nessas partes: um corte no componente 1 separa as seções sem voto em Romeu Zema (63,3% do total) com acerto balanceado de 100,0%; um corte no componente 2 separa as seções sem voto em Ronaldo Caiado (7,3% do total) com acerto balanceado de 99,4%. A mistura com k = 5 reproduz a divisão por Romeu Zema (100 pontos de diferença na proporção de zeros entre grupos); não reproduz a divisão por Ronaldo Caiado (11 pontos de diferença na proporção de zeros entre grupos). As partes que definem os grupos quase não pesam no plano (carga máxima em módulo nos dois componentes: as cinco candidaturas menos votadas, 0,12; Samara, 0,04; as três candidaturas menos votadas, 0,12): essa parte da divisão não aparece na figura.
- O ajuste publicado é o de maior log-verossimilhança entre 8 sementes de 10 inicializações cada (semente 20261011; o máximo apareceu só nela). A log-verossimilhança média por seção vai de −9,36 a 6,41 entre as sementes, e a partição muda com elas (índice de Rand ajustado contra a escolhida de 0,46 a 0,56): a superfície tem muitos máximos locais, porque cada padrão exato de zeros é um subespaço onde um componente se encaixa com variância quase nula. O que não muda é a relação com a geografia: o V de Cramér entre grupo e região fica entre 0,20 e 0,22 em todas. Com k = 4, a melhor log-verossimilhança encontrada (−0,42) fica abaixo da de k = 3 (5,26), o que o máximo global não permitiria, porque um componente a mais nunca piora o melhor ajuste: a tabela do BIC compara máximos locais.

| grupo | rótulo | seções |
|---|---|---|
| 1 | sem voto nas cinco candidaturas menos votadas e sem voto em Romeu Zema; Lula 49% dos válidos; Nordeste 39% das seções | 253.433 |
| 2 | sem voto em Romeu Zema e em Samara e com voto em ao menos uma das cinco candidaturas menos votadas; Flávio 47% dos válidos; Sudeste 38% das seções | 43.478 |
| 3 | com voto em ao menos uma das sete candidaturas menos votadas, com voto em Romeu Zema em 79% das seções e sem voto em Samara em 73% das seções; Flávio 48% dos válidos; Sudeste 44% das seções | 33.206 |
| 4 | com voto em Samara; Flávio 50% dos válidos; Sudeste 66% das seções | 52.720 |
| 5 | sem voto nas três candidaturas menos votadas, sem voto em Samara e com voto em Romeu Zema; Flávio 52% dos válidos; Sudeste 59% das seções | 115.053 |

- k = 3: BIC -5.237.193,9, log-verossimilhança média 5,2641
- k = 4: BIC 423.201,8, log-verossimilhança média -0,4187
- k = 5: BIC -6.378.213,9, log-verossimilhança média 6,4131

### Sensibilidade: a mesma mistura (k = 5, 8 sementes) com zero trocado por meio voto, e não por 0,0001, antes de fechar a composição

V de Cramér entre grupo e região 0,392; entre grupo e UF 0,416.

- Grupo 1: Lula muito alto, Flávio baixo, terceiros baixos; Nordeste 84% das seções; 97.785 seções.
- Grupo 2: nulos baixos, Lula alto, Flávio baixo; Nordeste 42% e Sudeste 17% das seções; 29.874 seções.
- Grupo 3: brancos muito baixos, terceiros baixos; Nordeste 32% e Norte 23% das seções; 52.498 seções.
- Grupo 4: brancos altos, Lula baixo, nulos altos; Sudeste 68% das seções; 181.827 seções.
- Grupo 5: nulos baixos, Flávio alto, Lula baixo; Sudeste 40% e Sul 26% das seções; 135.906 seções.

Índice de Rand ajustado contra a partição principal: versão de 15 partes 0,018; zero trocado por meio voto 0,204.

## C. Modelo de urna

- Dentro da zona há diferença entre modelos separável de zero, o que não é efeito da urna enquanto a alocação dos modelos dentro da zona não for aleatória: na mesma zona, a urna mais nova dá a Flávio −0,73 ponto em relação à mais velha (IC 95% de −1,03 a −0,44, não contém o zero); sem o controle, −1,42; 531 zonas.
- No mesmo prédio, a urna mais nova dá a Flávio 0,11 ponto em relação à mais velha (IC 95% de 0,02 a 0,20, não contém o zero); sem o controle, −0,52; 7.899 locais.
- Com a linha de base da própria seção em 2022, na mesma zona, a urna mais nova dá a Flávio, sobre Bolsonaro, 0,22 ponto em relação à mais velha (IC 95% de 0,14 a 0,31, não contém o zero); sem o controle, 0,39; 443 zonas.
- Em 2022, na mesma zona, a UE2020 dá a Bolsonaro 1,41 ponto em relação à UE2015 (IC 95% de 0,84 a 2,00, não contém o zero); sem o controle, 1,32; 264 zonas.
- Em 2022, no mesmo prédio, a UE2020 dá a Bolsonaro 0,85 ponto em relação à UE2015 (IC 95% de −0,15 a 2,04, contém o zero); sem o controle, 2,29; 85 locais.
- Nas mesmas seções de 2022 para 2026, agrupadas pelo modelo de 2022, a urna mais nova dá a Flávio, sobre Bolsonaro, −0,14 ponto em relação à mais velha (IC 95% de −0,26 a −0,03, não contém o zero); sem o controle, −0,34; 379 zonas.
- As quatro réguas da urna mais nova contra a mais velha dão a Flávio de −0,73 a +0,22 ponto (−0,73 dentro da zona; +0,11 no mesmo prédio; +0,22 com a linha de base da própria seção em 2022; −0,14 nas mesmas seções, pelo modelo da urna de 2022). Todas ficam abaixo de um ponto e o sinal muda conforme o controle: um efeito do equipamento tenderia a aparecer com o mesmo sinal nas réguas que controlam o lugar. A leitura é a alocação dos modelos dentro da zona, não efeito da máquina; o plano de alocação de urnas do TRE é o documento que resolve.

Bruto (soma dos votos por modelo, sem controle):

| modelo | seções | Flávio % | Lula % | abstenção % | brancos % | nulos % |
|---|---|---|---|---|---|---|
| UE2013 | 11.913 | 45,00 | 47,12 | 28,38 | 1,86 | 2,72 |
| UE2015 | 87.960 | 46,84 | 45,29 | 21,46 | 1,90 | 2,90 |
| UE2020 | 199.838 | 47,33 | 45,00 | 20,95 | 1,82 | 2,96 |
| UE2022 | 198.148 | 46,93 | 45,17 | 20,56 | 1,82 | 2,93 |
| sem modelo | 31 | 42,89 | 48,48 | 54,04 | 1,56 | 2,97 |

Dentro da zona (Diferença (modelo b menos modelo a) dentro do par município e zona com ao menos 20 seções de cada modelo, média ponderada pelos votantes das seções comparadas; IC por bootstrap de zonas.):

| a → b | unidades | seções a/b | Flávio pp | Lula pp | nulos pp | bruto Flávio |
|---|---|---|---|---|---|---|
| UE2013 → UE2015 | 99 | 4.371/13.019 | -1,16 (IC 95% de -2,03 a -0,37) | 1,44 (IC 95% de 0,59 a 2,37) | 0,04 (IC 95% de -0,05 a 0,13) | -1,79 |
| UE2013 → UE2020 | 1 | 22/210 | -6,26 (IC 95% de -6,26 a -6,26) | 9,71 (IC 95% de 9,71 a 9,71) | 1,01 (IC 95% de 1,01 a 1,01) | -6,26 |
| UE2013 → UE2022 | 5 | 109/561 | -5,72 (IC 95% de -7,61 a -3,36) | 7,17 (IC 95% de 3,69 a 10,21) | 0,41 (IC 95% de -0,17 a 0,83) | -7,07 |
| UE2015 → UE2020 | 284 | 19.225/35.308 | -0,62 (IC 95% de -1,01 a -0,23) | 0,72 (IC 95% de 0,28 a 1,17) | 0,15 (IC 95% de 0,09 a 0,21) | -0,87 |
| UE2015 → UE2022 | 287 | 19.091/34.099 | -0,79 (IC 95% de -1,16 a -0,41) | 0,96 (IC 95% de 0,53 a 1,39) | 0,20 (IC 95% de 0,15 a 0,26) | -1,41 |
| UE2020 → UE2022 | 384 | 41.124/40.815 | -0,20 (IC 95% de -0,46 a 0,08) | 0,27 (IC 95% de -0,05 a 0,57) | 0,04 (IC 95% de -0,00 a 0,08) | -0,29 |
| mais velha → mais nova | 531 | 32.920/56.847 | -0,73 (IC 95% de -1,03 a -0,44) | 0,90 (IC 95% de 0,57 a 1,23) | 0,13 (IC 95% de 0,09 a 0,17) | -1,42 |

Dentro do mesmo local (Diferença (modelo b menos modelo a) dentro do mesmo local de votação (mesmo prédio), com ao menos uma seção de cada modelo; IC por bootstrap de locais.):

| a → b | unidades | seções a/b | Flávio pp | Lula pp | nulos pp | bruto Flávio |
|---|---|---|---|---|---|---|
| UE2013 → UE2015 | 2.630 | 5.486/15.884 | 0,23 (IC 95% de 0,06 a 0,38) | -0,20 (IC 95% de -0,34 a -0,04) | -0,00 (IC 95% de -0,05 a 0,05) | -0,35 |
| UE2013 → UE2020 | 15 | 22/49 | 5,01 (IC 95% de 1,53 a 9,12) | -5,27 (IC 95% de -9,49 a -2,35) | -1,17 (IC 95% de -3,19 a 0,13) | 2,21 |
| UE2013 → UE2022 | 17 | 40/91 | 1,69 (IC 95% de -0,31 a 3,83) | -2,05 (IC 95% de -3,38 a -0,84) | -0,25 (IC 95% de -0,72 a 0,30) | 5,30 |
| UE2015 → UE2020 | 68 | 258/383 | 0,79 (IC 95% de -0,03 a 1,65) | -0,37 (IC 95% de -1,21 a 0,50) | 0,15 (IC 95% de -0,19 a 0,49) | -0,32 |
| UE2015 → UE2022 | 70 | 270/383 | 0,74 (IC 95% de -0,29 a 1,78) | -0,66 (IC 95% de -1,83 a 0,42) | -0,09 (IC 95% de -0,33 a 0,17) | 0,05 |
| UE2020 → UE2022 | 5.194 | 22.156/21.377 | 0,03 (IC 95% de -0,07 a 0,13) | -0,03 (IC 95% de -0,13 a 0,06) | -0,01 (IC 95% de -0,04 a 0,02) | -0,30 |
| mais velha → mais nova | 7.899 | 27.882/37.764 | 0,11 (IC 95% de 0,02 a 0,20) | -0,10 (IC 95% de -0,19 a -0,02) | -0,01 (IC 95% de -0,03 a 0,02) | -0,52 |

Variação contra a mesma seção em 2022 (Diferença entre modelos, dentro do par município e zona, da variação de cada seção contra ela mesma em 2022 (Flávio 2026 menos Bolsonaro 1º turno 2022; Lula 2026 menos Lula 2022, em % dos válidos). A linha de base de 2022 da mesma seção tira o perfil político do lugar; só seções casadas pelo número e pelo nome do local.):

- UE2013 → UE2015: 62 zonas; Flávio menos Bolsonaro 0,16 (IC 95% de -0,08 a 0,39); Lula -0,48 (IC 95% de -0,88 a -0,12)
- UE2013 → UE2020: 1 zonas; Flávio menos Bolsonaro -0,08 (IC 95% de -0,08 a -0,08); Lula -2,56 (IC 95% de -2,56 a -2,56)
- UE2013 → UE2022: 2 zonas; Flávio menos Bolsonaro -0,29 (IC 95% de -0,58 a -0,16); Lula -2,19 (IC 95% de -3,38 a 0,43)
- UE2015 → UE2020: 259 zonas; Flávio menos Bolsonaro 0,18 (IC 95% de 0,06 a 0,29); Lula -0,38 (IC 95% de -0,58 a -0,15)
- UE2015 → UE2022: 260 zonas; Flávio menos Bolsonaro 0,30 (IC 95% de 0,20 a 0,41); Lula -0,53 (IC 95% de -0,73 a -0,34)
- UE2020 → UE2022: 328 zonas; Flávio menos Bolsonaro 0,08 (IC 95% de -0,00 a 0,15); Lula -0,16 (IC 95% de -0,30 a -0,03)
- mais velha → mais nova: 443 zonas; Flávio menos Bolsonaro 0,22 (IC 95% de 0,14 a 0,31); Lula -0,46 (IC 95% de -0,62 a -0,31)

Troca de urna entre 2022 e 2026 (mesma seção; rótulo = modelo de 2022; 354.932 seções casadas). Variação de cada seção de 2022 para 2026 (Flávio 2026 menos Bolsonaro 1º turno 2022, em % dos válidos), comparada entre seções agrupadas pelo modelo da urna de 2022 dentro do par município e zona. Diferença b menos a: se a urna velha (a) de 2022 tivesse tirado voto de Bolsonaro, a diferença seria negativa.

- UE2009 → UE2020: 149 zonas; variação de Flávio sobre Bolsonaro -0,19 (IC 95% de -0,35 a -0,02)
- UE2010 → UE2020: 248 zonas; variação de Flávio sobre Bolsonaro -0,26 (IC 95% de -0,37 a -0,14)
- UE2011 → UE2020: 122 zonas; variação de Flávio sobre Bolsonaro -0,22 (IC 95% de -0,41 a -0,04)
- UE2013 → UE2020: 11 zonas; variação de Flávio sobre Bolsonaro 0,02 (IC 95% de -0,41 a 0,37)
- UE2015 → UE2020: 241 zonas; variação de Flávio sobre Bolsonaro -0,42 (IC 95% de -0,56 a -0,29)
- mais velha → mais nova: 379 zonas; variação de Flávio sobre Bolsonaro -0,14 (IC 95% de -0,26 a -0,03)

2022, mesmo estimador (Bolsonaro e Lula, 1º turno):

- dentro da zona, UE2009 → UE2020: 191 unidades; Bolsonaro 0,78 (IC 95% de 0,17 a 1,39), bruto 1,54
- dentro da zona, UE2010 → UE2020: 270 unidades; Bolsonaro 0,79 (IC 95% de 0,33 a 1,25), bruto 0,60
- dentro da zona, UE2011 → UE2020: 167 unidades; Bolsonaro 0,97 (IC 95% de 0,28 a 1,68), bruto 0,60
- dentro da zona, UE2013 → UE2020: 19 unidades; Bolsonaro 0,09 (IC 95% de -1,58 a 1,70), bruto -1,89
- dentro da zona, UE2015 → UE2020: 264 unidades; Bolsonaro 1,41 (IC 95% de 0,84 a 2,00), bruto 1,32
- dentro da zona, mais velha → mais nova: 474 unidades; Bolsonaro 0,46 (IC 95% de 0,02 a 0,88), bruto 0,92
- dentro do local, UE2009 → UE2020: 58 unidades; Bolsonaro 0,47 (IC 95% de -0,66 a 1,54), bruto -0,51
- dentro do local, UE2010 → UE2020: 85 unidades; Bolsonaro 0,51 (IC 95% de -0,50 a 1,53), bruto 0,90
- dentro do local, UE2011 → UE2020: 46 unidades; Bolsonaro 0,30 (IC 95% de -1,32 a 2,04), bruto 0,39
- dentro do local, UE2013 → UE2020: 24 unidades; Bolsonaro 0,05 (IC 95% de -1,45 a 1,87), bruto -0,95
- dentro do local, UE2015 → UE2020: 85 unidades; Bolsonaro 0,85 (IC 95% de -0,15 a 2,04), bruto 2,29
- dentro do local, mais velha → mais nova: 8.876 unidades; Bolsonaro -0,07 (IC 95% de -0,17 a 0,03), bruto 0,76

As réguas nacionais (urna mais nova contra a mais velha, Flávio):

- Dentro da zona: -0,73 (IC 95% de -1,03 a -0,44); sem controle -1,42; 531 zonas.
- No mesmo prédio: 0,11 (IC 95% de 0,02 a 0,20); sem controle -0,52; 7.899 locais.
- Com a linha de base da própria seção em 2022: 0,22 (IC 95% de 0,14 a 0,31); sem controle 0,39; 443 zonas.
- Nas mesmas seções, pelo modelo da urna de 2022: -0,14 (IC 95% de -0,26 a -0,03); sem controle -0,34; 379 zonas.

As quatro réguas da urna mais nova contra a mais velha dão a Flávio de −0,73 a +0,22 ponto (−0,73 dentro da zona; +0,11 no mesmo prédio; +0,22 com a linha de base da própria seção em 2022; −0,14 nas mesmas seções, pelo modelo da urna de 2022). Todas ficam abaixo de um ponto e o sinal muda conforme o controle: um efeito do equipamento tenderia a aparecer com o mesmo sinal nas réguas que controlam o lugar. A leitura é a alocação dos modelos dentro da zona, não efeito da máquina; o plano de alocação de urnas do TRE é o documento que resolve.

## D. Outras anomalias de seção

- Comparecimento acima de 100%: 0; igual a 100% (abstenção zero): 15, das quais 3 com 100 aptos ou mais.
- Zero voto em Lula com 200 votantes ou mais: 0 de 421.229 seções.
- Zero voto em Flávio com 200 votantes ou mais: 17 de 421.229 seções.
  - TABATINGA (AM), zona 36, seção 96, E. M. INDÍGENA AITCHA: Lula 340, Flávio 0 de 342 válidos (388 aptos, 346 votantes, UE2022). Aldeia ou terra indígena (inferido pelo cadastro do local).
  - SANTO ANTÔNIO DO IÇÁ (AM), zona 47, seção 10, E. E. D. PEDRO I: Lula 318, Flávio 0 de 319 válidos (364 aptos, 321 votantes, UE2022). Aldeia ou terra indígena (inferido pelo cadastro do local).
  - CONFRESA (MT), zona 28, seção 200, ESCOLA ESTADUAL TAPI'ITAWA: Lula 296, Flávio 0 de 297 válidos (315 aptos, 297 votantes, UE2022). Aldeia ou terra indígena (inferido pelo cadastro do local).
  - SANTO ANTÔNIO DO IÇÁ (AM), zona 47, seção 63, E. M. INDÍGENA BELA VISTA: Lula 284, Flávio 0 de 289 válidos (319 aptos, 290 votantes, UE2022). Aldeia ou terra indígena (inferido pelo cadastro do local).
  - MONTES ALTOS (MA), zona 103, seção 28, ESCOLA MUNICIPAL SAO JOSE: Lula 281, Flávio 0 de 281 válidos (318 aptos, 283 votantes, UE2020). Aldeia ou terra indígena (inferido pelo cadastro do local).
- Tipo de arquivo 1 (votação na urna (normal)): 497.809 seções; Flávio 47,03%, diferença média para o resto da zona 0,00 ponto.
- Tipo de arquivo 2 (votação recuperada (RED)): 50 seções; Flávio 45,17%, diferença média para o resto da zona 0,53 ponto.
- Tipo de arquivo 4 (sistema de apuração (4)): 2 seções; Flávio 46,72%, diferença média para o resto da zona -3,69 pontos.
- Tipo de arquivo 5 (sistema de apuração (5)): 29 seções; Flávio 40,31%, diferença média para o resto da zona sem resto de zona para comparar.
- Urna de seção: 494.829 seções; diferença média de Flávio para o resto da zona 0,00 ponto.
- Urna de contingência: 31 seções; diferença média de Flávio para o resto da zona -3,69 pontos.
- Urna de reserva (seção): 3.030 seções; diferença média de Flávio para o resto da zona 0,01 ponto.
- Horários (Brasília): abertura depois das 9h em 213 seções, depois das 10h em 22; encerramento depois das 18h em 43.003, depois das 19h em 8.366, depois das 20h em 1.342.
- Seções que encerraram depois das 19h: 8.366 seções; Lula 3,43 pontos e Flávio -2,84 pontos em relação ao resto da própria zona (fila longa costuma ser de seção grande e de bairro populoso; hipótese a conferir com a ata).
- Seções que abriram depois das 9h: 213 seções; Lula 3,57 pontos e Flávio -3,15 pontos em relação ao resto da própria zona (fila longa costuma ser de seção grande e de bairro populoso; hipótese a conferir com a ata).
- Boletins recebidos pelo TSE depois de meia-noite de 05/10: 340 seções, 75.465 válidos, Lula 65,17%; diferença média de Lula para o resto da zona 1,24 ponto.
  - CAPANEMA (PA): 101 seções, Lula 53,7%
  - CABO DE SANTO AGOSTINHO (PE): 51 seções, Lula 68,3%
  - VIANA (MA): 34 seções, Lula 59,6%
  - OEIRAS DO PARÁ (PA): 33 seções, Lula 75,4%
  - GURUPÁ (PA): 28 seções, Lula 70,6%
  - AFUÁ (PA): 24 seções, Lula 63,8%
  - JURUTI (PA): 23 seções, Lula 74,2%
  - CAJARI (MA): 11 seções, Lula 88,8%
  - MOJU (PA): 10 seções, Lula 72,7%
  - PAULISTA (PE): 7 seções, Lula 53,9%
- Boletins recebidos pelo TSE depois de 1h de 05/10: 332 seções, 73.153 válidos, Lula 64,56%; diferença média de Lula para o resto da zona 0,94 ponto.
  - CAPANEMA (PA): 101 seções, Lula 53,7%
  - CABO DE SANTO AGOSTINHO (PE): 51 seções, Lula 68,3%
  - VIANA (MA): 34 seções, Lula 59,6%
  - OEIRAS DO PARÁ (PA): 33 seções, Lula 75,4%
  - GURUPÁ (PA): 28 seções, Lula 70,6%
  - AFUÁ (PA): 24 seções, Lula 63,8%
  - JURUTI (PA): 23 seções, Lula 74,2%
  - CAJARI (MA): 11 seções, Lula 88,8%
  - MOJU (PA): 10 seções, Lula 72,7%
  - PAULISTA (PE): 7 seções, Lula 53,9%
- Benford do segundo dígito, Brasil, Lula: n = 497.574, qui-quadrado 5.640,6 com 9 graus de liberdade. Testes de dígito (último dígito e Benford do segundo dígito) são curiosidade metodológica: contagens de votos não seguem Benford por construção, e o teste rejeita ou aceita por motivos que nada têm a ver com fraude (Deckert, Myagkov e Ordeshook, 2011, Political Analysis 19(3)).

## Verificado (dado do TSE, conta direta)

- Base: 497.890 boletins de urna de seção, todos em zonas cuja soma das seções confere com o arquivo de zona do TSE.
- Seções com Lula em 90% ou mais dos válidos: 3.686 (0,74% das seções), 873.711 eleitores aptos; com Flávio: 186 (0,04%), 42.580 aptos.
- Comparecimento acima de 100% dos aptos: 0 seções; igual a 100%: 15.
- Seções com 200 votantes ou mais e nenhum voto em Lula: 0; nenhum voto em Flávio: 17.
- Das 2.441 seções com Lula em 90% ou mais que existem com o mesmo número e o mesmo local em 2022, 2.021 já davam 90% ou mais a ele no 1º turno de 2022 e 2.425 davam 80% ou mais; mediana de 2022: 93,3%.
- O EM convergiu nas 32 partidas (16 sementes, inicializações kmeans e k-means++, 10 partidas internas cada; critério do sklearn: variação da log-verossimilhança média abaixo de 0,0001, de 19 a 77 iterações). Refeita com tolerância 0,000001 e até 2.000 iterações, a melhor partida foi de 51 para 105 iterações e a log-verossimilhança média subiu 0,000688 por seção, mas a partição mudou (índice de Rand ajustado de 0,79 entre as duas): pelo critério declarado, o padrão parava cedo, e o ajuste publicado é o apertado. 2 de 32 partidas chegaram ao mesmo máximo, a 0,001 por seção (kmeans: 2 de 16; k-means++: 0 de 16). A partição escolhida é instável: índice de Rand ajustado médio de 0,78 contra as partidas que chegam ao máximo e de 0,18 contra as demais.

## Inferido (leitura dos números)

- As seções de 90% de Lula estão em zonas que já votam muito nele: mediana de 76,3% no resto da zona; o excesso típico da seção sobre a zona é de 17,1 pontos.
- Locais com nome de aldeia ou escola indígena: 1.428 seções, 565 delas com Lula em 90% ou mais (39,6% do tipo, contra 0,74% no total).
- Com as 15 partes, os cinco grupos não são geografia (V de Cramér entre grupo e região 0,21): separam as seções pelo padrão de zeros. 42,7% das células são zero e viram 0,0001; na seção mediana, de 327 aptos, um voto fica a 3,4 unidades de log do zero (de 3,2 a 3,8 entre o primeiro e o último décimo das seções), e a mistura usa esse degrau para separar grupos. O padrão que define cada grupo: grupo 1, sem voto nas cinco candidaturas menos votadas (100,0% das seções do grupo, contra 0,0% no grupo 2); grupo 2, sem voto em Romeu Zema (100,0% das seções do grupo, contra 0,0% no grupo 5); grupo 3, com voto em ao menos uma das sete candidaturas menos votadas (98,8% das seções do grupo, contra 15,1% no grupo 1); grupo 4, com voto em Samara (100,0% das seções do grupo, contra 0,0% no grupo 2); grupo 5, sem voto nas três candidaturas menos votadas (95,2% das seções do grupo, contra 48,2% no grupo 3).
- Com as cinco partes, a associação entre grupo e região sobe pouco (V de Cramér de 0,24, contra 0,21 com as 15 partes; 0,26 com a UF) e fica abaixo de 0,3: cada grupo ainda mistura regiões.
- Cinco partes não bastaram: três dos cinco grupos são artefatos da contagem inteira, não perfil de seção: o 1 (sem voto branco; 24.891 seções), o 3 (mesmo número de brancos e de nulos; 44.447 seções) e o 4 (sem voto nulo; 5.202 seções). Brancos e nulos são poucos votos por seção (mediana de 4 brancos e 7 nulos); no logaritmo, o zero vira um degrau de 3,5 unidades até o primeiro voto e o empate vira uma razão exata de 1, e a mistura gasta um componente em cada padrão. 1,34% das células são zero (5,31% das seções sem voto branco e 1,35% das seções sem voto nulo), e 8,93% das seções têm o mesmo número de brancos e de nulos.
- Na projeção, o componente 1 (54,5% da variância) opõe brancos (carga 0,89) a Lula (−0,28); o componente 2 (27,5% da variância) opõe nulos (carga 0,79) a Flávio (−0,54). Os centros dos grupos se afastam mais no componente 1 (variância ponderada dos centros 1,01, contra 0,25 no outro). Um corte no componente 1 separa as seções sem voto branco (5,3% do total) com acerto balanceado de 100,0%. Um corte no componente 2 separa as seções sem voto nulo (1,3% do total) com acerto balanceado de 99,7%.
- Dentro da zona há diferença entre modelos separável de zero, o que não é efeito da urna enquanto a alocação dos modelos dentro da zona não for aleatória: na mesma zona, a urna mais nova dá a Flávio −0,73 ponto em relação à mais velha (IC 95% de −1,03 a −0,44, não contém o zero); sem o controle, −1,42; 531 zonas.
- No mesmo prédio, a urna mais nova dá a Flávio 0,11 ponto em relação à mais velha (IC 95% de 0,02 a 0,20, não contém o zero); sem o controle, −0,52; 7.899 locais.
- Com a linha de base da própria seção em 2022, na mesma zona, a urna mais nova dá a Flávio, sobre Bolsonaro, 0,22 ponto em relação à mais velha (IC 95% de 0,14 a 0,31, não contém o zero); sem o controle, 0,39; 443 zonas.
- Em 2022, na mesma zona, a UE2020 dá a Bolsonaro 1,41 ponto em relação à UE2015 (IC 95% de 0,84 a 2,00, não contém o zero); sem o controle, 1,32; 264 zonas.
- Em 2022, no mesmo prédio, a UE2020 dá a Bolsonaro 0,85 ponto em relação à UE2015 (IC 95% de −0,15 a 2,04, contém o zero); sem o controle, 2,29; 85 locais.
- Nas mesmas seções de 2022 para 2026, agrupadas pelo modelo de 2022, a urna mais nova dá a Flávio, sobre Bolsonaro, −0,14 ponto em relação à mais velha (IC 95% de −0,26 a −0,03, não contém o zero); sem o controle, −0,34; 379 zonas.
- As quatro réguas da urna mais nova contra a mais velha dão a Flávio de −0,73 a +0,22 ponto (−0,73 dentro da zona; +0,11 no mesmo prédio; +0,22 com a linha de base da própria seção em 2022; −0,14 nas mesmas seções, pelo modelo da urna de 2022). Todas ficam abaixo de um ponto e o sinal muda conforme o controle: um efeito do equipamento tenderia a aparecer com o mesmo sinal nas réguas que controlam o lugar. A leitura é a alocação dos modelos dentro da zona, não efeito da máquina; o plano de alocação de urnas do TRE é o documento que resolve.

## Juízo editorial

- Seção com 90% para um candidato é, na esmagadora maioria, lugar que sempre votou assim: aldeia, zona rural do Nordeste, comunidade pequena. O número chama atenção na manchete e some quando se olha a zona e 2022.
- Nenhum dos testes por seção aponta irregularidade. O que fica atípico exige explicação documental (ata da mesa, log da urna, plano de alocação das urnas do TRE), não conclusão.

## Hipótese (a verificar)

- Diferença entre modelos de urna que sobreviva ao controle por zona pode vir da alocação não aleatória das urnas dentro da zona (escolas centrais e periféricas, locais grandes e pequenos). Só o plano de alocação do TRE separa essa hipótese de um efeito do equipamento.

## O achado que contraria a tese

- Quem espera achar seções novas de 90% encontra as velhas: 2.021 de 2.441 seções casadas de Lula já estavam acima de 90% em 2022.
- Cinco partes não bastaram: três dos cinco grupos são artefatos da contagem inteira, não perfil de seção: o 1 (sem voto branco; 24.891 seções), o 3 (mesmo número de brancos e de nulos; 44.447 seções) e o 4 (sem voto nulo; 5.202 seções). Brancos e nulos são poucos votos por seção (mediana de 4 brancos e 7 nulos); no logaritmo, o zero vira um degrau de 3,5 unidades até o primeiro voto e o empate vira uma razão exata de 1, e a mistura gasta um componente em cada padrão. 1,34% das células são zero (5,31% das seções sem voto branco e 1,35% das seções sem voto nulo), e 8,93% das seções têm o mesmo número de brancos e de nulos.
- Dentro da zona há diferença entre modelos separável de zero, o que não é efeito da urna enquanto a alocação dos modelos dentro da zona não for aleatória: na mesma zona, a urna mais nova dá a Flávio −0,73 ponto em relação à mais velha (IC 95% de −1,03 a −0,44, não contém o zero); sem o controle, −1,42; 531 zonas.

## Limites

- Zona é o par município e zona eleitoral, como no arquivo de zona do TSE.
- Seções agregadas não têm boletim próprio: o voto delas está no da seção principal, e os aptos do boletim já as incluem.
- Tipo de local é inferência por palavra-chave no cadastro de locais do TSE; o nome do local não prova o perfil do eleitor.
- O modelo da urna vem do log da própria urna; urna de reserva ou contingência aparece com o modelo da urna que gravou o boletim.
- A comparação com 2022 casa a seção pelo número e pelo nome do local; seção renumerada ou local trocado fica de fora.
- Seções pequenas inflam percentuais: 100% de 30 válidos não é o mesmo que 100% de 300. Por isso os cortes por tamanho e o corte de 100 votantes.
- A mistura gaussiana usa só Lula, Flávio, brancos, nulos e abstenção, em composição fechada: o voto em terceiros fica fora das partes, e o zero continua trocado por 0,0001. A versão com as 15 partes foi abandonada porque separava as seções pelo padrão de zeros das candidaturas nanicas.
- Benford e último dígito são curiosidade metodológica, não teste de fraude.

## Reprodução

```
python3 scripts/apuracao-2026-secoes.py            # exige coleta completa
python3 scripts/apuracao-2026-secoes.py --parcial  # com o que já existe
pytest -q tests/test_apuracao_2026_secoes.py
```
