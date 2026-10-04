"""Hero, resumo em 30 segundos, corridas, segundos turnos, fichas, mapa e tabela.

Regra desta camada: cada estado recebe uma frase em português corrente, letra
grande e um só desenho por ideia. Os números técnicos ficam nas fichas e na
tabela; o capítulo "Como lemos" explica em linguagem de aula.
"""

from __future__ import annotations

from html import escape as esc

from senado_2026.pagina import view as sv
from senado_2026.pagina.comum import (
    COR,
    ROTULO,
    campo_de,
    casa_do_arquivo,
    data_br,
    datas_br,
    foto,
    indice_fontes,
    num,
    pct,
    sigla,
    table,
)

from . import mapa as mapa_mod

CARTAO_CLASSE = {"direita": "dir", "centro": "cen", "esquerda": "esq"}
# Corte de "praticamente decidido", igual ao de saida.CLASSES.
DECIDIDA = 0.89
GRUPOS = (
    ("direita", "Direita e centro-direita"),
    ("centro", "Centro"),
    ("esquerda", "Esquerda e centro-esquerda"),
)
CLASSES = (
    ("apertada", "Ninguém sabe", "quem lidera tem menos de 70% de chance"),
    ("provavel", "Há um nome na frente, mas está aberto", "entre 70% e 89% de chance"),
    ("decidida", "Praticamente decidido", "89% de chance ou mais"),
)
fontes = sv.fontes
foco = sv.foco


def _fav(e: dict) -> dict | None:
    return mapa_mod.favorito(e)


def _segundo(e: dict) -> dict | None:
    probs = e.get("probabilidades") or []
    return probs[1] if len(probs) > 1 else None


def _par_modal(e: dict) -> dict | None:
    pares = e.get("pares_2t") or []
    return pares[0] if pares else None


def placar(par: dict) -> tuple[float, float]:
    """Placar entre os dois nomes: o medido pelos institutos quando existe,
    senão a projeção por transferência."""
    a, b = par["nomes"]
    if par.get("medido") and par.get("medicao"):
        pa = par["medicao"]["fracao_primeiro_nome"]
        return pa, 100 - pa
    return par["projecao"][a], par["projecao"][b]


def _chances(p: float | None) -> str:
    """'9 chances em 10', '2 em 3', 'cara ou coroa': a probabilidade em palavras."""
    if p is None:
        return "sem estimativa"
    if p >= 0.97:
        return "quase certo"
    if p >= 0.85:
        return "9 chances em 10"
    if p >= 0.72:
        return "3 chances em 4"
    if p >= 0.6:
        return "2 chances em 3"
    if p >= 0.55:
        return "pouco mais que cara ou coroa"
    return "cara ou coroa"


def lidera(c: dict) -> str:
    """'é o favorito' ou 'é a favorita' pelo gênero declarado no TSE; sem o
    registro, 'tem a candidatura favorita', que não presume nada."""
    g = (c.get("genero") or "").upper()
    if g.startswith("FEM"):
        return "é a favorita"
    if g.startswith("MASC"):
        return "é o favorito"
    return "tem a candidatura favorita"


def veredito(e: dict) -> tuple[str, str]:
    """(classe css, texto curto) sobre quando a disputa termina."""
    p1 = e.get("p_decide_1t") or 0
    if p1 >= 0.85:
        return "1t", "Termina no 1º turno"
    if p1 >= 0.5:
        return "1t", f"Deve terminar no 1º turno ({pct(p1)})"
    if p1 >= 0.15:
        return "2t", f"Deve ir ao 2º turno ({pct(1 - p1)})"
    return "2t", "Vai ao 2º turno"


def frase(e: dict) -> str:
    """Uma frase por estado, sem jargão."""
    fav = _fav(e)
    if not fav:
        return "Nenhuma pesquisa registrada: a página não aponta nome."
    seg = _segundo(e)
    p = fav.get("p_eleito") or 0
    nome = esc(fav.get("nome", ""))
    if p >= DECIDIDA:
        return f"{nome} tem {pct(p)} de chance de governar o estado: {_chances(p)}."
    if p >= 0.7:
        outro = (
            f" {esc(seg.get('nome', ''))} tem {pct(seg.get('p_eleito'))}."
            if seg
            else ""
        )
        return f"{nome} {lidera(fav)}, com {pct(p)}, mas a disputa ainda está aberta.{outro}"
    if seg:
        return (
            f"Empate: {nome} tem {pct(p)} e {esc(seg.get('nome', ''))} tem "
            f"{pct(seg.get('p_eleito'))}. É {_chances(p)}."
        )
    return f"{nome} lidera com {pct(p)} de chance."


# ---------------------------------------------------------------- hero


def _tile(uf: str, e: dict) -> str:
    fav = _fav(e)
    if not fav:
        return (
            f'<a class="gv-tile gv-tile-sem" href="#estado-{uf}" aria-label="{esc(e.get("nome", uf))}: sem pesquisa">'
            f"<b>{uf}</b><span>?</span></a>"
        )
    campo = campo_de(fav.get("campo"))
    cls, _ = veredito(e)
    rotulo = f"{e.get('nome', uf)}: {fav.get('nome')} {pct(fav.get('p_eleito'))}, {veredito(e)[1].lower()}"
    return (
        f'<a class="gv-tile gv-tile-{cls}" style="--c:{COR[campo]}" href="#estado-{uf}" '
        f'aria-label="{esc(rotulo)}" title="{esc(rotulo)}">'
        f"<b>{uf}</b>{foto(fav, 40)}<span>{pct(fav.get('p_eleito'))}</span></a>"
    )


def hero_cartoes(data: dict) -> str:
    n = data["nacional"]
    dec = n.get("decididos_1t") or {}
    seg = n.get("segundo_turno") or {}
    estados = data["estados"]
    ordem = n.get("ranking_apertadas") or sorted(estados)
    # Do mais decidido ao mais incerto, da esquerda para a direita.
    tiles = "".join(_tile(uf, estados[uf]) for uf in reversed(ordem))
    tiles += "".join(
        _tile(uf, estados[uf]) for uf in sorted(estados) if uf not in ordem
    )
    return (
        '<div class="gv-hero-nums">'
        '<div class="gv-hero-num"><b>' + num(dec.get("esperado", 0), 0) + "</b>"
        "<span>estados devem decidir o governo já amanhã, no 1º turno</span></div>"
        '<div class="gv-hero-num gv-hero-num-2t"><b>'
        + num(seg.get("esperado", 0), 0)
        + "</b>"
        f"<span>estados devem ir ao 2º turno, em {data_br(data.get('segundo_turno_data'))}</span></div>"
        "</div>"
        '<div class="gv-tiles-wrap"><p class="gv-tiles-cap">Os 27 estados, do mais decidido ao mais incerto. '
        "A cor é o campo de quem lidera, o número é a chance de governar, e as listras avisam que o 2º turno é mais provável.</p>"
        f'<div class="gv-tiles">{tiles}</div></div>'
    )


# ---------------------------------------------------------------- 30 segundos


def _lista_ufs(ufs: list[str], estados: dict) -> str:
    return ", ".join(
        f'<a href="#estado-{u}">{esc(estados[u].get("nome", u))}</a>' for u in ufs
    )


def resumo_30s(data: dict) -> str:
    estados = data["estados"]
    n = data["nacional"]
    classes = n.get("por_classe") or {}
    decididos = classes.get("decidida") or []
    abertos = classes.get("provavel") or []
    empates = classes.get("apertada") or []
    g = n.get("por_grupo", {})
    itens = []
    if decididos:
        itens.append(
            f"<li><b>Onde já dá para saber.</b> Em {num(len(decididos), 0)} estados quem lidera tem "
            f"89% de chance ou mais: {_lista_ufs(decididos, estados)}.</li>"
        )
    if empates:
        itens.append(
            f"<li><b>Onde ninguém sabe.</b> Em {num(len(empates), 0)} estados a disputa é cara ou "
            f"coroa, ou perto disso: {_lista_ufs(empates, estados)}.</li>"
        )
    if abertos:
        itens.append(
            f"<li><b>Onde há um nome na frente, mas não garantia.</b> {_lista_ufs(abertos, estados)}.</li>"
        )
    if g.get("direita") and g.get("esquerda"):
        itens.append(
            "<li><b>O saldo do país.</b> Se tudo sair como as pesquisas apontam, a direita e a "
            f"centro-direita ficam com cerca de {num(g['direita']['esperado'], 0)} governos, o centro com "
            f"{num(g['centro']['esperado'], 0)} e a esquerda e centro-esquerda com "
            f"{num(g['esquerda']['esperado'], 0)}.</li>"
        )
    return '<ul class="gv-30s">' + "".join(itens) + "</ul>"


# ---------------------------------------------------------------- corridas


def _card_corrida(uf: str, e: dict) -> str:
    fav = _fav(e)
    if not fav:
        return (
            f'<li class="gv-race gv-race-sem" id="corrida-{uf}"><div class="gv-race-head">'
            f'<a class="gv-uf" href="#estado-{uf}">{uf}</a><span class="gv-estado">{esc(e.get("nome", uf))}</span></div>'
            f'<p class="gv-frase">{frase(e)}</p></li>'
        )
    campo = campo_de(fav.get("campo"))
    seg = _segundo(e)
    cls, ver = veredito(e)
    par = _par_modal(e)
    duelo = ""
    if par and cls == "2t":
        a, b = par["nomes"]
        pa, pb = placar(par)
        como = "medido pelos institutos" if par.get("medido") else "estimado"
        duelo = (
            f'<p class="gv-duelo-txt">No 2º turno mais provável, {esc(a)} <b>{num(pa, 0)}</b> × '
            f"<b>{num(pb, 0)}</b> {esc(b)} <small>({como})</small></p>"
        )
    segundo = ""
    if seg and (seg.get("p_eleito") or 0) >= 0.03:
        segundo = (
            f'<div class="gv-race-rival">{foto(seg, 40)}<span><b>{esc(seg.get("nome", ""))}</b>'
            f'<br>{pct(seg.get("p_eleito"))}</span></div>'
        )
    antiga = (
        '<span class="gv-chip gv-chip-antiga">pesquisa antiga</span>'
        if e.get("cobertura") == "antiga"
        else ""
    )
    p = fav.get("p_eleito") or 0
    return (
        f'<li class="gv-race" id="corrida-{uf}" style="--c:{COR[campo]}">'
        '<div class="gv-race-head">'
        f'<a class="gv-uf" href="#estado-{uf}">{uf}</a><span class="gv-estado">{esc(e.get("nome", uf))}</span>'
        f'<span class="gv-chip gv-chip-{cls}">{esc(ver)}</span>{antiga}</div>'
        '<div class="gv-race-body">'
        f'<div class="gv-race-fav">{foto(fav, 64)}<div><b class="gv-race-nome">{esc(fav.get("nome", ""))}</b>'
        f'<span class="gv-race-meta">{sigla(fav.get("partido"))} · {ROTULO[campo].lower()}</span></div></div>'
        f'<div class="gv-race-p"><b>{pct(p)}</b><span>de chance de governar</span>'
        f'<div class="gv-bar" role="img" aria-label="Chance de eleição de {esc(fav.get("nome", ""))}: {pct(p)}">'
        f'<div class="gv-bar-fill" style="width:{100 * p:.1f}%"></div></div></div>'
        f"{segundo}</div>"
        f'<p class="gv-frase">{frase(e)}</p>{duelo}</li>'
    )


def corridas(data: dict) -> str:
    estados = data["estados"]
    ordem = data["nacional"].get("ranking_apertadas") or sorted(estados)
    blocos = []
    for classe, rotulo, regra in CLASSES:
        ufs = [u for u in ordem if estados[u].get("classe") == classe]
        if not ufs:
            continue
        cards = "".join(_card_corrida(u, estados[u]) for u in ufs)
        blocos.append(
            f'<section class="gv-bloco gv-bloco-{classe}" aria-labelledby="corridas-{classe}">'
            f'<h3 id="corridas-{classe}">{rotulo} <small>{num(len(ufs), 0)} estados · {regra}</small></h3>'
            f'<ol class="gv-races">{cards}</ol></section>'
        )
    sem = [u for u in sorted(estados) if estados[u].get("cobertura") == "sem_pesquisa"]
    if sem:
        cards = "".join(_card_corrida(u, estados[u]) for u in sem)
        blocos.append(
            '<section class="gv-bloco" aria-labelledby="corridas-sem"><h3 id="corridas-sem">'
            f'Sem pesquisa <small>{num(len(sem), 0)} estados</small></h3><ol class="gv-races">{cards}</ol></section>'
        )
    return "".join(blocos)


# --------------------------------------------------------- segundos turnos


def _cartao_par(uf: str, e: dict, par: dict) -> str:
    a, b = par["nomes"]
    pa, pb = placar(par)
    ca, cb = (campo_de(c) for c in par["campos"])
    fa = {"nome": a, "campo": ca, "foto": par["fotos"][0]}
    fb = {"nome": b, "campo": cb, "foto": par["fotos"][1]}
    pv = par["p_vence_dado_par"]
    if par.get("medido") and par.get("medicao"):
        casas = sorted({o["instituto"] for o in par["medicao"].get("ondas", [])})
        fonte = f"Placar medido por {esc(', '.join(casas))}."
        tag = '<span class="gv-chip gv-chip-medido">medido</span>'
    else:
        fonte = "Nenhum instituto mediu este par: o placar é uma estimativa da casa."
        tag = '<span class="gv-chip gv-chip-estimado">estimado</span>'
    lider, p_lider = (a, pv[a]) if pv[a] >= pv[b] else (b, pv[b])
    return (
        f'<li class="gv-par-card" id="par-{uf}">'
        f'<div class="gv-par-head"><a class="gv-uf" href="#estado-{uf}">{uf}</a>'
        f'<span class="gv-estado">{esc(e.get("nome", uf))}</span>'
        f'<span class="gv-chip gv-chip-2t">2º turno em {pct(par["p_par"])} das simulações</span>{tag}</div>'
        '<div class="gv-par-corpo">'
        f'<div class="gv-par-lado">{foto(fa, 80)}<b>{esc(a)}</b><span class="gv-race-meta">{sigla(par["partidos"][0])}</span></div>'
        '<div class="gv-par-meio">'
        f'<div class="gv-placar"><b class="gv-c-{ca}">{num(pa, 0)}</b><span>×</span><b class="gv-c-{cb}">{num(pb, 0)}</b></div>'
        f'<div class="gv-duelo" role="img" aria-label="Placar projetado: {esc(a)} {num(pa, 0)}%, {esc(b)} {num(pb, 0)}%">'
        f'<div class="gv-duelo-a sn-bg-{ca}" style="width:{pa:.1f}%"></div>'
        f'<div class="gv-duelo-b sn-bg-{cb}" style="width:{pb:.1f}%"></div></div>'
        f'<p class="gv-par-frase">{esc(lider)} venceria esse 2º turno em {pct(p_lider)} das vezes: {_chances(p_lider)}.</p>'
        "</div>"
        f'<div class="gv-par-lado gv-par-lado-b">{foto(fb, 80)}<b>{esc(b)}</b><span class="gv-race-meta">{sigla(par["partidos"][1])}</span></div>'
        "</div>"
        f'<p class="gv-par-fonte">{fonte}</p></li>'
    )


def segundos_turnos(data: dict, minimo: float = 0.2) -> str:
    estados = data["estados"]
    ordem = sorted(
        (u for u in estados if (estados[u].get("p_segundo_turno") or 0) >= minimo),
        key=lambda u: -(estados[u].get("p_segundo_turno") or 0),
    )
    cards = []
    for u in ordem:
        par = _par_modal(estados[u])
        if par:
            cards.append(_cartao_par(u, estados[u], par))
    if not cards:
        return "<p>Nenhum estado tem 2º turno provável.</p>"
    return '<ol class="gv-pares">' + "".join(cards) + "</ol>"


# ---------------------------------------------------------------- fichas


def _cobertura_texto(e: dict, data: dict) -> str:
    cob = e.get("cobertura")
    janela = data.get("parametros", {}).get("janela_campo_minimo")
    if cob == "sem_pesquisa":
        return "Nenhuma pesquisa de governador registrada para este estado."
    if cob == "antiga":
        return "Sem pesquisa recente: a conta usa pesquisa antiga com peso fraco, e a incerteza é alta."
    return f"Pesquisas com campo a partir de {data_br(janela)}." if janela else ""


def _cand_media(c: dict, e: dict) -> str:
    campo = campo_de(c.get("campo"))
    por_nome = {p.get("nome"): p for p in e.get("probabilidades", [])}
    p = por_nome.get(c.get("nome"), {})
    return (
        '<li class="sn-cand sn-cand-small">'
        f"{foto(c, 40)}"
        '<div class="sn-cand-txt">'
        f"<b>{esc(c.get('nome', ''))}</b>"
        f'<span class="sn-meta">{sigla(c.get("partido"))} · {ROTULO[campo].lower()} · '
        f"{num(c.get('validos', 0), 0)}% dos votos válidos nas pesquisas · chance de governar {pct(p.get('p_eleito'))}</span></div></li>"
    )


def _pesquisas(e: dict, idx: dict) -> str:
    itens = []
    for p in e.get("pesquisas_usadas", []):
        f = idx.get(p.get("arquivo"))
        casa = esc(casa_do_arquivo(p.get("arquivo", ""), f))
        campo = (
            datas_br(f.get("campo"))
            if f and f.get("campo")
            else data_br(p.get("campo_fim"))
        )
        n = f" · {num(f['n'], 0)} entrevistas" if f and f.get("n") else ""
        link = (
            f' · <a href="{esc(f["url"])}" rel="noopener">fonte</a>'
            if f and f.get("url")
            else ""
        )
        itens.append(f"<li>{casa}, {campo}{n}{link}</li>")
    if not itens:
        return '<p class="sn-meta">Nenhuma pesquisa usada.</p>'
    return '<ul class="sn-pesq">' + "".join(itens) + "</ul>"


def _pares_ficha(e: dict) -> str:
    pares = e.get("pares_2t") or []
    if not pares:
        return ""
    itens = []
    for par in pares[:3]:
        a, b = par["nomes"]
        pa, pb = placar(par)
        como = "medido" if par.get("medido") else "estimado"
        pv = par["p_vence_dado_par"]
        itens.append(
            f"<li><b>{esc(a)} {num(pa, 0)} × {num(pb, 0)} {esc(b)}</b> "
            f'<span class="gv-chip gv-chip-{como}">{como}</span><br>'
            f'<span class="sn-meta">esse par aparece em {pct(par["p_par"])} das simulações; {esc(a)} venceria '
            f"em {pct(pv[a])} delas</span></li>"
        )
    return '<ul class="gv-ficha-pares">' + "".join(itens) + "</ul>"


def corpo_ficha(uf: str, e: dict, data: dict, idx: dict) -> str:
    cob = e.get("cobertura")
    cobertura = {
        "recente": "recente",
        "antiga": "antiga",
        "sem_pesquisa": "sem pesquisa",
    }
    partes = [f'<p class="gv-frase gv-frase-ficha">{frase(e)}</p>']
    fav = _fav(e)
    if fav:
        campo = campo_de(fav.get("campo"))
        _, ver = veredito(e)
        partes.append(
            '<div class="gv-ficha-fav">'
            f"{foto(fav, 72)}"
            f'<div><b class="gv-race-nome">{esc(fav.get("nome", ""))}</b>'
            f'<span class="gv-race-meta">{sigla(fav.get("partido"))} · {ROTULO[campo].lower()}</span>'
            f'<div class="gv-bar" role="img" aria-label="Chance de eleição de {esc(fav.get("nome", ""))}: {pct(fav.get("p_eleito"))}">'
            f'<div class="gv-bar-fill" style="width:{100 * (fav.get("p_eleito") or 0):.1f}%;background:{COR[campo]}"></div></div>'
            f'<span class="sn-meta">{pct(fav.get("p_eleito"))} de chance: vence já no 1º turno em {pct(fav.get("p_vence_1t"))} '
            f'das simulações e no 2º turno em {pct(fav.get("p_vence_2t"))}</span></div></div>'
            f'<p class="gv-decisao"><span class="gv-chip gv-chip-{veredito(e)[0]}">{esc(ver)}</span> '
            f'1º turno decide em {pct(e.get("p_decide_1t"))} das simulações; 2º turno em {pct(e.get("p_segundo_turno"))}.</p>'
        )
        media = e.get("media", [])[:4]
        if media:
            partes.append(
                '<h4 class="sn-h">O que as pesquisas dizem do 1º turno</h4><ul class="sn-cands">'
                + "".join(_cand_media(c, e) for c in media)
                + "</ul>"
                + f'<p class="sn-meta">Indecisos {num(e.get("indecisos", 0), 0)}% e branco ou nulo '
                f'{num(e.get("branco_nulo", 0), 0)}% dos entrevistados.</p>'
            )
        pares = _pares_ficha(e)
        if pares:
            partes.append('<h4 class="sn-h">Se houver 2º turno</h4>' + pares)
    partes.append(
        f'<h4 class="sn-h">Pesquisas usadas</h4><p class="sn-meta"><b>Cobertura {cobertura.get(cob, esc(cob or ""))}.</b> '
        f"{_cobertura_texto(e, data)}</p>" + _pesquisas(e, idx)
    )
    notas = e.get("notas", [])
    if notas:
        partes.append(
            '<details class="gv-tec"><summary>Notas técnicas</summary>'
            + "".join(f'<p class="sn-meta">{datas_br(n)}</p>' for n in notas)
            + "</details>"
        )
    return "".join(partes)


def _resumo(e: dict) -> str:
    fav = _fav(e)
    if not fav:
        return "sem pesquisa"
    return f"{esc(fav.get('nome', ''))} {pct(fav.get('p_eleito'))} · {veredito(e)[1].lower()}"


def fichas(data: dict) -> str:
    idx = indice_fontes(data)
    aberto = foco(data)
    out = []
    for uf in sorted(data["estados"], key=lambda u: data["estados"][u].get("nome", u)):
        e = data["estados"][uf]
        out.append(
            f'<details class="sn-ficha" id="estado-{uf}" data-uf="{uf}"'
            f'{" open" if uf == aberto else ""}>'
            f"<summary><b>{uf}</b><span>{esc(e.get('nome', uf))}</span>"
            f"<small>{_resumo(e)}</small></summary>"
            f'<div class="sn-ficha-corpo">{corpo_ficha(uf, e, data, idx)}</div></details>'
        )
    return '<div class="sn-fichas">' + "".join(out) + "</div>"


def mapa_secao(data: dict) -> str:
    estados = data["estados"]
    idx = indice_fontes(data)
    uf = foco(data)
    e = estados[uf]
    return (
        '<div class="sn-mapa" id="sn-mapa">'
        '<figure class="sn-map-fig">'
        '<h3 id="sn-map-title" class="sn-sr">Campo de quem lidera, por estado</h3>'
        f"{mapa_mod.svg(estados)}"
        "<figcaption>Clique ou toque num estado para ver a ficha. A cor é o campo de quem lidera; "
        "listras marcam onde o 2º turno é mais provável que a decisão no 1º.</figcaption></figure>"
        '<aside class="sn-painel" id="sn-painel" aria-live="polite" aria-label="Ficha do estado selecionado">'
        f'<h3 id="sn-painel-titulo">{esc(e.get("nome", uf))} ({uf})</h3>'
        f'<div id="sn-painel-corpo">{corpo_ficha(uf, e, data, idx)}</div></aside>'
        f"{mapa_mod.legenda()}</div>"
    )


# ---------------------------------------------------------------- tabela


def _casas(e: dict, idx: dict) -> str:
    casas = []
    for p in e.get("pesquisas_usadas", []):
        casa = casa_do_arquivo(p.get("arquivo", ""), idx.get(p.get("arquivo")))
        if casa not in casas:
            casas.append(casa)
    fim = max(
        (p.get("campo_fim") or "" for p in e.get("pesquisas_usadas", [])), default=""
    )
    if not casas:
        return "nenhuma"
    return esc(", ".join(casas)) + (f" · até {data_br(fim)}" if fim else "")


def tabela(data: dict) -> str:
    idx = indice_fontes(data)
    rows = []
    for uf in sorted(data["estados"]):
        e = data["estados"][uf]
        fav = _fav(e)
        par = _par_modal(e)
        if fav:
            nome = f"{esc(fav.get('nome', ''))} ({sigla(fav.get('partido'))})"
            p_el, p1, p2 = (
                pct(fav.get("p_eleito")),
                pct(e.get("p_decide_1t")),
                pct(e.get("p_segundo_turno")),
            )
        else:
            nome, p_el, p1, p2 = "–", "–", "–", "–"
        if par and fav:
            a, b = par["nomes"]
            par_txt = f"{esc(a)} × {esc(b)}"
            pa, pb = placar(par)
            proj = f"{num(pa, 0)} × {num(pb, 0)}" + (
                " (medido)" if par.get("medido") else " (estimado)"
            )
        else:
            par_txt, proj = "–", "–"
        cob = {"recente": "recente", "antiga": "antiga", "sem_pesquisa": "sem pesquisa"}
        rows.append(
            [
                f'<a href="#estado-{uf}"><b>{uf}</b></a>',
                nome,
                p_el,
                p1,
                p2,
                par_txt,
                proj,
                esc(
                    {
                        "apertada": "aberta",
                        "provavel": "um nome na frente",
                        "decidida": "decidida",
                    }.get(e.get("classe") or "", "–")
                ),
                cob.get(e.get("cobertura"), esc(e.get("cobertura") or "")),
                _casas(e, idx),
            ]
        )
    headers = [
        "UF",
        "Quem lidera",
        "Chance de governar",
        "1º turno decide",
        "2º turno",
        "Par mais provável",
        "Placar do par",
        "Disputa",
        "Cobertura",
        "Pesquisas",
    ]
    return table(
        headers,
        rows,
        "Quem lidera, probabilidades e par de 2º turno por estado",
        {2, 3, 4, 6},
        sortable=True,
    )
