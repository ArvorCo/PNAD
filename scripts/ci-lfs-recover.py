"""Restore public LFS inputs on CI when the LFS batch endpoint is unavailable."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import urlopen

CHUNK = 1024 * 1024


def matches(path, oid, size):
    if not path.is_file() or path.stat().st_size != size:
        return False
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest() == oid


def fetch(path, oid, size, urls):
    """Only replace the checkout file after receiving the bytes committed in Git."""
    errors = []
    for url in urls:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as output:
            tmp = Path(output.name)
        try:
            with urlopen(url, timeout=60) as response, tmp.open("wb") as handle:
                shutil.copyfileobj(response, handle, CHUNK)
            if not matches(tmp, oid, size):
                raise ValueError("size or SHA-256 differs from the committed pointer")
            tmp.chmod(0o644)
            tmp.replace(path)
            return
        except (URLError, OSError, ValueError) as e:
            errors.append(f"{url}: {e}")
        finally:
            tmp.unlink(missing_ok=True)
    raise RuntimeError(f"Could not restore {path}: " + " | ".join(errors))


def restore(group, revision, repository):
    oid, size, paths = group
    source = next((p for p in paths if matches(p, oid, size)), None)
    if source is None:
        source = paths[0]
        urls = [
            f"https://media.githubusercontent.com/media/{repository}/{revision}/{quote(p.as_posix())}"
            for p in paths
        ]
        if repository.lower() == "arvorco/pnad":
            urls.extend(
                "https://brasil.arvor.co/" + quote(p.relative_to("docs").as_posix())
                for p in paths
                if p.is_relative_to("docs")
            )
        fetch(source, oid, size, urls)
    for path in paths:
        if path != source and not matches(path, oid, size):
            shutil.copyfile(source, path)
            if not matches(path, oid, size):
                raise RuntimeError(f"Local copy verification failed: {path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include", required=True)
    args = parser.parse_args()
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    repository = os.environ["GITHUB_REPOSITORY"]
    inventory = subprocess.check_output(
        ["git", "lfs", "ls-files", "--json", "--include=" + args.include, revision],
        text=True,
    )
    grouped = defaultdict(list)
    for item in json.loads(inventory)["files"]:
        if item["oid_type"] != "sha256":
            raise ValueError(f"Unsupported digest for {item['name']}")
        grouped[item["oid"], item["size"]].append(Path(item["name"]))
    jobs = [(oid, size, paths) for (oid, size), paths in grouped.items()]
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda job: restore(job, revision, repository), jobs))
    print(
        f"Verified {sum(map(len, grouped.values()))} paths against {len(jobs)} LFS objects."
    )


if __name__ == "__main__":
    main()
