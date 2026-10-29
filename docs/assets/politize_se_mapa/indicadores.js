/* Idade/sexo cadastrais e crimes estaduais, mantendo suas unidades separadas. */
window.criarIndicadoresMapa=function({S,COR,H,h,nf0}){
  const perfil=window.PolitizePerfil, resumos=new Map(), completos=new Map();let crimes;
  const demografia={mulheres:['Sexo feminino no cadastro','perfil_feminino_pct',1,35,65,['#247b80','#ba7639']],jovens:['Eleitores de 16 a 24 anos','perfil_jovens_pct',2,0,30,['#f1e9d2','#247b80']],idosos:['Eleitores de 60 anos ou mais','perfil_idosos_pct',3,5,50,['#f3e6d7','#97521f']]};
  const ativo=()=>Object.hasOwn(demografia,S.camada)||S.camada.startsWith('crime_');
  const demografica=()=>Object.hasOwn(demografia,S.camada);
  async function instalar(){
    for(const[k,[nome,campo,,minimo,maximo,paleta]]of Object.entries(demografia)){
      S.meta.camadas[k]={nome,campo,tipo:'sequencial',minimo,maximo,baixo:minimo+'%',alto:maximo+'%',grupo:'Perfil do eleitorado',explica:'TSE 2026: percentuais sobre os inscritos, incluindo não informados no denominador. Sexo cadastral, não identidade de gênero. Não identifica quem compareceu ou como votou.'};COR[k]=paleta;
    }
    try{crimes=await window.PolitizeCrimes.dados();}catch{crimes=null;}
    if(!crimes)return;
    for(const[k,m]of Object.entries(crimes.metricas)){
      const vs=Object.values(crimes.ufs).map(u=>u.indicadores[k].taxa).filter(v=>v!==null).sort((a,b)=>a-b), max=vs[Math.floor((vs.length-1)*.95)]||1;
      S.meta.camadas['crime_'+k]={nome:m.nome+' · UF · 2025',campo:'crime_'+k,tipo:'sequencial',minimo:0,maximo:max,baixo:'0',alto:max.toLocaleString('pt-BR',{maximumFractionDigits:1})+'+',grupo:'Crimes registrados · UF',explica:'Taxa por 100 mil habitantes, Sinesp 2025 / população IBGE 2025. Registros do estado inteiro, não do município, seção ou prédio. Grupos com várias UFs somam registros e população uma vez por UF. A cor satura no percentil 95 das taxas estaduais.'};COR['crime_'+k]=['#f4e5b9','#8c2744'];
    }
    S.meta.camadas.crime_indice={nome:'Índice de registros criminais · UF',campo:'crime_indice',tipo:'sequencial',minimo:0,maximo:100,baixo:'0',alto:'100',grupo:'Crimes registrados · UF',explica:crimes.metodo_indice.formula+' Experimental, não oficial; não mede risco individual. Grupos com várias UFs usam a média simples dos índices estaduais, uma vez por UF.'};COR.crime_indice=['#f4e5b9','#8c2744'];
  }
  async function carregar(ufs){
    await Promise.all(ufs.map(async uf=>{
      try{resumos.set(uf,await perfil.dados(uf,true));if(H.ativo())completos.set(uf,await perfil.dados(uf));}catch{resumos.delete(uf);completos.delete(uf);}
    }));
  }
  function stats(l){
    if(l.horario){const d=completos.get(l.uf);return d?perfil.estatisticas(perfil.somar(perfil.selecionar(d,{local:l.id,secoes:l.secoes}))):null;}
    return resumos.get(l.uf)?.locais[l.id]||null;
  }
  function aplicar(ls){
    for(const l of ls){const r=stats(l);l.perfil_stats=r;l.perfil_total=r?.[0]||null;
      for(const[, [,campo,i]]of Object.entries(demografia))l[campo]=r?.[0]?100*r[i]/r[0]:null;
      const u=crimes?.ufs[l.uf];l.crime_indice=u?.indice??null;
      for(const k of Object.keys(crimes?.metricas||{}))l['crime_'+k]=u?.indicadores[k].taxa??null;
    }return ls;
  }
  function grupo(ls){
    if(demografica()){const i=demografia[S.camada][2],rs=ls.map(l=>l.perfil_stats).filter(r=>r?.[0]),n=rs.reduce((s,r)=>s+r[0],0);return n?100*rs.reduce((s,r)=>s+r[i],0)/n:null;}
    const ufs=[...new Set(ls.map(l=>l.uf))].map(uf=>crimes?.ufs[uf]).filter(Boolean);
    if(S.camada==='crime_indice'){const vs=ufs.map(u=>u.indice).filter(v=>v!==null);return vs.length?vs.reduce((a,b)=>a+b,0)/vs.length:null;}
    const k=S.camada.slice(6),valid=ufs.filter(u=>u.indicadores[k]?.taxa!==null);return valid.length?100000*valid.reduce((s,u)=>s+u.indicadores[k].n,0)/valid.reduce((s,u)=>s+u.populacao,0):null;
  }
  function legenda(){
    if(!ativo())return false;
    const c=S.meta.camadas[S.camada],paleta=COR[S.camada],demo=demografica(),indice=S.camada==='crime_indice';
    document.querySelector('#mapa-escala').replaceChildren(h('b',{},c.nome),h('span',{class:'mapa-mini-escala',style:`background:linear-gradient(90deg,${paleta.join(',')})`}),h('span',{},c.baixo+' → '+c.alto),h('small',{},demo?'% dos inscritos · TSE 2026 · cinza: sem perfil':indice?'Experimental · 2025 · estado inteiro':'Por 100 mil habitantes · estado inteiro'));
    document.querySelector('#legenda').replaceChildren(h('p',{},c.explica),h('p',{},demo?'Nos grupos, somamos os inscritos e recalculamos o percentual. Com filtro de horário, consideramos o perfil cadastral das seções selecionadas.':'Não é uma medida do bairro ou do local de votação. Ausência ou cobertura incompleta ficam sem taxa; não viram zero.'),demo?h('a',{href:'assets/politize_se/perfil/indice.json'},'Fonte e cobertura do perfil'):h('a',{href:'assets/politize_se/crimes/dados.json'},'Dados, componentes e fontes'));
    return true;
  }
  function texto(l){const v=l[S.meta.camadas[S.camada].campo],t=typeof v==='number'?v.toLocaleString('pt-BR',{maximumFractionDigits:1}):'Sem dado';return S.meta.camadas[S.camada].nome+': '+t+(demografica()?'% dos inscritos':S.camada==='crime_indice'?' / 100 · estado inteiro':' / 100 mil · estado inteiro');}
  const colunas=()=>[[S.meta.camadas[S.camada].campo,S.meta.camadas[S.camada].nome]];
  const celula=l=>h('td',{class:'num'},l[S.meta.camadas[S.camada].campo]===null?'Sem dado':l[S.meta.camadas[S.camada].campo].toLocaleString('pt-BR',{maximumFractionDigits:1})+(demografica()?'%':''),h('small',{},demografica()?(l.perfil_total?nf0.format(l.perfil_total)+' inscritos':'Sem perfil'):l.uf+' · estado inteiro'));
  const colunasCsv=['perfil_inscritos','perfil_feminino_pct','perfil_jovens_16_24_pct','perfil_idosos_60_mais_pct','crime_indice_uf_2025',...['homicidio_doloso','trafico','roubo_veiculo','furto_veiculo','estupro','estupro_vulneravel','roubo_carga','roubo_banco','feminicidio'].map(k=>'crime_'+k+'_uf_2025_por_100mil')];
  const csv=l=>[l.perfil_total,l.perfil_feminino_pct,l.perfil_jovens_pct,l.perfil_idosos_pct,l.crime_indice,...['homicidio_doloso','trafico','roubo_veiculo','furto_veiculo','estupro','estupro_vulneravel','roubo_carga','roubo_banco','feminicidio'].map(k=>l['crime_'+k])].map(v=>typeof v==='number'?String(v).replace('.',','):v);
  return{instalar,carregar,aplicar,grupo,legenda,ativo,texto,colunas,celula,colunasCsv,csv};
};
