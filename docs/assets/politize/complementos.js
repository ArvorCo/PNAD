// Seções recuperadas após o catálogo histórico: consulta operacional própria.
import { blocoLogs } from './logs.js?v=20261015-8';

export async function buscarComplemento(buscar, uf, zona, secao) {
  const dados = await buscar('assets/logs_urnas_2026/complementos.json');
  return dados && dados[`${uf}-${zona}-${secao}`] || null;
}

export async function mostrarComplemento({ h, buscar, r, alvo, limpar, vigente }) {
  const c = r.complemento;
  const logs = await blocoLogs({ h, buscar, uf: c.uf, zona: c.zona,
    secao: { secao: c.secao }, local: { local_id: c.local_id } });
  if (!vigente()) return;
  const titulo = h('h2', { tabindex: '-1' }, `Seção ${c.secao}`);
  const cab = h('section', { class: 'sua-secao entra' },
    h('p', { class: 'kicker' }, `${c.municipio} · ${c.uf} · Zona ${c.zona}`), titulo,
    h('p', { class: 'sub' }, c.local || `Local ${c.local_id.split('-').at(-1)}: endereço não disponível no cadastro publicado.`),
    h('p', {}, 'O BU e o log desta seção foram recuperados após o catálogo original. A análise operacional está abaixo; a classificação histórica e o perfil de conversa desta seção ainda não foram calculados.'),
    c.local_disponivel ? h('p', {}, h('a', { href: `politizesuavizinhanca.html#l=${encodeURIComponent(c.local_id)}` }, 'Consultar o local de votação no catálogo histórico'), ' — os totais daquele catálogo não incluem esta seção suplementar.') : null);
  alvo.replaceChildren(
    h('div', { class: 'nova-busca' }, h('button', { type: 'button', class: 'btn btn-sec', onclick: limpar }, 'Nova busca')),
    cab, h('article', { class: 'fiscal entra' }, h('div', { class: 'fis-corpo' }, logs)));
  document.querySelector('#resultado').setAttribute('aria-busy', 'false');
  history.replaceState(null, '', `${location.pathname}${location.search}#s=${c.uf}-${c.zona}-${c.secao}`);
  document.title = `Seção ${c.secao} · ${c.municipio} · Politize sua vizinhança`;
  titulo.focus({ preventScroll: true });
  document.querySelector('#resultado').scrollIntoView({ block: 'start' });
}
