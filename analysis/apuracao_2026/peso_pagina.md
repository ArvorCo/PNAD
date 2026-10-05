# Peso da página do dossiê da apuração (05/10/2026)

Medição de `scripts/apuracao-2026-peso.py`: Chromium do Playwright, janela 1440 × 1000, página aberta em `file://`, contexto novo a cada rodada, mediana de 3 rodadas. "Carga" é o estado logo depois do evento `load`; "materializada" é depois de `beforeprint`, que materializa toda figura adiada (o mesmo gatilho que os auditores usam). RSS é o processo renderizador, lido do sistema pelo PID. Os valores crus ficam em `peso_pagina.json`.

| medida | antes (commit 47bbacc) | depois, na carga | depois, tudo materializado |
|---|---|---|---|
| arquivo | 9,300,540 bytes | 9,304,366 bytes | idem |
| DOMContentLoaded | 697 ms | 511 ms | idem |
| load | 914 ms | 757 ms | idem |
| nós do DOM | 54,899 | 28,768 | 55,055 |
| heap de JavaScript | 12.3 MB | 2.4 MB | 12.3 MB |
| RSS do renderizador | 463.9 MB | 333.9 MB | 431.2 MB |
| figuras adiadas | 0 | 13 | 0 |
| materialização das 13 | | | 51 ms |

O arquivo cresce 3,8 KB (espera e envoltório de cada figura adiada); o que muda é o que o navegador monta e pinta na carga. O custo volta inteiro só quando o leitor rola por todas as figuras ou imprime, e mesmo assim o RSS fica abaixo do anterior porque a materialização acontece fora do parse inicial.

## Figuras adiadas (corpo acima de 150 KB, `ADIAR_ACIMA`)

- lotes_noite
- noite_regioes_diferenca
- dispersao_municipios
- mapa_swing_uf
- senado_carregadores_mapa
- secoes_90
- clusters_secoes
- fechamento_persistencia
- terceira_via_mapa
- terceira_via_teto_uf
- terceira_via_prioridade
- reguas_divergencia_mapa
- nulo_2022_municipios

A lista sai do tamanho do corpo gerado e muda com os dados; a regra é a constante, não a lista.

## Como funciona

Ver a nota de carregamento sob demanda em `CATALOGO_FIGURAS.md` e a docstring de `scripts/apuracao_2026/pagina_fig_base.py`. Conferido no navegador em 05/10/2026: sem JavaScript o `<noscript>` é parseado e o SVG pinta (713 px de altura); com JavaScript o bloco é texto cru na carga, materializa ao rolar, pela âncora do capítulo e por `beforeprint`, e a ficha por vizinho mais próximo funciona depois da materialização; zero erros de console. `render-audit.py` e `contrast-audit.py` zerados sobre a página servida.
