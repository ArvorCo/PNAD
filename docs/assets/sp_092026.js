'use strict';
(() => {
  const search = document.querySelector('#municipal-search');
  const normal = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  if (search) {
    search.addEventListener('input', () => {
      const query = normal(search.value);
      let count = 0;
      for (const row of document.querySelectorAll('#municipal-table tbody tr')) {
        row.hidden = !normal(row.cells[0].textContent + ' ' + row.cells[1].textContent).includes(query);
        if (!row.hidden) count++;
      }
      document.querySelector('#table-count').textContent = `${count} municípios encontrados`;
    });
  }
  const layer = document.querySelector('#map-layer');
  const city = document.querySelector('#map-city');
  const paths = [...document.querySelectorAll('#municipal-map path')];
  const legend = document.querySelector('#map-legend');
  const panel = document.querySelector('#map-readout');
  const colors = {'Jair → Jair':'#28705f','Jair → PT':'#d8a631','PT → PT':'#b84648','Jair → Empate':'#859394'};
  const fmt = (v, digits=0) => Number(v).toLocaleString('pt-BR', {minimumFractionDigits:digits, maximumFractionDigits:digits});
  const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const blend = (a,b,t) => '#' + a.map((v,i)=>Math.round(v+(b[i]-v)*t).toString(16).padStart(2,'0')).join('');
  const INDEX_NAMES = {i_tarcisio:'Tarcísio', i_pontes:'Marcos Pontes', i_derrite:'Derrite', i_salles:'Salles', i_carla:'Carla Zambelli', i_eduardo:'Eduardo Bolsonaro', i_prado:'André do Prado', i_gil:'Gil Diniz'};
  let byId;
  function selected() {
    if (!byId || !city.value) return;
    const r = byId[city.value], key = layer.value;
    const countLayer = key.endsWith('_1') || key==='eleitorado';
    const val = key==='virada' ? r.virada : fmt(r[key] || 0, countLayer ? 0 : (key.startsWith('i_') ? 0 : 2));
    const indices = Object.entries(INDEX_NAMES).map(([k,n]) => `<div><dt>Índice ${escape(n)}</dt><dd>${fmt(r[k] || 0)}</dd></div>`).join('');
    panel.innerHTML = `<span class="eyebrow">${escape(r.regiao)} · IBGE ${r.id}</span><h3>${escape(r.nome)}</h3><p><b>${escape(layer.selectedOptions[0].textContent)}</b><br>${escape(val)}</p><dl>${[
      ['Eleitorado 2026',fmt(r.eleitorado)],['Vencedores',r.virada],['Bolsonaro 2022 · 1º',fmt(r.jair_2022_1_pct,2)+'%'],['Tarcísio 2022 · 1º',fmt(r.tarcisio_2022_1_pct,2)+'%'],['Rodrigo Garcia 2022 · 1º',fmt(r.garcia1||0,2)+'%'],['Tarcísio menos Bolsonaro · 2º',fmt(r.tar2_menos_bol2_pp||0,2)+' pp'],['Estoque localizado',fmt(r.estoque_votos||0)+' · '+fmt(r.estoque_pct||0,2)+'%'],['Bolsonaro 2018 · 2º',fmt(r.jair_2018_2)+' · '+fmt(r.jair_2018_2_pct,2)+'%'],['Bolsonaro 2022 · 2º',fmt(r.jair_2022_2)+' · '+fmt(r.jair_2022_2_pct,2)+'%'],['Tarcísio 2022 · 2º',fmt(r.tarcisio_2022_2)+' · '+fmt(r.tarcisio_2022_2_pct,2)+'%'],['Renda pc · Censo 2022','R$ '+fmt(r.renda,2)]
    ].map(([a,b])=>`<div><dt>${escape(a)}</dt><dd>${escape(b)}</dd></div>`).join('')}${indices}</dl><p class="note">Índice 100 = o nome rendeu no município o mesmo que Bolsonaro rendeu no 1º turno de 2022, em relação às respectivas médias estaduais.</p>`;
    paths.forEach(p=>p.classList.toggle('selected',p.dataset.id===city.value));
  }
  function redraw() {
    if (!byId) return;
    const key = layer.value;
    const values = Object.values(byId).map(r=>r[key] || 0);
    const lo = Math.min(...values), hi = Math.max(...values);
    const log = key==='eleitorado' || key.endsWith('_1') || key==='pib_pc_2023' || key==='estoque_votos';
    const diverging = key.endsWith('_pp');
    const index = key.startsWith('i_');
    const bound = Math.max(Math.abs(lo),Math.abs(hi));
    paths.forEach(path => {
      const r=byId[path.dataset.id], value=r[key] || 0;
      let color;
      if(key==='virada') color=colors[r.virada];
      else if(diverging) color=blend([242,236,222],value<0?[174,68,67]:[30,102,83],Math.abs(value)/bound);
      else if(index) { const t=Math.min(1,Math.abs(Math.log(Math.max(value,1)/100))/Math.log(3)); color=blend([242,236,222],value<100?[174,68,67]:[30,102,83],t); }
      else {
        const ratio=log ? Math.log1p(value)/Math.log1p(hi) : (value-lo)/(hi-lo || 1);
        color=blend([230,231,206],[25,99,81],ratio);
      }
      path.setAttribute('fill',color);
      path.querySelector('title').textContent = `${r.nome}: ${key==='virada'?r.virada:fmt(value,log||index?0:2)}`;
    });
    legend.firstElementChild.textContent = key==='virada' ? 'Verde: Bolsonaro nas duas · Ocre: Bolsonaro → Lula · Vermelho: PT nas duas · Cinza: empate' : diverging ? `Vermelho: negativo · Claro: zero · Verde: positivo. Escala simétrica de −${fmt(bound,2)} a +${fmt(bound,2)} pp.` : index ? `Vermelho: abaixo de 100 (rende menos que Bolsonaro rendeu ali) · Claro: 100 · Verde: acima de 100. Escala logarítmica, saturando em um terço e no triplo. Intervalo observado: ${fmt(lo)} a ${fmt(hi)}.` : `Claro: menor valor · Verde escuro: maior valor. Intervalo observado: ${fmt(lo,log?0:2)} a ${fmt(hi,log?0:2)}. Escala ${log?'logarítmica para acomodar diferenças de magnitude':'linear'}.`;
    selected();
  }
  const svg = document.querySelector('#municipal-map');
  const base = [0, 0, 1000, 660];
  let vb = base.slice();
  const apply = () => svg.setAttribute('viewBox', vb.join(' '));
  const zoomTo = (cx, cy, w) => { const h = w * 0.66; vb = [cx - w / 2, cy - h / 2, w, h]; apply(); };
  const presets = {metro: [738, 470, 170], baixada: [760, 560, 150], campinas: [640, 400, 220]};
  const cityCenter = id => { const el = svg.querySelector(`path[data-id="${id}"]`); if (!el) return null; const b = el.getBBox(); return [b.x + b.width / 2, b.y + b.height / 2]; };
  const capital = cityCenter('3550308');
  if (capital) { presets.metro = [capital[0], capital[1], 170]; presets.baixada = [capital[0] + 25, capital[1] + 55, 150]; }
  const campinas = cityCenter('3509502'); if (campinas) presets.campinas = [campinas[0], campinas[1], 220];
  document.querySelectorAll('.zoom-bar button').forEach(btn => btn.addEventListener('click', () => {
    const kind = btn.dataset.zoom;
    if (kind === 'reset') { vb = base.slice(); apply(); return; }
    const cx = vb[0] + vb[2] / 2, cy = vb[1] + vb[3] / 2;
    if (kind === 'in') zoomTo(cx, cy, vb[2] / 1.6);
    else if (kind === 'out') zoomTo(cx, cy, Math.min(1000, vb[2] * 1.6));
    else if (presets[kind]) zoomTo(...presets[kind]);
  }));
  svg.addEventListener('wheel', e => { e.preventDefault(); const cx = vb[0] + vb[2] / 2, cy = vb[1] + vb[3] / 2; zoomTo(cx, cy, Math.min(1000, Math.max(60, vb[2] * (e.deltaY > 0 ? 1.15 : 0.87)))); }, {passive: false});
  let drag = null;
  svg.addEventListener('pointerdown', e => { drag = [e.clientX, e.clientY, vb.slice()]; svg.classList.add('dragging'); });
  window.addEventListener('pointermove', e => { if (!drag) return; const r = svg.getBoundingClientRect(); const k = vb[2] / r.width; vb = [drag[2][0] - (e.clientX - drag[0]) * k, drag[2][1] - (e.clientY - drag[1]) * k, vb[2], vb[3]]; apply(); });
  window.addEventListener('pointerup', () => { drag = null; svg.classList.remove('dragging'); });
  Promise.all([
    fetch('assets/sp_092026_data.json').then(r=>{if(!r.ok)throw new Error('dados indisponíveis');return r.json();}),
    fetch('assets/sp_092026_camada2.json').then(r=>{if(!r.ok)throw new Error('camada 2 indisponível');return r.json();})
  ]).then(([data, camada])=>{
    byId=Object.fromEntries(data.municipios.map(r=>[r.id,r]));
    for (const m of camada.carregadores.municipios) Object.assign(byId[m.id], m);
    paths.forEach(path=>path.addEventListener('click',()=>{city.value=path.dataset.id;selected();}));
    layer.addEventListener('change',redraw);
    city.addEventListener('change',selected);
  }).catch(()=>{
    layer.disabled=true;city.disabled=true;
    panel.textContent='Não foi possível carregar as camadas adicionais. O mapa inicial, as tabelas e os links de dados continuam disponíveis.';
  });
})();
