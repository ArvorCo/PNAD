"""Esqueleto do dossiê da apuração do 2º turno: cabeçalho, capa, navegação e montagem.

Os 16 capítulos ficam registrados em `CAPITULOS` como `(ident, curto, titulo,
arquivos)`. Cada um é o módulo `pagina_cap_<ident>.py` com `render(d, cap)`,
importado por `importlib`: módulo ausente, arquivo de dados ausente ou exceção
viram o bloco "capítulo em preparação" com o motivo, e o build nunca cai.
"""

from __future__ import annotations

import importlib
import traceback
from html import escape

from apuracao_2026.pagina_comum import pendente
from apuracao_2026.pagina_interativo import interativo_html

from .pagina_comum import (
    SLUG,
    URL,
    Capitulo,
    Dados,
    inteiro,
    milhoes,
    num,
)
from .pagina_css import CSS, FONTES, JS, JS_HEAD

YOUTUBE_LIVE = "kSELqiCudjU"
NOTICIAS = "../noticias_noite.json"
TITULO = "Apuração do 2º turno de 2026"
DESCRICAO = (
    "O resultado, a noite minuto a minuto, a parada de 114 minutos do TSE, a projeção da casa, "
    "os boletins, seções, abstenção, exterior, governadores, a totalização paralela e o que mudou entre a última pesquisa e a urna."
)

CAPITULOS: list[tuple[str, str, str, tuple[str, ...]]] = [
    ("abertura", "Resultado", "O resultado", ("presidente.json",)),
    ("noite", "A noite", "A noite minuto a minuto", ("linha_do_tempo.json",)),
    (
        "projecao",
        "Projeção",
        "A projeção da casa durante a noite",
        ("projecao_noite.json",),
    ),
    ("boletins", "Boletins", "Os boletins da noite", ()),
    (
        "cedo_tarde",
        "Cedo e tarde",
        "O que entrou cedo e o que entrou tarde",
        ("cedo_tarde.json",),
    ),
    (
        "turnos",
        "1T × 2T",
        "1º turno × 2º turno",
        ("comparacao_1t.json", "comparacao_2022.json"),
    ),
    (
        "transferencia",
        "Transferência",
        "De onde veio o voto: 1º turno → 2º turno",
        ("transferencia.json",),
    ),
    ("abstencao", "Abstenção", "A abstenção mais baixa", ("abstencao.json",)),
    (
        "secoes",
        "Seções",
        "Seção por seção: comparecimento, biometria, horários",
        ("secoes.json",),
    ),
    (
        "logs",
        "Logs",
        "O que os logs das 499 mil urnas dizem",
        ("logs.json",),
    ),
    ("exterior", "Exterior", "Exterior", ("exterior.json",)),
    ("governadores", "Governadores", "Seis governadores", ("governadores.json",)),
    (
        "pesquisas",
        "Pesquisas",
        "Pesquisas × urna e a hipótese do autor",
        ("pesquisas_vs_urna.json",),
    ),
    (
        "hipoteses",
        "Hipóteses",
        "O que poderia ter acontecido, e o que os dados dizem de cada hipótese",
        ("hipoteses.json",),
    ),
    ("paralela", "Paralela", "Totalização paralela", ("paralela.json",)),
    ("noticias", "Notícias", "O dia nas fontes", (NOTICIAS,)),
    ("auditoria", "Auditoria", "O acompanhamento, auditado", ("linha_do_tempo.json",)),
    ("video", "Vídeo", "O vídeo da apuração", ()),
    ("fontes", "Fontes", "Fontes e reprodução", ()),
]


def capitulos() -> list[Capitulo]:
    out = []
    for i, (ident, curto, titulo, arquivos) in enumerate(CAPITULOS, start=1):
        out.append(Capitulo(ident, f"{i:02d}", curto, titulo, arquivos, lambda d: ""))
    return out


def cabeca_padrao(cap: Capitulo) -> str:
    return (
        f'<div class="section-head"><p class="kicker">{cap.numero} / {cap.curto.upper()}</p>'
        f"<h2>{escape(cap.titulo)}</h2></div>"
    )


def envolver(cap: Capitulo, interno: str) -> str:
    """Põe o HTML interno do capítulo dentro de `<section id>` com a cabeça."""
    s = interno.lstrip()
    if s.startswith("<section"):
        return s if s.rstrip().endswith("</section>") else s + "</section>"
    if not s.startswith('<div class="section-head"'):
        s = cabeca_padrao(cap) + s
    return f'<section id="{cap.ident}">{s}</section>'


def montar(cap: Capitulo, d: Dados) -> tuple[str, bool, str]:
    """Devolve (html, completo, motivo). Nunca levanta exceção."""
    faltam = [a for a in cap.arquivos if d.get(a) is None]
    if faltam:
        motivo = f"falta {', '.join(faltam)}"
        d.aviso(f"capítulo {cap.ident}: {motivo}")
        return pendente(cap, faltam), False, motivo
    nome = f"apuracao_2t_2026.pagina_cap_{cap.ident}"
    try:
        mod = importlib.import_module(nome)
    except ModuleNotFoundError as erro:
        if erro.name != nome:
            motivo = f"pagina_cap_{cap.ident}.py: import falhou ({erro})"
        else:
            motivo = f"módulo pagina_cap_{cap.ident}.py ainda não existe"
        d.aviso(f"capítulo {cap.ident}: {motivo}")
        return pendente(cap, [motivo]), False, motivo
    except Exception as erro:  # o build não cai por módulo alheio quebrado
        motivo = f"pagina_cap_{cap.ident}.py: {type(erro).__name__} {erro}"
        d.aviso(f"capítulo {cap.ident}: {motivo}")
        return pendente(cap, [motivo]), False, motivo
    fn = getattr(mod, "render", None)
    if fn is None:
        motivo = f"pagina_cap_{cap.ident}.py sem render(d, cap)"
        return pendente(cap, [motivo]), False, motivo
    try:
        interno = fn(d, cap)
    except Exception as erro:  # idem: exceção vira capítulo em preparação
        quadro = traceback.extract_tb(erro.__traceback__)[-1]
        motivo = (
            f"{type(erro).__name__} {erro} "
            f"({quadro.filename.rsplit('/', 1)[-1]}:{quadro.lineno})"
        )
        d.aviso(f"capítulo {cap.ident}: {motivo}")
        return pendente(cap, [motivo]), False, motivo
    if not isinstance(interno, str) or not interno.strip():
        motivo = f"pagina_cap_{cap.ident}.render devolveu vazio"
        return pendente(cap, [motivo]), False, motivo
    return envolver(cap, interno), True, ""


def head(d: Dados) -> str:
    P = d.get("presidente.json")
    desc = DESCRICAO
    if P:
        n = P["nacional"]
        desc = (
            f"Lula {num(n['pct_lula'], 2)}% × Flávio {num(n['pct_flavio'], 2)}%, "
            f"{milhoes(n['margem_lula_votos'])} de votos de diferença. " + DESCRICAO
        )
    img = f"https://brasil.arvor.co/img/og/{SLUG}.png"
    return (
        '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{TITULO} | Arvor</title>{JS_HEAD}"
        f'<meta name="description" content="{escape(desc)}">'
        f'<link rel="canonical" href="{URL}">'
        '<meta property="og:type" content="article">'
        f'<meta property="og:title" content="{TITULO}: o resultado, a noite e o método">'
        f'<meta property="og:description" content="{escape(desc)}">'
        f'<meta property="og:url" content="{URL}">'
        f'<meta property="og:image" content="{img}">'
        '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
        '<meta name="twitter:card" content="summary_large_image">'
        f'<meta name="twitter:title" content="{TITULO}">'
        f'<meta name="twitter:description" content="{escape(desc)}">'
        f'<meta name="twitter:image" content="{img}">'
        f"{FONTES}<style>{CSS}</style></head>"
    )


def iframe_youtube(vid: str, titulo: str) -> str:
    return (
        f'<div class="video-embed"><iframe src="https://www.youtube.com/embed/{escape(vid)}" '
        f'title="{escape(titulo)}" loading="lazy" referrerpolicy="strict-origin-when-cross-origin" '
        'allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" '
        "allowfullscreen></iframe></div>"
    )


def hero(d: Dados) -> str:
    P = d.get("presidente.json")
    h = (
        '<header class="hero"><div class="wrap"><div class="masthead"><a href="index.html">ARVOR / BRASIL</a>'
        "<span>DOSSIÊ DA APURAÇÃO · 25.10.26</span>"
        '<a href="apuracao_1o_turno_2026.html">O DOSSIÊ DO 1º TURNO ↗</a></div>'
        '<p class="kicker">APURAÇÃO / 2º TURNO / PRESIDENTE E SEIS GOVERNADORES</p>'
    )
    if not P:
        return (
            h
            + "<h1>A apuração<br><em>do 2º turno.</em></h1>"
            + '<div class="pendente-bloco">capítulo em preparação: <code>presidente.json</code></div></div></header>'
        )
    n = P["nacional"]
    L = d.get("linha_do_tempo.json") or {}
    sil = (L.get("pausas") or {}).get("silencio_geral") or {}
    parada = (
        f" Entre {sil['ultimo_gerado_antes_brt'][11:16]} e {sil['primeiro_gerado_depois_brt'][11:16]}, "
        f"durante a prorrogação decidida no STF, o TSE ficou {num(sil['minutos'], 1)} minutos sem gerar arquivo algum."
        if sil.get("minutos")
        else ""
    )
    h += (
        f"<h1>Lula vence<br><em>por {milhoes(n['margem_lula_votos'])} de votos.</em></h1>"
        f'<p class="deck">Com {num(n["pst"], 2)}% das seções totalizadas, Lula tem {num(n["pct_lula"], 2)}% dos válidos '
        f"e Flávio Bolsonaro {num(n['pct_flavio'], 2)}%.{parada} Este dossiê mostra a noite como o banco a registrou, "
        "o que a projeção da casa disse a cada cinco minutos e o que mudou entre a última pesquisa e a urna.</p>"
        '<div class="score-grid">'
        f'<div><span>Presidente · válidos</span><b><i class="lula">{num(n["pct_lula"], 2)}</i> <small>×</small> '
        f'<i class="flavio">{num(n["pct_flavio"], 2)}</i></b><p>Lula (PT) / Flávio Bolsonaro (PL)</p></div>'
        f'<div><span>Votos</span><b>{num(n["lula"] / 1e6, 2)} mi</b><p>contra {num(n["flavio"] / 1e6, 2)} mi de Flávio</p></div>'
        f'<div><span>Abstenção</span><b>{num(n["pct_abstencao"], 2)}%</b><p>{inteiro(n["secoes"])} de {inteiro(n["secoes_total"])} seções</p></div>'
        "</div>"
        f'<p class="boundary">Versão nacional gerada pelo TSE às {n["gerado_brt"][11:19]} de 25/10 '
        f"({num(n['pst'], 2)}% das seções). Cada número desta página sai de um JSON listado em Fontes e reprodução.</p>"
        + iframe_youtube(YOUTUBE_LIVE, "Live da apuração do 2º turno, Arvor")
        + '<p class="hero-vivo">A live da noite, gravada no YouTube: telão, projeção e boletins como foram ao ar.</p>'
        "</div></header>"
    )
    return h


def nav(caps: list[Capitulo]) -> str:
    links = "".join(
        f'<a href="#{c.ident}"><span>{c.numero}</span>{escape(c.curto)}</a>'
        for c in caps
    )
    return (
        f'<nav class="cap" aria-label="Capítulos"><div class="wrap">{links}</div></nav>'
    )


def pagina(d: Dados) -> tuple[str, dict, dict]:
    caps = capitulos()
    corpo, estado, motivos = [], {}, {}
    for cap in caps:
        html, ok, motivo = montar(cap, d)
        corpo.append(html)
        estado[cap.ident] = ok
        if motivo:
            motivos[cap.ident] = motivo
    figs = (
        "".join(corpo)
        .replace("<figure", '<figure class="reveal"')
        .replace('<figure class="reveal" class=', "<figure class=")
    )
    h = (
        head(d)
        + '<body><a class="skip" href="#abertura">Pular para o conteúdo</a>'
        + hero(d)
        + nav(caps)
        + f'<main class="wrap">{figs}</main>'
        + '<footer class="wrap">Arvor · dossiê da apuração do 2º turno de 2026 · '
        '<a href="index.html">Biblioteca</a> · <a href="apuracao_1o_turno_2026.html">Dossiê do 1º turno</a> · '
        '<a href="reponderacao_pnad.html">Agregador</a> · <a href="totalizacao.html">Totalização paralela</a></footer>'
        + f"<script>{JS}</script>{interativo_html()}</body></html>"
    )
    return h.replace("<section ", "\n<section "), estado, motivos
