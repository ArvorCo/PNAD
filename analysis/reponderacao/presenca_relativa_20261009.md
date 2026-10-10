# Presença relativa: referência residual do primeiro turno — 09/10/2026

A referência extra do simulador muda de +5% para +3,8%. O cálculo fechado da
predição pré-urna dá +3,82955%; usamos uma casa decimal para não sugerir precisão
que o transporte ao segundo turno não tem. As duas centrais usam a mesma hipótese.
Zero e +5% continuam disponíveis; nenhum link publicado é reescrito.

## O que é observado e o que é calculado

O recorte é Brasil sem exterior nos dois lados. A predição final, gerada em
04/10 às 01:22:40, previa Flávio 45,26717% e Lula 45,12065% nos válidos.
A apuração completa nas 27 UFs deu 47,03761% e 45,15608%.

```
ajuste equivalente = 100 × [(F/L na urna) / (F/L na predição) − 1]
                   = +3,8295536732%
```

A razão F/L cancela o denominador dos válidos e não exclui as demais
candidaturas da conta original. Multiplicar apenas Flávio por 1,0382955 e
conservar as outras massas recompõe essa razão, mas dá 46,19981% × 44,35179%,
sem reproduzir todo o vetor da urna. Igualar Flávio contra todos os outros
candidatos exigiria +7,38468%. Não são duas estimativas da mesma taxa.

**Presença real por candidato não é identificada.** A razão de votos é o
produto da razão de preferências na população pela razão das taxas de presença.
A urna não revela as preferências dos ausentes. Fixar a previsão de preferências
e chamar todo resíduo de presença seria uma hipótese adicional. O resíduo inclui
erro das pesquisas, decisões finais, indecisos, voto útil e mobilização.

A própria tabela sintética da Nexus previa qF/qL = 1,0003066 no primeiro turno:
apenas +0,03066% relativos, condicionais às margens e à independência assumida
na tabela. Isso não é uma observação individual de 2026. No segundo turno, a
base Nexus tem qF/qL = 1,0001995; o controle aplica o fator extra 1,038 e
recalibra o total. Não somamos pontos percentuais de presença.

## Sensibilidade à referência

| Referência do primeiro turno | Resíduo equivalente F/L |
|---|---:|
| Predição arquivada, central | +3,83% |
| Média PNAD com Nexus | +4,35% |
| Média PNAD sem Nexus | +4,38% |
| Recência sem tendência | +4,63% |
| Indecisos proporcionais | +3,85% |
| Somente casas com PNAD | +5,20% |
| Publicadas, mesmas casas | +9,28% |
| Sem seleção de eleitor provável | +2,84% |

As sete casas da média dão de −7,08% (Gerp) a +16,61% (Nexus).
É desacordo entre referências, sem intervalo de confiança. A escolha de +3,8%
usa a predição arquivada completa, não seleciona a casa mais próxima da urna.
É calibração descritiva depois da eleição, sem teste independente ou ganho
preditivo demonstrado. Ondas pós-urna podem já incorporar parte do erro anterior:
transportar o resíduo pode repetir esse ajuste. Sua incerteza não entra
automaticamente no Monte Carlo. Zero permanece alternativa explícita.

## Fontes e reprodução

- `docs/assets/predicao_2026_1T_presidente.json` coincide byte a byte com o
  commit `1688f007f86eac5e07bf4234b5f6d2b2f4eade6a`; SHA-256
  `b0e9261020a48b16e3103ec8e4f77bc93ee69b5245e1bea82dd9382997d6bacc`.
- A [publicação desse commit no GitHub Pages](https://github.com/ArvorCo/PNAD/actions/runs/37176991078)
  terminou em 04/10 às 04:26:55 UTC (01:26:55 em Brasília), antes da votação.
  Conferência pela API de Actions filtrada pelo SHA completo. O build exige o
  hash fixo e geração anterior ao encerramento da votação; não recalcula o passado.
- Urna: `analysis/apuracao_2026/dados/presidente.json`, 27 UFs completas;
  votos de Flávio 55.960.603 e Lula 53.722.151. A média usa o corte fechado
  de 04/10 de `docs/assets/reponderacao_validos.json`.
- Metodologia de identificação parcial: [Jiang, King, Schmaltz e Tanner](https://gking.harvard.edu/publication/ecological-regression-with-partial-identification/).
- `scripts/reponderacao-presenca.py` produz a conta e a trilha de fontes;
  hashes e valores completos em `docs/assets/reponderacao_presenca.json` e
  no snapshot `c593ba54c460637c`. Interface em `#presenca-primeiro-turno`.

```sh
python3 scripts/reponderacao-build.py
python3 scripts/social-cards.py --only reponderacao_pnad
pytest -q tests/test_reponderacao_presenca.py tests/test_reponderacao_simulador.py
```

Os testes cobrem a referência anterior à urna, universo, fórmula, não
identificação, desacordo de âncoras, preservação de +5%, contabilidade e conteúdo
sem JavaScript. O navegador confere ambas as centrais, presets 0/+5/+3,8,
links e PNG, versões antigas e larguras 360/390/768. Resultado atual dos válidos:
Média 55,04% × 44,96%; Projeção 53,62% × 46,38%.

Validação final: suíte completa com 2.039 testes aprovados e 5 pulados;
Ruff, Black, sintaxe JavaScript, sitemap e conferência visual aprovados.
