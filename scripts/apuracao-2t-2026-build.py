#!/usr/bin/env python3
"""Gera docs/apuracao_2T_2026.html a partir dos JSONs de analysis/apuracao_2t_2026/dados/.

Cada capítulo é um módulo `scripts/apuracao_2t_2026/pagina_cap_<ident>.py` com
`render(d, cap)`. Módulo, arquivo ou chave ausente vira bloco "capítulo em
preparação" com o motivo; rodar de novo quando a peça aparecer preenche o capítulo.
O build falha se o HTML tiver travessão. Nunca edite o HTML gerado.

Uso:
    python3 scripts/apuracao-2t-2026-build.py [--dados PASTA] [--saida ARQUIVO]
"""

from __future__ import annotations

import argparse
from pathlib import Path

from apuracao_2t_2026.pagina_comum import DADOS, ROOT, SLUG, Dados
from apuracao_2t_2026.pagina_view import pagina
from ga_tag import injetar


def construir(
    dados: Path = DADOS, saida: Path | None = None
) -> tuple[Path, dict, dict]:
    d = Dados(pasta=dados)
    html, estado, motivos = pagina(d)
    if "—" in html:
        i = html.index("—")
        raise SystemExit(f"travessão no HTML gerado: …{html[max(0, i - 80) : i + 20]}…")
    saida = saida or ROOT / "docs" / f"{SLUG}.html"
    saida.write_text(injetar(html) + "\n", encoding="utf-8")
    return saida, estado, motivos


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dados", type=Path, default=DADOS)
    ap.add_argument("--saida", type=Path, default=None)
    a = ap.parse_args()
    saida, estado, motivos = construir(a.dados, a.saida)
    prontos = [k for k, v in estado.items() if v]
    pend = [k for k, v in estado.items() if not v]
    nome = saida.relative_to(ROOT) if saida.is_relative_to(ROOT) else saida
    print(f"{nome}: {saida.stat().st_size:,} bytes")
    print(f"capítulos completos ({len(prontos)}): {', '.join(prontos)}")
    print(f"capítulos pendentes ({len(pend)}): {', '.join(pend) or 'nenhum'}")
    for k, m in motivos.items():
        print(f"  {k}: {m}")


if __name__ == "__main__":
    main()
