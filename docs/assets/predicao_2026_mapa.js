/* Mapa interativo por UF da seção #territorio.
 * Camada por cima do SVG estático: sem este arquivo, ou se ele falhar, o mapa
 * gerado em Python continua inteiro, colorido e com links para as fichas.
 * Contrato com o simulador: document dispara "predicao:cenario" com
 * detail = {result, params, central}, em que result vem de Prediction2026.scenario.
 */
(() => {
  "use strict";
  if (typeof document === "undefined") return;

  const NEUTRAL = "#ece8da";
  const LULA = "#b02f21", FLAVIO = "#1457aa";
  const RAMPS = {
    lula: ["#f8ece6", "#e8a593", "#c4513c", "#7c1c11"],
    flavio: ["#eaf0f8", "#98b9e0", "#3f7cc4", "#0d3a78"],
    outros: ["#e9f3ee", "#93ccb4", "#2f9273", "#0b4f3c"],
    neutro: ["#f6f2e4", "#cdc1da", "#8c6fae", "#45276a"],
  };
  const PUOR = ["#b35806", "#542788"];
  const CAVEAT = "A cor mostra a estimativa pontual do modelo. Ela não indica liderança estatisticamente identificada.";

  /* Cores em OKLab: mesma conta de scripts/predicao_2026/mapa.py. */
  const lin = c => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
  const gam = c => { c = Math.min(1, Math.max(0, c)); return c <= 0.0031308 ? 12.92 * c : 1.055 * c ** (1 / 2.4) - 0.055; };
  const labCache = new Map();
  function toLab(hex) {
    if (labCache.has(hex)) return labCache.get(hex);
    const [r, g, b] = [1, 3, 5].map(i => lin(parseInt(hex.slice(i, i + 2), 16) / 255));
    const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b);
    const m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b);
    const s = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
    const out = [0.2104542553 * l + 0.793617785 * m - 0.0040720468 * s,
      1.9779984951 * l - 2.428592205 * m + 0.4505937099 * s,
      0.0259040371 * l + 0.7827717662 * m - 0.808675766 * s];
    labCache.set(hex, out);
    return out;
  }
  function fromLab([L, a, b]) {
    const l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3;
    const m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3;
    const s = (L - 0.0894841775 * a - 1.291485548 * b) ** 3;
    const rgb = [4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
      -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
      -0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s];
    return "#" + rgb.map(c => Math.round(255 * gam(c)).toString(16).padStart(2, "0")).join("");
  }
  function mix(c0, c1, t) {
    const a = toLab(c0), b = toLab(c1);
    return fromLab(a.map((x, i) => x + (b[i] - x) * t));
  }
  function ramp(stops, t) {
    const x = Math.min(1, Math.max(0, t)) * (stops.length - 1);
    const i = Math.min(stops.length - 2, Math.floor(x));
    return mix(stops[i], stops[i + 1], x - i);
  }

  const nf = new Map();
  function fmt(x, places = 1) {
    if (!nf.has(places)) nf.set(places, new Intl.NumberFormat("pt-BR", { minimumFractionDigits: places, maximumFractionDigits: places }));
    return nf.get(places).format(x).replace("-", "−");
  }
  const signed = (x, places = 1) => (x > 0 ? "+" : "") + fmt(Math.abs(x) < 0.5 * 10 ** -places ? 0 : x, places);
  const mi = x => fmt(x / 1e6, 2) + " mi";
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

  function niceStep(span) {
    const raw = span / 4, p = 10 ** Math.floor(Math.log10(raw || 1));
    return [1, 2, 2.5, 5, 10].map(k => k * p).find(k => k >= raw) || 10 * p;
  }
  function symmetric(values) {
    const top = Math.max(1, ...values.map(Math.abs));
    const step = top <= 2 ? 0.5 : top <= 5 ? 1 : top <= 20 ? 5 : 10;
    return Math.max(step, step * Math.ceil(top / step));
  }

  function init() {
    const root = document.getElementById("mapa-explorador");
    const dataNode = document.getElementById("prediction-data");
    if (!root || !dataNode) return;
    const data = JSON.parse(dataNode.textContent);
    let extra = { passado: {}, nomes: {} };
    try { extra = JSON.parse(document.getElementById("mapa-2022").textContent); } catch { /* swing fica indisponível */ }
    const $ = id => document.getElementById(id);
    const svg = $("mx-svg"), canvas = $("mx-canvas"), tip = $("mx-tip"), panel = $("mx-panel");
    const links = [...root.querySelectorAll("a.mx-uf")];
    if (!svg || !canvas || !tip || !panel || links.length !== 27) return;

    const states = Object.fromEntries(data.estados.map(s => [s.uf, s]));
    const priorWeight = data.configuracao.peso_prior;
    const names = extra.nomes || {};
    const past = extra.passado || {};
    const nameOf = uf => (names[uf] || uf) + (uf === "ZZ" ? "" : " (" + uf + ")");

    function normalize(rows) {
      const out = {};
      for (const r of rows) {
        const valid = r.lula + r.flavio + r.outros;
        if (!r.uf || !(valid > 0) || !(r.eleitorado > 0)) continue;
        out[r.uf] = { ...r, validos: valid, margem: 100 * (r.flavio - r.lula) / valid,
          pct: { lula: 100 * r.lula / valid, flavio: 100 * r.flavio / valid, outros: 100 * r.outros / valid } };
      }
      return out;
    }
    const central = normalize(data.central.ufs);

    const pctMetric = (k, label, colors) => ({ title: label + ", % dos votos válidos", short: label, unit: "%", get: r => r.pct[k], ramp: colors, scenario: true });
    const METRICS = {
      margem: { title: "Diferença Flávio menos Lula nos votos válidos", short: "Flávio menos Lula", unit: "pp", get: r => r.margem, party: true, scenario: true,
        legend: "Diferença Flávio menos Lula, em pontos percentuais dos votos válidos" },
      lula: pctMetric("lula", "Lula", RAMPS.lula),
      flavio: pctMetric("flavio", "Flávio Bolsonaro", RAMPS.flavio),
      outros: pctMetric("outros", "Demais candidaturas", RAMPS.outros),
      comparecimento: { title: "Comparecimento previsto, % do eleitorado", short: "Comparecimento", unit: "%", get: r => 100 * r.comparecimento / r.eleitorado, ramp: RAMPS.neutro, scenario: true },
      abstencao: { title: "Abstenção esperada, em milhões de eleitores", short: "Abstenção", unit: "mi", get: r => r.abstencao / 1e6, ramp: RAMPS.neutro, sqrt: true, scenario: true,
        note: "Escala de raiz quadrada: São Paulo sozinho tem mais ausentes que vários estados inteiros." },
      eleitorado: { title: "Eleitorado apto em 2026, em milhões", short: "Eleitorado", unit: "mi", get: r => r.eleitorado / 1e6, ramp: RAMPS.neutro, sqrt: true, scenario: false,
        note: "Escala de raiz quadrada. O eleitorado é do TSE e não muda com o cenário." },
      swing_flavio: { title: "Flávio em 2026 menos Jair Bolsonaro no 1º turno de 2022, pp dos válidos", short: "Flávio 2026 menos Bolsonaro 2022", unit: "pp", diverging: true, scenario: true,
        get: r => (past[r.uf] ? r.pct.flavio - past[r.uf].bolsonaro : null),
        note: "Comparação de agregados por UF com o resultado oficial do TSE em 2022. Não é transferência de eleitores individuais." },
      swing_lula: { title: "Lula em 2026 menos Lula no 1º turno de 2022, pp dos válidos", short: "Lula 2026 menos Lula 2022", unit: "pp", diverging: true, scenario: true,
        get: r => (past[r.uf] ? r.pct.lula - past[r.uf].lula : null),
        note: "Comparação de agregados por UF com o resultado oficial do TSE em 2022. Não é transferência de eleitores individuais." },
      ondas: { title: "Pesquisas estaduais usadas no pooling da UF", short: "Pesquisas usadas", unit: "", places: 0, ramp: RAMPS.neutro, scenario: false,
        get: r => (states[r.uf] ? states[r.uf].pesquisas.length : null),
        note: "Ondas estaduais elegíveis depois da regra de recência. Mais ondas não significa amostra maior: o peso de cada uma vem do n efetivo e da idade." },
      prior: { title: "Peso da prior territorial no pooling da UF, %", short: "Peso da prior", unit: "%", ramp: RAMPS.neutro, scenario: false,
        get: r => (states[r.uf] ? 100 * states[r.uf].peso_prior : null),
        note: "Quanto maior, mais a UF depende do histórico de 2022 com o movimento nacional, e menos das pesquisas do próprio estado." },
    };

    let metric = "margem", view = "central", scenario = null, selected = null, hovered = null, pending = false;

    function formatValue(m, v, diff) {
      if (v === null || v === undefined || !Number.isFinite(v)) return "sem dado";
      const places = m.places ?? (m.unit === "mi" ? 2 : 1);
      if (diff) return signed(v, m.unit === "mi" ? 2 : 1) + (m.unit === "mi" ? " mi" : " pp");
      if (m.unit === "pp") return signed(v, places) + " pp";
      if (m.unit === "mi") return fmt(v, places) + " mi";
      return fmt(v, places) + (m.unit ? m.unit : "");
    }

    function currentRows() {
      if (view === "central" || !scenario) return central;
      return scenario;
    }

    function valuesFor(m) {
      const out = {};
      const diff = view === "diff" && scenario && m.scenario;
      for (const uf of Object.keys(central)) {
        if (diff) {
          const a = scenario[uf] ? m.get(scenario[uf]) : null, b = m.get(central[uf]);
          out[uf] = a === null || b === null ? null : a - b;
        } else {
          const rows = currentRows();
          const r = rows[uf] || null;
          out[uf] = r ? m.get(r) : null;
        }
      }
      return { values: out, diff };
    }

    function scaleFor(m, values, diff) {
      const domestic = Object.entries(values).filter(([uf, v]) => uf !== "ZZ" && v !== null && Number.isFinite(v)).map(([, v]) => v);
      const both = !diff && scenario && m.scenario ? Object.keys(central).filter(uf => uf !== "ZZ").flatMap(uf => [central[uf], scenario[uf]].filter(Boolean).map(m.get)) : domestic;
      if (diff || m.party || m.diverging) {
        const D = symmetric(diff ? domestic : both.filter(v => v !== null));
        const [neg, pos] = (m.party && !diff) || (diff && metric === "margem") ? [LULA, FLAVIO] : PUOR;
        const color = v => mix(NEUTRAL, v > 0 ? pos : neg, Math.min(1, Math.abs(v) / D));
        const ticks = [-D, -D / 2, 0, D / 2, D].map(v => ({ v, t: (v + D) / (2 * D) }));
        const label = v => {
          if (!v) return "0";
          const n = fmt(Math.abs(v), Number.isInteger(v) ? 0 : 1);
          if ((m.party && !diff) || (diff && metric === "margem")) return (v < 0 ? "Lula +" : "Flávio +") + n;
          return (v < 0 ? "−" : "+") + n;
        };
        return { color, ticks, label, gradient: Array.from({ length: 17 }, (_, i) => color(-D + i * D / 8)) };
      }
      const vals = both.filter(v => v !== null);
      if (m.sqrt) {
        const top = Math.max(...vals);
        const hi = niceStep(top) * Math.ceil(top / niceStep(top));
        const t = v => Math.sqrt(Math.max(0, v) / hi);
        const color = v => ramp(m.ramp, t(v));
        const tickValues = [0, hi / 16, hi / 4, hi * 9 / 16, hi].map(v => (v < 1 ? Math.round(v * 10) / 10 : Math.round(v)));
        return { color, ticks: tickValues.map(v => ({ v, t: t(v) })), label: v => fmt(v, v < 1 && v > 0 ? 1 : 0),
          gradient: Array.from({ length: 11 }, (_, i) => ramp(m.ramp, i / 10)) };
      }
      let lo = Math.min(...vals), hi = Math.max(...vals);
      if (hi - lo < 1e-9) { lo -= 1; hi += 1; }
      const step = m.places === 0 ? Math.max(1, Math.round(niceStep(hi - lo))) : niceStep(hi - lo);
      lo = Math.floor(lo / step) * step; hi = Math.ceil(hi / step) * step;
      if (m.unit === "%" && lo < 0) lo = 0;
      const t = v => (v - lo) / (hi - lo);
      const color = v => ramp(m.ramp, t(v));
      const n = Math.round((hi - lo) / step);
      const every = Math.max(1, Math.ceil(n / 5));
      const ticks = [];
      for (let i = 0; i <= n; i += every) ticks.push({ v: lo + i * step, t: (i * step) / (hi - lo) });
      if (ticks[ticks.length - 1].t < 1) ticks.push({ v: hi, t: 1 });
      const places = step < 1 ? 1 : 0;
      return { color, ticks, label: v => fmt(v, m.places ?? places), gradient: Array.from({ length: 11 }, (_, i) => ramp(m.ramp, i / 10)) };
    }

    function scoreLine(r) {
      return r ? "Lula " + fmt(r.pct.lula) + "% · Flávio " + fmt(r.pct.flavio) + "% · Demais " + fmt(r.pct.outros) + "%" : "Fora deste cenário";
    }

    let last = null;
    function render() {
      pending = false;
      const m = METRICS[metric];
      const effectiveView = !scenario ? "central" : view === "diff" && !m.scenario ? "cenario" : view;
      const { values, diff } = valuesFor(m);
      const scale = scaleFor(m, values, diff);
      last = { m, values, diff, scale };
      const viewLabel = diff ? "cenário do leitor menos previsão central" : effectiveView === "cenario" ? "cenário do leitor" : "previsão central";
      $("mx-title").textContent = (diff ? "Cenário do leitor menos central: " + m.short : m.title) + (diff ? "" : ", " + viewLabel);
      for (const a of links) {
        const uf = a.dataset.uf, v = values[uf];
        const path = a.querySelector("path");
        path.setAttribute("fill", v === null ? "#d9d6cc" : scale.color(v));
        const r = currentRows()[uf] || central[uf];
        a.setAttribute("aria-label", nameOf(uf) + ": " + m.short + " " + formatValue(m, v, diff) + ". " + scoreLine(r) + " dos válidos. Enter abre a ficha.");
      }
      $("mx-legend-title").textContent = diff ? "Cenário do leitor menos previsão central: " + (m.legend || m.title) : (m.legend || m.title);
      $("mx-ramp").style.background = "linear-gradient(90deg, " + scale.gradient.map((c, i, a) => c + " " + (100 * i / (a.length - 1)).toFixed(2) + "%").join(", ") + ")";
      $("mx-ticks").innerHTML = scale.ticks.map((k, i, a) => '<span class="' + (i === 0 ? "mx-tick-start" : i === a.length - 1 ? "mx-tick-end" : "") + '" style="left:' + (100 * k.t).toFixed(2) + '%">' + esc(scale.label(k.v)) + "</span>").join("");
      const note = root.querySelector(".mx-legend-note");
      note.textContent = (m.note ? m.note + " " : "") + CAVEAT;
      for (const b of root.querySelectorAll("[data-metric]")) b.setAttribute("aria-pressed", String(b.dataset.metric === metric));
      const bar = $("mx-scenario");
      if (scenario) {
        bar.hidden = false;
        $("mx-scenario-text").textContent = effectiveView === "central"
          ? "Cenário do leitor guardado. O mapa mostra a previsão central."
          : diff ? "Cenário do leitor: o mapa mostra quanto o seu cenário difere da previsão central, UF por UF."
            : "Cenário do leitor: o mapa mostra as hipóteses escolhidas no simulador, não a previsão da Arvor.";
        for (const b of bar.querySelectorAll("[data-view]")) {
          b.setAttribute("aria-pressed", String(b.dataset.view === effectiveView));
          b.disabled = b.dataset.view === "diff" && !m.scenario;
        }
        $("mx-back").disabled = effectiveView === "central";
      } else bar.hidden = true;
      updateExterior();
      if (hovered) showTip(hovered.uf, hovered.anchor);
      if (selected) openPanel(selected, false);
    }
    function schedule() { if (!pending) { pending = true; requestAnimationFrame(render); } }

    function updateExterior() {
      const card = $("mx-zz");
      if (!card) return;
      const { m, values, diff } = last;
      const r = currentRows().ZZ;
      $("mx-zz-value").textContent = r || diff ? m.short + " " + formatValue(m, values.ZZ, diff) : "Exterior fora deste cenário";
      $("mx-zz-score").textContent = r ? scoreLine(r) + " · " + mi(r.eleitorado) + " de eleitores" : "O leitor excluiu o exterior no simulador.";
    }

    function showTip(uf, anchor) {
      const { m, values, diff } = last;
      const r = currentRows()[uf] || central[uf];
      let html = "<b>" + esc(nameOf(uf)) + '</b><span class="mx-tip-value">' + esc(m.short + ": " + formatValue(m, values[uf], diff)) + "</span>";
      if (diff) html += '<span class="mx-tip-score">Central ' + esc(formatValue(m, m.get(central[uf]), false)) + "; cenário " + esc(scenario[uf] ? formatValue(m, m.get(scenario[uf]), false) : "sem dado") + "</span>";
      html += '<span class="mx-tip-score">' + esc(scoreLine(r)) + "</span>";
      tip.innerHTML = html;
      tip.hidden = false;
      const box = canvas.getBoundingClientRect(), w = tip.offsetWidth, h = tip.offsetHeight;
      let x = anchor.x - box.left + 14, y = anchor.y - box.top + 14;
      if (x + w > box.width - 4) x = anchor.x - box.left - w - 14;
      if (y + h > box.height - 4) y = anchor.y - box.top - h - 14;
      tip.style.left = Math.max(4, x) + "px";
      tip.style.top = Math.max(4, y) + "px";
      hovered = { uf, anchor };
    }
    function hideTip() { tip.hidden = true; hovered = null; $("mx-hover").setAttribute("visibility", "hidden"); }
    function highlight(uf) {
      const use = $("mx-hover");
      use.setAttribute("href", "#mx-path-" + uf);
      use.setAttribute("visibility", "visible");
    }
    const centerOf = el => { const b = el.getBoundingClientRect(); return { x: b.left + b.width / 2, y: b.top + b.height / 2 }; };

    function pollRows(s) {
      const total = priorWeight + s.pesquisas.reduce((a, p) => a + p.peso_modelo, 0);
      if (!s.pesquisas.length) return '<p class="mx-panel-empty">Sem pesquisa recente elegível: prior de 2022 com o movimento nacional de 2026.</p>';
      return '<div class="mx-panel-scroll"><table><thead><tr><th scope="col">Casa</th><th scope="col">Fim do campo</th><th scope="col">n</th><th scope="col">Peso</th></tr></thead><tbody>' +
        s.pesquisas.map(p => "<tr><td>" + esc(p.instituto) + "</td><td>" + esc(p.campo.fim.split("-").reverse().join("/")) + "</td><td>" + fmt(p.n, 0) + "</td><td>" + fmt(100 * p.peso_modelo / total, 1) + "%</td></tr>").join("") +
        "<tr><td>Prior territorial</td><td>2022</td><td>" + fmt(priorWeight, 0) + "*</td><td>" + fmt(100 * s.peso_prior, 1) + "%</td></tr></tbody></table></div>" +
        '<p class="mx-panel-empty">* Entrevistas equivalentes atribuídas à prior. Peso é a fatia de cada fonte no pooling territorial da UF.</p>';
    }

    function openPanel(uf, announce = true) {
      const s = states[uf], c = central[uf];
      if (!s || !c) return;
      selected = uf;
      const sc = scenario && view !== "central" ? scenario[uf] : null;
      const shown = sc || c;
      const cols = sc ? ["Central", "Seu cenário"] : ["Central"];
      const block = (k, label, color) => "<tr><th scope=\"row\"><span class=\"mx-swatch\" style=\"background:" + color + "\"></span>" + label + "</th>" +
        [c, sc].filter(Boolean).map(r => "<td>" + fmt(r.pct[k]) + "%<br>" + mi(r[k]) + "</td>").join("") + "</tr>";
      const hist = s.tse && s.tse.historico_2022;
      const pastTurnout = hist && hist.aptos ? 100 * hist.comparecimento / hist.aptos : null;
      const demais = Object.entries({ renan_santos: "Renan Santos", cury: "Augusto Cury", caiado: "Ronaldo Caiado", zema: "Romeu Zema", restantes: "Demais nomes" })
        .map(([k, label]) => "<tr><td>" + label + "</td><td>" + mi(shown.demais[k]) + "</td><td>" + fmt(100 * shown.demais[k] / shown.validos) + "%</td></tr>").join("");
      const signal = s.sinal_comparecimento;
      const pastRow = past[uf];
      panel.innerHTML =
        '<h4 id="mx-panel-title">' + esc(nameOf(uf)) + "</h4>" +
        '<p class="mx-panel-sub">' + esc(s.regiao) + " · " + mi(s.eleitorado) + " de eleitores em 2026 · " + (sc ? "previsão central e cenário do leitor" : "previsão central") + "</p>" +
        "<h5>Placar nos votos válidos</h5><div class=\"mx-panel-scroll\"><table><thead><tr><th scope=\"col\">Bloco</th>" + cols.map(x => "<th scope=\"col\">" + x + "</th>").join("") + "</tr></thead><tbody>" +
        block("lula", "Lula", LULA) + block("flavio", "Flávio", FLAVIO) + block("outros", "Demais", "#0f7f5f") +
        "<tr><th scope=\"row\">Flávio menos Lula</th>" + [c, sc].filter(Boolean).map(r => "<td>" + signed(r.margem) + " pp</td>").join("") + "</tr></tbody></table></div>" +
        "<h5>Urna" + (sc ? ", cenário do leitor" : "") + "</h5><dl>" +
        "<dt>Eleitorado 2026</dt><dd>" + mi(shown.eleitorado) + "</dd>" +
        "<dt>Comparecimento previsto</dt><dd>" + fmt(100 * shown.comparecimento / shown.eleitorado) + "% (" + mi(shown.comparecimento) + ")</dd>" +
        (pastTurnout !== null ? "<dt>Comparecimento em 2022</dt><dd>" + fmt(pastTurnout) + "%</dd>" : "") +
        "<dt>Abstenção esperada</dt><dd>" + mi(shown.abstencao) + "</dd>" +
        "<dt>Brancos e nulos</dt><dd>" + mi(shown.branco_nulo) + " (" + fmt(100 * shown.branco_nulo / shown.comparecimento) + "% dos votantes)</dd>" +
        (pastRow ? "<dt>Mudança desde 2022</dt><dd>Flávio " + signed(shown.pct.flavio - pastRow.bolsonaro) + " pp sobre Bolsonaro; Lula " + signed(shown.pct.lula - pastRow.lula) + " pp</dd>" : "") +
        "</dl><h5>Abertura dos demais</h5><div class=\"mx-panel-scroll\"><table><thead><tr><th scope=\"col\">Nome</th><th scope=\"col\">Votos</th><th scope=\"col\">Válidos</th></tr></thead><tbody>" + demais + "</tbody></table></div>" +
        "<h5>Pesquisas usadas</h5>" + pollRows(s) +
        "<dl><dt>Peso da prior</dt><dd>" + fmt(100 * s.peso_prior, 1) + "%</dd>" +
        "<dt>Eleitor provável</dt><dd>" + (signal ? "Há cruzamento publicado por hábito de comparecimento" + (signal.rodada ? " (" + esc(signal.rodada) + ")" : "") : "Sem cruzamento elegível: fator neutro") + "</dd>" +
        "<dt>Reserva de 2º turno</dt><dd>" + (s.reserva && (s.reserva[0] || s.reserva[1]) ? "Lula +" + fmt(100 * s.reserva[0]) + " pp, Flávio +" + fmt(100 * s.reserva[1]) + " pp" : "Não medida") + "</dd></dl>" +
        '<p class="mx-panel-empty">Reserva: ganho de cada finalista do 1º para o 2º turno na mesma amostra, em pontos dos válidos. Não é migração individual medida.</p>' +
        '<div class="mx-panel-actions"><a href="#estado-' + uf + '" data-open="' + uf + '">Ficha estadual completa</a><button type="button" class="mx-close">Fechar ficha</button></div>';
      const sel = $("mx-sel");
      if (uf === "ZZ") sel.setAttribute("visibility", "hidden");
      else { sel.setAttribute("href", "#mx-path-" + uf); sel.setAttribute("visibility", "visible"); }
      for (const a of links) a.toggleAttribute("aria-current", a.dataset.uf === uf);
      const zz = $("mx-zz");
      if (zz) zz.toggleAttribute("aria-current", uf === "ZZ");
      if (announce) $("mx-live").textContent = "Ficha de " + nameOf(uf) + " aberta ao lado do mapa.";
    }
    function emptyPanel() {
      selected = null;
      panel.innerHTML = '<h4 id="mx-panel-title">Ficha do estado</h4><p class="mx-panel-empty">Clique, toque ou use Tab e Enter num estado para abrir a ficha aqui. As setas do teclado levam ao estado vizinho.</p>';
      $("mx-sel").setAttribute("visibility", "hidden");
      for (const a of links) a.removeAttribute("aria-current");
      if ($("mx-zz")) $("mx-zz").removeAttribute("aria-current");
    }
    function closePanel() {
      const uf = selected;
      emptyPanel();
      const target = uf === "ZZ" ? $("mx-zz") : links.find(a => a.dataset.uf === uf);
      if (target) target.focus();
    }

    const centers = Object.fromEntries(links.map(a => [a.dataset.uf, [Number(a.dataset.cx), Number(a.dataset.cy)]]));
    function neighbor(uf, dx, dy) {
      const [x0, y0] = centers[uf];
      let best = null, score = Infinity;
      for (const [k, [x, y]] of Object.entries(centers)) {
        if (k === uf) continue;
        const vx = x - x0, vy = y - y0, d = Math.hypot(vx, vy), cos = (vx * dx + vy * dy) / d;
        if (cos <= 0.35) continue;
        const sc = d * (1 + 2 * (1 - cos));
        if (sc < score) { score = sc; best = k; }
      }
      return best;
    }

    for (const a of links) {
      const uf = a.dataset.uf;
      a.setAttribute("role", "button");
      a.setAttribute("aria-controls", "mx-panel");
      a.addEventListener("pointermove", e => { if (e.pointerType !== "touch") { highlight(uf); showTip(uf, { x: e.clientX, y: e.clientY }); } });
      a.addEventListener("pointerleave", hideTip);
      a.addEventListener("focus", () => { highlight(uf); showTip(uf, centerOf(a.querySelector("path"))); });
      a.addEventListener("blur", hideTip);
      a.addEventListener("click", e => { e.preventDefault(); openPanel(uf); if (e.pointerType === "touch") hideTip(); });
      a.addEventListener("keydown", e => {
        const dirs = { ArrowRight: [1, 0], ArrowLeft: [-1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] };
        if (e.key === " ") { e.preventDefault(); openPanel(uf); }
        else if (e.key === "Escape") hideTip();
        else if (dirs[e.key]) {
          e.preventDefault();
          const next = neighbor(uf, ...dirs[e.key]);
          if (next) links.find(l => l.dataset.uf === next).focus();
        }
      });
    }
    const zz = $("mx-zz");
    if (zz) {
      zz.setAttribute("role", "button");
      zz.setAttribute("aria-controls", "mx-panel");
      zz.addEventListener("click", e => { e.preventDefault(); openPanel("ZZ"); });
      zz.addEventListener("keydown", e => { if (e.key === " ") { e.preventDefault(); openPanel("ZZ"); } });
    }
    panel.addEventListener("click", e => {
      const link = e.target.closest("[data-open]");
      if (link) { const d = document.getElementById("estado-" + link.dataset.open); if (d && d.tagName === "DETAILS") d.open = true; return; }
      if (e.target.closest(".mx-close")) closePanel();
    });
    root.querySelectorAll("[data-metric]").forEach(b => b.addEventListener("click", () => { metric = b.dataset.metric; render(); }));
    root.querySelectorAll("[data-view]").forEach(b => b.addEventListener("click", () => { view = b.dataset.view; render(); }));
    $("mx-back").addEventListener("click", () => { view = "central"; render(); });

    function receive(d) {
      if (!d.result || !Array.isArray(d.result.ufs)) return;
      if (d.central) { scenario = null; view = "central"; }
      else {
        const rows = normalize(d.result.ufs);
        if (!Object.keys(rows).length) return;
        scenario = rows;
        if (view === "central") view = "cenario";
      }
      schedule();
    }
    document.addEventListener("predicao:cenario", e => receive(e.detail || {}));

    render();
    for (const t of svg.querySelectorAll("a.mx-uf > path > title")) t.remove();
    emptyPanel();
    $("mx-controls").hidden = false;
    root.dataset.mode = "interativo";
    /* O simulador guarda o último cenário em window.predicaoCenario: cobre o evento disparado antes deste arquivo carregar. */
    if (window.predicaoCenario) receive(window.predicaoCenario);
  }

  function boot() {
    try { init(); } catch (error) {
      const root = document.getElementById("mapa-explorador");
      if (root) root.dataset.mode = "estatico";
      if (typeof console !== "undefined") console.warn("Mapa interativo indisponível; o mapa estático permanece.", error);
    }
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
