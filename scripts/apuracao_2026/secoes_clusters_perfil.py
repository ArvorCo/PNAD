"""Leitura da mistura de cinco partes: rótulos de perfil e frases, dos números.

O rótulo de cada grupo compara o centro do grupo (média das frações do
eleitorado das seções dele) com a média nacional entre seções, em desvios-padrão
entre seções: um quarto de desvio ou mais vira "alto" ou "baixo", um desvio ou
mais vira "muito alto" ou "muito baixo". Entram no máximo três partes, das mais
distantes da média para as menos. Quando o grupo é um artefato da contagem
inteira, o artefato abre o rótulo: ausência de voto numa parte em todas as
seções do grupo (padrão de zeros de `secoes_clusters_leitura`, tipo "sem") ou o
mesmo número de votos em duas partes (empate, por exemplo brancos iguais a
nulos). A região dominante fecha.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np

from .secoes_base import num, r2
from .secoes_clusters_leitura import (
    COBRE,
    DIFERE,
    FRASE_PARTE,
    extenso,
    juntar,
    sinal,
)

LIMIAR_DESVIO = 0.25
MUITO = 1.0
MAX_QUALIFICADORES = 3
REGIAO_DOMINANTE = 50.0  # % das seções do grupo
LIMIAR_GEOGRAFIA = 0.3
QUALIFICA = {  # parte: (nome, alto, baixo)
    "lula": ("Lula", "alto", "baixo"),
    "flavio": ("Flávio", "alto", "baixo"),
    "terceiros": ("terceiros", "altos", "baixos"),
    "brancos": ("brancos", "altos", "baixos"),
    "nulos": ("nulos", "altos", "baixos"),
    "abstencao": ("abstenção", "alta", "baixa"),
}
VOTO = {"brancos": "voto branco", "nulos": "voto nulo"}
NOME_PARTE = {
    "lula": "Lula",
    "flavio": "Flávio",
    "brancos": "brancos",
    "nulos": "nulos",
    "abstencao": "abstenção",
    "terceiros": "terceiros",
}


def referencia(comp: Any) -> dict[str, dict[str, float | None]]:
    """Média e desvio-padrão entre seções, em % do eleitorado, de cada parte.

    `comp` é a `Composicao` de `secoes_clusters` (chaves, eleitorado, fora).
    """
    cols = {k: comp.eleitorado[:, i] for i, k in enumerate(comp.chaves)}
    if comp.fora is not None:
        cols["terceiros"] = comp.fora
    return {
        k: {
            "media_pct": r2(100 * float(np.mean(v)), 3),
            "dp_pct": r2(100 * float(np.std(v)), 3),
        }
        for k, v in cols.items()
    }


def centro(c: Mapping[str, Any]) -> dict[str, float]:
    """Centro do grupo em % do eleitorado, com os terceiros (o que falta)."""
    out = dict(c["centro_pct_eleitorado"])
    if c.get("terceiros_pct_eleitorado") is not None:
        out["terceiros"] = c["terceiros_pct_eleitorado"]
    return out


def desvios(
    c: Mapping[str, Any], ref: Mapping[str, Mapping[str, float | None]]
) -> dict[str, float]:
    """Distância do centro do grupo à média nacional, em desvios-padrão entre seções."""
    out = {}
    for k, v in centro(c).items():
        r = ref.get(k) or {}
        dp = r.get("dp_pct")
        if v is None or not dp:
            continue
        out[k] = (v - (r.get("media_pct") or 0.0)) / dp
    return out


def partes_do_artefato(c: Mapping[str, Any]) -> set[str]:
    """Partes já descritas pelo artefato (zero ou empate), fora dos qualificadores."""
    out = {
        f
        for it in c.get("padrao_zeros") or []
        if it["tipo"] == "sem" and not it.get("conjunto")
        for f in it["partes"]
    }
    return out | {f for it in c.get("padrao_empates") or [] for f in it["partes"]}


def qualificadores(
    c: Mapping[str, Any], ref: Mapping[str, Mapping[str, float | None]]
) -> list[str]:
    z = desvios(c, ref)
    fora = partes_do_artefato(c) if c.get("artefato") else set()
    fortes = sorted(
        (
            k
            for k in z
            if k in QUALIFICA and k not in fora and abs(z[k]) >= LIMIAR_DESVIO
        ),
        key=lambda k: (-abs(z[k]), k),
    )[:MAX_QUALIFICADORES]
    out = []
    for k in fortes:
        nome, alto, baixo = QUALIFICA[k]
        grau = "muito " if abs(z[k]) >= MUITO else ""
        out.append(f"{nome} {grau}{alto if z[k] > 0 else baixo}")
    return out


def regiao_dominante(c: Mapping[str, Any]) -> str:
    regs = c.get("regioes") or []
    if not regs:
        return "região desconhecida"
    r0 = regs[0]
    if (r0["pct_do_cluster"] or 0) >= REGIAO_DOMINANTE or len(regs) < 2:
        return f"{r0['regiao']} {num(r0['pct_do_cluster'] or 0, 0)}% das seções"
    r1 = regs[1]
    return (
        f"{r0['regiao']} {num(r0['pct_do_cluster'] or 0, 0)}% e {r1['regiao']} "
        f"{num(r1['pct_do_cluster'] or 0, 0)}% das seções"
    )


def contagens(comp: Any) -> np.ndarray:
    """Votos (e abstenções) de cada parte por seção, inteiros."""
    return np.rint(comp.unidades[:, None] * comp.fr).astype(np.int64)


def empates_por_par(cont: np.ndarray, chaves: Sequence[str]) -> list[dict[str, Any]]:
    """Seções em que duas partes têm o mesmo número de votos, por par."""
    n = len(cont)
    out = []
    for i in range(len(chaves)):
        for j in range(i + 1, len(chaves)):
            m = int((cont[:, i] == cont[:, j]).sum())
            out.append(
                {
                    "partes": [chaves[i], chaves[j]],
                    "secoes": m,
                    "pct_secoes": r2(100 * m / n, 2),
                }
            )
    return out


def padroes_empate(
    cont: np.ndarray, rot: np.ndarray, k: int, chaves: Sequence[str]
) -> list[list[dict[str, Any]]]:
    """Empate que define cada grupo: mesma regra do padrão de zeros.

    Vale quando o mesmo número de votos em duas partes cobre ao menos 95% das
    seções do grupo e difere em ao menos 30 pontos de algum outro grupo.
    """
    grupos = [rot == c for c in range(k)]
    saida: list[list[dict[str, Any]]] = [[] for _ in range(k)]
    for i in range(len(chaves)):
        for j in range(i + 1, len(chaves)):
            eq = cont[:, i] == cont[:, j]
            sh = np.array(
                [100 * float(eq[g].mean()) if g.any() else 0.0 for g in grupos]
            )
            for c in range(k):
                outros = [g for g in range(k) if g != c]
                if not outros:
                    continue
                g = min(outros, key=lambda o: sh[o])
                if sh[c] >= COBRE and sh[c] - sh[g] >= DIFERE:
                    saida[c].append(
                        {
                            "partes": [chaves[i], chaves[j]],
                            "pct_grupo": r2(sh[c], 1),
                            "outro_grupo": g,
                            "pct_outro": r2(sh[g], 1),
                            "pct_por_grupo": [r2(v, 1) for v in sh],
                        }
                    )
    return saida


def artefato(c: Mapping[str, Any], nomes: Mapping[str, str]) -> str:
    """O artefato da contagem que define o grupo inteiro, se houver.

    Ausência de voto numa parte (padrão de zeros do tipo "sem") ou o mesmo
    número de votos em duas partes. Ter voto numa parte (tipo "com") não entra:
    no modelo de cinco partes é o estado comum, não um traço do grupo.
    """
    frases = []
    for it in c.get("padrao_zeros") or []:
        if it["tipo"] != "sem" or it.get("conjunto"):
            continue
        f = it["partes"][0]
        frases.append(
            FRASE_PARTE[f][0] if f in FRASE_PARTE else f"sem voto em {nomes.get(f, f)}"
        )
    for it in c.get("padrao_empates") or []:
        a, b = (_nome(x, nomes) for x in it["partes"])
        frases.append(f"mesmo número de {a} e de {b}")
    return juntar(frases)


def rotulo_perfil(
    c: Mapping[str, Any],
    ref: Mapping[str, Mapping[str, float | None]],
    nomes: Mapping[str, str],
) -> str:
    """'Lula alto, abstenção alta; Nordeste 78% das seções'."""
    quals = qualificadores(c, ref)
    perfil = ", ".join(quals) if quals else "perto da média nacional"
    art = c.get("artefato")
    partes = [art] if art else []
    return "; ".join([*partes, perfil, regiao_dominante(c)])


def resumo_grupos(comps: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Só o essencial de cada grupo: rótulo, tamanho, região e centro nos válidos."""
    out = []
    for c in comps:
        r0 = (c.get("regioes") or [{}])[0]
        out.append(
            {
                "id": c["id"],
                "rotulo": c["rotulo"],
                "secoes": c["secoes"],
                "pct_secoes": c["pct_secoes"],
                "regiao": r0.get("regiao"),
                "regiao_pct": r0.get("pct_do_cluster"),
                "centro_pct_validos": c["centro_pct_validos"],
            }
        )
    return out


# ---------------------------------------------------------------- frases


def _nome(k: str, nomes: Mapping[str, str]) -> str:
    return NOME_PARTE.get(k) or nomes.get(k, k)


def _sem(k: str, nomes: Mapping[str, str]) -> str:
    """'sem voto branco', 'sem voto em Lula'."""
    return FRASE_PARTE[k][0] if k in FRASE_PARTE else f"sem voto em {_nome(k, nomes)}"


def leitura_projecao_perfil(
    c: Mapping[str, Any], nomes: Mapping[str, str]
) -> str | None:
    """O que cada eixo da projeção opõe e em qual eixo os grupos se afastam."""
    P = c.get("pca") or {}
    cargas = P.get("cargas") or []
    ve = P.get("variancia_explicada") or []
    if not cargas or len(ve) < 2:
        return None
    frases = []
    for j, eixo in enumerate(("pc1", "pc2")):
        pos = max(cargas, key=lambda x: x[eixo])
        neg = min(cargas, key=lambda x: x[eixo])
        frases.append(
            f"o componente {j + 1} ({num(100 * ve[j], 1)}% da variância) opõe "
            f"{_nome(pos['feature'], nomes)} (carga {sinal(pos[eixo])}) a "
            f"{_nome(neg['feature'], nomes)} ({sinal(neg[eixo])})"
        )
    texto = "Na projeção, " + "; ".join(frases) + "."
    centros = P.get("centros") or []
    tam = {cc["id"]: cc["secoes"] for cc in c.get("componentes") or []}
    if len(centros) > 1:
        w = np.array([tam.get(x["cluster"], 1) for x in centros], dtype=float)
        disp = []
        for eixo in ("x", "y"):
            v = np.array([x[eixo] for x in centros], dtype=float)
            m = float(np.average(v, weights=w))
            disp.append(float(np.average((v - m) ** 2, weights=w)))
        j = int(np.argmax(disp))
        texto += (
            f" Os centros dos grupos se afastam mais no componente {j + 1} "
            f"(variância ponderada dos centros {num(disp[j], 2)}, contra "
            f"{num(disp[1 - j], 2)} no outro)."
        )
    for s in P.get("separacao") or []:
        if (s.get("acerto_balanceado_pct") or 0) >= 90 and (
            s.get("zeros_pct") or 0
        ) > 0:
            texto += (
                f" Um corte no componente {s['componente']} separa as seções "
                f"{_sem(s['feature'], nomes)} ({num(s['zeros_pct'], 1)}% do total) com "
                f"acerto balanceado de {num(s['acerto_balanceado_pct'], 1)}%."
            )
    return texto


def estabilidade_perfil(c: Mapping[str, Any]) -> str | None:
    aj = c.get("ajuste") or {}
    d = aj.get("diagnostico_convergencia")
    if not d:
        return None
    vs = [s["cramer_v_regiao"] for s in aj.get("sementes") or []]
    texto = d["frase"]
    if vs:
        texto += (
            f" O V de Cramér entre grupo e região fica entre {num(min(vs), 2)} e "
            f"{num(max(vs), 2)} em todas as partidas."
        )
    return texto


def artefatos(c: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [cc for cc in c["componentes"] if cc.get("artefato")]


def _geografia(c: Mapping[str, Any]) -> str:
    k = c["k"]
    v, vu = c["cramer_v_regiao"] or 0.0, c["cramer_v_uf"] or 0.0
    q = (c.get("variantes") or {}).get("quinze_partes") or {}
    v15 = q.get("cramer_v_regiao")
    antes = (
        f", contra {num(v15, 2)} com as {len(q.get('features') or [])} partes"
        if v15 is not None
        else ""
    )
    if v >= LIMIAR_GEOGRAFIA:
        return (
            f"Com as cinco partes, os {extenso(k)} grupos acompanham a geografia: V de "
            f"Cramér entre grupo e região de {num(v, 2)}{antes}, e de {num(vu, 2)} com a UF."
        )
    if v15 is not None and v > v15 + 0.02:
        return (
            f"Com as cinco partes, a associação entre grupo e região sobe pouco (V de "
            f"Cramér de {num(v, 2)}{antes}; {num(vu, 2)} com a UF) e fica abaixo de "
            f"{num(LIMIAR_GEOGRAFIA, 1)}: cada grupo ainda mistura regiões."
        )
    return (
        f"Com as cinco partes, a associação entre grupo e região não melhora (V de "
        f"Cramér de {num(v, 2)}{antes}; {num(vu, 2)} com a UF)."
    )


def _artefatos(c: Mapping[str, Any], nomes: Mapping[str, str]) -> str:
    k = c["k"]
    zp = c.get("zeros_por_parte") or {}
    med = c.get("mediana_votos_por_secao") or {}
    deg = c.get("degrau_log") or {}
    sem = juntar(
        [
            f"{num(z['pct_secoes'], 2)}% das seções {_sem(p, nomes)}"
            for p, z in zp.items()
            if (z.get("pct_secoes") or 0) >= 0.1
        ]
    )
    emp = [
        e
        for e in c.get("empates_por_par") or []
        if any(
            it["partes"] == e["partes"]
            for cc in c["componentes"]
            for it in cc.get("padrao_empates") or []
        )
    ]
    frase_emp = juntar(
        [
            f"{num(e['pct_secoes'], 2)}% das seções têm o mesmo número de "
            f"{_nome(e['partes'][0], nomes)} e de {_nome(e['partes'][1], nomes)}"
            for e in emp
        ]
    )
    zeros = f"{num(c['zeros_substituidos_pct'], 2)}% das células são zero" + (
        f" ({sem})" if sem else ""
    )
    art = artefatos(c)
    if not art:
        return (
            f"Nenhum grupo é artefato da contagem inteira: {zeros}, e nenhum padrão de "
            "zeros ou de empate cobre 95% das seções de um grupo."
        )
    defs = juntar(
        [
            f"o {cc['id'] + 1} ({cc['artefato']}; {num(cc['secoes'], 0)} seções)"
            for cc in art
        ]
    )
    pequenas = juntar(
        [
            f"{num(med[p], 0)} {_nome(p, nomes)}"
            for p in ("brancos", "nulos")
            if med.get(p) is not None
        ]
    )
    texto = (
        f"Cinco partes não bastaram: {extenso(len(art))} dos {extenso(k)} grupos "
        f"{'é artefato' if len(art) == 1 else 'são artefatos'} da contagem inteira, não "
        f"perfil de seção: {defs}."
    )
    tem_zero = any(
        it["tipo"] == "sem" and not it.get("conjunto")
        for cc in art
        for it in cc.get("padrao_zeros") or []
    )
    tem_emp = any(cc.get("padrao_empates") for cc in art)
    mecanismo = juntar(
        (
            [
                f"o zero vira um degrau de {num(deg.get('mediana') or 0, 1)} unidades até o primeiro voto"
            ]
            if tem_zero
            else []
        )
        + (["o empate vira uma razão exata de 1"] if tem_emp else [])
    )
    if pequenas and mecanismo:
        texto += (
            f" Brancos e nulos são poucos votos por seção (mediana de {pequenas}); no "
            f"logaritmo, {mecanismo}, e a mistura gasta um componente em cada padrão."
        )
    texto += f" {zeros[0].upper()}{zeros[1:]}" + (
        f", e {frase_emp}." if frase_emp else "."
    )
    return texto


def _perfis(c: Mapping[str, Any]) -> str | None:
    """Os grupos que não são artefato: o que mostram e se repetem o mapa."""
    sub = [cc for cc in c["componentes"] if not cc.get("artefato")]
    if not sub or len(sub) == len(c["componentes"]):
        return None
    tot = sum(cc["pct_secoes"] or 0 for cc in sub)
    itens = []
    for cc in sub:
        cv = cc["centro_pct_validos"]
        r0 = (cc.get("regioes") or [{}])[0]
        itens.append(
            f"o {cc['id'] + 1} (Lula {num(cv['lula'] or 0, 1)}% e Flávio "
            f"{num(cv['flavio'] or 0, 1)}% dos válidos; {r0.get('regiao', '')} "
            f"{num(r0.get('pct_do_cluster') or 0, 0)}% das seções)"
        )
    texto = (
        f"{'O outro grupo' if len(sub) == 1 else 'Os outros ' + extenso(len(sub))}, com "
        f"{num(tot, 1)}% das seções, {'é perfil' if len(sub) == 1 else 'são perfis'} de "
        f"voto: {juntar(itens)}."
    )
    lid = {}
    for cc in sub:
        cv = cc["centro_pct_validos"]
        nome = "Lula" if (cv["lula"] or 0) >= (cv["flavio"] or 0) else "Flávio"
        lid.setdefault(nome, cc)
    if len(sub) == 2 and len(lid) == 2:
        rl = (lid["Lula"].get("regioes") or [{}])[0]
        rf = (lid["Flávio"].get("regioes") or [{}])[0]
        if rl.get("regiao") != rf.get("regiao"):
            texto += (
                " É a divisão que o mapa por zona já mostra: o grupo em que Lula lidera "
                f"tem {num(rl.get('pct_do_cluster') or 0, 0)}% das seções no "
                f"{rl.get('regiao')}, e o grupo em que Flávio lidera, "
                f"{num(rf.get('pct_do_cluster') or 0, 0)}% no {rf.get('regiao')}. Nessa "
                "parte, a mistura não acrescenta ao mapa."
            )
    return texto


def _geometria(c: Mapping[str, Any], nomes: Mapping[str, str]) -> str | None:
    """Por que as partes pequenas mandam no espaço das log-razões."""
    cargas = (c.get("pca") or {}).get("cargas") or []
    med = c.get("mediana_votos_por_secao") or {}
    if not cargas or not med.get("lula"):
        return None
    top = max(cargas, key=lambda x: abs(x["pc1"]))
    if top["feature"] not in ("brancos", "nulos") or not med.get(top["feature"]):
        return None
    m, ml = med[top["feature"]], med["lula"]
    return (
        "No espaço das log-razões, uma parte pequena pesa tanto quanto uma grande: "
        f"passar de {num(m, 0)} para {num(2 * m, 0)} {_nome(top['feature'], nomes)} "
        f"afasta a seção tanto quanto passar de {num(ml, 0)} para {num(2 * ml, 0)} votos "
        f"em Lula. Por isso o primeiro eixo da projeção é o "
        f"{VOTO.get(top['feature'], top['feature'])} (carga {sinal(abs(top['pc1']))}), "
        "não a disputa entre os finalistas."
    )


def leitura(c: Mapping[str, Any], nomes: Mapping[str, str]) -> dict[str, str | None]:
    """As frases de leitura com nome, para o texto da página escolher cada uma."""
    return {
        "geografia": _geografia(c),
        "artefatos": _artefatos(c, nomes),
        "perfis": _perfis(c),
        "geometria": _geometria(c, nomes),
    }


def interpretar_perfil(c: Mapping[str, Any], nomes: Mapping[str, str]) -> list[str]:
    """Frases geradas dos números. A primeira compara a geografia com a versão de 15
    partes; a segunda diz quantos grupos ainda são artefatos da contagem inteira; a
    terceira lê os grupos que são perfil de voto."""
    comps = c["componentes"]
    frases = [x for x in leitura(c, nomes).values() if x]
    for cc in comps:
        cv = cc["centro_pct_validos"]
        ce = centro(cc)
        frases.append(
            f"Grupo {cc['id'] + 1}: {cc['rotulo']}; {num(cc['secoes'], 0)} seções "
            f"({num(cc['pct_secoes'], 1)}%). Centro: Lula {num(cv['lula'] or 0, 1)}% e "
            f"Flávio {num(cv['flavio'] or 0, 1)}% dos válidos; abstenção "
            f"{num(ce.get('abstencao') or 0, 1)}%, brancos {num(ce.get('brancos') or 0, 1)}%, "
            f"nulos {num(ce.get('nulos') or 0, 1)}% e terceiros "
            f"{num(ce.get('terceiros') or 0, 1)}% do eleitorado."
        )
    a = comps[c["mais_anomalo"]["id"]]
    frases.append(
        f"O grupo de menor densidade e maior dispersão é o {a['id'] + 1} "
        f"({a['rotulo']}); as 20 seções menos prováveis dele vêm com o que "
        "provavelmente as explica."
    )
    mv = (c.get("variantes") or {}).get("meio_voto")
    ari = (c.get("sensibilidade") or {}).get("ari_principal_vs_meio_voto")
    if mv and ari is not None:
        frases.append(
            "Com zero trocado por meio voto, e não por 0,0001, o V de Cramér entre "
            f"grupo e região é {num(mv['cramer_v_regiao'] or 0, 2)} e o índice de Rand "
            f"ajustado contra a partição principal, {num(ari, 2)}."
        )
    return frases


def textos(saida: dict[str, Any], nomes: Mapping[str, str]) -> None:
    """Rótulos e frases do bloco principal, todos refeitos a partir do dicionário."""
    ref = saida["referencia_nacional"]
    for cc in saida["componentes"]:
        cc["artefato"] = artefato(cc, nomes) or None
        cc["rotulo"] = rotulo_perfil(cc, ref, nomes)
    saida["leitura_projecao"] = leitura_projecao_perfil(saida, nomes)
    saida["estabilidade"] = estabilidade_perfil(saida)
    saida["leitura"] = leitura(saida, nomes)
    saida["interpretacao"] = interpretar_perfil(saida, nomes)
