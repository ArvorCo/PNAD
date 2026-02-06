# Changelog

All notable changes to this project are documented here.

## [0.2.0] - 2025-09-07

### Added
- **Comprehensive Income Analysis Suite** (`notebooks/PNADC_exploration.ipynb`)
  - Individual income band analysis with two versions: (0-2, 2-5, 5+ MW) and (0-2, 2-5, 5-10, 10+ MW)
  - Household income aggregation using dom_id identifier
  - Per capita income calculations and distributions
  - Geographic analysis by Brazilian states, capital cities, and metropolitan regions
  - Demographic breakdowns by sex, age groups, race, and education levels
  
- **Advanced Statistical Analysis**
  - Gini coefficient calculation and Lorenz curve visualization
  - Statistical tests for income distribution comparisons (Kruskal-Wallis, Mann-Whitney U)
  - Income mobility analysis with transition matrices
  - Bootstrap confidence intervals for state-level income estimates
  - Multivariate regression analysis for income determinants
  - Principal Component Analysis (PCA) for dimensionality reduction
  - K-means clustering for income pattern identification

- **Machine Learning Models**
  - Random Forest Regressor for income prediction (R² ~0.40-0.45)
  - Gradient Boosting Regressor with feature importance analysis
  - Comprehensive model evaluation metrics (MAE, RMSE, R²)
  - Feature engineering from categorical variables

- **Professional Visualizations**
  - 6-panel dashboard with income distribution histograms
  - Interactive choropleth maps of Brazil (using plotly/folium)
  - Demographic pyramids with income overlays
  - Sankey diagrams for income flow analysis
  - Advanced correlation heatmaps
  - Time series visualizations of income trends
  - Publication-ready charts with Portuguese labels

- **NPV/IPCA Infrastructure**
  - `scripts/fetch_ipca.py` - Fetch inflation data from BCB API
  - `scripts/npv_deflators.py` - Apply IPCA deflators for NPV adjustment
  - `scripts/validate_income.py` - Income data validation utilities
  - Integration with BCB API for real-time IPCA data
  - Automatic NPV adjustment to July 2025 prices

- **Development Tools**
  - `scripts/find-duplicate-cells.py` - Detect duplicate code in notebooks
  - `scripts/patch_notebook_npv.py` - Fix notebook JSON issues
  - `CLAUDE.md` - Comprehensive AI assistant instructions and data dictionary
  - Updated `AGENTS.md` with income analysis methodology and best practices

- **Testing**
  - `tests/test_npv_deflators.py` - Unit tests for NPV calculations
  - `tests/test_validate_income.py` - Income validation tests

### Changed
- Reorganized notebook structure for logical execution flow (data → analysis → visualization)
- Enhanced requirements.txt with all necessary packages (plotly, altair, geopandas, scipy, statsmodels)
- Updated README.md with comprehensive analysis capabilities and results

### Fixed
- Notebook cell execution order (moved data loading before visualizations)
- JSON parsing errors in notebook cells
- AttributeError in model evaluation (fixed .round() on float objects)
- ValueError in Lorenz curve fill_between function
- KeyError for V2005 column name (corrected to V2005__condio_no_domiclio)
- Multivariate analysis encoding issues for categorical variables

### Technical Improvements
- Optimized memory usage with efficient pandas operations
- Added proper error handling for missing data
- Implemented non-parametric statistical tests for skewed distributions
- Added fallback options for geographic data fetching

## Unreleased
- Add installable `pnad` CLI entrypoint via `pyproject.toml`:
  - New `scripts/pnad.py` command with:
    - `pipeline-run` to orchestrate extract/label/NPV refresh and SQLite rebuild.
    - `download-pnadc` for raw file acquisition from explicit URLs.
    - `download-news` for RSS ingestion filtered by keyword.
    - `sqlite-build` for CSV -> SQLite table loading with type inference and optional indexes.
  - Legacy `pnadc_cli` subcommands remain available directly through `pnad` pass-through.
- Consolidate agent guidance into `AGENTS.md` and replace `CLAUDE.md`/`GEMINI.md` with symlinks.
- Rewrite `README.md` with operational quickstart focused on `pnad --help` and automation flows.
- Add streaming CLI `scripts/pnadc_cli.py` with subcommands:
  - `inspect`, `head`, `select`, `filter`, `sample`, `agg` for CSV-like PNADC files.
  - `layout`, `fwf-extract`, `fwf-schema` to parse SAS layouts and extract fixed-width fields.
  - `dict-extract`, `emit-codes`, `join-codes` for code-table management and labeling.
  - `household-agg` to aggregate persons to household level via `dom_id` and income sum.
- Add SAS INPUT layout parser `scripts/layout_sas.py` (supports labels, slugging, char/num and widths).
- Add tests covering delimiter sniffing and sampling, safe row expressions, and SAS layout parsing (`tests/`).
- Add `requirements.txt` and exploratory notebook `notebooks/PNADC_exploration.ipynb`.
- Add PNADC layout files (`input_PNADC_trimestral.*`) and dictionary Excel (`dicionario_PNADC_microdados_trimestral.xls`).
- Track new monthly extract `PNADC_022025.txt` (LFS-managed).
- Replace `Definicao_variaveis_derivadas.pdf` with `Definicao_variaveis.pdf`; remove temporary doc artifacts.
- Update `.gitignore` to reflect new tools and artifacts.

- Add IPCA/NPV workflow
  - New `scripts/npv_deflators.py` to emitir fatores de deflação (IPCA) para uma data-alvo e aplicar aos rendimentos (VD4019/VD4020), gerando colunas em BRL a preços de jul/2025 e em salários mínimos (parametrizável, padrão R$ 1.518).
  - Add `samples/ipca_sample.csv` e testes `tests/test_npv_deflators.py`.
  - README atualizado com metodologia, manutenção (como manter dados NPV atualizados) e pontos de fricção a validar.

## 0.1.0 - 2025-09-02
- Initialize repository with PNADC scaffold and Git LFS tracking.
