# A prorrogação como peça de um plano: hipóteses adversariais e suas assinaturas nos dados

Memorando interno (26/10/2026, 03h30). Exercício de "time vermelho": supor que a prorrogação da votação até 19h foi planejada e perguntar como cada peça serviria a um resultado dirigido, que marca cada mecanismo deixaria nos dados, o que o acervo já mostra e o que ainda falta testar. Nada aqui é afirmação; é roteiro de teste. Nenhuma frase deste arquivo vai para texto público sem passar pela régua do `TESE.md` e do CLAUDE.md (fato, inferência, juízo, hipótese; nunca "fraude").

## 0. O que está documentado (fatos com fonte em `noticias_noite.json`)
- Pedido da coligação de Lula ao STF (Reclamação 101673) protocolado entre 16:23 e 16:32, alegando ônibus parados em Salvador e problemas em SP; o PL também pediu, por chuva, em 17 a 19 cidades. PGE contra às 17:01. Zanin decidiu por volta de 17:03 (16:57 a 17:03 conforme a fonte). TSE avisou as seções às 17:49; TRE-SP recebeu às 18:17 com mais de 80% das seções fechadas. Salvador: 544 ônibus parados (Procon-BA), secretário de Mobilidade preso por ordem do TRE-BA.
- TSE sem publicar nenhum arquivo entre 17:07:09 e 19:01:44 (114,6 min), com 1.225 seções (Lula 57,66%) no último arquivo antes da parada.
- Urnas: último voto mediana 17:01, p99 17:15; 99,18% dos BUs emitidos até 17:30; 0,72% das seções votaram depois das 19h (menos que no 1T). Recebimento dos BUs pelo TSE: 0,47% antes das 19h; em 12 UFs o primeiro recebimento só entre 19:09 e 19:45; RJ 20:07.
- Regiões (F entre os dois, 1T → 2T): Sudeste 56,42 → 52,76 (−3,66); Sul 65,76 → 62,58 (−3,19); Centro-Oeste 63,40 → 60,01 (−3,39); Norte 52,40 → 49,99 (−2,41); Nordeste 32,74 → 30,80 (−1,94). Comparecimento: Sudeste +2,43 pp, Sul +2,27, Centro-Oeste +1,65, Nordeste +1,79, Norte −1,82. Ou seja: a diferença encolheu mais no Sudeste e no Sul, e o salto de comparecimento foi maior lá, não no Nordeste.
- Vídeo de artistas sobre ônibus em SP e BA: ainda não está no acervo. Alegação do Leonardo: metadado da manhã, divulgação no fim da tarde. Precisa do arquivo original (ou do link da primeira publicação) para extrair data de criação, software e cadeia de republicação.

## 1. Cinco mecanismos possíveis e a marca de cada um

### H1. Prorrogação como cobertura para votos tardios ("pianista" com urna aberta)
Como seria: seções escolhidas ficam abertas até 19h; mesário habilita eleitores ausentes por ano de nascimento e vota por eles.
Assinatura: seções com último voto depois de 17:30 concentradas em zonas específicas; salto de comparecimento e de habilitação por ano de nascimento nessas seções; voto das seções tardias deslocado contra as vizinhas do mesmo município e contra a própria seção no 1T; no log, cadência de votos entre 17h e 19h e habilitações sem biometria no mesmo intervalo.
O que já se vê: na amostra, tardias são 0,72%; fatia de Flávio nas tardias +4,83 contra as vizinhas, mas diferença em diferenças −0,15 (n 45); comparecimento +5 e salto de biometria juntos em 0,19% das seções, sem deslocamento de voto (0,03). Sinal ausente na amostra.
Falta: banco completo (contagem nacional das tardias por zona), log por seção (votos por hora 17h–19h, método de habilitação por hora), e o cruzamento das tardias com o voto. É o teste mais direto e o mais barato.

### H2. Prorrogação como justificativa para a janela de silêncio da totalização (17:07–19:01)
Como seria: o alvo não é a urna, é a totalização. Duas horas sem publicação dão tempo para intervenção entre o recebimento do BU e a soma (substituição de BU, BU do sistema de apuração, reordenação), sem que o público veja versões intermediárias.
Assinatura: BU publicado diferente do BU impresso (QR da paralela) ou do RDV; BUs do tipo "sistema de apuração" (tipo_arquivo ≥ 3) acima do 1T; soma das seções diferente do arquivo de zona/UF/BR; hashes de transmissão repetidos ou reemitidos; carimbo de recebimento (dr_hr) incoerente com emissão.
O que já se vê: paralela 177 de 177 iguais (amostra pequena e autosselecionada); RDV igual ao BU em 105.571 de 110.003 conferidos (os demais ainda em conferência); conferência BU × zona passou no AC; BU de sistema de apuração 0 na amostra; o recebimento dos BUs só começou perto das 19h em 12 UFs, o que é a anomalia a explicar (retenção no TRE? fila de transmissão? política do TSE durante a prorrogação?).
Falta: conferência completa seção → zona → UF → BR com o banco inteiro (está na cadeia pós-coleta); distribuição de dr_hr por UF contra o 1T; se a ordem de recebimento se correlaciona com o voto dentro do município (um "atraso seletivo" deixaria marca); contagem nacional de tipo_arquivo ≥ 3. Se as somas fecharem e os BUs assinados pela urna baterem, a totalização fica excluída como lugar do deslocamento, e o que restou está dentro das urnas ou dos eleitores.

### H3. Prorrogação como instrumento de comparecimento diferencial (transporte, "busão")
Como seria: mobilização de última hora onde Lula é forte, com a extensão garantindo que quem chegasse tarde votasse.
Assinatura: comparecimento subindo mais no Nordeste e nas periferias, concentrado na última hora (cadência nos logs 16h–19h), abstenção caindo onde Lula é forte.
O que já se vê: contrário. A abstenção caiu mais onde Lula teve menos voto no 1T (−1,80 contra −1,23 onde teve mais); o comparecimento subiu mais no Sudeste e no Sul; no Norte caiu; correlação entre variação da abstenção e resíduo de Flávio por UF 0,02; quase nenhuma urna ficou aberta depois das 17h. Na Bahia, onde os ônibus pararam, Flávio perdeu menos terreno que a média. Mecanismo possível só antes das 17h e sem a marca esperada.
Falta: cadência por hora nos logs (parcela dos votos nas últimas duas horas, 2T contra 1T, por região), e o cruzamento com as mudanças de local.

### H4. Prorrogação e silêncio como construção de narrativa (cobertura para um resultado distante das pesquisas)
Como seria: não há intervenção em urna nem em totalização; o que se planeja é a explicação pública. A extensão pedida com vídeo e petição prontos, o silêncio de duas horas e a ordem dos lotes (Lula 57,66% nas primeiras 1.225 seções; Flávio à frente de 19:45 a 20:23; virada depois) produzem a história "comparecimento recorde virou a eleição", que absorve um deslocamento de 5,5 pontos contra todas as pesquisas.
Assinatura: pedido e peças de comunicação preparados antes do fato que os justifica (metadado do vídeo, hora do protocolo contra hora dos ônibus parados), extensão nacional para um problema local, retenção da divulgação sem justificativa técnica publicada.
O que já se vê: cronologia compatível com preparo (petição às 16:23/16:32; decisão 17:03; aviso às seções só às 17:49, quando 80% já tinham fechado; PGE contra), mas isso prova coordenação de comunicação e jurídica, não fraude de voto. Nunca escrever além disso.
Falta: o vídeo e seus metadados; a íntegra da Reclamação 101673 e dos anexos (quem assinou, hora, quais provas); a justificativa do TSE para parar a divulgação (pedir por LAI).

### H5. Software e metadados da urna (urna religada, reinício, carga, versão)
Como seria: intervenção na urna antes ou durante a votação, deixando marca no log (reinício no meio da votação, carga posterior, versão diferente) ou nos metadados (serial, código de carga, hash do sistema, mídia, certificado) repetidos ou incoerentes.
Assinatura: reinício durante a votação com mudança de cadência de voto; carga depois da abertura; versão de software fora do padrão; ID/serial do log diferente do BU; mesmo código de carga ou mesmo hash de sistema em urnas que não deveriam compartilhar; certificado de hardware do `.vsc` repetido.
O que já se vê: "Problema ao desmontar a MR" antes da zerésima em 2.198 de 2.270 seções do AC (rotina da urna religada com a carga de setembro; vira contagem à parte); IDs repetidos no 2T 0; ID do BU presente no log em 100%; carga posterior ao primeiro voto 2 no 1T (reservas); 2.074 seções trocaram de urna sem efeito no voto (+0,05 pp, IC inclui zero).
Falta (pedido do Leonardo, 26/10): análise de TODOS os metadados da urna por seção, procurando repetição e incoerência: serial/ID (BU e log), código de carga, versão do software e hash do sistema no log, mídia de carga, chave/certificado de hardware do `.vsc`, data/hora de carga e de zerésima; comparar com o 1T e com o que o TSE declara como esperado (uma carga por urna, um certificado por urna). Entra como sinal no escore por seção se houver repetição fora das explicações legítimas.

## 2. O discriminador que decide entre "mudança real" e "rig"
Um deslocamento uniforme de 3 pontos em todas as 27 UFs com a geografia preservada (resíduo 0,75) é compatível com duas coisas: (a) mudança real e nacional de última hora entre quem compareceu, ou (b) deslocamento aplicado de forma uniforme. O que separa as duas:
1. Os BUs assinados pelas urnas (QR da paralela, RDV, `.vsc`) somam exatamente os arquivos publicados? Se sim, (b) teria de acontecer dentro das urnas, não na totalização.
2. Dentro das urnas, o deslocamento aparece igual em todo tipo de seção (modelo, tamanho, biometria, horário, urna trocada ou não)? Um rig em software deixaria heterogeneidade por modelo ou por versão; uma mudança de eleitores deixa heterogeneidade por perfil de eleitorado. Os cruzamentos por modelo e por versão são o teste.
3. A cadência por hora (logs) mostra o 2T com a mesma forma do 1T? Uma inserção de votos deixaria rajadas ou janelas sem biometria.
4. A abstenção caiu mais nos lugares em que Flávio é forte e Flávio perdeu mais fatia justamente no Sudeste e no Sul: quem compareceu a mais no Sudeste votou menos em Flávio do que a média da região no 1T, ou a terceira via do Sudeste (9% dos válidos) foi menos para Flávio do que as pesquisas mediram. Os dois são testáveis por seção com o banco completo.

## 3. Ordem de testes (fase 2)
1. Conferência completa seção → zona → UF → BR, RDV × BU, paralela × BU (H2).
2. Tardias, cadência 17h–19h, habilitação por hora (logs) (H1, H3).
3. Metadados da urna: repetição e incoerência (H5).
4. Deslocamento por modelo, versão, tamanho, biometria, urna trocada (discriminador 2).
5. Vídeo e Reclamação: metadados e cronologia (H4).
