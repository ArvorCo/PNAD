#!/usr/bin/env python3
"""Mapa quadrado (1:1) de quem venceu cada município no 1º turno de 2026, em três cores.

Flávio em verde, Lula em vermelho e terceira via (Cury, Renan ou Caiado, o mais votado entre
eles) em amarelo, quando algum deles for o mais votado do município. Tom mais claro quando a
margem entre o primeiro e o segundo fica abaixo de 10 pontos. Empate exato fica em branco.
Reaproveita projeção, malhas e paleta de `scripts/abstencao-1t-mapa.py`.

Saídas: `docs/assets/vencedor_1t_2026_mapa.html` e `docs/img/vencedor_1t_2026.png` (2160 px).

Uso: python3 scripts/vencedor-1t-mapa.py [--sem-png]
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "abstencao", ROOT / "scripts" / "abstencao-1t-mapa.py"
)
assert _spec and _spec.loader
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

HTML = ROOT / "docs" / "assets" / "vencedor_1t_2026_mapa.html"
PNG = ROOT / "docs" / "img" / "vencedor_1t_2026.png"
MARGEM_APERTADA = 10.0

CANDIDATOS = {
    "flavio": "Flávio",
    "lula": "Lula",
    "cury": "Cury",
    "renan": "Renan",
    "caiado": "Caiado",
}
TERCEIRA = ("cury", "renan", "caiado")
COR = {
    "flavio": ("#2bb98a", "#9fe0c4"),
    "lula": ("#e8473a", "#f5a79d"),
    "terceira": ("#f0c86b", "#f7e2b0"),
    "empate": ("#f4f0e6", "#f4f0e6"),
}
NOME_LADO = {
    "flavio": "Flávio",
    "lula": "Lula",
    "terceira": "Terceira via",
    "empate": "Empate",
}


def carregar() -> dict:
    dados = json.loads(base.PRESIDENTE.read_text(encoding="utf-8"))
    idx = {c: i for i, c in enumerate(dados["municipios"]["colunas"])}
    municipios: dict[str, dict] = {}
    for r in dados["municipios"]["linhas"]:
        if r[idx["uf"]] == "ZZ":
            continue
        votos = {c: r[idx[c]] for c in CANDIDATOS}
        ordem = sorted(votos.items(), key=lambda kv: -kv[1])
        (c1, v1), (_, v2) = ordem[0], ordem[1]
        validos = r[idx["validos"]] or 1
        if v1 == v2:
            lado, vencedor = "empate", None
        else:
            lado = "terceira" if c1 in TERCEIRA else c1
            vencedor = c1
        melhor_terceira = max(TERCEIRA, key=lambda c: votos[c])
        municipios[r[idx["ibge"]]] = {
            "uf": r[idx["uf"]],
            "nome": r[idx["nome"]],
            "eleitores": r[idx["eleitores"]],
            "validos": validos,
            "lado": lado,
            "vencedor": vencedor,
            "margem_pp": 100 * (v1 - v2) / validos,
            "pct_flavio": 100 * votos["flavio"] / validos,
            "pct_lula": 100 * votos["lula"] / validos,
            "terceira_nome": melhor_terceira,
            "terceira_pct": 100 * votos[melhor_terceira] / validos,
        }
    ufs = {u["uf"]: u for u in dados["ufs"] if u["uf"] != "ZZ"}
    return {
        "municipios": municipios,
        "ufs": ufs,
        "nacional": dados["nacional"],
        "regioes": dados["regioes"],
    }


def fill(m: dict) -> str:
    escuro, claro = COR[m["lado"]]
    return (
        claro
        if (m["lado"] != "empate" and m["margem_pp"] < MARGEM_APERTADA)
        else escuro
    )


def resumo(dados: dict) -> dict:
    m = dados["municipios"].values()
    por_lado = {lado: [x for x in m if x["lado"] == lado] for lado in COR}
    contagem = {lado: len(v) for lado, v in por_lado.items()}
    eleitores = {lado: sum(x["eleitores"] for x in v) for lado, v in por_lado.items()}
    apertados = {
        lado: sum(1 for x in v if x["margem_pp"] < MARGEM_APERTADA)
        for lado, v in por_lado.items()
    }
    por_uf: dict[str, dict] = {}
    for x in m:
        d = por_uf.setdefault(
            x["uf"], {"flavio": 0, "lula": 0, "terceira": 0, "empate": 0}
        )
        d[x["lado"]] += 1
    melhor_terceira = sorted(m, key=lambda x: -x["terceira_pct"])[:3]
    empates = [x for x in m if x["lado"] == "empate"]
    return {
        "contagem": contagem,
        "eleitores": eleitores,
        "apertados": apertados,
        "por_uf": por_uf,
        "melhor_terceira": melhor_terceira,
        "empates": empates,
    }


def svg_mapa(dados: dict) -> str:
    ufs_geo = json.loads((base.GEO / "br_uf.geojson").read_text(encoding="utf-8"))
    proj = base.Projecao(*base.limites(ufs_geo))
    municipios_svg = []
    for uf in sorted(base.NOME_UF):
        geo = json.loads(
            (base.GEO / "mun" / f"{uf}.geojson").read_text(encoding="utf-8")
        )
        for feicao in geo["features"]:
            m = dados["municipios"].get(feicao["properties"]["codarea"])
            cor = fill(m) if m else "#1b2a4a"
            municipios_svg.append(
                f'<path d="{base.caminho(feicao["geometry"], proj)}" fill="{cor}"/>'
            )
    contornos, rotulos = [], []
    for feicao in ufs_geo["features"]:
        sigla = base.CODIGO_UF.get(str(feicao["properties"].get("codarea")), "")
        contornos.append(
            f'<path d="{base.caminho(feicao["geometry"], proj)}" fill="none" stroke="#060b1a" '
            'stroke-opacity="0.9" stroke-width="1.1" stroke-linejoin="round"/>'
        )
        if sigla:
            x, y = base.centroide_maior(feicao["geometry"], proj)
            dx, dy = base.DESLOCA.get(sigla, (0, 0))
            rotulos.append(
                f'<text class="sig" x="{x + dx:.1f}" y="{y + dy + 4:.1f}">{sigla}</text>'
            )
    lado = base.LADO
    return (
        f'<svg viewBox="0 0 {lado} {lado}" width="{lado}" height="{lado}" xmlns="http://www.w3.org/2000/svg">'
        '<g class="municipios" stroke="#060b1a" stroke-width="0.2" stroke-opacity="0.45">'
        + "".join(municipios_svg)
        + '</g><g class="contornos">'
        + "".join(contornos)
        + '</g><g class="rotulos">'
        + "".join(rotulos)
        + "</g></svg>"
    )


def barras_uf_html(dados: dict, res: dict) -> str:
    linhas = []
    ordem = sorted(
        res["por_uf"].items(),
        key=lambda kv: -kv[1]["flavio"] / max(1, sum(kv[1].values())),
    )
    for uf, d in ordem:
        total = max(1, sum(d.values()))
        f, lu, t = (
            100 * d["flavio"] / total,
            100 * d["lula"] / total,
            100 * d["terceira"] / total,
        )
        lider = dados["ufs"][uf]["lider"]
        cor_lider = COR["flavio"][0] if lider == "flavio" else COR["lula"][0]
        linhas.append(
            '<div class="linha">'
            f'<span class="sigla" style="color:{cor_lider}">{uf}</span>'
            f'<span class="barra"><i style="width:{f:.1f}%;background:{COR["flavio"][0]}"></i>'
            f'<i style="width:{t:.1f}%;background:{COR["terceira"][0]}"></i>'
            f'<i style="width:{lu:.1f}%;background:{COR["lula"][0]}"></i></span>'
            f'<span class="num">{d["flavio"]}<em>×</em>{d["lula"]}</span>'
            "</div>"
        )
    return "".join(linhas)


CSS_EXTRA = """
.sig{font-family:"JetBrains Mono",monospace;font-size:11px;font-weight:700;fill:#f4f0e6;text-anchor:middle;letter-spacing:1px;paint-order:stroke;stroke:#060b1a;stroke-width:3.5px;stroke-linejoin:round}
.placar{position:absolute;right:56px;top:34px;width:268px;display:flex;flex-direction:column;gap:4px;align-items:flex-end}
.placar .lado{text-align:right}
.placar .n{font-size:58px;font-weight:700;line-height:.95;letter-spacing:-2px}
.placar .l{font-family:"JetBrains Mono",monospace;font-size:10px;letter-spacing:3px;margin-top:2px;color:var(--suave)}
.placar .e{font-size:13px;color:var(--suave);margin-top:1px}
.placar .e b{color:var(--tinta)}
.placar .x{display:none}
.painel{top:236px}
.regioes{top:792px}
.cartoes{top:828px}
.leg{top:994px}
.painel .linha{grid-template-columns:30px 1fr 64px}
.painel .barra{display:flex;background:transparent}
.painel .barra i{display:block;height:100%;border-radius:0}
.painel .barra i:first-child{border-radius:3px 0 0 3px}
.painel .barra i:last-child{border-radius:0 3px 3px 0}
.painel .num em{font-style:normal;color:var(--suave);padding:0 3px}
.leg{position:absolute;left:56px;display:flex;gap:26px;align-items:center}
.leg .it{display:flex;align-items:center;gap:8px;font-size:14px}
.leg .sw{width:26px;height:16px;border-radius:4px;display:inline-block}
.leg .sw.meio{background:linear-gradient(90deg,var(--a) 50%,var(--b) 50%)}
.leg small{font-family:"JetBrains Mono",monospace;font-size:10px;color:var(--suave);letter-spacing:1px}
.cartao{width:274px}
.cartao .v{font-size:19px;white-space:nowrap}
.cartao ul{margin:4px 0 0;padding:0;list-style:none;font-size:12px;color:var(--suave);line-height:1.35}
.cartao ul b{color:var(--tinta);font-weight:500}
"""


def regioes_html(dados: dict, res: dict) -> str:
    ufs_regiao: dict[str, list[str]] = {}
    for uf, u in dados["ufs"].items():
        ufs_regiao.setdefault(u["regiao"], []).append(uf)
    itens = []
    for nome in ("Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"):
        f = sum(res["por_uf"][uf]["flavio"] for uf in ufs_regiao[nome])
        lu = sum(res["por_uf"][uf]["lula"] for uf in ufs_regiao[nome])
        cor = COR["flavio"][0] if f > lu else COR["lula"][0]
        itens.append(
            '<div class="reg">'
            f'<span class="ponto" style="background:{cor}"></span>'
            f'<span class="rnome">{nome}</span>'
            f'<span class="rval"><span style="color:{COR["flavio"][0]}">{f}</span>'
            f'<span style="color:var(--suave)"> × </span><span style="color:{COR["lula"][0]}">{lu}</span></span>'
            "</div>"
        )
    return "".join(itens)


def html(dados: dict, svg: str) -> str:
    res = resumo(dados)
    n = dados["nacional"]
    c, e = res["contagem"], res["eleitores"]
    logo = (ROOT / "docs" / "img" / "arvor_logo.png").resolve()
    css = base.CSS.replace("__L__", str(base.LADO)) + CSS_EXTRA
    terceira = "".join(
        f'<li><b>{base.nome_proprio(m["nome"])} ({m["uf"]})</b>: {CANDIDATOS[m["terceira_nome"]]} {base.pt(m["terceira_pct"])}%</li>'
        for m in res["melhor_terceira"]
    )
    empates = (
        "; ".join(f'{base.nome_proprio(m["nome"])} ({m["uf"]})' for m in res["empates"])
        or "nenhum"
    )
    apert = res["apertados"]
    gerado = n["gerado_em_brt"][:10]
    data_br = f"{gerado[8:10]}/{gerado[5:7]}/{gerado[:4]}"
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<title>Quem venceu cada município no 1º turno de 2026</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
<style>{css}</style></head>
<body><div class="pag">
<div class="grade"></div>
<div class="canto a"></div><div class="canto b"></div><div class="canto c"></div><div class="canto d"></div>
<div class="marca"><img src="file://{logo}" alt=""><b>ARVOR<small>INTELLIGENCE</small></b></div>
<div class="kicker">1º TURNO · 05/10/2026 · VOTOS VÁLIDOS POR MUNICÍPIO</div>
<h1>Quem venceu <em>cada município</em></h1>
<div class="placar">
<div class="lado"><div class="n" style="color:{COR["flavio"][0]}">{base.milhar(c["flavio"])}</div><div class="l">MUNICÍPIOS · FLÁVIO</div><div class="e"><b>{base.pt(e["flavio"] / 1e6)} mi</b> de eleitores</div></div>
<div class="x">×</div>
<div class="lado"><div class="n" style="color:{COR["lula"][0]}">{base.milhar(c["lula"])}</div><div class="l">MUNICÍPIOS · LULA</div><div class="e"><b>{base.pt(e["lula"] / 1e6)} mi</b> de eleitores</div></div>
</div>
{svg}
<div class="painel"><h2>MUNICÍPIOS POR ESTADO · FLÁVIO × LULA</h2>{barras_uf_html(dados, res)}</div>
<div class="regioes"><h2 style="margin:0 0 6px;font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:3px;color:var(--suave);font-weight:500">POR REGIÃO · MUNICÍPIOS</h2>{regioes_html(dados, res)}</div>
<div class="cartoes">
<div class="cartao"><div class="t">TERCEIRA VIA · MUNICÍPIOS VENCIDOS</div><div class="v" style="color:{COR["terceira"][0]}">{c["terceira"]} de {base.milhar(len(dados["municipios"]))}</div><ul>{terceira}</ul></div>
<div class="cartao"><div class="t">MARGEM ABAIXO DE {MARGEM_APERTADA:.0f} PONTOS</div><div class="v"><span style="color:{COR["flavio"][0]}">{base.milhar(apert["flavio"])}</span> <span style="color:var(--suave)">de Flávio ·</span> <span style="color:{COR["lula"][0]}">{base.milhar(apert["lula"])}</span> <span style="color:var(--suave)">de Lula</span></div><ul><li>empate exato: <b>{empates}</b></li></ul></div>
</div>
<div class="leg">
<span class="it"><span class="sw meio" style="--a:{COR["flavio"][0]};--b:{COR["flavio"][1]}"></span>Flávio <small>FOLGADO · APERTADO</small></span>
<span class="it"><span class="sw meio" style="--a:{COR["lula"][0]};--b:{COR["lula"][1]}"></span>Lula <small>FOLGADO · APERTADO</small></span>
<span class="it"><span class="sw" style="background:{COR["terceira"][0]}"></span>Terceira via</span>
<span class="it"><span class="sw" style="background:{COR["empate"][0]}"></span>Empate</span>
</div>
<div class="fonte"><span>Fonte: TSE, boletins de urna por seção, totalização de {data_br} · votos válidos; terceira via = Cury, Renan ou Caiado, o mais votado entre eles · malhas IBGE · exterior fora do mapa</span><b>brasil.arvor.co</b></div>
</div></body></html>
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    parser.add_argument("--sem-png", action="store_true", help="só grava o HTML")
    args = parser.parse_args(argv)
    dados = carregar()
    HTML.write_text(html(dados, svg_mapa(dados)), encoding="utf-8")
    res = resumo(dados)
    print(
        f"{HTML.relative_to(ROOT)}: {res['contagem']} municípios; eleitores {res['eleitores']}"
    )
    if not args.sem_png:
        base.HTML = HTML
        base.renderizar(PNG)
        print(f"{PNG.relative_to(ROOT)}: {PNG.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
