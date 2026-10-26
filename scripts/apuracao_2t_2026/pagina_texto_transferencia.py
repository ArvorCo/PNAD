"""Textos e tabelas do capítulo "De onde veio o voto: 1º turno → 2º turno".

Todo número sai de ``transferencia.json``; nenhum é digitado aqui. Os parágrafos
levam o selo da casa: verificado (as urnas), inferência (regressão e matriz),
hipótese (prior), achado contrário e juízo editorial.
"""

from __future__ import annotations

from html import escape

from apuracao_2026.pagina_comum import (
    caixa,
    inteiro,
    limites,
    nota,
    num,
    p,
    tabela,
)

NOME_ORIGEM = {
    "lula": "Base de Lula",
    "flavio": "Base de Flávio",
    "cury": "Augusto Cury",
    "renan": "Renan Santos",
    "caiado": "Ronaldo Caiado",
    "zema": "Romeu Zema",
    "outros": "Demais candidaturas",
    "brancos": "Brancos do 1º turno",
    "nulos": "Nulos do 1º turno",
    "abstencao": "Ausentes do 1º turno",
}
GRUPO = {
    "lula": "Lula no 1º turno",
    "flavio": "Flávio no 1º turno",
    "cury": "Augusto Cury",
    "renan": "Renan Santos",
    "caiado": "Ronaldo Caiado",
    "zema": "Romeu Zema",
    "outros": "Demais candidaturas",
    "abstencao": "Não votou no 1º turno",
    "terceira": "Terceira via somada",
    "terceira_menores": "Candidaturas com menos de 1% (Quaest)",
    "bn_ou_ausente": "Branco, nulo ou não votou",
}


def mi(v: float, casas: int = 2) -> str:
    """Milhões por extenso; abaixo de dois, "milhão" (0,72 milhão, 1,5 milhão)."""
    x = v / 1e6
    return f"{num(x, casas)} {'milhão' if abs(round(x, casas)) < 2 else 'milhões'}"


def mi_curto(v: float, casas: int = 2) -> str:
    return f"{num(v / 1e6, casas)} mi"


def pc(v: float, casas: int = 1) -> str:
    return f"{num(v, casas)}%"


def faixa(par: list[float], casas: int = 1, suf: str = "%") -> str:
    return f"{num(par[0], casas)}{suf} a {num(par[1], casas)}{suf}"


def sinal_mi(v: float) -> str:
    s = num(abs(v) / 1e6, 2)
    return ("+" if v > 0 else "−" if v < 0 else "") + s


def conta(T: dict, swing_municipios: float | None = None) -> str:
    c = T["contabilidade"]
    sw = c["h2h_flavio_2t"] - c["h2h_flavio_1t"]
    mun = (
        f"; {num(swing_municipios, 2).replace('-', '−')} nos municípios completos do capítulo anterior"
        if swing_municipios is not None
        else ""
    )
    return p(
        f"Lula foi de {inteiro(c['lula_1t'])} votos no 1º turno a {inteiro(c['lula_2t'])} no 2º, "
        f"{inteiro(c['ganho_lula'])} a mais. Flávio foi de {inteiro(c['flavio_1t'])} a {inteiro(c['flavio_2t'])}, "
        f"{inteiro(c['ganho_flavio'])} a mais. O saldo disponível tinha três fontes: os {inteiro(c['terceira_via_1t'])} votos "
        f"da terceira via, que saiu da cédula; a queda de {inteiro(c['queda_branco_nulo'])} brancos e nulos; e o aumento de "
        f"{inteiro(c['aumento_comparecimento'])} no comparecimento. Somam {inteiro(c['disponiveis'])}, exatamente o ganho "
        f"dos dois (resíduo {inteiro(c['conferencia_disponiveis_menos_ganhos'])}). Lula ficou com {pc(c['parte_lula_pct'])} "
        f"desse saldo e Flávio com {pc(c['parte_flavio_pct'])}. Mesmo que todo o ganho de Flávio viesse da terceira via e "
        f"ele não tivesse perdido um voto da base, seria só {pc(c['teto_terceira_para_flavio_se_fidelidade_100_pct'])} dela. "
        f"A parte de Flávio entre os dois foi de {pc(c['h2h_flavio_1t'], 2)} para {pc(c['h2h_flavio_2t'], 2)} "
        f"(−{num(abs(sw), 2)} pontos{mun}).",
        "verificado",
    )


def tabela_margens(T: dict) -> str:
    n = T["margens"]["nacional"]
    o, d = n["origens"], n["destinos"]
    linhas = [
        [
            "Lula",
            inteiro(o["lula"]),
            inteiro(d["lula"]),
            sinal_mi(d["lula"] - o["lula"]),
        ],
        [
            "Flávio",
            inteiro(o["flavio"]),
            inteiro(d["flavio"]),
            sinal_mi(d["flavio"] - o["flavio"]),
        ],
    ]
    terc = sum(o[k] for k in ("cury", "renan", "caiado", "zema", "outros"))
    for k in ("cury", "renan", "caiado", "zema", "outros"):
        linhas.append([NOME_ORIGEM[k], inteiro(o[k]), "", ""])
    linhas.append(["Terceira via somada", inteiro(terc), "0", sinal_mi(-terc)])
    linhas.append(
        [
            "Brancos",
            inteiro(o["brancos"]),
            inteiro(d["brancos"]),
            sinal_mi(d["brancos"] - o["brancos"]),
        ]
    )
    linhas.append(
        [
            "Nulos",
            inteiro(o["nulos"]),
            inteiro(d["nulos"]),
            sinal_mi(d["nulos"] - o["nulos"]),
        ]
    )
    linhas.append(
        [
            "Abstenção",
            inteiro(o["abstencao"]),
            inteiro(d["abstencao"]),
            sinal_mi(d["abstencao"] - o["abstencao"]),
        ]
    )
    tot1 = sum(o.values())
    tot2 = sum(d.values())
    dif = tot2 - tot1
    linhas.append(
        [
            "Eleitorado apurado",
            inteiro(tot1),
            inteiro(tot2),
            ("−" if dif < 0 else "+") + inteiro(abs(dif)) + " eleitores",
        ]
    )
    return tabela(
        ["", "1º turno (04/10)", "2º turno (25/10)", "Variação (mi)"],
        linhas,
        "As duas urnas, Brasil com exterior. Aptos = válidos + brancos + nulos + abstenção nos dois turnos. "
        f"O eleitorado nacional é o mesmo nos dois arquivos ({inteiro(n['eleitores_1t'])}); o apurado difere porque "
        f"{inteiro(n['eleitores_1t'] - n['apurado_1t'])} eleitores do 1º turno ficam fora da soma de comparecimento e "
        f"abstenção e {n['secoes_total_2t'] - n['secoes_2t']} seções do 2º turno não foram totalizadas "
        f"({inteiro(n['aptos_2t'] - n['apurado_2t'])} eleitores); a matriz reescala as origens. "
        "Fonte: presidente.json dos dois turnos, terceira_via.json para Zema.",
    )


def regressao_principal(T: dict) -> str:
    rp = T["regressao"]["robustez"][0]
    return p(
        "A urna não diz quem é quem; diz quanto cada município mudou. A variação dos votos de Lula, de Flávio e de branco e "
        "nulo entre os turnos, município a município, foi regredida contra a variação do comparecimento, com o estoque de "
        "terceira via e de branco e nulo do 1º turno como controles, efeito fixo de UF e peso pelo eleitorado "
        f"({inteiro(rp['n'])} municípios completos nos dois turnos). De cada 100 eleitores a mais na "
        f"urna, {num(rp['lula'], 1)} foram para Lula (intervalo de 95%: {num(rp['lula_ic95'][0], 1)} a "
        f"{num(rp['lula_ic95'][1], 1)}), {num(rp['flavio'], 1)} para Flávio e {num(rp['branco_nulo'], 1)} para "
        "branco ou nulo. Os três somam 100 pela própria conta, sem restrição imposta. Entre os que escolheram um dos dois, "
        f"{pc(rp['lula_entre_validos'])} foram de Lula, contra {pc(_lula_pais(T), 2)} dele nos válidos do país.",
        "inferencia",
    )


def _lula_pais(T: dict) -> float:
    d = T["margens"]["nacional"]["destinos"]
    return 100 * d["lula"] / (d["lula"] + d["flavio"])


def _retencao_flavio(T: dict) -> tuple[float, float, list[str]]:
    vals = [
        (x["publicado"]["F"], x["instituto"])
        for x in T["priors"]["linhas_publicadas"]
        if x["grupo"] == "flavio"
    ]
    lo = min(vals)
    hi = max(vals)
    return lo[0], hi[0], [lo[1], hi[1]]


def robustez_texto(T: dict) -> str:
    rob = {x["nome"]: x for x in T["regressao"]["robustez"]}
    nomes = list(rob)

    def v(i: int) -> str:
        return num(rob[nomes[i]]["lula"], 1)

    return p(
        f"A estimativa resiste a tirar as capitais ({v(3)}), a controlar pelos votos de Lula e Flávio no 1º turno ({v(4)}), "
        f"a tirar as quatro UFs em que a abstenção subiu ({v(5)}), a ficar só com os municípios de 50 mil eleitores ou mais "
        f"({v(6)}) e a dar o mesmo peso a cada município ({v(7)}). Não resiste a trocar o efeito fixo: com região no lugar "
        f"de UF, {v(1)}; sem efeito fixo, {v(2)}. Comparar municípios de UFs diferentes mistura o aumento do comparecimento "
        "com tudo o mais que separa uma UF da outra.",
        "inferencia",
    )


def tabela_robustez(T: dict) -> str:
    linhas = []
    for x in (
        T["regressao"]["robustez"]
        + T["regressao"]["secoes_resumo"]
        + (T["regressao"].get("secoes_amostra") or [])
    ):
        linhas.append(
            [
                escape(x["nome"]),
                inteiro(x["n"]),
                num(x["lula"], 1),
                faixa(x["lula_ic95"], 1, ""),
                num(x["flavio"], 1),
                num(x["branco_nulo"], 1),
                num(x["terceira_flavio"], 1),
            ]
        )
    return tabela(
        [
            "Especificação",
            "Unidades",
            "Lula por 100 a mais",
            "IC 95%",
            "Flávio",
            "Branco e nulo",
            "Terceira via a Flávio (por 100)",
        ],
        linhas,
        "Regressão ecológica da variação entre turnos; erro-padrão robusto por agrupamento em UF. As linhas de seções usam "
        + (
            "todas as seções casadas com o 1º turno e, para comparação, a amostra sorteada antes da votação (peso de desenho); "
            "grupos com uma seção só (cidades do exterior) saem dos efeitos fixos de município e zona. "
            if _censo(T)
            else "a amostra de seções sorteada antes da votação, com peso de desenho. "
        )
        + "Fonte: transferencia.json (regressao).",
    )


def _censo(T: dict) -> bool:
    return (T["regressao"].get("secoes") or {}).get("fonte") == "completo"


def secoes_contrario(T: dict) -> str:
    s = T["regressao"]["secoes_resumo"]
    if not s:
        return ""
    sec = T["regressao"]["secoes"]
    uf, mun, zona = s
    rp = T["regressao"]["robustez"][0]
    base = (
        f"Em todas as {inteiro(sec['n_casadas'])} seções casadas com o 1º turno (censo dos boletins; "
        f"{inteiro(sum(sec['excluidas'].values()))} ficaram fora por falta de par ou eleitorado alterado)"
        if _censo(T)
        else f"Na amostra de {inteiro(sec['n_casadas'])} seções sorteadas antes da votação"
    )
    amostra = T["regressao"].get("secoes_amostra") or []
    am_mun = next((x for x in amostra if "município" in x["nome"]), None)
    am_txt = (
        f" A amostra de 7.539 seções sorteada antes da votação dava {num(am_mun['lula'], 1)} entre seções do mesmo município; "
        "com todas as seções, a distância entre as escalas encolheu e os intervalos passaram a se cruzar."
        if am_mun and _censo(T)
        else ""
    )
    lo = min(mun["lula_ic95"][0], zona["lula_ic95"][0])
    hi = rp["lula_ic95"][1]
    return nota(
        "contrario",
        f"Na escala da seção, a resposta cai. {base}, cada uma comparada com ela mesma no 1º turno, a conta dá "
        f"{num(uf['lula'], 1)} com efeito fixo de UF, {num(mun['lula'], 1)} entre seções do mesmo município (intervalo de "
        f"{faixa(mun['lula_ic95'], 1, '')}) e {num(zona['lula'], 1)} entre seções da mesma zona, contra {num(rp['lula'], 1)} "
        f"entre municípios.{am_txt} O dado cabe em duas leituras e não escolhe entre elas: o município carrega efeito de "
        "contexto (onde a campanha de Lula mobilizou mais, também converteu mais quem já votava), e a seção carrega o vaivém de "
        "quem vota ou falta por acaso, que vota como a própria seção. A faixa defensável vai de "
        f"{num(lo, 0)} a {num(hi, 0)} por 100.",
        "A escala ainda muda a resposta.",
    )


def por_uf_texto(T: dict) -> str:
    ufs = [u for u in T["regressao"]["por_uf"] if "L" in u]
    fora = [u["uf"] for u in ufs if u["L"]["b"] > 1 or u["L"]["b"] < 0]
    mx = max(ufs, key=lambda u: u["L"]["b"])
    mn = min(ufs, key=lambda u: u["L"]["b"])
    return p(
        f"Dentro das UFs, entre os próprios municípios, a estimativa vai de {num(100 * mn['L']['b'], 1)} em {mn['uf']} a "
        f"{num(100 * mx['L']['b'], 1)} em {mx['uf']}. Acima de 100 ou abaixo de 0 não existe como transferência"
        + (
            f"; {', '.join(fora)} {'passa' if len(fora) == 1 else 'passam'} desse limite, o que mostra a regressão medindo o "
            "tipo de município, não o eleitor"
            if fora
            else ""
        )
        + ". Os intervalos das UFs pequenas são largos.",
        "inferencia",
    )


def ecologica(T: dict) -> str:
    c = T["regressao"]["principal"]["coef"]
    return caixa(
        "io",
        "Por que isto não identifica o eleitor.",
        f"<p>A mesma regressão diz que cada 100 votos brancos e nulos do 1º turno vêm com {num(-100 * c['F']['branco_nulo_1t']['b'], 0)} "
        f"votos a menos para Flávio e {num(100 * c['L']['branco_nulo_1t']['b'], 0)} a mais para Lula. Nenhum eleitor de branco ou "
        "nulo do 1º turno tira voto de Flávio no 2º: o coeficiente negativo mede o tipo de município em que havia muito branco e "
        "nulo, onde Lula cresceu mais. Toda conta desta seção vai de agregado para agregado.</p>",
    )


def rotatividade(T: dict) -> str:
    r = T["rotatividade"]
    s = r["secoes"]["nacional"]
    m = r["municipal"]
    c = r["central"]
    dobrada = T["ipf"]["sensibilidades"]["rotatividade_dobrada"]["metricas"]["voltaram"]
    volta = T["ipf"]["central"]["metricas"]
    rp = T["regressao"]["robustez"][0]
    return p(
        f"A urna mostra o saldo do comparecimento: {inteiro(c['liquido'])} eleitores a mais. O fluxo bruto é maior, porque há "
        "quem votou no 1º turno e faltou no 2º, e ninguém publica a lista. O piso sai das seções: dentro de uma seção, entrou pelo "
        "menos o aumento e saiu pelo menos a queda. "
        + (
            "Somado em todas as seções, esse piso é de "
            if _censo(T)
            else "Na amostra, esse piso extrapolado ao país é de "
        )
        + f"{mi(s.get('entrada_min_votos', 0))} de ausentes do 1º turno que votaram no 2º "
        f"({pc(100 * s['entrada_min_sobre_ausentes'])} dos ausentes) e {mi(s.get('saida_min_votos', 0))} de votantes que "
        f"faltaram; entre municípios, o piso é mais baixo ({mi(m['entrada_min_votos'])} e {mi(m['saida_min_votos'])}). A matriz "
        f"usa o menor fluxo compatível com o piso das seções e com o saldo real de cada UF: entrada de {mi(c['entrada'])} e "
        f"saída de {mi(c['saida'])}. Como parte de quem saiu votava, a divisão de quem voltou fica abaixo da do saldo: de cada "
        f"100 que voltaram, {num(volta['voltaram_lula_pct'], 0)} foram para Lula, contra {num(rp['lula'], 0)} por 100 eleitores "
        f"do saldo. Pode ter sido mais gente; com o dobro de rotatividade, {mi(dobrada)} teriam voltado.",
        "inferencia",
    )


def metodo_matriz(T: dict) -> str:
    c = T["ipf"]["central"]
    d = c["diagnostico"]
    return nota(
        "hipotese",
        "A matriz segue o método fixo da casa. Primeiro, a prior de cada linha: as bases de Lula e Flávio pela média da Nexus "
        "(24/10, p. 23) e da Quaest (21/10, p. 20); cada candidatura de terceira via pela média da Nexus, da Quaest e do Datafolha "
        "(22/10, p. 5) que a publicam; branco e nulo do 1º turno com metade continuando branco ou nulo e o resto na proporção da "
        "linha mista da Quaest; a mesma fração de cada eleitorado do 1º turno faltando no 2º. A linha de quem faltou no 1º turno "
        "vem da regressão e fica fixa. Depois, o ajuste proporcional iterativo, UF a UF, até bater exatamente as duas urnas "
        f"(desvio máximo de {num(max(c['confere']['linhas_max_desvio_votos'], c['confere']['colunas_max_desvio_votos']), 3)} voto "
        f"em linhas e colunas; até {inteiro(d['iteracoes_max'])} iterações). As origens "
        f"do 1º turno foram reescaladas para o eleitorado apurado do 2º (fator de {num(d['escala_min'], 5)} a "
        f"{num(d['escala_max'], 5)}). Nenhum zero estrutural: todo eleitor pode, em tese, fazer qualquer caminho, e zero de "
        "pesquisa vira piso de 0,2% da linha.",
        "Como a matriz foi montada.",
    )


def tabela_sensibilidades(T: dict) -> str:
    linhas = []
    for s in T["ipf"]["sensibilidades"].values():
        m = s["metricas"]
        linhas.append(
            [
                escape(s["nome"]),
                num(m["voltaram"] / 1e6, 2),
                pc(m["voltaram_lula_pct"]),
                pc(m["terceira"]["flavio_pct"]),
                pc(m["terceira"]["flavio_entre_finalistas"]),
                num(m["razao_consolidacao_flavio_lula"], 2),
                f"{num(m['fidelidade_lula'], 1)} / {num(m['fidelidade_flavio'], 1)}",
                pc(m["bn1_continua_bn_pct"]),
                num(m["explica_pp"], 2),
            ]
        )
    return tabela(
        [
            "Cenário",
            "Voltaram (mi)",
            "Deles, a Lula",
            "Terceira via a Flávio",
            "Idem, entre finalistas",
            "Razão Flávio : Lula fora da base",
            "Fidelidade Lula / Flávio",
            "Branco e nulo que continuam",
            "Explica (pp)",
        ],
        linhas,
        "Cada linha troca uma peça da prior e refaz o ajuste UF a UF. A última é diagnóstico: deixa o IPF mexer também na linha "
        "da regressão. Fonte: transferencia.json (ipf.sensibilidades).",
    )


def sobrevive(T: dict) -> str:
    inv = T["ipf"]["invariantes"]
    m = T["ipf"]["central"]["metricas"]
    pcand = inv["por_candidatura_flavio_pct"]
    return p(
        "O que as margens impõem e sobrevive a toda troca de prior: Lula ganhou fora da própria base de "
        f"{mi(inv['ganho_fora_base_lula'][0])} a {mi(inv['ganho_fora_base_lula'][1])}, Flávio de "
        f"{mi(inv['ganho_fora_base_flavio'][0])} a {mi(inv['ganho_fora_base_flavio'][1])}; a razão de consolidação fica entre "
        f"{num(inv['razao_consolidacao'][0], 2)} e {num(inv['razao_consolidacao'][1], 2)} para 1 (central "
        f"{num(m['razao_consolidacao_flavio_lula'], 2)}). Para cada voto que Flávio buscou fora da base, Lula buscou de "
        f"{num(1 / inv['razao_consolidacao'][1], 1)} a {num(1 / inv['razao_consolidacao'][0], 1)}. A terceira via deu a "
        f"Flávio de {faixa(inv['terceira_flavio_pct'])} do seu estoque em todos os cenários, e o "
        f"comparecimento explica de {num(inv['explica_pp'][0], 2)} a {num(inv['explica_pp'][1], 2)} ponto da queda dele.",
        "inferencia",
    ) + p(
        "O que depende da prior e não deve ser lido como medição: o corte candidato a candidato (a parte de Flávio vai de "
        f"{faixa(pcand['cury'], 0)} no eleitorado de Cury, de {faixa(pcand['renan'], 0)} no de Renan Santos, de "
        f"{faixa(pcand['caiado'], 0)} no de Caiado e de {faixa(pcand['zema'], 0)} no de Zema), a fidelidade de cada base "
        f"(Flávio de {faixa(inv['fidelidade_flavio'])}) e quanto do branco e nulo do 1º turno continuou branco ou nulo "
        f"({faixa(inv['bn1_continua_bn_pct'], 0)}).",
        "hipotese",
    )


def sem_informacao(T: dict) -> str:
    s = T["ipf"]["sem_informacao"]
    return p(
        "Prova de que o ajuste não inventa conhecimento: com uma prior sem informação nenhuma, as mesmas margens mandariam "
        f"{mi(s['voltaram'], 1)} de ausentes do 1º turno às urnas e devolveriam a Lula só {pc(s['fidelidade_lula'])} dos "
        "próprios eleitores. O IPF só fecha a conta da prior; o que a matriz diz além das margens vem das pesquisas e da "
        "regressão, com as páginas citadas.",
        "inferencia",
    )


def tabela_decomposicao(T: dict) -> str:
    sens = T["ipf"]["sensibilidades"]
    chaves = [k for k in sens if k != "abstencao_ajustada"]
    m = T["ipf"]["central"]["metricas"]
    dec = m["decomposicao_margem_flavio_menos_lula"]
    grupos = [
        ("Base de Flávio", ("flavio",)),
        ("Base de Lula", ("lula",)),
        ("Terceira via", ("cury", "renan", "caiado", "zema", "outros")),
        ("Branco e nulo do 1º turno", ("brancos", "nulos")),
        ("Ausentes do 1º turno", ("abstencao",)),
    ]
    linhas = []
    for nome, ks in grupos:
        cen = sum(dec[k] for k in ks)
        vals = [
            sum(
                sens[c]["metricas"]["decomposicao_margem_flavio_menos_lula"][k]
                for k in ks
            )
            for c in chaves
        ]
        linhas.append(
            [nome, sinal_mi(cen), f"{sinal_mi(min(vals))} a {sinal_mi(max(vals))}"]
        )
    total = m["margem_2t"] - m["margem_1t"]
    linhas.append(["Total (imposto pelas urnas)", sinal_mi(total), sinal_mi(total)])
    return tabela(
        ["Origem", "Matriz central (mi)", "Faixa nas trocas de prior (mi)"],
        linhas,
        "Contribuição de cada origem à mudança da diferença Flávio menos Lula entre os turnos, em milhões de votos "
        "(negativo: a favor de Lula). "
        "Só o total é imposto pelas urnas; a divisão depende da prior. Fonte: transferencia.json.",
    )


def tabela_pesquisas(T: dict) -> str:
    fontes = T["priors"]["fontes"]
    linhas = []
    for x in T["priors"]["linhas_publicadas"]:
        if x["grupo"] != "terceira":
            continue
        v = x["publicado"]
        linhas.append(
            [
                escape(f"{x['instituto']}, {x['campo']}"),
                str(x["pagina"]),
                escape(fontes[x["fonte"]]["registro"]),
                num(v["F"], 1),
                num(v["L"], 1),
                num(v["BN"], 1),
                num(v["NS"], 1),
                num(x["flavio_entre_finalistas"], 1),
            ]
        )
    return tabela(
        [
            "Pesquisa",
            "Página",
            "Registro",
            "Flávio",
            "Lula",
            "Branco e nulo",
            "Indeciso",
            "Flávio entre os dois",
        ],
        linhas,
        "Eleitorado da terceira via no 1º turno, voto lembrado na mesma entrevista, intenção de 2º turno. Percentuais publicados; "
        "bases dos grupos não publicadas. Fonte: PDFs com SHA-256 em transferencia.json (priors.fontes).",
    )


def tabela_linhas_candidato(T: dict) -> str:
    fontes = T["priors"]["fontes"]
    linhas = []
    for x in T["priors"]["linhas_publicadas"]:
        if x["grupo"] == "terceira":
            continue
        v = x["publicado"]
        linhas.append(
            [
                escape(str(GRUPO.get(x["grupo"]) or x["grupo"])),
                escape(f"{x['instituto']}, {x['campo']}"),
                str(x["pagina"]),
                escape(fontes[x["fonte"]]["registro"]),
                num(v["F"], 1),
                num(v["L"], 1),
                num(v["BN"], 1),
                num(v["NS"], 1),
            ]
        )
    return tabela(
        [
            "Grupo do 1º turno",
            "Pesquisa",
            "Página",
            "Registro",
            "Flávio",
            "Lula",
            "Branco e nulo",
            "Indeciso",
        ],
        linhas,
        "Todas as linhas transcritas, conferidas na imagem da página. Na Quaest, branco e nulo inclui quem diz que não vai votar.",
    )


def terceira_contrario(T: dict) -> str:
    pt = T["pesquisas"]["terceira_via_2t"]
    m = T["ipf"]["central"]["metricas"]
    inv = T["ipf"]["invariantes"]
    eq = [e for e in pt.get("equilibrio", []) if e]
    ondas = pt["linhas"]
    n_inst = len({x["instituto"] for x in ondas})
    r_lo, r_hi, r_inst = _retencao_flavio(T)
    sint = T["pesquisas"].get("sintese_pre_1t")
    sint_txt = (
        f" A síntese da casa de 04/10, antes do 1º turno, dizia que {pc(100 * sint['fracao_flavio'], 0)} da queda da terceira via "
        "reapareceria em Flávio."
        if sint
        else ""
    )
    eq_txt = ""
    if len(eq) == 2:
        eq_txt = (
            f" Para a matriz chegar ao menor número publicado ({pc(eq[0]['alvo_pct'])}), Flávio teria de ter retido só "
            f"{pc(eq[0]['fidelidade_flavio'])} da própria base, com {mi(eq[0]['flavio_para_lula'])} de eleitores dele indo a Lula; "
            f"para chegar ao maior ({pc(eq[1]['alvo_pct'])}), {pc(eq[1]['fidelidade_flavio'])}. As pesquisas mediram a retenção "
            f"de Flávio entre {pc(r_lo, 0)} ({r_inst[0]}) e {pc(r_hi, 0)} ({r_inst[1]})."
        )
    return nota(
        "contrario",
        f"As pesquisas mediram a terceira via indo para Flávio: de {faixa(pt['flavio_do_estoque'])} do eleitorado dela e de "
        f"{faixa(pt['flavio_entre_finalistas'])} entre os que escolheram um finalista, em {len(ondas)} ondas de {n_inst} "
        "institutos."
        f"{sint_txt} Na matriz, Flávio fica com {pc(m['terceira']['flavio_pct'])} do estoque "
        f"({pc(m['terceira']['flavio_entre_finalistas'])} entre os que escolheram um finalista), e em nenhuma troca de prior passa "
        f"de {pc(inv['terceira_flavio_pct'][1])}.{eq_txt} O menor número publicado fica perto do alcance da matriz; os "
        "maiores, não.",
        "A terceira via não foi para Flávio como as pesquisas mediram.",
    )


def terceira_regressao(T: dict) -> str:
    rob = T["regressao"]["robustez"]
    sec = T["regressao"]["secoes_resumo"]
    uf_fe = [x["terceira_flavio"] for x in rob if "UF" in x["nome"]]
    sem = next(x["terceira_flavio"] for x in rob if x["nome"].startswith("Sem efeito"))
    sec_txt = (
        f" e de {num(min(x['terceira_flavio'] for x in sec), 1)} a {num(max(x['terceira_flavio'] for x in sec), 1)} na escala da seção"
        if sec
        else ""
    )
    return p(
        "A regressão ecológica, que não usa pesquisa nenhuma, conta uma história próxima e mais frágil: por 100 votos de terceira "
        f"via, Flávio leva de {num(min(uf_fe), 1)} a {num(max(uf_fe), 1)} com efeito fixo de UF{sec_txt}, no piso do que as "
        f"pesquisas mediram, mas {num(sem, 1)} sem efeito fixo. A matriz e a regressão concordam no sentido; a regressão sozinha "
        "não sustentaria o número.",
        "inferencia",
    )


def reserva(T: dict) -> str:
    res = T["pesquisas"].get("reserva_voto_util")
    p1 = T["pesquisas"].get("pesquisas_1t")
    m = T["ipf"]["central"]["metricas"]
    inv = T["ipf"]["invariantes"]
    c = T["contabilidade"]
    if not res:
        return ""
    urna = 100 * c["flavio_1t"] / (c["lula_1t"] + c["flavio_1t"] + c["terceira_via_1t"])
    p1_txt = (
        f" Parte disso já tinha vindo no 1º turno: as pesquisas finais davam a Flávio {pc(p1['flavio_pesquisas_validos'])} dos "
        f"válidos, em média, e a urna deu {pc(urna)}."
        if p1
        else ""
    )
    return p(
        f"O mapa do voto útil de 26/09 somava {mi(res['eleitores'], 1)} de eleitores que escolhiam Flávio no 2º turno e ainda não "
        f"no 1º, na média de três casas.{p1_txt} Entre os turnos, o saldo de Flávio foi de {mi(c['ganho_flavio'])}; fora da própria "
        f"base, {mi(m['ganho_fora_base_flavio'])} pela matriz ({mi(inv['ganho_fora_base_flavio'][0])} a "
        f"{mi(inv['ganho_fora_base_flavio'][1])} nas trocas de prior).",
        "inferencia",
    )


def resposta(T: dict) -> str:
    r = T["resposta"]
    sec = (
        f"; na escala da seção, {pc(r['secoes_voltaram_lula_pct'], 0)}, e o comparecimento explicaria só "
        f"{num(r['secoes_explica_pp'], 2)} ponto"
        if "secoes_voltaram_lula_pct" in r
        else ""
    )
    return (
        '<aside class="io resposta-tr"><b>A resposta, em duas frases.</b>'
        f"<p>Dos {mi(r['voltaram_milhoes'] * 1e6)} que faltaram no 1º turno e votaram no 2º (o mínimo compatível com as seções), "
        f"de {pc(r['voltaram_lula_ic'][0], 0)} a {pc(r['voltaram_lula_ic'][1], 0)} teriam ido para Lula (estimativa ecológica, "
        f"intervalo de 95% da regressão entre municípios{sec}), e isso explica de {num(r['explica_pp_ic'][0], 2)} a "
        f"{num(r['explica_pp_ic'][1], 2)} ponto (central {num(r['explica_pp'], 2)}) dos {num(abs(r['swing_h2h_pp']), 2)} pontos "
        "que Flávio perdeu na parte entre os dois.</p>"
        f"<p>A terceira via rendeu a Flávio {pc(r['terceira_flavio_pct'])} do seu estoque (de "
        f"{faixa(r['terceira_flavio_faixa'])} nas trocas de prior) contra {faixa(r['pesquisas_flavio_do_estoque'])} que as "
        f"pesquisas mediram ({faixa(r['pesquisas_flavio_entre_finalistas'], 0)} entre os que escolheram um finalista).</p></aside>"
    )


def juizo(T: dict) -> str:
    inv = T["ipf"]["invariantes"]
    return nota(
        "juizo",
        "O voto que decidiu o 2º turno já estava na urna em 4 de outubro. Quem voltou para votar pesou no máximo "
        f"{num(inv['explica_pp'][1], 2)} ponto; o resto se decidiu entre eleitores que já tinham votado, na terceira via, no "
        "branco e nulo e na margem da própria base de Flávio. Para a campanha derrotada, o dado aponta para conversão, não para "
        "mobilização.",
        "Leitura da casa.",
    )


def limites_cap(T: dict) -> str:
    return limites(
        [
            "Regressão ecológica: vai de agregado para agregado e não identifica o voto de nenhum eleitor. A resposta muda com a "
            "escala (município ou seção) e com o efeito fixo (UF, região ou nenhum).",
            "A rotatividade bruta não é observada. A matriz usa o mínimo compatível com as seções; com mais rotatividade, voltam "
            "mais eleitores e a parte de Lula entre eles cai, por construção, para manter o saldo que a regressão mede.",
            "As linhas das pesquisas são voto lembrado do 1º turno cruzado com intenção de 2º turno, na mesma entrevista, sem bases "
            'publicadas por grupo. As pesquisas da última semana superestimaram Flávio em média (<a href="#pesquisas">capítulo '
            "das pesquisas</a>); usá-las como prior "
            "puxa a matriz para ele, e o ajuste às urnas desfaz parte disso.",
            "A matriz soma 28 ajustes (27 UFs e exterior) com a mesma prior em todas, mudando só a rotatividade. Diferenças "
            "regionais de transferência entram pelas margens de cada UF, não por linhas regionais das pesquisas.",
            "Brancos e nulos foram separados pela proporção de cada UF no 2º turno; a separação é hipótese.",
            "Nada aqui é prova de irregularidade. Pede explicação, não prova.",
        ],
        "Reprodução: <code>python3 scripts/apuracao-2t-2026-transferencia.py</code>; memorando em "
        "<code>analysis/apuracao_2t_2026/dados/transferencia.md</code>.",
    )


CSS = (
    "<style>.resposta-tr{border-left-width:6px;font-size:17px}"
    ".resposta-tr p{margin:8px 0 0}"
    "#transferencia .table-scroll table{font-variant-numeric:tabular-nums}"
    "#transferencia details.limites,#transferencia code{overflow-wrap:anywhere}</style>"
)
