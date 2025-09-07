Esse projeto é sobre a exploração da PNAD Contínua do IBGE.

Pegamos todos os microdados mais recentes da pesquisa.

O objetivo é simples: precisamos conseguir ter um software capaz de me dizer a porcentagem de pessoas em todo o Brasil considerando as seguintes faixa de renda:

1) 0 a 2 Salários Mínimos
2) 2 a 5 Salários Mínimos
3) 5 ou mais salários mínimos

Também precisaremos de outras faixas que podem depois ser passadas com valores específicos de faixa de renda.

## Análises Implementadas

### 📊 Distribuição de Renda por Faixas
- **Individual**: Análise de renda individual em faixas de salários mínimos (0-2, 2-5, 5-10, 10+ MW)
- **Domiciliar**: Agregação de renda por domicílio e análise per capita
- **Percentuais precisos**: Cálculo exato da distribuição populacional por faixa de renda

### 🗺️ Análise Geográfica
- Renda mediana por estado (UF)
- Comparação capital vs interior
- Análise por regiões metropolitanas

### 👥 Análise Demográfica
- Distribuição por sexo, idade, raça
- Análise por nível educacional
- Correlações entre características demográficas e renda

### 🤖 Modelo Preditivo
- Random Forest e Gradient Boosting para estimativa de renda
- R² Score: ~0.40-0.45
- Identificação de principais determinantes de renda

### 📈 Visualizações Avançadas
- Histogramas de distribuição de renda (MW e valores NPV)
- Mapas coropléticos interativos do Brasil
- Pirâmides demográficas com sobreposição de renda
- Diagramas Sankey de fluxo entre faixas de renda
- Heatmaps de correlação

Nosso objetivo é criar um notebook python exploratório desses dados utilizando o melhor conjunto de ferramentas de análise de dados numéricas e gráficos possível para chegarmos a esse resultado de forma relevante e inteligente.

Na pasta temos os seguintes arquivos:
- INPUT_SNIPC_PNADC.sas.txt que é usado por sistemas SAS para analisar os dados
- INPUT_SNIPC.txt que é uma tabela explicativa dos meses e códigos relacionados
PNADC_012025.txt e PNADC_022025.txt que contém os microdados da pesquisa
Variáveis_PNADC_Trimestral.xls, contendo o dicionário de dados completo dos microdados, que incluem dados de múltiplos anos.

- Definicao_variaveis_derivadas.pdf, que documenta alguns detalhes sobre o parsing de microdados.

Vamos trabalhar com o que há de melhor em análise numérico/matemática estatística, pois nossa base é muito grande e acredito que vamos precisar do melhor dos dados.

Eu acredito que os dados PNADC_022025.txt contém os dados do outro arquivo 01, portanto não será necessário processar os dois arquivos, provavelmente.


## Metodologia: NPV (valores a preços de jul/2025) e salários mínimos

- Índice de preços: adotamos o IPCA mensal (IBGE) como deflator padrão para trazer rendas a preços de jul/2025.
- Data‑alvo: jul/2025. Fator de deflação para um mês `t` é `IPCA[jul/2025] / IPCA[t]`.
- Salário mínimo de referência: R$ 1.518 (informado). Após deflacionar, adicionamos colunas em “salários mínimos” dividindo a renda deflacionada por 1.518.
- Colunas‑alvo: rendimentos principais da PNADC em “qualquer trabalho”: `VD4019` (habitual) e `VD4020` (efetivo). No CSV rotulado, elas aparecem como, por exemplo, `VD4019__rendim_habitual_qq_trabalho`.
- Referência temporal no microdado trimestral: na ausência de coluna explícita de mês, usamos o último mês do trimestre (1→mar, 2→jun, 3→set, 4→dez).

Scripts adicionados:
- `scripts/npv_deflators.py emit-factors --ipca-csv data/ipca.csv --target 2025-07 --out data/deflators_2025-07.csv`
  - Lê um CSV de IPCA mensal (colunas `date,index` ou `year,month,index`) e emite fatores `date,factor_to_target`.
- `scripts/npv_deflators.py apply --in data/base_labeled.csv --out data/base_labeled_npv.csv --ipca-csv data/ipca.csv --target 2025-07 --min-wage 1518`
  - Aplica fatores às colunas de renda (autodetecta `VD4019*` e `VD4020*`, ou usar `--columns col1,col2`).
  - Acrescenta colunas `<col>_202507` (deflacionado) e `<col>_mw` (em salários mínimos).

Como obter o IPCA (índice mensal):
- Via BCB/SGS (usado aqui):
  - `python scripts/fetch_ipca.py --out data/ipca.csv`
  - OBS: a série pública da SGS expõe a variação mensal; o script compõe um índice (base arbitrária) por capitalização. Para deflatores, a base cancela no quociente.
- Via IBGE/SIDRA: também é possível usar a API do IBGE para IPCA (índice nacional mensal). Se preferir essa fonte, podemos parametrizar um fetcher específico.

Exemplo mínimo (com o IPCA de exemplo em `samples/ipca_sample.csv`):

```
python scripts/npv_deflators.py emit-factors --ipca-csv samples/ipca_sample.csv --target 2025-07 --out data/deflators_sample.csv
python scripts/npv_deflators.py apply --in data/base_labeled.csv --out data/base_labeled_npv.csv --ipca-csv samples/ipca_sample.csv --target 2025-07 --min-wage 1518
```

Observações importantes:
- O CSV de IPCA precisa conter todos os meses de interesse. Se um mês/ano de uma linha não existir na série, as colunas deflacionadas ficam em branco nessa linha.
- Se houver coluna explícita de mês (formato `YYYY-MM`), passe com `--date-col`. Caso contrário, o script deriva de `Ano`/`Trimestre`.

## Manutenção e atualização (para manter NPV up‑to‑date)

1) Atualize a série mensal do IPCA em `data/ipca.csv` (ou informe outro caminho no comando). Formatos aceitos:
   - `date,index` (date = `YYYY-MM`)
   - `year,month,index`
2) Ajuste a data‑alvo e salário mínimo conforme o contexto atual:
   - `--target 2025-07` e `--min-wage 1518` (atualize quando necessário)
3) Reexecute `emit-factors` e depois `apply` para regenerar os CSVs com colunas NPV e em salários mínimos.
4) Registre no `CHANGELOG.md` a atualização do deflator (faixa de meses e data‑alvo).

Sugestão de organização de dados:
- `data/ipca.csv`: série de IPCA mensal consolidada
- `data/deflators_YYYY-MM.csv`: fatores para a data‑alvo
- `data/*_npv.csv`: outputs deflacionados

## Pontos de fricção e o que validar

- Variáveis de renda: confirmar se a análise usará `VD4019` (habitual) e/ou `VD4020` (efetivo) e se serão somadas a outras fontes (transferências, etc.).
- Temporalidade da PNADC: usando trimestre→mês (mar/jun/set/dez) por padrão; caso exista coluna de referência mensal, preferir a coluna explícita.
- Deflator (IPCA vs. INPC): IPCA é padrão; se o público alvo for domicílios das faixas mais baixas, INPC pode ser avaliado. Documentar escolha.
- Pesos amostrais: para percentuais populacionais, aplicar pesos da PNADC nas agregações (não incluso nos scripts atuais; decidir e documentar fluxo de ponderação).
- Renda domiciliar vs. individual: alguns indicadores são por domicílio (soma de rendas, per capita). Decidir quais colunas deflacionar/agregar e em que nível.
- Salário mínimo de referência: manter parametrizado (`--min-wage`) e registrar mudanças históricas quando for necessário comparar períodos longos.
- Qualidade/ausência de dados: linhas sem mês mapeado no IPCA ficam em branco nas colunas ajustadas; monitorar cobertura.

### Checagem de qualidade: VD4020

- Hipótese de consistência: `VD4020` (rendimento efetivo em qualquer trabalho) deve ser ≥ `VD4017` (rendimento efetivo do trabalho principal) e, quando não há rendimentos secundários, `VD4020 ≈ VD4017`.
- Checagem 1 (geral):
  - `python scripts/validate_income.py vd4020-vs-principal --in data/base_labeled.csv --target "VD4020__rendim_efetivo_qq_trabalho" --principal "VD4017__rendim_efetivo_trab_princ" --secondary-money "V405912__valor_do_rend_efe_em_dinheiro" --tol 1.0`
  - Relata a taxa de `VD4020 ≥ VD4017` e, quando não há `V405912`, a taxa de igualdade (dentro da tolerância `--tol`).
- Checagem 2 (componentes): se quiser forçar que `VD4020 = soma(componentes)`, especifique as colunas componentes (ex.: monetário principal/segundário e produtos, conforme disponíveis no extrato):
  - `python scripts/validate_income.py vd4020-components --in data/base_labeled.csv --target "VD4020__rendim_efetivo_qq_trabalho" --components "V405112__valor_do_rend_efe_em_dinheiro,V405122__valor_do_rend_efe_em_produtos,V405912__valor_do_rend_efe_em_dinheiro" --tol 1.0`
  - Observação: dependendo do layout, o valor em produtos do trabalho secundário pode não estar numérico separado; ajuste a lista de componentes conforme a versão dos microdados.

## Testes

- `pytest -q` roda testes incluindo os novos de deflator/NPV (`tests/test_npv_deflators.py`).
- Amostra de IPCA em `samples/ipca_sample.csv` cobre o fluxo de fator e aplicação.
