#!/usr/bin/env python3
"""Gera docs/apuracao_1o_turno_2026.html a partir dos JSONs de analysis/apuracao_2026/dados/.

Capítulo cujo JSON ainda não existe vira bloco "capítulo em preparação"; rodar de
novo quando o arquivo aparecer preenche o capítulo. Nunca edite o HTML gerado.

Uso:
    python3 scripts/apuracao-2026-build.py [--dados PASTA] [--saida ARQUIVO]
"""

from __future__ import annotations

import argparse
from pathlib import Path

from apuracao_2026.pagina_comum import DADOS, ROOT, SLUG, Dados
from apuracao_2026.pagina_view import pagina


def construir(dados: Path = DADOS, saida: Path | None = None) -> tuple[Path, dict]:
    d = Dados(pasta=dados)
    html, estado = pagina(d)
    if "—" in html:
        raise SystemExit("travessão no HTML gerado")
    saida = saida or ROOT / "docs" / f"{SLUG}.html"
    saida.write_text(html + "\n", encoding="utf-8")
    return saida, estado


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dados", type=Path, default=DADOS)
    ap.add_argument("--saida", type=Path, default=None)
    a = ap.parse_args()
    saida, estado = construir(a.dados, a.saida)
    prontos = [k for k, v in estado.items() if v]
    pend = [k for k, v in estado.items() if not v]
    print(
        f"{saida.relative_to(ROOT) if saida.is_relative_to(ROOT) else saida}: {saida.stat().st_size:,} bytes"
    )
    print(f"capítulos completos ({len(prontos)}): {', '.join(prontos)}")
    print(f"capítulos pendentes ({len(pend)}): {', '.join(pend) or 'nenhum'}")


if __name__ == "__main__":
    main()
