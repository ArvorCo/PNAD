# Roteiro ElevenLabs dos boletins (padrão desde 04/10/2026, 18h)

Modelo `eleven_v4` (clone profissional), estabilidade 0,4, estilo 0,3. Tags de áudio em inglês entre colchetes,
no ponto em que a entrega muda, no máximo uma a cada duas ou três frases (narração, não teatro):
`[serious]`, `[calm]`, `[thoughtful]`, `[curious]`, `[emphatic]`, `[excited]` (só em virada ou fechamento),
`[pause]`, `[short pause]`, `[slowly]` (para o placar), `[sighs]` (ressalva), `[clears throat]` (abertura, uma vez).
Reticências criam pausa curta; quebra de linha é um respiro maior; CAIXA ALTA dá ênfase a UM número por bloco.
Números por extenso quando a locução ganha ("cinquenta vírgula sete por cento", "quatro milhões e cem mil").
Sem travessão, sem hashtag, sem adjetivo decorativo. Abertura com hora; fecho com a leitura de analista.
Entre 500 e 600 palavras (3 a 4 minutos no v4, que fala pausado; 788 palavras deram 5 min 17 s). Arquivo: data/boletins/HHMM.txt, depois scripts/boletim-falar.sh (API direta por parágrafo, ffmpeg concat, afplay). Nunca o sag para boletins longos.

## Regras de leitura (desde 21:15 de 04/10)
- Senado: cada UF elege DOIS senadores; os dois mais votados entram, não disputam entre si. Dizer "os dois prováveis eleitos são X e Y" e, quando `segunda_vaga_apertada`, quem ameaça a segunda vaga e por quantos pontos. Nunca "X lidera a disputa contra Y" quando os dois estão nas duas vagas.
- Desde 22:40 de 04/10: NÃO falar de vão estadual, puxar voto ou transferência. O bloco estratégico é o tamanho das bancadas (JSON BANCADAS): Câmara por espectro e por partido, Senado de 2027, assembleias dos principais estados, governadores eleitos e segundos turnos, e o que isso significa para governabilidade.
- Governadores: separar "eleito no primeiro turno" (TSE marca) de "acima de cinquenta por cento com apuração parcial" e de "vai ao segundo turno".

## Fase final (desde 22:15 de 04/10, apuração acima de 99%)
- Não falar mais de atraso de leitura, arquivo atrasado, CDN ou cópia antiga. O assunto é resultado e o que ele significa.
- Fechar cada boletim com o quadro que se consolida: segundo turno presidencial com os dois nomes e a distância; governadores eleitos no primeiro turno (só os que o TSE marcou) e os pares do segundo turno; bancadas em formação.
