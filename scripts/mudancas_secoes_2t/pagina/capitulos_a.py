"""Capítulos 1 a 5: números públicos, o que mudou, distâncias, motivos e clima."""

from __future__ import annotations

from . import figuras as fg
from . import motivos as mt
from .contexto import NOME_UF, Contexto
from .tabelas import (
    caixa,
    contra,
    detalhes,
    estatisticas,
    figura,
    limite,
    link,
    lista,
    nota,
    secao,
    tabela,
)
from .util import (
    COR_CATEGORIA,
    CORES,
    data_br,
    dec,
    esc,
    ic,
    inteiro,
    pct,
    pp,
    sinal,
    titulo_pt,
)

EXPLICA_CATEGORIA = {
    "A": "O 1º turno foi em prédio provisório. No 2º, a seção volta ao prédio original.",
    "B": "A seção votou no prédio original no 1º turno e passa para um prédio provisório.",
    "C": "A seção troca um prédio provisório por outro.",
    "X": "O número do local original mudou.",
    "D": "Mesmo número de local, mas nome e endereço são outros: é outro prédio.",
    "E": "Mesmo número e nome, endereço diferente. Conta só quando a rua é outra.",
    "F": "Só o nome do prédio mudou. O eleitor vai ao mesmo prédio.",
    "G": "Nome e endereço iguais, coordenada do mapa a mais de 300 m. Correção de cadastro.",
    "H": "Nome e endereço iguais, coordenada moveu até 300 m.",
    "Z": "Nada mudou.",
}


def _ponto(rotulo: str, med: dict, cor: str) -> dict:
    return {
        "rotulo": rotulo,
        "v": med["valor"],
        "lo": med["ic95"][0],
        "hi": med["ic95"][1],
        "cor": cor,
        "txt": f"{inteiro(med['valor'])} m",
    }


def _metros(x) -> str:
    return "sem distância" if x is None else f"{inteiro(x)} m"


def _nome_uf(u: str) -> str:
    return NOME_UF.get(u, u)


def cap1_numeros(c: Contexto) -> str:
    d = c.d
    cp = d["confronto_publico"]
    por_id = {n["id"]: n for n in cp["numeros_publicos"]}
    ordem = [
        "tse_agencia_brasil",
        "coligacao_peticao",
        "forum_exportacao",
        "painel_tse",
    ]
    nomes = {
        "tse_agencia_brasil": "TSE, levantamento de 16/10",
        "coligacao_peticao": "Petição da coligação, 17/10",
        "forum_exportacao": "Exportação do TSE, 18/10 às 11h27",
        "painel_tse": "Painel do TSE, 18/10 às 20h27",
    }
    linhas = []
    for i in ordem:
        n = por_id[i]
        linhas.append(
            {
                "rotulo": nomes[i],
                "barras": [
                    {"v": n["secoes"]["publico"], "cor": CORES["tinta"]},
                    {"v": n["secoes"]["nosso"], "cor": CORES["verde_texto"]},
                ],
            }
        )
    linhas.append(
        {
            "rotulo": "Mudança real de prédio (regra deste laudo)",
            "barras": [{"v": c.secoes_real(), "cor": CORES["dourado"]}],
        }
    )
    svg = fg.barras_h(
        "Seções alteradas: números públicos e recortes do cadastro",
        "Barras de seções. Para cada número público, o recorte do cadastro de 18/10 que mais se aproxima, e por fim a mudança real de prédio.",
        linhas,
        legenda=[
            ("Número público", CORES["tinta"]),
            ("Recorte do cadastro mais próximo", CORES["verde_texto"]),
            ("Mudança real", CORES["dourado"]),
        ],
    )
    rows = []
    for i in ordem:
        n = por_id[i]
        ele_p = n["eleitores"]["publico"] if n["eleitores"] else None
        ele_n = n["eleitores"]["nosso"] if n["eleitores"] else None
        rows.append(
            [
                esc(n["fonte"]) + f'<br><small>{esc(n["carimbo"])}</small>',
                (inteiro(n["secoes"]["publico"]), n["secoes"]["publico"]),
                inteiro(ele_p) if ele_p is not None else "não informado",
                esc(n["descricao_hipotese"]),
                inteiro(n["secoes"]["nosso"]),
                (
                    pct(n["secoes"]["diferenca_pct"])
                    if n["secoes"]["diferenca_pct"] is not None
                    else ""
                ),
                inteiro(ele_n) if ele_n is not None else "",
                "<br>".join(esc(x) for x in n["o_que_nao_explica"]),
            ]
        )
    t_pub = tabela(
        [
            "Número público",
            "Seções",
            "Eleitores",
            "Recorte do cadastro mais próximo",
            "Nossas seções",
            "Diferença",
            "Nossos eleitores",
            "O que a hipótese não explica",
        ],
        rows,
        numericas=(1, 2, 4, 5, 6),
        rotulo="Números públicos contra recortes do cadastro",
        largura=980,
    )
    hip = cp["hipoteses"]
    ordem_h = sorted(hip, key=lambda k: -hip[k]["secoes"])
    t_hip = tabela(
        ["Recorte declarado antes da comparação", "Seções", "Eleitores"],
        [
            [
                esc(hip[k]["descricao"]),
                inteiro(hip[k]["secoes"]),
                inteiro(hip[k]["eleitores"]),
            ]
            for k in ordem_h
        ],
        numericas=(1, 2),
        rotulo="Sete recortes do cadastro",
    )
    sec_total = d["resumo"]["secoes_total"]
    corpo = (
        f"<p>Sobre o cadastro oficial de locais de votação de 18/10, a regra deste laudo encontra <b>{inteiro(c.secoes_real())} seções</b> e <b>{inteiro(c.mr['eleitores'])} eleitores</b> que mudam de prédio entre os turnos. Cada número público corresponde a um recorte diferente. Nenhum fecha com o outro.</p>"
        + figura(
            svg,
            "Fonte: cadastro do TSE de 18/10, painel do TSE e notícias; conta do laudo.",
        )
        + t_pub
        + caixa(
            "O painel de 18/10 contradiz o número de 16/10",
            f'O tribunal divulgou {inteiro(por_id["tse_agencia_brasil"]["secoes"]["publico"])} seções em 16/10 e o painel oficial, atualizado em 18/10, lista {inteiro(por_id["painel_tse"]["secoes"]["publico"])}. Mesma instituição, dois carimbos de hora, números diferentes. Não sabemos qual metodologia produziu cada um.',
        )
        + f"<p>A hipótese para a coligação é a mais próxima: {inteiro(cp['eleitores_fora_do_original_2t_contra_coligacao']['nosso'])} eleitores nas seções que no 2º turno votam fora do local original, contra {inteiro(cp['eleitores_fora_do_original_2t_contra_coligacao']['publico'])} no relatório, diferença de {sinal(cp['eleitores_fora_do_original_2t_contra_coligacao']['diferenca_pct'])}%. As seções divergem. Se a hipótese vale, o relatório contou seções em local provisório, inclusive as que já estavam assim no 1º turno, e não mudanças entre turnos. É hipótese, não afirmação.</p>"
        + detalhes("Os sete recortes testados", t_hip + nota(esc(cp["regra"])))
        + contra(
            "O que contraria a leitura de que algo sumiu",
            f"O TSE afirma que o número de seções se mantém em 499.248 no 2º turno (Fato ou Boato, 16/10). O cadastro confere: {inteiro(sec_total)} linhas por turno, 499.248 principais, nenhuma seção falta de um lado.",
        )
        + limite(
            "Reconciliação é hipótese de proximidade, não prova de método. Nenhum dos quatro números traz a regra de contagem. O cadastro de 18/10 ainda pode mudar até 25/10."
        )
    )
    return secao(
        1,
        "numeros",
        "Quatro números públicos.<br><em>Quatro tamanhos.</em>",
        f"{inteiro(por_id['tse_agencia_brasil']['secoes']['publico'])}, {inteiro(por_id['coligacao_peticao']['secoes']['publico'])}, {inteiro(por_id['forum_exportacao']['secoes']['publico'])} e {inteiro(por_id['painel_tse']['secoes']['publico'])} seções: nenhum bate com o outro, nem com o cadastro.",
        corpo,
    )


def cap2_mudou(c: Contexto) -> str:
    d = c.d
    r = d["resumo"]
    mr = c.mr
    cad = r["por_categoria_cadastro"]
    nomes = d["regras"]["nomes"]
    real = mr["por_categoria"]
    rows = []
    for k in ("A", "B", "C", "D", "E", "F", "G", "H", "Z"):
        rr = real.get(k)
        rows.append(
            [
                f"<b>{k}</b>",
                esc(nomes[k]) + f"<br><small>{esc(EXPLICA_CATEGORIA[k])}</small>",
                inteiro(cad[k]["secoes"]),
                inteiro(cad[k]["eleitores"]),
                inteiro(rr["secoes"]) if rr else "0",
                inteiro(rr["eleitores"]) if rr else "0",
            ]
        )
    t_cat = tabela(
        [
            "Cat.",
            "O que significa",
            "Seções no cadastro",
            "Eleitores no cadastro",
            "Seções com mudança real",
            "Eleitores com mudança real",
        ],
        rows,
        numericas=(2, 3, 4, 5),
        rotulo="Categorias A a Z",
        largura=720,
    )
    fo = r["fora_do_original"]
    cp = d["confronto_painel"]
    n_novas = c.novas_secoes()
    # gráfico por UF
    acc = c.por_uf_categoria()
    ordem = sorted(acc, key=lambda u: -sum(acc[u].values()))[:15]
    nomes_c = {
        "A": "A: retorno ao original",
        "B": "B: nova realocação",
        "C": "C: de provisório para provisório",
        "D": "D: mesmo número, outro prédio",
        "E": "E: mesmo número, outra rua",
    }
    cores_c = {k: COR_CATEGORIA[k] for k in nomes_c}
    svg = fg.empilhado(
        "Seções com mudança real por UF e categoria",
        "Barras empilhadas das quinze UFs com mais seções em mudança real.",
        [{"rotulo": _nome_uf(u), "segs": dict(acc[u])} for u in ordem],
        cores_c,
        nomes_c,
    )
    linhas_uf = []
    for u in sorted(acc, key=lambda u: -sum(acc[u].values())):
        info = c.uf_info(u)
        linhas_uf.append(
            [
                _nome_uf(u),
                inteiro(sum(acc[u].values())),
                inteiro(info["mudanca_real"]["eleitores"]),
                *[inteiro(acc[u].get(k, 0)) for k in ("A", "B", "C", "D", "E")],
                inteiro(info["fora_do_original_2t"]),
                inteiro(info["painel_tse_secoes"]),
            ]
        )
    t_uf = tabela(
        [
            "UF",
            "Seções",
            "Eleitores",
            "A",
            "B",
            "C",
            "D",
            "E",
            "Fora do original no 2º turno",
            "Seções no painel do TSE",
        ],
        linhas_uf,
        ordenavel=True,
        numericas=tuple(range(1, 10)),
        rotulo="Mudança real por UF",
        largura=760,
    )
    so_painel_pi = cp["so_painel_por_uf"].get("PI", 0)
    corpo = (
        estatisticas(
            [
                (
                    inteiro(real["A"]["secoes"]),
                    "seções voltam ao prédio original (categoria A)",
                ),
                (inteiro(n_novas), "seções em novas realocações (B, C, D e E)"),
                (
                    inteiro(fo["secoes_2t"]),
                    f"seções seguem fora do original em 25/10 ({inteiro(fo['eleitores_2t'])} eleitores)",
                ),
            ]
        )
        + "<p>Comparamos, seção a seção, a linha do cadastro de 02/10 (1º turno) com a de 18/10 (2º turno). Cada seção cai numa só categoria. Só vira <b>mudança real</b> o que o eleitor sente: outro prédio.</p>"
        + t_cat
        + nota(esc(d["regras"]["categorias"]["mudanca_real"]))
        + f"<p>Seguir fora do original não é mudar entre turnos. No 1º turno, {inteiro(fo['secoes_1t'])} seções ({inteiro(fo['eleitores_1t'])} eleitores) já votavam em local diferente do original. No 2º, são {inteiro(fo['secoes_2t'])} ({inteiro(fo['eleitores_2t'])} eleitores). A maioria fica onde estava.</p>"
        + figura(
            svg,
            "Fonte: cadastro do TSE de 02/10 e 18/10, classificação do laudo. Quinze UFs com mais seções.",
        )
        + detalhes("Tabela completa por UF", t_uf)
        + f"<h3>O painel do TSE contra o arquivo de locais</h3><p>O painel e o arquivo trazem o mesmo carimbo de hora (18/10, 20h27). As listas coincidem em {inteiro(cp['ambos'])} seções. Há {inteiro(cp['so_painel'])} só no painel e {inteiro(cp['so_zip'])} só no arquivo. A concordância é de {pct(cp['concordancia_pct'], 2)} sobre a união de {inteiro(cp['uniao'])} seções. Nas que constam dos dois, nomes e eleitorado conferem ({inteiro(cp['ambos_eleitorado_painel'])} eleitores nos dois lados).</p>"
        + lista(
            [
                f"{inteiro(cp['hipotese']['so_painel_final_e_o_original_e_zip_segue_temporario'])} das {inteiro(cp['hipotese']['so_painel_total'])} seções só do painel têm como local final o original do cadastro, enquanto o arquivo as mantém no provisório nos dois turnos. {inteiro(so_painel_pi)} dessas {inteiro(cp['so_painel'])} estão no Piauí.",
                f"{inteiro(cp['hipotese']['so_zip_nova_realocacao'])} das {inteiro(cp['hipotese']['so_zip_total'])} seções só do arquivo são novas realocações que o painel não lista.",
                f"O painel não lista seção que mantém o número do local e muda de prédio (categorias D e E): {inteiro(cp['mesmo_numero_outro_predio']['secoes_d_e_no_arquivo'])} no arquivo, {inteiro(cp['mesmo_numero_outro_predio']['secoes_d_e_com_mudanca_real'])} com mudança real, {inteiro(cp['mesmo_numero_outro_predio']['listadas_no_painel'])} no painel.",
            ]
        )
        + caixa(
            "O caso do Rio de Janeiro",
            "O TRE-RJ confirmou a troca de um local com cinco seções e cerca de 1.800 eleitores na 188ª zona (Rua Muaná para Rua Irapuá). O painel do TSE não a lista, porque o número do local não mudou. O arquivo a classifica como D, mudança real, com 1.880 eleitores. É o controle que usamos para provar que a regra enxerga esse tipo de troca.",
        )
        + nota(esc(cp["rotulo"]))
        + contra(
            "O que contraria a tese da mudança em massa",
            f"Das {inteiro(c.secoes_real())} seções com mudança real, {inteiro(real['A']['secoes'])} ({pct(100 * real['A']['secoes'] / c.secoes_real())}) voltam ao prédio onde a seção sempre votou. A tese de mudança em massa para o 2º turno não descreve a maior parte do que o cadastro registra.",
        )
        + limite(
            "O arquivo de 18/10 e o painel têm o mesmo carimbo e divergem em parte das seções. Não sabemos qual dos dois o TSE tratará como oficial. Classificar não é julgar motivo."
        )
    )
    return secao(
        2,
        "mudou",
        "O que mudou de verdade.<br><em>A maioria é retorno.</em>",
        f"{inteiro(real['A']['secoes'])} das {inteiro(c.secoes_real())} seções voltam ao prédio original. As outras {inteiro(n_novas)} são novas realocações.",
        corpo,
    )


def cap3_distancias(c: Contexto) -> str:
    d = c.d
    dist = d["distancia"]
    fx = dist["mudanca_real"]["faixas"]
    barras = fx[:7]
    outras = fx[7:]
    svg_h = fg.histograma(
        "Distância da mudança, em linha reta",
        "Número de seções por faixa de distância entre o local do 1º turno e o do 2º turno.",
        [(f["faixa"], f["secoes"], CORES["verde_texto"]) for f in barras],
        "seções por faixa de distância (linha reta, só com coordenada confiável)",
    )
    te = dist["teste_hipotese"]
    novas, a, viz, vizn = (
        te["novas_realocacoes"],
        te["categoria_a_no_1t"],
        te["predio_vizinho"],
        te["predio_vizinho_das_novas"],
    )
    m = lambda x: f"{inteiro(x['valor'])} m"  # noqa: E731
    svg_m = fg.pontos_ic(
        "Mediana da distância e intervalo de 95%",
        "Quatro medianas de distância em metros com intervalo de confiança.",
        [
            _ponto("Novas realocações", novas["mediana_m"], CORES["dourado"]),
            _ponto("Categoria A, no 1º turno", a["mediana_m"], CORES["verde_texto"]),
            _ponto("Prédio vizinho (todo o país)", viz["mediana_m"], CORES["cinza"]),
            _ponto(
                "Prédio vizinho das origens das novas",
                vizn["mediana_m"],
                CORES["cinza"],
            ),
        ],
        (0, 700),
        [0, 200, 400, 600],
        lambda v: f"{inteiro(v)} m",
        unidade="metros, mediana com IC 95% por reamostragem de pares de locais",
    )
    dif = te["diferencas_m"]
    t_dif = tabela(
        ["Comparação", "Diferença", "Intervalo de 95%"],
        [
            [
                "Novas realocações menos categoria A",
                f"{sinal(dif['novas_menos_a']['valor'], 0)} m",
                ic(dif["novas_menos_a"]["ic95"], 0),
            ],
            [
                "Novas realocações menos prédio vizinho",
                f"{sinal(dif['novas_menos_vizinho']['valor'], 0)} m",
                ic(dif["novas_menos_vizinho"]["ic95"], 0),
            ],
            [
                "Novas realocações menos prédio vizinho da origem",
                f"{sinal(dif['novas_menos_vizinho_da_origem']['valor'], 0)} m",
                ic(dif["novas_menos_vizinho_da_origem"]["ic95"], 0),
            ],
        ],
        numericas=(1,),
        rotulo="Diferenças de distância",
    )
    pc = dist["por_categoria"]
    rot_cat = {
        "A": "A: retorno ao original",
        "B": "B: nova realocação",
        "C": "C: de provisório para provisório",
        "D/E/G": "D e E: mesmo número, outro endereço",
    }
    t_cat = tabela(
        ["Categoria", "Seções com distância", "Mediana", "Percentil 90"],
        [
            [
                rot_cat[k],
                inteiro(pc[k]["secoes_com_distancia"]),
                _metros(pc[k]["mediana_m"]),
                _metros(pc[k]["p90_m"]),
            ]
            for k in pc
        ],
        numericas=(1, 2, 3),
        rotulo="Distância por categoria",
    )
    t_uf = tabela(
        [
            "UF",
            "Seções",
            "Eleitores",
            "Seções com distância",
            "Mediana",
            "Percentil 90",
        ],
        [
            [
                _nome_uf(x["uf"]),
                inteiro(x["secoes"]),
                inteiro(x["eleitores"]),
                inteiro(x["secoes_com_distancia"]),
                _metros(x["mediana_m"]),
                _metros(x["p90_m"]),
            ]
            for x in dist["por_uf"]
        ],
        ordenavel=True,
        numericas=(1, 2, 3, 4, 5),
        rotulo="Distância por UF",
    )
    top = dist["top_20"]
    mesmo_end = [
        x for x in top if x["end_1t"].strip().upper() == x["end_2t"].strip().upper()
    ]
    linhas_top = []
    for x in top:
        suspeita = x in mesmo_end
        rota = link(x["maps_rota"], "Rota") if x.get("maps_rota") else "sem rota"
        linhas_top.append(
            [
                f"{_nome_uf(x['uf'])} · {esc(titulo_pt(x['municipio']))}<br><small>zona {x['zona']}</small>",
                x["categoria"],
                inteiro(len(x["secoes"])),
                inteiro(x["eleitores"]),
                esc(x["nome_1t"]) + f"<br><small>{esc(x['end_1t'])}</small>",
                esc(x["nome_2t"]) + f"<br><small>{esc(x['end_2t'])}</small>",
                f"{dec(x['distancia_m'] / 1000, 1)} km"
                + (
                    "<br><small>mesmo endereço nos dois turnos: coordenada suspeita</small>"
                    if suspeita
                    else ""
                ),
                rota,
            ]
        )
    t_top = tabela(
        [
            "Município",
            "Cat.",
            "Seções",
            "Eleitores",
            "Local do 1º turno",
            "Local do 2º turno",
            "Distância",
            "Rota no Google Maps",
        ],
        linhas_top,
        numericas=(2, 3),
        rotulo="Vinte maiores deslocamentos",
        largura=980,
    )
    semcoord = sum(f["secoes"] for f in outras)
    corpo = (
        estatisticas(
            [
                (
                    f"{inteiro(dist['mudanca_real']['mediana_m'])} m",
                    "distância mediana, em linha reta",
                ),
                (
                    f"{inteiro(dist['mudanca_real']['p90_m'])} m",
                    "percentil 90: nove em cada dez ficam abaixo",
                ),
                (
                    f"{pct(novas['parcela_pct']['acima_1km']['valor'])} / {pct(novas['parcela_pct']['acima_2km']['valor'])}",
                    "das novas realocações acima de 1 km e de 2 km",
                ),
            ]
        )
        + f"<p>A mudança típica é curta: o eleitor vai a um prédio vizinho. A cauda existe. Entre as novas realocações, {pct(novas['parcela_pct']['acima_1km']['valor'])} passam de 1 km ({ic(novas['parcela_pct']['acima_1km']['ic95'], 1, False)}) e {pct(novas['parcela_pct']['acima_2km']['valor'])} passam de 2 km ({ic(novas['parcela_pct']['acima_2km']['ic95'], 1, False)}).</p>"
        + figura(
            svg_h,
            f"Fonte: coordenadas do cadastro do TSE. {inteiro(dist['mudanca_real']['secoes_com_distancia'])} seções com distância confiável; {inteiro(semcoord)} ficam fora (sem coordenada, coordenada repetida ou acima de 50 km).",
        )
        + figura(
            svg_m,
            "Fonte: laudo. Intervalo por reamostragem de pares de locais (as seções de um par têm a mesma distância).",
            700,
        )
        + t_dif
        + contra(
            "A distância das novas realocações não difere da do prédio vizinho",
            f"A mediana das novas ({m(novas['mediana_m'])}) é a da categoria A ({m(a['mediana_m'])}) e a do prédio mais próximo no município ({m(viz['mediana_m'])}). As diferenças têm o zero dentro do intervalo. Pela distância, não há sinal de que as novas realocações levem o eleitor mais longe do que um prédio vizinho levaria. Prédio mais próximo não é prédio disponível: pode não ter sala, acessibilidade ou energia.",
        )
        + "<h3>Por categoria</h3>"
        + t_cat
        + detalhes("Mediana e percentil 90 por UF", t_uf)
        + "<h3>Os vinte maiores deslocamentos</h3>"
        + (
            f"<p>Em {len(mesmo_end)} dos vinte, o endereço de texto é o mesmo nos dois turnos. A distância grande nesses casos indica coordenada errada em um dos cadastros, não deslocamento real. Conferimos pelo link de rota.</p>"
            if mesmo_end
            else ""
        )
        + t_top
        + limite(
            esc(dist["regra"])
            + " Coordenada repetida por três ou mais locais do município é marcador de posição, não posição do prédio."
        )
    )
    return secao(
        3,
        "distancias",
        "A distância típica é a de um prédio vizinho.<br><em>Com uma cauda acima de 1 km.</em>",
        f"Mediana de {inteiro(dist['mudanca_real']['mediana_m'])} m em linha reta, percentil 90 em {inteiro(dist['mudanca_real']['p90_m'])} m.",
        corpo,
    )


def _fonte_nota(n: dict) -> str:
    return f"{link(n['url'], n['veiculo'])}, {esc(data_br(n['data'])) if str(n['data'])[:2] == '20' else esc(n['data'])}"


def cap4_motivos(c: Contexto) -> str:
    mo = c.motivos
    linhas = [
        {
            "rotulo": x["rotulo"],
            "barras": [
                {
                    "v": x["secoes"],
                    "cor": (
                        CORES["tinta"]
                        if x["chave"] == mt.SEM
                        else (
                            COR_CATEGORIA["A"]
                            if x["chave"] != mt.GERAL
                            else CORES["cinza"]
                        )
                    ),
                },
                {
                    "v": x["eleitores"] * mo["secoes_total"] / mo["eleitores_total"],
                    "cor": CORES["linha"],
                    "txt": f"{inteiro(x['eleitores'])} eleitores",
                },
            ],
        }
        for x in mo["linhas"]
    ]
    svg = fg.barras_h(
        "Motivo publicado para cada mudança real",
        "Seções (barra escura ou verde) e eleitores (barra clara) por motivo atribuído ao local. Uma seção pode ter mais de um motivo.",
        linhas,
        legenda=[
            ("Seções", CORES["tinta"]),
            ("Eleitores (mesma proporção do total)", CORES["linha"]),
        ],
        maximo=mo["secoes_total"],
        lw=270,
    )
    sn = mo["sem_nota"]
    com = mo["com_nota"]
    # tabela por UF com a fonte
    notas_uf: dict[str, list[dict]] = {}
    for n in c.tre:
        if n.get("url") and n["uf"] != "BR":
            notas_uf.setdefault(n["uf"], []).append(n)
    linhas_uf = []
    for u in sorted(notas_uf):
        info = c.uf_info(u) if u in c.ufs else None
        for n in notas_uf[u]:
            linhas_uf.append(
                [
                    u,
                    inteiro(info["mudanca_real"]["secoes"]) if info else "",
                    inteiro(info["painel_tse_secoes"]) if info else "",
                    esc(n.get("numero_total_declarado") or "não informado"),
                    "; ".join(esc(x) for x in (n.get("motivos_citados") or []))
                    or "nenhum (nota diz que não houve mudança)",
                    _fonte_nota(n),
                ]
            )
    t_uf = tabela(
        [
            "UF",
            "Seções com mudança real (arquivo)",
            "Seções no painel do TSE",
            "O que a nota declara",
            "Motivos citados na nota",
            "Fonte",
        ],
        linhas_uf,
        numericas=(1, 2),
        rotulo="Notas dos TREs por UF",
        largura=980,
    )
    geral = mt.citado_em_geral(c.tre)
    t_geral = tabela(
        ["Motivo citado em alguma nota", "Notas que o citam"],
        [
            [
                esc(g["rotulo"]),
                ", ".join(
                    ("TSE e imprensa nacional" if u == "BR" else u) for u in g["ufs"]
                ),
            ]
            for g in geral
        ],
        rotulo="Motivos citados em geral",
    )
    sem = mt.ufs_sem_nota(c.tre, c.ufs)
    al, mtu = c.uf_info("AL"), c.uf_info("MT")
    painel_al = c.painel_por_municipio("AL")
    acc_al = c.por_uf_categoria().get("AL", {})
    em = next(
        (
            n
            for n in c.tre
            if n["uf"] == "BR" and "Estado de Minas" in (n.get("veiculo") or "")
        ),
        None,
    )
    corpo = (
        f"<p>Das {inteiro(mo['pares_total'])} trocas de local com mudança real ({inteiro(mo['secoes_total'])} seções), só {inteiro(com['pares'])} casam com alguma nota de TRE ou notícia que cite o local, o município ou a zona: {inteiro(com['secoes'])} seções e {inteiro(com['eleitores'])} eleitores. <b>Sem motivo publicado ficam {inteiro(sn['secoes'])} seções ({pct(100 * sn['secoes'] / mo['secoes_total'])}) e {inteiro(sn['eleitores'])} eleitores.</b> É a maior categoria do gráfico.</p>"
        + figura(
            svg,
            "Fonte: notas dos TREs, matérias e Fato ou Boato do TSE, casadas por local, zona ou município. Classificação por palavras-chave, descrita abaixo.",
            720,
        )
        + f"<p>Dos {inteiro(com['pares'])} pares com nota, {inteiro(mo['especificos']['pares'])} têm motivo próprio do local ({inteiro(mo['especificos']['secoes'])} seções). Os demais só repetem a justificativa geral da nota, sem ligá-la a um prédio. Reforma, calor, falta de espaço, pedido de mesários e acessibilidade aparecem onde há motivo local. Enchente aparece em Uruguaiana (RS).</p>"
        + "<h3>O que as notas dizem, estado a estado</h3>"
        + detalhes(
            "Tabela de notas por UF, com a fonte de cada uma", t_uf, aberto=False
        )
        + "<h3>Motivos citados em geral</h3>"
        + t_geral
        + nota(
            "O motivo geral de uma nota não explica uma seção específica. Aparece aqui para registrar o que o poder público e a imprensa alegam, não para atribuir causa a um local."
        )
        + "<h3>Onde a nota e o arquivo não conversam</h3>"
        + lista(
            [
                f"O TRE-AL disse em 16/10 que os locais permanecem os mesmos. O painel do TSE de 18/10 lista {inteiro(al['painel_tse_secoes'])} seções em Alagoas ({', '.join(f'{titulo_pt(k)} {v}' for k, v in sorted(painel_al.items(), key=lambda kv: -kv[1]))}), e o arquivo registra {inteiro(al['mudanca_real']['secoes'])} com mudança real. {inteiro(acc_al.get('A', 0))} dessas {inteiro(sum(acc_al.values()))} são retorno ao original. A nota é anterior ao cadastro de 18/10; pode haver decisão posterior ou outra leitura de &quot;mesmos locais&quot;.",
                f"O TRE-MT disse em 16/10 que não houve mudança. O painel lista {inteiro(mtu['painel_tse_secoes'])} seções em Mato Grosso, todas em Confresa, e o arquivo registra {inteiro(mtu['mudanca_real']['secoes'])}: uma nova realocação."
                + (
                    f" O TSE cita Confresa como caso de escola com cobertura danificada por chuva, com laudo de 11/10 que recomendava interdição ({link(em['url'], em['veiculo'])})."
                    if em
                    else ""
                ),
                f"{len(sem)} UFs sem nota localizada ({', '.join(sem)}). Busca feita em 19/10 nos sites dos TREs e na imprensa; falha de busca não prova que a nota não existe.",
            ]
        )
        + contra(
            "O que contraria a leitura de que não há motivo",
            "Onde existe motivo publicado, ele é concreto e plausível: reforma de escola, calor e salas pequenas, pedido de mesários e coordenadores, enchente em Uruguaiana, retorno ao prédio original no Rio Grande do Sul e no Rio Grande do Norte. A ausência de nota na maioria das seções não prova que o motivo não existe. Prova que o público não consegue conferi-lo.",
        )
        + limite(
            "O casamento entre nota e seção é por local, zona ou município; só o grau local indica o mesmo prédio. A classificação por palavras-chave lê só o trecho que a nota liga ao local e descarta frases marcadas como gerais. Segurança aparece como motivo no 1º turno do Rio (Agência Brasil, 04/10), não em nota do 2º turno."
        )
    )
    return secao(
        4,
        "motivos",
        "A maior categoria é<br><em>sem motivo publicado.</em>",
        f"Para {pct(100 * sn['secoes'] / mo['secoes_total'], 0)} das seções com mudança real, nenhuma nota pública diz o porquê.",
        corpo,
    )


def cap5_clima(c: Contexto) -> str:
    d = c.d
    cl = d["clima_resumo"]
    o, k = cl["origem_mudanca_real"], cl["controle"]
    dif = cl["origem_mudanca_real_menos_controle_pp"]
    linhas = [
        ("Chuva em 04/10 acima de 20 mm", "chuva_04_10_acima_20mm_pct"),
        (
            "Máximo diário de 05 a 18/10 acima de 20 mm",
            "chuva_max_05a18_acima_20mm_pct",
        ),
        (
            "Máximo diário de 05 a 18/10 acima de 50 mm",
            "chuva_max_05a18_acima_50mm_pct",
        ),
        ("Rajada de 05 a 18/10 acima de 60 km/h", "rajada_acima_60kmh_pct"),
    ]
    svg = fg.barras_h(
        "Chuva e vento nos locais de origem e nos de controle",
        "Parcela dos locais com chuva ou rajada acima do limite, para locais que mudaram e locais de controle.",
        [
            {
                "rotulo": r,
                "barras": [
                    {"v": o[ch], "cor": CORES["dourado"], "txt": pct(o[ch])},
                    {"v": k[ch], "cor": CORES["cinza"], "txt": pct(k[ch])},
                ],
            }
            for r, ch in linhas
        ],
        legenda=[
            (
                f"Origem de mudança real ({inteiro(o['com_dado'])} locais)",
                CORES["dourado"],
            ),
            (f"Controle ({inteiro(k['com_dado'])} locais)", CORES["cinza"]),
        ],
        maximo=40,
    )
    nomes_dif = {
        "chuva_04_10_acima_20mm": "Chuva em 04/10 acima de 20 mm",
        "chuva_max_05a18_acima_20mm": "Máximo diário de 05 a 18/10 acima de 20 mm",
        "chuva_max_05a18_acima_50mm": "Máximo diário de 05 a 18/10 acima de 50 mm",
        "rajada_acima_60kmh": "Rajada acima de 60 km/h",
    }
    t = tabela(
        ["Medida", "Origem menos controle", "Intervalo de 95%"],
        [
            [nomes_dif[k_], pp(dif[k_]["valor"], 1), ic(dif[k_]["ic95"], 1)]
            for k_ in nomes_dif
        ],
        numericas=(1,),
        rotulo="Diferença entre origem e controle",
    )
    sem = cl["origem_mudanca_real_sem_chuva_nem_vento"]
    n_chuva = round(o["chuva_max_05a18_acima_20mm_pct"] / 100 * o["com_dado"])
    conf = next(iter(c.local("MT", "CONFRESA")), None)
    conf_txt = ""
    if conf:
        cm = conf["clima"]
        conf_txt = (
            f"<h3>Confresa (MT), o caso que o TSE citou</h3><p>O TSE e a imprensa citam uma escola de Confresa com cobertura danificada por chuva e ventania em 9 e 10/10 e laudo de 11/10. O arquivo tem um só local de Mato Grosso em mudança real: {esc(conf['nome_1t'])} (zona {conf['zona']}), {inteiro(len(conf['secoes']))} seções e {inteiro(conf['eleitores'])} eleitores, que passam para {esc(conf['nome_2t'])}, a {inteiro(conf['distancia_m'])} m. A reanálise de 9 km registra, na coordenada de origem, {dec(cm['chuva_04_10_mm'], 1)} mm em 04/10, no máximo {dec(cm['chuva_max_05a18_mm'], 1)} mm em um dia de 05 a 18/10 ({data_br(cm['dia_chuva_max'])}) e rajada máxima de {dec(cm['rajada_max_kmh'], 1)} km/h ({data_br(cm['dia_rajada_max'])}). Nada de 9 e 10/10 passa desses valores.</p>"
            "<p>Isso não contradiz o laudo. A reanálise não enxerga a cobertura de uma escola, e uma ventania local pode escapar de uma célula de 9 km. Também não confirma: o TSE não nomeia a escola, e o TRE-MT disse em 16/10 que não houve mudança. Não afirmamos que este é o prédio do laudo.</p>"
        )
    corpo = (
        estatisticas(
            [
                (
                    pp(dif["chuva_max_05a18_acima_20mm"]["valor"], 1),
                    f"parcela com chuva diária acima de 20 mm, origem menos controle ({ic(dif['chuva_max_05a18_acima_20mm']['ic95'], 1)})",
                ),
                (
                    inteiro(sem["quantidade"]),
                    f"locais de origem sem chuva acima de 10 mm nem rajada acima de 50 km/h, de {inteiro(o['com_dado'])}",
                ),
                (
                    f"{inteiro(n_chuva)}",
                    f"locais de origem ({pct(o['chuva_max_05a18_acima_20mm_pct'])}) com algum dia acima de 20 mm",
                ),
            ]
        )
        + f"<p>Comparamos o clima nos {inteiro(o['locais'])} locais de origem das mudanças reais com {inteiro(k['locais'])} locais de controle, sorteados entre os que não mudaram. Janela: 28/09 a 18/10. Fonte: Open-Meteo, reanálise ERA5 (archive-api), na coordenada do 1º turno.</p>"
        + f"<p>Os locais que mudaram tiveram <b>menos</b> chuva forte que os de controle: {pct(o['chuva_max_05a18_acima_20mm_pct'])} contra {pct(k['chuva_max_05a18_acima_20mm_pct'])} com algum dia acima de 20 mm entre 05 e 18/10. Em 04/10, dia do 1º turno, não há diferença ({pp(dif['chuva_04_10_acima_20mm']['valor'], 1)}, {ic(dif['chuva_04_10_acima_20mm']['ic95'], 1)}). Para rajada, também não.</p>"
        + figura(
            svg,
            "Fonte: Open-Meteo (ERA5), coordenadas do cadastro do TSE. Controle: locais sem alteração.",
        )
        + t
        + conf_txt
        + contra(
            "O que o clima justifica",
            f"Chuva forte não é rara nos locais de origem: {pct(o['chuva_max_05a18_acima_20mm_pct'])} tiveram um dia acima de 20 mm e {pct(o['chuva_max_05a18_acima_50mm_pct'])} acima de 50 mm. Os motivos publicados por TREs do Sul e do Nordeste (temporais, enchentes, prédios danificados) são compatíveis com parte dos casos. O que o dado nega é a explicação genérica para a maioria, não cada caso.",
        )
        + limite(
            "Reanálise de 9 km não vê o telhado de uma escola nem um temporal de bairro. A coordenada do cadastro pode estar errada. Controle sorteado não é controle pareado por região. O resultado descreve o conjunto, não um prédio."
        )
    )
    return secao(
        5,
        "clima",
        "O clima não explica<br><em>a maioria.</em>",
        f"Os locais que mudaram tiveram menos chuva forte que os de controle: {pp(dif['chuva_max_05a18_acima_20mm']['valor'], 1)} ({ic(dif['chuva_max_05a18_acima_20mm']['ic95'], 1)}).",
        corpo,
    )
