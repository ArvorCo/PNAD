# Politize sua vizinhança: relatório do build

Gerado em 2026-10-07T21:11:21+00:00 por `python3 scripts/politize-build.py `. Tempo total: 118,9 s.

Escopo: nacional (27 UFs e exterior). Contrato: `analysis/politize/CONTRATO.md`. Decisões e desvios: `analysis/politize/DECISOES.md`.

## Conferência das somas

| conta | Flávio (22) | Lula (13) |
|---|---:|---:|
| soma dos locais | 56.102.134 | 53.877.286 |
| soma das seções (camada zona/) | 56.102.134 | 53.877.286 |
| banco de boletins (`voto_secao`, cargo 1) | 56.102.134 | 53.877.286 |
| diferença locais menos banco | 0 | 0 |
| totalização oficial do TSE | 56.104.503 | 53.879.538 |
| oficial menos banco | 2.369 | 2.252 |

Seções principais sem boletim no banco: 61. São as seções do exterior não instaladas e as 20 seções de Betim, Uberlândia e Carapicuíba cujo arquivo não foi publicado (`aux_404`), que a totalização oficial inclui e o banco por seção não tem; é a diferença entre o banco e o total oficial. Votos nominais em número fora da lista de candidaturas (número 28) contam como nulos, como no TSE: 5.246 votos. Seções cuja soma de votos difere do comparecimento: 0. Seções com boletim fora do cadastro de locais: 0.

## Recentragem do voto esperado (por UF)

Método: deslocamento aditivo por UF: esperado = bruto + (urna da UF − média do bruto na UF), médias ponderadas por válidos sobre os locais com renda estimada; o exterior não tem PNAD e fica sem esperado.

| UF | válidos | bruto Flávio | urna Flávio | desloc. Flávio | recentrado Flávio | bruto Lula | urna Lula | desloc. Lula | recentrado Lula | confere |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| AC | 469.066 | 40,51 | 64,56 | 24,04 | 64,555 | 48,89 | 28,73 | -20,16 | 28,732 | ok |
| AL | 1.818.856 | 39,87 | 40,45 | 0,58 | 40,449 | 49,66 | 54,73 | 5,07 | 54,730 | ok |
| AM | 2.170.763 | 42,23 | 45,00 | 2,76 | 44,996 | 46,90 | 48,23 | 1,33 | 48,232 | ok |
| AP | 464.858 | 42,96 | 45,67 | 2,71 | 45,665 | 46,02 | 45,71 | -0,30 | 45,714 | ok |
| BA | 8.560.291 | 40,58 | 28,53 | -12,04 | 28,534 | 48,84 | 66,17 | 17,34 | 66,175 | ok |
| CE | 5.617.814 | 40,08 | 31,27 | -8,80 | 31,273 | 49,42 | 63,29 | 13,87 | 63,286 | ok |
| DF | 1.772.808 | 45,89 | 51,31 | 5,42 | 51,309 | 42,45 | 38,11 | -4,33 | 38,111 | ok |
| ES | 2.251.078 | 43,44 | 54,78 | 11,35 | 54,782 | 45,48 | 37,76 | -7,72 | 37,761 | ok |
| GO | 3.827.823 | 44,26 | 53,60 | 9,35 | 53,605 | 44,52 | 31,06 | -13,46 | 31,059 | ok |
| MA | 4.010.439 | 39,90 | 30,90 | -9,00 | 30,895 | 49,64 | 63,99 | 14,35 | 63,991 | ok |
| MG | 11.974.357 | 44,18 | 48,24 | 4,06 | 48,242 | 44,60 | 43,33 | -1,28 | 43,328 | ok |
| MS | 1.490.278 | 44,92 | 58,60 | 13,68 | 58,603 | 43,72 | 34,68 | -9,04 | 34,682 | ok |
| MT | 1.993.288 | 45,30 | 65,15 | 19,84 | 65,148 | 43,27 | 29,18 | -14,09 | 29,182 | ok |
| PA | 4.863.172 | 41,60 | 44,50 | 2,90 | 44,497 | 47,64 | 49,91 | 2,28 | 49,911 | ok |
| PB | 2.513.747 | 40,67 | 33,07 | -7,60 | 33,073 | 48,72 | 61,31 | 12,58 | 61,308 | ok |
| PE | 5.601.017 | 40,22 | 31,03 | -9,18 | 31,031 | 49,24 | 63,45 | 14,22 | 63,452 | ok |
| PI | 2.146.394 | 40,72 | 24,09 | -16,64 | 24,088 | 48,66 | 70,99 | 22,33 | 70,989 | ok |
| PR | 6.585.243 | 45,32 | 59,91 | 14,59 | 59,912 | 43,22 | 31,20 | -12,02 | 31,200 | ok |
| RJ | 9.369.700 | 42,93 | 53,01 | 10,08 | 53,010 | 46,05 | 39,41 | -6,64 | 39,415 | ok |
| RN | 2.071.898 | 41,14 | 34,77 | -6,36 | 34,775 | 48,18 | 59,75 | 11,57 | 59,750 | ok |
| RO | 968.059 | 43,37 | 67,45 | 24,08 | 67,453 | 45,55 | 25,89 | -19,65 | 25,894 | ok |
| RR | 325.545 | 42,85 | 71,06 | 28,21 | 71,057 | 46,16 | 22,86 | -23,30 | 22,860 | ok |
| RS | 6.423.046 | 45,01 | 55,64 | 10,63 | 55,640 | 43,61 | 35,73 | -7,89 | 35,727 | ok |
| SC | 4.500.897 | 46,54 | 66,65 | 20,11 | 66,654 | 41,79 | 25,04 | -16,74 | 25,043 | ok |
| SE | 1.364.196 | 40,47 | 30,63 | -9,84 | 30,629 | 48,95 | 62,75 | 13,80 | 62,749 | ok |
| SP | 24.879.644 | 45,55 | 51,93 | 6,39 | 51,932 | 42,95 | 38,20 | -4,75 | 38,200 | ok |
| TO | 930.447 | 43,20 | 50,44 | 7,24 | 50,440 | 45,74 | 43,42 | -2,32 | 43,421 | ok |

Conferência por UF (média do esperado recentrado = urna da UF, tolerância 0,05 pp): 27 de 27 ok.
Média nacional do esperado recentrado: 47,0377 (Lula 45,1562), contra a urna dos locais no Brasil 47,0377 (diferença -0,0000 pp) e a urna nacional com exterior 47,0278 (diferença 0,0098 pp; tolerância 0,05 pp: ok). Vão médio ponderado por válidos nos locais: -0,0000 pp; nas seções: 0,0000 pp (o deslocamento é calculado sobre os locais e aplicado igual às seções).

Voto por faixa de renda nas pesquisas (válidos, média simples das duas casas):

| faixa | Flávio | Lula |
|---|---:|---:|
| até 2 SM | 33,48 | 57,06 |
| 2 a 5 SM | 49,11 | 39,17 |
| mais de 5 SM | 50,26 | 36,93 |

## Cobertura

- Locais com voto: 94.264 (94.093 no Brasil); seções principais com boletim: 499.187; aptos: 158.738.003.
- Locais no Brasil com coordenada: 93.473 (99,3%); com setor censitário: 93.464 (99,3%); com CEP válido: 93.541.
- 2022 (mesma seção e mesmo número de local): 85.342 locais com ao menos uma seção casada, 66.495 com todas; aptos casados 88,3% dos aptos.
- Renda estimada (PNAD): 94.093 locais no Brasil.
- Situação do setor: rural 27.565, sem setor 634, urbana 65.894
- Tipo do setor: aldeia 712, comum 88.131, favela 1.786, militar 23, outro 1.336, prisao 70, quilombo 1.405, sem setor 630

Perfil do eleitorado por UF (fonte; locais por seção, por zona, sem perfil):

| UF | arquivo por seção | locais por seção | locais por zona | sem perfil |
|---|---|---:|---:|---:|
| AC | ok | 660 | 0 | 0 |
| AL | arquivo por seção ausente | 0 | 1.075 | 0 |
| AM | arquivo por seção ausente | 0 | 1.619 | 0 |
| AP | arquivo por seção ausente | 0 | 370 | 0 |
| BA | arquivo por seção ausente | 0 | 9.198 | 0 |
| CE | arquivo por seção ausente | 0 | 6.703 | 0 |
| DF | arquivo por seção ausente | 0 | 622 | 0 |
| ES | arquivo por seção ausente | 0 | 1.765 | 0 |
| GO | arquivo por seção ausente | 0 | 2.476 | 0 |
| MA | arquivo por seção ausente | 0 | 5.779 | 0 |
| MG | arquivo por seção ausente | 0 | 10.073 | 0 |
| MS | arquivo por seção ausente | 0 | 1.021 | 0 |
| MT | arquivo por seção ausente | 0 | 1.501 | 0 |
| PA | arquivo por seção ausente | 0 | 5.784 | 0 |
| PB | arquivo por seção ausente | 0 | 1.837 | 0 |
| PE | arquivo por seção ausente | 0 | 3.389 | 0 |
| PI | arquivo por seção ausente | 0 | 3.368 | 0 |
| PR | arquivo por seção ausente | 0 | 4.792 | 0 |
| RJ | arquivo por seção ausente | 0 | 5.046 | 0 |
| RN | arquivo por seção ausente | 0 | 1.565 | 0 |
| RO | arquivo por seção ausente | 0 | 671 | 0 |
| RR | arquivo por seção ausente | 0 | 355 | 0 |
| RS | arquivo por seção ausente | 0 | 7.774 | 0 |
| SC | arquivo por seção ausente | 0 | 3.450 | 0 |
| SE | arquivo por seção ausente | 0 | 1.207 | 0 |
| SP | arquivo por seção ausente | 0 | 11.072 | 0 |
| TO | arquivo por seção ausente | 0 | 921 | 0 |
| ZZ | arquivo por seção ausente | 0 | 171 | 0 |

## Índice de conversa

Teto do potencial: 40 votos por 100 aptos. p99 observado do potencial: 44,78. Locais com índice 100 (saturados): 2.593.

| ponto da distribuição | índice (locais) | índice (seções com 30 aptos ou mais) | potencial (locais) | coluna `percentil` (locais do Brasil) |
|---|---:|---:|---:|---:|
| p1 | 29,0 | 31,0 | 11,63 | 0,0 |
| p5 | 37,0 | 37,0 | 14,70 | 4,6 |
| p10 | 40,0 | 41,0 | 16,09 | 9,2 |
| p25 | 46,0 | 47,0 | 18,52 | 25,0 |
| p50 | 55,0 | 56,0 | 22,08 | 50,0 |
| p75 | 68,0 | 69,0 | 27,22 | 75,0 |
| p90 | 82,0 | 83,0 | 32,96 | 89,8 |
| p95 | 92,0 | 91,0 | 36,70 | 94,4 |
| p99 | 100,0 | 100,0 | 44,78 | 98,1 |

A coluna `percentil` é a posição do potencial do local entre os locais do Brasil com boletim (0 a 100, arredondada para baixo; 100 = maior potencial do país); a da seção usa as seções com 30 aptos ou mais; `percentil_uf` repete a conta dentro da UF. O exterior só tem `percentil_uf`.

Seções com menos de 30 aptos (votos omitidos na camada zona/): 71.

Por região (médias ponderadas: índice e componentes por aptos, vão por válidos):

| região | locais | Flávio (% válidos) | índice médio | vão do perfil (pp) | c_perfil | c_ausentes | índice 100 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Centro-Oeste | 5.620 | 56,5 | 61,4 | -0,00 | 2,55 | 10,85 | 335 |
| Exterior | 171 | 43,5 | 91,5 | sem dado | sem dado | 31,35 | 50 |
| Nordeste | 34.121 | 30,9 | 52,0 | 0,00 | 3,19 | 9,20 | 46 |
| Norte | 10.380 | 49,2 | 53,7 | 0,00 | 4,05 | 9,72 | 683 |
| Sudeste | 27.956 | 51,4 | 63,0 | -0,00 | 3,00 | 11,35 | 1.028 |
| Sul | 16.016 | 60,1 | 57,3 | 0,00 | 3,05 | 10,23 | 451 |

## Arquétipos

| arquétipo | locais | % dos locais | % dos aptos | seções | secundário |
|---|---:|---:|---:|---:|---:|
| Fortaleza (`fortaleza`) | 18.920 | 20,1% | 21,1% | 110.381 | 0 |
| Muro (`muro`) | 27.649 | 29,3% | 15,0% | 83.137 | 0 |
| Pêndulo (`pendulo`) | 9.096 | 9,6% | 12,6% | 61.118 | 0 |
| Reencontro (`reencontro`) | 198 | 0,2% | 0,1% | 3.019 | 355 |
| Terreno fértil (`fertil`) | 22.892 | 24,3% | 35,8% | 158.851 | 17.551 |
| Dormindo (`dormindo`) | 1.136 | 1,2% | 1,1% | 8.874 | 3.872 |
| Abaixo do perfil (`abaixo_do_perfil`) | 3.543 | 3,8% | 2,8% | 15.606 | 25.025 |
| Na frente (`frente`) | 4.541 | 4,8% | 5,2% | 27.838 | 0 |
| Atrás (`atras`) | 6.289 | 6,7% | 6,4% | 30.363 | 0 |
| sem secundário | | | | | 47.461 |

## Conta do 2º turno

Transferência da terceira via: 30% sem escolha, 61% de quem escolhe para Flávio (coeficientes 0,427 e 0,273). Taxa de conversão declarada: 0,35.

Projeção somada (nacional do build): Flávio 60.080.145, Lula 56.420.605. Locais onde Flávio já passa: 44.609 de 94.264.

## PNAD

Preços de 2026-07 (fator IPCA 1,00811 sobre 2026-04); salário mínimo de 2026: R$ 1.621. Células substituídas por terem menos de 30 observações: 0.

## Tempos por UF (s)

AC 0,2, AL 0,5, AM 0,8, AP 0,2, BA 3,3, CE 2,6, DF 0,8, ES 1,1, GO 2,2, MA 2,0, MG 5,4, MS 0,8, MT 0,8, PA 2,3, PB 1,1, PE 2,5, PI 1,4, PR 2,8, RJ 6,3, RN 2,2, RO 0,8, RR 0,3, RS 3,2, SC 1,8, SE 0,6, SP 16,0, TO 0,5, ZZ 0,1
