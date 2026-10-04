"""Alertas e cenários por estado: registro indeferido, votos nulos e o que muda.

Tudo sai do JSON do motor (`alertas` e `cenarios` por estado, `cenarios` em
`senado_2027`). Sem essas chaves, nenhuma função daqui produz HTML.
"""

from __future__ import annotations

import re
from html import escape as esc

from .comum import (
    GRUPOS,
    barra,
    campo_de,
    data_br,
    datahora_br,
    num,
    pct,
    periodo_do_dia,
    sigla,
)

MARCADOR_PADRAO = "alerta"
SUFIXO_ROTULO = {
    "direita_centro_direita": "Direita e centro-direita",
    "direita_centro_direita_centro": "Direita, centro-direita e centro",
    "esquerda_centro_esquerda": "Esquerda e centro-esquerda",
    "bloco_oposicao": "O bloco de oposição",
}


def alertas_de(e: dict) -> list[dict]:
    return [a for a in e.get("alertas") or [] if isinstance(a, dict)]


def tem_alertas(data: dict) -> bool:
    return any(alertas_de(e) for e in data["estados"].values())


def _marcador(a: dict) -> str:
    return esc(a.get("marcador") or MARCADOR_PADRAO)


def chip_estado(e: dict) -> str:
    """Chip ao lado do nome do estado; vazio sem alerta."""
    marcas = []
    for a in alertas_de(e):
        m = _marcador(a)
        if m not in marcas:
            marcas.append(m)
    return "".join(f'<span class="sn-marca">{m}</span>' for m in marcas)


def chip_candidatura(e: dict, nome: str | None) -> str:
    """Chip ao lado do nome da candidatura atingida pelo alerta (chave `candidato`)."""
    marcas = []
    for a in alertas_de(e):
        if nome and a.get("candidato") == nome and _marcador(a) not in marcas:
            marcas.append(_marcador(a))
    return "".join(f'<span class="sn-marca">{m}</span>' for m in marcas)


def _fonte_li(f: dict) -> str:
    veiculo = esc(f.get("veiculo") or "fonte")
    quando = datahora_br(f.get("publicado_em"))
    url = f.get("url")
    titulo = f'<a href="{esc(url)}" rel="noopener">{veiculo}</a>' if url else veiculo
    return f"<li>{titulo}, {quando}</li>"


def bloco_alerta(e: dict) -> str:
    """Caixa de alerta no topo da ficha, com título, texto e fontes."""
    caixas = []
    for a in alertas_de(e):
        fontes = [f for f in a.get("fontes") or [] if isinstance(f, dict)]
        lista = (
            '<ul class="sn-alerta-fontes">'
            + "".join(_fonte_li(f) for f in fontes)
            + "</ul>"
            if fontes
            else ""
        )
        caixas.append(
            '<div class="sn-alerta" role="note">'
            f'<h4 class="sn-alerta-titulo">{esc(a.get("titulo") or "Alerta")}</h4>'
            f"<p>{esc(a.get('texto') or '')}</p>{lista}</div>"
        )
    return "".join(caixas)


def _fonte_cenario(f) -> str:
    if isinstance(f, dict):
        return _fonte_li(f)[4:-5]
    return esc(f)


def _central(e: dict) -> dict:
    return {c.get("nome"): c.get("p_eleito") for c in e.get("probabilidades", [])}


def _linha_cenario(c: dict, central: dict) -> str:
    campo = campo_de(c.get("campo"))
    ant = central.get(c.get("nome"))
    comp = f" · central {pct(ant)}" if ant is not None else ""
    return (
        '<li class="sn-cand sn-cand-small"><div class="sn-cand-txt">'
        f"<b>{esc(c.get('nome', ''))}</b>"
        f'<span class="sn-meta">{sigla(c.get("partido"))}{comp}</span>'
        f'<div class="sn-prob">{barra(c.get("p_eleito"), campo, "Probabilidade de eleição de " + c.get("nome", "") + " no cenário")}'
        f"<strong>{pct(c.get('p_eleito'))}</strong></div></div></li>"
    )


def cenarios_ficha(e: dict) -> str:
    """Bloco "E se os votos forem anulados?" abaixo das probabilidades centrais."""
    cens = [c for c in e.get("cenarios") or [] if isinstance(c, dict)]
    if not cens:
        return ""
    central = _central(e)
    blocos = []
    for c in cens:
        probs = sorted(
            c.get("probabilidades") or [],
            key=lambda x: x.get("p_eleito") or 0,
            reverse=True,
        )
        dupla = (
            f'<p class="sn-dupla">Chance de a dupla do cenário ser a eleita: '
            f"<strong>{pct(c['p_dupla_mais_provavel'])}</strong>"
            + (
                f" ({esc(' e '.join(c['eleitos_provaveis']))})"
                if c.get("eleitos_provaveis")
                else ""
            )
            + ".</p>"
            if c.get("p_dupla_mais_provavel") is not None
            else ""
        )
        fonte = (
            f'<p class="sn-meta">Fonte: {_fonte_cenario(c["fonte"])}.</p>'
            if c.get("fonte")
            else ""
        )
        blocos.append(
            '<div class="sn-cenario">'
            f'<h5 class="sn-cenario-rotulo">{esc(c.get("rotulo") or "Cenário")}</h5>'
            f'<p class="io sn-hipotese"><strong>Hipótese:</strong> {esc(c.get("hipotese") or "")}</p>'
            + (f"<p>{esc(c['descricao'])}</p>" if c.get("descricao") else "")
            + '<ul class="sn-cands">'
            + "".join(_linha_cenario(x, central) for x in probs)
            + f"</ul>{dupla}{fonte}</div>"
        )
    return (
        '<h4 class="sn-h">E se os votos forem anulados?</h4>'
        '<p class="sn-meta">A central acima mantém a candidatura porque a decisão é '
        "monocrática e o plenário pode revertê-la. Os cenários abaixo são hipótese "
        "explícita desta página, não previsão.</p>" + "".join(blocos)
    )


def aviso(data: dict) -> str:
    """Aviso no topo da página, só quando algum estado tem alerta."""
    itens, quando = [], ""
    for uf in sorted(data["estados"]):
        e = data["estados"][uf]
        for a in alertas_de(e):
            itens.append(
                f'<a href="#estado-{uf}">{esc(e.get("nome", uf))}: '
                f"{esc(a.get('titulo') or 'alerta')}</a>"
            )
            for f in a.get("fontes") or []:
                quando = max(quando, (f or {}).get("publicado_em") or "")
    if not itens:
        return ""
    periodo = periodo_do_dia(quando)
    dia = data_br(quando)[:5] if quando else ""
    rotulo = (
        "Atualização"
        + (f" de {dia}" if dia else "")
        + (f", {periodo}" if periodo else "")
    )
    return (
        '<aside class="sn-atualizacao" aria-label="Atualização">'
        f"<strong>{esc(rotulo)}.</strong> " + " · ".join(itens) + "</aside>"
    )


def fontes_alertas(data: dict) -> str:
    """Matérias arquivadas que sustentam os alertas, sem repetir arquivo."""
    vistos: dict[str, dict] = {}
    for e in data["estados"].values():
        for a in alertas_de(e):
            for f in a.get("fontes") or []:
                if isinstance(f, dict):
                    vistos.setdefault(f.get("arquivo") or f.get("url") or "", f)
    if not vistos:
        return ""
    itens = "".join(
        "<li>"
        + _fonte_li(f)[4:-5]
        + (f" · <code>{esc(f['arquivo'])}</code>" if f.get("arquivo") else "")
        + (
            f' · <code class="sn-hash">{esc(f["sha256"])}</code>'
            if f.get("sha256")
            else ""
        )
        + "</li>"
        for f in sorted(vistos.values(), key=lambda f: f.get("publicado_em") or "")
    )
    return (
        "<h3>Matérias arquivadas sobre os alertas</h3>"
        f'<ul class="sn-alerta-fontes">{itens}</ul>'
    )


def _rotulo_p(chave: str) -> str | None:
    if chave == "p_maioria_direita_mais_centro_direita":
        return "Direita e centro-direita fazem maioria (41 assentos ou mais)"
    m = re.match(r"p_(\d+)_(.+)$", chave)
    if not m or m.group(2) not in SUFIXO_ROTULO:
        return None
    return f"{SUFIXO_ROTULO[m.group(2)]} somam {m.group(1)} assentos ou mais"


def _esperado(src: dict, chave: str, comps: tuple) -> float | None:
    """Assentos esperados do grupo: `por_grupo` se houver, senão soma de `por_campo`."""
    g = (src.get("por_grupo") or {}).get(chave)
    if g and g.get("esperado") is not None:
        return g["esperado"]
    campos = src.get("por_campo") or {}
    vals = [
        campos[k]["esperado"]
        for k in comps
        if (campos.get(k) or {}).get("esperado") is not None
    ]
    return sum(vals) if vals else None


def _efeito_cenario(c: dict, s27: dict) -> str:
    partes = []
    for chave, rotulo, comps in GRUPOS:
        a, b = _esperado(s27, chave, comps), _esperado(c, chave, comps)
        if a is not None and b is not None:
            d = b - a
            partes.append(
                f"{rotulo.lower()}: {num(a)} para {num(b)} assentos esperados "
                f"({'+' if d >= 0 else '-'}{num(abs(d))})"
            )
    probs = []
    for k, v in c.items():
        rot = _rotulo_p(k)
        if rot and isinstance(v, (int, float)) and s27.get(k) is not None:
            probs.append(f"{rot.lower()}: {pct(s27[k])} para {pct(v)}")
    txt = esc("; ".join(partes))
    if probs:
        txt += (". " if txt else "") + esc("Probabilidades: " + "; ".join(probs))
    return txt


def limite_registro(data: dict) -> str:
    """Item de Limites sobre registro indeferido e votos nulos, com efeito nacional."""
    s27 = data["senado_2027"]
    cens = [c for c in s27.get("cenarios") or [] if isinstance(c, dict)]
    if not cens and not tem_alertas(data):
        return ""
    ufs = [
        data["estados"][uf].get("nome", uf)
        for uf in sorted(data["estados"])
        if alertas_de(data["estados"][uf])
    ]
    base = (
        "Registro indeferido, mas ainda decidível: a central mantém a candidatura "
        "enquanto o plenário puder revertê-la, e o voto nulo só existe no cenário. "
        f"Estados com alerta: {esc(', '.join(ufs))}."
        if ufs
        else "Registro indeferido e voto nulo entram só como cenário."
    )
    efeitos = "".join(
        f"<li><b>{esc(c.get('rotulo') or 'Cenário')}.</b> {_efeito_cenario(c, s27)}.</li>"
        for c in cens
    )
    return (
        f"<li><b>Registro indeferido e votos nulos.</b> {base}"
        + (f'<ul class="sn-limites-sub">{efeitos}</ul>' if efeitos else "")
        + "</li>"
    )
