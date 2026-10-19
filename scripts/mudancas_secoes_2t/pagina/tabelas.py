"""Blocos de HTML reutilizados nos capítulos: tabelas, caixas, listas e links."""

from __future__ import annotations

from .util import esc, limpa


def celula(c) -> tuple[str, str, str]:
    """Aceita texto, (html, valor_de_ordenacao) ou (html, valor, classe)."""
    if isinstance(c, tuple):
        html = c[0]
        valor = c[1] if len(c) > 1 else ""
        cls = c[2] if len(c) > 2 else ""
        return html, str(valor), cls
    return str(c), "", ""


def tabela(
    cabecalho: list[str],
    linhas: list[list],
    *,
    ordenavel: bool = False,
    numericas: tuple[int, ...] = (),
    rotulo: str = "Tabela de evidência",
    ident: str = "",
    largura: int = 560,
    atributos_linha: list[str] | None = None,
) -> str:
    th = "".join(
        '<th scope="col"'
        + (f' data-sort="{"num" if i in numericas else "txt"}"' if ordenavel else "")
        + (' class="num"' if i in numericas else "")
        + f">{h}</th>"
        for i, h in enumerate(cabecalho)
    )
    corpo = []
    for k, linha in enumerate(linhas):
        tds = []
        for i, c in enumerate(linha):
            html, val, cls = celula(c)
            classes = (cls + (" num" if i in numericas else "")).strip()
            tds.append(
                "<td"
                + (f' class="{classes}"' if classes else "")
                + (f' data-v="{esc(val)}"' if val != "" else "")
                + f">{html}</td>"
            )
        extra = f" {atributos_linha[k]}" if atributos_linha else ""
        corpo.append(f"<tr{extra}>" + "".join(tds) + "</tr>")
    return (
        f'<div class="table-scroll" tabindex="0" role="region" aria-label="{esc(rotulo)}">'
        f'<table style="min-width:{largura}px"'
        + (f' id="{ident}"' if ident else "")
        + (' data-sortable="1"' if ordenavel else "")
        + f"><thead><tr>{th}</tr></thead><tbody>{''.join(corpo)}</tbody></table></div>"
    )


def nota(texto: str) -> str:
    return f'<p class="note">{texto}</p>'


def limite(texto: str) -> str:
    return f'<p class="limite"><b>Limite.</b> {texto}</p>'


def caixa(titulo: str, texto: str, classe: str = "") -> str:
    return f'<aside class="callout {classe}"><b>{titulo}</b><p>{texto}</p></aside>'


def contra(titulo: str, texto: str) -> str:
    """Caixa do achado que contraria a tese, com o mesmo peso das demais."""
    return caixa(titulo, texto, "contra")


def detalhes(titulo: str, corpo: str, aberto: bool = False) -> str:
    return f'<details{" open" if aberto else ""}><summary>{titulo}</summary>{corpo}</details>'


def lista(itens: list[str]) -> str:
    return "<ul>" + "".join(f"<li>{i}</li>" for i in itens) + "</ul>"


def estatisticas(itens: list[tuple[str, str]]) -> str:
    return (
        '<div class="stats">'
        + "".join(f"<div><b>{v}</b><span>{r}</span></div>" for v, r in itens)
        + "</div>"
    )


def figura(svg: str, legenda: str = "", largura_min: int = 680) -> str:
    cap = f'<p class="figcap">{legenda}</p>' if legenda else ""
    return f'<figure class="chart"><div class="chart-scroll" tabindex="0" role="region" aria-label="Gráfico"><div style="min-width:{largura_min}px">{svg}</div></div>{cap}</figure>'


def link(url: str, rotulo: str) -> str:
    return f'<a href="{esc(url)}" rel="noopener">{esc(rotulo)}</a>'


def secao(num: int, ident: str, titulo: str, abertura: str, corpo: str) -> str:
    return (
        f'<section class="chapter" id="{ident}"><div class="section-heading">'
        f'<span class="section-number">{num:02}</span><div><h2>{titulo}</h2>'
        f'<p class="lead">{abertura}</p></div></div>{corpo}</section>'
    )


def sem_travessao(html: str) -> str:
    return limpa(html)
