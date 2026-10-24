"""Folha de estilo e script do relatório. O build grava os dois em docs/assets."""

from mudancas_secoes_2t.pagina.estilo import CSS as BASE

EXTRA = r"""
[hidden]{display:none!important}
#controles-horarios{margin:26px 0}#fuso-horario{font:inherit;max-width:100%;padding:10px;border:1px solid #80958c;background:#fffdf8;color:#192e2b}
.botoes-periodos{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0}
.botoes-periodos button{font:inherit;color:#192e2b;background:#f4f0e5;border:1px solid #a6b1a5;padding:12px 18px;text-align:left;cursor:pointer}
.botoes-periodos button[aria-pressed=true]{background:#193c35;color:#fffdf8;border-color:#193c35}
.botoes-periodos small{display:block;margin-top:5px;font-family:monospace}
.botoes-periodos button:focus-visible,#fuso-horario:focus-visible{outline:3px solid #ba7b37;outline-offset:3px}
.numero-chuva{font-size:64px!important;line-height:1.1!important;margin:12px 0!important;color:#193c35}.numero-chuva small{font-size:28px}
.leitura-periodo{padding:12px 20px}.painel-periodo h3{margin-top:24px}
@media print{.painel-periodo[hidden]{display:block!important}#controles-horarios{display:none!important}}
.regressao-clima{margin:24px 0}.regressao-clima img{width:100%;height:auto;display:block}.regressao-clima figcaption{font-size:16px;margin-top:12px}
.rotulo{font-size:19px;max-width:880px;border-left:4px solid var(--dourado);padding:4px 0 4px 14px;margin:20px 0}
.tag.fato{background:#e3e9df}
tr.extra{display:none}tr.extra.mostra{display:table-row}
.chapter-nav a:focus-visible{outline-offset:1px}
.mapas-comparados{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin:24px 0}
.mapas-comparados figure{margin:0;padding:18px;background:var(--painel,#fffdf8);border:1px solid #d3d1c6;min-width:0}
.mapas-comparados h3{margin:0 0 12px;font-size:22px}
.mapas-comparados svg{display:block;width:100%;height:auto}
.mapas-comparados figcaption{font-size:16px;line-height:1.5;margin-top:12px;color:#535b54}
.mapas-comparados .tm{font-size:15px;fill:#192e2b}
@media(max-width:760px){.mapas-comparados{grid-template-columns:1fr}.mapas-comparados figure{padding:12px}}
@media(max-width:860px){.chapter-nav{gap:16px}.table-scroll{margin-left:-4px;margin-right:-4px}}
"""

CSS = BASE.replace("@media print", EXTRA + "@media print", 1)

JS = r"""(function(){
'use strict';
document.documentElement.classList.add('js');
function numero(t){var s=String(t).replace(/\./g,'').replace(',','.').replace(/[^0-9.\-−]/g,'').replace(/−/g,'-');var n=parseFloat(s);return isNaN(n)?-Infinity:n}
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
  var sel=document.getElementById('filtro-uf'),out=document.getElementById('filtro-n');
  if(!sel)return;
  sel.closest('.js-only').hidden=false;
  var linhas=document.querySelectorAll('#curiosos tr[data-uf],#tabela-uf tr[data-uf],#tabela-cidades tr[data-uf]');
  var aplicar=function(){
    var v=sel.value,n=0;
    Array.prototype.forEach.call(linhas,function(r){
      var extra=r.classList.contains('extra'),ok=!v||r.getAttribute('data-uf')===v;
      r.hidden=!ok;
      if(extra){r.classList.toggle('mostra',!!v&&ok)}
      if(ok&&(!extra||v))n++;
    });
    if(out)out.textContent=v?n+' linhas de '+v:'';
    try{history.replaceState(null,'',v?'#uf='+v:location.pathname+location.search)}catch(e){}
  };
  sel.addEventListener('change',aplicar);
  var m=/#uf=([A-Z]{2})/.exec(location.hash);
  if(m){sel.value=m[1];if(sel.value!==m[1])sel.value=''}
  aplicar();
}
document.querySelectorAll('table[data-sortable]').forEach(ordenar);
filtrar();
var controles=document.getElementById('controles-horarios');
if(controles){
  controles.hidden=false;
  var botoes=controles.querySelectorAll('[data-periodo]');
  function periodo(chave){
    document.querySelectorAll('.painel-periodo').forEach(function(p){p.hidden=p.id!=='periodo-'+chave});
    botoes.forEach(function(b){b.setAttribute('aria-pressed',String(b.dataset.periodo===chave))});
  }
  botoes.forEach(function(b){b.addEventListener('click',function(){periodo(b.dataset.periodo)})});
  periodo('votacao');
  document.getElementById('fuso-horario').addEventListener('change',function(){
    var delta=Number(this.value)+3;
    document.querySelectorAll('.hora-local').forEach(function(el){
      el.textContent=String(Number(el.dataset.inicio)+delta).padStart(2,'0')+'h–'+String(Number(el.dataset.fim)+delta).padStart(2,'0')+'h';
    });
  });
}
})();
"""
