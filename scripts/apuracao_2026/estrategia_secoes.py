"""Seções do capítulo "O caminho do 2º turno", montadas a partir das fontes lidas.

Cada função recebe o dicionário ``fontes`` montado pelo script
``scripts/apuracao-2026-estrategia.py`` e devolve um bloco do JSON. Contas
elementares ficam em ``estrategia.py``; aqui só se cruzam fontes.
"""

from __future__ import annotations

from collections import defaultdict

from . import estrategia as E
from .estrategia_leitura import sem_acento

NUM_FLAVIO = 22
NUM_LULA = 13

# Linha da matriz aplicada a cada candidatura de terceira via. As cinco linhas
# publicadas pela Nexus (p. 79) cobrem Cury, Caiado, Renan, Zema e Samara.
# Candidaturas sem linha publicada recebem a linha da candidatura publicada do
# mesmo campo: esquerda (PSTU, PCB, PCO) usa Samara; direita (DC, Democrata)
# usa Zema. Juntas somam menos de 0,2% dos válidos.
LINHA_POR_NUMERO = {70: "Cury", 14: "Renan", 55: "Caiado", 30: "Zema", 80: "Samara"}
LINHA_POR_CAMPO = {
    "esquerda": "Samara",
    "centro-esquerda": "Samara",
    "centro": "Cury",
    "centro-direita": "Zema",
    "direita": "Zema",
}

# Governadores eleitos no 1º turno pelo campo da direita e da centro-direita
# que o capítulo trata como aliados possíveis. O nome confere a leitura.
ALIADOS = {
    "SP": "TARCÍSIO",
    "MG": "CLEITINHO",
    "AL": "JHC",
    "MS": "RIEDEL",
    "RS": "ZUCCO",
    "SC": "JORGINHO",
    "MT": "PIVETTA",
    "RO": "MARCOS ROGÉRIO",
    "RR": "ARTHUR HENRIQUE",
    "PB": "LUCAS RIBEIRO",
    "PA": "DR. DANIEL",
}

# Linhas de cruzamento governador × presidente publicadas pelo Datafolha no
# texto corrido dos relatórios estaduais (campo 08–10/09/2026), transcritas em
# docs/assets/datafolha_21092026_sudeste.json → cruzamentos_publicados.
LINHAS_DATAFOLHA = (
    ("SP", 4, "Tarcísio", "1t"),
    ("MG", 20, "Cleitinho", "1t"),
    ("MG", 21, "Cleitinho", "2t"),
    ("RJ", 12, "Douglas Ruas", "1t"),
    ("RJ", 13, "Douglas Ruas", "2t"),
    ("RJ", 12, "Eduardo Paes", "1t"),
    ("RJ", 13, "Eduardo Paes", "2t"),
)

UFS_2T_GOVERNADOR = ("AC", "AM", "DF", "ES", "RJ", "RN", "TO")
TOP_MUNICIPIOS = 20


def votos_numero(disputa: dict, numero: int) -> int:
    return next((c["votos"] for c in disputa["candidatos"] if c["numero"] == numero), 0)


def flavio_lula(disputa: dict) -> tuple[int, int]:
    return votos_numero(disputa, NUM_FLAVIO), votos_numero(disputa, NUM_LULA)


def a26_de(disputa: dict) -> dict:
    """Campos de 2026 usados por ``E.comparar_uf``."""
    f, lu = flavio_lula(disputa)
    return {
        "flavio": f,
        "lula": lu,
        "validos": disputa["validos"],
        "eleitores": disputa["eleitores"],
        "comparecimento": disputa["comparecimento"],
    }


def ufs_presidente(fontes: dict) -> list[str]:
    """As 27 UFs, sem BR e sem exterior, em ordem alfabética."""
    return sorted(uf for (uf, _m) in fontes["pres"] if uf not in ("BR", "ZZ"))


# ---------------------------------------------------------------- 1. aritmética


def matrizes(fontes: dict) -> dict:
    """Linhas Nexus (todas) e Datafolha (Cury e Caiado; resto herda a Nexus)."""
    tr = fontes["voto_util"]["nacional"]["transferencia"]
    nexus = {k: dict(v) for k, v in tr["linhas"].items()}
    df = fontes["datafolha"]["transfer"]
    poll = fontes["datafolha"]["poll"]
    campo = poll["campo"]
    destinos = df["destinations"]
    datafolha = dict(nexus)
    medidas = {}
    for nome, valores in df["measured_percentages"].items():
        linha = {}
        for dest, v in zip(destinos, valores, strict=True):
            chave = {"Lula": "Lula", "Flávio": "Flávio"}.get(dest, "Não escolha")
            linha[chave] = float(v)
        datafolha[nome] = linha
        medidas[nome] = linha
    return {
        "nexus": {
            "fonte": tr["fonte"],
            "arquivo": "docs/assets/voto_util_092026.json → nacional.transferencia",
            "linhas_publicadas": nexus,
            "linhas": {k: E.normalizar_linha(v) for k, v in nexus.items()},
        },
        "datafolha": {
            "fonte": (
                f"Datafolha, {poll['registro_tse']}, campo {_data_br(campo['inicio'])} "
                f"a {_data_br(campo['fim'])}, p. {df['measured_page']}"
            ),
            "nota": "linhas medidas para Cury e Caiado; as demais vêm da Nexus",
            "arquivo": "docs/assets/datafolha_21092026_data.json → transfer",
            "linhas_publicadas": medidas,
            "linhas": {k: E.normalizar_linha(v) for k, v in datafolha.items()},
        },
    }


def _data_br(iso: str) -> str:
    a, m, d = iso.split("-")
    return f"{d}/{m}/{a}"


def terceiros_nacionais(br: dict) -> list[dict]:
    """Candidaturas fora do par do 2º turno, com a linha de matriz aplicada."""
    saida = []
    for c in br["candidatos"]:
        if c["numero"] in (NUM_FLAVIO, NUM_LULA):
            continue
        linha = LINHA_POR_NUMERO.get(c["numero"]) or LINHA_POR_CAMPO[c["campo"]]
        saida.append(
            {
                "nome": c["nome"],
                "numero": c["numero"],
                "partido": c["partido"],
                "campo": c["campo"],
                "votos": c["votos"],
                "pct": E.r2(E.pct(c["votos"], br["validos"])),
                "linha": linha,
                "linha_propria": c["numero"] in LINHA_POR_NUMERO,
            }
        )
    return saida


def secao_aritmetica(fontes: dict) -> dict:
    br = fontes["pres"][("BR", "")]
    f1, l1 = flavio_lula(br)
    terceiros = terceiros_nacionais(br)
    pool = sum(t["votos"] for t in terceiros)
    origens = {t["nome"]: t["votos"] for t in terceiros}
    mats = matrizes(fontes)
    projecoes = []
    for chave, mat in mats.items():
        linhas = {t["nome"]: mat["linhas"][t["linha"]] for t in terceiros}
        for hip in E.HIPOTESES:
            p = E.projetar(f1, l1, origens, linhas, hip)
            p["matriz"] = chave
            projecoes.append(p)
    central = next(
        p for p in projecoes if p["matriz"] == "nexus" and p["hipotese"] == "fica_fora"
    )
    diferenca = f1 - l1
    escolhem = central["ganho_flavio"] + central["ganho_lula"]
    toda_para_lula = {}
    for chave in mats:
        p = next(
            x
            for x in projecoes
            if x["matriz"] == chave and x["hipotese"] == "fica_fora"
        )
        fora = sum(d["fora"] for d in p["detalhe"])
        toda_para_lula[chave] = {
            "nao_escolha_votos": fora,
            "margem_flavio_se_toda_for_lula": p["margem_votos"] - fora,
        }
    eq_todos = E.equilibrio(diferenca, pool)
    eq_medido = E.equilibrio(diferenca, escolhem)
    novos = []
    for p in projecoes:
        linha = {"matriz": p["matriz"], "hipotese": p["hipotese"]}
        for s in (0.55, 0.60, 0.65, 0.70):
            n = E.eleitores_novos_para_empatar(p["margem_votos"], s)
            linha[f"lula_{round(s * 100)}"] = None if n is None else round(n)
        novos.append(linha)
    t22 = fontes["api22"]["BR"]
    analogo_uf = analogo_2022_por_uf(fontes)
    nac = E.analogo_2022(
        f1,
        l1,
        pool,
        {
            "bolsonaro_1t": t22[1]["bolsonaro"],
            "bolsonaro_2t": t22[2]["bolsonaro"],
            "lula_1t": t22[1]["lula"],
            "lula_2t": t22[2]["lula"],
            "terceiros_1t": t22[1]["terceiros"],
        },
    )
    return {
        "primeiro_turno": {
            "eleitores": br["eleitores"],
            "comparecimento": br["comparecimento"],
            "comparecimento_pct": E.r2(E.pct(br["comparecimento"], br["eleitores"])),
            "abstencao": br["abstencao"],
            "abstencao_pct": E.r2(E.pct(br["abstencao"], br["eleitores"])),
            "validos": br["validos"],
            "brancos": br["brancos"],
            "nulos": br["nulos"],
            "brancos_nulos_pct_comparecimento": E.r2(
                E.pct(br["brancos"] + br["nulos"], br["comparecimento"])
            ),
            "flavio": f1,
            "flavio_pct": E.r2(E.pct(f1, br["validos"])),
            "lula": l1,
            "lula_pct": E.r2(E.pct(l1, br["validos"])),
            "diferenca_votos": diferenca,
            "diferenca_pp": E.r2(E.pct(diferenca, br["validos"])),
            "terceiros": terceiros,
            "terceiros_total": pool,
            "terceiros_pct": E.r2(E.pct(pool, br["validos"])),
            "snapshot_id": br["snapshot_id"],
            "capturado_em": br["capturado_em"],
            "gerado_em_tse": br["gerado_em"],
            "secoes_totalizadas": br["secoes_totalizadas"],
            "secoes": br["secoes"],
        },
        "matrizes": mats,
        "hipoteses": E.HIPOTESES,
        "projecoes": projecoes,
        "equilibrio": {
            "diferenca_1t": diferenca,
            "lula_precisa_se_todos_votarem_pct": E.r2(100 * (eq_todos or 0)),
            "lula_precisa_entre_quem_escolhe_pct": E.r2(100 * (eq_medido or 0)),
            "terceiros_que_escolhem_nexus": escolhem,
            "terceiros_que_escolhem_nexus_pct": E.r2(E.pct(escolhem, pool)),
            "lula_medido_entre_quem_escolhe_pct": E.r2(
                E.pct(central["ganho_lula"], escolhem)
            ),
            "saldo_que_lula_precisa_tirar_votos": diferenca,
            "saldo_que_lula_precisa_pct_terceiros": E.r2(E.pct(diferenca, pool)),
            "eleitores_novos_para_empatar": novos,
            "abstencao_1t": br["abstencao"],
            "nao_escolha_toda_para_lula": toda_para_lula,
            "base_flavio_trocando_para_lula_pct": E.r2(
                E.pct(central["margem_votos"], 2 * f1)
            ),
            "base_flavio_abstendo_pct": E.r2(E.pct(central["margem_votos"], f1)),
        },
        "analogo_2022": {
            "nacional": {
                "taxa_flavio": round(nac["taxa_flavio"], 4),
                "taxa_lula": round(nac["taxa_lula"], 4),
                "flavio": round(nac["flavio"]),
                "lula": round(nac["lula"]),
                "flavio_pct": E.r2(E.pct(nac["flavio"], nac["flavio"] + nac["lula"])),
                "margem_votos": round(nac["flavio"] - nac["lula"]),
            },
            "por_uf": analogo_uf,
            "entre_turnos_2022": {
                **E.variacao_comparecimento_2022(t22[1], t22[2]),
                "brancos_nulos_1t": t22[1]["brancos"] + t22[1]["nulos"],
                "brancos_nulos_2t": t22[2]["brancos"] + t22[2]["nulos"],
                "terceiros_1t": t22[1]["terceiros"],
                "diferenca_1t": t22[1]["lula"] - t22[1]["bolsonaro"],
                "diferenca_2t": t22[2]["lula"] - t22[2]["bolsonaro"],
                "arquivos": [t22[1]["arquivo"], t22[2]["arquivo"]],
            },
        },
    }


def analogo_2022_por_uf(fontes: dict) -> dict:
    """Analogia de 2022 aplicada UF a UF (e exterior), somada no país."""
    flavio = lula = 0.0
    linhas = []
    for (uf, _m), dis in fontes["pres"].items():
        if uf == "BR":
            continue
        f1, l1 = flavio_lula(dis)
        t26 = dis["validos"] - f1 - l1
        t22 = fontes["api22"][uf]
        a = E.analogo_2022(
            f1,
            l1,
            t26,
            {
                "bolsonaro_1t": t22[1]["bolsonaro"],
                "bolsonaro_2t": t22[2]["bolsonaro"],
                "lula_1t": t22[1]["lula"],
                "lula_2t": t22[2]["lula"],
                "terceiros_1t": t22[1]["terceiros"],
            },
        )
        flavio += a["flavio"]
        lula += a["lula"]
        linhas.append(
            {
                "uf": uf,
                "taxa_flavio": round(a["taxa_flavio"], 4),
                "taxa_lula": round(a["taxa_lula"], 4),
                "saldo_flavio": round(
                    (a["flavio"] - f1) - (a["lula"] - l1),
                ),
            }
        )
    linhas.sort(key=lambda x: -x["saldo_flavio"])
    return {
        "flavio": round(flavio),
        "lula": round(lula),
        "flavio_pct": E.r2(E.pct(flavio, flavio + lula)),
        "margem_votos": round(flavio - lula),
        "ufs": linhas,
    }


# ---------------------------------------------------------------- 2. geografia


def comparacoes_uf(fontes: dict) -> dict[str, dict]:
    saida = {}
    for (uf, _m), dis in fontes["pres"].items():
        if uf == "BR":
            continue
        t22 = fontes["api22"][uf]
        saida[uf] = E.comparar_uf(uf, a26_de(dis), t22[1], t22[2])
    return saida


def _agregar(fontes: dict, ufs: list[str], rotulo: str) -> dict:
    a26 = E.somar(
        (a26_de(fontes["pres"][(u, "")]) for u in ufs),
        ("flavio", "lula", "validos", "eleitores", "comparecimento"),
    )
    campos22 = (
        "bolsonaro",
        "lula",
        "validos",
        "eleitores",
        "comparecimento",
        "terceiros",
    )
    b1 = E.somar((fontes["api22"][u][1] for u in ufs), campos22)
    b2 = E.somar((fontes["api22"][u][2] for u in ufs), campos22)
    linha = E.comparar_uf(rotulo, a26, b1, b2)
    linha["ufs"] = ufs
    return linha


def municipios(fontes: dict) -> tuple[list[dict], dict]:
    """Comparação município a município (sem exterior), com o que ficou de fora."""
    linhas = []
    sem_2022 = []
    incompletos = 0
    for chave, dis in fontes["pres_mu"].items():
        uf, cd = chave
        if uf == "ZZ":
            continue
        meta = fontes["meta"].get(chave, {})
        r = fontes["mun22"].get(chave)
        if r is None:
            sem_2022.append({"uf": uf, "municipio": meta.get("nome"), "codigo_tse": cd})
            continue
        if dis["secoes_totalizadas"] < dis["secoes"]:
            incompletos += 1
        f, lu = flavio_lula(dis)
        vv = dis["validos"]
        v2 = r["bolsonaro_2t"] + r["lula_2t"]
        fp, b2p = E.pct(f, vv), E.pct(r["bolsonaro_2t"], v2)
        linhas.append(
            {
                "uf": uf,
                "codigo_tse": cd,
                "municipio": meta.get("nome", r["nome"]),
                "capital": meta.get("capital", False),
                "flavio": f,
                "lula": lu,
                "validos": vv,
                "flavio_pct": E.r2(fp),
                "lula_pct": E.r2(E.pct(lu, vv)),
                "bolsonaro_2022_1t": r["bolsonaro_1t"],
                "lula_2022_1t": r["lula_1t"],
                "validos_2022_1t": r["validos_1t"],
                "bolsonaro_2022_2t": r["bolsonaro_2t"],
                "lula_2022_2t": r["lula_2t"],
                "bolsonaro_2022_1t_pct": E.r2(
                    E.pct(r["bolsonaro_1t"], r["validos_1t"])
                ),
                "lula_2022_1t_pct": E.r2(E.pct(r["lula_1t"], r["validos_1t"])),
                "bolsonaro_2022_2t_pct": E.r2(b2p),
                "estoque_flavio": round(E.estoque(r["bolsonaro_2t"], b2p, fp)),
            }
        )
    return linhas, {"sem_2022": sem_2022, "arquivos_incompletos": incompletos}


def _resumo_mun(m: dict) -> dict:
    chaves = (
        "uf",
        "municipio",
        "capital",
        "flavio",
        "flavio_pct",
        "lula",
        "lula_pct",
        "bolsonaro_2022_1t_pct",
        "bolsonaro_2022_2t",
        "bolsonaro_2022_2t_pct",
        "lula_2022_1t",
        "lula_2022_1t_pct",
        "estoque_flavio",
    )
    return {k: m[k] for k in chaves}


def secao_geografia(fontes: dict) -> dict:
    comp = comparacoes_uf(fontes)
    ufs = ufs_presidente(fontes)
    regioes = {}
    for reg in E.REGIOES:
        membros = [u for u in ufs if E.regiao_de(u) == reg]
        linha = _agregar(fontes, membros, reg)
        linha["estoque_flavio_soma_ufs"] = sum(
            comp[u]["estoque_flavio"] for u in membros
        )
        linha["estoque_lula_soma_ufs"] = sum(comp[u]["estoque_lula"] for u in membros)
        regioes[reg] = linha
    brasil = _agregar(fontes, ufs, "Brasil sem exterior")
    lista = [comp[u] for u in ufs]
    acima = sorted(
        (c for c in lista if c["ja_supera_bolsonaro_2t"]),
        key=lambda c: -c["flavio_menos_bolsonaro_2t_pp"],
    )
    abaixo = sorted(
        (c for c in lista if not c["ja_supera_bolsonaro_2t"]),
        key=lambda c: c["flavio_menos_bolsonaro_2t_pp"],
    )
    por_estoque = sorted(lista, key=lambda c: -c["estoque_flavio"])
    est_total = sum(c["estoque_flavio"] for c in lista)
    mun, fora = municipios(fontes)
    mun_est = sorted(mun, key=lambda m: -m["estoque_flavio"])
    est_mun_total = sum(m["estoque_flavio"] for m in mun)
    est_capitais = sum(m["estoque_flavio"] for m in mun if m["capital"])
    return {
        "metodo_estoque": (
            "Estoque de Flávio = votos de Bolsonaro no 2º turno de 2022 × "
            "max(0; 1 − parcela de Flávio nos válidos do 1º turno de 2026 ÷ "
            "parcela de Bolsonaro nos válidos do 2º turno de 2022), por UF e por "
            "município. Mede, na escala do voto de 2022, a distância de parcela "
            "que falta. Não identifica eleitor; onde Flávio já passou de "
            "Bolsonaro o estoque é zero e o excedente não compensa outro lugar, "
            "por isso a soma municipal é maior que a estadual. O mesmo cálculo "
            "com Lula de 2022 dá o estoque de Lula."
        ),
        "ufs": sorted(lista, key=lambda c: c["uf"]),
        "exterior": comp["ZZ"],
        "regioes": regioes,
        "brasil_sem_exterior": brasil,
        "ja_supera_bolsonaro_2t": [c["uf"] for c in acima],
        "abaixo_de_bolsonaro_2t": [c["uf"] for c in abaixo],
        "estoque": {
            "total_ufs": est_total,
            "total_lula_ufs": sum(c["estoque_lula"] for c in lista),
            "top_ufs": [
                {
                    k: c[k]
                    for k in (
                        "uf",
                        "regiao",
                        "estoque_flavio",
                        "flavio_pct",
                        "bolsonaro_2022_2t_pct",
                        "bolsonaro_2022_2t",
                        "flavio_menos_bolsonaro_2t_votos",
                    )
                }
                for c in por_estoque[:10]
            ],
            "top5_ufs_parcela_pct": E.r2(
                E.pct(sum(c["estoque_flavio"] for c in por_estoque[:5]), est_total)
            ),
            "total_municipios": est_mun_total,
            "capitais": est_capitais,
            "capitais_pct": E.r2(E.pct(est_capitais, est_mun_total)),
            "municipios_com_estoque": sum(1 for m in mun if m["estoque_flavio"] > 0),
            "municipios_comparados": len(mun),
            "top_municipios": [_resumo_mun(m) for m in mun_est[:TOP_MUNICIPIOS]],
            "top20_municipios_parcela_pct": E.r2(
                E.pct(
                    sum(m["estoque_flavio"] for m in mun_est[:TOP_MUNICIPIOS]),
                    est_mun_total,
                )
            ),
            "fora_da_conta": fora,
        },
        "nordeste": secao_nordeste(fontes, comp, mun),
        "terceiros_por_regiao": terceiros_por_regiao(fontes),
        "_municipios": mun,
    }


def terceiros_por_regiao(fontes: dict) -> dict:
    """Parcela de cada candidatura de terceira via (votos) em cada região."""
    saida = {}
    for numero, rotulo in sorted(LINHA_POR_NUMERO.items()):
        por_reg: dict[str, int] = dict.fromkeys((*E.REGIOES, "Exterior"), 0)
        for (uf, _m), dis in fontes["pres"].items():
            if uf == "BR":
                continue
            por_reg[E.regiao_de(uf)] += votos_numero(dis, numero)
        total = sum(por_reg.values())
        saida[rotulo] = {
            "votos": por_reg,
            "pct": {r: E.r2(E.pct(v, total)) for r, v in por_reg.items()},
        }
    return saida


def secao_nordeste(fontes: dict, comp: dict, mun: list[dict]) -> dict:
    ne = [m for m in mun if m["uf"] in E.NORDESTE]
    grupos = {}
    campos = (
        "flavio",
        "lula",
        "validos",
        "bolsonaro_2022_1t",
        "lula_2022_1t",
        "validos_2022_1t",
        "bolsonaro_2022_2t",
        "lula_2022_2t",
        "estoque_flavio",
    )
    for rotulo, filtro in (("capitais", True), ("interior", False)):
        s = E.somar((m for m in ne if m["capital"] is filtro), campos)
        v2 = s["bolsonaro_2022_2t"] + s["lula_2022_2t"]
        grupos[rotulo] = {
            **s,
            "municipios": sum(1 for m in ne if m["capital"] is filtro),
            "flavio_pct": E.r2(E.pct(s["flavio"], s["validos"])),
            "lula_pct": E.r2(E.pct(s["lula"], s["validos"])),
            "bolsonaro_2022_1t_pct": E.r2(
                E.pct(s["bolsonaro_2022_1t"], s["validos_2022_1t"])
            ),
            "lula_2022_1t_pct": E.r2(E.pct(s["lula_2022_1t"], s["validos_2022_1t"])),
            "bolsonaro_2022_2t_pct": E.r2(E.pct(s["bolsonaro_2022_2t"], v2)),
            "lula_2022_2t_pct": E.r2(E.pct(s["lula_2022_2t"], v2)),
            "terceiros_2026": s["validos"] - s["flavio"] - s["lula"],
            "terceiros_2022_1t": s["validos_2022_1t"]
            - s["bolsonaro_2022_1t"]
            - s["lula_2022_1t"],
        }
        g = grupos[rotulo]
        g["flavio_menos_bolsonaro_1t_pp"] = E.r2(
            g["flavio_pct"] - g["bolsonaro_2022_1t_pct"]
        )
        g["lula_menos_lula_2022_1t_pp"] = E.r2(g["lula_pct"] - g["lula_2022_1t_pct"])
        g["lula_menos_lula_2022_1t_votos"] = s["lula"] - s["lula_2022_1t"]
        g["flavio_menos_bolsonaro_1t_votos"] = s["flavio"] - s["bolsonaro_2022_1t"]
        # Analogia de 2022 dentro do grupo: saldo líquido de Bolsonaro entre
        # turnos por voto de terceira via no 1º turno, aplicado ao de 2026.
        ganho_b = s["bolsonaro_2022_2t"] - s["bolsonaro_2022_1t"]
        ganho_l = s["lula_2022_2t"] - s["lula_2022_1t"]
        g["saldo_bolsonaro_entre_turnos_2022"] = ganho_b - ganho_l
        taxa = (
            (ganho_b - ganho_l) / g["terceiros_2022_1t"]
            if g["terceiros_2022_1t"]
            else 0
        )
        g["taxa_saldo_2022_por_terceiro"] = round(taxa, 4)
        g["saldo_analogo_2026"] = round(taxa * g["terceiros_2026"])
    capitais = sorted(
        (_resumo_mun(m) for m in ne if m["capital"]),
        key=lambda m: -m["estoque_flavio"],
    )
    queda_lula = sorted(
        ne, key=lambda m: m["lula"] - m["lula_2022_1t"]
    )  # mais negativo primeiro
    ganho_flavio = sorted(ne, key=lambda m: -(m["flavio"] - m["bolsonaro_2022_1t"]))
    ufs = sorted(
        (comp[u] for u in E.NORDESTE),
        key=lambda c: c["lula_menos_lula_2022_1t_pp"],
    )
    return {
        "capitais_x_interior": grupos,
        "capitais": capitais,
        "ufs_queda_lula": [
            {
                k: c[k]
                for k in (
                    "uf",
                    "lula_pct",
                    "lula_2022_1t_pct",
                    "lula_menos_lula_2022_1t_pp",
                    "lula_menos_lula_2022_1t_votos",
                    "flavio_pct",
                    "bolsonaro_2022_1t_pct",
                    "flavio_menos_bolsonaro_1t_pp",
                    "ja_supera_bolsonaro_2t",
                )
            }
            for c in ufs
        ],
        "municipios_queda_lula_votos": [
            {
                "uf": m["uf"],
                "municipio": m["municipio"],
                "capital": m["capital"],
                "lula": m["lula"],
                "lula_2022_1t": m["lula_2022_1t"],
                "variacao_votos": m["lula"] - m["lula_2022_1t"],
                "lula_pct": m["lula_pct"],
                "lula_2022_1t_pct": m["lula_2022_1t_pct"],
            }
            for m in queda_lula[:10]
        ],
        "municipios_ganho_flavio_votos": [
            {
                "uf": m["uf"],
                "municipio": m["municipio"],
                "capital": m["capital"],
                "flavio": m["flavio"],
                "bolsonaro_2022_1t": m["bolsonaro_2022_1t"],
                "variacao_votos": m["flavio"] - m["bolsonaro_2022_1t"],
                "flavio_pct": m["flavio_pct"],
                "bolsonaro_2022_1t_pct": m["bolsonaro_2022_1t_pct"],
            }
            for m in ganho_flavio[:10]
        ],
    }


# ---------------------------------------------------------------- 3. governadores


def linha_datafolha(sudeste: dict, uf: str, pagina: int, origem: str) -> dict | None:
    """Linha publicada governador → presidente, com rótulos curtos Flávio e Lula."""
    for bloco in sudeste["cruzamentos_publicados"]:
        if bloco["uf"] != uf or bloco["pagina"] != pagina:
            continue
        for nome, valores in bloco["linhas"].items():
            if not sem_acento(nome).startswith(sem_acento(origem)):
                continue
            saida = {"origem": nome, "pagina": pagina, "pdf": bloco["pdf"]}
            saida["destino_pergunta"] = bloco["destino_pergunta"]
            for dest, v in valores.items():
                if dest.startswith("Flavio"):
                    saida["Flávio"] = v
                elif dest.startswith("Lula"):
                    saida["Lula"] = v
                else:
                    saida[dest] = v
            return saida
    return None


def governador_eleito(dis: dict) -> dict:
    return dis["candidatos"][0]


def _alinhado(alinhados: dict[str, dict], uf: str, nome_urna: str) -> bool:
    """Candidatura marcada como aliada de Lula na exceção de campo da casa.

    Casa quando todas as palavras do nome da exceção aparecem no nome de urna,
    sempre na mesma UF ("RICARDO FERRAÇO", "OMAR AZIZ", "LUCAS RIBEIRO").
    """
    alvo = set(sem_acento(nome_urna).split())
    return any(v["uf"] == uf and set(k.split()) <= alvo for k, v in alinhados.items())


def lado(campo: str, alinhado_lula: bool) -> str:
    """Lado na disputa nacional: campo de Lula, campo de Flávio ou centro."""
    if alinhado_lula or campo in ("esquerda", "centro-esquerda"):
        return "lula"
    if campo in ("direita", "centro-direita"):
        return "flavio"
    return "centro"


def alinhados_lula(voto_util: dict) -> dict[str, dict]:
    return {
        sem_acento(e["nome"]): e
        for e in voto_util["campo_excecao"]
        if e["alinhado_lula"]
    }


def secao_governadores(fontes: dict) -> dict:
    alinhados = alinhados_lula(fontes["voto_util"])
    aliados = []
    for uf, esperado in ALIADOS.items():
        gdis = fontes["gov"][(uf, "")]
        pdis = fontes["pres"][(uf, "")]
        gov = governador_eleito(gdis)
        if esperado not in gov["nome"] and sem_acento(esperado) not in sem_acento(
            gov["nome"]
        ):
            raise ValueError(f"{uf}: esperado {esperado}, banco traz {gov['nome']}")
        f, lu = flavio_lula(pdis)
        aliado = next(
            (
                v
                for k, v in alinhados.items()
                if v["uf"] == uf and _alinhado({k: v}, uf, gov["nome"])
            ),
            None,
        )
        top, n_acima, soma_acima = municipios_governador(fontes, uf, gov["sqcand"])
        aliados.append(
            {
                "uf": uf,
                "governador": gov["nome"],
                "partido": gov["partido"],
                "campo": gov["campo"],
                "st_tse": gov["st"],
                "alinhado_lula": aliado is not None,
                "nota_alinhamento": aliado["motivo"] if aliado else None,
                "governador_votos": gov["votos"],
                "governador_pct": E.r2(E.pct(gov["votos"], gdis["validos"])),
                "validos_governador": gdis["validos"],
                "flavio_votos": f,
                "flavio_pct": E.r2(E.pct(f, pdis["validos"])),
                "lula_votos": lu,
                "lula_pct": E.r2(E.pct(lu, pdis["validos"])),
                "validos_presidente": pdis["validos"],
                "flavio_venceu_uf": f > lu,
                **E.vao(gov["votos"], gdis["validos"], f, pdis["validos"]),
                "municipios_governador_acima": n_acima,
                "soma_vao_municipal_positivo": soma_acima,
                "top_municipios": top,
            }
        )
    aliados.sort(key=lambda a: -a["vao_votos"])
    linhas = []
    for uf, pagina, origem, turno in LINHAS_DATAFOLHA:
        ln = linha_datafolha(fontes["sudeste"], uf, pagina, origem)
        if ln is None:
            continue
        ln.update({"uf": uf, "turno": turno})
        linhas.append(ln)
    return {
        "nota": (
            "Vão = votos do governador eleito menos votos de Flávio na mesma UF e "
            "na mesma urna. Teto endereçável, nunca transferência certa: parte do "
            "eleitorado do governador vota Lula por escolha medida."
        ),
        "aliados": aliados,
        "linhas_datafolha": linhas,
        "consolidacao_medida": consolidacao_medida(fontes, linhas),
        "segundo_turno_estadual": segundo_turno_estadual(fontes),
        "campo_linhas": fontes["sudeste"]["meta"]["campo_estadual"],
        "paginas_linhas": {
            uf: sorted({ln["pagina"] for ln in linhas if ln["uf"] == uf})
            for uf in sorted({ln["uf"] for ln in linhas})
        },
        "arquivo_linhas": "docs/assets/datafolha_21092026_sudeste.json",
    }


def municipios_governador(
    fontes: dict, uf: str, sq_gov: str
) -> tuple[list[dict], int, int]:
    """Municípios onde o governador mais superou Flávio em votos."""
    linhas = []
    for (u, cd), gdis in fontes["gov_mu"].items():
        if u != uf:
            continue
        pdis = fontes["pres_mu"].get((u, cd))
        if pdis is None:
            continue
        g = next((c["votos"] for c in gdis["candidatos"] if c["sqcand"] == sq_gov), 0)
        f, _lu = flavio_lula(pdis)
        linhas.append(
            {
                "municipio": fontes["meta"].get((u, cd), {}).get("nome", cd),
                "capital": fontes["meta"].get((u, cd), {}).get("capital", False),
                "governador": g,
                "flavio": f,
                "vao_votos": g - f,
                "governador_pct": E.r2(E.pct(g, gdis["validos"])),
                "flavio_pct": E.r2(E.pct(f, pdis["validos"])),
            }
        )
    linhas.sort(key=lambda x: -x["vao_votos"])
    acima = [x for x in linhas if x["vao_votos"] > 0]
    return linhas[:5], len(acima), sum(x["vao_votos"] for x in acima)


def consolidacao_medida(fontes: dict, linhas: list[dict]) -> list[dict]:
    """Saldo entre as perguntas de 1º e 2º turno no eleitorado do governador."""
    saida = []
    por_chave = {(ln["uf"], ln["origem"], ln["turno"]): ln for ln in linhas}
    votos_gov = {}
    for (uf, _m), dis in fontes["gov"].items():
        for c in dis["candidatos"]:
            votos_gov[(uf, sem_acento(c["nome"]))] = c["votos"]
    for (uf, origem, turno), l1 in por_chave.items():
        if turno != "1t":
            continue
        l2 = por_chave.get((uf, origem, "2t"))
        if l2 is None:
            continue
        nome = sem_acento(origem.split(" (")[0])
        votos = next(
            (
                v
                for (u, n), v in votos_gov.items()
                if u == uf and (n == nome or n.split()[0] == nome.split()[0])
            ),
            0,
        )
        taxa = E.consolidacao_entre_turnos(l1, l2)
        saida.append(
            {
                "uf": uf,
                "origem": origem,
                "linha_1t": {"Flávio": l1["Flávio"], "Lula": l1["Lula"]},
                "linha_2t": {"Flávio": l2["Flávio"], "Lula": l2["Lula"]},
                "paginas": [l1["pagina"], l2["pagina"]],
                "saldo_flavio_pontos": round(100 * taxa, 2),
                "votos_governador_urna": votos,
                "saldo_aplicado_a_urna": round(taxa * votos),
                "lula_1t_aplicado_a_urna": round(l1["Lula"] / 100 * votos),
                "lula_2t_aplicado_a_urna": round(l2["Lula"] / 100 * votos),
            }
        )
    return saida


def segundo_turno_estadual(fontes: dict) -> list[dict]:
    alinhados = alinhados_lula(fontes["voto_util"])
    saida = []
    for uf in UFS_2T_GOVERNADOR:
        gdis = fontes["gov"][(uf, "")]
        pdis = fontes["pres"][(uf, "")]
        f, lu = flavio_lula(pdis)
        par = []
        for c in gdis["candidatos"][:2]:
            alinhado = _alinhado(alinhados, uf, c["nome"])
            par.append(
                {
                    "nome": c["nome"],
                    "partido": c["partido"],
                    "campo": c["campo"],
                    "votos": c["votos"],
                    "pct": E.r2(E.pct(c["votos"], gdis["validos"])),
                    "st_tse": c["st"],
                    "alinhado_lula": alinhado,
                    "lado": lado(c["campo"], alinhado),
                }
            )
        saida.append(
            {
                "uf": uf,
                "par": par,
                "tipo": "+".join(sorted({c["lado"] for c in par})),
                "eleitores": pdis["eleitores"],
                "abstencao_pct": E.r2(E.pct(pdis["abstencao"], pdis["eleitores"])),
                "flavio_pct": E.r2(E.pct(f, pdis["validos"])),
                "lula_pct": E.r2(E.pct(lu, pdis["validos"])),
                "margem_flavio_votos": f - lu,
            }
        )
    return saida


# ---------------------------------------------------------------- 4. Congresso


def secao_congresso(fontes: dict) -> dict:
    final = fontes["final"]
    cam = final["camara"]
    sen = final["senado"]
    pl_novos = sum(1 for u in sen["ufs"] for e in u["eleitos"] if e["partido"] == "PL")
    provisorios = {
        u["uf"]: {sem_acento(e["nome"]) for e in u["eleitos"]}
        for u in cam["ufs"]
        if u.get("fonte") == "provisorio"
    }
    deputados = []
    for (uf, _m), dis in sorted(fontes["dep"].items()):
        top = []
        for c in dis["candidatos"][:3]:
            st = c["st"]
            if st is None and uf in provisorios:
                st = (
                    "eleito na alocação provisória"
                    if sem_acento(c["nome"]) in provisorios[uf]
                    else "fora da alocação provisória"
                )
            top.append(
                {
                    "nome": c["nome"],
                    "partido": c["partido"],
                    "campo": c["campo"],
                    "votos": c["votos"],
                    "pct_validos_uf": E.r2(E.pct(c["votos"], dis["validos"])),
                    "st_tse": c["st"],
                    "situacao": st,
                }
            )
        ancora = next(
            (
                c
                for c in dis["candidatos"]
                if c["campo"] in ("direita", "centro-direita")
            ),
            None,
        )
        deputados.append(
            {
                "uf": uf,
                "top3": top,
                "ancora_direita": (
                    {
                        "nome": ancora["nome"],
                        "partido": ancora["partido"],
                        "votos": ancora["votos"],
                        "pct_validos_uf": E.r2(E.pct(ancora["votos"], dis["validos"])),
                    }
                    if ancora
                    else None
                ),
            }
        )
    senadores = []
    for u in sen["ufs"]:
        senadores.append(
            {
                "uf": u["uf"],
                "eleitos": [
                    {k: e[k] for k in ("nome", "partido", "campo", "votos", "pct")}
                    for e in u["eleitos"]
                ],
                "fonte": u["fonte"],
            }
        )
    return {
        "fonte": "apuracao/data/boletins/final.json",
        "fonte_gerado_em": final["gerado_em"],
        "camara": {
            "vagas": cam["vagas_total"],
            "blocos": cam["blocos"],
            "por_campo": cam["por_campo"],
            "por_partido": cam["por_partido"],
            "ufs_provisorias": cam.get("ufs_provisorias", []),
            "maioria_absoluta": E.maioria_absoluta(cam["vagas_total"]),
            "tres_quintos": E.tres_quintos(cam["vagas_total"]),
        },
        "senado_2027": {
            "total": sen["senado_2027"]["total"],
            "por_bloco": sen["senado_2027"]["por_bloco"],
            "por_partido": sen["senado_2027"]["por_partido"],
            "pl_eleitos_2026": pl_novos,
            "maioria_absoluta": E.maioria_absoluta(sen["senado_2027"]["total"]),
            "tres_quintos": E.tres_quintos(sen["senado_2027"]["total"]),
        },
        "deputados_federais_top3": deputados,
        "senadores_eleitos_2026": senadores,
    }


def votos_terceiros_por_uf(fontes: dict, numero: int, n: int = 5) -> list[dict]:
    """UFs com mais votos de uma candidatura de terceira via."""
    linhas = []
    for (uf, _m), dis in fontes["pres"].items():
        if uf == "BR":
            continue
        v = votos_numero(dis, numero)
        linhas.append({"uf": uf, "votos": v, "pct": E.r2(E.pct(v, dis["validos"]))})
    linhas.sort(key=lambda x: -x["votos"])
    return linhas[:n]


def regioes_de(ufs: list[str]) -> dict[str, list[str]]:
    saida = defaultdict(list)
    for u in ufs:
        saida[E.regiao_de(u)].append(u)
    return dict(saida)
