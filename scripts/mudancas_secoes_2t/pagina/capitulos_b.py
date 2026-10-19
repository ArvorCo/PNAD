"""Capítulos 6 a 8: o 1º turno nessas seções, o efeito medido e os votos em jogo."""

from __future__ import annotations

from . import figuras as fg
from .contexto import Contexto
from .tabelas import (
    caixa,
    contra,
    detalhes,
    estatisticas,
    figura,
    limite,
    nota,
    secao,
    tabela,
)
from .util import CORES, dec, esc, ic, inteiro, pct, pp, sinal, titulo_pt


def _d(x: dict, casas: int = 2) -> str:
    """Diferença em pontos com o intervalo ao lado."""
    return f"{pp(x['valor'], casas)}<br><small>{ic(x['ic95'], casas)}</small>"


def cap6_primeiro_turno(c: Contexto) -> str:
    d = c.d
    cb = d["comportamento_1t"]
    ic1 = d["intercorrencias_1t"]
    comp = d["cenarios_abstencao"]["composicao_1t"]["mudanca_real"]
    pais = cb["pais_todas_as_urnas"]
    g = cb["grupos"]
    nomes_g = {
        "mudanca_real": "Todas com mudança real",
        "A": "Categoria A (retorno)",
        "novas": "Novas realocações",
    }
    linhas = []
    for k in ("mudanca_real", "A", "novas"):
        m = g[k]["metricas"]
        linhas.append(
            [
                f"<b>{nomes_g[k]}</b><br><small>{inteiro(g[k]['urnas'])} urnas, {inteiro(g[k]['municipios'])} municípios</small>",
                pct(m["abstencao"]["mesmo_municipio"]["grupo"]["valor"], 2),
                _d(m["abstencao"]["mesmo_municipio"]["diferenca_pp"]),
                _d(m["abstencao"]["pais"]["diferenca_pp"]),
                _d(m["flavio_validos"]["mesmo_municipio"]["diferenca_pp"]),
                _d(m["flavio_validos"]["pais"]["diferenca_pp"]),
                _d(m["lula_validos"]["mesmo_municipio"]["diferenca_pp"]),
                _d(m["lula_validos"]["pais"]["diferenca_pp"]),
            ]
        )
    t_comp = tabela(
        [
            "Grupo de urnas",
            "Abstenção do grupo",
            "Abstenção contra o município",
            "Abstenção contra o país",
            "Flávio (válidos) contra o município",
            "Flávio contra o país",
            "Lula (válidos) contra o município",
            "Lula contra o país",
        ],
        linhas,
        numericas=(1, 2, 3, 4, 5, 6, 7),
        rotulo="Comportamento no 1º turno",
        largura=980,
    )
    defs = ic1["definicoes"]
    ordem = [
        "bateria",
        "bateria_votacao",
        "reinicio",
        "abertura_atrasada",
        "fila_fechamento",
        "atencao_2_ou_3",
    ]
    nome_m = {
        "bateria": "Bateria, em qualquer momento",
        "bateria_votacao": "Bateria durante a votação",
        "reinicio": "Reinício durante a votação",
        "abertura_atrasada": "Abertura às 8h30 ou depois",
        "fila_fechamento": "Último voto depois das 18h",
        "atencao_2_ou_3": "Nível de atenção 2 ou 3 no log",
    }
    gi = ic1["grupos"]

    def rz(grupo, m):
        r = gi[grupo]["metricas"][m]["pais"]["razao"]
        return f"{dec(r['valor'], 2)}×<br><small>{ic(r['ic95'], 2, False)}</small>"

    t_int = tabela(
        [
            "Registro no log",
            "Parcela das urnas do país",
            "Mudança real",
            "Novas realocações",
            "Categoria A",
            "Local temporário no 1º turno",
        ],
        [
            [
                nome_m[m] + f"<br><small>{esc(defs[m])}</small>",
                pct(ic1["pais_parcela_pct"][m], 2),
                rz("mudanca_real", m),
                rz("novas", m),
                rz("A", m),
                rz("temp_1t", m),
            ]
            for m in ordem
        ],
        numericas=(1, 2, 3, 4, 5),
        rotulo="Intercorrências do 1º turno, razão contra o país",
        largura=900,
    )
    series = [("Mudança real", CORES["cinza"]), ("Novas realocações", CORES["dourado"])]

    def pt(grupo, m):
        r = gi[grupo]["metricas"][m]["pais"]["razao"]
        return {"v": r["valor"], "lo": r["ic95"][0], "hi": r["ic95"][1]}

    svg = fg.floresta_log(
        "Razão de intercorrências contra o país",
        "Razão entre a parcela de urnas com o registro nos grupos e no país, com intervalo de 95%, em escala logarítmica.",
        [
            {"rotulo": nome_m[m], "pontos": [pt("mudanca_real", m), pt("novas", m)]}
            for m in ordem
        ],
        series,
        lambda v: dec(v, 2) if v < 10 else dec(v, 1),
    )
    total_atr, ordem_atr = c.atrasadas()
    (uf_a, mun_a), n_a = ordem_atr[0]
    loc_a = max(c.reais, key=lambda x: x["abertura_min_atrasada"])
    nv = gi["novas"]["metricas"]
    cm = cb["grupos"]["novas"]["metricas"]
    corpo = (
        f"<p>As urnas com mudança real deram, no 1º turno, <b>{dec(comp['flavio_validos_pct'])}% dos válidos a Flávio e {dec(comp['lula_validos_pct'])}% a Lula</b>, com abstenção de {dec(comp['abstencao_pct'])}% ({inteiro(comp['urnas'])} urnas, exterior incluído). O país: {dec(pais['flavio_validos'])}% e {dec(pais['lula_validos'])}%, abstenção de {dec(pais['abstencao'])}%.</p>"
        + f"<p>A diferença contra o país é geografia. Contra as demais urnas do mesmo município, ela some: Flávio {pp(g['mudanca_real']['metricas']['flavio_validos']['mesmo_municipio']['diferenca_pp']['valor'])} ({ic(g['mudanca_real']['metricas']['flavio_validos']['mesmo_municipio']['diferenca_pp']['ic95'])}) e Lula {pp(g['mudanca_real']['metricas']['lula_validos']['mesmo_municipio']['diferenca_pp']['valor'])} ({ic(g['mudanca_real']['metricas']['lula_validos']['mesmo_municipio']['diferenca_pp']['ic95'])}). Isso descreve onde ficam as seções, não quem foi mudado.</p>"
        + t_comp
        + nota(esc(cb["regra"]))
        + contra(
            "O que contraria a tese de que nada diferencia essas urnas",
            f"A abstenção nas urnas da categoria A foi {pp(g['A']['metricas']['abstencao']['mesmo_municipio']['diferenca_pp']['valor'])} acima do resto do município ({ic(g['A']['metricas']['abstencao']['mesmo_municipio']['diferenca_pp']['ic95'])}). E nas novas realocações o placar do 1º turno é mais favorável a Flávio que no resto do município: {pp(cm['flavio_validos']['mesmo_municipio']['diferenca_pp']['valor'])} ({ic(cm['flavio_validos']['mesmo_municipio']['diferenca_pp']['ic95'])}), e menos favorável a Lula: {pp(cm['lula_validos']['mesmo_municipio']['diferenca_pp']['valor'])} ({ic(cm['lula_validos']['mesmo_municipio']['diferenca_pp']['ic95'])}). É meio ponto, com intervalo que exclui o zero. O voto do 1º turno é anterior à mudança, então isso descreve onde estão os prédios, não efeito de mudar.",
        )
        + "<h3>Intercorrências registradas no log da urna</h3>"
        + f"<p>Nas urnas das novas realocações, a bateria durante a votação aparece <b>{dec(nv['bateria_votacao']['pais']['razao']['valor'])} vez o país</b> ({ic(nv['bateria_votacao']['pais']['razao']['ic95'], 2, False)}). Em todas as urnas com mudança real, a razão é {dec(gi['mudanca_real']['metricas']['bateria_votacao']['pais']['razao']['valor'])} ({ic(gi['mudanca_real']['metricas']['bateria_votacao']['pais']['razao']['ic95'], 2, False)}). Atenção 2 ou 3 no log: {dec(nv['atencao_2_ou_3']['pais']['razao']['valor'])}× nas novas, com intervalo de {dec(nv['atencao_2_ou_3']['pais']['razao']['ic95'][0])} a {dec(nv['atencao_2_ou_3']['pais']['razao']['ic95'][1])}, que contém 1.</p>"
        + figura(
            svg,
            "Fonte: logs das urnas do 1º turno e boletins; razão contra as demais urnas do país. Eixo logarítmico; a linha escura marca 1×.",
        )
        + t_int
        + caixa(
            "A abertura atrasada é um prédio só",
            f"A razão de {dec(nv['abertura_atrasada']['pais']['razao']['valor'])}× nas novas realocações ({ic(nv['abertura_atrasada']['pais']['razao']['ic95'], 2, False)}) nasce de poucas urnas. Dos {inteiro(total_atr)} pares-seção com primeiro voto às 8h30 ou depois no arquivo, {inteiro(n_a)} estão em {esc(titulo_pt(mun_a))} ({uf_a}): {esc(loc_a['nome_1t'])}, categoria {loc_a['categoria']}. Sem esse prédio sobram {inteiro(total_atr - n_a)}. Não recalculamos a razão sem ele.",
        )
        + "<p>Duas leituras cabem. Primeira, inferência: parte das novas realocações saiu de prédios com problema de energia, o que é compatível com os motivos que os TREs alegam (queda de energia, reforma) e com a bateria na votação. Segunda, ressalva: bateria, reinício e fila são registro operacional, comuns em todo o país. Registro de log não é irregularidade e este laudo não o trata como tal.</p>"
        + limite(
            "As razões comparam parcelas de urnas com o registro contra o país; não identificam causa. O exterior fica fora das comparações. Intervalos por reamostragem de prédios (as urnas do mesmo local saem juntas), porque seções do mesmo prédio dividem o mesmo evento."
        )
    )
    return secao(
        6,
        "primeiro-turno",
        "No 1º turno,<br><em>geografia, não seleção.</em>",
        f"Contra o município, Flávio fica em {pp(g['mudanca_real']['metricas']['flavio_validos']['mesmo_municipio']['diferenca_pp']['valor'])} ({ic(g['mudanca_real']['metricas']['flavio_validos']['mesmo_municipio']['diferenca_pp']['ic95'])}). Contra o país, {pp(g['mudanca_real']['metricas']['flavio_validos']['pais']['diferenca_pp']['valor'])}.",
        corpo,
    )


def cap7_efeito(c: Contexto) -> str:
    d = c.d
    e = d["efeito_1t"]
    tr = e["tratamento"]
    ab = e["abstencao"]["mesmo_municipio"]["diferenca_pp"]
    abp = e["abstencao"]["pais"]["diferenca_pp"]
    dd = e["dif_em_dif"]["diferenca"]["mesmo_municipio"]["diferenca_pp"]
    cob = e["dif_em_dif"]["cobertura"]["temp_1t"]
    dose = e["dose_resposta"]["faixas"]
    linhas = []
    for f in dose:
        x = f["dif_em_dif"]["mesmo_municipio"]["diferenca_pp"]
        sem = "sem distância" in f["faixa"]
        linhas.append(
            {
                "rotulo": f["faixa"][0].upper() + f["faixa"][1:],
                "v": x["valor"],
                "lo": x["ic95"][0],
                "hi": x["ic95"][1],
                "cor": CORES["cinza"] if sem else CORES["dourado"],
                "txt": f"{sinal(x['valor'])} pp",
            }
        )
    svg = fg.pontos_ic(
        "Dose e resposta: variação da abstenção por distância até o prédio original",
        "Diferença em diferenças da abstenção, contra as seções estáveis do município, por faixa de distância, com intervalo de 95%.",
        linhas,
        (-1.5, 5),
        [-1, 0, 1, 2, 3, 4, 5],
        lambda v: dec(v, 0).replace("-", "\u2212"),
        unidade="pontos de abstenção a mais que o controle do município",
    )
    t_dose = tabela(
        [
            "Faixa de distância (categoria A)",
            "Urnas",
            "Urnas casadas com 2022",
            "Diferença em diferenças",
            "Intervalo de 95%",
        ],
        [
            [
                f["faixa"],
                inteiro(f["urnas"]),
                inteiro(f["urnas_casadas_2022"]),
                pp(f["dif_em_dif"]["mesmo_municipio"]["diferenca_pp"]["valor"]),
                ic(f["dif_em_dif"]["mesmo_municipio"]["diferenca_pp"]["ic95"]),
            ]
            for f in dose
        ],
        numericas=(1, 2, 3),
        rotulo="Dose e resposta por faixa",
    )
    dr = e["direcao"]
    rj = e["rj"]
    z = rj["zona_161"]
    tr22 = e["troca_desde_2022"]
    corpo = (
        f"<p>O 1º turno já foi um experimento natural. <b>{inteiro(tr['urnas'])} urnas</b> ({inteiro(tr['secoes_cadastro'])} seções no cadastro, {inteiro(tr['eleitores_cadastro'])} eleitores) votaram em local diferente do original em 04/10. A abstenção delas foi <b>{pp(ab['valor'])}</b> acima das demais urnas do mesmo município ({ic(ab['ic95'])}). Contra o país, {pp(abp['valor'])}: geografia de novo.</p>"
        + f"<p>Para isolar o efeito do local, comparamos a variação da abstenção da mesma seção entre o 2º turno de 2022 e o 1º de 2026, contra a variação das seções estáveis do município. Resultado: <b>{pp(dd['valor'])}</b> ({ic(dd['ic95'])}). Cobertura do casamento com 2022: {pct(cob['cobertura_pct'])}.</p>"
        + estatisticas(
            [
                (pp(dd["valor"]), f"diferença em diferenças ({ic(dd['ic95'])})"),
                (pp(ab["valor"]), f"abstenção contra o município ({ic(ab['ic95'])})"),
                (
                    pct(cob["cobertura_pct"]),
                    f"das {inteiro(cob['urnas'])} urnas casadas com a seção de 2022",
                ),
            ]
        )
        + "<h3>Dose e resposta</h3>"
        + f"<p>A categoria A permite medir a distância entre o prédio provisório e o original. A resposta cresce com a distância: até 500 m, {pp(dose[0]['dif_em_dif']['mesmo_municipio']['diferenca_pp']['valor'])}; acima de 5 km, {pp(dose[4]['dif_em_dif']['mesmo_municipio']['diferenca_pp']['valor'])} ({ic(dose[4]['dif_em_dif']['mesmo_municipio']['diferenca_pp']['ic95'])}).</p>"
        + figura(
            svg,
            "Diferença em diferenças: 1º turno de 2026 menos 2º turno de 2022, contra as seções estáveis do município. Fonte: boletins de 2026 e detalhe de votação por seção de 2022 (TSE). Categoria A.",
        )
        + t_dose
        + contra(
            "A resposta não é uma reta",
            f"Na faixa de 500 m a 1 km o efeito é {pp(dose[1]['dif_em_dif']['mesmo_municipio']['diferenca_pp']['valor'])} ({ic(dose[1]['dif_em_dif']['mesmo_municipio']['diferenca_pp']['ic95'])}), indistinguível de zero, e as faixas longas têm poucas urnas ({inteiro(dose[3]['urnas'])} entre 2 e 5 km, {inteiro(dose[4]['urnas'])} acima de 5 km). A leitura de que a distância pesa é plausível e coerente com a literatura, mas os dados desta tabela não a provam sozinhos.",
        )
        + "<h3>Direção do voto</h3>"
        + f"<p>Nas urnas em local temporário, a participação de Flávio nos válidos foi {pp(dr['flavio_validos']['mesmo_municipio']['diferenca_pp']['valor'])} do resto do município ({ic(dr['flavio_validos']['mesmo_municipio']['diferenca_pp']['ic95'])}) e a de Lula, {pp(dr['lula_validos']['mesmo_municipio']['diferenca_pp']['valor'])} ({ic(dr['lula_validos']['mesmo_municipio']['diferenca_pp']['ic95'])}). É meio ponto, nos dois sentidos, e descreve onde ficam os prédios temporários.</p>"
        + "<h3>Rio de Janeiro</h3>"
        + f"<p>No 1º turno, o TRE-RJ transferiu locais por segurança. A Agência Brasil (04/10) e a Agência Pública (16/10) falam em {esc('72 locais em 20 municípios, cerca de 200 mil eleitores')}. As transferências mantiveram o número do local e trocaram nome e endereço, então a regra do local diferente do original não as enxerga. Medimos pelo grupo de urnas transferidas (local temporário ou prédio trocado desde 2022) contra as estáveis da mesma zona: abstenção {pp(rj['abstencao_mesma_zona']['diferenca_pp']['valor'])} ({ic(rj['abstencao_mesma_zona']['diferenca_pp']['ic95'])}) e diferença em diferenças {pp(rj['dif_em_dif_mesma_zona']['diferenca_pp']['valor'])} ({ic(rj['dif_em_dif_mesma_zona']['diferenca_pp']['ic95'])}).</p>"
        + f"<p>Na zona {z['zona']} (Maré), a abstenção foi de {pct(z['abstencao_zona_1t'], 2)}, o mesmo número que o Consultor Jurídico publicou. Nas {inteiro(z['urnas_troca_desde_2022'])} urnas com prédio trocado, {pct(z['abstencao_1t_transferidas'], 2)} contra {pct(z['abstencao_1t_estaveis'], 2)} nas estáveis; a diferença em diferenças é {pp(z['dif_em_dif_pp'])}.</p>"
        + f"<p>Fora do Rio, a troca de prédio desde 2022 ({inteiro(tr22['urnas'])} urnas) dá {pp(tr22['dif_em_dif']['mesmo_municipio']['diferenca_pp']['valor'])} ({ic(tr22['dif_em_dif']['mesmo_municipio']['diferenca_pp']['ic95'])}).</p>"
        + caixa(
            "Rótulo obrigatório",
            esc(e["rotulo"])
            + " O TRE escolhe quais locais mudar. Nenhum número deste capítulo é efeito causal identificado.",
        )
        + limite(
            "Casamento com 2022 por seção cobre "
            + pct(cob["cobertura_pct"])
            + " das urnas. A escolha dos locais por segurança no Rio, por reforma ou por clima não é aleatória e pode se correlacionar com abstenção por outras vias."
        )
    )
    return secao(
        7,
        "efeito",
        "O efeito medido no 1º turno:<br><em>pequeno no agregado, maior com a distância.</em>",
        f"{pp(dd['valor'])} de abstenção em {inteiro(tr['urnas'])} urnas em local temporário ({ic(dd['ic95'])}). Não é efeito causal identificado.",
        corpo,
    )


def _linha_cenario(rot, grupo):
    return [
        rot,
        inteiro(grupo["urnas"]),
        sinal(-grupo["perdidos"]["flavio"], 0),
        sinal(-grupo["perdidos"]["lula"], 0),
        sinal(grupo["variacao_diferenca_flavio_menos_lula_votos"], 0),
        dec(grupo["variacao_diferenca_pp_validos_nacionais"], 4),
    ]


def cap8_votos(c: Contexto) -> str:
    d = c.d
    cen = d["cenarios_abstencao"]
    qp = d["quem_perde"]
    eb, er, bm = (
        cen["estimativa_brasileira"],
        cen["estimativa_rio"],
        cen["brady_mcnulty"],
    )
    ebn, eba = eb["novas_realocacoes"]["central"], eb["categoria_a_ganho"]["central"]
    sal = eb["saldo_1t_para_2t"]
    dif_total = d["totais_nacionais_1t"]["flavio"] - d["totais_nacionais_1t"]["lula"]

    def barras(grupo):
        return [
            {"v": -grupo["perdidos"]["flavio"], "cor": CORES["flavio"]},
            {"v": -grupo["perdidos"]["lula"], "cor": CORES["lula"]},
        ]

    linhas = [
        {
            "rotulo": "Brasil, 0,53 ponto: novas realocações perdem",
            "barras": barras(ebn),
        },
        {"rotulo": "Brasil, 0,53 ponto: categoria A recupera", "barras": barras(eba)},
        {
            "rotulo": "Rio, 1,65 ponto: novas realocações perdem",
            "barras": barras(er["novas_realocacoes"]),
        },
        {
            "rotulo": "Rio, 1,65 ponto: categoria A recupera",
            "barras": barras(er["categoria_a_ganho"]),
        },
        {
            "rotulo": "Brady e McNulty, 1,9 ponto: novas perdem",
            "barras": barras(bm["novas_realocacoes"]),
        },
        {
            "rotulo": "Brady e McNulty, 1,9 ponto: categoria A recupera",
            "barras": barras(bm["categoria_a_ganho"]),
        },
    ]
    svg = fg.divergente(
        "Votos perdidos e recuperados em três cenários medidos",
        "Barras divergentes de votos por candidato: as novas realocações perdem comparecimento, a categoria A recupera.",
        linhas,
        [("Flávio", CORES["flavio"]), ("Lula", CORES["lula"])],
        lambda v: sinal(v, 0),
    )
    linhas_t = []
    for f in cen["fixos"]:
        pts = f["mudanca_real"]["abstencao_extra_pp"]
        linhas_t.append(
            _linha_cenario(
                f"+{dec(pts, 0)} pontos: todas com mudança real", f["mudanca_real"]
            )
        )
        linhas_t.append(
            _linha_cenario(
                f"+{dec(pts, 0)} pontos: novas realocações", f["novas_realocacoes"]
            )
        )
        linhas_t.append(
            _linha_cenario(f"+{dec(pts, 0)} pontos: categoria A", f["categoria_a"])
        )
    linhas_t += [
        _linha_cenario(
            "0,53 ponto: fora do original em 25/10",
            eb["seguem_fora_do_original_2t"]["central"],
        ),
        _linha_cenario("0,53 ponto: novas realocações", ebn),
        _linha_cenario("0,53 ponto: categoria A recupera", eba),
        _linha_cenario(
            "1,65 ponto (Rio): fora do original em 25/10",
            er["seguem_fora_do_original_2t"],
        ),
        _linha_cenario("1,65 ponto (Rio): novas realocações", er["novas_realocacoes"]),
        _linha_cenario(
            "1,65 ponto (Rio): categoria A recupera", er["categoria_a_ganho"]
        ),
        _linha_cenario(
            "1,9 ponto (Brady e McNulty): novas realocações", bm["novas_realocacoes"]
        ),
        _linha_cenario(
            "1,9 ponto (Brady e McNulty): categoria A recupera", bm["categoria_a_ganho"]
        ),
    ]
    t = tabela(
        [
            "Cenário de abstenção",
            "Urnas",
            "Votos de Flávio",
            "Votos de Lula",
            "Variação de F menos L (votos)",
            "Em pontos dos válidos nacionais",
        ],
        linhas_t,
        numericas=(1, 2, 3, 4, 5),
        rotulo="Cenários de abstenção",
        largura=860,
    )
    fixo20 = cen["fixos"][-1]["mudanca_real"]
    corpo = (
        f"<p>{esc(qp['abstencao_maior'])}</p><p>{esc(qp['comparecimento_recuperado'])}</p>"
        + f"<p><b>O saldo nacional é de centenas de votos, não de dezenas de milhares.</b> Com a magnitude brasileira ({dec(eb['magnitude_pp']['central'])} ponto, {ic(eb['magnitude_pp']['ic95'])}), as seções fora do original em 25/10 perdem {inteiro(eb['seguem_fora_do_original_2t']['central']['perdidos']['flavio'])} votos de Flávio e {inteiro(eb['seguem_fora_do_original_2t']['central']['perdidos']['lula'])} de Lula. O saldo entre os dois é de {inteiro(eb['seguem_fora_do_original_2t']['central']['variacao_diferenca_flavio_menos_lula_votos'])} votos a favor de Flávio. Se as novas realocações perdem e a categoria A recupera, o saldo vira {inteiro(abs(sal['central']['variacao_diferenca_flavio_menos_lula_votos']))} votos a favor de Lula. Com o teto do Rio ({dec(er['magnitude_pp']['central'])} ponto), a variação chega a {inteiro(er['seguem_fora_do_original_2t']['variacao_diferenca_flavio_menos_lula_votos'])} votos. A diferença entre os dois no 1º turno foi de {inteiro(dif_total)} votos.</p>"
        + f"<p>Mesmo com {dec(fixo20['abstencao_extra_pp'], 0)} pontos a mais de abstenção em todas as urnas com mudança real, a diferença entre os candidatos varia {inteiro(fixo20['variacao_diferenca_flavio_menos_lula_votos'])} votos ({dec(fixo20['variacao_diferenca_pp_validos_nacionais'], 4)} ponto dos válidos nacionais).</p>"
        + figura(
            svg,
            "Fonte: conta do laudo sobre a composição de votos do 1º turno em cada urna. Barras à esquerda: votos perdidos; à direita: votos recuperados.",
        )
        + detalhes(
            "Tabela completa dos cenários",
            t
            + nota(
                "Nas linhas de +2 a +20 pontos, a categoria A aparece com a mesma perda das demais. Se ela recuperar o comparecimento, os sinais se invertem, como nas linhas de 0,53, 1,65 e 1,9 ponto."
            ),
            aberto=True,
        )
        + contra(
            "O dano real é local",
            f"O número nacional é pequeno porque o universo é pequeno: {inteiro(eb['seguem_fora_do_original_2t']['central']['urnas'])} urnas fora do original e {inteiro(cen['composicao_1t']['novas_realocacoes']['urnas'])} novas realocações, em meio a quase 500 mil. Para quem mora na seção, o custo de não achar o prédio é integral. Inferência: o dano recai sobre quem anda mais. A literatura aponta efeito maior com a distância, e o capítulo 7 mede {pp(dose_alta(d))} acima de 5 km, com poucas urnas. O saldo nacional pequeno não torna a mudança irrelevante para esses eleitores.",
        )
        + nota(
            esc(bm["fonte"])
            + " A magnitude de Brady e McNulty entra como ordem de grandeza, de outro país e de outra eleição."
        )
        + limite(
            esc(cen["regra"])
            + " No 2º turno o voto das demais candidaturas se redistribui. Aqui, perder voto significa deixar de comparecer na mesma proporção do 1º turno."
        )
    )
    return secao(
        8,
        "votos",
        "Quantos votos estão em jogo<br><em>e quem perde.</em>",
        "Lula perde mais voto absoluto que Flávio porque teve mais voto nessas urnas. O saldo entre os dois é de centenas de votos.",
        corpo,
    )


def dose_alta(d: dict) -> float:
    f = d["efeito_1t"]["dose_resposta"]["faixas"][4]
    return f["dif_em_dif"]["mesmo_municipio"]["diferenca_pp"]["valor"]
