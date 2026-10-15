"""Sensibilidade às cotas atuais, sem confundi-las com pesos finais observados."""

import importlib
import json
from pathlib import Path

PNAD = importlib.import_module("reponderacao-pnad")
ROOT = Path(__file__).resolve().parents[2]


def build(poll, old):
    processed = PNAD.process_poll(poll, PNAD.Benchmark(), PNAD.load_ipca())
    turn = processed["turnos"]["2t"]
    adjusted = turn["cenarios"][PNAD.MAIN_SERIES]["ajustado"]
    published = poll["publicado"]["2t"]
    current_cross = poll["cruzamentos"]["2t"]
    old_cross = old["cruzamentos"]["2t"]
    before = [
        dict(zip(old_cross["opcoes"], row, strict=True)) for row in old_cross["linhas"]
    ]
    after = [
        dict(zip(current_cross["opcoes"], row, strict=True))
        for row in current_cross["linhas"]
    ]
    weights = poll["renda"]["amostra_pct"]
    evolution = []
    for band, weight, a, b in zip(
        poll["renda"]["faixas"], weights, before, after, strict=True
    ):
        change = (b["flavio"] - b["lula"]) - (a["flavio"] - a["lula"])
        evolution.append(
            {
                "faixa": band["rotulo"],
                "antes": a,
                "agora": b,
                "mudanca_gap_pp": change,
                "contribuicao_condicional_pp": weight * change / 100,
            }
        )
    reconstructed_change = sum(r["contribuicao_condicional_pp"] for r in evolution)
    published_change = (published["flavio"] - published["lula"]) - (
        old["publicado"]["2t"]["flavio"] - old["publicado"]["2t"]["lula"]
    )
    return {
        "tipo": "sensibilidade_condicional_cotas_registradas",
        "hipotese": poll["renda"]["nota"],
        "pesos_registro_pct": weights,
        "pnad_pct": processed["renda"]["pnad_pct"][PNAD.MAIN_SERIES],
        "recomposto": turn["recomposto"],
        "reponderacao_pontual": adjusted,
        "gap_publicado_pp": published["flavio"] - published["lula"],
        "gap_ajustado_pp": adjusted["flavio"] - adjusted["lula"],
        "flavio_binario_pct": 100
        * adjusted["flavio"]
        / (adjusted["flavio"] + adjusted["lula"]),
        "delta_ajuste_pp": {k: adjusted[k] - published[k] for k in adjusted},
        "cenarios": {k: v["ajustado"] for k, v in turn["cenarios"].items()},
        "controles": json.loads((ROOT / poll["controles_arquivo"]).read_text()),
        "evolucao_0310": evolution,
        "mudanca_gap_recomposto_pp": reconstructed_change,
        "mudanca_gap_publicado_pp": published_change,
        "mudanca_residuo_pp": published_change - reconstructed_change,
        "limite": "Cotas atuais assumidas como pesos, sem perfil final ou bases publicadas. A evolução compara amostras independentes, não migração individual nem efeito do feriado; não se testou a significância das mudanças por faixa. Em 03/10, 31/42/27 era hipótese da onda anterior. Sem prova de mudança da composição nem de pesos finais iguais.",
    }
