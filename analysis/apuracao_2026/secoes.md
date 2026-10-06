# Análise por seção (boletins de urna), presidente, 1º turno de 2026

Gerado em 2026-10-06T00:58:12Z por `scripts/apuracao-2026-secoes.py`. Dados em `analysis/apuracao_2026/dados/secoes.json` (contrato em `analysis/apuracao_2026/CONTRATO_SECOES.md`).

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

## B. Mistura gaussiana (k = 3)

- Na especificação pedida, os três grupos não são geografia (V de Cramér entre grupo e região 0,13): separam as seções pelo padrão de zeros. 42,7% das células são zero e viram 0,0001; na seção mediana, de 327 aptos, um voto fica a 3,4 unidades de log do zero (de 3,2 a 3,8 entre o primeiro e o último décimo das seções), e a mistura usa esse degrau para separar grupos. O padrão que define cada grupo: grupo 1, sem voto nas cinco candidaturas menos votadas (100,0% das seções do grupo, contra 0,0% no grupo 3); grupo 2, com voto em ao menos uma das cinco candidaturas menos votadas (98,3% das seções do grupo, contra 0,0% no grupo 1); grupo 3, sem voto em Samara (100,0% das seções do grupo, contra 30,9% no grupo 2).
- Na versão com nanicas somadas, o V de Cramér entre grupo e região é 0,26; o padrão de zeros ainda separa os grupos (Renan Santos, 100 pontos de diferença na proporção de zeros).
- Na versão com cinco partes, o V de Cramér entre grupo e região é 0,36.
- Grupo 1: sem voto nas cinco candidaturas menos votadas; Flávio 47% dos válidos; Sudeste 37% das seções; 384.397 seções.
- Grupo 2: com voto em ao menos uma das cinco candidaturas menos votadas e com voto em Samara em 69% das seções; Flávio 46% dos válidos; Sudeste 48% das seções; 44.095 seções.
- Grupo 3: sem voto em Samara e com voto em ao menos uma das cinco candidaturas menos votadas; Flávio 50% dos válidos; Sudeste 53% das seções; 69.398 seções.
- O grupo de menor densidade e maior dispersão é o 2 (com voto em ao menos uma das cinco candidaturas menos votadas e com voto em Samara em 69% das seções; Flávio 46% dos válidos; Sudeste 48% das seções); as 20 seções menos prováveis dele vêm com o que provavelmente as explica.
- Na projeção, o componente 1 tem a maior carga em Romeu Zema (0,93) e o componente 2, em Ronaldo Caiado (0,82). As nuvens que se veem no plano são seções com e sem voto nessas partes: um corte no componente 1 separa as seções sem voto em Romeu Zema (63,3% do total) com acerto balanceado de 100,0%; um corte no componente 2 separa as seções sem voto em Ronaldo Caiado (7,3% do total) com acerto balanceado de 99,4%. A mistura com k = 3 não reproduz a divisão por Romeu Zema e Ronaldo Caiado (12 e 11 pontos de diferença na proporção de zeros entre grupos). As partes que definem os grupos quase não pesam no plano (carga máxima em módulo nos dois componentes: as cinco candidaturas menos votadas, 0,12; Samara, 0,04): essa parte da divisão não aparece na figura.
- O ajuste publicado é o de maior log-verossimilhança entre 8 sementes de 10 inicializações cada (semente 20261008; o máximo apareceu em duas delas). A log-verossimilhança média por seção vai de −11,50 a 5,26 entre as sementes, e a partição muda com elas (índice de Rand ajustado contra a escolhida de 0,04 a 1,00): a superfície tem muitos máximos locais, porque cada padrão exato de zeros é um subespaço onde um componente se encaixa com variância quase nula. O que não muda é a relação com a geografia: o V de Cramér entre grupo e região fica entre 0,13 e 0,27 em todas. Com k = 4, a melhor log-verossimilhança encontrada (−0,42) fica abaixo da de k = 3 (5,26), o que o máximo global não permitiria, porque um componente a mais nunca piora o melhor ajuste: a tabela do BIC compara máximos locais.

Escolha de k (juízo editorial): k = 3, escolha do autor pela leitura visual da projeção em dois componentes principais (05/10/2026; antes, k = 4). O BIC prefere k = 5.

Método: log-razão centrada (CLR) das 15 frações, com zero trocado por 0,0001 antes do log; a mistura é ajustada nas 14 coordenadas ortonormais do subespaço de soma zero (ILR), rotação que preserva Mahalanobis e densidade relativa. Covariância completa, 10 inicializações por semente, 8 sementes, fica a de maior log-verossimilhança (semente 20261008), ajuste sobre 497.890 seções (o país inteiro, sem amostra).

BIC (menor é melhor; com os degraus de zeros, a comparação entre k é instável e serve só de contraste; cada k com o melhor de todas as sementes):

- k = 3: BIC -5.237.193,9, log-verossimilhança média 5,264
- k = 4: BIC 423.201,8, log-verossimilhança média -0,419
- k = 5: BIC -6.378.213,9, log-verossimilhança média 6,413

| grupo | rótulo | seções | aptos médios | log-veross. média | log det Σ |
|---|---|---|---|---|---|
| 1 | sem voto nas cinco candidaturas menos votadas; Flávio 47% dos válidos; Sudeste 37% das seções | 384.397 | 312 | 12,14 | -60,5 |
| 2 | com voto em ao menos uma das cinco candidaturas menos votadas e com voto em Samara em 69% das seções; Flávio 46% dos válidos; Sudeste 48% das seções | 44.095 | 339 | -23,43 | 2,3 |
| 3 | sem voto em Samara e com voto em ao menos uma das cinco candidaturas menos votadas; Flávio 50% dos válidos; Sudeste 53% das seções | 69.398 | 336 | -14,58 | -14,5 |

Versão densa (mesma mistura (k = 3, mesmas sementes) sobre cinco partes quase sem zeros: Lula, Flávio, as outras dez candidaturas somadas, brancos e nulos somados, abstenção):

| grupo | rótulo | seções | aptos médios | log-veross. média | log det Σ |
|---|---|---|---|---|---|
| 1 | Lula 62% dos válidos, abstenção 26%, Nordeste 35% das seções | 6.852 | 289 | -11,45 | 3,1 |
| 2 | Lula 59% dos válidos, abstenção 22%, Nordeste 52% das seções | 113.004 | 296 | -3,93 | -5,8 |
| 3 | Flávio 50% dos válidos, abstenção 20%, Sudeste 48% das seções | 378.034 | 325 | -1,56 | -8,5 |

Grupo mais anômalo na versão pedida: 2. Critério: soma dos postos de menor log-verossimilhança média e de maior dispersão (log-determinante da covariância); empate decidido pela menor log-verossimilhança média. Amostras: as 20 seções de menor log-verossimilhança dentro do componente.

- CIUDAD GUAYANA (ZZ), zona 1, seção 91, EMBAIXADA EM CARACAS: Lula 0, Flávio 0 de 0 válidos (72 aptos, 0 votantes, sem modelo). Exterior (inferido pelo cadastro do local); seção minúscula (0 votantes); urna de contingência; sistema de apuração (5).
- VITÓRIA DA CONQUISTA (BA), zona 41, seção 400, CASE PROFESSOR WANDERLINO NOGUEIRA NETO: Lula 36, Flávio 17 de 53 válidos (53 aptos, 53 votantes, UE2020). Unidade prisional ou socioeducativa (inferido pelo cadastro do local); seção pequena (53 votantes); 53 de 53 aptos em trânsito.
- UIRAMUTÃ (RR), zona 7, seção 124, ESCOLA ESTADUAL INDÍGENA TUXAUA CRETÁCIO: Lula 51, Flávio 0 de 51 válidos (52 aptos, 52 votantes, UE2022). Aldeia ou terra indígena (inferido pelo cadastro do local); seção pequena (52 votantes).
- BAIÃO (PA), zona 35, seção 238, EMEF DE NOVO TESOURO: Lula 39, Flávio 10 de 49 válidos (51 aptos, 51 votantes, UE2020). Zona rural (inferido pelo cadastro do local); seção pequena (51 votantes).
- OCARA (CE), zona 67, seção 275, IGREJA BATISTA SHALON JERUSALEM: Lula 51, Flávio 25 de 79 válidos (83 aptos, 83 votantes, UE2022). Seção pequena (83 votantes); a zona inteira vota assim (Lula 68,5% na zona).
- ARAGUARI (MG), zona 16, seção 347, CEM ROSA MAMERI RADE: Lula 4, Flávio 33 de 37 válidos (37 aptos, 37 votantes, UE2020). Zona rural (inferido pelo cadastro do local); seção minúscula (37 votantes).
- ARAÇATUBA (SP), zona 299, seção 229, UI/UIP-ARAÇÁ: Lula 19, Flávio 12 de 32 válidos (34 aptos, 34 votantes, UE2022). Unidade prisional ou socioeducativa (inferido pelo cadastro do local); seção minúscula (34 votantes); 34 de 34 aptos em trânsito.
- CAPANEMA (PA), zona 25, seção 364, OLGA COSTA PEREIRA-EMEF- BAIRRO SANTA LUZIA: Lula 48, Flávio 17 de 70 válidos (73 aptos, 73 votantes, UE2022). Seção pequena (73 votantes).
- SÃO FÉLIX DO XINGU (PA), zona 53, seção 266, UNIDADE DE CUSTÓDIA E REINSERÇÃO DE SÃO FÉLIX DO XINGU (UCRSFX): Lula 6, Flávio 13 de 20 válidos (21 aptos, 21 votantes, UE2022). Unidade prisional ou socioeducativa (inferido pelo cadastro do local); seção minúscula (21 votantes); 21 de 21 aptos em trânsito.
- SANTO ESTEVÃO (BA), zona 143, seção 230, ESCOLA MUNICIPAL FRANCELINO PEREIRA DE ASSIS: Lula 138, Flávio 9 de 155 válidos (168 aptos, 168 votantes, UE2015). Zona rural (inferido pelo cadastro do local).
- POTIM (SP), zona 190, seção 154, PENITENCIÁRIA I DE POTIM: Lula 17, Flávio 3 de 22 válidos (24 aptos, 24 votantes, UE2015). Unidade prisional ou socioeducativa (inferido pelo cadastro do local); seção minúscula (24 votantes); 24 de 24 aptos em trânsito.
- SANTANA DO ACARAÚ (CE), zona 44, seção 193, ASSOCIAÇÃO COMUNITÁRIA DOS MORADORES DE CHOCALHO E DE CHINELO: Lula 53, Flávio 13 de 67 válidos (69 aptos, 69 votantes, UE2015). Zona rural (inferido pelo cadastro do local); seção pequena (69 votantes).
- CONGONHAS (MG), zona 85, seção 151, CENTRO MUNICIPAL DE EDUCAÇÃO INFANTIL ROSA CORDEIRO DE FREITAS: Lula 24, Flávio 18 de 43 válidos (46 aptos, 46 votantes, UE2015). Seção minúscula (46 votantes).
- SALVATERRA (PA), zona 3, seção 153, EMEIF SIRICARI: Lula 89, Flávio 26 de 117 válidos (120 aptos, 120 votantes, UE2022). Quilombo (inferido pelo cadastro do local).
- JACAREACANGA (PA), zona 102, seção 44, EMEF GETÚLIO VARGAS: Lula 0, Flávio 49 de 49 válidos (99 aptos, 50 votantes, UE2022). Zona rural (inferido pelo cadastro do local); seção pequena (50 votantes).
- MILHÃ (CE), zona 55, seção 163, E. E. I. E. F. IDELZUITE MONTEIRO DE OLIVEIRA: Lula 52, Flávio 15 de 69 válidos (73 aptos, 73 votantes, UE2015). Zona rural (inferido pelo cadastro do local); seção pequena (73 votantes); a zona inteira vota assim (Lula 76,1% na zona).
- DEPUTADO IRAPUAN PINHEIRO (CE), zona 55, seção 160, E.M.T.I. SÃO CAETANO: Lula 98, Flávio 20 de 122 válidos (127 aptos, 127 votantes, UE2015). Zona rural (inferido pelo cadastro do local); a zona inteira vota assim (Lula 76,4% na zona).
- ITAPETININGA (SP), zona 52, seção 386, FUNDAÇÃO CASA: Lula 0, Flávio 13 de 14 válidos (23 aptos, 15 votantes, UE2013). Unidade prisional ou socioeducativa (inferido pelo cadastro do local); seção minúscula (15 votantes); 23 de 23 aptos em trânsito.
- SÃO BERNARDO DO CAMPO (SP), zona 283, seção 538, CENTRO DE DETENÇÃO PROVISÓRIA (CDP) DE SBCAMPO: Lula 21, Flávio 0 de 24 válidos (29 aptos, 24 votantes, UE2015). Unidade prisional ou socioeducativa (inferido pelo cadastro do local); seção minúscula (24 votantes); 29 de 29 aptos em trânsito.
- CHAVES (PA), zona 17, seção 41, EMEIF JOSÉ VALERIO RODRIGUES: Lula 0, Flávio 52 de 53 válidos (82 aptos, 54 votantes, UE2022). Zona rural (inferido pelo cadastro do local); seção pequena (54 votantes).

Grupo mais anômalo na versão densa: 1.

- CIUDAD GUAYANA (ZZ), zona 1, seção 91, EMBAIXADA EM CARACAS: Lula 0, Flávio 0 de 0 válidos (72 aptos, 0 votantes, sem modelo). Exterior (inferido pelo cadastro do local); seção minúscula (0 votantes); urna de contingência; sistema de apuração (5).
- JACAREACANGA (PA), zona 102, seção 44, EMEF GETÚLIO VARGAS: Lula 0, Flávio 49 de 49 válidos (99 aptos, 50 votantes, UE2022). Zona rural (inferido pelo cadastro do local); seção pequena (50 votantes).
- ITAPETININGA (SP), zona 52, seção 386, FUNDAÇÃO CASA: Lula 0, Flávio 13 de 14 válidos (23 aptos, 15 votantes, UE2013). Unidade prisional ou socioeducativa (inferido pelo cadastro do local); seção minúscula (15 votantes); 23 de 23 aptos em trânsito.
- CÂNDIDO GODÓI (RS), zona 166, seção 81, ESCOLA STO INÁCIO (ABRANTES): Lula 0, Flávio 81 de 81 válidos (93 aptos, 84 votantes, UE2022). Seção pequena (84 votantes).
- POTIM (SP), zona 190, seção 154, PENITENCIÁRIA I DE POTIM: Lula 17, Flávio 3 de 22 válidos (24 aptos, 24 votantes, UE2015). Unidade prisional ou socioeducativa (inferido pelo cadastro do local); seção minúscula (24 votantes); 24 de 24 aptos em trânsito.
- CAPANEMA (PA), zona 25, seção 364, OLGA COSTA PEREIRA-EMEF- BAIRRO SANTA LUZIA: Lula 48, Flávio 17 de 70 válidos (73 aptos, 73 votantes, UE2022). Seção pequena (73 votantes).
- ARAÇATUBA (SP), zona 299, seção 229, UI/UIP-ARAÇÁ: Lula 19, Flávio 12 de 32 válidos (34 aptos, 34 votantes, UE2022). Unidade prisional ou socioeducativa (inferido pelo cadastro do local); seção minúscula (34 votantes); 34 de 34 aptos em trânsito.
- CHAVES (PA), zona 17, seção 41, EMEIF JOSÉ VALERIO RODRIGUES: Lula 0, Flávio 52 de 53 válidos (82 aptos, 54 votantes, UE2022). Zona rural (inferido pelo cadastro do local); seção pequena (54 votantes).
- OCARA (CE), zona 67, seção 275, IGREJA BATISTA SHALON JERUSALEM: Lula 51, Flávio 25 de 79 válidos (83 aptos, 83 votantes, UE2022). Seção pequena (83 votantes); a zona inteira vota assim (Lula 68,5% na zona).
- CONGONHAS (MG), zona 85, seção 151, CENTRO MUNICIPAL DE EDUCAÇÃO INFANTIL ROSA CORDEIRO DE FREITAS: Lula 24, Flávio 18 de 43 válidos (46 aptos, 46 votantes, UE2015). Seção minúscula (46 votantes).

Estabilidade (índice de Rand ajustado contra a versão pedida): segunda melhor semente 1,000; nanicas somadas 0,011; versão densa -0,052.

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

## Inferido (leitura dos números)

- As seções de 90% de Lula estão em zonas que já votam muito nele: mediana de 76,3% no resto da zona; o excesso típico da seção sobre a zona é de 17,1 pontos.
- Locais com nome de aldeia ou escola indígena: 1.428 seções, 565 delas com Lula em 90% ou mais (39,6% do tipo, contra 0,74% no total).
- Na especificação pedida, os três grupos não são geografia (V de Cramér entre grupo e região 0,13): separam as seções pelo padrão de zeros. 42,7% das células são zero e viram 0,0001; na seção mediana, de 327 aptos, um voto fica a 3,4 unidades de log do zero (de 3,2 a 3,8 entre o primeiro e o último décimo das seções), e a mistura usa esse degrau para separar grupos. O padrão que define cada grupo: grupo 1, sem voto nas cinco candidaturas menos votadas (100,0% das seções do grupo, contra 0,0% no grupo 3); grupo 2, com voto em ao menos uma das cinco candidaturas menos votadas (98,3% das seções do grupo, contra 0,0% no grupo 1); grupo 3, sem voto em Samara (100,0% das seções do grupo, contra 30,9% no grupo 2).
- Na versão com nanicas somadas, o V de Cramér entre grupo e região é 0,26; o padrão de zeros ainda separa os grupos (Renan Santos, 100 pontos de diferença na proporção de zeros).
- Na versão com cinco partes, o V de Cramér entre grupo e região é 0,36.
- Na projeção, o componente 1 tem a maior carga em Romeu Zema (0,93) e o componente 2, em Ronaldo Caiado (0,82). As nuvens que se veem no plano são seções com e sem voto nessas partes: um corte no componente 1 separa as seções sem voto em Romeu Zema (63,3% do total) com acerto balanceado de 100,0%; um corte no componente 2 separa as seções sem voto em Ronaldo Caiado (7,3% do total) com acerto balanceado de 99,4%. A mistura com k = 3 não reproduz a divisão por Romeu Zema e Ronaldo Caiado (12 e 11 pontos de diferença na proporção de zeros entre grupos). As partes que definem os grupos quase não pesam no plano (carga máxima em módulo nos dois componentes: as cinco candidaturas menos votadas, 0,12; Samara, 0,04): essa parte da divisão não aparece na figura.
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
- Na especificação pedida, os três grupos não são geografia (V de Cramér entre grupo e região 0,13): separam as seções pelo padrão de zeros. 42,7% das células são zero e viram 0,0001; na seção mediana, de 327 aptos, um voto fica a 3,4 unidades de log do zero (de 3,2 a 3,8 entre o primeiro e o último décimo das seções), e a mistura usa esse degrau para separar grupos. O padrão que define cada grupo: grupo 1, sem voto nas cinco candidaturas menos votadas (100,0% das seções do grupo, contra 0,0% no grupo 3); grupo 2, com voto em ao menos uma das cinco candidaturas menos votadas (98,3% das seções do grupo, contra 0,0% no grupo 1); grupo 3, sem voto em Samara (100,0% das seções do grupo, contra 30,9% no grupo 2).
- Dentro da zona há diferença entre modelos separável de zero, o que não é efeito da urna enquanto a alocação dos modelos dentro da zona não for aleatória: na mesma zona, a urna mais nova dá a Flávio −0,73 ponto em relação à mais velha (IC 95% de −1,03 a −0,44, não contém o zero); sem o controle, −1,42; 531 zonas.

## Limites

- Zona é o par município e zona eleitoral, como no arquivo de zona do TSE.
- Seções agregadas não têm boletim próprio: o voto delas está no da seção principal, e os aptos do boletim já as incluem.
- Tipo de local é inferência por palavra-chave no cadastro de locais do TSE; o nome do local não prova o perfil do eleitor.
- O modelo da urna vem do log da própria urna; urna de reserva ou contingência aparece com o modelo da urna que gravou o boletim.
- A comparação com 2022 casa a seção pelo número e pelo nome do local; seção renumerada ou local trocado fica de fora.
- Seções pequenas inflam percentuais: 100% de 30 válidos não é o mesmo que 100% de 300. Por isso os cortes por tamanho e o corte de 100 votantes.
- A mistura gaussiana sobre log-razões com zero trocado por 0,0001 é sensível ao padrão de zeros; a leitura política vem da versão densa.
- Benford e último dígito são curiosidade metodológica, não teste de fraude.

## Reprodução

```
python3 scripts/apuracao-2026-secoes.py            # exige coleta completa
python3 scripts/apuracao-2026-secoes.py --parcial  # com o que já existe
pytest -q tests/test_apuracao_2026_secoes.py
```
