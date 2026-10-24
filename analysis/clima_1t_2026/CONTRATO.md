# Clima, bateria e abstenção no 1º turno de 2026: contrato entre as partes

Relatório: `docs/clima_abstencao_1t_2026.html` (gerado por `scripts/clima-1t-build.py` a partir de
`analysis/clima_1t_2026/clima.json`; nunca editar o HTML). Motor: `scripts/clima-1t.py` + módulos
`scripts/clima_1t/` (< 1.000 linhas cada). Previsão: `scripts/clima-1t-previsao.py` (só a parte de
previsão, rápida, rodada todo dia pelo workflow `.github/workflows/clima_previsao.yml`).
Mapa de fiscais: `docs/fiscais_mapa.html` + `docs/assets/fiscais_mapa/app.js` leem
`docs/assets/fiscais_mapa/clima/<UF>.json` e `docs/assets/fiscais_mapa/clima/previsao.json`.
Regras da casa: pt-BR, sem travessão, nunca "fraude", leitura agregada por seção e local, registro de
bateria é operação prevista e não irregularidade, correlação não é causa, número com IC e fonte ao lado.

## Fontes (todas locais, menos a Open-Meteo)
- Locais e coordenadas: `data/outputs/locais_votacao_2026.sqlite` (tabela `secao`; 95.115 locais, 94.278 com
  coordenada no Brasil; 3 fora do território viram null). `local_id` = `UF-MUNTSE-ZONA-LOCALNR`.
- Boletins do 1º turno: `apuracao/data/secoes_2026.sqlite` (`bu`: aptos, comparecimento, abertura, encerramento,
  modelo_urna; `voto_secao` cargo 1). Abstenção 2022 2º turno por seção: a mesma fonte do Politize
  (`scripts/politize/fontes.py`, `ZIP_DETALHE_2022`, `ler_2022_2t`).
- Logs do 1º turno: `data/outputs/logs_urnas_2026.sqlite`, tabela `metricas`, `resumo` JSON:
  `contagens.eventos_bateria`, `bateria_fases` (pre_zeresima, pre_votacao, votacao, pos_votacao),
  `contagens.reinicios_durante_votacao`, `contagens.erros_na_janela_votacao`, `tempos_validos`,
  `primeiro_computo_s`, `ultimo_computo_s`. Simultaneidade já publicada em `docs/assets/fiscais_mapa/uf/<UF>.json`
  (códigos `bateria_votacao_local` e `bateria_votacao_isolada` na coluna `logs`).
- Clima observado: Open-Meteo archive (ERA5/ERA5-Land, `archive-api.open-meteo.com/v1/archive`), uma chamada por
  célula de 0,25° (floor(lat/0,25), floor(lon/0,25); ponto consultado = centro da célula), janela 2026-10-02 a
  2026-10-05 em diário (`precipitation_sum`, `precipitation_hours`, `wind_gusts_10m_max`, `temperature_2m_max`) e
  horário só em 2026-10-04 (`precipitation`, `wind_gusts_10m`), `timezone=America/Sao_Paulo`. 6.539 células.
  Respostas cruas em `data/originals/clima_1t_2026/archive/<cel>.json` (pasta ignorada pelo git);
  consolidado em `analysis/clima_1t_2026/celulas_archive.json`. Retomável; 429 espera e segue; nunca inventar.
  Os 2.033 pontos já baixados em `analysis/mudancas_secoes_2t/clima/open_meteo.json` servem de conferência.
- Clima previsto: Open-Meteo forecast (`api.open-meteo.com/v1/forecast`), células de 0,5°, `forecast_days=8`,
  diário `precipitation_sum`, `precipitation_probability_max`, `wind_gusts_10m_max`, `weather_code`;
  2.239 células. Consolidado em `docs/assets/fiscais_mapa/clima/previsao.json` com `gerado_em` e `alvo` 2026-10-25.

## Variáveis por local (todas calculadas pelo motor)
`chuva_04_10_mm` (diária), `chuva_votacao_mm` (soma horária 07h a 18h locais de 04/10), `hora_pico_chuva`,
`chuva_03_10_mm`, `chuva_02a05_max_mm`, `rajada_04_10_kmh`, `rajada_votacao_kmh` (máximo horário 07h a 18h),
`faixa_chuva` em {seca 0 mm, fraca até 5, moderada 5 a 20, forte 20 a 50, muito forte acima de 50},
`faixa_rajada` em {até 40, 40 a 60, 60 a 80, acima de 80 km/h}; por local também `urnas`, `urnas_bateria`,
`urnas_bateria_votacao`, `urnas_reinicio`, `aptos`, `comparecimento`, `abst_pct`, `abst22_pct` (seções casadas),
`dif_abst_pp` = abst 2026 1T menos abst 2022 2T, `abertura_atrasada` (primeiro voto 8h30 ou depois, fuso de
`apuracao_2026.secoes_base.fusos_por_municipio`), `flavio_v`, `lula_v`.

## Análises (payload `analysis/clima_1t_2026/clima.json`)
1. `bateria_x_chuva`: parcela de urnas com bateria durante a votação por faixa de chuva (diária e nas horas de
   votação) e por faixa de rajada; razão contra a faixa seca com IC 95% por bootstrap de células (2.000 réplicas);
   regressão logística com efeito fixo de UF e controles (tamanho da seção, modelo da urna) via statsmodels, odds
   ratio por 10 mm e por 10 km/h; mesma coisa para bateria em qualquer momento e para reinício. Separar bateria
   simultânea no município (rede) de isolada (tomada/fonte). Resultado esperado publicado nos dois sentidos.
2. `abstencao_x_chuva`: abstenção 2026 e dif_abst_pp (contra 2022) por faixa de chuva nas horas de votação, com
   controle: comparação dentro do mesmo município quando o município tem células em faixas diferentes, e
   dentro da mesma UF; IC por bootstrap de células; regressão linear ponderada por aptos com efeito fixo de UF.
   Também por rajada e por chuva + bateria (interação).
3. `abstencao_x_bateria`: dif_abst_pp das urnas com bateria durante a votação contra as demais do mesmo município
   (ponderado por aptos, IC), separando simultânea e isolada; e tempo em bateria não é medido: dizer.
4. `cadeia_completa`: tabela 2x2x2 chuva forte × bateria × abstenção acima da mediana do município, com contagens.
5. `locais_curiosos` (listas de até 30, cada item com local_id, nome, município, UF, números e link do mapa
   `fiscais_mapa.html#uf=XX&l=<local_id>`): (a) chuva forte + bateria durante a votação + dif_abst alta;
   (b) bateria durante a votação em 5+ urnas com chuva zero e sem outras urnas do município em bateria (pista de
   rede ou prédio); (c) chuva muito forte sem nenhuma bateria; (d) maior salto de abstenção contra 2022 entre os
   locais com chuva forte; (e) locais com chuva forte onde a abstenção caiu; (f) Confresa (MT) e os 334 pares de
   `analysis/mudancas_secoes_2t/mudancas.json` (origem) cruzados com estas variáveis.
6. `mapa_resumo`: por UF, chuva média ponderada por aptos em 04/10, parcela de locais com chuva forte, parcela de
   urnas com bateria durante a votação, abstenção.
7. `previsao_25_10`: regra de risco declarada: alto = chuva_mm ≥ 30 ou rajada ≥ 70 km/h ou (prob ≥ 80% e chuva ≥ 15);
   médio = chuva ≥ 10 ou rajada ≥ 50 ou prob ≥ 60%; baixo = o resto; por UF: eleitores e locais por nível de risco;
   lista das 30 cidades (município) com mais eleitores em risco alto. Rótulo: previsão de modelo global a 0,5°,
   muda todo dia; é indicativo de atenção, não previsão do que vai acontecer no prédio.
8. `limites` e `controles` (SHA-256 das fontes, totais batendo com o Politize e o motor das mudanças).

## Saídas para o mapa de fiscais
- `docs/assets/fiscais_mapa/clima/<UF>.json`: `{"gerado_em","fonte","celula_graus":0.25,"colunas":[local_id, cel,
  chuva_04_10_mm, chuva_votacao_mm, hora_pico_chuva, rajada_04_10_kmh, rajada_votacao_kmh, faixa_chuva, faixa_rajada,
  urnas, urnas_bateria, urnas_bateria_votacao, abst_pct, abst22_pct, dif_abst_pp],"linhas":[...]}` (um por UF, inclusive
  locais sem coordenada com clima null).
- `docs/assets/fiscais_mapa/clima/previsao.json`: `{"gerado_em","alvo":"2026-10-25","fonte","celula_graus":0.5,
  "regra_risco":{...},"dias":[...],"celulas":{"<floor(lat*2)/2>,<floor(lon*2)/2>":{"chuva_mm","prob_pct","rajada_kmh",
  "codigo_wmo","risco","serie":[{data,chuva_mm,prob_pct,rajada_kmh}]}},"resumo":{"por_uf":...,"cidades_risco_alto":[...]}}`.
  O app resolve o local pela chave da célula a partir de lat/lon. Chave com uma casa decimal exata (ex.: `-23.5,-46.5`).
- `docs/assets/clima_1t/dados.json` (payload público) e `docs/assets/clima_1t/locais.csv.gz`.

## Camada de mudanças no mapa (build do mapa, não do motor)
`scripts/fiscais-mapa-build.py` lê `docs/assets/politize/dados/mudancas/indice.json` e `<UF>/<zona>.json` (1.362 seções,
união arquivo + painel) e acrescenta a cada seção a coluna `mudanca` (null ou `{cat, nome_cat, fonte, nome_1t, end_1t,
nome_2t, end_2t, bairro_2t, cep_2t, lat_2t, lon_2t, distancia_m, maps_novo, motivo_tre, url_tre}`), cria as linhas das
seções que não estavam no acervo do mapa (nível `mudanca`, sem pontuação histórica) e registra no `indice.json` o
critério `mudanca_endereco` (nome "Mudou de endereço para o 2º turno", contagem, frase) para o seletor "Um critério só"
e para a caixa "O que mostrar". O ponto da seção que mudou fica no local do 2º turno quando há coordenada, com o
local do 1º turno na ficha.

## Atualização de 24/10: cenário territorial e rodada única
- `clima-1t-build.py` preserva a análise original de 04/10 em `clima.json` e carrega a previsão corrente uma só vez. Mapa, tabelas, metadados e JSON público usam a mesma rodada, inclusive SHA-256. A rodada integral fica em `analysis/clima_1t_2026/previsoes/`. O workflow diário reconstrói o relatório e os downloads. Respostas sem o dia alvo não substituem previsão completa.
- `territorio.py` cruza totalização municipal de `analysis/apuracao_2026/dados/presidente.json` com o índice de células por `(UF, código TSE)`, sem exterior. O mapa estadual usa aptos e presentes completos do TSE, não o subconjunto das urnas com clima/log.
- Cenário de persistência: A₂(m) = A₁(m), sem incremento climático, validação preditiva municipal, IC de previsão ou probabilidade de ranking. O estudo observacional não identificou um acréscimo causal transportável; não identificar efeito não prova efeito zero.
- Atenção conjunta: pelo menos 10 mil aptos, abstenção anterior acima da média brasileira sem exterior e pelo menos 50% do cadastro mapeado em risco climático alto. Exige previsão para todas as células mapeadas e ordena por eleitores expostos, não por faltas esperadas. Cortes editoriais, não ajustados ao resultado de 25/10. Todos os 5.571 municípios ficam no JSON; tabela mostra até 25 destaques.
- Abstenção usa totalização; exposição e chuva média usam eleitores do cadastro georreferenciado. Denominadores distintos, cobertura explicitada, nenhuma imputação aos sem clima e nenhum deslocamento automático dos prédios realocados. Chuva prevista diária não é chuva nas horas da votação.
- `docs/assets/clima_1t/cenario_2t.json` guarda taxas, exposição, regra, universos e hashes das fontes. A análise original, centrais eleitorais e snapshots das pesquisas não são recalculados por este build.
