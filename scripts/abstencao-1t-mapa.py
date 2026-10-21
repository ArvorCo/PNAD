#!/usr/bin/env python3
"""Mapa quadrado (1:1) da abstenção no 1º turno de 2026, município por município.

Lê `analysis/apuracao_2026/dados/presidente.json` (comparecimento por município, UF e
região, boletins de urna do TSE) e as malhas compactas do IBGE em `apuracao/public/geo/`
(municípios por UF e contorno dos estados). Monta um HTML com SVG embutido, sem rede além
das fontes do Google, e o renderiza em PNG 2160×2160 com Playwright.

Saídas: `docs/assets/abstencao_1t_2026_mapa.html` (fonte) e `docs/img/abstencao_1t_2026.png`.
Abstenção = 100 - pct_comparecimento. O exterior (ZZ) fica fora do mapa e entra como nota.

Uso: python3 scripts/abstencao-1t-mapa.py [--sem-png]
"""

from __future__ import annotations

import argparse
import json
import math
from itertools import pairwise
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRESIDENTE = ROOT / "analysis" / "apuracao_2026" / "dados" / "presidente.json"
GEO = ROOT / "apuracao" / "public" / "geo"
HTML = ROOT / "docs" / "assets" / "abstencao_1t_2026_mapa.html"
PNG = ROOT / "docs" / "img" / "abstencao_1t_2026.png"

LADO = 1080  # viewport; o PNG sai com DSF 2 (2160 px)
MAPA = (56, 176, 700, 664)  # x, y, largura, altura da área do mapa no SVG

# Escala de cor: abstenção baixa em verde-água, alta em vermelho. Cortes em pontos
# percentuais; fora da faixa a cor satura.
ESCALA = [
    (12.0, (18, 128, 142)),
    (17.0, (42, 154, 176)),
    (20.0, (120, 185, 170)),
    (22.0, (240, 200, 107)),
    (25.0, (244, 150, 78)),
    (30.0, (255, 90, 78)),
    (38.0, (143, 29, 44)),
]

REGIAO_COR = {
    "Norte": "#2bb98a",
    "Nordeste": "#5fd3e6",
    "Centro-Oeste": "#f0c86b",
    "Sudeste": "#ff8a7a",
    "Sul": "#8f9ff5",
}

# Rótulo de cada UF no mapa: deslocamento em px a partir do centróide do maior polígono,
# para as siglas pequenas do litoral não se sobreporem.
DESLOCA = {
    "DF": (12, -12),
    "SE": (22, 6),
    "AL": (24, 2),
    "PB": (26, -3),
    "RN": (22, -10),
    "PE": (-4, 6),
    "ES": (22, 2),
    "RJ": (18, 14),
    "SC": (18, 2),
    "AP": (0, -4),
}

# Estados pequenos ou colados: só a sigla no mapa; o valor fica no ranking ao lado.
SO_SIGLA = {"DF", "SE", "AL", "PB", "RN", "PE", "ES"}

MINUSCULAS = {"de", "do", "da", "dos", "das", "e", "d'"}


def nome_proprio(texto: str) -> str:
    """Caixa alta só nas iniciais, com as preposições em minúscula."""
    palavras = texto.lower().split()
    return " ".join(
        p if (i and p in MINUSCULAS) else p.capitalize() for i, p in enumerate(palavras)
    )


# Código IBGE de dois dígitos de cada UF, chave da malha `br_uf.geojson` (`codarea`).
CODIGO_UF = {
    "11": "RO",
    "12": "AC",
    "13": "AM",
    "14": "RR",
    "15": "PA",
    "16": "AP",
    "17": "TO",
    "21": "MA",
    "22": "PI",
    "23": "CE",
    "24": "RN",
    "25": "PB",
    "26": "PE",
    "27": "AL",
    "28": "SE",
    "29": "BA",
    "31": "MG",
    "32": "ES",
    "33": "RJ",
    "35": "SP",
    "41": "PR",
    "42": "SC",
    "43": "RS",
    "50": "MS",
    "51": "MT",
    "52": "GO",
    "53": "DF",
}

NOME_UF = {
    "AC": "Acre",
    "AL": "Alagoas",
    "AM": "Amazonas",
    "AP": "Amapá",
    "BA": "Bahia",
    "CE": "Ceará",
    "DF": "Distrito Federal",
    "ES": "Espírito Santo",
    "GO": "Goiás",
    "MA": "Maranhão",
    "MG": "Minas Gerais",
    "MS": "Mato Grosso do Sul",
    "MT": "Mato Grosso",
    "PA": "Pará",
    "PB": "Paraíba",
    "PE": "Pernambuco",
    "PI": "Piauí",
    "PR": "Paraná",
    "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte",
    "RO": "Rondônia",
    "RR": "Roraima",
    "RS": "Rio Grande do Sul",
    "SC": "Santa Catarina",
    "SE": "Sergipe",
    "SP": "São Paulo",
    "TO": "Tocantins",
}


def cor(valor: float) -> str:
    """Interpola a escala de cor em RGB e devolve `#rrggbb`."""
    pontos = ESCALA
    if valor <= pontos[0][0]:
        r, g, b = pontos[0][1]
    elif valor >= pontos[-1][0]:
        r, g, b = pontos[-1][1]
    else:
        r = g = b = 0
        for (v0, c0), (v1, c1) in pairwise(pontos):
            if v0 <= valor <= v1:
                t = (valor - v0) / (v1 - v0)
                r, g, b = (
                    round(a + (bb - a) * t) for a, bb in zip(c0, c1, strict=True)
                )
                break
    return f"#{r:02x}{g:02x}{b:02x}"


def pt(valor: float, casas: int = 1) -> str:
    return f"{valor:.{casas}f}".replace(".", ",")


def milhar(n: int) -> str:
    return f"{n:,}".replace(",", ".")


class Projecao:
    """Equirretangular com fator cos(lat média), ajustada à caixa do mapa."""

    def __init__(self, lon: tuple[float, float], lat: tuple[float, float]) -> None:
        self.lon0, self.lat0 = lon[0], lat[1]
        self.k = math.cos(math.radians((lat[0] + lat[1]) / 2))
        largura = (lon[1] - lon[0]) * self.k
        altura = lat[1] - lat[0]
        x, y, w, h = MAPA
        self.escala = min(w / largura, h / altura)
        self.dx = x + (w - largura * self.escala) / 2
        self.dy = y + (h - altura * self.escala) / 2

    def xy(self, lon: float, lat: float) -> tuple[float, float]:
        return (
            self.dx + (lon - self.lon0) * self.k * self.escala,
            self.dy + (self.lat0 - lat) * self.escala,
        )


def aneis(geometria: dict) -> list[list[list[float]]]:
    if geometria["type"] == "Polygon":
        return list(geometria["coordinates"])
    if geometria["type"] == "MultiPolygon":
        return [anel for poligono in geometria["coordinates"] for anel in poligono]
    return []


def caminho(geometria: dict, proj: Projecao) -> str:
    partes = []
    for anel in aneis(geometria):
        pontos = [proj.xy(lon, lat) for lon, lat in anel]
        partes.append("M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pontos) + "Z")
    return "".join(partes)


def centroide_maior(geometria: dict, proj: Projecao) -> tuple[float, float]:
    """Centróide (média dos vértices) do anel de maior área projetada."""
    melhor, area_max = None, -1.0
    for anel in aneis(geometria):
        pontos = [proj.xy(lon, lat) for lon, lat in anel]
        area = 0.0
        for (x0, y0), (x1, y1) in pairwise(pontos):
            area += x0 * y1 - x1 * y0
        area = abs(area) / 2
        if area > area_max:
            area_max, melhor = area, pontos
    assert melhor is not None
    return (
        sum(p[0] for p in melhor) / len(melhor),
        sum(p[1] for p in melhor) / len(melhor),
    )


def limites(ufs_geo: dict) -> tuple[tuple[float, float], tuple[float, float]]:
    lons, lats = [], []
    for feicao in ufs_geo["features"]:
        for anel in aneis(feicao["geometry"]):
            for lon, lat in anel:
                lons.append(lon)
                lats.append(lat)
    # Fernando de Noronha e Trindade esticariam a caixa; corta em -34,5 de longitude.
    lon_max = min(max(lons), -34.5)
    return (min(lons), lon_max), (min(lats), max(lats))


def carregar() -> dict:
    dados = json.loads(PRESIDENTE.read_text(encoding="utf-8"))
    colunas = dados["municipios"]["colunas"]
    idx = {c: i for i, c in enumerate(colunas)}
    municipios = {}
    for linha in dados["municipios"]["linhas"]:
        if linha[idx["uf"]] == "ZZ" or not isinstance(
            linha[idx["pct_comparecimento"]], (int, float)
        ):
            continue
        municipios[linha[idx["ibge"]]] = {
            "uf": linha[idx["uf"]],
            "nome": linha[idx["nome"]],
            "eleitores": linha[idx["eleitores"]],
            "abstencao": 100 - linha[idx["pct_comparecimento"]],
        }
    ufs = [
        {
            "uf": u["uf"],
            "nome": NOME_UF.get(u["uf"], u["nome"]),
            "regiao": u["regiao"],
            "eleitores": u["eleitores"],
            "abstencao": 100 - u["pct_comparecimento"],
        }
        for u in dados["ufs"]
        if u["uf"] != "ZZ"
    ]
    exterior = next(u for u in dados["ufs"] if u["uf"] == "ZZ")
    regioes = {
        nome: 100 - r["r2026"]["pct_comparecimento"]
        for nome, r in dados["regioes"].items()
        if nome in REGIAO_COR
    }
    nacional = dados["nacional"]
    return {
        "municipios": municipios,
        "ufs": sorted(ufs, key=lambda u: -u["abstencao"]),
        "regioes": regioes,
        "exterior": 100 - exterior["pct_comparecimento"],
        "nacional": {
            "abstencao": 100 - nacional["pct_comparecimento"],
            "abstencao_n": nacional["abstencao"],
            "eleitores": nacional["eleitores"],
            "gerado_em": nacional["gerado_em_brt"],
        },
    }


def svg_mapa(dados: dict) -> tuple[str, list[str]]:
    ufs_geo = json.loads((GEO / "br_uf.geojson").read_text(encoding="utf-8"))
    proj = Projecao(*limites(ufs_geo))
    municipios_svg: list[str] = []
    faltam: list[str] = []
    for uf in sorted(NOME_UF):
        geo = json.loads((GEO / "mun" / f"{uf}.geojson").read_text(encoding="utf-8"))
        for feicao in geo["features"]:
            codigo = feicao["properties"]["codarea"]
            m = dados["municipios"].get(codigo)
            if m is None:
                faltam.append(codigo)
                fill = "#1b2a4a"
            else:
                fill = cor(m["abstencao"])
            municipios_svg.append(
                f'<path d="{caminho(feicao["geometry"], proj)}" fill="{fill}"/>'
            )
    contornos = []
    rotulos = []
    por_uf = {u["uf"]: u for u in dados["ufs"]}
    for feicao in ufs_geo["features"]:
        sigla = CODIGO_UF.get(str(feicao["properties"].get("codarea")), "")
        contornos.append(
            f'<path d="{caminho(feicao["geometry"], proj)}" fill="none" '
            'stroke="#f4f0e6" stroke-opacity="0.55" stroke-width="0.9" '
            'stroke-linejoin="round"/>'
        )
        if sigla in por_uf:
            x, y = centroide_maior(feicao["geometry"], proj)
            dx, dy = DESLOCA.get(sigla, (0, 0))
            x, y = x + dx, y + dy
            valor = pt(por_uf[sigla]["abstencao"])
            if sigla in SO_SIGLA:
                rotulos.append(
                    f'<g class="rot" transform="translate({x:.1f} {y:.1f})">'
                    f'<text class="sig" y="4">{sigla}</text></g>'
                )
            else:
                rotulos.append(
                    f'<g class="rot" transform="translate({x:.1f} {y:.1f})">'
                    f'<text class="sig" y="-3">{sigla}</text>'
                    f'<text class="val" y="12">{valor}%</text></g>'
                )
    svg = (
        f'<svg viewBox="0 0 {LADO} {LADO}" width="{LADO}" height="{LADO}" '
        'xmlns="http://www.w3.org/2000/svg">'
        "<defs>"
        '<filter id="brilho" x="-10%" y="-10%" width="120%" height="120%">'
        '<feGaussianBlur stdDeviation="6" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>'
        "</filter>"
        "</defs>"
        '<g class="municipios" stroke="#060b1a" stroke-width="0.25" stroke-opacity="0.6">'
        + "".join(municipios_svg)
        + "</g>"
        '<g class="contornos" filter="url(#brilho)">' + "".join(contornos) + "</g>"
        '<g class="rotulos">' + "".join(rotulos) + "</g>"
        "</svg>"
    )
    return svg, faltam


def ranking_html(dados: dict) -> str:
    maior = max(u["abstencao"] for u in dados["ufs"])
    linhas = []
    for u in dados["ufs"]:
        largura = 100 * u["abstencao"] / maior
        linhas.append(
            '<div class="linha">'
            f'<span class="sigla" style="color:{REGIAO_COR[u["regiao"]]}">{u["uf"]}</span>'
            '<span class="barra"><i style="'
            f'width:{largura:.1f}%;background:{cor(u["abstencao"])}"></i></span>'
            f'<span class="num">{pt(u["abstencao"])}%</span>'
            "</div>"
        )
    return "".join(linhas)


def regioes_html(dados: dict) -> str:
    ordem = sorted(dados["regioes"].items(), key=lambda kv: kv[1])
    return "".join(
        '<div class="reg">'
        f'<span class="ponto" style="background:{REGIAO_COR[nome]}"></span>'
        f'<span class="rnome">{nome}</span>'
        f'<span class="rval" style="color:{cor(valor)}">{pt(valor)}%</span>'
        "</div>"
        for nome, valor in ordem
    )


def legenda_html() -> str:
    paradas = ", ".join(
        f"{cor(v)} {100 * (v - ESCALA[0][0]) / (ESCALA[-1][0] - ESCALA[0][0]):.0f}%"
        for v, _ in ESCALA
    )
    marcas = "".join(
        f'<span style="left:{100 * (v - ESCALA[0][0]) / (ESCALA[-1][0] - ESCALA[0][0]):.0f}%">{v:.0f}</span>'
        for v, _ in ESCALA[1:-1]
    )
    return (
        f'<div class="grad" style="background:linear-gradient(90deg, {paradas})"></div>'
        f'<div class="marcas"><span style="left:0">≤{ESCALA[0][0]:.0f}</span>{marcas}'
        f'<span style="left:100%">≥{ESCALA[-1][0]:.0f}%</span></div>'
    )


def extremos(dados: dict) -> dict:
    m = dados["municipios"]
    grandes = {k: v for k, v in m.items() if v["eleitores"] >= 2000}
    menor = min(grandes.values(), key=lambda v: v["abstencao"])
    maior = max(grandes.values(), key=lambda v: v["abstencao"])
    ufs = dados["ufs"]
    return {
        "mun_menor": menor,
        "mun_maior": maior,
        "uf_menor": ufs[-1],
        "uf_maior": ufs[0],
    }


CSS = """
:root{--fundo:#060b1a;--fundo1:#0c1a3a;--papel:#f4f0e6;--tinta:#eef2ff;--suave:#9aa6c4;--linha:rgba(154,166,196,.22);--teal:#5fd3e6;--ouro:#f0c86b}
*{box-sizing:border-box}
html,body{margin:0;width:__L__px;height:__L__px;background:var(--fundo);color:var(--tinta);font-family:"Space Grotesk",system-ui,sans-serif;overflow:hidden}
.pag{position:relative;width:__L__px;height:__L__px;background:radial-gradient(1200px 900px at 30% 40%,#0e1f45 0%,var(--fundo) 65%)}
.grade{position:absolute;inset:0;background-image:linear-gradient(var(--linha) 1px,transparent 1px),linear-gradient(90deg,var(--linha) 1px,transparent 1px);background-size:60px 60px;opacity:.18;mask-image:radial-gradient(circle at 35% 45%,#000 20%,transparent 75%)}
.marca{position:absolute;left:56px;top:44px;display:flex;align-items:center;gap:10px}
.marca img{height:30px}
.marca b{font-size:17px;letter-spacing:1px}
.marca small{display:block;font-family:"JetBrains Mono",monospace;font-size:9px;letter-spacing:3px;color:var(--teal)}
.kicker{position:absolute;left:56px;top:96px;font-family:"JetBrains Mono",monospace;font-size:12px;letter-spacing:4px;color:var(--ouro)}
h1{position:absolute;left:56px;top:116px;margin:0;font-size:52px;line-height:1.02;font-weight:700;letter-spacing:-1px}
h1 em{font-style:normal;color:var(--ouro)}
.kpi{position:absolute;right:56px;top:44px;text-align:right}
.kpi .n{font-size:112px;font-weight:700;line-height:.9;letter-spacing:-5px;color:#ff8a7a}
.kpi .n small{font-size:48px;letter-spacing:-1px}
.kpi .l{font-size:15px;color:var(--suave);margin-top:6px}
.kpi .l b{color:var(--tinta)}
svg{position:absolute;left:0;top:0}
.rot .sig{font-family:"JetBrains Mono",monospace;font-size:9.5px;font-weight:700;fill:#fff;text-anchor:middle;letter-spacing:1px;paint-order:stroke;stroke:#060b1a;stroke-width:3px;stroke-linejoin:round}
.rot .val{font-family:"JetBrains Mono",monospace;font-size:10.5px;fill:#fff;text-anchor:middle;paint-order:stroke;stroke:#060b1a;stroke-width:3px;stroke-linejoin:round}
.painel{position:absolute;right:56px;top:214px;width:268px}
.painel h2{margin:0 0 10px;font-family:"JetBrains Mono",monospace;font-size:11px;letter-spacing:3px;color:var(--suave);font-weight:500}
.linha{display:grid;grid-template-columns:30px 1fr 50px;align-items:center;gap:8px;height:19px}
.sigla{font-family:"JetBrains Mono",monospace;font-size:11px;font-weight:700;letter-spacing:1px}
.barra{height:9px;background:rgba(154,166,196,.12);border-radius:3px;overflow:hidden}
.barra i{display:block;height:100%;border-radius:3px}
.num{font-family:"JetBrains Mono",monospace;font-size:11px;text-align:right;color:var(--tinta)}
.regioes{position:absolute;right:56px;top:760px;width:268px}
.reg{display:grid;grid-template-columns:12px 1fr auto;align-items:center;gap:10px;height:26px;border-bottom:1px solid var(--linha)}
.ponto{width:10px;height:10px;border-radius:50%}
.rnome{font-size:14px}
.rval{font-family:"JetBrains Mono",monospace;font-size:14px;font-weight:700}
.legenda{position:absolute;left:56px;top:950px;width:560px}
.legenda h2{margin:0 0 8px;font-family:"JetBrains Mono",monospace;font-size:11px;letter-spacing:3px;color:var(--suave);font-weight:500}
.grad{height:14px;border-radius:7px}
.marcas{position:relative;height:16px;margin-top:4px;font-family:"JetBrains Mono",monospace;font-size:10px;color:var(--suave)}
.marcas span{position:absolute;transform:translateX(-50%)}
.marcas span:first-child{transform:none}
.marcas span:last-child{transform:translateX(-100%)}
.cartoes{position:absolute;left:56px;top:858px;display:flex;gap:12px}
.cartao{width:274px;padding:10px 14px;border:1px solid var(--linha);border-radius:10px;background:rgba(12,26,58,.72)}
.cartao .t{font-family:"JetBrains Mono",monospace;font-size:9.5px;letter-spacing:3px;color:var(--suave)}
.cartao .v{font-size:19px;font-weight:700;margin-top:2px;white-space:nowrap}
.cartao .d{font-size:12px;color:var(--suave);margin-top:1px}
.fonte{position:absolute;left:56px;right:56px;bottom:30px;display:flex;justify-content:space-between;font-family:"JetBrains Mono",monospace;font-size:10px;letter-spacing:1px;color:var(--suave)}
.fonte b{color:var(--teal);font-weight:500}
.canto{position:absolute;width:22px;height:22px;border:2px solid var(--teal);opacity:.7}
.canto.a{left:26px;top:26px;border-right:0;border-bottom:0}
.canto.b{right:26px;top:26px;border-left:0;border-bottom:0}
.canto.c{left:26px;bottom:26px;border-right:0;border-top:0}
.canto.d{right:26px;bottom:26px;border-left:0;border-top:0}
"""


def html(dados: dict, svg: str) -> str:
    n = dados["nacional"]
    ex = extremos(dados)
    logo = (ROOT / "docs" / "img" / "arvor_logo.png").resolve()
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<title>Abstenção no 1º turno de 2026, por município</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
<style>{CSS.replace("__L__", str(LADO))}</style></head>
<body><div class="pag">
<div class="grade"></div>
<div class="canto a"></div><div class="canto b"></div><div class="canto c"></div><div class="canto d"></div>
<div class="marca"><img src="file://{logo}" alt=""><b>ARVOR<small>INTELLIGENCE</small></b></div>
<div class="kicker">1º TURNO · 05/10/2026 · BOLETINS DE URNA DO TSE</div>
<h1>Onde o Brasil <em>faltou</em></h1>
<div class="kpi"><div class="n">{pt(n["abstencao"])}<small>%</small></div>
<div class="l"><b>{milhar(n["abstencao_n"])}</b> eleitores não votaram<br>de {milhar(n["eleitores"])} aptos</div></div>
{svg}
<div class="painel"><h2>ABSTENÇÃO POR ESTADO</h2>{ranking_html(dados)}</div>
<div class="regioes"><h2 style="margin:0 0 6px;font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:3px;color:var(--suave);font-weight:500">POR REGIÃO</h2>{regioes_html(dados)}</div>
<div class="cartoes">
<div class="cartao"><div class="t">MENOS FALTAS · ESTADO</div><div class="v" style="color:{cor(ex["uf_menor"]["abstencao"])}">{ex["uf_menor"]["nome"]} · {pt(ex["uf_menor"]["abstencao"])}%</div><div class="d">município: {nome_proprio(ex["mun_menor"]["nome"])} ({ex["mun_menor"]["uf"]}), {pt(ex["mun_menor"]["abstencao"])}%</div></div>
<div class="cartao"><div class="t">MAIS FALTAS · ESTADO</div><div class="v" style="color:{cor(ex["uf_maior"]["abstencao"])}">{ex["uf_maior"]["nome"]} · {pt(ex["uf_maior"]["abstencao"])}%</div><div class="d">município: {nome_proprio(ex["mun_maior"]["nome"])} ({ex["mun_maior"]["uf"]}), {pt(ex["mun_maior"]["abstencao"])}%</div></div>
</div>
<div class="legenda"><h2>ABSTENÇÃO POR MUNICÍPIO, % DOS APTOS</h2>{legenda_html()}</div>
<div class="fonte"><span>Fonte: TSE, boletins de urna por seção, totalização de {n["gerado_em"][:10].split("-")[2]}/{n["gerado_em"][5:7]}/2026 · malhas IBGE · exterior ({pt(dados["exterior"])}%) fora do mapa · municípios com 2.000+ eleitores nos destaques</span><b>brasil.arvor.co</b></div>
</div></body></html>
"""


def renderizar(destino: Path) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        navegador = p.chromium.launch()
        pagina = navegador.new_page(
            viewport={"width": LADO, "height": LADO}, device_scale_factor=2
        )
        pagina.goto(HTML.resolve().as_uri(), wait_until="networkidle")
        pagina.evaluate("document.fonts.ready")
        pagina.wait_for_timeout(600)
        pagina.screenshot(path=str(destino), full_page=False)
        navegador.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    parser.add_argument("--sem-png", action="store_true", help="só grava o HTML")
    args = parser.parse_args(argv)
    dados = carregar()
    svg, faltam = svg_mapa(dados)
    HTML.write_text(html(dados, svg), encoding="utf-8")
    print(
        f"{HTML.relative_to(ROOT)}: {len(dados['municipios'])} municípios, {len(faltam)} sem dado"
    )
    if faltam:
        print(
            "  sem dado no TSE:",
            ", ".join(faltam[:10]),
            "..." if len(faltam) > 10 else "",
        )
    if not args.sem_png:
        PNG.parent.mkdir(parents=True, exist_ok=True)
        renderizar(PNG)
        print(f"{PNG.relative_to(ROOT)}: {PNG.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
