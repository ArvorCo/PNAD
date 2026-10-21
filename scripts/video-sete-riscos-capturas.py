#!/usr/bin/env python3
"""Capturas de tela do vídeo Sete riscos, um fiscal (video/sete_riscos).

Reaproveita o motor de `scripts/video-masterclass-capturas.py` (servidor local de `docs/` em
4173, Playwright em Python, gravação webm convertida em mp4 por ffmpeg, cursor desenhado por
JS, analytics e supabase.co bloqueados, recusa de clique em `#btn-enviar`), apontado para a raiz
`video/sete_riscos`. O roteiro fica em `video/sete_riscos/capturas/roteiro.json`.

Quatro tipos de item, todos registrados em `src/dados/capturas.json` com o esquema do contrato
(`formatos`, `segundos`, `stills`), lido por `fonteMidia.ts`, `Still.tsx` e `Gravacao.tsx`:

- reaproveitadas: gravações da masterclass já presentes em `public/midia/` por hard link. O
  script só lê a duração de cada mp4 (ffprobe) e copia os quadros parados do `capturas.json` da
  masterclass. Nada é regravado.
- tomadas: gravações novas (hoje só `mapa_cep`), com `cap_<id>_<fmt>.mp4` e
  `cap_<id>_<nome>_<fmt>.png`, iguais às da masterclass.
- matérias: um quadro parado por caso, `cap_materia_<caso>_<fmt>.png`, da primeira fonte do caso
  em `analysis/apuracao_2026/fontes_fiscais.json` que tem URL. A página é rolada até o título.
  Se o site recusa, tenta o Wayback Machine (`/web/2026/`, depois `/web/2024/`).
- páginas: quadros parados isolados (`fiscaisdopl`, `totalizacao_painel_hoje`), só a primeira
  tela, sem preencher nem clicar em nada.

Quadro parado isolado (matéria ou página) entra assim, sem nome de still, para que
`<Still id="cap_materia_<caso>" />` resolva `midia/cap_materia_<caso>_<fmt>.png`:

    {"formatos": ["16x9", "9x16"], "segundos": 0, "stills": {}, "tipo": "still",
     "origem": "direto" | "archive", "url": "...", "por_formato": {...}}

Quando nada vem, o item fica com `"formatos": []` e `"falhou": "<motivo>"`, sem imagem. Nunca
se monta print. Cada PNG é conferido: tamanho exato do formato e luminância média entre 15 e
240 (nem tela branca nem tela preta); acima de 240 só passa com ao menos 2% de tinta, porque
matéria de texto corrido sobre fundo branco chega a 247 sem estar vazia.

Banner de cookies: o script não aceita consentimento. Clica só em botões de fechar ou recusar e
esconde por CSS o que sobrar (banner, paywall e barras fixas).

Uso:
    python3 scripts/video-sete-riscos-capturas.py
    python3 scripts/video-sete-riscos-capturas.py --so materia_itumbiara_2018
    python3 scripts/video-sete-riscos-capturas.py --registrar-existentes
"""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from playwright.sync_api import Error as ErroPlaywright
from playwright.sync_api import TimeoutError as TempoPlaywright
from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parents[1]
MASTER = RAIZ / "video" / "sete_riscos"
ROTEIRO = MASTER / "capturas" / "roteiro.json"
BRUTO = MASTER / "capturas" / "bruto"
MIDIA = MASTER / "public" / "midia"
SAIDA_JSON = MASTER / "src" / "dados" / "capturas.json"
MASTERCLASS_JSON = RAIZ / "video" / "masterclass" / "src" / "dados" / "capturas.json"
FONTES_FISCAIS = RAIZ / "analysis" / "apuracao_2026" / "fontes_fiscais.json"
MOTOR = RAIZ / "scripts" / "video-masterclass-capturas.py"


def carregar_motor():
    """Importa o motor da masterclass e o aponta para a raiz deste vídeo."""
    spec = importlib.util.spec_from_file_location("masterclass_capturas", MOTOR)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Motor ausente: {MOTOR}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.MASTER = MASTER
    mod.ROTEIRO = ROTEIRO
    mod.BRUTO = BRUTO
    mod.MIDIA = MIDIA
    mod.SAIDA_JSON = SAIDA_JSON
    return mod


mc = carregar_motor()
FORMATOS = mc.FORMATOS
ARQUIVOS_WAYBACK = (
    "https://web.archive.org/web/2026/",
    "https://web.archive.org/web/2024/",
)
TEXTO_MINIMO = 400
LUMA = (15.0, 240.0)
TINTA_MINIMA = 0.02

# Botões que fecham ou recusam. Aceitar consentimento fica de fora de propósito.
FECHAR = re.compile(
    r"^\s*(Fechar|Rejeitar|Rejeitar todos|Recusar|Recusar todos|Não aceito|"
    r"Continuar sem aceitar|Agora não|Entendi|Close|Reject all|Dismiss)\s*[×x]?\s*$",
    re.IGNORECASE,
)
FECHAR_SEL = (
    "[aria-label='close' i], [aria-label='fechar' i], [aria-label='Fechar janela' i], "
    "button.close, .modal-close, [class*='close-button']"
)

LIMPAR_JS = r"""
() => {
  const css = `
    [class*=paywall], [id*=paywall], [class*=cookie], [id*=cookie], [class*=consent],
    [id*=consent], [class*=lgpd], [id*=lgpd], #onetrust-consent-sdk, #didomi-host,
    #wm-ipp-base, #wm-ipp, #wm-ipp-print, #donato, [class*=modal-backdrop],
    [class*=newsletter-modal], iframe[src*=ads], [id^=google_ads], [class*=adsbygoogle],
    [class*=banner-ads], [id*=banner-topo] { display: none !important; }
    html, body { overflow: auto !important; position: static !important; }
    html { scroll-behavior: auto !important; }`;
  const s = document.createElement('style');
  s.id = '__captura_limpa';
  s.textContent = css;
  document.head.appendChild(s);
  const alto = innerHeight;
  for (const el of document.querySelectorAll('body *')) {
    const st = getComputedStyle(el);
    if (st.position !== 'fixed' && st.position !== 'sticky') continue;
    const r = el.getBoundingClientRect();
    const cabeca = r.top <= 4 && r.height < alto * 0.3;
    const pe = r.bottom >= alto - 4 && r.height < alto * 0.4;
    const capa = r.width * r.height > innerWidth * alto * 0.35;
    // Fixo é sempre cabeçalho, anúncio flutuante ou aviso; o texto da matéria nunca é fixo.
    if (st.position === 'fixed' || cabeca || pe || capa) {
      el.style.setProperty('display', 'none', 'important');
    }
  }
}
"""

TITULO_JS = r"""
() => {
  const sels = ['h1', '.titulo', '[class*=title]'];
  for (const sel of sels) {
    for (const el of document.querySelectorAll(sel)) {
      const r = el.getBoundingClientRect();
      const txt = (el.innerText || '').trim();
      if (r.width > 0 && r.height > 0 && txt.length >= 10) {
        const alvo = Math.max(0, r.top + scrollY - innerHeight * 0.16);
        window.scrollTo(0, alvo);
        return sel;
      }
    }
  }
  return null;
}
"""


# ------------------------------------------------------------------ dados


def carregar_saida() -> dict:
    if SAIDA_JSON.exists():
        return json.loads(SAIDA_JSON.read_text(encoding="utf-8"))
    return {}


def gravar_saida(dados: dict) -> None:
    SAIDA_JSON.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(dados, ensure_ascii=False, indent=2, sort_keys=True)
    SAIDA_JSON.write_text(texto + "\n", encoding="utf-8")


def materias_do_acervo(casos: list[str]) -> list[dict]:
    """Primeira fonte de cada caso que tem URL, a mesma escolha do JSON do vídeo."""
    acervo = json.loads(FONTES_FISCAIS.read_text(encoding="utf-8"))
    fontes = {f["id"]: f for f in acervo["fontes"]}
    por_caso = {c["id"]: c for c in acervo["casos"]}
    saida = []
    for caso in casos:
        c = por_caso.get(caso)
        if c is None:
            saida.append({"id": f"materia_{caso}", "caso": caso, "url": None})
            continue
        fonte = next(
            (fontes[f] for f in c["fontes"] if fontes.get(f, {}).get("url")), None
        )
        saida.append(
            {
                "id": f"materia_{caso}",
                "caso": caso,
                "fonte": fonte["id"] if fonte else None,
                "veiculo": fonte.get("veiculo") if fonte else None,
                "url": fonte["url"] if fonte else None,
            }
        )
    return saida


def atualizar_roteiro(roteiro: dict) -> dict:
    roteiro["materias"] = materias_do_acervo(roteiro["casos"])
    texto = json.dumps(roteiro, ensure_ascii=False, indent=2)
    ROTEIRO.write_text(texto + "\n", encoding="utf-8")
    return roteiro


# ------------------------------------------------------------------ reaproveitadas


def registrar_existentes(ids: list[str], saida: dict) -> list[tuple[str, str]]:
    """Registra as gravações da masterclass já ligadas em public/midia, sem regravar."""
    origem = json.loads(MASTERCLASS_JSON.read_text(encoding="utf-8"))
    relatorio = []
    for ident in ids:
        antiga = origem.get(ident)
        if antiga is None:
            relatorio.append((ident, "falhou: sem registro na masterclass"))
            continue
        por, faltas = {}, []
        for fmt in antiga["formatos"]:
            mp4 = MIDIA / f"cap_{ident}_{fmt}.mp4"
            if not mp4.exists():
                faltas.append(mp4.name)
                continue
            stills = antiga.get("por_formato", {}).get(fmt, {}).get("stills")
            stills = dict(stills if stills is not None else antiga["stills"])
            faltas += [
                f"cap_{ident}_{n}_{fmt}.png"
                for n in stills
                if not (MIDIA / f"cap_{ident}_{n}_{fmt}.png").exists()
            ]
            por[fmt] = {
                "segundos": round(mc.sondar(mp4)["segundos"], 2),
                "stills": stills,
            }
        if not por:
            relatorio.append((ident, "falhou: nenhum mp4 em public/midia"))
            continue
        principal = por.get("16x9") or next(iter(por.values()))
        saida[ident] = {
            "formatos": [f for f in antiga["formatos"] if f in por],
            "segundos": principal["segundos"],
            "stills": principal["stills"],
            "por_formato": por,
            "reaproveitada": "masterclass",
        }
        estado = "ok" if not faltas else "ok, faltam " + ", ".join(faltas)
        relatorio.append((ident, estado))
    return relatorio


# ------------------------------------------------------------------ quadros parados


def conferir_png(caminho: Path, fmt: str) -> str | None:
    """Motivo de reprovação, ou None se o quadro serve."""
    with Image.open(caminho) as im:
        if im.size != FORMATOS[fmt]["video"]:
            return f"tamanho {im.size[0]}x{im.size[1]}"
        cinza = np.asarray(im.convert("L"), float)
    luma = float(cinza.mean())
    if LUMA[0] <= luma <= LUMA[1]:
        return None
    # Página de texto corrido sobre fundo branco passa de 240 de média sem estar vazia. Ela
    # só serve se ao menos 2% dos pixels forem tinta (luma abaixo de 180, ou acima de 75 numa
    # tela escura); tela branca ou preta de verdade fica abaixo de 1%.
    tinta = float((cinza < 180).mean() if luma > LUMA[1] else (cinza > 75).mean())
    if tinta >= TINTA_MINIMA:
        return None
    return f"luminância média {luma:.0f} e {tinta:.1%} de tinta: tela quase vazia"


def contexto(navegador, fmt: str):
    largura, altura = FORMATOS[fmt]["janela"]
    ctx = navegador.new_context(
        viewport={"width": largura, "height": altura},
        device_scale_factor=FORMATOS[fmt]["escala"],
        has_touch=FORMATOS[fmt]["toque"],
        user_agent=mc.AGENTE,
        locale="pt-BR",
        timezone_id="America/Sao_Paulo",
        service_workers="block",
        accept_downloads=False,
    )
    ctx.route(mc.BLOQUEADOS, lambda rota: rota.abort())
    return ctx


def fechar_banners(pag) -> None:
    for _ in range(2):
        alvo = pag.get_by_role("button", name=FECHAR)
        alvo = alvo.or_(pag.locator(FECHAR_SEL))
        try:
            n = alvo.count()
        except ErroPlaywright:
            return
        clicou = False
        for i in range(min(n, 4)):
            item = alvo.nth(i)
            try:
                if item.is_visible():
                    item.click(timeout=1500, no_wait_after=True)
                    clicou = True
                    pag.wait_for_timeout(500)
            except ErroPlaywright:
                continue
        if not clicou:
            return


def fotografar(pw, url: str, fmt: str, destino: Path, pagina: dict) -> str | None:
    """Abre `url`, limpa a tela e grava o quadro. Devolve o motivo da falha, ou None."""
    if url.lower().split("?")[0].endswith(".pdf"):
        return "a fonte é um arquivo PDF, sem página para fotografar"
    navegador = pw.chromium.launch()
    ctx = contexto(navegador, fmt)
    pag = ctx.new_page()
    try:
        try:
            resp = pag.goto(url, wait_until="domcontentloaded", timeout=45000)
        except ErroPlaywright as e:
            texto = str(e)
            if "Download is starting" in texto:
                return "a URL entrega um arquivo (PDF), não uma página"
            return "não abriu: " + texto.splitlines()[0][:120]
        if resp is not None and resp.status >= 400:
            return f"HTTP {resp.status}"
        tipo = (resp.headers.get("content-type", "") if resp else "").lower()
        if "pdf" in tipo:
            return "a URL entrega um PDF, não uma página"
        with contextlib.suppress(TempoPlaywright):
            pag.wait_for_load_state("networkidle", timeout=25000)
        pag.wait_for_timeout(1500)
        texto = pag.evaluate("() => (document.body && document.body.innerText) || ''")
        if len(texto.strip()) < TEXTO_MINIMO:
            return f"página com {len(texto.strip())} caracteres de texto"
        if pagina.get("externa", True):
            fechar_banners(pag)
            pag.evaluate(LIMPAR_JS)
        if pagina.get("titulo", False):
            if pag.evaluate(TITULO_JS) is None:
                return "título (h1) não encontrado"
        else:
            pag.evaluate("() => window.scrollTo(0, 0)")
        pag.wait_for_timeout(900)
        pag.evaluate("() => document.fonts && document.fonts.ready")
        temp = destino.with_suffix(".tmp.png")
        pag.screenshot(path=str(temp))
        motivo = conferir_png(temp, fmt)
        if motivo:
            temp.unlink(missing_ok=True)
            return "quadro reprovado: " + motivo
        temp.replace(destino)
        return None
    finally:
        ctx.close()
        navegador.close()


def capturar_still(pw, item: dict, base: str, saida: dict) -> dict:
    """Um quadro parado por formato; tenta a URL direta e depois o Wayback Machine."""
    ident = item["id"]
    if item.get("pagina"):
        candidatos = [("direto", base + item["pagina"])]
    elif item.get("url"):
        candidatos = [("direto", item["url"])]
        if item.get("archive", True):
            candidatos += [("archive", p + item["url"]) for p in ARQUIVOS_WAYBACK]
    else:
        candidatos = []
    por, motivos = {}, {}
    for fmt in FORMATOS:
        destino = MIDIA / f"cap_{ident}_{fmt}.png"
        tentativas = []
        for origem, url in candidatos:
            motivo = fotografar(pw, url, fmt, destino, item)
            if motivo is None:
                por[fmt] = {"segundos": 0, "stills": {}, "origem": origem, "url": url}
                break
            tentativas.append(f"{origem}: {motivo}")
        else:
            motivos[fmt] = "; ".join(tentativas) or "sem URL no acervo"
    entrada: dict = {
        "formatos": [f for f in FORMATOS if f in por],
        "segundos": 0,
        "stills": {},
        "tipo": "still",
    }
    for chave in ("caso", "fonte", "veiculo"):
        if item.get(chave):
            entrada[chave] = item[chave]
    if por:
        principal = por.get("16x9") or next(iter(por.values()))
        entrada.update(
            origem=principal["origem"], url=principal["url"], por_formato=por
        )
        if motivos:
            entrada["falhas_por_formato"] = motivos
    else:
        anterior = saida.get(ident, {})
        if anterior.get("formatos") and all(
            (MIDIA / f"cap_{ident}_{f}.png").exists() for f in anterior["formatos"]
        ):
            anterior["ultima_falha"] = motivos.get("16x9", "")
            return anterior
        entrada["falhou"] = motivos.get("16x9") or next(iter(motivos.values()), "")
        entrada["url"] = item.get("url") or item.get("pagina")
    return entrada


# ------------------------------------------------------------------ gravações


def gravar_tomadas(pw, tomadas: list[dict], base: str, saida: dict) -> list[str]:
    linhas = []
    for tomada in tomadas:
        for fmt in tomada.get("formatos", list(FORMATOS)):
            r = mc.gravar_tomada(pw, tomada, fmt, base, ([], Path(".")), True)
            final = mc.finalizar_video(tomada, fmt, r)
            if final is not None and not r["falha"]:
                saida[tomada["id"]] = mc.entrada_json(
                    saida.get(tomada["id"], {}),
                    fmt,
                    final,
                    tomada.get("formatos", list(FORMATOS)),
                )
                gravar_saida(saida)
                erros = {k: round(v) for k, v in final["erro_quadro"].items()}
                linhas.append(
                    f"{tomada['id']} {fmt}: ok, {final['segundos']:.1f} s, quadros {final['stills']}, erro {erros}"
                )
            else:
                linhas.append(f"{tomada['id']} {fmt}: falhou ({r['falha']})")
            linhas += [f"    {a}" for a in r["avisos"] + r["erros"]]
    shutil.rmtree(BRUTO / "_temp", ignore_errors=True)
    return linhas


# ------------------------------------------------------------------ principal


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--so", action="append", help="id do item (repita para vários)")
    ap.add_argument(
        "--registrar-existentes",
        action="store_true",
        help="só registra as gravações reaproveitadas da masterclass",
    )
    ap.add_argument("--porta", type=int, default=4173)
    ap.add_argument("--manter-servidor", action="store_true")
    a = ap.parse_args()

    roteiro = atualizar_roteiro(json.loads(ROTEIRO.read_text(encoding="utf-8")))
    MIDIA.mkdir(parents=True, exist_ok=True)
    conhecidos = set(roteiro["reaproveitadas"]) | {
        p["id"] for p in roteiro["materias"] + roteiro["paginas"] + roteiro["tomadas"]
    }
    if a.so and not set(a.so) <= conhecidos:
        raise SystemExit(
            "Id desconhecido em --so: " + ", ".join(set(a.so) - conhecidos)
        )
    # Só entra o que este roteiro declara: a cópia herdada da masterclass sai.
    saida = {k: v for k, v in carregar_saida().items() if k in conhecidos}

    quer = (lambda i: i in a.so) if a.so else (lambda _i: True)
    reaproveitadas = [i for i in roteiro["reaproveitadas"] if quer(i)]
    for ident, estado in registrar_existentes(reaproveitadas, saida):
        print(f"[reaproveitada] {ident}: {estado}")
    gravar_saida(saida)
    if a.registrar_existentes:
        return 0

    for p in roteiro["materias"]:
        p["titulo"] = True
    stills = [p for p in roteiro["materias"] + roteiro["paginas"] if quer(p["id"])]
    tomadas = [t for t in roteiro["tomadas"] if quer(t["id"])]

    with mc.servidor(a.porta, a.manter_servidor) as base, sync_playwright() as pw:
        for item in stills:
            saida[item["id"]] = capturar_still(pw, item, base, saida)
            gravar_saida(saida)
            e = saida[item["id"]]
            if e.get("falhou"):
                estado = "falhou (" + e["falhou"][:160] + ")"
            else:
                estado = e.get("origem", "?") + " " + "/".join(e["formatos"])
            print(f"[still] {item['id']}: {estado}")
        for linha in gravar_tomadas(pw, tomadas, base, saida):
            print(f"[tomada] {linha}")
    gravar_saida(saida)
    print(f"\n{SAIDA_JSON}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
