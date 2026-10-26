#!/usr/bin/env python3
"""Capturas de tela do vídeo masterclass (video/masterclass).

Serve `docs/` em localhost, abre cada página com Playwright (Chromium sem janela), executa a
tomada descrita em `video/masterclass/capturas/roteiro.json` e grava:

- o vídeo cru em `capturas/bruto/<id>_<fmt>.webm` (ignorado pelo git);
- o vídeo normalizado em `public/midia/cap_<id>_<fmt>.mp4` (h264, 30 fps, sem áudio);
- os quadros parados em `public/midia/cap_<id>_<nome>_<fmt>.png`, no tamanho exato do formato;
- `src/dados/capturas.json`, com a duração de cada gravação e o segundo de cada quadro parado.

Formatos: 16x9 = janela 1920×1080, escala 1; 9x16 = janela 540×960, escala 2 real do
Chromium (layout móvel da página, gravado em 1080×1920).

O cursor é desenhado por um elemento injetado na página: seta no 16x9 (some depois de 1,2 s
parado, para o quadro parado sair limpo) e marca de toque no 9x16 (aparece só no toque).

Totalização: a câmera é falsa. O Chromium recebe um MJPEG com os QR codes dos exemplos oficiais
do TSE (`totalizacao/tests/fixtures/exemplos_tse_2026.json`), e a foto da galeria vem dos mesmos
QR em PNG. Nenhuma tomada clica em Enviar: o clique e a tecla são recusados se o alvo for
`#btn-enviar`, e todo pedido a `supabase.co` é abortado.

Uso:
    python3 scripts/video-masterclass-capturas.py
    python3 scripts/video-masterclass-capturas.py --so mapa_zoom --formato 9x16
    python3 scripts/video-masterclass-capturas.py --sem-video
"""

from __future__ import annotations

import argparse
import contextlib
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import qrcode
from PIL import Image, ImageDraw
from playwright.sync_api import Error as ErroPlaywright
from playwright.sync_api import Page, sync_playwright

RAIZ = Path(__file__).resolve().parents[1]
DOCS = RAIZ / "docs"
MASTER = RAIZ / "video" / "masterclass"
ROTEIRO = MASTER / "capturas" / "roteiro.json"
BRUTO = MASTER / "capturas" / "bruto"
MIDIA = MASTER / "public" / "midia"
SAIDA_JSON = MASTER / "src" / "dados" / "capturas.json"
EXEMPLOS_QR = RAIZ / "totalizacao" / "tests" / "fixtures" / "exemplos_tse_2026.json"

# O 9x16 usa a escala real do Chromium (--force-device-scale-factor) e não a emulada: o
# screencast que grava o vídeo sai em pixels CSS, e com a escala emulada o vídeo ficaria com a
# página em 540×960 num canto do quadro de 1080×1920. Com a escala real ele sai em 1080×1920.
FORMATOS = {
    "16x9": {
        "janela": (1920, 1080),
        "escala": 1,
        "video": (1920, 1080),
        "toque": False,
        "args": [],
    },
    "9x16": {
        "janela": (540, 960),
        "escala": 2,
        "video": (1080, 1920),
        "toque": True,
        "args": ["--force-device-scale-factor=2", "--window-size=540,960"],
    },
}
AGENTE = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
)
# Analytics fora da gravação; supabase.co bloqueado inteiro: nenhuma tomada fala com o backend.
BLOQUEADOS = re.compile(r"googletagmanager\.com|google-analytics\.com|supabase\.co")
PROIBIDO = "#btn-enviar"
PASSOS_MOUSE = 30
ERRO_QUADRO_MAX = 120

CURSOR_JS = r"""
(() => {
  const TOQUE = __TOQUE__;
  const SETA = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="36" height="36">'
    + '<path d="M4 2.5V19.6l4.6-4.2 3 6.6 3.1-1.4-3-6.4H18z" fill="#151812" stroke="#fff" '
    + 'stroke-width="1.6" stroke-linejoin="round"/></svg>';
  const DEDO = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 44 44" width="44" height="44">'
    + '<circle cx="22" cy="22" r="19" fill="rgba(255,255,255,.38)" stroke="rgba(21,24,18,.55)" '
    + 'stroke-width="2.5"/><circle cx="22" cy="22" r="8" fill="rgba(21,24,18,.45)"/></svg>';
  const LADO = TOQUE ? 44 : 36;
  const PONTA = TOQUE ? [22, 22] : [6, 4];
  let el = null;
  let x = -200;
  let y = -200;
  let relogio = null;
  function montar() {
    if (el && el.isConnected) return el;
    el = document.createElement('div');
    el.id = '__cursor';
    el.setAttribute('aria-hidden', 'true');
    if ('popover' in HTMLElement.prototype) el.popover = 'manual';
    el.style.cssText = 'position:fixed;inset:auto;left:0;top:0;margin:0;padding:0;border:0;'
      + 'background:transparent;overflow:visible;width:' + LADO + 'px;height:' + LADO + 'px;'
      + 'z-index:2147483647;pointer-events:none;opacity:0;'
      + 'transition:opacity .28s ease, scale .18s ease;will-change:transform,opacity';
    el.innerHTML = TOQUE ? DEDO : SETA;
    (document.body || document.documentElement).appendChild(el);
    try { if (el.showPopover) el.showPopover(); } catch (e) { /* sem popover: z-index basta */ }
    posicionar();
    return el;
  }
  function topo() {
    if (!el || !el.showPopover || !document.querySelector('dialog:modal')) return;
    try { el.hidePopover(); el.showPopover(); } catch (e) { /* idem */ }
  }
  function posicionar() {
    if (el) el.style.transform = 'translate(' + (x - PONTA[0]) + 'px,' + (y - PONTA[1]) + 'px)';
  }
  function mostrar(ms) {
    montar();
    topo();
    el.style.opacity = '1';
    clearTimeout(relogio);
    if (ms) relogio = setTimeout(() => { el.style.opacity = '0'; }, ms);
  }
  function ocultar() {
    montar();
    clearTimeout(relogio);
    el.style.opacity = '0';
  }
  document.addEventListener('mousemove', (ev) => {
    x = ev.clientX; y = ev.clientY;
    montar();
    posicionar();
    if (!TOQUE) mostrar(1200);
  }, true);
  document.addEventListener('mousedown', (ev) => {
    x = ev.clientX; y = ev.clientY;
    montar();
    posicionar();
    el.style.scale = TOQUE ? '1' : '.86';
    mostrar(0);
  }, true);
  document.addEventListener('mouseup', () => {
    if (!el) return;
    el.style.scale = '1';
    mostrar(TOQUE ? 420 : 1200);
  }, true);
  window.__cursor = {
    ocultar,
    tocar(px, py) { x = px; y = py; montar(); posicionar(); mostrar(TOQUE ? 520 : 1200); },
    visivel() { return Boolean(el) && getComputedStyle(el).opacity !== '0'; },
  };
  document.addEventListener('DOMContentLoaded', montar);
})();
"""

ESTILO_JS = r"""
(() => {
  const css = __CSS__;
  const por = () => {
    const s = document.createElement('style');
    s.id = '__captura_css';
    s.textContent = css;
    document.head.appendChild(s);
  };
  if (document.head) por(); else document.addEventListener('DOMContentLoaded', por);
})();
"""

ROLAR_JS = r"""
async ([cont, alvo, dy, dur, margem]) => {
  const caixa = cont ? document.querySelector(cont) : null;
  if (cont && !caixa) throw new Error('rolar: contêiner ausente ' + cont);
  const sc = caixa || document.scrollingElement || document.documentElement;
  let delta = dy || 0;
  if (alvo) {
    const a = document.querySelector(alvo);
    if (!a) throw new Error('rolar: alvo ausente ' + alvo);
    const base = caixa ? caixa.getBoundingClientRect().top : 0;
    delta = a.getBoundingClientRect().top - base - margem;
  }
  const antes = sc.style.scrollBehavior;
  const raiz = document.documentElement.style.scrollBehavior;
  sc.style.scrollBehavior = 'auto';
  document.documentElement.style.scrollBehavior = 'auto';
  const ini = sc.scrollTop;
  const fim = Math.max(0, Math.min(sc.scrollHeight - sc.clientHeight, ini + delta));
  const t0 = performance.now();
  await new Promise((ok) => {
    if (dur <= 0) { sc.scrollTop = fim; ok(); return; }
    function passo(t) {
      const k = Math.min(1, (t - t0) / (dur * 1000));
      const e = k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
      sc.scrollTop = ini + (fim - ini) * e;
      if (k < 1) requestAnimationFrame(passo); else ok();
    }
    requestAnimationFrame(passo);
  });
  sc.style.scrollBehavior = antes;
  document.documentElement.style.scrollBehavior = raiz;
  return sc.scrollTop;
}
"""

TILES_JS = r"""
() => {
  const t = [...document.querySelectorAll('.leaflet-tile-container img.leaflet-tile')];
  return [t.length, t.filter((i) => i.classList.contains('leaflet-tile-loaded')).length];
}
"""

ZOOM_JS = r"""
([id, nivel, animar]) => {
  const S = window.fiscaisMapa && window.fiscaisMapa.estado;
  if (!S || !S.mapa) throw new Error('mapa ainda não montado');
  let c = S.mapa.getCenter();
  if (id) {
    const l = S.locaisPorId.get(id);
    if (!l) throw new Error('local ausente no recorte: ' + id);
    c = L.latLng(l.lat, l.lon);
  }
  S.mapa.setView(c, nivel, { animate: animar });
  return S.mapa.getZoom();
}
"""

NA_TELA_JS = r"""
(el) => {
  const r = el.getBoundingClientRect();
  return r.width > 0 && r.top >= 0 && r.left >= 0
    && r.bottom <= innerHeight && r.right <= innerWidth;
}
"""

# Rola só o necessário: primeiro o contêiner rolável mais próximo (coluna de filtros, popup,
# painel), e a janela apenas se o elemento continuar fora da tela. scrollIntoView rolaria todos.
TRAZER_JS = r"""
async (el) => {
  const naTela = () => {
    const r = el.getBoundingClientRect();
    return r.top >= 0 && r.left >= 0 && r.bottom <= innerHeight && r.right <= innerWidth;
  };
  const animar = (sc, delta, dur) => new Promise((ok) => {
    const ini = sc.scrollTop;
    const fim = Math.max(0, Math.min(sc.scrollHeight - sc.clientHeight, ini + delta));
    const antes = sc.style.scrollBehavior;
    sc.style.scrollBehavior = 'auto';
    const t0 = performance.now();
    function passo(t) {
      const k = Math.min(1, (t - t0) / (dur * 1000));
      const e = k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
      sc.scrollTop = ini + (fim - ini) * e;
      if (k < 1) requestAnimationFrame(passo); else { sc.style.scrollBehavior = antes; ok(); }
    }
    requestAnimationFrame(passo);
  });
  const raiz = document.scrollingElement || document.documentElement;
  let p = el.parentElement;
  while (p && p !== document.body && p !== document.documentElement) {
    const cs = getComputedStyle(p);
    if (/(auto|scroll)/.test(cs.overflowY) && p.scrollHeight > p.clientHeight + 1) break;
    p = p.parentElement;
  }
  if (p && p !== document.body && p !== document.documentElement) {
    const rp = p.getBoundingClientRect();
    const r = el.getBoundingClientRect();
    await animar(p, r.top + r.height / 2 - (rp.top + rp.height / 2), 0.7);
    if (naTela()) return 'conteiner';
  }
  const r = el.getBoundingClientRect();
  document.documentElement.style.scrollBehavior = 'auto';
  await animar(raiz, r.top + r.height / 2 - innerHeight / 2, 0.8);
  return 'janela';
}
"""

PROIBIDO_JS = (
    "([x, y, sel]) => {"
    "  const ruim = (n) => Boolean(n && n.closest && n.closest('__P__'));"
    "  return ruim(document.elementFromPoint(x, y)) || ruim(sel ? document.querySelector(sel) : null);"
    "}"
).replace("__P__", PROIBIDO)


PRETO_JS = (
    "() => { for (const n of [document.documentElement, document.body]) "
    "if (n) n.style.background = '#000'; }"
)


class TomadaFalhou(RuntimeError):
    """Passo obrigatório que não deu certo."""


@dataclass
class Sessao:
    """Estado de uma gravação: página, formato, relógio e quadros parados."""

    pagina: Page
    tomada: str
    formato: str
    t0: float
    qr: list[Path]
    mouse: list[float]
    stills: dict[str, float] = field(default_factory=dict)
    avisos: list[str] = field(default_factory=list)

    @property
    def agora(self) -> float:
        return time.monotonic() - self.t0


# ------------------------------------------------------------------ servidor local


def url_responde(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=2) as r:
            return r.status == 200
    except OSError:
        return False


@contextlib.contextmanager
def servidor(porta: int, manter: bool):
    base = f"http://localhost:{porta}/"
    if url_responde(base + "fiscais_mapa.html"):
        print(f"Servidor já ativo em {base}; reaproveitado.")
        yield base
        return
    proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(porta), "--directory", str(DOCS)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(50):
            if url_responde(base + "fiscais_mapa.html"):
                break
            time.sleep(0.2)
        else:
            raise SystemExit(f"O servidor local não respondeu em {base}.")
        yield base
    finally:
        if manter:
            print(f"Servidor mantido em {base} (pid {proc.pid}).")
        else:
            proc.terminate()
            proc.wait(timeout=10)


# ------------------------------------------------------------------ QR codes


def gerar_qr(config: dict) -> tuple[list[Path], Path]:
    """PNG de cada QR do exemplo oficial escolhido e o MJPEG da câmera falsa."""
    exemplos = json.loads(EXEMPLOS_QR.read_text(encoding="utf-8"))["exemplos"]
    ex = exemplos[config.get("exemplo", 6)]
    textos = [t for parte in config.get("partes", ["qrbu", "qrce"]) for t in ex[parte]]
    lado = int(config.get("lado_px", 600))
    pasta = BRUTO / "qr"
    pasta.mkdir(parents=True, exist_ok=True)
    pngs, quadros = [], []
    for i, texto in enumerate(textos):
        q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=4)
        q.add_data(texto)
        q.make(fit=True)
        q.box_size = max(1, -(-lado // (q.modules_count + 8)))
        img = q.make_image(fill_color="black", back_color="white").convert("RGB")
        destino = pasta / f"qr_{i + 1}.png"
        img.save(destino)
        pngs.append(destino)
        quadro = pasta / f"camera_{i + 1}.png"
        quadro_camera(img, i).save(quadro)
        quadros.append(quadro)
    vazio = pasta / "camera_vazio.png"
    quadro_camera(None, 0).save(vazio)
    lista = []
    for q in quadros:
        lista += [
            f"file '{q.name}'",
            "duration 2.6",
            f"file '{vazio.name}'",
            "duration 0.7",
        ]
    lista.append(f"file '{vazio.name}'")
    (pasta / "camera.txt").write_text("\n".join(lista) + "\n", encoding="utf-8")
    mjpeg = pasta / "camera.mjpeg"
    ffmpeg(
        [
            *("-f", "concat", "-safe", "0", "-i", str(pasta / "camera.txt")),
            *("-vf", "fps=20,format=yuvj420p", "-q:v", "3", "-f", "mjpeg", str(mjpeg)),
        ]
    )
    return pngs, mjpeg


def quadro_camera(qr: Image.Image | None, semente: int) -> Image.Image:
    """Quadro 720×1280 (celular em pé) da câmera falsa: mesa, papel térmico, linhas e o QR."""
    fundo = Image.new("RGB", (720, 1280), (54, 52, 47))
    d = ImageDraw.Draw(fundo)
    d.rectangle((120, 0, 600, 1280), fill=(244, 242, 234))
    for k, y in enumerate(range(150, 330, 22)):
        larg = 380 - ((k + semente) % 3) * 70
        d.rectangle((160, y, 160 + larg, y + 9), fill=(196, 193, 183))
    for k, y in enumerate(range(830, 1010, 22)):
        larg = 330 - ((k + semente) % 2) * 90
        d.rectangle((160, y, 160 + larg, y + 9), fill=(196, 193, 183))
    if qr is not None:
        fundo.paste(qr.resize((420, 420), Image.NEAREST), (150, 370))
    return fundo


# ------------------------------------------------------------------ vídeo


def ffmpeg(args: list[str]) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def sondar(caminho: Path) -> dict:
    saida = subprocess.run(
        [
            *("ffprobe", "-v", "error", "-select_streams", "v:0"),
            *(
                "-show_entries",
                "stream=width,height:format=duration",
                "-of",
                "json",
                str(caminho),
            ),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    j = json.loads(saida.stdout)
    s = j["streams"][0]
    return {
        "largura": s["width"],
        "altura": s["height"],
        "segundos": float(j["format"]["duration"]),
    }


def primeiro_quadro_preto(video: Path, segundos: float = 8.0) -> float | None:
    """Segundo do primeiro quadro quase preto (o marcador de sincronia da tomada)."""
    taxa, lado = 30, 16 * 9
    bruto = subprocess.run(
        [
            *("ffmpeg", "-v", "error", "-t", str(segundos), "-i", str(video)),
            *("-vf", f"fps={taxa},scale=16:9,format=gray", "-f", "rawvideo", "-"),
        ],
        capture_output=True,
        check=True,
    ).stdout
    for i in range(len(bruto) // lado):
        quadro = bruto[i * lado : (i + 1) * lado]
        if sum(quadro) / lado < 16:
            return i / taxa
    return None


def normalizar(webm: Path, mp4: Path, tamanho: tuple[int, int]) -> None:
    largura, altura = tamanho
    ffmpeg(
        [
            *("-i", str(webm), "-vf", f"scale={largura}:{altura}:flags=lanczos,fps=30"),
            *(
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
            ),
            *("-movflags", "+faststart", "-an", str(mp4)),
        ]
    )


# ------------------------------------------------------------------ passos


def seletor_do(passo: dict) -> str:
    sel = passo.get("sel")
    if not sel:
        raise TomadaFalhou(f"passo sem seletor: {passo}")
    return sel


def esperar_sel(
    s: Sessao, sel: str, segundos: float = 30, estado: str = "visible"
) -> None:
    s.pagina.locator(sel).first.wait_for(state=estado, timeout=segundos * 1000)


def esperar_estavel(s: Sessao, sel: str) -> None:
    """Espera a caixa do elemento parar de mexer (rolagem suave, animação de entrada)."""
    loc = s.pagina.locator(sel).first
    anterior = None
    for _ in range(30):
        caixa = loc.bounding_box()
        atual = None if caixa is None else tuple(round(v) for v in caixa.values())
        if atual is not None and atual == anterior:
            return
        anterior = atual
        s.pagina.wait_for_timeout(100)


def trazer_para_tela(s: Sessao, sel: str) -> None:
    loc = s.pagina.locator(sel).first
    loc.wait_for(state="visible", timeout=30000)
    if not loc.evaluate(NA_TELA_JS):
        loc.evaluate(TRAZER_JS)
    esperar_estavel(s, sel)


def mover(s: Sessao, x: float, y: float, passos: int = PASSOS_MOUSE) -> None:
    s.pagina.mouse.move(x, y, steps=max(1, passos))
    s.mouse[:] = [x, y]


def centro_de(s: Sessao, sel: str, passo: dict) -> tuple[float, float]:
    trazer_para_tela(s, sel)
    caixa = s.pagina.locator(sel).first.bounding_box()
    if caixa is None:
        raise TomadaFalhou(f"sem caixa para {sel}")
    fx, fy = passo.get("ponto", [0.5, 0.5])
    return caixa["x"] + caixa["width"] * fx, caixa["y"] + caixa["height"] * fy


def recusar_proibido(s: Sessao, x: float, y: float, sel: str | None) -> None:
    if (sel and PROIBIDO in sel) or s.pagina.evaluate(PROIBIDO_JS, [x, y, sel]):
        raise TomadaFalhou("recusado: o alvo é o botão Enviar da totalização")


def clicar(s: Sessao, passo: dict) -> None:
    sel = seletor_do(passo)
    x, y = centro_de(s, sel, passo)
    recusar_proibido(s, x, y, sel)
    mover(s, x, y, passo.get("passos", PASSOS_MOUSE))
    s.pagina.wait_for_timeout(140)
    s.pagina.mouse.click(x, y, delay=90)


def digitar(s: Sessao, passo: dict) -> None:
    sel = seletor_do(passo)
    clicar(s, passo)
    if passo.get("limpar", True):
        s.pagina.locator(sel).first.fill("")
    s.pagina.keyboard.type(str(passo["texto"]), delay=passo.get("atraso_ms", 60))


def selecionar(s: Sessao, passo: dict) -> None:
    sel = seletor_do(passo)
    x, y = centro_de(s, sel, passo)
    mover(s, x, y, passo.get("passos", PASSOS_MOUSE))
    s.pagina.evaluate(
        "([x, y]) => window.__cursor && window.__cursor.tocar(x, y)", [x, y]
    )
    s.pagina.wait_for_timeout(250)
    s.pagina.locator(sel).first.select_option(str(passo["valor"]))


def rolar(s: Sessao, passo: dict) -> None:
    s.pagina.evaluate(
        ROLAR_JS,
        [
            passo.get("sel"),
            passo.get("ate"),
            passo.get("dy", 0),
            float(passo.get("duracao", 1.2)),
            passo.get("margem", 16),
        ],
    )


def esperar_tiles(s: Sessao, segundos: float = 15) -> None:
    """Todos os ladrilhos do Leaflet carregados e a contagem parada por três leituras."""
    fim = time.monotonic() + segundos
    estaveis, anterior = 0, None
    while time.monotonic() < fim:
        total, prontos = s.pagina.evaluate(TILES_JS)
        if total and total == prontos and (total, prontos) == anterior:
            estaveis += 1
            if estaveis >= 3:
                return
        else:
            estaveis = 0
        anterior = (total, prontos)
        s.pagina.wait_for_timeout(250)
    s.avisos.append(f"ladrilhos incompletos em {s.agora:.1f} s ({anterior})")


def zoom_mapa(s: Sessao, passo: dict) -> None:
    s.pagina.evaluate(
        ZOOM_JS, [passo.get("local"), passo["nivel"], passo.get("animar", True)]
    )
    s.pagina.wait_for_timeout(450)
    esperar_tiles(s, passo.get("tempo", 15))


def arquivos(s: Sessao, passo: dict) -> None:
    escolha = passo.get("qr", "todos")
    indices = range(len(s.qr)) if escolha == "todos" else [int(i) for i in escolha]
    caminhos = [str(s.qr[i]) for i in indices]
    botao = passo.get("botao")
    if not botao:
        s.pagina.locator(seletor_do(passo)).first.set_input_files(caminhos)
        return
    x, y = centro_de(s, botao, passo)
    recusar_proibido(s, x, y, botao)
    mover(s, x, y, passo.get("passos", PASSOS_MOUSE))
    s.pagina.wait_for_timeout(140)
    with s.pagina.expect_file_chooser() as pedido:
        s.pagina.mouse.click(x, y, delay=90)
    pedido.value.set_files(caminhos)


def tecla(s: Sessao, passo: dict) -> None:
    foco = s.pagina.evaluate(
        "() => document.activeElement && document.activeElement.id"
    )
    if f"#{foco}" == PROIBIDO:
        raise TomadaFalhou("recusado: o foco está no botão Enviar da totalização")
    s.pagina.keyboard.press(passo["tecla"])


def still(s: Sessao, passo: dict, fmt: str, saida: Path) -> None:
    if not passo.get("cursor", False) and s.pagina.evaluate(
        "() => Boolean(window.__cursor && window.__cursor.visivel())"
    ):
        s.pagina.evaluate("() => window.__cursor.ocultar()")
        s.pagina.wait_for_timeout(320)
    s.pagina.evaluate("() => document.fonts && document.fonts.ready")
    nome = passo["nome"]
    s.stills[nome] = round(s.agora, 2)
    s.pagina.screenshot(path=str(saida / f"cap_{s.tomada}_{nome}_{fmt}.png"))


def executar(s: Sessao, passo: dict, fmt: str, saida: Path, base: str) -> None:
    acao = passo["acao"]
    pag = s.pagina
    if acao == "ir":
        if "hash" in passo:
            pag.evaluate("h => { location.hash = h; }", passo["hash"])
        else:
            pag.goto(base + passo["url"], wait_until="load", timeout=120000)
    elif acao == "clicar":
        clicar(s, passo)
    elif acao == "digitar":
        digitar(s, passo)
    elif acao == "selecionar":
        selecionar(s, passo)
    elif acao == "esperar_sel":
        esperar_sel(
            s, seletor_do(passo), passo.get("tempo", 30), passo.get("estado", "visible")
        )
    elif acao == "esperar_js":
        pag.wait_for_function(
            passo["js"], timeout=passo.get("tempo", 30) * 1000, polling=200
        )
    elif acao == "pausa":
        pag.wait_for_timeout(float(passo["s"]) * 1000)
    elif acao == "still":
        still(s, passo, fmt, saida)
    elif acao == "mover":
        if "sel" in passo:
            x, y = centro_de(s, passo["sel"], passo)
        else:
            largura, altura = FORMATOS[fmt]["janela"]
            x, y = passo["x"] * largura, passo["y"] * altura
        mover(s, x, y, passo.get("passos", PASSOS_MOUSE))
    elif acao == "rolar":
        rolar(s, passo)
    elif acao == "arquivos":
        arquivos(s, passo)
    elif acao == "zoom_mapa":
        zoom_mapa(s, passo)
    elif acao == "tiles":
        esperar_tiles(s, passo.get("tempo", 15))
    elif acao == "tecla":
        tecla(s, passo)
    elif acao == "js":
        pag.evaluate(passo["js"])
    else:
        raise TomadaFalhou(f"ação desconhecida: {acao}")


def condicao_ok(s: Sessao, passo: dict) -> bool:
    if "se_presente" in passo and s.pagina.locator(passo["se_presente"]).count() == 0:
        return False
    return not (
        "se_ausente" in passo and s.pagina.locator(passo["se_ausente"]).count() > 0
    )


# ------------------------------------------------------------------ tomada


def opcoes_contexto(tomada: dict, fmt: str, gravar: bool) -> dict:
    f = FORMATOS[fmt]
    largura, altura = f["janela"]
    opcoes = {
        "has_touch": f["toque"],
        "user_agent": AGENTE,
        "locale": "pt-BR",
        "timezone_id": "America/Sao_Paulo",
        "service_workers": "block",
        "permissions": tomada.get("permissoes", []),
    }
    if f["args"]:
        opcoes["no_viewport"] = True
    else:
        opcoes["viewport"] = {"width": largura, "height": altura}
        opcoes["device_scale_factor"] = f["escala"]
    if tomada.get("reduzir_movimento"):
        opcoes["reduced_motion"] = "reduce"
    if gravar:
        BRUTO.mkdir(parents=True, exist_ok=True)
        vl, va = f["video"]
        opcoes["record_video_dir"] = str(BRUTO / "_temp")
        opcoes["record_video_size"] = {"width": vl, "height": va}
    return opcoes


def anotar_console(erros: list[str], tipo: str, texto: str) -> None:
    # "Failed to load resource" repete os pedidos bloqueados; as falhas reais vêm do requestfailed.
    if tipo == "error" and not texto.startswith("Failed to load resource"):
        erros.append(f"console: {texto[:160]}")


def anotar_falha(erros: list[str], url: str, motivo: str | None) -> None:
    # Pedidos bloqueados de propósito e ladrilhos que o Leaflet cancela ao mudar o zoom ficam fora.
    if BLOQUEADOS.search(url) or (motivo or "").endswith("ERR_ABORTED"):
        return
    erros.append(f"rede: {motivo} {url[:120]}")


def gravar_tomada(
    pw, tomada: dict, fmt: str, base: str, qr: tuple, gravar: bool
) -> dict:
    pngs, mjpeg = qr
    args = FORMATOS[fmt]["args"] + [
        a.replace("{camera}", str(mjpeg)) for a in tomada.get("args_navegador", [])
    ]
    navegador = pw.chromium.launch(args=args)
    ctx = navegador.new_context(**opcoes_contexto(tomada, fmt, gravar))
    ctx.route(BLOQUEADOS, lambda rota: rota.abort())
    ctx.add_init_script(
        CURSOR_JS.replace("__TOQUE__", "true" if FORMATOS[fmt]["toque"] else "false")
    )
    if tomada.get("css"):
        ctx.add_init_script(ESTILO_JS.replace("__CSS__", json.dumps(tomada["css"])))
    if tomada.get("init_js"):
        ctx.add_init_script(tomada["init_js"])
    erros: list[str] = []
    pag = ctx.new_page()
    largura, altura = FORMATOS[fmt]["janela"]
    s = Sessao(
        pag, tomada["id"], fmt, time.monotonic(), pngs, [largura * 0.62, altura * 0.58]
    )
    pag.on("pageerror", lambda e: erros.append(f"pageerror: {e}"))
    pag.on("console", lambda m: anotar_console(erros, m.type, m.text))
    pag.on("requestfailed", lambda req: anotar_falha(erros, req.url, req.failure))
    # Quadro preto de sincronia: o primeiro quadro escuro do vídeo marca este instante do
    # relógio da tomada, e a diferença corrige o segundo de cada quadro parado.
    pag.evaluate(PRETO_JS)
    t_preto = s.agora
    pag.wait_for_timeout(500)
    falha = None
    try:
        pag.goto(base + tomada["pagina"], wait_until="load", timeout=120000)
        pag.evaluate("() => document.fonts && document.fonts.ready")
        pag.mouse.move(*s.mouse)
        for passo in tomada["passos"]:
            if fmt not in passo.get("formatos", [fmt]) or not condicao_ok(s, passo):
                continue
            try:
                executar(s, passo, fmt, MIDIA, base)
            except (ErroPlaywright, TomadaFalhou) as e:
                msg = f"{passo['acao']} {passo.get('sel') or passo.get('nome') or ''}: {e}"
                if not passo.get("opcional"):
                    raise TomadaFalhou(msg) from e
                s.avisos.append("opcional falhou: " + msg.splitlines()[0][:200])
    except (ErroPlaywright, TomadaFalhou) as e:
        falha = str(e).splitlines()[0][:300]
    duracao = s.agora
    video = pag.video if gravar else None
    ctx.close()
    bruto = None
    if video is not None:
        bruto = BRUTO / f"{tomada['id']}_{fmt}.webm"
        shutil.move(video.path(), bruto)
    navegador.close()
    return {
        "stills": s.stills,
        "duracao": duracao,
        "t_preto": t_preto,
        "bruto": bruto,
        "avisos": s.avisos,
        "erros": sorted(set(erros))[:12],
        "falha": falha,
    }


def localizar_quadro(
    mp4: Path, png: Path, fmt: str, segundo: float
) -> tuple[float, float]:
    """Segundo do vídeo em que a tela mostra o quadro parado, perto do relógio da tomada.

    Sob carga (câmera, zxing, codificação em tempo real) o compositor do Chromium atrasa e o
    vídeo pode mostrar o estado novo até 2 s depois do relógio. Compara o quadro parado com os
    quadros do vídeo entre 0,6 s antes e 3 s depois: se o relógio já cai num quadro igual, fica
    ele; senão vale o primeiro quadro igual. Devolve também o erro mínimo, que confere o vídeo.
    """
    largura, altura = (160, 90) if fmt == "16x9" else (90, 160)
    taxa, ini = 20, max(0.0, segundo - 0.6)
    with Image.open(png) as im:
        ref = np.asarray(
            im.convert("L").resize((largura, altura), Image.BILINEAR), float
        )
    bruto = subprocess.run(
        [
            *(
                "ffmpeg",
                "-v",
                "error",
                "-ss",
                f"{ini:.2f}",
                "-t",
                "3.6",
                "-i",
                str(mp4),
            ),
            *("-vf", f"fps={taxa},scale={largura}:{altura}:flags=bilinear,format=gray"),
            *("-f", "rawvideo", "-"),
        ],
        capture_output=True,
        check=True,
    ).stdout
    quadros = np.frombuffer(bruto, np.uint8).reshape(-1, altura, largura).astype(float)
    if not len(quadros):
        return segundo, float("inf")
    erro = ((quadros - ref) ** 2).mean(axis=(1, 2))
    iguais = ini + np.flatnonzero(erro <= erro.min() * 1.5 + 4) / taxa
    perto = np.abs(iguais - segundo).min() <= 1 / taxa
    return (segundo if perto else float(iguais[0])), float(erro.min())


def finalizar_video(tomada: dict, fmt: str, r: dict) -> dict | None:
    """Converte o webm, acerta o relógio dos quadros parados e confere cada um no vídeo."""
    if r["bruto"] is None:
        return None
    mp4 = MIDIA / f"cap_{tomada['id']}_{fmt}.mp4"
    normalizar(r["bruto"], mp4, FORMATOS[fmt]["video"])
    preto = primeiro_quadro_preto(mp4)
    desloc = 0.0 if preto is None else min(3.0, max(-1.0, preto - r["t_preto"]))
    info = sondar(mp4)
    stills, erros = {}, {}
    for nome, bruto in r["stills"].items():
        png = MIDIA / f"cap_{tomada['id']}_{nome}_{fmt}.png"
        segundo, erros[nome] = localizar_quadro(mp4, png, fmt, bruto + desloc)
        stills[nome] = round(min(info["segundos"], segundo), 2)
    return {
        "segundos": round(info["segundos"], 2),
        "stills": stills,
        "atraso": {k: round(stills[k] - r["stills"][k] - desloc, 2) for k in stills},
        "erro_quadro": erros,
        "deslocamento": round(desloc, 2),
        "tamanho": (info["largura"], info["altura"]),
        "mp4": mp4,
    }


def carregar_saida() -> dict:
    if SAIDA_JSON.exists():
        return json.loads(SAIDA_JSON.read_text(encoding="utf-8"))
    return {}


def gravar_saida(dados: dict) -> None:
    SAIDA_JSON.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(dados, ensure_ascii=False, indent=2, sort_keys=True)
    SAIDA_JSON.write_text(texto + "\n", encoding="utf-8")


def entrada_json(
    antiga: dict, fmt: str, final: dict, formatos_tomada: list[str]
) -> dict:
    """Formato do contrato (`formatos`, `segundos`, `stills`) com o detalhe por formato.

    `segundos` e `stills` no topo repetem o 16x9 quando ele existe; cada formato tem relógio
    próprio em `por_formato`, porque a página móvel espera e rola em tempos diferentes.
    """
    por = dict(antiga.get("por_formato", {}))
    por[fmt] = {"segundos": final["segundos"], "stills": final["stills"]}
    principal = por.get("16x9") or por[fmt]
    return {
        "formatos": [f for f in formatos_tomada if f in por],
        "segundos": principal["segundos"],
        "stills": principal["stills"],
        "por_formato": por,
    }


def conferir_png(caminho: Path, fmt: str) -> bool:
    with Image.open(caminho) as im:
        return im.size == FORMATOS[fmt]["video"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--so", action="append", help="id da tomada (repita para várias)")
    ap.add_argument("--formato", choices=sorted(FORMATOS), help="só este formato")
    ap.add_argument("--sem-video", action="store_true", help="só os quadros parados")
    ap.add_argument("--porta", type=int, default=4173)
    ap.add_argument("--manter-servidor", action="store_true")
    a = ap.parse_args()

    roteiro = json.loads(ROTEIRO.read_text(encoding="utf-8"))
    tomadas = [t for t in roteiro["tomadas"] if not a.so or t["id"] in a.so]
    if a.so and len(tomadas) != len(set(a.so)):
        conhecidas = ", ".join(t["id"] for t in roteiro["tomadas"])
        raise SystemExit(f"Tomada desconhecida em --so. Conhecidas: {conhecidas}")
    MIDIA.mkdir(parents=True, exist_ok=True)
    qr = gerar_qr(roteiro.get("qr", {}))
    saida = carregar_saida()
    relatorio = []
    with servidor(a.porta, a.manter_servidor) as base, sync_playwright() as pw:
        for tomada in tomadas:
            formatos = [
                f
                for f in tomada.get("formatos", list(FORMATOS))
                if a.formato in (None, f)
            ]
            for fmt in formatos:
                inicio = time.monotonic()
                r = gravar_tomada(pw, tomada, fmt, base, qr, not a.sem_video)
                final = finalizar_video(tomada, fmt, r)
                if final is not None and not r["falha"]:
                    saida[tomada["id"]] = entrada_json(
                        saida.get(tomada["id"], {}),
                        fmt,
                        final,
                        tomada.get("formatos", list(FORMATOS)),
                    )
                    gravar_saida(saida)
                pngs = {
                    n: conferir_png(MIDIA / f"cap_{tomada['id']}_{n}_{fmt}.png", fmt)
                    for n in r["stills"]
                }
                relatorio.append((tomada["id"], fmt, r, final, pngs))
                estado = "FALHOU" if r["falha"] else "ok"
                dur = f"{final['segundos']:.1f} s" if final else "sem vídeo"
                print(
                    f"[{estado}] {tomada['id']} {fmt}: {dur}, {len(r['stills'])} quadros, {time.monotonic() - inicio:.0f} s de trabalho"
                )
                for linha in ([r["falha"]] if r["falha"] else []) + r["avisos"]:
                    print(f"    {linha}")
    shutil.rmtree(BRUTO / "_temp", ignore_errors=True)
    return imprimir_relatorio(relatorio)


def imprimir_relatorio(relatorio: list) -> int:
    print("\nConferência")
    problemas = 0
    for ident, fmt, r, final, pngs in relatorio:
        if final:
            ok = final["segundos"] > 2 and final["tamanho"] == FORMATOS[fmt]["video"]
            problemas += not ok
            print(
                f"  {'ok ' if ok else 'ERR'} cap_{ident}_{fmt}.mp4 {final['segundos']:.2f} s "
                f"{final['tamanho'][0]}×{final['tamanho'][1]} (deslocamento {final['deslocamento']:+.2f} s)"
            )
            quadros = final["stills"]
        else:
            quadros = r["stills"]
        for nome, segundo in quadros.items():
            ok = pngs.get(nome, False)
            extra = ""
            if final:
                # Erro quadrático médio em tons de cinza, imagem reduzida: o vídeo precisa
                # mostrar o mesmo que o quadro parado em algum instante perto do relógio.
                erro = final["erro_quadro"][nome]
                ok = ok and erro <= ERRO_QUADRO_MAX
                extra = f" (atraso {final['atraso'][nome]:+.2f} s, erro {erro:.0f})"
            problemas += not ok
            print(f"      {'ok ' if ok else 'ERR'} {nome} @ {segundo:.2f} s{extra}")
        problemas += bool(r["falha"])
        for e in r["erros"]:
            print(f"      página: {e}")
    print(f"\n{problemas} problema(s).")
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
