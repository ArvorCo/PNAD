"""Consolidação medida: a terceira via derrete nas pesquisas, e para onde vai.

Regressão ponderada nos votos válidos dos placares publicados, com efeito fixo
por casa, sobre as ondas nacionais de uma janela recente. A inclinação comum
diz quantos pontos por dia cada bloco ganha ou perde dentro da mesma casa. A
divisão da migração é a parte da queda da terceira via que reaparece em
Flávio. Projetar a tendência até a urna é extrapolação linear de uma tendência
medida nas pesquisas, não medição da urna.
"""

from __future__ import annotations

from datetime import date

import numpy as np

from .recencia import midpoint

KEYS = ("lula", "flavio", "terceira_via")
WINDOWS = (28, 14)
N_CAP = 2000
NOTA = (
    "Extrapolação linear de uma tendência medida nas pesquisas, não medição da "
    "urna. A inclinação é comum às casas depois de remover o nível próprio de "
    "cada uma; casas com uma única onda na janela não informam a inclinação. "
    "A migração projetada sai da terceira via e se divide como nas pesquisas; "
    "λ é essa migração dividida pela reserva nacional de 2º turno de cada "
    "finalista, limitada a [0, 1]."
)


def valid_shares(poll, vector="publicado_vetor"):
    """Lula, Flávio e terceira via em pontos dos válidos."""
    x = np.array(poll[vector][:3], float)
    if not np.isfinite(x).all() or (x < 0).any() or x.sum() <= 0:
        raise ValueError(f"Vetor inválido em {poll.get('id')}")
    return 100 * x / x.sum()


def regression(polls, window, *, vector="publicado_vetor", cap=N_CAP):
    """Mínimos quadrados ponderados com efeito fixo de casa e tendência comum.

    y_ik = α_casa(i),k + β_k t_i + ε_ik, com t_i = −idade do ponto médio do
    campo e peso min(n, cap). Erro padrão clássico de MQP, com variância
    residual estimada pelos graus de liberdade restantes.
    """
    rows = [p for p in polls if p["idade_campo_dias"] <= window]
    houses = sorted({p["instituto"] for p in rows})
    counts = {h: sum(p["instituto"] == h for p in rows) for h in houses}
    if not rows or sum(c - 1 for c in counts.values()) < 2:
        raise ValueError(f"Janela de {window} dias sem ondas repetidas suficientes")
    x = np.zeros((len(rows), len(houses) + 1))
    for i, p in enumerate(rows):
        x[i, houses.index(p["instituto"])] = 1.0
        x[i, -1] = -float(p["idade_campo_dias"])
    y = np.array([valid_shares(p, vector) for p in rows])
    w = np.array([min(float(p["n"]), cap) for p in rows])
    root = np.sqrt(w)[:, None]
    xs, ys = x * root, y * root
    coef, *_ = np.linalg.lstsq(xs, ys, rcond=None)
    rank = int(np.linalg.matrix_rank(xs))
    dof = len(rows) - rank
    if dof <= 0:
        raise ValueError(f"Janela de {window} dias sem graus de liberdade")
    resid = ys - xs @ coef
    sigma = resid.T @ resid / dof
    # (X'WX)^-1 pela QR de √W·X: evita formar X'WX, mal condicionado.
    r_inv = np.linalg.inv(np.linalg.qr(xs, mode="r"))
    slope = coef[-1]
    cov = sigma * float(np.sum(r_inv[-1] ** 2))
    se = np.sqrt(np.diag(cov))
    return {
        "janela_dias": window,
        "n_ondas": len(rows),
        "n_casas": len(houses),
        "n_casas_com_repeticao": sum(c > 1 for c in counts.values()),
        "graus_liberdade": dof,
        "vetor": vector,
        "peso": f"min(n, {cap})",
        "pesos": {p["id"]: float(v) for p, v in zip(rows, w, strict=True)},
        "inclinacao_pp_dia": dict(zip(KEYS, map(float, slope), strict=True)),
        "erro_padrao_pp_dia": dict(zip(KEYS, map(float, se), strict=True)),
        "covariancia_flavio_terceira": float(cov[1, 2]),
        "divisao": split(slope, cov),
    }


def split(slope, cov):
    """Parte de Flávio na queda da terceira via, s = β_F / (−β_T), método delta."""
    b_f, b_t = float(slope[1]), float(slope[2])
    if b_t >= 0:
        return {"flavio": None, "lula": None, "erro_padrao": None, "derrete": False}
    s = -b_f / b_t
    grad = np.array([-1 / b_t, b_f / b_t**2])
    sub = np.array([[cov[1, 1], cov[1, 2]], [cov[2, 1], cov[2, 2]]])
    se = float(np.sqrt(max(0.0, grad @ sub @ grad)))
    return {"flavio": s, "lula": 1 - s, "erro_padrao": se, "derrete": True}


def national_reserve(states):
    """Reserva nacional de cada finalista, ponderada pelo eleitorado da UF."""
    total = sum(s["eleitorado"] for s in states)
    return [
        sum(s["reserva"][k] * s["eleitorado"] for s in states) / total for k in (0, 1)
    ]


def projection(fit, horizon, reserve):
    """Migração esperada até a urna, em pp dos válidos, e λ por finalista."""
    drop = max(0.0, -fit["inclinacao_pp_dia"]["terceira_via"])
    share = fit["divisao"]["flavio"]
    share = 0.0 if share is None else min(1.0, max(0.0, share))
    total = drop * horizon
    moved = {"lula": total * (1 - share), "flavio": total * share}
    lam, cap = {}, {}
    for k, r in zip(("lula", "flavio"), reserve, strict=True):
        need = moved[k] / 100
        cap[k] = bool(need > r)
        lam[k] = min(1.0, need / r) if r > 0 else 0.0
    return {
        "queda_terceira_pp_dia": drop,
        "parte_flavio_usada": share,
        "migracao_total_pp": total,
        "migracao_pp": moved,
        "lambda": lam,
        "lambda_arredondado": {k: round(v, 2) for k, v in lam.items()},
        "teto_atingido": cap,
    }


ANCHOR = "inclusivo"
NOTA_ANCORA = (
    "Os cenários de consolidação partem da âncora de recência sem tendência "
    "(inclusivo). A central já projeta a queda da terceira via até a urna pela "
    "inclinação encolhida; aplicar a consolidação sobre ela contaria a mesma "
    "migração duas vezes."
)


def anchor_start(selected):
    """Data efetiva da âncora inclusivo: ponto médio do campo ponderado pela
    participação de cada casa na média por recência sem tendência."""
    total = sum(p["participacao_central_pct"] for p in selected)
    return (
        sum(midpoint(p["campo"]) * p["participacao_central_pct"] for p in selected)
        / total
    )


def consolidation(polls, selected, states, today, election):
    """Bloco "consolidacao" do JSON principal."""
    start = anchor_start(selected)
    age = today.toordinal() - start
    anchor = date.fromordinal(round(start))
    horizon = election.toordinal() - start
    reserve = national_reserve(states)
    fits = {str(win): regression(polls, win) for win in WINDOWS}
    return {
        "natureza": "Extrapolação linear de tendência medida nas pesquisas",
        "nota": NOTA,
        "ancora": ANCHOR,
        "nota_ancora": NOTA_ANCORA,
        "janelas": fits,
        "idade_efetiva_ancora_dias": age,
        "data_efetiva_ancora": anchor.isoformat(),
        "horizonte_dias": horizon,
        "reserva_nacional_pct": {
            "lula": 100 * reserve[0],
            "flavio": 100 * reserve[1],
        },
        "projecao": {
            key: projection(fit, horizon, reserve) for key, fit in fits.items()
        },
    }
