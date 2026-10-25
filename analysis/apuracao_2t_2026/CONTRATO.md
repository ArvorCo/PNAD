# Apuração do 2º turno (25/10/2026): contrato entre os pacotes

Base: `apuracao/` (coletor TSE, SQLite de auditoria, telão 1920×1080, Bun + TypeScript, zero lint, zero erro de tipo). O 1º turno fica intacto: `data/apuracao.sqlite` e `data/secoes_2026.sqlite` são só leitura e viram régua (`data/referencia_1t.json`, gerada por `scripts/referencia-1t.ts`). O 2º turno roda em `data/apuracao-2t.sqlite` com `APURACAO_ELEICOES=6258,6260 APURACAO_PLEITO=3221`.

Sem travessão em nenhum texto público (telão incluído). Rótulos obrigatórios: a totalização paralela é "soma dos BUs recebidos, não projeção"; atraso e abstenção atípica "pedem explicação, não indicam irregularidade"; pausa é "intervalo sem versão nova publicada", não acusação.

## Módulos comuns (já existem, não editar sem avisar)

- `src/turno2/comum.ts`: `REGIOES`, `NOME_REGIAO`, `ORDEM_REGIOES`, `regiaoDe(uf)`, `UFS_GOVERNADOR_2T = AC AM DF ES RN TO`, `FUSO_MIN`, `fusoMin(uf)`, `T0_2T_MS` (17:00 BRT de 25/10), `minutosDesde17h(iso)`, `hhmmDeMinutos(min)`, `corrigirTotalizadoEm(uf, totalizadoIso, geradoIso)`, `horaLocalUrnaParaIso(uf, texto)`, `horaBrasiliaParaIso(texto)`, `percentil`.
- `src/turno2/referencia.ts`: `carregarReferencia()` (cache por mtime; null se o arquivo faltar: tudo deve funcionar sem a régua, só sem comparação), tipos `Referencia1T`, `PontoCurva = [min, pst, st, ts, comparecimento, abstencao, pa]`, `pstNoMinuto(curva, min)`, `minutoDoPst(curva, pst)`, `atrasoVsReferencia(curva, pstAtual, minAgora)`.
- Convenções de tempo: "relógio da apuração" = minutos após 17:00 de Brasília (float, 1 decimal). **O `totalizado_em` (dt/ht) dos arquivos de UF de AC, AM, RO, RR, MT e MS vem em hora local rotulada como Brasília**: toda conta com `totalizado_em` por UF passa por `corrigirTotalizadoEm`. `gerado_em` (dg/hg) é Brasília real. Hora da urna (abertura, encerramento, emissão) é local: `horaLocalUrnaParaIso`. `dr_hr` do aux.json é Brasília.
- Régua do 1º turno (`data/referencia_1t.json`, 1,45 MB): `curvas.br`, `curvas.uf[UF]` (27 UFs + ZZ), `marcos.{br,uf}` (p50/p90/p99/p100 em minutos e hh:mm), `municipios[UF][cd5]` (`te, ts, st, comparecimento, abstencao, pa, fechou_min, apareceu_min`), `abstencao_uf[UF]`, `secoes_lag.uf[UF]` (lag encerramento→recebimento p50/p90/p99, encerramento p50/p90 hh:mm), `secoes_lag.municipio[UF][cd5]`, `governador_1t[UF]` (6 UFs, cargo 3).

## Donos de arquivos (dois pacotes nunca escrevem no mesmo arquivo)

| Pacote | Escreve em | Só lê |
|---|---|---|
| **motor e alertas** (Opus) | `src/collector/**`, `src/db/schema.sql` (aditivo), `src/db/escrita.ts`, `src/db/leitura.ts`, `src/secoes2t/**` (novo), `src/paralela/**` (novo), `src/server/api-2t-auditoria.ts`, `src/server/api-anomalias.ts`, `src/server/textos.ts`, `src/server/sse.ts`, `tests/pausas*.test.ts`, `tests/paralela*.test.ts`, `tests/secoes2t*.test.ts`, `tests/helpers-2t.ts`, `scripts/start-collect.sh`, `scripts/preflight.sh` | tudo |
| **indicadores** (Opus) | `src/server/api-2t-indicadores.ts`, `src/server/indicadores/**` (novo), `src/server/api-config.ts`, `src/server/nacional*.ts`, `tests/api-2t-indicadores*.test.ts`, `tests/api-schemas-2t.ts`, `tests/fixtures/2t/**`, `tests/server-helpers.ts` (aditivo) | tudo |
| **telão** (Sonnet) | `src/ui/**`, `src/director/**`, `public/*.html`, `public/*.json` (playlist), `tests/ui/**` | tudo |
| **público** (Sonnet) | `scripts/exportar-publico.ts`, `scripts/publicar-loop.sh`, `../docs/apuracao_2t_ao_vivo.html`, `../docs/assets/apuracao_2t/**`, `../scripts/social-cards.py` (manifesto, só acrescentar), `../tests/test_apuracao_2t_publico.py` | tudo |

Roteamento já está em `src/server/api.ts` (stubs devolvem `{pendente: true}`); `src/turno2/*` é do orquestrador. Quem precisar mudar um arquivo de outro pacote escreve a mudança desejada no relatório final em vez de editar.

## Rotas novas (todas GET, JSON, `Cache-Control: no-store`, aceitam `at=` ISO como as demais)

Convenções: `at` = instante avaliado (ISO UTC); `min` = minutos após 17:00 BRT; percentuais 0..100 com 2 decimais; `sqcand` como string; `uf` em caixa alta nas rotas `/api/2t/*`; `ele` e `cargo` opcionais com padrão presidente (6258/1).

### `/api/2t/regioes` (indicadores)
```
{ at, min, ele, cargo, turno, referencia_1t: boolean,
  brasil: Agregado, regioes: Agregado[] }       // ordem N, NE, CO, SE, S, ZZ
Agregado = { sigla, nome, ufs: string[],
  ts, st, snt, pst, te, est, comparecimento, abstencao, pa,     // soma dos arquivos de UF (v_atual), pa = abstencao/(comparecimento+abstencao)*100
  votos: { [sqcand]: { vap, pvapn } }, vv, vb, vn, tv,           // pvapn recalculado sobre vv da região
  lider: sqcand|null, margem_pp,                                 // diferença entre os dois em % válidos
  vel_10min_spm, eta_100_iso|null,                               // seções/min nos últimos 10 min e previsão de 100%
  ref_1t: { pst_mesmo_relogio, atraso_min, pa_final_1t } | null, // curva do 1T agregada pela soma dos st/ts das UFs da região no mesmo min
  atualizado_em }                                                // max totalizado_em corrigido das UFs
```

### `/api/2t/ufs` (indicadores)
```
{ at, min, ele, cargo, limiar_parada_min, ufs: UfLinha[] }   // 27 UFs + ZZ, ordem por pst crescente (mais lentas primeiro)
UfLinha = { uf, nome, regiao, ts, st, snt, pst, te, comparecimento, abstencao, pa,
  munnr, munpt, munf,                               // do monitor -ab
  votos: {[sqcand]:{vap,pvapn}}, lider, margem_pp,
  ultima_versao_em, idade_s,                        // totalizado_em corrigido e agora − ele
  vel_10min_spm, eta_100_iso|null,
  parada: boolean,                                  // st < ts e idade_s > limiar_parada_min*60 e país avançou no período
  ref_1t: { pst_mesmo_relogio, atraso_min, p50_min, p90_min, p99_min, p100_min, pa_final } | null,
  pendentes_maiores: [{ cd, nm, te, pst }] }        // até 3 municípios abertos (pst<100) por eleitorado, do nível mu
```

### `/api/2t/abstencao` (indicadores)
Base de comparação: municípios já fechados (st = ts > 0) no 2º turno contra os mesmos municípios no 1º (`referencia.municipios`).
```
{ at, min, ele, cargo, base: "municipios_fechados",
  brasil: Bloco, regioes: Bloco[], ufs: (Bloco & { pa_corrente, pa_final_1t })[],
  destaques: { subiu: Mun[], caiu: Mun[] } }        // |delta_pp| >= 3 e te >= 20000, até 20 cada, por |delta| desc
Bloco = { sigla|uf, nome, n_mun, n_mun_fechados, te_fechado, pct_te_fechado,
  comparecimento, abstencao, pa_2t, pa_1t_mesmos, delta_pp }
Mun = { uf, cd, nm, te, pa_2t, pa_1t, delta_pp, fechou_min }
```

### `/api/2t/estaduais` (indicadores)
```
{ at, min, ele: 6260, cargo: 3, ufs: Estadual[] }   // AC, AM, DF, ES, RN, TO nessa ordem
Estadual = { uf, nome, ts, st, pst, te, comparecimento, abstencao, pa, munnr, munpt, munf,
  cand: [{ sqcand, n, nome_urna, partido, vap, pvapn, campo }],   // ordem por número de urna
  lider, margem_pp, viradas: [{ at, de, para }], ultima_versao_em, idade_s,
  ref_1t: { pst_mesmo_relogio, atraso_min } | null,
  pa_final_1t }
```

### `/api/2t/evolucao?nivel=regiao|uf&passo=60` (indicadores)
```
{ at, ele, cargo, passo_s, candidatos: [{ sqcand, n, nome_urna }],
  series: { [chave]: [[min, pst, pvapn_cand_a, pvapn_cand_b, st]] },   // chave = sigla da região ou UF; BR sempre presente
  referencia_1t: { [chave]: [[min, pst]] } | null }                    // curva do 1T na mesma grade
```
Grade a cada `passo_s` desde 17:00 BRT; estado de cada UF num instante = última versão com totalizado_em corrigido ≤ instante; região = soma.

### `/api/2t/pausas` (motor)
```
{ at, min, limiar_min: 5,
  nacional: { ultima_versao_em, idade_s, st, ts, em_pausa, pausa_atual: {desde, minutos}|null,
              historico: [{ de, ate, minutos, st_antes, st_depois }] },
  soma_ufs: { st, pst, defasagem_secoes, defasagem_min },         // soma dos arquivos de UF menos arquivo nacional
  ufs: [{ uf, ultima_versao_em, idade_s, em_pausa, st, ts, historico_n }],
  referencia_1t: { pausa_geral: { de: "19:32", ate: "20:02", minutos: 29.6 }, travamento_nacional: { de: "18:00", ate: "18:10" } } }
```
Pausa = sem versão nova (idg/gerado_em) do arquivo com st < ts por mais de `limiar_min`, enquanto outro nível avança. Início e fim viram eventos (abaixo).

### `/api/2t/secoes` (motor)
Amostra ao vivo de seções do arquivo-urna do pleito 3221 (aux.json → hash → BU): encerramento (último voto, hora local → Brasília), emissão do BU, recebimento no TSE (`dr_hr`), e totalização do município.
```
{ at, min, desenho: { nacional_por_uf, estaduais_por_uf, inclui_paralela: true, intervalo_s },
  totais: { alvo, recebidas, pendentes, tardias },
  por_uf: [{ uf, alvo, recebidas, encerramento_p50_hhmm, encerramento_p90_hhmm, tarde_apos_1730_pct,
             lag_encerr_recebimento_min: {p50,p90,p99}, lag_encerr_emissao_min: {p50,p90},
             ref_1t: { lag_p50, lag_p90, enc_p90_hhmm } | null }],
  brasil: { ...mesmos campos de por_uf sem uf },
  tardias: [{ uf, mun, nm, zona, secao, encerramento_hhmm, recebido_hhmm, lag_min }],   // encerramento > 18:00 BRT, até 50
  ultimas: [{ uf, mun, zona, secao, recebido_em, lag_min }] }                            // 20 últimas recebidas
```

### `/api/2t/comparecimento` (motor, 25/10)
Vigilância de falso comparecimento (mesário "pianista"). Tipos em `apuracao/src/secoes2t/comparecimento-tipos.ts`, cálculo em `comparecimento.ts`, zod em `tests/api-schemas-2t.ts`, teste `tests/comparecimento2t-api.test.ts`. Régua por seção `data/referencia_1t_secoes.json` (`scripts/referencia-1t-secoes.ts`: BU do 1T em `secoes_2026.sqlite`, votos de Flávio e Lula e coordenadas do local no Politize; universo de 497.877 seções em 19,6 MB). `secao_2t` ganhou, por ALTER TABLE aditivo (`COLUNAS_ACRESCIDAS` em `src/db/abrir.ts`), `hab_biometria`, `hab_ano_nascimento`, `comp_sem_biometria`, `tipo_arquivo`, `tipo_urna`, `n_cargas`, `abertura_iso`; BU lido antes disso volta uma vez à fila.
- Escore 0 a 4 por seção: delta de comparecimento ≥ +5 pp contra a própria seção no 1T; sem biometria ≥ 10% e ≥ 2× a mediana do município no 1T; encerramento (hh:mm de Brasília) depois de 17:00; BU do sistema de apuração (`tipo_arquivo` ≥ 3). Depois das 19:00 e contingência (`tipo_urna` 3, 4 ou 6, ou mais de uma carga) contam à parte.
- Linha de base do 1T (`referencia.enc_1t_pct`): 92,38% das seções encerraram depois de 17:00, 8,42% depois de 18:00 e 1,63% depois de 19:00. O sinal "depois das 17:00" é quase universal; o discriminante é depois das 19:00.
- Votos da prorrogação: tardias (depois de 17:00) contra a própria seção no 1T (fatia de Flávio entre os dois, ponderada pelos votos do 2T) e contra as pontuais do mesmo município; deltas de fatia só com n ≥ 20, sempre com o n ao lado.
- Camada municipal: arquivos mu de presidente com pst ≥ 30%, `taxa_2t` = comparecimento / (comparecimento + abstenção) contra `100 − pa` do município no 1T (parcial contra total: o recorte de 30% limita, não elimina, essa diferença).
- Rótulo obrigatório: "Sinal pede explicação, não prova irregularidade; a extensão até 19h eleva o comparecimento legitimamente."

### `/api/2t/paralela` (motor)
Totalização paralela por QR (Supabase, projeto PNAD, views públicas `v_bu_publico`, `v_bu_voto_publico`, `v_bu_cargo_publico`, `v_totais_br`, `v_totais_uf`, `v_cobertura_uf`, `v_conflito`, `v_estatisticas`; URL e chave publicável em `../scripts/totalizacao_comum.py` e `../docs/assets/totalizacao/config.js`; só leitura).
```
{ at, fonte: "supabase", atualizado_em, erro: string|null,
  recebidos: { bus, envios, secoes, ufs, conflitos },
  conferencia: { iguais, divergentes, tse_ainda_nao_publicou, erro, fora_do_oficial, pendentes },
  cobertura_uf: [{ uf, bus, secoes_total, pct }],
  placar_bus: { presidente: { votos: {[numero]: votos}, comparecimento, aptos, brancos, nulos, secoes },
                governador: { [uf]: { votos: {[numero]: votos}, secoes } } },      // rótulo: soma dos BUs recebidos, não projeção
  divergencias: [{ uf, mun, zona, secao, recebido_em, conferido_em, campos: [{ campo, paralela, tse }] }],
  ultimos: [{ uf, mun, zona, secao, recebido_em, situacao }] }
```
Conferência: para cada BU aceito (fase O), buscar o aux.json e o BU oficial da seção no arquivo-urna (reaproveitar `scripts/secoes/*` e `scripts/bu-decode.ts`), comparar comparecimento, aptos e, por cargo, brancos, nulos e votos nominais por número. Situações iguais às de `../scripts/totalizacao-conferir-tse.py`. Divergência vira evento `error`.

### `/api/2t/projecao` (indicadores, 25/10/2026)
Projeção estatística do resultado final a partir do que já foi totalizado. Rótulo obrigatório, na tela e na API (`rotulo`): "projeção estatística a partir do que já foi totalizado; não é resultado nem previsão de vitória".
- Régua: `data/referencia_1t_votos.json` (`bun run scripts/referencia-1t-votos.ts`, só leitura de `data/apuracao.sqlite`): por UF e município, votos finais de Flávio (22) e Lula (13), válidos, comparecimento, eleitorado e a trajetória da noite de 04/10 (`c`: [st, f, l] por versão, st crescente). Conferência: Brasil 47,03 × 45,16 dos válidos; entre os dois, Flávio 51,01%.
- Motor puro `src/server/indicadores/projecao.ts`; leitura do banco e série em `projecao-dados.ts`. Oscilação de cada município = parte de Flávio observada no 2º turno menos a do 1º turno **no mesmo estágio da contagem** (mesma fração de seções, interpolada na trajetória). Comparar com o final do 1º turno herda o viés de ordem: na validação sobre o 1º turno, às 18:00 (10,85% das seções), projetava 52,51 contra 51,01 final, com faixa de 50,88 a 54,03 (`estagio=0` reproduz). Pooling parcial: município pesa n/(n + K), K = 2.000 votos; UF pesa N/(N + K_uf), K_uf = 20.000, e o resto vem do Brasil; UF sem observação usa o Brasil. Parte que falta = votos dos dois que faltavam no 1º turno nesse estágio × razão de votos dos dois 2º/1º observada na UF (fechados, se somam 20.000 votos do 1º turno; senão todos no mesmo estágio). Faixa de 90%: 200 reamostragens dos municípios observados dentro da UF, resíduo municipal sorteado com peso nos votos e erro comum normal de 1,0 ponto, tudo só sobre o que falta; semente fixa (a faixa não treme). Abaixo de 1% das seções do país, `projetado: null` com `motivo_sem_projecao`.
- Hipóteses declaradas: a ordem de contagem das seções dentro de cada município repete a do 1º turno; K, K_uf e o erro comum são escolhas, não estimativas. Com a régua igual ao próprio 1º turno a validação é circular (devolve 51,01 a qualquer hora, com faixa de 49,40 a 52,55 às 18:00); serve de prova de aritmética, não de acerto.
- Resposta: `{ at, min, ele, cargo, rotulo, candidatos: {f, l}, cobertura: {pst, st, ts, pct_vv_observado, municipios_observados, municipios_fechados, municipios_total}, brasil, regioes[6], ufs[28], parametros: {K, K_uf, mesmo_estagio, erro_comum_pp, reps, nivel_faixa, minimo_pst, metodo}, motivo_sem_projecao, serie }`; bloco `{ sigla, nome, pst, pct_vv_observado, p1_f, observado: {f, l, p_f}, projetado: {f, l, p_f, p_l, p_f_validos, p_l_validos, faixa90} | null, swing_pp }`, percentuais de 0 a 100 com p_f = Flávio entre os dois. `serie`: `[min, p_f_proj, faixa_a, faixa_b, p_f_obs, pst]`, acumulada ao vivo (passo mínimo 60 s, grade de 5 min reconstruída por leituras "até o instante", 4 por chamada) e gravada em `data/projecao_2t_serie.json`. Cache de 10 s. Zod em `tests/api-schemas-2t.ts`, testes em `tests/projecao.test.ts`.

## Eventos novos no `evento` (motor grava; `/api/anomalias` entrega; o telão mostra)

Categorias que o telão passa a aceitar (hoje `src/ui/data/api.ts` só mantém `virada | regressao | fechou | atraso`): acrescentar `pausa`, `divergencia`, `abstencao`, `paralela`. Mapeamento tipo → texto e categoria em `src/server/textos.ts`.

| tipo | severidade | categoria | quando |
|---|---|---|---|
| `pausa_nacional_inicio` / `pausa_nacional_fim` | warn (error se ≥ 15 min) / info | pausa | arquivo nacional sem versão nova > 5 min com st < ts enquanto a soma das UFs avança |
| `pausa_uf_inicio` / `pausa_uf_fim` | warn / info | pausa | arquivo de UF sem versão nova > 10 min com st < ts enquanto o país avança |
| `soma_ufs_adiante` | warn | pausa | soma das UFs à frente do nacional em > 2% de ts por > 5 min |
| `uf_atrasada_1t` | warn | atraso | atraso vs curva do 1T ≥ 20 min (um evento por UF por patamar de 20 min) |
| `abstencao_atipica_mun` | warn | abstencao | município fechado com te ≥ 20.000 e \|pa_2t − pa_1t\| ≥ 5 pp |
| `abstencao_atipica_uf` | warn | abstencao | UF com ≥ 30% do te fechado e \|delta_pp\| ≥ 2 |
| `secao_tardia` | info | atraso | seção amostrada com encerramento > 18:00 BRT |
| `divergencia_paralela` | error | divergencia | BU da totalização paralela difere do BU oficial da mesma seção |
| `paralela_conferida` | info | paralela | lote conferido (detalhe com contagens) |
| `virada`, `uf_fechou` | warn, info | virada, fechou | hoje derivados no servidor; passam a ser gravados pelo coletor (o servidor mantém a derivação como reserva quando não há linha gravada) |

`detalhe` sempre JSON com os números usados (st, ts, minutos, pa_2t, pa_1t, campos divergentes). Eventos operacionais (`erro_interno`, `pausa_global`, `skew_relogio`) continuam fora do ar.

## Telas novas do telão (1920×1080, sem rolagem, SVG em TypeScript puro, `register()` em `src/ui/views/`)

| id | conteúdo | dados |
|---|---|---|
| `pres` (existe) | duelo nacional; corrigir título ("Presidente, 2º turno") e os `ELE = 6257` fixos em `mov`, `lotes`, `acumulado` (ler `config.eleicoes.federal`) | existentes |
| `regioes` | 5 regiões + exterior: barra duelo F×L em % válidos, pst, abstenção, seções/min, atraso vs 1T; destaque da região mais lenta | `/api/2t/regioes` |
| `ufs` | ranking das 27 UFs + ZZ, mais lentas primeiro: pst, atraso vs 1T em min, seções faltantes, municípios faltantes (munnr/munpt/munf), idade da última versão, ETA, chip "parada" | `/api/2t/ufs` |
| `atraso` | "quem está lerdo": top 8 UFs por atraso vs 1T com barras de pst 1T × 2T no mesmo relógio, os maiores municípios ainda abertos no país, previsão de quem fecha por último (p100 do 1T) | `/api/2t/ufs`, régua pela API |
| `abstencao` | mapa das UFs colorido por Δ abstenção vs 1T (divergente, saturando em ±5 pp), tabela por região, 6 municípios que mais subiram e 6 que mais caíram, rótulo "base: municípios fechados" | `/api/2t/abstencao` |
| `secoes` | cadeia de tempos: encerramento → emissão → recebimento → totalização; histograma do lag por UF (p50/p90) com a marca do 1T; seções fechadas tarde; cobertura da amostra | `/api/2t/secoes` |
| `pausas` | linha do tempo da noite: versões do arquivo nacional, soma das UFs, pausas detectadas (faixas), pausa do 1T (19:32–20:02) como referência cinza | `/api/2t/pausas`, `/api/lotes` |
| `gov-2t` | 6 duelos estaduais (AC, AM, DF, ES, RN, TO) em cartões: fotos, % válidos, pst, abstenção, virada recente; tecla de UF leva a `gov-uf` (mapa municipal, existe) | `/api/2t/estaduais` |
| `paralela` | totalização paralela: BUs recebidos, cobertura por UF, conferidos iguais/divergentes, placar dos BUs (rótulo fixo "soma dos BUs recebidos, não projeção"), últimas divergências | `/api/2t/paralela` |
| `alertas` | feed das últimas 12 anomalias com categoria, hora, UF e texto; contador por categoria | `/api/anomalias` |
| `evolucao` | % válidos F×L ao longo da noite: nacional grande + small multiples por região (ou por UF com `m`), com a curva de pst do 1T pontilhada | `/api/2t/evolucao` |

Playlist padrão do 2º turno (quando `config.turno === 2`): `pres` 25 s, `regioes`, `ufs`, `evolucao`, `gov-2t`, `abstencao`, `atraso`, `pausas`, `paralela`, `alertas`, `pres-uf $destaque` (máx 3). Teclas: `9` ritmo continua; novas telas acessíveis por `/` (busca) e pelo diretor. `#mock=1` precisa gerar dados sintéticos para todas as rotas novas (ensaio sem banco). Toda tela precisa funcionar com `ref_1t: null` e com `/api/2t/paralela` em `erro` (mostrar "fonte indisponível", nunca tela em branco).

## Público (GitHub Pages)

`scripts/exportar-publico.ts` chama a API local e grava `docs/assets/apuracao_2t/{estado,regioes,ufs,abstencao,estaduais,evolucao,pausas,secoes,paralela,anomalias}.json` + `manifest.json` (gerado_em, hashes). `scripts/publicar-loop.sh` roda a exportação e `git add/commit/push` desses arquivos a cada N minutos (padrão 5), só quando houver mudança. `docs/apuracao_2t_ao_vivo.html` (à mão, GA tag via `scripts/ga_tag.py`, card no manifesto de `social-cards.py`, entra no sitemap) lê esses JSON com recarga automática a cada 60 s e mostra: placar duelo, regiões, ranking de UFs, 6 estaduais, abstenção vs 1T, pausas, paralela e alertas. Sem framework; funciona sem JS com a última versão embutida? Não: página pública depende de fetch, mas mostra `gerado_em` e aviso de idade dos dados.

## Ensaio e verificação

- `bun run check` em zero. Testes de rota com fixtures 6258/6260 (zero e parcial) em `tests/fixtures/2t/` e contratos zod em `tests/api-schemas-2t.ts`.
- Ensaio: `scripts/semear-ensaio.ts --turno 2` (ou `#mock=1` no telão) precisa cobrir as telas novas.
- Pré-live (24/10): `APURACAO_ELEICOES=6258,6260 APURACAO_PLEITO=3221 APURACAO_DB=data/apuracao-2t.sqlite bun run sweep` (já feito em 21/10: 13.140 arquivos, 100% ok, zero 404); `scripts/preflight.sh`; `python3 ../scripts/contrast-audit.py --width 1920 <url de cada tela nova>`; `python3 ../scripts/render-audit.py <url>`.
