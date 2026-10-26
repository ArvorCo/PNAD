# Vinhetas do telão do 2º turno (25/10/2026)

Remotion 4. Duas composições em `src/`: `Vinheta.tsx` (abertura, 61,7 s, tocada às 17h e a cada retomada da divulgação) e `Encerramento.tsx` (239,6 s, só manual: `Shift+V` no telão ou o botão "Vídeo de encerramento" no diretor).

`public/` fica fora do git: narração (`abertura.mp3`, `encerramento.mp3`, voz do Leonardo pelo ElevenLabs v4 a partir de `apuracao/data/vinheta/*.txt`), capturas do telão (`img/`, `final/`, geradas por `apuracao/scripts/qa-vinheta.ts`) e fontes. Os MP4 renderizados vão para `apuracao/public/vinheta/` e também não são versionados.

```bash
npm install
npm run typecheck && npm run lint
npm run render
npm run render:encerramento
```
