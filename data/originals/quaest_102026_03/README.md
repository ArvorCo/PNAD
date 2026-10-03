# Quaest · Presidência 2026 · campo de 02 e 03/10/2026

Registro BR-02197/2026, 3.702 eleitores de 16 anos ou mais, margem de 2 pontos com 95% de confiança, contratada pela Globo e pelo jornal O Globo. Divulgada em 03/10/2026, véspera do 1º turno. Metadados lidos nas três matérias do G1 (texto idêntico nas três).

**A íntegra em PDF não estava publicada** na consulta de 03/10/2026 (cerca de 19h35, horário de Brasília): a lista de mídia da Quaest (`wp-json/wp/v2/media`) tinha como último relatório presidencial nacional o `QUAEST+6+PRESIDENCIAL+28+09.pdf`. Os números vêm do painel do contratante, o G1, cuja API pública devolve a série completa com estratos:

- `g1_estimulada_1t.json`: 1º turno estimulado (`ESTIMULADA-PRE-003`), votos totais e estratos, inclusive renda em três faixas. Às 19h29 a série ainda terminava em 28/09; a coluna de 03/10 apareceu às 19h34.
- `g1_segundo_turno.json`: Lula × Flávio (`SEGTURNO-PRE-001`, rotulado "Segundo Turno - Cenário 1", único cenário de 2º turno listado no painel), total e estratos.
- `g1_aprovacao.json`: aprovação do governo (`APROVACAO-PRE-001`).
- `g1_painel.html`: a página do painel, onde estão os códigos das perguntas. Votos válidos (`VTSVALIDOS-PRE-001`) devolveu 404 na API.
- `materia_1t`, `materia_2t`, `materia_aprovacao` (`.html` e `.txt`): matérias do G1 com placar, registro, campo, n e margem.

Os valores do painel vêm em fração arredondada ao inteiro percentual e sem bases. Controles: o mesmo painel reproduz célula a célula, na coluna 28/09, o PDF da onda de 24 a 27/09 (`../quaest_092026_29/relatorio.pdf`, pp. 18, 24, 32 e 37), e o total do painel em 03/10 coincide com os votos totais das matérias. Os votos válidos da matéria (Lula 46, Flávio 45) saem do modelo de eleitor provável da Quaest, não da renormalização dos totais, e não entram no motor. URLs, bytes, SHA-256 e hora da captura em `fonte.json`.

Ficha do agregador: `analysis/reponderacao/pesquisas/quaest_2026-10-03.json`, gerada por `python3 scripts/quaest-031026-g1.py`. O perfil de renda é hipótese explícita (31/42/27, perfil da onda de 27/09, PDF p. 204). Quando o PDF sair, arquivar como `relatorio.pdf`, conferir os números contra o painel e trocar o perfil pelo publicado.
