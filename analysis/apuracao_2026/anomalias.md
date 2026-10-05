# Anomalias por zona eleitoral, presidente, 1º turno de 2026

Gerado em 2026-10-05T07:01:10+00:00 por `scripts/apuracao-2026-anomalias.py`. Dados em `analysis/apuracao_2026/dados/anomalias.json`.

> Escore alto quer dizer zona atípica dentro da própria UF e pede explicação. Não é indício de fraude.

## O que é

Camada de triagem sobre os 6.106 pares município-zona do Brasil no voto para presidente. Cada zona é comparada com a própria UF e com o próprio resultado de 2022. O escore de 0 a 100 diz quão atípica a zona é no país; a coluna de explicação diz por que ela provavelmente é atípica. A lista serve para escolher onde pedir boletim de urna, ata e log, não para concluir nada.

## Método

- Dados de 2026: arquivos de zona do TSE guardados pelo coletor (`apuracao/data/apuracao.sqlite`, só leitura), versão vigente de cada arquivo: a de maior hora de geração do TSE, com totais e votos por candidato (lidos do JSON original quando o coletor não os normalizou).
- Base de 2022: votos por candidato por zona (`data/raw/tse_resultados/votacao_candidato_munzona_2022.zip`) e aptos, comparecimento, brancos e nulos por seção (`data/raw/tse_resultados/detalhe_votacao_secao_2022.zip`). Referência por zona em 685 casos, pelo município inteiro (mesmo território) em 5.380, recomposta pelos locais de votação em 39 zonas redesenhadas, sem base em 2.
- Atributos: variação de Flávio contra Bolsonaro (1º e 2º turnos de 2022), variação de Lula, resíduo hierárquico da margem, variação do comparecimento, brancos e nulos (nível e variação), terceira via, variação do eleitorado, hora de conclusão da zona e versões do arquivo. Hora e versões contam só do lado tardio.
- z robusto: mediana e MAD (x1,4826) dentro da UF; escala da UF encolhida para a nacional com peso n/(n+20); desvio médio absoluto se o MAD for zero; atributo constante dá z = 0. Ajuste de tamanho: z eleitoral dividido por exp(b x (log eleitorado - mediana)), b estimado nas faixas de tamanho, limitado a [0,5; 3].
- Resíduo hierárquico: margem Flávio menos Lula 2026 menos margem Bolsonaro menos Lula 1º turno 2022; expectativa = variação da UF + efeito local (outras zonas do município, deixa-uma-fora, ou 5 zonas vizinhas de outros municípios), encolhido por n/(n+2).
- Leituras: z robusto (raiz da média dos quadrados); Mahalanobis robusta (numpy); Isolation Forest (scikit-learn); Local Outlier Factor (scikit-learn). Combinação: média dos percentis das leituras, de 0 a 100.
- Fuso: o TSE grava a hora de totalização (ht) na hora local; o banco a converte como se fosse Brasília. A correção usa a menor diferença entre gerado_em e totalizado_em de cada zona, arredondada em horas. Correções aplicadas: AC +2h (23 zonas), AM +1h (63 zonas), AM +2h (11 zonas), MS +1h (88 zonas), MT +1h (147 zonas), PE -1h (1 zona), RO +1h (56 zonas), RR +1h (16 zonas).
- Localização: média das coordenadas dos locais de votação da zona, ponderada pelo eleitorado e restrita ao retângulo do município; sem coordenada válida, centroide do município na malha do IBGE.

## Verificado (dado do TSE, conta direta)

- Leitura conferida contra `analysis/apuracao_2026/dados/zonas.json` (código independente, mesmo banco): 0 diferenças em 6.106 zonas nos campos flavio, lula, validos, secoes, secoes_total, comparecimento, snapshot_id.

- Na última versão guardada pelo coletor, 12 arquivos de zona estão abaixo de 100% (69 seções), enquanto os arquivos de UF fecharam todas as seções. Diferença por UF (seções da UF menos soma das zonas): BA +20, MG +30, SP +19.
- A hora de totalização (campo `ht`) dos arquivos de zona vem na hora local: a diferença entre a geração do arquivo e a totalização é de um minuto nas zonas de Brasília e de uma ou duas horas a mais nas de outro fuso. Sem correção, essas zonas pareceriam terminar antes do real. Correções: AC +2h (23 zonas), AM +1h (63 zonas), AM +2h (11 zonas), MS +1h (88 zonas), MT +1h (147 zonas), PE -1h (1 zona), RO +1h (56 zonas), RR +1h (16 zonas).
- O coletor marcou como regressivas 87 versões de arquivo de zona, porque o contador `idg` do TSE caiu. Nenhuma era cópia antiga: as 87 eram versões novas, geradas depois da anterior, com `idg` menor (86 zonas). Por isso a versão usada aqui é a de maior hora de geração, não a última sem a marca.

## As 25 zonas mais atípicas

Explicação provável é inferência por regra declarada, não verificação.

| # | Escore | Zona | IBGE | Eleitorado / seções | Flávio × Lula 2026 (Bolsonaro × Lula 1º t. 2022) | O que puxa o escore | Explicação provável |
|---|---|---|---|---|---|---|---|
| 1 | 99,9 | Queimada Nova (PI), zona 38 | 2208650 | 7.227 / 28 | 20,7 × 73,4 (10,8 × 85,1) | brancos e nulos 2026 menos 2022: +5,4 pp (mediana da UF +0,8; z +7,3); brancos e nulos em 2026: 10,1% (mediana da UF 4,1%; z +6,5); Lula 2026 menos Lula 2º turno 2022: -14,0 pp (mediana da UF -6,2; z -3,8) | efeito político local não medido (liderança, prefeitura, candidatura estadual): hipótese a verificar |
| 2 | 99,9 | Guarani de Goiás (GO), zona 47 | 5209408 | 4.796 / 17 | 26,6 × 40,2 (28,1 × 64,7) | terceira via em 2026: 33,2% (mediana da UF 14,5%; z +6,1); Lula 2026 menos Lula 2º turno 2022: -27,8 pp (mediana da UF -12,2; z -5,6); Lula 2026 menos Lula 1º turno 2022: -24,5 pp (mediana da UF -11,0; z -4,6) | zona pequena (17 seções), variância alta; voto concentrado em terceira via (Caiado 32,3%); padrão regional: 2 das 5 zonas mais próximas também estão entre as 5% mais atípicas, o que aponta para efeito político da região, não para uma urna isolada; contexto: ctx-075 |
| 3 | 99,9 | São Julião (PI), zona 40 | 2210300 | 5.605 / 23 | 20,8 × 75,5 (27,5 × 67,7) | variação da margem Flávio menos Lula além da UF e do município: -23,5 pp (mediana da UF +0,5; z -7,6); Flávio 2026 menos Bolsonaro 2º turno 2022: -9,2 pp (mediana da UF +2,4; z -6,5); Flávio 2026 menos Bolsonaro 1º turno 2022: -6,7 pp (mediana da UF +4,7; z -5,9) | efeito político local não medido (liderança, prefeitura, candidatura estadual): hipótese a verificar |
| 4 | 99,8 | Pedro Laurentino (PI), zona 69 | 2207934 | 3.276 / 13 | 23,9 × 73,0 (28,0 × 68,2) | variação da margem Flávio menos Lula além da UF e do município: -16,0 pp (mediana da UF +0,5; z -5,0); Flávio 2026 menos Bolsonaro 2º turno 2022: -5,8 pp (mediana da UF +2,4; z -5,0); Flávio 2026 menos Bolsonaro 1º turno 2022: -4,1 pp (mediana da UF +4,7; z -4,7) | zona pequena (13 seções), variância alta; eleitorado cresceu 21% desde 2022, bem acima da UF: transferência de títulos muda a composição da zona |
| 5 | 99,6 | Tibau (RN), zona 49 | 2411056 | 9.238 / 26 | 37,5 × 57,5 (28,7 × 66,7) | eleitorado de 2026 contra o de 2022: +39,9% (mediana da UF +5,0%; z +8,2); variação da margem Flávio menos Lula além da UF e do município: +9,9 pp (mediana da UF +0,4; z +3,1); Lula 2026 menos Lula 1º turno 2022: -9,2 pp (mediana da UF -4,1; z -3,0) | eleitorado cresceu 40% desde 2022, bem acima da UF: transferência de títulos muda a composição da zona |
| 6 | 99,6 | Colina (SP), zona 178 | 3512001 | 14.048 / 39 | 48,7 × 31,4 (46,8 × 44,6) | Lula 2026 menos Lula 2º turno 2022: -15,0 pp (mediana da UF -6,8; z -5,0); terceira via em 2026: 19,8% (mediana da UF 7,4%; z +4,8); Lula 2026 menos Lula 1º turno 2022: -13,2 pp (mediana da UF -4,4; z -3,6) | voto concentrado em terceira via (Augusto Cury 17,3%); contexto: ctx-068, ctx-069 |
| 7 | 99,6 | Varjota (CE), zona 65 | 2313955 | 15.992 / 59 | 34,3 × 59,8 (20,9 × 59,5) | Flávio 2026 menos Bolsonaro 1º turno 2022: +13,3 pp (mediana da UF +6,3; z +3,7); comparecimento 2026 menos 2022: +7,4 pp (mediana da UF +1,1; z +3,2); conclusão em 04/10 22:47 (Brasília), 107 min depois da mediana da UF (z +2,6) | totalização tardia que já se repetia em 2022: área remota; padrão regional: 2 das 5 zonas mais próximas também estão entre as 5% mais atípicas, o que aponta para efeito político da região, não para uma urna isolada |
| 8 | 99,5 | Itapirapuã Paulista (SP), zona 10 | 3522653 | 3.305 / 10 | 54,7 × 41,2 (37,4 × 57,4) | Flávio 2026 menos Bolsonaro 1º turno 2022: +17,3 pp (mediana da UF +5,1; z +6,1); Lula 2026 menos Lula 1º turno 2022: -16,2 pp (mediana da UF -4,4; z -5,2); variação da margem Flávio menos Lula além da UF e do município: +21,2 pp (mediana da UF +1,6; z +5,1) | zona pequena (10 seções), variância alta |
| 9 | 99,5 | Sandovalina (SP), zona 261 | 3545506 | 4.876 / 14 | 36,2 × 59,4 (33,8 × 61,1) | eleitorado de 2026 contra o de 2022: +39,5% (mediana da UF -2,3%; z +7,2) | zona pequena (14 seções), variância alta; eleitorado cresceu 40% desde 2022, bem acima da UF: transferência de títulos muda a composição da zona |
| 10 | 99,5 | São Francisco de Assis do Piauí (PI), zona 90 | 2209658 | 4.780 / 21 | 24,9 × 65,3 (17,0 × 74,8) | terceira via em 2026: 9,9% (mediana da UF 3,9%; z +6,1); brancos e nulos em 2026: 7,8% (mediana da UF 4,1%; z +4,0); brancos e nulos 2026 menos 2022: +2,9 pp (mediana da UF +0,8; z +3,1) | zona pequena (21 seções), variância alta; voto concentrado em terceira via (Augusto Cury 8,1%) |
| 11 | 99,4 | Sobral (CE), zona 24 | 2312908 | 88.248 / 289 | 34,0 × 59,4 (24,7 × 55,4) | brancos e nulos 2026 menos 2022: +3,3 pp (mediana da UF +1,5; z +5,0); brancos e nulos em 2026: 8,2% (mediana da UF 4,8%; z +4,2); Lula 2026 menos Lula 1º turno 2022: +3,9 pp (mediana da UF -3,8; z +3,5) | padrão regional: 3 das 5 zonas mais próximas também estão entre as 5% mais atípicas, o que aponta para efeito político da região, não para uma urna isolada; contexto: ctx-034, ctx-070, ctx-072 |
| 12 | 99,4 | São João do Triunfo (PR), zona 52 | 4125100 | 11.623 / 46 | 51,6 × 37,8 (33,8 × 58,6) | variação da margem Flávio menos Lula além da UF e do município: +23,0 pp (mediana da UF +1,3; z +5,9); Lula 2026 menos Lula 2º turno 2022: -21,6 pp (mediana da UF -7,4; z -5,6); Lula 2026 menos Lula 1º turno 2022: -20,8 pp (mediana da UF -6,8; z -5,0) | efeito político local não medido (liderança, prefeitura, candidatura estadual): hipótese a verificar |
| 13 | 99,4 | Mato Grosso (PB), zona 36 | 2509370 | 3.319 / 10 | 19,2 × 77,8 (7,9 × 88,7) | Lula 2026 menos Lula 1º turno 2022: -10,9 pp (mediana da UF -3,6; z -4,4); Flávio 2026 menos Bolsonaro 2º turno 2022: +9,7 pp (mediana da UF +2,0; z +4,3); Flávio 2026 menos Bolsonaro 1º turno 2022: +11,3 pp (mediana da UF +4,3; z +4,3) | zona pequena (10 seções), variância alta |
| 14 | 99,3 | Tenente Ananias (RN), zona 41 | 2414100 | 8.205 / 27 | 32,1 × 65,0 (20,7 × 75,9) | variação da margem Flávio menos Lula além da UF e do município: +13,5 pp (mediana da UF +0,4; z +4,3); Flávio 2026 menos Bolsonaro 2º turno 2022: +9,6 pp (mediana da UF +1,7; z +4,1); Flávio 2026 menos Bolsonaro 1º turno 2022: +11,4 pp (mediana da UF +4,7; z +4,1) | efeito político local não medido (liderança, prefeitura, candidatura estadual): hipótese a verificar |
| 15 | 99,2 | Quissamã (RJ), zona 255 | 3304151 | 19.085 / 62 | 52,1 × 41,6 (43,4 × 50,5) | variação da margem Flávio menos Lula além da UF e do município: +14,6 pp (mediana da UF +0,8; z +6,8); Lula 2026 menos Lula 2º turno 2022: -10,5 pp (mediana da UF -4,0; z -3,8); Flávio 2026 menos Bolsonaro 1º turno 2022: +8,7 pp (mediana da UF +2,1; z +3,6) | efeito político local não medido (liderança, prefeitura, candidatura estadual): hipótese a verificar |
| 16 | 99,2 | Serra Negra do Norte (RN), zona 26 | 2413409 | 6.262 / 22 | 40,8 × 55,2 (27,3 × 68,3) | variação da margem Flávio menos Lula além da UF e do município: +18,1 pp (mediana da UF +0,4; z +5,6); Lula 2026 menos Lula 1º turno 2022: -13,1 pp (mediana da UF -4,1; z -5,5); Flávio 2026 menos Bolsonaro 1º turno 2022: +13,5 pp (mediana da UF +4,7; z +5,4) | efeito político local não medido (liderança, prefeitura, candidatura estadual): hipótese a verificar; contexto: ctx-074 |
| 17 | 99,2 | Graça (CE), zona 79 | 2304657 | 12.854 / 47 | 19,2 × 75,8 (9,8 × 84,1) | comparecimento 2026 menos 2022: +10,6 pp (mediana da UF +1,1; z +4,8); conclusão em 04/10 22:53 (Brasília), 114 min depois da mediana da UF (z +2,7); Lula 2026 menos Lula 2º turno 2022: -12,7 pp (mediana da UF -7,4; z -2,7) | totalização tardia que não se repetia em 2022: pedir a hora de transmissão de cada seção |
| 18 | 99,2 | Jutaí (AM), zona 41 | 1302306 | 15.903 / 43 | 39,2 × 57,2 (22,6 × 70,0) | variação da margem Flávio menos Lula além da UF e do município: +22,6 pp (mediana da UF +0,7; z +6,5); Lula 2026 menos Lula 2º turno 2022: -18,4 pp (mediana da UF -5,2; z -4,2); Flávio 2026 menos Bolsonaro 2º turno 2022: +14,8 pp (mediana da UF +1,2; z +3,5) | efeito político local não medido (liderança, prefeitura, candidatura estadual): hipótese a verificar; contexto: ctx-052 |
| 19 | 99,2 | Macieira (SC), zona 6 | 4210050 | 2.360 / 7 | 59,2 × 34,6 (46,3 × 48,2) | eleitorado de 2026 contra o de 2022: +33,3% (mediana da UF +2,5%; z +6,1); variação da margem Flávio menos Lula além da UF e do município: +16,0 pp (mediana da UF +1,6; z +3,3) | zona pequena (7 seções), variância alta; eleitorado cresceu 33% desde 2022, bem acima da UF: transferência de títulos muda a composição da zona |
| 20 | 99,1 | Itaju do Colônia (BA), zona 137 | 2915403 | 6.225 / 20 | 34,4 × 63,0 (37,9 × 57,8) | Lula 2026 menos Lula 2º turno 2022: +4,2 pp (mediana da UF -6,3; z +4,7); variação da margem Flávio menos Lula além da UF e do município: -15,7 pp (mediana da UF +0,4; z -4,3); Lula 2026 menos Lula 1º turno 2022: +5,3 pp (mediana da UF -4,2; z +4,1) | efeito político local não medido (liderança, prefeitura, candidatura estadual): hipótese a verificar |
| 21 | 99,1 | Mucambo (CE), zona 79 | 2309003 | 12.736 / 45 | 24,5 × 69,8 (16,1 × 74,6) | comparecimento 2026 menos 2022: +8,6 pp (mediana da UF +1,1; z +3,8); brancos e nulos em 2026: 7,1% (mediana da UF 4,8%; z +2,8); brancos e nulos 2026 menos 2022: +2,7 pp (mediana da UF +1,5; z +2,5) | efeito político local não medido (liderança, prefeitura, candidatura estadual): hipótese a verificar |
| 22 | 99,1 | Jussari (BA), zona 28 | 2918555 | 4.647 / 16 | 30,6 × 67,5 (32,4 × 63,4) | Lula 2026 menos Lula 2º turno 2022: +3,5 pp (mediana da UF -6,3; z +4,4); Lula 2026 menos Lula 1º turno 2022: +4,2 pp (mediana da UF -4,2; z +3,6); Flávio 2026 menos Bolsonaro 2º turno 2022: -5,3 pp (mediana da UF +2,1; z -3,5) | zona pequena (16 seções), variância alta; padrão regional: 2 das 5 zonas mais próximas também estão entre as 5% mais atípicas, o que aponta para efeito político da região, não para uma urna isolada |
| 23 | 99,1 | Groaíras (CE), zona 65 | 2304905 | 9.842 / 34 | 36,8 × 57,5 (25,3 × 63,6) | variação da margem Flávio menos Lula além da UF e do município: +10,8 pp (mediana da UF +0,4; z +3,4); brancos e nulos em 2026: 7,5% (mediana da UF 4,8%; z +3,3); Flávio 2026 menos Bolsonaro 1º turno 2022: +11,5 pp (mediana da UF +6,3; z +2,7) | totalização tardia que não se repetia em 2022: pedir a hora de transmissão de cada seção; padrão regional: 4 das 5 zonas mais próximas também estão entre as 5% mais atípicas, o que aponta para efeito político da região, não para uma urna isolada |
| 24 | 99,1 | Rafael Godeiro (RN), zona 37 | 2410603 | 3.667 / 11 | 43,2 × 54,3 (33,4 × 61,6) | Flávio 2026 menos Bolsonaro 1º turno 2022: +9,8 pp (mediana da UF +4,7; z +3,2); variação da margem Flávio menos Lula além da UF e do município: +8,6 pp (mediana da UF +0,4; z +2,5) | zona pequena (11 seções), variância alta |
| 25 | 99,1 | Carnaúba dos Dantas (RN), zona 22 | 2402402 | 6.324 / 17 | 41,8 × 48,3 (37,5 × 54,4) | terceira via em 2026: 9,9% (mediana da UF 4,5%; z +6,1); brancos e nulos em 2026: 6,7% (mediana da UF 4,5%; z +2,6) | voto concentrado em terceira via (Augusto Cury 7,3%); contexto: ctx-074 |

## Inferido (leitura do modelo)

- Tamanho: a zona mediana do topo 50 tem 6.243 eleitores e 22 seções; a do país, 10.550 e 36. 33 das 50 têm até 30 seções, contra 43,8% das zonas do país.
- Padrão regional: 8 das 50 têm ao menos duas das cinco zonas vizinhas também entre as 5% mais atípicas. Agrupamento geográfico aponta para efeito político da região, não para urna isolada.
- UF das 50: PI 9, CE 8, RN 7, GO 5, SP 4, BA 4, PB 3, SC 2, PR 1, RJ 1, AM 1, RO 1, MT 1, TO 1, MS 1, MG 1.
- Estabilidade: só z robusto e Mahalanobis (sem scikit-learn): 34 das 50 zonas do topo repetem, correlação de postos 0,989; outra semente do Isolation Forest: 49 das 50 zonas do topo repetem, correlação de postos 0,999.
- Regras de explicação acionadas no topo 50: zona pequena (21); efeito político local não medido (16); voto concentrado em terceira via (10); eleitorado cresceu (10); padrão regional (8); totalização tardia que não se repetia em 2022 (2); totalização tardia que já se repetia em 2022 (1).

- Zonas tardias: 102 zonas fecharam bem depois da própria UF (z da hora de conclusão dentro da UF de 2,5 ou mais). A variação da margem além da UF e do município foi +0,11 pp nelas e +0,16 pp nas demais (média ponderada pelos válidos); correlação entre atraso e resíduo -0,038. Lula teve 43,6% dos válidos nas tardias, contra 48,7% no 1º turno de 2022 nas mesmas zonas; nas demais, 45,2% contra 48,6%. A margem de Flávio sobre Lula (contra Bolsonaro e Lula em 2022) andou +10,65 pp nas tardias e +7,33 pp nas demais; a parte da UF é +9,70 contra +7,34, a da vizinhança +0,83 contra -0,17. A diferença vem sobretudo da UF onde as tardias estão; descontadas UF e vizinhança, a demora não veio acompanhada de voto diferente do esperado.

### As 15 zonas que fecharam por último

| Zona | Conclusão (Brasília) | Minutos após a mediana da UF | Seções | Flávio × Lula 2026 | Lula 1º t. 2022 | Escore |
|---|---|---|---|---|---|---|
| Tabatinga (AM), zona 36 | 05/10 02:58 | 360 | 121 | 32,7 × 63,2 | 64,9 | 80,5 |
| Cajari (MA), zona 20 | 05/10 01:56 | 301 | 61 | 14,8 × 82,3 | 84,9 | 96,4 |
| Barreirinha (AM), zona 26 | 05/10 00:45 | 227 | 68 | 8,9 × 87,7 | 89,2 | 60,9 |
| São João das Missões (MG), zona 166 | 05/10 00:45 | 275 | 36 | 28,7 × 68,8 | 75,3 | 95,2 |
| Casa Nova (BA), zona 66 | 05/10 00:39 | 219 | 185 | 23,6 × 72,8 | 78,2 | 77,1 |
| Jutaí (AM), zona 41 | 05/10 00:11 | 192 | 43 | 39,2 × 57,2 | 70,0 | 99,2 |
| Maracanã (PA), zona 31 | 04/10 23:55 | 178 | 118 | 30,5 × 65,4 | 65,5 | 75,2 |
| Mucugê (BA), zona 119 | 04/10 23:49 | 169 | 34 | 29,5 × 66,5 | 68,5 | 96,0 |
| Pindobaçu (BA), zona 115 | 04/10 23:49 | 169 | 57 | 29,8 × 67,2 | 69,0 | 80,2 |
| Ataléia (MG), zona 270 | 04/10 23:41 | 210 | 38 | 34,3 × 61,2 | 67,2 | 77,0 |
| Euclides da Cunha (BA), zona 102 | 04/10 23:40 | 160 | 150 | 19,3 × 76,8 | 80,5 | 67,7 |
| Amaturá (AM), zona 22 | 04/10 23:38 | 160 | 23 | 21,6 × 75,7 | 73,0 | 96,2 |
| Paulistana (PI), zona 38 | 04/10 23:35 | 189 | 67 | 19,4 × 75,5 | 82,4 | 91,3 |
| Muaná (PA), zona 10 | 04/10 23:29 | 152 | 98 | 22,7 × 74,1 | 72,4 | 91,6 |
| Ouro Verde de Minas (MG), zona 270 | 04/10 23:24 | 194 | 25 | 42,2 × 53,9 | 60,1 | 70,3 |

## Hipótese (a verificar)

- 16 das 50 não acionam nenhuma regra estrutural (tamanho, área remota, aldeia, redesenho, crescimento do eleitorado, terceira via, padrão regional). Para elas a hipótese padrão é efeito político local não medido: prefeito, liderança, igreja, candidatura estadual.
- O que resolveria cada caso: boletim de urna por seção (votos por seção contra a zona), ata da mesa receptora, log da urna e registro de substituição ou contingência da seção, todos públicos no TSE.

## Contexto do dia da eleição

`analysis/apuracao_2026/dados/contexto_seguranca.json` tem 76 itens (71 conferidos na página). Temas: coerção 14, logística remota 14, urnas substituídas 10, Forças Armadas e PF 10, outro 9, nota do TSE ou TRE 7, totalização tardia 4, contingência 3, facção ou milícia 3, violência 2. Degrau de evidência: imprensa 65, documento_oficial 10, relato 1.

Itens sobre totalização e notas oficiais, conferidos na página:

- ctx-012: Congestionamento no sistema de dados gerou atraso na apuração, diz TSE (Agência Brasil, 2026-10-04, imprensa). Nunes Marques (22h14): por volta das 19h a totalização nacional para presidente ficou parada em 64% e retomou perto das 20h já em 84%, por "congestionamento de dados" e fluxo acima do normal; disse que, a princípio, não se sabe se isso derivou de outro problema; sem indicação de efeito nos votos. https://agenciabrasil.ebc.com.br/justica/noticia/2026-10/congestionamento-no-sistema-de-dados-gerou-atraso-na-apuracao-diz-tse
- ctx-013: TSE registrou congestionamento no sistema de divulgação, diz Nunes Marques (CNN Brasil, 2026-10-04, imprensa). Painel de divulgação do TSE ficou cerca de uma hora sem atualizar; equipe de TI detectou fluxo de dados acima do normal e isolou temporariamente outros sistemas por protocolo; segundo o ministro, o atraso não comprometeu apuração nem totalização. https://cnnbrasil.com.br/eleicoes/tse-registrou-congestionamento-no-sistema-de-divulgacao-diz-nunes-marques
- ctx-014: TSE destaca normalidade no 1º turno e redução das denúncias de desinformação (Agência Senado, 2026-10-04, imprensa). Relato da entrevista do TSE (23h50): 1.861 de 499.248 urnas substituídas, nenhuma votação manual, atraso de cerca de 50 minutos na atualização dos resultados, 907 registros de crimes eleitorais (311 de boca de urna, 272 de propaganda irregular) e abstenção de 21,07%. https://www12.senado.leg.br/noticias/materias/2026/10/04/tse-destaca-normalidade-no-1o-turno-e-reducao-das-denuncias-de-desinformacao
- ctx-016: "Não temos indicativo de interferência internacional", diz Nunes Marques (Metrópoles, 2026-10-04, imprensa). Balanço parcial das 14h20: Nunes Marques diz que "até o momento" não há indicativo concreto de interferência internacional e que PF e Abin não enviaram relatórios nesse sentido; 1.121 urnas substituídas (0,2%); 59 conduzidos e 25 flagrantes. https://www.metropoles.com/brasil/nao-temos-indicativo-de-interferencia-internacional-diz-nunes-marques
- ctx-017: TSE: Nunes Marques diz que não há indicativo de interferência internacional nas eleições (GC Mais, 2026-10-04, imprensa). PF abriu procedimento preliminar após representação da AGU sobre possível atuação externa; diretor-geral da PF: "Não comprovamos nenhum elemento concreto"; chuva no PR causou filas em alguns horários. https://gcmais.com.br/noticias/2026/10/04/tse-nunes-marques-diz-que-nao-ha-indicativo-de-interferencia-internacional-nas-eleicoes
- ctx-018: Eleições terminam com 408 ocorrências e 152 urnas substituídas em Minas Gerais (Por Dentro de Minas, 2026-10-04, imprensa). Balanço do TRE-MG: 408 ocorrências, 858 envolvidos, 156 conduzidos, 152 urnas substituídas (0,29% de 52.062); homicídio na TI Xakriabá (São João das Missões) atribuído a desavença familiar, sem relação com a eleição; outros veículos citam 145 ou 147 urnas. https://pordentrodeminas.com.br/noticias/eleicoes/2026/10/eleicoes-terminam-com-408-ocorrencias-e-147-urnas-substituidas-em-minas-gerais/
- ctx-019: Sistema do TSE fica travado por mais de 1 hora devido a volume de dados (Metrópoles, 2026-10-04, imprensa). Presidente: 64,81% das seções às 19h06 e retorno às 20h08 com 84,96%; texto diz que "as informações sobre as eleições nos estados, no entanto, seguiram atualizadas minuto a minuto" e, segundo apuração do veículo, houve só atraso no espelho do site, sem interrupção da totalização. https://www.metropoles.com/brasil/sistema-do-tse-fica-travado-por-mais-de-1-hora-devido-a-volume-de-dados
- ctx-020: DF é a primeira Unidade da Federação a concluir apuração no 1º turno (O Tempo, 2026-10-04, imprensa). O Distrito Federal concluiu a totalização do 1º turno às 20h15 de 04/10, primeira UF a chegar a 100%; o texto não informa horário das demais UFs. https://www.otempo.com.br/eleicoes/2026/2026/10/4/unidade-da-federacao-e-a-primeira-a-concluir-apuracao-no-1-turno
- ctx-021: Eleições 2026 em SC: apuração termina mais cedo (Agência AL (Alesc), 2026-10-04, imprensa). SC concluiu a totalização às 21h55, 39 minutos antes de 2022 (22h34); 106 de 17.326 urnas substituídas, sem votação em cédula; abstenção de 18,95%. https://www.alesc.sc.gov.br/agencia/noticia/eleicoes-2026-santa-catarina-balanco/
- ctx-065: Mapa da apuração das eleições 2026 em Casa Nova por zona eleitoral (O Tempo, None, imprensa). Página de resultados marca "100,00% das seções apuradas, atualizado às 00:43"; Lula 72,77% e Flávio Bolsonaro 23,55% dos válidos; comparecimento de 82,26% (47.049 de 57.196); zona eleitoral única; não explica o horário tardio. https://www.otempo.com.br/eleicoes/2026/analises/mapa-dos-votos/ba/casa-nova

Zonas do topo 50 com item de contexto no mesmo município. Coincidência de município não liga o fato à atipicidade da zona.

- Guarani de Goiás (GO), zona 47: Eleições 2026: Equatorial Goiás reforça operação de energia em Goiás (Badiinho, 2026-09-29, imprensa) https://www.badiinho.com.br/equatorial-goias-energia-eleicoes-2026/
- Colina (SP), zona 178: Augusto Cury vota em Colina, cidade natal no interior de São Paulo (NC News, 2026-10-04, imprensa) https://ncnews.com.br/2026/10/04/augusto-cury-vota-colina-eleicoes-2026/
- Colina (SP), zona 178: Escritor Augusto Cury 70 (AVANTE): candidato a Presidente em 2026 (Gazeta do Povo, None, imprensa) https://www.gazetadopovo.com.br/eleicoes/2026/candidatos/br/presidente/escritor-augusto-cury-avante-70/
- Sobral (CE), zona 24: Eleições 2026: Ceará terá reforço policial em áreas mapeadas com influência de facções criminosas (Diário do Nordeste, 2026-09-29, imprensa) https://diariodonordeste.verdesmares.com.br/seguranca/eleicoes-2026-ceara-tera-reforco-policial-em-areas-mapeadas-com-influencia-de-faccoes-criminosas-1.3794882
- Sobral (CE), zona 24: Ciro Gomes retoma domínio em Sobral após derrota histórica em 2022 (O Povo, 2026-10-04, imprensa) https://www.opovo.com.br/noticias/politica/eleicoes/2026/10/04/ciro-gomes-retoma-dominio-em-sobral-apos-derrota-historica-em-2022.html
- Sobral (CE), zona 24: Discussão entre eleitores termina em agressão durante votação em Sobral (CN7, 2026-10-04, imprensa) https://cn7.com.br/discussao-entre-eleitores-termina-em-agressao-durante-votacao-em-sobral/
- Serra Negra do Norte (RN), zona 26: Candidatos ao Governo intensificam agendas no último fim de semana completo antes das eleições no RN (BNews RN, 2026-09-27, imprensa) https://www.bnewsrn.com.br/noticias/politica/candidatos-ao-governo-intensificam-agendas-no-ultimo-fim-de-semana-completo-antes-das-eleicoes-no-rn.html
- Jutaí (AM), zona 41: Amazonas terá dois horários de votação nas Eleições 2026; veja como fica em cada município (NC News, 2026-09-28, imprensa) https://ncnews.com.br/2026/09/28/amazonas-tera-dois-horarios-de-votacao-nas-eleicoes-2026-veja-como-fica-em-cada-municipio/
- Carnaúba dos Dantas (RN), zona 22: Candidatos ao Governo intensificam agendas no último fim de semana completo antes das eleições no RN (BNews RN, 2026-09-27, imprensa) https://www.bnewsrn.com.br/noticias/politica/candidatos-ao-governo-intensificam-agendas-no-ultimo-fim-de-semana-completo-antes-das-eleicoes-no-rn.html
- Fortaleza (CE), zona 3: Prisões por compra de votos e urnas substituídas: veja balanço do 1º turno das eleições no Ceará (Diário do Nordeste, 2026-10-04, imprensa) https://diariodonordeste.verdesmares.com.br/pontopoder/prisoes-por-compra-de-votos-e-urnas-substituidas-veja-balanco-do-1-turno-das-eleicoes-no-ceara-1.3796350
- Nova Roma (GO), zona 47: Eleições 2026: Equatorial Goiás reforça operação de energia em Goiás (Badiinho, 2026-09-29, imprensa) https://www.badiinho.com.br/equatorial-goias-energia-eleicoes-2026/
- São Domingos (GO), zona 47: Eleições 2026: Equatorial Goiás reforça operação de energia em Goiás (Badiinho, 2026-09-29, imprensa) https://www.badiinho.com.br/equatorial-goias-energia-eleicoes-2026/
- Sobral (CE), zona 121: Eleições 2026: Ceará terá reforço policial em áreas mapeadas com influência de facções criminosas (Diário do Nordeste, 2026-09-29, imprensa) https://diariodonordeste.verdesmares.com.br/seguranca/eleicoes-2026-ceara-tera-reforco-policial-em-areas-mapeadas-com-influencia-de-faccoes-criminosas-1.3794882
- Sobral (CE), zona 121: Ciro Gomes retoma domínio em Sobral após derrota histórica em 2022 (O Povo, 2026-10-04, imprensa) https://www.opovo.com.br/noticias/politica/eleicoes/2026/10/04/ciro-gomes-retoma-dominio-em-sobral-apos-derrota-historica-em-2022.html
- Sobral (CE), zona 121: Discussão entre eleitores termina em agressão durante votação em Sobral (CN7, 2026-10-04, imprensa) https://cn7.com.br/discussao-entre-eleitores-termina-em-agressao-durante-votacao-em-sobral/

## Limites

- Zona não é seção: a unidade aqui soma de 4 a 673 seções, e um problema numa seção se dilui na zona.
- Variação contra 2022 não é fraude: candidatos diferentes (Flávio não é Jair, e a terceira via de 2026 não é a de 2022), prefeitos eleitos em 2024, mudança de eleitorado e migração explicam a maior parte.
- Zona pequena tem variância maior; o ajuste de tamanho reduz, mas não elimina, o peso delas no topo.
- O escore é posição relativa dentro do país (percentil médio), não probabilidade de irregularidade; 1% das zonas sempre terá escore 99.
- Explicação provável é regra declarada sobre dados públicos, não verificação no local.
- Os arquivos de zona do TSE pararam antes de 100% em 12 zonas (69 seções), embora os arquivos de UF tenham fechado: os números dessas zonas são parciais.

## Lista para mapa (topo 50)

```csv
lat;lon;escore;rotulo
-8.5387;-41.3715;99.9;Queimada Nova (PI), zona 38
-13.9268;-46.4814;99.9;Guarani de Goiás (GO), zona 47
-7.09;-40.8341;99.9;São Julião (PI), zona 40
-8.1054;-42.2657;99.8;Pedro Laurentino (PI), zona 69
-4.8452;-37.2581;99.6;Tibau (RN), zona 49
-20.7162;-48.5386;99.6;Colina (SP), zona 178
-4.1914;-40.4807;99.6;Varjota (CE), zona 65
-24.5504;-49.1811;99.5;Itapirapuã Paulista (SP), zona 10
-22.4632;-51.7903;99.5;Sandovalina (SP), zona 261
-8.1923;-41.6244;99.5;São Francisco de Assis do Piauí (PI), zona 90
-3.6948;-40.4035;99.4;Sobral (CE), zona 24
-25.6751;-50.2863;99.4;São João do Triunfo (PR), zona 52
-6.5418;-37.7167;99.4;Mato Grosso (PB), zona 36
-6.4606;-38.1734;99.3;Tenente Ananias (RN), zona 41
-22.1057;-41.4478;99.2;Quissamã (RJ), zona 255
-6.6677;-37.3985;99.2;Serra Negra do Norte (RN), zona 26
-4.0327;-40.7821;99.2;Graça (CE), zona 79
-2.7513;-66.7739;99.2;Jutaí (AM), zona 41
-26.8247;-51.3327;99.2;Macieira (SC), zona 6
-15.1517;-39.6849;99.1;Itaju do Colônia (BA), zona 137
-3.8999;-40.7525;99.1;Mucambo (CE), zona 79
-15.1799;-39.4945;99.1;Jussari (BA), zona 28
-3.9175;-40.38;99.1;Groaíras (CE), zona 65
-6.0756;-37.716;99.1;Rafael Godeiro (RN), zona 37
-6.5567;-36.5908;99.1;Carnaúba dos Dantas (RN), zona 22
-3.7316;-38.5127;99.0;Fortaleza (CE), zona 3
-7.1118;-36.9557;99.0;Areia de Baraúnas (PB), zona 65
-6.7517;-36.7321;99.0;Santana do Seridó (RN), zona 24
-6.3205;-38.4899;98.9;Venha-Ver (RN), zona 43
-13.7768;-46.9068;98.9;Nova Roma (GO), zona 47
-7.9726;-41.8713;98.8;Bela Vista do Piauí (PI), zona 37
-13.4564;-46.3718;98.8;São Domingos (GO), zona 47
-7.9868;-45.1627;98.8;Baixa Grande do Ribeiro (PI), zona 44
-15.3458;-48.7992;98.7;Vila Propício (GO), zona 74
-10.8256;-65.2928;98.7;Guajará-Mirim (RO), zona 1
-14.076;-51.8867;98.7;Nova Nazaré (MT), zona 30
-12.9177;-46.5767;98.6;Novo Alegre (TO), zona 22
-14.9599;-39.3019;98.6;Buerarema (BA), zona 166
-7.7854;-42.2504;98.6;Paes Landim (PI), zona 37
-3.746;-40.2681;98.5;Sobral (CE), zona 121
-23.8273;-54.5113;98.5;Japorã (MS), zona 33
-18.517;-49.501;98.5;Cachoeira Dourada (MG), zona 302
-6.9167;-41.8903;98.5;São João da Varjota (PI), zona 5
-16.9546;-49.2473;98.5;Hidrolândia (GO), zona 132
-27.4917;-50.9582;98.4;Vargem (SC), zona 7
-15.4621;-39.6508;98.4;Pau Brasil (BA), zona 133
-7.1168;-34.8365;98.4;João Pessoa (PB), zona 76
-5.6806;-42.7382;98.4;Miguel Leão (PI), zona 58
-23.7996;-46.7081;98.4;São Paulo (SP), zona 381
-5.7112;-38.1678;98.4;Potiretama (CE), zona 86
```

## Parágrafo publicável

A casa rodou uma triagem estatística sobre as 6.106 zonas eleitorais do país no voto para presidente, comparando cada uma com a própria UF e com o resultado de 2022. Das 50 zonas mais atípicas, 33 têm até 30 seções, e 34 têm explicação comum provável: tamanho pequeno, eleitorado que cresceu muito acima da UF desde 2022, voto regional em candidatura de terceira via, padrão compartilhado com as zonas vizinhas ou área remota. As outras 16 ficam como hipótese de política local, a conferir seção por seção. As 102 zonas que fecharam por último, bem depois da própria UF, votaram como as demais em relação à região: a variação da margem além do esperado foi de +0,11 ponto nelas e de +0,16 nas outras. Atipicidade não é irregularidade. A triagem por zona não prova nem descarta problema em seção específica; isso exige o boletim de urna, a ata da mesa e o log da urna, que o TSE publica.

## Reprodução

```
python3 scripts/apuracao-2026-anomalias.py
```
