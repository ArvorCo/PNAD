"""Figuras dos cards 17 a 24 da super thread: fechamento tardio, lentidão,
limites, checklist e os quatro cards do 2º turno."""

from __future__ import annotations

from .thread_base import (
    CINZA,
    FLAVIO,
    GOLD,
    GOLD_FILL,
    GRID,
    INK,
    LULA,
    MONO,
    MUTED,
    OUTROS,
    PAPER,
    PAPER2,
    WHITE,
    W,
    circ,
    dado,
    etiqueta,
    legenda,
    ln,
    mi_curto,
    nome_proprio,
    num,
    pct,
    r,
    sinal,
    svg,
    t,
)

# ------------------------------------------------------------------ 17 fechamento


def fig_fechamento() -> str:
    f = dado("fechamento")
    lh = f["lula_hora"]
    bruta = [
        x for x in lh["bruta"] if x["grupo"] == "Brasil" and x["lula_pct"] is not None
    ]
    out = [t(0, 24, "Lula nos válidos, pela hora do último voto", 17, INK, 700)]
    x0, base, esc = 10, 470, 5.4
    bw = 96
    for i, x in enumerate(bruta):
        xx = x0 + i * (bw + 14)
        hh = x["lula_pct"] * esc
        out.append(r(xx, base - hh, bw, hh, LULA, 3))
        out.append(
            t(
                xx + bw / 2,
                base - hh - 10,
                pct(x["lula_pct"], 1),
                18,
                LULA,
                800,
                "middle",
                MONO,
            )
        )
        out.append(
            t(
                xx + bw / 2,
                base + 24,
                x["faixa"].replace("depois de ", "após "),
                14,
                INK,
                600,
                "middle",
            )
        )
        out.append(
            t(
                xx + bw / 2,
                base + 44,
                f"{num(x['secoes'])}",
                13,
                MUTED,
                500,
                "middle",
                MONO,
            )
        )
    out.append(ln(x0, base, x0 + 4 * (bw + 14) - 14, base, INK, 1.5))
    out.append(
        t(
            0,
            560,
            "Seções por faixa embaixo. Bruto: mistura lugar, tamanho e distância.",
            15,
            MUTED,
            600,
        )
    )
    inc = {x["id"]: x["lula"]["coeficientes"]["horas_atraso"] for x in lh["inclinacao"]}
    est = {x["id"]: x["resultado"]["lula_pp"] for x in f["voto"]["estimadores"]}
    linhas = [
        ("Sem controle", inc["bruta"], "por hora de atraso"),
        ("Dentro da zona", inc["zona"], "por hora de atraso"),
        ("Zona, tamanho e local", inc["zona_controles"], "por hora de atraso"),
        (
            "Seção tardia em 2022",
            est["recebimento_decil_2022"],
            "contra a própria zona",
        ),
        (
            "Seção tardia em 2026",
            est["recebimento_decil_2026"],
            "contra a própria zona",
        ),
    ]
    px0, px1 = 640, 980
    vmax = 16

    def sx(v):
        return px0 + (px1 - px0) * v / vmax

    out.append(t(470, 24, "O que sobra com controles, pontos de Lula", 17, INK, 700))
    for v in (0, 4, 8, 12, 16):
        out.append(
            ln(
                sx(v),
                50,
                sx(v),
                470,
                GRID if v else INK,
                1.5 if not v else 1,
                None if not v else "3 5",
            )
        )
        out.append(t(sx(v), 494, f"+{v}" if v else "0", 14, MUTED, 600, "middle", MONO))
    y = 84
    for i, (nome, e, sub) in enumerate(linhas):
        cor = LULA if i == 0 else (GOLD if i >= 3 else FLAVIO)
        out.append(t(px0 - 12, y + 2, nome, 16, INK, 700, "end"))
        out.append(t(px0 - 12, y + 22, sub, 13, MUTED, 500, "end"))
        lo, hi = e["ic95"]
        out.append(ln(sx(lo), y, sx(hi), y, cor, 6))
        out.append(
            circ(sx(e["estimativa"]), y, 9, cor, f' stroke="{PAPER}" stroke-width="3"')
        )
        if e["estimativa"] > 10:
            out.append(
                t(
                    sx(lo) - 12,
                    y + 6,
                    sinal(e["estimativa"], 1),
                    16,
                    cor,
                    700,
                    "end",
                    MONO,
                )
            )
        else:
            out.append(
                t(
                    sx(hi) + 12,
                    y + 6,
                    sinal(e["estimativa"], 1),
                    16,
                    cor,
                    700,
                    "start",
                    MONO,
                )
            )
        y += 80
    out.append(
        t(
            470,
            560,
            "Com controles, sobra um quinto; e 2022 já mostrava o mesmo.",
            15,
            INK,
            600,
        )
    )
    return svg("".join(out), "Fechamento tardio e voto em Lula")


# ------------------------------------------------------------------ 18 lentidão


def fig_lentidao() -> str:
    lt = dado("lentidao_ufs")
    ufs = sorted(lt["ufs"], key=lambda u: u["marcos"]["2026_totalizado"]["99"])
    n = len(ufs)
    x0, x1 = 64, 990
    passo = (x1 - x0) / n
    y0, y1 = 60, 470
    m0, m1 = 60, 420

    def sy(m):
        return y0 + (y1 - y0) * (m - m0) / (m1 - m0)

    out = [
        t(
            0,
            24,
            "Hora em que cada UF passou de 99% das seções totalizadas",
            17,
            INK,
            700,
        )
    ]
    for m in range(m0, m1 + 1, 60):
        y = sy(m)
        hh = (17 * 60 + m) // 60 % 24
        out.append(ln(x0, y, x1, y, GRID, 1, "3 5"))
        out.append(t(x0 - 10, y + 5, f"{hh:02d}h", 15, MUTED, 600, "end", MONO))
    for i, u in enumerate(ufs):
        cx = x0 + passo * (i + 0.5)
        a = u["marcos"]["2022_totalizado"]["99"]
        b = u["marcos"]["2026_totalizado"]["99"]
        out.append(ln(cx, sy(a), cx, sy(b), "#9db4d8", 5))
        out.append(circ(cx, sy(a), 8, WHITE, f' stroke="{CINZA}" stroke-width="3"'))
        out.append(circ(cx, sy(b), 8, FLAVIO))
        out.append(t(cx, y1 + 30, u["uf"], 14, INK, 700, "middle", MONO))
    r99 = lt["resumo_99"]
    out.append(
        etiqueta(
            x1,
            y0 + 30,
            f"{r99['mais_rapidas_em_2026']} de {n} UFs mais rápidas em 2026",
            18,
            FLAVIO,
            anchor="end",
            weight=800,
        )
    )
    out.append(legenda([("2022", CINZA), ("2026", FLAVIO)], x0, 580, 16))
    return svg("".join(out), "Lentidão por UF em 2022 e 2026")


# ------------------------------------------------------------------ 19 limites


def fig_limites(colunas: list[tuple[str, str, list[str]]]) -> str:
    out = []
    cw = 240
    for i, (titulo, cor, itens) in enumerate(colunas):
        x = i * (cw + 13)
        out.append(r(x, 0, cw, 560, PAPER2, 10))
        out.append(r(x, 0, cw, 10, cor, 4))
        out.append(t(x + 18, 50, titulo, 22, cor, 800))
        y = 92
        for item in itens:
            linhas = _quebra(item, 21)
            out.append(circ(x + 22, y - 7, 6, cor))
            for k, s in enumerate(linhas):
                out.append(t(x + 36, y + k * 26, s, 19, INK, 500))
            y += 26 * len(linhas) + 26
    return svg("".join(out), "O que os dados provam e o que não provam")


def _quebra(s: str, n: int) -> list[str]:
    palavras, linhas, atual = s.split(), [], ""
    for p in palavras:
        if len(atual) + len(p) + 1 > n and atual:
            linhas.append(atual)
            atual = p
        else:
            atual = f"{atual} {p}".strip()
    if atual:
        linhas.append(atual)
    return linhas


# ------------------------------------------------------------------ 20 checklist


def fig_checklist(etapas: list[tuple[str, str, str]]) -> str:
    out = []
    n = len(etapas)
    y = 22
    passo = 570 / n
    for i, (titulo, numero, sub) in enumerate(etapas):
        yy = y + i * passo
        out.append(r(0, yy, W, passo - 12, WHITE if i % 2 else PAPER2, 8))
        out.append(circ(40, yy + (passo - 12) / 2, 20, FLAVIO))
        out.append(
            t(40, yy + (passo - 12) / 2 + 7, str(i + 1), 20, WHITE, 800, "middle", MONO)
        )
        out.append(t(80, yy + (passo - 12) / 2 - 4, titulo, 20, INK, 700))
        out.append(t(80, yy + (passo - 12) / 2 + 20, sub, 15, MUTED, 500))
        out.append(
            t(W - 20, yy + (passo - 12) / 2 + 10, numero, 26, FLAVIO, 800, "end", MONO)
        )
    return svg("".join(out), "Como conferir cada número")


# ------------------------------------------------------------------ 21 aritmética do 2º turno


def fig_aritmetica() -> str:
    e = dado("estrategia_2t")["aritmetica"]
    proj = next(
        p
        for p in e["projecoes"]
        if p["matriz"] == "nexus" and p["hipotese"] == "fica_fora"
    )
    det = proj["detalhe"]
    nomes = {
        "ESCRITOR AUGUSTO CURY": "Cury",
        "RENAN SANTOS": "Renan",
        "RONALDO CAIADO": "Caiado",
        "ZEMA": "Zema",
    }
    linhas = [d for d in det if d["origem"] in nomes]
    resto = [d for d in det if d["origem"] not in nomes]
    if resto:
        linhas.append(
            {
                "origem": "Demais",
                "votos_1t": sum(d["votos_1t"] for d in resto),
                "para_flavio": sum(d["para_flavio"] for d in resto),
                "para_lula": sum(d["para_lula"] for d in resto),
                "fora": sum(d["fora"] for d in resto),
            }
        )
    x0, x1 = 120, 860
    vmax = max(d["votos_1t"] for d in linhas)
    esc = (x1 - x0) / vmax
    out = [
        t(
            0,
            24,
            "Para onde vai a terceira via pela matriz da Nexus, votos",
            17,
            INK,
            700,
        )
    ]
    y = 50
    for d in linhas:
        nome = nomes.get(d["origem"], d["origem"])
        out.append(t(x0 - 12, y + 26, nome, 19, INK, 700, "end"))
        xx = x0
        for k, cor in (
            ("para_flavio", FLAVIO),
            ("para_lula", LULA),
            ("fora", "#c9c1ad"),
        ):
            w = d[k] * esc
            out.append(r(xx, y + 8, w, 30, cor))
            if w > 70:
                out.append(
                    t(
                        xx + w / 2,
                        y + 29,
                        mi_curto(d[k], 1),
                        14,
                        WHITE if k != "fora" else INK,
                        700,
                        "middle",
                        MONO,
                    )
                )
            xx += w
        out.append(
            t(
                xx + 10,
                y + 29,
                mi_curto(d["votos_1t"], 2),
                15,
                MUTED,
                600,
                "start",
                MONO,
            )
        )
        y += 52
    eq = e["equilibrio"]
    yb = 340
    out.append(r(0, yb, W, 230, PAPER2, 10))
    out.append(
        t(
            30,
            yb + 46,
            "Para virar só com esses votos, Lula precisaria de",
            19,
            INK,
            600,
        )
    )
    out.append(
        t(
            30,
            yb + 120,
            pct(eq["lula_precisa_se_todos_votarem_pct"], 0),
            76,
            LULA,
            800,
            "start",
            MONO,
        )
    )
    out.append(t(260, yb + 96, "de todos, se todos votassem.", 19, INK, 600))
    out.append(
        t(
            260,
            yb + 124,
            f"A Nexus mede {pct(eq['lula_medido_entre_quem_escolhe_pct'], 0)} entre os que escolhem.",
            19,
            INK,
            600,
        )
    )
    out.append(
        t(
            30,
            yb + 190,
            f"Só com o medido: Flávio {pct(proj['flavio_pct'])} × Lula {pct(proj['lula_pct'])} dos válidos",
            20,
            FLAVIO,
            800,
        )
    )
    out.append(
        legenda(
            [
                ("Flávio", FLAVIO),
                ("Lula", LULA),
                ("Branco, nulo ou indeciso", "#c9c1ad"),
            ],
            0,
            596,
            15,
        )
    )
    return svg("".join(out), "Aritmética do 2º turno")


# ------------------------------------------------------------------ 22 réguas


def fig_reguas() -> str:
    tv = dado("terceira_via")
    grupos = tv["reguas"]["modelos"]["classe"]["grupos"]
    pc = tv["agregados"]["brasil"]["por_classe"]
    tot = tv["reguas"]["totais"]["brasil"]
    rot = {
        "venceu_folga": "Flávio venceu com folga",
        "venceu_apertado": "Flávio venceu apertado",
        "perdeu_apertado": "Flávio perdeu apertado",
        "perdeu_folga": "Flávio perdeu com folga",
    }
    x0, x1 = 330, 970
    vmin, vmax = -0.3, 0.3

    def sx(v):
        return x0 + (x1 - x0) * (v - vmin) / (vmax - vmin)

    out = [
        t(
            0,
            24,
            "Saldo de Flávio por voto de terceira via, pela classe do município",
            17,
            INK,
            700,
        )
    ]
    for v in (-0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3):
        out.append(
            ln(
                sx(v),
                44,
                sx(v),
                500,
                INK if v == 0 else GRID,
                1.5 if v == 0 else 1,
                None if v == 0 else "3 5",
            )
        )
        out.append(
            t(sx(v), 524, sinal(v, 1) if v else "0", 14, MUTED, 600, "middle", MONO)
        )
    y = 80
    for k, nome in rot.items():
        g = grupos[k]
        nx = pc[k]["saldo"] / pc[k]["estoque"]
        out.append(t(x0 - 14, y + 18, nome, 17, INK, 700, "end"))
        out.append(
            t(
                x0 - 14,
                y + 38,
                f"{mi_curto(pc[k]['estoque'])} votos",
                13,
                MUTED,
                600,
                "end",
                MONO,
            )
        )
        out.append(
            r(sx(0) if nx >= 0 else sx(nx), y, abs(sx(nx) - sx(0)), 18, OUTROS, 2)
        )
        lo, hi = g["saldo_ic95"]
        yy = y + 34
        cor = FLAVIO if g["saldo"] >= 0 else LULA
        out.append(ln(sx(lo), yy, sx(hi), yy, cor, 5))
        out.append(
            circ(sx(g["saldo"]), yy, 8, cor, f' stroke="{PAPER}" stroke-width="2"')
        )
        out.append(
            t(sx(max(nx, hi)) + 10, y + 16, sinal(nx), 14, OUTROS, 700, "start", MONO)
        )
        out.append(
            t(
                sx(max(nx, hi)) + 10,
                yy + 6,
                sinal(g["saldo"]),
                14,
                cor,
                700,
                "start",
                MONO,
            )
        )
        y += 100
    out.append(
        legenda(
            [("Matriz da Nexus", OUTROS), ("Urna de 2022, com IC 95%", FLAVIO)],
            0,
            566,
            15,
        )
    )
    out.append(
        t(
            0,
            596,
            f"No país: Nexus {mi_curto(tot['nexus'])}, Datafolha {mi_curto(tot['datafolha'])}, urna de 2022 {mi_curto(tot['urna'], 0)}",
            15,
            INK,
            600,
        )
    )
    return svg("".join(out), "Duas réguas para a terceira via")


# ------------------------------------------------------------------ 23 militância


def fig_militancia() -> str:
    tv = dado("terceira_via")
    comb = tv["reguas"]["rankings"]["top"]["combinacao"][:10]
    x0, x1 = 230, 600
    vmax = max(x["teto"] for x in comb)
    esc = (x1 - x0) / vmax
    out = [t(0, 24, "Os dez municípios em que as duas réguas concordam", 17, INK, 700)]
    out.append(
        t(0, 46, "saldo esperado de Flávio, do piso ao teto, votos", 14, MUTED, 600)
    )
    y = 70
    for x in comb:
        out.append(
            t(
                x0 - 12,
                y + 18,
                f"{nome_proprio(x['nome'])} ({x['uf']})",
                15,
                INK,
                700,
                "end",
            )
        )
        out.append(r(x0, y + 6, x["piso"] * esc, 18, FLAVIO, 2))
        out.append(
            r(
                x0 + x["piso"] * esc,
                y + 6,
                (x["teto"] - x["piso"]) * esc,
                18,
                "#9db4d8",
                2,
            )
        )
        out.append(
            t(
                x0 + x["teto"] * esc + 8,
                y + 20,
                num(x["piso"]),
                13,
                INK,
                700,
                "start",
                MONO,
            )
        )
        y += 44
    risco = tv["nulo_2022"]["risco_2026"]
    taxa = tv["nulo_2022"]["com_2t_governador"]["delta_pp"] / 100
    ufs = {u["uf"]: u for u in dado("presidente")["ufs"]}
    bx = 700
    out.append(r(bx - 10, 56, 310, 520, PAPER2, 10))
    out.append(t(bx + 145, 90, "Risco de nulo nas UFs", 17, INK, 700, "middle"))
    out.append(t(bx + 145, 112, "com 2º turno de governador", 17, INK, 700, "middle"))
    lista = sorted(risco["ufs"], key=lambda u: -ufs[u]["comparecimento"])
    vm = max(ufs[u]["comparecimento"] * taxa for u in lista)
    yy = 146
    for u in lista:
        v = ufs[u]["comparecimento"] * taxa
        out.append(t(bx + 30, yy + 15, u, 15, INK, 700, "end", MONO))
        out.append(r(bx + 40, yy, 170 * v / vm, 20, GOLD_FILL, 2))
        out.append(
            t(
                bx + 48 + 170 * v / vm,
                yy + 15,
                mi_curto(v, 0),
                13,
                INK,
                700,
                "start",
                MONO,
            )
        )
        yy += 32
    out.append(
        t(bx + 145, yy + 40, mi_curto(risco["votos"], 0), 40, GOLD, 800, "middle", MONO)
    )
    out.append(
        t(bx + 145, yy + 70, "votos em risco, pela taxa", 15, INK, 600, "middle")
    )
    out.append(t(bx + 145, yy + 90, "medida em 2022", 15, INK, 600, "middle"))
    out.append(legenda([("Piso", FLAVIO), ("Até o teto", "#9db4d8")], 0, 596, 15))
    return svg("".join(out), "Mapa da militância")


# ------------------------------------------------------------------ 24 frases


def fig_frases() -> str:
    ar = dado("estrategia_2t")["aritmetica"]["matrizes"]
    nx, dfl = ar["nexus"]["linhas_publicadas"], ar["datafolha"]["linhas_publicadas"]
    votos = {
        t_["linha"]: t_["votos"]
        for t_ in dado("estrategia_2t")["aritmetica"]["primeiro_turno"]["terceiros"]
        if t_.get("linha_propria")
    }
    linhas = [
        ("Renan", "Nexus", nx["Renan"], "fechar sem arrogância"),
        ("Zema", "Nexus", nx["Zema"], "falta só fechar"),
        ("Cury", "Nexus", nx["Cury"], "conversa decide"),
        ("Cury", "Datafolha", dfl["Cury"], "conversa decide"),
        ("Caiado", "Nexus", nx["Caiado"], "medir antes de gastar"),
        ("Caiado", "Datafolha", dfl["Caiado"], "medir antes de gastar"),
    ]
    x0, x1 = 200, 760
    out = [
        t(
            0,
            24,
            "Como vota no 2º turno o eleitor de cada candidatura, % da linha",
            17,
            INK,
            700,
        )
    ]
    y = 52
    for nome, fonte, ln_, conselho in linhas:
        f = ln_["Flávio"]
        lu = ln_["Lula"]
        fora = ln_.get("Branco/nulo", 0) + ln_.get("Indecisos", 0)
        if not fora:
            fora = max(0, 100 - f - lu)
        soma = f + lu + fora
        out.append(t(x0 - 12, y + 22, nome, 19, INK, 800, "end"))
        out.append(t(x0 - 12, y + 42, fonte, 13, MUTED, 600, "end", MONO))
        xx = x0
        for v, cor, txt in (
            (f, FLAVIO, WHITE),
            (lu, LULA, WHITE),
            (fora, "#c9c1ad", INK),
        ):
            w = (x1 - x0) * v / soma
            out.append(r(xx, y + 6, w, 36, cor))
            if w > 40:
                out.append(
                    t(xx + w / 2, y + 30, num(v, 0), 16, txt, 800, "middle", MONO)
                )
            xx += w
        out.append(t(x1 + 14, y + 22, conselho, 16, INK, 700))
        if nome in votos and fonte == "Nexus":
            out.append(
                t(
                    x1 + 14,
                    y + 42,
                    f"{mi_curto(votos[nome])} votos",
                    13,
                    MUTED,
                    600,
                    "start",
                    MONO,
                )
            )
        y += 78
    out.append(
        legenda(
            [
                ("Flávio", FLAVIO),
                ("Lula", LULA),
                ("Branco, nulo ou indeciso", "#c9c1ad"),
            ],
            0,
            596,
            15,
        )
    )
    return svg("".join(out), "Linhas de transferência por candidatura")


__all__ = [
    "GOLD_FILL",
    "fig_aritmetica",
    "fig_checklist",
    "fig_fechamento",
    "fig_frases",
    "fig_lentidao",
    "fig_limites",
    "fig_militancia",
    "fig_reguas",
]
