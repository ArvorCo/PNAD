// Mapa de fiscais: aplicativo estático escrito à mão, sem build.
// Lê o formato 2 de scripts/fiscais-mapa-build.py: locais numa tabela, seções noutra.
// Abre com o país inteiro e todos os níveis; carrega a UF escolhida sob demanda, e o
// destaque nacional (capítulo 13 e logs com atenção 2 ou 3) quando os níveis de rotina e
// de um sinal estão desligados. CEP, zonas e municípios vêm de índices separados.
// Distância em linha reta pela fórmula inversa de Vincenty no elipsoide WGS84.
(function () {
  'use strict';

  const BASE = 'assets/fiscais_mapa/';
  const POLITIZE = 'assets/politize/dados/';
  const VERSAO = '20261024-clima-horario';
  const RAIOS = [1, 2, 5, 10, 15, 20, 30, 50];
  const RAIO_PADRAO = 10;
  // Chaves de nível na ordem de prioridade: histórico do capítulo 13 primeiro, depois a atenção dos logs.
  const NIVEIS = ['alta', 'media', 'baixa', 'log3', 'log2', 'log1', 'log0', 'mudanca'];
  // Abertura com todos os níveis, inclusive os registros de rotina: o mapa não esconde sinal nenhum.
  const PADRAO_NIVEIS = NIVEIS.slice();
  const PESO = { alta: 7, media: 6, baixa: 5, log3: 4, log2: 3, log1: 2, mudanca: 1.5, log0: 1 };
  const NOME_NIVEL = { alta: 'Prioridade alta', media: 'Prioridade média', baixa: 'Prioridade baixa', log3: 'Conferir o arquivo', log2: 'Sinais combinados', log1: 'Um sinal no log', log0: 'Registro de rotina', mudanca: 'Mudou de endereço' };
  const NOME_RISCO = { alto: 'alto', medio: 'médio', baixo: 'baixo' };
  const CRIT_MUDANCA = 'mudanca_endereco';
  const LIMITE_CHUVA_FORTE = 20; // mm no dia 04/10
  const CONFERIR_MUDANCA = 'confirme no e-Título onde a seção vota em 25/10 antes de sair de casa, porque o endereço pode ter mudado entre os turnos';
  const NOME_FONTE_MUDANCA = { ambos: 'o arquivo de locais e o painel do TSE concordam', so_zip: 'só o arquivo de locais do TSE mostra a mudança', so_painel: 'só o painel de seções alteradas do TSE mostra a mudança' };
  const UFS = { AC: 'Acre', AL: 'Alagoas', AP: 'Amapá', AM: 'Amazonas', BA: 'Bahia', CE: 'Ceará', DF: 'Distrito Federal', ES: 'Espírito Santo', GO: 'Goiás', MA: 'Maranhão', MT: 'Mato Grosso', MS: 'Mato Grosso do Sul', MG: 'Minas Gerais', PA: 'Pará', PB: 'Paraíba', PR: 'Paraná', PE: 'Pernambuco', PI: 'Piauí', RJ: 'Rio de Janeiro', RN: 'Rio Grande do Norte', RS: 'Rio Grande do Sul', RO: 'Rondônia', RR: 'Roraima', SC: 'Santa Catarina', SP: 'São Paulo', SE: 'Sergipe', TO: 'Tocantins', ZZ: 'Exterior' };
  const COLS_LISTA = [
    ['nivel', 'Nível'], ['uf', 'UF'], ['municipio', 'Município'], ['zona', 'Zona'], ['secao', 'Seção'],
    ['local', 'Local de votação'], ['votaram', 'Votaram'], ['placar', 'Flávio × Lula'],
    ['motivos', 'Por que está no mapa'], ['risco', 'Risco do território'], ['mudanca', 'Mudou de endereço'], ['dist', 'Distância'], ['coord', 'Mapa'],
  ];
  const COL_CHUVA = ['chuva', 'Chuva em 04/10'];
  const COL_RISCO25 = ['risco25', 'Risco climático 25/10'];
  const ZOOM_ROTULOS = 15;
  const MAX_ROTULO = 5;

  const S = {
    meta: null, locais: [], secoes: [], recorte: '',
    filtro: { uf: '', mun: '', zona: '', cep: '', texto: '', camada: 'todas', log: '', risco25: '', choveu: false, niveis: new Set(PADRAO_NIVEIS) },
    clima: { prev: undefined, ufs: new Map() },
    raio: RAIO_PADRAO, modo: 'mapa', centro: null, abrir: '',
    ordem: { col: 'nivel', dir: 1 }, pagina: 1, porPagina: 50, buscaLista: '',
    mapa: null, cluster: null, circulo: null, alvo: null, marcadores: new Map(),
    cache: new Map(), zonas: null, requisicao: 0, desenho: 0, loteMapa: null, listaAtual: [], locaisPorId: new Map(), aberto: null, listaRaio: true,
  };

  const $ = (s, r) => (r || document).querySelector(s);
  const nf1 = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  const nf0 = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 });
  const pct = (v) => (v === null || v === undefined ? '' : nf1.format(v).replace(',0', '') + '%');

  function h(tag, attrs) {
    const n = document.createElement(tag);
    const a = attrs || {};
    Object.keys(a).forEach((k) => {
      const v = a[k];
      if (v === null || v === undefined || v === false) return;
      if (k === 'class') n.className = v;
      else if (k === 'text') n.textContent = v;
      else if (k.indexOf('on') === 0 && typeof v === 'function') n.addEventListener(k.slice(2), v);
      else n.setAttribute(k, v === true ? '' : String(v));
    });
    for (let i = 2; i < arguments.length; i++) anexar(n, arguments[i]);
    return n;
  }
  function anexar(n, f) {
    if (f === null || f === undefined || f === false || f === '') return;
    if (Array.isArray(f)) { f.forEach((x) => anexar(n, x)); return; }
    n.appendChild(f instanceof Node ? f : document.createTextNode(String(f)));
  }
  const norm = (s) => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/\s+/g, ' ').trim();
  const so = (s) => String(s || '').replace(/\D/g, '');
  const cepFmt = (c) => { const d = so(c); return d.length === 8 ? d.slice(0, 5) + '-' + d.slice(5) : d; };
  const SIGLAS = new Set(['EE', 'EEF', 'EEE', 'EEEF', 'EEEFM', 'EEFM', 'EEM', 'EM', 'EMEF', 'EMEI', 'EMEB', 'EMEIEF', 'CEU', 'CIEP', 'CAIC', 'CEI', 'CMEI', 'CEF', 'CED', 'CE', 'ETEC', 'FATEC', 'SESC', 'SESI', 'SENAI', 'SENAC', 'IFAC', 'UFAC', 'IBGE', 'UF', 'II', 'III', 'IV', 'VI', 'VII', 'VIII', 'IX', 'XI', 'XII', 'BR', 'SP', 'RJ', 'MG', 'PUC', 'USP', 'UNESP', 'UFRJ', 'UFMG', 'APAE', 'CRAS', 'CSU', 'UBS', 'ESF']);
  const MINUSC = new Set(['de', 'da', 'do', 'das', 'dos', 'e', 'em', 'na', 'no', 'nas', 'nos', 'a', 'o', 'para', 'com', 'por']);
  function caixa(s) {
    return String(s || '').split(/(\s+|[(/.,-])/).map((p, i) => {
      const limpa = p.replace(/[^A-Za-zÀ-ú0-9]/g, '');
      if (!limpa) return p;
      const up = limpa.toUpperCase();
      if (SIGLAS.has(up) || (/^[A-Z]{2,5}$/.test(up) && !/[AEIOU]/.test(up))) return p.toUpperCase();
      const low = p.toLowerCase();
      if (i > 0 && MINUSC.has(low)) return low;
      return low.charAt(0).toUpperCase() + low.slice(1);
    }).join('');
  }
  const maiuscula = (t) => (t ? t.charAt(0).toUpperCase() + t.slice(1) : t);
  const km = (v) => (v === null || v === undefined ? '' : (v < 10 ? nf1.format(v) : nf0.format(v)) + ' km');
  const plural = (n, um, varios) => nf0.format(n) + ' ' + (n === 1 ? um : varios);

  function buscar(url) {
    if (url.indexOf(BASE) === 0 || url.indexOf(POLITIZE) === 0) url += (url.indexOf('?') < 0 ? '?' : '&') + 'v=' + VERSAO;
    if (S.cache.has(url)) return S.cache.get(url);
    const p = fetch(url, { credentials: 'same-origin' }).then((r) => {
      if (!r.ok) { const e = new Error('HTTP ' + r.status); e.status = r.status; throw e; }
      return r.json();
    });
    p.catch(() => S.cache.delete(url));
    S.cache.set(url, p);
    return p;
  }

  /* ------------------------------------------------------------ geodésia */

  // Fórmula inversa de Vincenty no elipsoide WGS84; distância em km. Se não convergir
  // (pontos quase antípodas, impossível dentro do Brasil), usa o grande círculo.
  function distanciaKm(lat1, lon1, lat2, lon2) {
    const a = 6378137, f = 1 / 298.257223563, b = a * (1 - f);
    const rad = Math.PI / 180;
    const L = (lon2 - lon1) * rad;
    const U1 = Math.atan((1 - f) * Math.tan(lat1 * rad));
    const U2 = Math.atan((1 - f) * Math.tan(lat2 * rad));
    const sinU1 = Math.sin(U1), cosU1 = Math.cos(U1), sinU2 = Math.sin(U2), cosU2 = Math.cos(U2);
    let lambda = L, it = 0, sinS, cosS, sigma, sinAlpha, cos2Alpha, cos2SigmaM, lambdaP;
    do {
      const sinL = Math.sin(lambda), cosL = Math.cos(lambda);
      sinS = Math.sqrt(Math.pow(cosU2 * sinL, 2) + Math.pow(cosU1 * sinU2 - sinU1 * cosU2 * cosL, 2));
      if (sinS === 0) return 0;
      cosS = sinU1 * sinU2 + cosU1 * cosU2 * cosL;
      sigma = Math.atan2(sinS, cosS);
      sinAlpha = cosU1 * cosU2 * sinL / sinS;
      cos2Alpha = 1 - sinAlpha * sinAlpha;
      cos2SigmaM = cos2Alpha !== 0 ? cosS - 2 * sinU1 * sinU2 / cos2Alpha : 0;
      const C = f / 16 * cos2Alpha * (4 + f * (4 - 3 * cos2Alpha));
      lambdaP = lambda;
      lambda = L + (1 - C) * f * sinAlpha * (sigma + C * sinS * (cos2SigmaM + C * cosS * (-1 + 2 * cos2SigmaM * cos2SigmaM)));
    } while (Math.abs(lambda - lambdaP) > 1e-12 && ++it < 200);
    if (it >= 200) return haversineKm(lat1, lon1, lat2, lon2);
    const u2 = cos2Alpha * (a * a - b * b) / (b * b);
    const A = 1 + u2 / 16384 * (4096 + u2 * (-768 + u2 * (320 - 175 * u2)));
    const B = u2 / 1024 * (256 + u2 * (-128 + u2 * (74 - 47 * u2)));
    const dS = B * sinS * (cos2SigmaM + B / 4 * (cosS * (-1 + 2 * cos2SigmaM * cos2SigmaM) - B / 6 * cos2SigmaM * (-3 + 4 * sinS * sinS) * (-3 + 4 * cos2SigmaM * cos2SigmaM)));
    return b * A * (sigma - dS) / 1000;
  }
  function haversineKm(lat1, lon1, lat2, lon2) {
    const rad = Math.PI / 180, dp = (lat2 - lat1) * rad, dl = (lon2 - lon1) * rad;
    const x = Math.pow(Math.sin(dp / 2), 2) + Math.cos(lat1 * rad) * Math.cos(lat2 * rad) * Math.pow(Math.sin(dl / 2), 2);
    return 2 * 6371.0088 * Math.asin(Math.min(1, Math.sqrt(x)));
  }
  const coordOk = (r) => typeof r.lat === 'number' && typeof r.lon === 'number' && isFinite(r.lat) && isFinite(r.lon);

  /* ------------------------------------------------------------ clima */

  // Chave da célula de 0,5 grau da previsão: "<floor(lat*2)/2>,<floor(lon*2)/2>", sempre com uma casa decimal.
  const chaveCelula = (lat, lon) => (Math.floor(lat * 2) / 2 + 0).toFixed(1) + ',' + (Math.floor(lon * 2) / 2 + 0).toFixed(1);
  const id1tDe = (s) => (s.mudanca && s.mudanca.id_1t ? s.mudanca.id_1t : s.local.id);

  // Falha ou 404 viram "sem dado": o clima nunca bloqueia o mapa.
  function carregarPrevisao() {
    if (!S.clima.prevPromessa) {
      S.clima.prevPromessa = buscar(BASE + 'clima/previsao.json')
        .then((d) => { S.clima.prev = d && d.celulas ? d : null; return S.clima.prev; })
        .catch(() => { S.clima.prev = null; return null; });
    }
    return S.clima.prevPromessa;
  }

  function carregarClimaUf(uf) {
    if (!uf || uf === 'ZZ') return Promise.resolve(null);
    if (!S.clima.ufs.has(uf)) {
      S.clima.ufs.set(uf, buscar(BASE + 'clima/' + uf + '.json').then((d) => {
        const cols = d.colunas;
        return { gerado_em: d.gerado_em, fonte: d.fonte, linhas: new Map(d.linhas.map((ln) => { const r = {}; cols.forEach((c, i) => { r[c] = ln[i]; }); return [r.local_id, r]; })) };
      }).catch(() => null));
    }
    return S.clima.ufs.get(uf);
  }

  const climaUfPronto = (uf) => S.clima.ufResolvidos && S.clima.ufResolvidos[uf];

  function passaRisco25(l, modo) {
    const p = S.clima.prev;
    if (!p || !coordOk(l)) return false;
    const c = p.celulas[chaveCelula(l.lat, l.lon)];
    return Boolean(c) && (c.risco === 'alto' || (modo === 'alto_medio' && c.risco === 'medio'));
  }

  function climaObservado(s) {
    const d = S.clima.ufResolvidos && S.clima.ufResolvidos[s.local.uf];
    return d ? d.linhas.get(id1tDe(s)) || null : null;
  }

  function passaChuvaForte(s) {
    const c = climaObservado(s);
    return Boolean(c) && typeof c.chuva_04_10_mm === 'number' && c.chuva_04_10_mm > LIMITE_CHUVA_FORTE;
  }

  function riscoPrevisto(l) {
    const p = S.clima.prev;
    if (!p || !coordOk(l)) return null;
    return p.celulas[chaveCelula(l.lat, l.lon)] || null;
  }

  // Carrega o que os filtros de clima pedem; sem o arquivo, o filtro se desliga e o mapa segue.
  async function prepararClima(f) {
    const avisos = [];
    if (f.risco25) {
      if (!await carregarPrevisao()) {
        f.risco25 = ''; $('#f-risco25').value = '';
        avisos.push('A previsão do tempo para 25/10 ainda não foi publicada; o filtro de risco climático ficou desligado.');
      }
    }
    if (f.choveu) {
      if (!f.uf) {
        f.choveu = false; $('#f-choveu').checked = false;
        avisos.push('Escolha o estado para filtrar por chuva forte no 1º turno: o arquivo de chuva é carregado por estado.');
      } else {
        const d = await carregarClimaUf(f.uf);
        if (d) registrarClimaUf(f.uf, d);
        else {
          f.choveu = false; $('#f-choveu').checked = false;
          avisos.push('Os dados de chuva de 04/10 para ' + (UFS[f.uf] || f.uf) + ' ainda não foram publicados; o filtro de chuva forte ficou desligado.');
        }
      }
    }
    $('#clima-aviso').hidden = !avisos.length;
    return avisos.join(' ') + (avisos.length ? ' ' : '');
  }

  function registrarClimaUf(uf, d) {
    if (!S.clima.ufResolvidos) S.clima.ufResolvidos = {};
    S.clima.ufResolvidos[uf] = d;
  }

  function formatarHora(v) {
    if (v === null || v === undefined || v === '') return '';
    if (typeof v === 'number') return v + 'h';
    const t = String(v);
    if (/^\d{1,2}$/.test(t)) return t + 'h';
    const m = t.match(/T(\d{2}):(\d{2})/);
    return m ? m[1] + 'h' + (m[2] === '00' ? '' : m[2]) : t;
  }

  function formatarCarimbo(iso) {
    if (!iso) return '';
    try { return new Date(iso).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short', timeZone: 'America/Sao_Paulo' }); } catch (e) { return String(iso); }
  }

  const mm = (v) => (typeof v === 'number' ? nf1.format(v) + ' mm' : 'sem dado');
  const kmh = (v) => (typeof v === 'number' ? nf0.format(v) + ' km/h' : 'sem dado');

  function blocoObservado(c, doPredioAntigo) {
    const NOME_FAIXA = { seca: 'seca', fraca: 'fraca', moderada: 'moderada', forte: 'forte', muito_forte: 'muito forte', ate_40: 'até 40 km/h', '40_60': '40 a 60 km/h', '60_80': '60 a 80 km/h', acima_80: 'acima de 80 km/h' };
    const faixa = (v) => (typeof v === 'string' && v ? ' (' + (NOME_FAIXA[v] || v.replace(/_/g, ' ')) + ')' : '');
    const itens = [
      h('li', {}, 'Chuva no dia: ' + mm(c.chuva_04_10_mm) + faixa(c.faixa_chuva) + '; nas horas de votação: ' + mm(c.chuva_votacao_mm) + (c.hora_pico_chuva ? '; pico por volta das ' + formatarHora(c.hora_pico_chuva) : '') + '.'),
      h('li', {}, 'Rajada de vento: ' + kmh(c.rajada_04_10_kmh) + ' no dia' + faixa(c.faixa_rajada) + '; ' + kmh(c.rajada_votacao_kmh) + ' nas horas de votação.'),
    ];
    if (typeof c.urnas === 'number' && c.urnas > 0) {
      itens.push(h('li', {}, nf0.format(c.urnas_bateria || 0) + ' de ' + plural(c.urnas, 'urna', 'urnas') + ' do prédio passaram para a bateria, ' + nf0.format(c.urnas_bateria_votacao || 0) + ' durante a votação.'));
    }
    if (typeof c.abst_pct === 'number') {
      const dif = typeof c.dif_abst_pp === 'number' ? ' (' + (c.dif_abst_pp > 0 ? '+' : '') + nf1.format(c.dif_abst_pp) + ' pontos)' : '';
      itens.push(h('li', {}, 'Abstenção de ' + pct(c.abst_pct) + (typeof c.abst22_pct === 'number' ? ', contra ' + pct(c.abst22_pct) + ' no 2º turno de 2022 (mesma seção)' : '') + dif + '.'));
    }
    return h('div', { class: 'ficha-clima-bloco' },
      h('b', {}, 'No dia do 1º turno (04/10)' + (doPredioAntigo ? ', no prédio onde estas seções votaram' : '')),
      h('ul', {}, itens),
      h('p', { class: 'ficha-meta' }, 'Valor da grade de 0,25 grau (fonte Open-Meteo), não medido no prédio. Chuva não prova efeito no comparecimento.'));
  }

  function blocoPrevisao(cel, prev) {
    const regra = prev.regra_risco;
    const textoRegra = !regra ? '' : typeof regra === 'string' ? regra : Object.keys(regra).map((k) => k.replace(/_/g, ' ') + ': ' + (typeof regra[k] === 'object' ? JSON.stringify(regra[k]) : regra[k])).join('; ');
    return h('div', { class: 'ficha-clima-bloco' },
      h('b', {}, 'Previsão para 25/10 · 8h–17h de Brasília'),
      h('ul', {},
        h('li', {}, 'Chuva acumulada na votação: ' + mm(cel.chuva_mm) + (typeof cel.prob_pct === 'number' ? '; maior probabilidade horária de ' + nf0.format(cel.prob_pct) + '%' : '') + '.'),
        h('li', {}, 'Rajada máxima na votação: ' + kmh(cel.rajada_kmh) + '.'),
        h('li', { class: 'risco-' + (cel.risco || 'baixo') }, h('b', {}, 'Risco climático previsto: ' + (NOME_RISCO[cel.risco] || cel.risco || 'sem dado') + '.'))),
      cel.periodos ? h('ul', {}, Object.entries(cel.periodos).filter(([k]) => k !== 'votacao').map(([, p]) => h('li', {}, p.nome + ' (' + p.inicio_brasilia + 'h–' + p.fim_brasilia + 'h Brasília): ' + mm(p.chuva_mm) + '; rajada máxima ' + kmh(p.rajada_kmh) + '.'))) : null,
      h('p', { class: 'ficha-meta' }, 'A probabilidade indicada é o máximo horário, não a probabilidade de chover no período inteiro. Previsão de modelo global, muda todo dia; indicativo de atenção, não previsão do prédio.' + (prev.gerado_em ? ' Gerada em ' + formatarCarimbo(prev.gerado_em) + '.' : '')),
      textoRegra ? h('details', {}, h('summary', {}, 'Como o risco é calculado'), h('p', { class: 'ficha-meta' }, textoRegra)) : null);
  }

  async function preencherClima(l, el) {
    const alvo = el && el.querySelector('.ficha-clima');
    if (!alvo) return;
    const movida = l.secoes.find((x) => x.mudanca && x.mudanca.id_1t && x.mudanca.id_1t !== l.id);
    const id1t = l.coord_fonte === 'local_2t' && movida ? movida.mudanca.id_1t : l.id;
    const res = await Promise.all([carregarPrevisao(), carregarClimaUf(l.uf)]);
    const prev = res[0], ufd = res[1];
    if (ufd) registrarClimaUf(l.uf, ufd);
    const c = ufd ? ufd.linhas.get(id1t) : null;
    const cel = prev ? riscoPrevisto(l) : null;
    const blocos = [c ? blocoObservado(c, l.coord_fonte === 'local_2t') : null, cel ? blocoPrevisao(cel, prev) : null].filter(Boolean);
    if (blocos.length) alvo.replaceChildren(...blocos); else alvo.remove();
  }

  /* ------------------------------------------------------------ dados */

  const chaveNivel = (s) => (s.nivel === 'logs' ? 'log' + (s.atencao === null || s.atencao === undefined ? 0 : s.atencao) : s.nivel);

  function preparar(d) {
    const m = S.meta;
    S.marcadores.clear();
    limparMarcadores();
    S.locais = d.locais.map((ln, i) => {
      const l = { i };
      m.colunas_locais.forEach((c, j) => { l[c] = ln[j]; });
      l.secoes = [];
      return l;
    });
    S.locaisPorId = new Map(S.locais.map((l) => [l.id, l]));
    S.destinoDoId1t = new Map();
    S.secoes = d.secoes.map((ln, i) => {
      const s = { i };
      m.colunas_secoes.forEach((c, j) => { s[c] = ln[j]; });
      const l = S.locais[s.li];
      s.local = l;
      s.uf = l.uf; s.zona = l.zona; s.municipio = l.municipio; s.mun = l.mun;
      s.chave = chaveNivel(s);
      s.crit = String(s.criterios || '').split('').filter(Boolean);
      s.critNomes = s.crit.map((c) => (m.criterios[c] && m.criterios[c].nome) || c);
      s.logs = s.logs || [];
      s.logNomes = s.logs.map((c) => ((m.logs && m.logs.criterios[c]) || {}).curto || c);
      s.familias = familiasDe(s.logs);
      s.mudanca = s.mudanca || null;
      if (s.mudanca && s.mudanca.id_1t && s.mudanca.id_1t !== l.id) {
        const lista = S.destinoDoId1t.get(s.mudanca.id_1t) || [];
        if (lista.indexOf(l) < 0) lista.push(l);
        S.destinoDoId1t.set(s.mudanca.id_1t, lista);
      }
      const mu = s.mudanca || {};
      s.busca = norm([l.local, l.endereco, l.bairro, l.municipio, l.uf, l.cep, s.explicacao, s.critNomes.join(' '), s.logNomes.join(' '), 'zona ' + l.zona, 'secao ' + s.secao, s.mudanca ? ['mudou de endereco', mu.nome_1t, mu.end_1t, mu.bairro_1t, mu.nome_cat].join(' ') : ''].join(' '));
      l.secoes.push(s);
      return s;
    });
  }

  function familiasDe(logs) {
    const fam = (S.meta.logs && S.meta.logs.familias) || {};
    return Object.keys(fam).filter((f) => fam[f].criterios.some((c) => logs.indexOf(c) >= 0));
  }

  // Que arquivo atende o filtro atual: a UF, o histórico sozinho, o destaque nacional ou o país inteiro.
  function arquivoDoRecorte() {
    const f = S.filtro;
    if (f.uf && S.meta.partes[f.uf]) return S.meta.partes[f.uf].arquivo;
    if (f.uf) return null;
    if (f.camada === 'originais' || (f.log && f.log.startsWith('historico:'))) return 'originais.json';
    if (f.log === CRIT_MUDANCA) return 'destaque.json';
    const precisaTudo = f.log || f.camada === 'logs' || f.niveis.has('log1') || f.niveis.has('log0');
    return precisaTudo ? 'dados.json' : 'destaque.json';
  }

  async function carregarRecorte(seq) {
    const arquivo = arquivoDoRecorte();
    if (arquivo === null) { preparar({ locais: [], secoes: [] }); S.recorte = ''; return true; }
    if (S.recorte === arquivo) return true;
    const f = S.filtro;
    setStatus(arquivo === 'dados.json' ? 'Carregando o país inteiro, todos os sinais (arquivo grande; escolha o estado para ir mais rápido)…' : 'Carregando ' + (f.uf ? UFS[f.uf] : arquivo === 'originais.json' ? 'as seções do capítulo 13' : 'o destaque nacional') + '…');
    const d = await buscar(BASE + arquivo);
    if (seq !== S.requisicao) return false;
    preparar(d);
    S.recorte = arquivo;
    return true;
  }

  function passaFiltro(s) {
    const f = S.filtro;
    const l = s.local;
    if (f.camada === 'originais' && (s.nivel === 'logs' || s.nivel === 'mudanca')) return false;
    if (f.camada === 'logs' && !s.logs.length) return false;
    if (f.log) {
      if (f.log === CRIT_MUDANCA) { if (!s.mudanca) return false; }
      else if (f.log.startsWith('historico:')) { if (s.crit.indexOf(f.log.slice(10)) < 0) return false; }
      else if (f.log.startsWith('familia:')) { if (s.familias.indexOf(f.log.slice(8)) < 0) return false; }
      else if (s.logs.indexOf(f.log) < 0) return false;
    } else if (!f.niveis.has(s.chave) && !(s.mudanca && f.niveis.has('mudanca'))) return false;
    if (f.risco25 && !passaRisco25(l, f.risco25)) return false;
    if (f.choveu && !passaChuvaForte(s)) return false;
    if (f.uf && l.uf !== f.uf) return false;
    if (f.mun && l.mun !== f.mun) return false;
    if (f.zona && Number(l.zona) !== Number(f.zona)) return false;
    if (f.texto) {
      const termos = norm(f.texto).split(' ');
      for (let i = 0; i < termos.length; i++) if (s.busca.indexOf(termos[i]) < 0) return false;
    }
    return true;
  }

  const filtradas = () => S.secoes.filter(passaFiltro);

  function comDistancia(rs) {
    rs.forEach((s) => { s.dist = S.centro && coordOk(s.local) ? distanciaKm(S.centro.lat, S.centro.lon, s.local.lat, s.local.lon) : null; });
    return rs;
  }

  /* ------------------------------------------------------------ busca */

  async function geocodificarCep(cep) {
    const arq = await buscar(BASE + 'cep/' + cep.slice(0, 2) + '.json').catch(() => null);
    if (arq && arq.exato && arq.exato[cep]) {
      const e = arq.exato[cep];
      return { lat: e[0], lon: e[1], rotulo: 'CEP ' + cepFmt(cep), precisao: e[2] === 1 ? 'o local de votação com este CEP' : 'os ' + e[2] + ' locais de votação com este CEP' };
    }
    const p5 = cep.slice(0, 5);
    if (arq && arq.p5 && arq.p5[p5]) {
      const q = arq.p5[p5];
      return { lat: q[0], lon: q[1], rotulo: 'CEP ' + cepFmt(cep), precisao: 'locais de votação com CEP começando em ' + p5 + ', nenhum com o CEP exato' };
    }
    if (arq && arq.p5) {
      let chaves = Object.keys(arq.p5).filter((k) => k.slice(0, 4) === cep.slice(0, 4));
      if (!chaves.length) chaves = Object.keys(arq.p5).filter((k) => k.slice(0, 3) === cep.slice(0, 3));
      if (chaves.length) {
        const alvo = Number(p5);
        chaves.sort((x, y) => Math.abs(Number(x) - alvo) - Math.abs(Number(y) - alvo));
        const g = arq.p5[chaves[0]];
        return { lat: g[0], lon: g[1], rotulo: 'CEP ' + cepFmt(cep), precisao: 'aproximação grossa pelo CEP de local de votação mais parecido (' + chaves[0] + '-…)' };
      }
    }
    return null;
  }

  async function centroZona(uf, zona) {
    if (uf === 'ZZ') return null; // A zona 1 abrange cidades em todo o mundo.
    if (!S.zonas) S.zonas = await buscar(BASE + 'zonas.json');
    const z = S.zonas[uf] && S.zonas[uf][String(Number(zona))];
    return z ? { lat: z[0], lon: z[1], rotulo: 'zona ' + Number(zona) + ' (' + uf + ')', precisao: 'centro dos ' + z[2] + ' locais de votação da zona' } : null;
  }

  async function aplicarBusca(rolar) {
    if (!S.meta) { setStatus('Carregando o índice de busca…'); return; }
    const seq = ++S.requisicao;
    const f = S.filtro;
    f.uf = $('#f-uf').value;
    f.camada = $('#f-camada').value;
    f.log = $('#f-log').value;
    f.risco25 = $('#f-risco25').value;
    f.choveu = $('#f-choveu').checked;
    f.mun = $('#f-mun').value;
    f.texto = $('#f-texto').value.trim();
    const zonaTxt = so($('#f-zona').value);
    const cep = f.uf === 'ZZ' ? '' : so($('#q-cep').value);
    if (zonaTxt && !f.uf) { setStatus('Escolha o estado para buscar a zona: o número da zona se repete entre os estados.', true); $('#f-uf').focus(); return; }
    if (cep && cep.length !== 8) { setStatus('O CEP precisa de 8 números.', true); $('#q-cep').focus(); return; }
    f.zona = zonaTxt ? String(Number(zonaTxt)) : '';
    f.cep = cep;
    let centro = null;
    try {
      if (!await carregarRecorte(seq)) return;
      const avisoClima = await prepararClima(f);
      if (seq !== S.requisicao) return;
      S.avisoLog = (S.avisoLog || '') + avisoClima;
      if (cep) {
        centro = await geocodificarCep(cep);
        if (seq !== S.requisicao) return;
        if (!centro) { setStatus('Nenhum local de votação tem CEP parecido com ' + cepFmt(cep) + '. Tente a zona ou a cidade.', true); return; }
      } else if (f.zona && f.uf !== 'ZZ') {
        centro = await centroZona(f.uf, f.zona);
        if (seq !== S.requisicao) return;
        if (!centro) { setStatus('A zona ' + f.zona + ' não aparece em ' + (UFS[f.uf] || f.uf) + ' nos dados. Confira o número no título de eleitor.', true); return; }
      }
    } catch (e) {
      console.error(e);
      if (seq !== S.requisicao) return;
      setStatus('Não foi possível carregar os dados agora. Tente de novo.', true);
      return;
    }
    if (seq !== S.requisicao) return;
    S.centro = centro;
    S.pagina = 1;
    if (centro && !S.ordemManual) S.ordem = { col: 'dist', dir: 1 };
    else if (!centro && !S.ordemManual) S.ordem = { col: 'nivel', dir: 1 };
    atualizar(true);
    if (window.innerWidth < 980 && rolar) $('#palco').scrollIntoView({ block: 'start', behavior: 'smooth' });
  }

  /* ------------------------------------------------------------ mapa */

  function iniciarMapa() {
    if (typeof L === 'undefined' || typeof L.markerClusterGroup !== 'function') {
      $('#mapa').replaceChildren(h('p', { class: 'aviso' }, 'A biblioteca do mapa não carregou. A lista continua disponível em "Ver em lista".'));
      return;
    }
    S.mapa = L.map('mapa', { zoomControl: true, preferCanvas: true, minZoom: 1, worldCopyJump: true }).setView([-14.5, -52], 4);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '© colaboradores do <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(S.mapa);
    L.control.scale({ imperial: false }).addTo(S.mapa);
    S.cluster = L.markerClusterGroup({
      chunkedLoading: false,
      showCoverageOnHover: false,
      spiderfyOnMaxZoom: true,
      maxClusterRadius: 50,
      iconCreateFunction: (c) => {
        let pior = 'log0';
        c.getAllChildMarkers().forEach((m) => { if (PESO[m.options.nivel] > PESO[pior]) pior = m.options.nivel; });
        const n = c.getChildCount();
        const tam = n < 10 ? 34 : n < 100 ? 40 : n < 1000 ? 46 : 54;
        return L.divIcon({ html: '<span>' + nf0.format(n) + '</span>', className: 'grupo grupo-' + pior, iconSize: [tam, tam] });
      },
    });
    S.mapa.addLayer(S.cluster);
    S.mapa.on('zoomend moveend', atualizarRotulos);
  }

  function limparMarcadores() {
    S.desenho++;
    if ($('#painel') && !$('#painel').hidden && !S.abrir) fecharPainel();
    clearTimeout(S.loteMapa); S.loteMapa = null;
    if (S.cluster) S.cluster.clearLayers();
    $('#mapa').setAttribute('aria-busy', 'false');
  }

  function adicionarMarcadores(lista) {
    limparMarcadores();
    const desenho = S.desenho;
    let offset = 0;
    $('#mapa').setAttribute('aria-busy', String(lista.length > 0));
    function lote() {
      if (desenho !== S.desenho) return;
      S.cluster.addLayers(lista.slice(offset, offset + 1000));
      offset += 1000;
      if (offset < lista.length) S.loteMapa = setTimeout(lote, 16);
      else { S.loteMapa = null; $('#mapa').setAttribute('aria-busy', 'false'); atualizarRotulos(); abrirPendente(); }
    }
    if (lista.length) S.loteMapa = setTimeout(lote, 0);
  }

  function rotuloSecoes(l) {
    const vis = l.secoes.filter(passaFiltro).sort((a, b) => PESO[b.chave] - PESO[a.chave] || a.secao - b.secao);
    const nums = vis.map((s) => s.secao);
    const txt = nums.slice(0, MAX_ROTULO).join(', ') + (nums.length > MAX_ROTULO ? ' +' + (nums.length - MAX_ROTULO) : '');
    return (nums.length === 1 ? 'Seção ' : 'Seções ') + txt;
  }

  // Prédio com seção que mudou de endereço vira losango; os demais, círculo. A cor segue o nível mais forte.
  function iconePino(nivel, n, mudou) {
    if (mudou) return L.divIcon({ className: 'pino-losango', iconSize: [24, 24], html: '<span class="losango pino-' + nivel + '"></span>' });
    return L.divIcon({ className: 'pino pino-' + nivel + (n >= 3 ? ' pino-varias' : ''), iconSize: [18, 18], html: '' });
  }

  function marcador(l, nivel) {
    let m = S.marcadores.get(l.id);
    const vis = l.secoes.filter(passaFiltro);
    const icone = iconePino(nivel, vis.length, vis.some((x) => x.mudanca));
    if (!m) {
      m = L.marker([l.lat, l.lon], { nivel, uf: l.uf, icon: icone, title: caixa(l.local), keyboard: true });
      m.bindTooltip(() => rotuloSecoes(l), { permanent: true, direction: 'bottom', offset: [0, 8], className: 'rotulo-secoes', interactive: false });
      if (telaPequena()) {
        // No celular a ficha é um painel fixo fora do mapa: um popup maior que o mapa empurra o pino
        // para fora da área visível, o agrupador remove o marcador e o popup fecha sozinho.
        m.on('click', (ev) => { L.DomEvent.stop(ev); abrirPainel(l, m); });
      } else {
        m.bindPopup(() => ficha(l), { maxWidth: 380, minWidth: 280, autoPanPadding: [24, 24], className: 'popup-ficha' });
        m.on('popupopen', () => { if (S.alvoLocal !== l.id) S.filtro.secaoAlvo = ''; S.aberto = l.id; carregarResultado(l, m.getPopup().getElement()); gravarHash(); });
        m.on('popupclose', () => { if (S.aberto === l.id) { S.aberto = null; S.filtro.secaoAlvo = ''; gravarHash(); } });
      }
      S.marcadores.set(l.id, m);
    } else {
      m.options.nivel = nivel;
      m.setIcon(icone);
      if (m.getTooltip()) m.setTooltipContent(rotuloSecoes(l));
    }
    return m;
  }

  // Os números das seções só aparecem escritos no mapa quando o zoom chega ao quarteirão.
  function atualizarRotulos() {
    if (!S.mapa || !S.cluster) return;
    const mostrar = S.mapa.getZoom() >= ZOOM_ROTULOS;
    $('#mapa').classList.toggle('com-rotulos', mostrar);
    const limites = S.mapa.getBounds();
    S.cluster.eachLayer((m) => {
      const t = m.getTooltip();
      if (!t) return;
      const visivel = mostrar && limites.contains(m.getLatLng()) && S.cluster.getVisibleParent(m) === m;
      if (visivel) { if (!m.isTooltipOpen()) m.openTooltip(); }
      else if (m.isTooltipOpen()) m.closeTooltip();
    });
  }

  function abrirPendente() {
    if (!S.abrir) return;
    let id = S.abrir;
    let m = S.marcadores.get(id);
    S.abrir = '';
    if (!m) {
      // Prédio do 1º turno cujas seções mudaram de endereço: abre o prédio novo, onde elas votam em 25/10.
      const novo = (S.destinoDoId1t.get(id) || []).find((x) => S.marcadores.has(x.id));
      if (novo) { id = novo.id; m = S.marcadores.get(id); }
    }
    if (!m) { setStatus('O prédio pedido não está no mapa com os filtros atuais. Marque mais níveis ou use "Limpar".', true); return; }
    const abrir = () => (telaPequena() ? abrirPainel(S.locaisPorId.get(id), m) : m.openPopup());
    if (m._icon) abrir();
    else S.cluster.zoomToShowLayer(m, abrir);
  }

  const telaPequena = () => window.matchMedia('(max-width: 979px)').matches;

  // Painel fixo do celular: a ficha do prédio, rolável, sem mexer no enquadramento do mapa.
  function abrirPainel(l, m) {
    const painel = $('#painel');
    const corpo = $('#painel-corpo');
    if (S.alvoLocal !== l.id) S.filtro.secaoAlvo = '';
    corpo.replaceChildren(ficha(l));
    painel.hidden = false;
    document.body.classList.add('painel-aberto');
    S.aberto = l.id;
    carregarResultado(l, corpo);
    gravarHash();
    if (m && S.mapa) S.mapa.panTo(m.getLatLng(), { animate: false });
    corpo.scrollTop = 0;
    const alvo = corpo.querySelector('#sec-atual');
    if (alvo) alvo.scrollIntoView({ block: 'nearest' });
    $('#painel-fechar').focus({ preventScroll: true });
  }

  function fecharPainel() {
    const painel = $('#painel');
    if (painel.hidden) return;
    painel.hidden = true;
    document.body.classList.remove('painel-aberto');
    S.aberto = null; S.filtro.secaoAlvo = '';
    gravarHash();
  }

  /* ------------------------------------------------------------ ficha do local */

  function chip(chave, extra) {
    return h('span', { class: 'chip n-' + chave }, NOME_NIVEL[chave] + (extra ? ' · ' + extra : ''));
  }

  function barraPlacar(s) {
    if (s.flavio_pct === null || s.flavio_pct === undefined || s.lula_pct === null || s.lula_pct === undefined) return null;
    const outros = Math.max(0, 100 - s.flavio_pct - s.lula_pct);
    return h('div', { class: 'placar', role: 'img', 'aria-label': 'Flávio ' + pct(s.flavio_pct) + ', Lula ' + pct(s.lula_pct) + ' dos votos válidos' },
      h('span', { class: 'p-f', style: 'width:' + s.flavio_pct + '%' }), h('span', { class: 'p-o', style: 'width:' + outros + '%' }), h('span', { class: 'p-l', style: 'width:' + s.lula_pct + '%' }));
  }

  function linhaResultado(s) {
    if (s.aptos === null || s.aptos === undefined) return h('p', { class: 'sec-res sem' }, 'Resultado da urna não disponível para esta seção.');
    const comp = s.comparecimento;
    const partes = [plural(s.aptos, 'eleitor apto', 'eleitores aptos')];
    if (comp !== null && comp !== undefined) partes.push(nf0.format(comp) + ' votaram (' + pct(100 * comp / s.aptos) + ')');
    return h('div', { class: 'sec-res' },
      h('p', {}, partes.join(' · ')),
      s.flavio_pct !== null && s.flavio_pct !== undefined ? h('p', { class: 'sec-placar' }, h('b', { class: 'tf' }, 'Flávio ' + pct(s.flavio_pct)), ' × ', h('b', { class: 'tl' }, 'Lula ' + pct(s.lula_pct)), h('small', {}, ' dos válidos, 1º turno')) : null,
      barraPlacar(s));
  }

  function motivosDe(s) {
    const fam = (S.meta.logs && S.meta.logs.familias) || {};
    const itens = [];
    s.critNomes.forEach((n) => itens.push(h('li', { class: 'm-hist' }, maiuscula(n))));
    s.familias.forEach((f) => {
      const nomes = fam[f].criterios.filter((c) => s.logs.indexOf(c) >= 0).map((c) => S.meta.logs.criterios[c].curto);
      itens.push(h('li', { class: 'm-log' }, h('b', {}, fam[f].curto + ': '), nomes.join('; ')));
    });
    return itens;
  }

  function distanciaMudanca(m) {
    if (typeof m.distancia_m !== 'number') return null;
    return m.distancia_m < 1000 ? nf0.format(m.distancia_m) + ' m' : km(m.distancia_m / 1000);
  }

  function blocoMudanca(s) {
    const m = s.mudanca;
    if (!m) return null;
    const onde = (nome, end, bairro, cep) => [caixa(nome), caixa(end), caixa(bairro), cep ? 'CEP ' + cepFmt(cep) : ''].filter(Boolean).join(' · ');
    const dist = distanciaMudanca(m);
    const graus = { local: 'Nota do TRE sobre este local', zona: 'Nota do TRE sobre a zona', municipio: 'Nota do TRE sobre o município, que pode não se referir a esta seção' };
    return h('div', { class: 'mud' },
      h('b', { class: 'mud-t' }, 'Mudou de endereço para o 2º turno'),
      h('p', {}, h('b', {}, (m.nome_cat || '') + '. '), m.frase || ''),
      h('p', {}, h('b', {}, 'Votou no 1º turno: '), onde(m.nome_1t, m.end_1t, m.bairro_1t, '')),
      h('p', {}, h('b', {}, 'Vota em 25/10: '), onde(m.nome_2t, m.end_2t, m.bairro_2t, m.cep_2t)),
      dist ? h('p', {}, 'Distância em linha reta entre os dois endereços: ' + dist + '.') : null,
      h('p', { class: 'ficha-meta' }, 'Fonte: ' + (NOME_FONTE_MUDANCA[m.fonte] || m.fonte) + '.' + (m.fonte !== 'ambos' ? ' As duas fontes do TSE divergem: confira no e-Título.' : '')),
      m.agregada_a ? h('p', { class: 'ficha-meta' }, 'Seção agregada à seção ' + m.agregada_a + ': o resultado do 1º turno aparece na seção ' + m.agregada_a + '.') : null,
      m.coord_2t ? null : h('p', { class: 'ficha-meta' }, 'O endereço novo não tem coordenada: o ponto no mapa é o prédio do 1º turno. Use o botão para abrir o endereço novo no Google Maps.'),
      m.motivo_tre ? h('p', { class: 'ficha-meta' }, (graus[m.grau_tre] || 'Nota do TRE') + ': ' + m.motivo_tre + ' ', m.url_tre ? h('a', { href: m.url_tre, target: '_blank', rel: 'noopener' }, 'Ler a nota do TRE') : null) : null,
      h('p', { class: 'mud-links' },
        m.maps_novo ? h('a', { class: 'btn-maps', href: m.maps_novo, target: '_blank', rel: 'noopener' }, 'Abrir no Google Maps') : null,
        h('a', { href: 'mudancas_secoes_abstencoes.html' }, 'Laudo das mudanças de endereço')));
  }

  function cartaoSecao(s, destacar) {
    const atual = destacar === s.secao;
    return h('li', { class: 'sec' + (atual ? ' sec-atual' : ''), id: atual ? 'sec-atual' : null, 'data-secao': String(s.secao) },
      h('div', { class: 'sec-cab' }, h('b', {}, 'Seção ' + s.secao), ' ', s.nivel !== 'logs' && s.nivel !== 'mudanca' ? chip(s.nivel, s.pontuacao !== null && s.pontuacao !== undefined ? s.pontuacao + ' pontos no cap. 13' : 'cap. 13') : null, s.logs.length ? chip('log' + (s.atencao || 0)) : null, s.mudanca ? chip('mudanca') : null),
      blocoMudanca(s),
      linhaResultado(s),
      s.nivel === 'mudanca' ? null : h('ul', { class: 'sec-motivos' }, motivosDe(s)),
      s.explicacao ? h('p', { class: 'sec-expl' }, 'Explicação provável: ' + s.explicacao) : null,
      h('p', { class: 'sec-pol' }),
      h('p', { class: 'sec-links' }, h('a', { href: 'politizesuavizinhanca.html#s=' + encodeURIComponent(s.uf + '-' + s.zona + '-' + s.secao) }, 'Ficha completa da seção no Politize')));
  }

  function ficha(l) {
    const vis = l.secoes.filter(passaFiltro).sort((a, b) => PESO[b.chave] - PESO[a.chave] || (b.pontuacao || 0) - (a.pontuacao || 0) || a.secao - b.secao);
    const todas = vis.length ? vis : l.secoes.slice().sort((a, b) => PESO[b.chave] - PESO[a.chave] || a.secao - b.secao);
    const dist = S.centro && coordOk(l) ? distanciaKm(S.centro.lat, S.centro.lon, l.lat, l.lon) : null;
    const pior = todas[0] ? todas[0].chave : 'log0';
    const conferir = [];
    todas.forEach((s) => {
      s.crit.forEach((c) => { const t = S.meta.criterios[c] && S.meta.criterios[c].conferir; if (t && conferir.indexOf(t) < 0) conferir.push(t); });
      s.familias.forEach((f) => { const t = S.meta.logs.familias[f].conferir; if (conferir.indexOf(t) < 0) conferir.push(t); });
      if (s.mudanca && conferir.indexOf(CONFERIR_MUDANCA) < 0) conferir.push(CONFERIR_MUDANCA);
    });
    const gmaps = 'https://www.google.com/maps/search/?api=1&query=' + l.lat + ',' + l.lon;
    const link = location.origin + location.pathname + '#uf=' + l.uf + '&l=' + encodeURIComponent(l.id) + (S.filtro.secaoAlvo ? '&s=' + encodeURIComponent(S.filtro.secaoAlvo) : '');
    const total = l.secoes_total;
    return h('div', { class: 'ficha' },
      chip(pior),
      h('h3', {}, caixa(l.local)),
      h('p', { class: 'ficha-end' }, [caixa(l.endereco), caixa(l.bairro), caixa(l.municipio) + '/' + l.uf, l.cep ? 'CEP ' + cepFmt(l.cep) : ''].filter(Boolean).join(' · ')),
      h('p', { class: 'ficha-meta' }, 'Zona ' + l.zona + ' · ' + (total ? plural(total, 'seção no prédio', 'seções no prédio') + ', ' + todas.length + ' no mapa' : plural(todas.length, 'seção no mapa', 'seções no mapa')) + (l.aptos_total ? ' · ' + nf0.format(l.aptos_total) + ' eleitores aptos' : '') + (dist !== null ? ' · ' + km(dist) + ' em linha reta de ' + S.centro.rotulo : '')),
      l.coord_fonte === 'cidade' ? h('p', { class: 'ficha-meta' }, 'Ponto aproximado da cidade, não do prédio. Confira o endereço antes de se deslocar.') : null,
      l.coord_fonte === 'local_2t' ? h('p', { class: 'ficha-meta' }, 'Prédio onde as seções abaixo votam no 2º turno. Resultado e sinais de cada seção são do prédio onde ela votou no 1º turno.') : null,
      h('ul', { class: 'ficha-secoes' }, todas.map((s) => cartaoSecao(s, Number(S.filtro.secaoAlvo)))),
      vis.length && vis.length < l.secoes.length ? h('p', { class: 'ficha-meta' }, (l.secoes.length - vis.length) + ' seção(ões) deste prédio fora dos filtros.') : null,
      l.coord_fonte === 'local_2t' ? null : h('div', { class: 'ficha-extra' }, h('p', { class: 'ficha-meta' }, 'Carregando as outras seções do prédio…')),
      h('div', { class: 'ficha-clima' }),
      l.risco ? h('p', { class: 'ficha-risco' }, h('b', {}, 'Risco do território: ' + (NOME_RISCO[l.risco] || l.risco)), l.risco_motivos && l.risco_motivos.length ? ' (' + l.risco_motivos.join('; ') + ')' : '', '. ', maiuscula(S.meta.risco_validar || ''), '.') : null,
      conferir.length ? h('div', { class: 'ficha-conf' }, h('b', {}, 'O que conferir no dia'), h('ul', {}, conferir.map((t) => h('li', {}, maiuscula(t))))) : null,
      h('p', { class: 'ficha-links' },
        h('a', { href: gmaps, target: '_blank', rel: 'noopener' }, 'Como chegar (Google Maps)'), ' · ',
        h('a', { href: 'politizesuavizinhanca.html#l=' + encodeURIComponent(l.id) }, 'Este prédio no Politize'), ' · ',
        h('a', { href: link, onclick: (ev) => { ev.preventDefault(); copiar(link, ev.target); } }, 'Copiar link')));
  }

  // As demais seções do prédio (sem sinal no mapa) vêm do Politize, para o fiscal ver o prédio inteiro.
  async function carregarResultado(l, el) {
    preencherClima(l, el);
    const caixaExtra = el && el.querySelector('.ficha-extra');
    if (!caixaExtra || !l.mun) return;
    // Seção que mudou de endereço traz o id do prédio do 1º turno, que é o que o Politize conhece.
    const ids = new Set([l.id].concat(l.secoes.filter((x) => x.mudanca && x.mudanca.id_1t).map((x) => x.mudanca.id_1t)));
    buscar(POLITIZE + 'fiscal/' + l.uf + '/' + Number(l.zona) + '.json').then((f) => {
      const cols = f.secoes.colunas;
      const nomes = { maxima: 'Prioridade máxima', alta: 'Prioridade alta', reforcada: 'Atenção reforçada', padrao: 'Atenção padrão' };
      f.secoes.linhas.forEach((ln) => {
        const r = Object.fromEntries(cols.map((c, i) => [c, ln[i]]));
        const alvo = el.querySelector('.sec[data-secao="' + r.secao + '"] .sec-pol');
        if (alvo && ids.has(r.local_id)) alvo.replaceChildren('No Politize, que soma todos os motivos numa escala própria: ' + (nomes[r.nivel] || r.nivel) + ' (' + plural(r.pontos, 'ponto', 'pontos') + ').');
      });
    }).catch(() => {});
    try {
      const z = await buscar(POLITIZE + 'zona/' + l.uf + '/' + Number(l.zona) + '.json');
      const cols = z.secoes.colunas;
      // Seção que votava aqui no 1º turno e mudou de endereço aparece no prédio novo, não nesta lista.
      const foram = S.secoes.filter((x) => x.mudanca && x.mudanca.id_1t === l.id && x.local !== l).map((x) => Number(x.secao)).sort((a, b) => a - b);
      const noMapa = new Set(l.secoes.map((s) => Number(s.secao)).concat(foram));
      const avisoForam = foram.length ? h('p', { class: 'ficha-meta' }, (foram.length === 1 ? '1 seção votava aqui no 1º turno e mudou' : nf0.format(foram.length) + ' seções votavam aqui no 1º turno e mudaram') + ' de endereço para o 2º turno (' + foram.join(', ') + '): ' + (foram.length === 1 ? 'ela aparece' : 'elas aparecem') + ' no prédio novo.') : null;
      const outras = z.secoes.linhas.map((ln) => Object.fromEntries(cols.map((c, i) => [c, ln[i]]))).filter((r) => ids.has(r.local_id) && !noMapa.has(Number(r.secao))).sort((a, b) => a.secao - b.secao);
      if (!outras.length) { caixaExtra.replaceChildren(avisoForam || h('p', { class: 'ficha-meta' }, 'Todas as seções deste prédio estão no mapa.')); return; }
      const soma = outras.reduce((acc, r) => { acc.aptos += r.aptos || 0; acc.comp += r.comparecimento || 0; acc.f += r.flavio || 0; acc.l += r.lula || 0; acc.v += (r.flavio || 0) + (r.lula || 0) + (r.terceira || 0); return acc; }, { aptos: 0, comp: 0, f: 0, l: 0, v: 0 });
      caixaExtra.replaceChildren(avisoForam,
        h('details', {}, h('summary', {}, 'Mais ' + plural(outras.length, 'seção do prédio sem sinal', 'seções do prédio sem sinal')),
          h('p', { class: 'ficha-meta' }, 'Juntas: ' + nf0.format(soma.aptos) + ' aptos, ' + nf0.format(soma.comp) + ' votaram' + (soma.v ? '; Flávio ' + pct(100 * soma.f / soma.v) + ' × Lula ' + pct(100 * soma.l / soma.v) + ' dos válidos' : '') + '. Toda seção precisa de fiscal, mesmo sem sinal.'),
          h('p', { class: 'sec-outras' }, outras.map((r) => h('a', { href: 'politizesuavizinhanca.html#s=' + encodeURIComponent(l.uf + '-' + l.zona + '-' + r.secao) }, String(r.secao))))));
    } catch (e) {
      caixaExtra.replaceChildren(h('p', { class: 'ficha-meta' }, 'As outras seções do prédio não carregaram agora.'));
    }
  }

  function copiar(texto, botao) {
    const ok = () => { const t = botao.textContent; botao.textContent = 'Link copiado'; setTimeout(() => { botao.textContent = t; }, 1500); };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(texto).then(ok, () => window.prompt('Copie o link:', texto));
    else window.prompt('Copie o link:', texto);
  }

  function desenharMapa(rs, enquadrar) {
    if (!S.mapa) return { locais: 0 };
    const noRaio = rs.filter((s) => coordOk(s.local) && (!S.centro || s.dist <= S.raio));
    const ids = new Map();
    noRaio.forEach((s) => {
      const n = ids.get(s.local.id);
      if (!n || PESO[s.chave] > PESO[n]) ids.set(s.local.id, s.chave);
    });
    const lista = [];
    ids.forEach((nivel, id) => lista.push(marcador(S.locaisPorId.get(id), nivel)));
    adicionarMarcadores(lista);
    if (S.circulo) { S.mapa.removeLayer(S.circulo); S.circulo = null; }
    if (S.alvo) { S.mapa.removeLayer(S.alvo); S.alvo = null; }
    if (S.centro) {
      S.circulo = L.circle([S.centro.lat, S.centro.lon], { radius: S.raio * 1000, color: '#151812', weight: 2, dashArray: '6 6', fill: true, fillOpacity: 0.04, interactive: false }).addTo(S.mapa);
      S.alvo = L.marker([S.centro.lat, S.centro.lon], { icon: L.divIcon({ className: 'alvo', iconSize: [22, 22], html: '' }), title: S.centro.rotulo, keyboard: false, interactive: false }).addTo(S.mapa);
    }
    const alvo = S.abrir ? S.locaisPorId.get(S.abrir) || (S.destinoDoId1t.get(S.abrir) || [])[0] || null : null;
    if (enquadrar) {
      // Com um prédio a abrir, o mapa vai direto ao quarteirão, sem animação, para a ficha abrir sem corrida com o enquadramento.
      if (alvo && coordOk(alvo)) S.mapa.setView([alvo.lat, alvo.lon], ZOOM_ROTULOS + 2, { animate: false });
      else if (S.centro) S.mapa.fitBounds(S.circulo.getBounds(), { padding: [24, 24], maxZoom: 16 });
      else if (lista.length) {
        // Sem filtro de estado, o enquadramento é o Brasil; o exterior continua no mapa, fora do quadro inicial.
        const brasil = lista.filter((m) => m.options.uf !== 'ZZ');
        S.mapa.fitBounds(L.featureGroup(brasil.length ? brasil : lista).getBounds(), { padding: [30, 30], maxZoom: 15 });
      }
    }
    return { locais: lista.length, secoes: noRaio.length };
  }

  /* ------------------------------------------------------------ lista */

  function valorOrdem(s, col) {
    if (col === 'nivel') return -PESO[s.chave] * 1e6 - (s.pontuacao || 0) - (s.atencao || 0);
    if (col === 'dist') return s.dist === null || s.dist === undefined ? 1e9 : s.dist;
    if (col === 'coord') return coordOk(s.local) ? 0 : 1;
    if (col === 'motivos') return s.critNomes.concat(s.logNomes).join('; ');
    if (col === 'risco') return { alto: 0, medio: 1, baixo: 2 }[s.local.risco] ?? 3;
    if (col === 'votaram') return s.comparecimento === null || s.comparecimento === undefined ? -1 : s.comparecimento;
    if (col === 'placar') return s.flavio_pct === null || s.flavio_pct === undefined ? -1 : s.flavio_pct;
    if (col === 'local') return s.local.local || '';
    if (col === 'mudanca') return s.mudanca ? 0 : 1;
    if (col === 'chuva') { const c = climaObservado(s); return c && typeof c.chuva_04_10_mm === 'number' ? -c.chuva_04_10_mm : 1e9; }
    if (col === 'risco25') { const c = riscoPrevisto(s.local); return c ? { alto: 0, medio: 1, baixo: 2 }[c.risco] ?? 3 : 4; }
    const v = s[col];
    return v === null || v === undefined ? '' : v;
  }

  function ordenar(rs) {
    const c = S.ordem.col, d = S.ordem.dir;
    const col = new Intl.Collator('pt-BR', { numeric: true, sensitivity: 'base' });
    return rs.slice().sort((a, b) => {
      const x = valorOrdem(a, c), y = valorOrdem(b, c);
      let r = typeof x === 'number' && typeof y === 'number' ? x - y : col.compare(String(x), String(y));
      if (r === 0) r = col.compare(a.uf + a.municipio, b.uf + b.municipio) || a.zona - b.zona || a.secao - b.secao;
      return r * d;
    });
  }

  function linhasLista(rs) {
    const q = norm(S.buscaLista);
    if (!q) return rs;
    const termos = q.split(' ');
    return rs.filter((s) => termos.every((t) => s.busca.indexOf(t) >= 0));
  }

  // As colunas de clima só existem depois que os arquivos de clima chegam.
  function colunasLista() {
    const cols = COLS_LISTA.slice();
    const extra = [];
    if (S.clima.ufResolvidos && Object.keys(S.clima.ufResolvidos).length) extra.push(COL_CHUVA);
    if (S.clima.prev) extra.push(COL_RISCO25);
    cols.splice(cols.findIndex((c) => c[0] === 'mudanca') + 1, 0, ...extra);
    return cols;
  }

  function celulaMudanca(s) {
    const m = s.mudanca;
    if (!m) return h('td', {});
    const dist = distanciaMudanca(m);
    return h('td', {}, h('b', {}, m.nome_cat || 'Mudou de endereço'),
      h('small', {}, 'Antes: ' + [caixa(m.nome_1t), caixa(m.end_1t)].filter(Boolean).join(' · ') + (dist ? ' · a ' + dist : '')),
      h('small', {}, m.fonte === 'ambos' ? 'Arquivo e painel do TSE concordam' : 'As duas fontes do TSE divergem'));
  }

  function celulasClima(s, cols) {
    const out = [];
    cols.forEach((c) => {
      if (c[0] === 'chuva') {
        const o = climaObservado(s);
        out.push(h('td', { class: 'num' }, o && typeof o.chuva_04_10_mm === 'number' ? [nf1.format(o.chuva_04_10_mm) + ' mm', typeof o.chuva_votacao_mm === 'number' ? h('small', {}, nf1.format(o.chuva_votacao_mm) + ' mm na votação') : null] : ''));
      } else if (c[0] === 'risco25') {
        const p = riscoPrevisto(s.local);
        out.push(h('td', {}, p ? [NOME_RISCO[p.risco] || p.risco, typeof p.chuva_mm === 'number' ? h('small', {}, nf1.format(p.chuva_mm) + ' mm entre 8h–17h BRT') : null] : ''));
      }
    });
    return out;
  }

  function desenharLista(rs) {
    const caixaRaio = $('#l-raio-caixa');
    caixaRaio.hidden = !S.centro;
    if (S.centro) { $('#l-raio').checked = S.listaRaio; $('#l-raio-txt').textContent = 'Só até ' + S.raio + ' km de ' + S.centro.rotulo; }
    const base = S.centro && S.listaRaio ? rs.filter((s) => s.dist !== null && s.dist <= S.raio) : rs;
    const todas = ordenar(linhasLista(base));
    S.listaAtual = todas;
    const n = todas.length;
    const paginas = Math.max(1, Math.ceil(n / S.porPagina));
    if (S.pagina > paginas) S.pagina = paginas;
    const ini = (S.pagina - 1) * S.porPagina;
    const pag = todas.slice(ini, ini + S.porPagina);
    const semCoord = todas.filter((s) => !coordOk(s.local)).length;
    $('#l-resumo').textContent = plural(n, 'seção', 'seções') + (S.centro && S.listaRaio ? ' até ' + S.raio + ' km de ' + S.centro.rotulo : ' pelos filtros, sem limite de distância') +
      (semCoord ? ', ' + nf0.format(semCoord) + ' sem coordenada' : '') + (S.centro ? '. A coluna de distância mede a partir de ' + S.centro.rotulo + '.' : '.');

    const thead = $('#tabela thead');
    const cols = colunasLista();
    thead.replaceChildren(h('tr', {}, cols.map((c) => {
      const ativo = S.ordem.col === c[0];
      return h('th', { scope: 'col', 'aria-sort': ativo ? (S.ordem.dir === 1 ? 'ascending' : 'descending') : 'none' },
        h('button', { type: 'button', class: 'ord', onclick: () => {
          if (S.ordem.col === c[0]) S.ordem.dir = -S.ordem.dir; else { S.ordem.col = c[0]; S.ordem.dir = 1; }
          S.ordemManual = true; S.pagina = 1; atualizar(false);
        } }, c[1], h('span', { class: 'seta', 'aria-hidden': 'true' }, ativo ? (S.ordem.dir === 1 ? ' ▲' : ' ▼') : '')));
    })));
    const tbody = $('#tabela tbody');
    tbody.replaceChildren(...pag.map((s) => {
      const l = s.local;
      return h('tr', {},
        h('td', {}, s.nivel !== 'logs' ? chip(s.nivel) : null, s.logs.length ? chip('log' + (s.atencao || 0)) : null, s.mudanca && s.nivel !== 'mudanca' ? chip('mudanca') : null),
        h('td', {}, l.uf), h('td', {}, caixa(l.municipio)), h('td', { class: 'num' }, String(l.zona)),
        h('td', { class: 'num' }, h('a', { href: 'politizesuavizinhanca.html#s=' + encodeURIComponent(l.uf + '-' + l.zona + '-' + s.secao), title: 'Ficha completa desta seção no Politize' }, String(s.secao))),
        h('td', {}, caixa(l.local), h('small', {}, [caixa(l.endereco), caixa(l.bairro)].filter(Boolean).join(' · '))),
        h('td', { class: 'num' }, s.comparecimento === null || s.comparecimento === undefined ? '' : [nf0.format(s.comparecimento), s.aptos ? h('small', {}, 'de ' + nf0.format(s.aptos)) : null]),
        h('td', { class: 'num' }, s.flavio_pct === null || s.flavio_pct === undefined ? '' : [h('span', { class: 'tf' }, pct(s.flavio_pct)), ' × ', h('span', { class: 'tl' }, pct(s.lula_pct))]),
        h('td', {}, motivosDaLinha(s)),
        h('td', {}, l.risco ? NOME_RISCO[l.risco] || l.risco : 'sem base'),
        celulaMudanca(s),
        celulasClima(s, cols),
        h('td', { class: 'num' }, km(s.dist)),
        h('td', {}, coordOk(l)
          ? h('a', { href: '#', onclick: (ev) => { ev.preventDefault(); S.abrir = l.id; trocarModo('mapa'); } }, 'Ver no mapa')
          : h('span', { class: 'sem' }, 'sem coordenada')));
    }));
    if (!pag.length) tbody.replaceChildren(h('tr', {}, h('td', { colspan: String(cols.length) }, 'Nenhuma seção com esses filtros.')));
    desenharPaginas(paginas);
  }

  function motivosDaLinha(s) {
    let nomes = s.critNomes.map(maiuscula).concat(s.logNomes);
    const f = S.filtro.log;
    const escolhido = f.startsWith('historico:') ? maiuscula((S.meta.criterios[f.slice(10)] || {}).nome || '') : f && !f.startsWith('familia:') ? ((S.meta.logs.criterios[f] || {}).curto || '') : '';
    if (escolhido && nomes.indexOf(escolhido) >= 0) nomes = [escolhido].concat(nomes.filter((n) => n !== escolhido));
    if (!nomes.length && s.mudanca) nomes = [NOME_NIVEL.mudanca];
    return h('div', { class: 'criterios-linha' }, h('span', {}, nomes[0] || ''), nomes.length > 1
      ? h('details', {}, h('summary', {}, 'Mais ' + (nomes.length - 1) + (nomes.length === 2 ? ' motivo' : ' motivos')), h('ul', {}, nomes.slice(1).map((n) => h('li', {}, n))))
      : null);
  }

  function desenharPaginas(total) {
    const nav = $('#paginas');
    const botoes = [];
    const ir = (p) => () => { S.pagina = p; atualizar(false); $('#lista').scrollIntoView({ block: 'start' }); };
    botoes.push(h('button', { type: 'button', disabled: S.pagina <= 1, onclick: ir(S.pagina - 1) }, 'Anterior'));
    const vistas = new Set([1, total, S.pagina - 2, S.pagina - 1, S.pagina, S.pagina + 1, S.pagina + 2]);
    let ult = 0;
    for (let p = 1; p <= total; p++) {
      if (!vistas.has(p)) continue;
      if (p - ult > 1) botoes.push(h('span', { class: 'reticencias' }, '…'));
      botoes.push(h('button', { type: 'button', 'aria-current': p === S.pagina ? 'page' : null, onclick: ir(p) }, String(p)));
      ult = p;
    }
    botoes.push(h('button', { type: 'button', disabled: S.pagina >= total, onclick: ir(S.pagina + 1) }, 'Próxima'));
    nav.replaceChildren(...botoes);
  }

  function exportarCsv() {
    const rs = S.listaAtual || [];
    const cab = ['nivel_historico', 'atencao_log', 'uf', 'municipio', 'zona', 'secao', 'local', 'endereco', 'bairro', 'cep', 'lat', 'lon', 'distancia_km_linha_reta', 'pontuacao', 'aptos', 'votaram', 'flavio_pct_validos', 'lula_pct_validos', 'criterios_historicos', 'diagnosticos_log', 'familias_log', 'explicacao_provavel', 'risco_territorio', 'mediana_votacao_s', 'processo_mediana_s', 'cadencia_mediana_s', 'coordenada_fonte', 'google_maps', 'ficha_secao',
      'mudou_endereco', 'mudanca_categoria', 'mudanca_fonte', 'mudanca_local_1t', 'mudanca_endereco_1t', 'mudanca_bairro_1t', 'mudanca_local_2t', 'mudanca_endereco_2t', 'mudanca_bairro_2t', 'mudanca_cep_2t', 'mudanca_lat_2t', 'mudanca_lon_2t', 'mudanca_distancia_m', 'mudanca_nota_tre', 'mudanca_url_tre', 'mudanca_google_maps_local_novo', 'mudanca_agregada_a',
      'chuva_04_10_mm', 'chuva_votacao_mm', 'hora_pico_chuva', 'rajada_04_10_kmh', 'rajada_votacao_kmh', 'urnas_bateria_votacao_predio', 'abstencao_1t_2026_pct', 'abstencao_2t_2022_pct', 'variacao_contra_2022_pp', 'risco_climatico_25_10_08a17_brt', 'chuva_prevista_25_10_08a17_brt_mm', 'prob_horaria_max_25_10_08a17_brt_pct', 'rajada_max_25_10_08a17_brt_kmh'];
    const dec = (v, c) => (v === null || v === undefined || v === '' ? '' : (typeof v === 'number' ? v.toFixed(c).replace('.', ',') : String(v)));
    const esc = (v) => { const s = v === null || v === undefined ? '' : String(v); return /[";\n\r]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; };
    const linhas = [cab.join(';')];
    rs.forEach((s) => {
      const l = s.local;
      const m = s.mudanca || {};
      const o = climaObservado(s) || {};
      const pv = riscoPrevisto(l) || {};
      linhas.push([
        s.nivel === 'logs' ? '' : NOME_NIVEL[s.nivel], s.logs.length ? s.atencao : '', l.uf, l.municipio, l.zona, s.secao, l.local, l.endereco, l.bairro, l.cep,
        coordOk(l) ? dec(l.lat, 5) : '', coordOk(l) ? dec(l.lon, 5) : '', s.dist === null || s.dist === undefined ? '' : dec(s.dist, 2),
        s.pontuacao, s.aptos, s.comparecimento, dec(s.flavio_pct, 2), dec(s.lula_pct, 2),
        s.crit.join('|'), s.logs.join('|'), s.familias.join('|'), s.explicacao, l.risco || '', dec(s.tempo_voto, 1), dec(s.processo_mediana, 1), dec(s.cadencia_mediana, 1), l.coord_fonte,
        coordOk(l) ? 'https://www.google.com/maps/search/?api=1&query=' + l.lat + ',' + l.lon : '',
        'https://brasil.arvor.co/politizesuavizinhanca.html#s=' + l.uf + '-' + l.zona + '-' + s.secao,
        s.mudanca ? 'sim' : '', m.nome_cat, m.fonte, m.nome_1t, m.end_1t, m.bairro_1t, m.nome_2t, m.end_2t, m.bairro_2t, m.cep_2t, dec(m.lat_2t, 6), dec(m.lon_2t, 6), dec(m.distancia_m, 0), m.motivo_tre, m.url_tre, m.maps_novo, m.agregada_a,
        dec(o.chuva_04_10_mm, 1), dec(o.chuva_votacao_mm, 1), o.hora_pico_chuva, dec(o.rajada_04_10_kmh, 0), dec(o.rajada_votacao_kmh, 0), o.urnas_bateria_votacao, dec(o.abst_pct, 1), dec(o.abst22_pct, 1), dec(o.dif_abst_pp, 1), pv.risco, dec(pv.chuva_mm, 1), dec(pv.prob_pct, 0), dec(pv.rajada_kmh, 0),
      ].map(esc).join(';'));
    });
    const blob = new Blob(['﻿' + linhas.join('\r\n')], { type: 'text/csv;charset=utf-8' });
    const a = h('a', { href: URL.createObjectURL(blob), download: 'fiscais_filtrados_' + new Date().toISOString().slice(0, 10) + '.csv' });
    document.body.appendChild(a);
    a.click();
    setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
  }

  /* ------------------------------------------------------------ estado e controles */

  function setStatus(t, erro) {
    const s = $('#status');
    s.textContent = t;
    s.classList.toggle('erro', Boolean(erro));
    if (erro && window.innerWidth < 980) s.scrollIntoView({ block: 'center', behavior: 'smooth' });
  }

  function atualizar(enquadrar) {
    if (!S.meta) return;
    const rs = comDistancia(filtradas());
    const semCoord = rs.filter((s) => !coordOk(s.local)).length;
    let aviso = S.avisoLog || '';
    if (!S.filtro.niveis.size && !S.filtro.log) aviso += 'Nenhum nível marcado em "O que mostrar": marque ao menos um, ou use "Limpar". ';
    if (S.modo === 'mapa') {
      const res = desenharMapa(rs, enquadrar);
      const onde = S.centro ? ' até ' + S.raio + ' km de ' + S.centro.rotulo + ' (' + S.centro.precisao + ')' : '';
      setStatus(aviso + plural(res.locais || 0, 'prédio', 'prédios') + ' com ' + plural(res.secoes || 0, 'seção no mapa', 'seções no mapa') + onde + '.' +
        (semCoord && !S.centro ? ' ' + nf0.format(semCoord) + ' sem coordenada ficam fora do mapa; veja em lista.' : '') +
        (S.centro && rs.length && !res.secoes ? ' Aumente a distância ou veja em lista.' : '') +
        (!rs.length && S.filtro.uf && !S.meta.partes[S.filtro.uf] ? ' Nenhuma seção sinalizada neste estado.' : ''));
    } else {
      desenharLista(rs);
      setStatus(aviso + plural(S.listaAtual.length, 'seção na lista', 'seções na lista') + (S.centro && S.listaRaio ? ', até ' + S.raio + ' km do ponto buscado.' : ', sem limite de distância.'));
    }
    atualizarCriterio(rs);
    gravarHash();
    S.avisoLog = '';
  }

  function trocarModo(m, semAtualizar) {
    S.modo = m;
    if (m === 'lista') limparMarcadores();
    $('#m-mapa').setAttribute('aria-pressed', String(m === 'mapa'));
    $('#m-lista').setAttribute('aria-pressed', String(m === 'lista'));
    $('#mapa').hidden = m !== 'mapa';
    $('#lista').hidden = m !== 'lista';
    $('#bloco-raio').hidden = false;
    document.body.classList.toggle('modo-lista', m === 'lista');
    if (semAtualizar) return;
    if (m === 'mapa' && S.mapa) setTimeout(() => { S.mapa.invalidateSize(); atualizar(true); }, 0);
    else atualizar(false);
  }

  function montarRaios() {
    const box = $('#raios');
    box.replaceChildren(...RAIOS.map((r) => h('button', { type: 'button', role: 'radio', 'aria-checked': String(r === S.raio), 'data-r': String(r), onclick: () => {
      S.raio = r;
      box.querySelectorAll('button').forEach((b) => b.setAttribute('aria-checked', String(Number(b.dataset.r) === r)));
      atualizar(true);
    } }, r + ' km')));
  }

  function montarUfs() {
    const sel = $('#f-uf');
    const presentes = new Set(Object.keys(S.meta.partes));
    Object.keys(UFS).forEach((u) => sel.appendChild(h('option', { value: u }, (u === 'ZZ' ? 'Exterior' : u + ' · ' + UFS[u]) + (presentes.has(u) ? '' : ' (sem seção sinalizada)'))));
  }

  function montarMunicipios() {
    if (!S.meta) return;
    const uf = $('#f-uf').value;
    const sel = $('#f-mun');
    if (!uf) { sel.replaceChildren(h('option', { value: '' }, 'Escolha o estado primeiro')); sel.disabled = true; return; }
    const lista = ((S.meta.partes[uf] || {}).municipios || []).slice().sort((a, b) => new Intl.Collator('pt-BR').compare(a[1], b[1]));
    sel.replaceChildren(h('option', { value: '' }, 'Todas (' + lista.length + ' com seção no mapa)'), ...lista.map((m) => h('option', { value: m[0] }, caixa(m[1]))));
    sel.disabled = false;
  }

  function montarNiveis() {
    const box = $('#niveis');
    const n = S.meta.niveis || {};
    const at = (S.meta.resumo && S.meta.resumo.atencao) || {};
    const contagem = { alta: n.alta, media: n.media, baixa: n.baixa, log3: at['3'], log2: at['2'], log1: at['1'], log0: at['0'], mudanca: S.meta.mudancas ? S.meta.mudancas.secoes : 0 };
    const grupos = [['Prioridade histórica (capítulo 13 do dossiê)', ['alta', 'media', 'baixa']], ['Sinais no log da urna', ['log3', 'log2', 'log1', 'log0']]];
    if (S.meta.mudancas) grupos.push(['Mudança para o 2º turno', ['mudanca']]);
    box.replaceChildren(...grupos.map((g) => h('div', { class: 'niveis-grupo' }, h('p', { class: 'rot' }, g[0]), g[1].map((k) =>
      h('label', { class: 'nv nv-' + k }, h('input', { type: 'checkbox', value: k, checked: S.filtro.niveis.has(k), onchange: (ev) => {
        if (ev.target.checked) S.filtro.niveis.add(k); else S.filtro.niveis.delete(k);
        S.pagina = 1;
        aplicarBusca();
      } }), h('span', { class: 'pt' }), h('span', { class: 'nv-t' }, NOME_NIVEL[k], h('small', {}, nf0.format(contagem[k] || 0))))))));
  }

  function montarCriterios() {
    const d = S.meta;
    const sel = $('#f-log');
    if (d.mudancas) sel.appendChild(h('optgroup', { label: 'Mudança de endereço para o 2º turno' }, h('option', { value: CRIT_MUDANCA }, d.mudancas.nome + ' · ' + nf0.format(d.mudancas.secoes))));
    const historicos = h('optgroup', { label: 'Critérios históricos (capítulo 13)' });
    Object.keys(d.criterios).forEach((k) => historicos.appendChild(h('option', { value: 'historico:' + k }, maiuscula(d.criterios[k].nome) + ' · ' + nf0.format(d.criterios[k].secoes))));
    sel.appendChild(historicos);
    if (!d.logs) return;
    const fam = d.logs.familias;
    const familias = h('optgroup', { label: 'Famílias de sinais do log' });
    Object.keys(fam).forEach((f) => {
      const n = fam[f].criterios.reduce((acc, c) => acc + (d.logs.criterios[c].secoes || 0), 0);
      familias.appendChild(h('option', { value: 'familia:' + f }, fam[f].nome + ' · até ' + nf0.format(n)));
    });
    sel.appendChild(familias);
    Object.keys(fam).forEach((f) => {
      const grupo = h('optgroup', { label: 'Log · ' + fam[f].nome });
      fam[f].criterios.forEach((k) => {
        const r = d.logs.criterios[k];
        if (!r.secoes) return; // diagnósticos testados sem nenhuma seção ficam fora do seletor
        grupo.appendChild(h('option', { value: k }, r.curto + ' · ' + nf0.format(r.secoes)));
      });
      if (grupo.children.length) sel.appendChild(grupo);
    });
  }

  function montarResumo() {
    const d = S.meta;
    const r = d.resumo || {};
    const at = r.atencao || {};
    $('#n-cap13').textContent = nf0.format(r.secoes_originais || 0);
    $('#n-log-forte').textContent = nf0.format((Number(at['3']) || 0) + (Number(at['2']) || 0));
    $('#n-rotina').textContent = nf0.format(Number(at['0']) || 0);
    if (d.mudancas) {
      $('#n-mud-secoes').textContent = nf0.format(d.mudancas.secoes);
      $('#n-mud-eleitores').textContent = nf0.format(d.mudancas.eleitores);
    }
    const zeros = (d.logs && d.logs.sem_ocorrencia) || [];
    if (zeros.length) $('#sem-ocorrencia').textContent = zeros.length + ' diagnósticos de rapidez foram testados em todas as urnas e não marcaram nenhuma seção (' + zeros.map((k) => d.logs.criterios[k].curto.toLowerCase()).join('; ') + '). Por isso não aparecem no seletor.';
    if (d.logs && d.logs.cobertura) {
      const c = d.logs.cobertura;
      $('#cobertura-logs').textContent = 'Logs lidos: ' + nf0.format(c.lidos) + ' de ' + nf0.format(c.catalogadas) + ' seções. Seção sem log analisado não significa seção sem ocorrência.';
    }
  }

  function atualizarCriterio(rs) {
    const f = S.filtro;
    let r = null, link = '';
    if (f.log === CRIT_MUDANCA && S.meta.mudancas) { const mu = S.meta.mudancas; link = 'mudancas_secoes_abstencoes.html'; r = { nome: mu.nome, regra: mu.frase + ' ' + nf0.format(mu.secoes) + ' seções e ' + nf0.format(mu.eleitores) + ' eleitores.', limite: mu.nota, conferir: maiuscula(CONFERIR_MUDANCA) }; }
    else if (f.log.startsWith('historico:')) { r = S.meta.criterios[f.log.slice(10)]; link = 'apuracao_1o_turno_2026.html#fiscais'; if (r) r = { nome: maiuscula(r.nome), regra: r.mede, conferir: r.conferir }; }
    else if (f.log.startsWith('familia:')) { const fm = S.meta.logs.familias[f.log.slice(8)]; link = 'logs_urnas_2026.html'; if (fm) r = { nome: fm.nome, regra: fm.explica, conferir: fm.conferir }; }
    else if (f.log) { const c = S.meta.logs.criterios[f.log]; link = 'logs_urnas_2026.html#' + f.log; if (c) r = { nome: c.curto, regra: c.regra, conferir: c.conferir, limite: c.limite }; }
    const exterior = rs.filter((s) => s.uf === 'ZZ').length;
    $('#recorte-ativo').textContent = (r ? r.nome : f.camada === 'logs' ? 'Só sinais do log' : f.camada === 'originais' ? 'Só critérios históricos' : 'Histórico e logs') + ' · ' + plural(rs.length, 'seção', 'seções') + (exterior ? ', ' + nf0.format(exterior) + ' no exterior' : '') + (S.modo === 'mapa' && S.centro ? ' (antes do raio)' : '') +
      (f.risco25 ? ' · risco climático previsto ' + (f.risco25 === 'alto' ? 'alto' : 'alto ou médio') + ' em 25/10' : '') + (f.choveu ? ' · choveu forte no 1º turno' : '');
    $('#criterio-ativo').hidden = !r;
    if (r) $('#criterio-ativo').replaceChildren(...[h('strong', {}, r.nome), h('p', {}, r.regra), r.limite ? h('p', { class: 'ajuda' }, r.limite) : null, h('p', {}, h('b', {}, 'Conferir: '), r.conferir), h('a', { href: link }, 'Ler a regra completa')].filter(Boolean));
    const fixo = Boolean(f.log);
    $('#niveis').classList.toggle('inativo', fixo);
    $('#niveis').querySelectorAll('input').forEach((i) => { i.disabled = fixo; });
    $('#niveis-aviso').hidden = !fixo;
  }

  function gravarHash() {
    const f = S.filtro, p = [];
    if (f.uf) p.push('uf=' + f.uf);
    if (f.mun) p.push('mun=' + encodeURIComponent(f.mun));
    if (f.zona) p.push('zona=' + f.zona);
    if (f.texto) p.push('q=' + encodeURIComponent(f.texto));
    const padrao = PADRAO_NIVEIS.length === f.niveis.size && PADRAO_NIVEIS.every((k) => f.niveis.has(k));
    if (!padrao) p.push('nivel=' + NIVEIS.filter((k) => f.niveis.has(k)).join(','));
    if (f.camada !== 'todas') p.push('camada=' + f.camada);
    if (f.log === CRIT_MUDANCA) p.push('crit=' + CRIT_MUDANCA);
    else if (f.log) p.push('log=' + encodeURIComponent(f.log));
    if (f.risco25) p.push('risco25=' + f.risco25);
    if (f.choveu) p.push('choveu=1');
    if (S.raio !== RAIO_PADRAO) p.push('raio=' + S.raio);
    if (S.modo === 'lista') p.push('modo=lista');
    const aberto = S.abrir || S.aberto;
    if (aberto) p.push('l=' + encodeURIComponent(aberto));
    if (aberto && f.secaoAlvo) p.push('s=' + encodeURIComponent(f.secaoAlvo));
    const novo = p.length ? '#' + p.join('&') : '';
    if (novo === location.hash || (!novo && !location.hash)) return;
    S.hashProprio = novo;
    try { history.replaceState(null, '', location.pathname + location.search + novo); } catch (e) { /* navegador embutido */ }
  }

  function lerHash() {
    const q = new URLSearchParams(location.hash.slice(1));
    const f = S.filtro;
    f.niveis = new Set(PADRAO_NIVEIS);
    $('#f-camada').value = ['todas', 'originais', 'logs'].indexOf(q.get('camada')) >= 0 ? q.get('camada') : 'todas';
    const pedido = q.get('crit') || q.get('log') || '';
    $('#f-log').value = pedido;
    S.avisoLog = '';
    if (pedido && !$('#f-log').value) {
      // Critério desconhecido, ou testado sem nenhuma seção: o mapa abre inteiro e avisa.
      const c = S.meta.logs && S.meta.logs.criterios[pedido];
      S.avisoLog = c ? 'O diagnóstico "' + c.curto + '" foi testado em todas as urnas e não marcou nenhuma seção. ' : 'O critério pedido no link não existe. ';
    }
    f.camada = $('#f-camada').value; f.log = $('#f-log').value;
    $('#f-risco25').value = ['alto', 'alto_medio'].indexOf(q.get('risco25')) >= 0 ? q.get('risco25') : '';
    $('#f-choveu').checked = q.get('choveu') === '1';
    f.risco25 = $('#f-risco25').value; f.choveu = $('#f-choveu').checked;
    // Links antigos: ambito=exterior equivale a uf=ZZ; ambito=brasil/todos não restringe.
    const uf = q.get('uf') && UFS[q.get('uf')] ? q.get('uf') : q.get('ambito') === 'exterior' ? 'ZZ' : '';
    $('#f-uf').value = uf;
    montarMunicipios();
    const mun = q.get('mun') || '';
    if (mun) {
      // Aceita o código do TSE ou, de links antigos, o nome do município.
      const lista = (S.meta.partes[uf] || {}).municipios || [];
      const achado = lista.find((m) => m[0] === mun) || lista.find((m) => norm(m[1]) === norm(mun));
      $('#f-mun').value = achado ? achado[0] : '';
    } else $('#f-mun').value = '';
    $('#f-zona').value = q.get('zona') ? so(q.get('zona')) : '';
    $('#q-cep').value = q.get('cep') ? cepFmt(q.get('cep')) : '';
    $('#q-cep').disabled = uf === 'ZZ';
    $('#f-texto').value = q.get('q') || '';
    if (q.has('nivel')) {
      const ns = [];
      q.get('nivel').split(',').forEach((n) => {
        if (NIVEIS.indexOf(n) >= 0) ns.push(n);
        else if (n === 'logs') ns.push('log3', 'log2', 'log1', 'log0');
      });
      if (ns.length || q.get('nivel') === '') f.niveis = new Set(ns);
    }
    if (f.camada === 'logs' && !q.has('nivel')) f.niveis = new Set(NIVEIS);
    const r = Number(q.get('raio'));
    S.raio = RAIOS.indexOf(r) >= 0 ? r : RAIO_PADRAO;
    S.abrir = q.get('l') || '';
    S.alvoLocal = S.abrir;
    f.secaoAlvo = S.abrir ? q.get('s') || '' : '';
    montarRaios();
    montarNiveis();
    return q.get('modo') === 'lista' ? 'lista' : 'mapa';
  }

  function limpar() {
    ['#q-cep', '#f-zona', '#f-texto', '#l-busca'].forEach((s) => { $(s).value = ''; });
    $('#f-uf').value = ''; $('#f-camada').value = 'todas'; $('#f-log').value = '';
    $('#f-risco25').value = ''; $('#f-choveu').checked = false;
    $('#q-cep').disabled = false;
    montarMunicipios();
    S.filtro = { uf: '', mun: '', zona: '', cep: '', texto: '', camada: 'todas', log: '', risco25: '', choveu: false, niveis: new Set(PADRAO_NIVEIS) };
    montarNiveis();
    S.centro = null; S.buscaLista = ''; S.pagina = 1; S.abrir = ''; S.ordemManual = false; S.ordem = { col: 'nivel', dir: 1 };
    if (S.modo === 'lista') trocarModo('mapa'); else aplicarBusca();
  }

  function ligar() {
    if (typeof ResizeObserver !== 'undefined') {
      const altura = new ResizeObserver(() => {
        document.documentElement.style.setProperty('--altura-topo', $('.topo').offsetHeight + 'px');
        if (S.mapa) S.mapa.invalidateSize({ pan: false });
      });
      altura.observe($('.topo'));
    }
    $('#f-busca').addEventListener('submit', (ev) => { ev.preventDefault(); aplicarBusca(true); });
    window.addEventListener('hashchange', () => {
      if (location.hash === S.hashProprio) return;
      const modo = lerHash();
      if (modo !== S.modo) trocarModo(modo); else aplicarBusca(true);
    });
    $('#b-limpar').addEventListener('click', limpar);
    const geo = $('#b-geo');
    if (geo && !navigator.geolocation) geo.hidden = true;
    if (geo) geo.addEventListener('click', () => {
      geo.disabled = true;
      setStatus('Pedindo a localização ao aparelho…');
      navigator.geolocation.getCurrentPosition(async (pos) => {
        geo.disabled = false;
        $('#q-cep').value = ''; $('#f-zona').value = '';
        const seq = ++S.requisicao;
        S.filtro.cep = ''; S.filtro.zona = '';
        if (!await carregarRecorte(seq)) return;
        S.centro = { lat: pos.coords.latitude, lon: pos.coords.longitude, rotulo: 'sua localização', precisao: 'posição informada pelo aparelho; ela não sai dele' };
        S.pagina = 1;
        if (!S.ordemManual) S.ordem = { col: 'dist', dir: 1 };
        atualizar(true);
        if (window.innerWidth < 980) $('#palco').scrollIntoView({ block: 'start', behavior: 'smooth' });
      }, () => { geo.disabled = false; setStatus('Não foi possível obter a localização. Use o CEP, a zona ou a cidade.', true); }, { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 });
    });
    $('#f-uf').addEventListener('change', () => {
      $('#q-cep').value = ''; $('#q-cep').disabled = $('#f-uf').value === 'ZZ';
      $('#f-zona').value = ''; montarMunicipios(); aplicarBusca();
    });
    $('#f-camada').addEventListener('change', () => { $('#f-log').value = ''; aplicarBusca(); });
    $('#f-log').addEventListener('change', function () { if (this.value) $('#f-camada').value = this.value === CRIT_MUDANCA ? 'todas' : this.value.startsWith('historico:') ? 'originais' : 'logs'; else $('#f-camada').value = 'todas'; aplicarBusca(); });
    $('#f-risco25').addEventListener('change', () => { S.pagina = 1; aplicarBusca(); });
    $('#f-choveu').addEventListener('change', () => { S.pagina = 1; aplicarBusca(); });
    $('#f-mun').addEventListener('change', () => aplicarBusca());
    $('#q-cep').addEventListener('input', (ev) => {
      const d = so(ev.target.value).slice(0, 8);
      ev.target.value = d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
    });
    let t;
    $('#f-texto').addEventListener('input', () => { clearTimeout(t); t = setTimeout(() => { S.filtro.texto = $('#f-texto').value.trim(); S.pagina = 1; atualizar(true); }, 250); });
    $('#m-mapa').addEventListener('click', () => trocarModo('mapa'));
    $('#m-lista').addEventListener('click', () => trocarModo('lista'));
    let tl;
    $('#l-busca').addEventListener('input', () => { clearTimeout(tl); tl = setTimeout(() => { S.buscaLista = $('#l-busca').value; S.pagina = 1; atualizar(false); }, 200); });
    $('#l-por-pag').addEventListener('change', () => { S.porPagina = Number($('#l-por-pag').value) || 50; S.pagina = 1; atualizar(false); });
    $('#l-csv').addEventListener('click', exportarCsv);
    $('#painel-fechar').addEventListener('click', fecharPainel);
    document.addEventListener('keydown', (ev) => { if (ev.key === 'Escape') fecharPainel(); });
    $('#l-raio').addEventListener('change', () => { S.listaRaio = $('#l-raio').checked; S.pagina = 1; atualizar(false); });
    const filtros = $('#filtros-toggle');
    if (filtros) filtros.addEventListener('click', () => {
      const aberto = filtros.getAttribute('aria-expanded') === 'true';
      filtros.setAttribute('aria-expanded', String(!aberto));
      document.body.classList.toggle('filtros-abertos', !aberto);
      if (S.mapa) setTimeout(() => S.mapa.invalidateSize(), 0);
    });
  }

  async function iniciar() {
    if (location.protocol === 'file:') {
      setStatus('Esta página lê arquivos de dados e precisa ser aberta por um endereço da web: https://brasil.arvor.co/fiscais_mapa.html.', true);
      return;
    }
    ligar();
    let d;
    try {
      d = await buscar(BASE + 'indice.json');
    } catch (e) {
      setStatus('Não foi possível carregar as seções sinalizadas. Recarregue a página.', true);
      return;
    }
    if (d.formato !== 2) { setStatus('Os dados do mapa estão numa versão antiga. Recarregue a página em alguns minutos.', true); return; }
    S.meta = d;
    montarCriterios();
    montarResumo();
    montarUfs();
    iniciarMapa();
    const modo = lerHash();
    S.filtro.uf = $('#f-uf').value;
    trocarModo(modo, true);
    await aplicarBusca();
  }

  // Gancho só de leitura para os scripts de QA (estado, mapa e filtros); não é API pública.
  window.fiscaisMapa = { estado: S, aplicarBusca, atualizar };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar);
  else iniciar();
})();
