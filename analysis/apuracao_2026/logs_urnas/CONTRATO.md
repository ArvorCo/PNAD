# Logs das urnas do primeiro turno de 2026

Camada operacional da apuração, do mapa de fiscais e da ficha de seção do
Politize. Fontes e métricas são agregadas por seção. As regras não recebem
votos de candidatos, preferências políticas ou características individuais.

## Fonte e cadeia de proveniência

- Catálogo: seções principais em `apuracao/data/secoes_2026.sqlite`, tabela
  `secao`, com município, zona, seção, hash de transmissão e nome do log.
- Downloads: endereço oficial `resultados.tse.jus.br/oficial/ele2026/arquivo-urna/3220/dados/`.
  A URL completa e o SHA-256 acompanham cada seção publicada.
- O coletor original havia guardado nomes e hashes, mas não os bytes dos logs.
  A recuperação usa o mesmo hash de transmissão do BU, sem substituir pela
  versão mais recente silenciosamente.
- Havendo SHA-256 anterior, os bytes precisam coincidir. Sem hash anterior,
  `hash_anterior_confere=null`: o hash novo identifica o arquivo, mas não
  representa uma comparação aprovada.
- Originais compactados: `data/raw/tse_logs_2026/logs.sqlite`. A tabela
  `catalogo` também preserva seções sem nome de log; `arquivos` guarda o ZIP,
  HTTP, data, hash e estado. Dados pesados ignorados pelo Git.
- Métricas: `data/outputs/logs_urnas_2026.sqlite`, com versão do leitor e hash
  do original. Mudança semântica no leitor ou na reconciliação exige incrementar
  `parser.VERSAO` e reprocessar. O observador em execução deve ser reiniciado.
- SHA-256 não é validação independente da assinatura eleitoral. O leitor
  reporta mensagens de verificação de assinatura emitidas pelo próprio sistema.
- A reconsulta de 15/10 dos 92 metadados sem nome de log está em `lacunas.json`,
  com as respostas originais em `data/originals/tse_logs_2026/lacunas/`. As 20
  seções antes `aux_404` agora oferecem BU e log; 41 continuam não instaladas e
  31 têm boletins do sistema de apuração sem log listado no hash arquivado.
  Os 20 BUs recuperados ficam em `complementos.json` e
  `data/originals/tse_logs_2026/complementos/`, com URL, SHA-256 e identidade
  validada pelo ASN.1. Complementam apenas chaves antes sem hash/log, nunca
  substituem um BU existente. O banco histórico da apuração permanece intacto.
  Os comandos de reconsulta/preparo retomam o manifesto preservado; uma nova
  rodada exige preservar outro snapshot, sem sobrescrever esta evidência.
- Referências: [documentação TSE 2026](https://www.tse.jus.br/eleicoes/eleicoes-2026)
  e [catálogo dos arquivos transmitidos](https://dadosabertos.tse.jus.br/dataset/resultados-2026-arquivos-transmitidos-para-totalizacao).
  O PDF de formato do log retornou HTTP 403 nesta rodada; não foi apresentado
  como documentação lida. O vocabulário foi conferido nos originais e contra BUs.

## Reconstrução

O parser abre ZIPs aninhados sem extração em disco, com teto de expansão e
profundidade. Decodifica Latin-1. Usa 4 e 5 de outubro, confirma identidade da
seção ou número interno da urna e exclui fases explicitamente não oficiais.
Metadados de carga anteriores ao dia 4 são usados quando não reaparecem no dia
da eleição: uma urna pode ter permanecido ligada desde a véspera. O último valor
anterior preenche só campos ausentes, sem sobrescrever identidade ou fase do dia.
Remove apenas linhas integralmente duplicadas. Recuos de carimbo temporal são
contados antes de ordenar os fragmentos. Mesmo um recuo de um segundo retira
a seção das comparações de duração; gravação assíncrona é explicação possível,
não se conclui automaticamente que o relógio físico foi adulterado.
Em pacote com um único arquivo de eventos e recuo de relógio, preserva-se a
ordem de escrita para reconstruir contagens: ordenar pelos carimbos poderia
inserir uma partida anterior dentro de um ciclo posterior. As durações continuam
inválidas. Em múltiplos fragmentos, a emenda temporal continua sujeita à qualidade
da ordem; discrepâncias permanecem explícitas e exigem conferência documental.

Três relógios distintos:

1. Habilitação: identificador digitado pelo mesário até eleitor habilitado.
2. Votação: habilitação até voto computado, excluindo suspensão parcial.
3. Intervalo: dois eventos de voto computado consecutivos. Inclui ociosidade;
   não mede fila, velocidade individual constante ou interrupção confirmada.

Ciclos sem suspensão e com confirmação de cargo são agrupados pela quantidade
de confirmações. Exterior não é comparado ao Brasil. Trânsito pode produzir
outras quantidades de cargos. A média geral pondera ciclos; o quadro por cargos
explicita a composição. Mediana e p90 nacionais vêm de histogramas agregados,
sem expandir ou publicar sequências individuais.

Suspensão sem voto não aumenta o comparecimento. Suspensão parcial gera voto
computado, mas fica fora do tempo de ciclo completo. Um pedido de cancelamento
pode cruzar com a captura de digital ainda em andamento; não encerra o estado
imediatamente. A volta à espera de identificador encerra a tentativa.

## Reconciliação e biometria

O número de eventos computados **e** de ciclos reconstruídos deve reproduzir
o comparecimento no BU associado. As categorias reconstruídas devem reproduzir:

- `hab_biometria`: reconhecimento biométrico;
- `hab_ano_nascimento`: habilitação biográfica;
- `comp_sem_biometria`: categoria sem biometria.

Biográficas / (biométricas + biográficas) e sem biometria / comparecimento são
taxas diferentes. BUs sem essas contagens, encontrados também no exterior,
produzem estado `ausente_bu`, não zero e não divergência. Categoria desconhecida
ou contagem divergente retira a seção das comparações de biometria.

Tempo comparável requer contagem conciliada, relógio consistente, zerésima
anterior e encerramento posterior localizados, sem linhas malformadas,
fase 2, pleito 3220 e ao menos 30 ciclos. A comparação de habilitação exige
também ao menos 30 etapas com início observado. Essas condições são regras de
qualidade da análise, não certificação de regularidade eleitoral.
Para comparação por modelo, uma seção com múltiplos modelos observados, modelo
indeterminado ou conflito entre log e BU também fica fora. Quando o BU não informa
o modelo e o log informa um único modelo, usa-se o observado no log. A comparação
de biometria igualmente exige modelo comparável; suas contagens reconciliadas
continuam disponíveis mesmo quando a referência não pode ser calculada.

## Diagnósticos e sensibilidades

As 18 regras e seus textos são fonte única em `scripts/apuracao_logs/criterios.py`.
O build publica regra, limitação, o que conferir, contagem e denominador avaliável.
São triagem exploratória, sem p-valor ou probabilidade de fraude.

Referências de tempo: UF × modelo × quantidade de confirmações de cargo.
Referências de biometria: UF × município × zona × modelo. Pelo menos 30 seções
elegíveis; biometria exige denominador de 50 pessoas. A seção participa da
referência. Mediana e escala 1,4826 × MAD, com piso de 3 segundos ou 1 ponto
percentual. Corte principal de 4 escalas, alternativas 3 e 5; diferenças mínimas
adicionais estão no catálogo. Sem suporte suficiente, referência ausente.

Os 12 critérios históricos e suas pontuações ficam preservados. Os diagnósticos
dos logs não somam pontos: são correlacionados e incluem recursos normais de
continuidade, como bateria. Os marcadores azuis significam registro operacional.
Falhas registradas antes de abrir ou depois de encerrar a votação podem entrar
na ocorrência do dia; não implicam que o eleitor enfrentou falha não resolvida.
Para assinaturas, o leitor conta separadamente erros seguidos de SUCESSO para o
mesmo arquivo e urna, erros sem sucesso posterior localizado e ordem temporal
incerta. Também separa ERRO/FATAL dentro e fora da janela entre a primeira
habilitação reconstruída e o último cômputo, quando essa janela é observável.
Texto crítico malformado entrou após conferência literal de “Eleitor foi ha`ilitado” no arquivo de RJ, zona 8, seção 61. O detector exige o mesmo
comprimento, prefixo reconhecível e uma ou duas substituições em três mensagens
fixas; não corrige eventos por semelhança. Não identifica a origem física do dano
nem substitui validação criptográfica da cadeia do log.

## Cobertura e publicação

`indice.json` publica os estados mutuamente exclusivos de todas as seções do
catálogo. Uma seção ausente do conjunto lido nunca recebe zero ocorrências.
Downloads pendentes, 404, hash divergente, sem BU, erro de leitura e pendência
da versão atual do leitor permanecem distinguíveis na ficha da seção.

- `docs/logs_urnas_2026.html`: relatório gerado, não editar diretamente.
- `docs/assets/logs_urnas_2026/indice.json`: cobertura, regras, sensibilidade e hashes do código.
- `zona/<UF>/<zona>.json.gz`: agregados por seção e motivos de indisponibilidade.
- `secoes.csv.gz`: mesmas métricas com URL e SHA-256, sem identificadores pessoais.
- `analysis/apuracao_2026/logs_urnas/resumo.json`: espelho do resumo publicado.
- `sinalizadas.json`: intermediário regenerável do mapa, ignorado pelo Git.
- `docs/assets/logs_urnas_2026/complementos.json`: vínculo dos 20 BUs recuperados
  ao local identificado no ASN.1. Endereços vêm apenas do cadastro existente.
  A ficha operacional funciona mesmo sem endereço, pontuação ou perfil histórico;
  as seções sinalizadas entram na lista do mapa mesmo sem coordenada.
- Mapa: índice leve, histórico e recortes por UF; acervo completo só quando
  solicitado. Exterior usa cidades aproximadas do Politize, nunca um endereço
  inventado de consulado. Zona 1 não é um centro geográfico mundial.
  Desenho em lotes canceláveis: mudar a UF ou os filtros interrompe os lotes do
  recorte anterior. A regressão de concorrência é exercitada no teste de navegador.

Os blocos de apuração e thread são gerados pela mesma função `view.bloco`.
A atualização cirúrgica evita regenerar capítulos históricos alheios à tarefa.
O Politize importa `logs.js`; a pontuação anterior não muda. Nenhum identificador
de eleitor ou mesário, sequência de horários individuais ou opção digitada é
exportado pelo novo conjunto público.

## Reprodução

```sh
python3 scripts/apuracao-2026-logs-coletar.py
python3 scripts/apuracao-2026-logs-lacunas.py
python3 scripts/apuracao-2026-logs-lacunas.py --preparar-bus
python3 scripts/apuracao-2026-logs-lacunas.py --aplicar
python3 scripts/apuracao-2026-logs-coletar.py
python3 scripts/apuracao-2026-logs-processar.py
python3 scripts/apuracao-2026-logs-build.py
python3 scripts/fiscais-mapa-build.py
python3 scripts/social-card-logs-urnas.py
python3 scripts/sitemap-build.py
pytest -q tests/test_apuracao_logs*.py tests/test_politize_fiscal.py
python3 -m http.server 4187 --directory docs
# Em outro terminal, com o servidor ativo:
python3 scripts/apuracao-2026-logs-ui.py
```

Coletor retomável, um escritor SQLite, limite de requisições e recuo em 403/429.
`--uf`, `--limite`, `--rps` e `--workers` permitem amostras operacionais.
Reserva mínima de 15 GiB no disco. Não apagar os originais para liberar espaço.
`--acompanhar` no processador acompanha downloads; encerrá-lo depois de alcançar
o catálogo antes do build final. Builds durante coleta são explicitamente parciais.

Os JSONs de zona usam gzip determinístico (mtime zero), descompactado no navegador
com `DecompressionStream`. Isso mantém o site abaixo do limite publicado de 1 GB
do GitHub Pages. O leitor reconhece também respostas já descompactadas pelo servidor.
Navegadores sem essa API mostram a limitação e o CSV, sem quebrar o restante da ficha.
