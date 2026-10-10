# Politize: o jogo da conversa. Decisões (10/10/2026)

1. **Arquitetura**: HTML + CSS + JS clássicos, dados embutidos em `dados.js` (sem fetch, sem módulo), para
   abrir de `file://`, de Android, iOS e desktop. O roteiro é autorado em JSON em `analysis/politize_game/roteiro/`
   e o build `scripts/politize-game-build.py` valida contra o contrato e grava o `dados.js`. Teste reprova
   se o publicado divergir do build.
2. **Arte em SVG procedural**, não imagem gerada por IA: 34 bustos e 14 cenas em menos de 60 KB, três expressões
   por avatar (fechado, neutro, aberto) que acompanham a confiança, zero rede, zero direito autoral alheio e
   estilo único. Gerar 34 retratos no ChatGPT custaria horas e daria estilo irregular; fica como upgrade
   opcional se o Leonardo quiser (os `visual` do roteiro já servem de prompt).
3. **Nomes de perfil ajustados para sobreviver a citação hostil** (CLAUDE.md: trabalho público precisa ser
   legalmente defensável). O pedido original trazia "petista semianalfabeto" e "homem gay militante do Soros".
   Viraram `lulista_gratidao` (seu Zé da feira, fundamental incompleto, voto por gratidão, retratado com
   esperteza) e `militante_ong` (coletinho, crachá, bottons: a caricatura é da militância profissional,
   não da orientação sexual, e sem teoria sobre financiador). "Universitário que não toma banho e fuma
   maconha" ficou como `universitario_humanas` (patchouli, Che, baseado): hábito e jargão, não pobreza.
   Regra geral do contrato: caricatura de comportamento político e estilo, nunca de cor, religião,
   orientação, deficiência ou origem como alvo. O humor atinge também o nosso lado (tio do churras que
   desqualifica, tia do zap que encaminha boato perdem ponto em dobro).
4. **Mecânica**: rodada de 8 conversas com mistura fixa por campo; confiança 0 a 100; cinco fases
   (abordagem, escuta, duas objeções, fecho); fraqueza do personagem dobra o efeito negativo da tag;
   opção `grave` encerra a conversa e sempre mostra a lição com a fonte; desfecho por limiares declarados
   no NPC; público do cenário multiplica (thread no X vale três). Com a esquerda ideológica o teto é o
   nulo. Semente reproduzível na URL (`#s=`). Sem cronômetro, por acessibilidade.
5. **Conduta ilegal só como opção errada**: carona, favor, boca de urna e ameaça existem apenas como
   `grave`, com a lei na lição (Código Eleitoral art. 299; Lei 6.091/1974; Lei 9.504/1997 art. 39 § 5º).
   O build falha se alguma dessas tags aparecer sem fonte de lei ou com tipo diferente de grave.
6. **Localização**: `docs/politize_game.html` na raiz do site e `docs/politize_game/` para os arquivos do
   jogo, como pedido. Linkado do Politize (chamada abaixo das conversas por origem e no rodapé) e da home.
