# Grupos de seções nos dois turnos de 2026 (mistura gaussiana)

**Atipicidade estatística não é irregularidade; o grupo pede explicação, não prova nada.**

Gerado em 2026-10-26T22:35:53+00:00 por `scripts/apuracao-2t-2026-anomalia.py`.

## Universo

- 497.796 seções do Brasil com boletim de urna nos dois turnos e pelo menos 30 aptos em ambos.
- Fora: 1.310 do exterior (abstenção muito acima da média formaria um grupo só com elas), 20 sem boletim em um dos turnos e 81 com menos de 30 aptos em algum turno.
- Comparecimento implícito (soma dos votos de presidente) contra o do BU: diverge em 2 seções; MG 41238 zona 39 seção 168 (281 votos, comparecimento do BU 0); MG 50075 zona 47 seção 41 (278 votos, comparecimento do BU 0). A diferença não muda as features.

## O espaço

Nove frações do eleitorado do próprio turno, em pontos percentuais: Lula, Flávio, outros, brancos e nulos no 1º turno; Lula, Flávio, brancos e nulos no 2º. Abstenção e comparecimento ficam implícitos. Cada coluna é padronizada (média zero, desvio um entre seções).

A mistura gaussiana com covariância completa é invariante a transformações afins invertíveis: trocar as quatro colunas do 2º turno pelas diferenças entre turnos (Lula, Flávio, brancos e nulos do 2T menos os do 1T) muda só a parametrização. A partição no ótimo é a mesma e a log-verossimilhança só muda pelo logaritmo do determinante da troca (zero para as diferenças em pontos; constante quando cada enquadramento é padronizado). Por isso o ajuste é feito nos níveis padronizados e os centros são publicados também em diferenças. A inicialização por k-means não é invariante, e partidas diferentes podem parar em ótimos locais diferentes; por isso fica a maior log-verossimilhança entre as 16 partidas. Conferência na amostra da escolha de k, com k = 8: índice de Rand ajustado de 0,9751 entre as partições ajustadas nos dois enquadramentos (melhor de 16 partidas em cada um) e diferença de −0,000005 na log-verossimilhança média, já descontado o determinante da mudança de coordenadas.

## Número de grupos

BIC e ICL para k = 2 a 10 na amostra estratificada por UF de 120.000 seções (semente 20261026), oito sementes e duas inicializações por k, uma partida cada:

| k | BIC | ICL | log-veross. média | iterações | convergiu |
|---|---|---|---|---|---|
| 2 | 1.750.758 | 1.798.953 | -7,2895 | 21 | sim |
| 3 | 1.720.640 | 1.812.293 | -7,1613 | 76 | sim |
| 4 | 1.703.164 | 1.812.979 | -7,0858 | 131 | sim |
| 5 | 1.691.749 | 1.818.490 | -7,0356 | 138 | sim |
| 6 | 1.683.169 | 1.827.170 | -6,9972 | 404 | sim |
| 7 | 1.676.440 | 1.833.415 | -6,9665 | 872 | sim |
| 8 | 1.671.596 | 1.840.869 | -6,9436 | 139 | sim |
| 9 | 1.668.489 | 1.854.062 | -6,9280 | 237 | sim |
| 10 | 1.665.724 | 1.861.442 | -6,9138 | 395 | sim |

Quedas do BIC, em % da queda total: 2 para 3, 35,42%; 3 para 4, 20,55%; 4 para 5, 13,42%; 5 para 6, 10,09%; 6 para 7, 7,91%; 7 para 8, 5,70%; 8 para 9, 3,65%; 9 para 10, 3,25%.

Regra declarada: k* é o menor k em que a queda do BIC do passo seguinte fica abaixo de 5% da queda total de k = 2 até k = 10 (o joelho); sem joelho, k* = argmin do ICL; 3 ≤ k* ≤ 10. Aplicada: joelho do BIC: k = 8 é o menor k em que a queda do BIC até k + 1 fica abaixo de 5% da queda total de k = 2 a k = 10. Joelho do BIC: 8; menor ICL: k = 2. **k* = 8.** O ICL, que penaliza grupos sobrepostos, é mínimo em k = 2: os grupos se sobrepõem e a mistura descreve regiões de uma nuvem contínua, não aglomerados separados.

## Convergência

O EM convergiu nas 16 partidas (8 sementes, inicializações kmeans e k-means++, uma partida cada; critério do sklearn: variação da log-verossimilhança média abaixo de 0,000001, de 114 a 628 iterações). Continuado a partir do ajuste escolhido, com tolerância 0,00000001 e até 5.000 iterações a mais, o EM rodou 86 iterações e a log-verossimilhança média subiu 0,000013 por seção, mas a partição mudou (índice de Rand ajustado de 0,98 entre as duas): pelo critério declarado, o ajuste anterior parava cedo, e o publicado é o apertado. 13 de 16 partidas chegaram ao mesmo máximo, a 0,001 por seção (kmeans: 8 de 8; k-means++: 5 de 8). A partição é estável: índice de Rand ajustado médio, contra a escolhida, de 0,96 entre as partidas que chegam ao máximo, de 0,94 a 0,98; de 0,48 entre as demais. A partida escolhida (semente 20261027, inicialização k-means++) convergiu em 114 iterações com tolerância 0,000001 e teto de 2.000 (dobrado até 2 vezes se preciso); a continuação adotada parou em 86 iterações a mais, com tolerância 0,00000001.

## k-means como contraste

| k | silhueta (níveis) | silhueta (níveis e deltas) |
|---|---|---|
| 2 | 0,286 | 0,207 |
| 3 | 0,222 | 0,202 |
| 4 | 0,173 | 0,181 |
| 5 | 0,172 | 0,160 |
| 6 | 0,170 | 0,144 |
| 7 | 0,167 | 0,141 |
| 8 | 0,164 | 0,135 |
| 9 | 0,147 | 0,129 |
| 10 | 0,143 | 0,125 |

Índice de Rand ajustado entre o k-means com k = 8 e a mistura: 0,356 nos níveis e 0,209 nos níveis e deltas. O k-means não é invariante à troca de coordenadas; a mistura é o modelo principal.

## Os grupos

Ordem por Lula no 2º turno (% do eleitorado) crescente. Centros pela média das seções de cada grupo.

- Grupo 0: 76.507 seções (15,37%), aptos médio 322,5. Flávio no 2º turno: 54,0% do eleitorado, contra 37,5% no país; Lula no 2º turno: 25,8% do eleitorado, contra 40,9% no país. Em diferenças: comparecimento +2,0, Lula +5,1, Flávio +3,4, brancos −0,3, nulos −0,1 pontos do eleitorado; terceira via no 1T 6,1%. Fatia de Flávio entre os dois: 70,8% no 1T, 67,5% no 2T.
- Grupo 1: 50.584 seções (10,16%), aptos médio 328,9. Terceira via no 1º turno: 9,7% do eleitorado, contra 5,8% no país; ganho de Flávio entre turnos: +4,3 pontos, contra +2,2 no país. Em diferenças: comparecimento +1,6, Lula +6,8, Flávio +4,3, brancos −0,1, nulos +0,3 pontos do eleitorado; terceira via no 1T 9,7%. Fatia de Flávio entre os dois: 60,0% no 1T, 57,0% no 2T.
- Grupo 2: 116.647 seções (23,43%), aptos médio 327,9. Brancos e nulos no 1º turno: 5,0% do eleitorado, contra 3,8% no país; brancos e nulos no 2º turno: 3,4% do eleitorado, contra 2,6% no país. Em diferenças: comparecimento +2,3, Lula +7,4, Flávio +3,1, brancos −0,9, nulos −0,7 pontos do eleitorado; terceira via no 1T 6,6%. Fatia de Flávio entre os dois: 59,5% no 1T, 55,3% no 2T.
- Grupo 3: 12.891 seções (2,59%), aptos médio 267,4. Variação do comparecimento entre turnos: −4,7 pontos, contra +1,7 no país; ganho de Lula entre turnos: +1,1 pontos, contra +6,4 no país. Em diferenças: comparecimento −4,7, Lula +1,1, Flávio −2,2, brancos −0,1, nulos −0,0 pontos do eleitorado; terceira via no 1T 3,5%. Fatia de Flávio entre os dois: 47,3% no 1T, 44,8% no 2T.
- Grupo 4: 103.357 seções (20,77%), aptos médio 323,0. Brancos e nulos no 2º turno: 1,9% do eleitorado, contra 2,6% no país. Em diferenças: comparecimento +1,8, Lula +6,4, Flávio +1,8, brancos −0,5, nulos −0,6 pontos do eleitorado; terceira via no 1T 5,3%. Fatia de Flávio entre os dois: 49,8% no 1T, 46,8% no 2T.
- Grupo 5 **(grupo atípico)**: 10.850 seções (2,18%), aptos médio 245,3. Brancos e nulos no 1º turno: 6,5% do eleitorado, contra 3,8% no país; brancos e nulos no 2º turno: 4,4% do eleitorado, contra 2,6% no país. Em diferenças: comparecimento −0,2, Lula +6,3, Flávio +1,2, brancos −0,9, nulos −1,2 pontos do eleitorado; terceira via no 1T 5,6%. Fatia de Flávio entre os dois: 42,2% no 1T, 39,5% no 2T.
- Grupo 6: 73.831 seções (14,83%), aptos médio 317,2. Lula no 2º turno: 56,4% do eleitorado, contra 40,9% no país; Flávio no 2º turno: 25,7% do eleitorado, contra 37,5% no país. Em diferenças: comparecimento +2,5, Lula +7,7, Flávio +1,3, brancos −0,8, nulos −1,1 pontos do eleitorado; terceira via no 1T 4,6%. Fatia de Flávio entre os dois: 33,7% no 1T, 31,6% no 2T.
- Grupo 7: 53.129 seções (10,67%), aptos médio 289,0. Flávio no 2º turno: 16,6% do eleitorado, contra 37,5% no país; Lula no 2º turno: 61,9% do eleitorado, contra 40,9% no país. Em diferenças: comparecimento +0,8, Lula +5,1, Flávio +0,1, brancos −0,4, nulos −1,4 pontos do eleitorado; terceira via no 1T 2,6%. Fatia de Flávio entre os dois: 22,9% no 1T, 21,5% no 2T.

## O grupo atípico

Grupo 5: soma dos postos de menor log-verossimilhança média e de maior dispersão (log-determinante da covariância); empate pela menor log-verossimilhança média, como no 1º turno. Segundo colocado: grupo 3, 2 posto(s) atrás.

- 10.850 seções (2,18%), aptos médio 245,3 contra 317,0 no país; seções com menos de 100 aptos: 8,4% contra 0,5%.
- Regiões: Sudeste 38,7% do grupo (2,07% da região), Nordeste 37,6% do grupo (2,90% da região), Norte 11,4% do grupo (2,82% da região), Sul 9,7% do grupo (1,47% da região), Centro-Oeste 2,6% do grupo (0,74% da região).
- Modelo da urna: UE2022 43,2%, UE2020 36,7%, UE2015 17,6%, UE2013 2,5%.
- Sinais existentes, no grupo contra o país: comparecimento +5 pp 8,34% contra 9,29%; sem biometria 3,86% contra 2,65%; ano de nascimento 7,10% contra 3,88%; salto de biometria 3,71% contra 1,80%; encerramento tardio 0,88% contra 1,46%; BU de apuração 0,00% contra 0,00%; mudança de local 0,26% contra 0,23%.
- Voto: a fatia de Flávio entre os dois no 2T fica −3,56 pontos contra as vizinhas do mesmo município (IC 95% de −3,83 a −3,27; 10.850 seções do grupo, 384.980 vizinhas, 2.749 municípios). Contra o 1T, a diferença em diferenças é −0,05 pontos (IC 95% de −0,19 a +0,07). O grupo foi definido pelas próprias frações de voto: a comparação descreve o tamanho da diferença, não é teste independente.

Seções do grupo com menor densidade (as 50 estão no JSON, com o link do Politize-se):

- MG, Passa Tempo, zona 208, seção 53: 165 aptos; brancos e nulos 9 + 30 no 1T e 10 + 25 no 2T; Lula 64 e Flávio 25 no 2T. Pela régua da casa: sem explicação provável pela regra: pede conferência na ata e no log.
- AC, Manoel Urbano, zona 3, seção 160: 236 aptos; brancos e nulos 0 + 3 no 1T e 0 + 21 no 2T; Lula 48 e Flávio 104 no 2T. Pela régua da casa: a própria seção já tinha 10% ou mais sem biometria no 1T.
- ES, Cariacica, zona 54, seção 609: 51 aptos; brancos e nulos 2 + 0 no 1T e 4 + 5 no 2T; Lula 18 e Flávio 15 no 2T. Pela régua da casa: aptos mudaram mais de 10% entre os turnos; seção pequena (menos de 100 aptos): um eleitor move mais de 1 pp.
- AM, Ipixuna, zona 45, seção 52: 333 aptos; brancos e nulos 0 + 27 no 1T e 0 + 53 no 2T; Lula 138 e Flávio 5 no 2T. Pela régua da casa: zona com biometria baixa também no 1T (mediana ≥ 10%), sem salto; a própria seção já tinha 10% ou mais sem biometria no 1T.
- RS, Candelária, zona 13, seção 95: 170 aptos; brancos e nulos 27 + 6 no 1T e 14 + 2 no 2T; Lula 61 e Flávio 54 no 2T. Pela régua da casa: zona com biometria baixa também no 1T (mediana ≥ 10%), sem salto.

## O que a mistura não separa

Entre os 8 grupos, o V de Cramér com a região é 0,446; com a UF, 0,402; com o modelo da urna, 0,037; com a faixa de aptos, 0,159. Os grupos de voto seguem a geografia política do país; o modelo da urna quase não separa nada.

O grupo atípico pesa de 0,74% a 2,90% das seções de cada região, e o V de Cramér entre ele e a região é 0,044 (UF: 0,082); com a faixa de aptos, 0,214: 34,0% das seções de 30 a 99 aptos caem nele, contra 2,18% do país (15,6 vezes), e seções com menos de 200 aptos são 28,5% do grupo contra 4,4% do país; o desvio entre as seções do grupo é 1,9 vezes o do país em nulos no 2º turno e 1,9 vezes o do país em nulos no 1º turno.

Pela régua declarada, o grupo atípico não é geografia; é, em boa parte, tamanho de seção (V de Cramér com a região 0,044, com a UF 0,082, com a faixa de aptos 0,214; seções de 30 a 99 aptos 15,6 vezes mais frequentes que no país). No centro, o que o distingue é: brancos e nulos no 1º turno: 6,5% do eleitorado, contra 3,8% no país; brancos e nulos no 2º turno: 4,4% do eleitorado, contra 2,6% no país. Entre os turnos, a fatia de Flávio no grupo andou como a das vizinhas do mesmo município (diferença em diferenças de −0,05 ponto, IC de 95% com o zero dentro).

UFs em que o grupo atípico pesa mais: AP 7,27% das seções (3,3 vezes o país); AC 7,05% das seções (3,2 vezes o país); TO 6,64% das seções (3,0 vezes o país); AL 5,10% das seções (2,3 vezes o país); ES 4,52% das seções (2,1 vezes o país); PB 3,94% das seções (1,8 vezes o país). Por faixa de aptos: 30 a 99, 34,03% (15,6 vezes); 100 a 199, 11,46% (5,3 vezes); 200 a 299, 2,92% (1,3 vezes); 300 a 399, 1,09% (0,5 vezes); 400 ou mais, 0,53% (0,2 vezes).

## Limites

- Atipicidade estatística não é irregularidade: o grupo atípico pede explicação, não prova nada, e nenhuma seção individual é acusada.
- O número de grupos é escolha por regra declarada antes de ver os grupos (joelho do BIC a 5% da queda total, ICL como alternativa); outra regra daria outro k.
- O grupo depende do espaço escolhido: nove frações do eleitorado, padronizadas. Outra padronização, outras variáveis (tamanho, renda, biometria) ou outro modelo formariam outros grupos.
- O grupo foi definido pelas próprias frações de voto; comparar o voto dele com o das vizinhas descreve o tamanho da diferença, não é teste independente.
- Seções pequenas têm frações mais instáveis (um eleitor move mais de um ponto em seção com menos de 100 aptos), e a mistura lê essa instabilidade como dispersão.
- O exterior fica fora (abstenção muito acima da média formaria um grupo só com essas urnas), assim como seções sem boletim em um dos turnos ou com menos de 30 aptos.
- A densidade é a do modelo ajustado: 'entre as 1% menos prováveis' é posição relativa no país, não probabilidade de erro ou de irregularidade.
- Frações discretas (zero branco, zero nulo) deixam a verossimilhança crescer sem limite quando um componente se cola num valor exato; essas partidas degeneradas (menor autovalor da covariância abaixo de 0,0001 nas coordenadas padronizadas) ficam fora da escolha por regra declarada e são contadas.
- O ICL mínimo em k = 2 mostra grupos sobrepostos: a mistura descreve regiões de uma nuvem contínua, e uma seção perto da fronteira poderia cair no grupo vizinho.

**Atipicidade estatística não é irregularidade; o grupo pede explicação, não prova nada.**
