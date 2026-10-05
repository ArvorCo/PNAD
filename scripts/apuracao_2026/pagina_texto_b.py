"""Frases dos capítulos 06 a 14 do dossiê da apuração, geradas dos números."""

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


def camara(C: dict) -> str:
    n = C["vagas_total"]
    b = C["blocos"]
    dir_ = b["direita + centro-direita"]
    esq = b["esquerda + centro-esquerda"]
    cen = b["centro"]
    partidos = sorted(C["por_partido"].items(), key=lambda kv: -kv[1])
    vp = C["votos_por_campo_pct"]
    cp = C["por_campo_pct"]
    conf = C.get("conferencia_provisorio_x_tse", [])
    iguais = sum(1 for x in conf if x.get("partidos_iguais") and x.get("mesmos_nomes"))
    top = C["deputados_mais_votados"][0]
    out = [
        p(
            f"Direita e centro-direita somam <strong>{dir_}</strong> das {n} cadeiras; esquerda e centro-esquerda, "
            f"{esq}; centro, {cen}. O bloco da direita passa da maioria simples ({maioria(n)}) e fica "
            f"{tres_quintos(n) - dir_} cadeiras abaixo dos três quintos ({tres_quintos(n)}) que uma emenda "
            "constitucional exige.",
            "verificado",
        ),
        p(
            "Maiores bancadas: "
            + lista([f"{escape(k)} {v}" for k, v in partidos[:7]])
            + f". Em votos, a direita teve {pct(vp['direita'])} e ficou com {pct(cp['direita'])} das cadeiras; "
            f"a esquerda, {pct(vp['esquerda'])} dos votos e {pct(cp['esquerda'])} das cadeiras.",
            "verificado",
        ),
        p(
            f"O deputado mais votado do país foi {nome_proprio(top['nome'])} ({escape(top['partido'])}-{top['uf']}), "
            f"com {inteiro(top['votos'])} votos, {pct(top['pct_na_uf'])} dos válidos da UF."
        ),
    ]
    if C.get("ufs_provisorias"):
        out.append(
            p(
                f"{C['n_ufs_tse']} UFs têm a lista de eleitos fechada pelo TSE. Em {len(C['ufs_provisorias'])} "
                f"({lista(C['ufs_provisorias'])}) a distribuição é provisória, calculada pela casa com quociente "
                f"eleitoral e sobras. O mesmo cálculo reproduziu o TSE, partido a partido e nome a nome, em "
                f"{iguais} de {len(conf)} UFs fechadas.",
                "inferencia",
            )
        )
    return "".join(out)


# ------------------------------------------------------------------ 07 Senado


def senado(S: dict) -> str:
    s = S["senado_2027"]
    n = s["total"]
    b = s["por_bloco"]
    pl_novos = S["eleitos_2026_por_partido"].get("PL", 0)
    dobradinhas = sorted(
        u
        for u, k in Counter(
            e["uf"] for e in S["eleitos_2026"] if e["partido"] == "PL"
        ).items()
        if k == 2
    )
    apertadas = sorted(S["disputas"], key=lambda d: d["margem_2a_vaga_pp"])[:3]
    eleitos = {(e["uf"], e["vaga"]): e for e in S["eleitos_2026"]}
    frases = []
    for d in apertadas:
        seg = eleitos.get((d["uf"], 2))
        ter = d["terceiro"]
        if seg:
            frases.append(
                f"{d['uf']}: {nome_proprio(seg['nome'])} ({escape(seg['partido'])}) à frente de "
                f"{nome_proprio(ter['nome'])} ({escape(ter['partido'])}) por {num(d['margem_2a_vaga_pp'], 2)} ponto "
                f"({inteiro(d['margem_2a_vaga_votos'])} votos)"
            )
    out = [
        p(
            f"O Senado de 2027 terá {n} cadeiras: {s['continuam']} de senadores eleitos em 2022 e {s['novos']} eleitos agora. "
            f"Direita e centro-direita somam <strong>{b['direita + centro-direita']}</strong>; esquerda e "
            f"centro-esquerda, {b['esquerda + centro-esquerda']}; centro, {b['centro']}.",
            "verificado",
        ),
        p(
            f"{b['direita + centro-direita']} passa da maioria absoluta ({maioria(n)}) e dos três quintos "
            f"({tres_quintos(n)}) de uma emenda constitucional. Não quer dizer votação certa: bloco de campo não é "
            "bancada disciplinada, e o centro decide quórum qualificado.",
            "juizo",
        ),
        p(
            f"O PL terá {s['por_partido'].get('PL', 0)} senadores, {pl_novos} eleitos em 2026, com as duas vagas em "
            f"{len(dobradinhas)} UFs ({lista(dobradinhas)}). O PT terá {s['por_partido'].get('PT', 0)}.",
            "verificado",
        ),
    ]
    if frases:
        out.append(
            p(
                "As segundas vagas mais apertadas: " + "; ".join(frases) + ".",
                "verificado",
            )
        )
    if S.get("n_ufs_provisorio"):
        out.append(
            p(
                f"{S['n_ufs_tse']} UFs com situação final do TSE; {S['n_ufs_provisorio']} pelas duas mais votadas, "
                "provisória até a marca do tribunal."
            )
        )
    return "".join(out)


# ------------------------------------------------------------------ 08 Assembleias


def assembleias(A: dict) -> str:
    casas = A["casas"]
    total = sum(c["vagas"] for c in casas)
    dir_ = sum(c["blocos"].get("direita + centro-direita", 0) for c in casas)
    esq = sum(c["blocos"].get("esquerda + centro-esquerda", 0) for c in casas)
    esquerda_maior = [
        c["uf"]
        for c in casas
        if c["blocos"].get("esquerda + centro-esquerda", 0)
        > c["blocos"].get("direita + centro-direita", 0)
    ]
    topo = max(
        ((c["uf"], m) for c in casas for m in c.get("mais_votados", [])[:1]),
        key=lambda x: x[1]["votos"],
    )
    prov = [c["uf"] for c in casas if c.get("fonte") != "tse"]
    out = [
        p(
            f"Nas {len(casas)} assembleias deste capítulo, {total} cadeiras: direita e centro-direita com {dir_}, "
            f"esquerda e centro-esquerda com {esq}. A esquerda só tem bloco maior em "
            f"{lista(esquerda_maior) if esquerda_maior else 'nenhuma delas'}.",
            "verificado",
        ),
        p(
            f"A candidatura mais votada para assembleia no país foi {nome_proprio(topo[1]['nome'])} "
            f"({escape(topo[1]['partido'])}-{topo[0]}), com {inteiro(topo[1]['votos'])} votos, "
            f"{pct(topo[1]['pct'])} dos válidos da UF."
        ),
    ]
    if prov:
        out.append(
            p(
                f"Em {lista(prov)} a composição é provisória, pelo mesmo cálculo de quociente usado na Câmara.",
                "inferencia",
            )
        )
    return "".join(out)


# ------------------------------------------------------------------ 09 Governadores


def governadores(G: dict) -> str:
    e = G["eleitos_1t_por_campo"]
    segundo = [u for u in G["ufs"] if u["decisao"] == "segundo_turno"]
    perto = G.get("mais_perto_de_50", [])
    vao = sorted(G["vao_estadual"]["lista"], key=lambda v: -v["vao_pp"])
    pos = [v for v in vao if v["vao_pp"] > 0][:5]
    neg = [v for v in vao if v["vao_pp"] < 0][-3:]
    gx = G["governador_x_presidente"]
    out = [
        p(
            f"{G['n_eleitos_1t']} governadores saíram eleitos no 1º turno: direita {e['direita']}, centro-direita "
            f"{e['centro-direita']}, centro {e['centro']}, centro-esquerda {e['centro-esquerda']}, esquerda {e['esquerda']}. "
            f"Há 2º turno em {G['n_segundo_turno']} UFs ({lista([u['uf'] for u in segundo])}).",
            "verificado",
        )
    ]
    if perto:
        out.append(
            p(
                "Os mais perto de 50%: "
                + lista(
                    [
                        f"{x['uf']}, {nome_proprio(x['lider']['nome'])} com {pct(x['lider']['pct'])} "
                        f"({'eleito' if x['decisao'] == 'eleito' else '2º turno'})"
                        for x in perto
                    ]
                )
                + "."
            )
        )
    out.append(
        p(
            "O vão estadual compara, na mesma urna, a candidatura ao governo com o presidenciável do mesmo bloco. "
            "Os maiores positivos: "
            + lista(
                [
                    f"{v['uf'].upper()} {nome_proprio(v['governador'])} {sinal(v['vao_pp'], 1)}"
                    for v in pos
                ]
            )
            + ". Os negativos mais fundos: "
            + lista(
                [
                    f"{v['uf'].upper()} {nome_proprio(v['governador'])} {sinal(v['vao_pp'], 1)}"
                    for v in neg
                ]
            )
            + ". É <strong>teto endereçável, nunca transferência certa</strong>: governador bem votado não carrega "
            "eleitor para outro cargo por decreto.",
            "inferencia",
        )
    )
    out.append(
        p(
            f"Em {gx['ufs_campo_difere']} UFs o governador eleito ou líder é de campo diferente do presidenciável "
            f"que venceu ali; em {gx['ufs_bloco_difere']}, de bloco diferente.",
            "verificado",
        )
    )
    return "".join(out)


# ------------------------------------------------------------------ 10 Pesquisas


def pesquisas(PV: dict) -> str:
    r = PV["resumo_ultimas_ondas"]
    pub, rep = r["publicado"], r["reponderado"]
    ref = PV["referencia_2022"]
    m = PV["medias"]
    ag_pub = m["agregador_publicado"]["diferenca_lula_menos_flavio"]["erro"]
    ag_rep = m["agregador_reponderado"]["diferenca_lula_menos_flavio"]["erro"]
    ef = PV["efeito_reponderacao"]["ultimas_ondas"]
    ult = sorted(
        (x for x in PV["pesquisas"] if x.get("ultima_onda_da_casa")),
        key=lambda x: abs(x["publicado"]["diferenca_lula_menos_flavio"]["erro"]),
    )
    perto = ult[:2]
    cc = PV["previsao_casa"]["central"]
    mc = PV["previsao_casa"]["monte_carlo"]
    out = [
        p(
            f"Na última onda de {pub['n']} institutos, o erro médio na diferença entre Lula e Flávio foi "
            f"<strong>{sinal(pub['media'], 2)} pontos</strong> a favor de Lula (mediana {sinal(pub['mediana'], 2)}). "
            f"{pub['positivos']} de {pub['n']} superestimaram Lula. {pub['fora_da_margem_aas']} erraram além da margem "
            f"de 95% da própria amostra. Em 2022, a média de {ref['n_casas']} casas errou "
            f"{sinal(ref['erro_comum_diferenca_lula_menos_bolsonaro'], 2)} na mesma direção.",
            "verificado",
        ),
        p(
            f"A dispersão entre institutos ({num(pub['desvio_padrao'], 2)} pontos) é maior que a esperada só pela "
            f"amostragem ({num(pub['desvio_esperado_so_amostragem_aas_pp'], 2)} sob amostragem simples). Efeito de casa "
            "existe e é grande.",
            "verificado",
        ),
    ]
    if len(perto) == 2:
        a, b = perto
        out.append(
            p(
                f"<strong>Proximidade não é acerto.</strong> {escape(a['instituto'])} e {escape(b['instituto'])} terminaram a "
                f"{num(abs(a['publicado']['diferenca_lula_menos_flavio']['erro']), 2)} e "
                f"{num(abs(b['publicado']['diferenca_lula_menos_flavio']['erro']), 2)} ponto da diferença da urna. "
                "Uma eleição é uma observação. Antes da urna, essas casas eram das que mais se afastavam das demais a "
                f"favor de Flávio; chegaram perto porque o erro comum foi grande e contrário ao desvio delas. Com os erros "
                f"espalhados como foram, a chance de ao menos uma de {pub['n']} casas cair a meio ponto da urna só pela "
                f"dispersão seria de {num(100 * r['prob_alguma_casa_a_meio_ponto_por_acaso'], 0)}%.",
                "juizo",
            )
        )
    out.append(
        p(
            f"A reponderação por renda, estrela da casa, levou o erro do agregador de {sinal(ag_pub, 2)} para "
            f"{sinal(ag_rep, 2)} pontos. Nas últimas ondas reponderáveis, {ef['aproximou']} de {ef['n']} andaram para a "
            f"urna, {ef['afastou']} se afastaram e {ef['neutro']} {'ficou parada' if ef['neutro'] == 1 else 'ficaram paradas'}. Corrigiu a direção e parte do tamanho; "
            f"não corrigiu tudo. A média reponderada ainda erra {sinal(rep['media'], 2)}. É sensibilidade de uma margem, "
            "não resultado corrigido.",
            "verificado",
        )
    )
    out.append(
        p(
            f"A central da casa, publicada na madrugada de 04/10, deu Flávio {num(cc['validos']['flavio'], 2)} e Lula "
            f"{num(cc['validos']['lula'], 2)}. Lula ficou a {num(abs(cc['erro_pp']['lula']), 2)} ponto; Flávio teve "
            f"{num(abs(cc['erro_pp']['flavio']), 2)} pontos a mais que a central. O erro na diferença foi "
            f"{sinal(cc['erro_diferenca_lula_menos_flavio'], 2)}, menor que o da média das pesquisas. A casa dava "
            f"{num(100 * mc['p_flavio_a_frente_de_lula'], 0)}% de chance de Flávio terminar à frente: disse empate, não "
            f"previu o vencedor. A urna caiu no percentil {num(100 * mc['margem_flavio_menos_lula']['percentil_urna'], 0)} "
            f"da distribuição. O ponto fraco foi a consolidação: a terceira via da urna ficou abaixo do percentil 5 da casa.",
            "verificado",
        )
    )
    return "".join(out)


def pesquisas_estaduais(PV: dict) -> str:
    g = PV["governador"]["resumo"]
    s = PV["senado"]["resumo"]
    return p(
        f"Governadores: o líder previsto liderou a urna em {g['acertos_lider']} de {g['n_ufs']} UFs; "
        f"{g['decididos_1t_urna']} UFs decidiram no 1º turno contra {num(g['decididos_1t_esperado'], 1)} esperadas; "
        f"Brier de {num(g['brier_decide_1t'], 3)} contra {num(g['brier_decide_1t_moeda'], 3)} de uma moeda. Senado: as "
        f"duas candidaturas mais prováveis de cada UF levaram {s['acertos_top2']} de {s['vagas']} vagas, contra "
        f"{num(s['acertos_top2_esperados'], 1)} esperadas; Brier de {num(s['brier'], 3)} em {s['n_candidaturas']} "
        "candidaturas.",
        "verificado",
    )


# ------------------------------------------------------------------ 11 Voto útil


def voto_util(V: dict) -> str:
    tv = V["terceira_via"]
    tc = V["terceiros_por_candidato"]["publicado"]
    q = tc["queda_pp"]
    rn = V["reserva_nacional"]
    agg = V["decomposicao"]["agregados"]["ultimas_ondas_publicado"]
    princ = agg["nexus_renormalizada"]
    fr = [
        agg[k]["fracao_explicada_diferenca"]
        for k in agg
        if "fracao_explicada_diferenca" in agg[k] and k != "proporcional"
    ]
    nomes = {
        "renan_santos": "Renan Santos",
        "caiado": "Caiado",
        "cury": "Cury",
        "zema": "Zema",
        "demais": "demais",
    }
    quedas = sorted(q.items(), key=lambda kv: -kv[1])
    return "".join(
        [
            p(
                f"As últimas ondas de {tv['n_publicado_todas']} institutos davam à terceira via {pct(tv['media_publicado_todas'])} "
                f"dos válidos. A urna deu <strong>{pct(tv['urna_validos'])}</strong>. Nenhuma onda final ficou abaixo da urna.",
                "verificado",
            ),
            p(
                "Quem perdeu, contra a média das últimas ondas: "
                + lista([f"{nomes.get(k, k)} {sinal(-v, 2)}" for k, v in quedas])
                + f". Quem recebeu: Flávio {sinal(princ['ganho_flavio_pp'], 2)} e Lula {sinal(princ['ganho_lula_pp'], 2)} "
                "pontos sobre o que as pesquisas finais deram a cada um. O voto útil foi de um lado só.",
                "verificado",
            ),
            p(
                f"Na mesma pesquisa, Flávio tinha em média {num(rn['reserva_media_flavio_pp'], 2)} pontos a mais no 2º "
                f"turno do que no 1º; Lula, {num(rn['reserva_media_lula_pp'], 2)}. A urna revelou no 1º turno a mediana de "
                f"{num(100 * rn['lambda_flavio']['mediana'], 0)}% da reserva de Flávio e "
                f"{num(100 * rn['theta_lula']['mediana'], 0)}% da de Lula.",
                "inferencia",
            ),
            p(
                f"Pela matriz da Nexus, a consolidação da terceira via explica {sinal(princ['explicado_diferenca_pp'], 2)} "
                f"dos {sinal(princ['erro_diferenca_lula_menos_flavio_pp'], 2)} pontos de erro na diferença "
                f"({num(100 * min(fr), 0)}% a {num(100 * max(fr), 0)}% conforme a variante). O resto é deslocamento "
                "entre os finalistas: efeito de casa, movimento de última hora, comparecimento diferencial. Os dados não "
                "separam os três. A conta depende de uma matriz medida duas semanas antes da eleição.",
                "hipotese",
            ),
        ]
    )


# ------------------------------------------------------------------ 12 Anomalias


def anomalias(A: dict) -> str:
    r = A["resumo"]
    topo = A["topo"]
    local = [
        t
        for t in topo
        if any("efeito político local" in e for e in t.get("explicacao_provavel", []))
    ]
    comuns = len(topo) - len(local)
    td = r["tardias"]
    rob = A.get("robustez", {})
    s1 = rob.get("semente_1", {})
    return "".join(
        [
            p(
                f"A casa rodou uma triagem estatística sobre as {inteiro(r['n_zonas'])} zonas eleitorais do país no voto "
                "para presidente. Cada zona é comparada com a própria UF e com o próprio resultado de 2022, por quatro "
                "leituras (z robusto, Mahalanobis, Isolation Forest e Local Outlier Factor) combinadas num escore de 0 a 100."
            ),
            p(
                f"<strong>Nenhuma das {len(topo)} zonas mais atípicas aponta fraude.</strong> {comuns} têm explicação comum "
                "provável (zona pequena, voto regional em terceira via, padrão compartilhado com as vizinhas, área remota); "
                f"{len(local)} ficam como hipótese de política local, a conferir seção por seção. "
                f"{r['pequenas_ate_30_secoes']['topo']} das {len(topo)} têm até 30 seções.",
                "inferencia",
            ),
            p(
                f"As {td['n']} zonas que fecharam bem depois da própria UF votaram como as demais em relação à região: a "
                f"variação da margem além do esperado foi de {sinal(td['residuo_medio_pp_tardias'], 2)} ponto nelas e de "
                f"{sinal(td['residuo_medio_pp_demais'], 2)} nas outras. O movimento extra delas é efeito do estado, não da "
                "demora. Correlação entre atraso e resíduo: "
                f"{num(td['correlacao_atraso_residuo'], 3)}.",
                "verificado",
            ),
            p(
                f"A lista é estável: com outra semente do Isolation Forest, {s1.get('comuns_topo', 's/d')} das "
                f"{s1.get('n_topo', len(topo))} zonas se repetem. Atipicidade não é irregularidade. A triagem por zona "
                "não prova nem descarta problema em seção específica; isso exige o boletim de urna, a ata da mesa e o "
                "log da urna, que o TSE publica.",
                "juizo",
            ),
        ]
    )


# ------------------------------------------------------------------ 13 2º turno


def segundo_turno(E: dict) -> str:
    ar = E["aritmetica"]
    pt = ar["primeiro_turno"]
    proj = ar["projecoes"]
    eq = ar["equilibrio"]
    mn = min(proj, key=lambda x: x["margem_votos"])
    mx = max(proj, key=lambda x: x["margem_votos"])
    est = E["geografia"]["estoque"]
    ri = E["riscos"]["estoque_lula_maior"]
    an = ar["analogo_2022"]["nacional"]
    ne = eq["nao_escolha_toda_para_lula"]["nexus"]
    return "".join(
        [
            p(
                f"Flávio sai do 1º turno com {milhoes(pt['diferenca_votos'])} de votos de vantagem. O 2º turno começa nos "
                f"{milhoes(pt['terceiros_total'])} de votos dados a outras candidaturas ({pct(pt['terceiros_pct'])}).",
                "verificado",
            ),
            p(
                f"Aplicadas as matrizes de transferência publicadas (Nexus e Datafolha) sob três hipóteses para a não "
                f"escolha, Flávio vai de {pct(mn['flavio_pct'])} a {pct(mx['flavio_pct'])} dos válidos; a margem fica entre "
                f"{milhoes(mn['margem_votos'])} e {milhoes(mx['margem_votos'])} de votos. Nenhuma das seis combinações "
                "desfaz a vantagem.",
                "inferencia",
            ),
            p(
                f"Para virar só com a terceira via, Lula precisaria de {pct(eq['lula_precisa_se_todos_votarem_pct'])} de todos "
                f"esses votos. A Nexus mede {pct(eq['lula_medido_entre_quem_escolhe_pct'])} entre os que escolhem. Mesmo "
                f"com toda a não escolha da terceira via indo para Lula, Flávio ficaria {milhoes(ne['margem_flavio_se_toda_for_lula'])} "
                "à frente.",
                "inferencia",
            ),
            p(
                f"<strong>O achado contra a tese:</strong> o risco não está na transferência, está na base e no comparecimento. "
                f"Se {pct(eq['base_flavio_trocando_para_lula_pct'])} da base de Flávio trocar de lado, ou "
                f"{pct(eq['base_flavio_abstendo_pct'])} deixar de votar, a margem central some. E o estoque de 2022 que "
                f"Lula ainda não reconquistou ({milhoes(ri['estoque_lula'])}) é {num(ri['razao'], 2)} vezes o de Flávio "
                f"({milhoes(ri['estoque_flavio'])}). Quem tem mais eleitor de 2022 para buscar é Lula.",
                "inferencia",
            ),
            p(
                f"Analogia, uma eleição só: se cada voto de terceira via rendesse o que rendeu entre os turnos de 2022, "
                f"Flávio teria {pct(an['flavio_pct'])}. Os terceiros de 2022 eram outros; a analogia mede ordem de grandeza, "
                f"não destino. O estoque de Flávio está {num(est['top5_ufs_parcela_pct'], 0)}% em cinco UFs.",
                "hipotese",
            ),
        ]
    )


# ------------------------------------------------------------------ 14 Auditoria


def auditoria(P: dict, L: dict) -> str:
    mc = P["meta_contagens"]
    conf = P["conferencia"]
    sm = conf["soma_municipios_menos_nacional"]
    su = conf["soma_ufs_menos_nacional"]
    inc = conf["municipios_incompletos"]
    lat = [x for x in L["latencia"]["por_hora"] if x["grupo"] == "presidente_br"]
    p50 = sorted(x["p50_s"] for x in lat)
    mediana = p50[len(p50) // 2] if p50 else None
    return "".join(
        [
            p(
                f"O coletor da casa leu os arquivos públicos do TSE durante toda a apuração e guardou cada versão com a hora "
                f"de geração do TSE, a hora de leitura e o SHA-256: {inteiro(mc['snapshots'])} versões de "
                f"{inteiro(mc['arquivos'])} arquivos, em {inteiro(mc['fetches'])} leituras.",
                "verificado",
            ),
            p(
                f"A soma das UFs bate com o arquivo nacional: diferença de {inteiro(su['secoes'])} seções e "
                f"{inteiro(su['validos'])} válidos. A soma dos municípios fica {inteiro(abs(sm['secoes']))} seções e "
                f"{inteiro(abs(sm['validos']))} válidos abaixo, porque {len(inc)} arquivos municipais de presidente "
                "congelaram incompletos e ainda respondiam “não modificado” de madrugada.",
                "verificado",
            ),
            p(
                f"Latência entre a geração do arquivo nacional e a nossa leitura: na hora mediana da noite, {num(mediana, 0)} "
                "segundos. Inclui o intervalo de sondagem do coletor; é teto da demora de publicação, não medida dela."
            ),
            p(
                "Limites: a casa não tem boletim de urna por seção; os proporcionais por município só guardam o primeiro e o "
                "último retrato; a classificação de campo é editorial (tucano é centro-esquerda). Tudo se reproduz a partir "
                "do banco e dos scripts listados no capítulo seguinte."
            ),
        ]
    )


def nome_uf(uf: str) -> str:
    return NOME_UF.get(uf, uf)


def campo(c: str) -> str:
    return ROTULO_CAMPO.get(c, c)
