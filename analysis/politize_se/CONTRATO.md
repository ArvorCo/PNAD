# Politize-se: contrato entre motor de dados, frases, aplicativo e mapa

Página: `docs/politizese.html` (`https://brasil.arvor.co/politizese.html`; atalho `docs/politize-se/index.html`).
Pergunta do app: **entenda o que aconteceu na sua seção e no seu local de votação**, 1º × 2º turno de 2026.
Sucessor neutro do Politize sua vizinhança (`politizesuavizinhanca.html`, campanha do 2º turno, preservado como
arquivo com um aviso de uma linha no topo apontando para cá). Aplicativo estático, HTML + CSS + JS puros, sem
framework e sem build; toda conta roda no Python e o JS só lê, ordena por distância e formata.

## Regras de texto (JSON, HTML, JS)

- pt-BR corrente, sem travessão, nunca "fraude". Sem tom de campanha: a eleição acabou; é leitura pública.
- Rótulo fixo: **sinal pede explicação, não prova irregularidade**; a explicação provável vem antes de suspeita.
- Leitura agregada por seção, como o TSE publica. O voto é secreto; nenhum número descreve uma pessoa. Seção
  com menos de 30 aptos em qualquer turno não mostra votos, comparecimento nem biometria (só aptos).
- Sem presumir gênero ("quem votou", "o eleitorado"). Nenhum nome de pessoa além dos dois candidatos (Flávio,
  Lula). Frases geradas não citam o nome do local nem do município: o app mostra o nome do local como título,
  como está no cadastro do TSE. O card não traz nome de local (escolas levam nome de gente).

## Reprodução

```
python3 scripts/politize-se-build.py            # Brasil e exterior, ~95 s
python3 scripts/politize-se-build.py --uf AC    # amostra; mescla no índice existente
pytest -q tests/test_politize_se.py
python3 scripts/social-cards.py --only politizese
python3 scripts/sitemap-build.py
```

Módulos em `scripts/politize_se/`: `tempo.py` (horas em Brasília), `urna.py` (mesma urna nos dois turnos),
`textos.py` (frases por regra e modelos), `fontes.py` (leitura somente leitura, por UF), `montagem.py`
(seção, prédio, município), `saida.py` (JSON). Reexecutável a qualquer momento da coleta do 2º turno: cada
build relê o banco e marca a cobertura. Rodar de novo quando a coleta dos BUs terminar (perto das 03h50 de
26/10), depois de `--refazer-erros`/`--revisitar`, e quando os logs do 2º turno forem processados.

## Fontes (somente leitura; `indice.json.fontes` grava tamanho, data e SHA-256)

| chave | caminho | uso |
|---|---|---|
| boletins_2t | `apuracao/data/secoes_2t_2026.sqlite` (`?mode=ro`, `PRAGMA query_only`; em coleta) | `secao` (catálogo, `nsp`, `dr_hr`), `bu` (aptos, comparecimento, biometria, horários, urna, cargas, tipo de arquivo), `voto_secao` cargo 1 |
| boletins_1t | `apuracao/data/secoes_2026.sqlite` | biometria, horários, urna e carga do 1º turno; mapa número interno → seção |
| politize | `docs/assets/politize/dados/{zona,mun,fiscal,mudancas,cep}` | voto do 1º turno por seção, agregação do 1º turno, cadastro do local (nome, endereço, bairro, CEP, coordenada), fiscal recomendado, mudanças de local |
| regua_1t | `apuracao/data/referencia_1t_secoes.json` | régua dos sinais (mesma do dossiê) |
| logs_1t | `docs/assets/logs_urnas_2026/zona/<UF>/<zona>.json.gz` | sinais dos logs do 1º turno; nível 0 a 3 por `apuracao_logs.familias.atencao` |
| logs_2t | `docs/assets/logs_urnas_2t_2026/zona/<UF>/<zona>.json.gz` (sinais, bateria, `erro_mr_pre_zeresima`) e `data/outputs/logs_urnas_2t_2026.sqlite` (`metricas.resumo`: `partidas_dia`, `metadados_urna`, via `json_extract`) | campos `log2_*`; `indice.logs_2t.disponivel = true` desde 26/10 (regra 2 do critério de erro técnico) |
| clima | `docs/assets/fiscais_mapa/clima/<UF>.json` (1º turno observado, ERA5), `observado_2t.json` (chuva de 25/10 por célula de 0,25°: estação CEMADEN a até 50 km ou modelo ECMWF IFS provisório; `analysis/clima_2t_2026/CONTRATO.md`) e `previsao.json` (previsão da véspera, célula de 0,5°, campo secundário) | caixa de clima do prédio |

Fora desta versão (próximas camadas): RDV do 2º turno (`apuracao/data/rdv_2t_2026.sqlite`, só AC, AM, DF, ES,
RN, TO); governador nas seis UFs; trocas de urna com contexto nacional de `analysis/apuracao_2t_2026/dados/urnas.json`
(o build recalcula a classificação por seção pela mesma regra).

## Unidade e chaves

- **Seção principal** = chave (UF, zona, seção). Universo = principais do 1º turno (Politize) ∪ principais do
  2º turno (catálogo `secao` com `nsp` nulo, 0 ou igual à própria seção). Agregadas: `agregadas1` (Politize)
  e `agregadas2` (catálogo do 2º turno). `agreg_igual = false` avisa que a comparação é aproximada. O app
  resolve uma seção digitada que seja agregada para a principal (primeiro pela agregação do 2º turno).
- **Prédio** = `local_id` do Politize, `"UF-MUNTSE-ZONA-LOCALNR"` (local do 1º turno). Seção sem local no
  Politize usa o número do local do BU do 2º turno; sem nenhum, `"UF-MUN-ZONA-sem-local"`. `local_nr2` guarda
  o número do local no BU do 2º turno (difere quando a seção mudou de local).
- **Horários** em minutos desde a meia-noite de Brasília do dia do turno: fuso da UF + correção por município
  pela abertura modal às 8h (regra de `apuracao_2t_2026.secoes_fonte`). Exterior em hora local da cidade.
  Recebimento do BU (`dr_hr` do catálogo) já vem em Brasília; passa de 1440 depois da meia-noite.

## Arquivos (`docs/assets/politize_se/dados/`)

Listas compactas `{"colunas": [...], "linhas": [[...]]}`; `null` = ausência; taxas com uma casa; booleanos
como 0/1.

### `indice.json` (~600 KB)
`versao`, `gerado_em`, `rotulo`, `rotulos[]`, `cobertura {nacional {secoes, com_bu_2t, pct, banco_2t_bus,
banco_2t_principais, coleta_completa}, ufs {UF: {secoes, com_bu_2t, pct}}}`, `logs_2t {disponivel, nota}`,
`anomalia_ml {disponivel, secoes, anomalas, gerado_em, nota}` (mistura estatística dos dois turnos; `disponivel =
false` e os demais nulos enquanto o motor não gravar os dois arquivos), `ufs {UF: totais}`, `zonas {UF: [zonas]}`,
`municipios {colunas: [uf, mun_tse, nome, lat, lon, pais, nome_tse, n_locais, n_secoes, n_bu2, aptos, fatia_f1,
fatia_f2, arquivo]}`, `frases {código: modelo}`, `frases_codigos [códigos na ordem do índice numérico]`,
`catalogos {sinais, explicacoes, urna, fiscal_niveis, fiscal_criterios, log, log_rotina, log_familias, log_niveis,
mudanca, modelos_urna, clima2, clima2o, ml {k, rotulos {id: rótulo do grupo}, atipico (id do grupo atípico),
rotulo_casa}}`, `fontes[]`, `escopo`.

### `zona/<UF>/<zona>.json.gz` (um por zona; gzip com data zerada; 95 MB com a coleta completa do 2º turno e os logs, 26/10)
O app abre só este arquivo para uma seção (DecompressionStream, como os logs do 1º turno).
`{uf, zona, versao, gerado_em, cobertura {secoes, com_bu_2t}, municipios {mun_tse: {nome, ...totais}},
locais {colunas, clima1, clima2, linhas}, secoes {colunas, linhas}}`.

**Colunas da seção** (nesta ordem; 1º e 2º turno lado a lado):

| grupo | colunas |
|---|---|
| identidade | `secao`, `mun_tse`, `li` (posição do prédio em `locais.linhas`), `local_nr2`, `agregadas1`, `agregadas2`, `agreg_igual`, `pequena` |
| 1º turno | `aptos1`, `comp1`, `flavio1`, `lula1`, `terceira1`, `brancos1`, `nulos1`, `sem_bio1`, `ano_nasc1`, `hab_bio1`, `abert1`, `enc1`, `rec1`, `urna1`, `modelo1`, `tipo_urna1`, `cargas1` |
| 2º turno | `bu2` (0/1: boletim lido), `aptos2`, `comp2`, `flavio2`, `lula2`, `brancos2`, `nulos2`, `sem_bio2`, `ano_nasc2`, `hab_bio2`, `abert2`, `enc2`, `rec2`, `urna2`, `modelo2`, `tipo_urna2`, `cargas2`, `tipo_arquivo2` |
| taxas e deltas | `comp_pct1`, `comp_pct2`, `d_comp_pp`, `abst_pct1`, `abst_pct2`, `bn_pct1`, `bn_pct2` (% do comparecimento), `flavio_v1`, `lula_v1`, `terceira_v1` (% dos válidos do 1º turno), `fatia_f1`, `fatia_f2` (Flávio / (Flávio + Lula)), `d_fatia_pp`, `sem_bio_pct1`, `sem_bio_pct2`, `ano_nasc_pct1`, `ano_nasc_pct2` (% do comparecimento) |
| urna | `urna_situacao` (`mesma`, `mesma_recarga`, `reserva`, `nova`, `outra_secao_zona`, `outra_secao_municipio`, `outro_municipio`, `sem_1t`; regra em `politize_se/urna.py`), `contingencia2` |
| sinais 2T | `escore` (0 a 6), `sinais` (`delta`, `sem_bio`, `ano_nasc`, `salto_bio`, `tardia`, `papel`), `explicacoes` (chaves de `secoes_ranking.REGRAS_EXPLICACAO`) |
| fiscal 1T | `fiscal_nivel` (`maxima`, `alta`, `reforcada`, `padrao`), `fiscal_pontos`, `fiscal_sinais` (códigos de `fiscal/regras.json`), `c13_nivel` |
| logs | `log1_atencao` (0 a 3), `log1_sinais`, `log1_familias`, `log2_atencao`, `log2_sinais`, `log2_familias` (códigos de `apuracao_logs.familias`), `log2_reinicios` (`[[minuto de Brasília, votos antes, votos depois], ...]`, partidas do sistema na fase de votação), `log2_bateria` (`simultanea`, `isolada`, `votacao` ou `null`), `log2_bateria_simultaneas`, `log2_erro_mr` (avisos de problema ao desmontar a MR antes da zerésima: contexto, fora do erro técnico), `log2_meta` (`[versão do aplicativo, carga registrada em, série da MR]`) |
| estatística 1T × 2T | `ml_grupo` (0 a k−1, ou `null`), `ml_anomalo` (0/1: a seção está no grupo atípico do país; `null` sem dado), `ml_p` (parcela das seções do país com densidade menor, 0 a 1 com 4 casas; 0,01 = entre as 1% menos prováveis; `null` sem dado). Fonte: `data/outputs/apuracao_2t_2026/anomalia_secoes.json.gz` do motor (`analysis/apuracao_2t_2026/CONTRATO_ANOMALIA.md`), lido por `fontes.anomalia_ml(uf)`; exterior e seções com menos de 30 aptos ficam fora do motor e vêm `null` |
| mudança | `mudanca` (`null` ou `{cat, nome1, nome2, end2, bairro2, dist_m, motivo, url, fonte, real, maps}`) |
| texto | `frases` = `[[índice do código, arg0, arg1, ...], ...]` |

Identidades (testadas): `aptos = comparecimento + abstenção` e `comparecimento = Flávio + Lula (+ demais no
1º turno) + brancos + nulos` nos dois turnos, sempre que os campos estão presentes.

**Colunas do prédio** (`locais`): `local_id, mun_tse, nome, endereco, bairro, cep, lat, lon, secoes,
secao_link, n_secoes, n_bu2, aptos1, comp1, flavio1, lula1, terceira1, bn1, aptos2, comp2, flavio2, lula2,
bn2, comp_pct1, comp_pct2, comp_pct1_par, d_comp_pp, abst_pct1, abst_pct2, bn_pct1, bn_pct2, flavio_v1,
lula_v1, terceira_v1, fatia_f1, fatia_f1_par, fatia_f2, d_fatia_pp, escore_max, secoes_sinal, secoes_sinal2,
secoes_mudaram, urnas_trocadas, log2_atencao_max, secoes_log_subiu, secoes_log_persiste, secoes_log_reinicio,
secoes_log_bateria, secoes_anomalas, clima1, clima2, clima2o, frases`. Totais do 2º turno só sobre seções com BU lido;
`secoes_anomalas` conta as seções com BU do 2º turno no grupo atípico e fica `null` quando nenhuma seção do grupo
tem dado da mistura (sem o motor, o mapa pinta de cinza, não de "nenhuma");
`*_par` = 1º turno **sobre as mesmas seções**; deltas do prédio, do município e da UF usam o par (a cobertura
parcial não inventa variação). `clima1` = `[chuva_mm (horas de votação), chuva_dia_mm, faixa, rajada_kmh, pico,
urnas, urnas_bateria_votacao]`; `clima2` = `[chuva_mm, prob_pct, rajada_kmh, risco]` (previsão da véspera).
Totais do município (`municipios`) têm as mesmas chaves agregadas (`CAMPOS_TOTAIS` em `saida.py`).

### `mun/<UF>/<mun>.json` (um por município; JSON simples; **é o que o mapa do Brasil consome**)
`{uf, mun_tse, nome, versao, gerado_em, totais, locais {colunas, linhas}}`, um prédio por linha:
`local_id, zona, nome, endereco, bairro, cep, lat, lon, n_secoes, n_bu2, secao_link, aptos1, aptos2,
comp_pct1, comp_pct2, d_comp_pp, abst_pct2, bn_pct2, flavio2, lula2, fatia_f1, fatia_f1_par, fatia_f2,
d_fatia_pp, escore_max, secoes_sinal, secoes_sinal2, secoes_mudaram, urnas_trocadas, log2_atencao_max,
secoes_log_subiu, secoes_log_persiste, secoes_log_reinicio, secoes_log_bateria, secoes_anomalas, link`.

### `cep/<2 dígitos>.json`
Cópia do índice de CEP do Politize (`exato`, `prefixo5` → `local_id`): CEP dos locais de votação, não do eleitor.

## Contrato com o mapa do Brasil (próxima peça, base `docs/fiscais_mapa.html` formato 2)

Por prédio, sem abrir as zonas: lê `indice.json.municipios` (arquivo por município) e cada `mun/<UF>/<mun>.json`.
- **cor por resultado do 2º turno**: `fatia_f2` (Flávio entre os dois; Lula = 100 − fatia); `null` quando
  `n_bu2 = 0` (cinza, "2º turno ainda não lido");
- **variação contra o 1º turno**: `d_fatia_pp` (mesmas seções) e `d_comp_pp`;
- **abstenção**: `abst_pct2` (e `comp_pct2`);
- **sinal**: `escore_max` (0 a 6), `secoes_sinal`, `secoes_sinal2`; `urnas_trocadas`, `secoes_mudaram`;
- **logs do 2º turno** (novo em 26/10): `log2_atencao_max` (0 a 3), `secoes_log_subiu` (seções que foram de 0/1 no 1º
  turno para 2/3 no 2º), `secoes_log_persiste` (2/3 nos dois), `secoes_log_reinicio` (urna religada na votação),
  `secoes_log_bateria` (bateria na votação). As mesmas chaves entram em `totais` do município e da UF;
- **tamanho**: `aptos2` (ou `aptos1` sem BU);
- **link**: `politizese.html#uf=<UF>&z=<zona>&s=<secao_link>` (menor seção do prédio). O app também aceita
  `#uf=<UF>&z=<zona>&l=<local_id>` para abrir a ficha do prédio. Coordenada `null` (620 locais e exterior por
  cidade) vira só linha de lista, nunca ponto inventado.

## Frases geradas por regra (`politize_se/textos.py`)

O build decide quais frases valem e grava `[código, args formatados em pt-BR]`; os modelos ficam uma vez em
`indice.json.frases`; o app troca `{0}`, `{1}`... `textos.render()` é o mesmo algoritmo, usado nos testes.
- **Seção**, nesta ordem: pequena | ainda sem BU do 2º turno (+ resultado do 1º turno) | resultado do 2º turno,
  fatia entre os dois contra o 1º turno (igual abaixo de 0,5 ponto), comparecimento (igual abaixo de 1 ponto),
  brancos e nulos, biometria; horário do último voto nos dois turnos; recebimento do BU; situação da urna;
  contingência; sinais (0, 1 ou n) com a explicação provável ou o pedido de conferir ata e log; grupo da mistura
  estatística (`ml_atipico`: "Pela estatística dos dois turnos, esta seção está no grupo atípico do país: pede
  explicação, não prova irregularidade."; `ml_comum`: fora do grupo atípico; nada quando `ml_anomalo` é `null`);
  agregação mudada; mudança de local (categoria e distância); logs; nível de fiscalização do 1º turno.
- **Logs** (regra do coordenador, 26/10): atenção de 0/1 no 1º turno para 2/3 no 2º → "o nível de atenção do log
  subiu de X para Y", com os diagnósticos e o rótulo; mesma atenção nos dois turnos e alguma família em comum →
  "o mesmo sinal já aparecia no 1º turno" (mesmo nível sem família em comum: "o 1º turno tinha o mesmo nível de
  atenção, com outro tipo de sinal"); só rotina no 2º turno (com o nível do 1º quando era 2 ou 3); demais casos com
  o nível do 1º ao lado. Depois: reinício na votação (hora de Brasília, votos antes e depois), bateria na votação
  (simultânea ou isolada) e o aviso da MR antes da zerésima como rotina. Sem log do 2º turno, cai na frase do 1º.
- **Prédio**: cobertura parcial; resultado do 2º turno; variação da fatia nas mesmas seções contra a variação
  do município; comparecimento contra o município; seções com sinal e escore máximo; seções que mudaram de endereço;
  seções cujo log subiu para 2/3, que têm 2/3 nos dois turnos, com urna religada e com bateria na votação; seções
  no grupo atípico da estatística (`p_ml`, com concordância "está"/"estão"; só quando a contagem é maior que zero).

## Aplicativo (`docs/politizese.html`, `docs/assets/politize_se/app.js`, `app.css`)

- Cópia adaptada da busca do Politize (UF + zona + seção em primeiro lugar, CEP, cidade e bairro, localização),
  sem importar módulos do antigo. Zona validada contra `indice.zonas`. Em `file://`, aviso e busca desligada.
- Ficha da seção: cabeçalho (seção, zona, UF, local, endereço), selos, parágrafo gerado, barras dos dois
  turnos sobre os aptos, tabela 1º × 2º (aptos, votaram, comparecimento, abstenção, votos, brancos, nulos,
  fatia, biometria, primeiro e último voto, recebimento do BU, urna, tipo, cargas), barras de identificação,
  caixas de sinais, grupo estatístico (`blocoMl`: "No grupo atípico do país" ou "Fora do grupo atípico", grupo com o
  rótulo de `catalogos.ml`, densidade em palavras: `ml_p < 0,01` "entre as 1% menos prováveis do país", `< 0,05`
  "entre as 5% menos prováveis do país", senão "densidade comum"; sem dado, "a análise estatística dos dois turnos
  ainda não cobre esta seção"; sempre com `rotulo_casa`), urna, logs (atenção e famílias nos dois turnos, reinícios,
  bateria, MR, versão e carga), fiscal do 1º turno, mudança de local e clima; selo "grupo atípico" e linha no card e
  no texto compartilhável só quando `ml_anomalo`;
  "Neste prédio" com as seções lado a lado e o prédio contra o município; compartilhar (card 1080 × 1080 no
  canvas, sem nome de local; copiar texto; copiar link).
- Privacidade: a página **nunca escreve a seção no endereço** (o link é montado só quando pedido); o `#`
  é lido só ao abrir um link compartilhado. Geolocalização e CEP ficam no aparelho. Única medição: a tag do
  site (`scripts/ga_tag.py`).
  A contagem de relatos é pedida ao Supabase pela zona inteira (`uf` e `zona`), nunca pela seção; a seção
  só sai do aparelho quando a pessoa envia um relato (seção "Relatos" abaixo).
- Links: `apuracao_2T_2026.html` e `fiscais_mapa.html` (placeholder até o mapa novo).

## Limites (escritos na página)

Não diz como uma pessoa votou nem por que o comparecimento mudou; cobertura do 2º turno pode ser parcial;
clima do 2º turno vem de pluviômetro a até 50 km ou de modelo provisório, estimativa para a célula e não medição no prédio; o nível de fiscalização é a régua publicada antes do 2º turno, sem registro do
que cada fiscal conferiu; reinício da urna e bateria têm explicação técnica comum e só o log não diz a causa.

## Mapa do Brasil (`docs/politizese_mapa.html`, 26/10/2026)

Página escrita à mão; app em `docs/assets/politize_se_mapa/{app.js,app.css}` (Leaflet 1.9.4 e markercluster
1.5.3 do cdnjs com SRI, pontos em círculo desenhados em canvas); dados em `docs/assets/politize_se_mapa/`,
**formato 3** próprio (o app recusa outro). Substitui o placeholder `fiscais_mapa.html` nos links do Politize-se.

```
python3 scripts/politize-se-build.py          # primeiro o Politize-se (cobertura do 2º turno)
python3 scripts/politize-se-mapa-build.py     # depois o mapa, ~7 s; --uf AC mescla uma amostra
pytest -q tests/test_politize_se_mapa.py
python3 scripts/social-cards.py --only politizese_mapa
python3 scripts/render-audit.py http://localhost:4173/politizese_mapa.html
python3 scripts/contrast-audit.py http://localhost:4173/politizese_mapa.html
```

Módulos `scripts/politize_se/mapa_dados.py` (leitura de `indice.json`, `mun/<UF>/<mun>.json` e das listas de
seções de `zona/<UF>/<zona>.json.gz`; validação da coordenada; regra das seções pequenas; `CAMADAS`, texto da
interface) e `mapa_saida.py` (gravação). Reaproveita `apuracao_logs.mapa.tabela` por import.

- `indice.json`: `formato`, `gerado_em`, `fonte_gerado_em` (= `gerado_em` do Politize-se), `rotulos`,
  `cobertura` (copiada), `camadas`, `camada_padrao` (`resultado`), `catalogos {sinais, explicacoes, urna, log,
  log_familias, log_niveis, ml}`, `anomalia_ml` (copiado do Politize-se; `{disponivel: false}` sem o motor),
  `colunas_locais`, `colunas_municipios`, `resumo {locais, com_coord, sem_coord, com_bu2, secoes, secoes_bu2,
  aptos, bytes_ufs}`, `ufs {UF: {arquivo, bytes, contagens, municipios [[mun_tse, nome]]}}`, `zonas {UF: {zona:
  [lat, lon, n]}}`.
- `uf/<UF>.json`: `municipios` (totais da cidade para "prédio contra a cidade") e `locais`, um prédio por linha:
  `id, nome, endereco, bairro, cep, lat, lon, aprox, n_secoes, n_bu2, secao_link, secoes, aptos1, aptos2,
  comp_pct1, comp_pct2, d_comp_pp, abst_pct2, bn_pct2, fatia_f1_par, fatia_f2, d_fatia_pp, escore_max,
  secoes_sinal, secoes_mudaram, urnas_trocadas, secoes_anomalas, modelo, modelos, log1_max, log2_max, log_subiu,
  chuva2_*`. Zona e município saem do `id`. Sem BU do 2º turno, os campos
  do 2º turno e as variações ficam `null` (cinza no mapa); prédio ou município com menos de 30 eleitores não
  mostra voto nem comparecimento; coordenada fora do território vira `null` (só lista); exterior tem `aprox = 1`
  (ponto da cidade do consulado).
- `cep/<2 dígitos>.json`: `exato` e `p5` → `[lat, lon, n]`, média dos locais de votação com o CEP.
- Camadas: resultado do 2º turno (`fatia_f2`), mudança contra o 1º turno (`d_fatia_pp`), mudança do
  comparecimento (`d_comp_pp`), abstenção (`abst_pct2`), sinais (`escore_max`), urna trocada, mudança de
  endereço (esta não depende do BU), modelo da urna, registro da urna do 2º turno, mudou entre os turnos, chuva do
  dia e **grupo atípico (estatística)** (`anomalia`: tipo `presenca`, campo `secoes_anomalas`, `precisa_bu2` e
  `precisa_ml`; cor neutro → roxo `#6b4a92`, teto de parcela 0,25 no grupo de pontos; a explicação diz que o grupo
  foi definido por mistura estatística sobre as frações do eleitorado nos dois turnos, sem o exterior, e traz o
  rótulo da casa; prédio com `secoes_anomalas` nulo fica cinza, e a legenda avisa quando a análise ainda não entrou
  nos dados). Grupo de pontos: média ponderada pelos eleitores, ou parcela dos prédios
  com o atributo; a cor pura fica no anel e o miolo é clareado até o número passar 4,5:1.
- A ficha abre as seções direto de `zona/<UF>/<zona>.json.gz` (sem cópia): 1º → 2º turno de comparecimento,
  Flávio entre os dois e sem digital, sinais com a explicação provável; o botão "Entenda esta seção no
  Politize-se" abre `politizese.html#uf=&z=&s=` da seção escolhida (padrão: `secao_link`).
- Endereço da página: `uf`, `mun`, `zona`, `q`, `camada`, `raio`, `modo`, `l` (prédio). Nunca o CEP, a
  localização nem a seção. Entradas: botão no topo do Politize-se e "Este prédio no mapa" na ficha
  (`politizese_mapa.html#uf=&l=`), botão no capítulo de seções do dossiê (`pagina_cap_secoes.BOTAO_MAPA`, depois
  do mapa do ranking), uma etiqueta no destaque do Politize-se da home; card `politizese_mapa`.

## Relatos (26/10/2026)

Bloco "Notou algo na sua seção? Conte para a gente" na ficha da seção, logo depois da ficha principal
(`blocoRelato` em `app.js`). A pessoa escolhe o tipo, o turno, a hora aproximada (opcional), escreve o texto,
diz se viu ou soube por outra pessoa e, se quiser retorno, deixa e-mail ou telefone. Aviso de uma frase:
relato anônimo por padrão, contato só se informado, uso para análise e possível retorno, texto nunca publicado.

**Caminho.** Navegador → Edge Function `receber-relato` (`totalizacao/supabase/functions/receber-relato/`,
validação pura em `totalizacao/src/relato/validar.ts`, testes `totalizacao/tests/relato.test.ts`) →
`registrar_relato(jsonb)` (service_role) → tabela `relato_secao` (migração
`totalizacao/supabase/migrations/0005_relatos_secao.sql`, projeto Supabase PNAD). Configuração pública
(URL e chave publicável) reaproveitada de `docs/assets/totalizacao/config.js`.

**Esquema de `relato_secao`.** `id`, `criado_em` (do servidor), `turno` (1 ou 2), `uf` (27 UFs e `ZZ`),
`zona`, `secao` (1 a 9999), `local_id` (opcional, mesmo formato do Politize-se e da mesma UF),
`secao_no_cadastro` (a seção existe em `secao_ref`; relato fora do cadastro é gravado e marcado, não
recusado), `tipo` (enum `relato_tipo`: `fila_longa`, `urna_trocada`, `biometria_falhou`,
`votou_sem_biometria`, `mesario_conduta`, `boca_de_urna`, `transporte_irregular`, `local_mudou`,
`secao_fechou_cedo`, `secao_fechou_tarde`, `outro`), `texto` (1 a 1.000 caracteres, sem caracteres de
controle nem inversão bidirecional), `hora_aproximada` (HH:MM, opcional), `presenciou` (bool), `contato`
(opcional; e-mail em minúsculas ou telefone como `+55DDDNÚMERO`), `ip_hash` (SHA-256 de
`SAL_IP|relato|dia UTC|IP`; o sal vem de `supabase secrets` e o IP nunca é gravado), `user_agent` (só
sistema e navegador, sem versão: `android/chrome`), `origem` (`politize-se`), `versao` (do app), `desafio_hash` (migração 0006), `status`
(enum `relato_status`: `novo`, `lido`, `descartado`; uso interno). Os tipos estão iguais na migração, no
validador, no app e no exportador (`tests/test_politize_se_relatos.py`).

**Barreiras contra robô, sem terceiros (decisão de 26/10: sem Cloudflare/Turnstile).** Validação em
`totalizacao/src/relato/desafio.ts` e `validar.ts`, testes em `totalizacao/tests/relato_desafio.test.ts`.
1. **Desafio próprio**: no primeiro toque no formulário o app faz `GET receber-relato?desafio=1`; a função
   devolve `carimbo_ms.aleatório.HMAC-SHA256(SAL_IP)`, válido por 10 minutos. Quem só lê a ficha não chama a função.
2. **Tempo mínimo**: o carimbo do desafio é a abertura; envio com menos de 8 s volta 400 ("envio rapido
   demais"). O carimbo é assinado, então trocá-lo invalida o desafio.
3. **Prova de trabalho**: o aparelho procura, num Worker com SHA-256 em JS puro, um `nonce` decimal tal que
   `sha256(desafio + nonce)` comece com 18 bits zero (cerca de 262 mil tentativas em média; 0,1 s num
   computador e alguns décimos a poucos segundos num celular), com a barra curta "conferindo...". A função confere com um hash só.
4. **Campo-armadilha** `website`, fora da tela por CSS e com `aria-hidden`: ausente volta 400; preenchido volta
   200 `aceito` sem gravar.
5. **Uso único**: `desafio_hash` (SHA-256 do desafio) é único na tabela (migração 0006); reuso volta 409.

**Limites.** Cinco relatos por `ip_hash` na última hora, conferidos dentro de `registrar_relato` sob lock do
próprio `ip_hash` (envios simultâneos não furam o limite); o sexto volta HTTP 429. O IP vem do primeiro item de
`x-forwarded-for` posto pela plataforma (um cabeçalho forjado pelo cliente não burla o limite: conferido em
26/10). O hash troca à meia-noite UTC, então a janela recomeça na virada do dia. Corpo até 8 KB; só aceita
`Origin` de `brasil.arvor.co`, `localhost:4173` e `127.0.0.1:4173`. A resposta é só `{status, motivo}`, sem eco
do texto ou do contato; o log da função grava só o código do erro, porque a mensagem do Postgres repete a
linha recusada. Essas barreiras encarecem o robô, não o impedem: quem gastar CPU e trocar de IP ainda envia.

**Segurança.** RLS ligado em `relato_secao` e `relato_moderacao`, nenhuma policy; `anon` não lê a tabela nem
executa a função (conferido: HTTP 42501 nas duas). `service_role` só tem `select, insert` (sem `update`,
`delete` nem `truncate`, que pularia o trigger). Conteúdo imutável por trigger: `delete` falha e `update` só
passa quando muda apenas `status`; cada troca grava `relato_moderacao` (`de`, `para`, `em`, `papel`), também
imutável. Funções com `search_path = public, extensions`.

**O que é público.** Só duas views, lidas com a chave publicável: `v_relatos_resumo` (UF, tipo, turno, n) e
`v_relatos_secao` (UF, zona, seção, tipo, turno, n). Nenhuma traz texto, contato, hora, `ip_hash` ou
navegador, e as duas excluem `descartado`. O app mostra "N relatos nesta seção" com a divisão por tipo e
avisa que o texto não é publicado. Uma contagem não é verificação: o relato é declaração de quem enviou.

**Moderação e análise.** `python3 scripts/politize-se-relatos.py` (`--status novo`, `--desde ID`) exporta
JSON e CSV para `analysis/politize_se/relatos/`, ignorada pelo git, com o token do CLI do Supabase no keychain
(nunca a chave publicável). `--marcar lido|descartado ID...` troca o status. Texto bruto e contato nunca vão
para `docs/`. Qualquer número publicado a partir dos relatos sai de contagem, com o rótulo de que relato
pede explicação e não prova irregularidade; nenhum texto é citado sem revisão e sem retirar dados pessoais.
- **Modelo da urna (26/10/2026)**: os arquivos por zona já trazem `modelo1` e `modelo2` (de `bu.modelo_urna`
  de cada turno; o Politize-se não guarda `modelo_fonte`), então o build do Politize-se não mudou. O build do
  mapa conta, por prédio, as seções por modelo (`modelos` = `[[modelo, n], ...]`, do maior para o menor) e grava
  `modelo` = o único modelo do prédio, ou `misto` quando há mais de um. Modelo da seção = o do 2º turno quando o
  boletim já foi lido, senão o do 1º (`mapa_dados.modelo_secao`). `indice.modelos_urna {nacional, ufs}` traz
  seções por modelo e prédios por modelo (com `misto` e `sem_dado`), usados na legenda da camada `modelo`
  (tipo `categoria`, uma cor por modelo de UE2009 a UE2022 e âmbar para misto). A ficha mostra o modelo de cada
  seção nos dois turnos com "mesma urna nos dois turnos" ou "urna trocada" (de `urna_situacao`); a lista e o
  CSV têm o modelo predominante (o de mais seções) e a contagem do prédio. Na ficha da seção do Politize-se,
  a caixa "A urna" abre com o modelo dos dois turnos e "Mesma urna nos dois turnos" ou "Urna trocada".
- **Registro da urna do 2º turno no mapa (26/10/2026)**: o build do mapa lê, por seção, `log1_atencao`,
  `log2_atencao`, `log2_familias`, `log2_reinicios` e `log2_bateria` dos arquivos por zona e grava por prédio
  `log1_max`, `log2_max` (nível 0 a 3 mais alto; `null` sem registro lido) e `log_subiu` (seções que estavam em 0
  ou 1 no 1º turno e foram a 2 ou 3 no 2º). `indice.logs_2t` = o bloco do Politize-se mais `predios_com_log`,
  `predios_por_nivel`, `predios_subiu` e o mesmo por UF. Camadas `log2` ("Sinais nos logs, 2º turno", cores e
  nomes dos níveis do mapa de fiscais: Registro de rotina, Um sinal no log, Sinais combinados, Conferir o
  arquivo) e `log_subiu` ("Mudou entre os turnos"); prédio sem registro lido fica cinza. A ficha mostra por seção
  nível 1º → 2º turno, famílias, reinícios na votação com o horário e bateria na votação; lista e CSV trazem o
  nível máximo dos dois turnos e as seções que subiram. Numa amostra (`--uf`), o índice de CEP não é regravado
  (prefixos de CEP atravessam estados) e as contagens por UF são mescladas.

## Mudanças de esquema (registro para o mapa)

- **26/10/2026, grupo atípico da mistura estatística dos dois turnos** (`analysis/apuracao_2t_2026/CONTRATO_ANOMALIA.md`,
  seção 7). Seção: acrescentadas `ml_grupo`, `ml_anomalo`, `ml_p` depois de `log2_meta` e antes de `mudanca`. Prédio
  (zona), prédio no arquivo do município e totais (município e UF): acrescentada `secoes_anomalas` depois de
  `secoes_log_bateria` (na zona, antes de `clima1`; no município, antes de `link`). Índice: `anomalia_ml {disponivel,
  secoes, anomalas, gerado_em, nota}` e `catalogos.ml {k, rotulos, atipico, rotulo_casa}`; fontes `anomalia_ml_indice`
  e `anomalia_ml_secoes` (registradas com `existe: false` enquanto o motor não grava). Frases novas `ml_atipico`,
  `ml_comum` e `p_ml`. Mapa do Brasil: coluna `secoes_anomalas` em `colunas_locais` (depois de `urnas_trocadas`) e em
  `colunas_municipios` (no fim), camada `anomalia`, `indice.anomalia_ml` e `catalogos.ml` copiados; o app bumpou
  `VERSAO` para `20261026e`. Tudo degrada sem os arquivos do motor: campos nulos, `disponivel = false`, camada em
  cinza, build sem erro (o CI não tem os arquivos pesados). Leitura por nome de coluna, nunca por posição.

- **26/10/2026, logs do 2º turno.** Seção: acrescentadas `log1_familias`, `log2_familias`, `log2_reinicios`,
  `log2_bateria`, `log2_bateria_simultaneas`, `log2_erro_mr`, `log2_meta`; `log2_atencao` e `log2_sinais` agora
  preenchidos. Prédio (zona e município) e totais: acrescentadas `log2_atencao_max`, `secoes_log_subiu`,
  `secoes_log_persiste`, `secoes_log_reinicio`, `secoes_log_bateria`, antes de `clima1` na zona e antes de `link` no
  município (o mapa deve ler as colunas pelo nome, nunca pela posição). Índice: `logs_2t.disponivel = true`,
  `catalogos.log_niveis`, `catalogos.log_familias[*].curto`, fontes `logs_2t_indice` e `logs_2t_metricas`. Banco de
  BUs do 2º turno completo (499.207 seções principais) e dados regerados.

- **26/10/2026, chuva do 2º turno.** Prédio (zona): acrescentada `clima2o` depois de `clima2`, com
  `locais.clima2o = [chuva_mm (07h às 18h de Brasília), fonte_votacao, chuva_dia_mm (00h às 24h), fonte_dia,
  rajada_kmh, n_estacoes, dist_km, fonte]`; fontes `cemaden`, `inmet`, `ambos`, `ifs_provisorio` ou `era5`;
  índice `catalogos.clima2o` com `gerado_em`, `fonte`, `rotulos_fonte`, `raio_km`, `cortes` e `nota`. A ficha mostra
  primeiro a chuva do dia ("chuva medida em estações CEMADEN a X km" ou "modelo, provisório") e deixa a previsão
  da véspera como linha secundária. Mapa do Brasil: colunas `chuva2_mm`, `chuva2_vot_mm`, `chuva2_fonte`,
  `chuva2_fonte_vot`, `chuva2_dist_km`, `chuva2_n` no fim de `colunas_locais`, camada `chuva2` ("Chuva no dia do
  2º turno", 0 a 40 mm), filtro "Só prédios com chuva forte no dia do 2º turno" (`chuva_dia_mm ≥ 20`, `#chuva=1`),
  bloco "No dia do 2º turno" na ficha e `indice.clima2`/`indice.chuva_forte_mm`. Sem `observado_2t.json` os campos
  ficam nulos e o mapa segue.

## Economia e segurança compartilhadas (28/10/2026)

`python3 scripts/politize-se-mapa-build.py` também publica `contexto/<UF>.json` e
`contexto/indice.json` no diretório do mapa. `politize_se/territorio.py` lê os fragmentos
municipais do Politize anterior e `data/outputs/fiscais_risco_municipios.csv`, somente
para leitura. A junção usa o `local_id` completo para renda/escolaridade e UF + código
TSE com zeros à esquerda para segurança. Prédio novo sem perfil conserva renda nula;
exterior não recebe as bases brasileiras. Não transporta índices de campanha.

- Renda: valores já publicados pelo modelo PNADC anual 2025 × escolaridade TSE ×
  situação do setor, preços de julho/2026. Mediana estimada e faixas domiciliares
  até 2, 2–5 e mais de 5 salários de R$ 1.621. Não é renda medida no bairro nem
  renda por pessoa. As barras acomodam o arredondamento sem mudar os números.
- Escolaridade: perfil do eleitorado; origem por seção, zona ou combinação de ambas
  registrada no município. Não apresentar o fallback por zona como medição do prédio.
- Homicídios: Atlas da Violência/SIM 2024, óbitos por residência, contagem, taxa por
  100 mil e quintil entre municípios com dado. Nulo permanece nulo, nunca zero.
- Crime organizado: documentação municipal com fonte e período originais. Sem registro
  positivo não comprova ausência. Não usar favela, terra indígena ou quilombo como
  indicador de criminalidade; não transportar o escore territorial editorial para esta régua.

Mapa: camadas `renda`, `renda_ate2`, `homicidios`, legenda visível também no celular,
valores nos rótulos dos pontos no zoom de quarteirão e colunas no CSV. Na camada de
homicídios, agrupamentos usam média simples das taxas dos municípios distintos, sem
repetir uma cidade pelo número de prédios; é resumo das taxas, não taxa regional.
Renda usa a média das estimativas dos prédios ponderada pelo eleitorado, declarada na
legenda. Não condiciona contexto à presença do boletim do 2º turno.

`assets/politize_se/territorio.{js,css}` renderiza ambas as páginas, carregando contexto
por UF sob demanda. Fichas mostram distribuições de renda/escolaridade, régua municipal
de homicídios, contagem, ano, fontes e limites. Erro de carga oferece nova tentativa
sem impedir os dados eleitorais. `relatos.js` e `politize_se_mapa/ficha.js` separam as
interfaces antigas para manter os arquivos abaixo de mil linhas.

Validação: `tests/test_politize_se_territorio.py` confere os novos campos de todos os
prédios contra os fragmentos de contexto e a fonte municipal, além de nulos, zeros,
exterior e prédios novos. Testes de navegador em `tmp/politize-territorio/` (rascunhos
locais, fora da publicação) cobrem desktop, celular, camadas e ligação prédio/seção.

## Filtros de horário no mapa (28/10/2026)

`politizese_mapa.html` tem seletores independentes para encerramento no boletim e
último voto computado no log do 2º turno. Cada um aceita qualquer horário, até
17:15:00 inclusive, após 17:15:00 ou sem horário utilizável. O cruzamento é uma
interseção na mesma seção; o prédio só aparece se alguma seção passar. O placar
soma todos os votos do dia dessas seções, sem atribuir candidato a voto individual.
O último voto não equivale ao encerramento formal.

- Fonte dos segundos: bancos locais `secoes_2t_2026.sqlite` e
  `logs_urnas_2t_2026.sqlite`. Não usar os horários arredondados a minuto nos
  fragmentos anteriores. Conversão municipal para Brasília por `deslocamentos`,
  conferida contra a hora modal de abertura dos boletins. Inclui Acre (+2 h) e
  Fernando de Noronha (−1 h). Data dos boletins: 25/10/2026.
- Último voto exige log processado, relógio válido, identidade/carga confirmadas e
  contagem igual ao comparecimento do boletim. Exterior não é classificado nesse
  corte nacional. Dados ausentes ou inconsistentes não entram em “até”.
- Exportador `scripts/politize-se-horarios-build.py`, motor
  `scripts/politize_se/horarios.py`; arquivos compactos por UF em
  `docs/assets/politize_se_mapa/horarios/`, com colunas explícitas, índice, hashes,
  contagens e identificação dos bancos de origem. Atualizar após a coleta e o
  build do Politize-se. Alternativa conjunta: `politize-se-mapa-build.py --horarios`.
- Foto de 28/10: encerramento até/após = 488.813/9.084 seções; último voto até/após
  = 494.959/2.790. Dos 1.499 registros sem último voto classificável no mapa,
  1.310 são exterior, 41 não têm boletim do 2º turno, 141 têm inconsistência de
  relógio, cinco de contagem e dois não têm log. Todos os boletins estão no mapa.
- `horarios.js` seleciona e recompõe os valores eleitorais, sinais, modelos e
  seções do prédio. Mudanças entre turnos usam as mesmas seções e agregação
  compatível. Não modifica o objeto original. Proteção de seções pequenas
  mantida na exportação e na recomposição. Contexto de renda, chuva e homicídios
  continua do prédio/município; referência eleitoral da cidade é completa.
- Hash: `enc=ate|apos|sem` e `ultimo=ate|apos|sem`. CSV mantém as colunas anteriores
  e acrescenta critérios, números das seções e os dois horários com segundos.
  A ficha só lista as seções selecionadas e mostra os dois horários em Brasília.
- Testes em `tests/test_politize_se_horarios.py`: fronteira de um segundo, fusos,
  exclusões, ausência versus zero, privacidade, cruzamento, recomposição, hashes
  e correspondência integral entre seções do mapa e arquivos de horários.
- Validação desta implementação: 32 testes do mapa, horários e território passaram;
  lint e sintaxe JavaScript aprovados. Playwright conferiu desktop, celular,
  ficha de prédio com seleção parcial, CSV, restauração do link, limpeza e
  contagens nacionais (494.959 até/2.790 após pelo último voto; 9.084 após pelo
  encerramento), sem erros JavaScript. Capturas locais em `tmp/horarios-mapa/`.

## Movimento horário e visões de zona/município (28/10/2026)

- `python3 scripts/politize-se-movimento-build.py` lê o histograma horário do
  banco de métricas dos logs do 2º turno. Pode ser chamado junto aos builds
  principais com `politize-se-build.py --movimento` ou
  `politize-se-mapa-build.py --movimento`. Não reabre microdados nem persiste
  identificadores de eleitores. Saída compacta por UF em
  `docs/assets/politize_se/movimento/`; índice com hashes, cobertura e totais.
- Faixas de uma hora, em Brasília, dia 25/10/2026. Fuso municipal derivado pela
  mesma regra de `logs_cadencia.deslocamentos` usada nos filtros de encerramento
  (inclui +2 no Acre e −1 em Fernando de Noronha). Cada seção exige relógio e
  histograma válidos, contagem reconciliada e pelo menos 30 aptos nos turnos
  publicados. O exportador confirma a soma contra o comparecimento do fragmento
  público. Exterior fica sem gráfico comparável. `null` não é uma hora com zero.
- Foto desta versão: 497.668 de 499.248 seções, 127.816.305 cômputos nos gráficos.
  Exclusões disjuntas: 81 seções pequenas, 141 relógios inconsistentes, cinco
  contagens inconsistentes, dois logs ausentes e 1.351 registros do exterior
  (incluindo 41 sem boletim do 2º turno). O índice registra esses motivos.
- `movimento.js` é compartilhado por mapa e Politize-se. Soma contagens antes
  de obter pico e percentuais. Declara todos os empates; não escolhe uma hora
  arbitrária. O total e a cobertura do gráfico dizem respeito aos logs
  utilizáveis, enquanto o placar eleitoral da ficha mantém seu universo de BUs.
  Gráfico interativo por toque/foco, tabela das 24 horas e opção de escolher
  uma seção dentro do local. As barras são relativas ao pico do próprio recorte.
- Mede eventos de voto computado, não fila, ocupação do local, intenção de voto
  nem previsão de movimento. A barra das 17h engloba 17:00–17:59; não representa
  o corte exato de 17h15. A visualização horária é exclusivamente do 2º turno,
  explicitado no cabeçalho, mesmo quando a ficha eleitoral compara dois turnos.
- Mapa: camada `pico`, atalho “Horários”, legenda e rótulo no ponto. Nos grupos,
  o pico vem da soma dos histogramas das seções representadas, nunca da média
  das horas dos prédios. `enc`/`ultimo` filtram as seções antes da agregação.
  Horários são carregados sob demanda; cerca de 6,5 MB gzip para todo o país.
  Na lista, a camada inclui coluna ordenável de pico e cobertura; o CSV exporta
  pico, seções cobertas, seções do recorte e contagens das 24 horas em Brasília.
- Politize-se: `visoes.js` implementa zona e município com placar dos dois
  turnos, cobertura, movimento, lista pesquisável de locais e links relacionados.
  Município usa seus totais publicados; zona soma as contagens dos locais do
  seu fragmento, sem somar percentuais nem repetir totais municipais inteiros.
  Zona e município não formam uma árvore: os links abrem recortes inteiros e
  explicam que podem se cruzar. Seção e local têm navegação para ambos.
- Rotas: `#uf=CE&z=26&visao=zona` e
  `#uf=CE&mun=14672&visao=municipio`. Links antigos de seção/local preservados.
  Busca por cidade sem bairro agora abre o resumo municipal; com bairro mantém
  a aproximação por local. Botão “Ver a zona” exige UF/zona, sem exigir seção.
- Código reorganizado para manter arquivos abaixo de 1.000 linhas:
  `compartilhar.js` contém o card da seção; `geodesia.js` contém a distância do
  mapa, com a fórmula anterior preservada. Testes em
  `tests/test_politize_se_movimento.py`; capturas em `tmp/movimento/`.

### Encerramento e último voto em destaque (29/10/2026)

- Dois filtros independentes, sempre visíveis acima do mapa, selecionam seções
  pelo encerramento do BU (`enc`) e último cômputo do log (`ultimo`). Cada um
  aceita até, após, sem horário ou qualquer horário; o corte é editável em HH:MM,
  no horário de Brasília. Até inclui HH:MM:00; após exige segundo maior.
- Links antigos conservam o corte 17:15. Cortes novos usam `enc_h`/`ultimo_h`,
  por exemplo `#uf=CE&camada=ultimo_voto&ultimo=apos&ultimo_h=17%3A00`.
  Horários inválidos no link voltam ao padrão explícito 17:15. O CSV registra
  os dois cortes além dos horários exatos por seção. As contagens do índice de
  dados continuam sendo a referência original de 17:15, não um recálculo do filtro.
- `ultimos.js` acrescenta as camadas `ultimo_voto` e `encerramento`. Cada ponto
  usa o horário mais tardio **utilizável** das seções representadas; grupos também
  usam o mais tardio conhecido, nunca média nem categoria modal. Ausências não
  viram zero. A ficha e a lista mostram cobertura por relógio e deixam claro que
  o horário resumido não pertence necessariamente a todas as seções do prédio.
- Faixas de cor: até 16h; depois de 16h até 16h30; depois de 16h30 até 17h;
  depois de 17h até 17h15; depois de 17h15 até 17h30; depois de 17h30 até 18h;
  após 18h. A legenda e os rótulos declaram o critério. Filtros são aplicados
  antes do máximo, da cor e da recomposição dos votos do prédio.
- A antiga lente “Horários” passa a se chamar “Pico de votos”. Sua distribuição
  permanece na ficha, em um painel expansível, após a tabela com os horários
  individuais. Último voto e encerramento são apresentados separadamente.
- Conferência no Ceará: 955 seções com último cômputo >17:00:00; oito >17:15:00.
  Com último cômputo >17:00:00 e encerramento <=17:30:00, restam 950. São seções,
  não quantidades de votos após esses horários. QA em `tmp/ultimos-mapa/`.

## Grupos armados e cartografia territorial (29/10/2026)

- `python3 scripts/politize-se-seguranca-build.py` exporta o conjunto independente
  `docs/assets/politize_se/seguranca/`, sem regravar votos, chuva ou horários.
  O cliente compartilhado `seguranca.js` aparece nas fichas de seção, prédio,
  zona e município. O mapa oferece `crime`, `controle` e `influencia`, com links
  compartilháveis, legenda, lista e colunas documentais no CSV.
- Presença municipal: 367 municípios, com fontes individuais; 343 nomes
  associados ao TSE entre os 344 do FBSP/Instituto Mãe Crioula, Cartografias
  da Violência na Amazônia 2025, quadros 3.2–3.10. Amanã/AM permanece sem
  correspondência, conforme a auditoria da base anterior. Não interpretar os
  demais municípios como ausência de grupos, nem pintar polígonos municipais
  como domínio territorial. As fontes de imprensa são registros distintos do
  levantamento do FBSP e mantêm suas datas.
- Revisão da transposição: `ctx-034`, Diário do Nordeste de 29/09/2026, cita
  Sobral e Juazeiro do Norte como sedes de gabinetes de segurança. Essas duas
  cidades não recebem presença positiva só por essa referência. Permanecem os
  quatro municípios com relatos de extorsão no contexto descrito. `ctx-033`,
  Gazeta do Povo de 24/09/2026, relaciona vinte municípios do RJ. Ambas as páginas
  foram relidas em 29/10/2026; o acervo anterior é preservado, a correção aplica-se
  à nova camada. Temas genéricos de violência/coerção não entram automaticamente.
- Controle e influência: imagens originais GENI/UFF e Fogo Cruzado, território
  de 2024, relatório publicado em dezembro de 2025. Fonte e widget preservados
  em `data/originals/analise_realidade_eleicao/`. As imagens PNG são extraídas
  sem alteração; seus hashes coincidem com o manifesto original. A sobreposição
  Leaflet usa os limites Web Mercator publicados, a mesma projeção da interseção.
  Não é um levantamento territorial nacional nem atualização da situação de 2026.
- Interseções apenas em pontos cadastrais do RJ cuja coordenada coincide com a
  base-fonte. Não exigir BU completo para contexto geográfico. Resolução próxima
  de 34 × 37 m; classe `Sem marcação` distinta de `null` (fora da janela ou sem
  coordenada confirmada). Controle e influência são separados, nunca somados.
  Grupos de pontos com categorias diferentes usam cor neutra, sem atribuir ao
  conjunto a categoria majoritária. Pontos próximos da borda recebem ressalva.
- Os filtros de horários selecionam seções e placares; não recortam a cartografia
  original. Escola não identifica residência de eleitores nem demonstra vínculo
  com grupo, coação, fraude ou causa do voto. Fontes, datas e limites aparecem
  junto aos resultados. Proveniência e hashes ficam no conjunto público.
- Validação: `tests/test_politize_se_seguranca.py` confere fontes, as duas exclusões,
  cobertura FBSP, hashes, paridade com as interseções auditadas e categorias
  ausentes/mistas no cliente. QA de ambas as páginas, quatro níveis geográficos,
  sobreposição, troca de camadas e telas móveis em `tmp/seguranca-politize/`.
