'use strict';
(() => {
  const records=JSON.parse(document.getElementById('scenario-data').textContent);
  const controls=['turn','target','score','region','association'].map(k=>document.getElementById('lv-'+k));
  const format=n=>n.toLocaleString('pt-BR',{minimumFractionDigits:1,maximumFractionDigits:1});
  const update=()=>{
    const [turn,target,score,region,association]=controls.map(el=>el.value);
    const record=records.find(r=>r.ballot===turn && r.score===score && r.region_mode===region && r.association===Number(association) && (target==='hist' ? r.target!==.75&&r.target!==.85 : r.target===Number(target)));
    const output=document.getElementById('lv-result');
    output.replaceChildren();
    const main=document.createElement('div');
    main.textContent=`${turn==='1t'?'1º':'2º'} turno: Lula ${format(record.valid[0])}% · Flávio ${format(record.valid[1])}% dos válidos${turn==='1t'?` · demais candidaturas ${format(record.valid.slice(2).reduce((a,b)=>a+b,0))}%`:''}.`;
    const note=document.createElement('small');note.textContent=`Comparecimento-alvo: ${format(100*record.target)}%. Cenário condicionado às premissas, não previsão nem intervalo de confiança.`;
    output.append(main,note);
  };
  controls.forEach(el=>el.addEventListener('change',update));update();
})();
