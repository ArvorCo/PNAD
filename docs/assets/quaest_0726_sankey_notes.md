# Sankey Quaest jul/2026 — transferência 1º → 2º turno (Lula × Flávio)

**Fonte:** Genial/Quaest Nacional, Julho/2026 — `data/pesquisas/quaest/2026-07/Quaest_072026.pdf`.
Toplines: 1º turno pág. 25; 2º turno Cenário 1 (Lula×Flávio) pág. 37; "definitivo/pode mudar" pág. 35; recorte por posicionamento pág. 38. Comparação: deck de junho, págs. 22 e 34.

## O que é FATO (publicado)
- **1º turno (jul):** Lula 40, Flávio 28, Caiado 4, Renan 3, Zema 2, quatro menores 1 cada, Indecisos 11, Branco/Nulo/Não vai votar 8.
- **2º turno Cenário 1 (jul):** Lula 45, Flávio 37, Branco/Nulo 14, Indecisos 4.
- **Deltas líquidos 1º→2º:** Lula **+5**, Flávio **+9**, Branco/Nulo **+6**, Indecisos **−7**. Some fecha: o "pool" liberado (13 p.p. de candidatos fora da cédula + 7 p.p. de indecisos que decidem = 20) é absorvido exatamente como +5/+9/+6.
- **Volatilidade (pág. 35):** entre os que podem mudar o voto — Caiado 57%, Renan 65%, Zema 70% — contra apenas 23% de Lula e 37% de Flávio. O bloco de terceiros é fluido, coerente com dispersão no 2º turno.

## O que a Quaest NÃO publica (o achado)
A Quaest **não divulga a matriz de transição** voto-no-1º-turno × voto-no-2º-turno. O deck traz toplines e recortes por subgrupo (região, sexo, idade, escolaridade, renda, religião e **posicionamento ideológico autodeclarado**). O recorte por "posicionamento" (pág. 38) é o mais próximo de uma transição — mas é **proxy ideológico, não o voto declarado no 1º turno**. Portanto, o fluxo do Sankey é **INFERÊNCIA** (modelo de cruzamento-mínimo/retenção-máxima): os totais de nó e os deltas líquidos são medidos; a repartição de cada elo é hipótese compatível, não medição. É mais uma peça publicada sem o cruzamento que sustentaria a leitura.

## O que o fluxo revela
- **De onde vêm os +9 de Flávio:** dos ~13 p.p. de terceiros majoritariamente à direita/centro-direita (Caiado, Zema, Renan) que saem da cédula, mais uma fração menor de indecisos. Consolidação previsível do antipetismo — mas **incompleta**.
- **Vazamento na direita não-bolsonarista (pág. 38, FATO):** nesse segmento Flávio cai na série (84→90→88→82→**74**), com **15% indo para Lula** e ~11% em branco/nulo. Ou seja, Flávio **não** herda 100% do campo anti-Lula; ~1 em cada 4 recusa a transferência. Essa é a assimetria a destacar.
- **Lula retém quase toda a base:** lulistas 97% Lula, esquerda não-lulista 86%. Ganho líquido menor (+5) porque já partia mais alto e há menos "sobra" à esquerda para capturar.
- **Branco/Nulo cresce +6 (8→14):** parte do eleitorado de terceiros e de indecisos recusa os dois nomes — reservatório real de rejeição dupla, não ruído.

## A queda na direita não-bolsonarista (perícia da série 84→90→88→82→74)

**Datas das ondas (FATO, eixo da pág. 38):** Mar/26 → Abr/26 → Mai/26 → Jun/26 → Jul/26. Julho: coleta 10–13/jul, n=2.004 face a face, ME ±2 p.p., registro BR-07181/2026 (pág. 3).

**Base do subgrupo: NÃO PUBLICADA.** O deck não traz nem a distribuição marginal do autoposicionamento (a pergunta existe — `def_pol` no questionário) nem o n não ponderado de nenhum recorte. Base de subgrupo é exigência de transparência WAPOR/ABEP que a Quaest não cumpre em nenhuma das 121 páginas.

**Estimativa do n (INFERÊNCIA):** resolvendo os pesos dos segmentos por álgebra (topline = Σ peso×coluna, pág. 32 × pág. 25), o sistema é mal-condicionado à esquerda, mas o segmento "direita não-bolsonarista" fica em **~19–23%** (melhor ajuste jul: ~22%; jun: ~19%) → **n ≈ 380–460**. Margens do recorte (p≈0,5): deff 1 → ±4,6–5,0; deff 1,5 → ±5,6–6,1; deff 2 → ±6,5–7,1 p.p. Com 334 conglomerados × 6 entrevistas, deff 1,5–2 é o cenário realista.

**(a) Ruído ou anomalia?** Diferença entre ondas independentes (p≈0,78, n≈380): SE ≈ ±3,0/±3,7/±4,3 p.p. (deff 1/1,5/2).
- Queda **82→74 (8 p.p.)** = 1,9–2,7σ → **zona cinzenta**: grande demais para ignorar, pequena demais para afirmar; com deff 2 pode ser ruído. Dizemos isso com honestidade.
- Queda acumulada **90→74 (16 p.p. desde abril)** = 3,8–5,3σ → **dificilmente é só ruído amostral**, mesmo com deff 2.

**(b) Rotação territorial:** entre junho e julho **333 dos 334 setores mudaram** (Jaccard 0,15%, `quaest_0726_territory.json`). Cada onda é uma amostra territorial quase disjunta — a rotação infla a variância entre ondas além do SE nominal e coincide exatamente com a queda 82→74. Não é prova de causa; é confundidor documentado.

**(c) Composição do segmento:** o rótulo é autodeclarado a cada onda — não é painel. A crise Michelle×Flávio (à qual o deck dedica ~15 páginas) pode re-rotular bolsonaristas desiludidos como "direita não-bolsonarista", diluindo o voto Flávio no segmento **sem migração real de voto**. Nossa reconstrução algébrica sugere o segmento em ~19% (jun) → ~22–23% (jul) — compatível com engorda de composição, mas dentro da incerteza do método. Sinal convergente: o painel **Bolsonarista também caiu 97→91** em julho, e no segmento a desaprovação de Lula quase não mudou (89→86) — o voto que sai de Flávio vai sobretudo para "não vai votar" (9→15), não para Lula (6→8). Padrão mais compatível com **desmobilização real do campo da direita pós-crise familiar** do que com artefato puro.

**Veredito da série:** anomalia digna de registro, **não** prova de manipulação. A queda de julho isolada está na margem do recorte; a queda acumulada desde abril não se explica por ruído puro, mas tem dois confundidores documentados (rotação de 99,7% dos setores; recomposição do segmento autodeclarado) e um mecanismo plausível (crise Michelle×Flávio, com o dinheiro indo para abstenção). O que transforma isso em achado de auditoria é a **opacidade**: sem base de subgrupo publicada, nem a Quaest nem o leitor conseguem separar migração real de artefato — e isso é escolha editorial do instituto.

## Consistência junho × julho
Estrutura **estável**: jun 1º turno 39×29 → 2º turno 44×38; jul 40×28 → 45×37. O salto de Flávio no 2º turno (~+9) e a vantagem de Lula (~7–8 p.p.) repetem-se. **Nenhum** pico mês-a-mês suspeito; nada da patologia "Lula retém 100% e Flávio vaza tudo" — na verdade Flávio ganha mais na transferência (+9 vs +5), o que é aritmeticamente esperado por ter mais candidatos afins eliminados.

## Veredito calibrado
Os números são **internamente coerentes** e batem na conservação de massa; não há sinal de manipulação. O problema é de **transparência metodológica**: sem a matriz de transição publicada, a Quaest deixa o passo mais informativo — quem migra para quem — por conta do leitor. **Hipótese**, não acusação: a opacidade favorece narrativas de "consolidação" que os dados só sustentam parcialmente (a direita não-bolsonarista vaza para Lula e para o branco/nulo). Fato reportável: **mais um recorte sem o cruzamento que o justificaria.**
