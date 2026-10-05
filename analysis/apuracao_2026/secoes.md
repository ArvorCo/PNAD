# Análise por seção (boletins de urna), presidente, 1º turno de 2026

Gerado em 2026-10-05T16:51:30Z por `scripts/apuracao-2026-secoes.py`. Dados em `analysis/apuracao_2026/dados/secoes.json` (contrato em `analysis/apuracao_2026/CONTRATO_SECOES.md`).

> Seção atípica é seção que pede explicação, não indício de irregularidade. O que resolve cada caso é documento: ata da mesa, log da urna e plano de alocação das urnas do TRE.

**Coleta parcial.** 70.736 seções válidas de 499.248 seções principais do país; UFs completas: AC, AL, AP, DF, ES, MS, MT, RN, RO, RR, SE, TO. Os números mudam quando a coleta terminar.

## Cobertura

- Seções no cadastro do TSE (cs): 517.179, das quais 17.931 agregadas (sem boletim próprio).
- Boletins lidos: 72.051; válidos para a análise: 70.736.
- Fora: 427.197 seções, seção principal sem boletim de urna no banco (ainda não coletada ou sem arquivo).
- Fora: 1.143 seções, soma das seções diferente do arquivo de zona do TSE.
- Fora: 158 seções, soma das seções diferente do arquivo de zona do TSE, que congelou com menos seções totalizadas do que as existentes (st < ts).
- Fora: 14 seções, zona ainda não conferida contra o arquivo de zona do TSE.
- Nas seções válidas: Flávio 49,83% e Lula 43,50% dos válidos, 16.498.678 válidos.

## A. Seções com 90% ou mais para um candidato

Quem espera achar seções novas de 90% encontra as velhas: 128 de 163 seções casadas de Lula já estavam acima de 90% em 2022.

| candidato | limiar | seções | com 100+ votantes | aptos | % das seções |
|---|---|---|---|---|---|
| Lula | 90% | 313 | 289 | 77.047 | 0,44 |
| Lula | 95% | 123 | 110 | 27.729 | 0,17 |
| Lula | 100% | 10 | 4 | 1.170 | 0,01 |
| Flávio | 90% | 31 | 28 | 8.150 | 0,04 |
| Flávio | 95% | 2 | 1 | 451 | 0,00 |
| Flávio | 100% | 0 | 0 | 0 | 0,00 |

Por tamanho (votantes da seção):

| faixa | seções | Lula ≥ 90% | % | Flávio ≥ 90% | % |
|---|---|---|---|---|---|
| 1–49 | 67 | 6 | 8,96 | 1 | 1,49 |
| 50–99 | 411 | 18 | 4,38 | 2 | 0,49 |
| 100–199 | 12.475 | 133 | 1,07 | 6 | 0,05 |
| 200–299 | 49.186 | 149 | 0,30 | 17 | 0,03 |
| 300–399 | 8.549 | 7 | 0,08 | 5 | 0,06 |
| 400+ | 48 | 0 | 0,00 | 0 | 0,00 |

- Lula: 313 seções em 90% ou mais; o resto da zona dá 54,0% a Lula (mediana) e o excesso da seção sobre a zona é 40,5 pontos (mediana); 246 seções ficam 20 pontos ou mais acima da própria zona.
- Flávio: 31 seções em 90% ou mais; o resto da zona dá 74,1% a Flávio (mediana) e o excesso da seção sobre a zona é 17,4 pontos (mediana); 10 seções ficam 20 pontos ou mais acima da própria zona.

Por tipo de local (inferência por palavra-chave; regras no JSON):

| tipo | seções | Lula ≥ 90% | % do tipo | Flávio ≥ 90% | % do tipo |
|---|---|---|---|---|---|
| escola ou universidade | 51.362 | 25 | 0,05 | 19 | 0,04 |
| outro | 11.303 | 4 | 0,04 | 2 | 0,02 |
| zona rural | 6.916 | 48 | 0,69 | 9 | 0,13 |
| aldeia ou terra indígena | 514 | 222 | 43,19 | 1 | 0,19 |
| assentamento | 415 | 6 | 1,45 | 0 | 0,00 |
| quilombo | 113 | 6 | 5,31 | 0 | 0,00 |
| unidade prisional ou socioeducativa | 58 | 2 | 3,45 | 0 | 0,00 |
| voto em trânsito | 38 | 0 | 0,00 | 0 | 0,00 |
| exterior | 17 | 0 | 0,00 | 0 | 0,00 |

Cruzamento com as 50 zonas mais atípicas de `anomalias.json`: 13 estão na base, 3 têm ao menos uma seção de 90%. Taxa de seções com Lula em 90% ou mais: 5,65% nessas zonas e 0,42% nas demais; Flávio: 0,00% e 0,04%.

Mesma seção em 2022 (mesma UF, município, zona e número de seção, e mesmo nome do local de votação nos dois cadastros (sem acento e sem espaços repetidos)): 46.159 de 70.736 seções casadas.
- Lula em 90% ou mais em 2026, casadas: 163; Lula já tinha 90% ou mais no 1º turno de 2022 em 128 e no 2º turno em 151; mediana de 2022 93,3% (1º turno); variação mediana 0,8 pontos.
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

- Na especificação pedida, os quatro grupos não são geografia (V de Cramér entre grupo e região 0,16): separam as seções pelo padrão de zeros. 44,4% das células são zero e viram 0,0001; no log, uma candidatura sem voto fica a 3 ou 4 unidades de uma com um voto, e a mistura usa esse degrau para separar grupos (a parte que mais distingue os grupos é `n55`, com 100 pontos de diferença na proporção de zeros entre eles).
- Na versão com nanicas somadas, o V de Cramér entre grupo e região é 0,15; o padrão de zeros ainda separa os grupos (`n14`, 100 pontos).
- Na versão com cinco partes, o V de Cramér entre grupo e região é 0,43.
- Grupo 0: Lula 56% dos válidos, abstenção 21%, Nordeste 61% das seções; 6.782 seções.
- Grupo 1: Flávio 49% dos válidos, abstenção 20%, Centro-Oeste 38% das seções; 4.658 seções.
- Grupo 2: Flávio 50% dos válidos, abstenção 20%, Nordeste 35% das seções; 44.210 seções.
- Grupo 3: Flávio 54% dos válidos, abstenção 20%, Centro-Oeste 42% das seções; 15.086 seções.
- O grupo de menor densidade e maior dispersão é o 1 (Flávio 49% dos válidos, abstenção 20%, Centro-Oeste 38% das seções); as 20 seções menos prováveis dele vêm com o que provavelmente as explica.

Método: log-razão centrada (CLR) das 15 frações, com zero trocado por 0,0001 antes do log; a mistura é ajustada nas 14 coordenadas ortonormais do subespaço de soma zero (ILR), rotação que preserva Mahalanobis e densidade relativa. Covariância completa, 10 inicializações, semente 20261005, ajuste sobre 70.736 seções (o país inteiro, sem amostra).

BIC (menor é melhor; com os degraus de zeros, a comparação entre k é instável e serve só de contraste):

- k = 3: BIC 440.088,7, log-verossimilhança média -3,082
- k = 4: BIC 466.708,6, log-verossimilhança média -3,261
- k = 5: BIC 421.224,5, log-verossimilhança média -2,930

| grupo | rótulo | seções | aptos médios | log-veross. média | log det Σ |
|---|---|---|---|---|---|
| 0 | Lula 56% dos válidos, abstenção 21%, Nordeste 61% das seções | 6.782 | 285 | -3,86 | -34,7 |
| 1 | Flávio 49% dos válidos, abstenção 20%, Centro-Oeste 38% das seções | 4.658 | 301 | -22,92 | 0,7 |
| 2 | Flávio 50% dos válidos, abstenção 20%, Nordeste 35% das seções | 44.210 | 304 | 0,05 | -38,8 |
| 3 | Flávio 54% dos válidos, abstenção 20%, Centro-Oeste 42% das seções | 15.086 | 318 | -6,61 | -28,6 |

Versão densa (mesma mistura (k = 4, mesma semente) sobre cinco partes quase sem zeros: Lula, Flávio, as outras dez candidaturas somadas, brancos e nulos somados, abstenção):

| grupo | rótulo | seções | aptos médios | log-veross. média | log det Σ |
|---|---|---|---|---|---|
| 0 | Lula 64% dos válidos, abstenção 19%, Nordeste 85% das seções | 20.450 | 302 | -2,57 | -8,2 |
| 1 | Lula 60% dos válidos, abstenção 19%, Norte 39% das seções | 1.252 | 233 | -10,69 | 2,1 |
| 2 | Flávio 54% dos válidos, abstenção 20%, Centro-Oeste 40% das seções | 31.236 | 316 | -1,06 | -10,1 |
| 3 | Flávio 65% dos válidos, abstenção 23%, Centro-Oeste 50% das seções | 17.798 | 293 | -2,95 | -7,4 |

Grupo mais anômalo na versão pedida: 1. Critério: soma dos postos de menor log-verossimilhança média e de maior dispersão (log-determinante da covariância); empate decidido pela menor log-verossimilhança média. Amostras: as 20 seções de menor log-verossimilhança dentro do componente.

- UIRAMUTÃ (RR), zona 7, seção 124, ESCOLA ESTADUAL INDÍGENA TUXAUA CRETÁCIO: Lula 51, Flávio 0 de 51 válidos (52 aptos, 52 votantes, UE2022). Aldeia ou terra indígena (inferido pelo cadastro do local); seção pequena (52 votantes).
- MAZAGÃO (AP), zona 5, seção 33, ESCOLA MUNICIPAL BARRO ALTO: Lula 43, Flávio 0 de 47 válidos (67 aptos, 49 votantes, UE2020). Zona rural (inferido pelo cadastro do local); seção minúscula (49 votantes).
- PEIXOTO DE AZEVEDO (MT), zona 33, seção 255, ESCOLA ESTADUAL INDIGENA METUKTIRE: Lula 156, Flávio 0 de 159 válidos (231 aptos, 159 votantes, UE2020). Aldeia ou terra indígena (inferido pelo cadastro do local).
- ARACRUZ (ES), zona 20, seção 232, ASSOCIAÇÃO DA ALDEIA INDÍGENA NOVA ESPERANÇA (ALDEIA NOVA ESPERANÇA): Lula 33, Flávio 0 de 33 válidos (56 aptos, 33 votantes, UE2020). Aldeia ou terra indígena (inferido pelo cadastro do local); seção minúscula (33 votantes).
- FORMOSO DO ARAGUAIA (TO), zona 15, seção 72, ALDEIA SÃO JOÃO: Lula 126, Flávio 0 de 127 válidos (159 aptos, 132 votantes, UE2020). Aldeia ou terra indígena (inferido pelo cadastro do local).
- CRUZEIRO DO SUL (AC), zona 4, seção 457, ESCOLA TAMÃKÃYÃ: Lula 151, Flávio 0 de 151 válidos (208 aptos, 155 votantes, UE2022). Aldeia ou terra indígena (inferido pelo cadastro do local).
- TOCANTINÓPOLIS (TO), zona 9, seção 184, ESCOLA ESTADUAL INDÍGENA KUNITIK: Lula 59, Flávio 0 de 60 válidos (62 aptos, 60 votantes, UE2022). Aldeia ou terra indígena (inferido pelo cadastro do local); seção pequena (60 votantes).
- CARIACICA (ES), zona 54, seção 674, CPFC - CENTRO PRISIONAL FEMININO DE CARIACICA: Lula 29, Flávio 6 de 39 válidos (56 aptos, 41 votantes, UE2015). Unidade prisional ou socioeducativa (inferido pelo cadastro do local); seção minúscula (41 votantes); 56 de 56 aptos em trânsito.
- UIRAMUTÃ (RR), zona 7, seção 61, IGREJA INDIGENA CORAÇÃO DO MUNDO: Lula 185, Flávio 0 de 185 válidos (212 aptos, 185 votantes, UE2022). Aldeia ou terra indígena (inferido pelo cadastro do local).
- CONFRESA (MT), zona 28, seção 200, ESCOLA ESTADUAL TAPI'ITAWA: Lula 296, Flávio 0 de 297 válidos (315 aptos, 297 votantes, UE2022). Aldeia ou terra indígena (inferido pelo cadastro do local).
- PORTO VELHO (RO), zona 6, seção 516, KYOWÃ - ESCOLA ESTADUAL - ALDEIA KARITIANA: Lula 100, Flávio 0 de 102 válidos (115 aptos, 104 votantes, UE2020). Aldeia ou terra indígena (inferido pelo cadastro do local).
- MAZAGÃO (AP), zona 5, seção 75, ESCOLA MUNICIPAL SOROROCA: Lula 81, Flávio 0 de 81 válidos (90 aptos, 81 votantes, UE2020). Seção pequena (81 votantes).
- ARAL MOREIRA (MS), zona 19, seção 313, ESCOLA POLO - CHERU APYKA RENDY: Lula 52, Flávio 0 de 52 válidos (63 aptos, 53 votantes, UE2020). Aldeia ou terra indígena (inferido pelo cadastro do local); seção pequena (53 votantes).
- GOIATINS (TO), zona 32, seção 60, ESCOLA INDIGENA TXUARET: Lula 106, Flávio 0 de 107 válidos (130 aptos, 112 votantes, UE2022). Aldeia ou terra indígena (inferido pelo cadastro do local).
- AQUIDAUANA (MS), zona 10, seção 130, E. M. VISCONDE DE TAUNAY: Lula 11, Flávio 8 de 20 válidos (227 aptos, 21 votantes, UE2015). Seção minúscula (21 votantes).
- UIRAMUTÃ (RR), zona 7, seção 102, IGREJA INDIGENA CORAÇÃO DO MUNDO: Lula 192, Flávio 0 de 192 válidos (206 aptos, 192 votantes, UE2022). Aldeia ou terra indígena (inferido pelo cadastro do local).
- PORTO ALEGRE DO NORTE (MT), zona 28, seção 191, ESCOLA ESTADUAL TAPI ' ITAWA - ANEXO I: Lula 61, Flávio 0 de 61 válidos (65 aptos, 61 votantes, UE2022). Aldeia ou terra indígena (inferido pelo cadastro do local); seção pequena (61 votantes).
- TOCANTINÓPOLIS (TO), zona 9, seção 192, ESCOLA INDÍGENA MANTY'Q SÃO JOSÉ: Lula 159, Flávio 0 de 159 válidos (175 aptos, 165 votantes, UE2022). Aldeia ou terra indígena (inferido pelo cadastro do local).
- PARANÃ (TO), zona 18, seção 87, ESCOLA MUNICIPAL ALBINO: Lula 37, Flávio 0 de 37 válidos (43 aptos, 39 votantes, UE2020). Quilombo (inferido pelo cadastro do local); seção minúscula (39 votantes).
- JI-PARANÁ (RO), zona 3, seção 999, CASA DE DETENÇÃO DE JI-PARANÁ - SEJUS-CDJP: Lula 19, Flávio 17 de 38 válidos (42 aptos, 38 votantes, UE2022). Unidade prisional ou socioeducativa (inferido pelo cadastro do local); seção minúscula (38 votantes); 42 de 42 aptos em trânsito.

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

Estabilidade (índice de Rand ajustado contra a versão pedida): outra semente 0,402; nanicas somadas 0,185; versão densa 0,030.

## C. Modelo de urna

- Dentro da mesma zona, o modelo da urna não move o voto de forma separável de zero: a urna mais nova da zona dá a Flávio -0,38 ponto em relação à mais velha (IC 95% de -0,95 a 0,20), contra -1,86 na comparação bruta, em 74 zonas.
- No mesmo prédio, Flávio: 0,14 ponto no modelo mais nova contra o mais velha dentro da mesma unidade (IC 95% de -0,01 a 0,29, contém o zero); sem o controle, -1,84, em 2.252 locais.

Bruto (soma dos votos por modelo, sem controle):

| modelo | seções | Flávio % | Lula % | abstenção % | brancos % | nulos % |
|---|---|---|---|---|---|---|
| UE2013 | 1.270 | 45,12 | 47,58 | 21,88 | 1,66 | 3,03 |
| UE2015 | 9.411 | 47,68 | 44,77 | 20,85 | 1,57 | 2,68 |
| UE2020 | 30.761 | 50,38 | 42,95 | 20,00 | 1,40 | 2,57 |
| UE2022 | 29.289 | 50,21 | 43,45 | 20,15 | 1,39 | 2,70 |
| sem modelo | 5 | 26,09 | 60,87 | 52,58 | 0,00 | 0,00 |

Dentro da zona (Diferença (modelo b menos modelo a) dentro do par município e zona com ao menos 20 seções de cada modelo, média ponderada pelos votantes das seções comparadas; IC por bootstrap de zonas.):

| a → b | unidades | seções a/b | Flávio pp | Lula pp | nulos pp | bruto Flávio |
|---|---|---|---|---|---|---|
| UE2013 → UE2015 | 8 | 582/1.216 | -1,78 (IC 95% de -3,03 a -0,28) | 1,71 (IC 95% de 0,18 a 3,00) | 0,08 (IC 95% de -0,13 a 0,35) | 2,48 |
| UE2013 → UE2022 | 4 | 87/377 | -4,70 (IC 95% de -6,89 a -2,65) | 5,00 (IC 95% de 2,76 a 7,26) | 0,12 (IC 95% de -0,27 a 0,50) | -4,76 |
| UE2015 → UE2022 | 6 | 1.304/495 | -0,47 (IC 95% de -2,97 a 2,50) | 0,77 (IC 95% de -2,19 a 3,20) | 0,10 (IC 95% de -0,05 a 0,23) | -0,75 |
| UE2020 → UE2022 | 64 | 5.091/5.053 | -0,34 (IC 95% de -0,89 a 0,13) | 0,33 (IC 95% de -0,12 a 0,83) | -0,06 (IC 95% de -0,14 a 0,02) | -1,01 |
| mais velha → mais nova | 74 | 6.103/5.890 | -0,38 (IC 95% de -0,95 a 0,20) | 0,39 (IC 95% de -0,18 a 0,96) | -0,03 (IC 95% de -0,11 a 0,05) | -1,86 |

Dentro do mesmo local (Diferença (modelo b menos modelo a) dentro do mesmo local de votação (mesmo prédio), com ao menos uma seção de cada modelo; IC por bootstrap de locais.):

| a → b | unidades | seções a/b | Flávio pp | Lula pp | nulos pp | bruto Flávio |
|---|---|---|---|---|---|---|
| UE2013 → UE2015 | 217 | 557/1.279 | 0,23 (IC 95% de -0,30 a 0,77) | -0,27 (IC 95% de -0,81 a 0,28) | 0,06 (IC 95% de -0,13 a 0,25) | -2,71 |
| UE2013 → UE2022 | 2 | 10/9 | 2,97 (IC 95% de 1,29 a 3,79) | -1,55 (IC 95% de -2,55 a 0,50) | -0,93 (IC 95% de -1,38 a 0,00) | 0,92 |
| UE2015 → UE2022 | 1 | 2/14 | 1,72 (IC 95% de 1,72 a 1,72) | -2,24 (IC 95% de -2,24 a -2,24) | 0,01 (IC 95% de 0,01 a 0,01) | 1,72 |
| UE2020 → UE2022 | 2.032 | 6.573/6.781 | 0,12 (IC 95% de -0,03 a 0,28) | -0,13 (IC 95% de -0,29 a 0,02) | -0,08 (IC 95% de -0,13 a -0,02) | -1,09 |
| mais velha → mais nova | 2.252 | 7.142/8.083 | 0,14 (IC 95% de -0,01 a 0,29) | -0,15 (IC 95% de -0,30 a -0,00) | -0,06 (IC 95% de -0,11 a -0,01) | -1,84 |

Variação contra a mesma seção em 2022 (Diferença entre modelos, dentro do par município e zona, da variação de cada seção contra ela mesma em 2022 (Flávio 2026 menos Bolsonaro 1º turno 2022; Lula 2026 menos Lula 2022, em % dos válidos). A linha de base de 2022 da mesma seção tira o perfil político do lugar; só seções casadas pelo número e pelo nome do local.):

- UE2013 → UE2015: 3 zonas; Flávio menos Bolsonaro 0,07 (IC 95% de -0,51 a 0,53); Lula -0,52 (IC 95% de -1,65 a 0,70)
- UE2013 → UE2022: 1 zonas; Flávio menos Bolsonaro -0,58 (IC 95% de -0,58 a -0,58); Lula 0,43 (IC 95% de 0,43 a 0,43)
- UE2015 → UE2022: 6 zonas; Flávio menos Bolsonaro 0,60 (IC 95% de -0,05 a 1,21); Lula -0,66 (IC 95% de -1,29 a -0,05)
- UE2020 → UE2022: 34 zonas; Flávio menos Bolsonaro 0,10 (IC 95% de -0,08 a 0,32); Lula -0,21 (IC 95% de -0,48 a 0,01)
- mais velha → mais nova: 42 zonas; Flávio menos Bolsonaro 0,22 (IC 95% de 0,01 a 0,44); Lula -0,35 (IC 95% de -0,62 a -0,10)

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
- Zero voto em Lula com 200 votantes ou mais: 0 de 57.783 seções.
- Zero voto em Flávio com 200 votantes ou mais: 1 de 57.783 seções.
  - CONFRESA (MT), zona 28, seção 200, ESCOLA ESTADUAL TAPI'ITAWA: Lula 296, Flávio 0 de 297 válidos (315 aptos, 297 votantes, UE2022). Aldeia ou terra indígena (inferido pelo cadastro do local).
- Tipo de arquivo 1 (votação na urna (normal)): 70.715 seções; Flávio 49,83%, diferença média para o resto da zona 0,00 ponto.
- Tipo de arquivo 2 (votação recuperada (RED)): 16 seções; Flávio 46,43%, diferença média para o resto da zona 0,01 ponto.
- Tipo de arquivo 5 (sistema de apuração (5)): 5 seções; Flávio 26,09%, diferença média para o resto da zona n/d ponto.
- Urna de seção: 70.371 seções; diferença média de Flávio para o resto da zona 0,00 ponto.
- Urna de contingência: 5 seções; diferença média de Flávio para o resto da zona n/d ponto.
- Urna de reserva (seção): 360 seções; diferença média de Flávio para o resto da zona 0,07 ponto.
- Horários (Brasília): abertura depois das 9h em 30 seções, depois das 10h em 1; encerramento depois das 18h em 6.261, depois das 19h em 1.139, depois das 20h em 122.
- Boletins recebidos pelo TSE depois de meia-noite de 05/10: 0 seções, 0 válidos, Lula n/d%; diferença média de Lula para o resto da zona n/d ponto.
- Boletins recebidos pelo TSE depois de 1h de 05/10: 0 seções, 0 válidos, Lula n/d%; diferença média de Lula para o resto da zona n/d ponto.
- Benford do segundo dígito, Brasil, Lula: n = 70.700, qui-quadrado 536,4 com 9 graus de liberdade. Testes de dígito (último dígito e Benford do segundo dígito) são curiosidade metodológica: contagens de votos não seguem Benford por construção, e o teste rejeita ou aceita por motivos que nada têm a ver com fraude (Deckert, Myagkov e Ordeshook, 2011, Political Analysis 19(3)).

## Verificado (dado do TSE, conta direta)

- Base: 70.736 boletins de urna de seção, todos em zonas cuja soma das seções confere com o arquivo de zona do TSE (coleta parcial).
- Seções com Lula em 90% ou mais dos válidos: 313 (0,44% das seções), 77.047 eleitores aptos; com Flávio: 31 (0,04%), 8.150 aptos.
- Comparecimento acima de 100% dos aptos: 0 seções; igual a 100%: 1.
- Seções com 200 votantes ou mais e nenhum voto em Lula: 0; nenhum voto em Flávio: 1.
- Das 163 seções com Lula em 90% ou mais que existem com o mesmo número e o mesmo local em 2022, 128 já davam 90% ou mais a ele no 1º turno de 2022 e 160 davam 80% ou mais; mediana de 2022: 93,3%.

## Inferido (leitura dos números)

- As seções de 90% de Lula estão em zonas que já votam muito nele: mediana de 54,0% no resto da zona; o excesso típico sobre a zona é de 40,5 pontos.
- Locais com nome de aldeia ou escola indígena: 514 seções, 222 delas com Lula em 90% ou mais (43,2% do tipo, contra 0,44% no total).
- Na especificação pedida, os quatro grupos não são geografia (V de Cramér entre grupo e região 0,16): separam as seções pelo padrão de zeros. 44,4% das células são zero e viram 0,0001; no log, uma candidatura sem voto fica a 3 ou 4 unidades de uma com um voto, e a mistura usa esse degrau para separar grupos (a parte que mais distingue os grupos é `n55`, com 100 pontos de diferença na proporção de zeros entre eles).
- Na versão com nanicas somadas, o V de Cramér entre grupo e região é 0,15; o padrão de zeros ainda separa os grupos (`n14`, 100 pontos).
- Na versão com cinco partes, o V de Cramér entre grupo e região é 0,43.
- Dentro da mesma zona, o modelo da urna não move o voto de forma separável de zero: a urna mais nova da zona dá a Flávio -0,38 ponto em relação à mais velha (IC 95% de -0,95 a 0,20), contra -1,86 na comparação bruta, em 74 zonas.
- No mesmo prédio, Flávio: 0,14 ponto no modelo mais nova contra o mais velha dentro da mesma unidade (IC 95% de -0,01 a 0,29, contém o zero); sem o controle, -1,84, em 2.252 locais.

## Juízo editorial

- Seção com 90% para um candidato é, na esmagadora maioria, lugar que sempre votou assim: aldeia, zona rural do Nordeste, comunidade pequena. O número chama atenção na manchete e some quando se olha a zona e 2022.
- Nenhum dos testes por seção aponta irregularidade. O que fica atípico exige explicação documental (ata da mesa, log da urna, plano de alocação das urnas do TRE), não conclusão.

## Hipótese (a verificar)

- Diferença entre modelos de urna que sobreviva ao controle por zona pode vir da alocação não aleatória das urnas dentro da zona (escolas centrais e periféricas, locais grandes e pequenos). Só o plano de alocação do TRE separa essa hipótese de um efeito do equipamento.

## O achado que contraria a tese

- Quem espera achar seções novas de 90% encontra as velhas: 128 de 163 seções casadas de Lula já estavam acima de 90% em 2022.
- Na especificação pedida, os quatro grupos não são geografia (V de Cramér entre grupo e região 0,16): separam as seções pelo padrão de zeros. 44,4% das células são zero e viram 0,0001; no log, uma candidatura sem voto fica a 3 ou 4 unidades de uma com um voto, e a mistura usa esse degrau para separar grupos (a parte que mais distingue os grupos é `n55`, com 100 pontos de diferença na proporção de zeros entre eles).
- Dentro da mesma zona, o modelo da urna não move o voto de forma separável de zero: a urna mais nova da zona dá a Flávio -0,38 ponto em relação à mais velha (IC 95% de -0,95 a 0,20), contra -1,86 na comparação bruta, em 74 zonas.

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
