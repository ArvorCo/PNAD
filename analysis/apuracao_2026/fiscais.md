# Onde colocar fiscal: prioridade de fiscalização por seção, 2º turno de 2026

Gerado em 2026-10-06T23:02:53Z por `scripts/apuracao-2026-fiscais.py`. Dados em `analysis/apuracao_2026/dados/fiscais.json` (contrato em `analysis/apuracao_2026/CONTRATO_FISCAIS.md`, versão 1.1).

> Atipicidade estatística não é irregularidade. A lista é de prioridade de fiscalização, não de acusação. O que resolve cada item é a ata da mesa, o log da urna e a presença do fiscal.

## Método

- Universo: as seções válidas do capítulo 12, as seções com boletim íntegro das três zonas que divergem do arquivo de zona do TSE e as seções principais ativas sem arquivo publicado. Zona, município e UF recalculados sobre esse universo.
- Doze critérios com limiar declarado; pontuação = soma de pesos; nível por cortes declarados. alta: pontuação 5 ou mais e nenhuma explicação comum documentada (aldeia, presídio, exterior, trânsito, seção minúscula); média: 3 ou mais, ou 5 ou mais com explicação comum; baixa: o resto. Seção de 90% que já votava assim em 2022 (enclave) fica em baixa. Com pesos iguais, cada critério vale 1: alta com 3 critérios ou mais, média com 2.
- Pesos: a 3; b 3; c 3; d 2; e 2; f 2; g 1; h_sem_arquivo 3; h_zona_congelada 1; i 1; j 2; k 1; l 2.
- Explicação comum documentada (tira a seção do nível alta): aldeia ou terra indígena (tipo de local inferido 'aldeia ou terra indígena' (ALDEIA, INDIGENA ou TERRA INDIG no nome, bairro ou endereço do local)); unidade prisional ou socioeducativa (tipo oficial do TSE 'Preso provisório' ou nome do local com PRESIDIO, PENITENCIARIA, CADEIA, SOCIOEDUCATIV e afins); seção no exterior (UF ZZ); voto em trânsito (tipo oficial do TSE 'Voto em trânsito' ou 20% ou mais dos aptos em trânsito); seção minúscula (menos de 50 votantes).

## Critérios

| id | nome | regra | peso | seções | alta | média | baixa | só este |
|---|---|---|---|---|---|---|---|---|
| a | 90% ou mais com excesso sobre a zona | Lula ou Flávio com 90% ou mais dos válidos, 100 votantes ou mais e 20 pontos ou mais acima do resto da zona (a zona sem a própria seção). Seção casada com 2022 em que o mesmo campo já tinha 90% ou mais (1º ou 2º turno) fica em nível baixa | 3 | 1.180 | 42 | 379 | 759 | 859 |
| b | zero voto num dos dois | Lula ou Flávio com zero voto e 150 votantes ou mais | 3 | 26 | 0 | 8 | 18 | 3 |
| c | comparecimento total | comparecimento igual ou maior que os aptos e 50 aptos ou mais | 3 | 10 | 0 | 8 | 2 | 9 |
| d | encerramento tardio com Lula acima da zona | último voto às 19:00 de Brasília ou depois e Lula 10 pontos ou mais acima do resto da zona; exterior fora | 2 | 1.634 | 33 | 222 | 1.379 | 1.290 |
| e | entre as 200 menos prováveis da mistura | as 200 seções de menor log-verossimilhança na mistura de cinco grupos do capítulo 12, refeita com a semente e a inicialização gravadas em secoes.json e conferida contra as 50 menos prováveis publicadas | 2 | 200 | 12 | 113 | 75 | 69 |
| f | urna ou arquivo fora do padrão com voto diferente da zona | arquivo recuperado ou de sistema de apuração (tipo de arquivo diferente de 1), urna de contingência ou reserva (tipo de urna diferente de 1) ou mais de uma carga, e Lula ou Flávio 10 pontos ou mais longe do resto da zona | 2 | 449 | 5 | 40 | 404 | 391 |
| g | boletim recebido de madrugada | recebimento (dr/hr do aux.json) às 00:00 de 05/10 ou depois; exterior fora | 1 | 340 | 3 | 11 | 326 | 319 |
| h | sem arquivo publicado ou em zona congelada | (1) seção principal ativa sem aux.json publicado (o TSE devolve 404; peso 3); (2) seção que faltava num arquivo de zona de presidente que ficou parado incompleto por 6 horas ou mais depois das 17h de Brasília: as k de recebimento mais recente até a geração da versão parada, k = seções totalizáveis menos totalizadas (peso 1) | 3 ou 1 | 89 | 3 | 23 | 63 | 83 |
| i | zona entre as 50 mais atípicas e seção longe da UF | seção numa das 50 zonas de maior escore em anomalias.json com Lula ou Flávio 10 pontos ou mais acima da própria UF | 1 | 1.566 | 14 | 45 | 1.507 | 1.482 |
| j | variação 2022-2026 fora da faixa da UF | seção casada com 2022 (mesmo número e mesmo local), 50 ou mais votos nominais nos dois anos; variação da margem (Flávio menos Lula em 2026 contra Bolsonaro menos Lula no 1º turno de 2022) a mais de 3 desvios-padrão da média das seções casadas da UF | 2 | 2.397 | 23 | 308 | 2.066 | 2.044 |
| k | brancos ou nulos muito acima da zona | brancos ou nulos (% do comparecimento) 3 desvios-padrão ou mais acima da média das outras seções da zona e 3 pontos ou mais acima dela; 50 votantes ou mais e ao menos 8 outras seções na zona | 1 | 5.730 | 20 | 419 | 5.291 | 5.242 |
| l | local com três ou mais seções sinalizadas | local de votação com 3 ou mais seções sinalizadas pelos critérios de seção (a, b, c, d, e, f, j, k); g, h e i ficam fora da contagem porque valem para o local ou a zona inteira por construção | 2 | 799 | 50 | 605 | 144 | 0 |

Explicação comum e o que o fiscal confere:

- **a**: explicação comum: aldeia, comunidade fechada ou enclave que já votava assim em 2022. O fiscal confere: identificação dos eleitores (biometria ou documento) e boletim impresso afixado contra o publicado.
- **b**: explicação comum: aldeia ou comunidade fechada que vota em bloco. O fiscal confere: boletim impresso afixado na porta contra o publicado e número de votantes na ata.
- **c**: explicação comum: seção de unidade prisional ou de trânsito, com cadastro pequeno e fechado. O fiscal confere: caderno de votação (quem assinou), habilitações por ano de nascimento no log da urna e ata.
- **d**: explicação comum: fila longa em seção grande e identificação biométrica lenta: no capítulo de encerramento, a seção que fechou às 19h ou depois tem, em média, +4,86 pontos de Lula sobre as demais da mesma zona (IC 95% de +4,45 a +5,29); o limiar de 10 pontos fica acima disso. O fiscal confere: senhas entregues às 17h, quantos votaram depois e habilitações por ano de nascimento no fim do dia (log da urna).
- **e**: explicação comum: seção pequena com abstenção, brancos ou nulos fora do comum (aldeia, zona rural, presídio). O fiscal confere: ata: número de votantes, brancos, nulos e ocorrências.
- **f**: explicação comum: urna trocada por defeito ou dados recuperados de mídia. O fiscal confere: ata: troca de urna ou recuperação de dados, hora, motivo, lacres e número da urna.
- **g**: explicação comum: área remota com transmissão por satélite, barco ou avião. O fiscal confere: hora de emissão do boletim e caminho da mídia até o ponto de transmissão.
- **h**: explicação comum: atraso de publicação do TSE: os votos estão no arquivo da UF. O fiscal confere: boletim impresso afixado e cópia pedida ao presidente da mesa (Lei 9.504, art. 68, § 1º).
- **i**: explicação comum: zona pequena, terceira via forte ou liderança local (ver a explicação da zona em anomalias.json). O fiscal confere: ata e boletim impresso, com a explicação da zona em mãos.
- **j**: explicação comum: eleitorado remanejado entre seções, liderança local ou candidatura estadual forte. O fiscal confere: ata e se o eleitorado da seção mudou (remanejamento).
- **k**: explicação comum: eleitor idoso ou com dificuldade na urna, orientação errada ou campanha de voto nulo local. O fiscal confere: ata: reclamação sobre a urna, o teclado ou a orientação ao eleitor.
- **l**: explicação comum: local grande numa área que vota em bloco. O fiscal confere: um fiscal no prédio pode cobrir várias seções do mesmo local (Lei 9.504, art. 65, § 1º).

## Resultado

| nível | seções | locais | municípios | aptos das seções | aptos dos locais |
|---|---|---|---|---|---|
| alta | 82 | 59 | 50 | 24.307 | 80.099 |
| média | 1.230 | 778 | 511 | 344.069 | 900.142 |
| baixa | 11.733 | 9.479 | 3.172 | 3.422.359 | 16.749.649 |

- Eleitorado das seções sinalizadas: 3.790.735 aptos (2,39% do universo); dos locais inteiros que as contêm: 17.500.058 (11,02%).
- Fiscais, um por local: alta 59; alta e média 817; todos 10.174.
- Fiscais, um por seção: alta 82; alta e média 1.312; todos 13.045. Base legal: Lei 9.504/1997, art. 65, § 1º (um fiscal pode cobrir mais de uma seção no mesmo local) e § 4º (até dois fiscais de cada partido por seção), como registrado em fechamento.json, fontes_legais.

### Os 10 municípios de maior pontuação somada

| # | município | seções | alta | média | locais | pontuação | Flávio × Lula (%) |
|---|---|---|---|---|---|---|---|
| 1 | SÃO PAULO (SP) | 937 | 2 | 47 | 325 | 1.161 | 42,1 × 46,6 |
| 2 | JOÃO PESSOA (PB) | 273 | 0 | 1 | 57 | 282 | 45,7 × 46,5 |
| 3 | FORTALEZA (CE) | 241 | 1 | 5 | 69 | 274 | 39,3 × 53,5 |
| 4 | RIO DE JANEIRO (RJ) | 181 | 0 | 9 | 155 | 264 | 47,9 × 43,9 |
| 5 | TABATINGA (AM) | 31 | 0 | 17 | 13 | 180 | 32,7 × 63,2 |
| 6 | SOBRAL (CE) | 141 | 3 | 8 | 63 | 176 | 33,7 × 59,7 |
| 7 | BELO HORIZONTE (MG) | 91 | 0 | 12 | 69 | 143 | 48,3 × 41,4 |
| 8 | BRASÍLIA (DF) | 75 | 0 | 10 | 61 | 130 | 51,3 × 38,1 |
| 9 | CAPANEMA (PA) | 107 | 0 | 2 | 44 | 122 | 39,4 × 54,8 |
| 10 | FEIRA DE SANTANA (BA) | 46 | 0 | 14 | 30 | 111 | 35,8 × 57,1 |

### Os 10 primeiros locais (nível do local, depois pontuação somada)

| # | local e endereço | seções sinalizadas | nível | pontuação | critérios |
|---|---|---|---|---|---|
| 1 | E. E. SANTO ANTONIO DO MATUPI (COMUNIDADE SANTO ANTONIO DO MATURI BR 230 TRANSAMAZONICA, ZONA RURAL), MANICORÉ (AM), zona 16 | 7 de 13 | alta | 36 | a 6, f 2, l 7 |
| 2 | EEFM CESAR ALMEIDA (COMUNIDADE MORAES ALMEIDA, ZONA RURAL), ITAITUBA (PA), zona 34 | 5 de 14 | alta | 25 | a 5, l 5 |
| 3 | ESCOLA MUNICIPAL LYCIA PEDRAL (RUA EDUARDO DALTRO S/N - ZONA URBANA, ALTO MARON), VITÓRIA DA CONQUISTA (BA), zona 41 | 9 de 15 | alta | 24 | d 4, h 8, l 4 |
| 4 | UNIDADE ESCOLAR PRESIDENTE VARGAS (PRACA DA IGREJA S/N, CENTRO), BAIXA GRANDE DO RIBEIRO (PI), zona 44 | 8 de 8 | alta | 24 | i 8, j 4, l 4 |
| 5 | ESCOLA MUNICIPAL AURELIANO FRANCISCO NETO (POVOADO DE EXTREMA, S/N, ZONA RURAL), AFRÂNIO (PE), zona 107 | 5 de 6 | alta | 21 | j 5, k 1, l 5 |
| 6 | ESCOLA MUNICIPAL THEOTÔNIO COSTA (POVOADO COCO, POVOADO CÔCO ZONA RURAL), PINHEIRO (MA), zona 37 | 4 de 4 | alta | 21 | a 4, k 1, l 4 |
| 7 | EM IRMA SIMAS (RUA JOSE SOBREIRA, 608, SAPIRANGA-COITÉ), FORTALEZA (CE), zona 112 | 5 de 10 | alta | 20 | d 4, k 2, l 5 |
| 8 | GINASIO POLIESPORTIVO MUNICIPAL (RUA PASTOR ALBERT ERBERT, CIDADE ALTA, BAIRRO CENTRO), CHARRUA (RS), zona 100 | 4 de 4 | alta | 20 | a 4, l 4 |
| 9 | COLEGIO ESTADUAL FRANCISCO NEVES FILHO (R TENENTE CEL. CARLOS SOUZA, 20  CENTRO, CENTRO), SÃO JOÃO DO TRIUNFO (PR), zona 52 | 8 de 11 | alta | 19 | i 7, j 3, l 3 |
| 10 | ETI MARIA DE LOURDES DE VASCONCELOS (RUA MONSENHOR LINHARES, S/N, ARACATIAÇU), SOBRAL (CE), zona 121 | 4 de 4 | alta | 19 | d 4, i 3, l 4 |

### Arquivos de zona parados incompletos

| UF | município (TSE) | zona | versão parada (Brasília) | horas | faltavam | identificadas | conferem |
|---|---|---|---|---|---|---|---|
| BA | 33693 | 177 | 2026-10-04 21:00:57 | 15,9 | 4 | 4 | sim |
| BA | 34673 | 132 | 2026-10-04 21:00:56 | 15,9 | 1 | 1 | sim |
| BA | 36013 | 119 | 2026-10-04 21:00:57 | 15,9 | 1 | 1 | sim |
| BA | 39659 | 41 | 2026-10-04 21:00:57 | 15,9 | 14 | 14 | sim |
| MG | 40622 | 187 | 2026-10-04 20:58:25 | 14,8 | 4 | 4 | sim |
| MG | 41556 | 72 | 2026-10-04 20:54:31 | 14,9 | 3 | 3 | sim |
| MG | 41696 | 120 | 2026-10-04 21:01:43 | 14,8 | 9 | 9 | sim |
| MG | 42005 | 266 | 2026-10-04 21:01:08 | 14,8 | 7 | 7 | sim |
| MG | 46078 | 160 | 2026-10-04 21:01:09 | 14,8 | 1 | 1 | sim |
| MG | 51977 | 46 | 2026-10-04 21:01:43 | 14,8 | 1 | 1 | sim |
| MG | 53171 | 135 | 2026-10-04 21:01:08 | 14,8 | 5 | 5 | sim |
| SP | 67130 | 287 | 2026-10-04 20:58:51 | 14,8 | 19 | 19 | sim |

## Sensibilidade a pesos iguais

pesos iguais: cada critério vale 1; alta com 3 critérios ou mais, média com 2, mesma regra de explicação comum e de enclave.

Com pesos iguais, 432 seções mudam de nível (3,3%); a correlação de postos entre as duas pontuações é 0,548; dos 100 locais de maior pontuação, 61 continuam entre os 100 primeiros, e dos 100 municípios, 81.

| nível com pesos | nível com pesos iguais | seções |
|---|---|---|
| alta | alta | 41 |
| alta | média | 41 |
| alta | baixa | 0 |
| média | alta | 4 |
| média | média | 854 |
| média | baixa | 372 |
| baixa | alta | 0 |
| baixa | média | 15 |
| baixa | baixa | 11.718 |

## Risco e contexto do território

soma de pontos: mapeamento público de crime organizado no município 2; homicídios no 5º quintil nacional 2 (4º quintil 1); favela ou comunidade urbana 1; terra indígena ou quilombo a até 2 km 1; faixa de fronteira 1; garimpo 1; unidade prisional ou socioeducativa 1; sede municipal a 50 km ou mais por estrada (ou em linha reta, sem rota) 1. Alto com 4 pontos ou mais, médio com 2 ou 3, baixo com 0 ou 1; nulo quando nenhuma camada cobre o local. Terra indígena e quilombo valem por polígono oficial (FUNAI), tipo do setor censitário ou nome do local; o proxy por ponto de localidade do IBGE vale só a até 0,5 km e em setor rural.

| camada | fonte | status | seções cobertas | motivo |
|---|---|---|---|---|
| rural_urbano | Malha de setores censitários do Censo 2022 (GeoPackage, Brasil) | ok | 12966 |  |
| rural_urbano | Dicionário de dados da malha de setores e agregados do Censo 2022 | ok | 12966 |  |
| terra_indigena | Terras indígenas, poligonais (WFS Funai:tis_poligonais, GeoJSON) | ok | 12926 |  |
| terra_indigena | Localidades indígenas do Censo 2022 (LI, pontos, CSV) | proxy | 12926 |  |
| terra_indigena | Dicionário de dados das localidades indígenas 2022 | ok | 12926 |  |
| quilombo | Áreas de quilombolas (acervo fundiário e certificação do INCRA) | falhou |  | a exportação de shapefile da certificação do INCRA (https://certificacao.incra.gov.br/csv_shp/export_shp.py) devolveu HTTP 200 com a tela de login gov.br (sso.acesso.gov.br); o índice csv_shp devolveu HTTP 403; o serviço OGC do acervo fundiário (acervofundiario.incra.gov.br/i3geo) não listou camada de quilombolas; sem polígono oficial de território quilombola, a camada usa o proxy declarado do IBGE |
| quilombo | Localidades quilombolas do Censo 2022 (pontos, CSV) | proxy | 12912 |  |
| quilombo | Dicionário das localidades quilombolas 2022 | ok | 12912 |  |
| fronteira | Municípios da faixa de fronteira e cidades-gêmeas 2024 (XLS) | ok | 13024 |  |
| garimpo | SIGMINE, processos minerários ativos na fase LAVRA GARIMPEIRA (camada 0, GeoJSON) | ok | 12912 |  |
| garimpo | SIGMINE, reservas garimpeiras (camada 4, GeoJSON) | ok | 12912 |  |
| homicidios_municipio | Atlas da Violência, série 20, taxa de homicídios registrados por município (abrangência 4) | ok | 11805 |  |
| homicidios_municipio | Atlas da Violência, série 328, homicídios registrados por município (abrangência 4) | ok | 11805 |  |
| homicidios_municipio | Atlas da Violência, metadados da série 20 | ok | 11805 |  |
| sede_municipal | Localidades do Brasil 2022 (GeoPackage compactado) | ok |  |  |
| crime_organizado | Mapa histórico dos grupos armados no Rio de Janeiro (GENI/UFF e Fogo Cruzado) | falhou |  | a página do GENI/UFF devolveu HTTP 200 e traz relatório em PDF e link para mapa interativo (fogocruzado.org.br, HTTP 403); arquivos de dados encontrados na página: 0; sem base de dados com licença declarada, a fonte não é usada |
| crime_organizado | Cartografias da Violência na Amazônia, 4ª edição, quadros 3.2 a 3.10 (presença por município) | ok | 13024 |  |
| todas | Cadastro de locais de votação e seções do TSE, 2026 (tabela secao) | ok |  |  |
| todas | Tabela municipio do banco da apuração (código TSE para IBGE) | ok |  | banco ainda gravado por outro processo; SHA-256 não é estável |
| crime_organizado | Itens de imprensa arquivados sobre segurança na eleição | ok | 13024 |  |
| acesso | Lista de aeródromos públicos | ok | 1534 |  |
| acesso | OSRM, serviço table, perfil carro | ok | 1534 |  |

## Exportáveis

- `docs/assets/fiscais_2026.csv`: uma linha por seção sinalizada; 13.045 linhas; 10,88 MB; SHA-256 `90691aa66a338d35951c3527476cd862689eb61d72e90c9a3bfa827349af75be`.
- `docs/assets/fiscais_2026_por_local.csv`: uma linha por local de votação com seção sinalizada; 10.174 linhas; 3,72 MB; SHA-256 `35dbb9abdc63c5679e7f4762974bc88a3c9f7b372db1650dfc5feb2d983a4dca`.
- `docs/assets/fiscais_2026.xlsx`: abas Leia-me, Seções, Locais, Municípios, UFs, Critérios e Riscos; 13.045 linhas; 9,11 MB; SHA-256 `dcac6856ef3c78c6cabb6b54163c264fc77203f8fdab9971af94447ec63344d3`.

## Verificado

- Universo: 499.207 seções, das quais 497.890 são as válidas do capítulo 12, 1.297 têm boletim íntegro nas três zonas que divergem do arquivo de zona do TSE e 20 não têm arquivo publicado.
- 13.045 seções disparam ao menos um critério (2,6% do universo), em 10.174 locais de votação: 82 em nível alta, 1.230 em média e 11.733 em baixa. Atipicidade estatística não é irregularidade.
- Seções por critério: a (90% ou mais com excesso sobre a zona) 1.180; b (zero voto num dos dois) 26; c (comparecimento total) 10; d (encerramento tardio com Lula acima da zona) 1.634; e (entre as 200 menos prováveis da mistura) 200; f (urna ou arquivo fora do padrão com voto diferente da zona) 449; g (boletim recebido de madrugada) 340; h (sem arquivo publicado ou em zona congelada) 89; i (zona entre as 50 mais atípicas e seção longe da UF) 1.566; j (variação 2022-2026 fora da faixa da UF) 2.397; k (brancos ou nulos muito acima da zona) 5.730; l (local com três ou mais seções sinalizadas) 799.
- A mistura gaussiana do capítulo 12 foi refeita com a semente gravada: 50 das 50 seções menos prováveis publicadas saem iguais, com diferença máxima de 0,000 na log-verossimilhança.
- 12 arquivos de zona de presidente ficaram parados incompletos por 14,8 a 15,9 horas depois da última versão gerada perto das 21h de Brasília, com 69 seções faltando. Em 12 das 12 zonas, as seções que faltavam são exatamente as recebidas no último minuto antes da versão parada, separadas das anteriores por 30 segundos ou mais: o lote chegou e não entrou na totalização da zona. Os votos estão no arquivo da UF.
- 20 seções principais ativas não têm aux.json publicado (o TSE devolve 404): BETIM (MG), zona 319: 3; CARAPICUÍBA (SP), zona 388: 12; UBERLÂNDIA (MG), zona 279: 5. Exigem explicação documental: o boletim impresso afixado e a cópia pedida ao presidente da mesa resolvem.

## Inferido

- O critério a (90% ou mais com excesso de 20 pontos sobre a zona) dispara em 1.180 seções; 644 delas já votavam assim em 2022 e ficam em nível baixa como enclaves.
- O critério que mais sinaliza é o de brancos ou nulos muito acima da zona (5.730 seções, 5.242 só por ele); com peso 1, quase todas ficam em nível baixa (5.291).
- Com pesos iguais, 432 seções mudam de nível (3,3%); a correlação de postos entre as duas pontuações é 0,548; dos 100 locais de maior pontuação, 61 continuam entre os 100 primeiros, e dos 100 municípios, 81.

## Juízo editorial

- Um fiscal por local cobre as seções de nível alta em 59 locais e as de alta e média em 817; um por seção pede 1.312 fiscais para alta e média e 13.045 para a lista inteira. A lei permite que um fiscal cubra várias seções do mesmo local (Lei 9.504, art. 65, § 1º).
- Fiscal evita erro e intimidação dos dois lados: a mesma presença que protege o voto de Flávio onde ele é competitivo vigia a seção em que Lula aparece muito acima das vizinhas. Os três rankings usam as mesmas seções sinalizadas; mudam só o peso e o recorte. Nenhum deles é acusação.
- Pela ordem de prioridade (seções de nível alta, depois média, depois pontuação somada), os cinco municípios que pedem mais fiscal são ITAITUBA (PA), 23 seções; PINHEIRO (MA), 16 seções; SÃO JOÃO DO TRIUNFO (PR), 34 seções; BAIXA GRANDE DO RIBEIRO (PI), 36 seções; MANICORÉ (AM), 21 seções. A lista é de prioridade de fiscalização, não de acusação.

## Hipótese

- Seção quase unânime, com zero voto num dos dois ou com comparecimento total, sem explicação comum, pode vir de liderança local, de erro de mesário, de eleitor levado em bloco ou de irregularidade. O boletim não separa essas hipóteses: o que resolve cada item é a ata da mesa, o log da urna e a presença do fiscal.
- Seção que encerrou depois das 19h com Lula muito acima da zona pode ser fila longa em área pobre (o efeito típico dentro da zona está no capítulo de encerramento) ou pode pedir conferência das habilitações por ano de nascimento no fim do dia; só o log da urna separa as duas.

## Achado contrário

- Das 11.733 seções de nível baixa, 487 são aldeias ou unidades prisionais pelo cadastro: a explicação comum documentada desarma boa parte do que parece bizarro.
- 724 das 13.045 seções sinalizadas têm explicação comum documentada (aldeia, presídio, exterior, trânsito ou seção minúscula) e por regra nunca chegam a nível alta.
- Pela pontuação bruta, 9 dos 10 locais mais pontuados não chegam a nível alta e 8 ficam em aldeia ou terra indígena: são lugares que votam em bloco e somam muitas seções no mesmo prédio. Por isso a lista de prioridade ordena primeiro pelo nível, que separa a explicação comum, e só depois pela pontuação.
- A atipicidade não tem lado só: 78 das 1.180 seções do critério a são de Flávio com 90% ou mais, e o fiscal que vigia uma seção protege os dois votos.

## Limites

- Atipicidade estatística não é irregularidade: cada critério aponta seção que pede explicação, não seção com irregularidade. A lista é de prioridade de fiscalização, não de acusação.
- O boletim de urna mostra quanto se votou, não por quê. O que separa liderança local, erro de mesário, fila e irregularidade é a ata da mesa, o log da urna e a presença do fiscal no dia.
- Pesos e cortes de nível são juízo editorial declarado; a sensibilidade a pesos iguais fica publicada ao lado.
- Tipo de local (aldeia, presídio, zona rural, hospital) é inferência por palavra-chave no cadastro do TSE, não verificação no terreno.
- Excesso sobre a zona compara a seção com o resto da própria zona; zona com uma seção só não tem régua e fica fora dos critérios que dependem dela.
- O casamento com 2022 exige mesmo número de seção e mesmo nome de local; seção renumerada ou mudada de prédio fica sem comparação (critérios a, enclave, e j).
- A mistura gaussiana cobre só as seções válidas do capítulo 12; as três zonas divergentes (Betim 319, Uberlândia 279, Carapicuíba 388) entram nos demais critérios.
- As 20 seções sem aux.json publicado não têm voto conhecido: entram só pelo critério h.
- O 2º turno tem outra cédula e outro comparecimento: a lista prioriza onde houve atipicidade no 1º turno, não prevê o que vai acontecer no 2º.
- A camada de risco do território é contexto público com data, não avaliação de segurança: o nível de risco fiscal é regra declarada e deve ser validado com a PM e o TRE local antes de mandar alguém ao local.
- Crime organizado só aparece onde há mapeamento público documentado; ausência de mapeamento não é ausência de risco.

## Fontes

- `apuracao/data/secoes_2026.sqlite`: boletins de urna e aux.json por seção, 1º turno de 2026 (TSE); 8.550.633.472 bytes; SHA-256 `b5e927bebb760c42b2ed3b43bc47ec4efb1565eb46ae57c8c547404d4ffccfa7`.
- `data/outputs/locais_votacao_2026.sqlite`: cadastro de locais de votação 2026 do TSE, por seção; 131.772.416 bytes; SHA-256 `57d96007cfb84bf4c27ff8e0c5dda488aa533b8be13a12267b230857d91c5624`.
- `apuracao/data/apuracao.sqlite`: versões dos arquivos de zona do TSE e lista de candidaturas; 12.940.087.296 bytes; banco ainda gravado pelo coletor: vale o instante (tamanho e data).
- `data/raw/tse_resultados/votacao_secao_2022/votacao_secao_2022_BR.zip`: votos por candidato e seção, 2022 (TSE); 271.292.455 bytes; SHA-256 `9353993de5cf03778aef44e01d4925e7ee105f5262491d344a2f0dbc956b0139`.
- `data/raw/tse_resultados/detalhe_votacao_secao_2022.zip`: totais e local de votação por seção, 2022 (TSE); 243.822.213 bytes; SHA-256 `ad22c50b9e6d9dfb096a2170680a190f1734895ba89d8977b95fd63ca02c03da`.
- `analysis/apuracao_2026/dados/secoes.json`: capítulo 12: mistura gaussiana e seções atípicas; 763.205 bytes; SHA-256 `ff0a44102f5bf5d26f8f5826919648670080b5f64c77edd05d9019ad4f683678`.
- `analysis/apuracao_2026/dados/anomalias.json`: capítulo 11: as 50 zonas mais atípicas; 1.244.570 bytes; SHA-256 `d8b15a888ee89f0cf7349f9de410e00a77b2d929ef7fa06dff3ef899fcef1e0a`.
- `analysis/apuracao_2026/dados/fechamento.json`: encerramento por seção e fontes legais; 643.143 bytes; SHA-256 `f1bab6c7b967a18f4b293195a05117f2c3697f63c6f8186dae289b017b29b6a9`.
- `analysis/apuracao_2026/dados/contexto_seguranca.json`: matérias de imprensa sobre segurança e logística no dia; 134.561 bytes; SHA-256 `b7d60d47b5323d0a9f2ee8cc76f8d698eb03843a57abe8d4f6f8d62c47431e2f`.
- Código Eleitoral (Lei nº 4.737/1965), art. 132: perante as mesas receptoras, candidatos, delegados e fiscais dos partidos podem fiscalizar a votação, formular protestos e fazer impugnações, inclusive sobre a identidade do eleitor. texto do artigo em resultado de busca (modeloinicial.com.br).
- Lei nº 9.504/1997, art. 65, caput e §§ 1º a 4º: fiscal maior de 18 anos e fora da mesa; um fiscal pode fiscalizar mais de uma seção no mesmo local de votação (§ 1º); credenciais expedidas pelos partidos ou coligações (§ 2º); no máximo 2 fiscais de cada partido ou coligação por seção (§ 4º). texto do artigo em reprodução da lei (modeloinicial.com.br).
- Lei nº 9.504/1997, arts. 66 e 68, § 1º: partidos e coligações podem fiscalizar todas as fases da votação e da apuração (art. 66); o presidente da mesa entrega cópia do boletim de urna ao partido que a pedir até uma hora depois da expedição (art. 68, § 1º). texto em reprodução da lei (pdba.georgetown.edu).
- Lei nº 9.504/1997, art. 39, § 5º, II, e art. 41-A: arregimentação de eleitor e propaganda de boca de urna no dia da eleição são crime (art. 39, § 5º, II); captação ilícita de sufrágio, a compra de voto, sujeita a multa e cassação do registro ou do diploma (art. 41-A). resultado de busca com o texto dos dispositivos.
