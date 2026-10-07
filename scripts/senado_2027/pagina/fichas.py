"""Fichas individuais dos titulares da página do Senado de 2027."""

from __future__ import annotations

from html import escape as esc

from senado_2026.pagina.comum import data_br, num

from . import texto as tx
from .comum import (
    BLOCO,
    CONTINGENCIA,
    SINAL,
    TIPO,
    _c,
    _chip,
    _iso_br,
    _link,
    _ordenado_por_c,
    _partido_uf,
    _sinal,
    _tabela,
)

MANDATO = {
    "eleito_2026": "eleito em 2026",
    "reeleito_2026": "reeleito em 2026",
    "ate_2031": "mandato até 2031",
    "suplente_ate_2031": "suplente, mandato até 2031",
}


def _lista_fontes(fontes: list[dict]) -> str:
    if not fontes:
        return '<p class="sn27-meta">Sem fonte registrada.</p>'
    return "<ul>" + "".join(f"<li>{_link(f)}</li>" for f in fontes) + "</ul>"


def _meter(classe: str, rotulo: str, valor: float, aria: str) -> str:
    v = max(0.0, min(100.0, valor))
    return (
        f'<div class="sn27-meter sn27-meter-{classe}" role="img" '
        f'aria-label="{esc(aria)}: {num(valor)} de 100">'
        f"<b>{rotulo}</b>"
        f'<div class="sn27-meter-track"><div class="sn27-meter-fill" '
        f'style="width:{v:.1f}%"></div></div>'
        f'<b class="sn27-meter-v">{num(valor, 0)}</b></div>'
    )


def _conta_c(p: dict) -> str:
    cen = p["scores"]["cenarios"]
    ordem: list[str] = []
    linhas: dict[str, dict] = {}
    for c in tx.CENARIOS:
        for a in cen[c]["ajustes"]:
            if a["chave"] not in linhas:
                ordem.append(a["chave"])
                linhas[a["chave"]] = {"rotulo": a["rotulo"]}
            linhas[a["chave"]][c] = a
    rows = []
    for k in ordem:
        ln = linhas[k]
        cel = []
        for c in tx.CENARIOS:
            a = ln.get(c)
            cel += [
                _sinal(a["C_imp"], 1) if a else "",
                _sinal(a["C_pec"], 1) if a else "",
            ]
        rows.append([esc(ln["rotulo"]), *cel])
    rows.append(
        [
            "<b>Total</b>",
            *[
                f"<b>{num(cen[c][alvo], 0)}</b>"
                for c in tx.CENARIOS
                for alvo in ("C_imp", "C_pec")
            ],
        ]
    )
    return _tabela(
        ["Linha", "Imp. Flávio", "PEC Flávio", "Imp. Lula", "PEC Lula"],
        rows,
        f"A conta do C de {p['nome']}",
        {1, 2, 3, 4},
    )


def _caso(c: dict, kpc: dict) -> str:
    meta = [
        f"Tipo: {esc(TIPO.get(c['tipo'], c['tipo']))}",
        f"foro: {esc(c.get('foro') or 'não informado')}",
        f"relator: {esc(c.get('relator') or 'não informado')}",
        f"fato: {data_br(c.get('data_fato'))}",
        f"última decisão: {data_br(c.get('data_ultima_decisao'))}",
        f"confiança: {esc((c.get('confianca') or '').replace('media', 'média'))}",
    ]
    if c["id"] in kpc:
        meta.append(f"pontos na régua: {num(kpc[c['id']]['pontos'], 0)}")
    defesa = c.get("defesa") or "Manifestação da defesa não localizada nesta pesquisa."
    return (
        '<div class="sn27-caso">'
        f"<b>{esc(c['titulo'])}</b> {_chip(c['estagio'])}"
        f'<p class="sn27-meta">{"; ".join(meta)}.</p>'
        f"<p>{_iso_br(c.get('resumo'))}</p>"
        f'<p class="sn27-defesa"><b>Defesa.</b> {_iso_br(defesa)}</p>'
        f"{_lista_fontes(c.get('fontes') or [])}</div>"
    )


def _anteriores(p: dict) -> str:
    sa = p.get("scores_anteriores") or {}
    partes = []
    for nome, chave in (
        ("Claude", "claude"),
        ("Gemini", "gemini"),
        ("ChatGPT", "chatgpt"),
        ("Perplexity", "perplexity"),
    ):
        v = sa.get(chave)
        if not v:
            partes.append(f"{nome} sem leitura")
            continue
        partes.append(
            nome
            + " "
            + ", ".join(
                f"{esc(k)} {num(x, 0)}"
                for k, x in v.items()
                if isinstance(x, (int, float))
            )
        )
    return (
        '<p class="sn27-meta">Leituras anteriores dos quatro relatórios (não usadas '
        f"no cálculo): {'; '.join(partes)}.</p>"
    )


def _mandato(p: dict) -> str:
    m = MANDATO.get(p.get("mandato"), p.get("mandato") or "")
    return m[:1].upper() + m[1:]


def _corpo(p: dict, data: dict) -> str:
    sc = p["scores"]
    kpc = {k["id"]: k for k in sc.get("K_por_caso") or []}
    casos = p.get("casos") or []
    casos_html = (
        "".join(_caso(c, kpc) for c in casos)
        if casos
        else "<p>Nada localizado nas fontes desta pesquisa (K = 0). Não é certidão "
        "negativa.</p>"
    )
    sinais = "".join(
        f"<li><b>{esc(SINAL.get(s['tipo'], s['tipo']))}</b>"
        f"{' (' + esc(s['alvo']) + ')' if s.get('alvo') else ''}, "
        f"{data_br(s.get('data'))}. {_iso_br(s.get('resumo'))} "
        f"{'; '.join(_link(f) for f in s.get('fontes') or [])}</li>"
        for s in p.get("sinais_contrapeso") or []
    )
    voto = p.get("votacao_2026") or {}
    votos = (
        f" Votação em 2026: {num(voto['votos'], 0)} votos." if voto.get("votos") else ""
    )
    return (
        f"<p>{_iso_br(p.get('nota_editorial'))}</p>"
        f'<p class="sn27-meta">{esc(_mandato(p))}. '
        f"Bloco {esc(BLOCO.get(p['bloco'], p['bloco']))}: "
        f"{_iso_br(p.get('bloco_justificativa'))}{votos}</p>"
        f"<h4>Casos (K = {num(sc['K'])})</h4>{casos_html}"
        f"<h4>A conta do C</h4>{_conta_c(p)}"
        f"<h4>Sinais de contrapeso</h4><ul>{sinais}</ul>"
        f'<p class="sn27-meta">Confiança da ficha: '
        f"{esc(sc['confianca'].replace('media', 'média'))} "
        f"(±{sc['incerteza_pp']} pontos). Verificado em "
        f"{data_br(p.get('verificado_em'))}.</p>" + _anteriores(p)
    )


def fichas(data: dict) -> str:
    out = []
    for item in _ordenado_por_c(data):
        t = item["titular"]
        sc = t["scores"]
        cont = item.get("contingencia")
        cont_html = ""
        if cont:
            cont_html = (
                f'<div class="sn27-caixa"><p><b>Contingência:</b> '
                f"{esc(CONTINGENCIA.get(cont.get('tipo'), cont.get('tipo') or ''))}. "
                f"{_iso_br(cont.get('nota'))}</p></div>"
            )
        sub = item.get("substituto")
        sub_html = ""
        if sub:
            sub_html = (
                f"<h4>Quem pode assumir: {esc(sub['nome'])} ({_partido_uf(sub)})</h4>"
                + _meter("k", "K", sub["scores"]["K"], f"K de {sub['nome']}")
                + _meter("c", "C", _c(sub), f"C de impeachment de {sub['nome']}")
                + _corpo(sub, data)
            )
        out.append(
            f'<details class="sn27-ficha" id="ficha-{esc(t["slug"])}">'
            '<summary class="sn27-sem-foto">'
            f'<div class="sn27-ficha-id"><b>{esc(t["nome"])}</b>'
            f"<small>{_partido_uf(t)} · {esc(BLOCO.get(t['bloco'], t['bloco']))} · "
            f"cadeira {esc(item['cadeira'])}</small></div>"
            '<div class="sn27-ficha-meters">'
            + _meter("k", "K", sc["K"], f"Exposição judicial de {t['nome']}")
            + _meter("c", "C", _c(t), f"Contrapeso ao impeachment de {t['nome']}")
            + "</div></summary>"
            '<div class="sn27-ficha-corpo">'
            + cont_html
            + _corpo(t, data)
            + sub_html
            + "</div></details>"
        )
    return '<div class="sn27-fichas">' + "".join(out) + "</div>"
