(() => {
  'use strict';
  const D = JSON.parse(document.getElementById('dados').textContent);
  const $ = id => document.getElementById(id);
  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const n = (v, places = 0) => v == null ? 's/d' : Number(v).toLocaleString('pt-BR', {minimumFractionDigits: places, maximumFractionDigits: places});
  const norm = s => String(s).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const M = new Map(D.municipios.map(m => [m.ibge, m]));
  const faixas = new Map(D.faixas_flavio.map(f => [f.id, new Set(f.municipios)]));
  const labels = {
    renda_ate2: 'Renda domiciliar estimada até 2 SM (%)',
    renda_mais5: 'Renda domiciliar estimada acima de 5 SM (%)',
    superior: 'Superior completo no cadastro eleitoral (%)',
    ips: 'IPS Brasil 2026 (pontos)',
    homicidios_taxa_100mil: 'Homicídios por 100 mil habitantes (2024)',
    rural_pct: 'Eleitorado em locais classificados como rurais (%)'
  };
  const placar = p => `<div class="placar" role="img" aria-label="Lula ${n(p,2)}%, Flávio ${n(100-p,2)}%"><span class="lula" style="width:${p}%">${n(p,1)}%</span><span class="flavio" style="width:${100-p}%">${n(100-p,1)}%</span></div>`;
  const table = (headers, rows, caption='') => `<div class="table-scroll"><table>${caption ? `<caption>${caption}</caption>` : ''}<thead><tr>${headers.map(h=>`<th scope="col">${h}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr>${r.map(v=>`<td>${v}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
  function select(ibge) {
    const m = M.get(ibge); if (!m) return;
    $('selecionado').innerHTML = `<h3>${esc(m.nome)} / ${m.uf}</h3>${placar(m.pct_lula)}<p class="key"><span>Lula: ${n(m.lula)} votos</span><span>Flávio: ${n(m.flavio)} votos</span></p><p>Diferença: <b>${n(m.diferenca)} votos</b> · ${n(m.validos)} válidos · ${n(m.secoes)} seções.</p><p>Renda domiciliar estimada: <b>${n(m.renda_ate2,1)}% até 2 SM</b> e <b>${n(m.renda_mais5,1)}% acima de 5 SM</b>. Superior completo: ${n(m.superior,1)}%. Cobertura do perfil de renda: ${n(m.cobertura_renda,1)}% dos aptos nos locais da base.</p><p>IPS 2026: <b>${n(m.ips,2)}</b> · Homicídios 2024: <b>${n(m.homicidios_taxa_100mil,2)} por 100 mil</b> (${n(m.homicidios_n)} registros).</p><p class="small">${m.crime_documentado ? 'Presença de crime organizado documentada na base municipal; não identifica domínio do bairro nem coação eleitoral.' : 'Sem presença criminal documentada nesta base. Isso não significa ausência de crime organizado.'}</p>${m.crime_fontes ? `<details><summary>Origem documental da presença</summary><p>${esc(m.crime_fontes)}</p></details>` : ''}<p class="small">IBGE ${m.ibge} · ${m.sede_lat != null ? `Sede: ${n(m.sede_lat,5)}, ${n(m.sede_lon,5)} · <a href="https://www.openstreetmap.org/?mlat=${m.sede_lat}&mlon=${m.sede_lon}#map=12/${m.sede_lat}/${m.sede_lon}" target="_blank" rel="noopener">Localizar a sede</a>` : 'Sede sem coordenada nesta base'} · <a href="politizese_mapa.html#uf=${m.uf}">Locais de votação na UF</a></p>`;
    $('selecionado').scrollIntoView({behavior:'auto', block:'center'});
  }
  document.addEventListener('click', e => {
    const target = e.target.closest('[data-ibge]');
    if (target) {e.preventDefault(); select(target.dataset.ibge);}
  });
  let pagina = 0;
  const pageSize = 25;
  function municipalities(reset = true) {
    if (reset) pagina = 0;
    const query = norm($('busca-municipio').value), uf = $('uf').value, faixa = $('faixa').value, order = $('ordem').value;
    let rs = D.municipios.filter(m => (!uf || m.uf === uf) && (!query || norm(m.nome+' '+m.ibge).includes(query)) && (faixa === '' || faixas.get(faixa).has(m.ibge)));
    rs.sort((a,b)=> order==='nome' ? a.nome.localeCompare(b.nome, 'pt-BR') : order==='diferenca' ? b.diferenca-a.diferenca : a.pct_flavio-b.pct_flavio);
    pagina = Math.min(pagina,Math.max(0,Math.ceil(rs.length/pageSize)-1));
    const view = rs.slice(pagina*pageSize,(pagina+1)*pageSize);
    $('tabela-municipios').innerHTML = view.length ? table(['Município','Flávio','Lula','Diferença','Renda até 2 SM¹','IPS 2026','Homicídios²'], view.map(m=>[
      `<button data-ibge="${m.ibge}">${esc(m.nome)} / ${m.uf}</button>`,`${n(m.pct_flavio,2)}%`,`${n(m.pct_lula,2)}%`,n(m.diferenca),`${n(m.renda_ate2,1)}%`,n(m.ips,2),n(m.homicidios_taxa_100mil,2)
    ]),'¹ Parcela estimada pela PNAD, não renda medida. ² Taxa municipal por 100 mil, 2024; s/d significa ausência de dado.') : '<p>Nenhum município satisfaz estes filtros.</p>';
    $('paginacao').innerHTML = `<button id="anterior" ${pagina===0?'disabled':''}>← Anterior</button><span role="status">${n(rs.length)} municípios · página ${pagina+1} de ${Math.max(1,Math.ceil(rs.length/pageSize))}</span><button id="proxima" ${(pagina+1)*pageSize>=rs.length?'disabled':''}>Próxima →</button>`;
    $('anterior').onclick = () => {pagina--;municipalities(false);};
    $('proxima').onclick = () => {pagina++;municipalities(false);};
  }
  for (const uf of [...new Set(D.municipios.map(m=>m.uf))].sort()) $('uf').add(new Option(uf,uf));
  ['uf','faixa','ordem'].forEach(id=>$(id).addEventListener('change',()=>municipalities()));
  $('busca-municipio').addEventListener('input',()=>municipalities());
  function scatter() {
    const key=$('variavel').value, adjusted=$('escala').value==='uf';
    const rs=D.municipios.filter(m=>m[key]!=null && m.pct_lula!=null && m.completo);
    const groups={};
    for (const m of rs) {const g=groups[m.uf] ||= {x:0,y:0,n:0};g.x+=m[key];g.y+=m.pct_lula;g.n++;}
    const points=rs.map(m=>({m,x:m[key]-(adjusted?groups[m.uf].x/groups[m.uf].n:0),y:m.pct_lula-(adjusted?groups[m.uf].y/groups[m.uf].n:0)}));
    const xs=points.map(p=>p.x), ys=points.map(p=>p.y);
    let xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=adjusted?Math.min(...ys):0,ymax=adjusted?Math.max(...ys):100;
    if (adjusted) {xmax=Math.max(Math.abs(xmin),Math.abs(xmax));xmin=-xmax;ymax=Math.max(Math.abs(ymin),Math.abs(ymax));ymin=-ymax;}
    const x=v=>70+(v-xmin)/(xmax-xmin||1)*820, y=v=>420-(v-ymin)/(ymax-ymin||1)*385;
    let svg=`<svg viewBox="0 0 940 500" role="img" aria-label="Dispersão de ${esc(labels[key])} contra voto municipal em Lula${adjusted?', descontadas médias estaduais':''}"><title>${esc(labels[key])} e voto em Lula</title>`;
    for(let i=0;i<=5;i++) {
      const vx=xmin+(xmax-xmin)*i/5,vy=ymin+(ymax-ymin)*i/5;
      svg+=`<line class="axis" x1="${x(vx)}" x2="${x(vx)}" y1="35" y2="420"/><text x="${x(vx)}" y="444" text-anchor="middle">${n(vx,1)}</text><line class="axis" x1="70" x2="890" y1="${y(vy)}" y2="${y(vy)}"/><text x="58" y="${y(vy)+4}" text-anchor="end">${n(vy,0)}</text>`;
    }
    svg+=`<text x="70" y="20">${adjusted?'Desvio do voto em Lula, pp':'Voto em Lula, % dos válidos'}</text><text x="480" y="483" text-anchor="middle">${adjusted?'Desvio da média estadual: ':''}${esc(labels[key])}</text>`;
    for(const p of points) svg+=`<circle class="point" cx="${x(p.x).toFixed(2)}" cy="${y(p.y).toFixed(2)}" r="2.3" data-ibge="${p.m.ibge}"><title>${esc(p.m.nome)}/${p.m.uf}: indicador ${n(p.m[key],2)}, Lula ${n(p.m.pct_lula,2)}%; ${adjusted?'desvios '+n(p.x,2)+' / '+n(p.y,2):''}</title></circle>`;
    $('dispersao').innerHTML=svg+'</svg>';
    const s=D.estatisticas.municipios[key];
    $('coeficientes').innerHTML=[['Pearson',s.pearson],['Spearman',s.spearman],['Peso dos válidos',s.ponderada_validos],['Dentro da UF',s.dentro_grupo]].map(([l,v])=>`<div><strong>${n(v,2)}</strong><span>${l}</span></div>`).join('');
    $('scatter-caption').textContent=`${n(rs.length)} municípios com dados; cada ponto tem o mesmo tamanho. ${adjusted?'Os dois eixos descontam a média da UF; zero significa a média estadual.':'As cores não representam partidos; são apenas pontos territoriais.'} Os coeficientes se referem a Lula. Com Flávio, o sinal é oposto. Toque no ponto para abrir seus dados; a tabela permite busca por teclado.`;
  }
  $('variavel').addEventListener('change',scatter);$('escala').addEventListener('change',scatter);
  const capitals=D.municipios.filter(m=>m.capital).sort((a,b)=>a.nome.localeCompare(b.nome,'pt-BR'));
  for(const m of capitals) $('capital').add(new Option(m.nome+' / '+m.uf,m.ibge));
  $('capital').value=capitals.find(m=>m.uf==='SP')?.ibge || capitals[0].ibge;
  function capital() {
    const id=$('capital').value, m=M.get(id), key=$('ordem-zona').value;
    const rs=D.zonas.filter(z=>z.ibge===id).sort((a,b)=>key==='zona'?a.zona-b.zona:(b[key]??-Infinity)-(a[key]??-Infinity));
    const cover=D.cobertura_capitais.find(c=>c.uf===m.uf);
    $('capital-resumo').innerHTML=`<h3>${esc(m.nome)} / ${m.uf}</h3><p>${rs.length} zonas · ${n(cover.bus)} BUs de ${n(cover.secoes)} seções · ${n(cover.bus_validos)} votos válidos nos BUs e no total oficial. Lula ${n(m.pct_lula,2)}%; Flávio ${n(m.pct_flavio,2)}%.</p>`;
    $('zonas-barras').innerHTML=rs.map(z=>`<div class="zone-row"><a href="${esc(z.link)}">Zona ${z.zona} ↗</a>${placar(z.pct_lula)}<small>${key==='zona'?n(z.locais)+' locais':n(z[key],1)+'% · '+(key==='renda_mais5'?'>5 SM':key==='renda_ate2'?'até 2 SM':key==='superior'?'superior':'Lula')}</small></div>`).join('');
    $('zonas-tabela').innerHTML=table(['Zona','Lula','Flávio','Até 2 SM¹','Acima de 5 SM¹','Superior','BUs / seções'],rs.map(z=>[`<a href="${esc(z.link)}">${z.zona}</a>`,n(z.pct_lula,2)+'%',n(100-z.pct_lula,2)+'%',n(z.renda_ate2,1)+'%',n(z.renda_mais5,1)+'%',n(z.superior,1)+'%',`${z.bus} / ${z.secoes}`]),'¹ Renda domiciliar estimada pela composição dos locais. Universo: somente a parte da zona dentro da capital.');
  }
  $('capital').addEventListener('change',capital);$('ordem-zona').addEventListener('change',capital);
  municipalities();scatter();capital();document.documentElement.classList.add('js');
})();
