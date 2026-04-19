---
name: pnad-query
description: Use this skill for ad-hoc read-only SQL on the PNADC SQLite database produced by this repo (`data/outputs/brasil.sqlite`). Trigger when the user asks for a precise custom aggregate — a specific AVG/SUM/COUNT, a specific UF or demographic cut, an arbitrary filter — that `brasil dashboard` or `brasil renda-por-faixa-sm` cannot express. Provides a PT/EN column dictionary, ten ready-made safe queries, and LLM guardrails. Companion to `brasil-cli-analyst` for the "exact number for X" use case.
---

# pnad-query

A narrow-focus skill: **run safe, read-only SQL** against the PNADC SQLite
database built by `brasil pipeline-run` / `brasil pipeline-run-anual`.

Use when the question is:

- *"Exact average labor income in Pernambuco for men aged 40-59"*
- *"Share of households in Recife where the reference person has completed higher education"*
- *"Count of workers with formal contract in Santa Catarina industry"*

— i.e. **specific, flat queries** the dashboard does not express.

For broader "paint me a picture" questions, prefer `brasil-cli-analyst`.

---

## the one command you need

```bash
brasil query \
  --db data/outputs/brasil.sqlite \
  --sql "<YOUR_SQL>" \
  --format json
```

Defaults: read-only, max 500 rows, JSON output, sampling metadata attached.

---

## tables

| table | survey | primary income column | separate benefits? |
|---|---|---|---|
| `base_labeled_npv` | **PNADC trimestral** | `VD4020__rendim_efetivo_qq_trabalho` (effective labor income) | ❌ |
| `base_anual_labeled_npv` | **PNADC anual visita 5** | `VD5001__rendim_domiciliar` (full household income) | ✅ — `V5001A2..V5008A2` |

Rule of thumb:

- If the question involves **benefits / pensions / capital** → `base_anual_labeled_npv`.
- If the question involves **occupation / labor status / industry** → either, but annual is more complete for household-level questions.
- If the question is **quarterly time-series** (e.g. 2025 Q1 vs Q3) → `base_labeled_npv`.

Always inspect schema first:

```bash
brasil query --db data/outputs/brasil.sqlite \
  --sql "PRAGMA table_info(base_anual_labeled_npv)" --max-rows 300
```

---

## column dictionary (most-used fields, PT / EN)

Column names in SQLite are `VARIABLE__slug`, where `VARIABLE` is the IBGE
code and `slug` is a short Portuguese label. Select the raw column by its
full name; reference it in narrative with the human label.

### geography

| column | label (pt) | label (en) |
|---|---|---|
| `UF__unidade_da_federacao` | UF (código 11-53) | state code |
| `UF_label` | UF (nome) | state name |
| `Capital__municipio_da_capital` | capital (código) | capital city code |
| `Capital_label` | capital x interior | capital vs interior |
| `RM_RIDE__reg_metr_e_reg_adm_int_des` | região metropolitana | metro region |

### household

| column | label (pt) | label (en) |
|---|---|---|
| `dom_id` | identificador do domicílio | household ID |
| `UPA__unidade_primaria_de_amostragem` | UPA | primary sampling unit |
| `VD2003__numero_de_componentes_do_domic` | nº de pessoas no domicílio | household size |

### weights

| column | label (pt) | label (en) |
|---|---|---|
| `V1028__peso_com_calibracao` | peso (trimestral) | quarterly weight |
| `V1027__peso_sem_calibracao` | peso sem calibração | non-calibrated weight |
| `V1032__peso_com_calibracao` | peso (anual) | annual weight |
| `V1028001..V1028200` | pesos replicados trimestral | quarterly replicate weights |
| `V1032001..V1032200` | pesos replicados anual | annual replicate weights |

### person demographics

| column | label (pt) | label (en) |
|---|---|---|
| `V2007__sexo` | sexo | sex |
| `V2007_label` | sexo (rótulo) | sex (label) |
| `V2009__idade_na_data_de_referencia` | idade | age |
| `V2010__cor_ou_raca` | cor/raça | race/color |
| `V2010_label` | cor/raça (rótulo) | race/color (label) |
| `V3009A__curso_mais_elevado_q_frequento` | escolaridade | education |

### occupation (quarterly)

| column | label (pt) | label (en) |
|---|---|---|
| `VD4009__condicao_na_ocupacao_semana_de` | condição ocupacional | occupation status |
| `VD4005__pessoas_desalentadas` | desalento | discouragement |
| `V4010_label` | grande grupo ocupacional | major occupation group |

### income (quarterly PNADC)

| column | label (pt) | label (en) |
|---|---|---|
| `VD4019__rendim_habitual_qq_trabalho` | rendimento habitual de todos os trabalhos | habitual labor income |
| `VD4020__rendim_efetivo_qq_trabalho` | rendimento efetivo de todos os trabalhos | effective labor income |

### income (annual PNADC visita 5)

| column | label (pt) | label (en) |
|---|---|---|
| `VD5001__rendim_domiciliar` | rendimento domiciliar total | total household income |
| `V5001A2__val_recebido_aposentad_bpc` | aposentadoria + BPC recebidos | retirement + BPC received |
| `V5002A2__val_recebido_pensao_alim` | pensão alimentícia recebida | alimony received |
| `V5003A2__val_recebido_seguro_desemp` | seguro-desemprego recebido | unemployment insurance received |
| `V5004A2__val_recebido_bolsa_familia` | Bolsa Família recebido | Bolsa Família received |
| `V5005A2__val_recebido_outros_prog_soc` | outros programas sociais | other social programs |
| `V5006A2__val_recebido_juros_poup_fin` | juros e rendimentos financeiros | interest and capital gains |
| `V5007A2__val_recebido_aluguel_arrend` | aluguel e arrendamento | rent received |
| `V5008A2__val_recebido_outros_rendim` | outros rendimentos | other income |

### suffixes added by this repo's pipeline

| suffix | meaning |
|---|---|
| `_<YYYYMM>` | IPCA-deflated to the target month (e.g. `VD4020__rendim..._202601`) |
| `_mw` | converted to multiples of the minimum wage at the target month |

---

## ten ready-made safe queries

### 1. average household income per UF (annual)

```sql
SELECT UF_label AS uf,
       AVG(VD5001__rendim_domiciliar) AS avg_brl,
       COUNT(DISTINCT dom_id) AS households
FROM base_anual_labeled_npv
WHERE VD5001__rendim_domiciliar > 0
GROUP BY 1
ORDER BY 2 DESC;
```

### 2. median household size

```sql
SELECT VD2003__numero_de_componentes_do_domic AS n_pessoas,
       COUNT(*) AS n_domicilios
FROM base_anual_labeled_npv
GROUP BY 1 ORDER BY 1;
```

### 3. share of households receiving Bolsa Família by UF

```sql
SELECT UF_label AS uf,
       100.0 * SUM(CASE WHEN V5004A2__val_recebido_bolsa_familia > 0 THEN 1 ELSE 0 END)
             / COUNT(*) AS pct_bolsa_familia
FROM base_anual_labeled_npv
GROUP BY 1 ORDER BY 2 DESC;
```

### 4. average labor income for men vs women (annual)

```sql
SELECT V2007_label AS sexo,
       AVG(VD4020__rendim_efetivo_qq_trabalho) AS avg_brl
FROM base_anual_labeled_npv
WHERE VD4020__rendim_efetivo_qq_trabalho > 0
GROUP BY 1;
```

### 5. race × education crosstab (counts)

```sql
SELECT V2010_label AS cor,
       V3009A__curso_mais_elevado_q_frequento AS escolaridade,
       COUNT(*) AS n
FROM base_anual_labeled_npv
GROUP BY 1, 2
ORDER BY 1, 2;
```

### 6. top 10 highest-earning households in the country (annual)

```sql
SELECT dom_id, UF_label, VD5001__rendim_domiciliar
FROM base_anual_labeled_npv
ORDER BY VD5001__rendim_domiciliar DESC
LIMIT 10;
```

### 7. share of people in each age bracket (quarterly)

```sql
SELECT CASE
         WHEN V2009__idade_na_data_de_referencia < 14 THEN '00-13'
         WHEN V2009__idade_na_data_de_referencia < 25 THEN '14-24'
         WHEN V2009__idade_na_data_de_referencia < 40 THEN '25-39'
         WHEN V2009__idade_na_data_de_referencia < 60 THEN '40-59'
         ELSE '60+'
       END AS faixa,
       COUNT(*) AS n
FROM base_labeled_npv
GROUP BY 1 ORDER BY 1;
```

### 8. median retirement income in a macro-region

```sql
SELECT UF_label AS uf,
       AVG(V5001A2__val_recebido_aposentad_bpc) AS avg_aposentadoria
FROM base_anual_labeled_npv
WHERE UF_label IN ('Maranhão','Piauí','Ceará','Rio Grande do Norte','Paraíba',
                   'Pernambuco','Alagoas','Sergipe','Bahia')
  AND V5001A2__val_recebido_aposentad_bpc > 0
GROUP BY 1 ORDER BY 2 DESC;
```

### 9. share of informally-employed workers by UF (quarterly)

```sql
SELECT UF_label AS uf,
       100.0 * SUM(CASE WHEN VD4009_label LIKE '%sem carteira%' THEN 1 ELSE 0 END)
             / SUM(CASE WHEN VD4009_label IS NOT NULL THEN 1 ELSE 0 END) AS pct_informal
FROM base_labeled_npv
GROUP BY 1 ORDER BY 2 DESC;
```

### 10. inequality within a single UF (P90/P10 of household income)

```sql
WITH ranked AS (
  SELECT VD5001__rendim_domiciliar AS r,
         NTILE(10) OVER (ORDER BY VD5001__rendim_domiciliar) AS decile
  FROM base_anual_labeled_npv
  WHERE UF_label = 'São Paulo' AND VD5001__rendim_domiciliar > 0
)
SELECT decile, AVG(r) AS avg_r
FROM ranked
GROUP BY decile ORDER BY decile;
```

(Then compute P90/P10 = `avg_r[10] / avg_r[1]` in your narrative.)

---

## guardrails for LLM agents

1. **Never claim CI from a `brasil query` result.** Arbitrary SQL does not
   compute bootstrap variance. If the user needs CI/MOE, switch to
   `brasil renda-por-faixa-sm --format json` or
   `brasil dashboard --format json`.

2. **Inspect schema before inventing column names.** A wrong column name
   will silently return `NULL` or error. Always `PRAGMA table_info(...)`
   first in a fresh session.

3. **Cite vintage.** Every published number should say *which edition* of
   the PNADC was used. `brasil query --format json` includes vintage in
   `sampling`/metadata.

4. **Read-only by default.** If the user needs `UPDATE`/`DELETE`, require
   them to pass `--allow-write` explicitly and explain the risk.

5. **Use `LIMIT` when exploring.** `--max-rows 500` is the default, but
   prefer `LIMIT 20` in the SQL itself for cost clarity.

6. **No multi-statement SQL.** If you need a CTE + aggregation, write them
   as a single `WITH ... SELECT` query, not two `;`-separated statements.

7. **Don't JOIN trimestral and anual tables on `dom_id`.** Different
   sampling frames. If a cross-survey question arises, escalate to
   `brasil-cli-analyst` which knows the right lens.

---

## when to hand off

- If the user's question needs **CI, Gini, Lorenz, or band-level weighted
  estimates** → switch to `brasil-cli-analyst`.
- If the user's question is a **long narrative briefing** → switch to
  `brasil-cli-analyst`.
- If the user wants a **chart** → point them to `docs/index.html` or
  generate one via Python + matplotlib using the SQL result.
