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

## 2º turno (25/10)

1. Banco separado: `APURACAO_ELEICOES=6258,6260 APURACAO_DB=data/apuracao-2t.sqlite scripts/start-collect.sh`.
2. Servidor no mesmo banco: `APURACAO_DB=data/apuracao-2t.sqlite scripts/start-serve.sh`. O turno é detectado pelos arquivos de 6258/6260 (ou `APURACAO_TURNO=2`).
3. O telão troca sozinho pelo `turno` de `/api/config`: `pres` vira duelo com barra bipartida e mapa divergente.
4. Antes, `bun run sweep` com as mesmas variáveis para conferir que os arquivos existem.

## Verificação

- `bun run check` sem erro.
- `bun run scripts/semear-ensaio.ts && APURACAO_DB=data/ensaio.sqlite bun run serve`, depois `bun run qa/i1.ts`: presidente, SP por município, zonas da capital, governador e senado, diretor, atualização ao vivo pelo SSE, zero requisição fora de 127.0.0.1.
- Contraste: `python3 ../scripts/contrast-audit.py --width 1920 "http://127.0.0.1:4180/#v=pres&auto=0&hud=0&replay=2026-10-04T23:00:00-03:00,1"` (o replay troca o SSE por sondagem, porque a auditoria espera a rede ficar ociosa; uma URL por execução).
- `grep -rn $'\u2014' src public README.md` vazio (nenhum travessão em texto do telão).
