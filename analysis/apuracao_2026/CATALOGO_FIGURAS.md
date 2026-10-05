# Catálogo de figuras do dossiê (contrato entre figuras e texto)

Regra: o texto chama `figura_catalogo("nome", dados, **opcoes)` (acessor em `scripts/apuracao_2026/pagina_comum.py`; `figura(svg, legenda)` já existia e continua sendo o envoltório de figura), que procura `FIGURAS["nome"]` em `scripts/apuracao_2026/pagina_figuras.py` e, se ainda não existir, devolve um bloco `<figure class="pendente">`. Cada figura devolve HTML completo: `<figure class="reveal">` com SVG (com `<title>`), ficha interativa (`data-tip` + JSON embutido) e `<figcaption>`. Toda figura tem versão empilhada ou rolagem interna abaixo de 720 px. Interação: ficha escura da casa ao passar o mouse ou tocar (padrão de `docs/assets/reponderacao_tip.js`), realce do elemento, e, quando indicado, botões de alternância (`data-alt`) que trocam a série sem recarregar; tudo funciona em `file://`.

| nome | capítulo | o que mostra | interação |
|---|---|---|---|
| `placar_candidatos` | 1 | barras horizontais dos 6 primeiros (votos e % válidos) | ficha com votos, %, diferença para o 1º |
| `mapa_vencedor_uf` | 1 | coroplético por UF, cor do vencedor em bandas pela margem | ficha por UF: votos e % dos dois, margem, 2022 |
| `acumulado_noite` | 2 | linha de votos acumulados por candidato com as 3 paradas sombreadas | ficha por versão: hora, seções, votos, % |
| `lotes_noite` | 2 | barras do que cada versão acrescentou (válidos) + linha de seções | ficha por lote; alternância válidos / seções |
| `mapa_hora_100` | 2 | coroplético da hora em que cada UF fechou | ficha: hora, última seção, seções tardias |
| `divergencia_nacional` | 2 e 3 | nacional × soma das UFs × monitoramento, 18:40 a 20:10 | ficha por minuto: as três contagens e a diferença |
| `latencia_hora` | 3 e 14 | p50/p95 da latência de leitura por hora | ficha por hora |
| `regioes_2022_2026` | 4 | barras divergentes por UF (swing de Flávio e de Lula), agrupadas por região | ficha: 2022, 2026, votos; alternância 1T 2022 / 2T 2022 |
| `dispersao_municipios` | 4 | município: Bolsonaro 2022 × Flávio 2026 (ponto por município, área = eleitorado, cor por região) | ficha por município; filtro por região |
| `mapa_swing_uf` | 4 | mapas municipais de SP, MG, BA, PE com o swing (um por aba) | ficha por município; abas |
| `capitais_interior` | 4 | barras: capitais × interior por região, 2022 × 2026 | ficha |
| `comparecimento_regioes` | 4 | comparecimento 2022 × 2026 por UF (pontos ligados) | ficha |
| `mapa_mundi_exterior` | 5 | bolhas por cidade sobre o mundo, cor do líder | ficha por cidade: eleitorado, votantes, %, hora local |
| `exterior_continentes` | 5 | barras empilhadas por continente e país (top 12) | ficha; alternância continente / país |
| `hemiciclo_camara` | 6 | 513 cadeiras por campo | ficha por cadeira: nome, partido, UF, votos; alternância campo / partido |
| `camara_partidos` | 6 | barras das 14 bancadas, 2022 × 2026 lado a lado | ficha |
| `votos_x_cadeiras` | 6 | empilhadas % votos × % cadeiras por campo | ficha |
| `camara_por_uf` | 6 | pequenos múltiplos ou empilhadas por UF (campo) | ficha |
| `hemiciclo_senado` | 7 | 81 (27 contorno + 54 novos) por campo | ficha por assento; alternância 2023 / 2027 |
| `senado_segundas_vagas` | 7 | distância entre 2º e 3º por UF | ficha |
| `assembleias_campo` | 8 | empilhadas por campo nas 11 casas, 2022 × 2026 | ficha |
| `vao_estadual` | 9 | barras com sinal: governador do campo menos presidenciável | ficha com os dois % e votos |
| `governadores_mapa` | 9 | coroplético: eleito 1º turno (campo) ou 2º turno (hachura clara) | ficha |
| `pesquisas_erro` | 10 | pontos por instituto com seta publicado → reponderado, contra a urna | ficha; alternância diferença / Flávio / Lula |
| `pesquisas_serie` | 10 | série do agregador (publicado e reponderado) e a urna como ponto final | ficha por dia |
| `central_casa_ufs` | 10 | erro da central da casa por UF | ficha |
| `senado_brier` | 10 | p_eleito prevista × eleito (pontos) | ficha |
| `voto_util_cascata` | 11 | cascata: terceiros nas pesquisas → urna, por candidato | ficha |
| `reserva_vs_urna` | 11 | reserva medida × revelada por UF | ficha |
| `mapa_anomalias` | 12 | 50 zonas mais atípicas no mapa, raio pelo score | ficha com features e explicação |
| `anomalias_features` | 12 | barras das features normalizadas das 25 primeiras (heatmap) | ficha |
| `transferencia_cenarios` | 13 | barras dos seis cenários de 2º turno | ficha |
| `estoque_uf` | 13 | barras do estoque de 2022 por UF | ficha |
| `movimentos_2t` | 13 | barras dos dez movimentos por votos esperados | ficha com regra |
| `auditoria_coletor` | 14 | versões gravadas por hora e classes de leitura | ficha |
