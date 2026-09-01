#!/usr/bin/env python3
"""Gera docs/mg_082026_thread.html: dois posts para o X e a imagem única.

Não é a thread educativa de dezoito cards. É o formato curto: um post com o
infográfico e um post com o link, para circular sem exigir que o leitor
acompanhe uma sequência.

Reprodução:
    python3 scripts/mg-082026-infografico.py && python3 scripts/mg-082026-thread.py
"""

from __future__ import annotations

from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAIDA = ROOT / "docs/mg_082026_thread.html"

POST1 = """Minas Gerais decide a eleição e quase ninguém entende Minas.

São 16,3 milhões de eleitores, o segundo maior colégio do Brasil. Em 2022 o estado foi decidido por 0,40 ponto. Agora o Datafolha de agosto mostra Lula com 46 e Flávio Bolsonaro com 42 dentro do estado.

Pegamos os 853 municípios mineiros, um por um, com os votos oficiais do TSE de 2018 e de 2022. E achamos uma coisa que ninguém tinha medido.

Todo mundo repete que Cleitinho é o grande puxador de voto da direita mineira. Ele fez 4,2 milhões de votos para o Senado em 2022, o maior número do estado inteiro. Só que, no mesmo dia e na mesma urna, ele fez 41,3% e Bolsonaro fez 43,4%.

Ou seja: Cleitinho não puxa mais voto que Bolsonaro. Ele puxa em outro lugar. E isso muda tudo.

Montamos uma régua simples. Em cada cidade, medimos quanto cada nome rendeu ali comparado com a média dele mesmo no estado, e comparamos com Bolsonaro. Deu este mapa:

Cleitinho vai mais longe que Bolsonaro em 431 cidades, quase todas no Oeste e nos vales pobres do Norte.

Bruno Engler vai mais longe em 75 cidades, mas elas valem 30% do eleitorado, porque são a Grande BH.

Nikolas Ferreira vai mais longe em 45 cidades, quase todas no cinturão metropolitano.

E em 302 cidades, que são 24% do eleitorado, nenhum dos três supera Bolsonaro.

Na prática: o aliado que ajuda numa praça atrapalha na outra. No Sul e no Triângulo, que juntos são 13,85% do eleitorado mineiro, nenhum dos três ajuda. Ali o candidato se vira sozinho.

Mas existe um lugar onde os três ajudam ao mesmo tempo: o cinturão do minério, o Quadrilátero Ferrífero. Bolsonaro fez só 36,9% ali, contra 43,4% no estado. Dez das vinte cidades trocaram de lado em 2022. E tem pauta concreta esperando na mesa: a Vale está sendo cobrada em R$ 17,7 bilhões de royalties atrasados, e R$ 3,2 bilhões disso iriam para municípios mineiros. Só Itabira teria R$ 822,6 milhões a receber.

Isso não é discussão ideológica. É dinheiro que a cidade tem a receber, com valor, devedor e destinatário.

Minas não é um bloco. São sete conversas diferentes, e cada uma tem um assunto que funciona:

No minério: o minério sai daqui e a conta fica aqui.

Na periferia de BH: não falta discurso, falta ônibus, posto e polícia.

No Sul e no Triângulo: o café perdeu 34% do que exportava aos Estados Unidos neste ano.

Nos vales do Norte: ali não se pede o voto, se pede para ser ouvido.

Quem tratar Minas como um bloco vai perder Minas por pouco. De novo."""

POST2 = """O dossiê inteiro está publicado e aberto: os 853 municípios, as sete regiões, o mapa interativo, quem tem base eleitoral medida em cada canto do estado e a metodologia completa.

brasil.arvor.co/mg_082026.html

Qualquer pessoa pode refazer as contas. Os arquivos do TSE, do IBGE e da PNAD estão listados um a um, com o código de verificação de cada um. Se algum número estiver errado, dá para provar."""


def bloco(indice: int, rotulo: str, texto: str, extra: str = "") -> str:
    return f"""
<section class="post" id="p{indice}">
  <div class="post-label">Post {indice}/2 · <b>{escape(rotulo)}</b></div>
  {extra}
  <div class="copy" data-copy="{escape(texto, quote=True)}">{escape(texto).replace(chr(10) + chr(10), "</p><p>").replace(chr(10), "<br>").join(("<p>", "</p>"))}</div>
  <button class="copy-btn" onclick="cp(this)">Copiar texto</button>
  <p class="chars">{len(texto)} caracteres</p>
</section>"""


IMAGEM = """
  <figure class="shot">
    <img src="img/og/mg_082026_infografico.png" alt="Infográfico do atlas de Minas Gerais: mapa dos 853 municípios pintado por quem vai mais longe que Bolsonaro, retratos de Flávio Bolsonaro, Cleitinho, Nikolas Ferreira e Bruno Engler, tabela dos sete corredores e o alvo no cinturão do minério.">
    <figcaption>Anexe esta imagem ao post. Ela está em <code>docs/img/og/mg_082026_infografico.png</code>, em 3000 por 6324 pixels.</figcaption>
  </figure>"""

HTML = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Minas 2026: os dois posts do atlas · Arvor</title>
<meta name="description" content="Dois posts prontos para o X com o infográfico do atlas de Minas Gerais: o mapa de quem vai mais longe que Bolsonaro em cada uma das 853 cidades, e o alvo no cinturão do minério.">
<link rel="canonical" href="https://brasil.arvor.co/mg_082026_thread.html">
<link rel="icon" href="favicon.ico" sizes="any">
<link rel="icon" href="img/favicon.svg" type="image/svg+xml">
<meta name="theme-color" content="#0c0d0b">
<meta property="og:type" content="article">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="Arvor Intelligence">
<meta property="og:title" content="Minas 2026: os dois posts do atlas">
<meta property="og:description" content="O mapa de quem vai mais longe que Bolsonaro em cada uma das 853 cidades de Minas, com o texto pronto para publicar.">
<meta property="og:url" content="https://brasil.arvor.co/mg_082026_thread.html">
<meta property="og:image" content="https://brasil.arvor.co/img/og/mg_082026_thread.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@leonardodias">
<meta name="twitter:image" content="https://brasil.arvor.co/img/og/mg_082026_thread.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,500;0,9..144,900;1,9..144,500&amp;family=IBM+Plex+Mono:wght@500&amp;family=IBM+Plex+Sans+Condensed:wght@400;600;700&amp;display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{box-sizing:border-box}}
:root{{--bg:#0c0d0b;--bg2:#131512;--bg3:#191c18;--ink:#f4f2ea;--ink2:#ddd8ca;
 --muted:#9a9789;--lime:#cfe63c;--cyan:#45c9c2;--amber:#f0a930;
 --line:rgb(244 242 234 / 13%);--line2:rgb(244 242 234 / 26%);
 --display:Fraunces,Georgia,serif;--sans:"IBM Plex Sans Condensed",Arial,sans-serif;
 --mono:"IBM Plex Mono",ui-monospace,monospace;--wrap:min(1080px,calc(100% - 40px))}}
html{{scroll-behavior:smooth;-webkit-text-size-adjust:100%}}
body{{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);
 font-size:17px;line-height:1.62;-webkit-font-smoothing:antialiased}}
.wrap{{width:var(--wrap);margin:0 auto}}
a{{color:var(--cyan)}}
.top{{padding:34px 0 8px;display:flex;flex-wrap:wrap;gap:14px;align-items:center;justify-content:space-between}}
.brand-lockup{{display:flex;align-items:center;gap:11px;font-family:var(--mono);
 font-size:.76rem;letter-spacing:.13em;text-transform:uppercase;color:var(--muted)}}
.brand-lockup img{{width:26px;height:26px;border-radius:4px}}
.top .back{{font-family:var(--mono);font-size:.74rem;letter-spacing:.1em;text-transform:uppercase;
 color:var(--lime);text-decoration:none;border:1px solid var(--line2);border-radius:999px;padding:7px 15px}}
h1{{font-family:var(--display);font-size:clamp(2.3rem,6.4vw,4.2rem);line-height:.98;
 letter-spacing:-.028em;margin:18px 0 0;font-weight:900}}
h1 em{{display:block;font-style:italic;color:var(--lime);font-weight:500}}
.deck{{max-width:74ch;color:var(--ink2);margin:20px 0 0;font-size:1.06rem}}
.howto{{margin:26px 0 40px;border:1px solid var(--line);border-left:3px solid var(--cyan);
 border-radius:4px;background:var(--bg3);padding:18px 20px;color:var(--ink2);font-size:.95rem}}
.howto b{{color:var(--ink)}}
.post{{margin:0 0 46px;padding:26px 0 0;border-top:1px solid var(--line)}}
.post-label{{font-family:var(--mono);font-size:.72rem;letter-spacing:.13em;
 text-transform:uppercase;color:var(--muted);margin-bottom:18px}}
.post-label b{{color:var(--lime);font-weight:500}}
.shot{{margin:0 0 20px;border:1px solid var(--line);background:var(--bg2);padding:12px}}
.shot img{{width:100%;display:block}}
.shot figcaption{{margin-top:12px;font-family:var(--mono);font-size:.74rem;color:var(--muted);line-height:1.5}}
.shot code{{color:var(--amber)}}
.copy{{margin:14px 0 0;border:1px solid var(--line);border-radius:6px;background:var(--bg2);
 padding:20px 22px;font-size:1.02rem;color:var(--ink)}}
.copy p{{margin:0 0 .95em}}
.copy p:last-child{{margin-bottom:0}}
.copy-btn{{margin-top:12px;font-family:var(--mono);font-size:.74rem;letter-spacing:.11em;
 text-transform:uppercase;color:var(--lime);background:none;cursor:pointer;
 border:1px solid var(--line2);border-radius:999px;padding:9px 17px}}
.copy-btn:hover{{border-color:var(--lime)}}
.chars{{margin:10px 0 0;font-family:var(--mono);font-size:.72rem;color:var(--muted)}}
footer{{margin-top:20px;padding:34px 0 70px;border-top:1px solid var(--line)}}
footer h2{{font-family:var(--display);font-weight:900;font-size:1.7rem;margin:0 0 14px}}
footer p{{color:var(--muted);font-size:.92rem;max-width:82ch;margin:0 0 12px}}
@media(max-width:620px){{.copy{{padding:16px 15px;font-size:.95rem}}}}
</style>
</head>
<body>
<div class="wrap">
  <div class="top">
    <span class="brand-lockup"><img src="img/arvor_logo.png" alt="">Arvor Intelligence</span>
    <a class="back" href="mg_082026.html">Ver o dossiê completo</a>
  </div>
  <h1>Minas em dois posts<em>e uma imagem só.</em></h1>
  <p class="deck">O atlas de Minas Gerais tem quinze capítulos e 853 municípios. Isso não cabe numa linha do tempo. Então o argumento inteiro foi reduzido a um infográfico e a dois posts: o primeiro carrega a descoberta, o segundo entrega o dossiê para quem quiser conferir.</p>
  <div class="howto"><b>Como publicar.</b> Anexe a imagem ao primeiro post e copie o texto abaixo dela. O segundo post entra como resposta ao primeiro, com o link. O texto do primeiro post passa de 280 caracteres e por isso exige conta paga no X.</div>

{bloco(1, "a descoberta, com a imagem", POST1, IMAGEM)}
{bloco(2, "o link, em resposta ao primeiro", POST2)}

<footer>
  <h2>Refaça a conta</h2>
  <p>Os números destes posts saem da votação nominal por município publicada pelo Tribunal Superior Eleitoral para 2018 e 2022, do perfil do eleitorado de 1º de julho de 2026, do Censo 2022 e do PIB municipal do IBGE, e da PNAD contínua anual de 2025. A pesquisa citada é o Datafolha de Minas Gerais com campo de 18 a 20 de agosto de 2026, 1.204 entrevistas e margem de 3 pontos.</p>
  <p>O índice que compara cada nome com Bolsonaro é medida de alcance territorial em eleições passadas, e não de transferência de voto. A unidade é o município, nunca a pessoa. As duas ressalvas estão escritas no dossiê, no mesmo lugar do achado.</p>
  <p>Retratos do Wikimedia Commons, com autoria e licença creditadas no dossiê e na imagem. Nenhum instituto, veículo, partido ou campanha participou da produção deste material.</p>
</footer>
</div>
<script>
function cp(button){{
  const node = button.previousElementSibling;
  const text = node.getAttribute('data-copy') || node.innerText;
  navigator.clipboard.writeText(text).then(() => {{
    const original = button.textContent;
    button.textContent = 'copiado';
    setTimeout(() => {{ button.textContent = original; }}, 1600);
  }});
}}
</script>
</body>
</html>"""

if "—" in HTML:
    raise SystemExit("travessão encontrado na página da thread")
SAIDA.write_text(HTML, encoding="utf-8")
print(f"gravado {SAIDA}")
print(f"post 1: {len(POST1)} caracteres | post 2: {len(POST2)} caracteres")
