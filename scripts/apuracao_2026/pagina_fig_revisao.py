"""Figuras da revisão geral do dossiê: quatro teses que estavam só em prosa.

- `noite_pesos_regioes` (cap. 2): peso de cada região nos válidos já apurados às
  18:10, às 19:32 e no fim (`noite_regioes.json → composicao_apurada`);
- `marcos_falha` (cap. 3): as três camadas da noite numa linha do tempo, paradas do
  arquivo nacional, pausa geral, lacunas do carimbo de recebimento e marcos de 50%,
  90% e 99% das seções (`linha_do_tempo.json`, `arquitetura.json`,
  `lentidao_ufs.json`);
- `urna_reguas` (cap. 12): a urna mais nova contra a mais velha pelas quatro réguas,
  com intervalo de 95% e a diferença bruta (`secoes.json → urna.reguas`);
- `terceira_via_reguas_totais` (cap. 13): saldo da terceira via para Flávio pelas
  réguas da pesquisa e da urna de 2022, contra a diferença do 1º turno
  (`terceira_via.json → reguas.totais.brasil`).

Cada figura tem a versão larga e a empilhada abaixo de 720 px (`larga_estreita`),
SVG desenhado aqui, ficha por linha e nenhum número digitado.
"""

from __future__ import annotations

from .pagina_comum import FLAVIO, GOLD, inteiro, num
from .pagina_fig_base import (
    COR_REGIAO,
    GRADE,
    INK,
    MUTED,
    PAPER,
    REGIOES,
    Tips,
    W,
    area,
    dado,
    escala,
    ficha,
    figura_html,
    hit,
    larga_estreita,
    ln,
    minutos,
    pp,
    r,
    registra,
    rot_hora,
    sobre,
    svg_abre,
    t,
)
from .pagina_fig_terceira_via import sinal_votos, votos_curto

CINZA_TXT = "#5f6773"
TEAL = "#0f7f5f"
ROXO = "#5a4a9e"
CLARO = "#d8cfb8"
ESTREITA = 380
EXT = {0: "nenhuma", 1: "uma", 2: "duas", 3: "três", 4: "quatro"}


def _hora(s: str) -> str:
    return s.strip().split(" ")[-1][:5]


# ------------------------------------------------------------------ cap. 2


def _pesos_linhas(N: dict) -> tuple[str, str, list[dict]]:
    comp = N["composicao_apurada"]
    pico = N["decomposicao"]["pico_brt"][:16]
    pausa = N["lacuna_da_soma"]["de_brt"][:16]
    linhas = []
    for reg in REGIOES:
        linhas.append(
            {
                "regiao": reg,
                "pico": comp[pico][reg]["apurado_pct"],
                "pausa": comp[pausa][reg]["apurado_pct"] if pausa in comp else None,
                "final": comp[pico][reg]["final_pct"],
                "secoes_pico": comp[pico][reg].get("secoes_pct"),
            }
        )
    return pico, pausa, linhas


def _pesos_svg(
    linhas: list[dict], pico: str, pausa: str, keys: list[str], largura: float
) -> str:
    estreita = largura < 700
    esq = 12 if estreita else 160
    topo = 56 if estreita else 52
    passo = 62 if estreita else 52
    dir_ = largura - (16 if estreita else 150)
    hi = max(max(x["pico"], x["final"], x["pausa"] or 0) for x in linhas)
    hi = 10 * (int(hi // 10) + 1)
    X = escala(0, hi, esq, dir_)
    base = topo + passo * len(linhas)
    h = base + (88 if estreita else 70)
    fs = 15 if estreita else 14
    out = [
        svg_abre(
            largura,
            h,
            "Peso de cada região nos válidos já apurados",
            f"Parcela de cada região nos válidos apurados às {_hora(pico)} (círculo cheio), às {_hora(pausa)} "
            "(círculo vazado) e no resultado final (traço preto).",
        )
    ]
    for v in range(0, int(hi) + 1, 10):
        out.append(ln(X(v), topo - 12, X(v), base, GRADE))
        out.append(t(X(v), base + 22, f"{v}%", fs - 1, MUTED, "middle", mono=True))
    for i, x in enumerate(linhas):
        y = topo + i * passo + passo / 2 + (10 if estreita else 0)
        cor = COR_REGIAO[x["regiao"]]
        corpo = []
        if estreita:
            corpo.append(t(esq, y - 22, x["regiao"], fs, INK, weight="700"))
        else:
            corpo.append(t(esq - 14, y + 5, x["regiao"], fs, INK, "end", "700"))
        a, b = sorted((x["pico"], x["final"]))
        corpo.append(ln(X(a), y, X(b), y, CLARO, 6, ' stroke-linecap="round"'))
        corpo.append(ln(X(x["final"]), y - 13, X(x["final"]), y + 13, INK, 3.5))
        if x["pausa"] is not None:
            corpo.append(
                f'<circle cx="{X(x["pausa"]):.1f}" cy="{y:.1f}" r="7" fill="{PAPER}" '
                f'stroke="{cor}" stroke-width="3"/>'
            )
        corpo.append(
            f'<circle cx="{X(x["pico"]):.1f}" cy="{y:.1f}" r="8" fill="{cor}"/>'
        )
        if estreita:
            corpo.append(
                t(
                    dir_,
                    y - 18,
                    f"{num(x['pico'], 1)} → {num(x['final'], 1)}%",
                    13,
                    INK,
                    "end",
                    mono=True,
                )
            )
        else:
            corpo.append(
                t(
                    dir_ + 16,
                    y + 5,
                    f"{num(x['pico'], 1)} → {num(x['final'], 1)}%",
                    13,
                    INK,
                    mono=True,
                )
            )
        corpo.insert(0, area(0, y - passo / 2, largura, passo))
        out.append(hit("".join(corpo), keys[i]))
    yl = base + (52 if estreita else 50)
    leg = [
        f'<circle cx="{esq + 8:.1f}" cy="{yl - 5:.1f}" r="7" fill="{INK}"/>',
        t(esq + 22, yl, _hora(pico), fs - 1),
        f'<circle cx="{esq + 98:.1f}" cy="{yl - 5:.1f}" r="6" fill="{PAPER}" stroke="{INK}" stroke-width="3"/>',
        t(esq + 112, yl, _hora(pausa), fs - 1),
        ln(esq + 188, yl - 16, esq + 188, yl + 6, INK, 3.5),
        t(esq + 200, yl, "final", fs - 1),
    ]
    out.append("".join(leg))
    out.append("</svg>")
    return "".join(out)


@registra("noite_pesos_regioes")
def noite_pesos_regioes(d, **_op) -> str:
    N = dado(d, "noite_regioes")
    pico, pausa, linhas = _pesos_linhas(N)
    tips = Tips()
    keys = []
    for x in linhas:
        lin = [
            (f"Peso às {_hora(pico)}", f"{num(x['pico'], 1)}%"),
            (
                f"Peso às {_hora(pausa)}",
                f"{num(x['pausa'], 1)}%" if x["pausa"] else "s/d",
            ),
            ("Peso final", f"{num(x['final'], 1)}%"),
            ("Diferença às " + _hora(pico), pp(x["pico"] - x["final"], 1)),
        ]
        if x["secoes_pico"] is not None:
            lin.append(
                (
                    f"Seções da região já apuradas às {_hora(pico)}",
                    f"{num(x['secoes_pico'], 1)}%",
                )
            )
        keys.append(tips.add(ficha(x["regiao"], "parcela dos válidos apurados", lin)))
    larga = _pesos_svg(linhas, pico, pausa, keys, W)
    estreita = _pesos_svg(linhas, pico, pausa, keys, ESTREITA)
    legenda_ = (
        f"Parcela de cada região nos válidos já apurados, às {_hora(pico)} (pico da vantagem de Flávio), às "
        f"{_hora(pausa)} (quando os arquivos de UF pararam) e no fim. Norte, Centro-Oeste e Sul pesavam acima do "
        "próprio tamanho no começo; Nordeste e Sudeste, abaixo. Fonte: noite_regioes.json."
    )
    return figura_html(
        "noite_pesos_regioes",
        larga_estreita(larga, estreita),
        legenda_,
        tips,
        modo="full",
    )


# ------------------------------------------------------------------ cap. 3


def _faixas_falha(d) -> tuple[list[dict], dict]:
    L = dado(d, "linha_do_tempo")
    A = dado(d, "arquitetura")
    T = dado(d, "lentidao_ufs")
    paradas = [
        x
        for x in L["travamentos"]["nacional"]
        if (x.get("secoes_no_salto") or 0) >= 1000
    ]
    faixas: list[dict] = []
    for i, x in enumerate(paradas):
        faixas.append(
            {
                "linha": 0,
                "de": minutos(x["de_brt"]),
                "ate": minutos(x["ate_brt"]),
                "cor": INK,
                "rot": f"{num(x['minutos'], 0)} min",
                "tit": f"{i + 1}ª parada do arquivo nacional",
                "fic": [
                    ("De", _hora(x["de_brt"])),
                    ("Até", _hora(x["ate_brt"])),
                    ("Duração", f"{num(x['minutos'], 1)} min"),
                    ("Seções que chegaram de uma vez", inteiro(x["secoes_no_salto"])),
                    (
                        "Seções antes e depois",
                        f"{num(x['pst_de'], 2)}% → {num(x['pst_ate'], 2)}%",
                    ),
                ],
            }
        )
    for x in L["pausa_geral"]["lacunas"]:
        lei = x["leituras_no_intervalo"]
        faixas.append(
            {
                "linha": 1,
                "de": minutos(x["de_brt"]),
                "ate": minutos(x["ate_brt"]),
                "cor": GOLD,
                "rot": f"{num(x['minutos'], 0)} min",
                "tit": "Nenhum arquivo de resultado gerado",
                "fic": [
                    ("De", _hora(x["de_brt"])),
                    ("Até", _hora(x["ate_brt"])),
                    ("Duração", f"{num(x['minutos'], 1)} min"),
                    ("Leituras do coletor", inteiro(sum(lei.values()))),
                    ("Sem modificação (304)", inteiro(lei.get("nao_modificado", 0))),
                ],
            }
        )
    des = A["recebimento_2026"].get("desaceleracao")
    if des:
        faixas.append(
            {
                "linha": 2,
                "de": minutos(des["janela"][0]),
                "ate": minutos(des["janela"][1]) + 1,
                "cor": "#9fd0bf",
                "rot": "",
                "tit": "Carimbos desaceleram",
                "fic": [
                    ("Janela", f"{des['janela'][0]} a {des['janela'][1]}"),
                    ("Carimbos por minuto", inteiro(des["media_janela"])),
                    (
                        f"Média de {des['base'][0]} a {des['base'][1]}",
                        inteiro(des["media_base"]),
                    ),
                    ("Razão", f"{num(100 * des['razao'], 0)}%"),
                ],
            }
        )
    for x in A["recebimento_2026"]["lacunas"]:
        faixas.append(
            {
                "linha": 2,
                "de": minutos(x["de"]),
                "ate": minutos(x["ate"]),
                "cor": TEAL,
                "rot": f"{num(x['minutos'], 0)} min",
                "tit": "Nenhum boletim com carimbo de recebimento",
                "fic": [
                    ("De", _hora(x["de"])),
                    ("Até", _hora(x["ate"])),
                    ("Duração", f"{num(x['minutos'], 1)} min"),
                ],
            }
        )
    marcos = {
        k: minutos(v) for k, v in T["nacional"]["horas_2026"].items() if "(" not in v
    }
    dv = L["divergencia_soma_ufs"]["maior_diferenca_visivel"]
    extra = {"marcos": marcos, "divergencia": dv}
    return faixas, extra


LINHAS_FALHA = [
    "Arquivo nacional de presidente",
    "Todos os arquivos de resultado",
    "Carimbo de recebimento das seções",
    "País: seções totalizadas",
]


def _falha_svg(faixas: list[dict], extra: dict, keys: list[str], largura: float) -> str:
    estreita = largura < 700
    ini, fim = 17 * 60 + 30, 21 * 60 + 30
    esq = 10 if estreita else 270
    dir_ = largura - (14 if estreita else 24)
    topo = 30
    passo = 74 if estreita else 62
    X = escala(ini, fim, esq, dir_)
    base = topo + passo * len(LINHAS_FALHA)
    h = base + 44
    fs = 15 if estreita else 14
    out = [
        svg_abre(
            largura,
            h,
            "A noite em três camadas",
            "Paradas do arquivo nacional, pausa em que nenhum arquivo de resultado foi gerado, lacunas do carimbo de "
            "recebimento dos boletins e marcos de 50%, 90% e 99% das seções, pela hora de Brasília.",
        )
    ]
    m = ini
    while m <= fim:
        out.append(ln(X(m), topo - 4, X(m), base, GRADE))
        if not estreita or m % 60 == 0:
            out.append(
                t(X(m), base + 24, rot_hora(m), fs - 1, MUTED, "middle", mono=True)
            )
        m += 30
    for i, nome in enumerate(LINHAS_FALHA):
        y0 = topo + i * passo
        if estreita:
            out.append(t(esq, y0 + 20, nome, fs, INK, weight="700"))
        else:
            out.append(t(esq - 14, y0 + passo / 2 + 5, nome, fs, INK, "end", "700"))
        out.append(ln(esq, y0 + passo, dir_, y0 + passo, GRADE))
    altura = 20 if estreita else 24
    for f, k in zip(faixas, keys, strict=True):
        y0 = topo + f["linha"] * passo + (passo - altura) / 2 + (14 if estreita else 0)
        corpo = [area(X(f["de"]), y0 - 6, X(f["ate"]) - X(f["de"]), altura + 12)]
        corpo.append(
            r(
                X(f["de"]),
                y0,
                max(X(f["ate"]) - X(f["de"]), 2),
                altura,
                f["cor"],
                f' stroke="{PAPER}" stroke-width="1.5"',
            )
        )
        meio = (X(f["de"]) + X(f["ate"])) / 2
        if f["rot"] and X(f["ate"]) - X(f["de"]) > 52:
            corpo.append(
                t(
                    meio,
                    y0 + altura / 2 + 5,
                    f["rot"],
                    13,
                    sobre(f["cor"]),
                    "middle",
                    "700",
                )
            )
        elif f["rot"] and not estreita:
            corpo.append(t(meio, y0 - 6, f["rot"], 13, INK, "middle", "700"))
        out.append(hit("".join(corpo), k))
    yb = topo + 3 * passo + passo / 2 + (14 if estreita else 0)
    for pct_, mm in sorted(extra["marcos"].items(), key=lambda kv: kv[1]):
        if ini <= mm <= fim:
            out.append(ln(X(mm), yb - 14, X(mm), yb + 14, FLAVIO, 3))
            out.append(t(X(mm), yb - 20, f"{pct_}%", 13, FLAVIO, "middle", "700"))
            out.append(t(X(mm), yb + 30, rot_hora(mm), 13, MUTED, "middle", mono=True))
    out.append("</svg>")
    return "".join(out)


@registra("marcos_falha")
def marcos_falha(d, **_op) -> str:
    faixas, extra = _faixas_falha(d)
    tips = Tips()
    keys = [tips.add(ficha(f["tit"], "hora de Brasília", f["fic"])) for f in faixas]
    larga = _falha_svg(faixas, extra, keys, W)
    estreita = _falha_svg(faixas, extra, keys, ESTREITA)
    dv = extra["divergencia"]
    legenda_ = (
        "Preto: arquivo nacional de presidente sem versão nova, com seções represadas. Dourado: nenhum arquivo de "
        "resultado de nenhum cargo em nenhum nível. Verde: nenhum boletim com carimbo de recebimento nas seções "
        "coletadas; verde claro, carimbos a cerca de um terço do ritmo anterior. Azul: país a 50%, 90% e 99% das "
        f"seções. Às {dv['hora_brt']} a soma das UFs tinha {inteiro(dv['secoes'])} seções a mais que o nacional. "
        "Fonte: linha_do_tempo.json, arquitetura.json e lentidao_ufs.json."
    )
    return figura_html(
        "marcos_falha", larga_estreita(larga, estreita), legenda_, tips, modo="full"
    )


# ------------------------------------------------------------------ cap. 12


def _sinal(x: float, casas: int = 2) -> str:
    return ("+" if x > 0 else "−" if x < 0 else "") + num(abs(x), casas)


def _intervalo_svg(
    titulo: str,
    desc: str,
    linhas: list[dict],
    keys: list[str],
    largura: float,
    lo: float,
    hi: float,
    passo_eixo: float,
    fmt,
    faixa: tuple[float, float] | None = None,
    verticais: list[tuple[float, str]] | None = None,
    barras: bool = False,
) -> str:
    """Pontos com intervalo (ou barras a partir do zero), uma linha por régua."""
    estreita = largura < 700
    esq = (34 if barras else 14) if estreita else 400
    dir_ = largura - ((74 if barras else 16) if estreita else (40 if barras else 230))
    topo = 48 if estreita else 40
    passo = 86 if estreita else 58
    X = escala(lo, hi, esq, dir_)
    base = topo + passo * len(linhas)
    h = base + 50
    fs = 15 if estreita else 14
    out = [svg_abre(largura, h, titulo, desc)]
    if faixa:
        out.append(
            r(
                X(faixa[0]),
                topo - 10,
                X(faixa[1]) - X(faixa[0]),
                base - topo + 10,
                "#ece5d3",
            )
        )
    v = lo
    while v <= hi + 1e-9:
        out.append(
            ln(
                X(v),
                topo - 10,
                X(v),
                base,
                INK if abs(v) < 1e-9 else GRADE,
                1.4 if abs(v) < 1e-9 else 1,
            )
        )
        if not estreita or abs(round(v / passo_eixo) % 2) == 0:
            out.append(t(X(v), base + 24, fmt(v), fs - 1, MUTED, "middle", mono=True))
        v += passo_eixo
    for xv, rot in verticais or []:
        out.append(
            ln(X(xv), topo - 26, X(xv), base, GOLD, 2, ' stroke-dasharray="6 4"')
        )
        out.append(t(X(xv) + 6, topo - 28, rot, 13, GOLD, "start", "700"))
    for i, x in enumerate(linhas):
        y = topo + i * passo + passo / 2 + (12 if estreita else 0)
        corpo = [area(0, y - passo / 2, largura, passo)]
        if estreita:
            corpo.append(t(esq, y - 24, x["nome"], fs, INK, weight="700"))
        else:
            corpo.append(t(esq - 14, y + 5, x["nome"], fs, INK, "end", "700"))
        cor = x.get("cor", INK)
        if barras:
            a, b = sorted((0, x["v"]))
            corpo.append(r(X(a), y - 11, max(X(b) - X(a), 2), 22, cor))
            lado = "start" if x["v"] >= 0 else "end"
            dx = 8 if x["v"] >= 0 else -8
            if x.get("ic"):
                c0, c1 = x["ic"]
                corpo.append(ln(X(c0), y, X(c1), y, INK, 2.5))
                corpo.append(ln(X(c0), y - 8, X(c0), y + 8, INK, 2.5))
                corpo.append(ln(X(c1), y - 8, X(c1), y + 8, INK, 2.5))
                fim_ = X(max(c1, x["v"])) if x["v"] >= 0 else X(min(c0, x["v"]))
            else:
                fim_ = X(x["v"])
            corpo.append(
                t(fim_ + dx, y + 5, x["rot"], fs - 1, INK, lado, "700", mono=True)
            )
        else:
            c0, c1 = x["ic"]
            corpo.append(ln(X(c0), y, X(c1), y, cor, 3, ' stroke-linecap="round"'))
            if x.get("bruto") is not None:
                xb = X(x["bruto"])
                corpo.append(
                    f'<path d="M{xb:.1f} {y - 8:.1f}l8 8l-8 8l-8 -8z" fill="{PAPER}" stroke="{CINZA_TXT}" stroke-width="2"/>'
                )
            corpo.append(
                f'<circle cx="{X(x["v"]):.1f}" cy="{y:.1f}" r="7" fill="{cor}"/>'
            )
            if estreita:
                corpo.append(
                    t(X(x["v"]), y + 26, x["rot"], 13, INK, "middle", "700", mono=True)
                )
            else:
                corpo.append(
                    t(
                        dir_ + 24,
                        y + 5,
                        x["rot"],
                        fs - 1,
                        INK,
                        "start",
                        "700",
                        mono=True,
                    )
                )
        out.append(hit("".join(corpo), keys[i]))
    out.append("</svg>")
    return "".join(out)


@registra("urna_reguas")
def urna_reguas(d, **_op) -> str:
    S = dado(d, "secoes")
    rg = S["urna"]["reguas"]
    itens = rg["itens"]
    tips = Tips()
    linhas, keys = [], []
    for i in itens:
        a, b = i["ic95"]
        linhas.append(
            {
                "nome": i["regua"][0].upper() + i["regua"][1:],
                "v": i["estimativa"],
                "ic": (a, b),
                "bruto": i.get("bruto"),
                "cor": FLAVIO,
                "rot": f"{_sinal(i['estimativa'])} ({_sinal(a)} a {_sinal(b)})",
            }
        )
        keys.append(
            tips.add(
                ficha(
                    i["regua"],
                    "urna mais nova menos a mais velha, Flávio em pontos",
                    [
                        ("Estimativa", f"{_sinal(i['estimativa'])} ponto"),
                        ("Intervalo de 95%", f"{_sinal(a)} a {_sinal(b)}"),
                        (
                            "Sem controle",
                            _sinal(i["bruto"]) if i.get("bruto") is not None else "s/d",
                        ),
                        ("Unidades", f"{inteiro(i['unidades'])} {i['unidade']}"),
                    ],
                )
            )
        )
    lim = rg["limiar_pp"]
    vals = [x for li in linhas for x in (*li["ic"], li["bruto"] or 0)]
    lo = -max(lim, -min(vals)) - 0.2
    hi = max(lim, max(vals)) + 0.2
    lo, hi = round(lo * 2) / 2 - 0.5, round(hi * 2) / 2 + 0.5

    def fmt(v: float) -> str:
        return _sinal(v, 1)

    titulo = "Urna mais nova contra a mais velha: quatro réguas"
    desc = (
        f"Diferença para Flávio, em pontos, pelas quatro réguas; todas dentro de ±{num(lim, 0)} ponto e com sinal que "
        "muda conforme o controle."
    )
    larga = _intervalo_svg(titulo, desc, linhas, keys, W, lo, hi, 0.5, fmt, (-lim, lim))
    estreita = _intervalo_svg(
        titulo, desc, linhas, keys, ESTREITA, lo, hi, 0.5, fmt, (-lim, lim)
    )
    legenda_ = (
        "Ponto azul e traço: estimativa e intervalo de 95% por bootstrap. Losango vazado: a mesma diferença sem "
        f"controle. Faixa clara: menos de {num(lim, 0)} ponto para cada lado. "
        f"{str(EXT.get(rg['positivas'], rg['positivas'])).capitalize()} réguas dão sinal positivo e {EXT.get(rg['negativas'], rg['negativas'])}, "
        "negativo; a maior em módulo é "
        f"{num(rg['max_abs_pp'], 2)} ponto. Fonte: secoes.json (urna.reguas)."
    )
    return figura_html(
        "urna_reguas", larga_estreita(larga, estreita), legenda_, tips, modo="full"
    )


# ------------------------------------------------------------------ cap. 13


@registra("terceira_via_reguas_totais")
def terceira_via_reguas_totais(d, **_op) -> str:
    TV = dado(d, "terceira_via")
    br = TV["reguas"]["totais"]["brasil"]
    dif = TV["prioridade"]["diferenca_nacional"]
    lo95, hi95 = br["urna_ic95"]
    linhas = [
        {"nome": "Pesquisa: matriz Nexus", "v": br["nexus"], "cor": ROXO},
        {
            "nome": "Pesquisa: Datafolha em Cury e Caiado",
            "v": br["datafolha"],
            "cor": TEAL,
        },
        {
            "nome": "Urna de 2022, por classe de margem",
            "v": br["urna"],
            "cor": INK,
            "ic": (lo95, hi95),
        },
        {"nome": "Urna de 2022, por região", "v": br["urna_regiao"], "cor": CINZA_TXT},
        {"nome": "Razão simples de 2022 (teto)", "v": br["razao_simples"], "cor": GOLD},
    ]
    tips = Tips()
    keys = []
    for x in linhas:
        x["rot"] = sinal_votos(x["v"])
        lin = [("Saldo para Flávio", f"{sinal_votos(x['v'])} votos")]
        if x.get("ic"):
            lin.append(
                ("Intervalo de 95%", f"{sinal_votos(lo95)} a {sinal_votos(hi95)}")
            )
        lin.append(("Diferença do 1º turno", f"{votos_curto(dif)} votos"))
        lin.append(("Terceira via de 2026", f"{inteiro(br['estoque'])} votos"))
        keys.append(
            tips.add(ficha(x["nome"], "saldo da terceira via no 2º turno", lin))
        )
    vals = [x["v"] for x in linhas] + [lo95, hi95, -dif]
    lo = (min(vals) // 1e6) * 1e6 - 1e6
    hi = (max(vals) // 1e6 + 1) * 1e6 + 1e6

    def fmt(v: float) -> str:
        return f"{_sinal(v / 1e6, 0)} mi" if v else "0"

    titulo = "O saldo da terceira via para Flávio, régua a régua"
    desc = (
        f"Saldo da terceira via para Flávio no 2º turno por cinco réguas, contra os {votos_curto(dif)} votos de "
        "diferença do 1º turno."
    )
    vert = [(-dif, f"Lula empata: −{votos_curto(dif)}")]
    larga = _intervalo_svg(
        titulo, desc, linhas, keys, W, lo, hi, 1e6, fmt, verticais=vert, barras=True
    )
    estreita = _intervalo_svg(
        titulo,
        desc,
        linhas,
        keys,
        ESTREITA,
        lo,
        hi,
        1e6,
        fmt,
        verticais=vert,
        barras=True,
    )
    legenda_ = (
        "Votos de terceira via do 1º turno que viram saldo para Flávio (positivo) ou Lula (negativo) no 2º turno, com "
        "as bases do 1º turno fixas. Pesquisa: a linha de cada candidatura aplicada a cada município. Urna de 2022: o "
        "que a terceira via rendeu a Bolsonaro entre os turnos de 2022, por regressão com efeito fixo de UF, com "
        "intervalo de 95%. Razão simples: todo o ganho entre os turnos creditado à terceira via. A linha tracejada é o "
        "saldo que Lula precisaria para empatar. Fonte: terceira_via.json (reguas.totais)."
    )
    return figura_html(
        "terceira_via_reguas_totais",
        larga_estreita(larga, estreita),
        legenda_,
        tips,
        modo="full",
    )
