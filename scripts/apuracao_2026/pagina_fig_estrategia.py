"""Figuras dos capítulos 12 e 13: atributos das zonas atípicas e o caminho do 2º turno.

Os cenários de 2º turno combinam duas matrizes publicadas (Nexus e Datafolha)
com três hipóteses declaradas para a parcela que não escolhe; nada aqui é
previsão. O estoque é medido na escala do voto de 2022 e não identifica eleitor.
"""

from __future__ import annotations

import math

from .pagina_comum import NOME_UF, inteiro, num
from .pagina_fig_base import (
    FLAVIO,
    GRADE,
    INK,
    LULA,
    MUTED,
    Tips,
    W,
    area,
    dado,
    escala,
    ficha,
    figura_html,
    hit,
    legenda,
    ln,
    nome_bonito,
    pct,
    pp,
    r,
    registra,
    sobre,
    svg_abre,
    t,
    ticks,
)

ROT_HIPOTESE = {
    "fica_fora": "só o medido",
    "proporcional": "não escolha proporcional",
    "meio_a_meio": "não escolha meio a meio",
}
ROT_MATRIZ = {"nexus": "Nexus", "datafolha": "Datafolha"}
GOLD = "#7d5b00"


# ------------------------------------------------------------------ 12 atributos das zonas

NEG = ["#1f5f78", "#3f7591", "#a9c9d3"]
POS = ["#f0c39a", "#d0864a", "#9a4a12"]
CORTES_Z = [-4, -2.5, -1.5, 1.5, 2.5, 4]


def cor_z(z: float) -> str:
    if z <= CORTES_Z[0]:
        return NEG[0]
    if z <= CORTES_Z[1]:
        return NEG[1]
    if z <= CORTES_Z[2]:
        return NEG[2]
    if z < CORTES_Z[3]:
        return "#efeadf"
    if z < CORTES_Z[4]:
        return POS[0]
    if z < CORTES_Z[5]:
        return POS[1]
    return POS[2]


ROT_CURTO = {
    "d_flavio_1t": "Flávio − Bols. 1º t.",
    "d_flavio_2t": "Flávio − Bols. 2º t.",
    "d_lula_1t": "Lula − Lula 1º t.",
    "d_lula_2t": "Lula − Lula 2º t.",
    "residuo_hierarquico": "resíduo local",
    "d_comparecimento": "comparecimento",
    "brancos_nulos": "brancos e nulos",
    "d_brancos_nulos": "Δ brancos e nulos",
    "terceiros": "terceira via",
    "log_var_eleitorado": "eleitorado",
    "log_atraso": "atraso",
    "versoes_residuo": "versões",
}


@registra("anomalias_features")
def anomalias_features(d, **_op) -> str:
    A = dado(d, "anomalias")
    topo_z = A["topo"][:25]
    feats = list(A["metodo"]["atributos"].keys())
    esq, topo = 300, 150
    cw, ch = (W - esq - 20) / len(feats), 28
    h = topo + ch * len(topo_z) + 70
    out = [
        svg_abre(
            W,
            h,
            "Atributos das 25 zonas mais atípicas, em z robusto dentro da UF",
            "Cada célula é o z de um atributo; laranja acima da mediana da UF, azul abaixo; perto de zero fica neutro.",
        )
    ]
    for j, f in enumerate(feats):
        x = esq + j * cw + cw / 2
        out.append(
            t(
                x,
                topo - 12,
                ROT_CURTO.get(f, f),
                13,
                INK,
                "start",
                "600",
                extra=f' transform="rotate(-40 {x:.1f} {topo - 12})"',
            )
        )
    tips = Tips()
    linhas = []
    for i, z in enumerate(topo_z):
        y = topo + i * ch
        nome = f"{z['posicao']}. {nome_bonito(z['municipio'])} ({z['uf']})"
        out.append(t(esq - 12, y + ch / 2 + 5, nome, 13.5, INK, "end"))
        for j, f in enumerate(feats):
            v = z["z"].get(f, 0) or 0
            cor = cor_z(v)
            x = esq + j * cw
            bruto = z["atributos_pp"].get(f)
            desc = A["metodo"]["atributos"][f]["descricao"]
            unid = A["metodo"]["atributos"][f].get("unidade", "")
            linhas.append(
                [
                    f"{nome_bonito(z['municipio'])} ({z['uf']}), zona {int(z['zona'])}",
                    desc,
                    num(v, 2),
                    f"{num(bruto, 2)} {unid}" if bruto is not None else "",
                    num(z["escore"], 1),
                ]
            )
            cel = r(x + 1, y + 1, cw - 2, ch - 2, cor)
            if abs(v) >= 1.5:
                cel += t(
                    x + cw / 2,
                    y + ch / 2 + 5,
                    num(v, 1),
                    13,
                    sobre(cor),
                    "middle",
                    "600",
                    mono=True,
                )
            out.append(f'<g class="hit" data-k="r{len(linhas) - 1}">{cel}</g>')
    yl = topo + ch * len(topo_z) + 30
    itens = [
        ("z ≤ −4", NEG[0]),
        ("−4 a −2,5", NEG[1]),
        ("−2,5 a −1,5", NEG[2]),
        ("perto de zero", "#efeadf"),
        ("1,5 a 2,5", POS[0]),
        ("2,5 a 4", POS[1]),
        ("z ≥ 4", POS[2]),
    ]
    out.append(legenda(itens, esq, yl, 13))
    out.append("</svg>")
    tips.tabela(
        ["Zona", "Atributo", "z robusto na UF", "Valor", "Escore da zona"],
        linhas,
        sub=1,
    )
    legenda_ = (
        "z robusto (mediana e desvio absoluto mediano dentro da UF) de cada atributo nas 25 zonas de escore mais alto. "
        f"{A['aviso']} Fonte: anomalias.json."
    )
    return figura_html(
        "anomalias_features", "".join(out), legenda_, tips, minw=900, dim=False
    )


# ------------------------------------------------------------------ 13 cenários


@registra("transferencia_cenarios")
def transferencia_cenarios(d, **_op) -> str:
    E = dado(d, "estrategia_2t")
    proj = E["aritmetica"]["projecoes"]
    esq, topo, passo = 330, 70, 46
    h = topo + passo * len(proj) + 50
    # barra 100% começa no zero: a diferença entre as cores é a diferença real
    lo, hi = 0, 100
    X = escala(lo, hi, esq, W - 60)
    out = [
        svg_abre(
            W,
            h,
            "Seis cenários de 2º turno a partir do 1º turno e de matrizes publicadas",
            "Barra dividida em Flávio e Lula nos válidos projetados; linha a 50%.",
        ),
        legenda([("Flávio", FLAVIO), ("Lula", LULA)], esq, 24),
    ]
    for v in ticks(lo, hi, 4):
        out.append(ln(X(v), topo - 6, X(v), h - 34, GRADE))
        out.append(t(X(v), h - 14, f"{num(v, 0)}%", 13, MUTED, "middle", mono=True))
    tips = Tips()
    for i, p in enumerate(proj):
        y = topo + i * passo
        xf = X(p["flavio_pct"])
        rot = f"{ROT_MATRIZ.get(p['matriz'], p['matriz'])} · {ROT_HIPOTESE.get(p['hipotese'], p['hipotese'])}"
        corpo = (
            t(esq - 12, y + 25, rot, 14, INK, "end")
            + r(esq, y + 6, xf - esq, passo - 14, FLAVIO)
            + r(xf, y + 6, W - 60 - xf, passo - 14, LULA)
            + t(
                esq + 10,
                y + 26,
                f"{num(p['flavio_pct'], 2)}%",
                14,
                "#ffffff",
                weight="700",
                mono=True,
            )
            + t(
                W - 70,
                y + 26,
                f"{num(p['lula_pct'], 2)}%",
                14,
                "#ffffff",
                "end",
                "700",
                mono=True,
            )
        )
        k = tips.add(
            ficha(
                rot,
                "projeção sob hipótese",
                [
                    ("Flávio", f"{inteiro(p['flavio'])} ({pct(p['flavio_pct'])})"),
                    ("Lula", f"{inteiro(p['lula'])} ({pct(p['lula_pct'])})"),
                    (
                        "Margem",
                        f"{inteiro(p['margem_votos'])} votos · {pp(p['margem_pp'])}",
                    ),
                    (
                        "Ganho sobre o 1º turno",
                        f"Flávio +{inteiro(p['ganho_flavio'])} · Lula +{inteiro(p['ganho_lula'])}",
                    ),
                    ("Válidos projetados", inteiro(p["validos"])),
                ],
                E["aritmetica"]["hipoteses"].get(p["hipotese"], ""),
            )
        )
        out.append(hit(area(0, y, W, passo) + corpo, k, foco=True))
    out.append(ln(X(50), topo - 12, X(50), h - 34, "#ffffff", 2))
    out.append(ln(X(50), topo - 12, X(50), topo - 2, INK, 2))
    out.append(t(X(50), topo - 18, "50%", 13, INK, "middle", "700"))
    out.append("</svg>")
    eq = E["aritmetica"]["equilibrio"]
    legenda_ = (
        "Cada linha aplica aos votos de terceiros do 1º turno uma matriz de transferência publicada (Nexus/BTG p. 79 ou Datafolha) "
        f"e uma hipótese para quem não escolheu. Para empatar, Lula precisaria de {pct(eq['lula_precisa_entre_quem_escolhe_pct'], 1)} "
        "dos terceiros que escolhem. Aritmética sob hipóteses, não previsão. Fonte: estrategia_2t.json."
    )
    return figura_html(
        "transferencia_cenarios", "".join(out), legenda_, tips, minw=820, dim=False
    )


@registra("estoque_uf")
def estoque_uf(d, **_op) -> str:
    E = dado(d, "estrategia_2t")["geografia"]
    ufs = sorted(E["ufs"], key=lambda u: (-u["estoque_flavio"], -u["estoque_lula"]))
    esq, topo, passo = 200, 60, 26
    h = topo + passo * len(ufs) + 50
    vmax = max(max(u["estoque_flavio"], u["estoque_lula"]) for u in ufs)
    vmax = math.ceil(vmax / 200000) * 200000
    # folga de 84 de cada lado para o rótulo de valor, que nunca encosta no nome
    ini, fim = esq + 84, W - 100
    meio = (ini + fim) / 2
    XL = escala(0, vmax, meio, ini)
    XF = escala(0, vmax, meio, fim)
    out = [
        svg_abre(
            W,
            h,
            "Estoque de 2022 por UF: votos que faltam a Flávio e a Lula na escala do 2º turno de 2022",
            "À direita, o estoque de Flávio; à esquerda, o de Lula; em votos.",
        ),
        t(meio + 8, 30, "estoque de Flávio →", 14, FLAVIO, weight="700"),
        t(meio - 8, 30, "← estoque de Lula", 14, LULA, "end", "700"),
    ]
    for v in ticks(0, vmax, 4):
        for X in (XL, XF) if v else (XF,):
            out.append(ln(X(v), topo - 6, X(v), h - 34, GRADE))
            out.append(
                t(
                    X(v),
                    h - 14,
                    f"{num(v / 1000, 0)} mil" if v else "0",
                    13,
                    MUTED,
                    "middle",
                    mono=True,
                )
            )
    tips = Tips()
    for i, u in enumerate(ufs):
        y = topo + i * passo
        corpo = (
            r(meio, y + 4, XF(u["estoque_flavio"]) - meio, passo - 8, FLAVIO)
            + r(
                XL(u["estoque_lula"]),
                y + 4,
                meio - XL(u["estoque_lula"]),
                passo - 8,
                LULA,
            )
            + t(esq - 12, y + 18, NOME_UF[u["uf"]], 13.5, INK, "end")
        )
        if u["estoque_flavio"]:
            corpo += t(
                XF(u["estoque_flavio"]) + 6,
                y + 18,
                inteiro(u["estoque_flavio"]),
                13,
                INK,
                mono=True,
            )
        if u["estoque_lula"]:
            corpo += t(
                XL(u["estoque_lula"]) - 6,
                y + 18,
                inteiro(u["estoque_lula"]),
                13,
                INK,
                "end",
                mono=True,
            )
        k = tips.add(
            ficha(
                f"{NOME_UF[u['uf']]} ({u['uf']})",
                u["regiao"],
                [
                    (
                        "Flávio 2026 · Bolsonaro 2022 (2º t.)",
                        f"{pct(u['flavio_pct'])} · {pct(u['bolsonaro_2022_2t_pct'])}",
                    ),
                    (
                        "Lula 2026 · Lula 2022 (2º t.)",
                        f"{pct(u['lula_pct'])} · {pct(u['lula_2022_2t_pct'])}",
                    ),
                    ("Estoque de Flávio", inteiro(u["estoque_flavio"])),
                    ("Estoque de Lula", inteiro(u["estoque_lula"])),
                    (
                        "Já supera Bolsonaro no 2º t.",
                        "sim" if u["ja_supera_bolsonaro_2t"] else "não",
                    ),
                ],
            )
        )
        out.append(hit(area(0, y, W, passo) + corpo, k))
    out.append(ln(meio, topo - 6, meio, h - 34, INK, 1.4))
    out.append("</svg>")
    est = E["estoque"]
    legenda_ = (
        f"Estoque = votos do candidato de 2022 no 2º turno × a fração de parcela que ainda falta em 2026. Somado: "
        f"{inteiro(est['total_ufs'])} para Flávio e {inteiro(est['total_lula_ufs'])} para Lula. Não identifica eleitor; "
        "onde o candidato já passou de 2022 o estoque é zero. Fonte: estrategia_2t.json."
    )
    x_lula = XL(max(u["estoque_lula"] for u in ufs)) - 74
    return figura_html(
        "estoque_uf",
        "".join(out),
        legenda_,
        tips,
        minw=820,
        foco=(x_lula, meio + 4, meio + 4),
    )


ANALOGIA = "#6b4a92"


def _rotulo_duplo(x: float, y: float, s: str, n: int = 46) -> str:
    """Rótulo à direita em uma ou duas linhas, sem cortar palavra."""
    if len(s) <= n:
        return t(x, y, s, 14, INK, "end")
    palavras, a = s.split(), ""
    while palavras and len(a) + len(palavras[0]) + 1 <= n:
        a = f"{a} {palavras.pop(0)}".strip()
    return t(x, y - 9, a, 13.5, INK, "end") + t(
        x, y + 9, " ".join(palavras), 13.5, INK, "end"
    )


def _cor_rotulo(rotulo: str) -> str:
    if "analogia" in rotulo:
        return ANALOGIA
    if "hipótese" in rotulo:
        return GOLD
    return FLAVIO


def _onde(o: dict) -> str:
    nome = o.get("uf") or nome_bonito(o.get("municipio", "?"))
    v = o.get("votos") or o.get("vao_votos") or o.get("saldo_flavio") or 0
    return f"{nome} {inteiro(v)}"


@registra("movimentos_2t")
def movimentos_2t(d, **_op) -> str:
    M = sorted(
        dado(d, "estrategia_2t")["movimentos"], key=lambda m: -m["votos_esperados"]
    )
    esq, topo, passo = 420, 50, 44
    h = topo + passo * len(M) + 46
    vmax = math.ceil(max(m["votos_esperados"] for m in M) / 250000) * 250000
    X = escala(0, vmax, esq, W - 140)
    out = [
        svg_abre(
            W,
            h,
            "Dez movimentos para o 2º turno, por votos esperados",
            "Barras em votos esperados pela regra declarada de cada movimento; cor pelo tipo de enunciado.",
        ),
        legenda(
            [
                ("inferência sobre medição publicada", FLAVIO),
                ("hipótese declarada", GOLD),
                ("analogia histórica", ANALOGIA),
            ],
            esq - 400,
            24,
            13,
        ),
    ]
    for v in ticks(0, vmax, 5):
        out.append(ln(X(v), topo - 4, X(v), h - 34, GRADE))
        out.append(
            t(
                X(v),
                h - 14,
                f"{num(v / 1e6, 2)} mi" if v else "0",
                13,
                MUTED,
                "middle",
                mono=True,
            )
        )
    tips = Tips()
    for i, m in enumerate(M):
        y = topo + i * passo
        cor = _cor_rotulo(m.get("rotulo") or "")
        titulo = m["titulo"]
        corpo = (
            _rotulo_duplo(esq - 12, y + 26, titulo)
            + r(esq, y + 8, X(m["votos_esperados"]) - esq, passo - 16, cor)
            + t(
                X(m["votos_esperados"]) + 8,
                y + 27,
                inteiro(m["votos_esperados"]),
                14,
                INK,
                mono=True,
            )
        )
        linhas = [
            ("Votos esperados", inteiro(m["votos_esperados"])),
            ("Alvo", m.get("alvo", "")),
        ]
        if m.get("teto"):
            linhas.append(("Teto", inteiro(m["teto"])))
        if m.get("onde"):
            linhas.append(("Onde", ", ".join(_onde(o) for o in m["onde"][:4])))
        k = tips.add(ficha(titulo, m.get("rotulo", ""), linhas, m.get("regra", "")))
        out.append(hit(area(0, y, W, passo) + corpo, k, foco=True))
    out.append("</svg>")
    legenda_ = (
        "Votos esperados de cada movimento pela regra escrita na ficha; os movimentos se sobrepõem e não se somam. "
        "Juízo editorial sobre aritmética pública. Fonte: estrategia_2t.json."
    )
    return figura_html("movimentos_2t", "".join(out), legenda_, tips, minw=860)
