# Machine learning na previsão presidencial de 2026: avaliação

Corte: 03/10/2026. Eleição: 04/10/2026. Números desta nota vêm de
`docs/assets/predicao_2026_1T_presidente.json` (chaves `nacional.dinamico`,
`nacional.alvos`, `sensibilidades`, `validacao_preditiva`) e de
`docs/assets/predicao_2026_validacao_preditiva.json`, gerados por
`python3 scripts/predicao-2026-build.py --hoje 2026-10-03`.

## Resposta curta

Não. Para este problema, nesta eleição, um algoritmo supervisionado de machine
learning não deixaria o modelo mais correto. Deixaria o modelo mais
confiante sem base para isso. O que a literatura usa para agregar pesquisas
e prever eleição não é aprendizado supervisionado. É um modelo estatístico
de espaço de estados: um filtro que separa o movimento real do eleitorado do
ruído de cada pesquisa e do desvio próprio de cada instituto. Esse modelo foi
implementado agora como âncora alternativa (DLM, `scripts/predicao_2026/dinamico.py`)
e testado contra a âncora atual. Ele não venceu. A âncora central continua a
mesma.

## 1. O que um modelo supervisionado exigiria

Um modelo supervisionado aprende uma função f(x) → y a partir de muitos pares
observados (x, y). Aqui:

- x seria o estado das pesquisas a d dias da eleição: média, dispersão
  entre casas, tendência, efeitos de casa, indecisos, talvez variáveis
  estruturais (aprovação, economia).
- y seria o resultado oficial do TSE na mesma eleição e na mesma unidade
  (Brasil ou UF).

O ponto que decide tudo é que **a unidade independente é a eleição, não a
pesquisa nem a UF**. As 38 ondas nacionais de 2026 não são 38 exemplos: todas
compartilham o mesmo erro comum em relação à urna de amanhã, e esse erro é
justamente o que se quer aprender. As 27 UFs de uma mesma eleição também não
são 27 exemplos independentes: um deslocamento nacional move todas juntas. O
trabalho de Shirani-Mehr, Rothschild, Goel e Gelman (2018) mostra, em
pesquisas eleitorais estaduais dos Estados Unidos, que o erro total das
pesquisas é bem maior que o erro amostral declarado e que boa parte dele é
viés comum dentro de cada eleição. Com uma ou duas eleições de treino, esse
componente tem um ou dois sorteios.

Um gradient boosting, uma rede neural ou mesmo uma regressão regularizada
precisariam, para estimar com honestidade uma função de dezenas de entradas,
de dezenas de eleições comparáveis com pesquisas arquivadas no mesmo formato.
A regularização reduz a variância do ajuste; não cria eleições que não
existem.

## 2. O que o repositório tem (conferido em 03/10/2026)

- **Resultados oficiais do TSE de 2018 e 2022**, por seção e por
  município/zona: `data/raw/tse_resultados/detalhe_votacao_secao_2018.zip`,
  `detalhe_votacao_secao_2022.zip`, `votacao_candidato_munzona_2018.zip`,
  `votacao_candidato_munzona_2022.zip`, `votacao_partido_munzona_2022.zip`,
  resumos em `data/raw/tse_resultados/api_2022/` e por UF em
  `analysis/voto_util/tse_2022_uf.json`.
- **Pesquisas só de 2026.** As pastas de `data/originals/` com relatórios de
  institutos vão de `*_052026*` a `*_102026*`, e as fichas de
  `analysis/reponderacao/pesquisas/` começam em maio de 2026. Busca por
  pesquisas de 2018 ou 2022 (`ls data/originals`, `grep` em `analysis/` e
  `docs/assets/`) não encontrou nenhuma transcrição nem PDF arquivado.

Portanto, o número de pares (pesquisa, resultado) disponíveis para treino é
**zero**. Mesmo arquivando as pesquisas finais de 2018 e 2022, seriam dois
pares no nível nacional.

## 3. Por que treinar ML agora seria ajuste a ruído

1. **Sem rótulo.** O resultado de 2026 não existe antes de amanhã. Usar 2022
   exige as pesquisas de 2022, que não estão no acervo.
2. **Uma eleição de referência não identifica o erro comum.** Qualquer
   coeficiente aprendido de 2022 (por exemplo, "as pesquisas subestimaram a
   direita") seria a medida de um único sorteio de um erro que muda de
   sinal e tamanho entre eleições. Jennings e Wlezien (2018), "Election
   polling errors across time and space" (*Nature Human Behaviour*), com
   pesquisas de dezenas de países, documentam que o erro médio das
   pesquisas de véspera é estável no agregado, mas varia muito de uma
   eleição para outra.
3. **Mudança de regime.** 2026 tem candidatos diferentes, casas novas
   (Palver, Gerp, Alfa, Indexa), métodos novos (painéis digitais) e
   reponderação PNAD própria da Arvor. Um modelo treinado em 2018 e 2022
   extrapolaria fora do domínio.
4. **Graus de liberdade.** Com 38 ondas, 14 casas e 5 categorias, qualquer
   modelo flexível tem mais parâmetros que informação independente sobre o
   que importa (o nível da urna).

O que **dá** para fazer com rigor dentro de 2026, sem urna, é medir quão bem
cada regra prevê a **próxima pesquisa**. Isso foi feito (seção 6). Mede
capacidade de rastrear o consenso das pesquisas, não acerto eleitoral.

## 4. O estado da arte real

O padrão na ciência política quantitativa é o **modelo dinâmico Bayesiano de
espaço de estados**:

- **Jackman (2005), "Pooling the polls over an election campaign"**,
  *Australian Journal of Political Science*. A intenção de voto verdadeira é
  um passeio aleatório diário; cada pesquisa a observa com erro amostral e
  um **efeito de casa** constante. A identificação exige uma âncora: Jackman
  usa o resultado da eleição anterior nas pontas da série; sem ela, a soma
  zero dos efeitos de casa é a hipótese.
- **Linzer (2013), "Dynamic Bayesian forecasting of presidential elections
  in the states"**, *Journal of the American Statistical Association*.
  Passeio aleatório por estado com componente nacional comum, pooling parcial
  entre estados e uma prior estrutural (modelo de fundamentos, como
  aprovação e economia) para o dia da eleição. Longe da eleição a prior
  domina; perto, as pesquisas.
- **Heidemanns, Gelman e Morris (2020), "An updated dynamic Bayesian
  forecasting model for the US presidential election"**, *Harvard Data
  Science Review*. Base do modelo da The Economist
  (código em https://github.com/TheEconomist/us-potus-model). Acrescenta
  erros correlacionados entre estados, efeitos de casa, de modo de coleta e
  de população (eleitor registrado ou provável), e um termo de erro
  não amostral comum.
- **Shirani-Mehr, Rothschild, Goel e Gelman (2018), "Disentangling bias and
  variance in election polls"**, *Journal of the American Statistical
  Association*. Mede o erro total de pesquisa: viés comum por eleição e
  variância excedente além da amostral.
- Referências de método: Harvey (1989), *Forecasting, structural time series
  models and the Kalman filter*; Durbin e Koopman (2012), *Time series
  analysis by state space methods*.

### O que já existe no motor da Arvor

| Componente do estado da arte | No motor atual |
|---|---|
| Ponderação temporal das pesquisas | Sim. Decaimento exponencial pelo meio do campo, meia-vida de 3 dias. Um filtro de nível local em regime estacionário é exatamente uma média móvel exponencial; ver seção 5. |
| Erro amostral por n e efeito de desenho | Sim, deff 1,5 no bootstrap e no pooling estadual. |
| Pooling parcial estadual com prior | Sim. Log-proporções com prior territorial de 2022 (350 unidades) e movimento nacional contemporâneo. |
| Coerência nacional dos estados | Sim. Raking IPF às margens nacionais, também por réplica no Monte Carlo. |
| Erro comum de pesquisa | Sim, Student-t com 5 graus de liberdade e 2 pp de desvio na diferença. **Assumido, não calibrado.** |
| Erro regional correlacionado | Sim, 1 pp por região, assumido. |
| Efeitos de casa | Diagnóstico (`nacional.efeitos_casa`) e cenário "casas"; fora da central. |
| Passeio aleatório com variância estimada | **Novo**: âncora "dinamico". |
| Erro não amostral estimado | **Novo**: o DLM estima o multiplicador phi. |
| Posterior conjunta (estado nacional, estados, casas) | Não. O motor é modular: âncora nacional, depois geografia, depois Monte Carlo. |
| Prior estrutural (fundamentos) | Não, e não deve haver sem histórico brasileiro arquivado que a valide. |
| Dinâmica temporal por UF | Não. Estaduais entram com decaimento de 7 dias e movimento nacional, sem passeio aleatório próprio. |

## 5. A âncora dinâmica implementada

`scripts/predicao_2026/dinamico.py`, exposta em `base.national` como
`nacional.alvos.dinamico`, com detalhes em `nacional.dinamico`.

**Modelo.** Estado = nível das cinco categorias (Lula, Flávio, demais,
indecisos, branco/nulo) na escala aditiva, em passeio aleatório de tempo
contínuo, mais um efeito constante por casa. Observação = vetor da onda no
ponto médio do campo (PNAD quando há cruzamento, publicado nas demais, o
mesmo `previsao_vetor` da central). As covariâncias vivem no subespaço de
soma zero, então o filtro usa quatro categorias e branco/nulo é complemento,
sem dependência da categoria omitida.

- Erro de observação: phi × (diag(p) − pp′) × 1,5 / min(n, 2000).
- Evolução: q × (diag(m) − mm′) por dia, m = média das ondas.
- Efeito de casa: prior N(0, S) com desvios por categoria, **condicionada à
  soma zero entre as casas** (hipótese de identificação: o nível é o que a
  casa média da janela mediria).
- Hiperparâmetros (q, cinco desvios de casa, phi) por máxima
  verossimilhança marginal do filtro de Kalman (scipy L-BFGS-B, três
  partidas).
- Janela: as mesmas 38 ondas da central, desde 15/08. Ampliar para 01/08 ou
  15/07 (46 e 51 ondas) foi testado na validação e não melhorou a previsão
  de pesquisas; a janela ficou igual à da central.

**Estimativas** (`nacional.dinamico.parametros`):

- phi = 2,10, isto é, deff efetivo de 3,15. A verossimilhança sobe de
  382,87 (phi = 1) para 392,37: as pesquisas variam bem mais do que o erro
  amostral declarado explica, como em Shirani-Mehr et al. (2018).
- Desvio diário do nível: 0,59 pp em Lula e 0,58 pp em Flávio.
- Desvio dos efeitos de casa: 3,66 pp em Lula, 5,69 pp em Flávio.
- Com essas variâncias, o filtro em regime estacionário equivale a uma média
  exponencial com meia-vida de cerca de 2,6 dias (aproximação para uma
  categoria, 0,78 onda por dia e n = 2.000). A meia-vida de 3 dias da
  central, escolhida antes, fica próxima do que os dados estimam.

**Vetor da âncora em 03/10** (`nacional.alvos`, em % do total):

| Âncora | Lula | Flávio | Demais | Indecisos | Branco/nulo |
|---|---|---|---|---|---|
| Central (recência) | 40,41 | 39,98 | 12,55 | 3,45 | 3,61 |
| Dinâmica (DLM) | 41,19 | 39,72 | 12,26 | 3,40 | 3,42 |

Nos válidos, o estado final do DLM é Lula 44,21 × Flávio 42,63, diferença
F−L de −1,58 pp com desvio de 2,71 pp. Depois da geografia, do eleitor
provável e da contagem de votos, o cenário "Âncora dinâmica" dá Lula 44,72 ×
Flávio 42,62 (F−L −2,09), contra 44,00 × 43,01 (F−L −0,98) da central
(`sensibilidades`). Variantes: phi = 1 dá F−L −1,12 nos válidos da âncora;
só ondas com PNAD, −1,40.

**Efeitos de casa** (efeito na diferença L−F dos válidos, em pp; positivo =
mais Lula que a casa média): MDA +7,19 (1 onda), Alfa +4,99 (1), Quaest +4,99
(5), Indexa +3,00 (1), AtlasIntel +0,71 (3), Nexus +0,55 (7), Vox −0,24 (2),
Meio/Ideia −1,28 (1), Real Time −1,31 (3), PoderData −2,29 (1), Palver −2,37
(4), Datafolha −3,51 (6), Futura −4,27 (2), Gerp −6,14 (1). Casas com uma
onda têm desvio de cerca de 3,2 pp. Isso descreve desvio relativo às outras
casas, não erro contra a urna.

**Incerteza no simulador.** Para a âncora dinâmica o navegador reutiliza o
bootstrap das casas centrais e o recentra no estado final do DLM (desloca o
alvo sorteado por `alvos.dinamico − alvos.inclusivo`). Assim o erro comum,
regional e de comparecimento continua o mesmo de todas as âncoras, e o
desvio do estado final (2,71 pp na diferença) fica registrado no JSON sem
ser somado duas vezes.

## 6. Validação preditiva (sem urna)

`scripts/predicao_2026/preditiva.py`. Para cada origem t de 01/09 a 01/10,
cada âncora usa só ondas divulgadas até t e prevê as ondas com campo iniciado
1 a 7 dias depois. O DLM reestima seus hiperparâmetros a cada origem. Erro em
pontos dos válidos; margem = Lula − Flávio. **Isto mede previsão de
pesquisas, não da urna.**

Origem móvel, 204 pares, 31 ondas alvo:

| Âncora | MAE margem | RMSE margem | Viés margem | MAE parcelas |
|---|---|---|---|---|
| Recência 3 dias, janela 7 (central) | 3,43 | 4,05 | +1,25 | 2,93 |
| Recência 1 dia, janela 7 | 3,61 | 4,48 | +0,29 | 2,99 |
| Recência 5 dias, janela 7 | 3,46 | 4,08 | +1,45 | 2,96 |
| Recência 7 dias, janela 7 | 3,48 | 4,11 | +1,53 | 2,98 |
| Peso igual, janela 7 | 3,57 | 4,22 | +1,73 | 3,03 |
| Recência 3 dias, janela 14 | 3,42 | 4,03 | +1,26 | 2,99 |
| Peso igual, janela 14 | 3,52 | 4,18 | +1,82 | 3,29 |
| DLM, phi estimado | 3,53 | 4,19 | +1,83 | 3,53 |
| DLM, phi = 1 | 3,47 | 4,14 | +1,50 | 3,29 |

Comparação pareada por onda alvo (média dos horizontes): DLM menos central
= +0,10 pp de MAE, erro-padrão 0,14; o DLM foi melhor em 14 de 31 ondas.
Meia-vida de 5 dias menos 3 dias: +0,03 (erro-padrão 0,05). Peso igual menos
recência: +0,14 (0,10). **Nenhuma alternativa separa da central.** Não há
ajuste barato de meia-vida claramente melhor: 3 dias tem o menor MAE entre as
janelas de 7 dias, e a janela de 14 dias empata (3,42).

Deixando a casa do alvo fora (32 ondas): central 3,76, DLM 3,84 (diferença
+0,07, erro-padrão 0,24). Sem separação.

Prevendo a próxima onda de uma casa já conhecida (115 pares, 19 ondas): DLM
com o efeito da casa 2,07 de MAE, última onda da mesma casa 1,92, central
3,19. Os efeitos de casa são reais e persistentes (o DLM com efeito de casa
bate a central por 1,20 pp, erro-padrão 0,38), mas isso serve para prever a
próxima pesquisa de um instituto, não o nível do país.

O viés positivo de todas as âncoras (+1,25 a +1,83 na margem L−F) diz que,
em setembro, as pesquisas seguintes vieram sistematicamente menos favoráveis
a Lula do que a média anterior: houve tendência, e nenhuma âncora sem termo
de deriva a antecipa. A meia-vida de 1 dia reduz esse viés (+0,29), ao custo
de mais variância e RMSE maior.

## 7. Onde machine learning seria defensável

**Defensável, quando houver acervo:**

1. **Aprender hiperparâmetros por validação entre eleições**: meia-vida ou
   variância de evolução, encolhimento dos efeitos de casa, desvio do erro
   comum, correlação regional, peso da prior territorial. Exige pesquisas de
   2014, 2018 e 2022 (nacionais e estaduais) arquivadas com documento, mais o
   resultado do TSE. É estimação de poucos parâmetros com validação cruzada
   por eleição, não uma rede neural.
2. **Calibração das faixas de incerteza** (por exemplo, calibração conformal
   ou ajuste do desvio do erro comum) com erros históricos de véspera por
   eleição e UF.
3. **Pesos de combinação entre âncoras** (stacking) aprendidos em eleições
   passadas, com restrição de soma um e poucas âncoras.

**Não defensável:**

1. Gradient boosting, florestas ou redes mapeando pesquisas para resultado
   com uma ou duas eleições de treino.
2. Tratar as UFs de uma eleição, ou as ondas de uma campanha, como exemplos
   independentes.
3. Usar a série de 2026 para "aprender" o resultado de 2026: o único rótulo
   disponível antes da urna é a própria pesquisa, e prever pesquisa não
   corrige o erro comum das pesquisas.

## 8. Pendência: calibrar o erro comum

O desvio de 2 pp do erro comum na diferença F−L (`configuracao.incerteza`) é
assumido. Calibrá-lo com os erros das pesquisas finais de 2018 e 2022 contra
o TSE ficou **pendente**, porque o repositório não tem essas pesquisas e a
regra da casa exige documento arquivado. Para fazer:

1. Baixar os relatórios das últimas ondas antes do 1º turno de 2018 e de 2022
   de cada casa com registro nacional (Datafolha, Ibope/Ipec, Quaest,
   AtlasIntel, PoderData, Paraná Pesquisas, entre outras), cada um em
   `data/originals/<casa>_<MMAAAA>/` com URL, SHA-256 e página do placar.
2. Transcrever votos válidos, campo, n e registro, no mesmo formato das
   fichas de 2026.
3. Calcular, por eleição, o erro da média das casas na diferença dos dois
   primeiros contra `votacao_candidato_munzona_<ano>.zip`.
4. Mesmo assim serão dois pontos. O desvio estimado deve ser publicado como
   referência, combinado com a literatura internacional (Jennings e Wlezien,
   2018), e não como calibração.

## 9. Limitações da âncora dinâmica

- A soma zero dos efeitos de casa define o nível pela casa média. Se a
  maioria das casas errar na mesma direção, o DLM erra junto. Esse erro só
  está no Monte Carlo, com desvio assumido.
- O passeio aleatório não tem deriva. Em campanha com tendência, todas as
  âncoras ficam atrás; a validação mostra isso.
- Os efeitos de casa são constantes no tempo. Mudança de método no meio da
  campanha (por exemplo, perfil de renda da Atlas em setembro) vira
  movimento do nível ou resíduo.
- Escala aditiva com truncamento e normalização no fim; nas categorias
  pequenas (indecisos, branco/nulo) a aproximação gaussiana é mais fraca.
- Hiperparâmetros estimados com 38 ondas; o desvio dos efeitos de casa
  depende muito das casas com uma onda só.
