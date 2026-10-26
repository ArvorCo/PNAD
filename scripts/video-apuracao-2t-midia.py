#!/usr/bin/env python3
"""Clipes e stills do vídeo "A noite do 2º turno" (video/apuracao_2t) pelo ``openclaw``.

Wrapper fino de `scripts/video-sete-riscos-midia.py`: importa o módulo, aponta todas as pastas
para `video/apuracao_2t` e troca a lista de cenas válidas pelos ids de `src/ordem.ts`. Gerador,
cache, sondagem, absorção de arquivos feitos à mão, recorte 9:16 e plano B local (mflux) são o
mesmo código. Uso e opções: `python3 scripts/video-apuracao-2t-midia.py --help`.
"""

from __future__ import annotations

import importlib
import re
import sys

base = importlib.import_module("video-sete-riscos-midia")

PROJETO = base.RAIZ / "video" / "apuracao_2t"
MIDIA = PROJETO / "midia"
ORDEM_TS = PROJETO / "src" / "ordem.ts"


def cenas_da_ordem() -> frozenset[str]:
    """Ids de `ORDEM` em `src/ordem.ts`."""
    bloco = ORDEM_TS.read_text(encoding="utf-8").split("export const ORDEM", 1)[-1]
    return frozenset(re.findall(r'\{\s*id:\s*"([^"]+)",\s*capitulo:', bloco))


base.PROJETO = PROJETO
base.MIDIA = MIDIA
base.MANIFESTO = MIDIA / "manifesto.json"
base.CACHE = MIDIA / "cache.json"
base.SONDAGEM = MIDIA / "sondagem.json"
base.ENTRADA = MIDIA / "entrada"
base.BRUTOS = MIDIA / "brutos"
base.PUBLICO = PROJETO / "public" / "midia"
base.SAIDA_DADOS = PROJETO / "src" / "dados" / "midia.json"
base.CENAS_VALIDAS = cenas_da_ordem()
base.__doc__ = __doc__

if __name__ == "__main__":
    sys.exit(base.main())
