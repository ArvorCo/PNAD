# Logs das urnas: 1º × 2º turno, seção a seção

Rótulo: pede explicação, não prova irregularidade.

- Seções com log analisado: 1º turno 499176, 2º turno 499176, nos dois 499174.
- Atenção 2 ou mais no 2º turno entre as que tinham 2 ou mais no 1º: {'secoes_1t': 10168, 'pct_2t_dado_1t': 15.598, 'pct_2t_geral': 1.892}.
- Atenção 3 nos dois: {'secoes_1t': 1918, 'pct_2t_dado_1t': 6.1, 'pct_2t_geral': 0.206}.

## Matriz de atenção (1º turno x 2º turno)

| 1T \ 2T | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| 0 | 334082 | 62757 | 4013 | 258 |
| 1 | 57877 | 26432 | 3099 | 488 |
| 2 | 3534 | 3584 | 968 | 164 |
| 3 | 620 | 844 | 337 | 117 |

## Diagnósticos

| Diagnóstico | nos dois | só 1T | só 2T |
|---|---|---|---|
| Falha declarada de verificação de assinatura | 0 | 18 | 8 |
| Operação com bateria registrada | 38294 | 78722 | 66641 |
| Passagem para bateria durante a votação, só nesta urna | 1573 | 11095 | 10279 |
| Passagem para bateria durante a votação, junto com outras urnas do município | 4888 | 36923 | 33506 |
| Habilitação biográfica acima da referência | 550 | 956 | 842 |
| Categorias de habilitação não reconciliadas | 0 | 10 | 6 |
| Cancelamentos de habilitação acima da referência | 925 | 5276 | 1712 |
| Ciclo de votação não reconstruído | 130 | 4414 | 1050 |
| Contagem do log não reconciliada com o BU | 0 | 10 | 6 |
| Erro técnico registrado no dia | 1755 | 3822 | 17823 |
| Identidade ou fase de parte dos registros não confirmada | 0 | 18 | 7 |
| Habilitação mais lenta que a referência | 157 | 438 | 238 |
| Janela de inspeção de cinco minutos ou mais | 9101 | 21402 | 69337 |
| Intervalo de 30 minutos entre cômputos | 9122 | 8228 | 26553 |
| Sistema ligado novamente durante a votação | 2344 | 13116 | 9927 |
| Aplicação reiniciada durante a votação | 2377 | 13301 | 10001 |
| Sequência temporal inconsistente ou relógio ajustado | 7 | 274 | 162 |
| Retomadas após inatividade acima da referência | 54 | 5447 | 94 |
| Eleitores sem biometria acima da referência | 5617 | 301 | 305 |
| Suspensões repetidas de votação | 8 | 3132 | 38 |
| Votação mais lenta que a referência | 10 | 845 | 33 |
| Estrutura ou texto crítico malformado | 2 | 0 | 0 |
| Zerésima anterior não localizada no pacote | 0 | 2 | 1 |

## Sinais novos do 2º turno

- Erro técnico: 497705 seções com ERRO/FATAL no dia; em 478127 o único erro é o do GAP ao desmontar a memória de resultado, antes da zerésima. GAP 'Problema ao desmontar a MR' antes da zerésima: urna religada no 2º turno com a carga de setembro. Desde a regra 2 (26/10/2026) esse erro sai do critério de erro técnico e fica em contagem própria (erro_mr_pre_zeresima).
- Urna do BU entre as que escreveram o log: {'True': 499176}.
- Código de carga do BU registrado no log da mesma urna: {'True': 499176} (None: o log não traz a cerimônia de carga da urna do BU).
- Seções com cadência horária confiável e 100 cômputos ou mais: 494035.

pede explicação, não prova irregularidade.
