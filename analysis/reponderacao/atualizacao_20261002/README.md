# Conferência documental de 02/10/2026

O agregador foi atualizado para 78 ondas reponderáveis de 11 institutos. Foram
arquivadas cinco íntegras e conferidos os 14 documentos do catálogo do Poder360
de 02/10. Datafolha e Indexa têm resumos nesse catálogo; os cálculos usam suas
íntegras de 68 e 94 páginas, respectivamente. Versões distintas foram preservadas
e cópias idênticas remetem ao arquivo canônico em `catalogo-fontes.json`.

| Pesquisa, divulgação | Documento | O que mudou |
| --- | --- | --- |
| Datafolha, 01/10 | Íntegra de 68 páginas publicada em 02/10 | Dois turnos integrados; 18 tabelas do anexo extraídas automaticamente |
| Real Time Big Data, 01/10 | 65 páginas | Primeiro turno integrado; segundo sem voto por renda |
| Indexa/Broadcast, 30/09 | 94 páginas, imagens | Dois turnos integrados; OCR integral e transcrição visual com controle por gênero |
| Futura, 30/09 | 46 páginas | Mesma ficha completada: n=2.000, CATI, campo 25–29/09; continua sem voto por renda |
| Vox Brasil, 02/10 | 14 páginas | Nova ficha documental, sem voto por renda e fora dos ajustes |
| Alfa/TMC, 24/09 | Publicações do contratante | Lacuna do inventário preenchida; íntegra não localizada, sem ajuste |

Os PDFs, seus textos e metadados ficam em `data/originals/<instituto>_<MMAAAA>_<dia>/`.
O JSON de cada pesquisa permanece em `analysis/reponderacao/pesquisas/`.
`downloads.json` registra as cinco aquisições; `auditoria.json` registra fontes,
hashes, cinco cruzamentos novos e sete controles independentes.

## Contas verificadas

Valores na ordem Lula × Flávio. Régua principal: PNADC anual 2025, visita 1,
pessoas 16+, renda domiciliar efetiva, com o delta ancorado no placar publicado.

| Pesquisa | Turno | Publicado | Reponderado |
| --- | --- | --- | --- |
| Datafolha | 1º | 42 × 38 | 39,938 × 40,850 |
| Datafolha | 2º | 48 × 45 | 45,226 × 48,187 |
| Real Time | 1º | 43 × 39 | 40,337 × 41,561 |
| Indexa | 1º | 39 × 34 | 38,536 × 34,848 |
| Indexa | 2º | 43 × 42 | 42,480 × 42,916 |

A Datafolha usa as bases ponderadas de intenção de voto 1.209/856/344, somando
2.409; 97 dos 2.506 casos não aparecem na tabela de renda. Não usa bases de
motivação e não identifica o voto desses ausentes. Traços explícitos permanecem
no anexo e viram zero somente no cálculo, conforme o método existente.

A Real Time publica 1% em Outros, mas deixa uma célula desse grupo sem número.
A tabela parcial não foi renormalizada. Entra na série de líderes do primeiro
turno, mas fica fora do modelo de válidos, que exige todos os candidatos positivos.
A Indexa agrega não iria votar a branco/nulo nos totais e recortes, conservando
a mesma partição. Candidaturas com zero no total e sem coluna de renda continuam
sem células imputadas. Os perfis da Indexa e da Real Time não distinguem bruto
de ponderado, limitação registrada nas fichas.

Na janela 26/09–02/10, a média reponderada é 41,13 × 39,61 no primeiro turno
(oito casas) e 43,90 × 45,85 no segundo (seis). O modelo condicional de válidos,
PNAD mais comparecimento central, marca 44,4 / 42,2 / 13,4 no primeiro turno
(Lula / Flávio / demais, sete casas) e 49,0 / 51,0 no segundo (seis).
Sensibilidade e projeção condicional não identificam o resultado da eleição.

## Relatórios posteriores e pendências

A íntegra anterior da Datafolha, gerada em 28/09 e já integrada ao campo de
22–23/09, foi reconferida e ganhou metadados de integridade. Sua divulgação
continua em 24/09. A Futura também conserva divulgação e identificador originais.
Documentos recebidos depois não criam ondas ou renovam a janela de sete dias.

`varredura.json` registra as bibliotecas oficiais da Gerp e da Quaest, o catálogo
de relatórios, anúncios e limites da busca. DataTrends e França aparecem como
pendências de 02/10: resultados ou íntegra nacional não localizados na conferência.
Levantamentos estaduais e anúncios sem resultado ficam fora do cálculo.

## Reprodução e validação

```sh
python3 scripts/pesquisas-pdf-ocr.py data/originals/indexa_092026_30/relatorio.pdf
python3 scripts/pesquisas-021026-renda.py
python3 scripts/reponderacao-pnad.py calcular --hoje 2026-10-02
python3 scripts/reponderacao-build.py
python3 scripts/social-cards.py --only reponderacao_pnad
pytest -q
```

Validação: 489 testes passaram. Renderização e contraste: zero falhas no desktop
e no celular. Playwright conferiu três modos e cinco cenários nos dois turnos,
sem erros JavaScript, recursos locais ausentes ou overflow horizontal; o conteúdo
permanece visível sem JavaScript. Evidências visuais e registros de QA ficam em
`tmp/reponderacao_20261002/`, dentro do workspace e fora do versionamento.
