# Contributing

Thanks for contributing.

## What Is Most Useful

High-value contributions include:

- bug fixes in parsing, weighting, and dashboard logic
- improvements to annual income composition workflows
- better tests for methodological edge cases
- performance improvements for large fixed-width files
- documentation that improves reproducibility
- decomposition of oversized modules into smaller maintainable pieces

## Ground Rules

- keep outputs reproducible
- prefer explicit methodology over hidden magic
- do not weaken read-only defaults in LLM-facing paths
- do not silently change statistical meaning
- do not commit private data or secrets

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## Before Opening A PR

Run the relevant tests:

```bash
python -m pytest -q
```

Useful narrower runs:

```bash
python -m pytest -q tests/test_query.py
python -m pytest -q tests/test_dashboard.py tests/test_dashboard_anual.py
python -m pytest -q tests/test_ibge_sync.py
```

## Pull Request Expectations

A good PR should include:

- what changed
- why it changed
- how it was validated
- whether methodology or output contracts changed

If you change:

- SQL output shape
- dashboard JSON contracts
- weighting logic
- annual/trimestral income interpretation

call that out explicitly.

## Design Notes

The main technical debt is the size of `scripts/pnad.py`.

If you refactor, prefer:

- smaller modules
- stable CLI contracts
- tests added before behavioral changes

## Data Hygiene

- treat `data/` as local execution state unless the file is intentionally small and committed
- prefer tiny fixtures in `samples/` or synthetic rows in tests
- never commit credentials or proprietary data
