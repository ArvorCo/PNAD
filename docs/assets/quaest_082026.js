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
    const margin = { top: 50, right: 38, bottom: 45, left: 45 };
    const min = Math.min(...redValues, ...blueValues) - 3;
    const max = Math.max(...redValues, ...blueValues) + 3;
    const x = index => margin.left + index * ((width - margin.left - margin.right) / (dates.length - 1));
    const y = value => margin.top + (max - value) * ((height - margin.top - margin.bottom) / (max - min));
    const svg = svgEl('svg', { viewBox: `0 0 ${width} ${height}`, role: 'img', 'aria-label': title });

    svg.append(svgEl('text', { x: margin.left, y: 25, fill: '#081522', 'font-size': 18, 'font-weight': 700 }, title));
    for (let value = Math.ceil(min / 5) * 5; value <= max; value += 5) {
      const rowY = y(value);
      svg.append(svgEl('line', { x1: margin.left, y1: rowY, x2: width - margin.right, y2: rowY, stroke: '#d9ddde', 'stroke-width': 1 }));
      svg.append(svgEl('text', { x: margin.left - 10, y: rowY + 4, fill: '#617080', 'font-size': 11, 'text-anchor': 'end' }, `${value}%`));
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
        svg.append(svgEl('text', { x: x(index), y: y(value) - 14, fill: color, 'font-size': 14, 'font-weight': 700, 'text-anchor': 'middle' }, value));
      });
      const last = values.length - 1;
      svg.append(svgEl('text', { x: x(last) + 15, y: y(values[last]) + 5, fill: color, 'font-size': 12, 'font-weight': 700 }, name));
    });
    dates.forEach((date, index) => svg.append(svgEl('text', { x: x(index), y: height - 16, fill: '#617080', 'font-size': 12, 'text-anchor': 'middle' }, date)));
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
    const rowH = 46;
    const height = 78 + rows.length * rowH;
    const left = 210;
    const right = 150;
    const scale = value => (value / 70) * (width - left - right);
    const svg = svgEl('svg', {
      viewBox: `0 0 ${width} ${height}`,
      role: 'img',
      'aria-label': 'Desaprovação de Lula contra voto em Flávio no segundo turno, por recorte'
    });
    svg.append(txt(left, 26, 'DESAPROVAÇÃO DE LULA', { fill: RED, 'font-weight': 700, 'font-size': 13 }));
    svg.append(txt(left + 300, 26, 'VOTO EM FLÁVIO NO 2º TURNO', { fill: BLUE, 'font-weight': 700, 'font-size': 13 }));
    svg.append(txt(width - right + 14, 26, 'O VÃO', { fill: INK, 'font-weight': 700, 'font-size': 13 }));
    rows.forEach((row, index) => {
      const y = 56 + index * rowH;
      svg.append(svgEl('line', { x1: left, y1: y + 34, x2: width - right, y2: y + 34, stroke: GRID }));
      svg.append(txt(left - 14, y + 24, row.segment, { 'text-anchor': 'end', 'font-family': SANS, 'font-size': 15, 'font-weight': 700, fill: INK }));
      svg.append(svgEl('rect', { x: left, y: y + 4, width: scale(row.disapproval), height: 12, fill: RED, opacity: .28 }));
      svg.append(svgEl('rect', { x: left, y: y + 18, width: scale(row.flavio_runoff), height: 12, fill: BLUE }));
      svg.append(svgEl('rect', { x: left + scale(row.flavio_runoff), y: y + 4, width: scale(row.unconverted), height: 26, fill: 'none', stroke: INK, 'stroke-dasharray': '3 3' }));
      svg.append(txt(left + scale(row.disapproval) + 8, y + 15, `${row.disapproval}`, { fill: RED, 'font-weight': 700 }));
      svg.append(txt(left + scale(row.flavio_runoff) + 8, y + 29, `${row.flavio_runoff}`, { fill: BLUE, 'font-weight': 700 }));
      svg.append(txt(width - right + 14, y + 24, `+${row.unconverted}`, { fill: INK, 'font-weight': 700, 'font-size': 20 }));
    });
    target.replaceChildren(svg);
  }

  // Capítulo 03: os quatro cenários de segundo turno da mesma amostra.
  function renderScenarios(data) {
    const target = $('#scenario-chart');
    if (!target) return;
    const rows = data.strategy.substitution.scenarios;
    const width = 1080;
    const rowH = 92;
    const height = 70 + rows.length * rowH;
    const left = 250;
    const right = 120;
    const scale = value => left + ((value - 28) / 22) * (width - left - right);
    const svg = svgEl('svg', {
      viewBox: `0 0 ${width} ${height}`,
      role: 'img',
      'aria-label': 'Quatro cenários de segundo turno medidos na mesma amostra'
    });
    svg.append(svgEl('line', { x1: scale(44), y1: 40, x2: scale(44), y2: height - 20, stroke: RED, 'stroke-dasharray': '5 5', opacity: .5 }));
    svg.append(txt(scale(44), 30, 'Lula praticamente parado', { 'text-anchor': 'middle', fill: RED, 'font-weight': 700 }));
    rows.forEach((row, index) => {
      const y = 74 + index * rowH;
      const xLula = scale(row.lula);
      const xChallenger = scale(row.challenger_pct);
      svg.append(txt(left - 20, y + 5, row.challenger, { 'text-anchor': 'end', 'font-family': SANS, 'font-size': 18, 'font-weight': 700, fill: INK }));
      svg.append(txt(left - 20, y + 26, `branco, nulo e indeciso ${row.non_choice}`, { 'text-anchor': 'end', 'font-size': 11 }));
      svg.append(svgEl('line', { x1: xChallenger, y1: y, x2: xLula, y2: y, stroke: INK, 'stroke-width': 3, opacity: .25 }));
      svg.append(svgEl('circle', { cx: xChallenger, cy: y, r: 15, fill: index ? '#8c9db4' : BLUE }));
      svg.append(svgEl('circle', { cx: xLula, cy: y, r: 15, fill: RED }));
      svg.append(txt(xChallenger, y + 5, `${row.challenger_pct}`, { 'text-anchor': 'middle', fill: '#fff', 'font-weight': 700, 'font-size': 14 }));
      svg.append(txt(xLula, y + 5, `${row.lula}`, { 'text-anchor': 'middle', fill: '#fff', 'font-weight': 700, 'font-size': 14 }));
      svg.append(txt(width - right + 16, y + 6, `${row.gap} pontos`, { fill: index ? MUTED : INK, 'font-weight': 700, 'font-size': index ? 15 : 19 }));
    });
    target.replaceChildren(svg);
  }

  // Capítulo 03: o custo de trocar Flávio, recorte a recorte.
  function renderSubstitution(data) {
    const target = $('#substitution-chart');
    if (!target) return;
    const rows = [...data.strategy.substitution.segments].sort((a, b) => b.gap_to_best - a.gap_to_best);
    const width = 1080;
    const rowH = 30;
    const height = 60 + rows.length * rowH;
    const mid = 620;
    const unit = 22;
    const svg = svgEl('svg', {
      viewBox: `0 0 ${width} ${height}`,
      role: 'img',
      'aria-label': 'Diferença entre Flávio e o melhor adversário alternativo, recorte a recorte'
    });
    svg.append(svgEl('line', { x1: mid, y1: 34, x2: mid, y2: height - 14, stroke: INK, 'stroke-width': 1.5 }));
    svg.append(txt(mid - 16, 24, 'melhor sem Flávio', { 'text-anchor': 'end', 'font-weight': 700, fill: MUTED }));
    svg.append(txt(mid + 16, 24, 'melhor com Flávio', { 'font-weight': 700, fill: BLUE }));
    rows.forEach((row, index) => {
      const y = 44 + index * rowH;
      const value = row.gap_to_best;
      const w = Math.abs(value) * unit;
      const positive = value >= 0;
      svg.append(txt(190, y + 15, row.segment, { 'text-anchor': 'end', 'font-family': SANS, 'font-size': 14, 'font-weight': 700, fill: INK }));
      svg.append(txt(210, y + 15, `melhor alternativa: ${row.best_alternative} ${row.best_alternative_pct}`, { 'font-size': 11 }));
      svg.append(svgEl('rect', { x: positive ? mid : mid - w, y: y + 4, width: Math.max(w, 2), height: 16, fill: positive ? BLUE : GOLD }));
      svg.append(txt(positive ? mid + w + 8 : mid - w - 8, y + 17, `${positive ? '+' : ''}${value}`, { 'text-anchor': positive ? 'start' : 'end', 'font-weight': 700, fill: positive ? BLUE : GOLD }));
    });
    target.replaceChildren(svg);
  }

  // Capítulo 04: onde o voto está, bloco a bloco, com largura pelo tamanho do bloco.
  function renderBlocMosaic(data) {
    const target = $('#bloc-mosaic');
    if (!target) return;
    const rows = data.strategy.useful_vote.rows;
    const width = 1080;
    const height = 460;
    const top = 96;
    const plot = 288;
    const svg = svgEl('svg', {
      viewBox: `0 0 ${width} ${height}`,
      role: 'img',
      'aria-label': 'Mapa do voto por bloco de posicionamento, com largura proporcional ao tamanho do bloco'
    });
    const totalShare = rows.reduce((sum, row) => sum + row.share, 0);
    let x = 0;
    const parts = [
      { key: 'lula_pp', color: RED, label: 'Lula' },
      { key: 'flavio_vote', color: BLUE, label: 'Flávio' },
      { key: 'third_way_pp', color: GOLD, label: 'terceira via' },
      { key: 'parked_pp', color: '#8c9db4', label: 'estacionado' }
    ];
    rows.forEach(row => {
      const w = (row.share / totalShare) * (width - 12);
      let y = top;
      parts.forEach(part => {
        const h = (row[part.key] / 100) * plot;
        if (h <= 0) return;
        svg.append(svgEl('rect', { x, y, width: w - 4, height: h, fill: part.color }));
        if (h > 26 && w > 90) {
          svg.append(txt(x + 10, y + 22, `${row[part.key]}`, { fill: '#fff', 'font-weight': 700, 'font-size': 15 }));
        }
        y += h;
      });
      svg.append(txt(x + 2, top - 34, row.bloc, { 'font-family': SANS, 'font-size': 14, 'font-weight': 700, fill: INK }));
      svg.append(txt(x + 2, top - 16, `${row.share}% do eleitorado`, { 'font-size': 11 }));
      const br = value => value.toFixed(2).replace('.', ',');
      svg.append(txt(x + 2, top + plot + 24, `3ª via ${br(row.third_way_national)}`, { 'font-size': 11, fill: GOLD, 'font-weight': 700 }));
      svg.append(txt(x + 2, top + plot + 42, `parado ${br(row.parked_national)}`, { 'font-size': 11, fill: MUTED, 'font-weight': 700 }));
      svg.append(txt(x + 2, top + plot + 60, `folga ${br(row.slack_national)}`, { 'font-size': 11, fill: BLUE, 'font-weight': 700 }));
      x += w;
    });
    svg.append(txt(2, 22, 'Altura: composição do voto dentro do bloco. Largura: tamanho do bloco no eleitorado. Pontos: conversão para o total nacional.', { 'font-size': 12 }));
    target.replaceChildren(svg);
  }

  // Capítulo 05: quanto de cada programa econômico chega e é sentido.
  function renderPrograms(data) {
    const target = $('#program-chart');
    if (!target) return;
    const rows = data.strategy.programs.rows;
    const width = 1080;
    const height = 300;
    const svg = svgEl('svg', {
      viewBox: `0 0 ${width} ${height}`,
      role: 'img',
      'aria-label': 'Alcance efetivo da isenção do IRPF e do Desenrola 2.0'
    });
    rows.forEach((row, index) => {
      const x = index * 540;
      const steps = [
        { label: 'eleitorado', value: 100, color: '#c7ced6' },
        { label: 'diz ter sido alcançado', value: row.reached_pct, color: BLUE },
        { label: 'sentiu aumento real na renda', value: row.felt_a_lot_national, color: GREEN }
      ];
      svg.append(txt(x + 10, 30, row.program, { 'font-family': SANS, 'font-size': 20, 'font-weight': 700, fill: INK }));
      steps.forEach((step, level) => {
        const y = 62 + level * 78;
        const w = Math.max((step.value / 100) * 430, 3);
        svg.append(txt(x + 10, y - 6, step.label, { 'font-size': 12 }));
        svg.append(svgEl('rect', { x: x + 10, y, width: w, height: 42, fill: step.color }));
        const inside = w > 110;
        svg.append(txt(inside ? x + 22 : x + 20 + w, y + 28, `${step.value.toString().replace('.', ',')}%`, {
          fill: inside && level ? '#fff' : INK,
          'font-weight': 700,
          'font-size': 24
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
    const rowH = 58;
    const height = 74 + rows.length * rowH;
    const left = 190;
    const svg = svgEl('svg', {
      viewBox: `0 0 ${width} ${height}`,
      role: 'img',
      'aria-label': 'Canal de informação e margem de Flávio, por recorte'
    });
    svg.append(txt(left, 28, 'TV', { fill: RED, 'font-weight': 700, 'font-size': 13 }));
    svg.append(txt(left + 60, 28, 'REDES SOCIAIS', { fill: BLUE, 'font-weight': 700, 'font-size': 13 }));
    svg.append(txt(width - 20, 28, 'MARGEM DE FLÁVIO NO 2º TURNO', { 'text-anchor': 'end', 'font-weight': 700, 'font-size': 13, fill: INK }));
    rows.forEach((row, index) => {
      const y = 56 + index * rowH;
      const scale = value => (value / 60) * 420;
      svg.append(txt(left - 16, y + 26, row.segment, { 'text-anchor': 'end', 'font-family': SANS, 'font-size': 15, 'font-weight': 700, fill: INK }));
      svg.append(svgEl('rect', { x: left, y: y + 4, width: scale(row.tv), height: 16, fill: RED, opacity: .8 }));
      svg.append(svgEl('rect', { x: left, y: y + 24, width: scale(row.redes), height: 16, fill: BLUE }));
      svg.append(txt(left + scale(row.tv) + 8, y + 17, `${row.tv}`, { fill: RED, 'font-weight': 700 }));
      svg.append(txt(left + scale(row.redes) + 8, y + 37, `${row.redes}`, { fill: BLUE, 'font-weight': 700 }));
      const margin = row.flavio_margin;
      svg.append(txt(width - 20, y + 28, `${margin > 0 ? '+' : ''}${margin}`, { 'text-anchor': 'end', 'font-weight': 700, 'font-size': 26, fill: margin > 0 ? BLUE : RED }));
      svg.append(svgEl('line', { x1: left, y1: y + 50, x2: width - 20, y2: y + 50, stroke: GRID }));
    });
    target.replaceChildren(svg);
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
    } catch (error) {
      console.warn('Os gráficos dinâmicos mantiveram o conteúdo textual de fallback.', error);
    }
  }

  setupReveal();
  setupNavigation();
  loadData();
})();
