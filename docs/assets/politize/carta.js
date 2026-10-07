// Carta radial do boletim (o "mapa astral" do local de votação).
// Escrito à mão. Recebe números já lidos dos JSON; não calcula métrica nenhuma.
//
// Anatomia, de fora para dentro:
//   anel externo  = composição dos aptos do local no 1º turno (Flávio, Lula, outros nomes,
//                   branco e nulo, abstenção), em % dos aptos;
//   régua         = 40 marcas, uma por voto em 100 aptos até o teto do índice;
//   quatro setores = componentes do potencial (c_terceira, c_ausentes, c_reencontro, c_perfil),
//                   raio proporcional à raiz do valor, escala até metade do teto;
//   disco central = índice de conversa (0 a 100), com a faixa branca da bandeira.

const NS = 'http://www.w3.org/2000/svg';

export const CORES = {
  flavio: '#1f5f9e',
  lula: '#c8412f',
  terceira: '#0b7a3b',
  bn: '#e0b52a',
  abst: '#cfcabb',
  c_terceira: '#0b7a3b',
  c_ausentes: '#f2c230',
  c_reencontro: '#1f5f9e',
  c_perfil: '#7fa7cf',
  azul: '#0d2238',
};

function el(tag, attrs = {}, ...filhos) {
  const n = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v !== null && v !== undefined && v !== false) n.setAttribute(k, String(v));
  }
  for (const f of filhos) {
    if (f === null || f === undefined) continue;
    n.append(typeof f === 'string' ? document.createTextNode(f) : f);
  }
  return n;
}

const rad = (g) => ((g - 90) * Math.PI) / 180;
const ponto = (c, r, g) => [c + r * Math.cos(rad(g)), c + r * Math.sin(rad(g))];

function arco(c, r0, r1, g0, g1) {
  const grande = g1 - g0 > 180 ? 1 : 0;
  const [ax, ay] = ponto(c, r1, g0);
  const [bx, by] = ponto(c, r1, g1);
  const [cx, cy] = ponto(c, r0, g1);
  const [dx, dy] = ponto(c, r0, g0);
  const f = (x) => x.toFixed(2);
  return `M${f(ax)} ${f(ay)}A${r1} ${r1} 0 ${grande} 1 ${f(bx)} ${f(by)}L${f(cx)} ${f(cy)}A${r0} ${r0} 0 ${grande} 0 ${f(dx)} ${f(dy)}Z`;
}

let serial = 0;

/**
 * @param {object} o
 * @param {object} o.local   linha do local (objeto com as colunas do contrato)
 * @param {number} o.teto    teto do potencial (indice.parametros.teto_potencial)
 * @param {object} o.rotulos rótulos dos componentes {c_terceira: 'Votaram em outros nomes', ...}
 * @param {function} o.fmt   formatador de número com vírgula (1 casa)
 * @param {string} o.arquetipo nome do arquétipo, para o texto alternativo
 */
export function carta({ local, teto = 40, rotulos = {}, fmt, arquetipo = '' }) {
  const id = `carta-${++serial}`;
  const C = 210;
  const num = (v) => (typeof v === 'number' && Number.isFinite(v) ? v : null);
  const f1 = fmt || ((v) => String(v));

  const comps = ['c_terceira', 'c_ausentes', 'c_reencontro', 'c_perfil'];
  const anel = [
    ['flavio', num(local.flavio_a), 'Flávio'],
    ['lula', num(local.lula_a), 'Lula'],
    ['terceira', num(local.terceira_a), 'outros nomes'],
    ['bn', num(local.bn_a), 'branco e nulo'],
    ['abst', num(local.abst_a), 'abstenção'],
  ];

  const partes = [];
  for (const [k, v, nome] of anel) if (v !== null) partes.push(`${nome} ${f1(v)}`);
  const desc = [
    `Índice de conversa ${local.indice ?? 'sem dado'} de 100${arquetipo ? `, arquétipo ${arquetipo}` : ''}.`,
    comps
      .filter((k) => num(local[k]) !== null)
      .map((k) => `${rotulos[k] || k}: ${f1(local[k])} por 100 aptos`)
      .join('; ') + '.',
    partes.length ? `Composição dos aptos no 1º turno, em %: ${partes.join(', ')}.` : '',
  ].join(' ');

  const svg = el('svg', {
    viewBox: '0 0 420 420',
    class: 'carta-svg',
    role: 'img',
    'aria-labelledby': `${id}-t ${id}-d`,
    xmlns: NS,
  });
  svg.append(el('title', { id: `${id}-t` }, 'Carta da vizinhança'), el('desc', { id: `${id}-d` }, desc));

  const defs = el('defs');
  defs.append(el('clipPath', { id: `${id}-disco` }, el('circle', { cx: C, cy: C, r: 62 })));
  defs.append(
    el('path', { id: `${id}-faixa`, d: `M${C - 64} ${C + 22} Q ${C} ${C + 4} ${C + 64} ${C + 22}` }),
  );
  const hach = el('pattern', { id: `${id}-hach`, width: 6, height: 6, patternUnits: 'userSpaceOnUse', patternTransform: 'rotate(45)' });
  hach.append(el('rect', { width: 6, height: 6, fill: CORES.abst }), el('line', { x1: 0, y1: 0, x2: 0, y2: 6, stroke: '#b3ad9b', 'stroke-width': 2 }));
  defs.append(hach);
  svg.append(defs);

  // fundo
  svg.append(el('circle', { cx: C, cy: C, r: 205, fill: '#fbfaf5', stroke: '#d5d2c6' }));

  // anel externo: composição dos aptos
  const soma = anel.reduce((s, [, v]) => s + (v || 0), 0);
  if (soma > 0) {
    let g = 0;
    const gAnel = el('g', { class: 'carta-anel' });
    for (const [k, v] of anel) {
      if (!v) continue;
      const span = (360 * v) / soma;
      const g1 = g + span;
      if (span > 0.8) {
        gAnel.append(el('path', { d: arco(C, 180, 198, g + 0.35, g1 - 0.35), fill: k === 'abst' ? `url(#${id}-hach)` : CORES[k] }));
      }
      g = g1;
    }
    svg.append(gAnel);
  }

  // régua: 40 marcas (uma por voto em 100 aptos até o teto)
  const regua = el('g', { stroke: '#8f8a78', 'stroke-width': 1 });
  for (let i = 0; i < 40; i += 1) {
    const g = (360 * i) / 40;
    const longo = i % 10 === 0;
    const [x0, y0] = ponto(C, longo ? 166 : 170, g);
    const [x1, y1] = ponto(C, 175, g);
    regua.append(el('line', { x1: x0.toFixed(1), y1: y0.toFixed(1), x2: x1.toFixed(1), y2: y1.toFixed(1), 'stroke-width': longo ? 1.6 : 0.8 }));
  }
  svg.append(regua);

  // círculos-guia dos setores
  const R0 = 70;
  const R1 = 158;
  const escala = Math.max(1, teto / 2);
  const raio = (v) => R0 + (R1 - R0) * Math.sqrt(Math.max(0, Math.min(1, v / escala)));
  const guias = el('g', { fill: 'none', stroke: '#d9d5c7', 'stroke-dasharray': '2 3' });
  for (const v of [escala / 4, escala / 2, escala]) guias.append(el('circle', { cx: C, cy: C, r: raio(v).toFixed(1) }));
  svg.append(guias);

  // quatro setores (quadrantes): começando no alto, sentido horário
  const gSet = el('g', { class: 'carta-setores' });
  const gRot = el('g', { class: 'carta-valores' });
  comps.forEach((k, i) => {
    const v = num(local[k]);
    const g0 = i * 90 + 4;
    const g1 = (i + 1) * 90 - 4;
    gSet.append(el('path', { d: arco(C, R0, R1, g0, g1), fill: CORES[k], opacity: 0.1 }));
    if (v !== null && v > 0) {
      gSet.append(el('path', { d: arco(C, R0, raio(v), g0, g1), fill: CORES[k], stroke: '#ffffff', 'stroke-width': 1 }));
    }
    const [lx, ly] = ponto(C, R1 - 18, i * 90 + 45);
    const txt = v === null ? 's/d' : f1(v);
    const w = 12 + txt.length * 8.4;
    gRot.append(
      el('rect', { x: (lx - w / 2).toFixed(1), y: (ly - 12).toFixed(1), width: w.toFixed(1), height: 22, rx: 11, fill: '#ffffff', stroke: CORES[k], 'stroke-width': 1.5 }),
      el('text', { x: lx.toFixed(1), y: (ly + 4.5).toFixed(1), 'text-anchor': 'middle', 'font-family': 'IBM Plex Mono, monospace', 'font-size': 13, 'font-weight': 700, fill: '#151812' }, txt),
    );
  });
  svg.append(gSet, gRot);

  // disco central, com a faixa da bandeira
  const disco = el('g');
  disco.append(el('circle', { cx: C, cy: C, r: 62, fill: CORES.azul }));
  const clip = el('g', { 'clip-path': `url(#${id}-disco)` });
  clip.append(el('path', { d: `M${C - 70} ${C + 22} Q ${C} ${C + 4} ${C + 70} ${C + 22}`, stroke: '#ffffff', 'stroke-width': 15, fill: 'none' }));
  disco.append(clip);
  disco.append(
    el('text', { x: C, y: C + 3, 'text-anchor': 'middle', 'font-family': 'Fraunces, Georgia, serif', 'font-size': 44, 'font-weight': 900, fill: '#ffffff' }, local.indice === null || local.indice === undefined ? 's/d' : String(local.indice)),
  );
  const tp = el('text', { 'font-family': 'IBM Plex Mono, monospace', 'font-size': 7.6, 'font-weight': 700, 'letter-spacing': 0.9, fill: '#0b5a2c' });
  tp.append(el('textPath', { href: `#${id}-faixa`, startOffset: '50%', 'text-anchor': 'middle' }, 'ÍNDICE DE CONVERSA'));
  disco.append(tp);
  disco.append(el('text', { x: C, y: C + 46, 'text-anchor': 'middle', 'font-family': 'IBM Plex Mono, monospace', 'font-size': 10, 'font-weight': 700, fill: '#ffcc29' }, 'de 100'));
  svg.append(disco);

  return svg;
}

/** Losango pequeno (marca da casa nesta página) com o índice dentro. */
export function losango(valor, cor, tam = 44) {
  const s = el('svg', { viewBox: '0 0 44 44', width: tam, height: tam, class: 'losango', 'aria-hidden': 'true', focusable: 'false' });
  s.append(el('path', { d: 'M22 1 L43 22 L22 43 L1 22 Z', fill: cor }));
  s.append(el('text', { x: 22, y: 26.5, 'text-anchor': 'middle', 'font-family': 'IBM Plex Mono, monospace', 'font-size': 13, 'font-weight': 700, fill: cor === '#f2c230' ? '#151812' : '#ffffff' }, valor === null || valor === undefined ? '' : String(valor)));
  return s;
}
