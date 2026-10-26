"""Capítulo 04 do dossiê do 2º turno: os boletins falados da noite.

Um bloco por boletim de `docs/assets/apuracao_2t/boletins/<HHMM>.{mp3,txt,meta.json}`:
player sem autoplay (`preload="none"`), placar do momento pelo arquivo nacional
(`linha_do_tempo.json`, última versão gerada até a hora do boletim), seções que
entraram desde o boletim anterior e o roteiro em `<details>`.
"""

from __future__ import annotations

import json
import re
from html import escape
from itertools import pairwise
from pathlib import Path

from apuracao_2026.pagina_comum import limites, nota, p

from .pagina_comum import ROOT, Capitulo, Dados, cabeca, inteiro, num
from .pagina_fig_noite import minuto_de, serie

PASTA = ROOT / "docs/assets/apuracao_2t/boletins"
URL_REL = "assets/apuracao_2t/boletins"
NAO_FOI_AO_AR = {
    "2120": "falha ao publicar; o áudio foi gerado e não chegou à transmissão"
}

SIGLAS = {"PNAD", "IBGE", "ADPF", "PSDB", "MDB"}
BITRATES = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320]


def duracao_mp3(caminho: Path) -> float | None:
    """Duração aproximada de um MP3 de taxa constante pelo cabeçalho do primeiro quadro."""
    dados = caminho.read_bytes()
    i = 0
    if dados[:3] == b"ID3":
        tam = (dados[6] << 21) | (dados[7] << 14) | (dados[8] << 7) | dados[9]
        i = 10 + tam
    while i < len(dados) - 4:
        if dados[i] == 0xFF and (dados[i + 1] & 0xE0) == 0xE0:
            versao = (dados[i + 1] >> 3) & 0x3
            idx = (dados[i + 2] >> 4) & 0xF
            if versao == 3 and 0 < idx < 15:
                return (len(dados) - i) * 8 / (BITRATES[idx] * 1000)
            return None
        i += 1
    return None


def boletins() -> list[dict]:
    out = []
    for mp3 in sorted(PASTA.glob("*.mp3")):
        hid = mp3.stem
        if not re.fullmatch(r"\d{4}", hid):
            continue
        meta_p = PASTA / f"{hid}.meta.json"
        txt_p = PASTA / f"{hid}.txt"
        meta = json.loads(meta_p.read_text(encoding="utf-8")) if meta_p.exists() else {}
        out.append(
            {
                "id": hid,
                "hora": meta.get("hora") or f"{hid[:2]}:{hid[2:]}",
                "meta": meta,
                "roteiro": txt_p.read_text(encoding="utf-8") if txt_p.exists() else "",
                "duracao": meta.get("duracao_s") or duracao_mp3(mp3),
                "aproximada": not meta.get("duracao_s"),
                "bytes": mp3.stat().st_size,
            }
        )
    return out


def limpa_roteiro(s: str) -> str:
    """Tira as marcações de interpretação ([slowly], [thoughtful]) e a ênfase em caixa alta."""
    s = re.sub(r"\[[^\]]*\]\s*", "", s)
    s = s.replace("—", ", ")
    s = re.sub(
        r"\b([A-ZÁÉÍÓÚÂÊÔÃÕÇ]{4,})\b",
        lambda m: m.group(1) if m.group(1) in SIGLAS else m.group(1).lower(),
        s,
    )
    return s.strip()


def versao_ate(vs: list[dict], minuto: float) -> dict | None:
    ok = [v for v in vs if v["min"] <= minuto]
    return ok[-1] if ok else None


def minuto_boletim(b: dict) -> float:
    criado = b["meta"].get("criado_em")
    if criado:
        # UTC para Brasília (UTC−3)
        data, _, h = criado.replace("Z", "").partition("T")
        hh, mm, ss = h.split(":")
        m = minuto_de(f"{data} {int(hh):02d}:{mm}:{ss[:2]}")
        return (m or 0) - 180
    return (int(b["id"][:2]) - 17) * 60 + int(b["id"][2:])


def fmt_dur(s: float | None, aprox: bool) -> str:
    if not s:
        return "duração não registrada"
    m, ss = divmod(round(s), 60)
    return f"{'cerca de ' if aprox else ''}{m}:{ss:02d}"


def bloco(b: dict, v: dict | None, ant: dict | None) -> str:
    falha = NAO_FOI_AO_AR.get(b["id"])
    cls = "boletim falhou" if falha else "boletim"
    h = f'<article class="{cls}" id="boletim-{b["id"]}"><h3>{b["hora"]}<span>{fmt_dur(b["duracao"], b["aproximada"])}</span></h3>'
    if falha:
        h += f"<p><b>Não foi ao ar:</b> {escape(falha)}.</p>"
    h += (
        f'<audio controls preload="none" src="{URL_REL}/{b["id"]}.mp3">'
        f'<a href="{URL_REL}/{b["id"]}.mp3">Baixar o áudio de {b["hora"]}</a></audio>'
    )
    if v:
        lote = ""
        if ant is not None:
            lote = f" · +{inteiro(v['st'] - ant['st'])} seções desde o boletim anterior"
        h += (
            '<p class="placar-mini">'
            f'<span class="lula">Lula {num(v["pct_lula"], 2)}%</span>'
            f'<span class="flavio">Flávio {num(v["pct_flavio"], 2)}%</span>'
            f"<span>{num(v['pst'], 2)}% das seções</span></p>"
            f"<p>Arquivo nacional na versão de {v['gerado_brt'][11:19]}{lote}.</p>"
        )
    elif b["meta"].get("resumo"):
        h += f"<p>{escape(b['meta']['resumo'])}</p>"
    motivos = b["meta"].get("motivos_modo")
    if motivos:
        h += f"<p>Motivo do boletim: {escape('; '.join(motivos))}.</p>"
    if b["roteiro"]:
        h += (
            "<details><summary>Roteiro lido</summary>"
            f'<p class="roteiro">{escape(limpa_roteiro(b["roteiro"]))}</p></details>'
        )
    return h + "</article>"


def render(d: Dados, cap: Capitulo) -> str:
    bs = boletins()
    if not bs:
        raise FileNotFoundError(f"{PASTA.relative_to(ROOT)} sem boletins")
    L = d.get("linha_do_tempo.json")
    vs = serie(L) if L else []
    tot = sum(b["duracao"] or 0 for b in bs)
    falhas = [b["hora"] for b in bs if b["id"] in NAO_FOI_AO_AR]
    h = cabeca(
        cap,
        f"{len(bs)} boletins,<br><em>{num(tot / 60, 0)} minutos de voz.</em>",
        f"De {bs[0]['hora']} a {bs[-1]['hora']}, um boletim a cada 10 minutos fora da parada, gerado do banco e lido com a voz do autor.",
    )
    h += nota(
        "verificado",
        "Os boletins foram gerados por inteligência artificial. O roteiro foi escrito por um modelo de linguagem a partir do banco do "
        "coletor e das notícias da hora; a voz é a do Leonardo Dias, clonada no ElevenLabs (modelo v4). Nenhum boletim foi editado "
        "depois de ir ao ar. Os players não tocam sozinhos.",
        "Voz sintética, roteiro automático.",
    )
    if falhas:
        h += p(
            f"O boletim de {', '.join(falhas)} foi gerado e não foi ao ar por falha ao publicar; fica aqui como registro.",
            "verificado",
        )
    for a, b in pairwise(bs):
        ma = int(a["id"][:2]) * 60 + int(a["id"][2:])
        mb = int(b["id"][:2]) * 60 + int(b["id"][2:])
        if mb - ma > 30:
            h += p(
                f"Entre os boletins de {a['hora']} e {b['hora']} houve {mb - ma} minutos sem boletim: o boletim só sai com "
                "versão nova, e o TSE não gerou arquivo durante a parada (capítulo 02).",
                "verificado",
            )
    h += '<div class="boletins">'
    ant = None
    for b in bs:
        v = versao_ate(vs, minuto_boletim(b)) if vs else None
        h += bloco(b, v, ant)
        if v:
            ant = v
    h += "</div>"
    h += limites(
        [
            "O placar de cada bloco é o do arquivo nacional na última versão gerada até a hora em que o boletim foi montado; o áudio pode citar número de outra leitura.",
            "No roteiro publicado, as marcações de interpretação da voz (como [slowly]) foram retiradas e a ênfase em maiúsculas voltou à caixa normal.",
            "Duração com 'cerca de' é estimada pelo tamanho do arquivo.",
        ]
    )
    return h
