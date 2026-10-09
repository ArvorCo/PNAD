# Incorporação nacional de 09/10/2026

Primeiro envio: `2795993f`, redesenho das três rotas e documentação Vox,
publicado em GitHub Pages. A rodada seguinte acrescenta Atlas/Bloomberg.

- Fonte oficial: https://atlasintel.org/poll/brazil-national-2026-10-09
- Íntegra: `data/originals/atlas_102026_09/relatorio.pdf`, 20 páginas,
  SHA-256 `f730a1c0aec0f00e1be083e8aff4f53e1ee3fdd5294cdcd8a1ff4ee699801eb9`.
- Registro BR-03663/2026, 5.026 entrevistas, campo 03–08/10, divulgação 09/10.
- Conferência visual: perfil p. 5, total p. 7, válidos p. 8, cruzamentos p. 9.
  Perfil de renda 19,4/12,2/26,3/26,1/16,1%, normalizado pela soma 100,1%.
  Recomposição também por sexo e região; resíduo máximo 0,0844 pp.
- Placar válido publicado: Flávio 52,8% × Lula 47,2%. Troca apenas da margem
  de renda: 53,16% × 46,84%. Não separa branco/nulo de não sei.
- Campo misto: a onda recebe cálculo e entra na série descritiva, mas fica
  fora da central que exige início após 04/10. Sem recorte pós-urna publicado.
  A central mantém 55,32% × 44,68%, com presença relativa de Flávio +5%.
- Os cortes nominais de outubro usam a limitação de IPCA do motor existente:
  último índice arquivado 07/2026; não se extrapola inflação posterior.
- Agenda consultada identifica Atlas e Vox como nacionais e três entradas
  Igape estaduais. Vox já incorporada; Datafolha e PoderData são de 08/10,
  sem duplicação. Catálogos GERP, Palver e posts Quaest não mostraram nova
  onda nacional na consulta. Capturas, horário UTC e hashes em
  `data/originals/reponderacao_20261009/`. Isso delimita a busca, não prova
  ausência em outros canais.

O CI do primeiro envio apontou três arquivos fora do formato Black, um teste
que ainda chamava a cobertura pelo gerador antigo e duas datas de sitemap
anteriores ao commit. A rodada corrige esses pontos. O teste histórico de
17/09 agora fixa aquela referência; uma nova Atlas com renda não perpetua a
ausência de cruzamento das ondas anteriores.

QA do navegador: presets, parâmetros extremos, conservação das massas,
link e imagem PNG, motor arquivado, versão inexistente, âncoras antigas,
três larguras e JavaScript desligado. A ficha Atlas abre pela âncora; o link
publicado da versão `43b90fe501f43fcd` continua reproduzível. A versão atual
`0d389d59d46a9e09` registra a nova exclusão documental, sem alterar a central.

Validação: `pytest -q` — 2.010 passaram, 5 ignorados. Após especificar o
rótulo agregado da não escolha na ficha Atlas, os 46 testes pertinentes
passaram. `ruff check scripts/ docs/ tests/`, Black e verificação do sitemap
passaram; nenhuma alteração foi feita nos rascunhos de outras tarefas.
