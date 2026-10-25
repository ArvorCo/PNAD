# Apuração 2026 ao vivo

Subprojeto local para a noite de 04/10/2026. Faz três coisas:

1. **coletor**: lê a divulgação oficial do TSE (`resultados.tse.jus.br/oficial`) em camadas, com GET condicional e detecção de mudança pelo monitoramento `-ab`;
2. **SQLite de auditoria**: grava todo snapshot com o corpo original (gzip), a hora de geração do arquivo no TSE, a hora da totalização, a hora da nossa leitura e o hash, e cada requisição, mudada ou não, no log `fetch`. É a prova dos tempos e movimentos da apuração;
3. **telão**: uma página 1920 × 1080 sem rolagem para a live (OBS), com mapas em três níveis (UF, município, zona) e todas as eleições, comandada por teclado ou por um diretor em segunda janela.

Roda só no Mac, sem nenhuma fonte externa em tempo de execução. Stack: TypeScript, Bun 1.3, `bun:sqlite`, zero lint e zero erro de tipo.

## Arquivos do TSE

Base `https://resultados.tse.jus.br/oficial`, ciclo `ele2026`, pleito `3220`. Todos os números chegam como texto com vírgula; o parser converte.

| Arquivo | URL | Conteúdo |
|---|---|---|
| Índice | `/comum/config/ele-c.json` | eleições **6257** Federal (cargo `1` Presidente), **6259** Estadual (`3` Governador, `5` Senador, `6` Dep. Federal, `7` Dep. Estadual, `8` Dep. Distrital), **6261** Municipal (`25`, só Fernando de Noronha). 2º turno: 6258 / 6260 |
| Municípios | `/ele2026/{ele}/config/mun-e00{ele}-cm.json` | `abr[]` (27 UFs + `zz`) com `mu[]`: `cd` (TSE), `cdi` (IBGE), `nm`, `c` (capital), `z[]` (zonas) |
| Monitoramento BR | `/ele2026/{ele}/dados/br/br-e00{ele}-ab.json` | por UF: `dt/ht`, `munnr/munpt/munf`, seções `s{}`, eleitorado `e{}` |
| Monitoramento UF | `/ele2026/{ele}/dados/{uf}/{uf}-e00{ele}-ab.json` | por município; é o detector de mudança |
| Resultado | `/ele2026/{ele}/dados/{abr}/{abr}-c000{cargo}-e00{ele}-u.json`, `{abr}` = `br`, `{uf}`, `{uf}{mun5}` ou `{uf}{mun5}-z{zona4}` | `dg/hg/idg` (geração), `dt/ht` (totalização), `tf`, `carg[]` com candidatos, `s{}`, `e{}`, `v{}` |
| Agregado por UF | `/ele2026/{ele}/dados/{uf}/{uf}-c000{cargo}-e00{ele}-e.json` | 404 em 2026 até agora; sondado a cada 600 s |
| Simplificado | `dados-simplificados/*-r.json` | 404 em 2026; não usado |
| Seções | `/ele2026/arquivo-urna/3220/config/{uf}/{uf}-p003220-cs.json` | só metadado; boletim de urna fora do escopo |

`idg` é contador global monotônico: arquivo que chega com `idg` menor que o anterior é cópia velha do CDN, fica arquivado com `regressivo = 1` e não vira versão atual.

## Arquitetura

```
TSE (Akamai) ── GET condicional, gzip ──▶ coletor (bun run collect) ──▶ data/apuracao.sqlite (WAL, escritor único)
                                                                              │ leitura (readonly)
                                          servidor (bun run serve) ◀──────────┘  API JSON + SSE /events
                                                  │
                    telão http://127.0.0.1:4180/#v=pres        diretor http://127.0.0.1:4180/director.html
```

- `src/collector/`: fila por prioridade, limitador (token bucket), HTTP com classificação por corpo, agendador em camadas T0 a T3, varredura a cada 30 min, saúde em `meta.estado_coletor`.
- `src/db/`: esquema, escrita em lote, leitura. `src/parse/`: zod `passthrough`, números, drift, normalização.
- `src/server/`: API de leitura, SSE por sondagem do `snapshot.id` a cada 500 ms com `Last-Event-ID`, estáticos de `public/`.
- `src/ui/`: telão em TypeScript puro e SVG, sem framework. `src/director/`: diretor por `BroadcastChannel('apuracao')`.
- `src/replay/`: sequenciador que regrava fixtures ou um banco no mesmo formato do coletor.

O telão fala com o servidor por `src/ui/data/api.ts`, que normaliza o ingresso: siglas de UF em caixa alta, `estado.br` nulo vira zeros, anomalias pela categoria (as operacionais ficam fora do ar) e o exterior fora de `config.ufs`. Os eventos `snapshot` (kind `resultado`, `ab`, `config`), `evento` (kind `anomalia`) e `estado` (batimento a cada 5 s) chegam por `src/ui/data/sse.ts`, que assina `/events?tudo=1`. Sem evento por 90 s, o telão sonda a cada 30 s; nunca fica em branco.

## Comandos

```bash
bun install                 # dependências
bun run assets              # malhas do IBGE, fontes, campos.json, fotos (já rodado em 03/10)
bun run sweep               # uma varredura completa contra o TSE, com resumo de classes e latências
bun run collect             # coletor (use scripts/start-collect.sh no dia)
bun run serve               # servidor em http://127.0.0.1:4180 (use scripts/start-serve.sh no dia)
bun run build:ui            # empacota telão e diretor em public/dist/
bun run check               # tsc + eslint + bun test
bun run scripts/semear-ensaio.ts         # banco de ensaio data/ensaio.sqlite (dados inventados)
bun run scripts/semear-ensaio.ts --mais 1  # acrescenta um passo com o servidor aberto (teste do SSE)
APURACAO_DB=data/ensaio.sqlite bun run serve
```

### Endereços do telão (tudo no hash)

| Hash | Uso |
|---|---|
| `#v=pres&auto=1&hud=0` | **browser source do OBS** (rotação automática, sem HUD) |
| `#v=pres&auto=0` | presidente fixo |
| `#v=pres-uf&uf=SP` | presidente com a malha municipal da UF |
| `#v=mun&uf=SP&mun=71072&z=1` | município com o cartograma de zonas |
| `#v=gov`, `#v=sen`, `#v=fed-uf&uf=SP`, `#v=est-uf&uf=SP`, `#v=dis-df`, `#v=ritmo`, `#v=mov` | demais telas |
| `#mock=1&speed=60` | apuração sintética determinística, sem banco |
| `#replay=2026-10-04T17:30:00-03:00,60` | relê o banco real pelo parâmetro `at=`, 60 vezes mais rápido |

### Teclado

| Tecla | Ação |
|---|---|
| `←` `→` | tela anterior e próxima |
| `espaço` | pausa a rotação; `a` volta ao automático |
| `1` `3` `5` `6` `7` `8` | cargos (códigos do TSE); `9` ritmo; `0` movimento |
| duas letras em 900 ms | UF (`s` `p` = São Paulo) |
| `Backspace` | sobe um nível (zona, município, UF, Brasil) |
| `/` | busca de município, candidato ou UF |
| `z` | liga e desliga as zonas no município; `↑` `↓` andam entre zonas |
| `f` tela cheia, `h` HUD, `m` variante, `r` recarrega os dados | |

O diretor (`/director.html`, segunda janela do mesmo Chrome) espelha a tela atual e manda navegação, pausa, dwell e HUD por `BroadcastChannel`. Precisa estar na mesma origem que o telão.

## API

Servidor em `http://127.0.0.1:4180`. Respostas JSON com `Cache-Control: no-store`; `at=` (ISO) em todos os endpoints de leitura devolve o estado naquele instante. Esquemas completos em `tests/api-schemas.ts`.

| Endpoint | Resposta |
|---|---|
| `GET /api/config` | `{turno, eleicoes:{federal,estadual}, ufs:[{uf,nome,cdi?,te}], municipios:{UF:[{cd,cdi,nm,c,z[],te?}]}}`; `ufs[].uf` em minúscula, chaves de `municipios` em caixa alta |
| `GET /api/estado` | `{agora, pronto, turno, coletor, db, ultimo_snapshot, br:{ts,st,pst,dt_ht,hg,lido_em,atraso_s,ultima_leitura_em,idade_s}\|null, ufs:[{uf,nome,pst,st,ts,munnr,munpt,munf,dt_ht,fechou_em?}], historico, latencias}` |
| `GET /api/resultado?ele&cargo&abr` | `{ele, cargo:{cd,nome,nome_f,nv}, tpabr, abr, nome_escopo, dg_hg, dt_ht, lido_em, tf, idg, snapshot_id, anterior_id, s, e, v, cand:[...], partidos:[...], candidatos_normalizados, blob_url}`; `snapshot_id=` pede uma versão |
| `GET /api/mapa?ele&cargo&nivel=uf\|mun\|zona&pai` | `{nivel, pai, gerado_em, unidades:[{cd,cdi?,nm,te?,pst,tf,snapshot_id,lider?,segundo?,margem?,top?}]}` |
| `GET /api/serie?ele&cargo&abr` | `{abr, pontos:[{at,snapshot_id,pst,cand:{sqcand:pvapn}}], viradas:[{at,snapshot_id,de,para}], candidatos:[...]}` |
| `GET /api/anomalias[?severidade&limit]` | `[{id, at, tipo, categoria:virada\|regressao\|fechou\|atraso\|outro, severidade, uf, abr, cargo, texto, detalhe, derivado}]` |
| `GET /events[?tudo=1\|nivel=br,uf,mun,zona]` | SSE: `snapshot` `{kind:resultado\|ab\|config, ele, cargo, abr, nivel, snapshot_id, at, pst, tf}`, `evento` `{kind:anomalia, ...}` (warn e error), `estado` `{agora, pronto, max_snapshot_id}` |
| `/api/snapshots`, `/api/latencia`, `/api/fim`, `/api/velocidade`, `/api/andamento`, `/api/fetches`, `/api/blob/:id` | auditoria: versões de um arquivo, latências, municípios que fecharam, velocidade, `-ab`, log de requisições e o JSON original |
| `/api/boletins*`, `/boletins/HHMM.mp3` | boletim falado do 2º turno (seção própria abaixo); únicas rotas com POST |

Estáticos: HTML, `dist/` e JSON com `Cache-Control: no-cache` (um `build:ui` durante a live chega no próximo recarregamento do OBS); `geo/`, `fonts/` e `fotos/` com `max-age=3600`.

## SQLite

`data/apuracao.sqlite`, WAL, `synchronous=NORMAL`, `foreign_keys=ON`, `busy_timeout=5000`. Esquema em `src/db/schema.sql`.

- Configuração: `meta`, `eleicao`, `cargo`, `uf`, `municipio`, `zona`, `partido`, `federacao`, `candidato`.
- Registro: `arquivo` (uma linha por URL, com etag, sha, idg, último snapshot, backoff).
- Log: `fetch` (toda requisição: status, classe, etag, `Date` do servidor, bytes, sha, se mudou).
- Corpos: `blob` (gzip, deduplicado por sha256). Versões: `snapshot` (`capturado_em`, `gerado_em`, `totalizado_em`, `idg`, `regressivo`, `anterior_id`).
- Séries: `totais`, `voto_candidato`, `voto_partido`, `voto_agremiacao`, `ab_estado`, `e_entrada`, `evento`.
- Views: `v_atual`, `v_snapshot_delta`, `v_voto_candidato_delta`, `v_municipio_fim`, `v_ab_atual`.

### Consultas de auditoria

```sql
-- Latência de captura (leitura menos geração) e de geração (geração menos totalização) por nível
SELECT nivel, COUNT(*) n, ROUND(AVG(latencia_captura_s),1) captura_media, ROUND(MAX(latencia_captura_s),1) captura_max,
       ROUND(AVG(latencia_geracao_s),1) geracao_media
FROM v_snapshot_delta d JOIN arquivo a ON a.id = d.arquivo_id
WHERE a.tipo = 'u' AND d.regressivo = 0 GROUP BY d.nivel;

-- Regressões: contagens que diminuíram entre versões consecutivas do mesmo arquivo
SELECT chave, capturado_em, d_st, d_vvc, d_tv FROM v_snapshot_delta
WHERE regressivo = 0 AND (d_st < 0 OR d_vvc < 0 OR d_tv < 0) ORDER BY capturado_em;

-- Cópias velhas do CDN (idg menor que o anterior)
SELECT a.chave, s.capturado_em, s.idg FROM snapshot s JOIN arquivo a ON a.id = s.arquivo_id WHERE s.regressivo = 1;

-- Hora em que cada UF fechou (presidente, 100% das seções)
SELECT a.uf, MIN(s.totalizado_em) fim FROM arquivo a
JOIN snapshot s ON s.arquivo_id = a.id AND s.regressivo = 0 JOIN totais t ON t.snapshot_id = s.id
WHERE a.tipo = 'u' AND a.cargo_cd = 1 AND a.nivel = 'uf' AND t.ts > 0 AND t.st = t.ts GROUP BY a.uf ORDER BY fim;

-- Municípios finalizados por UF e o último a fechar
SELECT uf, COUNT(*) finalizados, MAX(totalizado_em) ultimo FROM v_municipio_fim WHERE cargo_cd = 1 GROUP BY uf;

-- Movimento: votos ganhos por candidato a cada versão do arquivo nacional de presidente
SELECT d.gerado_em, c.nome_urna, d.vap, d.d_vap, ROUND(d.pvapn, 2) pct, d.dt_s
FROM v_voto_candidato_delta d JOIN arquivo a ON a.id = d.arquivo_id JOIN candidato c ON c.sqcand = d.sqcand
WHERE a.chave = 'u:6257:1:br:::' ORDER BY d.snapshot_id, d.vap DESC;

-- Desperdício do CDN: requisições por classe
SELECT classe, COUNT(*), SUM(bytes) FROM fetch GROUP BY classe;
```

## Runbook de 04/10 (horário de Brasília)

- **16:30** `scripts/preflight.sh`: Bun, `df` com pelo menos 40 GiB, `curl -sI` do `ele-c.json` (200 e etag), relógio contra `Date` (desvio abaixo de 2 s), sem pidfile velho, `PRAGMA quick_check`, `pmset -g` sem sono agendado.
- **16:40** `scripts/start-collect.sh`, depois `scripts/start-serve.sh`; abrir `http://127.0.0.1:4180/#v=pres`.
- **16:50** `/api/estado`: T0 fluindo, parcela de 304, filas, `pausa_global_ate` nulo, desvio pequeno.
- **17:00 em diante**, vigiar: `negado` e `limite` (devem ser 0), fila T2 (acima de 5.000 por mais de 5 min: `APURACAO_MIN_INTERVALO_MU=600`), `wal_mb` abaixo de 300, banco contra os 10 GB, `/api/anomalias?severidade=error`, `e_file_appeared`, `df -h` a cada hora.
- **Recuperação**: coletor cai, o laço reinicia e o estado volta do banco; 403, pausa automática, e à mão `APURACAO_UA=... APURACAO_CONCURRENCY=8`; disco, `APURACAO_SWEEP_MIN=0` e `APURACAO_ZONAS=final`; suspeita de corrupção, parar o coletor, `.backup`, `integrity_check`; servidor travado, reiniciar só ele (o telão segura o último snapshot e reconecta sozinho).
- **Depois**: `PRAGMA wal_checkpoint(TRUNCATE)`, cópia do banco, `bun run backfill`, `VACUUM` numa cópia para o relatório.

### O que fazer se

| Sintoma | Onde aparece | Ação |
|---|---|---|
| 403 ou 429 do TSE | `/api/estado` (`coletor.taxas_60s.negado` e `.limite`, `coletor.pausa_global_ate`), log `data/logs/collect-*.log` | a pausa é automática; se repetir, parar o coletor e religar com `APURACAO_UA="<UA de navegador atual>" APURACAO_CONCURRENCY=8 scripts/start-collect.sh` |
| fila T2 acima de 5.000 por mais de 5 min | `/api/estado` (`coletor.fila`) | `APURACAO_MIN_INTERVALO_MU=600` em `meta.ajustes` (a quente) ou na partida |
| disco abaixo de 40 GiB ou banco perto de 10 GB | `df -h`, `/api/estado` (`coletor.db_mb`, `coletor.wal_mb`) | `APURACAO_SWEEP_MIN=0` e `APURACAO_ZONAS=final`; WAL acima de 300 MB: conferir se algum leitor ficou preso (reiniciar o servidor libera o checkpoint) |
| telão parado ou servidor sem resposta | HUD do telão (`rede`), `curl -s 127.0.0.1:4180/api/estado` | reiniciar só o servidor (`pkill -f "src/server/main.ts"`; o `start-serve.sh` religa em 2 s). O coletor continua gravando e o telão segura o último dado e reconecta sozinho |
| coletor caiu | log com `"t":"reinicio"` | o laço do `start-collect.sh` religa e o estado volta do banco; se cair em ciclo, ler o último erro do log antes de qualquer outra coisa |
| suspeita de banco corrompido | erro de SQLite no log | parar o coletor, `sqlite3 data/apuracao.sqlite ".backup data/copia.sqlite"`, `PRAGMA integrity_check` na cópia; religar só com resultado `ok` |
| Mac dormiu ou sem rede | lacuna no log `fetch` | `pmset -g` e Wi-Fi; o coletor retoma sozinho, e a lacuna fica registrada como prova |

OBS: browser source 1920 × 1080 em `http://127.0.0.1:4180/#v=pres&auto=1&hud=0`, "atualizar navegador quando a cena ficar ativa" desligado. Diretor no segundo monitor, no mesmo Chrome do teste (o OBS tem o próprio Chromium: para comandar o OBS pelo diretor, abra o diretor como dock personalizado do OBS com a mesma URL).

## Ajustes

Por variável de ambiente na partida ou, a quente, em `meta.ajustes` (JSON com os mesmos nomes, relido a cada 10 s):

| Variável | Padrão | Efeito |
|---|---|---|
| `APURACAO_DB` | `data/apuracao.sqlite` | banco (coletor e servidor) |
| `APURACAO_PORT` | `4180` | porta do servidor |
| `APURACAO_ELEICOES` | `6257,6259,6261` | eleições coletadas (2º turno: `6258,6260`) |
| `APURACAO_CONCURRENCY` | `32` | requisições em voo |
| `APURACAO_UA` | navegador | User-Agent |
| `APURACAO_SWEEP_MIN` | `30` | minutos entre varreduras completas; `0` desliga |
| `APURACAO_SWEEP_RPS` | `40` | teto da varredura avulsa (`bun run sweep`) em requisições por segundo |
| `APURACAO_ZONAS` | `sempre` | `final` só busca zona quando o município fecha |
| `APURACAO_MIN_INTERVALO_MU` | `300` | segundos entre leituras de um município fora das capitais (capitais e `te` acima de 200 mil: 120) |
| `APURACAO_SEM_CONDICIONAL` | vazio | `1` desliga `If-None-Match` |
| `APURACAO_BASE_URL` | TSE oficial | troca a base (testes) |
| `APURACAO_TURNO` | detectado | `2` força o telão no 2º turno |
| `APURACAO_PLEITO` | `3220` | pleito filtrado no `ele-c.json` (em 2024 o 2º turno veio em pleito próprio: 452 e 453) |

## 2º turno (25/10)

O 2º turno roda sobre o mesmo coletor, servidor e telão, com banco próprio e uma camada nova de indicadores, alertas e amostra de seções. O 1º turno não é tocado: `data/apuracao.sqlite` e `data/secoes_2026.sqlite` viram régua de comparação. Contrato entre as partes em `../analysis/apuracao_2t_2026/CONTRATO.md`.

### Partida

```bash
bun run scripts/referencia-1t.ts        # régua do 1º turno em data/referencia_1t.json (~25 s, só leitura dos bancos do 1T)
scripts/preflight.sh 2t                 # régua, -cs.json do pleito 3221, Supabase da totalização paralela, relógio, disco
scripts/start-collect.sh 2t             # APURACAO_ELEICOES=6258,6260 APURACAO_PLEITO=3221 APURACAO_DB=data/apuracao-2t.sqlite APURACAO_PAUSA_MIN=7
APURACAO_DB=data/apuracao-2t.sqlite scripts/start-serve.sh
nohup scripts/publicar-loop.sh >/dev/null 2>&1 &   # página pública: exporta e dá push a cada 5 min
```

Ou tudo de uma vez, no horário: `nohup scripts/ligar-2t-agendado.sh >/dev/null 2>&1 &` fica esperando (sem sondar o TSE) e às 16:40 de Brasília de 25/10 roda preflight, coletor, servidor e publicação; `--agora` liga na hora, `kill $(cat data/logs/agendado-2t.pid)` cancela. Ligado em 22/10 nesta máquina.

Varredura de conferência feita em 21/10 com as mesmas variáveis: 13.105 arquivos ok, 35 inexistentes (os agregados `-e`). Governador em 2º turno em seis UFs: AC, AM, DF, ES, RN e TO. O telão troca sozinho pelo `turno` de `/api/config`; `APURACAO_TURNO=2` força.

### Régua do 1º turno

`data/referencia_1t.json`: curva de seções totalizadas por minuto (Brasil e 27 UFs + exterior), marcos p50/p90/p99/p100, abstenção final por município e por UF, lag encerramento → recebimento por UF e por município (das seções do 1T), governador das seis UFs. **Convenção de relógio**: minutos após 17:00 de Brasília. O `dt/ht` dos arquivos de AC, AM, RO, RR, MT e MS vem em hora local rotulada como Brasília; `corrigirTotalizadoEm` (`src/turno2/comum.ts`) e `RelogioArquivo` (`src/server/indicadores/base.ts`) corrigem isso, herdam o instante em versão regerada e nunca deixam o carimbo passar da geração. Sem o arquivo, tudo funciona e as comparações saem `null`.

### Rotas novas

| Endpoint | Resposta |
|---|---|
| `GET /api/2t/regioes` | soma dos arquivos de UF por região (N, NE, CO, SE, S, exterior) e Brasil: seções, votos do duelo, abstenção, seções/min, ETA, atraso vs 1T no mesmo relógio |
| `GET /api/2t/ufs` | 27 UFs + exterior, mais lentas primeiro: pst, municípios faltantes, idade da última versão, `parada`, atraso vs 1T, três maiores municípios abertos |
| `GET /api/2t/abstencao` | abstenção dos municípios já fechados contra os mesmos municípios no 1T (Brasil, regiões, UFs, destaques ±3 pp) |
| `GET /api/2t/estaduais` | os seis duelos de governador com viradas, campo e régua |
| `GET /api/2t/evolucao?nivel=regiao\|uf&passo=60` | séries por região ou UF (pst e % válidos dos dois) na grade da noite, com a curva do 1T |
| `GET /api/2t/pausas` | pausa nacional, geral e por UF (início, fim, minutos), soma das UFs contra o arquivo nacional, pausa do 1T como referência |
| `GET /api/2t/secoes` | amostra de seções do arquivo-urna: encerramento → emissão → recebimento → totalização, por UF e Brasil, seções tardias |
| `GET /api/2t/paralela` | totalização paralela por QR: BUs recebidos, cobertura, conferência contra o BU oficial, divergências, placar dos BUs (soma dos BUs recebidos, não projeção) |

`/api/config` ganha `ufs_governador_2t` e `regioes`; `/api/anomalias` ganha as categorias `pausa`, `divergencia`, `abstencao` e `paralela`. Contratos zod em `tests/api-schemas-2t.ts` e `tests/helpers-2t.ts`.

### Alertas gravados pelo coletor

`pausa_nacional_inicio/fim`, `pausa_geral_inicio/fim` (nenhum arquivo publica), `pausa_uf_inicio/fim`, `pausa_nacional_longa`/`pausa_geral_longa` (error ao passar de 15 min), `soma_ufs_adiante`, `uf_atrasada_1t` (patamares de 20 min), `abstencao_atipica_mun` (te ≥ 20 mil e |Δ| ≥ 5 pp), `abstencao_atipica_uf` (≥ 30% do eleitorado fechado e |Δ| ≥ 2 pp), `secao_tardia` (encerramento após 18:00), `divergencia_paralela` (error), `paralela_conferida`, `virada` e `uf_fechou`. Textos e categorias em `src/server/textos.ts`; o telão só mostra o que tem categoria. Regras que o replay do 1º turno exigiu: arquivo que o coletor não leu há 180 s não entra em pausa; a detecção espera 1 min além do limiar (atraso do CDN); versão que chega velha não encerra pausa. Com limiar de 5 min o replay do 1º turno dava quatro pausas falsas de cadência; com 7 sobra só a parada real de 25 min, por isso o `start-collect.sh 2t` exporta `APURACAO_PAUSA_MIN=7`.

### Amostra de seções e totalização paralela

Amostra equiprovável por município (150 seções por UF, 600 nas seis UFs com governador, mais toda seção que chegar pela totalização paralela), aux.json → hash → BU, com balde próprio (`APURACAO_SECOES_RPS` 15, `APURACAO_SECOES_CONCORRENCIA` 12: com 4 a rodada de 7,5 mil seções levava 30 min) e reconsulta a cada `APURACAO_SECOES_INTERVALO_S` (900). A ponte com o Supabase lê as views públicas a cada `APURACAO_PARALELA_INTERVALO_S` (60) e confere cada BU aceito contra o BU oficial da mesma seção com as regras de `../scripts/totalizacao-conferir-tse.py`. Desligar: `APURACAO_SECOES=0` (as seções da paralela continuam, porque a conferência depende delas) e `APURACAO_PARALELA=0`. Tabelas novas: `pausa`, `secao_2t`, `paralela_bu`, `paralela_conferencia`.

### Telas novas e teclado

| Tela | Tecla | Conteúdo |
|---|---|---|
| `regioes` | Shift+N | duelo por região, pst, abstenção, atraso vs 1T |
| `ufs` | Shift+U | ranking das UFs, mais lentas primeiro, chip "parada" |
| `atraso` | Shift+D | quem está lerdo: UFs atrasadas vs 1T, maiores municípios abertos, quem fecha por último |
| `abstencao` | Shift+B | mapa divergente Δ abstenção vs 1T (±5 pp), base municípios fechados |
| `secoes` | Shift+S | cadeia encerramento → emissão → recebimento → totalização |
| `pausas` | Shift+P | linha do tempo da noite com as pausas e a faixa cinza do 1T (19:32–20:02) |
| `gov-2t` | `3` ou Shift+G | seis duelos estaduais; tecla de UF leva a `gov-uf` |
| `paralela` | Shift+T | totalização paralela: cobertura, conferência, divergências |
| `alertas` | Shift+L | feed das anomalias por categoria |
| `evolucao` | Shift+E | % válidos na noite, nacional + regiões; `m` troca para 27 UFs |

Playlist do 2º turno em `public/playlist-2t.json` (a do contrato é reserva). Ensaio sem banco: `#mock=1` já é 2º turno (`&turno=1` volta ao 1º), com `t0=<min após 17h>`, `falha=rota[:erro|pendente|fonte]`, `sem1t=1` e `congelar=1` (relógio parado, necessário para o auditor de contraste). Banco de ensaio: `bun run scripts/semear-ensaio.ts --turno 2` gera `data/ensaio-2t.sqlite`.

### Demonstração com dados reais do 1º turno

`bun run scripts/demonstrar-2t.ts` (cerca de 90 s, só leitura dos bancos do 1T) repassa as 104.683 leituras reais da noite de 04/10 pelo `processar()` do coletor com o motor ligado e grava `../analysis/apuracao_2t_2026/demonstracao_1t.{md,json}`: parada nacional de 18:48:59 a 19:14:08 detectada ao segundo, pausa geral de 19:32 a 20:02 e travamento das 18:00 como pausas gerais, 3 viradas (RR, TO, AM), 28 fechamentos no mesmo segundo do dossiê, zero alerta de atraso ou abstenção contra a própria noite (40 pela interpolação antiga; 28 quando a noite é atrasada em 30 min), e conferência de três BUs oficiais reais (SP, AC, exterior) contra cópias adulteradas: 3 iguais, 6 divergentes com os campos, 1 à espera do TSE. O replay revelou e corrigiu a regra de versão regressiva (o `idg` menor descartava 2.213 versões reais; agora vale a hora de geração), o atraso por interpolação (platô de 19:32) e a hora de fechamento no texto do telão. A régua data a curva pela publicação (`gerado_em`), por isso dispensa fuso.

### Página pública

`scripts/exportar-publico.ts` grava `../docs/assets/apuracao_2t/*.json` + `manifest.json` (sem municípios do config, sem identificador pessoal, abaixo de 2 MB); `scripts/publicar-loop.sh` exporta e dá commit + push só dessa pasta a cada `INTERVALO_S` (300; `PUSH=0` só commita). `../docs/apuracao_2t_ao_vivo.html` lê os JSON, recarrega a cada 60 s, avisa dados com mais de 10 min e aceita `?fonte=exemplo`. Card em `img/og/apuracao_2t_ao_vivo.png`; depois do primeiro commit da página rode `python3 ../scripts/sitemap-build.py`.

## Boletim falado (2º turno)

A cada 10 minutos o boletim lê os dados, escreve o roteiro na voz do Leonardo, gera o áudio e deixa o mp3 pronto. Substitui o laço `scripts/boletim-loop.sh` do 1º turno (que tocava sozinho pelo `afplay`).

**Regra firme: o boletim nunca dá play automático.** O gerador só deixa o áudio pronto e o widget do telão avisa ("novo boletim das HH:MM", pulsando). O play acontece só por ação do Leonardo: tecla `b` no telão, clique no botão do widget ou "tocar" no diretor. Não há tocar ao ficar pronto, fila automática nem tocar o próximo ao terminar; o servidor só põe no ar por `POST /api/boletins/:id/tocar`, e nada no gerador chama essa rota. A única retomada é a do mesmo boletim que já está no ar quando o telão recarrega no meio dele.

**Arquitetura.** O gerador roda num processo próprio (`bun run boletim`, laço de religar em `scripts/start-boletim.sh`), fora do servidor do telão: uma correção no prompt ou nos dados reinicia só ele. O servidor serve a lista, o controle, o mp3 e os eventos. Estado em arquivos em `data/boletins-2t/`, cada arquivo com um único escritor e gravação atômica; nada vai para o SQLite.

| Arquivo | Escritor | Conteúdo |
|---|---|---|
| `indice.json` | gerador | `{itens:[{id, hora, estado: gerando\|pronto\|erro, etapa, origem, modo, palavras, duracao_s, resumo, erro}]}` |
| `gerador.json` | gerador | batimento a cada 2 s: pid, relógio, `proximo_ciclo_em`, `gerando`, `etapa`, `ultimo_erro` |
| `controle.json` | servidor | `no_ar {id, desde, duracao_s}`, `tocados`, `descartados` |
| `pedido.json` | servidor | geração manual pedida pelo diretor; o gerador apaga ao atender |
| `HHMM.dados.json`, `.prompt.txt`, `.txt`, `.mp3`, `.meta.json`, `.tts.log` | gerador | resumo e base do delta, prompt enviado, roteiro final, áudio, tempos e avisos, saída do TTS |

**Ciclo.** Alinhado aos múltiplos de `APURACAO_BOLETIM_INTERVALO_S` a partir de `APURACAO_BOLETIM_INICIO` (17:10, 17:20...); `POST /api/boletins/gerar` gera a qualquer hora; nunca duas gerações ao mesmo tempo (ciclo que cai durante uma geração é pulado e registrado no log). Etapas:

1. **dados** (`src/boletim/dados.ts`): `/api/estado`, `/api/resultado` (6258/1/br), `/api/2t/{regioes,ufs,abstencao,estaduais,pausas,secoes,paralela}`, `/api/anomalias`, `/api/lotes` e o resultado final do 1º turno lido uma vez de `data/apuracao.sqlite` (só leitura). Calcula o delta desde o boletim anterior (seções, votos, diferença F menos L, viradas por UF e nos governos, UFs que fecharam, pausas abertas e fechadas, divergências novas da paralela). Boletim anterior com mais de 30 min não serve de base: a janela volta a ser os últimos 10 min de versões. `bun run scripts/boletim-dados-2t.ts [--at ISO]` imprime o mesmo JSON sem gravar nada.
2. **roteiro** (`src/boletim/roteiro.ts`): `claude -p --model opus --no-session-persistence` com o prompt pelo stdin e ambiente limpo (sem as variáveis `CLAUDE*`/`ANTHROPIC*` de quem lançou o laço; o CLI usa o login próprio), guia `data/boletins/ESTILO.md` na íntegra (relido a cada boletim, então uma regra nova vale no ciclo seguinte; `data/` fica fora do git, por isso há a cópia versionada `src/boletim/ESTILO.md`, usada quando o vivo falta, e `APURACAO_BOLETIM_ESTILO` troca o caminho), estrutura obrigatória do 2º turno e o boletim anterior para não repetir. Tamanho pelo modo: abertura (antes das 17:00 ou zero seção) 150 a 200 palavras; pouca mudança 300 a 380, dizendo que o quadro se mantém; muita novidade (2 pontos de seções, virada, UF fechada, pausa, divergência nova, troca de liderança) 500 a 600. Acima do teto (230, 420, 640) há o segundo passo de enxugar. Guardas finais: sem markdown, travessão vira vírgula, frase com a palavra proibida sai. Uma nova tentativa se o CLI falhar.
3. **áudio** (`src/boletim/audio.ts`): chama o `scripts/boletim-tts.py` do 1º turno (ElevenLabs `eleven_v4`, por parágrafo com `previous_text`/`next_text`, estabilidade 0,4, estilo 0,3, concat pelo ffmpeg; chave e voz de `~/arvor/voicer/.env`, nunca copiadas). O caminho já provado em 30 boletins pesou mais que o porte para TypeScript. Duração pelo `ffprobe`.

**Ensaio de 25/10, 13:57** (servidor real, zero seção): abertura de 182 palavras, mp3 de 77,2 s; dados 0,2 s, roteiro 23,0 s, áudio 7,7 s, total 30,9 s. Num ensaio com o banco `data/ensaio-2t.sqlite` em 46% das seções, o roteiro de muita novidade levou 48 s e o passo de enxugar mais 79 s (710 para 560 palavras).

### Partida e variáveis

```bash
nohup scripts/start-boletim.sh >/dev/null 2>&1 &     # gerador com relógio (ligado em 25/10 às 13:57 nesta máquina)
pkill -f src/boletim/main.ts                         # recarrega o código: sai com 143 e o laço religa
kill $(cat data/boletins-2t/laco.pid); pkill -f src/boletim/main.ts   # desliga de vez
```

| Variável | Padrão | Efeito |
|---|---|---|
| `APURACAO_BOLETIM` | `1` no `start-boletim.sh` | `1` liga o relógio; `0` deixa só a geração manual |
| `APURACAO_BOLETIM_INTERVALO_S` | `600` | segundos entre ciclos (mínimo 60) |
| `APURACAO_BOLETIM_INICIO` | `17:10` | primeiro ciclo: `HH:MM` de Brasília no dia ou ISO completo |
| `APURACAO_BOLETIM_DIR` | `data/boletins-2t` | pasta do estado (servidor e gerador precisam da mesma) |
| `APURACAO_API` | `http://127.0.0.1:4180` | servidor lido pelo gerador |
| `APURACAO_BOLETIM_MODELO` | `opus` | modelo do `claude -p` |
| `APURACAO_BOLETIM_CLAUDE` | `claude` no PATH ou `~/.local/bin/claude` | CLI do roteiro |
| `APURACAO_BOLETIM_TTS` | `scripts/boletim-tts.py` | script de voz (`BOLETIM_MODEL`, `BOLETIM_STABILITY`, `BOLETIM_STYLE` continuam valendo) |
| `APURACAO_BOLETIM_AT` | vazio | ensaio sobre banco antigo: lê os dados neste instante |

### Rotas

| Rota | Efeito |
|---|---|
| `GET /api/boletins[?todos=1]` | `{agora, gerador:{vivo, relogio_ligado, proximo_ciclo_em, gerando, etapa, ultimo_erro}, no_ar:{id, hora, desde, duracao_s, decorrido_s}\|null, itens:[{id, hora, estado: gerando\|pronto\|no_ar\|tocado\|erro, palavras, duracao_s, resumo, erro, ...}]}`; descartados só com `todos=1` |
| `GET /api/boletins/:id` | `{item, texto, meta, mp3}` |
| `POST /api/boletins/gerar` | 202 grava o pedido; 409 se já está gerando; 503 se o gerador está fora do ar |
| `POST /api/boletins/:id/tocar` | põe no ar qualquer boletim com mp3 (pronto, tocado, no ar ou descartado, que volta à lista); 409 só se ainda gera ou não tem áudio; o que estava no ar sai |
| `POST /api/boletins/parar` | tira do ar o que estiver tocando |
| `POST /api/boletins/:id/descartar` | some da lista (e sai do ar, se estiver); arquivos ficam no disco |
| `POST /api/boletins/:id/fim` | o player avisa que o áudio terminou; só vale para o que está no ar |
| `GET /boletins/HHMM.mp3` | áudio com `Accept-Ranges` e respostas 206 |

POST só nessas rotas, só de 127.0.0.1 e com o cabeçalho `x-apuracao: boletim` (uma página de outra origem não consegue mandar o cabeçalho sem preflight, que o servidor não atende). Sem o `fim` do player, o servidor encerra sozinho 30 s depois da duração. O SSE ganhou `event: boletim` com `{kind: gerando|pronto|erro|no_ar|fim|descartado, id, hora?, desde?, duracao_s?, motivo?}` em todas as assinaturas; `/events?so=boletim` entrega só o boletim e o batimento, sem sondar o banco.

### Widget "Boletim Arvor" no telão (desde 25/10, 15:00)

O player mora no telão (`src/ui/components/boletim.ts`), em todas as telas e na rotação, canto inferior direito, mesma paleta e texto de 22 px no mínimo, **operado com o mouse** (na janela do Chrome que o OBS captura ou no diretor): título, os últimos 4 boletins (hora, duração, estado: gerando, pronto, no ar, tocado), "próximo às HH:MM" e os botões. Boletim novo acende o chip pulsante "novo boletim das HH:MM" por 20 s e põe a linha "novo boletim das HH:MM pronto para ir ao ar" no ticker por 3 min; o áudio não começa.

- **Mouse** (botões de 44 px no mínimo, com hover visível): cada item tem ▶ para tocar, inclusive os já tocados; o item no ar troca para ❚❚ (pausar e retomar) e ■ (parar); a barra de progresso é clicável para avançar ou voltar; ▾ recolhe o cartão.
- **Formato**: cartão aberto (cerca de 460 × 330 px) nas telas com o canto livre (`regioes`, `pausas`, `paralela`, `alertas`, `espera`) e durante os 20 s do alerta; nas demais (presidente, UFs, evolução, governadores, exterior, abstenção, atraso), pílula na faixa inferior, à esquerda do HUD, com ▶/❚❚, ■, o último boletim e o próximo ciclo e, enquanto toca, tempo e barra. Clicar no texto da pílula abre o cartão até a próxima troca de tela. Assim o widget não cobre dado. `#boletimw=aberto` ou `#boletimw=compacto` fixa um formato.
- **Teclas (atalho secundário)**: `b` toca o último pronto ainda não tocado ou, se não houver, o mais recente; `b` de novo pausa e retoma; `[` e `]` escolhem o item anterior e o seguinte (contorno no item, cartão aberto por 15 s) e `b` toca o escolhido; `Shift+B` para quando há boletim carregado (sem boletim, continua abrindo a tela de abstenção, como antes); `Ctrl+B` sempre para. O `b` espera 900 ms porque `b` + `a` é a Bahia.
- **Tocar de novo**: "tocado" é só rótulo. Todo boletim com mp3 toca de novo, inclusive os descartados (o diretor mostra com "mostrar descartados"; tocar um descartado o devolve à lista). A API só recusa boletim ainda gerando ou sem áudio.
- **Áudio**: um `<audio>` no próprio telão toca o mp3 quando chega o `no_ar` do SSE (vindo do clique, da tecla ou do diretor) e manda o `fim` ao terminar; terminar nunca puxa o próximo. Na fonte de navegador do telão no OBS, marque **"Control audio via OBS"**: o som do boletim passa a sair pelo mixer do OBS. Se o OBS captura a janela do Chrome, capture também o áudio desse Chrome. O OBS não exige gesto para tocar; num Chrome comum o widget mostra "clique para liberar o áudio".
- **Um player só**: cada telão aberto com som toca o `no_ar`. Deixe som em um único telão e abra os outros (ensaio, segunda tela) com `#boletim=0`, que mostra a lista e o progresso pelo relógio do servidor sem tocar. O telão avisa pelo `BroadcastChannel('apuracao')` que está tocando, e o `boletim.html` aberto no mesmo navegador cede a vez (`?forcar=1` força). `boletim.html` continua como reserva.
- **Toque de aviso**: desligado por padrão, porque o som do telão vai ao ar pelo OBS; `#som=1` liga um toque discreto quando um boletim fica pronto.
- Pausa longa: o servidor considera o boletim encerrado 30 s depois da duração, mas o telão segura o áudio pausado e retoma do ponto.

### Diretor, telão e OBS

- **Diretor** (`/director.html`, painel "boletim falado" no topo): estado do gerador e próximo ciclo, o que está no ar com tempo decorrido, "gerar agora" e "parar", e a lista com hora, estado, duração, palavras, modo e o resumo de uma linha (gerado dos dados, sem LLM). Cada item tem "tocar", "descartar" e, aberto, o roteiro com prévia do áudio para fone. Atualiza a cada 2 s.
- **Telão**: o widget acima e o chip "boletim das HH:MM no ar" na faixa inferior enquanto o áudio toca (aparecem também com `hud=0`).
- **OBS (reserva)**: fonte de navegador `http://127.0.0.1:4180/boletim.html`, 1920 × 1080, acima da cena do telão. Marque "Control audio via OBS" (o áudio entra no mixer do OBS como fonte própria, com volume e monitoramento) e desmarque "Shutdown source when not visible" e "Refresh browser when scene becomes active". O navegador do OBS não exige gesto do usuário para tocar som, então o comando "tocar" do diretor basta. A página é transparente; a tarja "Boletim das HH:MM, Arvor Intelligence", com barra de progresso, aparece só enquanto toca. Parâmetros: `?tarja=0` (só áudio), `?pos=bl|br|tl|tr` (canto; padrão inferior esquerdo, acima da faixa), `?vol=0.8`. Recarregar a fonte no meio de um boletim retoma do ponto em que ele está. Num Chrome comum aparece "clique para liberar o áudio" (ou abra com `--autoplay-policy=no-user-gesture-required`).
- **Abertura**: perto das 16:55, "gerar agora" produz o boletim de abertura (150 a 200 palavras), que fica pronto à espera do play; o relógio começa às 17:10.

### Reserva

- `scripts/boletim-tocar.sh HHMM` toca pelo `afplay` no desktop, como no 1º turno (sem argumento, o mp3 mais recente).
- Gerador fora do ar: o diretor mostra "gerador FORA DO AR"; religue com `scripts/start-boletim.sh` e leia `data/logs/boletim-2t-AAAAMMDD.log`.
- Geração manual por terminal: `curl -X POST -H 'x-apuracao: boletim' http://127.0.0.1:4180/api/boletins/gerar`.
- O servidor agora sai com 143 no SIGTERM, então `pkill -f src/server/main.ts` religa pelo `start-serve.sh` como o runbook diz (antes saía com 0 e o laço `until` encerrava).

## Verificação

- `bun run check` sem erro (`tests/boletim.test.ts` e `tests/boletim-server.test.ts` cobrem relógio, guardas, gerador, rotas, Range e SSE do boletim; `tests/preload.ts` dá aos testes uma pasta temporária de boletins).
- `bun run scripts/semear-ensaio.ts && APURACAO_DB=data/ensaio.sqlite bun run serve`, depois `bun run qa/i1.ts` (`qa/` é bancada local, fora do git e do lint; `qa/i2.ts` percorre todas as telas, a espera num banco vazio na porta 4181 e a rotação por 90 s): presidente, SP por município, zonas da capital, governador e senado, diretor, atualização ao vivo pelo SSE, zero requisição fora de 127.0.0.1.
- Contraste: `python3 ../scripts/contrast-audit.py --width 1920 "http://127.0.0.1:4180/#v=pres&auto=0&hud=0&replay=2026-10-04T23:00:00-03:00,1"` (o replay troca o SSE por sondagem, porque a auditoria espera a rede ficar ociosa; uma URL por execução).
- `grep -rn $'\u2014' src public README.md` vazio (nenhum travessão em texto do telão).
