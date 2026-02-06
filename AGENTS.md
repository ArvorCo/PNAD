# Repository Guidelines

## Single Source of Truth
- Agent instructions live in `AGENTS.md`.
- `CLAUDE.md` and `GEMINI.md` should be symlinks to this file.

## Project Structure & Module Organization
- Runtime data layout (local, heavy files ignored):
  - `data/raw/`: PNADC `.zip` / `.txt`.
  - `data/originals/`: IBGE docs/layouts + `salario_minimo.csv`.
  - `data/outputs/`: `base*.csv`, `ipca.csv`, `pnad.sqlite`.
- Root docs/metadata:
  - `README.md`: usage and operational docs.
  - `AGENTS.md`: repository guidance.
- Code and analysis:
  - `scripts/` for Python CLI/utilities.
  - `notebooks/` for exploratory analyses.
  - `tests/` for `pytest` automated tests.
  - `data/` scaffold only (`.gitkeep`).

## Core Commands
- Inspect raw file: `head -n 20 data/raw/PNADC_032025.txt`
- Validate size: `wc -l data/raw/PNADC_032025.txt`
- Run tests: `pytest -q`
- Main CLI help: `python scripts/pnad.py --help`
- Legacy command help: `python scripts/pnad.py help-legacy`

## Installable CLI (`pnad`)
- Install locally: `pip install -e .`
- Then use directly:
  - `pnad --help`
  - `pnad ibge-sync`
  - `pnad pipeline-run --raw latest`
  - `pnad renda-por-faixa-sm --input data/outputs/base_labeled.csv --group-by pais`
  - `pnad dashboard --input data/outputs/base_labeled.csv --interactive`

## Pipeline Defaults
- Pipeline command: `pnad pipeline-run`
- Steps executed:
  - emit code tables (`emit-codes`)
  - fixed-width extraction (`fwf-extract`)
  - code label join (`join-codes`)
  - IPCA refresh (`fetch_ipca.py`)
  - NPV adjustment (`npv_deflators.py apply`)
  - SQLite build (optional, on by default in pipeline)
- Outputs in `data/outputs/`:
  - `base.csv`, `base_labeled.csv`, `base_labeled_npv.csv`
  - `ipca.csv`
  - `pnad.sqlite` (table `base_labeled_npv`)
- Automatic defaults in `pipeline-run`:
  - If `--target` is omitted, use latest month from `--ipca-csv`.
  - If `--min-wage` is omitted, resolve from `--salario-minimo-csv` at or before target.
  - Manifest includes `target`, `min_wage`, `min_wage_source_month`.

## Key Data Variables
- Income:
  - `VD4019__rendim_habitual_qq_trabalho`
  - `VD4020__rendim_efetivo_qq_trabalho`
  - NPV-adjusted suffix: `_<YYYYMM>`
  - Minimum-wage suffix: `_mw`
- Geography:
  - `UF__unidade_da_federao`, `Capital__municpio_da_capital`, `RM_RIDE__reg_metr_e_reg_adm_int_des`
- Household:
  - `dom_id` composed from `Ano`, `Trimestre`, `UPA`, `V1008`

## Income Methodology
- Bands: `0-2`, `2-5`, `5-10`, `10+` minimum wages.
- Minimum wage source: `data/originals/salario_minimo.csv` (updated by `pnad ibge-sync`).
- Deflator: IPCA monthly index to target month (default = latest month in series).
- Per-capita income: household total divided by `VD2003__nmero_de_componentes_do_domic`.
- Weighted estimation default:
  - Use `V1028` (fallback `V1027`) for population distribution.
  - `--unweighted` is diagnostic only (not official estimate).

## Coding Style & Naming
- Prefer Python (PEP 8, 4 spaces).
- Script naming: `kebab-case` (new files), keep existing names for compatibility.
- Keep scripts stream-first for large data; avoid loading full files in memory when not needed.

## Testing Guidelines
- Tests in `tests/`, names `test_*.py`.
- Cover parsing, type conversion, schema checks, and CLI behavior.
- Run `pytest -q` before merging.

## Commit & PR Guidelines
- Commit style: imperative + scoped (example: `add pnad pipeline-run sqlite refresh`).
- PR should include:
  - purpose and change summary
  - commands used for validation
  - backward-compat notes (schema/column changes)

## Security & Data Handling
- Avoid committing sensitive or proprietary data.
- Prefer lightweight samples in `samples/` for tests.
- Normalize line endings to LF.
- Use Git LFS for large binaries when needed.

## Lessons Learned
- Safe filtering uses restricted AST compilation (`pnadc_cli.RowExpr`).
- Delimiter/header detection uses `parse_pnadc.sniff_delimiter` with fallbacks.
- SAS layout parser (`layout_sas.parse_layout`) supports labels/slugs and stable ordering.
- `fwf-extract` can derive `data_nascimento` and `dom_id`.
- `household-agg` streams rows and aggregates by `dom_id`.
- `npv_deflators.py` applies deflators and minimum-wage conversion in streaming mode.
- `pnad ibge-sync` refreshes monthly minimum wage from BCB SGS series `1619`.
- `pnad pipeline-run --raw latest` auto-resolves `target` (latest IPCA month) and `min_wage` from `salario_minimo.csv`.
- `pnad renda-por-faixa-sm` and `pnad dashboard` default to weighted population estimates (`V1028`, fallback `V1027`).
- `pnad dashboard` default `--sm-mode` is `alvo`; use `--sm-mode both` for period-vs-target comparison.
- Terminal output now has high-contrast Brazilian palette by faixa:
  - green (mais pobre), yellow (media baixa), blue (media alta), white (mais rica).
- `--group-by uf` default ordering is `renda_desc` (richer to poorer by average household SM).
- Dashboard sections now include:
  - top 10 UFs by income and by population,
  - macro-region panel,
  - socioeconomic "thermometer" insights (richest/poorest UF and concentration in lowest/highest faixa).
- Pretty outputs now map faixa de SM to BRL ranges (`R$`) for direct interpretation.
- Dashboard now includes an age pyramid (sexo x idade) and age recuts ordered by age buckets.
