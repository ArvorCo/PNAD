# Onde a votação termina tarde: encerramento e recebimento por seção, 2022 e 2026

Gerado em 2026-10-05T19:02:29Z por `scripts/apuracao-2026-fechamento.py`. Dados em `analysis/apuracao_2026/dados/fechamento.json`.

> Seção que fecha tarde é seção que pede explicação, não indício de irregularidade. O boletim de urna mostra quando a votação terminou e quantos votaram; não mostra por quê. O que separa fila, identificação lenta e irregularidade é documento: a ata da mesa e o log da urna.

**Coleta parcial.** UFs completas em 2026: AC, AL, AM, AP, CE, DF, ES, GO, MA, MS, MT, PA, PB, PE, PI, RN, RO, RR, SC, SE, TO. Em coleta: RS. Sem boletim ainda: BA, MG, PR, RJ, SP. As comparações entre anos usam só as UFs completas. Rodada final: rodar de novo este script e o build da página.

## Definições

- **minutos**: minutos depois das 17h de Brasília do dia da eleição (04/10/2026 e 02/10/2022).
- **encerramento**: hora de término da votação gravada no boletim de urna de 2026 (dataHoraEncerramento, que a especificação do TSE descreve como término da aquisição do voto, o último voto), na hora local da urna, convertida para Brasília pelo fuso do município.
- **fuso**: a votação abriu às 8h de Brasília no país inteiro; a hora local de abertura mais frequente no município dá o fuso (6h no Acre e no oeste do Amazonas, 7h em AM, RR, RO, MT e MS). Seção cujo boletim chegou ao TSE mais de 5 minutos antes do encerramento convertido fica sem hora de encerramento (relógio ou fuso inconsistente).
- **recebimento**: hora em que o boletim chegou ao TSE, já em hora de Brasília: campo dr/hr do aux.json em 2026 e DT_RECEBIMENTO_BU_HOR_TSE ('Hora TSE') em 2022. É a única régua dos dois anos e soma a fila da seção com o transporte da mídia até o ponto de transmissão.
- **tardia**: seção com encerramento às 18h de Brasília ou depois.
- **exterior**: fora das contas: vota na hora local da cidade.

- Seções de 2026 com boletim (Brasil, sem exterior): 218.163; com voto conferido: 216.759; com relógio ou fuso inconsistente (sem encerramento): 30.
- Seções de 2022 (Brasil): 471.010; nas UFs completas de 2026: 198.542.

## 1. Quando a votação termina

Encerramento (2026, último voto, hora de Brasília):

| grupo | seções | mediana | p90 | p99 | % 17:30+ | % 18:00+ | % 19:00+ |
|---|---|---|---|---|---|---|---|
| Brasil | 214.297 | 17:07 | 18:11 | 19:30 | 25,6 | 13,2 | 2,5 |
| Norte | 43.768 | 17:08 | 18:13 | 19:38 | 27,2 | 13,9 | 2,9 |
| Nordeste | 105.340 | 17:13 | 18:27 | 19:41 | 35,4 | 19,4 | 3,9 |
| Centro-Oeste | 38.019 | 17:04 | 17:32 | 18:29 | 10,7 | 3,5 | 0,3 |
| Sudeste | 9.844 | 17:03 | 17:23 | 18:14 | 7,7 | 2,0 | 0,1 |
| Sul | 17.326 | 17:02 | 17:14 | 18:00 | 4,7 | 1,0 | 0,0 |

Recebimento no TSE, 2026:

| grupo | seções | mediana | p90 | p99 | % 17:30+ | % 18:00+ | % 19:00+ |
|---|---|---|---|---|---|---|---|
| Brasil | 214.327 | 18:40 | 20:17 | 21:27 | 97,0 | 80,6 | 37,0 |
| Norte | 43.769 | 18:31 | 20:02 | 21:56 | 93,4 | 72,1 | 31,3 |
| Nordeste | 105.340 | 18:59 | 20:47 | 21:35 | 98,7 | 88,2 | 49,0 |
| Centro-Oeste | 38.048 | 18:21 | 19:14 | 20:50 | 95,2 | 67,8 | 17,9 |
| Sudeste | 9.844 | 18:17 | 19:00 | 19:28 | 99,2 | 70,3 | 9,9 |
| Sul | 17.326 | 18:46 | 19:25 | 20:59 | 98,5 | 89,7 | 35,0 |

Recebimento no TSE, 2022 (mesmas UFs):

| grupo | seções | mediana | p90 | p99 | % 17:30+ | % 18:00+ | % 19:00+ |
|---|---|---|---|---|---|---|---|
| Brasil | 198.542 | 19:31 | 20:36 | 22:29 | 98,9 | 95,4 | 68,7 |
| Norte | 38.975 | 19:17 | 20:26 | 22:06 | 97,3 | 91,6 | 60,5 |
| Nordeste | 98.154 | 19:53 | 21:04 | 22:54 | 99,9 | 99,0 | 83,2 |
| Centro-Oeste | 35.932 | 18:50 | 20:00 | 20:47 | 97,3 | 88,4 | 42,4 |
| Sudeste | 9.239 | 18:37 | 19:16 | 20:01 | 99,7 | 93,3 | 20,3 |
| Sul | 16.242 | 19:41 | 20:20 | 21:00 | 99,9 | 99,9 | 87,2 |

Por UF (encerramento 2026 | recebimento 2026 | recebimento 2022, % depois das 18h e mediana):

| UF | completa | enc. % 18h+ | enc. mediana | rec. 2026 mediana | rec. 2022 mediana |
|---|---|---|---|---|---|
| AC | sim | 3,3 | 17:03 | 18:18 | 18:52 |
| AL | sim | 33,0 | 17:32 | 19:21 | 20:25 |
| AM | sim | 23,7 | 17:23 | 18:36 | 19:16 |
| AP | sim | 15,4 | 17:12 | 18:45 | 19:19 |
| BA | não | n/d | n/d | n/d | 20:01 |
| CE | sim | 18,5 | 17:13 | 19:12 | 19:54 |
| DF | sim | 1,9 | 17:06 | 17:47 | 18:11 |
| ES | sim | 2,0 | 17:03 | 18:17 | 18:37 |
| GO | sim | 3,7 | 17:03 | 18:38 | 19:10 |
| MA | sim | 17,9 | 17:11 | 19:01 | 20:16 |
| MG | não | n/d | n/d | n/d | 19:46 |
| MS | sim | 1,4 | 17:03 | 18:10 | 18:35 |
| MT | sim | 6,2 | 17:07 | 18:25 | 19:07 |
| PA | sim | 17,6 | 17:13 | 18:43 | 19:33 |
| PB | sim | 10,2 | 17:07 | 18:15 | 19:30 |
| PE | sim | 29,0 | 17:30 | 19:05 | 19:58 |
| PI | sim | 9,0 | 17:05 | 18:39 | 19:30 |
| PR | não | n/d | n/d | n/d | 19:04 |
| RJ | não | n/d | n/d | n/d | 20:00 |
| RN | sim | 21,6 | 17:17 | 18:54 | 19:32 |
| RO | sim | 0,3 | 17:04 | 18:19 | 19:10 |
| RR | sim | 1,2 | 17:04 | 18:40 | 19:14 |
| RS | não | 0,9 | 17:02 | 18:33 | 19:08 |
| SC | sim | 1,0 | 17:02 | 18:46 | 19:41 |
| SE | sim | 7,9 | 17:04 | 18:42 | 19:18 |
| SP | não | n/d | n/d | n/d | 19:35 |
| TO | sim | 2,4 | 17:04 | 17:55 | 18:40 |

Por tamanho (aptos da seção), UFs completas:

| faixa | seções 2026 | votantes médios | % enc. 18h+ | % das tardias | % rec. 19h+ 2026 | % rec. 19h+ 2022 |
|---|---|---|---|---|---|---|
| até 199 | 11.660 | 128,0 | 0,2 | 0,1 | 36,3 | 69,5 |
| 200 a 249 | 25.725 | 184,8 | 0,5 | 0,5 | 24,8 | 59,4 |
| 250 a 299 | 48.444 | 224,4 | 3,7 | 6,3 | 25,6 | 58,8 |
| 300 a 349 | 69.594 | 263,9 | 12,9 | 31,9 | 35,9 | 66,0 |
| 350 a 399 | 55.169 | 301,9 | 27,7 | 54,2 | 52,3 | 77,2 |
| 400 ou mais | 3.735 | 341,0 | 52,9 | 7,0 | 62,6 | 86,0 |

Por tipo de local inferido, UFs completas:

| tipo | seções 2026 | % enc. 18h+ | % das tardias | rec. 2026 mediana | rec. 2022 mediana |
|---|---|---|---|---|---|
| aldeia ou terra indígena | 1.189 | 24,2 | 1,0 | 18:42 | 19:48 |
| zona rural, assentamento ou quilombo | 34.278 | 17,7 | 21,5 | 19:02 | 19:59 |
| unidade prisional ou socioeducativa | 160 | 0,6 | 0,0 | 18:19 | 18:48 |
| escola fora de zona rural | 138.137 | 11,9 | 58,2 | 18:37 | 19:28 |
| outro local | 40.563 | 13,4 | 19,3 | 18:39 | 19:26 |

Tipo de local é inferência por palavra-chave no nome, bairro e endereço do local de votação, na ordem das regras: a primeira que casa decide. Escola num povoado conta como zona rural. Em 2022 o arquivo não tem bairro, só nome e endereço.

## 2. Persistência (régua de recebimento)

- Critério: cobertura de 2026 de ao menos 95% das seções principais e 3 seções ou mais nos dois anos. Municípios comparados: 2.770.
- Mediana das medianas municipais: 19:38 em 2022 e 18:41 em 2026.
- Correlação 2022 × 2026 da mediana municipal: Pearson 0,478, Spearman 0,541 (IC 95% 0,512 a 0,568); dentro da UF, Pearson 0,354 e Spearman 0,392.
- Décimo mais tardio nos dois anos (corte de 2022: 20:35; de 2026: 19:31): 77 municípios, contra 27,7 esperados por acaso (2,78 vezes).
- p90 de recebimento às 19h ou depois: 1.780 municípios em 2026, 2.546 em 2022, 1.754 nos dois. O corte de hora fixo quase não separa nada em 2022, quando o recebimento inteiro foi mais tarde; por isso a persistência usa o décimo de cada ano.

| UF | município | eleitorado | mediana 2022 | mediana 2026 | último voto (mediana) | transporte (mediana) | % rural |
|---|---|---|---|---|---|---|---|
| MA | JATOBÁ | 7.205 | 22:46 | 20:59 | 17:03 | 3h55 | 56 |
| AL | OURO BRANCO | 10.029 | 22:20 | 20:59 | 19:22 | 1h09 | 0 |
| MA | ÁGUA DOCE DO MARANHÃO | 11.520 | 22:03 | 21:00 | 17:08 | 3h07 | 81 |
| CE | PIRES FERREIRA | 8.610 | 21:30 | 22:28 | 17:10 | 5h18 | 0 |
| AL | MATRIZ DE CAMARAGIBE | 18.656 | 21:37 | 20:59 | 18:01 | 2h57 | 0 |
| CE | VARJOTA | 15.992 | 22:30 | 20:50 | 17:20 | 3h31 | 20 |
| CE | SENADOR SÁ | 7.038 | 21:50 | 20:55 | 18:13 | 2h40 | 44 |
| PI | TANQUE DO PIAUÍ | 2.725 | 21:57 | 20:52 | 17:03 | 3h50 | 50 |
| AL | SÃO MIGUEL DOS MILAGRES | 8.255 | 21:43 | 20:56 | 18:29 | 2h25 | 14 |
| MA | BARREIRINHAS | 52.533 | 21:53 | 20:51 | 17:10 | 2h59 | 66 |
| AL | PIRANHAS | 20.101 | 21:36 | 20:56 | 18:20 | 2h06 | 27 |
| MA | ALTO ALEGRE DO MARANHÃO | 18.076 | 21:56 | 20:51 | 17:36 | 2h35 | 12 |
| MA | LAGOA GRANDE DO MARANHÃO | 9.997 | 22:34 | 20:35 | 18:15 | 2h03 | 43 |
| CE | BARREIRA | 19.586 | 21:31 | 20:55 | 18:03 | 3h01 | 0 |
| AL | MESSIAS | 14.073 | 21:47 | 20:48 | 17:58 | 2h04 | 0 |
| AL | SÃO BRÁS | 7.353 | 21:22 | 20:57 | 17:20 | 3h36 | 56 |
| PA | SANTO ANTÔNIO DO TAUÁ | 26.159 | 21:44 | 20:46 | 18:03 | 2h17 | 58 |
| AL | PARIPUEIRA | 12.721 | 21:26 | 20:51 | 18:22 | 1h51 | 0 |
| PI | VILA NOVA DO PIAUÍ | 3.001 | 22:13 | 20:30 | 17:07 | 3h21 | 33 |
| PI | MARCOLÂNDIA | 8.736 | 23:50 | 20:09 | 17:04 | 3h05 | 12 |
| PI | CURRAIS | 6.287 | 21:56 | 20:18 | 17:11 | 2h00 | 64 |
| AL | GIRAU DO PONCIANO | 28.504 | 20:56 | 21:39 | 18:20 | 2h39 | 59 |
| PI | SÃO MIGUEL DA BAIXA GRANDE | 2.835 | 21:04 | 20:52 | 17:04 | 3h49 | 9 |
| CE | UBAJARA | 27.963 | 20:52 | 21:02 | 17:42 | 3h09 | 35 |
| MA | SANTO AMARO DO MARANHÃO | 13.330 | 20:55 | 20:54 | 17:56 | 2h04 | 71 |
| CE | HIDROLÂNDIA | 16.000 | 20:48 | 20:58 | 17:06 | 3h40 | 20 |
| AL | OLHO D'ÁGUA DO CASADO | 7.631 | 20:48 | 20:56 | 19:03 | 1h48 | 0 |
| GO | CORUMBAÍBA | 7.145 | 20:58 | 20:47 | 17:06 | 3h40 | 61 |
| CE | GROAÍRAS | 9.842 | 20:42 | 21:01 | 17:22 | 3h42 | 21 |
| AL | IGREJA NOVA | 17.729 | 20:43 | 20:59 | 17:35 | 1h38 | 58 |

Locais de votação casados entre os anos: 32.611; Spearman 0,535; persistentes 1.020 contra 326,1 esperados; 2.391 seções de 2026 dentro deles.

## 3. Encerramento tardio e voto

Bruta, por faixa de encerramento (% dos válidos, Brasil das UFs completas):

| faixa | seções | votantes | Lula | Flávio |
|---|---|---|---|---|
| até 17:00 | 0 | 0 | n/d | n/d |
| 17:00 a 17:30 | 158.394 | 37.452.795 | 45,95 | 46,70 |
| 17:30 a 18:00 | 26.525 | 7.431.217 | 54,74 | 39,00 |
| 18:00 a 19:00 | 22.662 | 6.564.156 | 59,46 | 35,05 |
| depois de 19:00 | 5.415 | 1.599.938 | 66,71 | 28,97 |

Inclinação (pontos por hora de atraso no encerramento):

- bruta, sem controle: Lula +10,22 (IC 95% de +9,41 a +11,06); Flávio −8,81 (IC 95% de −9,58 a −8,07).
- dentro da zona: Lula +2,16 (IC 95% de +1,99 a +2,36); Flávio −1,82 (IC 95% de −2,00 a −1,66).
- dentro da zona, com tamanho e tipo de local: Lula +2,76 (IC 95% de +2,58 a +2,95); Flávio −2,29 (IC 95% de −2,46 a −2,12).

Spearman seção a seção dentro da UF (hora de encerramento × % de Lula):

- GO: 0,212 (15.686 seções)
- ES: 0,202 (9.844 seções)
- MS: 0,177 (7.106 seções)
- RO: 0,138 (4.698 seções)
- PE: 0,134 (21.418 seções)
- PI: 0,130 (10.225 seções)
- PA: 0,116 (20.827 seções)
- SE: 0,114 (5.923 seções)
- TO: 0,107 (4.384 seções)
- MT: 0,102 (8.246 seções)
- AC: 0,085 (2.270 seções)
- SC: 0,077 (17.326 seções)
- AM: 0,062 (8.156 seções)
- AL: 0,034 (6.987 seções)
- RR: 0,032 (1.519 seções)
- RN: 0,004 (8.083 seções)
- CE: -0,022 (23.765 seções)
- MA: -0,023 (18.093 seções)
- PB: -0,047 (9.557 seções)
- DF: -0,113 (6.969 seções)
- AP: -0,120 (1.914 seções)

Estimador do modelo de urna (seção tardia menos as demais da zona):

- encerrou às 18h ou depois, contra as demais da mesma zona (2026; 2.047 unidades, 28.028 seções tardias): Lula, % dos válidos +3,28 (de +2,95 a +3,62); Flávio, % dos válidos (Bolsonaro em 2022) −2,76 (de −3,08 a −2,45); comparecimento, % dos aptos −0,50 (de −0,63 a −0,37); votantes por seção +39,74 (de +38,48 a +41,00); votantes por hora de urna aberta +0,68 (de +0,56 a +0,79); habilitados por ano de nascimento, % dos votantes +0,69 (de +0,58 a +0,81); sem biometria cadastrada, % dos votantes −0,18 (de −0,39 a +0,01).
- o mesmo, dentro da zona e da mesma faixa de eleitorado apto (2026; 3.503 unidades, 26.676 seções tardias): Lula, % dos válidos +4,16 (de +3,88 a +4,46); Flávio, % dos válidos (Bolsonaro em 2022) −3,50 (de −3,77 a −3,22); comparecimento, % dos aptos +0,14 (de +0,03 a +0,26); votantes por seção +5,77 (de +5,27 a +6,23); votantes por hora de urna aberta −2,45 (de −2,50 a −2,40); habilitados por ano de nascimento, % dos votantes +1,13 (de +1,03 a +1,25); sem biometria cadastrada, % dos votantes −0,29 (de −0,46 a −0,12).
- encerrou às 19h ou depois, contra as demais da mesma zona (2026; 1.148 unidades, 5.415 seções tardias): Lula, % dos válidos +4,77 (de +4,26 a +5,29); Flávio, % dos válidos (Bolsonaro em 2022) −3,97 (de −4,45 a −3,51); comparecimento, % dos aptos −0,94 (de −1,21 a −0,67); votantes por seção +41,66 (de +39,78 a +43,54); votantes por hora de urna aberta −0,82 (de −1,00 a −0,64); habilitados por ano de nascimento, % dos votantes +1,33 (de +0,95 a +1,77); sem biometria cadastrada, % dos votantes −0,69 (de −1,11 a −0,34).
- chegou ao TSE no décimo mais tardio de 2026, contra as demais da zona (2026; 1.150 unidades, 20.389 seções tardias): Lula, % dos válidos +3,69 (de +3,16 a +4,25); Flávio, % dos válidos (Bolsonaro em 2022) −3,15 (de −3,67 a −2,68); comparecimento, % dos aptos −0,29 (de −0,47 a −0,09); votantes por seção +19,28 (de +17,04 a +21,48).
- chegou ao TSE no décimo mais tardio de 2022, contra as demais da zona (2022; 1.007 unidades, 15.565 seções tardias): Lula, % dos válidos +3,79 (de +3,11 a +4,47); Flávio, % dos válidos (Bolsonaro em 2022) −3,15 (de −3,78 a −2,54); comparecimento, % dos aptos −0,64 (de −0,95 a −0,37); votantes por seção +19,27 (de +16,03 a +22,72).

### Conferência com a análise por seção

- Publicado em `secoes.json` (2026-10-05T16:58:37Z, 76.315 seções válidas): 1.199 seções depois das 19h, Lula +2,73 e Flávio −2,22 contra o resto da zona.
- Base atual, mesmas UFs completas da rodada publicada: 1.094 seções; fórmula da análise por seção +2,74; a mesma fórmula contra só as não tardias +3,11; estimador deste capítulo +4,74 (IC 95% de +3,49 a +6,06).
- Base atual, todas as UFs com boletim: 5.417 seções; fórmula da análise por seção +3,41; a mesma fórmula contra só as não tardias +3,81; estimador deste capítulo +4,74 (IC 95% de +4,25 a +5,28).

A análise por seção compara cada seção tardia com o resto da própria zona, inclusive as outras seções tardias, e pondera pelos válidos da seção. O estimador deste capítulo compara o agregado das seções tardias com o das demais na mesma zona, pondera pelos votantes das duas partes e deixa fora a zona sem os dois grupos. Os dois medem a mesma coisa por caminhos diferentes; a diferença entre eles é de método e de base, não de dado.

## Achados

### Achado contrário

- O atraso é, antes de tudo, tamanho de seção: com 400 aptos ou mais, 52,9% das seções encerraram às 18h ou depois; com até 199, 0,2%. Dentro da mesma zona, a seção com 350 votantes ou mais tem 50,6 pontos a mais de chance de fechar às 18h ou depois do que a de 200 a 249.
- Onde a eleição termina tarde nos dois anos, termina tarde mais por distância do que por fila: nos 77 municípios que ficaram entre os 10% mais tardios do país nos dois anos, a votação terminou, na mediana, às 17:36 e a mídia levou 2h25 até o TSE; no conjunto, 17:06 e 1h20. Dos 1.020 locais de votação na mesma situação, 71,5% ficam em zona rural, assentamento ou quilombo pelo nome e endereço, contra 34,4% dos locais comparados.
- A seção que chega tarde ao TSE vota mais em Lula do que o resto da própria zona nos dois anos, e por margem parecida: +3,8 pontos em 2022 e +3,7 em 2026 (décimo mais tardio de cada ano). O padrão não nasceu em 2026.

### Verificado

- Nas 21 UFs completas, metade das urnas encerrou a votação até as 17:07 de Brasília; 13,2% encerraram às 18h ou depois e 2,5% às 19h ou depois.
- Nenhuma urna encerrou antes das 17h de Brasília (0 seções nessa faixa), coerente com a regra: às 17h quem está na fila recebe senha e vota depois.
- O boletim chegou ao TSE, na mediana, às 18:40 em 2026 e às 19:31 em 2022, nas mesmas UFs; depois das 19h chegaram 37,0% das seções em 2026 e 68,7% em 2022.
- As UFs com maior parcela de seções encerradas às 18h ou depois: AL 33,0%; PE 29,0%; AM 23,7%; RN 21,6%; CE 18,5%; as de menor: RR 1,2%; SC 1,0%; RO 0,3%.
- A régua de chegada de 2026 tem um buraco: nenhum boletim registrado como recebido entre 19:32 e 19:59 (27,5 minutos) e 8.825 nos cinco minutos seguintes. É a pausa geral do TSE da noite; nesse trecho a hora de chegada mede o tribunal, não a seção. Em 2022, o maior buraco foi de 7,4 minutos. O corte do décimo mais tardio de 2026 (19:31) cai antes do buraco: quem ficou preso nele continua no décimo.
- Da hora de recebimento de 2026, a fila (17h até o último voto) responde por 7 min na mediana e o caminho da mídia até o TSE por 1h19.

### Inferido

- Sem controle, cada hora de atraso no encerramento vem com +10,22 pontos de Lula nos válidos. Dentro da mesma zona, +2,16 (IC 95% de +1,99 a +2,36); dentro da zona com tamanho e tipo de local, +2,76 (IC 95% de +2,58 a +2,95). Sobra 27,0% da correlação bruta.
- Seções que encerraram depois das 19h: +20,6 pontos de Lula sem controle, +4,9 dentro da zona e +5,4 com tamanho e tipo, contra as que encerraram entre 17:00 e 17:30.
- A seção tardia tem mais eleitor habilitado por ano de nascimento (biometria que não reconheceu): +0,69 ponto dentro da zona e +1,13 dentro da zona e da faixa de tamanho. Com o mesmo tamanho, ela processou 2,4 votantes por hora a menos: votação mais lenta, não só mais gente.
- O atraso persiste no lugar: a correlação de postos entre a mediana municipal de recebimento de 2022 e a de 2026 é 0,54 (IC 95% de 0,51 a 0,57), 0,39 dentro da UF; 77 municípios ficaram no décimo mais tardio nos dois anos, 2,8 vezes o esperado por acaso.

### Juízo editorial

- A providência barata é pôr fiscal de partido nas seções que historicamente fecham tarde: é ali que a fila depois das 17h, o mesário e a boca de urna ficam sem testemunha. A lei permite que um mesmo fiscal cubra mais de uma seção do mesmo local de votação (Lei 9.504, art. 65, § 1º); os 1.020 locais persistentes somam 2.391 seções.
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
