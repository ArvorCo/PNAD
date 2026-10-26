# Registro Digital do Voto (RDV) do 2º turno de 2026

Coleta: `apuracao/scripts/rdv-coletar.ts` grava `apuracao/data/rdv_2t_2026.sqlite`.
Análise: `python3 scripts/apuracao-2t-2026-rdv.py` grava `analysis/apuracao_2t_2026/dados/rdv.json`.
Testes: `apuracao/tests/rdv-decode.test.ts` e `tests/test_apuracao_2t_2026_rdv.py`.

## Conclusão primeiro: o RDV não revela o voto cruzado

O pedido partia da premissa de que o RDV guarda, voto a voto e em ordem embaralhada, as
escolhas de cada eleitor em todos os cargos. A especificação oficial de 2026 e os arquivos
publicados mostram outra coisa:

1. Os votos ficam guardados **por eleição e por cargo**. Presidente está na eleição
   federal (6258) e governador na estadual (6260), cada um numa lista própria.
2. Cada lista vem **ordenada por tipo de voto e digitação**, não embaralhada. O README do
   pacote oficial (p. 7) diz que a ordenação existe "para salvaguardar seu sigilo": primeiro
   legenda, depois nominais, brancos, nulos, e dentro de cada tipo pela digitação.
3. Não existe registro por eleitor. Nada no arquivo liga o voto de presidente ao de
   governador de uma mesma pessoa.

O TSE descreve o mesmo princípio na página "Votação segura": o voto de cada cargo é
armazenado numa posição diferente, "não permitindo qualquer tipo de associação entre
votos, tampouco a associação desses votos com a sequência de comparecimento"
(`data/originals/rdv_2022_alegacoes/tse_votacao_segura.html`).

Conferido nos arquivos: as 2.270 seções do Acre com RDV têm as duas listas ordenadas
(`rdv_cargo.ordenado = 1` em 4.540 de 4.540), e as contagens batem com o BU em todas.

Consequência: a matriz presidente × governador **não é identificável** a partir de dado
público. O que se pode publicar é o intervalo que as duas margens permitem (limites de
Fréchet), seção a seção e somado. No Acre esse intervalo é largo demais para dizer algo:
o par Lula e Mailza Assis cabe entre 1,9% e 31,6% dos votantes; Flávio e Mailza, entre
24,0% e 56,8%. Quem quiser a matriz precisa de pesquisa de opinião com as duas perguntas
na mesma entrevista, não de arquivo de urna.

## Formato

- Arquivo: `o03221<uf><mun5><zona4><secao4>-rdv.dat`, listado no `aux.json` da seção com
  `"tp": "rdv"`, no mesmo hash do BU e do log. URL:
  `https://resultados.tse.jus.br/oficial/ele2026/arquivo-urna/3221/dados/<uf>/<mun>/<zona>/<secao>/<hash>/<arquivo>`.
  Na urna de reserva usada com o RED existe também `-rdvred.dat`.
- Especificação: `rdv.asn1` (ModuloRegistroDigitalVoto) do pacote "Formato dos arquivos de
  BU, RDV e assinatura digital", baixado em 25/10/2026 de
  `https://www.tse.jus.br/eleicoes/eleicoes-2026-content/arquivos/formato-arquivos-de-bu-rdv-e-assinatura-digital`
  (ZIP de 1.265.306 bytes, SHA-256 `b5ac413e…bbfbafd`; `rdv.asn1` SHA-256 `282dcde0…a465`).
  Arquivado em `data/originals/tse_formato_bu_rdv_2026/` com `fonte.json`; cópia em
  `apuracao/scripts/secoes/rdv.asn1`.
- Codificação: BER, IMPLICIT TAGS. Ao contrário do BU, sem envelope: a raiz já é
  `EntidadeResultadoRDV {cabecalho, urna, rdv}`. `rdv` traz pleito, fase, identificação da
  seção, histórico de cargas e `eleicoes` (CHOICE `[1]` urna e RED, `[2]` Sistema de
  Apuração). Cada eleição tem `votosCargos`; cada cargo, `quantidadeEscolhas` e a lista
  `votos` de `Voto {tipoVoto, digitacao?}`.
- Tipos de voto do RDV (numeração diferente da do BU): 1 legenda, 2 nominal, 3 branco,
  4 nulo, 5 branco após suspensão, 6 nulo após suspensão, 7 nulo por repetição, 8 e 9 nulo
  em cargo sem candidato. Nulo traz a digitação.
- Decodificador próprio sem dependência: `apuracao/src/secoes2t/rdv-decode.ts`, conferido
  contra `asn1tools` sobre a especificação oficial na seção de teste
  (`apuracao/tests/fixtures/rdv/`).

## Banco `rdv_2t_2026.sqlite`

- `rdv`: uma linha por seção tentada (status `ok`, `sem_rdv`, `agregada`, `aux_404`,
  `rdv_404`, `erro`), hash, nome, bytes, SHA-256, arquivo em gzip, cabeçalho, origem,
  `id_confere` (seção do arquivo = caminho), `confere` contra o BU (1, 0 ou nulo enquanto o
  BU não está no banco dos BUs) e as divergências.
- `rdv_cargo`: lista por cargo, tamanho e `ordenado`.
- `rdv_voto`: contagem por (cargo, tipo do RDV, digitação).
- O aux vem de `secoes_2t_2026.sqlite`, aberto só para leitura; o aux pedido pela própria
  coleta fica em `rdv.aux_json`.

Conferência com o BU: nominal por número, legenda por partido, branco (3 e 5) contra
branco, nulos (4, 6, 7) contra nulo, cargo sem candidato fundido ao nulo dos dois lados.
`--so-conferir` reconfere depois que o BU chega; `--reconferir-divergentes` refaz também as
que divergiram.

### Resultado final da coleta (26/10/2026)

- 517.179 seções tentadas (todas as do `-cs.json`), 499.205 com RDV, 17.931 sem aux (404,
  as mesmas sem BU) e 43 com aux sem RDV.
- **499.205 de 499.205 conferem com o BU, divergência zero.** 499.176 contra o BU da urna e
  29 contra o BU do Sistema de Apuração (`busa.dat`, campo `conferencia_busa` em `rdv.json`).
- Listas fora da ordem exigida pela especificação: zero.
- Duas seções do exterior (`o03221zz2956400010091-busa.dat` e
  `o03221zz3068600010443-busa.dat`) apareceram como "cargo 1 ausente do BU" na primeira
  passada. Não era divergência de votos nem limite da decodificação: o `busa.dat` decodifica
  com o cargo 1 e a lista de votáveis vazia (apuração totalmente manual, motivo 99, outros;
  72 e 30 aptos, comparecimento 0), e o RDV do SA traz o cargo 1 com zero votos. O comparador
  inferia o cargo pelas linhas de `voto_secao`, e cargo sem voto não gera linha. Corrigido
  (ausência só conta quando o RDV tem votos no cargo), com teste, e reconferido. As duas ficam
  listadas em `conferencia_busa.secoes_sem_votos` com o motivo; conferem por igualdade em
  zero, não por votos comparados.

## O que o RDV permite

- **Conferir o BU** seção a seção por outra via publicada pelo próprio TSE.
- **Ler a digitação dos nulos**, que o BU não mostra. É o único achado substantivo novo.
  Nas seis UFs com governador, 231.121 dos 452.800 nulos de governador (51,0%) são o número
  de um finalista presidencial digitado no campo de governador, e 119.562 dos 287.613 nulos
  de presidente (41,6%) são o número de um candidato a governador da UF. É piso: no AM (22),
  no DF (13) e no RN (13) um candidato a governador tem o número de um finalista, e ali a
  troca vira voto válido e não aparece (`numero_compartilhado` em `rdv.json`).
  No Acre, 72,7% dos nulos de governador (21.536 de 29.612) são números de presidente
  teclados no campo de governador: 12.082 vezes 22 e 9.454 vezes 13. Na outra direção,
  64% dos nulos de presidente são números de governador (11: 7.197; 10: 3.287). A diferença
  de brancos e nulos entre governador e presidente no estado (4,45 pp) é, em boa parte,
  número de presidente digitado no governo. Leitura cautelosa: a digitação mostra o que foi
  teclado, não a intenção (erro, protesto ou recusa das duas candidaturas, que no Acre são
  do mesmo campo de Flávio).
- **Contar brancos e nulos após suspensão e nulos por repetição** (tipos 5 a 7).
- **Medir quantos eleitores em trânsito** votaram só para presidente: a lista de presidente
  fica maior que a de governador (320 no Acre, em 45 seções), e a diferença entra na matriz
  como a categoria `transito`.

## O que o RDV não permite

- Reconstruir a sequência de votação: a lista é ordenada por tipo e digitação.
- Identificar eleitor, ligar voto a horário ou ao caderno de votação.
- Medir voto cruzado entre cargos, nem por eleitor nem por seção.
- Testar "votos de uma pessoa só" (um mesmo eleitor votando várias vezes): sem vínculo entre
  registros e sem ordem temporal, não há assinatura individual a procurar. O que existe é o
  comparecimento e a biometria no BU e a sequência de eventos no log da urna, que é onde esse
  teste deve ser feito.

## Hipóteses testáveis com o que existe

1. RDV = BU em toda seção (gravado em `rdv.confere`).
2. Listas sempre ordenadas no VOTA e no RED (desvio seria fuga da especificação).
3. Taxa de nulos por cargo e o que foi digitado, por UF e município; em particular a troca de
   campo (número de presidente no governo e vice-versa) nas seis UFs com governador.
4. Limites de Fréchet por seção para presidente × governador, somados por município e UF,
   publicados só como limites.

## O que se alegou sobre RDV em 2022, e a resposta

- **Jus.com.br, 25/07/2022** (Daniel Tiago Inácio Salina, "A possível fraude eleitoral do
  RDV"): combinações únicas de votos para deputado no RDV permitiriam ao partido conferir
  voto comprado. A premissa é que os votos de um eleitor ficam ligados entre cargos. A
  especificação de 2026 e a página do TSE dizem o contrário: cada cargo em lista própria,
  sem associação. No formato de 2026 a tese não se aplica.
- **Relatório apócrifo e live de Fernando Cerimedo, 04/11/2022**: dizia que diferenças nos
  logs provavam dois softwares de votação. O RDV só aparece no relatório como um dos tipos de
  arquivo publicados; a alegação era sobre os logs. O Comprova (09/11/2022) classificou como
  falso; o TSE afirmou que o VOTA das urnas antigas é o mesmo do modelo 2020.
- **Representação da coligação PL, Republicanos e PP, 22/11/2022**, com relatório do
  Instituto Voto Legal: pedia anular votos de urnas anteriores ao modelo 2020 por falta de
  identificação individual no log. Era alegação sobre log, não sobre RDV. Em 23/11/2022 o
  presidente do TSE, Alexandre de Moraes, indeferiu o pedido, chamou a alegação de falsa e
  aplicou multa de R$ 22.991.544,60 por litigância de má-fé, com bloqueio do fundo
  partidário das legendas da coligação.

Não localizamos nesta rodada alegação de 2022 que dependesse de ler voto cruzado no RDV.
Páginas arquivadas com SHA-256 em `data/originals/rdv_2022_alegacoes/fonte.json`.

## Limites

- `rdv.json` marca `meta.parcial` enquanto a coleta não cobre todas as seções do `-cs.json`.
- Seções agregadas não têm arquivo próprio; seções sem BU (aux 404) também não têm RDV.
- Seções com apuração pelo Sistema de Apuração usam `eleicoesSA`, sem ordenação obrigatória.
- Os limites de Fréchet usam só as margens da seção; nenhum modelo ecológico foi aplicado.
- Atipicidade pede explicação, não prova irregularidade.
