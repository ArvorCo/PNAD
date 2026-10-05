"""Pergunta 3 do fechamento: o que o encerramento tardio tem a ver com o voto.

Três réguas para a mesma pergunta, todas sobre a % de Lula e de Flávio nos
válidos da seção, no mesmo conjunto de seções (válidas, das UFs completas, com
hora de encerramento):

- bruta: percentual agregado por faixa de hora de encerramento, sem controle;
- dentro da zona: regressão ponderada pelos votantes com efeito fixo de zona,
  por faixa (contra 17:00 a 17:30) e contínua (pontos por hora de atraso);
- dentro da zona com controle de tamanho (aptos em faixas) e de tipo de local
  inferido (aldeia, zona rural, unidade prisional, outro).

Mais o estimador do modelo de urna (seção tardia contra as demais da mesma
zona) para fila, comparecimento e habilitação, e a conferência do número já
publicado na análise por seção. Correlação dentro da zona não identifica
mecanismo; só ata e log da urna separam fila, biometria e irregularidade.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd

from . import secoes_base
from .fechamento_base import FAIXAS_APTOS, FAIXAS_HORA, ORDEM_TIPO, spearman
from .fechamento_modelo import (
    dentro_zona,
    dif_secao_contra_demais,
    dif_zona_w6,
    dummies,
    fe_wls,
)
from .secoes_base import FLAVIO, LULA, pct, r2

REGIOES = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
FAIXAS_VOTANTES: list[tuple[str, int, int | None]] = [
    ("até 149", 0, 149),
    ("150 a 199", 150, 199),
    ("200 a 249", 200, 249),
    ("250 a 299", 250, 299),
    ("300 a 349", 300, 349),
    ("350 ou mais", 350, None),
]
REF_VOTANTES = "200 a 249"
REF_HORA = "17:00 a 17:30"
REF_APTOS = "300 a 349"
REF_TIPO = "escola fora de zona rural"
CORTE_TARDE = 60  # 18h
CORTE_W6 = 120  # 19h, o corte publicado na análise por seção
DECIL_RECEBIMENTO = 0.9

METRICAS_2026: dict[str, tuple[str, ...]] = {
    "lula_pp": (f"v{LULA}", "validos"),
    "flavio_pp": (f"v{FLAVIO}", "validos"),
    "comparecimento_pp": ("comparecimento", "aptos"),
    "votantes_secao": ("comparecimento", "cem"),
    "votantes_hora": ("comparecimento", "horas_x100"),
    "ano_nascimento_pp": ("hab_ano_nascimento", "comparecimento"),
    "sem_biometria_pp": ("comp_sem_biometria", "comparecimento"),
}
METRICAS_RECEBIMENTO_2026 = {
    k: METRICAS_2026[k]
    for k in ("lula_pp", "flavio_pp", "comparecimento_pp", "votantes_secao")
}
METRICAS_2022: dict[str, tuple[str, ...]] = {
    "lula_pp": ("lula_1t", "nominais_1t"),
    "flavio_pp": ("bolsonaro_1t", "nominais_1t"),
    "comparecimento_pp": ("comparecimento_2022", "aptos_2022"),
    "votantes_secao": ("comparecimento_2022", "cem"),
}
ROTULO_METRICA = {
    "lula_pp": "Lula, % dos válidos",
    "flavio_pp": "Flávio, % dos válidos (Bolsonaro em 2022)",
    "comparecimento_pp": "comparecimento, % dos aptos",
    "votantes_secao": "votantes por seção",
    "votantes_hora": "votantes por hora de urna aberta",
    "ano_nascimento_pp": "habilitados por ano de nascimento, % dos votantes",
    "sem_biometria_pp": "sem biometria cadastrada, % dos votantes",
}


def base_voto(d26: pd.DataFrame, completas: list[str]) -> pd.DataFrame:
    """Seções válidas das UFs completas, com voto e hora de encerramento."""
    comp = {u.lower() for u in completas}
    v = d26[
        d26["valida"]
        & d26["uf"].isin(comp)
        & (d26["validos"] > 0)
        & d26["enc_min"].notna()
    ].copy()
    v["zona_id"] = v["uf"] + "-" + v["mun"] + "-" + v["zona"].astype(str)
    v["horas_atraso"] = v["enc_min"] / 60
    return v


# ---------------------------------------------------------------- estimadores


def estimadores(
    v: pd.DataFrame, d22: pd.DataFrame, completas: list[str]
) -> list[dict[str, Any]]:
    out = []

    def junta(ident: str, rotulo: str, ano: int, definicao: str, unidade: str, r):
        out.append(
            {
                "id": ident,
                "rotulo": rotulo,
                "ano": ano,
                "definicao_tarde": definicao,
                "unidade": unidade,
                "resultado": r,
            }
        )

    tarde18 = v["enc_min"] >= CORTE_TARDE
    junta(
        "tarde18_zona",
        "encerrou às 18h ou depois, contra as demais da mesma zona",
        2026,
        "encerramento (último voto) às 18h de Brasília ou depois",
        "zona",
        dentro_zona(v, tarde18, METRICAS_2026),
    )
    junta(
        "tarde18_zona_tamanho",
        "o mesmo, dentro da zona e da mesma faixa de eleitorado apto",
        2026,
        "encerramento às 18h de Brasília ou depois",
        "zona e faixa de aptos",
        dentro_zona(
            v, tarde18, METRICAS_2026, unidade=("uf", "mun", "zona", "faixa_aptos")
        ),
    )
    junta(
        "tarde19_zona",
        "encerrou às 19h ou depois, contra as demais da mesma zona",
        2026,
        "encerramento às 19h de Brasília ou depois",
        "zona",
        dentro_zona(v, v["enc_min"] >= CORTE_W6, METRICAS_2026),
    )
    corte26 = float(v["rec_min"].quantile(DECIL_RECEBIMENTO))
    junta(
        "recebimento_decil_2026",
        "chegou ao TSE no décimo mais tardio de 2026, contra as demais da zona",
        2026,
        f"recebimento a partir de {r2(corte26, 1)} minutos depois das 17h (p90 de 2026)",
        "zona",
        dentro_zona(v, v["rec_min"] >= corte26, METRICAS_RECEBIMENTO_2026),
    )
    comp = {u.lower() for u in completas}
    w = d22[d22["uf"].isin(comp) & d22["rec_min"].notna()].copy()
    w["votantes"] = w["comparecimento_2022"]
    corte22 = float(w["rec_min"].quantile(DECIL_RECEBIMENTO)) if len(w) else None
    junta(
        "recebimento_decil_2022",
        "chegou ao TSE no décimo mais tardio de 2022, contra as demais da zona",
        2022,
        f"recebimento a partir de {r2(corte22, 1)} minutos depois das 17h (p90 de 2022)",
        "zona",
        dentro_zona(w, w["rec_min"] >= corte22, METRICAS_2022) if len(w) else None,
    )
    return out


# ---------------------------------------------------------------- Lula e hora


def _bruta(g: pd.DataFrame, grupo: str) -> list[dict[str, Any]]:
    linhas = []
    for nome, _lo, _hi in FAIXAS_HORA:
        x = g[g["faixa_hora"] == nome]
        validos = int(x["validos"].sum())
        linhas.append(
            {
                "grupo": grupo,
                "faixa": nome,
                "secoes": len(x),
                "votantes": int(x["comparecimento"].sum()),
                "validos": validos,
                "lula_pct": pct(int(x[f"v{LULA}"].sum()), validos),
                "flavio_pct": pct(int(x[f"v{FLAVIO}"].sum()), validos),
            }
        )
    return linhas


def _controles(v: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    ordem_aptos = [n for n, _lo, _hi in FAIXAS_APTOS]
    ma, na = dummies(v["faixa_aptos"], REF_APTOS, ordem_aptos)
    mt, nt = dummies(v["grupo_tipo"], REF_TIPO, ORDEM_TIPO)
    return np.column_stack([ma, mt]), [f"aptos {n}" for n in na] + nt


def _modelo(
    v: pd.DataFrame, y: str, x: np.ndarray, nomes: list[str], fe: bool
) -> dict[str, Any] | None:
    return fe_wls(
        v[y].to_numpy(),
        x,
        v["zona_id"].to_numpy(),
        v["comparecimento"].to_numpy(dtype=float),
        nomes,
        absorver=fe,
    )


def _so(r: dict[str, Any] | None, nomes: list[str]) -> dict[str, Any] | None:
    """Só os coeficientes de interesse (sem os de controle)."""
    if r is None:
        return None
    return {**r, "coeficientes": {n: r["coeficientes"][n] for n in nomes}}


def correlacao_lula(v: pd.DataFrame) -> dict[str, Any]:
    bruta = _bruta(v, "Brasil")
    for rg in REGIOES:
        g = v[v["regiao"] == rg]
        if len(g):
            bruta += _bruta(g, rg)
    ordem_hora = [n for n, _lo, _hi in FAIXAS_HORA]
    mh, nh = dummies(v["faixa_hora"], REF_HORA, ordem_hora)
    mc, nc = _controles(v)
    xc = np.column_stack([mh, mc])
    hora = v[["horas_atraso"]].to_numpy()
    xhc = np.column_stack([hora, mc])
    por_faixa, inclinacao = [], []
    for ident, rotulo, fe, ctl in (
        ("bruta", "bruta, sem controle", False, False),
        ("zona", "dentro da zona", True, False),
        (
            "zona_controles",
            "dentro da zona, com tamanho e tipo de local",
            True,
            True,
        ),
    ):
        lin_f: dict[str, Any] = {"id": ident, "rotulo": rotulo}
        lin_i: dict[str, Any] = {"id": ident, "rotulo": rotulo}
        for cand, col in (("lula", "lula_pct"), ("flavio", "flavio_pct")):
            if ctl:
                rf = _modelo(v, col, xc, nh + nc, fe)
                ri = _modelo(v, col, xhc, ["horas_atraso", *nc], fe)
            else:
                rf = _modelo(v, col, mh, nh, fe)
                ri = _modelo(v, col, hora, ["horas_atraso"], fe)
            lin_f[cand] = _so(rf, nh)
            lin_i[cand] = _so(ri, ["horas_atraso"])
        por_faixa.append(lin_f)
        inclinacao.append(lin_i)

    def sobra(cand: str, chave: str, lista: list[dict[str, Any]]) -> float | None:
        try:
            b = lista[0][cand]["coeficientes"][chave]["estimativa"]
            c = lista[2][cand]["coeficientes"][chave]["estimativa"]
        except (KeyError, TypeError):
            return None
        return r2(100 * c / b, 1) if b else None

    return {
        "conjunto": "seções válidas das UFs completas com hora de encerramento",
        "secoes": len(v),
        "zonas": int(v["zona_id"].nunique()),
        "faixas": [
            {
                "rotulo": n,
                "min_min": None if lo == -np.inf else lo,
                "max_min": None if hi == np.inf else hi,
            }
            for n, lo, hi in FAIXAS_HORA
        ],
        "referencia": REF_HORA,
        "controles": {
            "tamanho": f"faixas de eleitorado apto, referência {REF_APTOS}",
            "tipo": f"tipo de local inferido, referência {REF_TIPO}",
            "colunas": nc,
        },
        "peso": "votantes (comparecimento) da seção",
        "bruta": bruta,
        "por_faixa": por_faixa,
        "inclinacao": inclinacao,
        "sobrevive_pct": {
            "lula_inclinacao": sobra("lula", "horas_atraso", inclinacao),
            "flavio_inclinacao": sobra("flavio", "horas_atraso", inclinacao),
            "lula_depois_19h": sobra("lula", "depois de 19:00", por_faixa),
            "flavio_depois_19h": sobra("flavio", "depois de 19:00", por_faixa),
        },
        "spearman": {
            "brasil_lula": r2(spearman(v["enc_min"], v["lula_pct"]), 3),
            "brasil_flavio": r2(spearman(v["enc_min"], v["flavio_pct"]), 3),
        },
        "spearman_uf": spearman_uf(v),
    }


def spearman_uf(v: pd.DataFrame) -> list[dict[str, Any]]:
    out = []
    for uf, g in v.groupby("uf"):
        out.append(
            {
                "uf": str(uf).upper(),
                "regiao": g["regiao"].iloc[0],
                "secoes": len(g),
                "secoes_depois_1800": int((g["enc_min"] >= CORTE_TARDE).sum()),
                "rho_lula": r2(spearman(g["enc_min"], g["lula_pct"]), 3),
                "rho_flavio": r2(spearman(g["enc_min"], g["flavio_pct"]), 3),
            }
        )
    return sorted(
        out, key=lambda r: -(r["rho_lula"] if r["rho_lula"] is not None else -9)
    )


def conferencia_w6(
    v_todas: pd.DataFrame, secoes_json: Mapping[str, Any] | None
) -> dict[str, Any]:
    """Refaz o número publicado na análise por seção e o compara com o estimador."""
    publicado = None
    ufs_w6: list[str] = []
    if secoes_json:
        h = (secoes_json.get("outras") or {}).get("horarios") or {}
        publicado = next(
            (
                x
                for x in h.get("voto_vs_zona") or []
                if x.get("grupo") == "encerramento_depois_19h"
            ),
            None,
        )
        cob = secoes_json.get("cobertura") or {}
        ufs_w6 = list(cob.get("ufs_completas") or [])
        publicado = publicado and {
            "secoes": publicado.get("secoes"),
            "lula_pp": publicado.get("dif_zona_lula_pp"),
            "flavio_pp": publicado.get("dif_zona_flavio_pp"),
            "gerado_em": secoes_json.get("gerado_em"),
            "secoes_validas_na_base": cob.get("secoes_validas"),
            "ufs_completas_na_base": ufs_w6,
        }
    out: dict[str, Any] = {"publicado_secoes_json": publicado}
    for nome, sub in (
        ("base_atual", v_todas),
        (
            "base_atual_mesmas_ufs",
            v_todas[v_todas["uf"].str.upper().isin(ufs_w6)] if ufs_w6 else None,
        ),
    ):
        if sub is None or sub.empty:
            out[nome] = None
            continue
        tarde = sub["enc_min"] >= CORTE_W6
        g = sub[tarde]
        est = dentro_zona(
            sub,
            tarde,
            {k: METRICAS_2026[k] for k in ("lula_pp", "flavio_pp")},
        )
        out[nome] = {
            "secoes_depois_19h": int(tarde.sum()),
            "formula_secao_contra_resto": {
                "lula_pp": dif_zona_w6(g, "lula"),
                "flavio_pp": dif_zona_w6(g, "flavio"),
            },
            "formula_secao_contra_demais": {
                "lula_pp": dif_secao_contra_demais(sub, tarde, "lula"),
                "flavio_pp": dif_secao_contra_demais(sub, tarde, "flavio"),
            },
            "estimador_zona": est,
        }
    out["diferenca_de_metodo"] = (
        "A análise por seção compara cada seção tardia com o resto da própria zona, "
        "inclusive as outras seções tardias, e pondera pelos válidos da seção. O "
        "estimador deste capítulo compara o agregado das seções tardias com o das "
        "demais na mesma zona, pondera pelos votantes das duas partes e deixa fora a "
        "zona sem os dois grupos. Os dois medem a mesma coisa por caminhos diferentes; "
        "a diferença entre eles é de método e de base, não de dado."
    )
    return out


# ---------------------------------------------------------------- explicações


def modelo_atraso(v: pd.DataFrame) -> dict[str, Any]:
    """Probabilidade linear de fechar às 18h ou depois, com efeito fixo de zona."""
    v = v.dropna(subset=["ano_nascimento_pct", "sem_biometria_pct"])
    y = 100.0 * (v["enc_min"] >= CORTE_TARDE).to_numpy(dtype=float)
    fx = pd.Series(faixa_votantes(v["comparecimento"]), index=v.index)
    mv, nv = dummies(fx, REF_VOTANTES, [n for n, _lo, _hi in FAIXAS_VOTANTES])
    nv = [f"votantes {n}" for n in nv]
    ano = v["ano_nascimento_pct"].to_numpy(dtype=float)
    sem = v["sem_biometria_pct"].to_numpy(dtype=float)
    mt, nt = dummies(v["grupo_tipo"], REF_TIPO, ORDEM_TIPO)
    um = np.ones(len(v))
    zona = v["zona_id"].to_numpy()
    so_tamanho = fe_wls(y, mv, zona, um, nv)
    completo = fe_wls(
        y,
        np.column_stack([mv, ano, sem, mt]),
        zona,
        um,
        [*nv, "ano_nascimento_pp", "sem_biometria_pp", *nt],
    )
    return {
        "variavel": "100 se a seção encerrou às 18h de Brasília ou depois, 0 se não",
        "unidades": {
            "votantes": f"faixa de votantes da seção contra {REF_VOTANTES}",
            "ano_nascimento_pp": "cada ponto a mais de habilitados por ano de nascimento",
            "sem_biometria_pp": "cada ponto a mais de votantes sem biometria cadastrada",
            "tipo": f"contra {REF_TIPO}",
        },
        "media_pct": r2(float(y.mean()), 2),
        "so_tamanho": so_tamanho,
        "completo": completo,
    }


def explicacoes(
    v: pd.DataFrame, principais: pd.DataFrame, ests: list[dict[str, Any]]
) -> dict[str, Any]:
    e = {x["id"]: x["resultado"] for x in ests}
    return {
        "modelo_atraso": modelo_atraso(v),
        "fila": {
            "teste": (
                "votantes por seção e votantes por hora de urna aberta, seção tardia "
                "contra as demais da zona; parcela de seções tardias por faixa de aptos"
            ),
            "zona": e.get("tarde18_zona"),
            "zona_tamanho": e.get("tarde18_zona_tamanho"),
        },
        "identificacao": {
            "teste": (
                "parcela dos votantes habilitados por ano de nascimento (biometria "
                "cadastrada que não foi reconhecida) e sem biometria cadastrada, do "
                "próprio boletim"
            ),
            "idade": (
                "sem dado nacional de idade por seção: o perfil do eleitorado por seção "
                "de 2026 no acervo só cobre o Acre"
            ),
        },
        "irregularidade": {
            "testavel_com_bu": False,
            "secoes_com_hash_do_log": int(principais["com_hash_log"].sum()),
            "secoes_principais": int(principais["principais"].sum()),
        },
    }


def amostras(v: pd.DataFrame) -> dict[str, list[dict[str, Any]]]:
    extra = [
        "enc_min",
        "rec_min",
        "horas",
        "votantes_hora",
        "ano_nascimento_pct",
        "sem_biometria_pct",
    ]
    tarde = v.sort_values("enc_min", ascending=False)
    ano = v[(v["enc_min"] >= CORTE_W6) & (v["comparecimento"] >= 100)].sort_values(
        "ano_nascimento_pct", ascending=False
    )
    return {
        "encerramento_mais_tarde": secoes_base.amostras(tarde, 25, extra),
        "tarde_ano_nascimento": secoes_base.amostras(ano, 20, extra),
    }


def faixa_votantes(votantes: pd.Series) -> list[str | None]:
    out: list[str | None] = []
    for x in votantes:
        rot = None
        if pd.notna(x):
            for nome, lo, hi in FAIXAS_VOTANTES:
                if x >= lo and (hi is None or x <= hi):
                    rot = nome
                    break
        out.append(rot)
    return out
