# Datafolha 07/2026 — memórias de preparação (dossiê `datafolha_072026.html`)

> Status: **relatório completo AINDA NÃO divulgado** (divulgação na imprensa em
> 24/07/2026; relatório integral prometido para a semana seguinte). Tudo aqui é
> pré-análise com os números de imprensa. NÃO publicar dossiê definitivo antes
> de auditar o PDF oficial + registro TSE.

## O que já temos (fonte: imprensa, 24/07/2026)

- **1º turno:** Lula 40 (−1 vs jun), Flávio 32 (+1), Caiado 4 (+1), Zema 3 (+1),
  Renan 3 (=), Cury 2 (=), Samara 1 (−1), Daciolo 1 (=), Pimenta 1 (=),
  PSTU/PCB/PRTB não pontuaram, B/N 8 (+1), NS 3 (−1). Soma publicada: 98.
- **2º turno (24/07):** Lula 48 × Flávio 43 (B/N 9, NS 1); Lula 47 × Caiado 40
  (B/N 11, NS 2); Lula 48 × Zema 40 (B/N 10, NS 2).
- **Rejeição:** Flávio 48, Lula 46, Zema 13, Daciolo/Caiado/Renan 12, Pimenta 11,
  Samara 9, PCB/PRTB 8, Cury/PSTU 7.
- **Governo:** ruim/péssimo 38, ótimo/bom 32, regular 28; aprova 49 × desaprova 48.
- Série completa Lula×Flávio 2T e demais números em `dados.json`.

## Matemática de transferência (já rodada)

- Script: `scripts/datafolha-072026-graficos.py`. Método: matriz de afinidade
  a priori → **IPF/RAS (mínima entropia cruzada)** até bater as margens
  publicadas (1T escalado 98→101 pts do 2T). Leitura agregada, não painel.
- Hipóteses ideológicas (rev. Leonardo 25/07): **bases 100% fiéis** — voto
  de Flávio no 1T vai INTEIRO para Flávio no 2T (zero p/ Lula e zero p/
  B/N; cruzamento de base = ruído de pesquisa/troll), idem base Lula.
  Daciolo → Flávio quase integral (0 p/ B/N); Samara → Lula em totalidade;
  Cury → maioria Flávio; B/N do 2T alimentado quase só por
  Caiado/Zema/Renan (muito Flávio, um pouco Lula, resto anula).
- Resultados-chave (pontos do 2T Lula×Flávio):
  - Fora das bases, **Flávio +10,1 × Lula +6,8 (1,48:1)**. Junho foi 2:1
    (+12×+6) — citar a série: a consolidação pró-Flávio se repete.
  - Caiado→Flávio 2,1 de 4 (~54%); Zema→Flávio 1,8 de 3 (~60%);
    Renan→Flávio 1,9 de 3 (~64%); Daciolo→Flávio ~1,0 de 1; Cury→Flávio 1,1 de 2.
  - B/N: 8→9, alimentado por Caiado/Zema/Renan (1,1+0,8+0,8); NS: 3→1 e o
    indeciso que decide pende LEVEMENTE pró-Lula (1,0×0,6) — o ganho de
    Flávio vem todo da direita pulverizada, não do indeciso.
- Sensibilidade: a razão ~1,5:1 é robusta à escolha da prior (as margens
  mandam); o split candidato-a-candidato depende da prior — apresentar como
  estimativa, com a nota metodológica de sempre.

## Teses editoriais para o dossiê (com os 5 PNGs prontos em `docs/img/datafolha_072026/`)

1. **Sankey** (`sankey_lula_flavio.png`): quem transfere para quem quando a
   eleição afunila. Terceiras vias de direita são afluentes do rio Flávio.
2. **Cenários consolidados** (`cenarios_2turno.png`): Lula é constante (47–48);
   só o adversário muda. Flávio 43 (−5), Caiado/Zema 40 (−7/−8) e mais B/N.
   Teto anti-Lula = 43, só Flávio alcança.
3. **Blocos 1T** (`blocos_1turno.png`): oposição somada 45 × bloco Lula 42.
   Voto útil = antecipar consolidação inevitável. Flávio+Caiado+Zema já > 40 de Lula.
4. **Resiliência** (`resiliencia_series.png`): dez/25 51×36 → 2026 constante
   43 sob ataques (Banco Master maio, fogo cruzado das 3ªs vias). Liderou em
   abril (46×45). Piso de Flávio não cede há 3 pesquisas.
5. **Rejeição × teto** (`rejeicao_teto.png`): tese da 3ª via ("menos rejeição
   ganha") falha nos próprios números: ¼ da rejeição, 3 pts a menos no 2T.

## Ângulo político encomendado (Leonardo, 25/07)

- Inviabilidade das terceiras vias — tanto a a "falsa direita neotucana"
  (Zema/Renan/Caiado) quanto as da esquerda. Quem ataca Flávio agora fica
  fora de eventual governo e arrisca sabotar os próprios candidatos
  legislativos (PSD, NOVO, Missão; PP/União também podem acabar na oposição).
- Desafio estratégico 2026: **Senado** — eleger senadores alinhados exigirá a
  mesma resiliência; campanhas legislativas serão sabotadas. Tema para seção
  própria no dossiê definitivo.
- Post do X (~1500 chars) rascunhado em `post_x.md` (4 imagens + Sankey).

## Checklist quando o relatório completo sair

- [ ] Registro TSE (nº BR-XXXXX/2026), n, campo, municípios, tipo de coleta
  (jun foi BR-09956/2026, 2.004 entrevistas, 139 municípios, pontos de fluxo).
- [ ] Margem sobre a diferença: 48×43 → gap 5 pp; com deff simulado a margem
  da diferença fica ~±5 pp — checar se "Lula na frente" sobrevive (em junho
  não sobreviveu; reponderação PNAD zerou).
- [ ] Reponderar renda à PNAD (pipeline `brasil`) como em junho.
- [ ] Crosstabs oficiais de transferência 1T→2T: comparar com nossa matriz IPF
  (validação do método — publicar previsto × observado).
- [ ] Setores/bairros repetidos vs junho (fantasma da amostra repetida: jun
  repetiu 77% dos setores de maio).
- [ ] Perguntas aplicadas e não publicadas (perguntas-fantasma).
- [ ] Recortes: mulheres, ≤2 SM, fundamental (os 3 déficits de Flávio em jun).
- [ ] Atualizar razão de consolidação na série: mai 2:1 → jun 2:1 → jul 1,5:1.
