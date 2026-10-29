# Encerramento das seções do segundo turno de 2026

Imagem única com o acumulado de seções por corte horário e a votação das seções de cada intervalo. Brasil, sem exterior; eleição presidencial 6258, pleito 3221, 25/10/2026. Não compara turnos. Desde a revisão de 29/10, acrescenta uma coluna independente de cômputos nos logs.

## Fonte e cobertura

Leitura somente leitura de `apuracao/data/secoes_2t_2026.sqlite`. A tabela `bu` fornece `encerramento`, transcrito de `dadosSecao.dataHoraEncerramento` do BU binário. Este é o campo de encerramento utilizado na análise; não foi baixado um CSV BWEB com a coluna literal `DT_ENCERRAMENTO`. O decodificador está em `apuracao/scripts/secoes/banco.ts`.

Votos presidenciais vêm de `voto_secao` (cargo 1), aptos e comparecimento de `bu_cargo` (eleição 6258). O catálogo `secao` define as seções principais. Agregadas não são contadas novamente. O Brasil tem 497.897 seções principais no catálogo, todas com BU, identidade conferida e horário válido. O exterior é excluído antes do cálculo. Os totais recompõem 127.854.631 presentes = 123.710.622 válidos + 1.425.821 brancos + 2.718.188 nulos. Os aptos somam 157.828.819.

`docs/assets/encerramento_2t_2026/dados.json` conserva todos os agregados, a distribuição por segundo, cobertura e hash SHA-256 do extrato ordenado utilizado, incluindo os hashes individuais dos BUs no cálculo. O extrato de entrada é processado localmente e não publicado seção a seção.

## Fusos

Converte-se o relógio local para Brasília (UTC−3) antes de qualquer agrupamento: +2 horas no Acre e em 11 municípios do oeste do Amazonas; +1 hora no restante do Amazonas, RO, RR, MT e MS; −1 hora em Fernando de Noronha; zero nas demais localidades. Os códigos municipais e nomes das exceções estão no módulo de dados. A moda da hora de abertura, após conversão, é 8h em todos os 5.571 municípios, conferência independente realizada apenas com o próprio BU.

Fontes oficiais dos fusos:

- [TSE: horário unificado e Fernando de Noronha](https://www.tse.jus.br/comunicacao/noticias/2026/Setembro/faltam-26-dias-votacao-comeca-e-termina-no-mesmo-horario-em-todo-o-pais).
- [TRE-AM: os 11 municípios que seguem o Acre](https://www.tre-am.jus.br/comunicacao/noticias/2026/Setembro/eleitorado-do-amazonas-deve-ficar-atento-aos-horarios-de-votacao-nas-eleicoes-2026).

## Cortes e denominadores

Os cortes vão de 17:00:00 a 17:10:00 minuto a minuto, depois 17:15, 17:20, 17:25, 17:30, 18:00, 18:15, 18:30, 18:45 e 19:00, sempre com segundos zero. A última linha reúne horários estritamente posteriores a 19:00:00. O primeiro encerramento normalizado foi 17:00:09; o último, 23:04:42. Não se arredondam ou truncam os segundos.

A primeira linha inclui horários até 17:00:00. Cada linha seguinte exclui o corte anterior e inclui o corte atual. Assim, 17:02:00 entra no corte 17h02; 17:02:01 entra no corte 17h03. A interpretação alternativa de “minuto 17h02” incluindo até 17:02:59 não é a utilizada nesta imagem.

Barra: seções encerradas acumuladas / 497.897. Complemento: seções cujo encerramento registrado ainda é posterior ao corte. Não é uma observação ao vivo do funcionamento da seção. No bloco 03, contagens, comparecimento e votos pertencem somente às seções de cada intervalo. O bloco 02 usa todas as seções com logs utilizáveis, independentemente do horário de encerramento. Comparecimento percentual = presentes / aptos do intervalo. Participação dos candidatos = votos do candidato / (Flávio + Lula). UFs são as três com mais seções no intervalo; seus percentuais usam as seções da própria linha. Intervalos de durações distintas não devem ser comparados como taxas por minuto.

## Limite da interpretação

Todos os votos do dia de uma seção acompanham o horário em que ela encerrou. O campo não permite datar votos individuais, medir quantos ocorreram depois das 17h, identificar quais foram consequência de extensão do horário ou separar fila de procedimentos de encerramento. A documentação ASN.1 descreve o campo como término da aquisição do voto, mas isso não justifica tratá-lo como o instante de cada voto nem substituí-lo pelo último cômputo de log. O acumulado de seções continua usando somente o carimbo de encerramento solicitado. A coluna de logs acrescenta outra medida, com cobertura própria.

Os resultados descrevem composições territoriais distintas. Não estimam efeito causal do horário sobre o voto. Até 17:02:00, o agregado tem Flávio 49,7909% e Lula 50,2091% dos válidos; esse valor difere do placar da linha das 17h02, que representa exclusivamente (17:01:00, 17:02:00].

## Reprodução

```sh
.venv/bin/python scripts/encerramento-2t-2026-build.py
.venv/bin/pytest -q tests/test_encerramento_2t_2026.py tests/test_encerramento_logs.py
```

`--so-dados` refaz apenas os dados; `--so-imagem` desenha os agregados salvos. O gráfico usa Matplotlib e fontes locais da skill canvas-design. PNG com 2.800 × 3.200 pixels e PDF vetorial. Fontes tipográficas e PNG/PDF são renderizados sem imagem generativa. A publicação do pacote usa GitHub Pages; não envia o post a redes sociais.


## Cômputos por intervalo nos logs

O bloco 02 conta a mensagem literal `O voto do eleitor foi computado`. Não conta
entrada na fila, habilitações, confirmações de cada cargo ou recebimento pelo TSE.
Não distingue candidato, branco ou nulo. Os percentuais acumulados usam como
denominador os cômputos do dia inteiro nas seções elegíveis, sem extrapolar ausências.

Fontes somente leitura: `data/outputs/logs_urnas_2t_2026.sqlite` e os logs originais
compactados em `data/raw/tse_logs_2026/logs_2t.sqlite`. O universo de seções principais
é exatamente o do gráfico de BUs. Exigir hash do log igual ao associado ao BU,
pleito 3221, fase de votação, relógio válido, contagens e ciclos reconciliados pelo
leitor, total igual ao comparecimento atual do BU e cômputos dentro do dia de
votação após conversão municipal explícita para Brasília.

A regra de relógio do leitor invalida os tempos quando encontra recuos ou ajustes.
Neste extrato há 141 logs nacionais com recuo, de 497.895 processados. É um critério
conservador de cronologia; não significa que todo evento ou o total do BU esteja
errado. Os motivos de exclusão são guardados separadamente em `logs.json`.

Os resumos horários não são interpolados. Nas seções em que o último cômputo já
ocorreu até 17:00:00, o total reconciliado entra integralmente na primeira linha.
Nas demais, reler os textos arquivados com hash do pacote conferido, restringir aos
dias e às urnas aceitas pelo leitor, remover somente linhas exatamente duplicadas
e agrupar os segundos nos mesmos cortes inclusivos do gráfico. A releitura deve
recompor total, histograma horário, primeiro e último cômputos de cada seção.

O primeiro intervalo inclui o dia até 17:00:00. Os demais usam (início, fim],
inclusive após 19:00:00. No JSON e CSV ficam contagem do intervalo, contagem
acumulada, percentual do intervalo e percentual acumulado. Nunca se publica uma
associação entre horário individual e escolha do eleitor.

`encerramento_logs.py` faz a agregação, registra hash do extrato ordenado e a
cobertura por UF. `logs.json` é um agregado reutilizável: alterações de tamanho
ou mtime nas três fontes obrigam a releitura; `--refazer-logs` força o recálculo.
Mudanças na regra do agregador também exigem esse comando. Fontes alteradas
no decorrer da leitura fazem o gerador abortar. Os bancos não são regravados.


Resultado da revisão: 497.725 seções elegíveis (99,96545%), 127.812.804 cômputos
(99,96729% do comparecimento). Exclusões: 141 por relógio, 24 sem hash esperado
no catálogo do BU, cinco por contagem e duas sem log utilizável. Hash ausente não
é hash divergente. Os 41.827 presentes das seções excluídas não têm horário imputado.
Até 17:00:00: 127.778.764 cômputos; depois: 34.040 (0,0266327% dos cobertos).
Após 19:00:00: 11 cômputos. Foram relidos 29.599 logs; 468.126 seções tinham todo
o seu comparecimento computado até o primeiro corte, segundo as métricas.
