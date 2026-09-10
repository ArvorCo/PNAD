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

`lula`, `flavio`, `caiado`, `zema`, `cury`, `renan_santos`, `marcal`, `samara`, `outros`, `branco_nulo`, `indecisos`.
Quando o instituto publica um único número de não escolha, usar `branco_nulo` e deixar `indecisos` fora.
Candidatos com 1% ou menos podem ser somados em `outros`. As chaves de `publicado` precisam existir em `opcoes`.

## Regras de transcrição

1. Copiar exatamente o que está no PDF, sem arredondar nem corrigir. Célula em branco vira `0` e a nota registra.
2. O cruzamento precisa recompor o placar publicado: rodar `python3 scripts/reponderacao-pnad.py calcular` e conferir o resíduo impresso. Acima de 1,5 pp, procurar o erro (base errada, coluna trocada, perfil ponderado versus não ponderado) antes de gravar.
3. Se o instituto publica o perfil ponderado da amostra e também bases não ponderadas, testar os dois e ficar com o que recompõe melhor; registrar em `renda.nota`.
4. Preferir o cenário estimulado principal (o que o instituto usa na manchete). Registrar em `nota` qual cenário foi usado.
5. Segundo turno: Lula × Flávio Bolsonaro. Outros pares não entram.
