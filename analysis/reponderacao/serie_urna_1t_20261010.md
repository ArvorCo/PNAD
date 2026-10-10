# Série principal do primeiro turno até a urna — 10/10/2026

A página arquivada passa a abrir a análise com o agregador em votos válidos,
seguido dos placares finais e da mudança até o resultado oficial. O resultado
não é incorporado à curva das pesquisas. A série anterior sobre o total de
entrevistados e a predição algorítmica arquivada permanecem preservadas.

## Regra

- Mesmas casas com renda do agregador principal; última onda por casa na janela
  retrospectiva de sete dias pela divulgação, peso igual. Sem onda elegível,
  média ausente. Pontilhado somente visual; sem preenchimento numérico.
- Cada vetor completo de candidaturas vira 100% dos válidos antes da média.
  Todas as candidaturas além de Flávio e Lula compõem o bloco “demais”. Isso
  permite acompanhar ondas antigas com cédulas diferentes sem eliminar seus
  votos do denominador. Indecisos não são convertidos; comparecimento não é
  ajustado. É média descritiva, distinta da predição experimental.
- Ajuste de renda parcial: candidatura sem cruzamento mantém o publicado.
  Resíduos negativos truncados antes da normalização, como na auditoria da
  apuração. Datafolha e Quaest finais continuam condicionadas ao perfil de
  renda da onda anterior, explicitado nas fichas e na lista de casas.
- Corte em 03/10; janela final 27/09–03/10, dez casas. Não inclui as casas sem
  renda; a auditoria inclusiva de treze casas permanece na apuração.
- Urna em 04/10: denominador oficial **119.300.788 votos válidos**. A fonte
  `presidente.json` tem um subtotal `terceiros` além das candidaturas: não
  somá-lo novamente. Demais = válidos − votos de Flávio − votos de Lula.
- Histórico recalculado com os documentos disponíveis hoje; não representa
  versões publicadas em cada data. Nenhuma pesquisa ou parâmetro recalibrado
  usando a urna. A diferença até a urna mistura erro e escolhas finais, sem
  identificar migração individual.

## Resultado final, em % dos válidos

| Bloco | Publicado (mesmas 10) | PNAD (mesmas 10) | Urna | Urna − PNAD, pp |
|---|---:|---:|---:|---:|
| Flávio | 43,05 | 43,88 | 47,03 | +3,15 |
| Lula | 45,43 | 44,45 | 45,16 | +0,72 |
| Demais | 11,52 | 11,67 | 7,81 | −3,86 |
| Diferença Flávio − Lula | −2,38 | −0,57 | +1,87 | +2,43 |

## Implementação e conferência

`scripts/reponderacao_vista/urna_serie.py` calcula e exporta;
`urna_serie_view.py` desenha o gráfico e os cartões. Integração somente no
arquivo do primeiro turno, antes da projeção, pelo gerador de rotas.
`docs/assets/reponderacao_urna_serie_1t.json` e `.csv` expõem datas, cobertura,
ondas, placares finais, auditoria e hashes das fontes locais.

Testes cobrem normalização antes da média, peso igual por casa, corte temporal,
limites da janela, ausência de dados, exclusões, vetores parciais, sinais e
paridade com a auditoria final. Conferência visual em 1440, 768 e 390 px, mais
390 px sem JavaScript: sem transbordamento do corpo ou erros de execução;
gráfico rolável e detalhes abrem em todos os modos.
