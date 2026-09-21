#!/usr/bin/env python3
"""Archive public Palver crosstabs, without login or respondent-level access.

Fetch the two main ballots across all displayed waves and breakdowns, plus
all questions by income and total in the latest wave. Reuses local snapshots.
"""

import argparse
import gzip
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/originals/palver_explorer_20260921"
OUT = ROOT / "analysis/reponderacao/palver_explorer_20260921"
URL = "https://www.palver.com.br/survey/explore"
BALLOTS = ["stimulated_1r_vote_1_h", "lula_flavio"]


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def decode_loader(html):
    """Decode React Router's public, indexed JSON; never execute remote JS."""
    scripts = BeautifulSoup(html, "html.parser").find_all("script")
    chunks = []
    prefix = "window.__reactRouterContext.streamController.enqueue("
    for script in scripts:
        text = script.get_text()
        if text.startswith(prefix):
            chunks.append(json.loads(text[len(prefix) : text.rindex(")")]))
    if not chunks:
        raise ValueError("Public loader data missing")
    values = json.loads("".join(chunks))
    memo = {}

    def decode(index):
        if index in (-1, -5):  # undefined and null in turbo-stream
            return None
        if index < 0:
            raise ValueError(f"Unsupported encoded value: {index}")
        if index in memo:
            return memo[index]
        value = values[index]
        if isinstance(value, dict):
            result = {values[int(k[1:])]: decode(v) for k, v in value.items()}
        elif isinstance(value, list):
            result = [decode(v) for v in value]
        else:
            result = value
        memo[index] = result
        return result

    return decode(0)["loaderData"]["routes/survey.explore"]["explorer"]


def fetch(params, snapshot, refresh=False):
    provenance = snapshot.with_suffix(".source.json")
    if snapshot.exists() and provenance.exists() and not refresh:
        return decode_loader(
            gzip.decompress(snapshot.read_bytes()).decode()
        ), json.loads(provenance.read_text())
    response = requests.get(URL, params=params, timeout=45)
    response.raise_for_status()
    data = decode_loader(response.text)
    source = {
        "url": response.url,
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "html_sha256": hashlib.sha256(response.content).hexdigest(),
        "snapshot": str(snapshot.relative_to(ROOT)),
    }
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    snapshot.write_bytes(gzip.compress(response.content, mtime=0))
    dump(provenance, source)
    return data, source


def collect(job, refresh=False):
    wave, question, breakdown = job
    key = f"{question}--{breakdown or 'total'}"
    params = {"wave": wave, "question": question}
    if breakdown:
        params["breakdown"] = breakdown
    data, source = fetch(params, RAW / wave / f"{key}.html.gz", refresh)
    selected = data["selected"]
    assert selected["waveId"] == wave, selected
    assert selected["questionKey"] == question, selected
    available = selected["breakdownKey"] == breakdown
    # Older waves may not offer a newer breakdown. Never relabel the fallback.
    tables = data["crosstabs"] if available else []
    for table in tables:
        assert table["wave_id"] == wave
        assert table["question_key"] == question
        assert table["breakdown_key"] == breakdown
    path = OUT / wave / f"{key}.json"
    status = "available" if available and tables else "unavailable"
    dump(
        path,
        {"source": source, "status": status, "selected": selected, "tables": tables},
    )
    return {
        "file": str(path.relative_to(OUT)),
        "status": status,
        "tables": len(tables),
        **source,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    data, source = fetch({}, RAW / "catalog.html.gz", args.refresh)
    catalog = {k: data[k] for k in ["waves", "questions", "breakdowns"]}
    dump(OUT / "catalog.json", {"source": source, **catalog})
    waves = [w["id"] for w in catalog["waves"]]
    breakdowns = [None] + [b["key"] for b in catalog["breakdowns"]]
    jobs = {(w, q, b) for w in waves for q in BALLOTS for b in breakdowns}
    latest = data["selected"]["waveId"]
    jobs.update(
        (latest, q["key"], b) for q in catalog["questions"] for b in [None, "inc_std"]
    )
    jobs = sorted(jobs, key=lambda j: tuple(v or "" for v in j))
    results = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        for result in pool.map(lambda job: collect(job, args.refresh), jobs):
            results.append(result)
            if len(results) % 25 == 0:
                print(f"Archived {len(results)}/{len(jobs)} queries", flush=True)
    dump(OUT / "manifest.json", {"queries": results, "latest_wave": latest})
    print(
        f"Saved {len(results)} queries; {sum(r['tables'] for r in results)} tables to {OUT}"
    )


if __name__ == "__main__":
    main()
