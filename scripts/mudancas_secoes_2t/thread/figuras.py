"""Figuras dos três cards (viewBox 1000 × 680), desenhadas em Python.

Tudo sai de ``mudancas.json``. Cor de candidato só aparece onde o gráfico mede voto
(figura 3, votos perdidos por candidatura); mapa e histograma usam dourado, marinho e
verde. Rótulo sobre cor leva retângulo de fundo sólido para passar na auditoria de
contraste.
"""

from __future__ import annotations

import json
import math
from functools import cache

from apuracao_2026.thread_base import (
    FLAVIO,
    GRID,
    INK,
    LULA,
    MONO,
    MUTED,
    PAPER,
    PAPER2,
    ROOT,
    WHITE,
    circ,
    esc,
    ln,
    num,
    pct,
    r,
    sinal,
    svg,
    t,
)

from .base import dados, mi, publico

W, H = 1000, 680
H3 = 700
MALHA = ROOT / "data/originals/ibge_malhas/br_uf/br_uf_minima.geojson"

OURO = "#d9a82a"  # retorno ao prédio original (preenchimento)
OURO_TXT = "#7d5b00"
MARINHO = "#22305a"  # nova realocação
VERDE = "#0b6650"
CINZA = "#5f6773"
CINZA_BARRA = "#7b8494"
BORDA_UF = "#b9b09a"

LON0, LON1, LAT0, LAT1 = -74.2, -34.6, -33.9, 5.4
COS = math.cos(math.radians(-14.0))


def _largura(s: str, size: float, fator: float = 0.5) -> float:
    return fator * size * len(s)


def _quebra(s: str, n: int) -> list[str]:
    linhas, atual = [], ""
    for p in s.split():
        if atual and len(atual) + 1 + len(p) > n:
            linhas.append(atual)
            atual = p
        else:
            atual = f"{atual} {p}".strip()
    if atual:
        linhas.append(atual)
    return linhas


def _rotulo(x, y, s, size=16, fill=INK, fundo=PAPER, anchor="start", weight=600):
    """Texto com caixa sólida atrás (rótulo sobre cor)."""
    larg = _largura(s, size, 0.52) + 12
    x0 = {"start": x - 6, "middle": x - larg / 2, "end": x - larg + 6}[anchor]
    return r(x0, y - size * 0.95, larg, size * 1.35, fundo, 3) + t(
        x, y, s, size, fill, weight, anchor
    )


def _cabeca(x, y, s) -> str:
    return t(
        x, y, s.upper(), 15, MUTED, 700, family=MONO, extra=' letter-spacing="1.2"'
    )


# ------------------------------------------------------------------ figura 1


@cache
def _ufs() -> list[list[list[list[float]]]]:
    raw = json.loads(MALHA.read_text(encoding="utf-8"))
    out = []
    for feat in raw["features"]:
        g = feat["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        out.append(polys)
    return out


def _proj(w: float, h: float, pad: float):
    span_x, span_y = (LON1 - LON0) * COS, LAT1 - LAT0
    esc_ = min((w - 2 * pad) / span_x, (h - 2 * pad) / span_y)
    ox = pad + ((w - 2 * pad) - span_x * esc_) / 2
    oy = pad + ((h - 2 * pad) - span_y * esc_) / 2

    def f(lon: float, lat: float) -> tuple[float, float]:
        return ox + (lon - LON0) * COS * esc_, oy + (LAT1 - lat) * esc_

    return f


def pontos_origem() -> list[dict]:
    """Um ponto por local de origem com mudança real e coordenada confiável.

    Categoria do ponto: a do destino com mais eleitores (A volta ao original; o resto
    é nova realocação).
    """
    grupos: dict[tuple, dict] = {}
    for x in dados()["locais"]:
        if not x["mudanca_real"] or x.get("lat_1t") is None:
            continue
        if x.get("coord_repetida"):
            continue
        k = (x["uf"], x["mun_tse"], x["local_1t"])
        g = grupos.setdefault(
            k, {"lat": x["lat_1t"], "lon": x["lon_1t"], "e": 0, "cats": {}}
        )
        g["e"] += x["eleitores"]
        cat = "A" if x["categoria"] == "A" else "N"
        g["cats"][cat] = g["cats"].get(cat, 0) + x["eleitores"]
    out = []
    for g in grupos.values():
        g["cat"] = max(g["cats"], key=g["cats"].get)
        out.append(g)
    return sorted(out, key=lambda g: -g["e"])


def _mapa(x0: float, y0: float, w: float, h: float) -> str:
    f = _proj(w, h, 6)
    partes = []
    for polys in _ufs():
        d = ""
        for poly in polys:
            for anel in poly:
                pts = " ".join(
                    f"{x + x0:.1f},{y + y0:.1f}" for x, y in (f(a, b) for a, b in anel)
                )
                d += f"M{pts}Z"
        partes.append(
            f'<path d="{d}" fill="{PAPER2}" stroke="{BORDA_UF}" stroke-width="1" '
            f'stroke-linejoin="round"/>'
        )
    pts = []
    for g in pontos_origem():
        x, y = f(g["lon"], g["lat"])
        raio = 2.6 + 0.16 * math.sqrt(g["e"])
        cor, borda = (OURO, OURO_TXT) if g["cat"] == "A" else (MARINHO, WHITE)
        pts.append(
            circ(
                x + x0,
                y + y0,
                raio,
                cor,
                f' fill-opacity="0.82" stroke="{borda}" stroke-width="1.1"',
            )
        )
    return "".join(partes + pts)


def _barra_publica(y, nome, secoes, eleitores, maximo, x=545, esc_larg=300) -> str:
    larg = secoes / maximo * esc_larg
    sub = (
        f"{num(eleitores)} eleitores"
        if eleitores
        else "total de eleitores não informado"
    )
    return (
        t(x, y + 16, nome, 17, INK, 600)
        + r(x, y + 26, larg, 20, CINZA_BARRA, 2)
        + t(x + larg + 10, y + 43, num(secoes), 22, INK, 800)
        + t(x, y + 66, sub, 15, MUTED, 500)
    )


def fig_numeros() -> str:
    D = dados()
    R = D["resumo"]
    MR, FO = R["mudanca_real"], R["fora_do_original"]
    tse, col = publico("tse_agencia_brasil"), publico("coligacao_peticao")
    con, pai = publico("forum_exportacao"), publico("painel_tse")
    maximo = FO["secoes_2t"]
    a = MR["por_categoria"]["A"]["secoes"]
    pts = pontos_origem()
    n_a = sum(1 for g in pts if g["cat"] == "A")
    out = [_mapa(0, 10, 520, 540)]
    # legenda do mapa
    out.append(circ(16, 590, 8, OURO, f' stroke="{OURO_TXT}" stroke-width="1.2"'))
    out.append(t(32, 596, "Retorno ao prédio original", 17, INK, 600))
    out.append(circ(16, 622, 8, MARINHO))
    out.append(t(32, 628, "Nova realocação", 17, INK, 600))
    out.append(
        t(
            16,
            656,
            f"{num(len(pts))} locais de origem com coordenada ({num(n_a)} em dourado). "
            "Tamanho: eleitores.",
            15,
            MUTED,
            500,
        )
    )
    # painel dos números públicos
    out.append(_cabeca(545, 20, "O que se publicou, em seções"))
    dados_pub = [
        ("TSE, 16/10", tse["secoes"]["publico"], None),
        (
            "Petição da coligação de Lula, 17/10",
            col["secoes"]["publico"],
            col["eleitores"]["publico"],
        ),
        (
            "Consulta ao sistema do TSE, 18/10",
            con["secoes"]["publico"],
            con["eleitores"]["publico"],
        ),
        (
            "Painel oficial do TSE, 18/10, 20h27",
            pai["secoes"]["publico"],
            pai["eleitores"]["publico"],
        ),
    ]
    for i, (nome, s, e) in enumerate(dados_pub):
        out.append(_barra_publica(34 + i * 78, nome, s, e, maximo))
    # nossa conta
    y = 358
    out.append(ln(545, y, 1000, y, GRID, 1.5))
    out.append(_cabeca(545, y + 30, "Nossa conta, pelos dois arquivos do TSE"))
    y2 = y + 44
    larg_mr = MR["secoes"] / maximo * 300
    larg_a = a / maximo * 300
    out.append(t(545, y2 + 16, "Mudança real de prédio", 17, INK, 600))
    out.append(
        r(545, y2 + 26, larg_a, 20, OURO, 2, f' stroke="{OURO_TXT}" stroke-width="1"')
    )
    out.append(r(545 + larg_a, y2 + 26, larg_mr - larg_a, 20, MARINHO, 2))
    out.append(t(545 + larg_mr + 10, y2 + 43, num(MR["secoes"]), 22, INK, 800))
    out.append(
        t(
            545,
            y2 + 66,
            f"{num(MR['eleitores'])} eleitores; {num(a)} voltam ao original",
            15,
            MUTED,
            500,
        )
    )
    y3 = y2 + 84
    out.append(t(545, y3 + 16, "Seguem fora do original em 25/10", 17, INK, 600))
    out.append(r(545, y3 + 26, 300, 20, VERDE, 2))
    out.append(t(555 + 300, y3 + 43, num(FO["secoes_2t"]), 22, INK, 800))
    out.append(
        t(545, y3 + 66, f"{mi(FO['eleitores_2t'])} de eleitores", 15, MUTED, 500)
    )
    # chamada final
    out.append(r(545, 572, 455, 96, PAPER2, 6, f' stroke="{GRID}"'))
    for i, linha in enumerate(
        _quebra(
            "Sem lista por seção e sem o motivo de cada troca, não dá para saber "
            "qual regra gerou cada número.",
            44,
        )
    ):
        out.append(t(562, 603 + i * 25, linha, 18, INK, 600))
    return svg(
        "".join(out),
        "Mapa dos locais de origem com mudança real e quatro números públicos",
        W,
        H,
    )


# ------------------------------------------------------------------ figura 2


def _faixas_distancia() -> list[dict]:
    fx = dados()["distancia"]["mudanca_real"]["faixas"]
    return [
        f
        for f in fx
        if not f["faixa"].startswith(("acima de 50", "coordenada", "sem coord"))
    ]


def _histograma() -> str:
    D = dados()
    fx = _faixas_distancia()
    T = D["distancia"]["teste_hipotese"]
    med = D["resumo"]["mudanca_real"]["distancia_mediana_m"]
    viz = T["predio_vizinho"]["mediana_m"]["valor"]
    base_y, topo = 540, 150
    maxv = max(f["secoes"] for f in fx)
    x0, larg_col = 14, 70
    out = [
        t(0, 24, "Distância entre o endereço antigo e o novo", 20, INK, 700),
        t(0, 48, "Seções com mudança real e distância confiável", 16, MUTED, 500),
    ]
    out.append(ln(0, base_y, 540, base_y, INK, 1.5))
    contagens: list[str] = []
    for i, f in enumerate(fx):
        x = x0 + i * (larg_col + 6)
        alt = f["secoes"] / maxv * (base_y - topo)
        longe = i >= 3
        out.append(r(x, base_y - alt, larg_col, alt, OURO if longe else VERDE, 3))
        contagens.append(
            _rotulo(
                x + larg_col / 2,
                base_y - alt - 8,
                num(f["secoes"]),
                18,
                INK,
                PAPER,
                "middle",
                800,
            )
        )
        partes = f["faixa"].replace(" m", " m|").replace(" km", " km|").split("|")
        rot = f["faixa"].split(" ")
        if rot[0] == "até":
            l1, l2 = "até", " ".join(rot[1:])
        elif "a" in rot:
            k = rot.index("a")
            l1, l2 = " ".join(rot[: k + 1]), " ".join(rot[k + 1 :])
        else:
            l1, l2 = partes[0], ""
        out.append(t(x + larg_col / 2, base_y + 24, l1, 15, INK, 500, "middle"))
        out.append(t(x + larg_col / 2, base_y + 44, l2, 15, INK, 500, "middle"))
    # marcas dentro da faixa 300 a 500 m (índice 1)
    xb = x0 + 1 * (larg_col + 6)
    for valor, nome, nivel, lado in (
        (med, f"mediana {num(med)} m", 0, "end"),
        (viz, f"prédio vizinho {num(viz)} m", 1, "start"),
    ):
        xm = xb + (valor - 300) / 200 * larg_col
        y_lab = 96 + nivel * 28
        out.append(ln(xm, y_lab + 6, xm, base_y, INK, 2, "5 4"))
        dx = -8 if lado == "end" else 8
        out.append(_rotulo(xm + dx, y_lab, nome, 16, INK, PAPER, lado, 700))
    out.extend(contagens)
    soma_longe = sum(f["secoes"] for f in fx[3:])
    total = sum(f["secoes"] for f in fx)
    out.append(
        t(
            0,
            base_y + 82,
            f"Em dourado, acima de 1 km: {num(soma_longe)} de {num(total)} seções ({pct(soma_longe / total * 100, 1)}).",
            16,
            INK,
            600,
        )
    )
    sem = (
        D["resumo"]["mudanca_real"]["secoes"]
        - D["resumo"]["mudanca_real"]["secoes_com_distancia"]
    )
    out.append(
        t(
            0,
            base_y + 106,
            f"Linha reta, não o caminho a pé. {num(sem)} seções sem distância confiável.",
            15,
            MUTED,
            500,
        )
    )
    return "".join(out)


def _celular(x0: float, y0: float, w: float, h: float) -> str:
    D = dados()
    med = D["resumo"]["mudanca_real"]["distancia_mediana_m"]
    pad = 22
    xi, wi = x0 + pad, w - 2 * pad
    out = [
        r(x0, y0, w, h, WHITE, 26, f' stroke="{INK}" stroke-width="3"'),
        r(x0 + w / 2 - 36, y0 + 10, 72, 7, GRID, 3.5),
        _cabeca(xi, y0 + 52, "Local de votação · 2º turno"),
    ]
    y = y0 + 84
    for linha in _quebra("Sua seção mudou de endereço para o 2º turno", 26):
        out.append(t(xi, y, linha, 24, INK, 800))
        y += 29
    out.append(
        t(xi, y + 4, "A seção 123, zona 45, vota em outro lugar.", 16, MUTED, 500)
    )
    y += 28

    def caixa(yy, rot, nome, end, cor):
        return (
            r(xi, yy, wi, 92, PAPER2, 6)
            + r(xi, yy, 6, 92, cor, 3)
            + t(xi + 18, yy + 24, rot.upper(), 13.5, MUTED, 700, family=MONO)
            + t(xi + 18, yy + 52, nome, 19, INK, 700)
            + t(xi + 18, yy + 78, end, 15.5, MUTED, 500)
        )

    out.append(
        caixa(
            y,
            "Onde você votou no 1º turno",
            "Escola Municipal Exemplo",
            "Rua das Flores, s/n · Centro",
            CINZA,
        )
    )
    out.append(
        caixa(
            y + 106,
            "Onde vota em 25 de outubro",
            "Colégio Exemplo Novo",
            "Avenida Central, 200 · Bairro Novo",
            VERDE,
        )
    )
    y += 222
    out.append(t(xi, y, f"Distância: {num(med)} m em linha reta.", 19, INK, 700))
    out.append(r(xi, y + 20, wi, 50, VERDE, 8))
    out.append(
        t(
            xi + wi / 2,
            y + 52,
            "Abrir o novo endereço no Google Maps",
            17.5,
            WHITE,
            700,
            "middle",
        )
    )
    out.append(r(xi, y + 82, wi, 46, WHITE, 8, f' stroke="{VERDE}" stroke-width="2.5"'))
    out.append(
        t(
            xi + wi / 2,
            y + 111,
            "Conferir no TSE ou no e-Título",
            17.5,
            VERDE,
            700,
            "middle",
        )
    )
    out.append(t(xi, y + 158, "A conferência oficial é a do TSE", 15, MUTED, 500))
    out.append(t(xi, y + 178, "ou do aplicativo e-Título.", 15, MUTED, 500))
    return "".join(out)


def fig_alerta() -> str:
    out = [_histograma()]
    out.append(
        r(590, 4, 410, 30, MARINHO, 4)
        + t(795, 25, "EXEMPLO ILUSTRATIVO DO ALERTA", 15, WHITE, 700, "middle", MONO)
    )
    out.append(_celular(590, 44, 410, 626))
    return svg(
        "".join(out),
        "Histograma das distâncias e exemplo do alerta no aplicativo",
        W,
        H,
    )


# ------------------------------------------------------------------ figura 3


def _linhas_cenarios() -> list[dict]:
    C = dados()["cenarios_abstencao"]
    E = C["estimativa_brasileira"]["seguem_fora_do_original_2t"]["central"]
    R = C["estimativa_rio"]["seguem_fora_do_original_2t"]
    linhas = [
        {
            "nome": f"Efeito medido, +{num(E['abstencao_extra_pp'], 2)} ponto",
            "sub": f"{num(E['urnas'])} urnas fora do original",
            "f": E["perdidos"]["flavio"],
            "l": E["perdidos"]["lula"],
            "s": E["variacao_diferenca_flavio_menos_lula_votos"],
            "forte": True,
        },
        {
            "nome": f"Teto pelo Rio, +{num(R['abstencao_extra_pp'], 2)} pontos",
            "sub": f"{num(R['urnas'])} urnas fora do original",
            "f": R["perdidos"]["flavio"],
            "l": R["perdidos"]["lula"],
            "s": R["variacao_diferenca_flavio_menos_lula_votos"],
        },
    ]
    for f in C["fixos"]:
        m = f["mudanca_real"]
        linhas.append(
            {
                "nome": f"Cenário +{num(f['abstencao_extra_pp'], 0)} pontos",
                "sub": f"{num(m['urnas'])} urnas com mudança real",
                "f": m["perdidos"]["flavio"],
                "l": m["perdidos"]["lula"],
                "s": m["variacao_diferenca_flavio_menos_lula_votos"],
            }
        )
    return linhas


def _divergentes() -> str:
    C = dados()["cenarios_abstencao"]
    linhas = _linhas_cenarios()
    maximo = max(max(x["f"], x["l"]) for x in linhas)
    centro, meia = 560, 240
    esc_ = meia / maximo
    out = [
        t(
            0,
            22,
            "Votos que cada candidatura deixa de receber, por cenário",
            20,
            INK,
            700,
        ),
        t(centro - 8, 52, "Lula perde", 16, LULA, 800, "end"),
        t(centro + 8, 52, "Flávio perde", 16, FLAVIO, 800),
        t(1000, 52, "Diferença F − L", 16, INK, 800, "end"),
    ]
    y0, passo = 66, 42
    for i, x in enumerate(linhas):
        y = y0 + i * passo
        if x.get("forte"):
            out.append(r(0, y - 4, 1000, passo - 2, PAPER2, 4))
        out.append(t(0, y + 14, x["nome"], 17, INK, 700))
        out.append(t(0, y + 31, x["sub"], 14.5, MUTED, 500))
        wl, wf = x["l"] * esc_, x["f"] * esc_
        out.append(r(centro - wl, y + 2, wl, 24, LULA, 2))
        out.append(r(centro, y + 2, wf, 24, FLAVIO, 2))
        out.append(t(centro - wl - 6, y + 21, num(x["l"]), 16, INK, 700, "end"))
        out.append(t(centro + wf + 6, y + 21, num(x["f"]), 16, INK, 700))
        out.append(
            t(1000, y + 21, f"+{num(x['s'])} a favor de Flávio", 16, FLAVIO, 800, "end")
        )
    out.append(ln(centro, y0 - 6, centro, y0 + len(linhas) * passo, INK, 2))
    # saldo entre turnos
    y = y0 + len(linhas) * passo + 4
    E = C["estimativa_brasileira"]
    nr, ga = (
        E["novas_realocacoes"]["central"]["perdidos"],
        E["categoria_a_ganho"]["central"]["perdidos"],
    )
    saldo = abs(
        E["saldo_1t_para_2t"]["central"]["variacao_diferenca_flavio_menos_lula_votos"]
    )
    out.append(ln(0, y - 6, 1000, y - 6, GRID, 1.2))
    out.append(t(0, y + 14, "Saldo entre os turnos", 17, INK, 700))
    out.append(t(0, y + 31, "novas perdem, categoria A recupera", 14.5, MUTED, 500))
    out.append(
        t(
            centro,
            y + 21,
            f"novas perdem {num(nr['flavio'])} (F) e {num(nr['lula'])} (L); A recupera {num(abs(ga['flavio']))} e {num(abs(ga['lula']))}",
            15.5,
            INK,
            600,
            "middle",
        )
    )
    out.append(t(1000, y + 21, f"{num(saldo)} a favor de Lula", 16, LULA, 800, "end"))
    return "".join(out)


def _dose() -> str:
    EF = dados()["efeito_1t"]
    faixas = [
        f for f in EF["dose_resposta"]["faixas"] if not f["faixa"].startswith("sem ")
    ]
    media = EF["dif_em_dif"]["diferenca"]["mesmo_municipio"]["diferenca_pp"]["valor"]
    x_min, x_max, ini, fim = -0.6, 4.4, 250, 800
    esc_ = (fim - ini) / (x_max - x_min)

    def px(v):
        return ini + (v - x_min) * esc_

    topo = 452
    out = [
        t(
            0,
            topo - 28,
            "Abstenção a mais por distância percorrida, 1º turno (ponto percentual)",
            20,
            INK,
            700,
        ),
        t(
            0,
            topo - 8,
            "Diferença em diferenças contra 2022, categoria A, com intervalo de 95%",
            15.5,
            MUTED,
            500,
        ),
    ]
    passo = 38
    base = topo + 14 + len(faixas) * passo
    for v in range(5):
        out.append(ln(px(v), topo + 8, px(v), base - 6, GRID, 1))
        out.append(t(px(v), base + 14, f"{v}", 15, MUTED, 500, "middle"))
    out.append(ln(px(0), topo + 8, px(0), base - 6, INK, 2))
    out.append(ln(px(media), topo + 8, px(media), base - 6, VERDE, 2, "6 4"))
    out.append(
        _rotulo(
            px(media) + 6,
            base + 30,
            f"efeito geral {num(media, 2)}",
            15.5,
            VERDE,
            PAPER,
            "start",
            700,
        )
    )
    for i, f in enumerate(faixas):
        d = f["dif_em_dif"]["mesmo_municipio"]["diferenca_pp"]
        y = topo + 30 + i * passo
        sig = d["ic95"][0] > 0
        out.append(t(0, y + 5, f["faixa"], 17, INK, 700))
        out.append(
            t(160, y + 5, f"{num(f['urnas_casadas_2022'])} urnas", 14.5, MUTED, 500)
        )
        out.append(ln(px(d["ic95"][0]), y, px(d["ic95"][1]), y, OURO_TXT, 3.2))
        out.append(ln(px(d["ic95"][0]), y - 6, px(d["ic95"][0]), y + 6, OURO_TXT, 3))
        out.append(ln(px(d["ic95"][1]), y - 6, px(d["ic95"][1]), y + 6, OURO_TXT, 3))
        out.append(
            circ(
                px(d["valor"]),
                y,
                7.5,
                OURO_TXT if sig else PAPER,
                f' stroke="{OURO_TXT}" stroke-width="2.5"',
            )
        )
        out.append(
            t(
                1000,
                y + 5,
                f"{sinal(d['valor'])} ({sinal(d['ic95'][0], 2).lstrip('+')} a {sinal(d['ic95'][1], 2).lstrip('+')})",
                16,
                INK,
                700,
                "end",
            )
        )
    out.append(
        t(
            0,
            base + 44,
            "Ponto cheio: o intervalo não inclui zero. Ponto vazio: inclui.",
            15,
            MUTED,
            500,
        )
    )
    return "".join(out)


def fig_cenarios() -> str:
    return svg(
        _divergentes() + _dose(),
        "Votos perdidos por candidatura em cada cenário e abstenção por distância",
        W,
        H3,
    )


__all__ = ["esc", "fig_alerta", "fig_cenarios", "fig_numeros", "pontos_origem"]
