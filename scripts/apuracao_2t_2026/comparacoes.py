"""Comparações do 2º turno de 2026 com o 1º turno de 2026 e com o 2º turno de 2022."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable
from typing import Any

from .base import NOME_UF, ROTULO, colunar, d2, p2, resumo_distribuicao
from .carga import Contexto

REGIOES = ("Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul")


def _h2h(f: int | None, l_: int | None) -> float | None:
    """Parte de Flávio entre os dois finalistas, em %."""
    if f is None or l_ is None or f + l_ == 0:
        return None
    return p2(f, f + l_)


# ---------------------------------------------------------------- 1º turno


def _par_1t(m2: dict[str, Any], m1: dict[str, Any]) -> dict[str, Any]:
    f1, l1, v1 = m1["flavio"], m1["lula"], m1["validos"]
    pa1 = p2(m1["abstencao"], m1["eleitores"])
    pc1 = p2(m1["comparecimento"], m1["eleitores"])
    terceiros1 = v1 - f1 - l1
    df, dl = m2["flavio"] - f1, m2["lula"] - l1
    return {
        "cd_tse": m2.get("cd_tse"),
        "uf": m2["uf"],
        "nome": m2.get("nome"),
        "capital": m2.get("capital"),
        "regiao": m2.get("regiao"),
        "aptos": m2["aptos"],
        "completo": m2.get("completo", True),
        "t2_flavio": m2["flavio"],
        "t2_lula": m2["lula"],
        "t2_validos": m2["validos"],
        "t2_pct_flavio": m2["pct_flavio"],
        "t2_pct_lula": m2["pct_lula"],
        "t1_flavio": f1,
        "t1_lula": l1,
        "t1_validos": v1,
        "t1_terceiros": terceiros1,
        "t1_pct_flavio": p2(f1, v1),
        "t1_pct_lula": p2(l1, v1),
        "delta_votos_flavio": df,
        "delta_votos_lula": dl,
        "delta_fatia_flavio_pp": d2(m2["pct_flavio"], p2(f1, v1)),
        "delta_fatia_lula_pp": d2(m2["pct_lula"], p2(l1, v1)),
        "t1_h2h_flavio": _h2h(f1, l1),
        "t2_h2h_flavio": _h2h(m2["flavio"], m2["lula"]),
        "swing_h2h_flavio_pp": d2(_h2h(m2["flavio"], m2["lula"]), _h2h(f1, l1)),
        "ganho_flavio_sobre_terceiros_pct": p2(df, terceiros1),
        "ganho_lula_sobre_terceiros_pct": p2(dl, terceiros1),
        "t2_pct_comparecimento": m2["pct_comparecimento"],
        "t1_pct_comparecimento": pc1,
        "delta_comparecimento_pp": d2(m2["pct_comparecimento"], pc1),
        "t2_pct_abstencao": m2["pct_abstencao"],
        "t1_pct_abstencao": pa1,
        "delta_abstencao_pp": d2(m2["pct_abstencao"], pa1),
        "delta_comparecimento_votos": m2["comparecimento"] - m1["comparecimento"],
        "t2_validos_menos_t1": m2["validos"] - v1,
        "t1_aptos": m1["eleitores"],
        "t1_comparecimento": m1["comparecimento"],
        "t2_comparecimento": m2["comparecimento"],
    }


def _soma_1t(linhas: Iterable[dict[str, Any]]) -> dict[str, int]:
    chaves = ("eleitores", "comparecimento", "abstencao", "validos", "flavio", "lula")
    s: dict[str, int] = dict.fromkeys(chaves, 0)
    for r in linhas:
        for k in chaves:
            s[k] += r[k]
    return s


COLUNAS_PAR = (
    "cd_tse",
    "uf",
    "nome",
    "aptos",
    "t1_flavio",
    "t2_flavio",
    "delta_votos_flavio",
    "t1_pct_flavio",
    "t2_pct_flavio",
    "delta_fatia_flavio_pp",
    "t1_lula",
    "t2_lula",
    "delta_votos_lula",
    "t1_pct_lula",
    "t2_pct_lula",
    "delta_fatia_lula_pp",
    "t1_terceiros",
    "swing_h2h_flavio_pp",
    "delta_abstencao_pp",
)


def comparacao_1t(ctx: Contexto, municipios: list[dict[str, Any]]) -> dict[str, Any]:
    pares = []
    sem_1t = []
    for m in municipios:
        if m["uf"] == "ZZ":
            continue
        m1 = ctx.mun_1t.get(m["cd_tse"])
        if m1 is None:
            sem_1t.append(m["cd_tse"])
            continue
        pares.append(_par_1t(m, m1))
    completos = [p for p in pares if p["completo"]]

    def agregado(lista: list[dict[str, Any]], chave: str, valor: str) -> dict[str, Any]:
        m2 = {
            "uf": valor,
            "aptos": sum(p["aptos"] for p in lista),
            "flavio": sum(p["t2_flavio"] for p in lista),
            "lula": sum(p["t2_lula"] for p in lista),
            "validos": sum(p["t2_validos"] for p in lista),
        }
        m2["pct_flavio"] = p2(m2["flavio"], m2["validos"])
        m2["pct_lula"] = p2(m2["lula"], m2["validos"])
        mapa = {p["cd_tse"]: p for p in lista}
        muns2 = [m for m in municipios if m["cd_tse"] in mapa]
        comp2 = sum(m["comparecimento"] for m in muns2)
        abst2 = sum(m["abstencao"] for m in muns2)
        m2["comparecimento"] = comp2
        m2["pct_comparecimento"] = p2(comp2, comp2 + abst2)
        m2["pct_abstencao"] = p2(abst2, comp2 + abst2)
        m1 = _soma_1t(ctx.mun_1t[cd] for cd in mapa)
        par = _par_1t(m2, m1)
        par.pop("cd_tse")
        par["n_municipios"] = len(lista)
        par[chave] = valor
        return par

    por_uf: dict[str, list[dict[str, Any]]] = defaultdict(list)
    por_reg: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for p in completos:
        por_uf[p["uf"]].append(p)
        por_reg[p["regiao"]].append(p)
    ufs = [
        {"nome_uf": NOME_UF[uf], **agregado(lista, "uf", uf)}
        for uf, lista in sorted(por_uf.items())
    ]
    regioes = [agregado(por_reg[r], "regiao", r) for r in REGIOES if por_reg.get(r)]
    brasil = agregado(completos, "regiao", "Brasil (municípios completos)")

    def ordenar(chave: str, reverso: bool, filtro: Callable[[dict], bool]) -> list:
        lista = [p for p in completos if filtro(p)]
        return sorted(lista, key=lambda p: p[chave], reverse=reverso)

    f_ganhou = ordenar(
        "delta_votos_flavio", True, lambda p: p["delta_votos_flavio"] > 0
    )
    f_perdeu = ordenar(
        "delta_votos_flavio", False, lambda p: p["delta_votos_flavio"] < 0
    )
    l_ganhou = ordenar("delta_votos_lula", True, lambda p: p["delta_votos_lula"] > 0)
    l_perdeu = ordenar("delta_votos_lula", False, lambda p: p["delta_votos_lula"] < 0)
    absten_cai = sorted(
        (
            p
            for p in completos
            if p["aptos"] >= 5000
            and p["delta_abstencao_pp"] is not None
            and p["delta_abstencao_pp"] <= -5
        ),
        key=lambda p: p["delta_abstencao_pp"],
    )
    absten_sobe = sorted(
        (
            p
            for p in completos
            if p["aptos"] >= 5000
            and p["delta_abstencao_pp"] is not None
            and p["delta_abstencao_pp"] >= 5
        ),
        key=lambda p: -p["delta_abstencao_pp"],
    )
    pesos = [p["aptos"] for p in completos]

    def dist(chave: str) -> dict[str, Any]:
        vals = [(p[chave], p["aptos"]) for p in completos if p[chave] is not None]
        return resumo_distribuicao([v for v, _ in vals], [w for _, w in vals])

    return {
        "rotulo": ROTULO,
        "definicoes": {
            "fatias": "Flávio e Lula sobre os válidos de cada turno (1º turno com terceiros)",
            "h2h": (
                "t1_h2h_flavio e t2_h2h_flavio: parte de Flávio só entre os dois "
                "finalistas; swing_h2h_flavio_pp é a mudança dessa parte, a única "
                "comparável entre turnos com e sem terceiros"
            ),
            "ganho_sobre_terceiros": (
                "votos ganhos no 2º turno divididos pelos votos de terceiros do 1º "
                "turno no mesmo município; passa de 100% quando entra eleitor novo ou "
                "sai voto do adversário, e não identifica transferência individual"
            ),
            "abstencao": "sobre o eleitorado; 2º turno sobre as seções totalizadas",
            "comparecimento": (
                "t1_comparecimento e t2_comparecimento em eleitores; aptos é o "
                "eleitorado do 2º turno e t1_aptos, o do 1º"
            ),
            "base": "municípios com o arquivo presidencial completo nos dois turnos",
        },
        "brasil": brasil,
        "regioes": regioes,
        "ufs": ufs,
        "municipios": colunar(list(_par_1t_colunas()), pares),
        "n_municipios_completos": len(completos),
        "sem_1t": sem_1t,
        "flavio_ganhou_votos": {
            "n": len(f_ganhou),
            "lista": colunar(COLUNAS_PAR, f_ganhou),
        },
        "flavio_perdeu_votos": {
            "n": len(f_perdeu),
            "lista": colunar(COLUNAS_PAR, f_perdeu),
        },
        "flavio_maiores_perdas": f_perdeu[:30],
        "flavio_maiores_ganhos": f_ganhou[:30],
        "lula_ganhou_votos": {
            "n": len(l_ganhou),
            "lista": colunar(COLUNAS_PAR, l_ganhou),
        },
        "lula_perdeu_votos": {
            "n": len(l_perdeu),
            "lista": colunar(COLUNAS_PAR, l_perdeu),
        },
        "lula_maiores_perdas": l_perdeu[:30],
        "lula_maiores_ganhos": l_ganhou[:30],
        "dispersao_municipal": {
            "nota": "pesos = eleitorado do 2º turno; media_ponderada usa esses pesos",
            "swing_h2h_flavio_pp": dist("swing_h2h_flavio_pp"),
            "delta_fatia_flavio_pp": dist("delta_fatia_flavio_pp"),
            "delta_fatia_lula_pp": dist("delta_fatia_lula_pp"),
            "delta_abstencao_pp": dist("delta_abstencao_pp"),
            "ganho_flavio_sobre_terceiros_pct": dist(
                "ganho_flavio_sobre_terceiros_pct"
            ),
            "ganho_lula_sobre_terceiros_pct": dist("ganho_lula_sobre_terceiros_pct"),
            "n_swing_h2h_pro_flavio": sum(
                1 for p in completos if (p["swing_h2h_flavio_pp"] or 0) > 0
            ),
            "n_swing_h2h_pro_lula": sum(
                1 for p in completos if (p["swing_h2h_flavio_pp"] or 0) < 0
            ),
            "pesos_total": sum(pesos),
        },
        "abstencao_caiu_5pp": {
            "criterio": "delta_abstencao_pp <= -5 e eleitorado >= 5.000",
            "n": len(absten_cai),
            "lista": colunar(COLUNAS_PAR, absten_cai),
        },
        "abstencao_subiu_5pp": {
            "criterio": "delta_abstencao_pp >= 5 e eleitorado >= 5.000",
            "n": len(absten_sobe),
            "lista": colunar(COLUNAS_PAR, absten_sobe),
        },
    }


def _par_1t_colunas() -> tuple[str, ...]:
    exemplo = _par_1t(
        {
            "uf": "",
            "aptos": 0,
            "flavio": 0,
            "lula": 0,
            "validos": 0,
            "pct_flavio": None,
            "pct_lula": None,
            "pct_comparecimento": None,
            "pct_abstencao": None,
            "comparecimento": 0,
        },
        {
            "flavio": 0,
            "lula": 0,
            "validos": 0,
            "abstencao": 0,
            "eleitores": 0,
            "comparecimento": 0,
        },
    )
    return tuple(exemplo)


# ---------------------------------------------------------------- 2022


def _par_2022(m: dict[str, Any], r22: dict[str, Any]) -> dict[str, Any]:
    b, l22, v22 = r22["bolsonaro"], r22["lula"], r22["validos"]
    apt22, comp22, abs22 = (
        r22.get("aptos"),
        r22.get("comparecimento"),
        r22.get("abstencao"),
    )
    pa22 = p2(abs22, apt22)
    pb, pl = p2(b, v22), p2(l22, v22)
    vencedor22 = "lula" if l22 > b else "bolsonaro" if b > l22 else "empate"
    vencedor26 = (
        "lula"
        if m["lula"] > m["flavio"]
        else "flavio" if m["flavio"] > m["lula"] else "empate"
    )
    return {
        "cd_tse": m.get("cd_tse"),
        "uf": m["uf"],
        "nome": m.get("nome"),
        "regiao": m.get("regiao"),
        "aptos": m["aptos"],
        "completo": m.get("completo", True),
        "r22_aptos": apt22,
        "r22_comparecimento": comp22,
        "r22_abstencao": abs22,
        "r22_validos": v22,
        "r22_bolsonaro": b,
        "r22_lula": l22,
        "r22_pct_bolsonaro": pb,
        "r22_pct_lula": pl,
        "r22_pct_abstencao": pa22,
        "flavio": m["flavio"],
        "lula": m["lula"],
        "validos": m["validos"],
        "pct_flavio": m["pct_flavio"],
        "pct_lula": m["pct_lula"],
        "pct_abstencao": m["pct_abstencao"],
        "swing_lula_pp": d2(m["pct_lula"], pl),
        "flavio_menos_bolsonaro_pp": d2(m["pct_flavio"], pb),
        "delta_votos_lula": m["lula"] - l22,
        "delta_votos_direita": m["flavio"] - b,
        "delta_abstencao_pp": d2(m["pct_abstencao"], pa22),
        "delta_aptos": (m["aptos"] - apt22) if apt22 else None,
        "vencedor_2022": vencedor22,
        "vencedor_2026": vencedor26,
        "virou": (vencedor22 == "lula") != (vencedor26 == "lula"),
    }


def comparacao_2022(
    ctx: Contexto, municipios: list[dict[str, Any]], r2022: dict[str, Any]
) -> dict[str, Any]:
    base22 = r2022["municipios"]
    pares, sem_2022 = [], []
    for m in municipios:
        r22 = base22.get(m["cd_tse"])
        if r22 is None:
            sem_2022.append({"cd_tse": m["cd_tse"], "uf": m["uf"], "nome": m["nome"]})
            continue
        pares.append(_par_2022(m, r22))
    completos = [p for p in pares if p["completo"]]

    def agregar(lista: list[dict[str, Any]], rotulo: str, chave: str) -> dict[str, Any]:
        mapa = {p["cd_tse"] for p in lista}
        m = {
            "uf": rotulo,
            "aptos": 0,
            "flavio": 0,
            "lula": 0,
            "validos": 0,
            "comparecimento": 0,
            "abstencao": 0,
        }
        r: dict[str, int] = dict.fromkeys(
            ("bolsonaro", "lula", "validos", "aptos", "comparecimento", "abstencao"), 0
        )
        for mm in municipios:
            if mm["cd_tse"] in mapa:
                for k in m:
                    if k != "uf":
                        m[k] += mm[k]
                for k in r:
                    r[k] += base22[mm["cd_tse"]].get(k, 0)
        m["pct_flavio"] = p2(m["flavio"], m["validos"])
        m["pct_lula"] = p2(m["lula"], m["validos"])
        m["pct_abstencao"] = p2(m["abstencao"], m["comparecimento"] + m["abstencao"])
        par = _par_2022(m, r)
        par.pop("cd_tse")
        par.pop("nome")
        par[chave] = rotulo
        par["n_municipios"] = len(lista)
        return par

    por_uf: dict[str, list[dict[str, Any]]] = defaultdict(list)
    por_reg: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for p in completos:
        por_uf[p["uf"]].append(p)
        por_reg[p["regiao"]].append(p)
    brasil = agregar(
        [p for p in completos if p["uf"] != "ZZ"], "Brasil sem exterior", "uf"
    )
    grandes = [p for p in completos if p["aptos"] >= 10000 and p["uf"] != "ZZ"]
    vals = [(p["swing_lula_pp"], p["aptos"]) for p in completos if p["uf"] != "ZZ"]
    viradas = [p for p in completos if p["virou"]]
    colunas = (
        tuple(k for k in pares[0] if k not in ("completo", "regiao")) if pares else ()
    )
    return {
        "rotulo": ROTULO,
        "definicoes": {
            "fonte_2022": (
                "data/raw/tse_resultados/votacao_candidato_munzona_2022.zip (_BR.csv, "
                "cargo 1, turno 2) e detalhe_votacao_secao_2022.zip (_BR.csv, cargo 1, "
                "turno 2), somados por município"
            ),
            "swing_lula_pp": "fatia de Lula nos válidos, 2º turno de 2026 menos 2º turno de 2022",
            "flavio_menos_bolsonaro_pp": "Flávio 2026 menos Bolsonaro 2022, em pontos dos válidos",
            "abstencao": "sobre o eleitorado; 2026 sobre as seções totalizadas",
            "base": "municípios com o arquivo presidencial de 2026 completo",
        },
        "fontes_2022": r2022["fontes"],
        "brasil": brasil,
        "exterior": (
            agregar([p for p in completos if p["uf"] == "ZZ"], "ZZ", "uf")
            if por_uf.get("ZZ")
            else None
        ),
        "regioes": [
            agregar(por_reg[r], r, "regiao") for r in REGIOES if por_reg.get(r)
        ],
        "ufs": [agregar(lista, uf, "uf") for uf, lista in sorted(por_uf.items())],
        "municipios": colunar(colunas, pares),
        "sem_2022": sem_2022,
        "dispersao_swing_lula_pp": resumo_distribuicao(
            [v for v, _ in vals if v is not None],
            [w for v, w in vals if v is not None],
        ),
        "n_lula_subiu": sum(1 for v, _ in vals if v is not None and v > 0),
        "n_lula_caiu": sum(1 for v, _ in vals if v is not None and v < 0),
        "maiores_swing_pro_lula": sorted(grandes, key=lambda p: -p["swing_lula_pp"])[
            :30
        ],
        "maiores_swing_pro_flavio": sorted(grandes, key=lambda p: p["swing_lula_pp"])[
            :30
        ],
        "viraram": {
            "n": len(viradas),
            "lula_2022_para_flavio_2026": sum(
                1 for p in viradas if p["vencedor_2022"] == "lula"
            ),
            "bolsonaro_2022_para_lula_2026": sum(
                1 for p in viradas if p["vencedor_2022"] == "bolsonaro"
            ),
            "lista": colunar(colunas, sorted(viradas, key=lambda p: -p["aptos"])),
        },
    }


# ---------------------------------------------------------------- abstenção


def abstencao(
    ctx: Contexto,
    municipios: list[dict[str, Any]],
    r2022: dict[str, Any],
    ufs_pres: list[dict[str, Any]],
) -> dict[str, Any]:
    base22 = r2022["municipios"]
    linhas = []
    for m in municipios:
        if m["uf"] == "ZZ" or not m["completo"]:
            continue
        m1 = ctx.mun_1t.get(m["cd_tse"])
        r22 = base22.get(m["cd_tse"], {})
        pa1 = p2(m1["abstencao"], m1["eleitores"]) if m1 else None
        pa22 = p2(r22.get("abstencao"), r22.get("aptos"))
        linhas.append(
            {
                "cd_tse": m["cd_tse"],
                "uf": m["uf"],
                "nome": m["nome"],
                "regiao": m["regiao"],
                "capital": m["capital"],
                "aptos": m["aptos"],
                "abstencao": m["abstencao"],
                "pa_2t": m["pct_abstencao"],
                "pa_1t": pa1,
                "pa_2022_2t": pa22,
                "delta_1t_pp": d2(m["pct_abstencao"], pa1),
                "delta_2022_pp": d2(m["pct_abstencao"], pa22),
                "t1_abstencao": m1["abstencao"] if m1 else None,
                "t1_eleitores": m1["eleitores"] if m1 else None,
                "r22_abstencao": r22.get("abstencao"),
                "r22_aptos": r22.get("aptos"),
                "pct_lula": m["pct_lula"],
            }
        )

    def bloco(lista: list[dict[str, Any]], **rot: Any) -> dict[str, Any]:
        apt = sum(r["aptos"] for r in lista)
        ab = sum(r["abstencao"] for r in lista)
        com1 = [r for r in lista if r["t1_eleitores"]]
        e1 = sum(r["t1_eleitores"] for r in com1)
        a1 = sum(r["t1_abstencao"] for r in com1)
        com22 = [r for r in lista if r["r22_aptos"]]
        e22 = sum(r["r22_aptos"] for r in com22)
        a22 = sum(r["r22_abstencao"] for r in com22)
        return {
            **rot,
            "n_municipios": len(lista),
            "aptos": apt,
            "abstencao": ab,
            "pa_2t": p2(ab, apt),
            "pa_1t_mesmos": p2(a1, e1),
            "pa_2022_2t_mesmos": p2(a22, e22),
            "delta_1t_pp": d2(p2(ab, apt), p2(a1, e1)),
            "delta_2022_pp": d2(p2(ab, apt), p2(a22, e22)),
        }

    por_uf: dict[str, list[dict[str, Any]]] = defaultdict(list)
    por_reg: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in linhas:
        por_uf[r["uf"]].append(r)
        por_reg[r["regiao"]].append(r)
    uf_arquivo = {u["uf"]: u for u in ufs_pres}
    ufs = []
    for uf, lista in sorted(por_uf.items()):
        b = bloco(lista, uf=uf, nome=NOME_UF[uf])
        u = uf_arquivo[uf]
        b["arquivo_uf"] = {
            "pst": u["pst"],
            "pa_2t": u["pct_abstencao"],
            "pa_1t": p2(ctx.ufs_1t[uf]["abstencao"], ctx.ufs_1t[uf]["eleitores"]),
        }
        b["arquivo_uf"]["delta_1t_pp"] = d2(
            b["arquivo_uf"]["pa_2t"], b["arquivo_uf"]["pa_1t"]
        )
        ufs.append(b)
    ranking = sorted(ufs, key=lambda b: b["arquivo_uf"]["pa_2t"])
    grandes = [r for r in linhas if r["aptos"] >= 10000]
    capitais = [r for r in linhas if r["capital"]]
    interior = [r for r in linhas if not r["capital"]]

    def histograma(chave: str, passo: float, lista: list[dict[str, Any]]) -> list[dict]:
        caixas: dict[float, dict[str, Any]] = {}
        for r in lista:
            v = r[chave]
            if v is None:
                continue
            k = round(passo * (v // passo), 2)
            c = caixas.setdefault(
                k, {"de": k, "ate": round(k + passo, 2), "n": 0, "aptos": 0}
            )
            c["n"] += 1
            c["aptos"] += r["aptos"]
        return [caixas[k] for k in sorted(caixas)]

    baixa = [r for r in linhas if r["pa_2t"] is not None and r["pa_2t"] < 15]
    concentracao = []
    for reg in REGIOES:
        todos = por_reg.get(reg, [])
        b = [r for r in baixa if r["regiao"] == reg]
        concentracao.append(
            {
                "regiao": reg,
                "municipios": len(todos),
                "municipios_abaixo_15": len(b),
                "pct_municipios_abaixo_15": p2(len(b), len(todos)),
                "aptos_abaixo_15": sum(r["aptos"] for r in b),
                "pct_aptos_abaixo_15_no_pais": p2(
                    sum(r["aptos"] for r in b), sum(r["aptos"] for r in baixa)
                ),
            }
        )
    colunas = (
        "cd_tse",
        "uf",
        "nome",
        "capital",
        "aptos",
        "pa_2t",
        "pa_1t",
        "pa_2022_2t",
        "delta_1t_pp",
        "delta_2022_pp",
        "pct_lula",
    )
    return {
        "rotulo": ROTULO,
        "definicoes": {
            "pa": "abstenção sobre o eleitorado, em %",
            "base": (
                "municípios com o arquivo presidencial completo; 1º turno e 2º turno "
                "de 2022 nos mesmos municípios (pa_1t_mesmos, pa_2022_2t_mesmos)"
            ),
            "explicacoes_legitimas": (
                "a votação foi prorrogada até 19h em todo o país; mobilização de "
                "segundo turno e transporte gratuito também elevam o comparecimento"
            ),
        },
        "brasil": bloco(linhas, sigla="BR", nome="Brasil sem exterior"),
        "regioes": [bloco(por_reg[r], regiao=r) for r in REGIOES if por_reg.get(r)],
        "ufs": ufs,
        "ranking_ufs_menor_abstencao": [
            {
                "uf": b["uf"],
                "pa_2t": b["arquivo_uf"]["pa_2t"],
                "delta_1t_pp": b["arquivo_uf"]["delta_1t_pp"],
            }
            for b in ranking
        ],
        "capitais_x_interior": {
            "capitais": bloco(capitais, recorte="capitais"),
            "interior": bloco(interior, recorte="interior"),
            "capitais_lista": sorted(
                ({k: r[k] for k in colunas} for r in capitais), key=lambda r: r["pa_2t"]
            ),
        },
        "municipios_10mil": colunar(colunas, sorted(grandes, key=lambda r: r["pa_2t"])),
        "menores_10mil": [
            {k: r[k] for k in colunas}
            for r in sorted(grandes, key=lambda r: r["pa_2t"])[:30]
        ],
        "maiores_10mil": [
            {k: r[k] for k in colunas}
            for r in sorted(grandes, key=lambda r: -r["pa_2t"])[:30]
        ],
        "maior_queda_vs_1t_10mil": [
            {k: r[k] for k in colunas}
            for r in sorted(
                (g for g in grandes if g["delta_1t_pp"] is not None),
                key=lambda r: r["delta_1t_pp"],
            )[:30]
        ],
        "maior_alta_vs_1t_10mil": [
            {k: r[k] for k in colunas}
            for r in sorted(
                (g for g in grandes if g["delta_1t_pp"] is not None),
                key=lambda r: -r["delta_1t_pp"],
            )[:30]
        ],
        "histograma_pa_2t": {
            "passo_pp": 1,
            "caixas": histograma("pa_2t", 1.0, linhas),
        },
        "histograma_delta_1t": {
            "passo_pp": 0.5,
            "caixas": histograma("delta_1t_pp", 0.5, linhas),
        },
        "concentracao_abaixo_15": concentracao,
        "n_municipios_caiu_vs_1t": sum(
            1 for r in linhas if (r["delta_1t_pp"] or 0) < 0
        ),
        "n_municipios_subiu_vs_1t": sum(
            1 for r in linhas if (r["delta_1t_pp"] or 0) > 0
        ),
        "dispersao_delta_1t": resumo_distribuicao(
            [r["delta_1t_pp"] for r in linhas if r["delta_1t_pp"] is not None],
            [r["aptos"] for r in linhas if r["delta_1t_pp"] is not None],
        ),
    }
