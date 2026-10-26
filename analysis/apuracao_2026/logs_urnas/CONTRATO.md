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
  31 têm boletins do sistema de apuração sem log VOTA no hash arquivado.
  Esses 31 metadados listam arquivos `logSA`, de outra categoria e não processados
  pelo leitor de ciclos do VOTA. A ficha oferece seus endereços oficiais, sem
  apresentar contagens ou tempos não calculados. Não são ausência de todo registro.
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

As 25 regras e seus textos são fonte única em `scripts/apuracao_logs/criterios.py`.
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
- `secoes.csv.gz`: métricas por seção com URL e SHA-256, sem identificadores pessoais.
- `processos_por_tipo.csv.gz`: três linhas por seção, com distribuições e referências de cada tipo. Vincular a fonte pela chave UF/município/zona/seção do CSV principal.
- Horários operacionais e distribuições por tipo também estão no JSON da zona; não são sequências de eleitores. A separação dos CSVs evita um arquivo único acima de 100 MB.
- `analysis/apuracao_2026/logs_urnas/resumo.json`: espelho do resumo publicado.
- `sinalizadas.json`: intermediário regenerável do mapa, ignorado pelo Git.
- `docs/assets/logs_urnas_2026/complementos.json`: vínculo dos 20 BUs recuperados
  ao local identificado no ASN.1. Endereços vêm apenas do cadastro existente.
  A ficha operacional funciona mesmo sem endereço, pontuação ou perfil histórico;
  as seções sinalizadas entram na lista do mapa mesmo sem coordenada.
- Mapa: índice leve, histórico e recortes por UF; a abertura padrão usa o
  acervo completo, e links com UF carregam apenas o recorte correspondente. Exterior usa cidades aproximadas do Politize, nunca um endereço
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

## Consulta e apresentação (revisão de 15/10)

A entrada padrão do mapa usa **todos os territórios e todas as camadas**. A opção
“Todas” da UF limpa o recorte geográfico, inclusive depois de Exterior, e inclui
ZZ. “Limpar” restaura o mesmo conjunto. Links com filtro explícito continuam
respeitados. O seletor reúne os 12 critérios históricos e os 25 dos logs; cada
opção mostra sua contagem e abre a regra correspondente. CSV e lista incluem
seções sem coordenada, e a consulta combinada não duplica uma seção presente nas
duas camadas. Os números do recorte informam separadamente o exterior.

O relatório é gerado por `view.py`, com componentes de `painel.py`: distribuição
e quantis de duração, composição das habilitações, frequência dos critérios,
recuperação após mensagens de falha e cobertura. Taxas de ocorrência usam o
número avaliável específico de cada regra. As barras dos diagnósticos usam uma
mesma escala linear, com teto arredondado acima da maior taxa; não se impõe
largura mínima para ocorrências raras, cujas taxas continuam publicadas sem
arredondamento a zero. As regras e fontes permanecem acessíveis sem JavaScript.

O capítulo de fiscais e a thread recebem os 25 critérios **antes** das tabelas
históricas. A atualização é idempotente e preserva os outros capítulos. As
planilhas antigas são rotuladas como históricas; a consulta combinada tem sua
própria exportação no mapa. O Politize liga cada ocorrência à regra do relatório
e à consulta nacional do mesmo diagnóstico. Nenhuma dessas mudanças recalcula
pontuação política nem transforma uma ocorrência operacional em acusação.

A regressão de navegador confere abertura sem fragmento, Exterior → Todas,
Limpar, recarga, contagem dos 37 filtros, CSV com ZZ, busca do relatório,
âncoras, leitura sem JS, celular e a posição dos critérios no dossiê.


## Processo observado e caso Santos (leitor v10)

A revisão de 15/10 parte do relato de um leitor em Santos/SP, município TSE
70718, zona 273, seção 214. O original foi baixado novamente no mesmo endereço
oficial e coincide byte a byte com o SHA-256 anterior:
`4873b29f6fba577ab83c6360e6a4efe4b2986f3e206d3447b1388549ad704d1a`.
Os bytes estão no acervo local ignorado, em
`data/originals/tse_logs_2026/casos/sp-273-214/`; o pacote público fornece URL e
hash, não republica identificadores de mesários nem sequências de votação.

O arquivo registra uma partida antes da abertura, nenhum ERRO/FATAL ou nova
partida durante a votação, sete inspeções (14–41 s), nove retomadas da digitação
após inatividade e um cancelamento de habilitação às 10:43:10. Há 275 cômputos,
reconciliados com o BU e com as categorias 215 biométricas, 32 biográficas e
28 sem biometria. O relato de reinício não foi confirmado pelo arquivo; isso
não demonstra que o relato seja falso nem exclui ocorrência fora do registro.
Horário aproximado e ata são necessários para identificar o episódio.
A [orientação oficial de 2026](https://www.justicaeleitoral.jus.br/mesario/cursos/mesarios-brasil/m3-o-que-fazer-durante-a-votacao/a6-cabina-de-votacao/index.html)
prevê inspeções periódicas com convite aos fiscais presentes: explicação
possível para a convocação, não confirmação do que o leitor presenciou.

A leitura anterior cobria tempo após habilitação e intervalo geral, mas não
reconstruía uma métrica principal do processo eletrônico completo nem mostrava
inspeções e retomadas. Agora distinguimos:

- **Processo observado:** mensagem de identificador digitado pelo mesário até
  cômputo, com confirmação de cargo e sem suspensão parcial. A mensagem sucede
  a digitação; o início da conferência documental, a digitação em si e a fila
  não são observados. “Aguardando digitação” é estado de espera e não serve
  como início presumido do atendimento.
- **Identificação inequívoca:** exatamente uma mensagem de identificador no
  ciclo e nenhum cancelamento. Repetições podem envolver pessoas diferentes:
  não somar tentativas como se fossem a mesma pessoa. Uma tentativa encerrada e
  outra aberta depois não são vinculadas; o tempo delas permanece na cadência
  entre cômputos, sem ser atribuído ao processo de um eleitor específico. Início ausente ou ambíguo
  fica excluído, com cobertura publicada. Referência exige ≥30 processos e
  início inequívoco em ≥90% dos ciclos completos do grupo principal de cargos.
- **Tipos separados:** mediana do processo biométrico, biográfico e sem
  biometria; cada referência exige ≥30 processos daquele tipo, ≥30 seções
  elegíveis de mesma UF, modelo e cargos e categorias reconciliadas com o BU.
  A mediana de um tipo só dispara abaixo de 4 escalas robustas da referência
  e abaixo da metade dela. Três tipos são examinados, sem teste confirmatório.
- **Cadência:** intervalo entre cômputos consecutivos completos do grupo
  principal de cargos, na mesma urna e sessão. Nova partida LOGD ou VOTA
  delimita sessão; ciclo parcial ou cômputo não reconstruído quebra a cadeia.
  Inclui transição e espera. Exige ≥30 intervalos, com comparação por UF,
  modelo e cargos. Composição dos tipos e movimento ainda são confundidores.
- **Trecho rápido:** menor média de dez intervalos consecutivos (onze cômputos),
  comparada aos mínimos das outras seções, não a suas médias gerais. Além de
  UF/modelo/cargos, compara faixas de volume 0–99, 100–199, 200–299, 300–399,
  400–499 e 500+ intervalos. Exige corte robusto, menos da metade da referência
  e menos da metade da mediana própria. Janelas sobrepostas são exploratórias.

O grupo principal é o de mais ciclos completos. Empates que não coincidam
entre o agregador do processo e o grupo de votação ficam sem comparação,
sem misturar quantidades de cargos. Relógio inconsistente invalida todos os
novos tempos; a contagem continua separadamente reconciliada com o BU.
A média nacional pondera processos/intervalos por histogramas, não seções.
As bases de processo e cadência são distintas e explicitadas; não subtrair
suas médias como estimativa de espera. Medianas de etapas não são aditivas.
Em Santos: mediana da identificação 18 s, após habilitação 52 s, processo 73 s
(não 18+52) e cadência 97 s; média do processo 87,105 s; 275 processos e
274 intervalos; menor média móvel de dez intervalos 74 s.

Sete novas regras elevam os logs de 18 para 25 (37 com as 12 históricas).
Além das três de rapidez, detectam partida do sistema durante votação,
inspeção de ≥300 s, retomadas e cancelamentos acima da referência (≥3 eventos,
taxa por 100 cômputos acima de 4 escalas robustas e excesso ≥5 eventos por 100;
≥50 cômputos em seções elegíveis de mesma UF/modelo/cargos, ≥30 pares).
Uma contagem fixa de três eventos era comum demais na conferência exploratória
do DF; foi substituída pela comparação relativa antes de publicar. Inspeção rotineira não dispara só por existir;
registro de retomada não é reboot e vários avisos podem ser do mesmo ciclo.
A ficha exibe inspeções, cancelamentos e reinícios mesmo abaixo dos cortes.
As regras de reinício de VOTA e sistema podem descrever o mesmo episódio;
não devem ser somadas como evidências independentes.

A nova implementação está em `processo.py` e `regras_processo.py`, integrada ao
leitor, publicação, relatório, dossiê, mapa e Politize. O teste real de Santos
é opcional quando não existe acervo local; testes sintéticos exercitam limites
de sessão, identificações repetidas, cancelamento, amostra mínima e janelas.

### Preparação com relógio adiantado (leitor 11)

Pacotes aninhados podem conter uma carga antiga com carimbos de 04/10. O leitor exclui esses carimbos da votação somente quando o nome do arquivo registra arquivamento anterior à eleição, existe ajuste explícito para data anterior e o último registro escrito também é anterior. Havendo cômputo datado de 04 ou 05/10, não aplica essa exclusão. Preserva o original e conta `eventos_preparacao_excluidos`; não inventa horários corrigidos. A regra foi verificada nos pacotes BA/34797/60/30 e RJ/60011/204/266 e o acervo inteiro foi reprocessado.

A releitura integral separou 915 eventos de preparação em cinco seções. Em PA, município 04278, zona 73, seção 291, a emenda anterior reconstruía 355 ciclos; separar a partida histórica reconcilia os 356 cômputos, ciclos e comparecimentos do BU. As discrepâncias de contagem caíram de 11 para 10; isso é correção de leitura, não mudança do resultado eleitoral.

### 2º turno (pleito 3221), 26/10/2026

`apuracao_logs/pleito.py` reúne dia de votação e caminhos por pleito. Sem argumento, todos os módulos e scripts seguem o 1º turno como antes (720 seções relidas devolvem JSON idêntico às métricas publicadas, fora os campos novos). No 2º turno: originais em `data/raw/tse_logs_2026/logs_2t.sqlite`, métricas em `data/outputs/logs_urnas_2t_2026.sqlite`, agregados em `docs/assets/logs_urnas_2t_2026/` e `analysis/apuracao_2t_2026/logs_urnas/`.

- **A mesma carga serviu aos dois turnos.** O log do 2º turno traz a carga de setembro, o dia 04/10 e o dia 25/10. O leitor retém só 25 e 26/10 (`dia` em `analisar`); o resto entra como metadado anterior. Em AC, 2.230 de 2.270 logs começam, byte a byte, com o texto do log do 1º turno da mesma seção.
- **Guarda compacta** (`compacto.py`, `--guardar compacto`): prefixo do 1º turno por referência (SHA-256 do ZIP e do texto do 1º turno), restante em xz, metadados do prefixo copiados, diretório do ZIP com CRC-32 e SHA-256 por membro; sem prefixo verificável, texto inteiro em xz; ZIP aninhado guardado como veio. `reconstruir` refaz o texto e confere CRC e SHA. Em AC: 3,1 vezes menor que o ZIP, leitura idêntica nas 2.270 seções (`analisar` sobre o ZIP e sobre o pacote).
- **Campos novos, sem mudar a semântica (leitor continua 12)**: `urnas_log`, `urnas_excluidas_ids`, `cargas_log`, `midias_log`, `computados_por_hora` (relógio da urna) e `computados_por_hora_confiavel`, `contagens.erros_desmontar_mr[_antes_zeresima]`; na reconciliação, `identidade_log` (urna do BU entre as que escreveram o log, código de carga do BU no log da mesma urna). Métricas do 1º turno processadas antes não têm esses campos; quem os lê usa `.get`.
- **Erro técnico no 2º turno**: em AC, 2.259 de 2.270 seções registram ERRO no dia; em 2.198 o único é `GAP: Problema ao desmontar a MR` antes da zerésima. O critério publicado `erro_tecnico` não foi alterado; revisão da regra para o 2º turno exige decisão e nova versão declarada.
- **Comparação seção a seção** (`turnos.py`): matriz de atenção 1T × 2T, persistência e diagnósticos em ambos/só 1T/só 2T, mais os sinais novos. Gerada por `apuracao-2026-logs-build.py --pleito 3221`.

Ordem: (1) terminar a coleta de BUs do 2º turno (o catálogo dos logs é montado uma única vez, na primeira execução); (2) `python3 scripts/apuracao-2026-logs-coletar.py --pleito 3221 --origem apuracao/data/secoes_2t_2026.sqlite --db data/raw/tse_logs_2026/logs_2t.sqlite --guardar compacto --rps 20 --workers 16`; (3) `python3 scripts/apuracao-2026-logs-processar.py --pleito 3221 --workers 10`; (4) `python3 scripts/apuracao-2026-logs-build.py --pleito 3221`. Testes: `tests/test_apuracao_logs_2t.py`.
