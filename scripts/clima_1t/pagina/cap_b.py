"""Capítulos 5 a 7: locais curiosos, resumo por UF e previsão para 25/10."""

from __future__ import annotations

import re
from collections import Counter

from . import figs, mapas
from .comum import (
    COR_A,
    caixa,
    contra,
    estatisticas,
    figura,
    limite,
    lista,
    nota,
    secao,
    tabela,
)
from .util import Dados, dec, esc, hora_br, inteiro, pct, pp, titulo_pt

VISIVEIS = 10
NOME_NIVEL = {
    "alto": "Alto",
    "medio": "Médio",
    "baixo": "Baixo",
    "sem_dado": "Sem dado",
}
INDIGENA = re.compile(r"IND[IÍ]GENA|ALDEIA")
LISTAS = [
    (
        "a",
        "a_chuva_forte_bateria_abstencao_alta",
        "Chuva forte, bateria e abstenção alta",
    ),
    (
        "b",
        "b_bateria_em_predio_seco_e_sozinho",
        "Bateria em prédio seco e sozinho no município",
    ),
    ("c", "c_chuva_muito_forte_sem_bateria", "Chuva muito forte e nenhuma bateria"),
    (
        "d",
        "d_maior_salto_de_abstencao_com_chuva_forte",
        "Maior salto de abstenção com chuva forte",
    ),
    ("e", "e_chuva_forte_e_abstencao_caiu", "Chuva forte e abstenção que caiu"),
]


def _mm(x) -> str:
    return "sem dado" if x is None else dec(x, 1)


def _pp(x) -> str:
    return "sem dado" if x is None else pp(x)


def linhas_locais(itens: list[dict]) -> tuple[list[list], list[str]]:
    linhas, attrs = [], []
    for k, it in enumerate(itens):
        nome = (
            f'<a href="{esc(it["mapa"])}" rel="noopener">{esc(it["nome"])}</a>'
            f"<small>{esc(titulo_pt(it['municipio']))} ({esc(it['uf'])}), zona {it['zona']}</small>"
        )
        linhas.append(
            [
                nome,
                _mm(it["chuva_04_10_mm"]),
                _mm(it["chuva_votacao_mm"]),
                f"{it['urnas_bateria_votacao']} de {it['urnas']}",
                inteiro(it["aptos"]),
                pct(it["abst_pct"], 1),
                _pp(it["dif_abst_pp"]),
            ]
        )
        extra = ' class="extra"' if k >= VISIVEIS else ""
        attrs.append(f'data-uf="{esc(it["uf"])}"{extra}')
    return linhas, attrs


CAB_LOCAIS = [
    "Local de votação",
    "Chuva no dia (mm)",
    "Chuva na votação (mm)",
    "Urnas com bateria na votação",
    "Aptos",
    "Abstenção 2026",
    "2026 menos 2022",
]


def _tabela_lista(ident: str, itens: list[dict], rotulo: str) -> str:
    linhas, attrs = linhas_locais(itens)
    return tabela(
        CAB_LOCAIS,
        linhas,
        numericas=(1, 2, 4, 5, 6),
        rotulo=rotulo,
        ident=f"tabela-{ident}",
        largura=860,
        atributos_linha=attrs,
    )


def _cabecalho_lista(letra: str, titulo: str, bloco: dict) -> str:
    return (
        f"<h3>({letra}) {titulo}</h3>"
        f'<p class="note">Regra: {esc(bloco["regra"])}. Atendem à regra: <b>{inteiro(bloco["total_que_atende"])}</b>. '
        f"Os {min(VISIVEIS, len(bloco['itens']))} primeiros:</p>"
    )


def _n_indigenas(itens: list[dict]) -> int:
    return sum(1 for it in itens[:VISIVEIS] if INDIGENA.search(it["nome"].upper()))


def cap5_curiosos(dados: Dados) -> str:
    d = dados.d
    lc = d["locais_curiosos"]
    ufs = sorted({it["uf"] for _, k, _ in LISTAS for it in lc[k]["itens"]})
    opcoes = "".join(f'<option value="{u}">{u}</option>' for u in ufs)
    filtro = (
        '<div class="filtro js-only" hidden><label for="filtro-uf"><b>Filtrar por UF:</b></label>'
        f'<select id="filtro-uf"><option value="">Todas</option>{opcoes}</select>'
        '<output id="filtro-n" aria-live="polite"></output></div>'
    )
    blocos = []
    for letra, chave, titulo in LISTAS:
        b = lc[chave]
        blocos.append(
            _cabecalho_lista(letra, titulo, b)
            + _tabela_lista(letra, b["itens"], titulo)
            + _comentario(letra, b)
        )
    blocos.append(_lista_f(dados))
    corpo = (
        caixa(
            "Como ler estas listas.",
            "São pistas por regra declarada, não conclusão sobre o local. Um prédio aparece porque o número é extremo, "
            "não porque algo irregular tenha ocorrido. O log diz que a urna operou com bateria; a abstenção diz quantos faltaram. "
            "Nenhum dos dois diz por quê. Cada nome leva ao mapa de fiscais, com a ficha do prédio.",
        )
        + filtro
        + "".join(blocos)
        + nota(
            "Sem JavaScript, cada lista mostra os dez primeiros. Com JavaScript, o filtro por UF acima também mostra, entre os trinta primeiros de cada regra, os que pertencem ao estado escolhido."
        )
    )
    return secao(
        5,
        "curiosos",
        "Locais curiosos: <em>pistas para a ata</em>",
        "Seis listas, cada uma por uma regra declarada, para o fiscal e o jornalista abrirem a ficha do prédio no mapa de fiscais.",
        corpo,
    )


def _comentario(letra: str, b: dict) -> str:
    itens = b["itens"]
    if letra in ("a", "d"):
        n = _n_indigenas(itens)
        return nota(
            f"{n} dos {VISIVEIS} primeiros têm nome de escola indígena ou de aldeia, quase todos em Mato Grosso do Sul. "
            "São comunidades pequenas, com poucas centenas de aptos, onde poucos eleitores mudam a abstenção em vários pontos percentuais. "
            "O log não diz por que a abstenção subiu, e a chuva do dia não é a das horas de votação."
        )
    if letra == "b":
        it = itens[0]
        interm = (
            it["urnas_bateria_votacao"]
            - it["urnas_bateria_simultanea"]
            - it["urnas_bateria_isolada"]
        )
        ufs = Counter(i["uf"] for i in itens)
        ufs_txt = ", ".join(f"{u} ({n})" for u, n in ufs.most_common())
        return caixa(
            f"{titulo_pt(it['municipio'])} ({it['uf']}): {it['urnas_bateria_votacao']} de {it['urnas']} urnas em bateria, chuva zero.",
            f"Nenhuma das urnas do prédio tem a coincidência de cinco ou mais seções do município, a assinatura de um corte de energia da cidade; "
            f"{inteiro(interm)} coincidem com uma a quatro outras. É pista de rede elétrica local ou do próprio prédio, a conferir na ata e com a zona eleitoral. "
            f"Os dez locais da lista vêm de: {ufs_txt}. Bateria em prédio seco mostra que a chuva não é a única origem do registro.",
        )
    if letra == "c":
        it = itens[1]
        return nota(
            f"Chuva do dia não é chuva da votação. Em {titulo_pt(it['municipio'])} ({it['uf']}), a célula tem {_mm(it['chuva_04_10_mm'])} mm no dia e "
            f"{_mm(it['chuva_votacao_mm'])} mm nas horas de votação. O primeiro item da lista é a exceção: {_mm(itens[0]['chuva_votacao_mm'])} mm nas horas de votação e nenhuma urna com bateria."
        )
    it = itens[0]
    return nota(
        f"Em {titulo_pt(it['municipio'])} ({it['uf']}), a célula tem {_mm(it['chuva_04_10_mm'])} mm no dia e {_mm(it['chuva_votacao_mm'])} mm nas horas de votação: "
        "a chuva forte do dia caiu fora da janela em que as urnas estavam abertas. A regra usa a chuva do dia, e o motor não promete mais do que isso."
    )


def _lista_f(dados: Dados) -> str:
    f = dados.d["locais_curiosos"]["f_mudancas_2t"]
    ori, dem, conf = f["origens"], f["demais_locais"], f["confresa_mt"]
    linhas = [
        ("Origens das mudanças do 2º turno", ori),
        ("Demais locais", dem),
        (f"Confresa (MT), {conf['municipio']['locais']} locais", conf["municipio"]),
    ]
    tab = tabela(
        [
            "Grupo",
            "Locais",
            "Aptos",
            "Chuva média no dia (mm)",
            "Locais com chuva forte",
            "Urnas com bateria na votação",
            "Abstenção 2026",
            "2026 menos 2022",
        ],
        [
            [
                rot,
                inteiro(g["locais"]),
                inteiro(g["aptos"]),
                dec(g["chuva_04_10_media_mm"], 2),
                pct(g["locais_chuva_forte_pct"], 2),
                pct(g["urnas_bateria_votacao_pct"], 2),
                pct(g["abst_pct"], 2),
                pp(g["dif_abst_pp"]),
            ]
            for rot, g in linhas
        ],
        numericas=(1, 2, 3, 4, 5, 6, 7),
        rotulo="Locais de origem das mudanças do 2º turno",
        largura=900,
    )
    it_conf = conf["locais"]
    return (
        "<h3>(f) As mudanças de local do 2º turno e Confresa (MT)</h3>"
        f'<p class="note">{inteiro(f["pares_mudanca_real"])} pares de mudança real de prédio, {inteiro(f["origens_distintas"])} locais de origem distintos, '
        f"{inteiro(f['origens_com_clima'])} com clima. Descritivo: sem intervalo, porque são médias de grupos.</p>"
        + tab
        + caixa(
            "O que isso sustenta.",
            f"Os locais de origem tiveram menos chuva que o resto do país ({dec(ori['chuva_04_10_media_mm'], 2)} mm contra {dec(dem['chuva_04_10_media_mm'], 2)} mm no dia) "
            f"e mais registro de bateria ({pct(ori['urnas_bateria_votacao_pct'], 2)} contra {pct(dem['urnas_bateria_votacao_pct'], 2)}). "
            "Isso é compatível com realocações por problema de energia e não sustenta realocação por chuva. "
            f"Em Confresa, a chuva média foi de {dec(conf['municipio']['chuva_04_10_media_mm'], 2)} mm e nenhum local teve chuva forte. "
            "É inferência a partir de médias de grupos: o motivo de cada realocação está nas decisões dos tribunais regionais, no "
            '<a href="mudancas_secoes_abstencoes.html#motivos">laudo das mudanças de local</a>.',
        )
        + _tabela_lista("f", it_conf, "Locais de Confresa (MT)")
    )


# ------------------------------------------------------------------ cap. 6
def cap6_uf(dados: Dados) -> str:
    resumo = dados.d["mapa_resumo"]
    linhas, attrs = [], []
    for r in resumo:
        linhas.append(
            [
                (r["uf"], r["uf"]),
                inteiro(r["urnas"]),
                dec(r["chuva_04_10_media_mm"], 2),
                dec(r["chuva_votacao_media_mm"], 2),
                pct(r["locais_chuva_forte_pct"], 2),
                pct(r["urnas_bateria_votacao_pct"], 2),
                pct(r["abst_pct"], 2),
                pp(r["dif_abst_pp"]),
            ]
        )
        attrs.append(f'data-uf="{esc(r["uf"])}"')
    tab = tabela(
        [
            "UF",
            "Urnas",
            "Chuva média no dia (mm)",
            "Chuva média na votação (mm)",
            "Locais com chuva forte",
            "Urnas com bateria na votação",
            "Abstenção 2026",
            "2026 menos 2022",
        ],
        linhas,
        ordenavel=True,
        numericas=(1, 2, 3, 4, 5, 6, 7),
        rotulo="Resumo por UF",
        ident="tabela-uf",
        largura=860,
        atributos_linha=attrs,
    )
    mais_chuva = sorted(resumo, key=lambda r: -r["chuva_votacao_media_mm"])[:3]
    mais_bat = sorted(resumo, key=lambda r: -r["urnas_bateria_votacao_pct"])[:3]
    secos = sorted(
        (r for r in resumo if r["chuva_votacao_media_mm"] < 3),
        key=lambda r: -r["urnas_bateria_votacao_pct"],
    )[:3]
    pontos = [
        {
            "uf": r["uf"],
            "x": r["chuva_votacao_media_mm"],
            "y": r["urnas_bateria_votacao_pct"],
            "cor": COR_A,
            "rotulo": r["chuva_votacao_media_mm"] > 3
            or r["urnas_bateria_votacao_pct"] > 14,
        }
        for r in resumo
    ]
    graf = figs.dispersao_uf(
        "Chuva média nas horas de votação e urnas com bateria, por UF",
        "Cada ponto é um estado. Mato Grosso do Sul e São Paulo têm chuva e bateria altas; Pará, Tocantins e Piauí têm bateria alta com pouca chuva.",
        pontos,
        (0, 12),
        (0, 35),
        "chuva média nas horas de votação (mm, ponderada por aptos)",
        "% das urnas com bateria durante a votação",
        lambda t: f"{t:g}",
        lambda t: f"{t:g}%",
        [0, 2, 4, 6, 8, 10, 12],
        [0, 10, 20, 30],
    )

    def nomes(rs, campo, fmt):
        return ", ".join(f"{r['uf']} ({fmt(r[campo])})" for r in rs)

    corpo = f"<p>Chuva nas horas de votação: {nomes(mais_chuva, 'chuva_votacao_media_mm', lambda v: dec(v, 2) + ' mm')}. " f"Urnas com bateria na votação: {nomes(mais_bat, 'urnas_bateria_votacao_pct', lambda v: pct(v, 2))}.</p>" + figura(
        graf,
        "Média ponderada por aptos. A chuva aqui é a média do estado; a análise do capítulo 2 compara células.",
        600,
    ) + tab + contra(
        "Bateria alta onde quase não choveu.",
        f"Entre os estados com menos de 3 mm de chuva média nas horas de votação, "
        f"{nomes(secos, 'urnas_bateria_votacao_pct', lambda v: pct(v, 2))} têm as maiores parcelas de urnas com bateria. "
        "A chuva não explica o registro de bateria sozinha, e o capítulo 2 já mostrou que a bateria isolada, a que não coincide com outras urnas, não sobe com a chuva.",
    ) + limite(
        "Tabela descritiva, sem controles. A média do estado esconde diferenças entre células, e o resumo por UF não é uma prova de nada que o capítulo 2 não tenha medido."
    )
    return secao(
        6,
        "uf",
        "Por UF: <em>onde choveu e onde a urna foi à bateria</em>",
        "Mato Grosso do Sul e São Paulo juntam chuva forte e bateria. O Pará tem bateria sem chuva.",
        corpo,
    )


# ------------------------------------------------------------------ cap. 7
def cap7_previsao(dados: Dados) -> str:
    d = dados.d
    pv = d["previsao_25_10"]
    pais = pv["pais"]
    gerado = hora_br(pv["gerado_em"])
    alvo = f"{pv['alvo'][8:10]}/{pv['alvo'][5:7]}"
    mapa, cel = mapas.mapa_risco(dados)
    regra = pv["regra_risco"]
    uf_rank = sorted(
        pv["por_uf"].items(), key=lambda kv: -kv[1]["eleitores_risco_medio_ou_alto_pct"]
    )
    topo = [
        (uf, v) for uf, v in uf_rank if v["eleitores_risco_medio_ou_alto_pct"] >= 50
    ]
    graf = figs.barras_h(
        "Eleitores em área de risco climático previsto para 25 de outubro, por UF",
        "Barras por estado com a parcela do cadastro mapeado em risco alto e em risco médio ou alto na consulta indicada.",
        [
            {
                "rotulo": uf,
                "barras": [
                    {
                        "v": v["eleitores_risco_alto_pct"],
                        "cor": "#a8321f",
                        "txt": pct(v["eleitores_risco_alto_pct"], 1),
                    },
                    {
                        "v": v["eleitores_risco_medio_ou_alto_pct"],
                        "cor": "#e0b25a",
                        "txt": pct(v["eleitores_risco_medio_ou_alto_pct"], 1),
                    },
                ],
            }
            for uf, v in topo
        ],
        [("Risco alto", "#a8321f"), ("Risco médio ou alto", "#e0b25a")],
        fmt=lambda x: pct(x, 1),
        lw=60,
        maximo=100.0,
    )
    tab_nivel = tabela(
        [
            "Nível",
            "Eleitores",
            "Parcela do eleitorado",
            "Locais de votação",
            "Células de 0,5°",
            "Regra",
        ],
        [
            [
                NOME_NIVEL[n],
                inteiro(pais["eleitores"][n]),
                pct(dados.pct_eleitores(n), 2),
                inteiro(pais["locais"][n]),
                inteiro(pais["celulas"][n]),
                regra[n].replace(">=", "≥"),
            ]
            for n in NOME_NIVEL
        ],
        numericas=(1, 2, 3, 4),
        rotulo="Eleitores e locais por nível de risco",
        largura=900,
    )
    cidades = pv["cidades_risco_alto"]
    tab_cid = tabela(
        [
            "Município",
            "Eleitores em risco alto",
            "Locais em risco alto",
            "Chuva máxima 8h–17h (mm)",
            "Rajada máxima (km/h)",
        ],
        [
            [
                f"{esc(titulo_pt(c['municipio']))} ({esc(c['uf'])})",
                inteiro(c["eleitores_risco_alto"]),
                inteiro(c["locais_risco_alto"]),
                dec(c["chuva_mm_max"], 1),
                dec(c["rajada_kmh_max"], 1),
            ]
            for c in cidades
        ],
        ordenavel=True,
        numericas=(1, 2, 3, 4),
        rotulo="Trinta cidades com mais eleitores em risco alto",
        ident="tabela-cidades",
        largura=720,
        atributos_linha=[f'data-uf="{esc(c["uf"])}"' for c in cidades],
    )
    top3 = sorted(
        pv["por_uf"].items(), key=lambda kv: -kv[1]["eleitores_risco_alto_pct"]
    )[:3]
    top3_txt = ", ".join(
        f"{uf} {pct(v['eleitores_risco_alto_pct'], 1)}" for uf, v in top3
    )
    corpo = f'<p class="rotulo"><b>Previsão de modelo global a 0,5°, gerada em {gerado}, muda todo dia.</b> ' "É indicativo de atenção para a logística da fiscalização, não previsão do que vai acontecer no prédio.</p>" + estatisticas(
        [
            (
                inteiro(pais["eleitores"]["alto"]),
                f"eleitores em risco alto ({pct(dados.pct_eleitores('alto'), 2)}), em {inteiro(pais['locais']['alto'])} locais",
            ),
            (
                inteiro(pais["eleitores"]["medio"]),
                f"em risco médio ({pct(dados.pct_eleitores('medio'), 2)}), em {inteiro(pais['locais']['medio'])} locais",
            ),
            (
                inteiro(pais["eleitores"]["baixo"]),
                f"em risco baixo ({pct(dados.pct_eleitores('baixo'), 2)}), em {inteiro(pais['locais']['baixo'])} locais",
            ),
        ]
    ) + f"<p>Maiores parcelas do cadastro mapeado em risco alto: {top3_txt}.</p>" + figura(
        graf, "Estados com mais da metade do eleitorado em risco médio ou alto.", 600
    ) + figura(
        mapa,
        f"Células de 0,5° da previsão para {alvo}, geradas em {gerado}. Cada célula usa a regra declarada abaixo, somente entre 8h e 17h de Brasília.",
        560,
    ) + tab_nivel + f"<h3>As {len(cidades)} cidades com mais eleitores em risco alto</h3>" + tab_cid + nota(
        "Chuva e rajada são o máximo entre as células do município entre 8h e 17h de Brasília. Município com muitas células, como São Paulo, aparece com o valor mais alto delas."
    ) + "<h3>O que isso implica</h3>" + lista(
        [
            '<span class="tag fato">Fato medido</span> No 1º turno, a chuva se associou a mais urnas na bateria, quase todas por coincidência entre urnas do município. '
            "Para o dia 25, onde a previsão aponta chuva forte, é de se esperar mais registros de bateria e de queda de energia, sem que isso signifique falha da urna.",
            '<span class="tag inf">Inferência</span> A regra de risco inclui rajada por prudência logística. O 1º turno não mostra associação entre rajada e bateria '
            f"(razão de chances de {dec(dados.reg_bateria('bateria_votacao', 'rajada_votacao_x')['odds_ratio'], 2)} por 10 km/h), então o vento pesa menos que a chuva na leitura deste estudo.",
            '<span class="tag juizo">Juízo editorial</span> O que o fiscal confere é a ata: horário da queda de energia, horário em que a urna passou à bateria, '
            "horário em que a energia voltou e se houve fila parada. O estudo não sabe quais prédios têm gerador nem quais têm instalação elétrica mais frágil.",
            '<span class="tag juizo">Juízo editorial</span> Para o eleitor, o dado de 1º turno não sustenta que a chuva afaste o eleitor da seção. '
            "Quem mora em área de risco alto deve planejar o deslocamento como em qualquer dia de chuva forte; este relatório não mede horário de chegada.",
        ]
    ) + caixa(
        "Uma mesma consulta para os mapas e as contas.",
        f"Esta página, suas tabelas e os dados para download usam a consulta de {gerado}. "
        'O <a href="fiscais_mapa.html">mapa de fiscais</a> usa a mesma previsão. '
        "A rotina diária de atualização também reconstrói este relatório. "
        'A previsão é da <a href="https://open-meteo.com/en/docs">Open-Meteo Forecast API</a>; '
        "os cortes de risco são regras de atenção da Arvor, não alertas oficiais da Defesa Civil. "
        "Mantivemos os mesmos limiares em mm e km/h, agora aplicados somente à votação; "
        "a diferença em relação ao relatório diário anterior também reflete a mudança de janela, "
        "não apenas uma revisão meteorológica. Probabilidade significa o máximo entre as horas, "
        "nunca a probabilidade conjunta de chover na janela.",
    ) + limite(
        "Previsão de modelo global, com célula de 0,5° e resolução horária. Pode errar a intensidade, o lugar e a hora da pancada; não resolve cada prédio e muda a cada rodada do modelo. "
        f"As {inteiro(cel['alto'])} células de risco alto são uma regra de atenção, não uma probabilidade de problema."
    )
    return secao(
        7,
        "previsao",
        "E o dia 25? <em>A previsão do tempo para o 2º turno</em>",
        f"{inteiro(pais['eleitores']['alto'])} eleitores estão em células de risco alto na previsão de {gerado}. {top3_txt}.",
        corpo,
    )


__all__ = ["cap5_curiosos", "cap6_uf", "cap7_previsao"]
