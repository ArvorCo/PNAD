# Senado 2027 diante do STF: contrato entre as partes

Página final: `docs/senado_2027.html`, gerada por `python3 scripts/senado-2027-build.py`
a partir de `docs/senado_2027.template.html` e de `docs/assets/senado_2027.json`
(escrito por `python3 scripts/senado-2027-motor.py`). Nunca editar o HTML gerado.
Data de corte: 07/10/2026, três dias depois do 1º turno de 04/10/2026 e antes do 2º
turno de 25/10/2026. Origem da investigação: post de Andreza Matais no X (cerca de
06/10/2026) dizendo que entre os senadores eleitos há muitos investigados no Supremo
e que "ninguém vai mexer em quem pode picar". A página cita o post como origem, não
como tese: a tese é testada.

Regras da casa que valem para todo arquivo deste projeto: travessão (`—`) proibido em
qualquer texto; lint zero (`ruff check scripts tests`, `black --check scripts tests`);
testes em `tests/` importam módulos de `scripts/` no topo; scripts novos em `kebab-case`,
módulos importáveis em `scripts/senado_2027/` (pacote com `__init__.py`); texto gerado
nunca presume gênero ("a candidatura de X", "o mandato de X"); números com URL de
origem ao lado; nenhum score digitado à mão: K e C saem da régua do motor aplicada
aos fatos dos JSON. Presunção de inocência em toda frase: "investigado", "indiciado",
"réu", "condenado" exatamente como no documento de origem; "nada localizado" nunca
vira "ficha limpa".

## 1. Elenco: `analysis/senado_2027/elenco.json`

Lista das 81 cadeiras projetadas para 01/02/2027. Cada item:

```json
{"slug": "gustavo-gayer", "cadeira": "GO-2026-a", "nome": "Gustavo Gayer",
 "nome_completo": null, "partido": "PL", "uf": "GO",
 "mandato": "eleito_2026 | reeleito_2026 | ate_2031 | suplente_ate_2031",
 "bloco": "DB | D | CD | C | CE | E",
 "contingencia": null}
```

- `bloco` é classificação editorial declarada: `DB` direita bolsonarista, `D` direita,
  `CD` centro-direita, `C` centro e centrão, `CE` centro-esquerda, `E` esquerda.
  Tucano (PSDB, Cidadania) nunca entra como direita por decisão da casa (26/09/2026);
  Plínio Valério e Marina JHC recebem bloco próprio justificado no JSON do senador.
- `contingencia` descreve quando a cadeira pode mudar de ocupante antes ou depois da
  posse: `{"tipo": "segundo_turno_governo | sub_judice | licenca | ministerio",
  "substituto": {"nome": ..., "partido": ...}, "nota": ...}`.
- Cadeiras ocupadas hoje por suplente de titular licenciado (ministério ou licença):
  o elenco traz o **titular** como ocupante no cenário de governo Flávio (ministros
  de Lula voltam ao Senado em 01/01/2027) e o suplente como ocupante no cenário de
  governo Lula. Os dois recebem JSON próprio.

## 2. Um JSON por senador: `analysis/senado_2027/senadores/<slug>.json`

```json
{
  "slug": "gustavo-gayer",
  "nome": "Gustavo Gayer",
  "partido": "PL",
  "uf": "GO",
  "mandato": "eleito_2026",
  "bloco": "DB",
  "bloco_justificativa": "Deputado federal do PL, núcleo bolsonarista; ...",
  "alinhado_governo_lula": false,
  "votacao_2026": {"votos": 1234567, "fonte": "https://..."},
  "casos": [
    {
      "id": "gayer-inq4974",
      "titulo": "Réu por injúria contra Lula (Inq 4.974)",
      "tipo": "opiniao | patrimonial | eleitoral | 8_de_janeiro | outro",
      "estagio": "condenacao | reu | denuncia_oferecida | indiciado | suspenso | investigado | alvo_de_busca | condenacao_civel | eleitoral_pendente | reu_civel | citado | representacao | antigo_sem_desfecho | arquivamento_pedido | arquivado | acusacao_sem_procedimento | absolvido_ou_trancado | testemunha",
      "foro": "STF | STJ | TSE | TRF | primeira_instancia | PF | MP | outro | nao_informado",
      "relator": "Flávio Dino",
      "data_fato": "2026-04-28",
      "data_ultima_decisao": "2026-04-28",
      "resumo": "A 1ª Turma recebeu por unanimidade a denúncia da PGR ...",
      "defesa": "O deputado afirma que ...",
      "fontes": [
        {"url": "https://...", "veiculo": "Agência Brasil", "data": "2026-04-28",
         "titulo": "...", "acesso": "pagina | trecho_de_busca | relatorio_anterior"}
      ],
      "confianca": "alta | media | baixa",
      "nos_relatorios": {"claude": true, "gemini": true, "chatgpt": true, "perplexity": false}
    }
  ],
  "sinais_contrapeso": [
    {
      "tipo": "declaracao_pro_impeachment | autoria_pedido_impeachment | assinatura_pedido_impeachment | cpi_contra_ministros | acao_judicial_contra_ministro | representacao_administrativa_contra_ministro | voto_pec8_sim | voto_pec8_nao | voto_pec8_ausente | projeto_ou_pec_contra_stf | declaracao_contra_impeachment | dialogavel_segundo_stf | sondagem_com_ministro | nao_assinou_pedido | sem_posicao_localizada | defesa_do_stf",
      "alvo": "Moraes | Dino | Toffoli | Gilmar | Barroso | STF | PEC 8/2021 | ...",
      "data": "2026-10-05",
      "resumo": "Consta da lista de 49 do Metrópoles ...",
      "fontes": [{"url": "...", "veiculo": "...", "data": "...", "titulo": "...", "acesso": "..."}]
    }
  ],
  "nota_editorial": "Texto curto, em português corrente, que a página usa na ficha.",
  "scores_anteriores": {"claude": {"K": 100, "C": 92}, "gemini": {"K": 100, "C": 92},
                        "chatgpt": {"K": 90, "C_imp": 96, "P_pec": 96}, "perplexity": null},
  "verificado_em": "2026-10-07"
}
```

- `casos` só com procedimento que atinge o senador em pessoa. Processo contra parente,
  assessor, suplente ou aliado entra como `citado` no máximo, com o vínculo no resumo.
- Caso arquivado, trancado ou absolvido fica no JSON com o estágio correspondente: o
  motor dá peso pequeno, e a página mostra no anexo de arquivamentos.
- `defesa` é obrigatória sempre que houver manifestação localizada; sem ela, gravar
  "Manifestação da defesa não localizada nesta pesquisa".
- `scores_anteriores` guarda os números dos quatro relatórios de origem (Claude,
  Gemini, ChatGPT, Perplexity) só para a figura de dispersão; o motor não os usa.
- `fontes[].acesso`: `pagina` quando a URL foi aberta e lida; `trecho_de_busca` quando
  só o resumo do buscador foi lido; `relatorio_anterior` quando vem de um dos quatro
  relatórios sem reabertura. Confiança `alta` exige ao menos uma fonte `pagina` de
  órgão oficial (STF, PGR, PF, TSE, Senado, Agência Brasil) ou dois veículos
  independentes com `pagina`.

## 3. Régua (motor): `scripts/senado_2027/scores.py`

Nenhum score é copiado dos relatórios. O motor aplica a mesma régua aos fatos.

**K, exposição judicial documentada (0 a 100).** Por caso: estágio (condenação 60;
réu 45; denúncia oferecida 35; indiciado 30; suspenso 30, para réu com ação sobrestada
por licença da Casa ou liminar; investigado 25; alvo de busca 25; condenação cível 25,
para improbidade e indenização, que não são condenação criminal; eleitoral pendente 20;
réu cível 15; citado 12; representação 10; antigo sem desfecho 8, para procedimento com
última decisão anterior a 2024 e desfecho não localizado; pedido de arquivamento 8;
arquivado 6; acusação sem procedimento 5; absolvido ou trancado 4; testemunha 2)
+ 10 se o foro atual é o STF (+5 se STJ ou TSE) + 5 se o relator é um dos ministros alvo
de pedidos de impeachment (Moraes, Dino, Toffoli, Gilmar Mendes) + 10 se a última decisão
é de 2025 ou 2026. **Caso inativo** (arquivado, absolvido ou trancado, testemunha, acusação
sem procedimento, antigo sem desfecho, pedido de arquivamento) vale só os pontos do estágio.
K do senador = maior caso + 0,3 × soma dos demais, teto 100. K = 0 significa "nada
localizado nas fontes desta pesquisa".

**C, contrapeso (0 a 100, por alvo).** Dois alvos, sempre separados:
`C_imp` (impeachment de Alexandre de Moraes que chegue ao plenário em governo Flávio
Bolsonaro, 54 votos já na admissibilidade pela liminar de Gilmar Mendes) e `C_pec` (PEC
que limite o STF, 49 votos em dois turnos).
Base por bloco, `C_imp`: DB 85, D 75, CD 55, C 35, CE 10, E 3. Base `C_pec`:
DB 92, D 88, CD 80, C 65, CE 30, E 10. Ajustes (cada tipo conta uma vez), `C_imp` / `C_pec`:
declaração pró-impeachment +10 / +5; assinatura de pedido de impeachment +8 / +4; CPI
contra ministros (requerimento, relatoria ou assinatura) +8 / +4; ação judicial contra
ministro +8 / +4; representação administrativa (CNJ, Conselho) +4 / +2; PEC 8 "sim"
+3 / +10; PEC 8 "não" −10 / −20; declaração contra impeachment −15 / −5; "dialogável"
segundo ministros ou sondagem com ministro −8 / 0; não assinou pedido ou CPI da própria
bancada −4 / 0; sem posição localizada −6 / −3, **só quando não há nenhum sinal com
posição**; alinhamento declarado com o governo Lula −10 / −5; redutor patrimonial
−0,25 × K / −0,10 × K, aplicado só sobre a parcela de K que vem de casos `patrimonial`
ativos (condenação, condenação cível, réu, réu cível, suspenso, denúncia, indiciado,
investigado, alvo de busca); casos de `opiniao` e `8_de_janeiro` não reduzem, porque a
evidência aponta o efeito contrário. **Piso de autoria**: quem é autor de pedido de
impeachment ou relator de CPI que pediu indiciamento de ministro tem piso 85 em `C_imp`
e 90 em `C_pec`, porque autoria é o comportamento observado mais forte.
Limites 2 e 97. Cenário "governo Lula": `C_imp` dos blocos C e CD cai 15 pontos
e do bloco D cai 5; `C_pec` cai 8 e 3. O cenário é parâmetro do motor.

**Arbitragem.** Nenhum score dos quatro relatórios é usado. Cada divergência entre
relatórios, agentes e fontes fica em `analysis/senado_2027/arbitragem.json` (senador,
campo, o que cada relatório dizia, decisão, fonte) e a página publica a tabela inteira.

**Confiança por senador**: alta com dois ou mais sinais observados (voto nominal,
assinatura, CPI); média com declaração única; baixa para suplente ou sem sinal.
Incerteza da probabilidade: ±5, ±9 e ±14 pontos.

**Simulação**: 20.000 sorteios. Cada senador vota "sim" com probabilidade C sob um
choque comum por bloco e um choque nacional no logit, calibrados para correlação
latente intrabloco 0,35 e nacional 0,15 (desvios 1,01 e 0,87 no logit), para que a
variância não seja a de 81 moedas independentes e o valor esperado continue sendo a
soma dos C. Saídas:
distribuição de votos para PEC e impeachment, probabilidade de ≥49 e ≥54, e os
pivôs (senadores cuja troca de voto mais muda a chance de 54).

## 4. Saídas

- `docs/assets/senado_2027.json`: elenco com scores, casos, sinais, simulação,
  arbitragem (divergências entre os quatro relatórios e a resolução adotada),
  `gerado_em`, hashes dos JSON de entrada.
- `docs/assets/senado_2027.csv`: uma linha por senador, para download.
- `docs/senado_2027.html`: página.
- `docs/img/og/senado_2027.png`: card social pelo manifesto de `scripts/social-cards.py`.

## 5. Página (capítulos)

00 Hero: placar de votos esperados para PEC (49) e impeachment (54) nos dois cenários,
em números grandes, com frase em português corrente antes de qualquer gráfico.
01 De onde veio a pergunta: o post de Matais, a coluna de Bela Megale, os números da
imprensa (49, 48, 54, 30) e por que divergem.
02 A régua: o que é K, o que é C, o que não é (culpa, chantagem).
03 O mapa dos 81: dispersão K × C com os nomes, hemiciclo por faixa de C, ranking.
04 Dois tipos de exposição: opinião e 8 de janeiro radicalizam; patrimonial é onde a
hipótese pode valer. Figura por tipo.
05 A conta dos 49 e dos 54: distribuição simulada, pivôs nomeados, cenário Flávio e
cenário Lula, contingências (2º turno, Deltan, ministros que voltam).
06 Teste empírico: PEC 8/2021 nos 36 que já estavam lá; Alessandro Vieira, Damares e
Rogério Carvalho como contraexemplos.
07 Recomendações: alianças (quem cortejar e com que pauta), melhorias (regimento,
ordem das pautas, o que exigir de transparência do STF e do Senado), rotuladas como
juízo editorial, com o achado que contraria a tese publicado com o mesmo destaque.
08 Fichas dos 81, uma por senador, com casos, defesa, sinais e fontes.
09 Anexo: arquivamentos, absolvições, pendências eleitorais; arbitragem entre os
quatro relatórios; limites; fontes.

## 6. Template e módulos de página

Template `docs/senado_2027.template.html` com placeholders `{{NOME}}` trocados por
`scripts/senado-2027-build.py`. Módulos em `scripts/senado_2027/pagina/` (subpacote com
`__init__.py` próprio): `fixo.py` (prosa que não depende de número: aulas sobre estágios
processuais, rito do impeachment, o que K e C não são), `figuras.py` (SVG em Python com os
dados embutidos, nunca gráfico só por JS), `view.py` (hero, ranking, fichas, anexo, fontes),
`texto.py` (frases geradas a partir dos números). CSS próprio em `docs/assets/senado_2027.css`,
carregado depois de `predicao_2026.css`, `predicao_2026-responsive.css` e
`predicao_2026_ux.css`; JS só para ordenar tabela, abrir `<details>` por âncora e ficha ao
passar o ponteiro, reaproveitando `assets/predicao_2026_ui.js`.

Placeholders de bloco (cada um devolve HTML pronto): `HERO`, `AVISO`, `ORIGEM`, `REGUA`,
`MAPA_81`, `HEMICICLO`, `RANKING`, `TIPOS`, `CONTA`, `PIVOS`, `TESTE_PEC8`, `RECOMENDACOES`,
`FICHAS`, `ANEXO`, `ARBITRAGEM`, `LIMITES`, `FONTES`, `COMO_LEMOS`.
Placeholders de valor (texto curto): `DATE`, `N_SENADORES`, `N_COM_CASO`, `K_MEDIA`,
`K_MEDIANA`, `ESPERADO_PEC_FLAVIO`, `ESPERADO_IMP_FLAVIO`, `ESPERADO_PEC_LULA`,
`ESPERADO_IMP_LULA`, `P49_FLAVIO`, `P54_FLAVIO`, `P49_LULA`, `P54_LULA`, `N_ALTA`, `N_MEDIA`,
`N_BAIXA`, `N_PIVOS`, `PIVOS_NOMES`, `N_PEC8_PRESENTES`, `N_PEC8_SIM`, `N_PEC8_NAO`.
Padrão visual: frase em português corrente antes do gráfico, gráfico antes do parâmetro,
corpo em 18 px, probabilidade em palavras onde couber (`_chances()` de
`scripts/governador_2026`), parâmetros dentro de `<details class="gv-tec">`.
