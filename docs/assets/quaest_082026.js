(() => {
  'use strict';

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const svgNS = 'http://www.w3.org/2000/svg';

  function svgEl(name, attrs = {}, text = '') {
    const el = document.createElementNS(svgNS, name);
    Object.entries(attrs).forEach(([key, value]) => el.setAttribute(key, value));
    if (text) el.textContent = text;
    return el;
  }

  function lineChart(title, dates, redValues, blueValues) {
    const width = 530;
    const height = 280;
    const margin = { top: 50, right: 72, bottom: 45, left: 48 };
    const min = Math.min(...redValues, ...blueValues) - 3;
    const max = Math.max(...redValues, ...blueValues) + 3;
    const x = index => margin.left + index * ((width - margin.left - margin.right) / (dates.length - 1));
    const y = value => margin.top + (max - value) * ((height - margin.top - margin.bottom) / (max - min));
    const svg = svgEl('svg', { viewBox: `0 0 ${width} ${height}`, role: 'img', 'aria-label': title });

    svg.append(svgEl('text', { x: margin.left, y: 25, fill: '#081522', 'font-size': 20, 'font-weight': 700 }, title));
    for (let value = Math.ceil(min / 5) * 5; value <= max; value += 5) {
      const rowY = y(value);
      svg.append(svgEl('line', { x1: margin.left, y1: rowY, x2: width - margin.right, y2: rowY, stroke: '#d9ddde', 'stroke-width': 1 }));
      svg.append(svgEl('text', { x: margin.left - 10, y: rowY + 4, fill: '#617080', 'font-size': 13, 'text-anchor': 'end' }, `${value}%`));
    }

    const series = [
      { name: 'Lula', values: redValues, color: '#d9473f' },
      { name: 'Flávio', values: blueValues, color: '#2267ee' }
    ];
    series.forEach(({ name, values, color }) => {
      const path = values.map((value, index) => `${index ? 'L' : 'M'} ${x(index)} ${y(value)}`).join(' ');
      svg.append(svgEl('path', { d: path, fill: 'none', stroke: color, 'stroke-width': 5, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }));
      values.forEach((value, index) => {
        svg.append(svgEl('circle', { cx: x(index), cy: y(value), r: 7, fill: '#fffdf8', stroke: color, 'stroke-width': 4 }));
        svg.append(svgEl('text', { x: x(index), y: y(value) - 15, fill: color, 'font-size': 16, 'font-weight': 700, 'text-anchor': 'middle' }, value));
      });
      const last = values.length - 1;
      svg.append(svgEl('text', { x: x(last) + 15, y: y(values[last]) + 5, fill: color, 'font-size': 14, 'font-weight': 700 }, name));
    });
    dates.forEach((date, index) => svg.append(svgEl('text', { x: x(index), y: height - 14, fill: '#617080', 'font-size': 14, 'text-anchor': 'middle' }, date)));
    return svg;
  }

  function renderVoteSeries(data) {
    const target = $('#vote-series');
    if (!target) return;
    const first = data.vote.first_round;
    const runoff = data.vote.runoff;
    target.replaceChildren(
      lineChart('Primeiro turno', first.dates, first.Lula, first['Flávio Bolsonaro']),
      lineChart('Segundo turno', runoff.dates, runoff.Lula, runoff['Flávio Bolsonaro'])
    );
    target.classList.add('grid-2');
  }

  function renderSegments(data) {
    const target = $('#segment-chart');
    if (!target) return;
    const preferred = ['Sul', 'Evangélicos', '5+ SM', 'Homens', 'Nordeste', 'Pretos', 'Bolsa Família', 'Até 2 SM'];
    target.replaceChildren();
    preferred.forEach(label => {
      const [lula, flavio] = data.vote.runoff_segments[label];
      const gap = flavio - lula;
      const row = document.createElement('div');
      row.className = 'segment-row';
      const name = document.createElement('b');
      name.textContent = label;
      const bar = document.createElement('div');
      bar.className = `segment-bar${gap < 0 ? ' negative' : ''}`;
      const fill = document.createElement('span');
      fill.style.width = `${Math.min(50, Math.abs(gap))}%`;
      bar.append(fill);
      const output = document.createElement('output');
      output.textContent = `${gap >= 0 ? 'F' : 'L'} +${Math.abs(gap)}`;
      row.append(name, bar, output);
      target.append(row);
    });
  }

  function renderPolls(data) {
    const target = $('#poll-chart');
    if (!target) return;
    target.replaceChildren();
    data.comparators.forEach(poll => {
      const [lula, flavio] = poll.first;
      const scale = 1.08;
      const row = document.createElement('div');
      row.className = 'poll-row';
      row.innerHTML = `<div class="name"><b>${poll.poll}</b><small>${poll.field} · ${poll.mode}</small></div><div class="duel" aria-label="${poll.poll}: Lula ${lula}, Flávio ${flavio}"><span class="lula" style="width:${lula * scale}%"></span><span class="flavio" style="width:${flavio * scale}%"></span></div><output>${lula} × ${flavio}</output>`;
      target.append(row);
    });
  }

  const INK = '#081522';
  const MUTED = '#617080';
  const GRID = '#d9ddde';
  const RED = '#d9473f';
  const BLUE = '#2267ee';
  const GOLD = '#d89a24';
  const GREEN = '#15805e';
  const MONO = 'IBM Plex Mono, ui-monospace, monospace';
  const SANS = 'IBM Plex Sans Condensed, Arial, sans-serif';

  function txt(x, y, value, attrs = {}) {
    return svgEl(
      'text',
      { x, y, 'font-family': MONO, 'font-size': 12, fill: MUTED, ...attrs },
      value
    );
  }

  // Capítulo 02: desaprovação do governo menos voto em Flávio, por recorte.
  function renderConversion(data) {
    const target = $('#conversion-chart');
    if (!target) return;
    const rows = data.strategy.conversion.rows.slice(0, 12);
    const width = 1080;
    const rowH = 58;
    const left = 258;
    const right = 168;
    const height = 100 + rows.length * rowH;
    const scale = value => (value / 70) * (width - left - right);
    const svg = svgEl('svg', {
      viewBox: `0 0 ${width} ${height}`,
      role: 'img',
      'aria-label': 'Desaprovação de Lula contra voto em Flávio no segundo turno, por recorte'
    });
    svg.append(txt(left, 30, 'DESAPROVAÇÃO DE LULA', { fill: RED, 'font-weight': 700, 'font-size': 15 }));
    svg.append(txt(left + 330, 30, 'VOTO EM FLÁVIO NO 2º TURNO', { fill: BLUE, 'font-weight': 700, 'font-size': 15 }));
    svg.append(txt(width - 14, 30, 'O VÃO', { 'text-anchor': 'end', fill: INK, 'font-weight': 700, 'font-size': 15 }));
    rows.forEach((row, index) => {
      const y = 62 + index * rowH;
      const wDis = scale(row.disapproval);
      const wFla = scale(row.flavio_runoff);
      svg.append(svgEl('line', { x1: 14, y1: y + 44, x2: width - 14, y2: y + 44, stroke: GRID }));
      svg.append(txt(left - 18, y + 30, row.segment, { 'text-anchor': 'end', 'font-family': SANS, 'font-size': 18, 'font-weight': 700, fill: INK }));
      svg.append(svgEl('rect', { x: left, y: y + 2, width: wDis, height: 15, fill: RED, opacity: .3 }));
      svg.append(svgEl('rect', { x: left, y: y + 21, width: wFla, height: 15, fill: BLUE }));
      svg.append(svgEl('rect', { x: left + wFla, y: y + 2, width: wDis - wFla, height: 34, fill: 'none', stroke: INK, 'stroke-dasharray': '4 3' }));
      svg.append(txt(left + wDis + 12, y + 15, `${row.disapproval}`, { fill: RED, 'font-weight': 700, 'font-size': 16 }));
      svg.append(txt(left + wFla - 12, y + 35, `${row.flavio_runoff}`, { 'text-anchor': 'end', fill: '#fff', 'font-weight': 700, 'font-size': 16 }));
      svg.append(txt(width - 14, y + 30, `+${row.unconverted}`, { 'text-anchor': 'end', fill: INK, 'font-weight': 700, 'font-size': 26 }));
    });
    target.replaceChildren(svg);
  }

  // Capítulo 03: os quatro cenários de segundo turno da mesma amostra.
  function renderScenarios(data) {
    const target = $('#scenario-chart');
    if (!target) return;
    const rows = data.strategy.substitution.scenarios;
    const width = 1080;
    const rowH = 100;
    const height = 86 + rows.length * rowH;
    const left = 300;
    const right = 168;
    const scale = value => left + ((value - 28) / 22) * (width - left - right);
    const svg = svgEl('svg', {
      viewBox: `0 0 ${width} ${height}`,
      role: 'img',
      'aria-label': 'Quatro cenários de segundo turno medidos na mesma amostra'
    });
    svg.append(svgEl('line', { x1: scale(44), y1: 46, x2: scale(44), y2: height - 24, stroke: RED, 'stroke-dasharray': '6 5', opacity: .5 }));
    svg.append(txt(scale(44), 34, 'Lula praticamente parado', { 'text-anchor': 'middle', fill: RED, 'font-weight': 700, 'font-size': 15 }));
    rows.forEach((row, index) => {
      const y = 84 + index * rowH;
      const xLula = scale(row.lula);
      const xChallenger = scale(row.challenger_pct);
      svg.append(txt(left - 26, y + 2, row.challenger, { 'text-anchor': 'end', 'font-family': SANS, 'font-size': 21, 'font-weight': 700, fill: INK }));
      svg.append(txt(left - 26, y + 26, `branco, nulo e indeciso ${row.non_choice}`, { 'text-anchor': 'end', 'font-size': 14 }));
      svg.append(svgEl('line', { x1: xChallenger, y1: y - 4, x2: xLula, y2: y - 4, stroke: INK, 'stroke-width': 4, opacity: .22 }));
      svg.append(svgEl('circle', { cx: xChallenger, cy: y - 4, r: 20, fill: index ? '#8c9db4' : BLUE }));
      svg.append(svgEl('circle', { cx: xLula, cy: y - 4, r: 20, fill: RED }));
      svg.append(txt(xChallenger, y + 2, `${row.challenger_pct}`, { 'text-anchor': 'middle', fill: '#fff', 'font-weight': 700, 'font-size': 18 }));
      svg.append(txt(xLula, y + 2, `${row.lula}`, { 'text-anchor': 'middle', fill: '#fff', 'font-weight': 700, 'font-size': 18 }));
      svg.append(txt(width - 14, y + 3, `${row.gap} pontos`, { 'text-anchor': 'end', fill: index ? MUTED : INK, 'font-weight': 700, 'font-size': index ? 18 : 24 }));
    });
    target.replaceChildren(svg);
  }

  // Capítulo 03: o custo de trocar Flávio, recorte a recorte.
  function renderSubstitution(data) {
    const target = $('#substitution-chart');
    if (!target) return;
    const rows = [...data.strategy.substitution.segments].sort((a, b) => b.gap_to_best - a.gap_to_best);
    const width = 1080;
    const rowH = 40;
    const height = 72 + rows.length * rowH;
    const mid = 610;
    const unit = 21;
    const svg = svgEl('svg', {
      viewBox: `0 0 ${width} ${height}`,
      role: 'img',
      'aria-label': 'Diferença entre Flávio e o melhor adversário alternativo, recorte a recorte'
    });
    svg.append(svgEl('line', { x1: mid, y1: 42, x2: mid, y2: height - 16, stroke: INK, 'stroke-width': 1.5 }));
    svg.append(txt(mid - 18, 30, 'melhor sem Flávio', { 'text-anchor': 'end', 'font-weight': 700, 'font-size': 14, fill: GOLD }));
    svg.append(txt(mid + 18, 30, 'melhor com Flávio', { 'font-weight': 700, 'font-size': 14, fill: BLUE }));
    rows.forEach((row, index) => {
      const y = 52 + index * rowH;
      const value = row.gap_to_best;
      const w = Math.abs(value) * unit;
      const positive = value >= 0;
      svg.append(txt(214, y + 20, row.segment, { 'text-anchor': 'end', 'font-family': SANS, 'font-size': 16, 'font-weight': 700, fill: INK }));
      svg.append(txt(230, y + 20, `${row.best_alternative} faz ${row.best_alternative_pct}`, { 'font-size': 13 }));
      svg.append(svgEl('rect', { x: positive ? mid : mid - w, y: y + 6, width: Math.max(w, 3), height: 21, fill: positive ? BLUE : GOLD }));
      svg.append(txt(positive ? mid + w + 10 : mid - w - 10, y + 23, `${positive ? '+' : ''}${value}`, { 'text-anchor': positive ? 'start' : 'end', 'font-weight': 700, 'font-size': 17, fill: positive ? BLUE : GOLD }));
    });
    target.replaceChildren(svg);
  }

  // Capítulo 04: onde o voto está, bloco a bloco, com largura pelo tamanho do bloco.
  const MOSAIC_SHORT = {
    'Esquerda não lulista': 'Esq. não lulista',
    'Direita não bolsonarista': 'Direita não bolson.'
  };

  const MOSAIC_PARTS = [
    { key: 'lula_pp', color: RED, label: 'Lula' },
    { key: 'flavio_vote', color: BLUE, label: 'Flávio' },
    { key: 'third_way_pp', color: GOLD, label: 'terceira via' },
    { key: 'parked_pp', color: '#8c9db4', label: 'branco, nulo e indecisão' }
  ];

  function renderBlocMosaic(data) {
    const target = $('#bloc-mosaic');
    if (!target) return;
    const rows = data.strategy.useful_vote.rows;
    const width = 1080;
    const top = 96;
    const plot = 320;
    const height = top + plot + 62;
    const svg = svgEl('svg', {
      viewBox: `0 0 ${width} ${height}`,
      role: 'img',
      'aria-label': 'Mapa do voto por bloco de posicionamento, com largura proporcional ao tamanho do bloco'
    });
    const totalShare = rows.reduce((sum, row) => sum + row.share, 0);
    let x = 0;
    rows.forEach(row => {
      const w = (row.share / totalShare) * width;
      let y = top;
      MOSAIC_PARTS.forEach(part => {
        const h = (row[part.key] / 100) * plot;
        if (h <= 0) return;
        svg.append(svgEl('rect', { x, y, width: w - 6, height: h, fill: part.color }));
        if (h > 32 && w > 100) {
          svg.append(txt(x + 14, y + 30, `${row[part.key]}`, { fill: '#fff', 'font-weight': 700, 'font-size': 23 }));
        }
        y += h;
      });
      const label = MOSAIC_SHORT[row.bloc] || row.bloc;
      svg.append(txt(x, top - 44, label, { 'font-family': SANS, 'font-size': 18, 'font-weight': 700, fill: INK }));
      svg.append(txt(x, top - 20, `${row.share}%`, { 'font-size': 17, 'font-weight': 700 }));
      x += w;
    });
    let legendX = 0;
    MOSAIC_PARTS.forEach(part => {
      svg.append(svgEl('rect', { x: legendX, y: top + plot + 24, width: 15, height: 15, fill: part.color }));
      svg.append(txt(legendX + 23, top + plot + 37, part.label, { 'font-size': 14, 'font-weight': 700 }));
      legendX += 34 + part.label.length * 8.2;
    });
    target.replaceChildren(svg);
    renderBlocLegend(data);
  }

  // A conversão de cada bloco para pontos nacionais sai do SVG e vira cartão,
  // porque em coluna estreita o rótulo colava no vizinho e ficava ilegível.
  function renderBlocLegend(data) {
    const target = $('#bloc-legend');
    if (!target) return;
    const br = value => value.toFixed(2).replace('.', ',');
    target.replaceChildren();
    data.strategy.useful_vote.rows.forEach(row => {
      const card = document.createElement('article');
      card.innerHTML =
        `<h4>${row.bloc}</h4><span class="share">${row.share}% do eleitorado</span>` +
        `<dl><div><dt>terceira via</dt><dd class="gold">${br(row.third_way_national)}</dd></div>` +
        `<div><dt>estacionado</dt><dd>${br(row.parked_national)}</dd></div>` +
        `<div><dt>folga de Flávio</dt><dd class="blue">${br(row.slack_national)}</dd></div></dl>`;
      target.append(card);
    });
  }

  // Capítulo 05: quanto de cada programa econômico chega e é sentido.
  function renderPrograms(data) {
    const target = $('#program-chart');
    if (!target) return;
    const rows = data.strategy.programs.rows;
    const width = 1080;
    const height = 320;
    const svg = svgEl('svg', {
      viewBox: `0 0 ${width} ${height}`,
      role: 'img',
      'aria-label': 'Alcance efetivo da isenção do IRPF e do Desenrola 2.0'
    });
    rows.forEach((row, index) => {
      const x = index * 548;
      const steps = [
        { label: 'eleitorado', value: 100, color: '#c7ced6' },
        { label: 'diz ter sido alcançado', value: row.reached_pct, color: BLUE },
        { label: 'sentiu aumento real na renda', value: row.felt_a_lot_national, color: GREEN }
      ];
      svg.append(txt(x, 30, row.program, { 'font-family': SANS, 'font-size': 22, 'font-weight': 700, fill: INK }));
      steps.forEach((step, level) => {
        const y = 68 + level * 84;
        const w = Math.max((step.value / 100) * 430, 4);
        svg.append(txt(x, y - 8, step.label, { 'font-size': 15 }));
        svg.append(svgEl('rect', { x, y, width: w, height: 48, fill: step.color }));
        const inside = w > 130;
        svg.append(txt(inside ? x + 14 : x + w + 12, y + 34, `${step.value.toString().replace('.', ',')}%`, {
          fill: inside && level ? '#fff' : INK,
          'font-weight': 700,
          'font-size': 28
        }));
      });
    });
    target.replaceChildren(svg);
  }

  // Capítulo 06: canal de informação contra margem de Flávio, por recorte.
  function renderMedia(data) {
    const target = $('#media-chart');
    if (!target) return;
    const rows = data.strategy.media.rows;
    const width = 1080;
    const rowH = 68;
    const height = 92 + rows.length * rowH;
    const left = 232;
    const svg = svgEl('svg', {
      viewBox: `0 0 ${width} ${height}`,
      role: 'img',
      'aria-label': 'Canal de informação e margem de Flávio, por recorte'
    });
    svg.append(txt(left, 30, 'TV', { fill: RED, 'font-weight': 700, 'font-size': 15 }));
    svg.append(txt(left + 46, 30, 'REDES SOCIAIS', { fill: BLUE, 'font-weight': 700, 'font-size': 15 }));
    svg.append(txt(width - 14, 30, 'MARGEM DE FLÁVIO NO 2º TURNO', { 'text-anchor': 'end', 'font-weight': 700, 'font-size': 15, fill: INK }));
    rows.forEach((row, index) => {
      const y = 60 + index * rowH;
      const scale = value => (value / 60) * 480;
      svg.append(txt(left - 18, y + 32, row.segment, { 'text-anchor': 'end', 'font-family': SANS, 'font-size': 18, 'font-weight': 700, fill: INK }));
      svg.append(svgEl('rect', { x: left, y: y + 2, width: scale(row.tv), height: 20, fill: RED, opacity: .82 }));
      svg.append(svgEl('rect', { x: left, y: y + 26, width: scale(row.redes), height: 20, fill: BLUE }));
      svg.append(txt(left + scale(row.tv) + 10, y + 18, `${row.tv}`, { fill: RED, 'font-weight': 700, 'font-size': 17 }));
      svg.append(txt(left + scale(row.redes) + 10, y + 42, `${row.redes}`, { fill: BLUE, 'font-weight': 700, 'font-size': 17 }));
      const margin = row.flavio_margin;
      svg.append(txt(width - 14, y + 34, `${margin > 0 ? '+' : ''}${margin}`, { 'text-anchor': 'end', 'font-weight': 700, 'font-size': 30, fill: margin > 0 ? BLUE : RED }));
      svg.append(svgEl('line', { x1: 14, y1: y + 58, x2: width - 14, y2: y + 58, stroke: GRID }));
    });
    target.replaceChildren(svg);
  }

  // Capítulo 15: o que o questionário pergunta, e de quem cobra.
  function renderBalance(data) {
    const target = $('#balance-chart');
    if (!target) return;
    const order = ['Lula', 'Flávio', 'instituições', 'disputa', 'atributo', 'operacional', 'cadastro político', 'ambos', 'contexto'];
    const byOnus = data.strategy.questionnaire_balance.by_onus;
    const rows = order.filter(key => byOnus[key]).map(key => ({ key, ...byOnus[key] }));
    const width = 1080;
    const rowH = 56;
    const height = 92 + rows.length * rowH;
    const left = 250;
    const unit = 26;
    const svg = svgEl('svg', {
      viewBox: `0 0 ${width} ${height}`,
      role: 'img',
      'aria-label': 'Itens do questionário por quem a pergunta coloca em julgamento'
    });
    svg.append(txt(left, 30, 'PUBLICADOS', { fill: GREEN, 'font-weight': 700, 'font-size': 15 }));
    svg.append(txt(left + 150, 30, 'RETIDOS', { fill: RED, 'font-weight': 700, 'font-size': 15 }));
    svg.append(txt(width - 14, 30, 'ITENS NUMERADOS', { 'text-anchor': 'end', fill: INK, 'font-weight': 700, 'font-size': 15 }));
    rows.forEach((row, index) => {
      const y = 58 + index * rowH;
      svg.append(svgEl('line', { x1: 14, y1: y + 42, x2: width - 14, y2: y + 42, stroke: GRID }));
      svg.append(txt(left - 18, y + 26, row.key, { 'text-anchor': 'end', 'font-family': SANS, 'font-size': 18, 'font-weight': 700, fill: INK }));
      svg.append(svgEl('rect', { x: left, y: y + 8, width: row.published * unit, height: 24, fill: GREEN }));
      svg.append(svgEl('rect', { x: left + row.published * unit, y: y + 8, width: row.withheld * unit, height: 24, fill: RED, opacity: .55 }));
      if (row.published) {
        svg.append(txt(left + 10, y + 26, `${row.published}`, { fill: '#fff', 'font-weight': 700, 'font-size': 15 }));
      }
      if (row.withheld) {
        svg.append(txt(left + (row.published + row.withheld) * unit - 10, y + 26, `${row.withheld}`, { 'text-anchor': 'end', fill: '#fff', 'font-weight': 700, 'font-size': 15 }));
      }
      svg.append(txt(width - 14, y + 26, `${row.items}`, { 'text-anchor': 'end', fill: INK, 'font-weight': 700, 'font-size': 22 }));
    });
    target.replaceChildren(svg);
  }

  // Capítulo 15: quantas peças cada bloco rendeu na cobertura recuperada.
  function renderPress(data) {
    const target = $('#press-chart');
    if (!target) return;
    const rows = data.strategy.press.ledger
      .filter(row => row.headline_ready)
      .sort((a, b) => b.pieces - a.pieces);
    const width = 1080;
    const rowH = 40;
    const height = 76 + rows.length * rowH;
    const left = 470;
    const unit = 58;
    const svg = svgEl('svg', {
      viewBox: `0 0 ${width} ${height}`,
      role: 'img',
      'aria-label': 'Peças de imprensa recuperadas por bloco do questionário'
    });
    svg.append(txt(left, 30, 'PEÇAS RECUPERADAS NA COBERTURA DE 5 E 6 DE AGOSTO', { fill: INK, 'font-weight': 700, 'font-size': 15 }));
    rows.forEach((row, index) => {
      const y = 50 + index * rowH;
      const color = row.onus === 'Lula' ? RED : row.onus === 'Flávio' ? BLUE : '#8c9db4';
      svg.append(txt(left - 18, y + 22, row.tema.length > 52 ? `${row.tema.slice(0, 50)}…` : row.tema, { 'text-anchor': 'end', 'font-family': SANS, 'font-size': 15, 'font-weight': 700, fill: INK }));
      svg.append(txt(left - 18, y + 38, `${row.range} · ônus ${row.onus}`, { 'text-anchor': 'end', 'font-size': 12 }));
      if (row.pieces) {
        svg.append(svgEl('rect', { x: left, y: y + 8, width: row.pieces * unit, height: 22, fill: color }));
        svg.append(txt(left + row.pieces * unit + 10, y + 25, `${row.pieces}`, { fill: color, 'font-weight': 700, 'font-size': 19 }));
        const labelX = left + row.pieces * unit + 32;
        const room = Math.floor((width - 14 - labelX) / 7.2);
        let names = row.outlets.join(', ');
        if (names.length > room) {
          const shown = [];
          for (const outlet of row.outlets) {
            if ([...shown, outlet].join(', ').length + 10 > room) break;
            shown.push(outlet);
          }
          const rest = row.outlets.length - shown.length;
          names = !shown.length ? `${row.outlets.length} veículos` : rest > 0 ? `${shown.join(', ')} e mais ${rest}` : shown.join(', ');
        }
        svg.append(txt(labelX, y + 25, names, { 'font-size': 12 }));
      } else {
        svg.append(svgEl('rect', { x: left, y: y + 8, width: 4, height: 22, fill: GRID }));
        svg.append(txt(left + 14, y + 25, 'nenhuma peça recuperada', { fill: RED, 'font-weight': 700, 'font-size': 15 }));
      }
    });
    target.replaceChildren(svg);
    renderPressList(data);
  }

  function renderPressList(data) {
    const target = $('#press-list');
    if (!target) return;
    target.replaceChildren();
    data.strategy.press.pieces.forEach(piece => {
      const item = document.createElement('li');
      item.innerHTML =
        `<div><a href="${piece.url}" rel="noopener">${piece.outlet}: “${piece.title}”</a>` +
        `<small>bloco ${piece.block} · ${piece.angle}</small></div>`;
      target.append(item);
    });
    data.strategy.press.economy_other_waves.forEach(piece => {
      const item = document.createElement('li');
      item.innerHTML =
        `<div><a href="${piece.url}" rel="noopener">${piece.outlet}: “${piece.title}”</a>` +
        `<small>contraprova · publicado em ${piece.published} sobre o ${piece.wave}</small></div>`;
      target.append(item);
    });
  }

  function setupReveal() {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduced || !('IntersectionObserver' in window)) {
      $$('.reveal').forEach(el => el.classList.add('visible'));
      return;
    }
    document.documentElement.classList.add('reveal-ready');
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.08, rootMargin: '0px 0px -45px' });
    $$('.reveal').forEach(el => observer.observe(el));
  }

  function setupNavigation() {
    const links = $$('.toc a');
    const map = new Map(links.map(link => [link.getAttribute('href').slice(1), link]));
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        links.forEach(link => link.classList.remove('active'));
        map.get(entry.target.id)?.classList.add('active');
      });
    }, { rootMargin: '-35% 0px -60%' });
    $$('main section[id]').forEach(section => observer.observe(section));
  }

  async function loadData() {
    try {
      const response = await fetch('assets/quaest_082026_data.json');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      renderVoteSeries(data);
      renderSegments(data);
      renderPolls(data);
      renderConversion(data);
      renderScenarios(data);
      renderSubstitution(data);
      renderBlocMosaic(data);
      renderPrograms(data);
      renderMedia(data);
      renderBalance(data);
      renderPress(data);
    } catch (error) {
      console.warn('Os gráficos dinâmicos mantiveram o conteúdo textual de fallback.', error);
    }
  }

  setupReveal();
  setupNavigation();
  loadData();
})();
