/* Painel da totalização paralela. Escrito à mão. Sem biblioteca externa.
   1) carrega os JSON estáticos (caminhos relativos); 2) oferece "Atualizar agora" pelo PostgREST. */
(function () {
  'use strict';

  var DADOS = 'assets/totalizacao_dados/';
  var API = 'https://brvjvizqbyfamtxogvqf.supabase.co/rest/v1/';
  var CHAVE = 'sb_publishable_OdrY6f2C-CdRzkorgyaudQ_taVWSIKw'; // publicável por desenho
  var CANDS = [];
  var CORRIGE = { FLAVIO: 'Flávio' };
  var ESTATICOS = {
    br: 'totais_br.json', uf: 'totais_uf.json', resumo: 'resumo_cargo_uf.json',
    cobUf: 'cobertura_uf.json', conf: 'conflitos.json', est: 'estatisticas.json', manifest: 'manifest.json'
  };
  var VIVAS = {
    br: 'v_totais_br', uf: 'v_totais_uf', resumo: 'v_resumo_cargo_uf',
    cobUf: 'v_cobertura_uf', conf: 'v_conflito', est: 'v_estatisticas'
  };

  var D = { br: [], uf: [], resumo: [], cobUf: [], conf: [], est: {}, manifest: null, tse: null };
  var meta = { gerado: null, origem: 'estático' };
  var ordem = { cob: { col: 'pct', dir: -1 }, conf: { col: 'uf', dir: 1 } };

  function $(id) { return document.getElementById(id); }
  function nf(n, d) {
    return Number(n).toLocaleString('pt-BR', { minimumFractionDigits: d || 0, maximumFractionDigits: d || 0 });
  }
  function num(v) { var n = Number(v); return isFinite(n) ? n : 0; }
  function el(tag, cls, txt) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (txt !== undefined) e.textContent = txt;
    return e;
  }
  function vazio(texto) { return el('p', 'vazio', texto); }
  function uf(v) { return String(v || '').toUpperCase(); }
  function caixaNormal(t) {
    var peq = { de: 1, do: 1, da: 1, dos: 1, das: 1, e: 1 };
    return String(t).toLowerCase().split(/\s+/).map(function (w, i) {
      if (i > 0 && peq[w]) return w;
      var c = w.charAt(0).toUpperCase() + w.slice(1);
      return CORRIGE[c.toUpperCase()] || c;
    }).join(' ');
  }
  function achaCand(u, cargo, numero) {
    for (var i = 0; i < CANDS.length; i++) {
      var c = CANDS[i];
      if (String(c.uf).toLowerCase() === String(u).toLowerCase() && String(c.cargo) === String(cargo) && String(c.numero) === String(numero)) return c;
    }
    return null;
  }
  // nome_urna em caixa normal com a sigla; sem o arquivo ou sem o número, mostra o número.
  function nomeCand(u, cargo, numero, curto) {
    var c = achaCand(u, cargo, numero);
    if (!c || !c.nome_urna) return String(numero);
    var n = caixaNormal(c.nome_urna);
    return curto || !c.partido ? n : n + ' (' + c.partido + ')';
  }
  function hora(iso) {
    if (!iso) return 'sem registro';
    var d = new Date(iso);
    if (isNaN(d)) return String(iso);
    return d.toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });
  }
  function linhas(j) { return j && Array.isArray(j.linhas) ? j.linhas : []; }

  function aviso(texto, erro) {
    var box = $('avisos');
    var d = el('div', 'aviso' + (erro ? ' erro' : ''));
    d.appendChild(el('strong', '', erro ? 'Falha' : 'Aviso'));
    d.appendChild(document.createTextNode(texto));
    box.appendChild(d);
  }
  function limparAvisos() { $('avisos').textContent = ''; }

  /* ---------- cálculo ---------- */
  function cobTotais() {
    var t = { total: 0, com: 0, conf: 0, aptos: 0, aptosCom: 0 };
    D.cobUf.forEach(function (r) {
      t.total += num(r.secoes_total); t.com += num(r.secoes_com_bu); t.conf += num(r.secoes_em_conflito);
      t.aptos += num(r.aptos_total); t.aptosCom += num(r.aptos_com_bu);
    });
    return t;
  }
  function presidente(linhasTot) {
    var m = {}, total = 0;
    linhasTot.forEach(function (r) {
      if (String(r.cargo) !== '1') return;
      var c = String(r.candidato);
      m[c] = (m[c] || 0) + num(r.votos);
      total += num(r.votos);
    });
    return { por: m, total: total };
  }

  /* ---------- hero ---------- */
  function renderHero() {
    var t = cobTotais();
    var h = $('cobertura');
    h.textContent = '';
    if (!t.com) {
      h.textContent = 'Nenhum BU recebido ainda.';
      if (t.total) h.appendChild(document.createTextNode(' O país tem ' + nf(t.total) + ' seções à espera.'));
    } else {
      var pct = t.total ? t.com / t.total * 100 : 0;
      h.appendChild(document.createTextNode('Recebemos o BU de '));
      h.appendChild(el('b', '', nf(t.com)));
      h.appendChild(document.createTextNode(' seções, '));
      h.appendChild(el('b', '', nf(pct, 2) + '%'));
      h.appendChild(document.createTextNode(' das '));
      h.appendChild(el('b', '', nf(t.total)));
      h.appendChild(document.createTextNode(' seções do país.'));
    }
    var m = $('meta');
    var ult = D.est && D.est.ultimo_envio;
    m.textContent = 'Dados: ' + meta.origem + ' · gerados em ' + hora(meta.gerado) + ' · último envio: ' + hora(ult);
    var bar = $('barra-atualiza');
    if (!bar) {
      bar = el('div', 'atualiza');
      bar.id = 'barra-atualiza';
      var b = el('button', '', 'Atualizar agora');
      b.type = 'button';
      b.id = 'btn-atualiza';
      b.addEventListener('click', function () { atualizarAoVivo(false); });
      bar.appendChild(b);
      var s = el('span', '', 'Lê as views públicas do banco, sem passar por arquivo.');
      s.id = 'atualiza-msg';
      bar.appendChild(s);
      m.parentNode.appendChild(bar);
    }
  }

  /* ---------- placar ---------- */
  function renderPlacar() {
    var box = $('placar-corpo');
    box.textContent = '';
    var p = presidente(D.br);
    var t = cobTotais();
    if (!p.total) { box.appendChild(vazio('Nenhum BU recebido ainda. Quando a primeira seção chegar, o placar aparece aqui.')); return; }
    var f = num(p.por['22']), l = num(p.por['13']);
    var outros = p.total - f - l;
    var pf = f / p.total * 100, pl = l / p.total * 100;
    var dif = pf - pl;

    var c = el('div', 'placar');
    c.appendChild(el('p', 'selo', 'Soma dos BUs recebidos, não projeção'));
    var nums = el('div', 'nums');
    var a = el('div', 'flavio'); a.appendChild(el('b', '', nf(pf, 2) + '%'));
    a.appendChild(el('span', '', nomeCand('br', 1, 22) + ' · ' + nf(f) + ' votos'));
    var b = el('div', 'lula'); b.appendChild(el('b', '', nf(pl, 2) + '%'));
    b.appendChild(el('span', '', nomeCand('br', 1, 13) + ' · ' + nf(l) + ' votos'));
    nums.appendChild(a); nums.appendChild(b);
    c.appendChild(nums);

    var dv = el('div', 'diverge');
    dv.setAttribute('role', 'img');
    var lado = Math.min(50, Math.abs(dif) * 2.5); // 50% da trilha = 20 pontos
    dv.setAttribute('aria-label', 'Diferença de ' + nf(Math.abs(dif), 2) + ' pontos nos votos nominais somados');
    var seg = el('span', 'lado ' + (dif >= 0 ? 'f' : 'l'));
    seg.style.width = lado + '%';
    if (dif >= 0) seg.style.left = '50%'; else seg.style.right = '50%';
    dv.appendChild(seg);
    dv.appendChild(el('span', 'zero'));
    c.appendChild(dv);
    var esc = el('div', 'escala');
    esc.appendChild(el('span', '', 'Lula +20 pp'));
    esc.appendChild(el('span', '', '0'));
    esc.appendChild(el('span', '', 'Flávio +20 pp'));
    c.appendChild(esc);

    var quem = dif === 0 ? 'Flávio e Lula iguais na soma dos BUs recebidos' : (dif > 0 ? 'Flávio' : 'Lula') + ' com ' + nf(Math.abs(dif), 2) + ' pontos a mais que ' + (dif > 0 ? 'Lula' : 'Flávio') + ' na soma dos BUs recebidos';
    c.appendChild(el('p', 'dif', 'Diferença: ' + quem + '.'));
    if (outros > 0) c.appendChild(el('p', 'outros', 'Outros códigos: ' + nf(outros) + ' votos (' + nf(outros / p.total * 100, 2) + '%). Votos nominais: ' + nf(p.total) + '.'));
    else c.appendChild(el('p', 'outros', 'Votos nominais somados: ' + nf(p.total) + '.'));
    var pctApt = t.aptos ? t.aptosCom / t.aptos * 100 : 0;
    c.appendChild(el('p', 'cob-linha', 'Cobertura: ' + nf(pctApt, 2) + '% dos aptos do país (' + nf(t.aptosCom) + ' de ' + nf(t.aptos) + '). A amostra é de quem enviou, não é aleatória.'));
    box.appendChild(c);
  }

  /* ---------- tabelas ---------- */
  function cabecalho(cols, chave) {
    var thead = el('thead'), tr = el('tr');
    cols.forEach(function (c) {
      var th = el('th', c.num ? 'num' : '');
      th.scope = 'col';
      if (chave) {
        var btn = el('button', '', c.rot);
        btn.type = 'button';
        btn.addEventListener('click', function () {
          var o = ordem[chave];
          o.dir = o.col === c.id ? -o.dir : (c.num ? -1 : 1);
          o.col = c.id;
          if (chave === 'cob') renderCobertura(); else renderConflitos();
        });
        th.appendChild(btn);
        th.setAttribute('aria-sort', ordem[chave].col === c.id ? (ordem[chave].dir > 0 ? 'ascending' : 'descending') : 'none');
      } else th.textContent = c.rot;
      tr.appendChild(th);
    });
    thead.appendChild(tr);
    return thead;
  }
  function ordenar(arr, o) {
    return arr.slice().sort(function (a, b) {
      var x = a[o.col], y = b[o.col];
      if (typeof x === 'string') return o.dir * x.localeCompare(y, 'pt-BR');
      return o.dir * (num(x) - num(y)) || String(a.uf).localeCompare(String(b.uf));
    });
  }
  function celula(tr, txt, cls) { var td = el('td', cls || '', txt); tr.appendChild(td); return td; }

  function renderCobertura() {
    var box = $('cob-corpo');
    box.textContent = '';
    if (!D.cobUf.length) { box.appendChild(vazio('Sem dados de cobertura carregados.')); return; }
    var rows = D.cobUf.map(function (r) {
      var total = num(r.secoes_total), com = num(r.secoes_com_bu);
      return {
        uf: uf(r.uf), com: com, total: total, pct: total ? com / total * 100 : 0,
        aptosPct: num(r.aptos_total) ? num(r.aptos_com_bu) / num(r.aptos_total) * 100 : 0, conf: num(r.secoes_em_conflito)
      };
    });
    var cols = [
      { id: 'uf', rot: 'UF' }, { id: 'com', rot: 'Seções com BU', num: true }, { id: 'total', rot: 'Total', num: true },
      { id: 'pct', rot: 'Cobertura', num: true }, { id: 'aptosPct', rot: 'Aptos cobertos', num: true }, { id: 'conf', rot: 'Conflitos', num: true }
    ];
    var t = el('table');
    t.appendChild(cabecalho(cols, 'cob'));
    var tb = el('tbody');
    ordenar(rows, ordem.cob).forEach(function (r) {
      var tr = el('tr');
      celula(tr, r.uf, 'uf');
      celula(tr, nf(r.com), 'num'); celula(tr, nf(r.total), 'num');
      var td = celula(tr, '', 'num');
      td.appendChild(el('span', '', nf(r.pct, 2) + '%'));
      var pg = el('span', 'prog'); var i = el('i'); i.style.width = Math.min(100, r.pct) + '%'; pg.appendChild(i);
      td.appendChild(pg);
      celula(tr, nf(r.aptosPct, 2) + '%', 'num');
      celula(tr, nf(r.conf), 'num');
      tb.appendChild(tr);
    });
    t.appendChild(tb);
    box.appendChild(t);
  }

  function agrupar(arr, cargo) {
    var m = {};
    arr.forEach(function (r) {
      if (String(r.cargo) !== cargo) return;
      var k = uf(r.uf);
      (m[k] = m[k] || {})[String(r.candidato)] = (m[k][String(r.candidato)] || 0) + num(r.votos);
    });
    return m;
  }
  function secoesUf(u) {
    var n = 0;
    D.cobUf.forEach(function (r) { if (uf(r.uf) === u) n = num(r.secoes_com_bu); });
    return n;
  }

  function renderPorUf() {
    var box = $('uf-pres');
    box.textContent = '';
    var m = agrupar(D.uf, '1');
    var ufs = Object.keys(m).sort();
    if (!ufs.length) box.appendChild(vazio('Nenhum BU recebido ainda.'));
    else {
      var t = el('table');
      t.appendChild(cabecalho([{ rot: 'UF' }, { rot: nomeCand('br', 1, 22, true), num: true }, { rot: nomeCand('br', 1, 13, true), num: true }, { rot: 'Outros', num: true }, { rot: 'Flávio × Lula' }, { rot: 'Diferença', num: true }, { rot: 'Seções', num: true }]));
      var tb = el('tbody');
      ufs.forEach(function (u) {
        var v = m[u], tot = 0; Object.keys(v).forEach(function (k) { tot += v[k]; });
        var f = num(v['22']), l = num(v['13']), pf = tot ? f / tot * 100 : 0, pl = tot ? l / tot * 100 : 0, dif = pf - pl;
        var tr = el('tr');
        celula(tr, u, 'uf');
        celula(tr, nf(pf, 1) + '%', 'num'); celula(tr, nf(pl, 1) + '%', 'num');
        celula(tr, nf(tot ? (tot - f - l) / tot * 100 : 0, 1) + '%', 'num');
        var td = celula(tr, '');
        var mini = el('span', 'mini');
        var a = el('i', 'f'); a.style.width = pf / 2 + '%';
        var b = el('i', 'l'); b.style.width = pl / 2 + '%';
        mini.appendChild(a); mini.appendChild(b); td.appendChild(mini);
        celula(tr, (dif > 0 ? 'F +' : dif < 0 ? 'L +' : '') + nf(Math.abs(dif), 1) + ' pp', 'num');
        celula(tr, nf(secoesUf(u)), 'num');
        tb.appendChild(tr);
      });
      t.appendChild(tb);
      box.appendChild(t);
    }

    var g = agrupar(D.uf, '3');
    var gufs = Object.keys(g).sort();
    var gbox = $('uf-gov');
    gbox.textContent = '';
    $('uf-gov-bloco').hidden = !gufs.length;
    if (!gufs.length) return;
    var t2 = el('table');
    t2.appendChild(cabecalho([{ rot: 'UF' }, { rot: 'Candidatos por número e votos' }, { rot: 'Votos nominais', num: true }, { rot: 'Seções', num: true }]));
    var tb2 = el('tbody');
    gufs.forEach(function (u) {
      var v = g[u], tot = 0; Object.keys(v).forEach(function (k) { tot += v[k]; });
      var tr = el('tr');
      celula(tr, u, 'uf');
      var txt = Object.keys(v).sort(function (a, b) { return v[b] - v[a]; }).map(function (k) {
        var nm = nomeCand(u, 3, k);
        return (nm === String(k) ? 'Nº ' + k : nm + ' (nº ' + k + ')') + ': ' + nf(tot ? v[k] / tot * 100 : 0, 1) + '% (' + nf(v[k]) + ')';
      }).join(' · ');
      celula(tr, txt);
      celula(tr, nf(tot), 'num'); celula(tr, nf(secoesUf(u)), 'num');
      tb2.appendChild(tr);
    });
    t2.appendChild(tb2);
    gbox.appendChild(t2);
  }

  function renderConflitos() {
    var box = $('conf-corpo');
    box.textContent = '';
    if (!D.conf.length) { box.appendChild(vazio('Nenhuma seção em conflito.')); return; }
    var rows = D.conf.map(function (r) {
      return { uf: uf(r.uf), muni: num(r.muni), zona: num(r.zona), secao: num(r.secao), n: num(r.n_bus) };
    });
    var cols = [{ id: 'uf', rot: 'UF' }, { id: 'muni', rot: 'Município (código)', num: true }, { id: 'zona', rot: 'Zona', num: true },
      { id: 'secao', rot: 'Seção', num: true }, { id: 'n', rot: 'BUs diferentes', num: true }];
    var t = el('table');
    t.appendChild(cabecalho(cols, 'conf'));
    var tb = el('tbody');
    ordenar(rows, ordem.conf).forEach(function (r) {
      var tr = el('tr');
      celula(tr, r.uf, 'uf'); celula(tr, String(r.muni), 'num'); celula(tr, String(r.zona), 'num');
      celula(tr, String(r.secao), 'num'); celula(tr, String(r.n), 'num');
      tb.appendChild(tr);
    });
    t.appendChild(tb);
    box.appendChild(t);
  }

  function renderTse() {
    var f = $('tse-ficha'), box = $('tse-corpo');
    f.textContent = ''; box.textContent = '';
    function item(rot, valor, cls) {
      var d = el('div'); d.appendChild(el('dt', '', rot));
      d.appendChild(el('dd', cls || '', valor)); f.appendChild(d);
    }
    var t = D.tse, r = t && t.resumo;
    if (!r) {
      item('Estado', 'Conferência ainda não gerada.');
      box.appendChild(vazio('Nenhuma seção conferida ainda.'));
      return;
    }
    var oficiais = num(r.aceitos) - num(r.fora_do_oficial);
    item('BUs aceitos na fase oficial', nf(oficiais));
    item('Com BU publicado pelo TSE', nf(r.conferidos));
    item('Batem', nf(r.iguais), num(r.iguais) ? 'ok' : '');
    item('Divergem', nf(r.divergentes), num(r.divergentes) ? 'quebra' : 'ok');
    item('TSE ainda não publicou', nf(r.nao_publicados));
    if (num(r.erros)) item('Erros de consulta', nf(r.erros), 'quebra');
    item('Conferido em', hora(t.gerado_em));
    var linhasDiv = [];
    (t.secoes || []).forEach(function (s) {
      if (s.situacao !== 'divergente') return;
      (s.diferencas || []).forEach(function (d) {
        linhasDiv.push({ uf: uf(s.uf), muni: num(s.muni), zona: num(s.zona), secao: num(s.secao), campo: d.campo,
          cargo: d.cargo === null || d.cargo === undefined ? '' : String(d.cargo), chave: d.chave === null || d.chave === undefined ? '' : String(d.chave),
          qr: d.qr === null || d.qr === undefined ? '' : String(d.qr), tse: d.tse === null || d.tse === undefined ? '' : String(d.tse) });
      });
    });
    if (!num(r.conferidos)) { box.appendChild(vazio('Nenhuma seção conferida ainda: o TSE publica o BU da seção depois de totalizá-la.')); return; }
    if (!linhasDiv.length) { box.appendChild(vazio('Nenhuma divergência: todos os BUs conferidos batem com o publicado.')); return; }
    var cols = [{ id: 'uf', rot: 'UF' }, { id: 'muni', rot: 'Município', num: true }, { id: 'zona', rot: 'Zona', num: true }, { id: 'secao', rot: 'Seção', num: true },
      { id: 'campo', rot: 'Campo' }, { id: 'cargo', rot: 'Cargo' }, { id: 'chave', rot: 'Número' }, { id: 'qr', rot: 'QR impresso' }, { id: 'tse', rot: 'TSE' }];
    var tab = el('table');
    var thead = el('thead'), trh = el('tr');
    cols.forEach(function (c) { trh.appendChild(el('th', c.num ? 'num' : '', c.rot)); });
    thead.appendChild(trh); tab.appendChild(thead);
    var tb = el('tbody');
    linhasDiv.forEach(function (l) {
      var tr = el('tr');
      celula(tr, l.uf, 'uf'); celula(tr, String(l.muni), 'num'); celula(tr, String(l.zona), 'num'); celula(tr, String(l.secao), 'num');
      celula(tr, l.campo); celula(tr, l.cargo); celula(tr, l.chave); celula(tr, l.qr, 'num'); celula(tr, l.tse, 'num');
      tb.appendChild(tr);
    });
    tab.appendChild(tb);
    box.appendChild(tab);
  }

  function renderIntegridade() {
    var f = $('int-ficha');
    f.textContent = '';
    var mf = D.manifest, cad = mf && mf.cadeia;
    function item(rot, valor, cls) {
      var d = el('div'); d.appendChild(el('dt', '', rot));
      d.appendChild(el('dd', cls || '', valor)); f.appendChild(d);
    }
    if (cad) {
      var integra = cad.cadeia_integra !== false && !(cad.quebras && cad.quebras.length);
      item('Cadeia de hashes', integra ? 'Íntegra' : 'Quebrada em ' + (cad.quebras || []).length + ' elo(s)', integra ? 'ok' : 'quebra');
      item('BUs na cadeia', nf(cad.bus));
      item('Último elo', cad.ultimo_elo ? String(cad.ultimo_elo).slice(0, 12) + '…' : 'nenhum BU ainda');
    } else item('Cadeia de hashes', 'Manifesto não carregado.', 'quebra');
    item('Arquivos gerados em', hora(mf ? mf.gerado_em : meta.gerado));
    item('Último envio', hora(D.est && D.est.ultimo_envio));
    if (D.est && D.est.envios !== undefined) {
      item('Envios', nf(D.est.envios) + ' (aceitos ' + nf(D.est.envios_aceitos) + ', rejeitados ' + nf(D.est.envios_rejeitados) + ')');
    }

    if (mf && mf.arquivos) {
      var ul = el('ul', 'arquivos');
      Object.keys(mf.arquivos).sort().forEach(function (nome) {
        var li = el('li');
        var a = el('a', '', nome); a.href = DADOS + nome;
        li.appendChild(a);
        li.appendChild(document.createTextNode(' · ' + nf(mf.arquivos[nome].bytes) + ' bytes'));
        li.appendChild(el('span', 'h', 'SHA-256 ' + mf.arquivos[nome].sha256));
        ul.appendChild(li);
      });
      var box = $('int-arquivos');
      box.textContent = '';
      box.appendChild(ul);
    }
  }

  function renderTudo() {
    renderHero(); renderPlacar(); renderCobertura(); renderPorUf(); renderTse(); renderConflitos(); renderIntegridade();
  }

  /* ---------- carga ---------- */
  function buscar(url, opts) {
    var ctl = new AbortController();
    var timer = setTimeout(function () { ctl.abort(); }, 20000);
    opts = opts || {};
    opts.signal = ctl.signal;
    return fetch(url, opts).then(function (r) {
      clearTimeout(timer);
      if (!r.ok) throw new Error('HTTP ' + r.status + ' em ' + url.split('?')[0]);
      return r.json();
    }, function (e) { clearTimeout(timer); throw e; });
  }

  function carregarEstatico() {
    var chaves = Object.keys(ESTATICOS);
    return Promise.all(chaves.map(function (k) {
      return buscar(DADOS + ESTATICOS[k], { cache: 'no-cache' }).then(function (j) { return [k, j]; });
    })).then(function (res) {
      var g = null;
      res.forEach(function (p) {
        var k = p[0], j = p[1];
        if (k === 'manifest') D.manifest = j;
        else if (k === 'est') D.est = linhas(j)[0] || {};
        else D[k] = linhas(j);
        if (j && j.gerado_em && (!g || j.gerado_em < g)) g = j.gerado_em;
      });
      meta.gerado = g; meta.origem = 'arquivos estáticos';
    }).then(function () {
      return buscar(DADOS + 'candidatos_2t.json', { cache: 'no-cache' }).then(function (j) {
        CANDS = j && Array.isArray(j.candidatos) ? j.candidatos : [];
      }, function () { CANDS = []; });
    }).then(function () {
      return buscar(DADOS + 'conferencia_tse.json', { cache: 'no-cache' }).then(function (j) {
        D.tse = j && j.resumo ? j : null;
      }, function () { D.tse = null; });
    });
  }

  var EM_CURSO = false;
  function atualizarAoVivo(auto) {
    if (EM_CURSO) return;
    auto = auto === true;
    var btn = $('btn-atualiza'), msg = $('atualiza-msg');
    EM_CURSO = true;
    btn.disabled = true; msg.textContent = 'Consultando o banco…';
    var h = { apikey: CHAVE, Authorization: 'Bearer ' + CHAVE, Accept: 'application/json' };
    var chaves = Object.keys(VIVAS);
    Promise.all(chaves.map(function (k) {
      return buscar(API + VIVAS[k] + '?select=*', { headers: h }).then(function (j) { return [k, j]; });
    })).then(function (res) {
      res.forEach(function (p) {
        if (p[0] === 'est') D.est = Array.isArray(p[1]) ? (p[1][0] || {}) : {};
        else D[p[0]] = Array.isArray(p[1]) ? p[1] : [];
      });
      meta.gerado = new Date().toISOString(); meta.origem = 'ao vivo (views públicas)';
      limparAvisos();
      renderTudo();
      $('atualiza-msg').textContent = 'Atualizado às ' + hora(meta.gerado) + ' (renova sozinho a cada 30 s). Município por município segue nos arquivos estáticos.';
      $('btn-atualiza').disabled = false;
      EM_CURSO = false;
    }).catch(function (e) {
      if (!auto) aviso('Não foi possível ler o banco ao vivo (' + e.message + '). Os números abaixo continuam sendo os dos arquivos estáticos.', true);
      $('atualiza-msg').textContent = 'Falhou. Tente de novo em instantes.';
      $('btn-atualiza').disabled = false;
      EM_CURSO = false;
    });
  }

  function acompanharAoVivo() {
    atualizarAoVivo(true);
    setInterval(function () { if (!document.hidden) atualizarAoVivo(true); }, 30000);
    document.addEventListener('visibilitychange', function () { if (!document.hidden) atualizarAoVivo(true); });
  }

  function iniciar() {
    carregarEstatico().then(renderTudo).then(acompanharAoVivo).catch(function (e) {
      aviso('Não foi possível carregar os arquivos de dados (' + e.message + '). Abra a página por um servidor, não por arquivo do disco.', true);
      renderTudo();
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar); else iniciar();
})();
