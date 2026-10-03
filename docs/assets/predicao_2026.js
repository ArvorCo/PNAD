/* Pure scenario engine mirrors scripts/predicao_2026/motor.py. */
const Prediction2026 = (() => {
  "use strict";
  const keys = ["lula", "flavio", "outros"];
  const defaults = {base:"inclusivo",voto_lula:0,voto_flavio:0,indecisos_validos:1,
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
    const kind=["inclusivo","sem_recencia","casas"].includes(p.base)?"previsao_vetor":p.base==="pnad"?"pnad_vetor":"publicado_vetor";
    const temporal=norm(polls.map(poll=>p.base==="sem_recencia"?1:poll.peso_recencia));
    const domestic=data.estados.filter(s=>s.uf!=="ZZ"),exterior=data.estados.find(s=>s.uf==="ZZ");
    const weights=norm(domestic.map(s=>s.eleitorado)),regions=[...new Set(domestic.map(s=>s.regiao))].sort();
    const pcts=keys.map(()=>[]),gaps=[];
    for(let run=0;run<runs;run++) {
      if(isCancelled())return null;
      const hw=rng.dirichlet(temporal.map(w=>w*polls.length));
      const ps=polls.map(poll=>rng.dirichlet(poll[kind].map(x=>Math.max(x,1e-6)*Math.min(poll.n,2000)/1.5)));
      const target=Array.from({length:5},(_,k)=>sum(ps.map((v,h)=>hw[h]*v[k])));
      const common=rng.student()*Math.sqrt(3/5)*.01*sum(target.slice(0,3));
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
      margem:[quantile(gaps,.05),quantile(gaps,.95)],p_flavio_a_frente_de_lula:gaps.filter(x=>x>0).length/runs,
      p_lula_maioria:pcts[0].filter(x=>x>50).length/runs,p_flavio_maioria:pcts[1].filter(x=>x>50).length/runs};
  }
  return {defaults,state,aggregate,scenario,rake,simulate};
})();
if(typeof module!=="undefined"&&module.exports)module.exports=Prediction2026;

if(typeof document!=="undefined") {
  (()=>{
    "use strict";
    const data=JSON.parse(document.getElementById("prediction-data").textContent);
    const $=id=>document.getElementById(id),fmt=(n,d=1)=>n.toLocaleString("pt-BR",{minimumFractionDigits:d,maximumFractionDigits:d});
    const mi=n=>fmt(n/1e6,2)+" mi",names={lula:"Lula",flavio:"Flávio",outros:"Demais"};
    let edits={},revision=0,lastResult=null,simulationRunning=false;
    function params(){const p={...Prediction2026.defaults,ufs:structuredClone(edits),regioes:{}};
      document.querySelectorAll("[data-param]").forEach(el=>{
        const value=Number(el.value);p[el.dataset.param]=el.dataset.param.startsWith("voto_")?value/100:value;
        $("out-"+el.dataset.param).textContent=fmt(value,value%1?2:0)+el.dataset.suffix;
      });
      for(const k of ["base","comparecimento_modelo"])p[k]=$("param-"+k).value;
      p.indecisos_validos=Number($("param-indecisos_validos").value);
      p.indecisos_flavio=$("param-indecisos_flavio").value===""?null:Number($("param-indecisos_flavio").value);
      p.eleitor_provavel=$("param-eleitor_provavel").checked;p.exterior=$("param-exterior").checked;
      document.querySelectorAll("input[data-region]").forEach(el=>p.regioes[el.dataset.region]={comparecimento_pp:clipInput(el,-20,20)});
      return p;
    }
    function clipInput(el,min,max){const x=Number(el.value);return Number.isFinite(x)?Math.max(min,Math.min(max,x)):0;}
    function regionTable(result){return '<div class="table-scroll" tabindex="0" role="region" aria-label="Resultado do cenário por região"><table><thead><tr><th>Região</th><th>Lula</th><th>Flávio</th><th>Demais</th><th>Válidos</th></tr></thead><tbody>'+Object.entries(result.regioes).map(([r,b])=>'<tr><td>'+r+'</td>'+["lula","flavio","outros"].map(k=>'<td>'+fmt(b.percentuais[k])+"%<br>"+mi(b[k])+"</td>").join("")+'<td>'+mi(b.validos)+'</td></tr>').join("")+'</tbody></table></div>';}
    function update(){revision++;const p=params(),result=Prediction2026.scenario(data.estados,p);lastResult=result;
      const b=result.brasil;["lula","flavio","outros"].forEach(k=>{$("sim-"+k).textContent=fmt(b.percentuais[k])+"%";$("sim-votos-"+k).textContent=mi(b[k])+" votos";});
      $("sim-gap").textContent="Diferença F−L: "+fmt(b.margem_flavio_lula,2)+" pp";
      $("sim-attendance").textContent=mi(b.comparecimento)+" votantes";$("sim-absent").textContent=mi(b.abstencao)+" ausentes";$("sim-invalid").textContent=mi(b.branco_nulo)+" brancos/nulos";
      $("sim-region-table").innerHTML=regionTable(result);
      const changed=Object.keys(Prediction2026.defaults).some(k=>!["ufs","regioes"].includes(k)&&p[k]!==Prediction2026.defaults[k])||Object.keys(p.ufs).length>0||Object.values(p.regioes).some(r=>r.comparecimento_pp!==0);
      $("sim-label").textContent=changed?"Seu cenário condicional":"Previsão central";
      $("sim-uncertainty").textContent="Hipóteses atuais: intervalos ainda não simulados. Os intervalos do topo pertencem à previsão central.";
      $("uf-edits").textContent=Object.keys(edits).length?"UFs alteradas: "+Object.keys(edits).join(", ")+".":"Nenhuma UF alterada.";
      $("sim-conservation").textContent="Eleitorado = válidos + brancos/nulos + abstenção. A conta fecha.";
      if(!simulationRunning)$("sim-montecarlo").disabled=false;
    }
    document.querySelectorAll("input[data-param],input[data-region]").forEach(el=>el.addEventListener("input",update));
    document.querySelectorAll(".controls select,.controls input[type=checkbox]").forEach(el=>{if(el.id!=="uf-select")el.addEventListener("change",update);});
    $("uf-select").addEventListener("change",()=>{const e=edits[$("uf-select").value]||{};$("uf-turnout").value=e.comparecimento_pp||0;$("uf-differential").value=e.diferencial_pp||0;
      for(const k of ["lula","flavio"])$("uf-useful-"+k).value=e["voto_"+k]===undefined?"":100*e["voto_"+k];});
    for(const id of ["uf-turnout","uf-differential","uf-useful-lula","uf-useful-flavio"])$(id).addEventListener("input",()=>{
      const uf=$("uf-select").value,c=clipInput($("uf-turnout"),-20,20),d=clipInput($("uf-differential"),-20,20);
      const e={};if(c)e.comparecimento_pp=c;if(d)e.diferencial_pp=d;
      for(const k of ["lula","flavio"]){const el=$("uf-useful-"+k);if(el.value!=="")e["voto_"+k]=clipInput(el,0,100)/100;}
      if(Object.keys(e).length)edits[uf]=e;else delete edits[uf];update();});
    $("sim-reset").addEventListener("click",()=>{edits={};document.querySelectorAll("input[data-param],input[data-region]").forEach(el=>el.value=0);
      $("param-base").value="inclusivo";$("param-comparecimento_modelo").value="uf";$("param-indecisos_validos").value="1";$("param-indecisos_flavio").value="";
      $("param-eleitor_provavel").checked=true;$("param-exterior").checked=true;$("uf-turnout").value=0;$("uf-differential").value=0;$("uf-useful-lula").value="";$("uf-useful-flavio").value="";update();});
    $("sim-export").addEventListener("click",()=>{
      const body={referencia:data.referencia,hash_modelo:data.hash_modelo,hipotese:"Cenário do leitor, não previsão oficial da Arvor",...lastResult};
      const blob=new Blob([JSON.stringify(body,null,2)],{type:"application/json"}),url=URL.createObjectURL(blob),link=document.createElement("a");
      link.href=url;link.download="meu-cenario-presidente-2026.json";link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
    $("sim-montecarlo").addEventListener("click",async()=>{
      const version=revision,p=params();simulationRunning=true;$("sim-montecarlo").disabled=true;
      try{const result=await Prediction2026.simulate(data,p,(done,total)=>$("sim-uncertainty").textContent="Simulação: "+done+" / "+total+" sorteios.",()=>revision!==version);
        if(result){$("sim-uncertainty").textContent="Faixas condicionais de 90%: "+["lula","flavio","outros"].map(k=>names[k]+" "+fmt(result.intervalos[k][0])+"% a "+fmt(result.intervalos[k][2])+"%").join("; ")+". Diferença F−L: "+fmt(result.margem[0],2)+" a "+fmt(result.margem[1],2)+" pp. Flávio à frente de Lula: "+fmt(100*result.p_flavio_a_frente_de_lula)+"%. Acima de 50% dos válidos: Lula "+fmt(100*result.p_lula_maioria)+"%, Flávio "+fmt(100*result.p_flavio_maioria)+"%. "+result.runs+" sorteios, parâmetros de erro assumidos; probabilidades não calibradas historicamente.";}
        else $("sim-uncertainty").textContent="Hipótese alterada durante a simulação. Simule novamente para os controles atuais.";
      }catch(error){$("sim-uncertainty").textContent="Não foi possível concluir a simulação: "+error.message;}
      finally{simulationRunning=false;$("sim-montecarlo").disabled=false;}
    });
    update();
  })();
}
