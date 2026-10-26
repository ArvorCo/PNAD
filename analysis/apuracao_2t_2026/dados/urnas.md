# IDs das urnas por seção, 1º e 2º turnos de 2026

Gerado em 2026-10-26T15:54:23+00:00. Coleta do 2º turno: **completa**. Rótulo de tudo o que segue: pede explicação, não prova irregularidade.

Reprodução: `python3 scripts/apuracao-2t-2026-urnas.py` (lê os dois bancos de BUs por seção em modo somente leitura; reexecutável sobre a coleta parcial e a completa).

## O que se alegou em 2022 e o que o TSE respondeu

Fontes arquivadas com SHA-256 em `analysis/apuracao_2t_2026/urnas_fontes/fontes.json`.

- **A alegação** [pl_peticao, poder360_250mil, poder360_pedido]. Em 22/11/2022 a Coligação Pelo Bem do Brasil (PL, PP e Republicanos) pediu ao TSE verificação extraordinária (PetCiv 0601958-94.2022.6.00.0000), com relatório do Instituto Voto Legal. O argumento: nos logs das urnas UE2009, 2010, 2011, 2013 e 2015 o campo que deveria identificar a urna trazia o mesmo número, 67305985, em 59,1% das linhas; seriam 279.336 urnas (a decisão fala em 279.383). Pedia invalidar os votos dessas urnas só no 2º turno. A alegação era de um número genérico repetido no log de todas as urnas antigas, **não** de uma mesma urna votando em várias seções.
- **A resposta** [moraes_despacho, tse_decisao, cnn_area_tecnica, tse_noticia_plenario, agenciabrasil_plenario]. Em 22/11 o ministro Alexandre de Moraes deu 24 horas para incluir o 1º turno; em 23/11 indeferiu a petição por inépcia e falta de indícios, fixou multa de R$ 22.991.544,60 por litigância de má-fé e determinou outras providências; o Plenário confirmou em 15/12/2022. O parecer técnico da Secretaria de Tecnologia da Informação, transcrito na decisão, diz que cada urna tem número interno único (ID Urna), que o código de carga é gerado a partir dele, da seção e da hora da carga, fica gravado no log e consta do BU, e que por isso a urna é identificável independentemente do número interno no log das urnas antigas. As fontes oficiais obtidas não explicam a causa da repetição do 67305985.
- **Checagem com caso real** [aosfatos]. Na seção 511 da 1ª zona de Rio Branco (AC), o BU traz o ID 1103958, o log traz 67305985, e os dois compartilham o mesmo código de carga, mídia, seção, zona e município.

## O que os BUs e logs de 2026 mostram sobre o mesmo fenômeno

- **O número de 2022 não aparece.** Em nenhuma seção de 2026 o log traz 67305985 (1º turno: 0; 2º turno até aqui: 0). Seções em que o número interno do BU escreveu linhas no log, por modelo (1º turno): UE2013 11.919 de 11.921; UE2015 88.030 de 88.032; UE2020 200.447 de 200.453; UE2022 198.652 de 198.656; (2º turno até aqui): UE2013 12.455 de 12.455; UE2015 87.471 de 87.472; UE2020 200.489 de 200.490; UE2022 198.734 de 198.735. Nas UE2013 e UE2015, o campo do log que em 2022 trazia o número genérico traz agora o número interno da urna, como nas UE2020 e UE2022.
- **ID do BU contra o log.** No 1º turno, 14 seções têm um ID no BU que não escreveu linha no log; por tipo de arquivo {'2': 14} (2 = votação recuperada: o BU sai da mídia da urna que falhou, gravado por outra urna, cujo log é o que se publica). No 2º turno até aqui: 3.
- **Mesma urna em mais de uma seção.** 1º turno: 1 ID(s) em 29 seções (1 ID(s) de classe sistema_apuracao, mesma uf, UF ZZ); sem explicação pela regra: 0. 2º turno até aqui: 2 ID(s) em 29 seções (2 ID(s) de classe sistema_apuracao, mesma uf, UF ZZ); sem explicação pela regra: 0. Classe sistema_apuracao: o BU foi emitido pelo sistema de apuração da junta (tipo de arquivo 3 a 6) e o número interno é o do equipamento da junta, não de uma urna que recebeu votos na seção.
- **Mesma seção, mesma urna?** Das 499.187 seções com BU nos dois turnos, 494.753 votaram na mesma urna e 4.434 em urna diferente. Mesma urna com o mesmo código de carga: 494.394; mesma urna com carga diferente (recarga entre turnos): 359. Origem das urnas trocadas: {'urna_sem_bu_no_1t': 4353, 'veio_de_outra_secao_da_zona': 41, 'veio_de_outro_municipio': 28, 'veio_de_outra_zona_do_municipio': 12}. Tipo da urna no 2º turno entre as trocadas: {'4': 2816, '1': 1607, '3': 9, '6': 2} (1 = urna de seção, 4 = reserva que substituiu a da seção no dia). `urna_sem_bu_no_1t` é urna que não emitiu BU no 1º turno: substituição antes do 2º turno (com carga nova depois de 04/10) ou reserva acionada no dia.
- **As trocadas votam diferente das vizinhas?** Variação da fatia de Flávio do 1º para o 2º turno, menos a das seções do mesmo município que mantiveram a urna: todas as trocadas 0,02 pp (n = 4.425, IC95 -0,04 a 0,08); reserva ou contingência no 2º turno 0,04 pp (n = 2.818, IC95 -0,04 a 0,11); urna de seção diferente da do 1º turno -0,00 pp (n = 1.607, IC95 -0,10 a 0,10). Comparecimento, mesma conta: 0,08 pp (n = 4.425, IC95 0,00 a 0,16). Para cada seção com urna trocada: variação da fatia de Flávio (ou do comparecimento) do 1º para o 2º turno menos a variação média das seções do mesmo município que mantiveram a urna (mínimo de 3). Em pontos percentuais; IC de 95% pela aproximação normal. Não é efeito causal: a troca de urna acontece por defeito, e defeito não é sorteado.
- **Urnas que mudaram de seção entre os turnos**: {'urnas_em_outra_secao': 100, 'mesmo_municipio': 53, 'outro_municipio': 47, 'por_tipo_urna_2t': {'1': 48, '4': 33, '3': 19}}.

## Por turno

### 1º turno (base)

- Seções com BU lido: 499.187 de 499.248 seções principais do catálogo (99,99%).
- Modelos: UE2020 200.453 (40,16%); UE2022 198.656 (39,80%); UE2015 88.032 (17,64%); UE2013 11.921 (2,39%); sem informação 125 (0,03%).
- Tipo de urna no BU: seção 496.123; reserva da seção 3.033; contingência 31.
- IDs distintos: 499.159. IDs em mais de uma seção: 1, somando 29 seções.
  - BU emitido pelo sistema de apuração: o número é o do equipamento da junta, não de uma urna de votação: 1 IDs, 29 seções.
- Sem explicação pela regra: 0 IDs.
- ID do BU ausente das urnas que escreveram o log: 14 seções (por tipo de arquivo: {'2': 14}); seções cujo log traz o número 67305985 de 2022: 0.
- Código de carga repetido entre seções: 1 códigos, 29 seções.
- Carga: de 2026-09-15 15:57:00 a 2026-10-04 09:54:00; sem data 0; carga depois do 1º turno 0; carga depois da eleição 0; carga no dia da eleição 7 (por tipo de urna {'1': 4, '4': 3}); carga registrada depois do primeiro voto da seção 2, das quais sem contingência, reserva ou recarga declarada 0 (a abertura do BU de urna de reserva é a da seção, anterior à carga da reserva); BU com seção diferente do caminho 0.
- Seções com ID repetido, fatia de Flávio contra as vizinhas do município: sem seções comparáveis.

### 2º turno

- Seções com BU lido: 499.207 de 499.248 seções principais do catálogo (99,99%).
- Modelos: UE2020 200.490 (40,16%); UE2022 198.735 (39,81%); UE2015 87.472 (17,52%); UE2013 12.455 (2,50%); sem informação 55 (0,01%).
- Tipo de urna no BU: seção 493.464; reserva da seção 5.712; contingência 29; reserva ao encerrar 2.
- IDs distintos: 499.180. IDs em mais de uma seção: 2, somando 29 seções.
  - BU emitido pelo sistema de apuração: o número é o do equipamento da junta, não de uma urna de votação: 2 IDs, 29 seções.
- Sem explicação pela regra: 0 IDs.
- ID do BU ausente das urnas que escreveram o log: 3 seções (por tipo de arquivo: {'2': 3}); seções cujo log traz o número 67305985 de 2022: 0.
- Código de carga repetido entre seções: 2 códigos, 29 seções.
- Carga: de 2026-09-15 15:57:00 a 2026-10-25 10:04:00; sem data 0; carga depois do 1º turno 2.245; carga depois da eleição 0; carga no dia da eleição 5 (por tipo de urna {'1': 5}); carga registrada depois do primeiro voto da seção 0, das quais sem contingência, reserva ou recarga declarada 0 (a abertura do BU de urna de reserva é a da seção, anterior à carga da reserva); BU com seção diferente do caminho 0.
- Seções com ID repetido, fatia de Flávio contra as vizinhas do município: sem seções comparáveis.
- Mesmas seções, variação contra o próprio 1º turno menos a das vizinhas: sem seções comparáveis.

## Regra de classificação dos IDs repetidos

Para cada número interno presente em mais de uma seção do mesmo turno, testam-se as explicações legítimas nesta ordem: (1) mesmo BU, isto é, seção agregada; (2) BU emitido pelo sistema de apuração (tipo de arquivo 3 a 6); (3) se algum par de seções tem intervalo de votação (primeiro ao último voto, hora local da urna) sobreposto, a mesma urna não poderia estar nas duas: fica sem explicação; (4) contingência, reserva (tipo de urna 3, 4 ou 6) ou recarga (mais de uma carga) com horários disjuntos: troca compatível; (5) horários disjuntos sem nenhuma dessas declarações: sem explicação pela regra. Geografia registrada à parte (mesmo local, zona, município, UF ou UFs diferentes). Comparação de horários entre UFs de fusos diferentes é marcada.

## Limites

- Lê os BUs publicados pelo TSE e o resumo das urnas que escreveram o log, feito pelo coletor de BUs; não valida assinatura digital dos arquivos.
- Enquanto a coleta do 2º turno não termina, a ordem de coleta é por UF e os números do 2º turno não representam o país.
- A diferença em diferenças compara seções que trocaram de urna com vizinhas que não trocaram; troca de urna decorre de defeito ou de logística, não de sorteio, e por isso não identifica efeito causal.
- pede explicação, não prova irregularidade.
