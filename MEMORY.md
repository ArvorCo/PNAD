# PNAD · memória do projeto

## Regra canônica de workspace

- Este projeto vive em `~/arvor/PNAD`. Esta é a única árvore canônica e gravável.
- `~/clawd/projects/PNAD` é um espelho do vault mantido por processos de replicação. Tratar como **read-only**.
- Nunca criar, editar, gerar, copiar ou manter artefatos do PNAD em `~/clawd/projects/PNAD`.
- Relatórios, fontes, dados, scripts, testes, imagens e arquivos temporários do projeto devem nascer e permanecer em `~/arvor/PNAD`.

## Quaest nacional · agosto de 2026

- Dossiê público: `docs/quaest_082026.html`, registro TSE BR-06591/2026.
- Fontes: `data/pesquisas/quaest/2026-08/`. O CSV `detalhes-demograficos-cidade.csv` é um export do Google Analytics sem relação com a pesquisa e está excluído da análise.
- Pipeline: `scripts/quaest-august-audit.py` gera `docs/assets/quaest_082026_data.json`, `docs/assets/quaest_082026_territory.json` e `quaest_bairros_0826.csv`.
- Resultado: primeiro turno 39 × 30, gap 12→9; segundo 44 × 39, gap 8→5. Deff 6,18 seria necessário para zerar o primeiro turno; deff 1,58 basta no segundo.
- Questionário: 109 itens, 39 páginas, promessa de 20 minutos, 28 resíduos de template. O relatório publica 58 itens e omite 51, incluindo Q108–109 de validação eleitoral e Q83–98 de confiança.
- Amostra: sexo, idade e região muito próximos do TSE. A faixa até 2 SM fica 4,44 pp abaixo da PNAD anual 2025; a sensibilidade marginal amplia o gap Lula–Flávio em 1,17 pp.
- Corte etário revalidado no CSV anual: todas as idades 37,046/38,713/24,241; 16+ 35,440/39,231/25,329; 17+ 35,347/39,257/25,396. O relatório usa corretamente `V2009 >= 16`.
- Território julho→agosto: 22 municípios comuns, 9 pares município+bairro e zero setores censitários idênticos entre 334 + 334.
- Linguagem pública: não usar segunda pessoa nem apartes originados da conversa de produção. A comparação Quaest × PNAD usa barras paralelas responsivas, escala 0–50%, diferença e IC 95% separados.
- Card social `quaest_082026` integra o manifesto único; o hub passa de 11 para 12 auditorias.
- Limite editorial: análise pública, técnica e agregada dos pontos fortes e fracos de candidatos; não produzir microtargeting ou persuasão política individual.
