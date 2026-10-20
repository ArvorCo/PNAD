"""Análises 1 a 4 e 6 do contrato: bateria, reinício e abstenção contra chuva e vento.

Unidade: a urna (boletim do 1º turno no Brasil, seção principal) com clima na célula do
local. Abstenção sempre ponderada por aptos (razão de somas). Intervalos de 95% por
bootstrap de células (``estatistica.BootCelulas``); regressões com efeito fixo e erro-padrão
por conglomerado de célula. Correlação não é causa: o desenho só controla o que declara.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from clima_1t import estatistica as es
from clima_1t.variaveis import FAIXAS_CHUVA, FAIXAS_RAJADA, ROTULO_CHUVA, ROTULO_RAJADA

MIN_CELULAS = 20  # abaixo disso o bootstrap de células não dá intervalo confiável
MIN_ESTRATOS = 10
NOTA_CELULAS = f"menos de {MIN_CELULAS} células: sem intervalo de confiança"
NOTA_ESTRATOS = f"menos de {MIN_ESTRATOS} estratos com os dois grupos: sem intervalo"

EXPOSICOES: dict[str, tuple[str, tuple[str, ...], str]] = {
    "chuva_votacao": (
        "faixa_chuva_votacao",
        FAIXAS_CHUVA,
        "chuva das 7h às 18h de Brasília de 04/10 (mm)",
    ),
    "chuva_diaria": ("faixa_chuva", FAIXAS_CHUVA, "chuva no dia 04/10 inteiro (mm)"),
    "rajada_votacao": (
        "faixa_rajada_votacao",
        FAIXAS_RAJADA,
        "rajada máxima das 7h às 18h de Brasília de 04/10 (km/h)",
    ),
    "rajada_diaria": (
        "faixa_rajada",
        FAIXAS_RAJADA,
        "rajada máxima no dia 04/10 (km/h)",
    ),
}
CONTINUAS = {
    "chuva_votacao": ("chuva_votacao_mm", 10.0, "por 10 mm"),
    "chuva_diaria": ("chuva_04_10_mm", 10.0, "por 10 mm"),
    "rajada_votacao": ("rajada_votacao_kmh", 10.0, "por 10 km/h"),
    "rajada_diaria": ("rajada_04_10_kmh", 10.0, "por 10 km/h"),
    "chuva_estrita": ("chuva_votacao_estrita_mm", 10.0, "por 10 mm"),
}
DESFECHOS: dict[str, tuple[str, str, str]] = {
    "bateria_votacao": (
        "bateria_votacao",
        "relogio_ok",
        "urnas com registro de operação com bateria interna durante a votação, entre as "
        "urnas com log lido e relógio válido",
    ),
    "bateria_qualquer": (
        "bateria",
        "log_ok",
        "urnas com registro de bateria interna em qualquer momento do log, entre as urnas "
        "com log lido",
    ),
    "reinicio": (
        "reinicio",
        "log_ok",
        "urnas com reinício durante a votação, entre as urnas com log lido",
    ),
    "bateria_simultanea": (
        "bat_vot_local",
        "relogio_ok",
        "bateria durante a votação com 5 ou mais outras seções do município no mesmo "
        "minuto (±60 s), assinatura de fornecimento compartilhado; denominador: urnas com "
        "log e relógio válidos",
    ),
    "bateria_isolada": (
        "bat_vot_isolada",
        "relogio_ok",
        "bateria durante a votação sem nenhuma outra seção do município no mesmo minuto, "
        "assinatura de tomada, extensão ou fonte da própria urna; denominador: urnas com "
        "log e relógio válidos",
    ),
    "abertura_atrasada": (
        "abertura_atrasada",
        "hora_ok",
        "primeiro voto às 8h30 de Brasília ou depois, entre as urnas com hora de abertura",
    ),
}


def rotulos(faixas: tuple[str, ...]) -> dict[str, str]:
    return ROTULO_CHUVA if faixas == FAIXAS_CHUVA else ROTULO_RAJADA


def preparar(urnas: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray, int]:
    """Amostra analítica: urnas do Brasil com clima e aptos; índice de célula."""
    u = urnas.loc[urnas["tem_clima"] & (urnas["aptos"] > 0)].copy()
    u = u.reset_index(drop=True)
    for c in (
        "bateria_votacao",
        "bateria",
        "reinicio",
        "bat_vot_local",
        "bat_vot_isolada",
    ):
        u[c] = u[c].eq(True)
    u["abertura_atrasada"] = u["abertura_atrasada"].eq(True)
    u["hora_ok"] = u["hora_ok"].eq(True)
    u["log_aptos"] = np.log(u["aptos"])
    u["modelo"] = u["modelo_urna"].fillna("sem_modelo")
    u["mun_id"] = u["uf"] + "-" + u["mun"]
    u["abst_c"] = u["aptos_c"] - u["comp_c"]
    u["abst22"] = u["aptos22"] - u["comp22"]
    u["bat_vot_intermediaria"] = (
        u["bateria_votacao"] & ~u["bat_vot_local"] & ~u["bat_vot_isolada"]
    )
    for nome, (col, esc, _) in CONTINUAS.items():
        u[nome + "_x"] = u[col] / esc
    cel, _ = pd.factorize(u["cel"])
    return u, cel.astype(np.int64), int(cel.max() + 1)


def _ic_cel(valor: dict[str, Any], ncel: int) -> dict[str, Any]:
    return valor if ncel >= MIN_CELULAS else es.sem_ic(valor, NOTA_CELULAS)


def _indice_faixa(serie: pd.Series, faixas: tuple[str, ...]) -> np.ndarray:
    return (
        serie.map({f: i for i, f in enumerate(faixas)})
        .fillna(-1)
        .astype(int)
        .to_numpy()
    )


def _celulas_por_grupo(cel: np.ndarray, grupo: np.ndarray, n: int) -> list[int]:
    ok = grupo >= 0
    pares = pd.DataFrame({"g": grupo[ok], "c": cel[ok]}).drop_duplicates()
    cont = pares["g"].value_counts()
    return [int(cont.get(i, 0)) for i in range(n)]


# --- 1. Bateria e reinício contra chuva e vento ---------------------------------------


def bateria_x_chuva(
    u: pd.DataFrame, cel: np.ndarray, boot: es.BootCelulas
) -> dict[str, Any]:
    nomes = list(DESFECHOS)
    cols = []
    for y, den, _ in DESFECHOS.values():
        d = u[den].to_numpy(bool)
        cols += [(u[y].to_numpy(bool) & d).astype(float), d.astype(float)]
    valores = np.column_stack(cols)
    k = len(nomes)
    por_exposicao = {}
    for exp, (col, faixas, desc) in EXPOSICOES.items():
        g = _indice_faixa(u[col], faixas)
        nf = len(faixas)

        def f(s: np.ndarray, k: int = k) -> np.ndarray:
            out = []
            for j in range(k):
                p = es.razao(s, 2 * j, 2 * j + 1)
                with np.errstate(divide="ignore", invalid="ignore"):
                    out += [p, p / p[:, [0]]]
            return np.concatenate(out, axis=1)

        ponto, reps = es.aplicar(boot, cel, g, valores, nf, f)
        somas = np.zeros((nf, valores.shape[1]))
        np.add.at(somas, g[g >= 0], valores[g >= 0])
        ncel = _celulas_por_grupo(cel, g, nf)
        rot = rotulos(faixas)
        tabela = {}
        for j, nome in enumerate(nomes):
            linhas = []
            for i, fx in enumerate(faixas):
                ip, ir = (2 * j) * nf + i, (2 * j + 1) * nf + i
                linhas.append(
                    {
                        "faixa": fx,
                        "rotulo": rot[fx],
                        "celulas": ncel[i],
                        "urnas": int(somas[i, 2 * j + 1]),
                        "com_registro": int(somas[i, 2 * j]),
                        "parcela_pct": _ic_cel(
                            es.ic(ponto[ip], reps[:, ip], 100.0, 2), ncel[i]
                        ),
                        "razao_vs_ref": (
                            None
                            if i == 0
                            else _ic_cel(
                                es.ic(ponto[ir], reps[:, ir], 1.0, 3),
                                min(ncel[i], ncel[0]),
                            )
                        ),
                    }
                )
            tabela[nome] = linhas
        por_exposicao[exp] = {
            "descricao": desc,
            "referencia": faixas[0],
            "faixas": tabela,
        }
    return {
        "unidade": "urna (boletim do 1º turno, seção principal) com clima na célula do local",
        "desfechos": {n: d for n, (_, _, d) in DESFECHOS.items()},
        "por_exposicao": por_exposicao,
        "ic": f"bootstrap de células de 0,25° ({boot.reps} réplicas, percentis 2,5 e 97,5)",
    }


def regressoes_bateria(u: pd.DataFrame) -> dict[str, Any]:
    """Logísticas com efeito fixo de UF, log dos aptos e modelo da urna."""
    saida: dict[str, Any] = {
        "modelo": "logística; efeito fixo de UF (indicadoras); controles: log dos aptos "
        "da seção e modelo da urna (UE2013, UE2015, UE2020, UE2022); erro-padrão por "
        "conglomerado de célula de 0,25°",
        "unidades": {n: v[2] for n, v in CONTINUAS.items()},
        "desfechos": {},
    }
    planos = {
        "bateria_votacao": [
            ["chuva_votacao_x"],
            ["chuva_diaria_x"],
            ["rajada_votacao_x"],
            ["rajada_diaria_x"],
            ["chuva_votacao_x", "rajada_votacao_x"],
            ["chuva_estrita_x"],
        ],
        "bateria_qualquer": [["chuva_diaria_x"], ["rajada_diaria_x"]],
        "reinicio": [["chuva_votacao_x"], ["rajada_votacao_x"]],
        "bateria_simultanea": [["chuva_votacao_x"], ["rajada_votacao_x"]],
        "bateria_isolada": [["chuva_votacao_x"], ["rajada_votacao_x"]],
        "abertura_atrasada": [["chuva_diaria_x"], ["rajada_diaria_x"]],
    }
    for nome, modelos in planos.items():
        y, den, _ = DESFECHOS[nome]
        d = u.loc[u[den]].copy()
        d["y"] = d[y].astype(float)
        res = []
        for x in modelos:
            r = es.logit(d, "y", x, "cel", fe="uf", cat=["modelo"], num=["log_aptos"])
            r["exposicao"] = x
            res.append(r)
        saida["desfechos"][nome] = res
    d = u.loc[u["relogio_ok"]].copy()
    d["y"] = d["bateria_votacao"].astype(float) * 100
    d["um"] = 1.0
    saida["robustez_municipio"] = {
        "modelo": "probabilidade linear (pontos percentuais) com efeito fixo de município; "
        "compara urnas do mesmo município em células com chuva diferente",
        "bateria_votacao": [
            es.mqp_fe_municipio(d, "y", ["chuva_votacao_x"], "um", "cel"),
            es.mqp_fe_municipio(d, "y", ["rajada_votacao_x"], "um", "cel"),
        ],
    }
    return saida


# --- 2 e 3. Abstenção -------------------------------------------------------------------

COL_ABST = ["abst", "aptos", "abst_c", "aptos_c", "abst22", "aptos22"]


def _taxas(s4: np.ndarray) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Taxas (abstenção 2026 e diferença contra 2022) e pesos, a partir das somas."""
    with np.errstate(divide="ignore", invalid="ignore"):
        abst = s4[..., 0] / s4[..., 1]
        dif = s4[..., 2] / s4[..., 3] - s4[..., 4] / s4[..., 5]
    return {"abst": (abst, s4[..., 1]), "dif": (dif, s4[..., 3])}


def nacional(
    u: pd.DataFrame,
    cel: np.ndarray,
    boot: es.BootCelulas,
    grupo: np.ndarray,
    rot: list[str],
) -> list[dict[str, Any]]:
    """Abstenção e diferença contra 2022 por grupo, e diferença contra o grupo 0."""
    n = len(rot)
    v = u[COL_ABST].to_numpy(float)

    def f(s: np.ndarray) -> np.ndarray:
        t = _taxas(s)
        out = []
        for a, _ in t.values():
            out += [a, a - a[:, [0]]]
        return np.concatenate(out, axis=1)

    p, r = es.aplicar(boot, cel, grupo, v, n, f)
    somas = np.zeros((n, v.shape[1]))
    np.add.at(somas, grupo[grupo >= 0], v[grupo >= 0])
    urnas = np.bincount(grupo[grupo >= 0], minlength=n)
    ncel = _celulas_por_grupo(cel, grupo, n)
    linhas = []
    for i, nome in enumerate(rot):
        linhas.append(
            {
                "grupo": nome,
                "urnas": int(urnas[i]),
                "celulas": ncel[i],
                "aptos": int(somas[i, 1]),
                "aptos_casados_2022": int(somas[i, 3]),
                "abst_pct": _ic_cel(es.ic(p[i], r[:, i], 100.0, 2), ncel[i]),
                "abst_vs_ref_pp": (
                    None
                    if i == 0
                    else _ic_cel(
                        es.ic(p[n + i], r[:, n + i], 100.0, 2), min(ncel[i], ncel[0])
                    )
                ),
                "dif_abst_pp": _ic_cel(
                    es.ic(p[2 * n + i], r[:, 2 * n + i], 100.0, 2), ncel[i]
                ),
                "dif_vs_ref_pp": (
                    None
                    if i == 0
                    else _ic_cel(
                        es.ic(p[3 * n + i], r[:, 3 * n + i], 100.0, 2),
                        min(ncel[i], ncel[0]),
                    )
                ),
            }
        )
    return linhas


def dentro(
    u: pd.DataFrame,
    cel: np.ndarray,
    boot: es.BootCelulas,
    estrato: pd.Series,
    grupo: np.ndarray,
    rot: list[str],
    max_valores: float = 2.5e7,
) -> dict[str, Any]:
    """Diferença contra o grupo 0 dentro do mesmo estrato (UF, município ou prédio)."""
    n = len(rot)
    sid, _ = pd.factorize(estrato)
    v = u[COL_ABST].to_numpy(float)
    ok = grupo >= 0
    # estratos com o grupo de referência e ao menos um outro grupo, no ponto
    pres = pd.DataFrame({"s": sid[ok], "g": grupo[ok], "a": v[ok, 1]})
    pres = pres.loc[pres["a"] > 0].groupby(["s", "g"]).size().unstack(fill_value=0) > 0
    pres = pres.reindex(columns=range(n), fill_value=False)
    manter = pres.index[pres[0] & pres.drop(columns=0).any(axis=1)]
    novo = pd.Series(np.arange(len(manter)), index=manter)
    s_novo = pd.Series(sid).map(novo).fillna(-1).astype(int).to_numpy()
    g = np.where((s_novo >= 0) & ok, s_novo * n + grupo, -1)
    ns = len(manter)
    mascara = pres.loc[manter].to_numpy() & pres.loc[manter, [0]].to_numpy()
    if ns == 0:
        return {"estratos": 0}
    k = v.shape[1]
    bloco = max(1, int(max_valores // (ns * n * k)))
    b2 = es.BootCelulas(boot.n_celulas, boot.reps, boot.seed, min(bloco, 100))

    def f(s: np.ndarray) -> np.ndarray:
        s4 = s.reshape(s.shape[0], ns, n, k)
        out = []
        for taxa, peso in _taxas(s4).values():
            out.append(es.dif_dentro(taxa, peso, 0, mascara))
        return np.concatenate(out, axis=1)

    p, r = es.aplicar(b2, cel, g, v, ns * n, f)
    res = {"estratos": int(ns), "grupos": {}}
    for i, nome in enumerate(rot):
        if i == 0:
            continue
        ne = int(mascara[:, i].sum())
        va = es.ic(p[i], r[:, i], 100.0, 2)
        vd = es.ic(p[n + i], r[:, n + i], 100.0, 2)
        if ne < MIN_ESTRATOS:
            va, vd = es.sem_ic(va, NOTA_ESTRATOS), es.sem_ic(vd, NOTA_ESTRATOS)
        res["grupos"][nome] = {
            "estratos_com_os_dois": ne,
            "abst_vs_ref_pp": va,
            "dif_vs_ref_pp": vd,
        }
    return res


def abstencao_x_chuva(
    u: pd.DataFrame, cel: np.ndarray, boot: es.BootCelulas
) -> dict[str, Any]:
    saida: dict[str, Any] = {
        "medidas": {
            "abst_pct": "abstenção do 1º turno de 2026, aptos menos comparecimento sobre "
            "aptos, razão de somas (ponderada por aptos)",
            "dif_abst_pp": "abstenção de 2026 menos abstenção do 2º turno de 2022 nas mesmas "
            "seções (casadas por UF, município, zona e número), razão de somas de cada ano",
        },
        "por_exposicao": {},
    }
    for exp, (col, faixas, desc) in EXPOSICOES.items():
        g = _indice_faixa(u[col], faixas)
        rot = list(faixas)
        saida["por_exposicao"][exp] = {
            "descricao": desc,
            "referencia": faixas[0],
            "rotulos": rotulos(faixas),
            "pais": nacional(u, cel, boot, g, rot),
            "dentro_da_uf": dentro(u, cel, boot, u["uf"], g, rot),
            "dentro_do_municipio": dentro(u, cel, boot, u["mun_id"], g, rot),
        }
    binarios = {
        "chuva_votacao": ("chuva_votacao_mm", 5.0, ["até 5 mm", "mais de 5 mm"]),
        "chuva_diaria": ("chuva_04_10_mm", 20.0, ["até 20 mm", "mais de 20 mm"]),
        "rajada_votacao": (
            "rajada_votacao_kmh",
            60.0,
            ["até 60 km/h", "mais de 60 km/h"],
        ),
    }
    binario: dict[str, Any] = {
        "regra": "dois grupos por corte declarado, para que mais municípios tenham os dois "
        "lados; referência: o grupo de baixo",
    }
    saida["binario"] = binario
    for exp, (col, corte, rot) in binarios.items():
        x = u[col].to_numpy(float)
        g = np.where(np.isfinite(x), (x > corte).astype(int), -1)
        binario[exp] = {
            "corte": corte,
            "pais": nacional(u, cel, boot, g, rot),
            "dentro_da_uf": dentro(u, cel, boot, u["uf"], g, rot),
            "dentro_do_municipio": dentro(u, cel, boot, u["mun_id"], g, rot),
        }
    # chuva forte (dia) e bateria durante a votação, combinadas
    forte = u["faixa_chuva"].isin(["forte", "muito_forte"]).to_numpy()
    bat = (u["bateria_votacao"] & u["relogio_ok"]).to_numpy()
    rel = u["relogio_ok"].to_numpy()
    g = np.where(rel, forte.astype(int) * 2 + bat.astype(int), -1)
    rot = [
        "sem chuva forte, sem bateria",
        "sem chuva forte, com bateria",
        "chuva forte, sem bateria",
        "chuva forte, com bateria",
    ]
    saida["chuva_forte_e_bateria"] = {
        "regra": "chuva forte = mais de 20 mm no dia 04/10; bateria = registro durante a "
        "votação; urnas com log e relógio válidos",
        "pais": nacional(u, cel, boot, g, rot),
        "dentro_do_municipio": dentro(u, cel, boot, u["mun_id"], g, rot),
    }
    return saida


def regressoes_abstencao(u: pd.DataFrame) -> dict[str, Any]:
    d = u.copy()
    d["abst_pp"] = d["abst_pct"]
    d["bat"] = (d["bateria_votacao"] & d["relogio_ok"]).astype(float)
    d["chuva_x_bat"] = d["chuva_votacao_x"] * d["bat"]
    saida: dict[str, Any] = {
        "modelo": "mínimos quadrados ponderados por aptos (abstenção) ou por aptos casados "
        "(diferença contra 2022); efeito fixo de UF com log dos aptos, e efeito fixo de "
        "município; erro-padrão por conglomerado de célula; coeficientes em pontos "
        "percentuais por 10 mm ou por 10 km/h",
        "abstencao_2026": {},
        "dif_contra_2022": {},
    }
    for exp in (
        "chuva_votacao",
        "chuva_diaria",
        "rajada_votacao",
        "rajada_diaria",
        "chuva_estrita",
    ):
        x = [exp + "_x"]
        saida["abstencao_2026"][exp] = {
            "fe_uf": es.mqp(
                d, "abst_pp", x, "aptos", "cel", fe="uf", num=["log_aptos"]
            ),
            "fe_municipio": es.mqp_fe_municipio(d, "abst_pp", x, "aptos", "cel"),
        }
        dc = d.loc[d["aptos_c"] > 0]
        saida["dif_contra_2022"][exp] = {
            "fe_uf": es.mqp(
                dc, "dif_abst_pp", x, "aptos_c", "cel", fe="uf", num=["log_aptos"]
            ),
            "fe_municipio": es.mqp_fe_municipio(dc, "dif_abst_pp", x, "aptos_c", "cel"),
        }
    dr = d.loc[d["relogio_ok"]]
    xs = ["chuva_votacao_x", "bat", "chuva_x_bat"]
    saida["interacao_chuva_bateria"] = {
        "termos": "chuva_votacao_x (por 10 mm), bat (bateria durante a votação), chuva_x_bat",
        "abstencao_2026": {
            "fe_uf": es.mqp(
                dr, "abst_pp", xs, "aptos", "cel", fe="uf", num=["log_aptos"]
            ),
            "fe_municipio": es.mqp_fe_municipio(dr, "abst_pp", xs, "aptos", "cel"),
        },
        "dif_contra_2022": {
            "fe_municipio": es.mqp_fe_municipio(
                dr.loc[dr["aptos_c"] > 0], "dif_abst_pp", xs, "aptos_c", "cel"
            ),
        },
    }
    return saida


def abstencao_x_bateria(
    u: pd.DataFrame, cel: np.ndarray, boot: es.BootCelulas
) -> dict[str, Any]:
    rel = u["relogio_ok"].to_numpy()
    bat = u["bateria_votacao"].to_numpy()
    g2 = np.where(rel, bat.astype(int), -1)
    rot2 = ["sem bateria durante a votação", "com bateria durante a votação"]
    tipo = np.select(
        [~bat, u["bat_vot_local"].to_numpy(), u["bat_vot_isolada"].to_numpy()],
        [0, 1, 2],
        default=3,
    )
    g4 = np.where(rel, tipo, -1)
    rot4 = [
        "sem bateria durante a votação",
        "simultânea (5 ou mais outras seções do município no mesmo minuto)",
        "isolada (nenhuma outra seção do município no mesmo minuto)",
        "intermediária (1 a 4 outras seções no mesmo minuto)",
    ]
    d = u.copy()
    d["bat"] = (d["bateria_votacao"] & d["relogio_ok"]).astype(float)
    dr = d.loc[d["relogio_ok"]]
    return {
        "denominador": "urnas com log lido e relógio válido",
        "tempo_em_bateria": "não medido: o log diz que a urna operou com bateria, não por "
        "quanto tempo, nem se a fila parou",
        "pais": nacional(u, cel, boot, g2, rot2),
        "dentro_do_municipio": dentro(u, cel, boot, u["mun_id"], g2, rot2),
        "dentro_do_predio": dentro(u, cel, boot, u["local_id"], g2, rot2),
        "por_tipo": {
            "pais": nacional(u, cel, boot, g4, rot4),
            "dentro_do_municipio": dentro(u, cel, boot, u["mun_id"], g4, rot4),
            "dentro_do_predio": dentro(u, cel, boot, u["local_id"], g4, rot4),
        },
        "regressao": {
            "modelo": "MQP por aptos com efeito fixo de município; coeficiente de 'bat' em "
            "pontos percentuais",
            "abstencao_2026": es.mqp_fe_municipio(
                dr, "abst_pct", ["bat"], "aptos", "cel"
            ),
            "dif_contra_2022": es.mqp_fe_municipio(
                dr.loc[dr["aptos_c"] > 0], "dif_abst_pp", ["bat"], "aptos_c", "cel"
            ),
        },
    }


# --- 4. Cadeia completa -----------------------------------------------------------------


def cadeia_completa(u: pd.DataFrame) -> dict[str, Any]:
    d = u.loc[u["relogio_ok"]].copy()
    mediana = d.groupby("mun_id")["abst_pct"].transform("median")
    d["abst_alta"] = d["abst_pct"] > mediana
    saida = {
        "regra": "urnas com log e relógio válidos; abstenção alta = acima da mediana das "
        "urnas do mesmo município (empate na mediana não conta como alta)",
        "variantes": {},
    }
    variantes = {
        "chuva_forte_no_dia": d["faixa_chuva"].isin(["forte", "muito_forte"]),
        "chuva_moderada_ou_mais_nas_horas_de_votacao": d["faixa_chuva_votacao"].isin(
            ["moderada", "forte", "muito_forte"]
        ),
    }
    for nome, chuva in variantes.items():
        celulas = []
        for c in (False, True):
            for b in (False, True):
                for a in (False, True):
                    m = (
                        (chuva == c)
                        & (d["bateria_votacao"] == b)
                        & (d["abst_alta"] == a)
                    )
                    celulas.append(
                        {
                            "chuva": c,
                            "bateria": b,
                            "abst_alta": a,
                            "urnas": int(m.sum()),
                            "aptos": int(d.loc[m, "aptos"].sum()),
                        }
                    )
        cond = []
        for c in (False, True):
            for b in (False, True):
                m = (chuva == c) & (d["bateria_votacao"] == b)
                n = int(m.sum())
                cond.append(
                    {
                        "chuva": c,
                        "bateria": b,
                        "urnas": n,
                        "abst_alta_pct": (
                            round(100 * d.loc[m, "abst_alta"].mean(), 2) if n else None
                        ),
                    }
                )
        saida["variantes"][nome] = {
            "celulas_2x2x2": celulas,
            "abst_alta_por_combinacao": cond,
        }
    return saida


# --- 6. Resumo por UF -------------------------------------------------------------------


def mapa_resumo(u: pd.DataFrame, locais: pd.DataFrame) -> list[dict[str, Any]]:
    linhas = []
    lc = locais.loc[locais["chuva_04_10_mm"].notna()]
    for uf, d in u.groupby("uf"):
        ll = lc.loc[lc["uf"] == uf]
        w = d["aptos"]
        rel = d["relogio_ok"]
        casada = d["aptos_c"] > 0
        linhas.append(
            {
                "uf": uf,
                "urnas": len(d),
                "aptos": int(w.sum()),
                "locais_com_clima": len(ll),
                "chuva_04_10_media_mm": round(
                    float((d["chuva_04_10_mm"] * w).sum() / w.sum()), 2
                ),
                "chuva_votacao_media_mm": round(
                    float((d["chuva_votacao_mm"] * w).sum() / w.sum()), 2
                ),
                "locais_chuva_forte_pct": (
                    round(
                        100
                        * float(
                            ll["faixa_chuva"].isin(["forte", "muito_forte"]).mean()
                        ),
                        2,
                    )
                    if len(ll)
                    else None
                ),
                "urnas_bateria_votacao_pct": round(
                    100 * float(d.loc[rel, "bateria_votacao"].mean()), 2
                ),
                "abst_pct": round(100 * float(d["abst"].sum() / w.sum()), 2),
                "dif_abst_pp": (
                    round(
                        100
                        * float(
                            d.loc[casada, "abst_c"].sum()
                            / d.loc[casada, "aptos_c"].sum()
                            - d.loc[casada, "abst22"].sum()
                            / d.loc[casada, "aptos22"].sum()
                        ),
                        2,
                    )
                    if casada.any()
                    else None
                ),
            }
        )
    return linhas
