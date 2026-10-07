"""Página da super thread: CSS, JS de cópia e montagem do HTML dos cards 1:1."""

from __future__ import annotations

from ga_tag import injetar

from .thread_base import DOSSIE, OG, SLUG, URL, esc

TOM = {
    "flavio": "#1457aa",
    "lula": "#b02f21",
    "outros": "#0b6650",
}

CSS = """
*,*::before,*::after{box-sizing:border-box}
:root{--paper:#f4f0e6;--paper2:#ebe5d6;--ink:#192e2b;--muted:#535b54;--line:#d6cfbd;
  --flavio:#1457aa;--lula:#b02f21;--outros:#0f7f5f;--gold:#7d5b00;
  --display:Fraunces,Georgia,serif;--sans:"IBM Plex Sans Condensed",Arial,sans-serif;--mono:"IBM Plex Mono",ui-monospace,monospace;
  --wrap:min(1120px,calc(100% - 32px))}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:18px;line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{width:var(--wrap);margin:0 auto}
a{color:var(--flavio)}
.top{padding:28px 0 6px;display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between}
.brand-lockup{display:flex;align-items:center;gap:10px;font-family:var(--mono);font-size:.78rem;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.brand-lockup img{width:26px;height:26px;border-radius:4px}
.back{font-family:var(--mono);font-size:.78rem;letter-spacing:.08em;text-transform:uppercase;color:var(--flavio);text-decoration:none;border:1px solid var(--flavio);border-radius:999px;padding:7px 15px}
h1{font-family:var(--display);font-size:clamp(2.1rem,5.6vw,4rem);line-height:1.02;letter-spacing:-.02em;margin:16px 0 0;font-weight:900}
h1 em{display:block;font-style:italic;color:var(--flavio);font-weight:500}
.deck{max-width:74ch;margin:18px 0 0;font-size:1.08rem}
.howto{margin:22px 0 0;border-left:4px solid var(--flavio);background:var(--paper2);border-radius:4px;padding:16px 20px;font-size:.98rem;max-width:80ch}
.rail{position:sticky;top:0;z-index:20;margin:26px 0 0;padding:10px 0;background:rgb(244 240 230 / 94%);backdrop-filter:blur(8px);border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.rail .wrap{display:flex;gap:5px;align-items:center;overflow-x:auto;scrollbar-width:none}
.rail b{font-family:var(--mono);font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin-right:8px;white-space:nowrap}
.rail a{min-width:30px;height:30px;flex:0 0 auto;display:grid;place-items:center;border-radius:5px;border:1px solid var(--line);color:var(--ink);text-decoration:none;font-family:var(--mono);font-size:.78rem;background:#fff}
.post{margin:56px 0 0;scroll-margin-top:64px}
.post-label{width:min(100%,900px);margin:0 auto 10px;font-family:var(--mono);font-size:.78rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.post-label b{color:var(--ink)}
/* O card é quadrado, 1:1; a largura de trabalho do PNG é 1080 px. */
.card{position:relative;aspect-ratio:1/1;width:min(100%,900px);margin:0 auto;background:var(--paper);border:1px solid var(--line);border-radius:10px;overflow:hidden;container-type:inline-size;display:grid;grid-template-rows:auto auto minmax(0,1fr) auto}
.c-head{display:flex;align-items:center;justify-content:space-between;gap:12px;background:var(--ink);color:var(--paper);padding:1.5cqw 3.4cqw;border-bottom:.5cqw solid var(--accent)}
.c-brand{display:flex;align-items:center;gap:1.1cqw;font-family:var(--mono);font-size:1.6cqw;letter-spacing:.12em;text-transform:uppercase}
.c-brand img{width:2.8cqw;height:2.8cqw;border-radius:3px}
.c-pno{font-family:var(--mono);font-size:1.8cqw;font-weight:700;letter-spacing:.08em}
.c-top{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:0 3cqw;align-items:end;padding:2.6cqw 3.4cqw 0}
.c-tag{grid-column:1/-1;font-family:var(--mono);font-size:1.6cqw;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--accent);margin-bottom:.8cqw}
.c-top h2{font-family:var(--display);font-weight:800;font-size:3.9cqw;line-height:1.08;letter-spacing:-.015em;margin:0}
.c-metric{text-align:right;max-width:36cqw}
.c-metric b{display:block;font-family:var(--display);font-weight:900;font-size:7cqw;line-height:.95;letter-spacing:-.03em;color:var(--accent);white-space:nowrap}
.c-metric span{display:block;font-size:1.7cqw;line-height:1.3;color:var(--ink);margin-top:.6cqw}
.c-viz{min-height:0;display:flex;align-items:center;justify-content:center;padding:2cqw 3.4cqw 1cqw}
.c-viz svg{width:100%;height:100%;max-height:100%;display:block}
.c-foot{display:flex;justify-content:space-between;gap:2cqw;padding:1.3cqw 3.4cqw;border-top:1px solid var(--line);font-family:var(--mono);font-size:1.45cqw;color:var(--muted)}
.c-foot b{color:var(--ink);font-weight:700}
.copy{margin:16px auto 0;width:min(100%,900px);border:1px solid var(--line);border-radius:8px;background:#fff;padding:20px 22px;font-size:1rem;line-height:1.7;white-space:pre-wrap;position:relative}
.cc{display:block;text-align:right;font-family:var(--mono);font-size:.74rem;color:var(--muted);letter-spacing:.06em;margin-bottom:6px}
.copy-btn{margin:10px auto 0;display:block;width:min(100%,900px);font-family:var(--mono);font-size:.8rem;letter-spacing:.1em;text-transform:uppercase;background:var(--ink);color:var(--paper);border:0;border-radius:999px;padding:11px 18px;cursor:pointer;text-align:center}
.copy-btn:focus-visible{outline:3px solid var(--flavio);outline-offset:3px}
footer{margin:72px 0 0;border-top:1px solid var(--line);padding:30px 0 60px;font-size:.96rem}
footer h2{font-family:var(--display);font-size:1.6rem;margin:0 0 10px}
.pngs{columns:2 220px;padding-left:1.2em;font-family:var(--mono);font-size:.86rem}
@media (width <= 720px){
  .c-metric b{font-size:2.4rem!important}
  body{font-size:16px}
  .card{aspect-ratio:auto;display:block}
  .c-head{padding:10px 14px}
  .c-brand{font-size:.68rem;gap:8px}
  .c-brand img{width:22px;height:22px}
  .c-pno{font-size:.78rem}
  .c-top{display:block;padding:16px 16px 0}
  .c-tag{font-size:.72rem;margin-bottom:6px}
  .c-top h2{font-size:1.45rem}
  .c-metric{text-align:left;max-width:none;margin-top:12px}
  .c-metric b{white-space:normal}
  .c-metric span{font-size:.9rem}
  .c-viz{padding:14px 10px 8px;overflow-x:auto;justify-content:flex-start}
  .c-viz svg{height:auto;min-width:680px}
  .c-foot{flex-direction:column;gap:4px;padding:10px 16px;font-size:.7rem}
  .copy{padding:16px 15px;font-size:.95rem}
}
"""

JS = """
function cp(botao){
  var no = botao.previousElementSibling;
  var texto = no.getAttribute('data-copy');
  function pronto(){ var o = botao.textContent; botao.textContent = 'Copiado'; setTimeout(function(){ botao.textContent = o; }, 1600); }
  function reserva(){
    var area = document.createElement('textarea');
    area.value = texto; area.setAttribute('readonly', ''); area.style.position = 'fixed'; area.style.opacity = '0';
    document.body.appendChild(area); area.select();
    try { document.execCommand('copy'); pronto(); } catch (e) {}
    document.body.removeChild(area);
  }
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(texto).then(pronto, reserva);
  } else { reserva(); }
}
"""


def _tamanho_metrica(s: str) -> float:
    """A métrica cabe numa linha da coluna da direita, até 36% da largura do card."""
    n = len(s)
    if n <= 6:
        return 7.0
    return round(max(3.6, min(7.0, 44 / n)), 1)


def render_card(i: int, total: int, post: dict) -> str:
    cor = TOM[post["tom"]]
    corpo = post["corpo"]
    return f"""
<section class="post" id="p{i:02d}">
  <div class="post-label">Post {i:02d}/{total:02d} · <b>{esc(post["tag_f"])}</b></div>
  <article class="card" style="--accent:{cor}" aria-label="Card {i} de {total}: {esc(post["titulo_f"])}">
    <header class="c-head"><span class="c-brand">Arvor · Apuração 2026</span><span class="c-pno">{i:02d} / {total:02d}</span></header>
    <div class="c-top">
      <div class="c-tag">{esc(post["tag_f"])}</div>
      <h2>{esc(post["titulo_f"])}</h2>
      <div class="c-metric"><b style="font-size:{_tamanho_metrica(post["metrica_f"])}cqw">{esc(post["metrica_f"])}</b><span>{esc(post["metrica_rot_f"])}</span></div>
    </div>
    <div class="c-viz" tabindex="0" role="region" aria-label="Gráfico do card {i}">{post["svg"]}</div>
    <footer class="c-foot"><span>Fonte: {esc(post["fonte_f"])}</span><b>brasil.arvor.co</b></footer>
  </article>
  <div class="copy" data-copy="{esc(corpo)}"><span class="cc">{len(corpo)} caracteres</span>{esc(corpo)}</div>
  <button class="copy-btn" type="button" onclick="cp(this)">Copiar texto do post {i:02d}</button>
</section>"""


def pagina(posts: list[dict], pngs: list[str], v: dict) -> str:
    total = len(posts)
    cards = "".join(render_card(i + 1, total, p) for i, p in enumerate(posts))
    rail = "".join(f'<a href="#p{i + 1:02d}">{i + 1}</a>' for i in range(total))
    lista = "".join(f'<li><a href="{esc(p)}">{esc(p)}</a></li>' for p in pngs)
    titulo = "A apuração do 1º turno de 2026: a super thread"
    desc = (
        f"{total} cards quadrados com gráficos e o texto pronto para o X: o placar de "
        f"{v['f_pct']} contra {v['l_pct']}, a noite minuto a minuto, as paradas do TSE, "
        "pesquisas contra urna, a auditoria por zona e por seção e o caminho do 2º turno."
    )
    return injetar(f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(titulo)} · Arvor</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{URL}">
<link rel="icon" href="favicon.ico" sizes="any">
<link rel="icon" href="img/favicon.svg" type="image/svg+xml">
<meta name="theme-color" content="#192e2b">
<meta property="og:type" content="article">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="Arvor Intelligence">
<meta property="og:title" content="{esc(titulo)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{URL}">
<meta property="og:image" content="{OG}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@leonardodias">
<meta name="twitter:title" content="{esc(titulo)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{OG}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,500;0,9..144,700;0,9..144,800;0,9..144,900;1,9..144,500&amp;family=IBM+Plex+Mono:wght@400;500;600;700&amp;family=IBM+Plex+Sans+Condensed:wght@400;500;600;700;800&amp;display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<header class="wrap">
  <div class="top">
    <div class="brand-lockup"><img src="img/arvor_logo.png" alt="">Arvor Intelligence · super thread</div>
    <a class="back" href="{DOSSIE}.html">Abrir o dossiê</a>
  </div>
  <h1>A apuração do 1º turno de 2026. <em>A super thread, card a card.</em></h1>
  <p class="deck">Flávio Bolsonaro terminou o 1º turno com {esc(v["f_pct"])} dos válidos contra {esc(v["l_pct"])} de Lula, {esc(v["dif_mi"])} de votos à frente. Esta é a thread do dossiê da apuração: a noite minuto a minuto, as paradas do arquivo nacional do TSE, a arquitetura, 2022 contra 2026, Câmara, Senado, assembleias e governadores, pesquisas contra urna, a auditoria por zona e por seção e, no fim, o 2º turno com as estratégias e as frases para conversar com o eleitor de terceira via.</p>
  <div class="howto"><b>Como usar.</b> Cada card é a imagem do post, um quadrado que sai em 1080 por 1080 pixels; os PNGs prontos para anexar estão listados no fim da página. Embaixo de cada card está o texto do post, para X premium, com o botão de copiar. Nenhum número foi digitado à mão: todos saem dos arquivos de dados do dossiê, e o gerador recusa texto com algarismo solto, travessão, hashtag ou emoji. Onde há opinião da casa, o próprio texto diz juízo editorial.</div>
</header>
<nav class="rail" aria-label="Posts"><div class="wrap"><b>Posts</b>{rail}</div></nav>
<main class="wrap">{cards}</main>
<footer class="wrap">
  <h2>Imagens para anexar</h2>
  <p>Os {total} cards em PNG, 1080 por 1080 pixels, na ordem dos posts:</p>
  <ol class="pngs">{lista}</ol>
  <h2>Reprodução</h2>
  <p>python3 scripts/apuracao-2026-thread.py (com --png para regerar as imagens). Os números vêm de analysis/apuracao_2026/dados/; as falas citadas, de analysis/apuracao_2026/fontes_thread.json, com veículo, data e endereço. O dossiê completo está em <a href="{DOSSIE}.html">{DOSSIE}.html</a>.</p>
</footer>
<script>{JS}</script>
</body>
</html>
""")


__all__ = ["CSS", "JS", "SLUG", "TOM", "pagina", "render_card"]
