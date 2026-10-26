# Anomalia por mistura gaussiana nos dois turnos (seções do Brasil): contrato

Pedido do Leonardo (26/10/2026, noite): análise de anomalia por aprendizado não supervisionado
sobre as seções, usando os votos do 1º e do 2º turno em frações do eleitorado (Flávio/aptos,
Lula/aptos, comparecimento/aptos, brancos/aptos, nulos/aptos, outros candidatos/aptos), com
escolha declarada do número de grupos, iteração até a convergência, gráficos como os do 1º
turno e o grupo mais atípico transformado em sinal extra no dossiê, no Politize-se e no mapa
do Brasil. **Exterior fica fora** (abstenção muito acima da média formaria um grupo só com
essas urnas). Rótulo fixo em todo lugar: **atipicidade estatística não é irregularidade; o
grupo pede explicação, não prova nada.**

Reprodução, nesta ordem (depois de `apuracao-2t-2026-secoes.py --fonte completo`):
`python3 scripts/apuracao-2t-2026-anomalia.py` (motor; `--amostra N` para rascunho),
`python3 scripts/politize-se-build.py`, `python3 scripts/politize-se-mapa-build.py`,
`python3 scripts/apuracao-2t-2026-hipoteses.py`, `python3 scripts/video-apuracao-2t-dados.py`,
`python3 scripts/apuracao-2t-2026-build.py`, `python3 scripts/apuracao-2t-2026-thread.py --png`.

## 1. Universo e fonte

- Bancos de BUs por seção dos dois turnos, somente leitura: `apuracao/data/secoes_2026.sqlite`
  (1T) e `apuracao/data/secoes_2t_2026.sqlite` (2T); tabelas `bu` (aptos, comparecimento,
  modelo_urna, tipo_arquivo, tipo_urna, hab_*) e `voto_secao` (cargo 1; tipo 1 nominal com
  `numero`, 2 branco, 3 nulo). A UF está em minúsculas nos bancos (`ac`); no JSON e nas
  saídas, maiúsculas. Leitor pronto: `scripts/politize_se/fontes.bu(banco, uf)` devolve por
  (zona, seção) aptos, comparecimento, flavio, lula, brancos, nulos, outros e o resto do BU;
  `scripts/apuracao_2t_2026/urnas_base.ler` lê o banco inteiro (só Lula e Flávio). O motor
  pode ler direto com SQL em streaming por UF.
- Chave: (uf, mun, zona, secao). Entram as seções com BU nos dois turnos, `uf != 'zz'` e
  aptos ≥ 30 em ambos (497.796 seções em 26/10). As excluídas são contadas em
  `universo.excluidas` por motivo (exterior 1.310; sem par; aptos < 30).
- Aptos de cada turno é o denominador do próprio turno (`bu.aptos`, eleição federal).

## 2. Espaço de features

Frações do eleitorado por turno, em pontos percentuais antes da padronização:

| chave | definição |
|---|---|
| `lula1`, `flavio1`, `outros1`, `brancos1`, `nulos1` | votos / aptos do 1T |
| `lula2`, `flavio2`, `brancos2`, `nulos2` | votos / aptos do 2T |

Nove colunas. Abstenção e comparecimento entram implícitos: `comp1 = lula1 + flavio1 +
outros1 + brancos1 + nulos1` e `comp2 = lula2 + flavio2 + brancos2 + nulos2` (conferir contra
`bu.comparecimento`; a diferença, se houver, é registrada em `universo.comparecimento_divergente`
e não muda as features). Incluir `comp` como décima coluna deixaria a matriz de covariância
singular, porque é combinação linear exata das outras.

**Enquadramento por diferença é equivalente, e o JSON diz isso.** A mistura gaussiana com
covariância completa é invariante a transformações afins invertíveis: trocar as quatro colunas
do 2T por `delta_lula = lula2 - lula1` etc. muda só a parametrização, não a log-verossimilhança
nem a partição. O motor ajusta nos níveis padronizados (média zero e desvio um entre seções,
como no 1T) e **publica os centros também em diferenças** (`centro_delta_pp`: Δcomp, Δlula,
ΔFlávio, Δbrancos, Δnulos, e `terceira1_pp` = outros1), porque é como o leitor entende. O
k-means, que não é invariante, roda nos dois enquadramentos como contraste (seção 4).

## 3. Mistura gaussiana: ajuste e número de grupos

- `sklearn.mixture.GaussianMixture(covariance_type="full", reg_covar=1e-6, tol=1e-6,
  max_iter=2000)`; 8 sementes × duas inicializações (`kmeans`, `k-means++`), como no 1T
  (`scripts/apuracao_2026/secoes_clusters_motor.py`: reaproveitar por import `amostra_estratificada`,
  `ajustar_melhor`, `convergencia` de `secoes_clusters_diag`, `escolher_anomalo`,
  `mahalanobis_proprio`, `cramer`, sem editar os módulos do 1T).
- Escolha de k: BIC para k = 2..10 numa amostra estratificada por UF de 120.000 seções
  (semente 20261026), uma partida por semente; em `bic` cada linha traz k, BIC, ICL (BIC
  mais a entropia das responsabilidades, que penaliza grupos sobrepostos), log-verossimilhança
  média, iterações e convergência. **Regra declarada**: k* é o menor k em que a queda do BIC
  do passo seguinte fica abaixo de 5% da queda total de k = 2 até k = 10 (o "joelho"); se a
  curva não tiver joelho, k* = argmin do ICL. O JSON guarda `k_escolhido`, `regra` e os dois
  candidatos (`k_joelho_bic`, `k_min_icl`). k* nunca passa de 10 nem fica abaixo de 3.
- Com k*: ajuste na base inteira (497.796) com as mesmas sementes e inicializações; a melhor
  partida é a de maior log-verossimilhança; em seguida `convergencia()` aperta tolerância e
  confere o índice de Rand ajustado entre as partidas, como no 1T. `ajuste` publica
  `convergiu` (obrigatoriamente `true`), `iteracoes`, `sementes_no_maximo`, `tol`, `max_iter`
  e o diagnóstico. **Se alguma partida não convergir, o motor repete com `max_iter` dobrado
  antes de falhar**; nunca publica partida não convergida como escolhida.
- Ordem dos grupos: por `lula2` médio crescente (estável entre sementes), ids 0..k-1.

## 4. k-means (contraste)

`sklearn.cluster.KMeans(n_init=10, max_iter=1000, tol=1e-6, random_state=20261026)` para
k = 2..10 em dois enquadramentos sobre as mesmas seções padronizadas: `niveis` (as nove
colunas) e `niveis_e_deltas` (cinco do 1T mais Δlula, ΔFlávio, Δbrancos, Δnulos). Para cada
k: inércia, silhueta média numa amostra de 20.000 seções, `n_iter_` e `convergiu`
(`n_iter_ < max_iter`). Índice de Rand ajustado entre a partição do k-means (k = k*) e a da
mistura. Publicado como contraste: a mistura é o modelo principal.

## 5. Grupo mais atípico e sinal por seção

- Critério do 1T (`escolher_anomalo`): soma dos postos de menor log-verossimilhança média e
  de maior dispersão (log-determinante da covariância); empate pela menor log-verossimilhança.
  Publicar também o segundo colocado e a diferença, para o leitor ver se a escolha é folgada.
- **Sinal `anomalia_ml`** por seção: pertence ao grupo mais atípico (responsabilidade máxima
  nesse grupo). Também sai `anomalia_ml_score`: log-densidade da mistura na seção
  (`score_samples`), e `anomalia_ml_p` = parcela das seções do país com densidade menor
  (0 a 1; 0,01 = entre as 1% menos prováveis). O sinal binário é o que entra no Politize-se e
  no mapa; o score fica na ficha.
- O grupo atípico é descrito por: centros (frações do eleitorado nos dois turnos e deltas),
  tamanho, aptos médio, UFs e regiões (com `pct_da_uf`), modelo da urna, cruzamento com os
  sinais existentes (`escore` 0..6 de `secoes_sinais`, `tipo_arquivo` ≥ 3, contingência,
  mudança de local), abstenção média 1T e 2T, e **voto**: fatia de Flávio entre os dois no 2T
  contra as vizinhas do mesmo município e diferença em diferenças contra o 1T, reaproveitando
  `scripts/apuracao_2t_2026/secoes_voto.py` (`comparar` ou equivalente), com IC 95% por
  bootstrap de 2.000 reamostragens. Publicar o resultado seja qual for o sinal.
- 50 amostras do grupo atípico (menor log-verossimilhança) com uf, município (nome pelo
  catálogo do Politize-se, `docs/assets/politize/dados/mun/<UF>/<mun>.json`, ou o código),
  zona, seção, aptos 1T e 2T, comparecimento 1T e 2T, Lula e Flávio por turno, brancos e
  nulos, modelo, `escore`, e a explicação provável pela régua de `secoes_ranking.explicar`
  quando houver; `link` para o Politize-se (`politizese.html#uf=XX&zona=Z&secao=S`).

## 6. Saídas

### `analysis/apuracao_2t_2026/dados/anomalia_ml.json` (compacto, no git)

```
gerado_em, rotulo, fonte {banco_1t, banco_2t, sha256 de cada, secoes_json_sha256},
universo {secoes, excluidas {exterior, sem_par, aptos_menor_30, outros}, comparecimento_divergente},
features {colunas: [...9], unidade: "pct do eleitorado", padronizacao {media, desvio} por coluna,
          equivalencia_afim: texto},
bic [{k, bic, icl, loglik_media, iteracoes, convergiu}], k_escolhido, k_joelho_bic, k_min_icl, regra,
ajuste {covariancia, n_init, inits, sementes:[...], random_state, init, convergiu, iteracoes,
        sementes_no_maximo, tol, max_iter, reg_covar, loglik_media, segundos, diagnostico_convergencia},
kmeans {niveis: [{k, inercia, silhueta, iteracoes, convergiu}], niveis_e_deltas: [...],
        ari_com_mistura_k_estrela {niveis, niveis_e_deltas}},
componentes [{id, secoes, pct_secoes, aptos, aptos_medio, peso,
              centro_pct_eleitorado {9 chaves}, centro_delta_pp {comp, lula, flavio, brancos, nulos},
              comp1_pct, comp2_pct, abst1_pct, abst2_pct, fatia_f1, fatia_f2,
              dispersao_logdet, loglik_media, loglik_p05, mahalanobis_mediana,
              ufs_top [{uf, secoes, pct_do_cluster, pct_da_uf}], regioes [...], modelo_urna [...],
              sinais {escore_1_mais_pct, escore_2_mais_pct, papel_pct, contingencia_pct, mudanca_pct},
              rotulo (frase curta gerada por regra: o que distingue o centro do país)}],
mais_anomalo {id, criterio, segundo {id, diferenca_postos}, voto {fatia_f2_vs_vizinhas_pp, ic95,
              did_vs_1t_pp, ic95, n, n_vizinhas}, amostras [...50]},
menos_provaveis [...50 seções de menor densidade no país, com grupo],
cluster_regiao [...], cluster_uf [...], cluster_modelo [...], cramer_v_regiao, cramer_v_uf,
cramer_v_modelo,
pca {colunas: [x, y, cluster, top, uf, ...], pontos: [[...]], variancia_explicada: [v1, v2],
     elipses: [{cluster, cx, cy, rx, ry, ang}]}   # amostra estratificada de 8.000 pontos + as 300 menos prováveis
secoes_arquivo {arquivo, sha256, bytes, n_linhas, colunas}   # ponteiro para o arquivo pesado
```

### `data/outputs/apuracao_2t_2026/anomalia_secoes.json.gz` (pesado, fora do git)

Mesma convenção de `secoes_linhas.py` (`gravar`, `bloco`, `exigir`): `{"colunas": [uf, mun,
zona, secao, grupo, score, p, anomalo], "linhas": [...]}`, gzip com `mtime=0`. `uf` em
maiúsculas, `mun` com cinco dígitos, `grupo` 0..k-1, `score` com 3 casas, `p` com 4 casas,
`anomalo` 0/1. Quem consome: Politize-se (`politize_se/fontes.anomalia_ml(uf)`), mapa (via os
arquivos do Politize-se) e o capítulo do dossiê (só para a figura de mapa, por amostra; sem o
arquivo, a figura mostra o aviso padrão e o capítulo renderiza o resto).

### `analysis/apuracao_2t_2026/dados/anomalia_ml.md`

Memorando com os mesmos números: universo, k e por quê, convergência, os grupos em uma linha
cada, o atípico com voto e cruzamentos, e os limites.

## 7. Politize-se e mapa

- `politize_se/fontes.anomalia_ml(uf) -> dict[(zona, secao), (grupo, score, p, anomalo)]`
  lê o arquivo pesado; ausente, devolve `{}` e `indice.anomalia_ml.disponivel = false`.
- Por seção (`saida.COLUNAS_SECAO`): `ml_grupo` (int ou null), `ml_anomalo` (bool ou null),
  `ml_p` (0 a 1, 4 casas, ou null). `indice.catalogos.ml` traz `k`, os rótulos por grupo e o
  id do grupo atípico; `indice.anomalia_ml` traz `disponivel`, `secoes`, `anomalas`, `gerado_em`.
- Por prédio e por município (`somar`): `secoes_anomalas` (contagem). Entra em
  `saida.CAMPOS_LOCAL`, `COLUNAS_MUNICIPIOS` e `mapa_dados.COLUNAS_LOCAIS`.
- Camada do mapa `anomalia`: tipo `presenca`, campo `secoes_anomalas`, nome "Grupo atípico
  (estatística)", explicação com o rótulo da casa e a frase de que o grupo foi definido por
  mistura gaussiana sobre as frações do eleitorado nos dois turnos, sem o exterior.
  `precisa_bu2: true`. Cor em `docs/assets/politize_se_mapa/app.js` (`COR.anomalia`, par
  neutro → `#6b4a92`), `TETO_PARCELA.anomalia = 0.25`, coluna na lista.
- App do Politize-se (`docs/assets/politize_se/app.js`): caixa "Grupo estatístico" depois da
  caixa de sinais, com o grupo (rótulo do catálogo), a densidade em palavras ("entre as 1% menos
  prováveis do país" quando `ml_p` < 0,01; "fora do grupo atípico" quando `ml_anomalo` falso),
  o rótulo da casa e, no cartão compartilhável, um selo "grupo atípico" quando `ml_anomalo`.
  A frase gerada (`textos.py`) ganha o caso. Sem JS tudo continua legível.
- Registrar em `analysis/politize_se/CONTRATO.md` (seções de colunas, camadas e "Mudanças de
  esquema") e atualizar `tests/test_politize_se.py` e `tests/test_politize_se_mapa.py`
  (contrato das camadas, colunas). Jargão fora da interface: nunca "GMM", "cluster",
  "log-verossimilhança", "Mahalanobis" na tela; "grupo", "densidade", "estatística".

## 8. Capítulo do dossiê

Novo capítulo `anomalia` em `pagina_view.CAPITULOS`, depois de `secoes` e antes de `logs`:
`("anomalia", "Grupos", "Os grupos de seções nos dois turnos", ("anomalia_ml.json",))`.
Módulo `pagina_cap_anomalia.py` com `pagina_fig_anomalia*.py` e `pagina_texto_anomalia.py`
(abaixo de 1.000 linhas cada). Ordem fixa:

1. Abertura pelo número mais forte (quantas seções no grupo atípico e o que o define) e a
   caixa "Como ler" com o rótulo.
2. O espaço: as nove frações, a equivalência afim níveis/diferenças em uma frase, exterior fora.
3. Escolha de k: figura BIC e ICL por k (duas linhas, k* marcado), tabela, a regra em palavras.
4. Convergência: frase com iterações, sementes no máximo, tolerância; k-means como contraste
   (silhueta por k nos dois enquadramentos, ARI com a mistura).
5. Os grupos: painel como o do 1T (`_painel_clusters`), barras do eleitorado 1T e 2T lado a
   lado por grupo, centros em diferenças; composição regional (`clusters_regiao`); dispersão
   PCA com elipse do grupo atípico (`clusters_secoes`), figura pesada em `<noscript class="fig-src">`.
6. O grupo atípico: o que o define, voto contra vizinhas e DiD com IC (publicar seja qual for
   o sinal), cruzamento com os seis sinais e com modelo, mapa de pontos do Brasil
   (`pontos_brasil`) com as seções do grupo, tabela das 50 amostras com link para o Politize-se.
7. Achado contrário obrigatório: o que a mistura NÃO separa (por exemplo, se o grupo atípico
   for geografia ou tamanho de seção, dizer com o V de Cramér).
8. Limites (`limites()`): atipicidade não é irregularidade; k é escolha por regra declarada;
   o grupo depende da padronização; nenhuma seção individual é acusada; exterior fora.

Textos pelo padrão da casa (`pagina_comum.p` com selos verificado/inferência/hipótese/juízo,
`caixa`, `nota("contrario", ...)`), sem travessão, sem "fraude". Thread: um card novo
(`thread_posts_b.py` ou módulo novo) com o mapa dos pontos e o resumo do grupo atípico; só se
couber no portão de cards sem quebrar os testes.

## 9. Testes

- `tests/test_apuracao_2t_2026_anomalia.py`: motor em dados sintéticos pequenos (k escolhido
  pela regra em curva construída; convergência exigida; ordem estável; equivalência afim:
  mesma partição em níveis e em deltas com a mesma semente, ARI = 1); contrato do JSON quando
  existir (chaves, k entre 3 e 10, `ajuste.convergiu`, soma de `pct_secoes` = 100, ponteiro
  do arquivo pesado coerente com `secoes_arquivo`); sem travessão no `.md`.
- Capítulo: entra nos testes de capítulos (`caps_*`) com figuras presentes e regras de texto.
- Politize-se e mapa: colunas e camadas (seção 7).

## 10. Donos

| pacote | escreve em |
|---|---|
| motor | `scripts/apuracao-2t-2026-anomalia.py`, `scripts/apuracao_2t_2026/anomalia_*.py`, `dados/anomalia_ml.{json,md}`, `data/outputs/apuracao_2t_2026/anomalia_secoes.json.gz`, `tests/test_apuracao_2t_2026_anomalia.py` |
| Politize-se e mapa | `scripts/politize_se/{fontes,montagem,saida,textos,mapa_dados,mapa_saida}.py`, `scripts/politize-se-build.py` (catálogos), `docs/assets/politize_se/app.js`, `docs/assets/politize_se_mapa/app.js`, `analysis/politize_se/CONTRATO.md`, `tests/test_politize_se*.py` |
| capítulo | `scripts/apuracao_2t_2026/pagina_cap_anomalia.py`, `pagina_fig_anomalia*.py`, `pagina_texto_anomalia.py`, `pagina_view.py` (uma linha em `CAPITULOS`), `tests/test_apuracao_2t_2026_caps_*.py`, `CONTRATO_DOSSIE.md` (linha da tabela) |

## 11. Registro da execução (26/10/2026, noite)

- **Partida degenerada** (regra acrescentada pelo motor, não prevista acima): partida cuja matriz de
  covariância de algum componente tem menor autovalor abaixo de 1e-4 (componente colado num padrão
  de zeros, variância no piso do `reg_covar`) conta como degenerada, fica fora da escolha como a não
  convergida, e o número de degeneradas é publicado em `ajuste`. Na base inteira houve zero; no
  rascunho de 60 mil seções, em k = 9 e 10, uma partida assim venceria pela verossimilhança.
- Nomes reais no JSON que diferem do esboço da seção 6: o IC da fatia fica em `voto.ic95` e o da
  diferença em diferenças em `voto.ic95_did`; `terceira1_pp` fica dentro de `centro_delta_pp`;
  campos a mais por componente (`rotulo_curto`, `dispersao_relativa`, `centro_modelo_pct_eleitorado`),
  em `mais_anomalo` (`postos`, `seis_sinais`, `contra`, `leitura`, `conclusao`) e no topo
  (`cluster_tamanho`, `cramer_v_tamanho`, `pais.descritores`, `icl_definicao`). `score` é a
  log-densidade nas coordenadas padronizadas. `--so-texto` refaz leitura, conclusão e memorando sem reajustar.
- Politize-se: as listas de colunas chamam-se `saida.COLS_SECAO`, `COLS_LOCAL_MUN` (prédios no arquivo
  do município) e `CAMPOS_TOTAIS`; `ml_anomalo` sai 0/1; a camada `anomalia` leva `precisa_ml: true`
  (campo nulo pinta cinza, não "nenhuma seção"); `indice.anomalia_ml.disponivel` exige o arquivo pesado
  e o compacto.
- Resultado: 497.796 seções; k = 8 pelo joelho do BIC (BIC mínimo em 10, ICL mínimo em 2: grupos
  sobrepostos, regiões de uma nuvem contínua); 16 de 16 partidas convergidas, 13 no mesmo máximo;
  grupo atípico = 10.850 seções (2,18%), brancos e nulos muito altos nos dois turnos, em boa parte
  seções pequenas (34% das de 30 a 99 aptos), não geografia (V de Cramér 0,044 com região) nem modelo
  de urna (0,012); fatia de Flávio −3,56 pp contra vizinhas (IC −3,83 a −3,27, descritivo, o grupo é
  definido pelo voto) e DiD −0,05 pp (IC −0,19 a +0,07). Tempo: 16 min.
