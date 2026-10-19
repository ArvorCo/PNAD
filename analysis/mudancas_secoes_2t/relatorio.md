# Mudanças de local de votação entre os turnos de 2026: relatório do motor

Gerado em 2026-10-19T07:08:15+00:00 por `python3 scripts/mudancas-secoes-2t.py` (2000 réplicas de bootstrap, semente 20261019).

## Fontes

| chave | caminho | bytes | SHA-256 | confere |
|---|---|---|---|---|
| cadastro_1t | `data/raw/tse_eleitorado/eleitorado_local_votacao_2026.zip` | 88.044.650 | `045df0a517be35490bcdfdbaf91ed2224122efec9b0d2ab199836e15f8b0805c` | sim |
| cadastro_2t | `data/raw/tse_eleitorado/locais_2t/eleitorado_local_votacao_2026_20261018.zip` | 167.433.047 | `a948d3e587d7116ffe003fb07a083b2d1d64ce9a236f703f92d36e168f1b5adb` | sim |
| boletins_1t | `apuracao/data/secoes_2026.sqlite` | 8.550.633.472 | `None` |  |
| logs_1t | `data/outputs/logs_urnas_2026.sqlite` | 3.856.224.256 | `None` |  |
| mapa_fiscais | `docs/assets/fiscais_mapa/indice.json` | 167.386 | `455bde4ce5a715702ae7a8c3ecb38277ba4e246b86221df9b0462b67b2b5c82d` |  |
| presidente_2022 | `data/outputs/presidente_secao_2022.csv.gz` | 13.098.556 | `d10766833596c67ce15f2ed3978d78f5a60bab6329c1c436f3ca394f58d1852d` |  |
| detalhe_2022 | `data/raw/tse_resultados/detalhe_votacao_secao_2022.zip` | 243.822.213 | `ad22c50b9e6d9dfb096a2170680a190f1734895ba89d8977b95fd63ca02c03da` |  |
| clima_open_meteo | `analysis/mudancas_secoes_2t/clima/open_meteo.json` | 6.894.593 | `1ddbaaca61121627ca009872dacfd80b4bb155be4671765aac5a13e55efbf48d` |  |
| tre_noticias | `analysis/mudancas_secoes_2t/tre_noticias.json` | 49.558 | `ba374ddb8b668b2964d919795f9f41215b8ce591929f474a4936072d0e6c6a8c` |  |
| fontes_1t_imprensa | `analysis/mudancas_secoes_2t/fontes_1t.json` | 2.665 | `091a6f2ce84362dbeca0887393f7c7f12231d8228982aeb0ab77708b1f49bef9` |  |
| painel_tse | `data/originals/mudancas_secoes_2t/tse_painel_secoes_alteradas_20261018.json` | 244.861 | `babe867ced57917b76ecfcccd3fdee285b166ee7fee415a44daa52e73dcc5414` |  |

## Controles

| controle | esperado | obtido | passou |
|---|---|---|---|
| SHA-256 cadastro_1t | confere | sim | sim |
| SHA-256 cadastro_2t | confere | sim | sim |
| seções no cadastro | 517.179 | 517.179 | sim |
| soma das categorias | 517.179 | 517.179 | sim |
| referência do orquestrador, categoria A | 754 / 222.482 | 754 / 222.482 | sim |
| referência do orquestrador, categoria B | 255 / 72.878 | 255 / 72.878 | sim |
| referência do orquestrador, categoria C | 26 / 9.088 | 26 / 9.088 | sim |
| referência do orquestrador, categoria D | 86 / 27.388 | 86 / 27.388 | sim |
| referência do orquestrador, categoria E | 220 / 57.308 | 220 / 57.308 | sim |
| referência do orquestrador, categoria F | 208 / 66.456 | 208 / 66.456 | sim |
| referência do orquestrador, categoria G | 575 / 169.170 | 575 / 169.170 | sim |
| referência do orquestrador, categoria H | 1.034 / 284.030 | 1.034 / 284.030 | sim |
| referência do orquestrador, categoria Z | 514.021 | 514.021 | sim |
| fora do original no 1º turno | 6.535 / 1.916.865 | 6.535 / 1.916.865 | sim |
| fora do original no 2º turno | 6.036 / 1.767.261 | 6.036 / 1.767.261 | sim |
| caso de controle RJ 60011, zona 188, seções 123 a 127 (Rua Muaná para Rua Irapuá) | 5 seções, categoria D, mudança real | 5 seções, ['D'], mudança real True, 1880 eleitores (TRE-RJ: cerca de 1.800) | sim |
| válidos de presidente nas urnas do cadastro = soma de voto_secao | 119.300.852 | 119.300.852 | sim |
| abstenção nacional com exterior (ConJur: 21,08%) | 21,08 | 21,08 | sim |
| aptos e votos das urnas com mudança iguais aos do Politize | 0 | 0 | sim |
| cenários fecham (componentes somam o total) | sim | sim | sim |
| eleitorado do painel igual ao do arquivo nas seções dos dois | 286.517 | 286.517 | sim |
| nenhum travessão no JSON público | sim | sim | sim |
| nenhuma ocorrência da palavra vetada | sim | sim | sim |

## Decisões que o contrato não previa

- G nunca conta como mudança real. A fórmula do contrato incluía G até 50 km, mas G tem nome e endereço idênticos nos dois arquivos: o eleitor vai ao mesmo prédio. A conferência mostrou marcadores de posição: em Maringá (zona 137) 14 locais diferentes tinham no 1º turno a mesma coordenada; em Candeias (zona 127) vários locais passaram no 2º turno para a mesma coordenada. Se G contasse: 336 seções, 106.262 eleitores.
- A referência G = 575 inclui 239 seções em que a coordenada existe em um só dos turnos; elas ficam em G com coord_suspeita e distância nula.
- D só não conta quando nome e endereço normalizados são iguais (mudança de grafia, um caso em Maringá); D com endereço igual e nome de outra instituição conta, com confiança média.
- E conta quando o logradouro normalizado é outro (comparação tolerante a abreviação, complemento, número acrescentado e localidade antes da rua); número diferente no mesmo logradouro não conta. E real tem confiança média: pode ser outra entrada do mesmo prédio.
- A, B, C e X não contam quando nome e endereço normalizados são iguais (outro número para o mesmo prédio): 11 seções.
- Seção agregada vota na urna da principal: a camada efetiva copia para a agregada o local e a classificação da principal. 73 agregadas mudam de categoria por isso.
- Coordenada idêntica para três ou mais locais do mesmo município e turno é marcador de posição: a distância dessas seções fica fora das estatísticas e o link do mapa usa o endereço.
- No Rio de Janeiro as transferências do TRE-RJ no 1º turno mantiveram o número do local e trocaram nome e endereço, então não aparecem como local diferente do original. O efeito do 1º turno ganhou o grupo troca desde 2022 (mesmo número, nome sem palavra em comum com o de 2022).
- Diferença em diferenças: controle = seções estáveis (mesmo número de 2022 e nome compatível), não todas as demais, para não misturar no controle seções que também trocaram de prédio.
- Fila no fechamento = último voto depois das 18h de Brasília (a votação terminou às 17h); abertura atrasada = primeiro voto às 8h30 de Brasília ou depois; fuso pela moda da hora de abertura no município (apuracao_2026.secoes_base.fusos_por_municipio).
- O exterior fica fora de comportamento, intercorrências e efeito (regra da casa para comparações nacionais); entra nos cenários e nas contagens.
- No Politize, a lista é a união do arquivo de locais (mudança real) com o painel do TSE de seções alteradas, com o campo fonte.
- Medianas de distância com IC por reamostragem de pares de locais (todas as seções de um par têm a mesma distância). Comparações de votos e logs por bootstrap de prédios (as urnas de um mesmo local do 1º turno saem juntas), estratificado, e não seção a seção como dizia o contrato: seções do mesmo prédio dividem o mesmo evento (em Laranjeiras do Sul, PR, 12 urnas de uma só escola abriram depois das 8h30), e a reamostragem por seção estreitaria o IC sem base. Os pontos não mudam.

## Categorias (registro de cada seção como o TSE publica)

| categoria | nome | seções | eleitores |
|---|---|---|---|
| A | retorno ao original | 754 | 222.482 |
| B | nova realocação | 255 | 72.878 |
| C | de um temporário para outro | 26 | 9.088 |
| D | mesmo número, nome e endereço mudaram | 86 | 27.388 |
| E | mesmo número, endereço mudou | 220 | 57.308 |
| F | mesmo número, só o nome mudou | 208 | 66.456 |
| G | mesmo número, coordenada moveu mais de 300 m | 575 | 169.170 |
| H | mesmo número, coordenada moveu até 300 m | 1.034 | 284.030 |
| Z | igual | 514.021 | 157.836.663 |

Camada efetiva (agregada herda a principal):

| categoria | mudança real | seções | eleitores |
|---|---|---|---|
| A | sim | 781 | 225.624 |
| B | sim | 282 | 76.510 |
| C | não | 11 | 3.752 |
| C | sim | 15 | 5.336 |
| D | não | 15 | 4.307 |
| D | sim | 71 | 23.081 |
| E | não | 160 | 39.406 |
| E | sim | 62 | 18.017 |
| F | não | 208 | 66.456 |
| G | não | 587 | 170.694 |
| H | não | 1.034 | 283.975 |
| Z | não | 513.953 | 157.828.305 |

## Mudança real

- Seções: 1.211 (1.146 principais e 65 agregadas), 348.568 eleitores, 347.879 aptos nas urnas do 1º turno.
- Locais de origem 317, de destino 321, pares 334, municípios 212, UFs 26.
- Distância: mediana 382 m, p90 1.496 m (905 seções com distância confiável).
- Por categoria: A 781 seções / 225.624 eleitores; B 282 seções / 76.510 eleitores; C 15 seções / 5.336 eleitores; D 71 seções / 23.081 eleitores; E 62 seções / 18.017 eleitores
- Confiança média (E com outro logradouro, D com endereço igual): 72 seções.
- Fora do original: 1º turno 6.535 seções / 1.916.865 eleitores; 2º turno 6.036 / 1.767.261.
- Sensibilidade: G contaria 336 seções (106.262 eleitores); F com nome de outra instituição 34 seções.

## Confronto com os números públicos

- **TSE via Agência Brasil (17/10/2026), levantamento de 16/10** (16/10/2026 (dado citado pelo TSE)): hipótese mais próxima `qualquer_alteracao_a_h` (qualquer alteração de cadastro (A a H)), 3.158 seções contra 4.352 (-27,44%). Não explica: A contagem de seções difere -27,4% (3.158 contra 4.352). RJ 431 não aparece em nenhum recorte do arquivo de 18/10 (máximo 47). SP: 302 contra 982. MG: 321 contra 514. BA: 454 contra 312.
- **Relatório anexo à petição da coligação Brasil Pronto pra Mais (TSE 0603126-92.2026.6.00.0000), relatório de 17/10/2026 às 6h28** (17/10/2026 06:28): hipótese mais próxima `fora_do_original_2t` (seções que no 2º turno votam fora do local original do cadastro), 6.036 seções contra 4.864 (24,10%), 1.767.261 eleitores contra 1.795.241 (-1,56%). Não explica: A contagem de seções difere +24,1% (6.036 contra 4.864).
- **Revista Fórum, exportação do sistema do TSE; O Tempo/Folhapress: 2.033 seções e 592 mil eleitores** (18/10/2026 11:27): hipótese mais próxima `alteracao_sem_ajuste_de_coordenada_a_g` (alteração de número, nome, endereço ou coordenada acima de 300 m (A a G)), 2.124 seções contra 2.033 (4,48%), 624.770 eleitores contra 592.870 (5,38%). Não explica: A contagem de seções difere +4,5% (2.124 contra 2.033). Os eleitores diferem +5,4%.
- **Portal de Estatísticas do TSE, painel Seções Eleitorais Alteradas no Segundo Turno** (18/10/2026 20:27): hipótese mais próxima `numero_de_local_mudou_abcx` (número do local mudou entre os arquivos (A, B, C, X)), 1.035 seções contra 1.106 (-6,42%), 304.448 eleitores contra 321.382 (-5,27%). Não explica: A contagem de seções difere -6,4% (1.035 contra 1.106). Os eleitores diferem -5,3%.

## Painel do TSE contra o arquivo de locais

União 1.175; ambos 966; só painel 140; só arquivo 69; concordância 82,21%. Nos que constam dos dois, nomes conferem em 966 e o eleitorado é 286.517 no painel contra 286.517 no arquivo.

Nas 140 seções só do painel, 137 têm no painel como local final o local original do cadastro, enquanto o arquivo de locais as mantém no temporário nos dois turnos. Nas 69 só do arquivo, 68 são novas realocações (original no 1º turno, temporário no 2º) que o painel não lista.

Nas seções só do painel cujo local final é o original, o endereço do original (nome e endereço da própria linha do arquivo) foi preenchido em 137; bairro e CEP em 15 e coordenada em 15, tirados de outra seção que vota nesse local no 2º turno, no mesmo município e zona.

Seções de mesmo número com prédio trocado (D e E): 306 no arquivo, 133 com mudança real; listadas no painel: 0. O painel lista troca de local (inicial e final); seção que mantém o número e muda de prédio (D e E) fica de fora, inclusive o caso confirmado pelo TRE-RJ (zona 188, seções 123 a 127).

## Distância

- Novas realocações: mediana 385 m (IC 95% 141 a 573); acima de 1 km 12,70% (IC 95% 4,20 a 23,30); acima de 2 km 4,20% (IC 95% 1,30 a 8,40).
- Categoria A no 1º turno: mediana 382 m (IC 95% 286 a 455).
- Prédio vizinho (país): mediana 407 m (IC 95% 403 a 411); das origens das novas: 431 m (IC 95% 295 a 586).
- Diferenças: novas menos A 3,00 m (IC 95% -270 a 210); novas menos vizinho -21,00 m (IC 95% -267 a 163).

## Comportamento no 1º turno

- mudanca_real (1.137 urnas): abstenção contra o município 0,33 pp (IC 95% 0,17 a 0,54), contra o país -0,42 pp (IC 95% -0,94 a 0,13); Flávio nos válidos contra o município 0,16 pp (IC 95% -0,14 a 0,69), contra o país -5,39 pp (IC 95% -7,37 a -3,34); Lula contra o município -0,03 pp (IC 95% -0,60 a 0,28).
- A (754 urnas): abstenção contra o município 0,33 pp (IC 95% 0,10 a 0,60), contra o país -0,83 pp (IC 95% -1,47 a -0,16); Flávio nos válidos contra o município -0,02 pp (IC 95% -0,43 a 0,64), contra o país -6,78 pp (IC 95% -9,28 a -4,26); Lula contra o município 0,25 pp (IC 95% -0,49 a 0,68).
- novas (383 urnas): abstenção contra o município 0,33 pp (IC 95% 0,09 a 0,60), contra o país 0,38 pp (IC 95% -0,54 a 1,25); Flávio nos válidos contra o município 0,51 pp (IC 95% 0,05 a 1,16), contra o país -2,66 pp (IC 95% -6,25 a 0,79); Lula contra o município -0,57 pp (IC 95% -1,29 a -0,10).
- Teste da categoria A: Sim: +0,33 ponto, IC 95% de +0,10 a +0,60.

## Intercorrências no 1º turno (razão contra o país)

- mudanca_real: bateria 1,14 (IC 95% 0,96 a 1,34); bateria_votacao 1,31 (IC 95% 1,02 a 1,64); reinicio 1,68 (IC 95% 0,96 a 2,65); abertura_atrasada 8,82 (IC 95% 1,80 a 20,54); fila_fechamento 1,66 (IC 95% 1,28 a 2,10); atencao_2_ou_3 2,05 (IC 95% 1,14 a 3,44).
- A: bateria 1,00 (IC 95% 0,79 a 1,21); bateria_votacao 1,02 (IC 95% 0,72 a 1,37); reinicio 1,14 (IC 95% 0,66 a 1,67); abertura_atrasada 1,31 (IC 95% 0,00 a 3,47); fila_fechamento 1,52 (IC 95% 1,04 a 2,05); atencao_2_ou_3 1,64 (IC 95% 0,98 a 2,35).
- novas: bateria 1,42 (IC 95% 1,06 a 1,82); bateria_votacao 1,88 (IC 95% 1,33 a 2,49); reinicio 2,75 (IC 95% 0,91 a 5,33); abertura_atrasada 23,55 (IC 95% 3,71 a 56,65); fila_fechamento 1,94 (IC 95% 1,28 a 2,65); atencao_2_ou_3 2,85 (IC 95% 0,79 a 6,49).
- temp_1t: bateria 1,02 (IC 95% 0,95 a 1,09); bateria_votacao 0,99 (IC 95% 0,87 a 1,11); reinicio 1,00 (IC 95% 0,86 a 1,15); abertura_atrasada 0,68 (IC 95% 0,24 a 1,18); fila_fechamento 1,20 (IC 95% 1,06 a 1,35); atencao_2_ou_3 1,18 (IC 95% 0,98 a 1,38).

## Efeito medido no 1º turno

Rótulo: Diferença medida com controles por município e por 2022, não efeito causal identificado: a escolha dos locais pelo TRE não é aleatória.

- Tratamento: 6.535 seções / 1.916.865 eleitores no cadastro; 6.534 urnas com boletim no Brasil.
- Abstenção contra o município: 0,66 pp (IC 95% 0,55 a 0,79); contra o país: -0,66 pp (IC 95% -0,91 a -0,41).
- Diferença em diferenças (2026 1T menos 2022 2T): 0,53 pp (IC 95% 0,40 a 0,65) contra estáveis do município; cobertura 79,40%.
- Direção: Flávio 0,43 pp (IC 95% 0,25 a 0,71); Lula -0,46 pp (IC 95% -0,79 a -0,26) (contra o município).
- Troca de prédio desde 2022: 8.062 urnas; diferença em diferenças 0,32 pp (IC 95% 0,20 a 0,45).
- Dose e resposta (categoria A, diferença em diferenças contra o município): até 500 m (291 urnas) 0,52 pp (IC 95% 0,14 a 0,90); 500 m a 1 km (136 urnas) 0,02 pp (IC 95% -0,36 a 0,51); 1 a 2 km (36 urnas) 0,93 pp (IC 95% 0,72 a 1,21); 2 a 5 km (13 urnas) 1,15 pp (IC 95% 0,24 a 2,23); acima de 5 km (19 urnas) 2,43 pp (IC 95% 0,68 a 4,14); sem distância confiável (131 urnas) -0,02 pp (IC 95% -0,46 a 0,35)
- Rio de Janeiro, transferidas contra estáveis da mesma zona: abstenção 1,99 pp (IC 95% 1,35 a 2,64), diferença em diferenças 1,65 pp (IC 95% 1,21 a 2,15).
- Zona 161 (Maré): 211 urnas, abstenção da zona 28,46% (ConJur: 28,46%); 49 urnas com prédio trocado desde 2022; abstenção 1T transferidas 29,77% contra estáveis 27,22%; variação desde 2022 8,45 contra 3,95 pp, diferença em diferenças 4,50 pp.
- No cadastro de 02/10, as transferências do TRE-RJ não aparecem como local diferente do original: o número do local foi mantido e o nome e o endereço foram trocados. Por isso a regra local diferente do original não marca nenhuma urna no município do Rio; o grupo troca desde 2022 é a forma de enxergá-las.

## Cenários

- +2,00 pontos nas urnas com mudança real: Flávio perde 2.748, Lula 3.459; diferença F menos L varia 711 votos (0,0006 ponto dos válidos).
- +5,00 pontos nas urnas com mudança real: Flávio perde 6.869, Lula 8.647; diferença F menos L varia 1.778 votos (0,0015 ponto dos válidos).
- +10,00 pontos nas urnas com mudança real: Flávio perde 13.738, Lula 17.293; diferença F menos L varia 3.555 votos (0,0030 ponto dos válidos).
- +20,00 pontos nas urnas com mudança real: Flávio perde 27.476, Lula 34.586; diferença F menos L varia 7.110 votos (0,0060 ponto dos válidos).
- Estimativa brasileira (0,53 ponto, IC 0,40 a 0,65): nas 6.035 urnas fora do original em 25/10, Flávio perde 3.996 e Lula 4.564 em relação a votar no original; diferença entre os dois: 568 votos a favor de Flávio.
- Saldo entre turnos (novas perdem, A recupera): 102 votos a favor de Lula.
- Teto pelo Rio (1,65 ponto): nas urnas fora do original, Flávio perde 12.440 e Lula 14.207; diferença: 1.768 votos a favor de Flávio.

## Quem perde

- As 1.146 urnas com mudança real deram no 1º turno 41,42% dos válidos a Flávio e 52,10% a Lula. Com 2 pontos a mais de abstenção nelas, Flávio perderia 2.748 votos e Lula 3.459; a diferença entre os dois mudaria 711 votos a favor de Flávio (0,0006 ponto dos válidos nacionais do 1º turno). Quem perde mais voto é Lula, porque teve mais voto nessas urnas que Flávio.
- Na direção contrária, as urnas da categoria A voltam ao prédio original. Se recuperarem o comparecimento na magnitude medida no 1º turno (0,53 ponto, IC 95% de 0,40 a 0,65), Flávio ganharia 460 votos e Lula 605. Somando a perda das novas realocações e o ganho da categoria A, a diferença entre os dois varia 102 votos a favor de Lula (0,0001 ponto dos válidos nacionais).

## Clima e notas dos TREs

- Clima: ok.
  - origem_mudanca_real: 315 locais com dado; chuva em 04/10 acima de 20 mm 5,10%, acima de 50 mm 0,00%; máximo de 05 a 18/10 acima de 20 mm 23,80%, acima de 50 mm 3,50%; rajada acima de 60 km/h 11.
  - origem_qualquer_alteracao: 531 locais com dado; chuva em 04/10 acima de 20 mm 3,60%, acima de 50 mm 0,00%; máximo de 05 a 18/10 acima de 20 mm 22,60%, acima de 50 mm 2,30%; rajada acima de 60 km/h 11.
  - controle: 1.500 locais com dado; chuva em 04/10 acima de 20 mm 4,10%, acima de 50 mm 0,00%; máximo de 05 a 18/10 acima de 20 mm 31,70%, acima de 50 mm 2,90%; rajada acima de 60 km/h 67.
  - origem com mudança real menos controle: máximo de 05 a 18/10 acima de 20 mm -7,90 pp (IC 95% -13,10 a -2,90); chuva em 04/10 acima de 20 mm 0,90 pp (IC 95% -1,50 a 3,90); rajada acima de 60 km/h -1,00 pp (IC 95% -3,10 a 1,40); sem chuva acima de 10 mm nem rajada acima de 50 km/h no período: 109 locais de origem.
- Notas dos TREs: 37 itens lidos; 39 pares de locais casados com alguma nota ({'local': 28, 'municipio': 9, 'zona': 2})

## Limites

- Comparação, não efeito causal: o TRE escolhe quais locais mudar e por quê; seções com local temporário não são sorteadas.
- O cadastro de 18/10 ainda pode mudar até 25/10, e o painel do TSE com o mesmo carimbo de hora diverge do arquivo de locais em parte das seções.
- A distância é em linha reta entre as coordenadas do TSE, não o caminho a pé; coordenada repetida por três ou mais locais do município é marcador de posição e fica fora das estatísticas de distância.
- Nome e endereço iguais com coordenada diferente (categoria G) e troca só de nome (F) não contam como mudança real: o eleitor vai ao mesmo prédio. A sensibilidade está no resumo.
- Seção agregada vota na urna da principal e herda a classificação dela.
- Os cenários usam a composição do 1º turno de cada urna; no 2º turno o voto das demais candidaturas se redistribui. É a conta do tamanho, não previsão.
- Leitura agregada por seção: o voto é secreto e nada aqui identifica eleitor.
- Registro de bateria, reinício ou fila no log é registro operacional, não irregularidade.
- No Rio de Janeiro, as transferências por segurança no 1º turno mantiveram o número do local e trocaram nome e endereço; a regra local diferente do original não as enxerga, e o grupo troca desde 2022 também inclui renomeação de escola.
- O exterior fica fora das comparações nacionais de comportamento e intercorrências.
- As notas dos TREs casam por UF e município; só o grau local indica a mesma seção ou o mesmo prédio. Motivo ausente na nota fica como não informado.

## Reprodução

```
python3 scripts/mudancas-secoes-2t.py
pytest -q tests/test_mudancas_secoes_2t.py
ruff check scripts/mudancas_secoes_2t scripts/mudancas-secoes-2t.py tests/test_mudancas_secoes_2t.py
```
