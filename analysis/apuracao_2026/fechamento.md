# Onde a votação termina tarde: encerramento e recebimento por seção, 2022 e 2026

Gerado em 2026-10-05T23:15:25Z por `scripts/apuracao-2026-fechamento.py`. Dados em `analysis/apuracao_2026/dados/fechamento.json`.

> Seção que fecha tarde é seção que pede explicação, não indício de irregularidade. O boletim de urna mostra quando a votação terminou e quantos votaram; não mostra por quê. O que separa fila, identificação lenta e irregularidade é documento: a ata da mesa e o log da urna.

## Definições

- **minutos**: minutos depois das 17h de Brasília do dia da eleição (04/10/2026 e 02/10/2022).
- **encerramento**: hora de término da votação gravada no boletim de urna de 2026 (dataHoraEncerramento, que a especificação do TSE descreve como término da aquisição do voto, o último voto), na hora local da urna, convertida para Brasília pelo fuso do município.
- **fuso**: a votação abriu às 8h de Brasília no país inteiro; a hora local de abertura mais frequente no município dá o fuso (6h no Acre e no oeste do Amazonas, 7h em AM, RR, RO, MT e MS). Seção cujo boletim chegou ao TSE mais de 5 minutos antes do encerramento convertido fica sem hora de encerramento (relógio ou fuso inconsistente).
- **recebimento**: hora em que o boletim chegou ao TSE, já em hora de Brasília: campo dr/hr do aux.json em 2026 e DT_RECEBIMENTO_BU_HOR_TSE ('Hora TSE') em 2022. É a única régua dos dois anos e soma a fila da seção com o transporte da mídia até o ponto de transmissão.
- **tardia**: seção com encerramento às 18h de Brasília ou depois.
- **exterior**: fora das contas: vota na hora local da cidade.

- Seções de 2026 com boletim (Brasil, sem exterior): 497.877; com voto conferido: 496.580; com relógio ou fuso inconsistente (sem encerramento): 31.
- Seções de 2022 (Brasil): 471.010; nas UFs completas de 2026: 471.010.

## 1. Quando a votação termina

Encerramento (2026, último voto, hora de Brasília):

| grupo | seções | mediana | p90 | p99 | % 17:30+ | % 18:00+ | % 19:00+ |
|---|---|---|---|---|---|---|---|
| Brasil | 497.844 | 17:04 | 17:54 | 19:18 | 17,4 | 8,6 | 1,7 |
| Norte | 43.768 | 17:08 | 18:13 | 19:38 | 27,2 | 13,9 | 2,9 |
| Nordeste | 140.828 | 17:14 | 18:31 | 19:51 | 37,1 | 20,7 | 4,5 |
| Centro-Oeste | 38.019 | 17:04 | 17:32 | 18:29 | 10,7 | 3,5 | 0,3 |
| Sudeste | 203.215 | 17:04 | 17:24 | 18:29 | 8,0 | 2,9 | 0,3 |
| Sul | 72.014 | 17:02 | 17:09 | 17:55 | 3,2 | 0,8 | 0,0 |

Recebimento no TSE, 2026:

| grupo | seções | mediana | p90 | p99 | % 17:30+ | % 18:00+ | % 19:00+ |
|---|---|---|---|---|---|---|---|
| Brasil | 497.877 | 18:45 | 20:16 | 21:18 | 97,9 | 85,4 | 39,6 |
| Norte | 43.769 | 18:31 | 20:02 | 21:56 | 93,4 | 72,1 | 31,3 |
| Nordeste | 140.828 | 19:02 | 20:51 | 21:47 | 98,9 | 89,8 | 51,8 |
| Centro-Oeste | 38.048 | 18:21 | 19:14 | 20:50 | 95,2 | 67,8 | 17,9 |
| Sudeste | 203.217 | 18:55 | 20:11 | 21:00 | 99,5 | 93,1 | 44,5 |
| Sul | 72.015 | 18:25 | 19:11 | 20:40 | 95,4 | 72,7 | 18,4 |

Recebimento no TSE, 2022 (mesmas UFs):

| grupo | seções | mediana | p90 | p99 | % 17:30+ | % 18:00+ | % 19:00+ |
|---|---|---|---|---|---|---|---|
| Brasil | 471.010 | 19:34 | 20:30 | 22:14 | 99,4 | 97,5 | 74,5 |
| Norte | 38.975 | 19:17 | 20:26 | 22:06 | 97,3 | 91,6 | 60,5 |
| Nordeste | 132.578 | 19:55 | 21:06 | 23:00 | 99,9 | 99,1 | 84,1 |
| Centro-Oeste | 35.932 | 18:50 | 20:00 | 20:47 | 97,3 | 88,4 | 42,4 |
| Sudeste | 194.361 | 19:40 | 20:28 | 21:42 | 100,0 | 99,2 | 80,5 |
| Sul | 69.164 | 19:13 | 20:07 | 20:58 | 99,5 | 97,4 | 63,8 |

Por UF (encerramento 2026 | recebimento 2026 | recebimento 2022, % depois das 18h e mediana):

| UF | completa | enc. % 18h+ | enc. mediana | rec. 2026 mediana | rec. 2022 mediana |
|---|---|---|---|---|---|
| AC | sim | 3,3 | 17:03 | 18:18 | 18:52 |
| AL | sim | 33,0 | 17:32 | 19:21 | 20:25 |
| AM | sim | 23,7 | 17:23 | 18:36 | 19:16 |
| AP | sim | 15,4 | 17:12 | 18:45 | 19:19 |
| BA | sim | 24,7 | 17:19 | 19:11 | 20:01 |
| CE | sim | 18,5 | 17:13 | 19:12 | 19:54 |
| DF | sim | 1,9 | 17:06 | 17:47 | 18:11 |
| ES | sim | 2,0 | 17:03 | 18:17 | 18:37 |
| GO | sim | 3,7 | 17:03 | 18:38 | 19:10 |
| MA | sim | 17,9 | 17:11 | 19:01 | 20:16 |
| MG | sim | 4,5 | 17:03 | 18:57 | 19:46 |
| MS | sim | 1,4 | 17:03 | 18:10 | 18:35 |
| MT | sim | 6,2 | 17:07 | 18:25 | 19:07 |
| PA | sim | 17,6 | 17:13 | 18:43 | 19:33 |
| PB | sim | 10,2 | 17:07 | 18:15 | 19:30 |
| PE | sim | 29,0 | 17:30 | 19:05 | 19:58 |
| PI | sim | 9,0 | 17:05 | 18:39 | 19:30 |
| PR | sim | 0,9 | 17:02 | 18:12 | 19:04 |
| RJ | sim | 8,0 | 17:07 | 19:09 | 20:00 |
| RN | sim | 21,6 | 17:17 | 18:54 | 19:32 |
| RO | sim | 0,3 | 17:04 | 18:19 | 19:10 |
| RR | sim | 1,2 | 17:04 | 18:40 | 19:14 |
| RS | sim | 0,5 | 17:02 | 18:27 | 19:08 |
| SC | sim | 1,0 | 17:02 | 18:46 | 19:41 |
| SE | sim | 7,9 | 17:04 | 18:42 | 19:18 |
| SP | sim | 0,3 | 17:04 | 18:49 | 19:35 |
| TO | sim | 2,4 | 17:04 | 17:55 | 18:40 |

Por tamanho (aptos da seção), UFs completas:

| faixa | seções 2026 | votantes médios | % enc. 18h+ | % das tardias | % rec. 19h+ 2026 | % rec. 19h+ 2022 |
|---|---|---|---|---|---|---|
| até 199 | 21.764 | 124,5 | 0,2 | 0,1 | 36,7 | 72,1 |
| 200 a 249 | 49.148 | 181,8 | 0,3 | 0,4 | 28,9 | 63,9 |
| 250 a 299 | 97.872 | 221,0 | 2,4 | 5,5 | 28,5 | 64,0 |
| 300 a 349 | 167.135 | 259,3 | 7,2 | 28,1 | 37,4 | 70,5 |
| 350 a 399 | 142.096 | 294,3 | 15,6 | 51,5 | 50,5 | 81,6 |
| 400 ou mais | 19.862 | 327,1 | 31,0 | 14,3 | 63,9 | 90,3 |

Por tipo de local inferido, UFs completas:

| tipo | seções 2026 | % enc. 18h+ | % das tardias | rec. 2026 mediana | rec. 2022 mediana |
|---|---|---|---|---|---|
| aldeia ou terra indígena | 1.428 | 22,9 | 0,8 | 18:48 | 19:53 |
| zona rural, assentamento ou quilombo | 62.798 | 16,7 | 24,4 | 19:03 | 19:57 |
| unidade prisional ou socioeducativa | 293 | 2,4 | 0,0 | 18:24 | 19:11 |
| escola fora de zona rural | 312.787 | 8,0 | 58,4 | 18:43 | 19:32 |
| outro local | 120.571 | 5,9 | 16,4 | 18:46 | 19:33 |

Tipo de local é inferência por palavra-chave no nome, bairro e endereço do local de votação, na ordem das regras: a primeira que casa decide. Escola num povoado conta como zona rural. Em 2022 o arquivo não tem bairro, só nome e endereço.

## 2. Persistência (régua de recebimento)

- Critério: cobertura de 2026 de ao menos 95% das seções principais e 3 seções ou mais nos dois anos. Municípios comparados: 5.570.
- Mediana das medianas municipais: 19:37 em 2022 e 18:44 em 2026.
- Correlação 2022 × 2026 da mediana municipal: Pearson 0,528, Spearman 0,595 (IC 95% 0,576 a 0,614); dentro da UF, Pearson 0,437 e Spearman 0,484.
- Décimo mais tardio nos dois anos (corte de 2022: 20:30; de 2026: 20:01): 198 municípios, contra 55,7 esperados por acaso (3,55 vezes).
- p90 de recebimento às 19h ou depois: 3.418 municípios em 2026, 5.098 em 2022, 3.370 nos dois. O corte de hora fixo quase não separa nada em 2022, quando o recebimento inteiro foi mais tarde; por isso a persistência usa o décimo de cada ano.

| UF | município | eleitorado | mediana 2022 | mediana 2026 | último voto (mediana) | transporte (mediana) | % rural |
|---|---|---|---|---|---|---|---|
| MG | PINGO D'ÁGUA | 4.149 | 22:46 | 21:51 | 17:12 | 4h39 | 0 |
| BA | CAEM | 8.150 | 23:41 | 21:20 | 17:05 | 3h48 | 50 |
| MG | CATUJI | 8.492 | 23:04 | 21:13 | 17:26 | 3h47 | 41 |
| BA | ABARÉ | 14.734 | 22:15 | 22:18 | 19:18 | 2h02 | 60 |
| MG | IBIAÍ | 6.806 | 22:13 | 22:02 | 17:30 | 4h35 | 24 |
| MG | SANTANA DO MANHUAÇU | 7.807 | 22:20 | 21:32 | 17:04 | 4h24 | 0 |
| MG | ITAIPÉ | 9.564 | 22:03 | 22:06 | 17:22 | 4h44 | 23 |
| MG | GAMELEIRAS | 4.725 | 22:33 | 21:01 | 17:07 | 3h54 | 10 |
| BA | TAPEROÁ | 14.359 | 22:08 | 21:24 | 17:52 | 3h32 | 27 |
| MA | JATOBÁ | 7.205 | 22:46 | 20:59 | 17:03 | 3h55 | 56 |
| MG | TAPARUBA | 4.088 | 21:50 | 21:48 | 17:16 | 4h34 | 0 |
| MG | POTÉ | 12.644 | 21:40 | 21:39 | 17:20 | 4h19 | 2 |
| AL | OURO BRANCO | 10.029 | 22:20 | 20:59 | 19:22 | 1h09 | 0 |
| BA | SERROLÂNDIA | 11.033 | 22:08 | 20:59 | 17:27 | 3h34 | 30 |
| MA | ÁGUA DOCE DO MARANHÃO | 11.520 | 22:03 | 21:00 | 17:08 | 3h07 | 81 |
| CE | PIRES FERREIRA | 8.610 | 21:30 | 22:28 | 17:10 | 5h18 | 0 |
| BA | PRESIDENTE TANCREDO NEVES | 21.689 | 21:26 | 22:06 | 18:26 | 3h41 | 35 |
| BA | ITAGUAÇU DA BAHIA | 10.842 | 21:29 | 21:39 | 17:46 | 3h31 | 78 |
| MG | MENDES PIMENTEL | 4.977 | 22:22 | 20:56 | 17:04 | 3h53 | 0 |
| MG | PEDRAS DE MARIA DA CRUZ | 8.112 | 21:39 | 21:00 | 17:21 | 3h40 | 20 |
| BA | IRAJUBA | 5.507 | 21:37 | 20:59 | 17:07 | 3h51 | 33 |
| MG | SENHORA DE OLIVEIRA | 5.747 | 22:14 | 20:56 | 17:15 | 3h43 | 53 |
| MG | MARILAC | 4.681 | 22:50 | 20:52 | 17:43 | 3h10 | 7 |
| AL | MATRIZ DE CAMARAGIBE | 18.656 | 21:37 | 20:59 | 18:01 | 2h57 | 0 |
| MG | PORTO FIRME | 9.025 | 21:16 | 21:50 | 17:19 | 4h31 | 23 |
| MG | CURRAL DE DENTRO | 6.816 | 21:32 | 20:59 | 17:52 | 3h08 | 0 |
| MG | VARZELÂNDIA | 17.159 | 21:13 | 21:53 | 17:15 | 4h39 | 46 |
| BA | ITATIM | 12.954 | 21:32 | 20:58 | 17:49 | 3h04 | 15 |
| AL | SÃO MIGUEL DOS MILAGRES | 8.255 | 21:43 | 20:56 | 18:29 | 2h25 | 14 |
| BA | CANSANÇÃO | 28.890 | 21:26 | 20:59 | 18:07 | 2h08 | 67 |

Locais de votação casados entre os anos: 70.278; Spearman 0,555; persistentes 2.418 contra 702,8 esperados; 7.133 seções de 2026 dentro deles.

## 3. Encerramento tardio e voto

Bruta, por faixa de encerramento (% dos válidos, Brasil das UFs completas):

| faixa | seções | votantes | Lula | Flávio |
|---|---|---|---|---|
| até 17:00 | 0 | 0 | n/d | n/d |
| 17:00 a 17:30 | 409.775 | 99.650.206 | 42,27 | 49,48 |
| 17:30 a 18:00 | 43.800 | 12.398.038 | 53,16 | 40,28 |
| 18:00 a 19:00 | 34.613 | 10.070.165 | 58,62 | 35,69 |
| depois de 19:00 | 8.359 | 2.466.892 | 67,32 | 28,36 |

Inclinação (pontos por hora de atraso no encerramento):

- bruta, sem controle: Lula +12,56 (IC 95% de +11,95 a +13,15); Flávio −10,65 (IC 95% de −11,19 a −10,09).
- dentro da zona: Lula +2,24 (IC 95% de +2,10 a +2,39); Flávio −1,86 (IC 95% de −2,00 a −1,73).
- dentro da zona, com tamanho e tipo de local: Lula +2,55 (IC 95% de +2,40 a +2,69); Flávio −2,05 (IC 95% de −2,18 a −1,92).

Spearman seção a seção dentro da UF (hora de encerramento × % de Lula):

- SP: 0,354 (103.230 seções)
- GO: 0,212 (15.686 seções)
- ES: 0,202 (9.844 seções)
- MS: 0,177 (7.106 seções)
- MG: 0,160 (51.169 seções)
- RS: 0,149 (27.546 seções)
- RO: 0,138 (4.698 seções)
- PE: 0,134 (21.418 seções)
- PI: 0,130 (10.225 seções)
- PA: 0,116 (20.827 seções)
- SE: 0,114 (5.923 seções)
- PR: 0,112 (27.142 seções)
- TO: 0,107 (4.384 seções)
- MT: 0,102 (8.258 seções)
- BA: 0,086 (35.476 seções)
- AC: 0,085 (2.270 seções)
- RJ: 0,080 (37.675 seções)
- SC: 0,077 (17.326 seções)
- AM: 0,062 (8.156 seções)
- AL: 0,052 (7.101 seções)
- RR: 0,032 (1.519 seções)
- RN: 0,003 (8.115 seções)
- PB: -0,002 (10.712 seções)
- CE: -0,022 (23.765 seções)
- MA: -0,023 (18.093 seções)
- DF: -0,113 (6.969 seções)
- AP: -0,120 (1.914 seções)

Estimador do modelo de urna (seção tardia menos as demais da zona):

- encerrou às 18h ou depois, contra as demais da mesma zona (2026; 3.536 unidades, 42.917 seções tardias): Lula, % dos válidos +3,27 (de +2,98 a +3,56); Flávio, % dos válidos (Bolsonaro em 2022) −2,69 (de −2,97 a −2,43); comparecimento, % dos aptos −1,00 (de −1,17 a −0,83); votantes por seção +37,65 (de +36,57 a +38,79); votantes por hora de urna aberta +0,47 (de +0,37 a +0,59); habilitados por ano de nascimento, % dos votantes +1,01 (de +0,84 a +1,20); sem biometria cadastrada, % dos votantes −0,28 (de −0,42 a −0,14).
- o mesmo, dentro da zona e da mesma faixa de eleitorado apto (2026; 5.787 unidades, 40.777 seções tardias): Lula, % dos válidos +4,02 (de +3,78 a +4,27); Flávio, % dos válidos (Bolsonaro em 2022) −3,32 (de −3,57 a −3,10); comparecimento, % dos aptos −0,18 (de −0,32 a −0,04); votantes por seção +4,73 (de +4,17 a +5,26); votantes por hora de urna aberta −2,58 (de −2,64 a −2,52); habilitados por ano de nascimento, % dos votantes +1,37 (de +1,22 a +1,55); sem biometria cadastrada, % dos votantes −0,23 (de −0,36 a −0,09).
- encerrou às 19h ou depois, contra as demais da mesma zona (2026; 1.765 unidades, 8.359 seções tardias): Lula, % dos válidos +4,86 (de +4,45 a +5,29); Flávio, % dos válidos (Bolsonaro em 2022) −4,04 (de −4,43 a −3,67); comparecimento, % dos aptos −1,45 (de −1,72 a −1,19); votantes por seção +40,99 (de +39,29 a +42,73); votantes por hora de urna aberta −0,93 (de −1,10 a −0,77); habilitados por ano de nascimento, % dos votantes +1,48 (de +1,21 a +1,81); sem biometria cadastrada, % dos votantes −0,69 (de −0,99 a −0,43).
- chegou ao TSE no décimo mais tardio de 2026, contra as demais da zona (2026; 2.032 unidades, 43.783 seções tardias): Lula, % dos válidos +2,99 (de +2,60 a +3,40); Flávio, % dos válidos (Bolsonaro em 2022) −2,52 (de −2,89 a −2,17); comparecimento, % dos aptos −0,44 (de −0,59 a −0,27); votantes por seção +14,41 (de +12,48 a +16,27).
- chegou ao TSE no décimo mais tardio de 2022, contra as demais da zona (2022; 1.933 unidades, 37.301 seções tardias): Lula, % dos válidos +2,60 (de +2,17 a +3,05); Flávio, % dos válidos (Bolsonaro em 2022) −2,22 (de −2,60 a −1,84); comparecimento, % dos aptos −0,49 (de −0,69 a −0,30); votantes por seção +15,32 (de +13,25 a +17,33).

### Conferência com a análise por seção

- Publicado em `secoes.json` (2026-10-05T16:58:37Z, 76.315 seções válidas): 1.199 seções depois das 19h, Lula +2,73 e Flávio −2,22 contra o resto da zona.
- Base atual, mesmas UFs completas da rodada publicada: 1.138 seções; fórmula da análise por seção +2,66; a mesma fórmula contra só as não tardias +3,06; estimador deste capítulo +4,71 (IC 95% de +3,53 a +6,11).
- Base atual, todas as UFs com boletim: 8.359 seções; fórmula da análise por seção +3,43; a mesma fórmula contra só as não tardias +3,85; estimador deste capítulo +4,86 (IC 95% de +4,45 a +5,29).

A análise por seção compara cada seção tardia com o resto da própria zona, inclusive as outras seções tardias, e pondera pelos válidos da seção. O estimador deste capítulo compara o agregado das seções tardias com o das demais na mesma zona, pondera pelos votantes das duas partes e deixa fora a zona sem os dois grupos. Os dois medem a mesma coisa por caminhos diferentes; a diferença entre eles é de método e de base, não de dado.

## Achados

### Achado contrário

- O atraso é, antes de tudo, tamanho de seção: com 400 aptos ou mais, 31,0% das seções encerraram às 18h ou depois; com até 199, 0,2%. Dentro da mesma zona, a seção com 350 votantes ou mais tem 32,4 pontos a mais de chance de fechar às 18h ou depois do que a de 200 a 249.
- Onde a eleição termina tarde nos dois anos, termina tarde mais por distância do que por fila: nos 198 municípios que ficaram entre os 10% mais tardios do país nos dois anos, a votação terminou, na mediana, às 17:17 e a mídia levou 3h12 até o TSE; no conjunto, 17:04 e 1h28. Dos 2.418 locais de votação na mesma situação, 68,4% ficam em zona rural, assentamento ou quilombo pelo nome e endereço, contra 27,7% dos locais comparados.
- A seção que chega tarde ao TSE vota mais em Lula do que o resto da própria zona nos dois anos, e por margem parecida: +2,6 pontos em 2022 e +3,0 em 2026 (décimo mais tardio de cada ano). O padrão não nasceu em 2026.

### Verificado

- Nas 27 UFs completas, metade das urnas encerrou a votação até as 17:04 de Brasília; 8,6% encerraram às 18h ou depois e 1,7% às 19h ou depois.
- Nenhuma urna encerrou antes das 17h de Brasília (0 seções nessa faixa), coerente com a regra: às 17h quem está na fila recebe senha e vota depois.
- O boletim chegou ao TSE, na mediana, às 18:45 em 2026 e às 19:34 em 2022, nas mesmas UFs; depois das 19h chegaram 39,6% das seções em 2026 e 74,5% em 2022.
- As UFs com maior parcela de seções encerradas às 18h ou depois: AL 33,0%; PE 29,0%; BA 24,7%; AM 23,7%; RN 21,6%; as de menor: RS 0,5%; SP 0,3%; RO 0,3%.
- A régua de chegada de 2026 tem um buraco: nenhum boletim registrado como recebido entre 19:32 e 19:59 (27,5 minutos) e 19.784 nos cinco minutos seguintes. É a pausa geral do TSE da noite; nesse trecho a hora de chegada mede o tribunal, não a seção. Em 2022, o maior buraco foi de 7,4 minutos.
- Da hora de recebimento de 2026, a fila (17h até o último voto) responde por 4 min na mediana e o caminho da mídia até o TSE por 1h31.

### Inferido

- Sem controle, cada hora de atraso no encerramento vem com +12,56 pontos de Lula nos válidos. Dentro da mesma zona, +2,24 (IC 95% de +2,10 a +2,39); dentro da zona com tamanho e tipo de local, +2,55 (IC 95% de +2,40 a +2,69). Sobra 20,3% da correlação bruta.
- Seções que encerraram depois das 19h: +24,9 pontos de Lula sem controle, +5,0 dentro da zona e +4,9 com tamanho e tipo, contra as que encerraram entre 17:00 e 17:30.
- A seção tardia tem mais eleitor habilitado por ano de nascimento (biometria que não reconheceu): +1,01 ponto dentro da zona e +1,37 dentro da zona e da faixa de tamanho. Com o mesmo tamanho, ela processou 2,6 votantes por hora a menos: votação mais lenta, não só mais gente.
- O atraso persiste no lugar: a correlação de postos entre a mediana municipal de recebimento de 2022 e a de 2026 é 0,59 (IC 95% de 0,58 a 0,61), 0,48 dentro da UF; 198 municípios ficaram no décimo mais tardio nos dois anos, 3,5 vezes o esperado por acaso.

### Juízo editorial

- A providência barata é pôr fiscal de partido nas seções que historicamente fecham tarde: é ali que a fila depois das 17h, o mesário e a boca de urna ficam sem testemunha. A lei permite que um mesmo fiscal cubra mais de uma seção do mesmo local de votação (Lei 9.504, art. 65, § 1º); os 2.418 locais persistentes somam 7.133 seções.
- O número que importa é o que sobra dentro da zona, com tamanho e tipo de local controlados. Ele existe e é positivo para Lula; ele não diz por quê.

### Hipótese

- Mesário que vota no lugar de ausente (o pianista), compra de voto e boca de urna são hipóteses, não achados: o boletim não as testa. O que as testaria é o log da urna (cada habilitação com hora e forma; uma sequência de habilitações por ano de nascimento em poucos segundos no fim do dia é a assinatura do pianista), a ata da mesa (ocorrências, fiscais presentes, senhas entregues às 17h), boletim de ocorrência e representação ao juiz eleitoral ou ao Ministério Público Eleitoral.
- A parte da correlação que sobra dentro da zona pode vir do perfil do eleitor da seção (idade, escolaridade, trabalho braçal), que pesa ao mesmo tempo na identificação biométrica e no voto. Sem idade por seção para o país, isso fica hipótese.

## Fontes legais

- Res. TSE nº 23.751/2026 (atos gerais do processo eleitoral, Eleições 2026), artigo não conferido: votação das 8h às 17h, horário de Brasília, em todo o país; no exterior, hora local. Conferido pela citação na matéria do Poder360 de 04/10/2026 ('Eleições 2026: saiba até que horas você pode votar'); tse.jus.br devolveu 403 às ferramentas, por isso o número do artigo não foi conferido no texto da resolução.
- Código Eleitoral (Lei nº 4.737/1965), art. 153 e parágrafo único: às 17 horas o presidente da mesa entrega senhas a todos os eleitores presentes; a votação continua na ordem das senhas. Conferido texto do artigo em reprodução da lei (investidura.com.br).
- Código Eleitoral (Lei nº 4.737/1965), art. 132: perante as mesas receptoras, candidatos, delegados e fiscais dos partidos podem fiscalizar a votação, formular protestos e fazer impugnações, inclusive sobre a identidade do eleitor. Conferido texto do artigo em resultado de busca (modeloinicial.com.br).
- Lei nº 9.504/1997, art. 65, caput e §§ 1º a 4º: fiscal maior de 18 anos e fora da mesa; um fiscal pode fiscalizar mais de uma seção no mesmo local de votação (§ 1º); credenciais expedidas pelos partidos ou coligações (§ 2º); no máximo 2 fiscais de cada partido ou coligação por seção (§ 4º). Conferido texto do artigo em reprodução da lei (modeloinicial.com.br).
- Lei nº 9.504/1997, arts. 66 e 68, § 1º: partidos e coligações podem fiscalizar todas as fases da votação e da apuração (art. 66); o presidente da mesa entrega cópia do boletim de urna ao partido que a pedir até uma hora depois da expedição (art. 68, § 1º). Conferido texto em reprodução da lei (pdba.georgetown.edu).
- Lei nº 9.504/1997, art. 39, § 5º, II, e art. 41-A: arregimentação de eleitor e propaganda de boca de urna no dia da eleição são crime (art. 39, § 5º, II); captação ilícita de sufrágio, a compra de voto, sujeita a multa e cassação do registro ou do diploma (art. 41-A). Conferido resultado de busca com o texto dos dispositivos.

## Limites

- A coleta dos boletins de 2026 ainda está em andamento; as contas que comparam anos usam só as UFs completas, e os números mudam na rodada final.
- Encerramento existe só em 2026: o arquivo de 2022 não traz a hora do último voto. A comparação entre anos usa a hora de recebimento no TSE, que soma fila e transporte da mídia.
- A hora de encerramento depende do relógio da urna e do fuso inferido pelo município; seções com recebimento antes do encerramento convertido ficam fora das contas de encerramento.
- Tipo de local é inferência por palavra-chave, não cadastro oficial; em 2022 não há bairro no arquivo do TSE.
- Idade do eleitor por seção não está no acervo para o país (só o Acre); a parte da fila que vem de eleitor idoso não é separável aqui.
- Correlação dentro da zona não identifica mecanismo: fila, identificação lenta e irregularidade deixam o mesmo rastro no boletim. Só a ata da mesa e o log da urna, que registra cada habilitação com hora, separam as três.
- O log da urna de cada seção está publicado pelo TSE; o acervo da coleta guarda só o nome, o tamanho e o SHA-256 dele, não o arquivo.
- A hora de recebimento de 2026 atravessa a pausa geral do TSE: boletins que chegaram durante a pausa ficaram registrados no fim dela, e nesse trecho a hora mede o tribunal, não a seção.
