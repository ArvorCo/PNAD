# Chuva de 25/10/2026 (2º turno) por célula: contrato entre as partes

Motor: `scripts/clima-2t.py` + módulos `scripts/clima_2t/` (`estacoes.py`, `modelo.py`, `observado.py`), que
reaproveitam `scripts/clima_1t/` por import (grade de 0,25°, cliente da Open-Meteo com cota, faixas de chuva).
Os arquivos do 1º turno (`analysis/clima_1t_2026/`, `docs/assets/fiscais_mapa/clima/<UF>.json`, `previsao.json`)
não são tocados. Regras da casa: pt-BR, sem travessão, nunca "fraude", leitura agregada, correlação não é causa.

## Fontes testadas em 26/10/2026 (registro em `fontes/`, com SHA-256 em `fontes/manifesto.json`)
- **ERA5/ERA5T** (`archive-api.open-meteo.com`, `models=era5`): série termina em 20/10 23h UTC (atraso de cerca
  de 5 dias e 17 horas). Cobre a janela de votação de 25/10 (10h a 21h UTC) por volta de 31/10; a troca é
  `python3 scripts/clima-2t-modelo.py --fonte era5` seguido de `python3 scripts/clima-2t.py --consolidar --fonte era5`
  (o script recusa a coleta se a série ainda não alcançar 25/10 18h de Brasília).
- **ECMWF IFS** (`models=ecmwf_ifs`, o "best match" padrão do arquivo): cobre 25/10, mas é modelo operacional a
  9 km montado com as primeiras horas de cada rodada (devolve até horas futuras). Rótulo obrigatório:
  "modelo, provisório"; nunca "observado" nem "reanálise". Coleta das 6.539 células por
  `scripts/clima-2t-modelo.py --fonte ifs` (cota de 5 mil por hora: cerca de 1h15).
- **INMET** (`apitempo.inmet.gov.br`): catálogo `estacoes/T` responde (669 estações, 538 automáticas operantes;
  `fontes/inmet_catalogo_T.json`); a rota pública `estacao/<data>/<data>/<código>` devolve 204 sem corpo para
  qualquer data (também 2025), com cabeçalhos de navegador; a tabela do site busca por POST em `/estacao/front/`
  com token reCAPTCHA, que não usamos; o ZIP anual `portal.inmet.gov.br/uploads/dadoshistoricos/2026.zip` foi
  modificado em 05/10 e não chega a 25/10. Registro em `fontes/inmet_tentativas_25_10.json`. Sem dado INMET.
- **CEMADEN**: catálogo com coordenadas `resources.cemaden.gov.br/dados/311_24.json` (5.853 estações;
  `fontes/cemaden_catalogo_311_24.jsonp`). Duas vias de chuva:
  1. série horária do gráfico de cada estação, `mapservices.cemaden.gov.br/MapaInterativoWS/resources/horario/<id>/<h>`,
     só as últimas 96 horas (alcança 25/10 10h UTC até 29/10 de manhã); respondeu 503 durante 26/10 (o próprio
     gráfico do site ficou vazio). `scripts/clima-2t-cemaden.py` (nohup) insiste com espera crescente e para
     quando a janela de 96 horas não alcança mais a votação. Rótulos `Hh` em UTC tratados como início da hora.
  2. tabela de acumulados `resources.cemaden.gov.br/graficos/interativo/getJson2.php?uf=XX` (1 a 96 horas até a
     última leitura). `scripts/clima-2t-fotos-cemaden.py` (nohup) tira fotos agendadas; `acc48hr - acc24hr` às
     03h UTC de 27/10 e `acc72hr - acc48hr` às 03h UTC de 28/10 dão a chuva de 25/10 das 00h às 24h de Brasília.
     Só entram estações com última leitura até 2 horas antes da foto. "-" na tabela é janela sem acumulado (zero):
     em 26/10 o padrão é monotônico (nunca "-" numa janela maior quando a menor tem número) e o Ceará seco tem
     139 de 150 estações recentes com "-" em todas as janelas. É total diário, não as horas da votação.
  A consulta por período do CEMADEN tem captcha e não é usada; a API oficial (`sws.cemaden.gov.br/PED`) exige
  token de cadastro.

## Interpolação (`observado.py`)
Centro de cada uma das 6.539 células de 0,25° do 1º turno; estações a até 50 km (haversine), peso 1/d² com
d mínimo de 1 km. Por célula: `n_estacoes`, `distancia_min_km`, `fonte` (`cemaden`, `inmet`, `ambos`,
`ifs_provisorio`, `era5`) e a fonte de cada variável (`fonte_dia`, `fonte_votacao`). Sem estação a 50 km, a
variável vem do modelo. Rajada e temperatura vêm sempre do modelo (pluviômetro não mede vento). Janela da
votação: 07h às 18h de Brasília (horas 8 a 18 do modelo, convenção H-1 a H), a mesma da análise do 1º turno.
Cortes editoriais: chuva forte ≥ 20 mm (`chuva_forte` nas horas de votação, `chuva_forte_dia` no dia),
rajada ≥ 50 km/h.

## Saídas
- `analysis/clima_2t_2026/clima.json` (todas as variáveis por célula, cobertura, estações usadas) e
  `estacoes.json` (cada estação com medida de 25/10).
- `docs/assets/fiscais_mapa/clima/observado_2t.json`: `{formato, gerado_em, dia, fonte, rotulos_fonte,
  celula_graus: 0.25, chave, raio_km, peso, cortes, cobertura, estacoes, nota, colunas, celulas}`; chave
  `floor(lat*4)/4,floor(lon*4)/4` com duas casas (ex.: `-23.75,-46.75`). Colunas: `chuva_votacao_mm,
  fonte_votacao, chuva_dia_mm, fonte_dia, rajada_votacao_kmh, rajada_dia_kmh, n_estacoes, distancia_min_km,
  fonte, faixa_chuva, chuva_forte, faixa_chuva_dia, chuva_forte_dia, rajada_forte`. A chave é de 0,25° (não a de
  0,5° da previsão) porque a grade observada é a do 1º turno.
- Consumidores: mapa de fiscais (ficha "No dia do 2º turno", filtro e coluna de chuva forte em 25/10),
  Politize-se (`clima2o` por prédio), mapa do Politize-se (`chuva2_*` e camada `chuva2`) e o capítulo dos logs
  do dossiê do 2º turno (`logs_clima_obs.py`, chave `clima_observado` em `logs.json`).

## Atualização
Depois de cada foto do CEMADEN, da série horária ou da troca para ERA5:
```
python3 scripts/clima-2t.py --consolidar [--fonte era5]
python3 scripts/politize-se-build.py && python3 scripts/politize-se-mapa-build.py
python3 scripts/apuracao-2t-2026-logs.py && python3 scripts/apuracao-2t-2026-build.py
pytest -q tests/test_clima_2t_observado.py tests/test_politize_se.py tests/test_politize_se_mapa.py
```

## Limites (escritos nas fichas e no capítulo)
Pluviômetro a até 50 km é estimativa para a célula, não medição no prédio. O acumulado diário inclui madrugada e
noite. O modelo é provisório. Associação entre lugares, não efeito da chuva sobre urna ou eleitor.
