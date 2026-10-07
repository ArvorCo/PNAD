# Politize sua vizinhança: relatório do build

Gerado em 2026-10-07T23:10:47+00:00 por `python3 scripts/politize-build.py `. Tempo total: 443,3 s.

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
| AL | 1.818.856 | 39,89 | 40,45 | 0,56 | 40,449 | 49,64 | 54,73 | 5,09 | 54,730 | ok |
| AM | 2.170.763 | 42,23 | 45,00 | 2,76 | 44,996 | 46,90 | 48,23 | 1,33 | 48,232 | ok |
| AP | 464.858 | 42,97 | 45,67 | 2,70 | 45,665 | 46,00 | 45,71 | -0,28 | 45,714 | ok |
| BA | 8.560.291 | 40,61 | 28,53 | -12,08 | 28,534 | 48,80 | 66,17 | 17,38 | 66,175 | ok |
| CE | 5.617.814 | 40,10 | 31,27 | -8,82 | 31,273 | 49,39 | 63,29 | 13,89 | 63,286 | ok |
| DF | 1.772.808 | 45,90 | 51,31 | 5,41 | 51,309 | 42,43 | 38,11 | -4,32 | 38,111 | ok |
| ES | 2.251.078 | 43,45 | 54,78 | 11,33 | 54,782 | 45,46 | 37,76 | -7,70 | 37,761 | ok |
| GO | 3.827.823 | 44,27 | 53,60 | 9,34 | 53,605 | 44,51 | 31,06 | -13,45 | 31,059 | ok |
| MA | 4.010.439 | 39,93 | 30,90 | -9,04 | 30,895 | 49,59 | 63,99 | 14,40 | 63,991 | ok |
| MG | 11.974.357 | 44,20 | 48,24 | 4,05 | 48,242 | 44,59 | 43,33 | -1,26 | 43,328 | ok |
| MS | 1.490.278 | 44,94 | 58,60 | 13,66 | 58,603 | 43,70 | 34,68 | -9,02 | 34,682 | ok |
| MT | 1.993.288 | 45,32 | 65,15 | 19,83 | 65,148 | 43,26 | 29,18 | -14,08 | 29,182 | ok |
| PA | 4.863.172 | 41,64 | 44,50 | 2,86 | 44,497 | 47,59 | 49,91 | 2,32 | 49,911 | ok |
| PB | 2.513.747 | 40,68 | 33,07 | -7,61 | 33,073 | 48,71 | 61,31 | 12,60 | 61,308 | ok |
| PE | 5.601.017 | 40,24 | 31,03 | -9,21 | 31,031 | 49,21 | 63,45 | 14,25 | 63,452 | ok |
| PI | 2.146.394 | 40,75 | 24,09 | -16,66 | 24,088 | 48,63 | 70,99 | 22,36 | 70,989 | ok |
| PR | 6.585.243 | 45,34 | 59,91 | 14,57 | 59,912 | 43,20 | 31,20 | -12,00 | 31,200 | ok |
| RJ | 9.369.700 | 42,94 | 53,01 | 10,07 | 53,010 | 46,05 | 39,41 | -6,63 | 39,415 | ok |
| RN | 2.071.898 | 41,16 | 34,77 | -6,38 | 34,775 | 48,15 | 59,75 | 11,60 | 59,750 | ok |
| RO | 968.059 | 43,38 | 67,45 | 24,07 | 67,453 | 45,53 | 25,89 | -19,64 | 25,894 | ok |
| RR | 325.545 | 42,86 | 71,06 | 28,20 | 71,057 | 46,15 | 22,86 | -23,29 | 22,860 | ok |
| RS | 6.423.046 | 45,02 | 55,64 | 10,62 | 55,640 | 43,60 | 35,73 | -7,87 | 35,727 | ok |
| SC | 4.500.897 | 46,54 | 66,65 | 20,11 | 66,654 | 41,79 | 25,04 | -16,74 | 25,043 | ok |
| SE | 1.364.196 | 40,51 | 30,63 | -9,88 | 30,629 | 48,91 | 62,75 | 13,84 | 62,749 | ok |
| SP | 24.879.644 | 45,56 | 51,93 | 6,37 | 51,932 | 42,94 | 38,20 | -4,74 | 38,200 | ok |
| TO | 930.447 | 43,21 | 50,44 | 7,23 | 50,440 | 45,73 | 43,42 | -2,31 | 43,421 | ok |

Conferência por UF (média do esperado recentrado = urna da UF, tolerância 0,05 pp): 27 de 27 ok.
Média nacional do esperado recentrado: 47,0377 (Lula 45,1562), contra a urna dos locais no Brasil 47,0377 (diferença -0,0000 pp) e a urna nacional com exterior 47,0278 (diferença 0,0098 pp; tolerância 0,05 pp: ok). Vão médio ponderado por válidos nos locais: -0,0000 pp; nas seções: 0,0023 pp (o deslocamento é calculado sobre os locais e aplicado igual às seções).

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
| AL | ok | 1.071 | 4 | 0 |
| AM | arquivo por seção ausente | 0 | 1.619 | 0 |
| AP | ok | 368 | 2 | 0 |
| BA | ok | 9.179 | 19 | 0 |
| CE | ok | 6.692 | 11 | 0 |
| DF | ok | 614 | 8 | 0 |
| ES | ok | 1.749 | 16 | 0 |
| GO | ok | 2.466 | 10 | 0 |
| MA | ok | 5.749 | 30 | 0 |
| MG | ok | 10.059 | 14 | 0 |
| MS | ok | 1.019 | 2 | 0 |
| MT | ok | 1.496 | 5 | 0 |
| PA | ok | 5.775 | 9 | 0 |
| PB | ok | 1.827 | 10 | 0 |
| PE | ok | 3.366 | 23 | 0 |
| PI | ok | 3.355 | 13 | 0 |
| PR | ok | 4.789 | 3 | 0 |
| RJ | ok | 5.046 | 0 | 0 |
| RN | ok | 1.563 | 2 | 0 |
| RO | ok | 666 | 5 | 0 |
| RR | ok | 353 | 2 | 0 |
| RS | ok | 7.751 | 23 | 0 |
| SC | ok | 3.432 | 18 | 0 |
| SE | ok | 1.199 | 8 | 0 |
| SP | ok | 11.010 | 62 | 0 |
| TO | ok | 917 | 4 | 0 |
| ZZ | ok | 171 | 0 | 0 |

## Índice de conversa

Teto do potencial: 40 votos por 100 aptos. p99 observado do potencial: 35,09. Locais com índice 100 (saturados): 227 (0,24%).

Teto por componente, antes da soma: c_perfil 8 e c_reencontro 8 votos por 100 aptos. Locais em que o teto cortou: c_perfil 22.278, c_reencontro 185. O valor sem teto fica em `c_perfil_bruto` e `c_reencontro_bruto`.

| ponto da distribuição | índice (locais) | índice (seções com 30 aptos ou mais) | potencial (locais) | coluna `percentil` (locais do Brasil) |
|---|---:|---:|---:|---:|
| p1 | 29,0 | 31,0 | 11,54 | 0,0 |
| p5 | 36,0 | 37,0 | 14,58 | 4,6 |
| p10 | 40,0 | 40,0 | 15,96 | 9,2 |
| p25 | 46,0 | 47,0 | 18,29 | 25,0 |
| p50 | 53,0 | 55,0 | 21,38 | 50,0 |
| p75 | 63,0 | 66,0 | 25,09 | 75,0 |
| p90 | 73,0 | 77,0 | 29,02 | 89,8 |
| p95 | 78,0 | 82,0 | 31,33 | 94,4 |
| p99 | 88,0 | 92,0 | 35,09 | 98,1 |

A coluna `percentil` é a posição do potencial do local entre os locais do Brasil com boletim (0 a 100, arredondada para baixo; 100 = maior potencial do país); a da seção usa as seções com 30 aptos ou mais; `percentil_uf` repete a conta dentro da UF. O exterior só tem `percentil_uf`.

Seções com menos de 30 aptos (votos omitidos na camada zona/): 71.

Por região (médias ponderadas: índice e componentes por aptos, vão por válidos):

| região | locais | Flávio (% válidos) | índice médio | vão do perfil (pp) | c_perfil | c_ausentes | índice 100 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Centro-Oeste | 5.620 | 56,5 | 60,4 | -0,00 | 2,04 | 10,85 | 92 |
| Exterior | 171 | 43,5 | 91,4 | sem dado | sem dado | 31,35 | 49 |
| Nordeste | 34.121 | 30,9 | 50,5 | -0,00 | 2,57 | 9,20 | 6 |
| Norte | 10.380 | 49,2 | 50,0 | 0,00 | 2,50 | 9,72 | 4 |
| Sudeste | 27.956 | 51,4 | 61,6 | 0,00 | 2,40 | 11,35 | 48 |
| Sul | 16.016 | 60,1 | 55,6 | -0,00 | 2,32 | 10,23 | 28 |

## Arquétipos

| arquétipo | locais | % dos locais | % dos aptos | seções | secundário |
|---|---:|---:|---:|---:|---:|
| Fortaleza (`fortaleza`) | 18.920 | 20,1% | 21,1% | 110.381 | 0 |
| Muro (`muro`) | 27.649 | 29,3% | 15,0% | 83.137 | 0 |
| Pêndulo (`pendulo`) | 9.096 | 9,6% | 12,6% | 61.118 | 0 |
| Reencontro (`reencontro`) | 198 | 0,2% | 0,1% | 3.019 | 355 |
| Terreno fértil (`fertil`) | 22.892 | 24,3% | 35,8% | 158.851 | 17.551 |
| Dormindo (`dormindo`) | 1.136 | 1,2% | 1,1% | 8.874 | 3.872 |
| Abaixo do perfil (`abaixo_do_perfil`) | 3.523 | 3,7% | 2,8% | 15.552 | 24.888 |
| Na frente (`frente`) | 4.549 | 4,8% | 5,1% | 27.854 | 0 |
| Atrás (`atras`) | 6.301 | 6,7% | 6,4% | 30.401 | 0 |
| sem secundário | | | | | 47.598 |

Índice por arquétipo, locais com 300 aptos ou mais:

| arquétipo | locais | índice médio | % com índice 100 |
|---|---:|---:|---:|
| Fortaleza | 15.796 | 47,7 | 0,05% |
| Muro | 19.576 | 56,2 | 0,06% |
| Pêndulo | 8.112 | 61,2 | 0,28% |
| Reencontro | 99 | 76,4 | 13,13% |
| Terreno fértil | 20.993 | 61,6 | 0,22% |
| Dormindo | 918 | 65,7 | 0,44% |
| Abaixo do perfil | 2.818 | 61,4 | 0,00% |
| Na frente | 4.006 | 45,9 | 0,00% |
| Atrás | 5.690 | 42,3 | 0,00% |

## Conta do 2º turno

Transferência da terceira via: 30% sem escolha, 61% de quem escolhe para Flávio (coeficientes 0,427 e 0,273). Taxa de conversão declarada: 0,35.

Projeção somada (nacional do build): Flávio 60.080.145, Lula 56.420.605. Locais onde Flávio já passa: 44.609 de 94.264.

## PNAD

Preços de 2026-07 (fator IPCA 1,00811 sobre 2026-04); salário mínimo de 2026: R$ 1.621. Células substituídas por terem menos de 30 observações: 0.

## Tempos por UF (s)

AC 0,3, AL 0,7, AM 0,9, AP 0,2, BA 3,8, CE 3,3, DF 1,4, ES 1,8, GO 2,4, MA 16,9, MG 54,0, MS 6,8, MT 8,8, PA 18,5, PB 9,8, PE 21,9, PI 8,3, PR 26,5, RJ 37,3, RN 7,6, RO 4,3, RR 0,1, RS 26,5, SC 17,3, SE 4,9, SP 103,1, TO 3,8, ZZ 2,2
