"""Capítulos 01 a 05 do dossiê da apuração: resultado, noite, falha, regiões, exterior."""

from __future__ import annotations

from datetime import datetime
from html import escape

from . import pagina_comparacao as CMP
from . import pagina_figuras as F
from . import pagina_mapas as M
from . import pagina_texto as T
from .pagina_comum import (
    CANDIDATO,
    CINZA,
    FLAVIO,
    INK,
    LULA,
    NOME_UF,
    Capitulo,
    Dados,
    checar,
    figura,
    hora,
    inteiro,
    nome_proprio,
    num,
    p,
    secao,
    sinal,
    tabela,
)

HORA_APP_OFICIAL = "19:08"  # minuto em que a casa leu a tela do aplicativo oficial
INICIO = datetime(2026, 10, 4, 17, 0)
IMG = "img/apuracao_2026"


def minutos(brt: str) -> float:
    t = datetime.strptime(brt[:19], "%Y-%m-%d %H:%M:%S")
    return (t - INICIO).total_seconds() / 60


def eixo_horas(ate: int = 600, passo: int = 60) -> list[tuple[float, str]]:
    return [(m, f"{(17 + m // 60) % 24:02d}h") for m in range(0, ate + 1, passo)]


def versoes(L: dict) -> list[dict]:
    v = L["nacional"]["versoes"]
    return [dict(zip(v["colunas"], r, strict=False)) for r in v["linhas"]]


def paradas_nacionais(L: dict) -> list[dict]:
    return [
        t
        for t in L["travamentos"]["nacional"]
        if (t.get("secoes_no_salto") or 0) >= 1000
    ]


def imagem(arquivo: str, alt: str, legenda: str) -> str:
    return (
        f'<figure><img src="{IMG}/{arquivo}" alt="{escape(alt)}" loading="lazy" width="1600" '
        f'height="900"><figcaption>{legenda}</figcaption></figure>'
    )


# ------------------------------------------------------------------ 01


def r_abertura(d: Dados, cap: Capitulo) -> str:
    P = d.get("presidente.json")
    checar(
        d,
        "presidente.json",
        ["nacional.votos", "nacional.pct", "ufs", "nacional.comparacao"],
    )
    n = P["nacional"]
    h = secao(
        cap,
        "Flávio na frente.<br><em>2º turno com Lula.</em>",
        f"{num(n['pct']['flavio'], 2)}% contra {num(n['pct']['lula'], 2)}% dos válidos, "
        f"{inteiro(n['diferenca_votos'])} votos de diferença, 100% das seções.",
    )
    h += T.abertura(P)
    valores = {}
    for u in P["ufs"]:
        if u["uf"] == "ZZ":
            continue
        valores[u["uf"]] = (u["lider"], u["pct"]["flavio"] - u["pct"]["lula"], u)
    mapa = M.mapa_uf(
        valores,
        lambda uf, v: M.cor_vencedor(v[0], v[1]) if v else "#d8d4c8",
        lambda uf, v: uf,
        lambda uf, v: (
            f"{NOME_UF[uf]}: Flávio {num(v[2]['pct']['flavio'], 2)}% × Lula {num(v[2]['pct']['lula'], 2)}%"
            if v
            else uf
        ),
        "Quem venceu em cada UF",
        "Mapa do Brasil por UF: azul onde Flávio venceu, vermelho onde Lula venceu; tom mais escuro, margem maior.",
        legenda=[
            ("Flávio, margem até 5", M.AZUIS[0]),
            ("Flávio, 15 a 30", M.AZUIS[2]),
            ("Flávio, 30 ou mais", M.AZUIS[3]),
            ("Lula, margem até 5", M.VERMELHOS[0]),
            ("Lula, 15 a 30", M.VERMELHOS[2]),
            ("Lula, 30 ou mais", M.VERMELHOS[3]),
        ],
        escuro=lambda uf, v: bool(v) and M.escuro_vencedor(v[1]),
    )
    pct = n["pct"]
    barras = F.barras_h(
        [
            {
                "rotulo": CANDIDATO[k][0],
                "valor": pct[k],
                "cor": CANDIDATO[k][1],
                "texto": f"{num(pct[k], 2)}%",
            }
            for k in ("flavio", "lula", "cury", "renan", "caiado", "outros")
            if k in pct
        ],
        "Votos válidos por candidatura",
        "Barras horizontais com a parcela dos válidos: "
        + ", ".join(
            f"{CANDIDATO[k][0]} {num(pct[k], 2)}%"
            for k in ("flavio", "lula", "cury", "renan", "caiado")
            if k in pct
        ),
        largura=640,
        rotulo_w=150,
    )
    h += '<div class="duas">'
    h += figura(
        mapa,
        "Margem entre os dois primeiros em pontos dos válidos. Fonte: arquivos de UF do TSE, versão final de cada um.",
        larga=False,
    )
    h += figura(
        barras,
        "Parcela dos válidos no arquivo nacional final do TSE. “Outros” soma sete candidaturas.",
        larga=False,
    )
    h += "</div></section>"
    return h


# ------------------------------------------------------------------ 02


def r_noite(d: Dados, cap: Capitulo) -> str:
    L = d.get("linha_do_tempo.json")
    checar(
        d,
        "linha_do_tempo.json",
        [
            "nacional.versoes",
            "travamentos.nacional",
            "conclusao_ufs",
            "divergencia_soma_ufs",
        ],
    )
    linhas = [r for r in versoes(L) if r["gerado_brt"] >= "2026-10-04 17:00"]
    par = paradas_nacionais(L)
    h = secao(
        cap,
        "A noite<br><em>minuto a minuto.</em>",
        f"{inteiro(L['nacional']['n_versoes_genuinas'])} versões do arquivo nacional, três paradas no pico e um lote represado.",
    )
    h += T.noite(L, linhas, par)
    sombras = [
        (minutos(t["de_brt"]), minutos(t["ate_brt"]), f"parada {i + 1}")
        for i, t in enumerate(par)
    ]
    fim = max(minutos(r["gerado_brt"]) for r in linhas)
    ate = int(min(600, ((fim // 60) + 1) * 60))
    serie = [
        (
            "Flávio",
            FLAVIO,
            [(minutos(r["gerado_brt"]), r["flavio"] / 1e6) for r in linhas if r["st"]],
        ),
        (
            "Lula",
            LULA,
            [(minutos(r["gerado_brt"]), r["lula"] / 1e6) for r in linhas if r["st"]],
        ),
    ]
    topo = max(r["flavio"] for r in linhas) / 1e6
    ymax = (int(topo // 10) + 1) * 10
    h += figura(
        F.grafico_linhas(
            serie,
            (0, ate),
            (0, ymax),
            eixo_horas(ate),
            [(v, f"{v} mi") for v in range(0, ymax + 1, 10)],
            "Votos acumulados no arquivo nacional",
            "Linhas dos votos acumulados de Flávio e Lula a cada versão do arquivo nacional, das 17h à madrugada, com as três paradas sombreadas.",
            degraus=True,
            margem_dir=90,
            sombras=sombras,
        ),
        "Cada degrau é uma versão nova do arquivo nacional de presidente (hora de geração do TSE, Brasília). Faixas: intervalos em que o arquivo nacional não teve versão nova.",
        ident="fig-noite",
    )
    barras = []
    for r in linhas:
        if not r["d_vv"] or r["d_vv"] <= 0:
            continue
        df, dl = max(r["d_flavio"] or 0, 0), max(r["d_lula"] or 0, 0)
        barras.append(
            (
                minutos(r["gerado_brt"]),
                [
                    (df / 1e6, FLAVIO),
                    (dl / 1e6, LULA),
                    (max(r["d_vv"] - df - dl, 0) / 1e6, CINZA),
                ],
            )
        )
    vmax = max(sum(v for v, _ in s) for _, s in barras)
    ymax2 = (int(vmax // 5) + 1) * 5
    h += figura(
        F.barras_tempo(
            barras,
            (0, ate),
            eixo_horas(ate),
            [(v, f"{v} mi") for v in range(0, ymax2 + 1, 5)],
            ymax2,
            "O que cada atualização trouxe",
            "Barras finas com os votos válidos que cada versão nova do arquivo nacional acrescentou, divididos entre Flávio, Lula e outros; o maior lote é o das 20h04.",
            sombras=sombras,
            legenda=[("Flávio", FLAVIO), ("Lula", LULA), ("Outros", CINZA)],
        ),
        "Altura: válidos acrescentados pela versão. Depois de cada parada vem um lote maior, porque o arquivo represou o que as UFs já mostravam.",
        ident="fig-lotes",
    )
    h += T.noite_conclusao(L)
    conc = {x["uf"]: x for x in L["conclusao_ufs"] if x["uf"] != "ZZ"}
    cortes = [
        "2026-10-04 21:00",
        "2026-10-04 22:00",
        "2026-10-04 23:00",
        "2026-10-05 00:00",
    ]
    tons = ["#e9e4d8", "#c9d8ef", "#8fb0dd", "#4f7fc2", "#192e2b"]

    def cor_c(uf, v):
        if not v:
            return "#d8d4c8"
        return tons[sum(v["gerado_brt"] >= c for c in cortes)]

    h += figura(
        M.mapa_uf(
            conc,
            cor_c,
            lambda uf, v: f"{uf} {hora(v['gerado_brt'])}" if v else uf,
            lambda uf, v: (
                f"{NOME_UF[uf]}: 100% às {hora(v['gerado_brt'], True)}" if v else uf
            ),
            "Hora em que cada UF chegou a 100%",
            "Mapa por UF com a hora de geração da versão que completou 100% das seções de presidente.",
            legenda=[
                ("antes das 21h", tons[0]),
                ("21h a 22h", tons[1]),
                ("22h a 23h", tons[2]),
                ("23h a 0h", tons[3]),
                ("depois de 0h", tons[4]),
            ],
            escuro=lambda uf, v: bool(v) and v["gerado_brt"] >= cortes[2],
        ),
        "Hora de geração da versão com 100% das seções, no relógio de Brasília. A hora impressa pelo TSE no arquivo é a local e não serve para comparar UFs.",
        larga=False,
    )
    dv = L["divergencia_soma_ufs"]["minutos"]
    rows = [dict(zip(dv["colunas"], r, strict=False)) for r in dv["linhas"]]

    def mm(hm: str) -> float:
        hh, m_ = hm.split(":")
        return (int(hh) - 17) * 60 + int(m_)

    xs = [mm(r["hora_brt"]) for r in rows]
    ser = [
        (
            "Arquivo nacional",
            FLAVIO,
            [(mm(r["hora_brt"]), r["nacional_st_visivel"] / 1000) for r in rows],
        ),
        (
            "Soma das 28 UFs",
            INK,
            [(mm(r["hora_brt"]), r["soma_ufs_st_visivel"] / 1000) for r in rows],
        ),
        (
            "Andamento do TSE (-ab)",
            "#8a7a3a",
            [
                (mm(r["hora_brt"]), (r["andamento_br_st_visivel"] or 0) / 1000)
                for r in rows
                if r.get("andamento_br_st_visivel")
            ],
        ),
    ]
    lo = min(xs)
    hi = max(xs)
    ymin = int(min(r["nacional_st_visivel"] for r in rows) / 1000 // 50 * 50)
    ymax3 = int(max(r["soma_ufs_st_visivel"] for r in rows) / 1000 // 50 * 50 + 50)
    h += figura(
        F.grafico_linhas(
            ser,
            (lo, hi),
            (ymin, ymax3),
            [
                (x, f"{17 + int(x) // 60}:{int(x) % 60:02d}")
                for x in range(int(lo), int(hi) + 1, 15)
            ],
            [(v, f"{v} mil") for v in range(ymin, ymax3 + 1, 50)],
            "Seções no arquivo nacional contra a soma das UFs",
            "Três linhas em degrau entre 18h40 e 20h10: o arquivo nacional parado enquanto a soma das UFs e o andamento do TSE avançam.",
            degraus=True,
            margem_dir=190,
        ),
        "Seções totalizadas visíveis a cada minuto, em milhares. A distância vertical entre as linhas é o que o arquivo nacional deixou de mostrar.",
        ident="fig-divergencia",
    )
    h += "</section>"
    return h


# ------------------------------------------------------------------ 03


def r_falha(d: Dados, cap: Capitulo) -> str:
    L = d.get("linha_do_tempo.json")
    N = d.get("noticias_noite.json")
    linhas = versoes(L)
    par = paradas_nacionais(L)
    h = secao(
        cap,
        "A falha do TSE.<br><em>Três camadas, três fontes.</em>",
        "O que o banco da casa prova, o que o aplicativo oficial mostrava e o que o TSE disse. Cada camada com a própria fonte; nenhuma hora fundida com outra.",
    )
    citacao = T.falha_imprensa(N)
    h += '<div class="camadas">'
    h += "<div><h4>1. O banco da casa</h4><p>Hora de geração de cada versão (relógio do TSE) e hora da nossa leitura, com SHA-256. É a camada que mede.</p></div>"
    h += "<div><h4>2. O aplicativo oficial</h4><p>Tela do TSE lida pela casa durante a parada. É o que o eleitor via.</p></div>"
    h += f"<div><h4>3. Imprensa e TSE</h4><p>{len(N)} matérias da noite, com veículo, hora e grau de evidência. É a explicação oficial, como reportada.</p></div>"
    h += "</div>"
    h += "<h3>Camada 1: o que o banco prova</h3>" + p(
        "Os parágrafos desta camada saem das tabelas de versões e de leituras do coletor.",
        "verificado",
    )
    h += T.falha_banco(L, par, linhas)
    linhas_t = [
        [
            f"{hora(t['de_brt'], True)} a {hora(t['ate_brt'], True)}",
            num(t["minutos"], 1),
            f"{num(t['pst_de'], 2)}%",
            f"{num(t['pst_ate'], 2)}%",
            inteiro(t["secoes_no_salto"]),
            inteiro(t["leituras_no_intervalo"]["total"]),
            inteiro(t["leituras_no_intervalo"]["por_classe"].get("nao_modificado", 0)),
        ]
        for t in par
    ]
    h += tabela(
        [
            "Parada do arquivo nacional",
            "Minutos",
            "Seções antes",
            "Seções depois",
            "Seções no salto",
            "Leituras",
            "“Não modificado”",
        ],
        linhas_t,
        "Fonte: linha_do_tempo.json, travamentos.nacional. Horas de geração do TSE, Brasília.",
    )
    h += imagem(
        "b6-pres.png",
        "Telão da casa às 19:14 com a soma das 27 UFs e do exterior e o aviso de que o agregado nacional do TSE estava parado.",
        "Telão da casa às 19:14:15, já somando as UFs (“soma das 27 UFs e exterior”) e avisando, no rodapé, que o agregado nacional do TSE estava parado desde 19:14:08. Print do acompanhamento, não documento oficial.",
    )
    h += "<h3>Camada 2: o que o aplicativo oficial mostrava</h3>"
    h += p(T.falha_app(L, linhas, HORA_APP_OFICIAL)[3:-4], "verificado")
    h += "<h3>Camada 3: o que a imprensa e o TSE disseram</h3>"
    h += citacao
    temas = {"falha/atraso na divulgação", "declaração oficial TSE"}
    rel = [i for i in N if i.get("tema") in temas]
    rel.sort(key=lambda i: (i.get("data", ""), i.get("hora_se_houver", "") or "99"))
    h += tabela(
        ["Hora", "Veículo", "Matéria", "Grau de evidência"],
        [
            [
                escape(i.get("hora_se_houver") or "sem hora"),
                escape(i["veiculo"]),
                f'<a href="{escape(i["url"])}">{escape(i["titulo"])}</a>',
                escape(i.get("degrau_de_evidencia", "")),
            ]
            for i in rel
        ],
        "Fonte: noticias_noite.json. Hora como o veículo carimba; vazia quando a página lida não trazia hora.",
    )
    h += "<h3>O que o TSE não explicou</h3>"
    h += p(
        "Nas matérias lidas não aparecem: a causa do fluxo acima do normal; a origem do tráfego; por que o arquivo "
        "nacional de presidente parou enquanto os de UF avançavam, antes da pausa geral; por que nenhum arquivo de "
        "resultado foi gerado durante a pausa geral, se o problema era só de divulgação; nenhum relatório técnico, perícia "
        "ou prazo de esclarecimento.",
        "verificado",
    )
    h += p(
        "As paradas foram de publicação, não de contagem: os arquivos de UF e o andamento do TSE avançaram enquanto o "
        "nacional ficou parado, e o andamento publicou versão nova durante a pausa geral. Nada nos dados indica "
        "alteração de voto: a ordem dos candidatos nunca se inverteu e a soma das UFs bate com o nacional final. "
        "A causa da pausa não aparece nos dados; só o TSE pode explicá-la.",
        "inferencia",
    )
    longa = max((t["minutos"] for t in par), default=0)
    h += (
        f'<aside class="juizo"><b>Juízo editorial</b>Um sistema que para o arquivo de presidente por {num(longa, 0)} minutos na hora de '
        "maior atenção do país deve um relatório técnico público, com log de geração por arquivo, não só uma frase em "
        "entrevista. A explicação dada é compatível com os dados; não é suficiente para fechar o caso.</aside>"
    )
    h += imagem(
        "live-lotes-final.png",
        "Gráfico do telão com o que cada atualização do arquivo nacional acrescentou desde as 17h, com o pico às 20h04.",
        "Telão da casa ao fim da apuração: válidos e seções que cada atualização do arquivo nacional acrescentou. O pico perto das 20h é o lote represado pela parada. Print do acompanhamento.",
    )
    h += "</section>"
    return h


# ------------------------------------------------------------------ 04


def r_regioes(d: Dados, cap: Capitulo) -> str:
    P = d.get("presidente.json")
    checar(
        d,
        "presidente.json",
        ["regioes", "ufs", "municipios", "capitais", "maiores_variacoes"],
    )
    h = secao(
        cap,
        "Nordeste, Norte<br><em>e Centro-Sul.</em>",
        "2026 contra 2022, mesmo cargo, mesmo turno. Flávio contra Bolsonaro, Lula contra Lula.",
    )
    h += T.regioes(P)
    R = P["regioes"]
    ordem = [
        "Nordeste",
        "Norte",
        "Centro-Sul",
        "Sudeste",
        "Sul",
        "Centro-Oeste",
        "Exterior",
        "Brasil",
    ]
    linhas = []
    for nome in ordem:
        if nome not in R:
            continue
        r = R[nome]
        c = r["comparacao"]
        linhas.append(
            [
                nome,
                f"{num(r['r2026']['pct']['flavio'], 2)}",
                sinal(c["flavio_vs_bolsonaro_1t"]["pp"], 2),
                f"{num(r['r2026']['pct']['lula'], 2)}",
                sinal(c["lula_vs_lula_1t"]["pp"], 2),
                sinal(c["virada_margem_vs_1t_pp"], 2),
                sinal(c["comparecimento_vs_1t_pp"], 2),
            ]
        )
    h += tabela(
        [
            "Região",
            "Flávio %",
            "vs Bolsonaro 1T",
            "Lula %",
            "vs Lula 1T",
            "Virada da margem",
            "Comparecimento",
        ],
        linhas,
        "Pontos percentuais dos válidos contra o 1º turno de 2022. Centro-Sul = Sudeste, Sul e Centro-Oeste.",
    )
    ufs = sorted(
        (u for u in P["ufs"] if u["uf"] != "ZZ"),
        key=lambda u: -u["comparacao"]["virada_margem_vs_1t_pp"],
    )
    h += figura(
        F.divergentes(
            [
                (
                    u["uf"],
                    [
                        u["comparacao"]["flavio_vs_bolsonaro_1t"]["pp"],
                        u["comparacao"]["lula_vs_lula_1t"]["pp"],
                    ],
                )
                for u in ufs
            ],
            [
                ("Flávio menos Bolsonaro (1º turno 2022)", FLAVIO),
                ("Lula 2026 menos Lula (1º turno 2022)", LULA),
            ],
            "Variação por UF contra 2022",
            "Barras divergentes por UF, ordenadas pela virada da margem: em azul a variação de Flávio contra Bolsonaro, em vermelho a de Lula contra Lula.",
            largura=820,
            rotulo_w=60,
            casas=1,
        ),
        "Pontos percentuais dos válidos. Ordem: maior virada da margem para Flávio no topo.",
        ident="fig-swing-uf",
    )
    mun = P["municipios"]
    col = mun["colunas"]
    rows = [dict(zip(col, r, strict=False)) for r in mun["linhas"]]
    grupos = {"Nordeste": [], "Norte": [], "Centro-Sul": []}
    for r in rows:
        if r.get("pct_bolsonaro_2022_1t") is None or r.get("pct_flavio") is None:
            continue
        g = r.get("grupo")
        if g in grupos:
            grupos[g].append((r["pct_bolsonaro_2022_1t"], r["pct_flavio"]))
    n_pts = sum(len(v) for v in grupos.values())
    h += figura(
        F.dispersao(
            [
                ("Nordeste", LULA, grupos["Nordeste"]),
                ("Norte", "#0f7f5f", grupos["Norte"]),
                ("Centro-Sul", FLAVIO, grupos["Centro-Sul"]),
            ],
            (0, 100),
            (0, 100),
            20,
            "Bolsonaro no 1º turno de 2022 (% dos válidos)",
            "Flávio em 2026 (%)",
            "Município a município: Bolsonaro 2022 contra Flávio 2026",
            f"Dispersão de {n_pts} municípios; a maioria fica acima da diagonal, onde Flávio superou Bolsonaro.",
        ),
        f"{inteiro(n_pts)} municípios com arquivo completo e resultado de 2022. Acima da linha tracejada, Flávio fez mais que Bolsonaro no 1º turno de 2022.",
        ident="fig-dispersao",
    )
    valor = {str(r["ibge"]): r.get("virada_margem_pp") for r in rows}
    titulo = {
        str(
            r["ibge"]
        ): f"{nome_proprio(r['nome'])}: virada {sinal(r.get('virada_margem_pp'), 1)} pp"
        for r in rows
    }
    mapas = []
    for uf in ("SP", "MG", "BA", "PE"):
        svg = M.mapa_municipal(
            uf,
            valor,
            titulo,
            NOME_UF[uf],
            f"Mapa municipal de {NOME_UF[uf]} com a virada da margem Flávio menos Lula contra Bolsonaro menos Lula em 2022.",
        )
        if svg:
            mapas.append(svg)
    if mapas:
        h += (
            '<figure id="fig-mapas-mun"><div class="mapas">'
            + "".join(mapas)
            + "</div>"
            + M.legenda_swing_html()
            + "<figcaption>Virada da margem por município: (Flávio menos Lula em 2026) menos (Bolsonaro menos Lula no 1º turno de 2022), em pontos dos válidos.</figcaption></figure>"
        )
    mv = P["maiores_variacoes"].get("virada_margem_pp_10mil", {})

    def linhas_mv(lst):
        return [
            [
                f"{nome_proprio(x['nome'])} ({x['uf']})",
                inteiro(x["eleitores"]),
                num(x["pct_flavio"], 1),
                num(x["pct_lula"], 1),
                sinal(x["virada_margem_pp"], 1),
            ]
            for x in lst
        ]

    cab = ["Município", "Eleitores", "Flávio %", "Lula %", "Virada"]
    if mv:
        h += "<h3>Onde a margem mais andou</h3>"
        h += tabela(
            cab,
            linhas_mv(mv["maiores"][:10]),
            "Dez maiores viradas para Flávio, municípios com 10 mil eleitores ou mais.",
        )
        h += tabela(
            cab,
            linhas_mv(mv["menores"][:10]),
            "Dez maiores viradas para Lula, mesmo piso.",
        )
        h += (
            "<details><summary>As 30 de cada lado</summary>"
            + tabela(cab, linhas_mv(mv["maiores"]))
            + tabela(cab, linhas_mv(mv["menores"]))
            + "</details>"
        )
    caps = sorted(P["capitais"], key=lambda c: -(c.get("swing_flavio_pp") or 0))
    h += (
        "<details><summary>As 27 capitais</summary>"
        + tabela(
            [
                "Capital",
                "Flávio %",
                "vs Bolsonaro 1T",
                "Lula %",
                "vs Lula 1T",
                "Comparecimento",
            ],
            [
                [
                    f"{nome_proprio(c['nome'])} ({c['uf']})",
                    num(c["pct_flavio"], 2),
                    sinal(c["swing_flavio_pp"], 2),
                    num(c["pct_lula"], 2),
                    sinal(c["swing_lula_pp"], 2),
                    sinal(c["delta_comparecimento_pp"], 2),
                ]
                for c in caps
            ],
        )
        + "</details>"
    )
    fx = P["por_faixa_lula_2022"]
    h += tabela(
        [
            "Lula em 2022 (%)",
            "Municípios",
            "Flávio vs Bolsonaro",
            "Lula vs Lula",
            "Comparecimento",
            "Votos de Flávio",
            "Votos de Lula",
        ],
        [
            [
                f["faixa_lula_2022_pct"],
                inteiro(f["municipios"]),
                sinal(f["swing_flavio_pp"], 2),
                sinal(f["swing_lula_pp"], 2),
                sinal(f["delta_comparecimento_pp"], 2),
                sinal(f["delta_votos_flavio"], 0),
                sinal(f["delta_votos_lula"], 0),
            ]
            for f in fx
        ],
        "Municípios agrupados pela fatia de Lula no 1º turno de 2022. Variações em pontos; votos em diferença absoluta.",
    )
    h += CMP.regioes(d)
    h += "</section>"
    return h


# ------------------------------------------------------------------ 05


def r_exterior(d: Dados, cap: Capitulo) -> str:
    E = d.get("exterior.json")
    P = d.get("presidente.json")
    checar(
        d, "exterior.json", ["total", "cidades", "paises", "continentes", "hora_local"]
    )
    h = secao(
        cap,
        "Exterior.<br><em>Lula vence; a votação encolhe.</em>",
        f"{E['total']['cidades']} cidades, {E['total']['paises']} países, comparecimento de {num(E['total']['pct_comparecimento'], 2)}%.",
    )
    h += T.exterior(E, P)
    h += figura(
        M.mapa_mundo(
            E["cidades"],
            "Voto no exterior por cidade",
            "Mapa-múndi com uma bolha por cidade de votação; área proporcional aos válidos; azul onde Flávio lidera, vermelho onde Lula lidera.",
        ),
        "Área da bolha proporcional aos votos válidos da cidade. Fonte: arquivos de cidade do exterior do TSE, versão final.",
        ident="fig-mundo",
    )
    conts = sorted(E["continentes"], key=lambda x: -x["validos"])
    h += figura(
        F.empilhadas(
            [
                (
                    c["continente"],
                    [
                        (c["pct"]["flavio"], FLAVIO, "Flávio"),
                        (c["pct"]["lula"], LULA, "Lula"),
                        (100 - c["pct"]["flavio"] - c["pct"]["lula"], CINZA, "Outros"),
                    ],
                    f"{inteiro(c['validos'])} válidos",
                )
                for c in conts
            ],
            "Voto por continente",
            "Barras empilhadas por continente com a parcela de Flávio, Lula e outros nos válidos.",
            rotulo_w=200,
            direita_w=140,
        ),
        "Parcela dos válidos por continente (divisão M49 da ONU, América em três partes).",
    )
    cid = sorted(E["cidades"], key=lambda c: -(c["validos"] or 0))[:15]
    h += tabela(
        ["Cidade", "País", "Válidos", "Flávio %", "Lula %", "Comparecimento %"],
        [
            [
                nome_proprio(c["nome"]),
                escape(c["pais_nome"]),
                inteiro(c["validos"]),
                num(c["pct"]["flavio"], 1),
                num(c["pct"]["lula"], 1),
                num(c["pct_comparecimento"], 1),
            ]
            for c in cid
        ],
        "As 15 cidades com mais votos válidos.",
    )
    hl = E["hora_local"]
    h += "<details><summary>A hora local impressa pelo TSE</summary>"
    h += f"<p>{escape(hl['nota'])}</p>"
    h += tabela(
        [
            "Cidade",
            "País",
            "Totalização impressa",
            "Primeira versão gerada (Brasília)",
            "Deslocamento aparente (h)",
        ],
        [
            [
                nome_proprio(x["nome"]),
                escape(x["pais_nome"]),
                escape(x["totalizacao_impressa"]),
                escape(x["primeira_versao_totalizada_gerada_brt"]),
                num(x["deslocamento_aparente_h"], 1),
            ]
            for x in hl["mais_adiantadas"]
        ],
    )
    h += "</details></section>"
    return h
