# Onde colocar fiscal (capítulo 13): contrato do JSON

Arquivo: `analysis/apuracao_2026/dados/fiscais.json`, gerado por
`python3 scripts/apuracao-2026-fiscais.py` (módulos `scripts/apuracao_2026/fiscais_*.py`).
Leitor das figuras, do mapa navegável e do texto: capítulo 13 do dossiê ("Onde colocar
fiscal"). Nunca editar o JSON à mão. Exportáveis gerados na mesma rodada:
`docs/assets/fiscais_2026.csv`, `docs/assets/fiscais_2026_por_local.csv` e
`docs/assets/fiscais_2026.xlsx`.

Rótulo obrigatório, em todo bloco de texto público que usar este JSON (as três frases ficam
em `rotulos`, prontas para copiar):

1. Atipicidade estatística não é irregularidade.
2. A lista é de prioridade de fiscalização, não de acusação.
3. O que resolve cada item é a ata da mesa, o log da urna e a presença do fiscal.

Regras de texto que valem para todo campo do JSON: sem travessão, pt-BR, "atípico" e "exige
explicação documental" como vocabulário; nunca "fraude". Toda seção citada traz UF, município,
zona, seção, local de votação e endereço.

## Convenções

As do `CONTRATO_SECOES.md` (`uf` MAIÚSCULA, `mun_tse` texto de 5 dígitos, `ibge` texto de 7
dígitos ou `null`, `zona` e `secao` inteiros, `*_pct` de 0 a 100 com 2 casas, `*_pp` em
pontos, ausência = `null`, nunca zero). Mais:

- `local_id`: texto `"UF-MUNTSE-ZONA-LOCALNR"` (ex.: `"MA-07307-20-1104"`). Número do local
  de votação do cadastro do TSE, único dentro da zona. Seção sem número de local no cadastro:
  `"UF-MUNTSE-ZONA-s<secao>"`.
- Horários: `*_brasilia` na hora de Brasília (`AAAA-MM-DD HH:MM:SS`); `recebido_tse` é o
  `dr/hr` do `aux.json`, como publicado (Brasília). Exterior fica em hora local.
- `nivel`: `"alta"`, `"media"` ou `"baixa"` (sem acento na chave; o texto público escreve
  "média").
- Excesso sobre a zona: % do candidato na seção menos % do candidato no resto da zona (a zona
  sem a própria seção), em pontos dos válidos.

## Universo

Todas as seções principais com boletim de urna no banco: as 497.890 válidas do capítulo 12
mais as seções excluídas do capítulo 12 só porque a zona diverge do arquivo de zona do TSE
(Betim 319, Uberlândia 279, Carapicuíba 388), desde que o boletim delas seja íntegro (soma dos
votos de presidente igual ao comparecimento, aptos > 0, tipo de arquivo declarado). Mais as
20 seções principais ativas sem arquivo publicado (critério h), que entram sem votos. Zona e
município são recalculados sobre esse universo (só as três zonas acima mudam em relação ao
capítulo 12). A mistura gaussiana (critério e) cobre só as válidas do capítulo 12.

## Chaves de primeiro nível

| chave | tipo | conteúdo |
|---|---|---|
| `titulo` | str | |
| `gerado_em` | str ISO 8601 UTC | |
| `versao_contrato` | str | `"1.0"` |
| `aviso` | str | as três frases do rótulo, num parágrafo |
| `rotulos` | `{atipico, prioridade, resolve}` | as três frases, separadas |
| `meta` | objeto | ver 1 |
| `criterios` | lista de Criterio | ver 2 |
| `secoes` | lista de SecaoFiscal | todas as seções sinalizadas (ao menos um critério), ordenadas por nível (alta, média, baixa), pontuação decrescente, aptos decrescentes; ver 3 |
| `destaques` | lista de SecaoFiscal | as 300 primeiras de `secoes` com nível alta ou média, para tabela da página sem carregar tudo |
| `por_uf` | lista | ver 4 |
| `por_municipio` | lista | ver 4 |
| `por_zona` | lista | ver 4 |
| `por_local` | lista de Local | ver 5 |
| `prioridade_pl` | objeto | três rankings, ver 6 |
| `sensibilidade` | objeto | pesos iguais contra pesos declarados, ver 7 |
| `resumo` | objeto | ver 8 |
| `mapa` | objeto | pontos por local para o mapa navegável, ver 9 |
| `sem_arquivo` | lista de SecaoFiscal | as 20 seções sem `aux.json` publicado (também em `secoes`) |
| `zonas_congeladas` | lista | ver 10 |
| `achados` | `{verificado, inferido, juizo, hipotese, contrario}` | cada um lista de str |
| `limites` | lista de str | |

## 1. `meta`

```json
{
  "data_eleicao": "2026-10-04", "segundo_turno": "2026-10-25",
  "fontes": [{"chave": "boletins", "caminho": "apuracao/data/secoes_2026.sqlite",
              "descricao": "...", "bytes": 0, "sha256": "..." , "modificado_em": "..."}],
  "criterios": [{"id": "a", "regra": "...", "limiar": "...", "peso": 3}],
  "pesos": {"a": 3, "b": 3, "c": 3, "d": 2, "e": 2, "f": 2, "g": 1,
            "h_sem_arquivo": 3, "h_zona_congelada": 1, "i": 1, "j": 2, "k": 1, "l": 2},
  "cortes_nivel": {"alta": 5, "media": 3, "regra": "..."},
  "explicacoes_comuns": [{"codigo": "aldeia", "rotulo": "...", "regra": "...", "grupo": "comum_documentada"}],
  "base_legal": [{"norma": "...", "dispositivo": "...", "conteudo": "...", "fonte": "analysis/apuracao_2026/dados/fechamento.json"}],
  "universo": {"secoes_validas_cap12": 0, "secoes_zona_divergente_integras": 0,
               "secoes_sem_arquivo": 20, "secoes_universo": 0, "secoes_na_mistura": 0},
  "exportaveis": [{"formato": "csv|xlsx", "caminho": "docs/assets/fiscais_2026.csv",
                   "conteudo": "...", "linhas": 0, "colunas": ["..."], "separador": ";",
                   "decimal": ",", "codificacao": "utf-8-sig", "bytes": 0, "sha256": "..."}]
}
```

`fontes` traz `sha256` de todo arquivo lido; os bancos SQLite que o coletor ainda grava
(`apuracao.sqlite`) trazem `sha256` `null` e o motivo, com tamanho e data de modificação.

## 2. `Criterio`

```json
{"id": "a", "nome": "90% ou mais com excesso sobre a zona",
 "mede": "...", "regra": "...", "limiar": "...", "peso": 3,
 "secoes": 0, "secoes_por_nivel": {"alta": 0, "media": 0, "baixa": 0},
 "aptos": 0, "so_este": 0,
 "explicacao_comum": "...", "o_que_conferir": "...", "fonte": "..."}
```

`so_este`: seções em que só este critério disparou. Os critérios, com o limiar exato:

| id | nome | regra |
|---|---|---|
| a | 90% ou mais com excesso sobre a zona | Lula ou Flávio com 90% ou mais dos válidos, 100 votantes ou mais e excesso de 20 pp ou mais sobre o resto da zona. Seção casada com 2022 em que o mesmo campo já tinha 90% ou mais (Lula para Lula; Bolsonaro para Flávio; 1º ou 2º turno) é `enclave_2022` e fica em nível baixa |
| b | zero voto num dos dois | Lula ou Flávio com zero voto e 150 votantes ou mais |
| c | comparecimento total | comparecimento igual ou maior que os aptos (abstenção zero) e 50 aptos ou mais |
| d | encerramento tardio com Lula acima da zona | último voto às 19h de Brasília ou depois e Lula 10 pp ou mais acima do resto da zona |
| e | entre as 200 menos prováveis da mistura | as 200 seções de menor log-verossimilhança na mistura gaussiana de cinco grupos do capítulo 12 (as marcadas `top200` na figura `clusters_secoes`), refeita com a semente e a inicialização gravadas em `secoes.json` e conferida contra as 50 de `clusters.menos_provaveis`; o grupo de cada uma vai em `detalhe.e` |
| f | urna ou arquivo fora do padrão com voto diferente da zona | arquivo recuperado ou de sistema de apuração (tipo de arquivo diferente de 1), urna de contingência ou reserva (tipo de urna diferente de 1) ou mais de uma carga, e Lula ou Flávio 10 pp ou mais longe do resto da zona, para cima ou para baixo |
| g | boletim recebido de madrugada | `dr/hr` às 00:00 de 05/10 ou depois |
| h | sem arquivo ou em zona congelada | (1) seção principal ativa sem `aux.json` publicado (o TSE devolve 404; peso 3) ou (2) seção que faltava num arquivo de zona do TSE que ficou parado incompleto por 6 horas ou mais depois do fim da votação (boletim recebido depois da última versão incompleta; peso 1) |
| i | zona entre as 50 mais atípicas e seção longe da UF | seção numa das 50 zonas de `anomalias.json` (`topo`) com Lula ou Flávio 10 pp ou mais acima da própria UF |
| j | variação 2022-2026 fora da faixa da UF | seção casada com 2022 (mesmo número e mesmo local), 50 ou mais votos nominais nos dois anos; variação da margem (Flávio menos Lula em 2026 contra Bolsonaro menos Lula no 1º turno de 2022) a mais de 3 desvios-padrão da média das seções casadas da UF |
| k | brancos ou nulos muito acima da zona | brancos ou nulos (% do comparecimento) 3 desvios-padrão ou mais acima da média das outras seções da zona e 3 pp ou mais acima dela; 50 votantes ou mais e ao menos 8 outras seções na zona |
| l | local com três ou mais seções sinalizadas | local de votação com 3 ou mais seções sinalizadas pelos critérios de seção (a, b, c, d, e, f, j, k); g, h e i ficam fora da contagem porque valem para o local ou a zona inteira por construção |

## 3. `SecaoFiscal`

```json
{
  "uf": "MA", "regiao": "Nordeste", "municipio": "CAJARI", "mun_tse": "07307", "ibge": "2102408",
  "zona": 20, "secao": 45, "local_id": "MA-07307-20-1104", "local_nr": 1104,
  "local": "U.E. FULANO DE TAL", "endereco": "RUA X, S/N", "bairro": "POVOADO X", "cep": "65000000",
  "lat": -3.32123, "lon": -45.01234,
  "tipo_local_tse": "Convencional", "tipo_local_inferido": "escola ou universidade",
  "aptos": 250, "votantes": 210, "validos": 200, "brancos": 3, "nulos": 7,
  "lula": 190, "flavio": 6, "lula_pct": 95.0, "flavio_pct": 3.0,
  "zona_lula_pct": 82.3, "zona_flavio_pct": 14.8,
  "excesso_zona_lula_pp": 12.9, "excesso_zona_flavio_pp": -11.9,
  "uf_lula_pct": 70.1, "uf_flavio_pct": 25.0,
  "modelo_urna": "UE2020", "tipo_urna": 1, "tipo_arquivo": 1, "n_cargas": 1,
  "abertura_brasilia": "2026-10-04 08:00:01", "encerramento_brasilia": "2026-10-04 17:04:12",
  "recebido_tse": "2026-10-04 18:55:55",
  "casada_2022": true, "lula_2022_pct": 88.1, "flavio_2022_pct": 10.2,
  "criterios": ["a", "b"], "detalhe": {"a": {"candidato": "lula", "pct": 95.0, "excesso_zona_pp": 12.9}},
  "pontuacao": 6, "pontuacao_iguais": 2, "nivel": "alta", "nivel_iguais": "media",
  "grupo_explicacao": "exige_explicacao_documental",
  "explicacao_codigos": ["zona_rural"],
  "explicacao_provavel": "zona rural (inferido pelo cadastro do local)",
  "enclave_2022": false, "sem_boletim": false,
  "o_que_conferir": "...",
  "contexto": ["ctx-057"],
  "link_mapa": {"osm": "https://www.openstreetmap.org/?mlat=-3.32123&mlon=-45.01234#map=17/-3.32123/-45.01234",
                "google": "https://www.google.com/maps?q=-3.32123,-45.01234"}
}
```

- `lula_2022_pct` e `flavio_2022_pct`: % dos votos nominais de presidente no 1º turno de
  2022 na mesma seção (Bolsonaro no lugar de Flávio); `null` quando a seção não casa.
- `detalhe`: um objeto por critério disparado, com os números que o dispararam.
- `explicacao_codigos` (regra declarada em `meta.explicacoes_comuns`): `aldeia`, `presidio`,
  `exterior`, `transito`, `minuscula` (menos de 50 votantes) formam o grupo
  `comum_documentada`; `zona_rural`, `quilombo_assentamento`, `hospital`, `pequena` (50 a 99
  votantes), `urna_trocada` e `enclave_2022` são explicação provável, mas não tiram a seção do
  grupo `exige_explicacao_documental`. É inferência por palavra-chave no cadastro, não
  verificação.
- `contexto`: ids de `contexto_seguranca.json` (coerção, facção ou milícia, violência,
  logística remota, urnas substituídas) que citam o município; lista vazia quando nenhum cita.
- `sem_boletim`: `true` só nas 20 do critério h(1); nelas os campos de voto são `null`.
- `pontuacao`: soma dos pesos dos critérios disparados (`meta.pesos`). `nivel`: alta com
  pontuação 5 ou mais e grupo `exige_explicacao_documental`; média com 3 ou mais (ou 5 ou mais
  com explicação comum); baixa no resto. `enclave_2022` força baixa.
- `pontuacao_iguais` e `nivel_iguais`: peso 1 para todo critério; alta com 3 critérios ou
  mais, média com 2, baixa com 1 (mesma regra de grupo e de enclave).

## 4. Agregados

`por_uf` (as 28 UFs, exterior `ZZ`):
`{uf, regiao, secoes_universo, secoes, alta, media, baixa, locais, locais_alta, aptos_secoes,
pontuacao_soma, criterios: {id: n}}`.

`por_municipio`: a união dos 100 primeiros por pontuação somada e dos 100 primeiros por número
de seções sinalizadas: `{uf, municipio, mun_tse, ibge, secoes_universo, secoes, alta, media,
baixa, locais, aptos_secoes, pontuacao_soma, lula_pct, flavio_pct, margem_flavio_pp,
criterios: {id: n}, contexto: [{id, tema}], top_pontuacao: bool, top_secoes: bool,
posicao_pontuacao, posicao_secoes}`. `lula_pct`, `flavio_pct` e a margem são do município
inteiro (universo), não só das sinalizadas.

`por_zona`: toda zona com ao menos uma seção sinalizada: `{uf, municipio, mun_tse, zona,
secoes_universo, secoes, alta, media, baixa, pontuacao_soma, aptos_secoes, posicao_anomalias,
congelada}`; `posicao_anomalias` é a posição em `anomalias.json` (`topo`) ou `null`.

## 5. `Local` (`por_local`)

Um local de votação com várias seções sinalizadas vale mais: a lista agrupa por `local_id`,
ordenada por pontuação somada.

```json
{"local_id": "MA-07307-20-1104", "uf": "MA", "municipio": "CAJARI", "mun_tse": "07307",
 "ibge": "2102408", "zona": 20, "local_nr": 1104, "local": "...", "endereco": "...",
 "bairro": "...", "cep": "...", "lat": -3.32123, "lon": -45.01234,
 "tipo_local_inferido": "...", "secoes_local": 8, "secoes": 3, "lista_secoes": [45, 46, 50],
 "alta": 1, "media": 1, "baixa": 1, "nivel": "alta", "pontuacao_soma": 12, "pontuacao_max": 6,
 "aptos_local": 2400, "aptos_secoes": 900, "lula_pct": 80.1, "flavio_pct": 15.2,
 "criterios": {"a": 2, "b": 1}, "contexto": ["ctx-057"], "link_mapa": {"osm": "...", "google": "..."}}
```

`nivel` do local = o mais alto entre as seções dele; `lula_pct` e `flavio_pct` somam todas
as seções do local (sinalizadas ou não).

## 6. `prioridade_pl`

```json
{
  "leitura": "fiscal evita erro e intimidação dos dois lados ...",
  "geral": {"criterio": "...", "locais": [LocalCurto], "municipios": [MunCurto]},
  "protege_flavio": {"criterio": "...", "regra_municipio": "Flávio venceu ou perdeu por até 5 pp",
                     "municipios_elegiveis": 0, "secoes": 0, "aptos": 0,
                     "locais": [LocalCurto + {indice}], "municipios": [MunCurto + {indice}]},
  "vigia_lula": {"criterio": "...", "secoes": 0, "excesso_votos_lula": 0,
                 "locais": [LocalCurto + {excesso_votos_lula}], "municipios": [...]}
}
```

- `geral`: os 200 locais e os 100 municípios de maior pontuação somada.
- `protege_flavio`: só seções sinalizadas em municípios onde Flávio venceu ou perdeu por até
  5 pp dos válidos (universo); `indice` = soma de pontuação × aptos da seção, por local e por
  município; 200 locais e 100 municípios.
- `vigia_lula`: seções sinalizadas com Lula acima do resto da zona; `excesso_votos_lula` =
  (Lula % na seção menos Lula % no resto da zona) × válidos da seção / 100, somado por local e
  por município; 200 locais e 100 municípios.
- `LocalCurto`: `{local_id, uf, municipio, zona, local, endereco, bairro, lat, lon, secoes,
  nivel, pontuacao_soma}`; `MunCurto`: `{uf, municipio, mun_tse, secoes, alta, media,
  pontuacao_soma, flavio_pct, lula_pct}`.

## 7. `sensibilidade`

`{regra, matriz: [{nivel_pesos, nivel_iguais, secoes}], mudam_nivel, spearman_pontuacao,
top100_locais_comum, top100_municipios_comum, leitura}`.

## 8. `resumo`

```json
{"secoes_universo": 0, "secoes_sinalizadas": 0,
 "por_nivel": {"alta": {"secoes": 0, "locais": 0, "municipios": 0, "aptos": 0, "aptos_locais": 0}},
 "por_criterio": {"a": 0},
 "eleitorado": {"aptos_universo": 0, "aptos_sinalizadas": 0, "pct_sinalizadas": 0.0,
                "aptos_locais_sinalizados": 0, "pct_locais": 0.0},
 "fiscais": {"um_por_local": {"alta": 0, "alta_media": 0, "todos": 0},
             "um_por_secao": {"alta": 0, "alta_media": 0, "todos": 0},
             "dois_por_secao_maximo_legal": {"alta": 0, "alta_media": 0, "todos": 0},
             "base_legal": "Lei 9.504, art. 65, §§ 1º e 4º (fechamento.json, fontes_legais)"},
 "explicacao_comum": {"secoes": 0, "por_codigo": {"aldeia": 0}, "baixa_aldeia_presidio": 0},
 "enclaves_2022": 0, "sem_coordenada": {"secoes": 0, "locais": 0}}
```

`aptos_locais`: aptos de todas as seções dos locais sinalizados (o que um fiscal por local
enxerga). `um_por_local` conta locais; `um_por_secao` conta seções.

## 9. `mapa`

```json
{"colunas": ["lat", "lon", "nivel", "n_secoes", "pontuacao", "local"],
 "pontos": [[-3.32123, -45.01234, "alta", 3, 12, 0]],
 "n_locais": 0, "n_sem_coordenada": 0,
 "tiles": "https://tile.openstreetmap.org/{z}/{x}/{y}.png", "zoom_detalhe": 17}
```

Um ponto por local com coordenada; `local` é o índice em `por_local` (nome, endereço, seções
e links saem de lá). Coordenadas com 5 casas.

## 10. `zonas_congeladas`

`{uf, municipio, mun_tse, zona, ultima_incompleta_utc, primeira_completa_utc, horas_parada,
secoes_faltando, secoes_identificadas, conferem: bool}`: arquivos de zona de presidente cuja
última versão incompleta (gerada depois das 17h de Brasília de 04/10) ficou publicada 6 horas
ou mais antes da versão completa. `secoes_identificadas` = boletins da zona recebidos depois
da última versão incompleta; `conferem` diz se bate com `secoes_faltando` (ts menos st).

## Exportáveis (`meta.exportaveis`)

- `docs/assets/fiscais_2026.csv`: uma linha por seção de `secoes`, mesma ordem; `;` como
  separador, vírgula decimal, UTF-8 com BOM (abre direto no Excel em português).
- `docs/assets/fiscais_2026_por_local.csv`: uma linha por local de `por_local`.
- `docs/assets/fiscais_2026.xlsx`: abas "Leia-me", "Seções" (mesmas linhas de `secoes`),
  "Locais", "Municípios", "UFs" e "Critérios"; cabeçalho congelado e em negrito, filtro
  automático, links clicáveis, nível com cor de fundo.

Cada um com `linhas`, `bytes` e `sha256`, para o capítulo linkar o download.

## Mudanças

Toda mudança de chave já publicada fica registrada aqui, com data e motivo.

- 06/10/2026, versão 1.0.
