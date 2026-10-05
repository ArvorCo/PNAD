"""Figuras do bloco de arquitetura do capítulo 3: o desenho e o volume da noite.

`arquitetura_totalizacao` desenha dois painéis, o caminho do boletim como os
documentos do TSE o descrevem e o desenho com fila e agregação incremental; abaixo
de 720 px entra a versão empilhada em HTML, com as mesmas fichas.
`volume_noite` mostra, minuto a minuto, o que chegou (recebimento seção a seção,
extrapolado da coleta parcial) e o que foi publicado, com as paradas do arquivo
nacional sombreadas. Tudo sai de `arquitetura.json` e `linha_do_tempo.json`.
"""

from __future__ import annotations

import math
from html import escape

from .pagina_comum import inteiro, num
from .pagina_fig_base import (
    GRADE,
    INK,
    MUTED,
    OUTROS,
    Tips,
    W,
    area,
    botoes,
    chip,
    dado,
    escala,
    ficha,
    figura_html,
    hit,
    legenda,
    ln,
    minutos,
    r,
    registra,
    svg_abre,
    t,
    tabela_linhas,
    ticks,
)
from .pagina_fig_noite import HACHURA, eixo_x_horas, eixo_y, sombras

GOLD = "#7d5b00"
TEAL = "#0b6650"
BRANCO = "#ffffff"
TRACO_HIP = "#7d5b00"
COR_2022 = "#6b4a92"
DESACEL = "#efe8d6"  # mais claro que a sombra das paradas

# Natureza de cada caixa: documentada (há documento público), hipótese (do autor,
# sem documento) e proposta (o desenho recomendado).
NATUREZA = {
    "doc": ("Documentado", INK),
    "hip": ("Hipótese do autor", TRACO_HIP),
    "prop": ("Proposta", TEAL),
}

HOJE = [
    (
        "urna",
        "doc",
        "Urna e mídia de resultado",
        "BU assinado e cifrado, um por seção",
        "A urna grava o boletim (BU) e os demais arquivos assinados numa mídia de resultado, levada ao ponto de transmissão.",
        "CNN Brasil, 04/10/2026",
    ),
    (
        "transporte",
        "doc",
        "Transportador e JE-Connect",
        "rede privativa da Justiça Eleitoral",
        "Computadores da Justiça Eleitoral transmitem os pacotes por rede privativa e criptografada, do cartório ou de pontos JE-Connect.",
        "CNN Brasil, 04/10/2026; Res. TSE 23.673/2021",
    ),
    (
        "recepcao",
        "doc",
        "RecArquivos",
        "recebe e enfileira os pacotes",
        "Recebe os pacotes do Transportador e os põe à disposição do Sistot. O TSE descreveu em 2022 uma estrutura semelhante a uma fila de banco.",
        "Res. TSE 23.673/2021; ConJur, 29/10/2022 (Julio Valente, TSE)",
    ),
    (
        "sistot",
        "doc",
        "Sistot: totalização central",
        "banco Oracle em Exadata X8 (2020)",
        "Em 2020 a totalização foi centralizada no TSE, num banco Oracle sobre Exadata X8 Full Rack (8 nós) com Half Rack de reserva, recebendo mais de 1 milhão de linhas por minuto.",
        "Nota técnica do TSE, 17/11/2020; Poder360, 18/11/2020",
    ),
    (
        "banco",
        "hip",
        "Carga com índices e totais síncronos",
        "gargalo provável no pico",
        "Hipótese do autor: a carga de cada lote atualiza índices e recalcula totais dentro da mesma transação, e a fila cresce no pico. Nenhum documento público descreve o desenho de 2026.",
        "Hipótese; sem documento público de 2026",
    ),
    (
        "divulgacao",
        "doc",
        "Programa de divulgação",
        "converte em arquivos públicos",
        "Gera os arquivos JSON por cargo e nível (país, UF, município, zona). O TSE disse que o congestionamento de 04/10 ficou na conversão de dados pela divulgação.",
        "TSE, 04/10/2026 23:56; arquivos públicos",
    ),
    (
        "cdn",
        "doc",
        "CDN e público",
        "site, aplicativo, imprensa",
        "Os arquivos chegam ao público por uma rede de entrega (Akamai, segundo o TSE em 2020); entre 19:32 e 20:02 nenhum arquivo de resultado novo foi gerado.",
        "Poder360, 16/11/2020; banco da casa",
    ),
]

IDEAL = [
    (
        "i_urna",
        "doc",
        "Urna, mídia e transmissão",
        "o que já existe e funciona",
        "Nada muda na urna nem na rede privativa. A mudança começa no recebimento.",
        "Proposta da casa",
    ),
    (
        "i_log",
        "prop",
        "Log de eventos imutável",
        "Kafka ou equivalente, partição por UF",
        "Cada BU verificado vira um evento gravado uma vez, em ordem, com hash encadeado. Gravar é só acrescentar ao fim: não há índice nem total para atualizar.",
        "Uber Engineering, 21/12/2020 (Kafka); proposta da casa",
    ),
    (
        "i_consumidor",
        "prop",
        "Consumidores idempotentes",
        "um grupo por UF; reler não duplica",
        "Leem o log no próprio ritmo. A chave é a seção: o mesmo BU lido duas vezes soma uma vez só. Um consumidor lento atrasa a própria UF, não o país.",
        "Proposta da casa",
    ),
    (
        "i_agregado",
        "prop",
        "Totais incrementais",
        "soma o lote, não recalcula o país",
        "Cada BU acrescenta os próprios votos aos contadores de zona, município, UF e país. O custo é proporcional ao lote, nunca ao total já apurado.",
        "Proposta da casa",
    ),
    (
        "i_leitura",
        "prop",
        "Armazenamento de leitura",
        "relacional ou distribuído, fora do caminho de escrita",
        "Guarda os totais e os BUs para consulta. Para 57 milhões de linhas de voto, um relacional bem indexado basta; Cassandra ou HBase só se a escala mudar de ordem.",
        "Uber Engineering, 20/07/2023 (Cassandra); dimensionamento da casa",
    ),
    (
        "i_publicador",
        "prop",
        "Publicador assíncrono",
        "fotografia assinada a cada 30 s",
        "Lê os totais e gera os arquivos públicos num ritmo fixo, assinados e com o número do último evento incluído. Se atrasar, a divulgação atrasa; a totalização segue.",
        "Proposta da casa",
    ),
    (
        "i_cdn",
        "doc",
        "CDN e público",
        "igual a hoje",
        "Mesma entrega de hoje. O arquivo publicado diz até qual evento do log ele vai.",
        "Proposta da casa",
    ),
]

AUDITORIA = (
    "i_auditoria",
    "prop",
    "Auditoria independente",
    "relê o log e confere os totais",
    "Com o log público (BU a BU, com hora e hash), qualquer pessoa refaz a soma e confere a cadeia. É o que este dossiê fez com os arquivos públicos, só que completo.",
    "Proposta da casa",
)


def _caixa(
    k: str,
    nat: str,
    tit: str,
    sub: str,
    x: float,
    y: float,
    w: float,
    h: float,
) -> str:
    _, cor = NATUREZA[nat]
    fundo = "#fffdf8" if nat != "prop" else "#eef6f2"
    tracejado = ' stroke-dasharray="7 5"' if nat == "hip" else ""
    corpo = (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="4" '
        f'fill="{fundo}" stroke="{cor}" stroke-width="2"{tracejado}/>'
        + t(x + 14, y + 25, tit, 16, INK, weight="700")
        + t(x + 14, y + 46, sub, 13.5, MUTED)
    )
    return hit(corpo, k, foco=True)


def _seta(x1, y1, x2, y2, cor=INK) -> str:
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{cor}" '
        f'stroke-width="1.8" marker-end="url(#seta-arq)"/>'
    )


def _ficha_caixa(tips: Tips, item: tuple) -> None:
    k, nat, tit, _sub, frase, fonte = item
    rot, _ = NATUREZA[nat]
    tips.html[k] = ficha(tit, rot, [("Fonte", fonte)], frase)


def _painel(
    itens: list[tuple], x0: float, y0: float, w: float, h_caixa: float, gap: float
) -> list[str]:
    out = []
    for i, (k, nat, tit, sub, _f, _fo) in enumerate(itens):
        y = y0 + i * (h_caixa + gap)
        out.append(_caixa(k, nat, tit, sub, x0, y, w, h_caixa))
        if i + 1 < len(itens):
            out.append(
                _seta(x0 + w / 2, y + h_caixa, x0 + w / 2, y + h_caixa + gap - 3)
            )
    return out


def _lis(itens: list[tuple]) -> str:
    out = []
    for k, nat, tit, sub, _f, _fo in itens:
        rot, _ = NATUREZA[nat]
        out.append(
            f'<li class="hit arq-{nat}" data-k="{k}" tabindex="0"><b>{escape(tit)}</b>'
            f"<span>{escape(sub)}</span><em>{escape(rot)}</em></li>"
        )
    return f"<ol>{''.join(out)}</ol>"


def _html_empilhado(titulo: str, itens: list[tuple], extra: tuple | None = None) -> str:
    h = f'<div class="arq-col"><h4>{escape(titulo)}</h4>{_lis(itens)}'
    if extra:
        h += f'<p class="arq-lado">Fora do caminho, lendo o log:</p>{_lis([extra])}'
    return h + "</div>"


ESTILO_EMPILHADO = (
    "<style>#fig-arquitetura_totalizacao .arq-col h4{font:700 16px/1.4 var(--sans);margin:18px 0 8px}"
    "#fig-arquitetura_totalizacao ol{list-style:none;padding:0;margin:0}"
    "#fig-arquitetura_totalizacao li{position:relative;margin:0 0 22px;padding:10px 12px;"
    "background:#fffdf8;border:2px solid var(--ink);border-radius:4px}"
    "#fig-arquitetura_totalizacao li:not(:last-child)::after{content:'';position:absolute;left:50%;"
    "bottom:-20px;width:2px;height:16px;background:var(--ink)}"
    "#fig-arquitetura_totalizacao li.arq-hip{border-style:dashed;border-color:var(--gold)}"
    "#fig-arquitetura_totalizacao li.arq-prop{border-color:var(--teal);background:#eef6f2}"
    "#fig-arquitetura_totalizacao li b{display:block;font:700 15px/1.35 var(--sans)}"
    "#fig-arquitetura_totalizacao li span{display:block;font:14px/1.45 var(--sans);color:var(--muted)}"
    "#fig-arquitetura_totalizacao li em{display:block;font:600 12px/1.4 var(--mono);font-style:normal;"
    "letter-spacing:.06em;text-transform:uppercase;color:var(--ink);margin-top:4px}"
    "#fig-arquitetura_totalizacao .arq-lado{font:600 14px/1.4 var(--sans);margin:4px 0 8px}</style>"
)


@registra("arquitetura_totalizacao")
def arquitetura_totalizacao(d, **_op) -> str:
    A = dado(d, "arquitetura")
    vol = A["volume"]
    larg, h_caixa, gap = 380, 58, 26
    h = 120 + len(HOJE) * (h_caixa + gap) + 40
    xa, xb = 40, 600
    out = [
        svg_abre(
            W,
            h,
            "O caminho do boletim hoje e um desenho com fila e totais incrementais",
            "Painel esquerdo: componentes que os documentos do TSE nomeiam, com a hipótese do autor tracejada. "
            "Painel direito: log de eventos, consumidores idempotentes, totais incrementais e publicação assíncrona.",
        ),
        '<defs><marker id="seta-arq" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
        f'markerHeight="7" orient="auto"><path d="M0,0L10,5L0,10z" fill="{INK}"/></marker></defs>',
        t(xa, 40, "Como os documentos descrevem hoje", 19, INK, weight="800"),
        t(
            xa,
            64,
            "caminho único: cada lote passa pelo mesmo banco antes de virar arquivo",
            13.5,
            MUTED,
        ),
        t(xb, 40, "Como poderia ser", 19, TEAL, weight="800"),
        t(xb, 64, "escrever, somar e publicar em etapas separadas", 13.5, MUTED),
        ln(560, 24, 560, h - 20, GRADE, 1.5),
    ]
    out += _painel(HOJE, xa, 90, larg, h_caixa, gap)
    out += _painel(IDEAL, xb, 90, larg - 60, h_caixa, gap)
    # Auditoria: ao lado do log, com seta a partir dele.
    y_log = 90 + 1 * (h_caixa + gap)
    xa_aud = xb + larg - 40
    out.append(
        _caixa(
            AUDITORIA[0],
            AUDITORIA[1],
            "Auditoria",
            "relê o log",
            xa_aud,
            y_log + h_caixa + gap,
            150,
            h_caixa,
        )
    )
    out.append(
        f'<path d="M{xb + larg - 60:.1f},{y_log + h_caixa / 2:.1f} H{xa_aud + 75:.1f} V{y_log + h_caixa + gap - 3:.1f}" '
        f'fill="none" stroke="{TEAL}" stroke-width="1.8" stroke-dasharray="5 4" marker-end="url(#seta-arq)"/>'
    )
    # Nota de volume no rodapé do painel de hoje.
    yb = h - 22
    out.append(
        t(
            xa,
            yb,
            f"Pico medido: {num(vol['pico_secoes_por_segundo'], 0)} boletins por segundo, "
            f"cerca de {inteiro(vol['pico_linhas_por_segundo'])} linhas de voto por segundo",
            13.5,
            INK,
            weight="600",
        )
    )
    legenda_itens = [
        ("documentado", INK),
        ("hipótese do autor", TRACO_HIP),
        ("proposta", TEAL),
    ]
    out.append(legenda(legenda_itens, xb, yb, 13.5))
    out.append("</svg>")
    svg = "".join(out)

    tips = Tips()
    for item in HOJE + IDEAL + [AUDITORIA]:
        _ficha_caixa(tips, item)

    empilhado = (
        ESTILO_EMPILHADO
        + _html_empilhado("Como os documentos descrevem hoje", HOJE)
        + _html_empilhado("Como poderia ser", IDEAL, AUDITORIA)
    )
    corpo = (
        f'<div class="fig-larga">{svg}</div><div class="fig-estreita">{empilhado}</div>'
    )
    legenda_ = (
        "No primeiro painel, os componentes que documentos públicos nomeiam (resolução do TSE, nota técnica de 2020, "
        "declarações de 04/10/2026); a caixa tracejada é a hipótese do autor, sem documento de 2026. No segundo, "
        "o desenho proposto: o boletim é gravado uma vez num log, somado por consumidores que não recalculam "
        "o país e publicado num ritmo fixo. Fontes na ficha de cada caixa e em fontes_arquitetura.json."
    )
    return figura_html(
        "arquitetura_totalizacao", corpo, legenda_, tips, modo="full", dim=False
    )


# ------------------------------------------------------------------ volume


@registra("volume_noite")
def volume_noite(d, **_op) -> str:
    A = dado(d, "arquitetura")
    L = dado(d, "linha_do_tempo")
    r26 = tabela_linhas(A["recebimento_2026"])
    r22 = dict(A["recebimento_2022"]["linhas"])
    pub = {row[0]: row for row in A["publicacao_2026"]["linhas"]}
    taxas = A["nacional"]["taxas"]
    ini, fim = minutos(r26[0]["minuto"]), minutos(r26[-1]["minuto"]) + 1
    esq, topo, base, dir_ = 80, 70, 410, W - 90
    h = base + 56
    X = escala(ini, fim, esq, dir_)
    m_rec = max(max(x["secoes_extrapoladas"] for x in r26), max(r22.values() or [0]))
    teto_rec = math.ceil(m_rec * 1.18 / 1000) * 1000
    teto_pub = math.ceil(max(v[1] for v in pub.values()) * 1.18 / 1000) * 1000
    Yr = escala(0, teto_rec, base, topo)
    Yp = escala(0, teto_pub, base, topo)
    larg = (dir_ - esq) / (fim - ini)
    out = [
        svg_abre(
            W,
            h,
            "Boletins recebidos e arquivos publicados por minuto, 17h às 21h30",
            "Barras: seções recebidas por minuto em 2026 (coleta parcial extrapolada), em 2022 (país inteiro) "
            "ou versões de arquivo publicadas em 2026. Faixas: paradas do arquivo nacional; hachura: nenhum arquivo gerado.",
        ),
        HACHURA,
        sombras(L, X, topo, base),
    ]
    des = A["recebimento_2026"].get("desaceleracao")
    if des:
        a, b = minutos(des["janela"][0]), minutos(des["janela"][1]) + 1
        out.append(
            r(
                X(a),
                topo + 44,
                X(b) - X(a),
                base - topo - 44,
                DESACEL,
                f' stroke="{GOLD}" stroke-width="1.2" stroke-dasharray="4 3"',
            )
        )
        out.append(
            '<g data-alt-show="r26" pointer-events="none">'
            + chip(
                X(a) - 6,
                topo + 108,
                f"{des['janela'][0]} a {des['janela'][1]}: ritmo a {num(des['razao'] * 100, 0)}%",
                13,
                "end",
            )
            + "</g>"
        )
    g26 = [
        eixo_y(
            Yr, ticks(0, teto_rec, 5), esq, dir_, lambda v: f"{num(v / 1000, 0)} mil"
        )
    ]
    g22 = [
        eixo_y(
            Yr, ticks(0, teto_rec, 5), esq, dir_, lambda v: f"{num(v / 1000, 0)} mil"
        )
    ]
    gp = [
        eixo_y(
            Yp, ticks(0, teto_pub, 5), esq, dir_, lambda v: f"{num(v / 1000, 0)} mil"
        )
    ]
    for x in r26:
        m = minutos(x["minuto"])
        v = x["secoes_extrapoladas"]
        g26.append(r(X(m) + 0.4, Yr(v), larg - 0.8, base - Yr(v), INK))
        v22 = r22.get(x["minuto"], 0)
        g22.append(r(X(m) + 0.4, Yr(v22), larg - 0.8, base - Yr(v22), COR_2022))
        vp = pub.get(x["minuto"], [x["minuto"], 0, 0])[1]
        gp.append(r(X(m) + 0.4, Yp(vp), larg - 0.8, base - Yp(vp), OUTROS))
    # Taxa do arquivo nacional entre versões, em degraus dourados (só em 2026 recebido).
    for tx in taxas:
        a, b = minutos(tx["de"]), minutos(tx["ate"])
        if b < ini or a > fim or tx["secoes"] <= 0 or tx["minutos"] < 1:
            continue
        y = Yr(min(tx["secoes_por_minuto"], teto_rec))
        g26.append(ln(X(max(a, ini)), y, X(min(b, fim)), y, GOLD, 3))
    out.append(f'<g data-alt-show="r26">{"".join(g26)}</g>')
    out.append(f'<g data-alt-show="r22" display="none">{"".join(g22)}</g>')
    out.append(f'<g data-alt-show="pub" display="none">{"".join(gp)}</g>')
    out.append(ln(esq, base, dir_, base, INK, 1.2))
    out.append(eixo_x_horas(X, ini, fim, base, 30))
    lac = max(A["recebimento_2026"]["lacunas"], key=lambda z: z["minutos"])
    xl = X(minutos(lac["de"]))
    out.append(
        '<g data-alt-show="r26" pointer-events="none">'
        + chip(
            xl + 8,
            topo + 70,
            f"{num(lac['minutos'], 0)} min sem carimbo de recebimento",
            13,
        )
        + "</g>"
    )
    for chave, itens in (
        (
            "r26",
            [
                ("recebidas 2026 (extrapolado)", INK),
                ("ritmo do arquivo nacional", GOLD),
            ],
        ),
        ("r22", [("recebidas 2022, país inteiro", COR_2022)]),
        ("pub", [("versões de arquivo publicadas 2026 (piso)", OUTROS)]),
    ):
        oculto = "" if chave == "r26" else ' display="none"'
        out.append(
            f'<g data-alt-show="{chave}"{oculto}>{legenda(itens, esq, 26, 13.5)}</g>'
        )
    out.append(t(esq, 50, "seções ou versões por minuto", 13, MUTED))
    tips = Tips()
    linhas = []
    for i, x in enumerate(r26):
        m = minutos(x["minuto"])
        p = pub.get(x["minuto"], [x["minuto"], 0, 0])
        linhas.append(
            [
                x["minuto"],
                inteiro(x["secoes_amostra"]),
                inteiro(x["secoes_extrapoladas"]),
                inteiro(r22.get(x["minuto"], 0)),
                inteiro(p[1]),
                f"{num(p[2], 1)} MB",
            ]
        )
        out.append(hit(area(X(m), topo, larg, base - topo), f"r{i}"))
    tips.tabela(
        [
            "Minuto",
            "Seções recebidas (coleta)",
            "Extrapolado ao país",
            "Recebidas em 2022, mesmo minuto",
            "Versões publicadas 2026",
            "Volume publicado",
        ],
        linhas,
        sub=0,
        nota="Coleta parcial extrapolada; versões publicadas são piso (o coletor não lê todo arquivo a cada minuto).",
    )
    out.append("</svg>")
    ctl = botoes(
        [
            ("r26", "Recebidas 2026"),
            ("r22", "Recebidas 2022"),
            ("pub", "Publicadas 2026"),
        ],
        "r26",
        "Mostrar",
    )
    am = A["amostra"]
    pico = A["nacional"]["pico_sustentado"]
    legenda_ = (
        f"Recebimento pelo carimbo publicado no arquivo de cada seção, em {len(am['ufs_cobertas'])} UFs "
        f"({num(am['fracao_do_pais'] * 100, 1)}% das seções; faltam {', '.join(am['ufs_ausentes'])}), multiplicado por "
        f"{num(am['fator_extrapolacao'], 2)}: ordem de grandeza, não o minuto exato do país. O traço dourado é o ritmo "
        f"do arquivo nacional entre versões (pico de {inteiro(pico['secoes_por_minuto'])} seções por minuto). Em 2022, "
        f"país inteiro, o pico foi de {inteiro(A['recebimento_2022']['pico']['secoes'])} por minuto. "
        + (
            f"Faixa clara tracejada, dentro da terceira parada do nacional: de {des['janela'][0]} a {des['janela'][1]} os carimbos caem a "
            f"{num(des['razao'] * 100, 0)}% do ritmo dos vinte minutos anteriores, antes da pausa geral. "
            if des
            else ""
        )
        + "Fonte: arquitetura.json e linha_do_tempo.json."
    )
    return figura_html(
        "volume_noite", "".join(out), legenda_, tips, controles=ctl, minw=900, dim=False
    )
