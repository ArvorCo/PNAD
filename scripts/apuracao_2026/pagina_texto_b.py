"""Frases curtas dos capítulos 06 a 14 do dossiê da apuração, geradas dos números."""

from __future__ import annotations

import math
from collections import Counter
from html import escape

from .pagina_comum import (
    NOME_UF,
    ROTULO_CAMPO,
    inteiro,
    milhoes,
    nome_proprio,
    num,
    p,
    sinal,
)
from .pagina_texto import lista, pct


def maioria(n: int) -> int:
    return n // 2 + 1


def tres_quintos(n: int) -> int:
    return math.ceil(n * 3 / 5)


# ------------------------------------------------------------------ 06 Câmara


def camara_a(C: dict) -> str:
    n = C["vagas_total"]
    b = C["blocos"]
    dir_ = b["direita + centro-direita"]
    return p(
        f"Direita e centro-direita somam <strong>{dir_}</strong> das {n} cadeiras; esquerda e centro-esquerda, "
        f"{b['esquerda + centro-esquerda']}; centro, {b['centro']}. O bloco passa da maioria simples ({maioria(n)}) e fica "
        f"{tres_quintos(n) - dir_} cadeiras abaixo dos três quintos ({tres_quintos(n)}) da emenda constitucional.",
        "verificado",
    )


def camara_b(C: dict) -> str:
    partidos = sorted(C["por_partido"].items(), key=lambda kv: -kv[1])
    top = C["deputados_mais_votados"][0]
    return p(
        "Maiores bancadas: "
        + lista([f"{escape(k)} {v}" for k, v in partidos[:5]])
        + f". O deputado mais votado é {nome_proprio(top['nome'])} ({escape(top['partido'])}-{top['uf']}), "
        f"{inteiro(top['votos'])} votos, {pct(top['pct_na_uf'])} dos válidos da UF.",
        "verificado",
    )


def camara_c(C: dict) -> str:
    vp, cp = C["votos_por_campo_pct"], C["por_campo_pct"]
    return p(
        f"A direita teve {pct(vp['direita'])} dos votos e {pct(cp['direita'])} das cadeiras; a esquerda, "
        f"{pct(vp['esquerda'])} dos votos e {pct(cp['esquerda'])} das cadeiras. Votos de partido: nominais e de legenda somados.",
        "verificado",
    )


def camara_d(C: dict) -> str:
    conf = C.get("conferencia_provisorio_x_tse", [])
    iguais = sum(1 for x in conf if x.get("partidos_iguais") and x.get("mesmos_nomes"))
    if not C.get("ufs_provisorias"):
        return ""
    return p(
        f"O TSE fechou a lista em {C['n_ufs_tse']} UFs. Em {len(C['ufs_provisorias'])} ({lista(C['ufs_provisorias'])}) a "
        f"distribuição é provisória, pelo quociente da casa, que reproduziu o TSE nome a nome em {iguais} de {len(conf)} UFs fechadas.",
        "inferencia",
    )


# ------------------------------------------------------------------ 07 Senado


def senado_a(S: dict) -> str:
    s = S["senado_2027"]
    n, b = s["total"], s["por_bloco"]
    return p(
        f"O Senado de 2027 terá {n} cadeiras: {s['continuam']} de eleitos em 2022 e {s['novos']} de agora. Direita e "
        f"centro-direita somam <strong>{b['direita + centro-direita']}</strong>; esquerda e centro-esquerda, "
        f"{b['esquerda + centro-esquerda']}; centro, {b['centro']}. Passa da maioria absoluta ({maioria(n)}) e dos três "
        f"quintos ({tres_quintos(n)}).",
        "verificado",
    ) + p(
        "Bloco de campo não é bancada disciplinada, e o centro decide o quórum qualificado. Votação certa não decorre da soma.",
        "juizo",
    )


def senado_b(S: dict) -> str:
    s = S["senado_2027"]
    pl_novos = S["eleitos_2026_por_partido"].get("PL", 0)
    dob = sorted(
        u
        for u, k in Counter(
            e["uf"] for e in S["eleitos_2026"] if e["partido"] == "PL"
        ).items()
        if k == 2
    )
    return p(
        f"O PL terá {s['por_partido'].get('PL', 0)} senadores, {pl_novos} eleitos em 2026, com as duas vagas em "
        f"{len(dob)} UFs ({lista(dob)}). O PT terá {s['por_partido'].get('PT', 0)}.",
        "verificado",
    )


def senado_c(S: dict) -> str:
    eleitos = {(e["uf"], e["vaga"]): e for e in S["eleitos_2026"]}
    frases = []
    for d in sorted(S["disputas"], key=lambda d: d["margem_2a_vaga_pp"])[:3]:
        seg, ter = eleitos.get((d["uf"], 2)), d["terceiro"]
        if seg:
            frases.append(
                f"{d['uf']}: {nome_proprio(seg['nome'])} ({escape(seg['partido'])}) sobre {nome_proprio(ter['nome'])} "
                f"({escape(ter['partido'])}) por {num(d['margem_2a_vaga_pp'], 2)} ponto ({inteiro(d['margem_2a_vaga_votos'])} votos)"
            )
    n_prov = S.get("n_ufs_provisorio") or 0
    nota = (
        f" {n_prov} {'UF segue provisória' if n_prov == 1 else 'UFs seguem provisórias'} até a marca do TSE."
        if n_prov
        else ""
    )
    return p(
        "Segundas vagas mais apertadas. " + "; ".join(frases) + "." + nota, "verificado"
    )


# ------------------------------------------------------------------ 08 Assembleias


def assembleias_a(A: dict) -> str:
    casas = A["casas"]
    total = sum(c["vagas"] for c in casas)
    dir_ = sum(c["blocos"].get("direita + centro-direita", 0) for c in casas)
    esq = sum(c["blocos"].get("esquerda + centro-esquerda", 0) for c in casas)
    maior = [
        c["uf"]
        for c in casas
        if c["blocos"].get("esquerda + centro-esquerda", 0)
        > c["blocos"].get("direita + centro-direita", 0)
    ]
    return p(
        f"Nas {len(casas)} assembleias, {total} cadeiras: direita e centro-direita com {dir_}, esquerda e centro-esquerda com "
        f"{esq}. A esquerda só tem bloco maior em {lista(maior) if maior else 'nenhuma delas'}.",
        "verificado",
    )


def assembleias_b(A: dict) -> str:
    casas = A["casas"]
    topo = max(
        ((c["uf"], m) for c in casas for m in c.get("mais_votados", [])[:1]),
        key=lambda x: x[1]["votos"],
    )
    prov = [c["uf"] for c in casas if c.get("fonte") != "tse"]
    ressalva = (
        f" Composição provisória em {lista(prov)}, pelo quociente usado na Câmara."
        if prov
        else ""
    )
    return p(
        f"A candidatura mais votada para assembleia foi {nome_proprio(topo[1]['nome'])} ({escape(topo[1]['partido'])}-{topo[0]}), "
        f"{inteiro(topo[1]['votos'])} votos, {pct(topo[1]['pct'])} dos válidos da UF.{ressalva}",
        "verificado",
    )


# ------------------------------------------------------------------ 09 Governadores


def governadores_a(G: dict) -> str:
    e = G["eleitos_1t_por_campo"]
    segundo = [u["uf"] for u in G["ufs"] if u["decisao"] == "segundo_turno"]
    return p(
        f"{G['n_eleitos_1t']} governadores saíram eleitos no 1º turno: direita {e['direita']}, centro-direita "
        f"{e['centro-direita']}, centro {e['centro']}, centro-esquerda {e['centro-esquerda']}, esquerda {e['esquerda']}. "
        f"Há 2º turno em {G['n_segundo_turno']} UFs ({lista(segundo)}).",
        "verificado",
    )


def governadores_b(G: dict) -> str:
    V = G["vao_estadual"]
    vao = sorted(V["lista"], key=lambda v: -v["vao_pp"])
    com_lado_todos = [v for v in vao if v.get("comparacao") != "sem apoio declarado"]
    pos = [v for v in com_lado_todos if v["vao_pp"] > 0][:3]
    neg = [v for v in com_lado_todos if v["vao_pp"] < 0][-3:]

    def f(v):
        return (
            f"{v['uf'].upper()} {nome_proprio(v['governador'])} {sinal(v['vao_pp'], 1)}"
        )

    texto = p(
        "O vão compara, na mesma urna, a candidatura ao governo com o finalista presidencial do lado dela. Maiores "
        "positivos: "
        + lista([f(v) for v in pos])
        + "; negativos mais fundos: "
        + lista([f(v) for v in neg])
        + ". É <strong>teto endereçável, nunca transferência certa</strong>.",
        "inferencia",
    )
    centro = V.get("centro", [])
    if not centro:
        return texto
    sem = [c for c in centro if c["comparacao"] == "sem apoio declarado"]

    def fc(c, chave):
        return f"{c['uf']} {nome_proprio(c['governador'])} {sinal(c[chave], 1)}"

    partes = []
    if sem:
        partes.append(
            "Do centro sem apoio declarado, "
            + lista(
                [
                    f"{fc(c, 'vao_flavio_pp')} contra Flávio ({sinal(c['vao_lula_pp'], 1)} contra Lula)"
                    for c in sem
                ]
            )
            + "."
        )
    excecoes = [
        v
        for v in vao
        if v["campo"] != "centro" and v.get("comparacao") not in (None, "mesmo bloco")
    ]
    for v in excecoes:
        partes.append(
            f" {nome_proprio(v['governador'])} ({escape(v['partido'])}-{v['uf'].upper()}) é de "
            f"{ROTULO_CAMPO.get(v['campo'], v['campo']).lower()} com o PT na coligação: {sinal(v['vao_lula_pp'], 1)} contra "
            f"Lula, {sinal(v['vao_flavio_pp'], 1)} contra Flávio."
        )
    return texto + p("".join(partes), "inferencia")


def governadores_c(G: dict) -> str:
    gx = G["governador_x_presidente"]
    perto = G.get("mais_perto_de_50", [])
    ptxt = (
        " Mais perto de 50%: "
        + lista(
            [
                f"{nome_proprio(x['lider']['nome'])} ({x['uf']}) {pct(x['lider']['pct'])} "
                f"({'eleito' if x['decisao'] == 'eleito' else '2º turno'})"
                for x in perto
            ]
        )
        + "."
        if perto
        else ""
    )
    return p(
        f"Em {gx['ufs_campo_difere']} UFs o governador eleito ou líder é de campo diferente do presidenciável que "
        f"venceu ali; em {gx['ufs_bloco_difere']}, de bloco diferente.{ptxt}",
        "verificado",
    )


# ------------------------------------------------------------------ 10 Pesquisas


def pesquisas_a(PV: dict) -> str:
    r = PV["resumo_ultimas_ondas"]
    pub = r["publicado"]
    ref = PV["referencia_2022"]
    return p(
        f"Na última onda de {pub['n']} institutos, o erro médio na diferença Lula menos Flávio foi "
        f"<strong>{sinal(pub['media'], 2)} pontos</strong> a favor de Lula (mediana {sinal(pub['mediana'], 2)}). "
        f"{pub['positivos']} de {pub['n']} superestimaram Lula; {pub['fora_da_margem_aas']} erraram além da margem de 95%. "
        f"Em 2022, a média de {ref['n_casas']} casas errou {sinal(ref['erro_comum_diferenca_lula_menos_bolsonaro'], 2)}. "
        f"A dispersão entre institutos ({num(pub['desvio_padrao'], 2)}) supera a de amostragem pura "
        f"({num(pub['desvio_esperado_so_amostragem_aas_pp'], 2)}).",
        "verificado",
    )


def pesquisas_proximidade(PV: dict) -> str:
    r = PV["resumo_ultimas_ondas"]
    n = r["publicado"]["n"]
    ult = sorted(
        (x for x in PV["pesquisas"] if x.get("ultima_onda_da_casa")),
        key=lambda x: abs(x["publicado"]["diferenca_lula_menos_flavio"]["erro"]),
    )
    if len(ult) < 2:
        return ""
    a, b = ult[:2]
    ea = abs(a["publicado"]["diferenca_lula_menos_flavio"]["erro"])
    eb = abs(b["publicado"]["diferenca_lula_menos_flavio"]["erro"])
    return p(
        f"<strong>Proximidade não é acerto.</strong> {escape(a['instituto'])} e {escape(b['instituto'])} ficaram a {num(ea, 2)} "
        f"e {num(eb, 2)} ponto da urna, mas eram das casas mais pró-Flávio antes dela: chegaram perto porque o erro comum foi grande. "
        f"Uma eleição é uma observação, e a chance de ao menos uma de {n} casas cair a meio ponto só por dispersão seria de "
        f"{num(100 * r['prob_alguma_casa_a_meio_ponto_por_acaso'], 0)}%.",
        "juizo",
    )


def pesquisas_reponderacao(PV: dict) -> str:
    m = PV["medias"]
    ag_pub = m["agregador_publicado"]["diferenca_lula_menos_flavio"]["erro"]
    ag_rep = m["agregador_reponderado"]["diferenca_lula_menos_flavio"]["erro"]
    ef = PV["efeito_reponderacao"]["ultimas_ondas"]
    rep = PV["resumo_ultimas_ondas"]["reponderado"]
    return p(
        f"A reponderação por renda levou o erro do agregador de {sinal(ag_pub, 2)} para {sinal(ag_rep, 2)} pontos: "
        f"{ef['aproximou']} de {ef['n']} ondas andaram para a urna, {ef['afastou']} se afastaram. A média reponderada ainda "
        f"erra {sinal(rep['media'], 2)}. É sensibilidade de uma margem, não resultado corrigido.",
        "verificado",
    )


def pesquisas_central(PV: dict) -> str:
    cc = PV["previsao_casa"]["central"]
    mc = PV["previsao_casa"]["monte_carlo"]
    tv = mc["intervalos_90_validos"]["terceira_via"]
    return p(
        f"A central da casa deu Flávio {num(cc['validos']['flavio'], 2)} e Lula {num(cc['validos']['lula'], 2)}; o erro na "
        f"diferença foi {sinal(cc['erro_diferenca_lula_menos_flavio'], 2)}, menor que o da média das pesquisas. A casa dava "
        f"{num(100 * mc['p_flavio_a_frente_de_lula'], 0)}% de chance de Flávio à frente: disse empate, não previu o vencedor. "
        f"A urna caiu no percentil {num(100 * mc['margem_flavio_menos_lula']['percentil_urna'], 0)}. O ponto fraco foi a "
        f"consolidação: a terceira via teve {pct(tv['urna'])}, abaixo do percentil 5 do Monte Carlo ({pct(tv['p05'])}).",
        "verificado",
    )


def pesquisas_estaduais(PV: dict) -> str:
    g = PV["governador"]["resumo"]
    s = PV["senado"]["resumo"]
    return p(
        f"Governadores: o líder previsto liderou em {g['acertos_lider']} de {g['n_ufs']} UFs; {g['decididos_1t_urna']} UFs "
        f"decidiram no 1º turno contra {num(g['decididos_1t_esperado'], 1)} esperadas. Senado: as duas candidaturas mais "
        f"prováveis levaram {s['acertos_top2']} de {s['vagas']} vagas, contra {num(s['acertos_top2_esperados'], 1)} esperadas; "
        f"Brier {num(s['brier'], 3)}.",
        "verificado",
    )


# ------------------------------------------------------------------ 11 Voto útil


def voto_util_a(V: dict) -> str:
    tv = V["terceira_via"]
    tc = V["terceiros_por_candidato"]["publicado"]
    nomes = {
        "renan_santos": "Renan Santos",
        "caiado": "Caiado",
        "cury": "Cury",
        "zema": "Zema",
        "demais": "demais",
    }
    quedas = sorted(tc["queda_pp"].items(), key=lambda kv: -kv[1])[:4]
    princ = V["decomposicao"]["agregados"]["ultimas_ondas_publicado"][
        "nexus_renormalizada"
    ]
    return p(
        f"As últimas ondas de {tv['n_publicado_todas']} institutos davam {pct(tv['media_publicado_todas'])} à terceira via; a urna deu "
        f"<strong>{pct(tv['urna_validos'])}</strong>. Perderam: "
        + lista([f"{nomes.get(k, k)} {sinal(-v, 2)}" for k, v in quedas])
        + f". Ganharam: Flávio {sinal(princ['ganho_flavio_pp'], 2)} e Lula {sinal(princ['ganho_lula_pp'], 2)}. O voto útil foi de um lado só.",
        "verificado",
    )


def voto_util_b(V: dict) -> str:
    agg = V["decomposicao"]["agregados"]["ultimas_ondas_publicado"]
    princ = agg["nexus_renormalizada"]
    fr = [
        agg[k]["fracao_explicada_diferenca"]
        for k in agg
        if "fracao_explicada_diferenca" in agg[k] and k != "proporcional"
    ]
    return p(
        f"Pela matriz da Nexus, a consolidação explica {sinal(princ['explicado_diferenca_pp'], 2)} dos "
        f"{sinal(princ['erro_diferenca_lula_menos_flavio_pp'], 2)} pontos de erro ({num(100 * min(fr), 0)}% a {num(100 * max(fr), 0)}% "
        "conforme a variante). O resto é deslocamento entre os finalistas, que os dados não separam; a matriz foi medida duas "
        "semanas antes da eleição.",
        "hipotese",
    )


def voto_util_c(V: dict) -> str:
    rn = V["reserva_nacional"]
    return p(
        f"Nas mesmas pesquisas, Flávio tinha {num(rn['reserva_media_flavio_pp'], 2)} pontos a mais no 2º turno que no 1º; Lula, "
        f"{num(rn['reserva_media_lula_pp'], 2)}. A urna revelou no 1º turno a mediana de {num(100 * rn['lambda_flavio']['mediana'], 0)}% "
        f"da reserva de Flávio e {num(100 * rn['theta_lula']['mediana'], 0)}% da de Lula.",
        "inferencia",
    )


# ------------------------------------------------------------------ 12 Anomalias


def anomalias_a(A: dict) -> str:
    r, topo = A["resumo"], A["topo"]
    local = [
        t
        for t in topo
        if any("efeito político local" in e for e in t.get("explicacao_provavel", []))
    ]
    return p(
        f"A triagem comparou cada uma das {inteiro(r['n_zonas'])} zonas com a própria UF e com 2022, por quatro leituras (z robusto, "
        f"Mahalanobis, Isolation Forest e LOF). <strong>Nenhuma das {len(topo)} zonas mais atípicas aponta irregularidade.</strong> "
        f"{len(topo) - len(local)} têm explicação comum provável; {len(local)} ficam como hipótese de política local, a conferir "
        f"seção por seção. {r['pequenas_ate_30_secoes']['topo']} têm até 30 seções.",
        "inferencia",
    )


def anomalias_b(A: dict) -> str:
    td = A["resumo"]["tardias"]
    return p(
        f"As {td['n']} zonas que fecharam bem depois da própria UF votaram como as demais em relação à região: o resíduo da "
        f"margem foi {sinal(td['residuo_medio_pp_tardias'], 2)} ponto nelas e {sinal(td['residuo_medio_pp_demais'], 2)} nas outras "
        f"(correlação entre atraso e resíduo {sinal(td['correlacao_atraso_residuo'], 3)}). O movimento extra é efeito do estado, não da demora.",
        "verificado",
    )


def anomalias_c(A: dict, n_itens: int | None, n_oficiais: int | None) -> str:
    s1 = A.get("robustez", {}).get("semente_1", {})
    ctx = (
        f" A casa reuniu {n_itens} registros de segurança e logística do dia, {n_oficiais} oficiais."
        if n_itens
        else ""
    )
    return p(
        f"Com outra semente, {s1.get('comuns_topo', 's/d')} das {s1.get('n_topo', 's/d')} zonas se repetem. Atipicidade não é "
        "irregularidade: provar ou descartar exige boletim de urna, ata da mesa e log da urna, que o TSE publica."
        + ctx,
        "juizo",
    )


# ------------------------------------------------------------------ 13 2º turno


def segundo_turno_a(E: dict) -> str:
    ar = E["aritmetica"]
    pt, proj = ar["primeiro_turno"], ar["projecoes"]
    mn = min(proj, key=lambda x: x["margem_votos"])
    mx = max(proj, key=lambda x: x["margem_votos"])
    return p(
        f"Flávio sai com {milhoes(pt['diferenca_votos'])} de votos de vantagem; o 2º turno começa nos {milhoes(pt['terceiros_total'])} "
        f"dados a outras candidaturas ({pct(pt['terceiros_pct'])}). Com as matrizes publicadas (Nexus e Datafolha) e três hipóteses "
        f"para a não escolha, Flávio vai de {pct(mn['flavio_pct'])} a {pct(mx['flavio_pct'])} dos válidos, margem de "
        f"{milhoes(mn['margem_votos'])} a {milhoes(mx['margem_votos'])}. Nenhuma das seis combinações desfaz a vantagem.",
        "inferencia",
    )


def segundo_turno_b(E: dict) -> str:
    eq = E["aritmetica"]["equilibrio"]
    ne = eq["nao_escolha_toda_para_lula"]["nexus"]
    return p(
        f"Para virar só com a terceira via, Lula precisaria de {pct(eq['lula_precisa_se_todos_votarem_pct'])} desses votos; a Nexus "
        f"mede {pct(eq['lula_medido_entre_quem_escolhe_pct'])} entre quem escolhe. Com toda a não escolha indo para Lula, Flávio "
        f"ficaria {milhoes(ne['margem_flavio_se_toda_for_lula'])} à frente.",
        "inferencia",
    )


def segundo_turno_c(E: dict) -> str:
    eq = E["aritmetica"]["equilibrio"]
    ri = E["riscos"]["estoque_lula_maior"]
    return p(
        f"O risco está na base e no comparecimento. Se {pct(eq['base_flavio_trocando_para_lula_pct'])} "
        f"da base de Flávio trocar de lado, ou {pct(eq['base_flavio_abstendo_pct'])} deixar de votar, a margem central some. O estoque "
        f"de 2022 que Lula não reconquistou ({milhoes(ri['estoque_lula'])}) é {num(ri['razao'], 2)} vezes o de Flávio "
        f"({milhoes(ri['estoque_flavio'])}).",
        "contrario",
    )


def segundo_turno_d(E: dict) -> str:
    an = E["aritmetica"]["analogo_2022"]["nacional"]
    est = E["geografia"]["estoque"]
    return p(
        f"Se cada voto de terceira via rendesse o que rendeu entre os turnos de 2022, Flávio teria {pct(an['flavio_pct'])}. É uma "
        f"eleição só, com terceiros diferentes: mede ordem de grandeza, não destino. {num(est['top5_ufs_parcela_pct'], 0)}% do "
        "estoque de Flávio está em cinco UFs.",
        "hipotese",
    )


def segundo_turno_riscos(E: dict) -> str:
    ri = E["riscos"]
    out = []
    pu = ri.get("piores_ufs_votos_contra_2t_2022", [])
    if pu:
        out.append(
            p(
                "Onde Flávio mais fica abaixo de Bolsonaro no 2º turno de 2022, em votos: "
                + lista(
                    [
                        f"{x['uf']} {sinal(x['flavio_menos_bolsonaro_2t_votos'], 0)}"
                        for x in pu
                    ]
                )
                + ".",
                "verificado",
            )
        )
    gd = ri.get("governador_direita_eleito_flavio_perdeu", [])
    if gd:
        out.append(
            p(
                "Governador de direita eleito onde Flávio perdeu: "
                + lista(
                    [
                        f"{x['uf']}, {nome_proprio(x['governador'])} ({escape(x['partido'])}) {num(x['governador_pct'], 2)}%, "
                        f"Lula {num(x['lula_pct'], 2)} × Flávio {num(x['flavio_pct'], 2)}"
                        for x in gd
                    ]
                )
                + ". O eleitor desses governadores não seguiu o campo na eleição presidencial.",
                "verificado",
            )
        )
    return "".join(out)


# ------------------------------------------------------------------ 14 Auditoria


def auditoria_a(P: dict) -> str:
    mc = P["meta_contagens"]
    conf = P["conferencia"]
    sm, su = conf["soma_municipios_menos_nacional"], conf["soma_ufs_menos_nacional"]
    inc = conf["municipios_incompletos"]
    return p(
        f"O coletor guardou {inteiro(mc['snapshots'])} versões de {inteiro(mc['arquivos'])} arquivos em {inteiro(mc['fetches'])} leituras, "
        f"cada uma com hora de geração, hora de leitura e SHA-256. A soma das UFs bate com o nacional (diferença de {inteiro(su['secoes'])} "
        f"seções); a dos municípios fica {inteiro(abs(sm['secoes']))} seções e {inteiro(abs(sm['validos']))} válidos abaixo, porque "
        f"{len(inc)} arquivos municipais congelaram incompletos.",
        "verificado",
    )


def auditoria_b(L: dict) -> str:
    lat = [x for x in L["latencia"]["por_hora"] if x["grupo"] == "presidente_br"]
    p50 = sorted(x["p50_s"] for x in lat)
    mediana = p50[len(p50) // 2] if p50 else None
    return p(
        f"A latência mediana do arquivo nacional na noite foi de {num(mediana, 0)} segundos (capítulo 3), teto da demora "
        "de publicação, porque inclui o intervalo de sondagem.",
        "verificado",
    )


def nome_uf(uf: str) -> str:
    return NOME_UF.get(uf, uf)


def campo(c: str) -> str:
    return ROTULO_CAMPO.get(c, c)
