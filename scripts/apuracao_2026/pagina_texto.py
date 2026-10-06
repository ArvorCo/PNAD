"""Frases curtas dos capítulos 01 a 05 do dossiê da apuração, geradas dos números dos JSONs.

Regra: nenhuma frase daqui carrega número digitado. Todo número sai do dado
recebido; o que é juízo editorial vem rotulado na própria frase. Cada função
devolve no máximo um parágrafo, para o texto caber entre as figuras do catálogo.
"""

from __future__ import annotations

import json
from html import escape

from .pagina_comum import (
    Dados,
    figura_catalogo,
    hora,
    inteiro,
    milhoes,
    nota,
    num,
    p,
    rotulo,
    sinal,
    sinal_int,
)

DATA_2T = "25 de outubro"
VEZES = {1: "uma vez", 2: "duas vezes", 3: "três vezes", 4: "quatro vezes"}
EXTENSO = {
    2: "duas",
    3: "três",
    4: "quatro",
    5: "cinco",
    10: "dez",
    11: "onze",
    12: "doze",
}


def pct(x: float | None, casas: int = 2) -> str:
    return f"{num(x, casas)}%"


def lista(itens: list[str]) -> str:
    itens = [i for i in itens if i]
    if len(itens) <= 1:
        return "".join(itens)
    return ", ".join(itens[:-1]) + " e " + itens[-1]


def dados_figuras(d: Dados) -> dict:
    """Todos os JSONs do dossiê, por nome sem extensão, mais o agregador da casa."""
    chave = "__figuras__"
    if chave not in d.cache:
        tudo = {f.stem: d.get(f.name) for f in sorted(d.pasta.glob("*.json"))}
        agregador = d.pasta.parents[2] / "docs/assets/reponderacao_pnad.json"
        if agregador.exists():
            tudo["agregador"] = json.loads(agregador.read_text(encoding="utf-8"))
        d.cache[chave] = tudo
    return d.cache[chave]


def fig(nome: str, d: Dados, **op) -> str:
    """Figura do catálogo pelo nome, com todos os dados carregados."""
    return figura_catalogo(nome, dados_figuras(d), **op)


# ------------------------------------------------------------------ 01 abertura


def _cap(ident: str, n: int) -> str:
    return f'<a href="#{ident}">cap. {n}</a>'


def _votos_curto(x: float) -> str:
    return f"{milhoes(abs(x))}{' de' if abs(x) >= 1e6 else ''} votos"


def _sinal_mil(x: float) -> str:
    return ("+" if x > 0 else "−") + milhoes(abs(x))


def teses(d: Dados) -> str:
    """As dez frases do que o dossiê prova, cada uma com o número e o capítulo."""
    P = d.get("presidente.json")
    n = P["nacional"]
    cmp_ = n["comparacao"]
    ufs = [u for u in P["ufs"] if u["uf"] != "ZZ"]
    f_ufs = sum(1 for u in ufs if u["lider"] == "flavio")
    cresceu = sum(1 for u in ufs if u["comparacao"]["flavio_vs_bolsonaro_1t"]["pp"] > 0)
    itens: list[tuple[str, str]] = [
        (
            "verificado",
            f"Flávio fez <strong>{pct(n['pct']['flavio'])}</strong> dos válidos e Lula {pct(n['pct']['lula'])}, "
            f"{inteiro(n['diferenca_votos'])} votos de diferença; os dois vão ao 2º turno em {DATA_2T} ({_cap('abertura', 1)}).",
        ),
        (
            "verificado",
            f"Flávio venceu em {f_ufs} UFs e cresceu sobre Bolsonaro em {cresceu} de {len(ufs)}; a margem andou "
            f"{num(cmp_['virada_margem_vs_1t_pp'], 2)} pontos para ele desde o 1º turno de 2022 ({_cap('regioes', 4)}).",
        ),
    ]
    C, S = d.get("camara.json"), d.get("senado.json")
    if C and S:
        s27 = S["senado_2027"]
        itens.append(
            (
                "verificado",
                f"Direita e centro-direita somam {C['blocos']['direita + centro-direita']} das {C['vagas_total']} cadeiras "
                f"da Câmara e {s27['por_bloco']['direita + centro-direita']} das {s27['total']} do Senado de 2027 "
                f"({_cap('camara', 6)} e {_cap('senado', 7)}).",
            )
        )
    N = d.get("noite_regioes.json")
    if N:
        dec = N["decomposicao"]
        itens.append(
            (
                "inferencia",
                f"A vantagem de Flávio caiu de {num(dec['pico_pp'], 2)} pontos às {hora(dec['pico_brt'])} para "
                f"{num(n['diferenca_pp'], 2)} no fim, e {num(dec['entre_regioes_pct_da_queda'], 1)}% da queda é a ordem em que "
                f"as regiões chegaram, não voto que mudou ({_cap('noite', 2)}).",
            )
        )
    L = d.get("linha_do_tempo.json")
    if L:
        par = [
            t
            for t in L["travamentos"]["nacional"]
            if (t.get("secoes_no_salto") or 0) >= 1000
        ]
        pg = L["pausa_geral"]["lacunas"][0]
        dv = L["divergencia_soma_ufs"]["maior_diferenca_visivel"]
        itens.append(
            (
                "verificado",
                f"O arquivo nacional parou {VEZES.get(len(par), f'{len(par)} vezes')} ("
                + lista([f"{num(t['minutos'], 0)}" for t in par])
                + f" minutos) e, por {num(pg['minutos'], 0)} minutos, o TSE não gerou arquivo de resultado nenhum; às "
                f"{dv['hora_brt']} a soma das UFs estava {inteiro(dv['secoes'])} seções à frente do nacional "
                f"({_cap('falha-tse', 3)}).",
            )
        )
    A = d.get("arquitetura.json")
    if A:
        lac = A["recebimento_2026"]["lacunas"]
        itens.append(
            (
                "inferencia",
                f"O carimbo de recebimento dos boletins some nas mesmas {EXTENSO.get(len(lac), len(lac))} janelas: a parada não foi só de "
                f"vitrine, e a causa segue sem o relatório técnico que o TSE não publicou ({_cap('falha-tse', 3)}).",
            )
        )
    PV = d.get("pesquisas_vs_urna.json")
    if PV:
        pub = PV["resumo_ultimas_ondas"]["publicado"]
        ref = PV["referencia_2022"]
        itens.append(
            (
                "verificado",
                f"As últimas ondas de {pub['n']} institutos erraram a diferença em {sinal(pub['media'], 2)} pontos a favor "
                f"de Lula, na direção de 2022 ({sinal(ref['erro_comum_diferenca_lula_menos_bolsonaro'], 2)}); "
                f"{pub['positivos']} de {pub['n']} superestimaram Lula ({_cap('pesquisas', 10)}).",
            )
        )
    V = d.get("voto_util.json")
    if V:
        tv = V["terceira_via"]
        a = V["decomposicao"]["agregados"]["ultimas_ondas_publicado"][
            "nexus_renormalizada"
        ]
        itens.append(
            (
                "hipotese",
                f"A terceira via caiu de {pct(tv['media_publicado_todas'])} nas pesquisas para {pct(tv['urna_validos'])} "
                f"na urna, e o voto útil foi de um lado: Flávio {sinal(a['ganho_flavio_pp'], 2)}, Lula "
                f"{sinal(a['ganho_lula_pp'], 2)}; pela matriz Nexus, a consolidação explica "
                f"{num(100 * a['fracao_explicada_diferenca'], 0)}% do erro comum ({_cap('voto-util', 11)}).",
            )
        )
    AN, SE = d.get("anomalias.json"), d.get("secoes.json")
    if AN and SE:
        c22 = SE["extremos"]["comparacao_2022"]["lula"]
        rg = SE["urna"]["reguas"]
        itens.append(
            (
                "inferencia",
                f"Nenhuma das {len(AN['topo'])} zonas mais atípicas aponta irregularidade; das {inteiro(c22['secoes_90_2026_casadas'])} "
                f"seções de Lula acima de 90% que existem em 2022, {inteiro(c22['tambem_90_em_2022_1t'])} já davam 90% a ele, "
                f"e o modelo de urna move menos de {num(rg['limiar_pp'], 0)} ponto, com sinal que troca conforme o controle. "
                f"O que sobra pede documento: ata, log da urna e plano de alocação do TRE ({_cap('anomalias', 12)}).",
            )
        )
    E, TVJ = d.get("estrategia_2t.json"), d.get("terceira_via.json")
    if E and TVJ and "reguas" in TVJ:
        br = TVJ["reguas"]["totais"]["brasil"]
        lo, hi = br["urna_ic95"]
        eq = E["aritmetica"]["equilibrio"]
        itens.append(
            (
                "inferencia",
                f"Nas duas réguas, a terceira via rende saldo a Flávio no 2º turno: {_sinal_mil(br['nexus'])} pela matriz "
                f"Nexus e {_sinal_mil(br['urna'])} pela urna de 2022 (intervalo de 95% de {_sinal_mil(lo)} a {_sinal_mil(hi)}), sem desfazer "
                f"os {_votos_curto(n['diferenca_votos'])}. O risco é a base: se {pct(eq['base_flavio_trocando_para_lula_pct'])} "
                f"dela trocar de lado, a margem central some ({_cap('segundo-turno', 14)}).",
            )
        )
    lis = "".join(f"<li>{rotulo(t)} {x}</li>" for t, x in itens)
    return f'<h3>O que este dossiê prova</h3><ol class="teses">{lis}</ol>'


def abertura_b(P: dict) -> str:
    n = P["nacional"]
    c = n["pct"]
    return p(
        f"As outras {EXTENSO.get(len(n['candidaturas']) - 2, len(n['candidaturas']) - 2)} candidaturas somam {pct(c['terceiros'])}: Cury {pct(c['cury'])}, Renan Santos {pct(c['renan'])}, "
        f"Caiado {pct(c['caiado'])}. Compareceram {inteiro(n['comparecimento'])} eleitores ({pct(n['pct_comparecimento'])}); "
        f"brancos {pct(n['pct_brancos'])}, nulos {pct(n['pct_nulos'])}. Arquivo final do TSE, "
        f"{hora(n['gerado_em_brt'], True)} de 05/10, {inteiro(n['secoes'])} de {inteiro(n['secoes_total'])} seções.",
        "verificado",
    )


# ------------------------------------------------------------------ 02 noite


def noite_a(L: dict, linhas: list[dict]) -> str:
    m = L["marcos"]
    com = [r for r in linhas if r["st"]]
    sempre = all((r["flavio"] or 0) >= (r["lula"] or 0) for r in com)
    maior = max(linhas, key=lambda r: r["d_vv"] or 0)
    lider = (
        f"Flávio esteve à frente nas {inteiro(len(com))} versões do arquivo nacional com seções, das "
        if sempre
        else f"O arquivo nacional teve {inteiro(len(com))} versões com seções, das "
    )
    return p(
        lider
        + f"{hora(m['primeira_versao_nacional_com_secoes_brt'], True)} às {hora(m['versao_final_nacional_brt'], True)} de "
        "05/10. Mudou o tamanho da vantagem, não o líder. O arquivo parou no pico (capítulo 3), e a maior atualização, "
        f"às {hora(maior['gerado_brt'], True)}, trouxe {inteiro(maior['d_st'])} seções e {milhoes(maior['d_vv'])} de "
        f"válidos de uma vez, com Lula em {pct(maior['lote_pct_lula'])} do lote: o que as UFs já mostravam.",
        "verificado",
    )


def noite_d(L: dict) -> str:
    t = L["secoes_tardias"]["total"]
    return p(
        f"Depois da meia-noite o arquivo recebeu {inteiro(t['secoes'])} seções em {t['municipios']} municípios, "
        f"{inteiro(t['validos'])} válidos, Lula {pct(t['pct_lula'])}: áreas remotas, sem peso na diferença.",
        "verificado",
    )


# ------------------------------------------------------------------ 03 falha


def falha_app_curta(L: dict, linhas: list[dict], hora_app: str) -> str:
    dc = L["divergencia_soma_ufs"]["minutos"]
    rows = [dict(zip(dc["colunas"], r, strict=False)) for r in dc["linhas"]]
    r = next((x for x in rows if x["hora_brt"] == hora_app), None)
    if r is None:
        return "sem linha correspondente no banco"
    versao = next((x for x in linhas if x["st"] == r["nacional_st_visivel"]), None)
    total = L["divergencia_soma_ufs"]["secoes_total"]
    impresso = hora(versao["totalizacao_impressa"], True) if versao else "s/d"
    return (
        f"às {hora_app} mostrava “última atualização {impresso}” e {inteiro(r['nacional_st_visivel'])} seções "
        f"({num(100 * r['nacional_st_visivel'] / total, 2)}%), enquanto o andamento do TSE marcava "
        f"{inteiro(r['andamento_br_st_visivel'])} e a soma das UFs, {inteiro(r['soma_ufs_st_visivel'])}"
    )


def falha_principal_imprensa(N: list[dict]) -> dict | None:
    com = [
        i
        for i in N
        if "congestionamento"
        in (i.get("resumo_1_linha", "") + i.get("titulo", "")).lower()
    ]
    ab = next((i for i in com if "Agência Brasil" in i.get("veiculo", "")), None)
    return ab or (com[0] if com else None)


def falha_abre(L: dict, paradas: list[dict]) -> str:
    pg = L["pausa_geral"]["lacunas"][0]
    return p(
        f"O arquivo nacional de presidente parou {VEZES.get(len(paradas), f'{len(paradas)} vezes')} no pico, por "
        + lista([num(t["minutos"], 0) for t in paradas])
        + f" minutos, e de {hora(pg['de_brt'])} a {hora(pg['ate_brt'])} o TSE não gerou arquivo de resultado de nenhum "
        f"cargo em nenhum nível, por {num(pg['minutos'], 0)} minutos. O banco da casa prova as duas coisas pela hora de "
        "geração de cada versão, guardada com SHA-256.",
        "verificado",
    )


def falha_camadas(
    L: dict, linhas: list[dict], N: list[dict] | None, hora_app: str
) -> str:
    d = L["divergencia_soma_ufs"]["maior_diferenca_visivel"]
    principal = falha_principal_imprensa(N or [])
    tse = (
        f' O tribunal, segundo a <a href="{escape(principal["url"])}">{escape(principal["veiculo"])}</a>: '
        "“congestionamento de dados” (Nunes Marques), fluxo acima do normal, sistemas isolados, totalização não afetada."
        if principal
        else ""
    )
    h = p(
        f"Três fontes, três relógios. No banco, às {d['hora_brt']} a soma dos arquivos de UF tinha "
        f"{inteiro(d['secoes'])} seções a mais que o nacional ({num(d['pp_do_total'], 2)}% do total). O aplicativo "
        f"oficial {falha_app_curta(L, linhas, hora_app)}.{tse}",
        "verificado",
    )
    h += p(
        "As paradas foram de publicação, não de contagem: a ordem dos candidatos nunca se inverteu. A causa não aparece "
        "nos dados.",
        "inferencia",
    )
    return h


def falha_juizo(paradas: list[dict], L: dict) -> str:
    longa = max((t["minutos"] for t in paradas), default=0)
    pg = L["pausa_geral"]["lacunas"][0]
    lei = pg["leituras_no_intervalo"]
    return nota(
        "juizo",
        f"Parar o arquivo de presidente por {num(longa, 0)} minutos na hora de maior atenção do país exige relatório "
        "técnico público. Faltam a origem do fluxo acima do normal, o motivo de o nacional parar enquanto as UFs "
        f"avançavam e o de nada ser gerado em {num(pg['minutos'], 0)} minutos. O coletor fez {inteiro(sum(lei.values()))} "
        f"leituras na pausa; {inteiro(lei.get('nao_modificado', 0))} voltaram “não modificado”.",
    )


def falha_correcao() -> str:
    return (
        "<p><strong>Correção.</strong> Ao vivo dissemos que os arquivos municipais seguiam atualizando na pausa geral. "
        "Não seguiam: nenhum arquivo de resultado foi gerado.</p>"
    )


# ------------------------------------------------------------------ 04 regiões


def regioes_a(P: dict) -> str:
    R = P["regioes"]
    cs, ne = R["Centro-Sul"], R["Nordeste"]
    swings = [(u["uf"], u["comparacao"]) for u in P["ufs"] if u["uf"] != "ZZ"]
    cresceu = [uf for uf, c in swings if c["flavio_vs_bolsonaro_1t"]["pp"] > 0]
    caiu = [uf for uf, c in swings if c["flavio_vs_bolsonaro_1t"]["pp"] <= 0]
    lula_up = [uf for uf, c in swings if c["lula_vs_lula_1t"]["pp"] > 0]
    return p(
        f"Flávio cresceu sobre Bolsonaro em {len(cresceu)} de {len(swings)} UFs"
        + (f" (exceção: {lista(caiu)})" if caiu else "")
        + f"; Lula, em {len(lula_up)}. Lula perdeu {sinal_int(cs['comparacao']['lula_vs_lula_1t']['votos'])} votos no Centro-Sul, "
        f"{num(cs['contribuicao_pct_da_variacao_nacional']['lula_menos_lula_1t'], 1)}% da perda total; no Nordeste, "
        f"{sinal_int(ne['comparacao']['lula_vs_lula_1t']['votos'])}.",
        "verificado",
    )


def regioes_b(P: dict) -> str:
    R = P["regioes"]
    hi, lo = P["por_faixa_lula_2022"][-1], P["por_faixa_lula_2022"][0]
    ne = R["Nordeste"]
    return p(
        f"Flávio cresceu mais onde Lula era mais forte: {sinal(hi['swing_flavio_pp'], 2)} ponto nos {inteiro(hi['municipios'])} "
        f"municípios com Lula entre {hi['faixa_lula_2022_pct']}% em 2022, {sinal(lo['swing_flavio_pp'], 2)} nos "
        f"{inteiro(lo['municipios'])} com {lo['faixa_lula_2022_pct']}%. No Nordeste ele fez "
        f"{pct(ne['r2026']['pct']['flavio'])}, acima de Bolsonaro no 1º turno de 2022.",
        "verificado",
    )


def regioes_c(P: dict) -> str:
    swings = [(u["uf"], u["comparacao"]) for u in P["ufs"] if u["uf"] != "ZZ"]
    top = sorted(swings, key=lambda s: -s[1]["virada_margem_vs_1t_pp"])[:3]
    baixo = min(swings, key=lambda s: s[1]["lula_vs_lula_1t"]["pp"])
    return p(
        "Maiores viradas de margem: "
        + lista([f"{uf} {sinal(c['virada_margem_vs_1t_pp'], 2)}" for uf, c in top])
        + f" pontos. Maior queda de Lula: {baixo[0]} ({sinal(baixo[1]['lula_vs_lula_1t']['pp'], 2)}).",
        "verificado",
    )


def regioes_d(P: dict) -> str:
    caps = [c for c in P["capitais"] if c.get("swing_flavio_pp") is not None]
    cresc = sum(1 for c in caps if c["swing_flavio_pp"] > 0)
    lula = sum(1 for c in caps if (c.get("swing_lula_pp") or 0) > 0)
    return p(
        f"Flávio cresceu sobre Bolsonaro em {cresc} das {len(caps)} capitais; Lula cresceu sobre si mesmo em {lula}.",
        "verificado",
    )


def regioes_e(P: dict) -> str:
    R = P["regioes"]
    cs, ne, no = R["Centro-Sul"], R["Nordeste"], R["Norte"]
    nec = ne["comparacao"]
    return p(
        f"O comparecimento subiu no Norte ({sinal(no['comparacao']['comparecimento_vs_1t_pp'], 2)}) e no Nordeste "
        f"({sinal(nec['comparecimento_vs_1t_pp'], 2)}) e caiu no Centro-Sul ({sinal(cs['comparacao']['comparecimento_vs_1t_pp'], 2)}). "
        f"No Nordeste, Flávio ganhou {sinal_int(nec['flavio_vs_bolsonaro_1t']['votos'])} votos e Lula perdeu "
        f"{sinal_int(nec['lula_vs_lula_1t']['votos'])}: o saldo é compatível com voto novo e eleitor de terceira via. "
        "Dado agregado não identifica quem trocou de voto.",
        "inferencia",
    )


# ------------------------------------------------------------------ 05 exterior


def exterior_a(E: dict, P: dict) -> str:
    t = E["total"]
    zz = next(u for u in P["ufs"] if u["uf"] == "ZZ")
    c = zz["comparacao"]
    return p(
        f"Lula venceu no exterior: {pct(zz['pct']['lula'])} contra {pct(zz['pct']['flavio'])}, {inteiro(abs(zz['margem_votos']))} votos "
        f"de diferença, {inteiro(t['secoes'])} seções em {t['cidades']} cidades de {t['paises']} países. O comparecimento foi de "
        f"{pct(t['pct_comparecimento'])}, {num(abs(c['comparecimento_vs_1t_pp']), 2)} pontos abaixo do 1º turno de 2022.",
        "verificado",
    )


def exterior_b(E: dict) -> str:
    conts = sorted(E["continentes"], key=lambda x: -x["validos"])[:3]
    lider = [
        f"{x['continente']} ({'Flávio' if x['pct']['flavio'] > x['pct']['lula'] else 'Lula'} "
        f"{pct(max(x['pct']['flavio'], x['pct']['lula']))})"
        for x in conts
    ]
    pt = next((x for x in E["paises"] if x["pais"] == "PT"), None)
    extra = (
        f" Portugal deu a Flávio {pct(pt['pct']['flavio'])}, {sinal(pt['swing_flavio_vs_bolsonaro_1t_pp'], 2)} pontos sobre Bolsonaro nas mesmas cidades."
        if pt
        else ""
    )
    return p("Maiores colégios: " + lista(lider) + "." + extra, "verificado")
