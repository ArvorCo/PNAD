# Arquitetura da totalização: o que se prova, o que se infere, o que é hipótese

Bloco novo do capítulo 3 do dossiê (`h3` "Onde um sistema como esse engasga" e "O desenho que não engasga"). Reprodução: `python3 scripts/apuracao-2026-arquitetura.py` (grava `dados/arquitetura.json`, cerca de 40 s, só leitura local) e `python3 scripts/apuracao-2026-build.py`. Fontes com URL, data e o que cada uma prova: `fontes_arquitetura.json`. Testes: `pytest -q tests/test_apuracao_2026_arquitetura.py`.

## Pedido e hipótese do autor (05/10/2026)

Leonardo Dias: a centralização importa os boletins num Oracle Exadata, e a importação engasga num fluxo maior por causa dos índices das tabelas. Pediu a explicação da arquitetura, o comportamento de bancos Oracle sob alto throughput e uma recomendação (fila com Kafka e consumidor, a tática da Uber com Cassandra; banco distribuído conforme o volume). **Rótulo em todo o texto: hipótese do autor.**

## O que os documentos provam (verificado)

- Nota técnica do TSE de 17/11/2020 (PDF, 356.605 bytes, SHA-256 `abdcbc4e…cfd13`, lida no navegador): em 2020 a totalização foi centralizada no TSE num banco Oracle sobre **Exadata X8 Full Rack (oito nós) e Half Rack (quatro nós)**, Contrato TSE nº 22/2020 por inexigibilidade; as tabelas recebiam "mais de um milhão de linhas por minuto" a partir das 17h; a lentidão de 2020 veio do **plano de execução do otimizador** gerado com tabelas vazias, e o sistema de totalização foi parado para gerar outro; só dois de cinco testes rodaram no equipamento.
- Aos Fatos (28/11/2020): equipamento numa sala-cofre do TSE, operado pela equipe do tribunal (modelo Cloud at Customer).
- Portal de contratações de TIC do TSE (consultado 05/10/2026): item "Expansão contrato Oracle Cloud At Customer" na aba 2022 e 2023; suporte a hardware e sistemas Oracle em 2025. **O ETP e o contrato da expansão não foram lidos (HTTP 429).**
- Res. TSE 23.673/2021 (trecho via buscador): RecArquivos recebe os pacotes do Transportador e os entrega ao Sistot, que gerencia as totalizações. ConJur 29/10/2022: o TSE descreve a chegada dos BUs como "uma fila de banco".
- 04/10/2026: o presidente do TSE situou o congestionamento no **sistema de divulgação** ("conversão dos dados pelo programa de divulgação"), disse que a totalização não foi afetada e que a TI isolou outros sistemas (TSE 23h56; CNN 21h58; Agência Brasil 22h14). Sem relatório técnico.

**Não há documento que diga que o Exadata, ou qualquer Oracle, rodou a totalização ou a divulgação de 2026.** A hipótese continua hipótese: plausível pelos documentos de 2020, não provada para 2026, e o TSE aponta para a divulgação, não para a carga da totalização.

## Achado novo dos dados da casa (verificado)

O carimbo de recebimento publicado no `aux` de cada seção (`dr_hr`, hora de Brasília: AC e DF começam no mesmo 17:08) **some em três janelas que coincidem com as paradas do arquivo nacional**: 18:00:55 a 18:08:47 (7,9 min), 18:49:46 a 18:54:03 (4,3 min) e **19:31:50 a 19:59:22 (27,5 min)**, a pausa geral. Volta em rajada às 19:59. Amostra: 190.223 seções de 20 UFs (38,1% do país; faltam BA, MG, PE, PR, RJ, RS e SP).

Leitura (inferência): ou a recepção parou de registrar, ou o carimbo é aplicado por um componente posterior que parou junto com a divulgação. Os arquivos públicos não separam. Em qualquer caso a parada não foi só de vitrine.

## Dimensionamento (verificado na amostra; extrapolação declarada)

| Grandeza | Valor |
|---|---|
| BU médio (mediana, p95) | 10,75 KB (10,3; 16,4) |
| BUs do país | 5,4 GB; com logs de urna, 58 GB |
| Linhas de voto por seção (candidato × cargo) | 115 (presidente 7, governador 6, senador 10, federal 40, estadual 50) |
| Linhas de voto na noite | 57,5 milhões |
| Pico sustentado do arquivo nacional | 5.163 seções/min (18:43 a 18:49), 86/s, ~9.900 linhas/s, ~55 MB/min de BU |
| Pico de 2022, país inteiro | 5.022 BUs/min às 19:30; receber → 1ª totalização: mediana 45 s, p90 93 s, p99 339 s |
| Publicação 2026 (piso, coletor) | pico 6.052 versões/min (19:29), até 262 MB/min; mediana 18h a 19h30: 2.752/min; 28 minutos sem versão entre 19:33 e 20:01 |
| Parada mais longa do nacional (50,5 min) | 100.614 seções represadas = 11,6 milhões de linhas, 1,1 GB de BU |

Inferência: volume pequeno para qualquer banco atual (o próprio SQLite da casa num notebook guarda 21,9 milhões de linhas de voto e 550 mil versões de arquivo); 2022 recebeu a mesma ordem de BUs por minuto sem parar. Se houve gargalo, é de desenho, não de capacidade. A publicação multiplica o trabalho: até 262 MB/min de arquivos contra ~55 MB/min de BU.

## Mecanismo (inferência técnica) e recomendação (juízo editorial)

- Engasgo de banco relacional com pouco volume: amplificação de escrita em índices B-tree, trava nas linhas de total (país, candidato), recomputar totais a cada lote (custo cresce com o total), publicação síncrona lendo o mesmo banco. Fila não cresce em linha reta: perto da saturação, a espera explode; o pico é 18h a 20h.
- Recomendação proporcional: log de eventos só de acréscimo (Kafka ou equivalente, partição por UF, hash encadeado), consumidores idempotentes por seção, totais incrementais, publicação assíncrona por fotografia assinada com o número do último evento. Banco distribuído (HBase, Cassandra, CockroachDB, YugabyteDB) não se justifica pelo volume: o pico do TSE é cerca de 1% do que um cluster Cassandra da Uber escrevia em 2016; só por disponibilidade entre centros de dados.
- Referências Uber: Kafka (Uber Engineering, 21/12/2020; Fu e Soman, SIGMOD 2021), Cassandra (resumo da palestra de 2016 na High Scalability; Uber Engineering, 20/07/2023). O texto original da Uber com "um milhão de escritas por segundo" não foi localizado; cita-se o resumo.
- O que o TSE poderia publicar: desenho da totalização e da divulgação de 2026, log de eventos da noite com carimbo de recebimento, inclusão e geração de arquivo, relatório do incidente. Frase de fecho: o dossiê prova a parada pelos arquivos públicos; a causa é hipótese até o TSE publicar o relatório.

## Limites

- Coleta seção a seção parcial e sem os maiores colégios do Centro-Sul; a série extrapolada (fator 2,62) dá ordem de grandeza, não o minuto do país.
- Versões publicadas são piso: o coletor não lê todo arquivo a cada minuto.
- Buscas por parada comparável em 2022 e 2024 não acharam registro; ausência no buscador não prova ausência.
- tse.jus.br limitou o acesso (403/429): a resolução foi lida por trecho de buscador, e o anexo da expansão do contrato não foi lido.
