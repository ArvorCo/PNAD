"""Textos do capítulo "O que os logs das 499 mil urnas dizem".

Todo número sai de ``logs.json`` (``scripts/apuracao-2t-2026-logs.py``). Cada bloco
abre pelo número mais forte; fato, inferência, hipótese e juízo vêm com o selo da
casa. Rótulo fixo: pede explicação, não prova irregularidade.
"""

from __future__ import annotations

from html import escape

from apuracao_2026.pagina_comum import (
    caixa,
    cartao,
    inteiro,
    nota,
    num,
    p,
    sinal,
    tabela,
)

ROTULO = "Pede explicação, não prova irregularidade."


def _ic(b: dict, casas: int = 2) -> str:
    lo, hi = b["ic95_pp"]
    return f"{sinal(b['media_pp'], casas)} ponto (IC95 de {sinal(lo, casas)} a {sinal(hi, casas)}; {inteiro(b['n'])} seções)"


def _zero_dentro(b: dict) -> bool:
    lo, hi = b["ic95_pp"]
    return lo <= 0 <= hi


def _voto(L: dict, grupo: str) -> dict:
    for v in L["reinicios"]["voto"] + L["bateria"]["voto"]:
        if v["grupo"] == grupo:
            return v
    raise KeyError(grupo)


# ------------------------------------------------------------------ cabeça


def titulo(L: dict) -> str:
    return "O que os logs das <em>499 mil urnas</em> dizem"


def lead(L: dict) -> str:
    b = L["cadencia"]["brasil_2t"]
    a = L["cadencia"]["amostra_1t"]["brasil_1t"]
    return (
        f"Depois das 17h de Brasília, as urnas do 2º turno computaram {inteiro(b['computados_17_19'] + b['computados_depois_19'])} "
        f"votos de {num(b['computados'] / 1e6, 1)} milhões: {num(b['pct_17_19'], 3)}%. No 1º turno, nas mesmas seções, "
        f"{num(a['pct_17_19'], 1)}% dos votos entraram entre 17h e 19h. Depois das 19h, {inteiro(b['computados_depois_19'])} votos. "
        f"Lemos {inteiro(L['cobertura']['lidos'])} logs, um por urna, e cruzamos cada um com o BU da mesma seção e com o log do 1º turno."
    )


def cartoes(L: dict) -> str:
    c = L["cobertura"]
    b = L["cadencia"]["brasil_2t"]
    ig = L["integrado"]
    return (
        '<div class="finding-grid">'
        + cartao(
            inteiro(c["contagem_confere"]),
            f"logs com a mesma contagem do BU, de {inteiro(c['lidos'])} lidos",
        )
        + cartao(
            f"{num(b['pct_17_19'], 3)}%",
            "dos votos computados entre 17h e 19h de Brasília",
        )
        + cartao(
            inteiro(L["reinicios"]["secoes"]),
            "seções com o sistema religado durante a votação",
        )
        + cartao(
            inteiro(ig["as_duas"]),
            "seções com escore do BU e atenção dos logs, ambos 2 ou mais",
        )
        + "</div>"
    )


def fonte(L: dict) -> str:
    f = L["fontes"]
    a = L["cadencia"]["amostra_1t"]
    return caixa(
        "io",
        "Que base este capítulo lê",
        f" O log de cada urna do 2º turno, lido pelo leitor versão {escape(f['versao_parser'])} com as regras "
        f"versão {escape(f['versao_regras'])}, e o do 1º turno da mesma seção. As métricas por seção estão em "
        "<code>data/outputs/logs_urnas_2t_2026.sqlite</code>; os diagnósticos publicados, em "
        "<code>docs/assets/logs_urnas_2t_2026/</code>. A cadência do 1º turno vem de uma amostra de "
        f"{inteiro(a['secoes'])} seções relidas com o mesmo leitor, porque as métricas publicadas do 1º turno "
        "não guardavam votos por hora. O voto por seção vem do BU (<code>secoes.json</code>). "
        f"{ROTULO}",
    )


# ------------------------------------------------------------------ 1. cobertura


def cobertura(L: dict) -> str:
    c = L["cobertura"]
    sit = c["situacoes"]
    sem_log = c["catalogadas"] - c["lidos"]
    cont = [
        x
        for x in c["contagem_nao_confere"]
        if "contingência" in x["explicacao_possivel"]
    ]
    rein = [
        x for x in c["contagem_nao_confere"] if x not in cont and x["reinicios_sistema"]
    ]
    return (
        p(
            f"<strong>{inteiro(c['contagem_confere'])} dos {inteiro(c['lidos'])} logs</strong> reconstroem exatamente o "
            f"comparecimento do BU da mesma seção, voto a voto. As {inteiro(sem_log)} seções catalogadas sem log são "
            f"{inteiro(sit.get('nao_instalada', 0))} não instaladas, {inteiro(sit.get('apuracao_sem_log', 0))} com BU do "
            f"sistema de apuração (cédula, sem urna de votação) e {inteiro(sit.get('sem_nome', 0))} sem nome de arquivo no "
            "catálogo oficial.",
            "verificado",
        )
        + p(
            f"Nas {len(c['contagem_nao_confere'])} que não fecham, o log tem <strong>menos</strong> cômputos que o BU"
            + (", nunca mais" if c["log_menor_que_bu_em_todas"] else "")
            + f". {inteiro(len(cont))} têm urna de contingência ou mais de uma urna no mesmo pacote: os votos da primeira "
            "urna podem estar num log que não veio junto. "
            + (
                f"Nas outras {inteiro(len(rein))}, o sistema foi religado durante a votação e a diferença é de até "
                f"{inteiro(max(-x['diferenca'] for x in rein))} voto(s): o ciclo que estava aberto quando a urna caiu."
                if rein
                else ""
            ),
            "inferencia",
        )
        + p(
            f"A biometria fecha em {inteiro(c['biometria_confere'])} seções. As {inteiro(c['biometria_nao_conferida'])} "
            f"restantes não são divergência: {inteiro(c['biometria_ausente_bu'])} são do exterior, cujo BU não traz as "
            f"categorias de habilitação, e {inteiro(c['biometria_por_contagem'])} são as mesmas seis da contagem. "
            f"Uma só versão de software em todas as urnas lidas (10.23.0.0); a urna e o código de carga do BU aparecem "
            f"no log da mesma seção em {inteiro(c['urna_bu_no_log'])} de {inteiro(c['lidos'])}.",
            "verificado",
        )
    )


def tabela_seis(L: dict) -> str:
    linhas = [
        [
            f"{r['uf']} {r['zona']}/{r['secao']}",
            inteiro(r["computados_log"]),
            inteiro(r["comparecimento_bu"]),
            sinal(r["diferenca"], 0),
            escape(r["explicacao_possivel"]),
        ]
        for r in L["cobertura"]["contagem_nao_confere"]
    ]
    return tabela(
        [
            "UF zona/seção",
            "cômputos no log",
            "comparecimento no BU",
            "diferença",
            "explicação possível",
        ],
        linhas,
        "As seis seções em que o log não reconstrói o BU",
    )


# ------------------------------------------------------------------ 2. regra 2


def regra2(L: dict) -> str:
    g = L["regra2"]
    tipos = {x["tipo"]: x["secoes"] for x in g["por_tipo"]}
    com_rein = tipos.get(
        "memória de resultado depois da zerésima, com reinício na votação", 0
    )
    sem_rein = tipos.get(
        "memória de resultado depois da zerésima, sem reinício na votação", 0
    )
    pct = 100 * g["so_mr_antes_da_zeresima"] / g["secoes_com_erro"]
    return (
        p(
            f"<strong>{inteiro(g['secoes_com_erro'])} seções</strong> registraram ERRO no dia do 2º turno; em "
            f"{inteiro(g['so_mr_antes_da_zeresima'])} ({num(pct, 1)}%) o único erro é a mensagem do GAP “Problema ao "
            "desmontar a MR”, antes da zerésima. A mesma carga de setembro serviu aos dois turnos: a urna foi religada "
            "para o 2º turno com a memória de resultado do 1º e avisa isso ao ligar. Contada como erro técnico, a "
            "mensagem marcaria quase todas as urnas do país e o critério deixaria de distinguir seções.",
            "verificado",
        )
        + p(
            f"Por isso a regra mudou, com versão e data declaradas (versão 2, 26/10/2026): essa mensagem antes da "
            f"zerésima saiu do erro técnico e ficou em contagem própria, publicada por seção. Pela regra nova sobram "
            f"<strong>{inteiro(g['erro_tecnico_regra2'])} seções</strong>, contra {inteiro(g['criterio_1t'])} no 1º turno. "
            f"A alta é quase toda da mesma mensagem depois da zerésima: {inteiro(com_rein)} seções a repetem depois de um "
            f"reinício na votação, {inteiro(sem_rein)} sem reinício reconhecido. Mensagens sem relação com a memória de "
            f"resultado aparecem em {inteiro(g['com_mensagem_alheia_a_mr'])} seções.",
            "verificado",
        )
        + p(
            "A regra nova não esconde nada: a contagem do erro da MR antes da zerésima continua em cada seção do CSV "
            "público, e a mudança foi testada numa amostra de logs do 1º turno, em que a mensagem não aparece. "
            "O que ela evita é chamar de erro o efeito previsível de religar a urna.",
            "juizo",
        )
    )


# ------------------------------------------------------------------ 3. persistência


def persistencia(L: dict) -> str:
    P = L["persistencia"]
    m = P["matriz"]
    pe = P["persistencia"]
    d = {x["criterio"]: x for x in P["diagnosticos"]}
    sb = d.get("sem_biometria_alta", {})
    ret = d.get("retomadas_inatividade", {})
    ins = d.get("inspecao_prolongada", {})
    vezes = (
        pe["atencao_2_ou_mais"]["pct_2t_dado_1t"]
        / pe["atencao_2_ou_mais"]["pct_2t_geral"]
    )
    return (
        p(
            f"<strong>{inteiro(m.get('0x0', 0))} seções</strong> não tiveram sinal além da rotina (bateria fora da votação ou inspeção longa) em nenhum dos dois turnos. Das "
            f"{inteiro(pe['atencao_2_ou_mais']['secoes_1t'])} com atenção 2 ou mais no 1º turno, "
            f"{num(pe['atencao_2_ou_mais']['pct_2t_dado_1t'], 1)}% repetiram no 2º, {num(vezes, 1)} vezes a taxa geral "
            f"({num(pe['atencao_2_ou_mais']['pct_2t_geral'], 1)}%). Atenção 3 nos dois turnos: {inteiro(m.get('3x3', 0))} seções.",
            "verificado",
        )
        + p(
            f"O que persiste é do lugar ou do cadastro, não do dia. “Eleitores sem biometria acima da referência” "
            f"repetiu em {num(sb.get('pct_persiste'), 1)}% das seções: é o cadastro da seção que não tem digital, e o "
            "cadastro não muda em três semanas. O que é do dia some: “retomadas após inatividade” marcou "
            f"{inteiro(ret.get('total_1t'))} seções no 1º turno, com seis cargos na tela, e {inteiro(ret.get('total_2t'))} no 2º. "
            f"A inspeção de cinco minutos ou mais foi ao contrário: {inteiro(ins.get('total_1t'))} no 1º turno, "
            f"{inteiro(ins.get('total_2t'))} no 2º.",
            "inferencia",
        )
        + p(
            "Com menos eleitores por hora no 2º turno, a janela entre o início e o término da inspeção pode incluir mais "
            "espera pela confirmação no terminal; a regra não cronometra o trabalho físico. A explicação é possível, "
            "não está demonstrada, e a ata da seção resolve.",
            "hipotese",
        )
    )


# ------------------------------------------------------------------ 4. cadência


def cadencia(L: dict) -> str:
    c = L["cadencia"]
    b = c["brasil_2t"]
    a1 = c["amostra_1t"]["brasil_1t"]
    a2 = c["amostra_1t"]["brasil_2t_mesmas"]
    u = c["ultimo_voto"]
    t19 = c["bu_apos_19h"]
    ne = c["regioes"]["Nordeste"]
    lista = c["lista_depois_19"]
    lugares = sorted({f"{x['uf']}" for x in lista})
    ult = [
        x["pct_ultima_hora"] for x in c["por_sinal"] if x["pct_ultima_hora"] is not None
    ]
    return (
        p(
            f"<strong>{num(a2['pct_primeira_hora'], 1)}% dos votos do 2º turno entraram na primeira hora</strong>, das 8h às 9h, "
            f"contra {num(a1['pct_primeira_hora'], 1)}% no 1º turno nas mesmas seções. A última hora regular, das 16h às 17h, "
            f"teve {num(a2['pct_ultima_hora'], 1)}% contra {num(a1['pct_ultima_hora'], 1)}%. Entre 17h e 19h, "
            f"{num(b['pct_17_19'], 3)}% no 2º turno ({inteiro(b['computados_17_19'])} cômputos no país) contra "
            f"{num(a1['pct_17_19'], 1)}% no 1º. No Nordeste, a parcela das 17h às 19h foi de {num(ne['1t']['pct_17_19'], 1)}% "
            f"para {num(ne['2t']['pct_17_19'], 3)}%.",
            "verificado",
        )
        + p(
            f"O relógio de cada urna dá o último voto da seção. Depois das 17h30, {inteiro(u['depois_1730'])} seções "
            f"({num(u['pct_depois_1730'], 2)}%); no 1º turno, {num(u['amostra_1t']['pct_depois_1730'], 1)}% da amostra. Depois "
            f"das 19h, <strong>{inteiro(u['depois_19'])} seções, com um voto cada</strong>, todas entre 19h00 e 19h06, em "
            f"{', '.join(lugares)}. Dos {inteiro(t19['secoes'])} BUs encerrados depois das 19h, {inteiro(t19['ultimo_voto_ate_1715'])} "
            f"tiveram o último voto até 17h15 (mediana {t19['mediana_ultimo_voto']}): a urna ficou aberta, e ninguém votou.",
            "verificado",
        )
        + p(
            "Duas hipóteses sobre a prorrogação dependiam desta curva: votos inseridos sob a urna aberta até as 19h, e "
            "comparecimento trazido na última hora. Nenhuma das duas deixou a marca que deixaria. Não há volume de voto "
            "depois das 17h, e a forma do dia não muda nas seções com sinal: a última hora fica entre "
            f"{num(min(ult), 1)}% e {num(max(ult), 1)}% dos votos em todos os grupos da tabela abaixo, inclusive nas seções com reinício, bateria, liberação sem "
            "biometria ou escore alto no BU.",
            "inferencia",
        )
        + nota(
            "contrario",
            "A concentração na manhã tem duas leituras e o log não separa uma da outra. Com um ou dois cargos, o voto "
            "dura menos e a fila do fim do dia some; isso já basta para achatar a tarde. Uma mobilização de eleitores "
            "logo cedo deixaria a mesma marca. O que o log descarta é o voto tardio, não o comparecimento diferente.",
            "O que a curva não decide.",
        )
    )


def tabela_sinais(L: dict) -> str:
    linhas = [
        [
            escape(x["grupo"]),
            inteiro(x["secoes"]),
            f"{num(x['pct_primeira_hora'], 2)}%",
            f"{num(x['pct_ultima_hora'], 2)}%",
            f"{num(x['pct_17_19'], 3)}%",
        ]
        for x in L["cadencia"]["por_sinal"]
    ]
    return tabela(
        [
            "grupo de seções (2º turno)",
            "seções",
            "8h às 9h",
            "16h às 17h",
            "17h às 19h",
        ],
        linhas,
        "A forma do dia nas seções com sinal, hora de Brasília",
    )


def tabela_depois19(L: dict) -> str:
    linhas = [
        [
            f"<a href=\"politizese.html#uf={x['uf']}&amp;z={x['zona']}&amp;s={x['secao']}\">{x['uf']} {x['zona']}/{x['secao']}</a>",
            x["ultimo_voto_brt"],
            inteiro(x["votos_depois_19"]),
            inteiro(x["computados"]),
            f"{num(x['fatia_f1'], 1)} → {num(x['fatia_f'], 1)}",
        ]
        for x in L["cadencia"]["lista_depois_19"]
    ]
    return tabela(
        [
            "UF zona/seção",
            "último voto",
            "votos depois das 19h",
            "votos no dia",
            "fatia de Flávio 1T → 2T",
        ],
        linhas,
        "As seções com voto depois das 19h pelo relógio da urna",
    )


# ------------------------------------------------------------------ 5. reinícios e bateria


def reinicios(L: dict) -> str:
    R = L["reinicios"]
    todas = _voto(L, "todas com reinício")
    troca = _voto(L, "reinício com troca de urna ou urna de contingência")
    mesma = _voto(L, "reinício na mesma urna")
    q = R["pct_antes_quartis"]
    return p(
        f"<strong>{inteiro(R['secoes'])} seções</strong> tiveram o sistema religado durante a votação "
        f"({inteiro(R['partidas_sistema'])} partidas): {inteiro(R['so_2t'])} só no 2º turno e {inteiro(R['nos_dois'])} "
        f"nos dois. Em {inteiro(R['mesma_urna'])} a urna voltou a funcionar; em {inteiro(R['troca_ou_contingencia'])} "
        f"houve troca de urna ou urna de contingência. O primeiro reinício cai, na mediana, depois de "
        f"{num(R['pct_votos_antes_mediana'], 0)}% dos votos da seção (quartis {num(q[0], 0)}% e {num(q[2], 0)}%), e é "
        "mais comum de manhã, quando a urna trabalha mais. A contagem fecha com o BU em "
        f"{inteiro(R['contagem_confere'])} delas.",
        "verificado",
    ) + p(
        "A fatia de Flávio nessas seções mudou do 1º para o 2º turno o mesmo que nas vizinhas do município: "
        + (
            f"{_ic(todas['dif_em_dif_contra_1t'])}, média ponderada pelos votos. Com troca de urna, "
            f"{_ic(troca['dif_em_dif_contra_1t'])}. Nem a comparação crua com as vizinhas no 2º turno, sem "
            f"descontar o 1º, separa as seções com reinício na mesma urna: {_ic(mesma['contra_vizinhas_2t'])}."
            if _zero_dentro(mesma["contra_vizinhas_2t"])
            else f"{_ic(todas['dif_em_dif_contra_1t'])}, média ponderada pelos votos. Com troca de urna, "
            f"{_ic(troca['dif_em_dif_contra_1t'])}. Contra as vizinhas, só no 2º turno, as seções com reinício "
            f"na mesma urna dão {_ic(mesma['contra_vizinhas_2t'])}, diferença que some quando se desconta a "
            "própria seção no 1º turno: é do lugar, não do reinício."
        ),
        "verificado",
    )


def bateria(L: dict) -> str:
    B = L["bateria"]
    loc = _voto(L, "bateria durante a votação junto com o município")
    iso = _voto(L, "bateria durante a votação só nesta urna")
    faixas = B["por_chuva_prevista"]
    ref = B.get("referencia_1t") or {}
    votos = (
        abs(loc["dif_em_dif_contra_1t"]["media_pp"])
        / 100
        * (B.get("votos_medios_local") or 0)
    )
    return (
        p(
            f"<strong>{inteiro(B['bateria_votacao_local']['2t'])} seções</strong> passaram para a bateria durante a votação "
            f"junto com cinco ou mais urnas do mesmo município (assinatura de queda de energia no prédio ou na rede), "
            f"contra {inteiro(B['bateria_votacao_local']['1t'])} no 1º turno; só nesta urna, "
            f"{inteiro(B['bateria_votacao_isolada']['2t'])} contra {inteiro(B['bateria_votacao_isolada']['1t'])}. A repetição "
            f"nas mesmas seções é baixa ({inteiro(B['bateria_votacao_local']['nos_dois'])} nos dois turnos): a rede cai em "
            "lugares diferentes a cada dia.",
            "verificado",
        )
        + p(
            f"Voto: diferença em diferenças de {_ic(loc['dif_em_dif_contra_1t'], 3)} nas seções com queda junto com o "
            f"município, e de {_ic(iso['dif_em_dif_contra_1t'], 3)} na queda isolada. A primeira tem intervalo que não "
            f"inclui o zero e vale cerca de {num(votos, 2)} voto por seção, na direção de Lula.",
            "verificado",
        )
        + nota(
            "contrario",
            f"No 1º turno, com chuva observada, a queda de energia acompanhou a chuva ({num(ref.get('seca_pct'), 1)}% das urnas "
            f"na seca, {num(ref.get('forte_pct'), 1)}% com chuva forte). No 2º, com chuva <em>prevista</em>, não acompanha: "
            f"{num(faixas[0]['pct_bateria_votacao'], 1)}% até 1 mm, {num(faixas[1]['pct_bateria_votacao'], 1)}% de 1 a 5 mm, "
            f"{num(faixas[-1]['pct_bateria_votacao'], 1)}% com 20 mm ou mais. Previsão de modelo global a 0,5° não é chuva "
            "medida no prédio; o teste fica pendente da reanálise de 25/10, que sai com cerca de cinco dias de atraso.",
            "O achado do 1º turno não se repete com a previsão.",
        )
    )


# ------------------------------------------------------------------ 6. metadados


def _grupo_mr(x: dict) -> str:
    lugar = (
        f"do exterior, em {inteiro(x['municipios'])} cidades"
        if x["ufs"] == ["ZZ"]
        else f"da zona {x['zonas'][0].split('-')[1]} de {x['ufs'][0]}"
    )
    return f"{inteiro(x['secoes'])} seções {lugar} com o valor {x['serie']}"


def _mr_grupos(s: dict) -> str:
    partes = []
    pequenos = [g for g in s["voto_por_grupo"] if g["secoes_com_sinal"] < 5]
    for g in s["voto_por_grupo"]:
        b = g["dif_em_dif_contra_1t"]
        if b["media_pp"] is None or g in pequenos:
            continue
        uf, z = g["zona"].split("-")
        partes.append(f"zona {z} de {uf}, {_ic(b)}")
    return (
        "Grupo a grupo, com a mesma regra: "
        + "; ".join(partes)
        + (
            f"; mais {len(pequenos)} pares em "
            + ", ".join(sorted({g["zona"].replace("-", " zona ") for g in pequenos}))
            + f" ({inteiro(sum(g['secoes_com_sinal'] for g in pequenos))} seções), pequenos demais para "
            "conta própria, mas dentro do total"
            if pequenos
            else ""
        )
        + ". Os sinais se opõem entre as zonas do Rio e o grupo do Amapá tem nove seções: "
        "nada aponta numa direção comum, e cada grupo vale pelo que a relação de mídias da "
        "zona explicar."
    )


def _mr_exterior(s: dict) -> str:
    e = s["voto_exterior"]
    r5 = e["regra_5_vizinhas"]["dif_em_dif_contra_1t"]
    r3 = e["regra_3_vizinhas"]["dif_em_dif_contra_1t"]
    t = (
        f"No exterior, {inteiro(e['secoes_marcadas'])} seções têm série repetida, e em quase todas as cidades "
        "todas as seções do consulado compartilham o valor: com a regra de cinco vizinhas sem o sinal, "
        + (
            f"sobra {inteiro(r5['n'])} comparável. "
            if r5["n"] == 1
            else f"sobram {inteiro(r5['n'])} comparáveis. "
        )
    )
    if r3["media_pp"] is not None:
        t += (
            f"Afrouxando para três vizinhas, {_ic(r3)}. É esse grupo que, misturado ao Brasil, "
            "levava a conta a um efeito negativo para Flávio; a vizinhança do exterior é a cidade do "
            "consulado, com poucas seções e eleitorado diferente, e o número fica como sensibilidade, "
            "não como resultado."
        )
    return t


def _bu_mr(e: list[dict]) -> str:
    tot = sum(x["secoes"] for x in e)
    urna = sum(x["tipo_arquivo_urna"] for x in e)
    conf = sum(x["contagem_confere"] for x in e)
    frase = (
        "Todas têm BU gerado pela urna"
        if urna == tot
        else f"{inteiro(urna)} das {inteiro(tot)} têm BU gerado pela urna"
    )
    frase += (
        ", e a contagem do log fecha com o BU em todas."
        if conf == tot
        else f"; a contagem do log fecha com o BU em {inteiro(conf)}."
    )
    return frase


def metadados(L: dict) -> str:
    M = L["metadados"]
    s = M["serie_mr"]
    e = s["estruturais"]
    ext = next((x for x in e if x["ufs"] == ["ZZ"] and x["secoes"] > 100), None)
    cg = M["cargas"]
    z = M["zeresima_brt"]
    voto = s["voto_estruturais_brasil"]["dif_em_dif_contra_1t"]
    tot_estr = sum(x["secoes"] for x in e)
    cont = [x for x in cg["no_dia_ou_depois"] if x["tipo_urna"] in (3, 4, 6)]
    outras = [x for x in cg["no_dia_ou_depois"] if x["tipo_urna"] not in (3, 4, 6)]
    seis = {
        (x["uf"], x["zona"], x["secao"]): x
        for x in L["cobertura"]["contagem_nao_confere"]
    }
    frase_cont = "".join(
        f" Uma é urna de contingência carregada em {x['carga_registrada']}, na seção {x['uf']} {x['zona']}/{x['secao']}"
        + (
            f", a mesma em que o log tem {inteiro(-seis[(x['uf'], x['zona'], x['secao'])]['diferenca'])} votos a menos que o BU."
            if (x["uf"], x["zona"], x["secao"]) in seis
            else "."
        )
        for x in cont[:1]
    )
    ultima = max((x["carga_registrada"] for x in outras), default="")
    so_valor = sum(x["so_esse_valor_no_log_todo"] for x in e)
    return (
        p(
            f"<strong>{inteiro(s['valores_distintos'])} séries de memória de resultado</strong> aparecem nos logs do dia; "
            f"{inteiro(s['repetidos'])} se repetem em mais de uma seção, somando {inteiro(s['secoes_em_repeticao'])} seções. "
            f"Os {inteiro(s['pares_entre_lugares'])} pares soltos, em UFs ou zonas diferentes, batem com o acaso: num número "
            f"de 32 bits com esse total de valores, esperam-se {num(s['pares_esperados_por_acaso_32_bits'], 1)} coincidências.",
            "verificado",
        )
        + p(
            f"O resto são {len(e)} grupos fechados numa zona: "
            + "; ".join(_grupo_mr(x) for x in e)
            + f". Em {inteiro(so_valor)} das {inteiro(tot_estr)} seções desses grupos o mesmo valor é o único do log inteiro, "
            "inclusive no trecho do 1º turno: não é coisa do dia 25. "
            + _bu_mr(e)
            + f" No Brasil, sem o exterior, a fatia de Flávio nessas seções variou entre os turnos como "
            f"nas vizinhas do município: {_ic(voto)}, média ponderada pelos votos; a média simples por "
            f"seção dá {_ic(s['voto_estruturais_brasil']['sem_peso']['dif_em_dif_contra_1t'])}.",
            "verificado",
        )
        + p(_mr_grupos(s), "verificado")
        + nota(
            "contrario",
            _mr_exterior(s),
            "Os grupos não andam juntos, e o exterior fica fora.",
        )
        + p(
            f"Um mesmo pendrive não passa por {inteiro(ext['secoes'] if ext else 0)} seções em "
            f"{inteiro(ext['municipios'] if ext else 0)} cidades do exterior. A leitura mais simples é que, "
            "nessas urnas, o campo não identifica uma mídia física: lote de mídias com o mesmo número de série de fábrica "
            "ou valor padrão quando a mídia não informa um. Transmissão com a memória de outra urna deixaria outra marca, "
            "a contagem diferente do BU, que não aparece. Só a documentação do campo e a relação de mídias por zona "
            "decidem; pedimos as duas.",
            "hipotese",
        )
        + p(
            f"Carga: {inteiro(cg['antes_do_1t'])} urnas carregadas antes do 1º turno, {inteiro(cg['entre_turnos'])} entre os "
            f"turnos (urnas trocadas para o 2º) e {len(cg['no_dia_ou_depois'])} com data de carga no dia 25 ou depois."
            f"{frase_cont} As outras {len(outras)} têm data de carga posterior ao começo da própria votação (até {ultima[:5]}), "
            "o que é impossível na ordem do log: a explicação mais simples é o relógio da urna errado na cerimônia de "
            "carga, a conferir na ata." + _bu_carga(M) + " Zerésima entre 7h e 8h em "
            f"{inteiro(z['7_as_8'])} seções; depois das 8h em {inteiro(z['depois_das_8'])}.",
            "inferencia",
        )
    )


def _bu_carga(M: dict) -> str:
    c = ((M.get("dossie_metadados") or {}).get("coerencia_logs") or {}).get(
        "carga_registrada_vs_abertura"
    ) or {}
    n, bu = c.get("carga_depois_da_abertura_no_log"), c.get(
        "das_quais_bu_registra_carga_antes"
    )
    if not n or bu is None:
        return ""
    return (
        f" O BU dessas {inteiro(n)} registra a carga antes da votação em {inteiro(bu)} "
        "(capítulo de metadados do BU), o que reforça a leitura do relógio."
    )


def tabela_cargas(L: dict) -> str:
    linhas = [
        [
            f"{x['uf']} {x['zona']}/{x['secao']}",
            x["carga_registrada"],
            "contingência" if x["tipo_urna"] in (3, 4, 6) else "votação",
            "sim" if x["contagem_confere"] else "não",
        ]
        for x in L["metadados"]["cargas"]["no_dia_ou_depois"]
    ]
    return tabela(
        ["UF zona/seção", "carga registrada", "urna", "contagem fecha com o BU"],
        linhas,
        "Urnas com carga registrada em 25/10 ou depois",
    )


# ------------------------------------------------------------------ 7. integrado


def integrado(L: dict) -> str:
    ig = L["integrado"]
    vezes = (
        ig["as_duas"] / ig["esperado_se_independentes"]
        if ig["esperado_se_independentes"]
        else None
    )
    return p(
        f"<strong>{inteiro(ig['as_duas'])} seções</strong> têm ao mesmo tempo escore 2 ou mais no BU (comparecimento, "
        "biometria, horário, tipo de arquivo) e atenção 2 ou mais nos logs. Se as duas marcas fossem independentes, "
        f"seriam {num(ig['esperado_se_independentes'], 0)}: são {num(vezes, 1)} vezes isso. Parte da sobreposição é "
        "construção: os dois leem a liberação sem biometria, um pelo BU, outro pelo log.",
        "inferencia",
    ) + p(
        f"A fatia de Flávio nelas mudou entre os turnos o mesmo que nas vizinhas: {_ic(ig['voto']['dif_em_dif_contra_1t'])}. "
        "A lista abaixo é a das 50 primeiras pela ordem escore, atenção e magnitude, cada uma com o link para a seção "
        "no Politize-se, onde estão o resultado da urna nos dois turnos e o que o log registrou.",
        "verificado",
    )


def tabela_integrado(L: dict, n: int = 50) -> str:
    linhas = []
    for i, x in enumerate(L["integrado"]["secoes"][:n], start=1):
        diag = ", ".join(x["diagnosticos_log"])
        linhas.append(
            [
                str(i),
                f"{escape(x.get('municipio') or x['mun'])} ({x['uf']})",
                f"<a href=\"{x['politizese']}\">{x['zona']}/{x['secao']}</a>",
                str(x["escore_bu"]),
                str(x["atencao_log"]),
                escape(", ".join(x["sinais_bu"])),
                escape(diag),
                (
                    "n/d"
                    if x["fatia_f1"] is None
                    else f"{num(x['fatia_f1'], 1)} → {num(x['fatia_f'], 1)}"
                ),
            ]
        )
    return tabela(
        [
            "nº",
            "município",
            "zona/seção",
            "escore BU",
            "atenção log",
            "sinais do BU",
            "diagnósticos do log",
            "fatia de Flávio 1T → 2T",
        ],
        linhas,
        "As 50 primeiras seções com as duas marcas (ligação para o Politize-se)",
    )


# ------------------------------------------------------------------ fecho


def leitura(L: dict) -> str:
    return nota(
        "juizo",
        "O dossiê investiga uma mudança entre a última pesquisa e a urna. Os logs dizem onde ela não está: não há voto "
        "depois das 17h, a forma do dia não muda nas seções com sinal, reinício, bateria e metadado repetido não "
        "deslocam o voto, e o log fecha com o BU em todas as seções menos seis, sempre para menos. Se houve mudança, "
        "ela não aparece no funcionamento das urnas; o que resta para investigar está em quem compareceu e em como votou, "
        "e o log, por desenho, não registra voto.",
        "O que os logs tiram da mesa.",
    )


def limites_itens(L: dict) -> list[str]:
    return [
        "O log registra eventos da urna, não o voto: nenhuma conta deste capítulo identifica eleitor nem escolha individual.",
        "Hora do log é a do relógio da urna; a conversão para Brasília usa a hora modal do primeiro voto no município.",
        f"A cadência do 1º turno é uma amostra de {inteiro(L['cadencia']['amostra_1t']['secoes'])} seções (uma em cada cinco).",
        "Diferença em diferenças compara seções com sinal às vizinhas do mesmo município; não identifica causa.",
        "A chuva do 2º turno é previsão, não observação; o teste da bateria contra a chuva medida fica pendente.",
        "Atenção dos logs e escore do BU são ordenação para fiscalização, não probabilidade de irregularidade.",
        "A série da memória de resultado repetida pede a documentação do campo e a relação de mídias por zona.",
        ROTULO,
    ]
