# Recuos de carimbo nos logs do segundo turno

Publicação de 29/10/2026. Gerador: `scripts/politize-se-relogios-build.py`.
Módulo: `politize_se/relogios.py`. Interfaces compartilhadas `relogios.js/.css`
e adaptador próprio no mapa. Reutiliza o critério `relogio` que já integra
“Conferência do arquivo”; não cria um ponto extra nem altera o escore histórico.

## Evidência e interpretação

141 seções em 59 locais oficiais têm um recuo cada, conforme as métricas do leitor
12. Todas as 141 ocorrências foram relidas nos logs arquivados, com hash do pacote
compacto e do original conferidos contra o arquivo associado ao BU. Quantidade e
maior recuo devem recompor exatamente as métricas de cada seção.

**Todos os 141 aparecem antes do primeiro cômputo na ordem escrita do respectivo
arquivo e urna.** Isso não fixa sua posição real no tempo nem em outros arquivos.
113 têm na linha anterior mensagem do operador informando uma data de ajuste
anterior à eleição. 140 têm contagem e ciclos reconciliados com o comparecimento
no BU; um não. 122 seções são de SP. Esses resultados contrários a uma leitura de
recuo durante a votação devem acompanhar a divulgação do sinal.

Exemplo máximo: Jaú/SP, zona 63, seção 315. Um registro SCUE tem carimbo
26/10/2026 16:39:04, mas sua mensagem informa que o operador digitou 25/09/2026
16:42:00. A linha seguinte LOGD tem carimbo 25/10/2026 07:15:31, início das operações.
A diferença é 33h23min33s. Não afirmar que a urna voltou 33 horas durante a votação.
A causa de cada inconsistência requer conferência dos arquivos e da ata.

## Cobertura e agregação

497.897 seções principais nacionais do catálogo do mapa, sem exterior nem dupla
contagem de agregadas. 497.871 têm vínculo verificável entre o hash do log e o BU;
24 não têm hash esperado no catálogo e duas não têm log processado. Essas 26
não são zeros. Um local sem sinal conhecido e com cobertura parcial aparece cinza.

A cor informa duração do recuo: zero; até 60s; >60 a 300s; >300s. Ajuste sem recuo
é categoria própria, inexistente neste extrato. As faixas organizam a leitura,
não medem gravidade de irregularidade. Grupo de pontos usa o maior recuo das
seções representadas; recorte horário recalcula só com as seções selecionadas.
Os logs inconsistentes não possuem último voto utilizável no filtro de horário.

## Modelos e concentração geográfica

`python3 scripts/politize-se-relogios-modelos.py` grava
`analysis/politize_se/relogios-modelos.json`, cruzando os sinais com o modelo do
equipamento vinculado ao BU e usando como denominador as seções principais com
log verificável. Nos 141 casos, `modelo_fonte=log_mesma_urna`: o modelo vem do
log da mesma urna associada ao boletim, e não de inferência pelo ano da eleição:

| Modelo | Seções verificáveis | Com sinal | Taxa |
| --- | ---: | ---: | ---: |
| UE2013 | 11.434 | 1 | 0,00875% |
| UE2015 | 87.212 | 2 | 0,00229% |
| UE2020 | 200.490 | 53 | 0,02644% |
| UE2022 | 198.735 | 85 | 0,04277% |

UE2022 reúne 60,3% dos sinais e UE2020, 37,6%. Mas Jaú/SP concentra 106 dos 141
casos (75,2%): 64/135 seções UE2022 e 42/127 UE2020. As outras 68 seções do
município (UE2013/UE2015) não têm esse sinal. Sem Jaú, permanecem 21/198.600
na UE2022 (0,01057%) e 11/200.363 na UE2020 (0,00549%). A diferença por modelo
permanece, com poucos eventos e concentração geográfica muito acentuada.
O recorte é exploratório: não identifica defeito de modelo, causa operacional
nem efeito sobre votos. Comparar operações, arquivos e atas por local antes de
atribuir causalidade ao equipamento. As 26 seções sem modelo e sem log verificável
não entram nas taxas.

## Dados e privacidade

Cada ocorrência publica somente os dois carimbos, tamanho do recuo, aplicativos,
índice do arquivo, indicação de existência de cômputo anterior na ordem escrita
e, quando explícita, a data anterior informada pelo operador. Sem mensagens livres,
identificadores de eleitor, posição individual de votação ou preferência política.
Carimbos são normalizados por município para Brasília, preservando a virada de dia.

O índice conserva SHA-256 dos arquivos por UF, hash do extrato e lista das seções;
CSV público inclui chave, local, tamanho e contagem do sinal. Links levam ao aux
oficial do TSE. O log bruto permanece preservado no banco local em modo de leitura.

## Verificação

Testes cobrem escopo por urna e arquivo, fusos, contexto anterior ao primeiro
cômputo, ausência diferente de zero, limites de cor, agrupamento, filtros e
recomposição nacional. Navegador: mapa e seção em 390 e 1.440 px; ficha de Jaú com
a mensagem de data anterior explícita. Publicação usa checkout separado a partir
do remoto, preservando trabalhos locais de outras rodadas.
