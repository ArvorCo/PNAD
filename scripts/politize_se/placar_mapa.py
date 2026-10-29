"""Contagens exatas para anéis e agrupamentos; nunca somar percentuais arredondados."""

import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORIGEM = ROOT / "docs/assets/politize_se/dados"
DESTINO = ROOT / "docs/assets/politize_se_mapa/placares"


def par(local):
    """Mesma proteção de tamanho e cobertura já aplicada no mapa."""
    if not local.get("n_bu2") or local.get("fatia_f2") is None:
        return [None, None]
    if (local.get("aptos2") or local.get("aptos1") or 0) < 30:
        return [None, None]
    votos = [local.get("flavio2"), local.get("lula2")]
    return votos if all(isinstance(v, int) and v >= 0 for v in votos) else [None, None]


def publicar(ufs=None, origem=ORIGEM, destino=DESTINO):
    destino.mkdir(parents=True, exist_ok=True)
    total = 0
    for pasta in sorted((origem / "mun").iterdir()):
        if not pasta.is_dir() or (ufs and pasta.name not in ufs):
            continue
        locais = {}
        for path in sorted(pasta.glob("*.json")):
            d = json.loads(path.read_text())["locais"]
            for r in d["linhas"]:
                local = dict(zip(d["colunas"], r, strict=True))
                locais[local["local_id"]] = par(local)
        payload = {"formato": 1, "uf": pasta.name, "colunas": ["flavio2", "lula2"], "locais": locais}
        raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
        (destino / f"{pasta.name}.json.gz").write_bytes(gzip.compress(raw, mtime=0))
        total += len(locais)
    return total


if __name__ == "__main__":
    print(f"{publicar()} placares por local publicados")
