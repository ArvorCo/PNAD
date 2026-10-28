# Desenvolvimento: recência e escala

Verificação em 28/10/2026, após o pedido de substituir o retrato de 2010.

- **PNUD, Radar IDHM 2026:** dados de 2012 a **2024**, publicados em 26/05/2026; Brasil, macrorregiões, UFs e regiões metropolitanas. A atualização não oferece uma série recente para todos os municípios. Fonte primária: https://www.undp.org/pt/brazil/publications/radar-idhm-evolucao-do-idhm-e-de-seus-componentes-periodo-de-2012-2024
- **Atlas municipal PNUD:** a página oficial ainda descreve os Censos de 1991, 2000 e 2010. Não usar como retrato contemporâneo dos municípios nem atribuir às cidades o IDHM 2024 da UF ou da região metropolitana. https://www.undp.org/pt/brazil/atlas-dos-municipios
- **IPS Brasil 2026, escolhido para a análise municipal atual:** 5.570 municípios, 57 indicadores sociais e ambientais; bases disponíveis até 20/02/2026. Não é IDHM e não inclui renda como dimensão do índice. O ano da edição não é o ano de todos os indicadores. Doze deles não tiveram atualização frente à edição de 2025. As edições originais 2024/2025/2026 não são diretamente comparáveis. O método diz expressamente que a base municipal não permite análise intramunicipal. Referência: PDF metodológico, páginas impressas 4, 5, 8, 9 e 13, arquivado com SHA-256.
- **IFDM 2025:** alternativa de desenvolvimento municipal com ano-base 2023, encontrada na própria Firjan. Não chamar de IDHM. https://www.firjan.com.br/ifdm/

## Dados e reprodução

Originais em `data/originals/analise_realidade_eleicao/`, com URLs e SHA-256 em `fontes.json`. A exportação CSV do IPS não inclui código IBGE. A junção usa UF + nome normalizado e 17 equivalências explícitas, registradas na saída; não há aproximação automática. Todos os 5.570 registros casaram, sem duplicações. Dos 5.571 municípios no TSE, Boa Esperança do Norte/MT permanece sem IPS, como informa a metodologia.

`python scripts/analise-realidade-desenvolvimento.py` valida o hash, a escala 0–100 e a unicidade e grava `desenvolvimento.json`. Preferir o CSV oficial: o XLSX oficial arquivado contém células numéricas convertidas em datas; a rotina não o usa.

O relatório deve apresentar progresso social (IPS), renda estimada pela PNAD e escolaridade separadamente. Um índice municipal elevado não identifica a renda, a classe social nem o voto individual de seus moradores. Nas capitais, não replicar IPS municipal por zona para sugerir variação intramunicipal.
