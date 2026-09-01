#!/usr/bin/env python3
"""Gera a imagem única do atlas de Minas, para post no X.

Monta um HTML autocontido com o mapa real dos 853 municípios pintado por
corredor, os retratos com licença livre e os números da camada 2, e o
converte em PNG.

Reprodução:
    python3 scripts/mg-082026-camada2.py && python3 scripts/mg-082026-infografico.py
"""

from __future__ import annotations

import base64
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAMADA2 = ROOT / "docs/assets/mg_082026_camada2.json"
ATLAS = ROOT / "docs/assets/mg_082026_data.json"
GEO = ROOT / "docs/assets/mg_082026_municipios.geojson"
RETRATOS = Path(
    "/private/tmp/claude-501/-Users-leonardodias-arvor-PNAD/9d0228fe-30da-4049-b82b-a742ff2052db/scratchpad"
)
FONTE_HTML = ROOT / "docs/assets/og/mg_082026_infografico.html"
SAIDA_PNG = ROOT / "docs/img/og/mg_082026_infografico.png"

CORES = {
    "minerio": "#f0b429",
    "metropolitano": "#45c9c2",
    "oeste": "#7fd3a0",
    "aco": "#e08b5c",
    "mata": "#b490dd",
    "producao": "#6ea8e8",
    "vales": "#7d8a80",
}
FORA = "#242e26"

# Mapa principal: quem supera Bolsonaro em cada municipio.
CARREGADOR = {
    "cleit": ("#7fd3a0", "Cleitinho vai mais longe"),
    "engler": ("#b490dd", "Engler vai mais longe"),
    "niko": ("#45c9c2", "Nikolas vai mais longe"),
    "ninguem": ("#33403a", "nenhum supera Bolsonaro"),
}

CIDADES = [
    ("Belo Horizonte", -43.9386, -19.9208, "Belo Horizonte", "end", -14, 4),
    ("Uberlândia", -48.2772, -18.9186, "Uberlândia", "start", 13, 4),
    ("Juiz de Fora", -43.3496, -21.7642, "Juiz de Fora", "start", 13, 4),
    ("Montes Claros", -43.8647, -16.7350, "Montes Claros", "start", 13, 4),
    ("Divinópolis", -44.8839, -20.1394, "Divinópolis", "end", -14, 20),
    ("Ipatinga", -42.5369, -19.4703, "Ipatinga", "start", 13, 5),
    ("Itabira", -43.2269, -19.6194, "Itabira", "end", -13, -4),
    ("Varginha", -45.4300, -21.5514, "Varginha", "end", -14, 4),
    ("Teófilo Otoni", -41.5064, -17.8575, "Teófilo Otoni", "start", 13, 4),
]


def b64(caminho: Path) -> str:
    return base64.b64encode(caminho.read_bytes()).decode()


def quem_carrega() -> dict[str, str]:
    """Para cada municipio, qual dos tres vai mais longe que Bolsonaro."""
    import csv

    caminho = (
        ROOT
        / "data/pesquisas/estaduais/mg/2026-08/derivados/carregadores-municipais.csv"
    )
    saida = {}
    for linha in csv.DictReader(caminho.open(encoding="utf-8")):
        melhor = max(
            (float(linha["iC"]), "cleit"),
            (float(linha["iN"]), "niko"),
            (float(linha["iE"]), "engler"),
        )
        saida[linha["ibge"]] = "ninguem" if melhor[0] <= 100 else melhor[1]
    return saida


def constroi_mapa(camada: dict, largura: int, altura: int) -> tuple[str, str]:
    geo = json.loads(GEO.read_text(encoding="utf-8"))
    por_municipio = quem_carrega()

    lons, lats = [], []
    for feature in geo["features"]:
        for anel in feature["geometry"]["coordinates"]:
            for x, y in anel:
                lons.append(x)
                lats.append(y)
    lon0, lon1 = min(lons), max(lons)
    lat0, lat1 = min(lats), max(lats)
    meio = math.radians((lat0 + lat1) / 2)
    span_x = (lon1 - lon0) * math.cos(meio)
    span_y = lat1 - lat0
    escala = min(largura / span_x, altura / span_y)
    dx = (largura - span_x * escala) / 2
    dy = (altura - span_y * escala) / 2

    def projeta(x: float, y: float) -> tuple[float, float]:
        return (dx + (x - lon0) * math.cos(meio) * escala, dy + (lat1 - y) * escala)

    partes = []
    for feature in geo["features"]:
        chave = por_municipio.get(feature["properties"]["codigo_ibge"], "ninguem")
        cor = CARREGADOR[chave][0]
        trechos = []
        for anel in feature["geometry"]["coordinates"]:
            pontos = " ".join(
                f"{px:.1f} {py:.1f}" for px, py in (projeta(x, y) for x, y in anel)
            )
            trechos.append("M " + pontos + " Z")
        partes.append(
            f'<path d="{" ".join(trechos)}" fill="{cor}" stroke="#0e1611" stroke-width=".45"/>'
        )

    marcas = []
    for _, lon, lat, rotulo, ancora, dxr, dyr in CIDADES:
        px, py = projeta(lon, lat)
        marcas.append(
            f'<circle cx="{px:.1f}" cy="{py:.1f}" r="6" fill="#fffdf6" stroke="#0e1611" stroke-width="2.4"/>'
        )
        marcas.append(
            f'<text x="{px + dxr:.1f}" y="{py + dyr:.1f}" text-anchor="{ancora}" '
            f'font-family="IBM Plex Sans Condensed, Arial" font-size="20" font-weight="700" '
            f'fill="#fffdf6" stroke="#0e1611" stroke-width="5" paint-order="stroke">{rotulo}</text>'
        )
    return "".join(partes), "".join(marcas)


def votos_nominais() -> dict:
    import csv

    caminho = (
        ROOT
        / "data/pesquisas/estaduais/mg/2026-08/derivados/candidatos_2022_perfil_territorial.csv"
    )
    alvo = {
        "CLEITINHO": "cleitinho",
        "NIKOLAS FERREIRA": "nikolas",
        "BRUNO ENGLER": "engler",
    }
    saida = {}
    for linha in csv.DictReader(caminho.open(encoding="utf-8")):
        chave = alvo.get(linha["nome_urna"].strip().upper())
        if chave and chave not in saida:
            saida[chave] = int(linha["votos_mg"])
    return saida


def milhar(valor: float) -> str:
    return f"{valor:,.0f}".replace(",", ".")


def pct(valor: float, casas: int = 1) -> str:
    return f"{valor:.{casas}f}".replace(".", ",") + "%"


def main() -> None:
    camada = json.loads(CAMADA2.read_text(encoding="utf-8"))
    estado = camada["estado"]
    votos = votos_nominais()
    por_slug = {c["slug"]: c for c in camada["corredores"]}
    minerio = por_slug["minerio"]["resumo"]
    trio = camada["trio"]

    mapa_w, mapa_h = 840, 700
    caminhos, marcas = constroi_mapa(camada, mapa_w, mapa_h)

    import collections

    contagem = collections.Counter()
    eleitores_por = collections.Counter()
    import csv as _csv

    for linha in _csv.DictReader(
        (
            ROOT
            / "data/pesquisas/estaduais/mg/2026-08/derivados/carregadores-municipais.csv"
        ).open(encoding="utf-8")
    ):
        melhor = max(
            (float(linha["iC"]), "cleit"),
            (float(linha["iN"]), "niko"),
            (float(linha["iE"]), "engler"),
        )
        chave = "ninguem" if melhor[0] <= 100 else melhor[1]
        contagem[chave] += 1
        eleitores_por[chave] += int(linha["el"])
    total_el = sum(eleitores_por.values())
    legenda_mapa = "".join(
        f'<span style="border-top-color:{CARREGADOR[k][0]}">{CARREGADOR[k][1]}'
        f"<b>{contagem[k]} cidades, {100 * eleitores_por[k] / total_el:.0f}% do eleitorado</b></span>"
        for k in ("cleit", "engler", "niko", "ninguem")
    )

    retratos = {
        n: b64(RETRATOS / f"retrato_{n}.jpg")
        for n in ("flavio", "nikolas", "cleitinho", "engler")
    }
    logo = b64(ROOT / "docs/img/arvor_logo.png")

    fichas = [
        (
            "flavio",
            "Flávio Bolsonaro",
            "o candidato",
            f"{pct(42, 0)}",
            "no 2º turno em Minas, contra 46% de Lula",
            "#f0b429",
        ),
        (
            "cleitinho",
            "Cleitinho",
            "senador, candidato ao governo",
            milhar(votos["cleitinho"]),
            "votos em 2022, e ainda assim atrás de Bolsonaro no estado",
            "#7fd3a0",
        ),
        (
            "nikolas",
            "Nikolas Ferreira",
            "deputado federal",
            milhar(votos["nikolas"]),
            "votos, o maior do país, com 43,5% deles na Grande BH",
            "#45c9c2",
        ),
        (
            "engler",
            "Bruno Engler",
            "deputado estadual",
            milhar(votos["engler"]),
            "votos, quase todos dentro da região metropolitana",
            "#b490dd",
        ),
    ]
    cards = "".join(f"""
      <article class="ficha">
        <img src="data:image/jpeg;base64,{retratos[slug]}" alt="">
        <div class="ficha-txt">
          <h3>{nome}</h3><p class="cargo">{cargo}</p>
          <b style="color:{cor}">{numero}</b><p class="nota">{nota}</p>
        </div>
      </article>""" for slug, nome, cargo, numero, nota, cor in fichas)

    ordem = ["minerio", "metropolitano", "oeste", "aco", "mata", "producao", "vales"]
    linhas = "".join(
        f"""
      <tr><th>{por_slug[s]["nome"].replace("Corredor ", "")}</th>
      <td>{milhar(por_slug[s]["resumo"]["eleitores"])}</td>
      <td class="{"up" if por_slug[s]["resumo"]["iC"] > 100 else "dn"}">{por_slug[s]["resumo"]["iC"]}</td>
      <td class="{"up" if por_slug[s]["resumo"]["iN"] > 100 else "dn"}">{por_slug[s]["resumo"]["iN"]}</td>
      <td class="{"up" if por_slug[s]["resumo"]["iE"] > 100 else "dn"}">{por_slug[s]["resumo"]["iE"]}</td></tr>"""
        for s in ordem
    )

    falas = [
        (
            "minerio",
            "No cinturão do minério",
            "O minério sai daqui e a conta fica aqui.",
            "A Vale é cobrada em R$ 17,7 bilhões de royalties. R$ 3,2 bilhões iriam para municípios mineiros, e Itabira sozinha responde por R$ 822,6 milhões.",
        ),
        (
            "metropolitano",
            "Na periferia de BH",
            "Aqui não falta discurso. Falta ônibus, posto e polícia.",
            "Um quarto do eleitorado do estado. É onde Nikolas e Engler valem mais que qualquer outro nome da direita mineira.",
        ),
        (
            "producao",
            "No Sul e no Triângulo",
            "Minas produz o que o Brasil exporta.",
            "O café perdeu 34% do valor exportado aos Estados Unidos no semestre. Aqui nenhum aliado ajuda: o candidato se sustenta sozinho.",
        ),
        (
            "vales",
            "Nos vales do Norte",
            "Aqui não se pede o voto. Pede-se para ser ouvido.",
            "Rádio e parlamentar local. O objetivo é comprimir diferença, não vencer região, porque cada ponto custa muito mais.",
        ),
    ]
    blocos = "".join(f"""
      <article class="fala" style="border-top-color:{CORES[s]}">
        <p class="onde">{onde}</p><h4>{frase}</h4><p>{por}</p>
      </article>""" for s, onde, frase, por in falas)

    html = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,900&family=IBM+Plex+Sans+Condensed:wght@400;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
:root{{--bg:#0e1611;--pan:#16211a;--pan2:#1c2921;--line:#2c3b31;--ink:#fffdf6;--ink2:#c7d2c8;--dim:#94a396;--gold:#f0b429}}
body{{width:1500px;background:var(--bg);color:var(--ink);
 font-family:"IBM Plex Sans Condensed",Arial,sans-serif;font-size:17px;line-height:1.5}}
.pad{{padding:0 56px}}
header{{padding:52px 56px 34px;background:
 radial-gradient(900px 420px at 82% 8%,rgb(240 180 41/.16),transparent 62%),
 linear-gradient(150deg,#0e1611 0%,#132018 55%,#16281c 100%);border-bottom:1px solid var(--line)}}
.marca{{display:flex;align-items:center;gap:13px;font-family:"IBM Plex Mono",monospace;
 font-size:.82rem;letter-spacing:.2em;text-transform:uppercase;color:var(--gold)}}
.marca img{{width:34px;height:34px;object-fit:contain;filter:brightness(0) invert(1)}}
h1{{font-family:Fraunces,Georgia,serif;font-weight:900;font-size:107px;line-height:.9;
 letter-spacing:-.035em;margin:26px 0 0}}
h1 em{{font-style:normal;color:var(--gold)}}
.deck{{max-width:1080px;margin:24px 0 0;font-size:25px;line-height:1.45;color:var(--ink2)}}
.aposta{{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;margin:34px 0 0;
 background:var(--line);border:1px solid var(--line)}}
.aposta div{{background:#121c15;padding:20px 22px}}
.aposta b{{display:block;font-family:Fraunces,serif;font-weight:900;font-size:41px;
 line-height:1;color:var(--gold)}}
.aposta span{{display:block;margin-top:9px;font-size:16px;color:var(--dim);line-height:1.35}}
.faixa{{padding:40px 56px 10px}}
.rotulo{{font-family:"IBM Plex Mono",monospace;font-size:.82rem;letter-spacing:.2em;
 text-transform:uppercase;color:var(--gold);margin-bottom:16px}}
h2{{font-family:Fraunces,serif;font-weight:900;font-size:50px;line-height:1;
 letter-spacing:-.025em;margin-bottom:10px}}
.sub{{font-size:20px;color:var(--ink2);max-width:1180px;margin-bottom:24px}}
.fichas{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}}
.ficha{{background:var(--pan);border:1px solid var(--line);overflow:hidden}}
.ficha img{{width:100%;aspect-ratio:1;object-fit:cover;display:block;filter:saturate(.92)}}
.ficha-txt{{padding:17px 18px 20px}}
.ficha h3{{font-family:Fraunces,serif;font-weight:900;font-size:26px;line-height:1.05}}
.cargo{{font-family:"IBM Plex Mono",monospace;font-size:.72rem;letter-spacing:.13em;
 text-transform:uppercase;color:var(--dim);margin:6px 0 13px}}
.ficha b{{display:block;font-family:Fraunces,serif;font-weight:900;font-size:37px;line-height:1}}
.nota{{margin-top:9px;font-size:15.5px;color:var(--ink2);line-height:1.4}}
.duplo{{display:grid;grid-template-columns:860px 1fr;gap:32px;align-items:start}}
.mapa{{background:var(--pan);border:1px solid var(--line);padding:10px}}
.legenda{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:14px;padding:0 8px 8px}}
.legenda span{{display:block;font-size:16px;color:var(--ink);font-weight:600;
 border-top:4px solid transparent;padding-top:9px}}
.legenda i{{width:100%;height:0;display:block}}
.legenda b{{display:block;margin-top:4px;font-size:13.5px;color:var(--dim);font-weight:400;
 font-family:"IBM Plex Mono",monospace;letter-spacing:.02em;line-height:1.35}}
table{{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}}
th,td{{padding:11px 9px;border-bottom:1px solid var(--line);text-align:right;font-size:19px}}
thead th{{font-family:"IBM Plex Mono",monospace;font-size:.7rem;letter-spacing:.1em;
 text-transform:uppercase;color:var(--dim);border-bottom:1px solid #3c5044}}
tbody th{{text-align:left;font-weight:600;font-size:19px;display:flex;align-items:center;gap:9px}}
tbody th i{{width:13px;height:13px;border-radius:3px;flex:0 0 auto}}
td.up{{color:#7fd3a0;font-weight:700}} td.dn{{color:var(--dim)}}
.destaque{{margin-top:20px;padding:20px 22px;background:#1a2317;border:1px solid var(--gold)}}
.destaque b{{display:block;font-family:Fraunces,serif;font-weight:900;font-size:40px;
 line-height:1;color:var(--gold)}}
.destaque p{{margin-top:10px;font-size:16.5px;color:var(--ink2);line-height:1.45}}
.explica{{margin-top:15px;font-size:16px;color:var(--ink2);line-height:1.45;
 border-left:3px solid var(--gold);padding-left:14px}}
.alvo{{margin:38px 0 0;display:grid;grid-template-columns:1fr 1fr 1fr;gap:1px;
 background:var(--line);border:1px solid var(--gold)}}
.alvo div{{background:#1a2317;padding:24px 26px}}
.alvo b{{display:block;font-family:Fraunces,serif;font-weight:900;font-size:44px;
 line-height:1;color:var(--gold)}}
.alvo p{{margin-top:10px;font-size:17px;color:var(--ink2);line-height:1.42}}
.falas{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-top:24px}}
.fala{{background:var(--pan2);border:1px solid var(--line);border-top:4px solid;padding:20px 20px 22px}}
.onde{{font-family:"IBM Plex Mono",monospace;font-size:.7rem;letter-spacing:.13em;
 text-transform:uppercase;color:var(--dim)}}
.fala h4{{font-family:Fraunces,serif;font-weight:900;font-size:25px;line-height:1.14;margin:9px 0 11px}}
.fala p{{font-size:15.5px;color:var(--ink2);line-height:1.42}}
footer{{margin-top:44px;padding:26px 56px 40px;border-top:1px solid var(--line);
 display:flex;justify-content:space-between;align-items:flex-end;gap:30px}}
footer p{{font-size:14.5px;color:var(--dim);max-width:960px;line-height:1.5}}
footer b{{color:var(--gold);font-family:"IBM Plex Mono",monospace;font-size:19px;letter-spacing:.04em}}
</style></head><body>

<header>
  <div class="marca"><img src="data:image/png;base64,{logo}" alt="">Arvor Intelligence · atlas de Minas Gerais · setembro de 2026</div>
  <h1>Quem vence Minas<br><em>vence o Brasil.</em></h1>
  <p class="deck">Em 2022 o estado virou por 0,40 ponto. Auditamos os 853 municípios, os votos oficiais de 2018 e 2022 e as pesquisas de agosto, e achamos uma coisa que ninguém tinha medido: os três maiores puxadores de voto da direita mineira são fortes em lugares diferentes, e um deles é forte justo onde Bolsonaro foi fraco.</p>
  <div class="aposta">
    <div><b>{milhar(estado["eleitores"])}</b><span>eleitores em 853 municípios, o segundo maior colégio do país</span></div>
    <div><b>46 × 42</b><span>Lula e Flávio no 2º turno em Minas, Datafolha de 18 a 20 de agosto</span></div>
    <div><b>{estado["viradas_de"]}</b><span>cidades trocaram de lado entre 2018 e 2022, quase todas na mesma direção</span></div>
    <div><b>{milhar(estado["eleitores_disputados_5pp"])}</b><span>eleitores em cidades decididas por menos de 5 pontos</span></div>
  </div>
</header>

<section class="faixa">
  <p class="rotulo">Quem carrega voto em Minas</p>
  <h2>Quatro nomes, quatro mapas diferentes.</h2>
  <p class="sub">Comparar 41% de um senador com 6% de um deputado estadual não diz nada. Nós dividimos o desempenho de cada um pela média dele mesmo no estado, e comparamos com Bolsonaro no primeiro turno de 2022. Cem quer dizer render igual a ele naquela cidade.</p>
  <div class="fichas">{cards}</div>
</section>

<section class="faixa">
  <p class="rotulo">O mapa que ninguém tinha feito</p>
  <h2>Quem vai mais longe que Bolsonaro, cidade por cidade.</h2>
  <div class="duplo">
    <div class="mapa">
      <svg viewBox="0 0 {mapa_w} {mapa_h}" width="{mapa_w}" height="{mapa_h}">{caminhos}{marcas}</svg>
      <div class="legenda">{legenda_mapa}</div>
    </div>
    <div>
      <table>
        <thead><tr><th style="text-align:left">corredor</th><th>eleitores</th><th>Cleit</th><th>Niko</th><th>Engler</th></tr></thead>
        <tbody>{linhas}</tbody>
      </table>
      <div class="destaque">
        <b>{trio["municipios"]} cidades</b>
        <p>são as que Cleitinho, Nikolas e Engler superam ao mesmo tempo. Somam {milhar(trio["eleitores"])} eleitores, e metade delas fica no cinturão do minério. É onde a chapa inteira rende mais que o topo dela, ou seja, onde o problema não é o campo, é o nome.</p>
      </div>
      <p class="explica"><b>Como ler a tabela.</b> Verde é render mais que Bolsonaro rendeu ali, cinza é render menos. Cleitinho brilha no Oeste e nos vales, Nikolas e Engler brilham na Grande BH, e no Sul com o Triângulo, que sozinhos são 13,85% do eleitorado mineiro, nenhum dos três ajuda: ali o candidato se sustenta sozinho.</p>
    </div>
  </div>
  <div class="alvo">
    <div><b>{pct(minerio["bol1"])}</b><p>foi o que Bolsonaro fez no cinturão do minério, contra {pct(estado["bol1"])} no estado. É onde ele foi mais fraco entre as regiões ricas.</p></div>
    <div><b>{minerio["viradas"]} de {minerio["municipios"]}</b><p>cidades do corredor trocaram de lado em 2022, incluindo Itabira, Nova Lima e Congonhas.</p></div>
    <div><b>R$ 3,2 bi</b><p>é o que municípios mineiros receberiam da cobrança de royalties feita à Vale. Itabira sozinha, R$ 822,6 milhões.</p></div>
  </div>
</section>

<section class="faixa">
  <p class="rotulo">O que dizer em cada lugar</p>
  <h2>Minas não é um bloco. São sete conversas.</h2>
  <div class="falas">{blocos}</div>
</section>

<footer>
  <p>Fontes: TSE, votação nominal por município de 2018 e 2022, e perfil do eleitorado de 1º de julho de 2026. IBGE, Censo 2022, PIB municipal 2023 e PNAD contínua anual 2025. Datafolha em Minas Gerais, campo de 18 a 20 de agosto de 2026 com 1.204 entrevistas e margem de 3 pontos, e imprensa mineira citada no dossiê. Retratos via Wikimedia Commons: Agência Senado, Pablo Valadares/Câmara dos Deputados, Thiagogontt e Vivi melo15. Metodologia e base aberta no dossiê completo.</p>
  <b>brasil.arvor.co</b>
</footer>
</body></html>"""

    FONTE_HTML.parent.mkdir(parents=True, exist_ok=True)
    FONTE_HTML.write_text(html, encoding="utf-8")
    if "—" in html:
        raise SystemExit("travessão encontrado no infográfico")

    from playwright.sync_api import sync_playwright

    SAIDA_PNG.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as play:
        navegador = play.chromium.launch()
        pagina = navegador.new_page(
            viewport={"width": 1500, "height": 2200}, device_scale_factor=2
        )
        pagina.goto(FONTE_HTML.as_uri(), wait_until="networkidle")
        pagina.wait_for_timeout(2200)
        pagina.screenshot(path=str(SAIDA_PNG), full_page=True)
        navegador.close()
    tamanho = SAIDA_PNG.stat().st_size / 1_000_000
    print(f"gravado {SAIDA_PNG} ({tamanho:.1f} MB)")
    print(f"fonte em {FONTE_HTML}")


if __name__ == "__main__":
    main()
