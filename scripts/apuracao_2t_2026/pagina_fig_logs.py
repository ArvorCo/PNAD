"""Figuras do capítulo "O que os logs das 499 mil urnas dizem", blocos 1 a 3.

- ``logs_excecoes``: o que não fechou na leitura (cobertura e integridade);
- ``logs_regra2``: de 497.705 seções com ERRO ao erro técnico que sobra;
- ``logs_matriz``: atenção 0 a 3 no 1º turno contra o 2º, seção a seção;
- ``logs_persistencia``: os diagnósticos nos dois turnos, só no 1º, só no 2º.

SVG gerado aqui com os dados embutidos; a ficha é acréscimo do script da página.
Fonte única: ``analysis/apuracao_2t_2026/dados/logs.json``.
"""

from __future__ import annotations

from apuracao_2026.pagina_comum import CINZA, GOLD, INK, MUTED, inteiro, num
from apuracao_2026.pagina_fig_base import (
    GRADE,
    Tips,
    area,
    escala,
    ficha,
    figura_html,
    hit,
    legenda_html,
    ln,
    r,
    sobre,
    svg_abre,
    t,
)

TEAL = "#0c7a72"
VERMELHO = "#b02f21"
COR_1T = CINZA
COR_2T = INK
COR_SO2T = GOLD


def barras_h(
    nome: str,
    titulo: str,
    desc: str,
    linhas: list[tuple[str, float, str, str]],
    legenda: str,
    *,
    esq: int = 420,
    w: int = 1000,
    passo: int = 38,
    vmax: float | None = None,
    sufixo: str = "",
    apos: str = "",
) -> str:
    """Barras horizontais simples: (rótulo, valor, cor, nota da ficha)."""
    topo = 24
    h = topo + passo * len(linhas) + 16
    vmax = vmax or max([v for _, v, _, _ in linhas] + [1])
    x = escala(0, vmax, esq, w - 130)
    out = [svg_abre(w, h, titulo, desc)]
    tips = Tips()
    for i, (rot, v, cor, nota) in enumerate(linhas):
        y = topo + i * passo
        partes = [
            t(esq - 12, y + 19, rot, 14, INK, "end"),
            r(esq, y + 6, max(x(v) - esq, 0), 20, cor),
            t(
                max(x(v), esq) + 8,
                y + 21,
                f"{inteiro(v) if float(v).is_integer() else num(v, 2)}{sufixo}",
                14,
                INK,
                mono=True,
            ),
        ]
        k = tips.add(ficha(rot, "", [("valor", f"{inteiro(v)}{sufixo}")], nota))
        out.append(hit("".join(partes) + area(0, y, w, passo), k, foco=True))
    out.append(ln(esq, topo - 2, esq, h - 10, MUTED, 1))
    out.append("</svg>")
    return figura_html(nome, "".join(out), legenda, tips, minw=760, apos=apos)


# ------------------------------------------------------------------ 1. cobertura


def fig_excecoes(L: dict) -> str:
    c = L["cobertura"]
    sit = c["situacoes"]
    linhas = [
        (
            "seção não instalada (sem log)",
            sit.get("nao_instalada", 0),
            CINZA,
            "Seção marcada como não instalada no catálogo oficial.",
        ),
        (
            "BU do sistema de apuração, sem log de urna",
            sit.get("apuracao_sem_log", 0),
            CINZA,
            "Votação em cédula apurada pelo sistema da junta: não há log da urna de votação.",
        ),
        (
            "catálogo sem nome de log",
            sit.get("sem_nome", 0),
            CINZA,
            "Metadado oficial sem o nome do arquivo de log.",
        ),
        (
            "contagem do log diferente do BU",
            len(c["contagem_nao_confere"]),
            VERMELHO,
            "Em todas, o log tem menos cômputos que o BU; ver a tabela abaixo.",
        ),
        (
            "biometria sem as categorias no BU (exterior)",
            c["biometria_ausente_bu"],
            GOLD,
            "O BU do exterior não traz as contagens de habilitação: indisponível, não divergência.",
        ),
        (
            "biometria não conferida pela contagem",
            c["biometria_por_contagem"],
            VERMELHO,
            "As mesmas seis seções em que a contagem não fecha.",
        ),
        (
            "urna do BU ausente do log",
            c["lidos"] - c["urna_bu_no_log"],
            INK,
            "Número interno da urna do BU entre as urnas que escreveram o log.",
        ),
        (
            "código de carga do BU ausente do log",
            c["lidos"] - c["carga_bu_no_log"],
            INK,
            "Código de carga do BU registrado no log da mesma urna.",
        ),
        (
            "versão de software diferente de 10.23.0.0",
            c["lidos"] - max(c["versoes"].values()),
            INK,
            "Uma só versão em todas as urnas lidas.",
        ),
    ]
    legenda = (
        f"O que não fechou entre {inteiro(c['catalogadas'])} seções catalogadas e "
        f"{inteiro(c['lidos'])} logs lidos, em número de seções; zero é zero, não ausência de teste. "
        "Fonte: logs.json (cobertura)."
    )
    return barras_h(
        "logs_excecoes",
        "As exceções da leitura dos logs do 2º turno",
        "Barras horizontais com o número de seções em cada exceção da leitura; as três últimas são zero.",
        linhas,
        legenda,
    )


# ------------------------------------------------------------------ 2. regra 2


def fig_regra2(L: dict) -> str:
    g = L["regra2"]
    w, esq = 1000, 420
    total = g["secoes_com_erro"]
    mr = g["so_mr_antes_da_zeresima"]
    resto = g["erro_tecnico_regra2"]
    tipos = g["por_tipo"]
    topo = 70
    passo = 34
    h = topo + 10 + passo * (len(tipos) + 1) + 12
    x = escala(0, total, esq, w - 130)
    out = [
        svg_abre(
            w,
            h,
            "Erro registrado no log do 2º turno: o que é a urna religada e o que sobra",
            "Uma barra empilhada com as seções que só têm o erro de desmontar a memória de resultado antes "
            "da zerésima e as que sobram; abaixo, as que sobram por tipo de mensagem.",
        )
    ]
    tips = Tips()
    out.append(t(esq - 12, 30, "seções com ERRO ou FATAL no dia", 14, INK, "end"))
    k = tips.add(
        ficha(
            "Seções com ERRO ou FATAL no dia",
            f"{inteiro(total)} seções",
            [
                ("só o erro da MR antes da zerésima", inteiro(mr)),
                ("erro técnico pela regra 2", inteiro(resto)),
            ],
            "A urna foi religada no 2º turno com a carga de setembro; ao religar, registra o erro de desmontar a memória de resultado.",
        )
    )
    barra = r(esq, 14, x(mr) - esq, 24, CINZA) + r(
        x(mr), 14, x(total) - x(mr), 24, VERMELHO
    )
    barra += t(esq + 8, 31, f"{inteiro(mr)} só o erro da MR", 13, INK, weight="600")
    barra += t(x(total) + 8, 31, inteiro(total), 14, INK, mono=True)
    out.append(hit(barra + area(0, 8, w, 36), k, foco=True))
    out.append(
        t(
            esq + 8,
            62,
            f"as {inteiro(resto)} que sobram, por tipo de mensagem (uma seção pode ter mais de um tipo)",
            13,
            MUTED,
        )
    )
    vmax = max([x_["secoes"] for x_ in tipos] + [g["criterio_1t"], 1])
    xs = escala(0, vmax, esq, w - 130)
    linhas = [
        *[(x_["tipo"], x_["secoes"], VERMELHO) for x_ in tipos],
        ("referência: erro técnico no 1º turno (critério)", g["criterio_1t"], CINZA),
    ]
    for i, (rot, v, cor) in enumerate(linhas):
        y = topo + 10 + i * passo
        partes = [
            t(esq - 12, y + 17, rot, 13, INK, "end"),
            r(esq, y + 4, max(xs(v) - esq, 0), 18, cor),
            t(max(xs(v), esq) + 8, y + 18, inteiro(v), 13, INK, mono=True),
        ]
        k = tips.add(ficha(rot, "", [("seções", inteiro(v))]))
        out.append(hit("".join(partes) + area(0, y, w, passo), k, foco=True))
    out.append(ln(esq, 8, esq, h - 20, MUTED, 1))
    out.append("</svg>")
    legenda = (
        "Contagem de seções. A mensagem do GAP “Problema ao desmontar a MR” antes da zerésima saiu do "
        "critério de erro técnico na versão 2 das regras (26/10/2026) e ficou em contagem própria. O que "
        "sobra é dominado pela mesma mensagem depois da zerésima, quase sempre junto de um reinício. "
        "Fonte: logs.json (regra2)."
    )
    return figura_html("logs_regra2", "".join(out), legenda, tips, minw=760)


# ------------------------------------------------------------------ 3. matriz e persistência


def _cor_calor(frac: float) -> str:
    # papel → teal; seis degraus
    degraus = ["#f4f0e6", "#d9e8e1", "#b3d3c8", "#7fb6a8", "#2f7f73", "#0c5f57"]
    i = min(len(degraus) - 1, int(frac * (len(degraus) - 1) + 0.5))
    return degraus[i]


def fig_matriz(L: dict) -> str:
    m = L["persistencia"]["matriz"]
    esq, topo, cel = 200, 90, 120
    w, h = 760, topo + 4 * cel + 16
    out = [
        svg_abre(
            w,
            h,
            "Atenção dos logs no 1º turno contra o 2º, nas mesmas seções",
            "Matriz 4 por 4 com o número de seções em cada combinação de nível de atenção (0 a 3) "
            "no 1º turno (linhas) e no 2º turno (colunas), e a parcela da linha.",
        )
    ]
    out.append(t(esq + 2 * cel, 40, "2º turno", 15, INK, "middle", weight="700"))
    out.append(
        t(
            40,
            topo + 2 * cel,
            "1º turno",
            15,
            INK,
            "middle",
            weight="700",
            extra=f' transform="rotate(-90 40 {topo + 2 * cel})"',
        )
    )
    tips = Tips()
    for j in range(4):
        out.append(
            t(esq + j * cel + cel / 2, topo - 14, str(j), 15, INK, "middle", mono=True)
        )
    for i in range(4):
        out.append(
            t(esq - 14, topo + i * cel + cel / 2 + 5, str(i), 15, INK, "end", mono=True)
        )
        tot = sum(m.get(f"{i}x{j}", 0) for j in range(4)) or 1
        for j in range(4):
            v = m.get(f"{i}x{j}", 0)
            frac = v / tot
            cor = _cor_calor(frac)
            tx = sobre(cor)
            x0, y0 = esq + j * cel, topo + i * cel
            partes = [
                r(x0, y0, cel - 3, cel - 3, cor, f' stroke="{GRADE}"'),
                t(
                    x0 + cel / 2,
                    y0 + cel / 2 - 2,
                    inteiro(v),
                    16,
                    tx,
                    "middle",
                    weight="700",
                    mono=True,
                ),
                t(
                    x0 + cel / 2,
                    y0 + cel / 2 + 20,
                    f"{num(100 * frac, 1)}%",
                    13,
                    tx,
                    "middle",
                    mono=True,
                ),
            ]
            k = tips.add(
                ficha(
                    f"Atenção {i} no 1º turno, {j} no 2º",
                    f"{inteiro(v)} seções",
                    [("parcela da linha", f"{num(100 * frac, 2)}%")],
                )
            )
            out.append(hit("".join(partes), k, foco=True))
    out.append("</svg>")
    p = L["persistencia"]["persistencia"]
    legenda = (
        f"{inteiro(L['persistencia']['nos_dois'])} seções com log lido nos dois turnos. A porcentagem é da linha: "
        f"das {inteiro(p['atencao_2_ou_mais']['secoes_1t'])} seções com atenção 2 ou mais no 1º turno, "
        f"{num(p['atencao_2_ou_mais']['pct_2t_dado_1t'], 1)}% repetem 2 ou mais no 2º, contra "
        f"{num(p['atencao_2_ou_mais']['pct_2t_geral'], 1)}% no geral. Atenção é ordenação para fiscalização "
        "(0 rotina, 1 um tipo de sinal, 2 dois tipos, 3 conferência do arquivo ou três tipos), não "
        "probabilidade de irregularidade. Fonte: comparacao_turnos.json."
    )
    return figura_html(
        "logs_matriz", "".join(out), legenda, tips, modo="fit", dim=False
    )


def fig_persistencia(L: dict) -> str:
    diag = [
        d
        for d in L["persistencia"]["diagnosticos"]
        if d["total_1t"] + d["total_2t"] > 0
    ]
    w, esq, dir_ = 1100, 430, 170
    topo, passo = 50, 36
    h = topo + passo * len(diag) + 30
    vmax = max(d["so_1t"] + d["ambos"] + d["so_2t"] for d in diag)
    x = escala(0, vmax, esq, w - dir_)
    out = [
        svg_abre(
            w,
            h,
            "Os diagnósticos dos logs nos dois turnos",
            "Para cada diagnóstico, barra empilhada: seções só no 1º turno, nos dois e só no 2º turno; "
            "à direita, a parcela das seções do 1º turno que repetiram no 2º.",
        )
    ]
    out.append(t(w - dir_ + 14, topo - 18, "repetiu no 2º", 13, MUTED))
    tips = Tips()
    for i, d in enumerate(diag):
        y = topo + i * passo
        x1 = x(d["so_1t"])
        x2 = x(d["so_1t"] + d["ambos"])
        x3 = x(d["so_1t"] + d["ambos"] + d["so_2t"])
        partes = [
            t(esq - 12, y + 17, d["curto"], 13, INK, "end"),
            r(esq, y + 4, x1 - esq, 18, COR_1T),
            r(x1, y + 4, x2 - x1, 18, COR_2T),
            r(x2, y + 4, x3 - x2, 18, COR_SO2T),
            t(
                w - dir_ + 14,
                y + 18,
                "n/d" if d["pct_persiste"] is None else f"{num(d['pct_persiste'], 1)}%",
                13,
                INK,
                mono=True,
            ),
        ]
        k = tips.add(
            ficha(
                d["nome"],
                "seções",
                [
                    ("só no 1º turno", inteiro(d["so_1t"])),
                    ("nos dois turnos", inteiro(d["ambos"])),
                    ("só no 2º turno", inteiro(d["so_2t"])),
                    (
                        "repetiu no 2º (das do 1º)",
                        (
                            "n/d"
                            if d["pct_persiste"] is None
                            else f"{num(d['pct_persiste'], 1)}%"
                        ),
                    ),
                ],
            )
        )
        out.append(hit("".join(partes) + area(0, y, w, passo), k, foco=True))
    out.append(ln(esq, topo - 4, esq, h - 20, MUTED, 1))
    out.append("</svg>")
    leg = legenda_html(
        [
            ("só no 1º turno", COR_1T),
            ("nos dois turnos", COR_2T),
            ("só no 2º turno", COR_SO2T),
        ]
    )
    zeros = L["persistencia"]["sem_ocorrencia_nos_dois"]
    legenda = (
        "Seções com o diagnóstico em cada turno, nas mesmas seções. O que persiste aponta mais para o "
        "equipamento, o prédio ou a rotina da mesa do que para o dia; a regra não separa essas causas. "
        f"{len(zeros)} diagnósticos não marcaram seção alguma em nenhum dos turnos (os quatro de rapidez "
        "entre eles). Fonte: comparacao_turnos.json."
    )
    return figura_html(
        "logs_persistencia", "".join(out), legenda, tips, minw=860, apos=leg
    )
