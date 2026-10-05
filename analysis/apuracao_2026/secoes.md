# Análise por seção (boletins de urna), presidente, 1º turno de 2026

Gerado em 2026-10-05T16:55:31Z por `scripts/apuracao-2026-secoes.py`. Dados em `analysis/apuracao_2026/dados/secoes.json` (contrato em `analysis/apuracao_2026/CONTRATO_SECOES.md`).

> Seção atípica é seção que pede explicação, não indício de irregularidade. O que resolve cada caso é documento: ata da mesa, log da urna e plano de alocação das urnas do TRE.

**Coleta parcial.** 73.935 seções válidas de 499.248 seções principais do país; UFs completas: AC, AL, AP, DF, ES, MS, MT, RN, RO, RR, SE, TO. Os números mudam quando a coleta terminar.

## Cobertura

- Seções no cadastro do TSE (cs): 517.179, das quais 17.931 agregadas (sem boletim próprio).
- Boletins lidos: 75.244; válidos para a análise: 73.935.
- Fora: 424.004 seções, seção principal sem boletim de urna no banco (ainda não coletada ou sem arquivo).
- Fora: 1.143 seções, soma das seções diferente do arquivo de zona do TSE.
- Fora: 158 seções, soma das seções diferente do arquivo de zona do TSE, que congelou com menos seções totalizadas do que as existentes (st < ts).
- Fora: 8 seções, zona ainda não conferida contra o arquivo de zona do TSE.
- Nas seções válidas: Flávio 49,30% e Lula 44,04% dos válidos, 17.300.229 válidos.

## A. Seções com 90% ou mais para um candidato

Quem espera achar seções novas de 90% encontra as velhas: 128 de 164 seções casadas de Lula já estavam acima de 90% em 2022.

| candidato | limiar | seções | com 100+ votantes | aptos | % das seções |
|---|---|---|---|---|---|
| Lula | 90% | 316 | 292 | 77.911 | 0,43 |
| Lula | 95% | 123 | 110 | 27.729 | 0,17 |
| Lula | 100% | 10 | 4 | 1.170 | 0,01 |
| Flávio | 90% | 31 | 28 | 8.150 | 0,04 |
| Flávio | 95% | 2 | 1 | 451 | 0,00 |
| Flávio | 100% | 0 | 0 | 0 | 0,00 |

Por tamanho (votantes da seção):

| faixa | seções | Lula ≥ 90% | % | Flávio ≥ 90% | % |
|---|---|---|---|---|---|
| 1–49 | 69 | 6 | 8,70 | 1 | 1,45 |
| 50–99 | 419 | 18 | 4,30 | 2 | 0,48 |
| 100–199 | 12.722 | 135 | 1,06 | 6 | 0,05 |
| 200–299 | 51.287 | 150 | 0,29 | 17 | 0,03 |
| 300–399 | 9.390 | 7 | 0,07 | 5 | 0,05 |
| 400+ | 48 | 0 | 0,00 | 0 | 0,00 |

- Lula: 316 seções em 90% ou mais; o resto da zona dá 54,6% a Lula (mediana) e o excesso da seção sobre a zona é 40,5 pontos (mediana); 246 seções ficam 20 pontos ou mais acima da própria zona.
- Flávio: 31 seções em 90% ou mais; o resto da zona dá 74,1% a Flávio (mediana) e o excesso da seção sobre a zona é 17,4 pontos (mediana); 10 seções ficam 20 pontos ou mais acima da própria zona.

Por tipo de local (inferência por palavra-chave; regras no JSON):

| tipo | seções | Lula ≥ 90% | % do tipo | Flávio ≥ 90% | % do tipo |
|---|---|---|---|---|---|
| escola ou universidade | 53.557 | 26 | 0,05 | 19 | 0,04 |
| outro | 12.141 | 5 | 0,04 | 2 | 0,02 |
| zona rural | 7.051 | 49 | 0,69 | 9 | 0,13 |
| aldeia ou terra indígena | 528 | 222 | 42,05 | 1 | 0,19 |
| assentamento | 416 | 6 | 1,44 | 0 | 0,00 |
| quilombo | 113 | 6 | 5,31 | 0 | 0,00 |
| unidade prisional ou socioeducativa | 60 | 2 | 3,33 | 0 | 0,00 |
| voto em trânsito | 52 | 0 | 0,00 | 0 | 0,00 |
| exterior | 17 | 0 | 0,00 | 0 | 0,00 |

Cruzamento com as 50 zonas mais atípicas de `anomalias.json`: 14 estão na base, 3 têm ao menos uma seção de 90%. Taxa de seções com Lula em 90% ou mais: 2,59% nessas zonas e 0,41% nas demais; Flávio: 0,00% e 0,04%.

Mesma seção em 2022 (mesma UF, município, zona e número de seção, e mesmo nome do local de votação nos dois cadastros (sem acento e sem espaços repetidos)): 47.870 de 73.935 seções casadas.
- Lula em 90% ou mais em 2026, casadas: 164; Lula já tinha 90% ou mais no 1º turno de 2022 em 128 e no 2º turno em 152; mediana de 2022 93,3% (1º turno); variação mediana 0,8 pontos.
- Flávio em 90% ou mais em 2026, casadas: 12; Bolsonaro já tinha 90% ou mais no 1º turno de 2022 em 1 e no 2º turno em 6; mediana de 2022 84,7% (1º turno); variação mediana 6,1 pontos.

Amostras (as de maior excesso sobre a zona, 100 votantes ou mais):

- GUARANTÃ DO NORTE (MT), zona 44, seção 284, ALDEIA - SANKORASSAN: Lula 144, Flávio 3 de 150 válidos (171 aptos, 150 votantes, UE2020); Lula 96,0% na seção e 15,6% na zona. Aldeia ou terra indígena (inferido pelo cadastro do local).
- MARCELÂNDIA (MT), zona 32, seção 279, ESCOLA ESTADUAL INDÍGENA KAMADU: Lula 184, Flávio 2 de 190 válidos (231 aptos, 190 votantes, UE2020); Lula 96,8% na seção e 18,9% na zona. Aldeia ou terra indígena (inferido pelo cadastro do local).
- CONFRESA (MT), zona 28, seção 200, ESCOLA ESTADUAL TAPI'ITAWA: Lula 296, Flávio 0 de 297 válidos (315 aptos, 297 votantes, UE2022); Lula 99,7% na seção e 21,9% na zona. Aldeia ou terra indígena (inferido pelo cadastro do local).
- CONFRESA (MT), zona 28, seção 158, ESCOLA ESTADUAL TAPI'ITAWA: Lula 119, Flávio 1 de 120 válidos (133 aptos, 120 votantes, UE2022); Lula 99,2% na seção e 21,9% na zona. Aldeia ou terra indígena (inferido pelo cadastro do local).
- QUERÊNCIA (MT), zona 53, seção 163, AUDITÓRIO-SEDE DA ALDEIA KHIKATXI: Lula 247, Flávio 3 de 255 válidos (313 aptos, 259 votantes, UE2022); Lula 96,9% na seção e 21,4% na zona. Aldeia ou terra indígena (inferido pelo cadastro do local).
- ALTO ALEGRE (RR), zona 3, seção 226, POSTO DE SAÚDE DA SESAI - SIKAMABIU: Lula 235, Flávio 3 de 238 válidos (304 aptos, 238 votantes, UE2022); Lula 98,7% na seção e 23,9% na zona. Aldeia ou terra indígena (inferido pelo cadastro do local).
- CRUZEIRO DO SUL (AC), zona 4, seção 457, ESCOLA TAMÃKÃYÃ: Lula 151, Flávio 0 de 151 válidos (208 aptos, 155 votantes, UE2022); Lula 100,0% na seção e 24,9% na zona. Aldeia ou terra indígena (inferido pelo cadastro do local).
- JI-PARANÁ (RO), zona 30, seção 125, IKOLEN - POSTO INDÍGENA: Lula 225, Flávio 5 de 231 válidos (263 aptos, 233 votantes, UE2022); Lula 97,4% na seção e 22,5% na zona. Aldeia ou terra indígena (inferido pelo cadastro do local).
- UIRAMUTÃ (RR), zona 7, seção 56, ESCOLA MUNICIPAL INDÍGENA TANCREDO NEVES: Lula 25, Flávio 293 de 318 válidos (366 aptos, 321 votantes, UE2022); Flávio 92,1% na seção e 29,9% na zona. Aldeia ou terra indígena (inferido pelo cadastro do local).
- XAPURI (AC), zona 2, seção 36, ESCOLA ESTADUAL BÁRBARA VIEIRA DE SANTANA - SGAL SÃO JOSÉ: Lula 7, Flávio 113 de 125 válidos (154 aptos, 132 votantes, UE2022); Flávio 90,4% na seção e 61,8% na zona. Zona rural (inferido pelo cadastro do local).
- PORTO VELHO (RO), zona 6, seção 568, MORADORES DA LINHA 8 - ASSOCIAÇÃO - DISTRITO UNIAO BANDEIRANTE: Lula 15, Flávio 212 de 230 válidos (266 aptos, 233 votantes, UE2020); Flávio 92,2% na seção e 63,3% na zona. Sem regra estrutural acionada: comparar com ata e log da seção.
- PORTO VELHO (RO), zona 6, seção 540, MORADORES DA LINHA 8 - ASSOCIAÇÃO - DISTRITO UNIAO BANDEIRANTE: Lula 20, Flávio 209 de 231 válidos (268 aptos, 233 votantes, UE2022); Flávio 90,5% na seção e 63,3% na zona. Sem regra estrutural acionada: comparar com ata e log da seção.
- PORTO VELHO (RO), zona 6, seção 542, CÉSAR FREITAS CASSOL -ESCOLA ESTADUAL - DISTRITO UNIÃO BANDEIRANTE: Lula 16, Flávio 188 de 208 válidos (295 aptos, 212 votantes, UE2020); Flávio 90,4% na seção e 63,3% na zona. Sem regra estrutural acionada: comparar com ata e log da seção.
- ALTA FLORESTA D'OESTE (RO), zona 17, seção 88, IZIDORO STÉDILE - ESCOLA MUNICIPAL - DISTR IZIDOLÂNDIA: Lula 9, Flávio 120 de 129 válidos (177 aptos, 129 votantes, UE2022); Flávio 93,0% na seção e 70,1% na zona. Sem regra estrutural acionada: comparar com ata e log da seção.
- BRASILÉIA (AC), zona 6, seção 128, ESCOLA VALDOMIRO FERREIRA BARROSO - KM 19: Lula 14, Flávio 190 de 211 válidos (264 aptos, 222 votantes, UE2022); Flávio 90,0% na seção e 69,6% na zona. Zona rural (inferido pelo cadastro do local).
- JUÍNA (MT), zona 35, seção 335, ESCOLA MUNICIPAL OSVALDO CRUZ: Lula 5, Flávio 92 de 101 válidos (134 aptos, 105 votantes, UE2022); Flávio 91,1% na seção e 71,4% na zona. Zona rural (inferido pelo cadastro do local).

## B. Mistura gaussiana (k = 4)

- Na especificação pedida, os quatro grupos não são geografia (V de Cramér entre grupo e região 0,09): separam as seções pelo padrão de zeros. 44,4% das células são zero e viram 0,0001; no log, uma candidatura sem voto fica a 3 ou 4 unidades de uma com um voto, e a mistura usa esse degrau para separar grupos (a parte que mais distingue os grupos é `n55`, com 99 pontos de diferença na proporção de zeros entre eles).
- Na versão com nanicas somadas, o V de Cramér entre grupo e região é 0,18; o padrão de zeros ainda separa os grupos (`n55`, 100 pontos).
- Na versão com cinco partes, o V de Cramér entre grupo e região é 0,41.
- Grupo 0: Lula 59% dos válidos, abstenção 20%, Nordeste 56% das seções; 1.096 seções.
- Grupo 1: Flávio 49% dos válidos, abstenção 20%, Nordeste 37% das seções; 58.389 seções.
- Grupo 2: Flávio 50% dos válidos, abstenção 20%, Nordeste 35% das seções; 9.789 seções.
- Grupo 3: Flávio 52% dos válidos, abstenção 19%, Centro-Oeste 46% das seções; 4.661 seções.
- O grupo de menor densidade e maior dispersão é o 3 (Flávio 52% dos válidos, abstenção 19%, Centro-Oeste 46% das seções); as 20 seções menos prováveis dele vêm com o que provavelmente as explica.

Método: log-razão centrada (CLR) das 15 frações, com zero trocado por 0,0001 antes do log; a mistura é ajustada nas 14 coordenadas ortonormais do subespaço de soma zero (ILR), rotação que preserva Mahalanobis e densidade relativa. Covariância completa, 10 inicializações, semente 20261005, ajuste sobre 73.935 seções (o país inteiro, sem amostra).

BIC (menor é melhor; com os degraus de zeros, a comparação entre k é instável e serve só de contraste):

- k = 3: BIC 1.407.067,6, log-verossimilhança média -9,488
- k = 4: BIC -880.664,0, log-verossimilhança média 5,992
- k = 5: BIC -188.013,7, log-verossimilhança média 1,317

| grupo | rótulo | seções | aptos médios | log-veross. média | log det Σ |
|---|---|---|---|---|---|
| 0 | Lula 59% dos válidos, abstenção 20%, Nordeste 56% das seções | 1.096 | 277 | -10,15 | -25,8 |
| 1 | Flávio 49% dos válidos, abstenção 20%, Nordeste 37% das seções | 58.389 | 302 | 12,32 | -60,9 |
| 2 | Flávio 50% dos válidos, abstenção 20%, Nordeste 35% das seções | 9.789 | 318 | -17,42 | -8,9 |
| 3 | Flávio 52% dos válidos, abstenção 19%, Centro-Oeste 46% das seções | 4.661 | 331 | -20,35 | -4,5 |

Versão densa (mesma mistura (k = 4, mesma semente) sobre cinco partes quase sem zeros: Lula, Flávio, as outras dez candidaturas somadas, brancos e nulos somados, abstenção):

| grupo | rótulo | seções | aptos médios | log-veross. média | log det Σ |
|---|---|---|---|---|---|
| 0 | Lula 64% dos válidos, abstenção 19%, Nordeste 87% das seções | 21.228 | 301 | -2,55 | -8,2 |
| 1 | Lula 60% dos válidos, abstenção 19%, Norte 38% das seções | 1.303 | 235 | -10,67 | 2,1 |
| 2 | Flávio 53% dos válidos, abstenção 19%, Centro-Oeste 38% das seções | 33.131 | 318 | -1,07 | -10,0 |
| 3 | Flávio 65% dos válidos, abstenção 23%, Centro-Oeste 49% das seções | 18.273 | 293 | -2,98 | -7,4 |

Grupo mais anômalo na versão pedida: 3. Critério: soma dos postos de menor log-verossimilhança média e de maior dispersão (log-determinante da covariância); empate decidido pela menor log-verossimilhança média. Amostras: as 20 seções de menor log-verossimilhança dentro do componente.

- MAZAGÃO (AP), zona 5, seção 33, ESCOLA MUNICIPAL BARRO ALTO: Lula 43, Flávio 0 de 47 válidos (67 aptos, 49 votantes, UE2020). Zona rural (inferido pelo cadastro do local); seção minúscula (49 votantes).
- PEIXOTO DE AZEVEDO (MT), zona 33, seção 255, ESCOLA ESTADUAL INDIGENA METUKTIRE: Lula 156, Flávio 0 de 159 válidos (231 aptos, 159 votantes, UE2020). Aldeia ou terra indígena (inferido pelo cadastro do local).
- FORMOSO DO ARAGUAIA (TO), zona 15, seção 72, ALDEIA SÃO JOÃO: Lula 126, Flávio 0 de 127 válidos (159 aptos, 132 votantes, UE2020). Aldeia ou terra indígena (inferido pelo cadastro do local).
- TOCANTINÓPOLIS (TO), zona 9, seção 184, ESCOLA ESTADUAL INDÍGENA KUNITIK: Lula 59, Flávio 0 de 60 válidos (62 aptos, 60 votantes, UE2022). Aldeia ou terra indígena (inferido pelo cadastro do local); seção pequena (60 votantes).
- CONFRESA (MT), zona 28, seção 200, ESCOLA ESTADUAL TAPI'ITAWA: Lula 296, Flávio 0 de 297 válidos (315 aptos, 297 votantes, UE2022). Aldeia ou terra indígena (inferido pelo cadastro do local).
- NÍSIA FLORESTA (RN), zona 67, seção 123, ESC MUN ANA CARDOSO BARROS: Lula 166, Flávio 64 de 240 válidos (254 aptos, 250 votantes, UE2020). Sem regra estrutural acionada: comparar com ata e log da seção.
- MARACAJU (MS), zona 16, seção 81, EM PROFESSORA IRMA DE LIMA MATOS (NOVO): Lula 52, Flávio 209 de 270 válidos (306 aptos, 272 votantes, UE2015). Sem regra estrutural acionada: comparar com ata e log da seção.
- AMAMBAI (MS), zona 1, seção 191, EM POLO INDIGENA MBO'EROY GUARANI KAIOWA: Lula 144, Flávio 16 de 162 válidos (293 aptos, 169 votantes, UE2020). Aldeia ou terra indígena (inferido pelo cadastro do local).
- MARCELÂNDIA (MT), zona 32, seção 279, ESCOLA ESTADUAL INDÍGENA KAMADU: Lula 184, Flávio 2 de 190 válidos (231 aptos, 190 votantes, UE2020). Aldeia ou terra indígena (inferido pelo cadastro do local).
- PARANATINGA (MT), zona 57, seção 31, ESCOLA MUNICIPAL CEREMECE SEREPSE -MARECHAL RONDON: Lula 186, Flávio 3 de 194 válidos (295 aptos, 196 votantes, UE2020). Aldeia ou terra indígena (inferido pelo cadastro do local).
- AMÃ (ZZ), zona 1, seção 1931, EMBAIXADA DO BRASIL EM AMÃ: Lula 352, Flávio 31 de 405 válidos (744 aptos, 430 votantes, UE2015). Exterior (inferido pelo cadastro do local); a zona inteira vota assim (Lula 86,2% na zona).
- ALAGOA GRANDE (PB), zona 9, seção 171, ESCOLA MUNICIPAL FIRMO SANTINO DA SILVA: Lula 118, Flávio 13 de 139 válidos (151 aptos, 149 votantes, UE2020). Quilombo (inferido pelo cadastro do local).
- CAARAPÓ (MS), zona 28, seção 70, EMPG NHANDEJARA: Lula 128, Flávio 14 de 143 válidos (289 aptos, 153 votantes, UE2020). Aldeia ou terra indígena (inferido pelo cadastro do local).
- AMAMBAI (MS), zona 1, seção 158, EE INDÍGENA MBO'EROY GUARANI KAIOWÁ: Lula 147, Flávio 8 de 162 válidos (331 aptos, 167 votantes, UE2020). Aldeia ou terra indígena (inferido pelo cadastro do local).
- PEDRA BRANCA DO AMAPARI (AP), zona 11, seção 32, ESCOLA ESTADUAL DAS ALDEIAS WAIÃPI: Lula 225, Flávio 12 de 239 válidos (301 aptos, 245 votantes, UE2020). Aldeia ou terra indígena (inferido pelo cadastro do local).
- ABU DHABI (ZZ), zona 1, seção 1981, TWO SEASONS HOTEL: Lula 56, Flávio 89 de 169 válidos (393 aptos, 175 votantes, UE2015). Exterior (inferido pelo cadastro do local); a zona inteira vota assim (Flávio 48,6% na zona).
- TOBIAS BARRETO (SE), zona 23, seção 146, CENTRO COMUNITÁRIO ANTÔNIO JOSÉ FONTES: Lula 196, Flávio 36 de 242 válidos (259 aptos, 250 votantes, UE2020). Zona rural (inferido pelo cadastro do local).
- PARANATINGA (MT), zona 57, seção 84, ESCOLA MUNICIPAL CEREMECE SEREPSE -MARECHAL RONDON: Lula 212, Flávio 7 de 224 válidos (269 aptos, 224 votantes, UE2020). Aldeia ou terra indígena (inferido pelo cadastro do local).
- AMAMBAI (MS), zona 1, seção 130, EM POLO INDIGENA MBO'EROY GUARANI KAIOWA: Lula 150, Flávio 5 de 158 válidos (300 aptos, 161 votantes, UE2020). Aldeia ou terra indígena (inferido pelo cadastro do local).
- ABIDJÃ (ZZ), zona 1, seção 1, CHANCELARIA DA EMBAIXADA DO BRASIL EM ABIDJÃ: Lula 24, Flávio 13 de 44 válidos (91 aptos, 44 votantes, sem modelo). Exterior (inferido pelo cadastro do local); seção minúscula (44 votantes); urna de contingência; sistema de apuração (5); a zona inteira vota assim (Lula 54,5% na zona).

Grupo mais anômalo na versão densa: 1.

- UIRAMUTÃ (RR), zona 7, seção 124, ESCOLA ESTADUAL INDÍGENA TUXAUA CRETÁCIO: Lula 51, Flávio 0 de 51 válidos (52 aptos, 52 votantes, UE2022). Aldeia ou terra indígena (inferido pelo cadastro do local); seção pequena (52 votantes).
- MAZAGÃO (AP), zona 5, seção 33, ESCOLA MUNICIPAL BARRO ALTO: Lula 43, Flávio 0 de 47 válidos (67 aptos, 49 votantes, UE2020). Zona rural (inferido pelo cadastro do local); seção minúscula (49 votantes).
- PEIXOTO DE AZEVEDO (MT), zona 33, seção 255, ESCOLA ESTADUAL INDIGENA METUKTIRE: Lula 156, Flávio 0 de 159 válidos (231 aptos, 159 votantes, UE2020). Aldeia ou terra indígena (inferido pelo cadastro do local).
- ARACRUZ (ES), zona 20, seção 232, ASSOCIAÇÃO DA ALDEIA INDÍGENA NOVA ESPERANÇA (ALDEIA NOVA ESPERANÇA): Lula 33, Flávio 0 de 33 válidos (56 aptos, 33 votantes, UE2020). Aldeia ou terra indígena (inferido pelo cadastro do local); seção minúscula (33 votantes).
- TOCANTINÓPOLIS (TO), zona 9, seção 184, ESCOLA ESTADUAL INDÍGENA KUNITIK: Lula 59, Flávio 0 de 60 válidos (62 aptos, 60 votantes, UE2022). Aldeia ou terra indígena (inferido pelo cadastro do local); seção pequena (60 votantes).
- FORMOSO DO ARAGUAIA (TO), zona 15, seção 72, ALDEIA SÃO JOÃO: Lula 126, Flávio 0 de 127 válidos (159 aptos, 132 votantes, UE2020). Aldeia ou terra indígena (inferido pelo cadastro do local).
- PORTO VELHO (RO), zona 6, seção 516, KYOWÃ - ESCOLA ESTADUAL - ALDEIA KARITIANA: Lula 100, Flávio 0 de 102 válidos (115 aptos, 104 votantes, UE2020). Aldeia ou terra indígena (inferido pelo cadastro do local).
- GOIATINS (TO), zona 32, seção 60, ESCOLA INDIGENA TXUARET: Lula 106, Flávio 0 de 107 válidos (130 aptos, 112 votantes, UE2022). Aldeia ou terra indígena (inferido pelo cadastro do local).
- UIRAMUTÃ (RR), zona 7, seção 61, IGREJA INDIGENA CORAÇÃO DO MUNDO: Lula 185, Flávio 0 de 185 válidos (212 aptos, 185 votantes, UE2022). Aldeia ou terra indígena (inferido pelo cadastro do local).
- CONFRESA (MT), zona 28, seção 200, ESCOLA ESTADUAL TAPI'ITAWA: Lula 296, Flávio 0 de 297 válidos (315 aptos, 297 votantes, UE2022). Aldeia ou terra indígena (inferido pelo cadastro do local).

Estabilidade (índice de Rand ajustado contra a versão pedida): outra semente 0,173; nanicas somadas 0,092; versão densa -0,014.

## C. Modelo de urna

- O modelo da urna não move o voto de forma separável de zero dentro da zona: na mesma zona, a urna mais nova dá a Flávio 0,00 ponto em relação à mais velha (IC 95% de -0,70 a 0,69, contém o zero); sem o controle, -1,34; 79 zonas.
- No mesmo prédio, a urna mais nova dá a Flávio 0,13 ponto em relação à mais velha (IC 95% de -0,02 a 0,28, contém o zero); sem o controle, -1,73; 2.312 locais.
- Em 2022, na mesma zona, a UE2020 dá a Bolsonaro 1,41 ponto em relação à UE2015 (IC 95% de 0,84 a 2,00, não contém o zero); sem o controle, 1,32; 264 zonas.
- Em 2022, no mesmo prédio, a UE2020 dá a Bolsonaro 0,85 ponto em relação à UE2015 (IC 95% de -0,15 a 2,04, contém o zero); sem o controle, 2,29; 85 locais.
- Nas mesmas seções de 2022 para 2026, agrupadas pelo modelo de 2022, a urna mais nova dá a Flávio, sobre Bolsonaro, -0,18 ponto em relação à mais velha (IC 95% de -0,85 a 0,49, contém o zero); sem o controle, -0,49; 22 zonas.

Bruto (soma dos votos por modelo, sem controle):

| modelo | seções | Flávio % | Lula % | abstenção % | brancos % | nulos % |
|---|---|---|---|---|---|---|
| UE2013 | 1.933 | 44,81 | 47,83 | 19,79 | 1,84 | 3,29 |
| UE2015 | 10.559 | 47,40 | 45,03 | 20,32 | 1,61 | 2,73 |
| UE2020 | 31.622 | 49,80 | 43,58 | 19,94 | 1,42 | 2,63 |
| UE2022 | 29.816 | 49,80 | 43,90 | 20,15 | 1,39 | 2,73 |
| sem modelo | 5 | 26,09 | 60,87 | 52,58 | 0,00 | 0,00 |

Dentro da zona (Diferença (modelo b menos modelo a) dentro do par município e zona com ao menos 20 seções de cada modelo, média ponderada pelos votantes das seções comparadas; IC por bootstrap de zonas.):

| a → b | unidades | seções a/b | Flávio pp | Lula pp | nulos pp | bruto Flávio |
|---|---|---|---|---|---|---|
| UE2013 → UE2015 | 13 | 1.243/2.269 | 0,36 (IC 95% de -1,36 a 2,03) | -0,64 (IC 95% de -2,38 a 1,17) | -0,12 (IC 95% de -0,31 a 0,08) | 2,44 |
| UE2013 → UE2022 | 4 | 87/377 | -4,70 (IC 95% de -6,89 a -2,65) | 5,00 (IC 95% de 2,76 a 7,26) | 0,12 (IC 95% de -0,27 a 0,50) | -4,76 |
| UE2015 → UE2022 | 6 | 1.304/495 | -0,47 (IC 95% de -2,97 a 2,50) | 0,77 (IC 95% de -2,19 a 3,20) | 0,10 (IC 95% de -0,05 a 0,23) | -0,75 |
| UE2020 → UE2022 | 64 | 5.091/5.053 | -0,34 (IC 95% de -0,89 a 0,13) | 0,33 (IC 95% de -0,12 a 0,83) | -0,06 (IC 95% de -0,14 a 0,02) | -1,01 |
| mais velha → mais nova | 79 | 6.764/6.943 | 0,00 (IC 95% de -0,70 a 0,69) | -0,06 (IC 95% de -0,77 a 0,62) | -0,07 (IC 95% de -0,15 a 0,01) | -1,34 |

Dentro do mesmo local (Diferença (modelo b menos modelo a) dentro do mesmo local de votação (mesmo prédio), com ao menos uma seção de cada modelo; IC por bootstrap de locais.):

| a → b | unidades | seções a/b | Flávio pp | Lula pp | nulos pp | bruto Flávio |
|---|---|---|---|---|---|---|
| UE2013 → UE2015 | 277 | 765/1.637 | 0,13 (IC 95% de -0,30 a 0,55) | -0,17 (IC 95% de -0,60 a 0,28) | -0,02 (IC 95% de -0,16 a 0,13) | -2,35 |
| UE2013 → UE2022 | 2 | 10/9 | 2,97 (IC 95% de 1,29 a 3,79) | -1,55 (IC 95% de -2,55 a 0,50) | -0,93 (IC 95% de -1,38 a 0,00) | 0,92 |
| UE2015 → UE2022 | 1 | 2/14 | 1,72 (IC 95% de 1,72 a 1,72) | -2,24 (IC 95% de -2,24 a -2,24) | 0,01 (IC 95% de 0,01 a 0,01) | 1,72 |
| UE2020 → UE2022 | 2.032 | 6.573/6.781 | 0,12 (IC 95% de -0,03 a 0,28) | -0,13 (IC 95% de -0,29 a 0,02) | -0,08 (IC 95% de -0,13 a -0,02) | -1,09 |
| mais velha → mais nova | 2.312 | 7.350/8.441 | 0,13 (IC 95% de -0,02 a 0,28) | -0,14 (IC 95% de -0,28 a 0,00) | -0,07 (IC 95% de -0,12 a -0,02) | -1,73 |

Variação contra a mesma seção em 2022 (Diferença entre modelos, dentro do par município e zona, da variação de cada seção contra ela mesma em 2022 (Flávio 2026 menos Bolsonaro 1º turno 2022; Lula 2026 menos Lula 2022, em % dos válidos). A linha de base de 2022 da mesma seção tira o perfil político do lugar; só seções casadas pelo número e pelo nome do local.):

- UE2013 → UE2015: 6 zonas; Flávio menos Bolsonaro 0,30 (IC 95% de -0,15 a 0,71); Lula -0,55 (IC 95% de -1,16 a 0,11)
- UE2013 → UE2022: 1 zonas; Flávio menos Bolsonaro -0,58 (IC 95% de -0,58 a -0,58); Lula 0,43 (IC 95% de 0,43 a 0,43)
- UE2015 → UE2022: 6 zonas; Flávio menos Bolsonaro 0,60 (IC 95% de -0,05 a 1,21); Lula -0,66 (IC 95% de -1,29 a -0,05)
- UE2020 → UE2022: 34 zonas; Flávio menos Bolsonaro 0,10 (IC 95% de -0,08 a 0,32); Lula -0,21 (IC 95% de -0,48 a 0,01)
- mais velha → mais nova: 45 zonas; Flávio menos Bolsonaro 0,24 (IC 95% de 0,04 a 0,46); Lula -0,37 (IC 95% de -0,63 a -0,14)

Troca de urna entre 2022 e 2026 (mesma seção; rótulo = modelo de 2022; 47.672 seções casadas). Variação de cada seção de 2022 para 2026 (Flávio 2026 menos Bolsonaro 1º turno 2022, em % dos válidos), comparada entre seções agrupadas pelo modelo da urna de 2022 dentro do par município e zona. Diferença b menos a: se a urna velha (a) de 2022 tivesse tirado voto de Bolsonaro, a diferença seria negativa.

- UE2009 → UE2020: 2 zonas; variação de Flávio sobre Bolsonaro 0,62 (IC 95% de -1,40 a 1,68)
- UE2010 → UE2020: 2 zonas; variação de Flávio sobre Bolsonaro 1,25 (IC 95% de 1,09 a 1,97)
- UE2013 → UE2020: 1 zonas; variação de Flávio sobre Bolsonaro -0,56 (IC 95% de -0,56 a -0,56)
- UE2015 → UE2020: 6 zonas; variação de Flávio sobre Bolsonaro -0,47 (IC 95% de -2,28 a 0,65)
- mais velha → mais nova: 22 zonas; variação de Flávio sobre Bolsonaro -0,18 (IC 95% de -0,85 a 0,49)

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

### Registro (SP)

2026: seções de Registro ainda não coletadas.

2022 (1º turno): 154 seções.
- zona 172, UE2009: 2 seções, Bolsonaro 56,25%, Lula 34,79%, nulos 1,79%
- zona 172, UE2010: 35 seções, Bolsonaro 52,54%, Lula 38,69%, nulos 2,53%
- zona 172, UE2011: 4 seções, Bolsonaro 54,42%, Lula 39,11%, nulos 1,56%
- zona 172, UE2013: 7 seções, Bolsonaro 55,02%, Lula 38,37%, nulos 2,44%
- zona 172, UE2015: 32 seções, Bolsonaro 57,95%, Lula 33,81%, nulos 2,65%
- zona 172, UE2020: 74 seções, Bolsonaro 58,86%, Lula 32,21%, nulos 2,30%
- mesmo local em 2022, UE2009 → UE2010: 2 locais, Bolsonaro -0,09 (IC 95% de -1,84 a 3,43)
- mesmo local em 2022, UE2009 → UE2013: 1 locais, Bolsonaro 2,76 (IC 95% de 2,76 a 2,76)
- mesmo local em 2022, UE2010 → UE2013: 1 locais, Bolsonaro -0,67 (IC 95% de -0,67 a -0,67)
- mesmo local em 2022, mais velha → mais nova: 2 locais, Bolsonaro 1,17 (IC 95% de -1,84 a 2,76)

## D. Outras anomalias de seção

- Comparecimento acima de 100%: 0; igual a 100% (abstenção zero): 1, das quais 0 com 100 aptos ou mais.
- Zero voto em Lula com 200 votantes ou mais: 0 de 60.725 seções.
- Zero voto em Flávio com 200 votantes ou mais: 1 de 60.725 seções.
  - CONFRESA (MT), zona 28, seção 200, ESCOLA ESTADUAL TAPI'ITAWA: Lula 296, Flávio 0 de 297 válidos (315 aptos, 297 votantes, UE2022). Aldeia ou terra indígena (inferido pelo cadastro do local).
- Tipo de arquivo 1 (votação na urna (normal)): 73.914 seções; Flávio 49,30%, diferença média para o resto da zona 0,00 ponto.
- Tipo de arquivo 2 (votação recuperada (RED)): 16 seções; Flávio 46,43%, diferença média para o resto da zona 0,01 ponto.
- Tipo de arquivo 5 (sistema de apuração (5)): 5 seções; Flávio 26,09%, diferença média para o resto da zona sem resto de zona para comparar.
- Urna de seção: 73.522 seções; diferença média de Flávio para o resto da zona 0,00 ponto.
- Urna de contingência: 5 seções; diferença média de Flávio para o resto da zona sem resto de zona para comparar.
- Urna de reserva (seção): 408 seções; diferença média de Flávio para o resto da zona -0,12 ponto.
- Horários (Brasília): abertura depois das 9h em 30 seções, depois das 10h em 1; encerramento depois das 18h em 6.631, depois das 19h em 1.171, depois das 20h em 122.
- Boletins recebidos pelo TSE depois de meia-noite de 05/10: 0 seções, 0 válidos, Lula n/d%; diferença média de Lula para o resto da zona sem resto de zona para comparar.
- Boletins recebidos pelo TSE depois de 1h de 05/10: 0 seções, 0 válidos, Lula n/d%; diferença média de Lula para o resto da zona sem resto de zona para comparar.
- Benford do segundo dígito, Brasil, Lula: n = 73.899, qui-quadrado 627,1 com 9 graus de liberdade. Testes de dígito (último dígito e Benford do segundo dígito) são curiosidade metodológica: contagens de votos não seguem Benford por construção, e o teste rejeita ou aceita por motivos que nada têm a ver com fraude (Deckert, Myagkov e Ordeshook, 2011, Political Analysis 19(3)).

## Verificado (dado do TSE, conta direta)

- Base: 73.935 boletins de urna de seção, todos em zonas cuja soma das seções confere com o arquivo de zona do TSE (coleta parcial).
- Seções com Lula em 90% ou mais dos válidos: 316 (0,43% das seções), 77.911 eleitores aptos; com Flávio: 31 (0,04%), 8.150 aptos.
- Comparecimento acima de 100% dos aptos: 0 seções; igual a 100%: 1.
- Seções com 200 votantes ou mais e nenhum voto em Lula: 0; nenhum voto em Flávio: 1.
- Das 164 seções com Lula em 90% ou mais que existem com o mesmo número e o mesmo local em 2022, 128 já davam 90% ou mais a ele no 1º turno de 2022 e 161 davam 80% ou mais; mediana de 2022: 93,3%.

## Inferido (leitura dos números)

- As seções de 90% de Lula são, em boa parte, enclaves dentro de zonas que votam menos nele: mediana de 54,6% no resto da zona; o excesso típico da seção sobre a zona é de 40,5 pontos.
- Locais com nome de aldeia ou escola indígena: 528 seções, 222 delas com Lula em 90% ou mais (42,0% do tipo, contra 0,43% no total).
- Na especificação pedida, os quatro grupos não são geografia (V de Cramér entre grupo e região 0,09): separam as seções pelo padrão de zeros. 44,4% das células são zero e viram 0,0001; no log, uma candidatura sem voto fica a 3 ou 4 unidades de uma com um voto, e a mistura usa esse degrau para separar grupos (a parte que mais distingue os grupos é `n55`, com 99 pontos de diferença na proporção de zeros entre eles).
- Na versão com nanicas somadas, o V de Cramér entre grupo e região é 0,18; o padrão de zeros ainda separa os grupos (`n55`, 100 pontos).
- Na versão com cinco partes, o V de Cramér entre grupo e região é 0,41.
- O modelo da urna não move o voto de forma separável de zero dentro da zona: na mesma zona, a urna mais nova dá a Flávio 0,00 ponto em relação à mais velha (IC 95% de -0,70 a 0,69, contém o zero); sem o controle, -1,34; 79 zonas.
- No mesmo prédio, a urna mais nova dá a Flávio 0,13 ponto em relação à mais velha (IC 95% de -0,02 a 0,28, contém o zero); sem o controle, -1,73; 2.312 locais.
- Em 2022, na mesma zona, a UE2020 dá a Bolsonaro 1,41 ponto em relação à UE2015 (IC 95% de 0,84 a 2,00, não contém o zero); sem o controle, 1,32; 264 zonas.
- Em 2022, no mesmo prédio, a UE2020 dá a Bolsonaro 0,85 ponto em relação à UE2015 (IC 95% de -0,15 a 2,04, contém o zero); sem o controle, 2,29; 85 locais.
- Nas mesmas seções de 2022 para 2026, agrupadas pelo modelo de 2022, a urna mais nova dá a Flávio, sobre Bolsonaro, -0,18 ponto em relação à mais velha (IC 95% de -0,85 a 0,49, contém o zero); sem o controle, -0,49; 22 zonas.

## Juízo editorial

- Seção com 90% para um candidato é, na esmagadora maioria, lugar que sempre votou assim: aldeia, zona rural do Nordeste, comunidade pequena. O número chama atenção na manchete e some quando se olha a zona e 2022.
- Nenhum dos testes por seção aponta irregularidade. O que fica atípico exige explicação documental (ata da mesa, log da urna, plano de alocação das urnas do TRE), não conclusão.

## Hipótese (a verificar)

- Diferença entre modelos de urna que sobreviva ao controle por zona pode vir da alocação não aleatória das urnas dentro da zona (escolas centrais e periféricas, locais grandes e pequenos). Só o plano de alocação do TRE separa essa hipótese de um efeito do equipamento.

## O achado que contraria a tese

- Quem espera achar seções novas de 90% encontra as velhas: 128 de 164 seções casadas de Lula já estavam acima de 90% em 2022.
- Na especificação pedida, os quatro grupos não são geografia (V de Cramér entre grupo e região 0,09): separam as seções pelo padrão de zeros. 44,4% das células são zero e viram 0,0001; no log, uma candidatura sem voto fica a 3 ou 4 unidades de uma com um voto, e a mistura usa esse degrau para separar grupos (a parte que mais distingue os grupos é `n55`, com 99 pontos de diferença na proporção de zeros entre eles).
- O modelo da urna não move o voto de forma separável de zero dentro da zona: na mesma zona, a urna mais nova dá a Flávio 0,00 ponto em relação à mais velha (IC 95% de -0,70 a 0,69, contém o zero); sem o controle, -1,34; 79 zonas.

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
