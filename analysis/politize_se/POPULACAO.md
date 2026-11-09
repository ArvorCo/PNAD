# População residente × eleitorado × comparecimento municipal

Reprodução: `.venv/bin/python scripts/politize-se-populacao-build.py --coletar`.
Sem `--coletar`, usa exclusivamente as fontes arquivadas. Não altera boletins,
perfil eleitoral ou dados históricos. Fonte da interface: `populacao.js` nas pastas
`docs/assets/politize_se/` e `docs/assets/politize_se_mapa/`; HTML escrito à mão.

## Universos e método

- Censo 2022, tabela SIDRA 9514, variável 93, município, homens/mulheres,
  declaração de idade total. Somar classes não sobrepostas: 16 e 17; 18 e 19 mais
  20–24; demais grupos até 100+. As dez faixas reproduzem o perfil TSE.
  A soma 16+ mais 0–15 precisa reproduzir a população municipal total.
- Estimativa IBGE, tabela 6579, variável 9324, último ano retornado pela API no
  momento da coleta: 2026. O dado oficial é população total, todas as idades.
- **16+ municipal estimada pela Arvor** = total IBGE 2026 × proporção 16+ Censo
  2022. Hipótese de estrutura constante, sem envelhecimento, migração seletiva
  ou mudança de composição modelados. Não é projeção oficial IBGE por idade.
- PNADC, base local `base_labeled.csv`, primeiro trimestre de 2026, peso V1028.
  Referência estadual independente para moradores 16+, mulheres 16+, 16–24 e
  60+. Não se distribuem estimativas amostrais estaduais pelos municípios.
  Não há erro-padrão calculado; os números não são intervalos de confiança.
- Cadastro TSE: soma de todas as seções do perfil eleitoral 2026, por código
  municipal TSE. Idade e sexo não informados permanecem nos denominadores.
  Cadastro não é população residente nem perfil de quem efetivamente votou.
- Comparecimento: contagens `comp1`/`comp2` dos totais municipais publicados do
  Politize-se, não reconstrução de taxas arredondadas. Aptos de cada turno são
  mantidos separadamente do total do perfil. Cobertura de boletins é explícita.
- Ligação municipal pelo código IBGE do contexto territorial existente, nunca
  apenas por nome. 5.571 municípios, 5.570 com comparação. Boa Esperança do Norte
  não tem base de Censo municipal comparável e fica nula, não imputada.
  Mudanças de limites entre 2022 e 2026 podem afetar municípios de origem também.

## Interface

Seis camadas: inscritos/16+, comparecimento 1T/16+, comparecimento 2T/16+,
sexo feminino TSE−Censo, jovens 16–24 TSE−Censo, idosos 60+ TSE−Censo.
Nas três primeiras, razão de 100 significa igual tamanho. Área do círculo é
proporcional à razão (raio = 10 √(razão/100), limitado a 2–48 px). Razão menor que
100 gera círculo menor; maior que 100, maior. Azul abaixo e ferrugem acima.
Não se usa o módulo do saldo: isso faria déficit e excesso parecerem iguais.
Diferenças demográficas usam pontos percentuais e raio fixo, com referência zero.

Cada município aparece uma vez; nenhum total se repete por escola. Filtros de
zona, prédio, chuva e horário não se aplicam à população e são explicitados na
legenda. UF, município, busca por nome de município e distância ao ponto municipal
continuam operantes. A lista ordenável e o CSV incluem valores e nulos.

O painel comum aparece no mapa e nas visões municipal, local, seção e zona do
Politize-se. Na zona, os municípios atendidos aparecem separadamente, pois não se
pode atribuir a população inteira à fração de um município coberta pela zona.
A tabela de votos por seção passa a ser o primeiro bloco de dados da ficha do
prédio, com contagens em destaque, percentuais entre os dois candidatos e demais
indicadores em uma tabela técnica expansível.

## Interpretação e rastreabilidade

Diferenças podem refletir datas, migração, cobertura, revisão cadastral ou vínculos
com outro local. Não identificam causa nem demonstram irregularidade. O TSE
explica que domicílio eleitoral admite vínculos além da residência:
https://www.tse.jus.br/servicos-eleitorais/titulo-eleitoral/titulo-eleitoral-faq

Respostas IBGE completas em `data/originals/populacao_eleitorado/`, com recibos
URL/data/SHA-256. Metadados públicos incluem hashes das fontes reutilizadas,
perfil eleitoral original, hash da base PNAD, data dos boletins e hash dos totais.
Nenhum dado pessoal é exportado. As contagens são agregadas municipais.

## Verificação

`pytest -q tests/test_politize_se*.py tests/test_sitemap.py`: 108 testes passando.
`analysis/politize_se/qa-populacao.py` verifica as seis camadas, 5.571 pontos únicos,
retorno aos locais, exportação CSV, fichas de seção/município e telas de 390/1440 px.
Executar com servidor HTTP de `docs/` na porta 18779. Opcionalmente definir
`PLAYWRIGHT_CHROMIUM_EXECUTABLE` para um Chromium já instalado.

Serra do Navio e Fernando de Noronha não têm coordenada no índice eleitoral
reutilizado: usam ponto interno da malha IBGE arquivada, com origem indicada na
ficha. Todos os 5.571 municípios têm ponto; isso não equivale à posição da sede.
