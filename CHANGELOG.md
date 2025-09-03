# Changelog

All notable changes to this project are documented here.

## Unreleased
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

## 0.1.0 - 2025-09-02
- Initialize repository with PNADC scaffold and Git LFS tracking.
