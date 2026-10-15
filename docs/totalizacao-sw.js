/* Service worker da Totalização paralela.
   Fica na raiz de docs/ para poder controlar /totalizacao.html; o registro em app.js
   limita o escopo a "/totalizacao", então nenhuma outra página do site passa por aqui.
   Página, script, folha e config com rede primeiro e cache de reserva, para nunca misturar
   HTML de uma versão com JS de outra; ícones e manifesto em cache primeiro; decodificador e
   fontes em cache permanente por URL fixa. */

self.window = self; /* config.js grava em window.TOTALIZACAO_CONFIG */
importScripts('assets/totalizacao/config.js');

const VERSAO = (self.TOTALIZACAO_CONFIG && self.TOTALIZACAO_CONFIG.versao) || 'dev';
const CACHE = `totalizacao-${VERSAO}`;
const CACHE_LIBS = 'totalizacao-libs';
const PAGINA_URL = new URL('totalizacao.html', self.location.href).href;
const REDE_PRIMEIRO = [
  'totalizacao.html',
  'assets/totalizacao/app.css',
  'assets/totalizacao/app.js',
  'assets/totalizacao/config.js',
].map((p) => new URL(p, self.location.href).href);
const CASCA = [
  'totalizacao.html',
  'assets/totalizacao/app.css',
  'assets/totalizacao/app.js',
  'assets/totalizacao/config.js',
  'assets/totalizacao/manifest.webmanifest',
  'img/favicon.svg',
  'img/favicon-180.png',
  'img/arvor_logo.png',
].map((p) => new URL(p, self.location.href).href);
const LIBS = [
  'https://cdn.jsdelivr.net/npm/zxing-wasm@3.1.5/',
  'https://fonts.googleapis.com/',
  'https://fonts.gstatic.com/',
];

self.addEventListener('install', (ev) => {
  ev.waitUntil(
    caches.open(CACHE)
      .then((cache) => cache.addAll(CASCA))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener('activate', (ev) => {
  ev.waitUntil(
    caches.keys()
      .then((nomes) => Promise.all(
        nomes
          .filter((n) => n.startsWith('totalizacao-') && n !== CACHE && n !== CACHE_LIBS)
          .map((n) => caches.delete(n)),
      ))
      .then(() => self.clients.claim()),
  );
});

function semBusca(url) {
  return url.origin + url.pathname;
}

async function cascaPrimeiro(ev, chave) {
  const cache = await caches.open(CACHE);
  const guardado = await cache.match(chave);
  const rede = fetch(ev.request)
    .then((resp) => {
      if (resp && resp.ok) cache.put(chave, resp.clone());
      return resp;
    })
    .catch(() => null);
  if (guardado) {
    ev.waitUntil(rede);
    return guardado;
  }
  const resp = await rede;
  if (resp) return resp;
  if (chave === PAGINA_URL) {
    return new Response('<!doctype html><meta charset="utf-8"><title>Sem conexão</title><p>Sem conexão e sem cópia guardada da página. Abra de novo com rede uma vez; depois ela funciona sem rede.</p>', {
      status: 503,
      headers: { 'Content-Type': 'text/html; charset=utf-8' },
    });
  }
  return new Response('', { status: 504, statusText: 'Sem rede' });
}

async function redePrimeiro(ev, chave) {
  const cache = await caches.open(CACHE);
  try {
    const resp = await fetch(ev.request, { cache: 'no-cache' });
    if (resp && resp.ok) await cache.put(chave, resp.clone());
    return resp;
  } catch (erro) {
    const guardado = await cache.match(chave);
    if (guardado) return guardado;
    throw erro;
  }
}

async function libCachePrimeiro(ev) {
  const cache = await caches.open(CACHE_LIBS);
  const guardado = await cache.match(ev.request.url);
  if (guardado) return guardado;
  const resp = await fetch(ev.request);
  if (resp && resp.ok) await cache.put(ev.request.url, resp.clone());
  return resp;
}

self.addEventListener('fetch', (ev) => {
  const req = ev.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  const chave = semBusca(url);
  if (REDE_PRIMEIRO.includes(chave)) {
    ev.respondWith(redePrimeiro(ev, chave).catch(() => cascaPrimeiro(ev, chave)));
    return;
  }
  if (CASCA.includes(chave)) {
    ev.respondWith(cascaPrimeiro(ev, chave));
    return;
  }
  if (LIBS.some((prefixo) => req.url.startsWith(prefixo))) {
    ev.respondWith(libCachePrimeiro(ev));
  }
});
