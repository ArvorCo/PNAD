// Mapa da vizinhança do Politize. Escrito à mão, sem biblioteca e sem tile por padrão.
//
// Tudo é SVG na projeção Web Mercator (a mesma dos tiles), em "pixels do zoom Z" relativos ao local do
// boletim. Camadas, de baixo para cima: tiles de ruas (só depois do clique em "Ver ruas"), contorno dos
// municípios, anéis de 500 m e 1 km, todos os locais carregados (discretos), os oito do "ao redor"
// (com borda e rótulo), seleção, você, nomes de bairro e rótulos. Zoom e arrasto mudam só o viewBox,
// no padrão do mapa dos fiscais (scripts/apuracao_2026/pagina_fig_fiscais_nav.py); raio de ponto,
// fonte e borda são recalculados para ficarem do mesmo tamanho na tela em qualquer zoom.

const NS = 'http://www.w3.org/2000/svg';
const RUAS_CHAVE = 'politize-ruas';
const RUAS_ATRIB = '© colaboradores do OpenStreetMap, estilo Humanitarian OSM Team, servido por OSM France';
const MAX_TILES = 72;

function s(tag, attrs = {}) {
  const n = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) if (v !== null && v !== undefined) n.setAttribute(k, String(v));
  return n;
}
function el(tag, attrs = {}, ...filhos) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined || v === false) continue;
    if (k === 'class') n.className = v;
    else if (k.startsWith('on') && typeof v === 'function') n.addEventListener(k.slice(2), v);
    else n.setAttribute(k, v === true ? '' : String(v));
  }
  for (const f of filhos.flat()) if (f !== null && f !== undefined && f !== false) n.append(f instanceof Node ? f : document.createTextNode(String(f)));
  return n;
}

function projecao(z, lon0, lat0) {
  const T = 256 * 2 ** z;
  const mx = (lon) => ((lon + 180) / 360) * T;
  const my = (lat) => {
    const sn = Math.sin((Math.max(-85, Math.min(85, lat)) * Math.PI) / 180);
    return (0.5 - Math.log((1 + sn) / (1 - sn)) / (4 * Math.PI)) * T;
  };
  const x0 = mx(lon0);
  const y0 = my(lat0);
  return {
    z, T, x0, y0,
    X: (lon) => mx(lon) - x0,
    Y: (lat) => my(lat) - y0,
    porMetro: T / (40075016.686 * Math.cos((lat0 * Math.PI) / 180)),
  };
}

const temCoord = (o) => typeof o.lat === 'number' && typeof o.lon === 'number' && Number.isFinite(o.lat) && Number.isFinite(o.lon);
const curto = (t, n = 28) => (t.length > n ? `${t.slice(0, n - 1).trimEnd()}…` : t);
const sobrepoe = (a, b) => a[0] < b[2] && b[0] < a[2] && a[1] < b[3] && b[1] < a[3];

function ruasLigadas() {
  try {
    return localStorage.getItem(RUAS_CHAVE) === '1';
  } catch {
    return false;
  }
}
function gravarRuas(v) {
  try {
    localStorage.setItem(RUAS_CHAVE, v ? '1' : '0');
  } catch {
    // Sem armazenamento, a preferência vale só nesta visita.
  }
}

function aneisDe(geom) {
  if (!geom) return [];
  if (geom.type === 'Polygon') return geom.coordinates;
  if (geom.type === 'MultiPolygon') return geom.coordinates.flat();
  return [];
}

/** Contornos que cruzam a caixa [lon0, lat0, lon1, lat1]; `destaque` = código IBGE do município do boletim. */
function contornos(P, features, caixa, destaque, casas) {
  const g = s('g', { class: 'mp-mun' });
  const meus = [];
  for (const f of features || []) {
    const aneis = aneisDe(f.geometry);
    let a = Infinity;
    let b = Infinity;
    let c = -Infinity;
    let d = -Infinity;
    for (const anel of aneis) {
      for (const [lo, la] of anel) {
        if (lo < a) a = lo;
        if (lo > c) c = lo;
        if (la < b) b = la;
        if (la > d) d = la;
      }
    }
    if (caixa && (c < caixa[0] || a > caixa[2] || d < caixa[1] || b > caixa[3])) continue;
    let path = '';
    for (const anel of aneis) {
      path += `${anel.map(([lo, la], i) => `${i ? 'L' : 'M'}${P.X(lo).toFixed(casas)} ${P.Y(la).toFixed(casas)}`).join('')}Z`;
    }
    if (!path) continue;
    const cod = String((f.properties && (f.properties.codarea ?? f.properties.CD_MUN)) || '');
    const p = s('path', { d: path, class: destaque && cod === destaque ? 'mun' : 'mun outro', 'fill-rule': 'evenodd' });
    if (destaque && cod === destaque) meus.push(p);
    else g.append(p);
  }
  for (const p of meus) g.append(p);
  return g;
}

/** Zoom, arrasto, pinça e teclado sobre o viewBox; `aoMudar(u)` recebe unidades de mapa por pixel de tela. */
function navegacao(svg, vb0, aoMudar, aoTocar) {
  let vb = { ...vb0 };
  const W0 = vb0.w;
  const zoom = () => W0 / vb.w;
  const unidade = () => {
    const r = svg.getBoundingClientRect();
    return r.width && r.height ? Math.max(vb.w / r.width, vb.h / r.height) : vb.w / 600;
  };
  let pend = false;
  const agenda = () => {
    if (pend) return;
    pend = true;
    requestAnimationFrame(() => {
      pend = false;
      aoMudar(unidade(), vb);
    });
  };
  const aplica = () => {
    svg.setAttribute('viewBox', `${vb.x.toFixed(2)} ${vb.y.toFixed(2)} ${vb.w.toFixed(2)} ${vb.h.toFixed(2)}`);
    agenda();
  };
  const ponto = (cx, cy) => {
    const m = svg.getScreenCTM();
    if (!m) return null;
    const p = svg.createSVGPoint();
    p.x = cx;
    p.y = cy;
    return p.matrixTransform(m.inverse());
  };
  const zoomEm = (f, cx, cy) => {
    const k = Math.max(0.25, Math.min(24, zoom() * f));
    const nw = W0 / k;
    const nh = (vb0.h / vb0.w) * nw;
    const p = cx === undefined ? { x: vb.x + vb.w / 2, y: vb.y + vb.h / 2 } : ponto(cx, cy);
    if (!p) return;
    const rx = (p.x - vb.x) / vb.w;
    const ry = (p.y - vb.y) / vb.h;
    vb = { x: p.x - rx * nw, y: p.y - ry * nh, w: nw, h: nh };
    aplica();
  };
  const centrar = () => {
    vb = { ...vb0 };
    aplica();
  };
  svg.addEventListener('wheel', (ev) => {
    ev.preventDefault();
    zoomEm(Math.exp(-ev.deltaY * (ev.deltaMode === 1 ? 0.05 : 0.0022)), ev.clientX, ev.clientY);
  }, { passive: false });
  const toques = new Map();
  let arr = null;
  let moveu = false;
  let dist0 = 0;
  let k0 = 1;
  svg.addEventListener('pointerdown', (ev) => {
    toques.set(ev.pointerId, { x: ev.clientX, y: ev.clientY });
    if (toques.size === 1) {
      arr = { x: ev.clientX, y: ev.clientY, vx: vb.x, vy: vb.y };
      moveu = false;
    } else if (toques.size === 2) {
      const [a, b] = [...toques.values()];
      dist0 = Math.hypot(a.x - b.x, a.y - b.y);
      k0 = zoom();
      arr = null;
      moveu = true;
    }
  });
  svg.addEventListener('pointermove', (ev) => {
    if (!toques.has(ev.pointerId)) return;
    toques.set(ev.pointerId, { x: ev.clientX, y: ev.clientY });
    if (toques.size === 2 && dist0 > 0) {
      const [a, b] = [...toques.values()];
      zoomEm((k0 * Math.hypot(a.x - b.x, a.y - b.y)) / dist0 / zoom(), (a.x + b.x) / 2, (a.y + b.y) / 2);
      return;
    }
    if (!arr) return;
    const dx = ev.clientX - arr.x;
    const dy = ev.clientY - arr.y;
    if (!moveu && Math.abs(dx) + Math.abs(dy) < 6) return;
    if (!moveu) {
      try {
        svg.setPointerCapture(ev.pointerId);
      } catch {
        // captura opcional
      }
    }
    moveu = true;
    svg.classList.add('arrasta');
    const u = unidade();
    vb.x = arr.vx - dx * u;
    vb.y = arr.vy - dy * u;
    aplica();
  });
  const solta = (ev) => {
    const tocou = arr && !moveu && ev.type === 'pointerup';
    toques.delete(ev.pointerId);
    if (!toques.size) {
      svg.classList.remove('arrasta');
      arr = null;
      dist0 = 0;
    }
    if (tocou && aoTocar) aoTocar(ev);
  };
  svg.addEventListener('pointerup', solta);
  svg.addEventListener('pointercancel', solta);
  svg.addEventListener('dblclick', (ev) => {
    ev.preventDefault();
    zoomEm(2, ev.clientX, ev.clientY);
  });
  svg.addEventListener('keydown', (ev) => {
    if (ev.target !== svg) return;
    const f = { '+': 2, '=': 2, '-': 0.5, _: 0.5 }[ev.key];
    if (f) {
      zoomEm(f);
      ev.preventDefault();
      return;
    }
    if (ev.key === '0') {
      centrar();
      ev.preventDefault();
      return;
    }
    const d = vb.w * 0.15;
    const mv = { ArrowLeft: [-d, 0], ArrowRight: [d, 0], ArrowUp: [0, -d], ArrowDown: [0, d] }[ev.key];
    if (mv) {
      vb.x += mv[0];
      vb.y += mv[1];
      aplica();
      ev.preventDefault();
    }
  });
  window.addEventListener('resize', agenda);
  aplica();
  return { zoomEm, centrar, atualizar: agenda };
}

function escalaBonita(metros) {
  const passos = [10, 20, 50, 100, 200, 250, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000, 500000, 1000000];
  let m = passos[0];
  for (const p of passos) if (p <= metros) m = p;
  return m;
}
const txtMetros = (m) => (m < 1000 ? `${m} m` : `${(m / 1000).toLocaleString('pt-BR')} km`);

/**
 * Monta o mapa no `alvo`.
 * @param {object} o
 *   modo: 'local' | 'mundo'
 *   centro: {lat, lon}            ponto do boletim (origem da projeção)
 *   destaque: objeto do boletim   (local ou cidade), entra em `pontos`
 *   pontos: [{id, lat, lon, cor, peso, nome, perto (número 0..7 ou null), rotulo, aria}]
 *   bairros: [{nome, lat, lon, ids: [id]}]   (só no modo local)
 *   voce: {lat, lon} | null
 *   geo: Promise<FeatureCollection> | null; ibge: código do município do boletim
 *   aoEscolher(id)
 *   titulo: texto alternativo
 */
export function montarMapa(alvo, o) {
  const local = o.modo !== 'mundo';
  const P = projecao(local ? 18 : 8, o.centro.lon, o.centro.lat);
  const pts = o.pontos.filter(temCoord).map((p) => ({ ...p, x: P.X(p.lon), y: P.Y(p.lat) }));
  const perto = pts.filter((p) => p.perto !== null && p.perto !== undefined);

  // quadro inicial: no local, centrado no boletim com os oito e os anéis de 1 km dentro; no mundo, o planisfério
  let vb0;
  if (local) {
    const extra = o.voce && temCoord(o.voce) ? [{ x: P.X(o.voce.lon), y: P.Y(o.voce.lat) }] : [];
    const alcance = Math.max(...[...perto, ...extra].map((p) => Math.max(Math.abs(p.x), Math.abs(p.y))), 0);
    const meio = Math.max(alcance * 1.18, 1150 * P.porMetro);
    vb0 = { x: -meio, y: -meio, w: 2 * meio, h: 2 * meio };
  } else {
    const xa = P.X(-170);
    const xb = P.X(190);
    const ya = P.Y(78);
    const yb = P.Y(-56);
    vb0 = { x: xa, y: ya, w: xb - xa, h: yb - ya };
  }

  const svg = s('svg', { class: `mapa-svg${local ? '' : ' mundo'}`, role: 'group', 'aria-labelledby': 'mapa-t', tabindex: '0', preserveAspectRatio: 'xMidYMid meet', viewBox: `${vb0.x} ${vb0.y} ${vb0.w} ${vb0.h}` });
  const t = s('title', { id: 'mapa-t' });
  t.textContent = o.titulo || 'Mapa';
  svg.append(t);
  const gTiles = s('g', { class: 'mp-tiles' });
  const gMun = s('g');
  const gAneis = s('g', { class: 'mp-aneis' });
  const gCtx = s('g', { class: 'mp-ctx' });
  const gPerto = s('g', { class: 'mp-perto' });
  const gSel = s('g');
  const gBairro = s('g', { class: 'mp-bairro' });
  const gRot = s('g', { class: 'mp-rot' });
  svg.append(gTiles, gMun, gAneis, gCtx, gPerto, gSel, gBairro, gRot);

  // contornos (assíncrono)
  if (o.geo) {
    const lons = pts.map((p) => p.lon);
    const lats = pts.map((p) => p.lat);
    const caixa = local ? [Math.min(...lons) - 0.3, Math.min(...lats) - 0.3, Math.max(...lons) + 0.3, Math.max(...lats) + 0.3] : null;
    o.geo.then((geo) => {
      if (geo) gMun.append(contornos(P, geo.features, caixa, o.ibge, local ? 1 : 0));
    }).catch(() => {});
  }

  // anéis
  const aneis = [];
  if (local) {
    for (const m of [500, 1000]) {
      const r = m * P.porMetro;
      gAneis.append(s('circle', { cx: 0, cy: 0, r: r.toFixed(1), class: 'raio' }));
      const tx = s('text', { x: 0, y: -r, 'text-anchor': 'middle', class: 'raio-t' });
      tx.textContent = txtMetros(m);
      gAneis.append(tx);
      aneis.push({ r, tx });
    }
  }

  // pontos: contexto (todos) e os oito
  const maxPeso = Math.max(1, ...pts.map((p) => p.peso || 0));
  const circ = new Map();
  for (const p of pts) {
    const ehPerto = p.perto !== null && p.perto !== undefined;
    const c = s('circle', { cx: p.x.toFixed(1), cy: p.y.toFixed(1), fill: p.cor, class: ehPerto ? 'pt perto' : 'pt ctx', 'data-id': p.id });
    const tt = s('title');
    tt.textContent = p.aria || p.nome;
    c.append(tt);
    if (ehPerto && p.perto > 0) {
      c.setAttribute('tabindex', '0');
      c.setAttribute('role', 'button');
      c.setAttribute('aria-label', p.aria || p.nome);
      c.addEventListener('keydown', (ev) => {
        if (ev.key === 'Enter' || ev.key === ' ') {
          ev.preventDefault();
          o.aoEscolher(p.id);
        }
      });
    }
    (ehPerto ? gPerto : gCtx).append(c);
    circ.set(p.id, { c, p, ehPerto });
  }
  const sel = perto.find((p) => p.perto === 0);
  const anel = sel ? s('circle', { cx: sel.x.toFixed(1), cy: sel.y.toFixed(1), class: 'sel' }) : null;
  if (anel) gSel.append(anel);
  if (sel && circ.get(sel.id)) gSel.append(circ.get(sel.id).c);
  let voce = null;
  if (o.voce && temCoord(o.voce)) {
    voce = s('circle', { cx: P.X(o.voce.lon).toFixed(1), cy: P.Y(o.voce.lat).toFixed(1), class: 'voce' });
    const tv = s('title');
    tv.textContent = 'Você (a coordenada não sai do aparelho)';
    voce.append(tv);
    gSel.append(voce);
  }
  const bairros = (o.bairros || []).filter(temCoord).map((b) => ({ ...b, x: P.X(b.lon), y: P.Y(b.lat), pts: b.ids.map((id) => circ.get(id)).filter(Boolean).map((x) => x.p) }));

  // moldura HTML: botões, escala, norte, atribuição
  const caixaMapa = el('div', { class: 'mp' });
  const escala = el('div', { class: 'mp-escala', 'aria-hidden': 'true' }, el('span', { class: 'mp-barra' }), el('span', { class: 'mp-escala-t' }));
  const norte = el('div', { class: 'mp-norte', 'aria-hidden': 'true' }, 'N');
  const atrib = el('div', { class: 'mp-atrib', hidden: true }, RUAS_ATRIB);
  const aviso = el('p', { class: 'mp-aviso', role: 'status' });
  let nav = null;
  const botoes = el('div', { class: 'mp-zoom' },
    el('button', { type: 'button', class: 'mp-btn', 'aria-label': 'Aproximar', onclick: () => nav.zoomEm(2) }, '+'),
    el('button', { type: 'button', class: 'mp-btn', 'aria-label': 'Afastar', onclick: () => nav.zoomEm(0.5) }, '−'),
    el('button', { type: 'button', class: 'mp-btn mp-btn-t', onclick: () => nav.centrar() }, 'Centrar'));
  let ruas = false;
  const btnRuas = local ? el('button', { type: 'button', class: 'mp-btn mp-ruas', 'aria-pressed': 'false' }, 'Ver ruas') : null;
  caixaMapa.append(svg, botoes, norte);
  if (local) caixaMapa.append(escala, btnRuas, atrib);

  const tiles = new Map();
  let errosTile = 0;
  function atualizarTiles(u, vb) {
    if (!ruas) return;
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    let z = Math.ceil(P.z - Math.log2(Math.max(u / dpr, 1e-6)) - 0.15);
    z = Math.max(3, Math.min(18, z));
    let lado;
    let tx0;
    let tx1;
    let ty0;
    let ty1;
    for (;;) {
      lado = 256 * 2 ** (P.z - z);
      tx0 = Math.floor((vb.x + P.x0) / lado);
      tx1 = Math.floor((vb.x + vb.w + P.x0) / lado);
      ty0 = Math.floor((vb.y + P.y0) / lado);
      ty1 = Math.floor((vb.y + vb.h + P.y0) / lado);
      if ((tx1 - tx0 + 1) * (ty1 - ty0 + 1) <= MAX_TILES || z <= 3) break;
      z -= 1;
    }
    const n = 2 ** z;
    const quer = new Set();
    for (let tx = tx0; tx <= tx1; tx += 1) {
      for (let ty = Math.max(0, ty0); ty <= Math.min(n - 1, ty1); ty += 1) {
        const xw = ((tx % n) + n) % n;
        const k = `${z}/${xw}/${ty}/${tx}`;
        quer.add(k);
        if (tiles.has(k)) continue;
        const img = s('image', {
          x: (tx * lado - P.x0).toFixed(1), y: (ty * lado - P.y0).toFixed(1), width: lado.toFixed(1), height: lado.toFixed(1),
          preserveAspectRatio: 'none', href: `https://${'abc'[(xw + ty) % 3]}.tile.openstreetmap.fr/hot/${z}/${xw}/${ty}.png`,
        });
        img.addEventListener('error', () => {
          errosTile += 1;
          if (errosTile === 4) aviso.textContent = 'As ruas não carregaram (sem rede ou servidor de mapas fora do ar). O mapa segue sem elas.';
        });
        tiles.set(k, img);
        gTiles.append(img);
      }
    }
    for (const [k, img] of tiles) {
      if (!quer.has(k)) {
        img.remove();
        tiles.delete(k);
      }
    }
  }
  function ligarRuas(v) {
    if (v && (location.protocol === 'file:' || navigator.onLine === false)) {
      aviso.textContent = 'Sem conexão: as ruas vêm de um servidor de mapas e não carregam agora. O mapa segue sem elas.';
      v = false;
    }
    ruas = v;
    svg.classList.toggle('com-ruas', v);
    if (btnRuas) {
      btnRuas.setAttribute('aria-pressed', String(v));
      btnRuas.textContent = v ? 'Tirar ruas' : 'Ver ruas';
    }
    atrib.hidden = !v;
    if (!v) {
      for (const img of tiles.values()) img.remove();
      tiles.clear();
    } else {
      aviso.textContent = '';
    }
    nav.atualizar();
  }
  if (btnRuas) {
    btnRuas.addEventListener('click', () => {
      const v = !ruas;
      gravarRuas(v);
      ligarRuas(v);
    });
  }

  function redesenhar(u, vb) {
    // pontos
    for (const { c, p, ehPerto } of circ.values()) {
      const base = local ? (ehPerto ? 6 : 3.2) : Math.max(ehPerto ? 5 : 0, 1.6 + 5.4 * Math.sqrt((p.peso || 0) / maxPeso));
      const extra = local && ehPerto ? 3.2 * Math.sqrt((p.peso || 0) / maxPeso) : 0;
      c.setAttribute('r', ((base + extra + (p.perto === 0 ? 2 : 0)) * u).toFixed(2));
    }
    if (anel && sel) anel.setAttribute('r', (15 * u).toFixed(2));
    if (voce) voce.setAttribute('r', (6 * u).toFixed(2));
    for (const a of aneis) {
      // anel pequeno demais na tela (quadro de vários km) fica sem rótulo, para não brigar com os pontos
      if (a.r / u < 46) a.tx.setAttribute('display', 'none');
      else a.tx.removeAttribute('display');
      a.tx.setAttribute('font-size', (12 * u).toFixed(2));
      a.tx.setAttribute('stroke-width', (3.5 * u).toFixed(2));
      a.tx.setAttribute('y', (-a.r - 4 * u).toFixed(2));
    }
    // rótulos dos oito: nome curto com fundo; se colidir, só o número
    while (gRot.firstChild) gRot.firstChild.remove();
    const ocup = [];
    for (const p of perto) {
      const r = 9 * u;
      ocup.push([p.x - r, p.y - r, p.x + r, p.y + r]);
    }
    // áreas cobertas pelos botões, escala, norte e atribuição (em pixels de tela, convertidos)
    const R = vb.x + vb.w;
    const B = vb.y + vb.h;
    if (local) {
      ocup.push([R - 64 * u, vb.y, R, vb.y + 172 * u], [vb.x, vb.y, vb.x + 132 * u, vb.y + 60 * u], [vb.x, B - 96 * u, vb.x + 160 * u, B]);
      if (ruas) ocup.push([vb.x + vb.w * 0.28, B - 44 * u, R, B]);
    } else {
      ocup.push([R - 64 * u, vb.y, R, vb.y + 172 * u], [vb.x, B - 60 * u, vb.x + 48 * u, B]);
    }
    const fs = 12.5 * u;
    const pad = 4 * u;
    const ordem = [...perto].sort((a, b) => a.perto - b.perto);
    for (const p of ordem) {
      if (p.x < vb.x || p.x > vb.x + vb.w || p.y < vb.y || p.y > vb.y + vb.h) continue;
      const texto = curto(p.rotulo || p.nome);
      const w = texto.length * fs * 0.49 + 2 * pad;
      const hh = fs + 2 * pad;
      const d = 11 * u;
      const opcoes = [
        [p.x + d, p.y - hh / 2], [p.x - d - w, p.y - hh / 2], [p.x - w / 2, p.y - d - hh], [p.x - w / 2, p.y + d],
      ];
      let pos = null;
      for (const [x, y] of opcoes) {
        const caixa = [x, y, x + w, y + hh];
        if (caixa[0] < vb.x || caixa[2] > vb.x + vb.w || caixa[1] < vb.y || caixa[3] > vb.y + vb.h) continue;
        if (ocup.some((o2) => sobrepoe(caixa, o2) && !(o2[0] <= p.x && o2[2] >= p.x && o2[1] <= p.y && o2[3] >= p.y))) continue;
        pos = caixa;
        break;
      }
      let rotTxt = texto;
      if (!pos && p.perto === 0) {
        // o local do boletim sempre leva o nome: primeira posição livre de borda, mesmo com sobreposição
        const [x, y] = opcoes.find(([x1, y1]) => x1 >= vb.x && x1 + w <= vb.x + vb.w && y1 >= vb.y && y1 + hh <= vb.y + vb.h) || opcoes[0];
        pos = [x, y, x + w, y + hh];
      }
      if (!pos) {
        rotTxt = String(p.perto);
        const wn = rotTxt.length * fs * 0.62 + 2 * pad;
        pos = [p.x + d * 0.7, p.y - d * 0.7 - hh, p.x + d * 0.7 + wn, p.y - d * 0.7];
      }
      ocup.push(pos);
      gRot.append(
        s('rect', { x: pos[0].toFixed(2), y: pos[1].toFixed(2), width: (pos[2] - pos[0]).toFixed(2), height: (pos[3] - pos[1]).toFixed(2), rx: (3 * u).toFixed(2), class: p.perto === 0 ? 'rot-fundo meu' : 'rot-fundo' }),
      );
      const tx = s('text', { x: (pos[0] + pad).toFixed(2), y: (pos[3] - pad - fs * 0.18).toFixed(2), 'font-size': fs.toFixed(2), class: p.perto === 0 ? 'mp-r meu' : 'mp-r' });
      tx.textContent = rotTxt;
      gRot.append(tx);
    }
    // nomes de bairro: centroide, só com dois ou mais locais dentro do quadro
    while (gBairro.firstChild) gBairro.firstChild.remove();
    const fb = 10.5 * u;
    let n = 0;
    for (const b of bairros) {
      if (n >= 30) break;
      const dentro = b.pts.filter((p) => p.x >= vb.x && p.x <= vb.x + vb.w && p.y >= vb.y && p.y <= vb.y + vb.h).length;
      if (dentro < 2) continue;
      const texto = curto(b.nome.toLocaleUpperCase('pt-BR'), 24);
      const w = texto.length * fb * 0.72;
      const caixa = [b.x - w / 2, b.y - fb, b.x + w / 2, b.y + fb * 0.3];
      if (caixa[0] < vb.x || caixa[2] > vb.x + vb.w || caixa[1] < vb.y || caixa[3] > vb.y + vb.h) continue;
      if (ocup.some((o2) => sobrepoe(caixa, o2))) continue;
      ocup.push(caixa);
      const tx = s('text', { x: b.x.toFixed(2), y: b.y.toFixed(2), 'text-anchor': 'middle', 'font-size': fb.toFixed(2), 'stroke-width': (3 * u).toFixed(2), 'letter-spacing': (1.2 * u).toFixed(2), class: 'bairro-t' });
      tx.textContent = texto;
      gBairro.append(tx);
      n += 1;
    }
    // escala
    if (local) {
      const mPorPx = u / P.porMetro;
      const m = escalaBonita(mPorPx * 110);
      escala.querySelector('.mp-barra').style.width = `${Math.round(m / mPorPx)}px`;
      escala.querySelector('.mp-escala-t').textContent = txtMetros(m);
    }
    atualizarTiles(u, vb);
  }

  const aoTocar = (ev) => {
    const alvoEl = document.elementFromPoint(ev.clientX, ev.clientY);
    const id = alvoEl && alvoEl.getAttribute && alvoEl.getAttribute('data-id');
    if (id && (!sel || id !== sel.id)) o.aoEscolher(id);
  };

  const links = o.links || [];
  alvo.replaceChildren(caixaMapa, aviso, o.legenda || '', o.nota || '',
    links.length ? el('p', { class: 'mp-links' }, links.map(([href, texto]) => el('a', { href, target: '_blank', rel: 'noopener noreferrer' }, texto))) : '');
  nav = navegacao(svg, vb0, redesenhar, aoTocar);
  if (local && ruasLigadas()) ligarRuas(true);
  return nav;
}
