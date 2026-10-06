"""Valores formatados da super thread, um dicionário por tema.

Cada chave vira campo ``{chave}`` nos modelos dos posts. Nada aqui é digitado:
tudo é lido dos JSONs do dossiê e formatado por ``thread_base``.
"""

from __future__ import annotations

import math

from .thread_base import (
    dado,
    hora,
    hora_seg,
    mi,
    nome_proprio,
    num,
    pct,
    sinal,
    tabela,
)


def _ufs_presidente() -> list[dict]:
    return [u for u in dado("presidente")["ufs"] if u["uf"] != "ZZ"]


def capitais_interior() -> dict:
    """Capitais × interior por região: swing de Flávio e de Lula contra o 1º turno."""
    p = dado("presidente")
    caps = p["capitais"]
    out = {}
    for reg in ("Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"):
        tot = p["regioes"][reg]
        c = [x for x in caps if x["regiao"] == reg]
        cap = {
            "f26": sum(x["flavio"] for x in c),
            "l26": sum(x["lula"] for x in c),
            "v26": sum(x["validos"] for x in c),
            "b22": sum(x["bolsonaro_2022_1t"] for x in c),
            "l22": sum(x["lula_2022_1t"] for x in c),
            "v22": sum(x["validos_2022_1t"] for x in c),
        }
        r26, r22 = tot["r2026"], tot["r2022"]["t1"]
        inte = {
            "f26": r26["votos"]["flavio"] - cap["f26"],
            "l26": r26["votos"]["lula"] - cap["l26"],
            "v26": r26["validos"] - cap["v26"],
            "b22": r22["votos"]["bolsonaro"] - cap["b22"],
            "l22": r22["votos"]["lula"] - cap["l22"],
            "v22": r22["validos"] - cap["v22"],
        }
        linha = {}
        for nome, g in (("capitais", cap), ("interior", inte)):
            linha[nome] = {
                "flavio": 100 * g["f26"] / g["v26"],
                "swing_flavio": 100 * (g["f26"] / g["v26"] - g["b22"] / g["v22"]),
                "swing_lula": 100 * (g["l26"] / g["v26"] - g["l22"] / g["v22"]),
                "validos": g["v26"],
            }
        out[reg] = linha
    return out


def v_resultado() -> dict:
    n = dado("presidente")["nacional"]
    ufs = _ufs_presidente()
    versoes = list(tabela(dado("linha_do_tempo")["nacional"]["versoes"]))
    com_secoes = [x for x in versoes if x["st"] > 0]
    v = {
        "f_votos": num(n["votos"]["flavio"]),
        "l_votos": num(n["votos"]["lula"]),
        "f_pct": pct(n["pct"]["flavio"]),
        "l_pct": pct(n["pct"]["lula"]),
        "f_pct_n": num(n["pct"]["flavio"], 2),
        "l_pct_n": num(n["pct"]["lula"], 2),
        "dif_votos": num(n["diferenca_votos"]),
        "dif_mi": mi(n["diferenca_votos"]),
        "dif_pp": num(n["diferenca_pp"], 2),
        "terc_votos": num(n["votos"]["terceiros"]),
        "terc_mi": mi(n["votos"]["terceiros"]),
        "terc_pct": pct(n["pct"]["terceiros"]),
        "cury_pct": pct(n["pct"]["cury"]),
        "renan_pct": pct(n["pct"]["renan"]),
        "caiado_pct": pct(n["pct"]["caiado"]),
        "comp_pct": pct(n["pct_comparecimento"]),
        "abst_mi": mi(n["abstencao"]),
        "secoes": num(n["secoes"]),
        "ufs_f": str(sum(1 for u in ufs if u["lider"] == "flavio")),
        "ufs_l": str(sum(1 for u in ufs if u["lider"] == "lula")),
        "versoes_secoes": num(len(com_secoes)),
        "versoes_f_frente": num(sum(1 for x in com_secoes if x["flavio"] > x["lula"])),
        "gerado_final": hora_seg(n["gerado_em_brt"]),
        "brancos_pct": pct(n["pct_brancos"]),
        "nulos_pct": pct(n["pct_nulos"]),
        "segundo_ordinal": "2º",
    }
    return v


def v_noite() -> dict:
    nr = dado("noite_regioes")
    lid, dec = nr["lideranca"], nr["decomposicao"]
    comp = nr["composicao_apurada"][dec["pico_brt"]]
    d99, d00 = nr["depois_dos_99"], nr["depois_da_meia_noite"]
    ne = nr["nordeste"]
    return {
        "primeiro_min": hora(lid["primeiro_minuto_com_votos"]),
        "pico_hora": hora(dec["pico_brt"]),
        "pico_pp": num(dec["pico_pp"], 1),
        "pico_pst": pct(lid["maior_vantagem_pp"]["pst"], 1),
        "pico_peso_final": num(dec["pico_peso_final_pp"], 1),
        "final_pp": num(dec["final_pp"], 1),
        "queda_pp": num(dec["queda_pp"], 1),
        "entre_pp": num(dec["entre_regioes_pp"], 1),
        "dentro_pp": num(dec["dentro_das_regioes_pp"], 1),
        "entre_pct": pct(dec["entre_regioes_pct_da_queda"], 1),
        "maior_votos": mi(lid["maior_vantagem_votos"]["votos"]),
        "maior_votos_hora": hora(lid["maior_vantagem_votos"]["hora_brt"]),
        "lula_minutos": str(lid["minutos_com_lula_a_frente"]),
        "ne_apurado_pico": pct(comp["Nordeste"]["apurado_pct"], 1),
        "ne_final": pct(comp["Nordeste"]["final_pct"], 1),
        "sul_apurado_pico": pct(comp["Sul"]["apurado_pct"], 1),
        "sul_final": pct(comp["Sul"]["final_pct"], 1),
        "ne_desde": hora(ne["acima_do_proprio_peso_desde"]["de_brt"]),
        "ne_maior_faltava": pct(ne["maior_do_que_faltava"]["parcela_nordeste_pct"], 1),
        "ne_maior_faltava_hora": hora(ne["maior_do_que_faltava"]["hora_brt"]),
        "d99_hora": hora(d99["desde_brt"]),
        "d99_secoes": num(d99["st"]),
        "d99_lula": pct(d99["pct_lula"], 1),
        "d00_secoes": num(d00["st"]),
        "d00_validos": num(d00["vv"]),
        "d00_lula": pct(d00["pct_lula"], 1),
    }


def v_falha() -> dict:
    lt = dado("linha_do_tempo")
    tr = [x for x in lt["travamentos"]["nacional"] if x["pst_ate"] < 99.5]
    pg = lt["pausa_geral"]["lacunas"][0]
    arq = dado("arquitetura")
    rec = arq["recebimento_2026"]
    des = rec["desaceleracao"]
    div = lt["divergencia_soma_ufs"]["maior_diferenca_visivel"]
    longa = arq["nacional"]["parada_mais_longa"]
    lotes = [
        x
        for x in tabela(lt["nacional"]["versoes"])
        if x["gerado_brt"] == longa["ate_brt"]
    ]
    v = {
        "pausa_de": hora_seg(pg["de_brt"]),
        "pausa_ate": hora_seg(pg["ate_brt"]),
        "pausa_min": num(pg["minutos"], 1),
        "pausa_leituras": num(sum(pg["leituras_no_intervalo"].values())),
        "pausa_304": num(pg["leituras_no_intervalo"]["nao_modificado"]),
        "pausa_ab": num(len(pg["versoes_de_andamento_ab_no_intervalo"])),
        "des_razao": pct(100 * des["razao"], 0),
        "des_de": des["janela"][0],
        "des_ate": des["janela"][1],
        "des_media": num(des["media_janela"]),
        "des_base": num(des["media_base"]),
        "div_hora": div["hora_brt"],
        "div_secoes": num(div["secoes"]),
        "div_pp": pct(div["pp_do_total"], 1),
        "longa_secoes": num(longa["secoes_no_salto"]),
        "longa_leituras": num(longa["leituras_no_intervalo"]["total"]),
        "longa_304": num(
            longa["leituras_no_intervalo"]["por_classe"]["nao_modificado"]
        ),
        "n_paradas": str(len(tr)),
        "n_lacunas_carimbo": str(len(rec["lacunas"])),
    }
    if lotes:
        v["lote_vv"] = mi(lotes[0]["d_vv"])
    for i, p in enumerate(tr, 1):
        v[f"p{i}_de"] = hora_seg(p["de_brt"])
        v[f"p{i}_ate"] = hora_seg(p["ate_brt"])
        v[f"p{i}_min"] = num(p["minutos"], 1)
        v[f"p{i}_pst_de"] = pct(p["pst_de"], 1)
        v[f"p{i}_pst_ate"] = pct(p["pst_ate"], 1)
    for i, lac in enumerate(rec["lacunas"], 1):
        v[f"c{i}_de"] = hora(lac["de"])
        v[f"c{i}_ate"] = hora(lac["ate"])
        v[f"c{i}_min"] = num(lac["minutos"], 1)
    return v


def v_arquitetura() -> dict:
    a = dado("arquitetura")
    vol, nac, pub = a["volume"], a["nacional"], a["publicacao_2026"]
    r22 = a["recebimento_2022"]
    return {
        "nota_linhas_min": mi(vol["linhas_por_minuto_nota_tse_2020"], 1),
        "pico_linhas_min": num(vol["pico_linhas_por_minuto"]),
        "pico_linhas_s": num(vol["pico_linhas_por_segundo"]),
        "pico_secoes_s": num(vol["pico_secoes_por_segundo"], 0),
        "pico_mb_min": num(vol["pico_bu_mb_por_minuto"], 0),
        "bu_total_gb": num(vol["bu_total_mb"] / 1024, 1),
        "linhas_total": mi(vol["linhas_voto_total"], 1),
        "represadas_secoes": num(vol["secoes_represadas"]),
        "represadas_linhas": mi(vol["linhas_represadas"], 1),
        "represadas_gb": num(vol["mb_represados_bu"] / 1024, 1),
        "sust_secoes_min": num(nac["pico_sustentado"]["secoes_por_minuto"]),
        "pub_pico_versoes": num(pub["pico_versoes"]["versoes"]),
        "pub_pico_versoes_hora": pub["pico_versoes"]["minuto"],
        "pub_pico_mb": num(pub["pico_mb"]["mb"], 0),
        "pub_mediana": num(pub["mediana_versoes_por_minuto_18h_19h30"]),
        "r22_pico": num(r22["pico"]["secoes"]),
        "r22_pico_hora": r22["pico"]["minuto"],
        "r22_p50": num(r22["atraso_recebimento_totalizacao_s"]["p50"], 0),
        "versoes_banco": num(pub["versoes_total_banco"]),
        "fracao_nota": pct(
            100
            * vol["pico_linhas_por_minuto"]
            / vol["linhas_por_minuto_nota_tse_2020"],
            0,
        ),
    }


def v_regioes() -> dict:
    p = dado("presidente")
    n = p["nacional"]
    c1 = n["comparacao"]
    ci = capitais_interior()
    mun = [
        m
        for m in tabela(p["municipios"])
        if m["completo"] and m["swing_flavio_pp"] is not None
    ]
    reg = p["regioes"]
    ne, cs = reg["Nordeste"], reg["Centro-Sul"]
    perda_lula = c1["lula_vs_lula_1t"]["votos"]
    v = {
        "f_swing_pp": sinal(c1["flavio_vs_bolsonaro_1t"]["pp"]),
        "f_swing_votos": mi(c1["flavio_vs_bolsonaro_1t"]["votos"]),
        "l_swing_pp": sinal(c1["lula_vs_lula_1t"]["pp"]),
        "l_swing_votos": mi(perda_lula),
        "margem_virou": num(
            c1["flavio_vs_bolsonaro_1t"]["pp"] - c1["lula_vs_lula_1t"]["pp"], 2
        ),
        "ufs_f_cresceu": str(
            sum(
                1
                for u in _ufs_presidente()
                if u["comparacao"]["flavio_vs_bolsonaro_1t"]["pp"] > 0
            )
        ),
        "mun_f_cresceu": num(sum(1 for m in mun if m["swing_flavio_pp"] > 0)),
        "mun_total": num(len(mun)),
        "mun_l_cresceu": num(sum(1 for m in mun if m["swing_lula_pp"] > 0)),
        "cs_perda": mi(cs["comparacao"]["lula_vs_lula_1t"]["votos"]),
        "cs_perda_pct": pct(
            100 * cs["comparacao"]["lula_vs_lula_1t"]["votos"] / perda_lula, 1
        ),
        "ne_perda": mi(ne["comparacao"]["lula_vs_lula_1t"]["votos"]),
        "ne_flavio": pct(ne["r2026"]["pct"]["flavio"]),
        "ne_bols_2t": pct(ne["r2022"]["t2"]["pct"]["bolsonaro"]),
        "ne_ganho": mi(ne["comparacao"]["flavio_vs_bolsonaro_1t"]["votos"]),
    }
    for reg_nome, chave in (("Nordeste", "ne"), ("Sudeste", "se"), ("Sul", "sul")):
        for g in ("capitais", "interior"):
            v[f"{chave}_{g[:3]}_f"] = sinal(ci[reg_nome][g]["swing_flavio"])
            v[f"{chave}_{g[:3]}_l"] = sinal(ci[reg_nome][g]["swing_lula"])
    return v


def v_exterior() -> dict:
    e = dado("exterior")
    zz = next(u for u in dado("presidente")["ufs"] if u["uf"] == "ZZ")
    pais = {x["pais"]: x for x in e["paises"]}
    cont = {x["continente"]: x for x in e["continentes"]}
    tot = e["total"]
    pt, jp, us = pais["PT"], pais["JP"], pais["US"]
    return {
        "ext_l": pct(zz["pct"]["lula"]),
        "ext_f": pct(zz["pct"]["flavio"]),
        "ext_margem": num(zz["votos"]["lula"] - zz["votos"]["flavio"]),
        "ext_eleitores": num(tot["eleitores"]),
        "ext_eleitores_22": num(zz["r2022"]["t1"]["eleitores"]),
        "ext_comp": pct(tot["pct_comparecimento"]),
        "ext_comp_22": pct(zz["r2022"]["t1"]["pct_comparecimento"]),
        "ext_cidades": num(tot["cidades"]),
        "ext_paises": num(tot["paises"]),
        "pt_f": pct(pt["pct"]["flavio"]),
        "pt_swing": sinal(pt["swing_flavio_vs_bolsonaro_1t_pp"]),
        "pt_l_swing": sinal(pt["swing_lula_vs_lula_1t_pp"]),
        "jp_f": pct(jp["pct"]["flavio"]),
        "us_f": pct(us["pct"]["flavio"]),
        "eur_l": pct(cont["Europa"]["pct"]["lula"]),
        "an_f": pct(cont["América do Norte"]["pct"]["flavio"]),
    }


def v_camara() -> dict:
    c = dado("camara")
    cp = dado("comparacao_2022")["camara"]
    vagas = c["vagas_total"]
    pc, pp_ = c["por_campo"], c["por_partido"]
    top = c["deputados_mais_votados"][0]
    return {
        "cam_vagas": num(vagas),
        "cam_bloco_d": num(c["blocos"]["direita + centro-direita"]),
        "cam_bloco_e": num(c["blocos"]["esquerda + centro-esquerda"]),
        "cam_centro": num(c["blocos"]["centro"]),
        "cam_direita": num(pc["direita"]),
        "cam_cd": num(pc["centro-direita"]),
        "cam_esq": num(pc["esquerda"]),
        "cam_delta_direita": sinal(cp["delta_campo"]["direita"], 0),
        "cam_ganho_direita": num(cp["delta_campo"]["direita"]),
        "cam_delta_bloco_d": sinal(cp["delta_bloco"]["direita + centro-direita"], 0),
        "cam_delta_bloco_e": sinal(cp["delta_bloco"]["esquerda + centro-esquerda"], 0),
        "cam_bloco_d_22": num(cp["por_bloco_2022"]["direita + centro-direita"]),
        "cam_tres_quintos": num(math.ceil(vagas * 3 / 5)),
        "cam_maioria": num(vagas // 2 + 1),
        "cam_pl": num(pp_["PL"]),
        "cam_pt": num(pp_["PT"]),
        "cam_votos_d": pct(c["votos_por_campo_pct"]["direita"], 1),
        "cam_votos_e": pct(c["votos_por_campo_pct"]["esquerda"], 1),
        "cam_cadeiras_d": pct(c["por_campo_pct"]["direita"], 1),
        "cam_top_nome": nome_proprio(top["nome"]),
        "cam_top_votos": mi(top["votos"]),
        "cam_top_pct": pct(top["pct_na_uf"], 1),
        "cam_provisorias": ", ".join(c["ufs_provisorias"]),
        "cam_n_prov": str(c["n_ufs_provisorio"]),
    }


def v_senado() -> dict:
    s = dado("senado")
    s27 = s["senado_2027"]
    sx = dado("senado_x_flavio")
    nac = sx["nacional"]
    acima = sorted(
        (u for u in sx["ufs"] if u["melhor"]["vao_votantes_pp"] > 0),
        key=lambda u: -u["melhor"]["vao_votantes_pp"],
    )
    total = s27["total"]
    return {
        "sen_total": num(total),
        "sen_bloco_d": num(s27["por_bloco"]["direita + centro-direita"]),
        "sen_bloco_e": num(s27["por_bloco"]["esquerda + centro-esquerda"]),
        "sen_centro": num(s27["por_bloco"]["centro"]),
        "sen_tres_quintos": num(math.ceil(total * 3 / 5)),
        "sen_pl": num(s27["por_partido"]["PL"]),
        "sen_pl_2026": num(s["eleitos_2026_por_partido"]["PL"]),
        "sen_pt": num(s27["por_partido"]["PT"]),
        "sen_novos": num(s27["novos"]),
        "sen_continuam": num(s27["continuam"]),
        "sen_aliados_pct": pct(nac["aliados"]["pct"]),
        "sen_flavio_pct": pct(nac["flavio"]["pct"]),
        "sen_aliados_por_voto": num(nac["aliados"]["votos_por_voto_flavio"], 2),
        "sen_pl_ufs_abaixo": str(nac["pl"]["ufs_abaixo_de_flavio"]),
        "sen_ufs_acima": str(len(acima)),
        "sen_acima_lista": ", ".join(
            f"{nome_proprio(u['melhor']['nome'])} ({u['uf']}, "
            f"{sinal(u['melhor']['vao_votantes_pp'], 1)})"
            for u in acima[:5]
        ),
        "sen_ufs_acima_base": str(nac["melhor"]["ufs_acima_na_base"]),
    }


def v_assembleias() -> dict:
    a = dado("assembleias")
    cp = {c["uf"]: c for c in dado("comparacao_2022")["assembleias"]["casas"]}
    casas = {c["uf"]: c for c in a["casas"]}
    sp, mg, ba, ce = casas["SP"], casas["MG"], casas["BA"], casas["CE"]
    top = sp["mais_votados"][0]
    soma_d = sum(c["blocos"]["direita + centro-direita"] for c in a["casas"])
    soma_v = sum(c["vagas"] for c in a["casas"])
    soma_d22 = sum(cp[u]["por_bloco_2022"]["direita + centro-direita"] for u in cp)
    maioria = [
        c["uf"]
        for c in a["casas"]
        if c["blocos"]["direita + centro-direita"] * 2 > c["vagas"]
    ]
    return {
        "ass_n": str(len(a["casas"])),
        "ass_vagas": num(soma_v),
        "ass_bloco_d": num(soma_d),
        "ass_bloco_d_22": num(soma_d22),
        "ass_maioria_n": str(len(maioria)),
        "ass_maioria_lista": ", ".join(maioria),
        "sp_vagas": num(sp["vagas"]),
        "sp_d": num(sp["por_campo"]["direita"]),
        "sp_esq": num(sp["por_campo"]["esquerda"]),
        "sp_bloco_d": num(sp["blocos"]["direita + centro-direita"]),
        "sp_delta_d": sinal(cp["SP"]["delta_campo"]["direita"], 0),
        "sp_top_nome": nome_proprio(top["nome"]),
        "sp_top_votos": mi(top["votos"]),
        "mg_vagas": num(mg["vagas"]),
        "mg_d": num(mg["por_campo"]["direita"]),
        "mg_bloco_d": num(mg["blocos"]["direita + centro-direita"]),
        "ba_vagas": num(ba["vagas"]),
        "ba_esq": num(ba["por_campo"]["esquerda"]),
        "ce_vagas": num(ce["vagas"]),
        "ce_esq": num(ce["por_campo"]["esquerda"]),
    }


def _vao_principal() -> list[dict]:
    lista = dado("governadores")["vao_estadual"]["lista"]
    return [x for x in lista if x["principal"]]


def v_governadores() -> dict:
    g = dado("governadores")
    lista = {x["uf"]: x for x in _vao_principal()}
    lucas = lista["pb"]

    def vf(uf):
        return sinal(lista[uf]["vao_pp"], 1)

    return {
        "gov_1t": str(g["n_eleitos_1t"]),
        "gov_2t": str(g["n_segundo_turno"]),
        "gov_2t_lista": ", ".join(
            sorted(
                {
                    x["uf"].upper()
                    for x in g["vao_estadual"]["lista"]
                    if x["decisao"] == "segundo_turno"
                }
            )
        ),
        "gov_d": str(g["eleitos_1t_por_campo"]["direita"]),
        "gov_cd": str(g["eleitos_1t_por_campo"]["centro-direita"]),
        "gov_c": str(g["eleitos_1t_por_campo"]["centro"]),
        "gov_e": str(g["eleitos_1t_por_campo"]["esquerda"]),
        "vao_sp": vf("sp"),
        "vao_mg": vf("mg"),
        "vao_al": vf("al"),
        "vao_ms": vf("ms"),
        "vao_pa": vf("pa"),
        "vao_pr": vf("pr"),
        "vao_ro": vf("ro"),
        "vao_ac": vf("ac"),
        "vao_ce": vf("ce"),
        "vao_ba": vf("ba"),
        "vao_rn": vf("rn"),
        "vao_pb_flavio": sinal(lucas["vao_flavio_pp"], 1),
        "vao_ma": vf("ma"),
        "vao_pe": vf("pe"),
        "sp_tarc": pct(lista["sp"]["pct_governador"]),
        "sp_flavio": pct(lista["sp"]["pct_presidenciavel"]),
        "vao_pos": str(
            sum(
                1
                for x in lista.values()
                if x["finalista"] == "flavio" and x["vao_pp"] > 0
            )
        ),
        "vao_neg": str(
            sum(
                1
                for x in lista.values()
                if x["finalista"] == "flavio" and x["vao_pp"] < 0
            )
        ),
    }


def v_pesquisas() -> dict:
    p = dado("pesquisas_vs_urna")
    m = p["medias"]
    ro = p["resumo_ultimas_ondas"]["publicado"]
    pc = p["previsao_casa"]
    mc = pc["monte_carlo"]
    ult = [x for x in p["efeito_reponderacao"]["por_onda"] if x["ultima_onda_da_casa"]]
    aprox = sum(1 for x in ult if x["direcao"] == "aproximou")
    erro_central = pc["central"]["erro_diferenca_lula_menos_flavio"]
    ondas = {o["id"]: o for o in p["pesquisas"]}
    erros = [
        abs(ondas[i]["publicado"]["diferenca_lula_menos_flavio"]["erro"])
        for i in m["ultimas_ondas_publicado"]["ondas"]
    ]
    sen = p["senado"]["resumo"]
    gov = p["governador"]["resumo"]
    ref = p["referencia_2022"]
    return {
        "erro_comum": sinal(
            m["ultimas_ondas_publicado"]["diferenca_lula_menos_flavio"]["erro"]
        ),
        "erro_mediana": sinal(ro["mediana"]),
        "erro_2022": sinal(ref["erro_comum_diferenca_lula_menos_bolsonaro"]),
        "n_casas": str(ro["n"]),
        "casas_lula": str(ro["positivos"]),
        "casas_fora": str(ro["fora_da_margem_aas"]),
        "pesq_dif": sinal(
            m["ultimas_ondas_publicado"]["diferenca_lula_menos_flavio"]["pesquisa"]
        ),
        "pesq_f": pct(m["ultimas_ondas_publicado"]["validos_blocos"]["flavio"]),
        "pesq_l": pct(m["ultimas_ondas_publicado"]["validos_blocos"]["lula"]),
        "agr_pub": sinal(
            m["agregador_publicado"]["diferenca_lula_menos_flavio"]["erro"]
        ),
        "agr_rep": sinal(
            m["agregador_reponderado"]["diferenca_lula_menos_flavio"]["erro"]
        ),
        "rep_n": str(len(ult)),
        "rep_aprox": str(aprox),
        "central_f": pct(pc["central"]["validos"]["flavio"]),
        "central_l": pct(pc["central"]["validos"]["lula"]),
        "central_erro": sinal(erro_central),
        "central_melhor_que": str(sum(1 for e in erros if e > abs(erro_central))),
        "central_p": pct(100 * mc["p_flavio_a_frente_de_lula"], 0),
        "central_percentil": num(
            100 * mc["margem_flavio_menos_lula"]["percentil_urna"], 0
        ),
        "sen_brier": num(sen["brier"], 3),
        "sen_brier_uniforme": num(sen["brier_uniforme_2_sobre_k"], 3),
        "sen_acertos": str(sen["acertos_top2"]),
        "sen_vagas": str(sen["vagas"]),
        "gov_acertos": str(gov["acertos_lider"]),
        "gov_decididos": str(gov["decididos_1t_urna"]),
        "gov_esperado": num(gov["decididos_1t_esperado"], 1),
        "prob_meio_ponto": pct(
            100 * p["resumo_ultimas_ondas"]["prob_alguma_casa_a_meio_ponto_por_acaso"],
            0,
        ),
    }


def v_voto_util() -> dict:
    vu = dado("voto_util")
    tc = vu["terceiros_por_candidato"]["publicado"]
    urna = vu["terceiros_por_candidato"]["urna_validos"]
    pub = vu["terceira_via"]
    dec = vu["decomposicao"]["agregados"]["ultimas_ondas_publicado"]
    rn = vu["reserva_nacional"]
    terc_pesq = sum(
        tc["media_validos"][k]
        for k in ("cury", "renan_santos", "caiado", "zema", "demais")
    )
    return {
        "vu_pesq": pct(terc_pesq),
        "vu_urna": pct(pub["urna_validos"]),
        "vu_renan": sinal(-tc["queda_pp"]["renan_santos"]),
        "vu_caiado": sinal(-tc["queda_pp"]["caiado"]),
        "vu_cury": sinal(-tc["queda_pp"]["cury"]),
        "vu_zema": sinal(-tc["queda_pp"]["zema"]),
        "vu_f_ganho": sinal(rn["ganho_medio_validos_flavio_pp"]),
        "vu_l_ganho": sinal(rn["ganho_medio_validos_lula_pp"]),
        "vu_explica": pct(
            100 * dec["nexus_renormalizada"]["fracao_explicada_diferenca"], 0
        ),
        "vu_explica_pp": num(dec["nexus_renormalizada"]["explicado_diferenca_pp"], 2),
        "vu_faixa_min": pct(
            100 * dec["nexus_com_vazamento"]["fracao_explicada_diferenca"], 0
        ),
        "vu_faixa_max": pct(
            100 * dec["datafolha_caiado"]["fracao_explicada_diferenca"], 0
        ),
        "vu_reserva_f": pct(100 * rn["lambda_flavio"]["mediana"], 0),
        "vu_reserva_l": pct(100 * rn["theta_lula"]["mediana"], 0),
        "vu_urna_cury": pct(urna["cury"]),
        "vu_urna_renan": pct(urna["renan_santos"]),
    }
