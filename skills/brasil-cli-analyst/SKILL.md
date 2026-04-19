---
name: brasil-cli-analyst
description: Use this skill whenever the task needs to answer a question about Brazil with local official microdata — PNADC trimestral, PNADC anual visita 5, Censo 2022, TSE eleitorado, IPCA, or salário mínimo — using the `brasil` / `pnad` CLI. Trigger for any state-level income analysis, household income-band distribution, annual income-source composition (labor vs benefits vs pensions vs capital), dashboard snapshot, SQLite query, or when a journalist / analyst / LLM agent needs a read-mostly, statistically auditable answer grounded in the repo's local outputs instead of writing ad-hoc pandas code.
---

# brasil-cli-analyst

Use the local `brasil` CLI (alias `pnad`) as the primary interface to Brazilian
official microdata in this repository. It produces labeled CSVs, SQLite tables,
a rich terminal dashboard, and machine-readable JSON payloads with bootstrap
confidence intervals on every estimate.

---

## when to trigger this skill

- The user asks about Brazilian **income, poverty, inequality, demographics,
  regional comparison, benefits, pensions, informal work, or PNADC
  microdata**.
- The user wants a **state-by-state (UF)** or **macro-region** breakdown.
- The user wants a **faixa de salário mínimo** cut (0-2, 2-5, 5-10, 10+ SM).
- The user wants an **annual decomposition** of income into work / benefits
  / previdência / capital.
- The user needs **95% confidence intervals** (bootstrap over IBGE replicate
  weights).
- The user wants a **local, reproducible** answer — no network calls required
  once data is synced.
- The answer will feed a **narrative, briefing, dashboard, or report**.

## when NOT to trigger this skill

- The user wants to analyze a dataset not in this repo (POF, Censo Demográfico
  microdata, RAIS, CAGED).
- The user wants real-time market data, news, or web research — use a
  WebSearch or a dedicated finance tool.
- The user just wants to *read* the existing `docs/artigo_pt.md` or
  `docs/index.html` — no CLI call needed.

---

## decision tree — pick the right subcommand

```
                         ┌─────────────────────────────────────┐
                         │  user question about Brazilian data │
                         └──────────────┬──────────────────────┘
                                        │
                      ┌─────────────────┴──────────────────┐
                      │                                    │
           broad / interpretive?                  precise / custom cut?
           ("paint me a picture")                 ("exact number for X")
                      │                                    │
                      ▼                                    ▼
       ┌─────────────────────────┐             ┌──────────────────────────┐
       │  brasil dashboard       │             │   is it a faixa de SM    │
       │  --format json          │             │      distribution?       │
       └─────────┬───────────────┘             └──────────┬───────────────┘
                 │                                        │
                 ▼                                        ▼
    need benefits/pensions split?                  YES           NO
           │                                         │            │
         YES     NO                                  ▼            ▼
           │     │                  ┌────────────────────┐  ┌────────────────┐
           ▼     ▼                  │ brasil             │  │ brasil query   │
    --mode anual \            dashboard default         │ renda-por-faixa-sm │  │ --sql "..."    │
    --composition-by-band \   (tri + anual)              │ --format json      │  │ --db ...sqlite │
    --dependency-ranking                                 │ --group-by uf|pais │  └────────────────┘
                                                        └────────────────────┘
```

**One-line rule of thumb:**

| If the question is about… | Use |
|---|---|
| a picture of the whole country | `brasil dashboard --format json` |
| faixas 0-2/2-5/5-10/10+ SM | `brasil renda-por-faixa-sm --format json` |
| an exact custom aggregate (avg, median, count) | `brasil query --sql "..."` |
| labor vs benefits vs pensions composition | `brasil dashboard --mode anual --composition-by-band --dependency-ranking --format json` |
| "with vs without benefits" sensitivity | `brasil dashboard --mode anual` (see *annual income lenses* below) |
| refreshing data | `brasil ibge-sync` then `brasil pipeline-run` / `brasil pipeline-run-anual` |

---

## canonical workflow

1. **Check artifacts first.** Before running anything heavy, verify that
   `data/outputs/brasil.sqlite` and `data/outputs/base_*_labeled_npv.csv`
   already exist. Do NOT re-run pipelines unless artifacts are missing or
   obviously stale.

2. **Inspect schema** with `PRAGMA table_info(...)` before writing SQL.
   Column names are verbose (`VD5001__rendim_domiciliar`), and casual
   guessing causes silent mismatches.

3. **Prefer JSON output** for anything that will be consumed by another
   agent or a dashboard. Human-formatted tables are harder to parse.

4. **Pass through CI fields** (`*_moe`, `*_ci_low`, `*_ci_high`) whenever you
   report a number — never strip them. Auditability is the point.

5. **Cite the weight column and vintage.** Every claim should be traceable
   to a specific weight (`V1028` / `V1032`), a specific target month (IPCA
   deflator), and a specific SM reference.

---

## the three primary subcommands in detail

### `brasil dashboard`

A rich nation + UF + macro-region summary with CI, Lorenz, bands, cross-tabs,
age pyramid, and (in annual mode) income-source composition. Best first
command when you don't yet know what you're looking for.

```bash
# auto-discover and combine trimestral + anual when both are built
brasil dashboard

# annual, with the premium breakdowns
brasil dashboard \
  --mode anual \
  --composition-by-band \
  --dependency-ranking \
  --format json
```

Annual-mode payload includes:

- `income_composition_national` — national breakdown by source
- `composition_by_band` — per-faixa breakdown by source
- `uf_dependency_ranking` — state ranking by (benefits + previdência) share
- `income_lenses_national` — total income / excluding benefits / excluding
  transfers / labor-only

### `brasil renda-por-faixa-sm`

Explicit band distribution with per-group CI. Use when the user wants the
exact shape of the distribution.

```bash
brasil renda-por-faixa-sm \
  --input data/outputs/base_labeled_npv.csv \
  --group-by uf \
  --uf-order renda_desc \
  --format json
```

### `brasil query`

Arbitrary read-only SQL. Use when the other two can't express the cut.

```bash
brasil query \
  --db data/outputs/brasil.sqlite \
  --sql "SELECT UF_label AS uf, \
                AVG(VD5001__rendim_domiciliar) AS avg_brl, \
                COUNT(DISTINCT dom_id) AS households \
         FROM base_anual_labeled_npv \
         GROUP BY 1 ORDER BY 2 DESC LIMIT 5"
```

**Do NOT** claim CI from arbitrary SQL — `query` does not compute bootstrap
variance.

---

## eight example questions → exact CLI

| # | Question | Command |
|---|---|---|
| 1 | "What's the average household income in the Federal District vs Maranhão?" | `brasil dashboard --mode anual --format json \| jq '.modes.alvo.top10_uf_income[0], .modes.alvo.bottom10_uf_income[-1]'` |
| 2 | "What percentage of Brazilians live on up to 2 minimum wages?" | `brasil renda-por-faixa-sm --group-by pais --format json \| jq '.groups[0].bands[] \| select(.range=="0-2")'` |
| 3 | "How concentrated is income in São Paulo?" | `brasil query --sql "SELECT 100.0*SUM(CASE WHEN VD5001__rendim_domiciliar>16210 THEN VD5001__rendim_domiciliar ELSE 0 END)/SUM(VD5001__rendim_domiciliar) AS share_top_band FROM base_anual_labeled_npv WHERE UF_label='São Paulo'"` |
| 4 | "Which states depend most on Bolsa Família and pensions?" | `brasil dashboard --mode anual --dependency-ranking --format json \| jq '.uf_dependency_ranking[:10]'` |
| 5 | "What is the Gini coefficient for Brazil?" | `brasil dashboard --format json \| jq '.modes.alvo.national.gini_household_sm'` |
| 6 | "How many households are in faixa 10+ SM and what's their share?" | `brasil renda-por-faixa-sm --group-by pais --format json \| jq '.groups[0].bands[] \| select(.range=="10+")'` |
| 7 | "Share of income coming from labor in each band" | `brasil dashboard --mode anual --composition-by-band --format json \| jq '.composition_by_band'` |
| 8 | "Most populous UFs by quarterly persons_total" | `brasil dashboard --format json \| jq '.modes.alvo.top10_uf_population[] \| {uf:.label, persons:.persons_total}'` |

---

## annual income lenses

When the user wants a "with vs without benefits" sensitivity, the annual
dashboard exposes these lenses in `income_lenses_national` and
`income_lenses_by_band`:

| lens | what it excludes |
|---|---|
| `renda_total` | nothing — total household income as reported |
| `sem_beneficios_sociais` | subtracts Bolsa Família, BPC, and other social benefits |
| `sem_transferencias_publicas` | subtracts all public transfers (benefits + pensions) |
| `somente_trabalho` | labor-only income (VD4020/VD4019 equivalent) |

Typical usage: compare `renda_total.gini` vs `somente_trabalho.gini` to quantify
how much redistribution the state is actually doing.

---

## methodology cheat sheet

- **Quarterly** labor income: `VD4020` (effective), fallback `VD4019`
  (habitual).
- **Annual** household income: `VD5001`, plus 8 source columns
  (`V5001A2..V5008A2`) and 4 composition lenses.
- **Household aggregation:** `dom_id = f"{Ano}{Trimestre}{UPA}{V1008}"`.
- **Weights:**
  - Quarterly primary: `V1028__peso_com_calibracao` (fallback `V1027`).
  - Annual primary: `V1032__peso_com_calibracao` (fallback `V1031`).
- **Replicate weights** for CI: `V1028001..V1028200` (trimestral) or
  `V1032001..V1032200` (anual). 200 replicates → bootstrap variance.
- **Deflator:** IPCA monthly index; target month defaults to the latest
  IPCA month, override with `--target YYYY-MM`.
- **SM reference:** BCB series 1619 (nominal monthly minimum wage).

---

## safety & guardrails

- `brasil query` is **read-only by default**. Writes require `--allow-write`.
- Default SQL parser rejects multi-statement queries.
- Claim uncertainty only when you computed it — do **not** attach a
  fabricated `± X` margin to a `query` result.
- When reporting a number publicly, include:
  - weight column actually used
  - replicate count actually found
  - IPCA target month
  - SM reference month
  - rows / households that entered the estimate
- Anything under `--unweighted` is **diagnostic only**, never publication.

---

## troubleshooting

| symptom | cause | fix |
|---|---|---|
| `brasil dashboard` shows `0 réplicas` | primary weight column didn't match any replicate prefix | check `--weight-col`, rebuild with `pipeline-run-anual` so `V1032xxx` is included |
| `unknown column VD5001` | querying `base_labeled_npv` (trimestral) instead of `base_anual_labeled_npv` | switch table |
| empty output for anual | `base_anual_labeled_npv.csv` not built | `brasil pipeline-run-anual --raw latest` |
| Gini reads 0.0 | all incomes were 0 (or weight column missing) | check `--weight-col` and filter predicate |
| deflated prices look wrong | `--target` month not in IPCA series | `brasil ibge-sync` to refresh `data/outputs/ipca.csv` |
| `brasil query` raises on CTE | mutli-statement SQL blocked | split into separate `--sql` calls |

---

## related skill

- `pnad-query` — thin sibling skill specialized in **ad-hoc SQL** with a
  column dictionary and the 10 most common safe queries pre-written.

## references in this skill

- `references/cli-cookbook.md` — extended CLI patterns and SQL recipes.
- `examples/prompts.md` — end-to-end LLM prompts that produce good results.
