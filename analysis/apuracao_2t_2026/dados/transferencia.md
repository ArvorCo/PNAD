# Transferência de voto, 1º → 2º turno (presidente, 2026)

Gerado por `scripts/apuracao-2t-2026-transferencia.py` em 2026-10-26T07:06:08Z. Não editar à mão.

Rótulo: estimativa ecológica e matriz de hipótese: descreve agregados, não identifica o voto de nenhum eleitor; pede explicação, não prova.

## 1. A conta que as duas urnas fecham (fato)

- Lula 53.879.538 → 64.255.891 (10.376.353 a mais); Flávio 56.104.503 → 59.825.984 (3.721.481).
- Terceira via no 1º turno: 9.316.747; branco e nulo caíram 1.821.256; comparecimento subiu 2.959.831.
- Disponíveis: 14.097.834. Lula ficou com 73,6% do ganho líquido; Flávio com 26,4%.
- Parte de Flávio entre os dois: 51,01% → 48,21% (-2,80 pp).

## 2. Regressão ecológica (inferência)

- Principal (5566 municípios, efeito fixo de UF, pesos pelo eleitorado): de cada 100 eleitores a mais, Lula 61,8 (IC 95% 54,9 a 68,7), Flávio 35,5, branco/nulo 2,7.
- Terceira via (mesma regressão): Lula 48,4, Flávio 40,7, branco/nulo 10,9 por 100 votos.

| Especificação | n | Lula por 100 | IC 95% | Flávio | BN |
|---|---|---|---|---|---|
| Efeito fixo de UF (principal) | 5566 | 61,8 | 54,9 a 68,7 | 35,5 | 2,7 |
| Efeito fixo de região | 5567 | 53,3 | 46,1 a 60,5 | 42,1 | 4,6 |
| Sem efeito fixo | 5567 | 48,5 | 42,3 a 54,8 | 47,8 | 3,7 |
| Efeito fixo de UF, sem as capitais | 5541 | 64,5 | 58,6 a 70,4 | 31,6 | 3,9 |
| Efeito fixo de UF + votos de Lula e Flávio no 1º turno | 5566 | 61,7 | 53,3 a 70,2 | 35,3 | 2,9 |
| Efeito fixo de UF, sem AC, AP, AM e RR (abstenção subiu) | 5451 | 64,6 | 56,9 a 72,2 | 32,2 | 3,2 |
| Efeito fixo de UF, municípios com 50 mil eleitores ou mais | 492 | 62,0 | 47,4 a 76,7 | 38,0 | -0,0 |
| Efeito fixo de UF, cada município com o mesmo peso | 5566 | 61,0 | 55,6 a 66,4 | 34,8 | 4,2 |
| Seções (todas), efeito fixo de UF | 499115 | 58,5 | 53,5 a 63,5 | 38,3 | 3,2 |
| Seções (todas), efeito fixo de município | 499066 | 56,2 | 51,7 a 60,6 | 40,3 | 3,6 |
| Seções (todas), efeito fixo de zona | 499066 | 55,6 | 50,9 a 60,3 | 40,7 | 3,7 |
| Seções (amostra), efeito fixo de UF | 7539 | 52,4 | 46,7 a 58,1 | 43,8 | 3,8 |
| Seções (amostra), efeito fixo de município | 6134 | 50,9 | 45,3 a 56,5 | 45,0 | 4,2 |
| Seções (amostra), efeito fixo de zona | 6134 | 46,9 | 37,9 a 56,0 | 48,8 | 4,2 |

## 3. Matriz de hipótese (IPF por UF, abstenção fixa pela regressão)

- Voltaram (faltaram no 1º turno e votaram no 2º): 3,62 mi; Lula 59,7%, Flávio 37,5%, branco/nulo 2,8%.
- Faltaram no 2º depois de votar no 1º: 0,66 mi.
- Terceira via: Flávio 37,3% do estoque, Lula 52,5%, branco/nulo 9,7% (faixa de Flávio nas sensibilidades: 30,5 a 41,9%).
- Ganho fora da própria base: Lula 11,10 mi, Flávio 6,19 mi; razão 0,558 (faixa 0,475 a 0,612).
- Explica 0,28 pp (IC 0,11 a 0,45) dos 2,80 pp que Flávio perdeu entre os dois.

| Cenário | Voltaram (mi) | Lula entre eles | Terceira → Flávio | Razão de consolidação | Fidelidade L / F |
|---|---|---|---|---|---|
| Central | 3,62 | 59,7% | 37,3% | 0,558 | 98,7 / 95,6 |
| Fidelidade 0,93 | 3,62 | 59,7% | 41,9% | 0,612 | 97,4 / 93,8 |
| Fidelidade 0,99 | 3,62 | 59,7% | 30,5% | 0,475 | 99,3 / 97,5 |
| Abstenção, mínimo do IC | 3,62 | 54,0% | 36,4% | 0,566 | 98,7 / 95,5 |
| Abstenção, máximo do IC | 3,62 | 65,3% | 38,3% | 0,550 | 98,6 / 95,7 |
| Abstenção na escala da seção | 3,62 | 55,1% | 36,7% | 0,563 | 98,7 / 95,5 |
| Terceira via toda pela Nexus | 3,62 | 59,7% | 37,7% | 0,558 | 98,6 / 95,5 |
| Terceira via toda pelo Datafolha | 3,62 | 59,7% | 38,9% | 0,568 | 98,8 / 95,5 |
| Rotatividade dobrada | 4,28 | 58,2% | 37,4% | 0,575 | 98,2 / 95,0 |
| Branco e nulo pela Quaest | 3,62 | 59,7% | 37,0% | 0,575 | 98,3 / 95,1 |
| Abstenção também ajustada | 3,68 | 74,4% | 39,5% | 0,541 | 98,5 / 95,9 |

## 4. Contra as pesquisas

- Linhas publicadas da terceira via somada (6 ondas): Flávio de 43,0 a 50,5% do eleitorado, de 53,8 a 64,4% entre os que escolhem um finalista.
- Síntese da casa de 04/10: 62,2% da migração para Flávio.
- Mapa do voto útil (26/09): reserva de 2º turno de Flávio de 9,6 mi.

## 5. Limites

- Regressão ecológica: agregado para agregado, sensível à escala (município contra seção) e ao efeito fixo.
- A matriz depende da prior; só as razões impostas pelas margens sobrevivem à troca dela.
- Linhas de pesquisa são voto lembrado na mesma entrevista, sem bases publicadas por grupo.
- A rotatividade bruta (quem faltou num turno e votou no outro) não é observada; usamos o piso das seções.
