/* Sinesp: UF explícita em toda apresentação; não é estatística do prédio. */
(function(root){
  'use strict';
  let promise;
  const fmt=(v,d=1)=>typeof v==='number'?v.toLocaleString('pt-BR',{maximumFractionDigits:d}):'Sem dado';
  function el(tag,attrs={},...cs){const n=document.createElement(tag);Object.entries(attrs).forEach(([k,v])=>n.setAttribute(k,v));cs.flat(Infinity).forEach(c=>{if(c!==null&&c!==undefined)n.append(c instanceof Node?c:String(c));});return n;}
  function dados(){if(!promise){promise=fetch('assets/politize_se/crimes/dados.json?v=20261029-perfil1').then(r=>{if(!r.ok)throw new Error('Crimes indisponíveis');return r.json();});promise.catch(()=>{promise=null;});}return promise;}
  function render(d,uf){
    const u=d.ufs[uf],box=el('div',{},el('p',{class:'perfil-kicker'},'SINESP · 2025 · ESTADO INTEIRO'),el('h3',{},'Outros crimes registrados'));
    if(!u){box.append(el('p',{},'Esta base não cobre o exterior.'));return box;}
    box.append(el('p',{class:'crime-escopo'},`${u.nome} (${uf}) · população: ${fmt(u.populacao,0)}. Dados estaduais, não deste município ou local de votação.`));
    box.append(el('div',{class:'crime-indice'},el('div',{},el('span',{},'Índice de registros criminais'),el('b',{},fmt(u.indice),el('small',{},' / 100'))),el('span',{class:'crime-experimental'},'Experimental · UF')));
    const table=el('table',{},el('thead',{},el('tr',{},['Indicador','Registros','Por 100 mil'].map(t=>el('th',{scope:'col'},t)))),el('tbody',{},Object.entries(d.metricas).map(([k,m])=>{const r=u.indicadores[k];return el('tr',{},el('th',{scope:'row'},m.nome,el('small',{},m.unidade+(r.completo?' · 12 meses':` · cobertura incompleta (${r.meses}/12 meses)`))),el('td',{},fmt(r.n,0)),el('td',{},fmt(r.taxa,2)));})));
    box.append(el('div',{class:'crime-tabela',tabindex:0,role:'region','aria-label':'Registros estaduais de segurança pública'},table));
    const details=el('details',{},el('summary',{},'Como o índice é calculado e fontes'));
    details.append(el('p',{},d.metodo_indice.formula),el('table',{},el('thead',{},el('tr',{},['Componente','Peso','Nota'].map(t=>el('th',{},t)))),el('tbody',{},d.metodo_indice.componentes.map(k=>el('tr',{},el('th',{scope:'row'},d.metricas[k].nome),el('td',{},'20%'),el('td',{},fmt(u.componentes_indice[k])))))));
    details.append(el('p',{},`${d.metodo_indice.ufs_completas} UFs com todos os componentes completos. A nota é posição relativa entre essas UFs; não é percentual de vítimas nem probabilidade de crime.`),d.limites.map(t=>el('p',{},t)),el('ul',{},d.fontes.map(f=>el('li',{},el('a',{href:f.url,target:'_blank',rel:'noopener'},f.nome)))));
    box.append(el('p',{class:'perfil-nota'},'Roubo e furto referem-se a veículos. Tráfico também reflete atividade policial; registros dependem de denúncia e classificação. Índice descritivo, não risco individual.'),details);
    return box;
  }
  function painel(uf){const box=el('section',{class:'crimes-painel','aria-label':'Crimes registrados na UF','aria-busy':'true'});const carregar=async()=>{box.replaceChildren(el('p',{role:'status'},'Carregando registros estaduais…'));try{box.replaceChildren(render(await dados(),uf));}catch{const b=el('button',{type:'button'},'Tentar novamente');b.onclick=carregar;box.replaceChildren(el('p',{},'Os dados estaduais não carregaram.'),b);}finally{box.setAttribute('aria-busy','false');}};carregar();return box;}
  root.PolitizeCrimes={dados,painel,render};
})(window);
