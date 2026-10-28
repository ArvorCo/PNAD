"""Território armado: mapa rastreável, voto agregado e sensibilidade às bordas."""

import base64
from html import escape

from .dados import ROOT, ler
from .figuras import num
from .territorio import FONTE, GRUPOS, mercator


def barras(rows):
    h = '<div class="territorio-barras">'
    for r in rows:
        p = r["pct_lula"]
        titulo = f'{r["grupo"]} · {num(r["locais"])} locais · {num(r["validos"])} votos válidos'
        h += f'<div class="territorio-barra"><b>{escape(titulo)}</b>'
        if p is None:
            h += "<p>Sem locais neste recorte.</p></div>"
            continue
        h += f'<div class="territorio-votos" role="img" aria-label="Lula {p:.2f}%; Flávio {100-p:.2f}%"><span style="width:{p:.4f}%">L {num(p,1)}%</span><span style="width:{100-p:.4f}%">F {num(100-p,1)}%</span></div></div>'
    return h + "</div>"


def mapa(d):
    (north, west), (south, east) = d["janela"]
    width = 960
    height = (
        width
        * (mercator(north) - mercator(south))
        / ((east - west) * 3.141592653589793 / 180)
    )

    def xy(lat, lon):
        return (
            (lon - west) / (east - west) * width,
            (mercator(north) - mercator(lat))
            / (mercator(north) - mercator(south))
            * height,
        )

    png = base64.b64encode((FONTE / "geni_2024_controle.png").read_bytes()).decode()
    h = f'<figure class="territorio-mapa"><svg viewBox="0 0 {width} {height+40:.1f}" role="img" aria-label="Controle territorial armado em 2024 e locais de votação em 2026, janela metropolitana do Rio de Janeiro">'
    h += f'<defs><clipPath id="territorio-janela"><rect width="{width}" height="{height:.1f}"/></clipPath></defs>'
    h += f'<rect width="{width}" height="{height:.1f}" fill="#dce7e3"/>'
    malha = ler(ROOT / "apuracao/public/geo/mun/RJ.geojson")
    for feature in malha["features"]:
        geom = feature["geometry"]
        polygons = (
            geom["coordinates"]
            if geom["type"] == "MultiPolygon"
            else [geom["coordinates"]]
        )
        for polygon in polygons:
            path = "".join(
                "M"
                + "L".join(
                    f"{x:.2f},{y:.2f}" for lon, lat in ring for x, y in [xy(lat, lon)]
                )
                + "Z"
                for ring in polygon
            )
            h += f'<path d="{path}" fill="#eae8df" fill-rule="evenodd" stroke="#b8c4bd" stroke-width=".8" clip-path="url(#territorio-janela)"/>'
    for lat in (-22.6, -22.8, -23):
        _, y = xy(lat, west)
        h += f'<path d="M0 {y:.1f}H960" stroke="#ccc9bc" stroke-dasharray="3 5"/><text x="5" y="{y-5:.1f}" font-size="12" fill="#777">{lat:.1f}°</text>'
    h += f'<image href="data:image/png;base64,{png}" x="0" y="0" width="{width}" height="{height:.1f}" preserveAspectRatio="none" opacity=".75"/>'
    for r in d["locais"]:
        if r["controle"] == "Sem marcação":
            continue
        x, y = xy(r["lat"], r["lon"])
        text = f'{r["nome"]} · {r["municipio"]} · zona {r["zona"]} · controle {r["controle"]} (2024) · Lula {num(r["lula"])} / Flávio {num(r["flavio"])} votos (2026)'
        h += f'<a href="{escape(r["link"],quote=True)}" aria-label="{escape(text,quote=True)}"><circle cx="{x:.2f}" cy="{y:.2f}" r="2.1" fill="#252724" stroke="white" stroke-width=".5"><title>{escape(text)}</title></circle></a>'
    # Sedes IBGE da mesma base municipal; os círculos eleitorais vêm do cadastro.
    for r in d["referencias"]:
        x, y = xy(r["sede_lat"], r["sede_lon"])
        label = escape(r["nome"].title())
        h += f'<text x="{x:.1f}" y="{y:.1f}" font-size="13" stroke="#faf9f4" stroke-width="4" fill="#faf9f4">{label}</text>'
        h += f'<text x="{x:.1f}" y="{y:.1f}" font-size="13" fill="#252724">{label}</text>'
    h += f'<text x="8" y="{height+26:.1f}" font-size="13">● Local cadastral sobre área marcada como controle · toque para abrir a ficha</text></svg>'
    h += '<figcaption><div class="territorio-legenda">'
    for name, cor in (
        ("ADA", "#DDB310"),
        ("CV", "#C60000"),
        ("Milícia", "#00008B"),
        ("TCP", "#00B25D"),
    ):
        h += f'<span><i style="background:{cor}"></i>{name}</span>'
    return (
        h
        + "</div>Imagem territorial original GENI/Fogo Cruzado, reprojetada como no mapa publicado. A área vazia não certifica ausência de domínio. A janela não delimita a RMRJ.</figcaption></figure>"
    )


def render(d):
    # Import tardio evita ciclo com a página de auditoria.
    from .pagina_auditoria import tabela

    controls = [
        r
        for r in d["resumo"]
        if r["camada"] == "controle" and r["margem_m"] == 0 and r["grupo"] in GRUPOS
    ]
    n = sum(r["locais"] for r in controls)
    lula, flavio = (sum(r[k] for r in controls) for k in ("lula", "flavio"))
    pct = 100 * lula / (lula + flavio)
    h = f"""<div id="territorio-armado"><h3>Agora, o território delimitado: controle e influência no Rio</h3>
    <p>O mapa GENI/UFF–Fogo Cruzado de 2024 permite localizar áreas de controle armado. Encontramos <b>{num(n)} locais cadastrais de votação</b> sobre essas áreas, com BUs completos em 2026. Neles, Lula recebeu <b>{num(pct,2)}%</b> e Flávio <b>{num(100-pct,2)}%</b> dos votos válidos. O resultado varia por grupo e não sustenta a ideia de um voto uniforme nesses territórios.</p>
    <div class="note">O endereço é o do local de votação, não o do eleitor. O mapa antecede a eleição em dois anos; a classificação territorial pode ter mudado. Este cruzamento não identifica membros de grupos nem comprova pressão sobre eleitores.</div>
    {mapa(d)}<div class="duo"><div><h4>Controle territorial · voto no 2º turno</h4>{barras(controls)}</div><div><h4>Influência territorial · análise separada</h4>{barras([r for r in d['resumo'] if r['camada']=='influencia' and r['margem_m']==0 and r['grupo'] in GRUPOS])}</div></div>
    <h4>O resultado depende de pontos próximos à borda?</h4>
    <p>Retiramos locais próximos a outra classe do mapa. A resolução é de aproximadamente 34 × 37 metros por pixel. Os cortes de 100 e 300 metros são sensibilidades, não margens de erro conhecidas. Quanto menor o recorte, menor sua capacidade de representar o conjunto.</p>"""
    h += tabela(
        [
            "Controle",
            "Todos · locais / Lula",
            "Interior ≥100 m · locais / Lula",
            "Interior ≥300 m · locais / Lula",
        ],
        [
            [g]
            + [
                f'{num(r["locais"])} / {num(r["pct_lula"],2)+"%" if r["pct_lula"] is not None else "sem dado"}'
                for margin in (0, 100, 300)
                for r in d["resumo"]
                if r["camada"] == "controle"
                and r["grupo"] == g
                and r["margem_m"] == margin
            ]
            for g in GRUPOS
        ],
    )
    capital = [
        r
        for r in d["recortes"]
        if r["camada"] == "controle"
        and r["nivel"] == "zona"
        and str(r["mun_tse"]) == "60011"
    ]
    h += "<details><summary>Rio de Janeiro: zonas e grupos, somente locais sobre áreas de controle</summary>"
    h += tabela(
        ["Zona", "Grupo", "Locais", "Lula", "Flávio", "Lula %"],
        [
            [
                r["zona"],
                r["grupo"],
                num(r["locais"]),
                num(r["lula"]),
                num(r["flavio"]),
                num(r["pct_lula"], 2) + "%",
            ]
            for r in sorted(capital, key=lambda r: (r["zona"], r["grupo"]))
        ],
    )
    h += "</details><details><summary>Municípios e grupos no recorte territorial</summary>"
    h += tabela(
        ["Município", "Grupo", "Locais", "Lula", "Flávio", "Lula %"],
        [
            [
                escape(r["municipio"]),
                r["grupo"],
                num(r["locais"]),
                num(r["lula"]),
                num(r["flavio"]),
                num(r["pct_lula"], 2) + "%",
            ]
            for r in d["recortes"]
            if r["camada"] == "controle" and r["nivel"] == "municipio"
        ],
    )
    h += f"""</details><p class="small">Cobertura: {num(d['total_janela']['locais'])} locais cadastrais com BUs completos dentro da janela retangular da fonte. {num(d['excluidos_rj'].get('fora_janela',0))} locais do RJ ficam fora dela. Controle e influência são camadas separadas; seus votos não devem ser somados. A classificação “sem marcação” não foi usada como grupo de ausência comprovada de crime.</p>
    <details><summary>Proveniência, projeção e limitações</summary><p>{escape(d['metodo'])}</p><p>{escape(d['limites'])}</p><p>O JSON incorporado ao <a href="{d['fonte']['url']}">mapa público de 2024</a>, as imagens e o código que posiciona os pixels foram preservados com SHA-256. A transformação usa Web Mercator, como o desenho da camada; interpolar latitude linearmente deslocaria a classificação. <a href="https://geni.uff.br/wp-content/uploads/sites/357/2025/12/Relatorio-Mapa-2025-Alt3.pdf">Relatório metodológico de 2025</a>. Os registros se apoiam em denúncias e procedimentos de classificação territorial descritos pela fonte; não são um censo de toda a atuação criminal.</p></details>
    <p><a href="assets/analise_realidade_eleicao/territorio_locais.csv" download>Locais, votos e classificação (CSV)</a> · <a href="assets/analise_realidade_eleicao/territorio_recortes.csv" download>Municípios e zonas por grupo (CSV)</a> · <a href="assets/analise_realidade_eleicao/territorio.json">Dados, método e hashes (JSON)</a></p></div>"""
    return h
