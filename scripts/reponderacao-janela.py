"""Janela retrospectiva comum: divulgação em D-6..D, uma onda por instituto."""

from datetime import date, timedelta

WINDOW_DAYS = 7


def select(rows, day, window_days=WINDOW_DAYS):
    if window_days < 1:
        raise ValueError("A janela precisa ter pelo menos um dia")
    start = (day - timedelta(days=window_days - 1)).isoformat()
    end = day.isoformat()
    latest = {}
    for row in rows:
        release = row.get("divulgacao")
        if not release or not start <= release <= end:
            continue
        date.fromisoformat(release)
        institute = row["instituto"]
        rank = (release, row["campo"]["fim"], row.get("id", ""))
        previous = latest.get(institute)
        if previous is None or rank > (
            previous["divulgacao"],
            previous["campo"]["fim"],
            previous.get("id", ""),
        ):
            latest[institute] = row
    return [latest[key] for key in sorted(latest)]


def mean(rows, kind, key, day, window_days=WINDOW_DAYS):
    selected = select(rows, day, window_days)
    if not selected:
        return None
    return round(sum(row[kind][key] for row in selected) / len(selected), 2)


def coverage(rows, days, window_days=WINDOW_DAYS):
    result = []
    for day in days:
        selected = select(rows, date.fromisoformat(day), window_days)
        result.append(
            {
                "data": day,
                "n_institutos": len(selected),
                "ondas": [row["id"] for row in selected],
                "institutos": [row["instituto"] for row in selected],
            }
        )
    return result
