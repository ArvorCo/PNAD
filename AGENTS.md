# Repository Guidelines

## Project Structure & Module Organization
- Root contains PNAD/PNADC data and documentation:
  - `PNADC_*.txt`: raw data extracts (e.g., `PNADC_012025.txt`).
  - `INPUT_SNIPC*.txt` and `INPUT_SNIPC_PNADC.sas.txt`: input layouts/mappings.
  - `Corresp_var_SNIPC_PNADC.doc`, `Definicao_variaveis_derivadas.pdf`, `Variaveis_PNADC_Trimestral.xls`: reference docs.
  - `README.md`: repository overview. Add any new notes here.
- If adding code, use:
  - `scripts/` for Python/R/CLI utilities.
  - `notebooks/` for exploratory analyses.
  - `tests/` for automated tests.

## Build, Test, and Development Commands
- Inspect files: `head -n 20 PNADC_012025.txt` — quick preview of raw data.
- Search fields: `rg "^" -n PNADC_012025.txt` — sample line numbers to gauge size.
- Validate row count: `wc -l PNADC_012025.txt` — basic completeness check.
- Run a script (example): `python scripts/parse_pnadc.py PNADC_012025.txt -o out/`.

## Coding Style & Naming Conventions
- Languages: prefer Python (PEP 8; 4‑space indent) or R (tidyverse style). Keep scripts self‑contained and documented.
- Filenames: use `kebab-case` for scripts (e.g., `scripts/build-dictionary.py`).
- Data files: follow `PNADC_MMYYYY.txt` pattern for monthly snapshots.
- Optional tools if adding Python code: format with `black`, lint with `ruff`.

## Testing Guidelines
- Place tests in `tests/` using `pytest` with names like `test_*.py`.
- Aim to cover parsing, type conversion, and schema validation.
- Run tests: `pytest -q`.

## Commit & Pull Request Guidelines
- Commits: imperative mood, concise scope, e.g., `add parser for PNADC_022025 layout`.
- PRs should include:
  - Purpose and summary of changes.
  - Sample commands/data used for validation.
  - Notes on data schema changes and backward compatibility.
  - Screenshots or snippets when relevant (e.g., sample rows).

## Security & Data Handling
- Do not commit sensitive or proprietary data beyond approved samples.
- Prefer lightweight samples in `samples/` for testing; avoid large uploads.
- Normalize line endings to LF; document encodings if not UTF‑8.
- If adding large binaries, consider Git LFS and update `README.md` accordingly.
