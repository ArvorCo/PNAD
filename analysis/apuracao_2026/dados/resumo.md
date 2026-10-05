# Apuração do 1º turno de 2026: os 15 achados mais fortes dos dados

Gerado por `scripts/apuracao-2026-dados.py` em 2026-10-05T06:59:03Z (UTC). Versão nacional de presidente: snapshot 513491, gerada pelo TSE às 2026-10-05 02:59:31 (Brasília). Boletim `final.json` de 2026-10-05T06:29:53.765Z. Cada número sai de um arquivo em `analysis/apuracao_2026/dados/`, com o campo entre parênteses. Os 15 achados são fatos verificados no banco e nos arquivos do TSE; as inferências ficam numa seção própria, rotuladas.

Regra de versão usada em tudo: a versão vigente de cada arquivo é a última gerada pelo TSE (`gerado_em`). A marca `regressivo` do coletor não serve para isso (achado 13).

## Fatos verificados

**1. Resultado final com 100% das seções.** A última versão do arquivo nacional, gerada às 02:59:31 de 05/10 com 499.248 de 499.248 seções, dá Flávio Bolsonaro 56.104.503 votos (47,03% dos válidos) e Lula 53.879.538 (45,16%): diferença de 2.224.965 votos, 1,87 ponto. Comparecimento 78,92%, brancos 1,84% e nulos 2,93% do comparecimento. Flávio venceu em 15 UFs e Lula em 12. Flávio esteve à frente em todas as 330 versões novas com seções, da primeira (17:21:47, 1,23% das seções) à última.
Fonte: presidente.json (nacional.votos, nacional.pct, nacional.diferenca_votos, nacional.pct_comparecimento); linha_do_tempo.json (nacional.versoes, colunas flavio e lula).

**2. Contra o 1º turno de 2022, a margem virou 7,10 pontos.** Flávio fez +3,83 pontos e +5.032.158 votos sobre Bolsonaro (43,20% em 2022); Lula ficou 3,27 pontos e 3.379.966 votos abaixo do próprio resultado de 2022 (48,43%). A margem da direita foi de −5,23 para +1,87. Contra o 2º turno de 2022, Flávio ainda está 2,07 pontos abaixo de Bolsonaro (49,10%), que é outra disputa.
Fonte: presidente.json (nacional.comparacao, nacional.r2022).

**3. Flávio cresceu sobre Bolsonaro em 26 de 27 UFs e em 5.468 de 5.559 municípios.** A exceção estadual é DF (−0,34 ponto, −781 votos). Lula aumentou a própria fatia em 2 UFs (AP +0,04, DF +1,26) e em 102 municípios.
Fonte: presidente.json (ufs[].comparacao.flavio_vs_bolsonaro_1t, ufs[].comparacao.lula_vs_lula_1t; municipios, colunas swing_flavio_pp e swing_lula_pp, só municípios com arquivo completo e com 2022).

**4. A perda de Lula é do Centro-Sul.** Dos −3.379.966 votos que Lula perdeu contra 2022, −3.135.837 (92,8%) vieram do Centro-Sul, −258.555 (7,6%) do Nordeste e −4.028 do Norte. Maiores perdas por UF: SP −984.619, MG −613.635, RS −511.913, PR −308.895. Entre as capitais, São Paulo −224.163 e Salvador −78.370.
Fonte: presidente.json (regioes.*.comparacao.lula_vs_lula_1t, regioes.*.contribuicao_pct_da_variacao_nacional, ufs[].comparacao, capitais[].delta_votos_lula).

**5. O ganho de Flávio é nacional, e um terço veio do Nordeste.** Centro-Sul +2.785.951 (55,4%), Nordeste +1.611.579 (32,0%), Norte +613.276 (12,2%). No Nordeste Flávio fez 30,85%, acima de Bolsonaro no 1º turno (26,97%) e também no 2º turno de 2022 (30,66%).
Fonte: presidente.json (regioes.Nordeste, regioes.Norte, regioes.Centro-Sul: r2026.pct, r2022.t1.pct, r2022.t2.pct, comparacao.flavio_vs_bolsonaro_1t).

**6. Flávio cresceu mais onde Lula era mais forte.** Nos 1.478 municípios em que Lula teve 70 a 100% no 1º turno de 2022, Flávio subiu +4,74 pontos sobre Bolsonaro e Lula caiu −4,15; nos 489 em que Lula teve 0 a 30%, +3,31 e −3,16. Na faixa mais lulista, Flávio somou +899.751 votos e Lula −69.834. O movimento é quase uniforme no país, com leve ganho extra nos redutos petistas.
Fonte: presidente.json (por_faixa_lula_2022; somas de votos por faixa, não médias).

**7. O comparecimento subiu no Norte e no Nordeste e caiu no Sul e no Sudeste.** Variação contra o 1º turno de 2022, em pontos: Norte +1,51; Nordeste +1,14; Centro-Oeste −0,37; Sudeste −0,75; Sul −1,12; Brasil −0,14 (78,92% contra 79,05%). Maiores altas: RO +2,94, MA +2,47, PA +2,12; maiores quedas: MS −1,78, RS −1,57, DF −1,37. Nos municípios mais lulistas de 2022 a alta foi de +2,11 pontos, e mesmo assim Lula perdeu fatia ali.
Fonte: presidente.json (regioes.*.comparacao.comparecimento_vs_1t_pp, ufs[].comparacao.comparecimento_vs_1t_pp, por_faixa_lula_2022.delta_comparecimento_pp); comparecimento de 2022 por município lido do detalhe por seção do TSE.

**8. Onde a margem mais andou.** As maiores viradas para Flávio foram TO +13,41, RS +13,31, MT +10,51 pontos. A maior queda de Lula foi em GO (−8,46), onde Caiado teve 12,33% e Flávio subiu só +1,45; Goiânia é a capital em que Flávio mais ficou abaixo de Bolsonaro (−1,41). A margem andou para Lula só em DF (−1,60).
Fonte: presidente.json (ufs[].comparacao.virada_margem_vs_1t_pp, ufs[].pct.caiado, capitais[].swing_flavio_pp).

**9. Exterior: Lula vence, o comparecimento caiu e Portugal foi o país que mais andou para Flávio entre os que têm ao menos 5 mil válidos.** Lula 47,57% contra Flávio 43,49% (13.487 votos). O eleitorado no exterior foi de 695.355 para 916.534 (+31,8%) e o comparecimento de 304.032 para 341.766 (+12,4%): a taxa caiu de 43,72% para 37,29%. Lula leva a Europa (60,27%); Flávio, a América do Norte (54,60%) e a Ásia (62,35%, Japão 71,76%). Em Portugal Flávio fez 38,57%, +7,55 pontos sobre Bolsonaro nas mesmas cidades, e Lula −7,94.
Fonte: presidente.json (ufs[uf=ZZ] e ufs[uf=ZZ].r2022.t1); exterior.json (continentes, paises[pais=PT], paises[pais=JP]).

**10. O arquivo nacional de presidente parou três vezes no pico.** 18:00:33 a 18:10:48 (10,3 min, de 12,45% para 14,24% das seções); 18:48:59 a 19:14:08 (25,2 min, de 47,26% para 64,81% das seções); 19:14:08 a 20:04:39 (50,5 min, de 64,81% para 84,96% das seções). Na parada de 50,5 minutos o coletor leu o arquivo 101 vezes, 100 delas com 304 (não modificado). A maior defasagem visível foi às 19:14: a soma dos 28 arquivos de UF tinha 110.011 seções a mais que o nacional (22,04% do total). De 19:35 a 20:04 a diferença ficou entre 94.830 e 100.593 seções, enquanto o andamento nacional (-ab) do próprio TSE já marcava 423.922. O lote que destravou, às 20:04:39, trouxe 100.614 seções e 24,73 mi de válidos (Lula 47,31%, Flávio 45,04% do lote).
Fonte: linha_do_tempo.json (travamentos.nacional, divergencia_soma_ufs.minutos e maior_diferenca_visivel, nacional.versoes colunas d_st, d_vv, lote_pct_*).

**11. Das 19:32:47 às 20:01:55 o TSE não gerou nenhum arquivo de resultado.** Em 29,1 minutos, nenhuma versão de nenhum arquivo `-u` (presidente, governador, Senado, deputados; nacional, UF, município ou zona) tem hora de geração dentro do intervalo. O coletor fez 82.573 requisições nesse tempo (57.337 com 304; as 24.148 com corpo novo trazem versões geradas antes de 19:32:47). Os 28 arquivos de UF de presidente mostram a mesma parada. Só os arquivos de andamento (-ab) tiveram versão nova no intervalo: 52, todos gerados entre 19:45:14 e 19:45:32, numa única rodada.
Fonte: linha_do_tempo.json (pausa_geral.lacunas, travamentos.ufs, travamentos.todas_as_ufs_sem_versao_nova).

**12. A hora de totalização do TSE está no relógio local.** Contra a hora de geração (Brasília), a totalização impressa fica, na mediana, −121 min no AC, −61 no AM, −61 no MT, MS, RO e RR, e chega a +59,5 min em PE (Fernando de Noronha). No exterior, Wellington imprime 05/10/2026 09:19:47 num arquivo gerado às 17:21:13 de 04/10, e o andamento nacional (-ab) exibiu 05/10/2026 09:19:47 como última totalização durante toda a noite. 36 cidades do exterior aparecem totalizadas em 05/10 em arquivos gerados em 04/10.
Fonte: linha_do_tempo.json (fuso_da_totalizacao.por_uf, divergencia_soma_ufs.andamento_br_totalizacao_impressa_na_janela); exterior.json (hora_local).

**13. A marca de cópia antiga do coletor errou em 90,7% dos casos.** Dos 8.662 eventos `idg_regressivo`, 7.857 eram versões mais novas que tudo o que o mesmo arquivo já tinha publicado; só 761 eram cópias antigas e 44 repetiam a mesma geração. O contador `idg` do TSE não cresce dentro do arquivo. Em presidente, 36 arquivos municipais e 30 de zona tinham a versão final marcada (136 e 100 seções a mais nela). A hora de 100% das UFs muda: BA 00:40:21, não 01:56:58; MG 00:46:47, não 01:57:04; PA 23:55:38, não 00:11:39 (o AM fechou às 02:59:27).
Fonte: linha_do_tempo.json (idg_regressivo.total_por_classe, idg_regressivo.presidente_versao_vigente_marcada_regressiva, conclusao_ufs).

**14. 11 arquivos municipais e 12 de zona de presidente congelaram incompletos.** Pararam em versões geradas entre 20:54:32 e 21:01:44 de 04/10, com 42 seções a menos nos municípios; o andamento (-ab) da UF já os dava completos e as leituras seguintes receberam 304 até 03:38:14 de 05/10. O arquivo de governador dos mesmos municípios está completo em 11 de 11. A soma dos municípios fica 42 seções e 9.152 válidos abaixo do nacional (Flávio −2.836, Lula −5.865).
Fonte: presidente.json (conferencia.municipios_incompletos, com secoes_governador, conferencia.soma_municipios_menos_nacional); zonas.json (n_incompletas).

**15. Depois da meia-noite chegaram 15 seções, em 6 municípios, com 3.562 válidos: Lula 87,14%, Flávio 11,23%.** Cajari (MA) 6 seções, Lula 89,91%; Barreirinha (AM) 3 seções, Lula 93,78%; Tabatinga (AM) 2 seções, Lula 96,11%; São João das Missões (MG) 2 seções, Lula 82,45%; Jutaí (AM) 1 seção, Lula 51,26%; Casa Nova (BA) 1 seção, Lula 89,46%. O andamento (-ab) confirma as mesmas 15 seções; o arquivo nacional foi de 499.233 para 499.248.
Fonte: linha_do_tempo.json (secoes_tardias).

## Inferências (rotuladas, não são medição)

- **Inferência.** No Nordeste, o ganho líquido de Flávio (+1.611.579) foi 6,2 vezes a perda líquida de Lula (−258.555), com os válidos da região subindo 1.122.739 e os terceiros caindo de 6,27% para 5,37%. O saldo é compatível com voto novo e com eleitor de terceira via, mais do que com troca direta de Lula por Flávio. Dado agregado não identifica quem trocou de voto.
- **Inferência.** No Centro-Sul, Lula perdeu mais (−3.135.837) do que Flávio ganhou (+2.785.951), com o comparecimento caindo 0,78 ponto. Parte do voto de Lula em 2022 parece ter ido para a abstenção ou para outras candidaturas, não só para Flávio.
- **Inferência.** As paradas foram de publicação, não de contagem: entre 19:14 e 19:32 os arquivos de UF e o andamento (-ab) avançaram enquanto o arquivo nacional ficou parado (achado 10), e durante a pausa total o andamento ainda publicou versão nova (achado 11). A causa da pausa não aparece nos dados; só o TSE pode explicá-la.
- **Inferência.** As seções tardias vêm de municípios remotos e de voto petista, padrão compatível com logística de transmissão, e não mudam nada: 3.562 válidos contra uma diferença de 2.224.965 votos.

## Outros cargos, para referência

- Câmara: PL 25,82 mi de votos (22,72%) contra PT 14,79 mi (13,01%); mais votado do país, Nikolas Ferreira (PL-MG), 3.119.318 votos, 27,19% da UF. Bancada por campo: esquerda 124, centro-esquerda 13, centro 84, centro-direita 119, direita 173. Fonte: camara.json (votos_por_partido, deputados_mais_votados, por_campo).
- Senado: PL 19, MDB 7, PT 6, PP 3 entre os 54 eleitos de 2026. Fonte: senado.json (eleitos_2026_por_partido).

## Correções e atualizações ao BRIEF.md que os dados impõem

- Placar: o BRIEF usa a leitura das 23:43 (499.226 seções). O final, com 499.248 seções, é Flávio 56.104.503 contra Lula 53.879.538, diferença de 2.224.965.
- Cópias antigas: o banco tem 8.662 eventos `idg_regressivo`, não 515, e só 761 são cópias antigas (achado 13).
- "Arquivos de UF parados enquanto os municipais seguiam": nenhum arquivo de nenhum nível foi gerado entre 19:32:47 e 20:01:55; as leituras com corpo novo naquele intervalo eram de versões anteriores (achado 11).
- Hora de 100% das UFs: BA 00:40:21; MG 00:46:47; PA 23:55:38 (achado 13).
- Seções tardias no AM: Barreirinha 3, Tabatinga 2, Jutaí 1; no total, 15 seções depois da meia-noite (achado 15).
- Câmara no `final.json` regerado: 3 UFs provisórias (AM, MG, SP), PSD 43 e Republicanos 41 cadeiras.

## Limites

- Comparar Flávio com Bolsonaro e Lula com Lula de 2022 mede saldo agregado entre duas eleições com candidatos e eleitorado diferentes; não é transferência de eleitor.
- O comparecimento de 2022 por município vem do detalhe por seção do TSE (cargo de presidente, 1º turno); municípios novos (Boa Esperança do Norte, MT) ficam sem 2022.
- A latência (captura menos geração) inclui o intervalo de sondagem do coletor; é teto, não medida da demora do TSE.
- Zonas casam com 2022 pelo número; rezoneamento pode mudar o território de uma zona.
- O banco continua recebendo leituras; arquivos congelados podem ser republicados e mudar as conferências numa nova execução.
