"""Auxiliares compartilhados entre os blocos da página do Senado de 2027."""

from __future__ import annotations

import re
from html import escape as esc

from senado_2026.pagina.comum import data_br, datas_br, num

REPO = "https://github.com/ArvorCo/PNAD/blob/main/"


RELATORIOS_ORIGEM = (
    ("Claude", "analysis/senado_2027/relatorios_origem/01_claude.md"),
    ("Gemini", "analysis/senado_2027/relatorios_origem/02_gemini.md"),
    ("ChatGPT", "analysis/senado_2027/relatorios_origem/03_chatgpt.md"),
    ("Perplexity", "analysis/senado_2027/relatorios_origem/04_perplexity.pdf"),
)


BLOCO = {
    "DB": "direita bolsonarista",
    "D": "direita",
    "CD": "centro-direita",
    "C": "centro e centrão",
    "CE": "centro-esquerda",
    "E": "esquerda",
}


ESTAGIO = {
    "condenacao": "condenação",
    "condenacao_civel": "condenação cível",
    "reu": "réu",
    "reu_civel": "réu em ação cível",
    "suspenso": "ação suspensa",
    "denuncia_oferecida": "denúncia oferecida",
    "indiciado": "indiciado",
    "investigado": "investigado",
    "alvo_de_busca": "alvo de busca",
    "eleitoral_pendente": "eleitoral pendente",
    "citado": "citado",
    "representacao": "representação",
    "acusacao_sem_procedimento": "acusação sem procedimento",
    "arquivamento_pedido": "arquivamento pedido",
    "antigo_sem_desfecho": "antigo sem desfecho",
    "arquivado": "arquivado",
    "absolvido_ou_trancado": "absolvido ou trancado",
    "testemunha": "testemunha",
}


TIPO = {
    "opiniao": "opinião",
    "patrimonial": "patrimonial",
    "eleitoral": "eleitoral",
    "8_de_janeiro": "8 de janeiro",
    "outro": "outro",
}


SINAL = {
    "declaracao_pro_impeachment": "Declaração pró-impeachment",
    "assinatura_pedido_impeachment": "Assinatura de pedido de impeachment",
    "autoria_pedido_impeachment": "Autoria de pedido de impeachment",
    "cpi_contra_ministros": "CPI contra ministros",
    "voto_pec8_sim": "Votou sim na PEC 8/2021",
    "voto_pec8_nao": "Votou não na PEC 8/2021",
    "voto_pec8_ausente": "Ausente na PEC 8/2021",
    "projeto_ou_pec_contra_stf": "Projeto ou PEC sobre o STF",
    "declaracao_contra_impeachment": "Declaração contra impeachment",
    "dialogavel_segundo_stf": "Dialogável segundo ministros",
    "sondagem_com_ministro": "Sondou ministro do STF",
    "sem_posicao_localizada": "Sem posição localizada",
    "defesa_do_stf": "Defesa do STF",
    "acao_judicial_contra_ministro": "Ação judicial contra ministro",
    "representacao_administrativa_contra_ministro": "Representação contra ministro",
    "nao_assinou_pedido": "Não assinou pedido da própria bancada",
}


ACESSO = {
    "pagina": "página lida",
    "trecho_de_busca": "trecho de busca",
    "relatorio_anterior": "relatório anterior",
}


CONTINGENCIA = {
    "segundo_turno_governo": "disputa o 2º turno de governo em 25/10/2026",
    "sub_judice": "registro sub judice no TSE",
    "cassacao_pendente": "cassação pendente de novo julgamento",
    "ministerio": "titular no ministério",
    "suplente": "suplente assume a cadeira",
    "licenca": "titular licenciado",
}


def _sinal(v: float, casas: int = 0) -> str:
    if v > 0:
        return "+" + num(v, casas)
    if v < 0:
        return "−" + num(-v, casas)
    return num(0, casas)


def _tabela(
    headers: list[str],
    rows: list[list[str]],
    label: str,
    numericas: set[int] = frozenset(),
    sortable: bool = False,
    extra: str = "",
) -> str:
    def cls(j: int) -> str:
        return ' class="num"' if j in numericas else ""

    head = "".join(
        f'<th scope="col"{cls(j)}>{esc(h)}</th>' for j, h in enumerate(headers)
    )
    body = "".join(
        "<tr>" + "".join(f"<td{cls(j)}>{v}</td>" for j, v in enumerate(r)) + "</tr>"
        for r in rows
    )
    classe = f"table-scroll {extra}".strip()
    return (
        f'<div class="{classe}" tabindex="0" role="region" aria-label="{esc(label)}">'
        f'<table{" data-sortable" if sortable else ""}><thead><tr>{head}</tr></thead>'
        f"<tbody>{body}</tbody></table></div>"
    )


def _pessoas(data: dict) -> dict[str, dict]:
    """slug -> {pessoa, item, papel} para titulares e substitutos."""
    idx: dict[str, dict] = {}
    for item in data["elenco"]:
        idx[item["titular"]["slug"]] = {
            "pessoa": item["titular"],
            "item": item,
            "papel": "titular",
        }
        if item.get("substituto"):
            idx.setdefault(
                item["substituto"]["slug"],
                {"pessoa": item["substituto"], "item": item, "papel": "substituto"},
            )
    return idx


def _partido_uf(p: dict) -> str:
    return esc(f"{p.get('partido') or 'sem partido'}-{p.get('uf', '')}")


def _c(p: dict, cenario: str = "flavio", alvo: str = "C_imp") -> float:
    return p["scores"]["cenarios"][cenario][alvo]


def _ficha_href(info: dict) -> str:
    return f"#ficha-{esc(info['item']['titular']['slug'])}"


def _nome_link(info: dict) -> str:
    return f'<a href="{_ficha_href(info)}">{esc(info["pessoa"]["nome"])}</a>'


def _chip(estagio: str | None) -> str:
    if not estagio:
        return '<span class="sn27-chip">nada localizado</span>'
    return (
        f'<span class="sn27-chip sn27-chip-{esc(estagio)}">'
        f"{esc(ESTAGIO.get(estagio, estagio))}</span>"
    )


def _data(iso: str | None) -> str:
    """dd/mm/aaaa; datas parciais viram mm/aaaa ou só o ano."""
    if not iso:
        return "sem data"
    m = re.fullmatch(r"(\d{4})-(\d{2})", iso)
    if m:
        return f"{m.group(2)}/{m.group(1)}"
    if re.fullmatch(r"\d{4}", iso):
        return iso
    return data_br(iso)


def _iso_br(texto: str | None) -> str:
    """Escapa o texto e troca datas ISO por dd/mm/aaaa."""
    return datas_br(texto or "")


def _link(f: dict) -> str:
    """Fonte com veículo, data e selo de acesso."""
    url = f.get("url") or ""
    veiculo = esc(f.get("veiculo") or "fonte")
    titulo = esc(f.get("titulo") or "")
    rotulo = f'<a href="{esc(url)}" rel="noopener">{veiculo}</a>' if url else veiculo
    data = f", {_data(f['data'])}" if f.get("data") else ""
    acesso = ACESSO.get(f.get("acesso") or "", f.get("acesso") or "")
    selo = f' <span class="sn27-meta">({esc(acesso)})</span>' if acesso else ""
    tit = f": {titulo}" if titulo else ""
    return f"{rotulo}{data}{tit}{selo}"


def _ordenado_por_c(data: dict) -> list[dict]:
    return sorted(
        data["elenco"],
        key=lambda it: (-_c(it["titular"]), it["titular"]["nome"]),
    )


def _evento(data: dict, fonte_id: str) -> dict | None:
    for ev in data["contexto"].get("pos_eleicao", []):
        if fonte_id in ev.get("fontes", []):
            return ev
    return None
