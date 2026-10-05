# O caminho do 2º turno

Capítulo estratégico do dossiê da apuração do 1º turno de 2026. A casa tem lado: o projeto é a vitória de Flávio Bolsonaro em 25/10. O método não tem lado: cada movimento sai com número e fonte, e o achado que contraria a tese sai com o mesmo peso.

Números de 2026: banco da apuração (`apuracao/data/apuracao.sqlite`), arquivo nacional de presidente gerado pelo TSE em 05/10/2026, 02h59 (499.248 de 499.248 seções) e lido pelo coletor em 05/10/2026, 03h00, horário de Brasília. Números de 2022: arquivos do TSE em `data/raw/tse_resultados/api_2022/` e a tabela municipal `data/outputs/estaduais2026/municipios.csv`. Tudo se reproduz com `python3 scripts/apuracao-2026-estrategia.py`, que grava `analysis/apuracao_2026/dados/estrategia_2t.json`.

Rótulos: **Verificado** é número da urna ou de documento arquivado. **Inferência** é conta sobre medição publicada. **Hipótese** é suposição declarada, que pode estar errada. **Analogia** é o que aconteceu em 2022, uma eleição só. **Juízo editorial** é opinião da casa.

## Em cinco linhas

1. **Verificado.** Flávio sai do 1º turno com 2,22 milhões de votos de vantagem, 1,87 ponto dos válidos (47,03% contra 45,16%).
2. **Inferência.** A matriz de transferência da Nexus aplicada aos 9,32 milhões de votos de terceira via leva Flávio a 51,67% dos válidos só com o que foi medido. Na leitura mais favorável a ele, com as linhas do Datafolha para Cury e Caiado e com a não escolha votando na proporção da própria linha, a 52,27%.
3. **Inferência.** Para virar só com a terceira via, Lula precisaria de 61,94% de todos esses votos. A Nexus mede 36,98% entre os que escolhem. Mesmo que toda a não escolha da terceira via fosse para Lula, Flávio ainda teria 992 mil votos de vantagem.
4. **Inferência.** O risco maior não está na transferência. Está na base e no comparecimento: se 3,47% da base de Flávio trocar de lado, a margem central some. Contra o 1º turno de 2022, o comparecimento de 2026 variou −0,78 ponto no Centro-Sul e +1,14 no Nordeste, a direção errada para Flávio.
5. **Inferência.** O estoque de 2022 que Flávio ainda não alcançou soma 2,48 milhões de votos e está 85% no Centro-Sul. O de Lula é 2,84 vezes maior: quem tem mais eleitor de 2022 para buscar é Lula.

## 1. A aritmética do 2º turno

**Verificado.** Eleitorado de 158.745.502. Compareceram 125.275.835 (78,92%); faltaram 33.469.244 (21,08%). Brancos e nulos somaram 5.975.047, 4,77% de quem foi votar. Dos 119.300.788 votos válidos, Flávio teve 56.104.503 (47,03%) e Lula 53.879.538 (45,16%). Diferença: 2.224.965 votos.

O 2º turno começa nos 9.316.747 votos dados às outras candidaturas:

| Candidatura | Partido | Votos | Válidos | Linha da matriz |
| --- | --- | ---: | ---: | --- |
| Augusto Cury | AVANTE | 3.448.569 | 2,89% | Cury |
| Renan Santos | MISSÃO | 2.675.887 | 2,24% | Renan |
| Ronaldo Caiado | PSD | 2.605.148 | 2,18% | Caiado |
| Romeu Zema | NOVO | 326.488 | 0,27% | Zema |
| Demais seis candidaturas | UP, PSTU, DC, PCB, DEMOCRATA, PCO | 260.655 | 0,21% | própria (Samara) ou do mesmo campo |
| **Total** |  | **9.316.747** | **7,81%** |  |

**Inferência.** No acervo da casa, a única matriz com uma linha para cada candidatura de terceira via é a da Nexus/BTG, 18 a 20/09/2026, p. 79 (`docs/assets/voto_util_092026.json → nacional.transferencia`). O Datafolha publicou duas linhas no texto do relatório nacional (Datafolha, BR-04029/2026, campo 15/09/2026 a 17/09/2026, p. 7; `docs/assets/datafolha_21092026_data.json → transfer`), para Cury e Caiado; na matriz "Datafolha" as demais linhas vêm da Nexus. Cada linha diz, entre os eleitores de uma candidatura, quantos votariam em Flávio, em Lula ou em nenhum dos dois:

| Eleitorado de | Flávio | Lula | Branco, nulo ou indeciso | Soma | Datafolha (Flávio × Lula) |
| --- | ---: | ---: | ---: | ---: | --- |
| Cury | 44 | 30 | 25 | 99 | 44 × 32, não escolha 24 |
| Caiado | 30 | 36 | 33 | 99 | 42 × 27, não escolha 31 |
| Renan | 56 | 8 | 37 | 101 | sem linha |
| Zema | 59 | 13 | 29 | 101 | sem linha |
| Samara | 6 | 58 | 36 | 100 | sem linha |

As linhas somam 99 ou 101 por arredondamento do instituto; a conta divide cada uma pela própria soma. As cinco candidaturas sem linha publicada recebem a linha da candidatura publicada do mesmo campo: Hertz Dias (PSTU, linha de Samara), Clariana Barao (DC, linha de Zema), Edmilson Costa (PCB, linha de Samara), Veterinário Wilson Grassi (DEMOCRATA, linha de Zema) e Rui Costa Pimenta (PCO, linha de Samara). Juntas são 0,11% dos válidos.

**Hipóteses fixas da conta.** As bases do 1º turno ficam onde estão; branco, nulo e abstenção do 1º turno não entram; o comparecimento não muda. A única coisa que varia é o destino da parcela de cada linha que não escolheu ninguém:

- **só o medido:** essa parcela não vira voto válido;
- **proporcional:** vota na mesma proporção Flávio:Lula da própria linha;
- **meio a meio:** divide-se igualmente.

| Matriz | Hipótese | Flávio | Lula | Margem (votos) | Margem (pontos) |
| --- | --- | ---: | ---: | ---: | ---: |
| Nexus | só o medido | 51,67% | 48,33% | +3.895.146 | +3,35 |
| Nexus | não escolha na proporção da linha | 51,98% | 48,02% | +4.726.907 | +3,96 |
| Nexus | não escolha meio a meio | 51,63% | 48,37% | +3.895.146 | +3,26 |
| Datafolha em Cury e Caiado | só o medido | 51,88% | 48,12% | +4.369.957 | +3,75 |
| Datafolha em Cury e Caiado | não escolha na proporção da linha | 52,27% | 47,73% | +5.422.154 | +4,54 |
| Datafolha em Cury e Caiado | não escolha meio a meio | 51,83% | 48,17% | +4.369.957 | +3,66 |

Dividir a não escolha meio a meio não mexe na margem em votos: soma o mesmo aos dois lados e só dilui o percentual. Quem decide a margem é a parte medida das linhas. Na conta central (Nexus, só o medido), o eleitorado de Renan Santos entrega a Flávio o maior saldo, 1.271.709 votos; o de Ronaldo Caiado entrega o maior saldo a Lula, 157.888.

**Inferência. Ponto de equilíbrio.** Para Lula zerar a diferença do 1º turno só com a terceira via, precisaria de 61,94% de todos os 9,32 milhões de votos, se todos votassem em alguém. Pela Nexus, só 68,84% desse eleitorado escolhe um dos dois; entre eles, Lula precisaria de 67,35%, e a medição dá 36,98%. Mesmo que toda a não escolha da terceira via (2,90 milhões de votos, pela Nexus) fosse para Lula, Flávio terminaria com 992 mil votos de vantagem; com as linhas do Datafolha para Cury e Caiado, 1,57 milhão de votos.

**Inferência. Eleitor novo.** O caminho que sobra a Lula é trazer quem faltou. Para apagar a margem central de 3,90 milhões de votos só com eleitores que não votaram no 1º turno, seriam precisos 19,48 milhões de eleitores novos votando 60% em Lula, ou 9,74 milhões de eleitores novos votando 70%. A abstenção do 1º turno foi de 33,47 milhões de eleitores. **Verificado:** em 2022 o comparecimento subiu 570.424 votos entre os turnos (+0,36 ponto).

**Inferência. Base.** A mesma margem central some se 3,47% dos eleitores de Flávio no 1º turno votarem em Lula, ou se 6,94% deles deixarem de votar.

**Analogia.** Em 2022, entre os turnos, Bolsonaro ganhou 7.134.009 votos e Lula 3.086.495, partindo de 9.897.870 votos de terceira via. A diferença a favor de Lula caiu de 6.187.159 para 2.139.645. Se cada voto de terceira via de 2026 rendesse o que rendeu em 2022 (taxas de 0,7208 para Bolsonaro e 0,3118 para Lula, que incluem mudança de comparecimento e de branco e nulo), Flávio teria 52,52%; aplicando a taxa de cada UF à própria UF, 52,59%. A terceira via de 2022 era outra (Simone Tebet e Ciro Gomes); a analogia mede ordem de grandeza, não destino.

**Juízo editorial.** A aritmética favorece Flávio por uma margem que nenhuma das seis combinações de matriz e hipótese desfaz (de 3,90 a 5,42 milhões de votos). A campanha de Flávio é de defesa: segurar a base, colher o que as linhas já mediram e não perder comparecimento. A de Lula precisa mudar as linhas medidas ou trazer eleitor novo em escala que 2022 não mostrou.

## 2. Onde está o voto

Comparação de 2026 com 2022 por região: Nordeste (9 UFs), Norte (7) e Centro-Sul (Sudeste, Sul e Centro-Oeste com o DF, 11). Parcelas dos válidos de cada turno; o exterior fica à parte.

| Região | Flávio 2026 | Bolsonaro 2022, 1º t. | Bolsonaro 2022, 2º t. | Flávio − Bolsonaro 2º t. (pp) | Lula 2026 | Lula 2022, 1º t. | Terceira via 2026 | Estoque de Flávio | Estoque de Lula |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Nordeste | 30,85% | 26,97% | 30,66% | +0,20 | 63,77% | 66,76% | 5,37% | 162.996 | 1.802.097 |
| Norte | 49,15% | 45,45% | 51,03% | −1,87 | 44,65% | 47,09% | 6,20% | 200.014 | 394.458 |
| Centro-Sul | 54,02% | 49,90% | 56,71% | −2,69 | 36,87% | 40,71% | 9,12% | 2.116.164 | 4.848.822 |

**Verificado.** No 1º turno contra 1º turno, Flávio fica acima de Bolsonaro de 2022 nas três regiões (Nordeste +3,88; Norte +3,70; Centro-Sul +4,11) e em 26 das 27 UFs; a exceção: Distrito Federal (−0,34). Lula fica abaixo do próprio 1º turno de 2022 nas três regiões (Nordeste −2,99; Norte −2,44; Centro-Sul −3,85).

**Verificado.** Em seis UFs o 1º turno de Flávio já passou a parcela de Bolsonaro no 2º turno de 2022: MA, TO, CE, PI, BA e MT. No Nordeste como um todo, também: 30,85% contra 30,66%. No Centro-Sul, Flávio está 2,69 pontos abaixo do 2º turno de Bolsonaro, e foi ali que a terceira via teve mais voto: 9,12% dos válidos, contra 5,37% no Nordeste e 6,20% no Norte.

### O estoque de 2022

**Método.** Estoque de Flávio = votos de Bolsonaro no 2º turno de 2022 × max(0; 1 − parcela de Flávio nos válidos do 1º turno de 2026 ÷ parcela de Bolsonaro nos válidos do 2º turno de 2022), por UF e por município. Mede, na escala do voto de 2022, a distância de parcela que falta. Não identifica eleitor; onde Flávio já passou de Bolsonaro o estoque é zero e o excedente não compensa outro lugar, por isso a soma municipal é maior que a estadual. O mesmo cálculo com Lula de 2022 dá o estoque de Lula.

**Inferência.** O estoque de Flávio soma 2.479.174 votos pelas UFs. Cinco UFs guardam 70,02%: SP 851.320, RJ 336.114, MG 192.004, GO 190.827 e PR 165.646. Município a município, o estoque soma 3.076.825; as capitais guardam 44,43% dele e os 20 maiores estoques municipais, 43,57%.

| UF | Região | Flávio 2026 | Bols. 2022, 1º t. | Bols. 2022, 2º t. | Flávio − Bols. 2º t. (pp) | Flávio − Bols. 2º t. (votos) | Estoque de Flávio | Lula 2026 | Lula − Lula 2022, 1º t. (pp) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SP | Centro-Sul | 51,93% | 47,71% | 55,24% | −3,31 | −1.294.564 | 851.320 | 38,20% | −2,69 |
| RJ | Centro-Sul | 53,01% | 51,09% | 56,53% | −3,52 | −437.050 | 336.114 | 39,41% | −1,27 |
| MG | Centro-Sul | 48,24% | 43,60% | 49,80% | −1,56 | −363.762 | 192.004 | 43,33% | −4,96 |
| GO | Centro-Sul | 53,60% | 52,16% | 58,71% | −5,11 | −141.153 | 190.827 | 31,06% | −8,46 |
| PR | Centro-Sul | 59,91% | 55,26% | 62,40% | −2,48 | −213.998 | 165.646 | 31,20% | −4,79 |
| DF | Centro-Sul | 51,31% | 51,65% | 58,81% | −7,50 | −131.715 | 132.835 | 38,11% | +1,26 |
| SC | Centro-Sul | 66,65% | 62,21% | 69,27% | −2,62 | −47.610 | 115.163 | 25,04% | −4,49 |
| PE | Nordeste | 31,03% | 29,91% | 33,07% | −2,04 | −60.789 | 110.827 | 63,45% | −1,81 |
| AM | Norte | 45,00% | 42,80% | 48,90% | −3,90 | +15.023 | 76.783 | 48,23% | −1,35 |
| ES | Centro-Sul | 54,78% | 52,23% | 58,04% | −3,26 | −48.951 | 72.051 | 37,76% | −2,64 |
| RS | Centro-Sul | 55,64% | 48,89% | 56,35% | −0,71 | −159.402 | 47.015 | 35,73% | −6,56 |
| PA | Norte | 44,50% | 40,27% | 45,25% | −0,76 | +90.062 | 34.615 | 49,91% | −2,31 |
| RO | Norte | 67,45% | 64,36% | 70,66% | −3,21 | +19.752 | 28.760 | 25,89% | −3,09 |
| SE | Nordeste | 30,63% | 29,16% | 32,79% | −2,16 | −3.247 | 27.799 | 62,75% | −1,08 |
| AC | Norte | 64,56% | 62,50% | 70,30% | −5,74 | +15.057 | 23.515 | 28,73% | −0,53 |
| AP | Norte | 45,67% | 43,41% | 51,36% | −5,70 | +11.731 | 22.241 | 45,71% | +0,04 |
| AL | Nordeste | 40,45% | 36,05% | 41,32% | −0,87 | +47.891 | 14.481 | 54,73% | −1,77 |
| RR | Norte | 71,06% | 69,57% | 76,08% | −5,02 | +17.804 | 14.100 | 22,86% | −0,19 |
| MS | Centro-Sul | 58,60% | 52,70% | 59,49% | −0,89 | −7.255 | 13.189 | 34,68% | −4,36 |
| PB | Nordeste | 33,07% | 29,62% | 33,38% | −0,30 | +28.875 | 7.271 | 61,31% | −2,90 |
| RN | Nordeste | 34,77% | 31,02% | 34,90% | −0,13 | +9.112 | 2.618 | 59,75% | −3,23 |
| BA | Nordeste | 28,53% | 24,31% | 27,88% | +0,66 | +85.557 | 0 | 66,17% | −3,55 |
| CE | Nordeste | 31,27% | 25,38% | 30,03% | +1,24 | +122.373 | 0 | 63,29% | −2,62 |
| MA | Nordeste | 30,90% | 26,02% | 28,86% | +2,03 | +156.291 | 0 | 63,99% | −4,85 |
| MT | Centro-Sul | 65,15% | 59,84% | 65,08% | +0,07 | +81.851 | 0 | 29,18% | −5,21 |
| PI | Nordeste | 24,09% | 19,90% | 23,14% | +0,95 | +49.963 | 0 | 70,99% | −3,26 |
| TO | Norte | 50,44% | 44,00% | 48,64% | +1,80 | +57.667 | 0 | 43,42% | −6,97 |

Os municípios com maior estoque:

| Município | Flávio 2026 | Bolsonaro 2022, 2º t. | Estoque |
| --- | ---: | ---: | ---: |
| São Paulo (SP) | 42,13% | 46,46% | 297.358 |
| Rio de Janeiro (RJ) | 47,88% | 52,66% | 175.167 |
| Brasília (DF) | 51,31% | 58,81% | 132.835 |
| Belo Horizonte (MG) | 48,30% | 54,25% | 91.511 |
| Curitiba (PR) | 57,50% | 64,78% | 80.927 |
| Manaus (AM) | 54,28% | 61,28% | 79.086 |
| Goiânia (GO) | 54,68% | 63,95% | 74.343 |
| Recife (PE) | 38,37% | 43,68% | 52.646 |
| Belém (PA) | 43,74% | 49,72% | 51.375 |
| Porto Alegre (RS) | 41,86% | 46,50% | 37.981 |
| Fortaleza (CE) | 39,34% | 41,82% | 37.634 |
| Salvador (BA) | 27,03% | 29,27% | 34.527 |
| Guarulhos (SP) | 49,22% | 53,67% | 32.449 |
| Campinas (SP) | 52,07% | 56,22% | 27.161 |
| Londrina (PR) | 65,15% | 72,86% | 23.862 |

**Achado contrário.** O mesmo cálculo com Lula de 2022 dá 7.045.377 votos, 2,84 vezes o de Flávio. Lula está 5,74 pontos abaixo do próprio 2º turno de 2022; Flávio, 2,06 pontos abaixo do de Bolsonaro. O estoque de Lula está 69% no Centro-Sul, onde estão 73% dos votos de Cury e Caiado. E recuperar o estoque de Bolsonaro não basta: Bolsonaro perdeu com ele, com 49,10% dos válidos.

### Nordeste: capitais e interior

| Grupo | Flávio 2026 | Bols. 2022, 1º t. | Bols. 2022, 2º t. | Lula 2026 | Lula 2022, 1º t. | Lula, variação (pp) | Lula, variação (votos) | Estoque de Flávio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Capitais (9) | 37,40% | 34,94% | 40,51% | 55,25% | 55,81% | −0,56 | −88.358 | 224.346 |
| Interior (1.785) | 29,21% | 24,85% | 28,02% | 65,91% | 69,68% | −3,77 | −181.525 | 154.450 |

**Verificado.** A queda de Lula no Nordeste é do interior: −3,77 pontos no interior contra −0,56 nas capitais. Flávio varia +4,36 pontos no interior e +2,46 nas capitais, sobre Bolsonaro no 1º turno de 2022. Lula contra o próprio 1º turno de 2022, por UF: MA −4,85; BA −3,55; PI −3,26; RN −3,23; PB −2,90; CE −2,62; PE −1,81; AL −1,77; SE −1,08.

**Verificado.** Onde Lula perdeu mais votos contra o 1º turno de 2022: Salvador (BA) −78.370; Feira de Santana (BA) −17.541; Natal (RN) −11.739; São Luís (MA) −7.525; Teresina (PI) −5.119; Fortaleza (CE) −5.007. Onde Flávio mais ganhou sobre Bolsonaro no 1º turno: Fortaleza (CE) +56.089; Salvador (BA) +23.736; Maceió (AL) +19.736; São Luís (MA) +19.113; Feira de Santana (BA) +14.456; Teresina (PI) +14.030.

**Inferência.** No interior, Flávio já passou o 2º turno de Bolsonaro (29,21% contra 28,02%); nas capitais, ainda não (37,40% contra 40,51%). O estoque nordestino soma 224.346 nas capitais e 154.450 no interior. Capitais com maior estoque: Recife 38,37% contra 43,68%; Fortaleza 39,34% contra 41,82%; Salvador 27,03% contra 29,27%; Maceió 52,36% contra 57,18%; João Pessoa 45,67% contra 49,90%.

**Analogia.** Em 2022, entre os turnos, o saldo de Bolsonaro sobre Lula foi de 128.287 votos nas capitais nordestinas e de 265.438 no interior; por voto de terceira via do 1º turno, 0,2023 e 0,1886. Aplicado à terceira via de 2026, o interior rende 247.706 votos e as capitais 100.591.

**Juízo editorial.** No Nordeste o estoque aponta para as capitais e a história aponta para o interior. A casa fica com a história, porque ela mede voto que se moveu entre turnos e o estoque mede só distância de parcela: interior primeiro, capitais como vitrine.

## 3. Governadores como aliados

**Método.** Vão = votos do governador eleito menos votos de Flávio na mesma UF e na mesma urna; em pontos, cada um sobre os válidos do próprio cargo, como calcula o TSE (no governador, a base inclui votos anulados sub judice). Rótulo obrigatório: **teto endereçável, nunca transferência certa.** Parte do eleitorado do governador vota Lula por escolha medida.

| UF | Governador | Partido e campo | Votos | % válidos (gov.) | Flávio | % válidos (pres.) | Vão (pp) | Vão (votos) | Município de maior vão |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| SP | Tarcísio | REPUBLICANOS, direita | 14.491.874 | 62,65% | 12.922.023 | 51,93% | +10,72 | +1.569.851 | São Paulo +472.949 |
| PB | Lucas Ribeiro (aliado de Lula) | PP, centro-direita | 1.470.252 | 64,30% | 831.377 | 33,07% | +31,22 | +638.875 | Campina Grande +27.350 |
| MG | Cleitinho Azevedo | REPUBLICANOS, direita | 6.321.590 | 55,40% | 5.777.548 | 48,24% | +7,15 | +544.042 | Divinópolis +22.720 |
| PA | Dr. Daniel | PODE, centro-direita | 2.345.721 | 51,36% | 2.163.957 | 44,50% | +6,87 | +181.764 | Ananindeua +58.018 |
| AL | JHC | PSDB, centro-direita | 891.857 | 52,20% | 735.718 | 40,45% | +11,75 | +156.139 | Maceió +64.843 |
| MS | Eduardo Riedel | PP, centro-direita | 914.323 | 67,07% | 873.351 | 58,60% | +8,46 | +40.972 | Corumbá +5.475 |
| RR | Arthur Henrique | PL, direita | 220.809 | 69,13% | 231.322 | 71,06% | −1,93 | −10.513 | Uiramutã +264 |
| SC | Jorginho Mello | PL, direita | 2.942.386 | 68,98% | 3.000.020 | 66,65% | +2,32 | −57.634 | Joinville +11.219 |
| RS | Zucco | PL, direita | 3.516.048 | 58,05% | 3.573.783 | 55,64% | +2,41 | −57.735 | Pelotas +2.222 |
| RO | Marcos Rogério | PL, direita | 537.370 | 56,86% | 652.988 | 67,45% | −10,59 | −115.618 | nenhum |
| MT | Otaviano Pivetta | REPUBLICANOS, direita | 1.128.099 | 60,77% | 1.298.581 | 65,15% | −4,38 | −170.482 | Barão de Melgaço +1.450 |

**Verificado.** Os três maiores vãos em votos: SP (+1.569.851), PB (+638.875) e MG (+544.042). Em cinco UFs o governador aliado teve menos votos que Flávio: RR (Arthur Henrique, −10.513), SC (Jorginho Mello, −57.634), RS (Zucco, −57.735), RO (Marcos Rogério, −115.618) e MT (Otaviano Pivetta, −170.482). Ali o governador não tem voto a emprestar; é palanque, não reserva. Em SC e RS o governador tem parcela maior e menos votos que Flávio porque a eleição de governador teve menos votos válidos na mesma urna (SC: 4.265.641 contra 4.500.897; RS: 6.057.443 contra 6.423.046).

**Verificado, com ressalva.** Lucas Ribeiro (PP) é centro-direita pela classificação partidária da casa, mas é vice de João Azevêdo (PSB), aliado de Lula (`docs/assets/voto_util_092026.json`, `campo_excecao`). O vão de 31,22 pontos na Paraíba não é endereçável como aliança: é o eleitor de um governo aliado de Lula.

**Inferência sobre medição publicada.** O Datafolha publicou no texto dos relatórios estaduais, com campo em 08–10/09/2026, como vota para presidente o eleitor de cada governador. Páginas: MG pp. 20 e 21; RJ pp. 12 e 13; SP p. 4. Transcrição em `docs/assets/datafolha_21092026_sudeste.json`.

- **SP, p. 4:** entre os eleitores de Tarcísio, Flávio 59%, Lula 12%, Cury 8% no 1º turno. Aplicada aos 14.491.874 votos de Tarcísio, a linha de Lula daria 1.739.025 eleitores de Tarcísio com Lula, mais que o vão bruto de 1.569.851. Ordem de grandeza, não medição da urna: a linha é de setembro.
- **MG, pp. 20 e 21:** eleitores de Cleitinho, Flávio 60 → 71 e Lula 19 → 25 do 1º para o 2º turno. Saldo de +5 pontos para Flávio; sobre a urna de Cleitinho, +316.080 votos. Os 25% com Lula no 2º turno equivalem a 1.580.398 eleitores de Cleitinho.
- **RJ, pp. 12 e 13:** eleitores de Douglas Ruas, Flávio 82 → 91 e Lula 3 → 7 (saldo de +5 pontos; +213.560 votos). **Achado contrário:** eleitores de Eduardo Paes, Flávio 23 → 28 e Lula 56 → 64 (saldo de −3 pontos; −111.210 votos).

Onde cada governador mais superou Flávio, em votos (base para agenda conjunta):

- **SP, Tarcísio:** São Paulo +472.949, Guarulhos +43.187, Campinas +37.388, São Bernardo do Campo +34.004, São José dos Campos +32.289. O governador passou Flávio em 644 municípios, somando 1.573.850 votos.
- **PB, Lucas Ribeiro:** Campina Grande +27.350, Cajazeiras +20.799, Patos +15.249, Sousa +14.871, Monteiro +11.138. O governador passou Flávio em 222 municípios, somando 648.771 votos.
- **MG, Cleitinho Azevedo:** Divinópolis +22.720, Patos de Minas +13.463, Minas Novas +6.166, Ituiutaba +5.964, Paracatu +5.930. O governador passou Flávio em 774 municípios, somando 760.621 votos.
- **PA, Dr. Daniel:** Ananindeua +58.018, Belém +14.445, Abaetetuba +8.833, Cametá +6.662, Marituba +6.384. O governador passou Flávio em 89 municípios, somando 232.631 votos.
- **AL, JHC:** Maceió +64.843, Girau do Ponciano +5.514, Santana do Ipanema +5.005, Craíbas +3.688, São Miguel dos Campos +3.676. O governador passou Flávio em 86 municípios, somando 164.358 votos.
- **MS, Eduardo Riedel:** Corumbá +5.475, Miranda +2.772, Aquidauana +2.684, Japorã +2.330, Dourados +2.190. O governador passou Flávio em 65 municípios, somando 58.475 votos.

**Juízo editorial.** Agenda conjunta vale onde o vão é positivo e o governador não é aliado de Lula: SP com Tarcísio (São Paulo, Guarulhos e Campinas); MG com Cleitinho Azevedo (Divinópolis, Patos de Minas e Minas Novas); PA com Dr. Daniel (Ananindeua, Belém e Abaetetuba); AL com JHC (Maceió, Girau do Ponciano e Santana do Ipanema); MS com Eduardo Riedel (Corumbá, Miranda e Aquidauana). Fica de fora PB, onde o governador é aliado de Lula. Mesmo ali o vão é teto: parte do eleitor do governador vota Lula por escolha medida.

### Os sete 2º turnos estaduais

| UF | 1º colocado | 2º colocado | Eleitorado | Abstenção | Presidente (Flávio × Lula) | Margem de Flávio |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| AC | Mailza Assis (PP, centro-direita) 49,76% | Alan Rick (REPUBLICANOS, direita) 32,27% | 613.742 | 20,43% | 64,56% × 28,73% | +168.037 |
| AM | Omar Aziz (PSD, centro) 40,63% | Professora Maria do Carmo (PL, direita) 24,49% | 2.798.611 | 20,16% | 45,00% × 48,23% | −70.232 |
| DF | Celina Leão (PP, centro-direita) 49,93% | Leandro Grass (PT, esquerda) 34,47% | 2.258.320 | 18,90% | 51,31% × 38,11% | +233.989 |
| ES | Lorenzo Pazolini (REPUBLICANOS, direita) 49,65% | Ricardo Ferraço (MDB, centro) 34,06% | 2.991.650 | 21,37% | 54,78% × 37,76% | +383.166 |
| RJ | Douglas Ruas (PL, direita) 49,27% | Eduardo Paes (PSD, centro) 42,76% | 12.857.648 | 23,32% | 53,01% × 39,41% | +1.273.823 |
| RN | Allyson (UNIÃO, centro-direita) 36,94% | Cadu de Lula (PT, esquerda) 36,16% | 2.659.825 | 18,38% | 34,77% × 59,75% | −517.470 |
| TO | Professora Dorinha (UNIÃO, centro-direita) 45,52% | Vicentinho Júnior (PSDB, centro-esquerda) 43,94% | 1.182.023 | 18,34% | 50,44% × 43,42% | +65.312 |

**Verificado.** Em 2022, nas 12 UFs com 2º turno de governador (AL, AM, BA, ES, MS, PB, PE, RO, RS, SC, SE e SP), o comparecimento variou +0,47 ponto entre os turnos; nas outras 15, +0,24. A lista sai de `data/raw/tse_resultados/votacao_candidato_munzona_2022.zip`.

**Juízo editorial.** A arena que mais pesa é a disputa do RJ: 12.857.648 eleitores, Flávio +1.273.823 votos no 1º turno e um finalista da direita ou da centro-direita contra um da esquerda, da centro-esquerda ou aliado de Lula. DF, ES e TO repetem o desenho em escala menor, também em UFs que Flávio venceu. Em AM e RN o desenho é o mesmo, mas Lula venceu a UF: a disputa estadual mobiliza o eleitor do outro lado também. Em AC os dois finalistas são do mesmo bloco: não há polarização a explorar.

## 4. Senado e Câmara como argumento

**Verificado.** Na Câmara eleita, direita e centro-direita somam 292 das 513 cadeiras: acima da maioria absoluta (257) e abaixo dos três quintos de emenda constitucional (308). Esquerda e centro-esquerda somam 137; o centro, 84. PL 121, PT 70. No Senado de 2027, direita e centro-direita somam 52 de 81, acima dos três quintos (49); esquerda e centro-esquerda, 17. O PL terá 27 senadores, 19 eleitos agora. Fonte: `apuracao/data/boletins/final.json`, gerado em 05/10/2026, 03h29; UFs da Câmara ainda em alocação provisória: AM, MG e SP.

**Juízo editorial, a favor de Flávio.** Pela classificação de campo da casa, um presidente Flávio começa com maioria nas duas Casas sem depender do centro; a fidelidade de PP, União e Podemos a essa maioria é hipótese, não número. Um presidente Lula governaria contra 292 deputados e 52 senadores da direita e da centro-direita. O argumento é governabilidade: o eleitor de centro que quer estabilidade tem, na composição já eleita, um motivo concreto.

**Juízo editorial, achado contrário.** O mesmo número serve a Lula. Com Câmara e Senado à direita, o eleitor que teme concentração de poder pode votar Lula como contrapeso. A campanha de Flávio não deve vender a maioria como cheque em branco; deve vendê-la como fim do impasse.

**Verificado.** Âncoras de campanha. Deputados federais mais votados da direita e da centro-direita: Nikolas Ferreira (MG, PL) 3.119.318, 27,19% dos válidos; Lucas Pavanato (SP, PL) 3.038.438, 12,82% dos válidos; André Fernandes (CE, PL) 684.372, 12,39% dos válidos; Julia Zanatta (SC, PL) 560.223, 13,15% dos válidos; Jeffrey Chiquini (PR, NOVO) 425.399, 6,81% dos válidos; Lucas Polese (ES, PL) 419.735, 19,66% dos válidos; Delegado Caveira (PA, PL) 414.927, 8,58% dos válidos; Maurício Marcon (RS, PL) 379.834, 6,22% dos válidos; Dra. Alessandra Haber (PA, PODE) 272.856, 5,65% dos válidos; Guilherme Kilter (PR, NOVO) 269.832, 4,32% dos válidos. Senadores eleitos com mais votos nesse campo: Guilherme Derrite (SP, PP) 13.273.880; André do Prado (SP, PL) 12.703.089; Domingos Sávio (MG, PL) 4.968.829; Carlos Portinho (RJ, PL) 4.264.932; Carlos Jordy (RJ, PL) 3.912.405; Sanderson (RS, PL) 3.453.316; Marcel Van Hattem (RS, NOVO) 3.449.053; Filipe Barros (PR, PL) 3.148.583.

Os três deputados federais mais votados em cada UF e a âncora da direita (o mais votado da direita ou da centro-direita, com a parcela dos válidos da UF):

| UF | 1º | 2º | 3º | Âncora da direita |
| --- | --- | --- | --- | --- |
| AC | Socorro Neri (PP) 39.587 | Dr. Fábio Rueda (UNIÃO) 33.203 | Coronel Ulysses (UNIÃO) 33.155 | Socorro Neri (PP, 8,45%) |
| AL | Alvinho Lira (PP) 172.628 | Delegado Fabio Costa (PP) 165.649 | Luciano Amaral (PSD) 155.915 | Alvinho Lira (PP, 9,60%) |
| AM | Sargento Salazar (PL) 212.948 | Sidney Leite (PSD) 138.498 | Adail Filho (MDB) 137.148 | Sargento Salazar (PL, 10,04%) |
| AP | Felipe Show (UNIÃO) 34.587 | Josenildo (PDT) 26.453 | Aline Gurgel (UNIÃO) 25.501 | Felipe Show (UNIÃO, 7,51%) |
| BA | Pastor Sargento Isidório (AVANTE) 248.147 | Antonio Brito (PSD) 205.815 | Neto Carletto (AVANTE) 197.240 | Sandro Filho (PP, 2,02%) |
| CE | André Fernandes (PL) 684.372 | Tainah Marinho (PSB) 265.585 | Yury do Paredão (MDB) 261.291 | André Fernandes (PL, 12,39%) |
| DF | Fábio Felix (PSOL) 224.224 | Rafael Prudente (MDB) 119.427 | Alberto Fraga (PL) 118.579 | Alberto Fraga (PL, 7,09%) |
| ES | Lucas Polese (PL) 419.735 | Jack Rocha (PT) 142.187 | Dr. Bruno Resende (UNIÃO) 110.675 | Lucas Polese (PL, 19,66%) |
| GO | Bruno Peixoto (UNIÃO) 207.899 | Delegada Adriana Accorsi (PT) 177.103 | Fred Rodrigues (PL) 152.380 | Bruno Peixoto (UNIÃO, 5,76%) |
| MA | Pedro Lucas Fernandes (UNIÃO) 188.853 | Iracema Vale (MDB) 179.351 | Vinicius Ferro (MDB) 166.880 | Pedro Lucas Fernandes (UNIÃO, 4,75%) |
| MG | Nikolas Ferreira (PL) 3.119.318 | Ana Elisa (PT) 524.219 | Duda Salabert (PSOL) 229.535 | Nikolas Ferreira (PL, 27,19%) |
| MS | Camila Jara (PT) 154.157 | Marcos Pollon (PL) 140.129 | Rose Modesto (UNIÃO) 124.409 | Marcos Pollon (PL, 9,86%) |
| MT | Coronel Fernanda (PL) 205.064 | Professora Rosa Neide (PT) 140.351 | Fábio Garcia (UNIÃO) 139.777 | Coronel Fernanda (PL, 10,77%) |
| PA | Delegado Caveira (PL) 414.927 | Jader Filho (MDB) 326.617 | Dra. Alessandra Haber (PODE) 272.856 | Delegado Caveira (PL, 8,58%) |
| PB | Cabo Gilberto Silva (PL) 267.142 | Aguinaldo Ribeiro (PP) 180.720 | Ricardo Coutinho (PT) 163.277 | Cabo Gilberto Silva (PL, 11,11%) |
| PE | Pedro Campos (PSB) 261.555 | Jones Manoel (PSOL) 249.077 | Anderson Ferreira (PL) 185.429 | Anderson Ferreira (PL, 3,52%) |
| PI | Georgiano (PSD) 234.254 | Delegado Charles (PV) 184.763 | Castro Neto (MDB) 168.080 | Jadyel (REPUBLICANOS, 5,86%) |
| PR | Jeffrey Chiquini (NOVO) 425.399 | Guilherme Kilter (NOVO) 269.832 | Sargento Fahur (PL) 242.643 | Jeffrey Chiquini (NOVO, 6,81%) |
| RJ | Dr. Luizinho (PP) 213.904 | Rick Azevedo (PSOL) 191.371 | Lindbergh (PT) 181.768 | Dr. Luizinho (PP, 2,41%) |
| RN | Natália Bonavides (PT) 215.509 | Nina (PL) 185.248 | Benes Leocádio (UNIÃO) 171.396 | Nina (PL, 9,41%) |
| RO | Lucio Mosquini (PL) 158.421 | Coronel Chrisóstomo (PL) 51.487 | Thiago Flores (UNIÃO) 43.143 | Lucio Mosquini (PL, 16,93%) |
| RR | Marcos Jorge (REPUBLICANOS) 22.027 | Ítalo Otávio (REPUBLICANOS) 20.184 | Rodrigo Mesquita (PODE) 19.962 | Marcos Jorge (REPUBLICANOS, 6,91%) |
| RS | Maurício Marcon (PL) 379.834 | Fernanda Melchionna (PSOL) 280.262 | Giovani Cherini (PL) 234.171 | Maurício Marcon (PL, 6,22%) |
| SC | Julia Zanatta (PL) 560.223 | Ana Paula Lima (PT) 201.377 | Professor Pedro Uczai (PT) 164.389 | Julia Zanatta (PL, 13,15%) |
| SE | Yandra Moura (UNIÃO) 115.903 | Claudio Mitidieri (PSB) 105.865 | Joao Daniel (PT) 88.900 | Yandra Moura (UNIÃO, 8,94%) |
| SP | Lucas Pavanato (PL) 3.038.438 | Erika Hilton (PSOL) 1.596.472 | Sâmia Bomfim (PSOL) 583.107 | Lucas Pavanato (PL, 12,82%) |
| TO | Professora Janad Valcari (PP) 99.026 | Jair Farias (UNIÃO) 93.869 | Lucas Campelo (REPUBLICANOS) 85.376 | Professora Janad Valcari (PP, 10,92%) |

## 5. Riscos e achados contrários

**Verificado. Onde Flávio mais fica abaixo de Bolsonaro no 2º turno de 2022.** Em pontos: DF −7,50 (terceira via 10,58%); AC −5,74 (terceira via 6,71%); AP −5,70 (terceira via 8,62%); GO −5,11 (terceira via 15,34%); RR −5,02 (terceira via 6,08%); AM −3,90 (terceira via 6,77%). Em votos: SP −1.294.564; RJ −437.050; MG −363.762; PR −213.998; RS −159.402; GO −141.153. A única UF em que Flávio fica abaixo até do 1º turno de Bolsonaro: Distrito Federal.

**Verificado. Municípios grandes (mais de 100.000 válidos) onde Flávio ficou abaixo do 1º turno de Bolsonaro:** Luziânia (GO) −2,54; Goiânia (GO) −1,41; Recife (PE) −0,85; Cabo de Santo Agostinho (PE) −0,63; Olinda (PE) −0,53; Jaboatão dos Guararapes (PE) −0,46; Paulista (PE) −0,43; Brasília (DF) −0,34; Rio Branco (AC) −0,27; Camaragibe (PE) −0,20. Seis dos dez são de Pernambuco. Caiado teve 14,91% em Luziânia, 13,52% em Goiânia e 4,80% em Brasília, contra 2,18% no país.

**Verificado. Governador de direita ou centro-direita eleito onde Flávio perdeu:** AL, JHC (PSDB) eleito com 52,20%, e Lula 54,73% × Flávio 40,45%; PA, Dr. Daniel (PODE) eleito com 51,36%, e Lula 49,91% × Flávio 44,50%; PB, Lucas Ribeiro (PP, aliado de Lula) eleito com 64,30%, e Lula 61,31% × Flávio 33,07%. Nas três UFs o governador do bloco venceu e o presidenciável do bloco perdeu, na mesma urna.

**Comparecimento.**

| Região | 2022, 1º turno | 2026, 1º turno | 2026 − 2022 (pp) | 2022, entre turnos (pp) | Valor de +1 ponto em 2026 (saldo de Flávio) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Nordeste | 80,47% | 81,61% | +1,14 | +0,22 | −135.929 |
| Norte | 79,06% | 80,57% | +1,51 | −1,99 | +5.807 |
| Centro-Sul | 78,70% | 77,92% | −0,78 | +0,72 | +164.214 |

**Verificado.** Contra o 1º turno de 2022, o comparecimento de 2026 variou −0,78 ponto no Centro-Sul, +1,14 no Nordeste e +1,51 no Norte. Em 2022, entre os turnos, variou +0,72 no Centro-Sul, +0,22 no Nordeste e −1,99 no Norte; por UF, as maiores quedas foram AP −7,66, AC −5,98 e RR −5,22 e as maiores altas, MG +1,29, SC +1,01 e GO +0,98; a correlação entre a variação de cada UF e a parcela de Lula no 2º turno de 2022 foi de 0,20. **Hipótese.** Um ponto a mais de comparecimento nas 15 UFs de Flávio vale +174.158 votos de saldo; nas 12 de Lula, −140.066. Variação de 2022 = comparecimento do 2º turno menos o do 1º, mesmo eleitorado apto. Valor de 1 ponto em 2026 = saldo Flávio menos Lula se 1% do eleitorado apto a mais comparecer e votar como a própria UF votou no 1º turno (hipótese, não medição; o eleitor que falta não é o eleitor médio da UF).

**Verificado. Exterior.** Lula 47,57% × Flávio 43,49%, margem de 13.487 votos para Lula, com 330.882 válidos e comparecimento de 37,29% (era 43,72% no 1º turno de 2022). Não muda a conta nacional.

**Inferência. Incerteza da transferência.** As duas medições de Caiado discordam: Nexus Flávio 30 × Lula 36; Datafolha Flávio 42 × Lula 27. Entre as seis combinações de matriz e hipótese, a margem projetada vai de 3,90 a 5,42 milhões de votos. As linhas vêm de pesquisas de setembro. A central da casa, feita com o mesmo acervo de pesquisas, dava a Flávio +0,14 ponto sobre Lula nos válidos, e a urna deu +1,87. Em 2022 a média das pesquisas finais tinha superestimado a vantagem de Lula em 3,92 pontos (erro comum de 12 casas, `analysis/predicao_2026/erro_2022/erro_2022.json`). Nas duas eleições as pesquisas ficaram abaixo da urna na margem da direita; isso não diz em que direção erram as linhas de transferência, só que elas vêm de instrumentos que erraram.

**Inferência. Base.** 3,47% da base de Flávio trocando para Lula, ou 6,94% deixando de votar, zeram a margem central. É o número que a campanha deve vigiar.

## 6. Dez movimentos, do maior para o menor em votos esperados

**Juízo editorial.** A ordem é da casa. O número de cada movimento sai de uma regra escrita ao lado, sobre medição publicada, analogia declarada ou hipótese; nenhum é previsão. Os movimentos não se somam: o eleitor de Renan em São Paulo é o mesmo que a agenda com Tarcísio procura, e os movimentos territoriais (São Paulo, Minas, Rio, Nordeste) são o canal por onde passa parte do voto dos movimentos de terceira via. Só o comparecimento traz eleitor novo.

1. Colher o eleitor de Renan Santos: +1.271.709
2. Converter a não escolha da terceira via: +831.761
3. Agenda conjunta com Tarcísio em São Paulo: +724.594
4. Disputar o eleitor de Augusto Cury: +450.752
5. Nordeste: interior antes das capitais: +348.297
6. Agenda conjunta com Cleitinho em Minas: +316.080
7. Casar o 2º turno de Douglas Ruas com o de Flávio no Rio: +213.560
8. Fechar Zema e as candidaturas menores da direita: +174.623
9. Um ponto a mais de comparecimento nas 15 UFs de Flávio: +174.158
10. Disputar o eleitor de Caiado com Daniel Vilela em Goiás: +116.442

### 1. Colher o eleitor de Renan Santos

- **Votos esperados (saldo para Flávio): +1.271.709.** Regra: votos de Renan × (Flávio − Lula) da linha Nexus normalizada (Flávio 56 × Lula 8, soma 101).
- **Alvo:** 2.675.887 votos de Renan Santos (Missão).
- **Onde:** SP 804.310 (3,23%), MG 247.209 (2,06%), RJ 211.843 (2,26%), PR 177.434 (2,69%), RS 167.558 (2,61%).
- **Rótulo:** inferência sobre medição publicada (Nexus, p. 79).

### 2. Converter a não escolha da terceira via

- **Votos esperados (saldo para Flávio): +831.761.** Regra: margem com a não escolha votando na proporção da própria linha menos margem só com o medido.
- **Alvo:** parcela das linhas da Nexus em branco, nulo ou indecisa.
- **Teto endereçável:** 2.902.940 votos.
- **Rótulo:** hipótese declarada sobre medição publicada.

### 3. Agenda conjunta com Tarcísio em São Paulo

- **Votos esperados (saldo para Flávio): +724.594.** Regra: votos de Tarcísio × média do saldo entre as perguntas de 1º e 2º turno medido no eleitorado do governador aliado em MG (+5 pontos) e no RJ (+5 pontos); a transcrição da casa do relatório de SP (p. 4) só tem a linha de 1º turno, então a taxa é transportada.
- **Alvo:** 14.491.874 votos de Tarcísio; vão de 1.569.851 votos sobre Flávio.
- **Teto endereçável:** 1.569.851 votos.
- **Linha medida no 1º turno (Datafolha, SP p. 4):** eleitor de Tarcísio com Flávio 59%, com Lula 12%.
- **Onde:** São Paulo (+472.949), Guarulhos (+43.187), Campinas (+37.388), São Bernardo do Campo (+34.004), São José dos Campos (+32.289).
- **Rótulo:** hipótese (taxa medida em MG e RJ aplicada a SP).

### 4. Disputar o eleitor de Augusto Cury

- **Votos esperados (saldo para Flávio): +450.752.** Regra: média das linhas Nexus (Flávio 44 × Lula 30, soma 99) e Datafolha (Flávio 44 × Lula 32, soma 100) aplicadas aos votos de Cury.
- **Alvo:** 3.448.569 votos de Cury (Avante).
- **Faixa entre as duas medições:** +413.828 a +487.676.
- **Onde:** SP 892.368 (3,59%), MG 409.737 (3,42%), RJ 247.397 (2,64%), PR 205.095 (3,11%), BA 195.451 (2,28%).
- **Rótulo:** inferência sobre duas medições publicadas.

### 5. Nordeste: interior antes das capitais

- **Votos esperados (saldo para Flávio): +348.297.** Regra: saldo líquido de Bolsonaro entre turnos em 2022 por voto de terceira via, aplicado ao voto de terceira via de 2026, separado em interior e capitais.
- **Alvo:** 1.810.479 votos de terceira via no Nordeste, 1.313.323 no interior.
- **Partes:** interior +247.706, capitais +100.591.
- **Rótulo:** analogia histórica (uma eleição).

### 6. Agenda conjunta com Cleitinho em Minas

- **Votos esperados (saldo para Flávio): +316.080.** Regra: votos de Cleitinho × saldo entre as perguntas de 1º e 2º turno no eleitorado dele (Datafolha pp. 20–21: Flávio 60 → 71, Lula 19 → 25).
- **Alvo:** 6.321.590 votos de Cleitinho.
- **Teto endereçável:** 544.042 votos.
- **Onde:** Divinópolis (+22.720), Patos de Minas (+13.463), Minas Novas (+6.166), Ituiutaba (+5.964), Paracatu (+5.930).
- **Rótulo:** inferência sobre medição publicada.

### 7. Casar o 2º turno de Douglas Ruas com o de Flávio no Rio

- **Votos esperados (saldo para Flávio): +213.560.** Regra: votos de Ruas × saldo entre as perguntas de 1º e 2º turno no eleitorado dele (Datafolha pp. 12–13: Flávio 82 → 91, Lula 3 → 7).
- **Alvo:** 4.271.199 votos de Douglas Ruas.
- **Contraprova:** −111.210 votos do lado oposto, pela mesma regra.
- **Rótulo:** inferência sobre medição publicada.

### 8. Fechar Zema e as candidaturas menores da direita

- **Votos esperados (saldo para Flávio): +174.623.** Regra: linha de Zema na Nexus (Flávio 59 × Lula 13, soma 101) aplicada a Zema, DC e Democrata.
- **Alvo:** 383.412 votos.
- **Rótulo:** inferência sobre medição publicada.

### 9. Um ponto a mais de comparecimento nas 15 UFs de Flávio

- **Votos esperados (saldo para Flávio): +174.158.** Regra: 1% do eleitorado apto a mais, votando como a própria UF votou no 1º turno.
- **Alvo:** eleitor apto que faltou no 1º turno nas UFs que Flávio venceu.
- **Contraprova:** −140.066 votos do lado oposto, pela mesma regra.
- **Onde:** SP +44.107, PR +23.805, SC +23.106, RJ +16.611, RS +16.262.
- **Rótulo:** hipótese declarada.

### 10. Disputar o eleitor de Caiado com Daniel Vilela em Goiás

- **Votos esperados (saldo para Flávio): +116.442.** Regra: média das linhas Nexus (Flávio 30 × Lula 36, soma 99) e Datafolha (Flávio 42 × Lula 27, soma 100) aplicadas aos votos de Caiado.
- **Alvo:** 2.605.148 votos de Caiado, 472.041 em Goiás.
- **Faixa entre as duas medições:** −157.888 a +390.772.
- **Governador eleito em Goiás:** Daniel Vilela (MDB), 2.148.218 votos; vice e sucessor de Ronaldo Caiado.
- **Onde:** SP 579.571 (2,33%), GO 472.041 (12,33%), MG 230.423 (1,92%), RJ 199.844 (2,13%), PR 171.294 (2,60%).
- **Rótulo:** inferência sobre duas medições que discordam.

## O que mudaria esta leitura

- Uma matriz de transferência medida por UF. O acervo da casa tem a matriz nacional da Nexus e duas linhas nacionais do Datafolha; nenhuma diz para onde vai, em São Paulo ou em Goiás, o eleitor de Renan, Cury ou Caiado.
- A linha de 2º turno do eleitor de Tarcísio. A transcrição da casa tem a de Cleitinho e a de Ruas; a de São Paulo, que mais pesa, não está no acervo.
- Pesquisas do 2º turno com cruzamento pelo voto declarado no 1º turno. Com elas, as hipóteses deste capítulo viram medição.
