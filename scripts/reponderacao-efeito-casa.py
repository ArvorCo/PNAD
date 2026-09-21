"""Desvio contemporâneo dos placares publicados; não identifica viés contra a verdade."""

from datetime import date
from statistics import median


def midpoint(poll):
    start = date.fromisoformat(poll["campo"]["inicio"]).toordinal()
    end = date.fromisoformat(poll["campo"]["fim"]).toordinal()
    if end < start:
        raise ValueError(f"Campo invertido: {poll['id']}")
    return (start + end) / 2


def valid_gap(poll):
    values = poll.get("publicado", {}).get("2t", {})
    if not all(k in values for k in ("lula", "flavio")):
        return None
    lula, flavio = values["lula"], values["flavio"]
    if min(lula, flavio) < 0 or lula + flavio > 101 or lula + flavio <= 0:
        raise ValueError(f"Placar inválido: {poll['id']}")
    return 100 * (lula - flavio) / (lula + flavio)


def deduplicate(polls, reference):
    """Última revisão divulgada por instituto e período, inclusive fora da renda."""
    result = {}
    for poll in sorted(polls, key=lambda p: (p["divulgacao"], p["id"])):
        if poll["divulgacao"] > reference or poll["campo"]["fim"] > reference:
            continue
        if valid_gap(poll) is None:
            continue
        key = (poll["instituto"], poll["campo"]["inicio"], poll["campo"]["fim"])
        result[key] = poll
    return list(result.values())


def compare(polls, reference, *, days=45, radius=7, min_peers=3):
    """Uma onda por outro instituto; datas centrais ±7d; resumo mediano em 45d."""
    cutoff = date.fromisoformat(reference).toordinal() - days
    # Older observations can be peers at the left edge of the reporting window.
    eligible = deduplicate(polls, reference)
    grouped = {}
    for poll in eligible:
        center = midpoint(poll)
        if center < cutoff:
            continue
        peers = {}
        for other in eligible:
            if other["instituto"] == poll["instituto"]:
                continue
            distance = abs(midpoint(other) - center)
            if distance > radius:
                continue
            # For an equal distance, use the more recent field period, then ID.
            rank = (distance, -midpoint(other), other["id"])
            current = peers.get(other["instituto"])
            if current is None or rank < current[0]:
                peers[other["instituto"]] = (rank, other)
        if len(peers) < min_peers:
            continue
        comparators = [item[1] for item in peers.values()]
        baseline = median(valid_gap(p) for p in comparators)
        gap = valid_gap(poll)
        grouped.setdefault(poll["instituto"], []).append(
            {
                "id": poll["id"],
                "campo": poll["campo"],
                "publicado": poll["publicado"]["2t"],
                "diferenca_validos": gap,
                "mediana_outros": baseline,
                "desvio": gap - baseline,
                "pares": [
                    {
                        "id": p["id"],
                        "instituto": p["instituto"],
                        "distancia_dias": abs(midpoint(p) - center),
                        "diferenca_validos": valid_gap(p),
                    }
                    for p in sorted(comparators, key=lambda p: p["instituto"])
                ],
            }
        )
    result = {}
    for name in sorted({p["instituto"] for p in eligible}):
        waves = sorted(grouped.get(name, []), key=lambda p: p["campo"]["fim"])
        deltas = [p["desvio"] for p in waves]
        signal = median(deltas) if deltas else None
        direction = (
            (
                "Mais Lula"
                if signal > 2
                else "Mais Flávio" if signal < -2 else "Próximo da mediana"
            )
            if signal is not None
            else "Sem comparação"
        )
        result[name] = {
            "desvio_mediano": signal,
            "n_ondas": len(waves),
            "direcao": direction,
            "evidencia": "poucas ondas" if len(waves) < 3 else "exploratório",
            "minimo": min(deltas) if deltas else None,
            "maximo": max(deltas) if deltas else None,
            "ondas": waves,
        }
    return result
