"""Figuras de mapa de pontos do Senado de 2027: dispersão K x C, curva de K e relatórios."""

from __future__ import annotations

import math
import statistics

from .figuras_base import (
    BLOCOS,
    BORDA_BLOCO,
    COR_BLOCO,
    FAIXAS_K,
    GOLD,
    GRID,
    INK,
    MUTED,
    NEUTRO,
    RED,
    ROTULO_ALVO,
    ROTULO_BLOCO,
    ROTULO_CENARIO,
    TEAL,
    esc,
    figura,
    fmt,
    largura,
    ocupantes,
    sigla,
    svg,
    txt,
    valor_c,
    valor_k,
)

# Resolvedor de rótulos


def _caixa(anchor: str, x: float, y: float, w: float, tamanho: float):
    x0 = {"start": x, "end": x - w, "middle": x - w / 2}[anchor]
    return (x0 - 3, y - tamanho * 0.82, x0 + w + 3, y + tamanho * 0.22)


def _sobrepoe(a, b) -> float:
    dx = min(a[2], b[2]) - max(a[0], b[0])
    dy = min(a[3], b[3]) - max(a[1], b[1])
    return dx * dy if dx > 0 and dy > 0 else 0.0


def resolver_rotulos(
    pontos: list[tuple[float, float, float, str]],
    obstaculos: list[tuple[float, float, float, float]],
    limites: tuple[float, float, float, float],
    tamanho: float = 13,
) -> list[dict]:
    """Posiciona um rótulo por ponto sem sobrepor pontos, rótulos e obstáculos.

    Tenta oito posições junto ao ponto e depois posições afastadas com linha de
    chamada; se nada couber, fica com a de menor sobreposição.
    """
    ocupado = list(obstaculos)
    saida = []
    for x, y, r, texto in pontos:
        w = largura(texto, tamanho)
        base = tamanho * 0.32
        cands = [
            ("start", x + r + 7, y + base, False),
            ("end", x - r - 7, y + base, False),
            ("start", x + r + 5, y - r - 4, False),
            ("start", x + r + 5, y + r + tamanho * 0.82 + 3, False),
            ("end", x - r - 5, y - r - 4, False),
            ("end", x - r - 5, y + r + tamanho * 0.82 + 3, False),
            ("middle", x, y - r - 4, False),
            ("middle", x, y + r + tamanho * 0.82 + 3, False),
        ]
        for dx in (14, 34):
            for passo in range(0 if dx > 14 else 1, 10):
                for sinal in (-1, 1):
                    dy = sinal * passo * tamanho * 1.05
                    cands.append(("start", x + r + dx, y + base + dy, True))
                    cands.append(("end", x - r - dx, y + base + dy, True))
        melhor = None
        for anchor, tx, ty, chamada in cands:
            cx = _caixa(anchor, tx, ty, w, tamanho)
            if (
                cx[0] < limites[0]
                or cx[2] > limites[2]
                or cx[1] < limites[1]
                or cx[3] > limites[3]
            ):
                continue
            custo = sum(_sobrepoe(cx, o) for o in ocupado)
            if custo == 0:
                melhor = (0.0, anchor, tx, ty, chamada, cx)
                break
            if melhor is None or custo < melhor[0]:
                melhor = (custo, anchor, tx, ty, chamada, cx)
        if melhor is None:
            anchor, tx, ty, chamada = "start", x + r + 3, y + base, False
            cx = _caixa(anchor, tx, ty, w, tamanho)
        else:
            _, anchor, tx, ty, chamada, cx = melhor
        ocupado.append(cx)
        saida.append(
            {
                "texto": texto,
                "anchor": anchor,
                "x": tx,
                "y": ty,
                "chamada": chamada,
                "px": x,
                "py": y,
                "caixa": cx,
            }
        )
    return saida


def _espalhar(pontos: list[list[float]], r: float) -> None:
    """Afasta pontos coincidentes em espiral curta (in place): x, y, ..."""
    postos: list[tuple[float, float]] = []
    for p in pontos:
        x0, y0 = p[0], p[1]
        ang, raio = 0.0, 0.0
        x, y = x0, y0
        while any(math.hypot(x - a, y - b) < 2 * r - 1.5 for a, b in postos):
            ang += 2.4
            raio += r * 0.32
            x = x0 + raio * math.cos(ang)
            y = y0 + raio * math.sin(ang)
        p[0], p[1] = x, y
        postos.append((x, y))


# 1. Dispersão K × C


def dispersao_k_c(data: dict, cenario: str = "flavio", alvo: str = "C_imp") -> str:
    W, H = 960.0, 720.0
    x0, x1, y0, y1 = 78.0, 940.0, 22.0, 594.0
    c_min, c_max = -12.0, 112.0

    k_min, k_max = -4.0, 102.0

    def px(k: float) -> float:
        return x0 + (x1 - x0) * (k - k_min) / (k_max - k_min)

    def py(c: float) -> float:
        return y1 - (y1 - y0) * (c - c_min) / (c_max - c_min)

    pessoas = ocupantes(data, cenario)
    pts = []
    for p in pessoas:
        k, c = valor_k(p), valor_c(p, cenario, alvo)
        pts.append([px(k), py(c), k, c, p])
    pts.sort(key=lambda q: (BLOCOS.index(q[4]["bloco"]), q[4]["nome"]))
    raio = 6.0
    _espalhar(pts, raio)

    q = {
        "ep": sum(1 for _, _, k, c, _ in pts if k >= 35 and c >= 50),
        "ec": sum(1 for _, _, k, c, _ in pts if k >= 35 and c < 50),
        "pp": sum(1 for _, _, k, c, _ in pts if k < 35 and c >= 50),
        "pc": sum(1 for _, _, k, c, _ in pts if k < 35 and c < 50),
    }
    corpo = []
    # grade e eixos
    for c in range(0, 101, 20):
        corpo.append(
            f'<line x1="{x0}" x2="{x1}" y1="{py(c):.1f}" y2="{py(c):.1f}" '
            f'stroke="{GRID}" stroke-width="1"/>'
        )
        corpo.append(txt(x0 - 10, py(c) + 5, str(c), 14, "end", cor=MUTED))
    for k in range(0, 101, 20):
        corpo.append(
            f'<line x1="{px(k):.1f}" x2="{px(k):.1f}" y1="{y0}" y2="{y1}" '
            f'stroke="{GRID}" stroke-width="1"/>'
        )
        corpo.append(txt(px(k), y1 + 22, str(k), 14, "middle", cor=MUTED))
    corpo.append(
        txt(
            (x0 + x1) / 2,
            y1 + 50,
            "K, exposição judicial documentada (0 a 100)",
            15,
            "middle",
            600,
        )
    )
    corpo.append(
        txt(
            18,
            (y0 + y1) / 2,
            f"C, contrapeso no {ROTULO_ALVO[alvo]} (0 a 100)",
            15,
            "middle",
            600,
            extra=f' transform="rotate(-90 18 {(y0 + y1) / 2:.1f})"',
        )
    )
    # linhas de corte
    corpo.append(
        f'<line x1="{x0}" x2="{x1}" y1="{py(50):.1f}" y2="{py(50):.1f}" '
        f'stroke="{INK}" stroke-width="1.6" stroke-dasharray="3 4"/>'
    )
    corpo.append(
        f'<line x1="{px(35):.1f}" x2="{px(35):.1f}" y1="{y0}" y2="{y1}" '
        f'stroke="{INK}" stroke-width="1.6" stroke-dasharray="3 4"/>'
    )
    # quadrantes nas faixas acima de 100 e abaixo de 0, sem cobrir pontos
    quad = [
        (px(35) + 8, py(106), "start", f"Exposto e pró: {q['ep']}"),
        (x1 - 4, py(-7), "end", f"Exposto e contra: {q['ec']}"),
        (px(35) - 8, py(106), "end", f"Pouco exposto e pró: {q['pp']}"),
        (px(35) - 8, py(-7), "end", f"Pouco exposto e contra: {q['pc']}"),
    ]
    obst = []
    for x, y, anchor, rot in quad:
        corpo.append(txt(x, y, rot.upper(), 14, anchor, 700, MUTED))
        obst.append(_caixa(anchor, x, y, largura(rot, 14), 14))
    obst.append(_caixa("start", px(35) + 6, py(50) - 6, largura("C = 50", 13), 13))
    corpo.append(txt(x1 - 4, py(50) - 6, "C = 50", 13, "end", cor=MUTED))
    obst.append(_caixa("end", x1 - 4, py(50) - 6, largura("C = 50", 13), 13))
    corpo.append(txt(px(35) + 6, y1 - 8, "K = 35", 13, "start", cor=MUTED))
    obst.append(_caixa("start", px(35) + 6, y1 - 8, largura("K = 35", 13), 13))

    marcas = []
    for x, y, k, c, p in pts:
        b = p["bloco"]
        marcas.append(
            f'<circle class="sn27-ponto" data-slug="{esc(p["slug"])}" cx="{x:.1f}" '
            f'cy="{y:.1f}" r="{raio}" fill="{COR_BLOCO[b]}" stroke="{BORDA_BLOCO[b]}" '
            f'stroke-width="1.2" fill-opacity="0.9"><title>{esc(p["nome"])} '
            f"({esc(sigla(p))}), {ROTULO_BLOCO[b]}: K {fmt(k, 1)}, C {fmt(c, 1)}"
            "</title></circle>"
        )
        obst.append((x - raio, y - raio, x + raio, y + raio))

    alvos = [
        (x, y, raio, p["nome"]) for x, y, k, c, p in pts if k >= 20 or 35 <= c <= 80
    ]
    # primeiro os mais isolados à direita, depois o miolo
    alvos.sort(key=lambda a: -a[0])
    rot = resolver_rotulos(alvos, obst, (x0 + 2, y0, x1, y1 - 2), 13)
    rotulos = []
    for r in rot:
        if r["chamada"]:
            cx = r["caixa"]
            lx = cx[0] if r["anchor"] == "start" else cx[2]
            ly = (cx[1] + cx[3]) / 2
            rotulos.append(
                f'<line x1="{r["px"]:.1f}" y1="{r["py"]:.1f}" x2="{lx:.1f}" '
                f'y2="{ly:.1f}" stroke="{MUTED}" stroke-width="0.8"/>'
            )
        rotulos.append(
            f'<text x="{r["x"]:.1f}" y="{r["y"]:.1f}" font-size="13" '
            f'text-anchor="{r["anchor"]}" fill="{INK}" paint-order="stroke" '
            f'stroke="#f4f0e6" stroke-width="3" stroke-linejoin="round">'
            f'{esc(r["texto"])}</text>'
        )

    legenda_svg = []
    for i, b in enumerate(BLOCOS):
        n = sum(1 for *_, p in pts if p["bloco"] == b)
        rot_b = f"{ROTULO_BLOCO[b]} ({n})"
        lx = x0 + 6 + (i % 3) * 290
        ly = H - 40 + (i // 3) * 24
        legenda_svg.append(
            f'<circle cx="{lx + 6:.1f}" cy="{ly - 5:.1f}" r="6" fill="{COR_BLOCO[b]}" '
            f'stroke="{BORDA_BLOCO[b]}" stroke-width="1.2"/>'
        )
        legenda_svg.append(txt(lx + 18, ly, rot_b, 14))

    corpo_final = "".join(corpo + marcas + rotulos + legenda_svg)
    n_rot = len(alvos)
    rotulo = (
        f"Dispersão dos 81 senadores de 2027, {ROTULO_CENARIO[cenario]}: K no eixo "
        f"horizontal e C do {ROTULO_ALVO[alvo]} no vertical. {q['ep']} exposto e pró, "
        f"{q['ec']} exposto e contra, {q['pp']} pouco exposto e pró, "
        f"{q['pc']} pouco exposto e contra."
    )
    legenda = (
        f"Cada ponto é um senador de 2027 no {ROTULO_CENARIO[cenario]}. Quanto mais à "
        "direita, mais procedimento judicial documentado (K); quanto mais alto, mais "
        f"sinais públicos de contrapeso ao STF no {ROTULO_ALVO[alvo]} (C). "
        f"{q['ep']} senadores ficam no quadrante exposto e pró, {q['ec']} no exposto e "
        f"contra, {q['pp']} no pouco exposto e pró e {q['pc']} no pouco exposto e "
        f"contra. Os {n_rot} nomes escritos são os mais expostos (K de 20 ou mais) e "
        "os de posição incerta (C de 35 a 80). Linhas pontilhadas em C = 50 e K = 35. "
        "K não é culpa e C não é voto: são réguas sobre documentos públicos."
    )
    return figura(
        "sn27-fig-wide sn27-fig-dispersao",
        svg(W, H, rotulo, corpo_final, "sn27-svg-dispersao"),
        legenda,
    )


# 5. Curva de K


def curva_k(data: dict, cenario: str = "flavio") -> str:
    pessoas = ocupantes(data, cenario)
    ks = [valor_k(p) for p in pessoas]
    contagem = [
        sum(1 for k in ks if (k == 0 if hi == 0 else lo <= k <= hi))
        for lo, hi, _ in FAIXAS_K
    ]
    med, media = statistics.median(ks), statistics.fmean(ks)
    W, H = 960.0, 450.0
    x0, x1, y0, y1 = 50.0, 560.0, 100.0, 380.0
    topo = max(contagem)
    bw = (x1 - x0) / len(FAIXAS_K)
    corpo = [
        txt(x0, 30, f"Mediana {fmt(med, 1)}, média {fmt(media, 1)}", 17, "start", 700),
        txt(x0, 52, "senadores por faixa de K", 14, cor=MUTED),
    ]
    for i, ((_, _, rot), n) in enumerate(zip(FAIXAS_K, contagem, strict=True)):
        h = (y1 - y0) * n / topo
        x = x0 + i * bw
        cor = NEUTRO if i == 0 else GOLD
        corpo.append(
            f'<rect x="{x + 8:.1f}" y="{y1 - h:.1f}" width="{bw - 16:.1f}" '
            f'height="{h:.1f}" fill="{cor}"><title>K {rot}: {n} senadores</title></rect>'
        )
        corpo.append(txt(x + bw / 2, y1 - h - 8, str(n), 18, "middle", 700))
        corpo.append(txt(x + bw / 2, y1 + 22, rot, 14, "middle", cor=MUTED))
    corpo.append(
        f'<line x1="{x0}" x2="{x1}" y1="{y1}" y2="{y1}" stroke="{INK}"/>'
        + txt(
            (x0 + x1) / 2,
            y1 + 48,
            "K, exposição judicial documentada",
            14,
            "middle",
            cor=MUTED,
        )
    )
    top = data["ranking"]["K"][:10]
    por_slug = {p["slug"]: p for p in pessoas}
    corpo.append(txt(620, 30, "Os 10 maiores K", 17, "start", 700))
    escala = 0.8
    for i, r in enumerate(top):
        y = 62 + i * 33
        p = por_slug.get(r["slug"])
        sig = sigla(p) if p else r["uf"]
        corpo.append(txt(620, y + 12, r["nome"], 14, "start", 700))
        corpo.append(txt(620, y + 28, sig, 12, cor=MUTED))
        w = r["valor"] * escala
        corpo.append(
            f'<rect x="{810:.1f}" y="{y + 2}" width="{w:.1f}" height="14" '
            f'fill="{GOLD}"><title>{esc(r["nome"])}: K {fmt(r["valor"], 1)}</title></rect>'
        )
        corpo.append(txt(810 + w + 6, y + 14, fmt(r["valor"], 1), 13, "start", 700))
    n0 = contagem[0]
    n60 = sum(1 for k in ks if k >= 60)
    n20 = sum(1 for k in ks if k >= 20)
    rotulo = (
        "Barras de senadores por faixa de K: "
        + "; ".join(
            f"K {rot}: {n}" for (_, _, rot), n in zip(FAIXAS_K, contagem, strict=True)
        )
        + f". Mediana {fmt(med, 1)}, média {fmt(media, 1)}."
    )
    legenda = (
        f"K tem forma de L: {n0} dos 81 senadores não têm nenhum procedimento "
        f"localizado nas fontes desta pesquisa, {contagem[1]} têm só casos leves "
        f"(K de 1 a 19), {n20} passam de 20 e apenas {n60} passam de 60. A mediana "
        f"é {fmt(med, 1)} e a média, {fmt(media, 1)}, puxada pela cauda. K = 0 quer "
        "dizer nada localizado, não certidão negativa."
    )
    return figura(
        "sn27-fig-wide sn27-fig-curva-k",
        svg(W, H, rotulo, "".join(corpo), "sn27-svg-curva-k"),
        legenda,
        "curva-k",
    )


# 6. Dispersão entre relatórios

RELATORIOS = (
    ("claude", "Claude", TEAL, "circulo"),
    ("gemini", "Gemini", GOLD, "quadrado"),
    ("chatgpt", "ChatGPT", RED, "triangulo"),
)


def _marcador(forma: str, x: float, y: float, cor: str, titulo: str) -> str:
    t = f"<title>{esc(titulo)}</title>"
    if forma == "circulo":
        return (
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7.5" fill="none" stroke="{cor}" '
            f'stroke-width="2">{t}</circle>'
        )
    if forma == "quadrado":
        return (
            f'<rect x="{x - 4.5:.1f}" y="{y - 4.5:.1f}" width="9" height="9" '
            f'fill="none" stroke="{cor}" stroke-width="2">{t}</rect>'
        )
    return (
        f'<path d="M{x:.1f} {y - 6:.1f}L{x + 5.5:.1f} {y + 4:.1f}L{x - 5.5:.1f} '
        f'{y + 4:.1f}Z" fill="none" stroke="{cor}" stroke-width="2">{t}</path>'
    )


def dispersao_relatorios(data: dict) -> str:
    pessoas = ocupantes(data, "flavio")
    linhas = []
    for p in pessoas:
        ant = p.get("scores_anteriores") or {}
        vals = {}
        for chave, *_ in RELATORIOS:
            r = ant.get(chave)
            if isinstance(r, dict) and isinstance(r.get("K"), int | float):
                vals[chave] = float(r["K"])
        if vals:
            linhas.append((p, valor_k(p), vals))
    W, H = 960.0, 600.0
    x0, x1, y0, y1 = 80.0, 640.0, 40.0, 540.0

    def px(v: float) -> float:
        return x0 + (x1 - x0) * v / 100

    def py(v: float) -> float:
        return y1 - (y1 - y0) * v / 100

    corpo = []
    for v in range(0, 101, 20):
        corpo.append(
            f'<line x1="{x0}" x2="{x1}" y1="{py(v):.1f}" y2="{py(v):.1f}" stroke="{GRID}"/>'
            f'<line x1="{px(v):.1f}" x2="{px(v):.1f}" y1="{y0}" y2="{y1}" stroke="{GRID}"/>'
        )
        corpo.append(txt(x0 - 10, py(v) + 5, str(v), 14, "end", cor=MUTED))
        corpo.append(txt(px(v), y1 + 22, str(v), 14, "middle", cor=MUTED))
    corpo.append(
        f'<line x1="{px(0):.1f}" y1="{py(0):.1f}" x2="{px(100):.1f}" y2="{py(100):.1f}" '
        f'stroke="{INK}" stroke-width="1.4" stroke-dasharray="5 4"/>'
    )
    corpo.append(txt(px(78), py(84) - 6, "mesma nota", 13, "end", cor=MUTED))
    corpo.append(txt((x0 + x1) / 2, H - 14, "K da régua da casa", 15, "middle", 600))
    corpo.append(
        txt(
            22,
            (y0 + y1) / 2,
            "K dado por cada relatório de IA",
            15,
            "middle",
            600,
            extra=f' transform="rotate(-90 22 {(y0 + y1) / 2:.1f})"',
        )
    )
    spreads = []
    desvios = []
    for p, k, vals in linhas:
        x = px(k)
        vs = list(vals.values())
        if len(vs) > 1:
            spreads.append((max(vs) - min(vs), p["nome"]))
            corpo.append(
                f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{py(min(vs)):.1f}" '
                f'y2="{py(max(vs)):.1f}" stroke="{NEUTRO}" stroke-width="2"/>'
            )
        for chave, nome, cor, forma in RELATORIOS:
            if chave in vals:
                desvios.append(abs(vals[chave] - k))
                corpo.append(
                    _marcador(
                        forma,
                        x,
                        py(vals[chave]),
                        cor,
                        f"{p['nome']}: {nome} deu K {fmt(vals[chave])}, régua "
                        f"{fmt(k, 1)}",
                    )
                )
    # legenda e números à direita
    lx = 680.0
    corpo.append(txt(lx, 56, "Cada relatório", 16, "start", 700))
    for i, (_, nome, cor, forma) in enumerate(RELATORIOS):
        y = 86 + i * 26
        corpo.append(_marcador(forma, lx + 8, y - 5, cor, nome))
        corpo.append(txt(lx + 24, y, nome, 15))
    corpo.append(
        f'<line x1="{lx + 8}" x2="{lx + 8}" y1="{86 + 3 * 26 - 14}" '
        f'y2="{86 + 3 * 26 + 2}" stroke="{NEUTRO}" stroke-width="2"/>'
        + txt(lx + 24, 86 + 3 * 26, "do menor ao maior K", 15)
    )
    grandes = sorted(spreads, reverse=True)
    n20 = sum(1 for s, _ in spreads if s > 20)
    erro_medio = statistics.fmean(desvios) if desvios else 0.0
    corpo.append(txt(lx, 240, "Maiores divergências", 16, "start", 700))
    for i, (s, nome) in enumerate(grandes[:6]):
        corpo.append(txt(lx, 266 + i * 22, f"{nome}: {fmt(s)} pontos", 14))
    corpo.append(
        txt(lx, 420, f"Em {n20} senadores os", 14, cor=MUTED)
        + txt(lx, 440, "relatórios se afastam mais", 14, cor=MUTED)
        + txt(lx, 460, "de 20 pontos entre si.", 14, cor=MUTED)
    )
    rotulo = (
        f"Pontos ligados para {len(linhas)} senadores: K da régua da casa no eixo "
        "horizontal e K de cada relatório de IA no vertical. Em "
        f"{n20} senadores os relatórios divergem mais de 20 pontos entre si."
    )
    legenda = (
        f"Para {len(linhas)} senadores, os relatórios do Claude, do Gemini e do "
        "ChatGPT deram notas de exposição diferentes; o traço cinza liga a menor à "
        f"maior. Em {n20} casos a distância passa de 20 pontos, e a diferença média "
        f"entre um relatório e a régua da casa é de {fmt(erro_medio, 1)} pontos. "
        "Nenhum score foi copiado: a régua única recalculou todos a partir dos "
        "documentos."
    )
    return figura(
        "sn27-fig-wide sn27-fig-relatorios",
        svg(W, H, rotulo, "".join(corpo), "sn27-svg-relatorios"),
        legenda,
        "dispersao-relatorios",
    )
