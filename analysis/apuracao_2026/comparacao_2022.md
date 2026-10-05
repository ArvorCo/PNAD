# Apuração de 2026 contra 2022: os doze achados

Gerado por `scripts/apuracao-2026-comparacao.py` em 2026-10-05T07:19:22Z, com o boletim final de 2026-10-05T06:29:53.765Z. Dados completos em `analysis/apuracao_2026/dados/comparacao_2022.json`. Nenhum número deste texto foi digitado: todos saem do JSON.

## Achados

### 1. A margem virou 7,1 pontos sobre o 1º turno de 2022

Lula terminou o 1º turno de 2022 com 5,23 pontos de vantagem sobre Bolsonaro nos válidos. Em 2026 Flávio terminou o 1º turno 1,87 ponto à frente de Lula: a margem andou 7,10 pontos para a direita. Flávio teve +5.032.158 votos sobre Bolsonaro no 1º turno de 2022; Lula teve −3.379.966 sobre ele mesmo. Contra o 2º turno de 2022 (Lula 1,80 ponto à frente), a virada é de 3,67 pontos.

- Natureza: verificado (aritmética sobre os arquivos do TSE)
- Fonte: analysis/apuracao_2026/dados/comparacao_2022.json → presidente.saldo_nacional; api_2022 e presidente.json

### 2. Os dois finalistas de 2026 somam menos votos que os de 2022 no 2º turno

Flávio tem 2.101.851 votos a menos que Bolsonaro no 2º turno de 2022 (47,03% contra 49,10% dos válidos). Lula tem 6.466.461 a menos que ele próprio no 2º turno de 2022 (45,16% contra 50,90%). Somados, os dois finalistas estão 8.568.312 votos abaixo do 2º turno anterior, e as candidaturas de terceira via têm 9.316.747. O resultado do dia 25 depende de onde esse voto vai, e Lula está mais longe da própria marca que Flávio.

- Natureza: verificado; a leitura do 2º turno é inferência (comparar 1º com 2º turno mede distância, não prevê transferência)
- Fonte: analysis/apuracao_2026/dados/comparacao_2022.json → presidente.agregados.Brasil

### 3. No Nordeste, Flávio já passou o 2º turno de Bolsonaro

No Nordeste Flávio fez 10.398.973 votos no 1º turno, +436.026 sobre os 9.962.947 de Bolsonaro no 2º turno de 2022 (30,85% contra 30,66% dos válidos) e +1.611.579 sobre o 1º turno. No Norte, +227.096 sobre o 2º turno. No Centro-Sul, −2.763.609. A fatia de Flávio passa a de Bolsonaro no 2º turno em 6 UFs, 4 delas no Nordeste (MA, CE, PI e BA), em pontos: MA +2,03, TO +1,80, CE +1,24, PI +0,95, BA +0,66 e MT +0,07.

- Natureza: verificado (soma das UFs; votos a mais no agregado não dizem que são os mesmos eleitores)
- Fonte: analysis/apuracao_2026/dados/comparacao_2022.json → presidente.agregados e presidente.flavio_acima_bolsonaro_2t

### 4. O que falta para repetir o 2º turno de 2022 está no Centro-Sul

Flávio fica abaixo da fatia de Bolsonaro no 2º turno de 2022 em 21 UFs. As maiores distâncias em pontos: DF −7,50, AC −5,74, AP −5,70, GO −5,11 e RR −5,02. Em votos brutos: SP −1.294.564, RJ −437.050, MG −363.762 e PR −213.998. Contra o 1º turno de 2022, a fatia de Flávio é maior em 26 das 27 UFs; a exceção: DF.

- Natureza: verificado; dizer que essa diferença é a reserva do 2º turno é inferência (teto endereçável, não transferência certa)
- Fonte: analysis/apuracao_2026/dados/comparacao_2022.json → presidente.flavio_abaixo_bolsonaro_2t

### 5. A perda de Lula sobre 2022 é quase toda do Centro-Sul

Contra o 1º turno de 2022, Lula perdeu 3.379.966 votos no país. O Centro-Sul responde por 92,8% dessa perda (−3.135.837) e o Nordeste por 7,6% (−258.555). O ganho de Flávio sobre Bolsonaro no 1º turno se divide em 55,4% no Centro-Sul, 32,0% no Nordeste e 12,2% no Norte. No Nordeste, Lula perdeu 1,2% do que tinha no 1º turno de 2022, e Flávio teve +1.611.579 votos sobre Bolsonaro.

- Natureza: verificado
- Fonte: analysis/apuracao_2026/dados/comparacao_2022.json → presidente.contribuicao_regional_vs_1t

### 6. Comparecimento estável no país, maior no Norte e Nordeste, menor no Centro-Sul

O comparecimento foi de 78,92% contra 79,05% no 1º turno de 2022 (−0,14 ponto), com 1.593.463 votantes a mais e um eleitorado 2.291.491 maior. Nordeste +1,14 ponto, Norte +1,51, Centro-Sul −0,78. Brancos 1,84% (+0,25), nulos 2,93% (+0,11). A terceira via caiu de 8,37% para 7,81% dos válidos (−581.123 votos).

- Natureza: verificado
- Fonte: analysis/apuracao_2026/dados/comparacao_2022.json → presidente.agregados (comparecimento e abstenção sobre o eleitorado; brancos e nulos sobre o comparecimento)

### 7. Câmara: a direita ganhou 29 cadeiras e o bloco à direita ainda não chega a 308

Eleitos para a Câmara por campo, 2022 contra 2026: direita 144 e 173 (+29), centro-direita 128 e 119, centro 91 e 84, centro-esquerda 25 e 13, esquerda 125 e 124. O bloco de direita e centro-direita foi de 272 para 292 (+20), abaixo das 308 de emenda constitucional; esquerda e centro-esquerda, de 150 para 137. A esquerda em sentido estrito quase não se moveu; quem encolheu foi a centro-esquerda. Contando como direita as siglas extintas que a regra leva à centro-direita (PSC 6, PATRIOTA 4 e PTB 1), o ganho da direita cai para +18, e o bloco não muda. Pelo menos 66 cadeiras trocaram de bloco dentro das UFs.

- Natureza: verificado sob classificação editorial (contagem exata; campo pela tabela da casa); 2026 provisório em AM, MG e SP
- Fonte: analysis/apuracao_2026/dados/comparacao_2022.json → camara.por_campo_2022, camara.por_campo_2026, camara.trocas_de_bloco

### 8. O PL foi de 100 para 121 deputados; União e PDT perderam 23 juntos

PL: 100 para 121 cadeiras e de 16,62% para 22,72% dos votos de partido (+6,10 pontos). União: 58 para 46. PDT: 17 para 6. PP: 47 para 41. MDB: 42 para 36. Podemos, somado ao PSC que incorporou: 18 para 27. Novo: 3 para 10.

- Natureza: verificado; as somas de 2022 seguem a tabela de sucessores (PSC no Podemos, PTB e Patriota no PRD, PROS no Solidariedade)
- Fonte: analysis/apuracao_2026/dados/comparacao_2022.json → camara.partidos

### 9. Cadeiras contra votos: a sobra de cadeiras da direita caiu de +2,94 para +0,28 ponto

A direita foi de 25,13% para 33,44% dos votos de partido na Câmara e de 28,07% para 33,72% das cadeiras. A fatia de cadeiras menos a de votos da direita era de +2,94 pontos em 2022 e de +0,28 ponto em 2026. O prêmio de 2026 ficou com a centro-direita (+3,33); a esquerda fica 2,15 pontos abaixo do próprio voto. Votos por cadeira em 2026: esquerda 241.310, direita 219.746, centro-direita 189.821. Índice de Gallagher por partido: 3,55 em 2022 e 2,94 em 2026.

- Natureza: verificado sob classificação editorial; votos somados no país contra cadeiras distribuídas por UF; 2022 sem a legenda do MA (ausente do pacote do TSE)
- Fonte: analysis/apuracao_2026/dados/comparacao_2022.json → camara.proporcionalidade

### 10. Senado: nas 54 vagas renovadas, o bloco à direita foi de 21 para 33

Na urna de 2018, as 54 vagas renovadas agora deram 21 cadeiras ao bloco de direita e centro-direita, 2 delas de direita (5 se o PSL de 2018 contar como direita); em 2026 são 33 e 24. Esquerda e centro-esquerda caíram de 21 para 12. Somando os 27 eleitos de 2022, o Senado eleito de 2023 tinha 40 cadeiras de direita e centro-direita e o de 2027 terá 52: acima de 49 (três quintos), abaixo de 54 (dois terços). Direita 13 para 35 (16 para 35 com o PSL de 2018 como direita, e o bloco não muda); PL 9 para 27. No teto da direita de 2018 (toda sigla extinta que a regra leva à centro-direita contada como direita), a classe de 2018 teria 15 senadores de direita e o Senado de 2023, 26. Foram reeleitos 13 dos senadores eleitos em 2018.

- Natureza: verificado sob classificação editorial; eleitos da urna, não titulares (MT pela suplementar de 2020); a composição de 2023 é a da urna, não a da posse
- Fonte: analysis/apuracao_2026/dados/comparacao_2022.json → senado.classe_2018_composicao, senado.senado_2023, senado.senado_2027

### 11. Governadores: 10 dos 20 eleitos no 1º turno são de outro bloco

Dos 20 governadores eleitos no 1º turno de 2026, 10 são de bloco diferente do vencedor de 2022 (AL, AP, GO, MA, MS, PA, PB, PE, PR e RS); em MS e PE é o mesmo governador, que trocou de partido. Esquerda e centro-esquerda perderam 6 desses estados; direita e centro-direita ganharam 6 e perderam 1. Foram reeleitos 8 governadores (BA, CE, MS, PE, PI, SC, SE e SP), e 6 estados mantiveram o partido. Em 2022 o placar final foi 11 estados para esquerda e centro-esquerda, 5 para o centro e 11 para direita e centro-direita. Das 7 disputas de 2º turno de 2026, os dois finalistas são do mesmo bloco em AC (direita e centro-direita). Em DF e ES, nenhum finalista é do bloco do governador eleito em 2022: a troca de bloco já é certa.

- Natureza: verificado sob classificação editorial; reeleição pelo nome completo igual
- Fonte: analysis/apuracao_2026/dados/comparacao_2022.json → governadores

### 12. Nas 11 assembleias comparadas, a direita somou 57 cadeiras

Nas 11 casas comparadas (613 vagas), a direita foi de 129 para 186 e a centro-direita de 150 para 110; o bloco de direita e centro-direita, de 279 para 296. Esquerda e centro-esquerda caíram de 234 para 203, e toda a queda veio da centro-esquerda (55 para 18); a esquerda foi de 179 para 185. No teto da direita de 2022 (siglas extintas levadas à centro-direita contadas como direita: PATRIOTA 8, PSC 8, PMN 6 e PTB 3), o ganho da direita é de +32.

- Natureza: verificado sob classificação editorial; 2026 provisório em SP, MG, BA e PR
- Fonte: analysis/apuracao_2026/dados/comparacao_2022.json → assembleias.onze_casas

## Outros números

- Renovação da Câmara: 286 dos 513 eleitos em 2026 também foram eleitos em 2022 (55,8%), pelo nome completo igual na mesma UF (inferido: casamento de nomes).
- Senadores eleitos em 2018 reeleitos em 2026: MARCIO BITTAR (AC), EDUARDO BRAGA (AM), PLINIO VALÉRIO (AM), LUCAS BARRETO (AP), JAQUES WAGNER (BA), CID GOMES (CE), VENEZIANO (PB), HUMBERTO COSTA (PE), MARCELO CASTRO (PI), STYVENSON VALENTIM (RN), ROGERIO CARVALHO (SE), DELEGADO ALESSANDRO (SE) e EDUARDO GOMES (TO).
- Votos de partido na Câmara: 109.172.518 em 2022 (sem a legenda do MA) e 113.678.019 em 2026.
- O pacote de 2022 do TSE traz a eleição suplementar para governador de RR de 21/06/2026; nenhuma das 3 candidaturas aparece como eleita no arquivo. A comparação usa a eleição ordinária de 2022.

## Pressupostos e lacunas

- Eleito é o que o TSE grava em DS_SIT_TOT_TURNO (ELEITO, ELEITO POR QP, ELEITO POR MÉDIA) no pacote corrente, que incorpora retotalizações posteriores à eleição; a bancada pode diferir da diplomada em dezembro de 2022.
- Eleitos da urna, não titulares atuais: suplência, licença, morte e troca de partido depois da eleição ficam fora, salvo a exceção já declarada pela casa para Cleitinho (MG, Senado 2022).
- Campo de 2018 e 2022 pela tabela da casa (apuracao/public/campos.json); sigla extinta herda o campo do sucessor de 2026 (tabela `partidos`).
- Em 2018 o PSL vai ao União Brasil (centro-direita) pela regra de sucessão; a contagem com o PSL de 2018 como direita sai em `sensibilidade_psl_2018_direita`.
- Teto da direita de 2018 e 2022 (sensibilidade, não regra): toda sigla extinta que a sucessão leva à centro-direita conta como direita; dá o piso do crescimento da direita e não muda o bloco de direita e centro-direita.
- Câmara de 2026: UFs marcadas em `ufs_provisorias_2026` usam a alocação pelo quociente do telão, que reproduziu nome a nome o TSE nas UFs fechadas.
- Votos de partido na Câmara: nominais válidos mais legenda; no MA de 2022 só nominais, porque o pacote de partidos do TSE não traz o cargo.
- Governador de RR: a comparação usa a eleição ordinária de 2022; a suplementar de 21/06/2026 que o pacote traz fica registrada à parte.

## Tabela de partidos assumida

A tabela da casa (`apuracao/public/campos.json`) vence quando lista a sigla antiga (`direto`); senão vale o campo do sucessor de 2026 (`sucessor`). A coluna de evidência diz se o número do partido antigo aparece com a sigla sucessora no banco de 2026 ou se a sucessão é fato público de registro partidário sem documento arquivado aqui.

| Sigla antiga | Anos | Nº | Sigla de 2026 | Tipo | Campo usado | Evidência |
|---|---|---|---|---|---|---|
| DEM | 2018 | 25 | UNIÃO | fusão | centro-direita (sucessor) | fato público, sem documento no repositório |
| PATRI | 2018 | 51 | PRD | fusão | centro-direita (sucessor) | fato público, sem documento no repositório |
| PATRIOTA | 2018, 2022 | 51 | PRD | fusão | centro-direita (sucessor) | fato público, sem documento no repositório |
| PC DO B | 2018, 2022 | 65 | PCDOB | grafia | esquerda (direto) | número confirmado no banco de 2026 |
| PHS | 2018 | 31 | PODE | incorporação | centro-direita (sucessor) | fato público, sem documento no repositório |
| PMB | 2018, 2022 | 35 | DEMOCRATA | renomeação inferida | centro-direita (direto) | número confirmado no banco de 2026 |
| PMN | 2018, 2022 | 33 | MOBILIZA | renomeação | centro-direita (sucessor) | número confirmado no banco de 2026 |
| PPL | 2018 | 54 | PCDOB | incorporação | esquerda (sucessor) | fato público, sem documento no repositório |
| PPS | 2018 | 23 | CIDADANIA | renomeação | centro-esquerda (sucessor) | número confirmado no banco de 2026 |
| PR | 2018 | 22 | PL | renomeação | direita (sucessor) | número confirmado no banco de 2026 |
| PRB | 2018 | 10 | REPUBLICANOS | renomeação | direita (sucessor) | número confirmado no banco de 2026 |
| PROS | 2018, 2022 | 90 | SOLIDARIEDADE | incorporação | centro-esquerda (sucessor) | fato público, sem documento no repositório |
| PRP | 2018 | 44 | PRD | incorporação | centro-direita (sucessor) | fato público, sem documento no repositório |
| PSC | 2018, 2022 | 20 | PODE | incorporação | centro-direita (sucessor) | número confirmado no banco de 2026 |
| PSL | 2018 | 17 | UNIÃO | fusão | centro-direita (sucessor) | fato público, sem documento no repositório |
| PTB | 2018, 2022 | 14 | PRD | fusão | centro-direita (sucessor) | fato público, sem documento no repositório |
| PTC | 2018 | 36 | AGIR | renomeação | centro-direita (sucessor) | número confirmado no banco de 2026 |
