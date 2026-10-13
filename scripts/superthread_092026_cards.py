"""Textos e apresentação dos sete cards da rodada de setembro."""

from html import escape as esc

LIME = "#cfe63c"
CYAN = "#45c9c2"
AMBER = "#f0a930"
KIND = {
    "tese": (LIME, "tese"),
    "ponto": (CYAN, "ponto"),
    "limite": (AMBER, "contraprova"),
    "ordem": (LIME, "rota"),
}


def build_cards(
    *,
    AGG,
    ALVO,
    BASE,
    CAP,
    DFX,
    EST,
    MDA,
    NEX,
    NV,
    ONDAS,
    ORDEM,
    QUA,
    ULTIMO,
    VAO,
    ajustado,
    fmt,
    sgn,
    turno,
    viz_agregador,
    viz_datafolha,
    viz_nexus,
    viz_quaest,
    viz_quatro,
    viz_rota,
    viz_vao,
) -> list[dict]:
    df2, mda2, nex2, qua2 = (turno(i, "2t") for i in ORDEM)
    k2 = ULTIMO["2t"]["kernel"]
    ba, ce, pe = VAO["BA"], VAO["CE"], VAO["PE"]
    manaus, salvador, recife = CAP["Manaus"], CAP["Salvador"], CAP["Recife"]
    belem, fortaleza = CAP["Belém"], CAP["Fortaleza"]
    conquista = ALVO[("BA", "Vitória da Conquista")]
    rejeicao = DFX["tabelas"]["rejeicao"]["blocks"]["bloco3"]["rows"]
    ne_rej = rejeicao["Flavio Bolsonaro (PL)"]["Nordeste"]
    ne_rej_lula = rejeicao["Lula (PT)"]["Nordeste"]
    df_regiao = DFX["tabelas"]["turno2_flavio"]["blocks"]["bloco3"]["rows"]
    nexus_renda = {
        r["label"].split("  ")[-1].strip(): r["values"]
        for r in NEX["profile_tables"]["34"]
    }

    return [
        {
            "kind": "tese",
            "tag": "Abertura",
            "metric": "4 / 4",
            "title": "Quatro pesquisas em cinco dias, uma régua só, e todas andam para o mesmo lado",
            "t": "Datafolha, CNT/MDA, BTG/Nexus e Quaest publicaram entre 10 e 15 de setembro. As quatro discordam do placar. Nenhuma discorda do efeito da renda.",
            "chips": [
                (
                    "l",
                    f"Datafolha: {sgn(df2['gap_publicado'], 0)} vira {sgn(df2['gap_ajustado'], 2)}",
                ),
                (
                    "b",
                    f"média do 2º turno: {fmt(k2['ajustado']['flavio'], 2)} × {fmt(k2['ajustado']['lula'], 2)}",
                ),
                ("a", "a Quaest anda contra"),
            ],
            "viz": viz_quatro(),
            "copy": [
                "Quatro institutos nacionais publicaram em cinco dias, e o placar deles não bate. No 2º turno, Datafolha dá Lula 46 a 44, CNT/MDA dá 47,3 a 40, BTG/Nexus dá 47 a 46 e Quaest dá Flávio 42 a 40. Isso é uma variação de quase dez pontos na mesma quinzena, sobre a mesma eleição.",
                f"Há uma coisa em que as quatro concordam sem querer. Todas cruzam o voto por faixa de renda, e todas trazem uma composição de renda própria. Quando se troca só esse peso pelo da PNAD contínua anual de 2025, mantendo tudo o mais como o instituto publicou, as quatro andam para o mesmo lado. O Datafolha sai de Lula {sgn(df2['gap_publicado'], 0)} para Flávio {fmt(abs(df2['gap_ajustado']), 2)}. A MDA sai de {sgn(mda2['gap_publicado'], 1)} para {sgn(mda2['gap_ajustado'], 2)}. O BTG sai de {sgn(nex2['gap_publicado'], 0)} para {sgn(nex2['gap_ajustado'], 2)}. Quatro em quatro.",
                f"O tamanho do movimento tem explicação simples e verificável: ele acompanha o quanto cada amostra é mais pobre que o país. O Datafolha tem {fmt(ONDAS['Datafolha']['desvio_ate_primeira_faixa'], 2)} pontos a mais na faixa até dois salários mínimos do que a PNAD, e é o que mais se move. A Quaest tem {fmt(abs(ONDAS['Quaest']['desvio_ate_primeira_faixa']), 2)} pontos a menos, é a única amostra mais rica que o país, e é a única que anda na direção contrária: a régua tira de Flávio em vez de dar.",
                f"Na média do acervo, hoje com {len(AGG['pesquisas'])} pesquisas de {len(AGG['institutos'])} institutos, o 2º turno publicado está em Lula {fmt(k2['publicado']['lula'], 2)} contra {fmt(k2['publicado']['flavio'], 2)}. Sob a régua da PNAD, vira Flávio {fmt(k2['ajustado']['flavio'], 2)} contra {fmt(k2['ajustado']['lula'], 2)}.",
                f"Antes de qualquer manchete, dois testes. O primeiro é de amostragem: o intervalo de 95% da diferença no 2º turno é de {fmt(df2['margem_diferenca_95'], 2)} pontos no Datafolha e {fmt(nex2['margem_diferenca_95'], 2)} no BTG. Nenhuma das quatro separa os dois candidatos com 95% de confiança. O segundo é de composição, e é este: o sinal sobrevive à troca da margem dominante pela régua oficial. Uma manchete que diz lidera precisa passar nos dois.",
                "Isto é sensibilidade de uma margem sob régua comum, não é voto corrigido: a ponderação de cada instituto é conjunta e nenhum deles publica os pesos. Nos próximos seis posts, um dossiê por instituto, e depois a parte que ninguém está olhando, que são as pesquisas estaduais.",
                f"Acervo completo, com cada PDF e cada página: {BASE}/reponderacao_pnad.html",
            ],
            "foot": "PNADC anual 2025, visita 1, pessoas de 16+, preços de abril de 2026.",
            "link": "reponderacao_pnad.html",
        },
        {
            "kind": "ponto",
            "tag": "1 de 5 · Datafolha",
            "metric": f"{ne_rej}%",
            "title": "O teto do Nordeste não é falta de exposição: é rejeição declarada, e ela é o dobro da de Lula",
            "t": f"No Datafolha de 14/09, {ne_rej}% dos nordestinos dizem que não votariam em Flávio de jeito nenhum. Lula, no mesmo recorte, tem {ne_rej_lula}%.",
            "chips": [
                (
                    "l",
                    f"Nordeste 2º turno: {df_regiao['Lula (PT)']['Nordeste']} × {df_regiao['Flavio Bolsonaro (PL)']['Nordeste']}",
                ),
                (
                    "b",
                    f"Sul: {df_regiao['Lula (PT)']['Sul']} × {df_regiao['Flavio Bolsonaro (PL)']['Sul']}",
                ),
                ("a", "capital, RM e interior: 43, 43 e 45"),
            ],
            "viz": viz_datafolha(),
            "copy": [
                f"O Datafolha de 14 de setembro é a pesquisa com a amostra mais distante da régua oficial de renda entre as quatro: {fmt(ONDAS['Datafolha']['desvio_ate_primeira_faixa'], 2)} pontos a mais na faixa até dois salários do que a PNAD mede para o país. Trocar só esse peso leva o 2º turno de Lula 46 contra 44 para Flávio {fmt(ajustado('Datafolha', '2t', 'flavio'), 2)} contra {fmt(ajustado('Datafolha', '2t', 'lula'), 2)}. É o maior giro da rodada.",
                f"Mas o achado que interessa a quem faz campanha está no anexo regional, não na manchete. No 2º turno, o Nordeste dá {df_regiao['Lula (PT)']['Nordeste']} a Lula e {df_regiao['Flavio Bolsonaro (PL)']['Nordeste']} a Flávio. O Sul dá {df_regiao['Lula (PT)']['Sul']} e {df_regiao['Flavio Bolsonaro (PL)']['Sul']}, invertido. O Sudeste, {df_regiao['Lula (PT)']['Sudeste']} e {df_regiao['Flavio Bolsonaro (PL)']['Sudeste']}. Centro-Oeste e Norte juntos, {df_regiao['Lula (PT)']['Centro-Oeste/Norte']} e {df_regiao['Flavio Bolsonaro (PL)']['Centro-Oeste/Norte']}.",
                f"E a rejeição explica o teto melhor que o voto. {ne_rej}% do Nordeste declara que não votaria em Flávio em hipótese alguma, contra {ne_rej_lula}% que dizem o mesmo de Lula. No Sul a conta inverte: {rejeicao['Flavio Bolsonaro (PL)']['Sul']}% contra {rejeicao['Lula (PT)']['Sul']}%. Rejeição de 60 pontos não é um problema de agenda nem de tempo de televisão. É um problema de nome próprio, e ele não se resolve com mais comício do mesmo tipo.",
                f"O terceiro número desmonta um lugar-comum: capital, região metropolitana e interior praticamente não se separam. Flávio faz {df_regiao['Flavio Bolsonaro (PL)']['Regiao metropolitana']} na região metropolitana e {df_regiao['Flavio Bolsonaro (PL)']['Interior']} no interior. A fratura do Brasil, nesta eleição, é regional, não urbana. Quem organiza calendário por tamanho de cidade está usando um mapa que a pesquisa não confirma.",
                f"No 1º turno o desenho se repete com outra escala: Nordeste {DFX['tabelas']['estimulada_a']['blocks']['bloco3']['rows']['Lula (PT)']['Nordeste']} a {DFX['tabelas']['estimulada_a']['blocks']['bloco3']['rows']['Flavio Bolsonaro (PL)']['Nordeste']}, e Caiado marcando {DFX['tabelas']['estimulada_a']['blocks']['bloco3']['rows']['Ronaldo Caiado (PSD)']['Centro-Oeste/Norte']}% no Centro-Oeste e Norte, onde ele é o único nome do campo com voto regional próprio. A aprovação do governo no mesmo anexo dá {DFX['tabelas']['aprovacao']['blocks']['bloco3']['rows']['Aprova']['Nordeste']}% no Nordeste contra {DFX['tabelas']['aprovacao']['blocks']['bloco3']['rows']['Aprova']['Sul']}% no Sul: 24 pontos de distância dentro do mesmo país.",
                "A conclusão prática: no Nordeste, a candidatura presidencial não abre porta. Quem abre é o nome estadual, e o post 5 mostra por quanto.",
                f"Uma ressalva que a casa faz sempre e que vale aqui: o intervalo de 95% da diferença no 2º turno do Datafolha é de {fmt(df2['margem_diferenca_95'], 2)} pontos. A vantagem publicada de 2 pontos não separa os dois candidatos, e a versão correta da manchete é essa: Lula tem 46%, Flávio tem 44%, e a diferença não os separa com 95% de confiança.",
                f"Dossiê completo, com página e hash: {BASE}/datafolha_14092026.html",
            ],
            "foot": "Datafolha 14/09/2026, relatório completo, p. 38, 48, 49 e 57.",
            "link": "datafolha_14092026.html",
        },
        {
            "kind": "ponto",
            "tag": "2 de 5 · BTG/Nexus",
            "metric": f"{nexus_renda['De 2 até 5 S.M.'][1]} × {nexus_renda['De 2 até 5 S.M.'][0]}",
            "title": "A direita já ganha na classe média e perde no andar de baixo, e é isso que a régua da renda mede",
            "t": f"No BTG/Nexus, Flávio faz {nexus_renda['De 2 até 5 S.M.'][1]} contra {nexus_renda['De 2 até 5 S.M.'][0]} de Lula entre dois e cinco salários, e perde por {nexus_renda['Até 1 S.M.'][0]} a {nexus_renda['Até 1 S.M.'][1]} na faixa até um salário.",
            "chips": [
                (
                    "b",
                    f"2 a 5 S.M.: {sgn(nexus_renda['De 2 até 5 S.M.'][1] - nexus_renda['De 2 até 5 S.M.'][0], 0)} para Flávio",
                ),
                (
                    "l",
                    f"até 1 S.M.: {sgn(nexus_renda['Até 1 S.M.'][1] - nexus_renda['Até 1 S.M.'][0], 0)}",
                ),
                ("g", "a amostra mais próxima da PNAD"),
            ],
            "viz": viz_nexus(),
            "copy": [
                f"O BTG/Nexus de 14 de setembro publica 155 páginas e é, das quatro, a amostra que mais se parece com o país na renda: {fmt(ONDAS['Nexus']['desvio_ate_primeira_faixa'], 2)} pontos de distância da PNAD na faixa até dois salários. Por isso a reponderação quase não a move: o 2º turno sai de Lula 47 contra 46 para {fmt(ajustado('Nexus', '2t', 'lula'), 2)} contra {fmt(ajustado('Nexus', '2t', 'flavio'), 2)}, uma diferença de {fmt(abs(nex2['gap_ajustado']), 2)} de ponto. É a leitura que serve de controle das outras três.",
                f"O gradiente que ela mostra é o mapa de classe da eleição. Até um salário mínimo, Lula {nexus_renda['Até 1 S.M.'][0]} contra {nexus_renda['Até 1 S.M.'][1]}. De um a dois, {nexus_renda['De 1 até 2 S.M.'][0]} contra {nexus_renda['De 1 até 2 S.M.'][1]}. De dois a cinco, a virada: Flávio {nexus_renda['De 2 até 5 S.M.'][1]} contra {nexus_renda['De 2 até 5 S.M.'][0]}. Acima de cinco salários a vantagem se perde de novo: Lula {nexus_renda['Mais de 5 S.M.'][0]} contra {nexus_renda['Mais de 5 S.M.'][1]}. Flávio ganha o miolo e perde as duas pontas, e nenhum discurso de classe explica isso sozinho.",
                "A faixa de dois a cinco salários é onde a eleição está sendo decidida e é a maior do país: 39,3% dos brasileiros de 16 anos ou mais, pela PNAD. É o assalariado com carteira, o pequeno empresário, o motorista de aplicativo que passou a declarar renda. Não é o topo. A candidatura que tratar essa faixa como classe alta erra o tom e o programa.",
                f"A mesma tabela traz a região: Nordeste {NEX['profile_tables']['34'][10]['values'][0]} a {NEX['profile_tables']['34'][10]['values'][1]}, Sul {NEX['profile_tables']['34'][12]['values'][0]} a {NEX['profile_tables']['34'][12]['values'][1]}, Sudeste {NEX['profile_tables']['34'][11]['values'][0]} a {NEX['profile_tables']['34'][11]['values'][1]}. E a religião: entre evangélicos, Flávio {NEX['profile_tables']['33'][11]['values'][1]} contra {NEX['profile_tables']['33'][11]['values'][0]} de Lula no 1º turno, o recorte em que ele vai mais longe em todo o relatório.",
                f"No 2º turno, a mesma tabela separa o município: capital {NEX['profile_tables']['76'][13]['values'][0]} a {NEX['profile_tables']['76'][13]['values'][1]}, região metropolitana {NEX['profile_tables']['76'][14]['values'][0]} a {NEX['profile_tables']['76'][14]['values'][1]} e interior {NEX['profile_tables']['76'][15]['values'][0]} a {NEX['profile_tables']['76'][15]['values'][1]}. É o único dos quatro institutos em que o interior vira para Flávio e a capital não, o que coloca uma pergunta de desenho amostral que nenhum deles responde publicamente.",
                "Vale registrar o que o instituto é: a Nexus pertence à FSB Holding, que fatura publicidade do governo federal. Isso não invalida um número sequer, e os números dela são os mais próximos da régua oficial nesta rodada. Só precisa estar escrito.",
                "A consequência de programa é direta. A faixa que decide não quer transferência de renda nem corte de imposto do topo: ela quer preço de energia, juros do crédito consignado, segurança no trajeto de casa ao trabalho e escola que funcione. Quem falar com ela na linguagem do andar de cima perde o miolo sem ganhar o topo, que nesta pesquisa já está com o adversário.",
                f"Dossiê completo: {BASE}/nexus_btg_140926.html",
            ],
            "foot": "BTG/Nexus 14/09/2026, p. 33 e 34 do relatório de 155 páginas.",
            "link": "nexus_btg_140926.html",
        },
        {
            "kind": "limite",
            "tag": "3 de 5 · Quaest",
            "metric": sgn(qua2["gap_ajustado"], 2),
            "title": "A Quaest é a pesquisa que contraria a nossa tese, e por isso ela é a mais importante das quatro",
            "t": f"É a única amostra mais rica que o país. A régua da renda tira {fmt(abs(qua2['gap_ajustado'] - qua2['gap_publicado']), 2)} ponto de Flávio em vez de dar, e a vantagem publicada de 2 pontos vira {fmt(abs(qua2['gap_ajustado']), 2)}.",
            "chips": [
                (
                    "a",
                    f"desvio: {fmt(ONDAS['Quaest']['desvio_ate_primeira_faixa'], 2)} pontos",
                ),
                ("l", "2º turno publicado: 42 × 40"),
                (
                    "a",
                    f"com a PNAD: {fmt(ajustado('Quaest', '2t', 'flavio'), 2)} × {fmt(ajustado('Quaest', '2t', 'lula'), 2)}",
                ),
            ],
            "viz": viz_quaest(),
            "copy": [
                "Se um método só serve quando o resultado agrada, não é método. A Quaest de 14 de setembro é o teste, e nós publicamos o resultado com o mesmo destaque das outras três.",
                f"Ela é a única das quatro cuja amostra é mais rica que o país: {fmt(abs(ONDAS['Quaest']['desvio_ate_primeira_faixa']), 2)} pontos a menos na faixa até dois salários mínimos do que a PNAD anual de 2025 mede. Aplicada a mesma régua, na mesma direção, com o mesmo código, o resultado anda contra a hipótese de partida. O 2º turno publicado, Flávio 42 contra Lula 40, vira {fmt(ajustado('Quaest', '2t', 'flavio'), 2)} contra {fmt(ajustado('Quaest', '2t', 'lula'), 2)}: a vantagem encolhe de 2 pontos para {fmt(abs(qua2['gap_ajustado']), 2)}. No 1º turno, a diferença de Lula sobe de 5 para {fmt(turno('Quaest', '1t')['gap_ajustado'], 2)}.",
                "E há um segundo motivo para a Quaest merecer o post inteiro: ela é a única que declara a PNAD anual de 2025 como fonte da própria cota de renda, e a composição publicada na página 199 bate exatamente com as cotas registradas no TSE, 31, 42 e 27. Instituto que declara a régua e publica o perfil pode ser conferido. Os que não declaram, não.",
                f"O resto do relatório traz o que a campanha precisa: quatro origens de transferência medidas, e não estimadas, para o 2º turno; a convicção de voto de cada base, com {QUA['tables']['MOVEMENT'][5][1]}% dos eleitores de Lula dizendo que a escolha é definitiva contra {QUA['tables']['MOVEMENT'][5][2]}% dos de Flávio; e o cruzamento por identificação política que recompõe o placar publicado com resíduo abaixo de meio ponto.",
                f"Antes de qualquer conta derivada, a prova da leitura: recompomos o placar publicado usando as próprias bases de renda do instituto e chegamos a um resíduo de {fmt(QUA['proofs']['1t']['income_max_residual'], 2)} ponto no 1º turno. Se a recomposição não fecha, a transcrição está errada e nada do que vem depois vale. Esse passo é obrigatório e aparece em todos os dossiês do acervo.",
                "O que este post estabelece é o padrão de prova da casa: a mesma conta, aplicada a todas as pesquisas, com o resultado publicado seja qual for. Quem só mostra a reponderação que ajuda está fazendo militância com aparência de estatística.",
                f"Dossiê completo, com as 66 perguntas registradas: {BASE}/quaest_14092026.html",
            ],
            "foot": "Quaest/Globo 14/09/2026, BR-03607/2026, campo de 10 a 13 de setembro, 2.004 entrevistas.",
            "link": "quaest_14092026.html",
        },
        {
            "kind": "ponto",
            "tag": "4 de 5 · CNT/MDA e o acervo",
            "metric": f"{len(AGG['pesquisas'])}",
            "title": "A CNT/MDA entra no acervo e mostra por que uma pesquisa isolada não decide nada",
            "t": f"A 170ª rodada da CNT/MDA dá Lula {mda2['publicado']['lula']} contra {mda2['publicado']['flavio']} no 2º turno, a maior vantagem da quinzena. Sob a régua da PNAD, {sgn(mda2['gap_ajustado'], 2)}.",
            "chips": [
                ("l", f"MDA publicado: {sgn(mda2['gap_publicado'], 1)}"),
                ("a", f"com a PNAD: {sgn(mda2['gap_ajustado'], 2)}"),
                (
                    "g",
                    f"{len(AGG['pesquisas'])} pesquisas, {len(AGG['institutos'])} institutos",
                ),
            ],
            "viz": viz_agregador(),
            "copy": [
                f"A CNT/MDA divulgou em 15 de setembro a 170ª rodada, com {MDA['resultado']['n']} entrevistas presenciais. É a pesquisa mais favorável a Lula da quinzena: {mda2['publicado']['lula']} contra {mda2['publicado']['flavio']} no 2º turno e {turno('MDA', '1t')['publicado']['lula']} contra {turno('MDA', '1t')['publicado']['flavio']} no 1º.",
                f"O relatório declara, na página 3, que não houve ponderação dos dados. Quer dizer que a composição publicada na página 40 não é uma cota que foi imposta: é a distribuição das entrevistas que o campo produziu. E ela tem {fmt(ONDAS['MDA']['desvio_ate_primeira_faixa'], 2)} pontos a mais na faixa até dois salários mínimos do que a PNAD mede. Trocado esse peso, os {fmt(mda2['gap_publicado'], 1)} pontos viram {fmt(mda2['gap_ajustado'], 2)}.",
                "Duas observações documentais, porque importam para quem for citar a pesquisa: a capa e a metodologia trazem o registro BR-06902/2026, e a contracapa repete o BR-06935/2026, que é o código da rodada anterior. E a faixa de renda publicada inclui 1,4% de quem não informou, o que precisa ser tratado antes de qualquer conta derivada.",
                f"É para isso que existe o acervo. São {len(AGG['pesquisas'])} pesquisas de {len(AGG['institutos'])} institutos desde maio, cada uma com o PDF, a página do cruzamento de renda e o hash do arquivo, mais {len(AGG['nao_reponderaveis'])} que não publicam renda cruzada e por isso entram listadas e sem número. A média com meia-vida de 14 dias sobre o fim do campo dá, no 2º turno, Lula {fmt(k2['publicado']['lula'], 2)} contra {fmt(k2['publicado']['flavio'], 2)} no publicado e Flávio {fmt(k2['ajustado']['flavio'], 2)} contra {fmt(k2['ajustado']['lula'], 2)} sob a régua da PNAD.",
                f"A comparação entre institutos mostra o tamanho do problema. No mesmo 2º turno e na mesma quinzena, a Quaest dá Flávio na frente por 2 e a MDA dá Lula na frente por {fmt(mda2['gap_publicado'], 1)}: {fmt(abs(mda2['gap_publicado']) + 2, 1)} pontos de distância entre dois institutos, contra uma margem de diferença de {fmt(mda2['margem_diferenca_95'], 2)} pontos a 95% de confiança. O método de campo explica parte disso: a MDA faz presencial em domicílio e ponto de fluxo, com cotas e sem ponderação posterior; a Quaest sorteia municípios e setores censitários por probabilidade proporcional ao tamanho.",
                "A leitura honesta desse conjunto é chata: a eleição está dentro da margem, e a diferença entre os institutos é maior que a diferença entre os candidatos. Quem cita uma pesquisa isolada como tendência está escolhendo a que gosta.",
                f"Acervo, com filtro por instituto e por onda: {BASE}/reponderacao_pnad.html",
            ],
            "foot": "CNT/MDA 170ª rodada, BR-06902/2026, campo de 9 a 13 de setembro.",
            "link": "reponderacao_pnad.html",
        },
        {
            "kind": "ponto",
            "tag": "5 de 5 · as estaduais",
            "metric": f"{ce['vao_1t']}",
            "title": "Ninguém está olhando para as estaduais, e é lá que está o maior número da eleição",
            "t": f"A Quaest publicou 15 pesquisas estaduais em agosto e setembro. No Ceará, a direita tem {ce['gov']}% para o governo e Flávio tem {ce['flavio_1t']}% para presidente, na mesma entrevista.",
            "chips": [
                (
                    "c",
                    f"CE: {sgn(ce['vao_1t'], 0)} · BA: {sgn(ba['vao_1t'], 0)} · PE: {sgn(pe['vao_1t'], 0)}",
                ),
                ("a", "AC e RO: o sinal inverte"),
                ("g", f"PE no 2º turno contra 2º turno: {sgn(pe['vao_2t'], 0)}"),
            ],
            "viz": viz_vao(),
            "copy": [
                "Enquanto o país discute a quarta pesquisa nacional da semana, a Quaest publicou quinze pesquisas estaduais em agosto e setembro, e quase ninguém as leu. Os PDFs são imagem, sem camada de texto: transcrevemos página a página, com o número da página declarado no script, e uma leitura de máquina independente confere cada tabela.",
                f"O maior número da eleição está lá. No Ceará, a melhor candidatura de direita ao governo tem {ce['gov']}% e Flávio tem {ce['flavio_1t']}% para presidente. Mesma entrevista, mesmo entrevistado, mesmo peso: {ce['vao_1t']} pontos de distância. Na Bahia, {ba['gov']}% de {ba['candidato']} contra {ba['flavio_1t']}%: {ba['vao_1t']} pontos. Em Pernambuco, {pe['gov']}% de {pe['candidato']} contra {pe['flavio_1t']}%. No Maranhão, {VAO['MA']['gov']}% de {VAO['MA']['candidato']} contra {VAO['MA']['flavio_1t']}%.",
                f"Em cinco estados a Quaest mediu também o 2º turno presidencial, o que permite a comparação turno contra turno, a mais limpa possível. Pernambuco entrega o maior vão do país nessa régua: {pe['gov']}% no 2º turno estadual contra {pe['flavio_2t']}% no presidencial, {pe['vao_2t']} pontos.",
                f"E aqui está o achado que impede a leitura preguiçosa: o sinal inverte. No Acre, Flávio tem {VAO['AC']['flavio_1t']}% e o candidato da direita ao governo tem {VAO['AC']['gov']}%. Em Rondônia, {VAO['RO']['flavio_1t']}% contra {VAO['RO']['gov']}%. Onde o bolsonarismo é hegemônico, o nome nacional é o mais forte da cédula e puxa a chapa. O déficit é um fenômeno do Nordeste, não uma característica do candidato.",
                f"Os mesmos relatórios trazem o que falar em cada lugar, e isso desmonta o discurso único. Perguntado qual é o maior problema do estado, o Ceará responde violência com {dict(EST['temas']['CE'])['Violência']}%, o maior número de qualquer tema em qualquer estado da série. A Bahia responde violência com {dict(EST['temas']['BA'])['Violência']}%. O Maranhão responde saúde e infraestrutura, com {dict(EST['temas']['MA'])['Saúde']}% e {dict(EST['temas']['MA'])['Infraestrutura']}%. Roraima responde saúde com {dict(EST['temas']['RR'])['Saúde']}% e violência com {dict(EST['temas']['RR'])['Violência']}%. Levar segurança pública a Boa Vista é responder a uma pergunta que 6% do estado fez.",
                "O vão é teto endereçável, não previsão, e o dossiê repete isso em todos os capítulos. ACM Neto, Raquel Lyra e Ciro Gomes não são bolsonaristas, e quem vota neles não prometeu nada a ninguém. Nenhum instituto publica o cruzamento direto do voto para governador com o voto para presidente. Se publicasse, este dossiê teria metade do tamanho.",
                f"Atlas estadual completo, 15 pesquisas e 5.751 municípios: {BASE}/estaduais_092026.html",
            ],
            "foot": "Quaest, relatórios estaduais de agosto e setembro de 2026, com página declarada no dossiê.",
            "link": "estaduais_092026.html",
        },
        {
            "kind": "ordem",
            "tag": "Fecho · a rota",
            "metric": f"{fmt(manaus['bolsonaro_2t'] / 1000)} mil",
            "title": "O maior estoque de voto bolsonarista do Norte e do Nordeste fica numa capital que a campanha nunca visitou",
            "t": f"{manaus['municipio']} tem {fmt(manaus['bolsonaro_2t'])} votos de Bolsonaro de 2022, {fmt(manaus['bolsonaro_2t_pct'], 1)}% do 2º turno. O Amazonas é um dos dez estados fora do roteiro da pré-campanha.",
            "chips": [
                (
                    "g",
                    f"{fmt(NV['eleitores_2026'] / 1e6, 1)} mi de eleitores sem visita",
                ),
                (
                    "c",
                    f"metade do voto do NE em {EST['concentracao']['nordeste']['metade_em']} cidades",
                ),
                ("a", "o cerrado vale menos que uma tarde em Manaus"),
            ],
            "viz": viz_rota(),
            "copy": [
                f"Até 14 de setembro, a campanha tinha percorrido 17 unidades da federação e não tinha ido a dez, todas no Norte e no Nordeste, somando {fmt(NV['eleitores_2026'] / 1e6, 1)} milhões de eleitores. A leitura fácil é que ela evitou território hostil. Os números do TSE dizem outra coisa: três desses dez estados Bolsonaro venceu em 2022, e Roraima é o melhor resultado dele em todo o Brasil.",
                f"O voto que falta não está no sertão. Está nas capitais. {EST['concentracao']['nordeste']['metade_em']} municípios de {fmt(EST['concentracao']['nordeste']['municipios'])}, ou {fmt(EST['concentracao']['nordeste']['metade_pct_municipios'], 1)}% das cidades do Nordeste, concentram metade de todo o voto que Bolsonaro teve na região. {manaus['municipio']} sozinha guarda {fmt(manaus['bolsonaro_2t'])} votos, mais que {fortaleza['municipio']} ({fmt(fortaleza['bolsonaro_2t'])}) e uma vez e meia {salvador['municipio']} ({fmt(salvador['bolsonaro_2t'])}). {belem['municipio']} tem {fmt(belem['bolsonaro_2t'])}.",
                f"Duas decisões desta semana mostram o custo do mapa mental errado. Na Bahia, Salvador foi trocada por Vitória da Conquista: {fmt(salvador['bolsonaro_2t'])} votos contra {fmt(conquista['bolsonaro_2t'])}, cinco vezes e meia menos, em troca de um palanque mais confortável. Em Pernambuco, Santa Cruz do Capibaribe saiu da agenda em favor do Recife, e essa foi acertada: a cidade simbólica tem 27 mil votos de Bolsonaro, a capital tem {fmt(recife['bolsonaro_2t'])}.",
                f"O achado que contraria a nossa própria tese: a rota do MATOPIBA, que todo mundo cita quando fala de agro e Nordeste, soma {EST['matopiba']['municipios']} municípios, {fmt(EST['matopiba']['bolsonaro_2t'])} votos e {fmt(EST['matopiba']['eleitores_2026'])} eleitores. É metade do que Manaus entrega sozinha, espalhado por quatro estados. O cerrado rende doação, estrutura e pauta. Não rende volume.",
                "A ordem que sai dos números, sem datas e declarada como juízo editorial: Manaus antes de qualquer cidade média; Belém e São Luís no mesmo circuito; Salvador, e não só Conquista; a região metropolitana do Recife inteira; Maceió e Aracaju, onde a campanha nunca pisou; Fortaleza com o palanque estadual na frente, porque lá a rejeição é de 60%.",
                "E o que não fazer, que é a parte que custa voto: não abrir agenda no Nordeste pelo nome nacional, porque lá o palanque estadual tem teto muito maior; não levar discurso de segurança a Roraima, Tocantins e Alagoas, onde saúde vale de duas a cinco vezes mais; e não confundir estoque de 2022 com promessa de 2026, porque voto de quatro anos atrás mede onde o campo já esteve, não onde ele estará.",
                f"Rota completa, com o tema de cada estado e o que não dizer: {BASE}/estaduais_092026.html#rota",
            ],
            "foot": "TSE 2022 por município e eleitorado de 2026. Roteiro: Revista Fórum e BPMoney. Agenda: imprensa local, com link no dossiê.",
            "link": "estaduais_092026.html#rota",
        },
    ]


CSS = """
*,*::before,*::after{box-sizing:border-box}
:root{--bg:#0c0d0b;--bg2:#131512;--bg3:#191c18;--ink:#f4f2ea;--ink2:#ddd8ca;--muted:#9a9789;--faint:#8f8c7f;
 --lime:#cfe63c;--cyan:#45c9c2;--amber:#f0a930;--green:#34b47e;--lula:#d13c2e;--flavio:#5ba3e0;
 --line:rgb(244 242 234 / 13%);--line2:rgb(244 242 234 / 26%);
 --display:Fraunces,Georgia,serif;--sans:"IBM Plex Sans Condensed",Arial,sans-serif;--mono:"IBM Plex Mono",ui-monospace,monospace;
 --wrap:min(1080px,calc(100% - 40px))}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);font-size:17px;line-height:1.62;-webkit-font-smoothing:antialiased}
.wrap{width:var(--wrap);margin:0 auto}
a{color:var(--cyan)}
.top{padding:34px 0 8px;display:flex;flex-wrap:wrap;gap:14px;align-items:center;justify-content:space-between}
.brand-lockup{display:flex;align-items:center;gap:11px;font-family:var(--mono);font-size:.76rem;letter-spacing:.13em;text-transform:uppercase;color:var(--muted)}
.brand-lockup img{width:26px;height:26px;border-radius:4px}
.top .back{font-family:var(--mono);font-size:.74rem;letter-spacing:.1em;text-transform:uppercase;color:var(--lime);text-decoration:none;border:1px solid var(--line2);border-radius:999px;padding:7px 15px}
h1{font-family:var(--display);font-size:clamp(2.2rem,6vw,4.2rem);line-height:.99;letter-spacing:-.028em;margin:18px 0 0;font-weight:900}
h1 em{display:block;font-style:italic;color:var(--lime);font-weight:500}
.deck{max-width:78ch;color:var(--ink2);margin:20px 0 0;font-size:1.06rem}
.howto{margin:26px 0 0;border:1px solid var(--line);border-left:3px solid var(--cyan);border-radius:4px;background:var(--bg3);padding:18px 20px;color:var(--ink2);font-size:.95rem}
.howto b{color:var(--ink)}
.rail{position:sticky;top:0;z-index:30;margin:30px 0 0;padding:11px 0;background:rgb(12 13 11 / 93%);backdrop-filter:blur(10px);border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.rail .wrap{display:flex;gap:5px;align-items:center;overflow-x:auto;scrollbar-width:none}
.rail b{font-family:var(--mono);font-size:.68rem;letter-spacing:.13em;text-transform:uppercase;color:var(--faint);margin-right:8px;white-space:nowrap}
.rail a{width:26px;height:26px;flex:0 0 auto;display:grid;place-items:center;border-radius:5px;border:1px solid var(--line);color:var(--muted);text-decoration:none;font-family:var(--mono);font-size:.72rem}
.post{margin:52px 0 0;scroll-margin-top:64px}
.post-label{width:min(100%,820px);margin:0 auto 11px;font-family:var(--mono);font-size:.72rem;letter-spacing:.13em;text-transform:uppercase;color:var(--faint)}
.post-label b{color:var(--ink)}
/* O card é quadrado: 1:1 na largura de trabalho de 820px, que é o que se anexa. */
.card{position:relative;aspect-ratio:1/1;width:min(100%,820px);margin:0 auto;border:1px solid var(--line2);border-radius:8px;overflow:hidden;background:#0a0b09;container-type:inline-size;display:flex;flex-direction:column}
.card::before{content:"";position:absolute;inset:0;background:radial-gradient(120% 80% at 100% 0%,rgb(69 201 194 / 10%) 0,transparent 55%),radial-gradient(90% 70% at 0% 100%,rgb(207 230 60 / 8%) 0,transparent 60%)}
.card>*{position:relative;z-index:2}
.stripe{position:absolute;inset:0 0 auto 0;height:4px;z-index:3;background:var(--accent)}
.card-head{display:flex;align-items:center;justify-content:space-between;gap:14px;padding:2.2cqw 2.6cqw 0}
.chead{display:flex;align-items:center;gap:9px}
.chead img{width:2.6cqw;height:2.6cqw;min-width:22px;min-height:22px;border-radius:4px}
.chead b{display:block;font-size:1.65cqw;line-height:1.2}
.chead span{display:block;font-family:var(--mono);font-size:1.25cqw;color:var(--muted)}
.pno{font-family:var(--mono);font-size:1.35cqw;color:var(--accent);letter-spacing:.1em}
.card-body{flex:1;min-height:0;display:grid;grid-template-rows:auto minmax(0,1fr);gap:1.4cqw;padding:1.2cqw 2.6cqw}
.said{display:grid;grid-template-columns:auto minmax(0,1fr);gap:0 2.4cqw;align-items:start}
.said .num{grid-row:1/3}
.lead-tag{display:inline-block;font-family:var(--mono);font-size:1.2cqw;letter-spacing:.09em;text-transform:uppercase;color:var(--accent);border:1px solid currentcolor;border-radius:999px;padding:.45cqw 1cqw}
.metric{font-family:var(--display);font-weight:900;font-size:5cqw;line-height:.95;letter-spacing:-.03em;color:var(--accent);margin:.7cqw 0 0;white-space:nowrap}
.card h2{font-family:var(--display);font-size:2.55cqw;line-height:1.12;margin:.5cqw 0 .6cqw;font-weight:700}
.card .t{font-size:1.52cqw;line-height:1.42;color:var(--ink2);margin:0}
.kchips{display:flex;flex-wrap:wrap;gap:.55cqw;margin-top:.8cqw}
.kchip{font-family:var(--mono);font-size:1.14cqw;border:1px solid currentcolor;border-radius:999px;padding:.35cqw .8cqw;white-space:nowrap}
.kchip.l{color:#ea6a5c}.kchip.b{color:var(--flavio)}.kchip.a{color:var(--amber)}.kchip.c{color:var(--cyan)}.kchip.g{color:var(--green)}
.viz{border:1px solid var(--line);border-radius:6px;background:rgb(244 242 234 / 5%);padding:1.2cqw;min-width:0;min-height:0;display:flex;align-items:center;justify-content:center}
.viz svg{width:100%;height:100%;max-height:100%;display:block}
.card-foot{flex:0 0 auto;display:flex;justify-content:space-between;gap:12px;padding:1.1cqw 2.6cqw;font-family:var(--mono);font-size:1.12cqw;color:var(--faint);border-top:1px solid var(--line)}
.copy{margin:14px auto 0;width:min(100%,820px);border:1px solid var(--line);border-radius:6px;background:var(--bg2);padding:20px 22px;font-family:var(--mono);font-size:.88rem;line-height:1.72;color:var(--ink2);white-space:pre-wrap;position:relative}
.cc{position:absolute;top:12px;right:18px;font-size:.7rem;color:var(--faint);letter-spacing:.09em}
.copy-btn{margin:10px auto 0;display:block;width:min(100%,820px);text-align:left;font-family:var(--mono);font-size:.74rem;letter-spacing:.11em;text-transform:uppercase;background:transparent;color:var(--lime);border:1px solid var(--line2);border-radius:999px;padding:9px 18px;cursor:pointer}
.copy-btn:hover{border-color:var(--lime)}
footer{margin:72px 0 0;border-top:1px solid var(--line);padding:34px 0 60px;color:var(--muted);font-size:.92rem}
footer h2{font-family:var(--display);font-size:1.6rem;margin:0 0 10px;color:var(--ink)}
@media (width <= 720px){
 body{font-size:16px}
 .card{aspect-ratio:auto}
 .card-head{padding:16px 18px 0}
 .chead img{width:26px;height:26px}
 .chead b{font-size:.92rem}
 .chead span{font-size:.72rem}
 .pno{font-size:.8rem}
 .card-body{gap:16px;padding:16px 18px 20px}
 .said{grid-template-columns:1fr}
 .said .num{grid-row:auto}
 .lead-tag{font-size:.68rem;padding:5px 11px}
 .metric{font-size:2.4rem;margin:12px 0 4px}
 .card h2{font-size:1.42rem;margin-bottom:9px}
 .card .t{font-size:.96rem;line-height:1.55}
 .kchips{gap:7px;margin-top:13px}
 .kchip{font-size:.7rem;padding:4px 9px}
 .viz{padding:14px}
 .viz svg{height:auto}
 .card-foot{padding:12px 18px;font-size:.68rem;flex-direction:column;gap:4px}
 .copy{padding:16px 15px;font-size:.84rem}
 .cc{position:static;display:block;text-align:right;margin-bottom:8px}
}
"""


JS = """
function cp(button){
  const node = button.previousElementSibling;
  const text = node.getAttribute('data-copy') || node.innerText;
  navigator.clipboard.writeText(text).then(() => {
    const original = button.textContent;
    button.textContent = 'copiado';
    setTimeout(() => { button.textContent = original; }, 1600);
  });
}
"""


def render_card(index: int, total: int, card: dict, kinds: dict) -> str:
    accent, kind_label = kinds[card["kind"]]
    chips = "".join(
        f'<span class="kchip {tone}">{esc(label)}</span>'
        for tone, label in card["chips"]
    )
    body = "\n\n".join(card["copy"])
    return f"""
<section class="post" id="p{index}">
  <div class="post-label">Post {index}/{total} · <b>{esc(card["tag"])}</b> · {esc(kind_label)}</div>
  <div class="card" style="--accent:{accent}">
    <div class="stripe"></div>
    <div class="card-head">
      <div class="chead"><img src="img/arvor_logo.png" alt=""><div><b>Arvor Intelligence</b><span>brasil.arvor.co · rodada de setembro de 2026</span></div></div>
      <div class="pno">{index:02d} / {total:02d}</div>
    </div>
    <div class="card-body">
      <div class="said">
        <div class="num"><span class="lead-tag">{esc(card["tag"])}</span><div class="metric">{esc(card["metric"])}</div></div>
        <div><h2>{esc(card["title"])}</h2><p class="t">{esc(card["t"])}</p><div class="kchips">{chips}</div></div>
      </div>
      <div class="viz">{card["viz"]}</div>
    </div>
    <div class="card-foot"><span>{esc(card["foot"])}</span><span>{index:02d}/{total:02d}</span></div>
  </div>
  <div class="copy" data-copy="{esc(body)}"><span class="cc">{len(body)} chars</span>{esc(body)}</div>
  <button class="copy-btn" onclick="cp(this)">Copiar texto</button>
</section>"""
