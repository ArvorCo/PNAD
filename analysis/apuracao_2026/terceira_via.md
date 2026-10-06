# Onde está o voto da terceira via, cidade por cidade

Bloco do capítulo 13 do dossiê da apuração do 1º turno de 2026. Pedido de 05/10/2026: onde está o voto de terceira via para a militância da direita trabalhar no 2º turno, com inteligência local, e como evitar que ele vire nulo. A casa tem lado; o método não: cada número tem regra e fonte, e o achado que contraria a tese sai com o mesmo peso.

Reprodução: `python3 scripts/apuracao-2026-terceira-via.py`, que grava `analysis/apuracao_2026/dados/terceira_via.json`. Banco da apuração, versão vigente de cada arquivo pela hora de geração do TSE; o arquivo municipal mais novo foi gerado em 2026-10-05T15:53:07.000Z. A soma dos 5.757 arquivos municipais (5.571 municípios e 186 cidades do exterior) bate com o arquivo nacional candidatura a candidatura: sim. Onze arquivos municipais que congelaram incompletos na noite foram regerados pelo TSE e entram completos aqui.

Rótulos: **Verificado** é número da urna. **Inferência** é conta sobre medição publicada. **Hipótese** é suposição declarada. **Analogia** é o que aconteceu em 2022. **Juízo editorial** é opinião da casa.

## Em seis linhas

1. **Verificado.** A terceira via teve 9,32 milhões de votos: 9,29 milhões de votos no Brasil e 30 mil votos no exterior. Cury 37,03%, Renan 28,72%, Caiado 28,00%, Zema 3,48%, demais 2,77%.
2. **Verificado.** 63,34% desse voto está em municípios onde Flávio venceu; 48,87% onde venceu com folga e 20,67% onde Lula venceu com folga.
3. **Inferência.** Pela matriz Nexus aplicada município a município, o estoque dá a Flávio saldo de 1,66 milhão de votos. Os 100 municípios prioritários guardam 4,40 milhões de votos e saldo de 809 mil votos, 36,36% da diferença do 1º turno (2,22 milhões de votos); a parte que a matriz manda para branco, nulo ou indecisão nesses 100 é de 1,38 milhão de votos.
4. **Verificado.** Em 3.663 municípios um nome do lado de Flávio (governador ou Senado) teve mais votos que ele, somando 7,06 milhões de votos acima dele; 54,85% desse vão está no Nordeste. Sem os governadores que não declararam apoio a Flávio, o vão é de 5,31 milhões de votos.
5. **Analogia.** Em 2022, pela razão simples, cada voto de terceira via do 1º turno rendeu a Bolsonaro saldo de 0,59 entre os turnos onde Flávio venceu com folga em 2026, e de 0,19 onde Lula venceu com folga. A regressão com efeito fixo de UF, que separa a mobilização da base, dá +0,15 e −0,12 (seção 6).
6. **Inferência.** O branco e nulo de presidente subiu 0,67 ponto entre os turnos de 2022 nas 12 UFs com 2º turno de governador e caiu 0,38 ponto nas outras 15. Em 2026 há 2º turno de governador em AC, AM, DF, ES, RJ, RN e TO: pela mesma taxa, 132 mil votos em risco de virar branco ou nulo; 49,54% dos votantes dessas UFs estão no Rio de Janeiro.

## Regras

- **Terceira via:** votos válidos de presidente fora de Flávio Bolsonaro e Lula, no município (1º turno de 04/10/2026).
- **Classe de margem:** folga é 10 pontos ou mais dos válidos, para um lado ou para o outro. É uma das variáveis, nunca filtro: o ranking cobre o país inteiro.
- **Matriz:** linha de cada candidatura (Nexus/BTG, 18 a 20/09/2026, p. 79; para Cury e Caiado, sensibilidade com Datafolha, BR-04029/2026, campo 15/09/2026 a 17/09/2026, p. 7) normalizada para somar 1 e aplicada aos votos de cada candidatura em cada município; só a parte medida vira voto válido. Hipótese declarada: a matriz é nacional e aplicada localmente, como se o eleitor de cada candidatura votasse igual em todo o país.
- **Vão local:** votos da candidatura do lado de Flávio com mais votos no município, entre o governador comparado com Flávio no vão estadual da casa (governadores.json) e as candidaturas do bloco aliado ao Senado (eleitas e a mais votada, senado_x_flavio.json), menos os votos de Flávio no mesmo município. Em pontos, sobre os votantes de presidente. Mesma urna, cargos diferentes: não é transferência.
- **Teto endereçável local:** votos de terceira via mais o vão local positivo. As duas parcelas podem contar o mesmo eleitor (quem votou no governador e em Cury), por isso é teto endereçável, não previsão nem soma de pessoas.
- **Fator de conversão (juízo editorial):** vão local 0,35, matriz por nome 0,25, ambiente de 2022 0,25, margem do 1º turno 0,15. Cada variável vira a posição do município entre os 5.571 (0 = o menor valor do país, 1 = o maior; empate leva a posição média; sem dado, 0,5). Prioridade = votos de terceira via × fator.

## 1. O estoque

| Classe | Municípios | Terceira via | Parcela | Saldo esperado (Nexus) |
| --- | ---: | ---: | ---: | ---: |
| Flávio venceu com folga | 2.430 | 4.538.562 | 48,87% | 764.326 |
| Flávio venceu apertado | 476 | 1.344.282 | 14,47% | 250.943 |
| Flávio perdeu apertado | 364 | 1.484.650 | 15,99% | 289.657 |
| Flávio perdeu com folga | 2.301 | 1.919.658 | 20,67% | 359.087 |

| Região | Terceira via | Parcela do país | Onde Flávio venceu | Renan + Zema | Caiado | Saldo por voto (Nexus) | Vão local positivo | Razão simples de 2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Norte | 631.871 | 6,80% | 63,38% | 29,39% | 21,83% | 0,184 | 404.369 | 0,485 |
| Nordeste | 1.811.095 | 19,50% | 4,65% | 30,81% | 21,54% | 0,190 | 3.874.584 | 0,193 |
| Centro-Oeste | 987.718 | 10,64% | 97,59% | 18,09% | 62,11% | 0,070 | 299.461 | 0,549 |
| Sudeste | 4.342.954 | 46,76% | 70,79% | 35,40% | 24,15% | 0,195 | 2.373.034 | 0,375 |
| Sul | 1.513.514 | 16,30% | 89,85% | 35,06% | 27,09% | 0,192 | 113.026 | 0,706 |

**Verificado.** As capitais guardam 27,94% do estoque; capitais e cidades com 200.000 eleitores ou mais (102 municípios), 47,63%.

## 2. Leitura por região

**Nordeste.** O Nordeste guarda 1,81 milhão de votos de terceira via, 19,50% do país, e Flávio venceu em municípios que somam só 4,65% desse estoque. Ali o estoque é menor e o vão é maior: em 1.382 municípios um nome do lado de Flávio teve mais votos que ele, somando 3,87 milhões de votos acima dele. Os maiores vãos são de governadores eleitos que não declararam apoio a Flávio, e por isso são teto, não palanque: Raquel Lyra (PE, governo: 1,07 milhão de votos) e Eduardo Braide (MA, governo: 864 mil votos). Sem eles, o vão cai para 2,26 milhões de votos, puxado por Angelo Coronel (BA, Senado: 479 mil votos), Ciro Nogueira (PI, Senado: 403 mil votos) e Styvenson Valentim (RN, Senado: 299 mil votos). Na Paraíba nenhum nome do bloco passou Flávio: o vão de Lucas Ribeiro é de um aliado de Lula. Em 2022, pela razão simples, cada voto de terceira via do Nordeste rendeu a Bolsonaro saldo de 0,19 entre os turnos, o menor das cinco regiões; a regressão com efeito fixo de UF (seção 6) dá menos, porque separa a mobilização da base.

**Sul.** No Sul o estoque é de 1,51 milhão de votos, e 89,85% dele está onde Flávio venceu. Renan e Zema somam 35,06% desse estoque, contra 32,20% no país. Pela matriz, cada voto rende 0,19 de saldo a Flávio; em 2022, pela razão simples, rendeu 0,71, o maior das cinco regiões (a regressão da seção 6 dá menos). A direita local quase não passa Flávio ali (113 mil votos acima dele).

**Centro-Oeste.** No Centro-Oeste o estoque é de 988 mil votos, 97,59% onde Flávio venceu, mas é de Caiado: 62,11% do estoque, e Renan e Zema somam só 18,09%. Em Goiás, com 472 mil votos de Caiado, a matriz Nexus dá saldo de 4.538 votos a Flávio e a do Datafolha, 103 mil votos. Em 2022, pela razão simples, o Centro-Oeste converteu 0,55 por voto de terceira via, o segundo maior das cinco regiões.

**Sudeste.** O Sudeste tem o maior volume: 4,34 milhões de votos, 46,76% do país, 70,79% onde Flávio venceu. A direita local passa Flávio em 1.449 municípios, com 2,37 milhões de votos acima dele; São Paulo responde por 1,57 milhão de votos e Minas por 763 mil votos; 97,25% do vão da região vem de Tarcísio e Cleitinho. Em 2022 cada voto de terceira via rendeu 0,38.

**Norte.** O Norte tem 632 mil votos de terceira via, 63,38% onde Flávio venceu, e a direita local passa Flávio em 234 municípios (404 mil votos acima dele). Em 2022 cada voto de terceira via rendeu 0,49 de saldo a Bolsonaro, com Lula quase sem ganho entre os turnos.

**Juízo editorial, o que fazer em cada região.**

- **Nordeste:** palanque local antes de militância de rua. O estoque é pequeno (1,81 milhão de votos) e converteu pouco em 2022 (0,19 por voto pela razão simples), mas o vão dos nomes do bloco (Angelo Coronel, Ciro Nogueira e Styvenson Valentim) mostra eleitor que vota na direita local e não vota em Flávio.
- **Sul:** militância sobre o eleitor de terceira via, com o maior rendimento de 2022 pela razão simples (0,71 por voto) e quase nenhum vão local a explorar.
- **Centro-Oeste:** o eleitor de Caiado decide. Antes de gastar ali, medir a linha dele em Goiás: as duas medições nacionais discordam de lado.
- **Sudeste:** o volume está ali (4,34 milhões de votos), e a conversão depende de Tarcísio e Cleitinho subirem no palanque nas cidades grandes.
- **Norte:** estoque pequeno (632 mil votos) com rendimento alto em 2022 pela razão simples (0,49 por voto), concentrado em poucas cidades: Manaus, Belém e Ananindeua lideram o índice da região.

## 3. Os 100 municípios prioritários

**Juízo editorial.** Pesos do fator: vão local 0,35, matriz por nome 0,25, ambiente de 2022 0,25, margem do 1º turno 0,15. O vão local pesa mais porque é a única evidência medida no próprio município de que há eleitor que vota na direita e não vota em Flávio.

**Inferência.** Os 100 somam 4,40 milhões de votos de terceira via (47,34% do país), saldo esperado de 809 mil votos pela Nexus e de 1,03 milhão de votos com as linhas do Datafolha para Cury e Caiado. Por região: Norte 7, Nordeste 14, Centro-Oeste 6, Sudeste 55, Sul 18. Por classe: 57 onde Flávio venceu com folga, 17 apertado, 13 onde perdeu apertado e 13 onde perdeu com folga. 26 são capitais.

| Nº | Município | Eleitores | Terceira via | Renan / Zema / Cury / Caiado / outros | Margem de Flávio (pp) | Bolsonaro 2022, 2º t. | Nulo 2022, 1º→2º (pp) | Saldo esperado (Nexus) | Direita local acima de Flávio | Fator |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| 1 | São Paulo (SP) | 9.145.124 | 739.724 | 249.725 / 33.563 / 249.496 / 177.516 / 29.424 | −4,5 | 46,5% | +0,73 | +148.122 | Tarcísio (+472.949) | 0,598 |
| 2 | Rio de Janeiro (RJ) | 4.952.612 | 285.003 | 88.676 / 10.354 / 90.700 / 82.424 / 12.849 | +4,0 | 52,7% | −0,33 | +50.386 | nenhum acima de Flávio | 0,399 |
| 3 | Brasília (DF) | 2.258.320 | 187.565 | 46.714 / 4.915 / 45.979 / 85.076 / 4.881 | +13,2 | 58,8% | +0,54 | +24.262 | Michelle Bolsonaro (+28.880) | 0,444 |
| 4 | Belo Horizonte (MG) | 1.966.966 | 147.491 | 39.081 / 17.464 / 52.809 / 33.055 / 5.082 | +6,9 | 54,2% | −0,31 | +30.156 | nenhum acima de Flávio | 0,490 |
| 5 | Curitiba (PR) | 1.415.148 | 132.614 | 43.451 / 5.676 / 43.236 / 36.171 / 4.080 | +27,1 | 64,8% | +0,44 | +25.901 | nenhum acima de Flávio | 0,541 |
| 6 | Goiânia (GO) | 1.019.261 | 135.268 | 13.738 / 840 / 12.391 / 106.965 / 1.334 | +26,5 | 64,0% | +0,29 | +1.729 | Daniel Vilela (+907) | 0,451 |
| 7 | Fortaleza (CE) | 1.795.713 | 107.121 | 37.754 / 2.329 / 44.901 / 18.680 / 3.457 | −14,1 | 41,8% | +0,32 | +23.020 | Capitão Wagner (+30.114) | 0,530 |
| 8 | Manaus (AM) | 1.477.265 | 101.648 | 25.155 / 1.488 / 53.684 / 18.082 / 3.239 | +17,1 | 61,3% | +1,81 | +18.404 | nenhum acima de Flávio | 0,498 |
| 9 | Guarulhos (SP) | 948.908 | 75.393 | 25.059 / 2.129 / 29.230 / 16.304 / 2.671 | +9,0 | 53,7% | +0,11 | +15.137 | Tarcísio (+43.187) | 0,633 |
| 10 | Salvador (BA) | 1.955.479 | 111.468 | 29.219 / 2.052 / 40.676 / 36.320 / 3.201 | −38,2 | 29,3% | +1,16 | +17.333 | Angelo Coronel (+110.448) | 0,398 |
| 11 | Campinas (SP) | 873.613 | 61.515 | 20.543 / 3.399 / 21.080 / 13.896 / 2.597 | +13,9 | 56,2% | +0,54 | +12.484 | Tarcísio (+37.388) | 0,657 |
| 12 | Porto Alegre (RS) | 1.064.200 | 74.386 | 24.187 / 4.014 / 23.061 / 20.069 / 3.055 | −6,7 | 46,5% | +1,37 | +14.259 | Marcel Van Hattem (+6.645) | 0,486 |
| 13 | Belém (PA) | 1.048.781 | 68.271 | 21.476 / 1.131 / 28.127 / 14.850 / 2.687 | −4,3 | 49,7% | +0,32 | +12.938 | Dr. Daniel (+14.445) | 0,506 |
| 14 | São Bernardo do Campo (SP) | 626.647 | 52.441 | 18.211 / 1.933 / 20.524 / 9.815 / 1.958 | −4,9 | 46,2% | +0,60 | +11.142 | Tarcísio (+34.004) | 0,624 |
| 15 | Recife (PE) | 1.230.407 | 62.322 | 17.723 / 2.270 / 25.167 / 15.487 / 1.675 | −16,9 | 43,7% | +1,33 | +11.499 | Raquel Lyra (+60.033) | 0,522 |
| 16 | São José dos Campos (SP) | 540.217 | 42.545 | 14.299 / 2.564 / 15.476 / 8.645 / 1.561 | +24,8 | 62,6% | +0,78 | +9.098 | Tarcísio (+32.289) | 0,752 |
| 17 | São Luís (MA) | 761.443 | 52.471 | 14.793 / 1.019 / 21.153 / 13.405 / 2.101 | −17,5 | 39,6% | −0,12 | +8.979 | Eduardo Braide (+238.381) | 0,602 |
| 18 | Santo André (SP) | 573.503 | 47.873 | 16.436 / 1.835 / 17.802 / 10.051 / 1.749 | +6,0 | 52,1% | +0,74 | +9.940 | Tarcísio (+29.388) | 0,651 |
| 19 | Sorocaba (SP) | 531.342 | 41.856 | 14.567 / 1.613 / 15.819 / 8.358 / 1.499 | +23,7 | 61,1% | +0,24 | +8.852 | Tarcísio (+21.167) | 0,708 |
| 20 | Osasco (SP) | 583.991 | 47.253 | 16.086 / 1.627 / 17.295 / 10.481 / 1.764 | +2,1 | 49,6% | +0,46 | +9.608 | Tarcísio (+26.577) | 0,615 |
| 21 | Joinville (SC) | 443.225 | 33.641 | 13.253 / 2.690 / 10.874 / 5.809 / 1.015 | +49,1 | 76,6% | +0,03 | +8.394 | Jorginho Mello (+11.219) | 0,793 |
| 22 | Campo Grande (MS) | 641.185 | 44.160 | 14.315 / 1.385 / 16.454 / 10.578 / 1.428 | +26,3 | 62,6% | +1,45 | +8.729 | nenhum acima de Flávio | 0,592 |
| 23 | Ribeirão Preto (SP) | 473.134 | 36.766 | 10.657 / 2.065 / 14.498 / 8.426 / 1.120 | +21,3 | 59,6% | +0,25 | +7.136 | Tarcísio (+22.953) | 0,674 |
| 24 | Aparecida de Goiânia (GO) | 341.263 | 46.159 | 4.264 / 173 / 4.258 / 37.105 / 359 | +19,0 | 57,9% | −0,41 | +338 | Daniel Vilela (+25.435) | 0,529 |
| 25 | Maceió (AL) | 646.463 | 32.477 | 10.043 / 625 / 13.769 / 6.691 / 1.349 | +11,3 | 57,2% | +1,72 | +6.276 | Marina JHC (+68.501) | 0,696 |
| 26 | Jundiaí (SP) | 337.851 | 29.388 | 9.927 / 1.484 / 10.851 / 6.191 / 935 | +27,5 | 63,7% | +0,66 | +6.227 | Tarcísio (+18.742) | 0,755 |
| 27 | Florianópolis (SC) | 423.969 | 34.435 | 12.075 / 2.240 / 12.129 / 6.341 / 1.650 | +7,8 | 53,3% | +0,68 | +7.480 | Jorginho Mello (+9.110) | 0,614 |
| 28 | Contagem (MG) | 463.466 | 37.047 | 9.893 / 3.767 / 14.664 / 7.692 / 1.031 | +11,0 | 55,5% | −0,62 | +7.683 | nenhum acima de Flávio | 0,538 |
| 29 | Uberlândia (MG) | 540.033 | 39.249 | 10.535 / 3.921 / 11.754 / 12.145 / 894 | +10,5 | 53,1% | −0,38 | +7.463 | nenhum acima de Flávio | 0,499 |
| 30 | Santos (SP) | 348.832 | 28.191 | 9.666 / 1.206 / 9.289 / 6.939 / 1.091 | +10,7 | 56,2% | +1,14 | +5.671 | Tarcísio (+22.226) | 0,681 |
| 31 | São Gonçalo (RJ) | 653.184 | 34.139 | 10.184 / 754 / 12.679 / 9.204 / 1.318 | +12,0 | 55,4% | −0,64 | +6.031 | Douglas Ruas (+16.881) | 0,538 |
| 32 | Caxias do Sul (RS) | 342.998 | 27.774 | 8.846 / 1.181 / 9.857 / 7.161 / 729 | +35,8 | 66,4% | +0,41 | +5.480 | Zucco (+2.120) | 0,655 |
| 33 | Natal (RN) | 573.148 | 29.848 | 9.578 / 681 / 13.267 / 5.253 / 1.069 | −4,8 | 47,0% | −0,46 | +6.047 | Styvenson Valentim (+27.599) | 0,597 |
| 34 | Ananindeua (PA) | 358.249 | 25.122 | 8.201 / 279 / 10.901 / 4.868 / 873 | +1,2 | 50,3% | +0,10 | +5.014 | Dr. Daniel (+58.018) | 0,698 |
| 35 | Mogi das Cruzes (SP) | 334.039 | 27.343 | 8.987 / 1.041 / 9.566 / 6.751 / 998 | +15,0 | 56,8% | +0,45 | +5.346 | Tarcísio (+11.547) | 0,624 |
| 36 | Londrina (PR) | 394.978 | 31.887 | 8.534 / 1.352 / 11.533 / 9.466 / 1.002 | +41,0 | 72,9% | −0,09 | +5.396 | nenhum acima de Flávio | 0,530 |
| 37 | São José do Rio Preto (SP) | 344.760 | 22.968 | 7.027 / 1.012 / 8.735 / 5.606 / 588 | +34,1 | 67,9% | +0,36 | +4.504 | Tarcísio (+14.153) | 0,725 |
| 38 | Blumenau (SC) | 269.370 | 21.753 | 8.687 / 1.403 / 6.936 / 4.087 / 640 | +48,0 | 75,3% | −0,23 | +5.294 | Jorginho Mello (+2.222) | 0,760 |
| 39 | Macapá (AP) | 321.597 | 25.161 | 7.001 / 246 / 11.656 / 5.510 / 748 | +3,9 | 54,9% | +0,30 | +4.550 | Dr. Furlan (+43.732) | 0,655 |
| 40 | João Pessoa (PB) | 591.750 | 36.861 | 11.025 / 725 / 17.814 / 6.042 / 1.255 | −0,8 | 49,9% | +1,40 | +7.316 | nenhum acima de Flávio | 0,437 |
| 41 | Cuiabá (MT) | 456.517 | 29.772 | 8.103 / 860 / 10.898 / 8.377 / 1.534 | +23,6 | 61,5% | −0,07 | +5.212 | nenhum acima de Flávio | 0,523 |
| 42 | Barueri (SP) | 298.024 | 23.009 | 8.134 / 847 / 8.543 / 4.741 / 744 | +7,8 | 51,7% | +0,40 | +4.921 | Tarcísio (+17.949) | 0,674 |
| 43 | Nova Iguaçu (RJ) | 614.931 | 30.898 | 9.582 / 750 / 11.239 / 8.070 / 1.257 | +25,8 | 63,0% | −0,91 | +5.602 | nenhum acima de Flávio | 0,497 |
| 44 | Piracicaba (SP) | 311.212 | 20.562 | 6.887 / 917 / 7.284 / 4.802 / 672 | +35,8 | 67,9% | +0,15 | +4.195 | Tarcísio (+10.662) | 0,732 |
| 45 | Taubaté (SP) | 239.956 | 19.427 | 6.170 / 969 / 6.569 / 5.173 / 546 | +31,4 | 66,2% | +0,38 | +3.801 | Tarcísio (+16.199) | 0,751 |
| 46 | Duque de Caxias (RJ) | 634.694 | 34.032 | 10.367 / 687 / 12.012 / 9.479 / 1.487 | +18,6 | 58,3% | −0,72 | +5.931 | nenhum acima de Flávio | 0,422 |
| 47 | Mauá (SP) | 310.407 | 24.701 | 8.487 / 572 / 9.634 / 4.921 / 1.087 | −2,8 | 46,8% | +0,07 | +4.940 | Tarcísio (+12.340) | 0,578 |
| 48 | Teresina (PI) | 592.974 | 35.650 | 11.415 / 702 / 15.152 / 7.238 / 1.143 | −29,7 | 33,6% | +0,27 | +7.095 | nenhum acima de Flávio | 0,399 |
| 49 | Anápolis (GO) | 288.292 | 32.483 | 3.858 / 171 / 3.370 / 24.777 / 307 | +41,2 | 70,6% | −0,28 | +785 | nenhum acima de Flávio | 0,435 |
| 50 | Vila Velha (ES) | 347.987 | 24.247 | 8.260 / 1.001 / 8.988 / 5.226 / 772 | +19,9 | 60,9% | +0,91 | +5.133 | nenhum acima de Flávio | 0,579 |
| 51 | Maringá (PR) | 302.812 | 23.394 | 7.637 / 891 / 8.540 / 5.715 / 611 | +36,4 | 67,7% | +0,39 | +4.709 | nenhum acima de Flávio | 0,599 |
| 52 | Diadema (SP) | 331.016 | 24.139 | 8.356 / 641 / 9.413 / 4.784 / 945 | −14,9 | 40,0% | +0,11 | +4.943 | Tarcísio (+17.562) | 0,580 |
| 53 | Jaboatão dos Guararapes (PE) | 498.555 | 24.534 | 7.132 / 482 / 11.040 / 5.317 / 563 | −14,1 | 44,2% | +1,21 | +4.677 | Raquel Lyra (+30.909) | 0,568 |
| 54 | Betim (MG) | 301.594 | 23.363 | 6.754 / 2.026 / 9.937 / 4.036 / 610 | +7,5 | 52,4% | −0,95 | +5.121 | Cleitinho Azevedo (+2.838) | 0,592 |
| 55 | Serra (ES) | 361.737 | 23.477 | 8.234 / 755 / 9.305 / 4.498 / 685 | +7,1 | 53,1% | +0,71 | +5.124 | Lorenzo Pazolini (+782) | 0,582 |
| 56 | Porto Velho (RO) | 367.902 | 25.457 | 7.770 / 442 / 10.270 / 6.087 / 888 | +27,6 | 64,6% | +0,80 | +4.740 | nenhum acima de Flávio | 0,530 |
| 57 | Franca (SP) | 241.902 | 17.786 | 5.445 / 1.129 / 6.394 / 4.400 / 418 | +30,1 | 63,9% | +0,21 | +3.602 | Tarcísio (+11.804) | 0,732 |
| 58 | Juiz de Fora (MG) | 395.457 | 27.174 | 7.846 / 2.530 / 10.517 / 5.276 / 1.005 | −8,0 | 43,9% | −0,15 | +5.714 | nenhum acima de Flávio | 0,477 |
| 59 | Bauru (SP) | 278.336 | 19.289 | 6.000 / 702 / 6.828 / 5.107 / 652 | +24,1 | 61,0% | +0,21 | +3.603 | Tarcísio (+10.475) | 0,648 |
| 60 | Vitória (ES) | 267.102 | 18.794 | 6.204 / 1.114 / 6.426 / 4.389 / 661 | +7,9 | 54,7% | +1,30 | +3.891 | Lorenzo Pazolini (+11.550) | 0,646 |
| 61 | Carapicuíba (SP) | 290.495 | 21.115 | 6.928 / 528 / 7.858 / 5.068 / 733 | −3,0 | 46,5% | +0,05 | +4.089 | Tarcísio (+13.425) | 0,575 |
| 62 | Indaiatuba (SP) | 192.534 | 15.560 | 5.202 / 740 / 5.980 / 3.170 / 468 | +31,1 | 64,2% | +0,43 | +3.327 | Tarcísio (+10.365) | 0,763 |
| 63 | Canoas (RS) | 253.142 | 19.615 | 6.870 / 715 / 7.134 / 4.280 / 616 | +13,1 | 54,9% | +0,82 | +4.147 | Zucco (+1.146) | 0,591 |
| 64 | Praia Grande (SP) | 265.311 | 17.332 | 6.035 / 454 / 6.066 / 4.122 / 655 | +17,8 | 58,3% | +0,38 | +3.460 | Tarcísio (+10.254) | 0,661 |
| 65 | São Caetano do Sul (SP) | 147.744 | 14.650 | 5.168 / 811 / 4.890 / 3.322 / 459 | +20,4 | 60,1% | +1,72 | +3.153 | Tarcísio (+12.121) | 0,756 |
| 66 | São Vicente (SP) | 256.025 | 17.229 | 6.011 / 449 / 6.044 / 4.042 / 683 | +7,7 | 54,1% | +0,34 | +3.453 | Tarcísio (+10.817) | 0,633 |
| 67 | Itaquaquecetuba (SP) | 258.019 | 17.951 | 5.986 / 347 / 7.259 / 3.768 / 591 | −2,0 | 46,7% | −0,35 | +3.605 | Tarcísio (+13.644) | 0,606 |
| 68 | Suzano (SP) | 235.588 | 17.796 | 6.178 / 469 / 6.509 / 3.903 / 737 | +8,9 | 53,2% | +0,02 | +3.596 | Tarcísio (+7.867) | 0,611 |
| 69 | Niterói (RJ) | 412.252 | 25.308 | 7.859 / 1.280 / 8.218 / 6.877 / 1.074 | −4,6 | 48,8% | +0,54 | +4.684 | nenhum acima de Flávio | 0,427 |
| 70 | Ponta Grossa (PR) | 258.390 | 24.348 | 6.377 / 528 / 8.620 / 8.287 / 536 | +31,1 | 65,1% | −0,31 | +3.846 | nenhum acima de Flávio | 0,441 |
| 71 | São José (SC) | 195.574 | 15.576 | 5.780 / 758 / 5.779 / 2.730 / 529 | +28,0 | 63,2% | −0,16 | +3.561 | Jorginho Mello (+1.370) | 0,686 |
| 72 | Taboão da Serra (SP) | 212.014 | 17.963 | 5.895 / 548 / 6.918 / 3.959 / 643 | −10,5 | 41,6% | +0,15 | +3.570 | Tarcísio (+14.551) | 0,588 |
| 73 | Cotia (SP) | 194.159 | 16.961 | 5.766 / 610 / 6.247 / 3.731 / 607 | +4,4 | 49,1% | +0,63 | +3.479 | Tarcísio (+8.195) | 0,614 |
| 74 | Limeira (SP) | 219.483 | 13.567 | 4.732 / 519 / 4.950 / 2.948 / 418 | +46,5 | 73,5% | +0,19 | +2.861 | Tarcísio (+7.206) | 0,765 |
| 75 | Boa Vista (RR) | 241.509 | 14.422 | 5.077 / 255 / 6.075 / 2.530 / 485 | +54,1 | 79,5% | −0,10 | +3.140 | nenhum acima de Flávio | 0,716 |
| 76 | Uberaba (MG) | 236.838 | 18.247 | 4.740 / 2.073 / 5.850 / 5.218 / 366 | +12,5 | 54,0% | −0,53 | +3.581 | Cleitinho Azevedo (+2.572) | 0,561 |
| 77 | Guarujá (SP) | 238.913 | 16.887 | 5.078 / 428 / 6.967 / 3.791 / 623 | +13,6 | 56,6% | +0,48 | +3.168 | Tarcísio (+8.796) | 0,606 |
| 78 | São José dos Pinhais (PR) | 227.539 | 19.120 | 6.222 / 526 / 6.687 / 5.163 / 522 | +32,6 | 66,2% | −0,61 | +3.683 | nenhum acima de Flávio | 0,529 |
| 79 | Montes Claros (MG) | 283.875 | 18.087 | 4.267 / 1.809 / 8.142 / 3.477 / 392 | +6,7 | 51,2% | −0,43 | +3.660 | Cleitinho Azevedo (+3.484) | 0,556 |
| 80 | Aracaju (SE) | 422.179 | 28.938 | 7.431 / 567 / 12.086 / 7.916 / 938 | −16,8 | 42,7% | +0,94 | +4.755 | nenhum acima de Flávio | 0,347 |
| 81 | Cascavel (PR) | 239.954 | 16.209 | 5.823 / 537 / 5.583 / 3.880 / 386 | +37,2 | 66,9% | −0,41 | +3.452 | nenhum acima de Flávio | 0,610 |
| 82 | Feira de Santana (BA) | 435.631 | 24.032 | 5.720 / 408 / 9.356 / 7.997 / 551 | −21,3 | 36,0% | +0,93 | +3.565 | Angelo Coronel (+20.581) | 0,404 |
| 83 | Itajaí (SC) | 183.857 | 11.995 | 4.651 / 535 / 4.356 / 2.080 / 373 | +45,5 | 73,0% | −0,27 | +2.819 | Jorginho Mello (+6.907) | 0,805 |
| 84 | Americana (SP) | 181.216 | 11.967 | 3.959 / 582 / 4.763 / 2.331 / 332 | +35,9 | 67,3% | +0,44 | +2.569 | Tarcísio (+7.213) | 0,762 |
| 85 | Divinópolis (MG) | 171.705 | 11.518 | 3.219 / 1.277 / 4.568 / 2.214 / 240 | +16,7 | 55,6% | −0,84 | +2.546 | Cleitinho Azevedo (+22.720) | 0,774 |
| 86 | Pelotas (RS) | 244.459 | 19.890 | 6.035 / 552 / 7.244 / 5.418 / 641 | −5,0 | 43,8% | +1,16 | +3.592 | Zucco (+2.222) | 0,446 |
| 87 | Embu das Artes (SP) | 206.389 | 15.370 | 4.964 / 400 / 6.171 / 3.288 / 547 | −8,4 | 42,8% | −0,28 | +3.057 | Tarcísio (+10.704) | 0,576 |
| 88 | Jacareí (SP) | 171.394 | 12.371 | 4.092 / 529 / 4.424 / 2.830 / 496 | +26,0 | 62,6% | +0,61 | +2.465 | Tarcísio (+8.582) | 0,711 |
| 89 | Rio Branco (AC) | 270.174 | 18.536 | 4.808 / 359 / 7.747 / 5.143 / 479 | +36,5 | 72,5% | −0,36 | +3.117 | nenhum acima de Flávio | 0,468 |
| 90 | Cariacica (ES) | 274.339 | 17.046 | 5.701 / 463 / 6.632 / 3.755 / 495 | +12,0 | 56,4% | +0,84 | +3.507 | nenhum acima de Flávio | 0,503 |
| 91 | Palhoça (SC) | 154.633 | 11.853 | 4.644 / 450 / 4.464 / 1.950 / 345 | +34,6 | 65,7% | −0,53 | +2.795 | Jorginho Mello (+1.771) | 0,720 |
| 92 | Petrópolis (RJ) | 239.569 | 18.060 | 4.978 / 719 / 6.711 / 5.028 / 624 | +22,3 | 62,2% | −0,14 | +3.153 | nenhum acima de Flávio | 0,471 |
| 93 | Caruaru (PE) | 255.270 | 13.260 | 3.713 / 212 / 5.966 / 3.126 / 243 | −13,1 | 42,3% | +0,95 | +2.447 | Raquel Lyra (+63.810) | 0,640 |
| 94 | Gravataí (RS) | 192.077 | 14.762 | 4.627 / 426 / 5.495 / 3.797 / 417 | +22,3 | 60,2% | +0,38 | +2.822 | nenhum acima de Flávio | 0,573 |
| 95 | Sumaré (SP) | 199.975 | 12.256 | 4.322 / 432 / 4.787 / 2.302 / 413 | +19,4 | 57,3% | +0,03 | +2.662 | Tarcísio (+7.615) | 0,690 |
| 96 | Campos dos Goytacazes (RJ) | 370.466 | 20.200 | 4.913 / 486 / 7.900 / 6.170 / 731 | +25,6 | 63,1% | −0,71 | +3.098 | nenhum acima de Flávio | 0,415 |
| 97 | Ribeirão das Neves (MG) | 218.584 | 15.424 | 4.072 / 1.221 / 6.600 / 3.112 / 419 | +2,6 | 49,4% | −1,57 | +3.106 | Cleitinho Azevedo (+2.619) | 0,541 |
| 98 | Petrolina (PE) | 249.120 | 13.681 | 4.200 / 204 / 6.807 / 2.248 / 222 | −27,4 | 32,4% | +1,89 | +2.840 | Raquel Lyra (+26.935) | 0,601 |
| 99 | Olinda (PE) | 301.943 | 14.839 | 4.301 / 329 / 6.235 / 3.627 / 347 | −20,6 | 41,2% | +1,34 | +2.753 | Raquel Lyra (+21.858) | 0,543 |
| 100 | Novo Hamburgo (RS) | 174.486 | 11.437 | 4.011 / 539 / 3.962 / 2.617 / 308 | +36,4 | 68,5% | +0,46 | +2.451 | Zucco (+1.259) | 0,703 |

**Sensibilidade.** O que muda sem os pesos da casa:

| Ordem | Em comum com a central | Norte | Nordeste | Centro-Oeste | Sudeste | Sul | Saldo esperado dos 100 | Primeiros |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| só volume | 92 | 8 | 14 | 9 | 54 | 15 | 803.052 | São Paulo (SP), Rio de Janeiro (RJ), Brasília (DF), Belo Horizonte (MG), Goiânia (GO) |
| só vão local | 81 | 4 | 20 | 9 | 57 | 10 | 766.673 | São Paulo (SP), Brasília (DF), Salvador (BA), São Luís (MA), Goiânia (GO) |
| só margem | 89 | 8 | 10 | 9 | 51 | 22 | 796.899 | São Paulo (SP), Rio de Janeiro (RJ), Brasília (DF), Goiânia (GO), Curitiba (PR) |

Os 10 primeiros de cada UF pelo índice e os 10 de maior teto endereçável estão em `terceira_via.json` (`prioridade.por_uf`, `teto.ufs`).

## 4. Riscos e achado contrário

**Juízo editorial.** 47,63% do estoque está em capitais e cidades grandes, onde a militância de rua rende menos por hora e a mídia e as redes rendem mais.

**Analogia, achado contrário.** Onde Lula venceu com folga ficam 1,92 milhão de votos (20,67% do estoque). Pela matriz nacional, ali cada voto rende quase o mesmo que no país (0,187 contra 0,179), porque a matriz não sabe onde o eleitor mora. A urna de 2022 sabe: nesses municípios, cada voto de terceira via rendeu saldo de 0,188 a Bolsonaro, contra 0,589 onde Flávio venceu com folga. O trabalho ali rende menos por voto. Nas capitais do Nordeste, Lula fez +17,86 pontos sobre Flávio; a terceira via soma 497 mil votos, com 117 mil votos de Caiado, cuja linha Nexus dá mais a Lula (30 contra 36). Em Goiás, Caiado é 80,41% do estoque: pela Nexus o saldo do estado fica perto de zero.

## 5. O risco do voto nulo, medido em 2022

**Verificado.** Entre os turnos de 2022, branco e nulo de presidente foram de 4,41% para 4,59% dos votantes (+0,18 ponto; 247.790 votos a mais). A terceira via de 2022 tinha 9,86 milhões de votos: o branco e nulo novo equivale a 2,5% dela. Fonte: detalhe por seção do TSE, conferido com o arquivo nacional: sim.

**Inferência.** O aumento se concentrou onde havia 2º turno de governador: +0,67 ponto nas 12 UFs (AL, AM, BA, ES, MS, PB, PE, RO, RS, SC, SE e SP) e −0,38 nas outras 15. Controlando pela terceira via, o 2º turno estadual soma 1,03 ponto ao aumento; cada ponto de terceira via em 2022, 0,022. Sem 2º turno estadual, o branco e nulo caiu mais onde a terceira via era pequena e caiu menos onde era grande (do quinto menor ao maior: −0,77, −0,60, −0,49, −0,49, −0,24).

**Hipótese.** O eleitor que volta à urna pelo governador e não escolhe presidente explica a diferença. Em 2026 há 2º turno estadual em AC, AM, DF, ES, RJ, RN e TO, com 19,90 milhões de votantes; pela taxa de 2022, 132 mil votos em risco de branco ou nulo. A matriz Nexus manda 2,89 milhões de votos da terceira via para branco, nulo ou indecisão; a urna de 2022 mostra que boa parte disso escolhe ou falta.

Municípios com 20 mil votantes ou mais onde o branco e nulo mais cresceu em 2022:

| Município | 1º turno | 2º turno | Variação (pp) | Terceira via 2022 | 2º turno de governador em 2022 | Terceira via 2026 |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| Tabatinga (AM) | 2,14% | 5,89% | +3,75 | 6,04% | sim | 1.285 |
| Pesqueira (PE) | 4,14% | 7,48% | +3,33 | 3,32% | sim | 1.515 |
| Atalaia (AL) | 4,43% | 7,68% | +3,26 | 7,10% | sim | 952 |
| Santana do Ipanema (AL) | 3,72% | 6,92% | +3,20 | 6,30% | sim | 1.233 |
| Autazes (AM) | 2,28% | 5,16% | +2,87 | 4,50% | sim | 1.117 |
| Manacapuru (AM) | 1,96% | 4,76% | +2,80 | 5,25% | sim | 3.083 |
| Coari (AM) | 1,84% | 4,64% | +2,80 | 5,45% | sim | 1.476 |
| Iranduba (AM) | 2,04% | 4,82% | +2,78 | 6,49% | sim | 2.214 |
| Girau do Ponciano (AL) | 3,95% | 6,70% | +2,74 | 5,59% | sim | 657 |
| Araripina (PE) | 5,02% | 7,71% | +2,69 | 4,84% | sim | 2.295 |
| Tefé (AM) | 1,75% | 4,37% | +2,62 | 4,59% | sim | 1.654 |
| União dos Palmares (AL) | 4,12% | 6,63% | +2,51 | 6,21% | sim | 1.398 |
| Itacoatiara (AM) | 1,65% | 4,12% | +2,46 | 6,57% | sim | 3.250 |
| Teotônio Vilela (AL) | 5,24% | 7,66% | +2,42 | 6,53% | sim | 1.047 |
| Pilar (AL) | 4,84% | 7,11% | +2,27 | 7,86% | sim | 996 |

**Analogia.** A terceira via de 2022 era outra (Simone Tebet e Ciro Gomes). O acervo da casa (`data/originals/pesquisas_2022/`) só tem as últimas ondas de 1º turno; não há pesquisa de 2º turno de 2022 com o cruzamento pelo voto em Tebet ou Ciro, e não usamos nenhuma.

## 6. Pesquisa contra urna: duas réguas para o mesmo estoque

**Régua da urna de 2022.** Regressão ecológica município a município da variação do saldo Bolsonaro menos Lula entre os turnos de 2022 sobre os votantes do 1º turno, explicada pela parcela da terceira via e pela parcela de brancos e nulos do 1º turno, com efeito fixo de UF, ponderada pelos votantes; inclinação da terceira via por classe de margem de Flávio em 2026 (aplicação) e por região (sensibilidade); intervalos por bootstrap de municípios. Bootstrap de 1.000 reamostragens, semente 20261005.

| Grupo | Municípios | Bolsonaro por voto | Lula por voto | Saldo por voto | IC 95% do saldo | Razão simples | Nexus sobre 2026 | Datafolha sobre 2026 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Flávio venceu com folga | 2.429 | 0,554 | 0,404 | +0,150 | +0,083 a +0,228 | +0,589 | +0,168 | +0,230 |
| Flávio venceu apertado | 476 | 0,472 | 0,437 | +0,034 | −0,030 a +0,119 | +0,378 | +0,187 | +0,234 |
| Flávio perdeu apertado | 364 | 0,427 | 0,455 | −0,028 | −0,082 a +0,073 | +0,259 | +0,195 | +0,237 |
| Flávio perdeu com folga | 2.301 | 0,332 | 0,456 | −0,124 | −0,239 a −0,029 | +0,188 | +0,187 | +0,224 |
| Norte | 450 | 0,681 | 0,695 | −0,014 | −0,178 a +0,145 | +0,485 | +0,184 | +0,221 |
| Nordeste | 1.794 | 0,600 | 0,449 | +0,151 | −0,068 a +0,314 | +0,193 | +0,190 | +0,225 |
| Centro-Oeste | 467 | 0,396 | 0,405 | −0,009 | −0,111 a +0,129 | +0,549 | +0,070 | +0,197 |
| Sudeste | 1.668 | 0,317 | 0,440 | −0,123 | −0,206 a +0,095 | +0,375 | +0,195 | +0,237 |
| Sul | 1.191 | 0,352 | 0,387 | −0,035 | −0,180 a +0,148 | +0,706 | +0,192 | +0,241 |
| Brasil, inclinação única | 5.570 | 0,427 | 0,452 | −0,025 | −0,108 a +0,100 | +0,409 | +0,179 | +0,230 |

**Inferência.** A razão simples credita à terceira via todo o movimento entre os turnos. Sem efeito fixo de UF, a regressão dá +0,198 por voto de terceira via e uma constante de 3,39 pontos dos votantes a favor de Bolsonaro que não depende da terceira via. Por região, as inclinações de Bolsonaro e de Lula somam mais de um voto por voto de terceira via em Norte e Nordeste: a regressão ali capta algo além da terceira via, como comparecimento que anda junto com ela. A aplicação a 2026 usa a classe de margem.

**Inferência. Totais de 2026.** Nexus +1.664.014; Datafolha em Cury e Caiado +2.138.043; urna de 2022 por classe +448.181 (IC 95%: −167.003 a +1.145.029); urna por região −331.945; razão simples +3.927.301.

| Região | Terceira via | Nexus | Datafolha | Urna de 2022 | Nexus menos urna |
| --- | ---: | ---: | ---: | ---: | ---: |
| Norte | 631.871 | +116.594 | +139.404 | +32.618 | +83.976 |
| Nordeste | 1.811.095 | +343.642 | +408.248 | −189.686 | +533.328 |
| Centro-Oeste | 987.718 | +68.848 | +194.219 | +136.605 | −67.757 |
| Sudeste | 4.342.954 | +844.685 | +1.031.021 | +285.499 | +559.186 |
| Sul | 1.513.514 | +290.246 | +365.150 | +183.146 | +107.100 |

**Inferência. Ranking.** 60 dos 100 primeiros pelo saldo da pesquisa também estão nos 100 primeiros pela urna (robustos, 2.264.186 votos de terceira via); 40 só pela pesquisa e 40 só pela urna. Motivo dominante das divergências: só pesquisa, classe 29, só pesquisa, composicao 11, só urna, classe 32, só urna, composicao 8. A combinação ordena pelo piso (o menor saldo das duas) e mostra o teto.

| Nº | Município | Terceira via | Nexus | Datafolha | Urna | Piso | Teto | Nº pesquisa | Nº urna | Situação |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | Brasília (DF) | 187.565 | +24.262 | +41.194 | +28.154 | +24.262 | +28.154 | 5 | 1 | robusto |
| 2 | Curitiba (PR) | 132.614 | +25.901 | +32.593 | +19.905 | +19.905 | +25.901 | 4 | 3 | robusto |
| 3 | Manaus (AM) | 101.648 | +18.404 | +21.062 | +15.257 | +15.257 | +18.404 | 7 | 4 | robusto |
| 4 | Rio de Janeiro (RJ) | 285.003 | +50.386 | +65.803 | +9.747 | +9.747 | +50.386 | 2 | 5 | robusto |
| 5 | Campinas (SP) | 61.515 | +12.484 | +14.959 | +9.233 | +9.233 | +12.484 | 12 | 6 | robusto |
| 6 | Campo Grande (MS) | 44.160 | +8.729 | +10.605 | +6.628 | +6.628 | +8.729 | 20 | 8 | robusto |
| 7 | São José dos Campos (SP) | 42.545 | +9.098 | +10.587 | +6.386 | +6.386 | +9.098 | 17 | 9 | robusto |
| 8 | Sorocaba (SP) | 41.856 | +8.852 | +10.274 | +6.283 | +6.283 | +8.852 | 19 | 10 | robusto |
| 9 | Uberlândia (MG) | 39.249 | +7.463 | +9.770 | +5.891 | +5.891 | +7.463 | 24 | 11 | robusto |
| 10 | Contagem (MG) | 37.047 | +7.683 | +8.989 | +5.561 | +5.561 | +7.683 | 22 | 12 | robusto |
| 11 | Ribeirão Preto (SP) | 36.766 | +7.136 | +8.600 | +5.519 | +5.519 | +7.136 | 26 | 13 | robusto |
| 12 | São Gonçalo (RJ) | 34.139 | +6.031 | +7.698 | +5.124 | +5.124 | +6.031 | 31 | 14 | robusto |
| 13 | Duque de Caxias (RJ) | 34.032 | +5.931 | +7.670 | +5.108 | +5.108 | +5.931 | 32 | 15 | robusto |
| 14 | Joinville (SC) | 33.641 | +8.394 | +9.385 | +5.050 | +5.050 | +8.394 | 21 | 16 | robusto |
| 15 | Belo Horizonte (MG) | 147.491 | +30.156 | +35.986 | +5.044 | +5.044 | +30.156 | 3 | 17 | robusto |
| 16 | Maceió (AL) | 32.477 | +6.276 | +7.390 | +4.875 | +4.875 | +6.276 | 28 | 19 | robusto |
| 17 | Londrina (PR) | 31.887 | +5.396 | +7.143 | +4.786 | +4.786 | +5.396 | 37 | 20 | robusto |
| 18 | Nova Iguaçu (RJ) | 30.898 | +5.602 | +7.061 | +4.638 | +4.638 | +5.602 | 35 | 21 | robusto |
| 19 | Cuiabá (MT) | 29.772 | +5.212 | +6.743 | +4.469 | +4.469 | +5.212 | 40 | 22 | robusto |
| 20 | Jundiaí (SP) | 29.388 | +6.227 | +7.298 | +4.411 | +4.411 | +6.227 | 29 | 23 | robusto |
| 21 | Santos (SP) | 28.191 | +5.671 | +6.933 | +4.231 | +4.231 | +5.671 | 34 | 24 | robusto |
| 22 | Caxias do Sul (RS) | 27.774 | +5.480 | +6.777 | +4.169 | +4.169 | +5.480 | 36 | 25 | robusto |
| 23 | Mogi das Cruzes (SP) | 27.343 | +5.346 | +6.563 | +4.104 | +4.104 | +5.346 | 38 | 26 | robusto |
| 24 | Porto Velho (RO) | 25.457 | +4.740 | +5.802 | +3.821 | +3.821 | +4.740 | 49 | 27 | robusto |
| 25 | Ponta Grossa (PR) | 24.348 | +3.846 | +5.406 | +3.655 | +3.655 | +3.846 | 59 | 28 | robusto |
| 26 | Vila Velha (ES) | 24.247 | +5.133 | +6.041 | +3.639 | +3.639 | +5.133 | 41 | 29 | robusto |
| 27 | Maringá (PR) | 23.394 | +4.709 | +5.729 | +3.511 | +3.511 | +4.709 | 50 | 30 | robusto |
| 28 | São José do Rio Preto (SP) | 22.968 | +4.504 | +5.498 | +3.447 | +3.447 | +4.504 | 54 | 31 | robusto |
| 29 | Blumenau (SC) | 21.753 | +5.294 | +6.006 | +3.265 | +3.265 | +5.294 | 39 | 32 | robusto |
| 30 | Piracicaba (SP) | 20.562 | +4.195 | +5.051 | +3.086 | +3.086 | +4.195 | 55 | 33 | robusto |
| 31 | Campos dos Goytacazes (RJ) | 20.200 | +3.098 | +4.228 | +3.032 | +3.032 | +3.098 | 85 | 34 | robusto |
| 32 | Canoas (RS) | 19.615 | +4.147 | +4.895 | +2.944 | +2.944 | +4.147 | 56 | 35 | robusto |
| 33 | Taubaté (SP) | 19.427 | +3.801 | +4.750 | +2.916 | +2.916 | +3.801 | 60 | 36 | robusto |
| 34 | Bauru (SP) | 19.289 | +3.603 | +4.533 | +2.895 | +2.895 | +3.603 | 64 | 37 | robusto |
| 35 | São José dos Pinhais (PR) | 19.120 | +3.683 | +4.627 | +2.870 | +2.870 | +3.683 | 61 | 38 | robusto |
| 36 | Rio Branco (AC) | 18.536 | +3.117 | +4.034 | +2.782 | +2.782 | +3.117 | 83 | 39 | robusto |
| 37 | Uberaba (MG) | 18.247 | +3.581 | +4.555 | +2.739 | +2.739 | +3.581 | 69 | 40 | robusto |
| 38 | Petrópolis (RJ) | 18.060 | +3.153 | +4.068 | +2.711 | +2.711 | +3.153 | 81 | 41 | robusto |
| 39 | Franca (SP) | 17.786 | +3.602 | +4.392 | +2.670 | +2.670 | +3.602 | 65 | 43 | robusto |
| 40 | São João de Meriti (RJ) | 17.681 | +2.986 | +3.950 | +2.654 | +2.654 | +2.986 | 88 | 44 | robusto |
| 41 | Praia Grande (SP) | 17.332 | +3.460 | +4.199 | +2.602 | +2.602 | +3.460 | 75 | 45 | robusto |
| 42 | Guarulhos (SP) | 75.393 | +15.137 | +17.945 | +2.578 | +2.578 | +15.137 | 9 | 46 | robusto |
| 43 | Cariacica (ES) | 17.046 | +3.507 | +4.156 | +2.559 | +2.559 | +3.507 | 73 | 47 | robusto |
| 44 | Guarujá (SP) | 16.887 | +3.168 | +3.817 | +2.535 | +2.535 | +3.168 | 79 | 48 | robusto |
| 45 | Belford Roxo (RJ) | 16.224 | +2.796 | +3.610 | +2.435 | +2.435 | +2.796 | 93 | 49 | robusto |
| 46 | Cascavel (PR) | 16.209 | +3.452 | +4.150 | +2.433 | +2.433 | +3.452 | 77 | 50 | robusto |
| 47 | São José (SC) | 15.576 | +3.561 | +4.012 | +2.338 | +2.338 | +3.561 | 72 | 51 | robusto |
| 48 | Indaiatuba (SP) | 15.560 | +3.327 | +3.866 | +2.336 | +2.336 | +3.327 | 78 | 52 | robusto |
| 49 | Gravataí (RS) | 14.762 | +2.822 | +3.504 | +2.216 | +2.216 | +2.822 | 91 | 53 | robusto |
| 50 | Palmas (TO) | 14.750 | +2.561 | +3.350 | +2.214 | +2.214 | +2.561 | 102 | 54 | só urna |
| 51 | São Caetano do Sul (SP) | 14.650 | +3.153 | +3.748 | +2.199 | +2.199 | +3.153 | 80 | 55 | robusto |
| 52 | Boa Vista (RR) | 14.422 | +3.140 | +3.542 | +2.165 | +2.165 | +3.140 | 82 | 56 | robusto |
| 53 | Limeira (SP) | 13.567 | +2.861 | +3.376 | +2.036 | +2.036 | +2.861 | 89 | 58 | robusto |
| 54 | Sete Lagoas (MG) | 13.531 | +2.734 | +3.294 | +2.031 | +2.031 | +2.734 | 96 | 59 | robusto |
| 55 | Colombo (PR) | 13.316 | +2.429 | +3.158 | +1.999 | +1.999 | +2.429 | 115 | 60 | só urna |
| 56 | Jacareí (SP) | 12.371 | +2.465 | +2.966 | +1.857 | +1.857 | +2.465 | 111 | 62 | só urna |
| 57 | Sumaré (SP) | 12.256 | +2.662 | +3.045 | +1.840 | +1.840 | +2.662 | 99 | 63 | robusto |
| 58 | Santarém (PA) | 12.197 | +2.443 | +2.794 | +1.831 | +1.831 | +2.443 | 114 | 64 | só urna |
| 59 | Foz do Iguaçu (PR) | 12.139 | +2.665 | +3.192 | +1.822 | +1.822 | +2.665 | 98 | 65 | robusto |
| 60 | Imperatriz (MA) | 12.017 | +2.384 | +2.937 | +1.804 | +1.804 | +2.384 | 119 | 66 | só urna |
| 61 | Itajaí (SC) | 11.995 | +2.819 | +3.164 | +1.800 | +1.800 | +2.819 | 92 | 67 | robusto |
| 62 | Americana (SP) | 11.967 | +2.569 | +2.958 | +1.796 | +1.796 | +2.569 | 100 | 68 | robusto |
| 63 | Palhoça (SC) | 11.853 | +2.795 | +3.111 | +1.779 | +1.779 | +2.795 | 94 | 69 | robusto |
| 64 | Hortolândia (SP) | 11.725 | +2.552 | +2.889 | +1.760 | +1.760 | +2.552 | 105 | 70 | só urna |
| 65 | Goiânia (GO) | 135.268 | +1.729 | +23.991 | +20.304 | +1.729 | +20.304 | 155 | 2 | só urna |
| 66 | Divinópolis (MG) | 11.518 | +2.546 | +2.915 | +1.729 | +1.729 | +2.546 | 106 | 71 | só urna |
| 67 | Novo Hamburgo (RS) | 11.437 | +2.451 | +2.917 | +1.717 | +1.717 | +2.451 | 112 | 73 | só urna |
| 68 | Criciúma (SC) | 11.107 | +2.469 | +2.943 | +1.667 | +1.667 | +2.469 | 110 | 75 | só urna |
| 69 | Santo André (SP) | 47.873 | +9.940 | +11.676 | +1.637 | +1.637 | +9.940 | 15 | 76 | robusto |
| 70 | Várzea Grande (MT) | 10.772 | +1.921 | +2.520 | +1.617 | +1.617 | +1.921 | 139 | 77 | só urna |
| 71 | Osasco (SP) | 47.253 | +9.608 | +11.445 | +1.616 | +1.616 | +9.608 | 16 | 78 | robusto |
| 72 | Chapecó (SC) | 10.709 | +2.243 | +2.729 | +1.607 | +1.607 | +2.243 | 121 | 79 | só urna |
| 73 | São Leopoldo (RS) | 10.606 | +2.272 | +2.666 | +1.592 | +1.592 | +2.272 | 120 | 80 | só urna |
| 74 | Parauapebas (PA) | 10.509 | +2.227 | +2.415 | +1.577 | +1.577 | +2.227 | 123 | 81 | só urna |
| 75 | Macaé (RJ) | 10.414 | +1.888 | +2.264 | +1.563 | +1.563 | +1.888 | 141 | 82 | só urna |
| 76 | Nova Friburgo (RJ) | 10.399 | +1.844 | +2.351 | +1.561 | +1.561 | +1.844 | 146 | 83 | só urna |
| 77 | Magé (RJ) | 10.285 | +1.717 | +2.257 | +1.544 | +1.544 | +1.717 | 156 | 84 | só urna |
| 78 | Bragança Paulista (SP) | 10.099 | +2.081 | +2.493 | +1.516 | +1.516 | +2.081 | 129 | 85 | só urna |
| 79 | Passo Fundo (RS) | 10.063 | +1.988 | +2.500 | +1.510 | +1.510 | +1.988 | 132 | 86 | só urna |
| 80 | Rio Claro (SP) | 9.745 | +1.948 | +2.337 | +1.463 | +1.463 | +1.948 | 136 | 87 | só urna |
| 81 | Marília (SP) | 9.733 | +1.880 | +2.333 | +1.461 | +1.461 | +1.880 | 143 | 88 | só urna |
| 82 | Atibaia (SP) | 9.653 | +1.973 | +2.386 | +1.449 | +1.449 | +1.973 | 134 | 89 | só urna |
| 83 | Santana de Parnaíba (SP) | 9.632 | +2.205 | +2.534 | +1.446 | +1.446 | +2.205 | 125 | 90 | só urna |
| 84 | Ipatinga (MG) | 9.541 | +2.241 | +2.441 | +1.432 | +1.432 | +2.241 | 122 | 91 | só urna |
| 85 | Santa Bárbara D'oeste (SP) | 9.465 | +1.935 | +2.270 | +1.421 | +1.421 | +1.935 | 137 | 92 | só urna |
| 86 | Araucária (PR) | 9.359 | +1.742 | +2.187 | +1.405 | +1.405 | +1.742 | 153 | 93 | só urna |
| 87 | Itaboraí (RJ) | 9.341 | +1.613 | +2.118 | +1.402 | +1.402 | +1.613 | 163 | 94 | só urna |
| 88 | Itu (SP) | 9.283 | +1.821 | +2.233 | +1.393 | +1.393 | +1.821 | 147 | 96 | só urna |
| 89 | Presidente Prudente (SP) | 9.245 | +1.764 | +2.263 | +1.388 | +1.388 | +1.764 | 151 | 97 | só urna |
| 90 | Jaraguá do Sul (SC) | 9.162 | +2.145 | +2.419 | +1.375 | +1.375 | +2.145 | 127 | 98 | só urna |
| 91 | Pindamonhangaba (SP) | 8.989 | +1.637 | +2.077 | +1.349 | +1.349 | +1.637 | 162 | 99 | só urna |
| 92 | Dourados (MS) | 8.872 | +1.884 | +2.172 | +1.332 | +1.332 | +1.884 | 142 | 100 | só urna |
| 93 | Cabo Frio (RJ) | 8.817 | +1.602 | +1.950 | +1.323 | +1.323 | +1.602 | 166 | 101 | fora |
| 94 | Poços de Caldas (MG) | 8.783 | +2.024 | +2.327 | +1.318 | +1.318 | +2.024 | 131 | 102 | fora |
| 95 | Araçatuba (SP) | 8.761 | +1.644 | +2.041 | +1.315 | +1.315 | +1.644 | 160 | 103 | fora |
| 96 | Governador Valadares (MG) | 8.738 | +2.146 | +2.386 | +1.312 | +1.312 | +2.146 | 126 | 104 | fora |
| 97 | Botucatu (SP) | 8.738 | +1.579 | +1.968 | +1.312 | +1.312 | +1.579 | 170 | 105 | fora |
| 98 | Rondonópolis (MT) | 8.669 | +1.503 | +2.049 | +1.301 | +1.301 | +1.503 | 177 | 106 | fora |
| 99 | Pinhais (PR) | 8.651 | +1.747 | +2.169 | +1.299 | +1.299 | +1.747 | 152 | 107 | fora |
| 100 | Guarapuava (PR) | 8.377 | +1.574 | +2.003 | +1.257 | +1.257 | +1.574 | 171 | 108 | fora |

**Os movimentos do capítulo pelas duas réguas.**

| Movimento | Régua do capítulo | Urna de 2022 | Nota |
| ---: | ---: | --- | --- |
| 1. Colher o eleitor de Renan Santos | +1.271.709 | +121.401 | mesmo sinal |
| 2. Converter a não escolha da terceira via | +831.761 | não se aplica | a urna não separa quem não escolheu |
| 3. Agenda conjunta com Tarcísio em São Paulo | +724.594 | não se aplica | agenda com governador: a régua mede terceira via, não palanque |
| 4. Disputar o eleitor de Augusto Cury | +450.752 | +123.942 | mesmo sinal |
| 5. Nordeste: interior antes das capitais | +348.297 | −189.686 | a regra do capítulo já é analogia de 2022 (razão simples); aqui, a regressão |
| 6. Agenda conjunta com Cleitinho em Minas | +316.080 | não se aplica | agenda com governador: a régua mede terceira via, não palanque |
| 7. Casar o 2º turno de Douglas Ruas com o de Flávio no Rio | +213.560 | não se aplica | agenda com governador: a régua mede terceira via, não palanque |
| 8. Fechar Zema e as candidaturas menores da direita | +174.623 | +23.122 | mesmo sinal |
| 9. Um ponto a mais de comparecimento nas 15 UFs de Flávio | +174.158 | não se aplica | eleitor novo: a régua mede terceira via, não comparecimento |
| 10. Disputar o eleitor de Caiado com Daniel Vilela em Goiás | +116.442 | +170.826 | mesmo sinal |

**Retrovisão.** Não há no acervo pesquisa de 2º turno de 2022 com o cruzamento pelo voto de 1º turno (15 pastas em `data/originals/pesquisas_2022/`, 14 pesquisas transcritas em `analysis/predicao_2026/erro_2022/pesquisas_2022.json`, todas da última onda antes do 1º turno). Para o teste é preciso arquivar as primeiras ondas nacionais de 2º turno de outubro de 2022 que tenham cruzado o voto de 2º turno pelo voto em Tebet e Ciro, com URL, SHA-256 e página.

## Limites

- A matriz é nacional e aplicada localmente: o eleitor de Cury em Salvador vota, na conta, como o de Cury em Joinville.
- Vão local é mesma urna e cargos diferentes: não diz quem votou em quem, e o governador sem apoio declarado a Flávio é teto, não palanque.
- O teto soma parcelas que podem contar o mesmo eleitor.
- 2022 é uma eleição, com outra terceira via e outro desenho de 2º turno estadual; a régua da urna é inferência ecológica, de agregado para agregado.
- Nada aqui é previsão do 2º turno. Os pesos do índice são juízo editorial.
