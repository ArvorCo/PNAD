# Politize: o jogo da conversa. Contrato entre roteiro, motor e arte

Página: `docs/politize_game.html` (publicada em `https://brasil.arvor.co/politize_game.html`), linkada de
`docs/politizesuavizinhanca.html`. Pasta do jogo: `docs/politize_game/` (`app.js`, `app.css`, `avatares.js`,
`cenas.js`, `dados.js`, `manifest.webmanifest`). Tudo estático, HTML + CSS + JS puros, **scripts clássicos
(sem `type="module"`, sem `fetch`)**, para abrir inclusive de `file://`, em Android, iOS, desktop e qualquer
navegador dos últimos cinco anos. Sem framework, sem build de JS. Sem rastreador além do gtag que toda página
da casa carrega. Nada sai do aparelho: placar e progresso ficam em `localStorage` (com try/catch).

Ideia em uma frase: o jogador escolhe um personagem, encontra em cenários do dia a dia pessoas que votaram
em outros nomes, anularam, faltaram ou votam em Lula, e escolhe como puxar assunto, como escutar, como
responder e como encerrar. Acerto converte voto para Flávio; erro previsto (os `cuidado` e `o_que_nao_fazer`
do Politize) empurra para Lula ou endurece; com quem é petista de raiz o melhor resultado é o voto nulo.
Tom: sátira política dos dois lados, inclusive do nosso (tio do churras que encaminha boato perde ponto),
mas **toda lição é a do Politize**: escutar, perguntar, respeitar a decisão, nunca oferecer favor, nunca
boato, nunca medo, nunca propaganda no dia. O jogo ensina a conversar; a piada é só o açúcar.

## Regras de texto (JSON, HTML, JS, CSS e comentários)

- pt-BR. **Travessão (o traço longo, U+2014) proibido**; reescrever com vírgula, dois-pontos ou ponto. Hífen e `–` de intervalo
  numérico são permitidos. Teste reprova qualquer travessão.
- Frase curta, verbo forte, humor sem sermão. Caricatura é de **comportamento político e estilo**, nunca de
  cor, religião, orientação sexual, deficiência ou origem como alvo. Zero palavrão pesado (público geral).
- Candidatos: `Flávio` (Flávio Bolsonaro, 22) e `Lula` (13). Terceira via: Cury, Renan Santos, Caiado, Zema.
  Nunca inventar fato, proposta, escândalo ou número que não esteja em `docs/assets/politize/textos.json` ou
  `docs/assets/politize/propostas.json`. Proposta citada leva `fonte` com página do plano.
- "eleitorado de X", nunca "eleitores dele". O voto é secreto; o jogo é ficção com perfis, não pessoas.
- Nunca ensinar nem premiar: boca de urna, carona/comida/dinheiro/favor por voto (Código Eleitoral art.
  299; Lei 6.091/1974), propaganda no dia (Lei 9.504/1997 art. 39 § 5º e 39-A), ameaça, assédio, boato.
  Essas condutas existem **só como opção errada** de tipo `grave`, com `licao` citando o artigo.
- Sem emoji no texto do jogo (os avatares são SVG). Sem hashtag.

## Arquivos de roteiro (autorados, em `analysis/politize_game/roteiro/`)

Um JSON por bloco. O build `scripts/politize-game-build.py` valida tudo, resolve as `fonte`, injeta os
textos de apoio do Politize e grava `docs/politize_game/dados.js` como
`window.POLITIZE_GAME = {...};` (JSON embutido; nunca editar o `dados.js` à mão).

### `personagens.json` (jogáveis, 10)
```
{"versao":"1.0","personagens":[{
  "id":"tio_churras", "nome":"Tio do Churras", "idade":58, "pronome":"ele",
  "bio":"1 a 2 frases de humor, em 2ª pessoa (você).",
  "trunfo":{"tags":["agro","boomer"], "texto":"Com quem tem essas tags, começa com +10 de confiança."},
  "fraqueza":{"tag":"boato", "texto":"Toda opção com a tag boato custa o dobro para você."},
  "fala_inicial":"frase curta na tela de escolha",
  "visual":{"pele":"#...", "cabelo":"#...", "estilo_cabelo":"curto|calvo|coque|franja|longo|rabo|boné|sem",
            "acessorio":"oculos|bone|cordao|headset|biblia|espeto|celular|coletinho|chapeu|fone|crachá|nenhum",
            "roupa":"#...", "roupa_tipo":"polo|regata|camisa|camiseta|vestido|moletom|social|uniforme|jaqueta",
            "barba":true|false, "detalhe":"texto livre curto para o ilustrador"}
}]}
```
Jogáveis (ids fixos, a arte depende deles): `chad_genz` (Gen Z Chad Alpha, academia), `tio_churras`,
`tia_zap`, `mae_crista`, `chad_40_cristao` (pai de família 40+), `nerd_gamer`, `nerd_antifeminista` (jovem
mulher nerd), `empreendedora_mei` (dona de salão), `motoboy_app`, `agro_jovem`.
Tags de trunfo/fraqueza existentes: trunfo usa tags de NPC (abaixo); fraqueza usa tags de opção (abaixo).

### `cenarios.json` (14)
```
{"versao":"1.0","cenarios":[{
  "id":"padaria", "nome":"Padaria", "hora":"manhã", "publico":1,
  "descricao":"1 frase de cena, com cheiro, som ou detalhe.",
  "ambiente":{"paleta":["#..","#..","#.."], "props":["pao","vitrine","cafe"]},
  "abordagem":[  // 3 ou 4 opções para puxar assunto, válidas para qualquer NPC do cenário
    {"texto":"...", "tipo":"melhor|ok|erro|grave", "efeito":15, "tags":["pergunta"], "reacao":"frase genérica do NPC (pode usar {nome})"}
  ],
  "npcs_sugeridos":["isentao_cury","abstencionista"]   // quem aparece aqui com mais frequência
}]}
```
Ids fixos: `whatsapp_familia` (grupo da família, publico 2), `padaria`, `mercado`, `bar`, `shopping`,
`praia`, `show`, `game_online` (chat de voz), `churrasco`, `uber` (corrida de app), `saida_do_culto`,
`academia`, `fila_do_banco`, `rede_x` (thread pública no X, publico 3: cada voto vale três, cada erro também).
`publico` multiplica o desfecho no placar. `efeito` por tipo: melhor +12 a +18, ok +3 a +8, erro −8 a −15,
grave −30 e encerra a conversa (desfecho `baixo`).

### `npcs.json` (24) e `npcs_b.json` (mesma estrutura; o build junta)
```
{"versao":"1.0","npcs":[{
  "id":"isentao_cury", "nome":"Rodrigo, o isentão do Cury", "idade":38, "genero":"M|F",
  "campo":"terceira_via|nao_votou|nulo_branco|lulista_pragmatico|esquerda_ideologica|direita_desgarrada",
  "origem":"cury|renan|caiado|zema|outros_nominais|abstencao|brancos|nulos|bolsonaro_2022|lula",
  "tags":["classe_media","autoajuda","superior"],      // para trunfo dos jogáveis
  "dificuldade":1|2|3,  "confianca_inicial":35,          // 1: 40-50, 2: 30-40, 3: 15-30
  "desfechos":{"alto":"flavio","medio":"nulo|sem_mudanca","baixo":"lula|nulo"},
  "limiares":{"alto":70,"medio":40},                      // confiança final >= alto -> desfecho alto; >= medio -> medio; senão baixo
  "bio":"1 a 2 frases de caricatura (como o jogador o vê).",
  "visual":{...igual ao jogável...},
  "cenarios":["padaria","shopping","rede_x"],             // onde pode aparecer (2 a 5)
  "tema":"Saúde|Violência|Economia|Educação|Corrupção|Enchentes|Infraestrutura",  // tema do Politize que dói para ele
  "queixa":"fala de abertura do NPC depois da abordagem: a dor dele, 1 a 3 frases, na voz do personagem.",
  "escuta":[ 3 ou 4 opções; sempre: 1 melhor (pergunta aberta/escuta), 1 ok, 1 ou 2 erro (interromper, corrigir, já falar de candidato) ],
  "objecoes":[  // exatamente 2
    {"fala":"objeção na voz dele, 1 a 3 frases",
     "opcoes":[ 4 opções: 1 melhor, 1 ok, 1 erro, 1 grave OU erro ]}
  ],
  "fecho":[ 3 opções: melhor (deixa a decisão com ele, agradece), ok, erro (insiste/cobra) ],
  "desfecho_texto":{"flavio":"fala final dele", "nulo":"...", "lula":"...", "sem_mudanca":"..."}
}]}
```
Cada **opção** (em abordagem, escuta, objeções e fecho):
```
{"texto":"o que o jogador diz (1 a 2 frases, na voz do jogador genérico; sem presumir gênero)",
 "tipo":"melhor|ok|erro|grave", "efeito": int,
 "tags":["pergunta"|"escuta"|"respeito"|"programa"|"voto_util"|"alternancia"|"comparecimento"|
         "boato"|"medo"|"pressao"|"desqualifica"|"sermao"|"interrompe"|"carona"|"favor"|"boca_de_urna"|"ameaca"|"mentira"],
 "reacao":"o que o NPC responde (1 a 2 frases)",
 "licao":"só em erro/grave: 1 frase do porquê, em 2ª pessoa, sem sermão",
 "fonte":"só em erro/grave/programa: chave do Politize, ver abaixo"}
```
Chaves válidas de `fonte`:
- `textos.conversas_por_origem.<origem>.cuidado` | `.como_funciona` | `.um_jeito_de_conversar[i]`
- `textos.temas.<Tema>.cuidado` | `.abertura` | `.pergunta`
- `textos.arquetipos.<id>.o_que_nao_fazer[i]` | `.o_que_fazer[i]`
- `textos.perfil.escolaridade.<id>.como_conversar`
- `propostas.<tema_id>.<pagina>` (ex.: `propostas.seguranca.13`), usada em opções com tag `programa`
- `lei.art299` (Código Eleitoral, art. 299), `lei.6091` (transporte de eleitor), `lei.9504.39` (propaganda no dia),
  `lei.voto_secreto` (voto é secreto, leitura agregada). O build resolve essas chaves para o texto de apoio.
O build falha se a chave não existir.

Roster de NPC (ids fixos; a arte depende deles). Campo da esquerda, melhor desfecho = `nulo` salvo indicado:
`petista_ideologico` (camiseta vermelha, estrela), `lulista_gratidao` (seu Zé da feira, fundamental incompleto,
"Lula me deu"; desfecho alto = `flavio`), `universitario_humanas` (patchouli, Che, baseado), `feminista_militante`,
`militante_ong` (coletinho, crachá, bottons), `professora_sindicalizada`, `lulista_pragmatico` (pedreiro, "deu
aumento"; alto = `flavio`), `aposentada_inss` (alto = `flavio`), `sindicalista_cut` (megafone).
Terceira via, faltosos e desgarrados, alto = `flavio`: `isentao_cury`, `faria_limer_zema` (coletinho),
`coronel_caiado` (chapéu, cavalo), `mbl_perdido` (Renan, perdidão), `tiktoker_antissistema` (Renan),
`bolsonarista_magoado` (bolsonaro_2022, "sem o pai não voto"), `irmao_indeciso` (igreja, votou Cury),
`abstencionista_ressaca`, `nulista_protesto` ("são todos iguais"), `branquista` ("ninguém me representa"),
`empresario_zema` (comércio), `motorista_app_renan`, `dona_de_casa_ne` (votou Lula, "Flávio não me desagrada";
origem `lula`; alto = `flavio`, medio = `nulo`), `gamer_apolitico` (não votou, "política é cringe"),
`concursado_cury`.
`npcs.json` = os 12 primeiros do roster acima (da esquerda + isentao_cury, faria_limer_zema, coronel_caiado);
`npcs_b.json` = os 12 restantes.

### `interface.json`
Textos de tela: título, subtítulo, tutorial (3 passos), rótulos (confiança, dia, placar), telas de fim
(graus por pontuação: 5 graus com nome e frase), frases de compartilhar com `{flavio}`, `{nulo}`, `{lula}`,
textos de lição recorrente, aviso legal curto (lado declarado, ficção, voto secreto, lei do dia), rodapé.

## Mecânica (o motor implementa exatamente isto; o roteiro escreve contra isto)

1. **Rodada** = 8 conversas ("8 dias até 24/10"). Sorteio com mistura fixa: 3 terceira via/direita desgarrada,
   2 faltosos ou nulo/branco, 2 lulistas pragmáticos, 1 esquerda ideológica; sem repetir NPC na rodada; cenário
   sorteado entre `npc.cenarios`; `rede_x` no máximo uma vez por rodada.
2. **Confiança** começa em `npc.confianca_inicial` (+10 se alguma tag do NPC está no trunfo do jogador).
   Fases: abordagem (cenário) → queixa + escuta (NPC) → objeção 1 → objeção 2 → fecho. Cada opção soma
   `efeito`; se a opção tem a tag da fraqueza do jogador, o efeito negativo dobra. `grave` encerra na hora
   com desfecho `baixo` e mostra a lição com a fonte. Confiança fica em [0, 100].
3. **Desfecho**: final ≥ `limiares.alto` → `desfechos.alto`; ≥ `limiares.medio` → `desfechos.medio`; senão
   `desfechos.baixo`. Vale ×`cenario.publico` no placar (`flavio`, `nulo`, `lula`, `sem_mudanca`).
4. **Placar da rodada**: votos Flávio, nulos, Lula, sem mudança; saldo = flavio − lula. Grau pelo saldo e por
   erros graves (0 graves obrigatório para o grau máximo). Recorde e personagens já usados em `localStorage`.
5. **Caderno**: toda lição (erro/grave) vira um card com fonte; no fim, o recap lista as lições da rodada.
6. Sem cronômetro. Tudo acionável por toque e teclado (botões ≥ 44 px, foco visível, `aria-live` nas falas).
   `prefers-reduced-motion` desliga animação. Largura base 360 px (retrato); em ≥ 900 px o palco centraliza
   (máx. 720 px) com o caderno e o placar numa coluna lateral.

## Arte (`avatares.js` e `cenas.js`)

- `window.POLITIZE_AVATARES.svg(visual, expressao)` devolve string SVG 1:1 (viewBox 0 0 200 200), flat,
  três expressões: `fechado`, `neutro`, `aberto` (sobrancelhas e boca), construídas do objeto `visual` do
  contrato (pele, cabelo, estilo, acessório, roupa, barba). Sem texto dentro do SVG. Determinístico.
- `window.POLITIZE_CENAS.svg(cenario)` devolve fundo 16:9 (viewBox 0 0 640 360) com a paleta e 2 a 4 props
  simples do `ambiente`. Sem texto. Tamanho total dos dois arquivos abaixo de 60 KB.
- Contraste: texto sobre painel passa WCAG AA (auditar com `scripts/contrast-audit.py`).

## Paleta da casa (de `docs/assets/politize/app.css`)
`--paper:#f7f5ee --card:#fff --ink:#151812 --muted:#535b54 --line:#d5d2c6 --verde:#0b7a3b --amarelo:#f2c230
--ouro-txt:#7d5b00 --azul:#0d2238 --azul2:#1f5f9e --flavio:#1f5f9e --lula:#c8412f --lula-txt:#a8321f`.
Fontes: Fraunces (display), IBM Plex Sans Condensed (texto), IBM Plex Mono (rótulos), via Google Fonts com
fallback de sistema. Tamanho de corpo ≥ 17 px.
