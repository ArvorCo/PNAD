# Roteiro da narração: "Sete riscos, um fiscal"

Voz do Leonardo pelo ElevenLabs v4, uma cena por bloco `## id`, na ordem de CONTRATO seção 1.
Tags de áudio em inglês entre colchetes, no máximo uma a cada duas ou três frases. Reticências
criam pausa curta; uma CAIXA ALTA por bloco. Todo número vem de `src/dados/sete_riscos.json`;
todo fato externo vem de `roteiro/fontes.md`.

## abertura

[clears throat] [calm] Barcarena, no Pará. Uma seção rural com cento e quinze eleitores: noventa e oito vírgula dois por cento para Lula, com comparecimento de noventa e nove vírgula um. [thoughtful] No país, duas mil oitocentas e oitenta e três seções deram a Lula mais de noventa por cento. Para Flávio, cento e cinquenta e seis. Atipicidade estatística não é irregularidade. [serious] Ninguém sabe o que aconteceu lá dentro, porque só quem está na sala VÊ.
<!-- dado: exemplos.frente_1.aptos = 115 -->
<!-- dado: exemplos.frente_1.lula_pct = 98.21 -->
<!-- dado: exemplos.frente_1.comparecimento_pct = 99.13 -->
<!-- dado: lula_frente.secoes_lula_90 = 2883 -->
<!-- dado: lula_frente.secoes_flavio_90 = 156 -->

## tese

[serious] A tese cabe numa frase. O fiscal vê, anota e pede cópia. Ele não discute, não grita e não muda resultado: protege o voto de todo mundo. [short pause] Ele não precisa de arma, de gritaria nem de coragem teatral. Precisa de atenção, de papel e da lei na mão. Sete riscos, um fiscal, e só a LEI.

## cap-lei

[calm] Capítulo um. O fiscal e a lei.

## lei-poderes

[calm] Primeiro, o que a lei garante a quem chega à seção com credencial. O partido pode fiscalizar todas as fases da votação, com até dois fiscais por seção, um de cada vez, com credencial expedida pelo partido. [thoughtful] O fiscal pode protestar e impugnar durante a votação, inclusive a identidade do eleitor. No encerramento, o presidente da mesa entrega a cópia do boletim de urna a quem pedir. E o fiscal pode acompanhar a urna e o material até a junta eleitoral, por conta própria. [emphatic] Tudo isso está na lei, e nada disso depende de favor.
<!-- fonte: lei-9504-art-65-66-68 -->
<!-- fonte: codigo-eleitoral-art-131-132 -->
<!-- fonte: res-tse-23751-fiscais -->
<!-- fonte: res-tse-23751-art-165 -->

## lei-postura

[serious] Agora, a postura. Sabedoria, coragem e só a lei. O crachá leva só nome e partido. O fiscal não discute, não encosta em ninguém, anota hora e nome e pede ao presidente que registre na ata: o campo quatro ponto dois é feito para protesto e impugnação. [thoughtful] Se o presidente mandar sair, o fiscal sai, registra e comunica ao juiz eleitoral. Crime fora da seção vai ao Ministério Público Eleitoral, não à discussão na calçada. Na seção, quem decide é o presidente; fora dela, a polícia e o Ministério Público. [calm] Quem perde a calma perde a razão. Coragem é ficar. Sabedoria é não dar MOTIVO.
<!-- fonte: manual-mesario-ata -->
<!-- fonte: res-tse-23751-art-181 -->
<!-- fonte: denuncia-onde -->

## cap-riscos

[calm] Capítulo dois. Sete riscos.

## risco-boca-de-urna

[calm] Primeiro risco: boca de urna. É propaganda e aliciamento no dia da eleição, na porta do local. [serious] Em Paulista, Pernambuco, no segundo turno de dois mil e vinte, pessoas foram presas por aglomeração e boca de urna na porta de uma escola, e na mesma seção uma mesária foi detida por induzir eleitores. O desfecho não foi localizado. No primeiro turno de dois mil e vinte e quatro, o Ministério da Justiça contou mil cento e setenta ocorrências. [thoughtful] Sinal nos dados: nenhum. Voto aliciado é igual a qualquer outro na urna. A pena é detenção de seis meses a um ano. O fiscal registra de fora da seção, anota hora e local, e aciona o juiz e a polícia. Coragem é ficar. Sabedoria é não dar motivo.
<!-- dado: riscos[id=boca_urna].casos[0].ano = 2020 -->
<!-- dado: balanco_mj.1t_2024.boca_urna = 1170 -->
<!-- dado: riscos[id=boca_urna].casos[1].ano = 2024 -->
<!-- fonte: lei-9504-art-39 -->
<!-- fonte: caso-paulista-pe-2020 -->
<!-- fonte: caso-mj-1t-2024 -->

## risco-compra

[calm] Segundo risco: compra de voto. Dinheiro ou vantagem em troca do voto. O candidato que faz isso perde o registro ou o diploma, artigo quarenta e um A. [serious] Em dois mil e nove, o TSE cassou o governador do Maranhão, Jackson Lago, por cinco votos a dois. O relator viu compra em Imperatriz: um motorista preso com dezessete mil reais e tabelas de pagamento. [thoughtful] Sinal nos dados: nenhum. Em dois mil e vinte e quatro, foram quatrocentas e noventa e oito ocorrências em um dia. O fiscal anota quem, onde e quando, e avisa o juiz. Celular na cabine é proibido, artigo cento e trinta e sete da resolução. Quem prova é a testemunha, não o gráfico. Calma é ferramenta.
<!-- dado: riscos[id=compra].casos[0].ano = 2009 -->
<!-- dado: balanco_mj.1t_2024.compra = 498 -->
<!-- dado: riscos[id=compra].casos[1].ano = 2024 -->
<!-- fonte: lei-9504-art-41a -->
<!-- fonte: caso-jackson-lago-2009 -->
<!-- fonte: caso-mj-1t-2024 -->
<!-- fonte: res-tse-23751-art-137 -->

## risco-transporte

[calm] Terceiro risco: transporte de eleitores. Só a Justiça Eleitoral organiza o transporte; quem mais fornecer comete crime. [serious] Em Reserva, no Paraná, em dois mil e quatro, o filho do prefeito levou três eleitoras no carro da família, e o TSE restabeleceu a pena mínima de quatro anos. Em Anchieta, Santa Catarina, em dois mil e doze, um fiscal flagrado levando um eleitor foi absolvido: sem aliciamento provado, não há crime. [thoughtful] Sinal parcial: seção rural com comparecimento acima do padrão. Em dois mil e vinte e quatro, foram cinquenta e três veículos apreendidos. O fiscal anota placa e hora e avisa o juiz. Não aborda o motorista. Sabedoria é ver sem se meter.
<!-- dado: riscos[id=transporte].casos[0].ano = 2004 -->
<!-- dado: riscos[id=transporte].casos[1].ano = 2012 -->
<!-- dado: balanco_mj.1t_2024.veiculos_transporte = 53 -->
<!-- fonte: lei-6091-transporte -->
<!-- fonte: caso-hornung-reserva-2004 -->
<!-- fonte: caso-anchieta-sc-2012 -->
<!-- fonte: caso-mj-1t-2024 -->

## risco-medo

[serious] Quarto risco: voto sob ameaça. Facção ou milícia que intimida o eleitor. Coação é crime, artigo trezentos e um do Código Eleitoral. Em Santa Quitéria, no Ceará, o TSE manteve em dois mil e vinte e seis a cassação do prefeito e do vice por usar uma facção para intimidar apoiadores da chapa adversária, na campanha de dois mil e vinte e quatro. No Rio, o tribunal regional trocou cinquenta e três locais de votação por segurança. [thoughtful] Sinal parcial: a concentração extrema só se lê com o território. Numa seção ribeirinha de Bagre, no Pará, Lula teve noventa e sete vírgula seis por cento, com comparecimento de noventa e seis vírgula dois. O território explica; o boletim não. O fiscal não confronta: registra. Força federal, só o TSE requisita.
<!-- dado: riscos[id=medo].casos[0].ano = 2024 -->
<!-- dado: exemplos.frente_3.lula_pct = 97.58 -->
<!-- dado: exemplos.frente_3.comparecimento_pct = 96.24 -->
<!-- fonte: codigo-eleitoral-art-301 -->
<!-- fonte: caso-santa-quiteria-ce -->
<!-- fonte: caso-trerj-locais-2024 -->
<!-- fonte: codigo-eleitoral-art-23-xiv -->

## risco-mesario

[serious] Quinto risco: o mesário mal-intencionado. Quem conduz o voto de outra pessoa dentro da cabine. [calm] Em Itumbiara, Goiás, em dois mil e dezoito, o presidente de uma seção foi preso em flagrante, segundo a polícia, por conduzir o voto de uma eleitora de setenta e três anos que não pediu ajuda. Ele nega e foi liberado sob fiança. Não há condenação. [thoughtful] Sinal nos dados: nenhum. Não sobra número no boletim; só quem está na sala VÊ. O fiscal impugna na hora, artigo cento e trinta e dois, e pede ao presidente que registre na ata. Anota hora e nome. Não discute com o mesário. Coragem é ficar; sabedoria é a lei no papel.
<!-- dado: riscos[id=mesario].casos[0].ano = 2018 -->
<!-- fonte: caso-itumbiara-2018 -->
<!-- fonte: codigo-eleitoral-art-131-132 -->
<!-- fonte: manual-mesario-ata -->

## risco-pianista

[calm] Sexto risco: o mesário pianista. Quem vota no lugar de quem não veio. É crime, artigo trezentos e nove. [serious] Em Pescaria Brava, Santa Catarina, em dois mil e dezesseis, um mesário sozinho na sala votou por cinco ausentes, um morto desde dois mil e nove. Foi condenado, a seção foi anulada, e a diferença de um voto virou setenta e seis, sem trocar o vencedor. Em Macapá, a Polícia Federal investiga votos sem biometria em seção rural de dois mil e vinte e quatro. [thoughtful] Sinal parcial: comparecimento perto de cem por cento. Em Baião, no Pará, cinquenta e um de cinquenta e um eleitores votaram, e Lula teve setenta e nove vírgula seis. Isso não prova nada. O fiscal fica até o fim e confere o caderno de assinaturas contra o boletim.
<!-- dado: riscos[id=pianista].casos[0].ano = 2016 -->
<!-- dado: riscos[id=pianista].casos[1].ano = 2024 -->
<!-- dado: exemplos.baiao_pa.aptos = 51 -->
<!-- dado: exemplos.baiao_pa.votantes = 51 -->
<!-- dado: exemplos.baiao_pa.lula_pct = 79.59 -->
<!-- fonte: codigo-eleitoral-art-309 -->
<!-- fonte: caso-pescaria-brava-2016 -->
<!-- fonte: caso-doppelganger-macapa-2024 -->

## risco-totalizacao

[calm] Sétimo risco: a totalização não bater com o boletim. [serious] No Rio, em mil novecentos e oitenta e dois, o Jornal do Brasil denunciou pressão sobre a empresa que somava os mapas de apuração. A auditoria do Serpro achou a totalização mal planejada; o tribunal concluiu que os erros não foram intencionais. [thoughtful] Sinal nos dados: ele deixa, porque o boletim impresso e o publicado têm de ser iguais. Por isso o fiscal pede a cópia, lê o QR e compara com o site do TSE, artigo duzentos e sessenta e três. Divergência não se resolve na rua: vai à Justiça Eleitoral. Coragem é guardar o papel. Sabedoria é conferir sem acusar.
<!-- dado: riscos[id=totalizacao].casos[0].ano = 1982 -->
<!-- fonte: caso-proconsult-1982 -->
<!-- fonte: res-tse-23751-art-263 -->
<!-- fonte: tse-bu-qrcode -->

## cap-fechamento

[calm] Capítulo três. A hora de fechar.

## fecha-ultimos

[calm] Às dezessete horas, quem está na fila recebe senha e vota. [thoughtful] As duas últimas pessoas a votar são convidadas a acompanhar o encerramento e recebem o boletim. Uma cópia fica afixada na seção, e a via sai a quem pedir no momento do encerramento. [curious] Dica prática: chegue perto das dezessete horas, fique na fila por último, peça o boletim e fotografe o QR. [serious] Depois, o fiscal vai com a urna até a junta. O fim da votação é onde o voto vira número... e é onde a presença MAIS pesa.
<!-- fonte: tse-mesario-fila-17h -->
<!-- fonte: res-tse-23751-fiscais -->
<!-- fonte: res-tse-23751-art-165 -->

## fecha-totalizacao

[calm] Com o boletim na mão, a conferência tem endereço: brasil ponto arvor ponto co barra totalização. O aplicativo lê os QR do boletim, confere a assinatura da urna contra os certificados e grava. [thoughtful] O painel compara com o boletim que o TSE publica para a mesma seção. O rótulo é este: soma dos boletins recebidos, não projeção. Prova a transmissão e a totalização; não prova o interior da urna. [emphatic] É conferência, não é veredito.
<!-- fonte: totalizacao-arvor -->
<!-- fonte: tse-bu-qrcode -->

## cap-mapa

[calm] Capítulo quatro. Onde você faz diferença.

## mapa-fiscais

[curious] Para saber onde, abra brasil ponto arvor ponto co barra fiscais. Busque por CEP, zona ou município, escolha o raio e veja prédio por prédio. [thoughtful] Um exemplo: uma escola em Bangu, no Rio, com vinte e uma seções e cinco mil trezentos e vinte e um eleitores. Uma delas aparece em conferência do arquivo. Um fiscal para vinte e uma seções é POUCO. [calm] O mapa é lista de prioridade, não de acusação.
<!-- dado: predios[0].secoes_total = 21 -->
<!-- dado: predios[0].aptos_total = 5321 -->
<!-- dado: predios[0].por_atencao.3 = 1 -->
<!-- fonte: mapa-fiscais-arvor -->

## mapa-cadastro

[calm] Para ser fiscal, o cadastro é em fiscais do PL ponto com ponto br, até vinte e quatro de outubro, prazo do próprio site. Você precisa ter mais de dezoito anos e não pode ser mesário nem candidato. [thoughtful] A credencial é expedida pelo partido. Cadastre-se e peça a credencial ao partido.
<!-- dado: cadastro.prazo = 2026-10-24 -->
<!-- fonte: fiscaisdopl -->

## fecho-chamada

[serious] Três frases para levar. Atipicidade estatística não é irregularidade. A lista é de prioridade de fiscalização, não de acusação. O que resolve cada item é a ata da mesa, o log da urna e a presença do fiscal. [pause] [calm] Sete riscos. Um fiscal. Nenhuma arma além da lei. Daqui até o fim do segundo turno, cada seção sem olhar atento é uma seção sem testemunha. Alguém precisa estar olhando. Pode ser VOCÊ.
