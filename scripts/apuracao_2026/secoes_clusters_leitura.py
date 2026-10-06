"""Leitura dos grupos da mistura gaussiana: padrão de zeros, rótulos e frases.

Tudo sai dos números do bloco ajustado em `secoes_clusters`: o padrão de zeros
que define cada grupo (testado contra os outros grupos), o rótulo curto, a
comparação entre as nuvens visíveis na projeção e a divisão da mistura, a
estabilidade entre sementes e as frases de `interpretacao`, cuja primeira diz se
os grupos são geografia.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from itertools import pairwise
from typing import Any

import numpy as np

from .secoes_base import num, r2

LIMIAR_ZEROS = 50.0  # pontos de diferença na proporção de zeros entre grupos
COBRE = 95.0  # % das seções do grupo em que o padrão de zeros vale
DIFERE = 30.0  # pontos de diferença contra ao menos um outro grupo
LIMIAR_CARGA = 0.15  # carga abaixo disso nos dois componentes: quase não pesa
LIMIAR_SEPARA = 90.0  # acerto balanceado (%) de um corte no componente
LIMIAR_GEOGRAFIA = 0.3  # V de Cramér entre grupo e região
EXTENSO = {1: "um", 2: "dois", 3: "três", 4: "quatro", 5: "cinco", 6: "seis"}
EXTENSO_F = {
    2: "duas",
    3: "três",
    4: "quatro",
    5: "cinco",
    6: "seis",
    7: "sete",
    8: "oito",
    9: "nove",
    10: "dez",
}
NOMES_PARTES = {
    "brancos": "brancos",
    "nulos": "nulos",
    "abstencao": "abstenção",
    "demais": "candidaturas nanicas somadas",
    "terceiros": "as outras dez candidaturas somadas",
    "brancos_nulos": "brancos e nulos",
}
FRASE_PARTE = {  # (sem, com) para as partes que não são uma candidatura
    "brancos": ("sem voto branco", "com voto branco"),
    "nulos": ("sem voto nulo", "com voto nulo"),
    "abstencao": ("sem abstenção", "com abstenção"),
    "brancos_nulos": ("sem branco nem nulo", "com branco ou nulo"),
    "demais": (
        "sem voto nas candidaturas nanicas",
        "com voto nas candidaturas nanicas",
    ),
    "terceiros": (
        "sem voto nas outras dez candidaturas",
        "com voto nas outras dez candidaturas",
    ),
}


def extenso(n: int) -> str:
    return EXTENSO.get(n, str(n))


def amplitude_zeros(
    comps: Sequence[Mapping[str, Any]], features: Sequence[str]
) -> dict[str, float]:
    """Diferença, em pontos, entre a maior e a menor proporção de zeros por grupo."""
    amp = {}
    for f in features:
        vals = [cc["zeros_pct"].get(f) or 0.0 for cc in comps]
        amp[f] = max(vals) - min(vals)
    return amp


# ---------------------------------------------------------------- padrão de zeros


def menos_votadas(
    fr: np.ndarray, aptos: np.ndarray, chaves: Sequence[str]
) -> list[int]:
    """Índices das candidaturas (fora Lula e Flávio), da menos para a mais votada."""
    votos = (fr * aptos[:, None]).sum(axis=0)
    idx = [
        i
        for i, f in enumerate(chaves)
        if f not in NOMES_PARTES and f not in ("lula", "flavio")
    ]
    return sorted(idx, key=lambda i: (votos[i], chaves[i]))


def _parcelas(col: np.ndarray, grupos: Sequence[np.ndarray]) -> np.ndarray:
    return np.array([100 * float(col[g].mean()) if g.any() else 0.0 for g in grupos])


def _vale(sh: np.ndarray, c: int) -> tuple[bool, int]:
    """O padrão cobre o grupo `c` e difere de algum outro? Devolve o mais distante."""
    outros = [g for g in range(len(sh)) if g != c]
    if not outros:
        return False, -1
    g = min(outros, key=lambda o: sh[o])
    return bool(sh[c] >= COBRE and sh[c] - sh[g] >= DIFERE), g


def _item(
    tipo: str, partes: Sequence[str], sh: np.ndarray, c: int, g: int, m: int | None
) -> dict[str, Any]:
    return {
        "tipo": tipo,
        "conjunto": "menos_votadas" if m else None,
        "m": m,
        "partes": list(partes),
        "pct_grupo": r2(sh[c], 1),
        "outro_grupo": g,
        "pct_outro": r2(sh[g], 1),
        "pct_por_grupo": [r2(v, 1) for v in sh],
    }


def _prefixo(
    pref: Sequence[np.ndarray],
    c: int,
    tipo: str,
    menos: Sequence[int],
    chaves: Sequence[str],
) -> dict[str, Any] | None:
    """Nenhum voto nas m menos votadas (maior m) ou algum voto nelas (menor m)."""
    ms = [
        m
        for m in range(2, len(menos) + 1)
        if _vale(pref[m - 1] if tipo == "sem" else 100 - pref[m - 1], c)[0]
    ]
    if not ms:
        return None
    m = max(ms) if tipo == "sem" else min(ms)
    sh = pref[m - 1] if tipo == "sem" else 100 - pref[m - 1]
    return _item(tipo, [chaves[i] for i in menos[:m]], sh, c, _vale(sh, c)[1], m)


def _falta_distinguir(itens: Sequence[Mapping[str, Any]], c: int, k: int) -> list[int]:
    """Grupos dos quais nenhum item já separa `c` por `DIFERE` pontos."""
    return [
        g
        for g in range(k)
        if g != c
        and not any(
            abs(it["pct_por_grupo"][c] - it["pct_por_grupo"][g]) >= DIFERE
            for it in itens
        )
    ]


def padroes_zeros(
    zero: np.ndarray,
    rot: np.ndarray,
    k: int,
    chaves: Sequence[str],
    menos: Sequence[int],
) -> list[list[dict[str, Any]]]:
    """O padrão de zeros que define cada grupo, a partir dos números.

    Um padrão vale para o grupo quando cobre ao menos `COBRE`% das seções dele e
    difere em ao menos `DIFERE` pontos de algum outro grupo. Testa, nesta ordem:
    nenhum voto nas m candidaturas menos votadas (o maior m), algum voto nelas (o
    menor m) e cada parte sozinha (até duas). Se um outro grupo continua sem
    distinção, entra a parte que mais o separa, com a parcela ao lado.
    """
    grupos = [rot == c for c in range(k)]
    pref = [
        _parcelas(zero[:, list(menos[:m])].all(axis=1), grupos)
        for m in range(1, len(menos) + 1)
    ]
    sing = [_parcelas(zero[:, i], grupos) for i in range(len(chaves))]
    saida = []
    for c in range(k):
        itens: list[dict[str, Any]] = []
        usados: set[int] = set()
        prefixo = _prefixo(pref, c, "sem", menos, chaves)
        if prefixo:
            itens.append(prefixo)
            usados |= set(menos[: prefixo["m"]])
        simples = []
        for i in range(len(chaves)):
            if i in usados:
                continue
            for tipo, sh in (("sem", sing[i]), ("com", 100 - sing[i])):
                ok, g = _vale(sh, c)
                if ok:
                    simples.append((sh[c] - sh[g], tipo, i, sh, g))
        simples.sort(key=lambda t: (-t[0], t[2]))
        for _, tipo, i, sh, g in simples[:2]:
            itens.append(_item(tipo, [chaves[i]], sh, c, g, None))
            usados.add(i)
        if _falta_distinguir(itens, c, k):
            prefixo = _prefixo(pref, c, "com", menos, chaves)
            if prefixo:
                itens.append(prefixo)
        for g in _falta_distinguir(itens, c, k):
            livres = [i for i in range(len(chaves)) if i not in usados]
            if not livres:
                continue
            i = max(livres, key=lambda j: abs(sing[j][c] - sing[j][g]))
            if abs(sing[i][c] - sing[i][g]) < DIFERE:
                continue
            sem = sing[i][c] > sing[i][g]
            sh = sing[i] if sem else 100 - sing[i]
            tipo = "parcial_sem" if sem else "parcial_com"
            itens.append(_item(tipo, [chaves[i]], sh, c, g, None))
            usados.add(i)
        saida.append(itens)
    return saida


def _frase_simples(f: str, nome: str, sem: bool) -> str:
    if f in FRASE_PARTE:
        return FRASE_PARTE[f][0 if sem else 1]
    return f"{'sem' if sem else 'com'} voto em {nome}"


def frase_padrao(it: Mapping[str, Any], nomes: Mapping[str, str]) -> str:
    tipo = it["tipo"]
    if it.get("conjunto") == "menos_votadas":
        n = EXTENSO_F.get(it["m"], str(it["m"]))
        if tipo == "sem":
            return f"sem voto nas {n} candidaturas menos votadas"
        return f"com voto em ao menos uma das {n} candidaturas menos votadas"
    f = it["partes"][0]
    base = _frase_simples(f, nomes.get(f, f), tipo in ("sem", "parcial_sem"))
    if tipo.startswith("parcial"):
        return f"{base} em {num(it['pct_grupo'], 0)}% das seções"
    return base


def juntar(partes: Sequence[str]) -> str:
    if len(partes) <= 1:
        return "".join(partes)
    return ", ".join(partes[:-1]) + " e " + partes[-1]


def descrever_padrao(
    itens: Sequence[Mapping[str, Any]], nomes: Mapping[str, str]
) -> str:
    """Junta 'sem voto em A' e 'sem voto em B' em 'sem voto em A e em B'."""
    partes: list[str] = []
    for tipo in ("sem", "com"):
        do_tipo = [it for it in itens if it["tipo"] == tipo]
        simples = [
            nomes.get(it["partes"][0], it["partes"][0])
            for it in do_tipo
            if not it.get("conjunto") and it["partes"][0] not in FRASE_PARTE
        ]
        partes += [
            frase_padrao(it, nomes)
            for it in do_tipo
            if it.get("conjunto") or it["partes"][0] in FRASE_PARTE
        ]
        if simples:
            partes.append(f"{tipo} voto em " + " e em ".join(simples))
    partes += [
        frase_padrao(it, nomes) for it in itens if it["tipo"].startswith("parcial")
    ]
    return juntar(partes)


def rotulo(c: Mapping[str, Any], nomes: Mapping[str, str]) -> str:
    """Rótulo do grupo: o padrão de zeros que o define (se houver), o lado do voto
    e a região dominante; sem padrão de zeros, a abstenção no lugar dele."""
    v = c["centro_pct_validos"]
    reg = c["regioes"][0] if c["regioes"] else {"regiao": "?", "pct_do_cluster": 0}
    lider = "Lula" if (v["lula"] or 0) >= (v["flavio"] or 0) else "Flávio"
    pl = v["lula"] if lider == "Lula" else v["flavio"]
    regiao = f"{reg['regiao']} {num(reg['pct_do_cluster'] or 0, 0)}% das seções"
    padrao = descrever_padrao(c.get("padrao_zeros") or [], nomes)
    if padrao:
        return f"{padrao}; {lider} {num(pl or 0, 0)}% dos válidos; {regiao}"
    ab = c["centro_pct_eleitorado"].get("abstencao") or 0
    return f"{lider} {num(pl or 0, 0)}% dos válidos, abstenção {num(ab, 0)}%, {regiao}"


# ---------------------------------------------------------------- frases


def _carga(cargas: Sequence[Mapping[str, Any]], f: str) -> tuple[float, float]:
    c = next((x for x in cargas if x["feature"] == f), None)
    return (c["pc1"], c["pc2"]) if c else (0.0, 0.0)


def _nome_item(it: Mapping[str, Any], nomes: Mapping[str, str]) -> str:
    if it.get("conjunto") == "menos_votadas":
        return f"as {EXTENSO_F.get(it['m'], str(it['m']))} candidaturas menos votadas"
    f = it["partes"][0]
    return nomes.get(f, f)


def leitura_projecao(c: Mapping[str, Any], nomes: Mapping[str, str]) -> str | None:
    """Compara as nuvens visíveis na projeção com a divisão da mistura."""
    P = c.get("pca") or {}
    sep = P.get("separacao") or []
    if len(sep) < 2:
        return None
    amp = amplitude_zeros(c["componentes"], c["features"])
    nm = [nomes.get(s["feature"], s["feature"]) for s in sep]
    frases = [
        f"Na projeção, o componente 1 tem a maior carga em {nm[0]} "
        f"({num(sep[0]['carga'], 2)}) e o componente 2, em {nm[1]} "
        f"({num(sep[1]['carga'], 2)})."
    ]
    vis = [s for s in sep if (s.get("acerto_balanceado_pct") or 0) >= LIMIAR_SEPARA]
    if vis:
        frases.append(
            "As nuvens que se veem no plano são seções com e sem voto nessas partes: "
            + "; ".join(
                f"um corte no componente {s['componente']} separa as seções sem voto "
                f"em {nomes.get(s['feature'], s['feature'])} "
                f"({num(s['zeros_pct'], 1)}% do total) com acerto balanceado de "
                f"{num(s['acerto_balanceado_pct'], 1)}%"
                for s in vis
            )
            + "."
        )

    reproduz = [s for s in sep if amp.get(s["feature"], 0) >= LIMIAR_ZEROS]
    nao = [s for s in sep if amp.get(s["feature"], 0) < LIMIAR_ZEROS]
    partes = []
    if reproduz:
        partes.append("reproduz a divisão por " + _lista_amp(reproduz, amp, nomes))
    if nao:
        partes.append("não reproduz a divisão por " + _lista_amp(nao, amp, nomes))
    frases.append(f"A mistura com k = {c['k']} " + "; ".join(partes) + ".")
    visiveis = {s["feature"] for s in sep}
    cargas = P.get("cargas") or []
    ocultas, vistos = [], set()
    for cc in c["componentes"]:
        for it in cc.get("padrao_zeros") or []:
            chave = (it.get("conjunto"), it.get("m"), tuple(it["partes"]))
            if chave in vistos or set(it["partes"]) & visiveis:
                continue
            vistos.add(chave)
            cmax = max(max(abs(v) for v in _carga(cargas, f)) for f in it["partes"])
            if cmax < LIMIAR_CARGA:
                ocultas.append(f"{_nome_item(it, nomes)}, {num(cmax, 2)}")
    if ocultas:
        frases.append(
            "As partes que definem os grupos quase não pesam no plano (carga máxima "
            "em módulo nos dois componentes: "
            + "; ".join(ocultas)
            + "): essa parte da divisão não aparece na figura."
        )
    return " ".join(frases)


def _lista_amp(
    seps: Sequence[Mapping[str, Any]],
    amp: Mapping[str, float],
    nomes: Mapping[str, str],
) -> str:
    """'Romeu Zema e Ronaldo Caiado (12 e 11 pontos de diferença ...)'."""
    quem = juntar([nomes.get(s["feature"], s["feature"]) for s in seps])
    quanto = juntar([num(amp.get(s["feature"], 0), 0) for s in seps])
    return f"{quem} ({quanto} pontos de diferença na proporção de zeros entre grupos)"


def sinal(x: float, casas: int = 2) -> str:
    """Número com o menos tipográfico (U+2212) quando negativo."""
    return ("\u2212" if x < 0 else "") + num(abs(x), casas)


def estabilidade(c: Mapping[str, Any]) -> str | None:
    """Quanto o ajuste muda entre sementes: log-verossimilhança e partição."""
    aj = c.get("ajuste") or {}
    sm = aj.get("sementes") or []
    if len(sm) < 2:
        return None
    lls = [s["loglik_media"] for s in sm]
    aris = [s["ari_com_escolhida"] for s in sm if s["semente"] != aj["random_state"]]
    vs = [s["cramer_v_regiao"] for s in sm]
    no_max = aj.get("sementes_no_maximo") or 1
    vezes = "só nela" if no_max == 1 else f"em {EXTENSO_F.get(no_max, no_max)} delas"
    texto = (
        f"O ajuste publicado é o de maior log-verossimilhança entre {len(sm)} "
        f"sementes de {aj['n_init']} inicializações cada (semente {aj['random_state']}; "
        f"o máximo apareceu {vezes}). A log-verossimilhança média por seção vai de "
        f"{sinal(min(lls))} a {sinal(max(lls))} entre as sementes, e a partição muda "
        f"com elas (índice de Rand ajustado contra a escolhida de {num(min(aris), 2)} a "
        f"{num(max(aris), 2)}): a superfície tem muitos máximos locais, porque cada "
        "padrão exato de zeros é um subespaço onde um componente se encaixa com "
        "variância quase nula. O que não muda é a relação com a geografia: o V de "
        f"Cramér entre grupo e região fica entre {num(min(vs), 2)} e {num(max(vs), 2)} "
        "em todas."
    )
    bic = sorted(c.get("bic") or [], key=lambda b: b["k"])
    for a, b in pairwise(bic):
        if b["loglik_media"] < a["loglik_media"]:
            texto += (
                f" Com k = {b['k']}, a melhor log-verossimilhança encontrada "
                f"({sinal(b['loglik_media'])}) fica abaixo da de k = {a['k']} "
                f"({sinal(a['loglik_media'])}), o que o máximo global não permitiria, "
                "porque um componente a mais nunca piora o melhor ajuste: a tabela do "
                "BIC compara máximos locais."
            )
            break
    return texto


def _def_grupo(cc: Mapping[str, Any], nomes: Mapping[str, str]) -> str | None:
    itens = cc.get("padrao_zeros") or []
    if not itens:
        return None
    it = itens[0]
    return (
        f"grupo {cc['id'] + 1}, {frase_padrao(it, nomes)} "
        f"({num(it['pct_grupo'], 1)}% das seções do grupo, contra "
        f"{num(it['pct_outro'], 1)}% no grupo {it['outro_grupo'] + 1})"
    )


def interpretar(c: Mapping[str, Any], nomes: Mapping[str, str]) -> list[str]:
    """Frases geradas dos números; a primeira diz se os grupos são geografia."""
    comps = c["componentes"]
    k = c["k"]
    v = c["cramer_v_regiao"] or 0.0
    frases = []
    por_zeros = sum(
        1
        for cc in comps
        if any(it["tipo"] in ("sem", "com") for it in cc.get("padrao_zeros") or [])
    )
    deg = c.get("degrau_log") or {}
    if v < LIMIAR_GEOGRAFIA and por_zeros >= k - 1:
        defs = [d for d in (_def_grupo(cc, nomes) for cc in comps) if d]
        frases.append(
            f"Na especificação pedida, os {extenso(k)} grupos não são geografia (V de "
            f"Cramér entre grupo e região {num(v, 2)}): separam as seções pelo padrão "
            f"de zeros. {num(c['zeros_substituidos_pct'], 1)}% das células são zero e "
            "viram 0,0001; na seção mediana, de "
            f"{num(deg.get('aptos_mediana') or 0, 0)} aptos, um voto fica a "
            f"{num(deg.get('mediana') or 0, 1)} unidades de log do zero (de "
            f"{num(deg.get('p10') or 0, 1)} a {num(deg.get('p90') or 0, 1)} entre o "
            "primeiro e o último décimo das seções), e a mistura usa esse degrau para "
            "separar grupos. O padrão que define cada grupo: " + "; ".join(defs) + "."
        )
    elif v >= LIMIAR_GEOGRAFIA:
        zeros = (
            f"; o padrão de zeros também pesa em {extenso(por_zeros)} deles"
            if por_zeros
            else ""
        )
        frases.append(
            f"Os {extenso(k)} grupos acompanham a geografia (V de Cramér entre grupo "
            f"e região {num(v, 2)}){zeros}."
        )
    else:
        frases.append(
            "Os grupos não se reduzem à região (V de Cramér entre grupo e região "
            f"{num(v, 2)}); o que os separa precisa ser lido nos centros."
        )
    for nome, rot in (
        ("nanicos_somados", "nanicas somadas"),
        ("densa", "cinco partes"),
    ):
        var = (c.get("variantes") or {}).get(nome)
        if not var:
            continue
        vv = var["cramer_v_regiao"] or 0.0
        am = amplitude_zeros(var["componentes"], var["features"])
        fm = max(am, key=lambda f: am[f])
        motivo = (
            f"; o padrão de zeros ainda separa os grupos ({nomes.get(fm, fm)}, "
            f"{num(am[fm], 0)} pontos de diferença na proporção de zeros)"
            if am[fm] >= LIMIAR_ZEROS
            else ""
        )
        frases.append(
            f"Na versão com {rot}, o V de Cramér entre grupo e região é "
            f"{num(vv, 2)}{motivo}."
        )
    for cc in comps:
        frases.append(
            f"Grupo {cc['id'] + 1}: {cc['rotulo']}; {num(cc['secoes'], 0)} seções."
        )
    a = comps[c["mais_anomalo"]["id"]]
    frases.append(
        f"O grupo de menor densidade e maior dispersão é o {a['id'] + 1} "
        f"({a['rotulo']}); as 20 seções menos prováveis dele vêm com o que "
        "provavelmente as explica."
    )
    return frases
