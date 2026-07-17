# Atualização das minutas: mapa emenda → achado (pós-Quaest 07/2026)

Registro de trabalho da revisão jurídico-legislativa das duas peças da série de
auditorias (Projeto de Lei que altera a Lei 9.504/1997 e Minuta de Resolução que
altera a Res. TSE 23.600/2019). A redação original nasceu da 6ª rodada BTG/Nexus.
Esta rodada de emendas fecha as lacunas documentadas depois, pela auditoria
Genial/Quaest de julho e pela discussão pública com Felipe Nunes.

Fonte de verdade do texto normativo: `docs/nexus_btg_0726.html`, seções
`id="resolucao"` e `id="projeto-lei"` (o `docs/proposta.html` é gerado dali por
`python3 docs/build_proposta.py`). Texto integral também em
`data/pesquisas/quaest/propostas-regulatorias-2026.md`. Resumo no dossiê:
fragmento `docs/assets/quaest_0726_pl_update.html`.

Convenção: Fato = observação documental ou cálculo reproduzível; Inferência =
leitura mais compatível com os fatos; Hipótese = exige prova adicional.
Veredito da série, inalterado: prova de opacidade, não de fraude.

## Mapa: cada emenda e o achado que a motivou

| # | Emenda (Resolução) | Emenda (Projeto de Lei) | O que cobre | Achado motivador | Tipo |
|---|---|---|---|---|---|
| a | § 7º-Q | art. 33, inc. XVIII; art. 2º-E (md) | Matriz de transição entre cenários da mesma rodada (1º→2º turno) quando ambos são publicados, com base bruta e ponderada | A rodada divulga 1º e 2º turno como dois retratos e omite a migração de preferência que os liga | Fato |
| b | art. 10, § 4º; § 7º-J | art. 33, § 11; inc. X (já existente, reforçado) | Base não ponderada por subgrupo em todo recorte divulgado, inclusive peça gráfica e suplemento | Tabelas por sexo, idade, renda e região sem base não ponderada; recortes sem margem própria | Fato |
| c | § 7º-J ampliado | art. 33, inc. XIX; relatório item 10 (md) | Distribuição das entrevistas por dia da semana e faixa horária, duração média e mediana | Campo sexta→segunda nas duas rodadas, sem horário de coleta nem duração; é o que testaria filtro de porta e fadiga de instrumento (dossiê "campo") | Fato |
| d | § 7º-R | art. 33, § 6º-F; art. 2º-F (md) | Suplemento temático da mesma coleta é a mesma pesquisa, com topline integral; bloco diferido leva o rótulo "opinião medida antes de [fato]" | A Quaest separa temas em "recortes" divulgados depois para prolongar visibilidade; Nunes confirma a prática (publicação seletiva temporizada) | Fato |
| e | § 7º-O ampliado | art. 33, inc. XXII; art. 2º-G (md) | Estimativa por modelo (MRP, raking, pós-estratificação, imputação) rotulada como projeção de modelo, com premissas e código | A ficha técnica declara pós-estratificação por rake/MrP, sem especificação nem código | Fato |
| f | § 7º-V; art. 2º-A (md) | art. 33, § 16 | Instrumento final sem placeholder ou resíduo de template, com hash próprio; capa, rodada e projeto conferidos e coerentes | O questionário de julho traz 26 resíduos de template e o cabeçalho da rodada anterior (capa errada) | Fato |
| g | § 7º-S; art. 10, § 6º (md) | art. 33, inc. XX, § 15; § 12 (md) | Pergunta informativa rotulada "opinião após estímulo informacional" e percentual de quem declarou desconhecer o fato até ali ("ficou sabendo agora") | Perguntas que informam o eleitor de um fato moldam a resposta seguinte; sem o percentual, o efeito fica invisível no número | Inferência |
| h | § 7º-T; art. 10, § 10 (md) | art. 33, inc. XXI | Simetria de enunciado em confrontos de versões (acusação e resposta) com revisão de equilíbrio documentada | Preâmbulo acusatório sobre Flávio/Vorcaro sem simetria com o bloco Jaques Wagner/Master, que já vinha com negação explícita | Fato |
| i | § 7º-U; art. 2º-D (md) | art. 33, § 17 | Coleta de CPF, rede social, contato ou geolocalização vedada ou justificada com finalidade, base legal e dissociação comprovada | Formulário de julho passa a solicitar CPF e Instagram | Fato |
| j | art. 10, § 4º; § 11 (PL); art. 10, § 9º (md) | art. 33, § 11 | NS/NR nunca removidos de gráfico sem o valor na própria peça | Não sabe, não respondeu e recusa desaparecem de peças gráficas (padrão observado na série, ecoando o achado Atlas) | Fato |
| k | § 7º-N ampliado | art. 34 ampliado; art. 34, § 9º (md) | Acesso de pesquisador, instituição científica e auditor credenciado ao detalhamento de maior valor em ambiente seguro, sob termo de compromisso | Nunes trata microdados como ativo comercial que remunera a empresa; ajuste que preserva o valor comercial sem negar o núcleo replicável | Inferência |

### Notas de legística

- Numeração preservada. Nenhum § ou inciso já citado em outra página foi
  renumerado; todas as emendas são acréscimos. No PL, o cabeçalho do art. 1º
  passou de "incisos VIII a XVII e §§ 6º a 14" para "incisos VIII a XXII e §§ 6º
  a 17", e o rol de sanção do § 14 passou a alcançar o § 6º-F e os §§ 15 a 17,
  preservando a exclusão deliberada dos §§ 6º-C a 6º-E (dever de terceiro, cuja
  sanção segue no art. 33, § 3º).
- Separadores. Os incisos novos usam dois-pontos, e não travessão, por padrão da
  casa; os incisos antigos permanecem como estavam.
- Duas encarnações do texto integral divergem na numeração desde a origem
  (`nexus_btg_0726.html` usa a família § 6º/§ 7º; a md usa a família § 5º/art.
  2º-A). As emendas foram aplicadas em cada uma no seu próprio esquema; a
  substância é idêntica.
- A tabela "o que muda na prática" em `build_proposta.py` não foi tocada: ela já
  era um resumo não exaustivo e continua correta; as novas emendas entram no
  `proposta.html` por extração automática das seções do laudo.

## Post para thread (até 2000 caracteres, sem travessões)

Atualizei as duas minutas da série de auditorias, a lei e a resolução do TSE, com dez emendas. Cada uma tem um achado da auditoria Genial/Quaest de julho, e do debate público com Felipe Nunes, atrás dela.

A pesquisa publica 1º e 2º turno como dois retratos e some com a migração de voto entre eles. Agora a matriz de transição sai junto. O campo foi de sexta a segunda nas duas rodadas, sem horário nem duração declarados, justamente o que testaria filtro de porta e fadiga do questionário. Agora a distribuição por dia, hora e a duração média entram no registro.

A Quaest separa temas em "recortes" divulgados depois, para esticar a manchete. Agora o suplemento da mesma coleta é a mesma pesquisa: topline integral, e bloco guardado leva o rótulo "opinião medida antes do fato". A ficha técnica diz pós-estratificação por rake e MrP, sem código: agora estimativa de modelo é rotulada projeção de modelo, com specs. O questionário de julho trazia 26 resíduos de template e a capa da rodada anterior: agora a versão final tem hash próprio e capa, rodada e projeto conferidos.

Pergunta que informa o eleitor de um fato molda a resposta: agora vem rotulada, com o percentual de quem ficou sabendo ali. O preâmbulo acusatório sobre Flávio e Vorcaro não tinha simetria com o bloco Jaques Wagner e Master: agora confronto de versões exige carga equivalente e revisão registrada. O formulário passou a pedir CPF e Instagram: agora identificador forte só com base legal e dissociação. E o não sabe, não respondeu e recusa nunca mais saem do gráfico sem o valor no slide.

Sobre o argumento do Felipe, microdado como ativo comercial: a carência responde, e o acesso de pesquisador credenciado em ambiente seguro, sob termo de compromisso, preserva o valor comercial sem negar a reprodução do resultado.

O veredito segue o mesmo: prova de opacidade, não de fraude. O número sai com a prova. Texto aberto em brasil.arvor.co/proposta.html.
