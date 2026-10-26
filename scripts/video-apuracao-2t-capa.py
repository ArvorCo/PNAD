#!/usr/bin/env python3
"""Capas (thumbnails) do vídeo "A noite do 2º turno", 16:9 e 9:16.

Wrapper fino de `scripts/video-sete-riscos-capa.py`: mesmo HTML e mesma marca da casa, apontado
para `video/apuracao_2t`, com o fundo `public/midia/sala_apuracao_still_<fmt>.png` (item de
imagem do manifesto de mídia) e os textos deste vídeo. Fontes em `video/apuracao_2t/capa/`,
saídas em `video/apuracao_2t/out/capa_<fmt>.png`. Uso:

  python3 scripts/video-apuracao-2t-capa.py            # as duas capas
  python3 scripts/video-apuracao-2t-capa.py --so 9x16  # uma só

A duração do chip sai de `npm run verificar` (10:35 na revisão de 26/10/2026, após a regravação de cinco cenas).
"""

from __future__ import annotations

import importlib
import sys

base = importlib.import_module("video-sete-riscos-capa")

VIDEO = base.ROOT / "video" / "apuracao_2t"

base.VIDEO = VIDEO
base.CAPA = VIDEO / "capa"
base.SAIDA = VIDEO / "out"
base.FUNDO = "sala_apuracao_still"
base.NOME_CAPA = "apuração 2t"
base.TITULO = ("A noite do ", "2º turno", "")
base.SUBTITULO = "A projeção, os 114 minutos sem o TSE publicar e os logs de 499 mil urnas: o que a urna registrou e o que falta explicar"
base.KICKER = "DOSSIÊ DA APURAÇÃO · 2º TURNO 2026"
base.CHIPS = ("10:35", "2º turno · 25/10", "brasil.arvor.co")
base.__doc__ = __doc__

if __name__ == "__main__":
    sys.exit(base.main())
