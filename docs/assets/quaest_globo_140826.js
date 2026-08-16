(function () {
  "use strict";

  var DATA_URL = "assets/quaest_globo_140826_data.json";
  var STRATEGY_URL = "assets/quaest_globo_140826_estrategia.json";

  // Os dados vão embutidos na própria página. Sem isso, abrir o arquivo direto
  // do disco bloqueia o fetch e a página inteira cai no texto alternativo.
  function inline(id) {
    var node = document.getElementById(id);
    if (!node || !node.textContent.trim()) return null;
    try { return JSON.parse(node.textContent); } catch (error) { return null; }
  }

  function load(id, url) {
    var embedded = inline(id);
    if (embedded) return Promise.resolve(embedded);
    return fetch(url).then(function (response) {
      if (!response.ok) throw new Error(url + " " + response.status);
      return response.json();
    });
  }

  function el(name, attrs, text) {
    var node = document.createElement(name);
    Object.keys(attrs || {}).forEach(function (key) {
      if (key === "class") node.className = attrs[key];
      else node.setAttribute(key, attrs[key]);
    });
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function renderRanks(data) {
    var root = document.getElementById("strength-chart");
    if (!root) return;
    var items = Object.keys(data.segments["Flávio_margin"]).map(function (name) {
      return [name, data.segments["Flávio_margin"][name]];
    }).sort(function (a, b) { return b[1] - a[1]; });
    var chart = el("div", { class: "rank-chart" });
    items.forEach(function (item) {
      var row = el("div", { class: "rank-row" });
      var bar = el("div", { class: "axis-bar", "aria-hidden": "true" });
      var fill = el("span", { class: item[1] >= 0 ? "positive" : "negative" });
      fill.style.width = Math.min(50, Math.abs(item[1]) * 1.35) + "%";
      bar.appendChild(fill);
      row.appendChild(el("b", {}, item[0]));
      row.appendChild(bar);
      row.appendChild(el("output", {}, (item[1] > 0 ? "+" : "") + item[1] + " pp"));
      chart.appendChild(row);
    });
    root.replaceChildren(chart);
  }

  function renderGaps(data) {
    var root = document.getElementById("gap-chart");
    if (!root) return;
    var gaps = data.conversion_gap.segment_gaps;
    var runoff = data.segments.runoff;
    var disapproval = data.approval.disapproval;
    var names = Object.keys(gaps).sort(function (a, b) { return gaps[b] - gaps[a]; });
    var chart = el("div", { class: "gap-chart" });
    names.forEach(function (name) {
      var row = el("div", { class: "gap-row" });
      var track = el("div", { class: "gap-track", "aria-hidden": "true" });
      var dis = el("span", { class: "disapproval" });
      var vote = el("span", { class: "vote" });
      dis.style.width = disapproval[name] + "%";
      vote.style.width = runoff[name][1] + "%";
      track.appendChild(dis);
      track.appendChild(vote);
      row.appendChild(el("b", {}, name));
      row.appendChild(track);
      row.appendChild(el("output", {}, (gaps[name] > 0 ? "+" : "") + gaps[name]));
      chart.appendChild(row);
    });
    root.replaceChildren(chart);
  }

  function renderChannels(data) {
    var root = document.getElementById("channel-chart");
    if (!root) return;
    var segments = data.channels.segments;
    var names = ["60 anos ou mais", "Fundamental", "Até 2 SM", "Mulheres", "Independente", "Homens", "Superior", "16 a 34 anos", "Direita não bolsonarista"];
    var chart = el("div", { class: "channel-chart" });
    names.forEach(function (name) {
      var values = segments[name];
      var row = el("div", { class: "channel-row" });
      var track = el("div", { class: "channel-track" });
      var social = el("span", { class: "social" }, "redes " + values[0]);
      var tv = el("span", { class: "tv" }, "TV " + values[1]);
      social.style.width = Math.max(28, values[0] * 1.65) + "%";
      social.style.justifySelf = "end";
      tv.style.width = Math.max(28, values[1] * 1.65) + "%";
      track.appendChild(social);
      track.appendChild(tv);
      row.appendChild(el("b", {}, name));
      row.appendChild(track);
      row.appendChild(el("output", {}, (values[0] - values[1] > 0 ? "+" : "") + (values[0] - values[1])));
      chart.appendChild(row);
    });
    root.replaceChildren(chart);
  }

  function svgNode(name, attrs, text) {
    var node = document.createElementNS("http://www.w3.org/2000/svg", name);
    Object.keys(attrs || {}).forEach(function (key) { node.setAttribute(key, attrs[key]); });
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function ribbonPath(x1, x2, sy0, sy1, ty0, ty1) {
    var c1 = x1 + (x2 - x1) * .44;
    var c2 = x1 + (x2 - x1) * .56;
    return [
      "M", x1, sy0, "C", c1, sy0, c2, ty0, x2, ty0,
      "L", x2, ty1, "C", c2, ty1, c1, sy1, x1, sy1, "Z"
    ].join(" ");
  }

  function renderTransfer(data) {
    var root = document.getElementById("transfer-chart");
    if (!root) return;
    var transfer = data.transfer;
    var rows = Object.keys(transfer.sources);
    var targets = Object.keys(transfer.targets);
    var width = 960, top = 55, usable = 500, scale = usable / 100;
    var x1 = 145, x2 = 815;
    var svg = svgNode("svg", { viewBox: "0 0 " + width + " 620", role: "img", "aria-labelledby": "transfer-title transfer-desc" });
    svg.appendChild(svgNode("title", { id: "transfer-title" }, "Transferência estimada do primeiro para o segundo turno"));
    svg.appendChild(svgNode("desc", { id: "transfer-desc" }, "Todas as fitas são estimadas por IPF e fecham exatamente as margens publicadas de 38 a 31 no primeiro turno e 43 a 40 no segundo."));
    var defs = svgNode("defs");
    var colors = ["#d9473f", "#2267ee", "#7a8790", "#d89a24"];
    targets.forEach(function (target, index) {
      var pattern = svgNode("pattern", { id: "hatch-" + index, width: "9", height: "9", patternUnits: "userSpaceOnUse", patternTransform: "rotate(28)" });
      pattern.appendChild(svgNode("rect", { width: "9", height: "9", fill: colors[index], opacity: ".70" }));
      pattern.appendChild(svgNode("line", { x1: "0", y1: "0", x2: "0", y2: "9", stroke: "#fff", "stroke-width": "3", opacity: ".65" }));
      defs.appendChild(pattern);
    });
    svg.appendChild(defs);
    var sourceY = {}, targetY = {}, sourceCursor = top, targetCursor = top;
    rows.forEach(function (row) { sourceY[row] = sourceCursor; sourceCursor += transfer.sources[row] * scale; });
    targets.forEach(function (target) { targetY[target] = targetCursor; targetCursor += transfer.targets[target] * scale; });
    var sourceOffsets = {}, targetOffsets = {};
    rows.forEach(function (row) { sourceOffsets[row] = 0; });
    targets.forEach(function (target) { targetOffsets[target] = 0; });
    rows.forEach(function (row) {
      targets.forEach(function (target, targetIndex) {
        var value = transfer.matrix[row][target];
        if (value <= .005) return;
        var sy0 = sourceY[row] + sourceOffsets[row] * scale;
        var sy1 = sy0 + value * scale;
        var ty0 = targetY[target] + targetOffsets[target] * scale;
        var ty1 = ty0 + value * scale;
        sourceOffsets[row] += value;
        targetOffsets[target] += value;
        svg.appendChild(svgNode("path", { d: ribbonPath(x1, x2, sy0, sy1, ty0, ty1), fill: "url(#hatch-" + targetIndex + ")", class: "flow" }));
      });
    });
    rows.forEach(function (row) {
      var y = sourceY[row], height = transfer.sources[row] * scale;
      svg.appendChild(svgNode("rect", { x: x1 - 12, y: y, width: 12, height: Math.max(1, height), fill: "#152b3d" }));
      svg.appendChild(svgNode("text", { x: x1 - 18, y: y + height / 2 - 1, "text-anchor": "end", class: "node-label" }, row));
      svg.appendChild(svgNode("text", { x: x1 - 18, y: y + height / 2 + 13, "text-anchor": "end", class: "node-value" }, transfer.sources[row].toFixed(0) + "%"));
    });
    targets.forEach(function (target, index) {
      var y = targetY[target], height = transfer.targets[target] * scale;
      svg.appendChild(svgNode("rect", { x: x2, y: y, width: 12, height: height, fill: colors[index] }));
      svg.appendChild(svgNode("text", { x: x2 + 18, y: y + height / 2 - 1, class: "node-label" }, target));
      svg.appendChild(svgNode("text", { x: x2 + 18, y: y + height / 2 + 13, class: "node-value" }, transfer.targets[target].toFixed(0) + "%"));
    });
    svg.appendChild(svgNode("text", { x: x1, y: 30, "text-anchor": "middle", class: "node-label" }, "1º turno publicado"));
    svg.appendChild(svgNode("text", { x: x2, y: 30, "text-anchor": "middle", class: "node-label" }, "2º turno publicado"));
    root.replaceChildren(svg);
  }

  function pct(value) { return (value > 0 ? "+" : "") + value; }

  function renderMap(strategy) {
    var root = document.getElementById("map-chart");
    if (!root) return;
    var cuts = strategy.third_way_geography.cuts;
    var order = ["Sul", "Sudeste", "Mais de 5 SM", "2 a 5 SM", "Centro-Oeste/Norte", "Até 2 SM", "Nordeste"];
    var chart = el("div", { class: "map-chart" });
    order.forEach(function (name) {
      var cut = cuts[name];
      if (!cut) return;
      var row = el("div", { class: "map-row" });
      row.appendChild(el("b", {}, name));
      var track = el("div", { class: "map-track", "aria-hidden": "true" });
      [["lula", cut.Lula], ["flavio", cut["Flávio"]], ["third", cut.third_way], ["none", cut.non_choice]].forEach(function (pair) {
        var span = el("span", { class: pair[0] }, String(pair[1]));
        span.style.width = pair[1] + "%";
        track.appendChild(span);
      });
      row.appendChild(track);
      row.appendChild(el("output", { class: cut.flavio_margin >= 0 ? "up" : "down" }, pct(cut.flavio_margin)));
      chart.appendChild(row);
    });
    var key = el("p", { class: "map-key" });
    ["lula|Lula", "flavio|Flávio", "third|terceira via", "none|indeciso e branco"].forEach(function (item) {
      var parts = item.split("|");
      key.appendChild(el("span", { class: parts[0] }, parts[1]));
    });
    chart.appendChild(key);
    root.replaceChildren(chart);
  }

  function renderFirmness(strategy) {
    var root = document.getElementById("firmness-chart");
    if (!root) return;
    var firmness = strategy.vote_firmness;
    var order = ["Zema", "Caiado", "Renan", "Flávio", "Lula"];
    var chart = el("div", { class: "firmness-chart" });
    order.forEach(function (name) {
      var series = firmness.mutable[name];
      var last = series[series.length - 1];
      var row = el("div", { class: "firmness-row" });
      row.appendChild(el("b", {}, name));
      var bar = el("div", { class: "firmness-bar", "aria-hidden": "true" });
      var fill = el("span", { class: last >= 40 ? "soft" : "hard" });
      fill.style.width = last + "%";
      bar.appendChild(fill);
      row.appendChild(bar);
      row.appendChild(el("output", {}, last + "%"));
      row.appendChild(el("small", {}, "ondas: " + series.join(" · ") + " · ME ±" + firmness.moe[name]));
      chart.appendChild(row);
    });
    root.replaceChildren(chart);
  }

  function renderEquation(strategy) {
    var root = document.getElementById("equation-chart");
    if (!root) return;
    var single = strategy.single_round;
    var chart = el("div", { class: "equation-chart" });
    single.grid.forEach(function (step) {
      var row = el("div", { class: "equation-row" });
      row.appendChild(el("b", {}, step.third_way_capture_pct + "% da terceira via"));
      var track = el("div", { class: "equation-track", "aria-hidden": "true" });
      var got = el("span", { class: "got" });
      var gap = el("span", { class: "gap" });
      got.style.width = (100 * step.captured_points / single.points_needed) + "%";
      gap.style.width = (100 * step.still_missing_points / single.points_needed) + "%";
      track.appendChild(got);
      track.appendChild(gap);
      row.appendChild(track);
      row.appendChild(el("output", {}, step.still_missing_points > 0 ? "faltam " + step.still_missing_points.toFixed(2) : "fecha"));
      chart.appendChild(row);
    });
    root.replaceChildren(chart);
  }

  function renderPremium(strategy) {
    var root = document.getElementById("premium-chart");
    if (!root) return;
    var cuts = strategy.inevitability_premium.cuts;
    var names = Object.keys(cuts).sort(function (a, b) { return cuts[b].spread - cuts[a].spread; });
    var chart = el("div", { class: "premium-chart" });
    names.forEach(function (name) {
      var cut = cuts[name];
      var row = el("div", { class: "premium-row" });
      row.appendChild(el("b", {}, name));
      var track = el("div", { class: "premium-track", "aria-hidden": "true" });
      var down = el("span", { class: "down" });
      var up = el("span", { class: "up" });
      down.style.width = Math.abs(cut.flavio_premium) * 1.6 + "%";
      up.style.width = cut.lula_premium * 1.6 + "%";
      track.appendChild(down);
      track.appendChild(up);
      row.appendChild(track);
      row.appendChild(el("output", {}, pct(cut.flavio_premium) + " / " + pct(cut.lula_premium)));
      chart.appendChild(row);
    });
    root.replaceChildren(chart);
  }

  function renderPlan(strategy) {
    var root = document.getElementById("plan-ledger");
    if (!root) return;
    var ledger = el("div", { class: "ledger" });
    strategy.plan_crosswalk.forEach(function (item) {
      var row = el("div", { class: "ledger-row plan-row" });
      row.appendChild(el("code", {}, "p. " + item.plan_pages.join(" a ")));
      var head = el("b", {}, item.axis);
      row.appendChild(head);
      var body = el("div", {});
      body.appendChild(el("p", {}, item.evidence));
      var tags = el("p", { class: "plan-tags" });
      item.segments.forEach(function (segment) { tags.appendChild(el("span", {}, segment)); });
      tags.appendChild(el("span", { class: "src" }, "Quaest pp. " + item.quaest_pages.join(", ")));
      body.appendChild(tags);
      row.appendChild(body);
      ledger.appendChild(row);
    });
    root.replaceChildren(ledger);
  }

  function renderMedia(strategy) {
    var root = document.getElementById("media-ledger");
    if (!root) return;
    var frame = strategy.media_frame;
    var list = el("ol", { class: "media-list" });
    frame.headlines.forEach(function (item) {
      var entry = el("li", {});
      entry.appendChild(el("b", {}, item.outlet));
      var link = el("a", { href: item.url, rel: "noopener" }, item.headline);
      entry.appendChild(link);
      entry.appendChild(el("span", { class: item.lead_number === "runoff" ? "tag runoff" : "tag first" }, item.lead_number === "runoff" ? "abre pelo 2º turno" : "abre pelo 1º turno"));
      list.appendChild(entry);
    });
    root.replaceChildren(list);
  }

  var PALETTE = {
    lula: "#c03830",
    flavio: "#2267ee",
    third: "#5b3fd6",
    none: "#667079",
    ink: "#081522",
    gold: "#8a5e05",
    green: "#15805e"
  };

  function svg(width, height, label) {
    var node = svgNode("svg", { viewBox: "0 0 " + width + " " + height, role: "img", "aria-label": label });
    return node;
  }

  function txt(parent, x, y, value, opts) {
    opts = opts || {};
    var node = svgNode("text", {
      x: x, y: y,
      "font-family": opts.mono === false ? "'IBM Plex Sans Condensed', Arial, sans-serif" : "'IBM Plex Mono', monospace",
      "font-size": opts.size || 12,
      "font-weight": opts.weight || 400,
      fill: opts.fill || PALETTE.ink,
      "text-anchor": opts.anchor || "start"
    }, value);
    parent.appendChild(node);
    return node;
  }

  function rect(parent, x, y, w, h, fill, extra) {
    var attrs = { x: x, y: y, width: Math.max(0, w), height: Math.max(0, h), fill: fill };
    Object.keys(extra || {}).forEach(function (key) { attrs[key] = extra[key]; });
    parent.appendChild(svgNode("rect", attrs));
  }

  function renderScoreboard(data) {
    var root = document.getElementById("scoreboard-chart");
    if (!root) return;
    var first = data.first_round.values;
    var runoff = data.runoffs.values["Flávio Bolsonaro"];
    var chart = svg(960, 250, "Placar do primeiro e do segundo turno");
    var rounds = [
      { title: "1º turno · página 16", a: first["Lula"], b: first["Flávio Bolsonaro"], rest: "terceira via 12 · indeciso e branco 18", x: 20 },
      { title: "2º turno · página 30", a: runoff["Lula"], b: runoff.challenger, rest: "branco e nulo 13 · indeciso 4", x: 500 }
    ];
    rounds.forEach(function (round) {
      txt(chart, round.x, 26, round.title, { size: 13, fill: "#617080", weight: 700 });
      txt(chart, round.x, 96, String(round.a), { size: 74, weight: 800, fill: PALETTE.lula });
      txt(chart, round.x + 150, 96, String(round.b), { size: 74, weight: 800, fill: PALETTE.flavio });
      txt(chart, round.x, 122, "Lula", { size: 14, weight: 700 });
      txt(chart, round.x + 150, 122, "Flávio", { size: 14, weight: 700 });
      var scale = 400 / 100;
      rect(chart, round.x, 150, round.a * scale, 26, PALETTE.lula);
      rect(chart, round.x, 182, round.b * scale, 26, PALETTE.flavio);
      txt(chart, round.x, 226, round.rest, { size: 12, fill: "#617080" });
      txt(chart, round.x + 330, 96, "+" + (round.a - round.b), { size: 34, weight: 800, fill: PALETTE.ink });
      txt(chart, round.x + 330, 118, "de vantagem", { size: 11, fill: "#617080" });
    });
    root.replaceChildren(chart);
  }

  // Cartograma: cinco blocos na posição geográfica aproximada, cor pela margem.
  var TILES = [
    { key: "Centro-Oeste/Norte", label: "Norte e Centro-Oeste", x: 24, y: 34, w: 258, h: 176 },
    { key: "Nordeste", label: "Nordeste", x: 296, y: 34, w: 240, h: 176 },
    { key: "Sudeste", label: "Sudeste", x: 296, y: 226, w: 240, h: 160 },
    { key: "Sul", label: "Sul", x: 92, y: 226, w: 190, h: 160 }
  ];

  function marginColor(margin) {
    if (margin >= 10) return "#1b4bb8";
    if (margin >= 0) return "#5b8cf0";
    if (margin >= -15) return "#e9a19c";
    return "#b2302a";
  }

  function renderRegionTiles(strategy) {
    var root = document.getElementById("region-map");
    if (!root) return;
    var cuts = strategy.third_way_geography.cuts;
    var chart = svg(560, 452, "Cartograma das regiões pela margem de Flávio no primeiro turno");
    TILES.forEach(function (tile) {
      var cut = cuts[tile.key];
      if (!cut) return;
      var fill = marginColor(cut.flavio_margin);
      rect(chart, tile.x, tile.y, tile.w, tile.h, fill, { rx: 10 });
      var strong = cut.flavio_margin >= 10 || cut.flavio_margin < -15;
      var ink = strong ? "#fffdf8" : PALETTE.ink;
      txt(chart, tile.x + 16, tile.y + 28, tile.label, { size: 14, weight: 700, fill: ink, mono: false });
      txt(chart, tile.x + 16, tile.y + 84, (cut.flavio_margin > 0 ? "+" : "") + cut.flavio_margin, { size: 44, weight: 800, fill: ink });
      txt(chart, tile.x + 16, tile.h + tile.y - 44, "Lula " + cut.Lula + "  Flávio " + cut["Flávio"], { size: 12, weight: 700, fill: ink });
      txt(chart, tile.x + 16, tile.h + tile.y - 26, "3ª via " + cut.third_way + "  sem escolha " + cut.non_choice, { size: 11, fill: ink });
    });
    txt(chart, 24, 416, "Margem de Flávio contra Lula no primeiro turno, página 17.", { size: 11, fill: "#617080" });
    txt(chart, 24, 436, "A Quaest publica Norte e Centro-Oeste como um recorte só.", { size: 11, fill: "#617080" });
    root.replaceChildren(chart);
  }

  function renderPotential(strategy) {
    var root = document.getElementById("potential-chart");
    if (!root) return;
    var region = strategy.profile_region.values;
    var income = strategy.profile_income.values;
    var rows = [
      { label: "Sul", pair: region["Sul"] },
      { label: "Mais de 5 SM", pair: income["Mais de 5 SM"] },
      { label: "2 a 5 SM", pair: income["2 a 5 SM"] },
      { label: "Sudeste", pair: region["Sudeste"] },
      { label: "Centro-Oeste/Norte", pair: region["Centro-Oeste/Norte"] },
      { label: "Até 2 SM", pair: income["Até 2 SM"] },
      { label: "Nordeste", pair: region["Nordeste"] }
    ];
    var chart = svg(900, 60 + rows.length * 54, "Potencial de voto e rejeição de Lula e Flávio por recorte");
    txt(chart, 0, 16, "potencial de voto, quem diz que poderia votar", { size: 12, fill: "#617080" });
    txt(chart, 470, 16, "rejeição, quem diz que não votaria de jeito nenhum", { size: 12, fill: "#617080" });
    rows.forEach(function (row, index) {
      var y = 48 + index * 54;
      txt(chart, 0, y + 4, row.label, { size: 13, weight: 700, mono: false });
      [["Lula", 0], ["Flávio", 1]].forEach(function (pair, side) {
        var values = row.pair[pair[0]];
        var color = side === 0 ? PALETTE.lula : PALETTE.flavio;
        rect(chart, 180, y - 10 + side * 18, values[0] * 2.6, 15, color);
        txt(chart, 186 + values[0] * 2.6, y + 2 + side * 18, values[0], { size: 11, weight: 700, fill: color });
        rect(chart, 620, y - 10 + side * 18, values[2] * 2.6, 15, color, { opacity: ".38" });
        txt(chart, 626 + values[2] * 2.6, y + 2 + side * 18, values[2], { size: 11, weight: 700, fill: color });
      });
    });
    var legendY = 40 + rows.length * 54;
    rect(chart, 180, legendY, 13, 13, PALETTE.lula);
    txt(chart, 200, legendY + 11, "Lula", { size: 11 });
    rect(chart, 250, legendY, 13, 13, PALETTE.flavio);
    txt(chart, 270, legendY + 11, "Flávio", { size: 11 });
    txt(chart, 340, legendY + 11, "páginas 72 e 76 · barra clara é rejeição", { size: 11, fill: "#617080" });
    root.replaceChildren(chart);
  }

  function renderInterest(strategy) {
    var root = document.getElementById("interest-chart");
    if (!root) return;
    var cuts = strategy.interest.cuts;
    var shares = strategy.interest.shares;
    var names = ["Muito interessado", "Pouco interessado", "Nada interessado"];
    var chart = svg(900, 300, "Primeiro turno e estoque sem escolha por nível de interesse na eleição");
    names.forEach(function (name, index) {
      var cut = cuts[name];
      var x = 30 + index * 300;
      txt(chart, x, 22, name, { size: 14, weight: 700, mono: false });
      txt(chart, x, 40, shares[name] + "% da amostra · página 25", { size: 11, fill: "#617080" });
      var base = 210;
      var scale = 2.4;
      [[cut.Lula, PALETTE.lula, "Lula"], [cut["Flávio"], PALETTE.flavio, "Flávio"], [cut.third_way, PALETTE.third, "3ª via"], [cut.non_choice, PALETTE.none, "sem escolha"]].forEach(function (item, position) {
        var height = item[0] * scale;
        rect(chart, x + position * 56, base - height, 44, height, item[1], { rx: 2 });
        txt(chart, x + position * 56 + 22, base - height - 8, item[0], { size: 14, weight: 800, fill: item[1] === PALETTE.none ? PALETTE.ink : item[1], anchor: "middle" });
        txt(chart, x + position * 56 + 22, base + 18, item[2], { size: 10, fill: "#617080", anchor: "middle" });
      });
      txt(chart, x, base + 52, "Lula lidera por " + cut.lula_lead, { size: 12, weight: 700 });
    });
    txt(chart, 30, 288, "O estoque sem escolha vai de 6 a 35 pontos conforme o interesse cai. A vantagem de Lula não cai junto.", { size: 11, fill: "#617080" });
    root.replaceChildren(chart);
  }

  function renderConcerns(strategy) {
    var root = document.getElementById("concern-chart");
    if (!root) return;
    var values = strategy.concerns.positioning.values;
    var blocs = ["Lulista", "Esquerda não lulista", "Independente", "Direita não bolsonarista", "Bolsonarista"];
    var topics = [
      { key: "Violência", color: "#2267ee" },
      { key: "Economia", color: "#5b3fd6" },
      { key: "Corrupção", color: "#8a5e05" },
      { key: "Saúde", color: "#15805e" },
      { key: "Problemas sociais", color: "#c03830" }
    ];
    var chart = svg(900, 330, "Maior preocupação do país por bloco político");
    blocs.forEach(function (bloc, index) {
      var y = 40 + index * 56;
      txt(chart, 0, y + 4, bloc, { size: 12, weight: 700, mono: false });
      var x = 230;
      topics.forEach(function (topic) {
        var value = values[bloc][topic.key];
        var width = value * 6.5;
        rect(chart, x, y - 12, width, 24, topic.color);
        if (width > 30) txt(chart, x + width / 2, y + 5, value, { size: 12, weight: 700, fill: "#fffdf8", anchor: "middle" });
        x += width + 2;
      });
    });
    var legendY = 40 + blocs.length * 56;
    var lx = 230;
    topics.forEach(function (topic) {
      rect(chart, lx, legendY - 10, 12, 12, topic.color);
      txt(chart, lx + 17, legendY, topic.key, { size: 11 });
      lx += topic.key.length * 7 + 34;
    });
    txt(chart, 0, legendY + 26, "Página 159. Violência é a primeira preocupação nos cinco blocos, e a maior de todas é entre lulistas.", { size: 11, fill: "#617080" });
    root.replaceChildren(chart);
  }

  function renderSubstitution(strategy, data) {
    var root = document.getElementById("substitution-chart");
    if (!root) return;
    var rows = strategy.substitution.rows;
    var names = Object.keys(rows).sort(function (a, b) { return rows[b].flavio_margin - rows[a].flavio_margin; });
    var chart = svg(900, 60 + names.length * 26, "Margem de Flávio e de Caiado no segundo turno, por segmento");
    var zero = 470;
    var scale = 8.2;
    chart.appendChild(svgNode("line", { x1: zero, y1: 24, x2: zero, y2: 34 + names.length * 26, stroke: "#667079", "stroke-width": "1" }));
    txt(chart, zero, 18, "empate", { size: 11, fill: "#617080", anchor: "middle" });
    names.forEach(function (name, index) {
      var y = 40 + index * 26;
      var row = rows[name];
      txt(chart, 0, y + 4, name, { size: 12, mono: false });
      var xf = zero + row.flavio_margin * scale;
      var xc = zero + row.caiado_margin * scale;
      chart.appendChild(svgNode("line", { x1: Math.min(xf, xc), y1: y, x2: Math.max(xf, xc), y2: y, stroke: "#c9cfd3", "stroke-width": "5", "stroke-linecap": "round" }));
      chart.appendChild(svgNode("circle", { cx: xc, cy: y, r: 5, fill: "#667079" }));
      chart.appendChild(svgNode("circle", { cx: xf, cy: y, r: 6, fill: PALETTE.flavio }));
      txt(chart, 860, y + 4, (row.flavio_margin > 0 ? "+" : "") + row.flavio_margin, { size: 11, weight: 700, anchor: "end", fill: row.flavio_margin >= 0 ? PALETTE.flavio : PALETTE.lula });
    });
    var legendY = 44 + names.length * 26;
    chart.appendChild(svgNode("circle", { cx: 236, cy: legendY - 4, r: 6, fill: PALETTE.flavio }));
    txt(chart, 248, legendY, "Flávio contra Lula", { size: 11 });
    chart.appendChild(svgNode("circle", { cx: 400, cy: legendY - 4, r: 5, fill: "#667079" }));
    txt(chart, 412, legendY, "Caiado contra Lula · páginas 31 e 41", { size: 11 });
    root.replaceChildren(chart);
  }

  function renderEconomy(data) {
    var root = document.getElementById("economy-chart");
    if (!root) return;
    var findings = data.other_findings;
    var groups = [
      { title: "Economia nos últimos 12 meses", page: 141, values: findings.economy_past, order: ["Piorou", "Ficou igual", "Melhorou"] },
      { title: "Preço dos alimentos no último mês", page: 145, values: findings.food, order: ["Subiu", "Ficou igual", "Caiu"] },
      { title: "Expectativa para os próximos 12 meses", page: 149, values: findings.economy_future, order: ["Piorar", "Ficar igual", "Melhorar"] }
    ];
    var colors = ["#c03830", "#667079", "#15805e"];
    var chart = svg(900, 300, "Percepção econômica em três perguntas");
    groups.forEach(function (group, index) {
      var y = 40 + index * 88;
      txt(chart, 0, y - 12, group.title + " · página " + group.page, { size: 12, weight: 700, mono: false });
      var x = 0;
      group.order.forEach(function (key, position) {
        var value = group.values[key];
        var width = value * 8.6;
        rect(chart, x, y, width, 30, colors[position]);
        if (width > 40) {
          txt(chart, x + 10, y + 21, value + "%", { size: 14, weight: 800, fill: "#fffdf8" });
        }
        txt(chart, x, y + 48, key, { size: 11, fill: "#617080" });
        x += width + 3;
      });
    });
    root.replaceChildren(chart);
  }

  function enableReveal() {
    var nodes = document.querySelectorAll(".reveal");
    document.documentElement.classList.add("reveal-ready");
    if (!("IntersectionObserver" in window)) {
      nodes.forEach(function (node) { node.classList.add("visible"); });
      window.__revealReady = true;
      return;
    }
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          observer.unobserve(entry.target);
        }
      });
    }, { rootMargin: "0px 0px -7% 0px", threshold: .04 });
    nodes.forEach(function (node) { observer.observe(node); });
    window.__revealReady = true;
  }

  function enableToc() {
    var links = Array.from(document.querySelectorAll(".toc a"));
    var sections = links.map(function (link) { return document.querySelector(link.getAttribute("href")); }).filter(Boolean);
    if (!("IntersectionObserver" in window)) return;
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        links.forEach(function (link) { link.classList.toggle("active", link.getAttribute("href") === "#" + entry.target.id); });
      });
    }, { rootMargin: "-20% 0px -72% 0px" });
    sections.forEach(function (section) { observer.observe(section); });
  }

  document.addEventListener("DOMContentLoaded", function () {
    enableReveal();
    enableToc();
    load("dossier-data", DATA_URL).then(function (data) {
      renderRanks(data);
      renderGaps(data);
      renderChannels(data);
      renderTransfer(data);
      renderScoreboard(data);
      renderEconomy(data);
      return load("dossier-strategy", STRATEGY_URL).then(function (strategy) {
        renderMap(strategy);
        renderFirmness(strategy);
        renderEquation(strategy);
        renderPremium(strategy);
        renderPlan(strategy);
        renderMedia(strategy);
        renderRegionTiles(strategy);
        renderPotential(strategy);
        renderInterest(strategy);
        renderConcerns(strategy);
        renderSubstitution(strategy, data);
      });
    }).catch(function (error) {
      console.error("Quaest dossier fallback in use", error);
    });
  });
})();
