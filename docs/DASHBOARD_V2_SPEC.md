# Dashboard v2.0 - Especificação Técnica

## Objetivo

Evoluir o comando `brasil dashboard` para suportar análise completa de composição de renda da PNAD Anual Visita 5, permitindo:

1. Breakdown por fonte de renda
2. Análise de dependência de benefícios vs trabalho por UF
3. Validação de metodologia de centros de pesquisa
4. Faixas de renda com composição detalhada

## Variáveis de Renda (PNAD Anual Visita 5)

### Fontes de Renda Não-Trabalho (V50xxA2)
| Variável | Descrição | Categoria |
|----------|-----------|-----------|
| V5001A2 | BPC-LOAS | Benefício Social |
| V5002A2 | Bolsa Família | Benefício Social |
| V5003A2 | Outros programas sociais | Benefício Social |
| V5004A2 | Aposentadoria e pensão | Previdência |
| V5005A2 | Seguro-desemprego | Seguro |
| V5006A2 | Pensão alimentícia, doações | Transferência Privada |
| V5007A2 | Aluguel e arrendamento | Capital |
| V5008A2 | Outros (poupança, aplicações) | Capital |

### Agregados Domiciliares (VD50xx)
| Variável | Descrição |
|----------|-----------|
| VD5001 | Renda efetiva domiciliar total |
| VD5002 | Renda efetiva domiciliar per capita |
| VD5003 | Faixa de renda per capita (categorizada) |

### Renda do Trabalho (calculada)
```
Renda_Trabalho = VD5001 - sum(V5001A2, V5002A2, V5003A2, V5004A2, V5005A2, V5006A2, V5007A2, V5008A2)
```

## Categorias de Composição

1. **Trabalho**: Renda calculada por diferença
2. **Benefícios Sociais**: V5001A2 + V5002A2 + V5003A2
3. **Previdência**: V5004A2
4. **Seguro**: V5005A2
5. **Transferências Privadas**: V5006A2
6. **Capital**: V5007A2 + V5008A2

## Mudanças no CLI

### Novos argumentos para `brasil dashboard`

```
--mode {trimestral,anual,comparativo}
    Modo de análise. Default: auto-detecta baseado nas colunas disponíveis.

--breakdown
    Mostra composição de renda por fonte (só modo anual).

--source-detail
    Mostra cada fonte V50xxA2 separadamente (não agrupado).

--dependency-ranking
    Ordena UFs por % de renda de benefícios (mostra dependência).

--composition-by-band
    Mostra composição de renda dentro de cada faixa de SM.
```

### Exemplo de uso

```bash
# Dashboard anual com breakdown completo
brasil dashboard \
  --input data/outputs/base_anual_labeled_npv.csv \
  --mode anual \
  --breakdown \
  --dependency-ranking

# Composição por faixa de SM
brasil dashboard \
  --input data/outputs/base_anual_labeled_npv.csv \
  --mode anual \
  --composition-by-band \
  --ranges "0-1;1-2;2-5;5-10;10+"
```

## Mudanças no Código

### 1. `_detect_income_col()` (linha ~559)

Atualizar para detectar VD5001/VD5002 quando presente:

```python
def _detect_income_col(headers: Sequence[str], requested: Optional[str]) -> str:
    if requested:
        if requested not in headers:
            raise ValueError(f"income column not found: {requested}")
        return requested
    # Anual: renda domiciliar total
    c = next((h for h in headers if h.startswith("VD5001")), None)
    if c:
        return c
    # Trimestral: renda do trabalho
    c = next((h for h in headers if h.startswith("VD4020")), None)
    if c:
        return c
    c = next((h for h in headers if h.startswith("VD4019")), None)
    if c:
        return c
    raise ValueError("could not auto-detect income column; use --income-col")
```

### 2. Nova função `_detect_income_source_cols()`

```python
INCOME_SOURCE_COLS = {
    "bpc_loas": "V5001A2",
    "bolsa_familia": "V5002A2",
    "outros_sociais": "V5003A2",
    "aposentadoria_pensao": "V5004A2",
    "seguro_desemprego": "V5005A2",
    "pensao_doacao": "V5006A2",
    "aluguel": "V5007A2",
    "outros_capital": "V5008A2",
}

INCOME_CATEGORIES = {
    "trabalho": [],  # Calculado por diferença
    "beneficios_sociais": ["bpc_loas", "bolsa_familia", "outros_sociais"],
    "previdencia": ["aposentadoria_pensao"],
    "seguro": ["seguro_desemprego"],
    "transferencias_privadas": ["pensao_doacao"],
    "capital": ["aluguel", "outros_capital"],
}

def _detect_income_source_cols(headers: Sequence[str]) -> Dict[str, str]:
    """Detect income source columns in headers, return {source_key: actual_col_name}"""
    found = {}
    for key, prefix in INCOME_SOURCE_COLS.items():
        col = next((h for h in headers if h.startswith(prefix)), None)
        if col:
            found[key] = col
    return found
```

### 3. Nova função `_calculate_income_composition()`

```python
def _calculate_income_composition(
    row: Dict[str, str],
    total_income_col: str,
    source_cols: Dict[str, str],
) -> Dict[str, float]:
    """Calculate income composition for a household"""
    total = _parse_float(row.get(total_income_col, "")) or 0.0
    if total <= 0:
        return {}
    
    sources = {}
    non_work_total = 0.0
    
    for key, col in source_cols.items():
        val = _parse_float(row.get(col, "")) or 0.0
        sources[key] = val
        non_work_total += val
    
    # Renda do trabalho = total - soma das outras fontes
    sources["trabalho"] = max(0.0, total - non_work_total)
    
    # Calcula percentuais
    composition = {}
    for key, val in sources.items():
        composition[key] = val / total if total > 0 else 0.0
    
    return composition
```

### 4. Atualizar `_build_dashboard_payload()` (linha ~1259)

Adicionar lógica para:
- Detectar colunas de fonte de renda
- Calcular composição por domicílio
- Agregar por UF
- Agregar por faixa de SM

### 5. Novo payload JSON para modo anual

```json
{
  "mode": "anual",
  "income_col": "VD5001__rend_efetivo_domiciliar",
  "total_households": 374783,
  "total_income_mean": 5418.04,
  "total_income_median": 3200.00,
  
  "income_composition_national": {
    "trabalho": {"mean": 3902.19, "pct": 72.0},
    "beneficios_sociais": {"mean": 379.26, "pct": 7.0},
    "previdencia": {"mean": 975.25, "pct": 18.0},
    "seguro": {"mean": 27.09, "pct": 0.5},
    "transferencias_privadas": {"mean": 54.18, "pct": 1.0},
    "capital": {"mean": 81.27, "pct": 1.5}
  },
  
  "income_sources_detail": {
    "bpc_loas": {"mean": 108.36, "pct": 2.0, "recipients_pct": 3.2},
    "bolsa_familia": {"mean": 162.54, "pct": 3.0, "recipients_pct": 21.5},
    "outros_sociais": {"mean": 108.36, "pct": 2.0, "recipients_pct": 1.8},
    "aposentadoria_pensao": {"mean": 975.25, "pct": 18.0, "recipients_pct": 28.4},
    "seguro_desemprego": {"mean": 27.09, "pct": 0.5, "recipients_pct": 2.1},
    "pensao_doacao": {"mean": 54.18, "pct": 1.0, "recipients_pct": 4.3},
    "aluguel": {"mean": 54.18, "pct": 1.0, "recipients_pct": 5.2},
    "outros_capital": {"mean": 27.09, "pct": 0.5, "recipients_pct": 8.7}
  },
  
  "uf_dependency_ranking": [
    {
      "uf_code": "22",
      "uf_label": "Piauí",
      "income_mean": 2341.50,
      "work_pct": 48.2,
      "benefits_pct": 18.5,
      "previdencia_pct": 28.3,
      "dependency_score": 46.8
    },
    ...
  ],
  
  "composition_by_band": {
    "0-1SM": {
      "households_pct": 32.1,
      "composition": {
        "trabalho": 35.2,
        "beneficios_sociais": 28.4,
        "previdencia": 31.2,
        "outros": 5.2
      }
    },
    "1-2SM": {...},
    ...
  }
}
```

### 6. Atualizar `_print_dashboard_pretty()` para modo anual

Adicionar seções:
- Composição Nacional de Renda (barras)
- Ranking de Dependência por UF
- Composição por Faixa de SM

## Métricas-Chave para Jornalismo

1. **Dependency Score por UF**: `(beneficios + previdencia) / total * 100`
2. **Work Income Ratio**: `trabalho / total * 100`
3. **Beneficiary Rate**: `% domicílios que recebem cada tipo`
4. **Poverty Trap Indicator**: Domicílios onde `beneficios > trabalho` e renda < 2SM

## Testes

Adicionar em `tests/test_dashboard_anual.py`:

1. `test_detect_income_source_cols()`
2. `test_calculate_income_composition()`
3. `test_dashboard_anual_mode_detection()`
4. `test_dashboard_breakdown_output()`
5. `test_dependency_ranking_ordering()`

## Prioridade de Implementação

1. ✅ `_detect_income_col()` - detectar VD5001
2. ⬜ `_detect_income_source_cols()` - detectar V50xxA2
3. ⬜ `_calculate_income_composition()` - calcular composição
4. ⬜ Atualizar `_build_dashboard_payload()` - agregar
5. ⬜ Novos argumentos CLI
6. ⬜ Pretty print com barras
7. ⬜ Testes
