"""Valores numéricos dos capítulos explicativos, lidos do JSON do modelo.

Nenhum número do texto corrido é digitado no template: tudo o que muda com o
corte, a rodada ou a âncora vem daqui."""

from __future__ import annotations

from math import sqrt

from .view import number

CENTRAL = "Central inclusiva com recência, sem voto útil adicional"
SEM_EP = "Sem seleção de eleitor provável"
F25 = "Flávio antecipa 25% da reserva"
L25 = "Lula antecipa 25% da reserva"
LF25 = "Os dois antecipam 25% da reserva"
COMP_F = "Comparecimento de Flávio 3 pp acima de Lula"
COMP_L = "Comparecimento de Lula 3 pp acima de Flávio"
Z95 = 1.96


def signed(x, places=2):
    return ("+" if x > 0 else "") + number(x, places)


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

    out.update(dlm_values(nat["dinamico"], central, sens))
    out.update(predictive_values(data["validacao_preditiva"]))
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
