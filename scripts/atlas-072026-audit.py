#!/usr/bin/env python3
"""Reproduce the numerical checks used in the Atlas July 2026 dossier.

Além da aritmética de margem (a parte de auditoria), o script consolida os
cruzamentos transcritos do relatório Atlas/Bloomberg de julho de 2026 e deriva
os três painéis estratégicos publicados no dossiê:

* ``succession_ledger``  — Jair (cenário 2022 repetido) x Flávio (cenário 1),
  medidos nos MESMOS respondentes, por recorte. Mostra onde estão os 6,5 pontos
  que separam o herdeiro do pai dentro da mesma pesquisa.
* ``fear_to_vote_conversion`` — recortes em que o eleitor teme mais Lula do que
  Flávio e ainda assim vota em Lula. É o único lugar do relatório em que o
  déficit é de confiança, não de opinião.
* ``bolsonaro_2022_diaspora`` — para onde foi o voto de Jair/2022 que não está
  com Flávio hoje.

Números de origem: ``Atlas_0726.pdf`` (páginas 16, 20/21, 30, 34, 38 e 39),
transcritos manualmente porque os cruzamentos são publicados como imagem.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

N_ATLAS = 5_021
Z_95 = 1.96

GENDER_WAVES = {
    "june": {
        "men": {"share": 0.291, "n": round(4_999 * 0.472)},
        "women": {"share": 0.435, "n": round(4_999 * 0.528)},
    },
    "july": {
        "men": {"share": 0.385, "n": round(5_021 * 0.477)},
        "women": {"share": 0.334, "n": round(5_021 * 0.523)},
    },
}

# Atlas 07/2026, p.16 (repetição hipotética de 2022) x p.20 (cenário 1 de 2026).
# Mesma amostra, mesma onda: a diferença isola o custo da sucessão.
SUCCESSION = {
    "Total": (42.3, 35.8),
    "Homem": (45.2, 38.5),
    "Mulher": (39.6, 33.4),
    "16-24": (22.7, 9.7),
    "25-34": (48.8, 41.1),
    "35-44": (50.2, 43.1),
    "45-59": (47.9, 42.2),
    "60+": (34.0, 32.2),
    "Fundamental": (47.3, 43.9),
    "Médio": (43.3, 35.9),
    "Superior": (34.4, 25.6),
    "Renda até R$2 mil": (40.1, 35.3),
    "Renda R$2-3 mil": (43.2, 40.9),
    "Renda R$3-5 mil": (49.7, 41.4),
    "Renda R$5-10 mil": (41.3, 33.4),
    "Renda acima de R$10 mil": (33.1, 24.1),
    "Católico": (40.9, 36.3),
    "Evangélico": (65.4, 51.5),
    "Crente sem religião": (34.6, 30.1),
    "Agnóstico ou ateu": (8.3, 5.6),
    "Norte": (48.3, 37.0),
    "Nordeste": (23.5, 21.3),
    "Centro-Oeste": (47.8, 38.0),
    "Sudeste": (45.1, 37.2),
    "Sul": (62.0, 55.9),
    "Direita bolsonarista": (99.9, 97.4),
    "Direita não bolsonarista": (73.9, 53.6),
    "Independente": (34.9, 31.6),
    "Sem posicionamento declarado": (35.9, 16.2),
}

# Atlas 07/2026, p.38 (medo) x p.20 (voto no cenário 1).
# Cada célula: (teme Lula, teme Flávio, voto Lula, voto Flávio).
FEAR_VS_VOTE = {
    "Total": (44.6, 46.6, 44.9, 35.8),
    "Homem": (49.2, 40.0, 40.6, 38.5),
    "Mulher": (40.3, 52.6, 48.9, 33.4),
    "16-24": (24.3, 48.6, 36.9, 9.7),
    "25-34": (55.4, 31.1, 36.8, 41.1),
    "35-44": (51.5, 40.5, 36.8, 43.1),
    "45-59": (47.7, 49.2, 47.8, 42.2),
    "60+": (36.9, 61.2, 60.8, 32.2),
    "Fundamental": (52.4, 43.6, 46.8, 43.9),
    "Médio": (43.6, 42.8, 37.6, 35.9),
    "Superior": (36.1, 56.4, 54.2, 25.6),
    "Renda até R$2 mil": (47.4, 47.2, 53.5, 35.3),
    "Renda R$2-3 mil": (44.1, 43.0, 37.1, 40.9),
    "Renda R$3-5 mil": (50.5, 39.7, 35.8, 41.4),
    "Renda R$5-10 mil": (41.0, 51.2, 47.8, 33.4),
    "Renda acima de R$10 mil": (36.1, 54.8, 52.8, 24.1),
    "Católico": (45.5, 48.0, 50.0, 36.3),
    "Evangélico": (66.5, 22.6, 22.1, 51.5),
    "Norte": (52.6, 34.4, 31.7, 37.0),
    "Nordeste": (29.6, 62.7, 65.8, 21.3),
    "Centro-Oeste": (43.6, 42.3, 39.0, 38.0),
    "Sudeste": (46.1, 44.8, 41.2, 37.2),
    "Sul": (63.2, 31.6, 28.4, 55.9),
}

# Atlas 07/2026, p.20 e p.21: coluna "Jair Bolsonaro" do cruzamento de voto 2022.
BOLSONARO_2022_DIASPORA = {
    "Flávio Bolsonaro": 72.6,
    "Renan Santos": 10.2,
    "Romeu Zema": 6.3,
    "Ronaldo Caiado": 5.4,
    "Augusto Cury": 2.7,
    "Não sei": 1.8,
    "Lula": 0.5,
    "Samara Martins": 0.4,
    "Cabo Daciolo": 0.1,
    "Voto branco/nulo": 0.1,
}

# Atlas 07/2026, p.39: confiança para administrar cada área (Lula x Flávio).
GOVERNMENT_AREAS = {
    "Pobreza e desigualdade social": (51, 41),
    "Proteção do meio ambiente": (49, 41),
    "Saúde": (49, 43),
    "Educação": (49, 43),
    "Economia e inflação": (48, 44),
    "Geração de empregos": (48, 43),
    "Promoção da democracia": (48, 42),
    "Política externa": (48, 44),
    "Infraestrutura": (47, 44),
    "Criminalidade e tráfico de drogas": (46, 46),
    "Combate à corrupção": (45, 43),
    "Equilíbrio fiscal e controle de gastos": (45, 44),
    "Impostos / carga tributária": (45, 44),
}

# Cenário 1 da Atlas (p.18) x 1º turno do Datafolha 07/2026 (BR-01166/2026).
# A comparação só é válida sobre votos válidos: a Atlas registra 1,6% de
# branco/nulo + não sei contra 11% do Datafolha, e essa diferença de 9,4
# pontos comprime mecanicamente todas as porcentagens de um dos dois.
FIRST_ROUND_ATLAS = {
    "Lula": 44.9,
    "Flávio Bolsonaro": 35.8,
    "Renan Santos": 7.8,
    "Ronaldo Caiado": 3.1,
    "Romeu Zema": 2.8,
    "Samara Martins": 2.1,
    "Augusto Cury": 1.6,
    "Cabo Daciolo": 0.1,
    "Hertz Dias": 0.1,
    "Edmilson Costa": 0.1,
}
FIRST_ROUND_DATAFOLHA = {
    "Lula": 40.0,
    "Flávio Bolsonaro": 32.0,
    "Ronaldo Caiado": 4.0,
    "Romeu Zema": 3.0,
    "Renan Santos": 3.0,
    "Augusto Cury": 2.0,
    "Samara Martins": 1.0,
    "Cabo Daciolo": 1.0,
    "Rui Costa Pimenta": 1.0,
}
NON_CHOICE = {"atlas": 1.6, "datafolha": 11.0}

# Datafolha nacional de julho (BR-01166/2026): 331 pontos de fluxo, 2.004
# entrevistas, 328 pontos com exatamente 6 entrevistas.
DATAFOLHA_CLUSTER_SIZE = 6
DATAFOLHA_DEFF_THRESHOLDS = {"second_round_gap": 1.44, "first_round_gap": 4.68}


def moe_srs(n: int, share: float = 0.5, z_score: float = Z_95) -> float:
    """Return the simple-random-sample margin in percentage points."""
    return 100 * z_score * math.sqrt(share * (1 - share) / n)


def required_n(moe_pp: float, share: float = 0.5, z_score: float = Z_95) -> int:
    """Return the minimum SRS n for the requested percentage-point margin."""
    margin = moe_pp / 100
    return math.ceil((z_score**2 * share * (1 - share)) / margin**2)


def remove_full_support_overcapture(observed: float, fraction: float) -> float:
    """Remove an assumed fraction composed entirely of candidate supporters."""
    if not 0 <= fraction < 1:
        raise ValueError("fraction must be in [0, 1)")
    return (observed - fraction) / (1 - fraction)


def intracluster_rho(deff: float, cluster_size: int) -> float:
    """Invert Kish's deff = 1 + (m - 1) * rho for equal-sized clusters."""
    if cluster_size < 2:
        raise ValueError("cluster_size must be at least 2")
    return (deff - 1) / (cluster_size - 1)


def gender_gap_instability() -> dict[str, float]:
    """Compare the Flávio gender gap across independently treated waves."""
    june = GENDER_WAVES["june"]
    july = GENDER_WAVES["july"]
    june_gap = june["women"]["share"] - june["men"]["share"]
    july_gap = july["women"]["share"] - july["men"]["share"]
    swing = june_gap - july_gap
    variance = sum(
        cell["share"] * (1 - cell["share"]) / cell["n"]
        for wave in GENDER_WAVES.values()
        for cell in wave.values()
    )
    se = math.sqrt(variance)
    return {
        "june_women_minus_men_pp": round(100 * june_gap, 3),
        "july_women_minus_men_pp": round(100 * july_gap, 3),
        "gap_swing_pp": round(100 * swing, 3),
        "srs_standard_error_pp": round(100 * se, 3),
        "srs_z_score": round(swing / se, 3),
        "z_score_if_deff_2": round(swing / (se * math.sqrt(2)), 3),
    }


def succession_ledger() -> dict[str, object]:
    """Rank the segments where Flávio trails his father in the same wave."""
    rows = [
        {
            "segment": segment,
            "jair_2022_scenario_pct": jair,
            "flavio_2026_pct": flavio,
            "delta_pp": round(flavio - jair, 1),
            "retention_pct": round(100 * flavio / jair, 1) if jair else None,
        }
        for segment, (jair, flavio) in SUCCESSION.items()
    ]
    ranked = sorted(
        (row for row in rows if row["segment"] != "Total"),
        key=lambda row: row["delta_pp"],
    )
    return {
        "total_delta_pp": round(SUCCESSION["Total"][1] - SUCCESSION["Total"][0], 1),
        "rows": rows,
        "largest_losses": ranked[:8],
        "most_retained": list(reversed(ranked[-6:])),
        "note": (
            "Ambos os números vêm da mesma onda e dos mesmos respondentes. "
            "A Atlas não publica bases por recorte, portanto a diferença não "
            "recebe intervalo: é descritiva, não inferencial."
        ),
    }


def fear_to_vote_conversion() -> dict[str, object]:
    """Find segments that fear Lula more than Flávio and still vote for Lula."""
    rows = []
    for segment, (
        fear_lula,
        fear_flavio,
        vote_lula,
        vote_flavio,
    ) in FEAR_VS_VOTE.items():
        fear_edge = round(fear_lula - fear_flavio, 1)
        vote_edge = round(vote_flavio - vote_lula, 1)
        rows.append(
            {
                "segment": segment,
                "fear_lula_pct": fear_lula,
                "fear_flavio_pct": fear_flavio,
                "flavio_fear_edge_pp": fear_edge,
                "vote_lula_pct": vote_lula,
                "vote_flavio_pct": vote_flavio,
                "flavio_vote_edge_pp": vote_edge,
                "conversion_gap_pp": round(fear_edge - vote_edge, 1),
            }
        )
    unconverted = sorted(
        (row for row in rows if row["segment"] != "Total"),
        key=lambda row: row["conversion_gap_pp"],
        reverse=True,
    )
    return {
        "rows": rows,
        "largest_unconverted_advantage": unconverted[:6],
        "note": (
            "conversion_gap = vantagem de Flávio no medo menos vantagem de "
            "Flávio no voto. Positivo significa que o recorte teme mais o "
            "adversário do que o candidato e ainda assim não o acompanha."
        ),
    }


def intensity_premium() -> dict[str, object]:
    """Compare both July polls on valid votes and rank the online premium.

    A razão Atlas/Datafolha sobre votos válidos isola quanto cada candidatura
    é ampliada (ou reduzida) por um painel digital autosselecionado em relação
    a uma coleta presencial em ponto de fluxo. Não identifica a causa: mede a
    distância entre os dois desenhos, candidato a candidato.
    """
    atlas_total = sum(FIRST_ROUND_ATLAS.values())
    datafolha_total = sum(FIRST_ROUND_DATAFOLHA.values())
    rows = []
    for name in FIRST_ROUND_ATLAS:
        if name not in FIRST_ROUND_DATAFOLHA:
            continue
        atlas_valid = 100 * FIRST_ROUND_ATLAS[name] / atlas_total
        datafolha_valid = 100 * FIRST_ROUND_DATAFOLHA[name] / datafolha_total
        rows.append(
            {
                "candidate": name,
                "atlas_raw_pct": FIRST_ROUND_ATLAS[name],
                "datafolha_raw_pct": FIRST_ROUND_DATAFOLHA[name],
                "atlas_valid_pct": round(atlas_valid, 2),
                "datafolha_valid_pct": round(datafolha_valid, 2),
                "ratio": round(atlas_valid / datafolha_valid, 2),
            }
        )
    rows.sort(key=lambda row: row["ratio"], reverse=True)
    return {
        "valid_vote_base": {
            "atlas": round(atlas_total, 1),
            "datafolha": round(datafolha_total, 1),
        },
        "non_choice_pct": NON_CHOICE,
        "rows": rows,
        "reading": (
            "Sobre votos válidos, os dois institutos praticamente coincidem "
            "nos dois grandes (razão 0,99 em Lula e em Flávio) e divergem só "
            "nas candidaturas de movimento — Missão e UP para cima, "
            "governadores e Cury para baixo. O padrão é simétrico entre "
            "direita e esquerda, o que aponta para intensidade militante "
            "online, não para viés partidário do instituto."
        ),
    }


def datafolha_cluster_math() -> dict[str, object]:
    """Translate the Datafolha deff thresholds into intracluster correlation."""
    return {
        "design": (
            "331 setores censitários, 328 deles com exatamente 6 entrevistas "
            "(BR-01166/2026, campo 22-23/07/2026)."
        ),
        "cluster_size": DATAFOLHA_CLUSTER_SIZE,
        "implied_rho": {
            name: round(intracluster_rho(deff, DATAFOLHA_CLUSTER_SIZE), 4)
            for name, deff in DATAFOLHA_DEFF_THRESHOLDS.items()
        },
        "reading": (
            "Kish: deff = 1 + (m - 1) * rho. Para a vantagem de 5 pontos no "
            "2º turno deixar de ser significativa basta rho = 0,088 entre "
            "vizinhos do mesmo setor. Para a vantagem de 8 pontos no 1º turno "
            "cair, seria preciso rho = 0,736 — implausível. O 1º turno "
            "sobrevive; o 2º turno, não."
        ),
    }


def build_audit() -> dict:
    srs = moe_srs(N_ATLAS)
    deff_sensitivity = {
        str(deff): round(srs * math.sqrt(deff), 3) for deff in (1.0, 1.5, 2.0, 2.5, 3.0)
    }
    renan_observed = 0.078
    overcapture = {
        f"{int(100 * fraction)}%": {
            "adjusted_share_pct": round(
                100 * remove_full_support_overcapture(renan_observed, fraction), 3
            ),
            "shift_pp": round(
                100
                * (
                    renan_observed
                    - remove_full_support_overcapture(renan_observed, fraction)
                ),
                3,
            ),
        }
        for fraction in (0.01, 0.03, 0.05)
    }
    diaspora_right = round(
        sum(
            share
            for name, share in BOLSONARO_2022_DIASPORA.items()
            if name
            not in {
                "Flávio Bolsonaro",
                "Lula",
                "Não sei",
                "Voto branco/nulo",
                "Samara Martins",
            }
        ),
        1,
    )
    return {
        "poll": {
            "registration": "BR-08602/2026",
            "published_n": N_ATLAS,
            "field": "2026-07-22/2026-07-27",
        },
        "sampling_math": {
            "srs_moe_95_pct_at_50_pp": round(srs, 3),
            "n_required_for_1_pp": required_n(1.0),
            "moe_by_assumed_deff_pp": deff_sensitivity,
            "note": (
                "DEFF values are sensitivity scenarios, not estimates. "
                "Nonprobability selection bias is not identified by this calculation."
            ),
        },
        "renan_overcapture_sensitivity": overcapture,
        "gender_gap_instability": gender_gap_instability(),
        "succession_ledger": succession_ledger(),
        "fear_to_vote_conversion": fear_to_vote_conversion(),
        "bolsonaro_2022_diaspora": {
            "rows": BOLSONARO_2022_DIASPORA,
            "stays_with_flavio_pct": BOLSONARO_2022_DIASPORA["Flávio Bolsonaro"],
            "moves_to_other_right_pct": diaspora_right,
            "moves_to_lula_pct": BOLSONARO_2022_DIASPORA["Lula"],
            "reading": (
                "O eleitor de Jair/2022 que não está com Flávio não migrou "
                "para Lula: migrou para outros candidatos de direita. A perda "
                "de 1º turno é recuperável por consolidação, não por conversão."
            ),
        },
        "government_areas": {
            area: {"lula": lula, "flavio": flavio, "gap_pp": lula - flavio}
            for area, (lula, flavio) in GOVERNMENT_AREAS.items()
        },
        "intensity_premium": intensity_premium(),
        "datafolha_cluster_math": datafolha_cluster_math(),
        "cross_poll_check": {
            "atlas_renan_pct": 7.8,
            "datafolha_renan_pct": 3.0,
            "quaest_renan_pct": 3.0,
            "atlas_minus_each_pp": 4.8,
        },
        "interpretation": {
            "national_operational_band_pp": [4, 6],
            "fragile_subgroup_band_pp": [8, 12],
            "warning": (
                "These are audit reading bands, not formal confidence intervals. "
                "Atlas would need recruitment probabilities, weights, DEFF and a "
                "validated nonprobability model to identify a formal interval."
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/assets/atlas_072026_audit.json"),
    )
    args = parser.parse_args()
    audit = build_audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(audit["sampling_math"], ensure_ascii=False))
    for row in audit["succession_ledger"]["largest_losses"]:
        print(f'  {row["segment"]:<32} {row["delta_pp"]:+.1f} pp')
    print("\nprêmio de intensidade (Atlas/Datafolha sobre votos válidos):")
    for row in audit["intensity_premium"]["rows"]:
        print(
            f'  {row["candidate"]:<20} {row["atlas_valid_pct"]:>6.2f} x '
            f'{row["datafolha_valid_pct"]:>5.2f}  =  {row["ratio"]:.2f}x'
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
