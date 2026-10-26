"""Textos do capítulo "Seis governadores"; números de ``governadores.json``.

Viradas sobre o 1º turno, a disputa mais apertada e as trocas de liderança da
noite são detectadas pelos próprios dados, não escritas à mão.
"""

from __future__ import annotations

from apuracao_2026.pagina_comum import cartao, inteiro, nota, num, p
from apuracao_2026.pagina_fig_base import campo_nome

from .pagina_fig_governadores import nome, par


def lider_1t(u: dict) -> dict:
    return max(u["candidatos"], key=lambda c: c.get("t1_pct") or 0)


def viradas_1t(G: dict) -> list[dict]:
    """UFs em que o vencedor do 2º turno não liderava o 1º."""
    return [u for u in G["ufs"] if par(u)[0]["sqcand"] != lider_1t(u)["sqcand"]]


def mais_apertada(G: dict) -> dict:
    return min(G["ufs"], key=lambda u: u.get("margem_pp") or 0)


def com_trocas(G: dict) -> list[dict]:
    return [u for u in G["ufs"] if u.get("n_viradas")]


NUMERAL = {1: "Uma", 2: "Duas", 3: "Três", 4: "Quatro", 5: "Cinco", 6: "Seis"}


def titulo(G: dict) -> str:
    n = len(G["ufs"])
    nv = len(viradas_1t(G))
    ap = mais_apertada(G).get("margem_pp")
    if nv and ap is not None and ap < 2:
        vir = "virada" if nv == 1 else "viradas"
        return (
            f"{NUMERAL.get(n, n)} governadores.<br><em>{NUMERAL.get(nv, nv)} {vir} sobre o 1º turno, "
            f"uma disputa de {num(ap, 1)} ponto.</em>"
        )
    return f"{NUMERAL.get(n, n)} governadores.<br><em>O 2º turno nos estados.</em>"


def lead(G: dict) -> str:
    ap = mais_apertada(G)
    a, _ = par(ap)
    ufs = sorted(G["ufs"], key=lambda u: u["uf"])
    return (
        f"{', '.join(u['uf'] for u in ufs[:-1])} e {ufs[-1]['uf']}. A mais apertada, "
        f"{ap['uf']}, terminou com {inteiro(ap['margem_votos'])} votos de diferença para "
        f"{nome(a)}."
    )


def cartoes(G: dict) -> str:
    out = ['<div class="finding-grid">']
    vir = viradas_1t(G)
    if vir:
        maior = max(vir, key=lambda u: u.get("margem_pp") or 0)
        a, _ = par(maior)
        out.append(
            cartao(
                f"{num(a['pct'], 2)}%",
                f"{nome(a)} ({maior['uf']}), que estava atrás no 1º turno",
            )
        )
    ap = mais_apertada(G)
    out.append(
        cartao(
            f"{num(ap['margem_pp'], 2)} pp",
            f"{ap['uf']}: {inteiro(ap['margem_votos'])} votos de diferença",
        )
    )
    for u in com_trocas(G)[:1]:
        out.append(
            cartao(
                inteiro(u["n_viradas"]), f"trocas de liderança na noite em {u['uf']}"
            )
        )
    out.append(
        cartao(
            f"{len(vir)} de {len(G['ufs'])}",
            "UFs em que o líder do 1º turno perdeu"
            + (f" ({', '.join(u['uf'] for u in vir)})" if vir else ""),
        )
    )
    out.append("</div>")
    return "".join(out)


def abre(G: dict) -> str:
    frases = []
    ap = mais_apertada(G)
    vir = sorted(viradas_1t(G), key=lambda u: -(u.get("margem_pp") or 0))
    for u in vir:
        a, b = par(u)
        f = (
            f"No {u['uf']}, {nome(a)} ({a.get('partido')}) virou sobre {nome(b)} "
            f"({b.get('partido')}), que liderava o 1º turno por {num(b['t1_pct'], 2)}% a "
            f"{num(a['t1_pct'], 2)}%, e venceu por {num(a['pct'], 2)}% a {num(b['pct'], 2)}%"
        )
        if u is ap:
            f += (
                f": {num(ap['margem_pp'], 2)} pp, {inteiro(ap['margem_votos'])} votos em "
                f"{inteiro(ap.get('validos'))} válidos, a disputa mais apertada das seis"
            )
        frases.append(f + ".")
    if ap not in vir:
        a, b = par(ap)
        frases.append(
            f"No {ap['uf']}, {nome(a)} ({a.get('partido')}) venceu {nome(b)} ({b.get('partido')}) "
            f"por {num(ap['margem_pp'], 2)} pp, {inteiro(ap['margem_votos'])} votos em "
            f"{inteiro(ap.get('validos'))} válidos."
        )
    outros = [u for u in G["ufs"] if u not in vir and u is not ap]
    if outros:
        frases.append(
            "Nas demais, quem liderou o 1º turno confirmou: "
            + "; ".join(
                f"{u['uf']}, {nome(par(u)[0])} {num(par(u)[0]['pct'], 2)}%"
                for u in outros
            )
            + "."
        )
    return p(" ".join(frases), "verificado")


def noite(G: dict) -> str:
    tr = com_trocas(G)
    if not tr:
        return p(
            "Nenhuma UF teve troca de liderança entre versões do arquivo de governador durante a noite.",
            "verificado",
        )
    frases = []
    for u in tr:
        pst_max = max(v.get("pst") or 0 for v in u["viradas"])
        ult = u["viradas"][-1]
        frases.append(
            f"No {u['uf']}, {inteiro(u['n_viradas'])} trocas de liderança, todas com no máximo "
            f"{num(pst_max, 2)}% das seções totalizadas; a última, às {ult['gerado_brt'][-8:-3]}, "
            f"deixou {nome_bonito_sq(u, ult['para'])} à frente por {inteiro(ult['margem_votos'])} votos, "
            "e a liderança não mudou mais."
        )
    sem = [u["uf"] for u in G["ufs"] if not u.get("n_viradas")]
    if sem:
        frases.append(f"Em {', '.join(sem)}, quem abriu à frente terminou à frente.")
    return p(" ".join(frases), "verificado") + p(
        "Troca de liderança com menos de 1% das seções é ordem de chegada dos boletins, não mudança "
        "de voto: a primeira seção de uma cidade pesa mais do que pesará no fim.",
        "inferencia",
    )


def nome_bonito_sq(u: dict, sq: str) -> str:
    for c in u["candidatos"]:
        if c["sqcand"] == sq:
            return nome(c)
    return sq


def vao(G: dict) -> str:
    acima = []
    abaixo = []
    for u in G["ufs"]:
        a, _ = par(u)
        quem = "Flávio" if a.get("finalista_comparado") == "flavio" else "Lula"
        item = f"{u['uf']} ({nome(a)} {num(a['pct'], 2)}% contra {quem} {num(a['pct_presidencial_mesmo_lado'], 2)}%)"
        (acima if (a.get("vao_pp") or 0) > 0 else abaixo).append(item)
    return p(
        "Na mesma urna, o eleito ao governo rendeu acima do presidenciável do mesmo lado em "
        + ("; ".join(acima) or "nenhuma UF")
        + "; abaixo em "
        + ("; ".join(abaixo) or "nenhuma UF")
        + ".",
        "verificado",
    ) + nota(
        "juizo",
        f"O vão é {G.get('rotulo_vao', 'teto endereçável')}: mostra quanto voto o nome local tinha "
        "além do presidencial, sem dizer que esse eleitor mudaria de lado. O lado das candidaturas de "
        "centro segue a coligação registrada e as exceções declaradas pela casa, cada uma com a "
        "evidência na ficha.",
    )


def comparacao(G: dict) -> str:
    bn = sorted(
        G["ufs"], key=lambda u: -(u.get("brancos_nulos_gov_menos_pres_pp") or 0)
    )
    u = bn[0]
    if all((x.get("brancos_nulos_gov_menos_pres_pp") or 0) > 0 for x in G["ufs"]):
        frase = (
            "Em todas as UFs, brancos e nulos foram mais altos para governador que para presidente "
            f"na mesma urna; a maior distância foi no {u['uf']}, "
            f"{num(u['brancos_nulos_gov_menos_pres_pp'], 2)} pp."
        )
    else:
        frase = (
            f"Brancos e nulos de governador menos os de presidente: maior no {u['uf']}, "
            f"{num(u['brancos_nulos_gov_menos_pres_pp'], 2)} pp."
        )
    return p(frase, "verificado")


def campo_terceiros(G: dict) -> str:
    itens = []
    for u in sorted(G["ufs"], key=lambda u: u["uf"]):
        ter = u.get("t1_terceiro") or {}
        if ter:
            itens.append(
                f"{u['uf']} {campo_nome(ter.get('campo')).lower()} {num(ter.get('pct'), 1)}%"
            )
    return ", ".join(itens)


def limites_itens(G: dict) -> list[str]:
    return [
        "Campo político é classificação editorial da casa (tucano é centro-esquerda), declarada na ficha.",
        "Trocas de liderança contam versões genuínas consecutivas do arquivo de UF, na ordem de geração do TSE.",
        "O vão compara cargos diferentes na mesma urna: não identifica eleitor que votou cruzado.",
        f"Terceiros colocados do 1º turno, cujo eleitorado se redistribuiu: {campo_terceiros(G)}.",
        G.get("rotulo") or "",
    ]
