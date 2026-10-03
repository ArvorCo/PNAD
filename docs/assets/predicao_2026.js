/* Pure scenario engine mirrors scripts/predicao_2026/motor.py. */
const Prediction2026 = (() => {
  "use strict";
  const keys = ["lula", "flavio", "outros"];
  const defaults = {base:"central_inclinacao",voto_lula:0,voto_flavio:0,indecisos_validos:1,
    indecisos_flavio:null,comparecimento_pp:0,branco_nulo_pp:0,diferencial_pp:0,
    vies_pp:0,secoes_abstencao_pp:0,eleitor_provavel:true,exterior:true,
    comparecimento_modelo:"uf",regioes:{},ufs:{}};
  const sum = a => a.reduce((x,y) => x+y,0);
  const clip = (x,lo,hi) => Math.max(lo,Math.min(hi,x));
  const norm = a => {const total=sum(a); if(!(total>0)||a.some(x=>!Number.isFinite(x)||x<0))throw Error("Massa inválida");return a.map(x=>x/total);};
  function rates(mass,target,diff) {
    const offsets=[-diff/2,diff/2,0,0];let lo=-1,hi=1;
    for(let i=0;i<50;i++){const mid=(lo+hi)/2;
      const total=sum(mass.map((m,k)=>m*clip(target+offsets[k]+mid,0,1)));
      if(total<target)lo=mid;else hi=mid;}
    return offsets.map(x=>clip(target+x+(lo+hi)/2,0,1));
  }
  function state(s,params={},vector=null,turnout=null) {
    const p={...defaults,...params};
    for(const k of ["voto_lula","voto_flavio","indecisos_validos"])
      if(!(p[k]>=0&&p[k]<=1))throw Error("Parâmetro fora dos limites: "+k);
    const q=(vector||s.bases[p.base]).slice();let pi=norm(q.slice(0,3));
    if(p.eleitor_provavel)pi=norm(pi.map((v,k)=>v*s.eleitor_provavel_fatores[k]));
    const local=p.ufs[s.uf]||{},useful=[local.voto_lula??p.voto_lula,local.voto_flavio??p.voto_flavio];
    if(useful.some(x=>!(x>=0&&x<=1)))throw Error("Voto útil da UF fora dos limites");
    const requested=useful.map((x,k)=>x*s.reserva[k]);
    const factor=sum(requested)>0?Math.min(1,pi[2]/sum(requested)):1;
    const moved=requested.map(v=>v*factor);
    pi[0]+=moved[0];pi[1]+=moved[1];pi[2]=Math.max(0,pi[2]-sum(moved));
    const undecided=q[3]/Math.max(1e-9,1-q[4]);let destination=pi.slice();
    if(p.indecisos_flavio!==null){if(!(p.indecisos_flavio>=0&&p.indecisos_flavio<=1))throw Error("Destino inválido");destination=[1-p.indecisos_flavio,p.indecisos_flavio,0];}
    pi=norm(pi.map((v,k)=>(1-undecided)*v+undecided*p.indecisos_validos*destination[k]));
    const transfer=clip(p.vies_pp/200,-pi[1],pi[0]);pi[0]-=transfer;pi[1]+=transfer;
    const region=p.regioes[s.regiao]||{},uf=p.ufs[s.uf]||{};
    const high=sum(s.tse.bins.filter(b=>b.abstencao_historica_pct>=30).map(b=>b.eleitores_2026))/s.eleitorado;
    const baseTurnout=p.comparecimento_modelo==="secoes"?s.comparecimento_secoes:s.comparecimento;
    const tau=clip((turnout===null?baseTurnout:turnout)+(p.comparecimento_pp+(region.comparecimento_pp||0)+(uf.comparecimento_pp||0)+high*p.secoes_abstencao_pp)/100,0,1);
    let invalid=clip(s.branco_nulo+(p.branco_nulo_pp+(uf.branco_nulo_pp||0))/100,0,1);
    invalid+=(1-invalid)*undecided*(1-p.indecisos_validos);
    const mass=[...pi.map(v=>v*(1-invalid)),invalid];
    const differential=(p.diferencial_pp+(uf.diferencial_pp||0))/100;
    const r=differential?rates(mass,tau,differential):[tau,tau,tau,tau];
    const ballots=mass.map((v,k)=>s.eleitorado*v*r[k]);
    const attendance=sum(ballots),valid=sum(ballots.slice(0,3));
    return {uf:s.uf,regiao:s.regiao,eleitorado:s.eleitorado,lula:ballots[0],flavio:ballots[1],outros:ballots[2],
      branco_nulo:ballots[3],comparecimento:attendance,abstencao:s.eleitorado-attendance,validos:valid,
      taxas_por_preferencia:r,demais:Object.fromEntries(["renan_santos","cury","caiado","zema","restantes"].map((k,i)=>[k,ballots[2]*s.outros_composicao[i]]))};
  }
  function aggregate(rows) {
    const fields=["eleitorado","comparecimento","abstencao","branco_nulo",...keys];
    const out=Object.fromEntries(fields.map(k=>[k,sum(rows.map(r=>r[k]))]));
    out.validos=sum(keys.map(k=>out[k]));
    out.percentuais=Object.fromEntries(keys.map(k=>[k,out.validos?100*out[k]/out.validos:0]));
    out.margem_flavio_lula=out.percentuais.flavio-out.percentuais.lula;
    out.demais=Object.fromEntries(["renan_santos","cury","caiado","zema","restantes"].map(k=>[k,sum(rows.map(r=>r.demais[k]))]));
    return out;
  }
  function scenario(states,params={}) {
    const p={...defaults,...params};const rows=states.filter(s=>p.exterior||s.uf!=="ZZ").map(s=>state(s,p));
    const regions=Object.fromEntries([...new Set(rows.map(r=>r.regiao))].sort().map(k=>[k,aggregate(rows.filter(r=>r.regiao===k))]));
    return {parametros:p,brasil:aggregate(rows),regioes:regions,ufs:rows};
  }
  function random(seed) {
    let x=seed>>>0;return ()=>{x+=0x6D2B79F5;let t=x;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return ((t^(t>>>14))>>>0)/4294967296;};
  }
  function sampler(seed) {
    const r=random(seed);let spare=null;
    function normal(){if(spare!==null){const v=spare;spare=null;return v;}let u,v,s;
      do{u=2*r()-1;v=2*r()-1;s=u*u+v*v;}while(s>=1||s===0);
      const f=Math.sqrt(-2*Math.log(s)/s);spare=v*f;return u*f;}
    function gamma(a){if(a<1)return gamma(a+1)*Math.pow(Math.max(r(),1e-16),1/a);
      const d=a-1/3,c=1/Math.sqrt(9*d);for(;;){const x=normal();let v=1+c*x;if(v<=0)continue;v=v*v*v;const u=r();
        if(u<1-.0331*x*x*x*x||Math.log(u)<.5*x*x+d*(1-v+Math.log(v)))return d*v;}}
    const dirichlet=a=>norm(a.map(x=>gamma(Math.max(x,1e-6))));
    const student=()=>normal()/Math.sqrt(sum(Array.from({length:5},()=>normal()**2))/5);
    return {normal,dirichlet,student};
  }
  function rake(seed,weights,target) {
    const q=seed.map(row=>norm(row.map(v=>Math.max(v,1e-9))));
    for(let iteration=0;iteration<1000;iteration++) {
      const current=target.map((_,k)=>sum(q.map((row,s)=>weights[s]*row[k])));
      for(let s=0;s<q.length;s++){for(let k=0;k<target.length;k++)q[s][k]*=current[k]>0?target[k]/current[k]:0;q[s]=norm(q[s]);}
      const error=Math.max(...target.map((v,k)=>Math.abs(v-sum(q.map((row,s)=>weights[s]*row[k])))));
      if(error<1e-8)return q;
    }
    throw Error("Calibração não convergiu");
  }
  const quantile=(a,p)=>{const i=(a.length-1)*p;const lo=Math.floor(i);return a[lo]+(a[Math.ceil(i)]-a[lo])*(i-lo);};
  async function simulate(data,params,progress=()=>{},isCancelled=()=>false,runs=2000) {
    const p={...defaults,...params},rng=sampler(20261003);
    const polls=["pnad","publicado"].includes(p.base)?data.nacional.pareadas:data.nacional.selecionadas;
    // Toda âncora calculada sobre as casas centrais (dinâmica, tendência, central com inclinação) reutiliza
    // o bootstrap da central, recentrado por alvos[base] − alvos.inclusivo. Espelho de motor.bootstrap_design.
    const kind=p.base==="pnad"?"pnad_vetor":["publicado","todas"].includes(p.base)?"publicado_vetor":"previsao_vetor";
    const alvos=data.nacional.alvos;
    const shift=kind==="previsao_vetor"&&p.base!=="sem_recencia"&&alvos[p.base]?alvos[p.base].map((v,k)=>v-alvos.inclusivo[k]):null;
    // Desvio da projeção (motor.projection_sd), somado em quadratura ao erro comum de 2 pp na diferença F−L.
    const projection=["central_inclinacao","tendencia"].includes(p.base)?((data.nacional.incerteza_projecao_pp||{})[p.base]||0):0;
    const commonSd=Math.hypot(2,projection);
    const temporal=norm(polls.map(poll=>p.base==="sem_recencia"?1:poll.peso_recencia));
    const domestic=data.estados.filter(s=>s.uf!=="ZZ"),exterior=data.estados.find(s=>s.uf==="ZZ");
    const weights=norm(domestic.map(s=>s.eleitorado)),regions=[...new Set(domestic.map(s=>s.regiao))].sort();
    const pcts=keys.map(()=>[]),gaps=[];
    for(let run=0;run<runs;run++) {
      if(isCancelled())return null;
      const hw=rng.dirichlet(temporal.map(w=>w*polls.length));
      const ps=polls.map(poll=>rng.dirichlet(poll[kind].map(x=>Math.max(x,1e-6)*Math.min(poll.n,2000)/1.5)));
      const target=Array.from({length:5},(_,k)=>sum(ps.map((v,h)=>hw[h]*v[k])));
      if(shift)norm(target.map((v,k)=>Math.max(v+shift[k],1e-6))).forEach((v,k)=>{target[k]=v;});
      const common=rng.student()*Math.sqrt(3/5)*commonSd/200*sum(target.slice(0,3));
      const t=clip(common,-target[1],target[0]);target[0]-=t;target[1]+=t;
      const seeds=domestic.map(s=>rng.dirichlet(s.bases[p.base].map(x=>Math.max(x,1e-6)*Math.max(s.n_efetivo_assumido,150))));
      const q=rake(seeds,weights,target);
      const regionVote=regions.map(()=>rng.normal()*.01),regionTurnout=regions.map(()=>rng.normal()*.015);
      const commonTurnout=rng.normal()*.01,commonInvalid=rng.normal()*.008;
      const rows=domestic.map((s,i)=>{
        const ri=regions.indexOf(s.regiao);let pi=norm(q[i].slice(0,3));
        if(p.eleitor_provavel)pi=norm(pi.map((v,k)=>v*s.eleitor_provavel_fatores[k]));
        const d=clip(regionVote[ri]/2,-pi[1],pi[0]);pi[0]-=d;pi[1]+=d;
        const v=[...pi.map(x=>x*sum(q[i].slice(0,3))),...q[i].slice(3)];
        const base=p.comparecimento_modelo==="secoes"?s.comparecimento_secoes:s.comparecimento;
        const tau=clip(base+commonTurnout+regionTurnout[ri]+rng.normal()*.01,0,1);
        return state({...s,branco_nulo:clip(s.branco_nulo+commonInvalid,0,1)},{...p,eleitor_provavel:false},v,tau);
      });
      if(p.exterior&&exterior){const pi=rng.dirichlet(exterior.bases[p.base].slice(0,3).map(x=>Math.max(x,1e-6)*60));
        const v=[...pi.map(x=>x*sum(exterior.bases[p.base].slice(0,3))),...exterior.bases[p.base].slice(3)];
        const tau=clip(exterior.comparecimento+rng.normal()*.05,0,1);rows.push(state(exterior,p,v,tau));}
      const total=aggregate(rows);keys.forEach((k,i)=>pcts[i].push(total.percentuais[k]));gaps.push(total.margem_flavio_lula);
      if((run+1)%100===0){progress(run+1,runs);await new Promise(resolve=>setTimeout(resolve,0));}
    }
    pcts.forEach(a=>a.sort((a,b)=>a-b));gaps.sort((a,b)=>a-b);
    return {runs,intervalos:Object.fromEntries(keys.map((k,i)=>[k,[quantile(pcts[i],.05),quantile(pcts[i],.5),quantile(pcts[i],.95)]])),
      margem:[quantile(gaps,.05),quantile(gaps,.95)],margens:gaps,erro_comum_total_sd_pp:commonSd,p_flavio_a_frente_de_lula:gaps.filter(x=>x>0).length/runs,
      p_lula_maioria:pcts[0].filter(x=>x>50).length/runs,p_flavio_maioria:pcts[1].filter(x=>x>50).length/runs};
  }
  return {defaults,state,aggregate,scenario,rake,simulate};
})();
/* Utilidades puras do simulador: link do cenário, frase e histograma. Não alteram o motor. */
const PredictionSimulator = (() => {
  "use strict";
  // Referência do link e da frase: a central gravada em central.parametros (configure), não os defaults crus.
  let D={...Prediction2026.defaults};
  function configure(central={}){D={...Prediction2026.defaults,...central};return D;}
  const SCALAR=[["base","a","text"],["comparecimento_modelo","c","text"],["voto_flavio","vf","pct"],["voto_lula","vl","pct"],
    ["comparecimento_pp","cp","num"],["diferencial_pp","df","num"],["secoes_abstencao_pp","sa","num"],["branco_nulo_pp","bn","num"],
    ["vies_pp","ec","num"],["indecisos_validos","iv","pct"],["indecisos_flavio","if","pct"],["eleitor_provavel","ep","bool"],["exterior","ex","bool"]];
  const REGIONS={"Norte":"N","Nordeste":"NE","Centro-Oeste":"CO","Sudeste":"SE","Sul":"S"};
  const UF_FIELDS=[["comparecimento_pp","cp","num"],["diferencial_pp","df","num"],["voto_lula","vl","pct"],["voto_flavio","vf","pct"]];
  const ANCHORS={central_inclinacao:"âncora com tendência de 28 dias encolhida",inclusivo:"âncora de recência sem tendência (central até 03/10 à tarde)",sem_recencia:"âncora nacional com peso temporal igual",pnad:"âncora só nas casas reponderadas pela PNAD",
    publicado:"âncora nos placares publicados das casas PNAD",todas:"âncora em todas as casas publicadas",
    casas:"âncora sem o desvio relativo das casas",dinamico:"âncora nacional dinâmica",
    tendencia:"âncora de tendência projetada a 04/10",tendencia_corte:"âncora de tendência no nível do corte"};
  const clip=(x,lo,hi)=>Math.max(lo,Math.min(hi,x));
  const short=x=>String(+Number(x).toFixed(4));
  const same=(a,b)=>a===b||(typeof a==="number"&&typeof b==="number"&&Math.abs(a-b)<1e-9);
  const num=(x,d=1)=>Number(x).toLocaleString("pt-BR",{minimumFractionDigits:d,maximumFractionDigits:d});
  const plain=x=>Number(x).toLocaleString("pt-BR",{maximumFractionDigits:2});
  function signed(x,d=2){const r=Number(Number(x).toFixed(d));return r===0?num(0,d):(r>0?"+":"−")+num(Math.abs(r),d);}
  function code(kind,x){return kind==="pct"?short(100*x):kind==="bool"?(x?"1":"0"):kind==="num"?short(x):String(x);}
  function encode(params={}) {
    const p={...D,...params},out=[];
    for(const [k,c,kind] of SCALAR){if(same(p[k],D[k])||p[k]===undefined)continue;
      // Nulo só aparece quando a central tem valor: "if:p" = indecisos proporcionais.
      if(p[k]===null){if(D[k]!==null)out.push(c+":p");continue;}
      out.push(c+":"+code(kind,p[k]));}
    for(const [name,c] of Object.entries(REGIONS)){const v=((p.regioes||{})[name]||{}).comparecimento_pp;
      if(Number.isFinite(v)&&v!==0)out.push("r"+c+":"+short(v));}
    for(const uf of Object.keys(p.ufs||{}).sort()){const e=p.ufs[uf]||{};
      const parts=UF_FIELDS.filter(([k])=>Number.isFinite(e[k])&&(k.startsWith("voto_")||e[k]!==0)).map(([k,c,kind])=>c+code(kind,e[k]));
      if(parts.length)out.push(uf+":"+parts.join(","));}
    return out.join(";");
  }
  function decode(text="") {
    const p={...D,regioes:{},ufs:{}};
    for(const token of String(text).split(";")) {
      const i=token.indexOf(":");if(i<1)continue;
      const key=token.slice(0,i),raw=token.slice(i+1),x=Number(raw),ok=raw!==""&&Number.isFinite(x);
      const scalar=SCALAR.find(s=>s[1]===key);
      if(scalar){const [k,,kind]=scalar;
        if(kind==="text"){if(/^[a-z_]{1,24}$/.test(raw))p[k]=raw;}
        else if(raw==="p"&&k==="indecisos_flavio")p[k]=null;
        else if(ok)p[k]=kind==="bool"?x!==0:kind==="pct"?clip(x,0,100)/100:clip(x,-100,100);
        continue;}
      const region=Object.keys(REGIONS).find(n=>"r"+REGIONS[n]===key);
      if(region){if(ok&&x!==0)p.regioes[region]={comparecimento_pp:clip(x,-20,20)};continue;}
      if(/^[A-Z]{2}$/.test(key)){const e={};
        for(const part of raw.split(",")){const f=UF_FIELDS.find(([,c])=>part.startsWith(c)&&part.length>c.length);if(!f)continue;
          const y=Number(part.slice(f[1].length));if(!Number.isFinite(y))continue;
          const v=f[2]==="pct"?clip(y,0,100)/100:clip(y,-20,20);if(f[2]==="pct"||v!==0)e[f[0]]=v;}
        if(Object.keys(e).length)p.ufs[key]=e;}
    }
    return p;
  }
  const isCentral=params=>encode(params)==="";
  const list=a=>a.length<2?a.join(""):a.slice(0,-1).join(", ")+" e "+a[a.length-1];
  const more=(x,up,down)=>plain(Math.abs(x))+" pp "+(x>0?up:down);
  function ufSummary(e) {
    const out=[];
    if(e.comparecimento_pp)out.push("comparecimento "+signed(e.comparecimento_pp,1)+" pp");
    if(e.diferencial_pp)out.push("diferencial F−L "+signed(e.diferencial_pp,1)+" pp");
    if(Number.isFinite(e.voto_lula))out.push("reserva Lula "+plain(100*e.voto_lula)+"%");
    if(Number.isFinite(e.voto_flavio))out.push("reserva Flávio "+plain(100*e.voto_flavio)+"%");
    return out.join(", ");
  }
  function describe(params={}) {
    const p={...D,...params},out=[];
    if(p.voto_flavio>0)out.push("Flávio antecipando "+plain(100*p.voto_flavio)+"% da reserva");
    if(p.voto_lula>0)out.push("Lula antecipando "+plain(100*p.voto_lula)+"% da reserva");
    if(p.base!==D.base)out.push(ANCHORS[p.base]||"âncora nacional "+p.base);
    if(p.comparecimento_modelo!==D.comparecimento_modelo)out.push("comparecimento de partida pelas seções de 2022");
    if(p.comparecimento_pp)out.push("comparecimento "+more(p.comparecimento_pp,"maior","menor")+" em todo o país");
    const regions=Object.entries(p.regioes||{}).filter(([,v])=>v&&v.comparecimento_pp);
    const byValue={};regions.forEach(([r,v])=>(byValue[v.comparecimento_pp]=byValue[v.comparecimento_pp]||[]).push(r));
    for(const [v,names] of Object.entries(byValue))out.push("comparecimento "+more(Number(v),"maior","menor")+" "+list(names.map(n=>"no "+n)));
    if(p.diferencial_pp)out.push("eleitor de Flávio comparecendo "+more(p.diferencial_pp,"mais","menos")+" que o de Lula");
    if(p.secoes_abstencao_pp)out.push("comparecimento "+more(p.secoes_abstencao_pp,"maior","menor")+" nas seções de alta abstenção");
    if(p.vies_pp)out.push("erro comum de "+plain(Math.abs(p.vies_pp))+" pp a favor de "+(p.vies_pp>0?"Flávio":"Lula"));
    if(p.branco_nulo_pp)out.push("brancos e nulos "+more(p.branco_nulo_pp,"acima","abaixo")+" da central");
    if(p.indecisos_validos!==D.indecisos_validos)out.push(p.indecisos_validos===0?"nenhum indeciso chegando a voto válido":plain(100*p.indecisos_validos)+"% dos indecisos chegando a voto válido");
    if(!same(p.indecisos_flavio,D.indecisos_flavio))out.push(p.indecisos_flavio===null||p.indecisos_flavio===undefined?"indecisos que escolhem proporcionais às candidaturas":"indecisos que escolhem divididos "+plain(100-100*p.indecisos_flavio)+"/"+plain(100*p.indecisos_flavio)+" entre Lula e Flávio");
    if(!p.eleitor_provavel)out.push("sem o ajuste de eleitor provável");
    if(!p.exterior)out.push("sem o exterior");
    const ufs=Object.keys(p.ufs||{}).sort();
    if(ufs.length)out.push("ajuste local em "+(ufs.length>4?ufs.slice(0,4).join(", ")+" e mais "+(ufs.length-4)+" UFs":list(ufs)));
    return out;
  }
  function sentence(params,central,current,note) {
    const clauses=describe(params),a=central.margem_flavio_lula,b=current.margem_flavio_lula;
    const leader=x=>Number(x.toFixed(2))>0?"Flávio":Number(x.toFixed(2))<0?"Lula":null;
    if(!clauses.length)return "Sem hipóteses do leitor: cenário central do modelo, com diferença F−L de "+signed(b)+" pp nos votos válidos.";
    let s="Com "+list(clauses)+", a diferença F−L "+(Math.abs(b-a)<.005?"fica em "+signed(b)+" pp":"passa de "+signed(a)+" para "+signed(b)+" pp")+".";
    const before=leader(a),after=leader(b);
    s+=after===null?" Os dois empatam nos votos válidos.":after===before?" "+after+" segue à frente nos votos válidos.":" "+after+" passa à frente nos votos válidos.";
    for(const [k,n] of [["lula","Lula"],["flavio","Flávio"]])if(current.percentuais[k]>50)s+=" "+n+" supera 50% dos válidos neste cenário.";
    return note?s+" "+note:s;
  }
  function histogram(values,point,bins=32) {
    const a=values.slice().sort((x,y)=>x-y),q=p=>a[Math.min(a.length-1,Math.max(0,Math.round((a.length-1)*p)))];
    let lo=Math.min(q(.005),point,0),hi=Math.max(q(.995),point,0);const pad=(hi-lo)*.04||1;lo-=pad;hi+=pad;
    const counts=new Array(bins).fill(0);for(const v of a)if(v>=lo&&v<=hi)counts[Math.min(bins-1,Math.floor((v-lo)/(hi-lo)*bins))]++;
    const peak=Math.max(...counts,1),W=600,L=20,R=580,x=v=>L+(R-L)*(v-lo)/(hi-lo),bw=(R-L)/bins;
    let svg='<svg viewBox="0 0 '+W+' 190" role="img" aria-label="Distribuição simulada da diferença Flávio menos Lula neste cenário" xmlns="http://www.w3.org/2000/svg">';
    svg+='<rect x="'+x(q(.05)).toFixed(1)+'" y="8" width="'+Math.max(1,x(q(.95))-x(q(.05))).toFixed(1)+'" height="132" fill="#e7eddf"/>';
    counts.forEach((c,i)=>{const h=124*c/peak,mid=lo+(i+.5)*(hi-lo)/bins;if(c)svg+='<rect x="'+(L+i*bw+.5).toFixed(1)+'" y="'+(140-h).toFixed(1)+'" width="'+(bw-1).toFixed(1)+'" height="'+h.toFixed(1)+'" fill="'+(mid>0?"#1457aa":"#b02f21")+'"/>';});
    svg+='<line x1="'+x(0).toFixed(1)+'" x2="'+x(0).toFixed(1)+'" y1="4" y2="146" stroke="#192e2b" stroke-dasharray="4 3"/>';
    svg+='<line x1="'+x(point).toFixed(1)+'" x2="'+x(point).toFixed(1)+'" y1="4" y2="146" stroke="#192e2b" stroke-width="2"/>';
    const anchor=v=>x(v)<120?"start":x(v)>480?"end":"middle";
    svg+='<text x="'+x(0).toFixed(1)+'" y="162" font-size="13" text-anchor="'+anchor(0)+'" fill="#192e2b">Empate</text>';
    svg+='<text x="'+x(point).toFixed(1)+'" y="182" font-size="13" text-anchor="'+anchor(point)+'" fill="#192e2b">Seu cenário: '+signed(point)+' pp</text>';
    svg+='<text x="'+L+'" y="20" font-size="12" fill="#535b54">Lula à frente</text><text x="'+R+'" y="20" font-size="12" text-anchor="end" fill="#535b54">Flávio à frente</text>';
    return svg+"</svg>";
  }
  return {configure,reference:()=>({...D}),encode,decode,isCentral,describe,sentence,ufSummary,histogram,signed};
})();
if(typeof module!=="undefined"&&module.exports){module.exports=Prediction2026;module.exports.Simulador=PredictionSimulator;}

if(typeof document!=="undefined") {
  (()=>{
    "use strict";
    const $=id=>document.getElementById(id);
    const root=$("simulador-app");if(!root||!$("prediction-data"))return;
    const data=JSON.parse($("prediction-data").textContent),S=PredictionSimulator;
    // A central da página é a gravada no JSON (âncora e destino dos indecisos), não os defaults do motor.
    const D=S.configure((data.central||{}).parametros||{});
    const presets=JSON.parse(($("sim-presets-data")||{textContent:"[]"}).textContent);
    const fmt=(n,d=1)=>n.toLocaleString("pt-BR",{minimumFractionDigits:d,maximumFractionDigits:d});
    const mi=n=>fmt(n/1e6,2)+" mi",K=["lula","flavio","outros"],names={lula:"Lula",flavio:"Flávio",outros:"Demais"};
    const votes=x=>{const a=Math.abs(x);return (x>0?"+":x<0?"−":"")+(a>=1e6?fmt(a/1e6,2)+" mi":fmt(a/1e3,0)+" mil");};
    const central=Prediction2026.scenario(data.estados,D);
    const known=new Set(data.estados.map(s=>s.uf));
    let edits={},revision=0,lastResult=central,lastParams={...D},running=false,cancelled=false,view="regiao",ready=false,mcShown=false;

    function outputs(){document.querySelectorAll("[data-param]").forEach(el=>{
      const v=Number(el.value),out=$("out-"+el.dataset.param);
      out.textContent=el.dataset.suffix==="%"?fmt(v,v%1?2:0)+"%":(v>0?"+":v<0?"−":"")+fmt(Math.abs(v),v%1?2:0)+" pp";
      el.closest(".ctl").classList.toggle("changed",v!==0);});}
    function clipInput(el,min,max){const x=Number(el.value);return el.value!==""&&Number.isFinite(x)?Math.max(min,Math.min(max,x)):0;}
    function params(){
      const p={...D,ufs:structuredClone(edits),regioes:{}};
      document.querySelectorAll("[data-param]").forEach(el=>{const k=el.dataset.param,v=Number(el.value);p[k]=k.startsWith("voto_")?v/100:v;});
      for(const k of ["base","comparecimento_modelo"])p[k]=$("param-"+k).value;
      p.indecisos_validos=Number($("param-indecisos_validos").value);
      p.indecisos_flavio=$("param-indecisos_flavio").value===""?null:Number($("param-indecisos_flavio").value);
      p.eleitor_provavel=$("param-eleitor_provavel").checked;p.exterior=$("param-exterior").checked;
      document.querySelectorAll("input[data-region]").forEach(el=>{p.regioes[el.dataset.region]={comparecimento_pp:clipInput(el,-20,20)};});
      return p;
    }
    function choose(select,value,label){const v=String(value);
      if(![...select.options].some(o=>o.value===v)){if(!label)return;const o=document.createElement("option");o.value=v;o.textContent=label;select.append(o);}
      select.value=v;}
    function setControls(input){
      const p={...D,...input};
      document.querySelectorAll("[data-param]").forEach(el=>{const k=el.dataset.param;el.value=String(k.startsWith("voto_")?100*p[k]:p[k]);});
      choose($("param-base"),D.base);choose($("param-base"),p.base);
      choose($("param-comparecimento_modelo"),D.comparecimento_modelo);choose($("param-comparecimento_modelo"),p.comparecimento_modelo);
      choose($("param-indecisos_validos"),p.indecisos_validos,fmt(100*p.indecisos_validos,0)+"%, do link");
      choose($("param-indecisos_flavio"),p.indecisos_flavio===null?"":p.indecisos_flavio,p.indecisos_flavio===null?"":fmt(100-100*p.indecisos_flavio,0)+"% Lula, "+fmt(100*p.indecisos_flavio,0)+"% Flávio, do link");
      $("param-eleitor_provavel").checked=!!p.eleitor_provavel;$("param-exterior").checked=!!p.exterior;
      document.querySelectorAll("input[data-region]").forEach(el=>{el.value=String(((p.regioes||{})[el.dataset.region]||{}).comparecimento_pp||0);});
      edits=Object.fromEntries(Object.entries(structuredClone(p.ufs||{})).filter(([uf])=>known.has(uf)));
      loadUf();
    }
    function loadUf(){const e=edits[$("uf-select").value]||{};$("uf-turnout").value=e.comparecimento_pp||0;$("uf-differential").value=e.diferencial_pp||0;
      for(const k of ["lula","flavio"])$("uf-useful-"+k).value=e["voto_"+k]===undefined?"":String(100*e["voto_"+k]);}
    function track(b,labels){const p=b.percentuais;
      return ["lula","outros","flavio"].map(k=>'<div class="seg '+k+'" style="width:'+p[k].toFixed(3)+'%">'+(labels&&k!=="outros"&&p[k]>9?"<b>"+fmt(p[k])+"%</b>":"")+"</div>").join("");}
    function bars(b){const c=central.brasil.percentuais;
      return '<div class="bar-row"><span class="bar-label">Cenário</span><div class="bar-track">'+track(b,true)+'<div class="bar-half"></div>'+
        '<div class="bar-mark" style="left:'+c.lula.toFixed(3)+'%"></div><div class="bar-mark" style="left:'+(100-c.flavio).toFixed(3)+'%"></div></div></div>'+
        '<div class="bar-row ghost"><span class="bar-label">Central</span><div class="bar-track thin">'+track(central.brasil,false)+'<div class="bar-half"></div></div></div>'+
        '<div class="bar-axis"><span>Lula</span><span>50% dos válidos</span><span>Flávio</span></div>';}
    function pct(r){const v=r.lula+r.flavio+r.outros;return Object.fromEntries(K.map(k=>[k,v?100*r[k]/v:0]));}
    function table(result){
      const byUf=view==="uf",centralRows=byUf?Object.fromEntries(central.ufs.map(r=>[r.uf,r])):central.regioes;
      const rows=byUf?result.ufs.slice().sort((a,b)=>b.eleitorado-a.eleitorado).map(r=>[r.uf,r]):Object.entries(result.regioes);
      const body=rows.map(([name,r])=>{const p=byUf?pct(r):r.percentuais,c=centralRows[name],cp=byUf?pct(c):c.percentuais,gap=p.flavio-p.lula,delta=gap-(cp.flavio-cp.lula);
        const edited=byUf&&edits[name]||(!byUf&&(lastParams.regioes[name]||{}).comparecimento_pp);
        return '<tr'+(edited?' class="edited"':"")+'><th scope="row">'+name+(edited?' <small>ajustada</small>':"")+"</th>"+K.map(k=>"<td>"+fmt(p[k])+"%<small>"+mi(r[k])+"</small></td>").join("")+
          "<td>"+S.signed(gap)+"</td><td"+(Math.abs(delta)>=.005?' class="moved"':"")+">"+S.signed(delta)+"</td></tr>";}).join("");
      return '<div class="table-scroll" tabindex="0" role="region" aria-label="Resultado do cenário por '+(byUf?"UF, ordenado por eleitorado":"região")+'"><table><thead><tr><th scope="col">'+(byUf?"UF":"Região")+
        '</th><th scope="col">Lula</th><th scope="col">Flávio</th><th scope="col">Demais</th><th scope="col">F−L, pp</th><th scope="col">Δ F−L vs central</th></tr></thead><tbody>'+body+"</tbody></table></div>";}
    function chips(p){
      const items=[];
      for(const [r,v] of Object.entries(p.regioes))if(v.comparecimento_pp)items.push(["region",r,r+": comparecimento "+S.signed(v.comparecimento_pp,1)+" pp"]);
      for(const uf of Object.keys(edits).sort())items.push(["uf",uf,uf+": "+S.ufSummary(edits[uf])]);
      $("uf-edits").innerHTML=items.length?items.map(([t,k,text])=>'<li class="chip"><span>'+text+'</span><button type="button" data-remove-'+t+'="'+k+'" aria-label="Remover ajuste de '+k+'">×</button></li>').join(""):'<li class="chip-empty">Nenhuma UF ou região alterada.</li>';}
    function writeHash(p){const c=S.encode(p),target=c?"#sim="+c:"";
      if(!c&&!location.hash.startsWith("#sim="))return;if(location.hash===target)return;
      try{history.replaceState(null,"",location.pathname+location.search+target);}catch(e){/* file:// sem histórico: o botão de link continua funcionando */}}
    function dispatch(){const detail={result:lastResult,params:lastParams,central:S.isCentral(lastParams)};window.predicaoCenario=detail;
      document.dispatchEvent(new CustomEvent("predicao:cenario",{detail}));}
    function update(){
      revision++;const p=params(),result=Prediction2026.scenario(data.estados,p);lastResult=result;lastParams=p;outputs();
      const b=result.brasil,c=central.brasil,isCentral=S.isCentral(p),code=S.encode(p);
      K.forEach(k=>{$("sim-"+k).textContent=fmt(b.percentuais[k])+"%";$("sim-votos-"+k).textContent=mi(b[k])+" votos";
        const dp=b.percentuais[k]-c.percentuais[k],dv=b[k]-c[k];
        $("sim-delta-"+k).textContent=Math.abs(dp)<.005&&Math.abs(dv)<500?"Igual à central":S.signed(dp)+" pp · "+votes(dv)+" votos vs central";});
      $("sim-bars").innerHTML=bars(b);
      $("sim-gap").textContent="Diferença F−L: "+S.signed(b.margem_flavio_lula)+" pp (central: "+S.signed(c.margem_flavio_lula)+" pp)";
      const active=presets.find(x=>S.encode(x.parametros)===code);
      $("sim-sentence").textContent=S.sentence(p,c,b,active&&active.nota);
      $("sim-attendance").textContent=mi(b.comparecimento)+" votantes";$("sim-absent").textContent=mi(b.abstencao)+" ausentes";$("sim-invalid").textContent=mi(b.branco_nulo)+" brancos/nulos";
      $("sim-region-table").innerHTML=table(result);
      $("sim-label").textContent=isCentral?"Cenário central":"Seu cenário condicional";
      root.classList.toggle("is-central",isCentral);
      document.querySelectorAll(".preset").forEach(el=>{const pr=presets.find(x=>x.id===el.dataset.preset);el.setAttribute("aria-pressed",String(!!pr&&S.encode(pr.parametros)===code));});
      chips(p);
      $("dock-lula").textContent=fmt(b.percentuais.lula)+"%";$("dock-flavio").textContent=fmt(b.percentuais.flavio)+"%";$("dock-gap").textContent="F−L "+S.signed(b.margem_flavio_lula)+" pp";
      if(!running){$("sim-mc-cards").hidden=true;$("sim-mc-hist").hidden=true;
        $("sim-uncertainty").textContent=mcShown?"As hipóteses mudaram. Simule de novo para ver a incerteza dos controles atuais.":"Os intervalos do topo pertencem à previsão central. Mudou hipótese? Simule novamente: são 2.000 sorteios no seu navegador.";}
      writeHash(p);
      if(ready)dispatch();
    }
    function fromHash(){if(!location.hash.startsWith("#sim="))return false;let raw=location.hash.slice(5);
      try{raw=decodeURIComponent(raw);}catch(e){/* fragmento malformado: lê como veio */}
      setControls(S.decode(raw));return true;}
    function scrollToSimulator(){const target=root.closest("section")||root;requestAnimationFrame(()=>target.scrollIntoView({block:"start"}));}

    root.addEventListener("input",e=>{const t=e.target;if(t.matches("[data-param],[data-region]"))update();
      else if(t.matches("#uf-turnout,#uf-differential,#uf-useful-lula,#uf-useful-flavio")){
        const uf=$("uf-select").value,c=clipInput($("uf-turnout"),-20,20),d=clipInput($("uf-differential"),-20,20),e2={};
        if(c)e2.comparecimento_pp=c;if(d)e2.diferencial_pp=d;
        for(const k of ["lula","flavio"]){const el=$("uf-useful-"+k);if(el.value!=="")e2["voto_"+k]=clipInput(el,0,100)/100;}
        if(Object.keys(e2).length)edits[uf]=e2;else delete edits[uf];update();}});
    root.addEventListener("change",e=>{const t=e.target;if(t.id==="uf-select")loadUf();else if(t.matches(".controls select,.controls input[type=checkbox]"))update();});
    root.addEventListener("click",e=>{
      const t=e.target.closest("button");if(!t)return;
      if(t.classList.contains("help-toggle")){const box=$(t.getAttribute("aria-controls")),open=t.getAttribute("aria-expanded")!=="true";box.hidden=!open;t.setAttribute("aria-expanded",String(open));}
      else if(t.dataset.preset){const pr=presets.find(x=>x.id===t.dataset.preset);if(pr){setControls(pr.parametros);update();}}
      else if(t.dataset.removeUf){delete edits[t.dataset.removeUf];loadUf();update();}
      else if(t.dataset.removeRegion){const el=root.querySelector('input[data-region="'+t.dataset.removeRegion+'"]');if(el)el.value="0";update();}
      else if(t.dataset.view){view=t.dataset.view;root.querySelectorAll("[data-view]").forEach(x=>x.setAttribute("aria-pressed",String(x===t)));$("sim-region-table").innerHTML=table(lastResult);}
      else if(t.id==="sim-reset"||t.id==="dock-reset"){setControls({});update();}
    });
    $("sim-share").addEventListener("click",async()=>{
      const c=S.encode(lastParams),url=location.href.split("#")[0]+(c?"#sim="+c:"#simulador"),field=$("sim-share-url");
      field.value=url;field.hidden=false;let ok=false;
      try{await navigator.clipboard.writeText(url);ok=true;}catch(e){field.select();try{ok=document.execCommand("copy");}catch(e2){ok=false;}}
      $("sim-share-status").textContent=ok?"Link copiado. Quem abrir verá estes mesmos controles.":"Copie o link acima; o navegador não permitiu a cópia automática.";});
    $("sim-export").addEventListener("click",()=>{
      const body={referencia:data.referencia,hash_modelo:data.hash_modelo,hipotese:"Cenário condicional do leitor, não previsão oficial da Arvor",link:S.encode(lastParams),...lastResult};
      const blob=new Blob([JSON.stringify(body,null,2)],{type:"application/json"}),url=URL.createObjectURL(blob),link=document.createElement("a");
      link.href=url;link.download="meu-cenario-presidente-2026.json";link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
    function cards(r){const card=(title,value,note)=>'<div class="mc-card"><span>'+title+"</span><b>"+value+"</b><small>"+note+"</small></div>";
      return K.map(k=>card(names[k]+", faixa de 90%",fmt(r.intervalos[k][0])+"% a "+fmt(r.intervalos[k][2])+"%","mediana "+fmt(r.intervalos[k][1])+"% dos válidos")).join("")+
        card("Diferença F−L, faixa de 90%",S.signed(r.margem[0])+" a "+S.signed(r.margem[1])+" pp","negativo: Lula à frente")+
        card("Flávio à frente de Lula",fmt(100*r.p_flavio_a_frente_de_lula)+"%","dos sorteios")+
        card("Acima de 50% dos válidos","Lula "+fmt(100*r.p_lula_maioria)+"% · Flávio "+fmt(100*r.p_flavio_maioria)+"%","dos sorteios");}
    $("sim-cancel").addEventListener("click",()=>{cancelled=true;});
    $("sim-montecarlo").addEventListener("click",async()=>{
      if(running)return;const version=revision,p=lastParams,point=lastResult.brasil.margem_flavio_lula,bar=$("sim-progress"),status=$("sim-uncertainty");
      running=true;cancelled=false;$("sim-montecarlo").disabled=true;$("sim-cancel").hidden=false;bar.hidden=false;bar.value=0;
      $("sim-mc-cards").hidden=true;$("sim-mc-hist").hidden=true;status.textContent="Simulando: 0 de 2.000 sorteios.";
      try{const r=await Prediction2026.simulate(data,p,(done,total)=>{bar.max=total;bar.value=done;status.textContent="Simulando: "+fmt(done,0)+" de "+fmt(total,0)+" sorteios.";},()=>cancelled||revision!==version);
        if(r){mcShown=true;$("sim-mc-cards").innerHTML=cards(r);$("sim-mc-cards").hidden=false;
          if(Array.isArray(r.margens)&&r.margens.length){$("sim-mc-hist").innerHTML=S.histogram(r.margens,point)+"<figcaption>Diferença F−L em "+fmt(r.runs,0)+" sorteios. Faixa clara: 90% centrais. Linha cheia: o seu cenário sem sorteio.</figcaption>";$("sim-mc-hist").hidden=false;}
          status.textContent="Faixas condicionais às hipóteses deste cenário, com "+fmt(r.runs,0)+" sorteios e parâmetros de erro assumidos; probabilidades não calibradas historicamente.";}
        else status.textContent=cancelled?"Simulação cancelada. O cenário continua o mesmo.":"Hipótese alterada durante a simulação. Simule novamente para os controles atuais.";
      }catch(error){status.textContent="Não foi possível concluir a simulação: "+error.message;}
      finally{running=false;$("sim-montecarlo").disabled=false;$("sim-cancel").hidden=true;bar.hidden=true;}
    });
    window.addEventListener("hashchange",()=>{if(fromHash()){update();scrollToSimulator();}});
    const restored=fromHash();update();if(restored)scrollToSimulator();
    const start=()=>{if(ready)return;ready=true;dispatch();};
    if(document.readyState==="complete")setTimeout(start,0);else{document.addEventListener("DOMContentLoaded",start,{once:true});window.addEventListener("load",start,{once:true});}
  })();
}
