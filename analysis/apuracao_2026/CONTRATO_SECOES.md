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
| `clusters` | objeto | pergunta B (mistura gaussiana k = 3), ver 3 |
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

| chave | tipo | conteúdo |
|---|---|---|
| `k` | int | 3 (escolha do autor desde 05/10/2026; antes 4) |
| `escolha_k` | objeto | `{k, anterior, data, motivo, bic_prefere}`: o k é juízo editorial, o BIC fica ao lado |
| `features` | lista str | chaves das 15 componentes: 12 candidatos, `brancos`, `nulos`, `abstencao` |
| `base` | str | "votos de cada componente / aptos da seção (eleição federal)" |
| `transformacao` | str | "clr" (log-razão centrada); zeros substituídos por 0,0001 antes do log |
| `zero` | float | 0.0001 |
| `ajuste` | objeto | `{secoes_ajuste, secoes_atribuidas, amostra_estratificada: bool, covariancia: "full", n_init: 10, random_state, sementes: [{semente, loglik_media, convergiu, iteracoes, cramer_v_regiao, ari_com_escolhida}], inicializacoes, sementes_no_maximo, convergiu: bool, iteracoes, loglik_media}`; `random_state` é a semente escolhida (a de maior log-verossimilhança entre 8 sementes de 10 inicializações) |
| `bic` | lista | `{k, bic, loglik_media, loglik_sementes}` para k = 3, 4, 5, cada um com o melhor ajuste das mesmas sementes |
| `componentes` | lista de Componente | ordem do `id` (0 a k − 1, do mais lulista ao menos); no texto e nas figuras o grupo aparece como `id + 1` |
| `menos_votadas` | lista str | candidaturas fora Lula e Flávio, da menos para a mais votada (base dos padrões de zeros) |
| `degrau_log` | objeto | `{aptos_mediana, mediana, p10, p90}`: distância, em unidades de log, entre zero (0,0001) e um voto na seção |
| `mais_anomalo` | objeto | `{id, criterio, amostras: [SecaoRef + {loglik, mahalanobis}]}` (20 amostras) |
| `menos_provaveis` | lista | as 50 seções de menor log-verossimilhança: `SecaoRef + {cluster, loglik, mahalanobis}` |
| `cluster_regiao` | lista | `{cluster, regiao, secoes, pct_do_cluster, pct_da_regiao}` |
| `cluster_uf` | lista | `{cluster, uf, secoes, pct_do_cluster}` |
| `pca` | objeto | figura `clusters_secoes`: `{variancia_explicada: [f, f], cargas: [{feature, pc1, pc2}], separacao: [{componente, feature, carga, zeros_pct, acerto_balanceado_pct, corte}], centros: [{cluster, x, y}], elipses: [{cluster, x, y, cov: [[f, f], [f, f]]}], colunas: ["x", "y", "cluster", "top200", "uf"], pontos: [[x, y, cluster, 0/1, "UF"]], n_pontos}` (amostra estratificada por cluster de até 8 mil, mais as 200 menos prováveis com `top200 = 1`); `separacao` mede, para a parte de maior carga em cada componente, o melhor corte no eixo entre seções com e sem voto nela |
| `leitura_projecao` | str | compara as nuvens visíveis na projeção com a divisão da mistura |
| `estabilidade` | str | quanto a log-verossimilhança e a partição mudam entre sementes, e o V de Cramér em todas |
| `interpretacao` | lista str | primeira frase diz se os clusters são geografia |

`Componente`:
```json
{"id": 0, "rotulo": "sem voto nas cinco candidaturas menos votadas; Flávio 47% dos válidos; Sudeste 37% das seções",
 "secoes": 0, "pct_secoes": 0.0, "aptos": 0,
 "aptos_medio": 0.0, "votantes_medio": 0.0,
 "centro_pct_eleitorado": {"lula": 0.0, "flavio": 0.0, "n70": 0.0, "brancos": 0.0, "nulos": 0.0, "abstencao": 0.0},
 "centro_pct_validos": {"lula": 0.0, "flavio": 0.0, "outros": 0.0},
 "peso": 0.0, "dispersao_logdet": 0.0, "dispersao_traco": 0.0,
 "loglik_media": 0.0, "loglik_p05": 0.0, "mahalanobis_mediana": 0.0,
 "ufs_top": [{"uf": "BA", "secoes": 0, "pct_do_cluster": 0.0}],
 "regioes": [{"regiao": "Nordeste", "pct_do_cluster": 0.0}],
 "modelo_urna": [{"modelo": "UE2020", "pct_do_cluster": 0.0}]}
```
O centro em `% do eleitorado` é a média das frações observadas das seções do componente (não a
destransformação do centro em CLR, que distorce componentes raros); `centro_pct_validos` é a soma
dos votos do componente dividida pelos válidos do componente.

`padrao_zeros` (lista, em cada Componente): o padrão de zeros que define o grupo, gerado dos
números. Item: `{tipo: "sem"|"com"|"parcial_sem"|"parcial_com", conjunto: "menos_votadas"|null, m,
partes: [chaves], pct_grupo, outro_grupo, pct_outro, pct_por_grupo: [f]}`. Um padrão vale quando
cobre ao menos 95% das seções do grupo e difere em ao menos 30 pontos de algum outro grupo; testa
nenhum voto nas m candidaturas menos votadas (maior m), algum voto nelas (menor m) e cada parte
sozinha; `parcial_*` entra só quando outro grupo ficaria sem distinção. `rotulo` começa por esse
padrão.

## 4. `urna` (pergunta C)

| chave | tipo | conteúdo |
|---|---|---|
| `modelos` | lista str | modelos presentes, do mais velho ao mais novo |
| `por_uf` | lista | figura `modelo_urna_uf`: `{uf, regiao, modelo, secoes, pct_da_uf}` |
| `fonte_modelo` | lista | `{modelo_fonte, secoes}` (de onde veio o modelo: log da urna) |
| `bruto` | lista | `{modelo, secoes, votantes, validos, flavio_pct, lula_pct, abstencao_pct, brancos_pct, nulos_pct}` (soma de votos / soma da base) |
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
