# Vídeo "Alguém precisa estar olhando" (fiscais do 2º turno de 2026)

Vídeo animado em Remotion, nos formatos 16:9 (1920×1080) e 9:16 (1080×1920), com a narração na
voz do Leonardo (ElevenLabs v4), os doze critérios do capítulo 13 do dossiê da apuração, uma seção
real por critério, o mapa do nível alta e as duas ações: ser fiscal (fiscaisdopl.com.br) e o
Politize sua vizinhança (brasil.arvor.co/politize).

## Reprodução, nesta ordem

```bash
python3 scripts/video-fiscais-dados.py      # fiscais.json → video/fiscais/src/dados/dados.json
python3 scripts/video-fiscais-voz.py        # roteiro.md → public/voz/*.mp3, src/dados/voz.json, public/sfx/*
cd video/fiscais && npm install
node navegador.mjs                           # extrai o Chrome Headless Shell (o Remotion não consegue aqui)
npm run typecheck && npm run lint
npm run render                               # out/fiscais_16x9.mp4 e out/fiscais_9x16.mp4
```

Conferência rápida de quadros sem renderizar tudo: `node stills.mjs FiscaisWide 300 3600 14100`
grava PNGs em `out/stills/`. `npm run studio` abre o editor do Remotion.

## Como funciona

- `roteiro/roteiro.md` é a fonte da narração: um bloco `## id` por cena, com tags de áudio entre
  colchetes no padrão de `apuracao/data/boletins/ESTILO.md`. O script de voz gera cada cena com
  `previous_text`/`next_text` e pede o alinhamento por caractere, que vira palavras com início e
  fim em `src/dados/voz.json`. A duração de cada cena no vídeo é a duração do áudio mais 0,9 s.
- As cenas sincronizam os elementos com a fala por `quadro(palavras, "texto", reserva)`
  (`src/plano.ts`): o cartão da seção entra quando o nome do município é dito, o número grande
  quando o número é dito, e assim por diante. Os gatilhos dos doze critérios ficam em
  `src/destaques.ts`.
- Todo número na tela vem de `src/dados/dados.json`, gerado pelo script de dados a partir de
  `analysis/apuracao_2026/dados/fiscais.json`. A escolha da seção exemplo de cada critério segue
  regra declarada no script (nível mais alto, depois pontuação, depois votantes, sem repetir seção
  entre critérios). `tests/test_video_fiscais.py` confere os dados, o roteiro e o manifesto.
- Um só componente (`src/Video.tsx`) atende os dois formatos; `useFormato()` diz se a composição é
  vertical e cada cena troca linhas por colunas.
- Efeitos sonoros e trilha vêm da API de sound-generation e music do ElevenLabs e só são gerados
  quando o arquivo ainda não existe em `public/sfx/`.

## Rótulo obrigatório

As três frases do capítulo 13 estão no roteiro e na tela: atipicidade estatística não é
irregularidade; a lista é de prioridade de fiscalização, não de acusação; o que resolve cada item
é a ata da mesa, o log da urna e a presença do fiscal. O roteiro não usa a palavra "fraude".
