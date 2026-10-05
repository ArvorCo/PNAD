"""Camada interativa das figuras do dossiê: ficha, realce, alternâncias, abas e filtro.

Um bloco `<style>` e um `<script>`, emitidos uma vez por `interativo_html()`.
Cada `figure[data-fig]` lê as próprias fichas em `script.tips` (HTML por chave
ou tabela compacta `_rows`), põe a ficha dentro da caixa da figura (nunca fora
dela, virando para a esquerda perto da borda direita) e realça o elemento com
contorno lima. Toque mostra, toque fora esconde. Botões `data-alt` trocam a série
(elementos `data-alt-show`, preenchimentos `data-af` e traços `data-as`) sem recarregar; botões
`data-filtro` apagam os grupos `data-g` de outra região. Sem JavaScript, cada
figura continua inteira na alternância padrão. Funciona em `file://`.
"""

from __future__ import annotations

CSS = """
.fig-i{position:relative}
.fig-i .chart-scroll svg{min-width:var(--minw,760px)}
.fig-ctl{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin:0 0 12px}
.fig-ctl .rot{font:600 11.5px/1 var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-right:6px}
.fig-ctl button{font:600 13.5px/1 var(--sans);padding:8px 13px;border:1px solid var(--ink);background:transparent;color:var(--ink);cursor:pointer;border-radius:2px}
.fig-ctl button:hover{background:#e6dfcf}
.fig-ctl button[aria-pressed="true"]{background:var(--ink);color:var(--paper)}
.fig-ctl button:focus-visible{outline:3px solid var(--gold);outline-offset:2px}
.fig-ctl-tab{border-bottom:2px solid var(--ink);gap:0}
.fig-ctl-tab button{border:0;border-radius:0;padding:10px 16px}
html:not(.js) .fig-ctl{display:none}
.fig-i .chart-full svg{display:block;width:100%;height:auto}
.fig-leg{margin:8px 4px 0}.fig-leg .leg-tit{display:block;font:700 13px/1.4 var(--sans);margin-bottom:2px}
.fig-i .hit{cursor:pointer}
.fig-i .hit:focus{outline:none}
.fig-i .hit-cross,.fig-i .hit-halo{opacity:0;pointer-events:none}
.fig-i .hit.on .hit-cross,.fig-i .hit.on .hit-halo{opacity:1}
.fig-i .hit.on>rect:not(.hit-area),.fig-i .hit.on>circle,.fig-i .hit.on>path,.fig-i .hit.on>polygon{stroke:#a4d42b;stroke-width:3px}
.fig-i path.hit.on,.fig-i circle.hit.on,.fig-i rect.hit.on{stroke:#a4d42b;stroke-width:3px}
.fig-i[data-dim].lendo .hit:not(.on){opacity:.5}
.fig-i .apagado{opacity:.06}
.fig-i .near-halo{pointer-events:none}
.fig-tip{position:absolute;z-index:6;left:0;top:0;width:max-content;max-width:min(330px,calc(100% - 12px));
padding:12px 15px;background:#192e2b;color:#f4f0e7;border:1px solid #0f1f1d;
box-shadow:0 10px 28px rgba(15,31,29,.32);font:13.5px/1.5 var(--sans);pointer-events:none;
opacity:0;transition:opacity .12s ease}
.fig-tip.on{opacity:1}
.fig-tip p{margin:0 0 7px;max-width:none}
.fig-tip p:last-child{margin-bottom:0}
.fig-tip .tip-head{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 10px;font-size:15px}
.fig-tip .tip-head b{font-weight:800}
.fig-tip .tip-head span{font:11px/1.4 var(--mono);letter-spacing:.12em;text-transform:uppercase;color:#b9c6bd}
.fig-tip .tip-tab{width:100%;min-width:0;border-collapse:collapse;margin:2px 0 6px;font:12.5px/1.45 var(--mono)}
.fig-tip .tip-tab th,.fig-tip .tip-tab td{padding:2px 0;border:0;text-align:right;font-weight:500;white-space:nowrap;font-size:12.5px;font-family:var(--mono)}
.fig-tip .tip-tab th{text-align:left;color:#b9c6bd;padding-right:14px;white-space:normal}
.fig-tip .tip-tab td{color:#fffdf8}
.fig-tip .tip-nota{font-size:12px;color:#b9c6bd}
.fig-tip:empty{display:none}
.dica{display:inline-flex;align-items:center;gap:7px;margin-left:4px;font:11px/1.4 var(--mono);
letter-spacing:.08em;text-transform:uppercase;color:var(--muted);white-space:nowrap}
.dica::before{content:"";inline-size:8px;block-size:8px;border:2px solid var(--muted);border-radius:50%}
html:not(.js) .dica{display:none}
@media(max-width:719px){.fig-ctl button{padding:8px 10px;font-size:13px}.fig-tip{max-width:calc(100% - 12px)}}
@media print{.fig-ctl,.fig-tip,.dica{display:none}}
"""

JS = r"""
(function(){
var NS='http://www.w3.org/2000/svg';
function q(el,s){return Array.prototype.slice.call(el.querySelectorAll(s));}
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function monta(fig){
  var tips={},rows=null;
  q(fig,'script.tips').forEach(function(n){
    try{var d=JSON.parse(n.textContent);for(var k in d){if(k==='_rows'){rows=d[k];}else{tips[k]=d[k];}}}catch(e){}
  });
  var card=document.createElement('div');
  card.className='fig-tip';card.setAttribute('role','status');card.setAttribute('aria-live','polite');card.hidden=true;
  fig.appendChild(card);
  var atual=null,atualK=null,filtro='',halo=null,svgNear=fig.querySelector('svg[data-near]');
  if(svgNear){halo=svgNear.querySelector('.near-halo');}
  function conteudo(k){
    if(!k)return '';
    if(tips[k])return tips[k];
    if(rows&&k.charAt(0)==='r'){
      var l=rows.linhas[+k.slice(1)];if(!l)return '';
      var h='<p class="tip-head"><b>'+esc(l[0])+'</b>';
      if(rows.sub!=null&&l[rows.sub])h+='<span>'+esc(l[rows.sub])+'</span>';
      h+='</p><table class="tip-tab"><tbody>';
      for(var j=1;j<rows.campos.length;j++){
        if(j===rows.sub||l[j]===''||l[j]==null)continue;
        h+='<tr><th>'+esc(rows.campos[j])+'</th><td>'+esc(l[j])+'</td></tr>';
      }
      h+='</tbody></table>';
      if(rows.nota)h+='<p class="tip-nota">'+esc(rows.nota)+'</p>';
      return h;
    }
    return '';
  }
  function posiciona(px,py,alvo){
    var f=fig.getBoundingClientRect(),cw=card.offsetWidth,ch=card.offsetHeight,x,y;
    if(px==null){var b=alvo.getBoundingClientRect();px=b.left+b.width/2;py=b.top+b.height/2;}
    x=px-f.left+16;
    if(x+cw>f.width-6){x=px-f.left-cw-16;}
    if(x<6){x=Math.max(6,Math.min(f.width-cw-6,px-f.left-cw/2));}
    y=py-f.top-ch-14;
    if(y<6){y=py-f.top+20;}
    y=Math.max(6,Math.min(y,f.height-ch-6));
    card.style.left=Math.round(x)+'px';card.style.top=Math.round(y)+'px';
  }
  function abre(alvo,k,px,py){
    var h=conteudo(k);if(!h){return;}
    if(atual!==alvo||atualK!==k){
      if(atual&&atual!==alvo){atual.classList.remove('on');}
      atual=alvo;atualK=k;
      if(alvo!==halo){alvo.classList.add('on');}
      fig.classList.add('lendo');card.innerHTML=h;card.hidden=false;
    }
    posiciona(px,py,alvo);card.classList.add('on');
  }
  function fecha(){
    if(atual){atual.classList.remove('on');}
    atual=null;atualK=null;fig.classList.remove('lendo');
    card.classList.remove('on');card.hidden=true;
    if(halo){halo.setAttribute('display','none');}
  }
  function perto(ev){
    if(!svgNear||!rows||!rows.xy)return false;
    if(!svgNear.contains(ev.target))return false;
    var m=svgNear.getScreenCTM();if(!m)return false;
    var pt=svgNear.createSVGPoint();pt.x=ev.clientX;pt.y=ev.clientY;
    var p=pt.matrixTransform(m.inverse()),best=-1,bd=196;
    for(var i=0;i<rows.xy.length;i++){
      if(filtro!==''&&rows.g&&String(rows.g[i])!==filtro)continue;
      var dx=rows.xy[i][0]-p.x,dy=rows.xy[i][1]-p.y,dd=dx*dx+dy*dy;
      if(dd<bd){bd=dd;best=i;}
    }
    if(best<0)return false;
    var xy=rows.xy[best];
    halo.setAttribute('cx',xy[0]);halo.setAttribute('cy',xy[1]);
    halo.setAttribute('r',Math.max(6,(xy[2]||4)+3));halo.removeAttribute('display');
    abre(halo,'r'+best,ev.clientX,ev.clientY);
    return true;
  }
  function alvoDe(ev){var n=ev.target;var a=n&&n.closest?n.closest('.hit'):null;return a&&fig.contains(a)?a:null;}
  fig.addEventListener('pointermove',function(ev){
    if(ev.pointerType==='touch')return;
    var a=alvoDe(ev);
    if(a){abre(a,a.getAttribute('data-k'),ev.clientX,ev.clientY);}
    else if(!perto(ev)){fecha();}
  });
  fig.addEventListener('pointerleave',function(ev){if(ev.pointerType!=='touch'){fecha();}});
  document.addEventListener('pointerdown',function(ev){
    if(!fig.contains(ev.target)){fecha();return;}
    var a=alvoDe(ev);
    if(a){abre(a,a.getAttribute('data-k'),ev.clientX,ev.clientY);}
    else if(!perto(ev)){fecha();}
  });
  fig.addEventListener('focusin',function(ev){var a=alvoDe(ev);if(a){abre(a,a.getAttribute('data-k'));}});
  fig.addEventListener('focusout',function(){fecha();});
  fig.addEventListener('keydown',function(ev){if(ev.key==='Escape'){fecha();}});
  function troca(k,b){
    var grupo=b.parentNode;
    q(grupo,'[data-alt]').forEach(function(x){
      var on=x===b?'true':'false';x.setAttribute('aria-pressed',on);
      if(x.getAttribute('role')==='tab'){x.setAttribute('aria-selected',on);}
    });
    q(fig,'[data-alt-show]').forEach(function(e){
      var ok=(' '+e.getAttribute('data-alt-show')+' ').indexOf(' '+k+' ')>=0;
      if(e.namespaceURI===NS){if(ok){e.removeAttribute('display');}else{e.setAttribute('display','none');}}
      else{e.hidden=!ok;}
    });
    q(fig,'[data-af]').forEach(function(e){
      if(!e.hasAttribute('data-f0')){e.setAttribute('data-f0',e.getAttribute('fill')||'');}
      var cor=e.getAttribute('data-f0');
      e.getAttribute('data-af').split('|').forEach(function(par){var p=par.split('>');if(p[0]===k){cor=p[1];}});
      e.setAttribute('fill',cor);
    });
    q(fig,'[data-as]').forEach(function(e){
      if(!e.hasAttribute('data-s0')){e.setAttribute('data-s0',e.getAttribute('stroke')||'');}
      var cor=e.getAttribute('data-s0');
      e.getAttribute('data-as').split('|').forEach(function(par){var p=par.split('>');if(p[0]===k){cor=p[1];}});
      e.setAttribute('stroke',cor);
    });
    fecha();
  }
  q(fig,'button[data-alt]').forEach(function(b){b.addEventListener('click',function(){troca(b.getAttribute('data-alt'),b);});});
  q(fig,'button[data-filtro]').forEach(function(b){b.addEventListener('click',function(){
    filtro=b.getAttribute('data-filtro');
    q(b.parentNode,'[data-filtro]').forEach(function(x){x.setAttribute('aria-pressed',x===b?'true':'false');});
    q(fig,'[data-g]').forEach(function(e){e.classList.toggle('apagado',filtro!==''&&e.getAttribute('data-g')!==filtro);});
    fecha();
  });});
}
q(document,'figure[data-fig]').forEach(monta);
})();
"""


def interativo_html() -> str:
    """`<style>` e `<script>` da camada interativa; emitir uma vez, no fim do `<body>`."""
    return f"<style>{CSS}</style><script>{JS}</script>"
