# Senado 2027 diante do STF: contexto

Pesquisa de 07/10/2026. Cada fato vem seguido da fonte. A versão estruturada, com os ids de fonte e o campo `acesso` de cada uma, está em `contexto.json`. Onde a fonte não foi aberta, o texto diz.

## 1. Composição

**Os 54 eleitos conferem com o elenco, nome a nome.** A lista da Agência Senado tem os mesmos 54 nomes e partidos do elenco ([Agência Senado, 04/10/2026](https://www12.senado.leg.br/noticias/materias/2026/10/04/conheca-os-54-senadores-eleitos-neste-domingo)). A totalização oficial do TSE (cargo Senador, eleição 6259, 100% das seções) marca os mesmos 54 como eleitos, todos com voto "válido", Deltan Dallagnol inclusive. Os números de cada eleito estão em `contexto.json` (`composicao.eleitos_2026`). Eles vêm dos arquivos oficiais de divulgação do TSE que o coletor local guardou em `apuracao/data/apuracao.sqlite`. Nesta pesquisa não abri a página do TSE, mas os números batem com as 27 matérias estaduais da Agência Senado. Exemplos: Guilherme Derrite 13.273.880 (30,59%), André do Prado 12.703.089 (29,28%), Domingos Sávio 4.968.829, Deltan Dallagnol 2.904.594 (25,14%), Nicoletti 138.269.

**As 27 cadeiras até 2031 conferem** com a lista de senadores em exercício do Senado ([Dados Abertos do Senado, 07/10/2026](https://legis.senado.leg.br/dadosabertos/senador/lista/atual)).

**Renovação.** 14 reeleitos e 18 derrotados entre os 32 que tentaram a reeleição, o que dá 40 senadores novos ([Agência Senado, 05/10/2026](https://www12.senado.leg.br/noticias/materias/2026/10/05/em-2027-senado-tera-40-senadores-novos-e-14-reeleitos); [Agência Brasil, 05/10/2026](https://agenciabrasil.ebc.com.br/politica/noticia/2026-10/pl-elege-19-senadores-e-soma-28-mdb-conquista-sete-vagas-e-pt-seis)).

**Bancadas projetadas.** A Folha dá PL 28, PT 9, MDB 8, PP 6, União 6, PSD 5, Republicanos 5, PSB 4, Novo 3, Podemos 2, PSDB 2, Rede 1, PDT 1 e um sem partido, e já troca Cleitinho por Alex Diniz (PL) e Moro por Luis Felipe Cunha (União) ([Folha, 04/10/2026](https://www1.folha.uol.com.br/poder/2026/10/pl-tera-maior-bancada-do-senado-com-28-congressistas-conheca-nova-composicao.shtml)). O Poder360 tem os mesmos números até onde detalha ([Poder360, 05/10/2026](https://www.poder360.com.br/poder-eleicoes-2026/leia-a-lista-completa-dos-81-senadores-eleitos-para-2027/)). A Agência Brasil dá Republicanos 6 e União 5, sinal de que não trocou os suplentes por inteiro, e lembra que o PT vai a 10 se Wellington Dias voltar. O elenco dá PT 10 e PSD 4 porque põe Wellington Dias na cadeira do PI, como manda o contrato no cenário de governo Flávio. Trocando Dias por Jussara Lima, o elenco bate com a Folha em todos os partidos.

**Contingências** ([mandatos na API do Senado](https://legis.senado.leg.br/dadosabertos/senador/6337/mandatos), consulta de 07/10/2026):

- **MG**: Cleitinho foi eleito governador (55,40%). O 1º suplente é Alex Diniz (PL, segundo Metrópoles, JOTA e Folha) e o 2º é Wander de Souza. Confere com o elenco.
- **PR**: Sergio Moro (hoje no PL) foi eleito governador (50,10%). O 1º suplente é Luis Felipe Cunha (União) e o 2º é Ricardo Guerra. Confere.
- **AC**: Alan Rick disputa o 2º turno contra Mailza Assis (PP); no 1º turno foram 32,27% × 49,76%. O 1º suplente é Gemil Junior. O partido diverge: a API do Senado registra União, com filiação de 02/10/2022, e o JOTA escreve PSD. O elenco grava PSD "a confirmar", e o ponto segue sem confirmação.
- **AM**: Omar Aziz disputa o 2º turno contra Professora Maria do Carmo (PL); no 1º turno foram 40,63% × 24,49%. A 1ª suplente é Cheila Moreira (PT) e o 2º, João Pedro. Confere.
- **TO**: Professora Dorinha disputa o 2º turno contra Vicentinho Júnior (PSDB); no 1º turno foram 45,52% × 43,94%. A 1ª suplente é Professora Lu (o JOTA escreve Lú Parizi) e o 2º, Mauricio Buffon. O partido da suplente não foi confirmado: o arquivo de candidatos de 2022 do TSE devolveu HTTP 429.
- **CE: o elenco está desatualizado.** Camilo Santana está em exercício no Senado desde 02/04/2026, porque deixou o MEC. Augusta Brito exerceu o mandato de 04/02/2025 a 02/04/2026.
- **MA: o elenco está desatualizado.** Ana Paula Lobato reassumiu o mandato em 06/10/2026. Lourdinha Pereira exerceu de 05/08/2026 a 06/10/2026.
- **PI**: Wellington Dias está afastado como ministro do Desenvolvimento e Assistência Social, e Jussara Lima (PSD) exerce o mandato desde 06/05/2026 (Agência Brasil confirma). Confere.
- **AL**: Renan Filho voltou do ministério em 01/04/2026, e o elenco não registra contingência, o que está certo.
- Não há outro titular de cadeira até 2031 licenciado ou ministro.

**Deltan Dallagnol (PR).** O TRE-PR deferiu o registro por 4 a 3 em 08/09/2026. Na véspera da eleição, 03/10, o relator no TSE, Floriano de Azevedo Marques, indeferiu o registro sozinho e mandou anular os votos. No dia da eleição, 04/10, o presidente do TSE, Kassio Nunes Marques, suspendeu essa decisão: os votos foram contados e a palavra final ficou com o plenário. O registro consta como "deferido com recurso". O julgamento está marcado para 08/10, às 10h ([Gazeta do Povo, 07/10/2026](https://www.gazetadopovo.com.br/eleicoes/2026/tse-julga-casos-de-deltan-dallagnol-e-anthony-garotinho-para-definir-eleicoes-no-pr-e-rj/); [Revista Oeste, 07/10/2026](https://revistaoeste.com/politica/tse-julga-registro-da-candidatura-de-dallagnol-nesta-quinta-feira-8/); [Terra, 05/10/2026](https://terra.com.br/noticias/eleicoes/eleito-no-parana-deltan-dallagnol-deve-assumir-vaga-no-senado-com-processo-em-curso-no-tse,f092a88779f2ec7836a85e92b39ae4e1l2nss5ai.html)). Se o registro cair, um advogado ouvido pelo Terra prevê eleição suplementar. Outra matéria, lida apenas no trecho do buscador, fala no terceiro colocado. O ponto está em aberto.

## 2. PEC 8/2021

**O que a PEC faz.** Proíbe decisão individual de ministro que suspenda lei ou ato normativo de efeito geral, ou ato dos presidentes da República, do Senado, da Câmara ou do Congresso. No recesso, admite decisão individual em caso de grave urgência, mas o tribunal precisa julgá-la em até 30 dias depois da volta, senão ela perde o efeito. Concedida uma cautelar em ação de controle de constitucionalidade, o mérito deve ser julgado em seis meses ([Migalhas, 23/11/2023](https://www.migalhas.com.br/quentes/397396/senado-aprova-pec-que-limita-decisoes-monocraticas)). O limite aos pedidos de vista aparece no relato da Migalhas, mas a Revista Oeste noticiou que o trecho foi retirado no 1º turno (lido só no trecho do buscador). A ementa da PEC na Câmara não menciona vista: "declaração de inconstitucionalidade e concessão de medidas cautelares nos tribunais".

**Votação.** No painel oficial, o 1º e o 2º turno de 22/11/2023 deram 52 votos sim e 18 não, com os mesmos votos individuais nos dois turnos. Na véspera, o calendário especial passou por 48 a 20 ([Dados Abertos do Senado](https://legis.senado.leg.br/dadosabertos/votacao?codigoMateria=148030)). A lista completa dos 81 senadores de 2023 está em `pec8_votos`. Os códigos oficiais são:

- AP: ausente, oito casos contando também LP e LS. A CNN registrou essas ausências como "não compareceu".
- LP e LS: licença particular e licença de saúde.
- P-NRV: presente, sem voto registrado. Foram os casos de Cid Gomes e Omar Aziz.
- Presidente: Rodrigo Pacheco, que não votou.

A lista da CNN ([22/11/2023](https://www.cnnbrasil.com.br/politica/pec-que-limita-poderes-do-stf-e-aprovada-saiba-como-votou-cada-senador/)) tem 80 nomes e omite Oriovisto Guimarães, que votou sim. Fora isso, confere com o painel.

**Os 36 senadores de 2027 que já estavam no Senado em 2023:**

- **Votaram sim (25):** Alan Rick, Alessandro Vieira, Carlos Portinho, Damares Alves, Davi Alcolumbre, Dr. Hiran, Eduardo Gomes, Efraim Filho, Hamilton Mourão, Jaime Bagattoli, Jaques Wagner, Jorge Seif, Laércio Oliveira, Lucas Barreto, Magno Malta, Marcio Bittar, Marcos Pontes, Otto Alencar, Plínio Valério, Professora Dorinha, Rogério Marinho, Styvenson Valentim, Tereza Cristina, Wellington Fagundes e Wilder Morais.
- **Votaram não (6):** Beto Faro, Humberto Costa, Marcelo Castro, Rogério Carvalho, Romário e Teresa Leitão.
- **Ausentes (3):** Ana Paula Lobato, Eduardo Braga e Veneziano Vital do Rêgo.
- **Presentes sem voto (2):** Cid Gomes e Omar Aziz.

Em cinco cadeiras, quem votou em 2023 não é quem estará lá em 2027:

- Cadeira de Renan Filho: Fernando Farias votou não.
- Cadeira de Camilo Santana: Augusta Brito votou não.
- Cadeira de Wellington Dias: Jussara Lima votou não.
- Cadeiras de Alex Diniz e de Luis Felipe Cunha: os titulares, Cleitinho e Moro, votaram sim.

**Situação na Câmara.** A CCJC aprovou a admissibilidade em 09/10/2024, por 39 a 18, com relatoria de Marcel van Hattem. A PEC está "aguardando criação de comissão temporária". O último andamento é o REQ 5423/2025, de 04/12/2025 ([Dados Abertos da Câmara, proposição 2410488](https://dadosabertos.camara.leg.br/api/v2/proposicoes/2410488)).

## 3. Listas de declarados

- **Metrópoles: 49**, sendo 32 eleitos e 17 com mandato. Critério: "já se manifestou a favor". Conta Cleitinho e Moro pela cadeira, com a ressalva de que os suplentes devem assumir ([Metrópoles, 05/10/2026](https://www.metropoles.com/brasil/bancada-pro-impeachment-de-ministros-do-stf-deve-chegar-a-49-senadores)). Nomes em `listas_declarados.metropoles`.
- **Gazeta do Povo: 30 dos 54 eleitos.** Critério: declaração na campanha. Amapá, Bahia, Pará, Paraíba, Pernambuco e Piauí não têm eleito na lista. Mara Rocha e Marília Campos aparecem apenas como "admitem discutir". Arthur Lira disse em agosto que não entraria em conflito com o STF ([Gazeta do Povo, 05/10/2026](https://www.gazetadopovo.com.br/eleicoes/2026/eles-se-comprometeram-com-impeachment-de-ministros-stf/)).
- **JOTA: 31 dos 54 eleitos "tendem a apoiar", com bancada de "ao menos 48" na manchete e 47 no corpo do texto.** A planilha embutida na reportagem traz o posicionamento dos 54 eleitos e de 17 senadores atuais. Hamilton Mourão aparece como "pode apoiar, a depender do contexto", o que deve explicar a diferença entre 48 e 47 ([JOTA, 06/10/2026](https://www.jota.info/eleicoes/eleicoes-2026/31-dos-54-senadores-eleitos-tendem-a-apoiar-impeachment-bancada-tem-ao-menos-48); [planilha](https://docs.google.com/spreadsheets/d/16sTsNfZzA1m0eFdQvfwqASBhzs0_aahkI48FVnj5RuI/)).
- **Ranking dos Políticos, publicado pela CNN (Daniel Rittner) e pelo Poder360: 54**, sendo 37 dos 54 eleitos e 17 dos 27 com mandato. Dos 27 restantes, 6 são contrários (entre eles Marília Arraes e Jaques Wagner) e 21 não se posicionaram. O critério é apoio ao instrumento do impeachment, não voto em caso concreto, ressalva feita pelo próprio diretor do Ranking. Não há lista nominal completa nos textos ([CNN, 05/10/2026](https://www.cnnbrasil.com.br/blogs/daniel-rittner/eleicoes/senado-tera-dois-tercos-pro-impeachment-de-ministros-do-stf-em-2027/); [Poder360, 05/10/2026](https://www.poder360.com.br/poder-eleicoes-2026/senado-tera-54-votos-favoraveis-a-impeachment-no-stf-em-2027-diz-estudo/)).
- **Folha: o número final é 49, sendo 35 eleitos e 14 com mandato.** O endereço da matéria ainda diz "51, 3 abaixo do mínimo", porque a primeira versão somava 35 e 16. A versão atual tira Cleitinho e Moro, cujos suplentes não têm declaração pública ([Folha, 04/10/2026](https://www1.folha.uol.com.br/poder/2026/10/senado-tera-ao-menos-51-congressistas-a-favor-de-impeachment-no-stf-3-abaixo-do-minimo.shtml)). O NC News reproduziu os 51 da primeira versão ([05/10/2026](https://ncnews.com.br/2026/10/05/gilmar-mendes-reage-51-senadores-pro-impeachment-desafia-fux/)).
- **Malu Gaspar (O Globo): 49**, sendo 32 eleitos e 17 em mandato. Lido pela reprodução do Alô Alô Bahia ([05/10/2026](https://aloalobahia.com/noticias/2026/10/05/32-senadores-eleitos-tinham-como-pauta-o-impeachment-de-ministros-do-stf-veja-quem-sao/)). O Alô Alô Bahia não fez levantamento próprio: os 32 dele são os de Malu Gaspar. A página do O Globo não abriu, e o endereço do relatório de origem estava truncado.

**Por que os números diferem.** Os 25 eleitos que estão nas três listas nominais (Metrópoles, Gazeta e JOTA) são o núcleo comum. Fora dele:

- Só o JOTA inclui Cid Gomes e Marcelo Castro.
- Só o Metrópoles e o JOTA incluem Mara Rocha, Lucas Barreto e Alexandre Guimarães.
- Só o Metrópoles e a Gazeta incluem Azambuja, Mauro Mendes, Lahesio Bonfim e Teresa Surita. O JOTA deixa Azambuja e Mauro Mendes de fora porque os dois condicionam o afastamento a uma investigação.
- Só a Gazeta e o JOTA incluem Plínio Valério.

Somadas, as três listas têm 35 nomes de eleitos. Nos senadores com mandato até 2031, Metrópoles e JOTA trazem os mesmos 17. A Folha chega a 14 tirando Cleitinho, Moro e um terceiro nome que o texto lido não identifica.

## 4. Rito e quórum

**A Lei 1.079/1950.** Pelo art. 41, qualquer cidadão pode denunciar um ministro do STF. O art. 43 exige firma reconhecida, documentos e cinco testemunhas. Pelo art. 44, a Mesa recebe a denúncia e a encaminha a uma comissão especial, que dá parecer em 10 dias (art. 45). O texto da lei prevê maioria simples para admitir a denúncia (art. 47) e para a pronúncia (art. 54). A pronúncia suspende o ministro e corta um terço dos vencimentos (art. 57). A condenação exige dois terços (art. 68; Constituição, art. 52, parágrafo único) ([Planalto](https://www.planalto.gov.br/ccivil_03/leis/l1079.htm)).

**A liminar de Gilmar Mendes.** Não existe "nova lei do impeachment de 2025". Em 03/12/2025, nas ADPFs 1.259 (Solidariedade) e 1.260 (AMB), Gilmar Mendes suspendeu e reinterpretou trechos da Lei 1.079 ([Congresso em Foco, 03/12/2025](https://www.congressoemfoco.com.br/noticia/114458/decisao-de-gilmar-limita-processos-de-impeachment-contra-ministros)). A liminar teve quatro efeitos:

- só o PGR passou a poder denunciar ministro do STF;
- o recebimento da denúncia passou a exigir dois terços do Senado (54 votos);
- o mérito de decisão judicial deixou de servir como base para acusação;
- ficaram suspensos o afastamento automático e o corte de vencimentos.

Em 10/12/2025, a pedido da Advocacia do Senado, Gilmar recuou na exclusividade do PGR e devolveu a qualquer cidadão o direito de denunciar. Manteve os dois terços e levou o caso ao plenário presencial, tirando-o do plenário virtual marcado para 12 a 19/12 ([Agência Brasil via Movimento Econômico, 10/12/2025](https://movimentoeconomico.com.br/economia/justica/2025/12/10/gilmar-suspende-parte-de-decisao-sobre-impeachment-de-ministros-do-stf/); [Agência Senado, 10/12/2025](https://www12.senado.leg.br/noticias/materias/2025/12/10/moro-critica-gilmar-mendes-na-questao-do-impeachment-de-ministros-do-stf); [Rádio Senado, 12/12/2025](https://www12.senado.leg.br/radio/1/noticia/2025/12/12/gilmar-mendes-reconsidera-suspensao-parcial-da-lei-do-impeachment-de-ministros)). As datas do pedido de trabalho estavam trocadas: 03/12 é a liminar, 10/12 é a reconsideração e 12/12 é a nota da Rádio Senado sobre ela.

Até 02/09/2026, o plenário do STF não havia referendado a liminar ([Ranking dos Políticos](https://ranking.org.br/artigos/impeachment-de-ministro-do-stf); [Migalhas, 04/05/2026](https://www.migalhas.com.br/quentes/455135/impeachment-de-ministros-do-stf-volta-ao-radar-liminar-barra-avanco)). Não localizei julgamento posterior, e a matéria do O Tempo de 06/10 não foi aberta. A lei nova em discussão é o PL 1.388/2023, de Rodrigo Pacheco, nascido do anteprojeto da comissão de juristas presidida por Lewandowski. A CCJ tirou o projeto de pauta em 10/12/2025 ([Agência Senado](https://www12.senado.leg.br/noticias/materias/2025/12/10/ccj-adia-analise-de-nova-lei-do-impeachment-plenario-debatera-em-2026)).

**A reação do Senado em 03/12/2025.** Alcolumbre disse em plenário que só uma lei pode mudar a Lei 1.079. Anunciou reunião de líderes para votar um novo marco legal e o projeto que limita decisões monocráticas. Eduardo Braga, Rogério Marinho, Omar Aziz, Sergio Moro, Alan Rick, Damares Alves e Dr. Hiran discursaram contra a liminar ([Agência Senado, 03/12/2025](https://www12.senado.leg.br/noticias/materias/2025/12/03/senado-reage-a-decisao-que-dificulta-impeachment-de-ministros-do-stf)). Cleitinho apresentou uma PEC para devolver ao Senado o poder de receber denúncias ([Gazeta do Povo, 05/12/2025](https://www.gazetadopovo.com.br/republica/stf-e-alcolumbre-se-articulam-para-aprovar-nova-lei-que-dificulte-impeachment/)).

**O poder do presidente do Senado.** Um pedido só avança se o presidente do Senado despachar. No MS 30672, o plenário do STF manteve um arquivamento feito pela Mesa (lido em resumo de busca, sem acórdão).

- **Arquivamentos de 2020.** Em dezembro de 2020, Alcolumbre arquivou 57 pedidos contra ministros e 2 contra Augusto Aras, 17 deles contra Moraes ([CNN, 04/01/2021](https://www.cnnbrasil.com.br/politica/senado-arquivou-59-pedidos-de-impeachment-contra-pgr-e-ministros-do-stf-em-2020/)). A Bahia Notícias fala em 38, provavelmente contando documentos em vez de pedidos por ministro.
- **Pedidos parados hoje.** Alcolumbre falou em 109 pedidos contra os dez ministros em 01/09/2026, 55 deles contra Moraes ([CNN](https://www.cnnbrasil.com.br/politica/alcolumbre-sobre-stf-ser-alvo-de-109-pedidos-de-impeachment-nao-e-normal/)). A Bahia Notícias conta 134 desde 2021, 55 da gestão Pacheco e 79 da atual, e levanta a hipótese de um novo arquivamento em massa ([07/10/2026](https://www.bahianoticias.com.br/noticia/322145-alcolumbre-pode-repetir-o-que-fez-em-2020-e-arquivar-todos-os-134-pedidos-de-impeachment-de-ministros-do-stf)).
- **ADPF 378.** Os relatórios de origem a citam como precedente do rito de 2015, mas ela não foi reaberta nesta pesquisa.

**A proposta de Marinho.** É o PRS 54/2026, apresentado em 18/09/2026 ([Dados Abertos do Senado](https://legis.senado.leg.br/dadosabertos/materia/pesquisa/lista?sigla=PRS&numero=54&ano=2026); [Gazeta do Povo, 18/09/2026](https://www.gazetadopovo.com.br/republica/marinho-propoe-que-49-senadores-possam-abrir-impeachment-de-ministro-do-stf/)). O projeto:

- dá ao presidente do Senado 30 dias úteis para decidir sobre a denúncia;
- limita a rejeição liminar a quatro hipóteses;
- permite recurso contra a rejeição com assinatura de 9 senadores, e o recurso é aprovado com três quintos (49);
- se o presidente não decidir no prazo, 49 senadores podem exigir que a denúncia seja recebida.

O PRS ainda não foi votado.

**Quórum de PEC.** Três quintos em dois turnos em cada Casa: 49 senadores e 308 deputados. Cláusula pétrea não pode ser abolida (Constituição, art. 60).

## 5. Depois da eleição (04 a 07/10/2026)

- **Bela Megale (O Globo, 06/10), lida por reproduções** ([Política Livre](https://www.politicalivre.com.br/2026/10/stf-avalia-dialogo-e-investigacoes-para-conter-bancada-pro-impeachment/); [Brasil 247](https://www.brasil247.com/brasil/ministros-do-stf-discutem-resposta-a-bancada-que-defende-impeachment/)). Quatro ministros não identificados descrevem duas frentes:
  - diálogo com o PL considerado menos radical, citando Reinaldo Azambuja e Eduardo Gomes;
  - inquéritos sob relatoria do STF que podem andar antes da posse, citando Carlos Jordy (suspeita de desvio de cota parlamentar) e Mauro Mendes (suspeita de desvio de recursos estaduais envolvendo empresa de telefonia).

  Frase atribuída a um ministro: "A valentia vai até a página dois". A Política Livre grafa Mauro Mendes como PL-MT; ele é do União.
- **Andreza Matais, post no X.** "Entre os senadores eleitos, têm muitooos investigados no Supremo. Tirem esses da conta pró-impeachment. Ninguém vai mexer em quem pode picar." O post não traz nomes nem fonte. Li o texto no trecho indexado pelo buscador; a página do X não abriu. Nas notas da coluna dela no Metrópoles até 07/10 não há nenhuma que liste investigados ([índice da coluna](https://www.metropoles.com/colunas/andreza-matais)). A nota mais próxima, de 06/10, é sobre outro assunto: Gilmar Mendes arquivou, a pedido da PGR, o pedido de investigação de estupro contra Alfredo Gaspar, vice de Flávio. Gaspar nega a acusação ([Metrópoles](https://www.metropoles.com/colunas/andreza-matais/gilmar-mendes-manda-arquivar-investigacao-de-estupro-contra-vice-de-flavio)).
- **Gilmar Mendes.** Em conversas relatadas pela imprensa, disse "Sou um enfermeiro que já viu muito sangue. Não me afobo" ([Portal Carlos Souto, 06/10/2026](https://www.portalcarlossouto.com.br/noticias/politica/gilmar-mendes-comenta-votacao-recorde-a-favor-de-impeachment-no-senado/)). Em agosto, comentando as promessas de campanha, tinha dito que "entre o pensamento e a ação, o pensamento e o gesto, vai uma distância enorme" ([NC News](https://ncnews.com.br/2026/10/05/gilmar-mendes-reage-51-senadores-pro-impeachment-desafia-fux/)). Em 06/10 publicou no X que nenhuma liderança política de expressão questionou o resultado do 1º turno. A matéria do O Globo sobre Gilmar dizer que o STF "foi decisivo" não foi aberta.
- **Van Hattem responde a Gilmar.** "No dia 1º de fevereiro de 2027 começamos os trabalhos pelo seu impeachment e pelo de alguns de seus colegas" ([O Liberal, 07/10/2026](https://www.oliberal.com/politica/van-hattem-diz-a-gilmar-mendes-que-pedira-impeachment-de-ministro-no-senado-1.1178327)).
- **Marinho com Fachin, 06/10.** Depois da reunião, disse que o Senado "não vai se omitir" diante de crime de responsabilidade e que hoje se omite. Defendeu a regra das 49 assinaturas e afirmou que Moraes e Dino agem com "viés político" ([Valor](https://valor.globo.com/politica/noticia/2026/10/06/marinho-diz-que-tratou-sobre-impeachment-de-ministros-com-fachin.ghtml); [R7](https://noticias.r7.com/brasilia/apos-encontro-com-fachin-marinho-defende-investigacao-de-ministros-do-stf-pelo-senado-06102026/); [Correio Braziliense, 07/10](https://www.correiobraziliense.com.br/politica/2026/10/7516126-rogerio-marinho-manda-recado-a-dino-e-moraes-apos-reuniao-no-stf.html)).
- **Flávio Bolsonaro, 06/10.** "Com a maioria no Senado, com a maioria na Câmara para fazer o presidente da Câmara, para a gente mudar a Constituição e redemocratizar esse país". Não apresentou proposta concreta ([iG, 07/10/2026](https://ultimosegundo.ig.com.br/2026-10-07/flavio-fala-em-mudar-constituicao-com-maioria-no-congresso.html)).
- **Centrão, segundo a Folha de 07/10.** O grupo passa a defender o impeachment de ao menos um ministro por "sobrevivência eleitoral". Cinco políticos do centrão ouvidos dizem que um impeachment basta como recado, e o alvo mais provável seria Moraes. Eduardo Braga defende mandato para os novos ministros e evita falar de impeachment. Na pauta de reforma aparecem idade mínima de 60 anos, mandatos e foro de políticos nos TRFs ([Folha](https://www1.folha.uol.com.br/poder/2026/10/centrao-se-alinha-a-direita-e-passa-a-defender-impeachment-de-ao-menos-um-ministro-do-stf.shtml)).
- **Lahesio Bonfim (Novo-MA).** "Flávio Dino, eu estou indo atrás de você em Brasília". A assessoria do senador eleito chamou a fala de desabafo, e Dino não comentou ([Folha, 07/10/2026](https://www1.folha.uol.com.br/poder/2026/10/vou-atras-de-voce-senador-bolsonarista-eleito-no-ma-diz-que-vai-se-vingar-de-dino.shtml)).
- **Antes da eleição.**
  - **14/09:** Tereza Cristina ligou para mais de 40 parlamentares pedindo que fossem a Brasília acompanhar a sessão do STF de 15/09 sobre investigar Moraes ([Estadão](https://www.estadao.com.br/politica/coluna-do-estadao/tereza-cristina-aciona-40-senadores-para-acompanhar-em-brasilia-julgamento-de-moraes-no-stf/)).
  - **31/07:** Um blog relatou que dirigentes de União, PP e Republicanos ouviram de ministros do STF que seria "melhor não" se aliar a Flávio. É relato de bastidor com fontes anônimas ([Blog do Ricardo Antunes](https://ricardoantunes.net/temor-ao-stf-freia-apoio-do-centrao-a-flavio-bolsonaro/)).

## 6. Pedidos e CPIs contra ministros

- **Impeachment de Moraes, 04/09/2026.** Autor: Alessandro Vieira, com 20 assinaturas no total ([Portal Tela](https://www.portaltela.com/politica/2026/09/04/pedido-de-impeachment-de-moraes-e-protocolado-com-assinatura-de-20-senadores); [Diario de Pernambuco/Correio Braziliense](https://www.diariodepernambuco.com.br/politica/2026/09/11723169-vieira-pede-impeachment-de-moraes-20-senadores-ja-assinaram-o-pedido.html)).
  - **Assinaram:** Vieira, Leila Barros, Jorge Kajuru, Flávio Arns, Oriovisto Guimarães, Hamilton Mourão, Styvenson Valentim, Damares Alves, Tereza Cristina, Esperidião Amin, Cleitinho, Carlos Viana, Luis Carlos Heinze, Mara Gabrilli, Carlos Portinho, Marcos Pontes, Vanderlan Cardoso, Sargento Reginauro, Zequinha Marinho e Wilder Morais.
  - **Estarão no Senado em 2027:** Vieira, Portinho, Damares, Mourão, Pontes, Styvenson, Tereza Cristina e Wilder.
  - **Defesa:** o escritório Barci de Moraes confirmou que o ministro teve acesso ao contrato, mas diz que foi consulta de compliance sobre impedimento. O próprio pedido não dá por provado que pedidos de Vorcaro tenham sido atendidos.
  - **Marinho não assinou** para "não abrir brecha a uma futura alegação de nulidade" ([Gazeta do Povo, 06/09/2026](https://www.gazetadopovo.com.br/republica/lider-da-oposicao-nao-assina-pedido-de-impeachment-de-moraes-e-alega-riscos-de-nulidade/)).
- **Impeachment de Toffoli, 14/01/2026.** Assinam Magno Malta, Eduardo Girão e Damares Alves, que alegam violação da imparcialidade por vínculos de familiares do ministro com um fundo ligado ao Master ([Gazeta do Povo](https://www.gazetadopovo.com.br/republica/caso-master-senadores-da-oposicao-pedem-impeachment-de-toffoli/)).
- **CPI do Master (Moraes e Toffoli), 09/03/2026.** O requerimento de Vieira reuniu 29 assinaturas, e Flávio Bolsonaro foi a 29ª ([InfoMoney](https://www.infomoney.com.br/mercados/senador-obtem-assinaturas-para-abrir-cpi-contra-moraes-e-toffoli-por-caso-master/)).
  - **Assinaturas de quem estará no Senado em 2027 (15):** Alan Rick, Vieira, Portinho, Damares, Dr. Hiran, Mourão, Bagattoli, Laércio, Magno Malta, Bittar, Pontes, Plínio, Marinho, Styvenson e Wilder.
  - **Desfecho:** a CPI não foi instalada. Em 22/09/2026, Zanin negou liminar no mandado de segurança de Vieira contra a omissão de Alcolumbre ([SBT News](https://sbtnews.sbt.com.br/noticia/politica/zanin-nega-liminar-que-obriga-senado-a-apurar-caso-master)).
- **CPI do Crime Organizado, 14/04/2026.** O relatório de Vieira pedia o indiciamento de Toffoli, Moraes, Gilmar e Gonet, com encaminhamento ao impeachment. Foi rejeitado por 6 a 4 ([Congresso em Foco](https://www.congressoemfoco.com.br/noticia/118073/cpi-do-crime-organizado-relator-pede-indiciamento-de-ministros-do-stf); [Estadão via UOL](https://noticias.uol.com.br/ultimas-noticias/agencia-estado/2026/04/14/cpi-do-crime-organizado-rejeita-relatorio-que-visava-impeachment-de-ministros-do-stf-e-pgr.htm)).
  - **Contra o relatório:** Beto Faro, Teresa Leitão, Humberto Costa, Soraya Thronicke, Rogério Carvalho e Otto Alencar.
  - **A favor:** Vieira, Eduardo Girão, Magno Malta e Esperidião Amin.
  - **Antes da votação:** a base do governo trocou integrantes da comissão. O presidente da CPI, Fabiano Contarato, disse não ver prova de dolo.
  - **Reação do STF:** Gilmar pediu à PGR que investigue Vieira por abuso de autoridade ([Folha, 14/04/2026](https://www1.folha.uol.com.br/poder/2026/04/gilmar-pede-a-pgr-que-alessandro-vieira-seja-investigado-por-abuso-de-autoridade-em-cpi.shtml)).
- **Lista de apoio a impeachment de Moraes, 07/08/2025.** São 41 nomes reunidos durante a ocupação do plenário, mas a lista não é um pedido protocolado. Dos 41, 22 estarão no Senado em 2027 ([Bahia Notícias](https://www.bahianoticias.com.br/noticia/307266-oposicao-anuncia-que-tem-41-assinaturas-pelo-impeachment-de-alexandre-de-moraes-confira-quem-apoia-o-pedido)).

## O que ficou sem verificação

- Os votos de cada eleito vêm dos arquivos oficiais do TSE guardados pelo coletor local, não de página do TSE aberta nesta pesquisa.
- O partido atual dos suplentes Gemil Junior (AC) e Professora Lu (TO) não foi confirmado: o arquivo de candidatos de 2022 do TSE devolveu HTTP 429.
- As listas nominais completas do Ranking dos Políticos e da Folha não aparecem nos textos lidos.
- O post de Matais e a coluna de Bela Megale foram lidos por trecho de busca ou por reproduções.
- As matérias do O Tempo (06/10/2026) e do G1 (10/12/2025) não foram abertas.
- O julgamento de Deltan no TSE está marcado para 08/10, depois da data de corte.
- ADPF 378 e MS 30672 foram vistos sem leitura do acórdão.
- A matéria da Terra/Estadão sobre as "traições" na PEC 8 não foi aberta; o painel oficial do Senado a substitui.
