"""Hero e capítulos 1 a 4: método, chuva e bateria, chuva e abstenção, bateria e abstenção."""

from __future__ import annotations

import math

from . import figs, mapas
from .comum import (
    COR_A,
    COR_B,
    COR_C,
    COR_D,
    caixa,
    com_ic,
    contra,
    estatisticas,
    figura,
    limite,
    lista,
    nota,
    p_fmt,
    parcela,
    razao_ic,
    secao,
    tabela,
)
from .util import (
    GOMEZ_PP_POR_POLEGADA,
    MM_POR_POLEGADA,
    Dados,
    data_br,
    dec,
    hora_br,
    ic,
    inteiro,
    pct,
    pp,
    sinal,
)


def _cap(texto: str) -> str:
    return texto[:1].upper() + texto[1:]


def _forte(dados: Dados) -> dict:
    return next(
        f
        for f in dados.faixas("chuva_votacao", "bateria_votacao")
        if f["faixa"] == "forte"
    )


def _binario(dados: Dados, chave: str = "chuva_votacao") -> dict:
    return dados.d["abstencao_x_chuva"]["binario"][chave]


def _grupo_mais(b: dict, nivel: str) -> dict:
    """Comparação do corte binário: país, dentro da UF e dentro do município."""
    return {
        "pais": b["pais"][1],
        "uf": next(iter(b["dentro_da_uf"]["grupos"].values())),
        "mun": next(iter(b["dentro_do_municipio"]["grupos"].values())),
    }[nivel]


def _reg_abs(dados: Dados, medida: str, expo: str, fe: str) -> dict:
    r = dados.d["abstencao_x_chuva"]["regressoes"][medida][expo][fe]
    return next(iter(r["termos"].values()))


# ------------------------------------------------------------------ hero
def hero(dados: Dados) -> str:
    d = dados.d
    forte = _forte(dados)
    mun = _grupo_mais(_binario(dados), "mun")["abst_vs_ref_pp"]
    return (
        '<section class="hero"><div>'
        f'<p class="eyebrow">2º turno · previsão consultada em {hora_br(d["previsao_25_10"]["gerado_em"])}</p>'
        "<h1>Chuva no domingo.<br><em>Onde olhar, e o que podemos prever.</em></h1>"
        '<p class="deck">Mapa meteorológico para 25/10, abstenção observada no primeiro turno '
        "e um cenário de persistência por município. Tempo ruim merece atenção no deslocamento; "
        "os dados ainda não sustentam converter chuva em faltas adicionais.</p>"
        f'<p class="deck">Cruzamos a chuva de 4 de outubro, célula por célula, com o log e o boletim de '
        f"<b>{inteiro(d['cobertura']['urnas_amostra'])} urnas</b>. Onde choveu forte, mais urnas passaram a operar "
        "com a bateria interna, quase todas junto com outras urnas do mesmo município. A abstenção não acompanha: "
        f"dentro do município, a diferença é de {pp(mun['valor'])} e o intervalo inclui o zero.</p>"
        '<div class="chips">'
        f"<span>{inteiro(d['cobertura']['archive']['celulas'])} células de 0,25°</span>"
        f"<span>{inteiro(round(d['cobertura']['locais_com_clima'], -3))} locais de votação</span>"
        f"<span>previsão de {data_br(d['previsao_25_10']['alvo'])}: "
        f"{dec(dados.previsao_pais()['eleitores']['alto'] / 1e6, 1)} milhões de eleitores em risco alto "
        f"({hora_br(d['previsao_25_10']['gerado_em'])})</span>"
        "<span>histórico: ERA5 · previsão: Open-Meteo Forecast</span></div></div>"
        '<aside class="placar" aria-label="Placar do relatório">'
        '<p class="eyebrow">Bateria na chuva forte</p>'
        f"<b>{dec(forte['razao_vs_ref']['valor'], 2)}×</b>"
        f"<small>razão contra a faixa seca ({ic(forte['razao_vs_ref']['ic95'], 2, False)}). "
        f"{pct(forte['parcela_pct']['valor'], 2)} das urnas, contra "
        f"{pct(dados.faixas('chuva_votacao', 'bateria_votacao')[0]['parcela_pct']['valor'], 2)} sem chuva.</small><hr>"
        '<p class="eyebrow">Abstenção, dentro do município</p>'
        f"<b>{pp(mun['valor'])}</b>"
        f"<small>chuva acima de 5 mm contra até 5 mm ({ic(mun['ic95'])}). Não se separa de zero.</small>"
        "</aside></section>"
    )


def guia(dados: Dados) -> str:
    return (
        '<section class="guia" aria-label="Três caminhos de leitura">'
        '<article><span>Capítulo 2</span><h3><a href="#bateria">Chuva e bateria</a></h3>'
        "<p>A associação existe, mora na queda de energia que atinge várias urnas do município, e não na tomada de uma urna só.</p></article>"
        '<article><span>Capítulo 3</span><h3><a href="#abstencao">Chuva e abstenção</a></h3>'
        "<p>A diferença bruta some quando se compara dentro da UF e dentro do município. Um controle chega a inverter o sinal.</p></article>"
        '<article><span>Capítulo 7</span><h3><a href="#previsao">E o dia 25?</a></h3>'
        "<p>Quem está em área de risco alto, em que estados, e o que a mesa e o fiscal podem registrar.</p></article>"
        "</section>"
    )


# ------------------------------------------------------------------ cap. 1
def cap1_metodo(dados: Dados) -> str:
    d = dados.d
    cob, jan, cp = d["cobertura"], d["janela_votacao"], d["conferencia_pontos"]
    desf = d["bateria_x_chuva"]["desfechos"]
    mapa = mapas.mapa_faixas(dados)
    rot = d["faixas"]["chuva"]
    fusos = "".join(f"<li><b>{k}</b>: {v}</li>" for k, v in jan["local"].items())
    corpo = (
        estatisticas(
            [
                (
                    inteiro(cob["archive"]["celulas"]),
                    "células de 0,25° consultadas, todas com resposta",
                ),
                (
                    inteiro(cob["urnas_amostra"]),
                    f"urnas com clima e boletim, de {inteiro(cob['urnas_brasil'])} no país",
                ),
                (
                    inteiro(cob["locais_com_clima"]),
                    f"locais de votação com coordenada e clima, de {inteiro(cob['locais_brasil'])}",
                ),
            ]
        )
        + "<p>A chuva vem da reanálise ERA5 (Open-Meteo), uma consulta por célula de 0,25 grau, cerca de 28 km de lado. "
        "Cada local herda a chuva da célula onde está. O boletim de urna traz aptos e comparecimento de cada seção; "
        "o log traz os registros de operação com bateria e de reinício. A abstenção de 2022 vem do 2º turno daquele ano, nas seções com o mesmo número.</p>"
        f"<h3>A janela de votação</h3><p>A votação foi das 8h às 17h de Brasília em todo o país. A janela da chuva é "
        f"<b>{jan['regra'].split(' (')[0]}</b>: uma hora de folga de cada lado, a mesma fatia da série horária para todos os estados. "
        "No horário local, essa janela cai em horas diferentes:</p>"
        f"<ul>{fusos}</ul>"
        f"<p class=\"note\">Convenção da série: {jan['convencao']}. Sensibilidade: {jan['estrita']}.</p>"
        + figura(
            mapa,
            f"Chuva acumulada nas horas de votação de 04/10, por célula. Mostra as {inteiro(cob['archive']['celulas'])} células consultadas; "
            f"a análise usa as {inteiro(cob['celulas_na_amostra'])} que têm urna com boletim e clima. "
            "Faixas: " + "; ".join(rot.values()) + ".",
            largura_min=560,
        )
        + "<h3>Os desfechos</h3>"
        + lista(
            [
                f"<b>Bateria durante a votação.</b> {_cap(desf['bateria_votacao'])}",
                f"<b>Simultânea.</b> {_cap(desf['bateria_simultanea'])}",
                f"<b>Isolada.</b> {_cap(desf['bateria_isolada'])}",
            ]
        )
        + "<h3>A célula é boa o bastante?</h3>"
        f"<p>Para {inteiro(cp['pares'])} locais já consultados com coordenada exata no estudo das mudanças de local, "
        f"a chuva do dia na célula tem correlação de <b>{dec(cp['correlacao'], 3)}</b> com a do ponto exato, "
        f"diferença absoluta média de {dec(cp['diferenca_media_absoluta_mm'], 2)} mm (mediana {dec(cp['diferenca_mediana_absoluta_mm'], 2)} mm) "
        f"e mesma faixa de chuva em {pct(cp['mesma_faixa_pct'], 1)} dos casos.</p>"
        + limite(
            "A célula não vê o telhado. Pancada isolada pode não aparecer, e o erro de medida do clima puxa qualquer associação para perto de zero. "
            f"Locais sem coordenada no território ficam fora: {inteiro(dados.urnas_sem_clima())} urnas."
        )
    )
    return secao(
        1,
        "metodo",
        "O que medimos <em>e como</em>",
        "Chuva por célula de 0,25 grau, nas horas em que as urnas estavam abertas, cruzada com o log e o boletim de cada seção. O 2º turno de 2022 serve de base.",
        corpo,
    )


# ------------------------------------------------------------------ cap. 2
def _linha_faixa(f: dict) -> list:
    return [
        f["rotulo"],
        inteiro(f["celulas"]),
        inteiro(f["urnas"]),
        inteiro(f["com_registro"]),
        parcela(f["parcela_pct"]),
        razao_ic(f["razao_vs_ref"]),
    ]


def _linha_reg(rot: str, r: dict, unid: str) -> list:
    return [
        rot,
        unid,
        f"{dec(r['odds_ratio'], 2)}<small>{ic(r['ic95'], 2, False)}</small>",
        p_fmt(r["p"]),
    ]


def cap2_bateria(dados: Dados) -> str:
    d = dados.d
    faixas = dados.faixas("chuva_votacao", "bateria_votacao")
    sim = dados.faixas("chuva_votacao", "bateria_simultanea")
    iso = dados.faixas("chuva_votacao", "bateria_isolada")
    forte, seca = _forte(dados), faixas[0]
    or_chuva = dados.reg_bateria("bateria_votacao", "chuva_votacao_x")
    or_sim = dados.reg_bateria("bateria_simultanea", "chuva_votacao_x")
    or_iso = dados.reg_bateria("bateria_isolada", "chuva_votacao_x")
    or_raj = dados.reg_bateria("bateria_votacao", "rajada_votacao_x")
    rob = d["bateria_x_chuva"]["regressoes"]["robustez_municipio"]["bateria_votacao"][0]
    rm = rob["termos"]["chuva_votacao_x"]
    cores = [COR_D, COR_D, COR_A, COR_B]
    graf_parcela = figs.pontos_ic(
        "Parcela de urnas com bateria durante a votação, por faixa de chuva",
        "Quatro faixas de chuva nas horas de votação. A parcela sobe de cerca de 12% sem chuva ou com chuva fraca para quase 30% com chuva forte, com intervalo largo na faixa forte.",
        [
            {
                "rotulo": f["rotulo"],
                "v": f["parcela_pct"]["valor"],
                "lo": f["parcela_pct"]["ic95"][0],
                "hi": f["parcela_pct"]["ic95"][1],
                "cor": c,
                "txt": f"{dec(f['parcela_pct']['valor'], 1)}% ({dec(f['parcela_pct']['ic95'][0], 1)} a {dec(f['parcela_pct']['ic95'][1], 1)})",
            }
            for f, c in zip(faixas[:4], cores, strict=True)
        ],
        (0, 45),
        [0, 10, 20, 30, 40],
        lambda t: f"{t:g}%",
        lw=210,
        unidade="% das urnas com bateria durante a votação, IC 95%",
    )
    series = [
        ("Qualquer bateria na votação", COR_D),
        ("Simultânea (rede)", COR_A),
        ("Isolada (tomada ou fonte)", COR_B),
    ]
    graf_razao = figs.floresta_log(
        "Razão de bateria contra a faixa seca, por tipo de bateria",
        "Para chuva moderada e forte, a bateria simultânea sobe de 2 a 5 vezes e a bateria isolada cai abaixo de 1.",
        [
            {
                "rotulo": faixas[i]["rotulo"],
                "pontos": [
                    {
                        "v": g[i]["razao_vs_ref"]["valor"],
                        "lo": g[i]["razao_vs_ref"]["ic95"][0],
                        "hi": g[i]["razao_vs_ref"]["ic95"][1],
                    }
                    for g in (faixas, sim, iso)
                ],
            }
            for i in (1, 2, 3)
        ],
        series,
        lambda v: dec(v, 2),
    )
    tab_faixas = tabela(
        [
            "Chuva nas horas de votação",
            "Células",
            "Urnas",
            "Com registro",
            "Parcela",
            "Razão contra a seca",
        ],
        [_linha_faixa(f) for f in faixas],
        numericas=(1, 2, 3),
        rotulo="Bateria durante a votação por faixa de chuva",
        largura=700,
    )
    tab_sim_iso = tabela(
        [
            "Chuva nas horas de votação",
            "Simultânea: parcela",
            "Simultânea: razão",
            "Isolada: parcela",
            "Isolada: razão",
        ],
        [
            [
                s["rotulo"],
                parcela(s["parcela_pct"]),
                razao_ic(s["razao_vs_ref"]),
                parcela(i["parcela_pct"]),
                razao_ic(i["razao_vs_ref"]),
            ]
            for s, i in zip(sim, iso, strict=True)
        ],
        rotulo="Bateria simultânea e isolada por faixa de chuva",
        largura=760,
    )
    tab_reg = tabela(
        ["Desfecho", "Exposição", "Razão de chances", "p"],
        [
            _linha_reg(
                "Bateria na votação",
                or_chuva,
                "chuva nas horas de votação, por 10 mm",
            ),
            _linha_reg(
                "Bateria na votação",
                dados.reg_bateria("bateria_votacao", "chuva_diaria_x"),
                "chuva no dia, por 10 mm",
            ),
            _linha_reg(
                "Bateria na votação",
                dados.reg_bateria("bateria_votacao", "chuva_estrita_x"),
                "chuva das 8h às 17h, por 10 mm",
            ),
            _linha_reg(
                "Bateria na votação",
                or_raj,
                "rajada nas horas de votação, por 10 km/h",
            ),
            _linha_reg(
                "Bateria simultânea",
                or_sim,
                "chuva nas horas de votação, por 10 mm",
            ),
            _linha_reg(
                "Bateria isolada", or_iso, "chuva nas horas de votação, por 10 mm"
            ),
            _linha_reg(
                "Bateria simultânea",
                dados.reg_bateria("bateria_simultanea", "rajada_votacao_x"),
                "rajada nas horas de votação, por 10 km/h",
            ),
            _linha_reg(
                "Bateria isolada",
                dados.reg_bateria("bateria_isolada", "rajada_votacao_x"),
                "rajada nas horas de votação, por 10 km/h",
            ),
            _linha_reg(
                "Reinício na votação",
                dados.reg_bateria("reinicio", "chuva_votacao_x"),
                "chuva nas horas de votação, por 10 mm",
            ),
            _linha_reg(
                "Reinício na votação",
                dados.reg_bateria("reinicio", "rajada_votacao_x"),
                "rajada nas horas de votação, por 10 km/h",
            ),
        ],
        rotulo="Regressões logísticas de bateria e reinício",
        largura=720,
    )
    corpo = (
        caixa(
            "Bateria é operação prevista.",
            "O log registra que a urna operou com a bateria interna. Isso não é defeito nem irregularidade, e o log não diz por quanto tempo nem se a fila parou.",
        )
        + f"<p>Com chuva forte nas horas de votação, <b>{pct(forte['parcela_pct']['valor'], 2)}</b> das urnas registraram bateria durante a votação "
        f"({ic(forte['parcela_pct']['ic95'], 2, False)}). Sem chuva, {pct(seca['parcela_pct']['valor'], 2)}. "
        f"A razão é de <b>{dec(forte['razao_vs_ref']['valor'], 2)}×</b> ({ic(forte['razao_vs_ref']['ic95'], 2, False)}), "
        f"com {inteiro(forte['celulas'])} células na faixa forte.</p>"
        + figura(
            graf_parcela,
            "Barras de erro: IC 95% por bootstrap de células de 0,25°, não de urnas, porque urnas da mesma célula dividem a mesma chuva.",
            640,
        )
        + tab_faixas
        + nota(
            "Chuva fraca não eleva a bateria: a razão é de "
            f"{dec(faixas[1]['razao_vs_ref']['valor'], 2)}× ({ic(faixas[1]['razao_vs_ref']['ic95'], 2, False)}). "
            "A faixa muito forte tem uma célula e 41 urnas: fica no quadro, sem intervalo e sem leitura."
        )
        + "<h3>Toda na bateria simultânea</h3>"
        f"<p>Com o controle por UF, o tamanho da seção e o modelo da urna, cada 10 mm nas horas de votação eleva as chances de bateria em "
        f"<b>{dec(or_chuva['odds_ratio'], 2)}</b> ({ic(or_chuva['ic95'], 2, False)}). A rajada não se associa: "
        f"{dec(or_raj['odds_ratio'], 2)} por 10 km/h ({ic(or_raj['ic95'], 2, False)}). "
        f"A bateria simultânea, quando cinco ou mais outras seções do município registram o mesmo no mesmo minuto, sobe a "
        f"<b>{dec(or_sim['odds_ratio'], 2)}</b> ({ic(or_sim['ic95'], 2, False)}). A isolada não se separa do acaso: "
        f"{dec(or_iso['odds_ratio'], 2)} ({ic(or_iso['ic95'], 2, False)}).</p>"
        + figura(
            graf_razao,
            "Eixo logarítmico; a linha cheia marca razão 1, igual à faixa seca. A bateria isolada fica abaixo de 1 nas faixas moderada e forte.",
            640,
        )
        + tab_sim_iso
        + tab_reg
        + nota(
            "Duas razões ficam abaixo de 1 com intervalo que exclui 1: bateria isolada com rajada e reinício com rajada. São muitas comparações; tratamos como achado a verificar no 2º turno, não como efeito protetor do vento."
        )
        + contra(
            "Dentro do mesmo município, a chuva não se separa de zero.",
            f"Comparando urnas do mesmo município em células de chuva diferente, cada 10 mm se associa a {pp(rm['coef'])} de urnas com bateria "
            f"({ic(rm['ic95'])}; {inteiro(rob['municipios_informativos'])} municípios informativos). O intervalo é largo porque a chuva varia pouco dentro de um município. "
            "O que o dado sustenta é que a chuva forte atinge a rede elétrica de cidades inteiras, e não a tomada de uma urna isolada. "
            "Essa é uma inferência: o dado não separa a rede de outras diferenças entre regiões.",
        )
        + limite(
            "Correlação não é causa. Chuva e vento não são sorteados entre locais; regiões que chovem mais diferem em rede elétrica, distância e hábito de voto. "
            "Os controles reduzem e não eliminam essa diferença."
        )
    )
    return secao(
        2,
        "bateria",
        "Chuva e bateria: <em>a rede cai, a tomada não</em>",
        f"Onde choveu forte, {dec(forte['razao_vs_ref']['valor'], 2)} vezes mais urnas registraram bateria durante a votação, e quase toda a diferença está nas coincidências entre urnas do mesmo município.",
        corpo,
    )


# ------------------------------------------------------------------ cap. 3
def _p_faixa(ab: dict, faixa: str, nivel: str) -> dict | None:
    if nivel == "pais":
        return next((g for g in ab["pais"] if g["grupo"] == faixa), None)
    g = ab[nivel]["grupos"].get(faixa)
    return g


def cap3_abstencao(dados: Dados) -> str:
    d = dados.d
    ab = d["abstencao_x_chuva"]["por_exposicao"]["chuva_votacao"]
    b5 = _binario(dados)
    pais, uf, mun = (_grupo_mais(b5, k) for k in ("pais", "uf", "mun"))
    fe_mun = _reg_abs(dados, "abstencao_2026", "chuva_votacao", "fe_municipio")
    fe_mun22 = _reg_abs(dados, "dif_contra_2022", "chuva_votacao", "fe_municipio")
    fe_uf_dia = _reg_abs(dados, "abstencao_2026", "chuva_diaria", "fe_uf")
    fe_mun_dia = _reg_abs(dados, "abstencao_2026", "chuva_diaria", "fe_municipio")
    gomez_10mm = GOMEZ_PP_POR_POLEGADA * 10 / MM_POR_POLEGADA
    nomes = {
        "fraca": "Chuva fraca (até 5 mm)",
        "moderada": "Chuva moderada (5 a 20 mm)",
        "forte": "Chuva forte (20 a 50 mm)",
    }

    def ponto(g: dict | None, n_estratos: int | None = None) -> dict | None:
        if g is None:
            return None
        m = g["abst_vs_ref_pp"]
        ic95 = m.get("ic95")
        txt = pp(m["valor"])
        if n_estratos is not None:
            txt += f" · {n_estratos} estr."
        return {
            "v": m["valor"],
            "lo": ic95[0] if ic95 else None,
            "hi": ic95[1] if ic95 else None,
            "txt": txt,
        }

    linhas = []
    for f in ("fraca", "moderada", "forte"):
        gp = _p_faixa(ab, f, "pais")
        gu = _p_faixa(ab, f, "dentro_da_uf")
        gm = _p_faixa(ab, f, "dentro_do_municipio")
        linhas.append(
            {
                "rotulo": nomes[f],
                "pontos": [
                    ponto(gp),
                    ponto(gu, gu["estratos_com_os_dois"]) if gu else None,
                    ponto(gm, gm["estratos_com_os_dois"]) if gm else None,
                ],
            }
        )
    graf_faixa = figs.pontos_series(
        "Abstenção contra a faixa seca, por faixa de chuva e nível de comparação",
        "Para cada faixa de chuva, três comparações com a faixa seca: no país, dentro da mesma UF e dentro do mesmo município. A diferença do país encolhe e perde o intervalo quando a comparação fica local.",
        linhas,
        [("País", COR_D), ("Dentro da UF", COR_A), ("Dentro do município", COR_B)],
        (-6, 6),
        [-6, -3, 0, 3, 6],
        lambda t: sinal(t, 0),
        lw=190,
        unidade="pontos percentuais de abstenção contra a faixa seca; marca vazada: menos de 10 estratos, sem IC",
    )
    graf_resumo = figs.pontos_ic(
        "Efeito da chuva sobre a abstenção, do bruto ao controlado",
        "Seis estimativas em pontos percentuais. A diferença bruta de mais de dois pontos cai para perto de zero com os controles; com efeito fixo de UF e chuva do dia, o sinal fica negativo.",
        [
            {
                "rotulo": "Bruta no país (mais de 5 mm contra até 5 mm)",
                "v": pais["abst_vs_ref_pp"]["valor"],
                "lo": pais["abst_vs_ref_pp"]["ic95"][0],
                "hi": pais["abst_vs_ref_pp"]["ic95"][1],
                "cor": COR_D,
                "txt": pp(pais["abst_vs_ref_pp"]["valor"]),
            },
            {
                "rotulo": "Dentro da mesma UF",
                "v": uf["abst_vs_ref_pp"]["valor"],
                "lo": uf["abst_vs_ref_pp"]["ic95"][0],
                "hi": uf["abst_vs_ref_pp"]["ic95"][1],
                "cor": COR_A,
                "txt": pp(uf["abst_vs_ref_pp"]["valor"]),
            },
            {
                "rotulo": "Dentro do mesmo município",
                "v": mun["abst_vs_ref_pp"]["valor"],
                "lo": mun["abst_vs_ref_pp"]["ic95"][0],
                "hi": mun["abst_vs_ref_pp"]["ic95"][1],
                "cor": COR_A,
                "txt": pp(mun["abst_vs_ref_pp"]["valor"]),
            },
            {
                "rotulo": "Efeito fixo de município, por 10 mm",
                "v": fe_mun["coef"],
                "lo": fe_mun["ic95"][0],
                "hi": fe_mun["ic95"][1],
                "cor": COR_A,
                "txt": pp(fe_mun["coef"]),
            },
            {
                "rotulo": "Mesmo, contra 2022, por 10 mm",
                "v": fe_mun22["coef"],
                "lo": fe_mun22["ic95"][0],
                "hi": fe_mun22["ic95"][1],
                "cor": COR_C,
                "txt": pp(fe_mun22["coef"]),
            },
            {
                "rotulo": "Contraponto: efeito fixo de UF, chuva do dia, por 10 mm",
                "v": fe_uf_dia["coef"],
                "lo": fe_uf_dia["ic95"][0],
                "hi": fe_uf_dia["ic95"][1],
                "cor": COR_B,
                "txt": pp(fe_uf_dia["coef"]),
            },
        ],
        (-1.5, 3.0),
        [-1, 0, 1, 2, 3],
        lambda t: sinal(t, 0),
        lw=250,
        zero=0.0,
        rotulo_n=32,
        unidade="pontos percentuais de abstenção, IC 95%",
    )
    linhas_tab = []
    for g in ab["pais"]:
        if g["abst_pct"].get("ic95") is None:
            continue
        linhas_tab.append(
            [
                nomes.get(g["grupo"], "Seca (0 mm)"),
                inteiro(g["celulas"]),
                inteiro(g["aptos"]),
                parcela(g["abst_pct"]),
                com_ic(g["abst_vs_ref_pp"]) if g["abst_vs_ref_pp"] else "referência",
                com_ic(g["dif_abst_pp"]),
            ]
        )
    tab_faixa = tabela(
        [
            "Chuva nas horas de votação",
            "Células",
            "Aptos",
            "Abstenção 2026",
            "Contra a seca",
            "2026 menos 2022",
        ],
        linhas_tab,
        numericas=(1, 2),
        rotulo="Abstenção por faixa de chuva",
        largura=760,
    )
    tab_bin = tabela(
        [
            "Comparação (mais de 5 mm contra até 5 mm)",
            "Estratos",
            "Abstenção 2026",
            "2026 menos 2022",
        ],
        [
            [
                "País",
                "todos",
                com_ic(pais["abst_vs_ref_pp"]),
                com_ic(pais["dif_vs_ref_pp"]),
            ],
            [
                "Dentro da mesma UF",
                inteiro(b5["dentro_da_uf"]["estratos"]),
                com_ic(uf["abst_vs_ref_pp"]),
                com_ic(uf["dif_vs_ref_pp"]),
            ],
            [
                "Dentro do mesmo município",
                inteiro(b5["dentro_do_municipio"]["estratos"]),
                com_ic(mun["abst_vs_ref_pp"]),
                com_ic(mun["dif_vs_ref_pp"]),
            ],
        ],
        rotulo="Corte binário em 5 mm, três níveis de comparação",
        largura=640,
    )
    corpo = (
        f"<p>Na comparação bruta, as urnas com mais de 5 mm nas horas de votação tiveram abstenção <b>{pp(pais['abst_vs_ref_pp']['valor'])}</b> maior "
        f"({ic(pais['abst_vs_ref_pp']['ic95'])}). Dentro da mesma UF, a diferença cai para {pp(uf['abst_vs_ref_pp']['valor'])} "
        f"({ic(uf['abst_vs_ref_pp']['ic95'])}). Dentro do município, para {pp(mun['abst_vs_ref_pp']['valor'])} "
        f"({ic(mun['abst_vs_ref_pp']['ic95'])}).</p>"
        + figura(
            graf_faixa,
            "Cada faixa é comparada à seca. Com a comparação local, as faixas moderada e forte têm poucos estratos com os dois grupos.",
            640,
        )
        + tab_faixa
        + figura(
            graf_resumo,
            "As três primeiras linhas usam o corte de 5 mm; as demais são regressões lineares ponderadas por aptos, por 10 mm de chuva, com erro-padrão por célula.",
            640,
        )
        + tab_bin
        + nota(
            f"Contra o 2º turno de 2022, a diferença do país é de {pp(pais['dif_vs_ref_pp']['valor'])} e a de dentro da UF permanece em {pp(uf['dif_vs_ref_pp']['valor'])} "
            f"({ic(uf['dif_vs_ref_pp']['ic95'])}). Só dentro do município ela perde a força: {pp(mun['dif_vs_ref_pp']['valor'])} ({ic(mun['dif_vs_ref_pp']['ic95'])}). "
            "O dado não explica por quê."
        )
        + contra(
            "Com efeito fixo de UF, a chuva do dia vem associada a abstenção menor.",
            f"Cada 10 mm de chuva no dia se associa a {pp(fe_uf_dia['coef'])} de abstenção ({ic(fe_uf_dia['ic95'])}) quando se compara dentro do mesmo estado. "
            f"Dentro do município, o coeficiente volta a {pp(fe_mun_dia['coef'])} ({ic(fe_mun_dia['ic95'])}) e não se separa de zero. "
            "A leitura é que a diferença bruta é, em grande parte, geografia: os estados e regiões onde choveu em 4 de outubro diferem dos secos em abstenção por motivos que a chuva não explica. "
            "Um sinal negativo dentro da UF não tem leitura causal razoável, porque não há mecanismo para a chuva elevar a participação. "
            "A hipótese mais simples é composição: dentro de um estado, os municípios chuvosos diferem dos secos. Isso é hipótese, não medida.",
        )
        + caixa(
            "O resultado americano, em escala brasileira.",
            f"Gomez, Hansford e Krause (2007) encontraram queda de cerca de {dec(GOMEZ_PP_POR_POLEGADA, 1)} ponto de comparecimento por polegada de chuva ({dec(MM_POR_POLEGADA, 1)} mm) nos EUA, "
            f"o que equivale a aproximadamente {pp(-gomez_10mm)} por 10 mm, por nossa conversão. O nosso coeficiente dentro do município é de {pp(fe_mun['coef'])} "
            f"({ic(fe_mun['ic95'])}); o intervalo inclui esse valor e inclui o zero, então o dado não distingue um efeito americano de nenhum efeito. "
            "A comparação exige cautela: nos EUA o voto é facultativo, no Brasil é obrigatório, com justificativa ou multa para quem falta.",
        )
        + limite(
            "Abstenção é razão de somas ponderada por aptos; seção pequena não pesa como grande. A comparação com 2022 usa o 2º turno, com motivação diferente, "
            "e a renumeração de seções muda o eleitorado de parte delas."
        )
    )
    return secao(
        3,
        "abstencao",
        "Chuva e abstenção: <em>a diferença é geografia</em>",
        f"Chuva acima de 5 mm vem com {pp(pais['abst_vs_ref_pp']['valor'])} de abstenção no país. Dentro do município, a diferença é de {pp(mun['abst_vs_ref_pp']['valor'])}, e o intervalo inclui o zero.",
        corpo,
    )


# ------------------------------------------------------------------ cap. 4
def cap4_bateria_abstencao(dados: Dados) -> str:
    d = dados.d
    ab = d["abstencao_x_bateria"]
    pais = ab["pais"][1]
    mun = ab["dentro_do_municipio"]["grupos"]["com bateria durante a votação"]
    pre = ab["dentro_do_predio"]["grupos"]["com bateria durante a votação"]
    inter = d["abstencao_x_chuva"]["regressoes"]["interacao_chuva_bateria"]
    i_uf = inter["abstencao_2026"]["fe_uf"]["termos"]["chuva_x_bat"]
    i_mun = inter["abstencao_2026"]["fe_municipio"]["termos"]["chuva_x_bat"]
    var = d["cadeia_completa"]["variantes"]["chuva_forte_no_dia"][
        "abst_alta_por_combinacao"
    ]
    rot_comb = {
        (False, False): "Sem chuva forte, sem bateria",
        (False, True): "Sem chuva forte, com bateria",
        (True, False): "Com chuva forte, sem bateria",
        (True, True): "Com chuva forte, com bateria",
    }
    cor_comb = {
        (False, False): COR_D,
        (False, True): COR_A,
        (True, False): COR_C,
        (True, True): COR_B,
    }
    graf_cadeia = figs.pontos_referencia(
        "Urnas com abstenção acima da mediana do município, pela cadeia chuva e bateria",
        "Quatro combinações de chuva forte e bateria. Todas ficam perto de 50%, o valor que se esperaria sem relação alguma.",
        [
            {
                "rotulo": f"{rot_comb[(v['chuva'], v['bateria'])]} ({inteiro(v['urnas'])} urnas)",
                "v": v["abst_alta_pct"],
                "cor": cor_comb[(v["chuva"], v["bateria"])],
                "txt": pct(v["abst_alta_pct"], 2),
            }
            for v in var
        ],
        (47, 53),
        [47, 48, 49, 50, 51, 52, 53],
        50.0,
        "50% = nenhuma relação",
        lambda t: f"{t:g}%",
    )
    graf_bat = figs.pontos_ic(
        "Abstenção das urnas com bateria contra as demais, por nível de comparação",
        "Seis estimativas em pontos percentuais: no país, dentro do município e dentro do prédio, para a abstenção de 2026 e para a diferença contra 2022.",
        [
            {
                "rotulo": "País, abstenção 2026",
                "v": pais["abst_vs_ref_pp"]["valor"],
                "lo": pais["abst_vs_ref_pp"]["ic95"][0],
                "hi": pais["abst_vs_ref_pp"]["ic95"][1],
                "cor": COR_D,
                "txt": pp(pais["abst_vs_ref_pp"]["valor"]),
            },
            {
                "rotulo": "Dentro do município, abstenção 2026",
                "v": mun["abst_vs_ref_pp"]["valor"],
                "lo": mun["abst_vs_ref_pp"]["ic95"][0],
                "hi": mun["abst_vs_ref_pp"]["ic95"][1],
                "cor": COR_A,
                "txt": pp(mun["abst_vs_ref_pp"]["valor"]),
            },
            {
                "rotulo": "Dentro do prédio, abstenção 2026",
                "v": pre["abst_vs_ref_pp"]["valor"],
                "lo": pre["abst_vs_ref_pp"]["ic95"][0],
                "hi": pre["abst_vs_ref_pp"]["ic95"][1],
                "cor": COR_A,
                "txt": pp(pre["abst_vs_ref_pp"]["valor"]),
            },
            {
                "rotulo": "País, contra 2022",
                "v": pais["dif_vs_ref_pp"]["valor"],
                "lo": pais["dif_vs_ref_pp"]["ic95"][0],
                "hi": pais["dif_vs_ref_pp"]["ic95"][1],
                "cor": COR_C,
                "txt": pp(pais["dif_vs_ref_pp"]["valor"]),
            },
            {
                "rotulo": "Dentro do município, contra 2022",
                "v": mun["dif_vs_ref_pp"]["valor"],
                "lo": mun["dif_vs_ref_pp"]["ic95"][0],
                "hi": mun["dif_vs_ref_pp"]["ic95"][1],
                "cor": COR_C,
                "txt": pp(mun["dif_vs_ref_pp"]["valor"]),
            },
            {
                "rotulo": "Dentro do prédio, contra 2022",
                "v": pre["dif_vs_ref_pp"]["valor"],
                "lo": pre["dif_vs_ref_pp"]["ic95"][0],
                "hi": pre["dif_vs_ref_pp"]["ic95"][1],
                "cor": COR_C,
                "txt": pp(pre["dif_vs_ref_pp"]["valor"]),
            },
        ],
        (-0.7, 0.9),
        [-0.5, 0, 0.5],
        lambda t: sinal(t, 1),
        lw=250,
        zero=0.0,
        rotulo_n=32,
        unidade="pontos percentuais, urnas com bateria menos urnas sem bateria, IC 95%",
    )
    tab_tipo = tabela(
        [
            "Tipo de bateria na votação",
            "Urnas",
            "Abstenção 2026",
            "Contra quem não teve",
            "2026 menos 2022, contra quem não teve",
        ],
        [
            [
                g["grupo"].capitalize(),
                inteiro(g["urnas"]),
                parcela(g["abst_pct"]),
                com_ic(g["abst_vs_ref_pp"]) if g["abst_vs_ref_pp"] else "referência",
                com_ic(g["dif_vs_ref_pp"]) if g["dif_vs_ref_pp"] else "referência",
            ]
            for g in ab["por_tipo"]["pais"]
        ],
        numericas=(1,),
        rotulo="Abstenção por tipo de bateria",
        largura=760,
    )
    ch = d["cadeia_completa"]["variantes"]["chuva_forte_no_dia"][
        "abst_alta_por_combinacao"
    ][-1]
    margem = 196 * math.sqrt(0.25 / ch["urnas"])
    corpo = (
        f"<p>As urnas com bateria durante a votação tiveram abstenção <b>{pp(pais['abst_vs_ref_pp']['valor'])}</b> maior que as demais no país "
        f"({ic(pais['abst_vs_ref_pp']['ic95'])}). Dentro do mesmo prédio, a diferença é de <b>{pp(pre['abst_vs_ref_pp']['valor'])}</b> "
        f"({ic(pre['abst_vs_ref_pp']['ic95'])}). Contra 2022, dentro do prédio, {pp(pre['dif_vs_ref_pp']['valor'])} ({ic(pre['dif_vs_ref_pp']['ic95'])}). "
        "Urnas do mesmo prédio compartilham rua, clima e acesso; a diferença que sobra é de centésimos de ponto.</p>"
        + figura(
            graf_bat,
            "A diferença contra 2022 no país tem sinal oposto ao da abstenção bruta: a comparação nacional mistura geografia.",
            640,
        )
        + tab_tipo
        + "<h3>A cadeia completa: chuva, bateria e abstenção</h3>"
        "<p>Se a chuva derrubasse a energia e a queda de energia afastasse eleitores, as urnas com chuva forte e bateria teriam mais abstenção que as demais. "
        "Cruzamos as três coisas e perguntamos qual parcela das urnas tem abstenção acima da mediana do próprio município. Sem relação alguma, seria 50%.</p>"
        + figura(
            graf_cadeia,
            "Eixo recortado em 47% a 53% para as quatro combinações ficarem legíveis; a distância à linha é de no máximo dois pontos.",
            640,
        )
        + nota(
            f"A combinação de chuva forte com bateria chega a {pct(ch['abst_alta_pct'], 2)}. Com {inteiro(ch['urnas'])} urnas, a margem de amostragem simples é de cerca de "
            f"±{dec(margem, 1)} ponto (piso: não agrupa por célula, então o intervalo real é mais largo). O motor não calcula intervalo para estas parcelas."
        )
        + contra(
            "Há um sinal, e ele depende do controle.",
            f"Com efeito fixo de UF, a interação entre chuva e bateria é de {pp(i_uf['coef'])} por 10 mm ({ic(i_uf['ic95'])}). "
            f"Dentro do município, ela cai para {pp(i_mun['coef'])} ({ic(i_mun['ic95'])}) e perde a força. "
            "Tratamos isso como uma pista a observar no 2º turno, não como efeito: o sinal só existe quando a comparação mistura municípios.",
        )
        + limite(
            "O log diz que a urna operou com bateria, não por quanto tempo nem se a fila parou. Tempo em bateria não é medido; "
            "a comparação mede a presença do registro, não a duração do problema."
        )
    )
    return secao(
        4,
        "bateria-abstencao",
        "Bateria e abstenção: <em>não há cadeia</em>",
        f"Dentro do prédio, urna com bateria e urna sem bateria têm abstenção que difere em {pp(pre['abst_vs_ref_pp']['valor'])}. A cadeia chuva, bateria e abstenção não aparece.",
        corpo,
    )


__all__ = [
    "cap1_metodo",
    "cap2_bateria",
    "cap3_abstencao",
    "cap4_bateria_abstencao",
    "guia",
    "hero",
]
