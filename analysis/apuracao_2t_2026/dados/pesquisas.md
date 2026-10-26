# Pesquisas, centrais e projeções contra a urna do 2º turno de 2026

Gerado por `python3 scripts/apuracao-2t-2026-pesquisas.py`. Não editar à mão: o script regrava este arquivo e os três JSON ao lado.

Urna: `analysis/apuracao_2t_2026/dados/presidente.json` (sha256 `9eec711a4b12318a`).

Convenção: erro = pesquisa menos urna, em pontos dos votos válidos. Na diferença Flávio menos Lula (F−L), positivo quer dizer que a pesquisa pôs Flávio mais à frente do que a urna. O 1º turno e 2022 usaram L−F; para comparar, troque o sinal.

## 1. O que a urna devolveu (fato)

- Lula 64.255.891 × Flávio 59.825.984 votos; 51,79% × 48,21% dos válidos; F−L = −3,57 pp.
- Sem exterior (universo das pesquisas e das centrais): Lula 51,78% × Flávio 48,22%.
- Abstenção 19,22% contra 21,08% no 1º turno (−1,86 pp); comparecimento +2,96 milhões de eleitores. Nos 5.753 municípios já fechados: 19,26% contra 21,10% nos mesmos municípios.

## 2. Os números mais fortes

1. Erro comum das 20 casas (última onda, campo de 19 a 24/10): +5,53 pp em F−L; mediana +5,05.
2. Todas as 20 casas erraram para o mesmo lado: 20 superestimaram Flávio, nenhuma superestimou Lula.
3. 18 de 20 casas tinham Flávio à frente nos válidos; 2 acertaram o vencedor (Colectta, Vox Brasil).
4. Dispersão entre casas 1,69 pp, abaixo do desvio que só a amostragem simples produziria (2,06): o erro é comum, não de uma casa.
5. 16 de 20 erros ficam fora da margem de 95% da diferença sob amostragem simples.
6. Válidos oficiais das casas: erro comum +5,67 (19 casas).
7. Reponderação por renda (PNAD): 9 de 11 casas se afastaram da urna, 1 se aproximou; deslocamento médio +1,73 pp em F−L na direção de Flávio.
8. Nas mesmas 11 casas, erro comum publicado +5,73 contra reponderado +7,47.
9. Média Arvor 52,88 × 47,12: erro +9,33 pp em F−L.
10. Projeção Arvor 52,07 × 47,93: erro +7,70 pp; a âncora publicada sozinha errava +4,98, a PNAD somou +1,01 e a presença relativa de Flávio (+3,8%) somou +1,71.
11. 1º turno: erro comum +3,55 em L−F (superestimou Lula). 2º turno: −5,53 em L−F. Sinal invertido.
12. 2022 (1º turno): +3,92 em L−B. Dos três pontos medidos, o 2º turno de 2026 é o único em que o erro comum favoreceu o candidato da direita.
13. Mesma casa nos dois turnos: 10 de 13 inverteram o sinal; correlação dos erros −0,22.
14. Tendência publicada de 05 a 24/10 dentro de cada casa: −0,150 pp/dia em F−L (Flávio perdendo terreno); média +4,20 até 12/10 e +2,17 desde 19/10.
15. Repetir o 1º turno seção a seção, sem pesquisa nenhuma, errava +6,11 pp: as pesquisas (média +5,53) pouco melhoraram sobre a urna anterior.
16. Flávio ficou abaixo do transporte do 1º turno em 27 de 27 UFs; viés +3,02 pp na parcela dele, RMSE sem o viés só 0,75 pp: a geografia veio certa, o nível veio errado.
17. Contabilidade agregada: 14,10 milhões de votos disponíveis (terceira via, queda de branco/nulo e aumento de comparecimento); Flávio ficou com 26,4% do ganho líquido. Mesmo que todo o ganho dele viesse da terceira via, seria no máximo 39,9% dela.
18. Correlação entre UFs da variação da abstenção com o resíduo de Flávio: 0,02; da terceira via do 1º turno: −0,57.
19. Teto do comparecimento: mesmo atribuindo a Lula todo o aumento líquido, ele explica no máximo 2,36 pp da diferença.
20. Estaduais (Quaest e Datafolha, campo de 06 a 13/10): 7 de 7 acertaram o vencedor da UF; erro médio +2,33 pp em F−L.

## 3. Pesquisas nacionais, da mais próxima à mais distante

Erro F−L sobre os válidos do total publicado (regra da casa); oficial = válidos divulgados pela casa; PNAD = placar reponderado que entrou nas centrais. "(dentro)" marca erro menor que a margem AAS.

| Casa | Campo | Modo | Publicado F × L | Válidos F | Erro F−L | Erro oficial | Erro PNAD | Margem AAS |
|---|---|---|---|---|---|---|---|---|
| Vox Brasil | 20/10–22/10 | presencial | 44,3 × 45,4 | 49,39 | +2,34 (dentro) | +2,37 | sem PNAD | 4,52 |
| Colectta | 23/10–23/10 | presencial | 46,0 × 46,5 | 49,73 | +3,03 (dentro) | +2,97 | sem PNAD | 3,72 |
| Futura | 23/10–24/10 | telefone | 48,2 × 47,9 | 50,16 | +3,88 (dentro) | +3,77 | sem PNAD | 4,47 |
| Palver | 22/10–24/10 | online | 50,0 × 49,0 | 50,51 | +4,58 | n/d | +4,38 | 2,79 |
| Datafolha | 23/10–24/10 | presencial | 48,0 × 47,0 | 50,53 | +4,62 | +5,57 | +8,53 | 3,16 |
| Ipespe | 20/10–22/10 | telefone | 48,0 × 47,0 | 50,53 | +4,62 (dentro) | +4,57 | +6,25 | 5,19 |
| Nexus | 23/10–24/10 | telefone | 47,0 × 46,0 | 50,54 | +4,65 | +4,57 | +6,90 | 4,54 |
| Quaest | 23/10–24/10 | presencial | 46,0 × 45,0 | 50,55 | +4,67 | +5,57 | sem PNAD | 3,38 |
| Indexa/Broadcast | 20/10–21/10 | telefone | 45,2 × 44,1 | 50,62 | +4,80 | +4,77 | sem PNAD | 4,64 |
| MDA | 21/10–23/10 | presencial | 46,3 × 45,0 | 50,71 | +4,99 | +4,97 | +7,76 | 4,55 |
| AtlasIntel | 18/10–23/10 | online | 49,9 × 48,4 | 50,76 | +5,10 | +5,17 | +5,21 | 2,80 |
| PoderData | 23/10–24/10 | telefone | 49,0 × 47,0 | 51,04 | +5,65 | +5,57 | +8,43 | 3,16 |
| Meio/Ideia | 15/10–19/10 | telefone | 48,0 × 46,0 | 51,06 | +5,70 | +5,77 | sem PNAD | 5,22 |
| Instituto França | 21/10–23/10 | nao_informado | 45,6 × 43,1 | 51,41 | +6,39 | +6,37 | sem PNAD | 5,31 |
| Veritá | 19/10–23/10 | telefone | 49,4 × 46,5 | 51,55 | +6,68 | +6,69 | +7,68 | 1,60 |
| Gerp | 22/10–24/10 | telefone | 49,0 × 46,0 | 51,58 | +6,73 | +7,57 | +6,71 | 4,10 |
| Alfa Inteligência/TMC | 18/10–22/10 | presencial | 49,9 × 46,0 | 52,03 | +7,64 | +7,57 | +8,68 | 3,85 |
| DataTrends | 19/10–21/10 | telefone | 50,0 × 46,0 | 52,08 | +7,74 | +7,37 | sem PNAD | 4,47 |
| Real Time Big Data | 19/10–22/10 | telefone | 49,0 × 45,0 | 52,13 | +7,83 | +7,57 | +11,60 | 4,52 |
| Vetor/Arrow | 22/10–23/10 | telefone | 50,0 × 44,9 | 52,69 | +8,94 | +8,97 | sem PNAD | 2,42 |

Mais próximas: Vox Brasil (+2,34), Colectta (+3,03), Futura (+3,88). Mais distantes: Vetor/Arrow (+8,94), Real Time Big Data (+7,83), DataTrends (+7,74), Alfa Inteligência/TMC (+7,64).

Por modo de coleta (média do erro F−L): nao_informado +6,39 (n = 1); online +4,84 (n = 2); presencial +4,55 (n = 6); telefone +6,11 (n = 11). As duas casas que acertaram o vencedor são presenciais; o grupo presencial também inclui Alfa (+7,63). Amostra pequena: descrição, não teste.

Fora desta lista: Data Ranking (campo até 16/10) entrou na Projeção, mas a regra de campo encerrado a partir de 19/10 o exclui aqui.

## 4. A reponderação por renda nesta rodada (achado contrário à tese da casa)

**Fato.** A casa assumiu que os institutos subestimam a renda alta e, com ela, Flávio. Trocar o perfil de renda pela PNAD deslocou todas as casas reponderáveis para Flávio (média +1,73 pp em F−L), e a urna foi para o outro lado. 9 de 11 se afastaram, 1 se aproximou, 1 ficou neutra.

| Casa | Perfil de renda | Erro publicado | Erro PNAD | Variação do erro absoluto |
|---|---|---|---|---|
| Alfa Inteligência/TMC | perfil_publicado | +7,64 | +8,68 | +1,04 |
| AtlasIntel | perfil_publicado | +5,10 | +5,21 | +0,12 |
| Datafolha | hipotese_onda_anterior | +4,62 | +8,53 | +3,90 |
| Gerp | perfil_ponderado | +6,73 | +6,71 | −0,02 |
| Ipespe | perfil_publicado | +4,62 | +6,25 | +1,63 |
| MDA | perfil_publicado | +4,99 | +7,76 | +2,77 |
| Nexus | perfil_publicado | +4,65 | +6,90 | +2,25 |
| Palver | perfil_ponderado | +4,58 | +4,38 | −0,20 |
| PoderData | perfil_ponderado | +5,65 | +8,43 | +2,77 |
| Real Time Big Data | perfil_publicado | +7,83 | +11,60 | +3,77 |
| Veritá | hipotese_perfil_condicional | +6,68 | +7,68 | +1,01 |

No 1º turno a mesma régua aproximou 7 de 10 casas e cortou o erro do agregador de +4,25 para +2,43 (L−F). No 2º turno ela piorou todas as casas menos uma. **Juízo editorial:** a reponderação por renda não é uma correção estável de sinal conhecido; funcionou em uma rodada e falhou na seguinte. Publicar com o mesmo destaque que teve no 1º turno.

Ressalvas da própria série: Datafolha de 24/10 usou perfil da onda anterior (hipótese declarada), Veritá usou perfil condicional e várias casas têm `perfil_publicado` com etapa de ponderação não explicitada. Nas casas com perfil ponderado identificado, a variação do erro absoluto foi: Gerp −0,02; Palver −0,20; PoderData +2,77.

## 5. As centrais da casa

| Central | F | L | F−L | Erro F−L |
|---|---|---|---|---|
| Âncora da Projeção (published): recência e tendência encolhida, antes da presença relativa | 50,71 | 49,29 | +1,41 | +4,98 |
| Âncora da Projeção (pnad): recência e tendência encolhida, antes da presença relativa | 51,21 | 48,79 | +2,42 | +5,99 |
| Projeção Arvor | 52,07 | 47,93 | +4,13 | +7,70 |
| Média Arvor | 52,88 | 47,12 | +5,76 | +9,33 |

**Fato.** As duas camadas que a casa acrescentou às pesquisas apontavam para Flávio e somaram erro: PNAD +1,01 pp e presença relativa +3,8% +1,71 pp na Projeção. O +3,8% era o resíduo F/L do 1º turno transportado ao 2º, e o contrato da Projeção já o rotulava como hipótese que podia repetir ajuste absorvido. A Média, restrita às 11 casas com renda, errou +9,33, contra +5,53 da média simples publicada das 20 casas. Contra a urna sem exterior os erros são +9,32 e +7,69.

## 6. Comparação com o 1º turno e com 2022

- 1º turno de 2026: erro comum +3,55 pp em L−F, mediana +4,04, 13 casas; as pesquisas superestimaram Lula.
- 1º turno de 2022: +3,92 em L−B, Bolsonaro −4,33 pp.
- 2º turno de 2026: −5,53 em L−F; Flávio +2,76 pp acima da urna na média.
- Mesma casa nos dois turnos (13 casas): média 1T +3,55, média 2T −5,04, correlação −0,22. Quem mais superestimou Lula no 1º turno não é quem mais superestimou Flávio no 2º.

| Casa | Erro 1T (L−F) | Erro 2T (L−F) |
|---|---|---|
| AtlasIntel | +4,78 | −5,10 |
| Datafolha | +4,04 | −4,62 |
| Futura | −0,24 | −3,88 |
| Gerp | −0,26 | −6,73 |
| Indexa/Broadcast | +7,75 | −4,80 |
| MDA | +7,53 | −4,99 |
| Meio/Ideia | +2,88 | −5,70 |
| Nexus | +7,13 | −4,65 |
| Palver | −1,70 | −4,58 |
| PoderData | +2,94 | −5,65 |
| Quaest | +4,16 | −4,67 |
| Real Time Big Data | +6,12 | −7,83 |
| Vox Brasil | +0,97 | −2,34 |

## 7. O que as pesquisas mediram na última semana

**Fato.** As 58 ondas pós-urna (21 casas) mostram Flávio à frente em quase todas, com vantagem encolhendo: inclinação −0,114 pp/dia no conjunto e −0,150 dentro de cada casa. Na última semana (32 ondas) a inclinação dentro da casa é −0,022 pp/dia, quase parada, e a média F−L +2,17. A âncora da Projeção estimava Lula +0,071 pp/dia nos válidos.

**Correção do briefing.** A frase "tendência de Flávio subindo até 24/10 nas publicadas" não se sustenta nos dados do acervo: a série publicada vai de F−L +4,20 (campo até 12/10) a +2,17 (desde 19/10). O que subiu foi a Projeção da casa, por causa das camadas da seção 5. Mesmo extrapolando o ritmo de queda observado (−0,150 pp/dia) por 4,6 dias até a urna, F−L iria a +1,48, longe dos −3,57 da urna.

## 8. Estaduais do 2º turno

| Pesquisa | Campo | Válidos F | Urna F | Erro F−L | Vencedor | Erro do transporte |
|---|---|---|---|---|---|---|
| quaest_AC_2026-10-12 | 09/10–12/10 | 68,18 | 66,57 | +3,23 | certo | +5,34 |
| quaest_AM_2026-10-12 | 09/10–12/10 | 47,78 | 45,98 | +3,60 | certo | +5,21 |
| quaest_DF_2026-10-11 | 08/10–11/10 | 55,56 | 54,28 | +2,56 | certo | +6,19 |
| quaest_ES_2026-10-13 | 10/10–13/10 | 57,30 | 56,37 | +1,87 | certo | +5,68 |
| quaest_RN_2026-10-12 | 09/10–12/10 | 35,87 | 34,28 | +3,17 | certo | +5,27 |
| quaest_TO_2026-10-13 | 10/10–13/10 | 53,33 | 51,37 | +3,93 | certo | +5,01 |
| datafolha_DF_2026-10-07 | 06/10–07/10 | 53,26 | 54,28 | −2,03 | certo | +6,19 |

Duas semanas antes da urna, as estaduais erraram menos (média +2,33) que as nacionais da véspera e que o transporte do 1º turno nas mesmas UFs. Seis delas são da mesma casa e da mesma semana: não generalizar.

## 9. Projeção territorial por UF

| Método | UFs com vencedor certo | RMSE pond. (pp de Flávio) | Viés | RMSE sem viés | Nacional F | Erro F−L nacional | Erros de vencedor |
|---|---|---|---|---|---|---|---|
| Combinação experimental com âncora PNAD (projeção territorial de 19/10) | 26/27 | 2,74 | +2,64 | 0,74 | 50,90 | +5,36 | MG |
| Terceira via dividida 50/50 (projeção territorial de 19/10) | 26/27 | 2,75 | +2,68 | 0,61 | 50,94 | +5,44 | MG |
| Transporte proporcional do 1º turno, sem pesquisa (mapa de 2026-10-25) | 25/27 | 3,11 | +3,02 | 0,75 | 51,28 | +6,11 | AP, MG |
| Transporte proporcional do 1º turno, sem pesquisa (mapa de 2026-10-24) | 25/27 | 3,11 | +3,02 | 0,75 | 51,28 | +6,11 | AP, MG |
| Terceira via proporcional à seção (método selecionado) (projeção territorial de 19/10) | 25/27 | 3,11 | +3,02 | 0,75 | 51,28 | +6,11 | AP, MG |
| Projeção Arvor por UF (mapa de 2026-10-24) | 25/27 | 3,79 | +3,71 | 0,79 | 51,97 | +7,50 | AP, MG |
| Projeção Arvor por UF (mapa de 2026-10-25) | 25/27 | 3,89 | +3,81 | 0,79 | 52,07 | +7,69 | AP, MG |
| Matriz ecológica de 2022 por UF (projeção territorial de 19/10) | 24/27 | 4,28 | +4,24 | 0,61 | 52,53 | +8,62 | AM, AP, MG |
| Matriz ecológica de 2022 por contexto (projeção territorial de 19/10) | 24/27 | 4,40 | +4,35 | 0,66 | 52,65 | +8,86 | AM, AP, MG |
| Média Arvor por UF (mapa de 2026-10-24) | 24/27 | 4,65 | +4,58 | 0,83 | 52,84 | +9,23 | AM, AP, MG |
| Média Arvor por UF (mapa de 2026-10-25) | 24/27 | 4,69 | +4,62 | 0,83 | 52,88 | +9,32 | AM, AP, MG |
| Deslocamento uniforme por seção (projeção territorial de 19/10) | 24/27 | 4,72 | +4,68 | 0,64 | 52,94 | +9,43 | AM, AP, MG |
| Deslocamento uniforme por UF (projeção territorial de 19/10) | 24/27 | 4,73 | +4,69 | 0,62 | 52,95 | +9,45 | AM, AP, MG |

**Fato.** Todas as projeções acertaram a ordem dos estados (correlação 0,999 entre previsto e urna) e erraram o nível. O transporte proporcional errou o vencedor em AP, MG; a Média e a Projeção recentradas erraram mais (4,69 e 3,89 pp de RMSE contra 3,11 do transporte), porque o deslocamento comum em log-odds empurrou todas as UFs na direção errada. A retrospectiva 2018→2022 tinha RMSE estadual de 1,73 pp no método selecionado; em 2026 ele fez 3,11.

Resíduo do transporte por região (urna menos previsto, parcela de Flávio): N −2,56; NE −2,12; CO −3,30; SE −3,65; S −3,17. Maiores perdas de Flávio: RJ −4,22, SP −3,70, GO −3,60, AL −3,41; menores: PI −1,37, BA −1,56, PE −2,16.

## 10. Hipóteses candidatas

Legenda: **Fato** (medido nos arquivos), **Inferência** (apoiada nos fatos, não provada), **Juízo** (posição editorial), **Hipótese** (ainda exige prova). Nenhuma das hipóteses abaixo envolve, nem os dados sustentam, afirmação de irregularidade na votação ou na totalização.

### (a) Erro comum das pesquisas, como em 2022 e no 1º turno

- Sustenta (fato): 20 de 20 casas no mesmo sinal; dispersão 1,69 menor que o piso amostral 2,06; erro de tamanho próximo ao de 2022 (3,92) e do 1º turno (3,55), agora maior (5,53).
- Contraria (fato): o sinal inverteu. Em 2022 e no 1º turno de 2026 o erro favoreceu Lula; no 2º turno favoreceu Flávio. Correlação entre os erros da mesma casa −0,22: não é um viés fixo de cada instituto.
- Inferência: o componente comum domina, mas não é o mesmo viés estrutural "contra a direita" das rodadas anteriores. Uma leitura compatível é que as casas, depois do 1º turno, corrigiram ponderações na direção de Flávio (voto declarado no 1º turno, PNAD, escolaridade) e passaram do ponto. **Hipótese**: exige as matrizes de ponderação de antes e depois de 04/10 de cada casa. Contra ela: PoderData, CNT/MDA e Palver declaram ponderação pelo voto do 1º turno e erraram +5,65, +4,99, +4,58, perto da média (+5,53), não acima dela.
- Fato adicional: repetir o 1º turno sem pesquisa errava +6,11; as casas ficaram perto disso. Elas mediram, em média, o que a geografia do 1º turno já implicava.

### (b) Comparecimento diferencial

- Sustenta (fato): a abstenção caiu 1,86 pp (21,08% para 19,22%), 2,96 milhões a mais na urna. A Projeção supunha o comparecimento do 1º turno e presença relativa a favor de Flávio. O horário de votação foi estendido até 19h no dia (decisão de 25/10 registrada no contrato da apuração), o que eleva comparecimento legitimamente.
- Contraria (fato): é teto, não estimativa. Mesmo dando a Lula todo o aumento líquido, F−L iria de −3,57 para −1,21: no máximo 2,36 dos 5,53 pp de erro. Entre as UFs, a variação da abstenção não acompanha o resíduo de Flávio (correlação 0,02); AP, RR e AC tiveram abstenção maior que no 1º turno e o mesmo resíduo dos demais.
- Inferência: comparecimento pode explicar uma parte, não o erro inteiro, e não deixa assinatura geográfica nos agregados por UF. Teste decisivo: a régua por seção (`/api/2t/comparecimento`) cruzando variação de comparecimento com a fatia de Lula na mesma seção.

### (c) Indecisos e eleitor provável

- Contraria (fato): indecisos eram poucos. Mesmo dando todos a Lula, Flávio continuaria à frente em 8 de 20 casas e o erro médio cairia só para +3,45.
- Contraria (fato): todo filtro de presença declarada apontou para Flávio, na direção oposta à urna: Quaest eleitor provável 51/49 contra 50,55 da amostra completa (erro +5,57 contra +4,67); PoderData presença certa F/L 96/94 desloca F−L +1,05; Ipespe presença certa F/L 94/90 desloca F−L +2,17; Nexus eleitor provável 52,4/47,6 contra 50,54 da amostra completa.
- Inferência: presença autodeclarada não previu quem compareceu; o eleitor de Flávio declara mais certeza de votar, e isso não se converteu em vantagem na urna. **Juízo**: a decisão de não aplicar o eleitor provável da Nexus às centrais estava certa; aplicar o da Quaest à Projeção somou erro, pequeno pelo peso de 7%.

### (d) Reponderação por renda

- Fato: a urna testou a premissa e ela falhou nesta rodada (9 de 11 casas pioraram, erro comum 5,73 para 7,47). Ver seção 4.
- Hipótese: o gradiente renda × voto medido dentro das faixas não é transportável. Se o entrevistado de renda alta que a pesquisa alcança é mais pró-Flávio que o eleitor de renda alta da população, dar mais peso a ele amplia o erro. Exige microdados com pesos para testar; o anúncio da Palver de liberar a base individual depois do 2º turno permite a primeira prova.

### (e) Perfil de quem votou

- Fato (agregado por UF): Flávio ficou abaixo do transporte do 1º turno em todas as 27 UFs; o resíduo é maior onde a terceira via pesou mais no 1º turno (correlação −0,57) e no Sudeste, Centro-Oeste e Sul do que no Nordeste. Nacionalmente Flávio ganhou 3,72 milhões de votos entre os turnos; supondo que ele não perdeu ninguém do 1º turno, isso é no máximo 39,9% dos 9,32 milhões da terceira via, contra 61% entre os que escolhem um finalista na síntese que a casa usava (com 30% sem escolha, 43% do total).
- Inferência: o padrão é compatível com o eleitor da terceira via (Caiado, Cury, Renan, Zema) e parte do branco/nulo indo menos a Flávio do que as matrizes supunham. Não é medição: a identidade de agregados não diz quem trocou de voto.
- Contraria: sem dado individual nem cruzamento seção a seção, renda, idade e escolaridade de quem votou não são observáveis aqui.

## 11. ENTRADA DO AUTOR

<!-- ENTRADA DO AUTOR: início. Fonte: analysis/apuracao_2t_2026/hipotese_autor.md (tweet de 25/10, 21h41; imagem em noticias_fontes/tweet_leonardodias_20261025_2141.webp). -->
> **ENTRADA DO AUTOR (juízo editorial declarado de Leonardo Dias).** "Para chegar num resultado próximo ao final, tivemos de diminuir as abstenções para o volume real de 19,2%, aumentar a presença relativa pró-Lula para 12,5% e direcionar mais indecisos para o Lula. Essa seria a hipótese, se foi isso mesmo, não saberemos."

Cenário do simulador (Central Média de 24/10) que reproduz a urna: abstenção 18,50%, presença relativa de Flávio −12,5% (presença efetiva Flávio 76,0%, Lula 86,9%), indecisos 100% escolhendo, divisão 34,8% Flávio × 65,2% Lula; resultado 48,3 × 51,7. Empate exigiria presença relativa −6,4%, mantido o resto.

**Cenário refeito no motor da casa com a urna observada** (`hipotese_autor.json`; `scripts/reponderacao-simulador.py` sobre o snapshot `9399acb33c51065d`, último de 24/10, o único da data que reproduz o tweet: Flávio 48,33% e brancos e nulos de 3,09% do comparecimento; empate com presença −6,4% dá Flávio 49,99%). Fixados: abstenção 19,22% e brancos mais nulos 4.153.791 (3,24% de quem compareceu; o tweet usava 18,50% e 3,1%).

| Cenário | Presença relativa de Flávio | Indecisos para Flávio | Flávio | Lula | Erro F−L contra a urna | Votos de Flávio contra a urna |
|---|---|---|---|---|---|---|
| presença relativa resolvida para bater Flávio da urna; indecisos na proporção automática da central | −13,7% | 48,2% | 48,21 | 51,79 | 0,00 | 337 |
| sem solução entre 0 e 100%: mesmo com 100% dos indecisos para Lula e presença +3,8% da central, Flávio fica acima da urna | +3,8% | 0,0% | 51,98 | 48,02 | +7,53 | 4.672.724 |
| presença −12,5% e indecisos 34,8/65,2, com comparecimento e brancos e nulos da urna | −12,5% | 34,8% | 48,33 | 51,67 | +0,22 | 138.808 |
| central (+3,8%, divisão automática) só com comparecimento e BN da urna | +3,8% | 52,8% | 52,84 | 47,16 | +9,24 | 5.733.140 |

- (a) Com indecisos na proporção automática, bater a urna exige presença relativa de Flávio de −13,7%, contra +3,8% da central.
- (b) Mantida a presença +3,8%, nenhuma divisão dos indecisos alcança a urna: mesmo com todos para Lula, Flávio fica em 51,98% (+7,53 pp em F−L).
- (c) A combinação do autor (−12,5% e 34,8/65,2) com brancos e nulos reais dá Flávio 48,33% (+0,22 pp em F−L, 138.808 votos de Flávio acima da urna).

**Peça 1, abstenção.**
- Sustenta (fato): a urna mediu abstenção de 19,22%, o número que o tweet cita (o cenário da imagem usou 18,50%), contra 21,08% no 1º turno; 2,96 milhões a mais votaram. Nos mesmos municípios: 19,26% contra 21,10%.
- Contraria (fato): menos abstenção sozinha não move a razão entre os candidatos; só move se os novos votantes forem desiguais. Mesmo com todos para Lula, o efeito seria no máximo 2,36 pp em F−L, e entre as UFs a variação da abstenção não acompanha o resíduo de Flávio (correlação 0,02).

**Peça 2, presença diferencial (o centro da hipótese).**
- Presença por candidato **não é medida**: a urna diz quantos votaram, nunca em quem votaria quem ficou em casa. Por isso a frase final do autor é a leitura correta.
- Fato aritmético: no motor, com a urna fixada, a presença relativa necessária é −13,7%. Conferência por fora do motor: a razão F/L da Média Arvor precisava cair 17,0% (−13,9% sem o +3,8% já embutido); a da média simples publicada das 20 casas, −10,5%.
- Contraria (fato): essa mesma conta é idêntica à de um erro comum de medição; a urna não separa as duas. E a presença declarada nas pesquisas apontou para o outro lado: Ipespe desloca F−L +2,17; PoderData desloca F−L +1,05 a favor de Flávio. Se houve presença diferencial pró-Lula, ela contrariou o que os eleitores disseram aos institutos.

**Peça 3, destino dos indecisos.**
- Fato: indecisos médios de 2,0% nas últimas ondas. Com a divisão do autor (34,8% Flávio), o erro médio vai de +5,53 para +4,87 pp; com todos para Lula, +3,45.
- Contraria: os indecisos são poucos para carregar o resultado; no cenário do autor eles somam 2,2 milhões. O destino deles não é identificável no agregado.

**Leitura.** As três peças juntas reproduzem a urna por construção, como qualquer combinação que mude a razão F/L em cerca de 15%. A urna sustenta a abstenção como fato, deixa a presença diferencial sem medida e limita o papel dos indecisos. **Juízo editorial do autor, preservado:** "se foi isso mesmo, não saberemos".
<!-- ENTRADA DO AUTOR: fim -->

## 12. Limites

- A urna lida ao vivo é parcial até `presidente.json` do 2º turno existir; reexecutar o script atualiza tudo.
- Válidos de cada pesquisa são a renormalização dos inteiros publicados; o arredondamento sozinho move a diferença em até cerca de 1 pp em casas sem decimal.
- Margem AAS ignora ponderação e desenho: é piso, não intervalo da casa. O erro comum de 2 pp do Monte Carlo era hipótese; o erro observado na parcela de Flávio na Projeção foi 3,85 pp.
- Estaduais têm campo de 06 a 13/10; o mapa de 24/10 vem do histórico git (commit indicado no JSON) e o de 25/10 do arquivo de trabalho.
- Correlações entre 27 UFs são ecológicas. Nada aqui identifica migração individual, comparecimento por candidato ou irregularidade.

## 13. Consultas e fontes

- `python3 scripts/apuracao-2t-2026-pesquisas.py` (este memorando e os três JSON).
- Urna: `analysis/apuracao_2t_2026/dados/presidente.json` quando existir; senão `curl -s http://127.0.0.1:4180/api/2t/regioes`, `/api/2t/ufs`, `/api/2t/abstencao` e `/api/2t/evolucao` (nomes por número de urna).
- Pesquisas: `analysis/reponderacao/pesquisas/*.json` (placar de 2º turno, campo iniciado depois de 04/10); reponderado: `docs/assets/reponderacao_simulador.json` (`polls[].pnad`) e `docs/assets/reponderacao_pnad.json` (cenário pessoas16_efetivo).
- Centrais: `docs/assets/reponderacao_simulador.json` (`central`, `central_projection`, `projection.anchors`), snapshot `e1e4524328558a79`.
- Presença declarada: `analysis/reponderacao/historico_2t/presenca.json`; 1º turno: `analysis/apuracao_2026/dados/pesquisas_vs_urna.json` e `presidente.json`; 2022: `analysis/predicao_2026/erro_2022/erro_2022.json`.
- Território: `docs/assets/mapa_previsao_2t_2026.json` (25/10 e 24/10 via git), `docs/assets/projecao_secoes_2t_ufs.csv` (19/10), `analysis/projecao_secoes_2t/estaduais.json`, `analysis/reponderacao/estaduais/`.
