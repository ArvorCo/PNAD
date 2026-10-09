<div align="center">

# Brasil CLI

**A research-grade CLI for Brazilian public microdata.**

[![PyPI version](https://img.shields.io/pypi/v/brasil-cli.svg?color=009c3b&label=pypi)](https://pypi.org/project/brasil-cli/)
[![PyPI downloads](https://img.shields.io/pypi/dm/brasil-cli.svg?color=ffdf00&label=downloads)](https://pypi.org/project/brasil-cli/)
[![CI](https://github.com/ArvorCo/PNAD/actions/workflows/ci.yml/badge.svg)](https://github.com/ArvorCo/PNAD/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-002776.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%E2%80%933.13-3776AB.svg)](pyproject.toml)
[![Data: IBGE PNADC](https://img.shields.io/badge/data-IBGE%20PNADC-009c3b.svg)](https://www.ibge.gov.br/estatisticas/sociais/trabalho/9171-pesquisa-nacional-por-amostra-de-domicilios-continua-mensal.html)

![Brasil — renda domiciliar por UF](docs/assets/hero.png)

### 📚 [**All reports →**](https://brasil.arvor.co) &nbsp; · &nbsp; 📊 [Interactive data essay](https://brasil.arvor.co/pnad.html) &nbsp; · &nbsp; 🇧🇷 [Artigo PT](https://brasil.arvor.co/artigo_pt.html) &nbsp; · &nbsp; 🇬🇧 [Article EN](https://brasil.arvor.co/artigo_en.html)

</div>

---

## Why this exists

Brazil takes excellent photographs of itself. The IBGE's PNADC — a continuous
household survey that reaches roughly a quarter-million Brazilians each year —
is as meticulous a census as any nation conducts. And yet, between the raw
fixed-width files the government publishes and anything a citizen, journalist,
or policy analyst could read with their own eyes, there is a vast field of
friction: SAS layouts, archaic encodings, inflation deflators, nominal
minimum-wage splines, replicate weights nobody teaches. In that friction, the
country hides from itself.

This repository is an attempt to close that gap. It compresses the painful
path from official microdata into a single, auditable command-line tool
(`brasil`) whose output — CSVs, SQLite tables, JSON payloads, a rich terminal
dashboard, and the [interactive data essay](docs/pnad.html) in this folder —
any Brazilian (or anyone interested in the country) can read, reproduce, and
challenge. Numbers are not neutral, but auditability is. If a claim about
Brazilian inequality cannot be traced back to a bootstrap weight, a deflator,
and a specific UF row in the PNADC, it does not belong in public debate.

> **Canonical executable:** `brasil` &nbsp;·&nbsp; **Compatibility alias:** `pnad`

---

## What the project covers

### Official data sources

- **PNADC trimestral** microdata
- **PNADC anual visita 5** microdata (work + benefits + pensions + capital decomposition)
- **Censo 2022** definitive sector mesh and aggregated income files
- **TSE eleitorado** open-data resources
- **BCB / IPCA** inflation series
- **BCB / minimum wage** nominal monthly series (BCB 1619)

### Core outputs

- extracted CSVs · labeled CSVs · IPCA-deflated CSVs
- SQLite databases
- terminal dashboards (pretty + JSON)
- interactive HTML essay (`docs/pnad.html`)

### Core interfaces

`brasil ibge-sync` · `brasil pipeline-run` · `brasil pipeline-run-anual` · `brasil query` · `brasil renda-por-faixa-sm` · `brasil dashboard`

---

## Highlights

- End-to-end pipeline from official raw files to analytic outputs.
- Both **trimestral labor-income** and **anual full household-income composition** views.
- Auto-refreshes **IPCA** and **minimum wage** references.
- Builds **SQLite** outputs for low-friction analytics and LLM-driven workflows.
- `brasil query` defaults to **read-only SQL**, safe for agentic use.
- `brasil dashboard` produces **weighted estimates**, **95% confidence intervals** (bootstrap over 200 IBGE replicate weights), and a **statistical audit seal** on every render.
- Annual dashboard includes explicit income lenses:
  - total household income
  - income excluding social benefits
  - income excluding public transfers
  - work-only income
- Visual layer (`docs/pnad.html`) renders the same data as 15 interactive Plotly charts with a PT/EN toggle, suitable for GitHub Pages.

---

## Install

The fastest way — install directly from PyPI:

```bash
pip install brasil-cli
```

You get both executables:

```bash
brasil --help
pnad --help        # legacy alias
```

### From source (for contributors)

```bash
git clone https://github.com/ArvorCo/PNAD
cd PNAD

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
pip install -e ".[dev]"
```

---

## 60-second quickstart

```bash
# 1) sync official docs + latest quarterly PNADC
brasil ibge-sync

# 2) build trimestral analytic outputs
brasil pipeline-run --raw latest

# 3) sync full scope (annual visita 5 + census + TSE)
brasil ibge-sync --full

# 4) build annual visita 5 outputs
brasil pipeline-run-anual --raw latest

# Optional: sync/build annual visita 1 (used for newer renda calibration)
brasil ibge-sync --with-anual --anual-visit 1 --anual-year 2025
brasil pipeline-run-anual --visit 1 --raw latest

# 5) inspect with the terminal dashboard
brasil dashboard

# 6) render the interactive HTML essay
python docs/build_index.py
open docs/pnad.html

# 7) query the SQLite database (read-only by default)
brasil query \
  --db data/outputs/brasil.sqlite \
  --sql "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
```

Main generated outputs:

- `data/outputs/base_labeled_npv.csv` — trimestral, labeled, IPCA-adjusted
- `data/outputs/base_anual_labeled_npv.csv` — annual visita 5, labeled, IPCA-adjusted
- `data/outputs/base_anual_visita1_labeled_npv.csv` — annual visita 1, labeled, IPCA-adjusted, when built
- `data/outputs/brasil.sqlite` — SQLite with `base_labeled_npv`, `base_anual_labeled_npv`, and optional `base_anual_visita1_labeled_npv` tables
- `docs/index.html` — library hub linking every published report (hand-written)
- `docs/pnad.html` — static interactive essay (bilingual)
- `data/outputs/ipca.csv` — IPCA series
- `data/outputs/tse_eleitorado_perfil.sqlite` — compact TSE electorate benchmarks
- `data/outputs/tse_eleitorado_perfil_benchmark.json` — exact gender and age totals for polling audits
- `data/originals/censo_2022_setores_censitarios/` — official sector-methodology
  document and compact, reproducible sector validations used in polling audits

### Census-sector audit for electoral polls

The territorial annex is not a vote table. The proper comparison key is the
IBGE 15-digit census-sector geocode; a neighborhood label can cover multiple
sectors. Rebuild the June–July 2026 Quaest comparison and refresh the selected
sector populations from the official Panorama service with:

```bash
python3 -m pip install -e '.[audit]'
python3 scripts/quaest-territory-audit.py --refresh-ibge
python3 scripts/quaest-july-audit.py
```

The pipeline writes auditable CSVs beside each source annex and publishes the
summary as `docs/assets/quaest_0726_territory.json`. It deliberately does not
impute voting behavior from Census demographics.

---

## Typical workflows

### 1. Sync official data

```bash
brasil ibge-sync                          # latest quarterly scope
brasil ibge-sync --year 2025 --quarter 3  # a specific quarter
brasil ibge-sync --year 2025 --all-in-year
brasil ibge-sync --full                   # trimestral + annual + census + TSE
brasil ibge-sync --with-anual --anual-visit 1 --anual-year 2025
```

### 2. Build trimestral PNADC outputs

```bash
brasil pipeline-run \
  --raw latest \
  --layout data/originals/input_PNADC_trimestral.sas \
  --sqlite data/outputs/brasil.sqlite
```

### 3. Build annual PNADC outputs

```bash
# Historical default: visita 5
brasil pipeline-run-anual \
  --raw data/raw/pnadc_anual_visita5/PNADC_2024_visita5.txt \
  --layout data/originals/pnadc_anual_visita5/input_PNADC_2024_visita5.txt \
  --sqlite data/outputs/brasil.sqlite

# Newer annual income calibration: visita 1
brasil pipeline-run-anual --visit 1 --raw latest
```

### 4. Compute income bands

```bash
# Brazil-level distribution (with bootstrap CI)
brasil renda-por-faixa-sm \
  --input data/outputs/base_labeled_npv.csv \
  --group-by pais \
  --format json

# UF ranking
brasil renda-por-faixa-sm \
  --input data/outputs/base_labeled_npv.csv \
  --group-by uf \
  --uf-order renda_desc
```

### 5. Run the dashboard

```bash
# auto-discover and combine quarterly + annual when both exist
brasil dashboard

# explicit annual view (the one that separates work from benefits)
brasil dashboard \
  --input data/outputs/base_anual_labeled_npv.csv \
  --mode anual \
  --composition-by-band \
  --dependency-ranking

# export structured JSON for downstream tools or LLMs
brasil dashboard --format json > data/outputs/dashboard.json
```

### 6. Query with SQLite

```bash
# list tables
brasil query \
  --db data/outputs/brasil.sqlite \
  --sql "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"

# top UFs by household income
brasil query \
  --db data/outputs/brasil.sqlite \
  --sql "SELECT UF_label AS uf, AVG(VD5001__rendim_domiciliar) AS renda FROM base_anual_labeled_npv GROUP BY 1 ORDER BY 2 DESC LIMIT 10"
```

### 7. Build the interactive HTML essay

```bash
python docs/build_index.py                  # rebuilds docs/pnad.html
python docs/build_hero.py                   # regenerates docs/assets/hero.png
python -m http.server 8000 -d docs          # preview locally
```

The generated `docs/pnad.html` is a self-contained bilingual essay (PT/EN
toggle) with 15 interactive Plotly charts reading the same PNADC data as the
terminal dashboard. It is suitable for GitHub Pages (`main:/docs`).

---

## Command map

| Command | What it does | Best for |
|---|---|---|
| `ibge-sync` | Sync official files and docs | keeping local raw data fresh |
| `pipeline-run` | Build trimestral outputs | labor-income workflows |
| `pipeline-run-anual` | Build annual visita N outputs (`--visit 1..5`) | full household-income composition |
| `query` | Run read-only SQL on SQLite | LLMs, analysts, automation |
| `renda-por-faixa-sm` | Compute income-band distributions with CI | reporting by Brazil / UF |
| `dashboard` | Rich terminal + JSON dashboard | exploratory analysis, briefing, storytelling |
| `sqlite-build` | Rebuild a table from CSV | custom pipelines and refreshes |
| `help-legacy` | Show legacy parser help | low-level extraction tools |

---

## LLM / agent-friendly by design

This project is intentionally useful as an LLM-side tool.

- `brasil query` and `brasil dashboard` default to **JSON** output.
- SQL is **read-only by default**; writes require an explicit `--allow-write`.
- Query payloads include **sampling metadata** (CI level, replicate-weight base, method).
- The CLI hides most fragile survey mechanics (fixed-width parsing, replicate
  weighting, IPCA deflation) from the model.

The repository ships a project-local LLM skill:

- [`skills/brasil-cli-analyst/SKILL.md`](skills/brasil-cli-analyst/SKILL.md)

That skill teaches an agent when to use each subcommand without falling into
the dumbest interface for the question.

---

## Methodology notes

### Income definitions

- **Quarterly PNADC** defaults to work income (`VD4020`, fallback `VD4019`).
- **Annual visita 5** uses household total income (`VD5001`) plus source
  decomposition (`V5001A2..V5008A2`), enabling the labor-vs-benefits split
  that the quarterly survey cannot support.
- Household income distributions are aggregated through `dom_id`.

### Inflation and minimum wage

- Income is deflated with **IPCA** to a target month.
- Minimum-wage references come from **BCB series 1619**.
- If `--target` is omitted, the latest month in the IPCA series is used.

### Weights and uncertainty

- Quarterly estimates prefer `V1028` (fallback `V1027`); annual prefer `V1032`
  (fallback `V1031`).
- 95% confidence intervals use bootstrap over 200 replicate weights
  (`V1028001..V1028200` quarterly; `V1032001..V1032200` annual).
- `brasil query` does **not** infer CI for arbitrary SQL. For
  uncertainty-aware outputs, prefer `renda-por-faixa-sm --format json` or
  `dashboard --format json`.

### Read-only safety

- `brasil query` allows `SELECT`, `WITH`, `PRAGMA`, and `EXPLAIN` by default.
- Mutating SQL requires explicit `--allow-write`.

### Statistical audit seal

Every `dashboard` render prints an **audit seal** — a compact checklist that
confirms which weight column was selected, how many replicate columns were
found, whether the bootstrap CI was effective, which IPCA target month was
used, and which minimum-wage reference was applied. The seal includes a short
hash of input + target + rows + households so two observers can verify they
are looking at the same estimate.

---

## Repository layout

```text
scripts/      main CLI and data-processing logic
tests/        pytest suite (50+ tests)
skills/       project-local skills for LLM agents
docs/         technical specs, bilingual essay, HTML builder
analysis/     exploratory analysis artifacts
notebooks/    research notebooks
samples/      tiny fixtures / examples
data/         local scaffold, outputs, raw files, docs
```

Main code modules:

- [scripts/pnad.py](scripts/pnad.py) — top-level CLI, dashboards, query, sync, pipelines
- [scripts/pnadc_cli.py](scripts/pnadc_cli.py) — lower-level extraction and legacy tooling
- [scripts/npv_deflators.py](scripts/npv_deflators.py) — IPCA / deflator logic
- [scripts/layout_sas.py](scripts/layout_sas.py) — SAS layout parsing
- [docs/build_index.py](docs/build_index.py) — HTML essay generator
- [docs/build_hero.py](docs/build_hero.py) — static hero PNG generator

---

## Development

```bash
python -m pytest -q                          # run the full suite
ruff check scripts/ docs/                    # lint
black --check scripts/ docs/                 # formatting
python scripts/pnad.py --help
python -m pytest -q tests/test_dashboard.py  # dashboard tests only
```

### Zero-lint policy

This project keeps `ruff check scripts/ docs/` and `black --check` green at
all times. Info-level warnings count. No suppressions. When adding code,
first ensure `ruff --fix` yields zero issues and `black` reformats nothing.

---

## Contributing

Good contributions include:

- new survey integrations (PNADS, Censo Demográfico microdata, POF)
- more robust statistical validation
- better annual-income decomposition workflows
- dashboard refinements and new visualizations in `docs/pnad.html`
- documentation and examples
- performance improvements for large raw files
- decomposition of the single-file CLI into cleaner modules

Before opening a change:

1. run the relevant pytest subset
2. keep outputs reproducible (`brasil pipeline-run --raw latest` should
   produce the same files on two machines given the same raw input)
3. avoid unsafe SQL defaults
4. preserve weighted and uncertainty-aware paths

---

## Presidential forecast, 4 October 2026

`docs/predicao_2026_1T_presidente.html` is a generated experimental forecast.
It consumes the PNAD aggregator and archived state polls, calibrates UF
preferences to a common national margin, and converts them to votes using the
final TSE electorate and historical attendance. Its browser simulator allows
changes in tactical voting by UF, attendance, invalid votes and undecided voters.
Probabilities are conditional on assumed errors, without full electoral calibration.

Rebuild from a fresh checkout (large source ZIPs stay in ignored `data/`):

```bash
pip install -e '.[forecast]'
python3 scripts/predicao-2026-fontes.py
python3 scripts/predicao-2026-tse.py
python3 scripts/predicao-2026-validar.py
python3 scripts/predicao-2026-build.py --hoje 2026-10-03
```

After integrating new poll transcriptions, update on election morning:

```bash
python3 scripts/predicao-2026-build.py --refresh-agregador --hoje 2026-10-04
```

The command refreshes the PNAD page, forecast JSON/CSV/HTML and social card,
and preserves an immutable snapshot in `analysis/predicao_2026/snapshots/`.
The forecast weights national polls with a 3-day half-life and state polls with
a 7-day half-life, measured from the midpoint of fieldwork. One latest field
per house is retained. Its inclusive central target uses PNAD sensitivity where
available and the published result otherwise (including Vox Brasil). The
descriptive aggregator retains equal house weights. Override forecast decay
with `--meia-vida-nacional` and `--meia-vida-estadual` (positive days).
New state transcriptions with source pages belong in
`analysis/predicao_2026/estaduais/`; newer fields replace the same house/UF.
The 03 October update adds 25 Quaest waves, three Real Time Big Data waves
and Paraná's Tocantins wave. `predicao-2026-estaduais.py` reproduces the Quaest
transcriptions from the archived primary PDFs, Portuguese Tesseract OCR and
declared visual checks. It checks rounded crossbreak compatibility, retains
missing-habit mass and exposes the residues. The likely-voter selection assumes
the intending-to-vote subset has the preference of its published habit group;
it can be disabled in the simulator. Unusable or unverified located sources are
listed in the public package, without transporting their numbers.
It does not discover or transcribe new polls. `--skip-card` permits generation
without Chrome. `predicao-2026-fontes.py --refresh` refreshes official source
packages; rerun both TSE preparation commands afterward. No 2026 vote-count
results enter the model, and post-election cutoffs are rejected.

The 2018-to-2022 retrospective validates attendance only: the UF baseline
performed better than the section baseline. Sections therefore support
diagnostics and scenarios. Never infer an absentee's candidate from their
section, or call a relative house difference an identified electoral bias.
Edit the template and `scripts/predicao_2026/`, then rebuild the generated page.
Validate with `pytest -q tests/test_predicao_2026.py` and the full suite.

The 3 October evening version adds an interactive state map
(`scripts/predicao_2026/mapa.py`, `docs/assets/predicao_2026_mapa.js`), a
simulator with one-click presets and shareable `#sim=` links
(`scripts/predicao_2026/simulador.py`), a dynamic linear model anchor with
house effects (`scripts/predicao_2026/dinamico.py`) and a rolling-origin
predictive validation of every national anchor (`scripts/predicao_2026/preditiva.py`,
output in `docs/assets/predicao_2026_validacao_preditiva.json`). The validation
scores how well each anchor predicts the next polls, never the ballot. The DLM
did not beat the recency-weighted mean and stays an alternative in the
simulator. Since the evening of 3 October the central is the recency mean
shifted by the shrunken 28-day poll trend projected to election day
(`central_inclinacao`), the only variant that passed the criterion declared
before the test (paired MAE not worse and smaller absolute bias at 1 to 3 days),
with undecided voters split by availability (1 minus stated rejection). It is a
shrunken extrapolation of a trend measured in polls, not a measurement of the
ballot. Consolidation scenarios start from the no-trend anchor (`inclusivo`) to
avoid counting the same migration twice, and the Monte Carlo recentres the
house bootstrap on the chosen anchor and adds the slope uncertainty in
quadrature to the common error. `analysis/predicao_2026/avaliacao_ml.md` explains
why supervised machine learning cannot be trained on this archive: there is
one reference election and no archived 2018 or 2022 polls.

## Income reweighting and runoff scenarios

The public report has three routes: `docs/reponderacao_pnad.html` for the runoff
simulator, `docs/reponderacao_pnad_1o_turno_2026.html` for the first-round archive
and comparison with the ballot, and `docs/reponderacao_pnad_log.html` for wave
incorporations and documentary revisions. Generate all three together:

```bash
python3 scripts/reponderacao-pnad.py calcular --hoje 2026-10-09
python3 scripts/reponderacao-build.py
python3 scripts/social-cards.py --only reponderacao_pnad reponderacao_pnad_1o_turno_2026 reponderacao_pnad_log
python3 scripts/sitemap-build.py
```

The runoff central uses only fields beginning after 4 October, within a
seven-day release window and with one eligible wave per house. It is a
conditional scenario: income reweighting, the historical Nexus propensity
template and an explicit +5% relative-presence assumption for Flávio, selected
after the first round. The simulator exposes attendance, invalid votes,
undecided allocation and a common-error sensitivity; it does not estimate
winning probabilities. Displayed differences use **Flávio minus Lula**;
legacy JSON/CSV `gap_*` fields retain their documented Lula-minus-Flávio sign.

Shared `#sim=` links retain parameters and the immutable data version.
`docs/assets/reponderacao_cenarios/` keeps both each dataset and its calculation
engine; retain published snapshots so old links remain reproducible. PNG cards
include the scenario assumptions. `analysis/reponderacao/log.json` preserves
historical incorporation dates; subsequent builds append new waves and record
source-hash changes without replacing those dates.

Vox Brasil, released on 9 October (`BR-09623/2026`), is recorded with its
published result. Its income target and questionnaire are insufficient to
identify the income concept, and the public report lacks vote-by-income cells.
The wave therefore receives no income adjustment. Evidence is archived in
`data/originals/vox_102026_09/` and the public registry transcription in
`docs/fontes/vox_09102026/`.

## Project status

Production-useful for:

- exploratory socioeconomic analysis
- journalism and data-essay workflows
- public-policy research
- state-by-state income comparisons
- LLM-assisted analysis of Brazilian official data

It is **not** an official IBGE or TSE tool. Users should still understand the
underlying survey design before publishing strong claims. Start with the
bundled [interactive essay](docs/pnad.html) and the
[full article (PT)](docs/artigo_pt.html) / [(EN)](docs/artigo_en.html) for a
guided, auditable reading of what the data says.

---

## Community health

- [License — MIT](LICENSE)
- [Contributing](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security Policy](SECURITY.md)

---

<div align="center">
<sub>Written, compiled, and maintained by <a href="https://github.com/leonardodias-arvor">Leonardo Dias</a> with support from <a href="https://github.com/ArvorCo">Arvor</a>.<br>
Data © IBGE / PNADC · Code © <a href="LICENSE">MIT</a> · Prose © <a href="https://creativecommons.org/licenses/by/4.0/">CC-BY-4.0</a></sub>
</div>
