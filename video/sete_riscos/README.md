# Sete riscos, um fiscal (2º turno de 2026)

Vídeo de 9 a 11 minutos em Remotion, nos formatos 16:9 (1920×1080, composição `SeteRiscosWide`) e
9:16 (1080×1920, `SeteRiscosVertical`), narrado na voz do Leonardo (ElevenLabs v4), com a marca
Arvor Intelligence. Seis capítulos e 20 cenas: abertura, o fiscal e a lei, sete riscos (boca de
urna, compra de votos, transporte em massa, voto amedrontado, mesário mal-intencionado, mesário
pianista, totalização que não bate com o boletim), a hora de fechar, onde você faz diferença e o
convite. Nomes, esquemas e posse de cada arquivo estão em `CONTRATO.md`, a fonte única.

O projeto foi clonado de `video/masterclass/` em 21/10/2026. Nada aqui importa de lá.

## Reprodução, nesta ordem

```bash
python3 scripts/video-sete-riscos-dados.py      # fontes do repositório → src/dados/sete_riscos.json
# roteiro/fontes.md e roteiro/roteiro.md (um bloco "## id" por cena, na ordem de src/ordem.ts)
python3 scripts/video-sete-riscos-voz.py        # voz, música e efeitos → public/, src/dados/voz.json e musica.json
python3 scripts/video-sete-riscos-midia.py      # clipes e stills → public/midia/, src/dados/midia.json
python3 scripts/video-sete-riscos-capturas.py   # prints e gravações → public/midia/cap_*, src/dados/capturas.json
cd video/sete_riscos
npm run verificar                               # portão de duração
npm run typecheck && npm run lint               # zero erro e zero aviso
node navegador.mjs                              # extrai o Chrome Headless Shell (o Remotion não consegue aqui)
node stills.mjs SeteRiscosWide 30 400 ...       # quadros de conferência em out/stills/
npm run render                                  # out/sete_riscos_16x9.mp4 e out/sete_riscos_9x16.mp4
```

As cenas são escritas depois da voz, porque cada elemento entra na palavra em que é dito.

## Duração

De 540 a 690 segundos (9:00 a 11:30). `npm run verificar` soma voz, respiro de 0,9 s por cena e
cauda de 3 s, imprime cada capítulo e dá `OK`, `CURTO` (abaixo de 540 s) ou `LONGO` (acima de
690 s); com voz gerada, sai com código 1 fora da faixa. Sem voz, estima pelo roteiro a 145
palavras por minuto e só informa. Ajusta-se cortando ou estendendo o roteiro, nunca acelerando o
áudio.

## Dados

Todo número na tela vem de `src/dados/sete_riscos.json`, gerado por script com SHA-256 de cada
fonte. Até o script rodar, esse arquivo é cópia de `sete_riscos.placeholder.json` (mesmo
esquema, valores zerados), para o projeto compilar. Cenas ainda não desenhadas usam
`Placeholder`; as cenas `cap-*` usam `CartaoCapitulo`. O registro (`src/cenas/registro.ts` e
`registro_b.ts`) falha no typecheck se faltar cena.

## Rótulo obrigatório

Ditas em `abertura` (a primeira) e em `fecho-chamada` (as três), e na tela:

- Atipicidade estatística não é irregularidade.
- A lista é de prioridade de fiscalização, não de acusação.
- O que resolve cada item é a ata da mesa, o log da urna e a presença do fiscal.
