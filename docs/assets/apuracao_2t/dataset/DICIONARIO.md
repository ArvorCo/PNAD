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
