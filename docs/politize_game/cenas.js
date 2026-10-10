/* Politize: fundos de cena em SVG (16:9, viewBox 0 0 640 360). Sem dependencias. */
(function (w) {
  "use strict";

  function hx(c, d) {
    return typeof c === "string" && /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.test(c) ? c.toLowerCase() : d;
  }
  function rgb(c) {
    c = c.slice(1);
    if (c.length === 3) c = c.replace(/./g, "$&$&");
    return [0, 2, 4].map(function (i) { return parseInt(c.substr(i, 2), 16); });
  }
  function mix(a, b, t) {
    var x = rgb(a), y = rgb(b);
    return "#" + [0, 1, 2].map(function (i) {
      var v = Math.round(x[i] + (y[i] - x[i]) * t);
      return (v < 16 ? "0" : "") + v.toString(16);
    }).join("");
  }
  function dk(c, t) { return mix(c, "#000000", t); }
  function lt(c, t) { return mix(c, "#ffffff", t); }
  function lum(c) { var v = rgb(c); return (0.299 * v[0] + 0.587 * v[1] + 0.114 * v[2]) / 255; }
  function norm(s) {
    s = String(s == null ? "" : s).toLowerCase();
    if (s.normalize) s = s.normalize("NFD").replace(/[̀-ͯ]/g, "");
    return s.replace(/[^a-z_]/g, "");
  }
  function P(d, f, x) { return '<path d="' + d + '" fill="' + f + '"' + (x || "") + "/>"; }
  function S(d, s, wd, x) {
    return '<path d="' + d + '" fill="none" stroke="' + s + '" stroke-width="' + wd + '" stroke-linecap="round" stroke-linejoin="round"' + (x || "") + "/>";
  }
  function C(cx, cy, r, f, x) { return '<circle cx="' + cx + '" cy="' + cy + '" r="' + r + '" fill="' + f + '"' + (x || "") + "/>"; }
  function E(cx, cy, rx, ry, f, x) { return '<ellipse cx="' + cx + '" cy="' + cy + '" rx="' + rx + '" ry="' + ry + '" fill="' + f + '"' + (x || "") + "/>"; }
  function R(x, y, wd, h, r, f, xx) { return '<rect x="' + x + '" y="' + y + '" width="' + wd + '" height="' + h + '" rx="' + r + '" fill="' + f + '"' + (xx || "") + "/>"; }
  var OP = function (v) { return ' opacity="' + v + '"'; };

  var HORIZ = 250; // linha do chao
  // mesinha redonda: tampo em y -62
  function mesinha(k) { return R(-4, -60, 8, 60, 2, dk(k.p, 0.35)) + E(0, 0, 22, 5, dk(k.p, 0.35)) + E(0, -62, 38, 8, dk(k.a, 0.15)) + E(0, -64, 38, 8, k.a); }

  // props posicionaveis: desenhados com a base em (0,0); k = cores {c ceu, p chao, a destaque}
  var PROPS = {
    pao: function (k) {
      return R(-46, -50, 92, 50, 4, dk(k.a, 0.3)) + R(-50, -56, 100, 8, 3, dk(k.a, 0.45)) +
        P("M-38 -56L38 -56L32 -78L-32 -78Z", "#b07a3f") + E(-18, -82, 18, 9, "#d99a4e") + E(16, -82, 18, 9, "#c98940") +
        E(0, -90, 16, 8, "#e0a95e") + S("M-24 -84L-20 -79M-14 -84L-10 -79M10 -84L14 -79M20 -84L24 -79", "#9a6328", 2);
    },
    vitrine: function (k) {
      return R(-64, -96, 128, 96, 6, dk(k.a, 0.25)) + R(-56, -88, 112, 60, 3, lt(k.c, 0.6), OP(0.85)) +
        S("M-56 -58L56 -58", dk(k.a, 0.25), 3) + C(-36, -66, 7, "#d99a4e") + C(-18, -66, 7, "#e7b8c4") + C(0, -66, 7, "#c97b3c") +
        C(20, -66, 7, "#f2d38a") + C(-30, -36, 7, "#e7b8c4") + C(-8, -36, 7, "#d99a4e") + C(14, -36, 7, "#f2d38a") +
        P("M-50 -86L-30 -86L-56 -40Z", "#ffffff", OP(0.35));
    },
    cafe: function (k) {
      return mesinha(k) + E(0, -74, 18, 4, "#f4f1ea") + P("M-11 -96L11 -96L9 -76L-9 -76Z", "#f4f1ea") +
        S("M11 -92C19 -92 19 -82 10 -82", "#f4f1ea", 3) + E(0, -96, 11, 3, "#5a3420") +
        S("M-4 -104C-8 -110 0 -114 -4 -120M5 -104C1 -110 9 -114 5 -120", "#ffffff", 2.4, OP(0.75));
    },
    cerveja: function (k) {
      return mesinha(k) + R(-20, -112, 16, 44, 3, "#2f7a3e") + R(-16, -128, 8, 18, 2, "#2f7a3e") + R(-18, -96, 12, 14, 1, "#efe2b0") +
        P("M4 -106L26 -106L23 -68L7 -68Z", "#e9a11b") + R(3, -112, 24, 8, 4, "#fbf6e6") + S("M10 -98L10 -76", "#ffffff", 2, OP(0.5));
    },
    mesa: function (k) {
      return R(-70, -64, 6, 64, 2, dk(k.p, 0.4)) + R(64, -64, 6, 64, 2, dk(k.p, 0.4)) + R(-80, -72, 160, 12, 3, dk(k.a, 0.2)) +
        P("M-80 -66L80 -66L72 -40L-72 -40Z", k.a) + S("M-60 -66L-56 -42M-20 -66L-18 -42M20 -66L18 -42M60 -66L56 -42", lt(k.a, 0.35), 3);
    },
    guarda_sol: function (k) {
      var o = S("M0 0L0 -176", "#e8e2d0", 4), xs = [-84, -42, 0, 42, 84];
      for (var i = 0; i < 4; i++) {
        o += P("M0 -184L" + xs[i] + " -140Q" + (xs[i] + 21) + " -128 " + xs[i + 1] + " -140Z", i % 2 ? "#ffffff" : k.a);
      }
      return o + C(0, -186, 4, dk(k.a, 0.3)) + E(0, 2, 40, 6, "#000000", OP(0.12));
    },
    carrinho: function (k) {
      return P("M-50 -80L50 -80L40 -30L-40 -30Z", "none", ' stroke="' + dk(k.a, 0.2) + '" stroke-width="4"') +
        S("M-30 -80L-26 -30M-10 -80L-9 -30M10 -80L9 -30M30 -80L26 -30M-46 -62L46 -62M-43 -46L43 -46", dk(k.a, 0.2), 2.4) +
        S("M50 -80L66 -100L80 -100M-40 -30L-44 -14L44 -14", dk(k.a, 0.2), 4) + R(-36, -100, 26, 22, 2, "#e46a2e") + R(-6, -96, 18, 18, 2, "#f2c230") +
        C(-34, -6, 6, "#2a2d33") + C(34, -6, 6, "#2a2d33");
    },
    gondola: function (k) {
      var o = R(-70, -170, 140, 170, 4, dk(k.a, 0.15)) + R(-62, -162, 124, 156, 2, lt(k.c, 0.25));
      var cs = [k.a, "#e46a2e", "#f2c230", lt(k.a, 0.45), "#3f8f5a", "#c8412f"];
      for (var i = 0; i < 4; i++) {
        var y = -150 + i * 38;
        o += R(-62, y + 30, 124, 6, 1, dk(k.a, 0.3));
        for (var j = 0; j < 6; j++) o += R(-58 + j * 20, y + (j % 2 ? 6 : 2), 16, j % 2 ? 24 : 28, 2, cs[(i + j) % 6]);
      }
      return o;
    },
    esteira: function (k) {
      return P("M-80 -6L70 -22L74 -10L-76 6Z", "#2a2d33") + P("M-74 -8L64 -22L66 -18L-72 -4Z", "#4a4f57") +
        S("M56 -20L64 -110", k.eq, 7) + R(46, -126, 40, 18, 4, k.eq) + R(52, -122, 24, 10, 2, k.a);
    },
    halter: function (k) {
      var o = R(-66, -70, 6, 70, 2, k.eq) + R(60, -70, 6, 70, 2, k.eq) + R(-70, -74, 140, 6, 2, k.eq) + R(-70, -38, 140, 6, 2, k.eq);
      for (var i = 0; i < 3; i++) {
        var x = -46 + i * 46;
        o += R(x - 14, -86, 28, 4, 2, "#8a8f98") + R(x - 18, -94, 9, 20, 3, "#1f2226") + R(x + 9, -94, 9, 20, 3, "#1f2226");
        o += R(x - 14, -50, 28, 4, 2, "#8a8f98") + R(x - 18, -58, 9, 20, 3, k.a) + R(x + 9, -58, 9, 20, 3, k.a);
      }
      return o;
    },
    caixa: function (k) {
      return R(-70, -70, 140, 70, 4, dk(k.a, 0.2)) + R(-74, -76, 148, 10, 3, dk(k.a, 0.4)) +
        R(-20, -112, 52, 36, 4, "#2a2d33") + R(-14, -106, 40, 18, 2, "#8fd3a8") + R(-60, -60, 40, 6, 2, lt(k.a, 0.3)) +
        R(-30, -86, 10, 10, 2, "#c8c8c8");
    },
    celular: function (k) {
      return R(-50, -200, 100, 190, 14, "#1c1f24") + R(-42, -186, 84, 162, 6, lt(k.c, 0.75)) +
        R(-36, -176, 50, 18, 8, "#ffffff") + R(-14, -150, 50, 18, 8, k.a) + R(-36, -124, 58, 18, 8, "#ffffff") +
        R(-4, -98, 40, 18, 8, k.a) + R(-36, -72, 44, 18, 8, "#ffffff") + R(-12, -194, 24, 4, 2, "#3a3d42");
    },
    teclado: function (k) {
      var o = R(-80, -60, 160, 10, 2, dk(k.p, 0.35)) + R(-72, -50, 6, 50, 2, dk(k.p, 0.45)) + R(66, -50, 6, 50, 2, dk(k.p, 0.45)) +
        R(-60, -72, 96, 14, 3, "#1f2226");
      for (var i = 0; i < 9; i++) o += R(-56 + i * 10, -70, 7, 4, 1, i % 3 ? k.a : lt(k.a, 0.5)) + R(-56 + i * 10, -64, 7, 4, 1, i % 2 ? lt(k.a, 0.3) : k.a);
      return o + E(54, -64, 8, 6, "#1f2226");
    },
    monitor: function (k) {
      return R(-8, -40, 16, 40, 2, "#2a2d33") + R(-30, -6, 60, 6, 3, "#2a2d33") + R(-70, -120, 140, 84, 6, "#1c1f24") +
        R(-62, -112, 124, 68, 3, dk(k.a, 0.35)) + P("M-62 -60L-30 -84L-6 -68L24 -96L62 -70L62 -44L-62 -44Z", k.a, OP(0.85)) +
        C(36, -98, 6, lt(k.a, 0.6));
    },
    banco_igreja: function (k) {
      var b = dk(k.a, 0.35);
      return R(-90, -96, 180, 12, 3, b) + R(-90, -84, 180, 34, 2, dk(k.a, 0.2)) + R(-96, -54, 192, 12, 3, b) +
        R(-86, -42, 8, 42, 2, b) + R(78, -42, 8, 42, 2, b) + R(-96, -104, 10, 104, 3, b) + R(86, -104, 10, 104, 3, b);
    },
    porta: function (k) {
      return P("M-46 0L-46 -150Q0 -200 46 -150L46 0Z", dk(k.a, 0.3)) + P("M-38 0L-38 -146Q0 -188 38 -146L38 0Z", dk(k.a, 0.1)) +
        S("M0 -178L0 0", dk(k.a, 0.35), 3) + C(-8, -70, 3.5, "#d9a71c") + C(8, -70, 3.5, "#d9a71c");
    },
    churrasqueira: function (k) {
      return S("M-40 0L-30 -50M40 0L30 -50", "#2a2d33", 5) + P("M-56 -96L56 -96L48 -50L-48 -50Z", "#2a2d33") +
        R(-60, -102, 120, 8, 3, "#4a4f57") + S("M-50 -104L50 -104", "#8a8f98", 2) + E(-24, -108, 14, 5, "#8b3a22") + E(12, -108, 16, 5, "#a3502d") +
        P("M-34 -90L-20 -90L-27 -70Z", "#f2a33a", OP(0.8)) + P("M10 -90L26 -90L18 -66Z", "#e9572b", OP(0.8)) +
        S("M-10 -118C-18 -130 -2 -138 -10 -152M14 -118C6 -130 22 -138 14 -152", "#ffffff", 4, OP(0.45));
    },
    espeto: function () {
      var o = R(-34, -30, 68, 30, 4, "#5a3a22");
      for (var i = 0; i < 3; i++) {
        var x = -20 + i * 20;
        o += S("M" + x + " -24L" + x + " -140", "#b8b8b8", 3) + R(x - 9, -132, 18, 16, 6, "#8b3a22") + R(x - 8, -112, 16, 9, 3, "#9ac36b") +
          R(x - 9, -100, 18, 16, 6, "#a3502d") + R(x - 9, -80, 18, 14, 6, "#7a2f1a");
      }
      return o;
    },
    sacola: function (k) {
      return S("M-46 -60Q-34 -86 -22 -60", dk(k.a, 0.3), 3) + P("M-56 -60L-12 -60L-16 0L-52 0Z", k.a) +
        S("M2 -50Q16 -76 30 -50", "#7a5530", 3) + P("M-6 -50L40 -50L44 0L-10 0Z", "#d8c3a0") + R(4, -36, 26, 10, 2, "#c8412f", OP(0.8));
    },
    escada_rolante: function (k) {
      var o = P("M-90 0L-60 0L70 -150L100 -150L100 -120L-40 30L-90 30Z", dk(k.a, 0.25)) +
        S("M-78 -26L82 -190", "#2a2d33", 7) + S("M-78 -26L-92 -26M82 -190L104 -190", "#2a2d33", 7);
      for (var i = 0; i < 7; i++) o += S("M" + (-54 + i * 18) + " " + (-6 - i * 20.5) + "l18 0", lt(k.a, 0.5), 2.4);
      return o;
    },
    vitrine_loja: function (k) {
      return R(-74, -170, 148, 170, 4, dk(k.a, 0.3)) + R(-66, -150, 132, 140, 2, lt(k.c, 0.55)) +
        P("M-78 -186L78 -186L74 -164L-74 -164Z", k.a) + S("M-58 -186L-56 -164M-30 -186L-28 -164M0 -186L0 -164M30 -186L28 -164M58 -186L56 -164", "#ffffff", 6, OP(0.6)) +
        C(-24, -120, 10, "#e8e2d0") + P("M-40 -106L-8 -106L-4 -40L-44 -40Z", "#c8412f") + C(26, -118, 10, "#e8e2d0") +
        P("M10 -104L42 -104L46 -60L6 -60Z", "#1f5f9e") + P("M-60 -148L-34 -148L-62 -90Z", "#ffffff", OP(0.4));
    },
    cadeira: function (k) {
      return S("M-24 0L-20 -48M24 0L20 -48M20 -48L24 -110", dk(k.a, 0.3), 5) + R(-28, -54, 52, 10, 3, k.a) + R(14, -116, 14, 50, 4, k.a);
    },
    logo_x: function (k) {
      var f = k.escuro ? "#f7f5ee" : "#151812", t = k.escuro ? "#151812" : "#ffffff";
      return R(-56, -116, 112, 112, 26, f) + S("M-26 -86L26 -34M26 -86L-26 -34", t, 12) + S("M-26 -86L26 -34", k.a, 4);
    }
  };
  // props que pertencem a parede (base na linha do chao)
  var PAREDE = { vitrine_loja: 1, porta: 1, celular: 1, monitor: 0, logo_x: 1, escada_rolante: 1 };
  var SLOTS = [[100, 1.15], [540, 1.15], [196, 0.85], [446, 0.85], [30, 0.95], [610, 0.95]];

  function svg(cenario) {
    var amb = (cenario && cenario.ambiente) || {};
    var pal = amb.paleta || [];
    var k = { c: hx(pal[0], "#dfe8ef"), p: hx(pal[1], "#c9b28f"), a: hx(pal[2], "#1f5f9e") };
    k.eq = lum(k.c) < 0.3 ? "#8a8f98" : "#3a3d42";
    k.escuro = lum(k.c) < 0.3;
    var lista = (amb.props || []).map(norm);
    var tem = function (n) { return lista.indexOf(n) >= 0; };
    var o = [];

    // ceu ou parede, com faixa suave no alto
    o.push(R(0, 0, 640, 360, 0, k.c) + R(0, 0, 640, 70, 0, lt(k.c, 0.12)) + R(0, 70, 640, 8, 0, lt(k.c, 0.06)));
    // rodape de parede (so em interiores)
    if (!tem("onda") && !tem("carro") && !tem("palco")) o.push(R(0, 178, 640, 72, 0, dk(k.c, 0.06)) + R(0, 176, 640, 4, 0, lt(k.c, 0.2)));
    if (tem("onda")) {
      var mar = tem("areia") ? mix(k.p, "#1a6fa0", 0.35) : mix(k.c, "#1a6fa0", 0.6);
      o.push(R(0, 196, 640, 60, 0, mar) + S("M0 212Q40 204 80 212T160 212T240 212T320 212T400 212T480 212T560 212T640 212", lt(mar, 0.5), 3) +
        S("M0 236Q40 228 80 236T160 236T240 236T320 236T400 236T480 236T560 236T640 236", lt(mar, 0.7), 3) + C(560, 70, 26, "#f6d96b"));
    }
    if (tem("fila")) {
      var sl = mix(k.c, "#000000", 0.18);
      for (var f = 0; f < 9; f++) {
        var fx = 30 + f * 72, fh = 52 + (f * 37) % 20;
        o.push(C(fx, HORIZ - fh - 14, 11, sl) + P("M" + (fx - 18) + " " + HORIZ + "Q" + (fx - 18) + " " + (HORIZ - fh) + " " + fx + " " + (HORIZ - fh) +
          "Q" + (fx + 18) + " " + (HORIZ - fh) + " " + (fx + 18) + " " + HORIZ + "Z", sl));
      }
    }
    if (tem("carro")) {
      // janelas do carro
      var luzes = "";
      for (var q = 0; q < 14; q++) luzes += C(110 + (q * 151) % 420, 120 + (q * 37) % 60, 3 + (q % 3), q % 2 ? k.a : "#f6d96b", OP(0.7));
      o.push(luzes + P("M0 0L640 0L640 40L560 40L520 190L120 190L80 40L0 40Z", "#1f2226", OP(0.92)) + R(316, 40, 8, 150, 2, "#1f2226"));
    }
    // chao
    if (tem("areia")) k.p = mix(k.p, "#e8cf95", 0.8);
    if (!tem("carro")) o.push(R(0, HORIZ, 640, 110, 0, k.p) + R(0, HORIZ, 640, 5, 0, dk(k.p, 0.18)));
    if (tem("areia")) {
      var dots = "";
      for (var d = 0; d < 40; d++) dots += C((d * 97) % 640, 262 + (d * 53) % 92, 1.8, dk(k.p, 0.22));
      o.push(dots + S("M0 256Q160 248 320 256T640 256", lt(k.p, 0.4), 4));
    }
    if (tem("palco")) {
      o.push(R(0, 296, 640, 64, 0, dk(k.p, 0.35)) + R(0, 292, 640, 8, 0, k.a) + R(0, 0, 640, 26, 0, "#1f2226"));
      for (var s = 0; s < 6; s++) o.push(C(60 + s * 104, 20, 8, s % 2 ? k.a : "#f6d96b"));
    }
    if (tem("bolha")) {
      o.push(R(160, 34, 100, 48, 18, "#ffffff", OP(0.92)) + P("M180 80L174 98L198 80Z", "#ffffff", OP(0.92)) + C(190, 58, 6, k.a) + C(210, 58, 6, k.a) + C(230, 58, 6, k.a) +
        R(490, 70, 120, 46, 16, k.a) + P("M590 114L600 132L576 114Z", k.a) + R(508, 84, 70, 6, 3, "#ffffff", OP(0.8)) + R(508, 98, 46, 6, 3, "#ffffff", OP(0.8)));
    }

    // props posicionaveis, na ordem em que vieram
    var n = 0;
    lista.forEach(function (nm) {
      if (!PROPS[nm] || n >= SLOTS.length) return;
      var sl = SLOTS[n++];
      var y = PAREDE[nm] ? HORIZ + 4 : 316, sc = sl[1];
      if (tem("carro")) { y = 300; sc *= 0.6; }
      o.push('<g transform="translate(' + sl[0] + " " + y + ") scale(" + sc + ')">' + PROPS[nm](k) + "</g>");
    });

    // frente: painel do carro, retrovisor e feixes de luz
    if (tem("carro")) {
      o.push(P("M0 300Q320 270 640 300L640 360L0 360Z", "#2a2d33") + S("M40 360a70 70 0 0 1 140 0", "#151812", 12) +
        R(280, 300, 80, 12, 4, k.a, OP(0.7)));
    }
    if (tem("retrovisor")) o.push(R(318, 0, 4, 22, 1, "#151812") + R(270, 18, 100, 28, 10, "#151812") + R(276, 23, 88, 18, 7, lt(k.c, 0.35)));
    if (tem("luz")) {
      o.push(P("M90 0L130 0L240 360L-40 360Z", "#ffffff", OP(0.13)) + P("M510 0L550 0L680 360L400 360Z", "#ffffff", OP(0.13)) +
        P("M300 0L340 0L420 360L220 360Z", k.a, OP(0.1)));
    }
    // vinheta leve nas bordas
    o.push(R(0, 0, 640, 360, 0, "none", ' stroke="#000000" stroke-opacity=".08" stroke-width="24"'));
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 360" preserveAspectRatio="xMidYMid slice" aria-hidden="true">' + o.join("") + "</svg>";
  }

  w.POLITIZE_CENAS = { svg: svg, PROPS: Object.keys(PROPS).concat(["areia", "onda", "luz", "palco", "fila", "bolha", "carro", "retrovisor"]) };
})(window);
