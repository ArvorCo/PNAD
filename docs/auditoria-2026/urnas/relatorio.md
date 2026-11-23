# Auditoria de identificadores das urnas de 2026

**Em quatro seções, a mesma série física e o mesmo código de carga aparecem registrando votos em dois logs do mesmo turno.** São dois pares, um na Bahia e outro no Espírito Santo, em três locais. Todas as linhas de cômputo da série repetida em cada par coincidem, inclusive horário e código de verificação. Os quatro resultados presidenciais conferem, candidato por candidato, entre boletim de urna (BU), registro digital do voto (RDV) e tabela de votação por seção da totalização. **A seção 175 de Teixeira de Freitas ficou com uma lacuna de 136 cômputos no log atribuível à própria seção.** [Mapa](mapa.html) · [Pares de seções](pares_serie_ativa.csv) · [Cronologia dos arquivos](cronologia_pares.csv) · [Totalização](totalizacao.csv)

## Onde ocorreu e quantos votos as seções registraram

| Turno | Município e zona | Seção | Série final no BU | Lula | Flávio | Outros candidatos | Brancos | Nulos | Total presidencial |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| 1º | Teixeira de Freitas, BA · 183 | 175 | 02429118 | 88 | 160 | 6 | 7 | 11 | **272** |
| 1º | Teixeira de Freitas, BA · 183 | 181 | 02293617 | 102 | 143 | 9 | 3 | 6 | **263** |
| 2º | Santa Maria de Jetibá, ES · 9 | 85 | 01841837 | 80 | 218 | 0 | 5 | 5 | **308** |
| 2º | Santa Maria de Jetibá, ES · 9 | 112 | 01758779 | 60 | 229 | 0 | 1 | 14 | **304** |

As duas seções baianas funcionaram na Escola Municipal Clélia das Graças Figueiredo Pinto, local 1392. No Espírito Santo, a seção 85 funcionou na EEEFM Graça Aranha, local 1031, e a 112 na Comunidade Martim Lutero, local 1406. Os pares somam **535 votos no primeiro turno e 612 no segundo**. A soma de 1.147 mede a votação das quatro seções nos dois turnos. As linhas técnicas repetidas não contêm a escolha de candidato. Nenhuma dessas quatro seções integrou a lista anterior de títulos de mesário repetidos. [Votos por candidato, locais e BUs](casos_conferidos.csv) · [Auditoria dos mesários](../mesarios/relatorio.html)

### Teixeira de Freitas · 4 de outubro

A série **02423907** declara seção **181**. Suas 100 linhas de cômputo entre 08h06 e 12h23 estão tanto no pacote da 181 quanto no da 175. Na 181, as 100 linhas mais 163 da série 02293617 somam os 263 votos do BU. Na 175, o pacote traz 236 linhas de cômputo. Excluídas as 100 da 181, restam 24 da série 02424441 e 112 da série 02429118, ambas declarando a 175. O BU, o RDV e a totalização registram 272 na 175. **272 − (24 + 112) = 136** é a diferença que a trilha da própria seção deixa em aberto.

O log da 175 registra contingência bem-sucedida às 14h24. O histórico do primeiro turno preservado nos pacotes do segundo turno contém as mesmas sequências. A operação de contingência está documentada. A causa de o pacote incluir o trecho da 181 e a origem da lacuna na 175 permanecem abertas. Para esclarecer o caso, as peças mais específicas são as atas das duas mesas, o registro de troca de urna ou mídia da 183ª zona e a mídia ou o log da 175 anterior à contingência. O primeiro cômputo disponível que declara a 175 é das 13h29. [Cronologia e hashes das sequências](cronologia_pares.csv) · [Logs oficiais](logs_rebaixados.csv)

### Santa Maria de Jetibá · 25 de outubro

A série **01750820** declara seção **112**. Suas 304 linhas entre 08h01 e 16h40 estão nos dois pacotes, inclusive em membro interno de mesmo nome. No pacote da 85, há também 308 linhas de outra série, **01841837**, que declara seção 85. A soma bruta no pacote da 85 dá 612. Atribuir os trechos às seções declaradas reproduz **308 na 85 e 304 na 112**. Ambos os BUs têm tipo de arquivo RED, o Recuperador de Dados da urna. A sequência operacional que levou o trecho aos dois pacotes depende dos registros de recuperação da 9ª zona. [Comparação das linhas](pares_serie_ativa.csv) · [Tipos de arquivo na especificação do TSE](https://www.tse.jus.br/eleicoes/eleicoes-2026-content/arquivos/formato-arquivos-de-bu-rdv-e-assinatura-digital)

## Resultado nacional

O recorte inclui os 26 estados e o Distrito Federal e exclui o exterior. A unidade é turno, UF, município TSE, zona e seção com arquivo próprio de resultado. Seções agregadas sem BU próprio não geram uma segunda contagem. No primeiro turno, dois pacotes de Minas Gerais contêm log do Sistema de Apuração e BU com comparecimento informado como zero. Em ambos falta o evento de cômputo do aplicativo VOTA. [Cobertura](cobertura.json) · [Todos os resultados, inclusive divergências literais e dados ausentes](testes.csv)

| Conferência | 1º turno | 2º turno |
|---|---:|---:|
| Pares BU × RDV com os dois arquivos conferidos pelo tamanho e SHA-512 no manifesto da seção | 497.897 | 497.897 |
| Divergências entre BU e RDV na série física, mídias de carga e votação, código/data da carga, gerador de mídia, versão, tipo de urna ou tipo de arquivo | 0 | 0 |
| Divergências entre BU e RDV na seção efetiva (inclusive local), pleito, fase oficial, conjunto de eleições e cargos ou lista ordenada de cargas | 0 | 0 |
| Séries físicas ou códigos de carga do BU final repetidos entre seções | 0 | 0 |
| BUs, RDVs ou arquivos inteiros de log com SHA-256 repetido entre seções | 0 | 0 |
| Logs com evento de cômputo no turno | 497.895 | 497.897 |
| Seções com mais de uma série emitindo cômputos no próprio pacote | 2.100 | 1.414 |
| Seções com cômputo no log em que a série final do BU não emitiu nenhum desses eventos | 13 | 13 |
| Pares entre seções com repetição de série ativa e código de carga | 1 | 1 |

A busca de repetição inclui **todas as máquinas que emitiram a mensagem de voto computado**, inclusive as anteriores à substituição ou recuperação. Cada série ou carga conta uma vez por seção. As quatro séries finais dos BUs dos dois pares são distintas. A comparação dos identificadores no log usa a última declaração da própria máquina até o instante do cômputo e preserva declarações conflitantes no mesmo segundo. O intervalo inclui o dia de votação e o seguinte para captar encerramentos após a meia-noite. [Identificadores repetidos e número de seções](repeticoes.csv) · [Ocorrências por seção e valores observados](ocorrencias.csv)

### Diferenças de significado entre campos

- **Carga de contingência.** Em 3.004 seções no primeiro turno e 5.672 no segundo, o bloco completo da urna difere literalmente entre BU e RDV. Em todas, o BU traz a identificação da carga de contingência e o RDV informa a seção efetiva no campo correspondente. A série, as mídias, o código e o histórico de carga coincidem. Em 581 e 1.172 seções, respectivamente, o município ou a zona de preparação da carga difere do destino efetivo. A identificação principal da seção de votação coincide em todos os pares BU × RDV.
- **Local de votação.** No BU, o campo de local dentro da identificação da carga vale 1 em todos os registros em que essa alternativa contém um local. O local efetivo está na identificação principal da seção. Nos logs com reserva há declarações de local zero. Nas divergências literais de local no log, apenas a seção 85 do ES traz outro código efetivo distinto de zero e do próprio local. Esse código corresponde à 112.
- **Envelope do BU.** Os dois BUs mineiros de Sistema de Apuração no primeiro turno usam a alternativa de contingência no envelope, com município e zona. O corpo identifica a seção. Fase, município, zona e identificador eleitoral são compatíveis. [Distribuições dos campos](contexto_carga.csv)
- **Mídias e certificados.** Um gerador de mídias e uma flash de carga podem servir a várias urnas. Identificadores de flash de votação e de memória de resultado têm quatro bytes. A auditoria anterior separou colisões de valores curtos, agrupamentos de MR dentro da zona e equipamentos de apuração compartilhados. No recorte anterior, que inclui o exterior, a série e o certificado de urna trocaram juntos entre turnos, sem caso de mesma série com certificado diferente ou do inverso. [Auditoria de certificados, mídias e respectivos denominadores](metadados.md)

### As 29 seções da conferência aprofundada

As quatro seções dos pares e as 26 em que a série final do BU não emitiu cômputos têm uma seção em comum, a 112 do ES. A união abrange **29 seções-turno e 28 locais**. Nas 26, a série final aparece em outras mensagens do log e todos os códigos de carga observados nas máquinas com cômputo constam do histórico do BU. Em onze, a série final também emite a confirmação de encerramento. Os 29 logs foram baixados novamente e conferidos contra o SHA-256 do material analisado e o SHA-512 do manifesto da seção. [URLs dos logs e hashes verificados](logs_rebaixados.csv)

Os 29 casos somam **3.551 votos presidenciais no primeiro turno e 3.287 no segundo**. Os votos de cada candidato, os brancos e os nulos batem em **29 de 29** entre os dois binários e o arquivo de votação por seção publicado após a totalização. As três fontes são produtos da Justiça Eleitoral. A concordância testa a consistência entre publicações. A ata e as mídias locais são necessárias para atribuir causa à lacuna da Bahia. [Seções, motivos e placares](casos_conferidos.csv) · [Conferência da totalização](totalizacao.csv)

## Fontes, cobertura criptográfica e reprodução

A auditoria lê os identificadores diretamente dos arquivos conforme os esquemas ASN.1 do TSE. O teste nacional preserva a alternativa de identificação, o local efetivo e a ordem do histórico de cargas, pulando as folhas com votos individuais. A releitura dos 29 casos decodifica as listas integrais e recompõe a votação presidencial por candidato. O teste nacional de eleições e cargos compara conjuntos de identificadores. [Formato oficial](https://www.tse.jus.br/eleicoes/eleicoes-2026-content/arquivos/formato-arquivos-de-bu-rdv-e-assinatura-digital) · [Arquivos transmitidos](https://dadosabertos.tse.jus.br/dataset/resultados-2026-arquivos-transmitidos-para-totalizacao) · [Resultados por seção](https://dadosabertos.tse.jus.br/dataset/resultados-2026)

A leitura dos ZIPs estaduais verificou CRC, tamanho e nome dos membros selecionados. Recalculamos o SHA-512 do BU e do RDV em **995.794 pares** e comparamos com o mesmo manifesto de cada seção. A auditoria anterior verificou a cadeia de certificados e a assinatura de hardware. No processamento nacional dos logs, havia bytes do ZIP original para conferência direta do SHA-512 em **497.897 seções no 1º turno e 11.673 no 2º**. Para os demais logs do 2º turno, a cópia local usa armazenamento compacto com reconstrução dos textos e verificação dos hashes dos membros. Os 29 logs de interesse tiveram também a conferência direta do ZIP publicado. No segundo turno, os ZIPs estaduais forneceram dois RDVs e dois logs de votação ausentes dos índices locais. [Proveniência, URLs e hashes](fontes.json)

A partir da raiz do repositório, com os bancos de origem locais, os comandos abaixo reproduzem os testes e os arquivos de evidência. Os intermediários ficam em data/outputs/auditoria_ids_2026/.

~~~sh
python scripts/auditoria-ids-2026-pacotes.py
python scripts/auditoria-ids-2026-binarios.py --turno 1
python scripts/auditoria-ids-2026-binarios.py --turno 2
python scripts/auditoria-ids-2026-complementos.py
python scripts/auditoria-ids-2026-binarios.py --turno 2
python scripts/auditoria-ids-2026-logs.py
python scripts/auditoria-ids-2026-resumo.py
python scripts/auditoria-ids-2026-casos.py
python scripts/auditoria-ids-2026-originais.py
python scripts/auditoria-ids-2026-cronologia.py
python scripts/auditoria-ids-2026-totalizacao.py
python scripts/auditoria-ids-2026-mapa.py
~~~
