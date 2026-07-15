(() => {
  "use strict";

  const NS = "http://www.w3.org/2000/svg";
  const REDUCED = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const colors = {
    lula: "#b5202a",
    flavio: "#1f5fbf",
    gray: "#8a857a",
    gold: "#a06d00",
    green: "#06775a",
    orange: "#ef7622",
    navy: "#08275c",
    blue: "#1f5fbf",
    red: "#b5202a",
    ink: "#101014",
    band: "rgba(181,32,42,.16)",
  };
  // income waffle palette (poorest -> richest)
  const incomeColors = ["#7a1319", "#ef7622", "#1f5fbf", "#06775a"];

  const svgEl = (tag, attrs = {}) => {
    const el = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
    return el;
  };
  const text = (svg, x, y, str, cls = "axis-label", anchor = "middle") => {
    const t = svgEl("text", { x, y, class: cls, "text-anchor": anchor });
    t.textContent = str;
    svg.appendChild(t);
    return t;
  };
  const mount = (id, label, w, h) => {
    const target = document.getElementById(id);
    if (!target) return null;
    target.replaceChildren();
    const svg = svgEl("svg", { viewBox: `0 0 ${w} ${h}`, role: "img", "aria-label": label });
    target.appendChild(svg);
    return svg;
  };
  const br = (n, d = 1) => n.toLocaleString("pt-BR", { minimumFractionDigits: d, maximumFractionDigits: d });
  const sgn = (n, d = 1) => `${n > 0 ? "+" : n < 0 ? "−" : ""}${br(Math.abs(n), d)}`;

  /* ---------- line chart (runoff / first / spontaneous) ---------- */
  const lineChart = (id, dates, series, options = {}) => {
    const w = 760, h = 320;
    const pad = { left: 42, right: 42, top: 26, bottom: 46 };
    const svg = mount(id, options.label || "Série histórica", w, h);
    if (!svg) return;
    const yMax = options.yMax || 55;
    const x = i => pad.left + i * (w - pad.left - pad.right) / (dates.length - 1);
    const y = v => h - pad.bottom - v * (h - pad.top - pad.bottom) / yMax;
    for (let v = 0; v <= yMax; v += 10) {
      svg.appendChild(svgEl("line", { x1: pad.left, y1: y(v), x2: w - pad.right, y2: y(v), class: "gridline" }));
      text(svg, pad.left - 8, y(v) + 4, `${v}%`, "axis-label", "end");
    }
    dates.forEach((d, i) => text(svg, x(i), h - 18, d));
    Object.entries(series).forEach(([name, cfg]) => {
      const pts = cfg.values.map((v, i) => `${x(i)},${y(v)}`).join(" ");
      svg.appendChild(svgEl("polyline", { points: pts, fill: "none", stroke: cfg.color, "stroke-width": cfg.width || 4, "stroke-linejoin": "round", "stroke-linecap": "round" }));
      cfg.values.forEach((v, i) => {
        svg.appendChild(svgEl("circle", { cx: x(i), cy: y(v), r: 4.5, fill: cfg.color, stroke: "#fffaf0", "stroke-width": 1.4 }));
        text(svg, x(i), y(v) - 11, `${v}`, "value-label");
      });
      const last = cfg.values.at(-1);
      const lbl = text(svg, w - pad.right + 4, y(last) + (cfg.offset || 4), name, "series-label", "start");
      lbl.setAttribute("fill", cfg.color);
    });
  };

  /* ---------- gap series with confidence band (STAR of #margem) ---------- */
  const gapBandChart = (id, dates, gap, moe) => {
    const w = 760, h = 340;
    const pad = { left: 46, right: 46, top: 30, bottom: 52 };
    const svg = mount(id, "Vantagem de Lula sobre Flávio no 2º turno com banda de mais ou menos 4,18 pontos", w, h);
    if (!svg) return;
    const yMin = -6, yMax = 12;
    const x = i => pad.left + i * (w - pad.left - pad.right) / (gap.length - 1);
    const y = v => h - pad.bottom - (v - yMin) * (h - pad.top - pad.bottom) / (yMax - yMin);
    for (let v = yMin; v <= yMax; v += 3) {
      svg.appendChild(svgEl("line", { x1: pad.left, y1: y(v), x2: w - pad.right, y2: y(v), class: "gridline" }));
      text(svg, pad.left - 8, y(v) + 4, `${v > 0 ? "+" : ""}${v}`, "axis-label", "end");
    }
    // confidence ribbon gap +/- moe
    const up = gap.map((g, i) => `${x(i)},${y(g + moe)}`);
    const dn = gap.map((g, i) => `${x(i)},${y(g - moe)}`).reverse();
    svg.appendChild(svgEl("polygon", { points: [...up, ...dn].join(" "), fill: colors.band, stroke: "none" }));
    // zero reference (empate real)
    svg.appendChild(svgEl("line", { x1: pad.left, y1: y(0), x2: w - pad.right, y2: y(0), stroke: colors.ink, "stroke-width": 2, "stroke-dasharray": "2 5" }));
    text(svg, pad.left + 3, y(0) - 7, "EMPATE REAL (zero)", "axis-label", "start");
    dates.forEach((d, i) => text(svg, x(i), h - 20, d));
    // gap line
    const pts = gap.map((g, i) => `${x(i)},${y(g)}`).join(" ");
    svg.appendChild(svgEl("polyline", { points: pts, fill: "none", stroke: colors.lula, "stroke-width": 4, "stroke-linejoin": "round", "stroke-linecap": "round" }));
    gap.forEach((g, i) => {
      svg.appendChild(svgEl("circle", { cx: x(i), cy: y(g), r: 5, fill: colors.lula, stroke: "#fffaf0", "stroke-width": 1.5 }));
      text(svg, x(i), y(g) - 12, `+${g}`, "value-label");
    });
    // annotation on last point: band swallows zero
    const li = gap.length - 1;
    const t = text(svg, x(li) - 6, y(gap[li] - moe) + 20, "a banda encosta no zero", "anno", "end");
    t.setAttribute("fill", colors.red);
    text(svg, w - pad.right - 2, y(gap[li] + moe) - 6, "+4,18", "series-label", "end").setAttribute("fill", colors.gray);
  };

  /* ---------- interval scenarios (#margem) ---------- */
  const intervalChart = (id, margin) => {
    const w = 760, h = 250;
    const pad = { left: 112, right: 52, top: 34, bottom: 46 };
    const low = -4, high = 10;
    const x = v => pad.left + (v - low) * (w - pad.left - pad.right) / (high - low);
    const svg = mount(id, "Intervalos de confiança da diferença Lula menos Flávio", w, h);
    if (!svg) return;
    svg.appendChild(svgEl("line", { x1: x(0), y1: 16, x2: x(0), y2: h - pad.bottom, stroke: colors.red, "stroke-width": 2, "stroke-dasharray": "5 4" }));
    text(svg, x(0), 12, "ZERO", "axis-label", "middle");
    for (let v = low; v <= high; v += 2) text(svg, x(v), h - 18, `${v}`);
    margin.scenarios.forEach((row, i) => {
      const y = 52 + i * 52;
      text(svg, pad.left - 14, y + 4, `deff ${br(row.deff, 1)}`, "axis-label", "end");
      svg.appendChild(svgEl("line", { x1: x(row.gap_low), y1: y, x2: x(row.gap_high), y2: y, stroke: colors.navy, "stroke-width": 9, "stroke-linecap": "round" }));
      svg.appendChild(svgEl("circle", { cx: x(margin.observed_gap), cy: y, r: 6, fill: colors.red, stroke: "#fffaf0", "stroke-width": 1.4 }));
      text(svg, x(row.gap_high) + 9, y + 4, `±${br(row.difference_moe, 2)}`, "value-label", "start");
    });
  };

  /* ---------- diverging bars per UF (A1) ---------- */
  const ufDiverging = (id, ufRows) => {
    const rows = [...ufRows].sort((a, b) => b.delta - a.delta);
    const w = 760, rh = 21;
    const pad = { top: 30, bottom: 26 };
    const h = pad.top + pad.bottom + rows.length * rh;
    const center = 300;
    const max = Math.max(...rows.map(r => Math.abs(r.delta))) * 1.1;
    const plot = 300;
    const svg = mount(id, "Diferença entre a participação de cada UF na amostra e no eleitorado", w, h);
    if (!svg) return;
    svg.appendChild(svgEl("line", { x1: center, y1: pad.top - 10, x2: center, y2: h - pad.bottom + 4, stroke: colors.ink, "stroke-width": 1.5 }));
    text(svg, center, 14, "0", "axis-label", "middle");
    text(svg, center - 6, 14, "← sub-representado", "axis-label", "end").setAttribute("fill", colors.blue);
    text(svg, center + 6, 14, "sobre-representado →", "axis-label", "start").setAttribute("fill", colors.red);
    rows.forEach((r, i) => {
      const y = pad.top + i * rh;
      const size = plot * Math.abs(r.delta) / max;
      const x = r.delta >= 0 ? center : center - size;
      const hot = r.uf === "SP";
      // UF label sits on the near side of the bar
      const uflabel = text(svg, r.delta >= 0 ? center - 6 : center + 6, y + rh - 6, r.uf, "value-label", r.delta >= 0 ? "end" : "start");
      uflabel.setAttribute("fill", hot ? colors.red : colors.ink);
      svg.appendChild(svgEl("rect", { x, y: y + 2, width: size, height: rh - 6, fill: r.delta >= 0 ? colors.red : colors.blue, opacity: hot ? 1 : .82 }));
      const vlabel = text(svg, r.delta >= 0 ? x + size + 7 : x - 7, y + rh - 6, `${sgn(r.delta, 2)} pp · ${r.interviews}`, "value-label", r.delta >= 0 ? "start" : "end");
      vlabel.setAttribute("fill", hot ? colors.red : colors.ink);
    });
  };

  /* ---------- slope chart: Nexus meta -> TSE electorate (age) ---------- */
  const declutter = (items, minGap, minY, maxY) => {
    items.sort((a, b) => a.y - b.y);
    for (let i = 1; i < items.length; i++) {
      if (items[i].y < items[i - 1].y + minGap) items[i].y = items[i - 1].y + minGap;
    }
    const overflow = items.length ? items[items.length - 1].y - maxY : 0;
    if (overflow > 0) for (const it of items) it.y -= overflow;
    for (const it of items) if (it.y < minY) it.y = minY;
    return items;
  };
  const slopeChart = (id, rows) => {
    const w = 760, h = 340;
    const pad = { top: 46, bottom: 30, left: 150, right: 132 };
    const svg = mount(id, "Metas etárias da Nexus comparadas ao eleitorado do TSE", w, h);
    if (!svg) return;
    const xL = pad.left, xR = w - pad.right;
    const vals = rows.flatMap(r => [r.nexus, r.official]);
    const yMax = Math.max(...vals) * 1.1, yMin = Math.min(...vals) * .82;
    const y = v => pad.top + (yMax - v) * (h - pad.top - pad.bottom) / (yMax - yMin);
    svg.appendChild(svgEl("line", { x1: xL, y1: pad.top - 16, x2: xL, y2: h - pad.bottom, stroke: colors.ink, "stroke-width": 1 }));
    svg.appendChild(svgEl("line", { x1: xR, y1: pad.top - 16, x2: xR, y2: h - pad.bottom, stroke: colors.ink, "stroke-width": 1 }));
    text(svg, xL, pad.top - 24, "META NEXUS", "axis-label", "middle").setAttribute("fill", colors.orange);
    text(svg, xR, pad.top - 24, "ELEITORADO TSE", "axis-label", "middle").setAttribute("fill", colors.navy);
    rows.forEach(r => {
      const col = r.delta > 0 ? colors.red : colors.blue;
      svg.appendChild(svgEl("line", { x1: xL, y1: y(r.nexus), x2: xR, y2: y(r.official), stroke: col, "stroke-width": 3, opacity: .8 }));
      svg.appendChild(svgEl("circle", { cx: xL, cy: y(r.nexus), r: 4.5, fill: colors.orange }));
      svg.appendChild(svgEl("circle", { cx: xR, cy: y(r.official), r: 4.5, fill: colors.navy }));
    });
    const minY = pad.top - 4, maxY = h - pad.bottom;
    const left = declutter(rows.map(r => ({ y: y(r.nexus), anchor: y(r.nexus), r })), 17, minY, maxY);
    const right = declutter(rows.map(r => ({ y: y(r.official), anchor: y(r.official), r })), 17, minY, maxY);
    left.forEach(it => {
      if (Math.abs(it.y - it.anchor) > 2) svg.appendChild(svgEl("line", { x1: xL - 8, y1: it.anchor, x2: xL - 16, y2: it.y, stroke: colors.gray, "stroke-width": .8 }));
      text(svg, xL - 18, it.y + 4, `${it.r.category} · ${br(it.r.nexus, 0)}%`, "value-label", "end");
    });
    right.forEach(it => {
      if (Math.abs(it.y - it.anchor) > 2) svg.appendChild(svgEl("line", { x1: xR + 8, y1: it.anchor, x2: xR + 16, y2: it.y, stroke: colors.gray, "stroke-width": .8 }));
      text(svg, xR + 18, it.y + 4, `${br(it.r.official, 1)}%`, "value-label", "start");
    });
  };

  /* ---------- waffle: 100 cells PNAD vs Nexus (income) ---------- */
  const largestRemainder = arr => {
    const floors = arr.map(Math.floor);
    let rem = 100 - floors.reduce((a, b) => a + b, 0);
    const order = arr.map((v, i) => ({ i, frac: v - Math.floor(v) })).sort((a, b) => b.frac - a.frac);
    for (let k = 0; k < order.length && rem > 0; k++) { floors[order[k].i]++; rem--; }
    return floors;
  };
  const waffle = (svg, ox, oy, counts, cell, gap, title) => {
    text(svg, ox + (cell + gap) * 5, oy - 12, title, "series-label", "middle");
    let idx = 0;
    const seq = [];
    counts.forEach((c, band) => { for (let k = 0; k < c; k++) seq.push(band); });
    for (let i = 0; i < 100; i++) {
      const col = i % 10, rowN = Math.floor(i / 10);
      svg.appendChild(svgEl("rect", {
        x: ox + col * (cell + gap), y: oy + rowN * (cell + gap),
        width: cell, height: cell, rx: 1.5, fill: incomeColors[seq[i]] || "#ccc",
      }));
      idx++;
    }
  };
  const incomeWaffle = (id, bands) => {
    const w = 760, h = 340;
    const svg = mount(id, "Distribuição de renda domiciliar: PNAD comparada à meta da Nexus", w, h);
    if (!svg) return;
    const pnad = largestRemainder(bands.map(b => b.estimate));
    const nexus = largestRemainder(bands.map(b => b.nexus));
    const cell = 22, gap = 5;
    waffle(svg, 40, 46, pnad, cell, gap, "PNAD · IBGE");
    waffle(svg, 440, 46, nexus, cell, gap, "NEXUS · meta");
    // legend
    bands.forEach((b, i) => {
      const y = 330;
      const x = 40 + i * 185;
      svg.appendChild(svgEl("rect", { x, y: y - 11, width: 13, height: 13, rx: 2, fill: incomeColors[i] }));
      text(svg, x + 19, y, `${b.category}`, "axis-label", "start");
    });
  };

  /* ---------- frozen middle band across income waves (A2) ---------- */
  const frozenIncome = (id, series) => {
    const w = 760, h = 300;
    const pad = { left: 42, right: 118, top: 26, bottom: 44 };
    const waves = Object.keys(series);
    const svg = mount(id, "Faixas de renda declarada ao longo das cinco ondas", w, h);
    if (!svg) return;
    const labels = ["Até 1 SM", "1 a 2 SM", "2 a 5 SM", "5+ SM"];
    const cols = ["#7a1319", "#ef7622", "#b5202a", "#06775a"];
    const yMax = 50;
    const x = i => pad.left + i * (w - pad.left - pad.right) / (waves.length - 1);
    const y = v => h - pad.bottom - v * (h - pad.top - pad.bottom) / yMax;
    for (let v = 0; v <= yMax; v += 10) {
      svg.appendChild(svgEl("line", { x1: pad.left, y1: y(v), x2: w - pad.right, y2: y(v), class: "gridline" }));
      text(svg, pad.left - 8, y(v) + 4, `${v}%`, "axis-label", "end");
    }
    waves.forEach((wv, i) => text(svg, x(i), h - 18, wv));
    labels.forEach((lab, band) => {
      const vals = waves.map(wv => series[wv][band]);
      const frozen = band === 2;
      const pts = vals.map((v, i) => `${x(i)},${y(v)}`).join(" ");
      svg.appendChild(svgEl("polyline", { points: pts, fill: "none", stroke: cols[band], "stroke-width": frozen ? 5 : 2.4, "stroke-linejoin": "round", opacity: frozen ? 1 : .6, "stroke-dasharray": frozen ? "" : "" }));
      vals.forEach((v, i) => svg.appendChild(svgEl("circle", { cx: x(i), cy: y(v), r: frozen ? 4 : 2.6, fill: cols[band] })));
      const last = vals.at(-1);
      const t = text(svg, w - pad.right + 8, y(last) + (band === 1 ? -6 : band === 0 ? 12 : 4), lab, "series-label", "start");
      t.setAttribute("fill", cols[band]);
      if (frozen) t.setAttribute("font-size", "13");
    });
    text(svg, x(2), y(40) - 14, "40% · imóvel nas 5 ondas", "anno", "middle").setAttribute("fill", colors.red);
  };

  /* ---------- BTG profit bars with mandate annotation ---------- */
  const profitBars = (id, values) => {
    const w = 760, rh = 52;
    const pad = { left: 118, right: 60, top: 20, bottom: 20 };
    const h = pad.top + pad.bottom + values.length * rh;
    const svg = mount(id, "Lucro líquido ajustado do BTG por ano, com anotação de mandatos", w, h);
    if (!svg) return;
    const max = Math.max(...values.map(v => v.profit)) * 1.16;
    const scale = v => (w - pad.left - pad.right) * v / max;
    values.forEach((v, i) => {
      const y = pad.top + i * rh;
      const lula = v.year >= 2023;
      text(svg, pad.left - 12, y + rh / 2 + 2, String(v.year), "value-label", "end");
      svg.appendChild(svgEl("rect", { x: pad.left, y: y + 8, width: scale(v.profit), height: rh - 24, fill: lula ? colors.red : colors.blue }));
      text(svg, pad.left + scale(v.profit) + 8, y + rh / 2 + 2, `R$ ${br(v.profit, 1)} bi`, "value-label", "start");
    });
    // mandate brackets on the far left
    const bkt = (y1, y2, label, col) => {
      const bx = 46;
      svg.appendChild(svgEl("path", { d: `M ${bx + 10} ${y1} H ${bx} V ${y2} H ${bx + 10}`, fill: "none", stroke: col, "stroke-width": 1.6 }));
      const t = text(svg, bx - 4, (y1 + y2) / 2, label, "axis-label", "middle");
      t.setAttribute("transform", `rotate(-90 ${bx - 4} ${(y1 + y2) / 2})`);
      t.setAttribute("fill", col);
    };
    const yOf = i => pad.top + i * rh + 8;
    bkt(yOf(0), yOf(1) + rh - 24, "BOLSONARO", colors.blue);
    bkt(yOf(2), yOf(4) + rh - 24, "LULA", colors.red);
  };

  /* ---------- reweight dumbbells over the +/-4,18 band (#reponderacao) ---------- */
  const reweightNames = {
    a: "Publicado · 47×44", b: "Sexo · TSE", c: "Idade · TSE",
    d: "Renda · PNAD", e: "Escolaridade · PNAD", f: "Região · TSE",
    g: "Combinado · raking",
  };
  const reweightChart = (id, reweight, margin) => {
    const rows = reweight.scenarios;
    const band = margin.scenarios[0];
    const baseGap = margin.observed_gap;
    const w = 760, rh = 34;
    const pad = { left: 168, right: 40, top: 52, bottom: 34 };
    const h = pad.top + pad.bottom + rows.length * rh;
    const low = -2, high = 8;
    const svg = mount(id, "Gap de cada cenário de reponderação sobre a banda de mais ou menos 4,18 pontos", w, h);
    if (!svg) return;
    const x = v => pad.left + (v - low) * (w - pad.left - pad.right) / (high - low);
    const plotTop = pad.top - 12, plotBot = h - pad.bottom + 6;
    // confidence band (sampling margin around the published gap)
    svg.appendChild(svgEl("rect", {
      x: x(band.gap_low), y: plotTop, width: x(band.gap_high) - x(band.gap_low),
      height: plotBot - plotTop, fill: colors.band, stroke: "none",
    }));
    text(svg, x(baseGap), pad.top - 34, "margem ±4,18 da diferença (−1,18 a +7,18)", "anno", "middle")
      .setAttribute("fill", colors.gray);
    // gridlines
    for (let v = low; v <= high; v += 2) {
      svg.appendChild(svgEl("line", { x1: x(v), y1: plotTop, x2: x(v), y2: plotBot, class: "gridline" }));
      text(svg, x(v), plotBot + 18, `${v > 0 ? "+" : ""}${v}`);
    }
    // zero reference (empate real)
    svg.appendChild(svgEl("line", { x1: x(0), y1: plotTop, x2: x(0), y2: plotBot, stroke: colors.red, "stroke-width": 2, "stroke-dasharray": "5 4" }));
    text(svg, x(0), pad.top - 16, "EMPATE", "axis-label", "middle").setAttribute("fill", colors.red);
    rows.forEach((r, i) => {
      const y = pad.top + i * rh + rh / 2;
      const base = r.id === "a";
      const col = base ? colors.gray : (r.delta_gap >= 0 ? colors.red : colors.blue);
      const lbl = text(svg, pad.left - 14, y + 4, reweightNames[r.id] || r.id, "value-label", "end");
      lbl.setAttribute("fill", base ? colors.ink : col);
      if (!base) {
        // dumbbell: from the published +3,0 anchor to the reweighted gap
        svg.appendChild(svgEl("line", { x1: x(baseGap), y1: y, x2: x(r.gap), y2: y, stroke: col, "stroke-width": 3, opacity: .55 }));
        svg.appendChild(svgEl("circle", { cx: x(baseGap), cy: y, r: 3.4, fill: colors.gray }));
      }
      svg.appendChild(svgEl("circle", { cx: x(r.gap), cy: y, r: 6, fill: col, stroke: "#fffaf0", "stroke-width": 1.5 }));
      const side = r.gap >= baseGap ? 1 : -1;
      const vlbl = text(svg, x(r.gap) + side * 12, y + 4, sgn(r.gap, 1), "value-label", side > 0 ? "start" : "end");
      vlbl.setAttribute("fill", col);
      if (r.id === "d") text(svg, x(r.gap), y + 20, "quase encosta no zero", "anno", "middle").setAttribute("fill", colors.red);
    });
  };

  /* ---------- table helper ---------- */
  const tableRows = (id, rows, render) => {
    const body = document.getElementById(id);
    if (!body) return;
    body.replaceChildren(...rows.map(r => { const tr = document.createElement("tr"); tr.innerHTML = render(r); return tr; }));
  };

  /* ---------- render everything ---------- */
  const render = data => {
    const dates = data.series.dates;
    lineChart("chart-runoff", dates, {
      "Lula": { values: data.series.runoff.Lula, color: colors.lula, offset: -4 },
      "Flávio": { values: data.series.runoff["Flávio Bolsonaro"], color: colors.flavio, offset: 4 },
    }, { label: "Segundo turno Lula e Flávio", yMax: 55 });
    lineChart("chart-first", dates, {
      "Lula": { values: data.series.first_round.Lula, color: colors.lula, offset: -4 },
      "Flávio": { values: data.series.first_round["Flávio Bolsonaro"], color: colors.flavio, offset: 4 },
    }, { label: "Primeiro turno estimulado", yMax: 50 });
    lineChart("chart-spontaneous", dates, {
      "Lula": { values: data.series.spontaneous.Lula, color: colors.lula, offset: -4 },
      "Flávio": { values: data.series.spontaneous["Flávio Bolsonaro"], color: colors.flavio, offset: 2 },
      "NS/NR": { values: data.series.spontaneous["NS/NR"], color: colors.gray, width: 3, offset: 4 },
    }, { label: "Voto espontâneo", yMax: 40 });

    gapBandChart("chart-gap-band", dates, data.series.runoff.gap, data.margin.scenarios[0].difference_moe);
    intervalChart("chart-margin", data.margin);

    if (data.uf_distribution) {
      ufDiverging("chart-uf", data.uf_distribution.uf);
      tableRows("region-table-body", data.uf_distribution.region, r => `
        <td>${r.region}</td><td class="num">${r.interviews}</td>
        <td class="num">${br(r.sample_pct, 1)}%</td><td class="num">${br(r.electorate_pct, 1)}%</td>
        <td class="num">${r.design_pct}%</td>
        <td class="num ${Math.abs(r.delta) >= 1 ? "bad-cell" : ""}">${sgn(r.delta, 2)}</td>`);
    }

    slopeChart("chart-age", data.tse.age);
    incomeWaffle("chart-income", data.pnad_income.bands);
    frozenIncome("chart-income-frozen", data.income_series);
    profitBars("chart-profit", data.btg.values);

    if (data.reweight) {
      reweightChart("chart-reweight", data.reweight, data.margin);
      tableRows("reweight-table-body", data.reweight.scenarios, r => `
        <td><b>${reweightNames[r.id] || r.id}</b></td>
        <td>${r.ruler ? r.ruler.split(" — ")[0] : (r.id === "g" ? "as 5 margens (IPF)" : "—")}</td>
        <td class="num">${br(r.lula, 1)}</td><td class="num">${br(r.flavio, 1)}</td>
        <td class="num">${sgn(r.gap, 1)}</td>
        <td class="num">${r.id === "a" ? "—" : `${sgn(r.ci95.gap[0], 2)} a ${sgn(r.ci95.gap[1], 2)}`}</td>`);
      const marginName = { sexo: "Sexo", idade: "Idade", escolaridade: "Escolaridade", renda: "Renda", regiao: "Região" };
      tableRows("reweight-validation-body", data.reweight.validation.by_margin, r => `
        <td>${marginName[r.margin] || r.margin} <span class="muted">· p.${r.page}</span></td>
        <td class="num">${br(r.lula, 2)}</td><td class="num">${br(r.flavio, 2)}</td>
        <td class="num ${r.within_0_5 ? "ok-cell" : "bad-cell"}">${r.within_0_5 ? "sim" : "não"}</td>`);
    }

    tableRows("city-table-body", data.cities, r => `
      <td>${r.date}</td><td class="mono">${r.registration}</td>
      <td class="num">${r.interviews.toLocaleString("pt-BR")}</td>
      <td class="num">${r.municipalities}</td>
      <td class="num">${r.singleton_municipalities} (${br(r.singleton_city_pct, 1)}%)</td>
      <td class="num">${br(r.top10_pct, 1)}%</td>`);
    tableRows("overlap-table-body", data.city_overlaps, r => `
      <td>${r.from} → ${r.to}</td><td class="num">${r.intersection}</td>
      <td class="num">${br(r.jaccard, 3)}</td><td class="num">${br(r.current_retained_pct, 1)}%</td>
      <td class="num">+${r.entered} / −${r.left}</td>`);
    tableRows("income-table-body", data.pnad_income.bands, r => `
      <td>${r.category}</td><td class="num">${br(r.estimate, 1)}%</td>
      <td class="num">${br(r.low, 1)}–${br(r.high, 1)}%</td>
      <td class="num">${br(r.nexus, 1)}%</td>
      <td class="num ${Math.abs(r.delta) >= 3 ? "bad-cell" : ""}">${sgn(r.delta, 1)} pp</td>`);
    tableRows("file-table-body", data.files, r => `
      <td class="mono">${r.name}</td><td class="num">${br(r.bytes / 1024, 1)} KB</td>
      <td class="mono">${r.sha256.slice(0, 16)}…</td>`);
  };

  /* ---------- reveal on scroll + count-up ---------- */
  const setupReveal = () => {
    window.__revealReady = true;
    const items = document.querySelectorAll(".reveal");
    if (REDUCED || !("IntersectionObserver" in window)) {
      items.forEach(el => el.classList.add("in"));
      document.querySelectorAll("[data-count-to]").forEach(el => { el.textContent = el.dataset.countText || el.dataset.countTo; });
      return;
    }
    const io = new IntersectionObserver((entries, obs) => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.classList.add("in");
          e.target.querySelectorAll("[data-count-to]").forEach(countUp);
          if (e.target.matches("[data-count-to]")) countUp(e.target);
          obs.unobserve(e.target);
        }
      });
    }, { threshold: 0.16, rootMargin: "0px 0px -8% 0px" });
    items.forEach(el => io.observe(el));
  };
  const counted = new WeakSet();
  const countUp = el => {
    if (counted.has(el)) return;
    counted.add(el);
    const target = parseFloat(el.dataset.countTo);
    const dec = parseInt(el.dataset.countDec || "0", 10);
    const pre = el.dataset.countPre || "";
    const suf = el.dataset.countSuf || "";
    const dur = 1100;
    const start = performance.now();
    const step = now => {
      const p = Math.min(1, (now - start) / dur);
      const eased = 1 - Math.pow(1 - p, 3);
      el.textContent = pre + br(target * eased, dec) + suf;
      if (p < 1) requestAnimationFrame(step);
      else el.textContent = pre + br(target, dec) + suf;
    };
    requestAnimationFrame(step);
  };

  /* ---------- reading progress + TOC active ---------- */
  const setupChrome = () => {
    const bar = document.querySelector(".progress");
    const onScroll = () => {
      const max = document.documentElement.scrollHeight - window.innerHeight;
      if (bar) bar.style.width = `${max > 0 ? (window.scrollY / max) * 100 : 0}%`;
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    const links = [...document.querySelectorAll(".toc a")];
    const map = new Map(links.map(a => [a.getAttribute("href").slice(1), a]));
    if ("IntersectionObserver" in window) {
      const io = new IntersectionObserver(entries => {
        entries.forEach(e => {
          if (e.isIntersecting) {
            links.forEach(a => a.classList.remove("active"));
            const a = map.get(e.target.id);
            if (a) a.classList.add("active");
          }
        });
      }, { rootMargin: "-45% 0px -50% 0px" });
      document.querySelectorAll("section[id]").forEach(s => io.observe(s));
    }
  };

  document.addEventListener("DOMContentLoaded", () => { setupReveal(); setupChrome(); });

  fetch("assets/nexus_btg_0726_data.json")
    .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
    .then(render)
    .catch(err => {
      document.querySelectorAll(".chart").forEach(c => {
        if (!c.children.length) c.innerHTML = `<p class="fallback">Dados interativos indisponíveis: ${err.message}. O texto e as tabelas fixas permanecem válidos.</p>`;
      });
    });
})();
