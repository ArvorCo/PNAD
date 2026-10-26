# Apuração do 2º turno de 2026: números do dossiê

Gerado por `scripts/apuracao-2t-2026-dados.py` em 2026-10-26T01:59:29Z, a partir da versão nacional gerada pelo TSE às 2026-10-25 22:46:03 (snapshot 90388, 100,00% das seções). Banco `apuracao/data/apuracao-2t.sqlite` lido em modo somente leitura; versão vigente de cada arquivo = a mais nova pelo `gerado_em`.

Rótulo de todo o conjunto: atipicidade pede explicação, não prova irregularidade.

## 1. Placar

- Brasil (arquivo nacional `u:6258:1:br:::`): Lula 64.255.891 (51,79% dos válidos) × Flávio 59.825.984 (48,21%), diferença de 4.429.907 votos (3,58 pp). Seções 499.246 de 499.248. Brancos 1.430.493 (1,12% do comparecimento), nulos 2.723.298 (2,12%). Abstenção 19,22% do eleitorado das seções totalizadas. Origem: `presidente.json`, `nacional` (tabelas `snapshot`, `totais`, `voto_candidato`).
- Sem o exterior: Lula 51,78% × Flávio 48,22%, abstenção 18,99%. Exterior: Lula 53,86% × Flávio 46,14%, abstenção 58,37%.
- Norte: Lula 50,01% × Flávio 49,99% (Lula menos Flávio: 1.079 votos), abstenção 21,25%.
- Nordeste: Lula 69,37% × Flávio 30,63% (Lula menos Flávio: 13.653.472 votos), abstenção 16,49%.
- Centro-Oeste: Lula 39,99% × Flávio 60,01% (Lula menos Flávio: -1.869.948 votos), abstenção 20,05%.
- Sudeste: Lula 47,24% × Flávio 52,76% (Lula menos Flávio: -2.806.830 votos), abstenção 20,27%.
- Sul: Lula 37,42% × Flávio 62,58% (Lula menos Flávio: -4.576.523 votos), abstenção 18,19%.
- Exterior: Lula 53,86% × Flávio 46,14% (Lula menos Flávio: 28.657 votos), abstenção 58,37%.
- Achado: o Norte terminou empatado em 50,01% a 49,99%, com 1.079 votos de diferença em 10.048.173 válidos.
- Conferência: soma das UFs menos nacional = {'secoes': 0, 'comparecimento': 0, 'abstencao': 0, 'validos': 0, 'brancos': 0, 'nulos': 0, 'flavio': 0, 'lula': 0}; soma dos municípios menos nacional = {'secoes': -3, 'comparecimento': -649, 'abstencao': -87, 'validos': -630, 'brancos': -7, 'nulos': -12, 'flavio': -389, 'lula': -241}. Diferença não nula enquanto há seções por totalizar é defasagem entre versões geradas em instantes diferentes. Municípios incompletos: 4.

## 2. Os fatos da noite conferidos contra o banco

- Versão nacional gerada às 21:23:31: 99,85% das seções, Lula 64.135.805 × Flávio 59.767.310. Origem: `linha_do_tempo.json`, `nacional.serie`.
- Parada: o arquivo nacional não teve versão nova entre 17:07:01 e 19:01:56 (114,90 min; seções de 1.456 para 1.870). Em todo o banco (resultado, andamento e configuração dos dois pleitos), nenhum arquivo tem hora de geração entre 17:07:09 e 19:01:44 (114,60 min, 0 versões); o coletor fez 65.792 leituras nesse intervalo ({'igual': 3, 'nao_existe': 420, 'nao_modificado': 65147, 'ok': 222}). Consulta: `SELECT MAX(gerado_em) FROM snapshot WHERE gerado_em < meio` e `MIN(gerado_em) ... > meio`.
- A tabela `pausa` do coletor registra a pausa geral de 17:07:00 a 19:01:45 (114,80 min).
- Prorrogação: decisão do STF (ministro Cristiano Zanin) prorrogou a votação até 19h em todo o país, informada por volta de 17:03 a 17:08; o horário vem do noticiário da noite, não do banco.
- Pausa de UF AM: 19:01 a 19:39 (37,40 min; seções 152 para 3.090).
- Pausa de UF RR: 19:01 a 19:32 (30,80 min; seções 6 para 108).
- Pausa de UF AM: 19:39 a 19:47 (8,70 min; seções 3.090 para 4.270).
- Pausa de UF RR: 19:40 a 19:51 (10,70 min; seções 157 para 191).
- Pausa de UF RR: 20:01 a 20:11 (9,70 min; seções 308 para 450).
- Pausa de UF RR: 20:56 a 21:14 (18,00 min; seções 1.516 para 1.519).
- Pausa de UF AM: 21:06 a 21:49 (43,70 min; seções 8.022 para 8.156).
- Pausa de UF AM: 22:05 a 22:45 (40,00 min; seções 8.156 para 8.157).
- Abstenção às 21:30 (rota /api/2t/abstencao, municípios fechados): 19,25% contra 20,92% nos mesmos municípios no 1º turno (5.127 municípios).
- Abstenção final, 5.567 municípios completos sem exterior: 19,03% contra 20,85% no 1º turno e 20,48% no 2º turno de 2022 nos mesmos municípios. Origem: `abstencao.json`, `brasil`.
- Menores abstenções por UF (arquivo de UF, versão vigente): CE 13,89%; PE 15,18%; PB 15,54%; SE 15,71%; RN 16,06%; BA 16,71%; SC 16,96%. Os valores citados na noite (CE 14,8, PE 15,3, SE 15,6, PB 15,9, RN 16,4, SC 16,9) não coincidem com a versão vigente; a diferença pode vir da hora da leitura ou da base (municípios fechados contra arquivo de UF). Na versão vigente a BA entra entre as seis menores e SC sai.
- Paralela: 177 BUs em 15 UFs; conferência {'igual': 177}.
- Projeção da casa: primeiro ponto com projeção às 19:15 (1,58% das seções), Flávio 47,19% entre os dois (faixa de 90% de 45,72 a 48,84). Líder projetado em todos os 40 pontos: lula. Final observado: Flávio 48,21%; erro absoluto médio 0,39 pp, máximo 1,21 pp.
- Achado: na contagem observada, Flávio esteve à frente entre 19:50 e 20:25 (8 pontos de 5 min, máximo de 50,70% entre os dois), enquanto a projeção apontava Lula.

## 3. Cedo contra tarde

- 5.567 municípios em dez grupos pelo minuto em que fecharam. Parte de Flávio entre os dois: 44,57% no 1º decil e 47,93% no 10º. Mudança contra o 1º turno nos mesmos municípios (swing): -2,31, -2,47, -2,43, -2,43, -2,41, -2,62, -2,63, -2,49, -2,83, -3,08 pp. O swing quase constante mostra que a diferença entre cedo e tarde é de composição, não de mudança de voto. Origem: `cedo_tarde.json`, `decis_2t`.
- O último decil tem 63.399.716 eleitores e 19 capitais; o primeiro, 3.343.418 eleitores. Correlação de postos entre tamanho e minuto de fechamento: 0,42; entre a ordem de fechamento do 1º e do 2º turno: 0,52.
- Zonas (6.102): swing de -2,99 a -2,49 pp entre os decis.
- Primeira UF completa: SC às 21:08; última até a rodada: AM às 22:45. Ainda com seção por totalizar: BA, MG.
- Atípico: PONTE ALTA DO NORTE (SC, 8 seções) teve todas as seções totalizadas às 17:07, antes do fim da votação prorrogada. atipicidade pede explicação, não prova irregularidade.
- Regressões: 0 versões genuínas com menos seções ou menos comparecimento que a anterior; versões marcadas regressivas pelo coletor por nível: br 0 (cópias antigas 0); uf 53 (cópias antigas 53); mu 5 (cópias antigas 5); zona 3 (cópias antigas 3).

## 4. Contra o 1º turno

- 5.567 municípios completos: Flávio 55.539.389 para 59.201.903 (+3.662.514), Lula 52.731.403 para 62.849.441 (+10.118.038). Terceiros do 1º turno: 9.169.051. Flávio somou o equivalente a 39,94% desse estoque e Lula a 110,35% (o comparecimento cresceu 2.835.622). Parte de Flávio entre os dois: 51,30% para 48,51% (-2,79 pp). Origem: `comparacao_1t.json`, `brasil`.
- Swing a favor de Lula em 5.407 municípios e a favor de Flávio em 159; mediana -2,37 pp, desvio 1,25.
- Flávio perdeu votos absolutos em 938 municípios e ganhou em 4.620; Lula perdeu em 79 e ganhou em 5.487.
- Maiores perdas de Flávio: MACAPÁ (AP) -3.785; SENA MADUREIRA (AC) -2.292; TARAUACÁ (AC) -2.135; CRUZEIRO DO SUL (AC) -2.069; CAMPOS DOS GOYTACAZES (RJ) -1.389.
- Maiores perdas de Lula: MAZAGÃO (AP) -1.135; ICATU (MA) -968; PORTO WALTER (AC) -787; BAGRE (PA) -747; TURIAÇU (MA) -717.
- Norte: swing -2,41 pp; Flávio 2,23% e Lula 75,02% do estoque de terceiros; abstenção +1,82 pp.
- Nordeste: swing -1,94 pp; Flávio 21,65% e Lula 161,81% do estoque de terceiros; abstenção -1,79 pp.
- Centro-Oeste: swing -3,39 pp; Flávio 47,63% e Lula 78,05% do estoque de terceiros; abstenção -1,65 pp.
- Sudeste: swing -3,66 pp; Flávio 44,78% e Lula 110,53% do estoque de terceiros; abstenção -2,43 pp.
- Sul: swing -3,18 pp; Flávio 57,26% e Lula 88,07% do estoque de terceiros; abstenção -2,27 pp.
- Contrariando a tese de abstenção em queda geral: a abstenção subiu contra o 1º turno em AC (+5,65 pp), AM (+1,51 pp), AP (+8,06 pp), MA (+0,63 pp), PA (+1,22 pp), PI (+0,04 pp), RO (+0,21 pp), RR (+6,03 pp), TO (+0,89 pp). Parte do estoque de terceiros somada por Flávio nessas UFs: AC -47,93%, AM -1,03%, AP -33,94%, MA -4,81%, PA 13,23%, PI 8,36%, RO 33,22%, RR -58,81%, TO -2,46%.
- Municípios com abstenção pelo menos 5 pp menor que no 1º turno e 5 mil eleitores ou mais: 44; com abstenção 5 pp maior: 99.

## 5. Contra o 2º turno de 2022

- Mesmos 5.566 municípios, sem exterior: Lula 50,63% em 2022 contra 51,49% em 2026 (+0,86 pp); Flávio fica -0,86 pp de Bolsonaro. Abstenção 20,48% para 19,03%. Origem: `comparacao_2022.json`, `brasil`; fonte de 2022 em `fontes_2022`.
- Achado contrário ao agregado: Lula caiu contra 2022 em 4.356 municípios e subiu em 1.202; mediana municipal -2,04 pp, média ponderada pelo eleitorado +0,57 pp: mediana negativa com média ponderada positiva indica avanço de Lula concentrado nos municípios mais populosos.
- Municípios que trocaram de vencedor: 334 (288 de Lula para Flávio, 43 de Bolsonaro para Lula).
- UFs com maior avanço de Lula sobre 2022: DF +4,53, AP +4,24, AC +3,73, RR +3,62, RJ +3,43; maior recuo: TO -2,73, MA -1,62, BA -1,52, RS -1,48, CE -1,04.

## 6. Abstenção

- Norte: 21,25% (1º turno 19,43%, 2022 22,94%).
- Nordeste: 16,53% (1º turno 18,32%, 2022 19,47%).
- Centro-Oeste: 20,05% (1º turno 21,70%, 2022 20,64%).
- Sudeste: 20,27% (1º turno 22,70%, 2022 21,25%).
- Sul: 18,19% (1º turno 20,46%, 2022 18,60%).
- Capitais 18,78% (-2,13 pp contra o 1º turno); interior 19,11% (-1,73 pp).
- Abstenção abaixo de 15%: o Nordeste concentra 82,70% do eleitorado desses municípios; o Sul tem 33,19% dos seus municípios abaixo de 15%, com eleitorado médio de 6.825 por município.
- A abstenção caiu contra o 1º turno em 4.434 municípios e subiu em 1.126.
- Explicações legítimas para a queda: prorrogação da votação até 19h em todo o país, mobilização de segundo turno e transporte; o banco não separa essas causas.

## 7. Exterior

- 186 cidades (186 completas): Lula 53,86% × Flávio 46,14%, comparecimento 41,63%.
- US: Flávio 62,65% × Lula 37,35% (1º turno 61,10 × 31,68); comparecimento 32,98% (+4,53 pp).
- PT: Flávio 40,58% × Lula 59,42% (1º turno 38,57 × 52,45); comparecimento 43,93% (+5,47 pp).
- JP: Flávio 80,08% × Lula 19,92% (1º turno 71,76 × 15,27); comparecimento 42,60% (+1,12 pp).
- CA: Flávio 35,02% × Lula 64,98% (1º turno 32,52 × 57,75); comparecimento 54,01% (+5,58 pp).
- GB: Flávio 36,66% × Lula 63,34% (1º turno 35,42 × 57,03); comparecimento 42,06% (+5,08 pp).

## 8. Governadores

- AC: MAILZA ASSIS 66,21% × ALAN RICK 33,79% (133.527 votos, pst 100,00); 1º turno 49,76 × 32,27; viradas na noite: 0; vão do vencedor contra o presidencial do mesmo lado -0,36 pp; brancos e nulos de governador menos os de presidente +4,45 pp.
- AM: OMAR AZIZ 61,42% × PROFESSORA MARIA DO CARMO 38,58% (473.647 votos, pst 100,00); 1º turno 40,63 × 24,49; viradas na noite: 0; vão do vencedor contra o presidencial do mesmo lado +7,40 pp; brancos e nulos de governador menos os de presidente +2,04 pp.
- DF: CELINA LEÃO 57,18% × LEANDRO GRASS 42,82% (248.012 votos, pst 100,00); 1º turno 49,93 × 34,47; viradas na noite: 0; vão do vencedor contra o presidencial do mesmo lado +2,90 pp; brancos e nulos de governador menos os de presidente +3,51 pp.
- ES: LORENZO PAZOLINI 52,17% × RICARDO FERRAÇO 47,83% (95.699 votos, pst 100,00); 1º turno 49,65 × 34,06; viradas na noite: 4; vão do vencedor contra o presidencial do mesmo lado -4,20 pp; brancos e nulos de governador menos os de presidente +3,54 pp.
- RN: CADU DE LULA 50,77% × ALLYSON 49,23% (32.625 votos, pst 100,00); 1º turno 36,16 × 36,94; viradas na noite: 0; vão do vencedor contra o presidencial do mesmo lado -14,95 pp; brancos e nulos de governador menos os de presidente +1,55 pp.
- TO: VICENTINHO JÚNIOR 64,52% × PROFESSORA DORINHA 35,48% (253.007 votos, pst 100,00); 1º turno 43,94 × 45,52; viradas na noite: 0; vão do vencedor contra o presidencial do mesmo lado +15,89 pp; brancos e nulos de governador menos os de presidente +4,02 pp.
- Rótulo do vão: teto endereçável, nunca transferência certa.

## 9. Limites

- O horário da decisão do STF vem do noticiário; o banco mostra só o silêncio de publicação, não a causa.
- Exterior: a totalização impressa está em hora local; os relógios deste conjunto usam a hora de geração do TSE (Brasília).
- O 1º turno é comparado pela régua `referencia_1t.json` (fechamento por município) e por `analysis/apuracao_2026/dados/*.json`; no 1º turno a votação terminou às 17:00 e no 2º às 19:00, então minutos de fechamento não se comparam sem descontar 120 min (`atraso_vs_1t_descontada_prorrogacao_min`).
- Votos ganhos sobre o estoque de terceiros não identificam transferência individual: a conta mistura eleitor novo, eleitor que faltou e troca de lado.
- 2022 casa por código TSE do município; municípios sem par: 7. Zonas do 1º turno casam por número, e o rezoneamento pode mudar o território.
- Latência entre geração e captura é teto, não medida, porque inclui o intervalo de sondagem do coletor.
- A projeção da casa foi relida com `at=` sobre o banco: é a reconstrução do que o método diria em cada instante, não necessariamente o que a tela mostrou (`serie_ao_vivo`).
- A paralela é a soma dos BUs recebidos, não projeção; a amostra é de quem enviou.

