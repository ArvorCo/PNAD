# Projeção documental de votos válidos por onda

Implementação: `scripts/reponderacao_vista/historico_projecao.py`; transcrições em
`presenca.json`; triagem do acervo em `presenca_acervo.json`. A interface e os
exports são gerados por `reponderacao-build.py`. Não recalcula centrais, não
retroage a predição e não muda snapshots publicados.

## Regra

Para candidato c, massa selecionada A_c = V_c × q_c. O cenário converte 100% da
massa identificada de indecisos I, selecionada por q_I, proporcionalmente às
massas A: transferência_c = I × q_I × A_c / soma(A). Os válidos finais são a
normalização de A + transferência. Essa alocação NÃO muda a razão F/L; o eventual
efeito vem da seleção por presença. BN continua fora; BN+NS inseparáveis não são
desagregados. Não se atribui uma falsa taxa de comparecimento nacional.

- Ipespe 10/10 e 17/10: proporção que responde nota 10 de chance de comparecer,
  por candidato e entre indecisos (p. 12). Trata-se de um filtro de autodeclaração,
  não de probabilidades calibradas. Aplicar q à PNAD assume estabilidade após
  mudar a composição de renda. O placar do subconjunto na p. 13 é preservado na
  evidência; números arredondados da p. 12 não precisam reproduzi-lo exatamente.
- Nexus 13/10 e 19/10: soma de ida certa e provável por renda (p. 18).
- Veritá 21/10: certeza de ida por renda (p. 6).
- Nos dois últimos casos, q_c = soma(w_g × voto_cg × presença_g) /
  soma(w_g × voto_cg). w é o perfil publicado na projeção do publicado e a
  distribuição PNAD na projeção PNAD. A taxa é aplicada ao topline ancorado,
  conservando os resíduos da recomposição. Hipótese ecológica: voto e presença
  independentes dentro da renda. Não há cruzamento individual que a valide.
- Sem evidência própria incorporada: q=1 como peso relativo neutro, não como
  previsão de 100% de comparecimento. O resultado é normalização simples.
- Onda divulgada apenas em válidos: preservar o placar; total, indecisos e ajuste
  de renda permanecem indisponíveis. Não converter essa onda para total.

Cada pergunta de presença é do segundo turno da própria onda. Nexus anteriores
à urna perguntou sobre presença no primeiro turno: não transportar ao cenário
hipotético de segundo turno. Firmeza, rejeição, interesse, aprovação e voto
lembrado não são substitutos identificados de presença futura. A triagem textual
não demonstra ausência de perguntas em páginas gráficas; somente as transcrições
conferidas ativam seleção diferencial. A auditoria da última onda por casa está
exposta na interface, incluindo íntegras pendentes.

As comparações temporais também refletem mudança de instrumento, seleção e
cobertura. O checkbox não transforma essas regras distintas em um modelo
homogêneo validado. Não usa tendência, taxas de outra casa nem o ajuste relativo
extra de 3,8% das centrais.

## Urna e linhas

Atlas 03–08/10 atravessa o primeiro turno: a ficha preserva esse fato. As linhas
agora separam fases pelo encerramento do campo; 08/10 liga a 18/10, mas uma onda
encerrada antes da urna não é ligada à primeira encerrada depois.

Losangos em 04/10: urna do PRIMEIRO turno, incluindo exterior, proveniente de
`analysis/apuracao_2026/dados/presidente.json`. Total = válidos + brancos + nulos;
válidos incluem TODAS as candidaturas. Nunca normalizar só F e L nesse marco.
Não há urna de segundo turno na data desta implementação (21/10).

Balanço por casa: última pesquisa de PRIMEIRO turno comparável, com campo e
publicação até 04/10. Usa o balanço congelado de apuração; quando só existe onda
mais antiga compatível no acervo, mostra sua data. Não usa cenários hipotéticos
de segundo turno para medir erro. Totais de entrevistados e de votos depositados
são universos diferentes; indecisos existem somente na pesquisa. Erro = pesquisa
menos urna; na vantagem F−L, positivo favorece F relativamente ao resultado.
Não se aplica likely voter a esse balanço retrospectivo.

## Validação

Transcrições de presença: renderização visual das páginas citadas e SHA-256 da
íntegra. Testes de conservação, alocação proporcional, ausência de transporte,
bases válidas exclusivas, dados de renda faltantes, ponte Atlas e denominador da
urna em `tests/test_reponderacao_historico_projecao.py`. Testes documentais
existentes continuam exigindo todas as ondas e versões. Interação do checkbox e
legibilidade verificadas no navegador após publicação.
