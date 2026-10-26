"""Folha de estilo do dossiê do 2º turno: a do 1º turno mais vídeo, áudio e boletins."""

from __future__ import annotations

from apuracao_2026.pagina_css import CSS as CSS_1T
from apuracao_2026.pagina_css import FONTES, JS, JS_HEAD

EXTRA = """
.video-embed{position:relative;width:100%;aspect-ratio:16/9;background:#10201e;border:1px solid var(--ink);margin:24px 0}
.video-embed iframe{position:absolute;inset:0;width:100%;height:100%;border:0}
.hero .video-embed{margin:30px 0 8px}
.hero-vivo{font:600 13px/1.6 var(--sans);color:var(--muted);margin:0 0 18px}
.boletins{display:grid;gap:22px;margin:30px 0}
.boletim{border:1px solid var(--line);border-top:4px solid var(--ink);padding:18px 22px;background:var(--paper)}
.boletim.falhou{border-top-color:var(--gold)}
.boletim h3{margin:0 0 6px;font:700 20px/1.3 var(--sans)}
.boletim h3 span{font:600 13px var(--mono);color:var(--muted);margin-left:8px}
.boletim p{margin:6px 0;font-size:16px}
.boletim audio{display:block;width:100%;margin:12px 0}
.boletim details{margin:10px 0 0}
.boletim .roteiro{white-space:pre-line;font-size:15.5px;line-height:1.6;max-width:none}
.placar-mini{display:flex;flex-wrap:wrap;gap:6px 18px;font:600 15px/1.5 var(--sans)}
.placar-mini .lula{color:var(--red)}.placar-mini .flavio{color:var(--blue)}
.galeria figcaption{font-size:13.5px}
.frase-noite{font:500 21px/1.55 var(--display);max-width:900px;border-left:4px solid var(--red);padding:4px 0 4px 20px;margin:28px 0}
.cartaz-video{display:block;max-width:100%;height:auto;border:1px solid var(--line)}
@media(max-width:719px){.boletim{padding:14px 14px}.frase-noite{font-size:18px;padding-left:14px}}
"""

CSS = CSS_1T + EXTRA

__all__ = ["CSS", "EXTRA", "FONTES", "JS", "JS_HEAD"]
