"""Hero, quadro das corridas, segundos turnos, fichas, mapa e tabela."""

from __future__ import annotations

from html import escape as esc

from senado_2026.pagina import view as sv
from senado_2026.pagina.comum import (
    COR,
    ROTULO,
    barra,
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
GRUPOS = (
    ("direita", "Direita e centro-direita"),
    ("centro", "Centro"),
    ("esquerda", "Esquerda e centro-esquerda"),
)
CLASSE_ROTULO = {
    "apertada": ("Apertadas", "favorita com menos de 70% de chance"),
    "provavel": ("Prováveis", "favorita entre 70% e 90%"),
    "decidida": ("Decididas", "favorita com 90% ou mais"),
}
fontes = sv.fontes
foco = sv.foco


# ---------------------------------------------------------------- hero


def _ic(v: dict) -> str:
    ic = v.get("ic90")
    return f"IC90: {num(ic[0], 0)} a {num(ic[1], 0)}" if ic else "IC90 indisponível"


def hero_cartoes(data: dict) -> str:
    n = data["nacional"]
    dec = n.get("decididos_1t") or {}
    seg = n.get("segundo_turno") or {}
    topo = (
        '<div class="scoreboard gv-score gv-score-2">'
        '<div class="candidate sn-card gv-card-1t"><span>Decididos no 1º turno</span>'
        f"<b>{num(dec.get('esperado', 0))}<small>estados</small></b>"
        f"<strong>{_ic(dec)} estados</strong>"
        "<p>Candidatura com mais de 50% dos válidos em 04/10</p></div>"
        '<div class="candidate sn-card gv-card-2t"><span>Com 2º turno</span>'
        f"<b>{num(seg.get('esperado', 0))}<small>estados</small></b>"
        f"<strong>{_ic(seg)} estados</strong>"
        f"<p>Disputa decidida em {data_br(data.get('segundo_turno_data'))}</p></div></div>"
    )
    cartoes = []
    for chave, rotulo in GRUPOS:
        v = n.get("por_grupo", {}).get(chave, {})
        cartoes.append(
            f'<div class="candidate sn-card {CARTAO_CLASSE[chave]}">'
            f"<span>{esc(rotulo)}</span>"
            f"<b>{num(v.get('esperado', 0))}<small>governos</small></b>"
            f"<strong>{_ic(v)} governos</strong>"
            f"<p>Maioria dos 27 (14 ou mais) em {pct(v.get('p_maioria_14'))} dos sorteios</p></div>"
        )
    return (
        topo
        + '<div class="scoreboard sn-score gv-score">'
        + "".join(cartoes)
        + "</div>"
    )


# ---------------------------------------------------------------- corridas


def _fav(e: dict) -> dict | None:
    return mapa_mod.favorito(e)


def _par_modal(e: dict) -> dict | None:
    pares = e.get("pares_2t") or []
    return pares[0] if pares else None


def _barra_corrida(e: dict, fav: dict) -> str:
    campo = campo_de(fav.get("campo"))
    p1 = max(0.0, fav.get("p_vence_1t") or 0)
    p2 = max(0.0, fav.get("p_vence_2t") or 0)
    outro = max(0.0, 1 - p1 - p2)
    rotulo = (
        f"{fav.get('nome')}: vence no 1º turno em {pct(p1)}, no 2º turno em {pct(p2)}; "
        f"outro nome vence em {pct(outro)}"
    )
    return (
        f'<div class="gv-stack" role="img" aria-label="{esc(rotulo)}">'
        f'<div class="gv-seg gv-seg-1t sn-bg-{campo}" style="width:{100 * p1:.1f}%"></div>'
        f'<div class="gv-seg gv-seg-2t" style="width:{100 * p2:.1f}%;background:{COR[campo]}"></div>'
        f'<div class="gv-seg gv-seg-outro" style="width:{100 * outro:.1f}%"></div></div>'
    )


def _linha_corrida(uf: str, e: dict) -> str:
    fav = _fav(e)
    if not fav:
        return (
            f'<li class="gv-row gv-row-sem"><a class="gv-uf" href="#estado-{uf}">{uf}</a>'
            f'<span class="gv-nome">{esc(e.get("nome", uf))}: sem pesquisa</span></li>'
        )
    campo = campo_de(fav.get("campo"))
    par = _par_modal(e)
    par_txt = ""
    if par and (e.get("p_segundo_turno") or 0) >= 0.05:
        a, b = par["nomes"]
        pa, pb = par["projecao"][a], par["projecao"][b]
        como = "medido" if par.get("medido") else "estimado"
        par_txt = (
            f'<span class="gv-par">2º turno mais provável ({pct(par["p_par"])}): '
            f"{esc(a)} <b>{num(pa, 0)}</b> × <b>{num(pb, 0)}</b> {esc(b)} "
            f'<i class="gv-tag gv-tag-{como}">{como}</i></span>'
        )
    antiga = (
        ' <i class="gv-tag gv-tag-antiga">pesquisa antiga</i>'
        if e.get("cobertura") == "antiga"
        else ""
    )
    return (
        f'<li class="gv-row" id="corrida-{uf}">'
        f'<a class="gv-uf" href="#estado-{uf}">{uf}</a>'
        f"{foto(fav, 44)}"
        '<div class="gv-cand">'
        f'<span class="gv-nome">{esc(fav.get("nome", ""))}</span>'
        f'<span class="sn-meta">{sigla(fav.get("partido"))} · {ROTULO[campo].lower()} · '
        f"{esc(e.get('nome', uf))}{antiga}</span></div>"
        '<div class="gv-prob">'
        f'<strong class="gv-p">{pct(fav.get("p_eleito"))}</strong>'
        f"{_barra_corrida(e, fav)}"
        f'<span class="sn-meta">1º turno decide: {pct(e.get("p_decide_1t"))} · '
        f'2º turno: {pct(e.get("p_segundo_turno"))}</span></div>'
        f"{par_txt}</li>"
    )


def corridas(data: dict) -> str:
    estados = data["estados"]
    ordem = data["nacional"].get("ranking_apertadas") or sorted(estados)
    blocos = []
    for classe, (rotulo, regra) in CLASSE_ROTULO.items():
        ufs = [u for u in ordem if estados[u].get("classe") == classe]
        if not ufs:
            continue
        linhas = "".join(_linha_corrida(u, estados[u]) for u in ufs)
        blocos.append(
            f'<section class="gv-bloco gv-bloco-{classe}" aria-labelledby="corridas-{classe}">'
            f'<h3 id="corridas-{classe}">{rotulo} <small>{num(len(ufs), 0)} estados · {regra}</small></h3>'
            f'<ol class="gv-board">{linhas}</ol></section>'
        )
    sem = [u for u in sorted(estados) if estados[u].get("cobertura") == "sem_pesquisa"]
    if sem:
        linhas = "".join(_linha_corrida(u, estados[u]) for u in sem)
        blocos.append(
            '<section class="gv-bloco" aria-labelledby="corridas-sem"><h3 id="corridas-sem">'
            f"Sem pesquisa <small>{num(len(sem), 0)} estados</small></h3>"
            f'<ol class="gv-board">{linhas}</ol></section>'
        )
    legenda = (
        '<ul class="gv-legenda" aria-label="Legenda das barras">'
        '<li><span class="gv-sw gv-sw-1t"></span>favorita vence no 1º turno</li>'
        '<li><span class="gv-sw gv-sw-2t"></span>favorita vence no 2º turno</li>'
        '<li><span class="gv-sw gv-sw-outro"></span>outro nome vence</li></ul>'
    )
    return legenda + "".join(blocos)


# --------------------------------------------------------- segundos turnos


def _cartao_par(uf: str, e: dict, par: dict) -> str:
    a, b = par["nomes"]
    pa, pb = par["projecao"][a], par["projecao"][b]
    ca, cb = (campo_de(c) for c in par["campos"])
    fa = {"nome": a, "campo": ca, "foto": par["fotos"][0]}
    fb = {"nome": b, "campo": cb, "foto": par["fotos"][1]}
    ic = par.get("ic90_primeiro_nome") or [None, None]
    if par.get("medido") and par.get("medicao"):
        m = par["medicao"]
        casas = sorted({o["instituto"] for o in m.get("ondas", [])})
        fonte = (
            f"Medido por {esc(', '.join(casas))}: {esc(a)} {num(m['fracao_primeiro_nome'], 1)}% "
            f"× {num(100 - m['fracao_primeiro_nome'], 1)}% {esc(b)} dos válidos entre os dois."
        )
        tag = '<i class="gv-tag gv-tag-medido">medido</i>'
    else:
        fonte = (
            "Nenhum instituto mediu este par: a projeção vem da transferência "
            "declarada por campo, hipótese sem medição."
        )
        tag = '<i class="gv-tag gv-tag-estimado">estimado</i>'
    pv = par["p_vence_dado_par"]
    return (
        f'<li class="gv-par-card" id="par-{uf}">'
        f'<div class="gv-par-head"><a class="gv-uf" href="#estado-{uf}">{uf}</a>'
        f'<span>{esc(e.get("nome", uf))} · 2º turno em {pct(par["p_par"])} dos sorteios</span>{tag}</div>'
        '<div class="gv-par-corpo">'
        f'<div class="gv-par-lado">{foto(fa, 56)}<b>{esc(a)}</b>'
        f'<span class="sn-meta">{sigla(par["partidos"][0])} · {ROTULO[ca].lower()}</span></div>'
        '<div class="gv-par-meio">'
        f'<div class="gv-placar"><b class="gv-c-{ca}">{num(pa, 0)}</b><span>×</span><b class="gv-c-{cb}">{num(pb, 0)}</b></div>'
        f'<div class="gv-duelo" role="img" aria-label="Projeção: {esc(a)} {num(pa, 0)}%, {esc(b)} {num(pb, 0)}%">'
        f'<div class="gv-duelo-a sn-bg-{ca}" style="width:{pa:.1f}%"></div>'
        f'<div class="gv-duelo-b sn-bg-{cb}" style="width:{pb:.1f}%"></div></div>'
        f'<span class="sn-meta">Chance no 2º turno: {esc(a)} {pct(pv[a])} · {esc(b)} {pct(pv[b])}'
        + (
            f" · IC90 de {esc(a)}: {num(ic[0], 0)}% a {num(ic[1], 0)}%"
            if ic[0] is not None
            else ""
        )
        + "</span></div>"
        f'<div class="gv-par-lado gv-par-lado-b">{foto(fb, 56)}<b>{esc(b)}</b>'
        f'<span class="sn-meta">{sigla(par["partidos"][1])} · {ROTULO[cb].lower()}</span></div>'
        "</div>"
        f'<p class="sn-meta gv-par-fonte">{fonte}</p></li>'
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
        return (
            "Sem pesquisa recente. O modelo usa pesquisa antiga com peso fraco e "
            "marca a incerteza como alta."
        )
    return f"Pesquisas com campo a partir de {data_br(janela)}." if janela else ""


def _cand_media(c: dict, e: dict) -> str:
    campo = campo_de(c.get("campo"))
    por_nome = {p.get("nome"): p for p in e.get("probabilidades", [])}
    p = por_nome.get(c.get("nome"), {})
    ic = p.get("ic90_validos")
    extra = f" · IC90 {num(ic[0], 0)}% a {num(ic[1], 0)}%" if ic else ""
    return (
        '<li class="sn-cand sn-cand-small">'
        f"{foto({**c, 'foto': c.get('foto')}, 36)}"
        '<div class="sn-cand-txt">'
        f"<b>{esc(c.get('nome', ''))}</b>"
        f'<span class="sn-meta">{sigla(c.get("partido"))} · {ROTULO[campo].lower()} · '
        f"{num(c.get('validos', 0))}% dos válidos{extra} · eleição {pct(p.get('p_eleito'))}</span></div></li>"
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
        n = f" · n = {num(f['n'], 0)}" if f and f.get("n") else ""
        peso = f" · peso {pct(p['peso'])}" if p.get("peso") is not None else ""
        link = (
            f' · <a href="{esc(f["url"])}" rel="noopener">fonte</a>'
            if f and f.get("url")
            else ""
        )
        itens.append(f"<li>{casa}, campo {campo}{n}{peso}{link}</li>")
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
        pa, pb = par["projecao"][a], par["projecao"][b]
        como = "medido" if par.get("medido") else "estimado"
        pv = par["p_vence_dado_par"]
        itens.append(
            f"<li><b>{esc(a)} {num(pa, 0)} × {num(pb, 0)} {esc(b)}</b> "
            f'<i class="gv-tag gv-tag-{como}">{como}</i><br>'
            f'<span class="sn-meta">par em {pct(par["p_par"])} dos sorteios; chance de {esc(a)} '
            f"no 2º turno {pct(pv[a])}</span></li>"
        )
    return '<ul class="gv-ficha-pares">' + "".join(itens) + "</ul>"


def corpo_ficha(uf: str, e: dict, data: dict, idx: dict) -> str:
    cob = e.get("cobertura")
    cobertura = {
        "recente": "recente",
        "antiga": "antiga",
        "sem_pesquisa": "sem pesquisa",
    }
    partes = [
        f'<p class="sn-aviso sn-cob-{esc(cob or "")}"><b>Cobertura {cobertura.get(cob, esc(cob or ""))}.</b> '
        f"{_cobertura_texto(e, data)}</p>"
    ]
    fav = _fav(e)
    if fav:
        campo = campo_de(fav.get("campo"))
        partes.append(
            '<h4 class="sn-h">Favorita</h4><ol class="sn-cands"><li class="sn-cand">'
            f"{foto(fav, 64)}"
            '<div class="sn-cand-txt">'
            f"<b>{esc(fav.get('nome', ''))}</b>"
            f'<span class="sn-meta">{sigla(fav.get("partido"))} · {ROTULO[campo].lower()}</span>'
            f'<div class="sn-prob">{barra(fav.get("p_eleito"), campo, "Probabilidade de eleição de " + fav.get("nome", ""))}'
            f"<strong>{pct(fav.get('p_eleito'))}</strong></div>"
            f'<span class="sn-meta">vence no 1º turno {pct(fav.get("p_vence_1t"))} · no 2º turno '
            f'{pct(fav.get("p_vence_2t"))} · média das pesquisas {num(fav.get("validos_central", 0))}% dos válidos</span>'
            "</div></li></ol>"
            f'<p class="gv-decisao"><b>1º turno decide:</b> {pct(e.get("p_decide_1t"))} · '
            f'<b>2º turno:</b> {pct(e.get("p_segundo_turno"))}</p>'
        )
        media = e.get("media", [])[:4]
        if media:
            partes.append(
                '<h4 class="sn-h">1º turno, média das pesquisas</h4><ul class="sn-cands">'
                + "".join(_cand_media(c, e) for c in media)
                + "</ul>"
                + f'<p class="sn-meta">Indecisos {num(e.get("indecisos", 0))}% · branco e nulo '
                f'{num(e.get("branco_nulo", 0))}% dos entrevistados.</p>'
            )
        pares = _pares_ficha(e)
        if pares:
            partes.append('<h4 class="sn-h">Pares de 2º turno</h4>' + pares)
    partes.append('<h4 class="sn-h">Pesquisas usadas</h4>' + _pesquisas(e, idx))
    if e.get("incerteza"):
        partes.append(f'<p class="sn-meta">Incerteza: {esc(e["incerteza"])}.</p>')
    for nota in e.get("notas", []):
        partes.append(f'<p class="sn-meta">{datas_br(nota)}</p>')
    return "".join(partes)


def _resumo(e: dict) -> str:
    fav = _fav(e)
    if not fav:
        return "sem pesquisa"
    return f"{esc(fav.get('nome', ''))} {pct(fav.get('p_eleito'))} · 2º turno {pct(e.get('p_segundo_turno'))}"


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
        '<h3 id="sn-map-title" class="sn-sr">Campo da candidatura favorita, por estado</h3>'
        f"{mapa_mod.svg(estados)}"
        "<figcaption>Malha oficial do IBGE. A cor mostra o campo da candidatura com maior "
        "chance de eleição; listras marcam o estado onde o 2º turno é mais provável que a "
        "decisão no 1º. Clique ou toque num estado para ver a ficha.</figcaption></figure>"
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
            proj = f"{num(par['projecao'][a], 0)} × {num(par['projecao'][b], 0)}" + (
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
                esc(e.get("classe") or "–"),
                cob.get(e.get("cobertura"), esc(e.get("cobertura") or "")),
                _casas(e, idx),
            ]
        )
    headers = [
        "UF",
        "Favorita",
        "p eleição",
        "p 1º turno decide",
        "p 2º turno",
        "Par mais provável",
        "Projeção do par",
        "Disputa",
        "Cobertura",
        "Pesquisas",
    ]
    return table(
        headers,
        rows,
        "Favorita, probabilidades e par de 2º turno por estado",
        {2, 3, 4, 6},
        sortable=True,
    )
