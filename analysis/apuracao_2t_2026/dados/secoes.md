# Análise por seção do 2º turno de 2026: comparecimento, biometria e horário

> Sinal pede explicação, não prova irregularidade; a extensão até 19h eleva o comparecimento legitimamente.

Gerado em 2026-10-26T15:44:29+00:00 sobre a fonte **completo** (`apuracao/data/secoes_2t_2026.sqlite`), 499.207 seções com BU, 497.877 com a mesma seção na régua do 1T. Último recebimento lido: 23:21 de Brasília. Régua do 1T: `apuracao/data/referencia_1t_secoes.json` (SHA-256 `99939e691c45b5af`, gerada em 2026-10-25T21:45:14.554Z).

## Método

Cada seção é comparada com ela mesma no 1º turno. Seis sinais: (1) comparecimento/aptos ao menos 5 pp acima do 1T; (2) sem biometria cadastrada ≥ 10% e ≥ 2x a mediana do município no 1T; (3) habilitados por ano de nascimento (biometria cadastrada e não reconhecida) ≥ 10% e ≥ 2x a mediana municipal; (4) salto: a soma das duas parcelas ≥ 10% e 5 pp acima da própria seção no 1T; (5) tardia: último voto depois das 19:00 de Brasília ou 30 min depois do da própria seção no 1T; (6) BU do sistema de apuração. Os sinais 1, 2, 5 e 6 formam o escore 0 a 4 da rota `/api/2t/comparecimento`; esta análise soma 3 e 4 (escore 0 a 6). Contingência e encerramento depois das 17:00 são descrição.

Horas: a do BU é local; converte pelo fuso da UF e depois corrige por município pela abertura modal (a votação abriu às 08:00 de Brasília em todo o país). 12 municípios corrigidos (oeste do Amazonas); a régua do 1T recebe a mesma correção. Conferência: com o fuso só da UF, as contagens repetem as da rota: delta 46.241, sem_bio 13.228, tarde 382.467, tardia 7.257, apos_19h 4.468, papel 29, contingencia 5.743, escore_2_mais 2.581.

Voto: fatia de Flávio entre os dois (F/(F+L)). Toda comparação é dentro do município (seções com sinal contra as demais do mesmo município, média ponderada pelos votos das seções com sinal) e contra a própria seção no 1T (diferença em diferenças). Diferença só com n ≥ 20; o erro-padrão (ep) é aproximado, entre municípios.

## As seções ficaram abertas até 19h?

Não, na quase totalidade. O último voto tem mediana 17:01, p90 17:05 e p99 19:00; 98,22% encerraram até 17:15 e só 0,90% (4.468 seções) depois das 19:00. O BU foi emitido 2,00 min depois do último voto (mediana; p90 3,00 min): emissão mediana 17:03, 98,29% emitidos até 17:30. Emitir o BU fecha a urna. O que demorou foi o recebimento: mediana 20:27, só 0,30% recebidos antes das 19:00, intervalo encerramento→recebimento de 203,50 min na mediana (p90 238,50).

Contra o 1T nas mesmas seções, o 2T fechou mais cedo: depois das 18:00, 1,42% contra 8,54%; depois das 19:00, 0,90% contra 1,66%. No universo do 1T: 92,38% depois de 17:00, 8,42% depois de 18:00 e 1,63% depois de 19:00. O 2T tem um ou dois cargos contra seis no 1T, e a fila anda mais rápido. Leitura: a extensão até 19h não deixou urnas abertas; a urna fechou quando acabou a fila e o BU ficou à espera de transmissão. Quem atribuir a alta de comparecimento à prorrogação precisa mostrar seção que encerrou depois das 17h; na fonte lida são 7.257 tardias de 497.897. Por que o recebimento começou perto das 19h (regra de transmissão ou ordem do TSE) não está nos BUs: é pergunta à Justiça Eleitoral.

| UF | n | último voto p50 | p90 | depois 19:00 | BU emitido p50 | 1º recebimento | recebido antes 19:00 | atraso p50 (min) |
|---|---|---|---|---|---|---|---|---|
| AC | 2.270 | 17:01 | 17:03 | 0,00% | 17:03 | 17:05 | 1,15% | 173,50 |
| AL | 7.101 | 17:01 | 17:05 | 0,00% | 17:04 | 17:07 | 0,06% | 187,40 |
| AM | 8.157 | 17:02 | 17:05 | 0,00% | 17:04 | 17:03 | 2,44% | 163,80 |
| AP | 1.914 | 17:01 | 17:04 | 0,00% | 17:03 | 17:04 | 0,63% | 188,50 |
| BA | 35.476 | 17:02 | 17:07 | 2,08% | 17:04 | 17:05 | 0,03% | 216,50 |
| CE | 23.765 | 17:01 | 17:04 | 0,00% | 17:03 | 17:04 | 0,03% | 205,10 |
| DF | 6.969 | 17:03 | 17:07 | 0,17% | 17:06 | 17:04 | 1,71% | 150,20 |
| ES | 9.844 | 17:01 | 17:03 | 0,01% | 17:03 | 17:06 | 0,03% | 179,20 |
| GO | 15.686 | 17:01 | 17:03 | 0,00% | 17:03 | 17:04 | 0,05% | 202,80 |
| MA | 18.093 | 17:01 | 17:05 | 0,02% | 17:04 | 17:05 | 0,18% | 185,40 |
| MG | 52.062 | 17:01 | 17:03 | 0,00% | 17:03 | 17:05 | 0,08% | 210,20 |
| MS | 7.106 | 17:01 | 17:03 | 0,00% | 17:03 | 17:06 | 0,15% | 174,10 |
| MT | 8.287 | 17:02 | 17:05 | 0,06% | 17:04 | 17:05 | 0,30% | 183,20 |
| PA | 20.827 | 17:01 | 17:04 | 0,01% | 17:04 | 16:59 | 1,68% | 183,50 |
| PB | 10.712 | 17:01 | 17:05 | 0,77% | 17:03 | 17:05 | 1,09% | 156,90 |
| PE | 21.418 | 17:02 | 17:06 | 2,01% | 17:04 | 17:07 | 0,01% | 203,80 |
| PI | 10.225 | 17:01 | 17:04 | 0,05% | 17:03 | 17:07 | 0,02% | 214,10 |
| PR | 27.142 | 17:01 | 17:03 | 0,00% | 17:03 | 17:04 | 0,98% | 173,20 |
| RJ | 37.675 | 17:02 | 17:11 | 5,52% | 17:05 | 19:03 | 0,00% | 233,80 |
| RN | 8.115 | 17:01 | 17:04 | 0,01% | 17:04 | 17:06 | 0,06% | 190,60 |
| RO | 4.698 | 17:02 | 17:05 | 0,00% | 17:04 | 17:03 | 1,81% | 187,70 |
| RR | 1.519 | 17:01 | 17:04 | 0,00% | 17:04 | 17:04 | 0,92% | 202,00 |
| RS | 27.547 | 17:01 | 17:03 | 0,00% | 17:03 | 17:06 | 0,05% | 194,30 |
| SC | 17.326 | 17:01 | 17:02 | 0,00% | 17:03 | 17:01 | 0,63% | 198,30 |
| SE | 5.923 | 17:01 | 17:04 | 0,51% | 17:03 | 19:34 | 0,00% | 236,30 |
| SP | 103.656 | 17:02 | 17:06 | 1,04% | 17:04 | 19:03 | 0,00% | 217,20 |
| TO | 4.384 | 17:01 | 17:04 | 0,00% | 17:04 | 17:05 | 0,46% | 156,10 |
| ZZ | 0 | None | None | sem dado% | None | None | sem dado% | sem dado |

## Números por sinal

- Comparecimento: 81,01% no 2T contra 79,16% nas mesmas seções no 1T; diferença por seção p10 -1,50, p50 1,91, p90 4,89 pp (n 497.877). 9,29% das seções subiram 5 pp ou mais; 2,31% caíram 5 pp ou mais; 0,20% subiram 10 pp ou mais.
- Sem biometria cadastrada: 5,67% dos votantes no 2T contra 5,56% no 1T; 13.228 seções com sinal, das quais 11.883 já tinham o mesmo sinal no 1T (variação mediana 0,14 pp).
- Ano de nascimento: 6,75% no 2T contra 6,68% no 1T; 19.308 seções com sinal, 9.356 já com o sinal no 1T (variação mediana 2,08 pp).
- Salto da parcela sem biometria reconhecida contra a própria seção: 8.952 seções (variação p50 0,14 pp, p90 2,83); salto junto com comparecimento +5 pp: 1.324 seções.
- Tardias: 7.257, das quais 4.468 depois das 19:00. Contingência ou mais de uma carga: 5.743. BU do sistema de apuração: 29.
- Escore (0 a 6): 0: 414.244, 1: 75.687, 2: 8.528, 3: 721, 4: 26, 5: 1; 2 ou mais: 9.276.

## Relação com o voto (dentro do município)

| Sinal | seções | fatia F contra vizinhas (pp) | fatia F 2T−1T nas seções (pp) | diferença em diferenças (pp) | Lula no comparecimento contra vizinhas (pp) |
|---|---|---|---|---|---|
| comparecimento ≥ +5 pp contra a própria seção no 1T | 46.241 | -3,05 (ep 0,23; n 46.208 contra 392.182 em 3.749 municípios) | -2,97 | -0,17 (ep 0,02; n 46.200) | 2,87 |
| comparecimento ≥ 5 pp acima da alta mediana do município ou UF | 6.441 | -5,50 (ep 0,33; n 6.441 contra 370.138 em 2.243 municípios) | -2,62 | 0,05 (ep 0,06; n 6.437) | 5,22 |
| comparecimento ≥ +10 pp contra a própria seção no 1T | 993 | -8,78 (ep 1,31; n 993 contra 141.462 em 410 municípios) | -2,26 | 0,22 (ep 0,18; n 992) | 8,44 |
| sem biometria cadastrada ≥ 10% e ≥ 2x a mediana municipal do 1T | 13.228 | -1,67 (ep 0,27; n 13.228 contra 340.269 em 2.163 municípios) | -3,15 | -0,46 (ep 0,03; n 13.213) | 1,63 |
| habilitados por ano de nascimento ≥ 10% e ≥ 2x a mediana municipal | 19.308 | -0,07 (ep 0,43; n 19.308 contra 426.622 em 3.480 municípios) | -2,70 | 0,31 (ep 0,02; n 19.297) | 0,11 |
| sem biometria ou ano de nascimento acima da regra | 32.185 | -0,79 (ep 0,19; n 32.185 contra 431.272 em 3.965 municípios) | -2,89 | -0,02 (ep 0,02; n 32.161) | 0,79 |
| sem biometria reconhecida ≥ 10% e +5 pp contra a própria seção | 8.952 | -0,66 (ep 0,12; n 8.952 contra 395.961 em 3.040 municípios) | -2,48 | 0,14 (ep 0,02; n 8.941) | 0,62 |
| comparecimento ≥ +5 pp e salto da parcela sem biometria reconhecida | 1.324 | -2,50 (ep 0,24; n 1.324 contra 195.003 em 778 municípios) | -2,43 | 0,08 (ep 0,05; n 1.324) | 2,35 |
| encerrou depois das 19:00 ou 30 min depois do 1T (prorrogação) | 7.257 | 1,89 (ep 1,75; n 7.229 contra 126.625 em 200 municípios) | -3,17 | 0,03 (ep 0,18; n 7.229) | -1,76 |
| encerrou depois das 19:00 de Brasília | 4.468 | 1,65 (ep 1,86; n 4.468 contra 96.874 em 114 municípios) | -3,24 | -0,02 (ep 0,22; n 4.468) | -1,55 |
| urna de contingência ou com mais de uma carga | 5.741 | 0,06 (ep 0,12; n 5.714 contra 362.006 em 1.942 municípios) | -2,93 | 0,01 (ep 0,03; n 5.672) | -0,04 |
| BU do sistema de apuração | 27 | n abaixo de 20 | | | |
| escore 2 ou mais | 9.276 | -1,71 (ep 0,47; n 9.276 contra 387.902 em 2.429 municípios) | -2,81 | 0,03 (ep 0,04; n 9.266) | 1,64 |

Comparecimento alto × biometria baixa × fatia de Flávio contra o 1T:

| comp. +5 pp | biometria baixa | n | F subiu | F não subiu | fatia F 2T−1T (pp) |
|---|---|---|---|---|---|
| sim | sim | 4.078 | 508 | 3.570 | -2,89 |
| sim | não | 42.155 | 4.495 | 37.660 | -2,98 |
| não | sim | 28.083 | 3.324 | 24.759 | -2,89 |
| não | não | 423.490 | 42.246 | 381.244 | -2,96 |

Votos absolutos contra o 1T (n 497.806): Flávio ganhou votos em 79,73% das seções e Lula em 97,59%; Flávio ganhou e Lula perdeu em 3.485 seções, o inverso em 75.729. Ganho médio por seção: Flávio 7,42, Lula 20,76 votos. Seções com comparecimento +10 pp: 992 (Lula ganhou mais em 925, Flávio em 60).

## O que pede explicação

- Maior salto de biometria: Candeias (BA), zona 127, seção 336: +81,54 pp na parcela sem biometria reconhecida contra o 1T, com comparecimento 2,99 pp; habilitados por ano de nascimento 6,67% no 1T e 86,48% no 2T. Votos Flávio × Lula: 48,00 × 200,00 no 1T, 49,00 × 217,00 no 2T. Padrão de leitor biométrico que não reconheceu a seção inteira, hipótese a conferir no log. Classificação: sem explicação provável pela regra: pede conferência na ata e no log.
- Diferença em diferenças na fatia de Flávio maior que duas vezes o erro-padrão: comparecimento ≥ +5 pp contra a própria seção no 1T, -0,17 pp (ep 0,02, n 46.200); sem biometria cadastrada ≥ 10% e ≥ 2x a mediana municipal do 1T, -0,46 pp (ep 0,03, n 13.213); habilitados por ano de nascimento ≥ 10% e ≥ 2x a mediana municipal, 0,31 pp (ep 0,02, n 19.297); sem biometria reconhecida ≥ 10% e +5 pp contra a própria seção, 0,14 pp (ep 0,02, n 8.941). São deslocamentos de menos de um ponto, na direção de Lula quando negativos; não identificam mecanismo.

## Achados que contrariam a tese

- Em algumas UFs o comparecimento caiu contra o 1T (média por seção): AC -5,95 pp, AP -8,32 pp, RR -6,26 pp.
- As seções com alta acima da local são mais favoráveis a Lula que as vizinhas (-5,50 pp na fatia de Flávio, n 6.441), mas já eram no 1T: a diferença em diferenças é 0,05 pp (ep 0,06, n 6.437).
- Biometria baixa é estrutural, não do dia: 11.883 das 13.228 seções com sinal de sem biometria já o tinham no 1T, com variação mediana de 0,14 pp.
- As seções com sinal votam diferente das vizinhas porque já votavam assim: comparecimento +5 pp tem fatia de Flávio -3,05 pp contra as vizinhas, mas a diferença em diferenças contra o 1T é -0,17 pp (ep 0,02); sem biometria, -1,67 e -0,46 pp; salto de biometria, 0,14 pp (n 8.941).
- As tardias são seções mais favoráveis a Flávio que as vizinhas (1,89 pp), sem mudança relativa contra o 1T (0,03 pp, n 7.229).
- Nenhuma diferença acima mede fraude nem intenção: sinal pede explicação, não prova irregularidade.

## As mais atípicas

100 seções em `secoes_ranking.json`, por escore e magnitude; 6 sem explicação provável pela regra. As dez primeiras:

| UF | município | zona | seção | escore | sinais | comp. 2T−1T (pp) | salto biometria (pp) | último voto 1T → 2T | explicação provável |
|---|---|---|---|---|---|---|---|---|---|
| BA | Salvador | 19 | 192 | 5 | delta, sem_bio, ano_nasc, salto_bio, tardia | 7,90 | 5,87 | 17:20 → 19:03 | encerrou perto ou depois das 19:00: compatível com a extensão até 19h; comparecimento do 1T 10 pp ou mais abaixo da mediana municipal; alta acompanha a do município ou da UF (menos de 5 pp acima da mediana) |
| RJ | Rio de Janeiro | 9 | 262 | 4 | delta, ano_nasc, salto_bio, tardia | 5,95 | 47,64 | 17:22 → 19:04 | encerrou perto ou depois das 19:00: compatível com a extensão até 19h; urna de contingência ou com mais de uma carga; alta acompanha a do município ou da UF (menos de 5 pp acima da mediana) |
| RJ | Rio de Janeiro | 214 | 325 | 4 | delta, ano_nasc, salto_bio, tardia | 6,29 | 9,71 | 18:49 → 19:02 | encerrou perto ou depois das 19:00: compatível com a extensão até 19h; urna de contingência ou com mais de uma carga; salto de biometria em outras seções do mesmo local: leitor ou rede; alta acompanha a do município ou da UF (menos de 5 pp acima da mediana) |
| BA | Salvador | 2 | 366 | 4 | delta, sem_bio, ano_nasc, tardia | 13,06 | 3,66 | 17:34 → 19:02 | encerrou perto ou depois das 19:00: compatível com a extensão até 19h; a própria seção já tinha 10% ou mais sem biometria no 1T; comparecimento do 1T 10 pp ou mais abaixo da mediana municipal |
| SP | São Paulo | 4 | 81 | 4 | delta, ano_nasc, salto_bio, tardia | 6,11 | 9,03 | 17:06 → 19:01 | encerrou perto ou depois das 19:00: compatível com a extensão até 19h; alta acompanha a do município ou da UF (menos de 5 pp acima da mediana) |
| BA | Salvador | 5 | 259 | 4 | delta, sem_bio, ano_nasc, tardia | 7,74 | 2,61 | 17:06 → 19:06 | encerrou perto ou depois das 19:00: compatível com a extensão até 19h; a própria seção já tinha 10% ou mais sem biometria no 1T; comparecimento do 1T 10 pp ou mais abaixo da mediana municipal; alta acompanha a do município ou da UF (menos de 5 pp acima da mediana) |
| RJ | Petrópolis | 65 | 364 | 4 | delta, ano_nasc, salto_bio, tardia | 5,17 | 10,08 | 17:06 → 19:06 | encerrou perto ou depois das 19:00: compatível com a extensão até 19h; comparecimento do 1T 10 pp ou mais abaixo da mediana municipal; alta acompanha a do município ou da UF (menos de 5 pp acima da mediana) |
| SP | São Paulo | 251 | 41 | 4 | delta, ano_nasc, salto_bio, tardia | 7,67 | 5,12 | 17:05 → 19:01 | encerrou perto ou depois das 19:00: compatível com a extensão até 19h; alta acompanha a do município ou da UF (menos de 5 pp acima da mediana) |
| BA | Salvador | 18 | 426 | 4 | delta, sem_bio, ano_nasc, tardia | 9,12 | -2,75 | 17:06 → 19:01 | encerrou perto ou depois das 19:00: compatível com a extensão até 19h; a própria seção já tinha 10% ou mais sem biometria no 1T; comparecimento do 1T 10 pp ou mais abaixo da mediana municipal |
| BA | Salvador | 16 | 481 | 4 | delta, sem_bio, ano_nasc, tardia | 10,07 | 1,40 | 18:03 → 19:07 | encerrou perto ou depois das 19:00: compatível com a extensão até 19h; a própria seção já tinha 10% ou mais sem biometria no 1T; comparecimento do 1T 10 pp ou mais abaixo da mediana municipal |

## Limites e o que só o banco completo responde

- Amostra de 150 seções por UF: não estima o país nem localiza o caso raro; seções com sinal são poucas por UF e as diferenças por UF ficam abaixo de n 20.
- Só o banco completo dá: a contagem nacional de cada sinal; a vizinhança do mesmo local de votação (salto de biometria em várias seções do mesmo prédio indica leitor ou rede, não mesário); a distribuição municipal com n suficiente; as seções agregadas e as urnas trocadas em todo o país.
- BU não diz quem votou: só a ata, o caderno de votação e o log da urna separam falha de leitor, eleitor sem biometria e liberação indevida.
- Os votos de Flávio e Lula no 1T vêm da seção principal no Politize; seção agregada entre os turnos distorce a comparação (a explicação provável avisa).

Rodar sobre o banco completo, sem mudar código: `python3 scripts/apuracao-2t-2026-secoes.py --fonte completo` (ou `--fonte auto`, que o escolhe quando cobre 90% das seções do 1T).
