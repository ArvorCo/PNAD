"""Posts da thread dos fiscais: modelos com campos ``{chave}``, nunca algarismo solto.

Cada post: rótulo, tom, título, métrica, legenda da métrica, figura, fonte e
parágrafos. ``thread_base.digitos_soltos`` reprova algarismo fora dos campos; a
referência legal (artigo, lei, pena) também vem de campo, lida de
``fontes_fiscais.json``.
"""

from __future__ import annotations

from . import fthread_fig as G

KIT = [
    (
        "Chegar antes da abertura",
        "credencial, documento com foto, celular carregado, o print do local",
    ),
    ("Assistir à zerésima e assinar", "a prova impressa de que a urna começou vazia"),
    (
        "Conferir lacres e o número da urna",
        "e anotar na ata qualquer troca, com hora e motivo",
    ),
    (
        "Ficar na sala e anotar ocorrências",
        "liberação sem digital, ajuda na cabine, constrangimento",
    ),
    (
        "Olhar o entorno sem confrontar",
        "boca de urna, transporte, compra: filmar de fora, placa e hora",
    ),
    ("Fechamento e fila", "a hora em que a fila fechou e quem estava nela"),
    (
        "Boletim impresso e QR code",
        "pedir a via, fotografar e comparar com o publicado",
    ),
    (
        "Território de risco",
        "validar com a PM e o TRE local antes de ir; ninguém vai sozinho",
    ),
    (
        "Reportar no mesmo dia",
        "presidente da mesa, juiz eleitoral, MPE, polícia de plantão",
    ),
]

POSTS: list[dict] = [
    {
        "tag": "A lista",
        "tom": "flavio",
        "titulo": "{n_secoes} seções para conferir no 2º turno. Prioridade, não acusação.",
        "metrica": "{n_secoes}",
        "metrica_rot": "seções atípicas em {n_locais} locais de votação",
        "fig": G.fig_niveis,
        "fonte": "fiscais.json, boletins de urna do 1º turno publicados pelo TSE",
        "texto": [
            "O dossiê da apuração tem um capítulo com uma pergunta prática: se o PL tiver gente para pôr fiscal de partido numa parte das seções do 2º turno, onde essa gente rende mais? A resposta é uma lista de {n_secoes} seções, {pct_secoes} das {n_universo} seções com boletim publicado, em {n_locais} locais de votação, com endereço, coordenada e o motivo de cada uma estar ali.",
            "A lista sai de {n_criterios} critérios lidos nos boletins de urna do 1º turno: voto muito diferente do resto da zona, encerramento tardio, urna de reserva, boletim recebido de madrugada, brancos e nulos fora do padrão, variação fora da faixa desde 2022, entre outros. Cada critério tem peso declarado. A soma separa três níveis: alta, com pontuação {corte_alta} ou mais e nenhuma explicação comum no cadastro; média, com {corte_media} ou mais; baixa, o resto.",
            "O nível alta tem {alta_secoes} seções em {alta_locais} locais de {alta_mun} municípios. O nível média, {media_secoes} seções em {media_locais} locais. O nível baixa, {baixa_secoes} seções. Juntas, as seções sinalizadas reúnem {aptos_sinal} de eleitores aptos, {pct_aptos} do país.",
            "Quantas pessoas isso pede: um fiscal por local cobre o nível alta com {fis_alta} pessoas, alta e média com {fis_alta_media}, e a lista inteira com {fis_todos}. A lei permite um fiscal cobrindo várias seções do mesmo local, e até dois fiscais de cada partido por seção, o que daria {fis_dois_todos} pessoas para a lista inteira.",
            "Três frases valem para cada linha da lista. {rot_atipico} {rot_prioridade} {rot_resolve} Uma seção atípica tem quase sempre explicação comum: aldeia, presídio, zona rural, urna trocada por defeito, comunidade que vota em bloco há anos. A lista diz onde conferir primeiro, não o que aconteceu.",
            "O que o fiscal faz na seção é simples e está na lei: assiste à zerésima, confere a ata, anota o horário de encerramento, pede a via do boletim de urna impresso e fotografa o QR code para comparar com o publicado. Nesta thread: como a lista foi feita e o achado que a contraria, os cenários clássicos que o fiscal existe para impedir, o que já aconteceu no Brasil com data e tribunal, e o kit do dia. A lista inteira está no capítulo dos fiscais do dossiê, em brasil.arvor.co, com mapa navegável, e numa planilha Excel de {xlsx_tam} com abas por seção, local, município e UF.",
        ],
    },
    {
        "tag": "Como a lista foi feita",
        "tom": "outros",
        "titulo": "Os critérios, os níveis e o achado que contraria a própria lista.",
        "metrica": "{cod_rural}",
        "metrica_rot": "seções sinalizadas ficam em zona rural: explicação comum",
        "fig": G.fig_criterios,
        "fonte": "fiscais.json, criterios e resumo.explicacao_comum",
        "texto": [
            "Os critérios que mais disparam são {top1_nome}, em {top1_n} seções, {top2_nome}, em {top2_n}, e {top3_nome}, em {top3_n}. Nenhum deles prova nada sozinho. Brancos e nulos acima da zona aparecem onde há campanha local pelo voto nulo ou eleitorado mais velho; a variação desde 2022 aparece onde o município mudou; o encerramento tardio aparece onde houve fila.",
            "Os critérios mais raros pesam mais: {crit_c_nome}, em {crit_c} seções; {crit_b_nome}, em {crit_b}; {crit_h_nome}, em {crit_h}; {crit_f_nome}, em {crit_f}; {crit_g_nome}, em {crit_g}. Uma seção só chega ao nível alta somando vários sinais sem explicação no cadastro. Por isso o nível alta é pequeno.",
            "Onde fica o nível alta: {uf_alta1} tem {uf_alta1_n} locais, {uf_alta2} tem {uf_alta2_n} e {uf_alta3} tem {uf_alta3_n}. Em proporção das seções da própria UF, a maior taxa de seções sinalizadas fica em {uf_taxa}: {uf_taxa_pct}.",
            "Agora o achado que contraria a lista, e que precisa andar junto com ela. Das {n_secoes} seções, {cod_rural} ficam em zona rural, {cod_urna} tiveram urna trocada ou arquivo de recuperação, {cod_aldeia} estão em aldeia indígena, {cod_transito} são de voto em trânsito, {cod_quilombo} ficam em quilombo ou assentamento e {cod_presidio} em unidade prisional. Aldeia e presídio sozinhos levam {baixa_aldeia_presidio} seções para o nível baixa. E {enclaves} seções já votavam do mesmo jeito em 2022: são enclaves antigos, não novidade de 2026.",
            "Uma lista que cresce com aldeia, presídio e zona rural mede a geografia do país, não o comportamento da mesa. Aldeia vota em bloco porque a comunidade decide junta; presídio tem eleitorado pequeno e diferente; seção rural é pequena, e poucos votos mudam muito a porcentagem. Isso não é defeito escondido do método: está declarado no capítulo, e é por isso que a lista tem níveis.",
            "Testamos a escolha dos pesos. Com todos os critérios valendo o mesmo, {mudam_nivel} seções mudam de nível, {mudam_nivel_pct} da lista: o desenho geral não depende do peso que escolhemos. Há {sem_coord} locais sem coordenada conferida, que ficam na planilha com o endereço e sem ponto no mapa.",
            "O mapa do capítulo mostra cada local como um ponto, com cor pelo nível, e abre o endereço e o link de rota com um clique. A camada de território, com terra indígena, quilombo, favela, presídio, homicídios e acesso, serve para o fiscal planejar a ida e não aumenta a pontuação de ninguém.",
        ],
    },
    {
        "tag": "Os cenários, na mesa",
        "tom": "flavio",
        "titulo": "O que acontece dentro da seção, e o que deixa rastro no boletim.",
        "metrica": "{n_deixa} de {n_cenarios}",
        "metrica_rot": "cenários clássicos deixam sinal claro nos dados",
        "fig": lambda: G.fig_cenarios(("mesa", "cadastro")),
        "fonte": "fontes_fiscais.json, cenários e base legal; fiscais.json, critérios",
        "texto": [
            "Hipótese de risco, nunca descrição desta eleição. A lista lê números, e boa parte das manipulações clássicas do voto acontece dentro da sala sem deixar número nenhum. O dossiê descreve {n_cenarios} cenários: {n_deixa} deixam sinal claro nos dados, {n_parcial} deixam sinal fraco ou indireto e {n_nenhum} não deixam sinal algum. Este post trata dos que acontecem na mesa e no cadastro.",
            "O mesário pianista vota no lugar de quem não veio. O sinal possível é o comparecimento perto de cem por cento ou muito acima da zona, que o critério de comparecimento total pegou em {crit_c} seções. A biometria dificulta, mas a mesa pode liberar a urna sem digital, e o log registra cada liberação. O fiscal confere votantes da ata contra o caderno e o boletim e anota a hora dos últimos votos. É crime: {lei_ce_309}.",
            "O mesário que orienta o voto, constrange o eleitor ou entra na cabine para ajudar não deixa rastro no boletim. Só quem está na sala vê. O fiscal registra na ata cada ocorrência, com hora e nome, e impugna na hora, como garante o {lei_ce_132}.",
            "Urna de contingência é o caso oposto: deixa rastro. Quando a urna falha e é trocada, o tipo de urna e o arquivo mudam no boletim, e o critério de urna fora do padrão disparou em {crit_f} seções com voto diferente da zona. Trocar urna é procedimento normal. O risco é a troca sem ata: o fiscal exige hora, motivo, número da urna nova e estado dos lacres.",
            "A zerésima prova que a urna começou vazia. O fiscal chega antes da abertura, assiste à impressão e assina. No fim, pede a via do boletim impresso, que a lei manda entregar ({lei_l9504_68}), fotografa o QR code e compara com o boletim publicado. Seção sem arquivo ou em zona congelada, {crit_h} no 1º turno, se resolve pedindo o arquivo.",
            "Fila e horário deixam rastro: encerramento tardio com Lula acima da zona disparou em {crit_d} seções, boletim recebido de madrugada em {crit_g}. Quase sempre é fila longa ou transmissão difícil. O fiscal anota a hora em que a fila fechou e confere que votaram os que estavam nela, e só eles.",
            "No cadastro, eleitor fantasma e transferência em massa se combatem antes da eleição, com revisão do eleitorado ({lei_ce_289}). Presídio, aldeia, hospital e trânsito aparecem nos dados como explicação comum, não como sinal.",
        ],
    },
    {
        "tag": "Os cenários, fora da seção",
        "tom": "lula",
        "titulo": "Na porta e no território, quase nada aparece na urna. Só o fiscal vê.",
        "metrica": "{n_nenhum}",
        "metrica_rot": "cenários sem sinal nenhum nos dados",
        "fig": lambda: G.fig_cenarios(("entorno", "territorio")),
        "fonte": "fontes_fiscais.json, cenários e base legal; fiscais.json, critérios",
        "texto": [
            "Hipótese de risco, nunca descrição desta eleição. Fora da sala de votação, os cenários clássicos quase não deixam número. É onde o fiscal faz mais diferença, e onde corre mais risco.",
            "Boca de urna é propaganda e aliciamento no dia: material distribuído na porta, santinho derramado na calçada, carro de som, abordagem do eleitor na fila. É crime ({lei_l9504_39_p5}, {pena_l9504_39_p5}); a lei só admite a manifestação individual e silenciosa ({lei_l9504_39a}). Não deixa sinal no boletim. O fiscal não confronta: fotografa e filma de fora da seção, anota hora, local, placa e quem distribui, aciona o juiz eleitoral, o MPE e a polícia de plantão e pede a apreensão do material.",
            "Compra de voto é crime ({lei_ce_299}) e leva à cassação ({lei_l9504_41a}). O voto comprado é igual a qualquer outro na urna. A prova é testemunha, vídeo, dinheiro apreendido: quem oferece, o quê, onde e a que horas.",
            "Transporte irregular é ônibus, van ou carro pago por candidato, partido ou cabo eleitoral para levar eleitor no dia, quase sempre com comida e com o voto como condição. Só a Justiça Eleitoral pode organizar transporte gratuito em zona rural ({lei_l6091_11}), e a pena chega a {pena_l6091_11}. Pode aparecer como comparecimento acima do padrão numa seção rural, mas quase sempre não aparece. O fiscal anota placa, horário, motorista e quem paga, filma de fora e comunica o juiz e o MPE no mesmo dia.",
            "Voto de cabresto e voto sob ameaça de facção ou milícia podem deixar sinal fraco: concentração extrema num candidato e zona entre as mais atípicas, critérios que disparam em {crit_a} e {crit_i} seções. Mas comunidade que vota em bloco por convicção produz o mesmo número. Em área dominada, o fiscal não entra sem validar com a PM e o TRE local; a Justiça Eleitoral pode requisitar Força Federal ({lei_ce_23_xiv}).",
            "Abstenção induzida é o contrário do transporte irregular: impedir o eleitor de chegar, com ônibus que não sai, barreira na estrada ou ameaça. É crime ({lei_ce_297}). O fiscal registra lugar e hora do bloqueio e avisa o juiz eleitoral na hora, porque o remédio é no mesmo dia.",
        ],
    },
    {
        "tag": "O que já aconteceu",
        "tom": "outros",
        "titulo": "Nada disso é teoria. Os casos, com data e tribunal.",
        "metrica": "{n_casos}",
        "metrica_rot": "casos documentados, de {ano_ini} a {ano_fim}",
        "fig": G.fig_casos,
        "fonte": "fontes_fiscais.json, casos com instância, resultado e fonte lida",
        "texto": [
            "Verificado, com fonte. Os cenários dos dois posts anteriores não são teoria. O dossiê reúne {n_casos} casos brasileiros documentados, de {ano_ini} a {ano_fim}, cada um com data, instância, resultado e uma fonte lida pela casa. Nenhum é desta eleição.",
            "{casos_p1}",
            "{casos_p2}",
            "{casos_p3}",
            "Investigação, denúncia e condenação são coisas diferentes, e cada caso diz em que ponto parou. Os casos mostram que esses mecanismos existiram e que a Justiça Eleitoral os puniu quando houve prova. A lista completa, com o link de cada fonte, está no capítulo dos fiscais do dossiê em brasil.arvor.co.",
        ],
    },
    {
        "tag": "O kit do fiscal",
        "tom": "flavio",
        "titulo": "O que levar, o que conferir e a quem reportar.",
        "metrica": "{fis_alta_media}",
        "metrica_rot": "fiscais, um por local, cobrem os níveis alta e média",
        "fig": lambda: G.fig_kit(KIT),
        "fonte": "fiscais.json, resumo.fiscais e meta.base_legal; fontes_fiscais.json",
        "texto": [
            "O que levar: credencial do partido, documento com foto, celular carregado e bateria extra, o print do seu local com as seções e os critérios que dispararam, caneta e papel, e o contato do delegado do partido e do cartório eleitoral da zona.",
            "O que conferir, na ordem do dia. Chegar antes da abertura e assistir à impressão da zerésima, assinando. Conferir os lacres e o número da urna, e exigir na ata qualquer troca, com hora e motivo. Ficar na sala e anotar liberação sem digital, ajuda na cabine e constrangimento. Olhar o entorno sem confrontar: boca de urna, transporte, compra. No fechamento, anotar a hora em que a fila fechou e quem estava nela. Pedir a via do boletim impresso, fotografar o QR code e comparar com o publicado. Em seção com voto em trânsito, conferir que só vota quem consta do caderno daquela seção.",
            "A quem reportar. Dentro da seção, ao presidente da mesa e na ata, com a impugnação na hora. Fora dela, ao juiz eleitoral da zona, ao Ministério Público Eleitoral e à polícia de plantão. A Justiça Eleitoral recebe denúncia de propaganda irregular e de crime eleitoral pelos canais do TSE. Registro sem hora, lugar e prova vale pouco: foto, vídeo de fora da seção, placa, nome.",
            "O risco do território. Para cada local, o capítulo traz o contexto: terra indígena, quilombo, favela, unidade prisional, homicídios no município, fronteira, garimpo e distância até a sede. Isso não aumenta a pontuação de nenhuma seção; serve para planejar transporte, horário e companhia. Em área de facção, rural isolada ou indígena: validar com a PM e o TRE local antes de mandar alguém. Ninguém vai sozinho, e nenhum registro vale o risco de um confronto.",
            "Quantos: um fiscal por local cobre o nível alta com {fis_alta} pessoas, alta e média com {fis_alta_media}, a lista inteira com {fis_todos}. Comece pelo alta, depois o média, e no baixa basta conferir o boletim impresso.",
            "{rot_atipico} {rot_prioridade} {rot_resolve} A lista completa está no capítulo dos fiscais do dossiê da apuração em brasil.arvor.co, com mapa navegável, e para baixar: a planilha Excel de {xlsx_tam}, o CSV por seção e o CSV por local. Filtre pela sua UF e pelo seu município, ordene pelo nível e distribua um fiscal por local.",
        ],
    },
]


__all__ = ["KIT", "POSTS"]
