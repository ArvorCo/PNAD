"""Previsão presidencial da casa (central, Monte Carlo, âncoras, regiões, UFs) contra a urna.

Funções puras sobre o JSON publicado em ``docs/assets/predicao_2026_1T_presidente.json``
e o dicionário da urna montado por ``scripts/apuracao-2026-pesquisas.py``.
"""

from __future__ import annotations

import statistics

from . import pesquisas as P


def pct_validos(bloco: dict) -> dict:
    v = bloco["lula"] + bloco["flavio"] + bloco["outros"]
    return {
        "flavio": 100 * bloco["flavio"] / v,
        "lula": 100 * bloco["lula"] / v,
        "terceira_via": 100 * bloco["outros"] / v,
    }


def comparar_blocos(prev: dict, urna_v: dict) -> dict:
    ub = P.blocos(urna_v)
    erros = {k: prev[k] - ub[k] for k in ub}
    return {
        "validos": prev,
        "erro_pp": erros,
        "erro_diferenca_lula_menos_flavio": (prev["lula"] - prev["flavio"])
        - (ub["lula"] - ub["flavio"]),
        "eam_blocos_pp": statistics.fmean(abs(e) for e in erros.values()),
    }


def previsao_casa(prev: dict, urna: dict) -> dict:
    alvo = urna["validos"]
    br = prev["central"]["brasil"]
    central = comparar_blocos(pct_validos(br), alvo)
    dem = {k: 100 * v / br["validos"] for k, v in br["demais"].items()}
    dem_urna = {
        "renan_santos": alvo["renan_santos"],
        "cury": alvo["cury"],
        "caiado": alvo["caiado"],
        "zema": alvo["zema"],
    }
    dem_urna["restantes"] = 100 - alvo["flavio"] - alvo["lula"] - sum(dem_urna.values())
    central["terceiros_validos"] = dem
    central["terceiros_urna"] = dem_urna
    central["terceiros_erro_pp"] = {k: dem[k] - dem_urna[k] for k in dem}
    central["comparecimento"] = {
        "previsto": br["comparecimento"],
        "urna": urna["comparecimento"],
    }
    central["branco_nulo"] = {
        "previsto": br["branco_nulo"],
        "urna": urna["brancos"] + urna["nulos"],
    }
    inc = prev["incerteza"]
    margem_urna = alvo["flavio"] - alvo["lula"]
    mc = {
        "sorteios": inc["sorteios"],
        "erro_comum_sd_pp": inc["erro_comum_total_sd_pp"],
        "intervalos_90_validos": {},
        "margem_flavio_menos_lula": {
            **inc["margem"],
            "urna": margem_urna,
            "percentil_urna": P.percentil_histograma(
                margem_urna, inc["distribuicao_margem"], inc["limites_histograma"]
            ),
        },
        "p_flavio_a_frente_de_lula": inc["p_flavio_a_frente_de_lula"],
    }
    for k, uk in (("flavio", "flavio"), ("lula", "lula"), ("outros", "terceira_via")):
        q = inc["candidatos"][k]["percentual"]
        u = P.blocos(alvo)[uk]
        mc["intervalos_90_validos"][uk] = {
            "p05": q["p05"],
            "p50": q["p50"],
            "p95": q["p95"],
            "urna": u,
            "dentro": q["p05"] <= u <= q["p95"],
        }
    ancoras = {}
    for base, vet in prev["nacional"]["alvos"].items():
        s = vet[0] + vet[1] + vet[2]
        ancoras[base] = comparar_blocos(
            {
                "lula": 100 * vet[0] / s,
                "flavio": 100 * vet[1] / s,
                "terceira_via": 100 * vet[2] / s,
            },
            alvo,
        )
    sens = []
    for nome, s in prev["sensibilidades"].items():
        sens.append({"nome": nome, **comparar_blocos(pct_validos(s["brasil"]), alvo)})
    sens.sort(key=lambda r: abs(r["erro_diferenca_lula_menos_flavio"]))
    din = prev["nacional"]["dinamico"]["estado_final"]
    dlm = comparar_blocos(
        {
            "flavio": din["validos_pct"]["flavio"],
            "lula": din["validos_pct"]["lula"],
            "terceira_via": din["validos_pct"]["outros"],
        },
        alvo,
    )
    dlm["dp_margem_pp"] = din["dp_margem_pp"]
    dlm["z_urna"] = (margem_urna - din["margem_flavio_lula_validos_pp"]) / din[
        "dp_margem_pp"
    ]
    return {
        "gerado_em": prev["gerado_em"],
        "central": central,
        "monte_carlo": mc,
        "ancoras_validos": ancoras,
        "sensibilidades": sens,
        "dlm": dlm,
        "regioes": regioes(prev, urna),
        "ufs": ufs_central(prev, urna),
    }


MACRO = {
    "Nordeste": "Nordeste",
    "Norte": "Norte",
    "Sudeste": "Centro-Sul",
    "Sul": "Centro-Sul",
    "Centro-Oeste": "Centro-Sul",
    "Exterior": "Exterior",
}


def regioes(prev: dict, urna: dict) -> dict:
    reg_uf = {u["uf"]: u["regiao"] for u in prev["central"]["ufs"]}
    agreg: dict[str, dict] = {}
    for uf, u in urna["ufs"].items():
        for nivel in (reg_uf[uf], f"macro:{MACRO[reg_uf[uf]]}"):
            a = agreg.setdefault(nivel, {"flavio": 0, "lula": 0, "validos": 0})
            a["flavio"] += u["votos"]["flavio"]
            a["lula"] += u["votos"]["lula"]
            a["validos"] += u["validos_votos"]
    prev_agreg: dict[str, dict] = {}
    for u in prev["central"]["ufs"]:
        for nivel in (u["regiao"], f"macro:{MACRO[u['regiao']]}"):
            a = prev_agreg.setdefault(
                nivel, {"flavio": 0.0, "lula": 0.0, "outros": 0.0}
            )
            for k in a:
                a[k] += u[k]
    out = {}
    inc = prev["incerteza"]["regioes"]
    for nivel, a in sorted(agreg.items()):
        uv = {
            "flavio": 100 * a["flavio"] / a["validos"],
            "lula": 100 * a["lula"] / a["validos"],
        }
        cmp = comparar_blocos(pct_validos(prev_agreg[nivel]), uv)
        cmp["votos_urna"] = a
        if nivel in inc:
            cmp["intervalo_90_votos"] = {
                k: {
                    **inc[nivel][k]["votos"],
                    "urna": a[k],
                    "dentro": inc[nivel][k]["votos"]["p05"]
                    <= a[k]
                    <= inc[nivel][k]["votos"]["p95"],
                }
                for k in ("flavio", "lula")
            }
        out[nivel.replace("macro:", "macro_")] = cmp
    return out


def ufs_central(prev: dict, urna: dict) -> dict:
    linhas = []
    for u in prev["central"]["ufs"]:
        uv = urna["ufs"][u["uf"]]["validos"]
        c = comparar_blocos(pct_validos(u), uv)
        c["uf"], c["regiao"] = u["uf"], u["regiao"]
        prev_lider = (
            "flavio" if c["validos"]["flavio"] > c["validos"]["lula"] else "lula"
        )
        urna_lider = "flavio" if uv["flavio"] > uv["lula"] else "lula"
        c["lider_previsto"], c["lider_urna"] = prev_lider, urna_lider
        c["acertou_lider"] = prev_lider == urna_lider
        dem = {
            k: 100 * v / (u["lula"] + u["flavio"] + u["outros"])
            for k, v in u["demais"].items()
        }
        dem_u = {k: uv[k] for k in ("renan_santos", "cury", "caiado", "zema")}
        dem_u["restantes"] = 100 - uv["flavio"] - uv["lula"] - sum(dem_u.values())
        c["terceiros_erro_pp"] = {k: dem[k] - dem_u[k] for k in dem}
        linhas.append(c)
    linhas.sort(key=lambda r: -abs(r["erro_diferenca_lula_menos_flavio"]))
    sem_zz = [r for r in linhas if r["uf"] != "ZZ"]
    margem_urna = [
        r["validos"]["lula"]
        - r["validos"]["flavio"]
        - r["erro_diferenca_lula_menos_flavio"]
        for r in sem_zz
    ]
    erro_dif = [r["erro_diferenca_lula_menos_flavio"] for r in sem_zz]
    reg = statistics.linear_regression(margem_urna, erro_dif)
    return {
        "ordenacao": "maior erro absoluto na diferença L−F primeiro",
        "linhas": linhas,
        "resumo": {
            "n_ufs": len(sem_zz),
            "acertos_lider": sum(r["acertou_lider"] for r in sem_zz),
            "erros_lider": [r["uf"] for r in sem_zz if not r["acertou_lider"]],
            "eam_flavio_pp": statistics.fmean(
                abs(r["erro_pp"]["flavio"]) for r in sem_zz
            ),
            "eam_lula_pp": statistics.fmean(abs(r["erro_pp"]["lula"]) for r in sem_zz),
            "erro_medio_flavio_pp": statistics.fmean(
                r["erro_pp"]["flavio"] for r in sem_zz
            ),
            "erro_medio_lula_pp": statistics.fmean(
                r["erro_pp"]["lula"] for r in sem_zz
            ),
            "erro_medio_terceira_via_pp": statistics.fmean(
                r["erro_pp"]["terceira_via"] for r in sem_zz
            ),
            "ufs_flavio_subestimado": sum(r["erro_pp"]["flavio"] < 0 for r in sem_zz),
            "polarizacao": {
                "regra": (
                    "regressão, sem peso, do erro da central na diferença L−F de cada UF sobre a "
                    "diferença L−F da urna na UF; inclinação negativa = a urna foi mais polarizada "
                    "por UF do que a previsão"
                ),
                "inclinacao": reg.slope,
                "intercepto": reg.intercept,
                "correlacao": statistics.correlation(margem_urna, erro_dif),
            },
        },
    }
