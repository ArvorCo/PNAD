# Genial/Quaest nacional — julho de 2026

Pacote oficial baixado em 15 de julho de 2026 e usado na auditoria
[`docs/quaest_0726.html`](../../../../docs/quaest_0726.html).

## Registro e arquivos

- Registro TSE: `BR-07181/2026`.
- Campo: 10 a 13 de julho de 2026.
- Divulgação: 15 de julho de 2026.
- Amostra: 2.004 entrevistas presenciais domiciliares.
- Contratante: Banco Genial S.A.
- Custo: R$ 433.255,92.
- `Quaest_072026.pdf`: relatório público, 121 páginas.
- `Quaest_Questionario_072026.pdf`: instrumento registrado, 38 páginas.
- `Quaest_NFe_072026.pdf`: NFS-e nº 464.
- `Quaest_Responsável_072026.pdf`: declaração da responsável estatística.
- `Quaest_TSE_072026.html`: espelho local do registro PesqEle.
- `Quaest_Bairros_072026.pdf`: anexo de 334 setores censitários, assinado em
  16 de julho de 2026 às 11:03:27 (UTC−3).
- `quaest_bairros_0726.csv`: extração reprodutível das 334 linhas, enriquecida
  com população do setor no serviço oficial do Panorama do Censo 2022.

Os hashes SHA-256 e tamanhos são regenerados por
`python3 -m pip install -e '.[audit]'` e, depois,
`python3 scripts/quaest-territory-audit.py` e
`python3 scripts/quaest-july-audit.py`. Os resultados são gravados em
`docs/assets/quaest_0726_territory.json` e
`docs/assets/quaest_0726_data.json`.

## Auditoria geográfica

O anexo totaliza 334 setores, 120 municípios e 2.004 entrevistas: exatamente
seis entrevistas por setor. Todos os 334 códigos de julho foram encontrados no
serviço oficial do IBGE usado pelo mapa Panorama. A comparação com o anexo de
junho recuperado no PesqEle encontrou 27 municípios, seis pares
município/bairro e somente um setor exato em comum. Repetir o nome de um bairro
não significa repetir o setor ou os domicílios.

O anexo não publica intenção de voto, probabilidades de inclusão ou pesos por
setor. Logo, ele permite auditar a geografia, mas não autoriza atribuir a mudança
do placar a bairros específicos nem inferir voto a partir do perfil censitário.

## Falha de controle documental

O PDF cujo metadado interno diz `QUEST+GENIAL+NACIONAL+JUL26+REGISTRO` traz na
primeira página `OP093/25` e `PESQUISA GENIAL NACIONAL - JUNHO/2026`. O conteúdo
é o instrumento de julho, com 101 itens, mas o cabeçalho foi reaproveitado da
rodada anterior. Isso é evidência de falha de versão/rastreabilidade; isoladamente,
não prova que o instrumento errado foi aplicado no campo.
