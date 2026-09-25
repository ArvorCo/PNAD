# Atualização documental de 24/09/2026

Pesquisa no Poder360 e nas páginas dos institutos, com relatórios preservados, páginas de origem e SHA-256 em [verificacao.json](verificacao.json). As datas de divulgação permanecem separadas das datas de obtenção dos documentos.

| Instituto | Divulgação | Situação nesta atualização |
| --- | --- | --- |
| AtlasIntel | 23/09 | PDF arquivado; 1º turno integrado. Sem cruzamento de renda do 2º turno. |
| Futura | 24/09 | PDF arquivado; placares e perfil disponíveis, sem voto por renda. Sem ajuste. |
| Real Time Big Data | 24/09 | PDF arquivado; 1º turno integrado. Sem cruzamento de renda do 2º turno. |
| PoderData | 24/09 | PDF e gráficos da publicação arquivados; ambos os turnos integrados. O cruzamento do 2º turno está no gráfico complementar. |
| Palver | 24/09 | PDF e tabelas exatas do Explorer arquivados; ambos os turnos integrados. Margens ponderadas recuperadas por sistema linear e conferidas pelo tamanho efetivo. |
| Quaest nacional | 21/09 | Íntegra do instituto substitui a fonte parcial; ambos os turnos e perfil efetivamente publicado integrados, sem criar uma nova onda. |
| Veritá | 24/09 | PDF nacional consolidado de 27 amostras estaduais arquivado. Falta perfil ponderado nacional de renda; cenário inclui Marçal. Sem ajuste. |
| Datafolha | 24/09 | Nova divulgação cadastrada; relatório e cruzamentos desta onda ainda não localizados. Sem ajuste. |
| American Analytics | Prevista para 21/09 | O PDF do Poder360 é uma matéria de anúncio, com resultados antigos. Preservado como evidência da limitação, sem atribuir esses resultados à onda de setembro. |
| BTG/Nexus | 21/09 | Já integrado. Íntegra preservada em `data/originals/nexus_092026_21/`. |
| Gerp / MDA | 17/09 / 15/09 | Já integrados; nenhuma onda nacional posterior confirmada na consulta. |

## Arquivos recebidos do usuário

As cinco estaduais Quaest de SP, RJ, MG, PE e DF estão em [data/pesquisas/quaest/2026-09-23](../../../data/pesquisas/quaest/2026-09-23/README.md), com manifesto e hashes. Não entram nas médias nacionais.

A nacional recebida como `Quaest_23092026.pdf` corresponde à divulgação de **21/09**, com 247 páginas. Foi preservada uma única cópia, idêntica ao documento público do instituto: [relatorio-instituto.pdf](../../../data/originals/quaest_092026_24/relatorio-instituto.pdf). Os arquivos em Downloads foram mantidos.

## Reprodução

Execute na raiz do repositório, com os arquivos do Git LFS disponíveis:

```sh
python3 scripts/pesquisas-240926-renda.py
python3 scripts/reponderacao-pnad.py calcular --hoje 2026-09-24
python3 scripts/reponderacao-build.py --skip-home
python3 scripts/social-cards.py --only reponderacao_pnad
python3 -m pytest -q
```

O script extrai as tabelas nativas, documenta as transcrições de gráficos com página de origem e recompõe oito placares elegíveis por renda e por sexo, independentemente. Mantém a regra de ajuste ancorado ao placar publicado e as tolerâncias de arredondamento do agregador. No PoderData, a recomposição de Flávio por renda diverge 1,47 ponto no primeiro turno; o resíduo permanece explícito e não é tratado como efeito da PNAD.

A média móvel de sete dias em 24/09 usa seis institutos no primeiro turno e quatro no segundo, com os mesmos participantes nas versões publicada e reponderada. O ajuste é sensibilidade de uma margem, não previsão nem voto corrigido.

Fontes complementares: [links do Poder360](poder360-links.json), [matérias e anexos](fontes-web.json), [downloads iniciais](downloads.json), [margens da Palver](palver-margens.json). Os PDFs são abrangidos pela regra de Git LFS do repositório.
