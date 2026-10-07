# Instruções para os agentes de pesquisa (Senado 2027 diante do STF)

Leia antes de tudo `analysis/senado_2027/CONTRATO.md` (esquema dos JSON e régua) e
`analysis/senado_2027/elenco.json` (as 81 cadeiras). Os quatro relatórios de origem estão em
`analysis/senado_2027/relatorios_origem/` (01_claude.md é o primeiro e serve de base; 02_gemini.md,
03_chatgpt.md e 04_perplexity.txt foram feitos a partir dele buscando complementos; o 04 tem uma
lista de 645 URLs no fim, muitas úteis como pista). Use `grep -n "<nome>"` nos quatro para
levantar tudo o que já foi dito sobre cada senador antes de pesquisar.

## Tarefa
Para cada senador da sua lista, gravar `analysis/senado_2027/senadores/<slug>.json` exatamente
no esquema da seção 2 do contrato (slugs no elenco). Para cada um:
1. Levante todos os casos judiciais que atingem o senador em pessoa (STF, STJ, TSE, TRF,
   primeira instância, PF, MP): inquéritos, indiciamentos, denúncias, ações penais, condenações,
   processos eleitorais, arquivamentos, absolvições. Processo contra parente, assessor, suplente
   ou aliado entra no máximo como `citado`, com o vínculo explicado.
2. Para cada caso: estágio atual (o mais recente que você consiga provar), foro, relator, datas,
   resumo factual, manifestação da defesa (obrigatória quando existir), fontes com URL, veículo,
   data, título e `acesso` (`pagina` se abriu a URL; `trecho_de_busca` se só leu o resumo do
   buscador; `relatorio_anterior` se veio dos relatórios e não reabriu). `confianca` conforme o
   contrato. `nos_relatorios` diz em quais dos quatro relatórios o caso aparece.
3. Levante os sinais de contrapeso: declaração pró ou contra impeachment de ministro (listas do
   Metrópoles 05/10/2026, Gazeta do Povo, JOTA, CNN/Daniel Rittner, Ranking dos Políticos),
   assinatura de pedido de impeachment ou de CPI contra ministros, ação judicial contra ministro,
   voto nominal na PEC 8/2021 (22/11/2023, lista nominal da CNN Brasil e do Senado), projetos ou
   PECs contra o STF, "dialogável" segundo ministros (coluna de Bela Megale, O Globo, 06/10/2026),
   defesa pública do STF, alinhamento declarado com o governo Lula. Cada sinal com fonte.
4. `scores_anteriores`: copie os K e C que cada relatório deu ao senador (null onde o relatório
   não dá número). ChatGPT dá K, C-IMP e P-PEC. Perplexity não dá números.
5. `nota_editorial`: 2 a 4 frases em português corrente, sem travessão, que a página usa na ficha.
6. Resolva conflitos entre os relatórios pela fonte primária mais recente e registre no seu
   relatório final: "Relatório X dizia A; relatório Y dizia B; fonte Z confirma B em <data>".

## Regras
- Ferramentas: WebSearch e WebFetch. G1, Folha e UOL bloqueiam o WebFetch e a busca por domínio
  devolve zero: resultado nulo não prova ausência. Prefira STF (noticias.stf.jus.br,
  portal.stf.jus.br), Agência Brasil, Agência Senado, Agência Câmara, PGR, PF, TSE, Poder360,
  Metrópoles, CNN Brasil, Gazeta do Povo, JOTA, ConJur, Migalhas, Estadão, Veja, O Globo, Correio
  Braziliense, Congresso em Foco, O Antagonista, Revista Oeste, Brasil de Fato, veículos regionais.
- Nunca invente URL, data, número de inquérito ou estágio. Se não conseguir provar, grave o que
  os relatórios dizem com `acesso: relatorio_anterior` e `confianca: baixa`, e diga isso no resumo.
- Presunção de inocência: "investigado", "indiciado", "réu", "condenado" exatamente como na fonte.
  "Nada localizado" nunca vira "ficha limpa". Toda acusação vem com a versão da defesa.
- Sem travessão (`—`) em nenhum campo de texto. Use vírgula, dois-pontos ou ponto.
- Datas em ISO (AAAA-MM-DD). Texto em português do Brasil.
- Grave um arquivo por senador, JSON válido, UTF-8, indentação de 1 espaço, `ensure_ascii=False`.
  Valide com `python3 -c "import json,sys;json.load(open(sys.argv[1]))" <arquivo>`.
- Hoje é 07/10/2026. O 1º turno foi em 04/10/2026; o 2º turno (presidente e 7 estados) será em
  25/10/2026. Flávio Bolsonaro teve 47,03% e Lula 45,16% no 1º turno.
- Orçamento: até 10 buscas e 10 fetches por senador com caso conhecido, até 4 e 3 para senador
  sem caso conhecido nos relatórios (busque "<nome> STF inquérito", "<nome> investigado",
  "<nome> impeachment Moraes", "<nome> PEC 8"). Não gaste tempo em biografia.

## Relatório final (texto, para o orquestrador)
1. Lista dos arquivos gravados.
2. Conflitos entre relatórios e como resolveu, um por linha.
3. Fatos novos que nenhum dos quatro relatórios trazia.
4. O que ficou sem verificação (caso, senador, motivo).
5. Observações sobre fontes que bloquearam ou falharam.
