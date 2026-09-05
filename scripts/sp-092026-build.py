#!/usr/bin/env python3
"""Gera o atlas descritivo de SP exclusivamente de dados e fontes públicas."""

import json
import math
from html import escape as esc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs"
ASSETS = OUT / "assets"
D = json.loads((ASSETS / "sp_092026_data.json").read_text())
P = json.loads((ASSETS / "sp_092026_pesquisas.json").read_text())
N = json.loads((ASSETS / "sp_092026_pnad.json").read_text())
C = D["municipios"]
A = N["anual_2025_visita1"]
Q = N["trimestral_2026_t1"]


def fmt(v, n=0):
    return f"{v:,.{n}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def link(url, label):
    return f'<a href="{esc(url, quote=True)}">{esc(label)}</a>'


def table(head, rows, ident=""):
    return (
        f'<div class="table-scroll" tabindex="0" role="region" aria-label="Tabela: {esc(head[0])}"><table id="{ident}"><thead><tr>'
        + "".join(f'<th scope="col">{x}</th>' for x in head)
        + "</tr></thead><tbody>"
        + "".join("<tr>" + "".join(f"<td>{x}</td>" for x in r) + "</tr>" for r in rows)
        + "</tbody></table></div>"
    )


def bars(values, maxval=100):
    return (
        '<div class="bars">'
        + "".join(
            f'<div class="bar"><span>{esc(k)}</span><b>{fmt(v, 1)}%</b><div><i style="width:{min(100, v / maxval * 100):.3f}%"></i></div></div>'
            for k, v in values
        )
        + "</div>"
    )


def source(key, pages):
    return f'<p class="note">Fonte: {link(P["urls"][key], key.title())}, {pages}. Percentuais publicados; arredondamentos preservados.</p>'


def chapter(num, ident, title, lead, body, dark=False):
    return f'<section id="{ident}" class="chapter {"dark" if dark else ""}"><div class="wrap"><header class="chapter-head"><span class="number">{num:02}</span><div><h2>{title}</h2><p class="lead">{lead}</p></div></header>{body}</div></section>'


def svgmap():
    geo = json.loads((ASSETS / "sp_092026_municipios.geojson").read_text())
    byid = {r["id"]: r for r in C}
    colors = {
        "Jair → Jair": "#28705f",
        "Jair → PT": "#d8a631",
        "PT → PT": "#b84648",
        "Jair → Empate": "#859394",
    }
    polygons = []
    coords = []
    for feature in geo["features"]:
        shape = feature["geometry"]
        rings = (
            shape["coordinates"]
            if shape["type"] == "Polygon"
            else [ring for poly in shape["coordinates"] for ring in poly]
        )
        coords.extend(
            (x * math.cos(math.radians(23)), -y)
            for ring in rings
            for x, y, *rest in ring
        )
        polygons.append((feature["properties"]["codarea"], rings))
    xs, ys = zip(*coords, strict=True)
    xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
    scale = min(960 / (xmax - xmin), 620 / (ymax - ymin))
    paths = []
    for ident, rings in polygons:
        r = byid[ident]
        path = " ".join(
            "M"
            + "L".join(
                f"{20 + (x * math.cos(math.radians(23)) - xmin) * scale:.2f},{20 + (-y - ymin) * scale:.2f}"
                for x, y, *rest in ring
            )
            + "Z"
            for ring in rings
        )
        paths.append(
            f'<path data-id="{ident}" d="{path}" fill="{colors[r["virada"]]}" fill-rule="evenodd"><title>{esc(r["nome"])}: {esc(r["virada"])}; Bolsonaro 2022: {fmt(r["jair_2022_2_pct"], 2)}%</title></path>'
        )
    return (
        '<svg id="municipal-map" viewBox="0 0 1000 660" role="img" aria-labelledby="map-title"><title id="map-title">645 municípios de São Paulo: resultados presidenciais de 2018 e 2022</title>'
        + "".join(paths)
        + "</svg>"
    )


NEWS = [
    (
        "Metrópole de São Paulo",
        "Mobilidade e previsibilidade",
        "A cobertura da paralisação da CPTM em 4 de agosto registra efeitos sobre deslocamentos. O episódio documenta uma interrupção concreta; não mede, sozinho, a qualidade de todo o sistema.",
        "04/08/2026",
        "UOL",
        "https://noticias.uol.com.br/cotidiano/ultimas-noticias/2026/08/04/operacao-greve-cptm.ghtm",
    ),
    (
        "Campinas",
        "Continuidade do abastecimento",
        "A Ares-PCJ publicou interrupção programada da Sanasa para 18 de agosto. Manutenção anunciada não deve ser descrita como colapso hídrico: a questão observável é a informação ao usuário e a continuidade do serviço.",
        "Agosto/2026",
        "Ares-PCJ",
        "https://www.arespcj.com.br/conteudo/sanasa-campinas-interrupcao-programada1098",
    ),
    (
        "Baixada Santista",
        "Logística e execução de obras",
        "O termo de transferência de julho marca uma etapa contratual do túnel Santos–Guarujá. Projeto executivo, início de obras e entrega são marcos diferentes. O financiamento envolve esferas distintas de governo.",
        "07/07/2026",
        "Concessionária TSG",
        "https://tsgp.com.br/2026/07/07/tsg-concessionaria-assina-tti-e-avanca-com-o-tunel-santos-guaruja/",
    ),
    (
        "São José dos Campos",
        "Indústria e qualificação",
        "Notícia de agosto reúne vagas e bancos de talentos da Embraer. A existência de anúncios evidencia demanda de recrutamento; banco de talentos não equivale a contratação realizada.",
        "26/08/2026",
        "Notícias SJC",
        "https://noticiassjc.com.br/embraer-abre-dezenas-de-vagas-de-emprego-e-bancos-de-talentos-em-sao-jose/",
    ),
    (
        "Sorocaba",
        "Emprego industrial",
        "A abertura de 100 vagas na Toyota foi noticiada em agosto, com seleção sem exigência de experiência. É um fato localizado, distinto do saldo líquido de emprego de toda a região.",
        "25/08/2026",
        "Canal Estado SP",
        "https://www.canalestadosp.com.br/noticia/toyota-tem-100-vagas-abertas-em-sorocaba-e-selecao-nao-exige-experiencia-a3809c8b",
    ),
    (
        "Ribeirão Preto",
        "Calor e saúde pública",
        "O Jornal da USP discute os efeitos de variações climáticas e eventos extremos na saúde em Ribeirão Preto. A evidência liga exposição ambiental e capacidade dos serviços; não estabelece efeito eleitoral.",
        "12/08/2026",
        "Jornal da USP",
        "https://jornal.usp.br/campus-ribeirao-preto/variacoes-climaticas-e-eventos-extremos-aumentam-riscos-a-saude-publica-em-ribeirao-preto/",
    ),
    (
        "Araraquara e São Carlos",
        "Produção e mercado de trabalho",
        "O balanço econômico do segundo trimestre reúne superávit comercial e aumento do número de empresas, junto de saldo negativo de empregos no período. Exportação, abertura de empresas e emprego não são indicadores intercambiáveis.",
        "18/08/2026",
        "Jornal de Araraquara",
        "https://jornaldeararaquara.com.br/araraquara-encerra-2o-trimestre-com-superavit-de-us-17058-milhoes-e-saldo-positivo-de-945-empresas/",
    ),
    (
        "São José do Rio Preto e Araçatuba",
        "Estiagem, umidade e incêndios",
        "A cobertura de 28 de agosto registra alerta de calor e baixa umidade para o interior. Alerta meteorológico é previsão e orientação preventiva, não balanço de danos já ocorridos.",
        "28/08/2026",
        "Folha",
        "https://www1.folha.uol.com.br/cotidiano/2026/08/defesa-civil-alerta-para-umidade-critica-e-calor-extremo-no-interior-de-sp.shtml",
    ),
    (
        "Bauru e entorno",
        "Capacidade hospitalar",
        "A prefeitura de Duartina informou contratação de médicos para o Hospital Santa Luzia. Trata-se de anúncio do prestador público; efeitos sobre espera e desfechos exigem indicadores posteriores.",
        "10/08/2026",
        "Prefeitura de Duartina",
        "https://www.duartina.sp.gov.br/noticia/print-noticia/2603/hospital-santa-luzia-contrata-novos-medicos-para-mudancas-que-prometem-elevar-a-qualidade-do-atendimento/",
    ),
    (
        "Marília e Presidente Prudente",
        "Exposição ambiental e serviços de saúde",
        "O alerta de baixa umidade alcança o oeste paulista. Em Prudente, a cobertura do Agosto Laranja registra ação de conscientização sobre esclerose múltipla e serviços de reabilitação. São pautas diferentes, sem hierarquia regional inferida.",
        "31/08/2026",
        "Diário de Prudente",
        "https://www.diariodeprudente.com/centro-de-reabilitacao-encerra-agosto-laranja-com-acao-de-conscientizacao-sobre-esclerose-multipla1/",
    ),
    (
        "Vale do Ribeira",
        "Agricultura e educação técnica",
        "O IFSP Registro anunciou renovação de parceria com CoopercentralVR e Abavar. A cooperação aproxima ensino, pesquisa e organizações agrícolas. A existência da parceria não mede sua cobertura ou impacto econômico.",
        "27/08/2026",
        "IFSP Registro",
        "https://rgt.ifsp.edu.br/portal/sobre-o-campus/outras-noticias/223-snct/snct-2026/2850-ifsp-registro-renova-parceria-com-coopercentralvr-e-abavar",
    ),
]


def build():
    parts = []
    totalpop = sum(r["populacao"] for r in C)
    totalpib = sum(r["pib_2023"] for r in C)
    flips = [r for r in C if r["virada"] == "Jair → PT"]
    flipv = {
        k: sum(r[k] for r in flips)
        for k in ("jair_2018_2", "jair_2022_2", "pt_2018_2", "pt_2022_2", "populacao")
    }
    groups = [
        (
            "547",
            "Bolsonaro nas duas eleições",
            "Maioria dos municípios, sem equivalência com maioria da área urbana ou da população.",
        ),
        (
            "83",
            "Bolsonaro → Lula",
            f"{fmt(flipv['populacao'] / totalpop * 100, 1)}% da população do Censo 2022. Nenhuma virada ocorreu na direção inversa.",
        ),
        ("14", "PT nas duas eleições", "Haddad venceu em 2018 e Lula em 2022."),
        (
            "1",
            "Empate em Guará",
            "5.529 votos para cada candidato em 2022. Empate é uma categoria própria.",
        ),
    ]
    body = (
        '<div class="metrics four">'
        + "".join(
            f"<article><strong>{n}</strong><h3>{t}</h3><p>{s}</p></article>"
            for n, t, s in groups
        )
        + "</div>"
    )
    rows = []
    for yr, turn in [(2018, 1), (2018, 2), (2022, 1), (2022, 2)]:
        total = sum(D["totais_nominais"][f"{yr}_PRESIDENTE_{turn}"].values())
        b = sum(r[f"jair_{yr}_{turn}"] for r in C)
        pt_votes = sum(r[f"pt_{yr}_{turn}"] for r in C)
        rows.append(
            [
                f"{yr} · {turn}º",
                fmt(b),
                fmt(b / total * 100, 2) + "%",
                "Haddad" if yr == 2018 else "Lula",
                fmt(pt_votes),
                fmt(pt_votes / total * 100, 2) + "%",
            ]
        )
    body += table(
        ["Eleição", "Bolsonaro: votos", "% válidos", "PT", "Votos", "% válidos"], rows
    )
    body += '<div class="callout"><h3>A margem mudou; a origem individual dos votos não é observada.</h3><p>Nos 83 municípios de virada, Bolsonaro perdeu <b>662.840 votos</b> e Lula recebeu <b>1.868.006 votos a mais</b> que Haddad. O ganho petista responde por 73,8% da mudança aritmética da margem e a queda de Bolsonaro por 26,2%. Essas parcelas não identificam novos eleitores, migração individual, abstenção ou conversão.</p><p>Na capital, Bolsonaro passou de 3.694.834 para 3.191.484 votos; o PT, de 2.424.125 para 3.677.921. O mapa municipal deve ser lido junto do número de pessoas.</p></div><p class="note">Fonte: TSE, votação nominal por município e zona, 2018 e 2022; IBGE, Censo 2022. Valores recalculados a partir dos arquivos públicos.</p>'
    parts.append(
        chapter(
            1,
            "historia",
            "A maioria permaneceu. A vantagem encolheu.",
            "Bolsonaro passou de 67,97% para 55,24% dos votos válidos paulistas no segundo turno: queda de 12,73 pontos percentuais.",
            body,
        )
    )
    body = (
        '<div class="metrics three">'
        + f"<article><strong>R$ {fmt(totalpib / 1e12, 2)} tri</strong><h3>PIB municipal somado, 2023</h3><p>Produção econômica em preços correntes. Não é renda disponível das famílias.</p></article><article><strong>R$ {fmt(A['renda_pc_media_todos_abril_2026']['media'])}</strong><h3>Renda domiciliar per capita</h3><p>PNAD anual 2025, preços de abril de 2026; IC 95% de R$ {fmt(A['renda_pc_media_todos_abril_2026']['low'])} a R$ {fmt(A['renda_pc_media_todos_abril_2026']['high'])}.</p></article><article><strong>5,87%</strong><h3>Desocupação no recorte 16+</h3><p>PNAD 1º trimestre de 2026; IC 95%: 5,34% a 6,40%. O indicador oficial usual usa 14+.</p></article></div>"
    )
    body += (
        '<div class="split"><article><h3>Renda domiciliar de pessoas com 16 anos ou mais</h3>'
        + bars([(k, v["pct"]) for k, v in A["renda_domiciliar_16_mais"].items()])
        + '<p class="note">Renda conhecida, ponderada por pessoas; salário mínimo-alvo de R$ 1.621. Não é proporção de domicílios.</p></article><article><h3>Renda per capita nos domínios disponíveis</h3>'
        + table(
            ["Domínio PNAD", "Média em R$", "IC 95%"],
            [
                [
                    k,
                    fmt(v["renda_pc_media_abril_2026"]["media"]),
                    fmt(v["renda_pc_media_abril_2026"]["low"])
                    + " a "
                    + fmt(v["renda_pc_media_abril_2026"]["high"]),
                ]
                for k, v in A["territorios"].items()
            ],
        )
        + "</article></div>"
    )
    body += (
        '<p>A PNAD atualiza o estado e os domínios identificáveis na base. Ela não autoriza estimar renda em cada um dos 645 municípios: para isso usamos o Censo 2022. Escolaridade, no recorte 16+, é 25,62% até fundamental completo, 43,76% médio incompleto ou completo e 30,63% superior incompleto ou completo. Superior aqui não significa diploma concluído.</p><p class="note">Fonte: IBGE, PIB dos Municípios 2023 e PNADC anual 2025 visita 1 / trimestral 2026 T1. Pesos V1032/V1028 e 200 réplicas. '
        + link("assets/sp_092026_pnad.json", "Estimativas, intervalos e método")
        + ".</p>"
    )
    parts.append(
        chapter(
            2,
            "economia",
            "Uma potência econômica com rendas muito diferentes.",
            "Datas e universos estão separados: Censo 2022, PIB 2023, renda anual 2025 e trabalho no primeiro trimestre de 2026.",
            body,
            True,
        )
    )
    opts = [
        ("virada", "Vencedores 2018 × 2022"),
        ("jair_2018_2_pct", "Bolsonaro 2018 · 2º turno (%)"),
        ("jair_2022_2_pct", "Bolsonaro 2022 · 2º turno (%)"),
        ("tarcisio_2022_2_pct", "Tarcísio 2022 · 2º turno (%)"),
        ("mudanca_jair_pp", "Variação Bolsonaro 2018 → 2022 (pp)"),
        ("diferenca_governo_presidente_pp", "Tarcísio menos Bolsonaro 2022 (pp)"),
        ("eleitorado", "Eleitorado TSE 2026"),
        ("renda", "Renda per capita · Censo 2022 (R$)"),
        ("pib_pc_2023", "PIB per capita 2023 (R$)"),
    ]
    opts += [
        (f"{p}_{y}_1", f"{n} {y} · votos nominais")
        for p, n, years in [
            ("eduardo", "Eduardo Bolsonaro", [2018, 2022]),
            ("carla", "Carla Zambelli", [2018, 2022]),
            ("gil", "Gil Diniz", [2018, 2022]),
            ("mario", "Mário Frias", [2022]),
        ]
        for y in years
    ]
    body = (
        '<div class="controls"><label>Camada<select id="map-layer">'
        + "".join(f'<option value="{k}">{v}</option>' for k, v in opts)
        + '</select></label><label>Consultar município<select id="map-city"><option value="">Selecione um município</option>'
        + "".join(
            f'<option value="{r["id"]}">{esc(r["nome"])}</option>'
            for r in sorted(C, key=lambda r: r["nome"])
        )
        + "</select></label></div>"
    )
    body += (
        '<div class="map-layout"><div>'
        + svgmap()
        + '<p id="map-legend" class="legend"><span>Verde: Bolsonaro nas duas · Ocre: Bolsonaro → Lula · Vermelho: PT nas duas · Cinza: empate</span></p></div><aside id="map-readout" aria-live="polite"><span class="eyebrow">Atlas municipal</span><h3>645 histórias locais</h3><p>Toque no mapa ou escolha um município para consultar votos, eleitorado e renda.</p><p>Área territorial não é número de eleitores. As cores são descritivas e não representam prioridades de campanha.</p></aside></div><noscript><p>O mapa inicial funciona sem JavaScript. Para as demais camadas, consulte a tabela municipal e o CSV.</p></noscript><p class="note">Fonte: TSE e IBGE. Eleitorado: arquivo gerado em 01/07/2026, competência junho. Votos legislativos são nominais recebidos, separados dos votos de legenda e da situação jurídica atual.</p>'
    )
    parts.append(
        chapter(
            3,
            "mapa",
            "O território, em dezesseis camadas.",
            "A consulta combina resultado, mudança histórica e contexto econômico. Cada cargo conserva seu próprio denominador.",
            body,
        )
    )
    regs = sorted(D["regioes"], key=lambda r: -r["eleitorado"])
    body = table(
        [
            "Região intermediária IBGE",
            "Mun.",
            "Eleitorado 2026",
            "Bolsonaro 2018 · 2º",
            "Bolsonaro 2022 · 2º",
            "Tarcísio 2022 · 2º",
            "PIB 2023 · R$ bi",
        ],
        [
            [
                r["nome"],
                r["municipios"],
                fmt(r["eleitorado"]),
                fmt(100 * r["jair_2018_2"] / r["2018_PRESIDENTE_2_total"], 2) + "%",
                fmt(100 * r["jair_2022_2"] / r["2022_PRESIDENTE_2_total"], 2) + "%",
                fmt(100 * r["tarcisio_2022_2"] / r["2022_GOVERNADOR_2_total"], 2) + "%",
                fmt(r["pib_2023"] / 1e9, 1),
            ]
            for r in regs
        ],
    )
    body += (
        "<p>A região intermediária de São Paulo reúne "
        + fmt(regs[0]["eleitorado"] / D["eleitorado"]["total"] * 100, 1)
        + '% do eleitorado estadual. Ela inclui territórios distintos da capital, como Baixada Santista e Vale do Ribeira. Campinas é a segunda em eleitorado. A cidade-polo não deve substituir o conjunto da região na interpretação.</p><p class="note">Regiões geográficas intermediárias do IBGE; percentuais agregados por soma de votos, nunca média simples dos percentuais municipais.</p>'
    )
    parts.append(
        chapter(
            4,
            "regioes",
            "Onze regiões. Nenhuma é homogênea.",
            "A divisão do IBGE permite fechar os 645 municípios sem sobreposição. Os recortes jornalísticos do capítulo 12 usam outra escala e não são somados.",
            body,
        )
    )
    biggest = sorted(C, key=lambda r: -r["eleitorado"])[:20]
    body = table(
        [
            "Município",
            "Eleitorado",
            "Vencedores 2018 → 2022",
            "Bolsonaro 2022",
            "Tarcísio 2022",
        ],
        [
            [
                r["nome"],
                fmt(r["eleitorado"]),
                r["virada"],
                fmt(r["jair_2022_2_pct"], 2) + "%",
                fmt(r["tarcisio_2022_2_pct"], 2) + "%",
            ]
            for r in biggest
        ],
    )
    body += '<p class="note">Seleção objetiva: os vinte maiores eleitorados no arquivo do TSE de julho de 2026. Ambos os percentuais de voto são do segundo turno de 2022. A seleção não usa potencial de persuasão.</p>'
    parts.append(
        chapter(
            5,
            "cidades",
            "As vinte maiores cidades por eleitorado.",
            "Uma forma transparente de examinar a concentração demográfica, sem transformar municípios em uma lista de alvos.",
            body,
        )
    )
    names = [
        ("Eduardo Bolsonaro", "eduardo", "Federal", [2018, 2022]),
        ("Carla Zambelli", "carla", "Federal", [2018, 2022]),
        ("Mário Frias", "mario", "Federal", [2022]),
        ("Gil Diniz", "gil", "Estadual", [2018, 2022]),
    ]
    rows = []
    for name, key, cargo, years in names:
        vals = {y: sum(r.get(f"{key}_{y}_1", 0) for r in C) for y in years}
        rows.append(
            [
                name,
                cargo,
                fmt(vals[2018])
                if 2018 in vals
                else "Sem candidatura neste levantamento",
                fmt(vals[2022]),
                fmt((vals[2022] / vals[2018] - 1) * 100, 1) + "%"
                if 2018 in vals
                else "Não comparável",
            ]
        )
    body = table(
        ["Nome", "Deputado", "2018 · votos", "2022 · votos", "Variação nominal"], rows
    )
    body += '<p>Eduardo caiu de 1,84 milhão para 741,7 mil votos; Carla passou de 76,3 mil para 946,2 mil. Essas mudanças simultâneas não demonstram que eleitores de um migraram para a outra. Gil disputa outro cargo e Mário não tem observação eleitoral de 2018 neste conjunto.</p><h3>Governo: porcentagens próximas, contagens diferentes</h3><p>No segundo turno de 2022, Tarcísio recebeu <b>13.480.643 votos, 55,27%</b>; Bolsonaro, <b>14.216.587, 55,24%</b>. São 735.944 votos de diferença e apenas 0,03 ponto na participação. O total de votos válidos para governo é menor: percentuais quase iguais não provam que sejam os mesmos eleitores.</p><p class="note">TSE, QT_VOTOS_NOMINAIS. O registro de votos recebidos é histórico; não é afirmação sobre mandato, elegibilidade ou validade jurídica atual. Os dados por município de cada nome estão nas camadas do mapa e no CSV.</p>'
    parts.append(
        chapter(
            6,
            "nomes",
            "O voto de cada nome tem sua própria escala.",
            "Comparar deputados e presidente exige separar cargo, ano, tamanho do eleitorado e denominador. O mapa mostra a distribuição, sem inferir transferência de apoio.",
            body,
            True,
        )
    )
    rows = []
    for p in P["pesquisas"]:

        def score(k, poll=p):
            return (
                " × ".join(fmt(v, 1) for v in poll[k])
                if k in poll
                else "Não disponível"
            )

        rows.append(
            [
                link(P["urls"][p["id"]], p["nome"]),
                p["campo"],
                score("governo"),
                score("governo2"),
                score("presidente"),
                score("presidente2"),
            ]
        )
    body = table(
        [
            "Instituto",
            "Campo · 2026",
            "Gov. 1º · T × H",
            "Gov. 2º · T × H",
            "Pres. 1º · F × L",
            "Pres. 2º · F × L",
        ],
        rows,
    )
    body += '<p class="note">T = Tarcísio; H = Haddad; F = Flávio; L = Lula. Votos totais em %, com outros candidatos e não escolha fora dos pares mostrados. Cenários não são idênticos. Real Time inclui Marçal; Quaest aqui usa o cenário II, sem Marçal. Todos os registros e páginas estão abaixo.</p>'
    body += '<div class="callout"><h3>Os documentos têm níveis diferentes de completude.</h3><p>Datafolha presidencial vem da notícia da Folha de 22/08; o PDF recebido só cobre o estado. A notícia da Real Time informa 44% para Flávio e 49% para Lula no segundo turno. Esse resultado contrário aos demais está preservado, com conferência do PDF pendente. A Quaest não publica segundo turno presidencial no relatório estadual consultado.</p></div>'
    body += table(
        ["Instituto", "Amostra", "Margem declarada", "Método", "Registro", "Documento"],
        [
            [
                p["nome"],
                fmt(p["n"]),
                "±" + fmt(p["me"], 1) + " pp",
                p["metodo"],
                p["registro"],
                p["status"] + "; p. " + p["paginas"],
            ]
            for p in P["pesquisas"]
        ],
    )
    body += "<p>O corte desta revisão é 5 de setembro de 2026. Veritá de julho foi localizada em notícia, mas o denominador do placar 59,6 × 40,4 para governo requer confirmação; por isso não integra a tabela comparável. A busca por Futura não confirmou relatório estadual recente equivalente. Não substituímos resultados de SP por pesquisa nacional.</p>"
    body += (
        '<p class="note">Complementos: '
        + link(P["urls"]["datafolha_pres"], "Datafolha presidencial, Folha")
        + " · "
        + link(P["urls"]["rt_pres"], "Real Time presidencial, Metrópoles")
        + " · "
        + link(P["urls"]["verita"], "Veritá, notícia de julho")
        + ".</p>"
    )
    parts.append(
        chapter(
            7,
            "pesquisas",
            "Cinco institutos, perguntas que precisam ser distinguidas.",
            "Tarcísio aparece numericamente à frente de Haddad em todas as pesquisas reunidas. As diferenças de campo, método, lista e não escolha impedem tratar a sequência como uma única série.",
            body,
        )
    )
    body = (
        '<div class="split"><article><h3>Não escolha no 1º turno para governo</h3>'
        + bars([(p["nome"], p["nao_escolha_gov"]) for p in P["pesquisas"]])
        + '</article><article><h3>O contraste muda ao excluir a não escolha</h3><p>Na Quaest, Tarcísio tem 40% dos votos totais; excluídos 27% de não escolha, são aproximadamente <b>54,8% dos votos atribuídos a candidatos</b>. Na Atlas, 51,1% com 5,5% de não escolha equivalem a <b>54,1%</b>.</p><p>Haddad, pelo mesmo cálculo, passa de 27% a 37,0% na Quaest e de 39,9% a 42,2% na Atlas. A aproximação de um candidato não faz as pesquisas concordarem em tudo.</p><p class="note">Sensibilidade de denominador: valor / (100 − não escolha). Não é previsão de votos válidos na eleição nem reponderação da amostra.</p></article></div>'
    )
    body += (
        "<h3>Margem de um candidato não é margem da diferença</h3><p>A Atlas declara ±1 pp na página 5, enquanto seu catálogo informa ±2 pp. A discrepância precisa ser esclarecida. Sob amostragem aleatória simples, 1.810 entrevistas produziriam margem máxima de cerca de 2,30 pp; o desenho digital e a ponderação exigem explicação própria. Não substituímos a incerteza desconhecida por uma margem inventada.</p>"
        + source("atlas", "p. 5")
        + '<p class="note">'
        + link("https://www.atlasintel.org/polls/exclusive-polls", "Catálogo Atlas")
        + ". Os pares de intenções têm covariância; somar ou reutilizar mecanicamente a margem individual não calcula a incerteza da diferença.</p>"
    )
    parts.append(
        chapter(
            8,
            "comparabilidade",
            "Antes de discutir tendência, confira o denominador.",
            "A não escolha para governo varia de 5,5% a 27%. Parte da distância entre percentuais resulta dessa diferença de resposta.",
            body,
            True,
        )
    )
    rows = []
    for i, (k, v) in enumerate(A["renda_domiciliar_16_mais"].items()):
        rows.append(
            [
                k,
                fmt(v["pct"], 2),
                fmt(v["low"], 2) + " a " + fmt(v["high"], 2),
                fmt(P["perfis_renda_sm"]["Quaest"][i], 1),
                fmt(P["perfis_renda_sm"]["Datafolha"][i], 2),
            ]
        )
    body = table(
        [
            "Renda familiar",
            "PNAD 16+ · %",
            "IC 95% PNAD",
            "Quaest · %",
            "Datafolha · %",
        ],
        rows,
    )
    body += "<p>A PNAD está em preços de abril de 2026 e salário mínimo-alvo de R$ 1.621. As pesquisas perguntam renda declarada no campo de agosto; família, domicílio, universo eleitoral e não resposta também podem diferir. Datafolha deixa <b>3,42%</b> sem classificação nas três faixas. As bases publicadas são ponderadas: não devem ser chamadas de contagem bruta de entrevistas.</p><p>Os perfis são diferentes, mas esta tabela, isoladamente, não prova viés do voto. Uma reponderação exigiria harmonizar a régua temporal e os universos, verificar as células e conhecer as restrições conjuntas. Não publicamos um placar “corrigido”.</p><h3>Controles de transcrição</h3>"
    body += table(
        ["Fonte", "Controle", "Maior resíduo verificado"],
        [
            ["Datafolha, p. 27", "Sexo, idade e escolaridade; governo", "0,59 pp"],
            ["Atlas, p. 5, 10 e 18", "Sexo e renda; governo e Presidência", "0,15 pp"],
            ["Quaest, p. 9 e 114", "Sexo e renda; governo", "0,85 pp"],
        ],
    )
    body += (
        '<p class="note">Arredondamentos de bases e células limitam o fechamento. Foram extraídas as páginas 20 a 46 do anexo nativo Datafolha; no PDF Quaest de 117 páginas, o OCR integral é auxiliar, e as tabelas usadas foram conferidas visualmente. '
        + link(
            "assets/sp_092026_pesquisas.json", "Valores, resíduos, registros e hashes"
        )
        + ".</p>"
    )
    parts.append(
        chapter(
            9,
            "auditoria",
            "A composição social exige mais que uma tabela de cotas.",
            "A PNAD serve como referência de renda e escolaridade. O TSE é a referência para o universo do eleitorado; população com 16+ não é a mesma coisa que eleitores registrados.",
            body,
        )
    )
    rows = [
        [k, fmt(v[0], 1), fmt(v[1], 1), fmt(v[2], 1)]
        for k, v in P["atlas_alternativos"].items()
    ]
    body = table(
        [
            "Adversário de Lula na Atlas",
            "Adversário · %",
            "Lula · %",
            "Não escolha · %",
        ],
        rows,
    )
    body += (
        '<p>Dentro da mesma pesquisa Atlas, Flávio tem 46,8%, Caiado 45,4%, Zema 43,8% e Renan 33,5%. Lula também varia, de 41,1% a 43,3%. A troca de cenário é uma comparação de perguntas na mesma amostra; não é experimento causal nem prova de transferência de eleitores.</p><div class="split"><article><h3>Do primeiro para o segundo turno</h3>'
        + bars(
            [
                ("Flávio · primeiro", 39.9),
                ("Flávio · segundo", 46.8),
                ("Lula · primeiro", 36),
                ("Lula · segundo", 43.3),
            ]
        )
        + "</article><article><h3>O que a diferença permite afirmar</h3><p>Na Atlas, as margens de intenção crescem 6,9 pp para Flávio e 7,3 pp para Lula. São ganhos líquidos entre perguntas. A razão 0,95:1 não identifica ganho bruto fora das bases, porque pode haver saída e entrada simultâneas.</p><p>Os cruzamentos examinados não fornecem uma matriz individual completa que identifique o voto combinado Tarcísio + Flávio ou Tarcísio + Lula. Uma fita de fluxo dependeria de hipóteses, e não pode ser tratada como dado observado.</p></article></div>"
        + source("atlas", "p. 17 e 21 a 24")
    )
    parts.append(
        chapter(
            10,
            "cenarios",
            "Cenários alternativos não identificam percursos individuais.",
            "As margens são publicadas. A combinação de votos por pessoa requer uma tabela conjunta ou microdados pareados.",
            body,
        )
    )
    body = table(
        [
            "Nome",
            "Datafolha · média das duas",
            "Quaest · média das duas",
            "Quaest · 1ª escolha",
            "Quaest · 2ª escolha",
        ],
        [
            [
                name,
                fmt(
                    P["senado_datafolha"].get(
                        name, P["senado_datafolha"].get("Ricardo Salles", 0)
                    )
                    if name == "Salles"
                    else P["senado_datafolha"][name]
                ),
                *[fmt(v) for v in vals],
            ]
            for name, vals in P["senado_quaest"].items()
        ],
    )
    body += (
        "<p>As médias de duas escolhas somam 100% considerando candidatos e não escolha. Elas não são a proporção de entrevistados que citaram o nome ao menos uma vez. A primeira e a segunda escolha são posições de resposta, não previsão de quem ocupará a primeira ou a segunda cadeira.</p><p>Em 2018, Major Olímpio recebeu 9.039.717 votos e Mara Gabrilli, 6.513.282; em 2022, Marcos Pontes recebeu 10.714.913. O número de vagas mudou entre as duas eleições: comparar participações exige esse cuidado adicional.</p>"
        + source("datafolha", "p. 12 e 14")
        + source("quaest", "p. 61")
    )
    parts.append(
        chapter(
            11,
            "senado",
            "Duas vagas, duas escolhas, uma conta própria.",
            "O Senado tem disputa e denominador distintos. Não se pode somar votos de deputados ou popularidade presidencial para deduzir uma dupla vencedora.",
            body,
            True,
        )
    )
    body = (
        '<div class="split"><article><h3>Quaest: o problema mais grave</h3>'
        + bars(list(P["temas_quaest"].items()))
        + source("quaest", "p. 105")
        + "</article><article><h3>Atlas: até três problemas</h3>"
        + bars(list(P["temas_atlas"].items()))
        + source("atlas", "p. 41")
        + "</article></div>"
    )
    body += '<p>Violência e saúde aparecem entre os problemas mais citados. A Atlas permite até três respostas; a Quaest pede o problema mais grave. Os valores não medem a mesma coisa e não devem ser usados para dizer que um tema cresceu de uma pesquisa para outra.</p><h3>Como os temas aparecem nas notícias locais</h3><p class="note">Seleção documental, não amostra representativa da imprensa nem medição de prioridades regionais. A escala dos recortes abaixo difere das onze regiões IBGE.</p><div class="news-grid">'
    for region, title, copy, date, outlet, url in NEWS:
        body += f'<article><span class="eyebrow">{esc(region)}</span><h3>{esc(title)}</h3><p>{esc(copy.replace("–", " e "))}</p><p class="note">{esc(date)} · {link(url, outlet)}</p></article>'
    body += (
        '</div><p class="note">Financiamento do túnel: '
        + link(
            "https://www.gov.br/portos-e-aeroportos/pt-br/assuntos/noticias/2026/03-1/governo-assina-emprestimo-do-banco-do-brasil-para-conclusao-das-obras-do-tunel-santos-guaruja",
            "Ministério de Portos e Aeroportos",
        )
        + ".</p>"
    )
    parts.append(
        chapter(
            12,
            "temas",
            "Segurança, saúde e o cotidiano de cada região.",
            "As pesquisas medem saliência estadual. As notícias dão exemplos locais, sem permitir deduzir a opinião de todos os moradores.",
            body,
        )
    )
    body = (
        '<div class="editorial"><span class="eyebrow">Opinião editorial declarada · perspectiva favorável a Flávio Bolsonaro</span><h3>Uma preferência política não dispensa os fatos contrários.</h3><p>A perspectiva favorável a Flávio encontra apoio descritivo na votação histórica de Bolsonaro e na posição de Flávio nos cenários Datafolha e Atlas. Isso sustenta a leitura de competitividade paulista; não demonstra vitória garantida ou herança automática dos votos de Tarcísio.</p><p>O contraponto tem o mesmo peso: Bolsonaro perdeu 12,73 pontos entre os segundos turnos de 2018 e 2022; a notícia da Real Time traz Lula numericamente à frente no segundo turno; na Atlas, a avaliação negativa de Flávio é 55%, contra 42% positiva, e a rejeição declarada chega a 48,3%.</p><p>A leitura editorial é que competitividade e vulnerabilidade coexistem. Os dados publicados não identificam quantos eleitores combinam cada voto estadual e presidencial. Transformar a diferença entre candidatos em uma quantidade de votos “disponíveis” excederia a evidência.</p></div>'
        + source("atlas", "p. 37 e 39")
    )
    parts.append(
        chapter(
            13,
            "editorial",
            "O posicionamento está declarado. O método é verificável.",
            "Esta seção interpreta os fatos sob uma preferência editorial explícita. As tabelas mantêm os resultados desfavoráveis e as limitações das fontes.",
            body,
            True,
        )
    )
    body = '<div class="controls"><label>Filtrar tabela por município ou região<input id="municipal-search" type="search" placeholder="Ex.: Guará, Campinas, Santos"></label></div><p id="table-count" aria-live="polite">645 municípios</p>'
    body += table(
        [
            "Município",
            "Região IBGE",
            "Eleitorado",
            "Renda pc Censo · R$",
            "Bolsonaro 2018 · 2º",
            "Bolsonaro 2022 · 2º",
            "Tarcísio 2022 · 2º",
            "Vencedores",
        ],
        [
            [
                esc(r["nome"]),
                esc(r["regiao"]),
                fmt(r["eleitorado"]),
                fmt(r["renda"], 2),
                fmt(r["jair_2018_2_pct"], 2) + "%",
                fmt(r["jair_2022_2_pct"], 2) + "%",
                fmt(r["tarcisio_2022_2_pct"], 2) + "%",
                r["virada"],
            ]
            for r in sorted(C, key=lambda r: r["nome"])
        ],
        "municipal-table",
    )
    body = (
        "<details><summary>Abrir a tabela completa dos 645 municípios</summary>"
        + body
        + "</details><p>"
        + link("assets/sp_092026_municipios.csv", "Baixar CSV municipal")
        + " · "
        + link("assets/sp_092026_data.json", "Abrir base JSON")
        + " · "
        + link("assets/sp_092026_municipios.geojson", "Malha municipal GeoJSON")
        + "</p>"
    )
    parts.append(
        chapter(
            14,
            "dados",
            "Todos os municípios, com a mesma regra.",
            "O arquivo completo inclui os votos nominais dos parlamentares por ano, os totais por cargo, PIB, eleitorado e fontes geográficas.",
            body,
        )
    )
    body = '<ol class="method-list"><li><b>TSE.</b> ZIPs de votação por candidato, município e zona de 2018 e 2022. Presidência no arquivo BR filtrado por SP; demais cargos no arquivo SP, evitando duplicidade. Junção ao IBGE por nome normalizado e exceções explícitas. São 645 municípios.</li><li><b>Empates.</b> Comparação das contagens inteiras. Percentual igual a 50% não é vitória do candidato oposto. Guará permanece em categoria separada.</li><li><b>PNAD.</b> Renda conhecida de pessoas 16+; estatísticas monetárias e domínios identificados. População anual estimada e eleitorado cadastrado não são intercambiáveis. Os intervalos usam 200 réplicas oficiais e aproximação normal.</li><li><b>Pesquisas.</b> Percentuais publicados e arredondamentos preservados. Bases ponderadas não são contagens de campo. Não há média agregadora, ajuste causal ou previsão eleitoral neste relatório.</li><li><b>Geografia.</b> Municípios agrupados nas onze regiões intermediárias IBGE. A malha é simplificada para visualização; área não representa população. Censo e PIB conservam anos e conceitos distintos.</li><li><b>Rastreabilidade.</b> Os quatro PDFs têm SHA-256, número de páginas, registros e status de conferência na base de pesquisas. A ausência de um PDF ou cruzamento é indicada onde limita a análise.</li></ol>'
    body += table(
        ["Fonte", "Acesso"],
        [
            [
                "TSE, resultados 2018",
                link(
                    "https://dadosabertos.tse.jus.br/dataset/resultados-2018",
                    "Dados Abertos TSE",
                ),
            ],
            [
                "TSE, resultados 2022",
                link(
                    "https://dadosabertos.tse.jus.br/dataset/resultados-2022",
                    "Dados Abertos TSE",
                ),
            ],
            [
                "TSE, eleitorado",
                link(
                    "https://dadosabertos.tse.jus.br/dataset/eleitorado-atual",
                    "Perfil atual",
                ),
            ],
            [
                "IBGE, renda Censo 2022",
                link("https://sidra.ibge.gov.br/tabela/10295", "SIDRA 10295"),
            ],
            [
                "IBGE, população",
                link("https://sidra.ibge.gov.br/tabela/4714", "SIDRA 4714"),
            ],
            [
                "IBGE, PIB municipal",
                link(
                    "https://www.ibge.gov.br/estatisticas/economicas/contas-nacionais/9088-produto-interno-bruto-dos-municipios.html",
                    "PIB dos Municípios",
                ),
            ],
            [
                "IBGE, PNADC",
                link(
                    "https://www.ibge.gov.br/estatisticas/sociais/trabalho/9173-pesquisa-nacional-por-amostra-de-domicilios-continua-trimestral.html",
                    "PNAD Contínua",
                ),
            ],
        ],
    )
    body += '<h3>Reprodução</h3><pre><code>python3 scripts/sp-092026-data.py\npython3 scripts/sp-092026-pnad.py\npython3 scripts/sp-092026-polls.py\npython3 scripts/sp-092026-build.py</code></pre><p class="note">Requer os arquivos oficiais locais e dependências do projeto. Os números públicos são calculados dessas fontes; documentos privados de terceiros não são dependência de construção nem são distribuídos com esta página.</p>'
    body += (
        "<p>"
        + link("assets/sp_092026_pesquisas.json", "Pesquisas e hashes")
        + " · "
        + link("assets/sp_092026_pnad.json", "PNAD e incerteza")
        + " · "
        + link("index.html", "Voltar ao acervo")
        + "</p>"
    )
    parts.append(
        chapter(
            15,
            "fontes",
            "Uma trilha pública para refazer as contas.",
            "Este é um atlas descritivo com leitura editorial identificada. Não contém estimativas de persuasão individual, roteiro de campanha ou metas de conversão.",
            body,
        )
    )
    nav = [
        ("historia", "História"),
        ("mapa", "Mapa"),
        ("regioes", "Regiões"),
        ("nomes", "Nomes"),
        ("pesquisas", "Pesquisas"),
        ("auditoria", "Auditoria"),
        ("temas", "Temas"),
        ("fontes", "Fontes"),
    ]
    html = """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>São Paulo | voto, economia e pesquisas | setembro de 2026</title><meta name="description" content="Atlas descritivo dos 645 municípios de SP: TSE 2018/2022, PNAD, economia e pesquisas eleitorais, com fontes e incertezas explícitas."><meta property="og:title" content="São Paulo: a maioria permaneceu, a vantagem encolheu"><meta property="og:type" content="article"><meta property="og:url" content="https://brasil.arvor.co/sp_092026.html"><meta property="og:image" content="https://brasil.arvor.co/img/og/sp_092026.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="https://brasil.arvor.co/img/og/sp_092026.png"><link rel="canonical" href="https://brasil.arvor.co/sp_092026.html"><link rel="stylesheet" href="assets/sp_092026.css"><script defer src="assets/sp_092026.js"></script></head><body><a class="skip" href="#conteudo">Pular para o conteúdo</a><header class="masthead"><a href="index.html">ARVOR <span>Intelligence</span></a><span>Atlas estadual 02 / SP</span></header><main id="conteudo"><section class="hero"><div class="wrap"><p class="eyebrow">São Paulo · 5 de setembro de 2026 · dados e interpretação</p><h1>A maioria<br>permaneceu.<br><em>A vantagem<br>encolheu.</em></h1><div class="hero-bottom"><p>O estado que deu 67,97% a Bolsonaro em 2018 deu 55,24% em 2022. O que os votos, a economia e as pesquisas permitem dizer sobre São Paulo agora.</p><div><strong>645</strong><span>municípios<br>com dados conferidos</span></div><div><strong>34,1 mi</strong><span>eleitores<br>no cadastro TSE</span></div></div><p class="note">TSE: segundos turnos de 2018 e 2022; eleitorado de junho de 2026. Preferência editorial declarada no capítulo 13.</p></div></section><nav class="toc" aria-label="Capítulos">"""
    html += (
        "".join(link("#" + ident, label) for ident, label in nav)
        + "</nav>"
        + "".join(parts)
        + '</main><footer class="wrap footer"><b>ARVOR Intelligence</b><span>São Paulo · edição de setembro de 2026 · corte em 05/09</span></footer></body></html>'
    )
    assert "—" not in html and "–" not in html
    (OUT / "sp_092026.html").write_text(
        html.replace("<section ", "\n<section ").replace("<article>", "\n<article>")
        + "\n"
    )
    (ASSETS / "sp_092026_noticias.json").write_text(
        json.dumps(
            [
                dict(
                    zip(
                        ["recorte", "tema", "leitura", "data", "veiculo", "url"],
                        r,
                        strict=True,
                    )
                )
                for r in NEWS
            ],
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    print("Relatório gerado:", OUT / "sp_092026.html")


if __name__ == "__main__":
    build()
