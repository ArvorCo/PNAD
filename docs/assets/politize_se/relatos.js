/* Formulário e contagem dos relatos; dependências visuais injetadas pelo app. */
export function criarRelatos({ h, f0, aviso }) {
// Configuração pública da totalização (URL do Supabase e chave publicável) em
// assets/totalizacao/config.js. A chave publicável só lê as duas views de contagem e chama a
// função receber-relato, que valida, limita por IP e grava; o texto nunca é publicado. Barreiras
// contra robô sem terceiros: campo-armadilha, tempo mínimo de 8 s desde o desafio e prova de
// trabalho de 18 bits calculada no aparelho.
const CFG_REL = window.TOTALIZACAO_CONFIG || {};
const VERSAO_RELATO = '2026-10-26.2';
const MAX_TEXTO_RELATO = 1000;
const TIPOS_RELATO = [
  ['fila_longa', 'Fila longa'],
  ['urna_trocada', 'Urna trocada ou com defeito'],
  ['biometria_falhou', 'A digital não foi reconhecida'],
  ['votou_sem_biometria', 'Gente votando sem digital'],
  ['mesario_conduta', 'Conduta de mesário'],
  ['boca_de_urna', 'Boca de urna ou propaganda no local'],
  ['transporte_irregular', 'Transporte de eleitores oferecido por alguém'],
  ['local_mudou', 'O local de votação mudou'],
  ['secao_fechou_cedo', 'A seção fechou cedo'],
  ['secao_fechou_tarde', 'A seção fechou tarde'],
  ['outro', 'Outro'],
];
const NOME_TIPO_RELATO = Object.fromEntries(TIPOS_RELATO);
const relatosZona = new Map();

// Contagem lida por zona inteira, nunca pela seção: o servidor recebe só UF e zona, o mesmo que
// já recebe ao entregar o arquivo da zona; a seção é filtrada aqui no aparelho.
function carregarRelatosZona(uf, zona) {
  const chave = `${uf}|${zona}`;
  if (relatosZona.has(chave)) return relatosZona.get(chave);
  const p = (async () => {
    if (!CFG_REL.supabaseUrl || !CFG_REL.publishableKey) return null;
    const url = `${CFG_REL.supabaseUrl}/rest/v1/v_relatos_secao?uf=eq.${encodeURIComponent(uf)}&zona=eq.${Number(zona)}&select=secao,tipo,turno,n`;
    const r = await fetch(url, { headers: { apikey: CFG_REL.publishableKey, Authorization: `Bearer ${CFG_REL.publishableKey}` }, credentials: 'omit', referrerPolicy: 'no-referrer' });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const linhas = await r.json();
    return Array.isArray(linhas) ? linhas : [];
  })();
  relatosZona.set(chave, p);
  p.catch(() => relatosZona.delete(chave));
  return p;
}
async function pintarContagemRelatos(no, uf, zona, secao) {
  try {
    const linhas = await carregarRelatosZona(uf, zona);
    if (linhas === null) { no.textContent = ''; return; }
    const daSecao = linhas.filter((l) => Number(l.secao) === Number(secao));
    const total = daSecao.reduce((a, l) => a + (Number(l.n) || 0), 0);
    if (!total) { no.textContent = 'Nenhum relato sobre esta seção até agora.'; return; }
    const porTipo = new Map();
    for (const l of daSecao) porTipo.set(l.tipo, (porTipo.get(l.tipo) || 0) + (Number(l.n) || 0));
    const partes = [...porTipo].sort((a, b) => b[1] - a[1]).map(([t, n]) => `${(NOME_TIPO_RELATO[t] || 'outro').toLowerCase()}: ${f0(n)}`);
    no.textContent = `${f0(total)} ${total === 1 ? 'relato' : 'relatos'} nesta seção (${partes.join('; ')}). O texto dos relatos não é publicado.`;
  } catch {
    no.textContent = 'A contagem de relatos não carregou agora.';
  }
}

// Prova de trabalho no aparelho, sem serviço de terceiros: procura um nonce tal que
// sha256(desafio + nonce) comece com `bits` bits zero. Roda num Worker (SHA-256 em JS puro, com
// o estado do primeiro bloco fixo calculado uma vez), para a página não travar.
function trabalhoProva() {
  const K = new Uint32Array([
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
  ]);
  const W = new Uint32Array(64);
  const rotr = (x, n) => (x >>> n) | (x << (32 - n));
  function comprimir(st, b, o) {
    for (let i = 0; i < 16; i++) W[i] = (b[o + 4 * i] << 24) | (b[o + 4 * i + 1] << 16) | (b[o + 4 * i + 2] << 8) | b[o + 4 * i + 3];
    for (let i = 16; i < 64; i++) {
      const s0 = rotr(W[i - 15], 7) ^ rotr(W[i - 15], 18) ^ (W[i - 15] >>> 3);
      const s1 = rotr(W[i - 2], 17) ^ rotr(W[i - 2], 19) ^ (W[i - 2] >>> 10);
      W[i] = (W[i - 16] + s0 + W[i - 7] + s1) | 0;
    }
    let [a, bb, c, d, e, f, g, h] = st;
    for (let i = 0; i < 64; i++) {
      const t1 = (h + (rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25)) + ((e & f) ^ (~e & g)) + K[i] + W[i]) | 0;
      const t2 = ((rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22)) + ((a & bb) ^ (a & c) ^ (bb & c))) | 0;
      h = g; g = f; f = e; e = (d + t1) | 0; d = c; c = bb; bb = a; a = (t1 + t2) | 0;
    }
    st[0] += a; st[1] += bb; st[2] += c; st[3] += d; st[4] += e; st[5] += f; st[6] += g; st[7] += h;
  }
  self.onmessage = (ev) => {
    const { desafio, bits } = ev.data;
    const pre = new TextEncoder().encode(desafio);
    const fixos = Math.floor(pre.length / 64);
    const meio = new Uint32Array([0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]);
    for (let i = 0; i < fixos; i++) comprimir(meio, pre, i * 64);
    const resto = pre.subarray(fixos * 64);
    const buf = new Uint8Array(256);
    const st = new Uint32Array(8);
    const limite = 2 ** (32 - bits);
    for (let n = 0; ; n++) {
      const s = String(n);
      buf.set(resto);
      let p = resto.length;
      for (let i = 0; i < s.length; i++) buf[p++] = s.charCodeAt(i);
      const bitsMsg = (pre.length + s.length) * 8;
      buf[p++] = 0x80;
      const blocos = Math.ceil((p + 8) / 64);
      buf.fill(0, p, blocos * 64);
      const fim = blocos * 64;
      buf[fim - 4] = bitsMsg >>> 24; buf[fim - 3] = bitsMsg >>> 16; buf[fim - 2] = bitsMsg >>> 8; buf[fim - 1] = bitsMsg;
      st.set(meio);
      for (let i = 0; i < blocos; i++) comprimir(st, buf, i * 64);
      if (st[0] >>> 0 < limite) { self.postMessage({ nonce: s, tentativas: n + 1 }); return; }
      if ((n & 0x3fff) === 0) self.postMessage({ tentativas: n });
    }
  };
}

const ESPERA_MINIMA_MS = 8500; // a função exige 8 s; meio segundo de folga para a rede
const VIDA_DESAFIO_MS = 9 * 60_000; // a função aceita 10 min
async function pedirDesafio(funcao) {
  const r = await fetch(`${funcao}?desafio=1`, { headers: { apikey: CFG_REL.publishableKey || '', Authorization: `Bearer ${CFG_REL.publishableKey || ''}` }, credentials: 'omit', referrerPolicy: 'no-referrer' });
  const j = await r.json();
  if (!r.ok || !j || typeof j.desafio !== 'string') throw new Error('desafio indisponível');
  return { desafio: j.desafio, bits: Number(j.bits) || 18, recebido: Date.now() };
}
function provaDeTrabalho(desafio, bits, progresso) {
  return new Promise((res, rej) => {
    const url = URL.createObjectURL(new Blob([`(${trabalhoProva.toString()})()`], { type: 'text/javascript' }));
    const w = new Worker(url);
    URL.revokeObjectURL(url);
    const esperado = 2 ** bits;
    w.onmessage = (ev) => {
      if (ev.data.nonce !== undefined) { w.terminate(); res(ev.data.nonce); return; }
      progresso(Math.min(0.95, ev.data.tentativas / esperado));
    };
    w.onerror = (e) => { w.terminate(); rej(e); };
    w.postMessage({ desafio, bits });
  });
}

function blocoRelato(uf, zona, s, local) {
  const funcao = CFG_REL.supabaseUrl ? `${CFG_REL.supabaseUrl}/functions/v1/receber-relato` : null;
  const contagem = h('p', { class: 'relato-contagem', role: 'status' }, 'Carregando a contagem de relatos...');
  pintarContagemRelatos(contagem, uf, zona, s.secao);
  const status = h('p', { class: 'relato-status', role: 'status', 'aria-live': 'polite' });
  const contador = h('span', { class: 'relato-contador', 'aria-live': 'off' }, `0 de ${f0(MAX_TEXTO_RELATO)}`);
  const barra = h('span');
  const progresso = h('div', { class: 'relato-progresso', hidden: true, role: 'progressbar', 'aria-label': 'Conferindo o envio', 'aria-valuemin': '0', 'aria-valuemax': '100' },
    h('span', { class: 'relato-progresso-trilho' }, barra), h('span', { class: 'relato-progresso-rot' }, 'conferindo...'));
  const mostrar = (f) => { const v = Math.round(f * 100); barra.style.width = `${v}%`; progresso.setAttribute('aria-valuenow', String(v)); };
  let desafioP = null;
  const garantirDesafio = () => {
    if (!funcao) return null;
    if (!desafioP) desafioP = pedirDesafio(funcao).catch((e) => { desafioP = null; throw e; });
    return desafioP;
  };
  const texto = h('textarea', { id: 'rel-texto', rows: '5', maxlength: String(MAX_TEXTO_RELATO), required: true, 'aria-describedby': 'rel-texto-ajuda', oninput: () => { contador.textContent = `${f0([...texto.value].length)} de ${f0(MAX_TEXTO_RELATO)}`; } });
  const radio = (valor, rot, marcado) => h('label', { class: 'relato-opcao' }, h('input', { type: 'radio', name: 'rel-presenciou', value: valor, checked: marcado }), rot);
  const form = h('form', { class: 'relato-form', novalidate: true },
    h('div', { class: 'relato-grade' },
      h('div', {}, h('label', { for: 'rel-tipo', class: 'rot' }, 'O que você notou'),
        h('select', { id: 'rel-tipo', required: true }, h('option', { value: '' }, 'Escolha'), TIPOS_RELATO.map(([v, r]) => h('option', { value: v }, r)))),
      h('div', {}, h('label', { for: 'rel-turno', class: 'rot' }, 'Em qual turno'),
        h('select', { id: 'rel-turno' }, h('option', { value: '2' }, '2º turno, 25/10'), h('option', { value: '1' }, '1º turno, 04/10'))),
      h('div', {}, h('label', { for: 'rel-hora', class: 'rot' }, 'Hora aproximada (opcional)'), h('input', { id: 'rel-hora', type: 'time', step: '60' }))),
    h('label', { for: 'rel-texto', class: 'rot' }, 'Conte o que aconteceu'),
    texto,
    h('p', { id: 'rel-texto-ajuda', class: 'ajuda relato-ajuda' }, contador, ' · Descreva o fato, o horário e o lugar. Não escreva nome, CPF nem dado de outra pessoa.'),
    h('fieldset', { class: 'relato-campo' }, h('legend', { class: 'rot' }, 'Você presenciou?'),
      h('div', { class: 'relato-opcoes' }, radio('sim', 'Eu vi', true), radio('nao', 'Alguém me contou', false))),
    h('label', { for: 'rel-contato', class: 'rot' }, 'E-mail ou telefone (opcional)'),
    h('input', { id: 'rel-contato', type: 'text', inputmode: 'email', autocomplete: 'off', maxlength: '120', 'aria-describedby': 'rel-contato-ajuda' }),
    h('p', { id: 'rel-contato-ajuda', class: 'ajuda relato-ajuda' }, 'Só se quiser retorno. Sem contato, o relato é anônimo.'),
    h('div', { class: 'relato-mel', 'aria-hidden': 'true' }, h('label', { for: 'rel-website' }, 'Site (deixe em branco)'), h('input', { id: 'rel-website', name: 'website', type: 'text', tabindex: '-1', autocomplete: 'off' })),
    h('p', { class: 'ajuda relato-lgpd' }, 'O relato é anônimo por padrão, o contato só é guardado se você o informar, e usamos o envio apenas para análise e possível retorno, sem publicar o texto.'),
    h('div', { class: 'botoes' }, h('button', { type: 'submit', class: 'btn btn-prim', disabled: !funcao }, 'Enviar relato')),
    progresso,
    status);
  // O carimbo de abertura é o desafio, pedido no primeiro toque no formulário (quem só lê a
  // ficha não chama a função).
  form.addEventListener('focusin', () => { const p = garantirDesafio(); if (p) p.catch(() => {}); }, { once: true });
  const erro = (no, msg) => { no.setAttribute('aria-invalid', 'true'); status.className = 'relato-status erro'; status.textContent = msg; no.focus(); };
  form.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    for (const n of form.querySelectorAll('[aria-invalid]')) n.removeAttribute('aria-invalid');
    const tipo = form.querySelector('#rel-tipo');
    const hora = form.querySelector('#rel-hora');
    const contato = form.querySelector('#rel-contato');
    if (!tipo.value) return erro(tipo, 'Escolha o que você notou.');
    const t = texto.value.trim();
    if (!t) return erro(texto, 'Conte o que aconteceu, em poucas palavras.');
    if ([...t].length > MAX_TEXTO_RELATO) return erro(texto, `O texto passa de ${f0(MAX_TEXTO_RELATO)} caracteres.`);
    const c = contato.value.trim();
    if (c && !(/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(c) || /^[\d\s()+.-]{10,20}$/.test(c))) return erro(contato, 'Confira o e-mail ou o telefone, ou deixe em branco.');
    const botao = form.querySelector('button[type="submit"]');
    botao.disabled = true;
    status.className = 'relato-status';
    status.textContent = '';
    mostrar(0);
    progresso.hidden = false;
    let prova;
    try {
      let d = await garantirDesafio();
      if (Date.now() - d.recebido > VIDA_DESAFIO_MS) { desafioP = null; d = await garantirDesafio(); }
      const espera = new Promise((ok) => setTimeout(ok, Math.max(0, d.recebido + ESPERA_MINIMA_MS - Date.now())));
      const [nonce] = await Promise.all([provaDeTrabalho(d.desafio, d.bits, mostrar), espera]);
      prova = { desafio: d.desafio, nonce };
    } catch {
      progresso.hidden = true;
      botao.disabled = false;
      status.className = 'relato-status erro';
      status.textContent = 'Não foi possível preparar o envio agora. Verifique a conexão e tente de novo; o que você escreveu continua aqui.';
      return;
    }
    mostrar(1);
    status.textContent = 'Enviando...';
    const corpo = {
      turno: Number(form.querySelector('#rel-turno').value) === 1 ? 1 : 2,
      uf, zona: Number(zona), secao: Number(s.secao),
      local_id: local && local.local_id ? local.local_id : null,
      tipo: tipo.value, texto: t, hora_aproximada: hora.value ? hora.value.slice(0, 5) : null,
      presenciou: (form.querySelector('input[name="rel-presenciou"]:checked') || {}).value !== 'nao',
      contato: c || null, versao: VERSAO_RELATO,
      website: form.querySelector('#rel-website').value,
      desafio: prova.desafio, nonce: prova.nonce,
    };
    desafioP = null; // cada desafio vale para um envio
    let r = null;
    let dados = null;
    try {
      r = await fetch(funcao, {
        method: 'POST', credentials: 'omit', referrerPolicy: 'no-referrer',
        headers: { 'Content-Type': 'application/json', apikey: CFG_REL.publishableKey || '', Authorization: `Bearer ${CFG_REL.publishableKey || ''}` },
        body: JSON.stringify(corpo),
      });
      dados = await r.json().catch(() => null);
    } catch {
      r = null;
    }
    if (r && r.ok && dados && dados.status === 'aceito') {
      relatosZona.delete(`${uf}|${zona}`);
      const ok = h('div', { class: 'relato-ok', role: 'status', tabindex: '-1' },
        h('p', {}, h('strong', {}, 'Relato recebido. Obrigado.')),
        h('p', {}, c ? 'Se precisarmos de mais detalhes, usamos o contato que você deixou.' : 'Ele entra anônimo na fila de avaliação.'),
        h('p', { class: 'ajuda' }, 'Um relato sozinho não prova o que aconteceu: ele ajuda a saber onde olhar a ata, o boletim e o log da urna.'));
      form.replaceWith(ok);
      ok.focus();
      pintarContagemRelatos(contagem, uf, zona, s.secao);
      return;
    }
    progresso.hidden = true;
    botao.disabled = false;
    status.className = 'relato-status erro';
    status.textContent = r && r.status === 429
      ? 'Você já mandou vários relatos na última hora. Tente de novo mais tarde.'
      : r && r.status === 400
        ? 'O servidor recusou algum campo. Confira o texto, a hora e o contato.'
        : r && r.status === 409
          ? 'Este envio já foi usado. Toque em enviar de novo.'
          : 'Não foi possível enviar agora. Verifique a conexão e tente de novo; o que você escreveu continua aqui.';
  });
  return h('article', { class: 'ficha relato', 'aria-labelledby': 'rel-titulo' },
    h('p', { class: 'kicker' }, 'Relatos'),
    h('h2', { id: 'rel-titulo' }, 'Notou algo na sua seção? Conte para a gente'),
    contagem,
    h('p', { class: 'ajuda' }, `O relato fica ligado à seção ${s.secao} da zona ${zona} (${uf === 'ZZ' ? 'Exterior' : uf}). Avaliamos cada um antes de qualquer análise.`),
    funcao ? form : aviso('O envio de relatos está indisponível nesta versão da página.', 'Indisponível'));
}


return { blocoRelato };
}
