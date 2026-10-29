/* Visões geográficas: zona e município se cruzam; nenhum contém sempre o outro. */
export function criarVisoes({ h, E, f0, pc, caixa, carregarZona, carregarMun, executar, ErroUsuario }) {
  const mov = window.PolitizeMovimento;
  const somar = (ls, k) => ls.reduce((a, l) => a + (typeof l[k] === 'number' ? l[k] : 0), 0);
  function totalizar(ls) {
    const r = {};
    ['n_secoes', 'n_bu2', 'aptos1', 'comp1', 'flavio1', 'lula1', 'terceira1', 'bn1', 'aptos2', 'comp2', 'flavio2', 'lula2', 'bn2', 'secoes_sinal', 'urnas_trocadas', 'secoes_anomalas'].forEach((k) => { r[k] = somar(ls, k); });
    return r;
  }
  function nav({ uf, zona, mun, local, secao }, ativo) {
    const links = [
      secao ? ['secao', 'Seção ' + secao, `#uf=${uf}&z=${zona}&s=${secao}`] : null,
      local ? ['local', 'Local de votação', `#uf=${uf}&z=${zona}&l=${encodeURIComponent(local)}`] : null,
      zona ? ['zona', 'Zona ' + zona, `#uf=${uf}&z=${zona}&visao=zona`] : null,
      mun ? ['municipio', 'Município', `#uf=${uf}&mun=${mun}&visao=municipio`] : null,
    ].filter(Boolean);
    return h('nav', { class: 'visoes-nav', 'aria-label': 'Explorar outros níveis' }, links.map(([tipo, nome, href]) => h('a', { href, 'aria-current': tipo === ativo ? 'page' : null }, nome)));
  }
  function placar(t) {
    const ratio = (a, b) => b > 0 ? pc(100 * a / b) : 'sem dado';
    const linha = (nome, key, percent = false) => h('tr', {}, h('th', { scope: 'row' }, nome), [1, 2].map((turno) => h('td', {}, turno === 2 && !t.n_bu2 ? 'sem dado' : percent ? ratio(t['comp' + turno], t['aptos' + turno]) : f0(t[key + turno]))));
    return h('table', { class: 'visoes-turnos' },
      h('thead', {}, h('tr', {}, h('th', { scope: 'col' }, 'Votação do recorte inteiro'), h('th', { scope: 'col' }, '1º turno'), h('th', { scope: 'col' }, '2º turno'))),
      h('tbody', {}, linha('Eleitores aptos', 'aptos'), linha('Votaram', 'comp'), linha('Comparecimento', 'comp', true), linha('Flávio', 'flavio'), linha('Lula', 'lula'),
        h('tr', {}, h('th', { scope: 'row' }, 'Demais candidaturas'), h('td', {}, f0(t.terceira1)), h('td', {}, 'não há')), linha('Brancos e nulos', 'bn'),
        h('tr', {}, h('th', { scope: 'row' }, 'Flávio entre os dois'), [1, 2].map((i) => h('td', {}, i === 2 && !t.n_bu2 ? 'sem dado' : ratio(t['flavio' + i], t['flavio' + i] + t['lula' + i]))))));
  }
  function listaLocais(uf, locais) {
    const inp = h('input', { type: 'search', class: 'visoes-busca', placeholder: 'Filtrar locais por nome, bairro ou zona', 'aria-label': 'Filtrar locais de votação' });
    const cont = h('p', { class: 'ajuda', role: 'status' });
    const corpo = h('tbody');
    const mais = h('button', { type: 'button', class: 'btn btn-sec' }, 'Mostrar mais locais');
    let limite = 50;
    const desenhar = () => {
      const q = inp.value.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase();
      const ls = locais.filter((l) => [l.nome, l.bairro, l.zona, l._municipio].join(' ').normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase().includes(q));
      corpo.replaceChildren(...ls.slice(0, limite).map((l) => h('tr', {},
        h('td', {}, h('a', { href: `#uf=${uf}&z=${l.zona}&l=${encodeURIComponent(l.local_id)}` }, caixa(l.nome)), h('small', { style: 'display:block' }, [l._municipio, caixa(l.bairro)].filter(Boolean).join(' · '))),
        h('td', {}, h('a', { href: `#uf=${uf}&z=${l.zona}&visao=zona` }, String(l.zona))), h('td', {}, f0(l.n_secoes)), h('td', {}, pc(l.fatia_f2)))));
      cont.textContent = f0(ls.length) + ' locais encontrados · ' + f0(Math.min(limite, ls.length)) + ' exibidos';
      mais.hidden = limite >= ls.length;
    };
    inp.addEventListener('input', () => { limite = 50; desenhar(); });
    mais.addEventListener('click', () => { limite += 100; desenhar(); });
    desenhar();
    return h('section', {}, h('h3', {}, 'Explore os locais de votação'), inp, cont,
      h('div', { class: 'visoes-lista', tabindex: '0', role: 'region', 'aria-label': 'Locais de votação' }, h('table', {},
        h('thead', {}, h('tr', {}, ['Local de votação', 'Zona', 'Seções', 'Flávio entre os dois, 2º turno'].map((s) => h('th', { scope: 'col' }, s)))), corpo)), mais);
  }
  function render({ uf, tipo, titulo, totais, locais, ref, relacionados }) {
    E.atual = { tipo, ...ref };
    const url = tipo === 'zona' ? `#uf=${uf}&z=${ref.zona}&visao=zona` : `#uf=${uf}&mun=${ref.mun}&visao=municipio`;
    return h('article', { class: 'ficha visao-agregada', 'data-visao': tipo },
      h('p', { class: 'kicker' }, 'Visão de ' + (tipo === 'zona' ? 'zona eleitoral' : 'município') + ' · ' + uf), h('h2', {}, titulo), nav(ref, tipo),
      h('div', { class: 'visoes-resumo' }, [[totais.n_secoes, 'seções'], [locais.length, 'locais de votação'], [totais.n_bu2, 'seções com boletim do 2º turno']].map(([n, nome]) => h('div', {}, h('b', {}, f0(n)), nome))),
      h('p', { class: 'ajuda' }, 'Boletins dos dois turnos, somados neste recorte. Percentuais calculados depois da soma dos votos. A cobertura pode diferir entre turnos.'),
      placar(totais), window.PolitizePerfil.painel(ref,titulo), window.PolitizeCrimes.painel(uf), window.PolitizeSeguranca.painel({ ...ref, locais: locais.map((l) => l.local_id) }), mov.painel(ref, titulo),
      h('p', { class: 'visoes-aviso' }, 'Zona eleitoral e município são recortes que se cruzam: uma zona pode atender vários municípios e um município pode ter várias zonas. Os links abaixo abrem cada recorte inteiro.'),
      h('h3', {}, tipo === 'zona' ? 'Municípios atendidos por esta zona' : 'Zonas que atendem este município'), relacionados,
      h('p', { class: 'ajuda' }, '2º turno: ' + f0(totais.secoes_sinal) + ' seções com sinais · ' + f0(totais.urnas_trocadas) + ' urnas trocadas entre turnos. Sinais pedem explicação, não provam irregularidade.'),
      listaLocais(uf, locais), h('p', { class: 'botoes' },
        h('a', { class: 'btn btn-sec', href: 'politizese.html' + url }, 'Link desta visão'),
        h('a', { class: 'btn btn-sec', href: `politizese_mapa.html#uf=${uf}&${tipo === 'zona' ? 'zona=' + ref.zona : 'mun=' + ref.mun}&camada=pico` }, 'Ver movimento no mapa')));
  }
  async function zona(uf, z) {
    if (!(E.indice.zonas[uf] || []).map(Number).includes(Number(z))) throw new ErroUsuario('Zona não encontrada nesta UF.');
    const d = await carregarZona(uf, Number(z));
    const ls = d.listaLocais.map((l) => ({ ...l, zona: Number(z), _municipio: d.municipios[l.mun_tse]?.nome }));
    const refs = Object.entries(d.municipios).map(([mun, m]) => h('a', { href: `#uf=${uf}&mun=${mun}&visao=municipio` }, m.nome));
    return render({ uf, tipo: 'zona', titulo: `Zona ${Number(z)} · ${uf}`, totais: totalizar(ls), locais: ls, ref: { uf, zona: Number(z) }, relacionados: h('div', { class: 'visoes-links' }, refs) });
  }
  async function municipio(m) {
    const { d, locais } = await carregarMun(m);
    const zs = [...new Set(locais.map((l) => l.zona))].sort((a, b) => a - b);
    return render({ uf: m.uf, tipo: 'municipio', titulo: `${m.nome} · ${m.uf}`, totais: d.totais, locais, ref: { uf: m.uf, mun: String(m.mun_tse).padStart(5, '0') },
      relacionados: h('div', { class: 'visoes-links' }, zs.map((z) => h('a', { href: `#uf=${m.uf}&z=${z}&visao=zona` }, 'Zona ' + z))) });
  }
  function configurar() {
    document.querySelector('#ver-zona').addEventListener('click', () => {
      const uf = document.querySelector('#s-uf').value, z = Number(document.querySelector('#s-zona').value);
      executar('Abrindo a zona', () => zona(uf, z));
    });
  }
  function hash(p) {
    const uf = (p.get('uf') || '').toUpperCase(), z = Number(p.get('z'));
    if (p.get('visao') === 'zona') { executar('Abrindo a zona', () => zona(uf, z)); return true; }
    if (p.get('visao') === 'municipio') {
      const m = E.porChave.get(uf + '|' + Number(p.get('mun')));
      executar('Abrindo o município', () => { if (!m) throw new ErroUsuario('Município não encontrado nesta UF.'); return municipio(m); }); return true;
    }
    return false;
  }
  return { nav, zona, municipio, configurar, hash, totalizar };
}
