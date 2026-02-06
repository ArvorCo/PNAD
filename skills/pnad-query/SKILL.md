# pnad-query Skill

## Purpose
Use `pnad query` to run SQL analytics on PNAD SQLite outputs in a way that is robust for LLM workflows.

## When To Use
- You need aggregations or filters that are easier in SQL than in Python scripting.
- You need structured JSON output to feed another model/tool.
- You need quick schema discovery from `pnad.sqlite`.

## Prerequisites
- SQLite built locally, usually at `data/outputs/pnad.sqlite`.
- Main table available (default pipeline output): `base_labeled_npv`.

## Core Workflow
1. Discover tables.
2. Inspect table schema.
3. Run constrained aggregate query with explicit aliases.
4. Return JSON by default (or table mode for terminal inspection).

## Commands
```bash
# 1) list tables
pnad query --db data/outputs/pnad.sqlite \
  --sql "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"

# 2) inspect schema
pnad query --db data/outputs/pnad.sqlite \
  --sql "PRAGMA table_info(base_labeled_npv)"

# 3) aggregate example
pnad query --db data/outputs/pnad.sqlite \
  --sql "SELECT UF__unidade_da_federao AS uf, AVG(VD4020__rendim_efetivo_qq_trabalho) AS renda_media FROM base_labeled_npv GROUP BY 1 ORDER BY 2 DESC LIMIT 10"

# 4) human-readable table output
pnad query --db data/outputs/pnad.sqlite \
  --sql "SELECT UF__unidade_da_federao, COUNT(*) AS n FROM base_labeled_npv GROUP BY 1 ORDER BY 2 DESC LIMIT 10" \
  --format table
```

## Safety Defaults
- Read-only SQL is enforced by default.
- Allowed by default: `SELECT`, `WITH`, `PRAGMA`, `EXPLAIN`.
- Write statements require explicit `--allow-write`.

## Output Contract (JSON default)
- `columns`: ordered list of column names.
- `rows`: list of row objects.
- `row_count`: returned row count.
- `truncated`: if `--max-rows` cut the result.
- `elapsed_ms`: query latency.
- `read_only`: whether command ran in read-only mode.

## Prompting Tips For LLMs
- Always include explicit `LIMIT` (even with `--max-rows`).
- Always alias derived metrics (`AS renda_media`, `AS pct`).
- Prefer explicit grouping columns over `SELECT *`.
- Use schema discovery first if uncertain about column names.
