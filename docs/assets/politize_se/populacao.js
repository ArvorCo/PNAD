/* População residente não é cadastro eleitoral. Componente comum das duas páginas. */
(function () {
  'use strict';
  const BASE = 'assets/politize_se/populacao/';
  let promise;
  const num = v => typeof v === 'number' && Number.isFinite(v);
  const fmt = (v, d=0) => num(v) ? v.toLocaleString('pt-BR', {maximumFractionDigits:d}) : 'Sem dado';
  const pct = v => num(v) ? fmt(v, 1)+'%' : 'Sem dado';
  const signed = (v, unit='') => num(v) ? (v>0?'+':'')+fmt(v,1)+unit : 'Sem dado';
  const rate = (a,b) => num(a)&&num(b)&&b>0 ? 100*a/b : null;
  function el(tag, attrs={}, ...kids) {
    const n=document.createElement(tag);
    for(const [k,v] of Object.entries(attrs)) if(v!==null&&v!==false) n.setAttribute(k,v===true?'':v);
    for(const c of kids.flat(Infinity)) if(c!==null&&c!==undefined) n.append(c instanceof Node?c:document.createTextNode(String(c)));
    return n;
  }
  async function dados() {
    if(!promise) promise=Promise.all(['indice.json','municipios.json'].map(async f=>{
      const r=await fetch(BASE+f+'?v=20261109'); if(!r.ok)throw new Error('população '+r.status); return r.json();
    })).then(([meta,d])=>({meta,municipios:d.municipios,porId:new Map(d.municipios.map(m=>[m.uf+'-'+m.mun,m]))})).catch(e=>{promise=null;throw e;});
    return promise;
  }
  function tabela(headers, rows, label) {
    return el('div',{class:'pop-scroll',tabindex:'0',role:'region','aria-label':label}, el('table',{},
      el('thead',{},el('tr',{},headers.map(t=>el('th',{scope:'col'},t)))),
      el('tbody',{},rows.map(r=>el('tr',{},r.map((c,i)=>el(i?'td':'th',i?{}:{scope:'row'},c)))))));
  }
  function render(m, meta, {compact=false}={}) {
    if(!m)return el('p',{},'População municipal não disponível para este recorte.');
    const box=el('section',{class:'pop-painel','aria-label':'População e eleitorado do município'},
      el('p',{class:'pop-kicker'},'MUNICÍPIO INTEIRO · '+m.nome+' / '+m.uf),
      el('h2',{},'Moradores, eleitores e quem votou'),
      el('p',{class:'pop-intro'},'A população mora aqui; o cadastro reúne quem tem domicílio eleitoral aqui. São universos diferentes.'));
    const cards=[['População 16+ estimada',m.estimativa16,'Arvor · estrutura de 2022 × total IBGE '+meta.ano_estimativa],
      ['Eleitorado cadastrado',m.eleitorado,'TSE · 2026 · inscritos'],
      ['Comparecimento · 2º turno',m.comparecimento2,fmt(m.bu2)+' de '+fmt(m.secoes)+' seções com boletim']];
    box.append(el('div',{class:'pop-cards'},cards.map(([title,v,note])=>el('div',{},el('span',{},title),el('strong',{},fmt(v)),el('small',{},note)))));
    if(m.nota)box.append(el('p',{class:'pop-alerta'},m.nota));
    const comp=[['Eleitorado',m.eleitorado_por100,m.eleitorado_saldo],['Comparecimento · 1º turno',m.comparecimento1_por100,m.comparecimento1_saldo],['Comparecimento · 2º turno',m.comparecimento2_por100,m.comparecimento2_saldo]];
    box.append(tabela(['Em relação à população 16+ estimada','Por 100 moradores','Diferença em pessoas'],comp.map(([t,r,s])=>[t,fmt(r,1),signed(s)]),'Razões eleitorado e população'));
    box.append(el('p',{class:'pop-nota'},'100 significa tamanhos iguais. Acima de 100 há mais inscritos ou votantes do que moradores 16+ estimados. Isso não é uma taxa de participação dos residentes. Comparecimento incompleto é um mínimo observado.'));
    const comparar=el('details',{class:'pop-detalhes',open:!compact},el('summary',{},'Censo, estimativa recente e PNAD: conferir as bases'));
    comparar.append(tabela(['População municipal','Pessoas'],[['Censo 2022 · todas as idades',fmt(m.censo_total)],['Censo 2022 · 16+',fmt(m.censo16)],['IBGE '+meta.ano_estimativa+' · todas as idades',fmt(m.pop_total_recente)],['Arvor '+meta.ano_estimativa+' · 16+ estimada',fmt(m.estimativa16)],['Eleitorado / Censo 16+ de 2022',pct(rate(m.eleitorado,m.censo16))],['Aptos nos boletins · 1º / 2º turno',fmt(m.eleitorado_bu1)+' / '+fmt(m.eleitorado_bu2)]],'Bases populacionais'));
    comparar.append(el('p',{class:'pop-nota'},meta.metodo),el('p',{class:'pop-nota'},'Aptos dos boletins e inscritos no perfil cadastral podem diferir por data e cobertura. Boletins: '+fmt(m.bu1)+' / '+fmt(m.secoes)+' no 1º turno; '+fmt(m.bu2)+' / '+fmt(m.secoes)+' no 2º.'));
    const p=meta.pnad.ufs[m.uf];
    if(p)comparar.append(el('h3',{},'Referência estadual · '+m.uf+' inteira'),el('p',{},'PNAD Contínua · '+meta.pnad.trimestre+'º trimestre de '+meta.pnad.ano+': '+fmt(p.p16)+' moradores 16+ ('+pct(rate(p.p16,p.total))+' da população estadual). '+meta.pnad.universo),
      el('p',{class:'pop-nota'},'Não é medição deste município, nem intervalo de confiança da estimativa municipal. O cálculo usa o peso '+meta.pnad.peso+'.'));
    box.append(comparar);
    const perfil=el('details',{class:'pop-detalhes',open:!compact},el('summary',{},'Sexo e idade: cadastro × população 16+'));
    perfil.append(tabela(['Parcela entre pessoas 16+','TSE 2026','Censo municipal 2022','Diferença','PNAD da UF'],
      [['Sexo feminino','mulheres','mulheres16'],['16 a 24 anos','jovens','jovens16_24'],['60 anos ou mais','idosos','idosos60']].map(([t,k,pk])=>[t,pct(m[k+'_tse_pct']),pct(m[k+'_censo_pct']),signed(m[k+'_dif_pp'],' pp'),p?pct(rate(p[pk],p.p16)):'Sem dado']),'Diferenças de sexo e idade'));
    const v=m.tse_idade_sexo,c=m.censo_idade_sexo;
    if(v&&c)perfil.append(tabela(['Idade','TSE 2026','Censo 2022 · 16+','Diferença'],meta.faixas.slice(0,10).map((nome,i)=>{
      const t=rate(v.slice(i*3,i*3+3).reduce((a,b)=>a+b,0),m.eleitorado), p=rate(c[i][0]+c[i][1],m.censo16);
      return [nome,pct(t),pct(p),signed(num(t)&&num(p)?t-p:null,' pp')];
    }),'Distribuição etária comparada'));
    if(v)perfil.append(el('p',{class:'pop-nota'},'TSE: '+fmt(v.slice(30).reduce((a,b)=>a+b,0))+' sem idade informada; '+fmt(v.filter((_,i)=>i%3===2).reduce((a,b)=>a+b,0))+' sem sexo informado. Mantidos no denominador. Sexo cadastral não é identidade de gênero. As comparações têm datas diferentes; não descrevem quem compareceu.'));
    box.append(perfil);
    box.append(el('details',{class:'pop-detalhes'},el('summary',{},'O que pode explicar uma diferença?'),el('ul',{},meta.limites.map(t=>el('li',{},t))),
      el('p',{},el('a',{href:'https://www.tse.jus.br/servicos-eleitorais/titulo-eleitoral/titulo-eleitoral-faq',target:'_blank',rel:'noopener'},'O TSE explica os vínculos admitidos para domicílio eleitoral.')),
      el('p',{},'Para investigar: conferir o cadastro e suas revisões, migração e crescimento local, limites territoriais e cobertura dos boletins. Os dados aqui não isolam essas causas.')));
    box.append(el('nav',{class:'pop-links','aria-label':'Fontes da população'},
      el('a',{href:'https://sidra.ibge.gov.br/tabela/9514',target:'_blank',rel:'noopener'},'Censo 2022'),
      el('a',{href:'https://sidra.ibge.gov.br/tabela/6579',target:'_blank',rel:'noopener'},'Estimativa IBGE'),
      el('a',{href:BASE+'indice.json'},'Método, fontes e hashes'),el('a',{href:BASE+'municipios.csv',download:''},'Baixar municípios (CSV)')));
    return box;
  }
  function painel({uf,mun,local,compact=false}) {
    if(local) [uf,mun]=local.split('-');
    const box=el('section',{class:'pop-carregando','aria-busy':'true'},el('p',{role:'status'},'Carregando população e eleitorado…'));
    if(uf==='ZZ'||!mun){box.replaceChildren(el('p',{},uf==='ZZ'?'Exterior: não há população municipal brasileira comparável.':'A população é municipal; selecione um município inteiro.'));box.removeAttribute('aria-busy');return box;}
    const load=()=>dados().then(({meta,porId})=>box.replaceChildren(render(porId.get(uf+'-'+String(mun).padStart(5,'0')),meta,{compact}))).catch(()=>{
      const retry=el('button',{type:'button'},'Tentar novamente');retry.onclick=load;
      box.replaceChildren(el('p',{role:'status'},'Não foi possível carregar a comparação populacional.'),retry);
    }).finally(()=>box.removeAttribute('aria-busy'));
    load();return box;
  }
  window.PolitizePopulacao={dados,painel,render,fmt,pct,signed,num,rate,el};
})();
