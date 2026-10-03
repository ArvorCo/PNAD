# Erro das pesquisas no 1º turno presidencial de 2022

Memorando de 03/10/2026. Reprodução: `python3 scripts/predicao-2026-erro-2022.py`, que lê `pesquisas_2022.json` (transcrição manual, com arquivo e página de cada número) e o TSE, e grava `erro_2022.json`. Teste: `pytest -q tests/test_predicao_2026_erro_2022.py`.

Produto descritivo. Não é prognóstico e não ajusta a central de 2026.

## 1. Resultado oficial

Fonte rastreada: `analysis/voto_util/tse_2022_uf.json`, bloco `brasil_2022.t1`, SHA-256 `edda98f268c631f3883b19e97b4757fcfb28d0174d012b8b6e92524c92c000db`, copiado da API de resultados do TSE (eleição 544). O script confere o bloco contra o JSON bruto `data/raw/tse_resultados/api_2022/br-c0001-e000544-r.json` (SHA-256 `a87a25b7f7d7d5329e765c63cee49c30a160050efc4a19a0a5ad89f6e57d5d70`, totalização de 04/10/2022 10:27:34) e exige igualdade exata; confere também que as 27 UFs mais o exterior (`zz-c0001-e000544-r.json`) fecham o total do Brasil. As duas conferências passam.

| | Votos | % dos válidos |
|---|---:|---:|
| Lula | 57.259.504 | 48,43 |
| Bolsonaro | 51.072.345 | 43,20 |
| Simone Tebet | 4.915.423 | 4,16 |
| Ciro Gomes | 3.599.287 | 3,04 |
| Demais (7 nomes) | 1.383.160 | 1,17 |
| Válidos | 118.229.719 | |
| Brancos | 1.964.779 | 1,59% do comparecimento |
| Nulos | 3.487.874 | 2,82% do comparecimento |
| Comparecimento | 123.682.372 | 79,05% do eleitorado |
| Eleitorado apto | 156.454.011 | |

Diferença Lula menos Bolsonaro: 5,23 pontos. Sem o exterior a diferença muda na terceira casa decimal; o JSON guarda as duas versões e usa o total oficial.

## 2. Fontes arquivadas

Cada pasta em `data/originals/pesquisas_2022/<casa>/` tem os documentos e um `fonte.json` com URL, bytes, SHA-256, `creationDate` (quando PDF) e data de acesso. As páginas citadas estão renderizadas em `analysis/predicao_2026/erro_2022/renders/`.

| Casa | Registro | Campo (2022) | n | Documento | Nível |
|---|---|---|---:|---|---|
| Datafolha | BR-00245/2022 | 30/09 a 01/10 | 12.800 | matéria da Folha (contratante), HTML e captura | matéria do contratante |
| Ipec | BR-00999/2022 | 29/09 a 01/10 | 3.008 | CNN Brasil e infográfico do Poder360, concordantes | imprensa concordante |
| Quaest/Genial | BR-02444/2022 | 30/09 a 01/10 | 3.600 | PDF, p. 7 | PDF do instituto |
| AtlasIntel | BR-01318/2022 | 24/09 a 28/09 | 4.500 | PDF, pp. 7 e 8 | PDF do instituto |
| PoderData | BR-01426/2022 | 25/09 a 27/09 | 4.500 | infográficos do PoderData | infográfico do instituto |
| Paraná Pesquisas | BR-07917/2022 | 27/09 a 29/09 | 2.020 | PDF, p. 8 | PDF do instituto |
| CNT/MDA | BR-02944/2022 | 28/09 a 30/09 | 2.002 | PDF, pp. 8 e 9 | PDF do instituto |
| Ipespe/Abrapel | BR-05007/2022 | 30/09 | 1.100 | PDF, pp. 8 e 9 | PDF do instituto |
| FSB/BTG | BR-08123/2022 | 23/09 a 25/09 | 2.000 | PDF, pp. 12 e 16 | PDF do instituto |
| Modalmais/Futura | BR-06743/2022 | 26/09 a 28/09 | 2.000 | PDF (cópia do Wayback), pp. 9 e 10 | PDF do instituto |
| Ideia (Exame/Ideia) | BR-09782/2022 | 23/09 a 28/09 | 1.500 | PDF, p. 11 | PDF do instituto |
| Instituto Veritá | BR-05980/2022 | 24/09 a 29/09 | 51.169 | PDF, p. 6 | PDF do instituto |
| Gerp (fora da média) | BR-09102/2022 | 29/08 a 01/09 | 2.095 | PDF, p. 11 | PDF do instituto |
| Brasmarket (fora da média) | BR-08847/2022 | 26/09 a 28/09 | 1.600 | três matérias de imprensa | imprensa divergente |

Observações documentais:

- **Datafolha.** O PDF nacional da onda de 30/09 a 01/10 não foi localizado. O arquivo `Datafolha.pdf` que o Poder360 subiu em 01/10/2022 é o relatório de governador de Minas Gerais. Os números vêm da matéria da Folha, contratante. O infográfico do Poder360 da mesma onda inverte Tebet e Ciro (Ciro 6, Tebet 5) em relação à Folha (Tebet 6, Ciro 5); prevalece a Folha, que a versão em espanhol do jornal repete.
- **Ipec.** O domínio antigo do instituto não resolve e o atual devolve 403. Os números vêm de duas publicações independentes que concordam em todos os valores.
- **Quaest** publica só válidos.
- **Ideia e Veritá** não publicam válidos: os da Ideia saem dos totais e os do Veritá das contagens da p. 6, mais precisas que os percentuais. A tabela do Veritá omite Vera e Sofia Manzano, que somaram 0,06% dos válidos na urna.
- **Ipespe.** O PDF arquivado é a cópia que o Poder360 publicou, com metadado de repasse por WhatsApp.
- **Gerp** fica fora: o campo terminou em 01/09, um mês antes da urna, e a cartela ainda tinha Pablo Marçal e Roberto Jefferson.
- **Brasmarket** fica fora da média principal: não há documento do instituto nem do contratante e as matérias divergem entre si. Entra só na média ampliada de sensibilidade.

## 3. Erro por casa

Erro é pesquisa menos urna, em pontos dos válidos. Positivo superestima o candidato. Na coluna da diferença, positivo superestima a vantagem de Lula. A margem é a de 95% da diferença sob amostragem simples, sem efeito de desenho: é piso, não o intervalo real da casa.

| Casa | Válidos L × B | Lula | Bolsonaro | Tebet | Ciro | Demais | Diferença L−B | Erro absoluto médio | Margem AAS da diferença |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Datafolha | 50,0 × 36,0 | +1,57 | −7,20 | +1,84 | +1,96 | +1,83 | +8,77 | 2,88 | 1,6 |
| Ipec | 51,0 × 37,0 | +2,57 | −6,20 | +0,84 | +1,96 | +0,83 | +8,77 | 2,48 | 3,4 |
| Quaest/Genial | 49,0 × 38,0 | +0,57 | −5,20 | +0,84 | +2,96 | +0,83 | +5,77 | 2,08 | 3,0 |
| AtlasIntel | 50,7 × 41,0 | +2,27 | −2,20 | −1,56 | +0,56 | +0,93 | +4,47 | 1,50 | 2,8 |
| PoderData | 48,0 × 38,0 | −0,43 | −5,20 | +0,84 | +2,96 | +1,83 | +4,77 | 2,25 | 2,8 |
| Paraná Pesquisas | 47,1 × 40,0 | −1,33 | −3,20 | +2,14 | +2,16 | +0,23 | +1,87 | 1,81 | 4,2 |
| CNT/MDA | 48,3 × 39,7 | −0,13 | −3,50 | +0,54 | +1,86 | +1,23 | +3,37 | 1,45 | 4,3 |
| Ipespe/Abrapel | 49,0 × 35,0 | +0,57 | −8,20 | +2,84 | +4,96 | −0,17 | +8,77 | 3,35 | 5,5 |
| FSB/BTG | 48,0 × 37,0 | −0,43 | −6,20 | +0,84 | +4,96 | +0,83 | +5,77 | 2,65 | 4,1 |
| Modalmais/Futura | 43,6 × 40,5 | −4,83 | −2,70 | +3,54 | +2,96 | +1,03 | −2,13 | 3,01 | 4,2 |
| Ideia | 48,9 × 38,5 | +0,43 | −4,74 | +1,04 | +3,19 | +0,08 | +5,16 | 1,89 | 4,8 |
| Instituto Veritá | 42,6 × 45,7 | −5,81 | +2,50 | +0,15 | +1,16 | +2,01 | −8,31 | 2,32 | 0,8 |
| *Gerp (fora)* | 40,0 × 41,1 | −8,43 | −2,14 | +2,16 | +8,53 | −0,12 | −6,29 | 4,28 | 4,0 |
| *Brasmarket (fora)* | 34,7 × 51,0 | −13,75 | +7,76 | +1,68 | +3,91 | +0,40 | −21,51 | 5,50 | 4,7 |

Nas casas que publicam inteiros, a coluna "demais" é 100 menos os quatro principais e absorve o arredondamento; no Datafolha isso infla "demais" em cerca de um ponto. Datafolha, Ipec e Ipespe empatam em +8,77 porque os três publicaram uma diferença inteira de 14 pontos.

Melhor casa na diferença: Paraná Pesquisas (+1,87). Pior: Datafolha, Ipec e Ipespe empatados (+8,77); o script aponta o Datafolha por ordem de leitura, e a página deve citar os três. Pelo erro absoluto médio nos cinco grupos, a melhor é a CNT/MDA (1,45) e a pior a Ipespe (3,35).

## 4. Erro comum da média das casas

Média simples das 12 casas da média principal, contra a urna:

| | Média das casas | Urna | Erro comum | Desvio entre casas |
|---|---:|---:|---:|---:|
| Lula | 48,01 | 48,43 | −0,42 | 2,56 |
| Bolsonaro | 38,86 | 43,20 | −4,33 | 2,82 |
| Tebet | 5,32 | 4,16 | +1,16 | 1,32 |
| Ciro | 5,68 | 3,04 | +2,63 | 1,34 |
| Demais | 2,13 | 1,17 | +0,96 | 0,70 |
| Diferença L−B | 9,15 | 5,23 | **+3,92** | 4,96 |

- **O erro de 2022 não foi em Lula.** A média acertou Lula a menos de meio ponto. O erro esteve em Bolsonaro, subestimado por 11 das 12 casas (só o Veritá o superestimou), e em Ciro e Tebet, superestimados por quase todas. A leitura compatível com os dados é eleitor de terceira via e indeciso que terminou em Bolsonaro, por mudança tardia, por subdeclaração ou pelas duas coisas. Os dados não separam essas hipóteses.
- **Mediana dos erros na diferença: +4,96.** A média (+3,92) é puxada pelo Veritá (−8,31).
- **Sensibilidades:**

| Média | Casas | Erro na diferença | Mediana |
|---|---:|---:|---:|
| Principal | 12 | +3,92 | +4,96 |
| Só PDF do instituto | 9 | +2,75 | +4,47 |
| Sem o Veritá | 11 | +5,03 | +5,16 |
| Ampliada, com a Brasmarket | 13 | +1,96 | +4,77 |

O sinal é o mesmo em todas; o tamanho varia de 2 a 5 pontos conforme a regra de inclusão.

- **Componente próprio na diferença** (erro da casa menos erro comum), em pontos:
  - Datafolha, Ipec e Ipespe +4,85;
  - Quaest e FSB +1,85;
  - Ideia +1,24;
  - PoderData +0,85;
  - Atlas +0,55;
  - MDA −0,55;
  - Paraná −2,05;
  - Futura −6,05;
  - Veritá −12,23.

  O desvio entre casas (4,96) é maior que o erro comum: em 2022 o problema de cada casa variou mais do que o problema compartilhado.

## 5. Casas de 2022 que existem em 2026

Leitura de `docs/assets/predicao_2026_1T_presidente.json`, campo `nacional.efeitos_casa[casa].desvio_margem_pp`, sem edição. Positivo nas duas colunas significa mais Lula: em 2022, acima da urna; em 2026, acima da mediana das casas pareadas por época.

| 2022 | 2026 | Erro 2022 na diferença L−B | Desvio relativo 2026 L−F | Ondas 2026 |
|---|---|---:|---:|---:|
| Datafolha | Datafolha | +8,77 | −0,48 | 5 |
| Quaest/Genial | Quaest | +5,77 | +2,64 | 5 |
| AtlasIntel | AtlasIntel | +4,47 | −1,02 | 3 |
| PoderData | PoderData | +4,77 | −1,52 | 1 |
| CNT/MDA | MDA | +3,37 | +4,91 | 2 |
| FSB/BTG | Nexus (mesmo grupo) | +5,77 | −0,08 | 5 |
| Modalmais/Futura | Futura | −2,13 | −6,40 | 2 |
| Ideia | Meio/Ideia | +5,16 | −2,65 | 1 |

Quem mais superestimou Lula em 2022 (Datafolha) está hoje perto da mediana das casas. A única casa abaixo da urna entre as que seguem ativas (Futura) é hoje a mais distante para o lado de Flávio. O desvio relativo de 2026 não é erro: mede distância às outras casas, não à urna. A marca pode ter trocado de método, equipe ou dono (FSB/BTG para Nexus, Exame/Ideia para Meio/Ideia). Os números de 2026 vão mudar com a central em revisão; o script os relê a cada execução.

## 6. O que se pode e o que não se pode concluir

Pode-se dizer:

- Em 2022 a média das últimas pesquisas superestimou a vantagem de Lula no 1º turno em cerca de 4 pontos nos válidos.
- O erro esteve em Bolsonaro, não em Lula.
- O sinal sobrevive às quatro regras de inclusão testadas.
- Em 10 das 12 casas a diferença publicada ficou acima da urna, e em 8 delas o erro excede a margem de amostragem simples da diferença.

Não se pode dizer:

- **Que o erro vai se repetir em 2026, nem com que tamanho.** Uma eleição é um ponto: não há variância estimável do erro comum. Cartela, polarização, institutos, métodos e eleitorado são outros.
- **Que as casas erraram por viés de medição.** Nove das doze ondas encerraram o campo antes de 1º de outubro; parte do erro pode ser movimento real de última hora, inclusive voto útil em Bolsonaro vindo de Ciro e Tebet, e o desenho não separa as duas coisas.
- **Que uma casa é confiável ou não com base numa onda.** O ranking de 2022 mistura qualidade de método com data de campo e com arredondamento.
- **Que o desvio relativo de 2026 confirma ou contradiz o erro de 2022.** Ele não é medido contra urna.

## 7. Sugestão de texto para a página

> Em 2022, a média das últimas pesquisas de doze institutos antes do 1º turno deu a Lula 9,2 pontos de vantagem sobre Bolsonaro nos votos válidos. A urna deu 5,2. O erro não esteve em Lula, que as pesquisas acertaram a menos de meio ponto, e sim em Bolsonaro, subestimado por 11 das 12 casas, enquanto Ciro e Tebet foram superestimados. Não sabemos quanto disso foi eleitor que mudou de voto nos últimos dias e quanto foi viés de medição.
>
> A título de sensibilidade, e não de previsão: se o erro médio de 2022 se repetisse, a diferença de Flávio sobre Lula seria cerca de 4 pontos maior do que a central desta página; se o erro corresse no sentido oposto, seria 4 pontos menor. Uma eleição só não permite dizer qual das duas, nem se alguma, vai acontecer. Em 2022 o erro de cada instituto variou mais do que o erro comum a todos eles (de −8 a +9 pontos na diferença).

O número exato a usar vem de `erro_2022.json`, em `aplicacao_2026`: `deslocamentos_pp_em_flavio_menos_lula` dá +3,92 (repetição) e −3,92 (direção oposta). Aplicar à central fica a cargo do responsável pela previsão.

## 8. Casas não arquivadas

- **Real Time Big Data.** Nenhuma pesquisa nacional de 1º turno presidencial em 2022 localizada. A biblioteca de mídia do Poder360 só traz estaduais da casa, e as tabelas da Wikipédia em inglês e em português só listam uma nacional de março de 2021. A ausência não está provada.
- **Equilíbrio Brasil.** Aparece em índice secundário com campo de 20 a 22/09/2022; o documento não foi procurado.
- **XP/Ipespe.** A série não foi procurada; a onda do Ipespe arquivada é a parceria com a Abrapel.
- **Vox Populi, Datatempo e Ipri.** Não aparecem nos índices consultados para setembro de 2022; sem busca dedicada.
- **2018.** As pesquisas finais de 2018 não foram arquivadas nesta rodada, e por isso não há conta de 2018.

Caminhos que funcionaram, para a próxima rodada:

- A biblioteca de mídia do Poder360 por API (`wp-json/wp/v2/media?mime_type=application/pdf&after=...&before=...`) lista os PDFs que o veículo subiu em cada dia.
- A matéria-resumo do Poder360 de 02/10/2022 (arquivada em `data/originals/pesquisas_2022/poder360_indice/`) dá registro, n e campo de nove casas.

O Wayback Machine esteve fora do ar durante parte da coleta.

## 9. CI

Os PDFs ficam no Git LFS (`*.pdf` em `.gitattributes`). O passo `git lfs pull --include=...` do `.github/workflows/ci.yml` não inclui `data/originals/pesquisas_2022/**`. Sem esse acréscimo, o teste de SHA-256 dos PDFs é pulado no CI (o teste reconhece o ponteiro do LFS) e só roda localmente. As imagens e HTML não usam LFS e são conferidos sempre.
