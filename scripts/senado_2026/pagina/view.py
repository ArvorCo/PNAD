"""Hero, fichas estaduais, tabela das 27 UFs e fontes."""

from __future__ import annotations

from html import escape as esc

from . import alertas as al
from . import mapa as mapa_mod
from .comum import (
    GRUPOS,
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

CARTAO_CLASSE = {"direita": "dir", "centro": "cen", "esquerda": "esq"}


# ---------------------------------------------------------------- hero


def _grupo(por_campo: dict, por_grupo: dict, chave: str, componentes: tuple):
    if chave in por_grupo:
        return [(chave, por_grupo[chave])], True
    itens = [(k, por_campo[k]) for k in componentes if k in por_campo]
    return itens, len(itens) == 1


def hero_cartoes(data: dict) -> str:
    s27 = data["senado_2027"]
    por_campo, por_grupo = s27.get("por_campo", {}), s27.get("por_grupo", {})
    cartoes = []
    for chave, rotulo, comps in GRUPOS:
        itens, exato = _grupo(por_campo, por_grupo, chave, comps)
        esperado = sum(v.get("esperado", 0) for _, v in itens)
        continuam = sum(v.get("continuam", 0) for _, v in itens)
        novos = sum(v.get("novos_esperado", 0) for _, v in itens)
        if exato and itens and itens[0][1].get("ic90"):
            lo, hi = itens[0][1]["ic90"]
            ic = f"IC90: {num(lo, 0)} a {num(hi, 0)} assentos"
        else:
            partes = [
                f"{ROTULO.get(k, k)} {num(v['ic90'][0], 0)} a {num(v['ic90'][1], 0)}"
                for k, v in itens
                if v.get("ic90")
            ]
            ic = (
                "IC90 por campo: " + "; ".join(partes)
                if partes
                else "IC90 indisponível"
            )
        cartoes.append(
            f'<div class="candidate sn-card {CARTAO_CLASSE[chave]}">'
            f"<span>{esc(rotulo)}</span>"
            f"<b>{num(esperado)}<small>assentos</small></b>"
            f"<strong>{ic}</strong>"
            f"<p>{num(continuam, 0)} continuam · {num(novos)} novos esperados</p></div>"
        )
    extra = ""
    indef = por_grupo.get("indefinido") or por_campo.get("indefinido") or {}
    if indef.get("esperado", 0) > 0.05:
        extra = (
            '<p class="hero-caption">Sem campo definido: '
            f"{num(indef['esperado'])} assentos esperados.</p>"
        )
    return '<div class="scoreboard sn-score">' + "".join(cartoes) + "</div>" + extra


# ---------------------------------------------------------------- fichas


def _cobertura_texto(e: dict, data: dict) -> str:
    cob = e.get("cobertura")
    janela = data.get("parametros", {}).get("janela_campo_minimo")
    if cob == "sem_pesquisa":
        return (
            "Nenhuma pesquisa de Senado registrada para este estado. "
            "A página não indica nomes."
        )
    if cob == "antiga":
        return (
            "Sem pesquisa recente. O modelo usa pesquisa antiga com peso fraco e "
            "marca a incerteza como alta."
        )
    return (
        f"Pesquisas com campo a partir de {data_br(janela)}."
        if janela
        else "Pesquisas recentes."
    )


def _media(e: dict, nome: str) -> dict:
    for m in e.get("media", []):
        if m.get("nome") == nome:
            return m
    return {}


def _cand_grande(c: dict, e: dict) -> str:
    campo = campo_de(c.get("campo"))
    m = _media(e, c.get("nome"))
    extra = []
    if m.get("valor") is not None:
        extra.append(f"média das pesquisas {num(m['valor'])}% dos entrevistados")
    ic = c.get("ic90_validos")
    if ic:
        extra.append(f"IC90 dos válidos {num(ic[0])}% a {num(ic[1])}%")
    return (
        '<li class="sn-cand">'
        f"{foto(c, 64)}"
        '<div class="sn-cand-txt">'
        f"<b>{esc(c.get('nome', ''))}</b>{al.chip_candidatura(e, c.get('nome'))}"
        f'<span class="sn-meta">{sigla(c.get("partido"))} · {ROTULO[campo].lower()}</span>'
        f'<div class="sn-prob">{barra(c.get("p_eleito"), campo, "Probabilidade de eleição de " + c.get("nome", ""))}'
        f"<strong>{pct(c.get('p_eleito'))}</strong></div>"
        f'<span class="sn-meta">{"; ".join(extra)}</span>'
        "</div></li>"
    )


def _cand_pequeno(c: dict, e: dict) -> str:
    campo = campo_de(c.get("campo"))
    return (
        '<li class="sn-cand sn-cand-small">'
        f"{foto(c, 36)}"
        '<div class="sn-cand-txt">'
        f"<b>{esc(c.get('nome', ''))}</b>{al.chip_candidatura(e, c.get('nome'))}"
        f'<span class="sn-meta">{sigla(c.get("partido"))} · {ROTULO[campo].lower()} · '
        f"eleição {pct(c.get('p_eleito'))}</span></div></li>"
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


def corpo_ficha(uf: str, e: dict, data: dict, idx: dict) -> str:
    cob = e.get("cobertura")
    cobertura = {
        "recente": "recente",
        "antiga": "antiga",
        "sem_pesquisa": "sem pesquisa",
    }.get(cob, esc(cob or ""))
    partes = [
        al.bloco_alerta(e),
        f'<p class="sn-aviso sn-cob-{esc(cob or "")}"><b>Cobertura {cobertura}.</b> '
        f"{_cobertura_texto(e, data)}</p>",
    ]
    cands = e.get("probabilidades", [])
    if cob != "sem_pesquisa" and cands:
        eleitos = mapa_mod.eleitos(e)
        nomes = {c.get("nome") for c in eleitos}
        resto = sorted(
            (c for c in cands if c.get("nome") not in nomes),
            key=lambda c: c.get("p_eleito") or 0,
            reverse=True,
        )
        partes.append(
            '<h4 class="sn-h">Os dois eleitos prováveis</h4><ol class="sn-cands">'
            + "".join(_cand_grande(c, e) for c in eleitos)
            + "</ol>"
        )
        if e.get("p_dupla_mais_provavel") is not None:
            partes.append(
                f'<p class="sn-dupla">Chance de essa dupla ser a eleita: '
                f"<strong>{pct(e['p_dupla_mais_provavel'])}</strong>.</p>"
            )
        if resto[:2]:
            partes.append(
                '<h4 class="sn-h">Terceiro e quarto colocados</h4><ul class="sn-cands">'
                + "".join(_cand_pequeno(c, e) for c in resto[:2])
                + "</ul>"
            )
    partes.append(al.cenarios_ficha(e))
    partes.append('<h4 class="sn-h">Pesquisas usadas</h4>' + _pesquisas(e, idx))
    if e.get("incerteza"):
        partes.append(f'<p class="sn-meta">Incerteza: {esc(e["incerteza"])}.</p>')
    for nota in e.get("notas", []):
        partes.append(f'<p class="sn-meta">{datas_br(nota)}</p>')
    return "".join(partes)


def _resumo(e: dict) -> str:
    if e.get("cobertura") == "sem_pesquisa":
        return "sem pesquisa"
    nomes = [c.get("nome", "") for c in mapa_mod.eleitos(e)]
    return " e ".join(esc(n) for n in nomes) if nomes else "sem nomes"


def foco(data: dict) -> str:
    """UF aberta ao carregar: a de maior eleitorado entre as que têm pesquisa."""
    com = {
        u: e for u, e in data["estados"].items() if e.get("cobertura") != "sem_pesquisa"
    }
    base = com or data["estados"]
    return max(base, key=lambda u: base[u].get("eleitorado") or 0)


def fichas(data: dict) -> str:
    idx = indice_fontes(data)
    aberto = foco(data)
    out = []
    for uf in sorted(data["estados"], key=lambda u: data["estados"][u].get("nome", u)):
        e = data["estados"][uf]
        out.append(
            f'<details class="sn-ficha" id="estado-{uf}" data-uf="{uf}"'
            f'{" open" if uf == aberto else ""}>'
            f"<summary><b>{uf}</b><span>{esc(e.get('nome', uf))}{al.chip_estado(e)}</span>"
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
        '<h3 id="sn-map-title" class="sn-sr">Campo dos dois eleitos prováveis, por estado</h3>'
        f"{mapa_mod.svg(estados)}"
        "<figcaption>Malha oficial do IBGE. Cada estado elege duas vagas; a cor "
        "mostra os dois nomes mais prováveis, não o voto. Clique ou toque num "
        "estado para ver a ficha.</figcaption></figure>"
        '<aside class="sn-painel" id="sn-painel" aria-live="polite" aria-label="Ficha do estado selecionado">'
        f'<h3 id="sn-painel-titulo">{esc(e.get("nome", uf))} ({uf})</h3>'
        f'<div id="sn-painel-corpo">{corpo_ficha(uf, e, data, idx)}</div></aside>'
        f"{mapa_mod.legenda()}</div>"
    )


# ---------------------------------------------------------------- tabela


def _celula(c: dict | None, e: dict) -> tuple[str, str]:
    if not c:
        return "–", "–"
    return (
        f"{esc(c.get('nome', ''))} ({sigla(c.get('partido'))}){al.chip_candidatura(e, c.get('nome'))}",
        pct(c.get("p_eleito")),
    )


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
        if e.get("cobertura") == "sem_pesquisa":
            a = b = c = None
        else:
            eleitos = mapa_mod.eleitos(e)
            nomes = {x.get("nome") for x in eleitos}
            rest = sorted(
                (x for x in e.get("probabilidades", []) if x.get("nome") not in nomes),
                key=lambda x: x.get("p_eleito") or 0,
                reverse=True,
            )
            a = eleitos[0] if eleitos else None
            b = eleitos[1] if len(eleitos) > 1 else None
            c = rest[0] if rest else None
        (na, pa), (nb, pb), (nc, pc) = _celula(a, e), _celula(b, e), _celula(c, e)
        cob = {
            "recente": "recente",
            "antiga": "antiga",
            "sem_pesquisa": "sem pesquisa",
        }.get(e.get("cobertura"), esc(e.get("cobertura") or ""))
        rows.append(
            [
                f'<a href="#estado-{uf}"><b>{uf}</b></a>{al.chip_estado(e)}',
                na,
                pa,
                nb,
                pb,
                nc,
                pc,
                cob,
                _casas(e, idx),
                esc(e.get("incerteza") or "–"),
            ]
        )
    headers = [
        "UF",
        "Eleito provável 1",
        "p",
        "Eleito provável 2",
        "p",
        "Terceiro",
        "p",
        "Cobertura",
        "Pesquisas",
        "Incerteza",
    ]
    return table(
        headers,
        rows,
        "Eleitos prováveis e probabilidades por estado",
        {2, 4, 6},
        sortable=True,
    )


# ---------------------------------------------------------------- fontes


def fontes(data: dict) -> str:
    rows = []
    for f in sorted(
        data.get("fontes", []),
        key=lambda f: (f.get("uf") or "", f.get("arquivo") or ""),
    ):
        url = f.get("url")
        link = (
            f'<a href="{esc(url)}" rel="noopener">{esc(url)}</a>' if url else "sem URL"
        )
        rows.append(
            [
                esc(f.get("instituto") or ""),
                esc(f.get("uf") or ""),
                datas_br(f.get("campo")) or "sem data",
                num(f["n"], 0) if f.get("n") else "–",
                esc(f.get("registro_tse") or "–"),
                link,
                f"<code>{esc(f.get('arquivo') or '')}</code>",
                f'<code class="sn-hash">{esc(f.get("sha256") or "–")}</code>',
            ]
        )
    return table(
        [
            "Instituto",
            "UF",
            "Campo",
            "n",
            "Registro TSE",
            "URL",
            "Arquivo",
            "SHA-256",
        ],
        rows,
        "Pesquisas usadas, com registro, URL, arquivo e hash",
        {3},
    ) + al.fontes_alertas(data)
