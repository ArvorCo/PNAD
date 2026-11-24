# Um mesmo número de título em seções diferentes

**Eleições presidenciais de 2026 · Brasil sem exterior · conferência de 23 de novembro de 2026**

A denúncia se confirma no sentido literal. No primeiro turno, três números de título aparecem como mesário registrado em duas UFs no mesmo dia. No segundo, quatro outros números apresentam o mesmo padrão. São **sete números distintos, 14 seções e 14 locais**. A conferência de causa permanece aberta. O material permite identificar onde o mesmo número foi registrado, mas a presença física de uma pessoa, a intenção de quem fez o registro e eventual impacto eleitoral exigem outras evidências.

[Abrir o mapa por local](mapa.html) · [Lista por identificador](lista_mesarios.csv) · [Pares entre municípios](pares_municipios.csv) · [Conferência nos ZIPs do TSE](conferencia_tse.csv)

## Explicações oficiais

Em 23 de novembro de 2026, a Justiça Eleitoral atribuiu a erro de digitação a repetição de título mostrada em um vídeo. Segundo a checagem, o mesário pode digitar por engano uma sequência que corresponda a um título válido. A urna guarda o número informado e funciona sem consultar as demais urnas. A nota não descreve substituição automática do número pelo sistema.

Segundo a mesma nota, se o mesário vota naquela seção e há biometria disponível, a urna compara a digital apresentada com a cadastrada. Se o mesário é eleitor de outra seção, a urna armazena a digital coletada para posterior verificação pela Justiça Eleitoral. [Checagem da Justiça Eleitoral de 23/11/2026](https://www.justicaeleitoral.jus.br/fato-ou-boato/checagens/2026/repeticao-de-titulo-em-logs-de-urnas-nao-comprova-existencia-de-mesarios-virtuais).

Para conferir quem trabalhou em cada mesa, o art. 127, incisos VI e VIII, prevê a assinatura do Boletim de Identificação do Mesário e o registro de presenças, substituições e remanejamentos na ata. A checagem pública não identifica as seções do vídeo nem apresenta a conferência individual dos sete pares entre UFs deste relatório. A causa de cada um desses pares continua em aberto. [Resolução TSE nº 23.751/2026, art. 127](https://www.tse.jus.br/legislacao/compilada/res/2026/resolucao-no-23-751-de-26-de-fevereiro-de-2026).

## O que se espera encontrar

A mesa tem presidente, primeiro e segundo mesários e secretário. O manual orienta digitar e confirmar o título de cada integrante presente. Admite registro durante a votação e exige presença em ata. Há também registro ao fim dos trabalhos, substituições e remanejamentos. Uma única seção pode, portanto, registrar várias pessoas, e um número pode aparecer várias vezes. A função e o tipo de evento importam. [Manual do Mesário 2026, p. 15](https://www.justicaeleitoral.jus.br/eleicoes/mesario/assets/arquivos/manual_do_mesario.pdf#page=15) · [Resolução TSE 23.751/2026, arts. 9, 125–127](https://www.tse.jus.br/legislacao/compilada/res/2026/resolucao-no-23-751-de-26-de-fevereiro-de-2026)

Quatro identificadores distintos apareceram em 435.331 logs no primeiro turno (87,4%) e em 438.617 no segundo (88,1%). Em 204 e 89 logs, respectivamente, a triagem não encontrou a mensagem de registro. A distribuição completa, de zero a dez identificadores por seção, está no [resumo](resumo.json).

## Contagens no mesmo turno

| Maior alcance de cada número repetido | Números 1º T | Locais 1º T | Números 2º T | Locais 2º T |
|---|---:|---:|---:|---:|
| Seções do mesmo local cadastrado | 6.727 | 4.413 | 4.441 | 2.407 |
| Locais distintos do mesmo município | 342 | 451 | 313 | 358 |
| Municípios distintos na mesma UF | 20 | 40 | 16 | 32 |
| UFs distintas | 3 | 6 | 4 | 8 |
| **Total distinto por turno** | **7.092** | **4.851** | **4.774** | **2.772** |

Cada número entra em uma só classe por turno. Um local pode receber números de várias classes. O total deduplicado corresponde a 10.713 seções no primeiro turno e 6.035 no segundo. Considerando as chaves cadastrais de local nos dois turnos, são 6.917 locais distintos. As ocorrências restritas ao mesmo local representam 94,9% e 93,0% dos números repetidos. Uma verificação de remanejamento interno começa pela ata da mesa.

## Quantas vezes cada número se repete

A lista contém **11.585 identificadores distintos**. Desses, 281 repetiram em ambos os turnos. Somando apenas as seções adicionais dentro de cada turno, houve 7.257 repetições no primeiro e 4.901 no segundo. Para 11.106 identificadores houve só uma repetição no total.

A maior contagem pertence ao código de auditoria **M-2D3BB916DE19** neste snapshot. Aparece em dez seções e dez locais de votação da zona 254 de São Paulo no primeiro turno e em uma dessas seções no segundo. A conta é nove repetições no primeiro e zero no segundo. A aba **Seções** permite conferir cada local, o número de eventos de registro e as habilitações atribuídas. [Planilha filtrável](mesarios_por_secao.xlsx) · [Lista em CSV](lista_mesarios.csv)

## Quanto voto foi depositado nessas seções?

No primeiro turno, 10.713 seções concentram 2.791.092 votos para presidente. No segundo, 6.035 seções concentram 1.602.448. As chaves UF, município TSE, zona e seção se repetem nos dois recortes em 811 casos. A união tem **15.937 chaves de seção**. Os **4.393.540 votos** somam duas eleições sucessivas e podem incluir a mesma eleitora ou eleitor em ambas.

| Turno | Seções | Lula | Flávio Bolsonaro | Outros nominais no BU | Brancos | Nulos no BU | Total |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1º | 10.713 | 1.181.192 | 1.252.409 | 223.461 | 52.859 | 81.171 | 2.791.092 |
| 2º | 6.035 | 820.082 | 730.243 | 0 | 17.886 | 34.237 | 1.602.448 |

A planilha detalha todos os candidatos e separa os 119 votos nominais que o BU atribui ao nº 28 no primeiro turno. O banco de candidaturas da eleição 6257 contém 12 nomes, sem o nº 28. Preservamos o número e a classificação do boletim para permitir a reprodução.

Na aba **Por identificador**, cada uma das 11.866 linhas representa um dos 11.585 números em um turno em que ele se repetiu. Cada linha soma uma vez o BU de cada seção do identificador. Para totalizar o conjunto, a aba **Por seção** deduplica as seções entre identificadores. A seção inteira inclui eleitores atendidos por toda a equipe. Os logs atribuem 9.010 eventos de habilitação aos números repetidos no primeiro turno e 5.460 no segundo. O voto é secreto. [Planilha filtrável por identificador e turno](mesarios_votos_e_equipes.xlsx) · [CSV por identificador](votos_por_identificador.csv) · [CSV por seção com URLs e hashes dos BUs](votos_por_secao.csv)

Todos os 16.748 BUs do recorte foram descompactados do arquivo original preservado no acervo e decodificados novamente com a especificação ASN.1. Em cada um, conferiram o SHA-256, a identidade da seção, a fase oficial, o pleito, as contagens por número e tipo de voto, a soma do cargo e o comparecimento presidencial. A verificação de hash compara os bytes com o acervo e não substitui o exame da assinatura digital.

## Os quatro números são exclusivos da seção?

Relemos nacionalmente os 497.895 logs de cada turno com o critério de fase e identidade da urna aplicado também aos números que só aparecem uma vez. A contagem estrita de seções com exatamente quatro números no dia é 434.663 e 438.133. Os valores maiores na primeira parte do relatório (435.331 e 438.617) pertencem à triagem anterior a esse filtro. As 10.713 e 6.035 seções com duplicidades foram integralmente reproduzidas nessa nova leitura.

| Entre as seções com exatamente quatro títulos registrados no dia | 1º turno | 2º turno |
|---|---:|---:|
| Nenhum dos quatro registrado em outra seção do país | 430.504 | 436.191 |
| Exatamente um dos quatro em outra seção | 4.008 | 1.848 |
| Exatamente dois | 99 | 43 |
| Exatamente três | 18 | 10 |
| Todos os quatro aparecem em pelo menos uma outra seção, que pode ser diferente para cada um | 34 | 41 |

A proporção com alguma repetição foi **0,96%** e **0,44%** entre as equipes de tamanho quatro. O teste de qualquer duplicidade inclui também seções que registraram mais ou menos de quatro pessoas. A matriz guarda todos os tamanhos, inclusive zero. [Matriz nacional de unicidade](unicidade_por_equipe.csv)

Comparando duas seções específicas, **230 pares** no primeiro turno e **264** no segundo compartilham quatro ou mais títulos, inclusive equipes maiores. Nenhum desses pares atravessa municípios. O teste mais restrito, em que as duas seções registram exatamente os mesmos quatro números durante o dia inteiro, encontra um único par no primeiro turno e zero no segundo.

O par é a Escola Municipal São Domingos, Buritis/MG, zona 324, seções 30 e 36. Na seção 30 os quatro aparecem na etapa anterior à votação. Na seção 36 os mesmos quatro aparecem na etapa posterior. A menor diferença entre registros correspondentes foi **10 h 47 min 10 s**. Nenhum dos quatro recebeu atribuição de habilitação nos dois lados. As duas seções tiveram 511 votos presidenciais no total.

Contando somente a etapa de abertura, as duas seções de um par registraram exatamente os mesmos quatro títulos em 12 pares no primeiro turno e 18 no segundo. Em 28 dos 30 pares o código de local coincide. Os outros dois ocorreram em Sobral/CE, zona 24, seções 420 e 501, e em Glaucilândia/MG, zona 184, seções 501 e 506. Ao longo do dia, nos dois casos, uma seção acumulou quatro títulos e a outra oito.

Há também **36 e 62 pares** nos quais dois quartetos distintos aparecem em ordem invertida. Os quatro da abertura de A aparecem no fechamento de B, e vice-versa. São 97 no mesmo local cadastrado e um em locais distintos de Pirenópolis/GO, zona 26, seções 6 e 8. Esse padrão faz da troca da seção usada para registrar presença uma hipótese concreta a confrontar com as atas. Os marcadores de antes e depois são mensagens explícitas do VOTA no mesmo fragmento, dia e urna. Horário isolado não determina a etapa. Nenhum dos 9.345 pares de seções compartilha o hash do ZIP ou uma série de urna associada ao mesmo número repetido. [Pares, horários relativos e etapas](pares_de_secoes.csv) · [Votos em cada recorte](totais_por_recorte.csv)

## O código de auditoria identifica o mesmo número original?

Sim, **neste acervo**. Na linha de registro o log contém o número digitado com os seus 12 algarismos. Reabrimos os pacotes de todas as seções que sustentam as repetições, recalculamos o HMAC com o segredo local e comparamos diretamente os 12 dígitos preservando os zeros iniciais. Os **11.585 IDs da lista correspondem um a um a 11.585 sequências diferentes**. Também não houve colisão dos primeiros 12 caracteres hexadecimais usados na exibição entre os **2.063.000 identificadores internos distintos** registrados nos dois turnos.

No teste aritmético de estrutura, 11.018 números passaram pela regra geral de módulo 11 implementada pelo validate-docbr. Os outros 567 passaram pela variante de SP/MG documentada pelo Brazilian Utils. A resolução do TSE especifica a composição e o módulo 11. Os testes aritméticos não consultam o cadastro de inscrições e não confirmam emissão, situação cadastral ou quem digitou o número. [Conferência dos IDs](conferencia_ids.json) · [Resolução TSE 23.659/2021, art. 36](https://www.tse.jus.br/legislacao/compilada/res/2021/resolucao-no-23-659-de-26-de-outubro-de-2021) · [Regra geral no validate-docbr](https://raw.githubusercontent.com/alvarofpp/validate-docbr/master/validate_docbr/TituloEleitoral.py) · [Variante documentada pelo Brazilian Utils](https://brazilian-utils.com.br/pt-br/utils/voter-id/)

Para apurar autoria e possível repercussão, o confronto prioritário é entre as atas, o Boletim de Identificação dos Mesários, a designação e os registros de remanejamento ou substituição no módulo de convocação do ELO. Priorizar números com habilitação nos dois lados e incompatibilidade geográfica ou temporal, além de quartetos coincidentes em locais diferentes na abertura. Os votos totais da seção não estimam quantos votos dependem de eventual irregularidade. [Resolução TSE 23.751/2026, arts. 125 a 127](https://www.tse.jus.br/legislacao/compilada/res/2026/resolucao-no-23-751-de-26-de-fevereiro-de-2026)

## Os sete pares interestaduais

| Turno | Município e UF | Município e UF | Distância | Menor intervalo entre registros¹ |
|---|---|---|---:|---:|
| 1º | Ribeira do Pombal/BA | Rio de Janeiro/RJ | 1.441,6 km | 2 min 42 s |
| 1º | Goianésia/GO | Ataléia/MG | 905,4 km | 7 min 43 s |
| 1º | Petrópolis/RJ | Mogi Mirim/SP | 389,9 km | 16 min 56 s |
| 2º | Barrocas/BA | Patrocínio Paulista/SP | 1.333,8 km | 27 min 53 s |
| 2º | Uibaí/BA | Anápolis/GO | 921,4 km | 54 min |
| 2º | Quatro Pontes/PR | São Paulo/SP | 748,6 km | 47 s |
| 2º | Cidade Ocidental/GO | Palmas/TO | 645,9 km | 48 min 28 s |

¹ Menor diferença entre duas mensagens de registro para o número, uma de cada lado, após conversão dos relógios locais para UTC. Não mede permanência nem deslocamento. A distância é em linha reta entre as coordenadas do cadastro. Para a zona, a seção e o ZIP de cada ponta, consulte as [fontes por seção](fontes_municipios.csv).

Em todos os 43 pares entre municípios os ZIPs e as séries de urna dos eventos diferem entre os lados. Baixamos os 86 ZIPs novamente dos endereços oficiais. Todos os SHA-256 coincidiram com o acervo. Uma leitura independente dos ZIPs confirmou os 12 dígitos completos em ambos os arquivos de cada par. Nos sete pares interestaduais, quatro tiveram habilitação atribuída ao número em apenas um lado e três em nenhum lado.

## Onde o número também habilitou eleitores nos dois lados

| Turno | Municípios | Distância | Habilitações atribuídas, na ordem dos municípios | Menor intervalo entre habilitações |
|---|---|---:|---:|---:|
| 1º | Birigui/SP e Mauá/SP | 475,7 km | 8 e 4 | 2 h 34 min 51 s |
| 1º | Palmas/TO e Porto Nacional/TO | 61,8 km | 3 e 6 | 3 h 23 min 10 s |
| 1º | Itanhaém/SP e Peruíbe/SP | 27,7 km | 12 e 4 | 2 min 40 s |
| 2º | Campo Largo/PR e Lapa/PR | 38,1 km | 1 e 1 | 38 min 24 s |

Birigui e Mauá merecem confronto documental. As duas urnas mencionam biometria localizada nos arquivos coletados ao tratar do mesmo número. Essa mensagem descreve a fonte usada pela urna. Os logs públicos não trazem uma comparação das duas impressões digitais. Em Itanhaém e Peruíbe, o intervalo de 160 segundos entre habilitações atribuídas ao número também torna especialmente importante verificar quem estava em cada mesa. [Mensagens de origem e contagens por par](conferencia_tse.csv)

Comparei ainda as mesmas seções no outro turno. Em 37 dos 43 pares, o número aparece novamente em uma das duas seções. Nos seis restantes ele não reaparece em nenhuma das duas. Nos sete interestaduais a divisão é seis e um. Esse padrão ajuda o cartório a localizar o registro destoante. Conferi também se outro número registrado em qualquer dos turnos nas mesmas seções diferia por apenas um dígito ou pela troca de posição de dois dígitos. Isso aconteceu em três dos 43 pares e em nenhum dos sete interestaduais. O teste não descarta outras formas de erro de entrada ou associação. [Contraste por par](contraste_turnos.csv)

## Método, alcance e conferência

- Foram lidos 497.895 pacotes de seções principais em cada turno, de 497.897 chaves domésticas no catálogo de cada pleito. O exterior ficou fora do recorte. A unidade é a seção dentro do turno. Seções agregadas e cópias de linhas não contam como ocorrências independentes.
- O critério principal exige a mensagem positiva do aplicativo VOTA, `Mesário [12 dígitos] registrado`. Zeros à esquerda fazem parte da chave. Habilitação exige `Mesário [12 dígitos] habilitou o eleitor`. Pedidos de biometria, tentativas rejeitadas e digitação para encerramento ficam fora do critério. O cruzamento não usa votos ou dados de candidatos.
- Primeiro foi feita uma triagem por turno, com o dia eleitoral e o dia seguinte previsto pelo leitor para encerramentos tardios. No pacote do segundo turno o histórico do primeiro fica fora da janela. Para as coincidências houve releitura com descarte de fragmentos identificados como preparação, conferência de fase oficial e compatibilidade de município, zona e seção ou série com o BU. Os casos intermunicipais passaram também pela comparação direta dos números nos downloads oficiais.
- Os identificadores de consulta usam HMAC com segredo local. A lista conserva o vínculo entre turnos no mesmo acervo. A planilha inclui as aparições isoladas do outro turno dos identificadores selecionados. A repetição é calculada separadamente em cada turno, descontando a primeira seção.
- Local é a chave UF, município TSE, zona e número do local nos cadastros de 2 e 18 de outubro. Dois códigos podem representar instalações próximas ou até o mesmo endereço físico. Vinte e uma linhas de local/classe no primeiro turno e oito no segundo ficaram sem coordenadas válidas. Todas continuam nas tabelas. Todos os pares entre municípios tinham coordenadas nos dois lados. [Locais e seções](locais.csv) · [Versões e hashes](resumo.json)
- Para estabelecer a causa, confrontar as atas e os Boletins de Identificação dos Mesários de cada par com as designações, substituições e remanejamentos do juízo eleitoral. Eventual divergência entre documentos e log exige examinar o procedimento de registro com os cartórios e o TRE. A análise não atribui autoria, adulteração de dados ou voto a qualquer pessoa. [Resolução TSE 23.751/2026, art. 127](https://www.tse.jus.br/legislacao/compilada/res/2026/resolucao-no-23-751-de-26-de-fevereiro-de-2026)

## Reprodução

Na raiz do projeto, executar na sequência os scripts abaixo com o Python do ambiente do projeto. O extrator usa os dois bancos originais em modo de leitura. Os intermediários pseudonimizados ficam em `data/outputs/mesarios_2026/`. O segredo local precisa ser preservado para reproduzir os mesmos rótulos individuais.

```sh
.venv/bin/python scripts/mesarios-2026-extrair.py
.venv/bin/python scripts/mesarios-2026-analisar.py
.venv/bin/python scripts/mesarios-2026-fontes.py
.venv/bin/python scripts/mesarios-2026-contexto.py
.venv/bin/python scripts/mesarios-2026-lista.py
.venv/bin/python scripts/mesarios-2026-votos.py
.venv/bin/python scripts/mesarios-2026-equipes-extrair.py
.venv/bin/python scripts/mesarios-2026-equipes.py
.venv/bin/python scripts/mesarios-2026-conferir-ids.py
.venv/bin/python scripts/mesarios-2026-mapa.py
```
