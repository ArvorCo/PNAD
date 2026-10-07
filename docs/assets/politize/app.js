// Politize sua vizinhança: aplicativo estático, escrito à mão, sem framework e sem build.
// Lê os JSON gerados por scripts/politize-build.py (contrato em analysis/politize/CONTRATO.md)
// e os textos de docs/assets/politize/textos.json. Não calcula métrica eleitoral: só lê, ordena
// por distância e formata. Nada sai do aparelho: não há rastreador nem requisição a terceiros.

import { carta, losango, CORES } from './carta.js';
import { desenharCard } from './card.js';
import { montarMapa } from './mapa.js';

/* ------------------------------------------------------------------ configuração */

const HOST = location.hostname;
const DEV = ['localhost', '127.0.0.1', '[::1]', '::1'].includes(HOST) || HOST.endsWith('.localhost') || HOST.endsWith('.test');
const QS = new URLSearchParams(location.search);

// `?dados=` e `?textos=` só valem em desenvolvimento e só para caminho relativo do próprio site.
function caminhoDev(nome, pasta) {
  const v = QS.get(nome);
  if (!DEV || !v) return null;
  if (!/^[\w./-]+$/.test(v) || v.startsWith('/') || v.includes('//') || /^[a-z]+:/i.test(v)) return null;
  return pasta && !v.endsWith('/') ? `${v}/` : v;
}

const BASE_PADRAO = 'assets/politize/dados/';
const BASE = caminhoDev('dados', true) || BASE_PADRAO;
const TEXTOS_URLS = [caminhoDev('textos', false), 'assets/politize/textos.json', BASE !== BASE_PADRAO ? `${BASE}textos.json` : null].filter(Boolean);
const URL_PUBLICA = 'brasil.arvor.co/politizesuavizinhanca.html';
const RAIO_VIZINHOS_M = 15000;
const N_AO_REDOR = 7;

const ORDEM_ARQ = ['fortaleza', 'muro', 'pendulo', 'reencontro', 'fertil', 'dormindo', 'abaixo_do_perfil', 'frente', 'atras'];
const NOME_ARQ = {
  fortaleza: 'Fortaleza', muro: 'Muro', pendulo: 'Pêndulo', reencontro: 'Reencontro', fertil: 'Terreno fértil',
  dormindo: 'Dormindo', abaixo_do_perfil: 'Abaixo do perfil', frente: 'Na frente', atras: 'Atrás',
};
const COR_PADRAO = {
  fortaleza: 'verde', frente: 'verde', muro: 'azul', atras: 'azul', pendulo: 'amarelo', reencontro: 'amarelo',
  fertil: 'amarelo', dormindo: 'amarelo', abaixo_do_perfil: 'amarelo',
};
const PALETA = {
  verde: { fill: '#0b7a3b', txt: '#0a6e35', tinta: '#ffffff' },
  amarelo: { fill: '#f2c230', txt: '#7d5b00', tinta: '#151812' },
  azul: { fill: '#1f5f9e', txt: '#1a5189', tinta: '#ffffff' },
};
const NOME_UF = {
  AC: 'Acre', AL: 'Alagoas', AP: 'Amapá', AM: 'Amazonas', BA: 'Bahia', CE: 'Ceará', DF: 'Distrito Federal',
  ES: 'Espírito Santo', GO: 'Goiás', MA: 'Maranhão', MT: 'Mato Grosso', MS: 'Mato Grosso do Sul', MG: 'Minas Gerais',
  PA: 'Pará', PB: 'Paraíba', PR: 'Paraná', PE: 'Pernambuco', PI: 'Piauí', RJ: 'Rio de Janeiro',
  RN: 'Rio Grande do Norte', RS: 'Rio Grande do Sul', RO: 'Rondônia', RR: 'Roraima', SC: 'Santa Catarina',
  SP: 'São Paulo', SE: 'Sergipe', TO: 'Tocantins', ZZ: 'Exterior',
};
// Preposição com artigo de cada estado ("do Acre", "da Bahia", "de São Paulo").
const ART_UF = {
  AC: 'o', AP: 'o', AM: 'o', BA: 'a', CE: 'o', DF: 'o', ES: 'o', MA: 'o', PA: 'o', PB: 'a', PR: 'o', PI: 'o',
  RJ: 'o', RN: 'o', RS: 'o', TO: 'o',
};
const deUF = (u) => (u === 'ZZ' ? 'do exterior' : `${{ o: 'do', a: 'da' }[ART_UF[u]] || 'de'} ${NOME_UF[u] || u}`);
const emUF = (u) => (u === 'ZZ' ? 'no exterior' : `${{ o: 'no', a: 'na' }[ART_UF[u]] || 'em'} ${NOME_UF[u] || u}`);

const ROTULO_PERFIL = {
  escolaridade: { fund_inc: 'Fundamental incompleto', fund_med: 'Fundamental completo', med_sup_inc: 'Médio completo', superior: 'Superior completo' },
  idade: { a16_24: '16 a 24 anos', a25_34: '25 a 34 anos', a35_44: '35 a 44 anos', a45_59: '45 a 59 anos', a60: '60 anos ou mais' },
  renda: { ate2: 'Até 2 salários mínimos', de2a5: 'De 2 a 5 salários mínimos', mais5: 'Mais de 5 salários mínimos' },
};
const SETOR_TIPO = {
  favela: 'Favela ou comunidade urbana (IBGE)', aldeia: 'Aldeia indígena (IBGE)', quilombo: 'Território quilombola (IBGE)',
  prisao: 'Unidade prisional', militar: 'Área militar',
};
const IGNORAR_PROBLEMA = new Set(['NS/NR', 'Nenhum', 'Outros', 'Não sabe', 'Não respondeu']);

/* ------------------------------------------------------------------ estado */

const E = {
  textos: {},
  indice: null,
  muns: [],
  porChave: new Map(),
  cache: new Map(),
  locaisMun: new Map(),
  atual: null,
  pedido: 0,
  cidade: null,
};

/* ------------------------------------------------------------------ utilidades */

const $ = (s, r = document) => r.querySelector(s);

function h(tag, attrs = {}, ...filhos) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === 'class') n.className = v;
    else if (k === 'text') n.textContent = v;
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
const brl = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 });
const f1 = (v) => (num(v) === null ? 'sem dado' : nf1.format(v));
const f0 = (v) => (num(v) === null ? 'sem dado' : nf0.format(Math.round(v)));
const SD = 'sem dado';

function distTxt(m) {
  if (num(m) === null) return '';
  if (m < 950) return `${nf0.format(Math.max(50, Math.round(m / 50) * 50))} m`;
  return `${nf1.format(m / 1000)} km`;
}

function haversine(a, b) {
  if (!a || !b || num(a.lat) === null || num(b.lat) === null || num(a.lon) === null || num(b.lon) === null) return null;
  const R = 6371008.8;
  const r = Math.PI / 180;
  const dLat = (b.lat - a.lat) * r;
  const dLon = (b.lon - a.lon) * r;
  const s = Math.sin(dLat / 2) ** 2 + Math.cos(a.lat * r) * Math.cos(b.lat * r) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.min(1, Math.sqrt(s)));
}

const SIGLAS = new Set(['IBGE', 'IFAC', 'UFAC', 'SESC', 'SESI', 'SENAI', 'SENAC', 'CEU', 'EMEF', 'EMEI', 'EE', 'EEF', 'EEEFM', 'EMEB',
  'CIEP', 'CAIC', 'CEFET', 'USP', 'UNB', 'UFRJ', 'UFMG', 'ETEC', 'FATEC', 'UPA', 'APAE', 'CEI', 'CMEI', 'CE', 'CEM', 'EM', 'II',
  'III', 'IV', 'VI', 'VII', 'VIII', 'IX', 'XI', 'XII', 'CAIC', 'COHAB', 'CDHU', 'BNH', 'IEPTEC', 'IFSP', 'IFMG', 'UEPA', 'CRAS', 'CRE']);
const MINUSC = new Set(['de', 'da', 'do', 'das', 'dos', 'e', 'em', 'na', 'no', 'nas', 'nos', 'a', 'o', 'as', 'os', 'para', 'com', 'por']);

// O cadastro do TSE vem em CAIXA ALTA. Só converte quando o texto inteiro está em maiúsculas.
function caixa(s) {
  const t = String(s || '').replace(/\s+/g, ' ').trim();
  if (!t || t !== t.toUpperCase()) return t;
  return t
    .split(' ')
    .map((w, i) => {
      const limpa = w.replace(/[^\p{L}\p{N}]/gu, '');
      if (SIGLAS.has(limpa) || /\d/.test(w) || (limpa.length >= 2 && !/[AEIOUÁÉÍÓÚÂÊÔÃÕÀ]/u.test(limpa))) return w;
      const lw = w.toLocaleLowerCase('pt-BR');
      if (i > 0 && MINUSC.has(lw)) return lw;
      return lw.replace(/(^|[-'(/])(\p{L})/gu, (m, p, c) => p + c.toLocaleUpperCase('pt-BR'));
    })
    .join(' ');
}

function cepFmt(c) {
  const d = String(c || '').replace(/\D/g, '');
  if (d.length !== 8 || /^0+$/.test(d)) return '';
  return `${d.slice(0, 5)}-${d.slice(5)}`;
}

/* ------------------------------------------------------------------ textos */

function tx(caminho, reserva = '') {
  let o = E.textos;
  for (const k of caminho.split('.')) {
    if (!o || typeof o !== 'object') return reserva;
    o = o[k];
  }
  return typeof o === 'string' && o.trim() ? o : reserva;
}
function txa(caminho) {
  let o = E.textos;
  for (const k of caminho.split('.')) {
    if (!o || typeof o !== 'object') return [];
    o = o[k];
  }
  return Array.isArray(o) ? o.filter((x) => typeof x === 'string' && x.trim()) : [];
}
function txo(o, k) {
  return o && typeof o === 'object' && o[k] && typeof o[k] === 'object' ? o[k] : {};
}
const str = (v, reserva = '') => (typeof v === 'string' && v.trim() ? v : reserva);

// Interpola {chave}; aplica plural `{n} palavra|palavras`; frase com chave sem valor sai inteira.
function interp(modelo, vars) {
  if (!modelo) return '';
  let s = String(modelo).replace(/\{(\w+)\}(\s+)([^\s|{}.,;:!?()]+)\|([^\s|{}.,;:!?()]+)/gu, (m, k, sp, sg, pl) => {
    const v = vars[k];
    if (!v || v.txt === null || v.txt === undefined || v.txt === '') return m;
    return `${v.txt}${sp}${v.n === 1 ? sg : pl}`;
  });
  s = s.replace(/\{(\w+)\}/g, (m, k) => {
    const v = vars[k];
    return v && v.txt !== null && v.txt !== undefined && v.txt !== '' ? v.txt : m;
  });
  if (!/\{\w+\}/.test(s)) return s;
  const frases = s.split(/(?<=[.!?])\s+(?=[\p{Lu}\d{])/u);
  return frases.filter((f) => !/\{\w+\}/.test(f)).join(' ').trim();
}

// `em_aberto`, `bna` e `viravel` vêm do motor (contrato, bloco "Votos em aberto e local virável").
// em aberto = outros nomes + branco + nulo + abstenção; bna = branco + nulo + abstenção;
// virável = só branco, nulo e abstenção (bna) já bastam para quem está atrás passar.
// Linha sem a coluna `bna` vem de um build anterior à regra nova: o app refaz `bna` e `viravel` no cliente.
function emAberto(l) {
  if (num(l.em_aberto) !== null) return l.em_aberto;
  const p = ['terceira', 'brancos', 'nulos', 'aptos', 'comparecimento'].map((k) => num(l[k]));
  if (p.some((x) => x === null)) return null;
  return p[0] + p[1] + p[2] + p[3] - p[4];
}
function bnaDo(l) {
  if (num(l.bna) !== null) return l.bna;
  const p = ['brancos', 'nulos', 'aptos', 'comparecimento'].map((k) => num(l[k]));
  if (p.some((x) => x === null)) return null;
  return p[0] + p[1] + p[2] - p[3];
}
function viravelDo(l) {
  if (Object.prototype.hasOwnProperty.call(l, 'bna') && Object.prototype.hasOwnProperty.call(l, 'viravel')) return l.viravel || null;
  const bna = bnaDo(l);
  const f = num(l.flavio);
  const lu = num(l.lula);
  if (bna === null || f === null || lu === null) return null;
  if (lu > f && bna >= lu - f) return 'flavio';
  if (f > lu && bna >= f - lu) return 'lula';
  return null;
}

// Texto editorial com placeholders opcionais: interpola com o que houver; o que não fechar sai.
const it = (t, vars) => (str(t) ? interp(t, vars || {}) : '');

function corArq(cod) {
  const a = txo(E.textos.arquetipos, cod);
  const nome = str(a.cor, COR_PADRAO[cod] || 'verde');
  return PALETA[nome] || PALETA.verde;
}
function arqInfo(cod) {
  const a = txo(E.textos.arquetipos, cod);
  return {
    cod,
    nome: str(a.nome, NOME_ARQ[cod] || ''),
    signo: str(a.signo),
    lema: str(a.lema),
    leitura: str(a.leitura),
    fazer: Array.isArray(a.o_que_fazer) ? a.o_que_fazer.filter((x) => str(x)) : [],
    naoFazer: Array.isArray(a.o_que_nao_fazer) ? a.o_que_nao_fazer.filter((x) => str(x)) : [],
    cor: corArq(cod),
  };
}

/* ------------------------------------------------------------------ dados */

class ErroDados extends Error {
  constructor(msg, status, url) {
    super(msg);
    this.status = status;
    this.url = url;
  }
}

function buscarJSON(url) {
  if (E.cache.has(url)) return E.cache.get(url);
  const p = fetch(url, { credentials: 'same-origin' })
    .then((r) => {
      if (!r.ok) throw new ErroDados(`HTTP ${r.status}`, r.status, url);
      return r.json();
    })
    .catch((e) => {
      E.cache.delete(url);
      if (e instanceof ErroDados) throw e;
      throw new ErroDados(e.message || 'falha de rede', 0, url);
    });
  E.cache.set(url, p);
  return p;
}

function tabela(t) {
  if (!t || !Array.isArray(t.colunas) || !Array.isArray(t.linhas)) return [];
  const cols = t.colunas;
  return t.linhas.map((l) => {
    const o = {};
    for (let i = 0; i < cols.length; i += 1) o[cols[i]] = l[i] === undefined ? null : l[i];
    return o;
  });
}

const chaveMun = (uf, mun) => `${uf}|${Number.isFinite(Number(mun)) ? Number(mun) : String(mun)}`;

function prepararIndice(ind) {
  E.indice = ind;
  E.muns = tabela(ind.municipios).map((m) => ({
    ...m,
    nome: str(m.nome, String(m.mun_tse)),
    chave: chaveMun(m.uf, m.mun_tse),
    busca: norm(m.nome),
    arquivo: str(m.arquivo, `mun/${m.uf}/${m.mun_tse}.json`),
  }));
  for (const m of E.muns) E.porChave.set(m.chave, m);
}

async function carregarMun(m) {
  if (E.locaisMun.has(m.chave)) return E.locaisMun.get(m.chave);
  const d = await buscarJSON(BASE + m.arquivo);
  const pf = str(d.perfil_fonte);
  const locais = tabela(d.locais).map((l) => ({
    ...l,
    _uf: d.uf || m.uf,
    _mun: str(d.nome, m.nome),
    _munChave: m.chave,
    _ibge: String(d.ibge || m.ibge || ''),
    _perfilFonte: str(l.perfil_fonte, pf),
  }));
  const pacote = { mun: m, dados: d, locais };
  E.locaisMun.set(m.chave, pacote);
  return pacote;
}

// Município principal + vizinhos cujo centroide fica a até 15 km do ponto.
async function carregarEntorno(principais, ponto) {
  const alvo = new Map(principais.map((m) => [m.chave, m]));
  // Exterior: cada cidade de consulado é um arquivo com poucos locais; "ao redor" usa as sete cidades
  // mais próximas, sem limite de raio. No Brasil, vizinhos com centroide a até 15 km.
  const exterior = principais.length > 0 && principais.every((m) => m.uf === 'ZZ');
  if (ponto) {
    const viz = E.muns
      .filter((m) => !alvo.has(m.chave) && num(m.lat) !== null && (!exterior || m.uf === 'ZZ'))
      .map((m) => [m, haversine(ponto, m)])
      .filter(([, d]) => d !== null && (exterior || d <= RAIO_VIZINHOS_M))
      .sort((a, b) => a[1] - b[1])
      .slice(0, exterior ? N_AO_REDOR : 6);
    for (const [m] of viz) alvo.set(m.chave, m);
  }
  const res = await Promise.allSettled([...alvo.values()].map(carregarMun));
  const pool = [];
  res.forEach((r, i) => {
    const m = [...alvo.values()][i];
    if (r.status === 'fulfilled') pool.push(...r.value.locais);
    else if (principais.some((p) => p.chave === m.chave)) throw r.reason;
  });
  return pool;
}

function centroide(locais) {
  const c = locais.filter((l) => num(l.lat) !== null && num(l.lon) !== null);
  if (!c.length) return null;
  return { lat: c.reduce((s, l) => s + l.lat, 0) / c.length, lon: c.reduce((s, l) => s + l.lon, 0) / c.length };
}

function ordenar(locais, ref) {
  const com = locais.map((l) => ({ l, d: ref ? haversine(ref, l) : null }));
  com.sort((a, b) => {
    if (a.d === null && b.d === null) return (b.l.aptos || 0) - (a.l.aptos || 0);
    if (a.d === null) return 1;
    if (b.d === null) return -1;
    return a.d - b.d;
  });
  return com;
}

/* ------------------------------------------------------------------ avisos e estados */

function aviso(texto, titulo = 'Aviso', erro = false) {
  $('#avisos').append(h('div', { class: `aviso${erro ? ' erro' : ''}` }, h('strong', {}, titulo), texto));
}

function alvoResultado() {
  return $('#resultado-in');
}

function estadoCarregando(msg) {
  const r = alvoResultado();
  $('#resultado').setAttribute('aria-busy', 'true');
  r.replaceChildren(
    h('div', { class: 'carregando' }, h('div', { class: 'disco', 'aria-hidden': 'true' }), h('p', {}, msg || 'Lendo os arquivos da vizinhança'),
      h('div', { class: 'barra', 'aria-hidden': 'true' }), h('div', { class: 'barra', 'aria-hidden': 'true' })),
  );
}

function estadoErro(msg, tentar) {
  const r = alvoResultado();
  $('#resultado').setAttribute('aria-busy', 'false');
  r.replaceChildren(
    h('div', { class: 'aviso erro', role: 'alert' }, h('strong', {}, 'Não deu certo'), h('p', { style: 'margin:0' }, msg),
      tentar ? h('p', { style: 'margin:10px 0 0' }, h('button', { type: 'button', class: 'btn btn-sec', onclick: tentar }, 'Tentar de novo')) : null),
  );
}

function msgErro(e, contexto) {
  if (e && e.status === 404) return `${contexto}: o arquivo de dados não foi encontrado. Os dados podem estar sendo atualizados; tente daqui a pouco.`;
  if (e && e.status) return `${contexto}: o servidor respondeu com erro ${e.status}. Tente de novo em instantes.`;
  return `${contexto}: não conseguimos baixar os dados. Confira a conexão com a internet e tente de novo.`;
}

function estadoVazio() {
  $('#resultado').setAttribute('aria-busy', 'false');
  const itens = ORDEM_ARQ.map((cod) => {
    const a = arqInfo(cod);
    return h('li', {}, losango('', a.cor.fill, 40), a.signo ? h('span', { class: 'signo' }, `Signo: ${a.signo}`) : null, h('b', {}, a.nome), a.lema ? h('p', {}, a.lema) : null);
  });
  alvoResultado().replaceChildren(
    h('div', { class: 'vazio-intro entra' },
      h('p', { class: 'kicker' }, 'Antes de buscar'),
      h('h2', {}, 'Cada local de votação tem um signo'),
      h('p', {}, 'O boletim lê o 1º turno do seu local de votação e o classifica pela primeira regra que bate, nesta ordem. Busque acima para ver o seu.')),
    h('ol', { class: 'zodiaco entra', 'aria-label': 'Os nove arquétipos, na ordem das regras' }, itens),
  );
}

/* ------------------------------------------------------------------ página fixa */

function preencherLista(sel, itens) {
  const ul = $(sel);
  if (!ul) return;
  ul.replaceChildren(...itens.map((t) => h('li', {}, t)));
}

function renderPagina() {
  const p = (k) => tx(`pagina.${k}`);
  if (p('hero_titulo')) $('#hero-titulo').textContent = p('hero_titulo');
  $('#hero-em').textContent = p('hero_em');
  $('#hero-deck').textContent = p('hero_deck');

  preencherLista('#passos', txa('pagina.como_funciona'));
  preencherLista('#lista-metodo', txa('pagina.metodo'));
  preencherLista('#lista-limites', txa('pagina.limites'));
  preencherLista('#lista-privacidade', txa('pagina.privacidade'));
  preencherLista('#lista-tse', txa('pagina.regras_tse'));
  preencherLista('#lista-fontes-texto', txa('pagina.fontes'));
  for (const id of ['#como-funciona', '#privacidade']) {
    const s = $(id);
    if (s && !s.querySelector('li')) s.hidden = true;
  }
}

function renderIndiceFixo() {
  const ind = E.indice;
  const nac = ind.nacional || {};
  const nLocais = num(nac.n_locais) ?? E.muns.reduce((s, m) => s + (num(m.n_locais) || 0), 0);
  const aptos = num(nac.aptos) ?? E.muns.reduce((s, m) => s + (num(m.aptos) || 0), 0);
  const stats = [
    [num(nac.locais_com_boletim) ?? nLocais, 'locais de votação'],
    [aptos, 'eleitores aptos'],
    [E.muns.length, E.muns.length === 1 ? 'município' : 'municípios'],
  ].filter(([v]) => num(v) !== null && v > 0);
  const esc = Array.isArray(ind.escopo) ? ind.escopo.filter((u) => u !== 'ZZ') : null;
  const onde = esc && esc.length && esc.length < 27 ? `${esc.map(emUF).join(', ')} (estados já processados)` : 'no Brasil';
  const man = [];
  if (num(nac.locais_viraveis_flavio) !== null) {
    man.push(h('div', { class: 'm1' }, h('b', {}, f0(nac.locais_viraveis_flavio)),
      h('span', {}, `locais de votação ${onde} onde só os brancos, nulos e abstenções já virariam para Flávio${num(nac.aptos_locais_viraveis_flavio) !== null ? ` (${f0(nac.aptos_locais_viraveis_flavio)} eleitores aptos)` : ''}.`)));
  }
  if (num(nac.votos_em_aberto) !== null) {
    man.push(h('div', { class: 'm2' }, h('b', {}, f0(nac.votos_em_aberto)),
      h('span', {}, `votos em aberto no 1º turno ${onde} (outros nomes, brancos, nulos e quem não foi).`)));
  }
  $('#hero-manchete').replaceChildren(...man);
  const ea = nac.em_aberto || {};
  const linhasEA = [
    ['Outros nomes', ea.terceira], ['Brancos', ea.brancos], ['Nulos', ea.nulos], ['Abstenção', ea.abstencao],
    ['Total em aberto', nac.votos_em_aberto],
    ['Locais em que só branco, nulo e abstenção virariam para Flávio', nac.locais_viraveis_flavio],
    ['Locais em que só branco, nulo e abstenção virariam para Lula', nac.locais_viraveis_lula],
    ['Eleitores aptos nesses locais viráveis para Flávio', nac.aptos_locais_viraveis_flavio],
    ['Eleitores aptos nesses locais viráveis para Lula', nac.aptos_locais_viraveis_lula],
    ['Locais de votação com boletim', nac.locais_com_boletim],
    ['Seções com boletim', nac.secoes_com_boletim],
  ].filter(([, v]) => num(v) !== null);
  if (linhasEA.length) {
    $('#em-aberto').replaceChildren(
      h('p', { class: 'kicker' }, 'O que o 1º turno deixou em aberto, nos dois sentidos'),
      h('dl', {}, linhasEA.map(([a, b]) => [h('dt', {}, a), h('dd', {}, f0(b))])),
      num(nac.locais_viraveis_lula) !== null ? h('p', { class: 'nota-dois-lados' }, 'A conta vale para os dois lados: o mesmo voto em aberto que pode virar um local para Flávio pode virar outro para Lula. Por isso os dois números aparecem juntos.') : null);
  }
  $('#hero-stats').replaceChildren(...stats.map(([v, r]) => h('div', {}, h('dt', {}, r), h('dd', {}, f0(v)))));

  // parâmetros declarados
  const par = ind.parametros || {};
  const linhas = [];
  if (num(par.teto_potencial) !== null) linhas.push(['Teto do potencial (índice 100)', `${f1(par.teto_potencial)} votos por 100 aptos`]);
  if (num(par.p99_potencial) !== null) linhas.push(['Percentil 99 observado do potencial', `${f1(par.p99_potencial)} por 100 aptos`]);
  if (num(par.taxa_conversao) !== null) linhas.push(['Conversas que convencem (hipótese)', `${f0(par.taxa_conversao * 100)}%`]);
  const tr = par.transferencia_terceira || {};
  if (num(tr.sem_escolha) !== null) linhas.push(['Terceira via sem escolha no 2º turno', `${f0(tr.sem_escolha * 100)}%`]);
  if (num(tr.flavio_entre_escolhem) !== null) linhas.push(['Flávio entre quem escolhe', `${f0(tr.flavio_entre_escolhem * 100)}%`]);
  const box = $('#parametros');
  if (linhas.length) {
    box.replaceChildren(h('p', { class: 'kicker' }, 'Parâmetros desta versão dos dados'), h('dl', {}, linhas.map(([a, b]) => [h('dt', {}, a), h('dd', {}, b)])));
  }

  // fontes com bytes e sha256
  const fontes = Array.isArray(ind.fontes) ? ind.fontes : [];
  $('#fontes-corpo').replaceChildren(
    ...fontes.map((f) => {
      const bytes = num(f.bytes ?? f.tamanho);
      const sha = str(f.sha256);
      return h('tr', {},
        h('td', {}, str(f.chave, str(f.nome, '')), f.data ? h('div', { class: 'ajuda', style: 'margin:2px 0 0;font-size:.8rem' }, String(f.data)) : null),
        h('td', {}, h('code', {}, str(f.caminho, str(f.arquivo, str(f.path, ''))))),
        h('td', { class: 'num' }, bytes === null ? SD : tamanho(bytes)),
        h('td', {}, sha ? h('code', { title: sha }, sha.slice(0, 12)) : SD));
    }),
  );
  if (!fontes.length) $('.tabela-rolagem').hidden = true;
  if (ind.gerado_em) {
    const d = new Date(ind.gerado_em);
    $('#gerado-em').textContent = Number.isNaN(d.getTime())
      ? `Dados gerados em ${ind.gerado_em}.`
      : `Dados gerados em ${d.toLocaleDateString('pt-BR')}, às ${d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}. Versão do contrato: ${ind.versao_contrato || SD}.`;
  }
}

function tamanho(b) {
  if (b < 1024) return `${nf0.format(b)} B`;
  if (b < 1024 ** 2) return `${nf1.format(b / 1024)} KB`;
  if (b < 1024 ** 3) return `${nf1.format(b / 1024 ** 2)} MB`;
  return `${nf1.format(b / 1024 ** 3)} GB`;
}

function estrelas() {
  // 27 estrelas, uma por unidade da federação, como na bandeira. Posição pseudoaleatória fixa.
  const g = $('#estrelas');
  if (!g) return;
  let s = 20261025;
  const rnd = () => ((s = (s * 1103515245 + 12345) % 2147483648) / 2147483648);
  const NS = 'http://www.w3.org/2000/svg';
  for (let i = 0; i < 27; i += 1) {
    const c = document.createElementNS(NS, 'circle');
    c.setAttribute('cx', (rnd() * 1200).toFixed(1));
    c.setAttribute('cy', (rnd() * 500).toFixed(1));
    c.setAttribute('r', (0.8 + rnd() * 2.2).toFixed(2));
    c.setAttribute('opacity', (0.25 + rnd() * 0.55).toFixed(2));
    g.append(c);
  }
}

/* ------------------------------------------------------------------ conversas e propostas */

const ORDEM_ORIGEM = ['abstencao', 'brancos', 'nulos', 'cury', 'renan', 'caiado', 'zema', 'outros_nominais', 'bolsonaro_2022'];

function votosDaOrigem(l, k) {
  if (!l) return null;
  if (k === 'abstencao') {
    const a = num(l.aptos);
    const c = num(l.comparecimento);
    return a === null || c === null ? null : a - c;
  }
  if (k === 'bolsonaro_2022') {
    const r = num(l.reencontro_a);
    const a = num(l.aptos);
    if (r === null || a === null) return null;
    return r > 0 ? Math.round((r * a) / 100) : 0;
  }
  return num(l[k]);
}

function renderConversas(local) {
  const fonte = E.textos.conversas_por_origem;
  const sec = $('#conversas');
  if (!fonte || typeof fonte !== 'object' || !Object.keys(fonte).length) {
    sec.hidden = true;
    return;
  }
  sec.hidden = false;
  $('#conversas-intro').textContent = tx('pagina.conversas_intro');
  const chaves = [...ORDEM_ORIGEM.filter((k) => fonte[k]), ...Object.keys(fonte).filter((k) => !ORDEM_ORIGEM.includes(k))];
  let itens = chaves.map((k, i) => ({ k, i, o: txo(fonte, k), v: votosDaOrigem(local, k) }));
  if (local) itens.sort((a, b) => (b.v ?? -1) - (a.v ?? -1) || a.i - b.i);
  $('#conversas-local').textContent = local
    ? `Ordenado pelo local do boletim aberto, ${caixa(local.nome)}: quantos votos cada origem representou no 1º turno. Quem votou em Bolsonaro em 2022 e não em Flávio é saldo agregado, não contagem de pessoas.`
    : 'Abra um boletim acima para ver quantos votos cada origem representa no seu local de votação.';
  const vv = local ? E.varsAtual || {} : {};
  $('#lista-conversas').replaceChildren(...itens.map(({ k, o, v }) => {
    const jeitos = Array.isArray(o.um_jeito_de_conversar) ? o.um_jeito_de_conversar.map((x) => it(x, vv)).filter(Boolean) : [];
    const [ab, cf, cu] = [it(o.abertura, vv), it(o.como_funciona, vv), it(o.cuidado, vv)];
    return h('details', { class: 'origem', id: `origem-${k}` },
      h('summary', {}, h('span', { class: 't' }, str(o.rotulo, k)),
        local && v !== null ? h('span', { class: `q${v ? '' : ' zero'}` }, `${f0(v)} ${v === 1 ? 'voto' : 'votos'}`) : null),
      h('div', { class: 'corpo' },
        ab ? h('p', {}, ab) : null,
        cf ? [h('h4', {}, 'Como funciona'), h('p', { style: 'margin:0' }, cf)] : null,
        jeitos.length ? [h('h4', {}, 'Um jeito de conversar'), h('ul', {}, jeitos.map((t) => h('li', {}, t)))] : null,
        cu ? h('p', { class: 'cuidado' }, h('b', {}, 'Cuidado'), cu) : null));
  }));
}

let promessaPropostas = null;
function carregarPropostas() {
  if (!promessaPropostas) {
    promessaPropostas = fetch('assets/politize/propostas.json', { credentials: 'same-origin' })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => (d && Array.isArray(d.temas) && d.temas.length ? d : null))
      .catch(() => null);
  }
  return promessaPropostas;
}

function temaDoProblema(prop, problema) {
  if (!prop || !problema) return null;
  const alvo = norm(problema);
  return prop.temas.find((t) => (Array.isArray(t.problema_quaest) ? t.problema_quaest : [t.problema_quaest]).some((p) => p && norm(p) === alvo)) || null;
}

async function renderPropostas(problema) {
  const prop = await carregarPropostas();
  const sec = $('#propostas');
  if (!prop) {
    sec.hidden = true;
    return null;
  }
  const abrir = temaDoProblema(prop, problema);
  $('#lista-propostas').replaceChildren(...prop.temas.map((t) => {
    const cit = Array.isArray(t.citacoes) ? t.citacoes.filter((c) => c && str(c.texto)) : [];
    return h('details', { class: 'origem', id: `proposta-${String(t.id || '').replace(/[^\w-]/g, '')}`, open: abrir === t ? true : null },
      h('summary', {}, h('span', { class: 't' }, str(t.nome, String(t.id || ''))),
        cit.length ? h('span', { class: 'q zero' }, `${cit.length} ${cit.length === 1 ? 'trecho' : 'trechos'}`) : null),
      h('div', { class: 'corpo' },
        str(t.resumo) ? h('p', {}, t.resumo) : null,
        cit.map((c) => h('blockquote', { class: 'citacao' },
          str(c.titulo) ? h('p', { style: 'font-style:normal;font-family:var(--sans);font-weight:700;font-size:.95rem;margin-bottom:4px' }, c.titulo) : null,
          h('p', {}, `“${c.texto.trim()}”`),
          h('footer', {}, num(c.pagina) !== null || str(String(c.pagina ?? '')) ? `Programa de governo, p. ${c.pagina}` : 'Programa de governo')))));
  }));
  const aus = Array.isArray(prop.temas_ausentes) ? prop.temas_ausentes.map((x) => (typeof x === 'string' ? x : str(x && (x.nome || x.tema)))).filter(Boolean) : [];
  $('#propostas-ausentes').textContent = aus.length ? `Temas sem trecho correspondente no programa: ${aus.join(', ')}.` : '';
  const f = prop.fonte || {};
  const pf = $('#propostas-fonte');
  pf.replaceChildren(h('span', {},
    'Fonte: ', [str(f.titulo), str(f.candidato)].filter(Boolean).join(', ') || 'programa de governo',
    num(f.paginas) !== null ? `, ${f.paginas} páginas` : '',
    str(f.url) && /^https:\/\//.test(f.url) ? [' · ', h('a', { href: f.url, rel: 'noopener noreferrer' }, 'documento original')] : '',
    str(f.sha256) ? [' · SHA-256 ', h('code', { title: f.sha256 }, f.sha256.slice(0, 12))] : '',
    str(f.baixado_em) ? ` · baixado em ${f.baixado_em.slice(0, 10).split('-').reverse().join('/')}` : '',
    str(f.url_tse_pagina) && /^https:\/\//.test(f.url_tse_pagina) ? [' · ', h('a', { href: f.url_tse_pagina, rel: 'noopener noreferrer' }, 'página das propostas no TSE')] : '',
    str(f.nota) ? `. Nota: ${f.nota}.` : '.'));
  sec.hidden = false;
  return abrir;
}

function irParaTema(t) {
  const el = document.getElementById(`proposta-${String(t.id || '').replace(/[^\w-]/g, '')}`);
  if (!el) return;
  el.open = true;
  el.scrollIntoView({ block: 'start' });
  el.querySelector('summary').focus({ preventScroll: true });
}

/* ------------------------------------------------------------------ variáveis do texto */

function escala100(obj, chaves) {
  const v = chaves.map((k) => num(obj[k]));
  if (v.every((x) => x === null)) return null;
  const soma = v.reduce((s, x) => s + (x || 0), 0);
  const k = soma > 0 && soma <= 1.5 ? 100 : 1;
  const o = {};
  chaves.forEach((c, i) => {
    o[c] = v[i] === null ? null : v[i] * k;
  });
  return o;
}

function perfilDo(l) {
  const esc = escala100(l, ['fund_inc', 'fund_med', 'med_sup_inc', 'superior']);
  const ida = escala100(l, ['a16_24', 'a25_34', 'a35_44', 'a45_59', 'a60']);
  const ren = escala100({ ate2: l.renda_ate2, de2a5: l.renda_de2a5, mais5: l.renda_mais5 }, ['ate2', 'de2a5', 'mais5']);
  let fem = num(l.fem);
  if (fem !== null && fem <= 1) fem *= 100;
  return { escolaridade: esc, idade: ida, renda: ren, fem };
}

function dominante(o) {
  if (!o) return null;
  let melhor = null;
  for (const [k, v] of Object.entries(o)) if (num(v) !== null && (melhor === null || v > o[melhor])) melhor = k;
  return melhor;
}

function rotPerfil(grupo, k) {
  return str(txo(txo(E.textos.perfil, grupo), k).rotulo, ROTULO_PERFIL[grupo][k] || k);
}

function problemaTopo(uf) {
  const pr = uf && uf.problemas;
  if (!pr || !pr.valores) return null;
  const lista = Object.entries(pr.valores)
    .filter(([k, v]) => num(v) !== null && !IGNORAR_PROBLEMA.has(k))
    .sort((a, b) => b[1] - a[1]);
  if (!lista.length) return null;
  return { nome: lista[0][0], pct: lista[0][1], lista, pr };
}

function conversasDo(l) {
  const falt = num(l.faltam);
  if (falt !== null && falt > 0) return { modo: 'virar', n: num(l.conversas_para_virar) };
  if (falt === 0) return { modo: 'segurar', n: num(l.conversas_para_segurar) };
  return { modo: null, n: null };
}

function varsDo(l, ufDados) {
  const V = {};
  const set = (k, txt, n) => {
    V[k] = { txt: txt === null || txt === undefined ? null : String(txt), n };
  };
  const pct = (k) => set(k, num(l[k]) === null ? null : nf1.format(l[k]), num(l[k]));
  set('nome', caixa(l.nome));
  set('bairro', caixa(l.bairro) || null);
  set('municipio', l._mun);
  set('uf', l._uf);
  for (const k of ['flavio_v', 'lula_v', 'terceira_v', 'abst_a', 'reencontro_a', 'vao_perfil_pp']) pct(k);
  set('indice', num(l.indice) === null ? null : String(l.indice), num(l.indice));
  set('faltam', num(l.faltam) === null ? null : nf0.format(l.faltam), num(l.faltam));
  const cv = conversasDo(l);
  set('conversas', cv.n === null ? null : nf0.format(Math.round(cv.n)), cv.n === null ? null : Math.round(cv.n));
  set('aptos', num(l.aptos) === null ? null : nf0.format(l.aptos), num(l.aptos));
  set('renda_mediana', num(l.renda_mediana_brl) === null ? null : brl.format(l.renda_mediana_brl), null);
  const p = perfilDo(l);
  const dr = dominante(p.renda);
  const de = dominante(p.escolaridade);
  const di = dominante(p.idade);
  set('faixa_dominante', dr ? rotPerfil('renda', dr) : null);
  set('escolaridade_dominante', de ? rotPerfil('escolaridade', de) : null);
  set('idade_dominante', di ? rotPerfil('idade', di) : null);
  const pt = problemaTopo(ufDados);
  set('problema_uf', pt ? pt.nome.toLocaleLowerCase('pt-BR') : null);
  set('problema_uf_pct', pt ? nf0.format(pt.pct) : null, pt ? pt.pct : null);
  set('arquetipo', arqInfo(l.arquetipo).nome || null);
  return V;
}

/* ------------------------------------------------------------------ fluxo principal */

async function executar(msg, fn, contexto) {
  const meu = ++E.pedido;
  estadoCarregando(msg);
  try {
    const r = await fn();
    if (meu !== E.pedido) return;
    if (r) await mostrar(r);
  } catch (e) {
    if (meu !== E.pedido) return;
    if (!(e && e.usuario)) console.error(e);
    estadoErro(e && e.usuario ? e.message : msgErro(e, contexto), e && e.usuario ? null : () => executar(msg, fn, contexto));
  }
}

function erroUsuario(msg) {
  const e = new Error(msg);
  e.usuario = true;
  return e;
}

function munDoId(id) {
  const m = /^([A-Z]{2})-([^-]+)-(\d+)-(\d+)$/.exec(String(id || ''));
  if (!m) return null;
  return E.porChave.get(chaveMun(m[1], m[2])) || null;
}

async function porLocalId(id, extra = {}) {
  const mun = munDoId(id);
  if (!mun) throw erroUsuario('O link aponta para um local de votação que não está no índice. Ele pode ter sido digitado errado ou ser de outra versão dos dados.');
  const pacote = await carregarMun(mun);
  const local = pacote.locais.find((l) => l.local_id === id);
  if (!local) throw erroUsuario('Esse local de votação não está no arquivo do município. Busque pelo CEP ou pela cidade.');
  const pool = await carregarEntorno([mun], num(local.lat) !== null ? local : null);
  return { local, pool, ref: null, origem: 'link', ...extra };
}

async function porSecao(uf, zona, secao) {
  const zonas = E.indice && E.indice.zonas;
  if (zonas && typeof zonas === 'object' && Array.isArray(zonas[uf]) && !zonas[uf].map(Number).includes(zona)) {
    const lista = zonas[uf].map(Number).sort((a, b) => a - b);
    const amostra = lista.length > 12 ? `${lista.slice(0, 12).join(', ')} e outras` : lista.join(', ');
    throw erroUsuario(`A zona ${zona} não existe ${emUF(uf)} nos dados. Zonas de ${uf}: ${amostra}. Confira no título de eleitor ou no e-Título.`);
  }
  if (zonas && typeof zonas === 'object' && !Array.isArray(zonas[uf])) {
    throw erroUsuario(`Não há dados ${deUF(uf)} nesta versão. Os estados entram conforme os boletins de urna são processados.`);
  }
  const arq = await buscarJSON(`${BASE}zona/${uf}/${zona}.json`).catch((e) => {
    if (e.status === 404) return null;
    throw e;
  });
  if (!arq) throw erroUsuario(`Não achamos a zona ${zona} ${deUF(uf)} nos dados. Confira o número no título de eleitor ou no e-Título.`);
  const linhas = tabela(arq.secoes);
  let sec = linhas.find((x) => Number(x.secao) === secao);
  let agregada = false;
  if (!sec) {
    sec = linhas.find((x) => Array.isArray(x.agregadas) && x.agregadas.map(Number).includes(secao));
    agregada = Boolean(sec);
  }
  if (!sec) {
    throw erroUsuario(`A seção ${secao} não está na zona ${zona} ${deUF(uf)} nos dados. Confira os números no título ou no e-Título. Seções criadas depois do 1º turno não têm boletim.`);
  }
  const base = await porLocalId(sec.local_id);
  return { ...base, origem: 'secao', secao: sec, secaoDigitada: secao, agregada, zona, uf };
}

async function porCep(digitos) {
  const arq = await buscarJSON(`${BASE}cep/${digitos.slice(0, 2)}.json`).catch((e) => {
    if (e.status === 404) return null;
    throw e;
  });
  if (!arq) throw erroUsuario(`Não há local de votação com CEP começando em ${digitos.slice(0, 2)} nos dados. Tente pela cidade e bairro.`);
  const ex = arq.exato || {};
  const p5 = arq.prefixo5 || {};
  let ids = null;
  let precisao = null;
  if (Array.isArray(ex[digitos]) && ex[digitos].length) {
    ids = ex[digitos];
    precisao = 'exato';
  } else if (Array.isArray(p5[digitos.slice(0, 5)]) && p5[digitos.slice(0, 5)].length) {
    ids = p5[digitos.slice(0, 5)];
    precisao = 'prefixo5';
  } else {
    for (const n of [4, 3]) {
      const pre = digitos.slice(0, n);
      const alvo = Number(digitos.slice(0, 5));
      const chaves = Object.keys(p5).filter((k) => k.startsWith(pre)).sort((a, b) => Math.abs(Number(a) - alvo) - Math.abs(Number(b) - alvo));
      if (chaves.length) {
        ids = [...new Set(chaves.slice(0, 2).flatMap((k) => p5[k]))];
        precisao = `prefixo${n}`;
        break;
      }
    }
  }
  if (!ids || !ids.length) throw erroUsuario(`Não achamos local de votação com CEP parecido com ${cepFmt(digitos)}. Tente pela cidade e bairro.`);
  const muns = [...new Map(ids.map(munDoId).filter(Boolean).map((m) => [m.chave, m])).values()];
  if (!muns.length) throw erroUsuario('Os locais desse CEP não estão no índice de municípios desta versão dos dados.');
  const pacotes = await Promise.all(muns.map(carregarMun));
  const todos = pacotes.flatMap((p) => p.locais);
  const set = new Set(ids);
  const achados = todos.filter((l) => set.has(l.local_id));
  if (!achados.length) throw erroUsuario('Os locais desse CEP não foram encontrados nos arquivos dos municípios.');
  const ref = centroide(achados);
  const local = ordenar(achados, ref)[0].l;
  const pool = await carregarEntorno(muns, ref);
  return { local, pool, ref: null, origem: 'cep', precisao, nAchados: achados.length, cep: digitos };
}

async function porCidade(mun, bairro) {
  const pacote = await carregarMun(mun);
  let ref;
  let candidatos = pacote.locais;
  if (bairro) {
    candidatos = pacote.locais.filter((l) => (l.bairro || '') === bairro);
    ref = centroide(candidatos);
  } else {
    ref = num(mun.lat) !== null ? { lat: mun.lat, lon: mun.lon } : centroide(pacote.locais);
  }
  if (!candidatos.length) throw erroUsuario('Esse bairro não tem local de votação nos dados.');
  const local = ordenar(candidatos, ref)[0].l;
  const pool = await carregarEntorno([mun], num(local.lat) !== null ? local : ref);
  return { local, pool, ref: null, origem: bairro ? 'bairro' : 'cidade', bairro };
}

async function porPosicao(pos) {
  const voce = { lat: pos.coords.latitude, lon: pos.coords.longitude };
  const cand = E.muns.filter((m) => num(m.lat) !== null).map((m) => [m, haversine(voce, m)]).sort((a, b) => a[1] - b[1]);
  if (!cand.length) throw erroUsuario('O índice desta versão não tem coordenadas de municípios.');
  const [mun, d] = cand[0];
  const pool = await carregarEntorno([mun], voce);
  const ord = ordenar(pool, voce).filter((x) => x.d !== null);
  if (!ord.length) throw erroUsuario('Não achamos local de votação com coordenada perto de você.');
  const longe = ord[0].d > 50000 || d > 80000;
  return { local: ord[0].l, pool, ref: voce, origem: 'geo', longe };
}

/* ------------------------------------------------------------------ resultado */

async function mostrar(r) {
  E.atual = r;
  const { local, pool } = r;
  const centro = r.ref || (num(local.lat) !== null ? local : null);
  let ord = ordenar(pool.filter((l) => l.local_id !== local.local_id), centro);
  if (!centro) ord = ord.filter((x) => x.l._munChave === local._munChave);
  const aoRedor = ord.slice(0, N_AO_REDOR).sort((a, b) => (num(b.l.indice) ?? -1) - (num(a.l.indice) ?? -1) || (a.d ?? Infinity) - (b.d ?? Infinity));
  const raio1km = num(local.lat) !== null ? ordenar(pool, local).filter((x) => x.d !== null && x.d <= 1000).map((x) => x.l) : [];

  const ufDados = await buscarJSON(`${BASE}uf/${local._uf}.json`).catch(() => null);
  const pt0 = problemaTopo(ufDados);
  const temaAberto = await renderPropostas(pt0 ? pt0.nome : null);
  const vars = varsDo(local, ufDados);
  E.varsAtual = vars;
  renderConversas(local);
  const info = arqInfo(local.arquetipo);

  try {
    history.replaceState(null, '', `${location.pathname}${location.search}#${hashDo(r)}`);
  } catch {
    // Em alguns navegadores embutidos replaceState falha; o boletim aparece mesmo assim.
  }

  const alvo = alvoResultado();
  const boletim = renderBoletim(local, info, vars, ufDados, r, temaAberto);
  const viz = renderVizinhanca(local, aoRedor, pool, r, raio1km);
  const comp = renderCompartilhar(local, info, vars);
  const secBox = r.secao ? renderSecao(r, local) : null;
  const bairros = renderBairros(local, pool);
  alvo.replaceChildren(...[secBox, boletim, viz, bairros, comp].filter(Boolean));
  $('#resultado').setAttribute('aria-busy', 'false');
  document.title = `${caixa(local.nome)} · Politize sua vizinhança`;

  const titulo = (secBox || boletim).querySelector('h2');
  titulo.setAttribute('tabindex', '-1');
  titulo.focus({ preventScroll: true });
  $('#resultado').scrollIntoView({ block: 'start' });

  desenharMapa(viz.querySelector('.mapa-box'), local, aoRedor, pool, r).catch((e) => {
    console.warn('mapa', e);
  });
  desenharCardDo(comp, local, info, vars).catch((e) => console.warn('card', e));
}

function hashDo(r) {
  if (r.secao) return `s=${encodeURIComponent(`${r.uf}-${r.zona}-${r.secaoDigitada}`)}`;
  return `l=${encodeURIComponent(r.local.local_id)}`;
}

function etiquetaPrecisao(r) {
  if (r.origem === 'cep') {
    const c = cepFmt(r.cep);
    const m = {
      exato: `O CEP ${c} é de ${r.nAchados === 1 ? 'um local de votação' : `${r.nAchados} locais de votação`}. Mostramos o mais próximo do centro deles. A busca usa o CEP do local, não o seu endereço.`,
      prefixo5: `Nenhum local de votação tem exatamente o CEP ${c}. Mostramos locais com os cinco primeiros dígitos iguais: é uma aproximação pelo CEP dos locais, não pelo seu endereço.`,
      prefixo4: `Nenhum local tem CEP com os cinco primeiros dígitos de ${c}. Usamos o CEP de local mais parecido: aproximação grossa, confira o bairro.`,
      prefixo3: `Aproximação grossa: usamos o CEP de local de votação mais parecido com ${c}. Confira o bairro ou busque pela cidade.`,
    };
    return m[r.precisao] || '';
  }
  if (r.origem === 'geo') {
    return r.longe
      ? 'Você parece estar longe de qualquer local de votação dos dados. Mostramos o mais próximo, mas confira se é mesmo a sua vizinhança.'
      : 'Local de votação mais próximo da localização do aparelho. A coordenada não saiu do seu navegador.';
  }
  if (r.origem === 'secao') return 'Este é o local de votação da sua seção. A leitura do local soma todas as seções do mesmo endereço e é a principal para a conversa.';
  if (r.origem === 'bairro') return 'Local de votação do bairro mais próximo do centro dos locais do bairro.';
  if (r.origem === 'cidade') return 'Local de votação mais próximo do centro da cidade. Escolha um bairro para chegar mais perto.';
  return '';
}

function renderSecao(r, local) {
  const x = r.secao;
  const a = arqInfo(x.arquetipo);
  const votos = (k, kp) => h('dd', {}, num(x[k]) === null ? SD : f0(x[k]), h('small', {}, num(x[kp]) === null ? '' : `${nf1.format(x[kp])}% dos válidos`));
  const itens = [
    ['Aptos', h('dd', {}, f0(x.aptos), h('small', {}, num(x.comparecimento) === null ? '' : `${f0(x.comparecimento)} votaram`))],
    ['Flávio', votos('flavio', 'flavio_v')],
    ['Lula', votos('lula', 'lula_v')],
    ['Outros nomes', votos('terceira', 'terceira_v')],
    ['Abstenção', h('dd', {}, num(x.abst_a) === null ? SD : `${nf1.format(x.abst_a)}%`, h('small', {}, 'dos aptos'))],
    ['Bolsonaro em 2022', h('dd', {}, num(x.bolsonaro22_1t_v) === null ? SD : `${nf1.format(x.bolsonaro22_1t_v)}%`,
      h('small', {}, num(x.bolsonaro22_1t_v) === null ? 'seção sem par em 2022' : `1º turno, válidos; Flávio agora ${f1(x.flavio_v)}%`))],
  ];
  const falt = num(x.faltam);
  const conta = falt === null ? null : falt > 0
    ? `Na projeção do 2º turno, faltam ${f0(falt)} ${falt === 1 ? 'voto' : 'votos'} para Flávio passar Lula nesta seção${num(x.conversas_para_virar) !== null ? `, ou ${f0(x.conversas_para_virar)} ${Math.round(x.conversas_para_virar) === 1 ? 'conversa' : 'conversas'} pela hipótese declarada` : ''}.`
    : 'Na projeção do 2º turno, Flávio já passa Lula nesta seção.';
  return h('section', { class: 'sua-secao entra', 'aria-labelledby': 'sec-titulo' },
    h('p', { class: 'kicker' }, `Sua seção · ${NOME_UF[r.uf] || r.uf} · Zona ${r.zona}`),
    h('h2', { id: 'sec-titulo' }, `Seção ${x.secao}`),
    h('p', { class: 'sub' }, `Vota em ${caixa(x.local || local.nome)}${x.bairro || local.bairro ? `, ${caixa(x.bairro || local.bairro)}` : ''}, ${local._mun}.`),
    r.agregada ? h('p', { class: 'agregada' }, `A seção ${r.secaoDigitada} foi agregada à seção ${x.secao} no 1º turno: as duas votaram na mesma urna, e os números abaixo somam as duas.`) : null,
    h('dl', { class: 'sec-grade' }, itens.map(([t, dd]) => h('div', {}, h('dt', {}, t), dd))),
    h('div', { class: 'sec-arq' }, losango(x.indice, a.cor.fill, 52),
      h('div', {}, h('b', {}, a.nome || SD), h('span', {}, `Índice de conversa da seção: ${x.indice ?? SD} de 100`))),
    conta ? h('p', { class: 'ressalva', style: 'border-top:0;padding-top:0' }, conta) : null,
    h('p', { class: 'ressalva' }, 'Uma seção tem de 200 a 400 eleitores, então o número dela oscila mais. A leitura principal da conversa é a do local de votação, logo abaixo, que soma as seções do mesmo endereço. O voto é secreto: nenhum número descreve uma pessoa.'));
}

function barra(rotulo, valor, dom = false, cls = '', casas = 1) {
  const v = num(valor);
  const larg = v === null ? 0 : Math.max(0, Math.min(100, v));
  return h('div', { class: `barra-l${dom ? ' dom' : ''}` },
    h('span', { class: 'r' }, rotulo),
    h('span', { class: 't', 'aria-hidden': 'true' }, h('span', { class: `p ${cls}`, style: `width:${larg.toFixed(1)}%` })),
    h('span', { class: 'n' }, v === null ? SD : `${casas ? nf1.format(v) : nf0.format(v)}%`));
}

function renderBoletim(l, info, vars, ufDados, r, temaAberto = null) {
  const T = E.textos;
  const par = (E.indice && E.indice.parametros) || {};
  const teto = num(par.teto_potencial) || 40;
  const rotComp = {};
  for (const k of ['c_terceira', 'c_ausentes', 'c_reencontro', 'c_perfil']) rotComp[k] = str(txo(T.componentes, k).rotulo, k);

  // cabeçalho
  const etiquetas = [];
  if (num(l.aptos) !== null) etiquetas.push(h('li', {}, `${f0(l.aptos)} eleitores aptos`));
  if (num(l.secoes) !== null) etiquetas.push(h('li', {}, `${f0(l.secoes)} ${l.secoes === 1 ? 'seção' : 'seções'}`));
  if (l.zona !== null && l.zona !== undefined) etiquetas.push(h('li', {}, `Zona ${l.zona}`));
  if (str(l.tipo_local) && norm(l.tipo_local) !== 'convencional') etiquetas.push(h('li', {}, caixa(l.tipo_local)));
  if (SETOR_TIPO[l.setor_tipo]) etiquetas.push(h('li', {}, SETOR_TIPO[l.setor_tipo]));
  if (l.setor_situacao === 'rural') etiquetas.push(h('li', {}, 'Setor rural (IBGE)'));
  if (l._perfilFonte === 'zona') etiquetas.push(h('li', { class: 'alerta' }, 'Perfil da zona eleitoral, não da seção'));
  if (num(l.cobertura_2022) !== null && l.cobertura_2022 < 0.6) etiquetas.push(h('li', { class: 'alerta' }, 'Comparação com 2022 parcial'));

  const endereco = [caixa(l.endereco), caixa(l.bairro), `${l._mun}${l._uf && l._uf !== 'ZZ' ? `/${l._uf}` : ''}`, cepFmt(l.cep) ? `CEP ${cepFmt(l.cep)}` : '']
    .filter(Boolean)
    .join(' · ');
  const precisao = etiquetaPrecisao(r);

  const cab = h('header', { class: 'bol-cab' },
    h('p', { class: 'kicker' }, 'Boletim da vizinhança · 1º turno de 2026'),
    h('h2', { id: 'bol-titulo' }, caixa(l.nome)),
    h('p', { class: 'bol-end' }, endereco),
    h('ul', { class: 'etiquetas', 'aria-label': 'Sobre o local' }, etiquetas),
    precisao ? h('p', { class: 'precisao' }, precisao) : null);

  // carta + signo
  const svg = carta({ local: l, teto, rotulos: rotComp, fmt: (v) => nf1.format(v), arquetipo: info.nome });
  const legenda = h('ul', { class: 'legenda', 'aria-hidden': 'true' },
    [['flavio', 'Flávio'], ['lula', 'Lula'], ['terceira', 'Outros nomes'], ['bn', 'Branco e nulo'], ['abst', 'Abstenção']].map(([k, n]) =>
      h('li', {}, h('i', { class: k === 'abst' ? 'abst' : '', style: k === 'abst' ? null : `background:${CORES[k]}` }), n)));
  const legSet = h('ul', { class: 'legenda', 'aria-hidden': 'true' },
    ['c_terceira', 'c_ausentes', 'c_reencontro', 'c_perfil'].map((k) => h('li', {}, h('i', { style: `background:${CORES[k]}` }), rotComp[k])));
  const pctBr = num(l.percentil);
  const pctUf = num(l.percentil_uf);
  const estado = deUF(l._uf);
  const fraseRank = pctBr !== null
    ? `Esta vizinhança tem mais voto em disputa que ${nf0.format(pctBr)}% dos locais de votação do Brasil${pctUf !== null ? ` e que ${nf0.format(pctUf)}% dos ${estado}` : ''}.`
    : '';
  const cartaBox = h('div', { class: 'carta-box' }, svg,
    fraseRank ? h('p', { class: 'rank' }, fraseRank) : null,
    h('p', { class: 'legenda-t' }, 'Anel: os aptos no 1º turno'), legenda,
    h('p', { class: 'legenda-t' }, 'Setores: votos em disputa por 100 aptos'), legSet);

  const sec = l.arquetipo_secundario ? arqInfo(l.arquetipo_secundario) : null;
  const leitura = interp(info.leitura, vars);
  const signo = h('div', { class: 'signo-box' },
    h('p', { class: 'signo' }, info.signo ? `Arquétipo · signo ${info.signo}` : 'Arquétipo'),
    h('p', { class: 'nome-arq' }, info.nome || SD),
    info.lema ? h('p', { class: 'lema' }, info.lema) : null,
    leitura ? h('p', { class: 'leitura' }, leitura) : null,
    destaqueAberto(l),
    info.fazer.length || info.naoFazer.length
      ? h('div', { class: 'fazer' },
        info.fazer.length ? h('div', { class: 'sim' }, h('h4', {}, 'O que fazer'), h('ul', {}, info.fazer.map((t) => h('li', {}, interp(t, vars) || t.replace(/\{\w+\}/g, ''))))) : null,
        info.naoFazer.length ? h('div', { class: 'nao' }, h('h4', {}, 'O que não fazer'), h('ul', {}, info.naoFazer.map((t) => h('li', {}, interp(t, vars) || t.replace(/\{\w+\}/g, ''))))) : null)
      : null,
    sec && sec.nome ? h('p', { class: 'secundario' }, h('b', {}, `Traço secundário: ${sec.nome}. `), sec.lema) : null);

  const topo = h('div', { class: 'bol-topo' }, cartaBox, signo);

  // blocos
  const blocos = h('div', { class: 'bol-blocos' },
    blocoComponentes(l, teto, rotComp),
    blocoConta(l, vars, par),
    blocoTema(l, ufDados, temaAberto, vars),
    bloco2022(l),
    blocoPerfil(l));

  const art = h('article', { class: 'boletim entra', 'aria-labelledby': 'bol-titulo', style: `--cor-arq:${info.cor.fill};--cor-arq-txt:${info.cor.txt}` }, cab, topo, blocos);
  return art;
}

function destaqueAberto(l) {
  const f = num(l.flavio);
  const lu = num(l.lula);
  const fora = bnaDo(l);
  if (f === null || lu === null) return null;
  const dif = f - lu;
  const lado = dif === 0 ? 'Flávio e Lula empataram aqui no 1º turno' : dif > 0
    ? `No 1º turno, Flávio fez ${f0(dif)} ${dif === 1 ? 'voto' : 'votos'} a mais que Lula aqui (${f0(f)} a ${f0(lu)})`
    : `No 1º turno, Lula fez ${f0(-dif)} ${dif === -1 ? 'voto' : 'votos'} a mais que Flávio aqui (${f0(lu)} a ${f0(f)})`;
  const resto = fora === null ? '' : ` Branco, nulo e quem não foi votar somam ${f0(fora)}.`;
  const v = viravelDo(l);
  const ea = emAberto(l);
  return h('div', { class: `aberto${v === 'flavio' ? ' viravel' : ''}` },
    h('p', {}, `${lado}.${resto}${ea !== null ? ` Com outros nomes, ${f0(ea)} votos ficaram em aberto.` : ''}`),
    v === 'flavio' ? h('p', { class: 'selo' }, 'Só branco, nulo e abstenção já virariam este local para Flávio.') : null,
    v === 'lula' ? h('p', { class: 'selo contra' }, 'O mesmo vale ao contrário: só branco, nulo e abstenção já virariam este local para Lula. A vantagem precisa de cuidado.') : null);
}

function blocoComponentes(l, teto, rotComp) {
  const T = E.textos;
  const itens = ['c_terceira', 'c_ausentes', 'c_reencontro', 'c_perfil'].map((k) => {
    const c = txo(T.componentes, k);
    const amarelo = k === 'c_ausentes';
    const claro = k === 'c_perfil';
    return h('li', {},
      h('span', { class: 'val', style: `background:${CORES[k]};color:${amarelo || claro ? '#151812' : '#ffffff'}` }, f1(l[k])),
      h('div', {}, h('b', {}, rotComp[k]), it(c.explicacao) ? h('p', {}, it(c.explicacao)) : null));
  });
  const pot = num(l.potencial);
  itens.push(h('li', { class: 'pot' },
    pot === null ? 'Potencial sem dado.' : `Soma: ${f1(pot)} votos em disputa por 100 aptos. O índice divide a soma por ${f1(teto)} e para em 100: aqui deu ${l.indice ?? SD}.`));
  return h('section', { class: 'bloco', 'aria-labelledby': 'b-comp' },
    h('p', { class: 'kicker' }, 'Os quatro setores da carta'),
    h('h3', { id: 'b-comp' }, 'O que soma no índice de conversa'),
    h('ul', { class: 'componentes' }, itens));
}

function blocoConta(l, vars, par) {
  const cv = conversasDo(l);
  const modelo = cv.modo ? tx(`conta_2t.${cv.modo}`) : '';
  const frase = interp(modelo, vars);
  const regra = tx('conta_2t.regra_transferencia');
  const n = cv.n === null ? null : Math.round(cv.n);
  const taxa = num(par.taxa_conversao);
  return h('section', { class: 'bloco', 'aria-labelledby': 'b-conta' },
    h('p', { class: 'kicker' }, 'Projeção com premissas declaradas'),
    h('h3', { id: 'b-conta' }, 'A conta do 2º turno'),
    h('div', { class: 'placar' },
      h('div', { class: 'f' }, h('b', {}, f0(l.flavio_2t)), h('span', {}, 'votos Flávio, projeção')),
      h('div', { class: 'l' }, h('b', {}, f0(l.lula_2t)), h('span', {}, 'votos Lula, projeção'))),
    n !== null
      ? h('div', { class: 'conta-num' }, h('b', {}, nf0.format(n)),
        h('span', {}, cv.modo === 'virar'
          ? `${n === 1 ? 'conversa' : 'conversas'} para virar o local${num(l.faltam) !== null ? ` (faltam ${f0(l.faltam)} ${l.faltam === 1 ? 'voto' : 'votos'})` : ''}`
          : `${n === 1 ? 'conversa' : 'conversas'} para segurar o local`))
      : null,
    frase ? h('p', {}, frase) : null,
    regra ? h('p', { class: 'regra' }, regra) : null,
    taxa !== null && !regra ? h('p', { class: 'regra' }, `Hipótese: ${f0(taxa * 100)}% das conversas convencem.`) : null);
}

function blocoTema(l, ufDados, temaAberto = null, vars = {}) {
  const pt = problemaTopo(ufDados);
  const temas = E.textos.temas || {};
  const filhos = [h('p', { class: 'kicker' }, `Problema mais grave · ${NOME_UF[l._uf] || l._uf}`), h('h3', { id: 'b-tema' }, 'Sobre o que conversar')];
  let tema;
  if (pt) {
    tema = txo(temas, pt.nome);
    if (!str(tema.abertura) && !str(tema.pergunta)) tema = txo(temas, 'default');
    filhos.push(h('div', { class: 'tema-cab' }, h('span', { class: 'pct' }, `${nf0.format(pt.pct)}%`), h('span', {}, `apontam ${pt.nome.toLocaleLowerCase('pt-BR')} como o problema mais grave do estado`)));
    filhos.push(h('div', { class: 'barras' }, pt.lista.slice(0, 4).map(([k, v], i) => barra(k, v, i === 0, '', 0))));
  } else {
    tema = txo(temas, 'default');
    filhos.push(h('p', {}, l._uf === 'ZZ'
      ? 'A pesquisa estadual sobre o problema mais grave não cobre o exterior. Use a pergunta aberta abaixo.'
      : 'Este estado não tem a pergunta sobre o problema mais grave nos dados. Use a pergunta aberta abaixo.'));
  }
  const dl = h('dl', {});
  const [ab, pe, cu] = [it(tema.abertura, vars), it(tema.pergunta, vars), it(tema.cuidado, vars)];
  if (ab) dl.append(h('dt', {}, 'Como abrir'), h('dd', {}, ab));
  if (pe) dl.append(h('dt', {}, 'Pergunta para ouvir'), h('dd', { class: 'pergunta' }, pe));
  if (cu) dl.append(h('dt', {}, 'Cuidado'), h('dd', {}, cu));
  if (dl.children.length) filhos.push(h('div', { class: 'tema' }, dl));
  if (pt && temaAberto) {
    filhos.push(h('p', {}, h('button', { type: 'button', class: 'link-tema', onclick: () => irParaTema(temaAberto) },
      `Ver o que o programa de Flávio diz sobre ${pt.nome.toLocaleLowerCase('pt-BR')}`)));
  }
  if (pt) {
    const pr = pt.pr;
    const partes = [str(pr.pergunta), pr.campo ? `campo ${pr.campo}` : '', pr.fonte ? `arquivo ${pr.fonte}` : '', num(pr.pagina) !== null ? `p. ${pr.pagina}` : ''].filter(Boolean);
    filhos.push(h('p', { class: 'fonte-mini' }, `Fonte: ${partes.join(' · ')}`));
  }
  return h('section', { class: 'bloco', 'aria-labelledby': 'b-tema' }, filhos);
}

function bloco2022(l) {
  const filhos = [h('p', { class: 'kicker' }, 'Medido na urna, por seção'), h('h3', { id: 'b-2022' }, '2022 e 2026 no mesmo local')];
  if (num(l.bolsonaro22_1t_v) === null && num(l.lula22_1t_v) === null) {
    filhos.push(h('p', {}, 'As seções deste local não foram casadas com as de 2022. Sem comparação aqui.'));
  } else {
    filhos.push(h('div', { class: 'duelo' },
      barra('Bolsonaro 2022, 1º turno', l.bolsonaro22_1t_v, false, 'b22'),
      barra('Flávio 2026, 1º turno', l.flavio_v, true, 'f26'),
      barra('Lula 2022, 1º turno', l.lula22_1t_v, false, 'l22'),
      barra('Lula 2026, 1º turno', l.lula_v, false, 'l26')));
    filhos.push(h('p', { class: 'ajuda', style: 'margin-top:4px' }, 'Em % dos votos válidos.'));
    const re = num(l.reencontro_a);
    if (re !== null) {
      filhos.push(h('p', {}, re > 0
        ? `Saldo de reencontro: ${nf1.format(re)} em cada 100 aptos votaram em Bolsonaro em 2022 e não em Flávio em 2026, no agregado das seções.`
        : 'Sem saldo de reencontro: Flávio teve, em % dos aptos, pelo menos o que Bolsonaro teve no 1º turno de 2022.'));
    }
    if (num(l.bolsonaro22_2t_v) !== null) filhos.push(h('p', { class: 'ajuda' }, `No 2º turno de 2022, Bolsonaro teve ${f1(l.bolsonaro22_2t_v)}% e Lula ${f1(l.lula22_2t_v)}% dos válidos aqui.`));
    if (num(l.abst22_2t_a) !== null || num(l.abst_a) !== null) {
      filhos.push(h('h4', { class: 'sub-h' }, 'Quem faltou'));
      filhos.push(h('div', { class: 'duelo' },
        barra('Abstenção 2022, 2º turno', l.abst22_2t_a, false, 'ab22'),
        barra('Abstenção 2026, 1º turno', l.abst_a, true, 'ab26')));
      filhos.push(h('p', { class: 'ajuda', style: 'margin-top:4px' }, 'Em % dos aptos. O TSE não diz quem faltou; o perfil do eleitorado do local, mais abaixo, descreve todos os aptos, não só os ausentes.'));
    }
    if (num(l.cobertura_2022) !== null) filhos.push(h('p', { class: 'fonte-mini' }, `Cobertura do casamento com 2022: ${nf0.format(l.cobertura_2022 * 100)}% dos aptos.`));
  }
  return h('section', { class: 'bloco', 'aria-labelledby': 'b-2022' }, filhos);
}

function blocoPerfil(l) {
  const p = perfilDo(l);
  const T = E.textos;
  const grupo = (titulo, chave, valores, nota) => {
    if (!valores) return null;
    const dom = dominante(valores);
    const como = dom ? it(txo(txo(T.perfil, chave), dom).como_conversar) : '';
    return h('div', {},
      h('h4', {}, titulo, nota ? ' ' : null, nota ? h('span', { class: 'estimativa' }, nota) : null),
      h('div', { class: 'barras' }, Object.entries(valores).map(([k, v]) => barra(chave === 'renda' ? (ROTULO_PERFIL.renda[k] || k) : rotPerfil(chave, k), v, k === dom))),
      como ? h('p', { class: 'dica' }, h('b', {}, 'Como conversar'), como) : null);
  };
  const sexo = p.fem === null ? null : h('div', {}, h('h4', {}, 'Sexo'), h('div', { class: 'barras' }, barra('Mulheres', p.fem, p.fem >= 50), barra('Homens', 100 - p.fem, p.fem < 50)));
  const renda = grupo('Renda domiciliar', 'renda', p.renda, 'estimativa');
  if (renda && num(l.renda_mediana_brl) !== null) {
    renda.append(h('p', { class: 'ajuda' }, `Mediana estimada: ${brl.format(l.renda_mediana_brl)} por domicílio. Estimativa pela PNAD a partir da escolaridade do eleitorado e da situação do setor, não medição no bairro.`));
  }
  const fonte = l._perfilFonte === 'zona' ? 'Escolaridade, idade e sexo vêm do perfil da zona eleitoral (o TSE não publicou o arquivo por seção deste estado).' : 'Escolaridade, idade e sexo vêm do cadastro do TSE por seção, em % do eleitorado do local.';
  const conteudo = [grupo('Escolaridade', 'escolaridade', p.escolaridade), grupo('Idade', 'idade', p.idade), sexo, renda].filter(Boolean);
  return h('section', { class: 'bloco largo', 'aria-labelledby': 'b-perfil' },
    h('p', { class: 'kicker' }, 'Perfil do eleitorado do local'),
    h('h3', { id: 'b-perfil' }, 'Com quem conversar'),
    conteudo.length ? h('div', { class: 'perfil-g' }, conteudo) : h('p', {}, 'Sem perfil do eleitorado para este local.'),
    h('p', { class: 'fonte-mini' }, `${fonte} Nenhum número descreve uma pessoa.`));
}

/* ------------------------------------------------------------------ vizinhança: lista e mapa */

function blocoRaio(local, raio1km) {
  if (!raio1km.length) return null;
  const soma = (k) => raio1km.reduce((s, l) => s + (num(l[k]) || 0), 0);
  const ea = raio1km.reduce((s, l) => s + (emAberto(l) || 0), 0);
  const f = soma('flavio');
  const lu = soma('lula');
  const n = raio1km.length;
  return h('div', { class: 'raio-1km' },
    h('p', { class: 'kicker' }, 'Num raio de 1 km'),
    h('p', { class: 'raio-t1' }, `${n} ${n === 1 ? 'local de votação' : 'locais de votação'} a até 1 km de ${caixa(local.nome)}, somados:`),
    h('dl', {},
      h('div', { class: 'f' }, h('dt', {}, 'Flávio'), h('dd', {}, f0(f))),
      h('div', { class: 'l' }, h('dt', {}, 'Lula'), h('dd', {}, f0(lu))),
      h('div', { class: 'a' }, h('dt', {}, 'Em aberto'), h('dd', {}, f0(ea)))),
    h('p', { class: 'ajuda' }, `${f >= lu ? `Flávio à frente por ${f0(f - lu)}` : `Lula à frente por ${f0(lu - f)}`}. Em aberto: outros nomes, branco, nulo e abstenção. Distância em linha reta.`));
}

function renderVizinhanca(local, aoRedor, pool, r, raio1km = []) {
  const geo = r.origem === 'geo';
  const item = (l, d, atual, n = 0) => {
    const a = arqInfo(l.arquetipo);
    return h('li', {}, h('button', {
      type: 'button',
      'aria-current': atual ? 'true' : null,
      onclick: atual ? null : () => trocarLocal(l),
      'aria-label': `${caixa(l.nome)}, ${caixa(l.bairro) || l._mun}, arquétipo ${a.nome}, índice ${l.indice ?? SD}${d !== null ? `, a ${distTxt(d)}${geo ? ' de você' : ''}` : ''}${atual ? ', boletim aberto' : ''}`,
    },
    losango(l.indice, a.cor.fill, 44),
    h('span', {}, h('span', { class: 'nome' }, n ? h('span', { class: 'nlista' }, `${n}.`) : null, caixa(l.nome)), h('span', { class: 'sub' }, `${a.nome} · ${caixa(l.bairro) || l._mun}`)),
    h('span', { class: 'dist' }, atual ? (geo && d !== null ? distTxt(d) : 'aberto') : distTxt(d))));
  };
  const dLocal = geo ? haversine(r.ref, local) : null;
  const lista = h('div', { class: 'ao-redor' },
    h('p', { class: 'kicker' }, 'Ao redor'),
    h('h3', {}, geo ? 'Locais de votação perto de você' : 'Os locais de votação mais próximos'),
    h('p', { class: 'ajuda', style: 'margin:0 0 10px' }, 'Os sete mais próximos, do maior para o menor índice de conversa.'),
    h('ol', {}, item(local, dLocal, true), aoRedor.map((x, i) => item(x.l, x.d, false, i + 1))),
    h('p', { class: 'ajuda' }, geo ? 'Distância em linha reta a partir da localização do aparelho.' : 'Distância em linha reta a partir do local do boletim. Toque num local para abrir o boletim dele.'));
  const mapa = h('div', { class: 'mapa-box' }, h('p', { class: 'kicker' }, 'Mapa da vizinhança'), h('div', { id: 'viz-map', class: 'mapa-alvo' }, h('p', { class: 'ajuda' }, 'Desenhando o mapa...')));
  return h('section', { class: 'vizinhanca', 'aria-label': 'Vizinhança do local' }, mapa, h('div', {}, blocoRaio(local, raio1km), lista));
}

function renderBairros(local, pool) {
  const doMun = pool.filter((l) => l._munChave === local._munChave);
  const grupos = new Map();
  for (const l of doMun) {
    const b = l.bairro || '';
    if (!b) continue;
    const g = grupos.get(b) || { bairro: b, n: 0, aptos: 0, flavio: 0, lula: 0, aberto: 0, viraveis: 0 };
    g.n += 1;
    g.aptos += num(l.aptos) || 0;
    g.flavio += num(l.flavio) || 0;
    g.lula += num(l.lula) || 0;
    g.aberto += emAberto(l) || 0;
    if (viravelDo(l) === 'flavio') g.viraveis += 1;
    grupos.set(b, g);
  }
  if (grupos.size < 2) return null;
  const lista = [...grupos.values()].sort((a, b) => b.aberto - a.aberto);
  const meu = local.bairro || '';
  const munPacote = E.locaisMun.get(local._munChave);
  const linha = (g) => h('tr', { class: g.bairro === meu ? 'meu' : null },
    h('th', { scope: 'row' }, h('button', {
      type: 'button',
      class: 'link-bairro',
      onclick: () => munPacote && executar(`Abrindo ${caixa(g.bairro)}`, () => porCidade(munPacote.mun, g.bairro), `Locais de ${caixa(g.bairro)}`),
    }, caixa(g.bairro)), g.bairro === meu ? h('span', { class: 'voce-aqui' }, ' (este)') : null),
    h('td', { class: 'num' }, f0(g.aberto)),
    h('td', { class: 'num' }, f0(g.flavio)),
    h('td', { class: 'num' }, f0(g.lula)),
    h('td', { class: 'num' }, `${g.n}${g.viraveis ? ` (${g.viraveis} ${g.viraveis === 1 ? 'virável' : 'viráveis'})` : ''}`));
  const cab = () => h('thead', {}, h('tr', {}, ['Bairro', 'Em aberto', 'Flávio', 'Lula', 'Locais'].map((t, i) => h('th', { scope: 'col', class: i ? 'num' : null }, t))));
  const topo = lista.slice(0, 10);
  const resto = lista.slice(10);
  return h('section', { class: 'bairros', 'aria-labelledby': 'b-bairros' },
    h('p', { class: 'kicker' }, `${local._mun} por bairro`),
    h('h2', { id: 'b-bairros' }, 'Onde há mais voto em aberto na cidade'),
    h('p', { class: 'ajuda' }, 'Soma dos locais de votação de cada bairro do cadastro do TSE, do maior para o menor número de votos em aberto (outros nomes, branco, nulo e abstenção no 1º turno). Virável: local onde Lula ficou na frente e só branco, nulo e abstenção já virariam para Flávio. Toque no bairro para abrir o boletim.'),
    h('div', { class: 'tabela-rolagem', tabindex: '0', role: 'region', 'aria-label': 'Bairros por votos em aberto' },
      h('table', { class: 'tabela-fontes tabela-bairros' }, cab(), h('tbody', {}, topo.map(linha)))),
    resto.length ? h('details', { class: 'mais-bairros' }, h('summary', {}, `Ver os outros ${resto.length} bairros`),
      h('div', { class: 'tabela-rolagem', tabindex: '0', role: 'region', 'aria-label': 'Demais bairros' },
        h('table', { class: 'tabela-fontes tabela-bairros' }, cab(), h('tbody', {}, resto.map(linha))))) : null);
}

function trocarLocal(l) {
  const r = E.atual || {};
  executar('Abrindo o boletim do local', async () => ({ local: l, pool: r.pool || [], ref: r.origem === 'geo' ? r.ref : null, origem: r.origem === 'geo' ? 'geo' : 'link' }), 'Abrir o local');
}

function linksExternos(l) {
  if (num(l.lat) === null || num(l.lon) === null) return [];
  const la = l.lat;
  const lo = l.lon;
  return [
    [`https://www.openstreetmap.org/?mlat=${la}&mlon=${lo}#map=17/${la}/${lo}`, 'Abrir no OpenStreetMap'],
    [`https://www.google.com/maps?q=${la},${lo}`, 'Abrir no Google Maps'],
  ];
}

async function desenharMapa(box, local, aoRedor, pool, r) {
  const alvo = box.querySelector('#viz-map');
  const comCoord = (l) => num(l.lat) !== null && num(l.lon) !== null;
  if (!comCoord(local)) {
    alvo.replaceChildren(h('p', { class: 'ajuda' }, 'Este local não tem coordenada no cadastro do TSE. Sem mapa; a lista ao lado segue por município.'));
    return;
  }
  const posicao = new Map([[local.local_id, 0], ...aoRedor.map((x, i) => [x.l.local_id, i + 1])]);
  const porId = new Map(pool.map((l) => [l.local_id, l]));
  porId.set(local.local_id, local);
  const links = linksExternos(local);

  if (local._uf === 'ZZ') {
    const cidadePos = new Map([[local._munChave, 0]]);
    const cidadeLocal = new Map();
    aoRedor.forEach((x, i) => {
      if (!cidadePos.has(x.l._munChave)) {
        cidadePos.set(x.l._munChave, i + 1);
        cidadeLocal.set(x.l._munChave, x.l);
      }
    });
    const cidades = E.muns.filter((m) => m.uf === 'ZZ' && comCoord(m));
    const usados = new Set();
    const pontos = cidades.map((m) => {
      const fl = (num(m.flavio_v) || 0) >= (num(m.lula_v) || 0);
      usados.add(fl);
      const n = cidadePos.has(m.chave) ? cidadePos.get(m.chave) : null;
      return {
        id: m.chave, lat: m.lat, lon: m.lon, cor: fl ? '#1f5f9e' : '#c8412f', peso: m.aptos || 0, nome: m.nome, perto: n,
        aria: `${n ? `${n}. ` : ''}${m.nome}: ${f0(m.aptos)} aptos, Flávio ${f1(m.flavio_v)}%, Lula ${f1(m.lula_v)}%`,
      };
    });
    montarMapa(alvo, {
      modo: 'mundo',
      centro: { lat: local.lat, lon: local.lon },
      pontos,
      geo: buscarJSON(`${BASE}geo/ZZ.geojson`).catch(() => null),
      titulo: `Mapa do mundo com as ${cidades.length} cidades onde brasileiros votam no exterior; destaque em ${local._mun}. Azul: Flávio à frente; vermelho: Lula à frente; tamanho pelos aptos.`,
      aoEscolher: (id) => {
        if (cidadeLocal.has(id)) {
          trocarLocal(cidadeLocal.get(id));
          return;
        }
        const m = E.porChave.get(id);
        if (m) executar(`Abrindo ${m.nome}`, () => porCidade(m, ''), `Locais de ${m.nome}`);
      },
      legenda: h('ul', { class: 'mapa-leg' }, h('li', {}, h('i', { style: 'background:#1f5f9e' }), 'Flávio à frente'), h('li', {}, h('i', { style: 'background:#c8412f' }), 'Lula à frente')),
      nota: h('p', { class: 'ajuda' }, `${cidades.length} cidades com seção no exterior. Os números são a posição na lista ao lado; toque numa cidade para abrir o boletim dela. Use + e −, a roda do mouse ou o gesto de pinça para aproximar.`),
      links,
    });
    return;
  }

  const usados = new Map();
  const pontos = pool.filter(comCoord).map((l) => {
    const a = arqInfo(l.arquetipo);
    usados.set(l.arquetipo, a);
    const n = posicao.has(l.local_id) ? posicao.get(l.local_id) : null;
    return {
      id: l.local_id, lat: l.lat, lon: l.lon, cor: a.cor.fill, peso: l.aptos || 0, nome: caixa(l.nome), perto: n,
      aria: `${n ? `${n}. ` : ''}${caixa(l.nome)}, ${a.nome}, índice ${l.indice ?? SD}`,
    };
  });
  if (!posicao.has(local.local_id) || !pontos.some((p) => p.id === local.local_id)) {
    const a = arqInfo(local.arquetipo);
    pontos.push({ id: local.local_id, lat: local.lat, lon: local.lon, cor: a.cor.fill, peso: local.aptos || 0, nome: caixa(local.nome), perto: 0, aria: caixa(local.nome) });
  }
  const grupos = new Map();
  for (const l of pool) {
    if (l._munChave !== local._munChave || !comCoord(l) || !l.bairro) continue;
    const g = grupos.get(l.bairro) || { nome: caixa(l.bairro), lat: 0, lon: 0, ids: [] };
    g.lat += l.lat;
    g.lon += l.lon;
    g.ids.push(l.local_id);
    grupos.set(l.bairro, g);
  }
  const bairros = [...grupos.values()].filter((g) => g.ids.length >= 2).map((g) => ({ ...g, lat: g.lat / g.ids.length, lon: g.lon / g.ids.length }))
    .sort((a, b) => b.ids.length - a.ids.length);
  montarMapa(alvo, {
    modo: 'local',
    centro: { lat: local.lat, lon: local.lon },
    pontos,
    bairros,
    voce: r.origem === 'geo' ? r.ref : null,
    geo: buscarJSON(`${BASE}geo/${local._uf}.geojson`).catch(() => null),
    ibge: local._ibge,
    titulo: `Mapa dos locais de votação perto de ${caixa(local.nome)}, com anéis de 500 metros e 1 quilômetro. Cor pelo arquétipo; os números são a posição na lista ao lado.`,
    aoEscolher: (id) => {
      const l = porId.get(id);
      if (l) trocarLocal(l);
    },
    legenda: h('ul', { class: 'mapa-leg' },
      ORDEM_ARQ.filter((k) => usados.has(k)).map((k) => h('li', {}, h('i', { style: `background:${usados.get(k).cor.fill}` }), usados.get(k).nome)),
      r.origem === 'geo' ? h('li', {}, h('i', { style: 'background:#c8412f' }), 'Você') : null),
    nota: h('p', { class: 'ajuda' }, 'Todos os locais de votação da cidade aparecem como pontos pequenos; os sete mais próximos têm borda e nome (ou o número da lista, quando o nome não cabe). Arraste para mover; use + e −, a roda do mouse ou o gesto de pinça para aproximar. "Ver ruas" baixa o mapa de ruas do OpenStreetMap só quando você pede.'),
    links,
  });
}

/* ------------------------------------------------------------------ compartilhar */

function hashTexto(s) {
  let x = 0;
  for (let i = 0; i < s.length; i += 1) x = (x * 31 + s.charCodeAt(i)) >>> 0;
  return x;
}

function fraseCard(l, vars) {
  const modelos = txa('frases_compartilhar');
  if (!modelos.length) return '';
  const ini = hashTexto(l.local_id || '') % modelos.length;
  for (let i = 0; i < modelos.length; i += 1) {
    const m = modelos[(ini + i) % modelos.length];
    if (m.includes('{faltam}') && !(num(l.faltam) > 0)) continue;
    const f = interp(m, vars);
    if (f && !/\{\w+\}/.test(f) && f.length >= m.replace(/\{\w+\}/g, '').length * 0.6) return f;
  }
  return '';
}

function linkBoletim(l) {
  const u = new URL(location.href);
  u.hash = E.atual && E.atual.local === l ? hashDo(E.atual) : `l=${encodeURIComponent(l.local_id)}`;
  return u.toString();
}

function renderCompartilhar(l, info, vars) {
  const frase = fraseCard(l, vars);
  const canvas = h('canvas', { width: 1080, height: 1080, role: 'img', 'aria-label': `Card de ${caixa(l.nome)}: ${info.nome}, índice de conversa ${l.indice ?? SD} de 100.` });
  const feito = h('p', { class: 'feito', role: 'status', 'aria-live': 'polite' });
  const texto = `${frase ? `${frase} ` : ''}${linkBoletim(l)}`;
  const copiar = async (t, ok) => {
    try {
      await navigator.clipboard.writeText(t);
      feito.textContent = ok;
    } catch {
      const ta = h('textarea', { style: 'position:fixed;left:-9999px', 'aria-hidden': 'true' });
      ta.value = t;
      document.body.append(ta);
      ta.select();
      let deu = false;
      try {
        deu = document.execCommand('copy');
      } catch {
        deu = false;
      }
      ta.remove();
      feito.textContent = deu ? ok : 'Não deu para copiar automaticamente. Selecione o texto acima e copie.';
    }
  };
  const baixar = () => {
    canvas.toBlob((b) => {
      if (!b) {
        feito.textContent = 'O navegador não gerou a imagem. Tente de novo.';
        return;
      }
      const u = URL.createObjectURL(b);
      const a = h('a', { href: u, download: `politize-${norm(caixa(l.nome)).replace(/[^a-z0-9]+/g, '-').slice(0, 40)}.png` });
      document.body.append(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(u), 4000);
      feito.textContent = 'Imagem baixada.';
    }, 'image/png');
  };
  return h('section', { class: 'compartilhar', 'aria-labelledby': 'c-tit' },
    canvas,
    h('div', {},
      h('p', { class: 'kicker' }, 'Compartilhar'),
      h('h2', { id: 'c-tit' }, 'Leve o boletim para a conversa'),
      frase ? h('p', { class: 'texto-card' }, frase) : null,
      h('div', { class: 'acoes' },
        h('button', { type: 'button', class: 'btn btn-amar', onclick: baixar }, 'Baixar imagem (PNG)'),
        h('a', { class: 'btn btn-zap', href: `https://wa.me/?text=${encodeURIComponent(texto)}`, target: '_blank', rel: 'noopener noreferrer' }, 'Mandar para o grupo (WhatsApp)'),
        h('button', { type: 'button', class: 'btn btn-cont', onclick: () => copiar(texto, 'Texto copiado com o link.') }, 'Copiar texto'),
        h('button', { type: 'button', class: 'btn btn-cont', onclick: () => copiar(linkBoletim(l), 'Link copiado.') }, 'Copiar link')),
      feito,
      h('p', { class: 'ajuda', style: 'color:#c9d2da' }, tx('pagina.card_rodape', 'O card mostra só o local e números agregados por seção. O voto é secreto.'))));
}

async function desenharCardDo(comp, l, info, vars) {
  const canvas = comp.querySelector('canvas');
  const cv = conversasDo(l);
  const n = cv.n === null ? null : Math.round(cv.n);
  const numeros = [
    { valor: num(l.flavio_v) === null ? SD : `${nf1.format(l.flavio_v)}%`, rotulo: 'Flávio no 1º turno' },
    { valor: num(l.lula_v) === null ? SD : `${nf1.format(l.lula_v)}%`, rotulo: 'Lula no 1º turno' },
    { valor: n === null ? SD : nf0.format(n), rotulo: cv.modo === 'segurar' ? 'conversas para segurar' : 'conversas para virar' },
  ];
  const lugar = [caixa(l.bairro), `${l._mun}${l._uf && l._uf !== 'ZZ' ? `/${l._uf}` : ''}`].filter(Boolean).join(' · ');
  await desenharCard(canvas, {
    kicker: E.atual && E.atual.secao && E.atual.local === l ? `Boletim da vizinhança · Zona ${E.atual.zona}, seção ${E.atual.secao.secao}` : 'Boletim da vizinhança · 2º turno, 25/10',
    nome: caixa(l.nome),
    lugar,
    arquetipo: info.nome,
    indice: l.indice,
    numeros,
    frase: fraseCard(l, vars),
    rodape: [URL_PUBLICA, 'o voto é secreto: leitura agregada por seção, TSE'],
  });
}

/* ------------------------------------------------------------------ entrada: abas, CEP, cidade, localização */

function configurarAbas() {
  const abas = [...document.querySelectorAll('.abas [role="tab"]')];
  const ativar = (aba, foco = true) => {
    for (const a of abas) {
      const sel = a === aba;
      a.setAttribute('aria-selected', String(sel));
      a.tabIndex = sel ? 0 : -1;
      $(`#${a.getAttribute('aria-controls')}`).hidden = !sel;
    }
    if (foco) aba.focus();
  };
  abas.forEach((a, i) => {
    a.addEventListener('click', () => ativar(a));
    a.addEventListener('keydown', (ev) => {
      let j = null;
      if (ev.key === 'ArrowRight') j = (i + 1) % abas.length;
      else if (ev.key === 'ArrowLeft') j = (i - 1 + abas.length) % abas.length;
      else if (ev.key === 'Home') j = 0;
      else if (ev.key === 'End') j = abas.length - 1;
      if (j !== null) {
        ev.preventDefault();
        ativar(abas[j]);
      }
    });
  });
  if (!('geolocation' in navigator)) {
    $('#btn-geo').disabled = true;
    $('#p-geo .ajuda').textContent = 'Este navegador não oferece localização. Use o CEP ou a cidade.';
  }
}

function configurarSecao() {
  const uf = $('#s-uf');
  const zona = $('#s-zona');
  const sec = $('#s-secao');
  for (const inp of [zona, sec]) {
    inp.addEventListener('input', () => {
      inp.value = inp.value.replace(/\D/g, '').slice(0, 4);
    });
  }
  $('#form-secao').addEventListener('submit', (ev) => {
    ev.preventDefault();
    const u = uf.value;
    const z = Number(zona.value);
    const s = Number(sec.value);
    for (const c of [uf, zona, sec]) c.removeAttribute('aria-invalid');
    const faltando = [[!u, uf, 'o estado'], [!z, zona, 'a zona'], [!s, sec, 'a seção']].filter(([f]) => f);
    if (faltando.length) {
      faltando.forEach(([, c]) => c.setAttribute('aria-invalid', 'true'));
      estadoErro(`Preencha ${faltando.map((x) => x[2]).join(', ')}. Os três números estão no título de eleitor e no e-Título.`, null);
      faltando[0][1].focus();
      return;
    }
    executar(`Procurando a seção ${s} da zona ${z}`, () => porSecao(u, z, s), 'Busca pela seção');
  });
}

function preencherSecao(u, z, s) {
  $('#s-uf').value = u;
  $('#s-zona').value = String(z);
  $('#s-secao').value = String(s);
}

function filtrarUfs() {
  const zonas = E.indice && E.indice.zonas;
  if (!zonas || typeof zonas !== 'object') return;
  for (const o of [...$('#s-uf').options]) {
    if (o.value && !Array.isArray(zonas[o.value])) o.remove();
  }
  const sel = $('#s-uf');
  if (sel.options.length === 2) sel.selectedIndex = 1;
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
      inp.focus();
      return;
    }
    inp.removeAttribute('aria-invalid');
    executar('Procurando locais de votação com esse CEP', () => porCep(d), 'Busca por CEP');
  });
}

function configurarCidade() {
  const inp = $('#cidade');
  const lista = $('#cidade-lista');
  const sel = $('#bairro');
  const btn = $('#btn-cidade');
  let resultados = [];
  let ativo = -1;
  const ufs = new Set(Object.keys(NOME_UF).map((u) => u.toLowerCase()));

  const fechar = () => {
    lista.hidden = true;
    inp.setAttribute('aria-expanded', 'false');
    inp.removeAttribute('aria-activedescendant');
    ativo = -1;
  };
  const marcar = (nome, q) => {
    const n = norm(nome);
    const i = q ? n.indexOf(q) : -1;
    if (i < 0 || n.length !== nome.length) return [nome];
    return [nome.slice(0, i), h('mark', {}, nome.slice(i, i + q.length)), nome.slice(i + q.length)];
  };
  const pintarAtivo = () => {
    [...lista.children].forEach((li, i) => li.setAttribute('aria-selected', String(i === ativo)));
    if (ativo >= 0 && lista.children[ativo]) {
      inp.setAttribute('aria-activedescendant', lista.children[ativo].id);
      lista.children[ativo].scrollIntoView({ block: 'nearest' });
    } else inp.removeAttribute('aria-activedescendant');
  };
  const buscar = () => {
    let q = norm(inp.value);
    E.cidade = null;
    sel.disabled = true;
    btn.disabled = true;
    sel.replaceChildren(h('option', { value: '' }, 'Escolha a cidade primeiro'));
    if (q.length < 2) {
      fechar();
      return;
    }
    let uf = null;
    const partes = q.split(' ');
    if (partes.length > 1 && ufs.has(partes[partes.length - 1])) {
      uf = partes.pop().toUpperCase();
      q = partes.join(' ');
    }
    q = q.replace(/[()]/g, '').trim();
    const pont = [];
    for (const m of E.muns) {
      if (uf && m.uf !== uf) continue;
      let p = -1;
      if (m.busca.startsWith(q)) p = 0;
      else if (m.busca.includes(` ${q}`)) p = 1;
      else if (q.length >= 3 && m.busca.includes(q)) p = 2;
      if (p >= 0) pont.push([p, m]);
    }
    pont.sort((a, b) => a[0] - b[0] || (b[1].aptos || 0) - (a[1].aptos || 0));
    resultados = pont.slice(0, 8).map((x) => x[1]);
    ativo = resultados.length ? 0 : -1;
    lista.replaceChildren(
      ...(resultados.length
        ? resultados.map((m, i) => h('li', { id: `cid-${i}`, role: 'option', 'aria-selected': String(i === ativo), onmousedown: (ev) => { ev.preventDefault(); escolher(m); } },
          h('span', {}, marcar(m.nome, q)), h('span', { class: 'uf', 'aria-label': NOME_UF[m.uf] || m.uf }, m.uf === 'ZZ' ? 'EXT' : m.uf)))
        : [h('li', { role: 'option', 'aria-disabled': 'true', 'aria-selected': 'false', id: 'cid-vazio' }, h('span', { class: 'vazio' }, 'Nenhuma cidade com esse nome'))]),
    );
    lista.hidden = false;
    inp.setAttribute('aria-expanded', 'true');
    pintarAtivo();
  };

  async function escolher(m) {
    fechar();
    inp.value = `${m.nome} (${m.uf === 'ZZ' ? 'Exterior' : m.uf})`;
    E.cidade = m;
    sel.disabled = true;
    sel.replaceChildren(h('option', { value: '' }, 'Carregando bairros...'));
    try {
      const p = await carregarMun(m);
      if (E.cidade !== m) return;
      const cont = new Map();
      for (const l of p.locais) cont.set(l.bairro || '', (cont.get(l.bairro || '') || 0) + 1);
      const bairros = [...cont.entries()].filter(([b]) => b).sort((a, b) => caixa(a[0]).localeCompare(caixa(b[0]), 'pt-BR'));
      sel.replaceChildren(
        h('option', { value: '' }, `Sem bairro: o local mais perto do centro (${f0(p.locais.length)} ${p.locais.length === 1 ? 'local' : 'locais'})`),
        ...bairros.map(([b, n]) => h('option', { value: b }, `${caixa(b)} (${n} ${n === 1 ? 'local' : 'locais'})`)),
      );
      sel.disabled = false;
      btn.disabled = false;
      sel.focus();
    } catch (e) {
      sel.replaceChildren(h('option', { value: '' }, 'Não foi possível carregar os bairros'));
      estadoErro(msgErro(e, `Bairros de ${m.nome}`), () => escolher(m));
    }
  }

  inp.addEventListener('input', buscar);
  inp.addEventListener('focus', () => {
    if (!E.cidade && norm(inp.value).length >= 2) buscar();
  });
  inp.addEventListener('blur', () => setTimeout(fechar, 120));
  inp.addEventListener('keydown', (ev) => {
    const aberto = !lista.hidden;
    if (ev.key === 'ArrowDown') {
      ev.preventDefault();
      if (!aberto) buscar();
      else if (resultados.length) ativo = (ativo + 1) % resultados.length;
      pintarAtivo();
    } else if (ev.key === 'ArrowUp') {
      ev.preventDefault();
      if (resultados.length) ativo = (ativo - 1 + resultados.length) % resultados.length;
      pintarAtivo();
    } else if (ev.key === 'Enter') {
      if (aberto && resultados[ativo]) {
        ev.preventDefault();
        escolher(resultados[ativo]);
      } else if (!E.cidade) ev.preventDefault();
    } else if (ev.key === 'Escape') {
      if (aberto) {
        ev.preventDefault();
        fechar();
      }
    }
  });
  $('#form-cidade').addEventListener('submit', (ev) => {
    ev.preventDefault();
    if (!E.cidade) {
      inp.focus();
      return;
    }
    const m = E.cidade;
    const b = sel.value;
    executar(b ? `Abrindo ${caixa(b)}` : `Abrindo ${m.nome}`, () => porCidade(m, b), `Locais de ${m.nome}`);
  });
}

function configurarGeo() {
  $('#btn-geo').addEventListener('click', () => {
    if (!('geolocation' in navigator)) return;
    estadoCarregando('Pedindo a localização ao aparelho');
    const meu = ++E.pedido;
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        if (meu !== E.pedido) return;
        executar('Procurando os locais de votação perto de você', () => porPosicao(pos), 'Busca pela localização');
      },
      (err) => {
        if (meu !== E.pedido) return;
        const m = {
          1: 'O navegador não liberou a localização. Você pode liberar nas permissões do site ou usar o CEP e a cidade.',
          2: 'O aparelho não conseguiu achar a localização agora. Tente de novo ou use o CEP.',
          3: 'A localização demorou demais para chegar. Tente de novo ou use o CEP.',
        };
        estadoErro(m[err.code] || 'Não foi possível obter a localização.', err.code === 1 ? null : () => $('#btn-geo').click());
      },
      { enableHighAccuracy: false, timeout: 15000, maximumAge: 300000 },
    );
  });
}

function abrirHash() {
  const ms = /(?:^#|&)s=([^&]+)/.exec(location.hash);
  if (ms) {
    let v = '';
    try {
      v = decodeURIComponent(ms[1]);
    } catch {
      return false;
    }
    const p = /^([A-Z]{2})-(\d{1,4})-(\d{1,4})$/.exec(v);
    if (!p) return false;
    const [u, z, s] = [p[1], Number(p[2]), Number(p[3])];
    if (E.atual && E.atual.secao && E.atual.uf === u && E.atual.zona === z && E.atual.secaoDigitada === s) return true;
    preencherSecao(u, z, s);
    executar('Abrindo a seção do link', () => porSecao(u, z, s), 'Abrir o link da seção');
    return true;
  }
  const m = /(?:^#|&)l=([^&]+)/.exec(location.hash);
  if (!m) return false;
  let id;
  try {
    id = decodeURIComponent(m[1]);
  } catch {
    return false;
  }
  if (E.atual && !E.atual.secao && E.atual.local && E.atual.local.local_id === id) return true;
  executar('Abrindo o boletim do link', () => porLocalId(id), 'Abrir o link do boletim');
  return true;
}

/* ------------------------------------------------------------------ início */

async function iniciar() {
  estrelas();
  configurarAbas();
  configurarSecao();
  configurarCep();
  configurarCidade();
  configurarGeo();

  if (location.protocol === 'file:') {
    if (!document.querySelector('#avisos .aviso')) aviso('Esta página lê arquivos de dados e precisa ser aberta por um endereço da web, não direto do disco. Use https://brasil.arvor.co/politizesuavizinhanca.html, ou rode "python3 -m http.server 4173 --directory docs" e abra http://localhost:4173/politizesuavizinhanca.html.', 'Aberta como arquivo local', true);
    for (const b of document.querySelectorAll('.painel button, .painel input, .painel select')) b.disabled = true;
    alvoResultado().replaceChildren();
    return;
  }

  estadoCarregando('Carregando o índice de municípios');
  const textos = (async () => {
    for (const u of TEXTOS_URLS) {
      try {
        return await buscarJSON(u);
      } catch {
        // tenta o próximo caminho
      }
    }
    return null;
  })();
  const [rT, rI] = await Promise.allSettled([textos, buscarJSON(`${BASE}indice.json`)]);
  E.textos = rT.status === 'fulfilled' && rT.value && typeof rT.value === 'object' ? rT.value : {};
  if (!Object.keys(E.textos).length) console.warn('textos.json indisponível: a página segue com os rótulos mínimos.');
  renderPagina();

  if (rI.status !== 'fulfilled') {
    estadoErro(msgErro(rI.reason, 'Índice de municípios'), () => location.reload());
    return;
  }
  prepararIndice(rI.value);
  renderIndiceFixo();
  filtrarUfs();
  if (BASE !== BASE_PADRAO || E.indice.fixture) {
    aviso(`${str(E.indice.aviso, 'Dados de teste.')} Pasta de dados: ${BASE}.`, 'Modo de desenvolvimento');
  }
  renderConversas(null);
  const alvoProp = $('#conversas');
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver((ents) => {
      if (ents.some((e) => e.isIntersecting)) {
        io.disconnect();
        if (!E.atual) renderPropostas(null);
      }
    }, { rootMargin: '400px 0px' });
    io.observe(alvoProp);
  } else {
    renderPropostas(null);
  }
  window.addEventListener('hashchange', abrirHash);
  if (!abrirHash()) estadoVazio();
}

iniciar();
