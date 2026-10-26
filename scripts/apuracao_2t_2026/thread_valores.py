"""Valores formatados da thread do 2º turno, um dicionário por tema.

Cada chave vira campo ``{chave}`` nos modelos dos posts. Nada aqui é digitado:
tudo é lido dos JSONs do dossiê (``analysis/apuracao_2t_2026/dados``), do
levantamento de notícias da noite e dos boletins publicados, e formatado com as
funções da thread do 1º turno.
"""

from __future__ import annotations

import re
import statistics
from functools import cache

from apuracao_2026.thread_base import mi, nome_proprio, num, pct, sinal

from . import secoes_linhas
from .thread_base import (
    URL_DOSSIE,
    dado,
    hhmm_min,
    min_hhmm,
    tabela,
)

NOME_UF = {
    "AC": "Acre",
    "AL": "Alagoas",
    "AP": "Amapá",
    "AM": "Amazonas",
    "BA": "Bahia",
    "CE": "Ceará",
    "DF": "Distrito Federal",
    "ES": "Espírito Santo",
    "GO": "Goiás",
    "MA": "Maranhão",
    "MT": "Mato Grosso",
    "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais",
    "PA": "Pará",
    "PB": "Paraíba",
    "PR": "Paraná",
    "PE": "Pernambuco",
    "PI": "Piauí",
    "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul",
    "RO": "Rondônia",
    "RR": "Roraima",
    "SC": "Santa Catarina",
    "SP": "São Paulo",
    "SE": "Sergipe",
    "TO": "Tocantins",
}


def hora(s: str) -> str:
    """'2026-10-25 17:07:09' ou '17:07' vira '17:07'."""
    return s.split(" ")[-1][:5]


def hora_h(s: str) -> str:
    """'19:00' vira '19h'; '17:49' vira '17h49'."""
    hh, mm = hora(s).split(":")
    return f"{int(hh)}h" if mm == "00" else f"{int(hh)}h{mm}"


def _lista(itens: list[str]) -> str:
    if len(itens) <= 1:
        return "".join(itens)
    return ", ".join(itens[:-1]) + " e " + itens[-1]


@cache
def noticias() -> list[dict]:
    return dado("analysis/apuracao_2t_2026/noticias_noite.json")["itens"]


def noticia(padrao: str) -> dict:
    """O primeiro item da cronologia da noite cujo resumo casa com ``padrao``."""
    rx = re.compile(padrao)
    for it in noticias():
        if rx.search(it["resumo"]):
            return it
    raise ValueError(f"notícia não encontrada: {padrao}")


def _hora_noticia(it: dict) -> str:
    return it["quando"][11:16]


def serie_nacional() -> list[dict]:
    return tabela(dado("linha_do_tempo")["nacional"]["serie"])


# ------------------------------------------------------------------ 1 e 2


def v_resultado() -> dict:
    p = dado("presidente")
    n = p["nacional"]
    reg = {r["regiao"]: r for r in p["regioes"]}
    ufs = [u for u in p["ufs"] if u["uf"] != "ZZ"]
    norte = reg["Norte"]
    v = {
        "url_dossie": URL_DOSSIE,
        "l_pct": pct(n["pct_lula"]),
        "f_pct": pct(n["pct_flavio"]),
        "l_pct_n": num(n["pct_lula"], 2),
        "f_pct_n": num(n["pct_flavio"], 2),
        "l_votos": num(n["lula"]),
        "f_votos": num(n["flavio"]),
        "l_votos_mi": mi(n["lula"]),
        "f_votos_mi": mi(n["flavio"]),
        "dif_mi": mi(n["margem_lula_votos"]),
        "dif_votos": num(n["margem_lula_votos"]),
        "dif_pp": num(n["margem_lula_pp"], 2),
        "pst": pct(n["pst"]),
        "secoes": num(n["secoes"]),
        "secoes_total": num(n["secoes_total"]),
        "secoes_faltam": num(n["secoes_total"] - n["secoes"]),
        "abst_pct": pct(n["pct_abstencao"]),
        "abst_mi": mi(n["abstencao"]),
        "comp_pct": pct(n["pct_comparecimento"]),
        "comp_mi": mi(n["comparecimento"]),
        "brancos_pct": pct(n["pct_brancos"]),
        "nulos_pct": pct(n["pct_nulos"]),
        "gerado_final": hora(n["gerado_brt"]),
        "data_urna": "/".join(reversed(n["gerado_brt"][:10].split("-")[1:])),
        "ufs_l": str(sum(1 for u in ufs if u["margem_lula_votos"] > 0)),
        "ufs_f": str(sum(1 for u in ufs if u["margem_lula_votos"] < 0)),
        "norte_l": pct(norte["pct_lula"]),
        "norte_f": pct(norte["pct_flavio"]),
        "norte_l_n": num(norte["pct_lula"], 2),
        "norte_f_n": num(norte["pct_flavio"], 2),
        "norte_dif": num(norte["margem_lula_votos"]),
        "norte_validos": num(norte["validos"]),
        "norte_pst": pct(norte["pst"]),
        "norte_abst": pct(norte["pct_abstencao"]),
        "norte_ufs": str(len(norte["ufs"])),
        "ne_l": pct(reg["Nordeste"]["pct_lula"]),
        "ne_vant": mi(reg["Nordeste"]["margem_lula_votos"]),
        "sul_vant": mi(-reg["Sul"]["margem_lula_votos"]),
        "se_vant": mi(-reg["Sudeste"]["margem_lula_votos"]),
        "co_vant": mi(-reg["Centro-Oeste"]["margem_lula_votos"]),
        "sul_f": pct(reg["Sul"]["pct_flavio"]),
        "co_f": pct(reg["Centro-Oeste"]["pct_flavio"]),
        "se_f": pct(reg["Sudeste"]["pct_flavio"]),
        "centro_sul_vant": mi(
            -sum(
                reg[r]["margem_lula_votos"] for r in ("Sul", "Sudeste", "Centro-Oeste")
            )
        ),
        "ext_l": pct(p["exterior"]["pct_lula"]),
        "ext_abst": pct(p["exterior"]["pct_abstencao"]),
    }
    # Norte: a UF que mais pesa em cada lado da balança.
    nu = sorted(
        (u for u in ufs if u["regiao"] == "Norte"),
        key=lambda u: u["margem_lula_votos"],
    )
    v["norte_uf_f"] = NOME_UF[nu[0]["uf"]]
    v["norte_uf_f_vant"] = num(-nu[0]["margem_lula_votos"])
    v["norte_uf_l"] = NOME_UF[nu[-1]["uf"]]
    v["norte_uf_l_vant"] = num(nu[-1]["margem_lula_votos"])
    return v


# ------------------------------------------------------------------ 3 noite


def v_noite() -> dict:
    lt = dado("linha_do_tempo")
    pausas = lt["pausas"]
    sil = pausas["silencio_geral"]
    lac = pausas["maior_lacuna_nacional"]
    serie = [x for x in serie_nacional() if x["min"] >= 0]
    depois = [x for x in serie if x["min"] >= lac["ate_min"] and x["pct_flavio"]]
    acima = [x for x in depois if x["pct_flavio"] > 50]
    maior = max(serie, key=lambda x: x["lote_st"])
    ufs = [x for x in pausas["tabela_do_coletor"] if x["nivel"] != "geral"]
    maior_uf = max((x for x in ufs if x["minutos"]), key=lambda x: x["minutos"])
    leit = sil["leituras_por_classe"]
    susp = noticia(r"suspendeu a totalização às 17h06 com")
    v = {
        "sil_de": hora(sil["ultimo_gerado_antes_brt"]),
        "sil_ate": hora(sil["primeiro_gerado_depois_brt"]),
        "sil_de_s": sil["ultimo_gerado_antes_brt"][11:19],
        "sil_ate_s": sil["primeiro_gerado_depois_brt"][11:19],
        "sil_min": num(sil["minutos"], 1),
        "sil_versoes": num(sil["versoes_geradas_dentro"]),
        "sil_leituras": num(sil["leituras_no_intervalo"]),
        "sil_304": num(leit["nao_modificado"]),
        "sil_404": num(leit["nao_existe"]),
        "nac_versoes": num(len(serie)),
        "lac_st_de": num(lac["st_antes"]),
        "lac_st_ate": num(lac["st_depois"]),
        "f50_de": hora(acima[0]["gerado_brt"]),
        "f50_ate": hora(acima[-1]["gerado_brt"]),
        "f50_max": pct(max(x["pct_flavio"] for x in acima)),
        "f50_n": str(len(acima)),
        "maior_lote_hora": hora(maior["gerado_brt"]),
        "maior_lote_st": num(maior["lote_st"]),
        "maior_lote_f": pct(maior["lote_pct_flavio"]),
        "pausas_uf_n": str(len(ufs)),
        "pausa_uf_max_uf": NOME_UF[maior_uf["uf"]],
        "pausa_uf_max_min": num(maior_uf["minutos"], 1),
        "susp_veic": susp["veiculo"],
        "susp_hora": re.search(r"às (\d+h\d+)", susp["resumo"]).group(1),
        "susp_st": re.search(r"com ([\d.]+) de", susp["resumo"]).group(1),
        "regressivas": num(
            sum(
                x["marcadas_regressivas"]
                for x in lt["regressoes"]["por_nivel"].values()
            )
        ),
        "copias_antigas": num(
            sum(x["copia_antiga"] for x in lt["regressoes"]["por_nivel"].values())
        ),
        "regressivas_genuinas": num(len(lt["regressoes"]["contagem_regressiva"])),
        "versoes_lidas": num(
            sum(x["capturas"] for x in lt["regressoes"]["por_nivel"].values())
        ),
    }
    return v


# ------------------------------------------------------------------ 4 e 5


def v_prorrogacao() -> dict:
    s = dado("secoes")
    pb = s["prorrogacao"]["brasil"]
    enc = s["agregados"]["brasil"]["encerramento"]
    lt = dado("linha_do_tempo")
    dec = noticia(r"^Zanin, na Reclamação")
    aviso = noticia(r"TSE avisou as seções")
    reaj = noticia(r"Zanin reajustou a decisão")
    sp = noticia(r"TRE-SP: mais de")
    relogio = re.search(r"(\d{2}:\d{2})", lt["relogio"]).group(1)
    v = {
        "fim_oficial": hora_h(relogio),
        "fim_novo": hora_h(s["regras"]["apos_hhmm"]),
        "dec_hora": _hora_noticia(dec),
        "dec_veic": dec["veiculo"].split(" (")[0],
        "aviso_hora": re.search(r"às (\d+h\d+)", aviso["resumo"]).group(1),
        "aviso_atraso": re.search(r"(\d+) minutos após", aviso["resumo"]).group(1),
        "aviso_veic": aviso["veiculo"],
        "reaj_hora": _hora_noticia(reaj),
        "reaj_veic": reaj["veiculo"],
        "sp_pct": re.search(r"mais de (\d+%)", sp["resumo"]).group(1),
        "sp_hora": re.search(r"às (\d+h\d+)", sp["resumo"]).group(1),
        "sp_veic": sp["veiculo"],
        "enc_p50": pb["encerramento_p50"],
        "enc_p90": pb["encerramento_p90"],
        "enc_p99": pb["encerramento_p99"],
        "enc_ate_1715": pct(pb["pct_ate_1715"]),
        "emis_p50": pb["emissao_p50"],
        "emis_lag": num(pb["emissao_menos_encerramento_p50_min"], 0),
        "emis_ate_1730": pct(pb["pct_bu_emitido_ate_1730"]),
        "apos19_pct": pct(pb["pct_apos_1900"]),
        "apos19_n": num(pb["n_apos_1900"]),
        "apos18_pct": pct(pb["pct_apos_1800"]),
        "apos19_1t": pct(s["enc_1t_pct"]["apos_1900"]),
        "apos18_1t": pct(s["enc_1t_pct"]["apos_1800"]),
        "amostra_tardias": num(enc["n_tardias"]),
        "amostra_n": num(s["totais"]["secoes"]),
        "secoes_fonte": s["fonte"],
        "enc_p90_1t": enc["p90_1t_mesmas"],
        # transmissão
        "rec_antes19_pct": pct(pb["pct_recebido_antes_1900"], 1),
        "rec_p10": pb["recebimento_p10"],
        "rec_p50": pb["recebimento_p50"],
        "lag_emis_rec": num(pb["lag_emissao_recebimento_p50_min"], 0),
        "lag_enc_rec_p90": num(pb["lag_encerramento_recebimento_p90_min"], 0),
    }
    linhas = tabela(secoes_linhas.bloco(s))
    cedo = [x for x in linhas if x["rec_min"] is not None and x["rec_min"] < 120]
    v["base_antes19_n"] = str(len(cedo))
    v["base_antes19_ate"] = min_hhmm(17 * 60 + int(max(x["rec_min"] for x in cedo)))
    v["base_antes19_ufs"] = str(len({x["uf"] for x in cedo}))
    v["apos19_mun"] = num(len({(x["uf"], x["mun"]) for x in linhas if x["apos_19h"]}))
    por_uf = [
        u
        for u in s["prorrogacao"]["por_uf"]
        if u.get("recebimento_primeiro") and u.get("recebimento_p50")
    ]
    tardio = max(por_uf, key=lambda u: hhmm_min(u["recebimento_primeiro"]))
    v["uf_rec_tardio"] = NOME_UF[tardio["uf"]]
    v["uf_rec_tardio_hora"] = tardio["recebimento_primeiro"]
    lentos = sorted(por_uf, key=lambda u: -u["lag_emissao_recebimento_p50_min"])[:2]
    v["uf_lag_1"] = NOME_UF[lentos[0]["uf"]]
    v["uf_lag_1_min"] = num(lentos[0]["lag_emissao_recebimento_p50_min"], 0)
    v["uf_lag_2"] = NOME_UF[lentos[1]["uf"]]
    v["uf_lag_2_min"] = num(lentos[1]["lag_emissao_recebimento_p50_min"], 0)
    nm = noticia(r"bloqueio de recebimento")
    v["nm_hora"] = _hora_noticia(nm)
    v["nm_veic"] = nm["veiculo"]
    par = dado("paralela")["bus"]
    pares = [
        hhmm_min(b["tse_recebido_brt"]) - hhmm_min(b["recebido_brt"])
        for b in par
        if b.get("tse_recebido_brt") and b.get("recebido_brt")
    ]
    v["par_antes_tse"] = str(sum(1 for d in pares if d > 0))
    v["par_total"] = str(len(par))
    v["par_vantagem"] = num(statistics.median([d for d in pares if d > 0]), 0)
    v["par_antes19"] = str(
        sum(
            1
            for b in par
            if b.get("recebido_min") is not None and b["recebido_min"] < 120
        )
    )
    return v


# ------------------------------------------------------------------ 6 projeção


def _frase_faixa(fora: list[dict], pr: dict) -> str:
    """Frase sobre a cobertura da faixa de 90%, escrita conforme o dado."""
    n = pr["pontos_com_projecao"]
    if fora:
        return (
            f"Nos {len(fora)} últimos pontos, de {fora[0]['hhmm']} a {fora[-1]['hhmm']}, "
            f"o resultado final ficou fora da faixa, a no máximo "
            f"{num(max(x['distancia_pp'] for x in fora), 2)} ponto."
        )
    return (
        f"Nesta versão do arquivo, o resultado final ficou dentro da faixa em "
        f"{pr['pontos_com_final_dentro_da_faixa90']} dos {n} pontos, mas com folga de centésimos."
    )


def v_projecao() -> dict:
    pr = dado("projecao_noite")
    p1 = pr["primeiro_ponto_com_projecao"]
    fora = pr["pontos_fora_da_faixa90"]
    obs = pr["pontos_com_flavio_a_frente_no_observado"]
    pontos = [x for x in pr["pontos"] if x["p_f_projetado"] is not None]
    ultimo = pontos[-1]
    par = pr["parametros"]
    return {
        "proj_n": str(pr["pontos_com_projecao"]),
        "proj_lider_n": str(sum(1 for x in pontos if x["lider_projetado"] == "lula")),
        "proj_p1_hora": p1["hhmm"],
        "proj_p1_pst": pct(p1["pst"]),
        "proj_p1_st": num(p1["st"]),
        "proj_p1_mun": num(p1["municipios_observados"]),
        "proj_p1_f": pct(p1["p_f_projetado"]),
        "proj_p1_obs": pct(p1["p_f_observado"]),
        "proj_p1_faixa": f"{num(p1['faixa90'][0], 2)} a {num(p1['faixa90'][1], 2)}",
        "proj_final": pct(pr["observado_final"]["p_f_entre_os_dois"]),
        "proj_erro_medio": num(pr["erro_absoluto_pp"]["medio"], 2),
        "proj_erro_max": num(pr["erro_absoluto_pp"]["maximo"], 2),
        "proj_dentro": str(pr["pontos_com_final_dentro_da_faixa90"]),
        "proj_faixa_frase": _frase_faixa(fora, pr),
        "proj_ult_faixa": f"{num(ultimo['faixa90'][0], 2)} a {num(ultimo['faixa90'][1], 2)}",
        "proj_obs_n": str(obs["n"]),
        "proj_obs_de": obs["de"],
        "proj_obs_ate": obs["ate"],
        "proj_obs_max": pct(obs["maximo_p_f_observado"]),
        "proj_ult_hora": ultimo["hhmm"],
        "proj_ult_f": pct(ultimo["p_f_projetado"]),
        "proj_k": num(par["K"]),
        "proj_k_uf": num(par["K_uf"]),
        "proj_reps": num(par["reps"]),
        "proj_erro_comum": num(par["erro_comum_pp"]),
        "proj_min_pst": num(par["minimo_pst"]),
        "proj_aovivo_n": num(len(pr["serie_ao_vivo"]["linhas"])),
    }


# ------------------------------------------------------------------ 7 cedo e tarde


def v_cedo_tarde() -> dict:
    ct = dado("cedo_tarde")
    d = ct["decis_2t"]
    sw = [x["swing_h2h_flavio_pp"] for x in d]
    zs = [x["swing_h2h_flavio_pp"] for x in ct["zonas"]["decis"]]
    concl = dado("linha_do_tempo")["conclusao_ufs"]
    comp = [u for u in concl if u["fechou_brt"] and u["uf"] != "ZZ"]
    antes = [
        u
        for u in comp
        if u["atraso_vs_1t_descontada_prorrogacao_min"] is not None
        and u["atraso_vs_1t_descontada_prorrogacao_min"] < 0
    ]
    relogio = [u for u in comp if u["atraso_vs_1t_min"] > 0]
    mun = tabela(dado("presidente")["municipios"])
    cedo = [m for m in mun if m.get("fechou_min") is not None and m["fechou_min"] < 120]
    pa = cedo[0] if cedo else None
    v = {
        "ct_n": num(ct["n_municipios"]),
        "ct_d1": pct(d[0]["h2h_flavio"]),
        "ct_d10": pct(d[-1]["h2h_flavio"]),
        "ct_dmax": pct(max(x["h2h_flavio"] for x in d)),
        "ct_d1_ate": d[0]["fechou_hhmm_ate"],
        "ct_d10_de": d[-1]["fechou_hhmm_de"],
        "ct_d10_ate": d[-1]["fechou_hhmm_ate"],
        "ct_sw_menor": sinal(max(sw)),
        "ct_sw_maior": sinal(min(sw)),
        "ct_sw_d1": sinal(d[0]["swing_h2h_flavio_pp"]),
        "ct_sw_d10": sinal(d[-1]["swing_h2h_flavio_pp"]),
        "ct_zonas_n": num(ct["zonas"]["n"]),
        "ct_z_menor": sinal(max(zs)),
        "ct_z_maior": sinal(min(zs)),
        "ct_d10_aptos": mi(d[-1]["aptos"]),
        "ct_d1_aptos": mi(d[0]["aptos"]),
        "ct_d10_cap": str(d[-1]["capitais"]),
        "ct_d1_cap": str(d[0]["capitais"]),
        "ct_sp_tam": num(ct["spearman_tamanho_x_fechamento_2t"], 2),
        "ct_sp_ordem": num(ct["spearman_ordem_1t_x_2t"], 2),
        "ct_ufs_comp": str(len(comp)),
        "ct_ufs_antes": str(len(antes)),
        "ct_ufs_relogio": str(len(relogio)),
        "ct_uf_primeira": NOME_UF[comp[0]["uf"]],
        "ct_uf_primeira_hora": hora(comp[0]["fechou_brt"]),
        "ct_cedo_n": str(len(cedo)),
    }
    if pa:
        v["ct_pa_nome"] = nome_proprio(pa["nome"])
        v["ct_pa_uf"] = pa["uf"]
        v["ct_pa_secoes"] = str(pa["secoes"])
        v["ct_pa_hora"] = pa["fechou_hhmm"]
    return v


# ------------------------------------------------------------------ 8 1T × 2T


def v_turnos() -> dict:
    c = dado("comparacao_1t")
    b = c["brasil"]
    ufs = sorted(c["ufs"], key=lambda u: u["swing_h2h_flavio_pp"])
    pv = dado("pesquisas_vs_urna")
    cont = pv["hipoteses"]["contabilidade_entre_turnos"]
    cb = cont["brasil"]
    c22 = dado("comparacao_2022")
    perdas = c["flavio_maiores_perdas"]
    return {
        "t_h2h_1t": pct(b["t1_h2h_flavio"]),
        "t_h2h_2t": pct(b["t2_h2h_flavio"]),
        "t_swing": sinal(b["swing_h2h_flavio_pp"]),
        "t_mun": num(b["n_municipios"]),
        "t_ufs_caiu": str(sum(1 for u in ufs if u["swing_h2h_flavio_pp"] < 0)),
        "t_ufs": str(len(ufs)),
        "t_uf_maior": NOME_UF[ufs[0]["uf"]],
        "t_uf_maior_sw": sinal(ufs[0]["swing_h2h_flavio_pp"]),
        "t_uf_menor": NOME_UF[ufs[-1]["uf"]],
        "t_uf_menor_sw": sinal(ufs[-1]["swing_h2h_flavio_pp"]),
        "t_mun_l": num(c["dispersao_municipal"]["n_swing_h2h_pro_lula"]),
        "t_mun_f": num(c["dispersao_municipal"]["n_swing_h2h_pro_flavio"]),
        "t_mediana": sinal(c["dispersao_municipal"]["swing_h2h_flavio_pp"]["mediana"]),
        "t_desvio": num(c["dispersao_municipal"]["swing_h2h_flavio_pp"]["desvio"], 2),
        "t_ganho_f": mi(b["delta_votos_flavio"]),
        "t_ganho_l": mi(b["delta_votos_lula"]),
        "t_terc": mi(b["t1_terceiros"]),
        "t_f_terc": pct(b["ganho_flavio_sobre_terceiros_pct"], 1),
        "t_l_terc": pct(b["ganho_lula_sobre_terceiros_pct"], 1),
        "t_disp": mi(cb["disponivel"]),
        "t_disp_terc": mi(cb["terceiros_1t"]),
        "t_disp_bn": mi(cb["branco_nulo_1t"] - cb["branco_nulo_2t"]),
        "t_disp_comp": mi(cb["variacao_comparecimento"]),
        "t_parcela_f": pct(cb["parcela_flavio_do_ganho_pct"], 1),
        "t_teto_f": pct(cb["teto_parcela_flavio_da_terceira_via_pct"], 1),
        "t_perdeu": num(c["flavio_perdeu_votos"]["n"]),
        "t_ganhou": num(c["flavio_ganhou_votos"]["n"]),
        "t_l_perdeu": num(c["lula_perdeu_votos"]["n"]),
        "t_perda1": nome_proprio(perdas[0]["nome"]),
        "t_perda1_uf": perdas[0]["uf"],
        "t_perda1_v": num(-perdas[0]["delta_votos_flavio"]),
        "t_perda2": nome_proprio(perdas[1]["nome"]),
        "t_perda2_uf": perdas[1]["uf"],
        "t_perda2_v": num(-perdas[1]["delta_votos_flavio"]),
        "t22_l": pct(c22["brasil"]["r22_pct_lula"]),
        "t22_l26": pct(c22["brasil"]["pct_lula"]),
        "t22_sw": sinal(c22["brasil"]["swing_lula_pp"]),
        "t22_l_f": num(c22["viraram"]["lula_2022_para_flavio_2026"]),
        "t22_b_l": num(c22["viraram"]["bolsonaro_2022_para_lula_2026"]),
        "t22_mun_caiu": num(c22["n_lula_caiu"]),
    }


# ------------------------------------------------------------------ 9 abstenção


def v_abstencao() -> dict:
    a = dado("abstencao")
    br = a["brasil"]
    pv = dado("pesquisas_vs_urna")
    t1 = pv["urna"]["primeiro_turno_brasil"]
    cont = pv["hipoteses"]["contabilidade_entre_turnos"]
    subiu = sorted(
        (u for u in a["ufs"] if u["arquivo_uf"]["delta_1t_pp"] > 0),
        key=lambda u: -u["arquivo_uf"]["delta_1t_pp"],
    )
    caiu = min(a["ufs"], key=lambda u: u["arquivo_uf"]["delta_1t_pp"])
    reg = {r["regiao"]: r for r in a["regioes"]}
    rank = a["ranking_ufs_menor_abstencao"]
    cnn = noticia(r"menor desde 2006")
    cc = a["capitais_x_interior"]
    return {
        "ab_2t": pct(pv["urna"]["brasil"]["abstencao_pct"]),
        "ab_1t": pct(t1["abstencao_pct"]),
        "ab_mais_votaram": mi(cont["brasil"]["variacao_comparecimento"]),
        "ab_mun": num(br["n_municipios"]),
        "ab_mesmos_2t": pct(br["pa_2t"]),
        "ab_mesmos_1t": pct(br["pa_1t_mesmos"]),
        "ab_mesmos_22": pct(br["pa_2022_2t_mesmos"]),
        "ab_d1t": sinal(br["delta_1t_pp"]),
        "ab_d22": sinal(br["delta_2022_pp"]),
        "ab_d22_abs": num(abs(br["delta_2022_pp"]), 2),
        "ab_cnn_veic": cnn["veiculo"],
        "ab_cnn_hora": _hora_noticia(cnn),
        "ab_cnn_valor": re.search(r"2006 \(([\d,]+%)\)", cnn["resumo"]).group(1),
        "ab_tse": re.search(r"Abstenção de ([\d,]+%)", cnn["resumo"]).group(1),
        "ab_subiu_n": str(len(subiu)),
        "ab_sub1": NOME_UF[subiu[0]["uf"]],
        "ab_sub1_v": sinal(subiu[0]["arquivo_uf"]["delta_1t_pp"]),
        "ab_sub2": NOME_UF[subiu[1]["uf"]],
        "ab_sub2_v": sinal(subiu[1]["arquivo_uf"]["delta_1t_pp"]),
        "ab_sub3": NOME_UF[subiu[2]["uf"]],
        "ab_sub3_v": sinal(subiu[2]["arquivo_uf"]["delta_1t_pp"]),
        "ab_sub_resto": _lista([NOME_UF[u["uf"]] for u in subiu[3:]]),
        "ab_sub_resto_n": str(len(subiu) - 3),
        "ab_queda_max": num(-caiu["arquivo_uf"]["delta_1t_pp"], 2),
        "ab_queda_max_uf": NOME_UF[caiu["uf"]],
        "ab_norte_1t": pct(reg["Norte"]["pa_1t_mesmos"]),
        "ab_norte_2t": pct(reg["Norte"]["pa_2t"]),
        "ab_menor_uf": NOME_UF[rank[0]["uf"]],
        "ab_menor_v": pct(rank[0]["pa_2t"]),
        "ab_caiu_mun": num(a["n_municipios_caiu_vs_1t"]),
        "ab_subiu_mun": num(a["n_municipios_subiu_vs_1t"]),
        "ab_cap": pct(cc["capitais"]["pa_2t"]),
        "ab_cap_d": sinal(cc["capitais"]["delta_1t_pp"]),
        "ab_int": pct(cc["interior"]["pa_2t"]),
        "ab_int_d": sinal(cc["interior"]["delta_1t_pp"]),
        "ab_corr_res": sinal(cont["correlacao_variacao_abstencao_com_residuo"], 2),
        "ab_corr_terc": sinal(cont["correlacao_terceiros_1t_com_residuo"], 2),
        "ab_teto": num(cont["limite_comparecimento"]["parcela_maxima_explicada_pp"], 2),
    }


__all__ = [
    "NOME_UF",
    "hora",
    "noticia",
    "serie_nacional",
    "v_abstencao",
    "v_cedo_tarde",
    "v_noite",
    "v_projecao",
    "v_prorrogacao",
    "v_resultado",
    "v_turnos",
]
