(() => {
  "use strict";

  const DATA_URL = "assets/mg_082026_data.json";
  const GEO_URL = "assets/mg_082026_municipios.geojson";
  const NS = "http://www.w3.org/2000/svg";
  const COLORS = {
    ink: "#18231c", green: "#19633c", green2: "#49a367", red: "#a62f28",
    red2: "#e55745", gold: "#d3a51d", blue: "#2c6381", paper: "#f1ecdf",
    gray: "#8b938c", white: "#fffdf6"
  };
  let data;
  let geo;
  let projection;
  let activeLayer = "flip";

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const svgEl = (tag, attrs = {}) => {
    const node = document.createElementNS(NS, tag);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
    return node;
  };
  const fmt = new Intl.NumberFormat("pt-BR");
  const money = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });
  const compact = new Intl.NumberFormat("pt-BR", { notation: "compact", maximumFractionDigits: 1 });
  const pct = value => `${Number(value).toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%`;
  const signed = value => `${value > 0 ? "+" : ""}${Number(value).toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 })} pp`;
  const esc = value => String(value ?? "").replace(/[&<>'"]/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[char]));

  function allCoordinates(geometry) {
    const out = [];
    const walk = value => {
      if (typeof value[0] === "number") out.push(value);
      else value.forEach(walk);
    };
    walk(geometry.coordinates);
    return out;
  }

  function buildProjection(features, width = 720, height = 660, pad = 22) {
    const points = features.flatMap(feature => allCoordinates(feature.geometry));
    const xs = points.map(point => point[0]);
    const ys = points.map(point => point[1]);
    const bounds = { minX: Math.min(...xs), maxX: Math.max(...xs), minY: Math.min(...ys), maxY: Math.max(...ys) };
    const scale = Math.min((width - 2 * pad) / (bounds.maxX - bounds.minX), (height - 2 * pad) / (bounds.maxY - bounds.minY));
    const usedW = (bounds.maxX - bounds.minX) * scale;
    const usedH = (bounds.maxY - bounds.minY) * scale;
    const offsetX = (width - usedW) / 2;
    const offsetY = (height - usedH) / 2;
    return point => [offsetX + (point[0] - bounds.minX) * scale, offsetY + (bounds.maxY - point[1]) * scale];
  }

  function geometryPath(geometry, project = projection) {
    const ringPath = ring => ring.map((point, index) => `${index ? "L" : "M"}${project(point)[0].toFixed(2)},${project(point)[1].toFixed(2)}`).join("") + "Z";
    if (geometry.type === "Polygon") return geometry.coordinates.map(ringPath).join("");
    if (geometry.type === "MultiPolygon") return geometry.coordinates.flatMap(polygon => polygon.map(ringPath)).join("");
    return "";
  }

  function centerOf(feature) {
    const points = allCoordinates(feature.geometry);
    const xs = points.map(point => point[0]);
    const ys = points.map(point => point[1]);
    return projection([(Math.min(...xs) + Math.max(...xs)) / 2, (Math.min(...ys) + Math.max(...ys)) / 2]);
  }

  function mix(a, b, t) {
    const parse = color => color.match(/\w\w/g).map(value => parseInt(value, 16));
    const aa = parse(a), bb = parse(b);
    return `#${aa.map((value, index) => Math.round(value + (bb[index] - value) * t).toString(16).padStart(2, "0")).join("")}`;
  }

  function quantile(values, q) {
    const sorted = [...values].sort((a, b) => a - b);
    return sorted[Math.floor((sorted.length - 1) * q)];
  }

  const layerMeta = {
    flip: {
      title: "A fronteira de 160 cidades",
      text: "O amarelo não é um terceiro bloco. É o conjunto que trocou de vencedor, sobretudo ao redor da metrópole, na faixa central e na Zona da Mata.",
      legend: [[COLORS.green2, "Direita nas duas (285)"], ["#f4cd19", "Direita → esquerda (160)"], [COLORS.red2, "Esquerda nas duas (404)"], [COLORS.blue, "Esquerda → direita (4)"]],
      color: p => ({ "Direita nas duas": COLORS.green2, "Direita→esquerda": "#f4cd19", "Esquerda nas duas": COLORS.red2, "Esquerda→direita": COLORS.blue }[p.pres_virada])
    },
    margin: {
      title: "A linha de 50% corta o estado",
      text: "Vermelho indica margem da esquerda; verde, margem da direita. A cor intensa mostra fortaleza. O tom quase branco mostra o verdadeiro pêndulo.",
      legend: [[COLORS.red, "Esquerda +25 pp ou mais"], ["#e48a74", "Esquerda 0 a +25"], ["#eee7d8", "Empate"], ["#8cbc8d", "Direita 0 a +25"], [COLORS.green, "Direita +25 pp ou mais"]],
      color: p => {
        const value = Math.max(-50, Math.min(50, p.pres_2022_margem_esquerda_pp));
        return value >= 0 ? mix("#eee7d8", COLORS.red, value / 50) : mix("#eee7d8", COLORS.green, -value / 50);
      }
    },
    electorate: { title: "Tamanho político em 2026", text: "O eleitorado atual muda a leitura do mapa. Uma virada pequena na metrópole pesa mais que dezenas de municípios pequenos.", legend: [], value: p => p.eleitores_2026, colorScale: ["#dce8dd", COLORS.green] },
    nikolas: { title: "1,49 milhão com epicentro metropolitano", text: "A cor mostra a parcela dos votos válidos para deputado federal obtida por Nikolas em 2022. A região intermediária de Belo Horizonte concentrou 43,5% de sua votação estadual e 29,2% do eleitorado atual. Alcance legislativo não equivale a voto transferível.", legend: [], value: p => p.nikolas_2022_pct_validos_deputado, colorScale: ["#e6edf1", COLORS.blue] },
    income: { title: "A renda municipal não é o voto", text: "O Censo 2022 mostra uma clivagem nítida, mas há exceções: polos ricos próximos do empate e municípios pobres que permanecem à direita.", legend: [], value: p => p.renda_pc_media_2022, colorScale: ["#f3e6b2", "#a67300"] },
    gdp: { title: "Produção e renda são coisas diferentes", text: "PIB por habitante localiza polos produtivos, mineração, indústria e agro. Não diz quanto dessa produção chega ao domicílio médio.", legend: [], value: p => p.pib_pc_2023, colorScale: ["#dbe7ed", COLORS.blue] },
    pivotal: { title: "Relevância, competição e movimento", text: "O índice editorial aumenta com o eleitorado, com a proximidade de 50% e com a mudança desde 2018. Não é previsão nem taxa de persuasão.", legend: [], value: p => p.indice_pivotal, colorScale: ["#eee7d8", "#c48b0d"] }
  };

  function prepareContinuousLayers() {
    Object.entries(layerMeta).forEach(([key, meta]) => {
      if (!meta.value) return;
      const values = geo.features.map(feature => meta.value(feature.properties)).filter(Number.isFinite);
      const cuts = [0, .25, .5, .75, 1].map(q => quantile(values, q));
      meta.min = cuts[0]; meta.max = cuts[4];
      meta.color = properties => {
        const value = meta.value(properties);
        const t = (Math.log1p(value) - Math.log1p(meta.min)) / (Math.log1p(meta.max) - Math.log1p(meta.min));
        return mix(meta.colorScale[0], meta.colorScale[1], Math.max(0, Math.min(1, t)));
      };
      meta.legend = cuts.slice(0, -1).map((cut, index) => [mix(meta.colorScale[0], meta.colorScale[1], index / 3), `${formatLayerValue(key, cut)}${index === 3 ? " ou mais" : ""}`]);
    });
  }

  function formatLayerValue(layer, value) {
    if (layer === "electorate") return compact.format(value);
    if (layer === "nikolas") return pct(value);
    if (layer === "income" || layer === "gdp") return money.format(value);
    return Number(value).toLocaleString("pt-BR", { maximumFractionDigits: 1 });
  }

  function renderMap() {
    projection = buildProjection(geo.features, 760, 690, 24);
    prepareContinuousLayers();
    const map = $("#mg-map");
    map.innerHTML = "";
    geo.features.forEach(feature => {
      const path = svgEl("path", { d: geometryPath(feature.geometry), tabindex: "0", "data-code": feature.properties.codigo_ibge });
      path.addEventListener("pointerenter", event => showTooltip(event, feature));
      path.addEventListener("pointermove", moveTooltip);
      path.addEventListener("pointerleave", hideTooltip);
      path.addEventListener("focus", () => showTooltip(null, feature));
      path.addEventListener("blur", hideTooltip);
      map.append(path);
    });
    updateMapLayer("flip");
    $$("#map-layers button").forEach(button => button.addEventListener("click", () => {
      $$("#map-layers button").forEach(item => item.classList.toggle("active", item === button));
      updateMapLayer(button.dataset.layer);
    }));
    renderHeroOutline();
  }

  function updateMapLayer(layer) {
    activeLayer = layer;
    const meta = layerMeta[layer];
    $$("#mg-map path").forEach((path, index) => path.setAttribute("fill", meta.color(geo.features[index].properties)));
    $("#map-legend").innerHTML = meta.legend.map(([color, label]) => `<div class="legend-item"><i class="legend-swatch" style="background:${color}"></i><span>${esc(label)}</span></div>`).join("");
    $("#map-readout").innerHTML = `<p class="kicker">LEITURA DA CAMADA</p><h3>${esc(meta.title)}</h3><p>${esc(meta.text)}</p><dl><div><dt>Municípios</dt><dd>853</dd></div><div><dt>Eleitorado MG</dt><dd>16,38 mi</dd></div><div><dt>Camada</dt><dd>${esc($("#map-layers button.active").textContent)}</dd></div></dl>`;
  }

  function showTooltip(event, feature) {
    const p = feature.properties;
    const tooltip = $("#map-tooltip");
    tooltip.innerHTML = `<b>${esc(p.municipio)}</b><span>${esc(p.regiao_intermediaria)} · ${compact.format(p.eleitores_2026)} eleitores</span><span>2022: ${signed(p.pres_2022_margem_esquerda_pp)} para a esquerda</span><span>Movimento 2018–2022: ${signed(p.pres_deslocamento_esquerda_pp)}</span><span>Nikolas 2022: ${fmt.format(p.nikolas_2022_votos)} · ${pct(p.nikolas_2022_pct_validos_deputado)}</span><span>Renda per capita: ${money.format(p.renda_pc_media_2022)}</span><span>Índice pivotal: ${p.indice_pivotal}</span>`;
    tooltip.hidden = false;
    if (event) moveTooltip(event);
    else { tooltip.style.left = "20px"; tooltip.style.top = "90px"; }
  }
  function moveTooltip(event) {
    const tooltip = $("#map-tooltip");
    tooltip.style.left = `${Math.max(8, Math.min(innerWidth - tooltip.offsetWidth - 8, event.clientX + 18))}px`;
    tooltip.style.top = `${Math.max(8, Math.min(innerHeight - tooltip.offsetHeight - 8, event.clientY + 18))}px`;
  }
  function hideTooltip() { $("#map-tooltip").hidden = true; }

  function renderHeroOutline() {
    const hero = $("#hero-outline");
    const heroProject = buildProjection(geo.features, 640, 680, 16);
    hero.innerHTML = "";
    geo.features.forEach(feature => hero.append(svgEl("path", { d: geometryPath(feature.geometry, heroProject) })));
  }

  function barChart(selector, rows, options = {}) {
    const max = options.max || Math.max(...rows.flatMap(row => [row.value, row.value2 || 0]));
    $(selector).innerHTML = rows.map(row => {
      if (row.value2 === undefined) return `<div class="bar-row"><span class="label">${esc(row.label)}</span><div class="bar-track"><i class="bar-fill ${row.color || ""}" style="width:${100 * row.value / max}%"></i></div><b class="value">${esc(row.display || pct(row.value))}</b></div>`;
      return `<div class="bar-row dual"><span class="label">${esc(row.label)}</span><div class="bar-track" title="${esc(options.label1 || "Série 1")}: ${row.value}"><i class="bar-fill ${row.color || "green"}" style="width:${100 * row.value / max}%"></i></div><div class="bar-track" title="${esc(options.label2 || "Série 2")}: ${row.value2}"><i class="bar-fill ${row.color2 || "gold"}" style="width:${100 * row.value2 / max}%"></i></div><b class="value">${row.value} · ${row.value2}</b></div>`;
    }).join("");
  }

  function renderEconomy() {
    const annual = data.pnad.anual_2025_visita1;
    barChart("#income-pnad-chart", Object.entries(annual.renda_domiciliar_16_mais).map(([label, value]) => ({ label, value: value.pct, display: `${pct(value.pct)} ± ${pct(value.moe)}` })), { max: 50 });
    barChart("#territory-income-chart", Object.entries(annual.territorios).map(([label, value]) => ({ label, value: value.renda_pc_media_abril_2026.media, display: money.format(value.renda_pc_media_abril_2026.media) })), { max: 4500 });
  }

  function renderRegions() {
    const regions = data.regioes;
    const shell = $("#region-scatter");
    shell.innerHTML = "";
    const svg = svgEl("svg", { viewBox: "0 0 1000 480", role: "img" });
    const m = { l: 70, r: 40, t: 26, b: 55 }, w = 1000 - m.l - m.r, h = 480 - m.t - m.b;
    const xs = regions.map(item => item.renda_pc_media_2022), ys = regions.map(item => item.esquerda_2022_pct_validos), sizes = regions.map(item => item.eleitores_2026);
    const xMin = Math.floor(Math.min(...xs) / 200) * 200, xMax = Math.ceil(Math.max(...xs) / 200) * 200;
    const yMin = Math.floor(Math.min(...ys) / 5) * 5, yMax = Math.ceil(Math.max(...ys) / 5) * 5;
    const X = value => m.l + w * (value - xMin) / (xMax - xMin);
    const Y = value => m.t + h * (yMax - value) / (yMax - yMin);
    [40, 50, 60].forEach(value => {
      svg.append(svgEl("line", { x1: m.l, x2: m.l + w, y1: Y(value), y2: Y(value), class: "axis-line", opacity: value === 50 ? 1 : .3, "stroke-dasharray": value === 50 ? "6 5" : "" }));
      const label = svgEl("text", { x: 8, y: Y(value) + 4, class: "axis-label" }); label.textContent = `${value}% E`; svg.append(label);
    });
    [1000, 1200, 1400, 1600, 1800, 2000].filter(value => value >= xMin && value <= xMax).forEach(value => {
      svg.append(svgEl("line", { x1: X(value), x2: X(value), y1: m.t, y2: m.t + h, class: "axis-line", opacity: .2 }));
      const label = svgEl("text", { x: X(value), y: 460, class: "axis-label", "text-anchor": "middle" }); label.textContent = money.format(value); svg.append(label);
    });
    regions.forEach(region => {
      const radius = 7 + 19 * Math.sqrt(region.eleitores_2026 / Math.max(...sizes));
      const circle = svgEl("circle", { cx: X(region.renda_pc_media_2022), cy: Y(region.esquerda_2022_pct_validos), r: radius, class: "region-dot" });
      const title = svgEl("title"); title.textContent = `${region.regiao_intermediaria}: renda ${money.format(region.renda_pc_media_2022)}, esquerda ${pct(region.esquerda_2022_pct_validos)}, ${compact.format(region.eleitores_2026)} eleitores`; circle.append(title); svg.append(circle);
      const label = svgEl("text", { x: X(region.renda_pc_media_2022) + radius + 3, y: Y(region.esquerda_2022_pct_validos) + 3, class: "region-label" }); label.textContent = region.regiao_intermediaria; svg.append(label);
    });
    shell.append(svg);
    $("#region-table").innerHTML = regions.map(region => `<article class="region-chip"><b>${esc(region.regiao_intermediaria)}</b><span>${compact.format(region.eleitores_2026)} eleitores</span><span>${pct(region.esquerda_2022_pct_validos)} esquerda em 2022</span><span>${money.format(region.renda_pc_media_2022)} renda per capita</span><span>${pct(region.pib_mg_pct)} do PIB de MG</span></article>`).join("");
  }

  const routeGroups = [
    { key: "metro", color: "#f0c94c", cities: ["Belo Horizonte", "Contagem", "Betim", "Ribeirão das Neves", "Santa Luzia", "Ibirité", "Sabará", "Nova Lima", "Vespasiano", "Sete Lagoas"] },
    { key: "oeste", color: "#64b77d", cities: ["Uberlândia", "Uberaba", "Divinópolis", "Lavras", "Poços de Caldas"] },
    { key: "leste", color: "#69a7c9", cities: ["Juiz de Fora", "Itabira", "Governador Valadares"] },
    { key: "norte", color: "#ed6654", cities: ["Montes Claros", "Teófilo Otoni"] }
  ];

  function renderRoutes() {
    const svg = $("#route-map"); svg.innerHTML = "";
    geo.features.forEach(feature => svg.append(svgEl("path", { d: geometryPath(feature.geometry), class: "base" })));
    const byName = new Map(geo.features.map(feature => [feature.properties.municipio, feature]));
    routeGroups.forEach(group => {
      const points = group.cities.map(city => centerOf(byName.get(city))).filter(Boolean);
      if (points.length > 1) svg.append(svgEl("path", { d: points.map((point, index) => `${index ? "L" : "M"}${point[0]},${point[1]}`).join(""), class: "route-line", stroke: group.color }));
      points.forEach((point, index) => {
        svg.append(svgEl("circle", { cx: point[0], cy: point[1], r: 5, class: "route-dot", fill: group.color }));
        const label = svgEl("text", { x: point[0] + 7, y: point[1] - 7 }); label.textContent = group.cities[index]; svg.append(label);
      });
    });
  }

  function renderCityTable() {
    const rows = data.top_20_pivotais;
    const draw = filter => {
      const query = filter.trim().toLocaleLowerCase("pt-BR");
      const filtered = rows.filter(row => [row.municipio, row.regiao_imediata, row.regiao_intermediaria, row.pres_virada].join(" ").toLocaleLowerCase("pt-BR").includes(query));
      $("#city-table-body").innerHTML = filtered.map((row, index) => `<tr><td>${index + 1}</td><td><b>${esc(row.municipio)}</b><br><small>${esc(row.regiao_intermediaria)}</small></td><td>${fmt.format(row.eleitores_2026)}</td><td class="${row.pres_2022_margem_esquerda_pp > 0 ? "pos" : "neg"}">${signed(row.pres_2022_margem_esquerda_pp)}</td><td>${signed(row.pres_deslocamento_esquerda_pp)}</td><td>${money.format(row.pib_pc_2023)}</td><td><b>${row.indice_pivotal.toLocaleString("pt-BR")}</b></td></tr>`).join("");
      $("#city-count").textContent = `${filtered.length} município${filtered.length === 1 ? "" : "s"}`;
    };
    draw("");
    $("#city-filter").addEventListener("input", event => draw(event.target.value));
  }

  function renderPolls() {
    const q = data.pesquisas.quaest.governador_1t.valores;
    const r = data.pesquisas.real_time.governador_1t.valores;
    const names = ["Cleitinho Azevedo", "Patrus Ananias", "Alexandre Kalil", "Mateus Simões", "Gabriel Azevedo", "Flávio Roscoe"];
    barChart("#poll-comparison", names.map(name => ({ label: name.replace(" Azevedo", ""), value: q[name], value2: r[name] })), { max: 35, label1: "Quaest", label2: "Real Time" });
    const pnad = data.pnad.anual_2025_visita1.renda_domiciliar_16_mais;
    const qp = data.pesquisas.quaest.perfil.renda;
    const rp = data.pesquisas.real_time.perfil.renda;
    $("#sample-comparison").innerHTML = [
      ["Até 2 SM", pnad["Até 2 SM"].pct, qp["Até 2 SM"], rp["Até 2 SM"]],
      ["2 a 5 SM", pnad["Mais de 2 a 5 SM"].pct, qp["Mais de 2 a 5 SM"], rp["2 a 5 SM"]],
      ["Mais de 5 SM", pnad["Mais de 5 SM"].pct, qp["Mais de 5 SM"], rp["Mais de 5 SM"]]
    ].map(([label, a, b, c]) => `<div class="bar-row" style="grid-template-columns:100px 1fr"><span class="label">${label}</span><div><div class="bar-track" title="PNAD"><i class="bar-fill green" style="width:${a * 2}%"></i></div><div class="bar-track" title="Quaest"><i class="bar-fill" style="width:${b * 2}%"></i></div><div class="bar-track" title="Real Time"><i class="bar-fill red" style="width:${c * 2}%"></i></div><small>PNAD ${pct(a)} · Quaest ${b}% · Real Time ${c}%</small></div></div>`).join("");
  }

  const score = name => {
    const key = name.toLocaleLowerCase("pt-BR");
    if (/patrus|pimentel|haddad|lula|pt\b/.test(key)) return -1;
    if (/kalil/.test(key)) return -.4;
    if (/cleitinho|bolsonaro|viana|roscoe/.test(key)) return .85;
    if (/zema|anastasia|mateus|aro/.test(key)) return .55;
    if (/terceira|outros|gabriel|indec/.test(key)) return 0;
    return 0;
  };

  function ipf(rows, cols) {
    let matrix = rows.map(row => cols.map(col => {
      if (/indec/i.test(col.name)) return /indec/i.test(row.name) ? 8 : .45;
      if (/branco|não escolha/i.test(col.name)) return /branco/i.test(row.name) ? 10 : (/outros/i.test(row.name) ? .9 : .3);
      let value = Math.exp(-2.8 * Math.abs(score(row.name) - score(col.name)));
      if (row.name.split(" ")[0] === col.name.split(" ")[0]) value *= 12;
      if (/indec|branco/i.test(row.name)) value = .8;
      return Math.max(value, .0001);
    }));
    matrix = matrix.map((row, i) => { const sum = row.reduce((a, b) => a + b, 0); return row.map(value => value * rows[i].value / sum); });
    for (let iteration = 0; iteration < 800; iteration++) {
      cols.forEach((col, j) => { const sum = matrix.reduce((total, row) => total + row[j], 0); const factor = col.value / sum; matrix.forEach(row => { row[j] *= factor; }); });
      rows.forEach((row, i) => { const sum = matrix[i].reduce((a, b) => a + b, 0); const factor = row.value / sum; matrix[i] = matrix[i].map(value => value * factor); });
    }
    return matrix;
  }

  function groupedCandidates(items, count, otherName = "Outros") {
    const head = items.slice(0, count).map(item => ({ name: item.nome, value: item.pct_validos }));
    const rest = items.slice(count).reduce((sum, item) => sum + item.pct_validos, 0);
    if (rest > .01) head.push({ name: otherName, value: rest });
    return head;
  }

  function flowConfig(family, scenario) {
    const q = data.pesquisas.quaest;
    if (family === "poll-runoff") {
      const first = q.governador_1t.valores;
      const rows = ["Cleitinho Azevedo", "Patrus Ananias", "Alexandre Kalil", "Mateus Simões", "Gabriel Azevedo"].map(name => ({ name, value: first[name] }));
      rows.push({ name: "Outros", value: 7 }, { name: "Indecisos", value: 19 }, { name: "Branco/nulo", value: 12 });
      const names = scenario.split(" × "); const values = q.segundos_turnos.cenarios[scenario];
      return { rows, cols: [{ name: names[0], value: values[0] }, { name: names[1], value: values[1] }, { name: "Indecisos", value: values[2] }, { name: "Branco/nulo", value: values[3] }], caption: `Quaest, pp. 8 e 20. Cenário ${scenario}. As duas margens somam 100%; todas as fitas são estimadas.` };
    }
    if (family === "gov2018") {
      const first = data.eleicoes["2018_1_governador"].candidatos, second = data.eleicoes["2018_2_governador"].candidatos;
      return { rows: groupedCandidates(first, 4), cols: second.map(item => ({ name: item.nome, value: item.pct_validos })), caption: "TSE 2018, votos válidos para governador. A eleição teve dois turnos; as margens são oficiais e a matriz é ecológica." };
    }
    if (family === "cross2022") {
      const gov = data.eleicoes["2022_1_governador"].candidatos, pres = data.eleicoes["2022_1_presidente"].candidatos;
      return { rows: groupedCandidates(gov, 3), cols: [{ name: pres[0].nome, value: pres[0].pct_validos }, { name: pres[1].nome, value: pres[1].pct_validos }, { name: "Terceira via", value: pres.slice(2).reduce((sum, item) => sum + item.pct_validos, 0) }], caption: "TSE 2022, votos válidos no primeiro turno. Cargos diferentes, mesmos municípios, sem cruzamento individual publicado." };
    }
    const first = q.governador_1t.valores;
    const rows = ["Cleitinho Azevedo", "Patrus Ananias", "Alexandre Kalil", "Mateus Simões", "Gabriel Azevedo"].map(name => ({ name, value: first[name] }));
    rows.push({ name: "Outros", value: 7 }, { name: "Indecisos", value: 19 }, { name: "Branco/nulo", value: 12 });
    const president = q.presidente.cenario_1;
    return { rows, cols: [{ name: "Lula", value: president.Lula }, { name: "Flávio Bolsonaro", value: president["Flávio Bolsonaro"] }, { name: "Zema", value: president.Zema }, { name: "Terceira via", value: 9 }, { name: "Indecisos", value: president.Indecisos }, { name: "Branco/nulo", value: president["Branco/nulo/não vai votar"] }], caption: "Quaest, pp. 8 e 108. Duas perguntas na mesma amostra, sem tabela cruzada. A matriz é um cenário de consistência, não medição." };
  }

  function setupFlows() {
    const family = $("#flow-family"), scenario = $("#flow-scenario");
    const updateOptions = () => {
      const keys = family.value === "poll-runoff" ? Object.keys(data.pesquisas.quaest.segundos_turnos.cenarios) : [family.value === "gov2018" ? "Resultado oficial" : family.value === "cross2022" ? "Primeiro turno 2022" : "Cenário I Quaest"];
      scenario.innerHTML = keys.map(key => `<option>${esc(key)}</option>`).join("");
      renderFlow();
    };
    family.addEventListener("change", updateOptions); scenario.addEventListener("change", renderFlow); updateOptions();
  }

  function renderFlow() {
    const config = flowConfig($("#flow-family").value, $("#flow-scenario").value);
    const matrix = ipf(config.rows, config.cols), svg = $("#flow-chart"); svg.innerHTML = "";
    $("#flow-caption").textContent = config.caption;
    const top = 45, bottom = 600, height = bottom - top, gapL = 9, gapR = 14;
    const scaleL = (height - gapL * (config.rows.length - 1)) / 100, scaleR = (height - gapR * (config.cols.length - 1)) / 100;
    let y = top; const left = config.rows.map(row => { const node = { ...row, x: 170, y, h: row.value * scaleL }; y += node.h + gapL; return node; });
    y = top; const right = config.cols.map(col => { const node = { ...col, x: 980, y, h: col.value * scaleR }; y += node.h + gapR; return node; });
    const sourceOffset = left.map(() => 0), targetOffset = right.map(() => 0);
    const links = [];
    config.rows.forEach((row, i) => config.cols.forEach((col, j) => links.push({ i, j, value: matrix[i][j] })));
    links.sort((a, b) => b.value - a.value).forEach(link => {
      const s = left[link.i], t = right[link.j];
      const sy = s.y + sourceOffset[link.i] + link.value * scaleL / 2;
      const ty = t.y + targetOffset[link.j] + link.value * scaleR / 2;
      sourceOffset[link.i] += link.value * scaleL; targetOffset[link.j] += link.value * scaleR;
      const path = svgEl("path", { d: `M${s.x + 20},${sy} C500,${sy} 650,${ty} ${t.x},${ty}`, class: "flow-link", stroke: score(t.name) < -.2 ? COLORS.red2 : score(t.name) > .2 ? COLORS.green2 : /branco/.test(t.name.toLowerCase()) ? COLORS.ink : COLORS.gold, "stroke-width": Math.max(.4, link.value * 5.2) });
      const title = svgEl("title"); title.textContent = `${s.name} → ${t.name}: ${link.value.toFixed(2)} pontos estimados`; path.append(title); svg.append(path);
    });
    const drawNode = (node, side) => {
      const fill = score(node.name) < -.2 ? COLORS.red : score(node.name) > .2 ? COLORS.green : /branco/.test(node.name.toLowerCase()) ? COLORS.ink : COLORS.gold;
      svg.append(svgEl("rect", { x: node.x, y: node.y, width: 20, height: Math.max(1, node.h), fill, class: "node" }));
      const label = svgEl("text", { x: side === "left" ? node.x - 10 : node.x + 31, y: node.y + Math.min(node.h / 2, 18), class: "node-label", "text-anchor": side === "left" ? "end" : "start" }); label.textContent = node.name; svg.append(label);
      const value = svgEl("text", { x: side === "left" ? node.x - 10 : node.x + 31, y: node.y + Math.min(node.h / 2, 18) + 16, class: "node-value", "text-anchor": side === "left" ? "end" : "start" }); value.textContent = `${node.value.toFixed(1)}%`; svg.append(value);
    };
    left.forEach(node => drawNode(node, "left")); right.forEach(node => drawNode(node, "right"));
  }

  function renderSenate(poll = "quaest") {
    const source = poll === "quaest" ? data.pesquisas.quaest.senado : data.pesquisas.real_time.senado;
    const names = ["Marília Campos", "Carlos Viana", "Domingos Sávio", "Marcelo Aro", "Áurea Carolina", "Marco Antônio Superman"];
    const first = source.primeiro, second = source.segundo;
    $("#senate-chart").innerHTML = names.map(name => `<div class="senate-row"><span class="name">${esc(name)}</span><div class="senate-position"><i style="width:${(first[name] || 0) / 35 * 100}%"></i><b>1º · ${first[name] || 0}%</b></div><div class="senate-position second"><i style="width:${(second[name] || 0) / 35 * 100}%"></i><b>2º · ${second[name] || 0}%</b></div></div>`).join("");
  }

  function setupSenate() {
    $$(".senate-toggle button").forEach(button => button.addEventListener("click", () => {
      $$(".senate-toggle button").forEach(item => item.classList.toggle("active", item === button)); renderSenate(button.dataset.poll);
    }));
    renderSenate();
  }

  function renderProblems() {
    const values = data.pesquisas.quaest.problemas.valores;
    const names = ["Saúde", "Violência", "Economia", "Educação", "Corrupção", "Infraestrutura", "Pobreza/desigualdade", "Desemprego"];
    barChart("#problems-chart", names.map(label => ({ label, value: values[label], color: "red" })), { max: 30 });
  }

  function setupReveal() {
    if (!("IntersectionObserver" in window)) { $$(".reveal").forEach(node => node.classList.add("visible")); return; }
    const observer = new IntersectionObserver(entries => entries.forEach(entry => { if (entry.isIntersecting) { entry.target.classList.add("visible"); observer.unobserve(entry.target); } }), { rootMargin: "0px 0px -8%", threshold: .08 });
    $$(".reveal").forEach(node => observer.observe(node));
  }

  async function init() {
    setupReveal();
    try {
      [data, geo] = await Promise.all([fetch(DATA_URL).then(response => response.json()), fetch(GEO_URL).then(response => response.json())]);
      renderMap(); renderEconomy(); renderRegions(); renderRoutes(); renderCityTable(); renderPolls(); setupFlows(); setupSenate(); renderProblems();
    } catch (error) {
      console.error("Falha ao carregar o atlas de Minas Gerais", error);
      document.body.classList.add("data-error");
    }
  }

  init();
})();
