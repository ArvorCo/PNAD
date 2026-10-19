"""Comparações do 1º turno com IC por bootstrap: comportamento, intercorrências e efeito.

Unidade: urna (seção principal) com boletim, só Brasil (o exterior fica fora das
comparações nacionais, regra da casa). Grupos:

- ``mudanca_real``: urnas com mudança real de prédio entre os turnos; ``A`` (volta ao
  original) e ``novas`` (B, C, X, D e E reais).
- ``temp_1t``: urnas que votaram em 04/10 em local diferente do original no cadastro.
- ``troca``: urnas com o mesmo número de local de 2022, mas prédio com nome sem
  nenhuma palavra em comum com o de 2022 (o TRE reescreveu o registro do local).
- ``est``: urnas no mesmo número e com nome compatível com o de 2022 (controle limpo
  para a diferença em diferenças).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from mudancas_secoes_2t import endereco as en
from mudancas_secoes_2t import estatistica as es

CORTE_ESTAVEL = 0.34
FAIXAS_A = [
    (0, 500, "até 500 m"),
    (500, 1000, "500 m a 1 km"),
    (1000, 2000, "1 a 2 km"),
    (2000, 5000, "2 a 5 km"),
    (5000, float("inf"), "acima de 5 km"),
]
SEM_FAIXA = len(FAIXAS_A)
COLUNAS = [
    "aptos",
    "comp",
    "abst_num",
    "validos",
    "flavio",
    "lula",
    "terceira",
    "brancos",
    "nulos",
    "aptos_m",
    "abst_m",
    "aptos22",
    "abst22",
    "log_ok",
    "bateria",
    "bateria_votacao",
    "reinicio",
    "hora_ok",
    "abertura_atrasada",
    "fim_ok",
    "fila_fechamento",
    "atencao_23",
]
COL = {c: i for i, c in enumerate(COLUNAS)}
METRICAS_VOTO: dict[str, es.Metrica] = {
    "abstencao": ("razao", "abst_num", "aptos"),
    "flavio_validos": ("razao", "flavio", "validos"),
    "lula_validos": ("razao", "lula", "validos"),
    "brancos": ("razao", "brancos", "comp"),
    "nulos": ("razao", "nulos", "comp"),
}
METRICAS_INTERC: dict[str, es.Metrica] = {
    "bateria": ("razao", "bateria", "log_ok"),
    "bateria_votacao": ("razao", "bateria_votacao", "log_ok"),
    "reinicio": ("razao", "reinicio", "log_ok"),
    "abertura_atrasada": ("razao", "abertura_atrasada", "hora_ok"),
    "fila_fechamento": ("razao", "fila_fechamento", "fim_ok"),
    "atencao_2_ou_3": ("razao", "atencao_23", "log_ok"),
}
DD: es.Metrica = ("dif_razao", "abst_m", "aptos_m", "abst22", "aptos22")
ABST_M: es.Metrica = ("razao", "abst_m", "aptos_m")
ABST_22: es.Metrica = ("razao", "abst22", "aptos22")


def faixa_distancia(d: float | None) -> int:
    if d is None or not np.isfinite(d):
        return SEM_FAIXA
    for i, (lo, hi, _) in enumerate(FAIXAS_A):
        if lo <= d < hi:
            return i
    return SEM_FAIXA


def preparar(urnas: pd.DataFrame) -> pd.DataFrame:
    """Urnas do Brasil com boletim, marcas de grupo, colunas somáveis e célula."""
    u = urnas[(urnas["uf"] != "ZZ") & urnas["tem_bu"]].copy()
    real = u["mudanca_real"].astype(bool)
    u["mud"] = np.select([real & (u["categoria"] == "A"), real], ["A", "N"], "0")
    u["t1"] = u["temp_1t"].astype(bool)
    casada = (u["aptos_2022_2t"] > 0) & u["comp_2022_2t"].notna()
    mesmo_nr = u["local_nr_2022"] == u["local_1t"]
    sim = np.array(
        [
            en.semelhanca_nomes(a, b) if isinstance(a, str) else np.nan
            for a, b in zip(u["local_2022"], u["nome_1t"], strict=True)
        ]
    )
    u["sim_nome_2022"] = sim
    u["dd"] = u["t1"] & casada & (u["local_nr_2022"] == u["original_1t"])
    g22 = np.select(
        [
            u["t1"],
            ~casada,
            ~mesmo_nr,
            sim >= CORTE_ESTAVEL,
            sim == 0,
        ],
        ["tmp", "nc", "outro_nr", "est", "troca"],
        "amb",
    )
    u["g22"] = g22
    usa22 = u["dd"] | np.isin(g22, ["est", "troca"])
    dist_ok = ~u["distancia_suspeita"].astype(bool) & ~u["coord_repetida"].astype(bool)
    u["faixa"] = [
        faixa_distancia(d) if (m == "A" and ok) else (SEM_FAIXA if m == "A" else -1)
        for d, m, ok in zip(u["distancia_m"], u["mud"], dist_ok, strict=True)
    ]
    u["comp"] = u["comparecimento"]
    u["abst_num"] = u["aptos"] - u["comparecimento"]
    u["aptos_m"] = np.where(usa22, u["aptos"], 0)
    u["abst_m"] = np.where(usa22, u["abst_num"], 0)
    u["aptos22"] = np.where(usa22, u["aptos_2022_2t"], 0)
    u["abst22"] = np.where(usa22, u["aptos_2022_2t"] - u["comp_2022_2t"], 0)
    u["atencao_23"] = u["atencao_23"].eq(True) & u["log_ok"]
    for c in COLUNAS:
        u[c] = pd.to_numeric(u[c], errors="coerce").fillna(0).astype(float)
    rotulo = (
        u["mud"]
        + "|"
        + u["t1"].astype(int).astype(str)
        + "|"
        + u["dd"].astype(int).astype(str)
        + "|"
        + u["g22"]
        + "|"
        + u["faixa"].astype(str)
    )
    u["celula"], _ = pd.factorize(rotulo, sort=True)
    return u.reset_index(drop=True)


def celulas(u: pd.DataFrame) -> pd.DataFrame:
    c = u.groupby("celula")[["mud", "t1", "dd", "g22", "faixa"]].first()
    return c.sort_index()


def grupos_celula(cel: pd.DataFrame) -> dict[str, np.ndarray]:
    """Cada grupo é um conjunto de células (máscara sobre os ids de célula)."""
    g = {
        "mudanca_real": (cel["mud"] != "0").to_numpy(),
        "A": (cel["mud"] == "A").to_numpy(),
        "novas": (cel["mud"] == "N").to_numpy(),
        "temp_1t": cel["t1"].to_numpy(),
        "temp_1t_dd": (cel["t1"] & cel["dd"]).to_numpy(),
        "est": ((~cel["t1"]) & (cel["g22"] == "est")).to_numpy(),
        "troca": ((~cel["t1"]) & (cel["g22"] == "troca")).to_numpy(),
        "transferida": (cel["t1"] | (cel["g22"] == "troca")).to_numpy(),
    }
    for b in range(SEM_FAIXA + 1):
        a = (cel["mud"] == "A") & (cel["faixa"] == b)
        g[f"A_faixa_{b}"] = a.to_numpy()
        g[f"A_faixa_{b}_dd"] = (a & cel["dd"]).to_numpy()
    return g


@dataclass
class Tarefa:
    chave: str
    trat: str
    ctrl: str | None
    metrica: es.Metrica
    peso: str


@dataclass
class Passada:
    """Uma reamostragem: estratos (unidade × célula) e os grupos agregados por unidade."""

    reamostragem: es.Reamostragem
    unidade_estrato: np.ndarray
    celula_estrato: np.ndarray
    m: int
    nomes_unidade: list[Any] = field(default_factory=list)


def montar_passada(
    u: pd.DataFrame, unidade: pd.Series | None, reps: int, seed: int
) -> Passada:
    """Estratos = unidade (município, zona ou o país inteiro) × célula."""
    if unidade is None:
        unid = np.zeros(len(u), dtype=np.int64)
        nomes: list[Any] = ["BR"]
    else:
        unid, uniq = pd.factorize(unidade, sort=True)
        nomes = list(uniq)
    par = unid.astype(np.int64) * (int(u["celula"].max()) + 1) + u["celula"].to_numpy()
    est, uniq_par = pd.factorize(par, sort=True)
    ncel = int(u["celula"].max()) + 1
    re = es.Reamostragem(est, u[COLUNAS].to_numpy(float), reps, seed)
    return Passada(re, uniq_par // ncel, uniq_par % ncel, len(nomes), nomes)


def rodar(
    p: Passada, grupos: dict[str, np.ndarray], tarefas: list[Tarefa]
) -> dict[str, dict[str, Any]]:
    """Ponto e réplicas de cada tarefa, numa passada só pelas réplicas."""
    nomes = sorted({t.trat for t in tarefas} | {t.ctrl for t in tarefas if t.ctrl})
    mats = {
        g: es.agregador(p.unidade_estrato, grupos[g][p.celula_estrato], p.m)
        for g in nomes
    }
    total = es.agregador(p.unidade_estrato, np.ones(len(p.celula_estrato), bool), p.m)

    def avaliar(somas: np.ndarray) -> dict[str, tuple[np.ndarray, np.ndarray]]:
        tot = es.agregar(somas, total)
        agg = {g: es.agregar(somas, mats[g]) for g in nomes}
        return {
            t.chave: (agg[t.trat], agg[t.ctrl] if t.ctrl else tot - agg[t.trat])
            for t in tarefas
        }

    ponto = avaliar(p.reamostragem.pontual())
    usar = {
        t.chave: es.avaliaveis(*ponto[t.chave], t.metrica, t.peso, COL) for t in tarefas
    }
    saida: dict[str, dict[str, Any]] = {}
    for t in tarefas:
        tr, ct = ponto[t.chave]
        vt, vc = es.ponderada_mun(tr, ct, t.metrica, t.peso, COL, usar[t.chave])
        saida[t.chave] = {
            "vt": float(vt[0]),
            "vc": float(vc[0]),
            "rt": [],
            "rc": [],
            "unidades": int(usar[t.chave].sum()),
            "cobertura_peso": _cobertura(tr, usar[t.chave], t.peso),
            "n_trat": float(tr[0, :, COL["aptos"]].sum()),
        }
    for somas in p.reamostragem.replicas():
        bloco = avaliar(somas)
        for t in tarefas:
            vt, vc = es.ponderada_mun(
                *bloco[t.chave], t.metrica, t.peso, COL, usar[t.chave]
            )
            saida[t.chave]["rt"].append(vt)
            saida[t.chave]["rc"].append(vc)
    for v in saida.values():
        v["rt"] = np.concatenate(v["rt"]) if v["rt"] else np.array([])
        v["rc"] = np.concatenate(v["rc"]) if v["rc"] else np.array([])
    return saida


def _cobertura(tr: np.ndarray, usar: np.ndarray, peso: str) -> float | None:
    tot = tr[0, :, COL[peso]].sum()
    return None if tot <= 0 else round(float(tr[0, usar, COL[peso]].sum() / tot), 4)


def formatar(
    r: dict[str, Any], razao: bool = False, escala: float = 100.0
) -> dict[str, Any]:
    """Grupo, controles e diferença em pontos (e razão, quando pedida), com IC."""
    out = {
        "grupo": es.resumo_ic(r["vt"], r["rt"], escala),
        "controles": es.resumo_ic(r["vc"], r["rc"], escala),
        "diferenca_pp": es.resumo_ic(r["vt"] - r["vc"], r["rt"] - r["rc"], escala),
        "unidades_comparadas": r["unidades"],
        "cobertura_do_grupo": r["cobertura_peso"],
    }
    if razao:
        with np.errstate(divide="ignore", invalid="ignore"):
            rr = r["rt"] / r["rc"]
            ponto = r["vt"] / r["vc"] if r["vc"] else float("nan")
        out["razao"] = es.resumo_ic(ponto, rr, 1.0, 3)
    return out


def tarefas_padrao(
    grupos: list[str], metricas: dict[str, es.Metrica], prefixo: str, peso: Callable
) -> list[Tarefa]:
    return [
        Tarefa(f"{prefixo}|{g}|{m}", g, None, met, peso(met))
        for g in grupos
        for m, met in metricas.items()
    ]


def _peso_voto(met: es.Metrica) -> str:
    return "aptos"


def _peso_parcela(met: es.Metrica) -> str:
    return met[2]


def tarefas_todas() -> list[Tarefa]:
    t = tarefas_padrao(
        ["mudanca_real", "A", "novas"], METRICAS_VOTO, "comp", _peso_voto
    )
    t += tarefas_padrao(
        ["mudanca_real", "A", "novas", "temp_1t"],
        METRICAS_INTERC,
        "interc",
        _peso_parcela,
    )
    t += tarefas_padrao(["temp_1t"], METRICAS_VOTO, "efeito", _peso_voto)
    t += tarefas_padrao(["troca"], METRICAS_VOTO, "efeito_troca_todas", _peso_voto)
    for g in ("temp_1t_dd", "troca"):
        for nome, met in (("dd", DD), ("abst_2026", ABST_M), ("abst_2022", ABST_22)):
            t.append(Tarefa(f"dd|{g}|{nome}", g, "est", met, "aptos_m"))
    for g in ("troca",):
        for nome, met in METRICAS_VOTO.items():
            t.append(Tarefa(f"efeito_troca|{g}|{nome}", g, "est", met, "aptos"))
    for b in range(SEM_FAIXA + 1):
        t.append(
            Tarefa(
                f"dose|{b}|abst",
                f"A_faixa_{b}",
                None,
                METRICAS_VOTO["abstencao"],
                "aptos",
            )
        )
        t.append(Tarefa(f"dose|{b}|dd", f"A_faixa_{b}_dd", "est", DD, "aptos_m"))
    return t


def por_predio(u: pd.DataFrame, chave: list[str]) -> pd.DataFrame:
    """Soma as urnas de um mesmo prédio do 1º turno e célula: a unidade reamostrada.

    Seções do mesmo prédio dividem o mesmo evento (queda de energia, fila, troca de
    local), então reamostrar seção a seção subestimaria a incerteza; o bootstrap
    reamostra prédios (conglomerados). As somas, e portanto os pontos, não mudam.
    """
    g = u.groupby([*chave, "local_1t", "celula"], sort=True, as_index=False)
    out = g[COLUNAS].sum()
    out["urnas"] = g.size()["size"].to_numpy()
    return out


def executar(u: pd.DataFrame, reps: int, seed: int) -> dict[str, Any]:
    """As duas passadas: dentro do município e contra o país, por prédio."""
    cel = celulas(u)
    grupos = grupos_celula(cel)
    tarefas = tarefas_todas()
    trat_cel = (cel["mud"] != "0") | cel["t1"] | (cel["g22"] == "troca")
    mun_alvo = set(
        u.loc[u["celula"].isin(cel.index[trat_cel]), ["uf", "mun"]].apply(tuple, axis=1)
    )
    chave_mun = list(zip(u["uf"], u["mun"], strict=True))
    sub = u[[c in mun_alvo for c in chave_mun]].reset_index(drop=True)
    pred_sub = por_predio(sub, ["uf", "mun", "zona"])
    pred = por_predio(u, ["uf", "mun", "zona"])
    p_mun = montar_passada(pred_sub, pred_sub["uf"] + "-" + pred_sub["mun"], reps, seed)
    p_pais = montar_passada(pred, None, reps, seed + 1)
    return {
        "mun": rodar(p_mun, grupos, tarefas),
        "pais": rodar(p_pais, grupos, tarefas),
        "urnas_municipios_alvo": len(sub),
        "predios_municipios_alvo": len(pred_sub),
        "predios": len(pred),
        "municipios_alvo": len(mun_alvo),
        "celulas": len(cel),
        "unidade": "prédio do 1º turno × célula (conglomerado de urnas)",
    }


def bloco(res: dict[str, Any], chave: str, razao: bool = False) -> dict[str, Any]:
    return {
        "mesmo_municipio": formatar(res["mun"][chave], razao),
        "pais": formatar(res["pais"][chave], razao),
    }
