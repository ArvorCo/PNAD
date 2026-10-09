/* Interface do simulador; as contas ficam no motor compartilhado com Python. */
(() => {
  'use strict';
  const root=document.querySelector('#simulador');
  if (!root || !window.Reponderacao2T) return;
  let M=window.Reponderacao2T;
  const current=JSON.parse(document.querySelector('#rs-data').textContent);
  const engines=new Map([[current.engine,M]]);
  let data=current, p={...data.defaults}, result=data.central, loading=false, loadId=0;
  const $=id=>document.getElementById('rs-'+id);
  const fmt=n=>n.toLocaleString('pt-BR',{minimumFractionDigits:1,maximumFractionDigits:1});
  const signed=n=>(n>0?'+':n<0?'−':'')+fmt(Math.abs(n));
  const equal=(a,b)=>Object.keys(data.defaults).every(k=>a[k]===b[k]);
  const presets=current.presets;
  const names={publicado:'Publicado',pnad:'PNAD',modelo:'PNAD + comparecimento'};
  const ageNames={central:'idade central',idosos60:'presença 60+: 60%',idosos80:'presença 60+: 80%'};
  const mobile=matchMedia('(max-width:800px)');
  const primary=root.querySelector('.rs-primary'), rates=$('rates');
  const primaryHome=document.createComment('presença relativa');
  primary.before(primaryHome);
  function positionPrimary() {
    if(mobile.matches) root.querySelector('.rs-account').after(primary,rates);
    else primaryHome.after(primary,rates);
  }
  mobile.addEventListener('change',positionPrimary);positionPrimary();
  function label() {
    const preset=presets.find(x=>equal(p,{...data.defaults,...x.parametros}));
    return preset?.nome || 'Meu cenário';
  }
  function curve() {
    const points=[];
    for (let x=-30;x<=30;x+=2) points.push([x,M.evaluate(data,{...p,presenca_relativa:x}).diferenca_flavio_lula]);
    const extent=Math.max(5,...points.map(x=>Math.abs(x[1])));
    const px=x=>35+(x+30)*410/60, py=y=>75-y*53/extent;
    const path=points.map(([x,y],i)=>`${i?'L':'M'}${px(x).toFixed(2)},${py(y).toFixed(2)}`).join(' ');
    const grid=[-30,-15,0,15,30].map(x=>`<line x1="${px(x)}" x2="${px(x)}" y1="18" y2="135" stroke="#ffffff0d"/><text x="${px(x)}" y="153" text-anchor="middle" fill="#c5d2cb" font-size="10">${x>0?'+':''}${x}%</text>`).join('');
    $('curve').innerHTML=`<title>Diferença Flávio menos Lula por presença relativa</title>${grid}<line x1="35" x2="445" y1="75" y2="75" stroke="#91a69d" stroke-dasharray="3 4"/><text x="448" y="78" fill="#c5d2cb" font-size="9">0</text><path d="${path}" fill="none" stroke="#d9ef96" stroke-width="2"/><circle cx="${px(p.presenca_relativa)}" cy="${py(result.diferenca_flavio_lula)}" r="4" fill="#d9ef96"/><text x="${px(p.presenca_relativa)}" y="${py(result.diferenca_flavio_lula)-10}" text-anchor="middle" fill="#d9ef96" font-size="12">${signed(result.diferenca_flavio_lula)} pp</text>`;
    const threshold=M.breakEven(data,p);
    $('threshold').textContent=threshold===null?'Sem empate dentro da faixa de −30% a +30%, mantidas as outras hipóteses.':`Empate com presença relativa de Flávio em ${signed(threshold)}%, mantidas as outras hipóteses. O gráfico é sensibilidade, não intervalo.`;
  }
  function controls() {
    for (const el of root.querySelectorAll('[data-param]')) {
      const k=el.dataset.param;
      if (el.tagName==='SELECT' && ![...el.options].some(o=>o.value===String(p[k]===null?'p':p[k]))) {
        const o=new Option(`${fmt(p[k])}% para Flávio`,String(p[k]));el.add(o);
      }
      el.value=p[k]===null?'p':p[k];
      if ($('out-'+k)) $('out-'+k).textContent=`${['presenca_relativa','branco_nulo_pp','nulo_diferencial_pp','vies_pp'].includes(k)?signed(p[k]):fmt(p[k])}${['branco_nulo_pp','vies_pp'].includes(k)?' pp':'%'}`;
    }
    $('idade').disabled=p.modo!=='modelo';
  }
  function render(updateHash=false) {
    result=M.evaluate(data,p);
    controls();
    for (const k of ['flavio','lula']) {
      $(k).replaceChildren(document.createTextNode(fmt(result[k])),Object.assign(document.createElement('small'),{textContent:'%'}));
      $('bar-'+k).style.width=result[k]+'%';
    }
    $('label').textContent=label();$('reference').textContent=data.reference;
    $('gap').textContent=signed(result.diferenca_flavio_lula)+' pp';
    const central=M.evaluate(data);
    $('versus').textContent=equal(p,data.defaults)?'Positivo favorece Flávio; negativo favorece Lula.':`${signed(result.diferenca_flavio_lula-central.diferenca_flavio_lula)} pp em relação à central da versão ${data.reference}.`;
    $('absent').textContent=fmt(result.abstencao)+'%';
    $('invalid').textContent=fmt(100*result.branco_nulo/result.comparecimento)+'%';
    $('rates').textContent=`Presença efetiva no cenário: Flávio ${fmt(100*result.taxas.flavio)}% · Lula ${fmt(100*result.taxas.lula)}%.`;
    for(const [k,v] of Object.entries(result.por_100_eleitores)) {
      $('mass-'+k).textContent=fmt(v);
      const el=root.querySelector(`[data-mass="${k}"]`);el.style.width=v+'%';el.title=`${k}: ${fmt(v)} por 100 eleitores`;
    }
    root.querySelectorAll('[data-rs-preset]').forEach(b=>b.setAttribute('aria-pressed',String(equal(p,{...data.defaults,...presets.find(x=>x.id===b.dataset.rsPreset).parametros}))));
    const saturated=Object.values(result.taxas).some(q=>q>=1-1e-9);
    $('warning').textContent=[data!==current?`Dados arquivados de ${data.reference}; “Restaurar” volta à versão atual.`:'',saturated?'Uma taxa atingiu 100%; o teto físico limita a razão de presença.':'',p.modo!=='modelo'?'Base sem propensão Nexus; a presença relativa continua sendo sua hipótese livre.':''].filter(Boolean).join(' ');
    curve();
    if(updateHash) history.replaceState(null,'',M.encode(data,p));
    window.reponderacaoCenario={result,params:p,version:data.version};
    document.dispatchEvent(new CustomEvent('reponderacao:cenario',{detail:window.reponderacaoCenario}));
  }
  async function engineFor(chosen) {
    if(!/^[a-f0-9]{16}$/.test(chosen.engine)) throw Error('Motor do cenário não identificado.');
    if(!engines.has(chosen.engine)) {
      await new Promise((resolve,reject)=>{
        const script=document.createElement('script');
        script.src=`assets/reponderacao_cenarios/motor-${chosen.engine}.js`;
        script.onload=resolve;script.onerror=()=>reject(Error('Motor arquivado indisponível.'));
        document.head.append(script);
      });
      engines.set(chosen.engine,window.Reponderacao2T);
    }
    return engines.get(chosen.engine);
  }
  async function fromHash() {
    const id=++loadId;
    const version=location.hash.match(/(?:#sim=|;)v:([a-f0-9]{16})(?:;|$)/)?.[1];
    loading=true;
    try {
      let chosen=current;
      if(version && version!==current.version) {
        $('share-state').textContent='Carregando a versão do cenário compartilhado…';
        const response=await fetch(`assets/reponderacao_cenarios/${version}.json`);
        if(!response.ok) throw Error('A versão do link não está disponível. A central atual foi mantida; o cenário não foi recriado.');
        chosen=await response.json();
        if(chosen.version!==version || chosen.schema!==1) throw Error('Versão do cenário incompatível.');
      }
      const engine=await engineFor(chosen);
      if(id!==loadId) return;
      M=engine;data=chosen;p=M.decode(data,location.hash);
      $('share-state').textContent='';render();
    } catch(e) {
      if(id!==loadId) return;
      M=engines.get(current.engine);data=current;p={...current.defaults};render();$('share-state').textContent=e.message;
    } finally { if(id===loadId) loading=false; }
  }
  for(const el of root.querySelectorAll('[data-param]')) el.addEventListener('input',()=>{
    if(loading) return;
    const k=el.dataset.param;
    p[k]=['modo','idade'].includes(k)?el.value:el.value==='p'?null:Number(el.value);
    render(true);
  });
  root.querySelectorAll('[data-rs-preset]').forEach(el=>el.addEventListener('click',()=>{
    if(loading) return;p={...data.defaults,...presets.find(x=>x.id===el.dataset.rsPreset).parametros};render(true);
  }));
  $('reset').addEventListener('click',()=>{++loadId;loading=false;M=engines.get(current.engine);data=current;p={...current.defaults};render(true);$('share-state').textContent='';});
  function shareUrl(){return new URL('reponderacao_pnad.html',location.href).href+M.encode(data,p);}
  $('copy').addEventListener('click',async()=>{
    try{await navigator.clipboard.writeText(shareUrl());$('share-state').textContent='Link copiado: parâmetros e versão dos dados preservados.';}
    catch{const input=document.createElement('input');input.value=shareUrl();input.setAttribute('aria-label','Link do cenário');$('share-state').replaceChildren(input);input.select();}
  });
  function imageBlob() {
    const canvas=document.createElement('canvas');canvas.width=1200;canvas.height=630;
    const ctx=canvas.getContext('2d');ctx.fillStyle='#142d2a';ctx.fillRect(0,0,1200,630);
    const text=(t,x,y,font,color)=>{ctx.font=font;ctx.fillStyle=color;ctx.fillText(t,x,y);};
    text('ARVOR / ELEIÇÕES 2026 / 2º TURNO',55,52,'17px sans-serif','#d9ef96');
    text(label()+' · '+data.reference,55,96,'24px Georgia','#f4f0e7');
    text('Votos válidos · cenário condicional',55,136,'18px sans-serif','#c5d2cb');
    text('FLÁVIO BOLSONARO',55,201,'20px sans-serif','#a9cbff');text('LULA',650,201,'20px sans-serif','#f7b0aa');
    text(fmt(result.flavio)+'%',50,302,'96px Georgia','#a9cbff');text(fmt(result.lula)+'%',645,302,'96px Georgia','#f7b0aa');
    ctx.fillStyle='#a9cbff';ctx.fillRect(55,329,1090*result.flavio/100,16);ctx.fillStyle='#e5938c';ctx.fillRect(55+1090*result.flavio/100,329,1090*result.lula/100,16);
    text('Flávio − Lula: '+signed(result.diferenca_flavio_lula)+' pp',55,390,'29px Georgia','#d9ef96');
    text(`Presença relativa F: ${signed(p.presenca_relativa)}% · abstenção: ${fmt(result.abstencao)}% · B/N: ${fmt(100*result.branco_nulo/result.comparecimento)}% dos votantes`,55,430,'19px sans-serif','#f4f0e7');
    text(`${names[p.modo]} · ${ageNames[p.idade]} · Δ B/N: ${signed(p.branco_nulo_pp)} pp · saída desigual: ${signed(p.nulo_diferencial_pp)}%`,55,465,'16px sans-serif','#c5d2cb');
    text(`Indecisos válidos: ${fmt(p.indecisos_validos)}% · para F: ${p.indecisos_flavio===null?'proporcional':fmt(p.indecisos_flavio)+'%'} · erro comum F−L: ${signed(p.vies_pp)} pp`,55,493,'16px sans-serif','#c5d2cb');
    text('Hipóteses declaradas. Sem intervalo preditivo validado ou probabilidade de vitória.',55,553,'16px sans-serif','#c5d2cb');
    text('brasil.arvor.co/reponderacao_pnad.html',55,593,'17px sans-serif','#f4f0e7');
    text('dados '+data.version,880,593,'13px monospace','#c5d2cb');
    return new Promise(resolve=>canvas.toBlob(resolve,'image/png'));
  }
  $('image').addEventListener('click',async()=>{
    try{const blob=await imageBlob();if(!blob)throw Error();const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=`arvor-2turno-${data.reference}.png`;a.click();setTimeout(()=>URL.revokeObjectURL(url),10000);$('share-state').textContent='Imagem 1200 × 630 gerada com as hipóteses do cenário.';}
    catch{$('share-state').textContent='Não foi possível gerar a imagem neste navegador.';}
  });
  if(navigator.share) {
    $('share').hidden=false;$('share').addEventListener('click',async()=>{
      try{const blob=await imageBlob();const file=new File([blob],`arvor-2turno-${data.reference}.png`,{type:'image/png'});const payload={title:'Meu cenário do 2º turno · Arvor',text:`Flávio ${fmt(result.flavio)}% × Lula ${fmt(result.lula)}% dos válidos. Cenário condicional.`,url:shareUrl()};if(navigator.canShare?.({files:[file]}))payload.files=[file];await navigator.share(payload);}
      catch(e){if(e.name!=='AbortError')$('share-state').textContent='Use “Copiar link” ou “Baixar imagem” para compartilhar.';}
    });
  }
  root.querySelector('.rs-controls').hidden=false;root.querySelector('.rs-share').hidden=false;
  window.addEventListener('hashchange',fromHash);render();fromHash();
})();
