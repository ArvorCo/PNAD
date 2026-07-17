# Quaest julho/2026 — rejeição do Flávio + reponderação por renda

Perícia dupla sobre a Genial/Quaest de julho/2026 (registro BR-07181/2026, campo
10–13 jul, 2.004 entrevistas presenciais domiciliares). Contas reproduzíveis em
`quaest_0726_rejeicao_reponderacao.json`; visual em
`quaest_0726_rejeicao_reponderacao_fragment.html` (slide 1600×900 embutido, capturar
o elemento `.qrr` da slide com o padding da seção zerado).

---

## Perícia 1 — Rejeição de Flávio: o instrumento fabrica o teto

**Fato.** A Quaest não pergunta "não votaria de jeito nenhum". Pergunta, nome a nome,
um ternário sem meio-termo: *conhece e votaria / não conhece / conhece e não votaria*
(p46 do deck). Rejeição = "conhece e não votaria". Sem opção neutra, toda recusa mole
de quem conhece o nome entra como rejeição. Série Quaest para Flávio:
Abr 52 → Mai 54 → Jun 56 → **Jul 57**. Lula: 55 → 53 → 53 → **50**.

**Fato.** Benchmark de rejeição (Flávio / Lula):

| Instituto | Campo | Instrumento | Flávio | Lula |
|---|---|---|---|---|
| Genial/Quaest | 10–13 jul 2026 | conhece e não votaria (ternário) | **57** | **50** |
| Genial/Quaest | 5–8 jun 2026 | idem | 56 | 53 |
| BTG/Nexus (6ª) | jul 2026 | não votaria | 50 | 46 |
| Futura/Apex | 2026 | não votaria de jeito nenhum | 49,5 | — |
| Datafolha | 17–19 jun 2026 | não votaria de jeito nenhum | 48 | 46 |
| Datafolha | 3–5 mar 2026 | idem | 45 | — |
| AtlasIntel | jun 2026 | mede "medo", não rejeição clássica | n/d | n/d |

**Inferência.** A Quaest está acima de todas as casas para os dois nomes, mas o
excesso é **assimétrico**: sobre o Datafolha de junho, **+9 pp em Flávio** e só **+4 pp
em Lula**. O ternário converte o não-voto persuadável em rejeição, e esse não-voto mole
é maior em Flávio.

**Hipótese.** Como o não-voto de Flávio é mais reversível (o próprio Datafolha registra
que ele converte indecisos e transfere ~2:1), a Quaest superestima o teto de rejeição
*efetivo* dele mais do que o de Lula. O "57%" comprime o espaço real de crescimento.

**Coerência interna (57 de rejeição × 37 no 2º turno).** Compatível: voto 2T + rejeição
≤ 100 (Flávio 37+57=94; Lula 45+50=95). Os dois operam colados ao teto que o instrumento
desenha. Mas o teto de Flávio pela Quaest é 43 (100−57); pela rejeição dura do Datafolha
(48) seria 52. O instrumento tira ~9 pp do teto dele. O movimento jun→jul que abre a
tesoura não é Flávio subir (56→57, dentro da margem) — é **Lula cair** (53→50).

---

## Perícia 2 — Reponderação por renda: não explica o placar

**Método.** Reponderação marginal de tabela publicada. A Quaest só publica renda em
aprovação (p15) e 1º turno (p29); o 2º turno por renda **não existe no deck** (cenário 2T
é PROXY multiplicativo, nível hipótese). Amostra Quaest 31/42/27 → alvo PNAD 35,44/39,23/25,33
(PNADC anual v1 2024, 16+ com renda válida, abr/2026). `share_repond = Σ share_faixa × peso_alvo`.
O "publicado reconstruído" reproduz o topline (aprovação 48/47; 1T Lula ~41 vs 40).

**Deltas (reponderado − publicado):**

| Cenário | Publicado | Reponderado | Δ | Erro |
|---|---|---|---|---|
| Margem 1T Lula−Flávio | +13,5 | +14,3 | **+0,80** | ±0,9 |
| Margem 2T Lula×Flávio (proxy) | +9,8 | +10,7 | **+0,96** | ±0,9 |
| Saldo aprovação Lula | +0,9 | +2,2 | **+1,28** | ±0,9 |

Sensibilidade (±1 pp na meta da faixa baixa): margem 1T entre +0,62 e +0,99; saldo de
aprovação entre +0,99 e +1,59. Robusto e sempre pró-Lula.

**Caveats.** Uma dimensão só, sem microdados, sem interação com região/idade. Deck em
números inteiros → arredondamento ±0,5 pp propaga na soma. Resíduo de reconstrução ~0,9 pp
(1T reconstruído 40,87 vs topline 40) define o piso de ruído. 2T por renda não publicado.

**Veredito.** A renda **não explica o placar**. Reponderar a amostra ao país move a disputa
Lula×Flávio menos de 1 ponto em todo cenário de voto — dentro do erro. A direção é pró-Lula:
sub-representar o pobre (−4,44 pp na base) *subestima* Lula; corrigir amplia a vantagem dele,
de leve. O único indicador que chega perto de 1 ponto cheio é o saldo de aprovação (+1,28),
porque a aprovação tem o gradiente de renda mais íngreme (58 na base → 41 no topo).

---

## Script de reponderação (rodado via Bash)

```python
BANDS=["Até 2 SM","2-5 SM","5+ SM"]
QUAEST=[31.0,42.0,27.0]; PNAD=[35.44,39.231,25.329]
def norm(w): s=sum(w); return [x/s for x in w]
def rw(sh,w): w=norm(w); return sum(s*wi for s,wi in zip(sh,w))
# 1T: Lula[49,38,36] Flávio[23,29,30]; margem publicada vs PNAD
mp=rw([49,38,36],QUAEST)-rw([23,29,30],QUAEST)   # 13.46
mr=rw([49,38,36],PNAD)-rw([23,29,30],PNAD)        # 14.26  -> Δ +0.80
# Aprovação: Aprova[58,45,41] Desaprova[37,50,54]
sp=rw([58,45,41],QUAEST)-rw([37,50,54],QUAEST)    # 0.90
sr=rw([58,45,41],PNAD)-rw([37,50,54],PNAD)         # 2.18  -> Δ +1.28
```

Script completo (com 2T-proxy, sensibilidade e componente de baixa renda) reproduz o JSON.

---

## Thread (rascunho, primeira pessoa, ~1000 chars cada)

**Post 1 — rejeição**

Refiz a rejeição de Flávio na Quaest de julho: 57%, a mais alta do mercado. Fui
comparar casa a casa. Datafolha de junho: 48. Nexus: 50. Futura: 49,5. A Quaest crava
7 a 9 pontos acima de todo mundo. Por quê? Instrumento. As outras perguntam "não
votaria de jeito nenhum" — o núcleo duro. A Quaest pergunta, nome a nome, um ternário
sem meio-termo: conhece-e-votaria, não-conhece, ou conhece-e-não-votaria. Sem opção
neutra, todo eleitor que conhece Flávio e ainda não decidiu por ele vira "rejeição".
O detalhe que me travou: o excesso é assimétrico. Sobre o Datafolha, +9 pp em Flávio,
só +4 em Lula. O formato pune mais quem tem mais não-voto reversível — e o não-voto de
Flávio é justamente o que ele converte no 2º turno. O 57% não mede ódio a mais; mede
morno como se fosse ódio. E o que abre a tesoura em julho não é Flávio subir (56→57,
margem): é Lula cair (53→50).

**Post 2 — reponderação**

Segunda conta: a amostra da Quaest pende para a classe média (31/42/27 em salários
mínimos) e sub-representa a base do país em 4,4 pontos ante a PNAD. Reponderei cada
tabela publicada de volta ao perfil de renda real do Brasil. Resultado honesto: quase
nada. A margem Lula−Flávio no 1º turno anda +0,8; no 2º (proxy, porque o deck não
publica 2T por renda) +1,0. O saldo de aprovação do Lula é o único que mexe perto de
1 ponto cheio: +1,3, porque aprovação varia muito com renda (58 na base, 41 no topo).
Tudo isso cabe dentro do erro de arredondamento do deck. Conclusão que eu publicaria
nos dois sentidos: a renda NÃO explica o placar. A direção do viés é pró-Lula —
sub-representar o pobre subestima o Lula, corrigir amplia a vantagem dele. Mas de leve.
Quem quiser explicar por que a Quaest destoa vai ter que procurar em outro lugar que
não a renda.
