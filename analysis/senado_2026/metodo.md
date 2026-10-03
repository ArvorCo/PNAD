# Predição do Senado 2027: método do motor

Reprodução: `python3 scripts/senado-2026-calibracao.py --skip-download` (calibração de 2022)
e `python3 scripts/senado-2026-motor.py` (grava `docs/assets/predicao_senado.json`). Código em
`scripts/senado_2026/`: `base.py` (leitura, nomes, média), `calibracao.py` (2022),
`motor.py` (sorteios), `senado.py` (composição de 2027) e `saida.py` (JSON e validação).
Testes: `pytest -q tests/test_predicao_senado.py`.

## O que o modelo responde

A probabilidade de cada candidatura terminar entre as duas mais votadas do estado em 04/10/2026,
e a distribuição das 81 cadeiras do Senado em 2027 por campo e por partido. Não é previsão de
votos: os intervalos de votos válidos servem para mostrar a incerteza, não como estimativa de
resultado.

## 1. Dados e média central

- Uma onda por casa e estado: a estimulada mais recente pela data de divulgação. Espontânea e
  onda sem candidaturas ficam fora, com o motivo em `pesquisas_descartadas`.
- Central: só ondas com fim do campo em 28/09/2026 ou depois. Onda sem campo publicado e
  divulgada a partir de 30/09 recebe campo inferido (fim = divulgação menos 1 dia, início =
  divulgação menos 3 dias, `campo_inferido: true`). Onda sem campo divulgada antes de 30/09 usa a
  divulgação como data e nunca entra na central.
- Estado sem onda recente: as ondas mais recentes de cada casa viram prior fraca
  (`cobertura: "antiga"`, `incerteza: "alta"`), com a deriva dos dias extras. Estado sem pesquisa
  alguma: `cobertura: "sem_pesquisa"` e nenhum nome entre os eleitos prováveis.
- Pergunta com dois nomes por eleitor (`votos_por_eleitor = 2`): todos os valores são divididos
  por 2 antes de combinar, e a média trabalha com a fração de menções.
- Candidatura retirada depois do prazo (tabela `RETIRADAS` em `base.py`, com a fonte): o voto
  medido passa a indeciso em toda onda usada, porque o voto nela é nulo em 04/10.
- Peso da casa h: w_h = 2^(-idade_h / 5), idade em dias entre o meio do campo e 03/10, pesos
  normalizados; nenhuma casa pesa mais por tamanho de amostra.
- Cada onda é fechada em 100 (candidaturas, outros, indecisos, branco e nulo). Válidos da casa:
  v_hi = c_hi / (soma das candidaturas + outros). Central: v_i = soma_h w_h v_hi. Indecisos (U) e
  branco e nulo (B) são médias entre as casas que os publicam.
- Nomes: casamento com o TSE por `casamento_nomes.json` e pelas tabelas de apelido de
  `scripts/senado_2026/tse.py`; a mesma pessoa com grafias diferentes entre casas vira uma só
  candidatura, e as variantes ficam em `aliases`. Na saída o nome é o de urna do TSE quando há
  casamento.

## 2. Indecisos

- Proporcional (central): os válidos são v_i.
- Uniforme (sensibilidade): v_i^u = (v_i (1 - U - B) + U e_i / m) / (1 - B), com e_i = 1 para os
  m nomes com ao menos 1 ponto. Branco e nulo nunca viram voto válido.
- Em cada sorteio um dos dois cenários é escolhido: proporcional com probabilidade 0,7, uniforme
  com 0,3 (`mistura_indecisos`). Nenhum cenário dá 100% dos indecisos a um nome.

## 3. Incerteza, em três partes

1. Amostral: por casa, Dirichlet com concentração n_h / deff sobre o vetor fechado, deff = 1,5
   (Kish com cerca de 6 entrevistas por setor e correlação intraclasse perto de 0,1, hipótese
   declarada). Onda sem n usa o menor n do acervo. As casas se combinam pelos pesos w_h.
2. Não amostral, logística-normal. Para a candidatura i do campo f no estado u:

   eta_i = log v_i + s_nac Z_f + s_uf Z_(u,f) + sqrt(s_idio^2 + tau^2 d_u) Z_i,
   p_i = exp(eta_i) / soma_j exp(eta_j),

   com Z normais padrão independentes; Z_f é o mesmo em todos os estados do sorteio (o erro que
   atinge um campo no país inteiro), Z_(u,f) é do campo dentro do estado e Z_i é da candidatura.
   `outros` entra nos válidos e nunca é eleito.
3. Deriva: passeio aleatório de variância tau^2 por dia entre o fim do campo (média ponderada,
   d_u dias) e 04/10.

Calibração (`analysis/senado_2026/calibracao_2022.json`): as últimas pesquisas de Senado de 2022
por estado, indexadas pelas páginas da Wikipédia em português (wikitext guardado em
`data/originals/senado_102026/wikipedia_2022/` com SHA-256 e hora de acesso), contra a urna do TSE
(`votacao_candidato_munzona_2022.zip`, cargo 5, 1º turno, soma de `QT_VOTOS_NOMINAIS_VALIDOS` por
`SQ_CANDIDATO`). Janela: fim do campo de 24/09 a 01/10/2022, uma onda por casa. Base principal:
Datafolha, Ipec e Quaest. Candidatura com votos anulados sai dos dois lados.

- Na rodada de 03/10/2026: 26 pesquisas em 19 estados. Erro por candidatura nos válidos: média
  absoluta 3,91 pontos, raiz do erro quadrático 5,88 (171 candidaturas). Entre candidaturas que
  fizeram de 20% a 40%: média absoluta 7,70 e raiz 9,09 (29). Na diferença entre 2º e 3º
  colocados da urna: média absoluta 11,09 e desvio 12,02 (26). As candidaturas de direita ficaram,
  em média, 3,15 pontos abaixo da urna.
- A variância não amostral no log é estimada entre candidaturas com ao menos 10% dos válidos: a
  soma dos quadrados de d_i = log(urna_i) - log(pesquisa_i), centrados dentro de cada pesquisa,
  dividida pelos graus de liberdade, menos a parte amostral (1 - 1/K) soma 1 / (n_ef c_i). Deu
  0,1647. A deriva tau^2 = 0,00145 por dia vem de 93 pares de ondas seguidas da mesma casa em
  setembro de 2022, líquida da amostragem; a deriva dos 2,5 dias médios entre as pesquisas finais
  e a urna de 2022 é descontada para não contar duas vezes.
- Divisão: s_nac^2 = 0,0631 (variância das médias por campo, descontado o ruído da média);
  o resto se divide meio a meio entre s_uf^2 e s_idio^2 (0,0490 cada). A divisão entre campo no
  estado e candidatura não é identificada em 2022 (5 pares do mesmo campo); é hipótese declarada.
- Escala declarada: candidatura em 30% dos válidos, numa corrida 30/25/20/10/8/7 com cada nome
  num campo, tem desvio de 9,1 pontos de erro não amostral (`parametros.escala_erro_pp`).
- O viés de 2022 não desloca a central: o efeito de campo entra simétrico, nas duas direções.
- Sem calibração com ao menos 15 estados, o motor usa a hipótese de 6 pontos para a candidatura em
  30% (`calibracao.HIPOTESE`) e marca `erro.fonte = "hipotese"`.

## 4. Monte Carlo

20 mil sorteios por estado, semente 20261004, gerador do numpy. O choque nacional por campo é
gerado uma vez e compartilhado entre os estados; cada estado tem gerador próprio semeado pela
posição da UF, o que deixa a sensibilidade comparar os mesmos sorteios. Em cada sorteio os dois
maiores p_i são os eleitos. Saídas: `p_eleito` (frequência entre os dois; soma 2,0 por estado),
`p_primeiro`, `ic90_validos` (quantis de 5% e 95% de p_i), as cinco duplas mais frequentes e
`p_dupla_mais_provavel`. Os eleitos prováveis são a dupla mais frequente; `dupla_empatada`
marca diferença menor que 2 pontos percentuais para a segunda dupla. Incerteza: alta quando a
cobertura não é recente ou a dupla sai em menos de 35% dos sorteios; média até 60%; baixa acima.

## 5. Senado de 2027

Em cada sorteio: os 27 eleitos de 2022 (`senadores_2022.json`) mais os 54 sorteados. Campo e
partido vêm do TSE quando o nome casa, senão da pesquisa. Campo é classificação editorial da
casa (`PARTIDO_CAMPO`): tucano é centro-esquerda; PSD, MDB e Avante, centro; União, PP, Podemos,
PRD, Agir e Mobiliza, centro-direita; PL, Novo, Republicanos, PRTB, DC, Democrata e Missão,
direita. Os 27 de 2022 são os eleitos na urna, não os titulares atuais: suplência, licença e
migração partidária ficam fora. Única exceção declarada: Cleitinho (MG), eleito pelo PSC,
incorporado ao Podemos em 2023, contado como direita e Republicanos (`CAMPO_EXCECAO_2022`).
Saídas por campo, por grupo (direita mais centro-direita, centro, esquerda mais centro-esquerda,
IC90 calculado nos sorteios do grupo) e por partido, e as probabilidades de 41, 49 e 54 cadeiras.
Estado sem pesquisa sorteia as duas vagas da distribuição de campos das vagas dos estados com
cobertura recente (hipótese neutra em `parametros.estados_sem_pesquisa`).

## 6. Validação gravada

Recomposição de cada onda contra `soma_total`, estados em que as casas discordam da dupla líder,
soma de `p_eleito`, fechamento em 81 em todo sorteio, apelidos e grafias, retiradas, campos e n
inferidos, a calibração de 2022 e duas sensibilidades com os mesmos sorteios: erro não amostral e
deriva com desvio dobrado, e indecisos 100% uniformes (duplas que mudam e somas por campo).

## O que o modelo não faz

- Não prevê votos; dá probabilidade de eleição sob uma escala de erro declarada.
- Não modela coligação, dobradinha, desistência nem transferência de voto entre candidaturas.
- Não usa o resultado de 2022 como prior de nome ou de partido; 2022 só calibra a escala do erro.
- Não corrige viés de instituto nem de campo; a média por recência dá o mesmo peso a todas as
  casas.
- Trata a fração de menções de 2026 com a escala de erro medida em 2022, quando cada eleitor
  votava em um nome só.
