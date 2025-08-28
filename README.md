Esse projeto é sobre a exploração da PNAD Contínua do IBGE.

Pegamos todos os microdados mais recentes da pesquisa.

O objetivo é simples: precisamos conseguir ter um software capaz de me dizer a porcentagem de pessoas em todo o Brasil considerando as seguintes faixa de renda:

1) 0 a 2 Salários Mínimos
2) 2 a 5 Salários Mínimos
3) 5 ou mais salários mínimos

Também precisaremos de outras faixas que podem depois ser passadas com valores específicos de faixa de renda.

Nosso objetivo é criar um notebook python exploratório desses dados utilizando o melhor conjunto de ferramentas de análise de dados numéricas e gráficos possível para chegarmos a esse resultado de forma relevante e inteligente.

Na pasta temos os seguintes arquivos:
- INPUT_SNIPC_PNADC.sas.txt que é usado por sistemas SAS para analisar os dados
- INPUT_SNIPC.txt que é uma tabela explicativa dos meses e códigos relacionados
PNADC_012025.txt e PNADC_022025.txt que contém os microdados da pesquisa
Variáveis_PNADC_Trimestral.xls, contendo o dicionário de dados completo dos microdados, que incluem dados de múltiplos anos.

- Definicao_variaveis_derivadas.pdf, que documenta alguns detalhes sobre o parsing de microdados.

Vamos trabalhar com o que há de melhor em análise numérico/matemática estatística, pois nossa base é muito grande e acredito que vamos precisar do melhor dos dados.

Eu acredito que os dados PNADC_022025.txt contém os dados do outro arquivo 01, portanto não será necessário processar os dois arquivos, provavelmente.

