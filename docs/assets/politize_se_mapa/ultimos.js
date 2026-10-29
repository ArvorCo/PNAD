/* Dois relógios distintos. Prédio/grupo usa o mais tardio conhecido, não a média. */
window.criarUltimosMapa = function ({ S, COR, H, h }) {
  const limites = [57600, 59400, 61200, 62100, 63000, 64800];
  const nomes = ['Até 16h', '>16h–16h30', '>16h30–17h', '>17h–17h15', '>17h15–17h30', '>17h30–18h', 'Após 18h'];
  const cores = ['#457e89', '#529893', '#7b9c68', '#bb9d42', '#cc793a', '#ad503c', '#763f69'];
  const campos = { ultimo_voto: 'ultimo', encerramento: 'enc' };
  const titulos = { ultimo_voto: 'Último voto computado no log', encerramento: 'Encerramento no boletim de urna' };
  const ativo = () => Boolean(campos[S.camada]);
  const faixa = (v) => v === null || v === undefined ? null : String(limites.findIndex((s) => v <= s) < 0 ? limites.length : limites.findIndex((s) => v <= s));
  const cache = new Map();
  function instalar() {
    Object.keys(campos).forEach((k) => {
      COR[k] = Object.fromEntries(cores.map((c, i) => [String(i), c]));
      S.meta.camadas[k] = { nome: titulos[k], campo: campos[k] + '_faixa', tipo: 'categoria', categorias: nomes.map((_,i)=>String(i)), nomes:Object.fromEntries(nomes.map((s,i)=>[String(i),s])),
        explica: '25/10/2026, Brasília. A cor mostra o horário mais tardio utilizável entre as seções do ponto ou grupo. Não é uma média. A ficha mostra os horários individuais e a cobertura; horários ausentes não são estimados. Encerramento do BU e último voto no log são eventos diferentes.' };
    });
  }
  function aplicar(ls) {
    if (!ativo()) return ls;
    return ls.map((l) => {
      const key = l.id + ':' + (l.horario ? l.secoes.join(',') : '*');
      if (!cache.has(key)) {
        const allowed = l.horario ? new Set(l.secoes) : null;
        const ss = H.secoes(l).filter((s) => !allowed || allowed.has(s.secao));
        if (!ss.length) return {...l, enc_faixa:null, ultimo_faixa:null};
        const r = {horarios_total:ss.length};
        ['enc','ultimo'].forEach((k) => {
          const vs = ss.map((s)=>s[k]).filter((v)=>typeof v==='number' && Number.isFinite(v));
          r[k+'_cobertos']=vs.length; r[k+'_mais_tarde']=vs.length?Math.max(...vs):null; r[k+'_faixa']=faixa(r[k+'_mais_tarde']);
        });
        cache.set(key,r);
      }
      return {...l,...cache.get(key)};
    });
  }
  function grupo(ls) {
    const vs=ls.map((l)=>l[campos[S.camada]+'_mais_tarde']).filter((v)=>typeof v==='number' && Number.isFinite(v));
    return faixa(vs.length?Math.max(...vs):null);
  }
  function escala() {
    return h('span',{class:'ultimos-escala'},nomes.map((s,i)=>h('span',{},h('i',{style:'background:'+cores[i]}),s)),h('small',{},'Mais tardio conhecido por ponto/grupo · Brasília'));
  }
  function rotulo(l) { return h('small',{},(S.camada==='ultimo_voto'?'Último voto: ':'Encerramento: ')+window.HorariosPolitize.hora(l[campos[S.camada]+'_mais_tarde'])); }
  const colunasLista = [['ultimo_mais_tarde','Último voto · mais tardio'],['enc_mais_tarde','Encerramento · mais tardio']];
  function celula(l,k) { return h('td',{},window.HorariosPolitize.hora(l[k+'_mais_tarde']),h('small',{},(l[k+'_cobertos']??0)+' de '+(l.horarios_total??l.n_secoes)+' seções com horário')); }
  function ficha(l) {
    if (l.horarios_total === undefined) return null;
    return h('section',{class:'ficha-ultimos'},h('h4',{},'Horários mais tardios deste recorte'),h('p',{},'2º turno · Brasília · consulte cada seção na tabela abaixo.'),h('table',{},h('tbody',{},h('tr',{},h('th',{},'Último voto no log'),celula(l,'ultimo')),h('tr',{},h('th',{},'Encerramento no BU'),celula(l,'enc')))));
  }
  return {ativo, instalar, aplicar, grupo, escala, rotulo, colunasLista, celula, ficha, faixa};
};
