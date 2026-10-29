// Mapa do Brasil do Politize-se: aplicativo estático escrito à mão, sem build.
// Lê o formato 3 de scripts/politize-se-mapa-build.py: um índice e um arquivo de prédios
// por UF. Abre com o país inteiro (todas as UFs em paralelo) e a camada "resultado do
// 2º turno"; a ficha de cada prédio abre as seções direto do arquivo da zona do
// Politize-se (gzip, lido com DecompressionStream). CEP de local de votação, zonas e
// municípios vêm do índice. Distância em linha reta pela fórmula inversa de Vincenty no
// elipsoide WGS84 (detalhe técnico que fica neste comentário e no rodapé da página).
// Privacidade: o endereço da página guarda estado, cidade, zona, texto, camada, raio,
// modo e o prédio aberto; nunca o CEP, a localização nem a seção.
(function () {
  'use strict';

  const BASE = 'assets/politize_se_mapa/';
  const SECOES = 'assets/politize_se/dados/zona/';
  const VERSAO = '20261028-horarios';
  const FORMATO = 3;
  const RAIOS = [1, 2, 5, 10, 15, 20, 30, 50];
  const RAIO_PADRAO = 10;
  const ZOOM_ROTULOS = 15;
  const MAX_ROTULO = 6;
  const UFS = { AC: 'Acre', AL: 'Alagoas', AP: 'Amapá', AM: 'Amazonas', BA: 'Bahia', CE: 'Ceará', DF: 'Distrito Federal', ES: 'Espírito Santo', GO: 'Goiás', MA: 'Maranhão', MT: 'Mato Grosso', MS: 'Mato Grosso do Sul', MG: 'Minas Gerais', PA: 'Pará', PB: 'Paraíba', PR: 'Paraná', PE: 'Pernambuco', PI: 'Piauí', RJ: 'Rio de Janeiro', RN: 'Rio Grande do Norte', RS: 'Rio Grande do Sul', RO: 'Rondônia', RR: 'Roraima', SC: 'Santa Catarina', SP: 'São Paulo', SE: 'Sergipe', TO: 'Tocantins', ZZ: 'Exterior' };
  // Cores das camadas. Divergentes vão do lado "baixo" ao "alto" passando pelo neutro.
  const COR = {
    renda: ['#eef3dc', '#145d57'], renda_ate2: ['#f6efdb', '#946c14'], homicidios: ['#f7e8d6', '#8a321b'],
    neutro: '#ece8dc', semDado: '#a9a9a3',
    resultado: ['#c8412f', '#1f5f9e'], d_fatia: ['#c8412f', '#1f5f9e'], d_comp: ['#b8560f', '#0b7a3b'],
    // Modelo da urna: uma cor por modelo, distintas entre si e do cinza "sem dado".
    modelo: { UE2009: '#7f7f7f', UE2010: '#5f6b3a', UE2011: '#3f6f3f', UE2013: '#b8560f', UE2015: '#0f7f5f', UE2020: '#1f5f9e', UE2022: '#6b4a92', misto: '#e0a400' },
    // Níveis do registro da urna: as mesmas cores do mapa de fiscais.
    log2: { 0: '#9cb9c2', 1: '#4f8fa0', 2: '#0f5d6e', 3: '#5b2a86' },
    log_subiu: ['#d8d4c8', '#b8560f'],
    abst: ['#f2ead2', '#7a3500'], chuva2: ['#e3edf2', '#12466b'], sinal: ['#e4e0d4', '#5b2a86'], urna: ['#d8d4c8', '#5b2a86'], mudanca: ['#d8d4c8', '#a3205f'],
    // Grupo atípico da mistura estatística dos dois turnos: neutro → roxo.
    anomalia: ['#d8d4c8', '#6b4a92'],
  };
  // Regra do grupo (agrupador do mapa) para camadas de presença e de sinal: parcela dos prédios com o atributo.
  const TETO_PARCELA = { sinal: 0.5, urna: 0.25, mudanca: 0.1, log_subiu: 0.1, anomalia: 0.25 };
  const COLS_LISTA = [
    ['uf', 'UF'], ['municipio', 'Cidade'], ['zona', 'Zona'], ['nome', 'Local de votação'], ['secoes', 'Seções'],
    ['fatia_f2', 'Flávio × Lula, 2º turno'], ['d_fatia_pp', 'Mudança contra o 1º turno'], ['comp_pct2', 'Comparecimento'], ['abst_pct2', 'Abstenção'],
    ['renda_mediana_brl', 'Renda domiciliar estimada (R$)'], ['renda_ate2', 'Até 2 salários (%)'], ['homicidios_taxa_100mil', 'Homicídios municipais / 100 mil (2024)'],
    ['escore_max', 'Sinais'], ['log2_max', 'Registro da urna, 2º turno'], ['modelo', 'Modelo da urna'], ['urnas_trocadas', 'Urna trocada'], ['secoes_mudaram', 'Mudou de endereço'], ['secoes_anomalas', 'Grupo atípico'], ['dist', 'Distância'], ['acoes', 'Abrir'],
  ];

  const S = {
    meta: null, porUf: new Map(), locais: [], porId: new Map(), muni: new Map(),
    filtro: { uf: '', mun: '', zona: '', cep: '', texto: '', chuva: false }, camada: 'resultado',
    raio: RAIO_PADRAO, modo: 'mapa', centro: null, abrir: '',
    ordem: { col: 'nome', dir: 1 }, ordemManual: false, pagina: 1, porPagina: 50, buscaLista: '',
    mapa: null, canvas: null, cluster: null, circulo: null, alvo: null, marcadores: new Map(),
    cache: new Map(), requisicao: 0, desenho: 0, loteMapa: null, listaAtual: [], aberto: null, listaRaio: true, secaoSel: null,
  };

  const $ = (s, r) => (r || document).querySelector(s);
  const nf1 = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  const nf0 = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 });
  const vazio = (v) => v === null || v === undefined || v === '';
  const pct = (v) => (vazio(v) ? '' : nf1.format(v) + '%');
  const pp = (v) => (vazio(v) ? '' : (v > 0 ? '+' : '') + nf1.format(v) + ' pontos');
  const plural = (n, um, varios) => nf0.format(n) + ' ' + (n === 1 ? um : varios);
  const km = (v) => (vazio(v) ? '' : (v < 10 ? nf1.format(v) : nf0.format(v)) + ' km');

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
  const SIGLAS = new Set(['EE', 'EEF', 'EEE', 'EEEF', 'EEEFM', 'EEFM', 'EEM', 'EM', 'EMEF', 'EMEI', 'EMEB', 'EMEIEF', 'CEU', 'CIEP', 'CAIC', 'CEI', 'CMEI', 'CEF', 'CED', 'CE', 'ETEC', 'FATEC', 'SESC', 'SESI', 'SENAI', 'SENAC', 'IBGE', 'II', 'III', 'IV', 'VI', 'VII', 'VIII', 'IX', 'XI', 'XII', 'BR', 'PUC', 'USP', 'UNESP', 'UFRJ', 'UFMG', 'APAE', 'CRAS', 'CSU', 'UBS', 'ESF']);
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

  // Lê JSON simples ou gzip (pelos dois primeiros bytes), como o Politize-se.
  function buscar(url) {
    if (url.indexOf(BASE) === 0) url += (url.indexOf('?') < 0 ? '?' : '&') + 'v=' + VERSAO;
    if (S.cache.has(url)) return S.cache.get(url);
    const p = (async () => {
      const r = await fetch(url, { credentials: 'same-origin' });
      if (!r.ok) { const e = new Error('HTTP ' + r.status); e.status = r.status; throw e; }
      const blob = await r.blob();
      const ini = new Uint8Array(await blob.slice(0, 2).arrayBuffer());
      if (ini[0] !== 31 || ini[1] !== 139) return JSON.parse(await blob.text());
      if (!globalThis.DecompressionStream) throw new Error('navegador sem gzip');
      return new Response(blob.stream().pipeThrough(new DecompressionStream('gzip'))).json();
    })();
    p.catch(() => S.cache.delete(url));
    S.cache.set(url, p);
    return p;
  }
  const tabela = (t) => (t && t.colunas ? t.linhas.map((ln) => Object.fromEntries(t.colunas.map((c, i) => [c, ln[i] === undefined ? null : ln[i]]))) : []);

  const H = window.criarHorariosPolitize({ S, buscar, h, nf0 });
  const M = window.criarMovimentoMapa({ S, COR, h });

  /* ------------------------------------------------------------ geodésia */

  // Fórmula inversa de Vincenty no elipsoide WGS84; distância em km. Sem convergência
  // (pontos quase antípodas), usa o grande círculo.
  const { distanciaKm, haversineKm, coordOk } = window.GeoPolitize;

  /* ------------------------------------------------------------ cores */

  const hex = (c) => [1, 3, 5].map((i) => parseInt(c.slice(i, i + 2), 16));
  const paraHex = (rgb) => '#' + rgb.map((x) => Math.round(x).toString(16).padStart(2, '0')).join('');
  const misturar = (a, b, t) => { const x = hex(a), y = hex(b); return paraHex(x.map((v, i) => v + (y[i] - v) * t)); };
  function luminancia(c) {
    const v = hex(c).map((x) => { x /= 255; return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4); });
    return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2];
  }
  // Miolo do grupo: a cor do grupo clareada até o número escuro passar no contraste mínimo (4,5:1);
  // a cor pura fica no anel.
  function fundoLegivel(cor) {
    const tinta = luminancia('#151812') + 0.05;
    for (let t = 0.3; t < 1; t += 0.05) {
      const c = misturar(cor, '#ffffff', t);
      if ((luminancia(c) + 0.05) / tinta >= 4.8) return c;
    }
    return '#ffffff';
  }

  const camada = () => S.meta.camadas[S.camada];
  const valor = (l, k) => l[S.meta.camadas[k || S.camada].campo];

  function corValor(v, k) {
    const c = S.meta.camadas[k || S.camada];
    const par = COR[k || S.camada];
    if (vazio(v)) return COR.semDado;
    if (c.tipo === 'divergente') {
      const t = Math.max(-1, Math.min(1, (v - c.centro) / c.limite));
      return t >= 0 ? misturar(COR.neutro, par[1], Math.pow(t, 0.8)) : misturar(COR.neutro, par[0], Math.pow(-t, 0.8));
    }
    if (c.tipo === 'categoria') return COR[k || S.camada][v] || COR.semDado;
    if (c.tipo === 'sequencial') return misturar(par[0], par[1], Math.max(0, Math.min(1, (v - c.minimo) / (c.maximo - c.minimo))));
    return v > 0 ? par[1] : par[0];
  }

  // Sem boletim do 2º turno (ou sem registro da urna, ou sem a análise estatística), a
  // camada que depende dele fica cinza.
  const semDadoLocal = (l, c) => (c.precisa_bu2 && !l.n_bu2) || (c.precisa_log2 && vazio(l.log2_max)) || (c.precisa_ml && vazio(l[c.campo]));
  function corLocal(l) {
    const c = camada();
    if (semDadoLocal(l, c)) return COR.semDado;
    return corValor(valor(l));
  }

  // Cor do grupo do agrupador: média ponderada pelos eleitores (camadas contínuas) ou
  // parcela dos prédios com o atributo (sinais, urna trocada e mudança de endereço).
  function corGrupo(filhos) {
    const k = S.camada, c = camada();
    if (k === 'pico') return corValor(M.picoGrupo(filhos));
    const validos = filhos.filter((l) => !semDadoLocal(l, c));
    if (!validos.length) return COR.semDado;
    if (c.tipo === 'categoria') {
      // Grupo: o modelo mais comum entre os prédios do grupo.
      const n = {};
      validos.forEach((l) => { const v = valor(l); if (!vazio(v)) n[v] = (n[v] || 0) + 1; });
      const top = Object.keys(n).sort((a, b) => n[b] - n[a])[0];
      return top ? corValor(top) : COR.semDado;
    }
    if (TETO_PARCELA[k] !== undefined) {
      const n = validos.filter((l) => (valor(l) || 0) > 0).length;
      const t = Math.min(1, n / validos.length / TETO_PARCELA[k]);
      return misturar(COR[k][0], COR[k][1], t);
    }
    if (c.agregacao === 'municipios') {
      const municipios = new Map(validos.filter((l) => !vazio(valor(l))).map((l) => [l.uf + '-' + l.mun, valor(l)]));
      const valores = [...municipios.values()];
      return valores.length ? corValor(valores.reduce((a, v) => a + v, 0) / valores.length) : COR.semDado;
    }
    let soma = 0, peso = 0;
    validos.forEach((l) => { const v = valor(l); if (vazio(v)) return; const w = l.aptos2 || l.aptos1 || 1; soma += v * w; peso += w; });
    return peso ? corValor(soma / peso) : COR.semDado;
  }

  /* ------------------------------------------------------------ dados */

  function preparar(uf, d) {
    if (d.formato !== FORMATO) throw new Error('formato');
    const muns = new Map(tabela(d.municipios).map((m) => [m.mun, m]));
    muns.forEach((m, k) => S.muni.set(uf + '-' + k, m));
    const cols = d.locais.colunas;
    const lista = d.locais.linhas.map((ln) => {
      const l = {};
      cols.forEach((c, j) => { l[c] = ln[j]; });
      const partes = String(l.id).split('-');
      l.uf = uf; l.mun = partes[1]; l.zona = Number(partes[2]);
      const m = muns.get(l.mun);
      l.municipio = m ? m.nome : '';
      l.secoes = Array.isArray(l.secoes) ? l.secoes : [];
      l.busca = norm([l.nome, l.endereco, l.bairro, l.municipio, uf, l.cep, 'zona ' + l.zona].join(' '));
      return l;
    });
    S.porUf.set(uf, lista);
    lista.forEach((l) => S.porId.set(l.id, l));
  }

  async function carregarUfs(seq) {
    const f = S.filtro;
    const pedidas = f.uf ? [f.uf] : Object.keys(S.meta.ufs);
    const faltam = pedidas.filter((u) => !S.porUf.has(u) && S.meta.ufs[u]);
    if (faltam.length) {
      let feitos = 0;
      setStatus(f.uf ? 'Carregando ' + UFS[f.uf] + '…' : 'Carregando os locais de votação do país inteiro (0 de ' + faltam.length + ' estados)…');
      await Promise.all(faltam.map((u) => buscar(BASE + S.meta.ufs[u].arquivo).then((d) => {
        preparar(u, d);
        feitos++;
        if (!f.uf && seq === S.requisicao) setStatus('Carregando os locais de votação do país inteiro (' + feitos + ' de ' + faltam.length + ' estados)…');
      })));
    }
    await H.carregar(pedidas);
    await M.carregar(pedidas);
    if (seq !== S.requisicao) return false;
    S.locais = [].concat(...pedidas.map((u) => S.porUf.get(u) || []));
    return true;
  }

  function passaFiltro(l) {
    const f = S.filtro;
    if (f.mun && l.mun !== f.mun) return false;
    if (f.zona && l.zona !== Number(f.zona)) return false;
    if (f.chuva && !(typeof l.chuva2_mm === 'number' && l.chuva2_mm >= (S.meta.chuva_forte_mm || 20))) return false;
    if (f.texto) {
      const termos = norm(f.texto).split(' ');
      for (let i = 0; i < termos.length; i++) if (l.busca.indexOf(termos[i]) < 0) return false;
    }
    return true;
  }

  function comDistancia(ls) {
    ls.forEach((l) => { l.dist = S.centro && coordOk(l) ? distanciaKm(S.centro.lat, S.centro.lon, l.lat, l.lon) : null; });
    return ls;
  }

  /* ------------------------------------------------------------ busca */

  async function geocodificarCep(cep) {
    const arq = await buscar(BASE + 'cep/' + cep.slice(0, 2) + '.json').catch(() => null);
    if (arq && arq.exato && arq.exato[cep]) {
      const e = arq.exato[cep];
      return { lat: e[0], lon: e[1], rotulo: 'o CEP buscado', de: 'do CEP buscado', precisao: e[2] === 1 ? 'o local de votação com este CEP' : 'os ' + e[2] + ' locais de votação com este CEP' };
    }
    const p5 = cep.slice(0, 5);
    if (arq && arq.p5 && arq.p5[p5]) {
      const q = arq.p5[p5];
      return { lat: q[0], lon: q[1], rotulo: 'o CEP buscado', de: 'do CEP buscado', precisao: 'locais de votação com CEP começando em ' + p5 + ', nenhum com o CEP exato' };
    }
    if (arq && arq.p5) {
      let chaves = Object.keys(arq.p5).filter((k) => k.slice(0, 4) === cep.slice(0, 4));
      if (!chaves.length) chaves = Object.keys(arq.p5).filter((k) => k.slice(0, 3) === cep.slice(0, 3));
      if (chaves.length) {
        const alvo = Number(p5);
        chaves.sort((x, y) => Math.abs(Number(x) - alvo) - Math.abs(Number(y) - alvo));
        const g = arq.p5[chaves[0]];
        return { lat: g[0], lon: g[1], rotulo: 'o CEP buscado', de: 'do CEP buscado', precisao: 'aproximação pelo CEP de local de votação mais parecido' };
      }
    }
    return null;
  }

  function centroZona(uf, zona) {
    if (uf === 'ZZ') return null; // a zona do exterior cobre cidades do mundo inteiro
    const z = S.meta.zonas[uf] && S.meta.zonas[uf][String(Number(zona))];
    return z ? { lat: z[0], lon: z[1], rotulo: 'a zona ' + Number(zona) + ' (' + uf + ')', de: 'da zona ' + Number(zona) + ' (' + uf + ')', precisao: 'centro dos ' + z[2] + ' locais de votação da zona' } : null;
  }

  async function aplicarBusca(rolar) {
    if (!S.meta) return;
    const seq = ++S.requisicao;
    const f = S.filtro;
    f.uf = $('#f-uf').value;
    f.mun = $('#f-mun').value;
    f.texto = $('#f-texto').value.trim();
    f.chuva = $('#f-chuva').checked;
    if (H.lerControles()) { fecharPainel(); if (S.mapa) S.mapa.closePopup(); }
    const zonaTxt = so($('#f-zona').value);
    const cep = f.uf === 'ZZ' ? '' : so($('#q-cep').value);
    if (zonaTxt && !f.uf) { setStatus('Escolha o estado para buscar a zona: o número da zona se repete entre os estados.', true); $('#f-uf').focus(); return; }
    if (cep && cep.length !== 8) { setStatus('O CEP precisa de 8 números.', true); $('#q-cep').focus(); return; }
    f.zona = zonaTxt ? String(Number(zonaTxt)) : '';
    f.cep = cep;
    let centro = null;
    try {
      if (!await carregarUfs(seq)) return;
      if (cep) {
        centro = await geocodificarCep(cep);
        if (seq !== S.requisicao) return;
        if (!centro) { setStatus('Nenhum local de votação tem CEP parecido com ' + cepFmt(cep) + '. Tente a zona ou a cidade.', true); return; }
      } else if (f.zona) {
        centro = centroZona(f.uf, f.zona);
        if (!centro && f.uf !== 'ZZ') { setStatus('A zona ' + f.zona + ' não aparece em ' + (UFS[f.uf] || f.uf) + '. Confira o número no título de eleitor.', true); return; }
      }
    } catch (e) {
      console.error(e);
      if (seq !== S.requisicao) return;
      setStatus(e && e.message === 'formato' ? 'Os dados do mapa estão numa versão diferente da página. Recarregue em alguns minutos.' : 'Não foi possível carregar os dados agora. Tente de novo.', true);
      return;
    }
    if (seq !== S.requisicao) return;
    S.centro = centro;
    S.pagina = 1;
    if (!S.ordemManual) S.ordem = centro ? { col: 'dist', dir: 1 } : { col: 'nome', dir: 1 };
    atualizar(true);
    if (window.innerWidth < 980 && rolar) $('#palco').scrollIntoView({ block: 'start', behavior: 'smooth' });
  }

  /* ------------------------------------------------------------ mapa */

  function iniciarMapa() {
    if (typeof L === 'undefined' || typeof L.markerClusterGroup !== 'function') {
      $('#mapa').replaceChildren(h('p', { class: 'aviso' }, 'A biblioteca do mapa não carregou. A lista continua disponível em "Ver em lista".'));
      return;
    }
    S.mapa = L.map('mapa', { zoomControl: true, minZoom: 2, worldCopyJump: true }).setView([-14.5, -52], 4);
    S.canvas = L.canvas({ padding: 0.5 });
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
      disableClusteringAtZoom: 16,
      iconCreateFunction: (c) => {
        const filhos = c.getAllChildMarkers().map((m) => m.options.local);
        const cor = corGrupo(filhos);
        const n = c.getChildCount();
        const tam = n < 10 ? 34 : n < 100 ? 40 : n < 1000 ? 46 : 54;
        return L.divIcon({ html: '<span style="background:' + fundoLegivel(cor) + ';border-color:' + cor + '">' + nf0.format(n) + '</span>', className: 'grupo', iconSize: [tam, tam] });
      },
    });
    S.mapa.addLayer(S.cluster);
    S.mapa.on('zoomend moveend', atualizarRotulos);
  }

  function raioPonto(l) {
    const a = l.aptos2 || l.aptos1 || 0;
    return 5 + Math.min(4, Math.sqrt(a) / 16);
  }

  function marcador(l) {
    let m = S.marcadores.get(l.id);
    if (!m) {
      m = L.circleMarker([l.lat, l.lon], { renderer: S.canvas, radius: raioPonto(l), color: '#ffffff', weight: 1.5, fillOpacity: 0.95, fillColor: corLocal(l), local: l });
      if (telaPequena()) {
        // No celular a ficha é um painel fixo fora do mapa: um popup maior que a tela empurraria o ponto.
        m.on('click', (ev) => { L.DomEvent.stop(ev); abrirPainel(m.options.local, m); });
      } else {
        m.bindPopup(() => ficha(m.options.local), { maxWidth: 560, minWidth: 320, autoPanPadding: [24, 24], className: 'popup-ficha' });
        m.on('popupopen', () => { S.aberto = l.id; carregarSecoes(m.options.local, m.getPopup().getElement()); gravarHash(); });
        m.on('popupclose', () => { if (S.aberto === l.id) { S.aberto = null; gravarHash(); } });
      }
      S.marcadores.set(l.id, m);
    } else { m.options.local = l; m.setStyle({ fillColor: corLocal(l), radius: raioPonto(l) }); }
    return m;
  }

  function limparMarcadores() {
    S.desenho++;
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
      S.cluster.addLayers(lista.slice(offset, offset + 5000));
      offset += 5000;
      if (offset < lista.length) S.loteMapa = setTimeout(lote, 16);
      else { S.loteMapa = null; $('#mapa').setAttribute('aria-busy', 'false'); atualizarRotulos(); abrirPendente(); }
    }
    if (lista.length) S.loteMapa = setTimeout(lote, 0);
  }

  function rotuloSecoes(l) {
    const nums = l.secoes;
    const txt = nums.slice(0, MAX_ROTULO).join(', ') + (nums.length > MAX_ROTULO ? ' +' + (nums.length - MAX_ROTULO) : '');
    const label = h('span', {}, (nums.length === 1 ? 'Seção ' : 'Seções ') + txt);
    if (S.camada === 'pico') label.append(h('small', {}, vazio(l.pico_hora) ? 'Sem horário utilizável' : 'Pico: ' + S.meta.camadas.pico.nomes[l.pico_hora]));
    if (camada().grupo) {
      const v = valor(l);
      label.append(h('small', {}, S.camada === 'renda' ? window.PolitizeTerritorio.reais(v) : S.camada === 'renda_ate2' ? window.PolitizeTerritorio.perc(v) + ' até 2 salários' : window.PolitizeTerritorio.fmt(v, 2) + '/100 mil · município'));
    }
    return label;
  }

  // Os números das seções aparecem escritos no mapa só a partir do zoom de quarteirão.
  function atualizarRotulos() {
    if (!S.mapa || !S.cluster) return;
    const mostrar = S.mapa.getZoom() >= ZOOM_ROTULOS;
    $('#mapa').classList.toggle('com-rotulos', mostrar);
    if (!mostrar && !S.comRotulos) return;
    S.comRotulos = mostrar;
    const limites = S.mapa.getBounds();
    S.marcadores.forEach((m) => {
      const t = m.getTooltip();
      // Ponto em círculo não tem ícone: está visível, fora de grupo, quando o agrupador o pôs no mapa.
      const visivel = mostrar && Boolean(m._map) && limites.contains(m.getLatLng());
      if (visivel) {
        if (!t) m.bindTooltip(rotuloSecoes(m.options.local), { permanent: true, direction: 'bottom', offset: [0, 6], className: 'rotulo-secoes', interactive: false });
        else m.setTooltipContent(rotuloSecoes(m.options.local));
        if (!m.isTooltipOpen()) m.openTooltip();
      } else if (t && m.isTooltipOpen()) m.closeTooltip();
    });
  }

  function abrirPendente() {
    if (!S.abrir) return;
    const id = S.abrir;
    const m = S.marcadores.get(id);
    S.abrir = '';
    if (!m || !S.cluster.hasLayer(m)) {
      const l = S.porId.get(id);
      if (l && !coordOk(l)) { setStatus('Este local não tem coordenada no cadastro; ele aparece na lista.', true); return; }
      setStatus('O local pedido não está no mapa com a busca atual. Use "Limpar".', true);
      return;
    }
    const abrir = () => (telaPequena() ? abrirPainel(m.options.local, m) : m.openPopup());
    // O agrupador não sabe mostrar ponto em círculo: o mapa vai ao quarteirão, onde não há grupo.
    if (!m._map) S.mapa.setView(m.getLatLng(), ZOOM_ROTULOS + 2, { animate: false });
    if (m._map) abrir();
    else setTimeout(() => (m._map ? abrir() : setStatus('Não foi possível abrir o local pedido. Aproxime o mapa e toque no ponto.', true)), 120);
  }

  const telaPequena = () => window.matchMedia('(max-width: 979px)').matches;

  function abrirPainel(l, m) {
    const corpo = $('#painel-corpo');
    corpo.replaceChildren(ficha(l));
    $('#painel').hidden = false;
    document.body.classList.add('painel-aberto');
    S.aberto = l.id;
    carregarSecoes(l, corpo);
    gravarHash();
    if (m && S.mapa) S.mapa.panTo(m.getLatLng(), { animate: false });
    corpo.scrollTop = 0;
    $('#painel-fechar').focus({ preventScroll: true });
  }

  function fecharPainel() {
    if ($('#painel').hidden) return;
    $('#painel').hidden = true;
    document.body.classList.remove('painel-aberto');
    S.aberto = null;
    gravarHash();
  }

  function desenharMapa(ls, enquadrar) {
    if (!S.mapa) return { locais: 0 };
    const noRaio = ls.filter((l) => coordOk(l) && (!S.centro || l.dist <= S.raio));
    const lista = noRaio.map(marcador);
    adicionarMarcadores(lista);
    if (S.circulo) { S.mapa.removeLayer(S.circulo); S.circulo = null; }
    if (S.alvo) { S.mapa.removeLayer(S.alvo); S.alvo = null; }
    if (S.centro) {
      S.circulo = L.circle([S.centro.lat, S.centro.lon], { radius: S.raio * 1000, color: '#151812', weight: 2, dashArray: '6 6', fill: true, fillOpacity: 0.04, interactive: false }).addTo(S.mapa);
      S.alvo = L.marker([S.centro.lat, S.centro.lon], { icon: L.divIcon({ className: 'alvo', iconSize: [22, 22], html: '' }), keyboard: false, interactive: false }).addTo(S.mapa);
    }
    const alvo = S.abrir ? S.porId.get(S.abrir) : null;
    if (enquadrar) {
      if (alvo && coordOk(alvo)) S.mapa.setView([alvo.lat, alvo.lon], ZOOM_ROTULOS + 2, { animate: false });
      else if (S.centro) S.mapa.fitBounds(S.circulo.getBounds(), { padding: [24, 24], maxZoom: 16 });
      else if (noRaio.length) {
        // Sem estado escolhido, o quadro é o Brasil; o exterior segue no mapa, fora do quadro inicial.
        const br = noRaio.filter((l) => l.uf !== 'ZZ');
        const base = br.length ? br : noRaio;
        let s = 90, w = 180, n = -90, e = -180;
        base.forEach((l) => { s = Math.min(s, l.lat); n = Math.max(n, l.lat); w = Math.min(w, l.lon); e = Math.max(e, l.lon); });
        S.mapa.fitBounds([[s, w], [n, e]], { padding: [30, 30], maxZoom: 15 });
      }
    }
    return { locais: lista.length, semBu: noRaio.filter((l) => !l.n_bu2).length };
  }

  // Troca de camada: só recolore, sem recarregar nem reagrupar os pontos.
  async function recolorir() {
    if (S.camada === 'pico') {
      try { await M.carregar(); atualizar(false); }
      catch { setStatus('Os horários não carregaram. Selecione a camada novamente para tentar.', true); return; }
    }
    S.marcadores.forEach((m) => m.setStyle({ fillColor: corLocal(m.options.local) }));
    if (S.cluster) S.cluster.refreshClusters();
    atualizarRotulos();
    document.querySelectorAll('[data-lente]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.lente === S.camada)));
    document.querySelectorAll('input[name=camada]').forEach((b) => { b.checked = b.value === S.camada; });
    desenharLegenda();
    if (S.modo === 'lista') atualizar(false);
    gravarHash();
  }

  /* ------------------------------------------------------------ ficha do prédio */

  const { ficha, carregarSecoes, textoModelo, linkPolitize, nomeNivel, predominante } = window.criarFichaPolitize({ S, h, caixa, distanciaKm, coordOk, cepFmt, plural, nf0, nf1, km, pct, pp, vazio, buscar, SECOES, tabela, copiar, H });

  function copiar(texto, botao) {
    const ok = () => { const t = botao.textContent; botao.textContent = 'Link copiado'; setTimeout(() => { botao.textContent = t; }, 1500); };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(texto).then(ok, () => window.prompt('Copie o link:', texto));
    else window.prompt('Copie o link:', texto);
  }

  /* ------------------------------------------------------------ legenda e camadas */

  function montarCamadas() {
    const box = $('#camadas');
    const grupos = new Map();
    Object.entries(S.meta.camadas).forEach(([k, c]) => {
      const grupo = c.grupo || (k === 'chuva2' ? 'Clima' : 'Eleição e urnas');
      if (!grupos.has(grupo)) grupos.set(grupo, []);
      grupos.get(grupo).push(h('label', { class: 'camada' },
        h('input', { type: 'radio', name: 'camada', value: k, checked: k === S.camada, onchange: () => { S.camada = k; recolorir(); } }),
        h('span', {}, c.nome)));
    });
    box.replaceChildren(...['Economia e segurança', 'Clima', 'Eleição e urnas'].filter((g) => grupos.has(g)).map((g) =>
      h('fieldset', { class: 'camada-grupo' }, h('legend', {}, g), grupos.get(g))));
  }

  function desenharLegenda() {
    const c = camada(), k = S.camada, par = COR[k];
    document.querySelectorAll('[data-lente]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.lente === k)));
    const faixa = $('#mapa-escala');
    faixa.replaceChildren(...[h('b', {}, c.nome), c.tipo === 'sequencial' || c.tipo === 'divergente' ? [h('span', { class: 'mapa-mini-escala', style: 'background:linear-gradient(90deg,' + par[0] + ',' + par[1] + ')', 'aria-hidden': 'true' }), h('span', {}, c.baixo + ' → ' + c.alto)] : null, h('small', {}, c.agregacao === 'municipios' ? 'Dado municipal · 2024 · cinza: sem dado' : c.grupo ? 'Estimativa PNAD · cinza: sem dado' : 'Cinza: sem dado aplicável')].flat().filter(Boolean));
    if (k === 'pico') faixa.append(M.escala());
    const itens = [];
    if (c.tipo === 'divergente') {
      itens.push(h('div', { class: 'escala', style: 'background:linear-gradient(90deg,' + par[0] + ',' + COR.neutro + ',' + par[1] + ')', role: 'img', 'aria-label': c.baixo + ' à esquerda, ' + c.alto + ' à direita' }));
      itens.push(h('div', { class: 'escala-rot' }, h('span', {}, c.baixo), h('span', {}, c.alto)));
    } else if (c.tipo === 'sequencial') {
      itens.push(h('div', { class: 'escala', style: 'background:linear-gradient(90deg,' + par[0] + ',' + par[1] + ')', role: 'img', 'aria-label': c.baixo + ' a ' + c.alto }));
      itens.push(h('div', { class: 'escala-rot' }, h('span', {}, c.baixo), h('span', {}, c.alto)));
    } else if (k === 'pico') {
      itens.push(M.legenda());
    } else if (k === 'log2') {
      const lg = S.meta.logs_2t || {};
      const pn = lg.predios_por_nivel || {};
      itens.push(h('ul', { class: 'legenda-itens' }, c.categorias.map((n) => h('li', {},
        h('span', { class: 'bolinha', style: 'background:' + COR.log2[n] }),
        h('span', {}, h('b', {}, c.nomes[n]), ': ' + plural(pn[n] || 0, 'prédio', 'prédios'))))));
      if (!lg.predios_com_log) itens.push(h('p', { class: 'ajuda' }, 'Os registros das urnas do 2º turno ainda não entraram nos dados: todos os prédios ficam em cinza.'));
    } else if (c.tipo === 'categoria') {
      const nac = (S.meta.modelos_urna || {}).nacional || { secoes: {}, predios: {} };
      itens.push(h('ul', { class: 'legenda-itens' }, c.categorias.filter((m) => nac.secoes[m] || nac.predios[m]).map((m) => h('li', {},
        h('span', { class: 'bolinha', style: 'background:' + COR.modelo[m] }),
        h('span', {}, h('b', {}, m === 'misto' ? 'Misto' : m), ', ' + c.nomes[m] + ': ' + (m === 'misto' ? plural(nac.predios[m] || 0, 'prédio', 'prédios') : plural(nac.secoes[m] || 0, 'seção', 'seções') + ' no país'))))));
    } else {
      itens.push(h('ul', { class: 'legenda-itens' }, h('li', {}, h('span', { class: 'bolinha', style: 'background:' + par[1] }), c.alto), h('li', {}, h('span', { class: 'bolinha', style: 'background:' + par[0] }), c.baixo)));
    }
    if (k === 'log_subiu' && S.meta.logs_2t) itens.push(h('p', {}, h('b', {}, plural(S.meta.logs_2t.predios_subiu || 0, 'prédio', 'prédios')), ' no país com alguma seção que subiu de nível.'));
    if (k === 'anomalia') {
      const am = S.meta.anomalia_ml || {};
      const ml = (S.meta.catalogos || {}).ml || {};
      if (!am.disponivel) itens.push(h('p', { class: 'ajuda' }, 'A análise estatística dos dois turnos ainda não entrou nos dados: todos os prédios ficam em cinza.'));
      else itens.push(h('p', {}, h('b', {}, plural(am.anomalas || 0, 'seção', 'seções')), ' no grupo atípico do país, entre ' + nf0.format(am.secoes || 0) + ' seções analisadas' + (ml.k ? ', em ' + ml.k + ' grupos' : '') + '.'));
      itens.push(h('p', { class: 'ajuda' }, ml.rotulo_casa || 'Atipicidade estatística não é irregularidade: o grupo pede explicação, não prova nada.'));
    }
    const cinza = c.precisa_ml ? 'Cinza: a análise estatística ainda não cobre o prédio, ou ainda sem boletim do 2º turno.' : c.precisa_log2 ? 'Cinza: registro da urna do 2º turno ainda não lido.' : c.precisa_bu2 ? 'Cinza: ainda sem boletim do 2º turno, ou prédio com menos de 30 eleitores.' : 'Cinza: sem dado.';
    const grupo = k === 'pico' ? 'Nos grupos, a cor mostra o pico da soma dos votos por hora de todas as seções cobertas.' : c.agregacao === 'municipios' ? 'Nos grupos de pontos, a cor é a média simples das taxas dos municípios representados, contados uma vez cada. Não é uma taxa regional.' : c.tipo === 'categoria' ? 'Nos grupos de pontos, a cor é a categoria mais comum entre os prédios do grupo.' : TETO_PARCELA[k] !== undefined ? 'Nos grupos de pontos, a cor é a parcela dos prédios do grupo com o atributo.' : 'Nos grupos de pontos, a cor é a média dos prédios do grupo, ponderada pelos eleitores.';
    if (c.grupo) {
      const lista = H.filtrar(S.locais.filter(passaFiltro));
      const cobertos = lista.filter((l) => !vazio(valor(l))).length;
      itens.push(h('p', { class: 'territorio-cobertura' }, plural(cobertos, 'prédio com dado', 'prédios com dado') + ' de ' + nf0.format(lista.length) + ' no recorte selecionado.'));
    }
    if (H.ativo()) itens.push(h('p', { class: 'ajuda' }, 'As contagens nacionais desta legenda são a referência completa, sem o filtro de horários. Os pontos e seus placares consideram só as seções selecionadas.'));
    $('#legenda').replaceChildren(...itens, h('p', {}, c.explica), h('ul', { class: 'legenda-itens' }, h('li', {}, h('span', { class: 'bolinha bolinha-cinza' }), cinza)), h('p', { class: 'ajuda' }, grupo + ' O tamanho do ponto cresce com o número de eleitores.'));
  }

  /* ------------------------------------------------------------ lista */

  // Valor ausente vai sempre para o fim da lista, nas duas direções.
  function valorOrdem(l, col, dir) {
    if (col === 'pico_hora') return vazio(l.pico_hora) ? dir * 1e12 : l.pico_hora === 'empate' ? 24 : Number(l.pico_hora);
    if (col === 'secoes') return l.n_secoes || 0;
    if (col === 'acoes') return coordOk(l) ? 0 : 1;
    const v = col === 'dist' ? l.dist : l[col];
    if (!vazio(v)) return v;
    return ['nome', 'municipio', 'uf'].indexOf(col) >= 0 ? '' : dir * 1e12;
  }

  function ordenar(ls) {
    const c = S.ordem.col, d = S.ordem.dir;
    const col = new Intl.Collator('pt-BR', { numeric: true, sensitivity: 'base' });
    return ls.slice().sort((a, b) => {
      const x = valorOrdem(a, c, d), y = valorOrdem(b, c, d);
      let r = typeof x === 'number' && typeof y === 'number' ? x - y : col.compare(String(x), String(y));
      if (r === 0) r = col.compare(a.uf + a.municipio, b.uf + b.municipio) || a.zona - b.zona || col.compare(a.nome || '', b.nome || '');
      return r * d;
    });
  }

  function desenharLista(ls) {
    $('#l-raio-caixa').hidden = !S.centro;
    if (S.centro) { $('#l-raio').checked = S.listaRaio; $('#l-raio-txt').textContent = 'Só até ' + S.raio + ' km ' + S.centro.de; }
    let base = S.centro && S.listaRaio ? ls.filter((l) => l.dist !== null && l.dist <= S.raio) : ls;
    const q = norm(S.buscaLista);
    if (q) { const termos = q.split(' '); base = base.filter((l) => termos.every((t) => l.busca.indexOf(t) >= 0)); }
    const todas = ordenar(base);
    S.listaAtual = todas;
    const n = todas.length;
    const paginas = Math.max(1, Math.ceil(n / S.porPagina));
    if (S.pagina > paginas) S.pagina = paginas;
    const ini = (S.pagina - 1) * S.porPagina;
    const pag = todas.slice(ini, ini + S.porPagina);
    const semCoord = todas.filter((l) => !coordOk(l)).length;
    $('#l-resumo').textContent = plural(n, 'local de votação', 'locais de votação') + (S.centro && S.listaRaio ? ' até ' + S.raio + ' km ' + S.centro.de : ' pela busca, sem limite de distância') + (semCoord ? ', ' + nf0.format(semCoord) + ' sem coordenada' : '') + '.';
    const cols = S.camada === 'pico' ? [['pico_hora', 'Pico de votação, Brasília'], ...COLS_LISTA] : COLS_LISTA;
    $('#tabela thead').replaceChildren(h('tr', {}, cols.map((c) => {
      const ativo = S.ordem.col === c[0];
      return h('th', { scope: 'col', 'aria-sort': ativo ? (S.ordem.dir === 1 ? 'ascending' : 'descending') : 'none' },
        h('button', { type: 'button', class: 'ord', onclick: () => {
          if (S.ordem.col === c[0]) S.ordem.dir = -S.ordem.dir; else { S.ordem.col = c[0]; S.ordem.dir = 1; }
          S.ordemManual = true; S.pagina = 1; atualizar(false);
        } }, c[1], h('span', { class: 'seta', 'aria-hidden': 'true' }, ativo ? (S.ordem.dir === 1 ? ' ▲' : ' ▼') : '')));
    })));
    $('#tabela tbody').replaceChildren(...pag.map((l) => h('tr', {},
      S.camada === 'pico' ? h('td', {}, S.meta.camadas.pico.nomes[l.pico_hora] || 'Sem horário utilizável', h('small', {}, l.mov_cobertas + ' de ' + l.mov_total + ' seções')) : null,
      h('td', {}, l.uf), h('td', {}, caixa(l.municipio)), h('td', { class: 'num' }, String(l.zona)),
      h('td', {}, caixa(l.nome), h('small', {}, [caixa(l.endereco), caixa(l.bairro)].filter(Boolean).join(' · '))),
      h('td', { class: 'num' }, String(l.n_secoes || 0), h('small', {}, l.n_bu2 ? l.n_bu2 + ' com 2º turno' : 'sem 2º turno')),
      h('td', { class: 'num' }, vazio(l.fatia_f2) ? '' : [h('span', { class: 'tf' }, pct(l.fatia_f2)), ' × ', h('span', { class: 'tl' }, pct(100 - l.fatia_f2))]),
      h('td', { class: 'num' }, pp(l.d_fatia_pp)),
      h('td', { class: 'num' }, pct(l.comp_pct2), vazio(l.d_comp_pp) ? null : h('small', {}, pp(l.d_comp_pp))),
      h('td', { class: 'num' }, pct(l.abst_pct2)),
      h('td', { class: 'num' }, window.PolitizeTerritorio.reais(l.renda_mediana_brl)),
      h('td', { class: 'num' }, window.PolitizeTerritorio.perc(l.renda_ate2)),
      h('td', { class: 'num' }, window.PolitizeTerritorio.fmt(l.homicidios_taxa_100mil, 2)),
      h('td', { class: 'num' }, l.n_bu2 ? String(l.escore_max || 0) : '', l.secoes_sinal ? h('small', {}, plural(l.secoes_sinal, 'seção', 'seções')) : null),
      h('td', {}, vazio(l.log2_max) ? '' : nomeNivel(l.log2_max), vazio(l.log1_max) ? null : h('small', {}, '1º turno: ' + nomeNivel(l.log1_max))),
      h('td', {}, textoModelo(l)),
      h('td', { class: 'num' }, l.urnas_trocadas ? String(l.urnas_trocadas) : ''),
      h('td', { class: 'num' }, l.secoes_mudaram ? String(l.secoes_mudaram) : ''),
      h('td', { class: 'num' }, l.secoes_anomalas ? String(l.secoes_anomalas) : ''),
      h('td', { class: 'num' }, km(l.dist)),
      h('td', {},
        h('a', { href: linkPolitize(l, l.secao_link) }, 'Politize-se'),
        coordOk(l) ? h('small', {}, h('a', { href: '#', onclick: (ev) => { ev.preventDefault(); S.abrir = l.id; trocarModo('mapa'); } }, 'Ver no mapa')) : h('small', { class: 'sem' }, 'sem coordenada')))));
    if (!pag.length) $('#tabela tbody').replaceChildren(h('tr', {}, h('td', { colspan: String(cols.length) }, 'Nenhum local de votação com essa busca.')));
    desenharPaginas(paginas);
  }

  function desenharPaginas(total) {
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
    $('#paginas').replaceChildren(...botoes);
  }

  async function exportarCsv() {
    const seq = S.requisicao;
    try { await H.carregar([...new Set(S.listaAtual.map((l) => l.uf))], true); }
    catch (e) { setStatus('Não foi possível carregar os horários para a planilha. Tente de novo.', true); return; }
    if (seq !== S.requisicao) return;
    const cab = ['uf', 'cidade', 'zona', 'local', 'endereco', 'bairro', 'cep', 'lat', 'lon', 'distancia_km_linha_reta', 'secoes', 'secoes_com_2o_turno', 'eleitores', 'flavio_entre_os_dois_2t_pct', 'flavio_entre_os_dois_1t_mesmas_secoes_pct', 'mudanca_pontos', 'comparecimento_2t_pct', 'mudanca_comparecimento_pontos', 'abstencao_2t_pct', 'maior_numero_de_sinais_numa_secao', 'secoes_com_sinal', 'registro_urna_1t_nivel_max', 'registro_urna_2t_nivel_max', 'registro_urna_secoes_que_subiram', 'modelo_urna_predominante', 'modelos_urna_no_predio', 'urnas_trocadas', 'secoes_que_mudaram_de_endereco', 'secoes_no_grupo_atipico_estatistica', 'renda_domiciliar_mediana_estimada_brl_202607', 'renda_domiciliar_ate2sm_estimada_pct', 'homicidios_municipio_por100mil_2024', 'politize_se', 'google_maps'];
    const dec = (v, c) => (vazio(v) ? '' : typeof v === 'number' ? v.toFixed(c).replace('.', ',') : String(v));
    const esc = (v) => { const s = vazio(v) ? '' : String(v); return /[";\n\r]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; };
    cab.push(...H.colunasCsv);
    if (S.camada === 'pico') cab.push(...M.colunasCsv);
    const linhas = [cab.join(';')];
    (S.listaAtual || []).forEach((l) => {
      linhas.push([l.uf, l.municipio, l.zona, l.nome, l.endereco, l.bairro, l.cep, coordOk(l) ? dec(l.lat, 5) : '', coordOk(l) ? dec(l.lon, 5) : '', dec(l.dist, 2),
        l.n_secoes, l.n_bu2, l.aptos2 || l.aptos1, dec(l.fatia_f2, 1), dec(l.fatia_f1_par, 1), dec(l.d_fatia_pp, 1), dec(l.comp_pct2, 1), dec(l.d_comp_pp, 1), dec(l.abst_pct2, 1),
        l.n_bu2 ? l.escore_max : '', l.secoes_sinal, l.log1_max, l.log2_max, l.log_subiu, predominante(l), (l.modelos || []).map((m) => m[0] + ':' + m[1]).join('|'), l.urnas_trocadas, l.secoes_mudaram, l.secoes_anomalas,
        dec(l.renda_mediana_brl, 0), dec(l.renda_ate2, 1), dec(l.homicidios_taxa_100mil, 2),
        'https://brasil.arvor.co/' + linkPolitize(l, l.secao_link), coordOk(l) ? 'https://www.google.com/maps/search/?api=1&query=' + l.lat + ',' + l.lon : '', ...H.csv(l), ...M.csv(l)].map(esc).join(';'));
    });
    const blob = new Blob(['﻿' + linhas.join('\r\n')], { type: 'text/csv;charset=utf-8' });
    const a = h('a', { href: URL.createObjectURL(blob), download: 'locais_de_votacao_' + new Date().toISOString().slice(0, 10) + '.csv' });
    document.body.appendChild(a);
    a.click();
    setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
  }

  /* ------------------------------------------------------------ estado e controles */

  function setStatus(t, erro) {
    const s = $('#status');
    s.textContent = t;
    s.classList.toggle('erro', Boolean(erro));
  }

  function atualizar(enquadrar) {
    if (!S.meta) return;
    const ls = comDistancia(M.aplicar(H.filtrar(S.locais.filter(passaFiltro))));
    H.resumo(ls);
    desenharLegenda();
    const semCoord = ls.filter((l) => !coordOk(l)).length;
    if (S.modo === 'mapa') {
      const res = desenharMapa(ls, enquadrar);
      const semBu = res.semBu;
      const onde = S.centro ? ' até ' + S.raio + ' km ' + S.centro.de + ' (' + S.centro.precisao + ')' : '';
      setStatus(plural(res.locais || 0, 'local de votação no mapa', 'locais de votação no mapa') + onde + '.' +
        (semBu && camada().precisa_bu2 ? ' ' + nf0.format(semBu) + ' ainda sem boletim do 2º turno, em cinza.' : '') +
        (semCoord && !S.centro ? ' ' + nf0.format(semCoord) + ' sem coordenada ficam só na lista.' : '') +
        (S.centro && ls.length && !res.locais ? ' Aumente a distância ou veja em lista.' : ''));
    } else {
      desenharLista(ls);
      setStatus(plural(S.listaAtual.length, 'local de votação na lista', 'locais de votação na lista') + (S.centro && S.listaRaio ? ', até ' + S.raio + ' km do ponto buscado.' : '.'));
    }
    gravarHash();
  }

  function trocarModo(m, semAtualizar) {
    S.modo = m;
    if (m === 'lista') limparMarcadores();
    $('#m-mapa').setAttribute('aria-pressed', String(m === 'mapa'));
    $('#m-lista').setAttribute('aria-pressed', String(m === 'lista'));
    $('#mapa').hidden = m !== 'mapa';
    $('#lista').hidden = m !== 'lista';
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
    Object.keys(UFS).forEach((u) => { if (S.meta.ufs[u]) sel.appendChild(h('option', { value: u }, u === 'ZZ' ? 'Exterior' : u + ' · ' + UFS[u])); });
  }

  function montarMunicipios() {
    const uf = $('#f-uf').value;
    const sel = $('#f-mun');
    if (!uf || !S.meta.ufs[uf]) { sel.replaceChildren(h('option', { value: '' }, 'Escolha o estado primeiro')); sel.disabled = true; return; }
    const lista = S.meta.ufs[uf].municipios;
    sel.replaceChildren(h('option', { value: '' }, 'Todas (' + lista.length + ')'), ...lista.map((m) => h('option', { value: m[0] }, m[1])));
    sel.disabled = false;
  }

  function montarResumo() {
    const r = S.meta.resumo, cob = (S.meta.cobertura || {}).nacional || {};
    $('#n-locais').textContent = nf0.format(r.locais);
    $('#n-bu2').textContent = nf0.format(r.com_bu2);
    $('#n-secoes').textContent = nf0.format(r.secoes_bu2);
    const ufs = (S.meta.cobertura || {}).ufs || {};
    const faltam = Object.keys(ufs).filter((u) => !ufs[u].com_bu_2t).map((u) => (u === 'ZZ' ? 'exterior' : u));
    $('#cobertura').textContent = cob.coleta_completa ? 'Leitura dos boletins do 2º turno completa.' :
      'Leitura dos boletins do 2º turno em andamento: ' + nf0.format(cob.com_bu_2t || 0) + ' de ' + nf0.format(cob.secoes || 0) + ' seções (' + pct(cob.pct) + ')' + (faltam.length ? '; ainda sem nenhum boletim: ' + faltam.join(', ') : '') + '. Prédio sem boletim do 2º turno aparece em cinza.';
    $('#gerado-em').textContent = 'Dados gerados em ' + new Date(S.meta.gerado_em).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short', timeZone: 'America/Sao_Paulo' }) + ' (horário de Brasília).';
  }

  function gravarHash() {
    if (S.semGravar) return;
    const f = S.filtro, p = [];
    if (f.uf) p.push('uf=' + f.uf);
    if (f.mun) p.push('mun=' + encodeURIComponent(f.mun));
    if (f.zona) p.push('zona=' + f.zona);
    if (f.texto) p.push('q=' + encodeURIComponent(f.texto));
    if (f.chuva) p.push('chuva=1');
    H.gravarHash(p);
    if (S.camada !== S.meta.camada_padrao) p.push('camada=' + S.camada);
    if (S.raio !== RAIO_PADRAO) p.push('raio=' + S.raio);
    if (S.modo === 'lista') p.push('modo=lista');
    const aberto = S.abrir || S.aberto;
    if (aberto) p.push('l=' + encodeURIComponent(aberto));
    const novo = p.length ? '#' + p.join('&') : '';
    if (novo === location.hash || (!novo && !location.hash)) return;
    S.hashProprio = novo;
    try { history.replaceState(null, '', location.pathname + location.search + novo); } catch (e) { /* navegador embutido */ }
  }

  function lerHash() {
    // o estado vive no #; um link com ?camada=... (sem #) também é aceito na abertura
    const q = new URLSearchParams(location.hash.slice(1) || location.search.slice(1));
    let uf = q.get('uf') && S.meta.ufs[q.get('uf').toUpperCase()] ? q.get('uf').toUpperCase() : '';
    const l = q.get('l') || '';
    if (l && !uf && /^[A-Z]{2}-/.test(l) && S.meta.ufs[l.slice(0, 2)]) uf = l.slice(0, 2);
    $('#f-uf').value = uf;
    montarMunicipios();
    const mun = q.get('mun') || '';
    $('#f-mun').value = mun && S.meta.ufs[uf] && S.meta.ufs[uf].municipios.some((m) => m[0] === mun) ? mun : '';
    $('#f-zona').value = q.get('zona') ? so(q.get('zona')) : '';
    $('#q-cep').value = '';
    $('#q-cep').disabled = uf === 'ZZ';
    $('#f-texto').value = q.get('q') || '';
    $('#f-chuva').checked = q.get('chuva') === '1';
    H.lerHash(q);
    S.camada = S.meta.camadas[q.get('camada')] ? q.get('camada') : S.meta.camada_padrao;
    const r = Number(q.get('raio'));
    S.raio = RAIOS.indexOf(r) >= 0 ? r : RAIO_PADRAO;
    S.abrir = l;
    montarRaios();
    montarCamadas();
    desenharLegenda();
    return q.get('modo') === 'lista' ? 'lista' : 'mapa';
  }

  function limpar() {
    ['#q-cep', '#f-zona', '#f-texto', '#l-busca'].forEach((s) => { $(s).value = ''; });
    $('#f-uf').value = '';
    $('#q-cep').disabled = false;
    montarMunicipios();
    S.filtro = { uf: '', mun: '', zona: '', cep: '', texto: '', chuva: false };
    $('#f-chuva').checked = false; H.limpar();
    S.centro = null; S.buscaLista = ''; S.pagina = 1; S.abrir = ''; S.ordemManual = false;
    if (S.modo === 'lista') trocarModo('mapa'); else aplicarBusca();
  }

  function ligar() {
    document.querySelectorAll('[data-lente]').forEach((b) => b.addEventListener('click', () => {
      if (!S.meta?.camadas[b.dataset.lente]) return;
      S.camada = b.dataset.lente; recolorir();
    }));
    if (typeof ResizeObserver !== 'undefined') {
      new ResizeObserver(() => {
        document.documentElement.style.setProperty('--altura-topo', $('.topo').offsetHeight + 'px');
        if (S.mapa) S.mapa.invalidateSize({ pan: false });
      }).observe($('.topo'));
    }
    $('#f-busca').addEventListener('submit', (ev) => { ev.preventDefault(); aplicarBusca(true); });
    window.addEventListener('hashchange', () => {
      if (location.hash === S.hashProprio) return;
      // Link novo colado na barra: fecha a ficha aberta e aplica o estado inteiro do link de uma vez.
      S.semGravar = true;
      fecharPainel();
      if (S.mapa) S.mapa.closePopup();
      S.aberto = null;
      S.semGravar = false;
      const modo = lerHash();
      Object.assign(S.filtro, { uf: $('#f-uf').value, mun: $('#f-mun').value, zona: so($('#f-zona').value), texto: $('#f-texto').value.trim(), cep: '', chuva: $('#f-chuva').checked });
      S.centro = null;
      recolorir();
      if (modo !== S.modo) trocarModo(modo, true);
      aplicarBusca(true);
    });
    $('#b-limpar').addEventListener('click', limpar);
    $('#f-chuva').addEventListener('change', () => { S.pagina = 1; aplicarBusca(); });
    ['#f-encerramento', '#f-ultimo'].forEach((id) => $(id).addEventListener('change', () => aplicarBusca()));
    const geo = $('#b-geo');
    if (!navigator.geolocation) geo.hidden = true;
    geo.addEventListener('click', () => {
      geo.disabled = true;
      setStatus('Pedindo a localização ao aparelho…');
      navigator.geolocation.getCurrentPosition(async (pos) => {
        geo.disabled = false;
        $('#q-cep').value = ''; $('#f-zona').value = '';
        const seq = ++S.requisicao;
        S.filtro.cep = ''; S.filtro.zona = '';
        if (!await carregarUfs(seq)) return;
        S.centro = { lat: pos.coords.latitude, lon: pos.coords.longitude, rotulo: 'sua localização', de: 'da sua localização', precisao: 'posição informada pelo aparelho; ela não sai dele' };
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
    $('#f-mun').addEventListener('change', () => aplicarBusca());
    $('#q-cep').addEventListener('input', (ev) => {
      const d = so(ev.target.value).slice(0, 8);
      ev.target.value = d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
    });
    let t;
    $('#f-texto').addEventListener('input', () => { clearTimeout(t); t = setTimeout(() => { S.filtro.texto = $('#f-texto').value.trim(); S.pagina = 1; atualizar(true); }, 300); });
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
    filtros.addEventListener('click', () => {
      const aberto = filtros.getAttribute('aria-expanded') === 'true';
      filtros.setAttribute('aria-expanded', String(!aberto));
      document.body.classList.toggle('filtros-abertos', !aberto);
      if (S.mapa) setTimeout(() => S.mapa.invalidateSize(), 0);
    });
  }

  async function iniciar() {
    if (location.protocol === 'file:') {
      setStatus('Esta página lê arquivos de dados e precisa ser aberta por um endereço da web: https://brasil.arvor.co/politizese_mapa.html.', true);
      return;
    }
    ligar();
    let d;
    try {
      d = await buscar(BASE + 'indice.json');
    } catch (e) {
      setStatus('Não foi possível carregar os locais de votação. Recarregue a página.', true);
      return;
    }
    if (d.formato !== FORMATO) { setStatus('Os dados do mapa estão numa versão diferente da página. Recarregue em alguns minutos.', true); return; }
    S.meta = d;
    M.instalar();
    montarResumo();
    montarUfs();
    iniciarMapa();
    const modo = lerHash();
    trocarModo(modo, true);
    await aplicarBusca();
  }

  // Gancho só de leitura para os scripts de QA (estado e funções); não é API pública.
  window.politizeseMapa = { estado: S, aplicarBusca, atualizar, corValor, corGrupo };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar);
  else iniciar();
})();
