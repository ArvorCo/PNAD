"""Distribuição estadual do 2º turno recentrada nas centrais Arvor.

Reaproveita o motor da projeção territorial (`projecao_secoes_2t`): o voto de
cada seção do 1º turno é transportado pela regra selecionada na retrospectiva
2018→2022 (terceira via dividida na proporção local entre finalistas), as
pesquisas estaduais pós-urna atualizam os estados em que existem, e um único
deslocamento de log-odds recentra o país em cada âncora nacional: a Média Arvor
e a Projeção Arvor publicadas em `docs/assets/reponderacao_simulador.json`.
Comparecimento e branco/nulo ficam os do 1º turno em toda seção.
"""

from __future__ import annotations

import json
from datetime import date

import numpy as np
import pandas as pd
from projecao_secoes_2t.fontes import ROOT, complete_current, current, sha
from projecao_secoes_2t.motor import DEST, share
from projecao_secoes_2t.pesquisas import calibrate, state_records, update_states

SNAPSHOT = ROOT / "docs/assets/reponderacao_simulador.json"
VALIDACAO = ROOT / "analysis/projecao_secoes_2t/validacao.json"
OFICIAL = ROOT / "analysis/apuracao_2026/dados/presidente.json"

ANCORAS = {
    "media": ("central", "Média Arvor"),
    "projecao": ("central_projection", "Projeção Arvor"),
}


def proportional(frame: pd.DataFrame) -> np.ndarray:
    """Só o método selecionado; evita ajustar as matrizes ecológicas de novo."""
    x = frame[[f"{p}_1" for p in ("direita", "esquerda", "outros", "bn", "ausentes")]]
    x = x.to_numpy(float) / frame.aptos_1.to_numpy(float)[:, None]
    p = share(x)
    out = np.column_stack(
        [x[:, 0] + p * x[:, 2], x[:, 1] + (1 - p) * x[:, 2], x[:, 3:]]
    )
    if not np.allclose(out.sum(axis=1), 1, atol=1e-9) or (out < -1e-10).any():
        raise ValueError("Partição proporcional inválida")
    return out


def _check_published(frame: pd.DataFrame, history: np.ndarray) -> None:
    """O transporte proporcional precisa bater com a projeção territorial publicada."""
    published = pd.read_csv(ROOT / "docs/assets/projecao_secoes_2t_ufs.csv").set_index(
        "uf"
    )
    mine = aggregate(frame, history)
    for uf in mine.index:
        for col, dest in (
            ("proporcional_direita", "direita"),
            ("proporcional_esquerda", "esquerda"),
        ):
            if abs(published.loc[uf, col] - mine.loc[uf, dest]) > 0.5:
                raise ValueError(f"Transporte difere da projeção publicada em {uf}")


def anchors(snapshot: dict) -> dict[str, dict]:
    out = {}
    for key, (field, label) in ANCORAS.items():
        c = snapshot[field]
        f, l_ = c["flavio"], c["lula"]
        out[key] = {
            "rotulo": label,
            "flavio_validos": 100 * f / (f + l_),
            "flavio": f,
            "lula": l_,
            "diferenca_pp": f - l_,
            "casas": len(c["polls"]),
            "parametros": c["parametros"],
        }
    return out


def aggregate(frame: pd.DataFrame, values: np.ndarray) -> pd.DataFrame:
    counts = values * frame.aptos_1.to_numpy(float)[:, None]
    aux = frame[["uf"]].copy()
    aux[DEST] = counts
    return aux.groupby("uf").sum()


def state_rows(frame, history, by_anchor, official):
    nomes = {u["uf"]: u["nome"] for u in official["ufs"]}
    regioes = {u["uf"]: u["regiao"] for u in official["ufs"]}
    base = frame.groupby("uf")[["aptos_1", "direita_1", "esquerda_1", "outros_1"]].sum()
    rows = []
    for uf in sorted(base.index):
        f1, l1, o1 = (
            float(base.loc[uf, c]) for c in ("direita_1", "esquerda_1", "outros_1")
        )
        v1 = f1 + l1 + o1
        row = {
            "uf": uf,
            "nome": nomes[uf],
            "regiao": regioes[uf],
            "aptos": int(base.loc[uf, "aptos_1"]),
            "primeiro_turno": {
                "flavio_pct": 100 * f1 / v1,
                "lula_pct": 100 * l1 / v1,
                "terceiros_pct": 100 * o1 / v1,
                "diferenca_pp": 100 * (f1 - l1) / v1,
            },
            "transportado": _score(history.loc[uf]),
            "pesquisa_estadual": None,
        }
        for key, table in by_anchor.items():
            row[key] = _score(table.loc[uf])
        rows.append(row)
    return rows


def _score(counts) -> dict:
    f, l_, bn, aus = (float(counts[c]) for c in DEST)
    validos = f + l_
    return {
        "flavio_pct": 100 * f / validos,
        "lula_pct": 100 * l_ / validos,
        "diferenca_pp": 100 * (f - l_) / validos,
        "flavio_votos": f,
        "lula_votos": l_,
        "validos": validos,
        "branco_nulo": bn,
        "ausentes": aus,
    }


def national(counts) -> dict:
    total = counts.sum(axis=0)
    out = _score(total)
    out["comparecimento_pct"] = 100 * (1 - total["ausentes"] / total.sum())
    return out


def build(today: date) -> dict:
    snapshot = json.loads(SNAPSHOT.read_text())
    if snapshot["reference"] != today.isoformat():
        raise ValueError(
            f"Snapshot das centrais é de {snapshot['reference']}, não de {today}"
        )
    raw, meta26 = current(False)
    frame, coverage = complete_current(raw)
    validation = json.loads(VALIDACAO.read_text())
    if validation["selecionado"] != "proporcional":
        raise ValueError("Método selecionado mudou; revisar o mapa")
    sd_prior = max(2, validation["resultados"]["proporcional"]["rmse_uf_pp"])
    weights = frame.aptos_1.to_numpy(float)

    history = proportional(frame)
    records, source = state_records(today)
    updated, updates = update_states(frame, history, records, sd_prior)

    official = json.loads(OFICIAL.read_text())
    covered = {u["uf"] for u in updates}
    covered_pct = float(
        100 * frame.loc[frame.uf.isin(covered), "aptos_1"].sum() / weights.sum()
    )
    _check_published(frame, history)
    targets = anchors(snapshot)
    by_anchor, shifts = {}, {}
    for key, target in targets.items():
        calibrated, shift = calibrate(updated, weights, target["flavio_validos"] / 100)
        counts = aggregate(frame, calibrated)
        by_anchor[key] = counts
        shifts[key] = shift
        got = national(counts)["flavio_pct"]
        if abs(got - target["flavio_validos"]) > 1e-6:
            raise ValueError(f"Calibração não atingiu a âncora {key}: {got}")

    rows = state_rows(frame, aggregate(frame, history), by_anchor, official)
    for row in rows:
        hit = [u for u in updates if u["uf"] == row["uf"]]
        if hit:
            u = hit[0]
            row["pesquisa_estadual"] = {
                "instituto": u["instituto"],
                "campo": u["campo"],
                "n": u["n"],
                "publicado": u["publicado"],
                "flavio_validos_pct": u["pesquisa_pct"],
                "peso": u["peso_pesquisa"],
            }
    nat = {
        "primeiro_turno": _first_round_national(frame),
        "transportado": national(aggregate(frame, history)),
        "estaduais_atualizadas": national(aggregate(frame, updated)),
    }
    for key, counts in by_anchor.items():
        nat[key] = {**national(counts), "deslocamento_log_odds": shifts[key]}
    return {
        "schema": 1,
        "referencia": today.isoformat(),
        "eleicao": "2026-10-25",
        "universo": "Brasil sem exterior",
        "metodo": {
            "transporte": "Terceira via do 1º turno dividida na proporção local entre finalistas, seção a seção (método selecionado na retrospectiva 2018→2022, RMSE estadual 1,73 pp).",
            "estaduais": "Pesquisas estaduais pós-urna com meia-vida de 7 dias e janela de 14 dias atualizam a UF antes da calibração.",
            "cobertura_estaduais_pct": covered_pct,
            "calibracao": "Um deslocamento comum de log-odds por âncora leva o país exatamente ao valor da central; comparecimento e branco/nulo seguem os do 1º turno em cada seção.",
            "ancoras": targets,
            "dp_prior_pp": sd_prior,
            "limites": [
                "Expectativa pontual por UF; a cor não indica liderança estatisticamente identificada.",
                "Erro comum de 2 pp das pesquisas não se dilui entre estados: faixa ±2 pp é sensibilidade, não intervalo calibrado.",
                "A fusão completa não foi validada contra uma urna de 2º turno; só o transporte foi testado em 2018→2022.",
                "Sem probabilidade de vitória validada.",
            ],
        },
        "cobertura": coverage,
        "nacional": nat,
        "estaduais": updates,
        "fonte_estaduais": source,
        "ufs": rows,
        "fontes": {
            "snapshot_centrais": snapshot["version"],
            "motor_centrais": snapshot["engine"],
            "snapshot_sha256": sha(SNAPSHOT),
            "extrato_2026": meta26,
            "oficial_1t_sha256": sha(OFICIAL),
            "validacao_sha256": sha(VALIDACAO),
        },
    }


def _first_round_national(frame) -> dict:
    f, l_, o = (float(frame[f"{c}_1"].sum()) for c in ("direita", "esquerda", "outros"))
    v = f + l_ + o
    return {
        "flavio_pct": 100 * f / v,
        "lula_pct": 100 * l_ / v,
        "terceiros_pct": 100 * o / v,
        "diferenca_pp": 100 * (f - l_) / v,
        "comparecimento_pct": 100 * (1 - frame.ausentes_1.sum() / frame.aptos_1.sum()),
    }
