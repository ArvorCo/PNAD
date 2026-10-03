# Tendência, aceleração e teto na reta final: avaliação

Corte: 03/10/2026. Eleição: 04/10/2026. Todo número desta nota sai de
`docs/assets/predicao_2026_1T_presidente.json` (chaves `nacional.tendencia`,
`nacional.alvos`, `sensibilidades`, `validacao_preditiva`) e de
`docs/assets/predicao_2026_validacao_preditiva.json`, gerados por
`python3 scripts/predicao-2026-build.py --hoje 2026-10-03`. Código:
`scripts/predicao_2026/tendencia.py` (modelo e regressões),
`scripts/predicao_2026/migracao.py` (divisão da migração e teto),
`scripts/predicao_2026/preditiva.py` (validação). Transcrições com página:
`analysis/predicao_2026/tendencia/migracao_declarada.json` e
`analysis/predicao_2026/tendencia/estaduais_rotulos.json`.

## Resposta curta

1. **A queda da terceira via é robusta.** Nos válidos, com efeito fixo de casa,
   31 ondas em 28 dias: terceira via −0,32 pp/dia (ep 0,04; robusto por casa
   0,05), Flávio +0,19 (0,04), Lula +0,13 (0,03).
2. **A divisão é cerca de 60/40 para Flávio, e três fontes independentes
   concordam.** Série nacional de 28 dias 0,59 (dp 0,08); matriz declarada da
   Nexus 0,61 (0,04) e do Datafolha 0,62 (0,04); síntese 0,61. As estaduais
   apontam mais para Flávio (0,80 nos pares de setembro), com erro grande.
3. **A aceleração do Flávio não é identificável.** Em 28 dias a inclinação
   constante basta (razão de verossimilhança zero); o termo quadrático de
   Flávio é +0,014 pp/dia² com p = 0,17; a inclinação dele passa de 0,13 para
   0,26 pp/dia entre as duas metades da janela, diferença com p = 0,35. Só a
   janela de 14 dias dá p = 0,017, com 4 graus de liberdade e p ≈ 0,28 no erro
   robusto por casa.
4. **Não há teto de Lula visível no 1º turno até amanhã, mas a folga dele é a
   metade da de Flávio.** Lula sobe 0,13 pp/dia nos válidos sem curvatura
   (p = 0,69). A reserva (2º turno menos 1º turno, mesma onda) é 3,2 pp para
   Lula e 6,0 pp para Flávio na casa média do corte.
5. **O modelo dinâmico com tendência não prevê melhor que a central.** A
   variante simples "central + inclinação encolhida de 28 dias" é a única que
   passa o critério, em ponto, sem significância.

## 1. O modelo

Nível e inclinação por categoria em tempo contínuo (cinco partes, quatro
livres), com transição exata:

    d nível      = inclinação dt + σ_l dW1
    d inclinação = −κ · inclinação dt + σ_b dW2

Três variantes, mesmos efeitos de casa de soma zero, mesmo phi e mesma
observação do DLM de nível: inclinação constante (σ_b = 0, κ = 0), passeio
integrado (κ = 0) e **amortecida** (κ livre, inclinação Ornstein-Uhlenbeck). A
amortecida foi declarada principal antes da validação: o amortecimento impede
que uma inclinação estimada com ruído seja extrapolada sem freio, e com κ → 0
ela vira o passeio integrado. As integrais de covariância têm forma fechada e
o teste as confere contra a exponencial de matriz de Van Loan.

Verossimilhança no corte, janela desde 15/08, 39 ondas:

| Modelo | Parâmetros | log-verossimilhança | AIC | Diferença F−L projetada (válidos) |
|---|---|---|---|---|
| DLM de nível (atual) | 7 | 402,70 | −791,40 | −0,55 |
| Inclinação constante | 7 | 395,96 | −777,91 | −0,11 |
| Passeio integrado | 8 | 399,61 | −783,21 | −0,16 |
| Amortecida (âncora `tendencia`) | 9 | 403,19 | −788,38 | −0,45 |

A amortecida ganha 0,49 de log-verossimilhança sobre o nível com dois
parâmetros a mais (razão 0,98): o AIC prefere o DLM de nível. No corte, κ =
0,48 por dia (meia-vida da inclinação 1,45 dia). A verossimilhança tem dois
modos; em todas as origens de setembro da validação o ótimo foi o modo
degenerado (κ no teto de 2 por dia, inclinação que some em horas), ou seja, o
próprio modelo dizia que não havia tendência persistente. O ajuste usa várias
partidas em cada origem para não ficar preso a um modo só.

## 2. Âncoras nacionais

| Âncora | Lula | Flávio | Terceira via | F−L (válidos) | Cenário completo L / F | F−L completo |
|---|---|---|---|---|---|---|
| Central inclusiva | 44,02 | 43,05 | 12,93 | −0,96 | 44,53 / 43,04 | −1,48 |
| DLM de nível | 44,00 | 43,44 | 12,56 | −0,55 | 44,50 / 43,42 | −1,08 |
| Tendência, nível no corte (03/10) | 44,07 | 43,57 | 12,37 | −0,50 | 44,57 / 43,54 | −1,03 |
| Tendência projetada a 04/10 | 44,07 | 43,62 | 12,31 | −0,45 | 44,57 / 43,59 | −0,98 |
| Central + inclinação de 28 dias, a 04/10 | 44,75 | 44,10 | 11,15 | −0,65 | 45,23 / 44,05 | −1,17 |

Colunas de válidos: alvo nacional (`nacional.alvos`). Cenário completo:
`sensibilidades`, com eleitor provável, comparecimento e calibração estadual.
O desvio da diferença F−L é 1,86 pp no último campo (01/10), 2,45 no corte e
2,74 projetado a 04/10: a projeção desloca o centro em 0,24 pp e alarga a
incerteza. Inclinações no último campo, nos válidos: Lula +0,01, Flávio
+0,16, terceira via −0,17 pp/dia, todas com desvio de 0,25 a 0,34.

A central com inclinação parte da data efetiva da média central (28/09,
ponto médio ponderado pela recência) e projeta 5,7 dias com as inclinações
de 28 dias encolhidas pelo fator b²/(b² + ep²): Lula +0,125, Flávio +0,181,
terceira via −0,314 pp/dia.

## 3. A aceleração existe?

| Teste | Lula | Flávio | Terceira via |
|---|---|---|---|
| Inclinação linear, 28 dias (pp/dia, ep) | +0,131 (0,029) | +0,188 (0,037) | −0,319 (0,041) |
| Inclinação linear, 14 dias, ponto médio | +0,117 (0,061) | +0,266 (0,117) | −0,383 (0,128) |
| Termo quadrático, 28 dias (pp/dia², p) | −0,003 (0,69) | +0,014 (0,17) | −0,010 (0,35) |
| Termo quadrático, 14 dias (pp/dia², p) | +0,001 (0,98) | +0,130 (0,017) | −0,131 (0,045) |
| Primeira metade → segunda metade (pp/dia) | 0,125 → 0,139 | 0,127 → 0,259 | −0,252 → −0,397 |
| p da mudança entre metades | 0,90 | 0,35 | 0,34 |

Razão de verossimilhança, inclinação constante contra inclinação que muda
(mistura de qui-quadrado 0 e 1): janela inteira desde 15/08, estatística
7,30, p = 0,003; últimos 28 dias, estatística 0, p = 1. A inclinação mudou
entre agosto e setembro (no fim de agosto a terceira via subia); dentro de
setembro ela é constante para os dados.

A janela de 14 dias tem 20 ondas de 14 casas e 4 a 5 graus de liberdade. O
p = 0,017 do quadrático de Flávio cai para cerca de 0,28 com erro robusto
por casa (ep 0,12). E a própria divisão de 14 dias depende de qual data
define a janela: Flávio leva 0,69 do ganho pelo ponto médio do campo, 0,52
pelo fim do campo e 0,50 pela divulgação (`janela_14d_por_regra`). A leitura
de 50/50 nos últimos 14 dias vem dessa escolha, não dos dados.

Na validação, a variante com inclinação que muda (passeio integrado) não
prevê melhor que a de inclinação constante: diferença de MAE da margem +0,02
(ep 0,07); Flávio +0,10 (0,15).

**Conclusão:** a terceira via cai e Flávio leva a maior parte, mas a
aceleração dele não se distingue de zero com os dados que existem.

## 4. Validação de origem móvel

Previsão de pesquisas futuras, não da urna. Origens de 01/09 a 01/10, alvo
no ponto médio do campo da onda futura (é o uso real da âncora projetada),
211 pares, 32 ondas alvo. Viés = previsto menos observado.

| Âncora | MAE L−F | Viés L−F | Viés Lula | Viés Flávio | Viés terceira via |
|---|---|---|---|---|---|
| Central (recência 3 dias, janela 7) | 3,36 | +1,16 | −1,13 | −2,29 | +3,41 |
| DLM de nível | 3,43 | +1,76 | −1,44 | −3,20 | +4,65 |
| Tendência projetada | 3,43 | +1,77 | −1,45 | −3,21 | +4,66 |
| Tendência, nível na origem | 3,43 | +1,77 | −1,45 | −3,21 | +4,66 |
| Inclinação constante projetada | 3,25 | +0,92 | −2,15 | −3,07 | +5,22 |
| Passeio integrado projetado | 3,26 | +0,87 | −2,04 | −2,92 | +4,96 |
| Central + inclinação 14 dias | 3,38 | +1,17 | −1,04 | −2,21 | +3,25 |
| Central + inclinação 28 dias | 3,25 | +0,21 | −1,25 | −1,46 | +2,72 |

Por horizonte (dias entre a origem e o início do campo alvo):

| Âncora | MAE 1–2 | Viés 1–2 | MAE 1–3 | Viés 1–3 | MAE 3–7 | Viés 3–7 |
|---|---|---|---|---|---|---|
| Central | 3,15 | +1,09 | 3,16 | +1,17 | 3,45 | +1,19 |
| Tendência projetada | 3,43 | +1,56 | 3,41 | +1,63 | 3,44 | +1,85 |
| Central + inclinação 28 dias | 3,05 | +0,40 | 3,04 | +0,42 | 3,34 | +0,13 |

Comparação pareada contra a central, média por onda alvo (negativo favorece a
alternativa):

| Comparação | Margem | Lula | Flávio | Terceira via |
|---|---|---|---|---|
| Tendência, 1–3 dias | +0,26 (0,15) | +0,20 (0,13) | +0,48 (0,14) | +1,08 (0,16) |
| Central + 28 dias, 1–3 dias | −0,12 (0,15) | +0,11 (0,10) | −0,28 (0,18) | −0,25 (0,24) |
| Tendência, todos os horizontes | +0,07 (0,14) | +0,06 (0,09) | +0,55 (0,13) | +1,09 (0,13) |
| Central + 28 dias, todos | −0,10 (0,18) | +0,16 (0,09) | −0,29 (0,19) | −0,25 (0,25) |

Deixando a casa do alvo fora (33 ondas): central 3,69, tendência 3,77
(+0,08, ep 0,23), central + 28 dias 3,60 (−0,09, ep 0,12).

Leitura:

- A âncora DLM de tendência é, na prática, o DLM de nível em setembro: em
  cada origem o ajuste escolheu inclinação que some em horas. Ela fica pior
  que a central no horizonte curto e com viés maior.
- As tendências extrapoladas sem freio (constante e integrada) acertam um
  pouco mais a margem, mas erram mais Lula e a terceira via: no começo de
  setembro projetaram a subida da terceira via do fim de agosto.
- Todas as âncoras têm viés positivo na margem e negativo em Flávio: as ondas
  seguintes vieram com Flávio mais alto. A central com inclinação de 28 dias
  corta esse viés de +1,17 para +0,42 no horizonte de 1 a 3 dias.
- Ressalva de seleção: foram testadas quatro variantes com tendência. A
  melhor delas ganha 0,12 pp com erro-padrão de 0,15. Isso está dentro do que
  o acaso produz ao escolher a melhor de quatro.
- Setembro teve tendência monótona. Uma validação nesse período premia quem
  extrapola tendência; ela não mostra o que acontece se a tendência parar.

## 5. Divisão da migração da terceira via

Fração de Flávio no ganho conjunto dos dois finalistas (o resto é de Lula).
Nos válidos, o ganho conjunto é exatamente a queda da terceira via.

| Fonte | Arquivo e página | Fração de Flávio | dp |
|---|---|---|---|
| Série nacional, 28 dias, efeito fixo de casa | `nacional.tendencia.regressao_efeitos_fixos` | 0,59 | 0,08 |
| Série nacional, placar publicado, 28 dias | idem, `publicado_vetor_28d` | 0,60 | 0,06 |
| Nexus 28/09, matriz 1º × 2º turno, peso voto × "pode mudar" | `docs/fontes/nexus_btg_28092026.pdf`, pp. 20, 41 e 84 | 0,61 | 0,04 |
| Datafolha 01/10, matriz em texto, mesmo peso | `data/originals/datafolha_102026_02/relatorio.pdf`, pp. 5, 7 e 8 | 0,62 | 0,04 |
| Estaduais, pares de setembro (14 pares, 7 UFs) | `analysis/voto_util/quaest/`, `analysis/predicao_2026/estaduais/` | 0,80 | 0,20 |
| Estaduais, todos os pares (38 pares, 25 UFs) | idem | 0,88 | 0,24 |
| Síntese (variância inversa, quatro linhas do resumo) | `divisao_migracao.sintese` | 0,61 | 0,03 só amostral |

Linhas da matriz da Nexus (p. 84), Flávio contra Lula no 2º turno: Zema 66 a
0, Renan Santos 43 a 13, Cury 38 a 30, Caiado 32 a 32, Samara 36 a 41. No
Datafolha (p. 8): Renan 54 a 28, Caiado 46 a 30, Cury 44 a 30. A parcela que
diz poder mudar o voto é maior justamente no eleitorado de Caiado (Nexus 39%,
Datafolha 45%) e de Cury (34% e 38%), os mais divididos.

Segunda opção de quem pode mudar: Nexus p. 44, Lula 18 e Flávio 17 (fração
0,49); Datafolha p. 59 (anexo, p. 24), Flávio 23 e Lula 15 (0,61); entre não
alinhados que podem mudar (Datafolha p. 7), Flávio 21 e Lula 12. Essas bases
misturam eleitores de Lula, de Flávio e da terceira via, e **nenhum dos dois
relatórios cruza a segunda opção pelo voto de 1º turno**: a varredura com
pdftotext das 145 páginas da Nexus e das 68 do Datafolha não encontrou esse
cruzamento. Por isso a segunda opção não entra na síntese.

Estaduais: pares de ondas consecutivas da mesma casa na mesma UF (Quaest e
Real Time Big Data), variação nos válidos ponderada pelo eleitorado, erro
amostral com deff 1,5. Nos pares de setembro, Nordeste 0,79 (0,42) e Sul e
Sudeste 0,82 (0,25): diferença −0,03 (0,48), p = 0,95. Com todos os pares,
agosto incluso, o Nordeste dá 1,42 (0,67) porque Lula perde pontos em AL, MA,
RN e PE entre agosto e setembro enquanto a terceira via cai pouco; contra Sul
e Sudeste, p = 0,27. Os dados estaduais não sustentam divisão diferente
entre regiões. Ressalvas: nas rodadas anteriores da Quaest a terceira via sai
por diferença (cada número impresso tem ±0,5 pp), e a data dessas rodadas vem
do rótulo impresso, com regra declarada e conferida em três UFs.

## 6. O teto de Lula existe nos dados?

Teste direto: se houvesse teto vinculante, a inclinação de Lula cairia ao se
aproximar dele. Não cai: 0,125 pp/dia na primeira metade da janela de 28
dias e 0,139 na segunda; termo quadrático −0,003 (p = 0,69).

O que existe é uma folga menor. Na mesma onda, o voto de 2º turno é o teto
operacional do 1º. Regressão com efeito fixo de casa em 31 ondas, percentuais
do total (`nacional.tendencia.teto`):

| Série | Casa média no corte | Inclinação pp/dia (ep) |
|---|---|---|
| Lula, 1º turno | 42,3 | +0,160 (0,023) |
| Lula, 2º turno | 45,5 | +0,061 (0,020) |
| Reserva de Lula | 3,2 | −0,099 (0,016) |
| Flávio, 1º turno | 40,1 | +0,209 (0,033) |
| Flávio, 2º turno | 46,0 | +0,042 (0,028) |
| Reserva de Flávio | 6,0 | −0,167 (0,019) |

O 2º turno de Lula ainda sobe um pouco, então o teto não é fixo. A reserva
dele fecha em ritmo que a esgotaria em cerca de um mês, não em um dia. A
Nexus mede o mesmo pelo eleitor (p. 46): voto 42, piso 39, teto 44 para Lula;
37, 34 e 39 para Flávio. Nas duas medidas, o espaço de Flávio é maior ou
igual ao de Lula, e nenhuma delas mostra Lula batendo no teto antes de 04/10.

## 7. Recomendação sobre a central

Critério combinado: MAE pareado não pior que a central no horizonte de 1 a 3
dias **e** viés menor em módulo.

- **Âncora de tendência (DLM amortecido): não passa.** MAE pareado +0,26
  (ep 0,15) pior e viés +1,63 contra +1,17. Recomendo não torná-la central. Ela
  fica no seletor e nas sensibilidades.
- **Central + inclinação encolhida de 28 dias: passa em ponto.** MAE −0,12
  (ep 0,15) e viés +0,42 contra +1,17; deixando a casa fora, −0,09 (ep 0,12).
  A melhora não é estatisticamente distinguível de zero e foi escolhida entre
  quatro variantes. Se a decisão for corrigir o nível pela tendência, esta é a
  única forma defensável: ela move a diferença F−L do cenário completo de
  −1,48 para −1,17 pp (0,31 pp na direção de Flávio). Publicá-la como
  sensibilidade principal, com o rótulo "extrapolação de tendência das
  pesquisas, não medição da urna", é a opção de menor risco.

Decisão posterior (03/10, noite): a troca foi feita. A central passou a ser
`central_inclinacao`, com indecisos por disponibilidade; `inclusivo` continua
no seletor como "Recência sem tendência (central até 03/10 à tarde)".

## 8. Limites

- Tudo aqui mede pesquisas, não a urna. Viés comum a todas as casas continua
  fora do alcance de qualquer âncora e permanece no Monte Carlo.
- A matriz declarada é preferência de 2º turno do eleitorado de terceira via,
  não o destino de quem abandona o candidato no 1º turno; quem abandona pode
  ser justamente quem está mais perto de um finalista.
- A síntese mistura fluxo líquido e preferência declarada; o desvio dela é só
  amostral.
- A divisão estadual usa o n da ficha atual para as rodadas anteriores da
  Quaest, hipótese conferida nas 13 UFs em que as duas rodadas têm ficha
  própria (n idêntico).
