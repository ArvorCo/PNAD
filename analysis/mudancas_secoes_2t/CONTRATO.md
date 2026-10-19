# Mudanças de local de votação entre os turnos de 2026: contrato entre as partes

Laudo: `docs/mudancas_secoes_abstencoes.html` (gerado por `scripts/mudancas-secoes-2t-build.py`
a partir de `analysis/mudancas_secoes_2t/mudancas.json`; nunca editar o HTML gerado).
Motor: `scripts/mudancas-secoes-2t.py` + módulos `scripts/mudancas_secoes_2t/` (cada arquivo < 1.000 linhas).
Alerta no app: `docs/assets/politize/dados/mudancas/` lido por `docs/assets/politize/mudancas.js`.
Thread: `docs/mudancas_secoes_thread.html`, 3 cards 1:1, gerada por `scripts/mudancas-secoes-2t-thread.py`.
Regras da casa: pt-BR, sem travessão, nunca "fraude", frase curta, número com fonte e limite ao lado,
"eleitorado de X" (nunca "eleitores dele"), leitura agregada por seção (voto secreto).

## Fonte primária (já no disco)

- 1º turno: `data/raw/tse_eleitorado/eleitorado_local_votacao_2026.zip` (gerado pelo TSE em 02/10/2026 06:29,
  SHA-256 `045df0a517be35490bcdfdbaf91ed2224122efec9b0d2ab199836e15f8b0805c`, só `NR_TURNO=1`).
- 2º turno: `data/raw/tse_eleitorado/locais_2t/eleitorado_local_votacao_2026_20261018.zip` (gerado 18/10/2026 20:27,
  baixado 19/10 02:55 de `cdn.tse.jus.br/estatistica/sead/odsele/eleitorado_locais_votacao/eleitorado_local_votacao_2026.zip`,
  SHA-256 `a948d3e587d7116ffe003fb07a083b2d1d64ce9a236f703f92d36e168f1b5adb`, traz `NR_TURNO` 1 e 2; usar as linhas 2).
- Chave da seção: (`SG_UF`, `CD_MUNICIPIO`, `NR_ZONA`, `NR_SECAO`). 517.179 linhas por turno, todas `ATIVO`,
  499.248 principais e 17.931 agregadas. Nenhuma seção falta de um lado.
- CSV latin-1, separador `;`, decimais com vírgula. `NR_LOCAL_VOTACAO_ORIGINAL` = local cadastrado originalmente;
  quando o original está interditado, o TRE define outro local temporário (leiame.pdf do TSE, p. "NR LOCAL VOTACAO ORIGINAL").

## Classificação de cada seção (regra fixa, uma categoria por seção)

Comparar a linha do 1T (arquivo de 02/10) com a linha do 2T (arquivo de 18/10):

| cod | nome | regra |
|---|---|---|
| A | retorno ao original | `local_1t != local_2t`, `local_1t != orig_1t`, `local_2t == orig_2t` |
| B | nova realocação | `local_1t != local_2t`, `local_1t == orig_1t`, `local_2t != orig_2t` |
| C | de um temporário para outro | `local_1t != local_2t`, ambos diferentes do original |
| X | número original mudou | `local_1t != local_2t` e nenhum dos casos acima |
| D | mesmo número, nome e endereço mudaram | `local_1t == local_2t`, nome e endereço diferentes |
| E | mesmo número, endereço mudou | só o endereço difere |
| F | mesmo número, só o nome mudou | só o nome difere |
| G | mesmo número, coordenada moveu mais de 300 m | nome e endereço iguais, haversine > 300 m |
| H | mesmo número, coordenada moveu até 300 m | idem, <= 300 m |
| Z | igual | nada mudou |

Contagem de referência (19/10, cálculo do orquestrador): A 754 seções / 222.482 eleitores; B 255 / 72.878;
C 26 / 9.088; D 86 / 27.388; E 220 / 57.308; F 208 / 66.456; G 575 / 169.170; H 1.034 / 284.030; Z 514.021.
No 1T, 6.535 seções (1.916.865 eleitores) já votavam em local diferente do original; no 2T são 6.036 (1.767.261).

**Mudança real de endereço** (o que o eleitor sente) = A + B + C + X + D + (E e G filtrados). Em E e G o motor
precisa separar edição de cadastro de mudança de prédio: normalizar o endereço (maiúsculas, sem acento, sem
pontuação, abreviações R./RUA, AV./AVENIDA, N./Nº/N, sem complemento depois de " - ") e comparar o logradouro;
em G, deslocamento acima de 50 km é correção de coordenada, não mudança (marcar `coord_suspeita`). Cada seção
leva `mudanca_real: true|false` e `motivo_classificacao` em texto. F e H nunca são mudança real. Caso de
controle: RJ, município 60011, zona 188, seções 123–127, local 1295, Rua Muaná 105 → Rua Irapuá 243 (categoria D,
TRE-RJ confirmou 1.800 eleitores): tem de sair `mudanca_real: true`.

Distância da mudança: haversine entre a coordenada do 1T e a do 2T da mesma seção, em metros, `null` sem
coordenada, e `distancia_suspeita` quando acima de 50 km.

## Números públicos a confrontar (fontes em `fontes.json`, com URL, data, hash do HTML quando salvo)

- TSE via Agência Brasil 17/10: 4.352 seções (0,87% de 499.248), SP 982, MG 514, RJ 431, BA 312.
- Relatório anexo à petição da coligação Brasil Pronto pra Mais (TSE 0603126-92.2026.6.00.0000, 17/10): 4.864 seções, 1.795.241 eleitores.
- Consulta da Revista Fórum ao sistema do TSE em 18/10: 2.033 seções (2.015 no Brasil, 18 no exterior), 592.870 eleitores. O Tempo/Folhapress 18/10: 2.033 seções, 592 mil eleitores.
- TRE-RJ: um local, 5 seções, 1.800 eleitores. TRE-RS: 3 municípios, 4 locais, 9 seções. TRE-PI: 2 locais. TRE-CE: 4 locais. TRE-PA: 7 locais. TRE-PR: 8 locais em 7 municípios. TRE-ES: 3 locais.
- Hipótese a testar (não afirmar antes de testar): 1.795.241 eleitores do relatório da coligação está perto dos 1.767.261 eleitores das 6.036 seções que no 2T votam fora do local original; o número divulgado pode contar seções em local temporário, inclusive as que já estavam assim no 1T, e não mudanças entre turnos.

## Cruzamentos (só leitura)

- Votação do 1T por seção: `apuracao/data/secoes_2026.sqlite`, `voto_secao` (cargo 1, tipo 1 nominal: 22 Flávio, 13 Lula; 2 branco; 3 nulo), `bu_cargo` (aptos, comparecimento), `bu` (abertura, encerramento, modelo_urna, tipo_urna, hab_ano_nascimento, comp_sem_biometria). Chave (uf, mun, zona, secao); seção agregada soma na principal (`secao.nsp`).
- Logs do 1T: `docs/assets/fiscais_mapa/uf/<UF>.json` (`colunas_secoes` em `indice.json`: li, secao, nivel, pontuacao, criterios, explicacao, aptos, comparecimento, flavio_pct, lula_pct, logs, atencao, tempo_voto, processo_mediana, cadencia_mediana; `logs` é lista de códigos como `bateria`, `bateria_votacao_local`, `bateria_votacao_isolada`, `reinicios`, `erro_tecnico`, `suspensoes`; `atencao` 0–3). Alternativa completa: `data/outputs/logs_urnas_2026.sqlite`, tabela `metricas`, campo `resumo` JSON (`contagens.eventos_bateria`, `bateria_fases`, `contagens.reinicios_durante_votacao`).
- Politize: `docs/assets/politize/dados/zona/<UF>/<zona>.json` (`secoes.colunas`/`linhas`; `local_id` = `UF-MUNTSE-ZONA-LOCALNR`), `docs/assets/politize/dados/fiscal/<UF>/<zona>.json`.
- Clima: `analysis/mudancas_secoes_2t/clima/open_meteo.json` (escrito pelo agente de clima; ver abaixo).
- Notas dos TREs: `analysis/mudancas_secoes_2t/tre_noticias.json` (escrito pelo agente de notícias; ver abaixo).

## Saídas do motor

1. `analysis/mudancas_secoes_2t/mudancas.json`, com `gerado_em`, `fontes` (caminho, bytes, sha256, data de geração do TSE),
   `regras` (texto das categorias), `resumo` (por categoria: seções, eleitores; mudança real: seções, locais de origem,
   locais de destino, municípios, UFs, eleitores, aptos do 1T, mediana e p90 da distância), `confronto_publico`
   (nossos números ao lado de cada número público, com a hipótese de reconciliação e o que ela não explica),
   `por_uf` (seções e eleitores por categoria e mudança real; comparar com as notas dos TREs quando houver),
   `por_municipio` (top 40 por eleitores em mudança real), `locais` (um item por par origem→destino: uf, mun_tse,
   municipio, zona, local_1t, nome_1t, end_1t, bairro_1t, lat/lon 1t, local_2t, nome_2t, end_2t, bairro_2t, cep_2t, lat/lon 2t,
   distancia_m, categoria, mudanca_real, secoes[], eleitores, aptos_1t, comparecimento_1t, abst_1t_pct, flavio_1t, lula_1t,
   terceira_1t, brancos, nulos, flavio_v, lula_v, margem_v, logs_1t {bateria, bateria_votacao, reinicios, atencao_max, codigos},
   abertura_min_atrasada (seções com primeiro voto 30 min ou mais depois das 8h), fila_fechamento (último voto depois das 18h),
   clima {chuva_04_10_mm, chuva_max_05a18_mm, dia_chuva_max, rajada_max_kmh, dia_rajada_max, fonte}, motivo_tre (texto e url quando casado por município/local)),
   `comportamento_1t` (nas seções com mudança real contra o resto do município e contra o país: Flávio e Lula nos válidos,
   abstenção, brancos e nulos; diferença em pontos com IC 95% por bootstrap de seções),
   `intercorrencias_1t` (parcela das seções com bateria, bateria durante a votação, reinício, abertura atrasada, fila,
   atenção 2 ou 3, contra o país; razão e IC),
   `clima_resumo` (parcela dos locais de origem com chuva acima de 20 mm e de 50 mm em 04/10 e no período 05 a 18/10,
   contra os locais de controle; quantos têm rajada acima de 60 km/h; lista dos que não têm nada no período),
   `cenarios_abstencao` (para +2, +5, +10 e +20 pontos de abstenção extra sobre os aptos das seções com mudança real, voto perdido
   proporcional à composição do 1T da seção: votos perdidos por Flávio e por Lula, saldo na diferença F−L em votos e em
   pontos do total nacional de válidos do 1T; separar categoria A, que volta ao original, de B+C+D+E+G; fonte da magnitude:
   Brady e McNulty 2011, mudança de local reduz comparecimento em cerca de 1,9 ponto, citada como ordem de grandeza),
   `quem_perde` (frase gerada pelos números, nas duas direções), `limites` (lista).
2. `docs/assets/mudancas_secoes/dados.json` (cópia pública do payload sem campos internos) e
   `docs/assets/mudancas_secoes/secoes.csv` (uma linha por seção com mudança real, com as colunas acima).
3. `docs/assets/politize/dados/mudancas/indice.json` (`versao`, `gerado_em`, `total_secoes`, `total_eleitores`, `por_uf`,
   `categorias` com nome e frase em português corrente) e `mudancas/<UF>/<zona>.json` só das zonas com alguma seção em
   mudança real: `{"uf","zona","secoes":{"<secao>":{"categoria","nome_1t","end_1t","bairro_1t","nome_2t","end_2t",
   "bairro_2t","cep_2t","lat_2t","lon_2t","distancia_m","eleitores","motivo_tre","url_tre","mesmo_predio_1t":[secoes...]}}}`.
   Seções agregadas aparecem pela principal e também pelo próprio número.
4. Relatório `analysis/mudancas_secoes_2t/relatorio.md` com todos os números do resumo e os controles que passaram ou não.
5. Testes em `tests/test_mudancas_secoes_2t.py`: classificação com linhas sintéticas, caso de controle do RJ, soma das
   categorias = 517.179, cenários fecham, nenhum travessão no JSON público, CSV com o mesmo total.

## Clima (agente de clima)

Entrada: `analysis/mudancas_secoes_2t/pontos_clima.json` (lista de pontos `{id, lat, lon, grupo}`; `grupo` = `mudanca`
para a coordenada do 1T de todo local com qualquer categoria A–G, `controle` para amostra de locais inalterados).
Saída: `analysis/mudancas_secoes_2t/clima/open_meteo.json`: por `id`, série diária 2026-09-28 a 2026-10-18 de
`precipitation_sum` (mm), `precipitation_hours`, `wind_gusts_10m_max` (km/h), `temperature_2m_max`, com `fonte`
(`archive` ERA5 ou `forecast` com past_days), URL de cada chamada, hora da coleta. Guardar as respostas cruas em
`data/originals/mudancas_secoes_2t/open_meteo/<id>.json`. Se o INMET responder, gravar também
`clima/inmet_diario.json` das estações a até 50 km dos pontos de mudança, com a estação, distância e a mesma janela.

## Notas dos TREs (agente de notícias)

Saída: `analysis/mudancas_secoes_2t/tre_noticias.json`: lista de itens `{uf, veiculo, titulo, url, data, acesso_em,
sha256_html, caminho_local, locais:[{municipio, zona, local_antigo, local_novo, secoes, eleitores, motivo}], motivos_citados[],
numero_total_declarado, trecho}` para as 27 UFs quando houver nota do TRE, mais as matérias nacionais já citadas acima.
HTML cru em `data/originals/mudancas_secoes_2t/noticias/<uf>_<slug>.html`. Nunca inventar motivo; "não informado" é válido.

## Adendo de 19/10 (orquestrador): o efeito medido no próprio 1º turno

O 1º turno já foi um experimento natural: 6.535 seções (1.916.865 eleitores) votaram em local diferente do original
em 04/10 (`local_1t != orig_1t` no arquivo de 02/10), inclusive as transferências do TRE-RJ para fora de áreas
dominadas por facções (Maré: petição da coligação cita 52% do eleitorado votando fora da comunidade e abstenção
de 28,46%; levantamento do ConJur citado pela Agência Pública: nove zonas do RJ com locais alterados tiveram
abstenção média de 25,83% contra 21,08% no país). O motor acrescenta ao payload o bloco `efeito_1t`:

- `abstencao`: abstenção do 1T de 2026 nas seções em local temporário contra as demais seções do mesmo município
  (diferença ponderada por aptos) e contra o país; IC 95% por bootstrap de seções.
- `dif_em_dif`: a mesma comparação na variação 2026 1T menos 2022 2T da abstenção da mesma seção (aptos e
  comparecimento de 2022 por seção: a fonte que o Politize já usa, ver `scripts/politize/fontes.py`, `ZIP_DETALHE_2022`,
  e a forma de casar seção 2022 com 2026 em `scripts/politize/montagem.py`); publicar cobertura do casamento.
- `dose_resposta`: só para as seções da categoria A (temporário no 1T, original no 2T) a distância entre o local
  temporário (coordenada do 1T) e o original (coordenada do 2T) é conhecida; cruzar a variação da abstenção com a
  distância em faixas (até 500 m, 500 m a 1 km, 1 a 2 km, 2 a 5 km, acima de 5 km), ponderado por aptos, com IC.
- `direcao`: Flávio e Lula nos válidos do 1T nas seções em local temporário contra as demais do município e o país.
- `rj`: recorte do Rio de Janeiro (município 60011) por zona: seções em local temporário, abstenção 1T, 2022 e diferença.
- Rótulo: diferença medida com controles por município e por 2022, não efeito causal identificado; a seleção dos locais
  pelo TRE não é aleatória. O que o 1T mede para o 2T: as 6.036 seções que seguem fora do original em 25/10 e as
  novas realocações carregam esse mesmo risco; a categoria A volta ao original e pode recuperar comparecimento.
