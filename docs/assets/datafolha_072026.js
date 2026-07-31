/* Dossiê Datafolha julho/2026 — comportamento do explorador territorial.
   Sem dependências externas: barra de progresso, reveal por interseção,
   nav ativa, gráfico de dispersão dos 139 municípios e tabela ordenável. */

(function () {
  "use strict";

  var root = document.documentElement;
  root.classList.add("js");

  /* ---------- barra de progresso ---------- */
  var bar = document.querySelector(".progress");
  function onScroll() {
    if (!bar) return;
    var max = document.body.scrollHeight - window.innerHeight;
    bar.style.width = max > 0 ? (window.scrollY / max) * 100 + "%" : "0";
  }
  addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* ---------- reveal ---------- */
  var revealables = Array.prototype.slice.call(document.querySelectorAll(".reveal"));
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("in");
            io.unobserve(entry.target);
          }
        });
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.08 }
    );
    revealables.forEach(function (el) {
      io.observe(el);
    });
  } else {
    revealables.forEach(function (el) {
      el.classList.add("in");
    });
  }
  addEventListener("load", function () {
    setTimeout(function () {
      revealables.forEach(function (el) {
        el.classList.add("in");
      });
    }, 2500);
  });

  /* ---------- nav ativa ---------- */
  var links = Array.prototype.slice.call(document.querySelectorAll(".nav a[href^='#']"));
  var sections = links
    .map(function (a) {
      return document.querySelector(a.getAttribute("href"));
    })
    .filter(Boolean);
  if (sections.length && "IntersectionObserver" in window) {
    var navObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          links.forEach(function (a) {
            a.classList.toggle("active", a.getAttribute("href") === "#" + entry.target.id);
          });
        });
      },
      { rootMargin: "-45% 0px -50% 0px" }
    );
    sections.forEach(function (s) {
      navObserver.observe(s);
    });
  }

  /* ---------- renda: aluvial de distribuição e slope da reponderação ---------- */
  (function renda() {
    var data = window.__DATAFOLHA_RENDA__;
    var flow = document.getElementById("grafico-renda");
    var slope = document.getElementById("grafico-reponderacao");
    if (!data || (!flow && !slope)) return;

    var BANDS = ["ate2", "de2a5", "de5a10", "mais10"];
    var BAND_COLOR = {
      ate2: "#e0483a",
      de2a5: "#f0a930",
      de5a10: "#45c9c2",
      mais10: "#cfe63c"
    };
    var BAND_SHORT = {
      ate2: "até 2 SM",
      de2a5: "2 a 5 SM",
      de5a10: "5 a 10 SM",
      mais10: "10+ SM"
    };

    function num(value, digits) {
      return value.toLocaleString("pt-BR", {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits
      });
    }

    if (flow) {
      var columns = [
        { key: "datafolha_bases_do_cruzamento", title: "Datafolha", sub: "amostra de julho" },
        { key: "pnad_domicilios", title: "PNAD", sub: "domicílios" },
        { key: "pnad_pessoas_16", title: "PNAD", sub: "pessoas 16+" }
      ];
      var W = 1000;
      var H = 430;
      var top = 62;
      var bottom = 34;
      var colW = 104;
      var xs = [96, 448, 800];
      var parts = [];

      var stacks = columns.map(function (col, ci) {
        var dist = data.distribuicoes_pct[col.key];
        var acc = top;
        var segs = {};
        BANDS.forEach(function (band) {
          var h = (dist[band] / 100) * (H - top - bottom);
          segs[band] = { y0: acc, y1: acc + h, value: dist[band] };
          acc += h;
        });
        parts.push(
          '<text class="col-title" x="' +
            (xs[ci] + colW / 2) +
            '" y="30" text-anchor="middle">' +
            col.title +
            "</text>"
        );
        parts.push(
          '<text class="col-sub" x="' +
            (xs[ci] + colW / 2) +
            '" y="48" text-anchor="middle">' +
            col.sub +
            "</text>"
        );
        return segs;
      });

      // fitas entre colunas
      for (var ci = 0; ci < stacks.length - 1; ci++) {
        BANDS.forEach(function (band) {
          var a = stacks[ci][band];
          var b = stacks[ci + 1][band];
          var x1 = xs[ci] + colW;
          var x2 = xs[ci + 1];
          var cx = (x1 + x2) / 2;
          parts.push(
            '<path class="ribbon" fill="' +
              BAND_COLOR[band] +
              '" d="M' +
              x1 +
              "," +
              a.y0 +
              " C" +
              cx +
              "," +
              a.y0 +
              " " +
              cx +
              "," +
              b.y0 +
              " " +
              x2 +
              "," +
              b.y0 +
              " L" +
              x2 +
              "," +
              b.y1 +
              " C" +
              cx +
              "," +
              b.y1 +
              " " +
              cx +
              "," +
              a.y1 +
              " " +
              x1 +
              "," +
              a.y1 +
              ' Z"/>'
          );
        });
      }

      // colunas
      stacks.forEach(function (segs, ci) {
        BANDS.forEach(function (band) {
          var s = segs[band];
          parts.push(
            '<rect x="' +
              xs[ci] +
              '" y="' +
              s.y0 +
              '" width="' +
              colW +
              '" height="' +
              Math.max(s.y1 - s.y0, 1) +
              '" fill="' +
              BAND_COLOR[band] +
              '" rx="2"/>'
          );
          if (s.y1 - s.y0 > 22) {
            parts.push(
              '<text class="seg-value" x="' +
                (xs[ci] + colW / 2) +
                '" y="' +
                ((s.y0 + s.y1) / 2 + 5) +
                '" text-anchor="middle">' +
                num(s.value, 1) +
                "%</text>"
            );
          }
          if (ci === 0) {
            parts.push(
              '<text class="band-label" x="' +
                (xs[0] - 14) +
                '" y="' +
                ((s.y0 + s.y1) / 2 + 4) +
                '" text-anchor="end">' +
                BAND_SHORT[band] +
                "</text>"
            );
          }
        });
      });

      flow.querySelector("svg").innerHTML = parts.join("");
    }

    if (slope) {
      var picks = [
        "Datafolha · bases do cruzamento",
        "PNAD · domicílios",
        "PNAD · pessoas de 16 anos ou mais"
      ];
      var short = ["Datafolha", "PNAD domicílios", "PNAD pessoas 16+"];
      var rows = picks.map(function (name) {
        return data.segundo_turno.filter(function (item) {
          return item.cenario === name;
        })[0];
      });
      if (rows.some(function (r) { return !r; })) return;

      var SW = 1000;
      var SH = 380;
      var padL = 84;
      var padR = 120;
      var padT = 46;
      var padB = 52;
      var lo = 41;
      var hi = 49;
      var sx = function (i) {
        return padL + (i * (SW - padL - padR)) / (picks.length - 1);
      };
      var sy = function (v) {
        return SH - padB - ((v - lo) / (hi - lo)) * (SH - padT - padB);
      };
      var out = [];
      [42, 44, 46, 48].forEach(function (v) {
        out.push(
          '<line class="gridline" x1="' + padL + '" x2="' + (SW - padR) + '" y1="' + sy(v) + '" y2="' + sy(v) + '"/>'
        );
        out.push('<text class="axis-y" x="' + (padL - 12) + '" y="' + (sy(v) + 4) + '" text-anchor="end">' + v + "%</text>");
      });
      rows.forEach(function (row, i) {
        out.push('<text class="col-sub" x="' + sx(i) + '" y="' + (SH - 18) + '" text-anchor="middle">' + short[i] + "</text>");
        out.push('<line class="tick" x1="' + sx(i) + '" x2="' + sx(i) + '" y1="' + padT + '" y2="' + (SH - padB) + '"/>');
      });
      [
        { key: "lula", color: "#e0483a", name: "Lula", valueDy: -16, nameDy: -8 },
        { key: "flavio", color: "#3f8fd6", name: "Flávio", valueDy: 28, nameDy: 20 }
      ].forEach(function (serie) {
        var pts = rows.map(function (row, i) {
          return [sx(i), sy(row.resultado[serie.key])];
        });
        out.push(
          '<polyline class="slope-line" stroke="' +
            serie.color +
            '" points="' +
            pts
              .map(function (p) {
                return p[0] + "," + p[1];
              })
              .join(" ") +
            '"/>'
        );
        pts.forEach(function (p, i) {
          out.push('<circle class="slope-dot" cx="' + p[0] + '" cy="' + p[1] + '" r="7" fill="' + serie.color + '"/>');
          out.push(
            '<text class="slope-value" x="' +
              (i === 0 ? p[0] + 12 : i === pts.length - 1 ? p[0] - 12 : p[0]) +
              '" y="' +
              (p[1] + serie.valueDy) +
              '" text-anchor="' +
              (i === 0 ? "start" : i === pts.length - 1 ? "end" : "middle") +
              '" fill="' +
              serie.color +
              '">' +
              num(rows[i].resultado[serie.key], 1) +
              "</text>"
          );
        });
        var last = pts[pts.length - 1];
        out.push(
          '<text class="slope-name" x="' +
            (last[0] + 18) +
            '" y="' +
            (last[1] + serie.nameDy) +
            '" fill="' +
            serie.color +
            '">' +
            serie.name +
            "</text>"
        );
      });
      slope.querySelector("svg").innerHTML = out.join("");
    }
  })();

  /* ---------- Sankey 1º → 2º turno: barras = fato, fluxos = inferência ---------- */
  (function fluxo() {
    var data = window.__DATAFOLHA_FLUXO__;
    var host = document.getElementById("grafico-fluxo");
    if (!data || !host) return;

    var COLOR = { Lula: "#e0483a", "Flávio": "#3f8fd6", "Branco/nulo": "#8a8578", "Não sabe": "#5f5c52" };
    var ORIGEM_COR = {
      "Lula (PT)": "#e0483a",
      "Flávio Bolsonaro (PL)": "#3f8fd6",
      "Ronaldo Caiado (PSD)": "#f0a930",
      "Romeu Zema (Novo)": "#34b47e",
      "Renan Santos (Missão)": "#9b7bd4",
      "Augusto Cury (Avante)": "#c9a227",
      "Samara Martins (UP)": "#d1584f",
      "Cabo Daciolo (Mobiliza)": "#45c9c2",
      "Rui C. Pimenta (PCO)": "#b4645c",
      "Branco/nulo/nenhum": "#8a8578",
      "Não sabe": "#5f5c52"
    };
    var DESTINOS = ["Lula", "Flávio", "Branco/nulo", "Não sabe"];

    var W = 1000;
    var H = 560;
    var padT = 40;
    var padB = 26;
    var barW = 15;
    var xL = 208;
    var xR = W - 232;
    var gap = 9;

    var origens = Object.keys(data.fluxo);
    var totOrigem = {};
    var soma = 0;
    origens.forEach(function (o) {
      var t = DESTINOS.reduce(function (a, d) {
        return a + (data.fluxo[o][d] || 0);
      }, 0);
      totOrigem[o] = t;
      soma += t;
    });
    var scale = (H - padT - padB - gap * (origens.length - 1)) / soma;

    var yO = {};
    var cursor = padT;
    origens.forEach(function (o) {
      yO[o] = { y0: cursor, y1: cursor + totOrigem[o] * scale, cur: cursor };
      cursor = yO[o].y1 + gap;
    });

    var totDestino = {};
    DESTINOS.forEach(function (d) {
      totDestino[d] = origens.reduce(function (a, o) {
        return a + (data.fluxo[o][d] || 0);
      }, 0);
    });
    var yD = {};
    cursor = padT;
    var gapD = (H - padT - padB - soma * scale) / (DESTINOS.length - 1);
    DESTINOS.forEach(function (d) {
      yD[d] = { y0: cursor, y1: cursor + totDestino[d] * scale, cur: cursor };
      cursor = yD[d].y1 + gapD;
    });

    var parts = [
      '<defs><pattern id="hatch" width="7" height="7" patternTransform="rotate(45)" patternUnits="userSpaceOnUse">' +
        '<rect width="7" height="7" fill="rgba(244,242,234,.02)"/>' +
        '<line x1="0" y1="0" x2="0" y2="7" stroke="rgba(244,242,234,.35)" stroke-width="2.4"/></pattern></defs>'
    ];

    origens.forEach(function (o) {
      DESTINOS.forEach(function (d) {
        var v = data.fluxo[o][d] || 0;
        if (v < 0.02) return;
        var h = v * scale;
        var a0 = yO[o].cur;
        var b0 = yD[d].cur;
        yO[o].cur += h;
        yD[d].cur += h;
        var cx = (xL + barW + xR) / 2;
        var path =
          "M" + (xL + barW) + "," + a0 +
          " C" + cx + "," + a0 + " " + cx + "," + b0 + " " + xR + "," + b0 +
          " L" + xR + "," + (b0 + h) +
          " C" + cx + "," + (b0 + h) + " " + cx + "," + (a0 + h) + " " + (xL + barW) + "," + (a0 + h) + " Z";
        parts.push('<path class="flow" d="' + path + '" fill="' + COLOR[d] + '"/>');
        parts.push('<path class="flow-hatch" d="' + path + '" fill="url(#hatch)"/>');
      });
    });

    origens.forEach(function (o) {
      var b = yO[o];
      parts.push(
        '<rect x="' + xL + '" y="' + b.y0 + '" width="' + barW + '" height="' + Math.max(b.y1 - b.y0, 1.5) +
          '" fill="' + (ORIGEM_COR[o] || "#8a8578") + '" rx="2"/>'
      );
      var label = o.replace(/ \(.*\)/, "");
      var valor = data.primeiro_turno[o];
      var small = b.y1 - b.y0 < 14;
      parts.push(
        '<text class="sk-label' + (small ? " sk-small" : "") + '" x="' + (xL - 12) +
          '" y="' + ((b.y0 + b.y1) / 2 + (small ? 3 : 4)) + '" text-anchor="end">' +
          label + ' <tspan class="sk-num' + (small ? " sk-small" : "") + '">' + valor + "</tspan></text>"
      );
    });

    DESTINOS.forEach(function (d) {
      var b = yD[d];
      parts.push(
        '<rect x="' + xR + '" y="' + b.y0 + '" width="' + barW + '" height="' + Math.max(b.y1 - b.y0, 1.5) +
          '" fill="' + COLOR[d] + '" rx="2"/>'
      );
      var key = { Lula: "lula", "Flávio": "flavio", "Branco/nulo": "branco_nulo", "Não sabe": "nao_sabe" }[d];
      parts.push(
        '<text class="sk-label" x="' + (xR + barW + 12) + '" y="' + ((b.y0 + b.y1) / 2 + 4) + '">' +
          d + ' <tspan class="sk-num">' + data.segundo_turno[key] + "</tspan></text>"
      );
    });

    parts.push('<text class="sk-head" x="' + xL + '" y="20" text-anchor="end">1º TURNO</text>');
    parts.push('<text class="sk-head" x="' + (xR + barW) + '" y="20">2º TURNO · LULA × FLÁVIO</text>');

    host.querySelector("svg").innerHTML = parts.join("");
  })();

  /* ---------- explorador dos 139 municípios ---------- */
  var host = document.getElementById("explorador");
  if (!host) return;

  var plot = host.querySelector(".plot");
  var tip = host.querySelector(".plot-tip");
  var tbody = host.querySelector(".city-table tbody");
  var search = host.querySelector("input[type='search']");
  var filterButtons = Array.prototype.slice.call(host.querySelectorAll(".filters button"));
  var stats = host.querySelector(".explorer-stats");

  var REGION_COLOR = {
    SUDESTE: "#45c9c2",
    NORDESTE: "#e0483a",
    SUL: "#3f8fd6",
    "CENTRO OESTE": "#cfe63c",
    NORTE: "#f0a930"
  };

  var cities = [];
  var state = { region: "todas", query: "", sort: "entrevistas", dir: -1 };

  function fmt(n) {
    return n === null || n === undefined ? "—" : n.toLocaleString("pt-BR");
  }

  function pct(value, digits) {
    return value.toLocaleString("pt-BR", {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits
    });
  }

  function passes(city) {
    if (state.region !== "todas" && city.regiao !== state.region) return false;
    if (!state.query) return true;
    var q = state.query
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "")
      .toUpperCase();
    return (city.municipio + " " + city.uf).indexOf(q) >= 0;
  }

  function draw() {
    if (!plot) return;
    var W = 1000;
    var H = 500;
    var pad = { l: 54, r: 34, t: 36, b: 40 };
    var xs = function (v) {
      return pad.l + ((v - 10) / 70) * (W - pad.l - pad.r);
    };
    var ymin = Math.log10(2500);
    var ymax = Math.log10(16000000);
    var ys = function (v) {
      var t = (Math.log10(Math.max(v || 3000, 3000)) - ymin) / (ymax - ymin);
      return H - pad.b - t * (H - pad.t - pad.b);
    };

    var parts = [];
    parts.push('<g class="axis">');
    [20, 30, 40, 50, 60, 70].forEach(function (v) {
      parts.push(
        '<line class="' +
          (v === 50 ? "midline" : "gridline") +
          '" x1="' +
          xs(v) +
          '" x2="' +
          xs(v) +
          '" y1="' +
          pad.t +
          '" y2="' +
          (H - pad.b) +
          '"/>'
      );
      parts.push(
        '<text x="' + xs(v) + '" y="' + (H - pad.b + 18) + '" text-anchor="middle">' + v + "%</text>"
      );
    });
    [10000, 100000, 1000000].forEach(function (v) {
      parts.push(
        '<line class="gridline" x1="' +
          pad.l +
          '" x2="' +
          (W - pad.r) +
          '" y1="' +
          ys(v) +
          '" y2="' +
          ys(v) +
          '"/>'
      );
      parts.push(
        '<text x="' +
          (pad.l - 8) +
          '" y="' +
          (ys(v) + 4) +
          '" text-anchor="end">' +
          (v >= 1000000 ? "1 mi" : v / 1000 + " mil") +
          "</text>"
      );
    });
    parts.push(
      '<text x="' +
        (W - pad.r) +
        '" y="' +
        (H - pad.b + 33) +
        '" text-anchor="end">voto em Bolsonaro no 2º turno de 2022 →</text>'
    );
    parts.push("</g>");

    cities
      .slice()
      .sort(function (a, b) {
        return (b.eleitores || 0) - (a.eleitores || 0);
      })
      .forEach(function (city, index) {
        if (city.bolsonaro_2022_pct === null) return;
        var r = 4 + Math.sqrt(city.entrevistas) * 1.9;
        parts.push(
          '<circle class="dot' +
            (passes(city) ? "" : " dim") +
            '" data-i="' +
            index +
            '" cx="' +
            xs(city.bolsonaro_2022_pct).toFixed(1) +
            '" cy="' +
            ys(city.eleitores).toFixed(1) +
            '" r="' +
            r.toFixed(1) +
            '" fill="' +
            (REGION_COLOR[city.regiao] || "#9a9789") +
            '" fill-opacity="' +
            (city.ondas === 3 ? 0.72 : 0.3) +
            '" stroke="' +
            (REGION_COLOR[city.regiao] || "#9a9789") +
            '" stroke-opacity="0.9"><title>' +
            city.municipio +
            "/" +
            city.uf +
            "</title></circle>"
        );
      });

    plot.querySelector("svg").innerHTML = parts.join("");
    plot.querySelectorAll(".dot").forEach(function (dot) {
      dot.addEventListener("mouseenter", function (event) {
        var sorted = cities.slice().sort(function (a, b) {
          return (b.eleitores || 0) - (a.eleitores || 0);
        });
        var city = sorted[Number(dot.dataset.i)];
        if (!city || !tip) return;
        var box = plot.getBoundingClientRect();
        var point = event.target.getBoundingClientRect();
        tip.innerHTML =
          "<b>" +
          city.municipio +
          "/" +
          city.uf +
          "</b>" +
          city.entrevistas +
          " entrevistas · " +
          fmt(city.eleitores) +
          " eleitores<br>Bolsonaro 2022: " +
          pct(city.bolsonaro_2022_pct, 1) +
          "% · " +
          city.ondas +
          " de 3 ondas";
        tip.style.left = point.left - box.left + point.width / 2 + "px";
        tip.style.top = point.top - box.top + "px";
        tip.classList.add("on");
      });
      dot.addEventListener("mouseleave", function () {
        if (tip) tip.classList.remove("on");
      });
    });
  }

  function renderTable() {
    if (!tbody) return;
    var rows = cities.filter(passes);
    var key = state.sort;
    rows.sort(function (a, b) {
      var va = a[key];
      var vb = b[key];
      if (typeof va === "string") return va.localeCompare(vb) * state.dir;
      return ((va || 0) - (vb || 0)) * state.dir;
    });
    tbody.innerHTML = rows
      .map(function (city) {
        return (
          "<tr><td>" +
          city.municipio +
          "<span class='pill" +
          (city.ondas === 3 ? " fix" : "") +
          "' style='margin-left:8px'>" +
          city.ondas +
          "/3</span></td><td>" +
          city.uf +
          "</td><td class='num'>" +
          city.entrevistas +
          "</td><td class='num'>" +
          fmt(city.eleitores) +
          "</td><td class='num'>" +
          (city.bolsonaro_2022_pct === null ? "—" : pct(city.bolsonaro_2022_pct, 1) + "%") +
          "</td></tr>"
        );
      })
      .join("");

    if (stats) {
      var interviews = rows.reduce(function (acc, c) {
        return acc + c.entrevistas;
      }, 0);
      var voters = rows.reduce(function (acc, c) {
        return acc + (c.eleitores || 0);
      }, 0);
      var weighted = rows.reduce(function (acc, c) {
        return acc + c.entrevistas * (c.bolsonaro_2022_pct || 0);
      }, 0);
      var fixed = rows.filter(function (c) {
        return c.ondas === 3;
      }).length;
      stats.innerHTML =
        "<div><b>" +
        rows.length +
        "</b><span>municípios no filtro</span></div>" +
        "<div><b>" +
        fmt(interviews) +
        "</b><span>entrevistas · " +
        pct((interviews / 2004) * 100, 1) +
        "% da amostra</span></div>" +
        "<div><b>" +
        fixed +
        "</b><span>presentes nas três ondas</span></div>" +
        "<div><b>" +
        fmt(voters) +
        "</b><span>eleitores cobertos</span></div>" +
        "<div><b>" +
        (interviews ? pct(weighted / interviews, 2) : "0") +
        "%</b><span>Bolsonaro 2022, ponderado por entrevista</span></div>";
    }
  }

  function update() {
    draw();
    renderTable();
  }

  filterButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      filterButtons.forEach(function (b) {
        b.classList.remove("on");
      });
      button.classList.add("on");
      state.region = button.dataset.region;
      update();
    });
  });

  if (search) {
    search.addEventListener("input", function () {
      state.query = search.value.trim();
      update();
    });
  }

  host.querySelectorAll(".city-table thead th").forEach(function (th) {
    th.addEventListener("click", function () {
      var key = th.dataset.key;
      if (!key) return;
      state.dir = state.sort === key ? -state.dir : -1;
      state.sort = key;
      host.querySelectorAll(".city-table thead th").forEach(function (other) {
        other.classList.remove("asc", "desc");
      });
      th.classList.add(state.dir === 1 ? "asc" : "desc");
      renderTable();
    });
  });

  function load() {
    // O dossiê precisa abrir também em file://, onde fetch() de arquivo local
    // é bloqueado. Por isso os municípios chegam por script clássico, com o
    // JSON servido apenas como alternativa.
    if (Array.isArray(window.__DATAFOLHA_MUNICIPIOS__)) {
      cities = window.__DATAFOLHA_MUNICIPIOS__;
      update();
      return;
    }
    fetch("assets/datafolha_072026_municipios.json")
      .then(function (response) {
        return response.json();
      })
      .then(function (data) {
        cities = data;
        update();
      })
      .catch(function () {
        var note = host.querySelector(".explorer-stats");
        if (note) {
          note.innerHTML =
            "<div><b>—</b><span>dados dos municípios indisponíveis; veja assets/datafolha_072026_municipios.json</span></div>";
        }
      });
  }

  load();
})();
