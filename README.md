# Brasil CLI (PNADC + Censo + TSE)

CLI para baixar insumos oficiais (PNADC trimestral/anual, Censo 2022 e TSE), processar microdados e gerar bases analíticas em CSV + SQLite.

## Quickstart

1. Clone o repositório.
2. Crie e ative um ambiente virtual.
3. Instale dependências e o CLI localmente.
4. Baixe/atualize insumos oficiais do IBGE.
5. Rode o pipeline completo.

```bash
git clone <SEU_REPO_URL>
cd PNAD

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
pip install -e .

# scaffold local (ja vem no repo com .gitkeep, este comando e idempotente)
mkdir -p data/raw data/originals data/outputs

# baixa documentação oficial + último trimestre disponível
brasil ibge-sync

# executa extração + labels + NPV + SQLite usando o último raw local
brasil pipeline-run --raw latest

# pipeline PNADC anual visita 5 (todas as fontes de renda)
brasil pipeline-run-anual --raw data/raw/pnadc_anual_visita5/PNADC_2024_visita5.txt
```

Saídas principais:
- `data/outputs/base.csv`
- `data/outputs/base_labeled.csv`
- `data/outputs/base_labeled_npv.csv`
- `data/outputs/base_anual.csv`
- `data/outputs/base_anual_labeled.csv`
- `data/outputs/base_anual_labeled_npv.csv`
- `data/outputs/ipca.csv`
- `data/outputs/brasil.sqlite` (tabelas `base_labeled_npv` e `base_anual_labeled_npv`)

Compatibilidade:
- O comando legado `pnad` continua funcionando como alias do `brasil`.

## Estrutura Local

`data/` e versionado apenas com `.gitkeep` para scaffold.
Arquivos grandes e artefatos de execução continuam ignorados no Git:
- `data/raw/`: zips e `.txt` de microdados PNADC
- `data/originals/`: dicionários, inputs SAS/TXT e documentos oficiais
- `data/outputs/`: CSVs finais, IPCA e SQLite

## Comandos Principais

```bash
brasil --help
brasil ibge-sync --help
brasil pipeline-run --help
brasil pipeline-run-anual --help
brasil sqlite-build --help
brasil query --help
brasil renda-por-faixa-sm --help
brasil dashboard --help
```

### Atualizar para novos arquivos do IBGE

```bash
# sincroniza docs + último trimestre do último ano disponível
brasil ibge-sync

# baixa trimestre específico
brasil ibge-sync --year 2025 --quarter 3

# baixa todos os trimestres de um ano (última revisão de cada trimestre)
brasil ibge-sync --year 2025 --all-in-year
```

### Sync eleitoral completo (PNADC anual + Censo + TSE)

```bash
# baixa tudo para monitoramento eleitoral (trimestral + anual visita 5 + censo renda + tse)
brasil ibge-sync --full

# escopos individuais
brasil ibge-sync --with-anual --anual-year 2024
brasil ibge-sync --with-censo
brasil ibge-sync --with-tse --tse-year 2025
```

Diretorios adicionais usados no modo completo:
- `data/raw/pnadc_anual_visita5/`
- `data/originals/pnadc_anual_visita5/`
- `data/originals/censo_2022_renda_responsavel/`
- `data/raw/tse_eleitorado/`

### Rodar pipeline com caminhos explícitos

```bash
brasil pipeline-run \
  --sync-full \
  --raw data/raw/PNADC_032025.txt \
  --layout data/originals/input_PNADC_trimestral.sas \
  --out-dir data/outputs \
  --ipca-csv data/outputs/ipca.csv \
  --sqlite data/outputs/brasil.sqlite

brasil pipeline-run-anual \
  --raw data/raw/pnadc_anual_visita5/PNADC_2024_visita5.txt \
  --layout data/originals/pnadc_anual_visita5/input_PNADC_2024_visita5.txt \
  --out-dir data/outputs \
  --sqlite data/outputs/brasil.sqlite
```

Observacoes do pipeline:
- Se `--target` nao for informado, usa automaticamente o ultimo mes disponivel no IPCA.
- Se `--min-wage` nao for informado, usa automaticamente o salario minimo de `data/originals/salario_minimo.csv` no mes-alvo.
- O `DEFAULT_KEEP` do `fwf-extract` foi ampliado para incluir mais variaveis de desenho amostral, escolaridade e mercado de trabalho (ex.: `Estrato`, `V1022`, `V1023`, `V3002`, `VD3006`, `VD4001`, `VD4002`, `VD4010`, `V4012`, `V4013`, `V4029`, `V4039`).
- O `DEFAULT_KEEP` inclui tambem os pesos replicados `V1028001..V1028200`, usados para margem de erro/IC.

### Estatistica de renda por faixa de salario minimo

```bash
# Brasil (domicilios e pessoas por faixa de SM)
brasil renda-por-faixa-sm \
  --input data/outputs/base_labeled.csv \
  --group-by pais \
  --ranges "0-2;2-5;5-10;10+"

# Quebra por UF
brasil renda-por-faixa-sm \
  --input data/outputs/base_labeled.csv \
  --group-by uf \
  --ranges "0-2;2-5;5-10;10+"

# Quebra por UF em ordem alfabetica
brasil renda-por-faixa-sm \
  --input data/outputs/base_labeled.csv \
  --group-by uf \
  --uf-order alfabetica \
  --ranges "0-2;2-5;5-10;10+"

# UF especifica
brasil renda-por-faixa-sm \
  --input data/outputs/base_labeled.csv \
  --group-by uf \
  --state 35 \
  --ranges "0-2;2-5;5-10;10+"

# JSON para automacao
brasil renda-por-faixa-sm \
  --input data/outputs/base_labeled.csv \
  --group-by pais \
  --format json
```

Observacoes:
- O comando agrega renda familiar por `dom_id` somando a renda individual (padrao: `VD4020*`).
- Deflaciona a renda do periodo e o salario minimo nominal para o mes alvo (`--target`, ou ultimo mes no IPCA).
- `brasil ibge-sync` atualiza automaticamente `data/originals/salario_minimo.csv`.
- O padrao e ponderado (usa `V1028`, fallback `V1027`) para estimativa populacional.
- Se o CSV nao tiver peso, reexecute o pipeline para gerar `base_labeled.csv` com `V1028`.
- `--unweighted` existe apenas para diagnostico de amostra.
- Intervalos de confianca e margem de erro (IC 95%) sao calculados por padrao com pesos replicados (`V1028001..V1028200`), quando presentes no CSV.
- Se estiver usando CSV legado sem pesos replicados, o CLI sinaliza e segue sem CI ate o pipeline ser rerodado.
- Para desativar IC: `--no-ci`. Para outro nivel: `--ci-level 0.90` (por exemplo).
- O formato padrao (`--format pretty`) imprime tabela, barras e mini pizza no terminal.
- Paleta BR no terminal: verde (mais pobre), amarelo (media baixa), azul (media alta), branco (mais rica).
- O terminal mostra as faixas tambem em valores nominais (`R$`) para leitura direta pelo publico brasileiro.
- Em `--group-by uf`, a ordem padrao e `--uf-order renda_desc` (estado mais rico para o mais pobre, por media domiciliar em SM).

### Dashboard economico no terminal

```bash
# painel completo (default: --sm-mode alvo)
brasil dashboard \
  --input data/outputs/base_labeled.csv

# modo interativo (navega por secoes e modos)
brasil dashboard \
  --input data/outputs/base_labeled.csv \
  --interactive

# visual forte no terminal (cards, barras, sparklines e pizza textual)
brasil dashboard \
  --input data/outputs/base_labeled.csv

# comparacao completa entre SM do periodo e SM alvo
brasil dashboard \
  --input data/outputs/base_labeled.csv \
  --sm-mode both

# exportar snapshot estruturado
brasil dashboard \
  --input data/outputs/base_labeled.csv \
  --format json > data/outputs/dashboard.json
```

O dashboard agora inclui:
- Top 10 UFs por renda domiciliar em SM e Top 10 UFs por populacao estimada.
- Painel por macro-regiao (Norte/Nordeste/Sudeste/Sul/Centro-Oeste) com mix por faixa.
- Termometro socioeconomico com destaques automáticos (UF mais rica/pobre e concentracao nas faixas extrema baixa/extrema alta).
- Faixa de cores BR em alto contraste no cabecalho e nas barras (verde, amarelo, azul e branco).
- Legenda de faixas em `R$` (ex.: `0-2 SM = R$ 0,00 a R$ ...`) usando SM de referencia do modo.
- Piramide etaria (sexo x idade) em painel dedicado, com idades ordenadas de forma crescente.
- Recortes adicionais quando disponiveis no CSV (ex.: relacao no domicilio, condicao ocupacional, tipo/posicao de trabalho, RM/RIDE).
- Para variaveis de universo restrito (ocupacao e RM/RIDE), o dashboard diferencia `Nao se aplica`/`Fora de RM/RIDE` de `Sem informacao`.
- IC/margem de erro por faixa e por renda media (bootstrap por pesos replicados) por padrao.
- Controles amostrais: `--no-ci` e `--ci-level`.

## Rebuild de SQLite

```bash
brasil sqlite-build \
  --input data/outputs/base_labeled_npv.csv \
  --db data/outputs/brasil.sqlite \
  --table base_labeled_npv
```

## Query SQL para LLMs (`brasil query`)

`brasil query` roda SQL direto no SQLite e retorna JSON por padrão (ideal para uso por LLMs e automações).

```bash
# listar tabelas
brasil query \
  --db data/outputs/brasil.sqlite \
  --sql "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"

# schema de uma tabela
brasil query \
  --db data/outputs/brasil.sqlite \
  --sql "PRAGMA table_info(base_labeled_npv)"

# top UFs por renda média (exemplo)
brasil query \
  --db data/outputs/brasil.sqlite \
  --sql "SELECT UF__unidade_da_federacao AS uf, AVG(VD4020__rendim_efetivo_qq_trabalho) AS renda_media FROM base_labeled_npv GROUP BY 1 ORDER BY 2 DESC LIMIT 10"

# modo tabela para leitura humana
brasil query \
  --db data/outputs/brasil.sqlite \
  --sql "SELECT UF__unidade_da_federacao, COUNT(*) AS n FROM base_labeled_npv GROUP BY 1 ORDER BY 2 DESC LIMIT 10" \
  --format table
```

Observacoes:
- Formato padrao: `json`.
- Segurança por padrão: apenas SQL de leitura (`SELECT/WITH/PRAGMA/EXPLAIN`).
- Limite padrão de retorno: `--max-rows 200` (com flag de truncamento no payload).
- Também aceita SQL por arquivo (`--sql-file`) ou `stdin` (pipe).
- O payload JSON de `brasil query` inclui metadados amostrais (`sampling`) para orientar LLMs.
- `brasil query` nao infere IC automaticamente para SQL arbitrario; para IC pronto por padrao use `brasil renda-por-faixa-sm` ou `brasil dashboard`.

## Comandos legados

Subcomandos antigos continuam disponíveis via `brasil`:

```bash
brasil inspect data/outputs/base_labeled.csv
brasil fwf-extract data/originals/input_PNADC_trimestral.sas data/raw/PNADC_032025.txt --header > data/outputs/base.csv
brasil join-codes data/outputs/base.csv --codes-dir data/outputs > data/outputs/base_labeled.csv
```

## Testes

```bash
pytest -q
```

## Observações

- O repositório não versiona microdados brutos nem binários grandes de referência.
- Para atualizar insumos locais, execute `brasil ibge-sync` novamente.
- O comando de sync usa metadados (`ETag`/`Last-Modified`) para evitar re-download quando não houve mudança.
- Cada trimestre PNADC pode ocupar alguns GB após extração; garanta espaço em disco em `data/raw/`.
