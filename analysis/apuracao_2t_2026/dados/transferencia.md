# Transferência de voto, 1º → 2º turno (presidente, 2026)

Gerado por `scripts/apuracao-2t-2026-transferencia.py` em 2026-10-26T16:12:14Z. Não editar à mão.

Rótulo: estimativa ecológica e matriz de hipótese: descreve agregados, não identifica o voto de nenhum eleitor; pede explicação, não prova.

## 1. A conta que as duas urnas fecham (fato)

- Lula 53.879.538 → 64.256.232 (10.376.694 a mais); Flávio 56.104.503 → 59.826.041 (3.721.538).
- Terceira via no 1º turno: 9.316.747; branco e nulo caíram 1.821.246; comparecimento subiu 2.960.239.
- Disponíveis: 14.098.232. Lula ficou com 73,6% do ganho líquido; Flávio com 26,4%.
- Parte de Flávio entre os dois: 51,01% → 48,21% (-2,80 pp).

## 2. Regressão ecológica (inferência)

- Principal (5570 municípios, efeito fixo de UF, pesos pelo eleitorado): de cada 100 eleitores a mais, Lula 62,5 (IC 95% 55,1 a 70,0), Flávio 34,8, branco/nulo 2,6.
- Terceira via (mesma regressão): Lula 48,9, Flávio 40,3, branco/nulo 10,8 por 100 votos.

| Especificação | n | Lula por 100 | IC 95% | Flávio | BN |
|---|---|---|---|---|---|
| Efeito fixo de UF (principal) | 5570 | 62,5 | 55,1 a 70,0 | 34,8 | 2,6 |
| Efeito fixo de região | 5571 | 54,0 | 47,2 a 60,9 | 41,1 | 4,9 |
| Sem efeito fixo | 5571 | 49,1 | 42,6 a 55,6 | 47,2 | 3,8 |
| Efeito fixo de UF, sem as capitais | 5544 | 64,5 | 58,6 a 70,4 | 31,6 | 3,9 |
| Efeito fixo de UF + votos de Lula e Flávio no 1º turno | 5570 | 62,3 | 53,6 a 71,1 | 34,8 | 2,9 |
| Efeito fixo de UF, sem AC, AP, AM e RR (abstenção subiu) | 5455 | 65,5 | 57,1 a 73,8 | 31,4 | 3,1 |
| Efeito fixo de UF, municípios com 50 mil eleitores ou mais | 494 | 63,0 | 48,1 a 78,0 | 37,1 | -0,1 |
| Efeito fixo de UF, cada município com o mesmo peso | 5570 | 61,0 | 55,6 a 66,4 | 34,7 | 4,2 |
| Seções (todas), efeito fixo de UF | 499115 | 58,5 | 53,5 a 63,5 | 38,3 | 3,2 |
| Seções (todas), efeito fixo de município | 499066 | 56,2 | 51,7 a 60,6 | 40,3 | 3,6 |
| Seções (todas), efeito fixo de zona | 499066 | 55,6 | 50,9 a 60,3 | 40,7 | 3,7 |
| Seções (amostra), efeito fixo de UF | 7539 | 52,4 | 46,7 a 58,1 | 43,8 | 3,8 |
| Seções (amostra), efeito fixo de município | 6134 | 50,9 | 45,3 a 56,5 | 45,0 | 4,2 |
| Seções (amostra), efeito fixo de zona | 6134 | 46,9 | 37,9 a 56,0 | 48,8 | 4,2 |

## 3. Cenários de cruzamento entre as bases (IPF por UF)

- Padrão: Sem cruzamento; fecha as duas urnas em todas as UFs e no exterior; é o que a Quaest publicou (21/10, p. 20) nas duas direções e fica abaixo das linhas da Nexus (de 1,0% a 2,1%) (desvio máximo 0,0010 voto).
- Linhas de base publicadas: Lula → Flávio de 0,0 a 2,1%; Flávio → Lula de 0,0 a 2,0%.
- Não muda: voltaram 3,62 mi, Lula entre eles 60,3%; Lula recebeu da terceira via, do branco e nulo e do saldo entre as bases de 8,65 a 8,67 mi.
- Muda pouco: terceira via para Flávio de 32,5 a 33,3%.
- Muda: razão de consolidação de 0,494 a 0,547; fidelidade de Flávio de 95,0 a 97,1%.

| Cenário | Lula → Flávio | Flávio → Lula | Terceira → Flávio | Terceira → Lula | Razão | Fidelidade L / F |
|---|---|---|---|---|---|---|
| Sem cruzamento | 0,00% | 0,00% | 32,5% | 57,7% | 0,494 | 99,1 / 97,1 |
| 1% de cada base cruza | 1,00% | 1,00% | 32,9% | 57,4% | 0,522 | 98,1 / 96,1 |
| 2% de cada base cruza | 2,00% | 2,00% | 33,3% | 57,0% | 0,547 | 97,2 / 95,0 |
| O que as pesquisas mediram | 0,70% | 0,85% | 33,2% | 56,9% | 0,519 | 98,4 / 96,2 |

Cenário padrão, de cada 100 eleitores de cada origem do 1º turno (brancos e nulos somados):

| Origem | Votos no 1º turno | Lula | Flávio | Branco e nulo | Abstenção |
|---|---|---|---|---|---|
| Lula | 53.879.409 | 99,1 | 0,0 | 0,6 | 0,3 |
| Flávio | 56.104.549 | 0,0 | 97,1 | 2,1 | 0,8 |
| Augusto Cury | 3.448.571 | 65,4 | 25,3 | 8,8 | 0,4 |
| Renan Santos | 2.675.896 | 49,9 | 37,3 | 12,3 | 0,5 |
| Ronaldo Caiado | 2.605.151 | 52,9 | 38,4 | 8,3 | 0,4 |
| Romeu Zema | 326.489 | 46,4 | 47,1 | 6,2 | 0,3 |
| Demais | 260.657 | 99,6 | 0,1 | 0,1 | 0,2 |
| Brancos e nulos | 5.975.042 | 55,0 | 16,6 | 27,9 | 0,5 |
| Não votou | 33.469.314 | 6,5 | 4,0 | 0,3 | 89,2 |

## 4. Matriz de hipótese, cenário padrão (IPF por UF, abstenção fixa pela regressão)

- Voltaram (faltaram no 1º turno e votaram no 2º): 3,62 mi; Lula 60,3%, Flávio 37,0%, branco/nulo 2,8%.
- Faltaram no 2º depois de votar no 1º: 0,66 mi.
- Terceira via: Flávio 32,5% do estoque, Lula 57,7%, branco/nulo 9,4% (faixa de Flávio nas sensibilidades: 31,2 a 33,8%).
- Ganho fora da própria base: Lula 10,85 mi, Flávio 5,36 mi; razão 0,494 (faixa 0,489 a 0,547).
- Explica 0,30 pp (IC 0,11 a 0,48) dos 2,80 pp que Flávio perdeu entre os dois.

| Cenário | Voltaram (mi) | Lula entre eles | Terceira → Flávio | Razão de consolidação | Fidelidade L / F |
|---|---|---|---|---|---|
| Central (sem cruzamento) | 3,62 | 60,3% | 32,5% | 0,494 | 99,1 / 97,1 |
| Abstenção, mínimo do IC | 3,62 | 54,2% | 31,2% | 0,499 | 99,2 / 97,0 |
| Abstenção, máximo do IC | 3,62 | 66,4% | 33,8% | 0,489 | 99,1 / 97,2 |
| Terceira via toda pela Nexus | 3,62 | 60,3% | 33,0% | 0,498 | 99,1 / 97,0 |
| Terceira via toda pelo Datafolha | 3,62 | 60,3% | 33,2% | 0,497 | 99,2 / 97,1 |
| Abstenção na escala da seção | 3,62 | 55,1% | 31,5% | 0,498 | 99,2 / 97,0 |
| Rotatividade dobrada | 4,28 | 58,7% | 32,9% | 0,517 | 98,7 / 96,4 |
| Branco e nulo pela Quaest | 3,62 | 60,3% | 33,1% | 0,519 | 98,8 / 96,4 |
| Abstenção também ajustada | 3,72 | 77,8% | 36,1% | 0,483 | 99,0 / 97,2 |
| Cruzamento escolhido pelo ajuste | 3,62 | 60,3% | 37,4% | 0,557 | 98,7 / 95,6 |

## 5. Contra as pesquisas

- Linhas publicadas da terceira via somada (6 ondas): Flávio de 43,0 a 50,5% do eleitorado, de 53,8 a 64,4% entre os que escolhem um finalista.
- Para a terceira via dar 43,0% a Flávio, ele teria de perder para Lula, em saldo, 3,10% da base (1,74 mi).
- Para a terceira via dar 50,5% a Flávio, ele teria de perder para Lula, em saldo, 5,29% da base (2,97 mi).
- Síntese da casa de 04/10: 62,2% da migração para Flávio.
- Mapa do voto útil (26/09): reserva de 2º turno de Flávio de 9,6 mi.

## 6. Limites

- Regressão ecológica: agregado para agregado, sensível à escala (município contra seção) e ao efeito fixo.
- A matriz depende da prior; só as razões impostas pelas margens sobrevivem à troca dela.
- Linhas de pesquisa são voto lembrado na mesma entrevista, sem bases publicadas por grupo.
- A rotatividade bruta (quem faltou num turno e votou no outro) não é observada; usamos o piso das seções.
