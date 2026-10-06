"""Valores formatados da super thread, segunda metade: seções, urna, fechamento,
lentidão, fontes e o 2º turno."""

from __future__ import annotations

from .secoes_clusters_leitura import extenso
from .thread_base import (
    ROOT,
    dado,
    hora,
    mi,
    nome_proprio,
    num,
    pct,
    sinal,
    tabela,
)

NOME_NUMERO = {
    "n70": "Cury",
    "n14": "Renan",
    "n55": "Caiado",
    "n30": "Zema",
    "n80": "Samara",
    "n16": "Hertz Dias",
    "n27": "Clariana",
    "n21": "Edmilson",
    "n35": "Grassi",
    "n29": "Rui Pimenta",
}


def v_anomalias() -> dict:
    a = dado("anomalias")
    res = a["resumo"]
    topo = a["topo"][:50]
    hip = [
        x
        for x in topo
        if any("efeito político local" in e for e in x["explicacao_provavel"])
    ]
    rob = a["robustez"]["semente_1"]
    td = res["tardias"]
    qn = next(x for x in topo if x["municipio"] == "QUEIMADA NOVA")
    tib = next(x for x in topo if x["municipio"] == "TIBAU")
    gg = next(x for x in topo if x["municipio"] == "GUARANI DE GOIÁS")
    col = next(x for x in topo if x["municipio"] == "COLINA")
    return {
        "an_zonas": num(res["n_zonas"]),
        "an_topo": num(len(topo)),
        "an_hip": num(len(hip)),
        "an_comum": num(len(topo) - len(hip)),
        "an_rob": num(rob["comuns_topo"]),
        "an_rob_n": num(rob["n_topo"]),
        "an_tard_n": num(td["n"]),
        "an_tard_swing": sinal(td["margem_swing_pp_tardias"]),
        "an_dem_swing": sinal(td["margem_swing_pp_demais"]),
        "an_tard_uf": sinal(td["swing_uf_pp_tardias"]),
        "an_tard_res": sinal(td["residuo_medio_pp_tardias"]),
        "an_dem_res": sinal(td["residuo_medio_pp_demais"]),
        "an_qn_bn": pct(qn["brancos_nulos_pct"], 1),
        "an_tib_eleit": pct(tib["var_eleitorado_pct"], 1),
        "an_gg_caiado": pct(gg["terceiro_lider"]["pct"], 1),
        "an_col_cury": pct(col["terceiro_lider"]["pct"], 1),
    }


def v_secoes() -> dict:
    s = dado("secoes")
    e = s["extremos"]
    res = {(x["candidato"], x["limiar"]): x for x in e["resumo"]}
    c22 = e["comparacao_2022"]["lula"]
    ex = e["excesso"]["lula"]
    tipo = {x["tipo"]: x for x in e["tipo_local"]["linhas"]}
    ald = tipo["aldeia ou terra indígena"]
    rural = tipo["zona rural"]
    return {
        "s90_l": num(res[("lula", 90)]["secoes"]),
        "s90_l_aptos": num(res[("lula", 90)]["aptos"]),
        "s90_l_pct": pct(res[("lula", 90)]["pct_das_secoes"]),
        "s90_f": num(res[("flavio", 90)]["secoes"]),
        "s100_l": num(res[("lula", 100)]["secoes"]),
        "s100_f": num(res[("flavio", 100)]["secoes"]),
        "s_base": num(s["cobertura"]["secoes_validas"]),
        "s_casadas": num(c22["secoes_90_2026_casadas"]),
        "s_ja90": num(c22["tambem_90_em_2022_1t"]),
        "s_ja80": num(c22["acima_80_em_2022_1t"]),
        "s_med22": pct(c22["pct_2022_1t_mediana"], 1),
        "s_zona_med": pct(ex["zona_pct_mediana"], 1),
        "s_excesso": num(ex["excesso_zona_pp_mediana"], 1),
        "s_ald_90": num(ald["lula_90"]),
        "s_ald_todas": num(ald["todas"]),
        "s_ald_pct": pct(ald["lula_90_pct_do_tipo"], 1),
        "s_rural_90": num(rural["lula_90"]),
        "s_secoes_cad": num(s["cobertura"]["secoes_cs"]),
    }


def _perfil_curto(rotulo: str, limite: int = 26) -> str:
    """As duas primeiras marcas do rótulo, ou só a primeira se não couber."""
    perfil = rotulo.split("; ")[0].split(", ")
    dois = ", ".join(perfil[:2])
    return dois if len(dois) <= limite else perfil[0]


def _ganho(e: dict, k: str) -> float:
    return (e[k]["zona_mais_grupo"] or 0.0) - (e[k]["zona"] or 0.0)


def v_clusters() -> dict:
    c = dado("secoes")["clusters"]
    comp = c["componentes"]
    q = c["variantes"]["quinze_partes"]
    c5 = c["variantes"]["cinco_partes_clr"]
    dg = c["ajuste"]["diagnostico_convergencia"]
    e = c["explicacao_variancia"]
    med = c5["mediana_votos_por_secao"]
    art5 = [g for g in c5["grupos"] if g.get("artefato")]
    anom = comp[c["mais_anomalo"]["id"]]
    zz = next((u for u in anom["ufs_top"] if u["uf"] == "ZZ"), None)
    grupos = []
    for g in comp:
        reg = (g.get("regioes") or [{}])[0]
        grupos.append(
            f"{_perfil_curto(g['rotulo'])}, com {num(g['secoes'])} seções e "
            f"{pct(reg.get('pct_do_cluster') or 0, 0)} delas no {reg.get('regiao', '')}"
        )
    return {
        "cl_k": str(c["k"]),
        "cl_k_ext": extenso(c["k"]),
        "cl_n15": str(len(q["features"])),
        "cl_zeros15": pct(q["zeros_substituidos_pct"], 1),
        "cl_v15": num(q["cramer_v_regiao"], 2),
        "cl_med_brancos": num(med["brancos"]),
        "cl_med_nulos": num(med["nulos"]),
        "cl_v5": num(c5["cramer_v_regiao"], 2),
        "cl_art5_n": extenso(len(art5)).capitalize(),
        "cl_v": num(c["cramer_v_regiao"], 2),
        "cl_vuf": num(c["cramer_v_uf"], 2),
        "cl_grupos": "; ".join(grupos),
        "cl_partidas": str(dg["total"]),
        "cl_nomax": str(dg["no_maximo"]),
        "cl_amostra": num((dg.get("amostra") or 0) / 1000) + " mil",
        "cl_anom": str(anom["id"] + 1),
        "cl_anom_abst": pct(anom["centro_pct_eleitorado"]["abstencao"], 0),
        "cl_anom_secoes": num(anom["secoes"]),
        "cl_anom_zz": pct(zz["pct_do_cluster"], 0) if zz else pct(0, 0),
        "cl_ganho_lula": num(_ganho(e, "lula")),
        "cl_ganho_flavio": num(_ganho(e, "flavio")),
        "cl_ganho_brancos": num(_ganho(e, "brancos")),
        "cl_ganho_nulos": num(_ganho(e, "nulos")),
        "cl_r2_zona_lula": pct(e["lula"]["zona"], 0),
    }


def v_urna() -> dict:
    rg = {x["estimador"]: x for x in dado("secoes")["urna"]["reguas"]["itens"]}
    out = {"urna_max": num(dado("secoes")["urna"]["reguas"]["max_abs_pp"], 2)}
    for k, chave in (
        ("dentro_zona", "uz"),
        ("dentro_local", "ul"),
        ("dentro_zona_variacao", "uv"),
        ("troca_2022_2026", "ut"),
    ):
        x = rg[k]
        out[f"{chave}_est"] = sinal(x["estimativa"])
        out[f"{chave}_lo"] = sinal(x["ic95"][0])
        out[f"{chave}_hi"] = sinal(x["ic95"][1])
        out[f"{chave}_n"] = num(x["unidades"])
        out[f"{chave}_bruto"] = sinal(x["bruto"])
    return out


def v_fechamento() -> dict:
    f = dado("fechamento")
    lh = f["lula_hora"]
    bruta = [
        x for x in lh["bruta"] if x["grupo"] == "Brasil" and x["lula_pct"] is not None
    ]
    inc = {x["id"]: x["lula"]["coeficientes"]["horas_atraso"] for x in lh["inclinacao"]}
    est = {x["id"]: x["resultado"]["lula_pp"] for x in f["voto"]["estimadores"]}
    tam = {
        x["faixa"]: x["encerramento_2026"]["depois_1800_pct"]
        for x in f["tamanho"]["linhas"]
    }
    loc = f["persistencia"]["locais"]
    rural = next(t for t in loc["por_tipo"] if t["tipo"].startswith("zona rural"))
    dec = f["persistencia"]["decil"]
    v = {
        "fe_bruta_ini": pct(bruta[0]["lula_pct"], 1),
        "fe_bruta_fim": pct(bruta[-1]["lula_pct"], 1),
        "fe_inc_bruta": sinal(inc["bruta"]["estimativa"]),
        "fe_inc_zona": sinal(inc["zona"]["estimativa"]),
        "fe_inc_ctrl": sinal(inc["zona_controles"]["estimativa"]),
        "fe_inc_ctrl_lo": sinal(inc["zona_controles"]["ic95"][0]),
        "fe_inc_ctrl_hi": sinal(inc["zona_controles"]["ic95"][1]),
        "fe_sobra": pct(lh["sobrevive_pct"]["lula_inclinacao"], 1),
        "fe_dec26": sinal(est["recebimento_decil_2026"]["estimativa"], 1),
        "fe_dec22": sinal(est["recebimento_decil_2022"]["estimativa"], 1),
        "fe_tam_grande": pct(tam["400 ou mais"], 1),
        "fe_tam_pequena": pct(tam["até 199"], 1),
        "fe_locais": num(loc["persistentes"]),
        "fe_locais_secoes": num(loc["secoes_2026_nos_persistentes"]),
        "fe_locais_rural": pct(rural["pct_dos_persistentes"], 1),
        "fe_locais_rural_base": pct(rural["pct_dos_locais"], 1),
        "fe_mun_persist": num(dec["persistentes"]),
        "fe_mun_razao": num(dec["razao"], 1),
    }
    for i, x in enumerate(bruta):
        v[f"fe_b{i}"] = pct(x["lula_pct"], 1)
    return v


def v_lentidao() -> dict:
    lt = dado("lentidao_ufs")
    n = lt["nacional"]
    r99 = lt["resumo_99"]
    b = dado("fechamento")["distribuicao"]["brasil"]
    v = {
        "le_99_26": n["horas_2026"]["99"],
        "le_99_22": n["horas_2022"]["99"],
        "le_50_26": n["horas_2026"]["50"],
        "le_50_22": n["horas_2022"]["50"],
        "le_90_26": n["horas_2026"]["90"],
        "le_90_22": n["horas_2022"]["90"],
        "le_rapidas": str(r99["mais_rapidas_em_2026"]),
        "le_ufs": str(len(lt["ufs"])),
        "le_spearman": num(r99["spearman_ufs"], 2),
        "le_lentas": ", ".join(r99["classificacao"]["lentas_nos_dois"]),
        "le_n_lentas": str(len(r99["classificacao"]["lentas_nos_dois"])),
        "le_mediana_26": num(r99["mediana_2026"], 0),
        "le_mediana_22": num(r99["mediana_2022"], 0),
    }
    v["le_rec26"] = relogio(b["recebimento_2026"]["mediana"])
    v["le_rec22"] = relogio(b["recebimento_2022"]["mediana"])
    v["le_rec26_19"] = pct(b["recebimento_2026"]["depois_1900_pct"], 1)
    v["le_rec22_19"] = pct(b["recebimento_2022"]["depois_1900_pct"], 1)
    return v


def relogio(minutos_depois_das_17: float) -> str:
    total = 17 * 60 + round(minutos_depois_das_17)
    return f"{total // 60 % 24:02d}:{total % 60:02d}"


def v_fontes() -> dict:
    p = dado("pesquisas_vs_urna")
    arq = dado("arquitetura")
    s = dado("secoes")
    lt = dado("linha_do_tempo")
    versoes = tabela(lt["nacional"]["versoes"])
    return {
        "fo_sha": p["urna"]["versao_nacional"]["sha256"][:16],
        "fo_versoes": num(arq["publicacao_2026"]["versoes_total_banco"]),
        "fo_nacional": num(len(versoes)),
        "fo_boletins": num(s["cobertura"]["secoes_com_bu"]),
        "fo_cadastro": num(s["cobertura"]["secoes_cs"]),
        "fo_zona_div": num(
            next(
                x
                for x in s["cobertura"]["excluidas"]
                if x["codigo"] == "zona_divergente"
            )["secoes"]
        ),
        "fo_sem_bu": num(
            next(x for x in s["cobertura"]["excluidas"] if x["codigo"] == "sem_bu")[
                "secoes"
            ]
        ),
        "fo_contexto": num(len(dado("contexto_seguranca")["itens"])),
    }


def v_segundo_turno() -> dict:
    e = dado("estrategia_2t")
    ar = e["aritmetica"]
    eq = ar["equilibrio"]
    proj = {(p["matriz"], p["hipotese"]): p for p in ar["projecoes"]}
    nx = proj[("nexus", "fica_fora")]
    det = {d["origem"]: d for d in nx["detalhe"]}
    renan = det["RENAN SANTOS"]
    caiado = det["RONALDO CAIADO"]
    margens = [p["margem_votos"] for p in ar["projecoes"]]
    est = e["geografia"]["estoque"]
    lula_maior = e["riscos"]["estoque_lula_maior"]
    an = ar["analogo_2022"]["nacional"]
    linhas = ar["matrizes"]["nexus"]["linhas_publicadas"]
    dfl = ar["matrizes"]["datafolha"]["linhas_publicadas"]
    return {
        "eq_lula_todos": pct(eq["lula_precisa_se_todos_votarem_pct"]),
        "eq_lula_escolhe": pct(eq["lula_precisa_entre_quem_escolhe_pct"]),
        "eq_lula_medido": pct(eq["lula_medido_entre_quem_escolhe_pct"]),
        "eq_escolhe": pct(eq["terceiros_que_escolhem_nexus_pct"]),
        "eq_nao_escolha": mi(
            eq["nao_escolha_toda_para_lula"]["nexus"]["nao_escolha_votos"]
        ),
        "eq_sobra": mi(
            eq["nao_escolha_toda_para_lula"]["nexus"]["margem_flavio_se_toda_for_lula"],
            0,
        ),
        "eq_sobra_df": mi(
            eq["nao_escolha_toda_para_lula"]["datafolha"][
                "margem_flavio_se_toda_for_lula"
            ]
        ),
        "eq_base_troca": pct(eq["base_flavio_trocando_para_lula_pct"]),
        "eq_base_abst": pct(eq["base_flavio_abstendo_pct"]),
        "nx_f": pct(nx["flavio_pct"]),
        "nx_l": pct(nx["lula_pct"]),
        "nx_margem": mi(nx["margem_votos"]),
        "df_prop_f": pct(proj[("datafolha", "proporcional")]["flavio_pct"]),
        "margem_min": mi(min(margens)),
        "margem_max": mi(max(margens)),
        "renan_saldo": mi(renan["saldo_flavio"]),
        "caiado_saldo": mi(caiado["saldo_flavio"]),
        "estoque_f": mi(est["total_ufs"]),
        "estoque_l": mi(lula_maior["estoque_lula"]),
        "estoque_razao": num(lula_maior["razao"], 2),
        "an22_f": pct(an["flavio_pct"]),
        "abst_1t": mi(eq["abstencao_1t"]),
        "nx_cury_f": str(linhas["Cury"]["Flávio"]),
        "nx_cury_l": str(linhas["Cury"]["Lula"]),
        "nx_renan_f": str(linhas["Renan"]["Flávio"]),
        "nx_renan_l": str(linhas["Renan"]["Lula"]),
        "nx_caiado_f": str(linhas["Caiado"]["Flávio"]),
        "nx_caiado_l": str(linhas["Caiado"]["Lula"]),
        "nx_zema_f": str(linhas["Zema"]["Flávio"]),
        "nx_zema_l": str(linhas["Zema"]["Lula"]),
        "df_cury_f": num(dfl["Cury"]["Flávio"]),
        "df_cury_l": num(dfl["Cury"]["Lula"]),
        "df_caiado_f": num(dfl["Caiado"]["Flávio"]),
        "df_caiado_l": num(dfl["Caiado"]["Lula"]),
    }


def v_reguas() -> dict:
    t = dado("terceira_via")
    tot = t["reguas"]["totais"]["brasil"]
    rk = t["reguas"]["rankings"]
    cl = t["reguas"]["modelos"]["classe"]["grupos"]
    return {
        "rg_nexus": mi(tot["nexus"]),
        "rg_df": mi(tot["datafolha"]),
        "rg_urna": mi(tot["urna"]),
        "rg_urna_lo": mi(tot["urna_ic95"][0]),
        "rg_urna_hi": mi(tot["urna_ic95"][1]),
        "rg_pv_nexus": num(tot["pv_nexus"], 2),
        "rg_pv_urna": num(tot["pv_urna"], 2),
        "rg_robustos": str(rk["robustos"]),
        "rg_top": str(len(rk["top"]["pesquisa"])),
        "rg_robustos_estoque": mi(rk["robustos_estoque"]),
        "rg_folga_f": sinal(cl["venceu_folga"]["saldo"], 2),
        "rg_folga_l": sinal(cl["perdeu_folga"]["saldo"], 2),
        "rg_folga_l_lo": sinal(cl["perdeu_folga"]["saldo_ic95"][0], 2),
        "rg_folga_l_hi": sinal(cl["perdeu_folga"]["saldo_ic95"][1], 2),
        "rg_folga_f_lo": sinal(cl["venceu_folga"]["saldo_ic95"][0], 2),
        "rg_folga_f_hi": sinal(cl["venceu_folga"]["saldo_ic95"][1], 2),
    }


def v_militancia() -> dict:
    t = dado("terceira_via")
    ag = t["agregados"]
    br = ag["brasil"]
    ne = ag["regioes"]["Nordeste"]
    teto = sum(v["teto"] for v in t["teto"]["ufs"].values())
    comb = t["reguas"]["rankings"]["top"]["combinacao"][:10]
    risco = t["nulo_2022"]["risco_2026"]
    com, sem = t["nulo_2022"]["com_2t_governador"], t["nulo_2022"]["sem_2t_governador"]
    rj = next(u for u in dado("presidente")["ufs"] if u["uf"] == "RJ")
    top = t["prioridade"]["soma_top"]
    v = {
        "mil_teto": mi(teto),
        "mil_estoque": mi(br["estoque"]),
        "mil_vao": mi(br["vao_positivo"]),
        "mil_vao_sem": mi(br["vao_positivo_sem_governador_sem_apoio"]),
        "mil_vao_ne": mi(ne["vao_positivo"]),
        "mil_vao_ne_pct": pct(100 * ne["vao_positivo"] / br["vao_positivo"], 1),
        "mil_ne_onde_venceu": pct(ne["onde_flavio_venceu_parcela"], 1),
        "mil_risco": mi(risco["votos"], 0),
        "mil_risco_ufs": ", ".join(risco["ufs"]),
        "mil_risco_n": str(len(risco["ufs"])),
        "mil_risco_comp": mi(risco["comparecimento"]),
        "mil_rj_parcela": pct(100 * rj["comparecimento"] / risco["comparecimento"], 1),
        "mil_com_delta": sinal(com["delta_pp"], 2),
        "mil_sem_delta": sinal(sem["delta_pp"], 2),
        "mil_top_estoque": mi(top["estoque"]),
        "mil_top_saldo": mi(top["saldo"], 0),
        "mil_top_fora": mi(top["fora"]),
        "mil_comb_lista": ", ".join(nome_proprio(x["nome"]) for x in comb),
        "mil_comb1": nome_proprio(comb[0]["nome"]),
        "mil_comb1_piso": num(comb[0]["piso"]),
        "mil_comb1_teto": num(comb[0]["teto"]),
    }
    return v


def citacoes() -> dict:
    """Trechos de fala com fonte arquivada; sem fonte, a chave não existe."""
    caminho = ROOT / "analysis/apuracao_2026/fontes_thread.json"
    if not caminho.exists():
        return {}
    import json

    itens = json.loads(caminho.read_text(encoding="utf-8"))["itens"]
    out = {}
    for x in itens:
        if x.get("encontrada") and x.get("lida_no") == "pagina":
            out[x["id"]] = x
    return out


__all__ = [
    "NOME_NUMERO",
    "citacoes",
    "hora",
    "v_anomalias",
    "v_clusters",
    "v_fechamento",
    "v_fontes",
    "v_lentidao",
    "v_militancia",
    "v_reguas",
    "v_secoes",
    "v_segundo_turno",
    "v_urna",
]


def v_extras() -> dict:
    """Complementos usados em mais de um post."""
    p = dado("presidente")
    n = p["nacional"]
    ufs = [u for u in p["ufs"] if u["uf"] != "ZZ"]
    reg = p["regioes"]
    total_ganho = n["comparacao"]["flavio_vs_bolsonaro_1t"]["votos"]
    gov = {
        (x["uf"], x["governador"]): x
        for x in dado("governadores")["vao_estadual"]["lista"]
    }
    cadu = next(
        x for (uf, nome), x in gov.items() if uf == "rn" and nome.startswith("CADU")
    )
    pq = dado("pesquisas_vs_urna")
    ondas = {o["id"]: o for o in pq["pesquisas"]}
    ult = set(pq["medias"]["ultimas_ondas_publicado"]["ondas"])
    rank = [i for i in pq["ranking_publicado"] if i in ult]
    prox = [ondas[i] for i in rank[:2]]
    mov = {m["id"]: m for m in dado("estrategia_2t")["movimentos"]}
    outras = dado("secoes")["outras"]["comparecimento"]
    zero = dado("secoes")["outras"]["zero_votos"]
    v = {
        "n_ufs": str(len(ufs)),
        "ne_ganho_pct": pct(
            100
            * reg["Nordeste"]["comparacao"]["flavio_vs_bolsonaro_1t"]["votos"]
            / total_ganho,
            1,
        ),
        "f_vs_b2t": sinal(n["comparacao"]["flavio_vs_bolsonaro_2t"]["pp"]),
        "cadu": sinal(cadu["vao_pp"], 1),
        "prox1": prox[0]["instituto"],
        "prox2": prox[1]["instituto"],
        "prox_erro": sinal(prox[0]["publicado"]["diferenca_lula_menos_flavio"]["erro"]),
        "mov_tarcisio": mi(mov["sp_tarcisio"]["votos_esperados"], 0),
        "mov_cleitinho": mi(mov["mg_cleitinho"]["votos_esperados"], 0),
        "mov_ruas": mi(mov["rj_ruas"]["votos_esperados"], 0),
        "mov_renan": mi(mov["renan"]["votos_esperados"]),
        "mov_cury": mi(mov["cury"]["votos_esperados"], 0),
        "comp_acima_100": num(outras["acima_100"]),
        "comp_igual_100": num(outras["igual_100"]),
    }
    v["zero_min_votantes"] = num(zero["minimo_votantes"])
    v["zero_lula"] = num(zero["lula"]["secoes"])
    v["zero_flavio"] = num(zero["flavio"]["secoes"])
    v["zero_flavio_am"] = num(
        next((x["secoes"] for x in zero["flavio"]["por_uf"] if x["uf"] == "AM"), 0)
    )
    return v


def _limiar_da_chave(chave: str) -> str:
    """'depois_1800_pct' vira '18h'; 'acima_80_em_2022_1t' vira '80%'."""
    import re

    m = re.search(r"depois_(\d{2})(\d{2})", chave)
    if m:
        return f"{int(m.group(1))}h"
    m = re.search(r"acima_(\d+)_", chave)
    if m:
        return f"{m.group(1)}%"
    raise ValueError(chave)


def v_mais() -> dict:
    """Limiares de definição, lidos das chaves e listas dos próprios JSONs, e
    complementos dos posts."""
    p = dado("presidente")
    reg = p["regioes"]
    zz = next(u for u in p["ufs"] if u["uf"] == "ZZ")
    ext = dado("exterior")
    cont = {c["continente"]: c for c in ext["continentes"]}
    s = dado("secoes")
    ex = s["extremos"]
    lim = ex["limiares"]
    res = {(x["candidato"], x["limiar"]): x for x in ex["resumo"]}
    fl22 = ex["comparacao_2022"]["flavio"]
    f = dado("fechamento")
    faixas = [x["rotulo"] for x in f["lula_hora"]["faixas"] if x["min_min"] is not None]
    tam = f["tamanho"]["linhas"][0]["encerramento_2026"]
    chave18 = next(k for k in tam if k.startswith("depois_18"))
    chave19 = next(k for k in tam if k.startswith("depois_19"))
    ufs_f = sorted(
        (u for u in f["distribuicao"]["ufs"] if u["nivel"] == "uf"),
        key=lambda u: -u["encerramento_2026"]["depois_1800_pct"],
    )
    lt = dado("lentidao_ufs")["nacional"]
    marcos = list(lt["horas_2026"])
    camara = dado("camara")["por_partido"]
    a = {c["uf"]: c for c in dado("assembleias")["casas"]}
    gov = {
        (x["uf"], x["governador"].split()[0]): x
        for x in dado("governadores")["vao_estadual"]["lista"]
    }
    pq = dado("pesquisas_vs_urna")["resumo_ultimas_ondas"]
    modo = pq["por_modo_publicado"]
    tc = dado("voto_util")["terceiros_por_candidato"]["publicado"]
    sen = dado("senado")
    pl_ufs = {}
    for x in sen["eleitos_2026"]:
        if x["partido"] == "PL":
            pl_ufs[x["uf"]] = pl_ufs.get(x["uf"], 0) + 1
    dobradinhas = sorted(u for u, k in pl_ufs.items() if k >= 2)
    apertadas = sorted(sen["disputas"], key=lambda d: d["margem_2a_vaga_pp"])[:2]
    an = dado("anomalias")["resumo"]
    v = {
        "lim90": f"{lim[0]}%",
        "lim95": f"{lim[1]}%",
        "lim100": f"{lim[2]}%",
        "lim80": _limiar_da_chave("acima_80_em_2022_1t"),
        "h18": _limiar_da_chave(chave18),
        "h19": _limiar_da_chave(chave19),
        "fe_f0": faixas[0],
        "fe_ini": faixas[0].split(" ")[0],
        "fe_f1": faixas[1],
        "fe_f2": faixas[2],
        "fe_f3": faixas[3],
        "m50": f"{marcos[0]}%",
        "m90": f"{marcos[1]}%",
        "m99": f"{marcos[2]}%",
        "le_100_26": lt["horas_2026"]["100"],
        "le_100_22": lt["horas_2022"]["100"],
        "comp_ne": sinal(reg["Nordeste"]["comparacao"]["comparecimento_vs_1t_pp"]),
        "comp_no": sinal(reg["Norte"]["comparacao"]["comparecimento_vs_1t_pp"]),
        "comp_cs": sinal(reg["Centro-Sul"]["comparacao"]["comparecimento_vs_1t_pp"]),
        "comp_faixa": sinal(p["por_faixa_lula_2022"][-1]["delta_comparecimento_pp"]),
        "comp_faixa_rot": p["por_faixa_lula_2022"][-1]["faixa_lula_2022_pct"].replace(
            " a ", " a "
        )
        + "%",
        "ext_b2t": pct(zz["r2022"]["t2"]["pct"]["bolsonaro"]),
        "asia_f": pct(cont["Ásia"]["pct"]["flavio"]),
        "cam_uniao": num(camara["UNIÃO"]),
        "cam_psd": num(camara["PSD"]),
        "cam_rep": num(camara["REPUBLICANOS"]),
        "cam_pp": num(camara["PP"]),
        "cam_mdb": num(camara["MDB"]),
        "sen_dobradinhas": ", ".join(dobradinhas),
        "sen_n_dobradinhas": str(len(dobradinhas)),
        "sen_apertada_uf": apertadas[0]["uf"],
        "sen_apertada_pp": num(apertadas[0]["margem_2a_vaga_pp"], 2),
        "sen_apertada_votos": num(apertadas[0]["margem_2a_vaga_votos"]),
        "sen_apertada2_uf": apertadas[1]["uf"],
        "sen_apertada2_pp": num(apertadas[1]["margem_2a_vaga_pp"], 2),
        "mg_top_nome": nome_proprio(a["MG"]["mais_votados"][0]["nome"]),
        "mg_top_votos": num(a["MG"]["mais_votados"][0]["votos"]),
        "mg_top_partido": a["MG"]["mais_votados"][0]["partido"],
        "pres_media": sinal(modo["presencial"]["media"]),
        "tel_media": sinal(modo["telefone"]["media"]),
        "onl_media": sinal(modo["online"]["media"]),
        "pres_n": str(modo["presencial"]["n"]),
        "tel_n": str(modo["telefone"]["n"]),
        "onl_n": str(modo["online"]["n"]),
        "corr_casa": num(pq["correlacao_efeito_casa_pre_eleicao_com_erro"], 2),
        "rel_zema": pct(100 * tc["queda_relativa"]["zema"], 0),
        "rel_renan": pct(100 * tc["queda_relativa"]["renan_santos"], 0),
        "rel_caiado": pct(100 * tc["queda_relativa"]["caiado"], 0),
        "rel_cury": pct(100 * tc["queda_relativa"]["cury"], 0),
        "fat_renan": pct(100 * tc["fatia_da_queda"]["renan_santos"], 0),
        "fat_caiado": pct(100 * tc["fatia_da_queda"]["caiado"], 0),
        "s95_l": num(res[("lula", lim[1])]["secoes"]),
        "s95_f": num(res[("flavio", lim[1])]["secoes"]),
        "f90_casadas": num(fl22["secoes_90_2026_casadas"]),
        "f90_ja": num(fl22["tambem_90_em_2022_1t"]),
        "f90_med22": pct(fl22["pct_2022_1t_mediana"], 1),
        "f90_var": sinal(fl22["variacao_pp_mediana"], 1),
        "an_locais": num(an["referencia_2022"]["locais"]),
        "an_incompletas": num(an["zonas_incompletas"]),
        "fe_uf1": ufs_f[0]["chave"],
        "fe_uf1_pct": pct(ufs_f[0]["encerramento_2026"]["depois_1800_pct"], 1),
        "fe_uf2": ufs_f[1]["chave"],
        "fe_uf2_pct": pct(ufs_f[1]["encerramento_2026"]["depois_1800_pct"], 1),
        "fe_uf3": ufs_f[2]["chave"],
        "fe_uf3_pct": pct(ufs_f[2]["encerramento_2026"]["depois_1800_pct"], 1),
        "fe_ufz": ufs_f[-1]["chave"],
        "fe_ufz_pct": pct(ufs_f[-1]["encerramento_2026"]["depois_1800_pct"], 1),
    }
    for chave, (uf, nome) in {
        "rj_ruas": ("rj", "DOUGLAS"),
        "rj_paes": ("rj", "EDUARDO"),
        "df_celina": ("df", "CELINA"),
        "pr_moro": ("pr", "SERGIO"),
        "es_pazolini": ("es", "LORENZO"),
        "to_dorinha": ("to", "PROFESSORA"),
    }.items():
        v[chave] = pct(gov[(uf, nome)]["pct_governador"])
    for uf in ("RJ", "PR", "SC", "GO", "DF", "RS", "PE"):
        c = a[uf]
        v[f"{uf.lower()}_bloco_d"] = num(c["blocos"]["direita + centro-direita"])
        v[f"{uf.lower()}_vagas"] = num(c["vagas"])
        v[f"{uf.lower()}_centro"] = num(c["por_campo"]["centro"])
    return v


def v_mais_b() -> dict:
    p = dado("presidente")
    n = p["nacional"]
    ne = p["regioes"]["Nordeste"]["r2026"]
    ext = dado("exterior")["total"]
    s = dado("secoes")
    por_uf = [
        x
        for x in s["extremos"]["por_uf"]
        if x["candidato"] == "lula" and x["limiar"] == s["extremos"]["limiares"][0]
    ]
    topo_uf = max(por_uf, key=lambda x: x["pct_das_secoes_uf"])
    a22 = s["urna"]["ano_2022"]
    mods = a22["modelos"]
    par = next(
        x
        for x in a22["dentro_zona"]["pares"]
        if x["a"] == mods[-2] and x["b"] == mods[-1]
    )
    df = next(u for u in dado("lentidao_ufs")["ufs"] if u["uf"] == "DF")
    return {
        "lula_ne_parcela": pct(100 * ne["votos"]["lula"] / n["votos"]["lula"], 1),
        "flavio_ne_parcela": pct(100 * ne["votos"]["flavio"] / n["votos"]["flavio"], 1),
        "ne_validos_parcela": pct(100 * ne["validos"] / n["validos"], 1),
        "ext_ausentes": num(ext["eleitores"] - ext["comparecimento"]),
        "uf90": topo_uf["uf"],
        "uf90_n": num(topo_uf["secoes"]),
        "uf90_pct": pct(topo_uf["pct_das_secoes_uf"], 2),
        "u22_est": sinal(par["bolsonaro_pp"]["estimativa"]),
        "u22_lo": sinal(par["bolsonaro_pp"]["ic95"][0]),
        "u22_hi": sinal(par["bolsonaro_pp"]["ic95"][1]),
        "u22_n": num(par["unidades"]),
        "df_100_26": df["horas"]["2026_totalizado"]["100"],
        "df_100_22": df["horas"]["2022_totalizado"]["100"],
    }
