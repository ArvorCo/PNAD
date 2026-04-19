# LLM prompts that produce good results with `brasil-cli-analyst`

These are end-to-end prompts tested against an agent that has this skill
loaded and bash access to a machine with the repo installed. Copy and adapt.

---

## 1. "Paint me a picture of Brazilian income"

**User**: Dá um panorama geral da renda dos brasileiros hoje, com os pontos
mais importantes que eu precisaria saber em 90 segundos.

**Expected model behavior**:

```bash
brasil dashboard --mode anual --format json > /tmp/d.json
jq '{
  gini: .modes.alvo.national.gini_household_sm,
  avg_sm: .modes.alvo.national.avg_household_sm,
  median_sm: .modes.alvo.national.median_household_sm,
  top_uf: .modes.alvo.top10_uf_income[0],
  bottom_uf: .modes.alvo.bottom10_uf_income[0],
  insights: .modes.alvo.insights
}' /tmp/d.json
```

Then **summarize in 5 bullet points**, citing vintage + weight column.

---

## 2. "Where does Bolsa Família matter most?"

**User**: Em que UFs a fatia da renda vinda de benefícios sociais e
previdência é maior? Me dá um top 5 com número e comparação com a média BR.

**Expected**:

```bash
brasil dashboard --mode anual --dependency-ranking --format json | \
  jq '.uf_dependency_ranking | sort_by(-.dependency_score) | .[:5]'
```

Narrate the top 5 with their `dependency_score`, `benefits_pct`,
`previdencia_pct`, and compare to the national average.

---

## 3. "Is Santa Catarina richer than São Paulo?"

**User**: Santa Catarina supera São Paulo em renda média?

**Expected**:

```bash
brasil query \
  --db data/outputs/brasil.sqlite \
  --sql "SELECT UF_label AS uf, \
                AVG(VD5001__rendim_domiciliar) AS avg_brl, \
                COUNT(DISTINCT dom_id) AS households \
         FROM base_anual_labeled_npv \
         WHERE UF_label IN ('Santa Catarina','São Paulo') \
         GROUP BY 1"
```

Answer with both values and the difference; note this is unweighted from SQL
and suggest `renda-por-faixa-sm` if they need a weighted publication-ready
number.

---

## 4. "How unequal is Brazil really?"

**User**: O Brasil é mais igual ou mais desigual do que diz o discurso oficial?

**Expected**:

```bash
brasil dashboard --mode anual --format json | \
  jq '.modes.alvo.national | {gini: .gini_household_sm, bands: .bands}'
```

Contextualize: compare Gini to Portugal (0.33), Germany (0.30), USA (0.40).
Note that the value varies slightly by methodology (household per-capita vs
effective labor income) — cite which one was used.

---

## 5. "What's the racial income gap?"

**User**: Qual a diferença de renda entre brancos e pretos/pardos na faixa
mais alta de salário mínimo?

**Expected**:

```bash
brasil dashboard --mode anual --format json | \
  jq '.modes.alvo.cross.race_by_band'
```

Narrate the `10+` band: compare `pct_within_label` for "Branca", "Parda",
"Preta". Also compute the education gap for the same band — often more
informative.

---

## 6. "Give me a state-by-state heatmap in data"

**User**: Lista todas as 27 UFs ordenadas por renda média, com intervalo de
confiança.

**Expected**:

```bash
brasil dashboard --mode anual --format json | \
  jq '.modes.alvo.uf | sort_by(-.avg_household_sm) | \
      map({uf: .label, sm: .avg_household_sm, moe: .avg_household_sm_moe})'
```

---

## 7. "Check if the data is recent"

**User**: Qual a edição mais recente da PNADC que eu tenho localmente?

**Expected**:

```bash
brasil dashboard --format json | jq '{target, vintage: .metadata, sampling}'
```

If the target month looks old, suggest `brasil ibge-sync && brasil pipeline-run-anual`.

---

## 8. "Build a briefing for a journalism piece"

**User**: Preciso de um mini-briefing, com números específicos, sobre como a
renda se compõe por faixa — para uma matéria sobre dependência estatal.

**Expected**:

```bash
brasil dashboard --mode anual --composition-by-band --format json > /tmp/c.json
jq '.composition_by_band' /tmp/c.json
```

Then produce a 3-paragraph brief citing: for each band, the share from
labor, benefits, pensions, and capital. Include the caveat that
these percentages do not sum to 100 (households can have multiple sources
simultaneously in the PNADC).

---

## anti-patterns (don't do this)

- ❌ Claim `± X` uncertainty after a `brasil query` — query does not compute CI.
- ❌ Use `base_labeled_npv` when the question is about benefits/pensions —
  that's the trimestral table which doesn't separate sources.
- ❌ Omit the target month / vintage when reporting a number publicly.
- ❌ Use `--unweighted` for a publication claim.
- ❌ Assume column names — always `PRAGMA table_info(...)` first when
  writing fresh SQL.
- ❌ Try to JOIN trimestral and anual tables on `dom_id` — they use
  different sampling frames.
