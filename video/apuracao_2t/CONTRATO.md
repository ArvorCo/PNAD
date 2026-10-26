# Contrato do vídeo "A noite do 2º turno" (video/apuracao_2t)

Vídeo documental de cerca de 10 minutos (portão 570 a 660 s), 16:9 e 9:16, narrado na voz do
Leonardo (ElevenLabs v4 com tags de áudio), marca Arvor Intelligence, para fechar o dossiê
`docs/apuracao_2T_2026.html`. Projeto Remotion clonado de `video/sete_riscos/` (clone mais
recente de `video/masterclass/`) em 25/10/2026: mesmo motor (`plano.ts`, `Palco`, `Clipe`,
`HUD`, `Legenda`, `Trilha`), mesma paleta (`tema.ts`) e mesmos efeitos (`public/sfx`, os
genéricos copiados). Os três projetos irmãos (`fiscais`, `masterclass`, `sete_riscos`) seguem
intocados e nada aqui importa de lá. `node_modules` é link para `../sete_riscos/node_modules`.

Este arquivo é a fonte única dos nomes, esquemas e posse de arquivos. Quem precisar mudar um
esquema muda aqui primeiro.

**Estado em 26/10/2026: REVISÃO PELA TESE.md, VOZ E MÚSICA GERADAS, RENDER FEITO.** Duração 10:32
(632,0 s). A tese segue `analysis/apuracao_2t_2026/TESE.md` (juízo editorial do autor): a projeção
acertou; as pesquisas e a régua de renda mediram certo até o último campo, e a distância até a
urna é a medida do que mudou entre sábado e domingo. Revisão de 26/10: capítulo 6 virou "As
urnas por dentro" (logs, arquivos de assinatura, RDV e a totalização paralela); saíram
`noite-17h`, `noite-19h01`, `cap-paralela` e `paralela-convite`; `turnos-disponiveis` virou
`turnos-transferencia`; as cenas de seção usam o censo dos 499.207 boletins. Mudar a ordem exige
mudar juntos `src/ordem.ts`, a tabela da seção 1, `tests/test_video_apuracao_2t.py` (`IDS`) e
`src/cenas/registro.ts`.

## 1. Ordem das cenas (`src/ordem.ts`, `roteiro/roteiro.md`)

Um bloco `## id` por cena no roteiro, nesta ordem exata. Cartões `cap-*` são cenas narradas
curtas (3 a 5 s: "Capítulo dois. A projeção."), um por capítulo, menos a abertura.

| capítulo (id, número, título, cor) | cenas |
|---|---|
| `abertura` (0, "Abertura", `tealClaro`) | `abertura`, `tese` |
| `noite` (1, "A noite minuto a minuto", `flavio`) | `cap-noite`, `noite-stf`, `noite-parada`, `noite-virada`, `noite-fim` |
| `projecao` (2, "A projeção", `ouro`) | `cap-projecao`, `proj-primeiro-ponto`, `proj-serie`, `proj-sem-virada` |
| `turnos` (3, "Entre os dois turnos", `lula`) | `cap-turnos`, `turnos-swing-uf`, `turnos-transferencia`, `turnos-abstencao` |
| `secoes` (4, "Seção por seção", `media`) | `cap-secoes`, `secoes-encerramento`, `secoes-biometria`, `secoes-comparecimento`, `secoes-ranking` |
| `pesquisas` (5, "Pesquisas contra a urna", `outros`) | `cap-pesquisas`, `pesq-erro`, `pesq-reponderacao`, `pesq-hipotese` |
| `urnas` (6, "As urnas por dentro", `teal`) | `cap-urnas`, `urnas-cadencia`, `urnas-integridade`, `urnas-assinatura`, `paralela-177` |
| `fecho` (7, "Fecho", `tealClaro`) | `cap-fecho`, `fecho-arvor`, `fecho-chamada` |

32 cenas em 8 capítulos. Elo com o dossiê (`analysis/apuracao_2t_2026/CONTRATO_DOSSIE.md`): os
capítulos 1 a 7 do vídeo seguem os capítulos 2, 3, 6 e 7, 8, 11, 12 e 14 da página (a abertura
usa o 1).

## 2. Roteiro (`roteiro/roteiro.md`) e rótulos obrigatórios

- Cabeçalho livre, depois um `## id` por cena. Tags em inglês entre colchetes (`[calm]`,
  `[serious]`, `[thoughtful]`, `[curious]`, `[emphatic]`, `[short pause]`, `[pause]`,
  `[slowly]`), no máximo uma a cada duas ou três frases.
- Sem travessão (o traço longo), sem a palavra "fraude" (nem em paráfrase: "roubo de eleição",
  "eleição roubada"), sem hashtag, sem emoji. "Eleitorado de X", nunca "eleitores dele". Evitar
  abreviação que o v4 lê errado ("aptos" virou "apartamentos": escrever "eleitores").
- Números por extenso na narração (nenhum algarismo nas linhas narradas); uma CAIXA ALTA por
  bloco. Todo número narrado leva, dentro do bloco, um comentário HTML
  `<!-- dado: <caminho.no.apuracao_2t.json> = <valor como aparece no JSON> -->` (um por número;
  seletores `[i]`, `[campo=valor]` e `.length` aceitos). O teste exige que o valor por extenso
  apareça no bloco.
- Fatos externos (lei, decisão, matéria) só entram se estiverem em `roteiro/fontes.md` com URL,
  data de acesso e trecho. Marcar `<!-- fonte: <id em fontes.md> -->` no bloco.
- Alvo: cerca de 1.450 a 1.600 palavras narradas (145 palavras por minuto no v4), para 9:30 a
  11:00 com o respiro de 0,9 s por cena e a cauda de 3 s. Ajusta-se cortando ou estendendo o
  roteiro, nunca acelerando o áudio.
- **Rótulos obrigatórios** (CLAUDE.md e `analysis/apuracao_2t_2026/CONTRATO.md`), ditos no bloco
  indicado e repetidos na tela (`ROTULO` em `src/componentes/textos.ts`):
  - projeção: "projeção estatística a partir do que já foi totalizado; não é resultado nem
    previsão de vitória" (`proj-primeiro-ponto`);
  - totalização paralela: "soma dos BUs recebidos, não projeção" (`paralela-177`);
  - atraso e abstenção atípica: "pedem explicação, não indicam irregularidade";
  - pausa: "intervalo sem versão nova publicada", nunca acusação;
  - seções: "atipicidade estatística não é irregularidade" (`secoes-ranking`);
  - hipótese do autor: dita como juízo editorial, nunca como fato (`pesq-hipotese`).
  O teste `test_rotulos_obrigatorios_por_cena` confere os rótulos da projeção, da paralela e das
  seções; os demais são de revisão do roteiro.
- Posição editorial: a hipótese do autor sobre as pesquisas entra rotulada como juízo editorial;
  o erro das pesquisas é medido pelos números do dossiê, com o mesmo padrão para todos os
  institutos. Moraes e o STF só aparecem com decisão, data e base legal identificadas
  (`noite-stf`); nada além do que a fonte prova.

## 3. `src/dados/apuracao_2t.json` (gerado por `scripts/video-apuracao-2t-dados.py`)

Esquema (tipos em `src/tipos.ts`):

```
{ gerado_em, fontes: { caminho: sha256 },
  pendentes: [bloco...],      // blocos esperados que ainda não existem em disco
  avisos: [texto...],         // blocos acima de 600 KB, não embutidos (também entram em pendentes)
  mapa: { view: 1000, ufs: [{ uf, d }] },   // 27 UFs, mesma projeção dos vídeos irmãos
  presidente, linha_do_tempo, projecao_noite, comparacao_1t, abstencao,
  secoes_ranking, pesquisas_vs_urna, paralela,
  secoes, secoes_voto, hipotese_autor, logs, rdv, metadados, transferencia }   // cada um = JSON de
                                          // analysis/apuracao_2t_2026/dados/<bloco>.json
```

- Chave acima de 200 KB sai e entra em `avisos`; se for dicionário, desce um nível e fica com as
  subchaves que cabem (`secoes.agregados.brasil` fica, `secoes.agregados.por_municipio` sai),
  desde que o resultado caiba. O teste aceita o dicionário enxugado e exige aviso para cada
  subchave omitida.
- O script tolera ausência: bloco que falta vai para `pendentes` e a cena que o usa mostra
  "DADO PENDENTE" com o caminho, nunca erro de render. Rode de novo quando o dossiê gravar um
  bloco novo.
- As cenas leem valores **por caminho** (`src/ref.ts`: `presidente.nacional.pct.flavio`,
  `linha_do_tempo.nacional.curva`), então o esquema interno de cada bloco é decidido pelo dossiê
  e os caminhos do registro são ajustados no mesmo commit em que o bloco aparece.
- **Caminhos provisórios** em `src/cenas/registro.ts` (conferir quando o bloco existir):
  `presidente.nacional.{pct.flavio,pct.lula,secoes}` (forma do 1º turno),
  `linha_do_tempo.nacional.{curva,serie_flavio,serie_lula,secoes_19h01}`,
  `projecao_noite.{primeiro_ponto.p_f,serie}` (série `[min, p_f_proj, faixa_a, faixa_b, p_f_obs,
  pst]`, como na rota `/api/2t/projecao`), `comparacao_1t.ufs[].{uf,swing_pp,pct_1t,pct_2t}`,
  `abstencao.ufs[].{uf,delta_pp}`, `secoes_ranking.{encerramento.apos_17h_pct,total_sinalizadas,
  top[]}`, `pesquisas_vs_urna.{ranking_publicado,ranking_reponderado}[].{instituto,flavio,lula,
  erro_pp}`, `paralela.{recebidos.{bus,secoes},conferencia.{iguais,divergentes}}`.
- Eixo do tempo das séries: minutos depois das 17:00 de Brasília (convenção da apuração);
  `totalizado_em` de AC, AM, RO, RR, MT e MS vem em hora local e passa por
  `corrigirTotalizadoEm` antes de chegar ao dossiê, não aqui.
- Teste: `tests/test_video_apuracao_2t.py` confere o esquema, a união `prontos ∪ pendentes`, o
  SHA-256 de cada fonte e que cada bloco embutido é idêntico ao arquivo do dossiê.

## 4. Mídia (`midia/manifesto.json`, `midia/cache.json`, `src/dados/midia.json`)

Mesmo esquema e mesmo código da série, em `scripts/video-apuracao-2t-midia.py` (wrapper de
`scripts/video-sete-riscos-midia.py`: troca pastas e `CENAS_VALIDAS`, lida de `src/ordem.ts`).
O manifesto tem só itens de apoio (os gráficos e telas saem do Remotion e das capturas):
`sala_apuracao_noite` (clipe), `relogio_parado` (clipe, cena da parada), `escola_fim_da_tarde`
(clipe), `papel_boletim_mesa` (clipe) e `sala_apuracao_still` (imagem, fundo da capa). Prompts em
inglês, documental, sem rosto reconhecível, sem bandeira, sem cor partidária, sem texto legível.
Provedores: `openclaw infer` primeiro; se recusarem, `--mflux` (still local + Ken Burns); o que
sobrar fica `manual` e `--faltando` imprime o prompt (CapCut, Grok Imagine). Arquivos feitos à
mão caem em `midia/entrada/<id>_<fmt>.<ext>` e `--absorver` normaliza.

## 5. Capturas (`capturas/roteiro.json`, `src/dados/capturas.json`)

`scripts/video-apuracao-2t-capturas.py` (wrapper do motor de `video-sete-riscos-capturas.py`).
Três tipos:

- **telão**: quadros 1920×1080 já renderizados em `video/vinheta_2t/public/final/*.png`
  (`pres`, `projecao`, `regioes`, `ufs`, `abstencao`, `comparecimento`, `gov-2t`) copiados para
  `public/midia/cap_<id>_16x9.png` com o SHA-256 da origem. Só 16:9: a cena os mostra em moldura
  16:9 (`Zoom`) nos dois formatos, nunca recortados. Ids: `cap_tela_pres`, `cap_tela_projecao`,
  `cap_tela_regioes`, `cap_tela_ufs`, `cap_tela_abstencao`, `cap_tela_comparecimento`,
  `cap_tela_gov_2t`. `pausas` e `paralela` existem na pasta e ainda não têm id no roteiro.
- **páginas**: quadro parado do dossiê (`/apuracao_2T_2026.html`) e da live
  (`/apuracao_2t_ao_vivo.html`), servidos por `docs/` em 4173, 16:9 e 9:16. As páginas ainda não
  existem: o item fica `falhou` no registro até existirem. Nunca se monta print.
- **tomadas**: gravações com o motor da masterclass (vazio por enquanto).

## 6. Voz, música e efeitos (`scripts/video-apuracao-2t-voz.py`, núcleo em `scripts/video_voz.py`)

- Wrapper de `scripts/video-sete-riscos-voz.py`: troca `PROJETO`, `ORDEM_TS`, o catálogo de
  efeitos e os prompts de música. `public/voz/<id>.mp3`, `public/voz/<id>.palavras.json`,
  `src/dados/voz.json`; narração v4 com carimbo por palavra, `previous_text`/`next_text`.
- Música: uma faixa por capítulo em `public/musica/<capitulo>.mp3` (`/v1/music`, extensão do
  capítulo + 12 s, instrumental, −23 LUFS; espera de 90 s no 429), `src/dados/musica.json`.
  Prompts por capítulo: abertura (tensão atenta), noite (redação de eleição, pulso eletrônico),
  projeção (analítico, sintetizadores limpos), turnos (reflexivo, piano e cello), seções
  (forense, percussão seca), pesquisas (marimba e pizzicato), paralela (pulso cívico brilhante),
  fecho (cordas, resolução calma).
- Efeitos: 11 genéricos já copiados em `public/sfx` (`whoosh`, `blip`, `stamp`, `scan`,
  `chime`, `tique`, `alerta`, `papel`, `riser`, `zoom`, `qr`); o script gera os que faltarem.
- **Não gerar voz, música nem render antes do roteiro final.** `--so-musica` sem `voz.json`
  para antes de qualquer chamada.

## 7. Cenas (`src/cenas/`) e componentes genéricos

- `src/cenas/registro.ts` mapeia as 32 ids para `CenaDef` (`componente`, `gatilhos`, `midia`,
  `sfx`), com `satisfies Record<CenaId, CenaDef>`: cena sem registro não compila.
- `src/cenas/genericas.tsx` tem as fábricas, todas parametrizadas por props e por caminhos de
  dados (`src/ref.ts`):
  - `cenaTexto`: cartão com chip, título grande, subtítulo e linhas em sequência;
  - `cenaNumero`: número grande que sobe (`Contador`) mais números secundários;
  - `cenaSerie`: gráfico de linhas de série temporal (`SerieGrafico`), com marcas verticais
    rotuladas e faixas sombreadas (a parada do TSE, por exemplo); eixo em `hhmm` ou número;
  - `cenaMapa`: mapa de UF em cores (`MapaCores`), escala divergente (Lula, Flávio) ou sequencial;
  - `cenaRanking`: tabela de ranking (`Tabela`) com colunas declaradas;
  - `cenaCaptura`: tela do telão ou página em moldura 16:9 com zoom por keyframes (`Zoom`;
    `video: true` para gravação mp4).
  Cartões `cap-*` usam `CartaoCapitulo`. Dado ausente vira o aviso "DADO PENDENTE" com o caminho.
- Gatilhos: nome → [palavra, reserva em segundos]; busca sequencial. Ficam vazios até a voz
  existir; `genericas.tsx` aceita `gatilho` em marcas e faixas e `g.secundarios` nos números.
- Cena nova de formato próprio (um gráfico que as fábricas não cobrem) ganha arquivo próprio em
  `src/cenas/` e entra no registro; não se acrescenta caso especial às fábricas.

## 8. Posse de arquivos

| Etapa | Escreve | Não toca |
|---|---|---|
| estrutura (esta) | `src/ordem.ts`, `capitulos.ts`, `tipos.ts`, `dados.ts`, `ref.ts`, `Root.tsx`, `verificar.ts`, `linha.ts` (portão), `componentes/`, `cenas/genericas.tsx`, `cenas/registro.ts`, `package.json`, `README.md`, `CONTRATO.md`, scripts `video-apuracao-2t-*.py`, `tests/test_video_apuracao_2t.py`, `midia/manifesto.json`, `capturas/roteiro.json` | `roteiro/`, `public/voz`, `public/musica` |
| dados | `src/dados/apuracao_2t.json` (rodar o script quando o dossiê gravar bloco novo) | resto |
| roteiro (depois dos dados) | `roteiro/roteiro.md`, `roteiro/fontes.md` | resto |
| voz e música (depois do roteiro) | `public/voz`, `public/musica`, `src/dados/voz.json`, `musica.json` | resto |
| cenas finais (depois da voz) | gatilhos, caminhos de dados e cenas próprias em `src/cenas/` | resto |
| capturas das páginas (depois do dossiê e da live) | `public/midia/cap_*`, `src/dados/capturas.json` | resto |

Lint zero (`ruff`, `black`, `eslint`), typecheck zero. Scripts em Python: `kebab-case`, PEP 8.
Estado do `npm run verificar`: sem roteiro nem voz, informa "nada a medir" e sai com 0; com o
roteiro, estima a 145 palavras por minuto; com a voz, mede e sai com 1 fora de 570 a 660 s.
