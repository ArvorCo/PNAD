(() => {
  "use strict";

  const NS = "http://www.w3.org/2000/svg";
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const svgEl = (name, attrs = {}) => {
    const node = document.createElementNS(NS, name);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
    return node;
  };
  const addText = (svg, x, y, value, cls = "axis-label", anchor = "middle") => {
    const node = svgEl("text", { x, y, class: cls, "text-anchor": anchor });
    node.textContent = value;
    svg.append(node);
    return node;
  };

  function lineChart(target, series, dates) {
    const host = $(target);
    if (!host) return;
    const width = 780, height = 330, pad = { left: 42, right: 24, top: 20, bottom: 45 };
    const svg = svgEl("svg", { viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": host.dataset.label || "Série histórica" });
    const all = Object.values(series).flat();
    const min = Math.floor((Math.min(...all) - 3) / 5) * 5;
    const max = Math.ceil((Math.max(...all) + 3) / 5) * 5;
    const x = i => pad.left + i * (width - pad.left - pad.right) / (dates.length - 1);
    const y = v => pad.top + (max - v) * (height - pad.top - pad.bottom) / (max - min);
    for (let tick = min; tick <= max; tick += 5) {
      svg.append(svgEl("line", { x1: pad.left, x2: width - pad.right, y1: y(tick), y2: y(tick), stroke: "#d9dde4", "stroke-width": 1 }));
      addText(svg, pad.left - 8, y(tick) + 4, tick, "axis-label", "end");
    }
    dates.forEach((date, i) => addText(svg, x(i), height - 15, date, "axis-label"));
    const colors = ["#ef3e36", "#1b54f2"];
    Object.entries(series).forEach(([label, values], index) => {
      const points = values.map((value, i) => `${x(i)},${y(value)}`).join(" ");
      svg.append(svgEl("polyline", { points, class: "series-line", stroke: colors[index] }));
      values.forEach((value, i) => {
        svg.append(svgEl("circle", { cx: x(i), cy: y(value), r: i === values.length - 1 ? 7 : 4, fill: colors[index], stroke: "white", "stroke-width": 2 }));
        if (i >= values.length - 2) addText(svg, x(i), y(value) - 11, value, "value-label");
      });
      addText(svg, width - pad.right, y(values.at(-1)) + (index ? 21 : -13), label, "value-label", "end").setAttribute("fill", colors[index]);
    });
    host.replaceChildren(svg);
  }

  function groupedBars(target, groups, labels, colors = ["#ef3e36", "#1b54f2"]) {
    const host = $(target);
    if (!host) return;
    const width = 780, row = 70, height = 45 + groups.length * row, left = 130, right = 45;
    const svg = svgEl("svg", { viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": host.dataset.label || "Comparação" });
    const max = Math.max(...groups.flatMap(group => group.values));
    groups.forEach((group, i) => {
      const y = 25 + i * row;
      addText(svg, left - 12, y + 24, group.name, "axis-label", "end");
      group.values.forEach((value, j) => {
        const barY = y + j * 24;
        const barWidth = (width - left - right) * value / Math.max(60, max);
        svg.append(svgEl("rect", { x: left, y: barY, width: barWidth, height: 17, fill: colors[j], rx: 2 }));
        addText(svg, left + barWidth + 7, barY + 13, `${value.toLocaleString("pt-BR")}%`, "value-label", "start");
      });
    });
    labels.forEach((label, i) => {
      svg.append(svgEl("rect", { x: left + i * 130, y: height - 18, width: 12, height: 12, fill: colors[i] }));
      addText(svg, left + 18 + i * 130, height - 8, label, "axis-label", "start");
    });
    host.replaceChildren(svg);
  }

  function incomeChart(data) {
    const pnad = Object.values(data.benchmarks.pnad_income_2025.distribution).map(item => item.pct);
    const nexus = data.profiles.august.income;
    groupedBars("#income-chart", ["Até 1 SM", "1 a 2", "2 a 5", "5+ SM"].map((name, i) => ({ name, values: [nexus[i], Number(pnad[i].toFixed(1))] })), ["Nexus", "PNAD 2025"], ["#ef3e36", "#1b54f2"]);
  }

  function transferFlow(data) {
    const host = $("#transfer-flow");
    if (!host) return;
    const matrix = data.transfer.matrix;
    const rows = data.transfer.row_targets_scaled;
    const cols = data.transfer.column_targets;
    const sources = data.transfer.sources;
    const destinations = data.transfer.destinations;
    const width = 960, height = 620, top = 24, bottom = 24;
    const barX0 = 178, barX1 = 770, barW = 13;
    const colors = ["#ef3e36", "#74a2ff", "#d9ff43", "#a8afbb"];
    const sourceColors = { Lula: "#ef3e36", "Flávio": "#74a2ff" };
    const usable = height - top - bottom;
    const total = rows.reduce((sum, value) => sum + value, 0);
    const gapS = 7, gapT = 14;
    const k = Math.min((usable - gapS * (rows.length - 1)) / total, (usable - gapT * (cols.length - 1)) / total);
    const sourcePos = []; const targetPos = [];
    let cursor = top + (usable - total * k - gapS * (rows.length - 1)) / 2;
    rows.forEach(value => { sourcePos.push({ y: cursor, h: value * k, off: 0 }); cursor += value * k + gapS; });
    cursor = top + (usable - total * k - gapT * (cols.length - 1)) / 2;
    cols.forEach(value => { targetPos.push({ y: cursor, h: value * k, off: 0 }); cursor += value * k + gapT; });

    const svg = svgEl("svg", { viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": "Transferência agregada estimada por IPF" });
    const defs = svgEl("defs");
    colors.forEach((color, j) => {
      const pattern = svgEl("pattern", { id: `hatch${j}`, width: 7, height: 7, patternUnits: "userSpaceOnUse", patternTransform: "rotate(45)" });
      pattern.append(svgEl("rect", { width: 7, height: 7, fill: color, opacity: .22 }));
      pattern.append(svgEl("line", { x1: 0, y1: 0, x2: 0, y2: 7, stroke: color, "stroke-width": 2.6, opacity: .78 }));
      defs.append(pattern);
    });
    svg.append(defs);

    const mid = (barX1 - barX0 - barW) * .46;
    matrix.forEach((row, i) => row.forEach((value, j) => {
      if (value < .15) return;
      const h = value * k;
      const sy = sourcePos[i].y + sourcePos[i].off;
      const ty = targetPos[j].y + targetPos[j].off;
      sourcePos[i].off += h; targetPos[j].off += h;
      const x0 = barX0 + barW, x1 = barX1;
      const ribbon = svgEl("path", {
        d: `M ${x0} ${sy} C ${x0 + mid} ${sy}, ${x1 - mid} ${ty}, ${x1} ${ty}
            L ${x1} ${ty + h} C ${x1 - mid} ${ty + h}, ${x0 + mid} ${sy + h}, ${x0} ${sy + h} Z`,
        fill: `url(#hatch${j})`, stroke: colors[j], "stroke-width": .5, "stroke-opacity": .4,
      });
      const title = svgEl("title");
      title.textContent = `${sources[i]} → ${destinations[j]}: ${value.toLocaleString("pt-BR")} ponto(s) (inferência IPF)`;
      ribbon.append(title);
      svg.append(ribbon);
    }));

    rows.forEach((value, i) => {
      const { y, h } = sourcePos[i];
      svg.append(svgEl("rect", { x: barX0, y, width: barW, height: Math.max(h, 2), fill: sourceColors[sources[i]] || "#e8ecf4" }));
      const label = addText(svg, barX0 - 12, y + h / 2 + 4, `${sources[i]} ${(Math.round(rows[i] * 10) / 10).toLocaleString("pt-BR")}`, "sankey-label", "end");
      if (h < 13) label.setAttribute("y", y + h / 2 + 3.5);
    });
    cols.forEach((value, j) => {
      const { y, h } = targetPos[j];
      svg.append(svgEl("rect", { x: barX1, y, width: barW, height: Math.max(h, 2), fill: colors[j] }));
      addText(svg, barX1 + barW + 12, y + h / 2 + 4, `${destinations[j]} ${value}`, "sankey-label", "start");
    });
    addText(svg, barX0 + barW / 2, 14, "1º TURNO (fato)", "sankey-axis");
    addText(svg, barX1 + barW / 2, 14, "2º TURNO (fato)", "sankey-axis");
    host.replaceChildren(svg);
  }

  function archetypes(data) {
    const host = $("#archetypes");
    if (!host) return;
    host.replaceChildren(...data.women_pnad.groups.map(item => {
      const article = document.createElement("article");
      article.className = "card archetype";
      article.innerHTML = `<span class="card-number blue">${item.population_pct.toLocaleString("pt-BR")}%</span>
        <h3>${item.group}</h3>
        <dl><dt>idade média</dt><dd>${item.age_mean.toLocaleString("pt-BR")}</dd>
        <dt>renda domiciliar</dt><dd>${item.income_mean_sm.toLocaleString("pt-BR")} SM</dd>
        <dt>ocupadas</dt><dd>${item.occupied.toLocaleString("pt-BR")}%</dd>
        <dt>Bolsa Família</dt><dd>${item.bolsa_familia.toLocaleString("pt-BR")}%</dd>
        <dt>Nordeste</dt><dd>${item.northeast.toLocaleString("pt-BR")}%</dd></dl>`;
      return article;
    }));
  }

  function womenMaterial(women) {
    const host = $("#women-material");
    if (!host || !women) return;
    const ft = women.forca_de_trabalho.por_sexo;
    const esc = women.escolaridade.por_sexo;
    const bf = women.bolsa_familia.por_sexo;
    const chefia = women.chefia_domiciliar.por_sexo_do_responsavel;
    const rows = [
      { name: "Força de trabalho", m: ft.mulheres.taxa_de_participacao.pct, h: ft.homens.taxa_de_participacao.pct },
      { name: "Ensino superior", m: esc.mulheres.distribuicao.Superior.pct, h: esc.homens.distribuicao.Superior.pct },
      { name: "Chefia o domicílio", m: chefia.mulheres.chefia_pct.pct, h: chefia.homens.chefia_pct.pct },
      { name: "Bolsa Família (titular)", m: bf.mulheres.recebe_pessoalmente.pct, h: bf.homens.recebe_pessoalmente.pct },
      { name: "Domicílio até 1 SM", m: women.renda_domiciliar_por_faixa.por_sexo.mulheres.distribuicao["Até 1 SM"].pct, h: women.renda_domiciliar_por_faixa.por_sexo.homens.distribuicao["Até 1 SM"].pct },
    ];
    groupedBars("#women-material", rows.map(row => ({ name: row.name, values: [Number(row.m.toFixed(1)), Number(row.h.toFixed(1))] })), ["Mulheres", "Homens"], ["#ef3e36", "#1b54f2"]);
  }

  function womenRegion(women) {
    const host = $("#women-region");
    if (!host || !women) return;
    const regions = women.regiao.por_regiao;
    const order = ["Nordeste", "Norte", "Centro-Oeste", "Sudeste", "Sul"];
    const table = document.createElement("table");
    table.className = "delta-table";
    table.innerHTML = `<thead><tr><th>Região</th><th>Renda p.c.</th><th>Até 1 SM</th><th>Bolsa Família</th><th>Ocupadas</th></tr></thead>`;
    const body = document.createElement("tbody");
    order.forEach(name => {
      const region = regions[name];
      if (!region) return;
      const row = document.createElement("tr");
      const money = Math.round(region.renda_per_capita_media_brl.valor).toLocaleString("pt-BR");
      row.innerHTML = `<td>${name}</td><td>R$ ${money}</td>
        <td class="${region.ate_1_sm_pct.pct > 20 ? "hot" : ""}">${region.ate_1_sm_pct.pct.toFixed(1).replace(".", ",")}%</td>
        <td>${region.bolsa_familia_pct.pct.toFixed(1).replace(".", ",")}%</td>
        <td>${region.ocupadas_pct.pct.toFixed(1).replace(".", ",")}%</td>`;
      body.append(row);
    });
    table.append(body);
    host.replaceChildren(table);
  }

  function fillMetrics(data) {
    const paths = {
      "territory-overlap": data.territory.overlap,
      "territory-retention": `${data.territory.retention_pct.toLocaleString("pt-BR")}%`,
      "territory-entered": data.territory.entered,
      "income-gap": `${data.reweighting.august.runoff.income.gap.toLocaleString("pt-BR")}`,
      "transfer-ratio": `${data.transfer.consolidation.ratio_flavio_lula.toLocaleString("pt-BR")}:1`,
    };
    Object.entries(paths).forEach(([id, value]) => { const node = $(`#${id}`); if (node) node.textContent = value; });
  }

  function reveal() {
    const observer = new IntersectionObserver(entries => entries.forEach(entry => {
      if (entry.isIntersecting) { entry.target.classList.add("visible"); observer.unobserve(entry.target); }
    }), { threshold: .08 });
    $$(".reveal").forEach(node => observer.observe(node));
  }

  const asJson = response => { if (!response.ok) throw new Error(`HTTP ${response.status}`); return response.json(); };
  Promise.all([
    fetch("assets/nexus_btg_082026_1_data.json").then(asJson),
    fetch("assets/nexus_btg_082026_1_mulheres.json").then(asJson).catch(() => null),
  ])
    .then(([data, women]) => {
      lineChart("#first-series", data.series.first, data.series.dates);
      lineChart("#runoff-series", data.series.runoff, data.series.dates);
      incomeChart(data);
      transferFlow(data);
      archetypes(data);
      womenMaterial(women);
      womenRegion(women);
      fillMetrics(data);
      document.documentElement.classList.add("data-ready");
    })
    .catch(error => {
      document.documentElement.classList.add("data-failed");
      $$(".chart").forEach(node => { if (!node.children.length) node.textContent = "Gráfico disponível com o relatório servido por HTTP."; });
      console.warn("Dados auxiliares indisponíveis", error.message);
    });

  if ("IntersectionObserver" in window) reveal();
  else $$(".reveal").forEach(node => node.classList.add("visible"));
})();
