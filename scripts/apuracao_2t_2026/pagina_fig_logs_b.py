"""Figuras do capítulo "O que os logs das 499 mil urnas dizem", blocos 4 a 7.

- ``logs_cadencia``: cômputos por hora de Brasília, 1º turno (amostra) e 2º turno;
- ``logs_cadencia_regioes``: a mesma forma do dia, região por região;
- ``logs_reinicio_hora``: a hora do primeiro reinício durante a votação;
- ``logs_voto``: a fatia de Flávio nas seções com sinal, contra vizinhas e contra o 1º turno;
- ``logs_bateria_chuva``: bateria durante a votação por chuva prevista no município;
- ``logs_serie_mr``: a série da memória de resultado repetida;
- ``logs_integrado_mapa``: seções com escore do BU e atenção dos logs altos.

Fonte única: ``analysis/apuracao_2t_2026/dados/logs.json``.
"""

from __future__ import annotations

from apuracao_2026.pagina_comum import (
    CINZA,
    GOLD,
    INK,
    MUTED,
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
from apuracao_2026.pagina_mapas import pontos_brasil

from .pagina_fig_espelho import efeitos
from .pagina_fig_logs import COR_1T, COR_2T, VERMELHO, barras_h

HORAS = [str(h) for h in range(8, 20)]
ROT_HORA = {h: f"{int(h):02d}h" for h in HORAS}
ROT_HORA["19"] = "19h+"


# ------------------------------------------------------------------ 4. cadência


def _barras_horas(
    out: list,
    tips: Tips,
    x0: float,
    y0: float,
    larg: float,
    alt: float,
    p1: dict,
    p2: dict,
    vmax: float,
    rotulos: bool = True,
    titulo: str = "",
) -> None:
    passo = larg / len(HORAS)
    y = escala(0, vmax, y0 + alt, y0)
    if titulo:
        out.append(t(x0, y0 - 10, titulo, 14, INK, weight="700"))
    for v in range(0, int(vmax) + 1, 5 if vmax > 12 else 2):
        out.append(ln(x0, y(v), x0 + larg, y(v), GRADE, 1))
        out.append(t(x0 - 6, y(v) + 4, f"{v}%", 11, MUTED, "end", mono=True))
    for i, h in enumerate(HORAS):
        a, b = p1.get(h, 0.0), p2.get(h, 0.0)
        xa = x0 + i * passo + passo * 0.12
        bw = passo * 0.36
        partes = [
            r(xa, y(a), bw, y(0) - y(a), COR_1T),
            r(xa + bw, y(b), bw, y(0) - y(b), COR_2T),
        ]
        if rotulos:
            partes.append(
                t(
                    x0 + i * passo + passo / 2,
                    y0 + alt + 16,
                    ROT_HORA[h],
                    11,
                    INK,
                    "middle",
                    mono=True,
                )
            )
        k = tips.add(
            ficha(
                f"{ROT_HORA[h]} de Brasília",
                titulo or "Brasil",
                [("1º turno", f"{num(a, 2)}%"), ("2º turno", f"{num(b, 3)}%")],
            )
        )
        out.append(hit("".join(partes) + area(x0 + i * passo, y0, passo, alt), k))
    out.append(ln(x0, y(0), x0 + larg, y(0), MUTED, 1))


def fig_cadencia(L: dict) -> str:
    c = L["cadencia"]
    a = c["amostra_1t"]
    p1, p2 = a["brasil_1t"]["pct"], a["brasil_2t_mesmas"]["pct"]
    w, h = 1000, 420
    vmax = max([*p1.values(), *p2.values(), 1]) + 2
    out = [
        svg_abre(
            w,
            h,
            "Cômputos por hora de Brasília, 1º e 2º turno, nas mesmas seções",
            "Barras pareadas por hora, das 08h às 19h ou depois: parcela dos votos do dia computada em "
            "cada hora pelo relógio da urna, convertido para Brasília.",
        )
    ]
    tips = Tips()
    _barras_horas(out, tips, 70, 30, w - 100, h - 90, p1, p2, vmax)
    out.append("</svg>")
    leg = legenda_html(
        [
            ("1º turno (cinco cargos, seis votos)", COR_1T),
            ("2º turno (um ou dois votos)", COR_2T),
        ]
    )
    legenda = (
        f"Parcela dos cômputos do dia em cada hora, nas {inteiro(a['secoes'])} seções da amostra do 1º turno "
        "(uma em cada cinco, sorteio determinístico) e nas mesmas seções no 2º. Hora do relógio da urna "
        "convertida para Brasília pelo município. Depois das 17h o 2º turno tem "
        f"{inteiro(c['brasil_2t']['computados_17_19'])} cômputos no país inteiro, de "
        f"{num(c['brasil_2t']['computados'] / 1e6, 1)} milhões. Fonte: logs.json (cadencia)."
    )
    return figura_html("logs_cadencia", "".join(out), legenda, tips, minw=760, apos=leg)


def fig_cadencia_regioes(L: dict) -> str:
    reg = L["cadencia"]["regioes"]
    nomes = list(reg)
    col, lin = 3, 2
    pw, ph = 310, 190
    w = 60 + col * (pw + 40)
    h = lin * (ph + 80) + 20
    vmax = (
        max(
            max([*v["1t"]["pct"].values(), *v["2t"]["pct"].values()])
            for v in reg.values()
        )
        + 2
    )
    out = [
        svg_abre(
            w,
            h,
            "A forma do dia por região, 1º e 2º turno",
            "Cinco painéis, um por região, com as barras pareadas por hora de Brasília.",
        )
    ]
    tips = Tips()
    for i, nome in enumerate(nomes):
        cx, cy = i % col, i // col
        x0 = 60 + cx * (pw + 40)
        y0 = 40 + cy * (ph + 80)
        v = reg[nome]
        _barras_horas(
            out,
            tips,
            x0,
            y0,
            pw,
            ph,
            v["1t"]["pct"],
            v["2t"]["pct"],
            vmax,
            rotulos=True,
            titulo=f"{nome}: 17h–19h {num(v['1t']['pct_17_19'], 1)}% → {num(v['2t']['pct_17_19'], 2)}%",
        )
    out.append("</svg>")
    leg = legenda_html(
        [("1º turno, amostra", COR_1T), ("2º turno, todas as seções", COR_2T)]
    )
    legenda = (
        "Mesma conta da figura anterior, por região; no título de cada painel, a parcela dos votos "
        "computada entre 17h e 19h de Brasília no 1º e no 2º turno. Fonte: logs.json (cadencia.regioes)."
    )
    return figura_html(
        "logs_cadencia_regioes", "".join(out), legenda, tips, minw=900, apos=leg
    )


# ------------------------------------------------------------------ 5. reinícios, voto, bateria


def fig_reinicio_hora(L: dict) -> str:
    rh = L["reinicios"]["hora_brt"]
    linhas = [
        (f"{int(h):02d}h", n, INK, "primeiro reinício da seção nessa hora de Brasília")
        for h, n in sorted(rh.items(), key=lambda kv: int(kv[0]))
    ]
    legenda = (
        f"Seções com o sistema religado durante a votação, pela hora de Brasília do primeiro reinício "
        f"({inteiro(L['reinicios']['secoes'])} seções, exterior fora). A curva acompanha o movimento da "
        "manhã; não há concentração no fim da tarde. Fonte: logs.json (reinicios.hora_brt)."
    )
    return barras_h(
        "logs_reinicio_hora",
        "Hora do primeiro reinício durante a votação",
        "Barras horizontais com o número de seções por hora do primeiro reinício.",
        linhas,
        legenda,
        esq=120,
        w=900,
        passo=30,
    )


def _linhas_voto(L: dict) -> list[tuple[str, dict]]:
    out = [(v["grupo"], v) for v in L["reinicios"]["voto"]]
    out += [(v["grupo"], v) for v in L["bateria"]["voto"]]
    out.append(
        (
            "série da memória de resultado repetida (Brasil, sem exterior)",
            L["metadados"]["serie_mr"]["voto_estruturais_brasil"],
        )
    )
    out.append(
        ("escore do BU e atenção dos logs, ambos 2 ou mais", L["integrado"]["voto"])
    )
    return out


def fig_voto(L: dict) -> str:
    itens = []
    for nome, v in _linhas_voto(L):
        dd, cv = v["dif_em_dif_contra_1t"], v["contra_vizinhas_2t"]
        if dd["media_pp"] is None:
            continue
        itens.append(
            {
                "nome": nome,
                "n": dd["n"],
                "valor": dd["media_pp"],
                "intervalo": dd["ic95_pp"],
                "bruto": cv["media_pp"],
            }
        )
    return efeitos(
        "logs_voto",
        itens,
        "Lula e Flávio: mudanças associadas aos sinais dos logs",
        "Média ponderada pelos votos dos finalistas: mudança entre turnos nas seções com sinal menos a mudança "
        "nas vizinhas do município sem o sinal (cinco ou mais); exterior fora. Traços: intervalos de 95%. "
        "A ficha de cada ponto mostra também a diferença bruta do 2º turno. Fonte: logs.json.",
    )


def fig_bateria_chuva(L: dict) -> str:
    f = [x for x in L["bateria"]["por_chuva_prevista"] if x["secoes"]]
    w, esq = 1000, 230
    topo, passo = 40, 52
    h = topo + passo * len(f) + 30
    vmax = max(x["pct_bateria_votacao"] for x in f) + 2
    xs = escala(0, vmax, esq, w - 160)
    out = [
        svg_abre(
            w,
            h,
            "Bateria durante a votação por chuva prevista no município",
            "Para cada faixa de chuva prevista para 25/10, a parcela das seções com passagem para bateria "
            "durante a votação, separada em junto com o município, só nesta urna e o resto.",
        )
    ]
    tips = Tips()
    for i, x_ in enumerate(f):
        y = topo + i * passo
        loc, iso, tot = x_["pct_local"], x_["pct_isolada"], x_["pct_bateria_votacao"]
        resto = max(tot - loc - iso, 0)
        a1, a2, a3 = xs(loc), xs(loc + iso), xs(loc + iso + resto)
        partes = [
            t(
                esq - 12,
                y + 22,
                f"{x_['faixa']} ({inteiro(x_['secoes'])})",
                14,
                INK,
                "end",
            ),
            r(esq, y + 8, a1 - esq, 22, INK),
            r(a1, y + 8, a2 - a1, 22, GOLD),
            r(a2, y + 8, a3 - a2, 22, CINZA),
            t(a3 + 8, y + 24, f"{num(tot, 1)}%", 14, INK, mono=True),
        ]
        k = tips.add(
            ficha(
                f"Chuva prevista {x_['faixa']}",
                f"{inteiro(x_['secoes'])} seções",
                [
                    ("bateria na votação, total", f"{num(tot, 2)}%"),
                    ("junto com outras urnas do município", f"{num(loc, 2)}%"),
                    ("só nesta urna", f"{num(iso, 2)}%"),
                ],
            )
        )
        out.append(hit("".join(partes) + area(0, y, w, passo), k, foco=True))
    out.append(ln(esq, topo, esq, h - 20, MUTED, 1))
    out.append("</svg>")
    leg = legenda_html(
        [
            ("junto com 5 ou mais urnas do município", INK),
            ("só nesta urna", GOLD),
            ("de 1 a 4 coincidentes", CINZA),
        ]
    )
    ref = L["bateria"].get("referencia_1t")
    ref_txt = (
        f" No 1º turno, com chuva observada (ERA5), a bateria durante a votação foi de {num(ref['seca_pct'], 2)}% "
        f"na seca a {num(ref['forte_pct'], 2)}% com chuva forte nas horas de votação."
        if ref
        else ""
    )
    legenda = (
        f"Seções do país por faixa de chuva prevista (08h–17h) no município. Fonte da chuva: {L['bateria']['fonte_chuva']}."
        f"{ref_txt} Fonte: logs.json (bateria)."
    )
    return figura_html(
        "logs_bateria_chuva", "".join(out), legenda, tips, minw=760, apos=leg
    )


# ------------------------------------------------------------------ 6. metadados


def fig_serie_mr(L: dict) -> str:
    s = L["metadados"]["serie_mr"]
    linhas = [
        (
            f"{e['serie']} · {', '.join(z.replace('ZZ-1', 'exterior') for z in e['zonas'])}",
            e["secoes"],
            INK,
            f"{e['municipios']} município(s); contagem confere em {e['contagem_confere']}; "
            f"único valor do log inteiro, inclusive o trecho do 1º turno, em {e['so_esse_valor_no_log_todo']}.",
        )
        for e in s["estruturais"]
    ]
    linhas.append(
        (
            "pares entre lugares distantes (observados)",
            s["pares_entre_lugares"],
            GOLD,
            "Dois valores iguais em seções de UFs ou zonas diferentes.",
        )
    )
    linhas.append(
        (
            "pares esperados por acaso (32 bits)",
            s["pares_esperados_por_acaso_32_bits"],
            CINZA,
            "n(n−1)/2 dividido por 2³² com n igual ao número de valores distintos.",
        )
    )
    legenda = (
        f"Séries da memória de resultado registradas no dia: {inteiro(s['valores_distintos'])} valores; "
        f"{inteiro(s['repetidos'])} aparecem em mais de uma seção. Os grupos grandes ficam dentro de uma só "
        "zona; os pares soltos batem com o acaso de um número de 32 bits. Fonte: logs.json (metadados)."
    )
    return barras_h(
        "logs_serie_mr",
        "Série da memória de resultado repetida entre seções",
        "Barras com o número de seções de cada grupo com a mesma série da memória de resultado, mais os "
        "pares entre lugares distantes contra o esperado por acaso.",
        linhas,
        legenda,
        esq=430,
    )


# ------------------------------------------------------------------ 7. escore integrado

COR_ESCORE = {2: GOLD, 3: VERMELHO, 4: "#6b4a92"}


def fig_integrado_mapa(L: dict) -> str:
    ig = L["integrado"]
    sec = [
        s for s in ig["secoes"] if s.get("lat") is not None and s.get("lon") is not None
    ]
    pontos = []
    for s in sec:
        e = min(s["escore_bu"], 4)
        pontos.append(
            {
                "lat": s["lat"],
                "lon": s["lon"],
                "raio": 4.0
                + 0.01
                * (
                    4 - e
                ),  # escore maior por cima (pontos_brasil desenha do maior raio ao menor)
                "cor": COR_ESCORE[e],
                "titulo": (
                    f"{s.get('municipio') or s['mun']} ({s['uf']}), zona {s['zona']}, seção {s['secao']}: "
                    f"escore do BU {s['escore_bu']}, atenção dos logs {s['atencao_log']}"
                ),
                "rotulo": (
                    f"{s.get('municipio')} {s['zona']}/{s['secao']}"
                    if s["escore_bu"] >= 4
                    else ""
                ),
            }
        )
    svg = pontos_brasil(
        pontos,
        "Seções com escore do BU e atenção dos logs altos no 2º turno",
        "Pontos dos locais de votação sobre o contorno das UFs; cor pelo escore do BU.",
        rotulos=10,
    )
    svg = svg.replace('viewBox="0 0 640 640"', 'viewBox="0 0 800 640"', 1)
    leg = legenda_html(
        [
            ("escore do BU 2", GOLD),
            ("escore 3", VERMELHO),
            ("escore 4 ou mais", "#6b4a92"),
        ],
        "Cor: escore do BU (todas com atenção dos logs 2 ou 3)",
    )
    legenda = (
        f"{inteiro(len(sec))} de {inteiro(ig['as_duas'])} seções com as duas marcas e coordenada do local de "
        "votação (Politize). O ponto é o prédio, não o eleitor. Fonte: logs.json (integrado)."
    )
    return figura_html(
        "logs_integrado_mapa", svg, legenda, Tips(), modo="fit", apos=leg, dim=False
    )
