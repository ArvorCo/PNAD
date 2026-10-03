"""Validação de origem móvel: quanto cada âncora prevê PESQUISAS futuras.

Para cada data de origem t, cada âncora usa só ondas divulgadas até t e
prevê as ondas cujo campo começa de 1 a 7 dias depois de t. O alvo é o vetor
da própria onda (PNAD quando há cruzamento, publicado nas demais), o mesmo
que as âncoras consomem. Isso mede previsão de pesquisas, não da urna: as
ondas compartilham erro comum, e o teste não calibra probabilidade de
vitória.
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np

from . import dinamico, tendencia
from .recencia import age, decay, midpoint

KIND = "previsao_vetor"
ORIGINS = (date(2026, 9, 1), date(2026, 10, 1))
HORIZON = 7
RECENCY = {
    "recencia_3d_7d": (3.0, 7),
    "recencia_1d_7d": (1.0, 7),
    "recencia_5d_7d": (5.0, 7),
    "recencia_7d_7d": (7.0, 7),
    "igual_7d": (None, 7),
    "recencia_3d_14d": (3.0, 14),
    "igual_14d": (None, 14),
}
LABELS = {
    "recencia_3d_7d": "Recência, meia-vida 3 dias, janela 7 (central)",
    "recencia_1d_7d": "Recência, meia-vida 1 dia, janela 7",
    "recencia_5d_7d": "Recência, meia-vida 5 dias, janela 7",
    "recencia_7d_7d": "Recência, meia-vida 7 dias, janela 7",
    "igual_7d": "Peso igual, janela 7",
    "recencia_3d_14d": "Recência, meia-vida 3 dias, janela 14",
    "igual_14d": "Peso igual, janela 14",
    "dinamico": "DLM com efeitos de casa, phi estimado",
    "dinamico_phi1": "DLM com efeitos de casa, phi = 1",
    "dinamico_casa": "DLM: nível + efeito da casa do alvo",
    "ultima_onda_mesma_casa": "Última onda divulgada da mesma casa",
    "tendencia": "Tendência amortecida, projetada ao campo alvo",
    "tendencia_corte": "Tendência amortecida, nível na origem",
    "tendencia_integrada": "Tendência integrada (inclinação em passeio), projetada",
    "tendencia_constante": "Inclinação constante, projetada",
    "central_inclinacao_14d": "Central + inclinação encolhida de 14 dias, projetada",
    "central_inclinacao_28d": "Central + inclinação encolhida de 28 dias, projetada",
}
# Central corrigida pela inclinação da regressão de efeitos fixos (janela, dias).
SLOPED = {"central_inclinacao_14d": 14, "central_inclinacao_28d": 28}
# Variantes de tendência: nome da âncora → variante do modelo.
TREND = {
    "tendencia": "amortecida",
    "tendencia_integrada": "integrada",
    "tendencia_constante": "constante",
}
TREND_NAMES = (*TREND, "tendencia_corte")
AGNOSTIC = (*RECENCY, "dinamico", "dinamico_phi1", *TREND_NAMES, *SLOPED)
FOCUS = ("recencia_3d_7d", "dinamico", *TREND_NAMES, *SLOPED)
HORIZON_GROUPS = {"1-2": (1, 2), "1-3": (1, 3), "3-7": (3, HORIZON)}
SHARES = ("lula", "flavio", "outros")
HOUSE_AWARE = ("recencia_3d_7d", "dinamico", "dinamico_casa", "ultima_onda_mesma_casa")


def released(polls, t):
    iso = t.isoformat()
    return [p for p in polls if p["divulgacao"] <= iso and p["campo"]["fim"] <= iso]


def latest(polls, t, days):
    """Mesma regra de base.latest: última onda de cada casa divulgada na janela."""
    begin = (t - timedelta(days=days - 1)).isoformat()
    chosen = {}
    for p in polls:
        if not begin <= p["divulgacao"] <= t.isoformat():
            continue
        old = chosen.get(p["instituto"])
        key = (p["campo"]["fim"], p["divulgacao"], p["id"])
        if old is None or key > (old["campo"]["fim"], old["divulgacao"], old["id"]):
            chosen[p["instituto"]] = p
    return list(chosen.values())


def recency_anchor(info, t, half_life, days, *, when=False):
    chosen = latest(info, t, days)
    if not chosen:
        return (None, None) if when else None
    w = np.array(
        [
            1.0 if half_life is None else decay(age(p["campo"], t), half_life)
            for p in chosen
        ]
    )
    w = w / w.sum()
    vector = np.average([p[KIND] for p in chosen], axis=0, weights=w)
    if not when:
        return vector
    # Data efetiva da âncora: ponto médio dos campos ponderado pelo peso.
    return vector, float(w @ [midpoint(p["campo"]) for p in chosen])


def anchors(info, t, warm):
    """Âncoras nacionais na origem t, efeitos de casa do DLM e estados de tendência."""
    out = {name: recency_anchor(info, t, *cfg) for name, cfg in RECENCY.items()}
    houses, states = {}, {}
    vector, when = recency_anchor(info, t, *RECENCY["recencia_3d_7d"], when=True)
    if vector is not None:
        states["central"] = (vector, when)
        for name, days in SLOPED.items():
            states[name] = tendencia.shrunk_slopes(info, t, days, KIND)[0]
    if len(info) >= 3:
        out["dinamico"], houses, warm["phi"] = dinamico.level(
            info, t, KIND, start=warm.get("phi")
        )
        out["dinamico_phi1"], _, warm["um"] = dinamico.level(
            info, t, KIND, excess=False, start=warm.get("um")
        )
        for name, variant in TREND.items():
            states[name], warm[name] = tendencia.filtered(
                info, KIND, variant=variant, start=warm.get(name)
            )
        out["tendencia_corte"] = tendencia.vector_at(states["tendencia"], t.toordinal())
    return {k: v for k, v in out.items() if v is not None}, houses, states


def projected(found, states, target):
    """Tendências projetadas ao ponto médio do campo alvo: o uso real da âncora."""
    out = dict(found)
    when = midpoint(target["campo"])
    for name in TREND:
        if name in states:
            out[name] = tendencia.vector_at(states[name], when)
    if "central" in states:
        vector, start = states["central"]
        for name in SLOPED:
            out[name] = tendencia.shift_valid(vector, states[name], when - start)
    return out


def house_aware(found, houses, info, house):
    out = dict(found)
    if "dinamico" in found:
        effect = houses.get(house, np.zeros(len(found["dinamico"])))
        out["dinamico_casa"] = dinamico.simplex(found["dinamico"] + effect)
    own = [p for p in info if p["instituto"] == house]
    if own:
        last = max(own, key=lambda p: (p["campo"]["fim"], p["divulgacao"], p["id"]))
        out["ultima_onda_mesma_casa"] = np.array(last[KIND])
    return out


def valid(vector):
    v = np.asarray(vector, float)[:3]
    return 100 * v / v.sum()


def errors(prediction, observed):
    p, o = valid(prediction), valid(observed)
    return {
        "margem_lula_flavio": float((p[0] - p[1]) - (o[0] - o[1])),
        "lula": float(p[0] - o[0]),
        "flavio": float(p[1] - o[1]),
        "outros": float(p[2] - o[2]),
    }


def _by_share(shares):
    out = {}
    for k, name in enumerate(SHARES):
        out[f"mae_{name}_pp"] = float(np.mean(abs(shares[:, k])))
        out[f"vies_{name}_pp"] = float(np.mean(shares[:, k]))
    return out


def metrics(pairs, names):
    out = {}
    for name in names:
        rows = [p["erros"][name] for p in pairs if name in p["erros"]]
        if not rows:
            continue
        margin = np.array([r["margem_lula_flavio"] for r in rows])
        shares = np.array([[r[k] for k in ("lula", "flavio", "outros")] for r in rows])
        out[name] = {
            "rotulo": LABELS[name],
            "n_pares": len(rows),
            "mae_margem_pp": float(np.mean(abs(margin))),
            "rmse_margem_pp": float(np.sqrt(np.mean(margin**2))),
            "vies_margem_pp": float(np.mean(margin)),
            "mae_parcelas_pp": float(np.mean(abs(shares))),
            "rmse_parcelas_pp": float(np.sqrt(np.mean(shares**2))),
            **_by_share(shares),
        }
    return out


def paired(pairs, a, b):
    """Diferença de erro absoluto da margem por onda alvo (média nos horizontes).

    Agrupar por onda evita contar a mesma pesquisa sete vezes como se fossem
    sete evidências independentes.
    """
    by_target = {}
    for p in pairs:
        if a in p["erros"] and b in p["erros"]:
            d = abs(p["erros"][a]["margem_lula_flavio"]) - abs(
                p["erros"][b]["margem_lula_flavio"]
            )
            by_target.setdefault(p["alvo"], []).append(d)
    diffs = np.array([np.mean(v) for v in by_target.values()])
    if len(diffs) < 2:
        return None
    se = float(diffs.std(ddof=1) / np.sqrt(len(diffs)))
    return {
        "a": a,
        "b": b,
        "n_ondas_alvo": len(diffs),
        "diferenca_mae_margem_pp": float(diffs.mean()),
        "erro_padrao_pp": se,
        "a_melhor_em_ondas": int((diffs < 0).sum()),
        "b_melhor_em_ondas": int((diffs > 0).sum()),
        "leitura": "negativo favorece a; |diferença| < 2 erros-padrão não separa as âncoras",
    }


def paired_detail(pairs, a, b):
    """Pareado por onda alvo na margem e em cada parcela, com erro-padrão."""
    out = {}
    for key in ("margem_lula_flavio", *SHARES):
        by_target = {}
        for p in pairs:
            if a in p["erros"] and b in p["erros"]:
                d = abs(p["erros"][a][key]) - abs(p["erros"][b][key])
                by_target.setdefault(p["alvo"], []).append(d)
        diffs = np.array([np.mean(v) for v in by_target.values()])
        if len(diffs) < 2:
            return None
        out[key] = {
            "diferenca_mae_pp": float(diffs.mean()),
            "erro_padrao_pp": float(diffs.std(ddof=1) / np.sqrt(len(diffs))),
        }
    return {
        "a": a,
        "b": b,
        "n_ondas_alvo": len({p["alvo"] for p in pairs}),
        **out,
        "leitura": "negativo favorece a; média por onda alvo",
    }


def horizon_groups(pairs, names=FOCUS):
    out = {}
    for label, (lo, hi) in HORIZON_GROUPS.items():
        subset = [p for p in pairs if lo <= p["horizonte_dias"] <= hi]
        if not subset:
            continue
        out[label] = {
            "n_pares": len(subset),
            "n_ondas_alvo": len({p["alvo"] for p in subset}),
            "metricas": metrics(subset, names),
            "comparacoes": [
                x
                for x in (
                    paired_detail(subset, "tendencia", "recencia_3d_7d"),
                    paired_detail(subset, "tendencia", "dinamico"),
                    paired_detail(subset, "tendencia", "tendencia_corte"),
                    paired_detail(subset, "central_inclinacao_14d", "recencia_3d_7d"),
                    paired_detail(subset, "central_inclinacao_28d", "recencia_3d_7d"),
                )
                if x
            ],
        }
    return out


def rolling(polls):
    pairs, warm = [], {}
    t = ORIGINS[0]
    while t <= ORIGINS[1]:
        info = released(polls, t)
        targets = [
            p
            for p in polls
            if 1 <= (date.fromisoformat(p["campo"]["inicio"]) - t).days <= HORIZON
        ]
        if targets:
            found, houses, states = anchors(info, t, warm)
        for target in targets:
            predictions = house_aware(
                projected(found, states, target), houses, info, target["instituto"]
            )
            pairs.append(
                {
                    "origem": t.isoformat(),
                    "alvo": target["id"],
                    "casa": target["instituto"],
                    "horizonte_dias": (
                        date.fromisoformat(target["campo"]["inicio"]) - t
                    ).days,
                    "erros": {
                        k: errors(v, target[KIND]) for k, v in predictions.items()
                    },
                }
            )
        t += timedelta(days=1)
    return pairs


def leave_one_house_out(polls):
    pairs, warm = [], {}
    begin, end = ORIGINS[0].isoformat(), (ORIGINS[1] + timedelta(days=1)).isoformat()
    targets = sorted(
        (p for p in polls if begin <= p["campo"]["inicio"] <= end),
        key=lambda p: (p["campo"]["inicio"], p["id"]),
    )
    for target in targets:
        t = date.fromisoformat(target["campo"]["inicio"]) - timedelta(days=1)
        info = [p for p in released(polls, t) if p["instituto"] != target["instituto"]]
        found, _, states = anchors(info, t, warm)
        found = projected(found, states, target)
        pairs.append(
            {
                "origem": t.isoformat(),
                "alvo": target["id"],
                "casa": target["instituto"],
                "erros": {k: errors(v, target[KIND]) for k, v in found.items()},
            }
        )
    return pairs


def common(pairs, names):
    return [p for p in pairs if all(n in p["erros"] for n in names)]


def run(polls, *, window_start):
    roll = rolling(polls)
    main = common(roll, AGNOSTIC)
    aware = common(roll, HOUSE_AWARE)
    loho = common(leave_one_house_out(polls), AGNOSTIC)
    by_house = {}
    for p in loho:
        by_house.setdefault(p["casa"], []).append(p)
    horizon = {}
    for h in range(1, HORIZON + 1):
        subset = [p for p in main if p["horizonte_dias"] == h]
        if subset:
            horizon[str(h)] = metrics(subset, FOCUS)
    return {
        "natureza": "Previsão de PESQUISAS futuras, não da urna. As ondas compartilham erro comum que nenhuma âncora vê; MAE baixo não calibra probabilidade de vitória nem mede viés eleitoral.",
        "desenho": {
            "origens": [ORIGINS[0].isoformat(), ORIGINS[1].isoformat()],
            "horizonte_dias": [1, HORIZON],
            "informacao": "ondas com divulgação e fim de campo até a origem",
            "alvo": "ondas com início de campo 1 a 7 dias após a origem; vetor PNAD quando há cruzamento, publicado nas demais",
            "metrica": "erro em pontos dos votos válidos; margem = Lula − Flávio",
            "dinamico": "hiperparâmetros reestimados por máxima verossimilhança em cada origem, só com a informação disponível",
            "tendencia": "mesma reestimação; a âncora de tendência é projetada ao ponto médio do campo alvo (uso real), e a variante de nível usa o estado na origem",
            "janela_dinamico_inicio": window_start,
            "pares_comuns": "todas as âncoras avaliadas nos mesmos pares",
        },
        "origem_movel": {
            "n_pares": len(main),
            "n_ondas_alvo": len({p["alvo"] for p in main}),
            "metricas": metrics(main, AGNOSTIC),
            "por_horizonte": horizon,
            "por_grupo_horizonte": horizon_groups(main),
            "comparacoes": [
                x
                for x in (
                    paired(main, "dinamico", "recencia_3d_7d"),
                    paired(main, "recencia_1d_7d", "recencia_3d_7d"),
                    paired(main, "recencia_5d_7d", "recencia_3d_7d"),
                    paired(main, "igual_7d", "recencia_3d_7d"),
                    paired(main, "tendencia", "recencia_3d_7d"),
                    paired(main, "tendencia", "dinamico"),
                    paired(main, "tendencia_corte", "recencia_3d_7d"),
                    paired(main, "tendencia_integrada", "recencia_3d_7d"),
                    paired(main, "tendencia_constante", "recencia_3d_7d"),
                    paired(main, "central_inclinacao_14d", "recencia_3d_7d"),
                    paired(main, "central_inclinacao_28d", "recencia_3d_7d"),
                )
                if x
            ],
            "comparacoes_por_parcela": [
                x
                for x in (
                    paired_detail(main, "tendencia", "recencia_3d_7d"),
                    paired_detail(main, "tendencia", "dinamico"),
                    paired_detail(main, "tendencia", "tendencia_corte"),
                    paired_detail(main, "central_inclinacao_14d", "recencia_3d_7d"),
                    paired_detail(main, "central_inclinacao_28d", "recencia_3d_7d"),
                )
                if x
            ],
        },
        "aceleracao": {
            "nota": "Inclinação constante contra inclinação que muda (passeio integrado e amortecida), todas projetadas ao campo alvo, nos mesmos pares. Se a mudança de inclinação ajudasse a prever, as variantes com inclinação variável teriam MAE menor e viés menor em Flávio.",
            "metricas": metrics(
                main, ("tendencia_constante", "tendencia_integrada", "tendencia")
            ),
            "comparacoes": [
                x
                for x in (
                    paired_detail(main, "tendencia_integrada", "tendencia_constante"),
                    paired_detail(main, "tendencia", "tendencia_constante"),
                )
                if x
            ],
        },
        "com_casa_do_alvo": {
            "nota": "Prever a próxima onda de uma casa conhecida. Só pares em que a casa já tinha onda divulgada. Não é âncora nacional.",
            "n_pares": len(aware),
            "n_ondas_alvo": len({p["alvo"] for p in aware}),
            "metricas": metrics(aware, HOUSE_AWARE),
            "comparacoes": [
                x
                for x in (
                    paired(aware, "dinamico_casa", "ultima_onda_mesma_casa"),
                    paired(aware, "dinamico_casa", "recencia_3d_7d"),
                )
                if x
            ],
        },
        "deixa_uma_casa_fora": {
            "nota": "Cada onda com campo iniciado de 01/09 a 02/10 é prevista sem nenhuma onda da própria casa, com informação divulgada até a véspera do campo. Inclui o desvio próprio da casa, que nenhuma âncora conhece.",
            "n_pares": len(loho),
            "metricas": metrics(loho, AGNOSTIC),
            "por_casa": {
                house: {
                    "n": len(rows),
                    **{
                        name: m["mae_margem_pp"]
                        for name, m in metrics(
                            rows, ("recencia_3d_7d", "dinamico", "tendencia")
                        ).items()
                    },
                }
                for house, rows in sorted(by_house.items())
            },
            "comparacoes": [
                x
                for x in (
                    paired(loho, "dinamico", "recencia_3d_7d"),
                    paired(loho, "tendencia", "recencia_3d_7d"),
                    paired(loho, "tendencia", "dinamico"),
                    paired(loho, "central_inclinacao_14d", "recencia_3d_7d"),
                    paired(loho, "central_inclinacao_28d", "recencia_3d_7d"),
                )
                if x
            ],
            "comparacoes_por_parcela": [
                x for x in (paired_detail(loho, "tendencia", "recencia_3d_7d"),) if x
            ],
        },
    }
