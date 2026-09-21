"""Capítulo da transferência de voto do dossiê Sudeste de 21/09/2026.

Saiu de `datafolha-21092026-sudeste-view.py`, que já passava de mil linhas,
quando a cadeia de três níveis acrescentou a natureza ancorada, a tabela de
incerteza das linhas publicadas e a conta na tela de cada estado. Nenhum
número é digitado aqui: todos vêm de `docs/assets/datafolha_21092026_sudeste.json`.

O capítulo recebe de `ctx` os utilitários da página, para não duplicar
formatação nem referência de fonte.
"""

UFS = ("SP", "RJ", "MG")
NOME_UF = {"SP": "São Paulo", "RJ": "Rio de Janeiro", "MG": "Minas Gerais"}
# Valor que a célula São Paulo, Tarcísio para Lula no 2º turno tinha antes da
# ancoragem, com a mesma prior ideológica e o motor de duas vias. Fica aqui
# como registro do antes e do depois, e é conferido em teste.
ANTES_SP_TARCISIO_LULA_PP = 2.232


def tabela_de_cruzamentos(dados, ctx):
    linhas = []
    for cruzamento in dados["cruzamentos_publicados"]:
        destino = (
            "1º turno" if "1o turno" in cruzamento["destino_pergunta"] else "2º turno"
        )
        for origem, valores in cruzamento["linhas"].items():
            linhas.append(
                [
                    ctx["curto"](origem),
                    cruzamento["uf"],
                    destino,
                    ", ".join(
                        f"{ctx['curto'](nome)} {valor}%"
                        for nome, valor in valores.items()
                    ),
                    f"{100 - sum(valores.values())}%",
                    ctx["ref_pres"](cruzamento["pagina"], f"p. {cruzamento['pagina']}"),
                ]
            )
    return ctx["table"](
        [
            "Eleitorado do candidato ao governo",
            "UF",
            "Destino",
            "Destinos publicados",
            "Fora dos destinos publicados",
            "Fonte",
        ],
        linhas,
    )


def incerteza_das_linhas(dados, ctx):
    """Cada linha publicada com a base da subamostra e o intervalo ao lado."""
    num = ctx["num"]
    linhas = []
    com_zero = []
    for uf in UFS:
        for item in dados["transferencia"][uf]["incerteza_das_linhas_medidas"]:
            baixo, alto = item["ic95_com_deff_pct"]
            linhas.append(
                [
                    f"{uf} · {ctx['curto'](item['origem'])}",
                    ctx["curto"](item["destino"]),
                    item["turno"],
                    f"{item['valor_pct']}%",
                    str(item["n_subamostra"]),
                    f"{num(baixo, 1)} a {num(alto, 1)}%",
                    f"{num(item['pontos_do_eleitorado_pp'])} pp",
                ]
            )
            if item["zero_dentro_do_ic"]:
                com_zero.append(
                    f"{uf}, {ctx['curto'](item['origem'])} para "
                    f"{ctx['curto'](item['destino'])} no {item['turno']}"
                )
    deff = dados["transferencia"]["RJ"]["incerteza_das_linhas_medidas"][0]["deff"]
    ruas = next(
        r
        for r in dados["transferencia"]["RJ"]["incerteza_das_linhas_medidas"]
        if r["origem"].startswith("Douglas Ruas")
        and r["destino"].startswith("Lula")
        and r["turno"] == "2º turno"
    )
    h = (
        "<p><strong>Linha publicada também tem intervalo.</strong> Cada uma "
        "dessas leituras é uma proporção dentro de uma subamostra de algumas "
        "centenas de entrevistas, e o dossiê vinha apresentando todas como "
        "ponto. A tabela abaixo traz a base ponderada de cada origem, o "
        "intervalo de 95% com efeito de desenho plausível de "
        f"{num(deff, 1)} e o que a linha vale em pontos do eleitorado do "
        "estado.</p>"
    )
    h += ctx["table"](
        [
            "Eleitorado de origem",
            "Destino",
            "Turno",
            "Linha publicada",
            "Base ponderada",
            "IC95 com efeito de desenho",
            "Pontos do eleitorado",
        ],
        linhas,
    )
    h += (
        "<p>Duas leituras saem daí. A primeira: o eleitor de Douglas Ruas "
        f"que vota em Lula no segundo turno é {ruas['valor_pct']}% de uma "
        f"base de {ruas['n_subamostra']} entrevistas, intervalo de "
        f"{num(ruas['ic95_com_deff_pct'][0], 1)} a "
        f"{num(ruas['ic95_com_deff_pct'][1], 1)}%, com o zero fora mesmo "
        "depois do efeito de desenho, e coerente com os 3% do primeiro turno "
        f"{ctx['ref_pres'](12, 'p. 12')} e com os 7% do eleitorado de Ruas que "
        f"aprovam Lula. {ctx['ref_pres'](13, 'p. 13')} Medição não se "
        "sobrescreve por prior, por mais que a prior pareça óbvia. A segunda: "
        f"isso vale {num(ruas['pontos_do_eleitorado_pp'])} pontos do "
        "eleitorado fluminense, e uma fita visível no diagrama não é "
        "transferência grande.</p>"
    )
    if com_zero:
        h += (
            "<p>O contrário também precisa ser dito, e com o mesmo destaque: "
            + "; ".join(com_zero)
            + " tem o zero dentro do intervalo. Essas linhas não separam o "
            "valor publicado de nenhuma transferência.</p>"
        )
    return h


def conta_na_tela(dados, ctx):
    """Quanto do voto de Lula em cada estado sai do eleitorado da direita."""
    num = ctx["num"]
    h = ""
    for uf in ("SP", "MG"):
        conta = dados["transferencia"][uf]["conta_na_tela"]
        nome = ctx["curto"](conta["candidatura_de_direita"])
        parcelas = " + ".join(
            f"{ctx['curto'](p['origem'])} {p['linha_pct']}% de {p['massa_pct']} = "
            f"{num(p['pontos_pp'])}"
            for p in conta["parcelas"]
        )
        medido = (
            "pelo que o instituto mediu, sim"
            if conta["natureza"] == "medida"
            else "pelo que o instituto mediu no primeiro turno, sim"
        )
        h += (
            f"<p><strong>Os {conta['lula_no_estado_pct']} de Lula em {uf} exigem "
            f"voto de {nome}?</strong> Pela aritmética, não: fora de {nome} há "
            f"{num(conta['fora_da_direita_pp'], 0)} pontos, mais do que Lula "
            f"precisa. {medido[0].upper()}{medido[1:]}, cerca de "
            f"{num(conta['medido_na_direita_pp'])} pontos, um em cada "
            f"{num(conta['um_em_cada'], 0)} votos de Lula no estado. A conta na "
            f"tela: {parcelas}, somando {num(conta['medido_pp'])} pontos. Sobram "
            f"{num(conta['lula_no_estado_pct'] - conta['medido_pp'])} pontos para "
            f"{num(conta['resto_do_eleitorado_pp'], 0)} pontos de eleitorado, ou "
            f"{num(conta['exigencia_com_a_direita_pct'], 0)}% de tudo o que "
            f"resta. Sem o eleitor de {nome}, Lula precisaria de "
            f"{num(conta['exigencia_sem_a_direita_pct'], 0)}% do resto. "
            f"{ctx['ref_pres'](conta['fonte']['pagina'], 'p. ' + str(conta['fonte']['pagina']))}</p>"
        )
        if conta["natureza"] != "medida":
            h += (
                "<p>Em São Paulo a parcela acima é piso, não medição direta do "
                "segundo turno: sai da linha de primeiro turno multiplicada pela "
                f"retenção declarada de {num(conta['retencao'], 2)}. A estimativa "
                "ancorada da cadeia de três níveis dá "
                f"{num(conta['estimativa_ancorada_na_direita_pp'])} pontos, ou um "
                f"em cada {num(conta['um_em_cada_ancorado'], 0)} votos de Lula no "
                "estado.</p>"
            )
    mg = dados["transferencia"]["MG"]["fracao_do_voto_de_lula_na_direita_estadual"]
    h += (
        "<p>No segundo turno estadual mineiro a conta fica maior, porque "
        "Cleitinho recolhe eleitorado de Kalil, que o próprio instituto mede "
        f"entregando 66% a Lula. {ctx['ref_pres'](21, 'p. 21')} A cadeia devolve "
        f"{num(mg['pontos_pp'])} pontos, ou {num(mg['fracao_pct'], 0)}% de todo o "
        "voto de Lula em Minas, dentro do eleitorado de quem vota Cleitinho no "
        "segundo turno estadual. É estimativa ancorada, não medição, e o piso "
        "aritmético do próprio relatório já obriga um número positivo: Lula 46 "
        "menos Patrus 24 menos a não escolha do segundo turno estadual não cabe "
        "sem voto de Cleitinho.</p>"
    )
    return h


def tabela_de_robustez(dados, ctx):
    num = ctx["num"]
    pares = (
        ("gov1_pres1", "Governador 1º → presidente 1º"),
        ("gov1_pres2", "Governador 1º → presidente 2º"),
        ("gov2_pres2", "Governador 2º → presidente 2º"),
    )
    rotulo_natureza = {
        "medida": "Medida",
        "ancorada": "Ancorada em linha medida",
        "limitada": "Limitada por Fréchet",
        "estimada": "Estimada",
    }
    linhas = []
    for uf in UFS:
        for chave, rotulo in pares:
            robustez = dados["transferencia"][uf][chave]["robustez"]
            faixa = robustez["celula_direita_para_flavio"]
            valores = list(robustez["vazamento_da_direita_pct"].values())
            antes = robustez.get("vazamento_sem_ancoragem_pct")
            linhas.append(
                [
                    f"{uf} · {rotulo}",
                    rotulo_natureza.get(robustez["natureza"], robustez["natureza"]),
                    f"{num(min(valores))} a {num(max(valores))}%",
                    (
                        f"{num(min(antes.values()))} a {num(max(antes.values()))}%"
                        if antes
                        else "igual"
                    ),
                    f"{num(robustez['amplitude_entre_priors_pp'])} pp",
                    f"{num(faixa['frechet_min_pp'], 1)} a "
                    f"{num(faixa['frechet_max_pp'], 1)} pp",
                ]
            )
    return ctx["table"](
        [
            "Estado e par de perguntas",
            "Natureza",
            "Vazamento da direita, entre as priors",
            "O mesmo sem ancoragem",
            "Amplitude",
            "Fréchet da célula direita → Flávio",
        ],
        linhas,
    )


def tabela_de_sensibilidade(dados, ctx):
    num = ctx["num"]
    linhas = []
    for uf in UFS:
        grade = dados["transferencia"][uf]["gov2_pres2"]["sensibilidade"]
        valores = [g["direita_para_lula_pp"] for g in grade]
        fugas = [g["vazamento_pct"] for g in grade]
        robustez = dados["transferencia"][uf]["gov2_pres2"]["robustez"]
        linhas.append(
            [
                f"{uf} · {ctx['curto'](robustez['origem'])}",
                str(len(grade)),
                f"{num(min(valores))} a {num(max(valores))} pp",
                f"{num(min(fugas))} a {num(max(fugas))}%",
            ]
        )
    return ctx["table"](
        [
            "Estado e eleitorado de origem",
            "Combinações rodadas",
            "Origem da direita para Lula",
            "Vazamento total",
        ],
        linhas,
    )


def capitulo(dados, table, figure, ctx):
    ctx = {**ctx, "table": table}
    num = ctx["num"]
    curto = ctx["curto"]
    ref_pres = ctx["ref_pres"]
    fig = ctx["FIG"]
    varredura = dados["varredura_de_cruzamentos"]
    sp_conta = dados["transferencia"]["SP"]["conta_na_tela"]
    sp_lula = dados["transferencia"]["SP"]["gov1_pres2"]["robustez"][
        "celula_direita_para_lula"
    ]
    retencao = sp_conta["retencao"]

    h = ctx["bloco"](
        "sudeste-transferencia", "Treze linhas medidas, e um piso que elas impõem."
    )
    h += (
        "<p>Antes de estimar qualquer coisa, procuramos o cruzamento publicado. Ele "
        "existe. O relatório presidencial estadual cruza o voto para governador com "
        "o voto para presidente no texto corrido, em São Paulo, no Rio e em Minas: "
        f"<strong>{varredura['linhas_medidas']} linhas</strong> de origem, com a "
        "página ao lado. Elas entram fixas, como medição. Os anexos de tabelas "
        "cruzadas têm três blocos e nenhum deles usa o voto de outro cargo como "
        "coluna; os relatórios de governador não citam a Presidência.</p>"
    )
    h += tabela_de_cruzamentos(dados, ctx)
    h += (
        "<p>Três leituras diretas, sem modelo. Em Minas, <strong>25% do eleitor de "
        "Cleitinho vota em Lula</strong> no segundo turno presidencial, e 29% não "
        f"votam em Flávio. {ref_pres(21, 'p. 21')} Em São Paulo, <strong>41% do "
        "eleitorado de Tarcísio ficam fora de Flávio</strong> já no primeiro turno: "
        f"12 pontos com Lula e 8 com Cury. {ref_pres(4, 'p. 4')} No Rio, o eleitor "
        f"de Eduardo Paes dá 28% a Flávio no segundo turno. {ref_pres(13, 'p. 13')}</p>"
    )
    h += incerteza_das_linhas(dados, ctx)
    h += (
        "<p><strong>A regra que mudou.</strong> Uma estimativa de segundo turno não "
        "pode ficar abaixo do que o instituto mediu no primeiro turno, na mesma "
        "entrevista. Em São Paulo o relatório mede que 12% do eleitorado de "
        f"Tarcísio já votam em Lula no primeiro turno presidencial: "
        f"{num(sp_conta['medido_na_direita_pp'])} pontos do eleitorado paulista, "
        f"com retenção declarada de {num(retencao, 2)}. {ref_pres(4, 'p. 4')} Quem "
        "escolheu Lula no primeiro turno não some no segundo. A versão anterior "
        "desta página estimava essa célula por prior, sem piso, e devolvia "
        f"{num(ANTES_SP_TARCISIO_LULA_PP)} pontos, abaixo da própria medição do "
        "instituto. Agora a célula sai de uma cadeia de três níveis, governador, "
        "primeiro turno presidencial e segundo turno presidencial, com as linhas "
        "publicadas fixas no primeiro estágio, e devolve "
        f"{num(sp_lula['valor_pp'])} pontos. O erro era nosso, e o número que o "
        "corrige é do próprio relatório.</p>"
    )
    h += (
        "<p>Por isso o diagrama abaixo tem três naturezas de fita: <strong>sólida "
        "onde existe linha publicada neste par</strong>, <strong>pontilhada onde a "
        "célula tem piso medido em outro par da mesma amostra</strong> e hachurada "
        "onde nada a segura além da prior declarada. Toda célula não medida carrega "
        "a faixa de Fréchet, que é o único número imune à prior, e agora também o "
        "limite inferior que o piso medido impõe.</p>"
    )
    for uf in UFS:
        alvo = dados["transferencia"][uf]["gov1_pres2"]
        variante = alvo["variantes"]["ideologica"]
        publicadas = len(variante["linhas_medidas"])
        ancoradas = len(
            [
                k
                for k in variante["linhas_ancoradas"]
                if k not in variante["linhas_medidas"]
            ]
        )
        h += figure(
            fig.sankey(
                uf,
                alvo,
                f"{uf}: do voto de governador ao 2º turno presidencial",
                "Origem: voto estimulado para governador. Destino: 2º turno "
                "presidencial. Mesma amostra, campo de 8 a 10/09/2026.",
            ),
            ctx["aviso_rolar"](
                f"{NOME_UF[uf]}. {publicadas} das "
                f"{len(variante['origem_pct'])} origens têm linha publicada neste "
                f"par e {ancoradas} têm piso medido em outro par da mesma amostra. "
                "A largura é massa percentual agregada, proporcional em toda fita "
                "e sem espessura mínima, e não é acompanhamento de pessoas. "
                "Candidaturas abaixo de 3% sem linha publicada aparecem somadas em "
                "uma origem única."
            ),
        )
        h += (
            '<div class="flow-readout" aria-live="polite">Toque em uma fita ou use '
            "Tab para ler origem, destino, natureza e faixa de Fréchet.</div>"
        )
    h += (
        "<p>São Paulo continua sendo o caso a cobrar, por um motivo preciso. O "
        "instituto publicou o cruzamento com o <strong>primeiro</strong> turno "
        f"presidencial {ref_pres(4, 'p. 4')} e nenhuma linha com o segundo. Essa "
        "linha não fecha o diagrama paulista, e ancora: as duas origens grandes "
        "saem pontilhadas, com piso medido. O carioca tem duas origens sólidas "
        "mais Garotinho ancorado pela linha da p. 12, e o mineiro tem três "
        "sólidas. O que falta em São Paulo é o par de segundo turno contra "
        "segundo turno, e é ele que decide a eleição.</p>"
    )
    h += conta_na_tela(dados, ctx)
    h += ctx["bloco"]("sudeste-robustez", "O que sobrevive à troca da prior.")
    h += tabela_de_robustez(dados, ctx)
    amplitude = {
        uf: dados["transferencia"][uf]["gov2_pres2"]["robustez"][
            "amplitude_entre_priors_pp"
        ]
        for uf in UFS
    }
    antes_rj = dados["transferencia"]["RJ"]["gov2_pres2"]["robustez"][
        "vazamento_sem_ancoragem_pct"
    ]
    h += (
        "<p>A leitura é direta. <strong>Onde há linha publicada, a amplitude entre "
        "as priors é zero</strong>: a prior não move nada, porque a margem já está "
        "medida. Onde não há, ela decide o resultado. No Rio, o par de segundo "
        "turno contra segundo turno ia de "
        f"{num(min(antes_rj.values()))} a {num(max(antes_rj.values()))}% conforme a "
        "prior, amplitude que nenhum laudo deveria publicar sem âncora; com as "
        "linhas medidas de Ruas, Paes e Garotinho ancorando a cadeia, a amplitude "
        f"cai para {num(amplitude['RJ'])} pontos. Em Minas ela é de "
        f"{num(amplitude['MG'])} pontos. O par que nenhum dos três relatórios "
        "cruza continua sendo o mesmo, e publicá-lo custaria uma tabela ao "
        "instituto.</p>"
    )
    h += (
        "<p><strong>A prior não é o único parâmetro.</strong> A retenção de quem já "
        "escolheu um finalista no primeiro turno e a fidelidade de base do segundo "
        "turno estadual também são hipóteses declaradas. A grade abaixo roda as "
        "três priors contra retenções de 0,93 a 0,99 e fidelidades de 0,93 a 0,99, "
        "uma por vez, e mostra o que o resultado faz.</p>"
    )
    h += tabela_de_sensibilidade(dados, ctx)
    serie = dados["transferencia"]["SP"]["serie_do_vazamento"]
    setembro = list(serie["setembro_2026_pct"].values())
    sem_ancora = list(serie["setembro_2026_sem_ancoragem_pct"].values())
    h += (
        "<p><strong>Série de São Paulo.</strong> Em agosto a mesma conta devolveu "
        f"{num(serie['agosto_2026_datafolha_pct'])}% do eleitor de Tarcísio fora de "
        f"Flávio no segundo turno pelo Datafolha e "
        f"{num(serie['agosto_2026_atlas_pct'])}% pela Atlas. Em setembro, com a "
        f"cadeia ancorada, a faixa entre as priors vai de {num(min(setembro))}% a "
        f"{num(max(setembro))}%; sem ancoragem ela iria de {num(min(sem_ancora))}% "
        f"a {num(max(sem_ancora))}%. A comparação com agosto exige a ressalva: o "
        "número antigo foi estimado sem piso medido e não é comparável ponto a "
        "ponto com o novo. O que a série mostra é a direção, não a distância. "
        '<a class="refs" href="sp_092026.html">Atlas de São Paulo</a></p>'
    )
    h += (
        "<details><summary>Faixa de Fréchet de cada célula dos três diagramas</summary>"
    )
    rotulo = {"medida": "Publicada", "ancorada": "Ancorada", "limitada": "Limitada"}
    linhas = []
    for uf in UFS:
        *_, celulas = fig.celulas_do_diagrama(dados["transferencia"][uf]["gov1_pres2"])
        for celula in celulas:
            linhas.append(
                [
                    f"{uf} · {curto(celula['origem'])}",
                    fig.CURTO[celula["destino"]],
                    num(celula["valor_pp"]),
                    f"{num(celula['frechet_min_pp'], 1)} a "
                    f"{num(celula['frechet_max_pp'], 1)}",
                    (
                        num(celula["piso_medido_pp"])
                        if celula.get("piso_medido_pp")
                        else "sem piso"
                    ),
                    rotulo.get(celula["estado"], "Estimada"),
                ]
            )
    h += table(
        [
            "Origem",
            "Destino",
            "Valor no diagrama, pp",
            "Fréchet, pp",
            "Piso medido, pp",
            "Natureza",
        ],
        linhas,
    )
    h += (
        "<p>A prior é declarada e ideológica: base própria fiel, candidatura do mesmo "
        "campo migrando majoritariamente para o líder do campo, cruzamento para o "
        "campo oposto próximo de zero e não escolha absorvendo parte das perdas. Os "
        "zeros são estruturais e o ajuste proporcional os preserva. O cubo de três "
        "níveis nunca usa independência condicional dentro do intermediário: a "
        "distribuição de destino depende da origem e da via, com o termo de "
        "interação declarado no próprio script. A leitura é agregada e nunca "
        "descreve o percurso de um entrevistado.</p></details>"
    )
    return h
