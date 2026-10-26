# Metadados das urnas por seção: repetição e coerência (2º turno de 2026)

Gerado em 2026-10-26T13:08:42+00:00. Rótulo: **pede explicação, não prova irregularidade**. Estado: completo.

## Cobertura

- BUs: 1º turno 499.187, 2º turno 499.207 seções.
- `.vsc` do 2º turno: 517.179 seções tentadas (ok 499.207, agregada 17.931, sem_vsc 41) para 499.207 BUs.
- `.vsc` do 1º turno: 8.540 seções tentadas (ok 8.108, agregada 432) para 499.187 BUs.
- Logs processados do 2º turno: 499.176 seções, 499.176 com metadados da urna.

## O que o `.vsc` contém

Arquivo DER com três blocos: assinatura de software do TSE (usuário SEVIN), assinatura de hardware da urna (usuário UEAO e a série da urna) e um rodapé com o código do modelo (13, 15, 20, 22) e o algoritmo da chave de hardware. Cada bloco lista os arquivos da seção (bu.dat, rdv.dat, jufa.dat, imgbu.dat, imgze.dat, hash.dat, wsqbio.jez, wsqman.jez, wsqmes.jez, mr.ver, log.jez; no sistema de apuração, busa.dat e logsa.jez) com tamanho, SHA-512 e assinatura. O bloco de hardware termina no certificado X.509 da urna: PEM e Ed521 nas UE2020 e UE2022 (AC UE2020 e AC UE2022), DER e ECDSA P-521 nas UE2013 e UE2015 (AC URNA). A urna assina o SHA-512 do resumo SHA-512, a mesma regra do QR Code do BU.

## Repetição entre seções, 2º turno

| Campo | Fonte | Escopo | Seções com valor | Valores distintos | Grupos repetidos | Seções em grupos | Sem explicação (grupos/seções) |
|---|---|---|---:|---:|---:|---:|---:|
| Número interno da urna | BU | urna | 499.207 | 499.180 | 2 | 29 | 0 / 0 |
| Código da carga | BU | urna | 499.207 | 499.180 | 2 | 29 | 0 / 0 |
| Número de série da flash de votação (FV) | BU | urna | 499.207 | 499.149 | 30 | 88 | 0 / 0 |
| Número de série da mídia de carga (FC) | BU | compartilhado | 499.207 | 23.170 | 22.919 | 498.956 | 0 / 0 |
| Computador que gerou a mídia de carga (nome, TPM, instalação) | BU | compartilhado | 499.207 | 2.479 | 2.435 | 499.163 | 0 / 0 |
| Versão do software de votação | BU | global | 499.207 | 1 | | | coerente: 10.23.0.0 - Praia da Barra do Cahy (499.207) |
| SHA-256 do arquivo do BU | BU | secao | 499.207 | 499.207 | 0 | 0 | 0 / 0 |
| Hash de transmissão (diretório do aux) | BU | secao | 499.207 | 499.207 | 0 | 0 | 0 / 0 |
| SHA-256 do arquivo .vsc | .vsc | secao | 499.207 | 499.207 | 0 | 0 | 0 / 0 |
| Série da urna na assinatura de hardware | .vsc | urna | 499.207 | 499.179 | 3 | 31 | 0 / 0 |
| SHA-256 do certificado de hardware | .vsc | urna | 499.207 | 499.179 | 3 | 31 | 0 / 0 |
| SHA-256 da chave pública do certificado | .vsc | urna | 499.207 | 499.179 | 3 | 31 | 0 / 0 |
| Número de série do certificado dentro da AC emissora | .vsc | urna | 499.207 | 499.179 | 3 | 31 | 0 / 0 |
| Chave de software do TSE (série) | .vsc | global | 499.207 | 1 | | | coerente: 20260708 (499.207) |
| Data da chave de software do TSE | .vsc | global | 499.207 | 1 | | | coerente: 202607021654 (499.207) |
| Número de série da memória de resultado (MR) no log, no dia da eleição | log | urna | 497.718 | 496.267 | 41 | 1.591 | 0 / 0 |
| Computador que gerou a mídia de votação, no log do dia | log | compartilhado | 497.839 | 3.471 | 3.356 | 497.732 | 0 / 0 |
| Identificador da mídia de carga no log | log | compartilhado | 499.176 | 23.225 | 22.971 | 503.019 | 0 / 0 |
| Computador da mídia de carga no log | log | compartilhado | 12.214 | 2.164 | 1.723 | 12.233 | 0 / 0 |
| Versão da aplicação no log | log | global | 499.176 | 1 | | | coerente: 10.23.0.0 - Praia da Barra do Cahy (499.176) |

- Número interno da urna: Sistema de apuração: 2 grupos, 29 seções.
- Código da carga: Sistema de apuração: 2 grupos, 29 seções.
- Número de série da flash de votação (FV): Valor de preenchimento: 1 grupos, 30 seções; Coincidência de identificador de 4 bytes entre urnas diferentes: 29 grupos, 58 seções.
  Pares iguais observados 29; esperados ao acaso entre 499.177 identificadores de 32 bits: 29,01 (limite de 99,9%: 47).
- Número de série da mídia de carga (FC): Mídia ou computador compartilhado dentro da zona ou da UF: 22.919 grupos, 498.956 seções.
  Pares iguais observados 0; esperados ao acaso entre 23.170 identificadores de 32 bits: 0,06 (limite de 99,9%: 2).
- Computador que gerou a mídia de carga (nome, TPM, instalação): Mídia ou computador compartilhado dentro da zona ou da UF: 2.435 grupos, 499.163 seções.
- Série da urna na assinatura de hardware: Sistema de apuração: 2 grupos, 29 seções; Votação recuperada: 1 grupos, 2 seções.
- SHA-256 do certificado de hardware: Sistema de apuração: 2 grupos, 29 seções; Votação recuperada: 1 grupos, 2 seções.
- SHA-256 da chave pública do certificado: Sistema de apuração: 2 grupos, 29 seções; Votação recuperada: 1 grupos, 2 seções.
- Número de série do certificado dentro da AC emissora: Sistema de apuração: 2 grupos, 29 seções; Votação recuperada: 1 grupos, 2 seções.
- Número de série da memória de resultado (MR) no log, no dia da eleição: Votação recuperada: 2 grupos, 13 seções; Memórias de resultado com o mesmo número de série em várias urnas da mesma zona: 9 grupos, 1.518 seções; Coincidência de identificador de 4 bytes entre urnas diferentes: 30 grupos, 60 seções.
  Pares iguais observados 30; esperados ao acaso entre 497.817 identificadores de 32 bits: 28,85 (limite de 99,9%: 47).
- Computador que gerou a mídia de votação, no log do dia: Mídia ou computador compartilhado dentro da zona ou da UF: 3.356 grupos, 497.732 seções.
- Identificador da mídia de carga no log: Mídia ou computador compartilhado dentro da zona ou da UF: 22.971 grupos, 503.019 seções.
  Pares iguais observados 0; esperados ao acaso entre 23.225 identificadores de 32 bits: 0,06 (limite de 99,9%: 2).
- Computador da mídia de carga no log: Mídia ou computador compartilhado dentro da zona ou da UF: 1.723 grupos, 12.233 seções.

### Coerência BU × `.vsc`, 2º turno (499.207 seções com `.vsc` lido)

- Número interno do BU igual à série da assinatura de hardware: 499.191 sim, 0 não.
- CN do certificado igual à série: 499.207 sim, 0 não.
- Modelo no `.vsc` igual ao do BU: 499.178 sim, 0 não; AC compatível com o modelo: 499.207 sim, 0 não.
- Cadeia até a AC arquivada: 499.207 sim, 0 não. Por AC: AC UE2020 200.504, AC UE2022 198.746, AC URNA 99.957.
- Autoassinatura de hardware: 499.207 sim, 0 não; assinatura de hardware do BU: 499.207 sim, 0 não.
- BU publicado com o SHA-512 listado no `.vsc`: 499.207 sim, 0 não.
- Certificado válido no dia: 499.207 sim, 0 não.
- Minutos entre a emissão do BU e a assinatura de hardware: mediana 0,80, máximo 190,27.
- Falhas por teste: id_bu_diferente_da_serie_hw 0, modelo_vsc_diferente_do_bu 0, ac_incompativel_com_modelo 0, cadeia_valida_falso 0, hw_assinatura_ok_falso 0, hw_bu_assinatura_ok_falso 0, listas_ok_falso 0, hw_resumo_ok_falso 0, sw_resumo_ok_falso 0, cn_confere_usuario_falso 0, bu_diferente_do_vsc 0, certificado_fora_da_validade 0, vsc_antes_da_emissao_do_bu 0, vsc_mais_de_4h_depois_da_emissao 0.

## Repetição entre seções, 1º turno

| Campo | Fonte | Escopo | Seções com valor | Valores distintos | Grupos repetidos | Seções em grupos | Sem explicação (grupos/seções) |
|---|---|---|---:|---:|---:|---:|---:|
| Número interno da urna | BU | urna | 499.187 | 499.159 | 1 | 29 | 0 / 0 |
| Código da carga | BU | urna | 499.187 | 499.159 | 1 | 29 | 0 / 0 |
| Número de série da flash de votação (FV) | BU | urna | 499.187 | 499.122 | 31 | 96 | 0 / 0 |
| Número de série da mídia de carga (FC) | BU | compartilhado | 499.187 | 23.067 | 22.888 | 499.008 | 0 / 0 |
| Computador que gerou a mídia de carga (nome, TPM, instalação) | BU | compartilhado | 499.187 | 2.453 | 2.422 | 499.156 | 0 / 0 |
| Versão do software de votação | BU | global | 499.187 | 1 | | | coerente: 10.23.0.0 - Praia da Barra do Cahy (499.187) |
| SHA-256 do arquivo do BU | BU | secao | 499.187 | 499.187 | 0 | 0 | 0 / 0 |
| Hash de transmissão (diretório do aux) | BU | secao | 499.187 | 499.187 | 0 | 0 | 0 / 0 |
| SHA-256 do arquivo .vsc | .vsc | secao | 8.108 | 8.108 | 0 | 0 | 0 / 0 |
| Série da urna na assinatura de hardware | .vsc | urna | 8.108 | 8.108 | 0 | 0 | 0 / 0 |
| SHA-256 do certificado de hardware | .vsc | urna | 8.108 | 8.108 | 0 | 0 | 0 / 0 |
| SHA-256 da chave pública do certificado | .vsc | urna | 8.108 | 8.108 | 0 | 0 | 0 / 0 |
| Número de série do certificado dentro da AC emissora | .vsc | urna | 8.108 | 8.108 | 0 | 0 | 0 / 0 |
| Chave de software do TSE (série) | .vsc | global | 8.108 | 1 | | | coerente: 20260708 (8.108) |
| Data da chave de software do TSE | .vsc | global | 8.108 | 1 | | | coerente: 202607021654 (8.108) |
| Número de série da memória de resultado (MR) no log, no dia da eleição | log | urna | 0 | | | | sem dados |
| Computador que gerou a mídia de votação, no log do dia | log | compartilhado | 0 | | | | sem dados |
| Identificador da mídia de carga no log | log | compartilhado | 0 | | | | sem dados |
| Computador da mídia de carga no log | log | compartilhado | 0 | | | | sem dados |
| Versão da aplicação no log | log | global | 0 | | | | sem dados |

- Número interno da urna: Sistema de apuração: 1 grupos, 29 seções.
- Código da carga: Sistema de apuração: 1 grupos, 29 seções.
- Número de série da flash de votação (FV): Valor de preenchimento: 1 grupos, 36 seções; Coincidência de identificador de 4 bytes entre urnas diferentes: 30 grupos, 60 seções.
  Pares iguais observados 30; esperados ao acaso entre 499.151 identificadores de 32 bits: 29,01 (limite de 99,9%: 47).
- Número de série da mídia de carga (FC): Mídia ou computador compartilhado dentro da zona ou da UF: 22.888 grupos, 499.008 seções.
  Pares iguais observados 0; esperados ao acaso entre 23.067 identificadores de 32 bits: 0,06 (limite de 99,9%: 2).
- Computador que gerou a mídia de carga (nome, TPM, instalação): Mídia ou computador compartilhado dentro da zona ou da UF: 2.422 grupos, 499.156 seções.

### Coerência BU × `.vsc`, 1º turno (8.108 seções com `.vsc` lido)

- Número interno do BU igual à série da assinatura de hardware: 8.108 sim, 0 não.
- CN do certificado igual à série: 8.108 sim, 0 não.
- Modelo no `.vsc` igual ao do BU: 8.108 sim, 0 não; AC compatível com o modelo: 8.108 sim, 0 não.
- Cadeia até a AC arquivada: 8.108 sim, 0 não. Por AC: AC UE2022 4.150, AC UE2020 3.958.
- Autoassinatura de hardware: 8.108 sim, 0 não; assinatura de hardware do BU: 8.108 sim, 0 não.
- BU publicado com o SHA-512 listado no `.vsc`: 8.108 sim, 0 não.
- Certificado válido no dia: 8.108 sim, 0 não.
- Minutos entre a emissão do BU e a assinatura de hardware: mediana 1,05, máximo 17,22.
- Falhas por teste: id_bu_diferente_da_serie_hw 0, modelo_vsc_diferente_do_bu 0, ac_incompativel_com_modelo 0, cadeia_valida_falso 0, hw_assinatura_ok_falso 0, hw_bu_assinatura_ok_falso 0, listas_ok_falso 0, hw_resumo_ok_falso 0, sw_resumo_ok_falso 0, cn_confere_usuario_falso 0, bu_diferente_do_vsc 0, certificado_fora_da_validade 0, vsc_antes_da_emissao_do_bu 0, vsc_mais_de_4h_depois_da_emissao 0.

## A mesma seção nos dois turnos

- Seções com `.vsc` nos dois turnos: 8.108; mesma urna e mesmo certificado 8.009; urna e certificado trocados juntos 99.
- Mesma urna com certificado diferente: 0. Urna diferente com o mesmo certificado: 0. Certificado do 1º turno em outra seção no 2º: 2.
- Carga (BU, 499.187 seções): mesma urna e mesma carga 494.394; mesma urna com carga nova 359 (359 com a carga feita entre 05/10 e 24/10, recarga para o 2º turno); urna trocada 4.434, das quais com o mesmo código de carga 0.

## BU × log do 2º turno

- id_do_bu_no_log: cobertas 499.176, confere 499.176, não confere 0.
- carga_do_bu_no_log: cobertas 499.176, confere 499.176, não confere 0.
- midia_fc_do_bu_no_log: cobertas 499.176, confere 499.176, não confere 0.
- computador_da_midia_no_log: cobertas 12.214, confere 12.214, não confere 0.
- versao_do_bu_no_log: cobertas 499.176, confere 499.176, não confere 0.
- Carga registrada no log da urna do BU: 499.176 cobertas; antes da abertura 499.176, depois da abertura pelo log 5 (em 5 o BU registra a carga antes da abertura: relógio, não carga no dia), depois da abertura também pelo BU 0, no dia da eleição 1. Por mês: 2026-08 8, 2026-09 491.600, 2026-10 7.568.
- Reinícios durante a votação: 12.378 seções de 499.176. Distribuição: 0: 486.798, 1: 9.196, 2: 1.772, 3: 667, 4: 336, 5: 167, 6: 92, 7: 55, 8: 35, 9: 20, 10: 8, 11: 13, 12: 7, 13: 2, 14: 3, 16: 1, 17: 2, 20: 1, 21: 1.
- urna_do_bu_no_log_pelo_processamento: 499.176 sim, 0 não.
- carga_do_bu_no_log_pelo_processamento: 499.176 sim, 0 não.
- Seções com outra urna além da do BU no log: 1.839.

## Voto nos grupos fora da regra

Fatia de Flávio entre os válidos dos dois finalistas, menos a média das demais seções do município; e a mesma diferença para a variação 1º → 2º turno. Média, erro-padrão e IC de 95%.

| Grupo | n | 2º turno contra vizinhas (pp) | IC 95% | Dif. em dif. contra o 1º turno (pp) | IC 95% |
|---|---:|---:|---|---:|---|
| mr_mesma_serie_na_zona | 306 | 2,53 | 1,55 a 3,51 | 0,07 | -0,19 a 0,33 |
| mr_mesma_serie_na_zona_exterior | 1.212 | -4,20 | -6,70 a -1,70 | -1,68 | -2,21 a -1,15 |
| mesma_urna_carga_nova | 359 | -0,59 | -1,31 a 0,12 | -0,16 | -0,38 a 0,05 |
| data_de_carga_do_log_diverge_do_bu | 5 | -1,95 | -6,95 a 3,05 | 0,22 | -3,39 a 3,83 |
| reinicio_durante_votacao | 12.378 | -0,10 | -0,24 a 0,03 | -0,01 | -0,05 a 0,02 |
| qualquer sinal fora da regra (exceto recarga entre turnos, reinício, MR repetida na zona e data de carga do log) | 0 | | | | |

Nota (26/10, capítulo logs): as duas linhas mr_ são média simples por seção, sensibilidade. O número publicado no dossiê, nos mesmos 306 seções do Brasil, ponderado pelos votos dos dois finalistas e com 5 ou mais vizinhas, é +0,19 pp (IC95 -0,07 a +0,44); o exterior fica separado.

## Pendências

- `.vsc` do 1º turno parcial: a comparação de certificado entre turnos cobre só as seções já lidas.
- A assinatura de software (SEVIN, algoritmo 3 de 256 bits) não é verificada; só o resumo SHA-512 dela.
