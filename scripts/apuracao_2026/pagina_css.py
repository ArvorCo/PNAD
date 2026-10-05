"""Folha de estilo e script mínimo do dossiê da apuração (papel, tinta, três fontes)."""

FONTES = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700;800'
    "&family=Fraunces:ital,opsz,wght@0,9..144,500;0,9..144,700;1,9..144,500"
    '&family=IBM+Plex+Mono:wght@400;600&display=swap" rel="stylesheet">'
)

CSS = """
:root{--paper:#f4f0e6;--ink:#192e2b;--muted:#535b54;--line:#cbc5b5;--card:#ebe5d6;
--red:#b02f21;--blue:#1457aa;--teal:#0b6650;--gold:#7d5b00;
--sans:Archivo,Helvetica,Arial,sans-serif;--display:Fraunces,Georgia,serif;
--mono:"IBM Plex Mono",ui-monospace,monospace;--nav-h:52px}
*{box-sizing:border-box}
html{scroll-behavior:smooth;scroll-padding-top:calc(var(--nav-h) + 16px)}
body{margin:0;background:var(--paper);color:var(--ink);font:18px/1.62 var(--sans)}
a{color:var(--blue);text-underline-offset:3px}a:hover{color:var(--red)}
.wrap{width:min(1160px,calc(100% - 48px));margin:auto}
.skip{position:absolute;left:16px;top:-120px;background:var(--paper);color:var(--ink);padding:10px;z-index:30}
.skip:focus{top:10px}
.hero{border-top:8px solid var(--ink);padding:26px 0 42px;background:var(--paper)}
.masthead{display:flex;justify-content:space-between;gap:20px;border-bottom:1px solid var(--ink);
padding-bottom:16px;font:600 12px var(--sans);letter-spacing:.12em;text-transform:uppercase}
.masthead a{color:var(--ink);text-decoration:none;font-weight:800}
.kicker{font:700 12px/1.6 var(--sans);letter-spacing:.13em;color:var(--gold);margin:36px 0 18px;text-transform:uppercase}
h1{font:500 clamp(46px,7vw,96px)/1.02 var(--display);letter-spacing:-.035em;margin:24px 0 26px;max-width:980px}
h1 em{color:var(--blue);font-style:italic}
.deck{font-size:23px;line-height:1.5;max-width:860px}
.score-grid{display:grid;grid-template-columns:1.2fr 1fr 1fr;gap:28px;margin:34px 0 18px;padding:26px 0;border-block:2px solid var(--ink)}
.score-grid>div+div{border-left:1px solid var(--line);padding-left:28px}
.score-grid span{display:block;font:700 12px/1.5 var(--sans);letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.score-grid b{display:block;font:500 clamp(36px,4.6vw,60px)/1.25 var(--display);white-space:nowrap}
.score-grid i{font-style:normal}.score-grid small{font-size:24px;color:var(--muted)}
.score-grid p{font:14px/1.5 var(--sans);margin:4px 0}
.lula{color:var(--red)}.flavio{color:var(--blue)}
.boundary{font:600 14px/1.7 var(--sans);max-width:860px}
.meta{font:13px/1.7 var(--sans);color:var(--muted)}
nav.cap{position:sticky;top:0;z-index:10;background:var(--paper);border-bottom:1px solid var(--line)}
nav.cap .wrap{display:flex;gap:18px;overflow-x:auto;padding:14px 0;white-space:nowrap;scrollbar-width:thin}
nav.cap a{font:600 13px var(--sans);text-decoration:none;color:var(--ink);padding:2px 0;border-bottom:2px solid transparent}
nav.cap a[aria-current="true"]{border-bottom-color:var(--red)}
nav.cap a span{color:var(--muted);font-weight:500;margin-right:4px}
section{padding:68px 0;border-bottom:1px solid var(--line)}
.section-head{max-width:900px}
.section-head .kicker{margin:0 0 18px;color:var(--red)}
h2{font:500 clamp(31px,4.3vw,54px)/1.12 var(--display);letter-spacing:-.022em;margin:0 0 24px}
h2 em{color:var(--blue)}
h3{font:700 21px/1.35 var(--sans);margin:40px 0 10px}
.lead{font-size:22px;line-height:1.5}
p,ul,ol{max-width:900px}
li{margin-bottom:8px}
strong{font-weight:700}
.selo{display:inline-block;font:700 11px/1 var(--sans);letter-spacing:.06em;text-transform:uppercase;
padding:5px 7px 4px;border-radius:3px;color:#fff;vertical-align:2px;margin-right:4px}
.selo-verificado{background:var(--teal)}.selo-inferencia{background:var(--blue)}
.selo-hipotese{background:var(--gold)}.selo-juizo{background:var(--ink)}.selo-relato{background:var(--muted)}
figure{margin:34px 0;border:1px solid var(--line);padding:16px;background:var(--paper)}
.chart-scroll{overflow-x:auto}
.chart-scroll svg{display:block;width:100%;min-width:760px;height:auto}
.chart-fit svg{display:block;width:100%;max-width:760px;height:auto;margin:auto}
figcaption{font:13.5px/1.6 var(--sans);color:var(--muted);padding:12px 4px 2px;max-width:1000px}
.fig-estreita{display:none}
.fig-larga svg,.fig-estreita svg{display:block;width:100%;height:auto}
.mapas{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.mapas svg{display:block;width:100%;height:auto}
.duas{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px;align-items:start}
.duas>figure{margin:20px 0}
.legenda-mapa{list-style:none;display:flex;flex-wrap:wrap;gap:6px 16px;padding:0;margin:10px 0 0;font:13px var(--sans)}
.legenda-mapa li{margin:0;display:flex;align-items:center;gap:6px}
.legenda-mapa .sw{display:inline-block;width:14px;height:14px;border:1px solid #9a9c94}
.table-scroll{overflow-x:auto;margin:24px 0;border-top:2px solid var(--ink)}
table{border-collapse:collapse;width:100%;font:14px/1.5 var(--sans);min-width:560px}
caption{caption-side:top;text-align:left;font:13px var(--sans);color:var(--muted);padding:8px 0}
td,th{padding:10px 11px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th.num,td.num{text-align:right;font-variant-numeric:tabular-nums;font-family:var(--mono);font-size:13px;white-space:nowrap}
thead th{color:var(--muted);font-weight:600;font-size:12px}
tbody th{font-weight:600}
tbody tr:hover{background:#ebe4d4}
aside{padding:22px 26px;margin:28px 0;background:var(--card);border-left:4px solid var(--gold);max-width:960px}
aside b{display:block;margin-bottom:4px}
aside.juizo{border-left-color:var(--ink)}
details{border:1px solid var(--line);padding:12px 18px;margin:14px 0;max-width:1000px}
summary{cursor:pointer;font:600 15px var(--sans);padding:6px 0}
.finding-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:22px;border-block:2px solid var(--ink);padding:24px 0;margin:30px 0}
.finding-grid b{display:block;font:500 clamp(30px,3.6vw,46px)/1.15 var(--display);color:var(--ink)}
.finding-grid span{display:block;font:14px/1.5 var(--sans);color:var(--muted)}
.camadas{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px;margin:28px 0}
.camadas>div{background:var(--card);padding:18px 20px;border-top:4px solid var(--ink)}
.camadas h4{margin:0 0 8px;font:700 15px var(--sans);letter-spacing:.02em}
.camadas p{font-size:15.5px;margin:8px 0}
blockquote{margin:20px 0;padding:6px 0 6px 20px;border-left:3px solid var(--red);font:500 20px/1.5 var(--display);max-width:820px}
blockquote cite{display:block;font:13px var(--sans);color:var(--muted);font-style:normal;margin-top:6px}
.galeria{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}
.galeria figure{margin:0}
figure img{display:block;max-width:100%;height:auto}
.galeria img{display:block;width:100%;height:auto;border:1px solid var(--line)}
.pendente{border:2px dashed var(--gold);background:#efe8d4;padding:40px 28px;margin:40px 0}
.pendente-bloco{border:2px dashed var(--gold);background:#efe8d4;padding:18px 22px;margin:24px 0;font:600 15px var(--sans)}
code,.hash{font:12.5px/1.7 var(--mono);overflow-wrap:anywhere}
pre{padding:18px;background:var(--card);overflow-x:auto;font:13px/1.7 var(--mono)}
.fontes li{font-size:15px}
footer{padding:36px 0 60px;font:14px var(--sans);color:var(--muted)}
a:focus-visible,summary:focus-visible,.table-scroll:focus-visible,.chart-scroll:focus-visible,.chart-fit:focus-visible{outline:3px solid var(--gold);outline-offset:3px}
.js figure.reveal{opacity:0;transform:translateY(14px);transition:opacity .5s ease,transform .5s ease}
.js figure.reveal.in{opacity:1;transform:none}
@media(max-width:719px){
.fig-larga{display:none}.fig-estreita{display:block}
.wrap{width:calc(100% - 32px)}
body{font-size:17px}
.masthead{display:block}.masthead span{display:block;margin-top:8px}
.score-grid{grid-template-columns:1fr;gap:18px}
.score-grid>div+div{border-left:0;border-top:1px solid var(--line);padding:18px 0 0}
.score-grid b{font-size:42px}
.deck,.lead{font-size:19px}
h2{font-size:32px}
section{padding:46px 0}
figure{padding:8px;margin:24px 0}
.mapas,.duas,.galeria,.camadas{grid-template-columns:1fr}
.finding-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
aside{padding:16px 18px}
td,th{padding:8px}
}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}.js figure.reveal{opacity:1;transform:none;transition:none}}
@media print{nav.cap,.skip{display:none}.js figure.reveal{opacity:1;transform:none}.chart-scroll svg{min-width:0}details{break-inside:avoid}}
"""

JS_HEAD = "<script>document.documentElement.classList.add('js')</script>"

JS = """
(function(){
  var figs=document.querySelectorAll('figure.reveal');
  var tudo=function(){figs.forEach(function(f){f.classList.add('in')});};
  if(!('IntersectionObserver' in window)||navigator.webdriver){tudo();}
  else{
    var io=new IntersectionObserver(function(es){es.forEach(function(e){
      if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target);}});},
      {rootMargin:'0px 0px -8% 0px'});
    figs.forEach(function(f){io.observe(f)});
    window.addEventListener('beforeprint',tudo);
  }
  var nav=document.querySelector('nav.cap');
  if(nav){document.documentElement.style.setProperty('--nav-h',nav.offsetHeight+'px');}
  var links={};document.querySelectorAll('nav.cap a').forEach(function(a){links[a.getAttribute('href').slice(1)]=a;});
  if('IntersectionObserver' in window){
    var atual=null;
    var ob=new IntersectionObserver(function(es){es.forEach(function(e){
      if(e.isIntersecting&&links[e.target.id]){
        if(atual){atual.removeAttribute('aria-current');}
        atual=links[e.target.id];atual.setAttribute('aria-current','true');
        var faixa=atual.closest('nav');
        if(faixa){faixa.scrollTo({left:atual.offsetLeft-faixa.clientWidth/2+atual.offsetWidth/2,behavior:'smooth'});}
      }});},{rootMargin:'-40% 0px -55% 0px'});
    document.querySelectorAll('main section[id]').forEach(function(s){ob.observe(s)});
  }
})();
"""
