# Encerramento e recebimento do BU, segundo turno de 2026

Implementação de 29/10/2026. Recriar dados e imagem com
`.venv/bin/python scripts/politize-se-transmissao-build.py`.
`--so-imagem` usa o índice já exportado; `--so-dados` atualiza apenas os dados.
O build do mapa aceita `--transmissao` para reexportar a camada após seu catálogo.

## Unidade e significado

Banco local `apuracao/data/secoes_2t_2026.sqlite`, aberto somente para leitura.
Usar as seções principais, sem multiplicar seções agregadas, e excluir ZZ.
O catálogo do mapa identifica cada local por UF, município TSE, zona e local.
Dois locais oficiais no mesmo prédio continuam unidades diferentes nesta análise.

O intervalo de uma seção é o carimbo `dr/hr` do pacote selecionado no `aux.json`
menos `dadosSecao.dataHoraEncerramento` do BU. O segundo carimbo é o encerramento
usado nesta análise, não uma coluna CSV com nome literal DT_ENCERRAMENTO.
O extrator existente armazena os dois eventos em `bu.encerramento` e `secao.dr_hr`.
`bu.emissao` é uma terceira etapa e aparece na tabela por seção.

O carimbo do pacote é tratado como recebimento, não como início do envio, duração
da conexão ou publicação do placar. O coletor seleciona o pacote mais recente
com BU; não se deve chamar esse horário de primeira transmissão em todos os casos.
Neste extrato todas as 497.897 seções nacionais têm um único pacote catalogado.
Mais de um pacote em extratos futuros fica sem classificação automática.

Os horários do BU são locais; os do pacote são de Brasília. Converter apenas os
primeiros usando `apuracao_2t_2026.encerramento_dados.deslocamento`, incluindo o
Acre, a divisão municipal do Amazonas e Fernando de Noronha. Preservar segundos
e datas completas, inclusive recebimento posterior à meia-noite.

## Validação e cobertura

O gerador confere identidade/pleito, unicidade de seção no catálogo, igualdade do
carimbo com o hash selecionado no aux arquivado e recomposição de cada local.
O índice registra SHA-256 do extrato ordenado, com horários, aux e hash do BU,
além de hashes e tamanhos dos 27 arquivos compactados. O banco pesado não é copiado.

Há 497.881 seções com cronologia utilizável em 94.084 dos 94.094 locais oficiais.
Três seções têm recebimento anterior ao encerramento; outras 13 têm ordem
inconsistente entre encerramento, emissão e recebimento. Não corrigir nem zerar
intervalos negativos. Preservar os carimbos e motivos; excluir esses 16 registros
dos quantis, cores e rankings. Dez locais ficam sem intervalo utilizável.

## Cor, atenção e comparação dentro do local

Calcular primeiro o intervalo de cada seção. A cor do local usa seu máximo, nunca
o último recebimento menos o primeiro encerramento de seções diferentes.
Grupos de pontos usam o maior intervalo entre as seções representadas. Os filtros
de horário recompõem o máximo, a mediana e a cobertura apenas no recorte escolhido.
Cinza significa ausência de cronologia utilizável. Falha de carregamento é exibida.

Faixas com limite superior inclusivo: até 1h; >1h até 2h; >2h até 3h; >3h até 4h;
>4h até 5h; >5h. Acima de 4h recebe “atenção ao intervalo”; acima de 5h, “muita
atenção ao intervalo”. São cortes exploratórios para priorizar conferência
documental, sem calibração como teste de irregularidade. A distribuição nacional
é mostrada para evitar tratar um intervalo frequente como excepcional.

A mediana nacional é 3h23min30s; a de encerramento até emissão é 2min. Há 105
seções acima de 5h, distribuídas por 34 locais. O maior intervalo é 6h16min20s:
Escola Municipal de Paramana, Salvador/BA, zona 4, seção 374.

A ficha também compara a seção de maior intervalo com a mediana das demais
seções utilizáveis do local, excluindo a própria seção. Empates no máximo escolhem
a menor seção. Não há controle de logística ou estimativa de causalidade.
Em Manaus, E. M. Lucila Freitas, zona 58, seção 955: 3h56min47s contra mediana
de 6min nas outras oito seções. Esse contraste merece conferência própria mesmo
ficando abaixo do corte absoluto de 4h. Não possui um alerta causal separado.

## O que pode compor o intervalo

O [TRE-MG descreve o fluxo de transmissão e totalização](https://www.tre-mg.jus.br/comunicacao/noticias/2026/Setembro/saiba-como-e-feita-a-transmissao-e-totalizacao-dos-resultados):
emissão do BU, coleta e transporte da mídia, chegada a um ponto de transmissão,
envio e verificações. O intervalo observado pode abranger essas etapas e esperas.
O dado disponível não atribui uma causa a cada escola, seção ou município.

Para investigar um caso, confrontar ata, horários de coleta e entrega da mídia,
ponto e registros do Transportador/JE-Connect, conectividade, contingências,
eventuais reenvios e igualdade do BU impresso com o publicado. A distância temporal
isolada não demonstra alteração de votos. Os links por seção levam ao aux do TSE.

## Entregas e verificação

- `docs/assets/politize_se/transmissao/`: PNG/PDF, CSV por local, índice e 27 UFs.
- `docs/assets/politize_se/transmissao.js`: leitura e painel compartilhado.
- `docs/assets/politize_se_mapa/transmissao.js`: camada, legenda, agrupamento e CSV.
- `tests/test_politize_se_transmissao.py`: fusos, virada de data, inconsistências,
  limiares, paridade Python/JS, filtragem, agrupamento, hashes e recomposição nacional.
- QA de navegador em `tmp/transmissao_2t_2026/`: Chrome, larguras 390 e 1.440 px,
  mapa e ficha de seção, sem erro JS nem transbordamento horizontal da página.

A revisão de 29/10 inclui dados, gráficos e interfaces no pacote de publicação
do GitHub Pages. Não envia mensagens ou posts a redes sociais.
