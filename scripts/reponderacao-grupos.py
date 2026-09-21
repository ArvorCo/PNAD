"""Grupos editoriais do 1º turno, sem repartir categorias não identificadas."""

import importlib.util
from datetime import date
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "rolling_window", Path(__file__).with_name("reponderacao-janela.py")
)
WINDOW = importlib.util.module_from_spec(spec)
spec.loader.exec_module(WINDOW)

GROUPS = {
    "outros_centro_direita": "Outros (centro-direita)",
    "outros_esquerda_nanicos": "Outros (esquerda + nanicos)",
}
CURRENT_CENTER = {"zema", "cury", "caiado", "renan_santos", "clariana"}
CENTER = CURRENT_CENTER | {"aecio", "aldo", "avalanche"}
NON_CHOICE = {"branco_nulo", "indecisos", "nao_sabe", "nenhum"}
LEADERS = {"lula", "flavio"}
CURRENT_LEFT = {"samara", "rui", "edmilson", "hertz", "grassi"}
LEFT_NANICOS = CURRENT_LEFT | {"joaquim", "ciro", "daciolo", "hero", "outros_esquerda"}


def split_poll(poll, scenario):
    result = poll.get("turnos", {}).get("1t")
    if not result:
        return None, "Sem cruzamento de renda do 1º turno."
    options = set(result["opcoes"])
    if "marcal" in options:
        return None, "Cenário com Marçal excluído do primeiro turno."
    if "outros" in options:
        return (
            None,
            "Residual outros sem divisão individual por renda entre os dois grupos.",
        )
    verified = poll.get("grupos_1t_fonte", {}).get("lista_completa")
    if not verified and not (CURRENT_CENTER | CURRENT_LEFT).issubset(options):
        missing = (CURRENT_CENTER | CURRENT_LEFT) - options
        return (
            None,
            "Sem lista histórica completa validada ou voto por renda de: "
            + ", ".join(sorted(missing))
            + ".",
        )
    # O publicado original pode ter nomes positivos omitidos do cruzamento.
    original = poll.get("publicado", {}).get("1t", result["publicado"])
    omitted = {
        k for k, v in original.items() if v > 0 and k not in options | NON_CHOICE
    }
    if omitted:
        return (
            None,
            "Candidaturas publicadas sem cruzamento: "
            + ", ".join(sorted(omitted))
            + ".",
        )
    unknown = options - CENTER - LEADERS - NON_CHOICE - LEFT_NANICOS
    if unknown:
        return (
            None,
            "Candidaturas sem classificação editorial: "
            + ", ".join(sorted(unknown))
            + ".",
        )
    center = options & CENTER
    rest = options & LEFT_NANICOS
    values = {
        "publicado": result["publicado"],
        "ajustado": result["cenarios"][scenario]["ajustado"],
    }
    return {
        "id": poll["id"],
        "instituto": poll["instituto"],
        "campo": poll["campo"],
        "divulgacao": poll.get("divulgacao"),
        "componentes": {
            "outros_centro_direita": sorted(center),
            "outros_esquerda_nanicos": sorted(rest),
        },
        **{
            kind: {
                "outros_centro_direita": round(sum(v[k] for k in center), 3),
                "outros_esquerda_nanicos": round(sum(v[k] for k in rest), 3),
            }
            for kind, v in values.items()
        },
        "fonte_grupos": poll.get(
            "grupos_1t_fonte",
            {
                "nota": "Cenário contemporâneo completo, com todos os nomes individualizados por renda."
            },
        ),
    }, None


def weighted(rows, kind, key, day, window_days=7):
    return WINDOW.mean(rows, kind, key, day, window_days)


def aggregate_groups(polls, dates, today, scenario, window_days):
    eligible, excluded = [], []
    for poll in polls:
        if "1t" not in poll["turnos"]:
            continue
        row, reason = split_poll(poll, scenario)
        if row:
            eligible.append(row)
        else:
            excluded.append(
                {"id": poll["id"], "instituto": poll["instituto"], "motivo": reason}
            )
    # A janela é retrospectiva e ancorada na divulgação, como a dos candidatos.
    start = min(
        (row["divulgacao"] for row in eligible if row.get("divulgacao")), default=None
    )
    series = {
        kind: {
            group: [
                (
                    weighted(
                        eligible, kind, group, date.fromisoformat(day), window_days
                    )
                    if start and day >= start
                    else None
                )
                for day in dates
            ]
            for group in GROUPS
        }
        for kind in ["publicado", "ajustado"]
    }
    latest = {}
    for row in sorted(eligible, key=lambda r: r["campo"]["fim"]):
        if row["campo"]["fim"] <= today.isoformat():
            latest[row["instituto"]] = row
    summary = {
        "kernel": {
            kind: {g: weighted(eligible, kind, g, today, window_days) for g in GROUPS}
            for kind in series
        },
        "media_simples": {
            kind: {
                g: (
                    round(sum(r[kind][g] for r in latest.values()) / len(latest), 2)
                    if latest
                    else None
                )
                for g in GROUPS
            }
            for kind in series
        },
    }
    return {
        "cobertura_movel": WINDOW.coverage(eligible, dates, window_days),
        "rotulos": GROUPS,
        "regra": "Centro-direita = Zema, Cury, Caiado, Renan Santos e Clariana Barão; no histórico, também Aécio Neves, Aldo Rebelo e Leonardo Avalanche. Esquerda + nanicos = Samara, Rui Costa Pimenta, Edmilson Costa, Hertz Dias e Wilson Grassi; no histórico, também Joaquim Barbosa, Ciro Gomes, Cabo Daciolo e Heró Bezerra. Grassi integra o residual de nanicos, sem ser classificado como esquerda; o mesmo rótulo residual não atribui ideologia uniforme aos demais. Classificação editorial. Brancos, nulos e indecisos ficam fora. Primeiro somamos os candidatos oferecidos em cada cenário; depois calculamos a média dos grupos.",
        "cobertura": "As duas linhas usam as mesmas ondas com divisão identificável por renda. Recuperamos nos relatórios as candidaturas antes somadas internamente em outros. Uma candidatura não oferecida não é exigida para incluir a onda; se nenhum nome de um grupo foi oferecido, sua soma naquele cenário é zero, não uma estimativa eleitoral para nomes ausentes. Isso difere de candidato oferecido sem cruzamento, que nunca vira zero. Categorias do instituto que misturam os dois grupos continuam excluídas. A composição das cédulas muda ao longo do tempo. Lula e Flávio usam um conjunto mais amplo; as quatro médias não formam uma partição somável.",
        "ondas": eligible,
        "excluidas": excluded,
        "ultima_onda_por_instituto": {name: row["id"] for name, row in latest.items()},
        "serie": series,
        "ultimo": summary,
    }
