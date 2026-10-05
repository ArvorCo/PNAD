# Pesquisas, previsões da Arvor e voto útil contra a urna

1º turno presidencial de 04/10/2026. Memorando interno para o dossiê `docs/apuracao_1o_turno_2026.html`. Gerado por `python3 scripts/apuracao-2026-pesquisas.py`; números em `analysis/apuracao_2026/dados/pesquisas_vs_urna.json` e `voto_util.json`. Erro = pesquisa menos urna, em pontos dos votos válidos; na diferença L−F, positivo superestima Lula.

## 1. A urna

Arquivo nacional do TSE gerado em 05/10 às 02:59 (Brasília) (SHA-256 `07c3cc03e99e317e…`), 499.248 de 499.248 seções, o mesmo corte de `apuracao/data/boletins/final.json`. Flávio 47,03, Lula 45,16, Cury 2,89, Renan Santos 2,24, Caiado 2,18, Zema 0,27; terceira via 7,81. Diferença L−F: −1,87 ponto, 2.224.965 votos a favor de Flávio.

Pesquisas nos válidos pela regra da Arvor: candidaturas renormalizadas para 100, sem indecisos nem branco e nulo. EAM 5 = erro absoluto médio nas cinco candidaturas com 2% ou mais na urna (vazio quando o instituto agrupa nomes em "outros"). Margem AAS = margem de 95% da diferença sob amostragem simples, piso da incerteza.

## 2. Pesquisas com campo encerrado de 25/09 a 03/10

Ordenadas pelo erro absoluto na diferença L−F publicada. ● = última onda do instituto.

| # | Instituto | Campo | Flávio | Lula | Erro F | Erro L | Erro L−F | Erro L−F reponderado | EAM 5 | Margem AAS |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Gerp | 24–28/09 | 44,21 | 42,11 | −2,82 | −3,06 | −0,24 | −3,05 | 2,03 | 3,81 |
| 2 | Futura ● | 02–03/10 | 44,74 | 42,63 | −2,29 | −2,53 | −0,24 | sem renda | 1,65 | 4,20 |
| 3 | Gerp ● | 30/09–02/10 | 45,74 | 43,62 | −1,28 | −1,55 | −0,26 | −3,20 | 1,06 | 3,90 |
| 4 | Vox Brasil ● | 29/09–01/10 | 45,88 | 44,99 | −1,15 | −0,17 | +0,97 | sem renda | 0,91 | 4,30 |
| 5 | Futura | 25–29/09 | 44,42 | 41,47 | −2,61 | −3,69 | −1,08 | sem renda | 2,11 | 4,17 |
| 6 | Palver ● | 30/09–03/10 | 46,85 | 43,28 | −0,18 | −1,88 | −1,70 | −1,39 | 1,94 | 2,64 |
| 7 | Palver | 24–27/09 | 44,32 | 44,73 | −2,71 | −0,43 | +2,28 | +2,28 | 2,38 | 2,63 |
| 8 | Meio/Ideia ● | 25–28/09 | 39,06 | 40,08 | −7,96 | −5,08 | +2,88 | sem renda | 4,32 | 3,93 |
| 9 | PoderData ● | 30/09–02/10 | 44,09 | 45,16 | −2,94 | 0,00 | +2,94 | +0,91 | 0,86 | 3,04 |
| 10 | Datafolha ● | 02–03/10 | 43,48 | 45,65 | −3,55 | +0,49 | +4,04 | −1,07 | 1,52 | 3,05 |
| 11 | Quaest ● | 02–03/10 | 43,68 | 45,98 | −3,35 | +0,81 | +4,16 | +5,69 | 1,44 | 3,27 |
| 12 | AtlasIntel ● | 27/09–02/10 | 44,02 | 46,93 | −3,01 | +1,77 | +4,78 | +4,79 | 1,74 | 2,66 |
| 13 | AtlasIntel | 23–28/09 | 43,11 | 46,27 | −3,92 | +1,11 | +5,03 | +6,01 | 1,86 | 2,65 |
| 14 | Vox Brasil | 26–28/09 | 42,14 | 45,82 | −4,89 | +0,66 | +5,54 | sem renda | 1,76 | 4,23 |
| 15 | Real Time Big Data ● | 26–30/09 | 41,49 | 45,74 | −5,54 | +0,58 | +6,12 | +0,57 | 1,89 | 4,22 |
| 16 | Datafolha | 29/09–01/10 | 40,86 | 45,16 | −6,17 | 0,00 | +6,17 | +0,89 | 1,92 | 3,76 |
| 17 | Nexus ● | 25–27/09 | 38,95 | 44,21 | −8,08 | −0,95 | +7,13 | +6,56 | 3,29 | 4,09 |
| 18 | MDA ● | 30/09–02/10 | 42,18 | 47,84 | −4,85 | +2,67 | +7,53 | +5,27 | 1,98 | 4,37 |
| 19 | Indexa/Broadcast ● | 27–29/09 | 40,00 | 45,88 | −7,03 | +0,72 | +7,75 | +6,18 | 2,67 | 4,40 |
| 20 | Quaest | 24–27/09 | 40,00 | 45,88 | −7,03 | +0,72 | +7,75 | +9,42 | não abre | 4,39 |

| Referência | Flávio | Lula | Terceira via | Erro L−F |
|---|---|---|---|---|
| Última onda de cada casa, publicada | 43,09 | 44,77 | 12,14 | +3,55 |
| Agregador Arvor de 04/10, publicado | 43,05 | 45,43 | 11,52 | +4,25 |
| Agregador Arvor de 04/10, reponderado por renda | 43,88 | 44,45 | 11,67 | +2,43 |
| Central da Arvor (04/10) | 45,26 | 45,12 | 9,63 | +1,72 |
| Âncora dinâmica (DLM) | 44,01 | 44,42 | 11,57 | +2,27 |
| Erro comum de 2022 (12 casas, L−Bolsonaro) |  |  |  | +3,92 |

## 3. Proximidade não é acerto

**Parágrafo a publicar.** Na última onda, Futura e Gerp terminaram a 0,24 e 0,26 ponto da diferença entre Lula e Flávio na urna. Isso não prova que medem melhor. Uma eleição é uma observação. Em 2022 a média de 12 casas superestimou a vantagem de Lula em +3,92 pontos dos válidos; em 2026 a última onda de 13 casas superestimou em +3,55, na mesma direção. Antes da urna, as casas mais próximas eram justamente as que mais se afastavam das demais a favor de Flávio (desvio relativo medido pela Arvor antes da eleição: Futura −5,7, Gerp −5,2 pontos na diferença L−F). Chegaram perto porque o erro comum foi grande e contrário ao desvio delas. Com os erros espalhados como foram (média +3,55, desvio 3,15 entre casas), a chance de ao menos uma de 13 casas cair a meio ponto da urna só pela dispersão seria de 60%. Quem chegou mais perto desta vez errou na direção certa desta vez.

- Dois testes para chamar uma casa de certeira: o erro na diferença dentro da margem da própria amostra em 2026 (passam 6 das 13 últimas ondas, sob amostragem simples) e o mesmo em 2022. Só Futura passa nos dois (Futura: −2,13 em 2022 e −0,24 em 2026). Das 8 casas com onda final arquivada nas duas eleições, todas repetiram o sinal do erro e 7 superestimaram Lula nas duas (correlação 0,51 entre os erros das duas eleições). Com o erro comum duas vezes a favor de Lula, uma casa inclinada para o outro lado parece certeira duas vezes. Separar método de inclinação exige uma eleição em que o erro comum vá para o outro lado.
- Verificado: erros de cada onda contra o TSE, na tabela acima.
- Inferido: o desvio relativo de cada casa medido antes da urna ordena os erros (correlação 0,88 em 13 casas), mas por construção não diz nada do nível. Descontado esse desvio, o componente comum foi +4,24 pontos.
- Hipótese ilustrativa: a chance de 60% supõe erros normais independentes com a média e o desvio observados.

## 4. O erro comum se repetiu

| Conjunto | Casas | Erro médio L−F | Mediana | Desvio entre casas | Superestimaram Lula |
|---|---|---|---|---|---|
| 2022, última onda de cada instituto | 12 | +3,92 | +4,96 | 4,96 | 10 de 12 |
| 2026, última onda, publicada | 13 | +3,55 | +4,04 | 3,15 | 10 de 13 |
| 2026, última onda, reponderada | 10 | +2,43 | +2,85 | 3,65 | 7 de 10 |

- Verificado: o sinal e o tamanho do erro comum de 2022 se repetiram. Em 2022 o erro foi concentrado em Bolsonaro; em 2026, em Flávio (seção 6).
- Verificado: a dispersão entre casas (3,15 pontos) é maior que a esperada só pela amostragem (1,91 sob amostragem simples, 2,34 com efeito de desenho 1,5). 7 das 13 últimas ondas erraram a diferença por mais que a margem de 95% da própria amostra sob amostragem simples. Efeito de casa existe e é grande.
- Descritivo, sem teste: erro médio por modo de coleta, online +1,54 (2 casas); presencial +4,18 (4 casas); telefone +3,76 (7 casas). Com duas a sete casas por grupo, isso não separa modo de casa.

## 5. O que a reponderação por renda fez

| Instituto (última onda) | Erro L−F publicado | Erro L−F reponderado | Deslocamento L−F | Efeito | Perfil de renda |
|---|---|---|---|---|---|
| AtlasIntel | +4,78 | +4,79 | +0,01 | neutro |  |
| Datafolha | +4,04 | −1,07 | −5,11 | aproximou | perfil da onda anterior (hipótese) |
| Gerp | −0,26 | −3,20 | −2,94 | afastou |  |
| Indexa/Broadcast | +7,75 | +6,18 | −1,57 | aproximou |  |
| MDA | +7,53 | +5,27 | −2,25 | aproximou |  |
| Nexus | +7,13 | +6,56 | −0,57 | aproximou |  |
| Palver | −1,70 | −1,39 | +0,31 | aproximou | perfil reconstituído |
| PoderData | +2,94 | +0,91 | −2,03 | aproximou |  |
| Quaest | +4,16 | +5,69 | +1,53 | afastou | perfil da onda anterior (hipótese) |
| Real Time Big Data | +6,12 | +0,57 | −5,55 | aproximou |  |

- Verificado: no agregador de 04/10 (10 ondas), o erro na diferença L−F cai de +4,25 (publicado) para +2,43 (renda trocada pela PNAD). Nas últimas ondas, 7 de 10 se aproximaram da urna, 2 se afastaram (Gerp, Quaest) e 1 ficou parada. O deslocamento médio foi de −1,82 ponto na diferença L−F, a favor de Flávio.
- Contraprova publicada com o mesmo destaque: a Quaest se afastou, porque a amostra dela é mais rica que o país e a troca da renda empurra para Lula. A Gerp passou do ponto: estava a 0,26 da urna e foi para −3,20.
- Juízo editorial: a reponderação por renda corrigiu a direção do erro comum e cerca de 43% do tamanho dele no agregador. Não corrigiu tudo: a média reponderada ainda erra +2,43. É sensibilidade de uma margem, não resultado corrigido.
- Ressalva: Datafolha e Quaest de 03/10 usaram o perfil de renda da onda anterior como hipótese declarada, porque o painel do contratante não publica o perfil.

## 6. O que a previsão da Arvor acertou e errou

Central publicada na madrugada de 04/10 (docs/assets/predicao_2026_1T_presidente.json, gerada 2026-10-04T01:22:40-03:00): Flávio 45,26, Lula 45,12, terceira via 9,63. Urna: 47,03, 45,16 e 7,81.

- Verificado: Lula ficou a 0,05 ponto da central. Flávio teve 1,77 pontos a mais do que a central. O erro na diferença L−F foi +1,72, menor que o da média das pesquisas publicadas (+3,55) e da média reponderada (+2,43). 4 das 13 últimas ondas tiveram erro menor em módulo.
- Verificado: a diferença da urna (Flávio +1,87) caiu no percentil 77 da distribuição da Arvor, dentro do intervalo de 90% (−3,88 a +3,97). A Arvor dava 52% de chance de Flávio terminar à frente: não previu o vencedor do 1º turno, disse que era empate.
- Verificado: o ponto mais fraco da Arvor foi a consolidação. A terceira via da urna (7,81) ficou abaixo do percentil 5 da Arvor (8,67); Flávio e Lula ficaram dentro dos intervalos de 90%. Pela decomposição da seção 8, a consolidação explica de +0,50 a +0,93 dos +1,72 de erro na diferença; o resto é deslocamento entre os finalistas.
- Verificado, com ressalva de seleção: a sensibilidade publicada mais próxima da urna foi "Flávio antecipa 25% da reserva" (erro L−F +0,01). Ela é uma entre 23 sensibilidades; escolher a melhor depois da urna não é acerto. A de 2022 repetido erra −2,20: passou do ponto.
- Verificado: a âncora dinâmica (DLM) errou +2,27, mais que a central; a urna ficou a 1,0 desvio da margem dela.
- Comparecimento previsto 125,45 milhões, urna 125,28; branco e nulo previstos 5,51 milhões, urna 5,98.

| Região | Flávio previsto | Flávio urna | Erro F | Lula previsto | Lula urna | Erro L | Erro L−F |
|---|---|---|---|---|---|---|---|
| Centro-Sul (SE, S, CO) | 51,24 | 54,02 | −2,77 | 37,90 | 36,87 | +1,03 | +3,81 |
| Nordeste | 30,77 | 30,85 | −0,08 | 61,97 | 63,77 | −1,80 | −1,72 |
| Norte | 48,35 | 49,15 | −0,80 | 43,61 | 44,65 | −1,04 | −0,23 |
| Exterior | 42,05 | 43,49 | −1,44 | 43,41 | 47,57 | −4,15 | −2,72 |

- Verificado: o erro está no Centro-Sul, onde a Arvor deu a Flávio 2,77 pontos a menos. No Nordeste o sinal se inverte: Lula teve 1,80 pontos a mais que a central. O Norte ficou a 0,23 ponto.
- Verificado: o líder previsto venceu em 25 das 27 UFs; os erros foram AM e AP. Flávio foi subestimado em 22 UFs. Maiores erros na diferença L−F: PI −6,58, RS +6,30, GO +6,22, SC +5,74, BA −5,15, SE −4,98.
- Inferido: a urna foi mais polarizada por UF do que a previsão. Para cada 10 pontos de vantagem de um lado na UF, o erro da central andou 0,66 ponto a favor daquele lado (correlação −0,53 em 27 UFs, sem peso).

## 7. Governadores e Senado

**Governadores** (docs/assets/predicao_governador.json contra o TSE; situação provisória em AL, AM).

- Verificado: o líder previsto liderou a urna em 24 das 27 UFs; erros em AC, AL, RJ. Nos 7 estados com 2º turno, o par que vai à disputa era o par mais provável da Arvor em 7.
- Verificado: 20 UFs decididas no 1º turno, contra 17,6 esperadas (intervalo de 90% de 14 a 21). Brier da probabilidade de decidir no 1º turno: 0,127, contra 0,250 de uma moeda.
- Verificado: o voto do líder da urna caiu dentro do intervalo de 90% da Arvor em 27 das 27 UFs.
- Inferido: houve concentração nos líderes também nos estados. O líder previsto teve, em média, 2,80 pontos dos válidos a mais do que a Arvor previu. A medida usa o líder previsto, não o vencedor, para não carregar viés de seleção.

**Senado** (docs/assets/predicao_senado.json contra o TSE; duas vagas por UF; provisório em AM).

- Verificado: as duas candidaturas mais prováveis de cada UF levaram 42 das 54 vagas, contra 36,5 esperadas pelas próprias probabilidades da Arvor. A dupla inteira saiu certa em 15 UFs. Cobertura recente: 33 de 40; cobertura antiga: 9 de 14.
- Verificado: Brier de 0,0569 sobre 303 candidaturas. Referências: 0,0930 para "as duas primeiras da média com certeza" (40 vagas) e 0,1457 para probabilidade igual a todas.
- Calibração por faixa de probabilidade: de 10% a 30%, 2 eleitas contra 5,4 esperadas em 26 candidaturas; de 30% a 50%, 11 eleitas contra 10,1 esperadas em 25 candidaturas; de 50% a 70%, 17 eleitas contra 16,0 esperadas em 28 candidaturas; de 70% a 90%, 24 eleitas contra 21,4 esperadas em 27 candidaturas. A Arvor foi conservadora nas duas pontas: o improvável aconteceu menos e o provável aconteceu mais do que ela previu. Juízo: com cerca de 25 candidaturas por faixa, a diferença é pequena demais para chamar de descalibração.
- Maiores surpresas eleitas: Samanda de Lula (RN, 24%), Bruno Scheid (RO, 27%), Lahesio Bonfim (MA, 36%), Delegado Alessandro (SE, 37%). Favoritas que ficaram de fora: Roseana Sarney (MA, 78%), Alexandre Curi (PR, 71%), Capitão Alberto Neto (AM, 71%), André Moura (SE, 63%).

## 8. Voto útil: o que a urna mostrou

**Terceira via.** A última onda de 13 casas deu à terceira via 12,14 pontos dos válidos (11,67 reponderada, 10 casas). A urna deu 7,81. Nenhuma onda final ficou abaixo da urna; a mais baixa foi AtlasIntel, com 9,05. A média móvel de 7 dias do agregador caiu de 20,58 (15/09) para 10,36 (04/10); a urna continuou a queda. A central da Arvor (9,63) já tinha consolidação projetada e ainda assim ficou acima do próprio percentil 5 (8,67).

**Quem perdeu.** Contra a média das últimas ondas: Renan Santos −1,38 (−38% do que tinha); Caiado −1,20 (−35% do que tinha); Cury −0,69 (−19% do que tinha); Zema −0,63 (−70% do que tinha); demais −0,44 (−67% do que tinha). Quem recebeu: Flávio +3,94 e Lula +0,39 pontos dos válidos, em média, sobre o que cada pesquisa final deu a eles.

**Reserva de 2º turno.** Na mesma pesquisa, Flávio tinha em média 6,06 pontos a mais no 2º turno do que no 1º; Lula, 3,77. Pela contabilidade do mapa do voto útil, a urna revelou no 1º turno a mediana de 61% da reserva de Flávio (13 casas, de 7% a 118%) e 12% da de Lula. O voto útil foi de um lado só. Com os estados de 26/09, o mapa precisaria de λ = 0,82 e θ = 0,41 (versão calibrada) ou λ = 1,03 e θ = 0,18 (sem calibração) para reproduzir a urna; o cenário publicado mais próximo foi "Três quartos do voto útil" na versão calibrada e "Voto útil completo" na sem calibração.

**Decomposição do erro na diferença L−F.**

| Ponto de partida | Erro L−F | Queda da terceira via | Consolidação (Nexus) | Faixa entre variantes | Resíduo | Sem matriz |
|---|---|---|---|---|---|---|
| Última onda de 13 casas, publicada | +3,55 | 4,33 | +1,46 | +0,94 a +1,83 | +2,09 | −0,07 |
| Agregador de 04/10, publicado | +4,25 | 3,71 | +1,33 | +0,84 a +1,64 | +2,92 | −0,09 |
| Agregador de 04/10, reponderado | +2,43 | 3,86 | +1,47 | +0,95 a +1,77 | +0,96 | −0,02 |
| Central da Arvor | +1,72 | 1,82 | +0,77 | +0,50 a +0,93 | +0,95 | 0,00 |

- Estimativa, não medição: na última onda das 13 casas, a consolidação da terceira via explica de +0,94 a +1,83 dos +3,55 pontos de erro na diferença L−F, de 27% a 52%. O resto, de +1,72 a +2,60, é deslocamento entre os dois finalistas que a consolidação não explica: efeito de casa, movimento de última hora entre Lula e Flávio, comparecimento diferencial. Os dados não separam esses três.
- Sem matriz (cada ponto da terceira via repartido na proporção do placar), a consolidação explica perto de zero: o ganho de Flávio vem de a terceira via ser mais próxima dele, não de ela encolher.
- Por UF, a partir da central: o resíduo favorece Flávio no Sul e no Centro-Oeste (SC +5,68, RS +5,66, MS +4,24, GO +4,12) e favorece Lula no Nordeste (PI −7,01, SE −6,20, BA −5,42, AM −4,49). É o mesmo padrão de polarização da seção 6.

**Hipóteses declaradas.** (1) A linha de 2º turno de cada eleitorado (Nexus, 18 a 20/09, p. 79) vale para quem abandonou o candidato no 1º turno. (2) Variante principal: quem saiu e votou foi a Flávio ou Lula na razão da linha; variante com vazamento: a parte que iria a branco, nulo ou indeciso saiu dos válidos; variante Datafolha: Caiado com 42 a Flávio e 27 a Lula. (3) Candidaturas menores e "outros" sem linha publicada: meio a meio. (4) Abstenção não é modelada: quem deixou de votar aparece como resíduo. (5) A reserva por UF vem das pesquisas estaduais de setembro e carrega o movimento posterior.

**Conclusão com incerteza.** O voto útil existiu e foi assimétrico: a terceira via perdeu 4,33 pontos dos válidos entre as pesquisas finais e a urna, e a maior parte foi a Flávio. A consolidação explica de 27% a 52% do erro das pesquisas na diferença entre os dois. O resto é deslocamento entre os finalistas, com o mesmo sinal do erro comum de 2022. A estimativa depende de uma matriz medida por um instituto duas semanas antes da eleição e aplicada ao 1º turno.

## 9. Limites

- Uma eleição é uma observação. Nenhum ranking desta página mede a qualidade de um método; mede o erro de uma onda num dia.
- Reponderação por renda é sensibilidade de uma margem, sem microdados nem pesos individuais.
- A decomposição do voto útil é contabilidade sob hipóteses, não medição de eleitor.
- Governador em AL e AM e Senado no AM estavam sem marca final do TSE no momento do corte e usam a situação provisória pela regra da eleição.

## 10. Reprodução

```
python3 scripts/apuracao-2026-pesquisas.py
pytest -q tests/test_apuracao_2026_pesquisas.py
```
