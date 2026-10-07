# Politize sua vizinhança: decisões do motor de dados

Registro das escolhas feitas onde o contrato (`analysis/politize/CONTRATO.md`) era omisso, pedia algo que
as fontes não têm ou tinha consequência que vale ver antes de publicar. Os números citados saem de
`analysis/politize/relatorio_build.md` (build nacional de 07/10/2026) e dos JSON em
`docs/assets/politize/dados/`.

## Universo e votos

1. **Voto nominal em número fora da lista oficial (nº 28) conta como nulo**, como na totalização do TSE e
   como em `analysis/apuracao_2026/CONTRATO_SECOES.md`. São 5.246 votos. Sem isso, a terceira via ficaria
   5.246 votos acima do oficial e os válidos não fechariam com 47,03 / 45,16.
2. **Seção agregada vota no local da principal.** O cadastro dá à agregada o número do próprio local, e
   2.064 agregadas têm `local_nr` diferente da principal; como o voto delas está na urna da principal, o
   perfil delas também vai para a principal e para o local da principal.
3. **Diferença para o total oficial.** O banco por seção soma Flávio 56.102.134 e Lula 53.877.286; o TSE
   publica 56.104.503 e 53.879.538. A diferença (2.369 e 2.252) são as 20 seções sem arquivo publicado
   (`aux_404`, Betim, Uberlândia e Carapicuíba), que entram na totalização e não têm boletim; as outras 41
   seções principais sem boletim são do exterior e não foram instaladas.
4. Aptos e comparecimento vêm de `bu_cargo` (cargo 1), que inclui o eleitor em trânsito. Todos os tipos de
   urna e de arquivo (urna de seção, contingência, sistema de apuração) entram.
5. **Terceira via separada por candidatura** (pedido do coordenador): `cury` (70), `renan` (14), `caiado`
   (55), `zema` (30) e `outros_nominais` (demais números da lista: 16, 21, 27, 29, 35, 80). O nº 28 fica
   em `nulos`, como no item 1.

## 2022

6. **`abst22_2t_a` não está no CSV compacto de 2022**, que só traz aptos e comparecimento do 1º turno. O
   2º turno vem de `data/raw/tse_resultados/detalhe_votacao_secao_2022.zip` (arquivo
   `detalhe_votacao_secao_2022_BR.csv`, presidente, turno 2), lido em fluxo e registrado como fonte
   `detalhe_2022` em `indice.json`.
7. Seção casada: mesma UF, município, zona e número, `local_nr_2022` igual ao número do local de 2026,
   aptos de 2022 e nominais do 1º turno maiores que zero. Cobre 88,3% dos aptos.
8. **`reencontro_a` compara as mesmas seções**: Bolsonaro 2022 sobre os aptos de 2022 das seções casadas
   menos Flávio 2026 sobre os aptos de 2026 dessas mesmas seções. Comparar com Flávio do local inteiro
   misturaria seções sem par em 2022.
9. `cobertura_2022` sai como fração de 0 a 1 (três casas), lendo literalmente "aptos casados / aptos".
10. `conversas_para_segurar` sem seção casada usa a abstenção do 2º turno de 2022 do município (seções
    casadas); se o município também não tiver, a da UF.

## Perfil do eleitorado

11. **Só o Acre tem perfil por seção.** O download das demais UFs devolve HTTP 429 desde 17:30 (ver
    `data/raw/tse_eleitorado/perfil_eleitor_secao/download.log`); as outras 26 UFs e o exterior usam o
    perfil por zona. Na zona, os shares da zona são aplicados aos aptos de cada local e de cada seção
    (pseudo-contagem), e `perfil_fonte = "zona"`. Quando os arquivos chegarem, basta rodar o build de novo:
    o motor usa o arquivo por seção de toda UF que estiver íntegra.
12. Categorias "NÃO INFORMADO" e idade "Inválida" saem do denominador de cada dimensão. Quem tem 15 anos no
    cadastro de julho completa 16 até a eleição e entra em `a16_24`.
13. O perfil é de julho de 2026; a seção é ligada ao local pelo cadastro de outubro. Seção do perfil que
    não existe mais no cadastro vai para o local que o próprio perfil declara, se ele estiver no universo.

## Renda (PNAD)

14. **O arquivo não traz `VD3004`.** A escolaridade usa `VD3006` (grupamento de anos de estudo, fundamental
    de 9 anos): 1 a 3 (até 8 anos) = `fund_inc`; 4 (9 a 11 anos) = `fund_med`; 5 (12 a 15 anos) =
    `med_sup_inc`; 6 (16 anos ou mais) = `superior`. Superior completo de curso curto (15 anos de estudo)
    cai em `med_sup_inc`.
15. **Preços de julho de 2026**, o mês mais recente do `ipca.csv` (outubro não existe ainda): coluna
    `VD5001..._202604` vezes 1,00811. Salário mínimo de 2026 conferido em `salario_minimo.csv`: R$ 1.621.
    Faixas: até R$ 3.242 inclusive, até R$ 8.105 inclusive, acima.
16. Local sem setor (sem coordenada) usa a linha da UF sem situação (`situacao = "total"`). Nenhuma célula
    UF × escolaridade × situação ficou abaixo de 30 observações (mínimo 34); a regra de substituição
    existe e fica no campo `usa` de `pnad_renda.json`, que também traz as linhas `total` e `BR`.
17. A mediana da mistura sai da soma das funções de distribuição (caixas de R$ 10), não da média das
    medianas, e é publicada arredondada a R$ 10.
18. Limite: a escolaridade do TSE é a declarada no alistamento e envelhece; onde o cadastro é antigo, a
    renda estimada fica para baixo.

## Voto esperado e recentragem

19. Voto por faixa: Flávio e Lula sobre os válidos de cada casa (sem `branco_nulo` e `indecisos`), média
    simples de Datafolha e Quaest de 03/10.
20. **Recentragem por UF** (pedido do coordenador em 07/10, depois do primeiro build; o contrato foi
    atualizado no parágrafo "Voto esperado pelo perfil"). Para cada UF, deslocamento aditivo que iguala a
    média do esperado, ponderada por válidos, à urna da própria UF, sobre os locais com renda estimada. As
    27 UFs conferem dentro de 0,05 pp. A média nacional fecha com a urna dos locais no Brasil (47,0377) e
    fica a 0,0098 pp da urna com exterior (47,0278). Com o deslocamento nacional único (versão anterior,
    Flávio +3,691 pp, Lula −0,407 pp), o vão médio era Nordeste +13,20 pp e Sul −10,87 pp: o vão media
    região, não vizinhança. A tabela por UF está em `indice.json.parametros.recentragem.por_uf` e no
    relatório.
21. A seção recebe o mesmo deslocamento do local; o esperado da seção usa a escolaridade da própria seção e
    a situação do setor do local.
22. Como a recentragem é por UF, a amostra (`--uf`) já sai com a conta exata da UF; não há mais
    recentragem provisória nem cache dela.

## Índice e arquétipos

23. **Componente sem dado entra como zero no potencial e fica `null` no campo**: `c_reencontro` sem 2022
    casado; `c_perfil` no exterior (sem PNAD), onde o índice usa só os outros três componentes.
24. **O teto de 40 é menor que o observado no topo**: com a recentragem por UF, p99 do potencial = 44,78 e
    p95 = 36,70; 2.593 locais (2,8%) ficam com índice 100 (eram 5.719 com o deslocamento nacional).
    Mantido como o contrato pede; o p99 está em `indice.json.parametros`. A coluna `percentil` (item 41)
    não satura.
25. **Efeito regional, antes e depois.** Com o deslocamento nacional, `c_perfil` médio era 10,70 no
    Nordeste e 0,90 no Sul, 3.842 dos 5.719 locais saturados eram nordestinos e o índice médio do arquétipo
    `muro` era 86,2, o maior de todos. Com a recentragem por UF, o vão médio de cada região é zero,
    `c_perfil` médio fica entre 2,55 (Centro-Oeste) e 4,05 (Norte), o Nordeste tem 46 locais saturados e o
    índice médio do `muro` cai para 65,0 (`fortaleza` 46,9; `reencontro` 81,6, o maior). O `muro` continua
    acima da média porque abstenção, brancos e nulos também pesam lá. `abaixo_do_perfil` caiu de 6.701
    para 3.543 locais.
26. As regras de arquétipo leem os valores publicados (uma casa), para o número mostrado e o rótulo nunca se
    contradizerem; `fertil` usa `bn_v` (brancos e nulos sobre válidos).
27. **Arquétipo secundário ignora `frente` e `atras`**, que são o resto: com eles, toda Fortaleza teria
    "Na frente" como secundário e o "ou null" do contrato nunca aconteceria.
28. Conta do 2º turno: `flavio_2t = flavio + 0,427 × terceira`, `lula_2t = lula + 0,273 × terceira`
    (30% sem escolha; 61/39 entre quem escolhe). `faltam` é o menor inteiro que põe Flávio à frente
    (empate exato pede 1); `conversas_para_virar` = faltam / 0,35 arredondado para cima e `null` quando
    faltam = 0; `conversas_para_segurar` é `null` quando faltam > 0.

## Seções, exterior e pequenos grupos

29. **Seção com menos de 30 aptos** (71 no país) sai na camada `zona/` só com `secao`, `local_id`,
    `mun_tse`, `local`, `bairro`, `aptos`, `agregadas` e `coord_fonte`; votos, 2022, perfil, índice e
    percentis ficam `null`. O perfil também sai, porque escolaridade e idade de um grupo de 20 pessoas são
    tão pequenas quanto o voto.
30. **Exterior**: 186 cidades no cadastro do TSE, 146 com boletim (as outras 40 só têm seções não
    instaladas e não geram `mun/ZZ/*.json`); 171 locais, 1.310 seções principais, zona única 1. Coordenada
    da cidade (`exterior_cidades.json`) para todos os locais dela, `coord_fonte = "cidade"`; malha =
    `mundo.geojson`; sem CEP.

## Saída

31. Colunas acrescentadas ao contrato, sempre **no fim** das listas e na mesma ordem nas duas camadas:
    `em_aberto`, `bna`, `viravel`, `cury`, `renan`, `caiado`, `zema`, `outros_nominais`, `coord_fonte`,
    `percentil`, `percentil_uf`.
    `indice.municipios`: `coord_fonte`, `pais` (ISO do país no exterior) e `nome_tse` (nome do TSE quando
    difere do exibido, para a busca achar "Boa Saúde" e "Assú"). O `mun/*.json` ganha `pais` no topo.
32. **Totais de município, UF e país**: contagens somadas e taxas recalculadas sobre a soma; componentes do
    potencial são a soma dos votos endereçáveis de cada local por 100 aptos (o saldo de um local não
    cancela o de outro); `reencontro_a` ponderado por aptos e `vao_perfil_pp`/esperado por válidos; renda
    pela mistura das células com peso aptos × escolaridade. `votos_em_aberto`, `em_aberto`,
    `em_aberto_por_origem`, `locais_viraveis_*`, `locais_com_boletim` e `secoes_com_boletim` entram em
    todos os totais. `viravel` usa só `bna` (brancos + nulos + abstenção, sem a terceira via) e `>=`, como
    pedido; empate não é virada. Nacional: 20.701 locais viráveis para Flávio (40,1 milhões de aptos) e
    27.294 para Lula.
33. Nome do município: o do IBGE (agregados do Censo 2022). O arquivo do IBGE traz "Unas" para 2932507,
    cujo distrito-sede e o TSE dizem "Una": quando só o distrito-sede bate com o TSE, vale o distrito-sede
    (o único caso). Boa Esperança do Norte (MT) não está nos agregados e usa o nome do TSE em caixa normal.
34. Coordenada do município em `indice.municipios`: média das coordenadas dos locais ponderada por aptos
    (centro do eleitorado). Os 620 locais do Brasil sem coordenada no cadastro ficam com `lat`, `lon`,
    `coord_fonte` e setor `null`.
35. Nome, endereço e bairro do local ficam como no cadastro do TSE (maiúsculas): converter siglas de escola
    ("EMEF", "CIEP") por regra erraria mais do que acertaria.
36. `municipios_mais_disputados`: até 10 municípios com pelo menos 5 mil aptos e menor `|margem_v|`.
    `ranking_indice`: desempate por potencial e aptos.
37. Agregados do Censo por setor (pessoas, domicílios) não entram: a lista de colunas do local não os
    tem; o arquivo de agregados é usado só para o nome do município.
38. `indice.json` tem 689 KB (o contrato estimava 500 KB): 5.717 municípios × 14 colunas, 45 fontes com
    hash e a tabela de recentragem por UF.
39. `--uf` mescla: mantém em `indice.json` e em `cep/` as entradas das UFs não refeitas e o `nacional` do
    último build completo. O hash de `apuracao/data/apuracao.sqlite` é do arquivo principal no instante do
    build (o banco está em uso, com WAL).
40. Setor censitário: ponto a ponto pelo R-tree do GeoPackage, 0,12 ms por ponto (95 mil pontos em
    segundos), sem índice em memória. Ponto na divisa fica com o menor geocódigo; `CD_SIT` 9 (massa d'água)
    vira `null`. 93.464 dos 93.473 locais com coordenada caíram num setor.
41. **`percentil` e `percentil_uf`** (pedido do coordenador): parcela dos outros locais do Brasil com
    potencial estritamente menor, de 0 a 100, arredondada para baixo (100 = maior potencial do país;
    empates ficam iguais), para "mais voto em disputa que X% dos locais" nunca exagerar. A seção compara
    com as seções do Brasil com 30 aptos ou mais. O exterior tem `percentil = null` (o potencial dele não
    tem o componente de renda e não é comparável ao do país) e `percentil_uf` entre os locais do
    exterior. Em `--uf`, os dois percentis se referem ao escopo processado; só o build nacional produz o
    percentil do país.

## Aplicativo (registro do agente do app; não muda o contrato)

A1. **`mun_tse` com ou sem zero à esquerda**: o app compara o código do município pelo valor numérico e
    sempre usa a coluna `arquivo` do índice para achar `mun/<UF>/<mun_tse>.json`.
A2. **Escala dos shares**: perfil e renda em %; grupo que somar até 1,5 é multiplicado por 100. `masc` = 100 − `fem`.
A3. **CEP**: além de `exato` e `prefixo5`, tenta os prefixos de 5 dígitos mais próximos com os mesmos 4 e
    depois 3 primeiros dígitos, sempre com o aviso "aproximação grossa".
A4. **Texto com chave ausente**: a frase que contém a chave sem valor sai inteira; o app nunca mostra
    `undefined`, `NaN` ou `{chave}`. Chave ausente de `textos.json` cai em rótulo mínimo do app.
A5. **Card**: rodapé com as duas linhas pedidas ("brasil.arvor.co/politizesuavizinhanca.html" e "o voto é
    secreto: leitura agregada por seção, TSE"); `pagina.card_rodape` aparece na página sob os botões. Frase
    escolhida por hash do `local_id`; pula modelo com chave vazia e o que cita `{faltam}` quando `faltam = 0`.
A6. **`?dados=` e `?textos=`** só em localhost, `.localhost` e `.test`, só com caminho relativo do site.
A7. **Entrada por seção**: primeira aba; zona validada contra `indice.json.zonas`; seção agregada resolve
    para a principal com aviso; URL `#s=UF-zona-secao` (guarda a seção digitada) ou `#l=<local_id>`.
A8. **Exterior** sem coordenada: sem mapa; "ao redor" fica no mesmo município, por aptos.
A9. **file://**: módulo ES não roda; o aviso é um script clássico inline que desabilita a busca.
A10. **Paridade com o site de referência**: manchete do hero (`locais_viraveis_flavio` e `votos_em_aberto`,
    com "no Brasil" trocado pelos estados de `escopo` quando parcial); quadro nos dois sentidos no método
    (viráveis para Flávio e para Lula, com aptos); "Num raio de 1 km"; "ao redor" = 7 mais próximos
    reordenados por índice, desempate pela distância, distância em passos de 50 m; selo do local; visão
    "por bairro" calculada no cliente; botão WhatsApp; abstenção de 2022 ao lado da de 2026. Fora, por
    decisão: contador (exige servidor) e tiles.
A11. **Local virável (decisão do coordenador, 07/10)**: `viravel` = só branco + nulo + abstenção (`bna`) >=
    diferença. O app confia na coluna `viravel` só quando a linha traz `bna` (build com a regra nova); sem
    `bna`, refaz `bna` e `viravel` no cliente pela regra nova. Conferido em 9 locais do AC (3 Flávio, 3
    Lula, 3 nenhum) contra a conta em Python. O número nacional do hero vem do `indice.json` e só fica na
    regra nova quando o motor regravar.
A12. **Fixture** em `analysis/politize/fixture/` (`gera_fixture.py`, lint zero): Rio Branco com seis locais
    e doze seções inventados (152 agregada à 121), já com `bna` e a regra nova.

## Propostas de Flávio (08/10/2026)

A13. **Fonte do programa: espelho do Poder360, não o original do TSE.** A API do DivulgaCandContas
    (`.../candidatura/buscar/2026/BR/6257/candidato/280002551544`) e todos os hosts do TSE devolveram
    HTTP 429 por mais de 15 minutos. Com autorização do coordenador, o PDF veio de
    `static.poder360.com.br/uploads/2026/08/plano-flavio.pdf` (1.979.673 bytes, 76 páginas, SHA-256
    `a65ece32fba45e2bd13ca4f799872a8e78a492e16b5375fcd0e3756f4b77e5a4`, texto nativo, sem OCR). O arquivo
    foi criado em 18/08/2026 por PDFium, ou seja, é impressão do PDF, não o arquivo protocolado. `fonte.json`
    e `propostas.json` levam `espelho: true`, `conferido_com_tse: false` e a nota "espelho do PDF registrado
    no TSE, não conferido contra o original; comparar o hash quando o TSE voltar a responder". Quando o TSE
    responder, `python3 scripts/politize-propostas.py --conferir-tse` baixa o original e compara o hash
    (pode divergir só por impressão; nesse caso conferir o texto página a página).
A14. **Citação sai do PDF, nunca digitada.** A curadoria (`analysis/politize/propostas_curadoria.json`) guarda
    página e as palavras de abertura e fecho de cada trecho; o script extrai o intervalo literal com espaços
    colapsados. Reticências só nas pontas, quando o corte cai no meio da frase. Falhas de grafia do próprio
    programa ficam como estão (ex.: "na todos os dias", p. 33). `pagina` é o índice da página do PDF, que
    coincide com o número impresso. O script falha se título tiver fora de 4 a 6 palavras, trecho fora de
    120 a 450 caracteres, tema fora de 3 a 8 citações ou trecho ausente da página.
A15. **Travessão dentro de citação literal é permitido** (é citação). Nesta versão nenhuma citação o contém:
    as âncoras foram escolhidas para evitar os trechos do PDF que usam `—`. Resumo e título nunca o levam, e
    o verificador reprova.
A16. **Os 16 temas obrigatórios existem no programa** (`temas_ausentes` vazio). "Salário" não tem proposta
    própria (não há menção a salário mínimo); o tema Emprego cobre custo da carteira, contratos de primeiro
    emprego e 50+, negociado sobre legislado e trabalho por aplicativo. `problema_quaest` só casa com
    Segurança (Violência), Saúde, Educação, Corrupção, Infraestrutura, Enchentes e os três temas de Economia;
    os demais ficam `null`.
A13. **Conversas por origem** (`#conversas`): um `<details>` por chave de `textos.conversas_por_origem`; com
    boletim aberto, cada origem mostra os votos do local (abstenção = aptos − comparecimento; `bolsonaro_2022`
    = `reencontro_a` × aptos / 100 quando positivo, rotulado como saldo agregado) e a lista vem do maior para
    o menor; sem boletim, ordem fixa. Placeholders dos textos são interpolados; frase sem valor sai.
A14. **Propostas** (`#propostas`): `propostas.json` é buscado quando a seção de conversas chega perto da tela
    ou quando um boletim abre; sem arquivo ou sem temas, a seção fica oculta. O tema cujo `problema_quaest`
    casa com o problema do estado abre por padrão e o bloco "Sobre o que conversar" tem um botão que rola até
    ele sem mexer no `#s=`/`#l=`. O rodapé mostra título, páginas, link do documento, SHA-256 curto, data,
    link da página do TSE e a `nota` da fonte (espelho não conferido com o TSE). Antes de o arquivo existir,
    o navegador registra o 404 no console (aviso do próprio Chromium, não erro de script).
A15. **Exterior no mapa**: planisfério de `geo/ZZ.geojson` com um ponto por cidade do `indice.json` (azul
    Flávio à frente, vermelho Lula à frente, raio pelos aptos); toque abre a cidade. "Ao redor" no exterior
    usa as sete cidades mais próximas, sem limite de raio.
A16. **Percentil**: "Esta vizinhança tem mais voto em disputa que X% dos locais de votação do Brasil e que Y%
    dos {do/da/de estado}" sob a carta, com `percentil` e `percentil_uf`; sem as colunas, a frase não aparece.
    Preposição com artigo por estado (`deUF`/`emUF`: "do Rio de Janeiro", "da Bahia", "de São Paulo").
A17. **Peso dos arquivos**: `mun/SP/71072.json` tem 979 KB (279 KB com gzip, que o GitHub Pages aplica);
    `indice.json` 692 KB (206 KB gzip); `geo/SP.geojson` 310 KB (68 KB gzip). Abaixo do limite de 1,5 MB.
