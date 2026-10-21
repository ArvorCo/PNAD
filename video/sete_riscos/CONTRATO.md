# Contrato do vídeo "Sete riscos, um fiscal" (video/sete_riscos)

Vídeo de 9 a 11 minutos (portão 540 a 690 s), 16:9 e 9:16, narrado na voz do Leonardo
(ElevenLabs v4 com tags de áudio), marca Arvor Intelligence. Projeto Remotion clonado de
`video/masterclass/` em 21/10/2026: mesmo motor (`plano.ts`, `Palco`, `Clipe`, `Still`, `HUD`,
`Legenda`, `Trilha`), mesma paleta (`tema.ts`), mesmos efeitos (`public/sfx`, já copiados) e os
mesmos clipes e capturas já existentes (`public/midia`, copiados por hard link). A masterclass
segue intocada: nada aqui importa de lá e o teste dela continua valendo.

Este arquivo é a fonte única dos nomes, esquemas e posse de arquivos. Quem precisar mudar um
esquema muda aqui primeiro. Pedido do Leonardo (21/10/2026): explicar sete riscos ao voto no dia
da eleição (boca de urna, compra de votos, transporte em massa, voto amedrontado por criminosos,
mesário mal-intencionado, mesário pianista e totalização que não bate com o boletim), cada um
com caso real documentado e com o que o fiscal faz, "com sabedoria, coragem e contando apenas
com a lei"; o direito dos dois últimos eleitores de acompanhar o fechamento e receber o boletim;
o app de totalização; o mapa de fiscais e o cadastro do PL; seções reais com Lula na frente para
motivar a fiscalização; educativo, didático e sucinto, com a qualidade da masterclass.

## 1. Ordem das cenas (`src/ordem.ts`, `roteiro/roteiro.md`)

Um bloco `## id` por cena no roteiro, nesta ordem exata. Cartões `cap-*` são cenas narradas
curtas (3 a 5 s: "Capítulo dois. Sete riscos.").

| capítulo (id, número, título, cor) | cenas |
|---|---|
| `abertura` (0, "Abertura", `tealClaro`) | `abertura`, `tese` |
| `lei` (1, "O fiscal e a lei", `ouro`) | `cap-lei`, `lei-poderes`, `lei-postura` |
| `riscos` (2, "Sete riscos", `alta`) | `cap-riscos`, `risco-boca-de-urna`, `risco-compra`, `risco-transporte`, `risco-medo`, `risco-mesario`, `risco-pianista`, `risco-totalizacao` |
| `fechamento` (3, "A hora de fechar", `flavio`) | `cap-fechamento`, `fecha-ultimos`, `fecha-totalizacao` |
| `mapa` (4, "Onde você faz diferença", `teal`) | `cap-mapa`, `mapa-fiscais`, `mapa-cadastro` |
| `fecho` (5, "Convite", `tealClaro`) | `fecho-chamada` |

20 cenas. Cada cena `risco-*` segue o mesmo arco, nesta ordem e com a mesma duração aproximada
(40 a 55 s): **o que é** (uma frase) → **caso real** (nome do caso, ano, lugar, desfecho, com o
print da matéria na tela) → **sinal nos dados** (deixa, parcial ou nenhum; quando há seção real,
ela aparece) → **o que o fiscal faz** (dois ou três verbos, com a lei ao lado). A cena termina
com o cartão "o que o fiscal faz" fixo na tela.

## 2. Roteiro (`roteiro/roteiro.md`)

- Cabeçalho livre, depois um `## id` por cena. Tags em inglês entre colchetes (`[calm]`,
  `[serious]`, `[thoughtful]`, `[curious]`, `[emphatic]`, `[short pause]`, `[pause]`,
  `[slowly]`), no máximo uma a cada duas ou três frases.
- Sem travessão (o traço longo), sem a palavra "fraude" (nem em paráfrase: "roubo de eleição",
  "eleição roubada"), sem hashtag, sem emoji. "Risco", "crime eleitoral", "irregularidade" e o
  nome de cada cenário são as palavras.
- Números por extenso na narração (nenhum algarismo nas linhas narradas); uma CAIXA ALTA por
  bloco. "Eleitorado de X", nunca "eleitores dele". Nunca "o fiscal não pode ser expulso".
- Todo número narrado leva, dentro do bloco, um comentário HTML
  `<!-- dado: <caminho.no.sete_riscos.json> = <valor como aparece no JSON> -->` (um por
  número). O teste resolve o caminho (pontos para objetos, `[i]` para listas, `[campo=valor]`
  para achar um item numa lista) e exige que o valor por extenso apareça no bloco.
- Fatos externos (lei, caso, site, prazo) só entram se estiverem em `roteiro/fontes.md` com URL,
  data de acesso e trecho. Marcar `<!-- fonte: <id em fontes.md> -->` no bloco.
- Alvo: 1.350 a 1.650 palavras narradas (cerca de 145 palavras por minuto no v4), para 9 a 11
  minutos com o respiro de 0,9 s por cena e a cauda de 3 s.
- Três frases da casa: "Atipicidade estatística não é irregularidade." "A lista é de prioridade
  de fiscalização, não de acusação." "O que resolve cada item é a ata da mesa, o log da urna e a
  presença do fiscal." Faladas em `abertura` (a primeira) e em `fecho-chamada` (as três).
- Postura do fiscal (dita em `lei-postura` e repetida em cada risco com outras palavras): não
  discute, não grita, não encosta em ninguém; anota hora, nome e o que viu; pede ao presidente
  que registre na ata; impugna quando a lei permite; chama o juiz eleitoral; se for mandado
  sair, sai e registra. Coragem é ficar até o boletim; sabedoria é não dar motivo.
- URLs faladas: "fiscais do PL ponto com ponto br", "brasil ponto arvor ponto co barra
  totalização", "brasil ponto arvor ponto co barra fiscais".
- Seções com Lula na frente entram como motivação, sempre com o rótulo: a atipicidade não prova
  nada; prova quem está na sala.

## 3. `src/dados/sete_riscos.json` (gerado por `scripts/video-sete-riscos-dados.py`)

Nada digitado à mão. Fontes: `analysis/apuracao_2026/fontes_fiscais.json` (cenários, casos,
base legal, fontes), `analysis/apuracao_2026/dados/presidente.json` (urna),
`docs/assets/fiscais_mapa/indice.json` e `uf/<UF>.json` (seções, com `colunas_secoes`),
`analysis/apuracao_2026/dados/fiscais.json` (quando a seção está no capítulo 13),
`apuracao/public/geo/br_uf.geojson` (mapa), `totalizacao/tests/fixtures/exemplos_tse_2026.json`.
`fontes` guarda o SHA-256 de cada arquivo lido. Percentuais com duas casas.

```jsonc
{
  "gerado_em": "2026-10-21T...",
  "fontes": { "analysis/apuracao_2026/fontes_fiscais.json": "sha256..." },
  "urna": { "flavio_pct": 47.03, "lula_pct": 45.16, "diferenca_pp": 1.87, "diferenca_votos": 2224965,
            "secoes": 499248, "eleitores": 158745502, "comparecimento_pct": 78.92 },
  "riscos": [                                   // exatamente 7, nesta ordem, id = cena sem "risco-"
    { "id": "boca_urna", "cena": "risco-boca-de-urna", "nome": "Boca de urna", "familia": "entorno",
      "o_que_e": "...", "como_aparece": "...", "sinal": "nenhum" | "parcial" | "deixa",
      "sinal_texto": "...", "confere": "...",
      "lei": [ { "id": "l9504_39_p5", "norma": "Lei nº 9.504/1997", "dispositivo": "art. 39, § 5º, II",
                 "resumo": "...", "pena": "detenção de 6 meses a 1 ano e multa" | null } ],
      "casos": [ { "id": "paulista_pe_2020", "ano": 2020, "titulo": "...", "local": "PE / Paulista",
                   "instancia": "imprensa", "resultado_curto": "...", "rotulo_curto": "...",
                   "fonte": { "id": "dol_paulista_2020", "url": "https://...", "veiculo": "...",
                              "data": "2020-11-29", "titulo": "..." } } ],
      "numeros": { "mj_1t_2024": 1170 }        // só o que o roteiro cita; chave = id do caso do MJ
    }
  ],
  "balanco_mj": { "1t_2024": { "boca_urna": 1170, "compra": 498, "veiculos_transporte": 53,
                               "presos": 536, "apreendido_reais": 638000, "fonte_caso": "mj_1t_2024" },
                  "1t_2022": { "boca_urna": 456, "compra": 95, "transporte": 57, "presos": 352,
                               "crimes": 1378, "fonte_caso": "mj_1t_2022" } },
  "lei_fiscal": [ { "id": "fiscalizar", "texto": "Fiscalizar todas as fases da votação e da apuração",
                    "referencia": "Lei 9.504/1997, art. 66" }, ... ],            // 6 itens, ver abaixo
  "fechamento": [ { "id": "senhas", "texto": "...", "referencia": "Res. TSE 23.751/2026, art. 160, § 2º" }, ... ],
  "exemplos": { "<chave>": { "uf": "AM", "municipio": "Tabatinga", "zona": 36, "secao": 30, "local": "...",
                             "bairro": "...", "aptos": 386, "votantes": 360, "comparecimento_pct": 93.26,
                             "lula_pct": 94.05, "flavio_pct": 3.27, "nivel": "media" | null,
                             "criterios": ["a"], "explicacao": "..." | null, "logs": [...], "atencao": 2,
                             "o_que_conferir": "..." } },
  "lula_frente": { "secoes_lula_90": 0, "secoes_lula_80_comp_95": 0, "secoes_flavio_90": 78,
                   "lista": [ { "uf", "municipio", "zona", "secao", "aptos", "votantes",
                                "comparecimento_pct", "lula_pct", "flavio_pct", "nivel", "criterios",
                                "explicacao" } ] },                                   // até 12 itens
  "predios": [ { "local_id": "RJ-60011-233-1414", "uf": "RJ", "municipio": "Rio de Janeiro", "zona": 233,
                 "local": "ESCOLA MUNICIPAL GETÚLIO VARGAS", "bairro": "BANGU", "secoes_total": 21,
                 "aptos_total": 5321, "lula_pct": 0, "flavio_pct": 0,
                 "por_atencao": { "0": 5, "1": 6, "2": 0, "3": 1 } } ],
  "sinalizadas": { "secoes": 13045, "locais": 10174, "alta": 82, "media": 1230, "baixa": 11733 },
  "logs": { "processados": 499176, "atencao": { "0": 72082, "1": 87896, "2": 8250, "3": 1918 } },
  "mapa": { "view": 1000, "ufs": [ { "uf": "RJ", "d": "M..." } ] },
  "totalizacao": { "exemplos_oficiais": 10 },
  "cadastro": { "site": "fiscaisdopl.com.br", "prazo": "2026-10-24", "fonte": "fontes.md#fiscaisdopl" }
}
```

Riscos e casos obrigatórios (ids de `fontes_fiscais.json`), nesta ordem:

| risco `id` | cenário em `fontes_fiscais` | casos (primeiro = principal) | lei (ids de `base_legal`) |
|---|---|---|---|
| `boca_urna` | `boca_urna` | `paulista_pe_2020`, `mj_1t_2024` | `l9504_39_p5`, `l9504_39a` |
| `compra` | `compra` | `jackson_lago_2009`, `mj_1t_2024` | `l9504_41a`, `ce_299` |
| `transporte` | `transporte` | `hornung_reserva_2004`, `anchieta_sc_2012`, `mj_1t_2024` | `l6091_11`, `l6091_5` |
| `medo` | `medo` | `santa_quiteria_ce_faccao_2024`, `trerj_locais_votacao_milicia_2024` | `ce_301`, `ce_23_xiv` |
| `mesario` | `mesario` | `itumbiara_2018`, `paulista_pe_2020` | `ce_309`, `ce_132` |
| `pianista` | `pianista` | `pescaria_brava_2016`, `doppelganger_macapa_2024` | `ce_309`, `res_23751_senhas` |
| `totalizacao` | `apuracao_papel` | `proconsult_rj_1982`, `rj_1994_proporcional_anulada` | `l9504_68`, `res_23751_bu`, `l9504_66` |

Cada caso leva **uma** fonte (`fonte`), a primeira da lista `fontes` do caso que tenha URL; o
script falha se o caso não existir ou não tiver fonte. Se um id de `base_legal` não existir, o
script falha com o id.

`lei_fiscal` (6 itens, ids fixos): `fiscalizar` (Lei 9.504, art. 66), `dois` (Lei 9.504, art. 65,
§ 4º; Res. 23.751, art. 175, § 1º), `credencial` (Lei 9.504, art. 65, § 2º; Res. 23.751, art. 175,
§ 8º), `impugnar` (Código Eleitoral, art. 132; Res. 23.751, art. 176), `copia` (Lei 9.504, art. 68,
§ 1º; Res. 23.751, art. 127, XV), `ate_a_junta` (Res. 23.751, art. 165). Os textos vêm de
`base_legal` quando o id existe lá; os de resolução sem entrada ficam declarados no script com o
artigo ao lado, conferidos por `roteiro/fontes.md`.

`fechamento` (5 itens): `senhas` (art. 160, § 2º), `ultimos_dois` (art. 160, § 1º), `bu_afixado`
(art. 127, IX), `copia_no_encerramento` (art. 127, XV), `comparar_depois` (art. 263).

Chaves obrigatórias de `exemplos` (mesma regra de leitura da masterclass: seção pelo mapa de
fiscais, completada pelo capítulo 13): `tabatinga_am` (AM z36 s30), `baiao_pa` (PA z35 s238),
`puc_sp` (SP z1 s257), `sao_joao_missoes_mg` (MG z166 s267), `marau_rs` (RS z62 s15),
`porto_acre_ac` (AC z1 s621), mais `lula_frente.lista[0..2]` repetidas como `frente_1`,
`frente_2`, `frente_3`. `lula_frente.lista`: seções com `lula_pct >= 80`, `comparecimento_pct >= 95`,
`aptos >= 100`, excluindo explicação de aldeia, presídio, trânsito e exterior, ordenadas por nível
(alta, media, baixa, null) e depois por `lula_pct`; `secoes_lula_90` conta as seções do país com
`lula_pct >= 90` e `aptos >= 100` sem essas explicações, e `secoes_flavio_90` o mesmo para Flávio.
`predios`: `RJ-60011-233-1414` (Bangu).

## 4. Mídia (`midia/manifesto.json`, `midia/cache.json`, `src/dados/midia.json`)

Mesmo esquema e mesmo script da masterclass, copiado para `scripts/video-sete-riscos-midia.py`
(raiz `video/sete_riscos`). Itens **reaproveitados** (já em `public/midia`, hard link; entram no
manifesto com `cache` `origem: "manual"`, sem regerar): `fila_secao`, `urna_mesa_lacre`,
`boletim_impressora`, `maos_boletim_porta`, `fiscal_cadeira`, `escola_bangu_aerea`,
`rio_amazonia_escola`, `qr_celular`, `atas_mesa_lampada`, `teclado_urna_macro`, `secao_vazia`,
`boletim_porta`, `mapa_fundo_textura`.

Itens **novos** (vídeo de 8 s, 16x9 e 9x16; prompts em inglês, documental, sem rosto
reconhecível, sem bandeira, sem cor partidária, sem texto legível, sem logotipo, luz natural,
câmera lenta): `santinhos_calcada` (santinhos espalhados na calçada ao amanhecer, porta de
escola), `van_eleitores` (van parada numa rua de terra, pessoas descendo em grupo, vista de
longe), `envelope_mao` (mão entregando envelope a outra mão, foco raso, abstrato), `viela_noite`
(viela estreita à noite, luz amarela, câmera parada), `cabine_mesario` (cabine de votação vista
da mesa, cadeira vazia, sombra de uma pessoa), `caderno_assinatura` (caneta assinando um caderno
de folhas, macro), `fita_impressora_antiga` (impressora matricial e fita de papel, anos oitenta),
`entardecer_escola` (fachada de escola ao entardecer, última fila). Stills (Ken Burns, 2K):
`ata_mesa_still` (formulário em branco sobre mesa, caneta), `rua_escola_amanhecer_still`.
Provedores: `openclaw infer video|image generate` primeiro; se recusarem, still local por
mflux (`~/arvor/thumbnailer`, FLUX2 Klein) com clipe por `zoompan` no ffmpeg, como na masterclass;
o que sobrar fica `manual` e `--faltando` imprime o prompt para o Leonardo gerar no CapCut.

## 5. Capturas (`capturas/roteiro.json`, `src/dados/capturas.json`)

Mesmo esquema e mecanismo da masterclass, em `scripts/video-sete-riscos-capturas.py` (raiz
`video/sete_riscos`). **Reaproveitadas** (hard link já feito; o script só as registra em
`capturas.json` lendo a duração do arquivo): `totalizacao_ler`, `totalizacao_conferir`,
`totalizacao_painel`, `mapa_busca_rj`, `mapa_predio_rj`, `mapa_zoom`, `politize_bangu`.

**Novas, prints das matérias** (still por caso, `cap_materia_<caso>_<fmt>.png`, 16x9 em
1920×1080 e 9x16 em 1080×1920 DSF 2, página rolada até o título, com a barra de endereço
desenhada pelo componente `Navegador`, não pela captura): `paulista_pe_2020`, `jackson_lago_2009`,
`hornung_reserva_2004`, `anchieta_sc_2012`, `santa_quiteria_ce_faccao_2024`,
`trerj_locais_votacao_milicia_2024`, `itumbiara_2018`, `pescaria_brava_2016`,
`doppelganger_macapa_2024`, `proconsult_rj_1982`, `mj_1t_2024`. URL = `fonte.url` do caso no JSON
da seção 3. Site que bloqueia o Playwright: tentar `web.archive.org` com a mesma URL; se nada
vier, registrar `"falhou": "<motivo>"` em `capturas.json` e seguir. Nunca inventar print.
Também `cap_fiscaisdopl` (still da página de cadastro, sem preencher nada) e `cap_mapa_cep`
(busca no mapa de fiscais por um CEP de Bangu, raio 2 km).

## 6. Voz, música e efeitos (`scripts/video-sete-riscos-voz.py`, núcleo em `scripts/video_voz.py`)

- `public/voz/<id>.mp3`, `public/voz/<id>.palavras.json`, `src/dados/voz.json`.
- Música: uma faixa por capítulo em `public/musica/<capitulo>.mp3` (ElevenLabs `/v1/music`,
  `music_length_ms` = extensão do capítulo + 12 s, `force_instrumental`), normalizada a −23 LUFS;
  `src/dados/musica.json`. Prompts por capítulo: abertura e fecho (cordas suaves, esperança),
  lei (piano e pulso leve), riscos (tensão contida, percussão seca, sem drama), fechamento
  (calor, resolução), mapa (eletrônico leve, mapa se desenhando).
- Efeitos: os 17 já em `public/sfx`. Novos, se o `/v1/sound-generation` deixar: `sirene_longe`
  (sirene distante, 2 s), `passos` (passos em corredor, 2 s), `caneta` (caneta no papel, 1 s).

## 7. Cenas (`src/cenas/`, `src/cenas/registro.ts` e `registro_b.ts`)

- `registro.ts` cobre os capítulos 0 a 2 (abertura, lei, riscos); `registro_b.ts` cobre 3 a 5
  (fechamento, mapa, fecho), mesclado por spread, como na masterclass.
- Componente **`Risco`** (`src/componentes/Risco.tsx`), compartilhado pelas sete cenas de risco:
  cabeçalho com número do risco (1 de 7) e nome; painel "o que é"; cartão do caso com o print da
  matéria (`Navegador` + still `cap_materia_<caso>`), ano, lugar e desfecho; faixa "sinal nos
  dados" (chip `deixa` verde, `parcial` ouro, `nenhum` vermelho) com a seção real quando houver;
  cartão de lei (`Lei`) e cartão "o que o fiscal faz" que fica na tela. 16:9 em duas colunas;
  9:16 empilhado com o print ocupando a metade superior.
- Cada cena `risco-*` é um arquivo próprio (`RiscoBocaDeUrna.tsx` etc.) que só escolhe o risco e
  os gatilhos. Cenas de seção real reutilizam `CartaoSecao` e `GradeSecoes`.
- Gatilhos: nome → [palavra, reserva em segundos]; busca sequencial, como na masterclass.

## 8. Posse de arquivos (fase paralela)

| Agente | Escreve | Não toca |
|---|---|---|
| esqueleto (Opus) | `src/ordem.ts`, `capitulos.ts`, `tipos.ts`, `dados.ts`, `Root.tsx`, `verificar.ts` (portão 540 a 690), `cenas/registro*.ts` com `Placeholder`, `package.json` (nomes `SeteRiscosWide`/`SeteRiscosVertical`, saídas `out/sete_riscos_*.mp4`), `README.md`, `src/dados/masterclass.placeholder.json` → `sete_riscos.placeholder.json` | `src/dados/sete_riscos.json`, `roteiro/`, `midia/`, `capturas/`, `public/`, `scripts/` |
| dados (Opus) | `scripts/video-sete-riscos-dados.py`, `tests/test_video_sete_riscos.py`, `src/dados/sete_riscos.json` | resto |
| mídia (Opus) | `scripts/video-sete-riscos-midia.py`, `midia/*`, `public/midia/<novos>`, `src/dados/midia.json` | `cap_*` |
| capturas (Opus) | `scripts/video-sete-riscos-capturas.py`, `capturas/*`, `public/midia/cap_*`, `src/dados/capturas.json` | resto |
| fontes (Sonnet) | `roteiro/fontes.md` | resto |
| roteiro (Sonnet, depois de dados e fontes) | `roteiro/roteiro.md` | resto |
| cenas A (Opus, depois da voz) | `src/componentes/Risco.tsx`, cenas e registro dos capítulos 0 a 2 | capítulos 3 a 5 |
| cenas B (Opus, depois da voz) | cenas e registro dos capítulos 3 a 5, `capa/` | capítulos 0 a 2 |

Ninguém commita. Ninguém usa o navegador embutido (compartilhado): capturas via Playwright em
Python. Lint zero (`ruff`, `black`, `eslint`), typecheck zero. Scripts em Python: `kebab-case`,
PEP 8, `ruff` e `black` do `pyproject.toml`. Nada de 2026 entra como caso de risco (regra do
capítulo 13); 2026 só aparece como data de decisão de caso anterior.
