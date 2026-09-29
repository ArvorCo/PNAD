# BTG/Nexus, rodada 16, 28/09/2026

Relatório oficial arquivado em `docs/fontes/nexus_btg_28092026.pdf`;
registro BR-07557/2026 transcrito em
`docs/fontes/nexus_btg_28092026/registro-metodologia.txt`.
O questionário não pôde ser exportado: primeira página e PF15 (p. 13)
foram conferidas na interface, sem auditoria integral de ordem e rodízio.

## Reprodução

```sh
python3 scripts/nexus-btg-28092026-audit.py
python3 scripts/nexus-btg-28092026-build.py
python3 scripts/reponderacao-pnad.py calcular --hoje 2026-09-28
python3 scripts/reponderacao-build.py
python3 scripts/social-cards.py --only nexus_btg_28092026
python3 -m pytest -q
```

Dependências: NumPy, SciPy, `pdftotext`, benchmark PNAD/IPCA do agregador
e `analysis/voto_util/tse_2022_uf.json`. O JSON público conserva o hash
da base histórica, contagens e URLs oficiais de cada UF.

`relatorio.txt` e `paginas.json` contêm a extração das 145 páginas.
As tabelas de voto e presença são extraídas por programa; a matriz da
p. 84 exige conferência visual das cores para localizar as barras nulas.
Cinco partições independentes conferem a recomposição dos placares.

O produto principal é `docs/nexus_btg_28092026.html`, acompanhado de
`docs/assets/nexus_btg_28092026_data.json` e do CSV de cenários.
Transferências publicadas permanecem fixas; quatro origens dependem de
hipóteses explícitas. O bloco Outros é aproximado pela Samara e isso
é declarado ao lado do gráfico.

O modelo de presença usa uma tabela conjunta sintética e independência
entre voto e comparecimento dentro da célula. Não produz microdados
recuperados nem estimativa validada de comparecimento individual.
54 cenários por turno, três testes adicionais para 60+ e limites de
identificação por renda expõem a sensibilidade e a informação faltante.
Os cenários de presença não entram no agregador de renda.

## Verificação visual

Com `docs` servido localmente na porta 4173, execute
`python3 analysis/nexus_btg_28092026/visual-qa.py`.
O teste verifica 108 combinações do simulador, links locais, fallback
sem JavaScript e larguras de 390 e 1440 pixels. Os arquivos `qa-*.png`
e `visual-qa.json` registram o resultado.
