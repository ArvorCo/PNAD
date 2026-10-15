"""Mudança descritiva por renda em duas ondas anteriores à urna, com fontes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FOLDER = ROOT / "docs/fontes/quaest_14102026"
MANIFEST = ROOT / "analysis/quaest_141026/historico-fontes.json"
PAGES = [
    (
        "data/pesquisas/quaest/2026-08-14/relatorio.pdf",
        36,
        "julho-voto-p36",
        "Coluna Jul, série reproduzida no relatório de 14/08",
    ),
    (
        "data/pesquisas/quaest/2026-07/Quaest_072026.pdf",
        114,
        "julho-perfil-p114",
        "Perfil de renda de julho",
    ),
    (
        "data/originals/quaest_092026_29/relatorio.pdf",
        37,
        "setembro-voto-p37",
        "Coluna 28 Set, série do relatório de 28/09",
    ),
    (
        "data/originals/quaest_092026_29/relatorio.pdf",
        204,
        "setembro-perfil-p204",
        "Perfil de renda de setembro",
    ),
]


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_sources():
    """Renderiza páginas integrais de PDFs intactos; não cria outro PDF."""
    import fitz

    FOLDER.mkdir(parents=True, exist_ok=True)
    originals, pages = {}, []
    for filename, page, slug, label in PAGES:
        path = ROOT / filename
        if filename not in originals:
            originals[filename] = {
                "arquivo": filename,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        target = FOLDER / (slug + ".png")
        with fitz.open(path) as pdf:
            pdf[page - 1].get_pixmap(matrix=fitz.Matrix(2.4, 2.4)).save(target)
        pages.append(
            {
                "original": filename,
                "pagina_fisica": page,
                "arquivo": str(target.relative_to(ROOT)),
                "rotulo": label,
                "sha256": sha256(target),
            }
        )
    manifest = {
        "conferido_em": "2026-10-15",
        "originais": list(originals.values()),
        "paginas": pages,
        "nota": "Páginas integrais renderizadas; originais preservados, sem edição.",
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return manifest


def build(archived):
    before = next(p for p in archived if p["id"] == "quaest_2026-07-13")
    after = next(p for p in archived if p["id"] == "quaest_2026-09-27")
    weights = before["renda"]["amostra_pct"]
    if weights != after["renda"]["amostra_pct"] or sum(weights) != 100:
        raise ValueError("A decomposição exige a mesma margem publicada nas duas ondas")
    rows = []
    totals = []
    for poll in (before, after):
        cross = poll["cruzamentos"]["2t"]
        aligned = [
            dict(zip(cross["opcoes"], row, strict=True)) for row in cross["linhas"]
        ]
        if len(aligned) != 3 or any(sum(row.values()) != 100 for row in aligned):
            raise ValueError("Tabela histórica incompleta ou fora de 100%")
        rows.append(aligned)
        recomposed = {
            key: sum(w * r[key] for w, r in zip(weights, aligned, strict=True)) / 100
            for key in cross["opcoes"]
        }
        published = poll["publicado"]["2t"]
        gap = published["flavio"] - published["lula"]
        recomposed_gap = recomposed["flavio"] - recomposed["lula"]
        totals.append(
            {
                "id": poll["id"],
                "divulgacao": poll["divulgacao"],
                "publicado": published,
                "recomposto": recomposed,
                "gap_publicado_pp": gap,
                "gap_recomposto_pp": recomposed_gap,
                "residuo_gap_pp": gap - recomposed_gap,
            }
        )
    bands = []
    for index, (label, weight) in enumerate(
        zip(["Até 2 SM", "Mais de 2 a 5 SM", "Mais de 5 SM"], weights, strict=True)
    ):
        first, last = rows[0][index], rows[1][index]
        delta = (last["flavio"] - last["lula"]) - (first["flavio"] - first["lula"])
        bands.append(
            {
                "faixa": label,
                "peso_pct": weight,
                "julho": first,
                "setembro": last,
                "mudanca_gap_na_faixa_pp": delta,
                "contribuicao_gap_pp": weight * delta / 100,
            }
        )
    return {
        "inicio": totals[0],
        "fim": totals[1],
        "faixas": bands,
        "mudanca_gap_publicado_pp": totals[1]["gap_publicado_pp"]
        - totals[0]["gap_publicado_pp"],
        "mudanca_gap_recomposto_pp": sum(row["contribuicao_gap_pp"] for row in bands),
        "mudanca_residuo_pp": totals[1]["residuo_gap_pp"] - totals[0]["residuo_gap_pp"],
        "fontes": json.loads(MANIFEST.read_text()),
        "limite": "Contabilidade de margens publicadas em amostras diferentes, não migração individual, efeito causal da renda ou voto por renda de 14/10. Para em 28/09; em 03/10 o perfil final ainda não havia sido conferido.",
    }
