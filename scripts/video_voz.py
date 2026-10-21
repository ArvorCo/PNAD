"""Núcleo de narração, efeitos e música dos vídeos em Remotion, pela API do ElevenLabs.

Cada vídeo (`video/fiscais`, `video/masterclass`) descreve suas pastas num `Projeto` e chama
estas funções pelo próprio script (`video-fiscais-voz.py`, `video-masterclass-voz.py`):

- narração: um bloco `## id` do roteiro por cena, na voz do Leonardo (modelo eleven_v4,
  `previous_text`/`next_text` para a prosódia emendar), pelo endpoint com carimbo de tempo
  por caractere; grava `<voz_dir>/<id>.mp3` e `<voz_dir>/<id>.palavras.json`;
- manifesto: `voz_json` com cena, arquivo, duração (ffprobe), texto sem tags e palavras com
  início e fim, para as legendas e os gatilhos das cenas;
- efeitos curtos (`/v1/sound-generation`) e música (`/v1/music`), só quando o arquivo ainda
  não existe.

Chave e voz vêm de `~/arvor/voicer/.env` e nunca são impressas.
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = Path.home() / "arvor" / "voicer" / ".env"
API = "https://api.elevenlabs.io/v1"

MODELO = "eleven_v4"
AJUSTES = {
    "stability": 0.4,
    "similarity_boost": 0.8,
    "style": 0.3,
    "use_speaker_boost": True,
}
PARALELO = 4
TAG = re.compile(r"\[[a-z ]+\]")
TRAVESSAO = "\u2014"
COMENTARIO = re.compile(r"<!--.*?-->", re.DOTALL)


@dataclass(frozen=True)
class Projeto:
    """Pastas de um vídeo. `raiz` é `video/<nome>`; o resto costuma seguir o padrão."""

    raiz: Path
    roteiro: Path
    voz_dir: Path
    sfx_dir: Path
    musica_dir: Path
    voz_json: Path
    musica_json: Path

    @classmethod
    def padrao(cls, raiz: Path) -> Projeto:
        return cls(
            raiz=raiz,
            roteiro=raiz / "roteiro" / "roteiro.md",
            voz_dir=raiz / "public" / "voz",
            sfx_dir=raiz / "public" / "sfx",
            musica_dir=raiz / "public" / "musica",
            voz_json=raiz / "src" / "dados" / "voz.json",
            musica_json=raiz / "src" / "dados" / "musica.json",
        )


def ambiente() -> tuple[str, str]:
    chave = voz = ""
    for linha in ENV.read_text(encoding="utf-8").splitlines():
        if linha.startswith("ELEVENLABS_API_KEY="):
            chave = linha.split("=", 1)[1].strip().strip('"')
        elif linha.startswith("ELEVENLABS_VOICE_ID="):
            voz = linha.split("=", 1)[1].strip().strip('"')
    if not chave or not voz:
        raise SystemExit(f"ELEVENLABS_API_KEY ou ELEVENLABS_VOICE_ID ausentes em {ENV}")
    return chave, voz


def cenas(texto: str) -> list[tuple[str, str]]:
    """Blocos `## id` do roteiro, na ordem, com o texto a narrar: tags incluídas, comentários
    HTML (`<!-- dado: ... -->`, `<!-- fonte: ... -->`) removidos para não irem à voz."""
    saida: list[tuple[str, str]] = []
    atual: str | None = None
    corpo: list[str] = []

    def fechar() -> None:
        if atual:
            saida.append((atual, COMENTARIO.sub("", "\n".join(corpo)).strip()))

    for linha in texto.splitlines():
        if linha.startswith("## "):
            fechar()
            atual = linha[3:].strip()
            corpo = []
        elif atual is not None:
            corpo.append(linha)
    fechar()
    return saida


def limpar(texto: str) -> str:
    return re.sub(r"\s+", " ", TAG.sub("", texto)).strip()


def pedido(url: str, chave: str, corpo: dict) -> bytes:
    req = urllib.request.Request(
        url,
        data=json.dumps(corpo).encode(),
        headers={"xi-api-key": chave, "Content-Type": "application/json"},
    )
    return urllib.request.urlopen(req, timeout=600).read()


def palavras_do_alinhamento(alinhamento: dict) -> list[dict]:
    """Agrupa caracteres em palavras e descarta as tags entre colchetes."""
    chars = alinhamento["characters"]
    ini = alinhamento["character_start_times_seconds"]
    fim = alinhamento["character_end_times_seconds"]
    palavras: list[dict] = []
    atual = ""
    t0 = 0.0
    t1 = 0.0
    dentro_tag = False
    for c, a, b in zip(chars, ini, fim, strict=True):
        if c == "[":
            dentro_tag = True
        if dentro_tag:
            if c == "]":
                dentro_tag = False
            continue
        if c.isspace():
            if atual:
                palavras.append({"w": atual, "t": round(t0, 3), "f": round(t1, 3)})
                atual = ""
            continue
        if not atual:
            t0 = a
        atual += c
        t1 = b
    if atual:
        palavras.append({"w": atual, "t": round(t0, 3), "f": round(t1, 3)})
    return palavras


def duracao(arquivo: Path) -> float:
    saida = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(arquivo),
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return float(saida.strip())


def gerar_cena(
    projeto: Projeto, chave: str, voz: str, lista: list[tuple[str, str]], i: int
) -> dict:
    cid, texto = lista[i]
    corpo = {
        "text": texto,
        "model_id": MODELO,
        "voice_settings": AJUSTES,
        "previous_text": lista[i - 1][1] if i > 0 else None,
        "next_text": lista[i + 1][1] if i + 1 < len(lista) else None,
    }
    corpo = {k: v for k, v in corpo.items() if v is not None}
    resposta = json.loads(
        pedido(
            f"{API}/text-to-speech/{voz}/with-timestamps?output_format=mp3_44100_128",
            chave,
            corpo,
        )
    )
    destino = projeto.voz_dir / f"{cid}.mp3"
    destino.write_bytes(base64.b64decode(resposta["audio_base64"]))
    palavras = palavras_do_alinhamento(resposta["alignment"])
    (projeto.voz_dir / f"{cid}.palavras.json").write_text(
        json.dumps(palavras, ensure_ascii=False), encoding="utf-8"
    )
    print(f"  voz {cid}: {duracao(destino):.1f} s, {len(palavras)} palavras")
    return {"id": cid}


def ler_roteiro(projeto: Projeto) -> list[tuple[str, str]]:
    if not projeto.roteiro.exists():
        raise SystemExit(f"roteiro ausente: {projeto.roteiro.relative_to(ROOT)}")
    texto = projeto.roteiro.read_text(encoding="utf-8")
    lista = cenas(texto)
    if TRAVESSAO in texto:
        raise SystemExit("roteiro com travessão")
    return lista


def narrar(
    projeto: Projeto,
    chave: str,
    voz: str,
    lista: list[tuple[str, str]],
    so: str | None = None,
    forcar: bool = False,
) -> None:
    """Gera as cenas pendentes: todas com `forcar`, só `so`, ou as que ainda não têm áudio."""
    projeto.voz_dir.mkdir(parents=True, exist_ok=True)
    pendentes = [
        i
        for i, (cid, _) in enumerate(lista)
        if forcar
        or (so and cid == so)
        or (not so and not (projeto.voz_dir / f"{cid}.palavras.json").exists())
    ]
    with ThreadPoolExecutor(max_workers=PARALELO) as ex:
        list(ex.map(lambda i: gerar_cena(projeto, chave, voz, lista, i), pendentes))


def efeitos(
    projeto: Projeto, chave: str, catalogo: dict[str, tuple[str, float]]
) -> None:
    """Efeitos curtos do catálogo `{nome: (prompt, segundos)}` que ainda não existem."""
    projeto.sfx_dir.mkdir(parents=True, exist_ok=True)
    for nome, (prompt, segundos) in catalogo.items():
        destino = projeto.sfx_dir / f"{nome}.mp3"
        if destino.exists():
            continue
        destino.write_bytes(
            pedido(
                f"{API}/sound-generation",
                chave,
                {"text": prompt, "duration_seconds": segundos, "prompt_influence": 0.5},
            )
        )
        print(f"  sfx {nome}: {duracao(destino):.2f} s")


def musica(chave: str, destino: Path, corpo: dict) -> None:
    """Uma faixa de `/v1/music` gravada em `destino` (corpo: prompt, duração e opções)."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(pedido(f"{API}/music", chave, corpo))


def manifesto(projeto: Projeto, lista: list[tuple[str, str]]) -> None:
    cenas_json = []
    for cid, texto in lista:
        mp3 = projeto.voz_dir / f"{cid}.mp3"
        alinhamento = projeto.voz_dir / f"{cid}.palavras.json"
        if not alinhamento.exists():
            print(f"  (sem áudio ainda: {cid})")
            continue
        palavras = json.loads(alinhamento.read_text("utf-8"))
        cenas_json.append(
            {
                "id": cid,
                "arquivo": f"voz/{cid}.mp3",
                "segundos": round(duracao(mp3), 3),
                "texto": limpar(texto),
                "palavras": palavras,
            }
        )
    projeto.voz_json.parent.mkdir(parents=True, exist_ok=True)
    projeto.voz_json.write_text(
        json.dumps({"modelo": MODELO, "cenas": cenas_json}, ensure_ascii=False),
        encoding="utf-8",
    )
    total = sum(c["segundos"] for c in cenas_json)
    print(
        f"{projeto.voz_json.relative_to(ROOT)}: {len(cenas_json)} cenas, "
        f"{total:.0f} s de narração"
    )


def argumentos(descricao: str) -> argparse.ArgumentParser:
    """Opções comuns aos scripts de voz: `--so`, `--forcar`, `--sem-efeitos`."""
    parser = argparse.ArgumentParser(description=descricao)
    parser.add_argument("--so", help="regera só esta cena")
    parser.add_argument("--forcar", action="store_true", help="regera todas as cenas")
    parser.add_argument("--sem-efeitos", action="store_true")
    return parser
