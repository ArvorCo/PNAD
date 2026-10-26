# Roteiro da narração: "A noite do 2º turno"

Voz do Leonardo pelo ElevenLabs v4, uma cena por bloco `## id`, na ordem de CONTRATO seção 1.
Tags de áudio em inglês entre colchetes, no máximo uma a cada duas ou três frases; uma CAIXA ALTA
por bloco. Todo número vem de `src/dados/apuracao_2t.json`; todo fato externo vem de
`roteiro/fontes.md`. Tom: o vídeo não comemora o resultado da eleição; comemora o método, e
critica tudo, inclusive a casa.

## abertura

[serious] Domingo, vinte e cinco de outubro, dezessete horas e sete minutos. O TSE para de publicar. Nenhum arquivo novo, de nenhum tipo, por cento e catorze vírgula seis minutos. [short pause] Nesse intervalo, o nosso coletor bateu à porta sessenta e cinco mil setecentas e noventa e duas vezes. [thoughtful] Esta é a noite contada pelos dados que guardamos.
<!-- dado: linha_do_tempo.pausas.silencio_geral.ultimo_gerado_antes_brt = 17:07:09 -->
<!-- dado: linha_do_tempo.pausas.silencio_geral.minutos = 114.6 -->
<!-- dado: linha_do_tempo.pausas.silencio_geral.leituras_no_intervalo = 65792 -->

## tese

[calm] Este vídeo não comemora o resultado. Comemora método. [short pause] Na apuração, a projeção da casa apontou o vencedor com um vírgula cinquenta e oito por cento das seções e nunca mudou de lado. As pesquisas de sábado mostravam outra eleição. [serious] Entre sábado e domingo, algo mudou. Aqui está o que a urna registrou e o que falta explicar, com a conta na TELA.
<!-- dado: projecao_noite.primeiro_ponto_com_projecao.pst = 1.58 -->

## cap-noite

[calm] Capítulo um. A noite, minuto a minuto.

## noite-stf

[serious] Por volta das dezessete e três, o ministro Cristiano Zanin, do Supremo, atendeu à Reclamação cento e um mil seiscentos e setenta e três, da coligação de Lula, e prorrogou a votação até as dezenove. A Procuradoria-Geral Eleitoral tinha opinado contra. Depois, valeu só onde a seção seguia aberta. [thoughtful] O TSE avisou as seções às dezessete e quarenta e nove.
<!-- fonte: stf-rcl-101673 -->
<!-- fonte: estadao-pge -->
<!-- fonte: ab-ajuste -->
<!-- fonte: p360-17h49 -->

## noite-parada

[serious] E então, o silêncio. O último arquivo saiu às dezessete e sete; o seguinte, às dezenove e um. Em todo o nosso banco, ZERO versões nesse intervalo. [calm] Pausa é intervalo sem versão nova publicada, não acusação. O banco mostra o silêncio; a causa, o próprio TSE informou: a decisão do Supremo.
<!-- dado: linha_do_tempo.pausas.silencio_geral.primeiro_gerado_depois_brt = 19:01:44 -->
<!-- dado: linha_do_tempo.pausas.silencio_geral.versoes_geradas_dentro = 0 -->
<!-- fonte: oglobo-pausa -->

## noite-virada

[serious] Entre as dezenove e cinquenta e as vinte e vinte e cinco, Flávio esteve à frente na contagem. Chegou a cinquenta vírgula sete por cento dos votos dos dois. [thoughtful] Parecia virada. Mas, contra o próprio primeiro turno, município por município, Flávio já vinha abaixo.
<!-- dado: projecao_noite.pontos_com_flavio_a_frente_no_observado.de = 19:50 -->
<!-- dado: projecao_noite.pontos_com_flavio_a_frente_no_observado.ate = 20:25 -->
<!-- dado: projecao_noite.pontos_com_flavio_a_frente_no_observado.maximo_p_f_observado = 50.7 -->

## noite-fim

[calm] No fim, com cem por cento das seções: Lula, cinquenta e um vírgula setenta e nove por cento dos válidos, sessenta e quatro vírgula vinte e seis milhões de votos. Flávio, quarenta e oito vírgula vinte e um, cinquenta e nove vírgula oitenta e três milhões. Diferença de quatro vírgula quarenta e três milhões. [thoughtful] E o Norte terminou praticamente cinquenta a cinquenta, separado por mil e setenta e nove votos.
<!-- dado: presidente.nacional.pst = 100.0 -->
<!-- dado: presidente.nacional.pct_lula = 51.79 -->
<!-- dado: presidente.nacional.lula = 64256232 -->
<!-- dado: presidente.nacional.pct_flavio = 48.21 -->
<!-- dado: presidente.nacional.flavio = 59826041 -->
<!-- dado: presidente.nacional.margem_lula_votos = 4430191 -->
<!-- dado: presidente.regioes[0].pct_lula = 50.01 -->
<!-- dado: presidente.regioes[0].margem_lula_votos = 1079 -->

## cap-projecao

[calm] Capítulo dois. A projeção.

## proj-primeiro-ponto

[calm] Às dezenove e quinze, com um vírgula cinquenta e oito por cento das seções, a projeção deu a Flávio quarenta e sete vírgula dezenove por cento dos votos dos dois. [serious] É projeção estatística a partir do que já foi totalizado; não é resultado nem previsão de vitória. O método: cada município contra ele mesmo no primeiro turno, no mesmo estágio da contagem.
<!-- dado: projecao_noite.primeiro_ponto_com_projecao.hhmm = 19:15 -->
<!-- dado: projecao_noite.primeiro_ponto_com_projecao.pst = 1.58 -->
<!-- dado: projecao_noite.primeiro_ponto_com_projecao.p_f_projetado = 47.19 -->

## proj-serie

[thoughtful] Em quarenta pontos com projeção, o líder projetado foi Lula em todos. Erro absoluto médio de zero vírgula três nove ponto; o maior, um vírgula vinte e um. No fim, quarenta e oito vírgula vinte e um projetado e quarenta e oito vírgula vinte e um na urna. O resultado ficou dentro da faixa de noventa por cento nos quarenta pontos. [serious] O limite: no fim, a faixa ficou tão fina que acertar dentro dela não prova calibração.
<!-- dado: projecao_noite.pontos_com_projecao = 40 -->
<!-- dado: projecao_noite.erro_absoluto_pp.medio = 0.39 -->
<!-- dado: projecao_noite.erro_absoluto_pp.maximo = 1.21 -->
<!-- dado: projecao_noite.pontos[-1].p_f_projetado = 48.21 -->
<!-- dado: projecao_noite.observado_final.p_f_entre_os_dois = 48.21 -->
<!-- dado: projecao_noite.parametros.nivel_faixa = 90 -->
<!-- dado: projecao_noite.pontos_com_final_dentro_da_faixa90 = 40 -->

## proj-sem-virada

[calm] Pouco depois das vinte e uma e vinte, dissemos no ar: não há virada possível. A diferença passava de quatro milhões, e o que faltava contar não chegava a isso. [thoughtful] O mérito não é acertar uma noite. É mostrar a faixa, declarar o método antes e publicar o erro depois.
<!-- fonte: vinheta-encerramento -->

## cap-turnos

[calm] Capítulo três. Entre os dois turnos.

## turnos-swing-uf

[calm] Nos cinco mil quinhentos e setenta e um municípios completos, a parte de Flávio entre os finalistas caiu de cinquenta e um por cento para quarenta e oito vírgula dois. [serious] Caiu nas vinte e sete unidades da federação, sem exceção.
<!-- dado: comparacao_1t.n_municipios_completos = 5571 -->
<!-- dado: comparacao_1t.brasil.t1_h2h_flavio = 51.02 -->
<!-- dado: comparacao_1t.brasil.t2_h2h_flavio = 48.22 -->
<!-- dado: comparacao_1t.ufs.length = 27 -->

## turnos-transferencia

[thoughtful] Entre os turnos ficaram disponíveis catorze vírgula um milhões de votos, e Flávio ficou com vinte e seis vírgula quatro por cento do ganho. Pela estimativa ecológica, três vírgula sessenta e dois milhões que faltaram no primeiro turno voltaram. De cada cem votos a mais, entre cinquenta e seis e sessenta e três foram para Lula. Da terceira via, Flávio levou perto de trinta e dois por cento, menos do que as pesquisas mediam. [serious] É agregado, não o voto de ninguém.
<!-- dado: transferencia.contabilidade.disponiveis = 14098232 -->
<!-- dado: transferencia.contabilidade.parte_flavio_pct = 26.4 -->
<!-- dado: transferencia.resposta.voltaram_milhoes = 3.62 -->
<!-- dado: transferencia.resposta.secoes_por_100_lula = 56.17 -->
<!-- dado: transferencia.resposta.liquido_por_100_lula = 62.53 -->
<!-- dado: transferencia.resposta.terceira_flavio_pct = 32.48 -->

## turnos-abstencao

[calm] A abstenção foi de dezenove vírgula vinte e dois por cento, a menor desde dois mil e seis, segundo a CNN. [serious] Mas subiu no Amapá, oito vírgula zero seis pontos, em Roraima, seis vírgula zero três, e no Acre, cinco vírgula sessenta e cinco. [thoughtful] Abstenção atípica pede explicação; não indica irregularidade.
<!-- dado: presidente.nacional.pct_abstencao = 19.22 -->
<!-- dado: abstencao.ufs[uf=AP].delta_1t_pp = 8.06 -->
<!-- dado: abstencao.ufs[uf=RR].delta_1t_pp = 6.03 -->
<!-- dado: abstencao.ufs[uf=AC].delta_1t_pp = 5.65 -->
<!-- fonte: abstencao-2006 -->

## cap-secoes

[calm] Capítulo quatro. Seção por seção.

## secoes-encerramento

[serious] As urnas ficaram abertas até as dezenove? Lemos os quatrocentos e noventa e nove mil duzentos e sete boletins: na quase totalidade, não. Noventa e oito vírgula vinte e nove por cento dos boletins saíram até as dezessete e trinta. Quatro mil quatrocentos e sessenta e oito, zero vírgula nove por cento, foram encerrados depois das dezenove. [thoughtful] O atraso foi na transmissão: só zero vírgula três por cento chegaram antes das dezenove. Atraso pede explicação; não indica irregularidade.
<!-- dado: secoes.totais.secoes = 499207 -->
<!-- dado: secoes.prorrogacao.brasil.pct_bu_emitido_ate_1730 = 98.29 -->
<!-- dado: secoes.prorrogacao.brasil.n_apos_1900 = 4468 -->
<!-- dado: secoes.prorrogacao.brasil.pct_apos_1900 = 0.9 -->
<!-- dado: secoes.prorrogacao.brasil.pct_recebido_antes_1900 = 0.3 -->

## secoes-biometria

[calm] Biometria baixa assusta e quase sempre é cadastro. Das treze mil duzentas e vinte e oito seções com o sinal, onze mil oitocentas e oitenta e três já o tinham no primeiro turno. [thoughtful] O que pede conferência é outro caso: em Candeias, na Bahia, uma seção saltou oitenta e um vírgula cinquenta e quatro pontos sem biometria reconhecida. Só a ata e o log dizem por quê.
<!-- dado: secoes.agregados.brasil.persistencia.sem_bio_n = 13228 -->
<!-- dado: secoes.agregados.brasil.persistencia.sem_bio_ja_no_1t = 11883 -->
<!-- dado: secoes_ranking.secoes[28].municipio = Candeias -->
<!-- dado: secoes_ranking.secoes[28].salto_bio_pp = 81.54 -->

## secoes-comparecimento

[calm] O comparecimento subiu, em média, um vírgula setenta e um ponto por seção, contra ela mesma no primeiro turno. Quarenta e seis mil duzentas e quarenta e uma seções subiram cinco pontos ou mais. [serious] Nelas, a parte de Flávio andou zero vírgula dois ponto na direção de Lula, além do resto do município. É pequeno, é medido, e não identifica mecanismo.
<!-- dado: secoes.agregados.brasil.delta_comp.media = 1.71 -->
<!-- dado: secoes.agregados.brasil.sinais.delta = 46241 -->
<!-- dado: secoes_voto.sinais[sinal=delta].did_fatia_flavio_pp = -0.2 -->

## secoes-ranking

[calm] O ranking traz cem casos: as seções mais atípicas do país, com a explicação provável de cada uma. [serious] Atipicidade estatística não é irregularidade. Só a ata, o caderno e o log separam leitor, cadastro e erro de mesa.
<!-- dado: secoes_ranking.secoes.length = 100 -->

## cap-pesquisas

[calm] Capítulo cinco. As pesquisas contra a urna.

## pesq-erro

[serious] Vinte casas publicaram pesquisa na última semana. Todas puseram Flávio mais à frente do que a urna: cinco vírgula cinquenta e três pontos na diferença, em média. Dezoito tinham Flávio na frente; só duas apontaram o vencedor. [thoughtful] No primeiro turno, a distância tinha favorecido Lula, em três vírgula cinquenta e cinco. Em dois mil e vinte e dois, também, em três vírgula noventa e dois. Desta vez, o sinal virou, e virou em todas as casas ao mesmo tempo.
<!-- dado: pesquisas_vs_urna.resumo.n_casas = 20 -->
<!-- dado: pesquisas_vs_urna.resumo.publicado_validos_do_total.media = 5.53 -->
<!-- dado: pesquisas_vs_urna.resumo.flavio_a_frente_nos_validos = 18 -->
<!-- dado: pesquisas_vs_urna.resumo.acertaram_vencedor = 2 -->
<!-- dado: pesquisas_vs_urna.primeiro_turno.erro_comum_lula_menos_flavio = 3.55 -->
<!-- dado: pesquisas_vs_urna.referencia_2022.erro_comum_lula_menos_bolsonaro = 3.92 -->

## pesq-reponderacao

[serious] A régua de renda da casa afastou nove de onze casas da urna. A Média Arvor ficou a nove vírgula trinta e três pontos; a Projeção Arvor, a sete vírgula sete. [thoughtful] A leitura da casa, e é juízo editorial: as pesquisas e a régua mediram certo até o último campo, no sábado. Se mediram certo, essa distância é o tamanho do que mudou entre sábado e domingo. E a régua se afastar é o esperado se a mudança veio de quem comparece.
<!-- dado: pesquisas_vs_urna.efeito_reponderacao.afastou = 9 -->
<!-- dado: pesquisas_vs_urna.efeito_reponderacao.n = 11 -->
<!-- dado: pesquisas_vs_urna.centrais.media_arvor.erro_f_menos_l = 9.33 -->
<!-- dado: pesquisas_vs_urna.centrais.projecao_arvor.erro_f_menos_l = 7.7 -->

## pesq-hipotese

[thoughtful] O que mudou? A hipótese do autor, juízo editorial: para reproduzir a urna no simulador, a presença relativa de Flávio teria de ser treze vírgula setenta e três por cento menor que a de Lula. [serious] O que ainda falta explicar: a variação da abstenção por estado não acompanha a perda de Flávio, e a correlação entre as duas fica em zero vírgula zero dois; o aumento de comparecimento explica no máximo dois vírgula trinta e seis pontos. Se foi isso mesmo, não saberemos.
<!-- dado: hipotese_autor.presenca_necessaria_a = -13.73 -->
<!-- dado: pesquisas_vs_urna.hipoteses.contabilidade_entre_turnos.correlacao_variacao_abstencao_com_residuo = 0.02 -->
<!-- dado: pesquisas_vs_urna.hipoteses.contabilidade_entre_turnos.limite_comparecimento.parcela_maxima_explicada_pp = 2.36 -->

## cap-urnas

[calm] Capítulo seis. As urnas por dentro.

## urnas-cadencia

[serious] O log da urna registra a hora de cada voto. Lemos quatrocentos e noventa e nove mil cento e setenta e seis. Depois das dezessete horas, as urnas computaram só trinta e quatro mil trezentos e doze votos: zero vírgula zero três por cento do total. No primeiro turno, tinham sido dois vírgula oitenta e nove por cento. Depois das dezenove, onze votos, no país inteiro. [thoughtful] Entre oito e nove da manhã, dezesseis vírgula setenta e cinco por cento dos votos, contra nove vírgula quarenta e sete no primeiro turno.
<!-- dado: logs.cobertura.lidos = 499176 -->
<!-- dado: logs.cadencia.brasil_2t.computados_17_19 = 34312 -->
<!-- dado: logs.cadencia.brasil_2t.pct_17_19 = 0.03 -->
<!-- dado: logs.cadencia.amostra_1t.brasil_1t.pct_17_19 = 2.89 -->
<!-- dado: logs.cadencia.brasil_2t.computados_depois_19 = 11 -->
<!-- dado: logs.cadencia.brasil_2t.pct_primeira_hora = 16.75 -->
<!-- dado: logs.cadencia.amostra_1t.brasil_1t.pct_primeira_hora = 9.47 -->

## urnas-integridade

[calm] Em quatrocentos e noventa e nove mil cento e setenta logs, a contagem de votos é igual à do boletim. Nos seis restantes, o log tem menos registros. Todas rodaram a mesma versão do software. [thoughtful] Doze mil duzentas e setenta e uma seções tiveram o sistema religado durante a votação. Contra o primeiro turno, o voto nelas se moveu zero vírgula zero três ponto: nada além do ruído.
<!-- dado: logs.cobertura.contagem_confere = 499170 -->
<!-- dado: logs.cobertura.contagem_nao_confere.length = 6 -->
<!-- dado: logs.reinicios.secoes = 12271 -->
<!-- dado: logs.reinicios.voto[0].dif_em_dif_contra_1t.media_pp = -0.03 -->

## urnas-assinatura

[calm] Nos quatrocentos e noventa e nove mil duzentos e sete arquivos de assinatura lidos, a cadeia de certificados e a assinatura da urna conferem em todos. O registro digital do voto bate com o boletim em quatrocentos e noventa e nove mil duzentos e cinco seções, nenhuma divergente. [serious] O que pede explicação: a série da memória de resultado se repete em mil quinhentas e noventa e uma seções, quase todas no exterior e no Rio. Não prova irregularidade.
<!-- dado: metadados.turnos.2t.coerencia_vsc.cadeia_ate_a_ac.sim = 499207 -->
<!-- dado: rdv.cobertura.total.confere = 499205 -->
<!-- dado: logs.metadados.serie_mr.secoes_em_repeticao = 1591 -->

## paralela-177

[calm] E a totalização paralela por QR: cento e setenta e sete boletins enviados pelo público, de quinze estados. [emphatic] Cento e setenta e sete iguais ao TSE. [serious] É a soma dos BUs recebidos, não projeção.
<!-- dado: paralela.recebidos.bus = 177 -->
<!-- dado: paralela.recebidos.ufs = 15 -->
<!-- dado: paralela.conferencia.igual = 177 -->

## cap-fecho

[calm] Capítulo sete. Fecho.

## fecho-arvor

[calm] Este trabalho é da Arvor e da Arvor Intelligence. Dados abertos e método à vista. Conheça em arvor ponto co. Os laudos estão em brasil ponto arvor ponto co.

## fecho-chamada

[thoughtful] Se este vídeo ajudou a separar fato de hipótese, deixe o like e compartilhe com quem prefere conferir a acreditar. [calm] Para nós, a chave de ouro desta noite não é o placar. É o MÉTODO.
