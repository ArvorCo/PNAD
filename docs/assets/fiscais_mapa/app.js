// Mapa de fiscais: aplicativo estático escrito à mão, sem build.
// Lê assets/fiscais_mapa/dados.json (seções sinalizadas do capítulo 13) e, sob demanda,
// cep/<2>.json, zonas.json e municipios.json, gerados por scripts/fiscais-mapa-build.py.
// Distância em linha reta pela fórmula inversa de Vincenty no elipsoide WGS84.
(function () {
  'use strict';

  var BASE = 'assets/fiscais_mapa/';
  var RAIOS = [1, 2, 5, 10, 15, 20, 30, 50];
  var RAIO_PADRAO = 10;
  var NIVEIS = ['alta', 'media', 'baixa'];
  var NOME_NIVEL = { alta: 'Alta', media: 'Média', baixa: 'Baixa' };
  var PESO_NIVEL = { alta: 3, media: 2, baixa: 1 };
  var NOME_RISCO = { alto: 'alto', medio: 'médio', baixo: 'baixo' };
  var UFS = { AC: 'Acre', AL: 'Alagoas', AP: 'Amapá', AM: 'Amazonas', BA: 'Bahia', CE: 'Ceará', DF: 'Distrito Federal', ES: 'Espírito Santo', GO: 'Goiás', MA: 'Maranhão', MT: 'Mato Grosso', MS: 'Mato Grosso do Sul', MG: 'Minas Gerais', PA: 'Pará', PB: 'Paraíba', PR: 'Paraná', PE: 'Pernambuco', PI: 'Piauí', RJ: 'Rio de Janeiro', RN: 'Rio Grande do Norte', RS: 'Rio Grande do Sul', RO: 'Rondônia', RR: 'Roraima', SC: 'Santa Catarina', SP: 'São Paulo', SE: 'Sergipe', TO: 'Tocantins', ZZ: 'Exterior' };
  var COLS_LISTA = [
    ['nivel', 'Nível'], ['uf', 'UF'], ['municipio', 'Município'], ['zona', 'Zona'], ['secao', 'Seção'],
    ['local', 'Local de votação'], ['bairro', 'Bairro'], ['cep', 'CEP'], ['pontuacao', 'Pontos'],
    ['criterios', 'Critérios'], ['risco', 'Risco do território'], ['dist', 'Distância'], ['coord', 'Mapa'],
  ];

  var S = {
    dados: null, linhas: [], locais: new Map(), criterios: {},
    filtro: { uf: '', mun: '', zona: '', cep: '', texto: '', niveis: new Set(NIVEIS) },
    raio: RAIO_PADRAO, modo: 'mapa', centro: null,
    ordem: { col: 'nivel', dir: 1 }, pagina: 1, porPagina: 50, buscaLista: '',
    mapa: null, cluster: null, circulo: null, alvo: null, marcadores: new Map(),
    cache: new Map(), zonas: null, municipios: null,
  };

  var $ = function (s, r) { return (r || document).querySelector(s); };
  var nf1 = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  var nf0 = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 });

  function h(tag, attrs) {
    var n = document.createElement(tag);
    var a = attrs || {};
    Object.keys(a).forEach(function (k) {
      var v = a[k];
      if (v === null || v === undefined || v === false) return;
      if (k === 'class') n.className = v;
      else if (k === 'text') n.textContent = v;
      else if (k.indexOf('on') === 0 && typeof v === 'function') n.addEventListener(k.slice(2), v);
      else n.setAttribute(k, v === true ? '' : String(v));
    });
    for (var i = 2; i < arguments.length; i++) anexar(n, arguments[i]);
    return n;
  }
  function anexar(n, f) {
    if (f === null || f === undefined || f === false || f === '') return;
    if (Array.isArray(f)) { f.forEach(function (x) { anexar(n, x); }); return; }
    n.appendChild(f instanceof Node ? f : document.createTextNode(String(f)));
  }
  function norm(s) { return String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/\s+/g, ' ').trim(); }
  function so(s) { return String(s || '').replace(/\D/g, ''); }
  function cepFmt(c) { var d = so(c); return d.length === 8 ? d.slice(0, 5) + '-' + d.slice(5) : d; }
  var SIGLAS = new Set(['EE', 'EEF', 'EEE', 'EEEF', 'EEEFM', 'EEFM', 'EEM', 'EM', 'EMEF', 'EMEI', 'EMEB', 'EMEIEF', 'CEU', 'CIEP', 'CAIC', 'CEI', 'CMEI', 'CEF', 'CED', 'CE', 'ETEC', 'FATEC', 'SESC', 'SESI', 'SENAI', 'SENAC', 'IFAC', 'UFAC', 'IBGE', 'UF', 'II', 'III', 'IV', 'VI', 'VII', 'VIII', 'IX', 'XI', 'XII', 'BR', 'SP', 'RJ', 'MG', 'PUC', 'USP', 'UNESP', 'UFRJ', 'UFMG', 'APAE', 'CRAS', 'CSU', 'UBS', 'ESF']);
  var MINUSC = new Set(['de', 'da', 'do', 'das', 'dos', 'e', 'em', 'na', 'no', 'nas', 'nos', 'a', 'o', 'para', 'com', 'por']);
  function caixa(s) {
    return String(s || '').split(/(\s+|[(/.,-])/).map(function (p, i) {
      var limpa = p.replace(/[^A-Za-zÀ-ú0-9]/g, '');
      if (!limpa) return p;
      var up = limpa.toUpperCase();
      if (SIGLAS.has(up) || (/^[A-Z]{2,5}$/.test(up) && !/[AEIOU]/.test(up))) return p.toUpperCase();
      var low = p.toLowerCase();
      if (i > 0 && MINUSC.has(low)) return low;
      return low.charAt(0).toUpperCase() + low.slice(1);
    }).join('');
  }
  function maiuscula(t) { return t ? t.charAt(0).toUpperCase() + t.slice(1) : t; }
  function km(v) { return v === null || v === undefined ? '' : (v < 10 ? nf1.format(v) : nf0.format(v)) + ' km'; }

  function buscar(url) {
    if (S.cache.has(url)) return S.cache.get(url);
    var p = fetch(url, { credentials: 'same-origin' }).then(function (r) {
      if (!r.ok) { var e = new Error('HTTP ' + r.status); e.status = r.status; throw e; }
      return r.json();
    });
    p.catch(function () { S.cache.delete(url); });
    S.cache.set(url, p);
    return p;
  }

  /* ------------------------------------------------------------ geodésia */

  // Fórmula inversa de Vincenty no elipsoide WGS84; distância em km. Se não convergir
  // (pontos quase antípodas, impossível dentro do Brasil), usa o grande círculo.
  function distanciaKm(lat1, lon1, lat2, lon2) {
    var a = 6378137, f = 1 / 298.257223563, b = a * (1 - f);
    var rad = Math.PI / 180;
    var L = (lon2 - lon1) * rad;
    var U1 = Math.atan((1 - f) * Math.tan(lat1 * rad));
    var U2 = Math.atan((1 - f) * Math.tan(lat2 * rad));
    var sinU1 = Math.sin(U1), cosU1 = Math.cos(U1), sinU2 = Math.sin(U2), cosU2 = Math.cos(U2);
    var lambda = L, it = 0, sinS, cosS, sigma, sinAlpha, cos2Alpha, cos2SigmaM, lambdaP;
    do {
      var sinL = Math.sin(lambda), cosL = Math.cos(lambda);
      sinS = Math.sqrt(Math.pow(cosU2 * sinL, 2) + Math.pow(cosU1 * sinU2 - sinU1 * cosU2 * cosL, 2));
      if (sinS === 0) return 0;
      cosS = sinU1 * sinU2 + cosU1 * cosU2 * cosL;
      sigma = Math.atan2(sinS, cosS);
      sinAlpha = cosU1 * cosU2 * sinL / sinS;
      cos2Alpha = 1 - sinAlpha * sinAlpha;
      cos2SigmaM = cos2Alpha !== 0 ? cosS - 2 * sinU1 * sinU2 / cos2Alpha : 0;
      var C = f / 16 * cos2Alpha * (4 + f * (4 - 3 * cos2Alpha));
      lambdaP = lambda;
      lambda = L + (1 - C) * f * sinAlpha * (sigma + C * sinS * (cos2SigmaM + C * cosS * (-1 + 2 * cos2SigmaM * cos2SigmaM)));
    } while (Math.abs(lambda - lambdaP) > 1e-12 && ++it < 200);
    if (it >= 200) return haversineKm(lat1, lon1, lat2, lon2);
    var u2 = cos2Alpha * (a * a - b * b) / (b * b);
    var A = 1 + u2 / 16384 * (4096 + u2 * (-768 + u2 * (320 - 175 * u2)));
    var B = u2 / 1024 * (256 + u2 * (-128 + u2 * (74 - 47 * u2)));
    var dS = B * sinS * (cos2SigmaM + B / 4 * (cosS * (-1 + 2 * cos2SigmaM * cos2SigmaM) - B / 6 * cos2SigmaM * (-3 + 4 * sinS * sinS) * (-3 + 4 * cos2SigmaM * cos2SigmaM)));
    return b * A * (sigma - dS) / 1000;
  }
  function haversineKm(lat1, lon1, lat2, lon2) {
    var rad = Math.PI / 180, dp = (lat2 - lat1) * rad, dl = (lon2 - lon1) * rad;
    var x = Math.pow(Math.sin(dp / 2), 2) + Math.cos(lat1 * rad) * Math.cos(lat2 * rad) * Math.pow(Math.sin(dl / 2), 2);
    return 2 * 6371.0088 * Math.asin(Math.min(1, Math.sqrt(x)));
  }
  function coordOk(r) { return typeof r.lat === 'number' && typeof r.lon === 'number' && isFinite(r.lat) && isFinite(r.lon); }

  /* ------------------------------------------------------------ dados */

  function preparar(d) {
    S.dados = d;
    S.criterios = d.criterios || {};
    var cols = d.colunas;
    S.linhas = d.linhas.map(function (ln, i) {
      var r = { i: i };
      cols.forEach(function (c, j) { r[c] = ln[j]; });
      r.crit = String(r.criterios || '').split('');
      r.critNomes = r.crit.map(function (c) { return (S.criterios[c] && S.criterios[c].nome) || c; });
      r.busca = norm([r.local, r.endereco, r.bairro, r.municipio, r.uf, r.cep, r.explicacao, r.critNomes.join(' '), 'zona ' + r.zona, 'secao ' + r.secao].join(' '));
      return r;
    });
    S.linhas.forEach(function (r) {
      var l = S.locais.get(r.local_id);
      if (!l) {
        l = { id: r.local_id, uf: r.uf, municipio: r.municipio, zona: r.zona, local: r.local, endereco: r.endereco, bairro: r.bairro, cep: r.cep, lat: r.lat, lon: r.lon, secoes: [], nivel: 'baixa', risco: r.risco };
        S.locais.set(r.local_id, l);
      }
      l.secoes.push(r);
      if (PESO_NIVEL[r.nivel] > PESO_NIVEL[l.nivel]) l.nivel = r.nivel;
    });
  }

  function passaFiltro(r) {
    var f = S.filtro;
    if (!f.niveis.has(r.nivel)) return false;
    if (f.uf && r.uf !== f.uf) return false;
    if (f.mun && r.municipio !== f.mun) return false;
    if (f.zona && Number(r.zona) !== Number(f.zona)) return false;
    if (f.texto) {
      var termos = norm(f.texto).split(' ');
      for (var i = 0; i < termos.length; i++) if (r.busca.indexOf(termos[i]) < 0) return false;
    }
    return true;
  }

  function filtradas() { return S.linhas.filter(passaFiltro); }

  function comDistancia(rs) {
    rs.forEach(function (r) {
      r.dist = S.centro && coordOk(r) ? distanciaKm(S.centro.lat, S.centro.lon, r.lat, r.lon) : null;
    });
    return rs;
  }

  /* ------------------------------------------------------------ busca */

  async function geocodificarCep(cep) {
    var arq = await buscar(BASE + 'cep/' + cep.slice(0, 2) + '.json').catch(function () { return null; });
    if (arq && arq.exato && arq.exato[cep]) {
      var e = arq.exato[cep];
      return { lat: e[0], lon: e[1], rotulo: 'CEP ' + cepFmt(cep), precisao: e[2] === 1 ? 'o local de votação com este CEP' : 'os ' + e[2] + ' locais de votação com este CEP' };
    }
    var p5 = cep.slice(0, 5);
    if (arq && arq.p5 && arq.p5[p5]) {
      var q = arq.p5[p5];
      return { lat: q[0], lon: q[1], rotulo: 'CEP ' + cepFmt(cep), precisao: 'locais de votação com CEP começando em ' + p5 + ', nenhum com o CEP exato' };
    }
    if (arq && arq.p5) {
      var chaves = Object.keys(arq.p5).filter(function (k) { return k.slice(0, 4) === cep.slice(0, 4); });
      if (!chaves.length) chaves = Object.keys(arq.p5).filter(function (k) { return k.slice(0, 3) === cep.slice(0, 3); });
      if (chaves.length) {
        var alvo = Number(p5);
        chaves.sort(function (x, y) { return Math.abs(Number(x) - alvo) - Math.abs(Number(y) - alvo); });
        var g = arq.p5[chaves[0]];
        return { lat: g[0], lon: g[1], rotulo: 'CEP ' + cepFmt(cep), precisao: 'aproximação grossa: CEP de local de votação mais parecido (' + chaves[0] + '-…)' };
      }
    }
    return null;
  }

  async function centroZona(uf, zona) {
    if (!S.zonas) S.zonas = await buscar(BASE + 'zonas.json');
    var z = S.zonas[uf] && S.zonas[uf][String(Number(zona))];
    return z ? { lat: z[0], lon: z[1], rotulo: 'zona ' + Number(zona) + ' ' + (uf === 'ZZ' ? 'do exterior' : '(' + uf + ')'), precisao: 'centro dos ' + z[2] + ' locais de votação da zona' } : null;
  }

  async function centroMunicipio(uf, nome) {
    if (!S.municipios) S.municipios = await buscar(BASE + 'municipios.json');
    var alvo = norm(nome);
    for (var i = 0; i < S.municipios.length; i++) {
      var m = S.municipios[i];
      if (m[0] === uf && norm(m[1]) === alvo) return { lat: m[2], lon: m[3], rotulo: caixa(nome) + '/' + uf, precisao: 'centro do município' };
    }
    return null;
  }

  async function aplicarBusca(rolar) {
    var f = S.filtro;
    f.uf = $('#f-uf').value;
    f.mun = $('#f-mun').value;
    f.texto = $('#f-texto').value.trim();
    var zonaTxt = so($('#f-zona').value);
    var cep = so($('#q-cep').value);
    if (zonaTxt && !f.uf) { setStatus('Escolha a UF para buscar a zona: o número da zona se repete entre os estados.', true); $('#f-uf').focus(); return; }
    if (cep && cep.length !== 8) { setStatus('O CEP precisa de 8 dígitos.', true); $('#q-cep').focus(); return; }
    f.zona = zonaTxt ? String(Number(zonaTxt)) : '';
    f.cep = cep;
    var centro = null;
    try {
      if (cep) {
        centro = await geocodificarCep(cep);
        if (!centro) { setStatus('Nenhum local de votação tem CEP parecido com ' + cepFmt(cep) + '. Tente a zona ou o município.', true); return; }
      } else if (f.zona) {
        centro = await centroZona(f.uf, f.zona);
        if (!centro) { setStatus('A zona ' + f.zona + ' não aparece ' + (f.uf === 'ZZ' ? 'no exterior' : 'em ' + (UFS[f.uf] || f.uf)) + ' nos dados. Confira o número no título de eleitor.', true); return; }
      } else if (f.mun) {
        centro = await centroMunicipio(f.uf, f.mun);
      }
    } catch (e) {
      setStatus('Não foi possível carregar o índice de busca agora. Tente de novo.', true);
      return;
    }
    S.centro = centro;
    S.pagina = 1;
    atualizar(true);
    if (window.innerWidth < 980 && rolar) $('#status').scrollIntoView({ block: 'start', behavior: 'smooth' });
  }

  /* ------------------------------------------------------------ mapa */

  function iniciarMapa() {
    if (typeof L === 'undefined') {
      $('#mapa').replaceChildren(h('p', { class: 'aviso' }, 'A biblioteca do mapa não carregou. A lista continua disponível em "Ver em lista".'));
      return;
    }
    S.mapa = L.map('mapa', { zoomControl: true, preferCanvas: true, minZoom: 3, worldCopyJump: true }).setView([-14.5, -52], 4);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '© colaboradores do <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(S.mapa);
    L.control.scale({ imperial: false }).addTo(S.mapa);
    S.cluster = L.markerClusterGroup({
      chunkedLoading: true,
      showCoverageOnHover: false,
      spiderfyOnMaxZoom: true,
      maxClusterRadius: 50,
      iconCreateFunction: function (c) {
        var pior = 'baixa';
        c.getAllChildMarkers().forEach(function (m) { if (PESO_NIVEL[m.options.nivel] > PESO_NIVEL[pior]) pior = m.options.nivel; });
        var n = c.getChildCount();
        var tam = n < 10 ? 34 : n < 100 ? 40 : n < 1000 ? 46 : 54;
        return L.divIcon({ html: '<span>' + nf0.format(n) + '</span>', className: 'grupo grupo-' + pior, iconSize: [tam, tam] });
      },
    });
    S.mapa.addLayer(S.cluster);
    S.locais.forEach(function (l) {
      if (!coordOk(l)) return;
      var m = L.marker([l.lat, l.lon], {
        nivel: l.nivel,
        icon: L.divIcon({ className: 'pino pino-' + l.nivel, iconSize: [18, 18], html: '' }),
        title: caixa(l.local) + ', ' + NOME_NIVEL[l.nivel],
        keyboard: true,
      });
      m.bindPopup(function () { return ficha(l); }, { maxWidth: 360, minWidth: 260, autoPanPadding: [24, 24] });
      S.marcadores.set(l.id, m);
    });
  }

  function ficha(l) {
    var vis = l.secoes.filter(passaFiltro).sort(function (a, b) { return PESO_NIVEL[b.nivel] - PESO_NIVEL[a.nivel] || (b.pontuacao || 0) - (a.pontuacao || 0) || a.secao - b.secao; });
    var todas = vis.length ? vis : l.secoes;
    var dist = S.centro && coordOk(l) ? distanciaKm(S.centro.lat, S.centro.lon, l.lat, l.lon) : null;
    var conferir = [];
    todas.forEach(function (r) { r.crit.forEach(function (c) { var t = S.criterios[c] && S.criterios[c].conferir; if (t && conferir.indexOf(t) < 0) conferir.push(t); }); });
    var motivos = (S.dados.risco_local || {})[l.id] || [];
    var gmaps = 'https://www.google.com/maps/search/?api=1&query=' + l.lat + ',' + l.lon;
    var osm = 'https://www.openstreetmap.org/?mlat=' + l.lat + '&mlon=' + l.lon + '#map=17/' + l.lat + '/' + l.lon;
    return h('div', { class: 'ficha' },
      h('p', { class: 'ficha-nivel n-' + l.nivel }, 'Prioridade ' + NOME_NIVEL[l.nivel].toLowerCase()),
      h('h3', {}, caixa(l.local)),
      h('p', { class: 'ficha-end' }, [caixa(l.endereco), caixa(l.bairro), caixa(l.municipio) + '/' + l.uf, l.cep ? 'CEP ' + cepFmt(l.cep) : ''].filter(Boolean).join(' · ')),
      h('p', { class: 'ficha-meta' }, 'Zona ' + l.zona + (dist !== null ? ' · ' + km(dist) + ' em linha reta de ' + S.centro.rotulo : '')),
      h('ul', { class: 'ficha-secoes' }, todas.map(function (r) {
        return h('li', {},
          h('b', {}, 'Seção ' + r.secao), ' ',
          h('span', { class: 'chip n-' + r.nivel }, NOME_NIVEL[r.nivel]), ' ',
          r.critNomes.join('; '),
          r.explicacao ? h('small', {}, 'Explicação provável: ' + r.explicacao) : null,
          h('a', { class: 'ficha-pol', href: 'politizesuavizinhanca.html#s=' + encodeURIComponent(r.uf + '-' + r.zona + '-' + r.secao) }, 'Todos os motivos desta seção'));
      })),
      vis.length && vis.length < l.secoes.length ? h('p', { class: 'ficha-meta' }, (l.secoes.length - vis.length) + ' seção(ões) deste local fora dos filtros.') : null,
      l.risco ? h('p', { class: 'ficha-risco' }, h('b', {}, 'Risco do território: ' + (NOME_RISCO[l.risco] || l.risco)), motivos.length ? ' (' + motivos.join('; ') + ')' : '', '. ', maiuscula(S.dados.risco_validar || ''), '.') : null,
      conferir.length ? h('p', { class: 'ficha-conf' }, h('b', {}, 'O que conferir: '), conferir.join('; '), '.') : null,
      h('p', { class: 'ficha-links' },
        h('a', { href: gmaps, target: '_blank', rel: 'noopener' }, 'Abrir no Google Maps'), ' · ',
        h('a', { href: osm, target: '_blank', rel: 'noopener' }, 'OpenStreetMap')));
  }

  function desenharMapa(rs, enquadrar) {
    if (!S.mapa) return { locais: 0 };
    var noRaio = rs.filter(function (r) { return coordOk(r) && (!S.centro || r.dist <= S.raio); });
    var ids = new Set(noRaio.map(function (r) { return r.local_id; }));
    var lista = [];
    ids.forEach(function (id) { var m = S.marcadores.get(id); if (m) lista.push(m); });
    S.cluster.clearLayers();
    S.cluster.addLayers(lista);
    if (S.circulo) { S.mapa.removeLayer(S.circulo); S.circulo = null; }
    if (S.alvo) { S.mapa.removeLayer(S.alvo); S.alvo = null; }
    if (S.centro) {
      S.circulo = L.circle([S.centro.lat, S.centro.lon], { radius: S.raio * 1000, color: '#151812', weight: 2, dashArray: '6 6', fill: true, fillOpacity: 0.04, interactive: false }).addTo(S.mapa);
      S.alvo = L.marker([S.centro.lat, S.centro.lon], { icon: L.divIcon({ className: 'alvo', iconSize: [22, 22], html: '' }), title: S.centro.rotulo, keyboard: false, interactive: false }).addTo(S.mapa);
    }
    if (enquadrar) {
      if (S.centro) {
        S.mapa.fitBounds(S.circulo.getBounds(), { padding: [24, 24], maxZoom: 16 });
      } else if (lista.length) {
        S.mapa.fitBounds(L.featureGroup(lista).getBounds(), { padding: [30, 30], maxZoom: 15 });
      }
    }
    return { locais: lista.length, secoes: noRaio.length };
  }

  /* ------------------------------------------------------------ lista */

  function valorOrdem(r, col) {
    if (col === 'nivel') return -PESO_NIVEL[r.nivel] * 1e6 - (r.pontuacao || 0);
    if (col === 'dist') return r.dist === null || r.dist === undefined ? Infinity : r.dist;
    if (col === 'coord') return coordOk(r) ? 0 : 1;
    if (col === 'criterios') return r.critNomes.join('; ');
    if (col === 'risco') return { alto: 0, medio: 1, baixo: 2 }[r.risco] ?? 3;
    var v = r[col];
    return v === null || v === undefined ? '' : v;
  }

  function ordenar(rs) {
    var c = S.ordem.col, d = S.ordem.dir;
    var col = new Intl.Collator('pt-BR', { numeric: true, sensitivity: 'base' });
    return rs.slice().sort(function (a, b) {
      var x = valorOrdem(a, c), y = valorOrdem(b, c);
      var r = typeof x === 'number' && typeof y === 'number' ? x - y : col.compare(String(x), String(y));
      if (r === 0) r = col.compare(a.uf + a.municipio, b.uf + b.municipio) || a.zona - b.zona || a.secao - b.secao;
      return r * d;
    });
  }

  function linhasLista(rs) {
    var q = norm(S.buscaLista);
    if (!q) return rs;
    var termos = q.split(' ');
    return rs.filter(function (r) {
      for (var i = 0; i < termos.length; i++) if (r.busca.indexOf(termos[i]) < 0) return false;
      return true;
    });
  }

  function desenharLista(rs) {
    var todas = ordenar(linhasLista(rs));
    S.listaAtual = todas;
    var n = todas.length;
    var paginas = Math.max(1, Math.ceil(n / S.porPagina));
    if (S.pagina > paginas) S.pagina = paginas;
    var ini = (S.pagina - 1) * S.porPagina;
    var pag = todas.slice(ini, ini + S.porPagina);
    var semCoord = todas.filter(function (r) { return !coordOk(r); }).length;
    $('#l-resumo').textContent = nf0.format(n) + (n === 1 ? ' seção' : ' seções') + ' pelos filtros, sem limite de distância' +
      (semCoord ? ', ' + nf0.format(semCoord) + ' sem coordenada' : '') + (S.centro ? '. A coluna de distância mede a partir de ' + S.centro.rotulo + ', só para informação.' : '.');

    var thead = $('#tabela thead');
    thead.replaceChildren(h('tr', {}, COLS_LISTA.map(function (c) {
      var ativo = S.ordem.col === c[0];
      return h('th', { scope: 'col', 'aria-sort': ativo ? (S.ordem.dir === 1 ? 'ascending' : 'descending') : 'none' },
        h('button', { type: 'button', class: 'ord', onclick: function () {
          if (S.ordem.col === c[0]) S.ordem.dir = -S.ordem.dir; else { S.ordem.col = c[0]; S.ordem.dir = 1; }
          S.pagina = 1; atualizar(false);
        } }, c[1], h('span', { class: 'seta', 'aria-hidden': 'true' }, ativo ? (S.ordem.dir === 1 ? ' ▲' : ' ▼') : '')));
    })));
    $('#tabela tbody').replaceChildren.apply($('#tabela tbody'), pag.map(function (r) {
      return h('tr', {},
        h('td', {}, h('span', { class: 'chip n-' + r.nivel }, NOME_NIVEL[r.nivel])),
        h('td', {}, r.uf), h('td', {}, caixa(r.municipio)), h('td', { class: 'num' }, String(r.zona)),
        h('td', { class: 'num' }, h('a', { href: 'politizesuavizinhanca.html#s=' + encodeURIComponent(r.uf + '-' + r.zona + '-' + r.secao), title: 'Todos os motivos desta seção no Politize' }, String(r.secao))),
        h('td', {}, caixa(r.local), h('small', {}, caixa(r.endereco))), h('td', {}, caixa(r.bairro)), h('td', { class: 'num' }, cepFmt(r.cep)),
        h('td', { class: 'num' }, r.pontuacao === null || r.pontuacao === undefined ? '' : String(r.pontuacao)),
        h('td', {}, r.critNomes.join('; ')),
        h('td', {}, r.risco ? NOME_RISCO[r.risco] || r.risco : 'sem base'),
        h('td', { class: 'num' }, km(r.dist)),
        h('td', {}, coordOk(r)
          ? h('a', { href: 'https://www.google.com/maps/search/?api=1&query=' + r.lat + ',' + r.lon, target: '_blank', rel: 'noopener' }, 'Google Maps')
          : h('span', { class: 'sem' }, 'sem coordenada')));
    }));
    if (!pag.length) $('#tabela tbody').replaceChildren(h('tr', {}, h('td', { colspan: String(COLS_LISTA.length) }, 'Nenhuma seção com esses filtros.')));
    desenharPaginas(paginas);
  }

  function desenharPaginas(total) {
    var nav = $('#paginas');
    var botoes = [];
    var ir = function (p) { return function () { S.pagina = p; atualizar(false); $('#lista').scrollIntoView({ block: 'start' }); }; };
    botoes.push(h('button', { type: 'button', disabled: S.pagina <= 1, onclick: ir(S.pagina - 1) }, 'Anterior'));
    var vistas = new Set([1, total, S.pagina - 2, S.pagina - 1, S.pagina, S.pagina + 1, S.pagina + 2]);
    var ult = 0;
    for (var p = 1; p <= total; p++) {
      if (!vistas.has(p)) continue;
      if (p - ult > 1) botoes.push(h('span', { class: 'reticencias' }, '…'));
      botoes.push(h('button', { type: 'button', 'aria-current': p === S.pagina ? 'page' : null, onclick: ir(p) }, String(p)));
      ult = p;
    }
    botoes.push(h('button', { type: 'button', disabled: S.pagina >= total, onclick: ir(S.pagina + 1) }, 'Próxima'));
    nav.replaceChildren.apply(nav, botoes);
  }

  function exportarCsv() {
    var rs = S.listaAtual || [];
    var cab = ['nivel', 'uf', 'municipio', 'zona', 'secao', 'local', 'endereco', 'bairro', 'cep', 'lat', 'lon', 'distancia_km_linha_reta', 'pontuacao', 'criterios', 'explicacao_provavel', 'risco_territorio', 'aptos', 'flavio_pct', 'lula_pct', 'google_maps'];
    var dec = function (v, c) { return v === null || v === undefined || v === '' ? '' : (typeof v === 'number' ? v.toFixed(c).replace('.', ',') : String(v)); };
    var esc = function (v) { var s = v === null || v === undefined ? '' : String(v); return /[";\n\r]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; };
    var linhas = [cab.join(';')];
    rs.forEach(function (r) {
      linhas.push([
        NOME_NIVEL[r.nivel], r.uf, r.municipio, r.zona, r.secao, r.local, r.endereco, r.bairro, r.cep,
        coordOk(r) ? dec(r.lat, 5) : '', coordOk(r) ? dec(r.lon, 5) : '', r.dist === null || r.dist === undefined ? '' : dec(r.dist, 2),
        r.pontuacao, r.critNomes.join(' | '), r.explicacao, r.risco || '', r.aptos, dec(r.flavio_pct, 2), dec(r.lula_pct, 2),
        coordOk(r) ? 'https://www.google.com/maps/search/?api=1&query=' + r.lat + ',' + r.lon : '',
      ].map(esc).join(';'));
    });
    var blob = new Blob(['﻿' + linhas.join('\r\n')], { type: 'text/csv;charset=utf-8' });
    var a = h('a', { href: URL.createObjectURL(blob), download: 'fiscais_filtrados_' + new Date().toISOString().slice(0, 10) + '.csv' });
    document.body.appendChild(a);
    a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
  }

  /* ------------------------------------------------------------ estado e controles */

  function setStatus(t, erro) {
    var s = $('#status');
    s.textContent = t;
    s.classList.toggle('erro', Boolean(erro));
  }

  function atualizar(enquadrar) {
    if (!S.dados) return;
    var rs = comDistancia(filtradas());
    var semCoord = rs.filter(function (r) { return !coordOk(r); }).length;
    if (S.modo === 'mapa') {
      var res = desenharMapa(rs, enquadrar);
      var onde = S.centro ? ' a até ' + S.raio + ' km em linha reta de ' + S.centro.rotulo + ' (' + S.centro.precisao + ')' : '';
      setStatus(nf0.format(res.locais || 0) + (res.locais === 1 ? ' local de votação' : ' locais de votação') + ' com ' + nf0.format(res.secoes || 0) + (res.secoes === 1 ? ' seção sinalizada' : ' seções sinalizadas') + onde + '.' +
        (semCoord && !S.centro ? ' ' + nf0.format(semCoord) + ' sem coordenada válida ficam fora do mapa; veja em lista.' : '') +
        (S.centro && rs.length && !res.secoes ? ' Aumente a distância ou veja em lista.' : ''));
    } else {
      desenharLista(rs);
      setStatus(nf0.format(rs.length) + ' seções nos filtros. Na lista não há limite de distância.');
    }
    gravarHash();
  }

  function trocarModo(m) {
    S.modo = m;
    $('#m-mapa').setAttribute('aria-pressed', String(m === 'mapa'));
    $('#m-lista').setAttribute('aria-pressed', String(m === 'lista'));
    $('#mapa').hidden = m !== 'mapa';
    $('#lista').hidden = m !== 'lista';
    $('#bloco-raio').classList.toggle('inativo', m === 'lista');
    document.body.classList.toggle('modo-lista', m === 'lista');
    $('#raios').querySelectorAll('button').forEach(function (b) { b.disabled = m === 'lista'; });
    if (m === 'mapa' && S.mapa) setTimeout(function () { S.mapa.invalidateSize(); atualizar(true); }, 0);
    else atualizar(false);
  }

  function montarRaios() {
    var box = $('#raios');
    box.replaceChildren.apply(box, RAIOS.map(function (r) {
      return h('button', { type: 'button', role: 'radio', 'aria-checked': String(r === S.raio), 'data-r': String(r), onclick: function () {
        S.raio = r;
        box.querySelectorAll('button').forEach(function (b) { b.setAttribute('aria-checked', String(Number(b.dataset.r) === r)); });
        atualizar(true);
      } }, r + ' km');
    }));
  }

  function montarUfs() {
    var sel = $('#f-uf');
    var presentes = new Set(S.linhas.map(function (r) { return r.uf; }));
    Object.keys(UFS).forEach(function (u) {
      sel.appendChild(h('option', { value: u }, u + ' · ' + UFS[u] + (presentes.has(u) ? '' : ' (sem seção sinalizada)')));
    });
  }

  function montarMunicipios() {
    var uf = $('#f-uf').value;
    var sel = $('#f-mun');
    if (!uf) { sel.replaceChildren(h('option', { value: '' }, 'Escolha a UF primeiro')); sel.disabled = true; return; }
    var nomes = Array.from(new Set(S.linhas.filter(function (r) { return r.uf === uf; }).map(function (r) { return r.municipio; })))
      .sort(new Intl.Collator('pt-BR').compare);
    sel.replaceChildren.apply(sel, [h('option', { value: '' }, 'Todos (' + nomes.length + ' com seção sinalizada)')].concat(nomes.map(function (n) { return h('option', { value: n }, caixa(n)); })));
    sel.disabled = false;
  }

  function contarNiveis() {
    NIVEIS.forEach(function (n) {
      var c = S.linhas.filter(function (r) { return r.nivel === n; }).length;
      $('#n-' + n).textContent = nf0.format(c);
    });
  }

  function gravarHash() {
    var f = S.filtro, p = [];
    if (f.uf) p.push('uf=' + f.uf);
    if (f.mun) p.push('mun=' + encodeURIComponent(f.mun));
    if (f.zona) p.push('zona=' + f.zona);
    if (f.cep) p.push('cep=' + f.cep);
    if (f.texto) p.push('q=' + encodeURIComponent(f.texto));
    if (f.niveis.size < 3) p.push('nivel=' + Array.from(f.niveis).join(','));
    if (S.raio !== RAIO_PADRAO) p.push('raio=' + S.raio);
    if (S.modo === 'lista') p.push('modo=lista');
    try { history.replaceState(null, '', location.pathname + location.search + (p.length ? '#' + p.join('&') : '')); } catch (e) { /* navegador embutido */ }
  }

  function lerHash() {
    var q = new URLSearchParams(location.hash.slice(1));
    if (q.get('uf') && UFS[q.get('uf')]) { $('#f-uf').value = q.get('uf'); montarMunicipios(); }
    if (q.get('mun')) $('#f-mun').value = q.get('mun');
    if (q.get('zona')) $('#f-zona').value = so(q.get('zona'));
    if (q.get('cep')) $('#q-cep').value = cepFmt(q.get('cep'));
    if (q.get('q')) $('#f-texto').value = q.get('q');
    if (q.get('nivel')) {
      var ns = q.get('nivel').split(',').filter(function (n) { return NIVEIS.indexOf(n) >= 0; });
      if (ns.length) {
        S.filtro.niveis = new Set(ns);
        document.querySelectorAll('.niveis input').forEach(function (i) { i.checked = S.filtro.niveis.has(i.value); });
      }
    }
    var r = Number(q.get('raio'));
    if (RAIOS.indexOf(r) >= 0) S.raio = r;
    montarRaios();
    return q.get('modo') === 'lista' ? 'lista' : 'mapa';
  }

  function limpar() {
    ['#q-cep', '#f-zona', '#f-texto', '#l-busca'].forEach(function (s) { $(s).value = ''; });
    $('#f-uf').value = '';
    montarMunicipios();
    S.filtro = { uf: '', mun: '', zona: '', cep: '', texto: '', niveis: new Set(NIVEIS) };
    document.querySelectorAll('.niveis input').forEach(function (i) { i.checked = true; });
    S.centro = null; S.buscaLista = ''; S.pagina = 1;
    atualizar(true);
  }

  function ligar() {
    $('#f-busca').addEventListener('submit', function (ev) { ev.preventDefault(); aplicarBusca(true); });
    window.addEventListener('hashchange', function () { location.reload(); });
    $('#b-limpar').addEventListener('click', limpar);
    $('#f-uf').addEventListener('change', function () { montarMunicipios(); aplicarBusca(); });
    $('#f-mun').addEventListener('change', aplicarBusca);
    $('#q-cep').addEventListener('input', function (ev) {
      var d = so(ev.target.value).slice(0, 8);
      ev.target.value = d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
    });
    var t;
    $('#f-texto').addEventListener('input', function () { clearTimeout(t); t = setTimeout(function () { S.filtro.texto = $('#f-texto').value.trim(); S.pagina = 1; atualizar(true); }, 250); });
    document.querySelectorAll('.niveis input').forEach(function (i) {
      i.addEventListener('change', function () {
        if (i.checked) S.filtro.niveis.add(i.value); else S.filtro.niveis.delete(i.value);
        S.pagina = 1;
        atualizar(false);
      });
    });
    $('#m-mapa').addEventListener('click', function () { trocarModo('mapa'); });
    $('#m-lista').addEventListener('click', function () { trocarModo('lista'); });
    var tl;
    $('#l-busca').addEventListener('input', function () { clearTimeout(tl); tl = setTimeout(function () { S.buscaLista = $('#l-busca').value; S.pagina = 1; atualizar(false); }, 200); });
    $('#l-por-pag').addEventListener('change', function () { S.porPagina = Number($('#l-por-pag').value) || 50; S.pagina = 1; atualizar(false); });
    $('#l-csv').addEventListener('click', exportarCsv);
  }

  async function iniciar() {
    if (location.protocol === 'file:') {
      setStatus('Esta página lê arquivos de dados e precisa ser aberta por um endereço da web: https://brasil.arvor.co/fiscais_mapa.html.', true);
      return;
    }
    montarRaios();
    ligar();
    var d;
    try {
      d = await buscar(BASE + 'dados.json');
    } catch (e) {
      setStatus('Não foi possível carregar as seções sinalizadas. Recarregue a página.', true);
      return;
    }
    preparar(d);
    montarUfs();
    contarNiveis();
    iniciarMapa();
    var modo = lerHash();
    S.filtro.uf = $('#f-uf').value;
    if (so($('#f-zona').value) || so($('#q-cep').value) || $('#f-mun').value || $('#f-texto').value) await aplicarBusca();
    trocarModo(modo);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar);
  else iniciar();
})();
