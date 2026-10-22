# Demonstração do motor do 2º turno com a noite real do 1º turno

Gerado por `bun run scripts/demonstrar-2t.ts` em 22/10 02:17:56 (horário de Brasília), em 85,4 s. Arquivo irmão com todos os números: `demonstracao_1t.json`.

Fontes, todas abertas só para leitura:

- banco do 1º turno: `apuracao/data/apuracao.sqlite`
- BUs por seção do 1º turno: `apuracao/data/secoes_2026.sqlite`
- régua do 1º turno: `apuracao/data/referencia_1t.json`
- régua de pausas do dossiê: `analysis/apuracao_2026/dados/linha_do_tempo.json`

Bancos gerados pela demonstração (esquema real, recriados a cada execução, fora do git):

- regra atual, limiar 5 min: `apuracao/data/demo-replay-1t-l5.sqlite`
- regra atual, limiar 7 min: `apuracao/data/demo-replay-1t-l7.sqlite`
- regra de versão anterior, limiar 5 min: `apuracao/data/demo-replay-1t-anterior-l5.sqlite`
- conferência de BU: `apuracao/data/demo-paralela-1t.sqlite`

## Resumo

- **Pausas.** Com o limiar padrão de 5 min o motor abre 14 pausas; com 7 min, 9. As 5 a mais do limiar de 5 min (4 nacionais e 1 geral) são todas lacunas abaixo dos 8,0 min da régua do dossiê. Com 7 min, a única pausa de nível nacional é a parada de 18:48:59 a 19:14:08; a pausa geral de 19:32 e o travamento das 18:00 aparecem como pausas gerais (nenhum arquivo de presidente com versão nova).
- **Viradas e fechamentos.** 3 viradas de liderança (RR às 17:21:54, TO às 17:22:38, AM às 20:14:19) e 28 fechamentos de UF; líder inicial mais viradas termina no líder final em 28 de 28 arquivos de UF.
- **Régua do 1º turno.** `uf_atrasada_1t`: 0 alertas (a régua lida por interpolação, como estava, daria 40); `abstencao_atipica_mun`: 0; `abstencao_atipica_uf`: 0. A contraprova com a mesma noite atrasada em 30 min dispara 28 alertas de atraso.
- **Conferência de BU real.** 4 BUs oficiais decodificados; 9 de 9 comparações diretas e 10 de 10 conferências pela ponte com a situação esperada: 3 iguais, 6 divergentes e 1 à espera do TSE.
- **Três defeitos do motor apareceram no replay e foram corrigidos** (seção "Defeitos encontrados"): a regra de versão regressiva descartava 2.213 versões novas de presidente por causa do idg; a régua de atraso, lida por interpolação, acusava atraso de UF que estava no mesmo ponto do 1º turno na mesma hora; e o texto de fechamento usava carimbos de totalização fora da janela da geração (o exterior "fechava" às 09:19 do dia seguinte).

## (a) A noite de 04/10 relida pelo coletor do 2º turno

### Como foi feito

Cada leitura que o coletor do 1º turno gravou na tabela `fetch` para os 29 arquivos `-u` de presidente (Brasil, 27 UFs e exterior) e para os 28 arquivos `-ab` das UFs volta a passar por `processar()`, o pipeline do coletor, na ordem em que a resposta chegou: 104.683 leituras (ok 14.239, nao_modificado 89.573, igual 259, timeout 612), de 03/10 23:13:01 a 05/10 13:00:00. Corpo novo e corpo repetido voltam com o blob original, para o próprio coletor decidir entre versão nova, cópia regressiva e corpo igual. Do `-ab` só entram as leituras com corpo: a régua de abstenção lê o conteúdo, e o frescor que o motor exige é o dos arquivos de presidente.

`instalarTurno2` liga o motor exatamente como no ar (detector de pausas, viradas e fechamentos gravados pelo coletor, régua do 1º turno). A configuração de turno 1 (`APURACAO_ELEICOES=6257`) põe a eleição 6257 e o relógio da apuração em 17:00 de 04/10 (`T0_1T_MS`); `src/turno2/comum.ts` não foi tocado. A avaliação de 30 s roda pelo Agendador com a fila vazia: o replay nunca acessa a rede. Foram 4.533 avaliações por rodada.

### Pausas detectadas

#### Limiar nacional de 5 min (`APURACAO_PAUSA_MIN=5`, UF 10 min): 14 pausas

| Nível | UF | De | Até | Min | st antes → depois | Detectada | Na régua do dossiê (Δ início, Δ fim) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| geral |  | 04/10 18:00:33 | 04/10 18:09:11 | 8,6 | 66.453 → 66.456 | 18:07:01 | travamentos.todas_as_ufs_sem_versao_nova 18:00:27–18:09:11 (+6 s, 0 s) |
| nacional |  | 04/10 18:26:58 | 04/10 18:32:24 | 5,4 | 139.204 → 159.242 | 18:33:01 | não (lacuna abaixo de 8 min) |
| nacional |  | 04/10 18:32:24 | 04/10 18:37:14 | 4,8 | 159.242 → 182.745 | 18:38:31 | não (lacuna abaixo de 8 min) |
| nacional |  | 04/10 18:37:14 | 04/10 18:43:29 | 6,3 | 182.745 → 207.533 | 18:43:31 | não (lacuna abaixo de 8 min) |
| nacional |  | 04/10 18:43:29 | 04/10 18:48:59 | 5,5 | 207.533 → 235.931 | 18:49:31 | não (lacuna abaixo de 8 min) |
| nacional |  | 04/10 18:48:59 | 04/10 19:14:08 | 25,2 | 235.931 → 323.539 | 19:00:01 | travamentos.nacional 18:48:59–19:14:08 (0 s, 0 s) |
| geral |  | 04/10 19:17:16 | 04/10 19:26:12 | 8,9 | 367.369 → 368.156 | 19:23:31 | travamentos.todas_as_ufs_sem_versao_nova 19:17:16–19:26:04 (0 s, +8 s) |
| geral |  | 04/10 19:32:18 | 04/10 20:02:12 | 29,9 | 419.491 → 423.989 | 19:38:31 | travamentos.todas_as_ufs_sem_versao_nova 19:32:28–20:02:02 (-10 s, +10 s) |
| geral |  | 04/10 23:55:57 | 05/10 00:11:34 | 15,6 | 499.233 → 499.233 | 00:02:01 | travamentos.todas_as_ufs_sem_versao_nova 23:55:57–00:11:32 (0 s, +2 s) |
| geral |  | 05/10 00:12:01 | 05/10 00:29:44 | 17,7 | 499.234 → 499.234 | 00:18:01 | travamentos.todas_as_ufs_sem_versao_nova 00:12:01–00:29:43 (0 s, +1 s) |
| geral |  | 05/10 00:30:09 | 05/10 00:40:08 | 10,0 | 499.235 → 499.235 | 00:36:31 | travamentos.todas_as_ufs_sem_versao_nova 00:30:09–00:40:03 (0 s, +5 s) |
| geral |  | 05/10 00:40:28 | 05/10 00:46:24 | 5,9 | 499.236 → 499.236 | 00:46:31 | não (lacuna abaixo de 8 min) |
| geral |  | 05/10 00:46:47 | 05/10 01:57:04 | 70,3 | 499.241 → 499.241 | 00:53:01 | travamentos.todas_as_ufs_sem_versao_nova 00:46:47–01:56:53 (0 s, +11 s) |
| geral |  | 05/10 01:57:10 | 05/10 02:59:30 | 62,3 | 499.247 → 499.247 | 02:03:31 | travamentos.todas_as_ufs_sem_versao_nova 01:57:10–02:59:25 (0 s, +5 s) |

#### Limiar nacional de 7 min (`APURACAO_PAUSA_MIN=7`, UF 10 min): 9 pausas

| Nível | UF | De | Até | Min | st antes → depois | Detectada | Na régua do dossiê (Δ início, Δ fim) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| geral |  | 04/10 18:00:33 | 04/10 18:09:11 | 8,6 | 66.453 → 66.456 | 18:09:01 | travamentos.todas_as_ufs_sem_versao_nova 18:00:27–18:09:11 (+6 s, 0 s) |
| nacional |  | 04/10 18:48:59 | 04/10 19:14:08 | 25,2 | 235.931 → 323.539 | 19:02:01 | travamentos.nacional 18:48:59–19:14:08 (0 s, 0 s) |
| geral |  | 04/10 19:17:16 | 04/10 19:26:12 | 8,9 | 367.369 → 368.156 | 19:25:31 | travamentos.todas_as_ufs_sem_versao_nova 19:17:16–19:26:04 (0 s, +8 s) |
| geral |  | 04/10 19:32:28 | 04/10 20:02:12 | 29,7 | 423.988 → 423.989 | 19:40:31 | travamentos.todas_as_ufs_sem_versao_nova 19:32:28–20:02:02 (0 s, +10 s) |
| geral |  | 04/10 23:55:57 | 05/10 00:11:34 | 15,6 | 499.233 → 499.233 | 00:04:01 | travamentos.todas_as_ufs_sem_versao_nova 23:55:57–00:11:32 (0 s, +2 s) |
| geral |  | 05/10 00:12:01 | 05/10 00:29:44 | 17,7 | 499.234 → 499.234 | 00:20:01 | travamentos.todas_as_ufs_sem_versao_nova 00:12:01–00:29:43 (0 s, +1 s) |
| geral |  | 05/10 00:30:09 | 05/10 00:40:08 | 10,0 | 499.235 → 499.235 | 00:38:31 | travamentos.todas_as_ufs_sem_versao_nova 00:30:09–00:40:03 (0 s, +5 s) |
| geral |  | 05/10 00:46:47 | 05/10 01:57:04 | 70,3 | 499.241 → 499.241 | 00:55:01 | travamentos.todas_as_ufs_sem_versao_nova 00:46:47–01:56:53 (0 s, +11 s) |
| geral |  | 05/10 01:57:10 | 05/10 02:59:30 | 62,3 | 499.247 → 499.247 | 02:05:31 | travamentos.todas_as_ufs_sem_versao_nova 01:57:10–02:59:25 (0 s, +5 s) |

#### Diferença entre 5 e 7 min

Só com 5 min aparecem 5 pausas:

| Nível | UF | De | Até | Min | st antes → depois | Detectada | Na régua do dossiê (Δ início, Δ fim) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| nacional |  | 04/10 18:26:58 | 04/10 18:32:24 | 5,4 | 139.204 → 159.242 | 18:33:01 | não (lacuna abaixo de 8 min) |
| nacional |  | 04/10 18:32:24 | 04/10 18:37:14 | 4,8 | 159.242 → 182.745 | 18:38:31 | não (lacuna abaixo de 8 min) |
| nacional |  | 04/10 18:37:14 | 04/10 18:43:29 | 6,3 | 182.745 → 207.533 | 18:43:31 | não (lacuna abaixo de 8 min) |
| nacional |  | 04/10 18:43:29 | 04/10 18:48:59 | 5,5 | 207.533 → 235.931 | 18:49:31 | não (lacuna abaixo de 8 min) |
| geral |  | 05/10 00:40:28 | 05/10 00:46:24 | 5,9 | 499.236 → 499.236 | 00:46:31 | não (lacuna abaixo de 8 min) |

As 4 nacionais de 18:26:58 a 18:48:59 têm de 4,8 a 6,3 min: é a cadência do arquivo nacional naquele trecho, e nenhuma chega aos 8,0 min da régua do dossiê.

A de 18:32:24 fecha com 4,8 min, menos que o próprio limiar: foi aberta às 18:38:31, e a versão gerada às 18:37:14 só chegou às 18:39:24, 2,2 min depois de gerada, além da folga de 1 min do detector.

A pausa geral de 19:32:18 começa às 19:32:18 com 5 min e às 19:32:28 com 7 min: o início é a última versão de presidente conhecida quando a pausa abre (19:38:31 e 19:40:31), e a versão gerada às 19:32:28 só chegou entre as duas detecções. Chegou velha, por isso entra no histórico sem encerrar a pausa.

Confere com o relatório do motor: 5 min dá 4 pausas nacionais de cadência e 7 min deixa só a parada nacional de 18:48:59 a 19:14:08. Nos dois limiares as pausas gerais ficam a até 11 s das lacunas correspondentes do dossiê.

### Comparação com a régua do dossiê (limiar de 5 min)

Régua: `analysis/apuracao_2026/dados/linha_do_tempo.json`, limiar de 8,0 min. Regra do dossiê: "Lacuna maior que o limiar entre gerações consecutivas de versões novas do mesmo arquivo, com a contagem iniciada e incompleta. Leituras no intervalo vêm do log de requisições do coletor." As três primeiras linhas são os marcos citados no pedido.

| Intervalo | Nível | De | Até | Min | Na régua | Pausas do motor que tocam o intervalo | Min cobertos | Mesmo nível |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nenhuma UF com versão nova | geral | 04/10 18:00:27 | 04/10 18:09:11 | 8,7 | sim | geral 18:00:33–18:09:11 | 8,6 | sim |
| travamento nacional | nacional | 04/10 18:00:33 | 04/10 18:10:48 | 10,3 | sim | geral 18:00:33–18:09:11 | 8,6 | não |
| parada do arquivo nacional | nacional | 04/10 18:48:59 | 04/10 19:14:08 | 25,2 | sim | nacional 18:48:59–19:14:08 | 25,2 | sim |
| arquivo nacional sem versão nova | nacional | 04/10 19:14:08 | 04/10 20:04:39 | 50,5 | sim | geral 19:17:16–19:26:12; geral 19:32:18–20:02:12 | 38,8 | não |
| nenhuma UF com versão nova | geral | 04/10 19:17:16 | 04/10 19:26:04 | 8,8 | sim | geral 19:17:16–19:26:12 | 8,8 | sim |
| nenhuma UF com versão nova | geral | 04/10 19:32:28 | 04/10 20:02:02 | 29,6 | sim | geral 19:32:18–20:02:12 | 29,6 | sim |
| pausa geral | geral | 04/10 19:32:47 | 04/10 20:01:55 | 29,1 | sim | geral 19:32:18–20:02:12 | 29,1 | sim |
| arquivo nacional sem versão nova | nacional | 04/10 23:55:37 | 05/10 00:11:37 | 16,0 | sim | geral 23:55:57–00:11:34 | 15,6 | não |
| nenhuma UF com versão nova | geral | 04/10 23:55:57 | 05/10 00:11:32 | 15,6 | sim | geral 23:55:57–00:11:34 | 15,6 | sim |
| arquivo nacional sem versão nova | nacional | 05/10 00:11:37 | 05/10 00:29:47 | 18,2 | sim | geral 00:12:01–00:29:44 | 17,7 | não |
| nenhuma UF com versão nova | geral | 05/10 00:12:01 | 05/10 00:29:43 | 17,7 | sim | geral 00:12:01–00:29:44 | 17,7 | sim |
| arquivo nacional sem versão nova | nacional | 05/10 00:29:47 | 05/10 00:40:07 | 10,3 | sim | geral 00:30:09–00:40:08 | 10,0 | não |
| nenhuma UF com versão nova | geral | 05/10 00:30:09 | 05/10 00:40:03 | 9,9 | sim | geral 00:30:09–00:40:08 | 9,9 | sim |
| arquivo nacional sem versão nova | nacional | 05/10 00:46:28 | 05/10 01:56:51 | 70,4 | sim | geral 00:46:47–01:57:04 | 70,1 | não |
| nenhuma UF com versão nova | geral | 05/10 00:46:47 | 05/10 01:56:53 | 70,1 | sim | geral 00:46:47–01:57:04 | 70,1 | sim |
| arquivo nacional sem versão nova | nacional | 05/10 01:56:51 | 05/10 02:59:31 | 62,7 | sim | geral 00:46:47–01:57:04; geral 01:57:10–02:59:30 | 62,6 | não |
| nenhuma UF com versão nova | geral | 05/10 01:57:10 | 05/10 02:59:25 | 62,3 | sim | geral 01:57:10–02:59:30 | 62,3 | sim |

Leitura:

- **Travamento nacional de 18:00:33 a 18:10:48.** No mesmo trecho o dossiê registra nenhuma UF com versão nova de 18:00:27 a 18:09:11. O motor cobre com pausa geral de 18:00:33 a 18:09:11. Como ninguém publicava, a pausa é geral; quando as UFs voltam, o nacional volta 1,6 min depois, abaixo do limiar. É a regra declarada do detector: nível nacional só quando as UFs publicam e andam.
- **Parada do arquivo nacional de 18:48:59 a 19:14:08.** Detectada como pausa nacional; diferença contra o dossiê com limiar de 5 min: 0 s no início e 0 s no fim; 7 min: 0 s no início e 0 s no fim.
- **Pausa geral de 19:32:47 a 20:01:55.** O motor abre a pausa geral de 19:32:18 a 20:02:12. O dossiê mede a lacuna de geração em todos os cargos e níveis; o motor mede só os arquivos de presidente (Brasil e UFs), por isso o início é a última versão de presidente antes da parada e o fim, a primeira depois dela.
- **Arquivo nacional sem versão nova de 19:14:08 a 20:04:39 (50,5 min).** É o limite do motor que o replay mostra: ele cobre 38,8 min com pausa geral de 19:17:16 a 19:26:12 e pausa geral de 19:32:18 a 20:02:12, e nenhuma é nacional. Fora das pausas gerais as UFs publicavam com o nacional parado, mas o critério de "o país publica" exige idade mediana da última versão das UFs de até 3 min em toda a janela do limiar, e no trecho descoberto, de 19:26:12 a 19:32:18, ela passou de 3 min em 6 de 13 instantes (tabela abaixo, de 30 em 30 s, calculada como no detector). No fim desse trecho a soma das UFs tinha 419.491 seções e o arquivo nacional 323.539, 95.952 a menos. O único aviso do motor para isso é o `soma_ufs_adiante`, que dispara uma vez por episódio: 1 nesta noite, às 18:31:01.

| Instante | Idade mediana (min) | UFs |
| --- | --- | --- |
| 19:26:12 | 9,1 | 28 |
| 19:26:42 | 0,4 | 28 |
| 19:27:12 | 0,9 | 28 |
| 19:27:42 | 1,4 | 28 |
| 19:28:12 | 1,9 | 28 |
| 19:28:42 | 2,4 | 28 |
| 19:29:12 | 2,9 | 28 |
| 19:29:42 | 3,4 | 28 |
| 19:30:12 | 3,9 | 28 |
| 19:30:42 | 4,4 | 28 |
| 19:31:12 | 4,9 | 28 |
| 19:31:42 | 5,4 | 28 |
| 19:32:12 | 0,1 | 28 |

- **Cauda depois das 23:00.** 6 pausas gerais (23:55:57 a 00:11:34, 00:12:01 a 00:29:44, 00:30:09 a 00:40:08, 00:40:28 a 00:46:24, 00:46:47 a 01:57:04, 01:57:10 a 02:59:30); 5 delas coincidem com lacunas "nenhuma UF com versão nova" do dossiê. São reais pela definição, com 1 a 15 seções pendentes no país, e 4 viram `error` por passarem de 15 min numa hora em que só faltam seções isoladas.

### Viradas de liderança

| Hora | UF | De | Para | pst | Texto do telão |
| --- | --- | --- | --- | --- | --- |
| 17:21:54 | RR | Lula | Flavio Bolsonaro | 1,6 | Virada em RR: Flavio Bolsonaro passa Lula |
| 17:22:38 | TO | Lula | Flavio Bolsonaro | 6,5 | Virada em TO: Flavio Bolsonaro passa Lula |
| 20:14:19 | AM | Flavio Bolsonaro | Lula | 89,8 | Virada em AM: Lula passa Flavio Bolsonaro |

Conferência: em cada arquivo de UF, o líder da primeira versão com voto seguido das viradas gravadas termina no líder da última versão em 28 de 28 UFs. Nenhuma virada no arquivo nacional.

### Fechamentos de UF, em ordem

| # | UF | Gerada (BRT) | Capturada (BRT) | Totalização corrigida | Dossiê: gerada | Δ | Texto do telão |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | DF | 20:12:24 | 20:13:29 | 04/10 20:11:33 | 20:12:24 | 0 s | Distrito Federal fechou às 20:11 |
| 2 | RO | 20:51:00 | 20:52:09 | 04/10 20:49:42 | 20:51:00 | 0 s | Rondônia fechou às 20:49 |
| 3 | AC | 20:54:39 | 20:55:10 | 04/10 20:54:23 | 20:54:39 | 0 s | Acre fechou às 20:54 |
| 4 | TO | 20:54:47 | 20:55:40 | 04/10 20:54:25 | 20:54:47 | 0 s | Tocantins fechou às 20:54 |
| 5 | ES | 20:57:30 | 20:58:20 | 04/10 20:55:34 | 20:57:30 | 0 s | Espírito Santo fechou às 20:55 |
| 6 | AP | 21:04:20 | 21:05:02 | 04/10 21:02:15 | 21:04:20 | 0 s | Amapá fechou às 21:02 |
| 7 | MS | 21:04:51 | 21:05:33 | 04/10 21:02:35 | 21:04:51 | 0 s | Mato Grosso do Sul fechou às 21:02 |
| 8 | RR | 21:06:00 | 21:07:00 | 04/10 21:05:17 | 21:06:00 | 0 s | Roraima fechou às 21:05 |
| 9 | RS | 21:06:46 | 21:07:30 | 04/10 21:04:14 | 21:06:46 | 0 s | Rio Grande do Sul fechou às 21:04 |
| 10 | MT | 21:21:52 | 21:22:30 | 04/10 21:21:28 | 21:21:52 | 0 s | Mato Grosso fechou às 21:21 |
| 11 | SC | 21:53:57 | 21:55:21 | 04/10 21:53:19 | 21:53:57 | 0 s | Santa Catarina fechou às 21:53 |
| 12 | SE | 21:56:34 | 21:57:11 | 04/10 21:55:49 | 21:56:34 | 0 s | Sergipe fechou às 21:55 |
| 13 | RJ | 22:05:35 | 22:06:22 | 04/10 22:04:30 | 22:05:35 | 0 s | Rio de Janeiro fechou às 22:04 |
| 14 | GO | 22:36:05 | 22:36:42 | 04/10 22:35:05 | 22:36:05 | 0 s | Goiás fechou às 22:35 |
| 15 | PE | 22:40:14 | 22:41:33 | 04/10 22:39:20 | 22:40:14 | 0 s | Pernambuco fechou às 22:39 |
| 16 | PR | 22:40:50 | 22:41:53 | 04/10 22:40:11 | 22:40:50 | 0 s | Paraná fechou às 22:40 |
| 17 | SP | 22:47:51 | 22:48:43 | 04/10 22:47:00 | 22:47:51 | 0 s | São Paulo fechou às 22:47 |
| 18 | RN | 22:51:14 | 22:51:34 | 04/10 22:50:36 | 22:51:14 | 0 s | Rio Grande do Norte fechou às 22:50 |
| 19 | AL | 22:53:53 | 22:55:13 | 04/10 22:53:14 | 22:53:53 | 0 s | Alagoas fechou às 22:53 |
| 20 | ZZ | 22:54:52 | 22:56:13 | 05/10 09:19:47 | 22:54:52 | 0 s | Exterior fechou às 22:54 |
| 21 | CE | 23:09:58 | 23:11:13 | 04/10 23:09:22 | 23:09:58 | 0 s | Ceará fechou às 23:09 |
| 22 | PB | 23:22:27 | 23:23:24 | 04/10 23:21:16 | 23:22:27 | 0 s | Paraíba fechou às 23:21 |
| 23 | PI | 23:36:27 | 23:37:55 | 04/10 23:35:37 | 23:36:27 | 0 s | Piauí fechou às 23:35 |
| 24 | PA | 23:55:38 | 23:57:25 | 04/10 23:55:03 | 23:55:38 | 0 s | Pará fechou às 23:55 |
| 25 | BA | 00:40:21 | 00:41:16 | 05/10 00:39:20 | 00:40:21 | 0 s | Bahia fechou às 00:39 |
| 26 | MG | 00:46:47 | 00:47:56 | 05/10 00:45:39 | 00:46:47 | 0 s | Minas Gerais fechou às 00:45 |
| 27 | MA | 01:57:08 | 01:59:03 | 05/10 01:56:22 | 01:57:08 | 0 s | Maranhão fechou às 01:56 |
| 28 | AM | 02:59:27 | 03:00:04 | 05/10 00:58:39 | 02:59:27 | 0 s | Amazonas fechou às 02:59 |

O instante de fechamento gravado pelo coletor é a geração da primeira versão com todas as seções; ele coincide com o `conclusao_ufs` do dossiê em 28 de 28 UFs. O dossiê já registrava, na coluna `atraso_da_regra_do_coletor_min`, que a regra de versão anterior atrasava o fechamento de AC (1,7 min), TO (1,7 min), MT (2,2 min), RJ (2,0 min), GO (2,0 min), RN (3,7 min), AL (1,0 min), CE (1,0 min), PA (16,0 min), BA (76,6 min) e MG (70,3 min); a regra atual elimina essa diferença.

### Régua do 1º turno: atraso e abstenção

| Alerta | Rodada padrão |
| --- | --- |
| `uf_atrasada_1t` (atraso em degrau, regra atual) | 0 |
| `uf_atrasada_1t` pela interpolação (regra anterior, recalculada só para comparação) | 40 |
| `abstencao_atipica_mun` | 0 |
| `abstencao_atipica_uf` | 0 |
| contraprova: a mesma noite com 30 min de atraso | 28 |

**Abstenção: zero, e é o esperado.** A régua de abstenção é o resultado final do próprio 1º turno por município. No fim do replay 5.757 municípios estão fechados (1.372 com 20 mil eleitores ou mais), 5.717 deles com par na régua, em 28 UFs, e a maior diferença de abstenção contra a régua é de 0,005 pp, do tamanho do arredondamento da régua, que grava a abstenção com duas casas decimais. Medida contra ela mesma, a noite não tem como acusar 5 pp no município nem 2 pp na UF.

**Atraso: 0 alertas residuais, todos da construção da régua.** Pela definição o resultado também devia ser zero: no mesmo relógio, a UF tem o que o 1º turno tinha. Os 0 restantes vêm de versões que a régua põe antes de elas existirem: o `RelogioArquivo` usado por `scripts/referencia-1t.ts` data cada versão pelo `totalizado_em` (corrigido do fuso quando cabe) e, quando esse carimbo fica para trás, pelo instante da versão anterior; nenhuma das duas datas é a publicação. A tabela mostra, para cada alerta, o ponto da curva que passou da UF e a versão do 1º turno com aquelas seções:

| Alerta (BRT) | UF | Patamar | st da UF | Régua: passou às | st da régua | Versão gerada às | totalizado_em impresso | Régua adiantada (min) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Em 0 dos 0, a versão que a régua põe antes do alerta foi gerada de  min depois do instante que a régua lhe atribui (); em 0, ela nem existia na hora do alerta. Corrigir isso é gerar a curva da régua pelo instante de publicação (`gerado_em`), mudança em `scripts/referencia-1t.ts`, que é do orquestrador; fica registrada aqui, sem edição.

**Contraprova.** Um segundo `AlertasRegua`, fora do banco, lê os mesmos estados de UF com o relógio adiantado em 30 min, como se o 2º turno repetisse o 1º com esse atraso: 28 alertas em 28 UFs (patamares 20 min, de 17:10:31 a 17:27:01). O patamar de 20 min dispara 28 vezes, uma por UF, entre 17:10:31 e 17:27:01. Os 0 acima de 20 min caem em 0 UFs (; 0 deles nas UFs dos alertas residuais) e somam ao atraso simulado o adiantamento da régua descrito acima: com 30 min de atraso, basta a régua estar 10 min adiantada para o patamar chegar a 40. O alerta funciona sobre as curvas reais; o resultado da rodada padrão não vem de um alerta desligado.

### Defeitos encontrados no replay e corrigidos

**1. Regra de versão regressiva (`src/collector/processar-corpo.ts`).** O coletor tratava como cópia antiga toda versão com idg menor que o da versão atual, mesmo gerada depois. O idg não acompanha a hora de geração: na noite de 04/10, 2.213 versões de presidente (Brasil e UFs) geradas depois da atual chegaram com idg menor e foram descartadas. Exemplo do banco: MT gerado às 19:32:06 com 95,8% das seções, capturado às 19:33:57, descartado porque o idg caiu de 1.679.820 (versão gerada às 19:30:56, 95,5%) para 1.677.712; pela regra anterior o arquivo só voltou a andar às 20:04:38, 30,7 min depois. A regra agora ordena pela hora de geração (dg/hg) e usa o idg só para desempatar versões com a mesma hora ou sem hora (`versaoRegressiva`).

|  | Aceitas | Regressivas |
| --- | --- | --- |
| Regra anterior (flags gravadas pelo coletor do 1º turno) | 5.187 | 2.418 |
| Regra atual (replay) | 7.400 | 241 |

Entre as versões aceitas pela regra atual, 0 têm menos seções que a aceita anterior do mesmo arquivo: a ordem por geração não aceita conteúdo velho.

A rodada "regra de versão anterior, limiar 5 min" emula a regra anterior (o corpo que o coletor do 1º turno marcou como regressivo volta como leitura sem corpo, que era o efeito dele) e mostra o que mudou no motor: 19 pausas contra 14, 3 delas de UF (RN 22:11:14–22:21:53, st 8.114 → 8.114; SP 22:27:53–22:39:32, st 103.647 → 103.647; MG 23:12:26–23:23:46, st 52.058 → 52.058). As de UF fecham com o mesmo número de seções com que abriram: eram versões publicadas e descartadas, não paradas da UF. Com a regra anterior a régua dava 0 alertas de atraso em degrau e 51 pela interpolação.

| Nível | UF | De | Até | Min | st antes → depois | Detectada | Na régua do dossiê (Δ início, Δ fim) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| geral |  | 04/10 18:00:33 | 04/10 18:09:11 | 8,6 | 65.971 → 65.974 | 18:07:01 | travamentos.todas_as_ufs_sem_versao_nova 18:00:27–18:09:11 (+6 s, 0 s) |
| nacional |  | 04/10 18:26:58 | 04/10 18:32:24 | 5,4 | 139.204 → 159.242 | 18:33:01 | não (lacuna abaixo de 8 min) |
| nacional |  | 04/10 18:32:24 | 04/10 18:37:14 | 4,8 | 159.242 → 182.745 | 18:38:31 | não (lacuna abaixo de 8 min) |
| nacional |  | 04/10 18:37:14 | 04/10 18:43:29 | 6,3 | 182.745 → 207.533 | 18:43:31 | não (lacuna abaixo de 8 min) |
| nacional |  | 04/10 18:43:29 | 04/10 18:48:59 | 5,5 | 207.533 → 235.931 | 18:49:31 | não (lacuna abaixo de 8 min) |
| nacional |  | 04/10 18:48:59 | 04/10 19:14:08 | 25,2 | 235.931 → 323.539 | 19:00:01 | travamentos.nacional 18:48:59–19:14:08 (0 s, 0 s) |
| geral |  | 04/10 19:17:16 | 04/10 19:26:12 | 8,9 | 367.060 → 367.847 | 19:23:31 | travamentos.todas_as_ufs_sem_versao_nova 19:17:16–19:26:04 (0 s, +8 s) |
| geral |  | 04/10 19:32:18 | 04/10 20:02:12 | 29,9 | 419.444 → 423.942 | 19:38:31 | travamentos.todas_as_ufs_sem_versao_nova 19:32:28–20:02:02 (-10 s, +10 s) |
| UF | RN | 04/10 22:11:14 | 04/10 22:21:53 | 10,7 | 8.114 → 8.114 | 22:22:31 | não (lacuna abaixo de 8 min) |
| UF | SP | 04/10 22:27:53 | 04/10 22:39:32 | 11,7 | 103.647 → 103.647 | 22:39:01 | não (lacuna abaixo de 8 min) |
| UF | MG | 04/10 23:12:26 | 04/10 23:23:46 | 11,3 | 52.058 → 52.058 | 23:23:31 | não (lacuna abaixo de 8 min) |
| geral |  | 04/10 23:29:53 | 04/10 23:35:57 | 6,1 | 499.203 → 499.203 | 23:36:01 | não (lacuna abaixo de 8 min) |
| geral |  | 04/10 23:50:31 | 04/10 23:55:34 | 5,1 | 499.230 → 499.230 | 23:56:31 | não (lacuna abaixo de 8 min) |
| geral |  | 04/10 23:55:57 | 05/10 00:11:34 | 15,6 | 499.232 → 499.232 | 00:02:01 | travamentos.todas_as_ufs_sem_versao_nova 23:55:57–00:11:32 (0 s, +2 s) |
| geral |  | 05/10 00:12:01 | 05/10 00:29:47 | 17,8 | 499.234 → 499.234 | 00:18:01 | travamentos.todas_as_ufs_sem_versao_nova 00:12:01–00:29:43 (0 s, +4 s) |
| geral |  | 05/10 00:29:56 | 05/10 00:40:03 | 10,1 | 499.234 → 499.234 | 00:36:01 | travamentos.todas_as_ufs_sem_versao_nova 00:30:09–00:40:03 (-13 s, 0 s) |
| geral |  | 05/10 00:40:24 | 05/10 00:46:36 | 6,2 | 499.234 → 499.234 | 00:46:31 | não (lacuna abaixo de 8 min) |
| geral |  | 05/10 00:46:36 | 05/10 01:57:04 | 70,5 | 499.234 → 499.234 | 00:53:01 | travamentos.todas_as_ufs_sem_versao_nova 00:46:47–01:56:53 (-11 s, +11 s) |
| geral |  | 05/10 01:57:10 | 05/10 02:59:30 | 62,3 | 499.247 → 499.247 | 02:03:31 | travamentos.todas_as_ufs_sem_versao_nova 01:57:10–02:59:25 (0 s, +5 s) |

**2. Atraso contra a curva do 1º turno (`src/collector/regua.ts`).** O alerta usava `atrasoVsReferencia`, que interpola linearmente entre dois pontos da curva. Entre 19:32:47 e 20:01:55 o 1º turno não publicou nada; a interpolação fazia a curva subir nesse trecho, e toda UF que estava no mesmo ponto do 1º turno na mesma hora aparecia atrasada assim que o relógio passava 20 min do último ponto antes da lacuna. Na rodada padrão a interpolação dá 40 alertas, 26 deles entre 18:37:01 e 20:36:31. O alerta agora lê a curva em degraus: atraso é há quanto tempo, no mesmo relógio, o 1º turno já tinha passado do pst em que a UF está (`atrasoEmDegrau`, tolerância de meia unidade da 3ª casa decimal em que a régua grava o pst, abaixo de uma seção em qualquer UF). Os patamares de 20 min e o texto do evento não mudaram.

**3. Hora do fechamento de UF no telão (`src/server/textos.ts`).** O texto do `uf_fechou` usava a totalização corrigida do fuso. Em 2 das 28 UFs ela fica fora da janela de 15 min antes da geração do arquivo: ZZ (totalização 05/10 09:19:47, gerado 04/10 22:54:52) e AM (totalização 05/10 00:58:39, gerado 05/10 02:59:27). O exterior traz a totalização na hora local da cidade (`analysis/apuracao_2026/BRIEF.md`: Wellington, 09:19 de 05/10) e o AM, um carimbo que parou antes da última versão; o telão escreveria esses horários. Agora, fora da janela, o texto usa a geração do arquivo; dentro dela, nada muda. O detalhe gravado guarda os dois carimbos.

## (b) Conferência de BU real pela totalização paralela

Regra declarada de escolha: em cada UF, a primeira seção por (município, zona, seção) com BU guardado em `data/secoes_2026.sqlite` e com dois números votados para presidente (para dar o que mover). ZZ entra com boletim do Sistema de Apuração (`o03220zz2917300010494-busa.dat`). O hash e o arquivo vêm de `escolherHash` sobre o aux.json original, como o coletor faz, e são conferidos com o que o banco registrou.

| UF | Município | Zona | Seção | Uso | Arquivo | Origem do QR | sha256 | Hash, arquivo e sha256 iguais ao banco |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SP | Euclides da Cunha Paulista | 330 | 17 | igual, voto movido e comparecimento + 1 | `o03220sp6100003300017-bu.dat` | VOTA | `6cff49f9e2848ae4…` | sim |
| AC | Bujari | 9 | 1 | igual, voto movido e comparecimento + 1 | `o03220ac0100700090001-bu.dat` | VOTA | `e9bf12d281f0f0d3…` | sim |
| ZZ | Katmandu | 1 | 494 | igual, voto movido e comparecimento + 1 | `o03220zz2917300010494-busa.dat` | SA | `e7cc196e1ae20102…` | sim |
| AC | Bujari | 9 | 2 | aux.json não publicado (o TSE falso responde 404) | `o03220ac0100700090002-bu.dat` | VOTA | `1a3e4c3fca7a9697…` | sim |

O BU decodificado (`src/secoes2t/bu-decode.ts`) vira o registro das views públicas do Supabase (uma linha por cargo e uma por número votado, legenda como `LEGP<partido>`; no Sistema de Apuração o QR não traz APTO nem COMP, que ficam nulos). O lado da paralela passa por `cargosDoBu` e `qrComparavel`, o oficial por `resumoBu`, e os dois por `comparar` (`src/paralela/conferir.ts`).

### Comparação direta

| BU | Seção | Caso | Situação | Diferenças |
| --- | --- | --- | --- | --- |
| 1 | SP 61000 z330 s17 | BU idêntico ao oficial | igual | nenhuma |
| 2 | SP 61000 z330 s17 | um voto de presidente do 13 (123) para o 22 (70) | divergente | nominal 13: paralela 122, TSE 123; nominal 22: paralela 71, TSE 70 |
| 3 | SP 61000 z330 s17 | comparecimento do boletim (COMP) mais 1 | divergente | comparecimento: paralela 210, TSE 209 |
| 4 | AC 01007 z9 s1 | BU idêntico ao oficial | igual | nenhuma |
| 5 | AC 01007 z9 s1 | um voto de presidente do 22 (143) para o 13 (67) | divergente | nominal 13: paralela 68, TSE 67; nominal 22: paralela 142, TSE 143 |
| 6 | AC 01007 z9 s1 | comparecimento do boletim (COMP) mais 1 | divergente | comparecimento: paralela 242, TSE 241 |
| 7 | ZZ 29173 z1 s494 | BU idêntico ao oficial | igual | nenhuma |
| 8 | ZZ 29173 z1 s494 | um voto de presidente do 22 (11) para o 13 (1) | divergente | nominal 13: paralela 2, TSE 1; nominal 22: paralela 10, TSE 11 |
| 9 | ZZ 29173 z1 s494 | comparecimento de presidente (TOTC; o QR do Sistema de Apuração não traz COMP) mais 1 | divergente | comparecimento_cargo: paralela 14, TSE 13 |
| 10 | AC 01007 z9 s2 | aux.json ainda não publicado pelo TSE (404) | não comparado |  |

O caso sem aux.json não passa por `comparar`: sem aux não há BU oficial para buscar, e a situação vem da ponte, abaixo.

### Pela ponte do coletor

Os 10 registros entram pela `PonteParalela` real, com um Supabase falso servindo as três views e um TSE falso servindo o aux.json e o BU originais (o aux da última seção responde 404). O primeiro ciclo roda antes de a amostra buscar qualquer seção; o segundo, depois da busca.

| BU | Caso | 1º ciclo | 2º ciclo | Diferenças gravadas |
| --- | --- | --- | --- | --- |
| 1 | SP: BU idêntico ao oficial | tse_ainda_nao_publicou | igual | nenhuma |
| 2 | SP: um voto de presidente do 13 (123) para o 22 (70) | tse_ainda_nao_publicou | divergente | nominal 13: paralela 122, TSE 123; nominal 22: paralela 71, TSE 70 |
| 3 | SP: comparecimento do boletim (COMP) mais 1 | tse_ainda_nao_publicou | divergente | comparecimento: paralela 210, TSE 209 |
| 4 | AC: BU idêntico ao oficial | tse_ainda_nao_publicou | igual | nenhuma |
| 5 | AC: um voto de presidente do 22 (143) para o 13 (67) | tse_ainda_nao_publicou | divergente | nominal 13: paralela 68, TSE 67; nominal 22: paralela 142, TSE 143 |
| 6 | AC: comparecimento do boletim (COMP) mais 1 | tse_ainda_nao_publicou | divergente | comparecimento: paralela 242, TSE 241 |
| 7 | ZZ: BU idêntico ao oficial | tse_ainda_nao_publicou | igual | nenhuma |
| 8 | ZZ: um voto de presidente do 22 (11) para o 13 (1) | tse_ainda_nao_publicou | divergente | nominal 13: paralela 2, TSE 1; nominal 22: paralela 10, TSE 11 |
| 9 | ZZ: comparecimento de presidente (TOTC; o QR do Sistema de Apuração não traz COMP) mais 1 | tse_ainda_nao_publicou | divergente | comparecimento_cargo: paralela 14, TSE 13 |
| 10 | AC: aux.json ainda não publicado pelo TSE (404) | tse_ainda_nao_publicou | tse_ainda_nao_publicou | nenhuma |

Requisições ao TSE falso: 7 (6 com 200, 1 com 404). `/api/2t/paralela` sobre o banco da demonstração: conferência iguais 3, divergentes 6, tse_ainda_nao_publicou 1, erro 0, fora_do_oficial 0, pendentes 0; erro nulo.

### Evento `divergencia_paralela`: texto e detalhe

Texto exato que a rota `/api/anomalias` (a mesma que o telão lê, via `textoEvento` de `src/server/textos.ts`) devolve para cada divergência gravada pela ponte:

- BU 2 (`error`): "BU da totalização paralela difere do oficial na seção 17 da zona 330 de Euclides da Cunha Paulista (SP)"
- BU 3 (`error`): "BU da totalização paralela difere do oficial na seção 17 da zona 330 de Euclides da Cunha Paulista (SP)"
- BU 5 (`error`): "BU da totalização paralela difere do oficial na seção 1 da zona 9 de Bujari (AC)"
- BU 6 (`error`): "BU da totalização paralela difere do oficial na seção 1 da zona 9 de Bujari (AC)"
- BU 8 (`error`): "BU da totalização paralela difere do oficial na seção 494 da zona 1 de Katmandu (ZZ)"
- BU 9 (`error`): "BU da totalização paralela difere do oficial na seção 494 da zona 1 de Katmandu (ZZ)"
- lote (`paralela_conferida`): "Totalização paralela: 9 BUs conferidos, 3 iguais e 6 com diferença"

Detalhe gravado no banco para o BU 2:

```json
{
  "secao": 17,
  "zona": 330,
  "bu_id": 2,
  "hash_final": "sha256 do o03220sp6100003300017-bu.dat: 6cff49f9e2848ae4953405d90a03ea100b3cd7a7e9a9a743085a2ed93fee76d7",
  "recebido_em": "2026-10-04T23:50:00.000Z",
  "tse_sha256": "6cff49f9e2848ae4953405d90a03ea100b3cd7a7e9a9a743085a2ed93fee76d7",
  "campos": [
    {
      "campo": "presidente: votos no 13",
      "paralela": 122,
      "tse": 123
    },
    {
      "campo": "presidente: votos no 22",
      "paralela": 71,
      "tse": 70
    }
  ],
  "n_diferencas": 2
}
```

O `hash_final` do QR não está no arquivo `.dat`; a demonstração usa no lugar o sha256 do BU oficial, identificado como tal no próprio campo. O `recebido_em` é um instante fixo da demonstração, porque no 1º turno não houve envio real.

## O que isso prova e o que não prova

Prova:

- que o motor, ligado como no ar, detecta pausas, viradas e fechamentos de UF sobre as versões oficiais reais da noite de 04/10, nos mesmos segundos da régua publicada no dossiê, e que o limiar de 7 min separa a parada real da cadência normal do arquivo nacional;
- que a régua do 1º turno não acusa abstenção atípica contra a própria noite e acusa atraso quando a mesma noite chega atrasada;
- que a conferência da totalização paralela decodifica BUs oficiais reais (urna e Sistema de Apuração), declara igual o que é igual, aponta campo a campo um voto movido ou um comparecimento alterado em 1, espera o TSE quando o aux.json não existe e gera o evento e o texto que o telão mostra.

Não prova:

- o comportamento da rede, do CDN e da divulgação do TSE em 25/10: cadência, atrasos de entrega e paradas do 2º turno serão outros;
- a presença de BUs na totalização paralela: nenhum BU real foi enviado por QR nesta demonstração, e a leitura do QR, a cadeia de certificados e o Supabase de produção ficaram fora;
- que uma pausa, um atraso ou uma divergência signifiquem irregularidade: pausa é intervalo sem versão nova publicada, atraso pede explicação, e a conferência de BU prova transmissão e soma da seção, não o interior da urna.
