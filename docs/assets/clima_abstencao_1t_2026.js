(function(){
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
