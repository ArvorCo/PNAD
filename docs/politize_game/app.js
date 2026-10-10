/* Politize: o jogo da conversa. Motor em JS clássico (ES2017), sem módulos, sem fetch, sem dependências.
   Lê window.POLITIZE_GAME (dados.js), window.POLITIZE_AVATARES (avatares.js) e window.POLITIZE_CENAS (cenas.js).
   Mecânica: analysis/politize_game/CONTRATO.md. */
(function () {
  'use strict';

  var D = window.POLITIZE_GAME;
  var CHAVE_LS = 'politize_game_v1';
  var FASES = ['abordagem', 'escuta', 'objecao1', 'objecao2', 'fecho'];
  var RESULTADOS = ['flavio', 'nulo', 'lula', 'sem_mudanca'];
  var MISTURA = [
    { campos: ['terceira_via', 'direita_desgarrada'], n: 3 },
    { campos: ['nao_votou', 'nulo_branco'], n: 2 },
    { campos: ['lulista_pragmatico'], n: 2 },
    { campos: ['esquerda_ideologica'], n: 1 }
  ];
  var CONVERSAS_POR_RODADA = 8;
  var BONUS_TRUNFO = 10;
  var DURACAO_TWEEN = 600;   // barra de confiança e expressão do avatar
  var PAUSA_ESCOLHA = 450;   // opção marcada antes do balão do jogador
  var PAUSA_REACAO = 300;    // balão do jogador antes da reação do NPC
  var ESPERA_AUTO = 1600;    // melhor e razoável avançam sozinhos
  var ROLAGEM_FOLGA = 32;    // espaço acima do balão novo, onde cabem o rabicho e a etiqueta
  var CENA_MIN = 170;        // reserva: a altura mínima real vem de --cena-min no CSS (rosto inteiro visível)
  var ESCALAS = [1, 1.15, 1.3];
  var CHAVE_ESCALA = 'politize_game_escala';

  // Rótulos de reserva, usados só quando interface.rotulos não traz a chave.
  var RESERVA = {
    escolha: 'Escolha seu personagem', jogar: 'Jogar com', confianca: 'Confiança', dia: 'Dia', de: 'de',
    placar: 'Placar', flavio: 'Flávio', nulo: 'Nulo', lula: 'Lula', sem_mudanca: 'Sem mudança', saldo: 'Saldo',
    continuar: 'Continuar', proxima: 'Próxima conversa', ver_resultado: 'Ver resultado', jogar_de_novo: 'Jogar de novo',
    trocar: 'Trocar de personagem', compartilhar: 'Compartilhar', copiado: 'Texto copiado.', caderno: 'Caderno',
    caderno_vazio: 'Nenhuma lição ainda.', semente: 'Semente da rodada', recorde: 'Seu recorde', trunfo: 'Trunfo',
    fraqueza: 'Fraqueza', ja_jogado: 'Já jogado', licao: 'Lição', fonte: 'Fonte', ajuda: 'Ajuda', fechar: 'Fechar',
    voltar: 'Politize sua vizinhança', fechado: 'fechado', neutro: 'neutro', aberto: 'aberto', melhor: 'Boa escolha',
    ok: 'Razoável', erro: 'Erro', grave: 'Erro grave', fraqueza_dobrou: 'Sua fraqueza dobrou o custo.',
    encerrada: 'A conversa acabou aqui.', resultado: 'Resultado', vale: 'Vale', voto: 'voto', votos: 'votos', graves: 'Erros graves',
    abordagem: 'Puxe assunto', escuta: 'Escute', objecao: 'Responda', fecho: 'Encerre',
    fecho_narracao: 'Hora de encerrar a conversa.', rodada_compartilhada: 'Rodada compartilhada. Escolha um personagem.',
    licoes_rodada: 'Lições da rodada', nenhuma_licao: 'Rodada sem erro.', voce_disse: 'Você', copia_falhou: 'Não foi possível copiar.',
    trilha_abordagem: 'Puxar assunto', trilha_escuta: 'Escutar', trilha_objecao1: 'Objeção 1', trilha_objecao2: 'Objeção 2',
    trilha_fecho: 'Fechar', pedir_dica: 'Pedir uma dica', dica_usada: 'Dica usada nesta fase', dica_titulo: 'Dica do Politize',
    cuidado: 'Cuidado', dicas_usadas: 'Dicas usadas', segue_sozinho: 'A conversa segue sozinha em instantes.',
    caderno_curto: 'Caderno', dias_rot: 'Desfecho de cada dia', agora: 'agora', por_vir: 'ainda não', opcao: 'Opção',
    letra_menor: 'Diminuir a letra', letra_maior: 'Aumentar a letra', letra_agora: 'agora em'
  };

  var estado = null;     // rodada em andamento (ver novaRodada)
  var memoria = lerMemoria();
  var sementeUrl = lerSementeUrl();
  var focoAntes = null;  // elemento que tinha o foco antes de abrir um painel
  var timers = [];       // pausas da conversa, canceladas ao trocar de conversa
  var tween = 0;         // quadro pendente da animação de confiança
  var nivelEscala = 0;

  /* ---------- utilitários ---------- */

  function $(id) { return document.getElementById(id); }

  function el(tag, cls, texto) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (texto !== undefined && texto !== null) n.textContent = String(texto);
    return n;
  }

  function limpar(n) { while (n.firstChild) n.removeChild(n.firstChild); }

  function interfaceDados() { return (D && D.interface) || {}; }

  // Chaves do motor que o roteiro escreve com outro nome.
  var APELIDOS = { escolha: 'escolher_personagem', licoes_rodada: 'licoes' };

  function rot(chave) {
    var r = interfaceDados().rotulos || {};
    if (r[chave] !== undefined) return r[chave];
    if (APELIDOS[chave] && r[APELIDOS[chave]] !== undefined) return r[APELIDOS[chave]];
    return RESERVA[chave] || chave;
  }

  function rotFase(f) {
    var fases = interfaceDados().fases || {};
    return fases[f] !== undefined ? fases[f] : rot(f);
  }

  function textoFim(chave) { return (interfaceDados().fim || {})[chave] || ''; }

  function preencher(modelo, mapa) {
    return String(modelo || '').replace(/\{(\w+)\}/g, function (m, k) {
      return mapa[k] !== undefined ? String(mapa[k]) : m;
    });
  }

  function lista(v) {
    if (Array.isArray(v)) return v;
    if (v === undefined || v === null || v === '') return [];
    return [v];
  }

  function primeiroNome(npc) { return String(npc.nome || '').split(',')[0].trim(); }

  function semMovimento() {
    try { return window.matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) { return false; }
  }

  function agendar(fn, ms) {
    var id = setTimeout(fn, ms);
    timers.push(id);
    return id;
  }

  function limparTimers() {
    timers.forEach(function (id) { clearTimeout(id); });
    timers = [];
    if (tween && window.cancelAnimationFrame) window.cancelAnimationFrame(tween);
    tween = 0;
  }

  /* ---------- sorteio reproduzível ---------- */

  // mulberry32: PRNG de 32 bits, suficiente para sorteio de jogo.
  function mulberry32(a) {
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      var t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  // Deriva uma semente estável a partir da semente da rodada e de um sal numérico.
  function derivar(semente, sal) {
    var h = (semente ^ Math.imul(sal + 1, 0x9E3779B1)) >>> 0;
    h = Math.imul(h ^ (h >>> 16), 0x85EBCA6B) >>> 0;
    return (h ^ (h >>> 13)) >>> 0;
  }

  function embaralhar(arr, rng) {
    var a = arr.slice();
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(rng() * (i + 1));
      var t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }

  function sementeAleatoria() {
    if (window.crypto && window.crypto.getRandomValues) {
      var u = new Uint32Array(1);
      window.crypto.getRandomValues(u);
      return u[0] % 1000000000;
    }
    return Math.floor(Math.random() * 1000000000);
  }

  function lerSementeUrl() {
    var m = /(?:^|[#&])s=(\d{1,10})/.exec(window.location.hash || '');
    if (!m) return null;
    var n = parseInt(m[1], 10);
    return isFinite(n) ? (n >>> 0) : null;
  }

  function gravarSementeUrl(semente) {
    try { history.replaceState(null, '', '#s=' + semente); } catch (e) { /* file:// antigo ou sandbox */ }
  }

  /* ---------- índices ---------- */

  function porId(arr) {
    var m = {};
    lista(arr).forEach(function (x) { if (x && x.id) m[x.id] = x; });
    return m;
  }

  var CENARIOS = porId(D && D.cenarios);
  var NPCS = lista(D && D.npcs);
  var PERSONAGENS = lista(D && D.personagens);

  /* ---------- montagem da rodada ---------- */

  // Escolhe os NPCs pela mistura fixa; grupo sem NPC suficiente é completado com os demais.
  function sortearNpcs(rng) {
    var total = Math.min(CONVERSAS_POR_RODADA, NPCS.length);
    var pool = embaralhar(NPCS, rng);
    var usados = {};
    var escolhidos = [];
    MISTURA.forEach(function (g) {
      var achados = 0;
      for (var i = 0; i < pool.length && achados < g.n; i++) {
        var n = pool[i];
        if (!usados[n.id] && g.campos.indexOf(n.campo) >= 0) {
          usados[n.id] = true; escolhidos.push(n); achados++;
        }
      }
    });
    for (var k = 0; k < pool.length && escolhidos.length < total; k++) {
      if (!usados[pool[k].id]) { usados[pool[k].id] = true; escolhidos.push(pool[k]); }
    }
    return embaralhar(escolhidos.slice(0, total), rng);
  }

  // Sorteia o cenário de cada conversa; rede_x no máximo uma vez por rodada.
  function sortearCenario(npc, rng, redeUsada) {
    var validos = lista(npc.cenarios).filter(function (id) { return CENARIOS[id]; });
    if (redeUsada) validos = validos.filter(function (id) { return id !== 'rede_x'; });
    if (!validos.length) {
      validos = Object.keys(CENARIOS).filter(function (id) { return !(redeUsada && id === 'rede_x'); });
    }
    return CENARIOS[validos[Math.floor(rng() * validos.length)]];
  }

  function montarRodada(semente) {
    var rng = mulberry32(semente);
    var npcs = sortearNpcs(rng);
    var redeUsada = false;
    return npcs.map(function (npc) {
      var c = sortearCenario(npc, rng, redeUsada);
      if (c && c.id === 'rede_x') redeUsada = true;
      return { npc: npc, cenario: c };
    });
  }

  function novaRodada(personagem, semente) {
    estado = {
      personagem: personagem,
      semente: semente,
      rodada: montarRodada(semente),
      indice: 0,
      conversa: null,
      placar: { flavio: 0, nulo: 0, lula: 0, sem_mudanca: 0 },
      graves: 0,
      dicas: 0,
      passo: null,
      licoes: [],
      historico: []
    };
  }

  /* ---------- regras de uma conversa ---------- */

  function temTrunfo(personagem, npc) {
    var trunfo = lista(personagem.trunfo && personagem.trunfo.tags);
    return lista(npc.tags).some(function (t) { return trunfo.indexOf(t) >= 0; });
  }

  function limitar(v) { return Math.max(0, Math.min(100, v)); }

  function iniciarConversa() {
    var item = estado.rodada[estado.indice];
    var base = Number(item.npc.confianca_inicial) || 0;
    var trunfo = temTrunfo(estado.personagem, item.npc);
    estado.conversa = {
      npc: item.npc,
      cenario: item.cenario,
      fase: 0,
      confianca: limitar(base + (trunfo ? BONUS_TRUNFO : 0)),
      trunfo: trunfo,
      encerradaPorGrave: false,
      travada: false,
      dicas: {},
      resultado: null
    };
  }

  function opcoesDaFase(c) {
    var f = FASES[c.fase];
    var objs = lista(c.npc.objecoes);
    if (f === 'abordagem') return lista(c.cenario && c.cenario.abordagem);
    if (f === 'escuta') return lista(c.npc.escuta);
    if (f === 'objecao1') return lista(objs[0] && objs[0].opcoes);
    if (f === 'objecao2') return lista(objs[1] && objs[1].opcoes);
    return lista(c.npc.fecho);
  }

  // Fala que abre a fase: narração do cenário, queixa, objeção ou deixa de encerramento.
  function falaDaFase(c) {
    var f = FASES[c.fase];
    var objs = lista(c.npc.objecoes);
    if (f === 'abordagem') {
      return { narracao: true, texto: [c.cenario && c.cenario.descricao, c.npc.bio].filter(Boolean).join(' ') };
    }
    if (f === 'escuta') return { texto: c.npc.queixa };
    if (f === 'objecao1') return { texto: objs[0] && objs[0].fala };
    if (f === 'objecao2') return { texto: objs[1] && objs[1].fala };
    return { narracao: true, texto: rot('fecho_narracao') };
  }

  function rotuloFase(c) {
    var f = FASES[c.fase];
    if (f === 'objecao1' || f === 'objecao2') return rotFase('objecao');
    return rotFase(f);
  }

  // Embaralha as opções de forma estável por conversa e fase, para a semente reproduzir a rodada.
  function opcoesOrdenadas(c) {
    var rng = mulberry32(derivar(estado.semente, estado.indice * 10 + c.fase));
    return embaralhar(opcoesDaFase(c), rng);
  }

  function efeitoDe(op) {
    var ef = Number(op.efeito) || 0;
    var fraca = estado.personagem.fraqueza && estado.personagem.fraqueza.tag;
    var dobrou = ef < 0 && fraca && lista(op.tags).indexOf(fraca) >= 0;
    return { valor: dobrou ? ef * 2 : ef, dobrou: !!dobrou };
  }

  function expressao(conf) {
    if (conf < 35) return 'fechado';
    if (conf >= 65) return 'aberto';
    return 'neutro';
  }

  function decidirResultado(c) {
    var d = c.npc.desfechos || {};
    if (c.encerradaPorGrave) return d.baixo || 'lula';
    var l = c.npc.limiares || { alto: 70, medio: 40 };
    if (c.confianca >= l.alto) return d.alto || 'flavio';
    if (c.confianca >= l.medio) return d.medio || 'sem_mudanca';
    return d.baixo || 'lula';
  }

  function publicoDe(c) { return Math.max(1, Number(c.cenario && c.cenario.publico) || 1); }

  function registrarLicao(c, op) {
    if (op.tipo !== 'erro' && op.tipo !== 'grave') return;
    estado.licoes.push({
      tipo: op.tipo,
      npc: c.npc.nome,
      cenario: c.cenario ? c.cenario.nome : '',
      disse: op.texto,
      licao: op.licao || '',
      fonte: textoFonte(op)
    });
  }

  function textoFonte(op) {
    if (op.fonte_texto) return op.fonte_texto;
    var f = D && D.fontes;
    return (f && op.fonte && f[op.fonte]) || '';
  }

  /* ---------- placar e grau ---------- */

  function saldo() { return estado.placar.flavio - estado.placar.lula; }

  function minimoDoGrau(g) {
    var m = g.min_saldo !== undefined ? g.min_saldo : g.saldo_min;
    return typeof m === 'number' ? m : -Infinity;
  }

  // Graus do maior min_saldo para o menor; o grau máximo exige zero erros graves na rodada.
  function grauFinal() {
    var graus = lista(interfaceDados().graus).slice().sort(function (a, b) { return minimoDoGrau(b) - minimoDoGrau(a); });
    var s = saldo();
    for (var i = 0; i < graus.length; i++) {
      if (i === 0 && estado.graves > 0) continue;
      if (s >= minimoDoGrau(graus[i])) return graus[i];
    }
    return graus[graus.length - 1] || { nome: '', frase: '' };
  }

  /* ---------- memória local ---------- */

  function lerMemoria() {
    try {
      var bruto = window.localStorage.getItem(CHAVE_LS);
      var m = bruto ? JSON.parse(bruto) : null;
      if (m && typeof m === 'object') return { recorde: m.recorde || null, jogados: lista(m.jogados) };
    } catch (e) { /* sem armazenamento: segue sem memória */ }
    return { recorde: null, jogados: [] };
  }

  function gravarMemoria() {
    try { window.localStorage.setItem(CHAVE_LS, JSON.stringify(memoria)); } catch (e) { /* idem */ }
  }

  function atualizarMemoria(grau) {
    var id = estado.personagem.id;
    if (memoria.jogados.indexOf(id) < 0) memoria.jogados.push(id);
    var novo = { saldo: saldo(), grau: grau.nome || '', personagem: estado.personagem.nome || id };
    var bateu = !memoria.recorde || novo.saldo > memoria.recorde.saldo;
    if (bateu) memoria.recorde = novo;
    gravarMemoria();
    return bateu;
  }

  /* ---------- arte ---------- */

  // O gênero mora na pessoa, não no visual; a arte precisa dele.
  function visualDe(pessoa) { return Object.assign({ genero: pessoa.genero }, pessoa.visual || {}); }

  function svgAvatar(visual, expr) {
    try {
      if (window.POLITIZE_AVATARES && window.POLITIZE_AVATARES.svg) return window.POLITIZE_AVATARES.svg(visual || {}, expr);
    } catch (e) { /* arte indisponível: placeholder abaixo */ }
    return '<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg"><circle cx="100" cy="100" r="80" fill="#d5d2c6"/></svg>';
  }

  function svgCena(cenario) {
    try {
      if (window.POLITIZE_CENAS && window.POLITIZE_CENAS.svg) return window.POLITIZE_CENAS.svg(cenario || {});
    } catch (e) { /* idem */ }
    return '<svg viewBox="0 0 640 360" xmlns="http://www.w3.org/2000/svg"><rect width="640" height="360" fill="#cfd8e0"/></svg>';
  }

  // O SVG vem dos nossos próprios arquivos de arte, não de entrada do usuário.
  function porSvg(alvo, svg, cobrir) {
    alvo.innerHTML = svg;
    var s = alvo.querySelector('svg');
    if (!s) return;
    s.setAttribute('aria-hidden', 'true');
    s.setAttribute('focusable', 'false');
    if (cobrir) s.setAttribute('preserveAspectRatio', 'xMidYMax slice');
  }

  /* ---------- telas ---------- */

  function mostrarTela(id) {
    ['tela-menu', 'tela-palco', 'tela-fim'].forEach(function (t) { $(t).hidden = t !== id; });
    var jogando = id !== 'tela-menu';
    document.body.classList.toggle('em-jogo', jogando);
    $('lateral').hidden = !jogando;
    $('btn-caderno').hidden = !jogando;
    $('rodape').hidden = id === 'tela-palco';
    if (id !== 'tela-palco') $('confianca-barra').style.width = ''; // palco oculto não guarda barra dimensionada
    fecharLateral();
    window.scrollTo(0, 0);
  }

  function textosFixos() {
    var I = interfaceDados();
    if (I.titulo) { $('menu-titulo').textContent = I.titulo; }
    $('menu-subtitulo').textContent = I.subtitulo || '';
    $('menu-deck').textContent = I.deck || '';
    $('menu-deck').hidden = !I.deck;
    $('menu-escolha').textContent = rot('escolha');
    $('btn-ajuda').textContent = rot('ajuda');
    $('btn-dica').textContent = rot('pedir_dica');
    $('btn-caderno-txt').textContent = rot('caderno_curto');
    $('lateral-tit').textContent = rot('placar');
    $('caderno-tit').textContent = rot('caderno');
    $('lateral-fechar').textContent = rot('fechar');
    $('confianca-rot').textContent = rot('confianca');
    $('ajuda-tit').textContent = rot('ajuda');
    $('ajuda-fechar').textContent = rot('fechar');
    $('btn-compartilhar').textContent = rot('compartilhar');
    $('btn-de-novo').textContent = rot('jogar_de_novo');
    $('btn-trocar').textContent = rot('trocar');
    $('fim-kicker').textContent = textoFim('titulo') || rot('resultado');
    $('fim-licoes-tit').textContent = rot('licoes_rodada');
    if (I.rodape) $('rodape-texto').textContent = I.rodape;
    preencherTutorial($('menu-tutorial'));
    preencherTutorial($('ajuda-tutorial'));
    preencherAviso();
  }

  function preencherTutorial(alvo) {
    limpar(alvo);
    lista(interfaceDados().tutorial).forEach(function (p) { alvo.appendChild(el('li', '', p)); });
  }

  function preencherAviso() {
    var alvo = $('ajuda-texto');
    var aviso = interfaceDados().aviso;
    limpar(alvo);
    if (aviso && typeof aviso === 'object' && !Array.isArray(aviso)) {
      if (aviso.titulo) $('ajuda-tit').textContent = aviso.titulo;
      aviso = aviso.texto;
    }
    lista(aviso).forEach(function (p) { alvo.appendChild(el('p', '', p)); });
  }

  /* menu */

  function renderMenu() {
    var r = memoria.recorde;
    var rec = $('menu-recorde');
    rec.hidden = !r;
    if (r) rec.textContent = rot('recorde') + ': ' + rot('saldo') + ' ' + sinal(r.saldo) + ' · ' + r.grau + ' · ' + r.personagem;
    var avs = $('menu-semente');
    avs.hidden = sementeUrl === null;
    if (sementeUrl !== null) avs.textContent = rot('rodada_compartilhada') + ' ' + rot('semente') + ': ' + sementeUrl + '.';
    var alvo = $('menu-personagens');
    limpar(alvo);
    PERSONAGENS.forEach(function (p) {
      var li = el('li');
      li.appendChild(cartaoPersonagem(p));
      alvo.appendChild(li);
    });
  }

  function cartaoPersonagem(p) {
    var b = el('button', 'personagem');
    b.type = 'button';
    b.setAttribute('aria-label', rot('jogar') + ' ' + p.nome);
    var av = el('span', 'personagem-av');
    porSvg(av, svgAvatar(visualDe(p), 'neutro'), false);
    var corpo = el('span', 'personagem-corpo');
    var nome = el('span', 'personagem-nome', p.nome);
    corpo.appendChild(nome);
    if (memoria.jogados.indexOf(p.id) >= 0) corpo.appendChild(el('span', 'selo-jogado', rot('ja_jogado')));
    if (p.idade) corpo.appendChild(el('span', 'personagem-idade', p.idade + ' anos'));
    var tf = el('span', 'personagem-tfs');
    if (p.fala_inicial) corpo.appendChild(el('span', 'personagem-fala', aspas(p.fala_inicial)));
    if (p.bio) corpo.appendChild(el('span', 'personagem-bio', p.bio));
    tf.appendChild(linhaTF('t', rot('trunfo'), p.trunfo && p.trunfo.texto));
    tf.appendChild(linhaTF('f', rot('fraqueza'), p.fraqueza && p.fraqueza.texto));

    b.appendChild(av);
    b.appendChild(corpo);
    b.appendChild(tf);
    b.addEventListener('click', function () { comecar(p, sementeUrl !== null ? sementeUrl : sementeAleatoria()); });
    return b;
  }

  function linhaTF(cls, titulo, texto) {
    var s = el('span', 'personagem-tf ' + cls);
    if (!texto) return s;
    s.appendChild(el('b', '', titulo));
    s.appendChild(el('span', 'personagem-tf-txt', texto));
    return s;
  }

  // Cita entre aspas só quando o texto ainda não vem com elas.
  function aspas(t) { t = String(t || ''); return /^["\u201c]/.test(t) ? t : '"' + t + '"'; }

  function sinal(n) { return n > 0 ? '+' + n : String(n); }

  /* palco */

  function comecar(personagem, semente) {
    limparTimers();
    pararNpc();
    novaRodada(personagem, semente);
    sementeUrl = null;
    gravarSementeUrl(semente);
    if (!estado.rodada.length) return;
    mostrarTela('tela-palco');
    estado.svgEu = svgAvatar(visualDe(personagem), 'aberto');
    renderLateral();
    abrirConversa();
  }

  function abrirConversa() {
    limparTimers();
    restaurarCena();
    iniciarConversa();
    var c = estado.conversa;
    var n = estado.rodada.length;
    $('hud-dia').textContent = rot('dia') + ' ' + (estado.indice + 1) + ' ' + rot('de') + ' ' + n;
    renderDias();
    $('hud-cenario').textContent = c.cenario ? c.cenario.nome : '';
    porSvg($('cena-fundo'), svgCena(c.cenario), true);
    var pub = publicoDe(c);
    var selo = $('publico-selo');
    selo.hidden = pub <= 1;
    selo.textContent = rot('vale') + ' x' + pub;
    desenharNpc(c.confianca);
    var av = $('npc-avatar');
    av.classList.remove('troca');
    void av.offsetWidth; // reinicia a animação de entrada
    av.classList.add('troca');
    limpar($('confianca-chips'));
    pintarConfianca(c.confianca);
    ariaConfianca(c.confianca);
    limpar($('conversa'));
    $('painel-baixo').scrollTop = 0;
    renderFase();
  }

  /* avatar do NPC: funções opcionais de avatares.js, sempre conferidas antes */

  function avatares() { return window.POLITIZE_AVATARES || {}; }

  function chamarAvatar(nome, a, b) {
    var f = avatares()[nome];
    if (typeof f !== 'function') return false;
    try { f(a, b); return true; } catch (e) { return false; }
  }

  function svgNpc() { return $('npc-avatar').querySelector('svg'); }

  function pararNpc() {
    var s = svgNpc();
    if (s) chamarAvatar('parar', s);
  }

  function desenharNpc(conf) {
    var c = estado.conversa;
    var alvo = $('npc-avatar');
    pararNpc();
    porSvg(alvo, svgAvatar(visualDe(c.npc), expressao(conf)), false);
    alvo.setAttribute('data-expr', expressao(conf));
    var s = svgNpc();
    if (!s) return;
    chamarAvatar('ajustar', s, conf);
    chamarAvatar('vida', s);
  }

  // Sem ajustar() no avatares.js, a expressão só troca quando muda de faixa.
  function trocarExpressao(v) {
    if ($('npc-avatar').getAttribute('data-expr') === expressao(v)) return;
    desenharNpc(v);
  }

  /* confiança: barra com easing, cor por faixa e chip do delta */

  function pintarConfianca(v) {
    var r = Math.round(v);
    var expr = expressao(r);
    $('confianca').setAttribute('data-nivel', expr);
    $('confianca-barra').style.width = v + '%';
    $('confianca-valor').textContent = r + ' · ' + rot(expr);
  }

  function ariaConfianca(v) {
    $('confianca-trilho').setAttribute('aria-valuenow', String(v));
    $('confianca-trilho').setAttribute('aria-valuetext', v + ' de 100, ' + rot(expressao(v)));
  }

  function animarConfianca(de, para, delta) {
    mostrarChip(delta);
    ariaConfianca(para);
    var s = svgNpc();
    var temAjuste = typeof avatares().ajustar === 'function' && !!s;
    var fim = function () {
      tween = 0;
      pintarConfianca(para);
      if (temAjuste) chamarAvatar('ajustar', s, para); else trocarExpressao(para);
    };
    if (semMovimento() || de === para || !window.requestAnimationFrame) { fim(); return; }
    var t0 = null;
    var passo = function (t) {
      if (t0 === null) t0 = t;
      var k = Math.min(1, (t - t0) / DURACAO_TWEEN);
      var e = 1 - Math.pow(1 - k, 3);
      var v = de + (para - de) * e;
      pintarConfianca(v);
      if (temAjuste) chamarAvatar('ajustar', s, v);
      if (k < 1) tween = window.requestAnimationFrame(passo); else fim();
    };
    tween = window.requestAnimationFrame(passo);
  }

  function mostrarChip(delta) {
    if (!delta) return;
    var box = $('confianca-chips');
    var chip = el('span', 'chip-delta ' + (delta > 0 ? 'pos' : 'neg'), (delta > 0 ? '+' : '−') + Math.abs(delta));
    box.appendChild(chip);
    setTimeout(function () { if (chip.parentNode) chip.parentNode.removeChild(chip); }, 1500);
  }

  /* trilha das fases e pontos dos dias */

  function renderTrilha(completa) {
    var alvo = $('trilha');
    var c = estado.conversa;
    limpar(alvo);
    FASES.forEach(function (f, i) {
      var feita = completa || i < c.fase;
      var atual = !completa && i === c.fase;
      var li = el('li', feita ? 'feita' : (atual ? 'atual' : ''));
      var ponto = el('span', 'trilha-ponto', i + 1);
      ponto.setAttribute('aria-hidden', 'true');
      li.appendChild(ponto);
      li.appendChild(el('span', 'trilha-txt', rot('trilha_' + f)));
      if (atual) li.setAttribute('aria-current', 'step');
      alvo.appendChild(li);
    });
  }

  function renderDias() {
    var alvo = $('hud-dias');
    limpar(alvo);
    alvo.setAttribute('aria-label', rot('dias_rot'));
    estado.rodada.forEach(function (x, i) {
      var h = estado.historico[i];
      var cls = h ? 'dia-' + h.resultado : (i === estado.indice ? 'dia-atual' : 'dia-futuro');
      var li = el('li', cls);
      var quando = h ? rot(h.resultado) : (i === estado.indice ? rot('agora') : rot('por_vir'));
      li.appendChild(el('span', 'sr', rot('dia') + ' ' + (i + 1) + ': ' + quando));
      alvo.appendChild(li);
    });
  }

  /* balões da conversa */

  function adicionar(n) {
    n.classList.add('entra');
    $('conversa').appendChild(n);
    return n;
  }

  function balaoNpc(texto) {
    var c = estado.conversa;
    var b = el('div', 'balao balao-npc');
    b.appendChild(el('p', 'balao-nome', primeiroNome(c.npc)));
    b.appendChild(el('p', 'balao-texto', texto));
    return b;
  }

  function legenda(titulo, texto) {
    var b = el('div', 'legenda');
    var p = el('p', 'legenda-texto');
    if (titulo) p.appendChild(el('b', 'legenda-tit', titulo + '. '));
    p.appendChild(document.createTextNode(texto));
    b.appendChild(p);
    return b;
  }

  function balaoEu(texto) {
    var linha = el('div', 'linha-eu');
    var b = el('div', 'balao balao-eu');
    b.appendChild(el('p', 'balao-nome', rot('voce_disse')));
    b.appendChild(el('p', 'balao-texto', texto));
    var mini = el('span', 'eu-mini');
    mini.setAttribute('aria-hidden', 'true');
    porSvg(mini, estado.svgEu || svgAvatar(visualDe(estado.personagem), 'aberto'), false);
    linha.appendChild(b);
    linha.appendChild(mini);
    return linha;
  }

  // Posição de um nó dentro do conteúdo rolável do painel (offsetTop falha sob transform).
  function topoNoPainel(n) {
    var p = $('painel-baixo');
    return n.getBoundingClientRect().top - p.getBoundingClientRect().top + p.scrollTop;
  }

  // Leva o balão novo para o topo do painel; o histórico continua acima para quem quiser reler.
  function rolarPara(n) {
    if (!n) return;
    var p = $('painel-baixo');
    var topo = Math.max(0, topoNoPainel(n) - ROLAGEM_FOLGA);
    try { p.scrollTo({ top: topo, behavior: semMovimento() ? 'auto' : 'smooth' }); } catch (e) { p.scrollTop = topo; }
  }

  function garantirVisivel(n) {
    var p = $('painel-baixo');
    var topo = topoNoPainel(n);
    var fundo = topo + n.offsetHeight + 12;
    if (fundo <= p.scrollTop + p.clientHeight) return;
    var alvo = Math.min(topo - ROLAGEM_FOLGA, fundo - p.clientHeight);
    try { p.scrollTo({ top: alvo, behavior: semMovimento() ? 'auto' : 'smooth' }); } catch (e) { p.scrollTop = alvo; }
  }

  function animar(n) {
    n.classList.remove('entra');
    void n.offsetWidth;
    n.classList.add('entra');
  }

  function renderFase() {
    var c = estado.conversa;
    var fala = falaDaFase(c);
    var texto = preencher(fala.texto, { nome: primeiroNome(c.npc) });
    var novo = fala.narracao ? legenda(FASES[c.fase] === 'abordagem' ? c.npc.nome : '', texto) : balaoNpc(texto);
    adicionar(novo);
    renderTrilha(false);
    c.travada = false;
    estado.passo = null;
    $('reacao').hidden = true;
    limpar($('reacao'));
    $('fase-barra').hidden = false;
    $('fase-rot').textContent = rotuloFase(c);
    prepararDica();
    var alvo = $('opcoes');
    limpar(alvo);
    opcoesOrdenadas(c).forEach(function (op, i) { alvo.appendChild(botaoOpcao(op, i)); });
    alvo.hidden = false;
    animar(alvo);
    estado.balaoAtual = novo;
    ajustarCena();
    rolarPara(novo);
    focar(alvo.querySelector('button'));
  }

  // Em tela baixa, a cena encolhe (até CENA_MIN px) para o balão atual e duas opções caberem sem rolar.
  function ajustarCena() {
    var cena = $('cena');
    cena.style.flexBasis = '';
    var novo = estado && estado.balaoAtual;
    var ops = $('opcoes').querySelectorAll('.opcao');
    if (!novo || $('opcoes').hidden || !ops.length) return;
    var ultima = ops[Math.min(1, ops.length - 1)];
    var p = $('painel-baixo');
    var precisa = (topoNoPainel(ultima) + ultima.offsetHeight + 10) - (topoNoPainel(novo) - ROLAGEM_FOLGA);
    var falta = precisa - p.clientHeight;
    if (falta <= 0) return;
    var minimo = parseFloat(getComputedStyle(cena).minHeight) || CENA_MIN;
    cena.style.flexBasis = Math.max(minimo, cena.offsetHeight - falta) + 'px';
  }

  function restaurarCena() {
    if (estado) estado.balaoAtual = null;
    $('cena').style.flexBasis = '';
  }

  function botaoOpcao(op, i) {
    var b = el('button', 'opcao');
    b.type = 'button';
    b.setAttribute('data-n', String(i + 1));
    var n = el('span', 'opcao-n', i + 1);
    n.setAttribute('aria-hidden', 'true');
    b.appendChild(n);
    b.appendChild(el('span', 'opcao-txt', op.texto));
    b.setAttribute('aria-label', rot('opcao') + ' ' + (i + 1) + ': ' + op.texto);
    b.addEventListener('click', function () { escolher(op, b); });
    return b;
  }

  /* dica do Politize: uma por fase, sem custo de confiança */

  function apoioDe(npc) {
    var a = D && D.apoio;
    return (a && npc && npc.origem && a[npc.origem]) || null;
  }

  function itemDica(apoio, fase) {
    var l = lista(apoio.um_jeito_de_conversar);
    return l.length ? l[Math.min(fase, l.length - 1)] : '';
  }

  function prepararDica() {
    var c = estado.conversa;
    var b = $('btn-dica');
    var box = $('dica');
    box.hidden = true;
    limpar(box);
    b.setAttribute('aria-expanded', 'false');
    b.hidden = !apoioDe(c.npc);
    var usada = !!c.dicas[c.fase];
    b.setAttribute('aria-disabled', usada ? 'true' : 'false');
    b.textContent = usada ? rot('dica_usada') : rot('pedir_dica');
  }

  function pedirDica() {
    var c = estado.conversa;
    if (!c || c.travada || c.dicas[c.fase]) return;
    var apoio = apoioDe(c.npc);
    if (!apoio) return;
    c.dicas[c.fase] = true;
    estado.dicas++;
    var box = $('dica');
    limpar(box);
    box.appendChild(el('p', 'dica-rot', rot('dica_titulo') + (apoio.rotulo ? ': ' + apoio.rotulo : '')));
    var item = itemDica(apoio, c.fase);
    if (item) box.appendChild(el('p', 'dica-txt', item));
    if (apoio.cuidado) {
      var p = el('p', 'dica-cuidado');
      p.appendChild(el('b', '', rot('cuidado') + ': '));
      p.appendChild(document.createTextNode(apoio.cuidado));
      box.appendChild(p);
    }
    box.hidden = false;
    animar(box);
    var b = $('btn-dica');
    b.setAttribute('aria-disabled', 'true');
    b.setAttribute('aria-expanded', 'true');
    b.textContent = rot('dica_usada');
    focar(box, true);
    garantirVisivel(box);
  }

  /* escolha, reação e avanço */

  function escolher(op, botaoEscolhido) {
    var c = estado.conversa;
    if (!c || c.travada) return;
    c.travada = true;
    var ef = efeitoDe(op);
    var antes = c.confianca;
    c.confianca = limitar(c.confianca + ef.valor);
    if (op.tipo === 'grave') { c.encerradaPorGrave = true; estado.graves++; }
    registrarLicao(c, op);
    renderLateral();
    var tipo = op.tipo || 'ok';
    marcarOpcoes(botaoEscolhido, tipo);
    agendar(function () {
      $('opcoes').hidden = true;
      limpar($('opcoes'));
      $('fase-barra').hidden = true;
      $('dica').hidden = true;
      restaurarCena();
      var eu = adicionar(balaoEu(op.texto));
      rolarPara(eu);
      agendar(function () {
        adicionar(balaoNpc(preencher(op.reacao, { nome: primeiroNome(c.npc) })));
        var s = svgNpc();
        if (s) chamarAvatar('reagir', s, tipo);
        adicionar(notaReacao(op, ef, tipo));
        animarConfianca(antes, c.confianca, ef.valor);
        mostrarContinuar(tipo);
        rolarPara(eu);
      }, PAUSA_REACAO);
    }, PAUSA_ESCOLHA);
  }

  function marcarOpcoes(escolhido, tipo) {
    var bons = tipo === 'melhor' || tipo === 'ok';
    Array.prototype.forEach.call($('opcoes').querySelectorAll('button'), function (b) {
      b.setAttribute('aria-disabled', 'true');
      if (b === escolhido) {
        b.classList.add('escolhida', bons ? 'escolhida-boa' : 'escolhida-ruim');
        b.setAttribute('aria-pressed', 'true');
        b.appendChild(el('span', 'opcao-selo', rot(tipo)));
      } else {
        b.classList.add('esmaecida');
      }
    });
    $('btn-dica').setAttribute('aria-disabled', 'true');
  }

  function notaReacao(op, ef, tipo) {
    var box = el('div', 'nota-reacao');
    var cab = el('div', 'reacao-cab');
    cab.appendChild(el('span', 'tipo-selo tipo-' + tipo, rot(tipo)));
    cab.appendChild(el('span', 'delta ' + (ef.valor >= 0 ? 'pos' : 'neg'), rot('confianca') + ' ' + sinal(ef.valor)));
    box.appendChild(cab);
    if (ef.dobrou) box.appendChild(el('p', 'nota', rot('fraqueza_dobrou')));
    if (tipo === 'erro' || tipo === 'grave') box.appendChild(cardLicao(op));
    if (tipo === 'grave') box.appendChild(el('p', 'nota', rot('encerrada')));
    return box;
  }

  // Melhor e razoável seguem sozinhos; erro e grave esperam o leitor ler a lição.
  function mostrarContinuar(tipo) {
    var box = $('reacao');
    limpar(box);
    var token = {};
    estado.passo = token;
    var seguir = function () {
      if (estado.passo !== token) return;
      estado.passo = null;
      avancar();
    };
    var auto = tipo === 'melhor' || tipo === 'ok';
    if (auto) {
      var aviso = el('p', 'auto-aviso', rot('segue_sozinho'));
      var barra = el('span', 'auto-barra');
      barra.setAttribute('aria-hidden', 'true');
      aviso.appendChild(barra);
      box.appendChild(aviso);
      agendar(seguir, ESPERA_AUTO);
    }
    box.appendChild(botao(rot('continuar'), 'btn btn-prim btn-largo', seguir));
    box.hidden = false;
    animar(box);
    focar(box.querySelector('button'));
  }

  function cardLicao(op) {
    var card = el('div', 'licao-card' + (op.tipo === 'grave' ? ' grave' : ''));
    card.appendChild(el('h3', '', rot('licao')));
    if (op.licao) card.appendChild(el('p', '', op.licao));
    var fonte = textoFonte(op);
    if (fonte) {
      var p = el('p', 'fonte');
      p.appendChild(el('b', '', rot('fonte') + ': '));
      p.appendChild(document.createTextNode(fonte));
      card.appendChild(p);
    }
    return card;
  }

  function botao(texto, cls, acao) {
    var b = el('button', cls, texto);
    b.type = 'button';
    b.addEventListener('click', acao);
    return b;
  }

  function avancar() {
    var c = estado.conversa;
    if (c.encerradaPorGrave || c.fase >= FASES.length - 1) { encerrarConversa(); return; }
    c.fase++;
    renderFase();
  }

  function encerrarConversa() {
    var c = estado.conversa;
    var res = decidirResultado(c);
    var pub = publicoDe(c);
    c.resultado = res;
    c.travada = true;
    if (estado.placar[res] === undefined) estado.placar[res] = 0;
    estado.placar[res] += pub;
    estado.historico.push({ npc: c.npc.id, cenario: c.cenario && c.cenario.id, resultado: res, publico: pub, confianca: c.confianca });
    renderLateral();
    renderDias();
    renderTrilha(true);
    restaurarCena();
    var txt = (c.npc.desfecho_texto || {})[res] || '';
    var primeiro = txt ? adicionar(balaoNpc(txt)) : null;
    var d = adicionar(el('div', 'desfecho res-' + res));
    d.appendChild(el('p', 'rot', rot('resultado')));
    d.appendChild(el('p', 'res', rot(res)));
    d.appendChild(el('p', 'vale', rot('vale') + ' ' + pub + ' ' + (pub === 1 ? rot('voto') : rot('votos'))));
    var box = $('reacao');
    limpar(box);
    var ultimo = estado.indice >= estado.rodada.length - 1;
    box.appendChild(botao(ultimo ? rot('ver_resultado') : rot('proxima'), 'btn btn-prim btn-largo', proxima));
    box.hidden = false;
    $('opcoes').hidden = true;
    $('fase-barra').hidden = true;
    animar(box);
    rolarPara(primeiro || d);
    focar(box.querySelector('button'));
  }

  function proxima() {
    if (estado.indice >= estado.rodada.length - 1) { limparTimers(); pararNpc(); renderFim(); return; }
    estado.indice++;
    abrirConversa();
  }

  /* lateral: placar e caderno */

  function preencherPlacar(alvo) {
    limpar(alvo);
    RESULTADOS.forEach(function (k) { alvo.appendChild(celula(k, rot(k), estado.placar[k] || 0)); });
    alvo.appendChild(celula('saldo', rot('saldo'), sinal(saldo())));
  }

  function celula(cls, titulo, valor) {
    var d = el('div', cls);
    d.appendChild(el('dt', '', titulo));
    d.appendChild(el('dd', '', valor));
    return d;
  }

  // Placar final: número grande e barra proporcional ao maior resultado.
  function placarFim(alvo) {
    limpar(alvo);
    var p = estado.placar;
    var maior = Math.max(1, p.flavio || 0, p.nulo || 0, p.lula || 0, p.sem_mudanca || 0);
    RESULTADOS.forEach(function (k) {
      var v = p[k] || 0;
      var d = el('div', 'linha-placar ' + k);
      d.appendChild(el('dt', '', rot(k)));
      var dd = el('dd');
      dd.appendChild(el('span', 'num', v));
      var trilho = el('span', 'barra-placar');
      trilho.setAttribute('aria-hidden', 'true');
      if (v > 0) {
        var cheio = el('span', 'barra-placar-cheia');
        cheio.style.width = (100 * v / maior) + '%';
        trilho.appendChild(cheio);
      }
      dd.appendChild(trilho);
      d.appendChild(dd);
      alvo.appendChild(d);
    });
    var sd = el('div', 'linha-placar saldo');
    sd.appendChild(el('dt', '', rot('saldo')));
    var dd2 = el('dd');
    dd2.appendChild(el('span', 'num', sinal(saldo())));
    sd.appendChild(dd2);
    alvo.appendChild(sd);
  }

  function renderLateral() {
    preencherPlacar($('placar'));
    var p = estado.placar;
    $('hud-placar').textContent = rot('flavio') + ' ' + p.flavio + ' · ' + rot('nulo') + ' ' + p.nulo + ' · ' + rot('lula') + ' ' + p.lula + ' · ' + rot('saldo') + ' ' + sinal(saldo());
    preencherLicoes($('caderno-lista'), estado.licoes);
    var vazio = !estado.licoes.length;
    $('caderno-vazio').hidden = !vazio;
    $('caderno-vazio').textContent = rot('caderno_vazio');
    $('btn-caderno-n').textContent = String(estado.licoes.length);
  }

  function preencherLicoes(alvo, licoes) {
    limpar(alvo);
    licoes.forEach(function (l) {
      var li = el('li', l.tipo === 'grave' ? 'grave' : '');
      li.appendChild(el('span', 'quem', [rot(l.tipo), l.npc, l.cenario].filter(Boolean).join(' · ')));
      li.appendChild(el('span', 'disse', aspas(l.disse)));
      if (l.licao) li.appendChild(el('span', 'li', l.licao));
      if (l.fonte) li.appendChild(el('span', 'fonte', rot('fonte') + ': ' + l.fonte));
      alvo.appendChild(li);
    });
  }

  function abrirLateral() {
    focoAntes = document.activeElement;
    $('lateral').classList.add('aberto');
    $('btn-caderno').setAttribute('aria-expanded', 'true');
    focar($('lateral-fechar'));
  }

  function fecharLateral() {
    var aberto = $('lateral').classList.contains('aberto');
    $('lateral').classList.remove('aberto');
    $('btn-caderno').setAttribute('aria-expanded', 'false');
    if (aberto) restaurarFoco();
  }

  /* fim */

  function renderFim() {
    var grau = grauFinal();
    var bateu = atualizarMemoria(grau);
    mostrarTela('tela-fim');
    $('fim-grau-nome').textContent = grau.nome || '';
    $('fim-grau-frase').textContent = grau.frase || '';
    $('fim-resumo').textContent = preencher(textoFim('resumo'), estado.placar);
    $('fim-erros').textContent = textoFim(estado.graves ? 'com_erros' : 'sem_erros');
    placarFim($('fim-placar'));
    $('fim-dicas-n').textContent = rot('dicas_usadas') + ': ' + estado.dicas;
    var rec = $('fim-recorde');
    rec.hidden = !bateu;
    rec.textContent = rot('recorde') + ': ' + rot('saldo') + ' ' + sinal(saldo());
    preencherLicoes($('fim-licoes'), estado.licoes);
    if (!estado.licoes.length) $('fim-licoes').appendChild(el('li', '', rot('nenhuma_licao')));
    var dicas = $('fim-dicas');
    limpar(dicas);
    var I = interfaceDados();
    lista(I.dicas_gerais || I.licoes_recorrentes).forEach(function (t) { dicas.appendChild(el('li', '', t)); });
    $('fim-semente').textContent = rot('semente') + ': ' + estado.semente + ' · ' + rot('graves') + ': ' + estado.graves;
    $('fim-status').textContent = '';
    gravarSementeUrl(estado.semente);
    focar($('fim-grau-nome'), true);
  }

  function urlDaRodada() {
    var base = String(window.location.href).split('#')[0];
    return base + '#s=' + estado.semente;
  }

  function textoCompartilhar() {
    var modelos = lista(interfaceDados().compartilhar);
    var modelo = modelos.length ? modelos[estado.semente % modelos.length] : '{flavio} / {nulo} / {lula} · {grau}';
    return preencher(modelo, {
      flavio: estado.placar.flavio, nulo: estado.placar.nulo, lula: estado.placar.lula, grau: grauFinal().nome || ''
    });
  }

  function compartilhar() {
    var texto = textoCompartilhar();
    var url = urlDaRodada();
    if (navigator.share) {
      navigator.share({ title: document.title, text: texto, url: url }).catch(function () { /* cancelado */ });
      return;
    }
    copiar(texto + ' ' + url);
  }

  function copiar(texto) {
    var ok = function () { $('fim-status').textContent = rot('copiado'); };
    var falhou = function () { $('fim-status').textContent = copiaManual(texto) ? rot('copiado') : rot('copia_falhou'); };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(texto).then(ok, falhou);
    } else {
      falhou();
    }
  }

  // Alternativa para navegadores sem a API de área de transferência (ou em file://).
  function copiaManual(texto) {
    var ta = el('textarea');
    ta.value = texto;
    ta.setAttribute('readonly', '');
    ta.style.position = 'fixed';
    ta.style.top = '-1000px';
    document.body.appendChild(ta);
    ta.select();
    var ok = false;
    try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
    document.body.removeChild(ta);
    return ok;
  }

  /* ---------- ajuda, foco e teclado ---------- */

  function focar(n, programatico) {
    if (!n) return;
    if (programatico && !n.hasAttribute('tabindex')) n.setAttribute('tabindex', '-1');
    try { n.focus({ preventScroll: true }); } catch (e) { n.focus(); }
  }

  function restaurarFoco() {
    if (focoAntes && document.body.contains(focoAntes)) focar(focoAntes);
    focoAntes = null;
  }

  function abrirAjuda() {
    focoAntes = document.activeElement;
    $('ajuda').hidden = false;
    focar($('ajuda-fechar'));
  }

  function fecharAjuda() {
    $('ajuda').hidden = true;
    restaurarFoco();
  }

  function aoTeclar(ev) {
    if (ev.key === 'Escape') {
      if (!$('ajuda').hidden) { fecharAjuda(); return; }
      if ($('lateral').classList.contains('aberto')) { fecharLateral(); return; }
    }
    if (!$('ajuda').hidden || $('tela-palco').hidden || $('opcoes').hidden) return;
    if (!estado || !estado.conversa || estado.conversa.travada) return;
    if (ev.ctrlKey || ev.metaKey || ev.altKey) return;
    if (!/^[1-4]$/.test(ev.key)) return;
    var b = $('opcoes').querySelector('button[data-n="' + ev.key + '"]');
    if (b) { ev.preventDefault(); b.click(); }
  }

  // Mantém o Tab dentro da caixa de ajuda enquanto ela estiver aberta.
  function prenderTab(ev) {
    if (ev.key !== 'Tab' || $('ajuda').hidden) return;
    var focaveis = $('ajuda').querySelectorAll('button, a[href]');
    if (!focaveis.length) return;
    var prim = focaveis[0];
    var ult = focaveis[focaveis.length - 1];
    if (ev.shiftKey && document.activeElement === prim) { ev.preventDefault(); focar(ult); }
    else if (!ev.shiftKey && document.activeElement === ult) { ev.preventDefault(); focar(prim); }
  }

  function ligarEventos() {
    $('btn-ajuda').addEventListener('click', abrirAjuda);
    $('ajuda-fechar').addEventListener('click', fecharAjuda);
    $('ajuda').addEventListener('click', function (ev) { if (ev.target === $('ajuda')) fecharAjuda(); });
    $('btn-caderno').addEventListener('click', function () {
      if ($('lateral').classList.contains('aberto')) fecharLateral(); else abrirLateral();
    });
    $('lateral-fechar').addEventListener('click', fecharLateral);
    $('btn-compartilhar').addEventListener('click', compartilhar);
    $('btn-dica').addEventListener('click', pedirDica);
    $('btn-menor').addEventListener('click', function () { mudarEscala(-1); });
    $('btn-maior').addEventListener('click', function () { mudarEscala(1); });
    window.addEventListener('resize', function () { medirTopo(); ajustarCena(); });
    $('btn-de-novo').addEventListener('click', function () { comecar(estado.personagem, sementeAleatoria()); });
    $('btn-trocar').addEventListener('click', function () { limparTimers(); pararNpc(); mostrarTela('tela-menu'); renderMenu(); });
    document.addEventListener('keydown', aoTeclar);
    document.addEventListener('keydown', prenderTab);
    window.addEventListener('hashchange', function () {
      var s = lerSementeUrl();
      var mesmaEmCurso = estado && s === estado.semente && !$('tela-palco').hidden;
      if (s !== null && !mesmaEmCurso) { limparTimers(); pararNpc(); sementeUrl = s; mostrarTela('tela-menu'); renderMenu(); }
    });
  }

  /* ---------- tamanho da letra ---------- */

  function lerEscala() {
    try {
      var v = parseInt(window.localStorage.getItem(CHAVE_ESCALA), 10);
      if (v >= 0 && v < ESCALAS.length) return v;
    } catch (e) { /* sem armazenamento: começa em 100% */ }
    return 0;
  }

  function aplicarEscala(i) {
    nivelEscala = Math.max(0, Math.min(ESCALAS.length - 1, i));
    var pct = Math.round(ESCALAS[nivelEscala] * 100) + '%';
    document.documentElement.style.setProperty('--escala', String(ESCALAS[nivelEscala]));
    document.documentElement.setAttribute('data-escala', String(nivelEscala));
    var menor = $('btn-menor');
    var maior = $('btn-maior');
    menor.setAttribute('aria-disabled', nivelEscala === 0 ? 'true' : 'false');
    maior.setAttribute('aria-disabled', nivelEscala === ESCALAS.length - 1 ? 'true' : 'false');
    maior.setAttribute('aria-pressed', nivelEscala > 0 ? 'true' : 'false');
    menor.setAttribute('aria-label', rot('letra_menor') + ', ' + rot('letra_agora') + ' ' + pct);
    maior.setAttribute('aria-label', rot('letra_maior') + ', ' + rot('letra_agora') + ' ' + pct);
    medirTopo();
    if (estado && estado.balaoAtual) { ajustarCena(); rolarPara(estado.balaoAtual); }
  }

  function mudarEscala(passo) {
    var novo = nivelEscala + passo;
    if (novo < 0 || novo >= ESCALAS.length) return;
    aplicarEscala(novo);
    try { window.localStorage.setItem(CHAVE_ESCALA, String(nivelEscala)); } catch (e) { /* idem */ }
  }

  // A barra do topo cresce com a letra; o palco desconta a altura real dela.
  function medirTopo() {
    var h = $('topo').offsetHeight;
    if (h) document.documentElement.style.setProperty('--topo-h', h + 'px');
  }

  /* ---------- partida ---------- */

  function iniciar() {
    aplicarEscala(lerEscala());
    if (!D || !PERSONAGENS.length || !NPCS.length) {
      var alvo = $('menu-personagens');
      limpar(alvo);
      alvo.appendChild(el('li', 'noscript', 'Não foi possível carregar os dados do jogo. Recarregue a página.'));
      return;
    }
    textosFixos();
    ligarEventos();
    mostrarTela('tela-menu');
    renderMenu();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar);
  else iniciar();
})();
