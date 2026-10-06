"""Texto da segunda parte do capítulo 12: anomalias no nível da seção eleitoral.

Lê `secoes.json` (contrato em `analysis/apuracao_2026/CONTRATO_SECOES.md`). Regra
da casa: figura antes do parágrafo, frase curta, nenhum número digitado (todo
número sai do JSON), uma casa decimal, nunca "fraude". O que é inferência,
hipótese ou juízo editorial vem com o selo correspondente.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Callable
from html import escape

from .pagina_comum import NOME_UF, inteiro, milhoes, num, p, rotulo, sinal
from .pagina_fig_base import nome_bonito
from .pagina_fig_secoes import grupos_extenso, local_ref
from .pagina_texto import lista


def pct(x: float | None, casas: int = 1) -> str:
    return "s/d" if x is None else f"{num(x, casas)}%"


def pts(x: float | None, casas: int = 1) -> str:
    """Diferença em pontos com sinal: '+1,2 ponto' ou '−3,4 pontos'."""
    if x is None:
        return "s/d"
    return f"{sinal(x, casas)} {'ponto' if abs(round(x, casas)) < 2 else 'pontos'}"


NOME = {"lula": "Lula", "flavio": "Flávio"}


def _resumo(S: dict) -> dict[tuple[str, int], dict]:
    return {(x["candidato"], x["limiar"]): x for x in S["extremos"]["resumo"]}


# ------------------------------------------------------------------ da zona para a seção


def intro(S: dict) -> str:
    c = S["cobertura"]
    exc = [e for e in c.get("excluidas", []) if e.get("secoes")]
    excl = lista([f"{inteiro(e['secoes'])} por {escape(e['motivo'])}" for e in exc])
    cob = (
        f"A coleta ainda é parcial: {len(c.get('ufs_completas') or [])} UFs completas "
        f"({lista(sorted(c.get('ufs_completas') or []))}) e {len(c.get('ufs_incompletas') or [])} em andamento. "
        if c.get("parcial")
        else "A coleta cobre todas as UFs. "
    )
    h = p(
        "A zona soma centenas de urnas e dilui a que destoa. O boletim de cada urna mostra a seção sozinha: o local, "
        "o tamanho, o modelo da urna e a hora em que chegou ao TSE.",
    )
    h += p(
        cob
        + f"O cadastro tem {inteiro(c['secoes_cs'])} seções, {inteiro(c['secoes_agregadas_cs'])} delas agregadas a outra "
        f"(o voto está no boletim da principal). Temos boletim de {inteiro(c['secoes_com_bu'])} e usamos "
        f"{inteiro(c['secoes_validas'])}"
        + (f"; ficaram fora {excl}" if excl else "")
        + ". Cada zona usada teve a soma das seções conferida contra o arquivo de zona do TSE.",
        "verificado",
    )
    h += f'<aside class="juizo"><b>Frase responsável</b>{escape(S["aviso"])}</aside>'
    return h


# ------------------------------------------------------------------ seções acima de 90%


def extremos_contagem(S: dict) -> str:
    R = _resumo(S)
    E = S["extremos"]
    partes = []
    for c in ("lula", "flavio"):
        lim = [R.get((c, x)) for x in E["limiares"]]
        if not lim[0]:
            continue
        t90 = lim[0]
        resto = ", ".join(
            f"{x['limiar']}%{'' if x['limiar'] >= 100 else ' ou mais'} em {inteiro(x['secoes'])}"
            for x in lim[1:]
            if x
        )
        partes.append(
            f"{NOME[c]} teve 90% dos válidos ou mais em <strong>{inteiro(t90['secoes'])}</strong> seções "
            f"({pct(t90['pct_das_secoes'], 2)} das seções válidas, {milhoes(t90['aptos'])} eleitores aptos); {resto}"
        )
    return p(". ".join(partes) + ".", "verificado")


def extremos_onde(S: dict) -> str:
    E = S["extremos"]
    frases = []
    for c in ("lula", "flavio"):
        ufs = sorted(
            (x for x in E["por_uf"] if x["candidato"] == c and x["limiar"] == 90),
            key=lambda x: -x["secoes"],
        )[:3]
        mun = sorted(
            (x for x in E["por_municipio"] if x["candidato"] == c),
            key=lambda x: -x["secoes_90"],
        )[:3]
        if not ufs:
            continue
        frases.append(
            f"As de {NOME[c]} se concentram em "
            + lista(
                [
                    f"{NOME_UF.get(x['uf'], x['uf'])} ({inteiro(x['secoes'])})"
                    for x in ufs
                ]
            )
            + (
                "; os municípios com mais delas são "
                + lista(
                    [
                        f"{nome_bonito(m['municipio'])} ({m['uf']}, {inteiro(m['secoes_90'])} de {inteiro(m['secoes_total'])}, "
                        f"onde {NOME[c]} fez {pct(m['mun_pct'])} no município)"
                        for m in mun
                    ]
                )
                if mun
                else ""
            )
        )
    return p(". ".join(frases) + ".", "verificado") if frases else ""


def _faixa_alta(X: dict, corte: float = 80) -> dict | None:
    """Soma das faixas cuja zona já dá `corte`% ou mais ao candidato."""
    fx = [f for f in X["faixas_zona"] if (f.get("min_pct") or 0) >= corte]
    if not fx:
        return None
    return {"min_pct": corte, "secoes": sum(f["secoes"] or 0 for f in fx)}


def extremos_excesso(S: dict) -> str:
    X = S["extremos"]["excesso"]
    frases = []
    for c in ("lula", "flavio"):
        x = X[c]
        n = x["secoes"] or 0
        if not n:
            continue
        alta = _faixa_alta(x)
        parte = 100 * alta["secoes"] / n if alta else None
        frases.append(
            f"Das {inteiro(n)} seções de {NOME[c]} com 90% ou mais, {pct(parte)} estão em zonas onde ele já tem "
            f"{alta['min_pct'] if alta else 's/d'}% ou mais; a seção típica fica {pts(x.get('excesso_zona_pp_mediana'))} acima "
            f"do resto da zona. {inteiro(x['acima_zona_20pp'])} passam a zona por 20 pontos ou mais"
        )
    return p(
        ". ".join(frases)
        + ". São estas, e não as que repetem a vizinhança, que pedem a ata da mesa.",
        "verificado",
    )


def extremos_perfil(S: dict) -> str:
    E = S["extremos"]
    R = _resumo(S)
    tam = E["tamanho"]["linhas"]
    frases = []
    if tam:
        peq, gr = tam[0], tam[-1]
        frases.append(
            f"Seção pequena produz percentual extremo com poucos eleitores: entre as de {escape(str(peq['faixa']))} votantes, "
            f"{pct(peq['lula_90_pct'])} deram 90% ou mais a Lula e {pct(peq['flavio_90_pct'])} a Flávio; entre as de "
            f"{escape(str(gr['faixa']))}, {pct(gr['lula_90_pct'])} e {pct(gr['flavio_90_pct'])}"
        )
    l90 = R.get(("lula", 90))
    if l90 and l90["secoes"]:
        frases.append(
            f"{pct(100 * (l90['secoes'] - l90['secoes_100mais']) / l90['secoes'])} das seções de Lula com 90% ou mais têm menos de "
            f"{E['corte_tamanho']} votantes"
        )
    tipos = [x for x in E["tipo_local"]["linhas"] if x["todas"]]
    if tipos:
        topo = max(tipos, key=lambda x: x["lula_90_pct_do_tipo"])
        frases.append(
            f"Pelo nome do local, a maior taxa de Lula está em {escape(topo['tipo'])} ({pct(topo['lula_90_pct_do_tipo'])} de "
            f"{inteiro(topo['todas'])} seções)"
        )
    return p(". ".join(frases) + ".", "inferencia") if frases else ""


def extremos_cruzamento(S: dict) -> str:
    X = S["extremos"]["cruzamento_anomalias"]
    return p(
        f"Das {X['top_zonas']} zonas mais atípicas da triagem por zona, {X['zonas_top_com_secao_90']} têm ao menos uma seção de "
        f"90% ou mais, com {inteiro(X['secoes_90_no_top'])} seções no total. Nelas, {pct(X['taxa_lula_90_top_pct'])} das seções "
        f"dão 90% a Lula, contra {pct(X['taxa_lula_90_demais_pct'])} no resto do país; para Flávio, {pct(X['taxa_flavio_90_top_pct'])} "
        f"contra {pct(X['taxa_flavio_90_demais_pct'])}.",
        "verificado",
    )


def extremos_amostras(S: dict) -> str:
    E = S["extremos"]
    itens = []
    for c in ("lula", "flavio"):
        for s in E["amostras"][c][:3]:
            itens.append(
                f"<li>{NOME[c]} {pct(s[c + '_pct'])} em {escape(local_ref(s))}: {inteiro(s['comparecimento'])} votantes, "
                f"zona a {pct(s['zona_' + c + '_pct'])}. {escape(s.get('explicacao') or '')}</li>"
            )
    R = _resumo(S)
    cem = E["secoes_100pct"]
    frase_cem = []
    for c in ("lula", "flavio"):
        n = len(cem.get(c) or [])
        tot = (R.get((c, 100)) or {}).get("secoes")
        n20 = cem.get(f"{c}_total", n)
        frase_cem.append(
            f"{NOME[c]} teve 100% dos válidos em {inteiro(tot)} seções, {inteiro(n20)} delas com 20 válidos ou mais"
        )
    return (
        "<p>Três amostras de cada lado, as que mais passam a própria zona entre as de "
        f"{E['corte_tamanho']} votantes ou mais:</p><ul>"
        + "".join(itens)
        + "</ul>"
        + p("; ".join(frase_cem) + ".", "verificado")
    )


def _verbo(n: int, um: str, varios: str) -> str:
    return um if n == 1 else varios


def extremos_2022(S: dict) -> str:
    """A mesma seção em 2022, quando o coletor casou número e local nos dois cadastros."""
    C = S["extremos"].get("comparacao_2022") or {}
    if not C.get("disponivel"):
        motivo = C.get("motivo")
        return (
            p(f"Comparação com 2022 na mesma seção: {escape(motivo)}.", "verificado")
            if motivo
            else ""
        )
    frases = [
        f"A mesma seção existe em 2022 para {inteiro(C['secoes_casadas'])} das {inteiro(C['secoes_2026'])} seções desta base "
        f"(critério: {escape(C.get('criterio_mesma_secao', ''))})"
    ]
    for c, rival in (("lula", "Lula"), ("flavio", "Bolsonaro")):
        x = C.get(c) or {}
        if not x.get("secoes_90_2026_casadas"):
            continue
        novas = x["novas_abaixo_70_em_2022"]
        frases.append(
            f"das {inteiro(x['secoes_90_2026_casadas'])} com {NOME[c]} em 90% ou mais, {inteiro(x['tambem_90_em_2022_1t'])} já "
            f"{_verbo(x['tambem_90_em_2022_1t'], 'dava', 'davam')} 90% ou mais a {rival} no 1º turno de 2022 e "
            f"{inteiro(x['acima_80_em_2022_1t'])} {_verbo(x['acima_80_em_2022_1t'], 'dava', 'davam')} 80% ou mais (mediana de "
            f"{pct(x['pct_2022_1t_mediana'])}); "
            + (
                "nenhuma estava abaixo de 70%"
                if not novas
                else f"{inteiro(novas)} {_verbo(novas, 'estava', 'estavam')} abaixo de 70%"
            )
        )
    return p("; ".join(frases) + ".", "verificado")


def extremos_contrario(S: dict) -> str:
    C22 = S["extremos"].get("comparacao_2022") or {}
    x22 = C22.get("lula") or {}
    if C22.get("disponivel") and x22.get("secoes_90_2026_casadas"):
        parte = 100 * x22["acima_80_em_2022_1t"] / x22["secoes_90_2026_casadas"]
        return p(
            "<strong>O achado que contraria a leitura apressada:</strong> a zona engana, a própria seção não. Contra o resto da "
            f"zona, a seção de 90% parece destoar ({pts(S['extremos']['excesso']['lula'].get('excesso_zona_pp_mediana'))} na "
            f"mediana); contra ela mesma em 2022, {pct(parte)} das de Lula já davam 80% ou mais a ele. É o lugar de sempre, "
            "não um voto novo.",
            "inferencia",
        )
    X = S["extremos"]["excesso"]["lula"]
    n = X["secoes"] or 0
    alta = _faixa_alta(X)
    if not n or not alta:
        return ""
    parte = 100 * alta["secoes"] / n
    R = _resumo(S).get(("lula", 90)) or {}
    peq = (
        100 * (R["secoes"] - R["secoes_100mais"]) / R["secoes"]
        if R.get("secoes")
        else None
    )
    if parte >= 50:
        txt = (
            f"<strong>O achado que contraria a leitura apressada:</strong> a seção de 90% é, na maioria, a vizinhança de sempre. "
            f"{pct(parte)} das de Lula estão em zonas onde ele já passa de {alta['min_pct']}%, e {pct(peq)} têm menos de "
            f"{S['extremos']['corte_tamanho']} votantes. Percentual extremo em seção pequena de zona extrema é o resultado esperado."
        )
    else:
        txt = (
            f"<strong>O achado que pede explicação:</strong> só {pct(parte)} das seções de Lula com 90% ou mais estão em zonas onde ele "
            f"já passa de {alta['min_pct']}%. O restante destoa da vizinhança e precisa de ata, boletim e log, seção por seção."
        )
    return p(txt, "inferencia")


# ------------------------------------------------------------------ clusters


def analogia(k: int) -> str:
    n = grupos_extenso(k)
    return (
        f'<aside class="analogy"><b>Em linguagem de casa</b>Pense em {n} sacos de feijão despejados no mesmo chão. '
        f"A mistura gaussiana procura os {n} montes que melhor explicam como os grãos se espalharam e diz, para cada grão, "
        "de que saco ele mais provavelmente caiu. Grão longe de todos os montes é a seção pouco provável: não é grão estragado, "
        "é grão que pede um olhar.</aside>"
    )


def clusters_a(S: dict) -> str:
    C = S["clusters"]
    comps = C["componentes"]
    desc = lista(
        [
            f"grupo {c['id'] + 1} ({escape(c['rotulo'])}; {inteiro(c['secoes'])} seções)"
            for c in comps
        ]
    )
    interp = (C.get("interpretacao") or [""])[0]
    h = p(
        f"Cada seção entrou como {len(C['features'])} proporções do eleitorado apto (os {len(C['features']) - 3} candidatos, "
        f"brancos, nulos e abstenção), em log-razão centrada. A mistura de {C['k']} gaussianas separou: {desc}.",
        "verificado",
    )
    h += p(f"<strong>Grupo é geografia?</strong> {escape(interp)}", "inferencia")
    proj = C.get("leitura_projecao")
    if proj:
        h += p(escape(proj), "inferencia")
    if C.get("estabilidade"):
        h += p(escape(C["estabilidade"]), "verificado")
    h += escolha_k(C)
    return h


def escolha_k(C: dict) -> str:
    """Juízo editorial: k escolhido pelo autor, com o BIC ao lado."""
    bic = sorted(C.get("bic") or [], key=lambda b: b["k"])
    if not bic:
        return ""
    ek = C.get("escolha_k") or {}
    melhor = min(bic, key=lambda b: b["bic"])
    k = C["k"]
    motivo = ek.get("motivo") or "escolha do autor"
    concorda = (
        f"o BIC também prefere k = {k}"
        if melhor["k"] == k
        else f"entre os {grupos_extenso(len(bic))}, o BIC prefere k = {melhor['k']}"
    )
    return p(
        f"O número de grupos, k = {k}, é {escape(motivo)}. Pelo critério BIC (menor é melhor), "
        + lista([f"k = {b['k']} dá {menos(b['bic'], 0)}" for b in bic])
        + f"; {concorda}. Com tantos zeros, o BIC premia componente que se encaixa num padrão exato de zeros "
        "e serve de contraste, não de árbitro.",
        "juizo",
    )


def menos(x: float | None, casas: int = 1) -> str:
    """Número com o menos tipográfico, sem sinal de mais."""
    if x is None:
        return "s/d"
    return ("−" if round(x, casas) < 0 else "") + num(abs(x), casas)


def explicacao_principal(a: dict) -> str:
    """A primeira parte da explicação declarada, sem números entre parênteses."""
    e = (a.get("explicacao") or "sem explicação declarada").split(";")[0]
    return re.sub(r"\s*\([^)]*\)", "", e).strip() or "sem explicação declarada"


def clusters_b(S: dict) -> str:
    C = S["clusters"]
    ma = C["mais_anomalo"]
    comp = next((c for c in C["componentes"] if c["id"] == ma["id"]), None)
    if comp is None:
        return ""
    outros = [c for c in C["componentes"] if c["id"] != ma["id"]]
    ll_out = sum(c["loglik_media"] for c in outros) / len(outros) if outros else None
    expl = Counter(explicacao_principal(a) for a in ma["amostras"])
    comuns = lista([f"{escape(e)} ({inteiro(n)})" for e, n in expl.most_common(3)])
    mp = Counter(explicacao_principal(a) for a in C.get("menos_provaveis") or [])
    h = p(
        f"O grupo mais atípico é o {ma['id'] + 1} ({escape(comp['rotulo'])}). Critério: {escape(ma['criterio'].rstrip('.'))}. A log-verossimilhança média "
        f"dele é {menos(comp['loglik_media'], 1)}, contra {menos(ll_out, 1)} nos outros {grupos_extenso(len(outros))}, e a distância de Mahalanobis mediana, "
        f"{num(comp['mahalanobis_mediana'], 1)}. Nas {len(ma['amostras'])} amostras da tabela, pela primeira parte da explicação declarada, as mais frequentes são {comuns}.",
        "inferencia",
    )
    if mp:
        e, n = mp.most_common(1)[0]
        h += p(
            f"Entre as {len(C['menos_provaveis'])} seções menos prováveis do país inteiro, pela primeira parte da explicação declarada, a mais comum é "
            f"{escape(e)}, em {inteiro(n)}. A explicação é regra declarada pelo nome do local, não verificação.",
            "inferencia",
        )
    return h


# ------------------------------------------------------------------ urna


POUCAS = 30


def _maior(pares: list[dict], chave: str) -> dict | None:
    ok = [x for x in pares if (x.get(chave) or {}).get("estimativa") is not None]
    return max(ok, key=lambda x: x.get("unidades") or 0) if ok else None


def _fora_do_zero(x: dict) -> bool:
    for c in ("flavio_pp", "lula_pp"):
        ic = (x.get(c) or {}).get("ic95") or [None, None]
        if ic[0] is not None and ic[1] is not None and (ic[0] > 0 or ic[1] < 0):
            return True
    return False


def _ha_efeito(pares: list[dict]) -> bool:
    return any(_fora_do_zero(x) for x in pares)


def urna_a(S: dict) -> str:
    U = S["urna"]
    tot = Counter()
    for x in U["por_uf"]:
        tot[x["modelo"]] += x["secoes"]
    soma = sum(tot.values()) or 1
    dist = lista([f"{m} {pct(100 * tot[m] / soma)}" for m in U["modelos"] if tot[m]])
    bruto = {b["modelo"]: b for b in U["bruto"]}
    velho, novo = U["modelos"][0], U["modelos"][-1]
    h = p(escape((U.get("interpretacao") or [""])[0]), "inferencia")
    h += p(f"Distribuição das seções por modelo: {dist}.", "verificado")
    if velho in bruto and novo in bruto:
        bv, bn = bruto[velho], bruto[novo]
        h += p(
            f"Sem controle, Flávio tem {pct(bn['flavio_pct'])} dos válidos nas {novo} e {pct(bv['flavio_pct'])} nas {velho}; Lula, "
            f"{pct(bn['lula_pct'])} e {pct(bv['lula_pct'])}. Essa diferença bruta engana: urna nova vai primeiro para capital e "
            "cidade grande, que já votam diferente do interior. Comparar dentro da mesma zona, e melhor ainda dentro do mesmo "
            "prédio, separa o modelo da geografia.",
            "inferencia",
        )
    return h


def urna_b(S: dict) -> str:
    U = S["urna"]
    h = ""
    for est, onde in (
        ("dentro_zona", "dentro da mesma zona"),
        ("dentro_local", "dentro do mesmo prédio"),
    ):
        pares = (U.get(est) or {}).get("pares", [])
        ok = [
            x for x in pares if (x.get("flavio_pp") or {}).get("estimativa") is not None
        ]
        if not ok:
            continue
        m = max(ok, key=lambda x: x.get("unidades") or 0)
        f = m["flavio_pp"]
        lu = m.get("lula_pp") or {}
        fora = [x for x in ok if _fora_do_zero(x)]
        h += p(
            f"{onde.capitalize()}, no par com mais unidades ({m['b']} contra {m['a']}, {inteiro(m['unidades'])} unidades), Flávio "
            f"varia {pts(f['estimativa'], 2)} (intervalo de 95% de {sinal(f['ic95'][0], 2)} a {sinal(f['ic95'][1], 2)}), contra "
            f"{pts(f['bruto'], 2)} sem controle; Lula, {pts(lu.get('estimativa'), 2)}. "
            + (
                "Pares com intervalo que exclui o zero para Flávio ou Lula: "
                + lista(
                    [
                        f"{x['b']} contra {x['a']} ({inteiro(x['unidades'])} unidades, Flávio {pts(x['flavio_pp']['estimativa'], 2)})"
                        for x in fora
                    ]
                )
                + "."
                + (
                    f" Com menos de {POUCAS} unidades, o intervalo de bootstrap é frágil: "
                    + lista(
                        [
                            f"{x['b']} contra {x['a']}"
                            for x in fora
                            if (x.get("unidades") or 0) < POUCAS
                        ]
                    )
                    + "."
                    if any((x.get("unidades") or 0) < POUCAS for x in fora)
                    else ""
                )
                if fora
                else "Nenhum par tem intervalo que exclua o zero."
            ),
            "verificado",
        )
    A22 = U.get("ano_2022") or {}
    p22 = (A22.get("dentro_zona") or {}).get("pares", [])
    m22 = _maior(p22, "bolsonaro_pp")
    if m22:
        b = m22["bolsonaro_pp"]
        h += p(
            f"O mesmo estimador sobre o 1º turno de 2022, no par com mais zonas ({m22['b']} contra {m22['a']}), dá a Bolsonaro "
            f"{pts(b['estimativa'], 2)} (intervalo de {sinal(b['ic95'][0], 2)} a "
            f"{sinal(b['ic95'][1], 2)}), contra {pts(b['bruto'], 2)} sem controle, em {inteiro(m22['unidades'])} zonas.",
            "verificado",
        )
    h += _reguas(U)
    efeito = _ha_efeito((U.get("dentro_zona") or {}).get("pares", []))
    h += (
        '<aside class="hyp"><b>Hipótese</b>'
        + (
            "Onde o intervalo dentro da zona não contém o zero, as explicações candidatas antes de qualquer outra são: a zona "
            "mistura bairros e o TRE manda o modelo novo para os locais maiores; seção nova (criada por cadastro recente) recebe "
            "urna nova e tem perfil de eleitor diferente; urna de contingência substituindo a original muda o modelo do boletim. "
            if efeito
            else "Nenhum par tem intervalo dentro da zona que exclua o zero para Flávio ou Lula. Se um efeito aparecer com a coleta "
            "completa, as explicações a testar antes de qualquer outra são a alocação dos modelos pelo TRE dentro da zona, a "
            "seção criada por cadastro recente e a troca por urna de contingência. "
        )
        + "O documento que resolve é o plano de alocação de urnas do TRE de cada estado, com a lista de seções por modelo.</aside>"
    )
    return h


def _reguas(U: dict) -> str:
    """As réguas nacionais lado a lado e a leitura que sai delas."""
    rg = U.get("reguas") or {}
    itens = rg.get("itens") or []
    if not itens:
        return ""
    partes = [
        f"{escape(i['regua'])}, {pts(i['estimativa'], 2)} (intervalo de {sinal(i['ic95'][0], 2)} a "
        f"{sinal(i['ic95'][1], 2)}; {inteiro(i['unidades'])} {escape(i['unidade'])})"
        for i in itens
    ]
    desc = (
        "; ".join(partes[:-1]) + "; e " + partes[-1] if len(partes) > 1 else partes[0]
    )
    h = p(
        (
            "A mesma pergunta, a urna mais nova contra a mais velha, medida de quatro jeitos que controlam o lugar de "
            f"formas diferentes: {desc}."
            if len(itens) == 4
            else f"As réguas para Flávio: {desc}."
        ),
        "verificado",
    )
    if rg.get("leitura"):
        h += p(escape(rg["leitura"]), "inferencia")
    return h


# ------------------------------------------------------------------ outras


def outras_a(S: dict) -> str:
    OD = S["outras"]
    cp, zv = OD["comparecimento"], OD["zero_votos"]
    f1 = (
        f"{inteiro(cp['acima_100'])} seções com comparecimento acima de 100% dos aptos, {inteiro(cp['igual_100'])} com 100% e "
        f"{inteiro(cp['abstencao_zero'])} sem nenhuma abstenção"
    )
    zl = (zv.get("lula") or {}).get("secoes") or 0
    zf = (zv.get("flavio") or {}).get("secoes") or 0
    f2 = f"Entre as seções com {zv['minimo_votantes']} votantes ou mais, Lula zerou em {inteiro(zl)} e Flávio em {inteiro(zf)}"
    zl_uf = (zv.get("flavio") or {}).get("por_uf") or []
    if zf and zl_uf:
        f2 += (
            " (Flávio: " + lista([f"{x['uf']} {x['secoes']}" for x in zl_uf[:4]]) + ")"
        )
    cont = [
        x
        for x in OD.get("tipo_urna") or []
        if x.get("tipo_urna") != 1 and x.get("dif_zona_lula_pp") is not None
    ]
    f3 = ""
    if cont:
        f3 = "Urnas de contingência e reserva: " + lista(
            [
                f"{escape(x.get('descricao') or str(x.get('tipo_urna')))} em {inteiro(x['secoes'])} seções, Lula {pts(x.get('dif_zona_lula_pp'))} "
                "contra o resto da zona"
                for x in cont
            ]
        )
    arq = [x for x in OD.get("tipo_arquivo") or [] if x.get("tipo_arquivo") != 1]
    if arq:
        f3 += (
            (". " if f3 else "")
            + "Arquivos fora do padrão: "
            + lista(
                [
                    f"{escape(x.get('descricao') or str(x.get('tipo_arquivo')))} em {inteiro(x['secoes'])} seções"
                    for x in arq
                ]
            )
        )
    return p(". ".join(x for x in (f1, f2, f3) if x) + ".", "verificado")


def outras_b(S: dict) -> str:
    OD = S["outras"]
    H = OD["horarios"]
    rc = OD["recebimento"]
    d0 = rc.get("depois_0000") or {}
    d1 = rc.get("depois_0100") or {}
    enc, ab = H.get("encerramento") or {}, H.get("abertura") or {}
    h = p(
        f"{escape(H.get('fuso', ''))} Em hora de Brasília, {inteiro(ab.get('antes_0730'))} seções abriram antes das 7h30 e "
        f"{inteiro(ab.get('depois_0900'))} depois das 9h; {inteiro(enc.get('depois_1800'))} encerraram depois das 18h e "
        f"{inteiro(enc.get('depois_1900'))} depois das 19h.",
        "verificado",
    )
    if d0.get("secoes"):
        muns = lista(
            [
                f"{nome_bonito(m['municipio'])} ({m['uf']}, {inteiro(m['secoes'])})"
                for m in (d0.get("municipios") or [])[:4]
            ]
        )
        h += p(
            f"Depois da meia-noite chegaram {inteiro(d0['secoes'])} seções, com Lula a {pct(d0.get('lula_pct'))} dos "
            f"{inteiro(d0.get('validos'))} válidos"
            + (f", de {muns}" if muns else "")
            + f"; depois da 01h, {inteiro(d1.get('secoes'))}. É o lote tardio que o capítulo 2 descreve, agora com o endereço "
            "de cada seção.",
            "inferencia",
        )
    else:
        h += p(
            "Nenhuma seção desta cobertura chegou depois da meia-noite.", "verificado"
        )
    ud = OD.get("ultimo_digito") or []
    bf = OD.get("benford2") or []
    frase = []
    if ud:
        frase.append(
            f"No teste do último dígito, {sum(1 for x in ud if x['p'] < 0.05)} de {len(ud)} combinações de UF e candidato ficam "
            "abaixo de p = 0,05"
        )
    if bf:
        frase.append(
            f"no do segundo dígito de Benford, {sum(1 for x in bf if x['p'] < 0.05)} de {len(bf)}"
        )
    if frase:
        h += p(
            "; ".join(frase)
            + f". Sem nenhum desvio real, o acaso sozinho poria cerca de {max(1, round(len(ud or bf) / 20))} de cada "
            f"{len(ud or bf)} abaixo desse corte. {escape(OD.get('aviso_benford', ''))}",
            "inferencia",
        )
    return h


# ------------------------------------------------------------------ achados


ROT_ACHADO = [
    ("verificado", rotulo("verificado")),
    ("inferido", rotulo("inferencia")),
    ("juizo", rotulo("juizo")),
    ("hipotese", rotulo("hipotese")),
    ("contrario", '<span class="selo selo-contrario">Achado contrário</span>'),
]


def achados(S: dict) -> str:
    A = S.get("achados") or {}
    itens = [
        f"<li>{selo} {escape(texto)}</li>"
        for chave, selo in ROT_ACHADO
        for texto in A.get(chave) or []
    ]
    h = '<ul class="achados">' + "".join(itens) + "</ul>" if itens else ""
    if S.get("limites"):
        h += (
            "<details><summary>Limites da análise por seção</summary><ul>"
            + "".join(f"<li>{escape(x)}</li>" for x in S["limites"])
            + "</ul></details>"
        )
    return h


# ------------------------------------------------------------------ montagem


def bloco(S: dict, fig: Callable[[str], str]) -> str:
    """A parte por seção do capítulo 12, na ordem figura antes do parágrafo."""
    h = "<h3>Da zona para a seção</h3>" + intro(S)
    h += "<h3>Seções acima de 90%</h3>" + fig("secoes_90")
    h += extremos_contagem(S) + extremos_onde(S)
    h += fig("secoes_excesso") + extremos_excesso(S)
    h += fig("secoes_tamanho_tipo") + extremos_perfil(S) + extremos_cruzamento(S)
    h += extremos_2022(S) + extremos_amostras(S) + extremos_contrario(S)
    k = S["clusters"]["k"]
    h += f"<h3>{grupos_extenso(k).capitalize()} grupos de seções</h3>" + analogia(k)
    h += fig("clusters_secoes")
    h += clusters_a(S) + fig("clusters_regiao") + clusters_b(S)
    h += "<h3>Modelo de urna</h3>" + fig("modelo_urna_uf") + urna_a(S)
    h += fig("modelo_urna_zona") + urna_b(S)
    h += "<h3>O que mais a seção mostra</h3>" + fig("secoes_outras")
    h += outras_a(S) + outras_b(S)
    h += "<h3>O que a seção prova e o que não prova</h3>" + achados(S)
    return h


CHAVES = [
    "aviso",
    "cobertura",
    "extremos",
    "clusters",
    "urna",
    "outras",
    "achados",
    "limites",
]
