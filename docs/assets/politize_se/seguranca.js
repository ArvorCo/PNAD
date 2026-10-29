/* Documentação territorial compartilhada; presença não é domínio municipal. */
(function () {
  'use strict';
  const BASE = 'assets/politize_se/seguranca/';
  let promessa;
  function dados() {
    if (!promessa) promessa = fetch(BASE + 'dados.json?v=20261029-seguranca').then((r) => {
      if (!r.ok) throw new Error('Documentação indisponível');
      return r.json();
    }).catch((e) => { promessa = null; throw e; });
    return promessa;
  }
  function el(tag, attrs = {}, ...children) {
    const n = document.createElement(tag);
    Object.entries(attrs).forEach(([k, v]) => n.setAttribute(k, v));
    children.flat(Infinity).filter((v) => v !== null && v !== undefined).forEach((v) => n.append(v instanceof Node ? v : String(v)));
    return n;
  }
  const link = (url, label) => el('a', { href: url, target: '_blank', rel: 'noopener' }, label);
  function referencia(texto) {
    const urls = texto.match(/https:\/\/[^\s|,)]+/g) || [];
    const semUrl = texto.replace(/https:\/\/[^\s|,)]+/g, '').replace(/[,\s]+$/, '');
    return el('li', {}, semUrl, urls.map((u) => [' · ', link(u, 'Abrir fonte')]));
  }
  function status(d, id, tipo) {
    if (tipo === 'crime') return d.municipios[id.split('-').slice(0, 2).join('-')] ? 'documentado' : null;
    return d.locais_rj[id]?.[tipo] ?? null;
  }
  const rotulo = (s) => s === 'documentado' ? 'Presença documentada no município' : s || 'Sem cobertura territorial';
  function render(d, ref) {
    const ids = ref.locais || (ref.local ? [ref.local] : []);
    const keys = [...new Set(ids.map((id) => id.split('-').slice(0, 2).join('-')))];
    if (ref.mun) keys.push(ref.uf + '-' + ref.mun);
    const municipios = [...new Set(keys)].map((k) => [k, d.municipios[k]]).filter(([, m]) => m);
    const box = el('div', {}, el('p', { class: 'seg-eyebrow' }, 'Segurança / fontes públicas'), el('h3', {}, 'Grupos armados e território'));
    box.append(el('p', { class: 'seg-destaque' }, municipios.length ? `${municipios.length} município${municipios.length === 1 ? '' : 's'} com presença documentada neste recorte` : 'Sem registro no levantamento municipal reutilizado'));
    box.append(el('p', {}, 'O registro municipal não delimita bairros dominados nem indica controle do local de votação. Ausência de documentação não significa ausência de grupos.'));
    if (municipios.length) {
      const refs = [...new Set(municipios.flatMap(([, m]) => m.fontes))];
      box.append(el('details', { class: 'seg-fontes' }, el('summary', {}, 'Municípios, datas e fontes dos registros'),
        el('ul', {}, municipios.map(([, m]) => el('li', {}, m.nome, ' · ', m.fontes.join(', ')))),
        el('ul', {}, refs.map((r) => referencia(d.referencias[r] || r)))));
    }
    const rj = ids.filter((id) => id.startsWith('RJ-'));
    if (ref.uf === 'RJ' || rj.length) {
      box.append(el('h4', {}, 'Controle e influência · Rio de Janeiro · 2024'), el('p', {}, 'GENI/UFF e Fogo Cruzado, publicação de dezembro de 2025. A imagem delimita áreas na janela metropolitana publicada; não cobre todo o estado.'));
      for (const tipo of ['controle', 'influencia']) {
        const counts = new Map();
        rj.forEach((id) => { const s = rotulo(status(d, id, tipo)); counts.set(s, (counts.get(s) || 0) + 1); });
        box.append(el('p', { class: 'seg-destaque' }, (tipo === 'controle' ? 'Controle: ' : 'Influência: ') + [...counts].map(([s, n]) => `${s}${rj.length > 1 ? ' · ' + n + ' locais' : ''}`).join('; ')));
      }
      box.append(el('p', {}, 'Controle e influência são categorias distintas do estudo. “Sem marcação” significa ponto sem cor na imagem; “sem cobertura” inclui pontos fora da janela ou sem coordenada cadastral confirmada. Interseção aproximada, em pixels de cerca de 34 × 37 m.'));
      if (ref.local) {
        const r = d.locais_rj[ref.local];
        if (r?.controle && r.controle !== 'Sem marcação' && r.controle_borda_m < 100) box.append(el('p', { class: 'seg-nota' }, 'Ponto a menos de 100 m da borda de uma classe: a classificação é especialmente sensível à posição cadastral.'));
      }
      box.append(el('p', {}, link(d.fonte_territorial.pagina_projeto, 'Mapa original'), ' · ', link(d.relatorio, 'Relatório GENI/UFF e Fogo Cruzado')));
    } else box.append(el('p', { class: 'seg-nota' }, 'Não há delimitação territorial de controle nesta base para este recorte. O mapa territorial incorporado cobre parte do Rio de Janeiro.'));
    box.append(el('p', { class: 'seg-nota' }, 'As datas são as das fontes, não uma verificação da situação em 2026. A localização da escola não identifica a residência dos eleitores, seu vínculo com grupos, coação ou a causa do voto.'));
    const query = new URLSearchParams({ uf: ref.uf || '', camada: ref.uf === 'RJ' ? 'controle' : 'crime' });
    if (ref.local) query.set('l', ref.local);
    if (ref.mun) query.set('mun', ref.mun);
    if (ref.zona) query.set('zona', ref.zona);
    box.append(el('a', { class: 'seg-abrir', href: 'politizese_mapa.html?ver=20261029-seguranca#' + query }, 'Explorar grupos armados no mapa ↗'));
    return box;
  }
  function painel(ref) {
    const box = el('section', { class: 'seguranca-documentada', 'aria-label': 'Grupos armados e território', 'aria-busy': 'true' });
    const carregar = async () => {
      box.setAttribute('aria-busy', 'true');
      box.replaceChildren(el('p', { role: 'status' }, 'Carregando documentação territorial…'));
      try { box.replaceChildren(render(await dados(), ref)); }
      catch {
        const retry = el('button', { type: 'button' }, 'Tentar novamente');
        retry.addEventListener('click', carregar);
        box.replaceChildren(el('p', {}, 'Não foi possível carregar as fontes de segurança.'), retry);
      } finally { box.setAttribute('aria-busy', 'false'); }
    };
    carregar();
    return box;
  }
  window.PolitizeSeguranca = { dados, painel, status, rotulo, BASE };
})();
