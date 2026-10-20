"""Folha de estilo e script do relatório. O build grava os dois em docs/assets."""

from mudancas_secoes_2t.pagina.estilo import CSS as BASE

EXTRA = r"""
.rotulo{font-size:19px;max-width:880px;border-left:4px solid var(--dourado);padding:4px 0 4px 14px;margin:20px 0}
.tag.fato{background:#e3e9df}
tr.extra{display:none}tr.extra.mostra{display:table-row}
.chapter-nav a:focus-visible{outline-offset:1px}
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
})();
"""
