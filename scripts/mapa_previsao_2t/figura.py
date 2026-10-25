"""Infográfico 1:1 do mapa de previsão por estado (HTML autocontido e PNG).

Tudo que aparece na imagem vem do JSON gerado pelo motor; nada é digitado à
mão. O mapa usa a malha mínima do IBGE já arquivada (`voto_util_mapa.paths`) e
a cor interpola em OKLab (`predicao_2026.mapa.mix`) numa escala de raiz
quadrada: estados disputados ficam claros, estados decididos ficam saturados.
"""

from __future__ import annotations

import math
from html import escape as esc

from predicao_2026.mapa import mix
from projecao_secoes_2t.fontes import ROOT
from voto_util_mapa import paths

FONTE_HTML = ROOT / "docs/assets/og/mapa_previsao_2t_2026.html"
SAIDA_PNG = ROOT / "docs/img/og/mapa_previsao_2t_2026.png"

LADO = 1080
MAPA_W, MAPA_H = 610.0, 556.0
DOMINIO = 50.0
NEUTRO, LULA, FLAVIO = "#efe9db", "#d13c2e", "#2b6fd1"
FUNDO, TINTA, APAGADO, ACENTO = "#07111f", "#fffefa", "#8a95a8", "#c6ff3d"
EMPATE_PP = 5.0


def fmt(x: float, casas: int = 1) -> str:
    s = f"{x:,.{casas}f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return s.replace("-", "−")


def sinal(x: float, casas: int = 1) -> str:
    return ("+" if x > 0 else "") + fmt(x, casas)


def cor(diferenca: float) -> str:
    t = math.sqrt(min(1.0, abs(diferenca) / DOMINIO))
    return mix(NEUTRO, FLAVIO if diferenca > 0 else LULA, t)


def _rampa() -> str:
    paradas = []
    for i in range(33):
        v = -DOMINIO + i * 2 * DOMINIO / 32
        paradas.append(f"{cor(v)} {i * 100 / 32:.2f}%")
    return ", ".join(paradas)


def _tick_pos(v: float) -> float:
    """Posição 0–100% de um valor na rampa de raiz quadrada."""
    t = math.copysign(math.sqrt(min(1.0, abs(v) / DOMINIO)), v)
    return 50 + 50 * t


def legenda() -> str:
    ticks = ['<span class="lado" style="left:0">Lula à frente</span>']
    for v in (-40, -20, -10, -5, 0, 5, 10, 20, 40):
        ticks.append(
            f'<span style="left:{_tick_pos(v):.2f}%">{sinal(v, 0) if v else "0"}</span>'
        )
    ticks.append('<span class="lado" style="left:100%">Flávio à frente</span>')
    return (
        '<div class="legenda"><p class="legenda-titulo">Diferença Flávio menos Lula, '
        "em pontos dos votos válidos (Projeção Arvor). Quanto mais claro, mais disputado.</p>"
        f'<div class="rampa" style="background:linear-gradient(90deg,{_rampa()})"></div>'
        f'<div class="ticks">{"".join(ticks)}</div></div>'
    )


def mapa_svg(ufs: list[dict]) -> str:
    geo = paths(MAPA_W, MAPA_H, pad=6.0)
    por_uf = {r["uf"]: r for r in ufs}
    formas, rotulos = [], []
    for uf, g in sorted(geo.items()):
        r = por_uf[uf]
        d = r["projecao"]["diferenca_pp"]
        titulo = f"{r['nome']}: Flávio menos Lula {sinal(d)} pp"
        formas.append(
            f'<path d="{g["d"]}" fill="{cor(d)}"><title>{esc(titulo)}</title></path>'
        )
        texto = f"{uf} {sinal(d, 0)}"
        largura = 9 + 7.2 * len(texto)
        lx, ly = g["label"]
        if g["fora"]:
            ax, ay = g["anchor"]
            rotulos.append(
                f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{lx - 2:.1f}" y2="{ly - 3:.1f}" class="guia"/>'
                f'<rect x="{lx - 3:.1f}" y="{ly - 12:.1f}" width="{largura:.0f}" height="18" rx="4" class="chip"/>'
                f'<text x="{lx - 3 + largura / 2:.1f}" y="{ly - 2.6:.1f}" class="rotulo">{texto}</text>'
            )
        else:
            rotulos.append(
                f'<rect x="{lx - largura / 2:.1f}" y="{ly - 9:.1f}" width="{largura:.0f}" height="18" rx="4" class="chip"/>'
                f'<text x="{lx:.1f}" y="{ly + 0.4:.1f}" class="rotulo">{texto}</text>'
            )
    return (
        f'<svg class="mapa" viewBox="0 0 {MAPA_W:.0f} {MAPA_H:.0f}" xmlns="http://www.w3.org/2000/svg" '
        'role="img" aria-label="Mapa do Brasil por estado colorido pela diferença Flávio menos Lula">'
        f'<g stroke="{FUNDO}" stroke-width="1.2" stroke-linejoin="round">{"".join(formas)}</g>'
        f'<g class="rotulos">{"".join(rotulos)}</g></svg>'
    )


def ranking(ufs: list[dict]) -> str:
    linhas = []
    escala = 100.0 / (2 * DOMINIO)
    ordem = sorted(ufs, key=lambda r: -r["projecao"]["diferenca_pp"])
    for r in ordem:
        p, m, u = (
            r["projecao"]["diferenca_pp"],
            r["media"]["diferenca_pp"],
            r["primeiro_turno"]["diferenca_pp"],
        )
        esq = 50 + min(0.0, p) * escala
        larg = abs(p) * escala
        tick = 50 + max(-DOMINIO, min(DOMINIO, u)) * escala
        pesq = (
            '<i class="pesq" title="pesquisa estadual pós-urna"></i>'
            if r["pesquisa_estadual"]
            else ""
        )
        linhas.append(
            f'<div class="linha"><span class="uf">{r["uf"]}{pesq}</span>'
            f'<span class="barra"><i class="zero"></i>'
            f'<i class="fill" style="left:{esq:.2f}%;width:{larg:.2f}%;background:{cor(p)}"></i>'
            f'<i class="tick" style="left:{tick:.2f}%"></i></span>'
            f'<b style="color:{cor(p * 1.6)}">{sinal(p)}</b><span class="media">{sinal(m)}</span></div>'
        )
    return (
        '<div class="ranking"><div class="cab"><span class="uf">UF</span>'
        '<span class="barra-cab">barra = Projeção · traço branco = 1º turno</span>'
        '<b>Proj.</b><span class="media">Média</span></div>'
        f'{"".join(linhas)}</div>'
    )


def placar(titulo: str, f: float, l_: float, nota: str, destaque: bool = False) -> str:
    cls = ' class="card destaque"' if destaque else ' class="card"'
    return (
        f'<div{cls}><span class="card-titulo">{esc(titulo)}</span>'
        f'<span class="placar"><b class="f">{fmt(f)}</b><span class="x">×</span><b class="l">{fmt(l_)}</b></span>'
        f'<span class="nota">{nota}</span></div>'
    )


def pagina(data: dict) -> str:
    ufs = data["ufs"]
    nac = data["nacional"]
    proj, med, urna = nac["projecao"], nac["media"], nac["primeiro_turno"]
    f_proj = sum(r["projecao"]["diferenca_pp"] > 0 for r in ufs)
    f_med = sum(r["media"]["diferenca_pp"] > 0 for r in ufs)
    n_pesq = sum(1 for r in ufs if r["pesquisa_estadual"])
    disputados = [
        r["uf"] for r in ufs if abs(r["projecao"]["diferenca_pp"]) < EMPATE_PP
    ]
    disputados.sort(
        key=lambda u: abs(
            next(r for r in ufs if r["uf"] == u)["projecao"]["diferenca_pp"]
        )
    )
    referencia = data["referencia"][8:10] + "/" + data["referencia"][5:7]
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Mapa de previsão por estado · 2º turno 2026</title>
<!-- Gerado por scripts/mapa-previsao-2t.py. Não edite à mão. -->
<link href="https://fonts.googleapis.com/css2?family=Archivo+Black&family=IBM+Plex+Mono:wght@400;600&family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:{LADO}px;height:{LADO}px;overflow:hidden;background:{FUNDO};color:{TINTA};font-family:Inter,system-ui,sans-serif}}
.card-root{{position:relative;width:{LADO}px;height:{LADO}px;padding:40px 44px 34px;display:grid;grid-template-rows:auto 1fr auto;gap:14px}}
.card-root::before{{content:"";position:absolute;inset:0;z-index:0;
  background:linear-gradient(rgba(255,255,255,.045) 1px,transparent 1px) 0 0/68px 68px,
             linear-gradient(90deg,rgba(255,255,255,.045) 1px,transparent 1px) 0 0/68px 68px;
  -webkit-mask-image:linear-gradient(150deg,#000,transparent 70%)}}
.card-root>*{{position:relative;z-index:1}}
header{{display:flex;justify-content:space-between;align-items:flex-start;gap:24px}}
.eyebrow{{display:inline-flex;align-items:center;gap:10px;padding:7px 14px;border:1px solid rgba(255,255,255,.26);
  font-family:"IBM Plex Mono",monospace;font-size:13px;letter-spacing:.11em;text-transform:uppercase;color:{ACENTO}}}
.eyebrow i{{width:8px;height:8px;background:{ACENTO};display:block}}
h1{{font-family:"Archivo Black",sans-serif;font-size:50px;line-height:.92;letter-spacing:-.03em;text-transform:uppercase;margin-top:16px}}
h1 em{{font-style:normal;color:{ACENTO}}}
.lede{{font-size:16.5px;line-height:1.38;color:#c3cddd;max-width:640px;margin-top:12px}}
.lede b{{color:{TINTA}}}
.marca{{display:flex;flex-direction:column;align-items:flex-end;gap:8px;text-align:right;padding-top:2px}}
.marca img{{width:54px;height:54px;border-radius:50%;background:#fff;padding:5px}}
.marca span{{font-family:"IBM Plex Mono",monospace;font-size:12.5px;letter-spacing:.08em;color:{APAGADO};text-transform:uppercase}}
.marca b{{display:block;color:{ACENTO}}}
main{{display:grid;grid-template-columns:{MAPA_W:.0f}px 1fr;gap:18px;align-items:start}}
.mapa{{width:{MAPA_W:.0f}px;height:{MAPA_H:.0f}px;display:block}}
.chip{{fill:rgba(7,17,31,.82)}}
.rotulo{{font-family:"IBM Plex Mono",monospace;font-size:11.5px;font-weight:600;fill:{TINTA};text-anchor:middle;dominant-baseline:middle}}
.guia{{stroke:rgba(255,254,250,.75);stroke-width:1}}
.ranking{{font-family:"IBM Plex Mono",monospace;font-size:12.5px;display:flex;flex-direction:column;gap:0}}
.cab{{display:grid;grid-template-columns:36px 1fr 52px 50px;align-items:center;gap:8px;color:{APAGADO};font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;padding:0 0 6px;border-bottom:1px solid rgba(255,255,255,.18);margin-bottom:4px}}
.cab b{{font-weight:600;text-align:right;color:{TINTA}}}
.cab .media{{text-align:right}}
.linha{{display:grid;grid-template-columns:36px 1fr 52px 50px;align-items:center;gap:8px;height:18.6px}}
.linha .uf{{font-weight:600;display:flex;align-items:center;gap:4px}}
.linha b{{text-align:right;font-weight:600;font-size:12.5px}}
.linha .media{{text-align:right;color:{APAGADO};font-size:11.5px}}
.barra{{position:relative;height:12px;display:block}}
.barra .zero{{position:absolute;left:50%;top:-2px;bottom:-2px;width:1px;background:rgba(255,255,255,.35)}}
.barra .fill{{position:absolute;top:1px;height:10px;border-radius:2px}}
.barra .tick{{position:absolute;top:-1px;height:14px;width:2px;margin-left:-1px;background:{TINTA}}}
.pesq{{width:6px;height:6px;border-radius:50%;background:{ACENTO};display:inline-block}}
footer{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;align-items:stretch}}
.card{{border:1px solid rgba(255,255,255,.18);padding:12px 14px 11px;display:flex;flex-direction:column;gap:4px;background:rgba(255,255,255,.025)}}
.card.destaque{{border-color:{ACENTO}}}
.card-titulo{{font-family:"IBM Plex Mono",monospace;font-size:11.5px;letter-spacing:.09em;text-transform:uppercase;color:{APAGADO}}}
.destaque .card-titulo{{color:{ACENTO}}}
.placar{{display:flex;align-items:baseline;gap:10px;font-family:"Archivo Black",sans-serif;font-size:34px;letter-spacing:-.02em;line-height:1}}
.placar .f{{color:#74a2ff}}.placar .l{{color:#ef6a5c}}.placar .x{{font-family:Inter;font-weight:400;font-size:20px;color:{APAGADO}}}
.nota{{font-size:12.5px;line-height:1.3;color:#c3cddd}}
.nota b{{color:{TINTA}}}
.legenda{{grid-column:1/-1;display:grid;grid-template-columns:1fr;gap:6px;margin-top:2px}}
.legenda-titulo{{font-size:12.5px;color:#c3cddd}}
.rampa{{height:10px;border-radius:3px}}
.ticks{{position:relative;height:14px;font-family:"IBM Plex Mono",monospace;font-size:10.5px;color:{APAGADO}}}
.ticks span{{position:absolute;transform:translateX(-50%);white-space:nowrap}}
.ticks .lado{{top:14px;transform:none;color:#c3cddd}}
.ticks .lado:last-child{{transform:translateX(-100%)}}
.ticks{{height:30px}}
.rodape{{grid-column:1/-1;display:flex;justify-content:space-between;gap:20px;padding-top:10px;border-top:1px solid rgba(255,255,255,.2);
  font-family:"IBM Plex Mono",monospace;font-size:11px;line-height:1.35;color:{APAGADO}}}
.rodape b{{color:{ACENTO};white-space:nowrap}}
</style>
</head>
<body>
<div class="card-root">
  <header>
    <div>
      <span class="eyebrow"><i></i>Previsão do 2º turno · pesquisas até {referencia} · eleição 25/10/2026</span>
      <h1>Quem leva <em>cada estado</em></h1>
      <p class="lede">O voto de cada uma das <b>{fmt(data["cobertura"]["secoes"], 0)} seções</b> do 1º turno é transportado para o 2º, as pesquisas estaduais pós-urna atualizam <b>{n_pesq} estados</b> e um único deslocamento recentra o país na <b>Projeção Arvor</b> e na <b>Média Arvor</b>.</p>
    </div>
    <div class="marca"><img src="../../img/arvor_logo.png" alt=""><span>Arvor Intelligence<b>brasil.arvor.co</b></span></div>
  </header>
  <main>
    {mapa_svg(ufs)}
    {ranking(ufs)}
  </main>
  <footer>
    {placar("1º turno, urna (04/10)", urna["flavio_pct"], urna["lula_pct"], f"Flávio × Lula entre os válidos; terceiros {fmt(urna['terceiros_pct'])}%. Transportado seção a seção: <b>{fmt(nac['transportado']['flavio_pct'])} × {fmt(nac['transportado']['lula_pct'])}</b>.")}
    {placar(f"Projeção Arvor · {fmt(proj['diferenca_pp'])} pp", proj["flavio_pct"], proj["lula_pct"], f"Âncora do mapa. Flávio à frente em <b>{f_proj} estados</b>, Lula em <b>{27 - f_proj}</b>. Disputa abaixo de {fmt(EMPATE_PP, 0)} pp: <b>{', '.join(disputados)}</b>.", destaque=True)}
    {placar(f"Média Arvor · {fmt(med['diferenca_pp'])} pp", med["flavio_pct"], med["lula_pct"], f"{data['metodo']['ancoras']['media']['casas']} casas com voto por renda, PNAD + presença. Flávio à frente em <b>{f_med} estados</b>, Lula em <b>{27 - f_med}</b>.")}
    {legenda()}
    <div class="rodape"><span>Expectativa pontual por estado: a cor não identifica liderança. O erro comum de 2 pp das pesquisas não se dilui entre estados; faixa ±2 pp é sensibilidade. Transporte validado em 2018→2022 (erro 1,73 pp por UF); a fusão com pesquisas não foi validada contra urna de 2º turno. Sem probabilidade de vitória. Exterior fora do mapa. ● estado com pesquisa Quaest pós-urna.</span><b>brasil.arvor.co</b></div>
  </footer>
</div>
</body>
</html>
"""


def renderizar() -> None:
    from playwright.sync_api import sync_playwright

    SAIDA_PNG.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        nav = p.chromium.launch()
        pg = nav.new_page(
            viewport={"width": LADO, "height": LADO}, device_scale_factor=2
        )
        pg.goto(FONTE_HTML.as_uri(), wait_until="networkidle")
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(400)
        pg.screenshot(
            path=str(SAIDA_PNG), clip={"x": 0, "y": 0, "width": LADO, "height": LADO}
        )
        nav.close()
