#!/usr/bin/env python3
"""Gera a previsão presidencial, CSV, HTML e snapshot verificável do corte."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from datetime import date, datetime
from zoneinfo import ZoneInfo

from ga_tag import injetar
from predicao_2026.base import ELECTION, WINDOW_START, national, read, state_polls
from predicao_2026.consolidacao import consolidation
from predicao_2026.erro_2022 import SENS_INVERTED, SENS_REPEAT
from predicao_2026.erro_2022 import block as error_2022_block
from predicao_2026.erro_2022 import shifts as error_2022_shifts
from predicao_2026.motor import (
    DEFAULTS,
    DEFF,
    HALF_LIFE,
    POOL_STRENGTH,
    PROJECTED,
    scenario,
    simulate,
    territory,
)
from predicao_2026.preditiva import run as predictive_validation
from predicao_2026.recencia import NATIONAL_HALF_LIFE
from predicao_2026.rejeicao import block as rejection_block
from predicao_2026.rejeicao import resolve as resolve_rejection
from predicao_2026.tse import ROOT, sha
from predicao_2026.view import render

ASSET = ROOT / "docs/assets/predicao_2026_1T_presidente.json"
CENTRAL_LABEL = "Central: recência com tendência de 28 dias encolhida, indecisos por disponibilidade"
CONS_LABEL = "Consolidação na proporção medida, 28 dias"


def central_comparison(central, consolidated, national, cons):
    """Central nova contra o cenário de consolidação de 28 dias sobre inclusivo."""
    a, b = central["brasil"], consolidated["brasil"]
    sloped = national["tendencia"]["central_com_inclinacao"]
    return {
        "central_margem_pp": a["margem_flavio_lula"],
        "consolidacao_28_sobre_inclusivo_margem_pp": b["margem_flavio_lula"],
        "diferenca_pp": a["margem_flavio_lula"] - b["margem_flavio_lula"],
        "central_validos_pct": a["percentuais"],
        "consolidacao_validos_pct": b["percentuais"],
        "horizonte_dias_central": sloped["horizonte_dias"],
        "horizonte_dias_consolidacao": cons["horizonte_dias"],
        "nota": (
            "Os dois prolongam a mesma tendência de 28 dias pelo mesmo horizonte "
            "a partir da âncora inclusivo; a central encolhe cada inclinação "
            "pelo fator b² / (b² + ep²) e desloca as três parcelas dos válidos, "
            "enquanto o cenário de consolidação não encolhe, tira a migração só "
            "da terceira via e a converte em fração da reserva de 2º turno de "
            "cada finalista (λ arredondado), aplicada UF a UF."
        ),
    }


PREDICTIVE = ROOT / "docs/assets/predicao_2026_validacao_preditiva.json"
PAGE = ROOT / "docs/predicao_2026_1T_presidente.html"


def build(
    today, runs=6000, national_half_life=NATIONAL_HALF_LIFE, state_half_life=HALF_LIFE
):
    if today > ELECTION:
        raise ValueError(
            "Previsão pré-eleitoral exige corte em ou antes de 04/10/2026; não incorporar apuração"
        )
    tse = read(ROOT / "data/outputs/predicao_2026/tse.json")
    for metadata in (tse["locais_metadata"], tse["perfil_metadata"]):
        generated = datetime.strptime(metadata["DT_GERACAO"], "%d/%m/%Y").date()
        if generated > today:
            raise ValueError(
                "Cadastro TSE posterior ao corte: não usar em uma previsão retrospectiva"
            )
    validation = read(ROOT / "data/outputs/predicao_2026/validacao.json")
    n = national(today, national_half_life)
    polls, excluded = state_polls(today)
    states, iterations = territory(polls, n, tse, today, state_half_life)
    predictive = predictive_validation(n["pesquisas"], window_start=WINDOW_START)
    consolidacao = consolidation(
        n["pesquisas"], n["selecionadas"], states, today, ELECTION
    )
    measured = consolidacao["projecao"]["28"]["lambda_arredondado"]
    rejeicao = rejection_block(consolidacao, today, half_life=national_half_life)
    available = rejeicao["consolidacao_disponibilidade"]["28"]["lambda_arredondado"]
    # Central: âncora com tendência encolhida (DEFAULTS["base"]) e indecisos
    # por disponibilidade, resolvida para número; o motor segue numérico.
    central_params = resolve_rejection(
        {**DEFAULTS, "indecisos_flavio": "disponibilidade"}, rejeicao
    )
    central = scenario(states, central_params)
    mc = simulate(states, n, central_params, runs=runs)
    predictive["referencia"] = today.isoformat()
    # Testes de aceleração dentro da amostra, ao lado da comparação preditiva.
    predictive["aceleracao"]["dentro_da_amostra"] = n["tendencia"]["aceleracao"]
    # Erro comum de 2022 nas duas direções: medição histórica como cenário,
    # nunca ajuste da central. Valores lidos do JSON, não digitados.
    repeat_2022, inverted_2022 = error_2022_shifts()
    # Toda sensibilidade parte da central e troca só o que o rótulo diz.
    scenarios = {
        CENTRAL_LABEL: {},
        "Recência sem tendência (central anterior)": {
            "base": "inclusivo",
            "indecisos_flavio": None,
        },
        "Indecisos proporcionais às candidaturas": {"indecisos_flavio": None},
        "Recência sem tendência, indecisos por disponibilidade": {"base": "inclusivo"},
        "Mesmas casas centrais, peso temporal igual": {"base": "sem_recencia"},
        "Somente casas com reponderação PNAD": {"base": "pnad"},
        "Publicadas, mesmas casas": {"base": "publicado"},
        "Publicadas, todas as casas elegíveis": {"base": "todas"},
        "Âncora dinâmica (DLM com efeitos de casa)": {"base": "dinamico"},
        "Âncora de tendência projetada a 04/10": {"base": "tendencia"},
        "Âncora de tendência, nível no corte": {"base": "tendencia_corte"},
        "Recência sem tendência + desvio relativo das casas removido": {
            "base": "casas"
        },
        "Sem seleção de eleitor provável": {"eleitor_provavel": False},
        "Comparecimento por seção, pesos de 2026": {"comparecimento_modelo": "secoes"},
        "Flávio antecipa 25% da reserva": {"voto_flavio": 0.25},
        "Lula antecipa 25% da reserva": {"voto_lula": 0.25},
        "Os dois antecipam 25% da reserva": {"voto_lula": 0.25, "voto_flavio": 0.25},
        "Comparecimento de Flávio 3 pp acima de Lula": {"diferencial_pp": 3},
        "Comparecimento de Lula 3 pp acima de Flávio": {"diferencial_pp": -3},
        SENS_REPEAT: {"vies_pp": repeat_2022},
        SENS_INVERTED: {"vies_pp": inverted_2022},
        CONS_LABEL: {
            "base": consolidacao["ancora"],
            "voto_lula": measured["lula"],
            "voto_flavio": measured["flavio"],
        },
        "Consolidação 28 dias, divisão por disponibilidade": {
            "base": consolidacao["ancora"],
            "voto_lula": available["lula"],
            "voto_flavio": available["flavio"],
        },
    }
    sensitivities = {
        label: scenario(states, {**central_params, **params})
        for label, params in scenarios.items()
    }
    consolidacao["comparacao_central"] = central_comparison(
        sensitivities[CENTRAL_LABEL], sensitivities[CONS_LABEL], n, consolidacao
    )
    valid_sources = [
        p
        for p in n["selecionadas"]
        if all(
            k in p["previsao_opcoes"]
            for k in ("renan_santos", "cury", "caiado", "zema")
        )
    ]
    code = [
        ROOT / "scripts/predicao-2026-build.py",
        ROOT / "scripts/predicao-2026-estaduais.py",
        ROOT / "scripts/predicao_2026/base.py",
        ROOT / "scripts/predicao_2026/recencia.py",
        ROOT / "scripts/predicao_2026/motor.py",
        ROOT / "scripts/predicao_2026/tse.py",
        ROOT / "scripts/predicao_2026/validacao.py",
        ROOT / "scripts/predicao_2026/dinamico.py",
        ROOT / "scripts/predicao_2026/preditiva.py",
        ROOT / "scripts/predicao_2026/tendencia.py",
        ROOT / "scripts/predicao_2026/migracao.py",
        ROOT / "analysis/predicao_2026/tendencia/migracao_declarada.json",
        ROOT / "analysis/predicao_2026/tendencia/estaduais_rotulos.json",
        ROOT / "scripts/predicao_2026/consolidacao.py",
        ROOT / "scripts/predicao_2026/rejeicao.py",
        ROOT / "analysis/predicao_2026/rejeicao/rejeicao_092026.json",
        ROOT / "scripts/predicao_2026/erro_2022.py",
        ROOT / "docs/assets/predicao_2026.js",
    ]
    payload = {
        "schema": 2,
        "referencia": today.isoformat(),
        "eleicao": ELECTION.isoformat(),
        "natureza": "Previsão experimental condicional; probabilidades não calibradas historicamente",
        "configuracao": {
            "defaults": DEFAULTS,
            "central": central_params,
            "central_regra": "Âncora central_inclinacao (recência com meia-vida nacional e inclinação de 28 dias encolhida, projetada a 04/10) e indecisos que escolhem divididos por disponibilidade (1 − rejeição). Validada por origem móvel contra pesquisas, não contra a urna.",
            "deff_assumido": DEFF,
            "meia_vida_nacional_dias": national_half_life,
            "meia_vida_estadual_dias": state_half_life,
            "peso_prior": POOL_STRENGTH,
            "normalizacao": "truncar negativos aditivos, normalizar partições",
            "incerteza": {
                "base": central_params["base"],
                "indecisos_flavio": central_params["indecisos_flavio"],
                "recentramento": "bootstrap das casas centrais deslocado por alvos[base] − alvos.inclusivo em toda âncora calculada sobre as mesmas casas",
                "projecao_inclinacao": {
                    "aplica_em": list(PROJECTED),
                    "dp_margem_pp": n["incerteza_projecao_pp"],
                    "regra": "choque comum adicional na diferença F−L, somado em quadratura ao erro comum: sd = √(erro_comum² + dp_projeção²). Central com inclinação: horizonte × dp(β_F − β_L) das inclinações brutas de 28 dias, sem encolher. Tendência: √(dp_projetado² − dp_corte²) do filtro.",
                    "erro_comum_total_sd_pp": mc["erro_comum_total_sd_pp"],
                },
                "erro_comum_sd_margem_validos_pp": 2,
                "student_df": 5,
                "preferencia_regional_sd_pp": 1,
                "comparecimento_sd_pp": {"nacional": 1, "regional": 1.5, "uf": 1},
                "invalidos_sd_pp": 0.8,
            },
            "codigo": {str(p.relative_to(ROOT)): sha(p) for p in code},
        },
        "nacional": n,
        "estados": states,
        "estaduais_excluidas": excluded,
        "fontes_inspecionadas": (
            read(
                ROOT
                / "analysis/predicao_2026/atualizacao_20261003/fontes_inspecionadas.json"
            )
            if today >= date(2026, 10, 3)
            else []
        ),
        "central": central,
        "incerteza": mc,
        "sensibilidades": sensitivities,
        "consolidacao": consolidacao,
        "rejeicao": rejeicao,
        "erro_2022": error_2022_block(n["efeitos_casa"]),
        "validacao": validation,
        "validacao_preditiva": predictive,
        "calibracao_iteracoes": iterations,
        "abertura_demais": {
            "casas_nacionais": [p["id"] for p in valid_sources],
            "limite": "Distribuição dos demais condicionada às casas com abertura e recência; PNAD quando disponível, publicada nas demais; sem IC individual; mesma abertura central nas alternativas",
        },
        "fontes_tse": tse["fontes"],
        "fontes_prior": [
            {"arquivo": str(p.relative_to(ROOT)), "sha256": sha(p)}
            for p in (
                ROOT / "analysis/voto_util/tse_2022_uf.json",
                ROOT / "analysis/predicao_2026/tse_2022_exterior.json",
            )
        ],
        "tse_metadata": {
            k: tse[k]
            for k in (
                "perfil_metadata",
                "locais_metadata",
                "validacao_2022",
                "aptos_nao_instaladas_excluidos_2022",
            )
        },
        "qualidade": {
            "secoes_2022": tse["secoes_historicas_2022"],
            "secoes_2026": sum(u["secoes"] for u in tse["ufs"].values()),
            "pareamento_eleitores_pct": 100
            * sum(u["pareados_eleitores"] for u in tse["ufs"].values())
            / sum(u["eleitorado"] for u in tse["ufs"].values()),
            "diferenca_locais_perfil_eleitores": sum(
                u["eleitorado"] - u["eleitorado_perfil"] for u in tse["ufs"].values()
            ),
            "demografia_uf_sem_imputacao_secao": True,
            "n_ufs_cruzamento_comparecimento": sum(
                s["sinal_comparecimento"] is not None for s in states
            ),
            "n_estaduais_novas_integradas": sum(
                p["arquivo"].startswith("analysis/predicao_2026/estaduais/")
                for s in states
                for p in s["pesquisas"]
            ),
            "sem_validacao_presidencial_completa": True,
        },
    }
    payload["hash_modelo"] = hashlib.sha256(
        json.dumps(
            payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        ).encode()
    ).hexdigest()
    payload["gerado_em"] = datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat(
        timespec="seconds"
    )
    text = json.dumps(payload, ensure_ascii=False, indent=1) + "\n"
    ASSET.write_text(text, encoding="utf-8")
    PREDICTIVE.write_text(
        json.dumps(
            {**predictive, "hash_modelo": payload["hash_modelo"]},
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )
    snapshots = ROOT / "analysis/predicao_2026/snapshots"
    snapshots.mkdir(parents=True, exist_ok=True)
    snapshot = snapshots / f"{today.isoformat()}_{payload['hash_modelo'][:12]}.json"
    if not snapshot.exists():
        snapshot.write_text(text, encoding="utf-8")
    columns = [
        "uf",
        "regiao",
        "eleitorado",
        "comparecimento",
        "abstencao",
        "branco_nulo",
        "lula",
        "flavio",
        "outros",
        "lula_validos_pct",
        "flavio_validos_pct",
        "outros_validos_pct",
        "hash_modelo",
    ]
    with ASSET.with_suffix(".csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in central["ufs"]:
            out = {k: row[k] for k in columns if k in row}
            valid = sum(row[k] for k in ("lula", "flavio", "outros"))
            out.update(
                {
                    f"{k}_validos_pct": 100 * row[k] / valid
                    for k in ("lula", "flavio", "outros")
                }
            )
            out["hash_modelo"] = payload["hash_modelo"]
            writer.writerow(out)
    template = (ROOT / "docs/predicao_2026_1T_presidente.template.html").read_text(
        encoding="utf-8"
    )
    PAGE.write_text(injetar(render(payload, template)), encoding="utf-8")
    print(
        json.dumps(
            {
                "pagina": str(PAGE),
                "hash": payload["hash_modelo"],
                "central": central["brasil"]["percentuais"],
                "faixa_margem": mc["margem"],
                "snapshot": str(snapshot),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--hoje",
        type=date.fromisoformat,
        default=datetime.now(ZoneInfo("America/Sao_Paulo")).date(),
    )
    parser.add_argument("--sorteios", type=int, default=6000)
    parser.add_argument("--meia-vida-nacional", type=float, default=NATIONAL_HALF_LIFE)
    parser.add_argument("--meia-vida-estadual", type=float, default=HALF_LIFE)
    parser.add_argument(
        "--skip-card",
        action="store_true",
        help="Não renderiza o social card, útil sem Chrome",
    )
    parser.add_argument(
        "--refresh-agregador",
        action="store_true",
        help="Recalcula dados e página PNAD usando as transcrições já integradas",
    )
    args = parser.parse_args()
    if args.hoje > ELECTION:
        parser.error("Corte pós-eleição não é permitido para este modelo pré-eleitoral")
    if args.sorteios < 100:
        parser.error("Simulação requer ao menos 100 sorteios")
    from predicao_2026.recencia import decay

    for half_life in (args.meia_vida_nacional, args.meia_vida_estadual):
        try:
            decay(0, half_life)
        except ValueError as exc:
            parser.error(str(exc))
    if args.refresh_agregador:
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/reponderacao-pnad.py"),
                "calcular",
                "--hoje",
                args.hoje.isoformat(),
            ],
            check=True,
            cwd=ROOT,
        )
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/reponderacao-build.py"),
                "--skip-home",
            ],
            check=True,
            cwd=ROOT,
        )
    build(args.hoje, args.sorteios, args.meia_vida_nacional, args.meia_vida_estadual)
    if not args.skip_card:
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/social-cards.py"),
                "--only",
                "predicao_2026_1T_presidente",
            ],
            check=True,
            cwd=ROOT,
        )


if __name__ == "__main__":
    main()
