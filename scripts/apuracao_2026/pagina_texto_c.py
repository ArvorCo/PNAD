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

from .pagina_comum import NOME_UF, inteiro, milhoes, nota, num, p, sinal, tabela
from .pagina_fig_base import nome_bonito
from .pagina_fig_secoes import grupos_extenso, local_ref
from .pagina_fig_urna_voto import modelos_ordenados, por_uf, referencia_nacional
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


def _frases(texto: str) -> list[str]:
    """Divide texto do JSON em frases, sem cortar decimais nem siglas."""
    return [
        x.strip()
        for x in re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇ])", texto or "")
        if x.strip()
    ]


def intro(S: dict) -> str:
    c = S["cobertura"]
    exc = [e for e in c.get("excluidas", []) if e.get("secoes")]
    excl = lista([f"{inteiro(e['secoes'])} por {escape(e['motivo'])}" for e in exc])
    cob = (
        f"A coleta ainda é parcial ({len(c.get('ufs_completas') or [])} UFs completas). "
        if c.get("parcial")
        else ""
    )
    h = p(
        "A zona dilui a urna que destoa; o boletim mostra a seção sozinha. "
        + cob
        + f"De {inteiro(c['secoes_cs'])} seções no cadastro ({inteiro(c['secoes_agregadas_cs'])} agregadas à principal), "
        f"temos boletim de {inteiro(c['secoes_com_bu'])} e usamos {inteiro(c['secoes_validas'])}"
        + (f"; ficaram fora {excl}" if excl else "")
        + ". Cada zona usada teve a soma das seções conferida contra o arquivo de zona do TSE.",
        "verificado",
    )
    return h + nota("juizo", escape(S["aviso"]), "Frase responsável.")


# ------------------------------------------------------------------ seções acima de 90%


def extremos_contagem(S: dict) -> str:
    R = _resumo(S)
    E = S["extremos"]
    cem = E["secoes_100pct"]
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
        n20 = cem.get(f"{c}_total", len(cem.get(c) or []))
        partes.append(
            f"{NOME[c]} teve 90% dos válidos ou mais em <strong>{inteiro(t90['secoes'])}</strong> seções "
            f"({pct(t90['pct_das_secoes'], 2)}, {milhoes(t90['aptos'])} de aptos; {resto}, {inteiro(n20)} destas com 20 "
            "válidos ou mais)"
        )
    onde = []
    for c in ("lula", "flavio"):
        ufs = sorted(
            (x for x in E["por_uf"] if x["candidato"] == c and x["limiar"] == 90),
            key=lambda x: -x["secoes"],
        )[:3]
        if ufs:
            onde.append(
                f"as de {NOME[c]}, em "
                + lista([f"{x['uf']} ({inteiro(x['secoes'])})" for x in ufs])
            )
    frase = ". ".join(partes) + "."
    if onde:
        frase += " Concentração: " + "; ".join(onde) + "."
    return p(
        frase.replace("de aptos", "aptos").replace("mil aptos", "mil aptos"),
        "verificado",
    )


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
            f"das {inteiro(n)} de {NOME[c]}, {pct(parte)} estão em zonas onde ele já tem "
            f"{alta['min_pct'] if alta else 's/d'}% ou mais, a típica fica {pts(x.get('excesso_zona_pp_mediana'))} acima "
            f"do resto da zona e {inteiro(x['acima_zona_20pp'])} passam a zona por 20 pontos ou mais"
        )
    texto = "; ".join(frases)
    return p(
        texto[0].upper()
        + texto[1:]
        + ". São estas, e não as que repetem a vizinhança, que pedem a ata da mesa.",
        "verificado",
    )


def extremos_perfil(S: dict) -> str:
    E = S["extremos"]
    R = _resumo(S)
    X = E["cruzamento_anomalias"]
    tam = E["tamanho"]["linhas"]
    frases = []
    if tam:
        peq, gr = tam[0], tam[-1]
        frases.append(
            f"Seção pequena produz percentual extremo: com {escape(str(peq['faixa']))} votantes, "
            f"{pct(peq['lula_90_pct'])} deram 90% ou mais a Lula e {pct(peq['flavio_90_pct'])} a Flávio; com "
            f"{escape(str(gr['faixa']))}, {pct(gr['lula_90_pct'])} e {pct(gr['flavio_90_pct'])}"
        )
    l90 = R.get(("lula", 90))
    if l90 and l90["secoes"]:
        frases.append(
            f"{pct(100 * (l90['secoes'] - l90['secoes_100mais']) / l90['secoes'])} das de Lula têm menos de "
            f"{E['corte_tamanho']} votantes"
        )
    tipos = [x for x in E["tipo_local"]["linhas"] if x["todas"]]
    if tipos:
        topo = max(tipos, key=lambda x: x["lula_90_pct_do_tipo"])
        frases.append(
            f"pelo nome do local, a maior taxa de Lula está em {escape(topo['tipo'])} ({pct(topo['lula_90_pct_do_tipo'])} "
            f"de {inteiro(topo['todas'])} seções)"
        )
    frases.append(
        f"das {X['top_zonas']} zonas mais atípicas da triagem, só {X['zonas_top_com_secao_90']} têm seção de 90% ou "
        f"mais ({inteiro(X['secoes_90_no_top'])} seções)"
    )
    texto = "; ".join(frases) + "."
    return p(texto[0].upper() + texto[1:], "inferencia")


def _verbo(n: int, um: str, varios: str) -> str:
    return um if n == 1 else varios


def extremos_2022(S: dict) -> str:
    """A zona engana, a própria seção não: a mesma seção em 2022 (achado contrário)."""
    C = S["extremos"].get("comparacao_2022") or {}
    if not C.get("disponivel"):
        motivo = C.get("motivo")
        return (
            p(f"Comparação com 2022 na mesma seção: {escape(motivo)}.", "verificado")
            if motivo
            else ""
        )
    frases = []
    for c, rival in (("lula", "a ele"), ("flavio", "a Bolsonaro")):
        x = C.get(c) or {}
        if not x.get("secoes_90_2026_casadas"):
            continue
        novas = x["novas_abaixo_70_em_2022"]
        frases.append(
            f"das {inteiro(x['secoes_90_2026_casadas'])} de {NOME[c]}, {inteiro(x['tambem_90_em_2022_1t'])} já "
            f"{_verbo(x['tambem_90_em_2022_1t'], 'dava', 'davam')} 90% ou mais {rival} no 1º turno e "
            f"{inteiro(x['acima_80_em_2022_1t'])}, 80% (mediana {pct(x['pct_2022_1t_mediana'])}), "
            + (
                "nenhuma abaixo de 70%"
                if not novas
                else f"só {inteiro(novas)} abaixo de 70%"
            )
        )
    exc = S["extremos"]["excesso"]["lula"].get("excesso_zona_pp_mediana")
    return p(
        f"A zona engana; a própria seção não. Contra o resto da zona a seção de 90% parece destoar ({pts(exc)} na mediana), "
        f"mas {inteiro(C['secoes_casadas'])} seções casam com 2022 pelo número e pelo local e, entre as de 90% ou mais, "
        + "; ".join(frases)
        + ". É o lugar de sempre, não um voto novo.",
        "contrario",
    )


def extremos_amostras(S: dict) -> str:
    E = S["extremos"]
    linhas = []
    for c in ("lula", "flavio"):
        for s in E["amostras"][c][:3]:
            linhas.append(
                [
                    f"{NOME[c]} {pct(s[c + '_pct'])}",
                    escape(local_ref(s)),
                    inteiro(s["comparecimento"]),
                    pct(s["zona_" + c + "_pct"]),
                    escape(explicacao_principal(s)),
                ]
            )
    return tabela(
        ["Seção", "Onde", "Votantes", "Candidato no resto da zona", "Regra acionada"],
        linhas,
        f"As três seções de cada lado que mais passam a própria zona, entre as de {E['corte_tamanho']} votantes ou "
        "mais. A regra é inferência pelo cadastro do local, não verificação.",
    )


# ------------------------------------------------------------------ clusters


def _nome_parte(S: dict, chave: str) -> str:
    nomes = {c["chave"]: c["nome"] for c in S.get("candidatos") or []}
    return escape(nomes.get(chave, chave))


def _var(C: dict, chave: str) -> dict:
    return (C.get("variantes") or {}).get(chave) or {}


def clusters_falha(S: dict) -> str:
    """As três tentativas, em três passos curtos (antes da figura nova)."""
    C = S["clusters"]
    q, c5 = _var(C, "quinze_partes"), _var(C, "cinco_partes_clr")
    if not q or not c5:
        return ""
    med = c5.get("mediana_votos_por_secao") or {}
    art = [g for g in c5.get("grupos") or [] if g.get("artefato")]
    eixo = c5.get("eixo_1") or {}
    feature = str(eixo.get("feature") or "")
    eixo_nome = {"brancos": "o voto branco", "nulos": "o voto nulo"}.get(
        feature, feature
    )
    return p(
        "Pedimos grupos à mistura gaussiana três vezes. "
        f"A primeira usou as {len(q['features'])} partes de cada seção em log-razão: "
        f"{num(q['zeros_substituidos_pct'], 1)}% das células eram zero, e os grupos saíram de quem tem ou não tem "
        f"voto nas candidaturas nanicas (V de Cramér com a região de {num(q['cramer_v_regiao'], 2)}). "
        "A segunda usou só Lula, Flávio, brancos, nulos e abstenção, ainda em log-razão: com mediana de "
        f"{num(med.get('brancos') or 0, 0)} brancos e {num(med.get('nulos') or 0, 0)} nulos por seção, dobrar os "
        f"brancos pesava tanto quanto dobrar o voto em Lula; o primeiro eixo virou {escape(eixo_nome)} e "
        f"{grupos_extenso(len(art))} dos cinco grupos foram zero ou empate de brancos e nulos (V de "
        f"{num(c5['cramer_v_regiao'], 2)}). A terceira, a publicada, usa as mesmas cinco variáveis como "
        "proporções do eleitorado, sem log, como no pedido original: aí quatro brancos contra oito são um ponto "
        "do eleitorado e não mandam em nada.",
        "inferencia",
    )


def clusters_a(S: dict) -> str:
    """O que entrou no modelo publicado, o que ele separou e se o EM convergiu."""
    C = S["clusters"]
    comps = C["componentes"]
    pad = C.get("padronizacao") or {}
    nomes = {
        "lula": "Lula",
        "flavio": "Flávio",
        "brancos": "brancos",
        "nulos": "nulos",
        "abstencao": "abstenção",
    }
    dps = lista(
        [
            f"{nomes.get(k, k)} {num(v['dp_pct'], 1)}"
            for k, v in pad.items()
            if v.get("dp_pct") is not None
        ]
    )
    h = p(
        "Cada seção entra como cinco proporções do eleitorado apto: votos de Lula, de Flávio, brancos, nulos e "
        "abstenções, cada um dividido pelos aptos. O voto nas outras dez candidaturas fica implícito, como o que "
        "falta para 100%, e aparece no painel ao lado de cada grupo. Sem log, o zero fica como zero. Antes da "
        "mistura, cada proporção é padronizada: menos a média entre seções, dividida pelo desvio-padrão entre "
        f"seções ({dps}, em pontos do eleitorado). A mistura de {C['k']} gaussianas, com covariância completa, "
        "separou "
        + lista([f"{inteiro(c['secoes'])} (grupo {c['id'] + 1})" for c in comps])
        + " seções.",
        "verificado",
    )
    dg = (C.get("ajuste") or {}).get("diagnostico_convergencia")
    if dg:
        h += p(escape(dg["frase"]), "verificado")
    return h


def clusters_leitura(S: dict) -> str:
    """Geografia, o que os grupos acrescentam ao mapa (achado contrário quando
    não acrescentam) e o que cada eixo da projeção opõe."""
    C = S["clusters"]
    L = C.get("leitura") or {}
    h = p(escape(L["geografia"]), "inferencia") if L.get("geografia") else ""
    for chave in ("artefatos", "mapa"):
        x = L.get(chave)
        if not x:
            continue
        contrario = (chave == "artefatos" and "Nenhum grupo" not in x) or (
            chave == "mapa" and "não acrescenta" in x
        )
        h += nota("contrario", escape(x)) if contrario else p(escape(x), "inferencia")
    resto = [L.get("perfis"), L.get("geometria"), C.get("leitura_projecao")]
    if any(resto):
        h += p(" ".join(escape(x) for x in resto if x), "inferencia")
    return h


def escolha_k(C: dict) -> str:
    """Juízo editorial: k e as cinco partes são escolha do autor, com o BIC ao lado."""
    bic = sorted(C.get("bic") or [], key=lambda b: b["k"])
    if not bic:
        return ""
    ek = C.get("escolha_k") or {}
    melhor = min(bic, key=lambda b: b["bic"])
    atual = next((b for b in bic if b["k"] == C["k"]), None)
    k = C["k"]
    concorda = (
        f"o BIC também prefere k = {k}"
        if melhor["k"] == k
        else f"o BIC preferiria k = {melhor['k']} ({menos(melhor['bic'], 0)} contra {menos(atual['bic'], 0) if atual else 's/d'})"
    )
    return p(
        f"O número de grupos, k = {k}, e a escolha das cinco variáveis são do autor ({escape(ek.get('data') or '')}); "
        f"{concorda}. Deixar a terceira via implícita é decisão de leitura, não de método: a pergunta é como as "
        "seções se dividem entre os dois finalistas, o voto que não escolhe ninguém e quem não foi votar. Trocar a "
        "log-razão por proporções cruas também é escolha nossa, depois de duas tentativas que mediram a contagem e "
        "não o eleitorado.",
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
    frase_mp = ""
    if mp:
        e, n = mp.most_common(1)[0]
        frase_mp = f" No país, {escape(e)} explica {inteiro(n)} das {len(C['menos_provaveis'])} menos prováveis."
    return p(
        f"O grupo mais atípico é o {ma['id'] + 1} ({escape(comp['rotulo'])}): log-verossimilhança média "
        f"{menos(comp['loglik_media'], 1)}, contra "
        f"{menos(ll_out, 1)} nos outros, e Mahalanobis mediana {num(comp['mahalanobis_mediana'], 1)}. Nas "
        f"{len(ma['amostras'])} amostras menos prováveis dele, as explicações mais frequentes pelo cadastro são {comuns}."
        + frase_mp,
        "inferencia",
    )


# ------------------------------------------------------------------ urna


POUCAS = 30


def _fora_do_zero(x: dict) -> bool:
    for c in ("flavio_pp", "lula_pp"):
        lo, hi = (x.get(c) or {}).get("ic95") or [None, None]
        if lo is not None and hi is not None and (lo > 0 or hi < 0):
            return True
    return False


def urna_a(S: dict) -> str:
    U = S["urna"]
    tot = Counter()
    for x in U["por_uf"]:
        tot[x["modelo"]] += x["secoes"]
    soma = sum(tot.values()) or 1
    dist = lista([f"{m} {pct(100 * tot[m] / soma)}" for m in U["modelos"] if tot[m]])
    frase = f"Seções por modelo: {dist}."
    return p(frase, "verificado")


def urna_voto_nacional(S: dict) -> str:
    U = S["urna"]
    B = {b["modelo"]: b for b in U["bruto"]}
    mods = [m for m in modelos_ordenados(U) if m in B]
    if len(mods) < 2:
        return ""
    ref = referencia_nacional(U)
    velho, novo = mods[0], mods[-1]
    bv, bn = B[velho], B[novo]
    longe = max(mods, key=lambda m: abs(B[m]["flavio_pct"] - ref["flavio_pct"]))
    resto = [m for m in mods if m != longe]
    faixa = (
        min(B[m]["flavio_pct"] for m in resto),
        max(B[m]["flavio_pct"] for m in resto),
    )
    h = p(
        f"Sem controle, Flávio tem {pct(bv['flavio_pct'])} dos válidos nas {velho} e {pct(bn['flavio_pct'])} nas "
        f"{novo}; Lula, {pct(bv['lula_pct'])} e {pct(bn['lula_pct'])}. No país, {pct(ref['flavio_pct'])} e "
        f"{pct(ref['lula_pct'])}. O modelo que mais se afasta do país é a {longe}, com "
        f"{inteiro(B[longe]['secoes'])} seções e Flávio {pts(B[longe]['flavio_pct'] - ref['flavio_pct'])} contra o país; "
        f"nos outros modelos Flávio fica entre {pct(faixa[0])} e {pct(faixa[1])}. A abstenção vai de "
        f"{pct(bv['abstencao_pct'])} dos aptos nas {velho} a {pct(bn['abstencao_pct'])} nas {novo}.",
        "verificado",
    )
    frase = (
        "Diferença bruta não é efeito da máquina. Urna nova vai primeiro para capital e cidade grande, e a urna "
        "velha que sobra fica onde o eleitorado é outro"
    )
    if bv["abstencao_pct"] > bn["abstencao_pct"]:
        frase += (
            ": a abstenção mais alta das urnas antigas é sinal desse lugar, não de um equipamento que afaste "
            "eleitor"
        )
    return h + p(frase + ".", "inferencia")


def urna_voto_uf(S: dict) -> str:
    P = por_uf(S["urna"])
    difs = {u: o["dif"] for u, o in P.items() if o["dif"]}
    if not difs:
        return ""
    mais = sorted(difs, key=lambda u: -difs[u]["flavio"])
    pos = [u for u in mais if round(difs[u]["flavio"], 1) > 0]
    neg = [u for u in mais if round(difs[u]["flavio"], 1) < 0]
    grandes = [u for u in mais if abs(difs[u]["flavio"]) >= 10]

    def caso(u: str) -> str:
        x = difs[u]
        return (
            f"{NOME_UF.get(u, u)} ({x['novo']} contra {x['velho']}, Flávio "
            f"{pts(x['flavio'])}; Lula {pts(x['lula'])})"
        )

    frase = (
        f"Dentro da UF, a urna mais nova dá mais a Flávio que a mais velha em {len(pos)} das {len(difs)} UFs "
        f"e menos em {len(neg)}"
        + (
            f"; em {len(difs) - len(pos) - len(neg)}, empata na primeira casa. "
            if len(pos) + len(neg) < len(difs)
            else ". "
        )
    )
    if pos and neg:
        frase += (
            f"Os extremos vão para os dois lados: {caso(mais[0])} e {caso(mais[-1])}. "
        )
    frase += f"Em {len(grandes)} UFs a diferença passa de 10 pontos."
    h = p(frase, "verificado")
    if not (pos and neg):
        return h + p("Diferença bruta não é efeito da máquina.", "inferencia")
    rg = S["urna"].get("reguas") or {}
    mx, lim = rg.get("max_abs_pp"), rg.get("limiar_pp")
    controle = ""
    if mx is not None:
        controle = (
            " A UF é controle grosso demais; nas réguas abaixo, que comparam dentro da zona e do prédio, a "
            + (
                "diferença fica abaixo de um ponto."
                if lim is not None and mx < lim
                else f"diferença chega a {num(mx, 1)} pontos em módulo."
            )
        )
    return h + p(
        "A diferença entre modelos dentro da UF não é pequena, mas troca de sinal de um estado para o outro "
        "e quase se anula no país. Um equipamento que mudasse voto empurraria para o mesmo lado em toda parte. "
        "O que muda de sinal é o lugar: em cada UF o modelo novo foi para um pedaço diferente do território, e "
        f"ali o voto já era outro.{controle} Diferença bruta não é efeito da máquina.",
        "inferencia",
    )


def urna_reguas(S: dict) -> str:
    rg = S["urna"].get("reguas") or {}
    leitura = _frases(rg.get("leitura") or "")
    h = (
        p(" ".join(escape(x) for x in leitura[1:]), "inferencia")
        if len(leitura) > 1
        else ""
    )
    return h + nota(
        "hipotese", escape((S.get("achados") or {}).get("hipotese", [""])[0])
    )


def urna_pares(S: dict) -> str:
    U = S["urna"]
    frases = []
    for est, onde in (
        ("dentro_zona", "Dentro da zona"),
        ("dentro_local", "no mesmo prédio"),
    ):
        pares = [
            x
            for x in (U.get(est) or {}).get("pares", [])
            if (x.get("flavio_pp") or {}).get("estimativa") is not None
        ]
        fora = [x for x in pares if _fora_do_zero(x) and x["a"] != "mais velha"]
        if not fora:
            frases.append(f"{onde}, nenhum par exclui o zero")
            continue
        vals = [x["flavio_pp"]["estimativa"] for x in fora]
        sinal_ = (
            "todos com Flávio negativo"
            if all(v < 0 for v in vals)
            else (
                "todos com Flávio positivo"
                if all(v > 0 for v in vals)
                else "com sinais mistos"
            )
        )
        frases.append(
            f"{onde}, {len(fora)} pares de modelos excluem o zero, {sinal_} (de {pts(min(vals, key=abs), 2)} a "
            f"{pts(max(vals, key=abs), 2)})"
        )
    frageis = sorted(
        {
            f"{x['b']} contra {x['a']}"
            for est in ("dentro_zona", "dentro_local")
            for x in (U.get(est) or {}).get("pares", [])
            if _fora_do_zero(x) and (x.get("unidades") or 0) < POUCAS
        }
    )
    texto = "; ".join(frases) + "."
    if frageis:
        texto += (
            f" Com menos de {POUCAS} unidades, o intervalo é frágil: {lista(frageis)}."
        )
    A22 = U.get("ano_2022") or {}
    p22 = [
        x
        for x in (A22.get("dentro_zona") or {}).get("pares", [])
        if (x.get("bolsonaro_pp") or {}).get("estimativa") is not None
    ]
    if p22:
        m22 = max(p22, key=lambda x: x.get("unidades") or 0)
        b = m22["bolsonaro_pp"]
        texto += (
            f" Em 2022, no par com mais zonas ({m22['b']} contra {m22['a']}), o mesmo estimador dá a Bolsonaro "
            f"{pts(b['estimativa'], 2)} (de {sinal(b['ic95'][0], 2)} a {sinal(b['ic95'][1], 2)}; {inteiro(m22['unidades'])} zonas)."
        )
    return p(texto[0].upper() + texto[1:], "verificado")


# ------------------------------------------------------------------ outras


def outras_tabela(S: dict) -> str:
    OD = S["outras"]
    cp, zv = OD["comparecimento"], OD["zero_votos"]
    zl = (zv.get("lula") or {}).get("secoes") or 0
    zf = (zv.get("flavio") or {}).get("secoes") or 0
    zf_uf = (zv.get("flavio") or {}).get("por_uf") or []
    linhas = [
        ["Comparecimento acima de 100% dos aptos", inteiro(cp["acima_100"]), ""],
        [
            "Comparecimento de 100%",
            inteiro(cp["igual_100"]),
            f"{inteiro(cp['abstencao_zero'])} sem nenhuma abstenção",
        ],
        [f"Lula zerado, {zv['minimo_votantes']} votantes ou mais", inteiro(zl), ""],
        [
            f"Flávio zerado, {zv['minimo_votantes']} votantes ou mais",
            inteiro(zf),
            lista([f"{x['uf']} {x['secoes']}" for x in zf_uf[:4]]),
        ],
    ]
    for x in OD.get("tipo_urna") or []:
        if x.get("tipo_urna") != 1 and x.get("dif_zona_lula_pp") is not None:
            linhas.append(
                [
                    escape((x.get("descricao") or "").capitalize()),
                    inteiro(x["secoes"]),
                    f"Lula {pts(x['dif_zona_lula_pp'])}, Flávio {pts(x['dif_zona_flavio_pp'])} contra o resto da zona",
                ]
            )
    for x in OD.get("tipo_arquivo") or []:
        if x.get("tipo_arquivo") != 1:
            linhas.append(
                [
                    escape((x.get("descricao") or "").capitalize()),
                    inteiro(x["secoes"]),
                    "arquivo fora do padrão",
                ]
            )
    return tabela(
        ["O que a seção mostra", "Seções", "Detalhe"],
        linhas,
        "Contagens sobre as seções válidas.",
    )


def outras_b(S: dict) -> str:
    OD = S["outras"]
    H = OD["horarios"]
    rc = OD["recebimento"]
    d0 = rc.get("depois_0000") or {}
    d1 = rc.get("depois_0100") or {}
    ab = H.get("abertura") or {}
    frase = (
        f"Em hora de Brasília, {inteiro(ab.get('antes_0730'))} seções abriram antes das 7h30 e "
        f"{inteiro(ab.get('depois_0900'))} depois das 9h."
    )
    if d0.get("secoes"):
        muns = lista(
            [
                f"{nome_bonito(m['municipio'])} ({m['uf']}, {inteiro(m['secoes'])})"
                for m in (d0.get("municipios") or [])[:4]
            ]
        )
        frase += (
            f" Pelo carimbo de recebimento, {inteiro(d0['secoes'])} boletins chegaram depois da meia-noite, com Lula a "
            f"{pct(d0.get('lula_pct'))} dos {inteiro(d0.get('validos'))} válidos"
            + (f", sobretudo de {muns}" if muns else "")
            + f"; depois da 01h, {inteiro(d1.get('secoes'))}. A régua do capítulo 2, a hora de geração do arquivo "
            "nacional, conta bem menos seções depois da meia-noite; a diferença entre as duas réguas não está explicada "
            "nos dados e fica registrada como pendência."
        )
    h = p(frase, "verificado")
    ud = OD.get("ultimo_digito") or []
    bf = OD.get("benford2") or []
    if ud or bf:
        frase = []
        if ud:
            frase.append(
                f"No teste do último dígito, {sum(1 for x in ud if x['p'] < 0.05)} de {len(ud)} combinações de UF e "
                "candidato ficam abaixo de p = 0,05"
            )
        if bf:
            frase.append(
                f"no do segundo dígito de Benford, {sum(1 for x in bf if x['p'] < 0.05)} de {len(bf)}"
            )
        h += p(
            "; ".join(frase)
            + f". O acaso poria cerca de {max(1, round(len(ud or bf) / 20))} de cada {len(ud or bf)} abaixo do corte, e "
            "voto não segue Benford por construção (Deckert, Myagkov e Ordeshook, 2011): curiosidade, não teste.",
            "inferencia",
        )
    return h


# ------------------------------------------------------------------ montagem


def bloco(S: dict, fig: Callable[[str], str]) -> str:
    """A parte por seção do capítulo 12, figura antes do parágrafo que a lê."""
    h = "<h3>Da zona para a seção</h3>" + intro(S)
    h += "<h3>Seções acima de 90%</h3>" + fig("secoes_90") + extremos_contagem(S)
    h += fig("secoes_excesso") + extremos_excesso(S)
    h += fig("secoes_tamanho_tipo") + extremos_perfil(S)
    h += extremos_2022(S) + extremos_amostras(S)
    k = S["clusters"]["k"]
    h += f"<h3>{grupos_extenso(k).capitalize()} grupos de seções</h3>"
    h += clusters_falha(S) + fig("clusters_secoes") + clusters_a(S)
    h += clusters_leitura(S) + fig("clusters_regiao") + clusters_b(S)
    h += escolha_k(S["clusters"])
    h += "<h3>Modelo de urna</h3>" + fig("modelo_urna_uf") + urna_a(S)
    h += fig("voto_por_modelo_nacional") + urna_voto_nacional(S)
    h += fig("voto_por_modelo_uf") + urna_voto_uf(S)
    h += fig("urna_reguas") + urna_reguas(S)
    h += fig("modelo_urna_zona") + urna_pares(S)
    h += (
        "<h3>O que mais a seção mostra</h3>"
        + fig("secoes_outras")
        + outras_tabela(S)
        + outras_b(S)
    )
    return h


def limites_secao(S: dict) -> list[str]:
    """Limites da análise por seção que valem para o leitor (os de método ficam no memorando)."""
    chaves = ("Tipo de local", "A comparação com 2022", "A mistura gaussiana")
    return [escape(x) for x in S.get("limites") or [] if x.startswith(chaves)]


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
