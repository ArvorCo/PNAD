#!/usr/bin/env python3
"""Gera docs/mapa_do_voto_util.html: o mapa do voto util em Flavio no 1o turno.

Todo numero vem de `docs/assets/voto_util_092026.json` (gerado por
`voto-util-092026-data.py`). Figuras em `voto_util_figuras.py`, capitulos de
analise em `voto_util_capitulos.py` e de campanha em `voto_util_campanha.py`.
A pagina abre do disco, sem rede: o JavaScript so acrescenta a calculadora e o
seletor de estado; sem ele, tudo continua legivel.

Reproducao:
    python3 scripts/voto-util-092026-tse.py
    python3 scripts/voto-util-092026-data.py
    python3 scripts/voto-util-092026-build.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SAIDA = DOCS / "mapa_do_voto_util.html"


def _modulo(nome: str):
    if nome in sys.modules:
        return sys.modules[nome]
    spec = importlib.util.spec_from_file_location(nome, ROOT / "scripts" / f"{nome}.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nome] = mod
    spec.loader.exec_module(mod)
    return mod


CAP = _modulo("voto_util_capitulos")
CAMP = _modulo("voto_util_campanha")

SECOES = [
    ("tese", "A tese"),
    ("fenomeno", "O fenômeno"),
    ("matematica", "A regra"),
    ("mapa", "O mapa"),
    ("nacional", "Para onde vão"),
    ("reencontro", "Eleitor de 2022"),
    ("terceira", "Terceira via"),
    ("governadores", "Governadores"),
    ("senado", "Senado"),
    ("provavel", "Comparecimento"),
    ("resiliente", "Voto firme"),
    ("modelo", "O modelo"),
    ("argumentos", "O que dizer"),
    ("estados", "Seu estado"),
    ("kit", "Última semana"),
    ("municipios", "Cidades"),
    ("lei", "Dentro da lei"),
    ("limites", "Limites"),
    ("fontes", "Fontes"),
]

CSS = """
*,*::before,*::after{box-sizing:border-box}
:root{--paper:#f7f5ee;--paper2:#efece2;--card:#ffffff;--ink:#151812;--ink2:#2a2f27;--muted:#535b54;--line:#d5d2c6;
 --flavio:#1f5f9e;--flavio-txt:#1a5189;--lula:#c8412f;--lula-txt:#a8321f;--terceira:#0f7f5f;--gold:#7d5b00;--amarelo:#f2c230;
 --hero:#0d2238;--hero2:#123150;
 --display:Fraunces,Georgia,serif;--sans:"IBM Plex Sans Condensed",Arial,sans-serif;--mono:"IBM Plex Mono",ui-monospace,monospace;
 --wrap:min(1120px,calc(100% - 32px))}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:17.5px;line-height:1.62;-webkit-font-smoothing:antialiased}
.wrap{width:var(--wrap);margin:0 auto}
a{color:#1d5f97}
a:hover{color:#123f66}
code{font-family:var(--mono);font-size:.86em;background:var(--paper2);padding:1px 5px;border-radius:3px}
.skip{position:absolute;left:-9999px}
.skip:focus{left:8px;top:8px;background:var(--ink);color:var(--paper);padding:10px 14px;z-index:99}
.hero{background:linear-gradient(160deg,var(--hero) 0%,var(--hero2) 70%,#1b3f2c 100%);color:#f4f2ea;padding:0 0 48px;position:relative;overflow:hidden}
.hero::after{content:"";position:absolute;right:-120px;top:-120px;width:420px;height:420px;border-radius:50%;background:radial-gradient(circle,rgb(242 194 48 / 22%),transparent 70%)}
.hero a{color:var(--amarelo)}
.brand{display:flex;align-items:center;gap:10px;padding:22px 0 0;font-family:var(--mono);font-size:.76rem;letter-spacing:.13em;text-transform:uppercase;color:#b8c2cc;position:relative;z-index:1}
.brand a{display:flex;align-items:center;gap:10px;color:inherit;text-decoration:none}
.brand img{width:26px;height:26px;border-radius:4px}
.eyebrow{font-family:var(--mono);font-size:.76rem;letter-spacing:.14em;text-transform:uppercase;color:var(--amarelo);margin:34px 0 0}
.hero h1{font-family:var(--display);font-size:clamp(2.3rem,6.4vw,4.6rem);line-height:.98;letter-spacing:-.028em;margin:14px 0 0;font-weight:900;max-width:18ch;position:relative;z-index:1}
.hero h1 em{display:block;font-style:italic;font-weight:500;color:var(--amarelo)}
.hero .deck{max-width:74ch;color:#dfe5ea;font-size:1.08rem;margin:22px 0 0;position:relative;z-index:1}
.hero-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:18px;margin:32px 0 0;position:relative;z-index:1}
.hero-stats div{border-top:3px solid var(--amarelo);padding-top:10px}
.hero-stats b{display:block;font-family:var(--display);font-size:2.3rem;line-height:1;font-weight:900}
.hero-stats span{display:block;font-size:.9rem;color:#c9d2da;margin-top:6px}
.case-file{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:1px;background:#2b4560;border:1px solid #2b4560;margin:32px 0 0;position:relative;z-index:1}
.case-file>div{background:var(--hero);padding:12px 14px}
.case-file dt{font-family:var(--mono);font-size:.68rem;letter-spacing:.11em;text-transform:uppercase;color:#9fb0c0}
.case-file dd{margin:4px 0 0;font-size:.95rem}
.toc{position:sticky;top:0;z-index:20;background:rgb(247 245 238 / 96%);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
.toc .wrap{display:flex;gap:6px;align-items:center;overflow-x:auto;padding:10px 0;scrollbar-width:none}
.toc b{font-family:var(--mono);font-size:.68rem;letter-spacing:.13em;color:var(--muted);margin-right:8px;white-space:nowrap}
.toc a{font-family:var(--mono);font-size:.74rem;text-decoration:none;color:var(--muted);border:1px solid var(--line);border-radius:999px;padding:5px 12px;white-space:nowrap}
.toc a:hover{border-color:var(--ink);color:var(--ink)}
section{padding:56px 0;border-bottom:1px solid var(--line)}
section.escuro{background:var(--hero);color:#eef1f4}
.kicker{font-family:var(--mono);font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;color:var(--gold);margin:0}
h2{font-family:var(--display);font-size:clamp(1.7rem,3.4vw,2.55rem);line-height:1.08;letter-spacing:-.02em;margin:10px 0 18px;font-weight:700;max-width:30ch}
h3{font-family:var(--display);font-size:1.3rem;margin:30px 0 10px;font-weight:700}
h4{font-family:var(--mono);font-size:.74rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin:18px 0 6px}
p{max-width:78ch}
.lead{font-size:1.15rem}
.callout{border-left:3px solid var(--gold);background:var(--paper2);padding:16px 20px;margin:26px 0;max-width:82ch}
.callout.contra{border-left-color:var(--lula)}
.fig{margin:28px 0;border:1px solid var(--line);background:#fff;border-radius:8px;padding:16px}
.fig.wide{padding:18px 18px 12px}
.fig-svg{width:100%;height:auto;display:block}
figcaption{font-family:var(--mono);font-size:.78rem;color:var(--muted);margin-top:12px;line-height:1.5}
.mapa-grid{display:grid;grid-template-columns:1.25fr 1fr;gap:18px;align-items:start}
.mapa-grid .fig{margin:18px 0}
.table-scroll{overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:#fff;margin:22px 0}
table{border-collapse:collapse;width:100%;font-size:.92rem}
th,td{text-align:left;padding:9px 13px;border-bottom:1px solid var(--line);white-space:nowrap}
thead th{font-family:var(--mono);font-size:.7rem;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);background:var(--paper2)}
tbody th{font-weight:600}
.compact table{font-size:.86rem}
.sub{font-family:var(--mono);font-size:.74rem;color:var(--muted)}
.source{font-family:var(--mono);font-size:.78rem;color:var(--muted);line-height:1.55}
.grid2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin:22px 0}
.grid3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin:22px 0}
.card{background:#fff;border:1px solid var(--line);border-radius:8px;padding:16px 18px}
.card h3{margin-top:0;font-size:1.15rem}
.card p,.card li{font-size:.97rem}
.card.destaque-azul{border-top:4px solid var(--flavio)}
.card.destaque-vermelho{border-top:4px solid var(--lula)}
.card.ok{border-top:4px solid #2f7d52}
.card.nao{border-top:4px solid var(--lula)}
ol.numeros li,ol.passos li,ol.limites li{margin:0 0 12px;max-width:80ch}
ul.destaques li{margin:0 0 10px;max-width:84ch}
.args{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px;margin:18px 0}
.arg{background:#fff;border:1px solid var(--line);border-radius:8px;padding:14px 18px;border-left:4px solid var(--flavio)}
.arg.regiao{border-left-color:var(--amarelo)}
.arg h3{margin:4px 0 8px;font-size:1.08rem}
.arg ul{padding-left:18px;margin:0}
.arg li{margin:0 0 8px;font-size:.96rem}
ul.frases li{margin:0 0 8px;font-size:1rem}
ul.frases li::marker{content:"› ";color:var(--flavio)}
ul.ramos li{margin:0 0 8px;max-width:84ch}
.fichas{display:grid;gap:10px;margin:18px 0}
.ficha{background:#fff;border:1px solid var(--line);border-radius:8px}
.ficha summary{cursor:pointer;padding:12px 16px;display:flex;gap:10px;align-items:baseline;list-style:none}
.ficha summary::-webkit-details-marker{display:none}
.ficha summary::before{content:"+";font-family:var(--mono);color:var(--flavio);font-weight:700}
.ficha[open] summary::before{content:"−"}
.ficha summary b{font-family:var(--mono);font-size:.9rem;color:var(--flavio-txt)}
.ficha summary span{margin-left:auto;font-family:var(--mono);font-size:.8rem;color:var(--muted)}
.ficha-corpo{padding:0 16px 14px}
.seletor{display:flex;gap:10px;align-items:center;margin:14px 0;font-family:var(--mono);font-size:.85rem}
.seletor select{font:inherit;padding:6px 10px;border:1px solid var(--line);border-radius:6px;background:#fff}
.calc{background:#fff;border:2px solid var(--flavio);border-radius:10px;padding:18px 20px;margin:24px 0}
.calc-ctrl label{display:block;font-weight:600;margin-bottom:6px}
.calc-ctrl input[type=range]{width:100%;accent-color:var(--flavio)}
.calc fieldset{border:0;padding:0;margin:12px 0 0;display:flex;flex-wrap:wrap;gap:6px 18px}
.calc legend{font-weight:600;margin-bottom:4px}
.calc fieldset label{font-weight:400;display:flex;gap:6px;align-items:center}
.calc-bar{position:relative;height:34px;background:#e6e3d9;border-radius:6px;margin:18px 0 10px;overflow:hidden;display:flex}
.calc-f{display:block;height:100%;background:var(--flavio)}
.calc-l{display:block;height:100%;background:var(--lula);margin-left:auto}
.calc-50{position:absolute;left:50%;top:-4px;bottom:-4px;border-left:2px dashed var(--ink)}
#calc-txt{font-size:1.02rem;margin:4px 0 0}
.repro{font-family:var(--mono);font-size:.84rem;background:var(--paper2);border:1px solid var(--line);border-radius:6px;padding:14px 16px;line-height:2}
ul.fontes{max-width:92ch;padding-left:20px}
ul.fontes li{margin:0 0 6px;font-size:.92rem}
footer{padding:36px 0 64px;color:var(--muted);font-size:.93rem}
@media (width <= 860px){
 .mapa-grid,.grid2,.grid3{grid-template-columns:1fr}
}
@media (width <= 720px){
 body{font-size:16.5px}
 section{padding:40px 0}
 .hero-stats b{font-size:1.85rem}
 .fig{overflow-x:auto;padding:12px}
 .fig .fig-svg{min-width:680px}
 #fig-mapa_reserva .fig-svg{min-width:0}
 .fig::after{content:"arraste para o lado para ver o gráfico inteiro";display:block;font-family:var(--mono);font-size:.7rem;color:var(--muted);margin-top:6px}
 #fig-mapa_reserva::after{content:none}
 th,td{padding:8px 10px}
}
"""

JS = """
(function(){
  var dadosEl=document.getElementById('calc-dados');
  var calc=document.getElementById('calc');
  if(dadosEl&&calc){
    var dados=JSON.parse(dadosEl.textContent);
    var lam=document.getElementById('calc-lam'),out=document.getElementById('calc-lam-out');
    var f=document.getElementById('calc-f'),l=document.getElementById('calc-l'),txt=document.getElementById('calc-txt');
    function br(x){return x.toFixed(1).replace('.',',')}
    function atualiza(){
      var modo=document.querySelector('input[name=calc-lula]:checked').value;
      var i=Math.round(Number(lam.value)/5),p=dados[modo][i];
      out.textContent=lam.value+'%';
      f.style.width=p[1]+'%';l.style.width=p[2]+'%';
      var m=p[1]-p[2],frase;
      if(p[1]>50){frase='Flávio passa de 50% dos válidos: a eleição acabaria no 1º turno.';}
      else if(p[2]>50){frase='Lula passa de 50% dos válidos: a eleição acabaria no 1º turno.';}
      else if(m>0){frase='Flávio termina o 1º turno na frente, por '+br(m)+' pontos.';}
      else{frase='Lula termina o 1º turno na frente, por '+br(-m)+' pontos.';}
      txt.innerHTML='<b>Flávio '+br(p[1])+'%</b> × <b>Lula '+br(p[2])+'%</b> dos votos válidos. '+frase;
    }
    lam.addEventListener('input',atualiza);
    document.querySelectorAll('input[name=calc-lula]').forEach(function(r){r.addEventListener('change',atualiza)});
    calc.hidden=false;atualiza();
  }
  var sel=document.getElementById('sel-uf');
  if(sel){
    sel.parentNode.hidden=false;
    sel.addEventListener('change',function(){
      var el=document.getElementById(sel.value);
      if(el){el.open=true;el.scrollIntoView({block:'start'});}
    });
  }
})();
"""


def main() -> None:
    corpo = "".join(
        [
            CAP.cap_tese(),
            CAP.cap_fenomeno(),
            CAP.cap_matematica(),
            CAP.cap_mapa(),
            CAP.cap_nacional(),
            CAP.cap_reencontro(),
            CAP.cap_terceira(),
            CAP.cap_governadores(),
            CAP.cap_senado(),
            CAP.cap_provavel(),
            CAP.cap_resiliente(),
            CAP.cap_modelo(),
            CAMP.cap_argumentos(),
            CAMP.cap_estados(),
            CAMP.cap_kit(),
            CAP.cap_municipios(),
            CAMP.cap_lei(),
            CAP.cap_limites(),
            CAP.cap_fontes(),
        ]
    )
    links = "".join(f'<a href="#{slug}">{CAP.esc(nome)}</a>' for slug, nome in SECOES)
    f = CAP.F
    n_quaest = len(CAP.EST)
    n_rt = len(CAP.D["realtime"])
    n_atlas = len(CAP.D.get("atlas", {}))
    n_nac = len({o["instituto"] for o in CAP.D["nacional"]["ondas"]})
    rel_txt = (
        f"{n_quaest} relatórios estaduais da Quaest, {n_rt} da Real Time Big Data"
        + (f" e {n_atlas} da AtlasIntel" if n_atlas else "")
    )
    rel_curto = f"{n_quaest} Quaest, {n_rt} Real Time" + (
        f" e {n_atlas} Atlas" if n_atlas else ""
    )
    titulo = "O mapa do voto útil: onde estão os votos que decidem o 1º turno | Arvor"
    descricao = (
        f"{CAP.fmt(f['reserva_total'] / 1e6, 1)} milhões de eleitores já votam em Flávio no 2º turno e ainda não no 1º. "
        "Estado por estado: terceira via, governadores, Senado, comparecimento, argumentos e o modelo de cenário do voto útil."
    )
    pagina = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{CAP.esc(titulo)}</title>
<meta name="description" content="{CAP.esc(descricao)}">
<link rel="canonical" href="https://brasil.arvor.co/mapa_do_voto_util.html">
<link rel="icon" href="favicon.ico" sizes="any">
<link rel="icon" href="img/favicon.svg" type="image/svg+xml">
<meta name="theme-color" content="#0d2238">
<meta property="og:type" content="article">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="Arvor Intelligence">
<meta property="og:title" content="O mapa do voto útil no 1º turno">
<meta property="og:description" content="{CAP.esc(descricao)}">
<meta property="og:url" content="https://brasil.arvor.co/mapa_do_voto_util.html">
<meta property="og:image" content="https://brasil.arvor.co/img/og/mapa_do_voto_util.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@leonardodias">
<meta name="twitter:image" content="https://brasil.arvor.co/img/og/mapa_do_voto_util.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,500;0,9..144,700;0,9..144,900;1,9..144,500&amp;family=IBM+Plex+Mono:wght@400;500;700&amp;family=IBM+Plex+Sans+Condensed:wght@400;600;700&amp;display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<a class="skip" href="#conteudo">Pular para o conteúdo</a>
<header class="hero"><div class="wrap">
<div class="brand"><a href="index.html"><img src="img/arvor_logo.png" alt="">Arvor Intelligence · Perícia eleitoral</a></div>
<p class="eyebrow">Mapa do voto útil · 1º turno de 4 de outubro · dados até 25/09/2026</p>
<h1>O voto útil já começou.<em>Falta chegar a {CAP.fmt(f["reserva_total"] / 1e6, 1)} milhões de eleitores.</em></h1>
<p class="deck">A terceira via está secando e sete de cada dez pontos que ela perde vão para Flávio Bolsonaro. Este mapa lê {rel_txt}, estado por estado, para dizer onde está quem já escolheu Flávio no 2º turno e ainda não no 1º, quem vota em governador e senador de direita e ainda não fechou o presidente, e o que dizer a cada um. No fim, o modelo de cenário responde à pergunta que importa: se der certo, quanto Flávio teria dos votos válidos.</p>
{CAP.hero_stats()}
<dl class="case-file">
<div><dt>Relatórios estaduais</dt><dd>{rel_curto}</dd></div>
<div><dt>Onda mais recente</dt><dd>Quaest, 19 a 24/09</dd></div>
<div><dt>Pesquisas nacionais</dt><dd>{n_nac} institutos registrados</dd></div>
<div><dt>Base eleitoral</dt><dd>TSE 2022 e eleitorado 2026</dd></div>
<div><dt>Natureza</dt><dd>Análise e cenário, não pesquisa</dd></div>
<div><dt>Lado</dt><dd>Declarado: voto útil em Flávio</dd></div>
</dl>
</div></header>
<nav class="toc" aria-label="Capítulos"><div class="wrap"><b>NO MAPA</b>{links}</div></nav>
<main id="conteudo">{corpo}</main>
<footer><div class="wrap">
<p><strong>Arvor Intelligence</strong> · Análise de pesquisas registradas no TSE e de resultado eleitoral oficial. Não é pesquisa eleitoral e não é previsão: o modelo é cenário condicional com hipóteses declaradas. O capítulo de campanha é juízo editorial.</p>
<p><a href="index.html">Biblioteca</a> · <a href="reponderacao_pnad.html">Agregador PNAD</a> · <a href="estaduais_092026.html">Atlas estadual</a> · <a href="#conteudo">Voltar ao início</a></p>
</div></footer>
<script>{JS}</script>
</body>
</html>
"""
    if "—" in pagina:
        raise SystemExit("travessão proibido na página")
    SAIDA.write_text(pagina, encoding="utf-8")
    print("Gerado:", SAIDA, f"{len(pagina) / 1024:.0f} KB", len(SECOES), "capítulos")


if __name__ == "__main__":
    main()
