# A noite do 2º turno (apuração de 25/10/2026)

Vídeo documental de cerca de 10 minutos em Remotion, nos formatos 16:9 (1920×1080, composição
`Apuracao2tWide`) e 9:16 (1080×1920, `Apuracao2tVertical`), narrado na voz do Leonardo (ElevenLabs
v4), com a marca Arvor Intelligence, para fechar o dossiê `docs/apuracao_2T_2026.html`. Oito
capítulos e 32 cenas: abertura, a noite minuto a minuto, a projeção, entre os
dois turnos, seção por seção, pesquisas contra a urna, as urnas por dentro (logs, assinaturas e totalização paralela) e fecho. Nomes,
esquemas e posse de cada arquivo estão em `CONTRATO.md`, a fonte única.

Clonado de `video/sete_riscos/` em 25/10/2026. Nada aqui importa de lá, e os três projetos
irmãos seguem intactos. `node_modules` é um link para `../sete_riscos/node_modules` (mesmas
versões; rode `npm install` lá, não aqui).

## Estado

Pronto em 25/10/2026: roteiro e fontes (`roteiro/`), dados do dossiê (15 blocos), voz e música
(ElevenLabs v4), telas do telão e o topo do dossiê capturados, still de capa pelo mflux (os
geradores do openclaw recusaram), render 16:9 e 9:16 e capas em `out/`, kit de publicação em
`publicacao.md`. Duração 10:32 (revisão de 26/10/2026 pela TESE.md, com o capítulo dos logs das urnas).

## Reprodução, nesta ordem

```bash
python3 scripts/video-apuracao-2t-dados.py      # blocos do dossiê → src/dados/apuracao_2t.json (rode de novo a cada bloco novo)
python3 scripts/video-apuracao-2t-capturas.py   # telão (vinheta_2t) e páginas → public/midia/cap_*, src/dados/capturas.json
# roteiro/fontes.md e roteiro/roteiro.md (um bloco "## id" por cena, na ordem de src/ordem.ts)
python3 scripts/video-apuracao-2t-voz.py        # voz, música e efeitos → public/, src/dados/voz.json e musica.json
python3 scripts/video-apuracao-2t-midia.py      # clipes e stills de apoio → public/midia/, src/dados/midia.json
cd video/apuracao_2t
npm run verificar                               # portão de duração (570 a 660 s)
npm run typecheck && npm run lint               # zero erro e zero aviso
node navegador.mjs                              # extrai o Chrome Headless Shell (o Remotion não consegue aqui)
node stills.mjs Apuracao2tWide 30 400 ...       # quadros de conferência em out/stills/
npm run render                                  # out/apuracao_2t_16x9.mp4 e out/apuracao_2t_9x16.mp4
python3 scripts/video-apuracao-2t-capa.py       # capas (exige o still sala_apuracao_still)
pytest -q tests/test_video_apuracao_2t.py
```

As cenas finais (gatilhos e caminhos de dados) são ajustadas depois da voz, porque cada elemento
entra na palavra em que é dito.

## Duração

De 570 a 660 segundos (9:30 a 11:00). `npm run verificar` soma voz, respiro de 0,9 s por cena e
cauda de 3 s, imprime cada capítulo e dá `OK`, `CURTO` (abaixo de 570 s) ou `LONGO` (acima de
660 s); com voz gerada, sai com código 1 fora da faixa. Sem voz, estima pelo roteiro a 145
palavras por minuto e só informa; sem roteiro, avisa que não há o que medir. Ajusta-se cortando
ou estendendo o roteiro, nunca acelerando o áudio.

## Dados

Todo número na tela vem de `src/dados/apuracao_2t.json`, gerado por script com SHA-256 de cada
fonte. Bloco que ainda não existe no dossiê fica em `pendentes`. As cenas leem por caminho
(`src/ref.ts`), então o esquema de cada bloco é o do dossiê e o registro
(`src/cenas/registro.ts`) é ajustado junto. O registro falha no typecheck se faltar cena.

## Rótulos obrigatórios

Ditos no bloco indicado e repetidos na tela (`ROTULO` em `src/componentes/textos.ts`):

- Projeção estatística a partir do que já foi totalizado; não é resultado nem previsão de vitória.
- Totalização paralela: soma dos BUs recebidos, não projeção.
- Atraso e abstenção atípica pedem explicação, não indicam irregularidade.
- Pausa é intervalo sem versão nova publicada, não acusação.
- Atipicidade estatística não é irregularidade.
- A hipótese do autor é juízo editorial, não fato verificado.
