# Plano da página `docs/apuracao_1o_turno_2026.html`

Gerada por `scripts/apuracao-2026-build.py` a partir dos JSONs de `analysis/apuracao_2026/dados/` e dos memorandos `.md` da mesma pasta (nunca editar o HTML gerado). Módulos em `scripts/apuracao_2026/` (`figuras.py` SVG em Python, `view.py` HTML, `texto.py` frases geradas dos números). Paleta, fontes e regras: `BRIEF.md`.

## Capítulos (ordem na página; cada um abre pelo número mais forte)
1. **Abertura**: placar final, 2º turno, a frase de um parágrafo sobre a noite; card de números (seções, votos, comparecimento). Figura: mapa do Brasil por UF (quem venceu, banda pela margem) + barras dos cinco primeiros.
2. **A noite minuto a minuto**: linha de votos acumulados por candidato (desde 17:21) e barras do que cada atualização trouxe (lotes), com as três paradas do arquivo nacional marcadas; mapa do horário em que cada UF chegou a 100%; latência de leitura por hora. Figura extra: a divergência soma das UFs × arquivo nacional entre 18:40 e 20:10.
3. **A falha do TSE**: o que o banco prova (paradas, salto de 25 mi, cópias antigas do CDN, flag `e` no 2º turno, hora local no exterior), o que o app oficial mostrava às 19:08, o que a imprensa e o TSE disseram (`noticias_noite.json`), o que o TSE não explicou. Separar fato de hipótese. Prints do telão em `docs/img/apuracao_2026/`.
4. **Nordeste, Norte e Centro-Sul**: 2026 × 2022 por região e UF (swing de Flávio contra Bolsonaro e de Lula contra Lula), capitais × interior, os 30 maiores swings municipais para cada lado, comparecimento. Figuras: barras divergentes por UF, dispersão município 2022 × 2026, mapa municipal de SP/MG/BA/PE com o swing.
5. **Exterior**: por continente e país, as maiores cidades, a hora local do TSE. Figura: mapa-múndi com bolhas (porta do telão) e barras por continente.
6. **Câmara dos Deputados**: hemiciclo das 513 cadeiras por campo (cores da casa) e por partido, cadeiras × votos por campo, 21 UFs fechadas e 6 provisórias (declarar), os mais votados. Figura: hemiciclo + barras.
7. **Senado de 2027**: hemiciclo de 81 (27 ficam em contorno, 54 novos), por campo e partido, as segundas vagas apertadas, o que 52 e 49 significam. Figura: hemiciclo (porta de `scripts/senado_2026/pagina/hemiciclo.py`).
8. **Assembleias**: SP, MG, RJ, BA, RS, PR, PE, CE, GO, SC, DF por campo; mais votados. Figura: barras empilhadas.
9. **Governadores e o 2º turno**: 20 eleitos, 7 segundos turnos, vão estadual (Tarcísio, Cleitinho, JHC, Riedel…), as linhas medidas do Datafolha de 21/09 (transferência governador × presidente), rótulo "teto endereçável". Figura: barras do vão por UF com sinal.
10. **Pesquisas × urna**: tabela ordenada pela diferença (publicado e reponderado por renda), o parágrafo "proximidade não é acerto", erro comum de 2022 como referência, a central da casa e o DLM, Senado (Brier) e governadores. Figura: pontos por instituto contra a linha da urna; a reponderação como seta.
11. **Voto útil**: terceiros 7,8% contra as pesquisas, reserva de 2º turno medida contra o que aconteceu, decomposição com a matriz Nexus, incerteza declarada. Figura: cascata.
12. **Anomalias por zona**: método (robust z + Isolation Forest), limites, mapa das 50 zonas mais anômalas com rótulo, tabela das 25, contexto de segurança e fiscalização com fontes (`contexto_seguranca.json`), a frase responsável. Figura: mapa + dispersão score × eleitorado.
13. **O caminho do 2º turno** (juízo editorial declarado): aritmética da transferência sob três hipóteses, geografia do estoque de 2022, governadores aliados, bancadas como argumento, riscos e achados contrários, dez movimentos ordenados por votos esperados.
14. **Auditoria do próprio acompanhamento**: o que o coletor é, 496 mil versões, latência, 0 bloqueios, como reproduzir (`apuracao/README.md`), limites (sem BU; proporcionais só primeiro e último snapshot por município).
15. **Fontes e reprodução**: todos os scripts, JSONs, hashes, data de geração.

## Entregáveis da página
- `docs/apuracao_1o_turno_2026.html` (sem travessão; `grep -c "—"` zero), metatags OG com `og:image` `https://brasil.arvor.co/img/og/apuracao_1o_turno_2026.png` 1200×630; card no manifesto de `scripts/social-cards.py`; link na `docs/index.html` (hub editado à mão) como item novo no topo da lista.
- Auditorias: `python3 scripts/contrast-audit.py http://localhost:4173/apuracao_1o_turno_2026.html` e `python3 scripts/render-audit.py ...` zerados; mobile sem rolagem lateral (figuras largas com `min-width` e rolagem interna, menos mapas).
- `tests/test_apuracao_2026_build.py`: o build roda sobre os JSONs, a página contém cada capítulo, nenhum travessão, figuras com área.
