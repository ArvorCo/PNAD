#!/usr/bin/env python3
"""Integrate all archived Explorer versions; keep superseded samples out of means."""

import importlib.util
import json
from copy import deepcopy
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "analysis/reponderacao"
EXPLORER = BASE / "palver_explorer_20260921"
POLLS = BASE / "pesquisas"
URL = "https://www.palver.com.br/survey/explore"
NAMES = {
    "Lula (PT)": "lula",
    "Flávio Bolsonaro (PL)": "flavio",
    "Renan Santos (Missão)": "renan_santos",
    "Escritor Augusto Cury (Avante)": "cury",
    "Ronaldo Caiado (PSD)": "caiado",
    "Zema (Novo)": "zema",
    "Samara (UP)": "samara",
    "Pablo Marçal (PRTB)": "marcal",
    "Outros": "outros",
    "Branco/nulo ou não votaria": "branco_nulo",
    "Indecisos": "indecisos",
}
WAVES = [
    (
        "01_pesquisa_2026_08_10",
        "palver_2026-08-09",
        "2026-08-03",
        "2026-08-09",
        "2026-08-10",
        "BR-06596/2026",
        "Onda 1",
        "09/08",
    ),
    (
        "02_pesquisa_2026_09_09",
        "palver_2026-09-07",
        "2026-09-04",
        "2026-09-07",
        "2026-09-09",
        "BR-05420/2026",
        "Onda 2 original · substituída",
        "07/09 v1",
    ),
    (
        "02_pesquisa_2026_09_21",
        "palver_2026-09-07_v2",
        "2026-09-04",
        "2026-09-07",
        "2026-09-21",
        "BR-06100/2026",
        "Onda 2 revisada",
        "07/09 v2",
    ),
    (
        "03_pesquisa_2026_09_21",
        "palver_2026-09-18",
        "2026-09-15",
        "2026-09-18",
        "2026-09-21",
        "BR-00860/2026",
        "Onda 3",
        "18/09",
    ),
]
QUESTIONS = {"1t": "stimulated_1r_vote_1_h", "2t": "lula_flavio"}


def read(path):
    return json.loads(path.read_text())


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def integrate():
    spec = importlib.util.spec_from_file_location(
        "engine", ROOT / "scripts/reponderacao-pnad.py"
    )
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    benchmark, ipca = engine.Benchmark(), engine.load_ipca()
    audit = read(EXPLORER / "audit.json")
    dump(ROOT / "docs/assets/palver_explorer_auditoria.json", audit)
    template = read(POLLS / "palver_2026-09-18.json")
    history = []
    for wid, ident, start, end, release, registry, title, tick in WAVES:
        path = POLLS / f"{ident}.json"
        previous = read(path) if path.exists() else {}
        poll = {
            "id": ident,
            "instituto": "Palver",
            "contratante": "Palver (iniciativa própria)",
            "registro_tse": registry,
            "campo": {"inicio": start, "fim": end},
            "divulgacao": release,
            "n": 5000,
            "metodo": template["metodo"],
            "renda": deepcopy(template["renda"]),
            "publicado": {},
            "cruzamentos": {},
        }
        original_pdf = previous.get("publicado_pdf")
        if original_pdf is None and previous.get("fonte", {}).get("tipo") != "explorer":
            original_pdf = previous.get("publicado")
        if original_pdf:
            poll["publicado_pdf"] = original_pdf
        poll["fonte"] = {
            "tipo": "explorer",
            "url": URL
            + "?"
            + urlencode(
                {"wave": wid, "question": "lula_flavio", "breakdown": "inc_std"}
            ),
            "rotulo": f"Palver · {title}",
            "onda_explorer": wid,
            "snapshot": f"analysis/reponderacao/palver_explorer_20260921/{wid}/",
            "nota": f"{title}. Percentuais exatos do Explorer, sem arredondar o placar de partida. "
            "Distribuição ponderada de renda recuperada por sistema linear e validada contra os dois turnos e o n efetivo. "
            "Os n por faixa são contagens brutas, não os pesos de composição.",
        }
        if ident == "palver_2026-09-18":
            poll["fonte"]["nota"] += (
                " O catálogo encerra o campo em 20/09; mantemos 18/09 conforme o PDF. Divergência documental pendente."
            )
        if ident.endswith("_v2"):
            poll["fonte"]["nota"] += (
                " O PDF p. 30 mostra Lula 41% no 1º turno; o Explorer registra 40,440%. Versões preservadas, sem misturar os valores."
            )
        if wid.startswith("01_"):
            poll["fonte"]["campo_fonte"] = (
                "https://github.com/palverdata/pesquisa-palver/blob/7523cf14f0095f088ac9680e9c64a9923289fdb1/ondas/2026-08-10/config.yaml"
            )
        margin = audit["waves"][wid]["margins"]["inc_std"]
        assert margin["identified"] and margin["max_residual"] < 1e-10
        poll["renda"].update(
            amostra_pct=margin["weighted_pct"],
            perfil_tipo="perfil_ponderado_reconstituido",
            nota="Margem ponderada recuperada das tabelas exatas do Explorer, com posto completo e "
            "recomposição dos dois turnos e do n efetivo. Não usar as contagens brutas como pesos. "
            "Referência da Palver: PNADC 2024, visita 5. Valores nominais em salários mínimos de 2026.",
        )
        for turn, question in QUESTIONS.items():
            total_file = read(EXPLORER / wid / f"{question}--total.json")
            cross_file = read(EXPLORER / wid / f"{question}--inc_std.json")
            total, cross = total_file["tables"][0], cross_file["tables"][0]
            poll["publicado"][turn] = {
                NAMES[c["answer"]]: 100 * c["share"] for c in total["cells"]
            }
            answers = cross["answers"]
            cells = {
                (c["group"], c["answer"]): 100 * c["share"] for c in cross["cells"]
            }
            poll["cruzamentos"][turn] = {
                "opcoes": [NAMES[a] for a in answers],
                "linhas": [[cells[g, a] for a in answers] for g in cross["groups"]],
                "nota": "Tabela pública do Explorer; percentuais sem arredondamento e todas as alternativas expostas.",
                "proveniencia": {
                    "total": total_file["source"],
                    "renda": cross_file["source"],
                },
            }
        superseded = ident == "palver_2026-09-07"
        if superseded:
            poll.update(
                ignorar=True,
                motivo="Onda 2 original substituída pela versão revisada; disponível no histórico da Palver, fora das médias para não duplicar a amostra.",
            )
        if superseded:
            # Keep the older PDF's alternative first-round scenario verbatim.
            # The Explorer scenario is a different ballot and belongs in history.
            previous.update(ignorar=True, motivo=poll["motivo"])
            dump(path, previous)
        else:
            dump(path, poll)
        processed = engine.process_poll(poll, benchmark, ipca)
        processed.update(
            rotulo_historico=title,
            rotulo_eixo=tick,
            substituida=superseded,
            primeiro_turno_com_marcal="marcal" in poll["publicado"]["1t"],
        )
        history.append(processed)
    dump(
        ROOT / "docs/assets/palver_explorer_historico.json",
        {
            "pesquisas": history,
            "nota": "Três ondas, quatro versões. A original da onda 2 é arquivo; cenários com Marçal não entram na média do 1º turno. Histórico usa todas as versões.",
        },
    )
    print(
        "Palver: 3 ondas ativas; 4 versões no histórico; 2 primeiros turnos elegíveis."
    )


if __name__ == "__main__":
    integrate()
