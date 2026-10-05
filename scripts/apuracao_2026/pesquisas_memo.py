"""Memorando em pt-BR gerado de pesquisas_vs_urna.json e voto_util.json.

Nenhum número é digitado: todos saem dos dois payloads. O texto editorial é
fixo e foi escrito para sobreviver a citação hostil; quando um número muda, a
frase acompanha.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

BRASILIA = timezone(timedelta(hours=-3))

MESES = {
    "01": "jan",
    "02": "fev",
    "03": "mar",
    "04": "abr",
    "05": "mai",
    "06": "jun",
    "07": "jul",
    "08": "ago",
    "09": "set",
    "10": "out",
    "11": "nov",
    "12": "dez",
}


def num(x: float | None, casas: int = 2, sinal: bool = False) -> str:
    """Número em pt-BR, com sinal de menos tipográfico e ``+`` opcional."""
    if x is None:
        return "n/d"
    s = f"{abs(x):,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if round(x, casas) < 0:
        return f"−{s}"
    if sinal and round(x, casas) > 0:
        return f"+{s}"
    return s


MINUSCULAS = frozenset({"de", "da", "do", "das", "dos", "e"})


def nome_proprio(nome: str) -> str:
    """Caixa de título com partículas em minúscula: SAMANDA DE LULA -> Samanda de Lula."""
    partes = nome.lower().split()
    return " ".join(
        p if i and p in MINUSCULAS else p[:1].upper() + p[1:]
        for i, p in enumerate(partes)
    )


def milhar(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def hora_brasilia(iso: str) -> str:
    """'2026-10-05T05:59:31.000Z' -> '05/10 às 02:59 (Brasília)'."""
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(BRASILIA)
    return f"{dt:%d/%m} às {dt:%H:%M} (Brasília)"


def pct(x: float, casas: int = 0) -> str:
    return f"{num(100 * x, casas)}%"


def campo(c: dict) -> str:
    i, f = c["inicio"], c["fim"]
    if i[5:7] == f[5:7]:
        return f"{i[8:]}–{f[8:]}/{f[5:7]}"
    return f"{i[8:]}/{i[5:7]}–{f[8:]}/{f[5:7]}"


def tabela(cab: list[str], linhas: list[list[str]]) -> str:
    out = ["| " + " | ".join(cab) + " |", "|" + "|".join("---" for _ in cab) + "|"]
    out += ["| " + " | ".join(x) + " |" for x in linhas]
    return "\n".join(out)


def _ranking(d: dict) -> str:
    por_id = {x["id"]: x for x in d["pesquisas"]}
    linhas = []
    for i, pid in enumerate(d["ranking_publicado"], 1):
        x = por_id[pid]
        p, r = x["publicado"], x["reponderado"]
        linhas.append(
            [
                str(i),
                x["instituto"] + (" ●" if x["ultima_onda_da_casa"] else ""),
                campo(x["campo"]),
                num(p["validos"]["flavio"]),
                num(p["validos"]["lula"]),
                num(p["erro_pp"]["flavio"], sinal=True),
                num(p["erro_pp"]["lula"], sinal=True),
                num(p["diferenca_lula_menos_flavio"]["erro"], sinal=True),
                (
                    num(r["diferenca_lula_menos_flavio"]["erro"], sinal=True)
                    if r
                    else "sem renda"
                ),
                (
                    num(p["eam_candidatos_pp"])
                    if p["eam_candidatos_pp"] is not None
                    else "não abre"
                ),
                num(x["margem_95_diferenca_aas_pp"]),
            ]
        )
    cab = [
        "#",
        "Instituto",
        "Campo",
        "Flávio",
        "Lula",
        "Erro F",
        "Erro L",
        "Erro L−F",
        "Erro L−F reponderado",
        "EAM 5",
        "Margem AAS",
    ]
    return tabela(cab, linhas)


def _referencias(d: dict) -> str:
    m = d["medias"]
    c = d["previsao_casa"]
    r22 = d["referencia_2022"]
    linhas = []
    for chave in (
        "ultimas_ondas_publicado",
        "agregador_publicado",
        "agregador_reponderado",
    ):
        x = m[chave]
        linhas.append(
            [
                x["nome"],
                num(x["validos_blocos"]["flavio"]),
                num(x["validos_blocos"]["lula"]),
                num(x["validos_blocos"]["terceira_via"]),
                num(x["diferenca_lula_menos_flavio"]["erro"], sinal=True),
            ]
        )
    for nome, bloco in (
        ("Central da Arvor (04/10)", c["central"]),
        ("Âncora dinâmica (DLM)", c["dlm"]),
    ):
        v = bloco["validos"]
        linhas.append(
            [
                nome,
                num(v["flavio"]),
                num(v["lula"]),
                num(v["terceira_via"]),
                num(bloco["erro_diferenca_lula_menos_flavio"], sinal=True),
            ]
        )
    linhas.append(
        [
            f"Erro comum de 2022 ({r22['n_casas']} casas, L−Bolsonaro)",
            "",
            "",
            "",
            num(r22["erro_comum_diferenca_lula_menos_bolsonaro"], sinal=True),
        ]
    )
    return tabela(["Referência", "Flávio", "Lula", "Terceira via", "Erro L−F"], linhas)


def _secao_proximidade(d: dict) -> str:
    por_id = {x["id"]: x for x in d["pesquisas"]}
    finais = [
        por_id[i] for i in d["ranking_publicado"] if por_id[i]["ultima_onda_da_casa"]
    ]
    melhores = [
        x
        for x in finais
        if abs(x["publicado"]["diferenca_lula_menos_flavio"]["erro"])
        <= abs(finais[0]["publicado"]["diferenca_lula_menos_flavio"]["erro"]) + 0.05
    ]
    nomes = " e ".join(x["instituto"] for x in melhores)
    erros_melhores = " e ".join(
        num(abs(x["publicado"]["diferenca_lula_menos_flavio"]["erro"]))
        for x in melhores
    )
    efeitos = ", ".join(
        f"{x['instituto']} {num(x['efeito_casa_pre_eleicao_pp'], 1, sinal=True)}"
        for x in melhores
        if x["efeito_casa_pre_eleicao_pp"] is not None
    )
    res = d["resumo_ultimas_ondas"]["publicado"]
    r22 = d["referencia_2022"]
    rr = d["resumo_ultimas_ondas"]
    return f"""## 3. Proximidade não é acerto

**Parágrafo a publicar.** Na última onda, {nomes} terminaram a {erros_melhores} ponto da diferença entre Lula e Flávio na urna. Isso não prova que medem melhor. Uma eleição é uma observação. Em 2022 a média de {r22['n_casas']} casas superestimou a vantagem de Lula em {num(r22['erro_comum_diferenca_lula_menos_bolsonaro'], sinal=True)} pontos dos válidos; em 2026 a última onda de {res['n']} casas superestimou em {num(res['media'], sinal=True)}, na mesma direção. Antes da urna, as casas mais próximas eram justamente as que mais se afastavam das demais a favor de Flávio (desvio relativo medido pela Arvor antes da eleição: {efeitos} pontos na diferença L−F). Chegaram perto porque o erro comum foi grande e contrário ao desvio delas. Com os erros espalhados como foram (média {num(res['media'], sinal=True)}, desvio {num(res['desvio_padrao'])} entre casas), a chance de ao menos uma de {res['n']} casas cair a meio ponto da urna só pela dispersão seria de {pct(rr['prob_alguma_casa_a_meio_ponto_por_acaso'])}. Quem chegou mais perto desta vez errou na direção certa desta vez.

- Dois testes para chamar uma casa de certeira: o erro na diferença dentro da margem da própria amostra em 2026 (passam {res['n'] - res['fora_da_margem_aas']} das {res['n']} últimas ondas, sob amostragem simples) e o mesmo em 2022. {_dois_testes(d)}
- Verificado: erros de cada onda contra o TSE, na tabela acima.
- Inferido: o desvio relativo de cada casa medido antes da urna ordena os erros (correlação {num(rr['correlacao_efeito_casa_pre_eleicao_com_erro'])} em {rr['n_correlacao']} casas), mas por construção não diz nada do nível. Descontado esse desvio, o componente comum foi {num(rr['componente_comum_descontado_efeito_casa_pp'], sinal=True)} pontos.
- Hipótese ilustrativa: a chance de {pct(rr['prob_alguma_casa_a_meio_ponto_por_acaso'])} supõe erros normais independentes com a média e o desvio observados.
"""


def _dois_testes(d: dict) -> str:
    pn = d["painel_2022_2026"]
    ok = pn["dentro_da_margem_nas_duas"]
    linhas = {r["casa_2026"]: r for r in pn["linhas"]}
    if ok:
        detalhe = "; ".join(
            f"{c}: {num(linhas[c]['erro_2022_lula_menos_bolsonaro'], sinal=True)} em 2022 e "
            f"{num(linhas[c]['erro_2026_lula_menos_flavio'], sinal=True)} em 2026"
            for c in ok
        )
        quem = f"Só {' e '.join(ok)} passa nos dois ({detalhe})."
    else:
        quem = "Nenhuma casa passa nos dois."
    return (
        f"{quem} Das {pn['n_casas']} casas com onda final arquivada nas duas eleições, "
        f"{'todas' if pn['mesmo_sinal_nas_duas'] == pn['n_casas'] else pn['mesmo_sinal_nas_duas']}"
        " repetiram o sinal do erro e "
        f"{len(pn['superestimaram_lula_nas_duas'])} superestimaram Lula nas duas (correlação "
        f"{num(pn['correlacao_erros'])} entre os erros das duas eleições). Com o erro comum duas "
        "vezes a favor de Lula, uma casa inclinada para o outro lado parece certeira duas vezes. "
        "Separar método de inclinação exige uma eleição em que o erro comum vá para o outro lado."
    )


def _secao_erro_comum(d: dict) -> str:
    res = d["resumo_ultimas_ondas"]
    p, r = res["publicado"], res["reponderado"]
    r22 = d["referencia_2022"]
    linhas = [
        [
            "2022, última onda de cada instituto",
            str(r22["n_casas"]),
            num(r22["erro_comum_diferenca_lula_menos_bolsonaro"], sinal=True),
            num(r22["mediana"], sinal=True),
            num(r22["desvio_entre_casas"]),
            f"{r22['casas_que_superestimaram_lula']} de {r22['n_casas']}",
        ],
        [
            "2026, última onda, publicada",
            str(p["n"]),
            num(p["media"], sinal=True),
            num(p["mediana"], sinal=True),
            num(p["desvio_padrao"]),
            f"{p['positivos']} de {p['n']}",
        ],
        [
            "2026, última onda, reponderada",
            str(r["n"]),
            num(r["media"], sinal=True),
            num(r["mediana"], sinal=True),
            num(r["desvio_padrao"]),
            f"{r['positivos']} de {r['n']}",
        ],
    ]
    modos = res["por_modo_publicado"]
    txt_modo = "; ".join(
        f"{k} {num(v['media'], sinal=True)} ({v['n']} casas)" for k, v in modos.items()
    )
    return f"""## 4. O erro comum se repetiu

{tabela(["Conjunto", "Casas", "Erro médio L−F", "Mediana", "Desvio entre casas", "Superestimaram Lula"], linhas)}

- Verificado: o sinal e o tamanho do erro comum de 2022 se repetiram. Em 2022 o erro foi concentrado em Bolsonaro; em 2026, em Flávio (seção 6).
- Verificado: a dispersão entre casas ({num(p['desvio_padrao'])} pontos) é maior que a esperada só pela amostragem ({num(p['desvio_esperado_so_amostragem_aas_pp'])} sob amostragem simples, {num(p['desvio_esperado_so_amostragem_deff_pp'])} com efeito de desenho 1,5). {p['fora_da_margem_aas']} das {p['n']} últimas ondas erraram a diferença por mais que a margem de 95% da própria amostra sob amostragem simples. Efeito de casa existe e é grande.
- Descritivo, sem teste: erro médio por modo de coleta, {txt_modo}. Com duas a sete casas por grupo, isso não separa modo de casa.
"""


def _secao_reponderacao(d: dict) -> str:
    e = d["efeito_reponderacao"]
    m = d["medias"]
    ap, ar = m["agregador_publicado"], m["agregador_reponderado"]
    linhas = []
    for x in e["por_onda"]:
        if not x["ultima_onda_da_casa"]:
            continue
        nota = {
            "hipotese_onda_anterior": "perfil da onda anterior (hipótese)",
            "perfil_ponderado_reconstituido": "perfil reconstituído",
        }.get(x["perfil_renda"] or "", "")
        linhas.append(
            [
                x["instituto"],
                num(x["erro_dif_publicado"], sinal=True),
                num(x["erro_dif_reponderado"], sinal=True),
                num(x["deslocamento_lula_menos_flavio"], sinal=True),
                x["direcao"],
                nota,
            ]
        )
    u = e["ultimas_ondas"]
    afastaram = [
        x["instituto"]
        for x in e["por_onda"]
        if x["ultima_onda_da_casa"] and x["direcao"] == "afastou"
    ]
    return f"""## 5. O que a reponderação por renda fez

{tabela(["Instituto (última onda)", "Erro L−F publicado", "Erro L−F reponderado", "Deslocamento L−F", "Efeito", "Perfil de renda"], linhas)}

- Verificado: no agregador de 04/10 ({ap['n_ondas']} ondas), o erro na diferença L−F cai de {num(ap['diferenca_lula_menos_flavio']['erro'], sinal=True)} (publicado) para {num(ar['diferenca_lula_menos_flavio']['erro'], sinal=True)} (renda trocada pela PNAD). Nas últimas ondas, {u['aproximou']} de {u['n']} se aproximaram da urna, {u['afastou']} se afastaram ({', '.join(afastaram)}) e {u['neutro']} ficou parada. O deslocamento médio foi de {num(u['deslocamento_medio_lula_menos_flavio'], sinal=True)} ponto na diferença L−F, a favor de Flávio.
- Contraprova publicada com o mesmo destaque: a Quaest se afastou, porque a amostra dela é mais rica que o país e a troca da renda empurra para Lula. A Gerp passou do ponto: estava a {num(abs(next(x for x in e['por_onda'] if x['instituto'] == 'Gerp' and x['ultima_onda_da_casa'])['erro_dif_publicado']))} da urna e foi para {num(next(x for x in e['por_onda'] if x['instituto'] == 'Gerp' and x['ultima_onda_da_casa'])['erro_dif_reponderado'], sinal=True)}.
- Juízo editorial: a reponderação por renda corrigiu a direção do erro comum e cerca de {pct((ap['diferenca_lula_menos_flavio']['erro'] - ar['diferenca_lula_menos_flavio']['erro']) / ap['diferenca_lula_menos_flavio']['erro'])} do tamanho dele no agregador. Não corrigiu tudo: a média reponderada ainda erra {num(ar['diferenca_lula_menos_flavio']['erro'], sinal=True)}. É sensibilidade de uma margem, não resultado corrigido.
- Ressalva: Datafolha e Quaest de 03/10 usaram o perfil de renda da onda anterior como hipótese declarada, porque o painel do contratante não publica o perfil.
"""


def _secao_casa(d: dict, vu: dict) -> str:
    c = d["previsao_casa"]
    dcc = vu["decomposicao"]["agregados"]["central_casa"]
    faixa_c = [
        dcc[k]["explicado_diferenca_pp"]
        for k in ("nexus_com_vazamento", "nexus_renormalizada", "datafolha_caiado")
    ]
    ce, mc = c["central"], c["monte_carlo"]
    ic = mc["intervalos_90_validos"]
    mg = mc["margem_flavio_menos_lula"]
    reg = c["regioes"]
    ufs = c["ufs"]["resumo"]
    pol = ufs["polarizacao"]
    sens = c["sensibilidades"]
    melhor = sens[0]
    n_finais_melhores = sum(
        1
        for x in d["pesquisas"]
        if x["ultima_onda_da_casa"]
        and abs(x["publicado"]["diferenca_lula_menos_flavio"]["erro"])
        < abs(ce["erro_diferenca_lula_menos_flavio"])
    )
    n_finais = sum(1 for x in d["pesquisas"] if x["ultima_onda_da_casa"])
    rep22 = next(
        s
        for s in sens
        if s["nome"].startswith("Se o erro comum de 2022 se repetisse (")
    )
    linhas_reg = []
    for chave, rot in (
        ("macro_Centro-Sul", "Centro-Sul (SE, S, CO)"),
        ("macro_Nordeste", "Nordeste"),
        ("macro_Norte", "Norte"),
        ("Exterior", "Exterior"),
    ):
        x = reg[chave]
        linhas_reg.append(
            [
                rot,
                num(x["validos"]["flavio"]),
                num(x["validos"]["flavio"] - x["erro_pp"]["flavio"]),
                num(x["erro_pp"]["flavio"], sinal=True),
                num(x["validos"]["lula"]),
                num(x["validos"]["lula"] - x["erro_pp"]["lula"]),
                num(x["erro_pp"]["lula"], sinal=True),
                num(x["erro_diferenca_lula_menos_flavio"], sinal=True),
            ]
        )
    piores = c["ufs"]["linhas"][:6]
    txt_piores = ", ".join(
        f"{x['uf']} {num(x['erro_diferenca_lula_menos_flavio'], sinal=True)}"
        for x in piores
    )
    return f"""## 6. O que a previsão da Arvor acertou e errou

Central publicada na madrugada de 04/10 (docs/assets/predicao_2026_1T_presidente.json, gerada {c['gerado_em']}): Flávio {num(ce['validos']['flavio'])}, Lula {num(ce['validos']['lula'])}, terceira via {num(ce['validos']['terceira_via'])}. Urna: {num(ic['flavio']['urna'])}, {num(ic['lula']['urna'])} e {num(ic['terceira_via']['urna'])}.

- Verificado: Lula ficou a {num(abs(ce['erro_pp']['lula']))} ponto da central. Flávio teve {num(-ce['erro_pp']['flavio'])} pontos a mais do que a central. O erro na diferença L−F foi {num(ce['erro_diferenca_lula_menos_flavio'], sinal=True)}, menor que o da média das pesquisas publicadas ({num(d['medias']['ultimas_ondas_publicado']['diferenca_lula_menos_flavio']['erro'], sinal=True)}) e da média reponderada ({num(d['medias']['agregador_reponderado']['diferenca_lula_menos_flavio']['erro'], sinal=True)}). {n_finais_melhores} das {n_finais} últimas ondas tiveram erro menor em módulo.
- Verificado: a diferença da urna (Flávio {num(mg['urna'], sinal=True)}) caiu no percentil {num(100 * mg['percentil_urna'], 0)} da distribuição da Arvor, dentro do intervalo de 90% ({num(mg['p05'], sinal=True)} a {num(mg['p95'], sinal=True)}). A Arvor dava {pct(mc['p_flavio_a_frente_de_lula'])} de chance de Flávio terminar à frente: não previu o vencedor do 1º turno, disse que era empate.
- Verificado: o ponto mais fraco da Arvor foi a consolidação. A terceira via da urna ({num(ic['terceira_via']['urna'])}) ficou abaixo do percentil 5 da Arvor ({num(ic['terceira_via']['p05'])}); Flávio e Lula ficaram dentro dos intervalos de 90%. Pela decomposição da seção 8, a consolidação explica de {num(min(faixa_c), sinal=True)} a {num(max(faixa_c), sinal=True)} dos {num(ce['erro_diferenca_lula_menos_flavio'], sinal=True)} de erro na diferença; o resto é deslocamento entre os finalistas.
- Verificado, com ressalva de seleção: a sensibilidade publicada mais próxima da urna foi "{melhor['nome']}" (erro L−F {num(melhor['erro_diferenca_lula_menos_flavio'], sinal=True)}). Ela é uma entre {len(sens)} sensibilidades; escolher a melhor depois da urna não é acerto. A de 2022 repetido erra {num(rep22['erro_diferenca_lula_menos_flavio'], sinal=True)}: passou do ponto.
- Verificado: a âncora dinâmica (DLM) errou {num(c['dlm']['erro_diferenca_lula_menos_flavio'], sinal=True)}, mais que a central; a urna ficou a {num(c['dlm']['z_urna'], 1)} desvio da margem dela.
- Comparecimento previsto {num(ce['comparecimento']['previsto'] / 1e6)} milhões, urna {num(ce['comparecimento']['urna'] / 1e6)}; branco e nulo previstos {num(ce['branco_nulo']['previsto'] / 1e6)} milhões, urna {num(ce['branco_nulo']['urna'] / 1e6)}.

{tabela(["Região", "Flávio previsto", "Flávio urna", "Erro F", "Lula previsto", "Lula urna", "Erro L", "Erro L−F"], linhas_reg)}

- Verificado: o erro está no Centro-Sul, onde a Arvor deu a Flávio {num(-reg['macro_Centro-Sul']['erro_pp']['flavio'])} pontos a menos. No Nordeste o sinal se inverte: Lula teve {num(-reg['macro_Nordeste']['erro_pp']['lula'])} pontos a mais que a central. O Norte ficou a {num(abs(reg['macro_Norte']['erro_diferenca_lula_menos_flavio']))} ponto.
- Verificado: o líder previsto venceu em {ufs['acertos_lider']} das {ufs['n_ufs']} UFs; os erros foram {' e '.join(ufs['erros_lider'])}. Flávio foi subestimado em {ufs['ufs_flavio_subestimado']} UFs. Maiores erros na diferença L−F: {txt_piores}.
- Inferido: a urna foi mais polarizada por UF do que a previsão. Para cada 10 pontos de vantagem de um lado na UF, o erro da central andou {num(-10 * pol['inclinacao'])} ponto a favor daquele lado (correlação {num(pol['correlacao'])} em {ufs['n_ufs']} UFs, sem peso).
"""


def _secao_estaduais(d: dict) -> str:
    g, s = d["governador"]["resumo"], d["senado"]["resumo"]
    surpresas = ", ".join(
        f"{nome_proprio(x['nome'])} ({x['uf']}, {pct(x['p_eleito'])})"
        for x in s["eleitos_menos_provaveis"][:4]
    )
    falsos = ", ".join(
        f"{nome_proprio(x['nome'])} ({x['uf']}, {pct(x['p_eleito'])})"
        for x in s["nao_eleitos_mais_provaveis"][:4]
    )
    cal = "; ".join(
        f"de {pct(c['faixa'][0])} a {pct(c['faixa'][1])}, {c['observados']} eleitas contra "
        f"{num(c['esperados'], 1)} esperadas em {c['n']} candidaturas"
        for c in s["calibracao"]
        if c["n"] and c["faixa"][0] >= 0.1
    )
    rc, ra = s["por_cobertura"]["recente"], s["por_cobertura"]["antiga"]
    prov_g = ", ".join(g["provisorios"]) or "nenhuma"
    prov_s = ", ".join(s["provisorios"]) or "nenhuma"
    return f"""## 7. Governadores e Senado

**Governadores** (docs/assets/predicao_governador.json contra o TSE; situação provisória em {prov_g}).

- Verificado: o líder previsto liderou a urna em {g['acertos_lider']} das {g['n_ufs']} UFs; erros em {', '.join(g['erros_lider'])}. Nos {len(g['ufs_2t'])} estados com 2º turno, o par que vai à disputa era o par mais provável da Arvor em {g['pares_2t_acertados']}.
- Verificado: {g['decididos_1t_urna']} UFs decididas no 1º turno, contra {num(g['decididos_1t_esperado'], 1)} esperadas (intervalo de 90% de {g['decididos_1t_ic90'][0]} a {g['decididos_1t_ic90'][1]}). Brier da probabilidade de decidir no 1º turno: {num(g['brier_decide_1t'], 3)}, contra {num(g['brier_decide_1t_moeda'], 3)} de uma moeda.
- Verificado: o voto do líder da urna caiu dentro do intervalo de 90% da Arvor em {g['lider_dentro_ic90']} das {g['n_ufs']} UFs.
- Inferido: houve concentração nos líderes também nos estados. O líder previsto teve, em média, {num(-g['erro_medio_validos_lider_previsto_pp'])} pontos dos válidos a mais do que a Arvor previu. A medida usa o líder previsto, não o vencedor, para não carregar viés de seleção.

**Senado** (docs/assets/predicao_senado.json contra o TSE; duas vagas por UF; provisório em {prov_s}).

- Verificado: as duas candidaturas mais prováveis de cada UF levaram {s['acertos_top2']} das {s['vagas']} vagas, contra {num(s['acertos_top2_esperados'], 1)} esperadas pelas próprias probabilidades da Arvor. A dupla inteira saiu certa em {s['ufs_dupla_inteira']} UFs. Cobertura recente: {rc['acertos_top2']} de {rc['vagas']}; cobertura antiga: {ra['acertos_top2']} de {ra['vagas']}.
- Verificado: Brier de {num(s['brier'], 4)} sobre {s['n_candidaturas']} candidaturas. Referências: {num(s['brier_media_sem_incerteza'], 4)} para "as duas primeiras da média com certeza" ({s['acertos_top2_media_sem_incerteza']} vagas) e {num(s['brier_uniforme_2_sobre_k'], 4)} para probabilidade igual a todas.
- Calibração por faixa de probabilidade: {cal}. A Arvor foi conservadora nas duas pontas: o improvável aconteceu menos e o provável aconteceu mais do que ela previu. Juízo: com cerca de 25 candidaturas por faixa, a diferença é pequena demais para chamar de descalibração.
- Maiores surpresas eleitas: {surpresas}. Favoritas que ficaram de fora: {falsos}.
"""


def _secao_voto_util(d: dict, vu: dict) -> str:
    t = vu["terceira_via"]
    tc = vu["terceiros_por_candidato"]["publicado"]
    rn = vu["reserva_nacional"]
    mv = vu["modelo_voto_util"]
    dc = vu["decomposicao"]["agregados"]
    nomes = {
        "cury": "Cury",
        "renan_santos": "Renan Santos",
        "caiado": "Caiado",
        "zema": "Zema",
        "demais": "demais",
    }
    queda = sorted(tc["queda_pp"].items(), key=lambda kv: -kv[1])
    txt_queda = "; ".join(
        f"{nomes[k]} {num(-v, sinal=True)} ({pct(-tc['queda_relativa'][k])} do que tinha)"
        for k, v in queda
    )
    serie = [p for p in t["serie_agregador_7d_validos"] if p["publicado"] is not None]
    pico = max(
        (p for p in serie if p["data"] >= "2026-09-15"), key=lambda p: p["publicado"]
    )
    ult = serie[-1]
    linhas = []
    for chave, rot in (
        ("ultimas_ondas_publicado", "Última onda de 13 casas, publicada"),
        ("agregador_publicado", "Agregador de 04/10, publicado"),
        ("agregador_reponderado", "Agregador de 04/10, reponderado"),
        ("central_casa", "Central da Arvor"),
    ):
        v = dc[chave]
        p0 = v["nexus_renormalizada"]
        faixa = [
            v[k]["explicado_diferenca_pp"]
            for k in ("nexus_com_vazamento", "nexus_renormalizada", "datafolha_caiado")
        ]
        linhas.append(
            [
                rot,
                num(p0["erro_diferenca_lula_menos_flavio_pp"], sinal=True),
                num(p0["queda_terceira_via_pp"]),
                num(p0["explicado_diferenca_pp"], sinal=True),
                f"{num(min(faixa), sinal=True)} a {num(max(faixa), sinal=True)}",
                num(p0["residuo_diferenca_pp"], sinal=True),
                f"{num(v['proporcional']['explicado_diferenca_pp'], sinal=True)}",
            ]
        )
    ufs = vu["decomposicao"]["por_uf_central"]
    pos = sorted(
        (x for x in ufs if x["uf"] != "ZZ"), key=lambda x: -x["residuo_diferenca_pp"]
    )[:4]
    neg = sorted(
        (x for x in ufs if x["uf"] != "ZZ"), key=lambda x: x["residuo_diferenca_pp"]
    )[:4]
    u0 = dc["ultimas_ondas_publicado"]
    faixa0 = [
        u0[k]["explicado_diferenca_pp"]
        for k in ("nexus_com_vazamento", "datafolha_caiado")
    ]
    erro0 = u0["nexus_renormalizada"]["erro_diferenca_lula_menos_flavio_pp"]
    cal, bru = mv["calibrado"], mv["bruto"]
    return f"""## 8. Voto útil: o que a urna mostrou

**Terceira via.** A última onda de {t['n_publicado_todas']} casas deu à terceira via {num(t['media_publicado_todas'])} pontos dos válidos ({num(t['media_reponderado'])} reponderada, {t['n_reponderaveis']} casas). A urna deu {num(t['urna_validos'])}. Nenhuma onda final ficou abaixo da urna; a mais baixa foi {t['por_onda'][0]['instituto']}, com {num(t['por_onda'][0]['publicado_validos'])}. A média móvel de 7 dias do agregador caiu de {num(pico['publicado'])} ({pico['data'][8:]}/{pico['data'][5:7]}) para {num(ult['publicado'])} ({ult['data'][8:]}/{ult['data'][5:7]}); a urna continuou a queda. A central da Arvor ({num(t['central_casa'])}) já tinha consolidação projetada e ainda assim ficou acima do próprio percentil 5 ({num(t['central_casa_p05'])}).

**Quem perdeu.** Contra a média das últimas ondas: {txt_queda}. Quem recebeu: Flávio {num(rn['ganho_medio_validos_flavio_pp'], sinal=True)} e Lula {num(rn['ganho_medio_validos_lula_pp'], sinal=True)} pontos dos válidos, em média, sobre o que cada pesquisa final deu a eles.

**Reserva de 2º turno.** Na mesma pesquisa, Flávio tinha em média {num(rn['reserva_media_flavio_pp'])} pontos a mais no 2º turno do que no 1º; Lula, {num(rn['reserva_media_lula_pp'])}. Pela contabilidade do mapa do voto útil, a urna revelou no 1º turno a mediana de {pct(rn['lambda_flavio']['mediana'])} da reserva de Flávio ({rn['lambda_flavio']['n']} casas, de {pct(rn['lambda_flavio']['min'])} a {pct(rn['lambda_flavio']['max'])}) e {pct(rn['theta_lula']['mediana'])} da de Lula. O voto útil foi de um lado só. Com os estados de 26/09, o mapa precisaria de λ = {num(cal['lambda_flavio'])} e θ = {num(cal['theta_lula'])} (versão calibrada) ou λ = {num(bru['lambda_flavio'])} e θ = {num(bru['theta_lula'])} (sem calibração) para reproduzir a urna; o cenário publicado mais próximo foi "{cal['cenarios_por_distancia'][0]['nome']}" na versão calibrada e "{bru['cenarios_por_distancia'][0]['nome']}" na sem calibração.

**Decomposição do erro na diferença L−F.**

{tabela(["Ponto de partida", "Erro L−F", "Queda da terceira via", "Consolidação (Nexus)", "Faixa entre variantes", "Resíduo", "Sem matriz"], linhas)}

- Estimativa, não medição: na última onda das {t['n_publicado_todas']} casas, a consolidação da terceira via explica de {num(min(faixa0), sinal=True)} a {num(max(faixa0), sinal=True)} dos {num(erro0, sinal=True)} pontos de erro na diferença L−F, de {pct(min(faixa0) / erro0)} a {pct(max(faixa0) / erro0)}. O resto, de {num(erro0 - max(faixa0), sinal=True)} a {num(erro0 - min(faixa0), sinal=True)}, é deslocamento entre os dois finalistas que a consolidação não explica: efeito de casa, movimento de última hora entre Lula e Flávio, comparecimento diferencial. Os dados não separam esses três.
- Sem matriz (cada ponto da terceira via repartido na proporção do placar), a consolidação explica perto de zero: o ganho de Flávio vem de a terceira via ser mais próxima dele, não de ela encolher.
- Por UF, a partir da central: o resíduo favorece Flávio no Sul e no Centro-Oeste ({', '.join(f"{x['uf']} {num(x['residuo_diferenca_pp'], sinal=True)}" for x in pos)}) e favorece Lula no Nordeste ({', '.join(f"{x['uf']} {num(x['residuo_diferenca_pp'], sinal=True)}" for x in neg)}). É o mesmo padrão de polarização da seção 6.

**Hipóteses declaradas.** (1) A linha de 2º turno de cada eleitorado (Nexus, 18 a 20/09, p. 79) vale para quem abandonou o candidato no 1º turno. (2) Variante principal: quem saiu e votou foi a Flávio ou Lula na razão da linha; variante com vazamento: a parte que iria a branco, nulo ou indeciso saiu dos válidos; variante Datafolha: Caiado com 42 a Flávio e 27 a Lula. (3) Candidaturas menores e "outros" sem linha publicada: meio a meio. (4) Abstenção não é modelada: quem deixou de votar aparece como resíduo. (5) A reserva por UF vem das pesquisas estaduais de setembro e carrega o movimento posterior.

**Conclusão com incerteza.** O voto útil existiu e foi assimétrico: a terceira via perdeu {num(t['media_publicado_todas'] - t['urna_validos'])} pontos dos válidos entre as pesquisas finais e a urna, e a maior parte foi a Flávio. A consolidação explica de {pct(min(faixa0) / erro0)} a {pct(max(faixa0) / erro0)} do erro das pesquisas na diferença entre os dois. O resto é deslocamento entre os finalistas, com o mesmo sinal do erro comum de 2022. A estimativa depende de uma matriz medida por um instituto duas semanas antes da eleição e aplicada ao 1º turno.
"""


def memorando(d: dict, vu: dict) -> str:
    u = d["urna"]
    v = u["validos"]
    versao = u["versao_nacional"]
    cab = f"""# Pesquisas, previsões da Arvor e voto útil contra a urna

1º turno presidencial de 04/10/2026. Memorando interno para o dossiê `docs/apuracao_1o_turno_2026.html`. Gerado por `python3 scripts/apuracao-2026-pesquisas.py`; números em `analysis/apuracao_2026/dados/pesquisas_vs_urna.json` e `voto_util.json`. Erro = pesquisa menos urna, em pontos dos votos válidos; na diferença L−F, positivo superestima Lula.

## 1. A urna

Arquivo nacional do TSE gerado em {hora_brasilia(versao['gerado_em'])} (SHA-256 `{versao['sha256'][:16]}…`), {milhar(u['secoes'])} de {milhar(u['secoes_total'])} seções, o mesmo corte de `apuracao/data/boletins/final.json`. Flávio {num(v['flavio'])}, Lula {num(v['lula'])}, Cury {num(v['cury'])}, Renan Santos {num(v['renan_santos'])}, Caiado {num(v['caiado'])}, Zema {num(v['zema'])}; terceira via {num(100 - v['flavio'] - v['lula'])}. Diferença L−F: {num(v['lula'] - v['flavio'], sinal=True)} ponto, {milhar(u['diferenca_flavio_menos_lula_votos'])} votos a favor de Flávio.

Pesquisas nos válidos pela regra da Arvor: candidaturas renormalizadas para 100, sem indecisos nem branco e nulo. EAM 5 = erro absoluto médio nas cinco candidaturas com 2% ou mais na urna (vazio quando o instituto agrupa nomes em "outros"). Margem AAS = margem de 95% da diferença sob amostragem simples, piso da incerteza.

## 2. Pesquisas com campo encerrado de 25/09 a 03/10

Ordenadas pelo erro absoluto na diferença L−F publicada. ● = última onda do instituto.

{_ranking(d)}

{_referencias(d)}
"""
    fim = """## 9. Limites

- Uma eleição é uma observação. Nenhum ranking desta página mede a qualidade de um método; mede o erro de uma onda num dia.
- Reponderação por renda é sensibilidade de uma margem, sem microdados nem pesos individuais.
- A decomposição do voto útil é contabilidade sob hipóteses, não medição de eleitor.
- Governador em AL e AM e Senado no AM estavam sem marca final do TSE no momento do corte e usam a situação provisória pela regra da eleição.

## 10. Reprodução

```
python3 scripts/apuracao-2026-pesquisas.py
pytest -q tests/test_apuracao_2026_pesquisas.py
```
"""
    return "\n".join(
        [
            cab,
            _secao_proximidade(d),
            _secao_erro_comum(d),
            _secao_reponderacao(d),
            _secao_casa(d, vu),
            _secao_estaduais(d),
            _secao_voto_util(d, vu),
            fim,
        ]
    )
