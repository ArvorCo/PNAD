/* Camada de pico: soma os histogramas antes de achar o pico de cada grupo. */
window.criarMovimentoMapa = function ({ S, COR, h }) {
  const api = window.PolitizeMovimento, porUf = new Map(), cache = new Map();
  function instalar() {
    const cores = ['#2d5876','#2d5876','#2d5876','#2d5876','#2d5876','#2d5876','#2d5876','#2d5876','#245b87','#217b8c','#2f9184','#5d9b61','#929c3f','#b78e2a','#cb7325','#c45230','#a83a48','#81365d','#59376e','#49335f','#49335f','#49335f','#49335f','#49335f'];
    COR.pico = Object.fromEntries(cores.map((c, i) => [String(i), c])); COR.pico.empate = '#736e66';
    S.meta.camadas.pico = { nome: 'Horário de maior votação', campo: 'pico_hora', tipo: 'categoria', categorias: [...Array.from({ length:24 }, (_,i)=>String(i)), 'empate'],
      nomes: Object.fromEntries([...Array.from({length:24},(_,i)=>[String(i), api.faixa(i)]), ['empate','Duas ou mais faixas empatadas']]),
      explica: 'Hora com mais votos computados no 2º turno, em Brasília. O pico dos grupos é calculado somando os votos por hora, não pela média dos horários dos prédios. Abra o ponto para ver o gráfico e sua cobertura. Cinza indica falta de dados; empate tem cor própria.' };
  }
  async function carregar(ufs = S.filtro.uf ? [S.filtro.uf] : Object.keys(S.meta.ufs)) {
    if (S.camada !== 'pico') return;
    await Promise.all(ufs.map(async (uf) => { if (!porUf.has(uf)) porUf.set(uf, await api.dados(uf)); }));
  }
  function aplicar(locais) {
    if (S.camada !== 'pico') return locais;
    return locais.map((l) => {
      const d = porUf.get(l.uf);
      if (!d) return { ...l, pico_hora:null, mov_horas:null };
      const key = l.id + ':' + (l.horario ? l.secoes.join(',') : '*');
      if (!cache.has(key)) cache.set(key, api.resumo(d, { local:l.id, ...(l.horario ? {secoes:l.secoes}: {}) }));
      const r = cache.get(key);
      return {...l, pico_hora:api.pico(r.horas), mov_horas:r.horas, mov_cobertas:r.cobertas, mov_total:r.secoes};
    });
  }
  function picoGrupo(ls) {
    const horas = Array(24).fill(0);
    ls.forEach((l) => l.mov_horas?.forEach((v,i)=>{horas[i]+=v;}));
    return api.pico(horas);
  }
  function legenda() {
    return h('ul', {class:'legenda-itens'}, [...Array.from({length:11},(_,i)=>String(i+8)), 'empate'].map((k)=>h('li',{},h('span',{class:'bolinha',style:'background:'+COR.pico[k]}),S.meta.camadas.pico.nomes[k])),
      h('li',{},'Outras horas aparecem no gráfico do ponto.'));
  }
  function escala() {
    return h('span', {class:'mov-mapa-escala'}, Array.from({length:10},(_,i)=>i+8).map((hr)=>h('span',{},h('i',{style:'background:'+COR.pico[hr]}),hr+'h')),h('span',{},h('i',{style:'background:'+COR.pico.empate}),'Empate'));
  }
  const colunasCsv = ['pico_horario_brt_2t', 'secoes_com_histograma', 'secoes_no_recorte', 'votos_por_hora_brt_2t'];
  const csv = (l) => S.camada !== 'pico' ? [] : [S.meta.camadas.pico.nomes[l.pico_hora] || '', l.mov_cobertas, l.mov_total, l.mov_horas ? l.mov_horas.map((v,i)=>i+':'+v).join('|') : ''];
  return { instalar, carregar, aplicar, picoGrupo, legenda, escala, colunasCsv, csv };
};
