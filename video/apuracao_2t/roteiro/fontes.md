# Fontes externas do roteiro "A noite do 2º turno"

Fatos que não saem de `src/dados/apuracao_2t.json`. Cada entrada traz URL, data de acesso e o
trecho que sustenta a frase narrada. As páginas foram arquivadas pelo levantamento da noite em
`analysis/apuracao_2t_2026/noticias_fontes/` (SHA-256 em `analysis/apuracao_2t_2026/noticias_noite.json`).
Acesso de todas: 25/10/2026, entre 22h e 22h45 de Brasília.

## stf-rcl-101673

- STF (Notícias), "STF prorroga votação até as 19h em locais onde urnas permaneceram abertas após as 17h":
  https://noticias.stf.jus.br/postsnoticias/stf-prorroga-votacao-ate-as-19h-em-locais-onde-urnas-permaneceram-abertas-apos-as-17h/
- Arquivo: `noticias_fontes/stf_prorroga.html`.
- Trecho (resumo): o ministro Cristiano Zanin, na Reclamação 101673 da Coligação Brasil Pronto Pra
  Mais (Salvador, Feira de Santana e Lauro de Freitas; ADPF 1013), estendeu a votação até 19h onde
  as urnas não fecharam às 17h. Hora da decisão: 17h03 segundo Poder360 e O Globo (Lupa diz 16h57
  e Estadão 17h01); por isso o roteiro diz "por volta das dezessete e três".

## estadao-pge

- Estadão, "Antes de decisão de Zanin, Procuradoria-Geral Eleitoral defendeu manter votação até 17h":
  https://www.estadao.com.br/politica/eleicoes/antes-de-decisao-de-zanin-procuradoria-geral-eleitoral-defendeu-manter-votacao-ate-17h/
- Trecho (resumo): a PGE opinou por manter o fim da votação às 17h; o parecer chegou ao TSE às 17h01.

## ab-ajuste

- Agência Brasil, "Horário de votação ampliado será apenas onde urnas não foram fechadas" (18h08):
  https://agenciabrasil.ebc.com.br/justica/noticia/2026-10/horario-de-votacao-ampliado-sera-apenas-onde-urnas-nao-foram-fechadas
- Trecho (resumo): depois de o TSE informar que as urnas fecharam no horário oficial, Zanin
  reajustou a decisão para valer só para as seções ainda abertas.

## p360-17h49

- Poder360, "TSE avisou seções sobre prorrogação às 17h49":
  https://www.poder360.com.br/poder-eleicoes-2026/tse-avisou-secoes-sobre-prorrogacao-as-17h49/
- Trecho (resumo): o TSE avisou as seções às 17h49, 46 minutos após a decisão; urnas já
  fechadas não foram reabertas.

## ab-tresp-80

- Agência Brasil, "Em SP, 80% das urnas estavam encerradas quando votação foi prorrogada" (19h00):
  https://agenciabrasil.ebc.com.br/politica/noticia/2026-10/em-sp-80-das-urnas-estavam-encerradas-quando-votacao-foi-prorrogada
- G1 (mesma declaração, 18h17):
  https://g1.globo.com/sp/sao-paulo/eleicoes/2026/noticia/2026/10/25/presidente-do-tre-sp-afirma-que-so-recebeu-decisao-de-prorrogar-votacao-as-18h17-e-que-nao-houve-prejuizo-para-os-eleitores.ghtml
- Trecho (resumo): o presidente do TRE-SP disse que mais de 80% das seções do estado já estavam
  fechadas quando chegou o aviso oficial do STF, às 18h17. O Poder360 (22h00) registra outra fala,
  de que recebeu a decisão perto das 17h; o roteiro usa a da comunicação oficial e diz "diz ter".

## oglobo-pausa

- O Globo, "TSE pausa divulgação de resultados da eleição com 0,25% das urnas apuradas após Zanin estender votação até as 19h" (17h22):
  https://oglobo.globo.com/politica/eleicoes-2026/noticia/2026/10/25/tse-pausa-divulgacao-de-resultados-da-eleicao-com-025percent-das-urnas-apuradas-apos-zanin-estender-votacao-ate-as-19h.ghtml
- Agência Brasil, "TSE retoma contagem de votos em todo o país":
  https://agenciabrasil.ebc.com.br/justica/noticia/2026-10/tse-retoma-contagem-de-votos-em-todo-o-pais
- Trecho (resumo): o TSE confirmou que pausou a totalização e a divulgação por causa da decisão
  de Zanin, e retomou às 19h.

## abstencao-2006

- CNN Brasil, "Abstenção no 2º turno cai para 19,21%, menor índice desde 2006":
  https://www.cnnbrasil.com.br/eleicoes/abstencao-no-2o-turno-cai-para-1921-menor-indice-desde-2006/
- Poder360, "Abstenção fica em 19,21% no 2º turno, a menor desde 2006":
  https://www.poder360.com.br/poder-eleicoes-2026/abstencao-fica-em-1921-no-2o-turno-a-menor-desde-2006/
- Divergência registrada: o título do G1 fala em "menor desde 2010"; por isso o roteiro atribui a
  comparação à CNN e ao Poder360. O percentual narrado (19,22%) é o da versão final do dossiê.

## vinheta-encerramento

- Boletim final falado no ar pela casa, gerado com os dados lidos às 21:23:51 de Brasília
  (`apuracao/data/vinheta/encerramento.txt` e `encerramento.dados.json`, fora do git por serem
  dados da apuração local): "Para virar, Flávio precisaria de mais do que todos os votos que
  restam. Não há virada possível." Diferença no momento: 4.364.428 votos.
