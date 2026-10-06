# QA visual do dossiê da apuração do 1º turno (05/10/2026)

Página: `docs/apuracao_1o_turno_2026.html` servida em `http://localhost:4175` (Playwright/Chromium, `device_scale_factor` 1).
Larguras: 1440, 1024 e 390 px. 69 `<figure>`: 63 figuras de dados com `data-fig` e 6 prints da galeria do capítulo 15 (dentro de `<details>` fechado, sem defeito).
Capturas por elemento (3 larguras e cada estado `data-alt` em 1440): `/private/tmp/claude-501/-Users-leonardodias-arvor-PNAD/3ce2ab50-1f54-441f-be09-acf59c1e5268/scratchpad/qa-visual/<nome>-<largura>[-alt-<chave>].png`. Não ficaram em `analysis/apuracao_2026/qa-visual/` porque o `.gitignore` só cobre `analysis/apuracao_2026/qa-*.png`, não a subpasta.
Scripts de medição: `qa_visual.py`, `alt2.py`, `sortp.py`, `ovl_any.js` na mesma pasta temporária.

Fora do escopo, como pedido: rótulos longos cortados em `clusters_regiao` e a tabela de Registro em `modelo_urna_zona`.

## O que passou sem defeito

- Console: zero erro e zero aviso nas três larguras. Página sem rolagem lateral (scrollWidth = largura da janela nas três).
- Nenhuma `<figure class="pendente">`. Nenhum "undefined", "NaN", "None", "null", "nan" ou "Infinity" no texto da página nem nas fichas. Toda figura de dados tem `figcaption` preenchida.
- Fichas: três alvos `.hit` (primeiro, meio, último) em cada figura aparecem com texto e somem no `pointerleave`, nas três larguras. As duas falhas aparentes em 390 (`fechamento_regioes`, `fechamento_voto_lula`) eram do teste: o centro do alvo caía fora do trecho visível da rolagem interna. As figuras de dispersão e mapa por vizinho mais próximo (`svg[data-near]`) não têm `.hit` por desenho.
- Botões `data-alt`: os 93 estados das 22 figuras com alternância trocam o SVG (hash do `outerHTML` muda) e nenhum deixa texto fora da viewBox além dos dois casos da tabela.
- Texto SVG abaixo de 11 px em 1440: nenhum.
- Os "elementos de área zero" acusados em `dispersao_municipios`, `terceira_via_mapa`, `reguas_divergencia_mapa`, `nulo_2022_municipios`, `fechamento_persistencia` e `clusters_secoes` são pontos desenhados como `M x y h0` com traço redondo. Não são defeito.
- Tabela ordenável fora de figura (`pagina_texto_reguas.py`, os 100 pela combinação das duas réguas): cabeçalho `sticky` confirmado com rolagem interna (`max-height: 560px`); ordena asc no 1º clique e desc no 2º.

## Defeitos, por gravidade

| # | Figura | Largura | Defeito | Medida | Gravidade |
|---|---|---|---|---|---|
| 1 | página inteira (figuras adiadas) | 1440, 390 | Âncora de capítulo e de figura cai longe do alvo. As figuras adiadas ficam com altura de espera menor que a real e, ao chegar, empurram o alvo para baixo | Link `#segundo-turno` no menu, clicado do topo: o capítulo para a **3.664 px** do topo da janela. Carga direta com hash, 2,5 s depois: `#fig-terceira_via_prioridade` a 3.662 px (1440) e 2.873 (390); `#fig-reguas_divergencia_mapa` a 3.661 e **6.867**; `#fig-estoque_uf` a 3.662; `#fig-clusters_secoes` a 1.399 e 2.022; `#fig-pesquisas_erro` a 1.403 (essa nem é adiada) | quebra a leitura |
| 2 | `terceira_via_prioridade` | todas | A tabela dos 100 diz "Clique no cabeçalho para ordenar" e não ordena. O `<script>` que monta os botões vem dentro do `<noscript class="fig-src">`; o `<template>` insere o script sem executar | `table[data-ordena]`: 0 `button.ord`, `data-ok` ausente, depois de materializar por rolagem e por `beforeprint` | quebra a leitura |
| 3 | `placar_candidatos` | 390 | A primeira figura do dossiê mostra só até 20% do eixo. As duas barras principais aparecem cortadas e os números 47,03% e 45,16% ficam fora da tela | rolagem interna 340 de 720 px; rótulos a 555 e 569 px da esquerda | quebra a leitura |
| 4 | `regioes_2022_2026` | 390 | O zero das barras divergentes está fora da área visível. O leitor só vê as perdas de Lula; nenhuma barra de Flávio aparece sem rolar | zero a 456 px numa área de 340; rolagem 340 de 820 | quebra a leitura |
| 5 | `capitais_interior`, `comparecimento_regioes`, `lentidao_ufs_2022_2026`, `estoque_uf`, `vao_estadual`, `senado_vao_candidatos`, `pesquisas_erro`, `central_casa_ufs` | 390 | Mesmo problema: o estado inicial da rolagem mostra rótulos e só o lado esquerdo do eixo. Em `lentidao_ufs_2022_2026` aparece um único ponto (DF) e o eixo vai só de 18h a 19h; em `comparecimento_regioes` aparece só a coluna de nomes | rolagem 340 de 820 a 860 px; nenhuma pista de rolagem (sem máscara, sombra ou texto) | quebra a leitura |
| 6 | `reserva_vs_urna` | 1440, 1024, 390 | Siglas de UF sobrepostas e sobre outros pontos no aglomerado de 3 a 6 pp. CE, PB, PI, AL e BA ficam ilegíveis | 8 pares de siglas se sobrepõem: BA/PB 41% da área, RR/SP 26%, BA/PI 24%, MG/TO 19%, PB/PI 18%, AL/CE 17%, ES/TO 14%, AC/ES 7%. AL e CE ficam sob 3 pontos cada | quebra a leitura |
| 7 | `volume_noite` | todas | Legenda com lista vazia: "(99,7% das seções; faltam ), multiplicado por 1,00". `ufs_ausentes` vem vazio, mas a cobertura não é 100% | texto literal na `figcaption` | atrapalha |
| 8 | `volume_noite` | 1440, 1024 | O chip "19:22 a 19:31: ritmo a 35%" fica sobre as barras de 18:28 a 18:50, longe da faixa que descreve, e as barras escuras atravessam o texto | chip ancorado em `X(a) - 6`, `topo + 108`, com `text-anchor="end"` | atrapalha |
| 9 | `clusters_secoes` | todas | A elipse dourada do "grupo mais atípico" (Grupo 3, verde) envolve as nuvens dos quatro grupos. O dourado é a mesma cor do Grupo 4 (`#7d5b00`), então o leitor associa "mais atípico" ao Grupo 4 | elipse de x −2,4 a +4,0 no CP1; contém os quatro centros | atrapalha |
| 10 | `capitais_interior` | todas | A legenda usa quadrados cinza e preto ("1º turno de 2022", "2026"), mas as barras são azul ou vermelho, em tom claro e escuro | 2 amostras de cor da legenda não aparecem no gráfico | atrapalha |
| 11 | `regioes_2022_2026` (aba "Contra o 2º turno de 2022") | 1440, 1024 | Com as duas barras negativas na mesma linha, os rótulos colidem entre si e com o cabeçalho de região | Rondônia "−3,2" sobre "−3,4"; Rio de Janeiro "−3,5"/"−4,1"; Centro-Oeste "−3,7" sobre a faixa da região | atrapalha |
| 12 | `senado_segundas_vagas` | 1440, 1024, 390 | O cabeçalho "2º eleito × 3º colocado" fica sobre o item "Direita" da legenda. O rótulo "18,95" de MS invade o nome "Capitão Contar × Vander Loubet" | sobreposição de 39×9 px com a legenda; 2×15 px no rótulo de MS. A barra de MS chega a 632 px e a coluna de nomes começa em 678 | atrapalha |
| 13 | `pesquisas_erro` | todas | Os intervalos de 95% de Real Time, Nexus, MDA e Indexa acabam exatamente em +10, o fim do eixo, sem marca de corte. Os rótulos de valor ("−0,3", "+4,2", "+7,1") ficam sobre o ponto reponderado e a seta | 4 traços acabam em x = +10,0 | atrapalha |
| 14 | `terceira_via_mapa` | 1440 | O rótulo "São Paulo" cobre a própria bolha de São Paulo (salmão, `r` 26), e as bolhas azuis menores, desenhadas por cima, escondem o resto. "Curitiba" também cobre a própria bolha | bolha de SP em (409, 439) na viewBox; o chip do rótulo cobre a metade direita dela | atrapalha |
| 15 | `dispersao_municipios` | todas | Os rótulos "São Paulo", "Salvador" e "Rio de Janeiro" não têm linha até o ponto. O de São Paulo fica ao lado de uma bolha laranja do Nordeste, e a bolha azul de SP (a maior, `r` 14,5) fica enterrada na nuvem | rótulo 25 px à direita e 15 px abaixo do centro de SP | atrapalha |
| 16 | `latencia_hora` | todas | Os nomes das séries ficam empilhados à direita na ordem UF, Nacional, Município, Zona, longe do fim de cada linha: Município termina em 01h e Zona em 02h, abaixo de UF. Na legenda, a unidade é "segundos"; no eixo, h, min e s | ordem dos rótulos diferente da ordem das linhas em 02h | atrapalha |
| 17 | `secoes_outras` | todas | Painel "Seções recebidas por hora": a linha de "Lula, % dos válidos" não tem eixo nem valores; o eixo x pula de 21h para 23h, 01h e 08h sem marcar a quebra. "Hora de encerramento" não tem eixo y | 0 rótulos de y nos dois painéis de cima | atrapalha |
| 18 | `estoque_uf` | todas | Só as barras de Flávio têm rótulo de valor. As de Lula, maiores (SP perto de 1,7 milhão; total 7,05 milhões contra 2,48), ficam sem número. Há também dois "0" sobrepostos no eixo | 21 rótulos para Flávio, 0 para Lula; "0"/"0" com 100% de sobreposição | atrapalha |
| 19 | `secoes_tamanho_tipo` | 1440, 1024 | O SVG reserva a altura da aba com mais grupos: em "Por votantes" sobram cerca de 220 px vazios entre as barras e a legenda. Na aba "Por tipo de local", "unidade prisional ou socioeducativa" passa por baixo do eixo e da barra | vazio de 395 a 615 px de 791; o rótulo invade 16 px depois de x = 272 | atrapalha |
| 20 | `fechamento_persistencia` | todas | Uma legenda só mistura duas codificações: as cores do mapa ("p90 às 19h ou depois também em 2022", verde-escuro) e as das regiões da dispersão (Norte, verde-petróleo). Os dois verdes não se distinguem | 2 verdes na mesma legenda, um para cada painel | atrapalha |
| 21 | `transferencia_cenarios` | todas | Barras 100% empilhadas com eixo cortado em 40%. A parte de Flávio parece 3,3 vezes a de Lula para 51,7 contra 48,3 | eixo de 40% a 60% | atrapalha |
| 22 | `lentidao_marcos` | todas | Os pequenos múltiplos não têm rótulo de hora nem de percentual; só o texto abaixo da grade diz "17h a 01h, 0 a 100%" | 0 rótulos de eixo em 28 painéis | atrapalha |
| 23 | `mapa_mundi_exterior` | 390 | Os rótulos das cidades (Boston, Miami, Londres, Lisboa, Nagóia) saem em 4 px | `minfont` 4,0 px; 5 de 5 rótulos | atrapalha |
| 24 | figuras adiadas (13) | 1440, 390 | A caixa de espera tem altura diferente da figura real e a página salta quando ela chega. É a causa do item 1 e de saltos no Safari, que não ancora a rolagem | 1440: `clusters_secoes` 743→2.840, `prioridade` 764→1.761, `teto_uf` 743→1.562, `reguas` 764→1.569, `senado_carregadores_mapa` 764→1.565. 390: `clusters_secoes` 518→5.366, `teto_uf` 524→2.001 | atrapalha |
| 25 | 54 das 63 figuras | 390 | Rolagem interna de 2 a 3 vezes a largura, sem pista visual de que há conteúdo à direita | contêiner `.chart-scroll` de 340 px com conteúdo de 700 a 980 px; `terceira_via_prioridade`, tabela de 2.321 px | atrapalha |
| 26 | `placar_candidatos` | 1440, 1024 | A linha tracejada de 50% atravessa os rótulos "47,03% · 56.104.503" e "45,16% · 53.879.538" | linha em x ≈ 893 px; rótulo de 870 a 1.030 | cosmético |
| 27 | `camara_por_uf`, `votos_x_cadeiras`, `assembleias_campo` | todas | A linha tracejada de metade das cadeiras corta os números dentro das barras: "4" no Acre, ES e Amazonas, "8" no Paraná, "10" na Bahia, "16,9%" e "16,8%" em `votos_x_cadeiras` | 6 ou mais rótulos atravessados | cosmético |
| 28 | `senado_vao_candidatos` | 1440, 1024, 390 | O cabeçalho "Senado à frente de Flávio →" sai da viewBox pela direita | 15,3 px (1440), 12,8 (1024), 11,2 (390), nas duas abas | cosmético |
| 29 | `hemiciclo_camara` | 1440 | O rótulo "257 maioria" passa do topo da viewBox | 1,8 px, nas abas campo e partido | cosmético |
| 30 | `exterior_continentes` | 1440, 1024 | Na aba "Por continente" sobram cerca de 220 px vazios (altura reservada para 12 países), com o tracejado de 50% descendo até o fim | barras até 395 px de um SVG de 610 | cosmético |
| 31 | `acumulado_noite`, `lotes_noite`, `noite_regioes_lotes` | 1440, 1024 | O eixo vai até 03h ou 00h, mas tudo acontece até 21h30. Mais de 40% da largura fica sem dado | 21h a 03h, 6 de 10 horas sem variação | cosmético |
| 32 | `central_casa_ufs` | todas | "líder errado" (AM e AP) fica uns 380 px à direita da barra que qualifica | rótulo em x ≈ 990; a barra acaba em ≈ 410 | cosmético |
| 33 | `regioes_2022_2026`, `capitais_interior`, `central_casa_ufs`, `divergencia_nacional` | todas | Eixo numérico sem unidade ("−10 … +10", "80%" sem dizer de quê); a unidade só aparece na legenda | sem medida | cosmético |
| 34 | `modelo_urna_uf` | todas | O segmento cinza-escuro no fim da barra do exterior (ZZ) não está na legenda | 1 cor fora da legenda | cosmético |
| 35 | `secoes_tamanho_tipo` | todas | A legenda repete a explicação: "O tipo de local é inferido pelo nome (Tipo de local é inferência por palavra-chave … do cadastro.)." | texto literal | cosmético |
| 36 | `senado_pl_x_flavio_uf` | 1440 | No Distrito Federal os rótulos "+5,2" e "+7,4" se tocam | 14×5 px | cosmético |
| 37 | `arquitetura_totalizacao` | 1440 | "relacional ou distribuído, fora do caminho de escrita" encosta na borda direita da caixa "Armazenamento de leitura" | menos de 2 px de folga | cosmético |

## Correção sugerida, por módulo

1. **Âncoras e altura de espera (itens 1 e 24).** `scripts/apuracao_2026/pagina_fig_base.py` (`figura_html`, `ADIAR_ACIMA`) e `scripts/apuracao_2026/pagina_interativo.py` (`materializa`, `porAncora`). Grave a altura real de cada figura adiada em 1440 e em 390 (o build já sabe o `viewBox`) e aplique-a à espera como `aspect-ratio` do SVG mais a altura fixa da legenda, ou como `min-height` por faixa de largura. Em `porAncora`, depois de materializar, volte a chamar `alvo.scrollIntoView()` num `requestAnimationFrame`. No clique de link interno, materialize com `materializaTodas()` tudo o que fica acima do alvo antes de rolar. Teste: o `qa-ux` do capítulo com `#segundo-turno` precisa terminar com o topo do alvo entre 0 e a altura da barra.
2. **Ordenação da tabela adiada (item 2).** `scripts/apuracao_2026/pagina_fig_terceira_via_b.py:84`. Tire o `<script>` de dentro do corpo da figura e ponha a função de ordenar em `pagina_interativo.py`, chamada por `monta(fig)` (que roda depois de `materializa`) para cada `table[data-ordena]` sem `data-ok`. A outra tabela (`pagina_texto_reguas.py:272`) passa a usar a mesma função.
3. **Celular (itens 3, 4, 5 e 25).** `scripts/apuracao_2026/pagina_css.py` (regra `.chart-scroll`) e cada `@registra`. O mais barato: em `pagina_interativo.py`, ao montar a figura, rolar a `.chart-scroll` até o zero do eixo (`data-x0` gravado pelo gerador) nas barras divergentes, ou até o fim nas séries temporais (os rótulos finais), e pôr uma máscara de esmaecer na borda que ainda tem conteúdo. O correto: dar versão empilhada abaixo de 720 px às figuras de barras horizontais, como `arquitetura_totalizacao` já tem. Prioridade: `placar_candidatos` (`pagina_fig_noite.py:130`), `regioes_2022_2026` (`pagina_fig_regioes.py:68`), `capitais_interior` (`:360`), `comparecimento_regioes` (`:486`), `lentidao_ufs_2022_2026` (`pagina_fig_noite_regioes.py:464`), `estoque_uf` (`pagina_fig_estrategia.py:267`), `vao_estadual` (`pagina_fig_congresso.py:767`), `pesquisas_erro` e `central_casa_ufs` (`pagina_fig_pesquisas.py:56` e `:455`).
4. **`reserva_vs_urna` (item 6).** `pagina_fig_pesquisas.py:808`. Faça o desvio dos rótulos por colisão: ordene por y, empurre na vertical até não haver interseção e ligue cada sigla ao ponto com um fio. Outra saída: rotule só as UFs fora do aglomerado (x ≥ 6,5 ou y ≥ 7) e deixe a ficha para as outras.
5. **`volume_noite` (itens 7 e 8).** `pagina_fig_arquitetura.py:528`: quando `am['ufs_ausentes']` vier vazio, omita "faltam …" e escreva a cobertura certa. Hoje "27 UFs, 99,7%" e o fator 1,00 se contradizem: confira `fracao_do_pais` e `fator_extrapolacao` em `arquitetura.json`. `pagina_fig_arquitetura.py:411-419`: ancore o chip dentro da própria faixa tracejada (`X(a)` com `text-anchor="start"` acima de `topo + 44`) ou acima das barras, com fundo opaco.
6. **`clusters_secoes` (item 9).** `pagina_fig_secoes.py:731`: tire a elipse ou desenhe-a só sobre a nuvem do Grupo 3, com a cor do grupo (verde) em traço tracejado. Não use o dourado do Grupo 4.
7. **`capitais_interior` (item 10).** `pagina_fig_regioes.py:360`: troque as amostras da legenda por um par azul-claro e azul-escuro e escreva "tom claro: 2022; tom escuro: 2026; azul: direita à frente; vermelho: Lula à frente".
8. **`regioes_2022_2026`, aba do 2º turno (item 11).** `pagina_fig_regioes.py:68`: quando as duas barras têm o mesmo sinal, ponha o rótulo da barra menor dentro dela, ou alterne o lado.
9. **`senado_segundas_vagas` (item 12).** `pagina_fig_congresso.py:631`: desça o cabeçalho da coluna de nomes para a linha de baixo da legenda e faça a coluna começar em `X(max) + largura do rótulo + 12`.
10. **`pesquisas_erro` (item 13).** `pagina_fig_pesquisas.py:56`: aumente o domínio para +12 ou desenhe uma seta ou um "›" no traço cortado. Ponha o rótulo de valor depois do maior dos dois pontos.
11. **`terceira_via_mapa`, `dispersao_municipios` (itens 14 e 15).** `pagina_fig_terceira_via.py:161` e `pagina_fig_regioes.py:216`: desloque o rótulo para fora do raio da bolha (`r + 6`) com fio até o centro e desenhe por último o contorno da bolha rotulada, por cima das outras.
12. **`latencia_hora` (item 16).** `pagina_fig_noite.py:600`: ponha cada rótulo no y do último ponto da própria série, com desvio anticolisão, e diga "minutos" na legenda.
13. **`secoes_outras` (item 17).** `pagina_fig_secoes_b.py:738`: um eixo direito com 0% e 100% (ou o mínimo e o máximo) para a linha de Lula, uma marca de quebra entre 21h e 08h, e os valores do y dos histogramas.
14. **`estoque_uf` (item 18).** `pagina_fig_estrategia.py:267`: rotule as barras de Lula à esquerda, com a mesma regra das de Flávio, e retire o tick "0" duplicado.
15. **`secoes_tamanho_tipo`, `exterior_continentes` (itens 19 e 30).** `pagina_fig_secoes.py:545` e `pagina_fig_regioes.py:626`: um SVG por aba, com altura própria, trocado por `data-alt-show` no elemento `<svg>`, ou `viewBox` recalculado na troca. Abra a margem esquerda para caber "unidade prisional ou socioeducativa" ou quebre o rótulo em duas linhas.
16. **`fechamento_persistencia` (item 20).** `pagina_fig_fechamento.py:341`: duas legendas, uma sob cada painel, e um tom do mapa que não seja verde.
17. **`transferencia_cenarios` (item 21).** `pagina_fig_estrategia.py:182`: barra 100% começando em 0, ou só a diferença para 50% em barra divergente.
18. **`lentidao_marcos` (item 22).** `pagina_fig_noite_regioes.py:591`: rotule 18h, 21h e 0h no x e 50% no y do primeiro painel (BR).
19. **`mapa_mundi_exterior` (item 23).** `pagina_fig_mapas.py:460`: abaixo de 720 px, esconda os rótulos ou aumente-os para 11 px compensando a escala (`font-size` em função de `vb.width / largura`).
20. **Cosméticos (26 a 37).** Linhas de referência atrás do texto, ou rótulos com fundo (`paint-order: stroke`, traço na cor do papel) em `pagina_fig_noite.py:130` e `pagina_fig_congresso.py:331/408/717`. Margem direita de 16 px em `pagina_fig_senado_flavio.py:259`, superior de 4 px em `pagina_fig_congresso.py:100`. Domínio do eixo de tempo até 22h em `pagina_fig_noite.py:241/343` e `pagina_fig_noite_regioes.py:79`. "líder errado" encostado na barra em `pagina_fig_pesquisas.py:455`. Unidade no eixo ("pp", "% das seções") nos quatro módulos do item 33. Cinza da ZZ na legenda em `pagina_fig_secoes_b.py:201`. Texto duplicado em `pagina_fig_secoes.py:545`. Rótulos do DF em `pagina_fig_senado_flavio.py:133`. Largura da caixa em `pagina_fig_arquitetura.py:271`.

## Testes de regressão sugeridos

- `qa-figuras.py`: carregar `#segundo-turno`, `#fig-terceira_via_prioridade` e `#fig-reguas_divergencia_mapa` e exigir o topo do alvo em [0, 120] px depois de 2 s, em 1440 e em 390.
- Toda `table[data-ordena]` precisa ter um `button.ord` por `th` depois de `beforeprint`.
- Em 390, para cada `.chart-scroll` com barras divergentes, o x do rótulo "0" precisa ficar dentro de `clientWidth`. Na primeira figura do capítulo 1, os rótulos dos dois primeiros colocados precisam estar visíveis.
- Rodar `ovl_any.js` (interseção de caixas de `<text>` acima de 1,5 × 3 px, sem contar rótulos girados) com lista de exceções declaradas, e falhar acima de zero.
- `figcaption` sem o padrão `\(\s*\)` nem `faltam \)`.

## Estado depois da correção (W14, 05/10/2026)

Medido com os mesmos scripts (`qa_visual.py`, `ovl_any.js`, `sortp.py`) e mais três da pasta `scratchpad/w14/`: `alturas.py` (espera contra figura real), `ancoras.py` (desvio do alvo em 15 links do menu e 7 `#fig-` diretos) e `tudo.py` (todas as figuras, todas as abas, 1440, 1024 e 390). Regressões em `tests/test_apuracao_2026_qa_visual.py`.

| # | Estado | Antes | Depois |
|---|---|---|---|
| 1 | corrigido | `#segundo-turno` a 3.664 px; `#fig-reguas_divergencia_mapa` a 6.867 px (390) | 15 links do menu e 7 âncoras diretas, 1440 e 390: desvio máximo de 1 px (uma rodada deu 67 px em `#senado` a 390 com a rolagem suave ainda em curso aos 1,8 s; não se repetiu em quatro rodadas). O clique e a carga com hash materializam as adiadas acima do alvo no mesmo capítulo antes de rolar; `load` e `document.fonts.ready` devolvem o alvo ao topo enquanto o leitor não rolou |
| 2 | corrigido | 0 `button.ord` | 19 botões na tabela da figura e 13 na do texto, ordem asc no 1º clique e desc no 2º; ordenação por delegação em `pagina_interativo.py`, sem `<script>` dentro de figura |
| 3 | corrigido | 47,03% e 45,16% fora da tela em 390 | versão empilhada abaixo de 720 px (viewBox 360): nome e parcela na mesma linha, barra embaixo, os seis visíveis |
| 4 | corrigido | zero a 456 px numa área de 340 | versão empilhada abaixo de 720 px, sigla da UF, zero no centro, as duas direções visíveis |
| 5 | corrigido | rolagem em 0, só nomes | `data-foco` abre no zero e na maior barra: capitais 450 px, comparecimento 140, lentidão (faixa dos 99%) 315, estoque 154, vão estadual 520, Senado 480, pesquisas 394, central 413 |
| 6 | corrigido | 8 pares de siglas sobrepostos | 0 (busca de posição livre, fio até o ponto, pontos desenhados antes das siglas) |
| 7 | corrigido | "faltam )" e fator 1,00 | "nas 27 UFs (99,7% das seções têm o carimbo), multiplicado por 1,003"; 0 legendas com lista vazia na página |
| 8 | corrigido | chip sobre as barras de 18:28 a 18:50 | chip à direita da própria faixa, sob o rótulo da lacuna; 0 sobreposições |
| 9 | não tocado | | fora do escopo (W13) |
| 10 | corrigido | 2 amostras de cor fora do gráfico | legenda com o par claro (2022) e o par escuro (2026) em azul e vermelho; unidade no eixo |
| 11 | corrigido | "−3,2" sobre "−3,4" e outros | linhas de 36 px, barras a 15 px, rótulos com contorno: 0 sobreposições nas duas abas |
| 12 | corrigido | 39×9 px com a legenda; 2×15 px em MS | coluna de nomes depois do maior rótulo, cabeçalho sob a legenda: 0 |
| 13 | corrigido | 4 traços acabam em +10 | eixo cobre a margem de 95% (até 14 pp, com ponta de corte se passar); rótulos com contorno; unidade no eixo |
| 14 | corrigido | rótulo sobre a bolha de SP, bolha enterrada | rótulo fora do raio com fio, bolha rotulada redesenhada cheia e contornada por cima |
| 15 | corrigido | rótulos sem fio | mesmo método do item 14 |
| 16 | corrigido | nomes empilhados longe das linhas | cada nome no fim da própria linha; legenda diz escala logarítmica de 30 s a 1 h |
| 17 | não tocado | | fora do escopo (W13) |
| 18 | corrigido | 0 rótulos de Lula; "0" duplicado | 27 rótulos de Lula, um "0" só, folga de 84 entre valor e nome |
| 19 | não tocado | | fora do escopo (W13) |
| 20 | corrigido | dois verdes numa legenda | uma legenda por painel; o mapa usa carvão `#2f2f2f` |
| 21 | corrigido | eixo de 40% a 60% | barra 100% de 0 a 100% |
| 22 | corrigido | 0 rótulos de eixo | painel BR com 18h, 20h, 22h, 0h e 50% |
| 23 | corrigido | rótulos a 4 px | rótulos do mapa-múndi somem abaixo de 720 px; a ficha dá o nome |
| 24 | corrigido | `clusters_secoes` 518 → 5.366 (390) etc. | as 13 adiadas, em 1440, 1024 e 390: diferença 0 px. A espera usa a classe, a largura mínima e a razão do viewBox do gráfico; controles, legenda HTML e tabelas saem do `<noscript>` |
| 25 | corrigido | nenhuma pista | sombra interna na borda com conteúdo e linha "role para o lado →" acima do gráfico (some na primeira rolagem sem mudar a altura); a espera adiada recebe a mesma linha |
| 26 | corrigido | linha de 50% sobre os rótulos | rótulos com contorno da cor do papel |
| 27 | corrigido | linha corta "4", "8", "10", "16,9%" | números desenhados depois da linha, com contorno na cor da barra |
| 28 | corrigido | 15,3 px fora | 0 (cabeçalho preso à margem quando o zero fica à direita) |
| 29 | corrigido | 1,8 px fora | 0 |
| 30 | corrigido | 220 px vazios | `data-alt-vb`: a aba troca o viewBox (514 px por continente, 719 por país) |
| 31 | corrigido | eixo até 03h ou 00h | eixo até 22h nas três figuras, com nota no desenho do que veio depois (117 versões, 99,75% a 100%; 29 lotes, 290.588 válidos) |
| 32 | corrigido | rótulo a ~380 px da barra | encostado na barra (depois do número ou do outro lado do zero) |
| 33 | corrigido | eixo sem unidade | unidade no eixo de `regioes_2022_2026`, `capitais_interior`, `central_casa_ufs` e `divergencia_nacional` |
| 34 | não corrigido | | `modelo_urna_uf` vive em `pagina_fig_secoes_b.py`, módulo reservado à W13 |
| 35 | não tocado | | fora do escopo (W13) |
| 36 | corrigido | 14×5 px | barras a 16 px uma da outra e rótulos com contorno: 0 |
| 37 | corrigido | menos de 2 px de folga | subtítulo quebra em duas linhas e a caixa cresce |

Extra: `fechamento_regioes` tinha "17h" encostando no "0%" (6×4 px) nos painéis; o primeiro rótulo de hora passou a alinhar à esquerda.

Auditores (servidor em 4173): `render-audit.py` 0 problema em 1440 e 390; `contrast-audit.py` 0 abaixo do AA em 1440, 1024 e 390. Para chegar a zero em 390, o guarda passou a ignorar texto que a rolagem interna deixa fora da área visível do contêiner (validado numa página de teste: o recorte deixa de contar e as duas reprovações reais continuam).
