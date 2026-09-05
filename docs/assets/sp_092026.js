'use strict';
(() => {
  const search = document.querySelector('#municipal-search');
  const normal = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  search.addEventListener('input', () => {
    const query = normal(search.value);
    let count = 0;
    for (const row of document.querySelectorAll('#municipal-table tbody tr')) {
      row.hidden = !normal(row.cells[0].textContent + ' ' + row.cells[1].textContent).includes(query);
      if (!row.hidden) count++;
    }
    document.querySelector('#table-count').textContent = `${count} municípios encontrados`;
  });
  const layer = document.querySelector('#map-layer');
  const city = document.querySelector('#map-city');
  const paths = [...document.querySelectorAll('#municipal-map path')];
  const legend = document.querySelector('#map-legend');
  const panel = document.querySelector('#map-readout');
  const colors = {'Jair → Jair':'#28705f','Jair → PT':'#d8a631','PT → PT':'#b84648','Jair → Empate':'#859394'};
  const fmt = (v, digits=0) => Number(v).toLocaleString('pt-BR', {minimumFractionDigits:digits, maximumFractionDigits:digits});
  const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const blend = (a,b,t) => '#' + a.map((v,i)=>Math.round(v+(b[i]-v)*t).toString(16).padStart(2,'0')).join('');
  let byId;
  function selected() {
    if (!byId || !city.value) return;
    const r = byId[city.value], key = layer.value;
    const countLayer = key.endsWith('_1') || key==='eleitorado';
    const val = key==='virada' ? r.virada : fmt(r[key] || 0, countLayer ? 0 : 2);
    panel.innerHTML = `<span class="eyebrow">${escape(r.regiao)} · IBGE ${r.id}</span><h3>${escape(r.nome)}</h3><p><b>${escape(layer.selectedOptions[0].textContent)}</b><br>${escape(val)}</p><dl>${[
      ['Eleitorado 2026',fmt(r.eleitorado)],['Vencedores',r.virada],['Bolsonaro 2018 · 2º',fmt(r.jair_2018_2)+' · '+fmt(r.jair_2018_2_pct,2)+'%'],['Bolsonaro 2022 · 2º',fmt(r.jair_2022_2)+' · '+fmt(r.jair_2022_2_pct,2)+'%'],['Tarcísio 2022 · 2º',fmt(r.tarcisio_2022_2)+' · '+fmt(r.tarcisio_2022_2_pct,2)+'%'],['Renda pc · Censo 2022','R$ '+fmt(r.renda,2)]
    ].map(([a,b])=>`<div><dt>${escape(a)}</dt><dd>${escape(b)}</dd></div>`).join('')}</dl>`;
    paths.forEach(p=>p.classList.toggle('selected',p.dataset.id===city.value));
  }
  function redraw() {
    if (!byId) return;
    const key = layer.value;
    const values = Object.values(byId).map(r=>r[key] || 0);
    const lo = Math.min(...values), hi = Math.max(...values);
    const log = key==='eleitorado' || key.endsWith('_1') || key==='pib_pc_2023';
    const diverging = key.endsWith('_pp');
    const bound = Math.max(Math.abs(lo),Math.abs(hi));
    paths.forEach(path => {
      const r=byId[path.dataset.id], value=r[key] || 0;
      let color;
      if(key==='virada') color=colors[r.virada];
      else if(diverging) color=blend([242,236,222],value<0?[174,68,67]:[30,102,83],Math.abs(value)/bound);
      else {
        const ratio=log ? Math.log1p(value)/Math.log1p(hi) : (value-lo)/(hi-lo || 1);
        color=blend([230,231,206],[25,99,81],ratio);
      }
      path.setAttribute('fill',color);
      path.querySelector('title').textContent = `${r.nome}: ${key==='virada'?r.virada:fmt(value,log?0:2)}`;
    });
    legend.firstElementChild.textContent = key==='virada' ? 'Verde: Bolsonaro nas duas · Ocre: Bolsonaro → Lula · Vermelho: PT nas duas · Cinza: empate' : diverging ? `Vermelho: negativo · Claro: zero · Verde: positivo. Escala simétrica de −${fmt(bound,2)} a +${fmt(bound,2)} pp.` : `Claro: menor valor · Verde escuro: maior valor. Intervalo observado: ${fmt(lo,log?0:2)} a ${fmt(hi,log?0:2)}. Escala ${log?'logarítmica para acomodar diferenças de magnitude':'linear'}.`;
    selected();
  }
  fetch('assets/sp_092026_data.json').then(r=>{if(!r.ok)throw new Error('dados indisponíveis');return r.json();}).then(data=>{
    byId=Object.fromEntries(data.municipios.map(r=>[r.id,r]));
    paths.forEach(path=>path.addEventListener('click',()=>{city.value=path.dataset.id;selected();}));
    layer.addEventListener('change',redraw);
    city.addEventListener('change',selected);
  }).catch(()=>{
    layer.disabled=true;city.disabled=true;
    panel.textContent='Não foi possível carregar as camadas adicionais. O mapa inicial, as tabelas e os links de dados continuam disponíveis.';
  });
})();
