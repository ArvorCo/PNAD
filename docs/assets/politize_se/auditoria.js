/* Índice público por seção e por local do respectivo turno. */
(() => {
  'use strict';
  const base = window.PolitizeDadosAuditoria;
  const porSecao = new Map(), porLocal = new Map();
  function adicionar(indice, chave, registro) {
    if (!indice.has(chave)) indice.set(chave, []);
    indice.get(chave).push(registro);
  }
  for (const [uf, linhas] of Object.entries(base || {})) {
    for (const [mun, zona, secao, turno, local, quantidade, alcance, habilitacao, equipe, urna] of linhas) {
      const prefixo = [uf, mun, zona].join('-');
      const r = {uf, mun, zona, secao, turno, local, quantidade, alcance, habilitacao, equipe, urna};
      adicionar(porSecao, prefixo + '-' + secao, r);
      adicionar(porLocal, prefixo + '-' + local, r);
    }
  }
  const sem = 'Sem ocorrência na lista publicada';
  const categorias = {
    mesarios: [sem, 'Seções do mesmo local', 'Locais distintos no município', 'Municípios distintos na UF', 'UFs distintas'],
    urnas: [sem, 'Série final do BU sem evento de cômputo', 'Trecho de cômputo em dois logs']
  };
  const camadas = {};
  for (const tipo of Object.keys(categorias)) {
    for (const turno of [1, 2]) camadas[tipo + '_' + turno + 't'] = {tipo, turno};
  }
  const relatorio = 'auditoria_urnas_2026.html';
  function registros(ref) {
    if (ref.secao !== undefined) {
      const mun = String(ref.mun).padStart(5,'0');
      return porSecao.get([ref.uf, mun, Number(ref.zona), Number(ref.secao)].join('-')) || [];
    }
    const lista = porLocal.get(ref.local || ref.id) || [];
    return ref.secoes ? lista.filter(r => ref.secoes.includes(r.secao)) : lista;
  }
  function nivel(local, camada) {
    if (!base || local.uf === 'ZZ') return null;
    const {tipo, turno} = camadas[camada];
    const lista = porLocal.get(local.id);
    if (!lista) return 0;
    let maximo = 0;
    for (const r of lista) {
      if (r.turno === turno && (!local.horario || local.secoes.includes(r.secao))) {
        maximo = Math.max(maximo, tipo === 'mesarios' ? r.alcance : r.urna);
      }
    }
    return maximo;
  }
  function nivelGrupo(locais, camada) {
    let maximo = null;
    for (const local of locais) {
      const v = nivel(local, camada);
      if (v !== null && (maximo === null || v > maximo)) maximo = v;
    }
    return maximo;
  }
  function el(tag, texto) {
    const n = document.createElement(tag);
    if (texto) n.textContent = texto;
    return n;
  }
  function link(href, texto) {
    const a = el('a', texto); a.href = href; return a;
  }
  function painel(ref) {
    const box = el('details');
    box.className = 'auditoria-painel';
    const linhas = registros(ref);
    const indisponivel = !base || ref.uf === 'ZZ';
    const titulo = indisponivel ? 'Cobertura da auditoria' : linhas.length ? 'Ocorrências de auditoria' : 'Consulta à auditoria';
    box.append(el('summary', titulo + ' · mesários e urnas'));
    if (indisponivel || !linhas.length) {
      box.append(el('p', !base ? 'Os dados da auditoria não carregaram.' : ref.uf === 'ZZ' ? 'O exterior está fora das duas auditorias.' : 'Nenhuma ocorrência neste recorte das listas publicadas para os dois turnos.'));
    } else {
      if (ref.secao !== undefined) box.open = true;
      const ul = el('ul');
      for (const r of linhas.slice().sort((a,b) => a.turno-b.turno || a.secao-b.secao)) {
        const li = el('li');
        const rotulo = r.turno + 'º turno · seção ' + r.secao;
        li.append(ref.secao === undefined ? link('politizese.html#uf='+r.uf+'&z='+r.zona+'&s='+r.secao, rotulo) : el('strong', rotulo));
        if (r.quantidade) {
          li.append(el('p', r.quantidade + (r.quantidade===1 ? ' número de mesário registrado' : ' números de mesário registrados') + ' em mais de uma seção. Maior alcance observado nesta seção: ' + categorias.mesarios[r.alcance].toLowerCase() + '.'));
          if (r.habilitacao) li.append(el('p', 'Há habilitações atribuídas ao mesmo número nos dois lados de um par entre municípios.'));
          if (r.equipe) li.append(el('p', 'As mesmas quatro sequências de título aparecem durante o dia em outra seção com equipe de quatro.'));
        }
        if (r.urna) {
          const nota = r.urna === 1 ? 'A série que gerou o BU aparece no log, mas outras séries emitiram os eventos de cômputo.' :
            r.uf === 'BA' && r.secao === 175 ? 'O log traz 100 cômputos da seção 181. Restam 136 atribuíveis à 175 para 272 votos no BU e no RDV. A causa da lacuna segue aberta.' :
            r.uf === 'BA' ? 'As 100 linhas desta urna também aparecem no log da seção 175. As linhas atribuídas à 181 fecham os 263 votos da seção.' :
            'As 304 linhas da seção 112 aparecem também no pacote da 85. A separação por seção reproduz os dois resultados.';
          li.append(el('p', nota + ' O placar presidencial desta seção confere entre BU, RDV e totalização.'));
        }
        ul.append(li);
      }
      box.append(ul, el('p','O registro do número exige confronto com as atas para estabelecer presença física. As contagens de votos são agregadas por seção.'));
    }
    box.append(link(relatorio, 'Ler o relatório e baixar os dados'), document.createTextNode(' · '), link('auditoria-2026/mesarios/mapa.html','Mapa de mesários'),document.createTextNode(' · '),link('auditoria-2026/urnas/mapa.html','Mapa de urnas'));
    return box;
  }
  function instalar(meta, cores) {
    for (const [id,{tipo,turno}] of Object.entries(camadas)) {
      const tema = tipo==='mesarios' ? 'Registros de mesários' : 'Identificadores das urnas';
      meta.camadas[id] = {nome: tema+' · '+turno+'º turno',campo:id,tipo:'categoria',grupo:'Auditoria de mesários e urnas',explica:'Maior categoria observada entre as seções do local no turno selecionado.'};
      cores[id] = tipo==='mesarios' ? ['#bfc9c5','#80b1a4','#398781','#c78a35','#923748'] : ['#bfc9c5','#497c9a','#a4412d'];
    }
  }
  function legenda(id, cores) {
    const {tipo,turno} = camadas[id];
    const nomes=categorias[tipo];
    function escala() {
      const ul=el('ul'); ul.className='legenda-itens';
      nomes.forEach((nome,i) => {const li=el('li'),cor=el('span');cor.className='bolinha';cor.style.background=cores[i];li.append(cor,document.createTextNode(nome));ul.append(li);});
      return ul;
    }
    const titulo=(tipo==='mesarios'?'Mesários':'Urnas')+' · '+turno+'º turno';
    document.querySelector('#mapa-escala').replaceChildren(el('b',titulo),escala());
    document.querySelector('#legenda').replaceChildren(escala(),el('p','A cor do local ou grupo mostra a maior categoria das seções representadas. O cadastro do mapa pode diferir entre turnos. Locais sem coordenadas podem ser consultados na auditoria. O exterior está fora do recorte.'),
      el('p',!base?'Os dados da auditoria não carregaram.':tipo==='mesarios'?'A coincidência é do número digitado. A presença física precisa de comprovação documental.':'Os dois pares com trecho de cômputo em comum ficam na Bahia e no Espírito Santo.'),
      link(relatorio+'#'+tipo,'Ler a auditoria e consultar as fontes'));
  }
  window.PolitizeAuditoria = {camadas, categorias, nivel, nivelGrupo, painel, instalar, legenda};
})();
