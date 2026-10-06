"""Mapa navegável do capítulo 13 (onde colocar fiscal): malha, pan, zoom e busca.

Sem biblioteca externa e sem tile de rede. O SVG sai inteiro do Python, na
projeção da casa (`voto_util_mapa`, `MW` × `MH`), com a malha das UFs e um ponto
por local de votação; o JavaScript deste módulo só muda o `viewBox`:

- roda do mouse e pinça aproximam em torno do ponteiro; arrastar move; duplo
  clique centra e aproxima; botões +, − e "Brasil"; teclado (+, −, setas, 0);
- passado `ZOOM_MALHA`, a malha municipal das UFs à vista entra sob demanda, lida
  de um `<script type="application/json" class="fz-mun">` por UF (só as UFs com
  pontos), com coordenadas da mesma projeção multiplicadas por `ESCALA_MALHA` e
  passos relativos inteiros; passado `ZOOM_ROTULO`, os nomes de município;
- traço e ponto com `vector-effect="non-scaling-stroke"`: o ponto tem o mesmo
  tamanho na tela em qualquer zoom;
- clique ou toque num ponto abre o painel do local, abaixo do mapa, com os dois
  links externos (OpenStreetMap e Google Maps, a única coisa que pede rede);
- caixa de busca por município ou local, e lista das UFs que centra o mapa.

Sem script a figura continua inteira: o Brasil com todos os pontos e a ficha
padrão de cada um fica sem pan e zoom, e a lista de locais do capítulo traz os
mesmos endereços e links.
"""

from __future__ import annotations

import json
from functools import cache
from itertools import pairwise

import voto_util_mapa as VM

from .pagina_fig_mapas import MH, MW
from .pagina_mapas import _aneis, _geo_municipal

ESCALA_MALHA = 10
ZOOM_MALHA = 2.5
ZOOM_ROTULO = 7.0
ZOOM_MAX = 40.0


def _proj():
    proj, _ = VM._proj(MW, MH, 10.0)
    return proj


def _caminho_int(aneis, proj, tol: float = 4.0) -> tuple[str, list[float]]:
    """Contorno em inteiros (projeção × `ESCALA_MALHA`), passos relativos, e a caixa."""
    partes = []
    xs: list[float] = []
    ys: list[float] = []
    for anel in aneis:
        pts: list[tuple[int, int]] = []
        for lon, lat in anel:
            x, y = proj(lon, lat)
            p = (round(x * ESCALA_MALHA), round(y * ESCALA_MALHA))
            if pts and abs(p[0] - pts[-1][0]) + abs(p[1] - pts[-1][1]) < tol:
                continue
            pts.append(p)
        if len(pts) < 3:
            continue
        xs += [p[0] for p in pts]
        ys += [p[1] for p in pts]
        passos = " ".join(f"{b[0] - a[0]} {b[1] - a[1]}" for a, b in pairwise(pts))
        partes.append(f"M{pts[0][0]} {pts[0][1]}l{passos}z")
    caixa = [min(xs), min(ys), max(xs), max(ys)] if xs else [0, 0, 0, 0]
    return "".join(partes), caixa


def _centro(aneis, proj) -> tuple[float, float] | None:
    melhor, area_max = None, 0.0
    for anel in aneis:
        a = cx = cy = 0.0
        for (x0, y0), (x1, y1) in zip(anel, anel[1:] + anel[:1], strict=True):
            cr = x0 * y1 - x1 * y0
            a += cr
            cx += (x0 + x1) * cr
            cy += (y0 + y1) * cr
        if a and abs(a) > area_max:
            area_max = abs(a)
            melhor = (cx / (3 * a), cy / (3 * a))
    if melhor is None:
        return None
    x, y = proj(*melhor)
    return round(x, 1), round(y, 1)


@cache
def malha_uf(uf: str) -> dict | None:
    """Malha municipal de uma UF: [código, path, x do rótulo, y do rótulo, área relativa]."""
    geo = _geo_municipal(uf)
    if geo is None:
        return None
    proj = _proj()
    linhas, caixa = [], [1e9, 1e9, -1e9, -1e9]
    for f in geo["features"]:
        aneis = _aneis(f["geometry"])
        d, cx = _caminho_int(aneis, proj)
        if not d:
            continue
        c = _centro(aneis, proj) or ((cx[0] + cx[2]) / 20, (cx[1] + cx[3]) / 20)
        tam = (cx[2] - cx[0]) * (cx[3] - cx[1])
        linhas.append([str(f["properties"]["codarea"]), d, c[0], c[1], tam])
        caixa = [
            min(caixa[0], cx[0]),
            min(caixa[1], cx[1]),
            max(caixa[2], cx[2]),
            max(caixa[3], cx[3]),
        ]
    return {"uf": uf, "caixa": [v / ESCALA_MALHA for v in caixa], "m": linhas}


def blocos_malha(ufs: list[str], nomes: dict[str, str]) -> str:
    """Um `<script type="application/json" class="fz-mun">` por UF com pontos."""
    out = []
    for uf in sorted(set(ufs)):
        m = malha_uf(uf)
        if m is None:
            continue
        dado = dict(
            m,
            m=[[nomes.get(cod, ""), d, x, y, tam] for cod, d, x, y, tam in m["m"] if d],
        )
        texto = json.dumps(dado, ensure_ascii=False, separators=(",", ":"))
        out.append(
            f'<script type="application/json" class="fz-mun" data-uf="{uf}">'
            + texto.replace("</", "<\\/")
            + "</script>"
        )
    return "".join(out)


CSS = """
.fz-ctl{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:0 0 10px}
.fz-ctl input{font:15px/1.3 var(--sans);padding:8px 10px;border:1px solid var(--ink);background:#fffdf8;color:var(--ink);min-width:0;flex:1 1 220px;border-radius:2px}
.fz-ctl input:focus-visible{outline:3px solid var(--gold);outline-offset:1px}
.fz-btn{font:700 15px/1 var(--sans);min-width:40px;padding:9px 12px;border:1px solid var(--ink);background:transparent;color:var(--ink);cursor:pointer;border-radius:2px}
.fz-btn:hover{background:#e6dfcf}.fz-btn:focus-visible{outline:3px solid var(--gold);outline-offset:2px}
.fz-res{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 10px;padding:0;list-style:none}
.fz-res:empty{display:none}
.fz-res button{font:13.5px/1.3 var(--sans);text-align:left;padding:6px 10px;border:1px solid var(--line);background:#fffdf8;color:var(--ink);cursor:pointer;border-radius:2px}
.fz-res button:hover{border-color:var(--ink)}
.fz-quadro{display:grid;grid-template-columns:minmax(0,1fr) 210px;gap:14px;align-items:start}
.fz-mapa{position:relative;border:1px solid var(--line);background:#f8f5ec;overflow:hidden}
.fz-mapa svg{display:block;width:100%;height:auto;touch-action:none;cursor:grab;user-select:none;-webkit-user-select:none}
.fz-mapa svg.arrasta{cursor:grabbing}
.fz-mapa svg.fz-perto .fz-uf{fill:#f4f0e6;stroke-opacity:.45}
.fig-i.arrasta .fig-tip{display:none}
.fz-zoom{position:absolute;right:8px;top:8px;display:flex;flex-direction:column;gap:4px;z-index:3}
.fz-zoom .fz-btn{background:#fffdf8;padding:7px 0;width:40px}
.fz-escala{position:absolute;left:8px;bottom:6px;font:600 12px/1.3 var(--mono);color:var(--muted);background:rgba(248,245,236,.9);padding:2px 6px}
.fz-ufs{max-height:520px;overflow-y:auto;border:1px solid var(--line);padding:6px;margin:0;list-style:none;background:#fffdf8}
.fz-ufs li{margin:0}
.fz-ufs button{display:flex;justify-content:space-between;width:100%;gap:8px;font:14px/1.3 var(--sans);padding:6px 8px;border:0;background:transparent;color:var(--ink);cursor:pointer;text-align:left}
.fz-ufs button:hover,.fz-ufs button[aria-pressed="true"]{background:#e6dfcf}
.fz-ufs b{font:600 13px/1.3 var(--mono)}
.fz-painel{margin:12px 0 0;padding:14px 16px;border:1px solid var(--ink);background:#fffdf8;font:15px/1.5 var(--sans)}
.fz-painel h4{margin:0 0 6px;font:700 17px/1.3 var(--sans)}
.fz-painel p{margin:0 0 6px;max-width:none}
.fz-painel .fz-links a{display:inline-block;margin:4px 12px 0 0;font-weight:700}
.fz-mapa .fz-rot text{paint-order:stroke;stroke:#f8f5ec;stroke-width:3px;stroke-linejoin:round;pointer-events:none}
html:not(.js) .fz-ctl,html:not(.js) .fz-zoom,html:not(.js) .fz-res{display:none}
@media(max-width:719px){.fz-quadro{grid-template-columns:minmax(0,1fr)}
.fz-ufs{max-height:none;display:flex;flex-wrap:wrap;gap:4px}.fz-ufs li{flex:0 0 auto}
.fz-ufs button{width:auto;border:1px solid var(--line)}}
@media print{.fz-ctl,.fz-zoom,.fz-res{display:none}}
.fs-chip{display:inline-block;margin:1px 4px 1px 0;padding:1px 7px;border:1px solid var(--line);border-radius:10px;font:600 12.5px/1.5 var(--sans);background:#fffdf8;color:var(--ink);white-space:nowrap}
.fs-chip-vazio{color:var(--muted);border-style:dashed}
.fs-nivel-alta{background:#7a3500;border-color:#7a3500;color:#fff}
.fs-nivel-media{background:#f3dcb6;border-color:#c27a1d;color:var(--ink)}
.fs-nivel-baixa{background:#ece9df;color:var(--ink)}
.fs-risco-alto{background:#5b2a86;border-color:#5b2a86;color:#fff}
.fs-risco-medio{background:#e6dcf0;border-color:#9a7cc0;color:var(--ink)}
.fs-risco-baixo{background:#f2eff6;color:var(--ink)}
.fs-tab{max-height:600px;overflow:auto}.fs-tab thead th{position:sticky;top:0;z-index:1;background:var(--paper)}
.fs-tab td,.fs-tab th{font-size:14.5px;vertical-align:top}
.fs-tab-locais td:nth-child(4){min-width:200px}
.fs-links a{white-space:nowrap;margin-right:8px;font-weight:600}
.fs-down ul.fs-downs{list-style:none;padding:0;margin:10px 0;display:grid;gap:10px}
.fs-baixar{display:inline-block;padding:10px 16px;background:var(--ink);color:var(--paper);font:700 16px/1.2 var(--sans);text-decoration:none;border-radius:2px;margin-right:12px}
.fs-baixar:hover,.fs-baixar:focus-visible{background:var(--blue);color:#fff}
.fs-det{font:13px/1.5 var(--sans);color:var(--muted);overflow-wrap:anywhere}
.fs-det code{font-size:11.5px}
.fs-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px;margin:16px 0 0}
.fs-card{border:1px solid var(--line);border-top:4px solid #7a3500;background:#fffdf8;padding:12px 14px;font:15px/1.5 var(--sans);min-width:0}
.fs-card h4{margin:2px 0 4px;font:700 16.5px/1.3 var(--sans)}
.fs-card p{margin:0 0 6px;max-width:none}
.fs-card-k{font:600 12.5px/1.5 var(--mono);color:var(--muted)}
.fs-end{color:var(--muted);font-size:14px}
.fs-num{display:grid;grid-template-columns:1fr 1fr;gap:4px 12px;margin:8px 0}
.fs-num dt{font:600 12px/1.3 var(--mono);color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.fs-num dd{margin:0;font:600 15px/1.4 var(--mono)}
.fs-num small{display:block;font:12.5px/1.3 var(--sans);color:var(--muted)}
.fs-cr{margin:0 0 6px;padding-left:18px;font-size:14px}
.fs-terr{font-size:14px;border-left:3px solid #5b2a86;padding-left:8px}
.fs-cob{margin:4px 0;padding-left:18px;font:14px/1.5 var(--sans)}
#fiscais .fontes li,.fs-cob li{overflow-wrap:anywhere}
.fs-cens{margin:12px 0}
.fs-cen{border-left:4px solid var(--line);padding:4px 0 4px 14px;margin:14px 0}
.fs-cen h4{margin:0 0 6px;font:700 17px/1.3 var(--sans)}
.fs-cen p{margin:0 0 8px}
.fs-casos-lista li{margin:0 0 10px;overflow-wrap:anywhere}
.fs-casos td,.fs-casos th{font-size:14.5px;vertical-align:top}
.fs-casos td:nth-child(4){min-width:240px}
"""

JS = r"""
(function(){
var NS='http://www.w3.org/2000/svg',ESC=__ESC__,ZM=__ZM__,ZR=__ZR__,ZX=__ZX__;
function q(el,s){return Array.prototype.slice.call(el.querySelectorAll(s));}
function sem(s){return String(s||'').normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase();}
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function inicia(fig){
  var svg=fig.querySelector('svg.fz-svg');
  if(!svg||svg.getAttribute('data-fz')){return;}
  svg.setAttribute('data-fz','1');
  var base=svg.viewBox.baseVal,W0=base.width,H0=base.height;
  var vb={x:0,y:0,w:W0,h:H0};
  var dados=null;
  q(fig,'script.fz-dados').forEach(function(n){try{dados=JSON.parse(n.textContent);}catch(e){}});
  if(!dados){return;}
  var P=dados.pontos,rows=null;
  q(fig,'script.tips').forEach(function(n){try{var t=JSON.parse(n.textContent);if(t._rows){rows=t._rows;}}catch(e){}});
  if(!rows){return;}
  var L=rows.linhas,campos=rows.campos;
  function osm(s){return 'https://www.openstreetmap.org/?mlat='+s[2]+'&mlon='+s[3]+'#map=17/'+s[2]+'/'+s[3];}
  function goo(s){return 'https://www.google.com/maps?q='+s[2]+','+s[3];}
  var gMun=svg.querySelector('.fz-mun-g'),gRot=svg.querySelector('.fz-rot'),sel=svg.querySelector('.fz-sel');
  var malhas={},carregadas={};
  q(fig,'script.fz-mun').forEach(function(n){malhas[n.getAttribute('data-uf')]=n;});
  var painel=fig.querySelector('.fz-painel'),escala=fig.querySelector('.fz-escala');
  function zoom(){return W0/vb.w;}
  function aplica(){
    var k=zoom();
    if(k<=1.0001){vb={x:0,y:0,w:W0,h:H0};}
    else{
      vb.x=Math.max(-vb.w*0.4,Math.min(W0-vb.w*0.6,vb.x));
      vb.y=Math.max(-vb.h*0.4,Math.min(H0-vb.h*0.6,vb.y));
    }
    svg.setAttribute('viewBox',vb.x.toFixed(2)+' '+vb.y.toFixed(2)+' '+vb.w.toFixed(2)+' '+vb.h.toFixed(2));
    if(escala){escala.textContent='zoom '+(Math.round(k*10)/10).toString().replace('.',',')+'×';}
    agenda();
  }
  var pend=false;
  function agenda(){if(pend){return;}pend=true;requestAnimationFrame(function(){pend=false;camadas();});}
  function px(){var r=svg.getBoundingClientRect();return r.width?vb.w/r.width:1;}
  function camadas(){
    var k=zoom();
    if(k>=ZM){
      for(var uf in malhas){
        var n=malhas[uf],c=n._c;
        if(!c){try{c=n._c=JSON.parse(n.textContent);}catch(e){continue;}}
        var b=c.caixa;
        if(b[2]<vb.x||b[0]>vb.x+vb.w||b[3]<vb.y||b[1]>vb.y+vb.h){continue;}
        if(!carregadas[uf]){
          var g=document.createElementNS(NS,'g');g.setAttribute('data-uf',uf);
          var d=c.m.map(function(m){return m[1];}).join('');
          var p=document.createElementNS(NS,'path');
          p.setAttribute('d',d);p.setAttribute('fill','#ebe5d6');p.setAttribute('stroke','#b3ab95');
          p.setAttribute('stroke-width','0.7');p.setAttribute('vector-effect','non-scaling-stroke');
          g.appendChild(p);gMun.appendChild(g);carregadas[uf]=c;
        }
      }
      gMun.removeAttribute('display');svg.classList.add('fz-perto');
    }else{gMun.setAttribute('display','none');svg.classList.remove('fz-perto');}
    while(gRot.firstChild){gRot.removeChild(gRot.firstChild);}
    if(k>=ZR){
      var u=px(),fs=13*u,ocup=[],cand=[];
      for(var uf2 in carregadas){
        carregadas[uf2].m.forEach(function(m){
          var x=m[2],y=m[3];
          if(!m[0]||x<vb.x||x>vb.x+vb.w||y<vb.y||y>vb.y+vb.h){return;}
          cand.push(m);
        });
      }
      cand.sort(function(a,b){return b[4]-a[4];});
      for(var i=0;i<cand.length&&ocup.length<70;i++){
        var m=cand[i],w=0.55*13*m[0].length*u,h=16*u;
        var cx=m[2]-w/2,cy=m[3]-h/2,ok=true;
        for(var j=0;j<ocup.length;j++){var o=ocup[j];if(cx<o[2]&&o[0]<cx+w&&cy<o[3]&&o[1]<cy+h){ok=false;break;}}
        if(!ok){continue;}
        ocup.push([cx,cy,cx+w,cy+h]);
        var t=document.createElementNS(NS,'text');
        t.setAttribute('x',m[2]);t.setAttribute('y',m[3]);t.setAttribute('text-anchor','middle');
        t.setAttribute('font-size',fs.toFixed(3));t.setAttribute('fill','#535b54');
        t.setAttribute('font-family','Archivo, Helvetica, Arial, sans-serif');
        t.style.strokeWidth=(3*u).toFixed(3);
        t.textContent=m[0];gRot.appendChild(t);
      }
    }
    if(sel&&sel.getAttribute('data-i')){var s=P[+sel.getAttribute('data-i')];marca(s);}
  }
  function pontoSvg(cx,cy){var m=svg.getScreenCTM();if(!m){return null;}var pt=svg.createSVGPoint();pt.x=cx;pt.y=cy;return pt.matrixTransform(m.inverse());}
  function zoomEm(f,cx,cy){
    var k=zoom()*f;k=Math.max(1,Math.min(ZX,k));
    var nw=W0/k,nh=H0/k,p=cx==null?{x:vb.x+vb.w/2,y:vb.y+vb.h/2}:pontoSvg(cx,cy);
    if(!p){return;}
    var rx=(p.x-vb.x)/vb.w,ry=(p.y-vb.y)/vb.h;
    vb={x:p.x-rx*nw,y:p.y-ry*nh,w:nw,h:nh};aplica();
  }
  function centra(x,y,k){k=Math.max(1,Math.min(ZX,k||zoom()));var nw=W0/k,nh=H0/k;vb={x:x-nw/2,y:y-nh/2,w:nw,h:nh};aplica();}
  function caixa(b){var k=Math.min(W0/Math.max(b[2]-b[0],4),H0/Math.max(b[3]-b[1],4))*0.85;centra((b[0]+b[2])/2,(b[1]+b[3])/2,Math.max(1,k));}
  svg.addEventListener('wheel',function(ev){ev.preventDefault();zoomEm(Math.exp(-ev.deltaY*(ev.deltaMode===1?0.05:0.0022)),ev.clientX,ev.clientY);},{passive:false});
  var toques={},arr=null,moveu=false,dist0=0,k0=1;
  svg.addEventListener('pointerdown',function(ev){
    toques[ev.pointerId]={x:ev.clientX,y:ev.clientY};
    try{svg.setPointerCapture(ev.pointerId);}catch(e){}
    var ids=Object.keys(toques);
    if(ids.length===1){arr={x:ev.clientX,y:ev.clientY,vx:vb.x,vy:vb.y};moveu=false;}
    else if(ids.length===2){var a=toques[ids[0]],b=toques[ids[1]];dist0=Math.hypot(a.x-b.x,a.y-b.y);k0=zoom();arr=null;moveu=true;}
  });
  svg.addEventListener('pointermove',function(ev){
    if(!toques[ev.pointerId]){return;}
    toques[ev.pointerId]={x:ev.clientX,y:ev.clientY};
    var ids=Object.keys(toques);
    if(ids.length===2&&dist0>0){
      var a=toques[ids[0]],b=toques[ids[1]],d=Math.hypot(a.x-b.x,a.y-b.y);
      zoomEm((k0*d/dist0)/zoom(),(a.x+b.x)/2,(a.y+b.y)/2);return;
    }
    if(!arr){return;}
    var dx=ev.clientX-arr.x,dy=ev.clientY-arr.y;
    if(!moveu&&Math.abs(dx)+Math.abs(dy)<5){return;}
    moveu=true;svg.classList.add('arrasta');fig.classList.add('arrasta');
    var u=px();vb.x=arr.vx-dx*u;vb.y=arr.vy-dy*u;aplica();
  });
  function solta(ev){
    delete toques[ev.pointerId];
    if(Object.keys(toques).length===0){
      svg.classList.remove('arrasta');fig.classList.remove('arrasta');
      if(arr&&!moveu&&ev.type==='pointerup'){escolhe(ev.clientX,ev.clientY);}
      arr=null;dist0=0;
    }
  }
  svg.addEventListener('pointerup',solta);svg.addEventListener('pointercancel',solta);
  svg.addEventListener('dblclick',function(ev){ev.preventDefault();var p=pontoSvg(ev.clientX,ev.clientY);if(p){centra(p.x,p.y,zoom()*2);}});
  function maisPerto(cx,cy,raio){
    var p=pontoSvg(cx,cy);if(!p){return -1;}
    var u=px(),best=-1,bd=Math.pow(raio*u,2);
    for(var i=0;i<P.length;i++){var dx=P[i][0]-p.x,dy=P[i][1]-p.y,dd=dx*dx+dy*dy;if(dd<bd){bd=dd;best=i;}}
    return best;
  }
  function marca(s){
    if(!sel||!s){return;}
    sel.setAttribute('cx',s[0]);sel.setAttribute('cy',s[1]);sel.setAttribute('r',(12*px()).toFixed(3));
    sel.removeAttribute('display');
  }
  function mostra(i){
    var s=P[i];if(!s||!painel){return;}
    sel.setAttribute('data-i',i);marca(s);
    var l=L[i]||[],h='<h4>'+esc(l[0]||'')+'</h4>';
    for(var j=1;j<campos.length;j++){if(l[j]===''||l[j]==null){continue;}h+='<p><b>'+esc(campos[j])+':</b> '+esc(l[j])+'</p>';}
    h+='<p class="fz-links"><a href="'+esc(osm(s))+'" target="_blank" rel="noopener">Abrir no OpenStreetMap ↗</a>'+
      '<a href="'+esc(goo(s))+'" target="_blank" rel="noopener">Abrir no Google Maps ↗</a></p>';
    painel.innerHTML=h;
  }
  function escolhe(cx,cy){var i=maisPerto(cx,cy,14);if(i>=0){mostra(i);}}
  function botao(sel_,fn){q(fig,sel_).forEach(function(b){b.addEventListener('click',fn);});}
  botao('[data-fz="mais"]',function(){zoomEm(2);});
  botao('[data-fz="menos"]',function(){zoomEm(0.5);});
  botao('[data-fz="brasil"]',function(){vb={x:0,y:0,w:W0,h:H0};aplica();q(fig,'.fz-ufs button').forEach(function(x){x.setAttribute('aria-pressed','false');});});
  q(fig,'.fz-ufs button').forEach(function(b){b.addEventListener('click',function(){
    q(fig,'.fz-ufs button').forEach(function(x){x.setAttribute('aria-pressed',x===b?'true':'false');});
    caixa(b.getAttribute('data-caixa').split(' ').map(Number));
  });});
  svg.setAttribute('tabindex','0');
  svg.addEventListener('keydown',function(ev){
    var u=vb.w*0.15,f={'+':2,'=':2,'-':0.5,'_':0.5}[ev.key];
    if(f){zoomEm(f);ev.preventDefault();return;}
    if(ev.key==='0'){vb={x:0,y:0,w:W0,h:H0};aplica();ev.preventDefault();return;}
    var mv={ArrowLeft:[-u,0],ArrowRight:[u,0],ArrowUp:[0,-u],ArrowDown:[0,u]}[ev.key];
    if(mv){vb.x+=mv[0];vb.y+=mv[1];aplica();ev.preventDefault();}
  });
  var busca=fig.querySelector('.fz-busca input'),res=fig.querySelector('.fz-res');
  var indice=L.map(function(l){return sem(l[0]+' '+l[1]);});
  function procura(texto,ir){
    var t=sem(texto).trim();res.innerHTML='';
    if(t.length<2){return;}
    var achou=[];
    for(var i=0;i<P.length&&achou.length<8;i++){if(indice[i].indexOf(t)>=0){achou.push(i);}}
    if(!achou.length){res.innerHTML='<li>nenhum local com esse nome</li>';return;}
    achou.forEach(function(i){
      var li=document.createElement('li'),b=document.createElement('button');b.type='button';
      b.textContent=L[i][0]+' · '+L[i][1];
      b.addEventListener('click',function(){centra(P[i][0],P[i][1],Math.max(zoom(),14));mostra(i);});
      li.appendChild(b);res.appendChild(li);
    });
    if(ir){centra(P[achou[0]][0],P[achou[0]][1],Math.max(zoom(),14));mostra(achou[0]);}
  }
  if(busca){
    busca.addEventListener('input',function(){procura(busca.value,false);});
    busca.addEventListener('keydown',function(ev){if(ev.key==='Enter'){ev.preventDefault();procura(busca.value,true);}});
    botao('[data-fz="buscar"]',function(){procura(busca.value,true);});
  }
  fig._fz={zoom:zoom,vb:function(){return vb;},centra:centra,procura:procura};
  aplica();
}
function todas(){q(document,'figure[data-fz-fig]').forEach(inicia);}
document.addEventListener('fig:pronta',function(ev){if(ev.target&&ev.target.hasAttribute&&ev.target.hasAttribute('data-fz-fig')){inicia(ev.target);}});
if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',todas);}else{todas();}
})();
"""


def js() -> str:
    return (
        JS.replace("__ESC__", str(ESCALA_MALHA))
        .replace("__ZM__", str(ZOOM_MALHA))
        .replace("__ZR__", str(ZOOM_ROTULO))
        .replace("__ZX__", str(ZOOM_MAX))
    )
