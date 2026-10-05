"""Riscos, achados contrários e os dez movimentos do capítulo "O caminho do 2º turno".

Recebe as seções já montadas por ``estrategia_secoes.py`` e as fontes lidas.
Os votos esperados de cada movimento saem de uma regra escrita ao lado do
número; nenhum é previsão, e os movimentos territoriais se sobrepõem aos de
terceira via (o mesmo eleitor pode estar nos dois).
"""

from __future__ import annotations

from . import estrategia as E
from .estrategia import milhar
from .estrategia_leitura import sem_acento
from .estrategia_secoes import (
    a26_de,
    flavio_lula,
    ufs_presidente,
    votos_numero,
    votos_terceiros_por_uf,
)

PONTOS_COMPARECIMENTO = 1.0
MUNICIPIO_GRANDE = 100_000  # votos válidos para presidente em 2026
NUM_CAIADO = 55


def _pct_candidato(fontes: dict, m: dict, numero: int) -> float:
    dis = fontes["pres_mu"][(m["uf"], m["codigo_tse"])]
    return E.r2(E.pct(votos_numero(dis, numero), dis["validos"]))


def _valor_comparecimento(fontes: dict, ufs: list[str]) -> dict:
    """Saldo de +1 ponto de comparecimento nas UFs, eleitor novo votando como a UF."""
    total = 0.0
    linhas = []
    for uf in ufs:
        dis = fontes["pres"][(uf, "")]
        f, lu = flavio_lula(dis)
        vv = dis["validos"]
        saldo = E.saldo_comparecimento(
            dis["eleitores"],
            PONTOS_COMPARECIMENTO,
            vv / dis["comparecimento"] if dis["comparecimento"] else 0.0,
            f / vv if vv else 0.0,
            lu / vv if vv else 0.0,
        )
        total += saldo
        linhas.append({"uf": uf, "saldo_flavio": round(saldo)})
    linhas.sort(key=lambda x: -abs(x["saldo_flavio"]))
    return {"saldo_flavio": round(total), "ufs": linhas}


def _comparecimento(fontes: dict, geo: dict) -> dict:
    ufs = ufs_presidente(fontes)
    api = fontes["api22"]
    por_uf = []
    for uf in ufs:
        v = E.variacao_comparecimento_2022(api[uf][1], api[uf][2])
        v["uf"] = uf
        v["regiao"] = E.regiao_de(uf)
        v["governador_2t_2022"] = uf in fontes["gov_2t_2022"]
        v["lula_2022_2t_pct"] = E.r2(E.pct(api[uf][2]["lula"], api[uf][2]["validos"]))
        por_uf.append(v)
    grupos = {}
    for rotulo, cond in (
        ("com_2t_governador_2022", True),
        ("sem_2t_governador_2022", False),
    ):
        membros = [u for u in ufs if (u in fontes["gov_2t_2022"]) is cond]
        c1 = sum(api[u][1]["comparecimento"] for u in membros)
        c2 = sum(api[u][2]["comparecimento"] for u in membros)
        el = sum(api[u][1]["eleitores"] for u in membros)
        grupos[rotulo] = {
            "ufs": membros,
            "variacao_votos": c2 - c1,
            "variacao_pp": E.r2(E.pct(c2, el) - E.pct(c1, el)),
        }
    regioes = {}
    for reg in E.REGIOES:
        membros = [u for u in ufs if E.regiao_de(u) == reg]
        c1 = sum(api[u][1]["comparecimento"] for u in membros)
        c2 = sum(api[u][2]["comparecimento"] for u in membros)
        el = sum(api[u][1]["eleitores"] for u in membros)
        r = geo["regioes"][reg]
        regioes[reg] = {
            "variacao_2022_votos": c2 - c1,
            "variacao_2022_pp": E.r2(E.pct(c2, el) - E.pct(c1, el)),
            "comparecimento_2026_pct": r["comparecimento_2026_pct"],
            "comparecimento_2022_1t_pct": r["comparecimento_2022_1t_pct"],
            "diferenca_2026_menos_2022_1t_pp": E.r2(
                r["comparecimento_2026_pct"] - r["comparecimento_2022_1t_pct"]
            ),
            "valor_1pp_2026": _valor_comparecimento(fontes, membros)["saldo_flavio"],
        }
    corr = E.correlacao(
        [p["variacao_pp"] for p in por_uf], [p["lula_2022_2t_pct"] for p in por_uf]
    )
    venceu_f = [
        u
        for u in ufs
        if a26_de(fontes["pres"][(u, "")])["flavio"]
        > a26_de(fontes["pres"][(u, "")])["lula"]
    ]
    venceu_l = [u for u in ufs if u not in venceu_f]
    return {
        "nota": (
            "Variação de 2022 = comparecimento do 2º turno menos o do 1º, mesmo "
            "eleitorado apto. Valor de 1 ponto em 2026 = saldo Flávio menos Lula "
            "se 1% do eleitorado apto a mais comparecer e votar como a própria UF "
            "votou no 1º turno (hipótese, não medição; o eleitor que falta não é "
            "o eleitor médio da UF)."
        ),
        "por_uf_2022": sorted(por_uf, key=lambda p: p["variacao_pp"]),
        "grupos_2022": grupos,
        "regioes": regioes,
        "correlacao_variacao_2022_x_lula_2t_2022": (
            None if corr is None else round(corr, 3)
        ),
        "valor_1pp_ufs_flavio": _valor_comparecimento(fontes, venceu_f),
        "valor_1pp_ufs_lula": _valor_comparecimento(fontes, venceu_l),
        "ufs_flavio": venceu_f,
        "ufs_lula": venceu_l,
    }


def _governo_direita_flavio_perdeu(fontes: dict) -> list[dict]:
    saida = []
    for uf in ufs_presidente(fontes):
        gdis = fontes["gov"][(uf, "")]
        top = gdis["candidatos"][0]
        eleito = top["st"] == "Eleito" or (
            top["st"] is None and E.pct(top["votos"], gdis["validos"]) > 50
        )
        if not eleito or top["campo"] not in ("direita", "centro-direita"):
            continue
        f, lu = flavio_lula(fontes["pres"][(uf, "")])
        if f >= lu:
            continue
        vv = fontes["pres"][(uf, "")]["validos"]
        saida.append(
            {
                "uf": uf,
                "governador": top["nome"],
                "partido": top["partido"],
                "campo": top["campo"],
                "governador_pct": E.r2(E.pct(top["votos"], gdis["validos"])),
                "flavio_pct": E.r2(E.pct(f, vv)),
                "lula_pct": E.r2(E.pct(lu, vv)),
                "lula_menos_flavio_votos": lu - f,
            }
        )
    return saida


def secao_riscos(fontes: dict, arit: dict, geo: dict, gov: dict) -> dict:
    ufs = geo["ufs"]
    piores_pp = sorted(ufs, key=lambda c: c["flavio_menos_bolsonaro_2t_pp"])[:6]
    piores_votos = sorted(ufs, key=lambda c: c["flavio_menos_bolsonaro_2t_votos"])[:6]
    piores_1t = sorted(ufs, key=lambda c: c["flavio_menos_bolsonaro_1t_pp"])[:5]
    mun = geo["_municipios"]
    recuo = sorted(mun, key=lambda m: m["flavio"] - m["bolsonaro_2022_1t"])[:10]
    grandes = [m for m in mun if m["validos"] >= MUNICIPIO_GRANDE]
    recuo_pp = sorted(
        grandes, key=lambda m: m["flavio_pct"] - m["bolsonaro_2022_1t_pct"]
    )[:10]
    projs = arit["projecoes"]
    margens = [p["margem_votos"] for p in projs]
    nexus = arit["matrizes"]["nexus"]["linhas_publicadas"]
    datafolha = arit["matrizes"]["datafolha"]["linhas_publicadas"]
    pred = fontes["predicao"]["central"]["brasil"]
    p1 = arit["primeiro_turno"]
    ext = geo["exterior"]
    api_zz = fontes["api22"]["ZZ"]
    estoque_flavio = geo["estoque"]["total_ufs"]
    estoque_lula = geo["estoque"]["total_lula_ufs"]
    return {
        "piores_ufs_pp_contra_2t_2022": [
            {
                k: c[k]
                for k in (
                    "uf",
                    "flavio_pct",
                    "bolsonaro_2022_2t_pct",
                    "flavio_menos_bolsonaro_2t_pp",
                    "terceiros_pct",
                )
            }
            for c in piores_pp
        ],
        "piores_ufs_votos_contra_2t_2022": [
            {
                k: c[k]
                for k in (
                    "uf",
                    "flavio",
                    "bolsonaro_2022_2t",
                    "flavio_menos_bolsonaro_2t_votos",
                )
            }
            for c in piores_votos
        ],
        "piores_ufs_contra_1t_2022": [
            {
                k: c[k]
                for k in (
                    "uf",
                    "flavio_pct",
                    "bolsonaro_2022_1t_pct",
                    "flavio_menos_bolsonaro_1t_pp",
                )
            }
            for c in piores_1t
        ],
        "municipios_abaixo_de_bolsonaro_1t_votos": [
            {
                "uf": m["uf"],
                "municipio": m["municipio"],
                "flavio": m["flavio"],
                "bolsonaro_2022_1t": m["bolsonaro_2022_1t"],
                "variacao_votos": m["flavio"] - m["bolsonaro_2022_1t"],
                "flavio_pct": m["flavio_pct"],
                "bolsonaro_2022_1t_pct": m["bolsonaro_2022_1t_pct"],
            }
            for m in recuo
        ],
        "municipio_grande_minimo_validos": MUNICIPIO_GRANDE,
        "municipios_grandes_abaixo_de_bolsonaro_1t_pp": [
            {
                "uf": m["uf"],
                "municipio": m["municipio"],
                "validos": m["validos"],
                "flavio_pct": m["flavio_pct"],
                "bolsonaro_2022_1t_pct": m["bolsonaro_2022_1t_pct"],
                "diferenca_pp": E.r2(m["flavio_pct"] - m["bolsonaro_2022_1t_pct"]),
                "caiado_pct": _pct_candidato(fontes, m, NUM_CAIADO),
                "terceiros_pct": E.r2(
                    E.pct(m["validos"] - m["flavio"] - m["lula"], m["validos"])
                ),
            }
            for m in recuo_pp
        ],
        "governador_direita_eleito_flavio_perdeu": _governo_direita_flavio_perdeu(
            fontes
        ),
        "estoque_lula_maior": {
            "estoque_flavio": estoque_flavio,
            "estoque_lula": estoque_lula,
            "razao": (
                round(estoque_lula / estoque_flavio, 2) if estoque_flavio else None
            ),
            "lula_2022_2t_pct": geo["brasil_sem_exterior"]["lula_2022_2t_pct"],
            "lula_2026_pct": geo["brasil_sem_exterior"]["lula_pct"],
            "bolsonaro_2022_2t_pct": geo["brasil_sem_exterior"][
                "bolsonaro_2022_2t_pct"
            ],
            "flavio_2026_pct": geo["brasil_sem_exterior"]["flavio_pct"],
        },
        "comparecimento": _comparecimento(fontes, geo),
        "exterior": {
            "flavio_pct": ext["flavio_pct"],
            "lula_pct": ext["lula_pct"],
            "margem_votos": ext["margem_votos"],
            "validos": ext["validos_2026"],
            "eleitores": ext["eleitores_2026"],
            "comparecimento_2026_pct": ext["comparecimento_2026_pct"],
            "comparecimento_2022_1t_pct": ext["comparecimento_2022_1t_pct"],
            "comparecimento_2022_2t_pct": ext["comparecimento_2022_2t_pct"],
            "bolsonaro_2022_2t_pct": ext["bolsonaro_2022_2t_pct"],
            "lula_2022_2t_margem_votos": api_zz[2]["lula"] - api_zz[2]["bolsonaro"],
        },
        "transferencia": {
            "margem_min": min(margens),
            "margem_max": max(margens),
            "caiado_nexus": nexus["Caiado"],
            "caiado_datafolha": datafolha["Caiado"],
            "cury_nexus": nexus["Cury"],
            "cury_datafolha": datafolha["Cury"],
            "central_casa_margem_pp": E.r2(pred["margem_flavio_lula"]),
            "urna_margem_pp": p1["diferenca_pp"],
            "central_casa_menos_urna_pp": E.r2(
                pred["margem_flavio_lula"] - p1["diferenca_pp"]
            ),
            "erro_comum_2022_casas": fontes["erro_2022"]["media_das_casas"]["n_casas"],
            "erro_comum_2022_pp": round(
                fontes["erro_2022"]["aplicacao_2026"][
                    "erro_comum_2022_diferenca_lula_menos_bolsonaro_pp"
                ],
                2,
            ),
        },
        "base": {
            "trocar_para_lula_pct": arit["equilibrio"][
                "base_flavio_trocando_para_lula_pct"
            ],
            "abster_pct": arit["equilibrio"]["base_flavio_abstendo_pct"],
        },
    }


# ---------------------------------------------------------------- movimentos


def _saldo_central(arit: dict, origem: str) -> int:
    central = next(
        p
        for p in arit["projecoes"]
        if p["matriz"] == "nexus" and p["hipotese"] == "fica_fora"
    )
    return next(d["saldo_flavio"] for d in central["detalhe"] if d["origem"] == origem)


def _saldo(arit: dict, matriz: str, hipotese: str, origem: str) -> int:
    proj = next(
        p
        for p in arit["projecoes"]
        if p["matriz"] == matriz and p["hipotese"] == hipotese
    )
    return next(d["saldo_flavio"] for d in proj["detalhe"] if d["origem"] == origem)


def _margem(arit: dict, matriz: str, hipotese: str) -> int:
    return next(
        p["margem_votos"]
        for p in arit["projecoes"]
        if p["matriz"] == matriz and p["hipotese"] == hipotese
    )


def sinal_pontos(x: float) -> str:
    """Saldo em pontos com sinal, para a regra escrita ao lado do número."""
    return f"{x:+g} pontos".replace(".", ",").replace("-", "\u2212")


def _fl(linhas: dict, nome: str) -> str:
    """Linha publicada como texto: Flávio × Lula, sobre a soma da linha."""
    ln = linhas[nome]
    return f"Flávio {ln['Flávio']:g} × Lula {ln['Lula']:g}, soma {sum(ln.values()):g}"


def _entre(c: dict) -> str:
    """Linhas de 1º e 2º turno no eleitorado do governador, com as páginas."""
    a, b = c["linha_1t"], c["linha_2t"]
    return (
        f"Datafolha pp. {c['paginas'][0]}–{c['paginas'][1]}: Flávio {a['Flávio']} → "
        f"{b['Flávio']}, Lula {a['Lula']} → {b['Lula']}"
    )


def secao_movimentos(fontes: dict, arit: dict, geo: dict, gov: dict) -> list[dict]:
    nx = arit["matrizes"]["nexus"]["linhas_publicadas"]
    dfo = arit["matrizes"]["datafolha"]["linhas_publicadas"]
    terceiros = {t["numero"]: t for t in arit["primeiro_turno"]["terceiros"]}
    cury, renan, caiado = terceiros[70], terceiros[14], terceiros[55]
    zema_dir = [t for t in terceiros.values() if t["linha"] == "Zema"]
    medidas = gov["consolidacao_medida"]
    mg = next(c for c in medidas if c["uf"] == "MG")
    rj_ruas = next(c for c in medidas if c["origem"].startswith("Douglas"))
    rj_paes = next(c for c in medidas if c["origem"].startswith("Eduardo"))
    # Taxa transportada para SP: média do saldo medido no eleitorado do
    # governador aliado em MG (Cleitinho) e no RJ (Douglas Ruas).
    taxa_aliado = (mg["saldo_flavio_pontos"] + rj_ruas["saldo_flavio_pontos"]) / 200
    sp = next(a for a in gov["aliados"] if a["uf"] == "SP")
    linha_sp = next(ln for ln in gov["linhas_datafolha"] if ln["uf"] == "SP")
    ne = geo["nordeste"]["capitais_x_interior"]
    comp = _comparecimento(fontes, geo)
    fora_total = sum(
        d["fora"]
        for p in arit["projecoes"]
        if p["matriz"] == "nexus" and p["hipotese"] == "fica_fora"
        for d in p["detalhe"]
    )
    cury_df = _saldo(arit, "datafolha", "fica_fora", cury["nome"])
    caiado_df = _saldo(arit, "datafolha", "fica_fora", caiado["nome"])
    cury_nx = _saldo_central(arit, cury["nome"])
    caiado_nx = _saldo_central(arit, caiado["nome"])
    go = fontes["gov"][("GO", "")]["candidatos"][0]
    caiado_go = next(
        u for u in votos_terceiros_por_uf(fontes, 55, 27) if u["uf"] == "GO"
    )
    movimentos = [
        {
            "id": "renan",
            "titulo": "Colher o eleitor de Renan Santos",
            "alvo": f"{milhar(renan['votos'])} votos de Renan Santos (Missão)",
            "votos_esperados": _saldo_central(arit, renan["nome"]),
            "regra": f"votos de Renan × (Flávio − Lula) da linha Nexus normalizada ({_fl(nx, 'Renan')})",
            "onde": votos_terceiros_por_uf(fontes, 14),
            "rotulo": "inferência sobre medição publicada (Nexus, p. 79)",
        },
        {
            "id": "nao_escolha",
            "titulo": "Converter a não escolha da terceira via",
            "alvo": "parcela das linhas da Nexus em branco, nulo ou indecisa",
            "votos_esperados": _margem(arit, "nexus", "proporcional")
            - _margem(arit, "nexus", "fica_fora"),
            "regra": "margem com a não escolha votando na proporção da própria linha menos margem só com o medido",
            "teto": fora_total,
            "rotulo": "hipótese declarada sobre medição publicada",
        },
        {
            "id": "sp_tarcisio",
            "titulo": "Agenda conjunta com Tarcísio em São Paulo",
            "alvo": (
                f"{milhar(sp['governador_votos'])} votos de Tarcísio; vão de "
                f"{milhar(sp['vao_votos'])} votos sobre Flávio"
            ),
            "votos_esperados": round(sp["governador_votos"] * taxa_aliado),
            "regra": (
                "votos de Tarcísio × média do saldo entre as perguntas de 1º e 2º "
                f"turno medido no eleitorado do governador aliado em MG "
                f"({sinal_pontos(mg['saldo_flavio_pontos'])}) e no RJ "
                f"({sinal_pontos(rj_ruas['saldo_flavio_pontos'])}); a transcrição da "
                "casa do relatório de SP (p. 4) só tem a linha de 1º turno, então a "
                "taxa é transportada"
            ),
            "teto": sp["vao_votos"],
            "linha_medida_1t": {"Flávio": linha_sp["Flávio"], "Lula": linha_sp["Lula"]},
            "onde": sp["top_municipios"],
            "rotulo": "hipótese (taxa medida em MG e RJ aplicada a SP)",
        },
        {
            "id": "cury",
            "titulo": "Disputar o eleitor de Augusto Cury",
            "alvo": f"{milhar(cury['votos'])} votos de Cury (Avante)",
            "votos_esperados": round((cury_nx + cury_df) / 2),
            "regra": (
                f"média das linhas Nexus ({_fl(nx, 'Cury')}) e Datafolha "
                f"({_fl(dfo, 'Cury')}) aplicadas aos votos de Cury"
            ),
            "faixa": [min(cury_nx, cury_df), max(cury_nx, cury_df)],
            "onde": votos_terceiros_por_uf(fontes, 70),
            "rotulo": "inferência sobre duas medições publicadas",
        },
        {
            "id": "mg_cleitinho",
            "titulo": "Agenda conjunta com Cleitinho em Minas",
            "alvo": f"{milhar(mg['votos_governador_urna'])} votos de Cleitinho",
            "votos_esperados": mg["saldo_aplicado_a_urna"],
            "regra": (
                "votos de Cleitinho × saldo entre as perguntas de 1º e 2º turno "
                f"no eleitorado dele ({_entre(mg)})"
            ),
            "teto": next(a["vao_votos"] for a in gov["aliados"] if a["uf"] == "MG"),
            "onde": next(
                a["top_municipios"] for a in gov["aliados"] if a["uf"] == "MG"
            ),
            "rotulo": "inferência sobre medição publicada",
        },
        {
            "id": "ne_interior",
            "titulo": "Nordeste: interior antes das capitais",
            "alvo": (
                f"{milhar(ne['interior']['terceiros_2026'] + ne['capitais']['terceiros_2026'])}"
                " votos de terceira via no Nordeste, "
                f"{milhar(ne['interior']['terceiros_2026'])} no interior"
            ),
            "votos_esperados": ne["interior"]["saldo_analogo_2026"]
            + ne["capitais"]["saldo_analogo_2026"],
            "regra": (
                "saldo líquido de Bolsonaro entre turnos em 2022 por voto de terceira "
                "via, aplicado ao voto de terceira via de 2026, separado em interior "
                "e capitais"
            ),
            "partes": {
                "interior": ne["interior"]["saldo_analogo_2026"],
                "capitais": ne["capitais"]["saldo_analogo_2026"],
            },
            "rotulo": "analogia histórica (uma eleição)",
        },
        {
            "id": "rj_ruas",
            "titulo": "Casar o 2º turno de Douglas Ruas com o de Flávio no Rio",
            "alvo": f"{milhar(rj_ruas['votos_governador_urna'])} votos de Douglas Ruas",
            "votos_esperados": rj_ruas["saldo_aplicado_a_urna"],
            "regra": (
                "votos de Ruas × saldo entre as perguntas de 1º e 2º turno no "
                f"eleitorado dele ({_entre(rj_ruas)})"
            ),
            "contraprova": rj_paes["saldo_aplicado_a_urna"],
            "rotulo": "inferência sobre medição publicada",
        },
        {
            "id": "direita_menor",
            "titulo": "Fechar Zema e as candidaturas menores da direita",
            "alvo": f"{milhar(sum(t['votos'] for t in zema_dir))} votos",
            "votos_esperados": sum(_saldo_central(arit, t["nome"]) for t in zema_dir),
            "regra": f"linha de Zema na Nexus ({_fl(nx, 'Zema')}) aplicada a Zema, DC e Democrata",
            "rotulo": "inferência sobre medição publicada",
        },
        {
            "id": "comparecimento",
            "titulo": "Um ponto a mais de comparecimento nas 15 UFs de Flávio",
            "alvo": "eleitor apto que faltou no 1º turno nas UFs que Flávio venceu",
            "votos_esperados": comp["valor_1pp_ufs_flavio"]["saldo_flavio"],
            "regra": "1% do eleitorado apto a mais, votando como a própria UF votou no 1º turno",
            "contraprova": comp["valor_1pp_ufs_lula"]["saldo_flavio"],
            "onde": comp["valor_1pp_ufs_flavio"]["ufs"][:5],
            "rotulo": "hipótese declarada",
        },
        {
            "id": "caiado_go",
            "titulo": "Disputar o eleitor de Caiado com Daniel Vilela em Goiás",
            "alvo": (
                f"{milhar(caiado['votos'])} votos de Caiado, "
                f"{milhar(caiado_go['votos'])} em Goiás"
            ),
            "votos_esperados": round((caiado_nx + caiado_df) / 2),
            "regra": (
                f"média das linhas Nexus ({_fl(nx, 'Caiado')}) e Datafolha "
                f"({_fl(dfo, 'Caiado')}) aplicadas aos votos de Caiado"
            ),
            "faixa": [min(caiado_nx, caiado_df), max(caiado_nx, caiado_df)],
            "governador_go": {
                "nome": go["nome"],
                "partido": go["partido"],
                "campo": go["campo"],
                "votos": go["votos"],
                "nota": next(
                    (
                        e["motivo"]
                        for e in fontes["voto_util"]["campo_excecao"]
                        if e["uf"] == "GO"
                        and set(sem_acento(e["nome"]).split())
                        <= set(sem_acento(go["nome"]).split())
                    ),
                    None,
                ),
            },
            "onde": votos_terceiros_por_uf(fontes, 55),
            "rotulo": "inferência sobre duas medições que discordam",
        },
    ]
    return E.ordenar_movimentos(movimentos)
