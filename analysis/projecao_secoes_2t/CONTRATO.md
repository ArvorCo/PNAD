# Projeção territorial do segundo turno — protocolo de desenvolvimento

Corte: 19/10/2026. Esta versão experimental combina apuração por seção, transporte histórico e pesquisas pós-primeiro turno. Preserva as duas centrais já publicadas. Não é reconstrução do código de Pedro Werneck: as nove imagens fornecidas inspiram a comparação de métodos, mas não especificam um algoritmo reproduzível completo.

## Unidades e identidades

Uma linha atual corresponde ao boletim da seção principal; agregadas não são votos adicionais. Chave: UF, município TSE, zona, seção. Aptos = direita + esquerda + outros + branco/nulo + ausentes. Para 2018, direita é Bolsonaro/17 e esquerda Haddad/13; para 2022 Bolsonaro/22 e Lula/13; em 2026 Flávio/22 e Lula/13. São rótulos de correspondência entre finalistas, não equivalência entre candidatos.

Ler os dois turnos dos ZIPs do TSE, casar chaves e nome normalizado do local, exigir partições completas, reportar perdas. Modelar proporções em cada eleitorado quando aptos mudam. Limites de transferência individual só se calculam no subconjunto com aptos idênticos, sob hipótese adicional de população fechada (mesmo total tampouco prova mesmas pessoas).

## Comparação declarada antes dos resultados

Aprender somente em 2018, prever 2022. Não sortear seções da mesma eleição para alegar validação temporal. Comparar: divisão 50/50 dos terceiros; divisão proporcional aos finalistas na própria seção; deslocamento histórico de log-odds por UF; deslocamento da própria seção, encolhido para município/UF; matriz de transição ecológica não negativa por UF; matriz com contexto do voto inicial. Usar RMSE ponderado das parcelas válidas por UF como critério principal, erro nacional assinado e erro por seção como diagnósticos. A seleção numa única eleição é exploratória; relatar todos os métodos. Se o método complexo não vence, não promovê-lo por ser complexo.

Matrizes têm cinco origens (finalistas, terceiros, BN, ausência) e quatro destinos (finalistas, BN, ausência). Linhas não negativas somam um. Ajustar por mínimos quadrados ponderados por aptos, com penalização hierárquica: UF contra Brasil; contexto por UF contra UF. Cortes contextuais prévios: parcela da direita entre finalistas menor que 35%, entre 35 e 65%, acima de 65%. Penalidade fixa equivalente a 50 mil aptos na UF e 20 mil no contexto. São hipóteses de regularização, não tamanhos amostrais medidos.

O modelo por seção usa o deslocamento histórico em log-odds, encolhido com 500 votos equivalentes para o município; município com 5 mil para UF. Se o local muda ou não há chave anterior, usa município/UF. A soma de seções continua sendo o país. A matriz descreve uma alocação compatível sob hipóteses; não identifica a migração individual. Limites de Duncan–Davis são publicados para expor a informação efetivamente disponível.

## Pesquisas e prudência

Pesquisas nacionais recentes são uma segunda medição, não seções adicionais. A versão avançada deve expor transporte sem pesquisas, pesquisas isoladas e combinação. Variância nacional de transporte não pode encolher com centenas de milhares de seções; um erro comum permanece. Estados com pesquisa são atualizados com recência e erro de casa, sem transportar pesquisas pré-04/10 nem tratá-las como casas nacionais. Toda calibração deve publicar o deslocamento aplicado. Inferência de transferência, comparecimento e preferência são dimensões diferentes.

Não há base para probabilidade de vitória validada com uma retrospectiva. Faixas serão sensibilidades condicionais e não confiança eleitoral calibrada. O resultado local é expectativa fracionária agregada, nunca perfil de uma pessoa, lista de persuasão ou certeza sobre vizinhos.

## Referências

- [TSE, dados de 2018](https://dadosabertos.tse.jus.br/dataset/resultados-2018) e respectivos arquivos de 2022; URLs e SHA-256 nos manifestos.
- [Jiang, King, Schmaltz e Tanner, Ecological Regression with Partial Identification](https://gking.harvard.edu/publication/ecological-regression-with-partial-identification/): identificação parcial e limites, não autorização para confundir marginais com movimentos individuais.
- [Imai, Lu e Strauss, Bayesian and Frequentist Approaches to Ecological Inference](https://imai.fas.harvard.edu/research/files/eiall.pdf).


## Resultado da rodada e uso da versão

A retrospectiva selecionou a divisão proporcional local (RMSE estadual 1,73 pp; erro nacional −1,71 pp). Matrizes de UF/contexto: 2,20/2,28 pp. Transporte direto de deslocamento: 10,64/11,26 pp. Não houve promoção de matriz pela proximidade com os números da referência. Aplicadas a 2026, matrizes dão F 52,53–52,65%; proporcional local, 51,28%.

A combinação experimental usa 47,78% de peso para a âncora PNAD inclusiva das pesquisas (50,49% F) e 52,22% para proporcional local. Resultado 50,90% F. Piso de desvio histórico de 2 pp, pesquisas com erro comum de 2 pp, parcela amostral/entre casas e incerteza da tendência. Independência entre erros é hipótese. Não reaplica o resíduo relativo +3,8% das centrais antigas: o transporte da apuração já incorpora composição e presença. Essa fusão completa não foi validada retrospectivamente; as pesquisas de 2022 arquivadas no projeto são do primeiro turno, não podem ser tratadas como pesquisas do segundo.

Estaduais Quaest nas seis UFs com disputa de governador atualizam a distribuição antes da calibração nacional; não reduzem a incerteza nacional. Fonte original do contratante arquivada, incluindo inconsistências de registros no texto. O registro não foi conferido no PesqEle nesta rodada. Cobertura 7,92% do eleitorado; não generalizar para UFs não pesquisadas.

Unidades atuais: 496.580 boletins auditados, mais três resíduos municipais (Betim, Uberlândia, Carapicuíba), cobrindo 157.828.968 aptos. Exterior separado, sem extrapolar PNAD ou pesquisas nacionais. Não há previsão individual, probabilidade validada de vitória nem substituição automática das centrais existentes.
