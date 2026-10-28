# Dataset aberto por seção: 1º e 2º turnos de 2026

**Universo.** Seções do Brasil e do exterior com boletim de urna em ao menos um dos dois turnos de 2026 (união das chaves dos dois bancos locais). Nenhum voto de seção
pequena é ocultado: o TSE publica o boletim de cada seção.

**Arquivo.** `secoes_1t_2t_2026.csv.gz`, 32.321.393 bytes (32,3 MB),
499.207 linhas de dados mais o cabeçalho, CSV separado por vírgula, UTF-8, gzip.
SHA-256 `199bb2fe46abe46a4c808f381992dfba033ebca61ec90a4d608d5f26a2b0e060`. Gerado em 2026-10-26T23:50:40+00:00.

**Rótulo.** Sinal pede explicação, não prova irregularidade; atipicidade estatística não é irregularidade. Os sinais e o grupo da mistura ordenam o que merece
conferência; não identificam causa nem conduta.

**Vazio** significa sem dado: seção sem boletim naquele turno, sem log processado,
sem cadastro no Politize-se ou fora do motor da mistura (exterior e seções com menos
de 30 aptos). Horários estão como impressos no BU, sem conversão de fuso.

**Fontes.** Boletins de urna decodificados dos arquivos públicos do TSE (bancos locais do
coletor), logs das urnas e camada pública do Politize-se:
- `apuracao/data/secoes_2026.sqlite`: 8.550.633.472 bytes, SHA-256 `2cfbf8259e7461ec313f3554716d6f6b86079eaa10310b3230aabd3fed1941c8`
- `apuracao/data/secoes_2t_2026.sqlite`: 1.504.579.584 bytes, SHA-256 `f442ae7ba203803ec21a96890cdbb7a51e9718d48bc12014a15159f9c73c1189`
- `docs/assets/politize_se/dados/indice.json`: 639.217 bytes, SHA-256 `25feb7166ea6921d3628c6c85181623dd15cdd8c80d88a775996241282973a61`

Cada log de urna do 2º turno tem URL oficial e SHA-256 em `docs/assets/logs_urnas_2t_2026/secoes.csv.gz`. Os bancos
brutos (BUs decodificados, RDV, arquivos `.vsc` e logs) não cabem no repositório e ficam
em depósito separado; seus hashes são publicados em `analysis/apuracao_2t_2026/deposito_bruto.json`
quando o depósito é enviado.

## Colunas

| coluna | definição | fonte | unidade |
|---|---|---|---|
| `uf` | Unidade da federação; ZZ é o exterior | BU | sigla |
| `mun_tse` | Código TSE do município, cinco dígitos com zeros à esquerda | BU | código |
| `municipio` | Nome do município no cadastro do Politize-se | Politize-se | texto |
| `zona` | Zona eleitoral | BU | número |
| `secao` | Seção eleitoral (seção principal; seções agregadas entram nela) | BU | número |
| `local_id` | Identificador do local de votação (UF-município-zona-número do local) | Politize-se | código |
| `aptos_1t` | Eleitores aptos na urna no 1º turno (seção mais trânsito) | BU | pessoas |
| `comparecimento_1t` | Eleitores que compareceram no 1º turno | BU | pessoas |
| `lula_1t` | Votos nominais em Lula (13) para presidente no 1º turno | BU | votos |
| `flavio_1t` | Votos nominais em Flávio Bolsonaro (22) para presidente no 1º turno | BU | votos |
| `outros_1t` | Votos nominais nas demais candidaturas a presidente no 1º turno | BU | votos |
| `brancos_1t` | Votos em branco para presidente no 1º turno | BU | votos |
| `nulos_1t` | Votos nulos para presidente no 1º turno | BU | votos |
| `sem_biometria_1t` | Eleitores que compareceram sem biometria cadastrada no 1º turno | BU | pessoas |
| `ano_nascimento_1t` | Eleitores habilitados por dados biográficos (ano de nascimento) no 1º turno | BU | pessoas |
| `biometria_1t` | Eleitores habilitados pela biometria no 1º turno | BU | pessoas |
| `abertura_1t` | Horário do primeiro voto no 1º turno, como impresso no BU, sem conversão de fuso | BU | data e hora |
| `encerramento_1t` | Horário do último voto no 1º turno, como impresso no BU | BU | data e hora |
| `emissao_bu_1t` | Horário de emissão do BU no 1º turno | BU | data e hora |
| `recebimento_1t` | Recebimento do arquivo pelo TSE no 1º turno, como publicado | BU | data e hora |
| `urna_1t` | Número interno (série) da urna que emitiu o BU no 1º turno | BU | número |
| `modelo_1t` | Modelo da urna no 1º turno (UE2009 a UE2022), lido do log | log | texto |
| `tipo_urna_1t` | Tipo da urna no 1º turno: 1 seção, 3 contingência, 4 reserva de seção, 6 reserva encerrando seção | BU | código |
| `tipo_arquivo_1t` | Tipo do arquivo no 1º turno: 1 votação na urna, 2 votação recuperada, 3 a 6 sistema de apuração | BU | código |
| `cargas_1t` | Número de cargas no histórico da urna no 1º turno | BU | contagem |
| `aptos_2t` | Eleitores aptos na urna no 2º turno (seção mais trânsito) | BU | pessoas |
| `comparecimento_2t` | Eleitores que compareceram no 2º turno | BU | pessoas |
| `lula_2t` | Votos nominais em Lula (13) no 2º turno | BU | votos |
| `flavio_2t` | Votos nominais em Flávio Bolsonaro (22) no 2º turno | BU | votos |
| `brancos_2t` | Votos em branco para presidente no 2º turno | BU | votos |
| `nulos_2t` | Votos nulos para presidente no 2º turno | BU | votos |
| `sem_biometria_2t` | Eleitores que compareceram sem biometria cadastrada no 2º turno | BU | pessoas |
| `ano_nascimento_2t` | Eleitores habilitados por dados biográficos (ano de nascimento) no 2º turno | BU | pessoas |
| `biometria_2t` | Eleitores habilitados pela biometria no 2º turno | BU | pessoas |
| `abertura_2t` | Horário do primeiro voto no 2º turno, como impresso no BU, sem conversão de fuso | BU | data e hora |
| `encerramento_2t` | Horário do último voto no 2º turno, como impresso no BU | BU | data e hora |
| `emissao_bu_2t` | Horário de emissão do BU no 2º turno | BU | data e hora |
| `recebimento_2t` | Recebimento do arquivo pelo TSE no 2º turno, como publicado | BU | data e hora |
| `urna_2t` | Número interno (série) da urna que emitiu o BU no 2º turno | BU | número |
| `modelo_2t` | Modelo da urna no 2º turno (UE2009 a UE2022), lido do log | log | texto |
| `tipo_urna_2t` | Tipo da urna no 2º turno: 1 seção, 3 contingência, 4 reserva de seção, 6 reserva encerrando seção | BU | código |
| `tipo_arquivo_2t` | Tipo do arquivo no 2º turno: 1 votação na urna, 2 votação recuperada, 3 a 6 sistema de apuração | BU | código |
| `cargas_2t` | Número de cargas no histórico da urna no 2º turno | BU | contagem |
| `urna_situacao` | Situação da urna entre os turnos: mesma, mesma_recarga, reserva, nova, outra_secao_zona, outra_secao_municipio, outro_municipio, sem_1t | Politize-se | categoria |
| `escore_sinais_2t` | Número de sinais do 2º turno na seção (regras em politize_se/secoes) | Politize-se | contagem |
| `sinais_2t` | Sinais do 2º turno separados por barra vertical: delta, sem_bio, ano_nasc, salto_bio, tardia, papel | Politize-se | lista |
| `log_atencao_1t` | Nível de atenção do log da urna no 1º turno, 0 a 3 (0 rotina, 1 um sinal, 2 sinais combinados, 3 conferir o arquivo) | log | nível |
| `log_atencao_2t` | Nível de atenção do log da urna no 2º turno, mesma escala | log | nível |
| `log_sinais_2t` | Diagnósticos do log do 2º turno separados por barra vertical (catálogo em politize_se/dados/indice.json) | log | lista |
| `mudanca_local` | 1 quando a seção mudou de prédio entre os turnos (mudança real pelo cadastro do TSE), 0 quando não; vazio sem cadastro | Politize-se | 0 ou 1 |
| `ml_grupo` | Grupo da mistura estatística dos dois turnos (0 a k menos 1); vazio para exterior e seções fora do motor | mistura | código |
| `ml_anomalo` | 1 quando a seção está no grupo atípico do país, 0 quando não; vazio sem dado | mistura | 0 ou 1 |
| `ml_p` | Parcela das seções do país com densidade menor na mistura (0,01 = entre as 1% menos prováveis) | mistura | fração |

Fonte "BU": boletim de urna decodificado. "log": log da urna (modelo e diagnósticos).
"Politize-se": camada pública em `docs/assets/politize_se/dados/`. "mistura": modelo
estatístico dos dois turnos (`analysis/apuracao_2t_2026/CONTRATO_ANOMALIA.md`).

## Listas municipais: menos votos no 2º turno

Dois arquivos com o mesmo esquema, CSV separado por vírgula, ponto como separador
decimal, UTF-8, sem compressão, ordenados da maior perda para a menor:

- `municipios_flavio_menos_votos_2t.csv`: municípios do Brasil, sem o exterior, em que Flávio teve menos votos absolutos no 2º turno do que no 1º (arquivo de presidente completo nos dois turnos); 938 linhas de dados mais o cabeçalho, 133.344 bytes, SHA-256 `a79cac30ac4ab38f1e0416ff34a1580cddfd51616c39cd0fa969c381545d0389`.
- `municipios_lula_menos_votos_2t.csv`: municípios do Brasil, sem o exterior, em que Lula teve menos votos absolutos no 2º turno do que no 1º (arquivo de presidente completo nos dois turnos); 79 linhas de dados mais o cabeçalho, 11.720 bytes, SHA-256 `b04cca559d46d1f5be2342c70f6c3acce9ea7e143b90c21211087c596aee300d`.

**Fonte.** `analysis/apuracao_2t_2026/dados/comparacao_1t.json` (gerado em 2026-10-27T23:36:02Z); `analysis/apuracao_2t_2026/dados/governadores.json` (gerado em 2026-10-26T16:03:53Z). Municípios com o arquivo de presidente completo nos dois turnos,
sem o exterior; o código TSE casa os dois turnos.

**Rótulo.** Votos absolutos, não fatia dos válidos; menos votos não identifica eleitor nem motivo. As colunas `perda_*` repartem a perda por duas réguas declaradas,
o teto e a proporcional; são contas sob hipótese, não identificação de eleitor.

| coluna | definição | unidade |
|---|---|---|
| `uf` | Unidade da federação | sigla |
| `mun_tse` | Código TSE do município, cinco dígitos | código |
| `municipio` | Nome do município como no arquivo do TSE | texto |
| `governador_2t` | 1 quando a UF teve 2º turno de governador (UFs de governadores.json), 0 quando não | 0 ou 1 |
| `aptos_1t` | Eleitorado do município no 1º turno | pessoas |
| `aptos_2t` | Eleitorado do município no 2º turno | pessoas |
| `comparecimento_1t` | Eleitores que compareceram no 1º turno | pessoas |
| `comparecimento_2t` | Eleitores que compareceram no 2º turno | pessoas |
| `dif_comparecimento` | comparecimento_2t menos comparecimento_1t | pessoas |
| `pct_comparecimento_1t` | comparecimento_1t sobre aptos_1t, duas casas | % |
| `pct_comparecimento_2t` | comparecimento_2t sobre aptos_2t, duas casas | % |
| `validos_1t` | Votos válidos para presidente no 1º turno, todas as candidaturas | votos |
| `validos_2t` | Votos válidos para presidente no 2º turno | votos |
| `terceiros_1t` | Votos válidos do 1º turno em candidaturas que não Flávio e Lula | votos |
| `flavio_1t` | Votos em Flávio Bolsonaro no 1º turno | votos |
| `flavio_2t` | Votos em Flávio Bolsonaro no 2º turno | votos |
| `dif_flavio` | flavio_2t menos flavio_1t | votos |
| `lula_1t` | Votos em Lula no 1º turno | votos |
| `lula_2t` | Votos em Lula no 2º turno | votos |
| `dif_lula` | lula_2t menos lula_1t | votos |
| `parte_flavio_1t` | Flávio sobre Flávio mais Lula no 1º turno, duas casas | % |
| `parte_flavio_2t` | Flávio sobre Flávio mais Lula no 2º turno (os válidos), duas casas | % |
| `mudanca_parte_flavio_pp` | parte_flavio_2t menos parte_flavio_1t | pontos percentuais |
| `perda` | Votos que o candidato da lista perdeu, positivo: flavio_1t menos flavio_2t na lista de Flávio, lula_1t menos lula_2t na de Lula | votos |
| `perda_teto_comparecimento` | Régua do teto: menor valor entre a perda e a queda do comparecimento (zero quando o comparecimento não caiu), como se todo eleitor que deixou de votar fosse do candidato | votos |
| `perda_fora_teto` | perda menos perda_teto_comparecimento: o mínimo que a queda do comparecimento não cobre | votos |
| `perda_proporcional_comparecimento` | Régua proporcional: menor valor entre a perda e a queda do comparecimento vezes os votos do candidato no 1º turno sobre comparecimento_1t, como se quem deixou de votar votasse como o município no 1º turno; uma casa | votos |
| `perda_fora_proporcional` | perda menos perda_proporcional_comparecimento; uma casa | votos |
