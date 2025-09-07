# CLAUDE.md - AI Assistant Instructions for PNAD Analysis

## Project Overview
This repository contains analysis tools and notebooks for the PNAD Contínua (PNADC) microdata from IBGE, focusing on Brazilian income distribution analysis. The primary goal is understanding income inequality patterns and creating predictive models for income estimation.

## Key Variables and Data Dictionary

### Income Variables (Primary Focus)
- `VD4020__rendim_efetivo_qq_trabalho`: Effective income from any work (nominal)
- `VD4020__rendim_efetivo_qq_trabalho_202507`: NPV-adjusted income (Jul/2025 prices)
- `VD4020__rendim_efetivo_qq_trabalho_mw`: Income in minimum wages (MW = R$ 1,518)
- `VD4019__rendim_habitual_qq_trabalho`: Usual income from any work

### Geographic Variables
- `UF__unidade_da_federao`: State code (with `UF_label` for names)
- `Capital__municpio_da_capital`: Capital city indicator
- `RM_RIDE__reg_metr_e_reg_adm_int_des`: Metropolitan region

### Demographic Variables
- `V2007__sexo`: Sex (1=Male, 2=Female)
- `V2009__idade_na_data_de_referncia`: Age at reference date
- `V2010__cor_ou_raa`: Race/color classification
- `V3001__sabe_ler_e_escrever`: Literacy indicator
- `V3009A__curso_mais_elevado_que_frequentou`: Highest education level

### Household Variables
- `VD2003__nmero_de_componentes_do_domic`: Number of household members
- `dom_id`: Household identifier (Ano_Trimestre_UPA_V1008)
- `V1008__nmero_de_seleo_do_domiclio`: Household selection number

## Common Analysis Patterns

### 1. Income Band Analysis
```python
# Standard income bands in minimum wages
def categorize_income(mw):
    if mw < 2: return '0-2 MW'
    elif mw < 5: return '2-5 MW'
    elif mw < 10: return '5-10 MW'
    else: return '10+ MW'
```

### 2. Household Aggregation
```python
# Create household ID
df['dom_id'] = (df['Ano__ano_de_referncia'].astype(str) + '_' +
                df['Trimestre__trimestre_de_referncia'].astype(str) + '_' +
                df['UPA__unidade_primria_de_amostragem'].astype(str) + '_' +
                df['V1008__nmero_de_seleo_do_domiclio'].astype(str))

# Aggregate by household
household_income = df.groupby('dom_id').agg({
    'VD4020__rendim_efetivo_qq_trabalho_mw': 'sum',
    'VD2003__nmero_de_componentes_do_domic': 'first'
})
```

### 3. NPV Adjustment Workflow
1. Fetch IPCA from BCB API (series 433)
2. Calculate cumulative index and factors
3. Apply factor based on year-month (derived from Ano/Trimestre)
4. Create NPV-adjusted columns with suffix `_202507`

## Important Considerations

### Data Quality
- **Missing Income**: Many individuals have null income (non-workers, children)
- **Outliers**: Cap visualizations at reasonable limits (e.g., 20 MW for individual income)
- **Weights**: Consider using sample weights for population-level statistics

### Performance Tips
- Use `pd.read_parquet()` for faster loading than CSV
- Filter data early: `df[df['income_col'].notna() & (df['income_col'] > 0)]`
- Use DuckDB for large aggregations: `con.sql("SELECT ... FROM base")`
- Chunk processing for memory-intensive operations

### Visualization Guidelines
- **Colors**: Use RdYlGn for income (red=low, green=high)
- **Bins**: Standard bins at 2, 5, 10 MW boundaries
- **Labels**: Use Portuguese labels for publication
- **Interactive**: Prefer plotly for interactive charts

## Testing and Validation

### Key Metrics to Validate
1. **Total observations**: ~475,000 individuals per quarter
2. **Households**: ~150,000 unique households
3. **Income distribution**: Median ~1.2 MW, Mean ~2.0 MW
4. **Missing income**: ~50% (includes non-workers)

### Common Pitfalls to Avoid
- Don't assume all individuals have income
- Remember to filter outliers for visualizations
- Use appropriate statistical tests (often non-parametric due to skewed distributions)
- Check for temporal consistency when comparing quarters

## Workflow for New Analysis

1. **Load Data**: Start with `base_labeled_npv.parquet` for NPV-adjusted data
2. **Filter**: Remove nulls and zeros for income analysis
3. **Aggregate**: Use `dom_id` for household-level analysis
4. **Visualize**: Start with distributions, then geographic/demographic breakdowns
5. **Model**: Use Random Forest or Gradient Boosting for income prediction
6. **Document**: Update CHANGELOG.md with new findings

## Key Functions and Scripts

### CLI Tools
- `scripts/pnadc_cli.py`: Main CLI for data processing
- `scripts/npv_deflators.py`: NPV adjustment utilities
- `scripts/fetch_ipca.py`: Fetch inflation data from BCB

### Notebooks
- `notebooks/PNADC_exploration.ipynb`: Main analysis notebook with:
  - Income band analysis (individual and household)
  - Geographic and demographic breakdowns
  - Predictive models
  - Advanced visualizations

## Model Performance Benchmarks
- **Random Forest R²**: ~0.40-0.45
- **Key predictors**: Education, Age, State, Urban/Rural
- **MAE**: ~1.5 MW typical error

## Contact and Resources
- IBGE PNADC: https://www.ibge.gov.br/estatisticas/sociais/trabalho/pnad-continua
- BCB API: https://dadosabertos.bcb.gov.br/
- Project repository: [Current repository]