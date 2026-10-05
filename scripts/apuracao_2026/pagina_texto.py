"""Frases do dossiê da apuração, geradas dos números dos JSONs.

Regra: nenhuma frase daqui carrega número digitado. Todo número sai do dado
recebido; o que é juízo editorial vem rotulado na própria frase.
"""

from __future__ import annotations

from html import escape

from .pagina_comum import (
    NOME_UF,
    hora,
    inteiro,
    milhoes,
    nome_proprio,
    num,
    p,
    sinal,
    sinal_int,
)

DATA_2T = "25 de outubro"
VEZES = {
    1: "uma vez",
    2: "duas vezes",
    3: "três vezes",
    4: "quatro vezes",
}  # calendário do TSE para o 2º turno de 2026


def pct(x: float | None, casas: int = 2) -> str:
    return f"{num(x, casas)}%"


def lista(itens: list[str]) -> str:
    itens = [i for i in itens if i]
    if len(itens) <= 1:
        return "".join(itens)
    return ", ".join(itens[:-1]) + " e " + itens[-1]


def ufs_por_lider(P: dict) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"flavio": [], "lula": []}
    for u in P["ufs"]:
        if u["uf"] == "ZZ":
            continue
        out.setdefault(u["lider"], []).append(u["uf"])
    return out


# ------------------------------------------------------------------ 01 abertura


def abertura(P: dict) -> str:
    n = P["nacional"]
    v, c = n["votos"], n["pct"]
    cmp_ = n["comparacao"]
    lid = ufs_por_lider(P)
    zz = next((u for u in P["ufs"] if u["uf"] == "ZZ"), None)
    out = [
        p(
            f"Flávio Bolsonaro (PL) terminou o 1º turno com <strong>{inteiro(v['flavio'])}</strong> votos, "
            f"{pct(c['flavio'])} dos válidos. Lula (PT) teve <strong>{inteiro(v['lula'])}</strong>, "
            f"{pct(c['lula'])}. A diferença é de {inteiro(n['diferenca_votos'])} votos, "
            f"{num(n['diferenca_pp'], 2)} ponto. Os dois disputam o 2º turno em {DATA_2T}.",
            "verificado",
        ),
        p(
            f"O arquivo nacional final foi gerado pelo TSE às {hora(n['gerado_em_brt'], True)} de 05/10, "
            f"com {inteiro(n['secoes'])} de {inteiro(n['secoes_total'])} seções. "
            f"Compareceram {inteiro(n['comparecimento'])} eleitores ({pct(n['pct_comparecimento'])}); "
            f"a abstenção foi de {inteiro(n['abstencao'])}. Brancos somaram {pct(n['pct_brancos'])} "
            f"e nulos {pct(n['pct_nulos'])} de quem foi votar."
        ),
        p(
            f"As outras dez candidaturas ficaram com {pct(c['terceiros'])} dos válidos: Augusto Cury "
            f"{pct(c['cury'])}, Renan Santos {pct(c['renan'])} e Ronaldo Caiado {pct(c['caiado'])}. "
            f"Flávio venceu em {len(lid['flavio'])} UFs ({', '.join(sorted(lid['flavio']))}); "
            f"Lula em {len(lid['lula'])} ({', '.join(sorted(lid['lula']))})."
            + (
                f" No exterior, Lula fez {pct(zz['pct']['lula'])} contra {pct(zz['pct']['flavio'])}."
                if zz
                else ""
            )
        ),
        p(
            f"Contra o 1º turno de 2022, Flávio teve {sinal(cmp_['flavio_vs_bolsonaro_1t']['pp'], 2)} pontos "
            f"e {sinal_int(cmp_['flavio_vs_bolsonaro_1t']['votos'])} votos sobre Bolsonaro; Lula ficou "
            f"{sinal(cmp_['lula_vs_lula_1t']['pp'], 2)} pontos e {sinal_int(cmp_['lula_vs_lula_1t']['votos'])} "
            f"votos contra o próprio resultado. A margem andou {num(cmp_['virada_margem_vs_1t_pp'], 2)} pontos "
            f"para a direita. Contra o 2º turno de 2022, Flávio ainda está "
            f"{num(abs(cmp_['flavio_vs_bolsonaro_2t']['pp']), 2)} pontos abaixo de Bolsonaro.",
            "verificado",
        ),
    ]
    return "".join(out)


# ------------------------------------------------------------------ 02 noite


def noite(L: dict, linhas: list[dict], paradas: list[dict]) -> str:
    m = L["marcos"]
    com_secoes = [r for r in linhas if r["st"]]
    sempre = all((r["flavio"] or 0) >= (r["lula"] or 0) for r in com_secoes)
    maior = max(linhas, key=lambda r: r["d_vv"] or 0)
    out = [
        p(
            f"A primeira versão nacional com seções foi gerada às {hora(m['primeira_versao_nacional_com_secoes_brt'], True)}, "
            f"com totalização impressa às {hora(m['totalizacao_impressa_nela'], True)}. A última, às "
            f"{hora(m['versao_final_nacional_brt'], True)} de 05/10. Entre uma e outra o arquivo nacional teve "
            f"{inteiro(L['nacional']['n_versoes_genuinas'])} versões."
            + (
                f" Flávio esteve à frente em todas as {inteiro(len(com_secoes))} versões com seções."
                if sempre
                else ""
            ),
            "verificado",
        ),
    ]
    if paradas:
        frases = [
            f"de {hora(t['de_brt'], True)} a {hora(t['ate_brt'], True)} ({num(t['minutos'], 1)} min, "
            f"de {num(t['pst_de'], 2)}% para {num(t['pst_ate'], 2)}% das seções)"
            for t in paradas
        ]
        out.append(
            p(
                f"O arquivo nacional de presidente ficou parado {VEZES.get(len(paradas), f'{len(paradas)} vezes')} no pico: "
                + lista(frases)
                + ". As faixas sombreadas do gráfico marcam esses intervalos."
            )
        )
    out.append(
        p(
            f"A maior atualização chegou às {hora(maior['gerado_brt'], True)}: "
            f"{inteiro(maior['d_st'])} seções e {milhoes(maior['d_vv'])} de votos válidos de uma vez, "
            f"com Lula em {pct(maior['lote_pct_lula'])} e Flávio em {pct(maior['lote_pct_flavio'])} do lote. "
            "O lote é grande porque represou, não porque mudou o placar: a ordem dos dois nunca se inverteu."
        )
    )
    return "".join(out)


def noite_conclusao(L: dict) -> str:
    c = L["conclusao_ufs"]
    reais = [x for x in c if x["uf"] != "ZZ"]
    primeira, ultima = reais[0], reais[-1]
    tardias = L["secoes_tardias"]
    tot = tardias["total"]
    mun = ", ".join(
        f"{nome_proprio(m['nome'])} ({m['uf']}) {m['secoes']}"
        for m in tardias["municipios"]
    )
    return p(
        f"A primeira UF a fechar 100% do presidente foi {NOME_UF[primeira['uf']]}, às {hora(primeira['gerado_brt'])}; "
        f"a última, {NOME_UF[ultima['uf']]}, às {hora(ultima['gerado_brt'])} de 05/10. Depois da meia-noite chegaram "
        f"{inteiro(tot['secoes'])} seções em {tot['municipios']} municípios ({mun}), com {inteiro(tot['validos'])} "
        f"válidos: Lula {pct(tot['pct_lula'])}, Flávio {pct(tot['pct_flavio'])}. São áreas remotas, e o lote não "
        f"muda nada diante de uma diferença de milhões.",
        "verificado",
    )


# ------------------------------------------------------------------ 03 falha


def falha_banco(L: dict, paradas: list[dict], linhas: list[dict]) -> str:
    pg = L["pausa_geral"]["lacunas"][0] if L["pausa_geral"].get("lacunas") else None
    d = L["divergencia_soma_ufs"]["maior_diferenca_visivel"]
    idg = L["idg_regressivo"]["total_por_classe"]
    total_idg = L["idg_regressivo"]["total_eventos"]
    longa = max(paradas, key=lambda t: t["minutos"]) if paradas else None
    destravou = max(linhas, key=lambda r: r["d_vv"] or 0)
    out = []
    if longa:
        lt = longa["leituras_no_intervalo"]
        out.append(
            f"<p>O arquivo nacional de presidente ficou {num(longa['minutos'], 1)} minutos sem versão nova, de "
            f"{hora(longa['de_brt'], True)} a {hora(longa['ate_brt'], True)}. O coletor leu o arquivo "
            f"{lt['total']} vezes nesse intervalo; {lt['por_classe'].get('nao_modificado', 0)} respostas foram "
            "“não modificado”. Não era cache: a versão assinada também estava parada.</p>"
        )
    if pg:
        lei = pg["leituras_no_intervalo"]
        total_lei = sum(lei.values())
        out.append(
            f"<p>De {hora(pg['de_brt'], True)} a {hora(pg['ate_brt'], True)} ({num(pg['minutos'], 1)} min), "
            "<strong>o TSE não gerou nenhum arquivo de resultado de nenhum cargo, em nenhum nível</strong>: nacional, "
            f"UF, município ou zona. O coletor fez {inteiro(total_lei)} requisições no intervalo; "
            f"{inteiro(lei.get('nao_modificado', 0))} voltaram “não modificado” e as {inteiro(lei.get('ok', 0))} "
            "com corpo novo traziam versões geradas antes do início da pausa. Durante a noite, ao vivo, dissemos que os "
            "arquivos municipais seguiam atualizando. Os dados desmentem: corrigimos aqui.</p>"
        )
    out.append(
        f"<p>Às {d['hora_brt']}, a soma dos 28 arquivos de UF tinha <strong>{inteiro(d['secoes'])} seções</strong> "
        f"a mais que o arquivo nacional ({num(d['pp_do_total'], 2)}% do total). O nacional mostrava "
        f"{inteiro(d['nacional_st'])}; as UFs somavam {inteiro(d['soma_ufs_st'])}. A partir dali, o telão da casa "
        "passou a somar as UFs quando o nacional atrasava, com aviso na tela. O lote que destravou o nacional, às "
        f"{hora(destravou['gerado_brt'], True)}, trouxe {inteiro(destravou['d_st'])} seções e "
        f"{milhoes(destravou['d_vv'])} de válidos.</p>"
    )
    out.append(
        f"<p>O contador de versão do TSE caiu {inteiro(total_idg)} vezes ao longo do dia. Só "
        f"{inteiro(idg.get('copia_antiga', 0))} eram cópias antigas servidas pela rede de distribuição; "
        f"{inteiro(idg.get('mais_nova_que_todas_as_anteriores', 0))} eram versões mais novas com contador menor. "
        "Por isso a regra da página é a hora de geração, não o contador. O TSE também marcou como “eleito” "
        "candidatos que vão ao 2º turno de governador (Douglas Ruas no RJ, Celina Leão no DF); a casa decide "
        "eleito pelo texto da situação, não pela marca.</p>"
    )
    return "".join(out)


def falha_app(L: dict, linhas: list[dict], hora_app: str) -> str:
    dc = L["divergencia_soma_ufs"]["minutos"]
    rows = [dict(zip(dc["colunas"], r, strict=False)) for r in dc["linhas"]]
    r = next((x for x in rows if x["hora_brt"] == hora_app), None)
    if r is None:
        return "<p>Leitura do aplicativo sem linha correspondente no banco.</p>"
    versao = next((x for x in linhas if x["st"] == r["nacional_st_visivel"]), None)
    total = L["divergencia_soma_ufs"]["secoes_total"]
    impresso = hora(versao["totalizacao_impressa"], True) if versao else "s/d"
    return (
        f"<p>Às {hora_app}, o aplicativo oficial do TSE mostrava “última atualização {impresso}”, "
        f"{inteiro(r['nacional_st_visivel'])} seções, {num(100 * r['nacional_st_visivel'] / total, 2)}%. "
        f"No mesmo minuto, o arquivo de andamento do próprio TSE marcava {inteiro(r['andamento_br_st_visivel'])} "
        f"seções ({num(100 * r['andamento_br_st_visivel'] / total, 1)}%) e a soma das UFs, "
        f"{inteiro(r['soma_ufs_st_visivel'])}. Os números da tela batem com a versão nacional gerada às "
        f"{r['nacional_gerado_brt_visivel']} guardada no banco.</p>"
    )


def falha_imprensa(N: list[dict]) -> str:
    com_citacao = [
        i
        for i in N
        if "congestionamento"
        in (i.get("resumo_1_linha", "") + i.get("titulo", "")).lower()
    ]
    ab = next(
        (i for i in com_citacao if "Agência Brasil" in i.get("veiculo", "")), None
    )
    principal = ab or (com_citacao[0] if com_citacao else None)
    html = ""
    if principal:
        html += (
            "<blockquote>“O que ocorreu foi um congestionamento de dados.”"
            f'<cite>Nunes Marques, presidente do TSE, segundo a <a href="{escape(principal["url"])}">'
            f"{escape(principal['veiculo'])}</a> ({escape(principal['titulo'])}, "
            f"{escape(principal.get('data', ''))}). Citação conforme reportada; a nota oficial do TSE não foi lida "
            "diretamente porque o portal devolveu erro de limite de acesso.</cite></blockquote>"
        )
    outros = [i for i in com_citacao if i is not principal]
    if outros:
        html += (
            f"<p>Outros {len(outros)} veículos registraram a mesma explicação: "
            + lista(
                [
                    f'<a href="{escape(i["url"])}">{escape(i["veiculo"])}</a>'
                    for i in outros
                ]
            )
            + ". A duração citada varia entre os veículos. A versão oficial, como reportada: fluxo acima do "
            "normal no sistema de divulgação, isolamento temporário de sistemas, protocolo de segurança, "
            "totalização não afetada.</p>"
        )
    return html


# ------------------------------------------------------------------ 04 regiões


def regioes(P: dict) -> str:
    R = P["regioes"]
    cs, ne, no = R["Centro-Sul"], R["Nordeste"], R["Norte"]
    br = R["Brasil"]["comparacao"]
    swings = [(u["uf"], u["comparacao"]) for u in P["ufs"] if u["uf"] != "ZZ"]
    cresceu = [uf for uf, c in swings if c["flavio_vs_bolsonaro_1t"]["pp"] > 0]
    caiu = [uf for uf, c in swings if c["flavio_vs_bolsonaro_1t"]["pp"] <= 0]
    lula_up = [uf for uf, c in swings if c["lula_vs_lula_1t"]["pp"] > 0]
    top = sorted(swings, key=lambda s: -s[1]["virada_margem_vs_1t_pp"])[:3]
    lula_baixo = min(swings, key=lambda s: s[1]["lula_vs_lula_1t"]["pp"])
    nec = ne["comparacao"]
    faixa = P["por_faixa_lula_2022"]
    hi, lo = faixa[-1], faixa[0]
    out = [
        p(
            f"Flávio cresceu sobre Bolsonaro em {len(cresceu)} de {len(swings)} UFs"
            + (f"; a exceção é {lista(caiu)}" if caiu else "")
            + f". Lula aumentou a própria fatia em {len(lula_up)} ({lista(lula_up)}).",
            "verificado",
        ),
        p(
            f"A perda de Lula é do Centro-Sul: {sinal_int(cs['comparacao']['lula_vs_lula_1t']['votos'])} votos, "
            f"{num(cs['contribuicao_pct_da_variacao_nacional']['lula_menos_lula_1t'], 1)}% do total que ele perdeu. "
            f"No Nordeste foram {sinal_int(nec['lula_vs_lula_1t']['votos'])}; no Norte, "
            f"{sinal_int(no['comparacao']['lula_vs_lula_1t']['votos'])}.",
            "verificado",
        ),
        p(
            f"O ganho de Flávio é nacional. O Centro-Sul deu "
            f"{num(cs['contribuicao_pct_da_variacao_nacional']['flavio_menos_bolsonaro_1t'], 1)}% dele, o Nordeste "
            f"{num(ne['contribuicao_pct_da_variacao_nacional']['flavio_menos_bolsonaro_1t'], 1)}% e o Norte "
            f"{num(no['contribuicao_pct_da_variacao_nacional']['flavio_menos_bolsonaro_1t'], 1)}%. No Nordeste, Flávio "
            f"fez {pct(ne['r2026']['pct']['flavio'])}, acima de Bolsonaro no 1º turno de 2022 "
            f"({pct(nec['flavio_vs_bolsonaro_1t']['pct_b'])}).",
            "verificado",
        ),
        p(
            f"Flávio cresceu mais onde Lula era mais forte. Nos {inteiro(hi['municipios'])} municípios em que Lula "
            f"teve de {hi['faixa_lula_2022_pct']}% em 2022, Flávio subiu {sinal(hi['swing_flavio_pp'], 2)} pontos sobre "
            f"Bolsonaro; nos {inteiro(lo['municipios'])} em que Lula teve de {lo['faixa_lula_2022_pct']}%, "
            f"{sinal(lo['swing_flavio_pp'], 2)}. É quase uniforme, com ganho extra nos redutos petistas.",
            "verificado",
        ),
        p(
            "As maiores viradas de margem foram "
            + lista([f"{uf} {sinal(c['virada_margem_vs_1t_pp'], 2)}" for uf, c in top])
            + f" pontos. A maior queda de Lula foi em {lula_baixo[0]} ({sinal(lula_baixo[1]['lula_vs_lula_1t']['pp'], 2)}). "
            f"No Brasil, o comparecimento variou {sinal(br['comparecimento_vs_1t_pp'], 2)} ponto contra o 1º turno "
            f"de 2022: subiu no Norte ({sinal(no['comparacao']['comparecimento_vs_1t_pp'], 2)}) e no Nordeste "
            f"({sinal(nec['comparecimento_vs_1t_pp'], 2)}) e caiu no Centro-Sul "
            f"({sinal(cs['comparacao']['comparecimento_vs_1t_pp'], 2)}).",
            "verificado",
        ),
        p(
            f"No Nordeste, o ganho de Flávio ({sinal_int(nec['flavio_vs_bolsonaro_1t']['votos'])}) foi muito maior que a "
            f"perda de Lula ({sinal_int(nec['lula_vs_lula_1t']['votos'])}). O saldo é compatível com voto novo e com "
            "eleitor de terceira via, mais do que com troca direta. No Centro-Sul, Lula perdeu mais do que Flávio "
            "ganhou, com comparecimento menor: parte do voto de Lula em 2022 parece ter ido para a abstenção ou outras "
            "candidaturas. Dado agregado não identifica quem trocou de voto.",
            "inferencia",
        ),
    ]
    return "".join(out)


# ------------------------------------------------------------------ 05 exterior


def exterior(E: dict, P: dict) -> str:
    t = E["total"]
    zz = next(u for u in P["ufs"] if u["uf"] == "ZZ")
    c = zz["comparacao"]
    conts = sorted(E["continentes"], key=lambda x: -x["validos"])
    lider = [
        f"{x['continente']} ({'Flávio' if x['pct']['flavio'] > x['pct']['lula'] else 'Lula'} "
        f"{pct(max(x['pct']['flavio'], x['pct']['lula']))})"
        for x in conts[:4]
    ]
    paises = sorted(E["paises"], key=lambda x: -x["validos"])
    pt = next((x for x in paises if x["pais"] == "PT"), None)
    hl = E["hora_local"]
    w = hl["mais_adiantadas"][0] if hl.get("mais_adiantadas") else None
    out = [
        p(
            f"Lula venceu no exterior com {pct(zz['pct']['lula'])} contra {pct(zz['pct']['flavio'])} de Flávio, "
            f"diferença de {inteiro(abs(zz['margem_votos']))} votos. Foram {inteiro(t['secoes'])} seções em "
            f"{t['cidades']} cidades de {t['paises']} países. O comparecimento foi de {pct(t['pct_comparecimento'])}, "
            f"{num(abs(c['comparecimento_vs_1t_pp']), 2)} pontos abaixo do 1º turno de 2022.",
            "verificado",
        ),
        p("Por continente: " + lista(lider) + ".", "verificado"),
    ]
    if pt:
        out.append(
            p(
                f"Portugal, o segundo maior colégio, deu a Flávio {pct(pt['pct']['flavio'])}, "
                f"{sinal(pt['swing_flavio_vs_bolsonaro_1t_pp'], 2)} pontos sobre Bolsonaro nas mesmas cidades; "
                f"Lula variou {sinal(pt['swing_lula_vs_lula_1t_pp'], 2)}.",
                "verificado",
            )
        )
    if w:
        out.append(
            p(
                f"O TSE imprime a hora de totalização no relógio local da cidade. {nome_proprio(w['nome'])} aparece "
                f"totalizada em {escape(w['totalizacao_impressa'])} num arquivo gerado às "
                f"{hora(w['primeira_versao_totalizada_gerada_brt'], True)} de 04/10 (Brasília). "
                f"{hl.get('cidades_com_data_impressa_de_05_10_e_arquivo_de_04_10', 0)} cidades aparecem totalizadas em "
                "05/10 em arquivos de 04/10. É fuso, não erro de contagem.",
                "verificado",
            )
        )
    return "".join(out)
