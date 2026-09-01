#!/usr/bin/env python3
"""Embute a base analítica dentro do próprio dossiê.

Sem isto, a página depende de `fetch` para desenhar cada gráfico, e abrir o
arquivo direto do disco, com o esquema `file:`, bloqueia a requisição e derruba
todas as figuras de uma vez, deixando só o texto alternativo. Com os dados
embutidos, o dossiê desenha em qualquer contexto: servidor, disco, arquivo
salvo por um leitor ou cópia enviada por mensagem.

Roda depois dos scripts de auditoria e da camada estratégica, e é idempotente:
substitui apenas o conteúdo entre as tags de dados já presentes no HTML.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs/quaest_globo_140826.html"
PAYLOADS = {
    "dossier-data": ROOT / "docs/assets/quaest_globo_140826_data.json",
    "dossier-strategy": ROOT / "docs/assets/quaest_globo_140826_estrategia.json",
}


def compact(path: Path) -> str:
    payload = json.loads(path.read_text())
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    # `</script>` dentro de JSON encerraria a tag antes da hora.
    return text.replace("<", "\\u003c")


def embed(page: Path) -> dict:
    html = page.read_text()
    sizes = {}
    for element_id, source in PAYLOADS.items():
        if not source.exists():
            raise FileNotFoundError(source)
        body = compact(source)
        pattern = re.compile(
            r'(<script type="application/json" id="%s">).*?(</script>)' % element_id,
            re.S,
        )
        if not pattern.search(html):
            raise ValueError(f"A página não tem a tag de dados {element_id}")
        html = pattern.sub(lambda m: m.group(1) + body + m.group(2), html, count=1)
        sizes[element_id] = len(body)
    page.write_text(html)
    return sizes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--page", type=Path, default=PAGE)
    args = parser.parse_args()
    sizes = embed(args.page)
    print(
        json.dumps(
            {
                "page": str(args.page.relative_to(ROOT)),
                "embedded_bytes": sizes,
                "total_kb": round(sum(sizes.values()) / 1024, 1),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
