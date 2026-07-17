# Censo 2022 — setores censitários

Fontes oficiais usadas para validar os anexos territoriais de pesquisas
eleitorais.

- `IBGE_Setores_censitarios.pdf`: publicação de 2024 sobre a **Malha de Setores
  Censitários preliminares**, 43 páginas, SHA-256
  `d881d72a234e8ae2694900fcd8676404e959e09370bdaac03463454c7877fc03`.
- `quaest_sector_reference_2026-07-16.json`: recorte leve dos 667 geocódigos
  distintos usados pela Quaest em junho e julho, com população do Censo 2022 e
  estado da validação no serviço oficial do Panorama.

O PDF preliminar explica geocódigo, finalidade e heterogeneidade dos setores,
mas não é mais a versão territorial vigente. O IBGE informa que a malha
definitiva substitui a preliminar e disponibiliza agregados definitivos com mais
de 3.000 variáveis, atualizados em 20 de maio de 2026. Novos processos devem
usar a malha e os agregados definitivos; o material preliminar fica preservado
apenas para rastrear a fonte citada nos anexos da Quaest.

Atualização do recorte:

```bash
python3 -m pip install -e '.[audit]'
python3 scripts/quaest-territory-audit.py --refresh-ibge
```

Serviços consultados pelo script:

- Panorama: <https://censo2022.ibge.gov.br/panorama/mapas.html?localidade=&recorte=setores_censitarios>
- API de agregados por setor: `servicodados.ibge.gov.br/api/v2/censos/demografico/2022/agregados/setores-censitarios/`
- API da malha por município: `servicodados.ibge.gov.br/api/v2/censos/demografico/2022/malhas/setores-censitarios/`
