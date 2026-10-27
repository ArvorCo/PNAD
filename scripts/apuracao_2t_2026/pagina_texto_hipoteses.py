"""Textos do capítulo "O que poderia ter acontecido, e o que os dados dizem de cada hipótese".

Cada número vem de ``hipoteses.json`` (gerado por
``scripts/apuracao-2t-2026-hipoteses.py`` a partir dos outros JSONs do acervo).
Regra de escrita: fato, inferência, juízo e hipótese separados por selo; cada
frase contenciosa diz de quem é a conclusão; nunca "fraude"; sem travessão.
"""

from __future__ import annotations

from html import escape

from apuracao_2026.pagina_comum import (
    caixa,
    cartao,
    inteiro,
    limites,
    nota,
    num,
    p,
    rotulo,
    sinal,
    tabela,
)

ESTILO_ESTADO = {
    "descartada": ("#cfe5d6", "#173d28"),
    "compativel": ("#f2dfb0", "#4d3a00"),
    "pendente": ("#dcd6ec", "#33295a"),
}
ESTILO_RES = {
    "exclui": ("#cfe5d6", "#173d28"),
    "não exclui": ("#f2dfb0", "#4d3a00"),
    "pendente": ("#dcd6ec", "#33295a"),
    "não se aplica": ("#f4f0e6", "#535b54"),
}
# Na página, o código "exclui" do JSON diz só que a marca esperada não aparece nos
# arquivos públicos; "não exclui", que o teste não alcança o mecanismo.
ROTULO_RES = {
    "exclui": "marca ausente",
    "não exclui": "não alcança",
    "pendente": "pendente",
    "não se aplica": "não se aplica",
}


def chip(texto: str, fundo: str, letra: str) -> str:
    return (
        f'<span style="display:inline-block;padding:2px 9px;border-radius:4px;background:{fundo};'
        f'color:{letra};font-weight:700;font-size:15px;white-space:nowrap">{escape(texto)}</span>'
    )


def estado(H: dict, ident: str, alcance: bool = True) -> str:
    hp = next(h for h in H["hipoteses"] if h["id"] == ident)
    e = hp["estado"]
    c = chip(H["estados"][e], *ESTILO_ESTADO[e])
    return f"{c} <small>{escape(hp['alcance'])}</small>" if alcance else c


def resultado(res: str) -> str:
    return chip(ROTULO_RES.get(res, res), *ESTILO_RES[res])


def ic(b: dict, casas: int = 2) -> str:
    lo, hi = b["ic95_pp"]
    return f"IC95 de {sinal(lo, casas)} a {sinal(hi, casas)}"


def _uf_lista(xs: list[str]) -> str:
    return ", ".join(xs)


def _horas(minutos: int) -> str:
    h, m = divmod(int(minutos), 60)
    return f"{h}h{m:02d}" if h else f"{m} minutos"


def _metricas(v: dict) -> str:
    m = v.get("metricas_na_captura")
    if not m:
        return ""
    c = v["capturado_em"]
    return f" ({m['curtidas']} curtidas e {m['comentarios']} comentários na captura de {c[8:10]}/{c[5:7]}, às {c[11:16]})"


# ------------------------------------------------------------------ abertura


def lead(H: dict) -> str:
    n = {
        k: sum(1 for h in H["hipoteses"] if h["estado"] == k)
        for k in ("descartada", "compativel", "pendente")
    }
    return (
        f"Seis mecanismos, o mesmo esqueleto para cada um e oito testes. {n['descartada']} ficam sem a marca "
        f"que deixariam nos dados, {n['pendente']} dependem de documento que ninguém publicou e "
        f"{n['compativel']} é compatível com tudo o que se mediu sem que nada a identifique."
    )


def como_ler(H: dict) -> str:
    return caixa(
        "io",
        "Como ler este capítulo",
        " Cada hipótese é um mecanismo possível, escrito como alguém que quisesse explicar o resultado o escreveria. "
        "Para cada uma: como seria, a marca que deixaria nos dados, o que os dados mostram e o que ainda falta. "
        f"Os selos separam {rotulo('verificado')}, {rotulo('inferencia')}, {rotulo('juizo')} e {rotulo('hipotese')}. "
        "Hipótese não é acusação: é roteiro de teste. Descartar um mecanismo quer dizer que a marca que ele deixaria "
        f"não está nos arquivos públicos, não que alguém tenha sido inocentado ou acusado. Regra da casa: {H['rotulo']}.",
    )


def cartoes(H: dict) -> str:
    s = H["cronologia"]["silencio"]
    h1, h2 = H["h1"], H["h2"]
    return (
        '<div class="finding-grid">'
        + cartao(
            f"{num(h1['pct_17_19'], 3)}%",
            "dos votos do dia computados entre 17h e 19h de Brasília",
        )
        + cartao(
            inteiro(h2["vsc_bu_igual"]), "BUs publicados iguais ao que a urna assinou"
        )
        + cartao(
            f"{num(s['minutos'], 1)} min",
            "sem o TSE gerar arquivo algum, das 17:07 às 19:01",
        )
        + cartao(
            f"{H['h6']['casas_mesmo_sentido']} de {H['h6']['casas']}",
            "casas com o erro no mesmo sentido",
        )
        + "</div>"
    )


def documentado(H: dict) -> str:
    c = H["cronologia"]
    m = {x["hora"][:5]: x for x in c["marcos"]}
    v = c["video"]
    u = c["urnas"]
    s = c["silencio"]
    stf = c["marcos"][2]
    pr = v["primeira_republicacao"]
    h = "<h3>O que está documentado</h3>"
    h += p(
        f"Em matéria publicada às {m['12:47']['hora']}, O Globo informou que o TRE-BA mandou prender o secretário de Mobilidade de Salvador e "
        f"restabelecer a frota. Às 16:16 o Procon-BA contava 370 ônibus parados; às 17:09, 544, em cinco garagens "
        f"(Agência Brasil). O pedido da coligação de Lula ao STF, na Reclamação 101673, chegou com carimbo citado "
        f"como {stf['carimbos_citados'][0]} (Agência Brasil) ou {stf['carimbos_citados'][1]} (O Globo, que transcreve "
        f"a decisão). No TSE, onde as duas campanhas também haviam pedido prorrogação, a Procuradoria-Geral Eleitoral opinou contra; o parecer chegou às 17:01. "
        f"O ministro Cristiano Zanin prorrogou a votação até 19h por volta das 17:03. O TSE avisou as seções às 17:49, "
        f"{H['h4']['aviso_depois_da_decisao_min']} minutos depois. O TRE-SP disse ter recebido o aviso oficial às 18:17, "
        "com mais de 80% das seções de São Paulo já fechadas. Às 18:08 Zanin restringiu a decisão às seções "
        "ainda abertas.",
        "verificado",
    )
    b = s["banco"]
    h += p(
        f"Entre {s['inicio']} e {s['fim']} o TSE não gerou nenhum arquivo, de nenhum tipo, nos dois pleitos: "
        f"{num(s['minutos'], 1)} minutos, com {inteiro(s['leituras_no_intervalo'])} leituras do nosso coletor no "
        f"intervalo e {s['versoes_geradas_dentro']} versões novas. Só no arquivo nacional de presidente, a lacuna vai "
        f"da versão de {b['versao_brt']} à de {b['proxima_brt']}, {num(b['lacuna_min'], 1)} minutos: a primeira conta "
        "olha todos os arquivos; a segunda, só esse. A última versão antes da pausa tinha "
        f"{inteiro(b['secoes'])} seções totalizadas, com Lula a {num(b['lula_pct'], 2)}% nessa fração. "
        "Nas urnas, o encerramento do BU (último cômputo registrado) teve "
        f"mediana às {u['encerramento_p50']} e a emissão do BU às {u['emissao_p50']}; {num(u['pct_ate_1715'], 2)}% "
        f"das seções encerraram até 17:15 e só {num(u['pct_apos_1900'], 2)}% depois das 19h. O recebimento dos BUs "
        f"pelo TSE teve mediana às {u['recebimento_p50']}: {num(u['pct_recebido_antes_1900'], 2)}% chegaram antes das 19h.",
        "verificado",
    )
    rep = (
        f"A primeira republicação que localizamos é de {pr['veiculo']}, às {pr['hora_brt']}, pelo carimbo da própria "
        f"página; arquivamos {len(v['republicacoes'])} republicações com hora. "
        if pr
        else ""
    )
    h += p(
        f"O vídeo com a marca 342 Artes, em que Caetano Veloso e Camila Pitanga denunciam a redução das frotas em "
        f"Salvador e São Paulo e pedem extensão do horário de votação na Bahia e em São Paulo, foi publicado no "
        f"Instagram às {v['publicado_brt_segundos']} de Brasília pelo perfil {v['perfil']}, com coautores, pelo "
        f"carimbo da plataforma{_metricas(v)}: de {H['h4']['video_antes_da_peticao_faixa_min'][0]} a "
        f"{H['h4']['video_antes_da_peticao_faixa_min'][1]} minutos antes dos carimbos citados para o pedido ao STF e "
        f"{_horas(H['h4']['video_antes_da_decisao_min'])} antes da decisão. {rep}A cópia que recebemos foi reexportada às 04:04 de 26/10 e não guarda a data de gravação.",
        "verificado",
    )
    h += nota(
        "hipotese",
        "Que o vídeo tenha sido gravado de manhã, antes do fato que denuncia, e guardado até o fim da tarde é "
        f"hipótese do autor. Contra ela, o documentado: a ordem de prisão do secretário saiu em matéria às "
        f"{m['12:47']['hora']} e os ônibus parados eram notícia desde o início da tarde, horas antes da publicação "
        f"às {v['publicado_brt_segundos']}. A cópia recebida não sustenta nem derruba a hipótese: a hora de gravação "
        "só aparece no arquivo original de quem gravou. O carimbo da plataforma prova a hora da publicação, não a da "
        "produção.",
    )
    return h


def tabela_marcos(H: dict) -> str:
    linhas = []
    for x in H["cronologia"]["marcos"]:
        linhas.append(
            [
                x["hora"][:5],
                escape(x["rotulo"]),
                f'<a href="{escape(x["url"])}" rel="noopener">{escape(x["veiculo"])}</a>',
                rotulo(
                    {
                        "fato": "verificado",
                        "relato": "relato",
                        "declaracao": "relato",
                    }.get(x["tipo"], "relato")
                ),
            ]
        )
    return tabela(
        ["Hora", "Marco", "Fonte", "Natureza"],
        linhas,
        "Marcos da tarde com a fonte de cada um",
    )


def fato_e_hipotese() -> str:
    return (
        "<h3>O que é fato e o que é hipótese</h3>"
        + p(
            "São fatos com fonte: a decisão, os horários do pedido, do parecer e do aviso, a contagem de ônibus parados, "
            "a ordem de prisão, a publicação do vídeo antes da decisão e o silêncio de 114 minutos do TSE, que o nosso "
            "banco registrou arquivo a arquivo.",
            "verificado",
        )
        + p(
            "São hipóteses: que a prorrogação tenha sido parte de um plano; que o silêncio tenha servido a outra coisa "
            "além da decisão judicial; que o vídeo tenha sido preparado antes do fato que denuncia; que algo tenha sido "
            "feito nas urnas ou na soma. Nenhuma delas está provada, e algumas estão descartadas pelos dados abaixo.",
            "hipotese",
        )
    )


# ------------------------------------------------------------------ hipóteses


def _esqueleto(
    H: dict,
    ident: str,
    como: str,
    marca: str,
    mostram: list[str],
    falta: str,
    extra: str = "",
) -> str:
    hp = next(h for h in H["hipoteses"] if h["id"] == ident)
    lis = "".join(f"<li>{x}</li>" for x in mostram)
    return (
        f'<h3 id="hip-{ident}">{ident.upper()}. {escape(hp["titulo"])}</h3>'
        f"<p>{estado(H, ident)}</p>"
        f"<p><b>Como seria.</b> {como}</p>"
        f"<p><b>A marca que deixaria nos dados.</b> {marca}</p>"
        f"<p><b>O que os dados mostram.</b> {rotulo('verificado')}</p><ul>{lis}</ul>"
        f"{extra}<p><b>O que ainda falta.</b> {falta}</p>"
    )


def h1(H: dict) -> str:
    x = H["h1"]
    return _esqueleto(
        H,
        "h1",
        "Seções escolhidas ficam abertas até 19h sob a cobertura da prorrogação, e alguém vota por eleitores "
        "ausentes, habilitados por ano de nascimento.",
        "Votos computados depois das 17h em quantidade que pese na margem; seções tardias com o voto deslocado "
        "contra as vizinhas e contra o próprio 1º turno; rajadas de habilitação sem biometria no fim do dia.",
        [
            f"Entre 17h e 19h de Brasília as urnas computaram {inteiro(x['computados_17_19'])} votos, "
            f"{num(x['pct_17_19'], 3)}% dos {num(x['computados'] / 1e6, 1)} milhões do dia; depois das 19h, "
            f"{inteiro(x['computados_depois_19'])}. No 1º turno, com cinco cargos e seis votos, a parcela entre 17h e 19h foi "
            f"{num(x['pct_17_19_1t'], 2)}%. A margem de Lula é de {inteiro(x['margem_votos'])} votos.",
            f"{inteiro(x['bus_apos_19h'])} BUs foram encerrados depois das 19h; em "
            f"{inteiro(x['bus_apos_19h_ultimo_voto_ate_1715'])} deles o último voto foi até 17:15. A urna ficou "
            "ligada sem receber voto depois do horário normal.",
            f"As {inteiro(x['apos_19h']['secoes'])} seções encerradas depois das 19h já eram "
            f"{num(x['apos_19h']['contra_vizinhas_pp'], 2)} pp mais favoráveis a Flávio que as vizinhas; contra o "
            f"próprio 1º turno, a diferença em diferenças é {sinal(x['apos_19h']['did_pp'], 2)} pp "
            f"({ic(x['apos_19h'])}). Com a regra mais larga de tardia ({inteiro(x['tardias']['secoes'])} seções), "
            f"{sinal(x['tardias']['did_pp'], 2)} pp ({ic(x['tardias'])}).",
        ],
        "A ata de cada seção tardia, que registra quem chegou depois das 17h e por quê. Os logs dizem quando o "
        "voto entrou, não quem estava na fila.",
    )


def h2(H: dict) -> str:
    x = H["h2"]
    z = x["zona"] or {}
    zona = (
        f"A soma dos BUs de presidente fecha com o arquivo de zona do TSE em {inteiro(z['zonas_conferem'])} de "
        f"{inteiro(z['zonas'])} zonas ({inteiro(z['secoes_conferidas'])} seções); nenhuma diverge."
        + (
            " A soma das UFs fecha com o arquivo nacional sem diferença em nenhum campo."
            if x["soma_ufs_menos_nacional"]
            and not any(x["soma_ufs_menos_nacional"].values())
            else ""
        )
        if z
        else "A conferência por zona depende do banco local, ausente nesta execução."
    )
    return _esqueleto(
        H,
        "h2",
        "O alvo não é a urna, é a soma. Durante as duas horas sem publicação, BUs seriam substituídos ou somados "
        "fora de ordem entre o recebimento e a divulgação, sem que o público visse versões intermediárias.",
        "BU publicado diferente do que a urna assinou; RDV ou log que não batem com o BU; soma das seções diferente "
        "do arquivo de zona, UF ou Brasil; BUs do sistema de apuração em número anormal ou fora do exterior.",
        [
            f"Os {inteiro(x['vsc_ok'])} arquivos de assinatura (<code>.vsc</code>) lidos têm cadeia válida até a "
            f"autoridade certificadora em {inteiro(x['vsc_cadeia'])}, assinatura da urna sobre o BU válida em "
            f"{inteiro(x['vsc_assinatura_bu'])} e o BU publicado igual ao resumo assinado em "
            f"{inteiro(x['vsc_bu_igual'])}; {x['vsc_falhas']} falhas.",
            f"O registro digital do voto bate com o BU em {inteiro(x['rdv_confere'])} de {inteiro(x['rdv_ok'])} "
            f"seções; o log da urna, em {inteiro(x['log_confere'])} de {inteiro(x['log_lidos'])} (nas "
            f"{x['log_nao_confere']} restantes o log tem menos registros que o BU, todas com urna religada ou de "
            "contingência).",
            zona,
            f"Os {x['sistema_apuracao_secoes']} BUs do sistema de apuração estão todos em {_uf_lista(x['sistema_apuracao_ufs'])} "
            "(exterior), e os registros de voto deles conferem com o BU.",
            f"A totalização paralela conferiu {inteiro(x['paralela'].get('igual', 0))} BUs impressos, lidos por QR "
            "nas seções, e todos são iguais aos publicados.",
        ],
        "Por que o recebimento dos BUs pelo TSE só ganhou ritmo depois das 19h (mediana às "
        f"{x['recebimento_p50']}) e por que a divulgação parou por inteiro. Os arquivos mostram o efeito, não a "
        "causa; a justificativa do TSE pode ser pedida pela Lei de Acesso à Informação.",
        nota(
            "inferencia",
            "Se as somas fecham e cada BU é o que a urna assinou, qualquer deslocamento teria de ter acontecido "
            "antes da assinatura, dentro das urnas ou entre os eleitores. Na totalização, a marca esperada não "
            "aparece nos arquivos públicos; o teste não alcança o que veio antes da assinatura.",
        ),
    )


def h3(H: dict) -> str:
    x = H["h3"]
    t0, _, t2 = x["tercos"]
    reg = x["regioes"]
    return _esqueleto(
        H,
        "h3",
        "Mobilização de última hora onde Lula é forte, com ônibus e com a prorrogação garantindo que quem chegasse "
        "tarde votasse.",
        "Comparecimento subindo mais no Nordeste e nas periferias, concentrado na última hora; abstenção caindo mais "
        "onde Lula é forte; variação da abstenção acompanhando o resíduo de Flávio entre as UFs.",
        [
            f"Em três grupos de municípios com o mesmo eleitorado, ordenados pela força de Flávio no 1º turno, a "
            f"abstenção variou {sinal(t0['abstencao_variacao_pp'], 2)} pp onde Flávio era mais fraco, "
            f"{sinal(x['tercos'][1]['abstencao_variacao_pp'], 2)} no meio e {sinal(t2['abstencao_variacao_pp'], 2)} "
            "onde era mais forte: a queda foi praticamente a mesma nos três.",
            f"O comparecimento subiu mais no Sudeste ({sinal(reg['Sudeste']['comparecimento_pp'], 2)} pp) e no Sul "
            f"({sinal(reg['Sul']['comparecimento_pp'], 2)}) que no Nordeste ({sinal(reg['Nordeste']['comparecimento_pp'], 2)}); "
            f"no Norte caiu ({sinal(reg['Norte']['comparecimento_pp'], 2)}).",
            f"Na Bahia, onde os ônibus pararam, Flávio perdeu {num(-x['bahia']['deslocamento_flavio_pp'], 2)} pp na parte "
            "entre os dois finalistas, do 1º para o 2º turno, somados os municípios, menos que o país na mesma régua "
            f"({num(-x['brasil_deslocamento_pp'], 2)}).",
            f"Entre as UFs, a correlação da variação da abstenção com o resíduo de Flávio é "
            f"{num(x['correlacao_uf_abstencao_residuo'], 2)}. Mesmo dando a Lula todo o aumento líquido de "
            f"comparecimento, ele explica no máximo {num(x['teto_comparecimento_pp'], 2)} pp; a matriz de transferência "
            f"estima {num(x['ipf_explica_pp'], 2)} pp (IC de {num(x['ipf_explica_ic'][0], 2)} a "
            f"{num(x['ipf_explica_ic'][1], 2)}).",
            f"A última hora do dia (16h) teve {num(x['ultima_hora_2t'], 2)}% dos votos, contra "
            f"{num(x['ultima_hora_1t'], 2)}% no 1º turno, na amostra de uma seção em cinco lida nos dois turnos: "
            "o fim do dia não inchou.",
        ],
        "O inquérito da Polícia Federal sobre retenção de ônibus e as listas de frota das empresas. Mobilização "
        "antes das 17h não deixa marca própria no BU; o que os dados dizem é que ela, se houve, não tem o tamanho "
        "do deslocamento.",
    )


def h4(H: dict) -> str:
    x = H["h4"]
    return _esqueleto(
        H,
        "h4",
        "Não há intervenção na urna nem na soma. O que se planeja é a explicação pública: petição e vídeo prontos, "
        "extensão nacional para um problema local, silêncio de duas horas e a ordem dos lotes produzindo a história "
        "de que o comparecimento virou a eleição.",
        "Peças de comunicação publicadas antes do fato que as justificaria; pedido protocolado logo depois da peça; "
        "retenção da divulgação sem justificativa técnica publicada.",
        [
            f"O vídeo foi publicado no Instagram às {H['cronologia']['video']['publicado_brt_segundos']}, de "
            f"{x['video_antes_da_peticao_faixa_min'][0]} a {x['video_antes_da_peticao_faixa_min'][1]} minutos antes "
            f"dos carimbos citados para o pedido ao STF ({' e '.join(x['stf_carimbos'])}) e "
            f"{_horas(x['video_antes_da_decisao_min'])} antes da decisão. A hora de produção não está estabelecida. Os ônibus parados em Salvador eram notícia desde o início da tarde, e a "
            "ordem de prisão do secretário é anterior às duas peças.",
            f"O aviso às seções veio {x['aviso_depois_da_decisao_min']} minutos depois da decisão, quando a maioria "
            f"já tinha fechado. A divulgação ficou {num(x['silencio_min'], 1)} minutos parada.",
            "A campanha de Flávio também pediu prorrogação ao TSE, por chuva, alagamentos e falta de energia, e pediu "
            "que a divulgação só começasse depois do fim da votação nesses locais (Poder360, 16:54).",
        ],
        "A íntegra da Reclamação 101673 e dos anexos, a justificativa do TSE para suspender a divulgação, e o "
        "arquivo original do vídeo com a data de gravação.",
        nota(
            "hipotese",
            "A sequência de horários é compatível com ação coordenada e com ações independentes; só a íntegra da "
            "Reclamação e o original do vídeo separam as duas. Pedir prorrogação à Justiça e publicar um vídeo são "
            "atos permitidos a qualquer campanha.",
        )
        + p(
            "A cronologia não prova intervenção em voto, e os dados de urna não ligam a prorrogação ao resultado: "
            "quase nenhuma urna recebeu voto depois das 17h.",
            "inferencia",
        ),
    )


def _cargas(x: dict) -> str:
    """Cargas entre os turnos: contagem do log e separação pelos ``.vsc`` dos dois turnos."""
    if x.get("cargas_entre_turnos") is None:
        return ""
    t = f" Entre os turnos, {inteiro(x['cargas_entre_turnos'])} urnas têm carga registrada no log."
    v = x.get("cargas_vsc")
    if v:
        de, ate = v["carga_nova_de"], v["carga_nova_ate"]
        t += (
            " A comparação dos <code>.vsc</code> dos dois turnos separa os casos: "
            f"{inteiro(v['mesma_urna_carga_nova'])} seções mantiveram a urna e receberam carga nova, de "
            f"{de[8:10]}/{de[5:7]} a {ate[8:10]}/{ate[5:7]}, e {inteiro(v['urna_trocada'])} trocaram de urna; "
            f"nenhuma carga nova cai fora do intervalo entre os turnos ({v['carga_nova_fora_do_intervalo']}). "
            "O motivo de cada recarga e de cada troca não está nos arquivos lidos."
        )
    return t


def h5(H: dict) -> str:
    x = H["h5"]
    M = H["banco"]["modelo"]
    mod = (
        f"O deslocamento da fatia de Flávio do 1º para o 2º turno, na mesma seção, vai de "
        f"{sinal(min(m['deslocamento_pp'] for m in M['modelos'] if m['secoes'] >= 1000), 2)} a "
        f"{sinal(max(m['deslocamento_pp'] for m in M['modelos'] if m['secoes'] >= 1000), 2)} pp entre os quatro modelos; "
        f"descontado o município, a maior diferença entre modelos é {num(x['modelo_amplitude_pp'], 2)} pp."
        if M
        else "O deslocamento por modelo depende do banco local, ausente nesta execução."
    )
    return _esqueleto(
        H,
        "h5",
        "Intervenção no software ou na carga da urna, antes ou durante a votação, mudando a contagem.",
        "Versão de software fora do padrão; carga depois da abertura; ID, código de carga ou certificado repetidos "
        "onde não deveriam; reinício no meio da votação com mudança de voto; deslocamento diferente por modelo.",
        [
            f"Uma única versão de software em todas as {inteiro(x['versao_secoes'])} seções: {escape(x['versao'])}.",
            f"O ID da urna do BU está no log em {inteiro(x['id_bu_no_log'])} seções, e o código de carga em "
            f"{inteiro(x['carga_bu_no_log'])}. Nenhuma carga depois da abertura da votação "
            f"({x['carga_depois_da_abertura']}).{_cargas(x)} "
            f"IDs repetidos: {x['ids_repetidos_secoes']} seções, todas do sistema de apuração; sem explicação, "
            f"{x['ids_repetidos_sem_explicacao']}.",
            mod,
            f"Memória de resultado com a mesma série em várias urnas da zona ({inteiro(x['mr_repetida_secoes'])} seções "
            f"no Brasil): diferença em diferenças {sinal(x['mr_repetida']['media_pp'], 2)} pp ({ic(x['mr_repetida'])}).",
            f"Sistema religado durante a votação em {inteiro(x['reinicios_secoes'])} seções: "
            f"{sinal(x['reinicios']['media_pp'], 2)} pp ({ic(x['reinicios'])}). Urna trocada entre os turnos: "
            f"{sinal(x['urnas_trocadas']['media_pp'], 2)} pp ({ic(x['urnas_trocadas'])}).",
            f"A mensagem de erro ao desmontar a memória de resultado antes da zerésima aparece em "
            f"{inteiro(x['mr_antes_zeresima'])} seções: é a rotina da urna religada com a carga de setembro, não "
            "erro do dia.",
        ],
        "A assinatura de software das urnas (bloco do TSE no <code>.vsc</code>) não foi verificada aqui; só o resumo. "
        "Conferir essa assinatura e os resumos do sistema contra os publicados pelo TSE na cerimônia de lacração é o "
        "que testaria uma alteração igual em todas as urnas, que não deixaria marca por modelo nem por versão.",
    )


def _presenca(x: dict) -> str:
    """Presença relativa necessária, comparada dentro do mesmo motor quando o número existe."""
    fora = (
        f"Por fora do motor, sem o ajuste de presença que a casa já aplicava, a razão entre os votos de Flávio e "
        f"de Lula na Média Arvor teria de cair {num(-x['presenca_relativa_necessaria_pct'], 1)}%."
    )
    if x.get("presenca_necessaria_motor_pct") is None:
        return (
            f"<li>{fora} O cenário do autor usou {sinal(x['autor_cenario_pct'], 1)}%. Nenhuma pesquisa mediu "
            "presença diferencial desse tamanho.</li>"
        )
    return (
        "<li>No motor da casa, com o comparecimento e os brancos e nulos da urna, a presença relativa de Flávio que "
        f"reproduz a urna é {sinal(x['presenca_necessaria_motor_pct'], 1)}%; o cenário do autor usou "
        f"{sinal(x['autor_cenario_pct'], 1)}% no mesmo motor. {fora} Nenhuma pesquisa mediu presença diferencial "
        "desse tamanho.</li>"
    )


def _erro_comum(x: dict) -> str:
    """Precedente: erro comum das casas a favor de Lula nos 1º turnos de 2022 e de 2026."""
    pr = x.get("erro_comum_precedentes") or []
    if not pr:
        return ""
    casos = "; ".join(
        f"no {c['turno']}, {sinal(c['erro_pp'], 2)} pp em {c['diferenca']}, com {c['mesmo_sentido']} de "
        f"{c['casas']} casas do mesmo lado"
        for c in pr
    )
    return (
        "<li>Erro comum, com a maioria das casas do mesmo lado, não exige mudança de última hora: apareceu também "
        f"{casos}. Nesses turnos, o desenho é compatível com viés de método comum às casas ou com casas que "
        "convergem umas para as outras (herding), e as mesmas duas leituras cabem aqui.</li>"
    )


def h6(H: dict) -> str:
    x = H["h6"]
    pd = "; ".join(
        f"{d['instituto']} {sinal(d['deslocamento_f_menos_l'], 2)} pp"
        for d in x["presenca_declarada"]
    )
    sustenta = (
        "<p><b>O que sustenta.</b></p><ul>"
        f"<li>{x['casas_mesmo_sentido']} de {x['casas']} casas erraram no mesmo sentido, em média "
        f"{sinal(x['erro_medio_pp'], 2)} pp em Flávio menos Lula, com dispersão de {num(x['dispersao_pp'], 2)} pp, "
        f"menor que os {num(x['dispersao_amostral_pp'], 2)} pp que a amostragem sozinha daria: as casas mediram a "
        "mesma coisa, e o eleitorado se afastou dela por igual.</li>"
        f"<li>A geografia veio certa: transportado o 1º turno, Flávio ficou abaixo do previsto em "
        f"{x['ufs_flavio_abaixo']} de {x['ufs']} UFs, com desvio comum de {num(x['vies_comum_pp'], 2)} pp e erro de "
        f"só {num(x['rmse_sem_vies_pp'], 2)} pp depois de descontá-lo.</li>"
        f"<li>Cerca de {num(x['voltaram_milhoes'], 2)} milhões que faltaram no 1º turno votaram no 2º, "
        f"{num(x['voltaram_lula_pct'], 1)}% deles em Lula pela matriz da casa (IC de "
        f"{num(x['voltaram_lula_ic'][0], 1)} a {num(x['voltaram_lula_ic'][1], 1)}); pela regressão, de cada 100 "
        f"votantes a mais, {num(x['por_100_lula_secoes'], 0)} (seções) a {num(x['por_100_lula_municipios'], 0)} "
        "(municípios) foram para Lula.</li>"
        f"<li>A terceira via rendeu a Flávio {num(x['terceira_flavio_pct'], 1)}% do seu estoque (faixa de "
        f"{num(x['terceira_flavio_faixa'][0], 1)} a {num(x['terceira_flavio_faixa'][1], 1)}), contra "
        f"{num(x['pesquisas_flavio_do_estoque'][0], 1)} a {num(x['pesquisas_flavio_do_estoque'][1], 1)}% medidos "
        "pelas pesquisas.</li></ul>"
    )
    contraria = (
        "<p><b>O que contraria.</b></p><ul>"
        f"<li>A tendência publicada já era de Flávio perdendo terreno ({sinal(x['tendencia_pp_dia'], 3)} pp por dia "
        "dentro de cada casa): parte da mudança pode ter começado antes do sábado. Mesmo assim, levada até a urna, "
        f"daria Flávio {sinal(x['tendencia_extrapolada_f_menos_l'], 2)} pp, longe dos "
        f"{sinal(x['urna_f_menos_l'], 2)} da urna.</li>"
        f"<li>O comparecimento sozinho explica no máximo {num(x['teto_comparecimento_pp'], 2)} pp do erro.</li>"
        f"<li>Os filtros de presença declarada publicados apontaram para Flávio ({pd}), na direção oposta à urna: "
        "a presença declarada não antecipou quem compareceu.</li>"
        + _presenca(x)
        + _erro_comum(x)
        + "</ul>"
    )
    return (
        f'<h3 id="hip-h6">H6. {escape(next(h["titulo"] for h in H["hipoteses"] if h["id"] == "h6"))}</h3>'
        f"<p>{estado(H, 'h6')}</p>"
        + p(
            "As pesquisas e a régua de renda mediram certo até o último campo, em 23 e 24 de outubro, e entre "
            "sábado e domingo o eleitorado mudou: parte de opinião, parte de quem foi votar. É a tese do autor do dossiê.",
            "juizo",
        )
        + "<p><b>A marca que deixaria nos dados.</b> Erro de mesmo sinal em todas as casas, dispersão pequena entre "
        "elas, geografia preservada com o nível deslocado, voto novo pendendo para um lado.</p>"
        + sustenta
        + contraria
        + "<p><b>O que ainda falta.</b> Nada que exista: não houve medição entre o último campo e a urna. "
        "A tese não tem como ser identificada pelos dados públicos, só tornada mais ou menos compatível.</p>"
    )


# ------------------------------------------------------------------ discriminador e quadro


def discriminador(H: dict) -> str:
    x = H["h6"]
    return "<h3>O discriminador: o mesmo deslocamento serve a duas leituras</h3>" + p(
        f"O deslocamento foi uniforme: Flávio abaixo do previsto em {x['ufs_flavio_abaixo']} de {x['ufs']} UFs, "
        f"{num(x['vies_comum_pp'], 2)} pp em comum e {num(x['rmse_sem_vies_pp'], 2)} pp de resto. Isso é compatível "
        "com uma mudança real e nacional entre quem compareceu, e também com um deslocamento aplicado por igual. "
        "Os testes abaixo separam as duas leituras onde podem.",
        "inferencia",
    )


def tabela_testes(H: dict) -> str:
    linhas = [
        [
            escape(t_["teste"]),
            escape(t_["pergunta"]),
            resultado(t_["resultado"]),
            escape(t_["o_que"]),
        ]
        for t_ in H["discriminador"]
    ]
    return tabela(
        ["Teste", "Pergunta", "Resultado", "O que o resultado alcança"],
        linhas,
        "Os oito testes",
    )


def tabela_modelos(H: dict) -> str:
    M = H["banco"]["modelo"]
    if not M:
        return ""
    linhas = [
        [
            escape(m["modelo"]),
            inteiro(m["secoes"]),
            sinal(m["deslocamento_pp"], 2),
            sinal(m["dentro_do_municipio_pp"], 3),
            f"{sinal(m['ic95_pp'][0], 3)} a {sinal(m['ic95_pp'][1], 3)}",
        ]
        for m in M["modelos"]
    ]
    return (
        "<details><summary>O deslocamento por modelo de urna</summary>"
        + tabela(
            [
                "Modelo",
                "Seções",
                "Deslocamento (pp)",
                "Contra o município (pp)",
                "IC95",
            ],
            linhas,
            f"Fatia de Flávio entre os dois, 2º turno menos 1º, na mesma seção; {inteiro(M['secoes'])} seções com "
            f"{M['minimo_votos']} votos ou mais nos dois turnos, sem exterior. Erro-padrão agrupado por município.",
        )
        + p(
            "Diferenças de centésimos de ponto. Uma delas tem intervalo que não toca o zero, e o tamanho dela, "
            "de um centésimo, não move nenhuma seção.",
            "inferencia",
        )
        + "</details>"
    )


def tabela_tercos(H: dict) -> str:
    linhas = [
        [
            escape(x["grupo"]),
            inteiro(x["municipios"]),
            f"{num(x['flavio_1t_min'], 1)} a {num(x['flavio_1t_max'], 1)}%",
            sinal(x["abstencao_variacao_pp"], 2),
            sinal(x["deslocamento_flavio_pp"], 2),
        ]
        for x in H["h3"]["tercos"]
    ]
    return (
        "<details><summary>Abstenção × força de Flávio, em três grupos de mesmo eleitorado</summary>"
        + tabela(
            [
                "Grupo",
                "Municípios",
                "Flávio no 1º turno",
                "Abstenção (pp)",
                "Deslocamento de Flávio (pp)",
            ],
            linhas,
            "Variação contra o 1º turno, ponderada pelo eleitorado; sem exterior.",
        )
        + p(
            "A abstenção caiu o mesmo nos três grupos, e Flávio perdeu mais onde era mais forte. Em pontos "
            "percentuais, parte disso é aritmética: o mesmo deslocamento em proporção pesa mais perto de 50%.",
            "inferencia",
        )
        + "</details>"
    )


def quadro(H: dict) -> str:
    decide = {
        "h1": "ata das seções tardias",
        "h2": "justificativa do TSE para o silêncio (a soma já fecha)",
        "h3": "inquérito da PF e frota das empresas",
        "h4": "íntegra da Reclamação 101673, original do vídeo, justificativa do TSE",
        "h5": "assinatura de software e resumos do sistema conferidos contra o TSE",
        "h6": "nada que exista: não houve medição entre o último campo e a urna",
    }
    linhas = [
        [
            f"{h['id'].upper()}. {escape(h['titulo'])}",
            estado(H, h["id"]),
            escape(decide[h["id"]]),
        ]
        for h in H["hipoteses"]
    ]
    return (
        "<h3>Quadro-resumo</h3>"
        + tabela(
            ["Hipótese", "Estado", "O que decidiria"],
            linhas,
            "As seis hipóteses e o estado de cada uma",
        )
        + p(
            "Descartada quer dizer que a marca que o mecanismo deixaria não está nos arquivos públicos. Compatível quer "
            f"dizer que os dados admitem o mecanismo e nenhum teste o isola. Regra da casa: {H['rotulo']}.",
            "inferencia",
        )
        + nota(
            "juizo",
            "A leitura do autor do dossiê é a H6: o eleitorado mudou entre sábado e domingo, em opinião e em quem foi "
            "votar. As outras ficam publicadas com o mesmo cuidado porque é o que a casa faz com a própria tese. Nas "
            "palavras dele, na noite da apuração: “se foi isso mesmo, não saberemos”.",
        )
    )


def limites_itens(H: dict) -> list[str]:
    return [
        "Os horários da tarde vêm do noticiário, com a fonte de cada um; o banco do coletor só registra o silêncio "
        "do TSE, não a causa.",
        "Os carimbos de republicação do vídeo são os das páginas arquivadas; a página sem fuso no carimbo foi lida "
        "como hora de Brasília.",
        "Diferença em diferenças compara seções com sinal contra vizinhas e contra o próprio 1º turno; não identifica "
        "efeito causal.",
        f"Conferência por zona e deslocamento por modelo: {escape(H['banco']['origem'])}.",
        "Hipótese descartada pelos dados públicos pode reaparecer com documento novo; o capítulo será refeito se "
        "a ata, a íntegra da Reclamação ou o original do vídeo vierem a público.",
    ]


def fecho(H: dict) -> str:
    return limites(limites_itens(H))
