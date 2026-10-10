# Transferência de indecisos — 10/10/2026

Os controles de conversão e destino saem de “Mais hipóteses” para o topo do
simulador. O destino ganha régua 0–100%, campo numérico em décimos, opção
50/50 e restauração da proporção automática. A imagem e o link registram a
divisão; a tela mostra tamanho na base, volume dos presentes, transferências
iniciais e efeito final contra a divisão automática.

## Fontes e dimensões

O acervo continua com referência de 09/10; esta rodada altera o simulador,
sem incorporar pesquisa nova. Indecisos publicados: Datafolha 1%, PoderData
2% e Vox Brasil 9,7%. A Média inclui as duas casas com renda; a Projeção inclui
Vox pelo publicado. Não transformar o 1% de uma casa em tamanho de toda a base.

Na base PNAD, Média: 1,3470% indecisos, 1,6503 milhão presente no cenário
central; Projeção: 3,8697%, 4,7452 milhões presentes. Seleção Nexus e presença
relativa alteram o peso dos que compareceriam; o percentual na base e o
volume entre presentes são denominadores diferentes. Fontes preservadas no
snapshot e publicadas em `#indecisos-fontes`.

## Regra e contabilidade

`undecided_policy="central_proportion"`: antes de converter indecisos ou
aplicar saídas extras e erro comum, calcular F/(F+L) entre os presentes de
cada pesquisa. Média simples dessas razões para a Média Arvor; razão da
âncora para a Projeção. Aplicar essa proporção comum a todos os indecisos
que escolhem candidato. `indecisos_flavio=None` mantém essa regra automática;
um número fixa uma divisão independente da central e dos outros controles.

Referências atuais: 55,0394% para Flávio na Média e 53,6161% na Projeção.
A referência acompanha base, idade e presença relativa. No Monte Carlo,
o destino automático fica fixado na âncora do cenário para todos os sorteios;
a faixa continua condicional ao destino escolhido, sem aprender migração.

A conversão central permanece em 100% dos indecisos presentes. É hipótese
editável, não observação. O complemento termina em branco/nulo; a abstenção
é controlada à parte. As transferências iniciais somam o pool presente.
Saídas adicionais e erro comum são aplicados depois. Impacto final = resultado
com a divisão escolhida menos resultado com divisão automática, mantendo todos
os demais controles, inclusive conversão, comparecimento e base.

Nas casas com quantidades distintas de indecisos, uma divisão comum não é
idêntica à regra antiga por pesquisa. A Média muda +0,0010 pp de Flávio
(55,0394% → 55,0405%); arredondada segue 55,0% × 45,0%. A Projeção permanece
53,6% × 46,4%. Todos para Lula ou Flávio são cenários extremos: efeito em
Flávio de −0,7617 ou +0,6222 pp na Média; −2,1268 ou +1,8400 na Projeção.
Não são previsões do destino dos indecisos.

Sem painel individual, não identificamos conversão real até a urna. A régua
mede consequências de hipóteses sobre o pool publicado, atualizado quando
novas ondas entram no build. Não há erro adicional de transferência estimado.

## Reprodução e preservação

`python3 scripts/reponderacao-build.py` atualiza a base e a interface.
`scripts/reponderacao-simulador.py` e seu espelho JS compartilham a regra;
`undecided()` fornece as dimensões e o impacto. Sem o campo de política,
o motor conserva exatamente a regra antiga por pesquisa. Snapshots e motores
publicados anteriores permanecem; o arquivo do primeiro turno não é recalculado.

Snapshot desta rodada: `a55474752ad0103a`; motor `47866e5493a4e9be`.
Testes específicos: exemplo de 1% com efeito de 0,5 pp em uma disputa empatada,
divisão comum em casas diferentes, conversão parcial, ausência preservada,
pool zero, Monte Carlo com destino fixo, paridade Python/JS e versões antigas.

Validação: 2.072 testes aprovados e 5 pulados na suíte completa; Ruff, Black,
sintaxe JS e sitemap aprovados. Chrome: duas centrais, proporção automática,
divisão livre/decimal, conversão parcial, entrada inválida, links, imagem,
versão antiga e telas de 360/390/768 pixels; nenhum erro no navegador.
