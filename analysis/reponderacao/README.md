# Agregador Arvor: manifesto de pesquisas

Uma pesquisa, um arquivo JSON em `pesquisas/<instituto>_<AAAA-MM-DD do fim do campo>.json`.
Exemplo completo: `pesquisas/datafolha_2026-08-19.json`. O motor é `scripts/reponderacao-pnad.py`.

## Campos

| Campo | Obrigatório | Conteúdo |
|---|---|---|
| `id` | sim | igual ao nome do arquivo sem `.json` |
| `instituto` | sim | nome curto e estável: `Datafolha`, `Quaest`, `AtlasIntel`, `Nexus`, `PoderData`, `Veritá`, `Gerp`, `Vox Brasil`, `Meio/Ideia`, `Real Time Big Data`, `Paraná Pesquisas`, `Futura` |
| `contratante` | sim | quem pagou, como está no registro |
| `registro_tse` | sim | `BR-0XXXX/2026`; `null` se não localizado, com o motivo em `notas` |
| `campo` | sim | `{"inicio": "AAAA-MM-DD", "fim": "AAAA-MM-DD"}` |
| `divulgacao` | sim | data de divulgação |
| `n` | sim | entrevistas |
| `metodo` | sim | `presencial`, `telefônico`, `online`, `misto` (com detalhe curto) |
| `fonte` | sim | `{"pdf": "caminho no repo", "url": "link público ou null", "paginas": {"perfil_renda": n, "1t_renda": n, "2t_renda": n}}` (página do PDF, contada a partir de 1) |
| `dossie` | não | arquivo em `docs/` quando a casa já auditou a onda |
| `renda.unidade` | sim | `salarios_minimos` (faixas em múltiplos do salário mínimo) ou `reais_nominais` (faixas em R$ do cartão) |
| `renda.ano_referencia` | sim se SM | ano do salário mínimo do cartão (2026 = R$ 1.621; 2025 = R$ 1.518; 2024 = R$ 1.412). Se o cartão traz reais, confira de que ano são os valores |
| `renda.mes_precos` | não | `AAAAMM` dos preços do cartão quando for `reais_nominais`; padrão é o mês do fim do campo |
| `renda.faixas` | sim | lista `{"rotulo": "...", "max": limite superior}`; a última tem `"max": null`. Em SM o `max` é o múltiplo (2, 5, 10); em reais é o valor em R$ |
| `renda.bases` ou `renda.amostra_pct` | sim, um dos dois | `bases`: entrevistados por faixa (não ponderado) quando o relatório dá bases; `amostra_pct`: perfil da amostra em % por faixa. Quem não declara renda fica fora (o motor renormaliza) |
| `renda.nota` | não | como a renda foi perguntada, se a base é ponderada, o que ficou de fora |
| `publicado` | sim | `{"2t": {...}, "1t": {...}}`, placar nacional publicado, em % |
| `cruzamentos` | sim | por turno: `{"opcoes": [...], "linhas": [[...], ...], "nota": "..."}`; uma linha por faixa de renda, na mesma ordem de `renda.faixas`, cada linha na ordem de `opcoes` |
| `ignorar` | não | `true` quando não há cruzamento por renda; então preencher `motivo` e ainda assim `publicado` |
| `notas` | não | qualquer ressalva |

## Chaves das opções (usar sempre estas)

`lula`, `flavio`, `caiado`, `zema`, `cury`, `renan_santos`, `marcal`, `samara`, `clariana`, `grassi`, `rui`, `edmilson`, `hertz`, `ciro`, `aldo`, `outros`, `branco_nulo`, `indecisos`.
Quando o instituto publica um único número de não escolha, usar `branco_nulo` e deixar `indecisos` fora.
Preservar os candidatos individualmente sempre que o cruzamento permitir: agregar em `outros` impede a separação editorial dos grupos. Nomes sem cruzamento podem constar em `publicado`, mas não recebem reponderação nem são preenchidos com zero.

## Regras de transcrição

1. Copiar exatamente o que está no PDF, sem arredondar nem corrigir. Célula em branco vira `0` e a nota registra.
2. O cruzamento precisa recompor o placar publicado: rodar `python3 scripts/reponderacao-pnad.py calcular` e conferir o resíduo impresso. Acima de 1,5 pp, procurar o erro (base errada, coluna trocada, perfil ponderado versus não ponderado) antes de gravar.
3. Se o instituto publica o perfil ponderado da amostra e também bases não ponderadas, testar os dois e ficar com o que recompõe melhor; registrar em `renda.nota`.
4. Usar cenário estimulado **sem Marçal**, com seu próprio placar e seu próprio cruzamento de renda. Sem alternativa documentada, excluir aquele primeiro turno, preservando o segundo. Nunca remover apenas o voto de Marçal ou redistribuí-lo.
5. Segundo turno: Lula × Flávio Bolsonaro. Outros pares não entram.

## Seleção e grupos do primeiro turno (18/09/2026)

`scripts/reponderacao-cenarios.py` documenta as alternativas transcritas, com páginas físicas do PDF: Datafolha agosto (36–37), Real Time setembro (15/18), Quaest 02/09 (25/31), Quaest 07/09 (26/32) e Gerp maio (13/14). Também individualiza os menores da situação B do Datafolha 03/09 (37–38), sem alterar Lula ou Flávio. Os manifestos originais não são sobrescritos. O JSON gerado registra `selecao_1t` e conserva o resultado anterior em `turnos_arquivados`, fora de médias, séries e CSV corrente. Dossiês históricos podem consultar esse arquivo explicitamente.

Marçal também está dentro de `outros` na MDA de 15/09: sua exclusão não pode depender apenas da chave individual `marcal`. Ao cadastrar uma nova onda, conferir a lista completa do cenário no relatório.

`scripts/reponderacao-grupos.py` soma as candidaturas dentro de cada onda e depois aplica a mesma meia-vida de 14 dias aos dois grupos:

- **Outros (centro-direita), cinza:** Zema, Augusto Cury, Ronaldo Caiado, Renan Santos e Clariana Barão.
- **Outros (esquerda + nanicos), preto:** Samara, Rui Costa Pimenta, Edmilson Costa, Hertz Dias e Wilson Grassi. A inclusão de Grassi é no residual de nanicos, não uma atribuição de posição de esquerda.

Classificação editorial aprovada pelo responsável pelo projeto. A inclusão de Clariana considera suas [propostas econômicas](https://clarianabarao.com.br/propostas); a manutenção de Grassi no residual considera a pauta da candidatura e a orientação partidária descritas no [perfil publicado pela Band](https://www.band.com.br/politica/eleicoes/eleicoes-2026-conheca-as-propostas-e-o-perfil-de-wilson-grassi-democrata).

Os grupos só usam ondas em que a divisão por renda é identificável. `Outros` indivisível ou candidato sem linha de renda não vira zero: nem mesmo um total publicado de 0% permite inferir zeros em cada faixa. Por isso, Atlas 17/09 entra na curva de Lula/Flávio, mas não nas curvas dos grupos. Na referência de 17/09, a cobertura dos grupos é de quatro ondas (Datafolha 19/08, 02/09 e 10/09; Quaest 01/09), de dois institutos; último campo em 10/09. As quatro linhas do gráfico não são uma partição somável, pois a cobertura dos líderes é mais ampla.

Reprodução:

```sh
python3 scripts/reponderacao-pnad.py calcular --hoje 2026-09-17
python3 scripts/reponderacao-build.py
pytest -q
```

A página publica cobertura, exclusões e seleção por onda. `docs/assets/reponderacao_grupos_1t.csv` contém as somas publicadas e reponderadas por grupo e onda.
