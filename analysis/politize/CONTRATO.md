# Politize sua vizinhança: contrato entre motor de dados, textos e aplicativo

Página: `docs/politizesuavizinhanca.html` (publicada em `https://brasil.arvor.co/politizesuavizinhanca.html`).
Aplicativo estático: HTML + CSS + JS puros, sem framework e sem build, servido pelo GitHub Pages.
Toda a inteligência roda no navegador sobre arquivos JSON fixos gerados por script. Nunca editar JSON à mão.

Ideia em uma frase: o eleitor digita **UF, zona e seção** (o que está no título de eleitor e no e-Título),
ou o CEP, ou escolhe cidade e bairro, ou usa a localização do aparelho, e recebe um **boletim da
vizinhança**, no formato de mapa astral, dizendo em quais locais de votação ao
redor dele o voto ainda está em disputa, com quem conversar (perfil do eleitorado), sobre o que conversar
(tema que dói no estado) e quantas conversas fazem diferença. O lado é declarado: a página é escrita para
quem quer eleger Flávio Bolsonaro no 2º turno de 25/10/2026. O método é o mesmo da casa: tudo
reproduzível, cada número com fonte, limites escritos ao lado do número.

## Regras de texto (valem para JSON, HTML e JS)

- pt-BR, sem travessão, nunca. Frase curta, verbo forte.
- "estimativa" e "teto endereçável" como vocabulário para o que é modelo; "medido" para o que vem da urna.
- Nunca "fraude". Nunca sugerir boca de urna, propaganda no dia, pressão ou assédio. Conversar é com vizinho,
  família e colega, antes do dia 25/10; a página cita a regra do TSE sobre propaganda no dia da eleição.
- O voto é secreto. Toda leitura é agregada por seção e local de votação (TSE publica assim). Nenhum número
  descreve uma pessoa. Essa frase aparece no app, nos limites e no card.
- "eleitorado de X" ou "quem votou em X", nunca "eleitores dele".
- Candidatos: `Flávio` (Flávio Bolsonaro, nº 22), `Lula` (nº 13). Terceira via = soma dos demais nominais.

## Unidade de análise

Duas camadas, sempre as duas: a **seção** (a urna da pessoa; é o que ela digita) e o **local de votação**
(escola, igreja, clube) = a vizinhança, que soma as seções do mesmo endereço. Entrada principal do app:
UF + zona + seção (decisão do Leonardo em 07/10/2026: "as pessoas acham mais fácil"). O boletim mostra os
números da seção, os do local e a vizinhança ao redor. Métricas, índice e arquétipo são calculados nas duas
camadas, com a mesma fórmula; a seção tem 200 a 400 eleitores, então a página diz que o número da seção é
mais ruidoso e usa o local como leitura principal da conversa.

**Local de votação** (escola, igreja, clube) = a vizinhança. Chave `local_id` = `"UF-MUNTSE-ZONA-LOCALNR"`
(ex.: `"SP-71072-1-1015"`), como em `CONTRATO_FISCAIS.md`. Seções agregadas somam na principal.
Universo: locais do cadastro `data/outputs/locais_votacao_2026.sqlite` cujas seções principais têm boletim
em `apuracao/data/secoes_2026.sqlite` (cargo 1, presidente). Exterior (`ZZ`) entra com a coordenada da cidade (ver
seção "Exterior").

## Fontes (todas já no disco; o build grava bytes, sha256 e data de cada uma em `indice.json`)

| chave | caminho | uso |
|---|---|---|
| boletins_2026 | `apuracao/data/secoes_2026.sqlite` (tabelas `voto_secao`, `bu_cargo`, `bu`) | votos de presidente 1º turno 2026 por seção, aptos, comparecimento |
| locais_2026 | `data/outputs/locais_votacao_2026.sqlite` | local, endereço, bairro, CEP, lat/lon, eleitores por seção |
| presidente_2022 | `data/outputs/presidente_secao_2022.csv.gz` | Lula e Bolsonaro 1º e 2º turno 2022 por seção, local_nr_2022 |
| perfil_secao_2026 | `data/raw/tse_eleitorado/perfil_eleitor_secao/perfil_eleitor_secao_2026_<UF>.zip` (download em curso; AC já existe) | sexo, faixa etária, escolaridade por seção |
| perfil_zona_2026 | `data/raw/tse_eleitorado/perfil_eleitorado_2026.zip` (`perfil_eleitorado_2026_<UF>.csv`, por zona) | fallback do perfil quando a UF não tem arquivo por seção |
| censo_setores | `data/raw/ibge_setores_2022/BR_setores_CD2022.gpkg` (R-tree, ponto a ponto) + `data/originals/censo_2022_setores_censitarios/Agregados_por_setores_basico_BR.csv` | situação urbana/rural, tipo (favela, aldeia, prisão), bairro IBGE, pessoas e domicílios do setor |
| pnad_2025 | `data/outputs/base_anual_visita1_labeled_npv.csv` (PNADC anual 2025, visita 1, pessoas 16+, peso `V1032`) | distribuição de renda domiciliar por UF × escolaridade × situação |
| pesquisas_renda | `analysis/reponderacao/pesquisas/datafolha_2026-10-03.json` e `quaest_2026-10-03.json` | voto por faixa de renda (1º e 2º turno) para o voto esperado pelo perfil |
| problemas_uf | `analysis/voto_util/problemas_quaest_092026.json` | problema mais grave por estado (Quaest), tema de conversa |
| salario_minimo | `data/originals/salario_minimo.csv` | R$ 1.621 em 2026 para as faixas em SM |
| malha_municipal | `apuracao/public/geo/mun/<UF>.geojson` | contorno dos municípios para o mapa do app |

Censo 2022 **não publica renda por setor**; a renda da vizinhança é estimativa pela PNAD a partir da
escolaridade do eleitorado (TSE) e da situação do setor (IBGE). Isso fica escrito na página.

## Métricas por local (tudo calculado no build, em Python; o JS só lê e formata)

Base dos percentuais declarada no nome: `_v` = % dos válidos (nominais dos candidatos), `_a` = % dos aptos.

```
aptos, secoes, comparecimento, abstencao = aptos - comparecimento
flavio, lula, terceira, brancos, nulos           (votos 2026, 1º turno)
validos = flavio + lula + terceira
flavio_v, lula_v, terceira_v                     (% dos válidos)
flavio_a, lula_a, terceira_a, bn_a, abst_a       (% dos aptos; bn = brancos + nulos)
margem_v = flavio_v - lula_v

2022 (seções casadas por número e local_nr; `cobertura_2022` = aptos casados / aptos):
bolsonaro22_1t_v, lula22_1t_v, bolsonaro22_2t_v, lula22_2t_v, abst22_2t_a
reencontro_a = max(0, bolsonaro22_1t_a - flavio_a)   em % dos aptos (quem votou Bolsonaro em 2022 e
                                                       não votou Flávio em 2026, saldo agregado)
```

Perfil do eleitorado (shares em % do eleitorado do local; fonte `perfil_fonte` = `secao` ou `zona`):

```
sexo: {fem, masc}
idade: {a16_24, a25_34, a35_44, a45_59, a60}
escolaridade (4 grupos TSE): {fund_inc  = analfabeto + lê e escreve + fundamental incompleto,
                              fund_med  = fundamental completo + médio incompleto,
                              med_sup_inc = médio completo + superior incompleto,
                              superior  = superior completo}
```

Renda estimada (PNAD): tabela `pnad_renda.json` com, para cada UF × grupo de escolaridade × situação
(urbana, rural), a distribuição do rendimento domiciliar efetivo (VD5001, preços de out/2026 pelo IPCA,
pessoas de 16 anos ou mais, peso V1032) nas três faixas das pesquisas: `ate2` (até 2 SM = R$ 3.242),
`de2a5`, `mais5`; e a mediana em reais. Renda do local = mistura dessas linhas pelos shares de
escolaridade do local e pela situação do setor censitário do ponto. Campos: `renda_est: {ate2, de2a5,
mais5, mediana_brl}`, `renda_fonte: "pnad_por_escolaridade"`.

Voto esperado pelo perfil: `esperado_flavio_v` e `esperado_lula_v` = soma, por faixa de renda, de
`renda_est[faixa] × voto da faixa` nas pesquisas (média simples de Datafolha e Quaest de 03/10, 1º turno,
sobre válidos), **recentrada por UF**: para cada UF, `esperado = bruto + (urna da UF − média do bruto na
UF)`, médias ponderadas por válidos sobre os locais com renda estimada, de modo que a média do esperado em
cada UF seja igual à urna da UF (e, por consequência, a média nacional igual à urna do Brasil). A
recentragem remove o erro comum das pesquisas e a diferença entre estados e preserva só a estrutura por
renda dentro do estado (decisão de 07/10/2026: com deslocamento nacional único o vão virava geografia
regional, Nordeste +13,2 pp e Sul −10,9 pp). O exterior não tem PNAD e fica sem esperado. `vao_perfil_pp =
esperado_flavio_v - flavio_v` (positivo = Flávio rendeu abaixo do que o perfil de renda da vizinhança
sugere dentro do próprio estado).

Votos em aberto e local virável (espelho do site de referência, lado Lula, que publica "lugares de votação
onde só os brancos, nulos e abstenções já dariam pra virar"):

```
em_aberto = terceira + brancos + nulos + abstencao            (votos; quem votou e não escolheu os dois, mais quem não foi)
bna       = brancos + nulos + abstencao                       (votos; sem a terceira via)
viravel   = "flavio" se lula > flavio e bna >= lula - flavio   (só branco, nulo e abstenção já virariam o local)
          = "lula"   se flavio > lula e bna >= flavio - lula   (simétrico, publicado com o mesmo peso)
          = null nos demais casos
```
Agregados (`indice.json.nacional`, `ufs[]`, `uf/<UF>.json.totais`, `mun/*.json.totais`): `votos_em_aberto`,
`em_aberto: {terceira, brancos, nulos, abstencao}`, `em_aberto_por_origem: {abstencao, caiado, renan, cury,
zema, outros_nominais, nulos, brancos}`, `locais_viraveis_flavio`, `aptos_locais_viraveis_flavio`,
`locais_viraveis_lula`, `locais_com_boletim`, `secoes_com_boletim`. Por local e por seção, colunas
`em_aberto`, `bna`, `viravel`, `cury`, `renan`, `caiado`, `zema`, `outros_nominais`, `coord_fonte`.

### Índice de conversa (0 a 100) e componentes, em votos por 100 aptos

```
c_terceira  = terceira_a + bn_a                    (votou e não escolheu os dois)
c_ausentes  = 0.5 × abst_a                         (não foi; metade do peso, porque abstenção converte mal)
c_reencontro = reencontro_a                        (saiu do campo entre 2022 e 2026)
c_perfil    = max(0, vao_perfil_pp) × validos / aptos
potencial   = c_terceira + c_ausentes + c_reencontro + c_perfil
indice      = round(100 × min(1, potencial / 40))  (40 por 100 aptos = teto prático observado; registrar o p99 real no indice.json)
```

Conta do 2º turno na vizinhança (`conta_2t`): a terceira via (nominais fora dos dois) fica 30% sem
escolha (cruzamento agregado da Nexus de 21/09, p. 79: 40,4 Flávio, 28,4 Lula, 31 sem escolha) e o resto
divide-se 61% Flávio / 39% Lula (síntese de três fontes: série de 2º turno, matriz Nexus 28/09 e matriz
Datafolha 01/10, registrada em `analysis/predicao_2026`); logo `flavio_2t = flavio + 0,427 × terceira`,
`lula_2t = lula + 0,273 × terceira`. Brancos, nulos e abstenção não viram voto. Parâmetros em
`indice.json.parametros.transferencia_terceira = {sem_escolha: 0.30, flavio_entre_escolhem: 0.61}`; `faltam` = votos que Flávio precisa a mais para passar Lula no local
(0 se já passa); `conversas_para_virar` = `faltam` dividido por 0,35 (hipótese declarada: uma em cada
três conversas convence; `taxa_conversao` fica em `indice.json`). Quando `faltam` = 0: `conversas_para_
segurar` = abstenção esperada do próprio lado, `flavio_2t × abst22_2t_a/100`.

Percentis: `percentil` = posição do `potencial` do local entre todos os locais do Brasil com boletim (0 a
100; 100 = maior potencial do país); para a seção, entre as seções com 30 aptos ou mais. `percentil_uf` =
posição dentro da própria UF. O exterior tem só `percentil_uf`, porque o potencial dele não tem c_perfil.
É o número da frase "esta vizinhança tem mais voto em disputa que X% dos locais do Brasil".

### Arquétipo (um por local; primeira regra que bate, nesta ordem)

| código | nome | regra |
|---|---|---|
| `fortaleza` | Fortaleza | `flavio_v >= 60` |
| `muro` | Muro | `lula_v >= 65` |
| `pendulo` | Pêndulo | `abs(margem_v) <= 6` |
| `reencontro` | Reencontro | `reencontro_a >= 5` |
| `fertil` | Terreno fértil | `terceira_v + bn_v >= 12` (bn sobre válidos para a regra) |
| `dormindo` | Dormindo | `abst_a >= 28` |
| `abaixo_do_perfil` | Abaixo do perfil | `vao_perfil_pp >= 5` |
| `frente` | Na frente | `margem_v > 6` (resto com Flávio à frente) |
| `atras` | Atrás | resto |

Também `arquetipo_secundario`: a próxima regra que bate (ou `null`). Os textos de cada arquétipo vêm de
`textos.json` (escritor). O motor só grava os códigos.

## Arquivos gerados (tudo em `docs/assets/politize/dados/`)

Convenção de compactação: cada lista de locais vem como `{"colunas": [...], "linhas": [[...], ...]}`.
`null` para ausência. Floats com 1 casa em `_v`/`_a`/`_pp`, inteiros em contagens.

1. `indice.json` (≈ 500 KB): `{gerado_em, versao_contrato: "1.0", fontes: [...], parametros: {taxa_conversao,
   transferencia_terceira, teto_potencial, recentragem: {metodo, por_uf: {UF: {esperado_bruto_flavio, urna_flavio, deslocamento_flavio_pp, ...}}}},
   nacional: {aptos, flavio_v, lula_v, ...}, ufs: [{uf, nome, aptos, flavio_v, lula_v, abst_a,
   n_locais, arquivo}], municipios: {"colunas": ["uf","mun_tse","ibge","nome","lat","lon","n_locais",
   "aptos","flavio_v","lula_v","arquivo"], "linhas": [...]}}`. `arquivo` = `"mun/SP/71072.json"`.
   Capitais e exterior incluídos. `nome` em caixa normal (não MAIÚSCULA) para busca e exibição.
2. `mun/<UF>/<mun_tse>.json` (um por município): `{uf, mun_tse, ibge, nome, totais: {... mesmas métricas
   do local, somadas ...}, perfil_fonte, locais: {"colunas": [...], "linhas": [...]}}`. Colunas do local,
   nesta ordem: `local_id, local_nr, zona, nome, endereco, bairro, cep, lat, lon, tipo_local, secoes,
   aptos, comparecimento, flavio, lula, terceira, brancos, nulos, flavio_v, lula_v, terceira_v, flavio_a,
   lula_a, terceira_a, bn_a, abst_a, margem_v, cobertura_2022, bolsonaro22_1t_v, lula22_1t_v,
   bolsonaro22_2t_v, lula22_2t_v, abst22_2t_a, reencontro_a, fem, a16_24, a25_34, a35_44, a45_59, a60,
   fund_inc, fund_med, med_sup_inc, superior, setor_situacao, setor_tipo, renda_ate2, renda_de2a5,
   renda_mais5, renda_mediana_brl, esperado_flavio_v, vao_perfil_pp, c_terceira, c_ausentes,
   c_reencontro, c_perfil, potencial, indice, arquetipo, arquetipo_secundario, flavio_2t, lula_2t,
   faltam, conversas_para_virar, conversas_para_segurar`.
   `setor_situacao` ∈ {`urbana`, `rural`, null}; `setor_tipo` ∈ {`comum`, `favela`, `aldeia`, `quilombo`,
   `prisao`, `militar`, `outro`, null}.
2b. `zona/<UF>/<zona>.json` (um por zona eleitoral, ≈ 2.640 arquivos; a zona é única dentro da UF):
   `{uf, zona, municipios: [{mun_tse, nome}], secoes: {"colunas": [...], "linhas": [...]}}` com, por seção
   principal: `secao, local_id, mun_tse, local, bairro, aptos, comparecimento, flavio, lula, terceira,
   brancos, nulos, flavio_v, lula_v, terceira_v, abst_a, bn_a, margem_v, cobertura_2022, bolsonaro22_1t_v,
   lula22_1t_v, bolsonaro22_2t_v, lula22_2t_v, reencontro_a, perfil_fonte, fem, a16_24, a25_34, a35_44,
   a45_59, a60, fund_inc, fund_med, med_sup_inc, superior, indice, arquetipo, faltam, conversas_para_virar,
   agregadas` (lista de números de seções agregadas nesta principal, ou `[]`). A busca por UF + zona +
   seção abre este arquivo; se a seção digitada for agregada, o app a resolve para a principal e avisa.
   O `indice.json` ganha `zonas: {"UF": [números de zona]}` para validar a digitação sem rede extra.
3. `cep/<2 primeiros dígitos>.json` (≈ 100 arquivos): `{"exato": {"01311000": ["SP-71072-1-1015", ...]},
   "prefixo5": {"01311": ["SP-71072-1-1015", ...]}}`. Só CEPs dos locais de votação; o app explica que a
   busca por CEP aproxima pelo CEP dos locais, não pelo endereço da pessoa.
4. `uf/<UF>.json`: `{uf, nome, regiao, totais, problemas: {pergunta, campo, valores, fonte, pagina} | null,
   municipios_mais_disputados: [...], ranking_indice: [top 20 locais por índice com ≥ 300 aptos]}`.
5. `geo/<UF>.geojson`: cópia da malha municipal (`codarea` = IBGE 7 dígitos).
6. `pnad_renda.json` (tabela intermediária, também publicada): `{faixas, salario_minimo_2026, mes_precos,
   linhas: [{uf, escolaridade, situacao, ate2, de2a5, mais5, mediana_brl, n_amostra, peso}]}`.

Relatório do build: `analysis/politize/relatorio_build.md` com cobertura (locais com voto, com 2022,
com perfil por seção vs zona, com setor), distribuição do índice (percentis), contagem por arquétipo,
e a conferência: soma dos votos de Flávio e Lula em todos os locais = soma do banco de boletins; e a
média do esperado recentrado = urna em cada UF (tolerância 0,05 pp).

## Scripts e testes

- `scripts/politize-build.py` (CLI; `--uf AC` para amostra rápida; `--so-pnad` para refazer a tabela;
  `--sem-setor` para pular o GeoPackage) com módulos em `scripts/politize/`: `fontes.py` (leitura),
  `pnad.py` (tabela de renda), `metricas.py` (funções puras, testáveis), `arquetipos.py`, `fragmentos.py`
  (escrita dos JSON), `relatorio.py`. Nenhum arquivo acima de 1.000 linhas. Stream-first.
- Caches intermediários em `analysis/politize/cache/` (ignorado pelo git): setor por local, perfil por local.
- `tests/test_politize.py`: métricas puras com números de brinquedo, regras de arquétipo em ordem, soma dos
  fragmentos de uma UF pequena (AC) contra o banco, contrato de colunas, ausência de travessão em todo texto.
- Lint zero: `ruff check scripts/politize scripts/politize-build.py tests/test_politize.py` e `black --check`.

## Textos (`docs/assets/politize/textos.json`, escrito pelo redator; o app interpola)

Placeholders entre chaves: `{nome}`, `{bairro}`, `{municipio}`, `{uf}`, `{flavio_v}`, `{lula_v}`, `{terceira_v}`,
`{abst_a}`, `{reencontro_a}`, `{vao_perfil_pp}`, `{indice}`, `{faltam}`, `{conversas}`, `{aptos}`,
`{renda_mediana}`, `{faixa_dominante}`, `{escolaridade_dominante}`, `{idade_dominante}`, `{problema_uf}`,
`{problema_uf_pct}`, `{arquetipo}`. O JS substitui, formata números com vírgula e aplica plural por regra
simples (`{conversas} conversa|conversas`).

Estrutura:
```
{
 "versao": "1.0",
 "arquetipos": {"fortaleza": {"nome", "signo" (emoji proibido; usar palavra), "lema", "leitura" (2 a 3 frases
     com placeholders), "o_que_fazer": [3 itens], "o_que_nao_fazer": [2 itens], "cor": "verde|amarelo|azul"}, ...},
 "componentes": {"c_terceira": {"rotulo", "explicacao"}, "c_ausentes": ..., "c_reencontro": ..., "c_perfil": ...},
 "perfil": {"escolaridade": {"fund_inc": {"rotulo", "como_conversar"}, ...}, "idade": {...}, "renda": {...}},
 "temas": {"Violência": {"abertura", "pergunta", "cuidado"}, "Saúde": ..., "Economia": ..., "Educação": ...,
           "Corrupção": ..., "Enchentes": ..., "Infraestrutura": ..., "Outros": ..., "default": ...},
 "conta_2t": {"virar", "segurar", "regra_transferencia"},
 "pagina": {"hero_titulo", "hero_em", "hero_deck", "como_funciona": [4 passos], "metodo": [...],
            "limites": [...], "privacidade": [...], "regras_tse": [...], "fontes": [...], "card_rodape"},
 "frases_compartilhar": [modelos para o texto do card, com placeholders]
}
```
Toda afirmação de método nos textos precisa bater com este contrato. Temas: a `pergunta` é uma pergunta
aberta para a conversa, o `cuidado` é o que não dizer. Nenhum tema nomeia caso, escândalo ou pessoa que não
esteja em documento do repositório.

## Aplicativo (`docs/politizesuavizinhanca.html`, `docs/assets/politize/app.js`, `app.css`)

- Sem dependência externa além das fontes do Google já usadas pela casa. Funciona só com `fetch` dos JSON
  (GitHub Pages). Em `file://` mostra aviso claro em vez de tela em branco.
- Fluxo: (1) entrada: **UF, zona e seção** em primeiro lugar e em destaque (três campos; a zona e a seção
  são números; validar a zona contra `indice.json.zonas`; dica "está no seu título de eleitor e no
  e-Título"), e, como alternativas, CEP (8 dígitos, com máscara), ou cidade (typeahead sobre `indice.json`, com UF) e
  bairro (lista do município), ou "usar minha localização" (Geolocation API; a coordenada não sai do
  aparelho). (2) resultado: pela seção, o boletim abre com um bloco **"Sua seção"** (seção, aptos, Flávio e
  Lula em votos e %, abstenção, 2022, índice e arquétipo da seção) seguido do bloco do **local** (a
  vizinhança, leitura principal) e dos 7 locais seguintes "ao redor"; pelos outros caminhos, o local
  mais próximo vira o boletim sem o bloco da seção. A URL ganha `#s=<UF>-<zona>-<secao>` quando a entrada
  foi por seção e `#l=<local_id>` nos demais casos, para compartilhar. (3) boletim no formato de mapa astral: a carta
  (SVG radial com os quatro componentes do potencial como setores e o índice no centro), o arquétipo com
  nome e lema, a leitura em prosa, "com quem conversar" (perfil), "sobre o que conversar" (tema do estado),
  "a conta do 2º turno" (faltam / conversas), a comparação com 2022, e a renda estimada com o rótulo de
  estimativa. (4) mapa da vizinhança: SVG com o contorno do município (`geo/<UF>.geojson`) e um ponto por
  local, cor pelo arquétipo, tamanho pelos aptos, o local escolhido destacado; clique troca o boletim.
  (5) card para compartilhar: `<canvas>` 1080×1080 renderizado no cliente, com download PNG e botão de
  copiar texto (modelo de `frases_compartilhar`), mais link do boletim. (6) rodapé metodológico com
  método, limites, privacidade, regras do TSE e fontes com hashes de `indice.json`.
- Visual: cores do Brasil (verde `#0b7a3b`/`#0f9d58`, amarelo `#f2c230`/`#ffcc29`, azul `#0d2238`/`#1f5f9e`,
  branco papel) sobre a tipografia da casa (Fraunces display, IBM Plex Sans Condensed, IBM Plex Mono).
  Contraste WCAG AA medido com `scripts/contrast-audit.py`; `scripts/render-audit.py` zerado.
- Mobile-first: largura de 360 px sem rolagem lateral; toque de 44 px; o mapa cabe na tela.
- Acessibilidade: `aria-live` no resultado, foco gerenciado, teclado no typeahead, texto alternativo no SVG.
- Desempenho: `indice.json` carregado uma vez; município e CEP sob demanda; `Cache-Control` do Pages.
  Nenhum número digitado à mão no HTML: tudo vem dos JSON.
- Análise de uso: nenhuma. Nada de rastreador.

## Exterior (`ZZ`)

O eleitorado no exterior entra inteiro, pela mesma entrada UF + zona + seção: a UF é `ZZ` ("Exterior", na
lista de UFs do app), a zona é sempre 1 e cada "município" do TSE é a cidade da embaixada ou do consulado
(186 cidades, 2.715 seções, das quais cerca de 1.300 principais com boletim; as demais são agregadas e
somam na principal). O cadastro não traz lat/lon para o exterior: o motor usa as coordenadas da cidade em
`apuracao/public/geo/exterior_cidades.json` (`cd` = código TSE do município, `lat`, `lon`, `pais`) para
todos os locais daquela cidade, grava `coord_fonte: "cidade"` (contra `"cadastro"` no Brasil) e copia
`apuracao/public/geo/mundo.geojson` para `dados/geo/ZZ.geojson`. O `uf/ZZ.json` traz `problemas: null`
e `regiao: "Exterior"`. No app, o mapa do exterior é o planisfério com um ponto por cidade; a busca por
CEP não cobre o exterior (os CEPs do cadastro são fictícios, como `11111111`) e a busca por cidade lista
as cidades do exterior com o país ao lado. Perfil: por seção quando `perfil_eleitor_secao_2026_ZZ.zip`
existir, senão por zona (`perfil_eleitorado_2026_ZZ.csv`). Renda estimada: a PNAD não cobre o exterior,
então `renda_est` e `c_perfil` são `null` no exterior e o índice usa os outros três componentes; a página
diz isso na ficha.

Seções muito pequenas (menos de 30 aptos, comuns no exterior e em aldeias): a camada da seção não mostra os
votos; o app mostra só o local e explica que a seção é pequena demais para leitura própria.

## Fora do escopo desta versão

Deputados e Senado; voto em trânsito (locais do tipo "Voto em trânsito" entram na lista por município, sem
peso no mapa); rotas; dados individuais de qualquer natureza.
