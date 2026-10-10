/* Interface do simulador; as contas ficam no motor compartilhado com Python. */
(() => {
  'use strict';
  const root=document.querySelector('#simulador');
  if (!root || !window.Reponderacao2T || !window.ReponderacaoContagem) return;
  let M=window.Reponderacao2T;
  const current=JSON.parse(document.querySelector('#rs-data').textContent);
  const engines=new Map([[current.engine,M]]);
  let data=current, p={...data.defaults}, result=data.central, loading=false, loadId=0, mcId=0, mcTimer;
  const $=id=>document.getElementById('rs-'+id);
  const fmt=n=>n.toLocaleString('pt-BR',{minimumFractionDigits:1,maximumFractionDigits:1});
  const signed=n=>(n>0?'+':n<0?'−':'')+fmt(Math.abs(n));
  const millions=n=>fmt(n/1e6);
  const electorate=()=>data.electorate || current.electorate;
  const counts=()=>window.ReponderacaoContagem.counts(result,electorate());
  const equal=(a,b)=>Object.keys(data.defaults).every(k=>a[k]===b[k]);
  const centre=()=>p.centro || 'media';
  const centreNames={media:'Central Média Arvor',projecao:'Central Projeção Arvor'};
  const centralParams=()=>({...data.defaults,...(data.projection?{centro:centre()}:{})});
  const presets=current.presets;
  const names={publicado:'Publicado',pnad:'PNAD',modelo:'PNAD + comparecimento'};
  const ageNames={central:'idade central',idosos60:'presença 60+: 60%',idosos80:'presença 60+: 80%'};
  const mobile=matchMedia('(max-width:800px)');
  const primary=root.querySelector('.rs-primary'), rates=$('rates'), undecidedPanel=root.querySelector('.rs-undecided');
  const primaryHome=document.createComment('presença relativa');
  const undecidedHome=document.createComment('transferência de indecisos');
  undecidedPanel.before(undecidedHome);
  primary.before(primaryHome);
  function positionPrimary() {
    if(mobile.matches) root.querySelector('.rs-account').after(primary,rates,undecidedPanel);
    else {primaryHome.after(primary,rates);undecidedHome.after(undecidedPanel);}
  }
  mobile.addEventListener('change',positionPrimary);positionPrimary();
  function label() {
    if(equal(p,centralParams())) return centreNames[centre()];
    const preset=presets.find(x=>equal(p,{...centralParams(),...x.parametros}));
    return `${preset?.nome || 'Meu cenário'} · ${centre()==='projecao'?'Projeção':'Média'}`;
  }
  function simulations() {
    clearTimeout(mcTimer);const id=++mcId;
    const visible=centre()==='projecao' && Boolean(data.projection) && typeof M.simulate==='function';
    $('uncertainty').hidden=!visible;
    if(!visible) return;
    $('mc-ranges').textContent='Calculando os 2.000 sorteios desta versão…';$('mc-frequency').textContent='';
    const chosen=data, params={...p}, engine=M;
    mcTimer=setTimeout(()=>{
      if(id!==mcId) return;
      const u=engine.simulate(chosen,params);
      $('mc-ranges').textContent=`Flávio ${fmt(u.flavio.p05)}–${fmt(u.flavio.p95)}% · Lula ${fmt(u.lula.p05)}–${fmt(u.lula.p95)}%`;
      $('mc-frequency').textContent=`Flávio à frente em ${fmt(100*u.share_flavio_ahead)}% dos ${u.runs.toLocaleString('pt-BR')} sorteios nestas hipóteses. Diferença F−L: ${signed(u.gap.p05)} a ${signed(u.gap.p95)} pp.`;
      window.reponderacaoCenario.monte_carlo=u;
      document.dispatchEvent(new CustomEvent('reponderacao:cenario',{detail:window.reponderacaoCenario}));
    },80);
  }
  function centralCards() {
    const extra=signed(data.defaults.presenca_relativa)+'%';
    $('relative-explanation').textContent=data.presence_model
      ? `as duas centrais usam propensão Nexus + ajuste relativo de Flávio ${extra}, referência residual do 1º turno transportada como hipótese. Não é presença medida por candidato.`
      : `esta versão arquivada usa propensão Nexus + presença relativa de Flávio ${extra}, hipótese declarada sem taxa por candidato medida na urna.`;
    $('presence-origin').textContent=data.presence_model
      ? `Referência desta versão: ${extra} extra, a partir do resíduo do 1º turno. `
      : `Referência arquivada: ${extra} extra. A conta abaixo documenta a revisão atual; restaure para usar os novos dados. `;
    for(const button of root.querySelectorAll('[data-rs-central]')) {
      const key=button.dataset.rsCentral, available=key==='media' || Boolean(data.projection);
      button.disabled=!available;button.setAttribute('aria-pressed',String(key===centre()));
      button.closest('article').classList.toggle('is-active',key===centre());
      const value=key==='media'?data.central:data.central_projection;
      $('central-score-'+key).textContent=available?`${fmt(value.flavio)}% × ${fmt(value.lula)}%`:'Sem modelo nesta versão';
    }
    $('base-explanation').textContent=centre()==='media'
      ? 'Média: peso igual entre casas com cruzamento de renda elegível. Monte Carlo não participa desta central.'
      : `Projeção: recência em ${data.projection.selected.length} casas; resultado publicado quando falta renda. ${data.projection.trend.pnad.status}`;
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
      if(k==='indecisos_flavio') continue;
      if (el.tagName==='SELECT' && ![...el.options].some(o=>o.value===String(p[k]===null?'p':p[k]))) {
        const o=new Option(`${fmt(p[k])}% para Flávio`,String(p[k]));el.add(o);
      }
      el.value=p[k]===null?'p':p[k];
      if ($('out-'+k)) $('out-'+k).textContent=`${['presenca_relativa','branco_nulo_pp','nulo_diferencial_pp','vies_pp'].includes(k)?signed(p[k]):fmt(p[k])}${['branco_nulo_pp','vies_pp'].includes(k)?' pp':'%'}`;
    }
    $('idade').disabled=p.modo!=='modelo';
  }
  function undecided() {
    const engine=typeof M.undecided==='function'?M:engines.get(current.engine);
    const u=engine.undecided({...data,electorate:electorate()},p);
    const precise=n=>n.toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2});
    const change=n=>(n>0?'+':n<0?'−':'')+precise(Math.abs(n));
    $('undecided-pool').textContent=`${fmt(u.survey_pct)}% na base ${p.modo==='publicado'?'publicada':'PNAD'} · ${fmt(u.present_voters_pct)}% dos votantes neste cenário · ${precise(u.present_total/1e6)} milhões de indecisos presentes.`;
    $('out-indecisos_flavio').textContent=`Flávio ${fmt(u.chosen_flavio_pct)}% · Lula ${fmt(100-u.chosen_flavio_pct)}%`;
    $('indecisos_flavio').value=u.chosen_flavio_pct;
    if(document.activeElement!==$('indecisos_flavio-number')) $('indecisos_flavio-number').value=u.chosen_flavio_pct.toFixed(1);
    $('undecided-proportional').setAttribute('aria-pressed',String(p.indecisos_flavio===null));
    const rule=u.policy==='central_proportion'?'a proporção Flávio/Lula da central, antes da conversão':'a proporção de cada pesquisa, regra deste link arquivado';
    $('undecided-rule').textContent=p.indecisos_flavio===null?`Automático: acompanha ${rule}. Arraste para criar outra divisão.`:`Divisão livre: ${fmt(u.chosen_flavio_pct)}% para Flávio, ${fmt(100-u.chosen_flavio_pct)}% para Lula. Proporção automática desta base: ${fmt(u.proportional_flavio_pct)}% / ${fmt(100-u.proportional_flavio_pct)}%.`;
    for(const [key,value] of [['flavio',u.to_flavio],['lula',u.to_lula],['invalid',u.to_invalid]]) {
      root.querySelector(`[data-undecided-part="${key}"]`).style.width=(u.present_total?100*value/u.present_total:0)+'%';
      $('undecided-to-'+key).textContent=precise(value/1e6);
    }
    $('undecided-impact').textContent=`Efeito nos válidos de Flávio: ${change(u.impact_flavio_pp)} pp · ${change(u.impact_flavio_votes/1e6)} milhão de votos vs. divisão automática, com os demais controles iguais.`;
    return u;
  }
  function turnout() {
    const t=data.turnout_model;
    $('turnout-readout').hidden=!t;$('turnout-options').hidden=!t;
    if(!t) return;
    const baseline=t.first_round,delta=p.comparecimento-baseline.turnout_pct;
    const precise=n=>n.toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2});
    const direction=delta>0?'+':delta<0?'−':'';
    $('turnout-readout').textContent=`1º turno observado: ${precise(baseline.turnout_pct)}% compareceram. Neste cenário: ${direction}${precise(Math.abs(delta))} pp e ${signed(electorate().total*delta/100/1e6)} milhão de mudança no comparecimento. Abstenção: ${precise(100-p.comparecimento)}%.`;
    const choices=root.querySelector('.rs-turnout-choices'),fragment=document.createDocumentFragment();
    for(const row of t.scenarios) {
      const button=document.createElement('button');button.type='button';button.dataset.rsTurnout=row.id;
      button.setAttribute('aria-pressed',String(Math.abs(p.comparecimento-row.turnout_pct)<1e-8));
      for(const [tag,txt] of [['span',row.name],['b',precise(row.turnout_pct)+'%'],['small',(row.delta_turnout_pp>0?'+':row.delta_turnout_pp<0?'−':'')+precise(Math.abs(row.delta_turnout_pp))+' pp vs. 1º turno']]) {
        const el=document.createElement(tag);el.textContent=txt;button.append(el);
      }
      fragment.append(button);
    }
    choices.replaceChildren(fragment);
  }
  function render(updateHash=false) {
    result=M.evaluate(data,p);
    const totals=counts();
    controls();
    for (const k of ['flavio','lula']) {
      $(k).replaceChildren(document.createTextNode(fmt(result[k])),Object.assign(document.createElement('small'),{textContent:'%'}));
      $('bar-'+k).style.width=result[k]+'%';
      $('count-'+k).textContent=millions(totals[k])+' milhões de votos';
    }
    $('label').textContent=label();$('reference').textContent=data.reference;
    $('gap').textContent=signed(result.diferenca_flavio_lula)+' pp';
    $('count-gap').textContent=signed(totals.diferenca_flavio_lula/1e6)+' milhões de votos';
    const central=M.evaluate(data,centralParams());
    $('versus').textContent=equal(p,centralParams())?'Positivo favorece Flávio; negativo favorece Lula.':`${signed(result.diferenca_flavio_lula-central.diferenca_flavio_lula)} pp em relação à ${centreNames[centre()]} desta versão.`;
    $('absent').textContent=fmt(result.abstencao)+'%';
    $('invalid').textContent=fmt(100*result.branco_nulo/result.comparecimento)+'%';
    $('attendance').textContent=fmt(result.comparecimento)+'%';
    for(const k of ['abstencao','branco_nulo','validos','comparecimento']) {
      $('count-'+k).replaceChildren(document.createTextNode(millions(totals[k])+' '),Object.assign(document.createElement('small'),{textContent:'milhões'}));
      $('count-'+k).title=totals[k].toLocaleString('pt-BR',{maximumFractionDigits:0})+' no cenário, antes de arredondar em milhões';
    }
    $('count-eleitorado').textContent=`${millions(totals.eleitorado)} milhões de eleitores · TSE 2026 · ${electorate().scope}${data.electorate?'':' · base atual aplicada a esta versão antiga'}`;
    $('rates').textContent=`Presença efetiva no cenário: Flávio ${fmt(100*result.taxas.flavio)}% · Lula ${fmt(100*result.taxas.lula)}%.`;
    for(const [k,v] of Object.entries(result.por_100_eleitores)) {
      $('mass-'+k).textContent=fmt(v);
      const el=root.querySelector(`[data-mass="${k}"]`);el.style.width=v+'%';el.title=`${k}: ${fmt(v)} por 100 eleitores`;
    }
    root.querySelectorAll('[data-rs-preset]').forEach(b=>b.setAttribute('aria-pressed',String(equal(p,{...centralParams(),...presets.find(x=>x.id===b.dataset.rsPreset).parametros}))));
    const saturated=Object.values(result.taxas).some(q=>q>=1-1e-9);
    $('warning').textContent=[data!==current?`Dados arquivados de ${data.reference}; “Restaurar” volta à versão atual.`:'',saturated?'Uma taxa atingiu 100%; o teto físico limita a razão de presença.':'',p.modo!=='modelo'?'Base sem propensão Nexus; a presença relativa continua sendo sua hipótese livre.':''].filter(Boolean).join(' ');
    centralCards();curve();turnout();const undecidedResult=undecided();
    if(updateHash) history.replaceState(null,'',M.encode(data,p));
    window.reponderacaoCenario={result,params:p,version:data.version,totais:totals,base_eleitorado:electorate(),indecisos:undecidedResult};
    document.dispatchEvent(new CustomEvent('reponderacao:cenario',{detail:window.reponderacaoCenario}));
    simulations();
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
    loading=true;clearTimeout(mcTimer);++mcId;
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
    if(el.type==='number' && (el.value==='' || !el.validity.valid)) return;
    const k=el.dataset.param;
    p[k]=['modo','idade'].includes(k)?el.value:el.value==='p'?null:Number(el.value);
    render(true);
  });
  $('undecided-proportional').addEventListener('click',()=>{if(!loading){p.indecisos_flavio=null;render(true);}});
  $('indecisos_flavio-number').addEventListener('blur',()=>{$('indecisos_flavio-number').value=window.reponderacaoCenario.indecisos.chosen_flavio_pct.toFixed(1);});
  root.querySelectorAll('[data-rs-undecided-share]').forEach(el=>el.addEventListener('click',()=>{if(!loading){p.indecisos_flavio=Number(el.dataset.rsUndecidedShare);render(true);}}));
  root.querySelectorAll('[data-rs-preset]').forEach(el=>el.addEventListener('click',()=>{
    if(loading) return;p={...centralParams(),...presets.find(x=>x.id===el.dataset.rsPreset).parametros};render(true);
  }));
  root.querySelectorAll('[data-rs-central]').forEach(el=>el.addEventListener('click',()=>{
    if(loading || el.disabled) return;p={...p,centro:el.dataset.rsCentral};render(true);
  }));
  root.addEventListener('click',event=>{
    const button=event.target.closest('[data-rs-turnout]');
    if(!button || loading || !data.turnout_model) return;
    const scenario=data.turnout_model.scenarios.find(r=>r.id===button.dataset.rsTurnout);
    if(!scenario) return;p={...p,comparecimento:scenario.turnout_pct};render(true);
  });
  $('reset').addEventListener('click',()=>{const key=data===current?centre():'media';++loadId;loading=false;M=engines.get(current.engine);data=current;p={...current.defaults,centro:key};render(true);$('share-state').textContent='';});
  function shareUrl(){return new URL('reponderacao_pnad.html',location.href).href+M.encode(data,p);}
  $('copy').addEventListener('click',async()=>{
    try{await navigator.clipboard.writeText(shareUrl());$('share-state').textContent='Link copiado: parâmetros e versão dos dados preservados.';}
    catch{const input=document.createElement('input');input.value=shareUrl();input.setAttribute('aria-label','Link do cenário');$('share-state').replaceChildren(input);input.select();}
  });
  function imageBlob() {
    const totals=counts();
    const canvas=document.createElement('canvas');canvas.width=1200;canvas.height=630;
    const ctx=canvas.getContext('2d');ctx.fillStyle='#142d2a';ctx.fillRect(0,0,1200,630);
    const text=(t,x,y,font,color)=>{ctx.font=font;ctx.fillStyle=color;ctx.fillText(t,x,y);};
    text('ARVOR / ELEIÇÕES 2026 / 2º TURNO',55,52,'17px sans-serif','#d9ef96');
    text(label()+' · '+data.reference,55,96,'24px Georgia','#f4f0e7');
    const u=centre()==='projecao'?M.simulate(data,p):null;
    const subtitle=u?`Válidos · 90% dos sorteios: F ${fmt(u.flavio.p05)}–${fmt(u.flavio.p95)}% / L ${fmt(u.lula.p05)}–${fmt(u.lula.p95)}%`:'Votos válidos · cenário condicional';
    text(subtitle,55,136,'18px sans-serif','#c5d2cb');
    text('FLÁVIO BOLSONARO',55,178,'20px sans-serif','#a9cbff');text('LULA',650,178,'20px sans-serif','#f7b0aa');
    text(fmt(result.flavio)+'%',50,265,'90px Georgia','#a9cbff');text(fmt(result.lula)+'%',645,265,'90px Georgia','#f7b0aa');
    text(millions(totals.flavio)+' milhões de votos',55,299,'22px sans-serif','#a9cbff');text(millions(totals.lula)+' milhões de votos',650,299,'22px sans-serif','#f7b0aa');
    ctx.fillStyle='#a9cbff';ctx.fillRect(55,319,1090*result.flavio/100,13);ctx.fillStyle='#e5938c';ctx.fillRect(55+1090*result.flavio/100,319,1090*result.lula/100,13);
    text('Flávio − Lula: '+signed(result.diferenca_flavio_lula)+' pp',55,369,'27px Georgia','#d9ef96');
    text(signed(totals.diferenca_flavio_lula/1e6)+' milhões de votos',650,369,'24px Georgia','#d9ef96');
    for(const [k,name,x] of [['validos','VÁLIDOS',55],['branco_nulo','BRANCOS/NULOS',435],['abstencao','ABSTENÇÕES',815]]) {
      text(name,x,403,'13px sans-serif','#c5d2cb');text(millions(totals[k])+' milhões',x,432,'25px Georgia','#f4f0e7');
    }
    text(`Compareceriam: ${millions(totals.comparecimento)} mi · base TSE: ${millions(totals.eleitorado)} mi (${electorate().scope}${data.electorate?'':'; base atual'}) · arredondados`,55,457,'15px sans-serif','#c5d2cb');
    text(`Presença relativa F: ${signed(p.presenca_relativa)}% · abstenção: ${fmt(result.abstencao)}% · B/N: ${fmt(100*result.branco_nulo/result.comparecimento)}% dos votantes`,55,486,'17px sans-serif','#f4f0e7');
    text(`${names[p.modo]} · ${ageNames[p.idade]} · Δ B/N: ${signed(p.branco_nulo_pp)} pp · saída desigual: ${signed(p.nulo_diferencial_pp)}% · erro F−L: ${signed(p.vies_pp)} pp`,55,511,'15px sans-serif','#c5d2cb');
    const allocation=window.reponderacaoCenario.indecisos;
    text(`Indecisos: ${fmt(allocation.survey_pct)}% na base · ${fmt(p.indecisos_validos)}% escolhem · divisão F ${fmt(allocation.chosen_flavio_pct)}% / L ${fmt(100-allocation.chosen_flavio_pct)}%`,55,536,'15px sans-serif','#c5d2cb');
    text('Hipóteses declaradas. Sem intervalo preditivo validado ou probabilidade de vitória.',55,566,'15px sans-serif','#c5d2cb');
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
      try{const blob=await imageBlob();const file=new File([blob],`arvor-2turno-${data.reference}.png`,{type:'image/png'});const totals=counts();const payload={title:'Meu cenário do 2º turno · Arvor',text:`${label()}: Flávio ${fmt(result.flavio)}% (${millions(totals.flavio)} mi) × Lula ${fmt(result.lula)}% (${millions(totals.lula)} mi). Votos válidos, cenário condicional.`,url:shareUrl()};if(navigator.canShare?.({files:[file]}))payload.files=[file];await navigator.share(payload);}
      catch(e){if(e.name!=='AbortError')$('share-state').textContent='Use “Copiar link” ou “Baixar imagem” para compartilhar.';}
    });
  }
  root.querySelector('.rs-controls').hidden=false;root.querySelector('.rs-share').hidden=false;
  window.addEventListener('hashchange',()=>{if(!location.hash || location.hash.startsWith('#sim=')) fromHash();});render();fromHash();
})();
