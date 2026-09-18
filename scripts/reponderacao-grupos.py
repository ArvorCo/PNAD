"""Grupos editoriais do 1º turno, sem repartir categorias não identificadas."""

from datetime import date

GROUPS = {
    "outros_centro_direita": "Outros (centro-direita)",
    "outros_esquerda_nanicos": "Outros (esquerda + nanicos)",
}
CENTER = {"zema", "cury", "caiado", "renan_santos", "clariana"}
NON_CHOICE = {"branco_nulo", "indecisos", "nao_sabe", "nenhum"}
LEADERS = {"lula", "flavio"}
LEFT_NANICOS = {"samara", "rui", "edmilson", "hertz", "grassi"}


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
    missing = CENTER - options
    if missing:
        return (
            None,
            "Sem voto por renda individualizado de: "
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
    rest = options & LEFT_NANICOS
    if not rest:
        return None, "Sem categoria identificada para as demais candidaturas."
    values = {
        "publicado": result["publicado"],
        "ajustado": result["cenarios"][scenario]["ajustado"],
    }
    return {
        "id": poll["id"],
        "instituto": poll["instituto"],
        "campo": poll["campo"],
        "componentes": {
            "outros_centro_direita": sorted(CENTER),
            "outros_esquerda_nanicos": sorted(rest),
        },
        **{
            kind: {
                "outros_centro_direita": round(sum(v[k] for k in CENTER), 3),
                "outros_esquerda_nanicos": round(sum(v[k] for k in rest), 3),
            }
            for kind, v in values.items()
        },
    }, None


def weighted(rows, kind, group, day, half_life, causal=False):
    pairs = []
    for row in rows:
        end = date.fromisoformat(row["campo"]["fim"])
        if causal and end > day:
            continue
        weight = 0.5 ** (abs((day - end).days) / half_life)
        pairs.append((weight, row[kind][group]))
    if not pairs:
        return None
    return round(sum(w * v for w, v in pairs) / sum(w for w, _ in pairs), 2)


def aggregate_groups(polls, dates, today, scenario, half_life):
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
    # Mantém a convenção do gráfico existente, com alisador simétrico,
    # mas não extrapola grupos para antes da primeira onda identificável.
    start = min((row["campo"]["fim"] for row in eligible), default=None)
    series = {
        kind: {
            group: [
                (
                    weighted(eligible, kind, group, date.fromisoformat(day), half_life)
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
            kind: {
                g: weighted(eligible, kind, g, today, half_life, causal=True)
                for g in GROUPS
            }
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
        "rotulos": GROUPS,
        "regra": "Centro-direita = Zema + Cury + Caiado + Renan Santos + Clariana Barão. Esquerda + nanicos = Samara, Rui Costa Pimenta, Edmilson Costa, Hertz Dias e Wilson Grassi; Grassi integra o residual de nanicos, sem ser classificado como esquerda. Classificação editorial, não atributo medido pelo instituto. Brancos, nulos e indecisos ficam fora. Primeiro somamos os candidatos por onda; depois calculamos a média dos grupos.",
        "cobertura": "As duas linhas usam as mesmas ondas com divisão identificável por renda; não se reparte outros nem se preenche candidato sem cruzamento com zero, mesmo que tenha arredondado para 0% no total. Lula e Flávio usam todas as ondas elegíveis sem Marçal, um conjunto mais amplo. Por isso, as quatro médias não formam uma partição somável.",
        "ondas": eligible,
        "excluidas": excluded,
        "ultima_onda_por_instituto": {name: row["id"] for name, row in latest.items()},
        "serie": series,
        "ultimo": summary,
    }
