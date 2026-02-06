# PNAD/PNADC Pipeline

CLI para baixar insumos oficiais da PNAD Contínua (IBGE), processar microdados e gerar uma base final em CSV + SQLite.

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
pnad ibge-sync

# executa extração + labels + NPV + SQLite usando o último raw local
pnad pipeline-run --raw latest
```

Saídas principais:
- `data/outputs/base.csv`
- `data/outputs/base_labeled.csv`
- `data/outputs/base_labeled_npv.csv`
- `data/outputs/ipca.csv`
- `data/outputs/pnad.sqlite` (tabela `base_labeled_npv`)

## Estrutura Local

`data/` e versionado apenas com `.gitkeep` para scaffold.
Arquivos grandes e artefatos de execução continuam ignorados no Git:
- `data/raw/`: zips e `.txt` de microdados PNADC
- `data/originals/`: dicionários, inputs SAS/TXT e documentos oficiais
- `data/outputs/`: CSVs finais, IPCA e SQLite

## Comandos Principais

```bash
pnad --help
pnad ibge-sync --help
pnad pipeline-run --help
pnad sqlite-build --help
pnad renda-por-faixa-sm --help
pnad dashboard --help
```

### Atualizar para novos arquivos do IBGE

```bash
# sincroniza docs + último trimestre do último ano disponível
pnad ibge-sync

# baixa trimestre específico
pnad ibge-sync --year 2025 --quarter 3

# baixa todos os trimestres de um ano (última revisão de cada trimestre)
pnad ibge-sync --year 2025 --all-in-year
```

### Rodar pipeline com caminhos explícitos

```bash
pnad pipeline-run \
  --raw data/raw/PNADC_032025.txt \
  --layout data/originals/input_PNADC_trimestral.sas \
  --out-dir data/outputs \
  --ipca-csv data/outputs/ipca.csv \
  --sqlite data/outputs/pnad.sqlite
```

Observacoes do pipeline:
- Se `--target` nao for informado, usa automaticamente o ultimo mes disponivel no IPCA.
- Se `--min-wage` nao for informado, usa automaticamente o salario minimo de `data/originals/salario_minimo.csv` no mes-alvo.

### Estatistica de renda por faixa de salario minimo

```bash
# Brasil (domicilios e pessoas por faixa de SM)
pnad renda-por-faixa-sm \
  --input data/outputs/base_labeled.csv \
  --group-by pais \
  --ranges "0-2;2-5;5-10;10+"

# Quebra por UF
pnad renda-por-faixa-sm \
  --input data/outputs/base_labeled.csv \
  --group-by uf \
  --ranges "0-2;2-5;5-10;10+"

# Quebra por UF em ordem alfabetica
pnad renda-por-faixa-sm \
  --input data/outputs/base_labeled.csv \
  --group-by uf \
  --uf-order alfabetica \
  --ranges "0-2;2-5;5-10;10+"

# UF especifica
pnad renda-por-faixa-sm \
  --input data/outputs/base_labeled.csv \
  --group-by uf \
  --state 35 \
  --ranges "0-2;2-5;5-10;10+"

# JSON para automacao
pnad renda-por-faixa-sm \
  --input data/outputs/base_labeled.csv \
  --group-by pais \
  --format json
```

Observacoes:
- O comando agrega renda familiar por `dom_id` somando a renda individual (padrao: `VD4020*`).
- Deflaciona a renda do periodo e o salario minimo nominal para o mes alvo (`--target`, ou ultimo mes no IPCA).
- `pnad ibge-sync` atualiza automaticamente `data/originals/salario_minimo.csv`.
- O padrao e ponderado (usa `V1028`, fallback `V1027`) para estimativa populacional.
- Se o CSV nao tiver peso, reexecute o pipeline para gerar `base_labeled.csv` com `V1028`.
- `--unweighted` existe apenas para diagnostico de amostra.
- O formato padrao (`--format pretty`) imprime tabela, barras e mini pizza no terminal.
- Paleta BR no terminal: verde (mais pobre), amarelo (media baixa), azul (media alta), branco (mais rica).
- O terminal mostra as faixas tambem em valores nominais (`R$`) para leitura direta pelo publico brasileiro.
- Em `--group-by uf`, a ordem padrao e `--uf-order renda_desc` (estado mais rico para o mais pobre, por media domiciliar em SM).

### Dashboard economico no terminal

```bash
# painel completo (default: --sm-mode alvo)
pnad dashboard \
  --input data/outputs/base_labeled.csv

# modo interativo (navega por secoes e modos)
pnad dashboard \
  --input data/outputs/base_labeled.csv \
  --interactive

# visual forte no terminal (cards, barras, sparklines e pizza textual)
pnad dashboard \
  --input data/outputs/base_labeled.csv

# comparacao completa entre SM do periodo e SM alvo
pnad dashboard \
  --input data/outputs/base_labeled.csv \
  --sm-mode both

# exportar snapshot estruturado
pnad dashboard \
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

## Rebuild de SQLite

```bash
pnad sqlite-build \
  --input data/outputs/base_labeled_npv.csv \
  --db data/outputs/pnad.sqlite \
  --table base_labeled_npv
```

## Comandos legados

Subcomandos antigos continuam disponíveis via `pnad`:

```bash
pnad inspect data/outputs/base_labeled.csv
pnad fwf-extract data/originals/input_PNADC_trimestral.sas data/raw/PNADC_032025.txt --header > data/outputs/base.csv
pnad join-codes data/outputs/base.csv --codes-dir data/outputs > data/outputs/base_labeled.csv
```

## Testes

```bash
pytest -q
```

## Observações

- O repositório não versiona microdados brutos nem binários grandes de referência.
- Para atualizar insumos locais, execute `pnad ibge-sync` novamente.
- O comando de sync usa metadados (`ETag`/`Last-Modified`) para evitar re-download quando não houve mudança.
- Cada trimestre PNADC pode ocupar alguns GB após extração; garanta espaço em disco em `data/raw/`.
