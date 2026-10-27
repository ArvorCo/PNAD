"""Figuras do capítulo "O que poderia ter acontecido".

- ``hipoteses_tarde``: linha do tempo da tarde de 25/10 (16:00 a 19:10), um marco por
  linha, com a faixa em que o TSE não gerou arquivo algum;
- ``hipoteses_matriz``: hipótese × teste, cor pelo resultado;
- ``hipoteses_cadencia``: a cadência horária do dia, 1º e 2º turno (de ``logs.json``).

Fonte: ``analysis/apuracao_2t_2026/dados/hipoteses.json`` e ``logs.json``.
"""

from __future__ import annotations

from apuracao_2026.pagina_comum import (
    GOLD,
    INK,
    LINE,
    MUTED,
    OUTROS,
    PAPER,
    inteiro,
    num,
)
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
    svg_abre,
    t,
)

from .pagina_fig_logs import COR_1T, COR_2T

INICIO, FIM = 16 * 60, 19 * 60 + 10
COR_RAIA = {
    "justica": GOLD,
    "transporte": OUTROS,
    "tse": INK,
    "urnas": "#1457aa",
    "video": "#6b4a92",
}
NOME_RAIA = {
    "justica": "Justiça e campanhas",
    "transporte": "Transporte",
    "tse": "TSE e TREs",
    "urnas": "Urnas (BU)",
    "video": "Vídeo",
}
COR_RES = {
    "exclui": ("#cfe5d6", "#173d28"),
    "não exclui": ("#f2dfb0", "#4d3a00"),
    "pendente": ("#dcd6ec", "#33295a"),
    "não se aplica": (PAPER, MUTED),
}
ROT_RES = {
    "exclui": "marca ausente",
    "não exclui": "não alcança",
    "pendente": "pendente",
    "não se aplica": "fora do teste",
}


def _min(hhmm: str) -> int:
    h, m = hhmm[:5].split(":")
    return int(h) * 60 + int(m)


def _linhas_tarde(H: dict) -> list[dict]:
    """Marcos da figura: os da cronologia, o vídeo e as medianas das urnas, por hora."""
    c = H["cronologia"]
    v = c["video"]
    u = c["urnas"]
    out = [
        {
            "hora": m["hora"][:5],
            "texto": m["rotulo"],
            "raia": m["raia"],
            "fonte": m["veiculo"],
            "tipo": m["tipo"],
        }
        for m in c["marcos"]
    ]
    out.append(
        {
            "hora": v["publicado_brt"],
            "texto": f"Vídeo publicado no Instagram (perfil {v['perfil']}) pede extensão em BA e SP",
            "raia": "video",
            "fonte": "Instagram, carimbo da plataforma",
            "tipo": "fato",
        }
    )
    pr = v["primeira_republicacao"]
    if pr:
        out.append(
            {
                "hora": pr["hora_brt"],
                "texto": f"Primeira republicação localizada do vídeo ({pr['veiculo']})",
                "raia": "video",
                "fonte": pr["veiculo"],
                "tipo": "fato",
            }
        )
    out.append(
        {
            "hora": u["encerramento_p50"],
            "texto": f"Mediana do último voto nas urnas; {num(u['pct_ate_1715'], 2)}% encerraram até 17:15",
            "raia": "urnas",
            "fonte": "BUs (secoes.json)",
            "tipo": "fato",
        }
    )
    out.append(
        {
            "hora": u["emissao_p50"],
            "texto": f"Mediana da emissão do BU; {num(u['pct_bu_emitido_ate_1730'], 2)}% emitidos até 17:30",
            "raia": "urnas",
            "fonte": "BUs (secoes.json)",
            "tipo": "fato",
        }
    )
    s = c["silencio"]
    out.append(
        {
            "hora": s["inicio"][:5],
            "texto": f"Último arquivo do TSE antes da pausa ({s['inicio']})",
            "raia": "tse",
            "fonte": "banco do coletor",
            "tipo": "fato",
        }
    )
    out.append(
        {
            "hora": s["fim"][:5],
            "texto": f"Primeiro arquivo do TSE depois da pausa ({s['fim']})",
            "raia": "tse",
            "fonte": "banco do coletor",
            "tipo": "fato",
        }
    )
    out.sort(key=lambda x: (_min(x["hora"]), x["raia"]))
    return out


def fig_tarde(H: dict) -> str:
    linhas = _linhas_tarde(H)
    s = H["cronologia"]["silencio"]
    w = 1100
    x0, x1 = 130, w - 20
    topo, passo = 70, 27
    h = topo + passo * len(linhas) + 50
    x = escala(INICIO, FIM, x0, x1)
    out = [
        svg_abre(
            w,
            h,
            "A tarde de 25 de outubro, das 16h às 19h10",
            "Um marco por linha, na ordem da hora de Brasília. Marcos anteriores às 16h ficam na margem "
            "esquerda com a hora escrita. A faixa cinza marca o intervalo em que o TSE não gerou arquivo algum.",
        )
    ]
    tips = Tips()
    xs, xe = x(_min(s["inicio"])), x(_min(s["fim"]))
    out.append(r(xs, topo - 18, xe - xs, passo * len(linhas) + 18, "#e9e4d6"))
    out.append(
        t(
            (xs + xe) / 2,
            topo - 26,
            f"TSE sem gerar arquivo: {num(s['minutos'], 1)} min",
            13,
            INK,
            "middle",
            "700",
        )
    )
    for m in range(INICIO, FIM + 1, 30):
        out.append(ln(x(m), topo - 18, x(m), topo + passo * len(linhas), GRADE, 1))
        out.append(
            t(
                x(m),
                h - 22,
                f"{m // 60:02d}:{m % 60:02d}",
                12,
                MUTED,
                "middle",
                mono=True,
            )
        )
    out.append(ln(x0, h - 40, x1, h - 40, MUTED, 1))
    for i, m in enumerate(linhas):
        y = topo + i * passo + 6
        mi = _min(m["hora"])
        antes = mi < INICIO
        cx = x(min(mi, FIM))
        cor = COR_RAIA[m["raia"]]
        partes = [ln(x0, y, x1, y, LINE, 0.6)]
        rot = f"{m['hora']} {m['texto']}"
        if antes:
            # marco anterior às 16h: seta na borda esquerda e rótulo dentro do gráfico
            partes.append(
                t(x0 - 10, y + 4, "antes de 16h ←", 11, MUTED, "end", mono=True)
            )
            partes.append(
                f'<circle cx="{x0:.1f}" cy="{y:.1f}" r="6" fill="{PAPER}" stroke="{cor}" stroke-width="2.5"/>'
            )
            cx = x0
        else:
            partes.append(
                f'<circle cx="{cx:.1f}" cy="{y:.1f}" r="6" fill="{cor}" stroke="{PAPER}" stroke-width="1.5"/>'
            )
        direita = cx <= x0 + 0.5 * (x1 - x0)
        cabe = int(((x1 - cx) if direita else (cx - 0)) / 6.9) - 3
        if len(rot) > cabe:
            rot = rot[: cabe - 1].rsplit(" ", 1)[0] + "…"
        if direita:
            partes.append(t(cx + 12, y + 4, rot, 12.5, INK, "start"))
        else:
            partes.append(t(cx - 12, y + 4, rot, 12.5, INK, "end"))
        k = tips.add(
            ficha(
                m["hora"],
                NOME_RAIA[m["raia"]],
                [("Fonte", m["fonte"]), ("Natureza", m["tipo"])],
                m["texto"],
            )
        )
        out.append(hit("".join(partes) + area(0, y - passo / 2, w, passo), k))
    out.append("</svg>")
    leg = legenda_html(
        [(NOME_RAIA[k], COR_RAIA[k]) for k in NOME_RAIA]
        + [("TSE sem gerar arquivo", "#e9e4d6")]
    )
    legenda = (
        f"Cada linha é um marco com fonte. Os horários do pedido ao STF vêm de duas fontes que divergem "
        f"({' e '.join(H['h4']['stf_carimbos'])}); a figura usa o primeiro. "
        f"A última versão nacional antes da pausa, às {s['banco']['versao_brt']}, tinha "
        f"{inteiro(s['banco']['secoes'])} seções totalizadas, com Lula a {num(s['banco']['lula_pct'], 2)}% nessa "
        "fração (banco do coletor). "
        "Fonte: hipoteses.json (cronologia), que lê noticias_noite.json, secoes.json, linha_do_tempo.json "
        "e as páginas do vídeo arquivadas em data/originals/prorrogacao_video/."
    )
    return figura_html(
        "hipoteses_tarde", "".join(out), legenda, tips, minw=900, apos=leg
    )


def fig_matriz(H: dict) -> str:
    testes = H["discriminador"]
    hips = H["hipoteses"]
    cw, ch = 112, 44
    x0, y0 = 250, 120
    w = x0 + cw * len(testes) + 20
    h = y0 + ch * len(hips) + 20
    out = [
        svg_abre(
            w,
            h,
            "Hipótese × teste",
            "Linhas: as seis hipóteses. Colunas: os oito testes. Cada célula diz se a marca esperada da hipótese "
            "não aparece nos arquivos públicos, se o teste não a alcança, se depende de documento ou se não se aplica.",
        )
    ]
    tips = Tips()
    for j, te in enumerate(testes):
        cx = x0 + j * cw + cw / 2
        palavras = te["teste"].split(" ")
        lin, atual = [], ""
        for p in palavras:
            if len(atual) + len(p) > 13 and atual:
                lin.append(atual)
                atual = p
            else:
                atual = (atual + " " + p).strip()
        lin.append(atual)
        for k, s in enumerate(lin[:4]):
            out.append(
                t(
                    cx,
                    y0 - 14 - 15 * (len(lin[:4]) - 1 - k),
                    s,
                    12,
                    INK,
                    "middle",
                    "700",
                )
            )
    for i, hp in enumerate(hips):
        y = y0 + i * ch
        out.append(
            t(
                x0 - 12,
                y + ch / 2 + 5,
                f"{hp['id'].upper()} {hp['curto']}",
                13,
                INK,
                "end",
            )
        )
        for j, te in enumerate(testes):
            res = te["celulas"][hp["id"]]
            fundo, letra = COR_RES[res]
            xx = x0 + j * cw
            k = tips.add(
                ficha(
                    te["teste"],
                    f"{hp['id'].upper()} {hp['titulo']}",
                    [("Resultado", ROT_RES[res])],
                    te["o_que"],
                )
            )
            cel = r(xx + 2, y + 2, cw - 4, ch - 4, fundo) + t(
                xx + cw / 2, y + ch / 2 + 5, ROT_RES[res], 12, letra, "middle", "600"
            )
            if res == "não se aplica":
                cel = (
                    f'<rect x="{xx + 2:.1f}" y="{y + 2:.1f}" width="{cw - 4:.1f}" height="{ch - 4:.1f}" '
                    f'fill="{fundo}" stroke="{LINE}" stroke-width="1"/>'
                    + t(xx + cw / 2, y + ch / 2 + 5, ROT_RES[res], 11, letra, "middle")
                )
            out.append(hit(cel + area(xx, y, cw, ch), k))
    out.append("</svg>")
    leg = legenda_html([(ROT_RES[k], v[0]) for k, v in COR_RES.items()])
    legenda = (
        "Leitura da casa sobre o que cada teste alcança. Marca ausente: o teste encontraria a marca do mecanismo, e "
        "ela não aparece nos arquivos públicos. Não alcança: o mecanismo passaria pelo teste sem deixar marca. "
        "Pendente: só um documento responde. Fonte: hipoteses.json (discriminador)."
    )
    return figura_html(
        "hipoteses_matriz", "".join(out), legenda, tips, minw=900, apos=leg
    )


def fig_cadencia(L: dict) -> str:
    c = L["cadencia"]
    p1 = c["amostra_1t"]["brasil_1t"]["pct"]
    p2 = c["brasil_2t"]["pct"]
    horas = [str(h) for h in range(8, 20)]
    w, h = 700, 280
    x0, y0, larg, alt = 50, 20, w - 70, h - 70
    vmax = max([*p1.values(), *p2.values()]) + 2
    y = escala(0, vmax, y0 + alt, y0)
    passo = larg / len(horas)
    out = [
        svg_abre(
            w,
            h,
            "Votos por hora de Brasília, 1º e 2º turno",
            "Barras pareadas por hora, das 8h às 19h: parcela dos votos do dia computada em cada hora.",
        )
    ]
    tips = Tips()
    for v in range(0, int(vmax) + 1, 5):
        out.append(ln(x0, y(v), x0 + larg, y(v), GRADE, 1))
        out.append(t(x0 - 6, y(v) + 4, f"{v}%", 11, MUTED, "end", mono=True))
    for i, hh in enumerate(horas):
        a, b = p1.get(hh, 0.0), p2.get(hh, 0.0)
        xa = x0 + i * passo + passo * 0.12
        bw = passo * 0.36
        rot = f"{int(hh):02d}h" + ("+" if hh == "19" else "")
        partes = [
            r(xa, y(a), bw, y(0) - y(a), COR_1T),
            r(xa + bw, y(b), bw, y(0) - y(b), COR_2T),
            t(
                x0 + i * passo + passo / 2,
                y0 + alt + 16,
                rot,
                11,
                INK,
                "middle",
                mono=True,
            ),
        ]
        k = tips.add(
            ficha(
                f"{rot} de Brasília",
                "Brasil",
                [("1º turno", f"{num(a, 2)}%"), ("2º turno", f"{num(b, 3)}%")],
            )
        )
        out.append(hit("".join(partes) + area(x0 + i * passo, y0, passo, alt), k))
    out.append(ln(x0, y(0), x0 + larg, y(0), MUTED, 1))
    out.append("</svg>")
    leg = legenda_html(
        [("1º turno, amostra de seções", COR_1T), ("2º turno, todas as seções", COR_2T)]
    )
    legenda = (
        f"Depois das 17h o 2º turno computou {inteiro(c['brasil_2t']['computados_17_19'])} votos, "
        f"{num(c['brasil_2t']['pct_17_19'], 3)}% do dia, contra {num(c['amostra_1t']['brasil_1t']['pct_17_19'], 2)}% "
        "no 1º turno (amostra de uma seção em cinco), que tinha cinco cargos, seis votos e fila mais lenta. A mesma "
        "figura, maior e por região, está no capítulo "
        "dos logs. Fonte: logs.json (cadencia)."
    )
    return figura_html(
        "hipoteses_cadencia", "".join(out), legenda, tips, modo="fit", apos=leg
    )
