"""Textos, seleção e tabela do capítulo `noticias` (o dia nas fontes) do 2º turno.

Tudo sai de `analysis/apuracao_2t_2026/noticias_noite.json` (104 registros com
URL, tipo de evidência e SHA-256 do texto bruto). Os rótulos dos marcos são
descrições curtas; números, horas e falas vêm sempre do registro.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from html import escape

from .pagina_comum import MEMOS, caixa, limites, p, tabela

ARQ = "noticias_noite.json"

TIPO = {
    "fato": ("verificado", "Fato documentado"),
    "declaracao": ("apuracao", "Declaração"),
    "relato": ("relato", "Relato"),
    "hipotese": ("hipotese", "Análise"),
}

TEMA = {
    "votacao_prorrogada": "Prorrogação",
    "totalizacao_tse": "Totalização",
    "boletins_tse": "Boletins do TSE",
    "resultado": "Resultado",
    "calendario": "Calendário",
    "judicializacao": "Ações judiciais",
    "transporte_eleitores": "Transporte",
    "ocorrencias_policiais": "Ocorrências",
    "violencia_politica": "Ocorrências",
    "boca_de_urna": "Ocorrências",
    "urnas_contingencia": "Urnas substituídas",
    "abstencao": "Abstenção",
    "declaracoes_campanhas": "Campanhas",
    "reacoes_institucionais": "Instituições",
    "observadores": "Instituições",
}
GRUPOS = [
    "Prorrogação",
    "Totalização",
    "Transporte",
    "Ocorrências",
    "Urnas substituídas",
    "Abstenção",
    "Campanhas",
    "Instituições",
    "Resultado",
    "Boletins do TSE",
    "Ações judiciais",
    "Calendário",
]


def grupo(item: dict) -> str:
    return TEMA.get(item.get("tema", ""), "Outros")


def limpa(s: str) -> str:
    """Regra de escrita da casa: o termo das fontes para a acusação vira 'irregularidade'."""
    s = re.sub(
        r"'[Ff]raude'",
        "palavras de ordem que acusavam irregularidade na eleição",
        s or "",
    )
    return re.sub(r"\b[Ff]raude\b", "irregularidade", s)


def tem_hora(item: dict) -> bool:
    return "T" in item["quando"] and not item.get("hora_desconhecida")


def hora(item: dict) -> str:
    q = item["quando"]
    return f"{q[11:13]}h{q[14:16]}" if tem_hora(item) else "sem hora"


def dia(item: dict) -> str:
    q = item["quando"]
    return f"{q[8:10]}/{q[5:7]}"


def minutos(item: dict) -> float | None:
    if not tem_hora(item):
        return None
    hh, mm = item["quando"][11:16].split(":")
    base = 0 if item["quando"][:10] == "2026-10-25" else None
    return None if base is None else int(hh) * 60 + int(mm)


def minuto_texto(s: str) -> float | None:
    """Primeira hora escrita '17h06' ou '17:06' no texto."""
    m = re.search(r"\b(\d{1,2})[h:](\d{2})\b", s or "")
    return int(m.group(1)) * 60 + int(m.group(2)) if m else None


def ordenados(N: dict) -> list[dict]:
    return sorted(
        N["itens"], key=lambda i: (i["quando"][:10], not tem_hora(i), i["quando"])
    )


def selo(item: dict) -> str:
    css, nome = TIPO.get(item["tipo"], ("relato", item["tipo"]))
    return f'<span class="selo selo-{css}">{nome}</span>'


def rotulo_hora(item: dict) -> str:
    h = hora(item)
    if item.get("hora_incerta"):
        h += " (hora incerta)"
    if item.get("quando_tipo") == "evento_ou_horario_citado" and tem_hora(item):
        h += ", hora do fato"
    if item["quando"][:10] != "2026-10-25":
        h = f"{dia(item)}, {h}"
    return h


def linha_item(item: dict, resumo: bool = True) -> str:
    corpo = escape(limpa(item["resumo"])) if resumo else escape(limpa(item["titulo"]))
    nota_ = (
        f' <span class="nt-nota">Nota da coleta: {escape(limpa(item["nota"]))}</span>'
        if item.get("nota")
        else ""
    )
    return (
        f'<li><b>{escape(rotulo_hora(item))}</b> · {escape(item["veiculo"])} {selo(item)} '
        f'{corpo} <a href="{escape(item["url"])}" rel="noopener">fonte</a>.{nota_}</li>'
    )


# ------------------------------------------------------------------ marcos


Pred = Callable[[dict], bool]


def _tem(*partes: str, tema: str | None = None) -> Pred:
    def f(i: dict) -> bool:
        if tema and i.get("tema") != tema:
            return False
        txt = i["resumo"]
        return all(x in txt for x in partes)

    return f


# (chave, rótulo curto, predicado, de onde vem a hora: 'quando' ou 'texto')
MARCOS: list[tuple[str, str, Pred, str]] = [
    (
        "pedido",
        "Campanha de Lula pede extensão ao TSE",
        _tem("protocola", "extensão"),
        "quando",
    ),
    (
        "pedidos",
        "As duas campanhas pedem prorrogação ao TSE",
        _tem("pediram ao TSE"),
        "quando",
    ),
    (
        "pge",
        "PGE opina contra a prorrogação",
        _tem("Procuradoria-Geral Eleitoral"),
        "quando",
    ),
    ("zanin", "Zanin decide na Reclamação 101673", _tem("Reclamação 101673"), "quando"),
    (
        "parada",
        "TSE suspende a totalização",
        _tem("suspendeu a totalização", tema="totalizacao_tse"),
        "texto",
    ),
    ("aviso", "TSE avisa as seções", _tem("avisou as seções"), "quando"),
    ("esclarece", "Zanin limita a urnas ainda abertas", _tem("esclareceu"), "quando"),
    ("tresp", "TRE-SP recebe o aviso oficial", _tem("TRE-SP", "fechadas"), "texto"),
    ("retomada", "TSE retoma a totalização", _tem("retomou a totalização"), "quando"),
    (
        "virada",
        "Flávio passa à frente na apuração",
        _tem("ultrapassado por Flávio"),
        "quando",
    ),
    (
        "eleito",
        "Vitória de Lula vira certeza matemática",
        _tem("reeleito", tema="resultado"),
        "quando",
    ),
    (
        "nunes",
        "Nunes Marques anuncia o resultado",
        _tem("matematicamente", tema="boletins_tse"),
        "quando",
    ),
]


def marcos(N: dict) -> list[dict]:
    """Marcos da noite com hora no eixo, na ordem da hora; marco sem registro some."""
    out = []
    itens = ordenados(N)
    for chave, rot, pred, de in MARCOS:
        achado = next((i for i in itens if pred(i)), None)
        if achado is None:
            continue
        m = minuto_texto(achado["resumo"]) if de == "texto" else minutos(achado)
        if m is None:
            m = minutos(achado)
        if m is None:
            continue
        out.append({"chave": chave, "rotulo": rot, "item": achado, "min": m})
    return sorted(out, key=lambda x: x["min"])


def janela_parada(N: dict) -> tuple[float, float] | None:
    """Parada da totalização do TSE segundo as fontes: início no texto, fim na retomada."""
    ms = {m["chave"]: m for m in marcos(N)}
    if "retomada" not in ms:
        return None
    ini = minuto_texto(ms["retomada"]["item"]["resumo"])
    if ini is None and "parada" in ms:
        ini = ms["parada"]["min"]
    return (ini, ms["retomada"]["min"]) if ini is not None else None


def secoes_na_parada(N: dict) -> str | None:
    ms = {m["chave"]: m for m in marcos(N)}
    if "retomada" not in ms:
        return None
    m = re.search(r"com ([\d.]+) das ([\d.]+) seções", ms["retomada"]["item"]["resumo"])
    return f"{m.group(1)} das {m.group(2)}" if m else None


# ------------------------------------------------------------------ blocos


def abertura(N: dict) -> str:
    itens = N["itens"]
    cont = {k: sum(1 for i in itens if i["tipo"] == k) for k in TIPO}
    ms = {m["chave"]: m for m in marcos(N)}
    partes = []
    for k in ("zanin", "aviso", "tresp"):
        if k in ms:
            partes.append(
                f"{escape(ms[k]['rotulo'])} ({_hm(ms[k]['min'])}, segundo {escape(ms[k]['item']['veiculo'])})"
            )
    secoes = secoes_na_parada(N)
    jan = janela_parada(N)
    h = p(
        f"O levantamento reúne {len(itens)} registros da imprensa e de órgãos públicos, fechado às "
        f"{escape(N['gerado_em'][11:13])}h{escape(N['gerado_em'][14:16])} de 25/10: {cont['fato']} fatos documentados, "
        f"{cont['declaracao']} declarações, {cont['relato']} relatos e {cont['hipotese']} análises. "
        "Cada um tem link, hora, tipo de evidência e o texto bruto guardado com SHA-256.",
        "verificado",
    )
    if partes:
        txt = (
            "A sequência que decidiu a noite, pelas fontes: " + "; ".join(partes) + "."
        )
        if jan and secoes:
            txt += (
                f" O TSE ficou sem divulgar entre {_hm(jan[0])} e {_hm(jan[1])}, parado com "
                f"{secoes} seções apuradas."
            )
        h += p(txt, "verificado")
    return h


def _hm(m: float) -> str:
    m = round(m)
    return f"{m // 60:02d}h{m % 60:02d}"


def cronologia(N: dict) -> str:
    lis = []
    for m in marcos(N):
        it = m["item"]
        lis.append(
            f'<li><b>{_hm(m["min"])}</b> <strong>{escape(m["rotulo"])}.</strong> '
            f'{escape(it["veiculo"])} {selo(it)} {escape(limpa(it["resumo"]))} '
            f'<a href="{escape(it["url"])}" rel="noopener">fonte</a>.'
            + (
                f' <span class="nt-nota">Nota da coleta: {escape(limpa(it["nota"]))}</span>'
                if it.get("nota")
                else ""
            )
            + "</li>"
        )
    citacao = next(
        (
            i
            for i in N["itens"]
            if i.get("tema") == "boletins_tse" and "pensada" in i["titulo"]
        ),
        None,
    )
    h = '<h3 id="noticias-cronologia">A cronologia da prorrogação</h3>'
    h += p(
        "A hora de cada marco é a do fato quando a fonte a informa, e a de publicação quando não "
        "informa; o registro diz qual das duas."
    )
    h += f'<ol class="nt-crono">{"".join(lis)}</ol>'
    if citacao:
        m = re.search(r"'([^']+)'", citacao["titulo"])
        if m:
            h += (
                f"<blockquote>{escape(m.group(1))}<cite>Nunes Marques, presidente do TSE, sobre a "
                f'prorrogação, no pronunciamento do resultado; {escape(citacao["veiculo"])}, '
                f'<a href="{escape(citacao["url"])}" rel="noopener">{escape(citacao["titulo"])}</a>.'
                "</cite></blockquote>"
            )
    return h


# (título, grupos, frase de abertura sem número)
BLOCOS = [
    (
        "Transporte de eleitores",
        ["Transporte"],
        "A frota reduzida de ônibus públicos foi o tema dominante do dia e a base dos pedidos de "
        "prorrogação. Os números de Salvador mudaram ao longo da tarde.",
    ),
    (
        "Ocorrências policiais",
        ["Ocorrências"],
        "Balanço oficial só até 19h; não localizamos o balanço final do dia.",
    ),
    (
        "Urnas substituídas",
        ["Urnas substituídas"],
        "O TSE divulgou contagens de troca de urna ao longo do dia, sem informar os motivos.",
    ),
    (
        "Abstenção",
        ["Abstenção"],
        "A queda da abstenção apareceu com comparações históricas diferentes conforme o veículo.",
    ),
    (
        "Campanhas e instituições",
        ["Campanhas", "Instituições"],
        "Falas atribuídas: entram como declaração, não como fato, e o que dizem não foi verificado aqui.",
    ),
]


def _prioridade(i: dict) -> tuple:
    ordem = {"fato": 0, "declaracao": 1, "relato": 2, "hipotese": 3}
    return (
        i["quando"][:10] != "2026-10-25",
        ordem.get(i["tipo"], 9),
        not i.get("nota"),
        i["quando"],
    )


def blocos(N: dict, maximo: int = 8) -> str:
    h = ""
    for titulo, grupos, frase in BLOCOS:
        itens = [i for i in N["itens"] if grupo(i) in grupos]
        if not itens:
            continue
        escolhidos = sorted(
            sorted(itens, key=_prioridade)[:maximo], key=lambda i: i["quando"]
        )
        resto = len(itens) - len(escolhidos)
        h += f"<h4>{escape(titulo)}</h4>{p(escape(frase))}"
        h += (
            '<ul class="nt-lista">'
            + "".join(linha_item(i) for i in escolhidos)
            + "</ul>"
        )
        if resto > 0:
            plural = "registro" if resto == 1 else "registros"
            h += f'<p class="nt-mais">Mais {resto} {plural} deste tema na <a href="#noticias-tabela">tabela completa</a>.</p>'
    return '<h3 id="noticias-temas">Por tema</h3>' + h


# (pergunta, palavra que identifica a nota)
DIVERGENCIAS = [
    ("Hora da decisão de Zanin", "Lupa fala em"),
    ("Carimbo de chegada ao STF", "16:"),
    ("Ônibus parados em Salvador", "ônibus"),
    ("Abstenção: menor desde quando", "menor desde"),
]


def divergencias(N: dict) -> str:
    com_nota = [i for i in ordenados(N) if i.get("nota")]
    destaque = []
    for pergunta, chave in DIVERGENCIAS:
        it = next((i for i in com_nota if chave in i["nota"]), None)
        if it:
            destaque.append(
                f"<li><b>{escape(pergunta)}.</b> {escape(limpa(it['nota']))} "
                f'(<a href="{escape(it["url"])}" rel="noopener">{escape(it["veiculo"])}</a>)</li>'
            )
    h = '<h3 id="noticias-divergencias">Onde as fontes não batem</h3>'
    h += p(
        "Divergência entre fontes fica registrada, não resolvida por escolha nossa. Quando um "
        "documento primário existir, ele decide."
    )
    if destaque:
        h += f'<ul class="achados">{"".join(destaque)}</ul>'
    linhas = [
        [
            escape(rotulo_hora(i)),
            escape(i["veiculo"]),
            escape(limpa(i["resumo"])),
            escape(limpa(i["nota"])),
        ]
        for i in com_nota
    ]
    h += (
        f"<details><summary>Todas as {len(com_nota)} notas da coleta</summary>"
        + tabela(["Hora", "Veículo", "Registro", "Nota da coleta"], linhas)
        + "</details>"
    )
    return h


def nao_encontrado(N: dict) -> str:
    lis = "".join(f"<li>{escape(limpa(x))}</li>" for x in N["nao_encontrado"])
    h = '<h3 id="noticias-ausencias">O que não foi encontrado</h3>'
    h += caixa(
        "io",
        "Lacunas do levantamento. ",
        "Ausência de resultado numa busca não prova ausência do fato. Cada item abaixo diz o que se "
        "procurou e onde.",
    )
    return h + f'<ul class="nt-lista">{lis}</ul>'


# ------------------------------------------------------------------ tabela filtrável

CSS = (
    "<style>"
    ".nt-crono,.nt-lista{padding-left:1.2em}.nt-crono li,.nt-lista li{margin:0 0 10px;line-height:1.55}"
    ".nt-nota{display:block;font-size:.92em;color:var(--muted,#535b54)}"
    ".nt-mais{font-size:.95em;color:var(--muted,#535b54)}"
    ".nt-ctl{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0}"
    ".nt-ctl button{font:600 13.5px/1 var(--sans,Archivo,sans-serif);padding:8px 12px;border:1px solid var(--ink,#192e2b);"
    "background:transparent;color:var(--ink,#192e2b);cursor:pointer;border-radius:2px}"
    '.nt-ctl button[aria-pressed="true"]{background:var(--ink,#192e2b);color:var(--paper,#f4f0e6)}'
    "html:not(.js) .nt-ctl{display:none}"
    ".nt-tab td{vertical-align:top}.nt-tab .hash{font-size:11.5px}"
    "</style>"
)

JS = (
    "<script>(function(){var b=document.getElementById('noticias-tabela');if(!b)return;"
    "var bs=b.querySelectorAll('.nt-ctl button'),rs=b.querySelectorAll('tbody tr'),c=b.querySelector('.nt-cont');"
    "function f(g){var n=0;rs.forEach(function(r){var ok=g===''||r.getAttribute('data-g')===g;r.hidden=!ok;if(ok)n++;});"
    "bs.forEach(function(x){x.setAttribute('aria-pressed',x.getAttribute('data-nt')===g?'true':'false');});"
    "if(c)c.textContent=n+' registros';}"
    "bs.forEach(function(x){x.addEventListener('click',function(){f(x.getAttribute('data-nt'));});});})();</script>"
)


def tabela_filtravel(N: dict) -> str:
    itens = ordenados(N)
    presentes = [g for g in GRUPOS if any(grupo(i) == g for i in itens)]
    outros = sorted({grupo(i) for i in itens} - set(presentes))
    btn = ['<button type="button" data-nt="" aria-pressed="true">Todos</button>']
    for g in presentes + outros:
        n = sum(1 for i in itens if grupo(i) == g)
        btn.append(
            f'<button type="button" data-nt="{escape(g)}" aria-pressed="false">{escape(g)} ({n})</button>'
        )
    linhas = []
    for i in itens:
        linhas.append(
            f'<tr data-g="{escape(grupo(i))}"><th scope="row">{escape(rotulo_hora(i))}</th>'
            f'<td>{escape(i["veiculo"])}</td><td>{selo(i)}</td><td>{escape(grupo(i))}</td>'
            f'<td><a href="{escape(i["url"])}" rel="noopener">{escape(limpa(i["titulo"]))}</a>. '
            f'{escape(limpa(i["resumo"]))}</td><td>{escape(limpa(i.get("quem_disse") or ""))}</td>'
            f'<td><span class="hash" title="{escape(i["sha256"])}">{escape(i["sha256"][:12])}</span></td></tr>'
        )
    cab = "".join(
        f'<th scope="col">{c}</th>'
        for c in (
            "Hora",
            "Veículo",
            "Tipo",
            "Tema",
            "Registro",
            "Quem disse",
            "SHA-256",
        )
    )
    return (
        f'<div id="noticias-tabela"><h3>Todos os {len(itens)} registros</h3>'
        f'<div class="nt-ctl" role="group" aria-label="Filtrar por tema">{"".join(btn)}</div>'
        f'<p class="nt-cont" aria-live="polite">{len(itens)} registros</p>'
        '<div class="table-scroll" tabindex="0"><table class="nt-tab">'
        f"<caption>Registros da noite em ordem de hora, com o tipo de evidência e os 12 primeiros "
        f"caracteres do SHA-256 do texto bruto (completo ao passar o ponteiro).</caption>"
        f"<thead><tr>{cab}</tr></thead><tbody>{''.join(linhas)}</tbody></table></div></div>"
    )


def limites_cap(N: dict) -> str:
    n_limpos = sum(
        1
        for i in N["itens"]
        if re.search(
            r"\b[Ff]raude\b", i["titulo"] + i["resumo"] + (i.get("quem_disse") or "")
        )
    )
    itens = [
        "Horários em Brasília. A hora é a do fato quando a fonte a informa e a de publicação quando não; hora incerta e hora desconhecida ficam marcadas.",
        "Fato documentado quer dizer boletim oficial ou decisão citada pela fonte, não verificação independente nossa. O TSE recusou acesso automatizado; os boletins dele entram de segunda mão.",
        "Folha e UOL não foram consultados nesta rodada: a falta deles é lacuna, não ausência de cobertura.",
        "Os resumos são da coleta, não citação literal; o link leva ao texto original e o SHA-256 identifica a cópia guardada.",
    ]
    if n_limpos:
        itens.append(
            f"Em {n_limpos} registros, a palavra usada pela fonte ou por quem ela cita para acusar a "
            "eleição foi trocada por “irregularidade”, regra de escrita da casa; o link leva ao texto original."
        )
    return limites(
        itens,
        f"Levantamento completo: <code>{escape(str((MEMOS / 'noticias_noite.md').relative_to(MEMOS.parents[1])))}</code> "
        "e o JSON ao lado, com a pasta <code>noticias_fontes/</code>.",
    )
