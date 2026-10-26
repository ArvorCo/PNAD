"""Valores formatados da thread do 2º turno, segunda parte: seções, pesquisas,
hipótese do autor, paralela, boletins, limites e fecho."""

from __future__ import annotations

import re
from itertools import pairwise

from apuracao_2026.thread_base import mi, nome_proprio, num, pct, sinal

from .pagina_cap_boletins import NAO_FOI_AO_AR, boletins
from .thread_base import MEMOS, dado
from .thread_valores import NOME_UF, noticia

# ------------------------------------------------------------------ 10 a 12 seções


def v_secoes() -> dict:
    s = dado("secoes")
    ag = s["agregados"]["brasil"]
    dc = ag["delta_comp"]
    por_uf = sorted(
        (u for u in s["agregados"]["por_uf"] if u["delta_comp"]["media"] is not None),
        key=lambda u: u["delta_comp"]["media"],
    )
    caiu = [u for u in por_uf if u["delta_comp"]["media"] < 0]
    ranking = dado("secoes_ranking")["secoes"]
    jag = max(ranking, key=lambda x: x["salto_bio_pp"])
    ps = ag["persistencia"]
    va = dado("secoes_voto")["votos_absolutos"]["comparecimento_10pp"]
    v = {
        "s_n": num(s["totais"]["secoes"]),
        "s_universo": num(s["n_universo_1t"]),
        "s_ref": num(ag["n_ref_1t"]),
        "s_ultimo_rec": s["max_recebido_hhmm"],
        "s_media_delta": num(dc["media"], 2),
        "s_p50_delta": num(dc["p50"], 2),
        "s_p10_delta": sinal(dc["p10"]),
        "s_p90_delta": sinal(dc["p90"]),
        "s_delta_pct": pct(dc["pct_5_mais"]),
        "s_delta_secoes": num(ag["sinais"]["delta"]),
        "s_rel_pct": pct(100 * dc["n_relativo_5_mais"] / dc["n"]),
        "s_rel_secoes": num(dc["n_relativo_5_mais"]),
        "s_queda_pct": pct(dc["pct_menos_5"]),
        "s_10pp_pct": pct(dc["pct_10_mais"]),
        "s_10pp_n": num(va["n"]),
        "s_10pp_lula": num(va["lula_ganhou_mais"]),
        "s_10pp_lula_pct": pct(va["pct_lula_ganhou_mais"]),
        "s_10pp_demais_pct": pct(va["pct_lula_ganhou_mais_demais"]),
        "s_comp_2t": pct(dc["comp_2t_pct"]),
        "s_comp_1t": pct(dc["comp_1t_pct"]),
        "s_caiu_n": str(len(caiu)),
        "s_caiu1": NOME_UF[caiu[0]["uf"]],
        "s_caiu1_v": sinal(caiu[0]["delta_comp"]["media"]),
        "s_caiu2": NOME_UF[caiu[1]["uf"]],
        "s_caiu2_v": sinal(caiu[1]["delta_comp"]["media"]),
        "s_caiu3": NOME_UF[caiu[2]["uf"]],
        "s_caiu3_v": sinal(caiu[2]["delta_comp"]["media"]),
        "s_escore2": num(ag["escore_2_mais"]),
        "s_papel": num(ag["urna"]["sistema_apuracao"]),
        "s_conting": num(ag["urna"]["contingencia"]),
        # biometria
        "b_sem_2t": pct(ag["sem_biometria"]["pct_2t"]),
        "b_sem_1t": pct(ag["sem_biometria"]["pct_1t_mesmas"]),
        "b_sem_n": num(ps["sem_bio_n"]),
        "b_sem_ja": num(ps["sem_bio_ja_no_1t"]),
        "b_sem_ja_pct": pct(100 * ps["sem_bio_ja_no_1t"] / ps["sem_bio_n"], 0),
        "b_sem_var": sinal(ps["sem_bio_dif_p50_pp"]),
        "b_ano_2t": pct(ag["ano_nascimento"]["pct_2t"]),
        "b_ano_1t": pct(ag["ano_nascimento"]["pct_1t_mesmas"]),
        "b_ano_n": num(ps["ano_nasc_n"]),
        "b_ano_ja": num(ps["ano_nasc_ja_no_1t"]),
        "b_ano_var": sinal(ps["ano_nasc_dif_p50_pp"]),
        "b_salto_n": num(ag["salto_biometria"]["n_sinal"]),
        "b_pian_n": num(ag["salto_biometria"]["n_comparecimento_e_salto"]),
        "jag_mun": jag["municipio"],
        "jag_uf": jag["uf"],
        "jag_zona": str(jag["zona"]),
        "jag_secao": str(jag["secao"]),
        "jag_salto": sinal(jag["salto_bio_pp"]),
        "jag_ano1": pct(jag["ano_nasc_pct_1t"]),
        "jag_ano2": pct(jag["ano_nasc_pct_2t"]),
        "jag_comp": sinal(jag["delta_comp_pp"]),
        "jag_f1": num(jag["flavio_1t"]),
        "jag_l1": num(jag["lula_1t"]),
        "jag_f2": num(jag["flavio_2t"]),
        "jag_l2": num(jag["lula_2t"]),
        "jag_enc": jag["encerramento_2t"],
        "rank_n": str(len(ranking)),
        "rank_sem_expl": str(sum(1 for x in ranking if x["sem_explicacao"])),
    }
    return v


def v_voto() -> dict:
    sv = dado("secoes_voto")
    si = {x["sinal"]: x for x in sv["sinais"]}
    passa = [
        x
        for x in sv["sinais"]
        if x.get("did_fatia_flavio_pp") is not None
        and x["n_did"] >= sv["n_min"]
        and abs(x["did_fatia_flavio_pp"]) > 2 * x["ep_did_fatia_flavio_pp"]
    ]
    t = {
        (x["comparecimento_alto"], x["biometria_baixa"]): x for x in sv["tabela_2x2x2"]
    }
    ambos, nenhum = t[(True, True)], t[(False, False)]
    va = sv["votos_absolutos"]
    v = {"vt_passa_n": str(len(passa))}
    for chave, nome in (
        ("delta", "d"),
        ("sinal_sem_bio", "sb"),
        ("biometria_baixa", "bb"),
        ("sinal_salto_bio", "sl"),
        ("delta_relativo", "dr"),
        ("tardia", "td"),
    ):
        x = si[chave]
        v[f"vt_{nome}_viz"] = sinal(x["dif_fatia_flavio_vs_vizinhas_pp"])
        v[f"vt_{nome}_did"] = sinal(x["did_fatia_flavio_pp"])
        v[f"vt_{nome}_ep"] = num(x["ep_did_fatia_flavio_pp"], 2)
        v[f"vt_{nome}_n"] = num(x["n_did"])
    dids = [abs(x["did_fatia_flavio_pp"]) for x in passa]
    v["vt_did_max"] = num(max(dids), 2)
    v["vt_passa_lula"] = str(sum(1 for x in passa if x["did_fatia_flavio_pp"] < 0))
    v["vt_passa_flavio"] = str(sum(1 for x in passa if x["did_fatia_flavio_pp"] > 0))
    an = si["sinal_ano_nasc"]
    v["vt_an_did"] = sinal(an["did_fatia_flavio_pp"])
    v["vt_an_n"] = num(an["n_did"])
    v["vt_ambos_n"] = num(ambos["n"])
    v["vt_ambos_sobe"] = num(ambos["n_flavio_sobe"])
    v["vt_ambos_sobe_pct"] = pct(ambos["pct_flavio_sobe"])
    v["vt_nenhum_sobe_pct"] = pct(nenhum["pct_flavio_sobe"])
    v["vt_ambos_d"] = sinal(ambos["delta_fatia_flavio_pp"])
    v["vt_nenhum_n"] = num(nenhum["n"])
    v["vt_nenhum_d"] = sinal(nenhum["delta_fatia_flavio_pp"])
    v["vt_f_ganhou"] = pct(va["flavio_ganhou"]["pct"])
    v["vt_l_ganhou"] = pct(va["lula_ganhou"]["pct"])
    v["vt_ganho_f"] = num(va["ganho_medio_flavio"], 2)
    v["vt_ganho_l"] = num(va["ganho_medio_lula"], 2)
    v["vt_n_min"] = str(sv["n_min"])
    return v


# ------------------------------------------------------------------ 13 e 14 pesquisas


def v_pesquisas() -> dict:
    pv = dado("pesquisas_vs_urna")
    rs = pv["resumo"]
    pub = rs["publicado_validos_do_total"]
    mod = pv["por_modo"]
    ranking = {p["id"]: p for p in pv["pesquisas"]}
    ordem = [ranking[i] for i in pv["ranking"]]
    tp = pv["tendencia_publicada"]
    pd = pv["hipoteses"]["presenca_declarada"]
    pre = dado("projecao_pre_urna")["metodos"]
    transp = pre["transportado_25_10"]
    proj_uf = pre["projecao_25_10"]
    v = {
        "pq_n": str(rs["n_casas"]),
        "pq_erro_abs": num(abs(pub["media"]), 2),
        "pq_ultimo_campo": max(p["campo"]["fim"] for p in pv["pesquisas"])[8:10]
        + "/"
        + max(p["campo"]["fim"] for p in pv["pesquisas"])[5:7],
        "pq_erro": sinal(pub["media"]),
        "pq_mediana": sinal(pub["mediana"]),
        "pq_min": sinal(pub["amplitude"][0]),
        "pq_max": sinal(pub["amplitude"][1]),
        "pq_pos": str(pub["positivos"]),
        "pq_neg": str(pub["negativos"]),
        "pq_desvio": num(pub["desvio_padrao"], 2),
        "pq_aas": num(rs["desvio_esperado_so_amostragem_aas_pp"], 2),
        "pq_fora": str(rs["fora_da_margem_aas"]),
        "pq_f_frente": str(rs["flavio_a_frente_nos_validos"]),
        "pq_acertos": str(rs["acertaram_vencedor"]),
        "pq_acertaram": " e ".join(rs["casas_que_acertaram_vencedor"]),
        "pq_oficial": sinal(rs["publicado_validos_oficiais"]["media"]),
        "pq_oficial_n": str(rs["publicado_validos_oficiais"]["n"]),
        "pq_urna_dif": sinal(rs["erro_media_simples"]["urna_f_menos_l"]),
        "pq_media_f": pct(rs["media_simples_validos"]["flavio"]),
        "pq_melhor": ordem[0]["instituto"],
        "pq_melhor_e": sinal(ordem[0]["erro_validos_do_total"]["erro_f_menos_l"]),
        "pq_pior": ordem[-1]["instituto"],
        "pq_pior_e": sinal(ordem[-1]["erro_validos_do_total"]["erro_f_menos_l"]),
        "pq_pres": sinal(mod["presencial"]["media"]),
        "pq_pres_n": str(mod["presencial"]["n"]),
        "pq_tel": sinal(mod["telefone"]["media"]),
        "pq_tel_n": str(mod["telefone"]["n"]),
        "pq_incl": sinal(tp["pos_urna_05_a_24"]["inclinacao_dentro_da_casa_pp_dia"], 3),
        "pq_ate12": sinal(tp["media_campo_ate_12_10"]),
        "pq_desde19": sinal(tp["media_campo_desde_19_10"]),
        "pq_extrap": sinal(tp["extrapolacao_ate_a_urna"]["f_menos_l_extrapolado"]),
        "pq_ondas": str(tp["pos_urna_05_a_24"]["n_ondas"]),
        "pq_pres_decl": _lista_presenca(pd),
    }
    cont = pv["hipoteses"]["contabilidade_entre_turnos"]
    v["pq_transp_e"] = sinal(transp["nacional_erro_f_menos_l_pp"])
    v["pq_res_ufs"] = str(cont["ufs_com_residuo_negativo"])
    v["pq_transp_vies"] = sinal(transp["vies_flavio_pp_ponderado"])
    v["pq_transp_rmse"] = num(transp["rmse_sem_vies_pp"], 2)
    v["pq_proj_uf_certo"] = str(proj_uf["acertou_vencedor"])
    v["pq_proj_uf_errou"] = " e ".join(
        NOME_UF[u] for u in proj_uf["errou_vencedor_ufs"]
    )
    v["pq_proj_uf_vies"] = sinal(proj_uf["vies_flavio_pp_ponderado"])
    return v


def _lista_presenca(pd: list[dict]) -> str:
    partes = []
    for x in pd:
        partes.append(
            f"{x['instituto']} desloca a diferença {sinal(x['deslocamento_f_menos_l'])}"
        )
    return "; ".join(partes)


def v_casa() -> dict:
    pv = dado("pesquisas_vs_urna")
    c = pv["centrais"]
    rs = pv["resumo"]
    ef = pv["efeito_reponderacao"]
    t1 = pv["primeiro_turno"]
    painel = pv["painel_1t_2t"]
    pub = c["ancora_projecao_published"]["erro_f_menos_l"]
    pnad = c["ancora_projecao_pnad"]["erro_f_menos_l"]
    proj = c["projecao_arvor"]["erro_f_menos_l"]
    piores = sorted(ef["por_casa"], key=lambda x: -x["variacao_erro_absoluto"])
    return {
        "cs_media": sinal(c["media_arvor"]["erro_f_menos_l"]),
        "cs_media_f": pct(c["media_arvor"]["validos"]["flavio"]),
        "cs_media_l": pct(c["media_arvor"]["validos"]["lula"]),
        "cs_proj": sinal(proj),
        "cs_proj_f": pct(c["projecao_arvor"]["validos"]["flavio"]),
        "cs_ancora": sinal(pub),
        "cs_pnad_soma": sinal(pnad - pub),
        "cs_pres_soma": sinal(proj - pnad),
        "cs_pres_pct": sinal(c["presenca_relativa_pct"], 1),
        "cs_snapshot": c["snapshot"],
        "cs_rep_n": str(ef["n"]),
        "cs_rep_afastou": str(ef["afastou"]),
        "cs_rep_aprox": str(ef["aproximou"]),
        "cs_rep_neutro": str(ef["neutro"]),
        "cs_rep_desloc": sinal(ef["deslocamento_medio_f_menos_l"]),
        "cs_rep_pub": sinal(rs["publicado_mesmas_casas_reponderadas"]["media"]),
        "cs_rep_pnad": sinal(rs["reponderado"]["media"]),
        "cs_rep_pior": piores[0]["instituto"],
        "cs_rep_pior_v": sinal(piores[0]["variacao_erro_absoluto"]),
        "cs_t1_aprox": str(t1["efeito_reponderacao_ultimas_ondas"]["aproximou"]),
        "cs_t1_n": str(t1["efeito_reponderacao_ultimas_ondas"]["n"]),
        "cs_t1_pub": sinal(t1["agregador_publicado_erro"]),
        "cs_t1_rep": sinal(t1["agregador_reponderado_erro"]),
        "cs_t1_erro": sinal(t1["erro_comum_lula_menos_flavio"]),
        "cs_t1_casas": str(t1["n_casas"]),
        "cs_22_erro": sinal(pv["referencia_2022"]["erro_comum_lula_menos_bolsonaro"]),
        "cs_painel_n": str(painel["n"]),
        "cs_painel_inv": str(painel["inverteram_sinal"]),
        "cs_painel_corr": sinal(painel["correlacao"], 2),
    }


# ------------------------------------------------------------------ 15 hipótese do autor


def v_mudanca() -> dict:
    """Notícias da noite usadas no card do que mudou entre sábado e domingo."""
    bus = noticia(r"atualizou para \d+ o total de ônibus parados")
    prisao = noticia(r"TRE-BA mandou prender")
    dec = noticia(r"^Zanin, na Reclamação")
    return {
        "mu_bus_n": re.search(r"para (\d+) o total", bus["resumo"]).group(1),
        "mu_bus_veic": bus["veiculo"],
        "mu_bus_hora": bus["quando"][11:16],
        "mu_prisao_veic": prisao["veiculo"],
        "mu_prisao_hora": prisao["quando"][11:16],
        "mu_reclamacao": re.search(r"Reclamação (\d+)", dec["resumo"]).group(1),
    }


def v_transferencia() -> dict:
    """Card da transferência 1º → 2º turno: ``transferencia.json`` (resposta e IPF)."""
    tr = dado("transferencia")
    rs = tr["resposta"]
    m = tr["ipf"]["central"]["metricas"]
    inv = tr["ipf"]["invariantes"]
    ct = tr["ipf"]["central"]["contagem_tipos"]
    pq = tr["pesquisas"]["terceira_via_2t"]
    reg = tr["regressao"]["robustez"][0]
    sec = next(x for x in tr["regressao"]["secoes_resumo"] if "município" in x["nome"])

    def faixa(par, casas=1, pct_=True):
        f = pct if pct_ else num
        return f"{f(par[0], casas)} a {f(par[1], casas)}"

    return {
        "tf_voltaram": mi(rs["voltaram_milhoes"] * 1e6),
        "tf_faltaram": mi(m["faltaram_no_2t"]),
        "tf_volt_l": pct(rs["voltaram_lula_pct"], 0),
        "tf_volt_l_faixa": faixa(rs["voltaram_lula_ic"], 0),
        "tf_volt_f": pct(m["voltaram_flavio_pct"], 0),
        "tf_explica": num(rs["explica_pp"], 2),
        "tf_explica_faixa": faixa(rs["explica_pp_ic"], 2, False),
        "tf_swing": num(abs(rs["swing_h2h_pp"]), 2),
        "tf_terc_f": pct(rs["terceira_flavio_pct"], 1),
        "tf_terc_l": pct(m["terceira"]["lula_pct"], 1),
        "tf_terc_faixa": faixa(rs["terceira_flavio_faixa"]),
        "tf_pq_terc": faixa(rs["pesquisas_flavio_do_estoque"]),
        "tf_pq_terc_fin": faixa(pq["flavio_entre_finalistas"]),
        "tf_pq_ondas": str(len(pq["linhas"])),
        "tf_razao": num(m["razao_consolidacao_flavio_lula"], 2),
        "tf_razao_faixa": faixa(inv["razao_consolidacao"], 2, False),
        "tf_fora_l": mi(m["ganho_fora_base_lula"]),
        "tf_fora_f": mi(m["ganho_fora_base_flavio"]),
        "tf_reg_l": num(reg["lula"], 1),
        "tf_reg_l_ic": faixa(reg["lula_ic95"], 1, False),
        "tf_reg_f": num(reg["flavio"], 1),
        "tf_reg_mun": num(reg["n"]),
        "tf_sec_l": num(sec["lula"], 1),
        "tf_sec_ic": faixa(sec["lula_ic95"], 1, False),
        "tf_sec_n": num(sec["n"]),
        "tf_sec_volt": pct(rs["secoes_voltaram_lula_pct"], 0),
        "tf_sec_explica": num(rs["secoes_explica_pp"], 2),
        "tf_medido_pct": pct(ct["medido"]["pct_votos"], 0),
        "tf_sintese": pct(100 * tr["pesquisas"]["sintese_pre_1t"]["fracao_flavio"], 1),
    }


def v_logs() -> dict:
    """Card dos logs das urnas: ``logs.json`` (cobertura, cadência, reinícios, bateria)."""
    lg = dado("logs")
    cob = lg["cobertura"]
    cad = lg["cadencia"]
    b2 = cad["brasil_2t"]
    a1 = cad["amostra_1t"]
    rei = lg["reinicios"]
    rv = next(x for x in rei["voto"] if x["grupo"] == "todas com reinício")
    bt = next(x for x in lg["bateria"]["voto"] if "junto" in x["grupo"])
    ig = lg["integrado"]
    mr = lg["metadados"]["serie_mr"]["estruturais"]
    apos17 = b2["computados_17_19"] + b2["computados_depois_19"]
    return {
        "lg_lidos": num(cob["lidos"]),
        "lg_catalogadas": num(cob["catalogadas"]),
        "lg_confere": num(cob["contagem_confere"]),
        "lg_nao_confere": str(len(cob["contagem_nao_confere"])),
        "lg_versao": next(iter(cob["versoes"])).split(" - ")[0],
        "lg_versoes_n": str(len(cob["versoes"])),
        "lg_apos17": num(apos17),
        "lg_computados": mi(b2["computados"]),
        "lg_apos17_pct": pct(100 * apos17 / b2["computados"], 3),
        "lg_apos19": num(b2["computados_depois_19"]),
        "lg_1t_17_19": pct(a1["brasil_1t"]["pct_17_19"], 1),
        "lg_2t_17_19_mesmas": pct(a1["brasil_2t_mesmas"]["pct_17_19"], 3),
        "lg_amostra_1t": num(a1["secoes"]),
        "lg_1h_2t": pct(b2["pct_primeira_hora"], 1),
        "lg_1h_1t": pct(a1["brasil_1t"]["pct_primeira_hora"], 1),
        "lg_bu19": num(cad["bu_apos_19h"]["secoes"]),
        "lg_bu19_ate1715": num(
            next(
                v
                for k, v in cad["bu_apos_19h"].items()
                if k.startswith("ultimo_voto_ate_")
            )
        ),
        "lg_bu19_mediana": cad["bu_apos_19h"]["mediana_ultimo_voto"],
        "lg_rei": num(rei["secoes"]),
        "lg_rei_did": sinal(rv["dif_em_dif_contra_1t"]["media_pp"], 2),
        "lg_rei_ic": (
            f"{sinal(rv['dif_em_dif_contra_1t']['ic95_pp'][0], 2)} a "
            f"{sinal(rv['dif_em_dif_contra_1t']['ic95_pp'][1], 2)}"
        ),
        "lg_bat_did": sinal(bt["dif_em_dif_contra_1t"]["media_pp"], 2),
        "lg_bat_n": num(bt["secoes_com_sinal"]),
        "lg_int": num(ig["as_duas"]),
        "lg_int_esp": num(ig["esperado_se_independentes"], 0),
        "lg_mr_grupos": str(len([x for x in mr if x["ufs"] != ["ZZ"]])),
        "lg_mr_secoes": num(sum(x["secoes"] for x in mr if x["ufs"] != ["ZZ"])),
        "lg_mr_grupos_ext": str(len([x for x in mr if x["ufs"] == ["ZZ"]])),
        "lg_mr_secoes_ext": num(sum(x["secoes"] for x in mr if x["ufs"] == ["ZZ"])),
        "lg_h_ini": f"{min(int(h) for h in b2['pct'])}h",
        "lg_h_ini2": f"{min(int(h) for h in b2['pct']) + 1}h",
        "lg_h1715": next(
            f"{k[-4:-2]}h{k[-2:]}"
            for k in cad["bu_apos_19h"]
            if k.startswith("ultimo_voto_ate_")
        ),
        "lg_mr_uma_zona": "sim" if all(len(x["zonas"]) == 1 for x in mr) else "não",
    }


def v_hipoteses() -> dict:
    """Card "O que poderia ter acontecido": ``hipoteses.json`` (estados e testes)."""
    hp = dado("hipoteses")
    est = hp["estados"]
    hs = {h["id"]: h for h in hp["hipoteses"]}
    h1, h2, h3, h4, h5 = hp["h1"], hp["h2"], hp["h3"], hp["h4"], hp["h5"]
    terc = {x["grupo"]: x for x in h3["tercos"]}
    fraco = next(x for k, x in terc.items() if "fraco" in k)
    forte = next(x for k, x in terc.items() if "forte" in k)
    meio = next(x for k, x in terc.items() if x not in (fraco, forte))
    ve = next(
        x for x in hp["precedentes"]["itens"] if x["id"] == "ve_2015_legislativas"
    )
    us = next(x for x in hp["precedentes"]["itens"] if x["id"] == "us_2022_harris")
    sil = hp["cronologia"]["silencio"]
    vid = hp["cronologia"]["video"]
    return {
        "hi_n": str(len(hs)),
        "hi_desc_n": str(sum(1 for h in hs.values() if h["estado"] == "descartada")),
        "hi_pend_n": str(sum(1 for h in hs.values() if h["estado"] == "pendente")),
        "hi_comp_n": str(sum(1 for h in hs.values() if h["estado"] == "compativel")),
        "hi_est_desc": est["descartada"],
        "hi_est_pend": est["pendente"],
        "hi_est_comp": est["compativel"],
        "hi_17_19": pct(h1["pct_17_19"], 3),
        "hi_17_19_1t": pct(h1["pct_17_19_1t"], 1),
        "hi_bu19": num(h1["bus_apos_19h"]),
        "hi_bu19_cedo": num(h1["bus_apos_19h_ultimo_voto_ate_1715"]),
        "hi_bus": num(h2["bus"]),
        "hi_vsc": num(h2["vsc_bu_igual"]),
        "hi_rdv": num(h2["rdv_confere"]),
        "hi_zonas": num(h2["zona"]["zonas_conferem"]),
        "hi_ab_fraco": sinal(fraco["abstencao_variacao_pp"]),
        "hi_ab_meio": sinal(meio["abstencao_variacao_pp"]),
        "hi_ab_forte": sinal(forte["abstencao_variacao_pp"]),
        "hi_desl_fraco": sinal(fraco["deslocamento_flavio_pp"]),
        "hi_desl_forte": sinal(forte["deslocamento_flavio_pp"]),
        "hi_sil": num(sil["minutos"], 1),
        "hi_video": vid["publicado_brt_segundos"],
        "hi_video_antes": str(h4["video_antes_da_peticao_min"]),
        "hi_mr_n": num(h5["mr_repetida_secoes"]),
        "hi_ve_ano": ve["data"][:4],
        "hi_us_ano": us["data"][:4],
    }


def v_hipotese() -> dict:
    h = dado("hipotese_autor")
    cen = {x["nome"]: x for x in h["cenarios"]}
    tw = h["reproducao_tweet"]
    a = cen["a_presenca_necessaria"]
    b = cen["b_limite_todos_indecisos_para_lula"]
    c = cen["c_combinacao_do_autor_com_bn_reais"]
    pv = dado("pesquisas_vs_urna")
    hp = pv["hipoteses"]
    memo = (MEMOS / "hipotese_autor.md").read_text(encoding="utf-8")
    trecho = re.search(r"> (Para chegar.*?não saberemos\.)", memo, re.DOTALL).group(1)
    hora_tw = re.search(r"às (\d{2}:\d{2})", memo).group(1)
    ind = hp["indecisos_extremo"]
    return {
        "hp_hora": hora_tw,
        "hp_tweet": f"“{' '.join(trecho.split())}”",
        "hp_pres": sinal(tw["parametros"]["presenca_relativa"], 1),
        "hp_comp": pct(tw["parametros"]["comparecimento"], 1),
        "hp_ind_f": pct(tw["parametros"]["indecisos_flavio"], 1),
        "hp_motor_f": pct(tw["flavio_validos_pct"]),
        "hp_snapshot": h["snapshot"]["versao"],
        "hp_bn": num(h["urna"]["brancos_mais_nulos"]),
        "hp_bn_pct": pct(h["urna"]["branco_nulo_pct_comparecimento"]),
        "hp_abst": pct(h["urna"]["abstencao_pct"]),
        "hp_a_pres": sinal(h["presenca_necessaria_a"], 1),
        "hp_central": sinal(pv["centrais"]["presenca_relativa_pct"], 1),
        "hp_b_f": pct(b["placar"]["flavio_validos_pct"]),
        "hp_b_e": sinal(b["contra_a_urna"]["diferenca_f_menos_l_pp"]),
        "hp_c_f": pct(c["placar"]["flavio_validos_pct"]),
        "hp_c_e": sinal(c["contra_a_urna"]["diferenca_f_menos_l_pp"]),
        "hp_c_votos": num(c["contra_a_urna"]["flavio_votos"]),
        "hp_a_f": pct(a["placar"]["flavio_validos_pct"]),
        "hp_empate": sinal(hp["presenca_relativa_necessaria"]["autor_empate_pct"], 1),
        "hp_nec_media": num(abs(hp["presenca_relativa_necessaria"]["media_arvor"]), 1),
        "hp_nec_simples": num(
            abs(hp["presenca_relativa_necessaria"]["media_simples_publicada_20_casas"]),
            1,
        ),
        "hp_ind_medio": pct(hp["indecisos_divisao_autor"]["indecisos_medios_pct"], 1),
        "hp_ind_erro": sinal(hp["indecisos_divisao_autor"]["erro_medio_f_menos_l"]),
        "hp_ind_lula_erro": sinal(ind["erro_medio_todos_indecisos_lula"]),
        "hp_ind_lula_frente": str(ind["flavio_ainda_a_frente"]),
    }


# ------------------------------------------------------------------ 16 paralela e boletins


def v_paralela() -> dict:
    p = dado("paralela")
    pr = p["placar_bus"]["presidente"]
    cob = sorted(p["cobertura_uf"], key=lambda x: -x["bus"])
    bol = boletins()
    horas = [int(b["id"][:2]) * 60 + int(b["id"][2:]) for b in bol]
    gaps = [b - a for a, b in pairwise(horas)]
    i = max(range(len(gaps)), key=lambda k: gaps[k])
    total_s = sum(b["duracao"] or 0 for b in bol)
    nao = sorted(NAO_FOI_AO_AR)
    return {
        "pa_bus": num(p["recebidos"]["bus"]),
        "pa_ufs": str(p["recebidos"]["ufs"]),
        "pa_iguais": num(p["conferencia"].get("igual", 0)),
        "pa_div": num(p["conferencia"].get("divergente", 0)),
        "pa_f": pct(pr["pct_flavio_nominais"]),
        "pa_comp": pct(pr["pct_comparecimento"]),
        "pa_aptos": num(pr["aptos"]),
        "pa_uf1": NOME_UF[cob[0]["uf"]],
        "pa_uf1_n": str(cob[0]["bus"]),
        "bo_n": str(len(bol)),
        "bo_min": num(total_s / 60, 0),
        "bo_primeiro": f"{bol[0]['id'][:2]}:{bol[0]['id'][2:]}",
        "bo_ultimo": f"{bol[-1]['id'][:2]}:{bol[-1]['id'][2:]}",
        "bo_gap": str(gaps[i]),
        "bo_gap_de": f"{bol[i]['id'][:2]}:{bol[i]['id'][2:]}",
        "bo_gap_ate": f"{bol[i + 1]['id'][:2]}:{bol[i + 1]['id'][2:]}",
        "bo_nao": f"{nao[0][:2]}:{nao[0][2:]}" if nao else "",
    }


# ------------------------------------------------------------------ 17 e 18


def v_limites() -> dict:
    p = dado("presidente")
    inc = p["conferencia"]["municipios_incompletos"]
    lt = dado("linha_do_tempo")
    abertas = [u["uf"] for u in lt["conclusao_ufs"] if not u["fechou_brt"]]
    pv = dado("pesquisas_vs_urna")
    rep = dado("urnas")["turnos"]["2t"]["repetidos"]
    ufs_rep = {ln_["uf"] for g in rep["grupos"] for ln_ in g["linhas"]}
    rdv = dado("rdv")["cobertura"]["total"]
    return {
        "ur_rep": str(rep["ids_repetidos"]),
        "ur_rep_secoes": str(rep["secoes_envolvidas"]),
        "ur_rep_onde": (
            "no exterior" if ufs_rep == {"zz"} else "em " + ", ".join(sorted(ufs_rep))
        ),
        "ur_rep_sobrepostas": str(rep["por_classe"]["sobreposicao"]["ids"]),
        "ur_rep_apuracao": str(rep["por_classe"]["sistema_apuracao"]["ids"]),
        "rdv_ok": num(rdv["ok"]),
        "rdv_aux404": num(rdv["aux_404"]),
        "rdv_sem": num(rdv.get("sem_rdv", 0)),
        "rdv_gov_pct": pct(
            dado("rdv")["troca_de_campo"]["seis_ufs"][
                "governador_com_numero_de_presidente_pct"
            ],
            1,
        ),
        "rdv_pres_pct": pct(
            dado("rdv")["troca_de_campo"]["seis_ufs"][
                "presidente_com_numero_de_governador_pct"
            ],
            1,
        ),
        "rdv_gov_nulos": num(
            dado("rdv")["troca_de_campo"]["seis_ufs"]["nulos_governador"]
        ),
        "rdv_div": num(rdv["ok"] - rdv["confere"]),
        "rdv_com_bu": num(rdv["com_bu"]),
        "li_mun_inc": str(len(inc)),
        "li_mun_inc_ex": f"{nome_proprio(inc[0]['nome'])} ({inc[0]['uf']})",
        "li_ufs_abertas": ", ".join(abertas),
        "li_ufs_abertas_n": str(len(abertas)),
        "li_n_fontes": str(len(pv["fontes"])),
        "li_versao": p["meta"]["versao_nacional_gerada_brt"][11:19],
    }


def v_fecho() -> dict:
    lt = dado("linha_do_tempo")
    return {
        "fe_versoes": num(
            sum(x["capturas"] for x in lt["regressoes"]["por_nivel"].values())
        ),
        "fe_eleitores_mi": mi(dado("presidente")["nacional"]["aptos"]),
    }


__all__ = [
    "v_casa",
    "v_fecho",
    "v_hipotese",
    "v_limites",
    "v_mudanca",
    "v_paralela",
    "v_pesquisas",
    "v_secoes",
    "v_transferencia",
    "v_voto",
]
