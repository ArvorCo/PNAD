(() => {
  "use strict";

  const NS = "http://www.w3.org/2000/svg";
  const REDUCED = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const C = {
    lula: "#ce3a22", flavio: "#2f5aa8", amber: "#d99516", pine: "#1e7a58",
    steel: "#2f5aa8", ink: "#131009", gray: "#8a8271",
    band: "rgba(217,149,22,.16)", quaest: "#ce3a22",
  };
  const incomeCols = ["#8a2b17", "#d99516", "#2f5aa8", "#1e7a58"];

  const fmt = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 2 });
  const br = (n, d = 1) => n.toLocaleString("pt-BR", { minimumFractionDigits: d, maximumFractionDigits: d });
  const sgn = (n, d = 1) => `${n > 0 ? "+" : n < 0 ? "−" : ""}${br(Math.abs(n), d)}`;
  const byId = (id) => document.getElementById(id);
  const esc = (v) => String(v).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");

  const el = (tag, attrs = {}) => { const e = document.createElementNS(NS, tag); for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v); return e; };
  const txt = (svg, x, y, s, cls = "axis-label", anchor = "middle") => {
    const t = el("text", { x, y, class: cls, "text-anchor": anchor }); t.textContent = s; svg.appendChild(t); return t;
  };
  const mount = (id, label, w, h) => {
    const target = byId(id); if (!target) return null;
    target.replaceChildren();
    const svg = el("svg", { viewBox: `0 0 ${w} ${h}`, role: "img", "aria-label": label });
    target.appendChild(svg); return svg;
  };

  /* ===================================================================
     SUPLEMENTO TEMÁTICO DE TARIFAS (16/07) — dado editorial estável.
     O data.json descreve o deck da corrida (15/07): 65 de 101 itens.
     O suplemento acendeu 8 itens antes fantasmas; aplicamos a diferença
     aqui para não regenerar o data.json e preservar seu papel de fonte
     do deck original. Sobram 28 itens sem topline (73/101 = 72,3%).
     =================================================================== */
  const SUPPLEMENT = {
    newly_published: [57, 58, 59, 60, 61, 63, 64, 65],
    file: { name: "Quaest_Tarifas_072026.pdf", bytes: 5158217, sha256: "5ed628b0c162267e08d03a6f3c60387a1b7aaa80f50f3efa01ba08db93159351" },
    groups: [
      { name: "Operacionais e perfil", questions: [1, 5, 7], note: "Elegibilidade, ocupação e consentimento de gravação — itens de triagem que nenhum instituto leva a topline." },
      { name: "Bloco tarifário residual", questions: [62], note: "Q62, patriotismo: o único item do bloco EUA/tarifas que o suplemento ainda retém — justo o que armaria o duelo direto Flávio × Lula sobre defender o Brasil." },
      { name: "Michelle, mulheres e Paulo Figueiredo", questions: [77, 80, 81, 82, 83], note: "Voto, gênero e o bloco Paulo Figueiredo seguem inteiros fora, no deck e no suplemento." },
      { name: "Diagnóstico e engajamento", questions: [29, 30, 33, 34, 35, 36, 37, 38, 39], note: "Melhor resultado para o país, expectativa de vencedor e sete ações de participação eleitoral." },
      { name: "País e MEI", questions: [42, 44, 45], note: "Direção do país e duas perguntas sobre política para MEIs." },
      { name: "Economia doméstica", questions: [87, 88], note: "Renda versus preços e situação econômica da família." },
      { name: "Ideologia e voto passado", questions: [92, 93, 94, 100, 101], note: "Esquerda/centro/direita (Q92), afetos partidários e recordação de voto; publicou-se apenas a escala Lulista/Bolsonarista (Q91)." },
    ],
  };

  /* ===================================================================
     HOUSE EFFECT — dados editoriais (estáveis a regenerações do data.json)
     Campo de 2º turno Lula x Flávio, julho/2026 (Wikipedia de agregação,
     conferida caso a caso na imprensa).
     =================================================================== */
  const HOUSE_JULY = [
    { inst: "Quaest", lula: 45, flavio: 37, gap: 8, mode: "presencial", quaest: true },
    { inst: "Ideia", lula: 45, flavio: 40, gap: 5, mode: "telefônico" },
    { inst: "Nexus/BTG", lula: 47, flavio: 44, gap: 3, mode: "presencial" },
    { inst: "Futura/Apex", lula: 46.3, flavio: 46.1, gap: 0.2, mode: "misto" },
  ];
  const FIELD = (() => {
    const others = HOUSE_JULY.filter((r) => !r.quaest);
    const mean = (k) => others.reduce((a, b) => a + b[k], 0) / others.length;
    return { lula: mean("lula"), flavio: mean("flavio"), gap: mean("gap") };
  })();

  /* ---------- house effect: dumbbell de níveis por instituto (estrela) ---------- */
  const houseLevels = (id) => {
    const rows = [...HOUSE_JULY].sort((a, b) => a.flavio - b.flavio);
    const w = 760, rh = 46;
    const pad = { left: 128, right: 54, top: 58, bottom: 20 };
    const h = pad.top + pad.bottom + rows.length * rh;
    const lo = 33, hi = 49;
    const svg = mount(id, "Níveis de Lula e Flávio no 2º turno de julho por instituto; Flávio da Quaest é o menor do campo", w, h);
    if (!svg) return;
    const x = (v) => pad.left + (v - lo) * (w - pad.left - pad.right) / (hi - lo);
    const top = pad.top - 14, bot = h - pad.bottom + 2;
    for (let v = 34; v <= 48; v += 2) {
      svg.appendChild(el("line", { x1: x(v), y1: top, x2: x(v), y2: bot, class: "gridline" }));
      txt(svg, x(v), bot + 16, `${v}`);
    }
    // field-average reference lines (excl. Quaest)
    const ref = (val, label, col) => {
      svg.appendChild(el("line", { x1: x(val), y1: top, x2: x(val), y2: bot, stroke: col, "stroke-width": 1.6, "stroke-dasharray": "4 4", opacity: .9 }));
      txt(svg, x(val), pad.top - 40, label, "axis-label", "middle").setAttribute("fill", col);
    };
    ref(FIELD.flavio, `Flávio · média ${br(FIELD.flavio, 1)}`, C.flavio);
    ref(FIELD.lula, `Lula · média ${br(FIELD.lula, 1)}`, C.lula);
    // header
    txt(svg, pad.left - 12, pad.top - 40, "JULHO 2026", "series-label", "end").setAttribute("fill", C.gray);
    rows.forEach((r, i) => {
      const y = pad.top + i * rh + rh / 2;
      const isQ = r.quaest;
      if (isQ) svg.appendChild(el("rect", { x: 6, y: y - rh / 2 + 3, width: w - 12, height: rh - 6, fill: "rgba(206,58,34,.07)" }));
      const lbl = txt(svg, pad.left - 12, y + 4, r.inst, "value-label", "end");
      lbl.setAttribute("fill", isQ ? C.quaest : C.ink);
      if (isQ) lbl.setAttribute("font-weight", "800");
      // connector
      svg.appendChild(el("line", { x1: x(r.flavio), y1: y, x2: x(r.lula), y2: y, stroke: C.gray, "stroke-width": 2.4, opacity: .5 }));
      // dots
      svg.appendChild(el("circle", { cx: x(r.flavio), cy: y, r: isQ ? 7 : 5.5, fill: C.flavio, stroke: "#fbf6ea", "stroke-width": 1.6 }));
      svg.appendChild(el("circle", { cx: x(r.lula), cy: y, r: isQ ? 7 : 5.5, fill: C.lula, stroke: "#fbf6ea", "stroke-width": 1.6 }));
      // when the two points nearly tie, stack labels vertically to avoid overprinting
      const close = Math.abs(r.lula - r.flavio) < 1.6;
      txt(svg, x(r.flavio), close ? y + 20 : y - 12, br(r.flavio, r.flavio % 1 ? 1 : 0), "value-label").setAttribute("fill", C.flavio);
      txt(svg, x(r.lula), y - 12, br(r.lula, r.lula % 1 ? 1 : 0), "value-label").setAttribute("fill", C.lula);
    });
    // annotation on Quaest Flávio
    const q = rows.find((r) => r.quaest);
    const qy = pad.top + rows.indexOf(q) * rh + rh / 2;
    txt(svg, x(q.flavio) - 10, qy + 22, "menor Flávio do campo", "anno", "start").setAttribute("fill", C.quaest);
  };

  /* ---------- house effect: gap dots (julho) ---------- */
  const houseGap = (id) => {
    const rows = [...HOUSE_JULY].sort((a, b) => a.gap - b.gap);
    const w = 760, h = 150;
    const pad = { left: 40, right: 40, top: 46, bottom: 34 };
    const lo = -1, hi = 9;
    const svg = mount(id, "Vantagem de Lula sobre Flávio no 2º turno de julho por instituto", w, h);
    if (!svg) return;
    const x = (v) => pad.left + (v - lo) * (w - pad.left - pad.right) / (hi - lo);
    const cy = pad.top + 22;
    svg.appendChild(el("line", { x1: pad.left, y1: cy, x2: w - pad.right, y2: cy, stroke: C.gray, "stroke-width": 1.4 }));
    for (let v = 0; v <= 8; v += 2) { svg.appendChild(el("line", { x1: x(v), y1: cy - 6, x2: x(v), y2: cy + 6, stroke: C.gray, "stroke-width": 1 })); txt(svg, x(v), h - 12, `+${v}`); }
    // field mean
    svg.appendChild(el("line", { x1: x(FIELD.gap), y1: pad.top - 12, x2: x(FIELD.gap), y2: cy + 30, stroke: C.gray, "stroke-width": 1.6, "stroke-dasharray": "4 4" }));
    txt(svg, x(FIELD.gap), pad.top - 16, `média do campo +${br(FIELD.gap, 1)}`, "axis-label").setAttribute("fill", C.gray);
    rows.forEach((r) => {
      const isQ = r.quaest;
      svg.appendChild(el("circle", { cx: x(r.gap), cy, r: isQ ? 9 : 6, fill: isQ ? C.quaest : C.flavio, stroke: "#fbf6ea", "stroke-width": 1.6 }));
      const t = txt(svg, x(r.gap), isQ ? cy + 26 : cy - 13, `${r.inst} ${sgn(r.gap, r.gap % 1 ? 1 : 0)}`, "value-label");
      if (isQ) t.setAttribute("fill", C.quaest);
    });
  };

  /* ===================================================================
     TRANSFERÊNCIA DE VOTO — Sankey 1º→2º turno (Lula × Flávio, jul/2026).
     Dados editoriais estáveis (toplines deck págs. 25/37). Nós = FATO;
     TODOS os fluxos são INFERÊNCIA — a Quaest não publica a matriz.
     =================================================================== */
  const SANKEY_COLS = { lula: "#d13f24", flavio: "#4a7fd0", neutro: "#8a8271" };
  const SANKEY = {
    r1: [
      { id: "r1_lula", l: "Lula", v: 40, c: "lula", d: "" },
      { id: "r1_flavio", l: "Flávio", v: 28, c: "flavio", d: "" },
      { id: "r1_outros", l: "Outros", v: 13, c: "neutro", d: "Caiado·Zema·Renan" },
      { id: "r1_indecisos", l: "Indecisos", v: 11, c: "neutro", d: "" },
      { id: "r1_branco", l: "Branco/Nulo", v: 8, c: "neutro", d: "" },
    ],
    r2: [
      { id: "r2_lula", l: "Lula", v: 45, c: "lula", d: "", delta: "+5" },
      { id: "r2_flavio", l: "Flávio", v: 37, c: "flavio", d: "", delta: "+9" },
      { id: "r2_branco", l: "Branco/Nulo", v: 14, c: "neutro", d: "", delta: "+6" },
      { id: "r2_indecisos", l: "Indecisos", v: 4, c: "neutro", d: "", delta: "−7" },
    ],
    links: [
      { s: "r1_lula", t: "r2_lula", v: 40, k: "ret" },
      { s: "r1_flavio", t: "r2_flavio", v: 28, k: "ret" },
      { s: "r1_branco", t: "r2_branco", v: 8, k: "ret" },
      { s: "r1_indecisos", t: "r2_indecisos", v: 4, k: "ret" },
      { s: "r1_outros", t: "r2_flavio", v: 8, k: "tr" },
      { s: "r1_outros", t: "r2_branco", v: 4, k: "tr" },
      { s: "r1_outros", t: "r2_lula", v: 1, k: "tr" },
      { s: "r1_indecisos", t: "r2_lula", v: 4, k: "tr" },
      { s: "r1_indecisos", t: "r2_branco", v: 2, k: "tr" },
      { s: "r1_indecisos", t: "r2_flavio", v: 1, k: "tr" },
    ],
  };
  const deltaColor = (n) => (n.c === "lula" ? "#ef6a52" : n.c === "flavio" ? "#7aa6e6" : "#b3ab98");

  const voteSankey = (id) => {
    const W = 920, H = 520, nodeW = 15, unit = 3.7, gap = 14;
    const pad = { t: 64, b: 26, l: 8, r: 8 };
    const svg = mount(id, "Sankey da transferência de votos do 1º para o 2º turno no cenário Lula × Flávio; nós publicados, todos os fluxos inferidos", W, H);
    if (!svg) return;
    const soft = { lula: "rgba(209,63,36,.32)", flavio: "rgba(74,127,208,.30)", neutro: "rgba(138,130,113,.24)" };
    const stripe = { lula: "rgba(239,106,82,.62)", flavio: "rgba(122,166,230,.58)", neutro: "rgba(167,157,134,.5)" };
    const defs = el("defs");
    ["lula", "flavio", "neutro"].forEach((c) => {
      const p = el("pattern", { id: `skH_${c}`, width: 7, height: 7, patternUnits: "userSpaceOnUse", patternTransform: "rotate(45)" });
      p.appendChild(el("rect", { width: 7, height: 7, fill: soft[c] }));
      p.appendChild(el("rect", { width: 2.6, height: 7, fill: stripe[c] }));
      defs.appendChild(p);
    });
    svg.appendChild(defs);
    const r1 = SANKEY.r1.map((n) => ({ ...n })), r2 = SANKEY.r2.map((n) => ({ ...n }));
    const xL = pad.l + 120, xR = W - pad.r - 108 - nodeW;
    const availH = H - pad.t - pad.b;
    const layout = (list, x) => {
      const total = list.reduce((a, n) => a + n.v * unit, 0) + (list.length - 1) * gap;
      let y = pad.t + (availH - total) / 2;
      list.forEach((n) => { n.x = x; n.y = y; n.h = n.v * unit; n.mid = y + n.h / 2; y += n.h + gap; n.tin = n.y; n.tout = n.y; });
    };
    layout(r1, xL); layout(r2, xR);
    const map = {}; r1.concat(r2).forEach((n) => { map[n.id] = n; });
    // column headers + provenance seals
    [[xL, "1º TURNO"], [xR, "2º TURNO"]].forEach(([x, label]) => {
      txt(svg, x + nodeW / 2, pad.t - 42, label, "series-label").setAttribute("fill", "#cabf9f");
      txt(svg, x + nodeW / 2, pad.t - 26, "FATO", "axis-label").setAttribute("fill", "#7aa6e6");
    });
    txt(svg, (xL + xR + nodeW) / 2, pad.t - 26, "FLUXOS = INFERÊNCIA", "axis-label").setAttribute("fill", "#b7b0a4");
    // flows: retention drawn last so transfers read on top
    const links = SANKEY.links.slice().sort((a, b) => (a.k === "ret" ? 1 : 0) - (b.k === "ret" ? 1 : 0));
    links.forEach((lk) => {
      const s = map[lk.s], t = map[lk.t], w = lk.v * unit, sy = s.tout, ty = t.tin; s.tout += w; t.tin += w;
      const x0 = s.x + nodeW, x1 = t.x, cx = (x0 + x1) / 2;
      const d = `M${x0},${sy}C${cx},${sy} ${cx},${ty} ${x1},${ty}L${x1},${ty + w}C${cx},${ty + w} ${cx},${sy + w} ${x0},${sy + w}Z`;
      svg.appendChild(el("path", { d, fill: `url(#skH_${t.c})`, stroke: stripe[t.c], "stroke-width": 0.8, "stroke-dasharray": "5 4", opacity: lk.k === "tr" ? 0.95 : 0.7 }));
    });
    // solid nodes = FATO
    r1.concat(r2).forEach((n) => { svg.appendChild(el("rect", { x: n.x, y: n.y, width: nodeW, height: Math.max(n.h, 1.5), rx: 2, fill: SANKEY_COLS[n.c] })); });
    const label = (n, side) => {
      const isL = side === "L", tx = isL ? n.x - 10 : n.x + nodeW + 10, anc = isL ? "end" : "start";
      txt(svg, tx, n.mid - 2, n.l, "value-label", anc).setAttribute("fill", "#efe6d4");
      const val = el("text", { x: tx, y: n.mid + 15, class: "value-label", "text-anchor": anc });
      val.setAttribute("fill", "#efe6d4");
      if (!isL && n.delta) {
        val.textContent = `${n.v}% `;
        const ds = el("tspan"); ds.setAttribute("fill", deltaColor(n)); ds.textContent = n.delta; val.appendChild(ds);
      } else { val.textContent = `${n.v}%`; }
      svg.appendChild(val);
      if (n.d) txt(svg, tx, n.mid + 29, n.d, "axis-label", anc).setAttribute("fill", "#a79d86");
    };
    r1.forEach((n) => label(n, "L")); r2.forEach((n) => label(n, "R"));
  };

  /* ---------- right (non-Bolsonaro) segment series: Flávio Mar→Jul ---------- */
  const rightSeriesChart = (id) => {
    const waves = ["Mar", "Abr", "Mai", "Jun", "Jul"], vals = [84, 90, 88, 82, 74];
    const W = 760, H = 262, pad = { left: 42, right: 120, top: 32, bottom: 40 };
    const svg = mount(id, "Voto em Flávio no segmento direita não-bolsonarista de março a julho de 2026", W, H);
    if (!svg) return;
    const lo = 68, hi = 94, blue = "#5f83b3";
    const x = (i) => pad.left + i * (W - pad.left - pad.right) / (waves.length - 1);
    const y = (v) => pad.top + (hi - v) * (H - pad.top - pad.bottom) / (hi - lo);
    for (let v = 70; v <= 90; v += 5) { svg.appendChild(el("line", { x1: pad.left, y1: y(v), x2: W - pad.right, y2: y(v), class: "gridline" })); txt(svg, pad.left - 8, y(v) + 4, `${v}`, "axis-label", "end"); }
    svg.appendChild(el("line", { x1: x(1), y1: y(90), x2: x(4), y2: y(74), stroke: C.quaest, "stroke-width": 1.3, "stroke-dasharray": "4 4", opacity: 0.8 }));
    let d = ""; vals.forEach((v, i) => { d += (i ? "L" : "M") + x(i) + "," + y(v); });
    svg.appendChild(el("path", { d, fill: "none", stroke: blue, "stroke-width": 2.6 }));
    vals.forEach((v, i) => {
      const end = i === 4;
      svg.appendChild(el("circle", { cx: x(i), cy: y(v), r: end ? 6 : 4.5, fill: end ? C.quaest : blue, stroke: "#131009", "stroke-width": 1.5 }));
      txt(svg, x(i), y(v) - 12, `${v}`, "value-label").setAttribute("fill", end ? C.quaest : "#7aa6e6");
      txt(svg, x(i), H - 14, waves[i], "axis-label");
    });
    txt(svg, W - pad.right + 10, y(83) - 4, "queda acumulada", "anno", "start").setAttribute("fill", C.gray);
    txt(svg, W - pad.right + 10, y(83) + 12, "90 → 74 = 3,8–5,3σ", "anno", "start").setAttribute("fill", C.gray);
    txt(svg, W - pad.right + 10, y(83) + 28, "com confundidores", "anno", "start").setAttribute("fill", C.gray);
  };

  /* ---------- interval scenarios (deff) ---------- */
  const intervalChart = (id, margin) => {
    const w = 760, h = 224;
    const pad = { left: 96, right: 58, top: 34, bottom: 44 };
    const lo = 0, hi = 14;
    const svg = mount(id, "Intervalo aproximado da diferença Lula menos Flávio por efeito de desenho", w, h);
    if (!svg) return;
    const x = (v) => pad.left + (v - lo) * (w - pad.left - pad.right) / (hi - lo);
    for (let v = 0; v <= 14; v += 2) { svg.appendChild(el("line", { x1: x(v), y1: 22, x2: x(v), y2: h - pad.bottom, class: "gridline" })); txt(svg, x(v), h - 18, `${v}`); }
    // zero would be off-scale left; mark "não inclui zero" ribbon start
    svg.appendChild(el("line", { x1: x(margin.observed_gap), y1: 18, x2: x(margin.observed_gap), y2: h - pad.bottom, stroke: C.gray, "stroke-width": 1.4, "stroke-dasharray": "3 4" }));
    txt(svg, x(margin.observed_gap), 14, `gap +${br(margin.observed_gap, 0)}`, "axis-label").setAttribute("fill", C.gray);
    margin.scenarios.forEach((row, i) => {
      const y = 50 + i * 50;
      txt(svg, pad.left - 12, y + 4, `deff ${br(row.deff, row.deff % 1 ? 1 : 0)}`, "value-label", "end");
      svg.appendChild(el("line", { x1: x(row.gap_low), y1: y, x2: x(row.gap_high), y2: y, stroke: C.steel, "stroke-width": 9, "stroke-linecap": "round" }));
      svg.appendChild(el("circle", { cx: x(margin.observed_gap), cy: y, r: 6, fill: C.quaest, stroke: "#fbf6ea", "stroke-width": 1.5 }));
      txt(svg, x(row.gap_low) - 8, y + 4, br(row.gap_low, 2), "value-label", "end");
      txt(svg, x(row.gap_high) + 8, y + 4, br(row.gap_high, 2), "value-label", "start");
    });
  };

  /* ---------- income dumbbell (PNAD vs Quaest) ---------- */
  const incomeChart = (id, bands) => {
    const rows = bands;
    const w = 760, rh = 62;
    const pad = { left: 96, right: 60, top: 40, bottom: 24 };
    const h = pad.top + pad.bottom + rows.length * rh;
    const lo = 20, hi = 45;
    const svg = mount(id, "Distribuição de renda familiar em salários mínimos: Quaest comparada à PNAD", w, h);
    if (!svg) return;
    const x = (v) => pad.left + (v - lo) * (w - pad.left - pad.right) / (hi - lo);
    const top = pad.top - 12, bot = h - pad.bottom + 2;
    for (let v = 20; v <= 45; v += 5) { svg.appendChild(el("line", { x1: x(v), y1: top, x2: x(v), y2: bot, class: "gridline" })); txt(svg, x(v), bot + 16, `${v}%`); }
    // color legend (centered) — avoids implying a fixed left/right axis order
    const legX = (pad.left + w - pad.right) / 2;
    svg.appendChild(el("circle", { cx: legX - 92, cy: pad.top - 24, r: 5.5, fill: C.pine }));
    txt(svg, legX - 82, pad.top - 20, "PNAD", "series-label", "start").setAttribute("fill", C.pine);
    svg.appendChild(el("circle", { cx: legX + 24, cy: pad.top - 24, r: 5.5, fill: C.quaest }));
    txt(svg, legX + 34, pad.top - 20, "QUAEST", "series-label", "start").setAttribute("fill", C.quaest);
    rows.forEach((r, i) => {
      const y = pad.top + i * rh + rh / 2;
      const pnad = r.estimate ?? r.official;
      txt(svg, pad.left - 12, y - 6, r.category, "value-label", "end");
      const big = Math.abs(r.delta) >= 3;
      txt(svg, pad.left - 12, y + 12, `${sgn(r.delta, 2)} pp`, "axis-label", "end").setAttribute("fill", big ? C.quaest : C.gray);
      svg.appendChild(el("line", { x1: x(pnad), y1: y, x2: x(r.quaest), y2: y, stroke: big ? C.quaest : C.gray, "stroke-width": 3, opacity: .55 }));
      svg.appendChild(el("circle", { cx: x(pnad), cy: y, r: 6.5, fill: C.pine, stroke: "#fbf6ea", "stroke-width": 1.5 }));
      svg.appendChild(el("circle", { cx: x(r.quaest), cy: y, r: 6.5, fill: C.quaest, stroke: "#fbf6ea", "stroke-width": 1.5 }));
      txt(svg, x(pnad), y - 12, `${br(pnad, 1)}`, "value-label").setAttribute("fill", C.pine);
      txt(svg, x(r.quaest), y - 12, `${br(r.quaest, 0)}`, "value-label").setAttribute("fill", C.quaest);
    });
  };

  /* ---------- finance bars with 2020-21 discontinuity ---------- */
  const financeChart = (id, fin) => {
    const series = fin.annual.map((r) => ({ label: String(r.year), value: r.annual_million, year: r.year }));
    series.push({ label: "1T26", value: fin.q1_2026_million, year: 2026 });
    const w = 760, h = 320;
    const pad = { left: 46, right: 20, top: 26, bottom: 44 };
    const svg = mount(id, "Lucro líquido do Banco Genial por ano em R$ milhões", w, h);
    if (!svg) return;
    const lo = -50, hi = 20;
    const y = (v) => pad.top + (hi - v) * (h - pad.top - pad.bottom) / (hi - lo);
    const n = series.length;
    const bandW = (w - pad.left - pad.right) / n;
    for (let v = -50; v <= 20; v += 10) { svg.appendChild(el("line", { x1: pad.left, y1: y(v), x2: w - pad.right, y2: y(v), class: "gridline" })); txt(svg, pad.left - 8, y(v) + 4, `${v}`, "axis-label", "end"); }
    // zero baseline
    svg.appendChild(el("line", { x1: pad.left, y1: y(0), x2: w - pad.right, y2: y(0), stroke: C.ink, "stroke-width": 1.6 }));
    series.forEach((s, i) => {
      const cx = pad.left + bandW * (i + 0.5);
      const bw = Math.min(46, bandW * 0.5);
      const pos = s.value >= 0;
      const yTop = pos ? y(s.value) : y(0);
      const hgt = Math.abs(y(s.value) - y(0));
      svg.appendChild(el("rect", { x: cx - bw / 2, y: yTop, width: bw, height: Math.max(1, hgt), fill: pos ? C.pine : C.quaest }));
      txt(svg, cx, pos ? yTop - 7 : yTop + hgt + 15, `${s.value > 0 ? "+" : ""}${br(s.value, 1)}`, "value-label").setAttribute("fill", pos ? C.pine : C.quaest);
      txt(svg, cx, h - 18, s.label, "axis-label");
    });
    // discontinuity between 2019 (i=0) and 2022 (i=1)
    const gx = pad.left + bandW * 1;
    svg.appendChild(el("path", { d: `M ${gx - 5} ${pad.top} l -6 ${h - pad.top - pad.bottom} M ${gx + 5} ${pad.top} l -6 ${h - pad.top - pad.bottom}`, stroke: C.gray, "stroke-width": 1.4, "stroke-dasharray": "3 3", fill: "none", opacity: .8 }));
    txt(svg, gx, pad.top - 8, "2020–21 s/ dados no IF.data", "anno", "middle").setAttribute("fill", C.gray);
  };

  /* ---------- region diverging (TSE) ---------- */
  const regionDiverging = (id, rows) => {
    const data = [...rows].sort((a, b) => b.delta - a.delta);
    const w = 760, rh = 34;
    const pad = { top: 30, bottom: 12 };
    const h = pad.top + pad.bottom + data.length * rh;
    const center = 300, plot = 300;
    const max = Math.max(...data.map((r) => Math.abs(r.delta))) * 1.15;
    const svg = mount(id, "Diferença entre a participação de cada região na amostra Quaest e no eleitorado do TSE", w, h);
    if (!svg) return;
    svg.appendChild(el("line", { x1: center, y1: pad.top - 8, x2: center, y2: h - pad.bottom, stroke: C.ink, "stroke-width": 1.5 }));
    txt(svg, center - 6, 16, "← sub-representado", "axis-label", "end").setAttribute("fill", C.steel);
    txt(svg, center + 6, 16, "sobre-representado →", "axis-label", "start").setAttribute("fill", C.quaest);
    data.forEach((r, i) => {
      const y = pad.top + i * rh;
      const size = plot * Math.abs(r.delta) / max;
      const x = r.delta >= 0 ? center : center - size;
      svg.appendChild(el("rect", { x, y: y + 4, width: size, height: rh - 12, fill: r.delta >= 0 ? C.quaest : C.steel, opacity: .85 }));
      txt(svg, r.delta >= 0 ? center - 8 : center + 8, y + rh - 8, r.category, "value-label", r.delta >= 0 ? "end" : "start");
      txt(svg, r.delta >= 0 ? x + size + 8 : x - 8, y + rh - 8, `${sgn(r.delta, 2)} pp`, "value-label", r.delta >= 0 ? "start" : "end");
    });
  };

  /* ---------- hydration of data.json ---------- */
  const benchmarkRows = (rows) => rows.map((r) => `
    <tr><td>${esc(r.category)}</td><td class="num">${fmt.format(r.quaest)}%</td>
    <td class="num">${fmt.format(r.official ?? r.estimate)}%</td>
    <td class="num ${Math.abs(r.delta) >= 1 ? "bad-cell" : "ok-cell"}">${r.delta > 0 ? "+" : ""}${fmt.format(r.delta)}</td></tr>`).join("");

  const setText = (id, v) => { const e = byId(id); if (e) e.textContent = v; };

  const renderCoverage = (cov) => {
    // aplica o suplemento de 16/07 sobre a base do deck da corrida (data.json)
    const lit = SUPPLEMENT.newly_published.filter((id) => cov.unpublished_ids.includes(id));
    const published = cov.published + lit.length;
    const unpublished = cov.unpublished - lit.length;
    const pct = Math.round((1000 * published) / cov.total_numbered_questions) / 10;
    const root = byId("ghost-groups");
    if (root) root.innerHTML = SUPPLEMENT.groups.map((g) => {
      const op = g.name.toLowerCase().includes("operacion");
      return `<article class="ghost-group${op ? " op" : ""}"><h3>${esc(g.name)}</h3>
        <div class="q-list">${g.questions.map((q) => `<span class="q-pill">Q${q}</span>`).join("")}</div>
        <p>${esc(g.note)}</p></article>`;
    }).join("");
    setText("coverage-published", published);
    setText("coverage-unpublished", unpublished);
    setText("coverage-percent", `${fmt.format(pct)}%`);
    const bar = byId("coverage-bar");
    if (bar) {
      const tot = published + unpublished;
      bar.innerHTML = `<span class="cov-pub" style="flex:${published}">${published} publicados</span><span class="cov-unpub" style="flex:${unpublished}">${unpublished} sem topline</span>`;
      bar.setAttribute("aria-label", `${published} de ${tot} itens publicados; ${unpublished} sem topline`);
    }
  };

  const renderBenchmarks = (b) => {
    const set = (id, rows) => { const e = byId(id); if (e) e.innerHTML = benchmarkRows(rows); };
    set("benchmark-sex", b.tse.sex);
    set("benchmark-age", b.tse.age);
    set("benchmark-region", b.tse.region);
    set("benchmark-income", b.pnad_income.bands);
    setText("tse-total", fmt.format(b.tse.resident_electors));
    regionDiverging("chart-region", b.tse.region);
    incomeChart("chart-income", b.pnad_income.bands);
  };

  const renderVote = (v) => {
    setText("first-gap", `${v.first_round.gap.at(-1)} p.p.`);
    setText("runoff-gap", `${v.runoff.gap.at(-1)} p.p.`);
    const best = v.runoff_july.reduce((a, b) => (a.opponent_pct > b.opponent_pct ? a : b));
    setText("best-opponent", best.opponent.split(" ")[0]);
    const bars = byId("runoff-bars");
    if (bars) bars.innerHTML = v.runoff_july.map((r) => `
      <div class="bar-row"><span>${esc(r.opponent)}</span>
      <span class="bar-track"><span class="bar-fill" style="width:${2 * r.opponent_pct}%"></span></span>
      <span class="bar-value">${r.opponent_pct}%</span></div>`).join("");
  };

  const renderTerritory = (t) => {
    const c = t.comparison;
    const valid = Object.entries(t.ibge_validation.statuses)
      .filter(([s]) => s !== "api_error" && s !== "absent_from_current_mesh")
      .reduce((a, [, n]) => a + n, 0);
    const total = Object.values(t.ibge_validation.statuses).reduce((a, n) => a + n, 0);
    setText("territory-common-municipalities", c.common_municipalities);
    setText("territory-common-neighborhoods", c.common_municipality_neighborhoods);
    setText("territory-common-sectors", c.common_exact_sectors);
    setText("territory-validated", `${valid}/${total}`);
    const ov = byId("territory-overlaps");
    if (ov) ov.innerHTML = c.common_neighborhood_details.map((r) => `
      <tr><td>${esc(r.municipality)} · ${esc(r.neighborhood_july)}</td>
      <td class="mono">${esc(r.june_sectors.join(", "))}</td>
      <td class="mono">${esc(r.july_sectors.join(", "))}</td>
      <td class="${r.same_exact_sector ? "st-partial" : "st-pass"}">${r.same_exact_sector ? "sim" : "não"}</td></tr>`).join("");
    const reg = byId("territory-regions");
    if (reg) {
      const order = ["Sudeste", "Nordeste", "Sul", "Norte", "Centro-Oeste"];
      reg.innerHTML = order.map((region) => {
        const jun = t.rounds.june.regions[region], jul = t.rounds.july.regions[region];
        return `<tr><td>${esc(region)}</td><td class="num">${jun}</td><td class="num">${jul}</td><td class="num">${fmt.format(100 * jul / t.rounds.july.sectors)}%</td></tr>`;
      }).join("");
    }
    const cap = byId("territory-capitals");
    if (cap) {
      const juneMap = new Map(t.capitals.june.map((r) => [r.municipality_code, r]));
      const common = t.capitals.july.filter((r) => juneMap.has(r.municipality_code))
        .sort((a, b) => b.sectors - a.sectors || a.municipality.localeCompare(b.municipality, "pt-BR"));
      cap.innerHTML = common.map((r) => {
        const old = juneMap.get(r.municipality_code);
        const moe = (1.959964 * Math.sqrt(0.25 / r.interviews) * 100);
        return `<tr><td>${esc(r.municipality)}</td><td class="num">${old.sectors}</td><td class="num">${r.sectors}</td><td class="num">${r.interviews}</td><td class="num">±${br(moe, 1)}</td></tr>`;
      }).join("");
    }
  };

  const renderManifest = (files) => {
    const body = byId("manifest");
    // acrescenta o suplemento de tarifas (16/07) ao pacote julho
    const all = files.concat([SUPPLEMENT.file]);
    if (body) body.innerHTML = all.map((f) => `<tr><td class="mono">${esc(f.name)}</td><td class="num">${fmt.format(f.bytes)}</td><td class="mono">${esc(f.sha256.slice(0, 20))}…</td></tr>`).join("");
  };

  const renderDiagnostics = (q) => {
    setText("template-total", q.template_residue.total);
    setText("template-item", q.template_residue.trazer_item_aqui);
    setText("template-opcao", q.template_residue.trazer_opcao_aqui);
    setText("questionnaire-title", q.pdf_metadata_title);
  };

  const renderMargin = (m) => { setText("srs-moe", `±${fmt.format(m.srs_worst_case_moe)}`); intervalChart("chart-margin", m); };

  /* ---------- reveal + count-up ---------- */
  const counted = new WeakSet();
  const countUp = (e) => {
    if (counted.has(e)) return; counted.add(e);
    const target = parseFloat(e.dataset.countTo);
    const dec = parseInt(e.dataset.countDec || "0", 10);
    const pre = e.dataset.countPre || "", suf = e.dataset.countSuf || "";
    const start = performance.now(), dur = 1000;
    const step = (now) => {
      const p = Math.min(1, (now - start) / dur), ease = 1 - Math.pow(1 - p, 3);
      e.textContent = pre + br(target * ease, dec) + suf;
      if (p < 1) requestAnimationFrame(step); else e.textContent = pre + br(target, dec) + suf;
    };
    requestAnimationFrame(step);
  };
  const setupReveal = () => {
    window.__revealReady = true;
    const items = document.querySelectorAll(".reveal");
    if (REDUCED || !("IntersectionObserver" in window)) {
      items.forEach((e) => e.classList.add("in"));
      document.querySelectorAll("[data-count-to]").forEach((e) => { e.textContent = (e.dataset.countPre || "") + br(parseFloat(e.dataset.countTo), parseInt(e.dataset.countDec || "0", 10)) + (e.dataset.countSuf || ""); });
      return;
    }
    const io = new IntersectionObserver((entries, obs) => {
      entries.forEach((en) => {
        if (en.isIntersecting) {
          en.target.classList.add("in");
          en.target.querySelectorAll("[data-count-to]").forEach(countUp);
          if (en.target.matches("[data-count-to]")) countUp(en.target);
          obs.unobserve(en.target);
        }
      });
    }, { threshold: 0.14, rootMargin: "0px 0px -8% 0px" });
    items.forEach((e) => io.observe(e));
  };

  /* ---------- chrome: progress + TOC active ---------- */
  const setupChrome = () => {
    const bar = document.querySelector(".progress");
    const onScroll = () => { const max = document.documentElement.scrollHeight - window.innerHeight; if (bar) bar.style.width = `${max > 0 ? (window.scrollY / max) * 100 : 0}%`; };
    window.addEventListener("scroll", onScroll, { passive: true }); onScroll();
    const links = [...document.querySelectorAll(".toc a")];
    const map = new Map(links.map((a) => [a.getAttribute("href").slice(1), a]));
    if ("IntersectionObserver" in window) {
      const io = new IntersectionObserver((entries) => {
        entries.forEach((e) => { if (e.isIntersecting) { links.forEach((a) => a.classList.remove("active")); const a = map.get(e.target.id); if (a) a.classList.add("active"); } });
      }, { rootMargin: "-45% 0px -50% 0px" });
      document.querySelectorAll("section[id]").forEach((s) => io.observe(s));
    }
  };

  document.addEventListener("DOMContentLoaded", () => { setupReveal(); setupChrome(); voteSankey("chart-sankey"); rightSeriesChart("chart-right-series"); houseLevels("chart-house-levels"); houseGap("chart-house-gap"); });

  fetch("assets/quaest_0726_data.json")
    .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
    .then((data) => {
      renderCoverage(data.publication_coverage);
      renderMargin(data.margin);
      renderBenchmarks(data.benchmarks);
      renderVote(data.vote);
      renderTerritory(data.territory);
      renderManifest(data.manifest);
      renderDiagnostics(data.questionnaire);
      financeChart("chart-finance", data.financials);
      document.documentElement.dataset.evidence = "loaded";
    })
    .catch((err) => {
      const warn = byId("data-warning");
      if (warn) { warn.hidden = false; warn.textContent = `A camada dinâmica não carregou: ${err.message}. Os achados essenciais permanecem no texto.`; }
      document.querySelectorAll(".chart").forEach((c) => { if (!c.children.length) c.innerHTML = `<p class="fallback">Dados interativos indisponíveis. O texto e as tabelas fixas permanecem válidos.</p>`; });
    });
})();
