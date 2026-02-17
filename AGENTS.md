# Repository Guidelines

## Single Source of Truth
- Agent instructions live in `AGENTS.md`.
- `CLAUDE.md` and `GEMINI.md` should be symlinks to this file.

## Project Structure & Module Organization
- Runtime data layout (local, heavy files ignored):
  - `data/raw/`: PNADC trimestral `.zip` / `.txt`.
  - `data/raw/pnadc_anual_visita5/`: PNADC anual visita 5.
  - `data/raw/tse_eleitorado/`: pacotes de perfil do eleitorado (TSE).
  - `data/originals/`: IBGE docs/layouts + `salario_minimo.csv`.
  - `data/originals/pnadc_anual_visita5/`: documentacao anual visita 5.
  - `data/originals/censo_2022_renda_responsavel/`: agregados do Censo 2022 (renda do responsavel).
  - `data/outputs/`: `base*.csv`, `ipca.csv`, `brasil.sqlite`.
- Root docs/metadata:
  - `README.md`: usage and operational docs.
  - `AGENTS.md`: repository guidance.
- Code and analysis:
  - `scripts/` for Python CLI/utilities.
  - `notebooks/` for exploratory analyses.
  - `tests/` for `pytest` automated tests.
  - `skills/` for project-local agent skills (e.g., `skills/pnad-query/SKILL.md`).
  - `data/` scaffold only (`.gitkeep`).

## Core Commands
- Inspect raw file: `head -n 20 data/raw/PNADC_032025.txt`
- Validate size: `wc -l data/raw/PNADC_032025.txt`
- Run tests: `pytest -q`
- Main CLI help: `python scripts/pnad.py --help`
- Legacy command help: `python scripts/pnad.py help-legacy`

## Installable CLI (`brasil`)
- Install locally: `pip install -e .`
- Compatibility alias: `pnad` remains available for legacy scripts.
- Then use directly:
  - `brasil --help`
  - `brasil ibge-sync`
  - `brasil ibge-sync --full`
  - `brasil pipeline-run --raw latest`
  - `brasil query --db data/outputs/brasil.sqlite --sql "SELECT name FROM sqlite_master WHERE type='table'"`
  - `brasil renda-por-faixa-sm --input data/outputs/base_labeled.csv --group-by pais`
  - `brasil dashboard --input data/outputs/base_labeled.csv --interactive`

## Pipeline Defaults
- Pipeline command: `brasil pipeline-run`
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
  - `brasil.sqlite` (table `base_labeled_npv`)
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
  - Replicate weights for sampling uncertainty: `V1028001..V1028200`
- Geography:
  - `UF__unidade_da_federacao`, `Capital__municipio_da_capital`, `RM_RIDE__reg_metr_e_reg_adm_int_des`
- Household:
  - `dom_id` composed from `Ano`, `Trimestre`, `UPA`, `V1008`

## Income Methodology
- Bands: `0-2`, `2-5`, `5-10`, `10+` minimum wages.
- Minimum wage source: `data/originals/salario_minimo.csv` (updated by `brasil ibge-sync`).
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
- Commit style: imperative + scoped (example: `add brasil pipeline-run sqlite refresh`).
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
- Official IBGE layout files (`data/originals/input_PNADC_trimestral.sas` and `.txt`) are `ISO-8859-1` (`latin-1`), not UTF-8.
- Reading layout in wrong encoding introduces mojibake in labels/slugs (example: `federacao`/`primria` artifacts); keep layout parsing encoding-aware and keep generated CSV/JSON output in UTF-8.
- If mojibake appears in derived headers/labels, rerun extraction pipeline after fixing layout encoding handling.
- `fwf-extract` can derive `data_nascimento` and `dom_id`.
- `household-agg` streams rows and aggregates by `dom_id`.
- `npv_deflators.py` applies deflators and minimum-wage conversion in streaming mode.
- `brasil ibge-sync` refreshes monthly minimum wage from BCB SGS series `1619`.
- `brasil pipeline-run --raw latest` auto-resolves `target` (latest IPCA month) and `min_wage` from `salario_minimo.csv`.
- `brasil renda-por-faixa-sm` and `brasil dashboard` default to weighted population estimates (`V1028`, fallback `V1027`).
- `brasil renda-por-faixa-sm` and `brasil dashboard` now compute sampling margin of error/CI by default (bootstrap replicate weights, `V1028001..V1028200`) when replicate columns are present.
- CI controls: `--no-ci` to disable, `--ci-level` to change confidence level.
- If legacy CSVs were generated before replicate columns were included, CI falls back to disabled until pipeline is rerun.
- `brasil dashboard` default `--sm-mode` is `alvo`; use `--sm-mode both` for period-vs-target comparison.
- `DEFAULT_KEEP` in `fwf-extract` now includes additional high-value modeling fields (sampling, schooling, labor-force and job-formality variables) with good observed coverage in PNADC 2025Q3 profiling.
- `DEFAULT_KEEP` also includes all 200 replicate weights to support uncertainty estimation end-to-end in open workflows.
- Terminal output now has high-contrast Brazilian palette by faixa:
  - green (mais pobre), yellow (media baixa), blue (media alta), white (mais rica).
- `--group-by uf` default ordering is `renda_desc` (richer to poorer by average household SM).
- Dashboard sections now include:
  - top 10 UFs by income and by population,
  - macro-region panel,
  - socioeconomic "thermometer" insights (richest/poorest UF and concentration in lowest/highest faixa).
- Pretty outputs now map faixa de SM to BRL ranges (`R$`) for direct interpretation.
- Dashboard now includes an age pyramid (sexo x idade) and age recuts ordered by age buckets.
- For restricted-universe variables, dashboard labels non-response explicitly:
  - `Nao se aplica (fora da ocupacao)` for occupation-only variables,
  - `Fora de RM/RIDE` for metro-region variable,
  avoiding false inflation of `Sem informacao`.
- `brasil query` is optimized for LLM workflows:
  - default output is JSON,
  - read-only SQL is enforced by default,
  - supports SQL via `--sql`, `--sql-file`, or stdin pipe,
  - table rendering is available via `--format table`,
  - JSON includes `sampling` metadata; CI is not auto-derived for arbitrary SQL.
- In PNADC layout, `var. auxil.` means `variavel auxiliar` (roteamento do questionario), not necessarily `auxilio social`.
- For labor income decomposition, keep `V4033/V4034*` (trabalho principal) together with `V405*` (trabalho secundario/outros); omitting `V403*` undercounts detailed components.

- `brasil ibge-sync --full` sincroniza escopos eleitorais completos: PNADC trimestral + PNADC anual visita 5 + Censo 2022 (renda do responsavel) + TSE (perfil do eleitorado).
