"""Séries de indecisos e branco/nulo/não vai votar, com cobertura pareada."""

from datetime import date

LABELS = {"indecisos": "Indecisos", "branco_nulo": "Branco/nulo/não vai votar"}


def extract(poll, turn, scenario):
    result = poll.get("turnos", {}).get(turn)
    if not result:
        return None, "Sem cruzamento de renda deste turno."
    if turn == "1t" and "marcal" in result["opcoes"]:
        return None, "Cenário com Marçal excluído do primeiro turno."
    values = {
        "publicado": result["publicado"],
        "ajustado": result["cenarios"][scenario]["ajustado"],
    }
    required = set(LABELS)
    # O acervo padroniza B/N e 'não vai votar' em branco_nulo e NS em indecisos.
    # Ausência da chave nunca é zero. Ambas precisam estar medidas por renda.
    if not required <= set(result["opcoes"]) or any(
        any(v.get(key) is None for key in required) for v in values.values()
    ):
        return (
            None,
            "Não há separação completa de indecisos e branco/nulo/não vai votar por renda.",
        )
    blank = ["branco_nulo"] + [
        key for key in ("nao_vai_votar", "nao_votaria") if key in result["opcoes"]
    ]
    if any(any(v.get(key) is None for key in blank) for v in values.values()):
        return None, "Categoria não vai votar sem valor correspondente."
    return {
        "id": poll["id"],
        "instituto": poll["instituto"],
        "campo": poll["campo"],
        "componentes": {"indecisos": ["indecisos"], "branco_nulo": blank},
        **{
            kind: {
                "indecisos": v["indecisos"],
                "branco_nulo": sum(v[key] for key in blank),
            }
            for kind, v in values.items()
        },
    }, None


def average(rows, kind, key, day, half_life, causal=False):
    pairs = []
    for row in rows:
        end = date.fromisoformat(row["campo"]["fim"])
        if causal and end > day:
            continue
        pairs.append((0.5 ** (abs((day - end).days) / half_life), row[kind][key]))
    return (
        round(sum(w * v for w, v in pairs) / sum(w for w, _ in pairs), 2)
        if pairs
        else None
    )


def aggregate(polls, turn, dates, today, scenario, half_life):
    rows, excluded = [], []
    for poll in polls:
        if turn not in poll.get("turnos", {}):
            continue
        row, reason = extract(poll, turn, scenario)
        if row is None:
            excluded.append(
                {"id": poll["id"], "instituto": poll["instituto"], "motivo": reason}
            )
        else:
            rows.append(row)
    start = min((r["campo"]["fim"] for r in rows), default=None)
    series = {
        kind: {
            key: [
                (
                    average(rows, kind, key, date.fromisoformat(day), half_life)
                    if start and day >= start
                    else None
                )
                for day in dates
            ]
            for key in LABELS
        }
        for kind in ("publicado", "ajustado")
    }
    return {
        "rotulos": LABELS,
        "ondas": rows,
        "excluidas": excluded,
        "serie": series,
        "regra": "Mesma média móvel dos candidatos: peso 0,5^(distância em dias/14), "
        "alisador simétrico no histórico e somente campos encerrados no valor corrente. "
        "As duas linhas usam as mesmas ondas com ambas as categorias publicadas e cruzadas "
        "por renda; os pesos são idênticos antes e depois do ajuste. Não há preenchimento "
        "por zero nem por complemento de 100%. Branco/nulo inclui não vai votar quando "
        "essa resposta está agregada pelo instituto; parcelas separadas são somadas antes "
        "da média. Indecisos inclui não sabe conforme a codificação da fonte. Os rótulos "
        "e a oferta dessas respostas variam entre institutos. Não vai votar é declaração "
        "de intenção, não estimativa de abstenção. A cobertura difere da dos candidatos; "
        "as linhas não formam uma partição que some 100%.",
        "ultimo": {
            kind: {
                key: average(rows, kind, key, today, half_life, causal=True)
                for key in LABELS
            }
            for kind in series
        },
    }
