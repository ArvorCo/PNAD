(function () {
  "use strict";

  var DATA_URL = "assets/quaest_globo_140826_data.json";
  var STRATEGY_URL = "assets/quaest_globo_140826_estrategia.json";

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
    fetch(DATA_URL).then(function (response) {
      if (!response.ok) throw new Error("data " + response.status);
      return response.json();
    }).then(function (data) {
      renderRanks(data);
      renderGaps(data);
      renderChannels(data);
      renderTransfer(data);
    }).catch(function (error) {
      console.error("Quaest dossier data fallback in use", error);
    });
    fetch(STRATEGY_URL).then(function (response) {
      if (!response.ok) throw new Error("strategy " + response.status);
      return response.json();
    }).then(function (strategy) {
      renderMap(strategy);
      renderFirmness(strategy);
      renderEquation(strategy);
      renderPremium(strategy);
      renderPlan(strategy);
      renderMedia(strategy);
    }).catch(function (error) {
      console.error("Quaest strategy fallback in use", error);
    });
  });
})();
