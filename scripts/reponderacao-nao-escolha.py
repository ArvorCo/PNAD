"""Séries de indecisos e branco/nulo/não vai votar, com cobertura pareada."""

import importlib.util
from datetime import date
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "rolling_window", Path(__file__).with_name("reponderacao-janela.py")
)
WINDOW = importlib.util.module_from_spec(spec)
spec.loader.exec_module(WINDOW)

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
        "divulgacao": poll.get("divulgacao"),
        "componentes": {"indecisos": ["indecisos"], "branco_nulo": blank},
        **{
            kind: {
                "indecisos": v["indecisos"],
                "branco_nulo": sum(v[key] for key in blank),
            }
            for kind, v in values.items()
        },
    }, None


def average(rows, kind, key, day, window_days=7):
    return WINDOW.mean(rows, kind, key, day, window_days)


def aggregate(polls, turn, dates, today, scenario, window_days):
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
    start = min((r["divulgacao"] for r in rows if r.get("divulgacao")), default=None)
    series = {
        kind: {
            key: [
                (
                    average(rows, kind, key, date.fromisoformat(day), window_days)
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
        "cobertura_movel": WINDOW.coverage(rows, dates, window_days),
        "rotulos": LABELS,
        "ondas": rows,
        "excluidas": excluded,
        "serie": series,
        "regra": "Mesma média móvel retrospectiva de 7 dias dos candidatos: divulgações de D-6 a D, "
        "última onda elegível de cada instituto e peso igual entre casas. "
        "As duas linhas usam as mesmas ondas com ambas as categorias publicadas e cruzadas "
        "por renda; os pesos são idênticos antes e depois do ajuste. Não há preenchimento "
        "por zero nem por complemento de 100%. Branco/nulo inclui não vai votar quando "
        "essa resposta está agregada pelo instituto; parcelas separadas são somadas antes "
        "da média. Indecisos inclui não sabe conforme a codificação da fonte. Os rótulos "
        "e a oferta dessas respostas variam entre institutos. Não vai votar é declaração "
        "de intenção, não estimativa de abstenção. A cobertura difere da dos candidatos; "
        "as linhas não formam uma partição que some 100%.",
        "ultimo": {
            kind: {key: average(rows, kind, key, today, window_days) for key in LABELS}
            for kind in series
        },
    }
