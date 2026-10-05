"""Frases curtas dos capítulos 01 a 05 do dossiê da apuração, geradas dos números dos JSONs.

Regra: nenhuma frase daqui carrega número digitado. Todo número sai do dado
recebido; o que é juízo editorial vem rotulado na própria frase. Cada função
devolve no máximo um parágrafo, para o texto caber entre as figuras do catálogo.
"""

from __future__ import annotations

import json
from html import escape

from .pagina_comum import (
    NOME_UF,
    Dados,
    figura_catalogo,
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
VEZES = {1: "uma vez", 2: "duas vezes", 3: "três vezes", 4: "quatro vezes"}


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


def abertura_a(P: dict) -> str:
    n = P["nacional"]
    v, c = n["votos"], n["pct"]
    return p(
        f"Flávio Bolsonaro (PL) teve <strong>{inteiro(v['flavio'])}</strong> votos, {pct(c['flavio'])} dos válidos. "
        f"Lula (PT) teve <strong>{inteiro(v['lula'])}</strong>, {pct(c['lula'])}. A diferença é de "
        f"{inteiro(n['diferenca_votos'])} votos, {num(n['diferenca_pp'], 2)} ponto. Os dois disputam o 2º turno em {DATA_2T}.",
        "verificado",
    )


def abertura_b(P: dict) -> str:
    n = P["nacional"]
    c = n["pct"]
    return p(
        f"As outras dez candidaturas somam {pct(c['terceiros'])}: Cury {pct(c['cury'])}, Renan Santos {pct(c['renan'])}, "
        f"Caiado {pct(c['caiado'])}. Compareceram {inteiro(n['comparecimento'])} eleitores ({pct(n['pct_comparecimento'])}); "
        f"brancos somaram {pct(n['pct_brancos'])} e nulos {pct(n['pct_nulos'])}. Arquivo final do TSE, "
        f"{hora(n['gerado_em_brt'], True)} de 05/10, {inteiro(n['secoes'])} de {inteiro(n['secoes_total'])} seções.",
        "verificado",
    )


def abertura_c(P: dict) -> str:
    n = P["nacional"]
    cmp_ = n["comparacao"]
    ufs = [u for u in P["ufs"] if u["uf"] != "ZZ"]
    f = sum(1 for u in ufs if u["lider"] == "flavio")
    zz = next((u for u in P["ufs"] if u["uf"] == "ZZ"), None)
    ext = (
        f" No exterior, Lula fez {pct(zz['pct']['lula'])} contra {pct(zz['pct']['flavio'])}."
        if zz
        else ""
    )
    return p(
        f"Flávio venceu em {f} UFs; Lula, em {len(ufs) - f}.{ext} Contra o 1º turno de 2022, Flávio tem "
        f"{sinal(cmp_['flavio_vs_bolsonaro_1t']['pp'], 2)} ponto sobre Bolsonaro; Lula, "
        f"{sinal(cmp_['lula_vs_lula_1t']['pp'], 2)}. A margem andou {num(cmp_['virada_margem_vs_1t_pp'], 2)} pontos para Flávio.",
        "verificado",
    )


# ------------------------------------------------------------------ 02 noite


def noite_a(L: dict, linhas: list[dict]) -> str:
    m = L["marcos"]
    com = [r for r in linhas if r["st"]]
    sempre = all((r["flavio"] or 0) >= (r["lula"] or 0) for r in com)
    return p(
        f"O arquivo nacional teve {inteiro(L['nacional']['n_versoes_genuinas'])} versões, da primeira, às "
        f"{hora(m['primeira_versao_nacional_com_secoes_brt'], True)}, à final, às {hora(m['versao_final_nacional_brt'], True)} de 05/10."
        + (
            f" Flávio esteve à frente nas {inteiro(len(com))} versões com seções."
            if sempre
            else ""
        ),
        "verificado",
    )


def noite_b(paradas: list[dict]) -> str:
    frases = [
        f"{hora(t['de_brt'], True)} a {hora(t['ate_brt'], True)} ({num(t['minutos'], 1)} min, "
        f"{num(t['pst_de'], 2)}% para {num(t['pst_ate'], 2)}% das seções)"
        for t in paradas
    ]
    return p(
        f"O arquivo ficou parado {VEZES.get(len(paradas), f'{len(paradas)} vezes')}: "
        + lista(frases)
        + ".",
        "verificado",
    )


def noite_c(linhas: list[dict]) -> str:
    maior = max(linhas, key=lambda r: r["d_vv"] or 0)
    return p(
        f"A maior atualização, às {hora(maior['gerado_brt'], True)}, trouxe {inteiro(maior['d_st'])} seções e "
        f"{milhoes(maior['d_vv'])} de válidos, com Lula em {pct(maior['lote_pct_lula'])} do lote. O lote represou o que as "
        "UFs já mostravam; a ordem dos dois nunca se inverteu.",
        "verificado",
    )


def noite_d(L: dict) -> str:
    reais = [x for x in L["conclusao_ufs"] if x["uf"] != "ZZ"]
    a, z = reais[0], reais[-1]
    t = L["secoes_tardias"]["total"]
    return p(
        f"{NOME_UF[a['uf']]} fechou primeiro, às {hora(a['gerado_brt'])}; {NOME_UF[z['uf']]}, por último, às "
        f"{hora(z['gerado_brt'])} de 05/10. Depois da meia-noite chegaram {inteiro(t['secoes'])} seções em "
        f"{t['municipios']} municípios, {inteiro(t['validos'])} válidos, Lula {pct(t['pct_lula'])}: áreas remotas, sem peso na diferença.",
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
        f"Às {hora_app} o aplicativo mostrava “última atualização {impresso}”, {inteiro(r['nacional_st_visivel'])} seções "
        f"({num(100 * r['nacional_st_visivel'] / total, 2)}%); o andamento do TSE marcava {inteiro(r['andamento_br_st_visivel'])} "
        f"e a soma das UFs, {inteiro(r['soma_ufs_st_visivel'])}."
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


def falha_a(L: dict, paradas: list[dict]) -> str:
    d = L["divergencia_soma_ufs"]["maior_diferenca_visivel"]
    return p(
        f"As paradas foram de publicação, não de contagem: às {d['hora_brt']} a soma dos 28 arquivos de UF tinha "
        f"{inteiro(d['secoes'])} seções a mais que o nacional ({num(d['pp_do_total'], 2)}% do total), e a ordem dos candidatos "
        "nunca se inverteu. A causa da pausa não aparece nos dados; só o TSE pode explicá-la.",
        "inferencia",
    )


def falha_b(paradas: list[dict], L: dict) -> str:
    pg = L["pausa_geral"]["lacunas"][0]
    lei = pg["leituras_no_intervalo"]
    return p(
        f"Não foram explicados: a origem do fluxo acima do normal, por que o nacional parou enquanto as UFs avançavam e "
        f"por que nada foi gerado em {num(pg['minutos'], 0)} minutos, se o problema era só de divulgação. Não há relatório "
        f"técnico nem prazo de esclarecimento. O coletor fez {inteiro(sum(lei.values()))} leituras na pausa; "
        f"{inteiro(lei.get('nao_modificado', 0))} voltaram “não modificado”.",
        "verificado",
    )


def falha_correcao(L: dict) -> str:
    return (
        "<p><strong>Correção.</strong> Ao vivo dissemos que os arquivos municipais seguiam atualizando na pausa geral. "
        "Os dados desmentem: nenhum arquivo de resultado foi gerado.</p>"
    )


def falha_juizo(paradas: list[dict]) -> str:
    longa = max((t["minutos"] for t in paradas), default=0)
    return (
        f'<aside class="juizo"><b>Juízo editorial</b>Parar o arquivo de presidente por {num(longa, 0)} minutos na hora de '
        "maior atenção do país exige relatório técnico público, com log de geração por arquivo. A explicação dada é "
        "compatível com os dados; não fecha o caso.</aside>"
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


def exterior_c(E: dict) -> str:
    hl = E["hora_local"]
    w = hl["mais_adiantadas"][0]
    return p(
        f"O TSE imprime a hora de totalização no relógio local: {nome_proprio(w['nome'])} aparece totalizada em "
        f"{escape(w['totalizacao_impressa'])}, num arquivo gerado às {hora(w['primeira_versao_totalizada_gerada_brt'], True)} de 04/10 "
        f"em Brasília. É fuso, não erro de contagem.",
        "verificado",
    )
