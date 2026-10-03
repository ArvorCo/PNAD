"""Valores numéricos dos capítulos explicativos, lidos do JSON do modelo.

Nenhum número do texto corrido é digitado no template: tudo o que muda com o
corte, a rodada ou a âncora vem daqui."""

from __future__ import annotations

from math import sqrt

from .view import number

CENTRAL = "Central: recência com tendência de 28 dias encolhida, indecisos por disponibilidade"
SEM_TEND = "Recência sem tendência, indecisos por disponibilidade"
PROP = "Indecisos proporcionais às candidaturas"
SEM_EP = "Sem seleção de eleitor provável"
F25 = "Flávio antecipa 25% da reserva"
L25 = "Lula antecipa 25% da reserva"
LF25 = "Os dois antecipam 25% da reserva"
COMP_F = "Comparecimento de Flávio 3 pp acima de Lula"
COMP_L = "Comparecimento de Lula 3 pp acima de Flávio"
Z95 = 1.96


def signed(x, places=2):
    return ("+" if x > 0 else "") + number(x, places)


def minus(x, places=2):
    """Como signed, com o sinal de menos tipográfico usado no simulador."""
    return signed(x, places).replace("-", "−")


def date_br(iso):
    year, month, day = iso.split("-")
    return f"{day}/{month}/{year}"


def day_month(iso):
    return date_br(iso)[:5]


def field_br(campo):
    return f"{day_month(campo['inicio'])} a {day_month(campo['fim'])}"


def pick(selected, instituto, fallback):
    for wave in selected:
        if wave["instituto"] == instituto:
            return wave
    return fallback(selected, key=lambda w: w["idade_campo_dias"])


def two_candidate_ci(vector, n, deff):
    """Intervalo de 95% da diferença entre os dois primeiros, em pontos."""
    p1, p2 = vector[0], vector[1]
    se = sqrt((p1 + p2 - (p1 - p2) ** 2) / n)
    d = 100 * (p1 - p2)
    half = 100 * Z95 * se
    half_deff = half * sqrt(deff)
    return d, (d - half, d + half), (d - half_deff, d + half_deff)


def comparison(items, a, b):
    return next(c for c in items if c["a"] == a and c["b"] == b)


def lead_example(wave, deff):
    name = wave["instituto"]
    d, srs, design = two_candidate_ci(wave["publicado_vetor"], wave["n"], deff)
    lead = f"{name} ({field_br(wave['campo'])}, {number(wave['n'], 0)} entrevistas) publicou "
    lead += f"Lula {number(100 * wave['publicado_vetor'][0], 0)}% e Flávio Bolsonaro "
    lead += f"{number(100 * wave['publicado_vetor'][1], 0)}%. "
    both = (
        f"Sob amostragem aleatória simples, o intervalo de 95% da diferença de "
        f"{number(abs(d), 0)} pontos vai de {signed(srs[0], 1)} a {signed(srs[1], 1)}. "
        f"Com efeito de desenho {number(deff, 1)}, o valor assumido por este modelo, vai de "
        f"{signed(design[0], 1)} a {signed(design[1], 1)}. "
    )
    srs_excludes = srs[0] > 0 or srs[1] < 0
    design_includes = design[0] <= 0 <= design[1]
    depends = srs_excludes and design_includes
    if depends:
        close = (
            "O primeiro intervalo exclui o zero por pouco; o segundo o inclui. "
            "A palavra “lidera” depende dessa hipótese sobre o desenho. "
            f"A frase que vale nos dois casos é: Lula tem "
            f"{number(100 * wave['publicado_vetor'][0], 0)}%, Flávio tem "
            f"{number(100 * wave['publicado_vetor'][1], 0)}%, e a diferença "
            "não separa os dois com 95% de confiança sob o desenho assumido."
        )
    else:
        close = (
            "Os dois testes dão a mesma resposta neste caso, "
            "e a frase deve acompanhá-la."
        )
    verdict = (
        "O exemplo acima passa por pouco no primeiro teste sob amostragem simples "
        "e reprova quando se admite o efeito de desenho assumido por este modelo."
        if depends
        else "O exemplo acima tem a mesma resposta nas duas hipóteses de desenho."
    )
    return lead + both + close, verdict


def values(data):
    nat = data["nacional"]
    selected = nat["selecionadas"]
    cfg = data["configuracao"]
    inc = data["incerteza"]
    central = data["central"]["brasil"]
    sens = data["sensibilidades"]
    deff = cfg["deff_assumido"]
    out = {}

    # Cabeçalhos e quantidades gerais.
    out["DATE_BR"] = date_br(data["referencia"])
    hash_ = data["hash_modelo"]
    out["MODEL_HASH_WBR"] = "<wbr>".join(
        hash_[i : i + 16] for i in range(0, len(hash_), 16)
    )
    out["N_RUNS"] = number(inc["sorteios"], 0)
    out["COMMON_SD"] = number(cfg["incerteza"]["erro_comum_sd_margem_validos_pp"], 0)
    out["PRIOR_N"] = number(cfg["peso_prior"], 0)
    out["DEFF"] = number(deff, 1)
    out["CENTRAL_LULA"] = number(central["percentuais"]["lula"], 1)
    out["CENTRAL_FLAVIO"] = number(central["percentuais"]["flavio"], 1)
    out["CENTRAL_GAP"] = number(central["margem_flavio_lula"], 2)
    out["CENTRAL_ELEITORADO_MI"] = number(central["eleitorado"] / 1e6, 1)
    out["CENTRAL_ABSTENCAO_MI"] = number(central["abstencao"] / 1e6, 1)
    out["CENTRAL_BRANCO_NULO_MI"] = number(central["branco_nulo"] / 1e6, 1)
    out["INDECISOS_VALIDOS"] = number(
        data["central"]["parametros"]["indecisos_validos"], 1
    )

    # Frase do resultado: lê o sinal e o intervalo, em vez de supô-los.
    gap = central["margem_flavio_lula"]
    lo, hi = inc["margem"]["p05"], inc["margem"]["p95"]
    ahead = "Lula" if gap < 0 else "Flávio"
    contains = lo <= 0 <= hi
    out["POINT_SENTENCE"] = f"{ahead} está à frente na estimativa pontual. " + (
        f"O intervalo contém o zero, então a página não afirma que {ahead} lidera."
        if contains
        else f"O intervalo não contém o zero, e a página afirma a vantagem de {ahead} sob o modelo."
    )

    # Alvos nacionais.
    alvos = nat["alvos"]
    out["ALVO_INDECISOS"] = number(100 * alvos["inclusivo"][3], 1)
    out["ALVO_BRANCO_NULO"] = number(100 * alvos["inclusivo"][4], 1)
    out["ALVO_PNAD_LULA"] = number(100 * alvos["pnad"][0], 1)
    out["ALVO_PNAD_FLAVIO"] = number(100 * alvos["pnad"][1], 1)
    out["ALVO_PUB_LULA"] = number(100 * alvos["publicado"][0], 1)
    out["ALVO_PUB_FLAVIO"] = number(100 * alvos["publicado"][1], 1)
    out["ALVO_DELTA_LULA"] = signed(100 * (alvos["pnad"][0] - alvos["publicado"][0]), 1)
    out["ALVO_DELTA_FLAVIO"] = signed(
        100 * (alvos["pnad"][1] - alvos["publicado"][1]), 1
    )

    # Exemplos de peso: duas ondas reais da seleção atual.
    a = pick(selected, "Datafolha", min)
    b = pick(selected, "AtlasIntel", max)
    for tag, wave in (("A", a), ("B", b)):
        out[f"EX{tag}_NOME"] = wave["instituto"]
        out[f"EX{tag}_CAMPO"] = field_br(wave["campo"])
        out[f"EX{tag}_IDADE"] = number(wave["idade_campo_dias"], 1)
        out[f"EX{tag}_PESO"] = number(wave["peso_recencia"], 2)
        out[f"EX{tag}_PART"] = number(wave["participacao_central_pct"], 1)
    h = len(selected)
    w = a["participacao_central_pct"] / 100
    out["EXA_ALPHA"] = number(h * w, 1)
    out["EXA_SD_PESO"] = number(100 * sqrt(w * (1 - w) / (h + 1)), 1)
    conc = min(a["n"], 2000) / deff
    pl = a["previsao_vetor"][0]
    out["EXA_CONC"] = number(conc, 0)
    out["EXA_SD_LULA"] = number(100 * sqrt(pl * (1 - pl) / (conc + 1)), 1)
    out["EXA_N"] = number(a["n"], 0)
    out["EXA_MOE"] = number(100 * Z95 * sqrt(0.25 / a["n"]), 1)
    out["EXA_SENTENCE"], out["EXA_VERDICT"] = lead_example(a, deff)

    # Pooling estadual, exemplos por UF.
    ufs = {s["uf"]: s for s in data["estados"]}
    for uf in ("AC", "BA", "SP"):
        s = ufs[uf]
        out[f"PRIOR_{uf}"] = number(100 * s["peso_prior"], 0)
        out[f"NEFF_{uf}"] = number(s["n_efetivo_assumido"], 0)
        out[f"ONDAS_{uf}"] = str(len(s["pesquisas"]))

    # Sensibilidades citadas no texto corrido.
    out["SENS_SEM_EP_LULA"] = number(sens[SEM_EP]["brasil"]["percentuais"]["lula"], 1)
    out["SENS_F25_GAP"] = number(sens[F25]["brasil"]["margem_flavio_lula"], 2)
    out["SENS_L25_GAP"] = number(sens[L25]["brasil"]["margem_flavio_lula"], 2)
    out["SENS_LF25_GAP"] = number(sens[LF25]["brasil"]["margem_flavio_lula"], 2)
    base_votes = central["lula"]
    out["COMP_F_PERDA_MI"] = number(
        abs(sens[COMP_F]["brasil"]["lula"] - base_votes) / 1e6, 1
    )
    out["COMP_L_GANHO_MI"] = number(
        abs(sens[COMP_L]["brasil"]["lula"] - base_votes) / 1e6, 1
    )

    out.update(trend_values(data))
    out.update(learning_values(data))
    out.update(dlm_values(nat["dinamico"], central, sens))
    out.update(consolidation_values(data))
    out.update(rejection_values(data))
    out.update(predictive_values(data["validacao_preditiva"]))
    out.update(error_2022_values(data))
    return out


def error_2022_values(data):
    """Bloco “O erro de 2022, casa por casa”: tudo lido de erro_2022."""
    e = data["erro_2022"]
    media = e["media_das_casas"]
    included = set(media["casas"])
    houses = [h for h in e["por_casa"] if h["id"] in included]
    gap = {h["id"]: h["diferenca_lula_menos_bolsonaro"]["erro"] for h in houses}
    official = e["resultado_oficial"]
    shares = official["parcelas_validos_pp"]
    sens = {s["nome"]: s for s in e["sensibilidades_da_media"]}
    labels = e["aplicacao_2026"]["sensibilidades"]
    scen = data["sensibilidades"]
    worst = max(gap.values())
    best = min(houses, key=lambda h: abs(gap[h["id"]]))
    other_way = sorted(
        (h for h in houses if gap[h["id"]] < 0), key=lambda h: -gap[h["id"]]
    )
    common = media["erro_comum_pp"]
    out = {
        "E22_TSE_LULA": number(shares["lula"], 2),
        "E22_TSE_BOLSONARO": number(shares["bolsonaro"], 2),
        "E22_TSE_GAP": number(official["diferenca_lula_menos_bolsonaro_pp"], 2),
        "E22_TSE_VALIDOS_MI": number(official["votos"]["validos"] / 1e6, 1),
        "E22_TSE_DATA": (
            official["conferencia_api_bruta"]["br"]["data_totalizacao"][:10]
            if official.get("conferencia_api_bruta")
            else ""
        ),
        "E22_MEDIA_GAP": number(
            media["media_simples_validos_pp"]["lula"]
            - media["media_simples_validos_pp"]["bolsonaro"],
            2,
        ),
        "E22_GAP": minus(media["erro_comum_diferenca_lula_menos_bolsonaro"]),
        "E22_MEDIANA": minus(media["mediana_dos_erros_diferenca_pp"]),
        "E22_LULA": minus(common["lula"]),
        "E22_BOLSONARO": minus(common["bolsonaro"]),
        "E22_TEBET": minus(common["tebet"]),
        "E22_CIRO": minus(common["ciro"]),
        "E22_N_CASAS": str(media["n_casas"]),
        "E22_N_SUBESTIMARAM": str(sum(h["erro_pp"]["bolsonaro"] < 0 for h in houses)),
        "E22_N_GAP_ACIMA": str(media["casas_que_superestimaram_lula_menos_bolsonaro"]),
        "E22_N_FORA_MARGEM": str(
            sum(
                gap[h["id"]] > 0 and h["erro_diferenca_fora_da_margem_aas"]
                for h in houses
            )
        ),
        "E22_N_ANTES": str(sum(h["campo"]["fim"] < "2022-10-01" for h in houses)),
        "E22_DISPERSAO": number(
            media["desvio_padrao_entre_casas_pp"]["diferenca_lula_menos_bolsonaro"], 2
        ),
        "E22_PIORES": _list(
            [h["casa"] for h in houses if abs(gap[h["id"]] - worst) < 0.005]
        ),
        "E22_PIOR_GAP": minus(worst),
        "E22_PIOR_PUBLICADA": number(
            next(
                h["diferenca_lula_menos_bolsonaro"]["pesquisa"]
                for h in houses
                if abs(gap[h["id"]] - worst) < 0.005
            ),
            0,
        ),
        "E22_CENTRAL_GAP": minus(data["central"]["brasil"]["margem_flavio_lula"]),
        "E22_MELHOR": best["casa"],
        "E22_MELHOR_GAP": minus(gap[best["id"]]),
        "E22_CONTRA": _list(
            [f"{h['casa']} ({minus(gap[h['id']])})" for h in other_way]
        ),
        "E22_SENS_PDF": minus(
            sens["so_pdf_do_instituto"]["erro_comum_diferenca_lula_menos_bolsonaro"]
        ),
        "E22_SENS_PDF_N": str(sens["so_pdf_do_instituto"]["n_casas"]),
        "E22_SENS_SEM_VERITA": minus(
            sens["sem_verita"]["erro_comum_diferenca_lula_menos_bolsonaro"]
        ),
        "E22_SENS_BRASMARKET": minus(
            sens["ampliada"]["erro_comum_diferenca_lula_menos_bolsonaro"]
        ),
    }
    for tag, key in (("FLAVIO", "repeticao"), ("LULA", "invertido")):
        b = scen[labels[key]]["brasil"]
        out[f"E22_SENS_GAP_{tag}"] = minus(b["margem_flavio_lula"])
        out[f"E22_SENS_{tag}_LULA"] = number(b["percentuais"]["lula"], 1)
        out[f"E22_SENS_{tag}_FLAVIO"] = number(b["percentuais"]["flavio"], 1)
    return out


def consolidation_values(data):
    """Bloco do simulador sobre a consolidação medida nas pesquisas."""
    from .motor import scenario

    cons = data["consolidacao"]
    central = data["central"]["brasil"]
    out = {
        "CONS_IDADE": number(cons["idade_efetiva_ancora_dias"], 1),
        "CONS_DATA": date_br(cons["data_efetiva_ancora"]),
        "CONS_HORIZONTE": number(cons["horizonte_dias"], 1),
        "CONS_RES_LULA": number(cons["reserva_nacional_pct"]["lula"], 1),
        "CONS_RES_FLAVIO": number(cons["reserva_nacional_pct"]["flavio"], 1),
    }
    caps = []
    for key in ("28", "14"):
        fit, proj = cons["janelas"][key], cons["projecao"][key]
        slope, se = fit["inclinacao_pp_dia"], fit["erro_padrao_pp_dia"]
        div = fit["divisao"]
        tag = f"CONS{key}"
        out[f"{tag}_ONDAS"] = str(fit["n_ondas"])
        out[f"{tag}_CASAS"] = str(fit["n_casas"])
        for k, name in (("terceira_via", "T"), ("flavio", "F"), ("lula", "L")):
            out[f"{tag}_{name}"] = minus(slope[k], 2)
            out[f"{tag}_{name}_EP"] = number(se[k], 2)
        out[f"{tag}_DIV_F"] = number(100 * proj["parte_flavio_usada"], 0)
        out[f"{tag}_DIV_L"] = number(100 * (1 - proj["parte_flavio_usada"]), 0)
        out[f"{tag}_DIV_EP"] = number(100 * (div["erro_padrao"] or 0), 0)
        out[f"{tag}_MIGR"] = number(proj["migracao_total_pp"], 2)
        out[f"{tag}_MIGR_F"] = number(proj["migracao_pp"]["flavio"], 2)
        out[f"{tag}_MIGR_L"] = number(proj["migracao_pp"]["lula"], 2)
        lam = proj["lambda_arredondado"]
        out[f"{tag}_LAMBDA_F"] = number(100 * lam["flavio"], 0)
        out[f"{tag}_LAMBDA_L"] = number(100 * lam["lula"], 0)
        result = scenario(
            data["estados"],
            {
                **data["central"]["parametros"],
                "base": cons["ancora"],
                "voto_flavio": lam["flavio"],
                "voto_lula": lam["lula"],
            },
        )["brasil"]
        out[f"{tag}_LULA"] = number(result["percentuais"]["lula"], 1)
        out[f"{tag}_FLAVIO"] = number(result["percentuais"]["flavio"], 1)
        out[f"{tag}_GAP"] = minus(result["margem_flavio_lula"], 2)
        out[f"{tag}_DELTA"] = minus(
            result["margem_flavio_lula"] - central["margem_flavio_lula"], 2
        )
        caps += [
            f"{name} em {key} dias"
            for k, name in (("lula", "Lula"), ("flavio", "Flávio"))
            if proj["teto_atingido"][k]
        ]
    cmp_ = cons["comparacao_central"]
    out["CONS_CMP_CENTRAL"] = minus(cmp_["central_margem_pp"], 2)
    out["CONS_CMP_CONS"] = minus(cmp_["consolidacao_28_sobre_inclusivo_margem_pp"], 2)
    out["CONS_CMP_DIFF"] = number(abs(cmp_["diferenca_pp"]), 2)
    short = cons["projecao"]["14"]["parte_flavio_usada"]
    short_se = cons["janelas"]["14"]["divisao"]["erro_padrao"] or 0
    half = abs(short - 0.5) <= Z95 * short_se
    out["CONS_METADE"] = (
        "Nos últimos 14 dias, a parte de Flávio na migração não se distingue de "
        "metade: o intervalo de 95% contém 50%."
        if half
        else "Nos últimos 14 dias, a parte de Flávio na migração se distingue de "
        "metade: o intervalo de 95% não contém 50%."
    )
    out["CONS_TETO"] = (
        " A migração projetada esgota a reserva medida para "
        + " e ".join(caps)
        + ", e o cenário usa o teto de 100%."
        if caps
        else ""
    )
    return out


def _list(names):
    return names[0] if len(names) < 2 else ", ".join(names[:-1]) + " e " + names[-1]


def rejection_values(data):
    """Bloco do simulador sobre rejeição como régua de destino."""
    rej = data["rejeicao"]
    sens = data["sensibilidades"]
    central = data["central"]["brasil"]
    media, comp = rej["media"], rej["comparacao"]

    def pct(x, places=1):
        return number(100 * x, places)

    out = {
        "REJ_N_CASAS": str(len(media["casas"])),
        "REJ_CASAS": _list(media["casas"]),
        "REJ_LULA": number(media["lula"], 1),
        "REJ_FLAVIO": number(media["flavio"], 1),
        "REJ_PARTE": pct(media["parte_flavio"]),
        "REJ_EP": number(100 * media["erro_padrao"], 1),
        "REJ_AMPL_LO": pct(media["amplitude_entre_casas"][0]),
        "REJ_AMPL_HI": pct(media["amplitude_entre_casas"][1]),
        "REJ_CARTAO": pct(rej["por_formato"]["cartao_multipla"]["parte_flavio"]),
        "REJ_GRADE": pct(rej["por_formato"]["grade_por_candidato"]["parte_flavio"]),
        "REJ_CONTROLES": _list(rej["controles_media"]["casas"]),
        "REJ_CONTROLE": pct(rej["controles_media"]["parte_flavio"]),
        "REJ_SERIE28": pct(comp["serie_28"]["parte_flavio"]),
        "REJ_SERIE14": pct(comp["serie_14"]["parte_flavio"]),
        "REJ_Z28": number(abs(comp["serie_28"]["z_disponibilidade_menos_serie"]), 1),
        "REJ_NEXUS": pct(comp["nexus_p84"]["parte_flavio_entre_finalistas"]),
        "REJ_DF": pct(
            comp["datafolha_segunda_opcao"]["hesitantes"][
                "parte_flavio_entre_finalistas"
            ]
        ),
    }
    picks = (
        ("Quaest", "Independente", "entre independentes na Quaest"),
        ("Palver", "Independente", "entre independentes na Palver"),
        ("Datafolha", "Nenhum/Não tem", "entre quem não tem partido no Datafolha"),
    )
    found = []
    for house, label, text in picks:
        seg = next(
            (
                g
                for g in rej["segmentos"]
                if g["instituto"] == house and g["rotulo"] == label
            ),
            None,
        )
        if seg:
            ep = (
                f" (erro padrão de {number(100 * seg['erro_padrao'], 1)} pontos)"
                if seg["erro_padrao"]
                else ""
            )
            found.append(f"{pct(seg['parte_flavio'], 0)}% {text}{ep}")
    out["REJ_INDEP"] = _list(found)
    share = media["parte_flavio"]
    measured = (
        ("a série de 28 dias", comp["serie_28"]["parte_flavio"]),
        ("a série de 14 dias", comp["serie_14"]["parte_flavio"]),
        ("a matriz da Nexus", comp["nexus_p84"]["parte_flavio_entre_finalistas"]),
        (
            "a segunda opção do Datafolha",
            comp["datafolha_segunda_opcao"]["hesitantes"][
                "parte_flavio_entre_finalistas"
            ],
        ),
    )
    above = [name for name, v in measured if v > share]
    below = [name for name, v in measured if v <= share]
    sentence = "A divisão por disponibilidade supõe que quem se move rejeita como o eleitorado inteiro."
    if above:
        sentence += f" Dá menos a Flávio que {_list(above)}"
        sentence += f" e mais que {_list(below)}." if below else "."
    else:
        sentence += f" Dá mais a Flávio que {_list(below)}."
    out["REJ_FRASE"] = sentence
    out["REJ_IND_PARTE"] = pct(data["central"]["parametros"]["indecisos_flavio"])
    out["REJ_IND_EFEITO"] = minus(
        central["margem_flavio_lula"] - sens[PROP]["brasil"]["margem_flavio_lula"], 2
    )
    for tag, label in (
        ("IND", CENTRAL),
        ("PROP", PROP),
        ("CONS", "Consolidação 28 dias, divisão por disponibilidade"),
    ):
        b = sens[label]["brasil"]
        out[f"REJ_{tag}_LULA"] = number(b["percentuais"]["lula"], 1)
        out[f"REJ_{tag}_FLAVIO"] = number(b["percentuais"]["flavio"], 1)
        out[f"REJ_{tag}_GAP"] = minus(b["margem_flavio_lula"], 2)
        out[f"REJ_{tag}_DELTA"] = minus(
            b["margem_flavio_lula"] - central["margem_flavio_lula"], 2
        )
    return out


def trend_values(data):
    """Passo 1: correção de tendência da central (inclinação encolhida)."""
    nat = data["nacional"]
    sloped = nat["tendencia"]["central_com_inclinacao"]
    shrunk = sloped["inclinacoes_encolhidas_validos_pp_dia"]
    raw = sloped["inclinacoes_brutas_validos_pp_dia"]
    alvo = nat["alvos"]["inclusivo"]
    before = 100 * (alvo[1] - alvo[0]) / sum(alvo[:3])
    sens = data["sensibilidades"]
    central = data["central"]["brasil"]["margem_flavio_lula"]
    unc = data["configuracao"]["incerteza"]["projecao_inclinacao"]
    out = {
        "TEND_JANELA": str(sloped["janela_dias"]),
        "TEND_DATA": date_br(sloped["data_efetiva_central"]),
        "TEND_HORIZ": number(sloped["horizonte_dias"], 2),
        "TEND_ALVO_ANTES": minus(before, 2),
        "TEND_ALVO_DEPOIS": minus(sloped["margem_flavio_lula_validos_pp"], 2),
        "TEND_ALVO_DELTA": minus(sloped["margem_flavio_lula_validos_pp"] - before, 2),
        "TEND_SEM": minus(sens[SEM_TEND]["brasil"]["margem_flavio_lula"], 2),
        "TEND_COM": minus(central, 2),
        "TEND_EFEITO": minus(
            central - sens[SEM_TEND]["brasil"]["margem_flavio_lula"], 2
        ),
        "TEND_DP_PROJ": number(unc["dp_margem_pp"]["central_inclinacao"], 2),
        "TEND_DP_TOTAL": number(unc["erro_comum_total_sd_pp"], 2),
    }
    for k, tag in (("lula", "L"), ("flavio", "F"), ("outros", "O")):
        out[f"TEND_{tag}"] = minus(shrunk[k], 3)
        out[f"TEND_{tag}_BRUTA"] = minus(raw[k], 3)
        out[f"TEND_{tag}_FATOR"] = number(100 * shrunk[k] / raw[k] if raw[k] else 0, 0)
    return out


def learning_values(data):
    """Capítulo #aprendizado: a central nova e o que a validação mostrou."""
    vp = data["validacao_preditiva"]
    group = vp["origem_movel"]["por_grupo_horizonte"]["1-3"]
    m = group["metricas"]

    def paired(a):
        c = next(
            x
            for x in group["comparacoes"]
            if x["a"] == a and x["b"] == "recencia_3d_7d"
        )
        return c["margem_lula_flavio"]

    out = {
        "APR_N_PARES": str(group["n_pares"]),
        "APR_N_ONDAS": str(group["n_ondas_alvo"]),
    }
    for tag, name in (
        ("CENTRAL", "recencia_3d_7d"),
        ("INCL", "central_inclinacao_28d"),
        ("TEND", "tendencia"),
    ):
        out[f"APR_MAE_{tag}"] = number(m[name]["mae_margem_pp"], 2)
        out[f"APR_VIES_{tag}"] = signed(m[name]["vies_margem_pp"], 2)
    for tag, name in (("INCL", "central_inclinacao_28d"), ("TEND", "tendencia")):
        c = paired(name)
        out[f"APR_DIFF_{tag}"] = minus(c["diferenca_mae_pp"], 2)
        out[f"APR_SE_{tag}"] = number(c["erro_padrao_pp"], 2)
    split = data["nacional"]["tendencia"]["divisao_migracao"]
    rows = {r["fonte"]: r for r in split["resumo"]}
    for tag, key in (
        ("SERIE", "serie_nacional_28d"),
        ("NEXUS", "nexus_matriz_quem_pode_mudar"),
        ("DF", "datafolha_matriz_quem_pode_mudar"),
    ):
        out[f"APR_MIG_{tag}"] = number(100 * rows[key]["fracao_flavio"], 0)
    out["APR_MIG_SINTESE"] = number(100 * split["sintese"]["fracao_flavio"], 0)
    acc = data["nacional"]["tendencia"]["aceleracao"]
    out["APR_ACEL_P"] = number(
        acc["quadratica_efeitos_fixos"]["28"]["categorias"]["flavio"]["p_aceleracao"],
        2,
    )
    out["APR_ACEL_RV_P"] = number(acc["ultimos_28_dias"]["p_valor_mistura_chi2"], 2)
    return out


def dlm_values(dlm, central, sens):
    par = dlm["parametros"]
    final = dlm["estado_final"]
    out = {
        "DLM_N_ONDAS": str(dlm["n_ondas"]),
        "DLM_N_CASAS": str(len(dlm["casas"])),
        "DLM_INICIO": day_month(dlm["janela_inicio"]),
        "DLM_VAL_LULA": number(final["validos_pct"]["lula"], 2),
        "DLM_VAL_FLAVIO": number(final["validos_pct"]["flavio"], 2),
        "DLM_VAL_GAP": number(final["margem_flavio_lula_validos_pp"], 2),
        "DLM_SD": number(final["dp_margem_pp"], 2),
        "DLM_PHI": number(par["phi_variancia_nao_amostral"], 2),
        "DLM_DEFF_EF": number(par["deff_efetivo"], 2),
        "DLM_LL": number(dlm["log_verossimilhanca"], 2),
        "DLM_LL_PHI1": number(par["log_verossimilhanca_phi_1"], 2),
        "DLM_LR": number(
            2 * (dlm["log_verossimilhanca"] - par["log_verossimilhanca_phi_1"]), 1
        ),
        "DLM_EVOL": number(par["dp_diario_nivel_pp"]["lula"], 2),
    }
    scenario = next(v for k, v in sens.items() if k.startswith("Âncora dinâmica"))
    out["DLM_SCEN_LULA"] = number(scenario["brasil"]["percentuais"]["lula"], 2)
    out["DLM_SCEN_FLAVIO"] = number(scenario["brasil"]["percentuais"]["flavio"], 2)
    out["DLM_SCEN_GAP"] = number(scenario["brasil"]["margem_flavio_lula"], 2)
    out["DLM_CENT_LULA"] = number(central["percentuais"]["lula"], 2)
    out["DLM_CENT_FLAVIO"] = number(central["percentuais"]["flavio"], 2)
    out["DLM_CENT_GAP"] = number(central["margem_flavio_lula"], 2)
    effects = dlm["efeitos_casa"]
    key = "efeito_margem_lula_flavio_validos_pp"
    top = max(effects, key=lambda h: effects[h][key])
    bottom = min(effects, key=lambda h: effects[h][key])
    out["DLM_HOUSE_TOP"] = top
    out["DLM_HOUSE_TOP_EF"] = signed(effects[top][key], 2)
    out["DLM_HOUSE_TOP_N"] = str(effects[top]["n_ondas"])
    out["DLM_HOUSE_BOTTOM"] = bottom
    out["DLM_HOUSE_BOTTOM_EF"] = signed(effects[bottom][key], 2)
    out["DLM_HOUSE_BOTTOM_N"] = str(effects[bottom]["n_ondas"])
    shift = scenario["brasil"]["margem_flavio_lula"] - central["margem_flavio_lula"]
    out["DLM_GAP_DIFF"] = number(abs(shift), 2)
    out["DLM_GAP_DIR"] = "a Flávio" if shift > 0 else "a Lula"
    singles = [e for e in effects.values() if e["n_ondas"] == 1]
    out["DLM_N_UMA_ONDA"] = str(len(singles))
    out["DLM_DP_UMA_ONDA"] = number(
        sum(e["dp_margem_pp"] for e in singles) / max(len(singles), 1), 1
    )
    return out


def predictive_values(vp):
    om = vp["origem_movel"]
    m = om["metricas"]
    design = vp["desenho"]
    out = {
        "PRED_N_PARES": str(om["n_pares"]),
        "PRED_N_ONDAS": str(om["n_ondas_alvo"]),
        "PRED_ORIGEM_INI": day_month(design["origens"][0]),
        "PRED_ORIGEM_FIM": day_month(design["origens"][1]),
        "PRED_H_MIN": str(design["horizonte_dias"][0]),
        "PRED_H_MAX": str(design["horizonte_dias"][1]),
    }
    for tag, name in (
        ("CENTRAL", "recencia_3d_7d"),
        ("DLM", "dinamico"),
        ("DLM1", "dinamico_phi1"),
        ("IGUAL", "igual_7d"),
        ("1D", "recencia_1d_7d"),
    ):
        out[f"PRED_MAE_{tag}"] = number(m[name]["mae_margem_pp"], 2)
        out[f"PRED_RMSE_{tag}"] = number(m[name]["rmse_margem_pp"], 2)
        out[f"PRED_VIES_{tag}"] = signed(m[name]["vies_margem_pp"], 2)
    biases = [v["vies_margem_pp"] for v in m.values()]
    out["PRED_VIES_MIN"] = signed(min(biases), 2)
    out["PRED_VIES_MAX"] = signed(max(biases), 2)
    dlm = comparison(om["comparacoes"], "dinamico", "recencia_3d_7d")
    out["PRED_DIFF_DLM"] = signed(dlm["diferenca_mae_margem_pp"], 2)
    out["PRED_SE_DLM"] = number(dlm["erro_padrao_pp"], 2)
    out["PRED_DLM_MELHOR"] = str(dlm["a_melhor_em_ondas"])
    half = comparison(om["comparacoes"], "recencia_5d_7d", "recencia_3d_7d")
    out["PRED_DIFF_5D"] = signed(half["diferenca_mae_margem_pp"], 2)
    out["PRED_SE_5D"] = number(half["erro_padrao_pp"], 2)

    loo = vp["deixa_uma_casa_fora"]
    lm = loo["metricas"]
    out["PRED_LOO_CENTRAL"] = number(lm["recencia_3d_7d"]["mae_margem_pp"], 2)
    out["PRED_LOO_DLM"] = number(lm["dinamico"]["mae_margem_pp"], 2)
    cmp_loo = comparison(loo["comparacoes"], "dinamico", "recencia_3d_7d")
    out["PRED_LOO_DIFF"] = signed(cmp_loo["diferenca_mae_margem_pp"], 2)
    out["PRED_LOO_SE"] = number(cmp_loo["erro_padrao_pp"], 2)
    out["PRED_LOO_N"] = str(loo["n_pares"])

    same = vp["com_casa_do_alvo"]
    sm = same["metricas"]
    out["PRED_SH_DLMCASA"] = number(sm["dinamico_casa"]["mae_margem_pp"], 2)
    out["PRED_SH_ULTIMA"] = number(sm["ultima_onda_mesma_casa"]["mae_margem_pp"], 2)
    out["PRED_SH_CENTRAL"] = number(sm["recencia_3d_7d"]["mae_margem_pp"], 2)
    gain = comparison(same["comparacoes"], "dinamico_casa", "recencia_3d_7d")
    out["PRED_SH_GANHO"] = number(abs(gain["diferenca_mae_margem_pp"]), 2)
    out["PRED_SH_SE"] = number(gain["erro_padrao_pp"], 2)
    out["PRED_SH_N"] = str(same["n_pares"])
    out["PRED_SH_ONDAS"] = str(same["n_ondas_alvo"])
    return out
