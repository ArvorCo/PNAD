# Clima, bateria e abstenção no 1º turno de 2026: relatório do motor

Gerado em 2026-10-20T01:28:11+00:00 por `scripts/clima-1t.py` (2.000 réplicas, semente 20261004). Contrato em `analysis/clima_1t_2026/CONTRATO.md`; payload em `analysis/clima_1t_2026/clima.json`.

Registro de bateria é operação prevista da urna, não irregularidade; correlação não é causa; leitura agregada por seção e por local.

## Achados

- Bateria durante a votação e chuva nas horas de votação (efeito fixo de UF): cada 10 mm se associa a chances 1,39 vezes maiores (IC 95% 1,14 a 1,70).
- Bateria simultânea no município (assinatura de rede): cada 10 mm se associa a chances 1,53 vezes maiores (IC 95% 1,20 a 1,95).
- Bateria isolada (assinatura de tomada ou fonte): razão de chances de 0,95 por 10 mm (IC 95% 0,83 a 1,09), sem associação que se separe do acaso.
- Bateria durante a votação e rajada nas horas de votação: razão de chances de 1,00 por 10 km/h (IC 95% 0,90 a 1,11), sem associação que se separe do acaso.
- Dentro do mesmo município (probabilidade linear), bateria durante a votação: 2,55 pontos percentuais por 10 mm (IC 95% -2,98 a 8,09), que não se separa de zero.
- Abstenção de 2026 e chuva nas horas de votação, dentro do mesmo município: -0,17 ponto percentual por 10 mm (IC 95% -0,51 a 0,16), que não se separa de zero.
- Abstenção de 2026 menos a do 2º turno de 2022, dentro do mesmo município: 0,23 ponto percentual por 10 mm (IC 95% -0,08 a 0,55), que não se separa de zero.
- Abstenção das urnas com bateria durante a votação contra as do mesmo prédio sem bateria: 0,06 ponto percentual (IC 95% -0,03 a 0,13), que não se separa de zero.
- Mesma comparação dentro do prédio, na diferença contra 2022: 0,08 ponto percentual a mais (IC 95% 0,01 a 0,16).
- Cadeia completa (parcela de urnas com abstenção acima da mediana do município, que seria 50% sem relação nenhuma): sem chuva forte e sem bateria: 49,61% de 410.566 urnas; sem chuva forte e com bateria: 50,15% de 62.143 urnas; com chuva forte e sem bateria: 49,35% de 17.839 urnas; com chuva forte e com bateria: 51,05% de 5.303 urnas.
- Previsão para 25/10 gerada em 2026-10-20T01:12:23+00:00: 42.346.497 eleitores (26,92%) em células de risco alto e 53.702.777 (34,14%) em risco médio; a previsão muda todo dia.

## Cobertura

- Células de 0,25° com local de votação: 6.539; com resposta da Open-Meteo: 6.539 (faltam 0); valores nulos: 0; requisições registradas: 69.
- Locais do Brasil: 95.115; com coordenada no território: 94.275; com clima: 94.275.
- Urnas do Brasil com boletim: 497.877; na amostra analítica (com clima e aptos): 496.051, em 6.516 células.

## Janela de votação e relógio

- Regra: das 7h às 18h de Brasília de 04/10 (horas 8 a 18 da série horária); a votação de 2026 foi das 8h às 17h de Brasília em todo o país; a janela tem uma hora de folga de cada lado.
- UTC-3 (maior parte do país): 7h às 18h locais.
- UTC-4 (AM, MT, MS, RO, RR): 6h às 17h locais.
- UTC-5 (AC e oeste do AM): 5h às 16h locais.
- UTC-2 (Fernando de Noronha): 8h às 19h locais.
- Sensibilidade: 8h às 17h de Brasília (horas 9 a 17), só o horário oficial, sem folga.
- Convenção: o valor horário da Open-Meteo na hora H é a chuva (ou a rajada máxima) da hora anterior, de H-1 a H.

## 1. Bateria e reinício contra chuva e vento

Unidade: urna (boletim do 1º turno, seção principal) com clima na célula do local. IC: bootstrap de células de 0,25° (2000 réplicas, percentis 2,5 e 97,5).

Denominadores:

- `bateria_votacao`: urnas com registro de operação com bateria interna durante a votação, entre as urnas com log lido e relógio válido.
- `bateria_qualquer`: urnas com registro de bateria interna em qualquer momento do log, entre as urnas com log lido.
- `reinicio`: urnas com reinício durante a votação, entre as urnas com log lido.
- `bateria_simultanea`: bateria durante a votação com 5 ou mais outras seções do município no mesmo minuto (±60 s), assinatura de fornecimento compartilhado; denominador: urnas com log e relógio válidos.
- `bateria_isolada`: bateria durante a votação sem nenhuma outra seção do município no mesmo minuto, assinatura de tomada, extensão ou fonte da própria urna; denominador: urnas com log e relógio válidos.
- `abertura_atrasada`: primeiro voto às 8h30 de Brasília ou depois, entre as urnas com hora de abertura.

### chuva nas horas de votação (7h às 18h de Brasília): `bateria_votacao`

| faixa | células | urnas | com registro | parcela | razão contra a referência |
|---|---|---|---|---|---|
| seca (0 mm) | 1.263 | 78.727 | 10.158 | 12,90% (IC 95% 11,35 a 14,78) | referência |
| fraca (até 5 mm) | 4.259 | 261.447 | 29.373 | 11,23% (IC 95% 10,46 a 12,13) | 0,87 (IC 95% 0,75 a 1,01) |
| moderada (5 a 20 mm) | 943 | 147.173 | 25.415 | 17,27% (IC 95% 15,45 a 19,47) | 1,34 (IC 95% 1,12 a 1,60) |
| forte (20 a 50 mm) | 50 | 8.463 | 2.500 | 29,54% (IC 95% 18,79 a 42,02) | 2,29 (IC 95% 1,44 a 3,29) |
| muito forte (acima de 50 mm) | 1 | 41 | 0 | 0,00% (menos de 20 células: sem intervalo de confiança) | 0,00 (menos de 20 células: sem intervalo de confiança) |

### chuva nas horas de votação (7h às 18h de Brasília): `bateria_simultanea`

| faixa | células | urnas | com registro | parcela | razão contra a referência |
|---|---|---|---|---|---|
| seca (0 mm) | 1.263 | 78.727 | 4.397 | 5,59% (IC 95% 4,41 a 6,95) | referência |
| fraca (até 5 mm) | 4.259 | 261.447 | 14.694 | 5,62% (IC 95% 4,99 a 6,34) | 1,01 (IC 95% 0,78 a 1,32) |
| moderada (5 a 20 mm) | 943 | 147.173 | 20.329 | 13,81% (IC 95% 11,90 a 15,77) | 2,47 (IC 95% 1,91 a 3,28) |
| forte (20 a 50 mm) | 50 | 8.463 | 2.271 | 26,83% (IC 95% 15,79 a 39,46) | 4,80 (IC 95% 2,76 a 7,34) |
| muito forte (acima de 50 mm) | 1 | 41 | 0 | 0,00% (menos de 20 células: sem intervalo de confiança) | 0,00 (menos de 20 células: sem intervalo de confiança) |

### chuva nas horas de votação (7h às 18h de Brasília): `bateria_isolada`

| faixa | células | urnas | com registro | parcela | razão contra a referência |
|---|---|---|---|---|---|
| seca (0 mm) | 1.263 | 78.727 | 2.418 | 3,07% (IC 95% 2,49 a 3,64) | referência |
| fraca (até 5 mm) | 4.259 | 261.447 | 7.319 | 2,80% (IC 95% 2,63 a 3,00) | 0,91 (IC 95% 0,76 a 1,15) |
| moderada (5 a 20 mm) | 943 | 147.173 | 2.720 | 1,85% (IC 95% 1,49 a 2,27) | 0,60 (IC 95% 0,45 a 0,80) |
| forte (20 a 50 mm) | 50 | 8.463 | 133 | 1,57% (IC 95% 1,14 a 2,41) | 0,51 (IC 95% 0,35 a 0,81) |
| muito forte (acima de 50 mm) | 1 | 41 | 0 | 0,00% (menos de 20 células: sem intervalo de confiança) | 0,00 (menos de 20 células: sem intervalo de confiança) |

### chuva no dia 04/10: `bateria_votacao`

| faixa | células | urnas | com registro | parcela | razão contra a referência |
|---|---|---|---|---|---|
| seca (0 mm) | 921 | 37.611 | 5.464 | 14,53% (IC 95% 13,01 a 16,47) | referência |
| fraca (até 5 mm) | 3.673 | 225.560 | 25.584 | 11,34% (IC 95% 10,50 a 12,37) | 0,78 (IC 95% 0,67 a 0,90) |
| moderada (5 a 20 mm) | 1.639 | 209.538 | 31.095 | 14,84% (IC 95% 13,46 a 16,22) | 1,02 (IC 95% 0,88 a 1,19) |
| forte (20 a 50 mm) | 277 | 22.924 | 5.234 | 22,83% (IC 95% 18,41 a 27,93) | 1,57 (IC 95% 1,22 a 1,98) |
| muito forte (acima de 50 mm) | 6 | 218 | 69 | 31,65% (menos de 20 células: sem intervalo de confiança) | 2,18 (menos de 20 células: sem intervalo de confiança) |

### chuva no dia 04/10: `bateria_simultanea`

| faixa | células | urnas | com registro | parcela | razão contra a referência |
|---|---|---|---|---|---|
| seca (0 mm) | 921 | 37.611 | 1.954 | 5,20% (IC 95% 3,80 a 7,20) | referência |
| fraca (até 5 mm) | 3.673 | 225.560 | 12.588 | 5,58% (IC 95% 4,91 a 6,36) | 1,07 (IC 95% 0,76 a 1,52) |
| moderada (5 a 20 mm) | 1.639 | 209.538 | 23.086 | 11,02% (IC 95% 9,42 a 12,59) | 2,12 (IC 95% 1,49 a 2,96) |
| forte (20 a 50 mm) | 277 | 22.924 | 4.003 | 17,46% (IC 95% 12,89 a 22,61) | 3,36 (IC 95% 2,18 a 5,09) |
| muito forte (acima de 50 mm) | 6 | 218 | 60 | 27,52% (menos de 20 células: sem intervalo de confiança) | 5,30 (menos de 20 células: sem intervalo de confiança) |

### chuva no dia 04/10: `bateria_isolada`

| faixa | células | urnas | com registro | parcela | razão contra a referência |
|---|---|---|---|---|---|
| seca (0 mm) | 921 | 37.611 | 1.354 | 3,60% (IC 95% 3,32 a 3,90) | referência |
| fraca (até 5 mm) | 3.673 | 225.560 | 6.342 | 2,81% (IC 95% 2,56 a 3,11) | 0,78 (IC 95% 0,69 a 0,88) |
| moderada (5 a 20 mm) | 1.639 | 209.538 | 4.214 | 2,01% (IC 95% 1,72 a 2,33) | 0,56 (IC 95% 0,47 a 0,66) |
| forte (20 a 50 mm) | 277 | 22.924 | 671 | 2,93% (IC 95% 2,44 a 3,56) | 0,81 (IC 95% 0,67 a 1,01) |
| muito forte (acima de 50 mm) | 6 | 218 | 9 | 4,13% (menos de 20 células: sem intervalo de confiança) | 1,15 (menos de 20 células: sem intervalo de confiança) |

### rajada máxima nas horas de votação: `bateria_votacao`

| faixa | células | urnas | com registro | parcela | razão contra a referência |
|---|---|---|---|---|---|
| até 40 km/h | 3.844 | 194.139 | 24.269 | 12,50% (IC 95% 11,49 a 13,64) | referência |
| 40 a 60 km/h | 2.567 | 286.759 | 39.666 | 13,83% (IC 95% 12,74 a 15,12) | 1,11 (IC 95% 0,98 a 1,24) |
| 60 a 80 km/h | 104 | 14.583 | 3.451 | 23,66% (IC 95% 18,27 a 29,91) | 1,89 (IC 95% 1,44 a 2,41) |
| acima de 80 km/h | 1 | 370 | 60 | 16,22% (menos de 20 células: sem intervalo de confiança) | 1,30 (menos de 20 células: sem intervalo de confiança) |

### rajada máxima nas horas de votação: `bateria_simultanea`

| faixa | células | urnas | com registro | parcela | razão contra a referência |
|---|---|---|---|---|---|
| até 40 km/h | 3.844 | 194.139 | 12.256 | 6,31% (IC 95% 5,51 a 7,26) | referência |
| 40 a 60 km/h | 2.567 | 286.759 | 26.449 | 9,22% (IC 95% 7,97 a 10,55) | 1,46 (IC 95% 1,18 a 1,77) |
| 60 a 80 km/h | 104 | 14.583 | 2.942 | 20,17% (IC 95% 14,82 a 26,24) | 3,20 (IC 95% 2,29 a 4,28) |
| acima de 80 km/h | 1 | 370 | 44 | 11,89% (menos de 20 células: sem intervalo de confiança) | 1,88 (menos de 20 células: sem intervalo de confiança) |

### rajada máxima nas horas de votação: `bateria_isolada`

| faixa | células | urnas | com registro | parcela | razão contra a referência |
|---|---|---|---|---|---|
| até 40 km/h | 3.844 | 194.139 | 6.129 | 3,16% (IC 95% 2,95 a 3,39) | referência |
| 40 a 60 km/h | 2.567 | 286.759 | 6.215 | 2,17% (IC 95% 1,90 a 2,45) | 0,69 (IC 95% 0,59 a 0,79) |
| 60 a 80 km/h | 104 | 14.583 | 239 | 1,64% (IC 95% 1,31 a 2,06) | 0,52 (IC 95% 0,41 a 0,66) |
| acima de 80 km/h | 1 | 370 | 7 | 1,89% (menos de 20 células: sem intervalo de confiança) | 0,60 (menos de 20 células: sem intervalo de confiança) |

### rajada máxima no dia 04/10: `bateria_votacao`

| faixa | células | urnas | com registro | parcela | razão contra a referência |
|---|---|---|---|---|---|
| até 40 km/h | 3.462 | 161.563 | 20.630 | 12,77% (IC 95% 11,60 a 14,06) | referência |
| 40 a 60 km/h | 2.914 | 317.247 | 43.085 | 13,58% (IC 95% 12,56 a 14,76) | 1,06 (IC 95% 0,94 a 1,21) |
| 60 a 80 km/h | 139 | 16.671 | 3.671 | 22,02% (IC 95% 17,28 a 27,70) | 1,73 (IC 95% 1,32 a 2,20) |
| acima de 80 km/h | 1 | 370 | 60 | 16,22% (menos de 20 células: sem intervalo de confiança) | 1,27 (menos de 20 células: sem intervalo de confiança) |

### rajada máxima no dia 04/10: `bateria_simultanea`

| faixa | células | urnas | com registro | parcela | razão contra a referência |
|---|---|---|---|---|---|
| até 40 km/h | 3.462 | 161.563 | 10.751 | 6,65% (IC 95% 5,69 a 7,73) | referência |
| 40 a 60 km/h | 2.914 | 317.247 | 27.851 | 8,78% (IC 95% 7,58 a 10,00) | 1,32 (IC 95% 1,06 a 1,62) |
| 60 a 80 km/h | 139 | 16.671 | 3.045 | 18,27% (IC 95% 13,64 a 23,73) | 2,75 (IC 95% 1,96 a 3,72) |
| acima de 80 km/h | 1 | 370 | 44 | 11,89% (menos de 20 células: sem intervalo de confiança) | 1,79 (menos de 20 células: sem intervalo de confiança) |

### rajada máxima no dia 04/10: `bateria_isolada`

| faixa | células | urnas | com registro | parcela | razão contra a referência |
|---|---|---|---|---|---|
| até 40 km/h | 3.462 | 161.563 | 5.133 | 3,18% (IC 95% 2,95 a 3,45) | referência |
| 40 a 60 km/h | 2.914 | 317.247 | 7.160 | 2,26% (IC 95% 1,99 a 2,53) | 0,71 (IC 95% 0,61 a 0,81) |
| 60 a 80 km/h | 139 | 16.671 | 290 | 1,74% (IC 95% 1,41 a 2,18) | 0,55 (IC 95% 0,44 a 0,69) |
| acima de 80 km/h | 1 | 370 | 7 | 1,89% (menos de 20 células: sem intervalo de confiança) | 0,59 (menos de 20 células: sem intervalo de confiança) |

### Regressões logísticas

logística; efeito fixo de UF (indicadoras); controles: log dos aptos da seção e modelo da urna (UE2013, UE2015, UE2020, UE2022); erro-padrão por conglomerado de célula de 0,25°.

| desfecho | exposição | odds ratio | urnas | eventos |
|---|---|---|---|---|
| `bateria_votacao` | chuva nas horas de votação, por 10 mm | 1,393 (IC 95% 1,139 a 1,705; p = 0,001) | 495.851 | 67.446 |
| `bateria_votacao` | chuva no dia, por 10 mm | 1,335 (IC 95% 1,183 a 1,505; p < 0,001) | 495.851 | 67.446 |
| `bateria_votacao` | rajada nas horas de votação, por 10 km/h | 0,998 (IC 95% 0,898 a 1,110; p = 0,975) | 495.851 | 67.446 |
| `bateria_votacao` | rajada no dia, por 10 km/h | 1,009 (IC 95% 0,910 a 1,118; p = 0,868) | 495.851 | 67.446 |
| `bateria_votacao` | chuva nas horas de votação, por 10 mm | 1,395 (IC 95% 1,138 a 1,711; p = 0,001) | 495.851 | 67.446 |
| `bateria_votacao` | rajada nas horas de votação, por 10 km/h | 0,988 (IC 95% 0,889 a 1,098; p = 0,822) | 495.851 | 67.446 |
| `bateria_votacao` | chuva das 8h às 17h de Brasília, por 10 mm | 1,330 (IC 95% 1,070 a 1,652; p = 0,010) | 495.851 | 67.446 |
| `bateria_qualquer` | chuva no dia, por 10 mm | 1,229 (IC 95% 1,135 a 1,331; p < 0,001) | 496.049 | 116.557 |
| `bateria_qualquer` | rajada no dia, por 10 km/h | 1,010 (IC 95% 0,946 a 1,078; p = 0,772) | 496.049 | 116.557 |
| `reinicio` | chuva nas horas de votação, por 10 mm | 0,995 (IC 95% 0,880 a 1,125; p = 0,937) | 496.049 | 15.591 |
| `reinicio` | rajada nas horas de votação, por 10 km/h | 0,956 (IC 95% 0,922 a 0,992; p = 0,016) | 496.049 | 15.591 |
| `bateria_simultanea` | chuva nas horas de votação, por 10 mm | 1,533 (IC 95% 1,203 a 1,952; p < 0,001) | 495.851 | 41.691 |
| `bateria_simultanea` | rajada nas horas de votação, por 10 km/h | 1,028 (IC 95% 0,884 a 1,195; p = 0,721) | 495.851 | 41.691 |
| `bateria_isolada` | chuva nas horas de votação, por 10 mm | 0,948 (IC 95% 0,826 a 1,088; p = 0,446) | 495.851 | 12.590 |
| `bateria_isolada` | rajada nas horas de votação, por 10 km/h | 0,904 (IC 95% 0,853 a 0,957; p < 0,001) | 495.851 | 12.590 |
| `abertura_atrasada` | chuva no dia, por 10 mm | 0,909 (IC 95% 0,706 a 1,170; p = 0,459) | 496.049 | 1.002 |
| `abertura_atrasada` | rajada no dia, por 10 km/h | 0,840 (IC 95% 0,601 a 1,172; p = 0,304) | 496.049 | 1.002 |

probabilidade linear (pontos percentuais) com efeito fixo de município; compara urnas do mesmo município em células com chuva diferente:

- chuva nas horas de votação, por 10 mm: 2,552 pp (IC 95% -2,982 a 8,086; p = 0,366); 2.926 municípios informativos, 379.001 urnas.
- rajada nas horas de votação, por 10 km/h: 0,248 pp (IC 95% -1,074 a 1,571; p = 0,713); 3.509 municípios informativos, 412.790 urnas.

## 2. Abstenção contra chuva e vento

- `abst_pct`: abstenção do 1º turno de 2026, aptos menos comparecimento sobre aptos, razão de somas (ponderada por aptos).
- `dif_abst_pp`: abstenção de 2026 menos abstenção do 2º turno de 2022 nas mesmas seções (casadas por UF, município, zona e número), razão de somas de cada ano.

### chuva nas horas de votação (7h às 18h de Brasília)

| grupo | urnas | células | aptos | abstenção 2026 | contra a referência | 2026 menos 2022 | contra a referência |
|---|---|---|---|---|---|---|---|
| seca | 78.763 | 1.263 | 24.240.304 | 20,02% (IC 95% 18,88 a 21,27) | referência | -0,23 pp (IC 95% -0,76 a 0,28) | referência |
| fraca | 261.570 | 4.259 | 81.971.238 | 20,20% (IC 95% 19,73 a 20,67) | 0,19 pp (IC 95% -1,22 a 1,50) | -0,10 pp (IC 95% -0,46 a 0,25) | 0,13 pp (IC 95% -0,53 a 0,79) |
| moderada | 147.211 | 943 | 48.416.690 | 22,23% (IC 95% 21,85 a 22,55) | 2,22 pp (IC 95% 0,89 a 3,43) | 1,64 pp (IC 95% 1,29 a 1,89) | 1,87 pp (IC 95% 1,25 a 2,48) |
| forte | 8.466 | 50 | 2.660.951 | 22,88% (IC 95% 22,05 a 23,80) | 2,86 pp (IC 95% 1,33 a 4,47) | 1,50 pp (IC 95% 0,56 a 2,23) | 1,74 pp (IC 95% 0,69 a 2,69) |
| muito_forte | 41 | 1 | 10.053 | 16,88% (menos de 20 células: sem intervalo de confiança) | -3,14 pp (menos de 20 células: sem intervalo de confiança) | -5,19 pp (menos de 20 células: sem intervalo de confiança) | -4,95 pp (menos de 20 células: sem intervalo de confiança) |

Dentro da mesma UF (24 estratos com a referência e outro grupo):

- fraca: abstenção -0,74 pp (IC 95% -1,23 a 0,35); 2026 menos 2022 1,11 pp (IC 95% 0,48 a 1,75); 24 estratos.
- moderada: abstenção -0,38 pp (IC 95% -1,68 a 1,07); 2026 menos 2022 0,76 pp (IC 95% 0,23 a 1,92); 18 estratos.
- forte: abstenção 1,29 pp (menos de 10 estratos com os dois grupos: sem intervalo); 2026 menos 2022 1,28 pp (menos de 10 estratos com os dois grupos: sem intervalo); 4 estratos.
- muito_forte: abstenção sem dado; 2026 menos 2022 sem dado; 0 estratos.

Dentro do mesmo município (533 estratos com a referência e outro grupo):

- fraca: abstenção -0,08 pp (IC 95% -0,78 a 1,41); 2026 menos 2022 0,80 pp (IC 95% -0,49 a 1,71); 531 estratos.
- moderada: abstenção -4,83 pp (menos de 10 estratos com os dois grupos: sem intervalo); 2026 menos 2022 4,11 pp (menos de 10 estratos com os dois grupos: sem intervalo); 7 estratos.
- forte: abstenção -2,54 pp (menos de 10 estratos com os dois grupos: sem intervalo); 2026 menos 2022 -4,39 pp (menos de 10 estratos com os dois grupos: sem intervalo); 1 estratos.
- muito_forte: abstenção sem dado; 2026 menos 2022 sem dado; 0 estratos.

### chuva no dia 04/10

| grupo | urnas | células | aptos | abstenção 2026 | contra a referência | 2026 menos 2022 | contra a referência |
|---|---|---|---|---|---|---|---|
| seca | 37.622 | 921 | 10.947.187 | 19,33% (IC 95% 18,87 a 19,78) | referência | -1,25 pp (IC 95% -1,56 a -0,97) | referência |
| fraca | 225.695 | 3.673 | 70.835.904 | 20,17% (IC 95% 19,50 a 20,88) | 0,84 pp (IC 95% 0,06 a 1,67) | -0,37 pp (IC 95% -0,83 a 0,06) | 0,88 pp (IC 95% 0,35 a 1,40) |
| moderada | 209.585 | 1.639 | 68.327.555 | 21,71% (IC 95% 21,30 a 22,07) | 2,39 pp (IC 95% 1,79 a 2,96) | 1,45 pp (IC 95% 1,17 a 1,69) | 2,70 pp (IC 95% 2,28 a 3,10) |
| forte | 22.931 | 277 | 7.121.535 | 21,48% (IC 95% 20,90 a 22,01) | 2,16 pp (IC 95% 1,41 a 2,82) | 1,35 pp (IC 95% 0,98 a 1,69) | 2,60 pp (IC 95% 2,15 a 3,06) |
| muito_forte | 218 | 6 | 67.055 | 25,88% (menos de 20 células: sem intervalo de confiança) | 6,55 pp (menos de 20 células: sem intervalo de confiança) | 2,77 pp (menos de 20 células: sem intervalo de confiança) | 4,02 pp (menos de 20 células: sem intervalo de confiança) |

Dentro da mesma UF (20 estratos com a referência e outro grupo):

- fraca: abstenção -0,63 pp (IC 95% -1,48 a 0,71); 2026 menos 2022 1,47 pp (IC 95% 0,76 a 2,89); 20 estratos.
- moderada: abstenção -1,53 pp (IC 95% -3,15 a 0,86); 2026 menos 2022 0,95 pp (IC 95% 0,35 a 4,21); 15 estratos.
- forte: abstenção -0,23 pp (menos de 10 estratos com os dois grupos: sem intervalo); 2026 menos 2022 0,58 pp (menos de 10 estratos com os dois grupos: sem intervalo); 7 estratos.
- muito_forte: abstenção 2,90 pp (menos de 10 estratos com os dois grupos: sem intervalo); 2026 menos 2022 1,61 pp (menos de 10 estratos com os dois grupos: sem intervalo); 1 estratos.

Dentro do mesmo município (341 estratos com a referência e outro grupo):

- fraca: abstenção -0,23 pp (IC 95% -1,14 a 0,86); 2026 menos 2022 1,02 pp (IC 95% 0,10 a 2,01); 340 estratos.
- moderada: abstenção -4,70 pp (menos de 10 estratos com os dois grupos: sem intervalo); 2026 menos 2022 4,13 pp (menos de 10 estratos com os dois grupos: sem intervalo); 5 estratos.
- forte: abstenção -2,54 pp (menos de 10 estratos com os dois grupos: sem intervalo); 2026 menos 2022 -4,39 pp (menos de 10 estratos com os dois grupos: sem intervalo); 1 estratos.
- muito_forte: abstenção sem dado; 2026 menos 2022 sem dado; 0 estratos.

### rajada máxima nas horas de votação

| grupo | urnas | células | aptos | abstenção 2026 | contra a referência | 2026 menos 2022 | contra a referência |
|---|---|---|---|---|---|---|---|
| ate_40 | 194.193 | 3.844 | 59.900.699 | 20,72% (IC 95% 20,34 a 21,09) | referência | -0,09 pp (IC 95% -0,45 a 0,25) | referência |
| 40_60 | 286.902 | 2.567 | 92.467.921 | 20,85% (IC 95% 20,23 a 21,40) | 0,13 pp (IC 95% -0,59 a 0,80) | 0,75 pp (IC 95% 0,39 a 1,06) | 0,84 pp (IC 95% 0,34 a 1,33) |
| 60_80 | 14.586 | 104 | 4.809.805 | 22,33% (IC 95% 21,21 a 23,22) | 1,62 pp (IC 95% 0,46 a 2,56) | 1,31 pp (IC 95% 0,17 a 2,32) | 1,40 pp (IC 95% 0,21 a 2,47) |
| acima_80 | 370 | 1 | 120.811 | 22,92% (menos de 20 células: sem intervalo de confiança) | 2,21 pp (menos de 20 células: sem intervalo de confiança) | 0,06 pp (menos de 20 células: sem intervalo de confiança) | 0,15 pp (menos de 20 células: sem intervalo de confiança) |

Dentro da mesma UF (26 estratos com a referência e outro grupo):

- 40_60: abstenção -0,87 pp (IC 95% -1,49 a -0,22); 2026 menos 2022 0,89 pp (IC 95% 0,40 a 1,67); 26 estratos.
- 60_80: abstenção -0,26 pp (IC 95% -1,99 a 1,18); 2026 menos 2022 0,93 pp (IC 95% -0,55 a 2,46); 13 estratos.
- acima_80: abstenção 1,58 pp (menos de 10 estratos com os dois grupos: sem intervalo); 2026 menos 2022 0,10 pp (menos de 10 estratos com os dois grupos: sem intervalo); 1 estratos.

Dentro do mesmo município (957 estratos com a referência e outro grupo):

- 40_60: abstenção 0,19 pp (IC 95% -0,71 a 0,96); 2026 menos 2022 -0,28 pp (IC 95% -1,00 a 0,61); 954 estratos.
- 60_80: abstenção 0,48 pp (IC 95% -1,70 a 1,81); 2026 menos 2022 -0,47 pp (IC 95% -2,18 a 0,83); 20 estratos.
- acima_80: abstenção sem dado; 2026 menos 2022 sem dado; 0 estratos.

### rajada máxima no dia 04/10

| grupo | urnas | células | aptos | abstenção 2026 | contra a referência | 2026 menos 2022 | contra a referência |
|---|---|---|---|---|---|---|---|
| ate_40 | 161.612 | 3.462 | 49.740.586 | 20,95% (IC 95% 20,53 a 21,36) | referência | -0,25 pp (IC 95% -0,70 a 0,16) | referência |
| 40_60 | 317.395 | 2.914 | 101.955.953 | 20,72% (IC 95% 20,14 a 21,24) | -0,23 pp (IC 95% -0,91 a 0,41) | 0,74 pp (IC 95% 0,42 a 1,02) | 0,99 pp (IC 95% 0,47 a 1,52) |
| 60_80 | 16.674 | 139 | 5.481.886 | 22,16% (IC 95% 21,16 a 23,01) | 1,21 pp (IC 95% 0,15 a 2,15) | 1,29 pp (IC 95% 0,33 a 2,22) | 1,54 pp (IC 95% 0,48 a 2,58) |
| acima_80 | 370 | 1 | 120.811 | 22,92% (menos de 20 células: sem intervalo de confiança) | 1,97 pp (menos de 20 células: sem intervalo de confiança) | 0,06 pp (menos de 20 células: sem intervalo de confiança) | 0,31 pp (menos de 20 células: sem intervalo de confiança) |

Dentro da mesma UF (26 estratos com a referência e outro grupo):

- 40_60: abstenção -1,01 pp (IC 95% -1,63 a -0,39); 2026 menos 2022 0,77 pp (IC 95% 0,32 a 1,53); 26 estratos.
- 60_80: abstenção 0,04 pp (IC 95% -1,52 a 1,31); 2026 menos 2022 0,84 pp (IC 95% -0,49 a 2,36); 17 estratos.
- acima_80: abstenção 1,78 pp (menos de 10 estratos com os dois grupos: sem intervalo); 2026 menos 2022 0,46 pp (menos de 10 estratos com os dois grupos: sem intervalo); 1 estratos.

Dentro do mesmo município (1.044 estratos com a referência e outro grupo):

- 40_60: abstenção -0,30 pp (IC 95% -0,84 a 0,17); 2026 menos 2022 0,20 pp (IC 95% -0,15 a 0,67); 1.036 estratos.
- 60_80: abstenção 1,13 pp (IC 95% -0,74 a 4,17); 2026 menos 2022 0,21 pp (IC 95% -1,42 a 1,09); 32 estratos.
- acima_80: abstenção sem dado; 2026 menos 2022 sem dado; 0 estratos.

### Cortes binários

dois grupos por corte declarado, para que mais municípios tenham os dois lados; referência: o grupo de baixo.

#### chuva nas horas de votação (7h às 18h de Brasília), corte em 5

| grupo | urnas | células | aptos | abstenção 2026 | contra a referência | 2026 menos 2022 | contra a referência |
|---|---|---|---|---|---|---|---|
| até 5 mm | 340.333 | 5.522 | 106.211.542 | 20,16% (IC 95% 19,69 a 20,66) | referência | -0,13 pp (IC 95% -0,44 a 0,16) | referência |
| mais de 5 mm | 155.718 | 994 | 51.087.694 | 22,27% (IC 95% 21,92 a 22,56) | 2,11 pp (IC 95% 1,50 a 2,67) | 1,63 pp (IC 95% 1,30 a 1,88) | 1,76 pp (IC 95% 1,32 a 2,15) |

Dentro da mesma UF (20 estratos com a referência e outro grupo):

- mais de 5 mm: abstenção 0,69 pp (IC 95% -0,04 a 1,33); 2026 menos 2022 1,90 pp (IC 95% 1,34 a 2,42); 20 estratos.

Dentro do mesmo município (345 estratos com a referência e outro grupo):

- mais de 5 mm: abstenção 0,26 pp (IC 95% -0,61 a 1,19); 2026 menos 2022 0,30 pp (IC 95% -0,38 a 0,92); 345 estratos.

#### chuva no dia 04/10, corte em 20

| grupo | urnas | células | aptos | abstenção 2026 | contra a referência | 2026 menos 2022 | contra a referência |
|---|---|---|---|---|---|---|---|
| até 20 mm | 472.902 | 6.233 | 150.110.646 | 20,81% (IC 95% 20,40 a 21,21) | referência | 0,40 pp (IC 95% 0,11 a 0,66) | referência |
| mais de 20 mm | 23.149 | 283 | 7.188.590 | 21,53% (IC 95% 20,96 a 22,04) | 0,71 pp (IC 95% 0,03 a 1,37) | 1,36 pp (IC 95% 0,99 a 1,70) | 0,96 pp (IC 95% 0,50 a 1,42) |

Dentro da mesma UF (12 estratos com a referência e outro grupo):

- mais de 20 mm: abstenção -0,20 pp (IC 95% -0,80 a 0,30); 2026 menos 2022 -0,33 pp (IC 95% -0,75 a 0,14); 12 estratos.

Dentro do mesmo município (219 estratos com a referência e outro grupo):

- mais de 20 mm: abstenção -0,14 pp (IC 95% -1,32 a 1,24); 2026 menos 2022 0,40 pp (IC 95% -0,55 a 1,63); 219 estratos.

#### rajada máxima nas horas de votação, corte em 60

| grupo | urnas | células | aptos | abstenção 2026 | contra a referência | 2026 menos 2022 | contra a referência |
|---|---|---|---|---|---|---|---|
| até 60 km/h | 481.095 | 6.411 | 152.368.620 | 20,80% (IC 95% 20,39 a 21,18) | referência | 0,42 pp (IC 95% 0,14 a 0,67) | referência |
| mais de 60 km/h | 14.956 | 105 | 4.930.616 | 22,35% (IC 95% 21,26 a 23,21) | 1,55 pp (IC 95% 0,41 a 2,50) | 1,28 pp (IC 95% 0,17 a 2,29) | 0,86 pp (IC 95% -0,30 a 1,90) |

Dentro da mesma UF (13 estratos com a referência e outro grupo):

- mais de 60 km/h: abstenção -0,33 pp (IC 95% -1,35 a 0,79); 2026 menos 2022 0,06 pp (IC 95% -1,09 a 1,27); 13 estratos.

Dentro do mesmo município (115 estratos com a referência e outro grupo):

- mais de 60 km/h: abstenção 0,07 pp (IC 95% -1,37 a 1,88); 2026 menos 2022 0,33 pp (IC 95% -0,80 a 1,28); 115 estratos.

### Chuva forte e bateria

chuva forte = mais de 20 mm no dia 04/10; bateria = registro durante a votação; urnas com log e relógio válidos.

| grupo | urnas | células | aptos | abstenção 2026 | contra a referência | 2026 menos 2022 | contra a referência |
|---|---|---|---|---|---|---|---|
| sem chuva forte, sem bateria | 410.566 | 5.668 | 130.889.232 | 20,76% (IC 95% 20,33 a 21,18) | referência | 0,45 pp (IC 95% 0,17 a 0,71) | referência |
| sem chuva forte, com bateria | 62.143 | 4.434 | 19.160.123 | 21,17% (IC 95% 20,85 a 21,46) | 0,41 pp (IC 95% 0,16 a 0,67) | 0,07 pp (IC 95% -0,29 a 0,41) | -0,38 pp (IC 95% -0,59 a -0,18) |
| chuva forte, sem bateria | 17.839 | 251 | 5.573.569 | 21,23% (IC 95% 20,66 a 21,78) | 0,47 pp (IC 95% -0,22 a 1,16) | 1,25 pp (IC 95% 0,89 a 1,59) | 0,80 pp (IC 95% 0,35 a 1,27) |
| chuva forte, com bateria | 5.303 | 252 | 1.612.721 | 22,54% (IC 95% 21,71 a 23,24) | 1,78 pp (IC 95% 0,85 a 2,58) | 1,74 pp (IC 95% 1,16 a 2,16) | 1,29 pp (IC 95% 0,67 a 1,79) |

Dentro do mesmo município (4.005 estratos com a referência e outro grupo):

- sem chuva forte, com bateria: abstenção 0,09 pp (IC 95% 0,00 a 0,21); 2026 menos 2022 0,10 pp (IC 95% 0,02 a 0,21); 3.934 estratos.
- chuva forte, sem bateria: abstenção 0,53 pp (IC 95% -0,82 a 2,10); 2026 menos 2022 0,70 pp (IC 95% -0,23 a 2,24); 169 estratos.
- chuva forte, com bateria: abstenção -0,18 pp (IC 95% -1,88 a 1,46); 2026 menos 2022 -0,16 pp (IC 95% -1,59 a 0,93); 112 estratos.

### Regressões lineares

mínimos quadrados ponderados por aptos (abstenção) ou por aptos casados (diferença contra 2022); efeito fixo de UF com log dos aptos, e efeito fixo de município; erro-padrão por conglomerado de célula; coeficientes em pontos percentuais por 10 mm ou por 10 km/h.

| medida | exposição | efeito fixo | coeficiente | urnas |
|---|---|---|---|---|
| abstenção de 2026 | chuva nas horas de votação, por 10 mm | UF | -0,227 pp (IC 95% -0,756 a 0,302; p = 0,400) | 496.051 |
| abstenção de 2026 | chuva nas horas de votação, por 10 mm | município | -0,174 pp (IC 95% -0,506 a 0,158; p = 0,303) | 379.158 |
| abstenção de 2026 | chuva no dia, por 10 mm | UF | -0,526 pp (IC 95% -0,862 a -0,190; p = 0,002) | 496.051 |
| abstenção de 2026 | chuva no dia, por 10 mm | município | 0,113 pp (IC 95% -0,331 a 0,557; p = 0,618) | 395.646 |
| abstenção de 2026 | rajada nas horas de votação, por 10 km/h | UF | -0,207 pp (IC 95% -0,453 a 0,040; p = 0,100) | 496.051 |
| abstenção de 2026 | rajada nas horas de votação, por 10 km/h | município | -0,001 pp (IC 95% -0,368 a 0,366; p = 0,996) | 412.933 |
| abstenção de 2026 | rajada no dia, por 10 km/h | UF | -0,340 pp (IC 95% -0,584 a -0,095; p = 0,006) | 496.051 |
| abstenção de 2026 | rajada no dia, por 10 km/h | município | -0,030 pp (IC 95% -0,365 a 0,304; p = 0,859) | 413.744 |
| abstenção de 2026 | chuva das 8h às 17h de Brasília, por 10 mm | UF | -0,341 pp (IC 95% -0,940 a 0,259; p = 0,265) | 496.051 |
| abstenção de 2026 | chuva das 8h às 17h de Brasília, por 10 mm | município | -0,249 pp (IC 95% -0,590 a 0,091; p = 0,152) | 375.153 |
| 2026 menos 2022 | chuva nas horas de votação, por 10 mm | UF | 0,297 pp (IC 95% -0,060 a 0,655; p = 0,103) | 458.736 |
| 2026 menos 2022 | chuva nas horas de votação, por 10 mm | município | 0,232 pp (IC 95% -0,081 a 0,546; p = 0,147) | 347.949 |
| 2026 menos 2022 | chuva no dia, por 10 mm | UF | 0,084 pp (IC 95% -0,115 a 0,283; p = 0,407) | 458.736 |
| 2026 menos 2022 | chuva no dia, por 10 mm | município | -0,023 pp (IC 95% -0,378 a 0,333; p = 0,901) | 363.714 |
| 2026 menos 2022 | rajada nas horas de votação, por 10 km/h | UF | 0,307 pp (IC 95% 0,125 a 0,488; p < 0,001) | 458.736 |
| 2026 menos 2022 | rajada nas horas de votação, por 10 km/h | município | 0,115 pp (IC 95% -0,221 a 0,451; p = 0,504) | 379.700 |
| 2026 menos 2022 | rajada no dia, por 10 km/h | UF | 0,245 pp (IC 95% 0,071 a 0,419; p = 0,006) | 458.736 |
| 2026 menos 2022 | rajada no dia, por 10 km/h | município | 0,169 pp (IC 95% -0,122 a 0,460; p = 0,255) | 380.481 |
| 2026 menos 2022 | chuva das 8h às 17h de Brasília, por 10 mm | UF | 0,318 pp (IC 95% -0,079 a 0,716; p = 0,117) | 458.736 |
| 2026 menos 2022 | chuva das 8h às 17h de Brasília, por 10 mm | município | 0,274 pp (IC 95% -0,045 a 0,593; p = 0,092) | 344.297 |

Interação chuva × bateria (chuva_votacao_x (por 10 mm), bat (bateria durante a votação), chuva_x_bat):

- abstenção de 2026, UF, chuva nas horas de votação, por 10 mm: -0,338 pp (IC 95% -0,870 a 0,194; p = 0,213).
- abstenção de 2026, UF, bateria durante a votação: 0,041 pp (IC 95% -0,183 a 0,265; p = 0,719).
- abstenção de 2026, UF, chuva × bateria: 0,453 pp (IC 95% 0,143 a 0,764; p = 0,004).
- abstenção de 2026, município, chuva nas horas de votação, por 10 mm: -0,192 pp (IC 95% -0,533 a 0,149; p = 0,270).
- abstenção de 2026, município, bateria durante a votação: 0,061 pp (IC 95% -0,034 a 0,157; p = 0,208).
- abstenção de 2026, município, chuva × bateria: 0,087 pp (IC 95% -0,094 a 0,268; p = 0,347).
- 2026 menos 2022, município, chuva nas horas de votação, por 10 mm: 0,209 pp (IC 95% -0,100 a 0,518; p = 0,186).
- 2026 menos 2022, município, bateria durante a votação: 0,040 pp (IC 95% -0,022 a 0,101; p = 0,203).
- 2026 menos 2022, município, chuva × bateria: 0,115 pp (IC 95% 0,003 a 0,227; p = 0,044).

## 3. Abstenção contra bateria

- Denominador: urnas com log lido e relógio válido.
- Tempo em bateria: não medido: o log diz que a urna operou com bateria, não por quanto tempo, nem se a fila parou.

| grupo | urnas | células | aptos | abstenção 2026 | contra a referência | 2026 menos 2022 | contra a referência |
|---|---|---|---|---|---|---|---|
| sem bateria durante a votação | 428.405 | 5.919 | 136.462.801 | 20,78% (IC 95% 20,36 a 21,18) | referência | 0,48 pp (IC 95% 0,22 a 0,73) | referência |
| com bateria durante a votação | 67.446 | 4.686 | 20.772.844 | 21,27% (IC 95% 20,97 a 21,55) | 0,50 pp (IC 95% 0,24 a 0,75) | 0,20 pp (IC 95% -0,14 a 0,53) | -0,28 pp (IC 95% -0,48 a -0,09) |

Dentro do mesmo município (4.185 estratos com a referência e outro grupo):

- com bateria durante a votação: abstenção 0,11 pp (IC 95% 0,02 a 0,23); 2026 menos 2022 0,10 pp (IC 95% 0,03 a 0,20); 4.185 estratos.

Dentro do mesmo prédio (14.438 estratos com a referência e outro grupo):

- com bateria durante a votação: abstenção 0,06 pp (IC 95% -0,03 a 0,13); 2026 menos 2022 0,08 pp (IC 95% 0,01 a 0,16); 14.438 estratos.

Por tipo de bateria:

| grupo | urnas | células | aptos | abstenção 2026 | contra a referência | 2026 menos 2022 | contra a referência |
|---|---|---|---|---|---|---|---|
| sem bateria durante a votação | 428.405 | 5.919 | 136.462.801 | 20,78% (IC 95% 20,36 a 21,18) | referência | 0,48 pp (IC 95% 0,22 a 0,73) | referência |
| simultânea (5 ou mais outras seções do município no mesmo minuto) | 41.691 | 1.665 | 13.116.905 | 21,78% (IC 95% 21,44 a 22,09) | 1,00 pp (IC 95% 0,67 a 1,35) | 0,51 pp (IC 95% 0,08 a 0,89) | 0,02 pp (IC 95% -0,29 a 0,30) |
| isolada (nenhuma outra seção do município no mesmo minuto) | 12.590 | 3.546 | 3.746.417 | 20,63% (IC 95% 20,39 a 20,86) | -0,15 pp (IC 95% -0,47 a 0,18) | -0,23 pp (IC 95% -0,46 a -0,03) | -0,72 pp (IC 95% -0,89 a -0,53) |
| intermediária (1 a 4 outras seções no mesmo minuto) | 13.165 | 2.428 | 3.909.522 | 20,18% (IC 95% 19,83 a 20,54) | -0,60 pp (IC 95% -0,83 a -0,36) | -0,40 pp (IC 95% -0,69 a -0,12) | -0,88 pp (IC 95% -1,07 a -0,69) |

Por tipo, dentro do mesmo município (4.185 estratos com a referência e outro grupo):

- simultânea (5 ou mais outras seções do município no mesmo minuto): abstenção 0,12 pp (IC 95% -0,04 a 0,30); 2026 menos 2022 0,11 pp (IC 95% -0,02 a 0,26); 1.063 estratos.
- isolada (nenhuma outra seção do município no mesmo minuto): abstenção 0,08 pp (IC 95% 0,00 a 0,17); 2026 menos 2022 0,15 pp (IC 95% 0,10 a 0,26); 3.622 estratos.
- intermediária (1 a 4 outras seções no mesmo minuto): abstenção 0,14 pp (IC 95% 0,04 a 0,24); 2026 menos 2022 0,04 pp (IC 95% -0,03 a 0,15); 2.011 estratos.

Por tipo, dentro do mesmo prédio (14.438 estratos com a referência e outro grupo):

- simultânea (5 ou mais outras seções do município no mesmo minuto): abstenção -0,02 pp (IC 95% -0,20 a 0,13); 2026 menos 2022 0,02 pp (IC 95% -0,12 a 0,16); 3.047 estratos.
- isolada (nenhuma outra seção do município no mesmo minuto): abstenção 0,12 pp (IC 95% 0,03 a 0,20); 2026 menos 2022 0,18 pp (IC 95% 0,09 a 0,26); 8.458 estratos.
- intermediária (1 a 4 outras seções no mesmo minuto): abstenção 0,10 pp (IC 95% -0,02 a 0,21); 2026 menos 2022 0,06 pp (IC 95% -0,06 a 0,17); 4.511 estratos.

MQP por aptos com efeito fixo de município; coeficiente de 'bat' em pontos percentuais:

- abstenção de 2026: 0,106 pp (IC 95% 0,011 a 0,202; p = 0,029); 466.464 urnas.
- 2026 menos 2022: 0,101 pp (IC 95% 0,049 a 0,154; p < 0,001); 429.676 urnas.

## 4. Cadeia completa

urnas com log e relógio válidos; abstenção alta = acima da mediana das urnas do mesmo município (empate na mediana não conta como alta).

### chuva forte no dia (mais de 20 mm)

| chuva | bateria | abstenção alta | urnas | aptos |
|---|---|---|---|---|
| não | não | não | 206.891 | 64.979.308 |
| não | não | sim | 203.675 | 65.909.924 |
| não | sim | não | 30.976 | 9.365.026 |
| não | sim | sim | 31.167 | 9.795.097 |
| sim | não | não | 9.035 | 2.798.675 |
| sim | não | sim | 8.804 | 2.774.894 |
| sim | sim | não | 2.596 | 780.250 |
| sim | sim | sim | 2.707 | 832.471 |

| chuva | bateria | urnas | abstenção acima da mediana do município |
|---|---|---|---|
| não | não | 410.566 | 49,61% |
| não | sim | 62.143 | 50,15% |
| sim | não | 17.839 | 49,35% |
| sim | sim | 5.303 | 51,05% |

### chuva moderada ou mais nas horas de votação (mais de 5 mm)

| chuva | bateria | abstenção alta | urnas | aptos |
|---|---|---|---|---|
| não | não | não | 151.685 | 46.658.484 |
| não | não | sim | 148.958 | 47.618.318 |
| não | sim | não | 19.689 | 5.762.791 |
| não | sim | sim | 19.842 | 6.122.189 |
| sim | não | não | 64.241 | 21.119.499 |
| sim | não | sim | 63.521 | 21.066.500 |
| sim | sim | não | 13.883 | 4.382.485 |
| sim | sim | sim | 14.032 | 4.505.379 |

| chuva | bateria | urnas | abstenção acima da mediana do município |
|---|---|---|---|
| não | não | 300.643 | 49,55% |
| não | sim | 39.531 | 50,19% |
| sim | não | 127.762 | 49,72% |
| sim | sim | 27.915 | 50,27% |

## 5. Locais curiosos

### a_chuva_forte_bateria_abstencao_alta

mais de 20 mm no dia 04/10, ao menos uma urna com bateria durante a votação e salto de abstenção contra 2022 acima da mediana dos locais do município; ao menos 200 aptos nas seções casadas com 2022; ordem: excesso sobre a mediana.

Atendem à regra: 643. Os cinco primeiros:

| local | município | chuva dia | chuva votação | urnas | bateria votação | abst. | 2026 menos 2022 |
|---|---|---|---|---|---|---|---|
| [EE. ANTONIA BINATO SILVA (VÓ NINA)](fiscais_mapa.html#uf=SP&l=SP-71870-330-1155) | TEODORO SAMPAIO (SP) | 27,2 | 23,6 | 2 | 2 | 44,42 | 18,59 |
| [ESCOLA MUNICIPAL INDÍGENA TUPÃI ARANDU RENOI](fiscais_mapa.html#uf=MS&l=MS-90174-52-1082) | ANTÔNIO JOÃO (MS) | 34,7 | 11,1 | 2 | 2 | 31,00 | 19,31 |
| [E.M. ADRIANO PIRES-ALDEIA PIRAJUÍ](fiscais_mapa.html#uf=MS&l=MS-91847-1-1058) | PARANHOS (MS) | 50,9 | 20,1 | 3 | 1 | 29,51 | 22,02 |
| [EE. PROFA. SEBASTIANA VALDÍRIA PEREIRA DA SILVA](fiscais_mapa.html#uf=SP&l=SP-62197-300-2135) | BAURU (SP) | 20,4 | 20,4 | 4 | 3 | 37,49 | 15,27 |
| [EMPG NHANDEJARA](fiscais_mapa.html#uf=MS&l=MS-90557-28-1120) | CAARAPÓ (MS) | 33,4 | 18,7 | 10 | 10 | 45,61 | 15,62 |

### b_bateria_em_predio_seco_e_sozinho

5 ou mais urnas com bateria durante a votação no mesmo prédio, chuva zero no dia 04/10 e nenhuma outra urna do município com bateria durante a votação (pista de rede elétrica do prédio ou do entorno, não de tempo).

Atendem à regra: 10. Os cinco primeiros:

| local | município | chuva dia | chuva votação | urnas | bateria votação | abst. | 2026 menos 2022 |
|---|---|---|---|---|---|---|---|
| [COLÉGIO ESTADUAL ANTONIO BATISTA](fiscais_mapa.html#uf=BA&l=BA-34312-64-1031) | CANDIBA (BA) | 0,0 | 0,0 | 10 | 10 | 22,27 | 2,47 |
| [ESCOLA MUNICIPAL EDUCANDARIO DIX SEPTIENSE](fiscais_mapa.html#uf=RN&l=RN-16837-49-1031) | GOVERNADOR DIX-SEPT ROSADO (RN) | 0,0 | 0,0 | 13 | 9 | 20,71 | 1,43 |
| [ESCOLA MUNICIPAL EM TEMPO INTEGRAL JACINTO DANTAS](fiscais_mapa.html#uf=PB&l=PB-21130-43-1031) | OURO VELHO (PB) | 0,0 | 0,0 | 8 | 8 | 13,97 | -0,02 |
| [CENTRO MUNICIPAL DE EDUCAÇÃO INFANTIL LUÍZA MARTINS GONDIM](fiscais_mapa.html#uf=RN&l=RN-18538-27-1040) | SÃO RAFAEL (RN) | 0,0 | 0,0 | 8 | 8 | 18,14 | -0,76 |
| [ESCOLA ESTADUAL CELSO RODRIGUES RÊGO (ANTIGA EEX-I)](fiscais_mapa.html#uf=AL&l=AL-28410-40-1023) | PIRANHAS (AL) | 0,0 | 0,0 | 15 | 7 | 22,47 | -1,75 |

### c_chuva_muito_forte_sem_bateria

mais de 50 mm no dia 04/10 e nenhuma urna do prédio com registro de bateria em qualquer momento; ordem: chuva, depois número de urnas; no máximo 2 por município.

Atendem à regra: 16. Os cinco primeiros:

| local | município | chuva dia | chuva votação | urnas | bateria votação | abst. | 2026 menos 2022 |
|---|---|---|---|---|---|---|---|
| [CEI CRESCER E APRENDER](fiscais_mapa.html#uf=MS&l=MS-98590-19-1163) | CORONEL SAPUCAIA (MS) | 90,3 | 67,1 | 1 | 0 | 8,21 | sem dado |
| [ESCOLA ESTADUAL PROFESSOR JOSÉ VICENTE](fiscais_mapa.html#uf=MG&l=MG-50296-220-1074) | PIUMHI (MG) | 53,2 | 7,6 | 9 | 0 | 25,23 | 3,79 |
| [ESCOLA ESTADUAL PROFESSOR FRANCISCO DE PAULA REBELO HORTA](fiscais_mapa.html#uf=MG&l=MG-50296-220-1058) | PIUMHI (MG) | 53,2 | 7,6 | 8 | 0 | 25,91 | 4,59 |
| [ESCOLA MUNICIPAL PADRE ARISTIDES QUEIROZ](fiscais_mapa.html#uf=MG&l=MG-50091-114-1031) | PIMENTA (MG) | 53,2 | 7,6 | 6 | 0 | 20,39 | 2,31 |
| [ESCOLA ESTADUAL SANTA TEREZINHA](fiscais_mapa.html#uf=MG&l=MG-44679-220-1015) | DORESÓPOLIS (MG) | 53,2 | 7,6 | 4 | 0 | 26,76 | 0,68 |

### d_maior_salto_de_abstencao_com_chuva_forte

mais de 20 mm no dia 04/10, ao menos 200 aptos nas seções casadas com 2022; ordem: diferença contra o 2º turno de 2022, maior primeiro.

Atendem à regra: 3.572. Os cinco primeiros:

| local | município | chuva dia | chuva votação | urnas | bateria votação | abst. | 2026 menos 2022 |
|---|---|---|---|---|---|---|---|
| [E.M. ADRIANO PIRES-ALDEIA PIRAJUÍ](fiscais_mapa.html#uf=MS&l=MS-91847-1-1058) | PARANHOS (MS) | 50,9 | 20,1 | 3 | 1 | 29,51 | 22,02 |
| [ESCOLA MUNICIPAL INDÍGENA TUPÃI ARANDU RENOI](fiscais_mapa.html#uf=MS&l=MS-90174-52-1082) | ANTÔNIO JOÃO (MS) | 34,7 | 11,1 | 2 | 2 | 31,00 | 19,31 |
| [EE. ANTONIA BINATO SILVA (VÓ NINA)](fiscais_mapa.html#uf=SP&l=SP-71870-330-1155) | TEODORO SAMPAIO (SP) | 27,2 | 23,6 | 2 | 2 | 44,42 | 18,59 |
| [POSTO DE SAÚDE ALVORADA DA BARRA](fiscais_mapa.html#uf=SP&l=SP-62499-26-1627) | BOTUCATU (SP) | 21,8 | 20,9 | 1 | 0 | 30,24 | 17,07 |
| [ESCOLA MUNICIPAL PÓLO SÃO JOSÉ](fiscais_mapa.html#uf=MS&l=MS-91847-1-1031) | PARANHOS (MS) | 50,9 | 20,1 | 2 | 1 | 59,96 | 16,22 |

### e_chuva_forte_e_abstencao_caiu

mais de 20 mm no dia 04/10, ao menos 200 aptos casados, abstenção de 2026 menor que a do 2º turno de 2022; ordem: maior queda primeiro.

Atendem à regra: 1.015. Os cinco primeiros:

| local | município | chuva dia | chuva votação | urnas | bateria votação | abst. | 2026 menos 2022 |
|---|---|---|---|---|---|---|---|
| [CENTRO COMUNITÁRIO DA LINHA SÃO LOURENÇO](fiscais_mapa.html#uf=SC&l=SC-81698-18-1112) | JABORÁ (SC) | 20,8 | 0,0 | 1 | 1 | 7,84 | -13,62 |
| [UNIDADE INTEGRADA NOSSA SENHORA DE FÁTIMA](fiscais_mapa.html#uf=MA&l=MA-07480-98-1147) | CIDELÂNDIA (MA) | 25,2 | 8,1 | 2 | 2 | 23,23 | -12,81 |
| [CÓLEGIO ESTADUAL SÃO JOÃO BATISTA DE LA SALLE](fiscais_mapa.html#uf=PR&l=PR-76996-118-1155) | MATELÂNDIA (PR) | 29,5 | 3,0 | 2 | 0 | 13,93 | -12,35 |
| [E.M. MARIO ROSSIN](fiscais_mapa.html#uf=SP&l=SP-68918-98-1104) | PITANGUEIRAS (SP) | 25,4 | 24,4 | 12 | 0 | 16,95 | -11,28 |
| [ESCOLA MUNICIPAL GERALDA CALIXTA LEAO](fiscais_mapa.html#uf=MG&l=MG-47074-338-1031) | JECEABA (MG) | 20,3 | 5,7 | 2 | 2 | 19,47 | -10,02 |

### f. Mudanças do 2º turno e Confresa (MT)

Pares com mudança real: 334; origens distintas: 317; com clima: 283.

| grupo | locais | aptos | chuva média | locais com chuva forte | bateria na votação | abstenção | 2026 menos 2022 |
|---|---|---|---|---|---|---|---|
| origens das mudanças | 283 | 454.653 | 4,98 | 4,59% | 18,97% | 20,14% | -0,16 |
| demais locais | 93.187 | 156.844.583 | 6,91 | 4,26% | 13,59% | 20,85% | 0,45 |
| Confresa (MT) | 17 | 26.068 | 3,08 | 0,00% | 16,25% | 23,49% | -2,24 |

## 6. Resumo por UF

| UF | urnas | chuva média no dia (mm) | chuva média na votação (mm) | locais com chuva forte | urnas com bateria na votação | abstenção | 2026 menos 2022 |
|---|---|---|---|---|---|---|---|
| AC | 2.270 | 3,05 | 0,36 | 0,00% | 8,77% | 20,43% | -7,96 |
| AL | 7.101 | 0,94 | 0,86 | 0,00% | 13,08% | 20,63% | -2,49 |
| AM | 8.157 | 4,42 | 1,15 | 0,30% | 10,16% | 20,16% | -1,79 |
| AP | 1.733 | 3,02 | 0,19 | 0,00% | 6,46% | 17,15% | -10,43 |
| BA | 35.328 | 1,85 | 1,08 | 0,00% | 13,62% | 19,98% | -0,42 |
| CE | 23.669 | 0,80 | 0,67 | 0,00% | 11,14% | 15,52% | -1,59 |
| DF | 6.967 | 2,06 | 1,99 | 0,00% | 9,23% | 18,90% | 2,26 |
| ES | 9.844 | 2,85 | 1,60 | 0,00% | 5,65% | 21,37% | 0,80 |
| GO | 15.669 | 6,88 | 4,70 | 0,73% | 9,76% | 21,83% | 0,78 |
| MA | 18.091 | 2,01 | 1,39 | 0,20% | 12,82% | 19,73% | -3,70 |
| MG | 51.974 | 9,09 | 4,82 | 5,44% | 7,93% | 22,81% | 1,88 |
| MS | 7.106 | 16,15 | 10,55 | 28,47% | 31,78% | 23,87% | 1,43 |
| MT | 8.195 | 4,61 | 3,11 | 0,67% | 15,88% | 22,20% | -0,48 |
| PA | 20.456 | 2,16 | 1,94 | 0,03% | 20,72% | 19,10% | -3,47 |
| PB | 10.642 | 0,62 | 0,06 | 0,00% | 7,73% | 17,37% | 0,75 |
| PE | 21.365 | 0,76 | 0,56 | 0,00% | 11,66% | 18,17% | 0,94 |
| PI | 10.128 | 0,33 | 0,31 | 0,00% | 15,52% | 17,13% | -1,57 |
| PR | 27.106 | 15,64 | 8,89 | 32,14% | 15,52% | 20,57% | 1,77 |
| RJ | 37.675 | 2,24 | 0,29 | 0,00% | 12,63% | 23,32% | 1,23 |
| RN | 8.103 | 0,85 | 0,05 | 0,00% | 9,81% | 18,38% | 1,12 |
| RO | 4.691 | 1,42 | 0,73 | 0,00% | 7,65% | 21,72% | -3,05 |
| RR | 1.431 | 2,04 | 0,79 | 0,00% | 13,00% | 17,19% | -4,68 |
| RS | 27.395 | 10,85 | 0,40 | 1,53% | 9,95% | 21,35% | 2,03 |
| SC | 17.288 | 12,82 | 2,02 | 15,78% | 7,74% | 18,94% | 1,44 |
| SE | 5.912 | 0,42 | 0,12 | 0,00% | 3,84% | 17,29% | -1,42 |
| SP | 103.375 | 12,58 | 11,72 | 8,23% | 20,09% | 22,54% | 1,38 |
| TO | 4.380 | 4,87 | 1,94 | 0,32% | 16,96% | 18,34% | -2,03 |

## 7. Previsão para 25/10

Gerada em 2026-10-20T01:12:23+00:00. Previsão de modelo global a 0,5°, que muda todo dia. É indicativo de atenção para a logística da fiscalização, não previsão do que vai acontecer no prédio.

- alto: chuva >= 30 mm ou rajada >= 70 km/h ou (probabilidade >= 80% e chuva >= 15 mm).
- médio: chuva >= 10 mm ou rajada >= 50 km/h ou probabilidade >= 60%.
- baixo: o resto.
- sem dado: a previsão ainda não alcança o dia alvo ou a célula não respondeu.
- dia: 2026-10-25.

| nível | eleitores | locais | células |
|---|---|---|---|
| alto | 42.346.497 | 16.298 | 191 |
| médio | 53.702.777 | 28.576 | 448 |
| baixo | 61.261.922 | 49.401 | 1.600 |
| sem dado | 0 | 0 | 0 |

Cidades com mais eleitores em risco alto:

| município | eleitores em risco alto | locais | chuva máxima (mm) | rajada máxima (km/h) |
|---|---|---|---|---|
| SÃO PAULO (SP) | 8.771.368 | 1.964 | 33,0 | 65,5 |
| CURITIBA (PR) | 1.410.995 | 422 | 46,2 | 40,3 |
| CAMPINAS (SP) | 870.672 | 267 | 28,5 | 68,0 |
| CAMPO GRANDE (MS) | 640.427 | 232 | 39,3 | 51,1 |
| SÃO BERNARDO DO CAMPO (SP) | 626.746 | 167 | 26,4 | 41,0 |
| OSASCO (SP) | 583.505 | 131 | 26,4 | 65,5 |
| SANTO ANDRÉ (SP) | 567.339 | 156 | 33,0 | 51,8 |
| SÃO JOSÉ DOS CAMPOS (SP) | 539.147 | 144 | 18,9 | 58,3 |
| SOROCABA (SP) | 526.433 | 182 | 38,1 | 55,8 |
| RIBEIRÃO PRETO (SP) | 471.128 | 132 | 28,5 | 54,4 |
| GUARULHOS (SP) | 452.208 | 132 | 26,4 | 65,5 |
| JOINVILLE (SC) | 441.735 | 104 | 49,8 | 48,2 |
| LONDRINA (PR) | 393.986 | 157 | 68,4 | 48,2 |
| SANTOS (SP) | 348.122 | 119 | 33,0 | 51,8 |
| CAXIAS DO SUL (RS) | 339.240 | 162 | 18,3 | 45,4 |
| JUNDIAÍ (SP) | 337.017 | 92 | 22,5 | 65,5 |
| DIADEMA (SP) | 330.968 | 90 | 26,4 | 41,0 |
| MAUÁ (SP) | 310.360 | 83 | 33,0 | 51,8 |
| PIRACICABA (SP) | 309.162 | 111 | 18,0 | 42,8 |
| MARINGÁ (PR) | 301.817 | 130 | 38,1 | 46,8 |
| MOGI DAS CRUZES (SP) | 296.957 | 99 | 33,0 | 59,4 |
| BARUERI (SP) | 294.125 | 64 | 26,4 | 65,5 |
| CARAPICUÍBA (SP) | 290.536 | 60 | 26,4 | 41,0 |
| BAURU (SP) | 277.509 | 97 | 21,6 | 49,0 |
| PRAIA GRANDE (SP) | 264.214 | 91 | 67,5 | 51,8 |
| PONTA GROSSA (PR) | 257.063 | 126 | 60,6 | 52,2 |
| SÃO VICENTE (SP) | 252.771 | 78 | 33,0 | 51,8 |
| TAUBATÉ (SP) | 239.475 | 71 | 18,9 | 58,3 |
| GUARUJÁ (SP) | 238.496 | 63 | 49,2 | 51,8 |
| SÃO JOSÉ DOS PINHAIS (PR) | 227.068 | 78 | 46,2 | 40,3 |

## Conferências

- Ponto exato contra célula (chuva diária de 04/10 no ponto exato do local (motor das mudanças, ERA5 pela Open-Meteo) contra a do centro da célula de 0,25° deste motor): 1.896 pares, correlação 0,9571, diferença absoluta média 1,07 mm (mediana 0,40 mm), mesma faixa em 89,72%.
- Politize: 497.877 seções conferidas, 497.877 iguais, 0 diferentes.

## Controles

| controle | esperado | obtido | passou |
|---|---|---|---|
| total nacional de validos igual ao motor das mudanças | 119300852 | 119300852 | sim |
| total nacional de flavio igual ao motor das mudanças | 56102134 | 56102134 | sim |
| total nacional de lula igual ao motor das mudanças | 53877286 | 53877286 | sim |
| total nacional de brancos igual ao motor das mudanças | 2300670 | 2300670 | sim |
| total nacional de nulos igual ao motor das mudanças | 3668806 | 3668806 | sim |
| células de 0,25° com resposta da Open-Meteo | 6539 | 6539 | sim |
| valores nulos nas respostas do arquivo | 0 | 0 | sim |
| urnas do Brasil sem local no cadastro | 0 | 0 | sim |
| urnas do Brasil sem clima (local sem coordenada no território) | pequeno e declarado | 1826 | sim |
| soma dos aptos por local igual à soma por urna | 157821892 | 157821892 | sim |
| moda da hora de Brasília do primeiro voto é 8 em todas as UFs (votação unificada) | 8 | [8] | sim |
| seções com o código bateria_votacao_local (mapa: 41811; sem boletim do 1º turno: 0) | 41811 | 41811 | sim |
| seções com o código bateria_votacao_isolada (mapa: 12668; sem boletim do 1º turno: 1) | 12667 | 12667 | sim |
| código de simultaneidade só em urna com bateria durante a votação | 0 | 0 | sim |
| aptos e votos por seção iguais aos do Politize | todas iguais | {'secoes_conferidas': 497877, 'iguais': 497877, 'diferentes': 0} | sim |
| urnas na amostra analítica (mais de 99% das urnas do Brasil) | 497877 | 496051 | sim |

## Fontes

| fonte | caminho | bytes | SHA-256 |
|---|---|---|---|
| cadastro de locais com coordenada (TSE) | `data/outputs/locais_votacao_2026.sqlite` | 131.772.416 | `57d96007cfb84bf4c27ff8e0c5dda488aa533b8be13a12267b230857d91c5624` |
| boletins de urna do 1º turno (TSE) | `apuracao/data/secoes_2026.sqlite` | 8.550.633.472 | `2cfbf8259e7461ec313f3554716d6f6b86079eaa10310b3230aabd3fed1941c8` |
| métricas dos logs das urnas do 1º turno | `data/outputs/logs_urnas_2026.sqlite` | 3.856.224.256 | `a176e0113cdb81c06379e306147cb65180acc4eec336aff5e6c9ac791f98a432` |
| índice do mapa de fiscais (códigos de log) | `docs/assets/fiscais_mapa/indice.json` | 169.094 | `f9f5f5920398475b241065e072445678bf0a33fd4db47c568d507f753204c249` |
| seções de 2022 (1º turno, compacto) | `data/outputs/presidente_secao_2022.csv.gz` | 13.098.556 | `d10766833596c67ce15f2ed3978d78f5a60bab6329c1c436f3ca394f58d1852d` |
| detalhe de votação por seção de 2022 (2º turno) | `data/raw/tse_resultados/detalhe_votacao_secao_2022.zip` | 243.822.213 | `ad22c50b9e6d9dfb096a2170680a190f1734895ba89d8977b95fd63ca02c03da` |
| Open-Meteo archive consolidado | `analysis/clima_1t_2026/celulas_archive.json` | 2.289.773 | `2f61239fed6bac452882e6f43939a136cb6104f104fde9c9e6ce3ca2590d5a12` |
| motor das mudanças de seção do 2º turno | `analysis/mudancas_secoes_2t/mudancas.json` | 1.850.633 | `53024840d36b8bb50b3a4c1abb5ea476a5cd5ea6b0e8b34944f63f2329e3ef2a` |
| previsão Open-Meteo para 25/10 | `docs/assets/fiscais_mapa/clima/previsao.json` | 1.481.824 | `10df1c33fb01efe0c4692f7c4741791ffd4c8f13aead795931c9949473c804a5` |

## Limites

- Correlação não é causa. Chuva e vento não são sorteados entre locais: regiões que chovem mais diferem em renda, distância, rede elétrica e hábito de voto. Os controles (efeito fixo de UF e de município, comparação dentro do prédio) reduzem e não eliminam essa diferença.
- O clima é de reanálise (ERA5 e ERA5-Land pela Open-Meteo) numa célula de 0,25°, cerca de 28 km: não é a chuva medida no telhado do prédio. Pancada isolada pode não aparecer, e o erro de medida puxa qualquer associação para perto de zero.
- Bateria é operação prevista da urna, não irregularidade. O log registra que a urna operou com a bateria interna, não por quanto tempo nem se a fila parou: tempo em bateria não é medido.
- A separação entre bateria simultânea (5 ou mais outras seções do município no mesmo minuto) e isolada vem do mapa de fiscais e exige relógio válido; de 1 a 4 seções coincidentes fica como intermediária.
- A comparação com 2022 usa o 2º turno daquele ano nas seções com o mesmo número em UF, município e zona. Renumeração e remanejamento entre 2022 e 2026 mudam o eleitorado de parte dessas seções, e 1º e 2º turno têm motivação diferente.
- Abstenção é sempre razão de somas ponderada por aptos; locais pequenos não pesam como grandes.
- Locais sem coordenada no cadastro (ou com coordenada fora do território) ficam sem clima e fora das análises; o exterior fica fora.
- Leitura agregada por seção e por local: nada aqui identifica eleitor.
- A previsão para 25/10 é de modelo global a 0,5° e muda todo dia; é indicativo de atenção para a logística, não previsão do que vai acontecer no prédio.

## Decisões

- Janela de votação no relógio de Brasília. O contrato pedia 7h a 18h locais; como a votação de 2026 abriu às 8h de Brasília no país inteiro (o primeiro voto tem moda às 8h de Brasília em todas as UFs, controle no payload), a janela local mudaria de posição no Acre, no Amazonas, em MT, MS, RO e RR e cobriria horas sem votação. A série da Open-Meteo já vem em Brasília; o fuso entra só na hora local do pico.
- Seca é 0,0 mm na precisão da Open-Meteo (menos de 0,05 mm). Faixas: fraca até 5, moderada até 20, forte até 50 e muito forte acima de 50 mm, limites superiores fechados. Rajada: até 40, até 60, até 80 e acima de 80 km/h.
- A faixa de chuva publicada no mapa usa a chuva do dia inteiro de 04/10; as análises mostram também a faixa pela chuva das horas de votação.
- Intervalo de confiança por bootstrap de células de 0,25° (conglomerado do clima), não de urnas: urnas da mesma célula dividem a mesma chuva. Grupo com menos de 20 células (ou comparação dentro de estrato com menos de 10 estratos) fica sem intervalo.
- Chuva do dia é o dia de 04/10 no relógio de Brasília (00h às 24h), como a Open-Meteo entrega com timezone=America/Sao_Paulo; no Acre o dia local começa duas horas depois.
- Bateria durante a votação tem como denominador as urnas com log e relógio válido; bateria em qualquer momento e reinício, as urnas com log.
- Odds ratio por 10 mm de chuva e por 10 km/h de rajada, em logística com efeito fixo de UF, log dos aptos e modelo da urna como controles.
- Na regressão de abstenção, efeito fixo de município pela subtração das médias ponderadas: só municípios com urnas em células de chuva diferente informam o coeficiente.
- Listas de locais curiosos exigem ao menos 200 aptos nas seções casadas com 2022 quando usam a diferença contra 2022, para que uma seção pequena não domine a lista.
