(function(){
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
