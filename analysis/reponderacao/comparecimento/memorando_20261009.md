# Comparecimento presidencial entre turnos — 09/10/2026

A referência nacional de comparecimento do simulador foi atualizada: a âncora Nexus de 79,578302% cede lugar à apuração efetiva do primeiro turno de 2026. Nas 27 UFs, 124.934.069 dos 157.828.968 eleitores compareceram (79,157882%); 32.894.899 faltaram (20,842118%). A conta fecha exatamente. O exterior permanece fora do universo das pesquisas e do simulador.

## Série e resultado

Seis eleições presidenciais com segundo turno desde 2002. Não misturar municipais, cujo universo do segundo turno é um subconjunto dos municípios do primeiro. 1994 e 1998 não tiveram segundo turno; 1989 antecede a era integral de urna eletrônica e fica fora da referência atual.

| Eleição | Comparecimento 1T | Comparecimento 2T | Δ comparecimento |
|---|---:|---:|---:|
| 2002 | 82,26% | 79,53% | −2,72 pp |
| 2006 | 83,25% | 81,01% | −2,24 pp |
| 2010 | 81,88% | 78,50% | −3,38 pp |
| 2014 | 80,61% | 78,90% | −1,71 pp |
| 2018 | 79,67% | 78,70% | −0,97 pp |
| 2022 | 79,05% | 79,42% | +0,36 pp |

A ausência cresceu em cinco das seis eleições, mas caiu em 2022. O sinal não é uma regra. As médias das variações são −1,777198 pp (seis eleições) e −0,772963 pp (2014/2018/2022). Aplicar taxas absolutas antigas ignoraria o nível efetivamente observado em 2026; todas as opções aplicam mudanças entre turnos ao nível atual.

## Retrospectiva exploratória e central

Com três ou mais eleições anteriores, avaliar 2014, 2018 e 2022, sem usar o ano alvo para estimar sua própria previsão:

| Regra | MAE / pp | Viés previsão − observado / pp |
|---|---:|---:|
| Repetir 1T | 1,02 | +0,77 |
| Repetir última variação | 1,25 | −1,25 |
| Média das três variações anteriores | 1,64 | −1,64 |
| Média de todas as anteriores | 1,73 | −1,73 |

Manter o comparecimento do primeiro turno teve menor erro nas três origens recentes. Isso sustenta uma **referência conservadora sem desconto automático**, não uma conclusão estatística de ausência constante. São três casos, a comparação foi exploratória e não há teste independente da seleção.

Conferência de fragilidade: incluir também 2010, permitindo duas eleições anteriores, troca o vencedor para a última variação (MAE 1,22 contra 1,61 da estabilidade). Essa informação está no relatório, no payload e nos testes. Não treinamos ML, não ajustamos coeficientes explicativos com seis pontos e não apresentamos o envelope como IC. Campanhas, transporte, clima, feriados e disputa estadual podem alterar a presença; esta série isolada não identifica seus efeitos causais.

## Cenários de 2026

| Hipótese | Comparecimento | Comparecimento / mi | Abstenção / mi | Δ comparecimento / mi |
|---|---:|---:|---:|---:|
| Central / repetir 1T | 79,16% | 124,93 | 32,89 | 0,00 |
| Média recente / 2014–2022 | 78,38% | 123,71 | 34,11 | −1,22 |
| Média completa / 2002–2022 | 77,38% | 122,13 | 35,70 | −2,80 |
| Variação de 2022 | 79,52% | 125,51 | 32,32 | +0,58 |
| Variação de 2010 | 75,78% | 119,60 | 38,23 | −5,33 |

O envelope observado transportado a 2026 é 75,78%–79,52% de comparecimento. **Não é limite nem intervalo preditivo para 2026.** O simulador também permite taxas fora desse envelope.

Os botões alteram apenas `comparecimento`; preservam central escolhida, presença relativa e demais controles. A calibração comum da Nexus conserva as razões entre taxas até o teto de 100%. Portanto, ausência uniforme modifica os volumes, mas não o placar nos válidos enquanto nenhuma taxa satura. Nenhuma preferência dos ausentes é identificada ou imputada. Brancos/nulos são votos de quem compareceu, em uma conta separada.

Monte Carlo continua condicionado ao comparecimento escolhido. Não incorporamos a variabilidade das analogias como uma distribuição probabilística estimada com seis eleições, nem confundimos seus cenários com os sorteios de preferência/erro amostral.

## Fontes e universo

- `serie_presidencial.json`: transcrição e URLs por ano. 2002: Relatório das Eleições 2002 do TSE, p. 26, cópia primária hospedada pelo Poder360; totais exatos. O SHA-256 da íntegra está registrado, e a cópia de conferência está no temporário local ignorado.
- 2006/2010: Agência Câmara de 01/11/2010, com os dados e manifestação do presidente do TSE. Percentuais publicados arredondados; não inventamos totais/decimais. Texto capturado em `camara_2006_2010.txt`.
- 2014: TSE de 06/10 (1T, taxa publicada 80,61%) e proclamação definitiva de 09/12 (2T, 112.683.879 presentes / 142.822.046 aptos). 1T permanece com precisão publicada.
- 2018/2022: ZIPs TSE já arquivados localmente, processados em streaming; apenas o membro presidencial `*_BR.csv`, uma vez por seção/turno. `*_BRASIL.csv` duplica presidente e não entra. Resultado, membros, datas de geração e hashes em `tse_2018_2022.json`.
- Tentativas de atualização dos ZIPs de 2002–2014 e de PDFs diretamente no portal retornaram HTTP 429. A série antiga usa os documentos publicados acima, sem alegar extração desses ZIPs. Os totais modernos foram reextraídos dos ZIPs locais.
- História inclui exterior; alvo de 2026 não inclui. Conferência 2018/2022: excluir ZZ muda o delta em −0,00222 e −0,00218 pp. Essa pequena diferença nesses dois anos sustenta a aproximação de transporte, não prova identidade nos demais. O relatório declara o universo distinto.
- Aptos com comparecimento e ausência ambos zero ficam como resíduo, sem serem recodificados como abstenção. Em 2018 são 470 no exterior; em 2022 são 84 no Brasil e 657 incluindo exterior. O estado de instalação não está informado em todas as linhas de 2018. O denominador histórico usa os aptos da fonte, e não apenas aptos reconciliados.

## Reprodução e verificação

```sh
python3 scripts/reponderacao-comparecimento-fontes.py  # exige ZIPs locais de 2018 e 2022
python3 scripts/reponderacao-build.py                 # usa resumos compactos versionados
pytest -q tests/test_reponderacao_comparecimento.py tests/test_reponderacao_projecao.py tests/test_reponderacao_simulador.py
```

Gráfico, retrospectivas e cenários em `reponderacao_pnad.html#comparecimento-historico`; payload separado em `docs/assets/reponderacao_comparecimento.json`. Links anteriores preservam a âncora antiga (inclusive `69656598a3c430d6`) e seus motores. Nova versão: `0e0f4566cb2fd88a`.

Conferências: 45 testes focados e suíte completa com 2.032 aprovados e cinco ignorados. Ruff, Black, sintaxe JavaScript e sitemap aprovados. Navegador sem erros com as nove opções nas duas centrais, conservação das massas, controles preservados, compartilhamento, volta à central, snapshot antigo, larguras 360/390/768 e leitura sem JavaScript.
