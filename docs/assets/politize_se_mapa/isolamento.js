/* Isolation Forest territorial: modelos próprios por nível, sem escore individual. */
'use strict';
window.criarIsolamentoMapa = function ({S, COR, H, h, nf0, buscar}) {
  const BASE = 'assets/politize_se/isolamento/';
  const niveis = {
    isolamento_local: {tabela:'locais', nome:'Local de votação', chave:l=>l.id},
    isolamento_zona: {tabela:'zonas', nome:'Zona eleitoral inteira', chave:l=>String(l.zona)},
    isolamento_municipio: {tabela:'municipios', nome:'Município inteiro', chave:l=>l.mun},
  };
  const dados = new Map();
  const numero = v => typeof v === 'number' && Number.isFinite(v);
  const fmt = v => numero(v) ? v.toLocaleString('pt-BR', {maximumFractionDigits:1}) : 'sem dado';
  const ativo = () => Object.hasOwn(niveis, S.camada);
  let meta = null;

  async function instalar() {
    for (const [k, nivel] of Object.entries(niveis)) {
      S.meta.camadas[k] = {
        nome:'Isolation Forest · ' + nivel.nome.toLowerCase(), campo:k,
        tipo:'sequencial', minimo:0, maximo:100, baixo:'P0', alto:'P100',
        grupo:'Padrões territoriais · Isolation Forest', precisa_ml:true,
        explica:'Posição nacional do padrão eleitoral entre unidades do mesmo nível. Quanto maior o percentil, mais isolada a combinação de votos e comparecimento nos dois turnos. Cada nível tem modelo próprio; não é média nem máximo das seções.',
      };
      COR[k] = ['#e5eee9', '#6c3e89'];
    }
    try { meta = await buscar(BASE + 'indice.json?v=20261029-isolamento1'); } catch { meta = null; }
  }

  async function carregar(ufs) {
    await Promise.all(ufs.filter(uf => !dados.has(uf)).map(async uf => {
      if (meta?.ufs && !Object.hasOwn(meta.ufs, uf)) return;
      try {
        const fonte = meta?.ufs?.[uf];
        const d = await buscar(BASE + (fonte?.arquivo || uf + '.json.gz') + '?v=' + (fonte?.sha256 || '20261029-isolamento1'));
        if (d.formato !== 1 || d.uf !== uf || !Array.isArray(d.colunas)) throw Error('formato');
        dados.set(uf, d);
      } catch { dados.delete(uf); }
    }));
  }

  function linha(l, nivel, secao) {
    if (l.horario) return null;
    const d = dados.get(l.uf);
    const chave = nivel === 'secoes' ? `${l.mun}-${l.zona}-${secao}` : niveis[nivel]?.chave(l);
    const valores = d?.[nivel === 'secoes' ? nivel : niveis[nivel]?.tabela]?.[chave];
    if (!valores) return null;
    const r = Object.fromEntries(d.colunas.map((c, i) => [c, valores[i]]));
    return numero(r.percentil) && r.percentil >= 0 && r.percentil <= 100 ? r : null;
  }

  function aplicar(ls) {
    for (const l of ls) for (const k of Object.keys(niveis)) l[k] = linha(l, k)?.percentil ?? null;
    return ls;
  }

  function grupo(ls) {
    if (!ls.length || ls.some(l => l.horario)) return null;
    if (S.camada === 'isolamento_local' && ls.length !== 1) return null;
    const nivel = niveis[S.camada];
    const chaves = new Set(ls.map(l => l.uf + '-' + nivel.chave(l)));
    return chaves.size === 1 ? linha(ls[0], S.camada)?.percentil ?? null : null;
  }

  const motivo = l => l.horario
    ? 'Sem modelo próprio para o recorte de horário'
    : 'Sem escore: unidade sem pares elegíveis ou dados indisponíveis';

  function efeitoPorte() {
    const faixas = meta?.niveis?.secoes?.diagnostico_tamanho || [];
    if (!faixas.length) return null;
    const rotulo = f => f.aptos_max_exclusivo === null ? f.aptos_min + '+' : f.aptos_min + '–' + (f.aptos_max_exclusivo - 1);
    return h('details', {class:'ficha-distribuicao isolamento-porte'},
      h('summary', {}, 'Como o tamanho da seção afeta o topo do ranking'),
      h('p', {}, 'Parcela de seções de cada tamanho que ficou no P99+ nacional. Proporções de grupos pequenos variam mais; o ranking não controla esse efeito.'),
      h('table', {class:'cmp'},
        h('thead', {}, h('tr', {}, h('th', {scope:'col'}, 'Aptos por seção'), h('th', {scope:'col'}, 'Seções'), h('th', {scope:'col'}, 'No P99+ nacional'))),
        h('tbody', {}, faixas.map(f => h('tr', {}, h('th', {scope:'row'}, rotulo(f)),
          h('td', {}, nf0.format(f.unidades)), h('td', {}, f.top1_pct.toLocaleString('pt-BR', {maximumFractionDigits:3}) + '%'))))),
      h('p', {class:'ficha-meta'}, 'Na tabela de seções, o percentil dentro do porte reposiciona o mesmo escore entre seções de tamanho semelhante. É uma sensibilidade de referência, não um novo modelo nem correção validada.'));
  }

  function descricao(r) {
    if (!r) return 'Sem escore';
    return 'P' + fmt(r.percentil) + ' · ' + nf0.format(r.secoes_usadas) + '/' + nf0.format(r.secoes_total) + ' seções elegíveis';
  }

  function texto(l) {
    const r = linha(l, S.camada);
    return 'Isolation Forest · ' + niveis[S.camada].nome + ': ' + (r ? descricao(r) : motivo(l));
  }

  function legenda() {
    if (!ativo()) return false;
    const c = S.meta.camadas[S.camada];
    document.querySelector('#mapa-escala').replaceChildren(
      h('b', {}, c.nome),
      h('span', {class:'mapa-mini-escala', style:`background:linear-gradient(90deg,${COR[S.camada].join(',')})`}),
      h('span', {}, 'P0 → P100'),
      h('small', {}, 'Maior = mais isolado · cinza: sem escore próprio'));
    const n = meta?.niveis?.[niveis[S.camada].tabela]?.unidades;
    document.querySelector('#legenda').replaceChildren(
      h('p', {}, c.explica),
      h('p', {}, S.camada === 'isolamento_local'
        ? 'Grupos geométricos de vários prédios ficam sem escore. Aproxime o mapa para ver cada local.'
        : 'Cada ponto mostra o contexto da unidade inteira. Grupos que misturam ' + (S.camada === 'isolamento_zona' ? 'zonas' : 'municípios') + ' ficam sem escore; grupos da mesma unidade repetem somente seu modelo próprio.'),
      h('p', {}, 'O modelo não controla porte nem geografia. Seções pequenas têm proporções mais variáveis e aparecem mais entre as isoladas; isolamento não significa desvio inexplicado.'),
      efeitoPorte(),
      h('p', {}, H.ativo() ? 'Filtro de horário ativo: não foi ajustado um modelo para esse subconjunto, que fica sem escore.' : 'P99 é uma convenção exploratória. Percentil e faixa entre sementes não são p-value, intervalo de confiança, chance de fraude ou teste de integridade eleitoral.'),
      numero(n) ? h('p', {}, nf0.format(n) + ' unidades elegíveis no modelo nacional deste nível.') : null,
      h('a', {href:BASE + 'indice.json'}, 'Modelo, variáveis, cobertura e fontes'));
    return true;
  }

  function resumoCelula(l, nivel) {
    const r = linha(l, nivel);
    return r ? [h('b', {}, 'P' + fmt(r.percentil)),
      r.percentil >= 99 ? h('small', {}, 'Entre 1% mais isolados · corte exploratório') : null,
      h('small', {}, 'Sementes: P' + fmt(r.percentil_min) + '–P' + fmt(r.percentil_max)),
      h('small', {}, nf0.format(r.secoes_usadas) + '/' + nf0.format(r.secoes_total) + ' seções elegíveis')]
      : [h('span', {}, 'Sem escore'), h('small', {}, motivo(l))];
  }
  const celula = l => h('td', {class:'num'}, resumoCelula(l, S.camada));
  const colunas = () => [[S.camada, 'Isolation Forest · ' + niveis[S.camada].nome]];

  function painel(l) {
    return h('details', {class:'ficha-distribuicao isolamento-painel', open:ativo()},
      h('summary', {}, 'Isolation Forest · padrões territoriais'),
      h('p', {}, 'Cada linha usa um ajuste próprio sobre votos e comparecimento. Posição nacional: maior percentil significa combinação mais isolada entre unidades do mesmo nível.'),
      h('table', {class:'cmp'},
        h('thead', {}, h('tr', {}, h('th', {scope:'col'}, 'Unidade'), h('th', {scope:'col'}, 'Posição e cobertura'))),
        h('tbody', {}, Object.entries(niveis).map(([k, nivel]) => h('tr', {},
          h('th', {scope:'row'}, nivel.nome), h('td', {}, resumoCelula(l, k)))))),
      h('p', {class:'ficha-meta'}, 'A faixa mostra variação entre sementes do algoritmo, não incerteza estatística calibrada. O escore usa apenas pares de seções elegíveis; a fração informa sua cobertura na unidade. Atipicidade pode refletir composição territorial, mudanças eleitorais ou dados incompletos; não identifica irregularidade.'),
      h('p', {class:'ficha-meta'}, 'Sem controle de porte ou geografia: seções pequenas têm proporções mais variáveis e aparecem mais no topo. Compare o tamanho da seção e a cobertura antes de interpretar seu percentil.'),
      efeitoPorte(),
      h('a', {href:BASE + 'indice.json'}, 'Método, variáveis e fontes'));
  }

  function celulaSecao(l, secao) {
    const r = linha(l, 'secoes', secao);
    return h('td', {class:'txt isolamento-secao'}, r ? [h('b', {}, 'P' + fmt(r.percentil)),
      r.percentil >= 99 ? h('small', {}, 'Entre 1% mais isolados · corte exploratório') : null,
      numero(r.percentil_porte) ? h('small', {}, 'Dentro do porte ' + r.faixa_porte + ': P' + fmt(r.percentil_porte) + ' · mesmo escore') : null,
      h('small', {}, nf0.format(r.aptos2) + ' aptos · seção elegível'),
      h('small', {}, 'Sementes: P' + fmt(r.percentil_min) + '–P' + fmt(r.percentil_max))]
      : h('small', {}, motivo(l)));
  }

  const camposCsv = ['percentil', 'percentil_min', 'percentil_max', 'score', 'secoes_usadas', 'secoes_total', 'aptos2'];
  const colunasCsv = Object.keys(niveis).flatMap(k => camposCsv.map(c => k + '_' + c));
  function csv(l) {
    return Object.keys(niveis).flatMap(k => {
      const r = linha(l, k);
      return camposCsv.map(c => numero(r?.[c]) ? String(r[c]).replace('.', ',') : null);
    });
  }

  return {instalar, carregar, aplicar, ativo, grupo, texto, legenda, celula, colunas, painel, celulaSecao, colunasCsv, csv};
};
