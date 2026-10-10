/* Politize: avatares em SVG (busto 1:1, viewBox 0 0 200 200). Sem dependencias. */
(function (w) {
  "use strict";

  // cores: valida hex e mistura
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
  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (m) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[m];
    });
  }
  function norm(s) {
    s = String(s == null ? "" : s).toLowerCase();
    if (s.normalize) s = s.normalize("NFD").replace(/[̀-ͯ]/g, "");
    return s.replace(/[^a-z_]/g, "");
  }

  // primitivas
  function P(d, f, x) { return '<path d="' + d + '" fill="' + esc(f) + '"' + (x || "") + "/>"; }
  function S(d, s, wd, x) {
    return '<path d="' + d + '" fill="none" stroke="' + esc(s) + '" stroke-width="' + wd +
      '" stroke-linecap="round" stroke-linejoin="round"' + (x || "") + "/>";
  }
  function C(cx, cy, r, f, x) { return '<circle cx="' + cx + '" cy="' + cy + '" r="' + r + '" fill="' + esc(f) + '"' + (x || "") + "/>"; }
  function E(cx, cy, rx, ry, f, x) {
    return '<ellipse cx="' + cx + '" cy="' + cy + '" rx="' + rx + '" ry="' + ry + '" fill="' + esc(f) + '"' + (x || "") + "/>";
  }
  function R(x, y, wd, h, r, f, xx) {
    return '<rect x="' + x + '" y="' + y + '" width="' + wd + '" height="' + h + '" rx="' + r + '" fill="' + esc(f) + '"' + (xx || "") + "/>";
  }

  var CABELOS = ["curto", "calvo", "coque", "franja", "longo", "rabo", "bone", "sem", "grisalho",
    "moicano", "colorido", "trancas", "careca_barba", "cabelo_branco"];
  var ACESS = ["oculos", "bone", "cordao", "headset", "biblia", "espeto", "celular", "coletinho",
    "chapeu", "fone", "cracha", "megafone", "caneca", "nenhum"];
  var ROUPAS = ["polo", "regata", "camisa", "camiseta", "vestido", "moletom", "social", "uniforme",
    "jaqueta", "colete"];
  var APELIDOS = { bibilia: "biblia", boneh: "bone", colete_puffer: "coletinho", headphone: "fone" };

  function pick(v, lista, d) {
    v = norm(v);
    v = APELIDOS[v] || v;
    return lista.indexOf(v) >= 0 ? v : d;
  }

  var SH = "M24 200C24 168 46 152 78 147L122 147C154 152 176 168 176 200Z";
  var CREW = "M24 200C24 168 46 152 78 147L86 147Q100 161 114 147L122 147C154 152 176 168 176 200Z";
  var VNECK = "M24 200C24 168 46 152 78 147L84 147L100 174L116 147L122 147C154 152 176 168 176 200Z";
  var DEEPV = "M24 200C24 168 46 152 78 147L84 147L100 192L116 147L122 147C154 152 176 168 176 200Z";

  // roupa: devolve [atras do pescoco, frente]
  function roupa(tipo, c, pele, v) {
    var d = dk(c, 0.22), back = "", o = "";
    if (tipo === "moletom") {
      back = P("M66 152C62 130 78 120 100 120C122 120 138 130 134 152Z", dk(c, 0.18));
      o = P(CREW, c) + S("M86 147Q100 161 114 147", d, 3) +
        S("M93 156L91 178", lt(c, 0.6), 2.2) + S("M107 156L109 178", lt(c, 0.6), 2.2) +
        S("M70 200C72 186 128 186 130 200", d, 2.5);
    } else if (tipo === "regata" || tipo === "vestido") {
      o = P(SH, pele) + S("M58 168C60 182 60 192 58 200M142 168C140 182 140 192 142 200", dk(pele, 0.15), 2);
      if (tipo === "regata") {
        o += P("M58 200L62 164C64 156 70 151 76 149L81 149Q100 174 119 149L124 149C130 151 136 156 138 164L142 200Z", c) +
          S("M81 149Q100 174 119 149", d, 2.5);
      } else {
        o += S("M78 150L82 168M122 150L118 168", c, 4) +
          P("M54 200C56 186 62 172 70 166Q100 182 130 166C138 172 144 186 146 200Z", c) +
          S("M70 166Q100 182 130 166", d, 2.5) + S("M66 190Q100 200 134 190", d, 1.6, ' opacity=".5"');
      }
    } else if (tipo === "social") {
      var g = v.gravata === false ? null : hx(v.gravata, "#8c2a2a");
      o = P(DEEPV, c) + P("M84 147L100 192L116 147Z", "#f4f2ec") +
        P("M84 146L95 158L92 164Z", "#ffffff") + P("M116 146L105 158L108 164Z", "#ffffff") +
        (g ? P("M96 157L104 157L106 163L100 190L94 163Z", g) + P("M96 152L104 152L104 158L96 158Z", dk(g, 0.15)) : "") +
        S("M84 147L100 192M116 147L100 192", dk(c, 0.35), 2.5) +
        S("M80 152L92 178M120 152L108 178", lt(c, 0.12), 2);
    } else if (tipo === "polo") {
      o = P(CREW, c) + R(96, 156, 8, 22, 2, d) + C(100, 164, 1.6, lt(c, 0.7)) + C(100, 172, 1.6, lt(c, 0.7)) +
        P("M80 144L99 156L90 166Z", lt(c, 0.15)) + P("M120 144L101 156L110 166Z", lt(c, 0.15)) +
        S("M80 144L99 156L90 166ZM120 144L101 156L110 166Z", d, 1.5);
    } else if (tipo === "camisa" || tipo === "colete") {
      var sc = tipo === "colete" ? "#f1efe8" : c;
      o = P(VNECK, sc) + P("M80 143L99 170L88 172L77 151Z", lt(sc, 0.18)) + P("M120 143L101 170L112 172L123 151Z", lt(sc, 0.18)) +
        S("M80 143L99 170L88 172L77 151ZM120 143L101 170L112 172L123 151Z", dk(sc, 0.25), 1.5) +
        C(100, 180, 1.8, dk(sc, 0.3)) + C(100, 191, 1.8, dk(sc, 0.3));
      if (tipo === "colete") {
        o += P("M30 200C30 172 46 158 70 151L94 182L94 200Z", c) + P("M170 200C170 172 154 158 130 151L106 182L106 200Z", c) +
          C(89, 190, 2, dk(c, 0.35)) + C(111, 190, 2, dk(c, 0.35));
      }
    } else if (tipo === "jaqueta") {
      o = P(SH, c) + P("M76 146Q100 158 124 146L128 138Q100 152 72 138Z", dk(c, 0.18)) +
        S("M100 154L100 200", dk(c, 0.4), 2.5) + S("M60 178L72 188M140 178L128 188", d, 2.5) +
        S("M48 162C46 176 46 188 48 200M152 162C154 176 154 188 152 200", d, 1.8);
    } else if (tipo === "uniforme") {
      o = P(CREW, c) + S("M86 147Q100 161 114 147", d, 3) + R(30, 176, 140, 8, 0, lt(c, 0.6)) +
        R(112, 160, 18, 12, 2, d) + R(70, 160, 16, 10, 2, lt(c, 0.3));
    } else {
      o = P(CREW, c) + S("M86 147Q100 161 114 147", d, 3);
    }
    o += S("M24 200C24 168 46 152 78 147M122 147C154 152 176 168 176 200", dk(tipo === "regata" || tipo === "vestido" ? pele : c, 0.28), 2.2);
    return [back, o];
  }

  // cabelo: devolve [atras da cabeca, frente]
  function cabelo(est, c, chapeu, fem) {
    var d = dk(c, 0.12), b = "", f = "";
    var CAP = "M62 90C58 52 78 40 100 40C124 40 142 52 138 90C136 78 130 68 122 64C112 70 90 70 78 64C70 68 64 78 62 90Z";
    var LADOS = "M62 98C60 86 62 76 67 70L72 73C69 81 69 90 70 100ZM138 98C140 86 138 76 133 70L128 73C131 81 131 90 130 100Z";
    var PARTE = "M62 100C58 54 78 38 100 38C122 38 142 54 138 100C134 76 122 60 104 54L100 62L96 54C78 60 66 76 62 100Z";
    if (est === "longo") {
      b = P("M60 90C56 48 78 34 100 34C122 34 144 48 140 90L148 162C130 172 70 172 52 162Z", d);
      f = PARTE;
    } else if (est === "trancas") {
      b = P("M62 90C58 50 78 36 100 36C122 36 142 50 138 90L140 112L60 112Z", d);
      for (var y = 106; y <= 170; y += 9) b += E(62, y, 7.5, 6, d) + E(138, y, 7.5, 6, d);
      b += C(62, 176, 4, "#e2b13c") + C(138, 176, 4, "#e2b13c");
      f = PARTE;
    } else if (est === "rabo") {
      b = P("M124 66C150 64 160 100 152 134C150 144 142 150 136 144C142 122 142 98 124 84Z", d);
      f = CAP;
    } else if (est === "coque") {
      b = chapeu ? "" : C(100, 36, 15, d) + R(92, 46, 16, 5, 2, dk(c, 0.35));
      f = "M62 90C58 52 78 42 100 42C122 42 142 52 138 90C130 66 116 58 100 58C84 58 70 66 62 90Z";
    } else if (est === "franja") {
      f = "M62 94C56 50 78 38 100 38C124 38 144 50 138 94C134 82 132 76 128 72L124 76L118 68L110 76L100 68L90 76L82 68L76 76L72 72C68 76 64 84 62 94Z";
    } else if (est === "colorido") {
      b = P("M58 92C54 48 78 34 100 34C122 34 146 48 142 92L144 132C134 138 126 134 124 126L76 126C74 134 66 138 56 132Z", d);
      f = "M62 100C56 50 78 38 100 38C124 38 144 50 138 100C134 84 130 76 126 72Q100 80 74 72C70 76 66 84 62 100Z";
      f = P(f, c) + S("M84 44C76 54 72 64 72 74", lt(c, 0.45), 5);
      return [b, chapeu ? P(LADOS, c) : f];
    } else if (est === "moicano") {
      f = P(LADOS, c, ' opacity=".45"') + P("M88 64L85 40L92 44L94 20L100 30L106 18L108 44L115 40L112 64Z", c);
      return [b, chapeu ? P(LADOS, c, ' opacity=".45"') : f];
    } else if (est === "cabelo_branco") {
      var wc = lum(c) > 0.7 ? c : "#ecebe6";
      f = C(70, 62, 12, wc) + C(82, 50, 14, wc) + C(100, 44, 15, wc) + C(118, 50, 14, wc) + C(130, 62, 12, wc) +
        P("M60 96C58 80 60 70 66 64L72 70C70 80 70 90 70 100ZM140 96C142 80 140 70 134 64L128 70C130 80 130 90 130 100Z", wc);
      return [b, chapeu ? P(LADOS, wc) : f];
    } else if (est === "grisalho") {
      var gc = mix(c, "#c9c9c4", 0.6);
      f = P(CAP, gc) + S("M66 84C66 76 70 70 74 66M134 84C134 76 130 70 126 66", "#f2f1ec", 3);
      return [b, chapeu ? P(LADOS, gc) : f];
    } else if (est === "calvo" || est === "bone") {
      f = LADOS;
    } else if (est === "sem" || est === "careca_barba") {
      return ["", ""];
    } else {
      f = fem ? "M60 102C54 52 78 38 100 38C124 38 146 52 140 102C136 84 132 72 124 66C112 72 88 72 76 66C68 72 64 84 60 102Z" : CAP;
    }
    return [b, P(chapeu ? LADOS : f, c)];
  }

  // rosto: sobrancelhas, olhos, nariz e boca por expressao
  function rosto(ex, pele, sob, fem) {
    var o = "", ol = "#1f1a17", nz = dk(pele, 0.28);
    var eyeRy = ex === "fechado" ? 3.6 : ex === "aberto" ? 5.6 : 5;
    o += E(86, 92, 4.4, eyeRy, ol) + E(114, 92, 4.4, eyeRy, ol);
    if (ex !== "fechado") o += C(87.6, 90, 1.4, "#ffffff") + C(115.6, 90, 1.4, "#ffffff");
    if (fem) o += S("M80 88L77 85M120 88L123 85", ol, 1.8);
    if (ex === "fechado") {
      o += S("M76 77L94 84M124 77L106 84", sob, 4.4);
    } else if (ex === "aberto") {
      o += S("M76 78Q85 68 95 75M105 75Q115 68 124 78", sob, 4);
    } else {
      o += S("M77 79Q86 75 95 79M105 79Q114 75 123 79", sob, 4);
    }
    o += S("M100 96Q96 106 101 107", nz, 2.2);
    var lb = fem ? "#b3473f" : dk(pele, 0.45);
    if (ex === "fechado") {
      o += S("M89 118Q100 111 111 118", lb, 3.4);
    } else if (ex === "aberto") {
      o += P("M86 112Q100 130 114 112Z", "#6b2420") + P("M88 112.6L112 112.6L110 116.5L90 116.5Z", "#ffffff") +
        S("M86 112Q100 130 114 112Z", lb, 2) +
        E(76, 108, 6.5, 3.6, "#e8796b", ' opacity=".4"') + E(124, 108, 6.5, 3.6, "#e8796b", ' opacity=".4"');
    } else {
      o += S("M91 115Q100 118 109 115", lb, 3.2);
    }
    return o;
  }

  function svg(visual, expressao) {
    var v = visual && typeof visual === "object" ? visual : {};
    var ex = ["fechado", "neutro", "aberto"].indexOf(expressao) >= 0 ? expressao : "neutro";
    var pele = hx(v.pele, "#d9a77c");
    var cab = hx(v.cabelo, "#3a2a20");
    var cor = hx(v.roupa, "#3f6f9a");
    var ca = hx(v.cor_acessorio, "");
    var est = pick(v.estilo_cabelo, CABELOS, "curto");
    var ac = pick(v.acessorio, ACESS, "nenhum");
    var tipo = pick(v.roupa_tipo, ROUPAS, "camiseta");
    var fem = norm(v.genero) === "f";
    var barba = v.barba === true || est === "careca_barba";
    if (est === "bone" && ac === "nenhum") ac = "bone";
    var chapeu = ac === "bone" || ac === "chapeu" || est === "bone";
    var pdk = dk(pele, 0.14);
    var sob = dk(cab, lum(cab) > 0.6 ? 0.35 : 0.2);
    var hair = cabelo(est, cab, chapeu, fem);
    var r = roupa(tipo, cor, pele, v);
    var o = [];

    // 1. fundo: cabelo de tras, capuz, fone no pescoco (parte de tras)
    o.push(hair[0], r[0]);
    if (ac === "fone") o.push(S("M78 142C80 128 120 128 122 142", "#23262b", 5));
    // 2. pescoco e roupa
    o.push(fem ? R(90, 108, 20, 52, 6, pdk) : R(87, 108, 26, 52, 6, pdk));
    o.push(r[1]);
    // 3. sobre a roupa
    if (ac === "coletinho") {
      var cv = ca || "#22304a", qd = dk(cv, 0.35);
      o.push(P("M26 200C26 170 46 154 74 148L90 160L94 200Z", cv) + P("M174 200C174 170 154 154 126 148L110 160L106 200Z", cv) +
        S("M36 170L90 170M30 184L92 184M60 158L88 158M110 170L164 170M108 184L170 184M112 158L140 158", qd, 2) +
        S("M90 160L94 200M110 160L106 200", dk(cv, 0.5), 2));
    } else if (ac === "cordao") {
      o.push(S("M84 150C86 178 114 178 116 150", ca || "#d9a71c", 3.2) + C(100, 178, 5.5, ca || "#d9a71c") + C(100, 178, 2.2, lt(ca || "#d9a71c", 0.5)));
    } else if (ac === "cracha") {
      var cc = ca || "#1f5f9e";
      o.push(S("M86 148L96 178M114 148L104 178", cc, 3) + R(89, 176, 22, 26, 3, "#ffffff", ' stroke="#9aa0a6" stroke-width="1.2"') +
        R(89, 176, 22, 7, 2, cc) + R(93, 186, 7, 8, 1, "#c9ccd1") + R(102, 187, 6, 2, 1, "#9aa0a6") + R(102, 191, 6, 2, 1, "#9aa0a6"));
    } else if (ac === "fone") {
      var fc = ca || "#e14b4b";
      o.push(E(78, 148, 10, 12, "#23262b") + E(122, 148, 10, 12, "#23262b") + E(78, 148, 5, 7, fc) + E(122, 148, 5, 7, fc));
    }
    // 4. cabeca
    o.push(E(64, 94, 7, 10, pdk) + E(136, 94, 7, 10, pdk));
    o.push(P(fem ? "M65 86C65 56 80 46 100 46C120 46 135 56 135 86C135 110 120 128 100 128C80 128 65 110 65 86Z"
      : "M63 86C63 55 80 45 100 45C120 45 137 55 137 86C137 112 124 131 100 131C76 131 63 112 63 86Z", pele));
    if (ac === "chapeu") o.push(E(100, 70, 38, 7, dk(pele, 0.2), ' opacity=".5"'));
    // 5. barba
    if (barba) {
      var bc = dk(cab, lum(cab) > 0.6 ? 0.1 : 0.25);
      o.push(P("M63 90C64 120 80 140 100 140C120 140 136 120 137 90L131 92C129 108 120 104 100 104C80 104 71 108 69 92Z", bc) +
        P("M86 108Q100 100 114 108L112 113Q100 108 88 113Z", bc));
    }
    // 6. rosto
    o.push(rosto(ex, pele, sob, fem));
    // 7. cabelo da frente
    o.push(hair[1]);
    // 8. cabeca: chapeus, oculos, headset
    if (ac === "bone") {
      var bn = ca || dk(cor, 0.1);
      o.push(P("M62 80C62 50 80 38 100 38C120 38 138 50 138 80Z", bn) +
        P("M56 80C70 70 130 70 144 80C148 87 140 91 132 88C112 82 88 82 68 88C60 91 52 87 56 80Z", dk(bn, 0.25)) +
        S("M100 40L100 76", dk(bn, 0.2), 1.6) + C(100, 39, 3, dk(bn, 0.25)) + R(88, 56, 24, 12, 3, lt(bn, 0.35)));
    } else if (ac === "chapeu") {
      var hc = ca || "#8a6a3d";
      o.push(E(100, 66, 72, 14, dk(hc, 0.15)) + E(100, 63, 70, 12, hc) +
        P("M70 64C70 40 82 26 92 30C96 33 104 33 108 30C118 26 130 40 130 64Z", hc) +
        P("M70 52L130 52L130 62Q100 68 70 62Z", dk(hc, 0.45)) + S("M100 32L100 44", dk(hc, 0.25), 2));
    }
    if (ac === "oculos") {
      var gl = "#1d1f22";
      o.push(C(86, 92, 10.5, "#ffffff", ' opacity=".2"') + C(114, 92, 10.5, "#ffffff", ' opacity=".2"') +
        S("M96.5 92a10.5 10.5 0 1 1 -21 0a10.5 10.5 0 1 1 21 0M124.5 92a10.5 10.5 0 1 1 -21 0a10.5 10.5 0 1 1 21 0M96 90Q100 86 104 90M75.5 90L65 87M124.5 90L135 87", gl, 3));
    }
    if (ac === "headset") {
      var hs = "#2a2d33", hl = ca || "#38d27a";
      o.push(S("M58 94C56 46 80 32 100 32C120 32 144 46 142 94", hs, 7) +
        R(52, 82, 15, 28, 7, hs) + R(133, 82, 15, 28, 7, hs) + R(55, 88, 4, 16, 2, hl) + R(141, 88, 4, 16, 2, hl) +
        S("M60 108C62 124 74 127 86 122", hs, 3.5) + C(89, 121, 4.5, hs));
    }
    // 9. objetos nas maos e ao lado do ombro
    if (ac === "biblia") {
      o.push('<g transform="rotate(-8 130 178)">' + R(110, 160, 40, 34, 3, "#2b1d14") + R(146, 162, 3, 30, 1, "#efe6cf") +
        S("M130 168L130 186M123 174L137 174", "#d9a71c", 2.6) + "</g>" + E(110, 186, 7, 9, pele) + E(152, 178, 6, 8, pele));
    } else if (ac === "celular") {
      o.push('<g transform="rotate(12 128 170)">' + R(116, 148, 24, 40, 5, "#1c1f24") + R(119, 153, 18, 29, 2, "#7fc3f0") +
        R(121, 157, 10, 3, 1, "#ffffff", ' opacity=".7"') + R(121, 163, 14, 3, 1, "#ffffff", ' opacity=".5"') + "</g>" +
        E(126, 188, 13, 10, pele) + S("M118 186Q126 182 134 186", pdk, 1.5));
    } else if (ac === "caneca") {
      var mc = ca || "#f2c230";
      o.push(S("M70 154C66 148 74 144 70 138M80 154C76 148 84 144 80 138", "#ffffff", 2.4, ' opacity=".8"') +
        S("M62 168C52 168 52 184 62 184", mc, 4) + R(62, 160, 26, 30, 4, mc) + R(62, 160, 26, 5, 2, dk(mc, 0.2)) +
        E(76, 193, 15, 8, pele));
    } else if (ac === "espeto") {
      o.push(S("M163 200L163 96", "#8a6b45", 3.4) + P("M159.5 98L163 86L166.5 98Z", "#c8c8c8") +
        R(152, 104, 22, 16, 6, "#8b3a22") + R(153, 123, 20, 9, 3, "#9ac36b") + R(152, 135, 22, 16, 6, "#a3502d") +
        R(153, 154, 20, 15, 6, "#7a2f1a") + E(163, 186, 11, 10, pele));
    } else if (ac === "megafone") {
      o.push(R(54, 170, 9, 18, 3, "#3a3d42", ' transform="rotate(-40 58 179)"') +
        P("M65 164L41 110L7 138L55 172Z", "#ece6d4", ' stroke="#3a3d42" stroke-width="2.4" stroke-linejoin="round"') + P("M47 124L44 117L13 142L19 146Z", "#c8412f") +
        E(24, 124, 22, 7, "#6b6f76", ' transform="rotate(-39 24 124)" stroke="#ece6d4" stroke-width="2"') + E(60, 176, 10, 9, pele));
    }
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" role="img" aria-hidden="true">' + o.join("") + "</svg>";
  }

  w.POLITIZE_AVATARES = { svg: svg, EXPRESSOES: ["fechado", "neutro", "aberto"], CABELOS: CABELOS, ACESSORIOS: ACESS, ROUPAS: ROUPAS };
})(window);
