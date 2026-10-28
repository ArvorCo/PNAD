import { criarRelatos } from './relatos.js?v=20261028';
// Politize-se: aplicativo estático, escrito à mão, sem framework e sem build.
// Cópia adaptada do aplicativo do Politize sua vizinhança (busca por seção, CEP, cidade e
// localização), sem importar nada dele: o antigo segue intacto como arquivo.
// Lê os JSON de docs/assets/politize_se/dados/ (contrato em analysis/politize_se/CONTRATO.md).
// Não calcula métrica eleitoral: lê, ordena por distância e formata. A seção digitada, o CEP e a
// coordenada não saem do aparelho e não vão para o endereço da página.

const HOST = location.hostname;
const DEV = ['localhost', '127.0.0.1', '[::1]', '::1'].includes(HOST) || HOST.endsWith('.localhost') || HOST.endsWith('.test');
const QS = new URLSearchParams(location.search);
function caminhoDev() {
  const v = QS.get('dados');
  if (!DEV || !v) return null;
  if (!/^[\w./-]+$/.test(v) || v.startsWith('/') || v.includes('//') || /^[a-z]+:/i.test(v)) return null;
  return v.endsWith('/') ? v : `${v}/`;
}
const BASE = caminhoDev() || 'assets/politize_se/dados/';
const URL_PUBLICA = 'https://brasil.arvor.co/politizese.html';
const N_AO_REDOR = 6;

const NOME_UF = {
  AC: 'Acre', AL: 'Alagoas', AP: 'Amapá', AM: 'Amazonas', BA: 'Bahia', CE: 'Ceará', DF: 'Distrito Federal',
  ES: 'Espírito Santo', GO: 'Goiás', MA: 'Maranhão', MT: 'Mato Grosso', MS: 'Mato Grosso do Sul', MG: 'Minas Gerais',
  PA: 'Pará', PB: 'Paraíba', PR: 'Paraná', PE: 'Pernambuco', PI: 'Piauí', RJ: 'Rio de Janeiro',
  RN: 'Rio Grande do Norte', RS: 'Rio Grande do Sul', RO: 'Rondônia', RR: 'Roraima', SC: 'Santa Catarina',
  SP: 'São Paulo', SE: 'Sergipe', TO: 'Tocantins', ZZ: 'Exterior',
};

const E = { indice: null, muns: [], porChave: new Map(), cache: new Map(), pedido: 0, cidade: null, atual: null };
const $ = (s) => document.querySelector(s);

/* ------------------------------------------------------------------ utilidades */

function h(tag, attrs = {}, ...filhos) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === 'class') n.className = v;
    else if (k === 'style') n.setAttribute('style', v);
    else if (k.startsWith('on') && typeof v === 'function') n.addEventListener(k.slice(2), v);
    else n.setAttribute(k, v === true ? '' : String(v));
  }
  for (const f of filhos.flat(Infinity)) {
    if (f === null || f === undefined || f === false || f === '') continue;
    n.append(f instanceof Node ? f : document.createTextNode(String(f)));
  }
  return n;
}
const norm = (s) => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/\s+/g, ' ').trim();
const num = (v) => (typeof v === 'number' && Number.isFinite(v) ? v : null);
const nf1 = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const nf0 = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 });
const SD = 'sem dado';
const f1 = (v) => (num(v) === null ? SD : nf1.format(v));
const f0 = (v) => (num(v) === null ? SD : nf0.format(Math.round(v)));
const pc = (v) => (num(v) === null ? SD : `${nf1.format(v)}%`);
const pp = (v) => {
  if (num(v) === null) return SD;
  const r = Math.round(v * 10) / 10;
  return `${r > 0 ? '+' : r < 0 ? '−' : ''}${nf1.format(Math.abs(r))}`;
};
function hora(m) {
  if (num(m) === null) return SD;
  const dias = Math.floor(m / 1440);
  const r = ((m % 1440) + 1440) % 1440;
  const s = `${String(Math.floor(r / 60)).padStart(2, '0')}h${String(r % 60).padStart(2, '0')}`;
  return dias > 0 ? `${s} do dia seguinte` : s;
}
function haversine(a, b) {
  if (!a || !b || num(a.lat) === null || num(b.lat) === null || num(a.lon) === null || num(b.lon) === null) return null;
  const R = 6371008.8;
  const r = Math.PI / 180;
  const s = Math.sin(((b.lat - a.lat) * r) / 2) ** 2 + Math.cos(a.lat * r) * Math.cos(b.lat * r) * Math.sin(((b.lon - a.lon) * r) / 2) ** 2;
  return 2 * R * Math.asin(Math.min(1, Math.sqrt(s)));
}
function distTxt(m) {
  if (num(m) === null) return '';
  if (m < 950) return `${nf0.format(Math.max(50, Math.round(m / 50) * 50))} m`;
  return `${nf1.format(m / 1000)} km`;
}
const SIGLAS = new Set(['EMEF', 'EMEI', 'EE', 'EEF', 'EEEFM', 'EMEB', 'CIEP', 'CAIC', 'CEFET', 'ETEC', 'FATEC', 'UPA', 'APAE', 'CEI', 'CMEI',
  'CE', 'CEM', 'EM', 'II', 'III', 'IV', 'VI', 'VII', 'VIII', 'IX', 'XI', 'XII', 'SESC', 'SESI', 'SENAI', 'SENAC', 'CEU', 'IFSP', 'CRAS']);
const MINUSC = new Set(['de', 'da', 'do', 'das', 'dos', 'e', 'em', 'na', 'no', 'nas', 'nos', 'a', 'o', 'as', 'os', 'para', 'com', 'por']);
// O cadastro do TSE vem em CAIXA ALTA. Só converte quando o texto inteiro está em maiúsculas.
function caixa(s) {
  const t = String(s || '').replace(/\s+/g, ' ').trim();
  if (!t || t !== t.toUpperCase()) return t;
  return t.split(' ').map((w, i) => {
    const limpa = w.replace(/[^\p{L}\p{N}]/gu, '');
    if (SIGLAS.has(limpa) || /\d/.test(w) || (limpa.length >= 2 && !/[AEIOUÁÉÍÓÚÂÊÔÃÕÀ]/u.test(limpa))) return w;
    const lw = w.toLocaleLowerCase('pt-BR');
    if (i > 0 && MINUSC.has(lw)) return lw;
    return lw.replace(/(^|[-'(/])(\p{L})/gu, (m, p, c) => p + c.toLocaleUpperCase('pt-BR'));
  }).join(' ');
}
const cepFmt = (c) => {
  const d = String(c || '').replace(/\D/g, '');
  return d.length === 8 && !/^0+$/.test(d) ? `${d.slice(0, 5)}-${d.slice(5)}` : '';
};

class ErroDados extends Error {
  constructor(msg, status = 0) {
    super(msg);
    this.status = status;
  }
}
class ErroUsuario extends Error {}

function buscarJSON(url) {
  if (E.cache.has(url)) return E.cache.get(url);
  const p = (async () => {
    let r;
    try {
      r = await fetch(url, { credentials: 'same-origin' });
    } catch (e) {
      throw new ErroDados(e.message || 'falha de rede');
    }
    if (!r.ok) throw new ErroDados(`HTTP ${r.status}`, r.status);
    const blob = await r.blob();
    const ini = new Uint8Array(await blob.slice(0, 2).arrayBuffer());
    if (ini[0] !== 31 || ini[1] !== 139) return JSON.parse(await blob.text());
    if (!globalThis.DecompressionStream) throw new ErroDados('navegador-sem-gzip');
    return new Response(blob.stream().pipeThrough(new DecompressionStream('gzip'))).json();
  })();
  E.cache.set(url, p);
  p.catch(() => E.cache.delete(url));
  return p;
}
function tabela(t) {
  if (!t || !Array.isArray(t.colunas) || !Array.isArray(t.linhas)) return [];
  return t.linhas.map((l) => Object.fromEntries(t.colunas.map((c, i) => [c, l[i] === undefined ? null : l[i]])));
}

// Frases geradas por regra no build: [código, arg0, arg1, ...]; os modelos vêm do índice.
function frase(lista) {
  const cods = (E.indice && E.indice.frases_codigos) || [];
  const mod = (E.indice && E.indice.frases) || {};
  return (lista || []).map(([i, ...args]) => {
    let t = mod[cods[i]] || '';
    args.forEach((a, j) => { t = t.split(`{${j}}`).join(String(a)); });
    return /\{\d\}/.test(t) ? '' : t;
  }).filter(Boolean).join(' ');
}

/* ------------------------------------------------------------------ dados */

const chaveMun = (uf, mun) => `${uf}|${Number(mun)}`;
function prepararIndice(ind) {
  E.indice = ind;
  E.muns = tabela(ind.municipios).map((m) => ({ ...m, chave: chaveMun(m.uf, m.mun_tse), busca: norm(m.nome) }));
  for (const m of E.muns) E.porChave.set(m.chave, m);
}
async function carregarZona(uf, zona) {
  const d = await buscarJSON(`${BASE}zona/${uf}/${zona}.json.gz`);
  if (d._pronto) return d;
  const c1 = d.locais.clima1 || [];
  const c2 = d.locais.clima2 || [];
  const c2o = d.locais.clima2o || [];
  d.listaLocais = tabela(d.locais).map((l, i) => ({
    ...l,
    li: i,
    clima1: Array.isArray(l.clima1) ? Object.fromEntries(c1.map((k, j) => [k, l.clima1[j]])) : null,
    clima2: Array.isArray(l.clima2) ? Object.fromEntries(c2.map((k, j) => [k, l.clima2[j]])) : null,
    clima2o: Array.isArray(l.clima2o) ? Object.fromEntries(c2o.map((k, j) => [k, l.clima2o[j]])) : null,
  }));
  d.listaSecoes = tabela(d.secoes);
  d._pronto = true;
  return d;
}
async function carregarMun(m) {
  const d = await buscarJSON(`${BASE}${m.arquivo}`);
  return { d, locais: tabela(d.locais).map((l) => ({ ...l, _uf: m.uf, _mun: m })) };
}
function munDoLocal(id) {
  const p = String(id || '').split('-');
  return p.length >= 4 ? E.porChave.get(chaveMun(p[0], p[1])) : null;
}

/* ------------------------------------------------------------------ estados */

function aviso(texto, titulo = 'Aviso', erro = false) {
  return h('p', { class: erro ? 'aviso erro' : 'aviso' }, h('strong', {}, titulo), texto);
}
const alvo = () => $('#resultado-in');
function estadoCarregando(msg) {
  $('#resultado').setAttribute('aria-busy', 'true');
  alvo().replaceChildren(h('p', { class: 'carregando' }, `${msg}...`));
}
function estadoErro(msg, tentar) {
  $('#resultado').setAttribute('aria-busy', 'false');
  alvo().replaceChildren(...[aviso(msg, 'Não deu certo', true), tentar ? h('button', { type: 'button', class: 'btn btn-sec', onclick: tentar }, 'Tentar de novo') : null].filter(Boolean));
}
function msgErro(e) {
  if (e instanceof ErroUsuario) return e.message;
  if (e && e.message === 'navegador-sem-gzip') return 'Este navegador não abre os dados compactados. Use uma versão atual do navegador.';
  if (e instanceof ErroDados && e.status === 404) return 'Esses dados não estão publicados nesta versão. Confira os números digitados.';
  return 'Não foi possível carregar os dados agora. Verifique a conexão e tente de novo.';
}
async function executar(msg, fn) {
  const meu = ++E.pedido;
  estadoCarregando(msg);
  try {
    const no = await fn();
    if (meu !== E.pedido) return;
    $('#resultado').setAttribute('aria-busy', 'false');
    alvo().replaceChildren(no);
    const t = alvo().querySelector('h2');
    if (t) {
      t.setAttribute('tabindex', '-1');
      t.focus({ preventScroll: true });
      $('#resultado').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  } catch (e) {
    if (meu !== E.pedido) return;
    estadoErro(msgErro(e), e instanceof ErroUsuario ? null : () => executar(msg, fn));
  }
}

/* ------------------------------------------------------------------ busca */

async function porSecao(uf, zona, secao) {
  const zs = E.indice.zonas[uf];
  if (!Array.isArray(zs)) throw new ErroUsuario(`Não há dados de ${NOME_UF[uf] || uf} nesta versão.`);
  if (!zs.map(Number).includes(zona)) {
    const lista = zs.map(Number).sort((a, b) => a - b);
    const amostra = lista.length > 12 ? `${lista.slice(0, 12).join(', ')} e outras` : lista.join(', ');
    throw new ErroUsuario(`A zona ${zona} não existe em ${NOME_UF[uf] || uf} nos dados. Zonas: ${amostra}. Confira no título ou no e-Título.`);
  }
  const zd = await carregarZona(uf, zona);
  let sec = zd.listaSecoes.find((x) => Number(x.secao) === secao);
  let agregada = null;
  if (!sec) {
    sec = zd.listaSecoes.find((x) => (x.agregadas2 || []).map(Number).includes(secao))
      || zd.listaSecoes.find((x) => (x.agregadas1 || []).map(Number).includes(secao));
    if (sec) agregada = secao;
  }
  if (!sec) throw new ErroUsuario(`A seção ${secao} não está na zona ${zona} de ${NOME_UF[uf] || uf}. Confira os números no título ou no e-Título.`);
  return renderSecao(uf, zd, sec, { agregada });
}
async function porLocal(id, extra = {}) {
  const p = String(id).split('-');
  const uf = p[0];
  const zona = Number(p[2]);
  const zd = await carregarZona(uf, zona);
  const local = zd.listaLocais.find((l) => l.local_id === id);
  if (!local) throw new ErroUsuario('Esse local de votação não está nos dados desta versão. Busque pela seção ou pela cidade.');
  return renderLocal(uf, zd, local, extra);
}
function maisPerto(locais, ref) {
  return locais.map((l) => ({ l, d: haversine(ref, l) })).sort((a, b) => {
    if (a.d === null && b.d === null) return (b.l.aptos2 || b.l.aptos1 || 0) - (a.l.aptos2 || a.l.aptos1 || 0);
    if (a.d === null) return 1;
    if (b.d === null) return -1;
    return a.d - b.d;
  });
}
function centro(ls) {
  const c = ls.filter((l) => num(l.lat) !== null && num(l.lon) !== null);
  return c.length ? { lat: c.reduce((s, l) => s + l.lat, 0) / c.length, lon: c.reduce((s, l) => s + l.lon, 0) / c.length } : null;
}
async function porCep(d) {
  const arq = await buscarJSON(`${BASE}cep/${d.slice(0, 2)}.json`).catch((e) => {
    if (e.status === 404) return null;
    throw e;
  });
  if (!arq) throw new ErroUsuario(`Não há local de votação com CEP começando em ${d.slice(0, 2)}. Tente pela cidade.`);
  const ex = arq.exato || {};
  const p5 = arq.prefixo5 || {};
  let ids = ex[d] || p5[d.slice(0, 5)] || null;
  let aprox = !ex[d];
  if (!ids) {
    const alvo5 = Number(d.slice(0, 5));
    const ch = Object.keys(p5).filter((k) => k.startsWith(d.slice(0, 3))).sort((a, b) => Math.abs(Number(a) - alvo5) - Math.abs(Number(b) - alvo5));
    ids = ch.length ? p5[ch[0]] : null;
    aprox = true;
  }
  if (!ids || !ids.length) throw new ErroUsuario(`Não achamos local de votação com CEP parecido com ${cepFmt(d)}. Tente pela cidade.`);
  const muns = [...new Map(ids.map(munDoLocal).filter(Boolean).map((m) => [m.chave, m])).values()];
  if (!muns.length) throw new ErroUsuario('Os locais desse CEP não estão no índice desta versão.');
  const pacotes = await Promise.all(muns.map(carregarMun));
  const todos = pacotes.flatMap((p) => p.locais);
  const set = new Set(ids);
  const achados = todos.filter((l) => set.has(l.local_id));
  if (!achados.length) throw new ErroUsuario('Os locais desse CEP não foram encontrados nos arquivos dos municípios.');
  const ref = centro(achados);
  const escolhido = maisPerto(achados, ref)[0].l;
  return porLocal(escolhido.local_id, { aoRedor: maisPerto(todos, escolhido).slice(1, N_AO_REDOR + 1), nota: aprox ? 'O CEP digitado não é de um local de votação; mostramos o local com CEP mais parecido.' : null });
}
async function porCidade(m, bairro) {
  const { locais } = await carregarMun(m);
  const cand = bairro ? locais.filter((l) => (l.bairro || '') === bairro) : locais;
  if (!cand.length) throw new ErroUsuario('Esse bairro não tem local de votação nos dados.');
  const ref = bairro ? centro(cand) : (num(m.lat) !== null ? { lat: m.lat, lon: m.lon } : centro(locais));
  const escolhido = maisPerto(cand, ref)[0].l;
  return porLocal(escolhido.local_id, { aoRedor: maisPerto(locais, escolhido).slice(1, N_AO_REDOR + 1) });
}
async function porPosicao(pos) {
  const voce = { lat: pos.coords.latitude, lon: pos.coords.longitude };
  const muns = E.muns.filter((m) => num(m.lat) !== null).map((m) => [m, haversine(voce, m)]).sort((a, b) => a[1] - b[1]).slice(0, 4).map((x) => x[0]);
  if (!muns.length) throw new ErroUsuario('O índice desta versão não tem coordenadas de municípios.');
  const res = await Promise.allSettled(muns.map(carregarMun));
  const todos = res.filter((r) => r.status === 'fulfilled').flatMap((r) => r.value.locais);
  const ord = maisPerto(todos, voce).filter((x) => x.d !== null);
  if (!ord.length) throw new ErroUsuario('Não achamos local de votação com coordenada perto de você.');
  return porLocal(ord[0].l.local_id, {
    aoRedor: ord.slice(1, N_AO_REDOR + 1),
    nota: ord[0].d > 50000 ? 'O local mais próximo está a mais de 50 km. Confira se a localização do aparelho está certa.' : null,
  });
}

/* ------------------------------------------------------------------ peças da ficha */

const cats = () => (E.indice && E.indice.catalogos) || {};
function barraEmpilhada(partes, rotulo) {
  const total = partes.reduce((s, p) => s + (num(p.v) || 0), 0);
  if (!total) return h('p', { class: 'ajuda' }, 'Sem dados para desenhar.');
  return [
    h('div', { class: 'barra-empilhada', role: 'img', 'aria-label': rotulo },
      partes.filter((p) => num(p.v) > 0).map((p) => h('span', { class: p.c, style: `width:${(100 * p.v) / total}%` }))),
    h('p', { class: 'leg' }, partes.map((p) => h('span', {}, h('i', { class: p.c, 'aria-hidden': 'true' }), `${p.r}: ${f0(p.v)} (${pc((100 * (p.v || 0)) / total)})`))),
  ];
}
function blocoTurno(t, s) {
  const um = t === 1;
  const aptos = s[`aptos${t}`];
  const comp = s[`comp${t}`];
  if (s.pequena) return h('div', { class: 'turno' }, h('h4', {}, `${t}º turno`), h('p', { class: 'ajuda' }, 'Seção com menos de 30 eleitores aptos: os votos não aparecem.'));
  if (!um && !s.bu2) return h('div', { class: 'turno' }, h('h4', {}, '2º turno'), h('p', { class: 'ajuda' }, 'Boletim ainda não lido pela nossa coleta.'));
  if (num(aptos) === null || num(comp) === null) return h('div', { class: 'turno' }, h('h4', {}, `${t}º turno`), h('p', { class: 'ajuda' }, 'Sem boletim desta seção neste turno.'));
  const partes = [
    { r: 'Flávio', v: s[`flavio${t}`], c: 'c-flavio' },
    { r: 'Lula', v: s[`lula${t}`], c: 'c-lula' },
    ...(um ? [{ r: 'Demais candidaturas', v: s.terceira1, c: 'c-outros' }] : []),
    { r: 'Brancos e nulos', v: (s[`brancos${t}`] || 0) + (s[`nulos${t}`] || 0), c: 'c-bn' },
    { r: 'Não votaram', v: aptos - comp, c: 'c-abst' },
  ];
  return h('div', { class: 'turno' }, h('h4', {}, `${t}º turno · ${f0(aptos)} aptos`), barraEmpilhada(partes, `${t}º turno: votos e abstenção sobre os aptos`));
}
function blocoBio(t, s) {
  const comp = s[`comp${t}`];
  const sem = s[`sem_bio${t}`];
  const ano = s[`ano_nasc${t}`];
  const bio = s[`hab_bio${t}`];
  if (s.pequena || num(comp) === null || num(sem) === null) return h('div', { class: 'turno' }, h('h4', {}, `Identificação · ${t}º turno`), h('p', { class: 'ajuda' }, 'Sem dado.'));
  return h('div', { class: 'turno' }, h('h4', {}, `Identificação · ${t}º turno`), barraEmpilhada([
    { r: 'Digital reconhecida', v: bio, c: 'c-bio' },
    { r: 'Ano de nascimento', v: ano, c: 'c-ano' },
    { r: 'Sem digital cadastrada', v: sem, c: 'c-sem' },
  ], `${t}º turno: como quem votou foi identificado`));
}
function tabelaTurnos(s) {
  const lin = (r, a, b, cls = '') => h('tr', {}, h('th', { scope: 'row' }, r), h('td', { class: `n ${cls}` }, a), h('td', { class: `n ${cls}` }, b));
  const pe = s.pequena;
  const v = (k) => (pe ? '' : f0(s[k]));
  const p = (k) => (pe ? '' : pc(s[k]));
  const modelo = (t) => [s[`modelo${t}`], s[`urna${t}`] ? `nº ${s[`urna${t}`]}` : null].filter(Boolean).join(' · ') || SD;
  const tipo = (t) => (cats().modelos_urna || {})[String(s[`tipo_urna${t}`])] || SD;
  const fuso = s._uf === 'ZZ' ? 'hora local' : 'Brasília';
  return h('div', { class: 'tabela-rolagem', tabindex: '0', role: 'region', 'aria-label': 'Primeiro e segundo turno lado a lado' },
    h('table', { class: 'tabela' },
      h('thead', {}, h('tr', {}, h('th', { scope: 'col' }, ''), h('th', { scope: 'col', class: 'n' }, '1º turno'), h('th', { scope: 'col', class: 'n' }, '2º turno'))),
      h('tbody', {},
        lin('Eleitores aptos', f0(s.aptos1), f0(s.aptos2)),
        lin('Votaram', v('comp1'), v('comp2')),
        lin('Comparecimento', p('comp_pct1'), p('comp_pct2')),
        lin('Abstenção', p('abst_pct1'), p('abst_pct2')),
        lin('Flávio, votos', v('flavio1'), v('flavio2')),
        lin('Lula, votos', v('lula1'), v('lula2')),
        lin('Demais candidaturas', v('terceira1'), pe ? '' : 'não há'),
        lin('Brancos', v('brancos1'), v('brancos2')),
        lin('Nulos', v('nulos1'), v('nulos2')),
        lin('Brancos e nulos, % de quem votou', p('bn_pct1'), p('bn_pct2')),
        lin('Flávio entre os dois', p('fatia_f1'), p('fatia_f2')),
        lin('Sem digital cadastrada, % de quem votou', p('sem_bio_pct1'), p('sem_bio_pct2')),
        lin('Liberados pelo ano de nascimento', p('ano_nasc_pct1'), p('ano_nasc_pct2')),
        lin(`Primeiro voto (${fuso})`, hora(s.abert1), hora(s.abert2)),
        lin(`Último voto (${fuso})`, hora(s.enc1), hora(s.enc2)),
        lin('Boletim recebido pelo TSE (Brasília)', hora(s.rec1), hora(s.rec2)),
        lin('Urna', modelo(1), modelo(2)),
        lin('Tipo de urna', tipo(1), tipo(2)),
        lin('Cargas da urna', f0(s.cargas1), f0(s.cargas2)),
      )));
}
function blocoSinais(s) {
  const c = cats();
  const itens = [];
  if (!s.bu2) itens.push(h('p', {}, 'Os sinais do 2º turno aparecem quando o boletim desta seção for lido.'));
  else if (!(s.sinais || []).length) itens.push(h('p', {}, 'Nenhum dos seis sinais acendeu.'));
  else {
    itens.push(h('ul', { class: 'lista-sinais' }, s.sinais.map((k) => h('li', {}, (c.sinais || {})[k] || k))));
    const exp = (s.explicacoes || []).map((k) => (c.explicacoes || {})[k]).filter(Boolean);
    itens.push(h('p', {}, exp.length ? `Explicação provável: ${exp.join('; ')}.` : 'Nenhuma explicação provável pela regra: vale conferir a ata da seção e o log da urna.'));
  }
  itens.push(h('p', { class: 'rotulo-casa' }, (E.indice && E.indice.rotulo) || 'Sinal pede explicação, não prova irregularidade.'));
  return h('div', { class: 'caixa' }, h('h4', {}, `Sinais do 2º turno${num(s.escore) !== null ? ` · escore ${s.escore} de 6` : ''}`), itens);
}
// Grupo da mistura estatística dos dois turnos (motor do dossiê): grupo, densidade em
// palavras e o rótulo da casa. Sem o arquivo do motor, os três campos vêm nulos.
function blocoMl(s) {
  const ml = cats().ml || {};
  const rotulo = ml.rotulo_casa || 'Atipicidade estatística não é irregularidade: o grupo pede explicação, não prova nada.';
  const itens = [];
  if (!s.bu2 || num(s.ml_grupo) === null || s.ml_anomalo === null || s.ml_anomalo === undefined) {
    itens.push(h('p', {}, 'A análise estatística dos dois turnos ainda não cobre esta seção.'));
  } else {
    const nome = (ml.rotulos || {})[String(s.ml_grupo)] || '';
    const densidade = num(s.ml_p) === null ? '' : s.ml_p < 0.01 ? 'entre as 1% menos prováveis do país' : s.ml_p < 0.05 ? 'entre as 5% menos prováveis do país' : 'densidade comum';
    itens.push(h('p', {}, h('b', {}, s.ml_anomalo ? 'No grupo atípico do país.' : 'Fora do grupo atípico.'), ` Grupo ${s.ml_grupo}${ml.k ? ` de ${ml.k}` : ''}${nome ? `: ${nome}` : ''}.${densidade ? ` Densidade: ${densidade}.` : ''}`));
    itens.push(h('p', { class: 'ajuda' }, 'Grupos definidos por mistura estatística sobre as frações do eleitorado nos dois turnos (votos de cada candidato, brancos, nulos e comparecimento sobre os aptos), sem o exterior. Os grupos são numerados a partir de zero, como no dossiê.'));
  }
  itens.push(h('p', { class: 'rotulo-casa' }, rotulo));
  return h('div', { class: 'caixa' }, h('h4', {}, 'Grupo estatístico'), itens);
}
function blocoUrna(s) {
  const c = cats();
  const t = s.urna_situacao ? (c.urna || {})[s.urna_situacao] : null;
  const mesma = s.urna_situacao === 'mesma' || s.urna_situacao === 'mesma_recarga';
  const veredito = !s.bu2 || !s.urna_situacao || s.urna_situacao === 'sem_1t' ? null : mesma ? 'Mesma urna nos dois turnos' : 'Urna trocada';
  const mod = (t) => s[`modelo${t}`] || 'modelo sem dado';
  return h('div', { class: 'caixa' }, h('h4', {}, 'A urna'),
    h('p', {}, h('b', {}, `1º turno: ${mod(1)} · 2º turno: ${s.bu2 ? mod(2) : 'boletim ainda não lido'}`), veredito ? `. ${veredito}.` : ''),
    h('p', {}, t || 'Sem os dois boletins para comparar a urna.'),
    s.contingencia2 ? h('p', {}, 'O boletim do 2º turno registra urna de contingência ou mais de uma carga, o que costuma acompanhar troca de urna no dia.') : null,
    h('p', { class: 'ajuda' }, 'Troca de urna tem explicação técnica comum: defeito, substituição ou reserva. O número interno e a carga vêm dos dois boletins.'));
}
function blocoLogs(s) {
  const c = cats();
  const nivel = (a) => (a === null || a === undefined ? null : ((c.log_niveis || {})[String(a)] || {}).nome || String(a));
  const fams = (l) => (l || []).map((k) => ((c.log_familias || {})[k] || {}).curto || k);
  const nomes = (l) => (l || []).map((k) => (c.log || {})[k]).filter(Boolean);
  const linha = (t, a, sin, fam) => h('p', {}, a === null || a === undefined
    ? `${t}: sem log processado para esta seção.`
    : `${t}: ${nivel(a)} (atenção ${a} de 3)${fam.length ? `, família ${fam.join(', ')}` : ''}. ${sin.length ? `${sin.join('; ')}.` : 'Sem ocorrência no log.'}`);
  const rein = (s.log2_reinicios || []).filter((x) => Array.isArray(x));
  const bat = { simultanea: 'passou para a bateria junto com outras urnas do município', isolada: 'passou para a bateria sozinha', votacao: 'passou para a bateria' }[s.log2_bateria];
  const meta = Array.isArray(s.log2_meta) ? s.log2_meta : null;
  return h('div', { class: 'caixa' }, h('h4', {}, 'Logs das urnas, 1º e 2º turno'),
    linha('1º turno', s.log1_atencao, nomes(s.log1_sinais), fams(s.log1_familias)),
    linha('2º turno', s.log2_atencao, nomes(s.log2_sinais), fams(s.log2_familias)),
    rein.length ? h('ul', { class: 'lista-sinais' }, rein.map(([m, a, d]) => h('li', {}, `Urna religada durante a votação às ${hora(m)}: ${f0(a)} votos antes, ${f0(d)} depois.`))) : null,
    bat ? h('p', {}, `Durante a votação do 2º turno, a urna ${bat}${num(s.log2_bateria_simultaneas) > 0 ? ` (${f0(s.log2_bateria_simultaneas)} outras no mesmo minuto)` : ''}.`) : null,
    num(s.log2_erro_mr) > 0 ? h('p', { class: 'ajuda' }, 'O aviso de problema ao desmontar a memória de resultado antes da zerésima é rotina da urna religada com a mesma carga; não conta como erro técnico.') : null,
    meta ? h('p', { class: 'ajuda' }, `Urna no 2º turno: versão ${meta[0] || SD}; carga registrada em ${meta[1] || SD}; memória de resultado ${meta[2] || SD}.`) : null,
    h('p', { class: 'rotulo-casa' }, (E.indice && E.indice.rotulo) || 'Sinal pede explicação, não prova irregularidade.'),
    h('p', { class: 'ajuda' }, h('a', { href: 'logs_urnas_2026.html' }, 'Como lemos os logs')));
}
function blocoFiscal(s) {
  const c = cats();
  if (!s.fiscal_nivel) return null;
  const niv = (c.fiscal_niveis || {})[s.fiscal_nivel] || {};
  const crit = (s.fiscal_sinais || []).map((k) => (c.fiscal_criterios || {})[k]).filter(Boolean);
  return h('div', { class: 'caixa' }, h('h4', {}, 'Fiscalização recomendada antes do 2º turno'),
    h('p', {}, `${niv.nome || s.fiscal_nivel}${num(s.fiscal_pontos) !== null ? `, ${s.fiscal_pontos} ${s.fiscal_pontos === 1 ? 'ponto' : 'pontos'}` : ''}.${crit.length ? ` Motivos: ${crit.join('; ')}.` : ''}`),
    h('p', { class: 'ajuda' }, 'Régua publicada pela casa antes do 2º turno. Não temos registro do que cada fiscal conferiu na seção.'));
}
function blocoMudanca(s) {
  const m = s.mudanca;
  if (!m) return null;
  const cat = (cats().mudanca || {})[m.cat] || {};
  return h('div', { class: 'caixa' }, h('h4', {}, `Local de votação: ${cat.nome || 'alteração entre os turnos'}`),
    h('p', {}, cat.frase || ''),
    m.nome1 ? h('p', {}, `1º turno: ${caixa(m.nome1)}.`) : null,
    m.nome2 ? h('p', {}, `2º turno: ${caixa(m.nome2)}${m.end2 ? `, ${caixa(m.end2)}` : ''}${m.bairro2 ? `, ${caixa(m.bairro2)}` : ''}.`) : null,
    num(m.dist_m) !== null ? h('p', {}, `Distância em linha reta: ${distTxt(m.dist_m)}.`) : null,
    m.motivo ? h('p', {}, `Motivo informado pelo TRE: ${m.motivo}.`) : null,
    h('p', { class: 'ajuda' }, h('a', { href: 'mudancas_secoes_abstencoes.html' }, 'Laudo das seções que mudaram de endereço')));
}
// Rótulo da fonte da chuva do 2º turno: estação a X km ou modelo provisório.
function rotuloFonte2(fonte, o) {
  if (fonte === 'cemaden' || fonte === 'inmet' || fonte === 'ambos') {
    const rede = { cemaden: 'CEMADEN', inmet: 'INMET', ambos: 'INMET/CEMADEN' }[fonte];
    const n = num(o.n_estacoes);
    return `chuva medida em ${n === 1 ? 'estação' : 'estações'} ${rede} a ${f1(o.dist_km)} km`;
  }
  if (fonte === 'era5') return 'chuva observada (reanálise climática)';
  if (fonte === 'ifs_provisorio') return 'modelo, provisório';
  return SD;
}
function blocoClima(l) {
  if (!l || (!l.clima1 && !l.clima2 && !l.clima2o)) return null;
  const a = l.clima1;
  const b = l.clima2;
  const o = l.clima2o;
  const medida = o && ['cemaden', 'inmet', 'ambos'].includes(o.fonte_dia);
  return h('div', { class: 'caixa' }, h('h4', {}, 'Clima'),
    a ? h('p', {}, `1º turno, observado: ${f1(a.chuva_mm)} mm de chuva nas horas de votação (${f1(a.chuva_dia_mm)} mm no dia), rajada de até ${f0(a.rajada_kmh)} km/h.${num(a.urnas_bateria_votacao) > 0 ? ` ${f0(a.urnas_bateria_votacao)} de ${f0(a.urnas)} urnas do local usaram bateria durante a votação.` : ''}`) : null,
    o ? h('p', {}, `2º turno, no dia: ${f1(o.chuva_dia_mm)} mm em 25/10 (${rotuloFonte2(o.fonte_dia, o)}); ${f1(o.chuva_mm)} mm nas horas de votação, 7h às 18h (${rotuloFonte2(o.fonte_votacao, o)}); rajada de até ${f0(o.rajada_kmh)} km/h (modelo, provisório).`) : null,
    b ? h('p', { class: o ? 'ajuda' : null }, `2º turno, previsão publicada na véspera: ${f1(b.chuva_mm)} mm, chance de chuva de ${f0(b.prob_pct)}%, risco ${b.risco || SD}.`) : null,
    h('p', { class: 'ajuda' }, 'Reanálise climática para o 1º turno. No 2º turno, pluviômetro a até 50 km é estimativa para a célula de 0,25 grau, não medição no prédio; onde não há estação, o modelo modelo meteorológico é provisório e será trocado pela reanálise climática.' + (medida ? '' : ' Sem estação a 50 km deste local.')));
}
function tabelaPredio(uf, zd, local, atual) {
  const secs = zd.listaSecoes.filter((s) => s.li === local.li).sort((a, b) => a.secao - b.secao);
  return h('div', { class: 'tabela-rolagem', tabindex: '0', role: 'region', 'aria-label': 'Seções deste local de votação' },
    h('table', { class: 'tabela' },
      h('thead', {}, h('tr', {}, ['Seção', 'Aptos', 'Flávio 2º', 'Lula 2º', 'Variação de Flávio', 'Comparecimento 2º', 'Sinais', 'Log 1º → 2º', 'Grupo estatístico'].map((t, i) => h('th', { scope: 'col', class: i ? 'n' : '' }, t)))),
      h('tbody', {}, secs.map((s) => h('tr', { class: s.secao === atual ? 'atual' : '' },
        h('td', {}, s.secao === atual ? `${s.secao} (esta)` : h('button', { type: 'button', class: 'link', onclick: () => executar(`Abrindo a seção ${s.secao}`, () => renderSecao(uf, zd, s, {})) }, String(s.secao))),
        h('td', { class: 'n' }, f0(s.aptos2 ?? s.aptos1)),
        h('td', { class: 'n' }, s.pequena || !s.bu2 ? '' : pc(s.fatia_f2)),
        h('td', { class: 'n' }, s.pequena || !s.bu2 || num(s.fatia_f2) === null ? '' : pc(100 - s.fatia_f2)),
        h('td', { class: `n ${num(s.d_fatia_pp) > 0 ? 'mais' : num(s.d_fatia_pp) < 0 ? 'menos' : ''}` }, s.pequena || !s.bu2 ? '' : pp(s.d_fatia_pp)),
        h('td', { class: 'n' }, s.pequena || !s.bu2 ? '' : pc(s.comp_pct2)),
        h('td', { class: 'n' }, s.bu2 ? f0(s.escore) : ''),
        h('td', { class: 'n' }, s.log2_atencao === null || s.log2_atencao === undefined ? '' : `${s.log1_atencao ?? '?'} → ${s.log2_atencao}`),
        h('td', { class: 'n' }, s.ml_anomalo === null || s.ml_anomalo === undefined ? '' : s.ml_anomalo ? 'atípico' : 'comum'),
      )))));
}
function tabelaContraMun(local, mun) {
  const lin = (r, a, b) => h('tr', {}, h('th', { scope: 'row' }, r), h('td', { class: 'n' }, a), h('td', { class: 'n' }, b));
  return h('div', { class: 'tabela-rolagem', tabindex: '0', role: 'region', 'aria-label': 'Local de votação contra o município' },
    h('table', { class: 'tabela' },
      h('thead', {}, h('tr', {}, h('th', { scope: 'col' }, ''), h('th', { scope: 'col', class: 'n' }, 'Este local'), h('th', { scope: 'col', class: 'n' }, 'Município'))),
      h('tbody', {},
        lin('Seções com boletim do 2º turno', `${f0(local.n_bu2)} de ${f0(local.n_secoes)}`, `${f0(mun.n_bu2)} de ${f0(mun.n_secoes)}`),
        lin('Flávio entre os dois, 2º turno', pc(local.fatia_f2), pc(mun.fatia_f2)),
        lin('Flávio entre os dois, 1º turno (mesmas seções)', pc(local.fatia_f1_par), pc(mun.fatia_f1_par)),
        lin('Variação, em pontos', pp(local.d_fatia_pp), pp(mun.d_fatia_pp)),
        lin('Comparecimento, 2º turno', pc(local.comp_pct2), pc(mun.comp_pct2)),
        lin('Variação do comparecimento', pp(local.d_comp_pp), pp(mun.d_comp_pp)),
        lin('Brancos e nulos, 2º turno', pc(local.bn_pct2), pc(mun.bn_pct2)),
        lin('Seções com algum sinal', f0(local.secoes_sinal), f0(mun.secoes_sinal)),
        lin('Urnas trocadas entre os turnos', f0(local.urnas_trocadas), f0(mun.urnas_trocadas)),
        lin('Log subiu para atenção 2 ou 3 no 2º turno', f0(local.secoes_log_subiu), f0(mun.secoes_log_subiu)),
        lin('Urna religada durante a votação, 2º turno', f0(local.secoes_log_reinicio), f0(mun.secoes_log_reinicio)),
        lin('Seções no grupo atípico (estatística dos dois turnos)', f0(local.secoes_anomalas), f0(mun.secoes_anomalas)),
      )));
}
function cabecalhoLocal(uf, zd, local) {
  const mun = (zd.municipios || {})[local.mun_tse] || {};
  return [
    h('p', { class: 'local-nome' }, caixa(local.nome) || 'Local de votação'),
    h('p', { class: 'local-end' }, [caixa(local.endereco), caixa(local.bairro), `${mun.nome || ''} (${uf === 'ZZ' ? 'Exterior' : uf})`, cepFmt(local.cep)].filter(Boolean).join(' · ')),
  ];
}
function linksFim(uf, local) {
  const noMapa = local && local.local_id ? `politizese_mapa.html#uf=${uf}&l=${encodeURIComponent(local.local_id)}` : 'politizese_mapa.html';
  return [
    h('p', {}, h('a', { class: 'btn btn-sec', href: noMapa }, local ? 'Este prédio no mapa' : 'Ver no mapa do Brasil')),
    h('p', { class: 'ajuda' }, 'Veja também o ', h('a', { href: 'apuracao_2T_2026.html' }, 'dossiê da apuração do 2º turno'), ' e o ', h('a', { href: 'politizese_mapa.html' }, 'mapa do Brasil com todos os locais de votação'), '.'),
  ];
}

/* ------------------------------------------------------------------ relatos da seção */

const { blocoRelato } = criarRelatos({ h, f0, aviso });

/* ------------------------------------------------------------------ fichas */

function renderSecao(uf, zd, s, extra) {
  s._uf = uf;
  E.atual = { tipo: 'secao', uf, zona: zd.zona, secao: s.secao };
  const local = zd.listaLocais[s.li] || null;
  const mun = (zd.municipios || {})[s.mun_tse] || {};
  const cob = zd.cobertura || {};
  const selos = [
    s.bu2 ? h('span', { class: 'selo ok' }, '2º turno lido') : h('span', { class: 'selo alerta' }, '2º turno ainda não lido'),
    s.bu2 && num(s.escore) > 0 ? h('span', { class: 'selo alerta' }, `${s.escore} ${s.escore === 1 ? 'sinal' : 'sinais'}`) : null,
    s.bu2 && s.ml_anomalo ? h('span', { class: 'selo alerta' }, 'grupo atípico') : null,
    s.urna_situacao && !['mesma', 'mesma_recarga'].includes(s.urna_situacao) ? h('span', { class: 'selo' }, 'urna trocada') : null,
    s.mudanca ? h('span', { class: 'selo' }, 'local alterado') : null,
  ];
  const ficha = h('article', { class: 'ficha', 'aria-labelledby': 'ficha-titulo' },
    h('p', { class: 'kicker' }, `Seção ${s.secao} · Zona ${zd.zona} · ${uf === 'ZZ' ? 'Exterior' : uf}`),
    h('h2', { id: 'ficha-titulo' }, `O que aconteceu na seção ${s.secao}`),
    local ? cabecalhoLocal(uf, zd, local) : h('p', { class: 'local-end' }, mun.nome || ''),
    h('div', { class: 'selos' }, selos),
    local ? window.PolitizeTerritorio.atalho(local.local_id) : null,
    extra.agregada ? aviso(`A seção ${extra.agregada} é agregada à seção ${s.secao}: as duas votam na mesma urna, e os números abaixo são da seção principal.`, 'Seção agregada') : null,
    cob.com_bu_2t < cob.secoes ? h('p', { class: 'ajuda' }, `Nesta zona, ${f0(cob.com_bu_2t)} de ${f0(cob.secoes)} seções já têm o boletim do 2º turno lido.`) : null,
    h('p', { class: 'leitura' }, frase(s.frases)),
    h('h3', {}, 'Os dois turnos'),
    h('div', { class: 'turnos' }, blocoTurno(1, s), blocoTurno(2, s)),
    tabelaTurnos(s),
    h('h3', {}, 'Como quem votou foi identificado'),
    h('div', { class: 'turnos' }, blocoBio(1, s), blocoBio(2, s)),
    h('h3', {}, 'Urna, sinais e registros'),
    h('div', { class: 'grade2' }, blocoSinais(s), blocoMl(s), blocoUrna(s), blocoLogs(s), blocoFiscal(s), blocoMudanca(s), blocoClima(local)),
  );
  const partes = [ficha, local ? window.PolitizeTerritorio.painel(local.local_id) : null, blocoRelato(uf, zd.zona, s, local)];
  if (local) {
    partes.push(h('article', { class: 'ficha' },
      h('p', { class: 'kicker' }, 'Neste prédio'),
      h('h2', {}, `As ${f0(local.n_secoes)} seções do local`),
      h('p', { class: 'leitura' }, frase(local.frases)),
      tabelaPredio(uf, zd, local, s.secao),
      h('h3', {}, 'O local contra o município'),
      tabelaContraMun(local, mun),
      linksFim(uf, local)));
  }
  partes.push(blocoCompartilhar({ uf, zona: zd.zona, s, mun }));
  return h('div', {}, partes);
}

function renderLocal(uf, zd, local, extra = {}) {
  E.atual = { tipo: 'local', uf, zona: zd.zona, local: local.local_id };
  const mun = (zd.municipios || {})[local.mun_tse] || {};
  const partes = [h('article', { class: 'ficha', 'aria-labelledby': 'ficha-titulo' },
    h('p', { class: 'kicker' }, `Local de votação · Zona ${zd.zona} · ${uf === 'ZZ' ? 'Exterior' : uf}`),
    h('h2', { id: 'ficha-titulo' }, 'O que aconteceu neste local de votação'),
    cabecalhoLocal(uf, zd, local),
    window.PolitizeTerritorio.atalho(local.local_id),
    extra.nota ? aviso(extra.nota, 'Aproximação') : null,
    h('p', { class: 'leitura' }, frase(local.frases)),
    h('p', { class: 'ajuda' }, 'Escolha a sua seção na tabela para ver o 1º e o 2º turno dela.'),
    tabelaPredio(uf, zd, local, null),
    h('h3', {}, 'O local contra o município'),
    tabelaContraMun(local, mun),
    blocoClima(local),
    window.PolitizeTerritorio.painel(local.local_id),
    extra.aoRedor && extra.aoRedor.length ? [h('h3', {}, 'Locais perto deste'), h('ul', { class: 'ao-redor' }, extra.aoRedor.map(({ l, d }) => h('li', {},
      h('button', { type: 'button', onclick: () => executar('Abrindo o local', () => porLocal(l.local_id, { aoRedor: extra.aoRedor.filter((x) => x.l !== l) })) },
        h('span', {}, `${caixa(l.nome)}${num(l.fatia_f2) !== null ? ` · Flávio ${pc(l.fatia_f2)} entre os dois` : ''}`), h('small', {}, distTxt(d))))))] : null,
    linksFim(uf, local))];
  return h('div', {}, partes);
}

/* ------------------------------------------------------------------ compartilhar */

function linkDe(uf, zona, secao) {
  return `${URL_PUBLICA}#uf=${uf}&z=${zona}&s=${secao}`;
}
function textoCompartilhar({ uf, zona, s, mun }) {
  const lugar = `seção ${s.secao}, zona ${zona}, ${mun.nome || ''} (${uf === 'ZZ' ? 'Exterior' : uf})`;
  if (s.pequena || !s.bu2 || num(s.fatia_f2) === null) return `Veja o que aconteceu na ${lugar}, no 1º e no 2º turno: ${linkDe(uf, zona, s.secao)}`;
  const ml = s.ml_anomalo ? ' Pela estatística dos dois turnos, a seção está no grupo atípico do país: pede explicação, não prova irregularidade.' : '';
  return `Na ${lugar}, o 2º turno deu Flávio ${pc(s.fatia_f2)} e Lula ${pc(100 - s.fatia_f2)} dos válidos; no 1º turno, entre os dois, Flávio tinha ${pc(s.fatia_f1)}. Comparecimento: ${pc(s.comp_pct1)} no 1º turno, ${pc(s.comp_pct2)} no 2º.${ml} Leitura agregada por seção, TSE. ${linkDe(uf, zona, s.secao)}`;
}
async function desenharCard(cv, { uf, zona, s, mun }) {
  const W = 1080;
  cv.width = W;
  cv.height = W;
  const c = cv.getContext('2d');
  try {
    if (document.fonts && document.fonts.load) await Promise.all([document.fonts.load('900 90px Fraunces'), document.fonts.load('600 34px "IBM Plex Sans Condensed"'), document.fonts.load('500 26px "IBM Plex Mono"')]);
  } catch {
    // sem a fonte da casa, o card sai com a de reserva
  }
  const FD = 'Fraunces, Georgia, serif';
  const FS = '"IBM Plex Sans Condensed", Arial, sans-serif';
  const FM = '"IBM Plex Mono", ui-monospace, monospace';
  c.fillStyle = '#f6f4ee';
  c.fillRect(0, 0, W, W);
  c.fillStyle = '#1d2a33';
  c.fillRect(0, 0, W, 250);
  c.fillStyle = '#f0c36a';
  c.font = `500 26px ${FM}`;
  c.fillText('POLITIZE-SE · ELEIÇÕES 2026', 70, 80);
  c.fillStyle = '#ffffff';
  c.font = `900 76px ${FD}`;
  c.fillText(`Seção ${s.secao} · Zona ${zona}`, 70, 165);
  c.font = `600 34px ${FS}`;
  c.fillStyle = '#dde3e8';
  c.fillText(`${mun.nome || ''} (${uf === 'ZZ' ? 'Exterior' : uf})`.slice(0, 48), 70, 215);
  const barra = (y, rot, f, l) => {
    c.fillStyle = '#16191c';
    c.font = `500 26px ${FM}`;
    c.fillText(rot, 70, y);
    if (num(f) === null) {
      c.font = `600 34px ${FS}`;
      c.fillText('sem dado', 70, y + 56);
      return;
    }
    const x0 = 70;
    const w = W - 140;
    c.fillStyle = '#1f5f9e';
    c.fillRect(x0, y + 18, (w * f) / 100, 64);
    c.fillStyle = '#b23a2a';
    c.fillRect(x0 + (w * f) / 100, y + 18, w - (w * f) / 100, 64);
    c.fillStyle = '#ffffff';
    c.font = `700 36px ${FS}`;
    if (f >= 18) c.fillText(`Flávio ${nf1.format(f)}%`, x0 + 18, y + 63);
    const tl = `Lula ${nf1.format(l)}%`;
    if (l >= 18) c.fillText(tl, x0 + w - 18 - c.measureText(tl).width, y + 63);
  };
  const ok2 = !s.pequena && s.bu2 && num(s.fatia_f2) !== null;
  barra(330, '2º TURNO · VOTOS VÁLIDOS', ok2 ? s.fatia_f2 : null, ok2 ? 100 - s.fatia_f2 : null);
  const ok1 = !s.pequena && num(s.fatia_f1) !== null;
  barra(500, '1º TURNO · ENTRE OS DOIS', ok1 ? s.fatia_f1 : null, ok1 ? 100 - s.fatia_f1 : null);
  c.fillStyle = '#16191c';
  c.font = `500 26px ${FM}`;
  c.fillText('COMPARECIMENTO', 70, 680);
  c.font = `900 64px ${FD}`;
  c.fillText(s.pequena ? 'seção pequena' : `${pc(s.comp_pct1)} → ${pc(s.comp_pct2)}`, 70, 755);
  c.font = `600 32px ${FS}`;
  c.fillStyle = '#4f5862';
  const sin = !s.bu2 ? '2º turno ainda não lido' : num(s.escore) > 0 ? `${s.escore} ${s.escore === 1 ? 'sinal pede' : 'sinais pedem'} explicação, sem provar irregularidade` : 'Nenhum sinal da régua da casa';
  c.fillText(sin, 70, 830);
  if (s.bu2 && s.ml_anomalo) {
    // selo do grupo atípico da mistura estatística dos dois turnos
    c.font = `600 26px ${FS}`;
    c.fillStyle = '#6b4a92';
    c.fillText('Grupo atípico na estatística dos dois turnos: pede explicação, não prova nada', 70, 872);
  }
  c.fillStyle = '#1d2a33';
  c.fillRect(0, 920, W, 160);
  c.fillStyle = '#ffffff';
  c.font = `600 32px ${FS}`;
  c.fillText('brasil.arvor.co/politizese.html', 70, 985);
  c.fillStyle = '#c4ccd3';
  c.font = `500 22px ${FM}`;
  c.fillText('LEITURA AGREGADA POR SEÇÃO, TSE · O VOTO É SECRETO', 70, 1035);
}
function blocoCompartilhar(dados) {
  const cv = h('canvas', { width: '1080', height: '1080', role: 'img', 'aria-label': 'Card para compartilhar com o resultado da seção nos dois turnos' });
  const status = h('p', { class: 'ajuda', role: 'status' });
  const copiar = async (texto, ok) => {
    try {
      await navigator.clipboard.writeText(texto);
      status.textContent = ok;
    } catch {
      status.textContent = texto;
    }
  };
  const art = h('article', { class: 'ficha' },
    h('p', { class: 'kicker' }, 'Compartilhar'),
    h('h2', {}, 'Leve a sua seção'),
    h('div', { class: 'compartilhar' }, cv, h('div', {},
      h('p', {}, 'O card e o link são montados no seu aparelho, só quando você pede. O link leva direto a esta seção.'),
      h('div', { class: 'botoes' },
        h('button', { type: 'button', class: 'btn btn-prim', onclick: () => { const a = h('a', { href: cv.toDataURL('image/png'), download: `politizese-${dados.uf}-${dados.zona}-${dados.s.secao}.png` }); document.body.append(a); a.click(); a.remove(); } }, 'Baixar imagem'),
        h('button', { type: 'button', class: 'btn btn-sec', onclick: () => copiar(textoCompartilhar(dados), 'Texto copiado.') }, 'Copiar texto'),
        h('button', { type: 'button', class: 'btn btn-sec', onclick: () => copiar(linkDe(dados.uf, dados.zona, dados.s.secao), 'Link copiado.') }, 'Copiar link')),
      status)));
  desenharCard(cv, dados);
  return art;
}

/* ------------------------------------------------------------------ página fixa */

function renderTopo() {
  const ind = E.indice;
  const cob = ind.cobertura || {};
  const n = cob.nacional || {};
  const nLocais = E.muns.reduce((s, m) => s + (m.n_locais || 0), 0);
  $('#numeros').replaceChildren(
    ...[[f0(n.secoes), 'seções no país e no exterior'], [f0(n.com_bu_2t), 'seções com boletim do 2º turno lido'], [f0(nLocais), 'locais de votação'], [f0(E.muns.length), 'municípios e cidades no exterior']]
      .map(([v, r]) => h('div', {}, h('dt', {}, r), h('dd', {}, v))));
  const falta = Object.entries(cob.ufs || {}).filter(([, c]) => c.com_bu_2t < c.secoes).map(([u, c]) => (c.com_bu_2t === 0 ? u : `${u} (${f1(c.pct)}%)`));
  $('#cobertura').textContent = n.coleta_completa && !falta.length
    ? `Todos os boletins do 2º turno foram lidos. Versão de ${new Date(ind.gerado_em).toLocaleString('pt-BR')}.`
    : `Leitura dos boletins do 2º turno em andamento: ${f1(n.pct)}% das seções. Ainda falta, total ou em parte: ${falta.join(', ')}. Os números do 1º turno valem para todas. Versão de ${new Date(ind.gerado_em).toLocaleString('pt-BR')}.`;
  const corpo = $('#fontes-corpo');
  corpo.replaceChildren(...(ind.fontes || []).map((f) => h('tr', {}, h('td', {}, f.chave), h('td', {}, f.caminho), h('td', { class: 'n' }, num(f.bytes) === null ? '' : `${nf1.format(f.bytes / 1e6)} MB`), h('td', { class: 'hash' }, f.sha256 || f.nota || ''))));
  $('#gerado-em').textContent = `Dados gerados em ${new Date(ind.gerado_em).toLocaleString('pt-BR')} por scripts/politize-se-build.py.`;
}

/* ------------------------------------------------------------------ formulários */

function configurarAbas() {
  const abas = [...document.querySelectorAll('[role="tab"]')];
  const ativar = (a, foco = true) => {
    for (const b of abas) {
      const sel = b === a;
      b.setAttribute('aria-selected', String(sel));
      b.tabIndex = sel ? 0 : -1;
      $(`#${b.getAttribute('aria-controls')}`).hidden = !sel;
    }
    if (foco) a.focus();
  };
  abas.forEach((a, i) => {
    a.addEventListener('click', () => ativar(a, false));
    a.addEventListener('keydown', (ev) => {
      const d = { ArrowRight: 1, ArrowLeft: -1 }[ev.key];
      if (d) {
        ev.preventDefault();
        ativar(abas[(i + d + abas.length) % abas.length]);
      }
    });
  });
}
function configurarSecao() {
  const uf = $('#s-uf');
  const zona = $('#s-zona');
  const sec = $('#s-secao');
  for (const inp of [zona, sec]) inp.addEventListener('input', () => { inp.value = inp.value.replace(/\D/g, '').slice(0, 4); });
  $('#form-secao').addEventListener('submit', (ev) => {
    ev.preventDefault();
    const u = uf.value;
    const z = Number(zona.value);
    const s = Number(sec.value);
    for (const c of [uf, zona, sec]) c.removeAttribute('aria-invalid');
    const falta = [[!u, uf, 'o estado'], [!z, zona, 'a zona'], [!s, sec, 'a seção']].filter(([f]) => f);
    if (falta.length) {
      falta.forEach(([, c]) => c.setAttribute('aria-invalid', 'true'));
      estadoErro(`Preencha ${falta.map((x) => x[2]).join(', ')}. Os três números estão no título de eleitor e no e-Título.`, null);
      falta[0][1].focus();
      return;
    }
    executar(`Procurando a seção ${s} da zona ${z}`, () => porSecao(u, z, s));
  });
}
function configurarCep() {
  const inp = $('#cep');
  inp.addEventListener('input', () => {
    const d = inp.value.replace(/\D/g, '').slice(0, 8);
    inp.value = d.length > 5 ? `${d.slice(0, 5)}-${d.slice(5)}` : d;
  });
  $('#form-cep').addEventListener('submit', (ev) => {
    ev.preventDefault();
    const d = inp.value.replace(/\D/g, '');
    if (d.length !== 8) {
      inp.setAttribute('aria-invalid', 'true');
      estadoErro('O CEP tem 8 dígitos, no formato 00000-000.', null);
      return;
    }
    inp.removeAttribute('aria-invalid');
    executar('Procurando locais de votação com esse CEP', () => porCep(d));
  });
}
function configurarCidade() {
  const inp = $('#cidade');
  const lista = $('#cidade-lista');
  const sel = $('#bairro');
  const btn = $('#btn-cidade');
  let res = [];
  let ativo = -1;
  const ufs = new Set(Object.keys(NOME_UF).map((u) => u.toLowerCase()));
  const fechar = () => {
    lista.hidden = true;
    inp.setAttribute('aria-expanded', 'false');
    inp.removeAttribute('aria-activedescendant');
    ativo = -1;
  };
  const pintar = () => {
    [...lista.children].forEach((li, i) => li.setAttribute('aria-selected', String(i === ativo)));
    if (ativo >= 0 && lista.children[ativo]) inp.setAttribute('aria-activedescendant', lista.children[ativo].id);
  };
  const buscar = () => {
    let q = norm(inp.value);
    E.cidade = null;
    sel.disabled = true;
    btn.disabled = true;
    sel.replaceChildren(h('option', { value: '' }, 'Escolha a cidade primeiro'));
    if (q.length < 2) return fechar();
    let uf = null;
    const p = q.split(' ');
    if (p.length > 1 && ufs.has(p[p.length - 1])) {
      uf = p.pop().toUpperCase();
      q = p.join(' ');
    }
    const pont = [];
    for (const m of E.muns) {
      if (uf && m.uf !== uf) continue;
      const b2 = norm(m.nome_tse || '');
      let s = -1;
      if (m.busca.startsWith(q) || b2.startsWith(q)) s = 0;
      else if (m.busca.includes(` ${q}`)) s = 1;
      else if (q.length >= 3 && m.busca.includes(q)) s = 2;
      if (s >= 0) pont.push([s, m]);
    }
    pont.sort((a, b) => a[0] - b[0] || (b[1].aptos || 0) - (a[1].aptos || 0));
    res = pont.slice(0, 8).map((x) => x[1]);
    ativo = res.length ? 0 : -1;
    lista.replaceChildren(...(res.length
      ? res.map((m, i) => h('li', { id: `cid-${i}`, role: 'option', 'aria-selected': String(i === ativo), onmousedown: (ev) => { ev.preventDefault(); escolher(m); } }, h('span', {}, m.nome), h('span', { class: 'uf' }, m.uf === 'ZZ' ? 'EXT' : m.uf)))
      : [h('li', { role: 'option', 'aria-disabled': 'true', 'aria-selected': 'false', id: 'cid-vazio' }, 'Nenhuma cidade com esse nome')]));
    lista.hidden = false;
    inp.setAttribute('aria-expanded', 'true');
    pintar();
  };
  async function escolher(m) {
    fechar();
    inp.value = `${m.nome} (${m.uf === 'ZZ' ? 'Exterior' : m.uf})`;
    E.cidade = m;
    sel.replaceChildren(h('option', { value: '' }, 'Carregando bairros...'));
    try {
      const { locais } = await carregarMun(m);
      if (E.cidade !== m) return;
      const cont = new Map();
      for (const l of locais) cont.set(l.bairro || '', (cont.get(l.bairro || '') || 0) + 1);
      const bairros = [...cont.entries()].filter(([b]) => b).sort((a, b) => caixa(a[0]).localeCompare(caixa(b[0]), 'pt-BR'));
      sel.replaceChildren(h('option', { value: '' }, `Sem bairro: o local mais perto do centro (${f0(locais.length)} ${locais.length === 1 ? 'local' : 'locais'})`),
        ...bairros.map(([b, n]) => h('option', { value: b }, `${caixa(b)} (${n} ${n === 1 ? 'local' : 'locais'})`)));
      sel.disabled = false;
      btn.disabled = false;
    } catch (e) {
      estadoErro(msgErro(e), () => escolher(m));
    }
  }
  inp.addEventListener('input', buscar);
  inp.addEventListener('blur', () => setTimeout(fechar, 120));
  inp.addEventListener('keydown', (ev) => {
    const aberto = !lista.hidden;
    if (ev.key === 'ArrowDown') {
      ev.preventDefault();
      if (!aberto) buscar();
      else if (res.length) ativo = (ativo + 1) % res.length;
      pintar();
    } else if (ev.key === 'ArrowUp') {
      ev.preventDefault();
      if (res.length) ativo = (ativo - 1 + res.length) % res.length;
      pintar();
    } else if (ev.key === 'Enter') {
      if (aberto && res[ativo]) {
        ev.preventDefault();
        escolher(res[ativo]);
      } else if (!E.cidade) ev.preventDefault();
    } else if (ev.key === 'Escape' && aberto) {
      ev.preventDefault();
      fechar();
    }
  });
  $('#form-cidade').addEventListener('submit', (ev) => {
    ev.preventDefault();
    if (!E.cidade) return inp.focus();
    const m = E.cidade;
    const b = sel.value;
    executar(`Abrindo ${b ? caixa(b) : m.nome}`, () => porCidade(m, b));
  });
}
function configurarGeo() {
  $('#btn-geo').addEventListener('click', () => {
    if (!('geolocation' in navigator)) return estadoErro('Este navegador não oferece localização. Use a seção, o CEP ou a cidade.', null);
    estadoCarregando('Pedindo a localização ao aparelho');
    const meu = ++E.pedido;
    navigator.geolocation.getCurrentPosition(
      (pos) => { if (meu === E.pedido) executar('Procurando os locais de votação perto de você', () => porPosicao(pos)); },
      (err) => {
        if (meu !== E.pedido) return;
        const m = { 1: 'O navegador não liberou a localização. Use a seção, o CEP ou a cidade.', 2: 'O aparelho não achou a localização agora.', 3: 'A localização demorou demais.' };
        estadoErro(m[err.code] || 'Não foi possível obter a localização.', null);
      },
      { enableHighAccuracy: false, timeout: 15000, maximumAge: 300000 },
    );
  });
}
function configurarLimpar() {
  document.querySelectorAll('[data-limpar]').forEach((b) => b.addEventListener('click', () => {
    E.pedido += 1;
    E.cidade = null;
    for (const id of ['#s-zona', '#s-secao', '#cep', '#cidade']) $(id).value = '';
    $('#s-uf').value = '';
    $('#bairro').replaceChildren(h('option', { value: '' }, 'Escolha a cidade primeiro'));
    $('#bairro').disabled = true;
    $('#btn-cidade').disabled = true;
    alvo().replaceChildren();
  }));
}
// Link compartilhado: #uf=SP&z=1&s=123 ou #uf=SP&z=1&l=<local_id>. Lido só ao abrir a página;
// a página nunca escreve a seção no endereço.
function abrirHash() {
  const p = new URLSearchParams(location.hash.replace(/^#/, ''));
  const uf = (p.get('uf') || '').toUpperCase();
  const z = Number(p.get('z'));
  const s = Number(p.get('s'));
  const l = p.get('l');
  if (!NOME_UF[uf] || !z) return;
  if (s) {
    $('#s-uf').value = uf;
    $('#s-zona').value = String(z);
    $('#s-secao').value = String(s);
    executar(`Abrindo a seção ${s} da zona ${z}`, () => porSecao(uf, z, s));
  } else if (l && /^[A-Z]{2}-\d+-\d+-[\w-]+$/.test(l)) {
    executar('Abrindo o local de votação', () => porLocal(l));
  }
}

async function iniciar() {
  if (location.protocol === 'file:') return;
  configurarAbas();
  configurarSecao();
  configurarCep();
  configurarCidade();
  configurarGeo();
  configurarLimpar();
  try {
    prepararIndice(await buscarJSON(`${BASE}indice.json`));
  } catch (e) {
    $('#avisos').replaceChildren(aviso(msgErro(e), 'Dados indisponíveis', true));
    return;
  }
  for (const o of [...$('#s-uf').options]) if (o.value && !Array.isArray(E.indice.zonas[o.value])) o.remove();
  renderTopo();
  abrirHash();
  window.addEventListener('hashchange', abrirHash);
}
iniciar();
