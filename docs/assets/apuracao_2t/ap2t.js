/* Apuração do 2º turno ao vivo. Escrito à mão, sem framework.
   Lê os JSON de assets/apuracao_2t/ (ou de exemplo/ com ?fonte=exemplo), confere o manifest a cada 60 s
   e só rebaixa o arquivo cujo SHA-256 mudou. Todo texto entra por textContent. */
(function () {
  'use strict';
  var ARQUIVOS = ['estado', 'config', 'regioes', 'ufs', 'abstencao', 'estaduais', 'evolucao', 'pausas', 'secoes', 'paralela', 'anomalias', 'resultado', 'mapa'];
  var EXEMPLO = new URLSearchParams(location.search).get('fonte') === 'exemplo';
  var BASE = 'assets/apuracao_2t/' + (EXEMPLO ? 'exemplo/' : '');
  var T0 = Date.parse('2026-10-25T20:00:00Z');
  var INTERVALO_MS = 60000, VELHO_MIN = 20;
  var D = {}, SHAS = {}, MANIFEST = null, sorts = {}, ultimaFalha = null;

  var nf0 = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 });
  var nf1 = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  var nf2 = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  var fmtHora = new Intl.DateTimeFormat('pt-BR', { timeZone: 'America/Sao_Paulo', hour: '2-digit', minute: '2-digit' });
  function n0(x) { return typeof x === 'number' ? nf0.format(x) : '-'; }
  function n1(x) { return typeof x === 'number' ? nf1.format(x) : '-'; }
  function n2(x) { return typeof x === 'number' ? nf2.format(x) : '-'; }
  function hora(iso) { var t = Date.parse(iso); return isNaN(t) ? '-' : fmtHora.format(new Date(t)); }
  function minDe(iso) { return (Date.parse(iso) - T0) / 60000; }
  function idade(s) {
    if (typeof s !== 'number') return '-';
    if (s < 60) return Math.round(s) + ' s';
    if (s < 3600) return Math.round(s / 60) + ' min';
    return Math.floor(s / 3600) + ' h ' + Math.round((s % 3600) / 60) + ' min';
  }
  function titulo(t) {
    return String(t || '').toLowerCase().replace(/(^|\s)(\S)/g, function (m, a, b) { return a + b.toUpperCase(); })
      .replace(/\b(Da|De|Do|Das|Dos|E)\b/g, function (m) { return m.toLowerCase(); });
  }

  /* DOM */
  function h(tag, cls, texto) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (texto !== undefined && texto !== null) e.textContent = texto;
    return e;
  }
  function add(pai) {
    for (var i = 1; i < arguments.length; i++) { if (arguments[i]) pai.appendChild(arguments[i]); }
    return pai;
  }
  var NS = 'http://www.w3.org/2000/svg';
  function s(tag, attrs, texto) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) { e.setAttribute(k, attrs[k]); }
    if (texto !== undefined) e.textContent = texto;
    return e;
  }
  function troca(id, no) {
    var alvo = document.getElementById(id);
    if (!alvo) return;
    while (alvo.firstChild) alvo.removeChild(alvo.firstChild);
    alvo.appendChild(no);
  }
  function vazio(msg) { return h('p', 'vazio', msg); }
  function ok(nome) { return !!D[nome] && !D[nome].pendente; }
  function dl(itens) {
    var d = h('dl', 'chave');
    itens.forEach(function (it) {
      var bloco = h('div'), dd = h('dd', null, it[1]);
      if (it[2]) dd.appendChild(h('small', null, it[2]));
      add(bloco, h('dt', null, it[0]), dd); d.appendChild(bloco);
    });
    return d;
  }
  function barraDuelo(pf, pl, fina) {
    var b = h('div', 'barra' + (fina ? ' fina' : ''));
    b.setAttribute('role', 'img');
    b.setAttribute('aria-label', 'Duelo: ' + n1(pf) + ' por cento contra ' + n1(pl) + ' por cento');
    var a = h('div', 'f'), c = h('div', 'l');
    a.style.width = pf + '%'; c.style.width = pl + '%';
    return add(b, a, c, h('div', 'meio'));
  }

  /* candidatos */
  function candidatos() {
    var mapa = {}, lista = (D.resultado && D.resultado.cand) || [];
    lista.forEach(function (c) { mapa[c.sqcand] = { sq: c.sqcand, n: c.n, nome: titulo(c.nmu || c.nm), sg: c.sg }; });
    var vot = D.regioes && D.regioes.brasil && D.regioes.brasil.votos || {};
    Object.keys(vot).forEach(function (sq) { if (!mapa[sq]) mapa[sq] = { sq: sq, n: '', nome: 'Candidato ' + sq.slice(-3), sg: '' }; });
    var todos = Object.keys(mapa).map(function (k) { return mapa[k]; });
    var f = todos.filter(function (c) { return c.n === '22'; })[0];
    var l = todos.filter(function (c) { return c.n === '13'; })[0];
    if (!f) f = todos.filter(function (c) { return c !== l; })[0];
    if (!l) l = todos.filter(function (c) { return c !== f; })[0];
    return { f: f, l: l, mapa: mapa };
  }
  function pv(agr, c) { var v = agr && agr.votos && c && agr.votos[c.sq]; return v ? v.pvapn : null; }
  function vap(agr, c) { var v = agr && agr.votos && c && agr.votos[c.sq]; return v ? v.vap : null; }
  function atrasoTxt(a) {
    if (typeof a !== 'number') return 'sem régua';
    if (a >= 2) return '+' + n0(a) + ' min';
    if (a <= -2) return n0(a) + ' min';
    return 'no ritmo';
  }

  /* placar */
  function rPlacar() {
    if (!ok('regioes')) return troca('placar-corpo', vazio('Aguardando o primeiro lote de dados do 2º turno.'));
    var C = candidatos(), b = D.regioes.brasil, pf = pv(b, C.f), pl = pv(b, C.l);
    if (pf === null || pl === null) return troca('placar-corpo', vazio('Aguardando votos válidos.'));
    var raiz = h('div');
    var duelo = h('div', 'duelo');
    [[C.f, pf, 'f'], [C.l, pl, 'l']].forEach(function (x) {
      var c = h('div', 'cand ' + x[2] + (x[1] > (x[2] === 'f' ? pl : pf) ? ' lidera' : ''));
      add(c, h('div', 'nome', x[0].nome), h('div', 'num', (x[0].n ? x[0].n + ' · ' : '') + x[0].sg), h('div', 'pct', n2(x[1]) + '%'),
        h('div', 'votos', n0(vap(b, x[0])) + ' votos'));
      duelo.appendChild(c);
    });
    raiz.appendChild(duelo);
    raiz.appendChild(barraDuelo(pf, pl));
    var dif = Math.abs(pf - pl), lider = pf > pl ? C.f : C.l;
    raiz.appendChild(h('p', 'lider-frase', dif < 0.005 ? 'Empate técnico na parcial.' : lider.nome + ' na frente por ' + n2(dif) + ' ponto percentual dos válidos apurados.'));
    var ref = b.ref_1t;
    raiz.appendChild(dl([
      ['Seções apuradas', n1(b.pst) + '%', n0(b.st) + ' de ' + n0(b.ts)],
      ['Faltam', n0(b.snt), 'seções'],
      ['Abstenção corrente', n1(b.pa) + '%', ref && typeof ref.pa_final_1t === 'number' ? '1º turno final: ' + n1(ref.pa_final_1t) + '%' : null],
      ['Contra o 1º turno', ref ? atrasoTxt(ref.atraso_min) : 'sem régua', ref ? 'no mesmo horário da apuração' : null]
    ]));
    raiz.appendChild(h('p', 'nota', 'Parcial de apuração, não é projeção. Votos válidos excluem brancos e nulos (' + n0(b.vb) + ' brancos e ' + n0(b.vn) + ' nulos até agora).'));
    troca('placar-corpo', raiz);
  }

  /* regiões */
  function rRegioes() {
    if (!ok('regioes')) return troca('regioes-corpo', vazio('Aguardando dados das regiões.'));
    var C = candidatos(), regs = D.regioes.regioes || [];
    var maisLenta = regs.reduce(function (m, r) { return !m || r.pst < m.pst ? r : m; }, null);
    var wrap = h('div', 'cartoes tres');
    regs.forEach(function (r) {
      var pf = pv(r, C.f), pl = pv(r, C.l);
      var c = h('article', 'cartao' + (maisLenta && r.sigla === maisLenta.sigla && r.pst < 99.9 ? ' lenta' : ''));
      var t = h('h3', null, r.nome);
      if (maisLenta && r.sigla === maisLenta.sigla && r.pst < 99.9) t.appendChild(h('span', 'chip alerta', 'mais lenta'));
      c.appendChild(t);
      if (pf !== null && pl !== null) {
        c.appendChild(barraDuelo(pf, pl, true));
        var l1 = h('div', 'linha');
        add(l1, h('span', 'f-txt', n1(pf) + '% ' + (C.f ? C.f.nome.split(' ')[0] : '')), h('span', 'l-txt', n1(pl) + '% ' + (C.l ? C.l.nome.split(' ')[0] : '')));
        c.appendChild(l1);
      }
      var l2 = h('div', 'linha');
      add(l2, h('span', null, 'apurado ' + n1(r.pst) + '%'), h('span', null, 'abstenção ' + n1(r.pa) + '%'));
      c.appendChild(l2);
      var l3 = h('div', 'linha');
      add(l3, h('span', null, n1(r.vel_10min_spm) + ' seções/min'), h('span', null, 'vs 1T: ' + atrasoTxt(r.ref_1t && r.ref_1t.atraso_min)));
      c.appendChild(l3);
      wrap.appendChild(c);
    });
    troca('regioes-corpo', wrap);
  }
  function rEvolucao() {
    var alvo = document.getElementById('evolucao-corpo');
    if (!alvo) return;
    var no = h('div');
    if (ok('evolucao') && D.evolucao.series && D.evolucao.series.BR && D.evolucao.series.BR.length > 1) {
      var pts = D.evolucao.series.BR, C = candidatos();
      var W = 640, H = 230, ml = 38, mr = 56, mt = 14, mb = 28, pw = W - ml - mr, ph = H - mt - mb;
      var xmax = Math.max(pts[pts.length - 1][0], 60), ymin = 30, ymax = 70;
      var X = function (m) { return ml + (m / xmax) * pw; };
      var Y = function (v) { v = Math.max(ymin, Math.min(ymax, v)); return mt + (1 - (v - ymin) / (ymax - ymin)) * ph; };
      var svg = s('svg', { viewBox: '0 0 ' + W + ' ' + H, role: 'img', 'aria-label': 'Percentual de votos válidos dos dois candidatos ao longo da noite' });
      [30, 40, 50, 60, 70].forEach(function (v) {
        svg.appendChild(s('line', { x1: ml, x2: W - mr, y1: Y(v), y2: Y(v), 'class': v === 50 ? 'eixo' : 'grade' }));
        svg.appendChild(s('text', { x: ml - 6, y: Y(v) + 4, 'text-anchor': 'end' }, v + '%'));
      });
      for (var hr = 0; hr * 60 <= xmax; hr++) { svg.appendChild(s('text', { x: X(hr * 60), y: H - 8, 'text-anchor': 'middle' }, (17 + hr) + 'h')); }
      [[2, 'l-f', C.f], [3, 'l-l', C.l]].forEach(function (x) {
        var d = pts.map(function (p, i) { return (i ? 'L' : 'M') + X(p[0]).toFixed(1) + ' ' + Y(p[x[0]]).toFixed(1); }).join(' ');
        svg.appendChild(s('path', { d: d, 'class': x[1] }));
        var ult = pts[pts.length - 1];
        svg.appendChild(s('text', { x: X(ult[0]) + 5, y: Y(ult[x[0]]) + 4, 'class': 'forte' }, n1(ult[x[0]]) + '%'));
      });
      var fig = h('figure');
      add(fig, svg, h('figcaption', null, 'Nacional ao longo da noite, % dos votos válidos apurados até cada horário. Linha azul: ' + (C.f ? C.f.nome : '') + '. Linha vermelha: ' + (C.l ? C.l.nome : '') + '. As primeiras horas pesam pouco: as seções que fecham primeiro não representam o país.'));
      no.appendChild(h('h3', null, 'Nacional ao longo da noite'));
      no.appendChild(fig);
    }
    troca('evolucao-corpo', no);
  }

  /* tabela ordenável */
  function tabela(id, legenda, cols, linhas, destaqueFn) {
    var st = sorts[id];
    var ord = linhas.slice();
    if (st) {
      var col = cols.filter(function (c) { return c.k === st.k; })[0];
      if (col) ord.sort(function (a, b) {
        var va = col.v(a), vb = col.v(b);
        if (va === vb) return 0;
        if (va === null || va === undefined) return 1;
        if (vb === null || vb === undefined) return -1;
        var r = typeof va === 'string' ? va.localeCompare(vb, 'pt-BR') : va - vb;
        return st.dir === 'asc' ? r : -r;
      });
    }
    var cont = h('div', 'rola');
    cont.tabIndex = 0; cont.setAttribute('role', 'region'); cont.setAttribute('aria-label', legenda);
    var t = h('table'), cap = h('caption', null, legenda), th = h('thead'), tr = h('tr');
    t.appendChild(cap);
    cols.forEach(function (c) {
      var cel = h('th', c.n ? 'n' : '');
      cel.scope = 'col';
      if (st && st.k === c.k) cel.setAttribute('aria-sort', st.dir === 'asc' ? 'ascending' : 'descending');
      var btn = h('button', null, c.t);
      btn.type = 'button';
      btn.addEventListener('click', function () {
        var atual = sorts[id];
        sorts[id] = { k: c.k, dir: atual && atual.k === c.k && atual.dir === 'asc' ? 'desc' : 'asc' };
        renderTudo();
      });
      cel.appendChild(btn); tr.appendChild(cel);
    });
    th.appendChild(tr); t.appendChild(th);
    var tb = h('tbody');
    ord.forEach(function (l) {
      var r = h('tr', destaqueFn && destaqueFn(l) ? 'destaque' : '');
      cols.forEach(function (c) {
        var td = h('td', c.n ? 'n' : '');
        var v = c.r(l);
        if (v instanceof Node) td.appendChild(v); else td.textContent = v;
        r.appendChild(td);
      });
      tb.appendChild(r);
    });
    t.appendChild(tb); cont.appendChild(t);
    return cont;
  }
  function pstCel(p) {
    var f = h('span'), b = h('span', 'mbar'), i = h('div');
    i.style.width = Math.max(0, Math.min(100, p)) + '%';
    b.appendChild(i);
    return add(f, document.createTextNode(n1(p) + '%'), b);
  }
  function chip(txt, cls) { return h('span', 'chip' + (cls ? ' ' + cls : ''), txt); }

  /* ranking de UFs */
  function rUfs() {
    if (!ok('ufs')) return troca('ufs-corpo', vazio('Aguardando dados das UFs.'));
    var C = candidatos();
    var cols = [
      { k: 'uf', t: 'UF', v: function (u) { return u.uf; }, r: function (u) { var f = h('span'); add(f, h('strong', null, u.uf), document.createTextNode(' ' + (u.nome || ''))); return f; } },
      { k: 'pst', t: 'Apurado', n: true, v: function (u) { return u.pst; }, r: function (u) { return pstCel(u.pst); } },
      { k: 'snt', t: 'Faltam', n: true, v: function (u) { return u.snt; }, r: function (u) { return n0(u.snt); } },
      { k: 'atraso', t: 'Atraso vs 1T', n: true, v: function (u) { return u.ref_1t ? u.ref_1t.atraso_min : null; }, r: function (u) { return atrasoTxt(u.ref_1t && u.ref_1t.atraso_min); } },
      { k: 'idade', t: 'Última versão', n: true, v: function (u) { return u.idade_s; }, r: function (u) { return idade(u.idade_s); } },
      { k: 'pa', t: 'Abstenção', n: true, v: function (u) { return u.pa; }, r: function (u) { return n1(u.pa) + '%'; } },
      { k: 'lider', t: 'À frente', v: function (u) { return u.margem_pp; }, r: function (u) {
        var c = C.mapa[u.lider]; return c ? c.nome.split(' ')[0] + ' +' + n1(u.margem_pp) : '-'; } },
      { k: 'status', t: 'Situação', v: function (u) { return u.parada ? 0 : 1; }, r: function (u) {
        if (u.parada) return chip('parada', 'erro');
        if (u.snt === 0) return chip('fechou', 'ok');
        return chip('apurando'); } }
    ];
    var raiz = h('div');
    var paradas = D.ufs.ufs.filter(function (u) { return u.parada; });
    if (paradas.length) raiz.appendChild(h('p', 'lider-frase', paradas.length + ' UF(s) sem versão nova há mais de ' + D.ufs.limiar_parada_min + ' min: ' + paradas.map(function (u) { return u.uf; }).join(', ') + '.'));
    raiz.appendChild(tabela('ufs', 'Ranking das UFs, mais lentas primeiro', cols, D.ufs.ufs, function (u) { return u.parada; }));
    troca('ufs-corpo', raiz);
  }

  /* estaduais */
  function rEstaduais() {
    if (!ok('estaduais')) return troca('estaduais-corpo', vazio('Aguardando dados dos governadores.'));
    var wrap = h('div', 'cartoes tres');
    D.estaduais.ufs.forEach(function (e) {
      var c = h('article', 'cartao');
      var t = h('h3', null, e.nome);
      t.appendChild(h('span', 'chip', e.uf));
      c.appendChild(t);
      var a = e.cand[0], b = e.cand[1];
      if (a && b) {
        c.appendChild(barraDuelo(a.pvapn, b.pvapn, true));
        [a, b].forEach(function (x, i) {
          var l = h('div', 'cand-l'), esq = h('div');
          add(esq, h('b', null, titulo(x.nome_urna)), h('small', null, x.n + ' · ' + x.partido + (e.lider === x.sqcand ? ' · à frente' : '')));
          add(l, esq, h('span', i === 0 ? 'f-txt' : 'l-txt', n1(x.pvapn) + '%'));
          c.appendChild(l);
        });
      }
      var l2 = h('div', 'linha');
      add(l2, h('span', null, 'apurado ' + n1(e.pst) + '%'), h('span', null, 'abstenção ' + n1(e.pa) + '%'));
      c.appendChild(l2);
      var l3 = h('div', 'linha');
      add(l3, h('span', null, 'diferença ' + n1(e.margem_pp) + ' pp'), h('span', null, 'vs 1T: ' + atrasoTxt(e.ref_1t && e.ref_1t.atraso_min)));
      c.appendChild(l3);
      if (e.margem_pp < 2) c.appendChild(h('p', 'mini', 'Diferença menor que 2 pontos: o que falta apurar pode virar o resultado.'));
      if (e.viradas && e.viradas.length) {
        var v = e.viradas[e.viradas.length - 1];
        c.appendChild(h('p', 'mini', 'Virada às ' + hora(v.at) + ' (Brasília): a liderança trocou de mãos.'));
      }
      wrap.appendChild(c);
    });
    troca('estaduais-corpo', wrap);
  }

  /* abstenção */
  function dTxt(d) { return (d > 0 ? '+' : '') + n2(d) + ' pp'; }
  function rAbstencao() {
    if (!ok('abstencao')) return troca('abstencao-corpo', vazio('Aguardando municípios fechados.'));
    var A = D.abstencao, raiz = h('div');
    var b = A.brasil;
    raiz.appendChild(dl([
      ['Brasil, 2º turno', n1(b.pa_2t) + '%', 'municípios fechados'],
      ['Mesmos municípios, 1º turno', n1(b.pa_1t_mesmos) + '%'],
      ['Diferença', dTxt(b.delta_pp)],
      ['Eleitorado já fechado', n1(b.pct_te_fechado) + '%', n0(b.n_mun_fechados) + ' de ' + n0(b.n_mun) + ' municípios']
    ]));
    var cols = [
      { k: 'uf', t: 'UF', v: function (u) { return u.uf; }, r: function (u) { return u.uf; } },
      { k: 'fech', t: 'Fechado', n: true, v: function (u) { return u.pct_te_fechado; }, r: function (u) { return n0(u.pct_te_fechado) + '%'; } },
      { k: 'p2', t: '2º turno', n: true, v: function (u) { return u.pa_2t; }, r: function (u) { return n1(u.pa_2t) + '%'; } },
      { k: 'p1', t: '1º turno', n: true, v: function (u) { return u.pa_1t_mesmos; }, r: function (u) { return n1(u.pa_1t_mesmos) + '%'; } },
      { k: 'd', t: 'Diferença', n: true, v: function (u) { return u.delta_pp; }, r: function (u) {
        var f = h('span', u.delta_pp >= 2 ? 'pos' : (u.delta_pp <= -2 ? 'neg' : ''), dTxt(u.delta_pp)); return f; } },
      { k: 'pe', t: 'Leitura', v: function (u) { return Math.abs(u.delta_pp); }, r: function (u) {
        return Math.abs(u.delta_pp) >= 2 && u.pct_te_fechado >= 30 ? chip('pede explicação', 'alerta') : ''; } }
    ];
    var com = A.ufs.filter(function (u) { return u.n_mun_fechados > 0; });
    if (!sorts.abstencao) sorts.abstencao = { k: 'd', dir: 'desc' };
    raiz.appendChild(h('h3', null, 'Por UF'));
    raiz.appendChild(tabela('abstencao', 'Abstenção por UF contra o 1º turno, municípios fechados', cols, com, function (u) { return Math.abs(u.delta_pp) >= 2 && u.pct_te_fechado >= 30; }));
    var duas = h('div', 'duas-col');
    [['Municípios que mais subiram', A.destaques && A.destaques.subiu], ['Municípios que mais caíram', A.destaques && A.destaques.caiu]].forEach(function (x) {
      var col = h('div'); col.appendChild(h('h3', null, x[0]));
      var ul = h('ul', 'lista-m');
      (x[1] || []).slice(0, 5).forEach(function (m) {
        var li = h('li'); add(li, h('span', null, m.nm + ' (' + m.uf + ')'), h('span', null, n1(m.pa_1t) + '% → ' + n1(m.pa_2t) + '%'));
        ul.appendChild(li);
      });
      if (!ul.firstChild) ul.appendChild(h('li', null, 'Nenhum município com diferença de 3 pontos ou mais e 20 mil eleitores ou mais.'));
      col.appendChild(ul); duas.appendChild(col);
    });
    raiz.appendChild(duas);
    raiz.appendChild(h('p', 'nota', 'Cidades que fecham cedo tendem a ser as menores. Variação de poucos pontos é comum; a lista pede explicação, não indica irregularidade.'));
    troca('abstencao-corpo', raiz);
  }

  /* pausas */
  function rPausas() {
    if (!ok('pausas')) return troca('pausas-corpo', vazio('Aguardando dados de pausas.'));
    var P = D.pausas, raiz = h('div'), nac = P.nacional || {};
    var xmax = Math.max(P.min + 15, 240), W = 640, H = 150, ml = 112, mr = 12, mt = 14, mb = 26, pw = W - ml - mr;
    var X = function (m) { return ml + Math.max(0, Math.min(xmax, m)) / xmax * pw; };
    var svg = s('svg', { viewBox: '0 0 ' + W + ' ' + H, role: 'img', 'aria-label': 'Linha do tempo das pausas do arquivo nacional contra a pausa do 1º turno' });
    var y1 = mt, y2 = mt + 50, hh = 34;
    svg.appendChild(s('text', { x: ml - 8, y: y1 + 22, 'text-anchor': 'end' }, '2º turno'));
    svg.appendChild(s('text', { x: ml - 8, y: y2 + 22, 'text-anchor': 'end' }, '1º turno (ref.)'));
    svg.appendChild(s('rect', { x: ml, y: y1, width: pw, height: hh, fill: 'none', 'class': 'eixo' }));
    svg.appendChild(s('rect', { x: ml, y: y2, width: pw, height: hh, fill: 'none', 'class': 'eixo' }));
    for (var hr = 0; hr * 60 <= xmax; hr++) {
      svg.appendChild(s('line', { x1: X(hr * 60), x2: X(hr * 60), y1: y1, y2: y2 + hh, 'class': 'grade' }));
      svg.appendChild(s('text', { x: X(hr * 60), y: H - 8, 'text-anchor': 'middle' }, (17 + hr) + 'h'));
    }
    var ref = P.referencia_1t || {};
    function minHM(t) { var p = String(t).split(':'); return (parseInt(p[0], 10) - 17) * 60 + parseInt(p[1], 10); }
    if (ref.pausa_geral) {
      var a = minHM(ref.pausa_geral.de), b = minHM(ref.pausa_geral.ate);
      svg.appendChild(s('rect', { x: X(a), y: y2, width: Math.max(2, X(b) - X(a)), height: hh, 'class': 'faixa-1t' }));
      svg.appendChild(s('rect', { x: X(a), y: y1, width: Math.max(2, X(b) - X(a)), height: hh, 'class': 'faixa-1t', opacity: 0.35 }));
    }
    if (ref.travamento_nacional) {
      var a2 = minHM(ref.travamento_nacional.de), b2 = minHM(ref.travamento_nacional.ate);
      svg.appendChild(s('rect', { x: X(a2), y: y2, width: Math.max(2, X(b2) - X(a2)), height: hh, 'class': 'faixa-1t' }));
    }
    (nac.historico || []).forEach(function (p) {
      var x0 = X(minDe(p.de)), x1 = X(minDe(p.ate));
      svg.appendChild(s('rect', { x: x0, y: y1, width: Math.max(3, x1 - x0), height: hh, 'class': 'faixa-pausa' }));
    });
    if (nac.pausa_atual) {
      var x3 = X(minDe(nac.pausa_atual.desde));
      svg.appendChild(s('rect', { x: x3, y: y1, width: Math.max(3, X(P.min) - x3), height: hh, 'class': 'faixa-atual' }));
    }
    svg.appendChild(s('line', { x1: X(P.min), x2: X(P.min), y1: y1 - 6, y2: y2 + hh, 'class': 'agora' }));
    svg.appendChild(s('text', { x: X(P.min), y: y1 - 6, 'text-anchor': 'end', 'class': 'forte' }, 'agora'));
    var fig = h('figure');
    add(fig, svg, h('figcaption', null, 'Eixo em horário de Brasília desde as 17h. Faixa cinza: pausa geral do 1º turno (19:32 a 20:02) e travamento do arquivo nacional (18:00 a 18:10), como referência.'));
    var leg = h('ul', 'legenda');
    [['c', 'Referência do 1º turno'], ['a', 'Pausa já encerrada'], ['v', 'Pausa em curso']].forEach(function (x) {
      var li = h('li'); add(li, h('span', 'sw ' + x[0]), document.createTextNode(x[1])); leg.appendChild(li);
    });
    fig.appendChild(leg);
    raiz.appendChild(fig);
    var estado = nac.em_pausa && nac.pausa_atual
      ? 'Arquivo nacional em pausa há ' + n0(nac.pausa_atual.minutos) + ' min.'
      : 'Arquivo nacional sem pausa agora; última versão há ' + idade(nac.idade_s) + '.';
    raiz.appendChild(h('p', 'lider-frase', estado));
    var hist = nac.historico || [];
    raiz.appendChild(h('p', 'nota', hist.length
      ? hist.length + ' pausa(s) já encerrada(s) hoje, a mais longa com ' + n1(Math.max.apply(null, hist.map(function (p) { return p.minutos; }))) + ' min. Limiar: ' + P.limiar_min + ' min sem versão nova.'
      : 'Nenhuma pausa acima de ' + P.limiar_min + ' min hoje.'));
    if (P.soma_ufs) raiz.appendChild(h('p', 'nota', 'Soma dos arquivos de UF menos o arquivo nacional: ' + n0(P.soma_ufs.defasagem_secoes) + ' seções (' + n1(P.soma_ufs.defasagem_min) + ' min de defasagem).'));
    var emPausa = (P.ufs || []).filter(function (u) { return u.em_pausa; });
    if (emPausa.length) {
      var ul = h('ul', 'legenda');
      emPausa.forEach(function (u) { var li = h('li'); add(li, chip(u.uf, 'erro'), document.createTextNode('sem versão nova há ' + idade(u.idade_s))); ul.appendChild(li); });
      raiz.appendChild(h('h3', null, 'UFs em pausa'));
      raiz.appendChild(ul);
    }
    troca('pausas-corpo', raiz);
  }

  /* paralela */
  function rParalela() {
    var P = D.paralela;
    if (!P || P.pendente) return troca('paralela-corpo', vazio('Aguardando a totalização paralela.'));
    if (P.erro) return troca('paralela-corpo', vazio('Fonte indisponível: ' + P.erro));
    var raiz = h('div'), r = P.recebidos || {}, cf = P.conferencia || {};
    raiz.appendChild(dl([
      ['BUs recebidos', n0(r.bus), n0(r.secoes) + ' seções em ' + n0(r.ufs) + ' UFs'],
      ['Conferidos iguais', n0(cf.iguais), 'ao BU publicado pelo TSE'],
      ['Divergências', n0(cf.divergentes), 'campos que diferem do TSE'],
      ['Seções em conflito', n0(r.conflitos), 'ficam fora da soma']
    ]));
    raiz.appendChild(h('p', 'nota', 'Aguardando o TSE publicar: ' + n0(cf.tse_ainda_nao_publicou) + ' · erro de leitura: ' + n0(cf.erro) + ' · fora do oficial: ' + n0(cf.fora_do_oficial) + ' · pendentes: ' + n0(cf.pendentes) + '.'));
    var pres = P.placar_bus && P.placar_bus.presidente, C = candidatos();
    if (pres && pres.votos) {
      var vf = pres.votos[C.f && C.f.n], vl = pres.votos[C.l && C.l.n];
      if (typeof vf === 'number' && typeof vl === 'number' && vf + vl > 0) {
        var tot = vf + vl, pf = vf / tot * 100, pl = 100 - pf;
        raiz.appendChild(h('h3', null, 'Placar dos BUs recebidos (votos nominais)'));
        raiz.appendChild(barraDuelo(pf, pl));
        var l = h('div', 'linha');
        add(l, h('span', 'f-txt', C.f.nome + ' ' + n1(pf) + '% (' + n0(vf) + ')'), h('span', 'l-txt', C.l.nome + ' ' + n1(pl) + '% (' + n0(vl) + ')'));
        raiz.appendChild(l);
        raiz.appendChild(h('p', 'nota', 'Soma dos BUs recebidos, não projeção. A amostra é de quem enviou e não representa o país.'));
      }
    }
    var cob = (P.cobertura_uf || []).slice().sort(function (a, b) { return b.pct - a.pct; }).slice(0, 8);
    if (cob.length) {
      var ul = h('ul', 'lista-m');
      cob.forEach(function (c) { var li = h('li'); add(li, h('span', null, c.uf), h('span', null, n0(c.bus) + ' BUs · ' + n2(c.pct) + '% das seções')); ul.appendChild(li); });
      raiz.appendChild(h('h3', null, 'Maior cobertura por UF'));
      raiz.appendChild(ul);
    }
    var dv = P.divergencias || [];
    raiz.appendChild(h('h3', null, 'Últimas divergências com o TSE'));
    if (dv.length) {
      var cols = [
        { k: 'sec', t: 'Seção', v: function (d) { return d.uf; }, r: function (d) { return d.uf + ' · zona ' + d.zona + ' · seção ' + d.secao; } },
        { k: 'cp', t: 'Campos (paralela contra TSE)', v: function (d) { return d.campos.length; }, r: function (d) { return d.campos.map(function (c) { return c.campo + ': ' + c.paralela + ' contra ' + c.tse; }).join('; '); } },
        { k: 'ho', t: 'Conferido', n: true, v: function (d) { return d.conferido_em; }, r: function (d) { return hora(d.conferido_em); } }
      ];
      raiz.appendChild(tabela('paralela', 'Seções divergentes', cols, dv));
      raiz.appendChild(h('p', 'nota', 'Divergência pede explicação, não indica irregularidade: pode ser erro de leitura do QR ou de transcrição.'));
    } else {
      raiz.appendChild(vazio('Nenhuma divergência até agora.'));
    }
    var p = h('p'); var a = h('a', null, 'Painel completo da totalização paralela'); a.href = 'totalizacao_painel.html';
    raiz.appendChild(add(p, a));
    troca('paralela-corpo', raiz);
  }

  /* alertas */
  var CAT = { pausa: 'pausa', atraso: 'atraso', abstencao: 'abstenção', divergencia: 'divergência', paralela: 'paralela', virada: 'virada', fechou: 'fechou', regressao: 'regressão', outro: 'outro' };
  function rAlertas() {
    var A = D.anomalias;
    if (!Array.isArray(A)) return troca('alertas-corpo', vazio('Aguardando alertas.'));
    var raiz = h('div'), cont = {};
    A.forEach(function (a) { cont[a.categoria] = (cont[a.categoria] || 0) + 1; });
    var c = h('div', 'cont-alertas');
    Object.keys(cont).forEach(function (k) { c.appendChild(chip((CAT[k] || k) + ': ' + cont[k], k === 'divergencia' ? 'erro' : (k === 'fechou' || k === 'paralela' ? 'ok' : 'alerta'))); });
    raiz.appendChild(c);
    var ul = h('ul', 'feed');
    A.slice(0, 20).forEach(function (a) {
      var li = h('li', a.severidade), topo = h('div', 'topo');
      add(topo, document.createTextNode(hora(a.at)), chip(CAT[a.categoria] || a.categoria), a.uf ? chip(a.uf) : null);
      add(li, topo, h('div', 'txt', a.texto));
      ul.appendChild(li);
    });
    if (!A.length) ul.appendChild(vazio('Nenhum alerta até agora.'));
    raiz.appendChild(ul);
    troca('alertas-corpo', raiz);
  }

  /* cabeçalho de estado */
  function atualizarMeta() {
    var meta = document.getElementById('meta'), av = document.getElementById('avisos');
    if (!meta || !av) return;
    while (meta.firstChild) meta.removeChild(meta.firstChild);
    while (av.firstChild) av.removeChild(av.firstChild);
    if (EXEMPLO) {
      var ex = h('div', 'aviso'); add(ex, h('strong', null, 'Dados de exemplo'), document.createTextNode('Valores sintéticos para ensaio do layout. Não são resultados da eleição.'));
      av.appendChild(ex);
    }
    if (!MANIFEST) {
      meta.appendChild(h('span', 'ponto velho'));
      meta.appendChild(document.createTextNode(ultimaFalha ? 'Sem dados ainda. ' + ultimaFalha : 'Carregando os dados...'));
      return;
    }
    var min = (Date.now() - Date.parse(MANIFEST.gerado_em)) / 60000, velho = min > VELHO_MIN && !EXEMPLO;
    meta.appendChild(h('span', 'ponto' + (velho ? ' velho' : '')));
    meta.appendChild(document.createTextNode('Dados de ' + hora(MANIFEST.gerado_em) + ' (Brasília)' + (EXEMPLO ? '' : ', há ' + idade(min * 60)) + ' · recarrega a cada 60 s'));
    if (velho) {
      var a = h('div', 'aviso'); add(a, h('strong', null, 'Dados com mais de ' + VELHO_MIN + ' minutos'), document.createTextNode('A publicação pode estar parada ou sem rede. O que você vê é a última versão publicada.'));
      av.appendChild(a);
    }
    var pend = (MANIFEST.pendentes || []);
    if (pend.length) {
      var p = h('div', 'aviso'); add(p, h('strong', null, 'Parte dos dados ainda não chegou'), document.createTextNode('Sem publicação para: ' + pend.join(', ') + '. Essas seções mostram a última versão disponível.'));
      av.appendChild(p);
    }
    if (ultimaFalha) {
      var f = h('div', 'aviso'); add(f, h('strong', null, 'Falha ao recarregar'), document.createTextNode(ultimaFalha));
      av.appendChild(f);
    }
  }

  function renderTudo() {
    var fns = [rPlacar, rRegioes, rEvolucao, rUfs, rEstaduais, rAbstencao, rPausas, rParalela, rAlertas, atualizarMeta];
    fns.forEach(function (f) {
      try { f(); } catch (e) { if (window.console) console.error(f.name, e); }
    });
  }

  /* carga */
  function pegar(url) {
    return fetch(url, { cache: 'no-store' }).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    });
  }
  function carregar() {
    return pegar(BASE + 'manifest.json?t=' + Date.now()).then(function (m) {
      /* O CDN pode devolver um manifesto anterior ao já exibido: a página nunca volta no tempo. */
      var novo = Date.parse(m && m.gerado_em), atual = MANIFEST ? Date.parse(MANIFEST.gerado_em) : NaN;
      if (MANIFEST && isFinite(atual) && !(novo >= atual)) { ultimaFalha = null; return []; }
      MANIFEST = m; ultimaFalha = null;
      var tarefas = ARQUIVOS.map(function (nome) {
        var info = m.arquivos && m.arquivos[nome];
        var sha = info ? info.sha256 : '';
        if (D[nome] && SHAS[nome] === sha && sha) return Promise.resolve(false);
        return pegar(BASE + nome + '.json?v=' + (sha ? sha.slice(0, 12) : Date.now())).then(function (j) {
          D[nome] = j; SHAS[nome] = sha; return true;
        }).catch(function () { return false; });
      });
      return Promise.all(tarefas);
    }).catch(function (e) {
      ultimaFalha = 'Não foi possível ler o manifesto (' + (e && e.message ? e.message : 'erro') + '). Tentando de novo em 60 s.';
    }).then(renderTudo);
  }
  function iniciar() {
    renderTudo();
    carregar();
    setInterval(carregar, INTERVALO_MS);
    setInterval(atualizarMeta, 15000);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar); else iniciar();
})();
