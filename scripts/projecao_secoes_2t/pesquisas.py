"""Atualização territorial com pesquisas, seguida de calibração nacional explícita."""

import json
from datetime import date

import numpy as np
from scipy.optimize import brentq
from scipy.special import expit

from .fontes import ROOT, sha
from .motor import logits, share


def calibrate(values, electorate, target):
    """Deslocamento comum de log-odds; conserva válidos, BN e ausência por linha."""
    if not 0 < target < 1:
        raise ValueError("Alvo de votos válidos deve estar entre zero e um")
    result = values.copy()
    mass = values[:, :2].sum(axis=1)
    weights = mass * electorate
    if weights.sum() <= 0:
        raise ValueError("Calibração exige votos válidos")
    original = logits(share(values))
    shift = brentq(
        lambda delta: np.average(expit(original + delta), weights=weights) - target,
        -40,
        40,
        xtol=1e-13,
    )
    p = expit(original + shift)
    result[:, 0], result[:, 1] = mass * p, mass * (1 - p)
    return result, float(shift)


def national_poll(snapshot, today):
    if snapshot["reference"] != today.isoformat():
        raise ValueError("Corte da pesquisa nacional difere do corte do modelo")
    projection = snapshot["projection"]
    selected = projection["selected"]
    rows = []
    for p in selected:
        if (
            p["campo"]["inicio"] <= "2026-10-04"
            or p["campo"]["fim"] > today.isoformat()
            or p["divulgacao"] > today.isoformat()
        ):
            raise ValueError("Pesquisa nacional fora do corte")
        q = p["pnad"]["flavio"] / (p["pnad"]["flavio"] + p["pnad"]["lula"])
        rows.append(
            {
                "id": p["id"],
                "instituto": p["instituto"],
                "campo": p["campo"],
                "divulgacao": p["divulgacao"],
                "n": p["n"],
                "peso": p["weight"],
                "flavio_validos": 100 * q,
                "pnad": p["income_available"],
            }
        )
    anchor = projection["anchors"]["pnad"]
    published = projection["anchors"]["published"]
    w = np.array([p["peso"] for p in rows])
    p = np.array([p["flavio_validos"] for p in rows]) / 100
    # Erro comum de 2 pp não diminui com número de casas/seções.
    house_variance = np.average((p - np.average(p, weights=w)) ** 2, weights=w)
    sampling_variance = sum(
        poll["peso"] ** 2 * 1.5 * 0.25 / min(poll["n"], 2000) for poll in rows
    )
    trend = projection["trend"]["pnad"]
    trend_sd = trend["dp_margem_projecao_pp"] / 200
    variance = (
        0.02**2 + max(house_variance * np.sum(w**2), sampling_variance) + trend_sd**2
    )
    return {
        "flavio_validos": 100 * anchor["flavio"] / (anchor["flavio"] + anchor["lula"]),
        "publicado_validos": 100
        * published["flavio"]
        / (published["flavio"] + published["lula"]),
        "variancia": float(variance),
        "erro_comum_pp": 2,
        "dp_tendencia_parcela_pp": trend_sd * 100,
        "casas": rows,
        "n_casas": len(rows),
        "regra": "Âncora PNAD inclusiva com recência e tendência pós-urna do agregador; sem reaplicar presença relativa +3,8%, pois o transporte da apuração já inclui composição e comparecimento. Indecisos divididos proporcionalmente entre finalistas; BN não é voto válido.",
    }


def state_records(today):
    path = ROOT / "analysis/projecao_secoes_2t/estaduais.json"
    records = json.loads(path.read_text())
    source = ROOT / records["source"]["arquivo"]
    if sha(source) != records["source"]["sha256"]:
        raise ValueError("Fonte estadual mudou")
    selected = []
    for row in records["pesquisas"]:
        if (
            row["campo"]["inicio"] <= "2026-10-04"
            or row["campo"]["fim"] > today.isoformat()
            or row["divulgacao"] > today.isoformat()
        ):
            continue
        age = (today - date.fromisoformat(row["campo"]["fim"])).days
        if age > 14:
            continue
        selected.append({**row, "recencia": 2 ** (-age / 7)})
    return selected, records["source"]


def update_states(frame, prior, records, tau_pp):
    result = prior.copy()
    updates = []
    for row in records:
        mask = (frame.uf == row["uf"]).to_numpy()
        weights = frame.loc[mask, "aptos_1"].to_numpy(float)
        old = share((result[mask] * weights[:, None]).sum(axis=0)[None, :])[0]
        f, left = row["publicado"]["flavio"], row["publicado"]["lula"]
        q = f / (f + left)
        n_eff = min(row["n"], 2000) * (f + left) / 100 / 1.5
        variance = q * (1 - q) / n_eff + 0.02**2
        prior_variance = (max(tau_pp, 2) / 100) ** 2
        gain = row["recencia"] * prior_variance / (prior_variance + variance)
        target = (1 - gain) * old + gain * q
        result[mask], shift = calibrate(result[mask], weights, target)
        updates.append(
            {
                **row,
                "anterior_pct": 100 * old,
                "pesquisa_pct": 100 * q,
                "atualizado_antes_calibracao_pct": 100 * target,
                "peso_pesquisa": gain,
                "deslocamento_log_odds": shift,
            }
        )
    return result, updates


def combine(frame, historical, validation, snapshot, today):
    weights = frame.aptos_1.to_numpy(float)
    prior = share((historical * weights[:, None]).sum(axis=0)[None, :])[0]
    poll = national_poll(snapshot, today)
    selected = validation["selecionado"]
    # Uma retrospectiva informa ordem de grandeza, não calibra uma probabilidade.
    sd_prior = max(2, validation["resultados"][selected]["rmse_uf_pp"])
    variance_prior = (sd_prior / 100) ** 2
    gain = variance_prior / (variance_prior + poll["variancia"])
    target = (1 - gain) * prior + gain * poll["flavio_validos"] / 100
    records, source = state_records(today)
    state_updated, updates = update_states(frame, historical, records, sd_prior)
    calibrated, delta = calibrate(state_updated, weights, target)
    covered = {row["uf"] for row in records}
    metadata = {
        "historico_pct": 100 * prior,
        "pesquisas_pct": poll["flavio_validos"],
        "combinado_pct": 100 * target,
        "peso_pesquisas": gain,
        "dp_transporte_pp": sd_prior,
        "deslocamento_nacional_log_odds": delta,
        "nacional": poll,
        "estaduais": updates,
        "fonte_estaduais": source,
        "cobertura_estaduais_pct": 100
        * frame.loc[frame.uf.isin(covered), "aptos_1"].sum()
        / weights.sum(),
        "hipoteses": [
            "Peso nacional por variâncias declaradas, assumindo erros independentes entre urna transportada e pesquisas; não aprendido em múltiplas eleições.",
            "Erro comum não se dilui em 500 mil seções; a faixa ±2 pp é sensibilidade, não intervalo calibrado.",
            "Estaduais atualizam a distribuição territorial antes de recentrar no alvo nacional combinado; não são novas casas nacionais.",
            "Pesquisas estaduais usam publicados: não há PNAD imputada. Erro de casa de 2 pp, deff 1,5, teto n=2000, meia-vida de 7 dias, janela de 14 dias.",
            "O total nacional das estaduais é neutralizado pela calibração; o desvio por UF permanece parcial.",
        ],
    }
    return calibrated, metadata
