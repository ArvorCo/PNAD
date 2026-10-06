"""Montagem da página do dossiê da apuração: cabeçalho, capa, navegação, fontes."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from functools import partial
from html import escape

from . import pagina_cap_a as A
from . import pagina_cap_b as B
from . import pagina_cap_c as C
from .pagina_comum import (
    ROOT,
    SLUG,
    URL,
    Capitulo,
    Dados,
    inteiro,
    montar,
    num,
    secao,
)
from .pagina_css import CSS, FONTES, JS, JS_HEAD
from .pagina_interativo import interativo_html

REPO = "https://github.com/ArvorCo/PNAD"

TITULO = "Apuração do 1º turno de 2026"
DESCRICAO = (
    "O resultado, a noite minuto a minuto, a falha do TSE com três camadas de fonte, Câmara, Senado, "
    "assembleias, governadores, pesquisas contra a urna, voto útil, anomalias por zona e por seção, onde colocar fiscal e o caminho do 2º turno."
)

SCRIPTS = [
    "scripts/apuracao-2026-dados.py",
    "scripts/apuracao-2026-pesquisas.py",
    "scripts/apuracao-2026-anomalias.py",
    "scripts/apuracao-2026-secoes.py",
    "scripts/apuracao-2026-fechamento.py",
    "scripts/apuracao-2026-estrategia.py",
    "scripts/apuracao-2026-comparacao.py",
    "scripts/apuracao-2026-noite-regioes.py",
    "scripts/apuracao-2026-senado-x-flavio.py",
    "scripts/apuracao-2026-arquitetura.py",
    "scripts/apuracao-2026-terceira-via.py",
    "scripts/apuracao-2026-build.py",
]
JSONS = [
    "presidente.json",
    "linha_do_tempo.json",
    "exterior.json",
    "zonas.json",
    "camara.json",
    "senado.json",
    "assembleias.json",
    "governadores.json",
    "noticias_noite.json",
    "pesquisas_vs_urna.json",
    "voto_util.json",
    "anomalias.json",
    "secoes.json",
    "fechamento.json",
    "contexto_seguranca.json",
    "estrategia_2t.json",
    "comparacao_2022.json",
    "noite_regioes.json",
    "lentidao_ufs.json",
    "senado_x_flavio.json",
    "arquitetura.json",
    "terceira_via.json",
    "fiscais.json",
]


def capitulos() -> list[Capitulo]:
    defs = [
        ("abertura", "Abertura", "O resultado", ("presidente.json",), A.r_abertura),
        (
            "noite",
            "A noite",
            "A noite minuto a minuto",
            ("linha_do_tempo.json",),
            A.r_noite,
        ),
        (
            "falha-tse",
            "A falha do TSE",
            "A falha do TSE",
            ("linha_do_tempo.json", "noticias_noite.json"),
            A.r_falha,
        ),
        (
            "regioes",
            "Regiões",
            "Nordeste, Norte e Centro-Sul",
            ("presidente.json",),
            A.r_regioes,
        ),
        (
            "exterior",
            "Exterior",
            "Exterior",
            ("exterior.json", "presidente.json"),
            A.r_exterior,
        ),
        ("camara", "Câmara", "Câmara dos Deputados", ("camara.json",), B.r_camara),
        ("senado", "Senado", "Senado de 2027", ("senado.json",), B.r_senado),
        (
            "assembleias",
            "Assembleias",
            "Assembleias",
            ("assembleias.json",),
            B.r_assembleias,
        ),
        (
            "governadores",
            "Governadores",
            "Governadores e o 2º turno",
            ("governadores.json",),
            B.r_governadores,
        ),
        (
            "pesquisas",
            "Pesquisas",
            "Pesquisas × urna",
            ("pesquisas_vs_urna.json",),
            C.r_pesquisas,
        ),
        ("voto-util", "Voto útil", "Voto útil", ("voto_util.json",), C.r_voto_util),
        (
            "anomalias",
            "Anomalias",
            "Anomalias por zona",
            ("anomalias.json",),
            C.r_anomalias,
        ),
        (
            "fiscais",
            "Fiscais",
            "Onde colocar fiscal",
            ("fiscais.json",),
            C.r_fiscais,
        ),
        (
            "segundo-turno",
            "2º turno",
            "O caminho do 2º turno",
            ("estrategia_2t.json",),
            C.r_segundo_turno,
        ),
        (
            "auditoria",
            "Auditoria",
            "Auditoria do próprio acompanhamento",
            ("presidente.json", "linha_do_tempo.json"),
            C.r_auditoria,
        ),
        ("fontes", "Fontes", "Fontes e reprodução", (), r_fontes),
    ]
    caps = []
    for i, (ident, curto, titulo, arquivos, fn) in enumerate(defs, start=1):
        cap = Capitulo(ident, f"{i:02d}", curto, titulo, arquivos, lambda d: "")
        cap.render = partial(fn, cap=cap)
        caps.append(cap)
    return caps


def head(d: Dados) -> str:
    P = d.get("presidente.json")
    desc = DESCRICAO
    if P:
        n = P["nacional"]
        desc = (
            f"Flávio {num(n['pct']['flavio'], 2)}% × Lula {num(n['pct']['lula'], 2)}%, "
            f"{inteiro(n['diferenca_votos'])} votos de diferença. " + DESCRICAO
        )
    img = f"https://brasil.arvor.co/img/og/{SLUG}.png"
    return (
        '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{TITULO} | Arvor</title>{JS_HEAD}"
        f'<meta name="description" content="{escape(desc)}">'
        f'<link rel="canonical" href="{URL}">'
        '<meta property="og:type" content="article">'
        f'<meta property="og:title" content="{TITULO}: o resultado, a noite e a falha do TSE">'
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


def hero(d: Dados) -> str:
    P = d.get("presidente.json")
    h = (
        '<header class="hero"><div class="wrap"><div class="masthead"><a href="index.html">ARVOR / BRASIL</a>'
        '<span>DOSSIÊ DA APURAÇÃO · 04 E 05.10.26</span><a href="predicao_2026_1T_presidente.html">A PREVISÃO DA CASA ↗</a></div>'
        '<p class="kicker">APURAÇÃO / 1º TURNO / PRESIDENTE, CONGRESSO E ESTADOS</p>'
    )
    if not P:
        h += "<h1>A apuração<br><em>do 1º turno.</em></h1>"
        h += '<div class="pendente-bloco">capítulo em preparação: <code>presidente.json</code></div></div></header>'
        return h
    n = P["nacional"]
    h += (
        f"<h1>Flávio na frente<br><em>por {inteiro(n['diferenca_votos'])} votos.</em></h1>"
        f'<p class="deck">Com 100% das seções, Flávio Bolsonaro tem {num(n["pct"]["flavio"], 2)}% dos válidos e Lula '
        f"{num(n['pct']['lula'], 2)}%. O 2º turno é entre os dois. No meio da noite, o arquivo nacional do TSE parou "
        "três vezes, e por 29 minutos nenhum arquivo de resultado foi gerado. Este dossiê separa o que o banco prova, "
        "o que o tribunal disse e o que ainda falta explicar.</p>"
        if n.get("secoes") == n.get("secoes_total")
        else f"<h1>Flávio na frente<br><em>por {inteiro(n['diferenca_votos'])} votos.</em></h1>"
    )
    L = d.get("linha_do_tempo.json")
    if L and L.get("pausa_geral", {}).get("lacunas"):
        mins = L["pausa_geral"]["lacunas"][0]["minutos"]
        h = h.replace("por 29 minutos", f"por {num(mins, 0)} minutos")
        vezes = {1: "uma vez", 2: "duas vezes", 3: "três vezes", 4: "quatro vezes"}
        n_par = len(A.paradas_nacionais(L))
        h = h.replace("parou três vezes", f"parou {vezes.get(n_par, f'{n_par} vezes')}")
    h += (
        '<div class="score-grid">'
        f'<div><span>Presidente · válidos</span><b><i class="flavio">{num(n["pct"]["flavio"], 2)}</i> <small>×</small> '
        f'<i class="lula">{num(n["pct"]["lula"], 2)}</i></b><p>Flávio Bolsonaro (PL) / Lula (PT)</p></div>'
        f'<div><span>Votos</span><b>{num(n["votos"]["flavio"] / 1e6, 2)} mi</b><p>contra {num(n["votos"]["lula"] / 1e6, 2)} mi de Lula</p></div>'
        f'<div><span>Comparecimento</span><b>{num(n["pct_comparecimento"], 2)}%</b><p>{inteiro(n["secoes"])} de {inteiro(n["secoes_total"])} seções</p></div>'
        "</div>"
        f'<p class="boundary">Arquivo nacional final gerado pelo TSE às {n["gerado_em_brt"][11:19]} de 05/10. '
        "Cada número desta página sai de um JSON listado em Fontes e reprodução.</p>"
        "</div></header>"
    )
    return h


def nav(caps: list[Capitulo]) -> str:
    links = "".join(
        f'<a href="#{c.ident}"><span>{c.numero}</span>{c.curto}</a>' for c in caps
    )
    return (
        f'<nav class="cap" aria-label="Capítulos"><div class="wrap">{links}</div></nav>'
    )


def r_fontes(d: Dados, cap: Capitulo) -> str:
    h = secao(
        cap,
        "Fontes<br><em>e reprodução.</em>",
        "Cada número da página sai de um destes arquivos, com hash e data de geração.",
    )
    linhas = []
    for nome in JSONS:
        d.get(nome)
        f = d.fontes.get(nome)
        if f:
            linhas.append(
                f'<li><a href="{REPO}/blob/main/analysis/apuracao_2026/dados/{nome}"><code>{nome}</code></a> · {escape(f.gerado_em or "s/d")}'
                f'<br><span class="hash">SHA-256 {f.sha256}</span></li>'
            )
        else:
            linhas.append(f"<li><code>{nome}</code> · ainda não disponível</li>")
    h += (
        f'<p class="io">Tudo o que esta página usa está no repositório público <a href="{REPO}">{REPO.removeprefix("https://")}</a>: '
        f'os dados em <a href="{REPO}/tree/main/analysis/apuracao_2026/dados">analysis/apuracao_2026/dados/</a>, '
        f'os memorandos de método em <a href="{REPO}/tree/main/analysis/apuracao_2026">analysis/apuracao_2026/</a>, '
        f'os extratos sob demanda em <a href="{REPO}/tree/main/analysis/apuracao_2026/extratos">extratos/</a>, '
        f'os scripts em <a href="{REPO}/tree/main/scripts">scripts/</a> e o coletor em <a href="{REPO}/tree/main/apuracao">apuracao/</a>. '
        "Os arquivos brutos do TSE, versão a versão com SHA-256, estão no banco do coletor (9,4 GB), que não cabe no GitHub e é enviado a pedido.</p>"
        "<h3>Dados</h3><p>Em <code>analysis/apuracao_2026/dados/</code>; memorandos de método em "
        '<code>analysis/apuracao_2026/*.md</code>. Clique no nome para baixar.</p><ol class="fontes">'
        + "".join(linhas)
        + "</ol>"
    )
    final = ROOT / "apuracao/data/boletins/final.json"
    if final.exists():
        sha = hashlib.sha256(final.read_bytes()).hexdigest()
        h += f'<p>Boletim final: <code>apuracao/data/boletins/final.json</code><br><span class="hash">SHA-256 {sha}</span></p>'
    h += (
        '<h3>Fontes primárias</h3><ul class="fontes">'
        "<li>Arquivos públicos de resultado do TSE, guardados pelo coletor da casa em <code>apuracao/data/apuracao.sqlite</code> "
        "com hora de geração, hora de leitura e SHA-256 (<code>apuracao/README.md</code>).</li>"
        "<li>Resultados de 2022 por município e zona: <code>data/raw/tse_resultados/</code>.</li>"
        "<li>Matérias da noite: <code>noticias_noite.json</code>, com veículo, hora e URL.</li>"
        "<li>Malhas do IBGE: <code>data/originals/ibge_malhas/</code> e <code>apuracao/public/geo/</code>.</li></ul>"
    )
    h += (
        "<details><summary>Reproduzir no repositório</summary><pre>"
        + "".join(f"python3 {x}\n" for x in SCRIPTS)
        + f"python3 scripts/social-cards.py --only {SLUG}</pre></details>"
    )
    agora = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    h += f'<p class="meta">Página gerada em {agora}.</p></section>'
    return h


def pagina(d: Dados) -> tuple[str, dict]:
    caps = capitulos()
    corpo, estado = [], {}
    for cap in caps:
        html, ok = montar(cap, d)
        corpo.append(html)
        estado[cap.ident] = ok
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
        + '<footer class="wrap">Arvor · dossiê da apuração do 1º turno de 2026 · '
        '<a href="index.html">Biblioteca</a> · <a href="predicao_2026_1T_presidente.html">Previsão</a> · '
        '<a href="reponderacao_pnad.html">Agregador</a></footer>'
        + f"<script>{JS}</script>{interativo_html()}</body></html>"
    )
    return h.replace("<section ", "\n<section "), estado
