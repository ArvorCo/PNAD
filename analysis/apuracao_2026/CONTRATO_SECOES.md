# Análise por seção (boletins de urna): contrato do JSON

Arquivo: `analysis/apuracao_2026/dados/secoes.json`, gerado por
`python3 scripts/apuracao-2026-secoes.py [--parcial]` (módulos `scripts/apuracao_2026/secoes_*.py`).
Leitor das figuras e do texto: capítulo 12 do dossiê. Nunca editar o JSON à mão.

Regras que valem para todo campo de texto do JSON: sem travessão, pt-BR, "atípico" e "exige
explicação documental" como vocabulário; nunca "fraude". Toda seção citada traz UF, município,
zona, seção e local de votação (registro `SecaoRef`, abaixo).

## Convenções

- `uf`: duas letras MAIÚSCULAS; exterior = `ZZ`. `regiao`: `Norte`, `Nordeste`, `Centro-Oeste`,
  `Sudeste`, `Sul`, `Exterior`.
- `mun_tse`: código TSE do município, texto de 5 dígitos. `ibge`: texto de 7 dígitos ou `null`.
- `zona`, `secao`: inteiros.
- Campos `*_pct`: percentual de 0 a 100, `float` com 2 casas. O texto público usa 1 casa.
- Campos `*_pp`: pontos percentuais (diferença de dois `_pct`), `float` com 2 casas.
- Contagens (`secoes`, `aptos`, `votantes`, `validos`, `votos`): inteiros.
- Base de percentual, sempre declarada no nome ou no campo `base`:
  - `% dos válidos` = votos do candidato / votos nominais nos 12 candidatos da lista (presidente
    não tem voto de legenda). Voto em número fora da lista (nº 28) é nulo técnico, como no TSE.
  - `% do eleitorado` = votos / `aptos` da eleição federal (`aptos_secao + aptos_tte`).
- `ic95`: lista `[inferior, superior]` na mesma unidade da estimativa.
- Ausência de dado é `null`, nunca zero.

## Registro `SecaoRef` (usado em todas as listas de amostras)

```json
{
  "uf": "MA", "regiao": "Nordeste", "municipio": "CAJARI", "mun_tse": "07307", "ibge": "2102408",
  "zona": 20, "secao": 45,
  "local": "U.E. FULANO DE TAL", "bairro": "POVOADO X", "tipo_local_tse": "Convencional",
  "tipo_local_inferido": "escola",
  "lat": -3.32, "lon": -45.01,
  "modelo_urna": "UE2020", "tipo_urna": 1, "tipo_arquivo": 1,
  "aptos": 250, "comparecimento": 210, "validos": 200,
  "lula": 190, "flavio": 6, "outros": 4, "brancos": 3, "nulos": 7,
  "lula_pct": 95.0, "flavio_pct": 3.0,
  "zona_lula_pct": 82.3, "zona_flavio_pct": 14.8,
  "mun_lula_pct": 82.3, "mun_flavio_pct": 14.8,
  "abertura_brasilia": "2026-10-04 08:00:01", "encerramento_brasilia": "2026-10-04 17:04:12",
  "recebido_tse": "2026-10-04 18:55:55",
  "explicacao": "aldeia ou terra indígena (inferido pelo nome do local)"
}
```

`outros` = válidos menos Lula menos Flávio. `nulos` inclui nulo técnico. `zona_*` e `mun_*` são
calculados sobre as seções válidas da mesma zona ou município, incluindo a própria seção.
`tipo_local_inferido` é inferência por palavra-chave (regras em `extremos.tipo_local.regras`);
`tipo_local_tse` é o tipo oficial do cadastro de locais (Convencional, Voto em trânsito, Preso
provisório, Temporário). `explicacao` é regra declarada, não verificação. Horários: o BU grava a
hora local da urna; `*_brasilia` aplica o fuso da UF (e dos municípios do oeste do AM e do AC);
exterior fica em hora local e `abertura_brasilia` é `null`. `recebido_tse` é o campo `dr/hr` do
`aux.json`, como publicado.

## Chaves de primeiro nível

| chave | tipo | conteúdo |
|---|---|---|
| `titulo` | str | |
| `gerado_em` | str ISO 8601 UTC | |
| `versao_contrato` | str | `"1.0"` |
| `aviso` | str | frase responsável (atípico não é irregularidade) |
| `fontes` | lista de `{chave, caminho, descricao}` | bancos e arquivos lidos |
| `cobertura` | objeto | ver 1 |
| `candidatos` | lista de `{numero, chave, nome, cor}` | os 12 da lista do TSE; `chave` = `lula`, `flavio` ou `n<numero>`; `cor` hex ou `null` |
| `extremos` | objeto | pergunta A (seções acima de 90%), ver 2 |
| `clusters` | objeto | pergunta B (mistura gaussiana k = 5 sobre cinco partes), ver 3 |
| `urna` | objeto | pergunta C (modelo de urna), ver 4 |
| `outras` | objeto | pergunta D (outras anomalias de seção), ver 5 |
| `achados` | `{verificado, inferido, juizo, hipotese, contrario}` | cada um lista de str |
| `limites` | lista de str | |

## 1. `cobertura`

```json
{
  "parcial": true,
  "carimbo_log": "2026-10-05T09:15:24Z", "restantes_log": 482439,
  "secoes_cs": 517179, "secoes_principais_cs": 499248, "secoes_agregadas_cs": 17931,
  "secoes_com_bu": 35234, "secoes_validas": 34990,
  "excluidas": [{"codigo": "zona_divergente", "motivo": "...", "secoes": 116, "aptos": 40745}],
  "ufs_completas": ["AC", "AP"], "ufs_incompletas": [{"uf": "AL", "coletadas": 6155, "total": 7246}],
  "por_uf": [{"uf": "AC", "secoes_cs": 2411, "agregadas": 141, "com_bu": 2270, "validas": 2270,
              "zonas": 23, "zonas_ok": 23, "zonas_divergentes": 0, "zonas_sem_conferencia": 0}],
  "totais_validos": {"aptos": 0, "comparecimento": 0, "validos": 0, "lula": 0, "flavio": 0,
                     "brancos": 0, "nulos": 0, "lula_pct": 0.0, "flavio_pct": 0.0}
}
```

Códigos de exclusão: `sem_bu` (seção principal sem boletim), `zona_sem_conferencia` (zona ainda
não conferida contra o arquivo de zona do TSE), `zona_divergente` (soma das seções diferente do
arquivo de zona; o motivo diz se o arquivo de zona congelou incompleto), `tipo_arquivo_ausente`,
`sem_aptos`. Seções agregadas não são exclusão: o voto delas está no BU da principal.

## 2. `extremos` (pergunta A)

| chave | tipo | conteúdo |
|---|---|---|
| `definicao` | str | base: % dos válidos de presidente por seção |
| `limiares` | lista int | `[90, 95, 100]` |
| `corte_tamanho` | int | `100` (votantes, isto é, comparecimento) |
| `resumo` | lista | `{candidato: "lula"|"flavio", limiar, secoes, secoes_100mais, aptos, votantes, validos, votos_candidato, pct_das_secoes}`; `pct_das_secoes` = % das seções válidas |
| `por_uf` | lista | `{uf, regiao, candidato, limiar, secoes, secoes_100mais, aptos, pct_das_secoes_uf}` (só UF com ao menos uma seção) |
| `por_municipio` | lista | os 40 municípios com mais seções ≥ 90% por candidato: `{uf, municipio, mun_tse, ibge, candidato, secoes_90, secoes_total, aptos_90, mun_pct}` |
| `tamanho` | objeto | `{faixas: [{rotulo, min, max}], linhas: [{faixa, todas, lula_90, flavio_90, lula_90_pct, flavio_90_pct}]}`; faixas por votantes: 1–49, 50–99, 100–199, 200–299, 300–399, 400+ |
| `histograma` | objeto | figura `secoes_90`: `{bins_pct: [0, 2.5, ..., 100], lula: [int], flavio: [int], lula_100mais: [int], flavio_100mais: [int]}` (contagem de seções por faixa de % dos válidos; último bin fechado em 100) |
| `excesso` | objeto | `{definicao, lula: Excesso, flavio: Excesso}`; `Excesso = {secoes, zona_pct_mediana, mun_pct_mediana, excesso_zona_pp_mediana, excesso_mun_pp_mediana, faixas_zona: [{rotulo, min_pct, max_pct, secoes}], acima_zona_10pp: int, acima_zona_20pp: int}`; excesso = % da seção menos % da zona sem a própria seção |
| `tipo_local` | objeto | `{regras: [{tipo, campo, palavras}], linhas: [{tipo, todas, lula_90, flavio_90, lula_90_pct_do_tipo, flavio_90_pct_do_tipo}], aviso}` |
| `modelo_urna` | lista | `{modelo, todas, lula_90, flavio_90, lula_90_pct_do_modelo, flavio_90_pct_do_modelo}` |
| `cruzamento_anomalias` | objeto | `{top_zonas: 50, zonas_top_com_secao_90, secoes_90_no_top, taxa_lula_90_top_pct, taxa_lula_90_demais_pct, taxa_flavio_90_top_pct, taxa_flavio_90_demais_pct, lista: [{posicao, uf, municipio, zona, escore, secoes, lula_90, flavio_90}]}` |
| `amostras` | objeto | `{lula: [SecaoRef], flavio: [SecaoRef]}`, até 25 por candidato, só seções com ≥ 100 votantes, ordenadas pelo excesso sobre a zona |
| `secoes_100pct` | objeto | `{lula: [SecaoRef], flavio: [SecaoRef]}`, todas as seções com 100% dos válidos e ≥ 20 válidos (até 60 cada) |
| `mapa` | objeto | figura `secoes_90`: `{colunas: ["lat", "lon", "lula_90", "flavio_90", "secoes"], pontos: [[...]]}`, um ponto por local de votação com ao menos uma seção ≥ 90%, coordenadas com 3 casas; `n_locais`, `n_sem_coordenada` |
| `comparacao_2022` | objeto | `{disponivel: bool, motivo: str}`: o TSE não publica voto por candidato por seção de 2022 nos arquivos que temos |

## 3. `clusters` (pergunta B)

Modelo principal desde 06/10/2026 (terceira tentativa): cinco variáveis por seção, votos de
Lula, de Flávio, brancos, nulos e abstenções, cada uma dividida pelos aptos da eleição federal.
Proporções cruas, sem log e sem troca de zero, como no pedido original do autor. O voto nas
outras dez candidaturas fica implícito: é o que falta para 100% (`1 − soma das cinco`, porque
comparecimento = válidos + brancos + nulos) e sai ao lado de cada centro em
`terceiros_pct_eleitorado`. Antes da mistura, cada proporção é padronizada (menos a média entre
seções, dividida pelo desvio-padrão entre seções; `padronizacao`). As duas tentativas anteriores,
em log-razão, ficam como registro do que não deu certo, em `variantes`.

Busca e ajuste: 16 sementes × 2 inicializações do sklearn (`kmeans` e `k-means++`), uma partida
cada (`n_init` 1), tolerância 1e-6 e até 2.000 iterações, numa amostra estratificada por UF de
150 mil seções (`ajuste.busca_em_amostra`; a busca na base inteira passava de 15 minutos); a
partida de maior log-verossimilhança na amostra é refinada na base inteira a partir dos próprios
parâmetros (mesma tolerância) e depois continuada com tolerância 1e-8 (diagnóstico abaixo).
Rótulos, centros, cruzamentos, PCA, BIC e amostras são da base inteira.

| chave | tipo | conteúdo |
|---|---|---|
| `k` | int | 5 (escolha do autor) |
| `escolha_k` | objeto | `{k, anterior, data, motivo, bic_prefere}`: o k é juízo editorial, o BIC fica ao lado |
| `features` | lista str | `["lula", "flavio", "brancos", "nulos", "abstencao"]` |
| `base` | str | descrição das variáveis (proporções cruas; terceiros implícitos) |
| `transformacao` | str | "padronizada"; `transformacao_detalhe` descreve a padronização |
| `zero` | null | sem troca de zero |
| `padronizacao` | objeto | `{parte: {media_pct, dp_pct}}`: média e desvio-padrão entre seções usados na padronização, em % do eleitorado |
| `referencia_nacional` | objeto | `{parte: {media_pct, dp_pct}}` para as cinco partes e `terceiros`: régua dos rótulos (a mesma da padronização, mais os terceiros) |
| `mediana_votos_por_secao` | objeto | `{parte: f}`: mediana, entre seções, dos votos (e abstenções) de cada parte |
| `empates_por_par` | lista | `{partes: [a, b], secoes, pct_secoes}` para os dez pares de partes: seções com o mesmo número de votos nas duas |
| `zeros_celulas_pct` | float | % das células (seção × parte) iguais a zero (não substituídas) |
| `zeros_por_parte` | objeto | `{parte: {secoes, pct_secoes}}`: seções com a parte zerada |
| `secoes_com_zero` | int | seções com ao menos uma parte zerada |
| `ajuste` | objeto | `{secoes_ajuste, secoes_atribuidas, amostra_estratificada: false, busca_em_amostra: {secoes, estratos: "uf", semente}, covariancia: "full", n_init: 1, inits, random_state, init, sementes: [{semente, init, loglik_media, convergiu, iteracoes, cramer_v_regiao, ari_com_escolhida}], inicializacoes, sementes_no_maximo, max_iter, tol, reg_covar, convergiu, iteracoes, loglik_media, segundos, diagnostico_convergencia}`; `loglik_media`, `convergiu` e `iteracoes` de cada linha de `sementes` são da amostra; `cramer_v_regiao` e `ari_com_escolhida` usam a partição que cada partida dá na base inteira, comparada com a da melhor partida da amostra; `max_iter`, `tol`, `convergiu`, `iteracoes` e `loglik_media` de fora da lista são do ajuste adotado na base inteira |
| `ajuste.diagnostico_convergencia` | objeto | ver abaixo |
| `bic` | lista | `{k, bic, loglik_media, loglik_sementes}` para k = 3, 4, 5, na base inteira; k = 3 e 4 com a busca das 16 sementes (`kmeans`) na mesma amostra e refino na base, k = 5 com o ajuste adotado |
| `componentes` | lista de Componente | ordem do `id` (0 a k − 1, do mais lulista ao menos); no texto e nas figuras o grupo aparece como `id + 1` |
| `menos_votadas` | lista str | vazia no modelo de cinco variáveis (só existe com candidaturas nanicas) |
| `mais_anomalo` | objeto | `{id, criterio, amostras: [SecaoRef + {loglik, mahalanobis, cluster}]}` (20 amostras) |
| `menos_provaveis` | lista | as 50 seções de menor log-verossimilhança: `SecaoRef + {cluster, loglik, mahalanobis}` |
| `cluster_regiao` | lista | `{cluster, regiao, secoes, pct_do_cluster, pct_da_regiao}` |
| `cluster_uf` | lista | `{cluster, uf, secoes, pct_do_cluster, pct_da_uf}` |
| `cramer_v_regiao`, `cramer_v_uf` | float | V de Cramér entre grupo e região, e entre grupo e UF |
| `explicacao_variancia` | objeto | `{parte: {regiao, zona, grupo, zona_mais_grupo}}` para as cinco partes e `terceiros`: R² (%) entre seções explicado pela região, pela zona (município e zona), pelo grupo e pela zona mais o grupo (regressão nos indicadores de grupo dentro da zona); mede o que a mistura acrescenta ao mapa por zona |
| `pca` | objeto | figura `clusters_secoes`: `{base, variancia_explicada: [f, f], cargas: [{feature, pc1, pc2}], separacao: [{componente, feature, carga, zeros_pct, acerto_balanceado_pct, corte}], centros: [{cluster, x, y}], elipses: [{cluster, x, y, cov: [[f, f], [f, f]]}], colunas: ["x", "y", "cluster", "top200", "uf"], pontos: [[x, y, cluster, 0/1, "UF"]], n_pontos}`; dois componentes principais das cinco proporções padronizadas; amostra estratificada por cluster de até 8 mil, mais as 200 menos prováveis com `top200 = 1` |
| `variantes.quinze_partes` | objeto | primeira tentativa (05/10/2026, log-razão das 15 partes), só agregados: `{descricao, abandonada_em, motivo, k, features (15), zeros_substituidos_pct, secoes_com_zero, degrau_log, bic, cramer_v_regiao, cramer_v_uf, ajuste: {sementes, n_init, random_state, sementes_no_maximo, loglik_sementes: [min, max], ari_outras_sementes: [min, max], cramer_v_sementes: [min, max]}, grupos: [Grupo], nuvens: {variancia_explicada, separacao}, diagnostico, leitura_projecao, estabilidade}` |
| `variantes.cinco_partes_clr` | objeto | segunda tentativa (06/10/2026, log-razão das cinco partes fechadas, zero trocado por 0,0001), só agregados: `{descricao, abandonada_em, motivo, k, features, zeros_substituidos_pct, zeros_por_parte, secoes_com_zero, degrau_log, mediana_votos_por_secao, empates_por_par (os de 1% ou mais), bic, cramer_v_regiao, cramer_v_uf, convergencia: {total, no_maximo, ari_medio_no_maximo, ari_medio_demais, particao_estavel, frase}, grupos: [Grupo + artefato], eixo_1: {variancia_explicada, feature, carga}, diagnostico}` |
| `leitura` | objeto | `{geografia, artefatos, mapa, perfis, geometria}`: as frases de leitura com nome (`mapa`, `perfis` e `geometria` podem ser `null`), para o texto escolher cada uma |
| `leitura_projecao` | str | o que cada eixo da projeção opõe e em qual eixo os centros se afastam |
| `estabilidade` | str | a frase do diagnóstico de convergência e o V de Cramér em todas as partidas |
| `interpretacao` | lista str | as frases de `leitura` que existem, na ordem (geografia, artefatos, mapa, perfis, geometria); depois um item por grupo e o mais atípico |

Os registros das tentativas são reaproveitados do JSON gravado por `--so-clusters` (o ajuste é
determinístico; refazê-los custa uns quinze minutos e devolve os mesmos números); a rodada
completa e `--so-clusters --refazer-tentativas` os recalculam.

`Grupo` (nas variantes): `{id, rotulo, secoes, pct_secoes, regiao, regiao_pct, centro_pct_validos}`.

`diagnostico_convergencia`:
```json
{"criterio_padrao": {"tol": 1e-06, "max_iter": 2000}, "sementes": 16,
 "inits": ["kmeans", "k-means++"], "partidas_internas": 1,
 "escolhida": {"semente": 0, "init": "kmeans"},
 "apertado": {"modo": "continua", "tol": 1e-08, "max_iter": 5000, "convergiu": true, "iteracoes": 0,
              "iteracoes_padrao": 0, "loglik_media_padrao": 0.0, "loglik_media_apertado": 0.0,
              "diferenca_loglik": 0.0, "ari_padrao_apertado": 1.0, "adotado": false, "regra": "..."},
 "tolerancia_maximo": 0.001, "ajustes": ["= ajuste.sementes"], "total": 32, "no_maximo": 0,
 "por_init": {"kmeans": {"total": 16, "no_maximo": 0}, "k-means++": {"total": 16, "no_maximo": 0}},
 "todas_convergiram": true, "iteracoes": [0, 0], "loglik_media": [0.0, 0.0],
 "ari_medio_no_maximo": 0.0, "ari_medio_demais": 0.0, "ari_no_maximo_faixa": [0.0, 0.0],
 "particao_estavel": true, "estabilidade": "estável", "amostra": 150000, "ari_amostra_base": 0.0,
 "frase": "O EM convergiu nas 32 partidas (...); N de M partidas chegaram ao mesmo máximo (...). A partição escolhida é estável: ..."}
```
No modelo principal (`apertado.modo` "continua"), o ajuste adotado na base inteira é continuado
a partir dos próprios parâmetros (`warm_start`) com `tol` 1e-8 e até 5.000 iterações; nas
tentativas em log-razão (`modo` "refaz"), a partida escolhida foi refeita com `tol` 1e-6 e até
2.000 iterações. Em qualquer modo, o apertado é adotado se a log-verossimilhança média subir
mais que 0,001 por seção ou se o índice de Rand ajustado entre as duas partições ficar abaixo de
0,99. `ari_amostra_base` compara a partição da melhor partida da amostra com a do ajuste
refinado na base. `ari_medio_no_maximo` e `ari_medio_demais` são médias do índice de Rand
ajustado contra a melhor partida, entre as partidas que chegam ao máximo (a 0,001 por seção) e
entre as demais (`null` se não houver); `estabilidade` é "estável" com média de 0,95 ou mais,
"estável no essencial" de 0,80 a 0,95 e "instável" abaixo disso (régua declarada,
`particao_estavel` = média de 0,95 ou mais).

`Componente`:
```json
{"id": 0, "rotulo": "Lula alto, Flávio baixo, abstenção alta; Nordeste 78% das seções",
 "secoes": 0, "pct_secoes": 0.0, "aptos": 0,
 "aptos_medio": 0.0, "votantes_medio": 0.0,
 "centro_pct_eleitorado": {"lula": 0.0, "flavio": 0.0, "brancos": 0.0, "nulos": 0.0, "abstencao": 0.0},
 "zeros_pct": {"lula": 0.0, "flavio": 0.0, "brancos": 0.0, "nulos": 0.0, "abstencao": 0.0},
 "centro_pct_validos": {"lula": 0.0, "flavio": 0.0, "outros": 0.0},
 "terceiros_pct_eleitorado": 0.0,
 "peso": 0.0, "dispersao_logdet": 0.0, "dispersao_traco": 0.0,
 "loglik_media": 0.0, "loglik_p05": 0.0, "mahalanobis_mediana": 0.0,
 "ufs_top": [{"uf": "BA", "secoes": 0, "pct_do_cluster": 0.0}],
 "regioes": [{"regiao": "Nordeste", "secoes": 0, "pct_do_cluster": 0.0}],
 "modelo_urna": [{"modelo": "UE2020", "pct_do_cluster": 0.0}],
 "padrao_zeros": [], "padrao_empates": [], "artefato": null}
```
O centro em `% do eleitorado` é a média das frações do eleitorado das seções do componente
(não a destransformação do centro em CLR, que distorce componentes raros), e as cinco partes
mais `terceiros_pct_eleitorado` somam 100; `centro_pct_validos` é a soma dos votos do
componente dividida pelos válidos do componente.

`rotulo` (gerado dos números): compara o centro de cada parte, e dos terceiros, com
`referencia_nacional` em desvios-padrão entre seções; um quarto de desvio ou mais vira "alto"
ou "baixo" (um desvio ou mais, "muito alto" ou "muito baixo"), no máximo três partes, das mais
distantes para as menos; sem nenhuma, "perto da média nacional". Fecha com a região dominante
(a primeira, se tiver ao menos 50% das seções do grupo; senão as duas primeiras). Quando o
grupo é artefato da contagem inteira, o rótulo abre por `artefato` e as partes dele saem dos
qualificadores.

`artefato` (str ou `null`): ausência de voto numa parte em todo o grupo (`padrao_zeros` com
`tipo` "sem"; ter voto, `tipo` "com", é o estado comum e não entra) ou o mesmo número de votos
em duas partes (`padrao_empates`, por exemplo "mesmo número de brancos e de nulos").
`padrao_empates` (lista): `{partes: [a, b], pct_grupo, outro_grupo, pct_outro, pct_por_grupo}`,
com a mesma regra do padrão de zeros (cobre ao menos 95% das seções do grupo e difere em ao
menos 30 pontos de algum outro grupo). Os grupos de `variantes.meio_voto` usam as mesmas
regras.

`padrao_zeros` (lista, em cada Componente): o padrão de zeros que define o grupo, gerado dos
números. Item: `{tipo: "sem"|"com"|"parcial_sem"|"parcial_com", conjunto: "menos_votadas"|null, m,
partes: [chaves], pct_grupo, outro_grupo, pct_outro, pct_por_grupo: [f]}`. Um padrão vale quando
cobre ao menos 95% das seções do grupo e difere em ao menos 30 pontos de algum outro grupo; testa
nenhum voto nas m candidaturas menos votadas (maior m), algum voto nelas (menor m) e cada parte
sozinha; `parcial_*` entra só quando outro grupo ficaria sem distinção.

## 4. `urna` (pergunta C)

| chave | tipo | conteúdo |
|---|---|---|
| `modelos` | lista str | modelos presentes, do mais velho ao mais novo |
| `por_uf` | lista | figura `modelo_urna_uf`: `{uf, regiao, modelo, secoes, pct_da_uf}` |
| `fonte_modelo` | lista | `{modelo_fonte, secoes}` (de onde veio o modelo: log da urna) |
| `bruto` | lista | `{modelo, secoes, votantes, validos, flavio_pct, lula_pct, abstencao_pct, brancos_pct, nulos_pct}` (soma de votos / soma da base) |
| `voto_por_uf_modelo` | lista | figuras `voto_por_modelo_nacional` e `voto_por_modelo_uf`: `{uf, regiao, modelo, secoes, votantes, validos, lula, flavio, lula_pct, flavio_pct, abstencao_pct}` por UF e modelo, mesma regra de `bruto` (seções válidas; sem modelo vira "sem modelo"; exterior com `uf` ZZ) |
| `dentro_zona` | Estimador | figura `modelo_urna_zona` |
| `dentro_local` | Estimador | mesmo prédio |
| `reguas` | objeto | `{itens: [{estimador, metrica, regua, unidade, unidades, estimativa, ic95, bruto}], max_abs_pp, positivas, negativas, limiar_pp, leitura}`: as quatro réguas nacionais da urna mais nova contra a mais velha para Flávio (zona, prédio, linha de base da seção em 2022, troca de urna entre as eleições); `leitura` sai do tamanho máximo e de o sinal mudar entre elas |
| `interpretacao` | lista str | primeira frase diz se o modelo move o voto dentro da zona; a última é `reguas.leitura` |

`Estimador`:
```json
{"definicao": "...", "minimo_secoes_por_modelo": 20, "bootstrap": 2000, "semente": 20261005,
 "pares": [{"a": "UE2020", "b": "UE2022", "unidades": 0, "secoes_a": 0, "secoes_b": 0,
            "votantes_a": 0, "votantes_b": 0,
            "flavio_pp": {"estimativa": 0.0, "ic95": [0.0, 0.0], "bruto": 0.0},
            "lula_pp": {...}, "abstencao_pp": {...}, "brancos_pp": {...}, "nulos_pp": {...}}]}
```
Diferença = modelo `b` menos modelo `a` (o mais novo menos o mais velho), em pp. `estimativa`:
média, ponderada pelos votantes da unidade (zona ou local), das diferenças dentro da unidade;
`ic95`: bootstrap de unidades (2.000 reamostras, percentis 2,5 e 97,5); `bruto`: diferença sem
controle, no mesmo subconjunto de seções. Para `dentro_local`, `minimo_secoes_por_modelo` = 1.
Bases: Flávio e Lula em % dos válidos; abstenção em % dos aptos; brancos e nulos em % do
comparecimento.

## 5. `outras` (pergunta D)

| chave | tipo | conteúdo |
|---|---|---|
| `comparecimento` | objeto | `{acima_100: int, igual_100: int, abstencao_zero: int, amostras: [SecaoRef]}` |
| `zero_votos` | objeto | `{minimo_votantes: 200, lula: {secoes, por_uf: [{uf, secoes}], amostras: [SecaoRef]}, flavio: {...}}` |
| `tipo_arquivo` | lista | `{tipo_arquivo, descricao, secoes, votantes, flavio_pct, lula_pct, dif_zona_flavio_pp, dif_zona_lula_pp}` (`dif_zona` = média ponderada de seção menos resto da zona) |
| `tipo_urna` | lista | mesmo formato, por `tipo_urna` (1 seção, 3 contingência, 4 reserva de seção, 6 reserva encerrando seção) |
| `cargas` | lista | mesmo formato, por `n_cargas` (1, 2, 3+) |
| `horarios` | objeto | `{fuso: str, abertura: {antes_0730, depois_0900, depois_1000, amostras}, encerramento: {depois_1800, depois_1900, depois_2000, amostras}, histograma_encerramento: [{hora, secoes}]}` (hora de Brasília) |
| `recebimento` | objeto | `{por_hora: [{hora: "AAAA-MM-DD HH", secoes, validos, lula_pct, flavio_pct}], depois_0000: {secoes, validos, lula_pct, flavio_pct, municipios: [{uf, municipio, secoes, lula_pct}]}, depois_0100: {...}, amostras: [SecaoRef]}` |
| `ultimo_digito` | lista | `{uf, candidato, n, chi2, gl, p, frequencias: [10 floats]}` (seções com ≥ 10 votos no candidato) |
| `benford2` | lista | `{uf, candidato, n, chi2, gl, p, observado: [10 floats], esperado: [10 floats]}` |
| `aviso_benford` | str | Benford em eleição é teste fraco (Deckert, Myagkov e Ordeshook, 2011) |

## Mudanças

Toda mudança de chave já publicada fica registrada aqui, com data e motivo.

- 05/10/2026, acréscimos (nenhuma chave publicada mudou):
  - `clusters.componentes[].zeros_pct` (dict feature → % de seções do grupo com zero
    nessa parte), `clusters.features`, `clusters.zeros_substituidos_pct`,
    `clusters.cramer_v_regiao`, `clusters.cramer_v_uf`, `clusters.sensibilidade`
    (`ari_principal_vs_outra_semente`, `ari_principal_vs_nanicos_somados`,
    `ari_principal_vs_densa`). `cluster_uf` usa a chave `uf` e `pct_da_uf`.
  - `clusters.variantes.nanicos_somados` e `clusters.variantes.densa`: mesma
    estrutura do bloco principal (`features`, `ajuste`, `componentes`,
    `mais_anomalo`, `menos_provaveis`, `cluster_regiao`, `cluster_uf`, `pca` com até
    4 mil pontos) e `descricao`. A densa (Lula, Flávio, terceiros, brancos e nulos,
    abstenção) é a leitura política; a principal é a especificação pedida.
  - Cada `SecaoRef` em listas de clusters ganha `loglik`, `mahalanobis`, `cluster`;
    nas amostras de `extremos`, `excesso_zona_pp` e `excesso_mun_pp`.
  - `urna.dentro_zona_variacao` (Estimador com `flavio_var_pp` e `lula_var_pp`:
    variação da mesma seção contra 2022) e `urna.troca_2022_2026` (Estimador cujo
    rótulo é o modelo de 2022 da seção; mais `modelos_2026_das_velhas`).
  - `urna.ano_2022` (`bruto`, `dentro_zona`, `dentro_local` com `bolsonaro_pp` no
    lugar de `flavio_pp`). Todo Estimador traz também o par
    `mais velha` → `mais nova` (o modelo mais novo contra o mais velho de cada unidade).
  - `urna.registro`: `dentro_local_2026`, `variacao_2026`, `mesmas_secoes` (por modelo
    de 2022: voto de 2022 e de 2026 nas mesmas seções), `ano_2022.dentro_local`.
  - `extremos.secoes_base`, `extremos.secoes_sem_validos`,
    `extremos.secoes_100pct.lula_total` e `flavio_total`;
    `extremos.comparacao_2022` com `secoes_casadas`,
    `secoes_90_em_2022_entre_casadas` e, por candidato, `secoes_90_2026_casadas`,
    `tambem_90_em_2022_1t`, `tambem_90_em_2022_2t`, `acima_80_em_2022_1t`,
    `pct_2022_1t_mediana`, `pct_2022_2t_mediana`, `variacao_pp_mediana`.
  - `outras.amostras_nao_padrao`, `outras.horarios.voto_vs_zona`,
    `outras.recebimento.depois_2200`, `outras.comparecimento.acima_98` e
    `igual_100_por_tamanho`.
  - `cobertura.confere_nacional` (só sem `--parcial`): soma de todos os boletins
    contra o arquivo nacional do TSE.
- 05/10/2026, k = 3 no lugar de k = 4 (pedido do autor, que lê três grupos na projeção
  em dois componentes principais): `clusters.k` passa a 3, as variantes também usam k = 3,
  e `clusters.escolha_k` registra a escolha, a data e o k que o BIC prefere. A tabela `bic`
  continua com k = 3, 4 e 5.
- 05/10/2026, ajuste por várias sementes: a semente única (20261005, 10 inicializações)
  parava em máximos locais muito diferentes (com k = 3, log-verossimilhança média de −11,50
  numa semente e +5,26 em outra). Cada k passa a ser ajustado com 8 sementes (20261005 a
  20261012), fica o de maior log-verossimilhança; `ajuste.random_state` é a semente escolhida
  e `ajuste.sementes` traz todas. `sensibilidade.ari_principal_vs_outra_semente` passa a
  comparar com a segunda melhor semente (`outra_semente_criterio`).
- 05/10/2026, rótulos: `componentes[].rotulo` começa pelo padrão de zeros que define o grupo
  (`componentes[].padrao_zeros`); acréscimos `menos_votadas`, `degrau_log`,
  `pca.separacao`, `pca.elipses` (centro e covariância de todas as seções de cada grupo no
  plano, para a elipse da figura), `leitura_projecao`, `estabilidade`. Texto e figuras numeram os grupos
  como `id + 1`.
- 05/10/2026, remoção: `urna.registro` (caso Registro, SP) sai do JSON, da figura
  `modelo_urna_zona`, do texto do capítulo 12 e do memorando, a pedido do autor. Ficam os
  quatro estimadores nacionais e o bloco de 2022; acréscimo `urna.reguas`, que junta as
  quatro réguas e escreve a leitura.
- 06/10/2026: `clusters.k` passa de 3 para 5 (escolha do autor; coincide com o k preferido pelo BIC); `componentes`, `mais_anomalo`, `cluster_regiao`, `cluster_uf` e `pca` seguem o mesmo esquema com cinco grupos; paleta da figura com cinco cores.
- 06/10/2026, acréscimo: `urna.voto_por_uf_modelo` (voto por UF e modelo de urna, somas e parcelas), para as figuras `voto_por_modelo_nacional` e `voto_por_modelo_uf`. Nenhuma chave publicada mudou. `scripts/apuracao-2026-secoes.py --so-urna` refaz só o bloco `urna` (e achados e memorando) sobre o JSON existente, sem refazer a mistura gaussiana.
- 06/10/2026, mistura de cinco partes no lugar da de 15 (pedido do autor). Motivo: com as 12
  candidaturas, brancos, nulos e abstenção, 42,7% das células eram zero; o zero trocado por
  0,0001 cria um degrau de 3 a 4 unidades de log até o primeiro voto, e a mistura passou a
  separar as seções pelo padrão de zeros das candidaturas nanicas (quem tem ou não tem voto em
  Zema, Samara e nas menos votadas), não pela geografia (V de Cramér com a região de 0,21).
  Mudanças de chave:
  - `clusters.features` passa a `["lula", "flavio", "brancos", "nulos", "abstencao"]`; `base`
    e `transformacao_detalhe` descrevem a composição fechada sobre as cinco partes; o voto em
    terceiros fica fora e sai em `componentes[].terceiros_pct_eleitorado` (acréscimo).
  - `componentes[].rotulo` passa a ser o rótulo de perfil (partes acima ou abaixo da média
    nacional e região dominante), com a régua em `referencia_nacional` (acréscimo).
  - Acréscimos: `zeros_por_parte`, `secoes_com_zero`, `mediana_votos_por_secao`,
    `empates_por_par`, `leitura`, `componentes[].padrao_empates`, `componentes[].artefato`,
    `ajuste.inits`, `ajuste.init`, `ajuste.diagnostico_convergencia`, `pca.base`; cada linha
    de `ajuste.sementes` ganha `init`.
  - `degrau_log` usa como base o total das cinco partes (aptos menos o voto em terceiros).
  - O ajuste principal passa de 8 sementes a 16 sementes × 2 inicializações (`kmeans` e
    `k-means++`), pedido de 06/10/2026 para provar que o EM vai até a convergência e que o
    máximo escolhido não é um máximo local pobre; a tabela `bic` usa as 16 sementes.
  - A PCA da figura passa a ser feita nas coordenadas ILR, com as cargas reescritas nas partes
    (os escores são os mesmos da PCA na CLR).
  - Removidas: `variantes.nanicos_somados`, `variantes.densa` e as chaves de `sensibilidade`
    `ari_principal_vs_outra_semente`, `outra_semente`, `outra_semente_criterio`,
    `ari_principal_vs_nanicos_somados` e `ari_principal_vs_densa` (eram sensibilidades da
    versão de 15 partes; a outra semente foi substituída pelo diagnóstico de convergência).
  - Acréscimos: `variantes.quinze_partes` (só agregados da versão abandonada),
    `variantes.meio_voto` (zero trocado por meio voto) e `sensibilidade` com
    `ari_principal_vs_quinze_partes` e `ari_principal_vs_meio_voto`.
  - `interpretacao` muda de estrutura: a primeira frase compara a geografia com a versão de 15
    partes e a segunda diz quantos grupos ainda são definidos por zero.
  - `scripts/apuracao-2026-secoes.py --so-clusters` refaz só o bloco `clusters` (e achados,
    limites e memorando) sobre o JSON existente; `--so-textos` não lê banco nenhum e refaz só
    os rótulos e as frases do bloco a partir dos números gravados (revisão editorial).
  - Resultado registrado na própria rodada: com cinco partes, três dos cinco grupos ainda são
    artefatos da contagem inteira de brancos e nulos (seção sem voto branco, seção sem voto
    nulo, seção com o mesmo número de brancos e de nulos); os outros dois repetem a divisão
    regional do mapa. O texto e a thread dizem isso, e `variantes.meio_voto` mostra o efeito
    de trocar o zero por meio voto.
- 06/10/2026, proporções cruas no lugar da log-razão (decisão do autor e do coordenador, depois
  do diagnóstico da segunda tentativa). Motivo: na log-razão das cinco partes, brancos e nulos,
  com mediana de 4 e 7 votos por seção, pesavam tanto quanto Lula e Flávio; o zero e o empate
  entre eles definiram três dos cinco grupos (V de Cramér com a região 0,24). O pedido original
  era "voto de cada candidato dividido pelo total do eleitorado da seção"; a log-razão e o zero
  trocado por 0,0001 foram acréscimo nosso. Mudanças de chave:
  - `transformacao` passa a "padronizada"; `zero` passa a `null`; acréscimo `padronizacao`.
  - `zeros_substituidos_pct` passa a `zeros_celulas_pct` no bloco principal (os zeros não são
    trocados); os registros das tentativas mantêm `zeros_substituidos_pct` e `degrau_log`, que
    saem do bloco principal.
  - A busca passa a uma partida por semente e inicialização (`n_init` 1), tolerância 1e-6 e até
    2.000 iterações, numa amostra estratificada por UF de 150 mil seções
    (`ajuste.busca_em_amostra`), com refino na base inteira; o diagnóstico continua o ajuste
    adotado com tolerância 1e-8 (`apertado.modo` "continua") e ganha `amostra`,
    `ari_amostra_base`, `ari_no_maximo_faixa` e `estabilidade`.
  - A PCA passa a ser das cinco proporções padronizadas.
  - Acréscimos: `explicacao_variancia` (R² por região, zona, grupo e zona mais grupo) e
    `leitura.mapa`; `variantes.cinco_partes_clr` (registro da segunda tentativa).
  - Removidas: `variantes.meio_voto` e `sensibilidade` (eram sensibilidades da log-razão).
