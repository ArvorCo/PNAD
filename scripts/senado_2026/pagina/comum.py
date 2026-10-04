"""Formatação, paleta e peças compartilhadas pelos módulos da página."""

from __future__ import annotations

import re
from datetime import date
from html import escape as esc

ASSENTOS = 81  # regra constitucional: três vagas por estado
POR_ESTADO = 2  # vagas em disputa por estado em cada eleição de 2/3

ORDEM = (
    "esquerda",
    "centro-esquerda",
    "centro",
    "centro-direita",
    "direita",
    "indefinido",
)
COR = {
    "esquerda": "#b02f21",
    "centro-esquerda": "#d9775f",
    "centro": "#8a7a3a",
    "centro-direita": "#4f7fc2",
    "direita": "#1457aa",
    "indefinido": "#8a8f98",
}
ROTULO = {
    "esquerda": "Esquerda",
    "centro-esquerda": "Centro-esquerda",
    "centro": "Centro",
    "centro-direita": "Centro-direita",
    "direita": "Direita",
    "indefinido": "Indefinido",
}
SEM_PESQUISA = "#d4d6d9"
INK = "#192e2b"
PAPER_CHIP = "#fffdf8"

GRUPOS = (
    ("direita", "Direita e centro-direita", ("direita", "centro-direita")),
    ("centro", "Centro", ("centro",)),
    ("esquerda", "Esquerda e centro-esquerda", ("centro-esquerda", "esquerda")),
)


def num(x: float, casas: int = 1) -> str:
    s = f"{x:,.{casas}f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


def pct(p: float | None) -> str:
    """Probabilidade (0 a 1) como percentual inteiro, sem falsa precisão nas pontas."""
    if p is None:
        return "–"
    v = 100 * p
    if 0 < v < 1:
        return "<1%"
    if 99 < v < 100:
        return ">99%"
    return f"{round(v)}%"


def data_br(iso: str | None) -> str:
    if not iso:
        return "sem data"
    try:
        d = date.fromisoformat(iso[:10])
    except ValueError:
        return esc(iso)
    return d.strftime("%d/%m/%Y")


def datas_br(texto: str | None) -> str:
    """Troca datas ISO dentro de um texto por dd/mm/aaaa."""
    return re.sub(r"(\d{4})-(\d{2})-(\d{2})", r"\3/\2/\1", esc(texto) if texto else "")


def campo_de(valor: str | None) -> str:
    v = (valor or "").strip().lower()
    return v if v in COR else "indefinido"


def sigla(valor: str | None) -> str:
    return esc(valor) if valor else "sem partido"


def lerp(c0: str, c1: str, t: float) -> str:
    a = [int(c0[i : i + 2], 16) for i in (1, 3, 5)]
    b = [int(c1[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(
        f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b, strict=True)
    )


def alocar(valores: dict[str, float], total: int) -> dict[str, int]:
    """Maiores restos: inteiros que somam `total`, proporcionais a `valores`."""
    soma = sum(valores.values())
    if soma <= 0:
        return dict.fromkeys(valores, 0)
    brutos = {k: v * total / soma for k, v in valores.items()}
    base = {k: int(v) for k, v in brutos.items()}
    falta = total - sum(base.values())
    ordem = sorted(brutos, key=lambda k: (brutos[k] - base[k], brutos[k]), reverse=True)
    for k in ordem[:falta]:
        base[k] += 1
    return base


def iniciais(nome: str) -> str:
    palavras = [
        p
        for p in re.findall(r"[^\W\d_]+", nome)
        if p.lower() not in {"de", "da", "do", "dos", "das", "e", "fixture"}
    ]
    if not palavras:
        return "?"
    if len(palavras) == 1:
        return palavras[0][0].upper()
    return (palavras[0][0] + palavras[-1][0]).upper()


def avatar(nome: str, tamanho: int, campo: str) -> str:
    """Avatar neutro com iniciais, quando a foto oficial não existe."""
    return (
        f'<svg class="sn-foto sn-c-{campo}" width="{tamanho}" height="{tamanho}" '
        f'style="width:{tamanho}px;height:{tamanho}px" '
        f'viewBox="0 0 48 48" role="img" aria-label="Sem foto: {esc(nome)}">'
        '<rect width="48" height="48" fill="#e4e1d3"/>'
        '<circle cx="24" cy="19" r="8" fill="#b9b6a6"/>'
        '<path d="M8 48c0-10 7-16 16-16s16 6 16 16z" fill="#b9b6a6"/>'
        f'<rect x="12" y="31" width="24" height="14" rx="3" fill="{PAPER_CHIP}"/>'
        f'<text x="24" y="42" text-anchor="middle" font-size="12" font-weight="700" '
        f'fill="{INK}" font-family="Archivo, Verdana, sans-serif">{esc(iniciais(nome))}</text>'
        "</svg>"
    )


def foto(c: dict, tamanho: int) -> str:
    campo = campo_de(c.get("campo"))
    caminho = c.get("foto")
    nome = c.get("nome") or "candidatura"
    if caminho:
        return (
            f'<img class="sn-foto sn-c-{campo}" src="{esc(caminho)}" width="{tamanho}" '
            f'height="{tamanho}" style="width:{tamanho}px;height:{tamanho}px" loading="lazy" alt="Foto oficial de {esc(nome)}">'
        )
    return avatar(nome, tamanho, campo)


def barra(p: float | None, campo: str, rotulo: str) -> str:
    """Barra horizontal de probabilidade: sempre `div` em bloco, nunca span inline."""
    v = 0.0 if p is None else max(0.0, min(1.0, p))
    return (
        f'<div class="sn-bar" role="img" aria-label="{esc(rotulo)}: {pct(p)}">'
        f'<div class="sn-bar-fill sn-bg-{campo}" style="width:{100 * v:.1f}%"></div></div>'
    )


def table(headers, rows, label: str, numericas: set[int], sortable: bool = False):
    def cls(j: int) -> str:
        return ' class="num"' if j in numericas else ""

    head = "".join(
        f'<th scope="col"{cls(j)}>{esc(h)}</th>' for j, h in enumerate(headers)
    )
    body = "".join(
        "<tr>" + "".join(f"<td{cls(j)}>{v}</td>" for j, v in enumerate(row)) + "</tr>"
        for row in rows
    )
    return (
        f'<div class="table-scroll" tabindex="0" role="region" aria-label="{esc(label)}">'
        f'<table{" data-sortable" if sortable else ""}><thead><tr>{head}</tr></thead>'
        f"<tbody>{body}</tbody></table></div>"
    )


def indice_fontes(data: dict) -> dict[str, dict]:
    return {f.get("arquivo"): f for f in data.get("fontes", []) if f.get("arquivo")}


def casa_do_arquivo(arquivo: str, fonte: dict | None) -> str:
    if fonte and fonte.get("instituto"):
        return fonte["instituto"]
    return arquivo.split("_")[0].capitalize()


def datahora_br(iso: str | None) -> str:
    """ISO com hora e deslocamento como `dd/mm/aaaa hh:mm` (hora do carimbo da fonte)."""
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})", iso or "")
    if not m:
        return data_br(iso)
    a, mes, d, h, mi = m.groups()
    return f"{d}/{mes}/{a} {h}:{mi}"


def periodo_do_dia(iso: str | None) -> str:
    """manhã, tarde ou noite, pela hora do carimbo; vazio se não houver hora."""
    m = re.match(r"\d{4}-\d{2}-\d{2}[T ](\d{2}):", iso or "")
    if not m:
        return ""
    h = int(m.group(1))
    return "manhã" if h < 12 else "tarde" if h < 18 else "noite"
