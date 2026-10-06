"""`resumo.md`: os 15 achados mais fortes, cada número lido dos conjuntos gerados.

Nenhum número é digitado aqui: todos saem dos dicionários que viram os JSON de
`analysis/apuracao_2026/dados/`, e cada achado cita arquivo e campo.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from .dados import pct


def n(x: float | None) -> str:
    """Inteiro com ponto de milhar."""
    if x is None:
        return "s/d"
    return f"{round(x):,}".replace(",", ".")


def _decimal(x: float, casas: int) -> Decimal:
    return Decimal(str(x)).quantize(Decimal(1).scaleb(-casas), rounding=ROUND_HALF_UP)


def p(x: float | None, casas: int = 2) -> str:
    """Número com vírgula decimal, arredondado meio para cima."""
    if x is None:
        return "s/d"
    return f"{_decimal(x, casas):.{casas}f}".replace(".", ",")


def s(x: float | None, casas: int = 2) -> str:
    """Número com sinal explícito (menos tipográfico) e vírgula decimal."""
    if x is None:
        return "s/d"
    texto = f"{_decimal(x, casas):+.{casas}f}".replace(".", ",")
    return texto.replace("-", "\u2212")


def secoes(k: int) -> str:
    return f"{n(k)} seção" if k == 1 else f"{n(k)} seções"


PARTICULAS = {"da", "das", "de", "do", "dos", "e"}


def nome_proprio(texto: str) -> str:
    """Caixa de nome próprio em português, com partículas em minúscula."""
    palavras = texto.lower().split()
    return " ".join(
        w if i > 0 and w in PARTICULAS else w[:1].upper() + w[1:]
        for i, w in enumerate(palavras)
    )


def sv(x: int | None) -> str:
    """Votos com sinal explícito."""
    if x is None:
        return "s/d"
    return ("+" if x >= 0 else "−") + n(abs(x))


def mi(x: float) -> str:
    return p(x / 1e6, 2) + " mi"


def hm(brt: str | None) -> str:
    """Hora `HH:MM:SS` de um carimbo `AAAA-MM-DD HH:MM:SS`."""
    return brt[11:] if brt else "s/d"


def _linhas(tabela: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        dict(zip(tabela["colunas"], linha, strict=True)) for linha in tabela["linhas"]
    ]


def _uf(ufs: list[dict[str, Any]], sigla: str) -> dict[str, Any]:
    return next(u for u in ufs if u["uf"] == sigla)


def escrever(produtos: dict[str, dict[str, Any]], meta: dict[str, Any]) -> str:
    pres = produtos["presidente.json"]
    linha = produtos["linha_do_tempo.json"]
    ext = produtos["exterior.json"]
    cam = produtos["camara.json"]
    sen = produtos["senado.json"]
    nac = pres["nacional"]
    comp = nac["comparacao"]
    ufs = [u for u in pres["ufs"] if u["uf"] != "ZZ"]
    reg = pres["regioes"]
    mun = [m for m in _linhas(pres["municipios"]) if m["completo"]]
    mun22 = [m for m in mun if m["swing_flavio_pp"] is not None]
    versoes = _linhas(linha["nacional"]["versoes"])
    com_secoes = [v for v in versoes if (v["st"] or 0) > 0]
    faixas = pres["por_faixa_lula_2022"]
    conf = pres["conferencia"]
    trav = linha["travamentos"]
    div = linha["divergencia_soma_ufs"]
    idg = linha["idg_regressivo"]
    tardias = linha["secoes_tardias"]
    zz = _uf(pres["ufs"], "ZZ")
    o: list[str] = []
    add = o.append

    add("# Apuração do 1º turno de 2026: os 15 achados mais fortes dos dados")
    add("")
    add(
        f"Gerado por `{meta['script']}` em {meta['gerado_em']} (UTC). Versão nacional de "
        f"presidente: snapshot {meta['versao_nacional_snapshot_id']}, gerada pelo TSE às "
        f"{nac['gerado_em_brt']} (Brasília). Boletim `final.json` de {meta['final_json_gerado_em']}. "
        "Cada número sai de um arquivo em `analysis/apuracao_2026/dados/`, com o campo entre "
        "parênteses. Os 15 achados são fatos verificados no banco e nos arquivos do TSE; as "
        "inferências ficam numa seção própria, rotuladas."
    )
    add("")
    add(
        "Regra de versão usada em tudo: a versão vigente de cada arquivo é a última gerada "
        "pelo TSE (`gerado_em`). A marca `regressivo` do coletor não serve para isso (achado 13)."
    )
    add("")
    add("## Fatos verificados")
    add("")

    # 1
    venceu_f = [u for u in ufs if u["votos"]["flavio"] > u["votos"]["lula"]]
    lidera = all(v["flavio"] >= v["lula"] for v in com_secoes)
    primeira = com_secoes[0]
    add(
        f"**1. Resultado final com 100% das seções.** A última versão do arquivo nacional, "
        f"gerada às {hm(nac['gerado_em_brt'])} de 05/10 com {n(nac['secoes'])} de "
        f"{n(nac['secoes_total'])} seções, dá Flávio Bolsonaro {n(nac['votos']['flavio'])} votos "
        f"({p(nac['pct']['flavio'])}% dos válidos) e Lula {n(nac['votos']['lula'])} "
        f"({p(nac['pct']['lula'])}%): diferença de {n(nac['diferenca_votos'])} votos, "
        f"{p(nac['diferenca_pp'])} ponto. Comparecimento {p(nac['pct_comparecimento'])}%, "
        f"brancos {p(nac['pct_brancos'])}% e nulos {p(nac['pct_nulos'])}% do comparecimento. "
        f"Flávio venceu em {len(venceu_f)} UFs e Lula em {len(ufs) - len(venceu_f)}. "
        + (
            f"Flávio esteve à frente em todas as {len(com_secoes)} versões novas com seções, "
            f"da primeira ({hm(primeira['gerado_brt'])}, {p(primeira['pst'])}% das seções) à "
            "última."
            if lidera
            else "Houve troca de liderança ao longo das versões."
        )
    )
    add(
        "Fonte: presidente.json (nacional.votos, nacional.pct, nacional.diferenca_votos, "
        "nacional.pct_comparecimento); linha_do_tempo.json (nacional.versoes, colunas flavio e lula)."
    )
    add("")

    # 2
    fb1, ll1 = comp["flavio_vs_bolsonaro_1t"], comp["lula_vs_lula_1t"]
    fb2 = comp["flavio_vs_bolsonaro_2t"]
    add(
        f"**2. Contra o 1º turno de 2022, a margem virou {p(comp['virada_margem_vs_1t_pp'])} "
        f"pontos.** Flávio fez {s(fb1['pp'])} pontos e {sv(fb1['votos'])} votos sobre Bolsonaro "
        f"({p(fb1['pct_b'])}% em 2022); Lula ficou {p(abs(ll1['pp']))} pontos e "
        f"{n(abs(ll1['votos']))} votos abaixo do próprio resultado de 2022 ({p(ll1['pct_b'])}%). A margem da direita foi de "
        f"{s(comp['margem_direita_2022_1t_pp'])} para {s(comp['margem_flavio_lula_2026_pp'])}. "
        f"Contra o 2º turno de 2022, Flávio ainda está {p(abs(fb2['pp']))} pontos abaixo de "
        f"Bolsonaro ({p(fb2['pct_b'])}%), que é outra disputa."
    )
    add("Fonte: presidente.json (nacional.comparacao, nacional.r2022).")
    add("")

    # 3
    sobe_f = [u for u in ufs if u["comparacao"]["flavio_vs_bolsonaro_1t"]["pp"] > 0]
    desce_f = [u for u in ufs if u["comparacao"]["flavio_vs_bolsonaro_1t"]["pp"] <= 0]
    sobe_l = [u for u in ufs if u["comparacao"]["lula_vs_lula_1t"]["pp"] > 0]
    mun_f = sum(1 for m in mun22 if m["swing_flavio_pp"] > 0)
    mun_l = sum(1 for m in mun22 if m["swing_lula_pp"] > 0)
    excecoes = "; ".join(
        f"{u['uf']} ({s(u['comparacao']['flavio_vs_bolsonaro_1t']['pp'])} ponto, "
        f"{sv(u['comparacao']['flavio_vs_bolsonaro_1t']['votos'])} votos)"
        for u in desce_f
    )
    add(
        f"**3. Flávio cresceu sobre Bolsonaro em {len(sobe_f)} de {len(ufs)} UFs e em "
        f"{n(mun_f)} de {n(len(mun22))} municípios.** A exceção estadual é {excecoes}. Lula "
        f"aumentou a própria fatia em {len(sobe_l)} UFs ("
        + ", ".join(
            f"{u['uf']} {s(u['comparacao']['lula_vs_lula_1t']['pp'])}" for u in sobe_l
        )
        + f") e em {n(mun_l)} municípios."
    )
    add(
        "Fonte: presidente.json (ufs[].comparacao.flavio_vs_bolsonaro_1t, "
        "ufs[].comparacao.lula_vs_lula_1t; municipios, colunas swing_flavio_pp e swing_lula_pp, "
        "só municípios com arquivo completo e com 2022)."
    )
    add("")

    # 4
    cs, ne, no = reg["Centro-Sul"], reg["Nordeste"], reg["Norte"]

    def contrib(r: dict[str, Any], chave: str) -> float:
        return r["contribuicao_pct_da_variacao_nacional"][chave]

    maiores_perdas = sorted(
        ufs, key=lambda u: u["comparacao"]["lula_vs_lula_1t"]["votos"]
    )[:4]
    cap_l = sorted(pres["capitais"], key=lambda c: c["delta_votos_lula"])[:2]
    add(
        f"**4. A perda de Lula é do Centro-Sul.** Dos {sv(ll1['votos'])} votos que Lula perdeu "
        f"contra 2022, {sv(cs['comparacao']['lula_vs_lula_1t']['votos'])} "
        f"({p(contrib(cs, 'lula_menos_lula_1t'), 1)}%) vieram do Centro-Sul, "
        f"{sv(ne['comparacao']['lula_vs_lula_1t']['votos'])} "
        f"({p(contrib(ne, 'lula_menos_lula_1t'), 1)}%) do Nordeste e "
        f"{sv(no['comparacao']['lula_vs_lula_1t']['votos'])} do Norte. Maiores perdas por UF: "
        + ", ".join(
            f"{u['uf']} {sv(u['comparacao']['lula_vs_lula_1t']['votos'])}"
            for u in maiores_perdas
        )
        + ". Entre as capitais, "
        + " e ".join(
            f"{nome_proprio(c['nome'])} {sv(c['delta_votos_lula'])}" for c in cap_l
        )
        + "."
    )
    add(
        "Fonte: presidente.json (regioes.*.comparacao.lula_vs_lula_1t, "
        "regioes.*.contribuicao_pct_da_variacao_nacional, ufs[].comparacao, capitais[].delta_votos_lula)."
    )
    add("")

    # 5
    add(
        f"**5. O ganho de Flávio é nacional, e um terço veio do Nordeste.** Centro-Sul "
        f"{sv(cs['comparacao']['flavio_vs_bolsonaro_1t']['votos'])} "
        f"({p(contrib(cs, 'flavio_menos_bolsonaro_1t'), 1)}%), Nordeste "
        f"{sv(ne['comparacao']['flavio_vs_bolsonaro_1t']['votos'])} "
        f"({p(contrib(ne, 'flavio_menos_bolsonaro_1t'), 1)}%), Norte "
        f"{sv(no['comparacao']['flavio_vs_bolsonaro_1t']['votos'])} "
        f"({p(contrib(no, 'flavio_menos_bolsonaro_1t'), 1)}%). No Nordeste Flávio fez "
        f"{p(ne['r2026']['pct']['flavio'])}%, acima de Bolsonaro no 1º turno "
        f"({p(ne['r2022']['t1']['pct']['bolsonaro'])}%) e também no 2º turno de 2022 "
        f"({p(ne['r2022']['t2']['pct']['bolsonaro'])}%)."
    )
    add(
        "Fonte: presidente.json (regioes.Nordeste, regioes.Norte, regioes.Centro-Sul: "
        "r2026.pct, r2022.t1.pct, r2022.t2.pct, comparacao.flavio_vs_bolsonaro_1t)."
    )
    add("")

    # 6
    f_baixa, f_alta = faixas[0], faixas[-1]
    add(
        f"**6. Flávio cresceu mais onde Lula era mais forte.** Nos {n(f_alta['municipios'])} "
        f"municípios em que Lula teve {f_alta['faixa_lula_2022_pct']}% no 1º turno de 2022, "
        f"Flávio subiu {s(f_alta['swing_flavio_pp'])} pontos sobre Bolsonaro e Lula caiu "
        f"{s(f_alta['swing_lula_pp'])}; nos {n(f_baixa['municipios'])} em que Lula teve "
        f"{f_baixa['faixa_lula_2022_pct']}%, {s(f_baixa['swing_flavio_pp'])} e "
        f"{s(f_baixa['swing_lula_pp'])}. Na faixa mais lulista, Flávio somou "
        f"{sv(f_alta['delta_votos_flavio'])} votos e Lula {sv(f_alta['delta_votos_lula'])}. "
        "O movimento é quase uniforme no país, com leve ganho extra nos redutos petistas."
    )
    add(
        "Fonte: presidente.json (por_faixa_lula_2022; somas de votos por faixa, não médias)."
    )
    add("")

    # 7
    regs = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
    ufs_comp = sorted(ufs, key=lambda u: -u["comparacao"]["comparecimento_vs_1t_pp"])
    add(
        "**7. O comparecimento subiu no Norte e no Nordeste e caiu no Sul e no Sudeste.** "
        "Variação contra o 1º turno de 2022, em pontos: "
        + "; ".join(
            f"{r} {s(reg[r]['comparacao']['comparecimento_vs_1t_pp'])}" for r in regs
        )
        + f"; Brasil {s(comp['comparecimento_vs_1t_pp'])} ({p(nac['pct_comparecimento'])}% contra "
        f"{p(nac['r2022']['t1']['pct_comparecimento'])}%). Maiores altas: "
        + ", ".join(
            f"{u['uf']} {s(u['comparacao']['comparecimento_vs_1t_pp'])}"
            for u in ufs_comp[:3]
        )
        + "; maiores quedas: "
        + ", ".join(
            f"{u['uf']} {s(u['comparacao']['comparecimento_vs_1t_pp'])}"
            for u in reversed(ufs_comp[-3:])
        )
        + f". Nos municípios mais lulistas de 2022 a alta foi de "
        f"{s(f_alta['delta_comparecimento_pp'])} pontos, e mesmo assim Lula perdeu fatia ali."
    )
    add(
        "Fonte: presidente.json (regioes.*.comparacao.comparecimento_vs_1t_pp, "
        "ufs[].comparacao.comparecimento_vs_1t_pp, por_faixa_lula_2022.delta_comparecimento_pp); "
        "comparecimento de 2022 por município lido do detalhe por seção do TSE."
    )
    add("")

    # 8
    virada = sorted(ufs, key=lambda u: -u["comparacao"]["virada_margem_vs_1t_pp"])
    go = _uf(ufs, "GO")
    queda_l = min(ufs, key=lambda u: u["comparacao"]["lula_vs_lula_1t"]["pp"])
    rumo_lula = [u for u in ufs if u["comparacao"]["virada_margem_vs_1t_pp"] < 0]
    goiania = next(c for c in pres["capitais"] if c["uf"] == "GO")
    add(
        "**8. Onde a margem mais andou.** As maiores viradas para Flávio foram "
        + ", ".join(
            f"{u['uf']} {s(u['comparacao']['virada_margem_vs_1t_pp'])}"
            for u in virada[:3]
        )
        + f" pontos. A maior queda de Lula foi em {queda_l['uf']} "
        f"({s(queda_l['comparacao']['lula_vs_lula_1t']['pp'])}), onde Caiado teve "
        f"{p(go['pct']['caiado'])}% e Flávio subiu só {s(go['comparacao']['flavio_vs_bolsonaro_1t']['pp'])}; "
        f"Goiânia é a capital em que Flávio mais ficou abaixo de Bolsonaro "
        f"({s(goiania['swing_flavio_pp'])}). A margem andou para Lula só em "
        + ", ".join(
            f"{u['uf']} ({s(u['comparacao']['virada_margem_vs_1t_pp'])})"
            for u in rumo_lula
        )
        + "."
    )
    add(
        "Fonte: presidente.json (ufs[].comparacao.virada_margem_vs_1t_pp, ufs[].pct.caiado, "
        "capitais[].swing_flavio_pp)."
    )
    add("")

    # 9
    t22 = zz["r2022"]["t1"]
    cont = {c["continente"]: c for c in ext["continentes"]}
    grandes = [x for x in ext["paises"] if x["validos"] >= 5000]
    pt = max(grandes, key=lambda x: x["swing_flavio_vs_bolsonaro_1t_pp"] or -99)
    if pt["pais"] != "PT":
        raise RuntimeError(
            "o achado 9 supõe Portugal como maior alta de Flávio; revise"
        )
    jp = next(x for x in ext["paises"] if x["pais"] == "JP")
    add(
        f"**9. Exterior: Lula vence, o comparecimento caiu e Portugal foi o país que mais "
        f"andou para Flávio entre os que têm ao menos 5 mil válidos.** Lula "
        f"{p(zz['pct']['lula'])}% contra Flávio {p(zz['pct']['flavio'])}% ("
        f"{n(zz['votos']['lula'] - zz['votos']['flavio'])} votos). O eleitorado no exterior foi de "
        f"{n(t22['eleitores'])} para {n(zz['eleitores'])} ("
        f"{s(100 * (zz['eleitores'] / t22['eleitores'] - 1), 1)}%) e o comparecimento de "
        f"{n(t22['comparecimento'])} para {n(zz['comparecimento'])} ("
        f"{s(100 * (zz['comparecimento'] / t22['comparecimento'] - 1), 1)}%): a taxa caiu de "
        f"{p(t22['pct_comparecimento'])}% para {p(zz['pct_comparecimento'])}%. Lula leva a Europa "
        f"({p(cont['Europa']['pct']['lula'])}%); Flávio, a América do Norte "
        f"({p(cont['América do Norte']['pct']['flavio'])}%) e a Ásia "
        f"({p(cont['Ásia']['pct']['flavio'])}%, Japão {p(jp['pct']['flavio'])}%). Em Portugal "
        f"Flávio fez {p(pt['pct']['flavio'])}%, {s(pt['swing_flavio_vs_bolsonaro_1t_pp'])} pontos "
        f"sobre Bolsonaro nas mesmas cidades, e Lula {s(pt['swing_lula_vs_lula_1t_pp'])}."
    )
    add(
        "Fonte: presidente.json (ufs[uf=ZZ] e ufs[uf=ZZ].r2022.t1); exterior.json "
        "(continentes, paises[pais=PT], paises[pais=JP])."
    )
    add("")

    # 10
    pico = [x for x in trav["nacional"] if x["pst_de"] < 99]
    grande = max(pico, key=lambda x: x["minutos"])
    lote = max(versoes[1:], key=lambda v: v.get("d_vv") or 0)
    pior = div["maior_diferenca_visivel"]
    minutos_div = _linhas(div["minutos"])
    estavel = [
        m for m in minutos_div if m["hora_brt"] >= "19:35" and m["hora_brt"] <= "20:04"
    ]
    ab_mesmo = estavel[0]["andamento_br_st_visivel"] if estavel else None
    add(
        "**10. O arquivo nacional de presidente parou três vezes no pico.** "
        + "; ".join(
            f"{hm(x['de_brt'])} a {hm(x['ate_brt'])} ({p(x['minutos'], 1)} min, de "
            f"{p(x['pst_de'])}% para {p(x['pst_ate'])}% das seções)"
            for x in pico
        )
        + f". Na parada de {p(grande['minutos'], 1)} minutos o coletor leu o arquivo "
        f"{n(grande['leituras_no_intervalo']['total'])} vezes, "
        f"{n(grande['leituras_no_intervalo']['por_classe'].get('nao_modificado', 0))} delas com 304 "
        f"(não modificado). A maior defasagem visível foi às {pior['hora_brt']}: a soma dos 28 "
        f"arquivos de UF tinha {n(pior['secoes'])} seções a mais que o nacional "
        f"({p(pior['pp_do_total'])}% do total). De 19:35 a 20:04 a diferença ficou entre "
        f"{n(min(m['diferenca_visivel'] for m in estavel))} e "
        f"{n(max(m['diferenca_visivel'] for m in estavel))} seções, enquanto o andamento "
        f"nacional (-ab) do próprio TSE já marcava {n(ab_mesmo)}. O lote que destravou, às "
        f"{hm(lote['gerado_brt'])}, trouxe {n(lote['d_st'])} seções e {mi(lote['d_vv'])} de "
        f"válidos (Lula {p(lote['lote_pct_lula'])}%, Flávio {p(lote['lote_pct_flavio'])}% do lote)."
    )
    add(
        "Fonte: linha_do_tempo.json (travamentos.nacional, divergencia_soma_ufs.minutos e "
        "maior_diferenca_visivel, nacional.versoes colunas d_st, d_vv, lote_pct_*)."
    )
    add("")

    # 11
    pausa = max(linha["pausa_geral"]["lacunas"], key=lambda x: x["minutos"])
    leit = pausa["leituras_no_intervalo"]
    ab_p = [x["gerado_brt"] for x in pausa["versoes_de_andamento_ab_no_intervalo"]]
    add(
        f"**11. Das {hm(pausa['de_brt'])} às {hm(pausa['ate_brt'])} o TSE não gerou nenhum "
        f"arquivo de resultado.** Em {p(pausa['minutos'], 1)} minutos, nenhuma versão de nenhum "
        "arquivo `-u` (presidente, governador, Senado, deputados; nacional, UF, município ou zona) "
        "tem hora de geração dentro do intervalo. O coletor fez "
        f"{n(sum(leit.values()))} requisições nesse tempo ({n(leit.get('nao_modificado', 0))} "
        f"com 304; as {n(leit.get('ok', 0))} com corpo novo trazem versões geradas antes de "
        f"{hm(pausa['de_brt'])}). Os 28 arquivos de UF de presidente mostram a mesma parada. "
        + (
            f"Só os arquivos de andamento (-ab) tiveram versão nova no intervalo: {len(ab_p)}, "
            f"todos gerados entre {hm(min(ab_p))} e {hm(max(ab_p))}, numa única rodada."
            if ab_p
            else "Nem os arquivos de andamento (-ab) tiveram versão nova no intervalo."
        )
    )
    add(
        "Fonte: linha_do_tempo.json (pausa_geral.lacunas, travamentos.ufs, "
        "travamentos.todas_as_ufs_sem_versao_nova)."
    )
    add("")

    # 12
    fusos = {x["uf"]: x for x in linha["fuso_da_totalizacao"]["por_uf"]}
    wel = next(
        c for c in ext["hora_local"]["mais_adiantadas"] if c["nome"] == "WELLINGTON"
    )
    add(
        "**12. A hora de totalização do TSE está no relógio local.** Contra a hora de geração "
        f"(Brasília), a totalização impressa fica, na mediana, {s(fusos['AC']['mediana_min'], 0)} "
        f"min no AC, {s(fusos['AM']['mediana_min'], 0)} no AM, {s(fusos['MT']['mediana_min'], 0)} "
        f"no MT, MS, RO e RR, e chega a {s(fusos['PE']['maximo_min'], 1)} min em PE (Fernando "
        f"de Noronha). No exterior, Wellington imprime {wel['totalizacao_impressa']} num arquivo "
        f"gerado às {hm(wel['primeira_versao_totalizada_gerada_brt'])} de 04/10, e o andamento "
        "nacional (-ab) exibiu "
        + ", ".join(div["andamento_br_totalizacao_impressa_na_janela"])
        + " como última totalização durante toda a noite. "
        f"{ext['hora_local']['cidades_com_data_impressa_de_05_10_e_arquivo_de_04_10']} cidades do "
        "exterior aparecem totalizadas em 05/10 em arquivos gerados em 04/10."
    )
    add(
        "Fonte: linha_do_tempo.json (fuso_da_totalizacao.por_uf, "
        "divergencia_soma_ufs.andamento_br_totalizacao_impressa_na_janela); exterior.json (hora_local)."
    )
    add("")

    # 13
    cls = idg["total_por_classe"]
    marc = idg["presidente_versao_vigente_marcada_regressiva"]
    concl = {c["uf"]: c for c in linha["conclusao_ufs"]}
    atrasos = sorted(
        (
            c
            for c in linha["conclusao_ufs"]
            if (c["atraso_da_regra_do_coletor_min"] or 0) > 10
        ),
        key=lambda c: -c["atraso_da_regra_do_coletor_min"],
    )
    add(
        f"**13. A marca de cópia antiga do coletor errou em {p(pct(cls['mais_nova_que_todas_as_anteriores'], idg['total_eventos'], 1), 1)}% "
        f"dos casos.** Dos {n(idg['total_eventos'])} eventos `idg_regressivo`, "
        f"{n(cls['mais_nova_que_todas_as_anteriores'])} eram versões mais novas que tudo o que "
        f"o mesmo arquivo já tinha publicado; só {n(cls['copia_antiga'])} eram cópias antigas e "
        f"{n(cls.get('mesma_geracao', 0))} repetiam a mesma geração. O contador `idg` do TSE não "
        f"cresce dentro do arquivo. Em presidente, {n(marc['arquivos_por_nivel'].get('mu', 0))} "
        f"arquivos municipais e {n(marc['arquivos_por_nivel'].get('zona', 0))} de zona tinham a "
        f"versão final marcada ({n(marc['secoes_a_mais_na_versao_vigente'].get('mu', 0))} e "
        f"{n(marc['secoes_a_mais_na_versao_vigente'].get('zona', 0))} seções a mais nela). A hora "
        "de 100% das UFs muda: "
        + "; ".join(
            f"{c['uf']} {hm(c['gerado_brt'])}, não {hm(c['regra_do_coletor_gerado_brt'])}"
            for c in atrasos
        )
        + f" (o AM fechou às {hm(concl['AM']['gerado_brt'])})."
    )
    add(
        "Fonte: linha_do_tempo.json (idg_regressivo.total_por_classe, "
        "idg_regressivo.presidente_versao_vigente_marcada_regressiva, conclusao_ufs)."
    )
    add("")

    # 14
    inc = conf["municipios_incompletos"]
    dmun = conf["soma_municipios_menos_nacional"]
    zon = produtos["zonas.json"]
    ultima = max((x["ultima_leitura_brt"] or "") for x in inc) if inc else None
    gov_ok = sum(
        1 for x in inc if x["secoes_governador"][0] == x["secoes_governador"][1]
    )
    if not inc:
        add(
            f"**14. Nenhum arquivo municipal de presidente está congelado incompleto na versão vigente; "
            f"{zon['n_incompletas']} arquivos de zona continuam incompletos.** Os municipais que "
            "congelaram na noite foram regerados pelo TSE depois, e o banco guarda as duas versões. A soma "
            f"dos municípios fica {n(abs(dmun['secoes']))} seções e {n(abs(dmun['validos']))} válidos "
            f"{'abaixo' if dmun['validos'] < 0 else 'acima'} do nacional "
            f"(Flávio {sv(dmun['flavio'])}, Lula {sv(dmun['lula'])})."
        )
    else:
        add(
            f"**14. {len(inc)} arquivos municipais e {zon['n_incompletas']} de zona de presidente "
            "congelaram incompletos.** Pararam em versões geradas entre "
            f"{hm(min(x['gerado_em_brt'] for x in inc))} e {hm(max(x['gerado_em_brt'] for x in inc))} "
            f"de 04/10, com {n(sum(x['secoes_total'] - x['secoes'] for x in inc))} seções a menos nos "
            "municípios; o andamento (-ab) da UF já os dava completos e as leituras seguintes "
            f"receberam 304 até {hm(ultima)} de 05/10. O arquivo de governador dos mesmos "
            f"municípios está completo em {gov_ok} de {len(inc)}. A soma dos municípios fica "
            f"{n(abs(dmun['secoes']))} seções e {n(abs(dmun['validos']))} válidos abaixo do nacional "
            f"(Flávio {sv(dmun['flavio'])}, Lula {sv(dmun['lula'])})."
        )
    add(
        "Fonte: presidente.json (conferencia.municipios_incompletos, com secoes_governador, "
        "conferencia.soma_municipios_menos_nacional); zonas.json (n_incompletas)."
    )
    add("")

    # 15
    tot = tardias["total"]
    add(
        f"**15. Depois da meia-noite chegaram {n(tot['secoes'])} seções, em "
        f"{n(tot['municipios'])} municípios, com {n(tot['validos'])} válidos: Lula "
        f"{p(tot['pct_lula'])}%, Flávio {p(tot['pct_flavio'])}%.** "
        + "; ".join(
            f"{nome_proprio(m['nome'])} ({m['uf']}) {secoes(m['secoes'])}, Lula {p(m['pct_lula'])}%"
            for m in tardias["municipios"]
        )
        + f". O andamento (-ab) confirma as mesmas {n(tardias['andamento_ab']['secoes'])} seções; "
        f"o arquivo nacional foi de {n(tardias['nacional_antes_do_corte'])} para "
        f"{n(tardias['nacional_final'])}."
    )
    add("Fonte: linha_do_tempo.json (secoes_tardias).")
    add("")

    # inferências
    add("## Inferências (rotuladas, não são medição)")
    add("")
    ne26, ne22 = ne["r2026"], ne["r2022"]["t1"]
    add(
        f"- **Inferência.** No Nordeste, o ganho líquido de Flávio "
        f"({sv(ne['comparacao']['flavio_vs_bolsonaro_1t']['votos'])}) foi "
        f"{p(ne['comparacao']['flavio_vs_bolsonaro_1t']['votos'] / abs(ne['comparacao']['lula_vs_lula_1t']['votos']), 1)} "
        f"vezes a perda líquida de Lula ({sv(ne['comparacao']['lula_vs_lula_1t']['votos'])}), "
        f"com os válidos da região subindo {n(ne26['validos'] - ne22['validos'])} e os terceiros "
        f"caindo de {p(ne22['pct']['terceiros'])}% para {p(ne26['pct']['terceiros'])}%. O saldo "
        "é compatível com voto novo e com eleitor de terceira via, mais do que com troca direta "
        "de Lula por Flávio. Dado agregado não identifica quem trocou de voto."
    )
    add(
        f"- **Inferência.** No Centro-Sul, Lula perdeu mais "
        f"({sv(cs['comparacao']['lula_vs_lula_1t']['votos'])}) do que Flávio ganhou "
        f"({sv(cs['comparacao']['flavio_vs_bolsonaro_1t']['votos'])}), com o comparecimento "
        f"caindo {p(abs(cs['comparacao']['comparecimento_vs_1t_pp']))} ponto. Parte do voto de Lula "
        "em 2022 parece ter ido para a abstenção ou para outras candidaturas, não só para Flávio."
    )
    add(
        "- **Inferência.** As paradas foram de publicação, não de contagem: entre 19:14 e "
        "19:32 os arquivos de UF e o andamento (-ab) avançaram enquanto o arquivo nacional "
        "ficou parado (achado 10), e durante a pausa total o andamento ainda publicou versão "
        "nova (achado 11). A causa da pausa não aparece nos dados; só o TSE pode explicá-la."
    )
    add(
        f"- **Inferência.** As seções tardias vêm de municípios remotos e de voto petista, "
        f"padrão compatível com logística de transmissão, e não mudam nada: {n(tot['validos'])} válidos "
        f"contra uma diferença de {n(nac['diferenca_votos'])} votos."
    )
    add("")

    # outros cargos
    pl = next(x for x in cam["votos_por_partido"] if x["partido"] == "PL")
    pt_ = next(x for x in cam["votos_por_partido"] if x["partido"] == "PT")
    top = cam["deputados_mais_votados"][0]
    add("## Outros cargos, para referência")
    add("")
    add(
        f"- Câmara: PL {mi(pl['votos'])} de votos ({p(pl['pct'])}%) contra PT {mi(pt_['votos'])} "
        f"({p(pt_['pct'])}%); mais votado do país, {nome_proprio(top['nome'])} ({top['partido']}-"
        f"{top['uf']}), {n(top['votos'])} votos, {p(top['pct_na_uf'])}% da UF. Bancada por campo: "
        + ", ".join(f"{k} {v}" for k, v in cam["por_campo"].items() if v)
        + ". Fonte: camara.json (votos_por_partido, deputados_mais_votados, por_campo)."
    )
    add(
        "- Senado: "
        + ", ".join(
            f"{k} {v}" for k, v in list(sen["eleitos_2026_por_partido"].items())[:4]
        )
        + f" entre os {len(sen['eleitos_2026'])} eleitos de 2026. Fonte: senado.json "
        "(eleitos_2026_por_partido)."
    )
    add("")

    # correções
    add("## Correções e atualizações ao BRIEF.md que os dados impõem")
    add("")
    add(
        f"- Placar: o BRIEF usa a leitura das 23:43 (499.226 seções). O final, com "
        f"{n(nac['secoes'])} seções, é Flávio {n(nac['votos']['flavio'])} contra Lula "
        f"{n(nac['votos']['lula'])}, diferença de {n(nac['diferenca_votos'])}."
    )
    add(
        f"- Cópias antigas: o banco tem {n(idg['total_eventos'])} eventos `idg_regressivo`, não "
        f"515, e só {n(cls['copia_antiga'])} são cópias antigas (achado 13)."
    )
    add(
        '- "Arquivos de UF parados enquanto os municipais seguiam": nenhum arquivo de nenhum '
        "nível foi gerado entre "
        f"{hm(pausa['de_brt'])} e {hm(pausa['ate_brt'])}; as leituras com corpo novo naquele "
        "intervalo eram de versões anteriores (achado 11)."
    )
    add(
        "- Hora de 100% das UFs: "
        + "; ".join(f"{c['uf']} {hm(c['gerado_brt'])}" for c in atrasos)
        + " (achado 13)."
    )
    add(
        "- Seções tardias no AM: "
        + ", ".join(
            f"{nome_proprio(m['nome'])} {m['secoes']}"
            for m in tardias["municipios"]
            if m["uf"] == "AM"
        )
        + f"; no total, {n(tot['secoes'])} seções depois da meia-noite (achado 15)."
    )
    add(
        f"- Câmara no `final.json` regerado: {cam['n_ufs_provisorio']} UFs provisórias ("
        + ", ".join(cam["ufs_provisorias"])
        + "), PSD "
        + str(cam["por_partido"].get("PSD"))
        + " e Republicanos "
        + str(cam["por_partido"].get("REPUBLICANOS"))
        + " cadeiras."
    )
    add("")
    add("## Limites")
    add("")
    add(
        "- Comparar Flávio com Bolsonaro e Lula com Lula de 2022 mede saldo agregado entre duas "
        "eleições com candidatos e eleitorado diferentes; não é transferência de eleitor."
    )
    add(
        "- O comparecimento de 2022 por município vem do detalhe por seção do TSE (cargo de "
        "presidente, 1º turno); municípios novos (Boa Esperança do Norte, MT) ficam sem 2022."
    )
    add(
        "- A latência (captura menos geração) inclui o intervalo de sondagem do coletor; é teto, "
        "não medida da demora do TSE."
    )
    add(
        "- Zonas casam com 2022 pelo número; rezoneamento pode mudar o território de uma zona."
    )
    add(
        "- O banco continua recebendo leituras; arquivos congelados podem ser republicados e "
        "mudar as conferências numa nova execução."
    )
    add("")
    return "\n".join(o)
