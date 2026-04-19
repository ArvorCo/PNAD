# CLI Cookbook

Use these patterns when operating the repo as a local Brazil-data tool.

## 1. Discover What Exists

```bash
brasil query --db data/outputs/brasil.sqlite \
  --sql "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
```

## 2. Inspect Table Schema

```bash
brasil query --db data/outputs/brasil.sqlite \
  --sql "PRAGMA table_info(base_labeled_npv)"

brasil query --db data/outputs/brasil.sqlite \
  --sql "PRAGMA table_info(base_anual_labeled_npv)"
```

## 3. Quarterly Income by UF

```bash
brasil query --db data/outputs/brasil.sqlite \
  --sql "SELECT UF__unidade_da_federacao AS uf, AVG(VD4020__rendim_efetivo_qq_trabalho) AS renda_media FROM base_labeled_npv GROUP BY 1 ORDER BY 2 DESC LIMIT 27"
```

## 4. Annual Household Income by UF

```bash
brasil query --db data/outputs/brasil.sqlite \
  --sql "SELECT UF__unidade_da_federacao AS uf, AVG(VD5001__rend_efetivo_domiciliar) AS renda_media_domiciliar FROM base_anual_labeled_npv GROUP BY 1 ORDER BY 2 DESC LIMIT 27"
```

## 5. Salary-Band Distribution

```bash
brasil renda-por-faixa-sm \
  --input data/outputs/base_labeled.csv \
  --group-by pais \
  --format json
```

Use this when the user asks:

- how much of Brazil is below 2 minimum wages
- which states concentrate more low-income households
- what share of people are in each income band

## 6. Broad Brazil Snapshot

```bash
brasil dashboard --format json
```

Good first step for:

- country briefings
- state comparisons
- quarterly vs annual context
- annual composition by source

## 7. Explicit Annual Composition

```bash
brasil dashboard \
  --input data/outputs/base_anual_labeled.csv \
  --mode anual \
  --format json
```

Read these JSON keys first:

- `income_composition_national`
- `income_sources_detail`
- `income_lenses_national`
- `uf_dependency_ranking`
- `composition_by_band`

## 8. Refresh Data Only If Needed

```bash
brasil ibge-sync
brasil pipeline-run --raw latest

brasil ibge-sync --full
brasil pipeline-run-anual --raw data/raw/pnadc_anual_visita5/PNADC_2024_visita5.txt
```

Avoid this path unless outputs are missing or clearly stale.

## 9. Prompting Tips For LLMs

- Ask one analytic question at a time.
- Discover schema before writing custom SQL.
- Use `dashboard` for broad context, `query` for exact cuts.
- Treat annual and quarterly outputs as different analytical products.
- Do not overclaim official precision when you only ran arbitrary SQL without CI.
