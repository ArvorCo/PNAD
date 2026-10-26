"""Capítulo 15 do dossiê do 2º turno: o vídeo da apuração.

O id do YouTube vem de `analysis/apuracao_2t_2026/video.json` (`{"youtube_id": null}`
enquanto o vídeo está em produção). Com id, entra o iframe preguiçoso; sem id, o
aviso e o cartaz `docs/img/apuracao_2t/capa_video.png`, se existir.
"""

from __future__ import annotations

import json
from html import escape

from apuracao_2026.pagina_comum import p

from .pagina_comum import MEMOS, ROOT, Capitulo, Dados, cabeca

ARQUIVO = MEMOS / "video.json"
CARTAZ = ROOT / "docs/img/apuracao_2t/capa_video.png"
DURACAO_ENCERRAMENTO = "3:59"


def config() -> dict:
    if not ARQUIVO.exists():
        return {}
    try:
        return json.loads(ARQUIVO.read_text(encoding="utf-8")) or {}
    except json.JSONDecodeError:
        return {}


def render(d: Dados, cap: Capitulo) -> str:
    from .pagina_view import iframe_youtube

    cfg = config()
    vid = cfg.get("youtube_id")
    h = cabeca(
        cap,
        "Dez minutos<br><em>de uma noite inteira.</em>",
        "O vídeo final resume a apuração em cerca de 10 minutos, com os números deste dossiê.",
    )
    if vid:
        h += iframe_youtube(str(vid), "O vídeo da apuração do 2º turno, Arvor")
        if cfg.get("titulo"):
            h += p(escape(str(cfg["titulo"])))
    else:
        h += '<div class="pendente-bloco">Vídeo em produção. O link entra aqui assim que for publicado.</div>'
        if CARTAZ.exists():
            h += (
                '<figure><img class="cartaz-video" src="img/apuracao_2t/capa_video.png" '
                'alt="Cartaz do vídeo da apuração do 2º turno" loading="lazy">'
                "<figcaption>Cartaz do vídeo em produção.</figcaption></figure>"
            )
    live = cfg.get("live_youtube_id")
    if live:
        h += "<h3>A apuração completa, ao vivo</h3>" + p(
            "A transmissão inteira da noite, do telão às 17h ao fechamento, está gravada no YouTube: "
            "projeção, boletins falados, pausas do TSE e a totalização paralela, como foram ao ar.",
            "verificado",
        )
        h += iframe_youtube(str(live), "A apuração completa do 2º turno ao vivo, Arvor")
    h += "<h3>O vídeo de encerramento da live</h3>" + p(
        f"A live terminou com um vídeo de encerramento de {DURACAO_ENCERRAMENTO}, feito em Remotion com a narração do autor "
        "pelo ElevenLabs v4 e capturas das telas da noite. Ele não é hospedado nesta página.",
        "verificado",
    )
    return h
