"""Folha de estilo e script do laudo. O build grava os dois em docs/assets."""

CSS = r""":root{color-scheme:light;--papel:#f4f0e6;--painel:#fffdf8;--tinta:#192e2b;--cinza:#535b54;--linha:#d3d1c6;--flavio:#1457aa;--lula:#b02f21;--terceira:#0f7f5f;--dourado:#7d5b00;--verde:#0c7a72;--serif:'Fraunces',Georgia,'Times New Roman',serif;--sans:'IBM Plex Sans Condensed','Arial Narrow',system-ui,sans-serif;--mono:'IBM Plex Mono',ui-monospace,Menlo,monospace;--wrap:1120px}
*{box-sizing:border-box}html{scroll-padding-top:16px;-webkit-text-size-adjust:100%}body{margin:0;background:var(--papel);color:var(--tinta);font-family:var(--sans);font-size:18px;line-height:1.6}
a{color:var(--tinta);text-underline-offset:3px}a:hover{color:var(--verde)}:focus-visible{outline:3px solid var(--flavio);outline-offset:3px}[hidden]{display:none!important}
.skip{position:absolute;left:8px;top:-60px;background:var(--painel);padding:10px 14px;z-index:10}.skip:focus{top:8px}
.masthead{max-width:var(--wrap);margin:auto;display:flex;gap:16px;justify-content:space-between;align-items:center;padding:20px 16px;border-bottom:1px solid var(--linha);font-size:13px;letter-spacing:.1em;text-transform:uppercase}
.masthead a{text-decoration:none;font-weight:600}main{max-width:var(--wrap);margin:auto;padding:0 16px}
h1,h2,h3{font-family:var(--serif);font-weight:500;line-height:1.1;letter-spacing:-.02em}h1{font-size:clamp(38px,6vw,70px);margin:0 0 24px}h2{font-size:clamp(30px,4vw,46px);margin:0 0 14px}h3{font-size:25px;margin:34px 0 12px}
h1 em,h2 em{font-style:italic;font-weight:400;color:var(--verde)}
.hero{display:grid;grid-template-columns:minmax(0,1.7fr) minmax(0,1fr);gap:48px;padding:56px 0 40px}.eyebrow{font-size:13px;letter-spacing:.14em;text-transform:uppercase;font-weight:600;margin:0 0 18px}
.deck{font-size:21px;line-height:1.55;max-width:720px}.chips{display:flex;flex-wrap:wrap;gap:10px;margin-top:22px}.chips span{border:1px solid var(--tinta);padding:5px 12px;font-size:15px;font-weight:500;background:var(--painel)}
.placar{align-self:start;background:var(--tinta);color:var(--papel);padding:30px 28px;border-top:5px solid var(--dourado)}.placar .eyebrow{color:#d6dfd3}.placar b{display:block;font-family:var(--serif);font-weight:500;font-size:clamp(40px,5vw,60px);line-height:1.1;margin:6px 0 4px}.placar small{display:block;font-size:14px;color:#d6dfd3;line-height:1.45}.placar hr{border:0;border-top:1px solid #4d6660;margin:20px 0}
.chapter-nav{display:flex;gap:22px;overflow-x:auto;white-space:nowrap;padding:14px 0;border-top:2px solid var(--tinta);border-bottom:1px solid var(--linha);font-size:14px;letter-spacing:.06em;text-transform:uppercase}.chapter-nav a{text-decoration:none;padding:4px 0}
.guia{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:26px;padding:34px 0}.guia article{border-left:3px solid var(--verde);padding-left:16px}.guia h3{font-size:22px;margin:6px 0 8px}.guia p{margin:0;font-size:16px}.guia a{text-decoration:none}.guia span{font-size:13px;color:var(--cinza);letter-spacing:.08em;text-transform:uppercase}
.chapter{padding:56px 0;border-top:1px solid var(--linha)}.section-heading{display:flex;gap:22px;margin-bottom:26px}.section-number{flex:none;width:44px;border-top:3px solid var(--verde);padding-top:10px;font-size:15px;font-weight:600}
.lead{font-size:21px;line-height:1.5;max-width:860px;margin:0}.chapter>p,.chapter>ul{max-width:880px}
.stats{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px;margin:26px 0}.stats>div{border-top:3px solid var(--verde);padding-top:12px}.stats b{display:block;font-family:var(--serif);font-weight:500;font-size:clamp(26px,3.4vw,36px);line-height:1.15}.stats span{display:block;font-size:15px;color:var(--cinza);line-height:1.4;margin-top:6px}
.chart{margin:24px 0;padding:16px;background:var(--painel);border:1px solid var(--linha)}.chart-scroll{overflow-x:auto;max-width:100%}.chart svg{display:block;width:100%;height:auto;font-family:var(--sans)}.tx{fill:#192e2b;font-size:14px}.tm{fill:#535b54;font-size:13px}.figcap{font-size:14px;color:var(--cinza);margin:10px 0 0}
.table-scroll{overflow-x:auto;max-width:100%;margin:22px 0;border:1px solid var(--linha);background:var(--painel)}table{border-collapse:collapse;width:100%;font-size:15px}th,td{padding:9px 12px;border-bottom:1px solid var(--linha);text-align:left;vertical-align:top;font-variant-numeric:tabular-nums}th{background:#e8e6dc;font-weight:600;font-size:14px;white-space:nowrap}th button{font:inherit;color:inherit;background:none;border:0;padding:0;cursor:pointer;text-align:left}th[aria-sort=ascending] button::after{content:' \25B2';font-size:11px}th[aria-sort=descending] button::after{content:' \25BC';font-size:11px}td.num,th.num{text-align:right}td small{display:block;color:var(--cinza);font-size:13px;line-height:1.35}tbody tr:hover{background:#f1efe5}
.note{font-size:15px;color:var(--cinza);max-width:880px}.limite{font-size:16px;border-left:3px solid var(--cinza);padding:2px 0 2px 14px;max-width:880px;margin:22px 0}
.callout{padding:20px 24px;background:#e3e9df;border-left:4px solid var(--verde);margin:26px 0;max-width:880px}.callout>b{font-size:19px}.callout p{margin:8px 0 0;font-size:17px}.callout.contra{background:#efe6cf;border-left-color:var(--dourado)}.callout.contra>b::before{content:'Contraponto. ';font-weight:600}
details{border-top:1px solid var(--linha);border-bottom:1px solid var(--linha);margin:24px 0;padding:0 2px}summary{cursor:pointer;padding:15px 0;font-weight:600;font-size:17px}
code{font-family:var(--mono);font-size:12px;overflow-wrap:anywhere}pre{overflow-x:auto;background:var(--painel);border:1px solid var(--linha);padding:14px}pre code{font-size:13px;overflow-wrap:normal}.hash{display:block;max-width:340px}
.tag{display:inline-block;font-size:12px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;padding:2px 8px;margin-right:6px;border:1px solid var(--tinta);background:var(--painel)}.tag.inf{background:#e8e6dc}.tag.juizo{background:#efe6cf}.tag.nao{background:#f3dfdb}
.veredito{padding-left:0;list-style:none}.veredito li{padding:12px 0;border-bottom:1px solid var(--linha)}
.downloads{display:flex;flex-wrap:wrap;gap:12px;margin:22px 0}.botao{display:inline-block;padding:12px 18px;border:2px solid var(--tinta);text-decoration:none;font-weight:600;background:var(--painel)}.botao:hover{background:var(--tinta);color:var(--papel)}
.filtro{display:flex;flex-wrap:wrap;align-items:center;gap:12px;margin:18px 0}.filtro select{min-height:44px;font:inherit;padding:6px 10px;background:var(--painel);border:1px solid var(--tinta)}.filtro output{font-size:15px;color:var(--cinza)}
footer{max-width:var(--wrap);margin:40px auto 0;padding:24px 16px 48px;border-top:1px solid var(--tinta);font-size:15px;display:flex;flex-wrap:wrap;gap:12px 28px}footer p{margin:0;max-width:640px}
@media(max-width:860px){.hero{grid-template-columns:minmax(0,1fr);gap:28px;padding:36px 0 28px}.guia,.stats{grid-template-columns:minmax(0,1fr)}.section-heading{gap:14px}.chapter{padding:40px 0}body{font-size:17px}.lead{font-size:19px}}
@media print{.chapter-nav,.filtro,.skip{display:none}details{display:block}details>*{display:block}body{background:#fff}}
"""

JS = r"""(function(){
'use strict';
function numero(t){var s=String(t).replace(/\./g,'').replace(',','.').replace(/[^0-9.\-]/g,'');var n=parseFloat(s);return isNaN(n)?-Infinity:n}
function ordenar(t){
  var cab=t.tHead.rows[0].cells;
  Array.prototype.forEach.call(cab,function(th,i){
    th.setAttribute('aria-sort','none');
    var b=document.createElement('button');b.type='button';b.innerHTML=th.innerHTML;th.innerHTML='';th.appendChild(b);
    b.addEventListener('click',function(){
      var asc=th.getAttribute('aria-sort')!=='ascending';
      Array.prototype.forEach.call(cab,function(o){o.setAttribute('aria-sort','none')});
      th.setAttribute('aria-sort',asc?'ascending':'descending');
      var num=th.getAttribute('data-sort')==='num';
      var linhas=Array.prototype.slice.call(t.tBodies[0].rows);
      var chave=function(r){var c=r.cells[i];var v=c.getAttribute('data-v');v=(v===null||v==='')?c.textContent:v;return num?numero(v):v.toLowerCase()};
      linhas.map(function(r,k){return {r:r,k:k,v:chave(r)}}).sort(function(a,b){
        var d=a.v<b.v?-1:a.v>b.v?1:0;return (asc?d:-d)||(a.k-b.k)
      }).forEach(function(o){t.tBodies[0].appendChild(o.r)});
    });
  });
}
function filtrar(){
  var sel=document.getElementById('filtro-uf'),t=document.getElementById('tabela-locais'),out=document.getElementById('filtro-n');
  if(!sel||!t)return;
  sel.closest('.js-only').hidden=false;
  var aplicar=function(){
    var v=sel.value,n=0,tot=t.tBodies[0].rows.length;
    Array.prototype.forEach.call(t.tBodies[0].rows,function(r){var ok=!v||r.getAttribute('data-uf')===v;r.hidden=!ok;if(ok)n++});
    if(out)out.textContent=n+' de '+tot+' pares de local';
    try{history.replaceState(null,'',v?'#uf='+v:location.pathname+location.search)}catch(e){}
  };
  sel.addEventListener('change',aplicar);
  var m=/#uf=([A-Z]{2})/.exec(location.hash);
  if(m){sel.value=m[1];if(sel.value!==m[1])sel.value=''}
  aplicar();
}
document.querySelectorAll('table[data-sortable]').forEach(ordenar);
filtrar();
})();
"""
