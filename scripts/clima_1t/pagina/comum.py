"""Peças de texto e tabela repetidas nos capítulos do relatório de clima."""

from __future__ import annotations

from mudancas_secoes_2t.pagina.tabelas import (  # noqa: F401
    caixa,
    contra,
    detalhes,
    estatisticas,
    figura,
    limite,
    link,
    lista,
    nota,
    secao,
    tabela,
)

from .util import dec, ic, pct, pp, sinal

COR_A = "#0c7a72"  # verde-petróleo
COR_B = "#7d5b00"  # dourado
COR_C = "#6b4a92"  # roxo
COR_D = "#535b54"  # cinza

TAG = {
    "fato": '<span class="tag fato">Fato medido</span>',
    "inf": '<span class="tag inf">Inferência</span>',
    "juizo": '<span class="tag juizo">Juízo editorial</span>',
    "nao": '<span class="tag nao">Não sustentado</span>',
}


def p_fmt(p: float) -> str:
    return "p < 0,001" if p < 0.001 else "p = " + dec(p, 3)


def com_ic(m: dict | None, casas: int = 2, unidade: str = "pp") -> str:
    """Valor com sinal e intervalo; sem intervalo, devolve a nota do motor."""
    if m is None:
        return "sem dado"
    v = sinal(m["valor"], casas) + (" " + unidade if unidade else "")
    if m.get("ic95"):
        return f"{v}<small>{ic(m['ic95'], casas)}</small>"
    return f"{v}<small>{m.get('nota', 'sem intervalo')}</small>"


def parcela(m: dict, casas: int = 2) -> str:
    v = pct(m["valor"], casas)
    if m.get("ic95"):
        return f"{v}<small>IC 95% de {dec(m['ic95'][0], casas)} a {dec(m['ic95'][1], casas)}</small>"
    return f"{v}<small>{m.get('nota', 'sem intervalo')}</small>"


def razao_ic(m: dict | None) -> str:
    if m is None:
        return "referência"
    v = dec(m["valor"], 2) + "×"
    if m.get("ic95"):
        return f"{v}<small>IC 95% de {dec(m['ic95'][0], 2)} a {dec(m['ic95'][1], 2)}</small>"
    return f"{v}<small>{m.get('nota', 'sem intervalo')}</small>"


def pp_ic(par_valor: float, par_ic, casas: int = 2) -> str:
    return f"{pp(par_valor, casas)} ({ic(par_ic, casas)})"
