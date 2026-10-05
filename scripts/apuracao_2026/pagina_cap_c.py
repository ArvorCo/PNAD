"""Capítulos 10 a 14 do dossiê da apuração: pesquisas, voto útil, anomalias, 2º turno, auditoria."""

from __future__ import annotations

import math
from datetime import date
from html import escape

from . import pagina_figuras as F
from . import pagina_mapas as M
from . import pagina_texto_b as T
from .pagina_comum import (
    CINZA,
    FLAVIO,
    GOLD,
    INK,
    LULA,
    Capitulo,
    Dados,
    checar,
    figura,
    inteiro,
    nome_proprio,
    num,
    p,
    secao,
    sinal,
    tabela,
)

IMG = "img/apuracao_2026"


def dm(iso: str) -> str:
    return f"{iso[8:10]}/{iso[5:7]}" if iso and len(iso) >= 10 else (iso or "")


# ------------------------------------------------------------------ 10


def r_pesquisas(d: Dados, cap: Capitulo) -> str:
    PV = d.get("pesquisas_vs_urna.json")
    checar(
        d,
        "pesquisas_vs_urna.json",
        [
            "pesquisas",
            "medias",
            "resumo_ultimas_ondas",
            "previsao_casa",
            "referencia_2022",
        ],
    )
    r = PV["resumo_ultimas_ondas"]["publicado"]
    h = secao(
        cap,
        "Pesquisas contra a urna.<br><em>O erro comum voltou.</em>",
        f"{sinal(r['media'], 2)} pontos na diferença Lula menos Flávio, na mesma direção de 2022.",
    )
    h += T.pesquisas(PV)
    pes = sorted(
        PV["pesquisas"],
        key=lambda x: abs(x["publicado"]["diferenca_lula_menos_flavio"]["erro"]),
    )
    linhas = []
    for x in pes:
        rep = x.get("reponderado") or {}
        rep_err = (rep.get("diferenca_lula_menos_flavio") or {}).get("erro")
        marca = " ●" if x.get("ultima_onda_da_casa") else ""
        linhas.append(
            (
                f"{x['instituto']} {dm(x['campo']['fim'])}{marca}",
                x["publicado"]["diferenca_lula_menos_flavio"]["erro"],
                rep_err,
            )
        )
    h += figura(
        F.pontos_setas(
            linhas,
            "Erro de cada pesquisa na diferença Lula menos Flávio",
            "Gráfico de pontos: erro de cada pesquisa na diferença entre Lula e Flávio contra a urna; seta até o valor reponderado por renda.",
            rotulo_w=230,
        ),
        "Erro = pesquisa menos urna, em pontos dos válidos. À direita do zero, a pesquisa superestimou Lula. Ponto escuro: publicado; ponto cinza e seta: a mesma onda com a renda trocada pela PNAD. ● última onda do instituto.",
        ident="fig-pesquisas",
    )
    tab = []
    for x in pes:
        pub = x["publicado"]
        rep = x.get("reponderado") or {}
        rep_err = (rep.get("diferenca_lula_menos_flavio") or {}).get("erro")
        tab.append(
            [
                f"{escape(x['instituto'])}{' ●' if x.get('ultima_onda_da_casa') else ''}",
                f"{dm(x['campo']['inicio'])} a {dm(x['campo']['fim'])}",
                num(pub["validos"].get("flavio"), 2),
                num(pub["validos"].get("lula"), 2),
                sinal(pub["diferenca_lula_menos_flavio"]["erro"], 2),
                sinal(rep_err, 2) if rep_err is not None else "sem renda",
                num(x.get("margem_95_diferenca_aas_pp"), 2),
            ]
        )
    h += tabela(
        [
            "Instituto",
            "Campo",
            "Flávio",
            "Lula",
            "Erro L−F",
            "Erro L−F reponderado",
            "Margem 95% da diferença",
        ],
        tab,
        "Pesquisas nacionais com campo encerrado de 25/09 a 03/10, nos válidos pela regra da casa. Ordem: menor erro absoluto na diferença.",
    )
    m = PV["medias"]
    pc = PV["previsao_casa"]
    ref = PV["referencia_2022"]
    linhas_m = [
        [
            escape(v["nome"]),
            num(v["validos_blocos"]["flavio"], 2),
            num(v["validos_blocos"]["lula"], 2),
            num(v["validos_blocos"]["terceira_via"], 2),
            sinal(v["diferenca_lula_menos_flavio"]["erro"], 2),
        ]
        for v in m.values()
    ]
    cv = pc["central"]["validos"]
    linhas_m.append(
        [
            "Central da casa (04/10)",
            num(cv["flavio"], 2),
            num(cv["lula"], 2),
            num(cv["terceira_via"], 2),
            sinal(pc["central"]["erro_diferenca_lula_menos_flavio"], 2),
        ]
    )
    dl = pc["dlm"]["validos"]
    linhas_m.append(
        [
            "Âncora dinâmica (DLM)",
            num(dl.get("flavio"), 2),
            num(dl.get("lula"), 2),
            num(dl.get("terceira_via"), 2),
            sinal(pc["dlm"]["erro_diferenca_lula_menos_flavio"], 2),
        ]
    )
    linhas_m.append(
        [
            f"Erro comum de 2022 ({ref['n_casas']} casas)",
            "",
            "",
            "",
            sinal(ref["erro_comum_diferenca_lula_menos_bolsonaro"], 2),
        ]
    )
    h += tabela(["Referência", "Flávio", "Lula", "Terceira via", "Erro L−F"], linhas_m)
    reg = pc["regioes"]
    h += tabela(
        [
            "Região",
            "Flávio previsto",
            "Erro Flávio",
            "Lula previsto",
            "Erro Lula",
            "Erro L−F",
        ],
        [
            [
                k.replace("macro_", ""),
                num(v["validos"]["flavio"], 2),
                sinal(v["erro_pp"]["flavio"], 2),
                num(v["validos"]["lula"], 2),
                sinal(v["erro_pp"]["lula"], 2),
                sinal(v["erro_diferenca_lula_menos_flavio"], 2),
            ]
            for k, v in reg.items()
            if k.startswith("macro_")
        ],
        "Central da casa por grande região. O erro está no Centro-Sul; no Nordeste o sinal se inverte.",
    )
    h += T.pesquisas_estaduais(PV)
    h += "</section>"
    return h


# ------------------------------------------------------------------ 11


def r_voto_util(d: Dados, cap: Capitulo) -> str:
    V = d.get("voto_util.json")
    checar(
        d,
        "voto_util.json",
        [
            "terceira_via",
            "terceiros_por_candidato",
            "reserva_nacional",
            "decomposicao.agregados",
        ],
    )
    tv = V["terceira_via"]
    h = secao(
        cap,
        "Voto útil.<br><em>De um lado só.</em>",
        f"Terceira via de {num(tv['media_publicado_todas'], 2)}% nas pesquisas finais para {num(tv['urna_validos'], 2)}% na urna.",
    )
    h += T.voto_util(V)
    a = V["decomposicao"]["agregados"]["ultimas_ondas_publicado"]["nexus_renormalizada"]
    h += figura(
        F.cascata(
            [
                (
                    "Erro das pesquisas (última onda)",
                    a["erro_diferenca_lula_menos_flavio_pp"],
                    "total",
                ),
                (
                    "Consolidação da terceira via (matriz Nexus)",
                    -a["explicado_diferenca_pp"],
                    "delta",
                ),
                (
                    "Deslocamento entre os finalistas",
                    -a["residuo_diferenca_pp"],
                    "delta",
                ),
                ("Urna", 0.0, "total"),
            ],
            "Decomposição do erro na diferença Lula menos Flávio",
            "Cascata: o erro médio das pesquisas na diferença, a parte explicada pela consolidação da terceira via e o resíduo entre os finalistas, até zero na urna.",
        ),
        "Pontos dos válidos. Barras azuis andam para Flávio. A divisão entre consolidação e deslocamento depende da matriz de transferência da Nexus (18 a 20/09, p. 79) e é estimativa, não medição.",
        larga=False,
        ident="fig-cascata",
    )
    tc = V["terceiros_por_candidato"]
    mv, uv = tc["publicado"]["media_validos"], tc["urna_validos"]
    nomes = {
        "renan_santos": "Renan Santos",
        "caiado": "Ronaldo Caiado",
        "cury": "Augusto Cury",
        "zema": "Romeu Zema",
        "demais": "Demais",
    }
    h += tabela(
        [
            "Candidatura",
            "Média das últimas ondas",
            "Urna",
            "Queda (pp)",
            "Queda relativa",
        ],
        [
            [
                nomes[k],
                num(mv[k], 2),
                num(uv.get(k), 2),
                sinal(-tc["publicado"]["queda_pp"][k], 2),
                f"{num(100 * tc['publicado']['queda_relativa'][k], 0)}%",
            ]
            for k in nomes
            if k in mv
        ],
        "Terceira via nas pesquisas finais e na urna, em pontos dos válidos.",
    )
    serie = tv.get("serie_agregador_7d_validos") or []
    if serie:
        d0 = date.fromisoformat(serie[0]["data"])
        pts_p = [
            ((date.fromisoformat(x["data"]) - d0).days, x["publicado"])
            for x in serie
            if x.get("publicado") is not None
        ]
        pts_a = [
            ((date.fromisoformat(x["data"]) - d0).days, x["ajustado"])
            for x in serie
            if x.get("ajustado") is not None
        ]
        fim = max(t for t, _ in pts_p)
        urna = [(fim + 1, tv["urna_validos"])]
        ymax = math.ceil(max(v for _, v in pts_p) / 5) * 5
        ticks = [
            (t, dm((d0.fromordinal(d0.toordinal() + t)).isoformat()))
            for t in range(0, fim + 2, 7)
        ]
        h += figura(
            F.grafico_linhas(
                [
                    ("Publicado", INK, pts_p),
                    ("Reponderado", CINZA, pts_a),
                    (f"Urna {num(tv['urna_validos'], 2)}%", LULA, urna),
                ],
                (0, fim + 2),
                (0, ymax),
                ticks,
                [(v, f"{v}%") for v in range(0, ymax + 1, 5)],
                "Terceira via na média móvel do agregador",
                "Linha da terceira via em parcela dos válidos na média móvel de 7 dias do agregador da casa, caindo até a véspera, e o ponto da urna abaixo dela.",
                margem_dir=150,
            ),
            escape(tv.get("nota_serie", "")),
        )
    h += "</section>"
    return h


# ------------------------------------------------------------------ 12


def r_anomalias(d: Dados, cap: Capitulo) -> str:
    A = d.get("anomalias.json")
    checar(d, "anomalias.json", ["topo", "resumo", "zonas", "zonas_colunas", "limites"])
    topo = A["topo"]
    h = secao(
        cap,
        "Anomalias por zona.<br><em>Triagem, não acusação.</em>",
        escape(A.get("aviso", "")),
    )
    h += T.anomalias(A)

    def local(t):
        return any(
            "efeito político local" in e for e in t.get("explicacao_provavel", [])
        )

    pontos = [
        {
            "lat": t["lat"],
            "lon": t["lon"],
            "raio": 5.5,
            "cor": GOLD if local(t) else INK,
            "titulo": f"{nome_proprio(t['municipio'])} ({t['uf']}), zona {int(t['zona'])}: escore {num(t['escore'], 1)}",
            "rotulo": f"{nome_proprio(t['municipio'])} ({t['uf']})",
        }
        for t in topo
        if t.get("lat") is not None
    ]
    h += figura(
        M.pontos_brasil(
            pontos,
            f"As {len(topo)} zonas mais atípicas",
            f"Mapa do Brasil com as {len(topo)} zonas de maior escore de atipicidade; dourado para hipótese de política local, escuro para explicação comum.",
            rotulos=10,
            legenda=[
                ("explicação comum provável", INK),
                ("hipótese de política local", GOLD),
            ],
        ),
        "Posição: média dos locais de votação da zona, ponderada pelo eleitorado. Rótulos nas dez primeiras.",
        larga=False,
        ident="fig-anomalias-mapa",
    )
    cols = A["zonas_colunas"]
    zs = [dict(zip(cols, z, strict=False)) for z in A["zonas"]]
    pts = [
        (math.log10(z["eleitorado"]), z["escore"])
        for z in zs
        if z.get("eleitorado") and z.get("escore") is not None
    ]
    h += figura(
        F.dispersao(
            [("Zona eleitoral", INK, pts)],
            (3, 6),
            (0, 100),
            1,
            "Eleitorado da zona (escala logarítmica)",
            "Escore de atipicidade",
            "Escore contra tamanho da zona",
            f"Dispersão de {len(pts)} zonas: escore de atipicidade contra o eleitorado; os escores mais altos se concentram nas zonas pequenas.",
            diagonal=False,
            raio=1.6,
            fmt_x=lambda t: {3: "1 mil", 4: "10 mil", 5: "100 mil", 6: "1 mi"}.get(
                round(t), ""
            ),
            passo_y=20,
        ),
        "Cada ponto é uma zona. Zona pequena tem variância maior; o ajuste de tamanho reduz, mas não elimina, o peso delas no topo.",
        ident="fig-anomalias-dispersao",
    )
    h += tabela(
        ["#", "Zona", "Escore", "Seções", "Flávio × Lula", "Explicação provável"],
        [
            [
                t["posicao"],
                f"{nome_proprio(t['municipio'])} ({t['uf']}), zona {int(t['zona'])}",
                num(t["escore"], 1),
                t["secoes"],
                f"{num(t['flavio_pct'], 1)} × {num(t['lula_pct'], 1)}",
                escape("; ".join(t.get("explicacao_provavel", []))),
            ]
            for t in topo[:25]
        ],
        "As 25 zonas de maior escore. Escore é posição relativa no país, não probabilidade de irregularidade.",
    )
    tard = A.get("topo_tardias", [])
    if tard:
        h += (
            "<details><summary>As zonas que fecharam por último</summary>"
            + tabela(
                [
                    "Zona",
                    "Conclusão (Brasília)",
                    "Min. após a mediana da UF",
                    "Seções",
                    "Flávio × Lula",
                    "Lula 1º t. 2022",
                ],
                [
                    [
                        f"{nome_proprio(t['municipio'])} ({t['uf']}), zona {int(t['zona'])}",
                        escape(t.get("conclusao_brasilia", "")),
                        num(t.get("atraso_vs_mediana_uf_min"), 0),
                        t["secoes"],
                        f"{num(t['flavio_pct'], 1)} × {num(t['lula_pct'], 1)}",
                        num(t.get("lula_22_1t_pct"), 1),
                    ]
                    for t in tard
                ],
            )
            + "</details>"
        )
    C = d.get("contexto_seguranca.json")
    if C:
        itens = [i for i in C["itens"] if i.get("degrau") == "documento_oficial"]
        cidades = {(t["uf"], t["municipio"]) for t in topo}
        ligados = [
            (t, c)
            for t in topo
            for c in t.get("contexto", [])
            if (t["uf"], t["municipio"]) in cidades
        ]
        h += "<h3>Contexto do dia</h3>"
        h += p(
            f"A casa reuniu {len(C['itens'])} registros sobre segurança, logística e fiscalização no dia da eleição. "
            f"{len(itens)} são documento oficial; os demais, imprensa ou relato. A tabela traz os documentos oficiais; os "
            "registros de imprensa ligados ao município de uma zona do topo vêm em seguida.",
            "verificado",
        )
        h += tabela(
            ["Órgão", "Registro", "Tema"],
            [
                [
                    escape(i["veiculo"]),
                    f'<a href="{escape(i["url"])}">{escape(i["titulo"])}</a>',
                    escape(i["tema"].replace("_", " ")),
                ]
                for i in itens
            ],
            "Documentos oficiais do contexto_seguranca.json.",
        )
        if ligados:
            h += "<details><summary>Registros de imprensa no município de uma zona do topo</summary><ul>"
            vistos = set()
            for t, c in ligados:
                if c["url"] in vistos:
                    continue
                vistos.add(c["url"])
                h += (
                    f"<li>{nome_proprio(t['municipio'])} ({t['uf']}): <a href=\"{escape(c['url'])}\">{escape(c['titulo'])}</a> "
                    f"({escape(c.get('veiculo', ''))})</li>"
                )
            h += "</ul></details>"
    h += (
        "<h3>Limites</h3><ul>"
        + "".join(f"<li>{escape(x)}</li>" for x in A["limites"])
        + "</ul>"
    )
    h += "</section>"
    return h


# ------------------------------------------------------------------ 13


def r_segundo_turno(d: Dados, cap: Capitulo) -> str:
    E = d.get("estrategia_2t.json")
    checar(
        d,
        "estrategia_2t.json",
        [
            "aritmetica.projecoes",
            "aritmetica.equilibrio",
            "geografia.estoque",
            "movimentos",
            "riscos",
        ],
    )
    h = secao(
        cap,
        "O caminho do 2º turno.<br><em>Juízo editorial declarado.</em>",
        "A casa tem lado: o projeto é a vitória de Flávio. O método não tem lado: cada movimento sai com número e fonte, e o achado contrário sai com o mesmo peso.",
    )
    h += T.segundo_turno(E)
    rot = {
        "fica_fora": "só o medido",
        "proporcional": "não escolha na proporção da linha",
        "meio_a_meio": "não escolha meio a meio",
    }
    h += tabela(
        ["Matriz", "Hipótese", "Flávio %", "Lula %", "Margem (votos)", "Margem (pp)"],
        [
            [
                x["matriz"].capitalize(),
                rot.get(x["hipotese"], x["hipotese"]),
                num(x["flavio_pct"], 2),
                num(x["lula_pct"], 2),
                sinal(x["margem_votos"], 0),
                sinal(x["margem_pp"], 2),
            ]
            for x in E["aritmetica"]["projecoes"]
        ],
        "Transferência da terceira via com as bases do 1º turno fixas. Inferência sobre medição publicada; não é previsão.",
    )
    top = E["geografia"]["estoque"]["top_ufs"]
    h += figura(
        F.barras_h(
            [
                {
                    "rotulo": x["uf"],
                    "valor": x["estoque_flavio"] / 1000,
                    "cor": FLAVIO,
                    "texto": f"{num(x['estoque_flavio'] / 1000, 0)} mil",
                }
                for x in top
            ],
            "Estoque de 2022 que Flávio ainda não alcançou",
            "Barras com o estoque de votos de Bolsonaro no 2º turno de 2022 ainda não alcançado por Flávio, nas dez maiores UFs.",
            largura=680,
            rotulo_w=60,
            passo=28,
        ),
        escape(E["geografia"].get("metodo_estoque", "")),
        larga=False,
    )
    mov = sorted(E["movimentos"], key=lambda m: m.get("ordem", 99))
    h += "<h3>Dez movimentos, do maior para o menor em votos esperados</h3>"
    h += (
        '<aside class="juizo"><b>Juízo editorial</b>A ordem é da casa. O número de cada movimento sai da regra escrita '
        "ao lado, sobre medição publicada ou analogia declarada; nenhum é previsão. Os movimentos não se somam: o eleitor "
        "de Renan em São Paulo é o mesmo que a agenda com Tarcísio procura.</aside>"
    )
    h += figura(
        F.barras_h(
            [
                {
                    "rotulo": f"{m['ordem']}. {m['titulo']}",
                    "valor": m["votos_esperados"] / 1000,
                    "cor": FLAVIO,
                    "texto": f"{num(m['votos_esperados'] / 1000, 0)} mil",
                }
                for m in mov
            ],
            "Votos esperados por movimento",
            "Barras horizontais com o saldo esperado em votos de cada um dos dez movimentos de campanha.",
            largura=960,
            rotulo_w=440,
            passo=30,
        ),
        "Saldo esperado para Flávio, em milhares de votos, pela regra de cada movimento.",
    )
    h += tabela(
        ["Movimento", "Regra", "Natureza"],
        [
            [
                escape(m["titulo"]),
                escape(m.get("regra", "")),
                escape(m.get("rotulo", "")),
            ]
            for m in mov
        ],
    )
    ri = E["riscos"]
    h += "<h3>Riscos e achados contrários</h3>"
    pu = ri.get("piores_ufs_votos_contra_2t_2022", [])
    if pu:
        h += p(
            "Onde Flávio mais fica abaixo de Bolsonaro no 2º turno de 2022, em votos: "
            + T.lista(
                [
                    f"{x['uf']} {sinal(x['flavio_menos_bolsonaro_2t_votos'], 0)}"
                    for x in pu
                ]
            )
            + ".",
            "verificado",
        )
    gd = ri.get("governador_direita_eleito_flavio_perdeu", [])
    if gd:
        h += p(
            "Governador de direita ou centro-direita eleito onde Flávio perdeu: "
            + T.lista(
                [
                    f"{x['uf']}, {nome_proprio(x['governador'])} ({escape(x['partido'])}) com {num(x['governador_pct'], 2)}%, e Lula {num(x['lula_pct'], 2)} × Flávio {num(x['flavio_pct'], 2)}"
                    for x in gd
                ]
            )
            + ". O eleitor desses governadores não seguiu o campo na eleição presidencial.",
            "verificado",
        )
    mg = ri.get("municipios_grandes_abaixo_de_bolsonaro_1t_pp", [])
    if mg:
        h += p(
            "Municípios com mais de "
            + inteiro(ri.get("municipio_grande_minimo_validos"))
            + " válidos onde Flávio ficou abaixo do 1º turno de Bolsonaro: "
            + T.lista(
                [
                    f"{nome_proprio(x['municipio'])} ({x['uf']}) {sinal(x['diferenca_pp'], 2)}"
                    for x in mg
                ]
            )
            + ".",
            "verificado",
        )
    h += "</section>"
    return h


# ------------------------------------------------------------------ 14


def r_auditoria(d: Dados, cap: Capitulo) -> str:
    P = d.get("presidente.json")
    L = d.get("linha_do_tempo.json")
    h = secao(
        cap,
        "Auditoria do próprio<br><em>acompanhamento.</em>",
        "O que o coletor da casa é, o que ele guardou e onde ele errou ao vivo.",
    )
    h += T.auditoria(P, L)
    lat = L["latencia"]["por_hora"]
    horas = sorted({x["hora_brt"] for x in lat})
    idx = {hh: i for i, hh in enumerate(horas)}
    grupos = [
        ("Nacional", "presidente_br", FLAVIO),
        ("UF", "presidente_uf", INK),
        ("Município", "presidente_mu", GOLD),
    ]
    series = [
        (nome, cor, [(idx[x["hora_brt"]], x["p50_s"]) for x in lat if x["grupo"] == g])
        for nome, g, cor in grupos
    ]
    ymax = max((v for _, _, s in series for _, v in s), default=60)
    ymax = int(math.ceil(ymax / 60) * 60)
    h += figura(
        F.grafico_linhas(
            series,
            (0, max(len(horas) - 1, 1)),
            (0, ymax),
            [(i, hh[-3:]) for i, hh in enumerate(horas) if i % 2 == 0],
            [(v, f"{v} s") for v in range(0, ymax + 1, max(60, ymax // 4 // 60 * 60))],
            "Latência mediana por hora",
            "Linhas com a mediana, por hora, dos segundos entre a geração do arquivo no TSE e a leitura pela casa, nos níveis nacional, UF e município.",
            margem_dir=110,
        ),
        escape(L["latencia"]["nota"]),
    )
    erros = [
        "Ao vivo dissemos que os arquivos municipais seguiam atualizando durante a parada. Os dados mostram que nenhum arquivo de resultado foi gerado entre o início e o fim da pausa geral.",
        "A regra do coletor para cópia antiga comparava o contador de versão do TSE, que não cresce dentro do arquivo. A página usa a hora de geração.",
        "A hora de 100% de algumas UFs saiu atrasada no telão pela mesma regra; as horas desta página são as da hora de geração.",
    ]
    h += (
        "<h3>Onde o acompanhamento errou ao vivo</h3><ul>"
        + "".join(f"<li>{e}</li>" for e in erros)
        + "</ul>"
    )
    galeria = [
        (
            "live-mov.png",
            "Telão: movimento da apuração às 18h07",
            "Movimento dos válidos a cada leitura, das 17h às 18h, e os seis maiores eleitorados.",
        ),
        (
            "i1-mun-zonas.png",
            "Telão: São Paulo por zona eleitoral",
            "Município de São Paulo por zona, área proporcional ao eleitorado, às 18h12.",
        ),
        (
            "live-est-pr.png",
            "Telão: deputados estaduais do Paraná",
            "Deputados estaduais do Paraná em apuração, com votos por campo e partido.",
        ),
        (
            "f4-exterior-dados.png",
            "Telão: voto no exterior",
            "Tela do exterior no início da divulgação, com a hora de totalização em relógio local.",
        ),
        (
            "i1-diretor.png",
            "Painel de direção do telão",
            "Painel de direção: telas, estados e roteiro do telão.",
        ),
        (
            "f3b-sen.png",
            "Telão: Senado em modo ensaio",
            "Modo ensaio, com arquivos de teste do TSE: os números não são da eleição.",
        ),
    ]
    h += '<div class="galeria">'
    for arq, alt, leg in galeria:
        alt_px = 1125 if arq == "i1-diretor.png" else 900
        h += (
            f'<figure><img src="{IMG}/{arq}" alt="{escape(alt)}" loading="lazy" width="1600" height="{alt_px}">'
            f"<figcaption>{escape(leg)} Print do acompanhamento.</figcaption></figure>"
        )
    h += "</div></section>"
    return h
