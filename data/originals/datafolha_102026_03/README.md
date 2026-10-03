# Datafolha · Presidência 2026 · campo de 02 e 03/10/2026

Registro BR-01708/2026, 4.006 entrevistas presenciais em 122 municípios, margem de 2 pontos, contratada pela Folha de S.Paulo e pela TV Globo. Divulgada em 03/10/2026, véspera do 1º turno.

**A íntegra em PDF não estava publicada** na consulta de 03/10/2026 (cerca de 19h10). A transcrição vem do painel do contratante, o G1, cuja API pública devolve a série completa com estratos:

- `g1_estimulada_1t.json`: 1º turno estimulado (`ESTIMULADA-PRE-002`), total e estratos, inclusive renda em três faixas.
- `g1_segundo_turno.json`: Lula × Flávio (`SEGTURNO-PRE-001`), total e estratos, inclusive renda.
- `g1_espontanea.json`: espontânea (`ESPONTANEA-PRE-001`).
- `g1_painel.html`: a página do painel, onde estão os códigos das perguntas. Votos válidos (`VTSVALIDOS-PRE-003`) devolveu 404 na API.
- `materia_folha.html` e `materia_folha.txt`: matéria da Folha com registro, campo, n e margem.

Os valores do painel vêm em fração arredondada ao inteiro percentual e sem bases. Controle: o mesmo painel reproduz célula a célula o PDF da onda de 01/10 (`../datafolha_102026_02/relatorio.pdf`). URLs, bytes, SHA-256 e hora da captura em `fonte.json`.

Ficha do agregador: `analysis/reponderacao/pesquisas/datafolha_2026-10-03.json`. O perfil de renda é hipótese explícita (bases ponderadas da onda de 01/10). Quando o PDF sair, arquivar como `relatorio.pdf`, conferir os números contra o painel e trocar o perfil pelo publicado.
