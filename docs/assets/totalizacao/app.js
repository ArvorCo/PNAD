/* Totalização paralela: leitor dos QR codes do boletim de urna.
   Módulo ES2020, sem framework e sem etapa de build. Tudo roda no navegador:
   a imagem é decodificada e descartada; só o texto dos QR vai ao servidor.

   Uma tela em três estados: ler (câmera e pastilhas), conferir (cartão com os
   números) e enviado (resultado). Texto explicativo e fila ficam na ficha (dialog).
   Decodificador: BarcodeDetector nativo quando o navegador o tem; senão, zxing-wasm
   fixado por versão e conferido pela impressão digital SHA-384 do binário.
   Fila: IndexedDB, com reenvio por recuo exponencial quando a rede volta.
   Gancho de teste: com `#debug` na URL, window.__totalizacaoDebug.injetarQr(texto)
   alimenta o leitor sem câmera. */

const CFG = window.TOTALIZACAO_CONFIG || {};
const VERSAO = CFG.versao || 'dev';
const DEBUG = location.hash === '#debug';

const ZXING_VERSAO = '3.1.5';
const ZXING_BASE = `https://cdn.jsdelivr.net/npm/zxing-wasm@${ZXING_VERSAO}/`;
const ZXING_LEITOR = `${ZXING_BASE}dist/es/reader/index.js`;
const ZXING_WASM = `${ZXING_BASE}dist/reader/zxing_reader.wasm`;
const ZXING_WASM_SHA384 = 'j+oLlDZCHaKuYeJqIqchqHw7yQwrHwxW1e2QNwHZK2VYBAMb3k6q0u2JDzXSqTGW';
const OPCOES_ZXING = {
  formats: ['QRCode'],
  tryHarder: true,
  tryRotate: true,
  tryInvert: false,
  tryDownscale: true,
  maxNumberOfSymbols: 8,
  textMode: 'Plain',
};

const MENSAGENS = {
  aceito: 'BU recebido e verificado.',
  repetido: 'Esta seção já tinha sido enviada com o mesmo resultado; obrigado por confirmar.',
  conflito: 'Outro BU diferente já foi enviado para esta seção; o seu ficou registrado e a seção vai para revisão.',
};
const TITULOS = { aceito: 'Aceito', repetido: 'Repetido', conflito: 'Conflito', rejeitado: 'Rejeitado' };
const CARGOS = {
  1: 'Presidente', 3: 'Governador', 5: 'Senador', 6: 'Deputado federal', 7: 'Deputado estadual',
  8: 'Deputado distrital', 11: 'Prefeito', 13: 'Vereador',
};
const MAX_QRBU = 4;
const ESPERA_MAXIMA_MS = 10 * 60 * 1000;
const TEMPO_REQUISICAO_MS = 20000;
const HISTORICO_MAXIMO = 60;
const ICONES = {
  ok: '<svg viewBox="0 0 24 24" width="52" height="52" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  aviso: '<svg viewBox="0 0 24 24" width="52" height="52" aria-hidden="true"><path d="M12 4v10M12 18.5v.5" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg>',
  erro: '<svg viewBox="0 0 24 24" width="52" height="52" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg>',
  andamento: '<svg viewBox="0 0 24 24" width="52" height="52" aria-hidden="true"><path d="M12 3v4M12 17v4M3 12h4M17 12h4" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg>',
  camera: '<svg viewBox="0 0 24 24" width="40" height="40" aria-hidden="true"><path d="M4 7h3l2-2h6l2 2h3v12H4z" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="13" r="3.5" fill="none" stroke="currentColor" stroke-width="2"/></svg>',
  check: '<svg viewBox="0 0 24 24" width="40" height="40" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>',
};

/* ---------- utilidades ---------- */
const esperar = (ms) => new Promise((res) => setTimeout(res, ms));
function esc(valor) {
  return String(valor ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
function uuid() {
  if (crypto.randomUUID) return crypto.randomUUID();
  const b = crypto.getRandomValues(new Uint8Array(16));
  b[6] = (b[6] & 0x0f) | 0x40;
  b[8] = (b[8] & 0x3f) | 0x80;
  const h = [...b].map((x) => x.toString(16).padStart(2, '0')).join('');
  return `${h.slice(0, 8)}-${h.slice(8, 12)}-${h.slice(12, 16)}-${h.slice(16, 20)}-${h.slice(20)}`;
}
let aparelhoSessao = null;
function aparelhoId() {
  const chave = 'totalizacao.aparelho';
  try {
    const atual = localStorage.getItem(chave);
    if (atual && /^[0-9a-f-]{36}$/.test(atual)) return atual;
    const novo = uuid();
    localStorage.setItem(chave, novo);
    return novo;
  } catch {
    if (!aparelhoSessao) aparelhoSessao = uuid();
    return aparelhoSessao;
  }
}
function dataBr(aaaammdd) {
  const m = /^(\d{4})(\d{2})(\d{2})$/.exec(aaaammdd || '');
  return m ? `${m[3]}/${m[2]}/${m[1]}` : aaaammdd || null;
}
function horaBr(hhmmss) {
  const m = /^(\d{2})(\d{2})(\d{2})$/.exec(hhmmss || '');
  return m ? `${m[1]}:${m[2]}` : null;
}
function quandoBr(ms) {
  return new Date(ms).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
}
function vibrar(ms) {
  try { if (navigator.vibrate) navigator.vibrate(ms); } catch { /* sem vibração */ }
}

/* ---------- leitura do texto do QR ---------- */
const RE_CABECALHO = /^(QRBU|QRCE):(\d{1,2}):(\d{1,2})(?=\s|$)/;

function classificar(texto) {
  if (typeof texto !== 'string') return null;
  const m = RE_CABECALHO.exec(texto);
  if (!m) return null;
  return { tipo: m[1], indice: Number(m[2]), total: Number(m[3]), texto };
}
function tokens(texto) {
  return texto.split(/\s+/).filter(Boolean).map((tok) => {
    const i = tok.indexOf(':');
    return i < 0 ? [tok, ''] : [tok.slice(0, i), tok.slice(i + 1)];
  });
}
function valor(toks, chave) {
  const par = toks.find(([k]) => k === chave);
  return par ? par[1] : null;
}

function novoConjunto() {
  return { qrbu: new Map(), qrce: new Map(), totalQrbu: null, vrqr: null, idueBu: null, idueCe: null };
}
let conjunto = novoConjunto();

/* Aceita um texto lido e devolve {resultado, mensagem}.
   resultado: novo | repetido | ignorado | invalido | conflito. */
function aceitar(c, texto) {
  const cab = classificar(texto);
  if (!cab) {
    return { resultado: 'ignorado', mensagem: 'Este QR não é de boletim de urna. Procure os códigos QRBU e QRCE no fim do boletim.' };
  }
  const toks = tokens(cab.texto);
  if (cab.tipo === 'QRBU') {
    if (cab.total < 1 || cab.total > MAX_QRBU || cab.indice < 1 || cab.indice > cab.total) {
      return { resultado: 'invalido', mensagem: `Cabeçalho QRBU fora do padrão (parte ${cab.indice} de ${cab.total}).` };
    }
    const vrqr = valor(toks, 'VRQR');
    if (!vrqr) return { resultado: 'invalido', mensagem: 'QRBU sem a versão do formato (VRQR). Leia de novo.' };
    if (c.totalQrbu !== null && c.totalQrbu !== cab.total) {
      return { resultado: 'conflito', mensagem: `Este QRBU diz ter ${cab.total} partes e os já lidos dizem ${c.totalQrbu}. São boletins diferentes: recomece a leitura.` };
    }
    if (c.vrqr !== null && c.vrqr !== vrqr) {
      return { resultado: 'conflito', mensagem: `A versão deste QR (${vrqr}) difere da dos já lidos (${c.vrqr}). Recomece a leitura.` };
    }
    const idue = valor(toks, 'IDUE');
    if (idue && c.idueCe && idue !== c.idueCe) {
      return { resultado: 'conflito', mensagem: `Este boletim é da urna ${idue} e o certificado lido é da urna ${c.idueCe}. Recomece com os QR de um só boletim.` };
    }
    const existente = c.qrbu.get(cab.indice);
    if (existente) {
      if (existente === cab.texto) return { resultado: 'repetido', mensagem: `QRBU ${cab.indice} de ${cab.total} já estava lido.` };
      return { resultado: 'conflito', mensagem: `O QRBU ${cab.indice} já foi lido com outro conteúdo. Se este é o boletim certo, recomece a leitura.` };
    }
    c.qrbu.set(cab.indice, cab.texto);
    c.totalQrbu = cab.total;
    c.vrqr = vrqr;
    if (idue) c.idueBu = idue;
    return { resultado: 'novo', mensagem: `QRBU ${cab.indice} de ${cab.total} lido.` };
  }
  if (cab.total !== 2 || cab.indice < 1 || cab.indice > 2) {
    return { resultado: 'invalido', mensagem: `Cabeçalho QRCE fora do padrão (parte ${cab.indice} de ${cab.total}; o certificado tem 2).` };
  }
  const idue = valor(toks, 'IDUE');
  if (idue && c.idueCe && idue !== c.idueCe) {
    return { resultado: 'conflito', mensagem: `Os dois QRCE são de urnas diferentes (${c.idueCe} e ${idue}). Recomece a leitura.` };
  }
  if (idue && c.idueBu && idue !== c.idueBu) {
    return { resultado: 'conflito', mensagem: `O certificado é da urna ${idue} e o boletim lido é da urna ${c.idueBu}. Recomece com os QR de um só boletim.` };
  }
  const existente = c.qrce.get(cab.indice);
  if (existente) {
    if (existente === cab.texto) return { resultado: 'repetido', mensagem: `QRCE ${cab.indice} de 2 já estava lido.` };
    return { resultado: 'conflito', mensagem: `O QRCE ${cab.indice} já foi lido com outro conteúdo. Recomece a leitura.` };
  }
  c.qrce.set(cab.indice, cab.texto);
  if (idue) c.idueCe = idue;
  return { resultado: 'novo', mensagem: `QRCE ${cab.indice} de 2 lido.` };
}
function completo(c) {
  return c.totalQrbu !== null && c.qrbu.size === c.totalQrbu && c.qrce.size === 2;
}
function lidos(c) {
  return c.qrbu.size + c.qrce.size;
}
function esperados(c) {
  return c.totalQrbu === null ? null : c.totalQrbu + 2;
}
function faltam(c) {
  const f = [];
  if (c.totalQrbu === null) f.push('QRBU (o primeiro QR do boletim)');
  else for (let i = 1; i <= c.totalQrbu; i += 1) if (!c.qrbu.has(i)) f.push(`QRBU ${i} de ${c.totalQrbu}`);
  for (const i of [1, 2]) if (!c.qrce.has(i)) f.push(`QRCE ${i} de 2`);
  return f;
}
function textos(c) {
  const bu = [...c.qrbu.keys()].sort((a, b) => a - b).map((i) => c.qrbu.get(i));
  const ce = [...c.qrce.keys()].sort((a, b) => a - b).map((i) => c.qrce.get(i));
  return [...bu, ...ce];
}

/* Cabeçalho e totais por cargo a partir das partes QRBU já lidas.
   Uma parte continua a anterior: tira o cabeçalho QRBU/VRQR das continuações e o
   HASH/ASSI que fecha cada parte, e lê a sequência como um só texto. */
function resumir(c) {
  if (c.qrbu.size === 0) return null;
  const partes = [...c.qrbu.keys()].sort((a, b) => a - b);
  const toks = [];
  partes.forEach((indice) => {
    for (const [k, v] of tokens(c.qrbu.get(indice))) {
      if (k === 'QRBU' || k === 'HASH' || k === 'ASSI') continue;
      if (k === 'VRQR' && indice !== 1) continue;
      toks.push([k, v]);
    }
  });
  const cab = {};
  for (const ch of ['VRQR', 'UNFE', 'MUNI', 'ZONA', 'SECA', 'TURN', 'DTPL', 'PLEI', 'IDUE', 'LOCA', 'APTO', 'COMP', 'FALT', 'ORIG', 'DTFC', 'HRFC']) {
    cab[ch] = valor(toks, ch);
  }
  const cargos = [];
  let atual = null;
  for (const [k, v] of toks) {
    if (k === 'CARG') {
      atual = { carg: v, nome: CARGOS[Number(v)] || `Cargo ${v}`, tipo: null, votos: [], nomi: null, bran: null, nulo: null, totc: null };
      cargos.push(atual);
      continue;
    }
    if (k === 'IDEL') { atual = null; continue; }
    if (!atual) continue;
    if (k === 'TIPO') atual.tipo = v;
    else if (/^\d+$/.test(k)) atual.votos.push([k, Number(v)]);
    else if (k === 'NOMI') atual.nomi = Number(v);
    else if (k === 'BRAN') atual.bran = Number(v);
    else if (k === 'NULO') atual.nulo = Number(v);
    else if (k === 'TOTC') atual.totc = Number(v);
  }
  return { ...cab, cargos, temCabecalho: c.qrbu.has(1) };
}

/* ---------- decodificador ---------- */
let modo = null;
let detector = null;
let zx = null;
let zxCarregando = null;
const canvasTrabalho = document.createElement('canvas');

function carregarZxing() {
  if (zx) return Promise.resolve(zx);
  if (!zxCarregando) {
    zxCarregando = (async () => {
      const mod = await import(ZXING_LEITOR);
      const resp = await fetch(ZXING_WASM);
      if (!resp.ok) throw new Error(`zxing-wasm: HTTP ${resp.status} ao baixar o decodificador`);
      const bin = await resp.arrayBuffer();
      if (crypto.subtle) {
        const hash = await crypto.subtle.digest('SHA-384', bin);
        const b64 = btoa(String.fromCharCode(...new Uint8Array(hash)));
        if (b64 !== ZXING_WASM_SHA384) throw new Error('zxing-wasm: o decodificador baixado não bate com a impressão digital esperada');
      }
      await mod.prepareZXingModule({ overrides: { wasmBinary: bin }, fireImmediately: true });
      zx = mod;
      return zx;
    })().catch((e) => { zxCarregando = null; throw e; });
  }
  return zxCarregando;
}
async function prepararDetector() {
  if (modo) return modo;
  if ('BarcodeDetector' in window) {
    try {
      const formatos = await window.BarcodeDetector.getSupportedFormats();
      if (formatos.includes('qr_code')) {
        detector = new window.BarcodeDetector({ formats: ['qr_code'] });
        modo = 'nativo';
        return modo;
      }
    } catch { /* sem detector nativo utilizável: cai no zxing */ }
  }
  await carregarZxing();
  modo = 'zxing';
  return modo;
}
function imagemDe(fonte, maxLado) {
  const w = fonte.videoWidth || fonte.width;
  const h = fonte.videoHeight || fonte.height;
  if (!w || !h) return null;
  const escala = Math.min(1, maxLado / Math.max(w, h));
  const cw = Math.max(1, Math.round(w * escala));
  const ch = Math.max(1, Math.round(h * escala));
  canvasTrabalho.width = cw;
  canvasTrabalho.height = ch;
  const ctx = canvasTrabalho.getContext('2d', { willReadFrequently: true });
  ctx.drawImage(fonte, 0, 0, cw, ch);
  return ctx.getImageData(0, 0, cw, ch);
}
function descartarImagem() {
  canvasTrabalho.width = 1;
  canvasTrabalho.height = 1;
}
async function decodificarZxing(fonte, maxLado) {
  await carregarZxing();
  const img = imagemDe(fonte, maxLado);
  if (!img) return [];
  try {
    const res = await zx.readBarcodes(img, OPCOES_ZXING);
    return res.filter((r) => r.isValid && r.text).map((r) => r.text);
  } finally {
    descartarImagem();
  }
}
async function decodificar(fonte, maxLado = 1600) {
  if (modo === 'nativo') {
    try {
      const res = await detector.detect(fonte);
      return res.map((r) => r.rawValue).filter(Boolean);
    } catch {
      /* o serviço nativo falhou nesta plataforma: troca para o zxing daqui em diante */
      await carregarZxing();
      modo = 'zxing';
    }
  }
  return decodificarZxing(fonte, maxLado);
}

/* ---------- interface: elementos e estados ---------- */
const ui = {};
let tela = 'ler';
let aguardandoId = null;
function ligarDom() {
  for (const id of ['tela', 'tela-ler', 'tela-conferir', 'tela-enviado', 'leitor-status', 'partes', 'camera-caixa', 'video', 'pre-camera', 'pre-icone', 'pre-texto', 'btn-camera', 'btn-parar', 'btn-foto', 'arquivo', 'btn-lanterna', 'btn-recomecar', 'btn-conferir', 'cartao', 'btn-voltar', 'btn-enviar', 'resultado', 'btn-outro', 'texto-lido', 'toast', 'chip-pendentes', 'btn-info', 'ficha', 'btn-fechar-ficha', 'rede', 'fila-status', 'btn-reenviar', 'fila-lista', 'historico', 'turnstile']) {
    ui[id] = document.getElementById(id);
  }
}
function irPara(nova) {
  tela = nova;
  limparToast();
  ui['tela-ler'].hidden = nova !== 'ler';
  ui['tela-conferir'].hidden = nova !== 'conferir';
  ui['tela-enviado'].hidden = nova !== 'enviado';
  ui.tela.dataset.estado = nova;
  if (nova !== 'ler') pararCamera();
  if (nova === 'conferir') renderCartao();
  const foco = nova === 'conferir' ? ui['btn-enviar'] : nova === 'enviado' ? ui['btn-outro'] : null;
  if (foco && !foco.disabled) foco.focus({ preventScroll: true });
  if (nova === 'conferir') ui['tela-conferir'].querySelector('.conteudo').scrollTop = 0;
}
let toastTimer = null;
function toast(mensagem, classe = '', ms = 4500) {
  ui.toast.className = `toast ${classe}`;
  ui.toast.textContent = mensagem;
  clearTimeout(toastTimer);
  if (ms > 0) toastTimer = setTimeout(() => { ui.toast.textContent = ''; }, ms);
}
function limparToast() {
  clearTimeout(toastTimer);
  ui.toast.textContent = '';
}

/* ---------- interface: ler ---------- */
function renderPartes() {
  const c = conjunto;
  const itens = [];
  if (c.totalQrbu === null) {
    itens.push('<li class="pastilha falta">BU<b>?</b></li>');
  } else {
    for (let i = 1; i <= c.totalQrbu; i += 1) {
      itens.push(`<li class="pastilha ${c.qrbu.has(i) ? 'lido' : 'falta'}">BU<b>${i}/${c.totalQrbu}</b></li>`);
    }
  }
  for (const i of [1, 2]) itens.push(`<li class="pastilha ${c.qrce.has(i) ? 'lido' : 'falta'}">Cert<b>${i}/2</b></li>`);
  ui.partes.innerHTML = itens.join('');
  const n = lidos(c);
  const total = esperados(c);
  let texto;
  if (n === 0) texto = 'Nenhum QR lido ainda.';
  else if (completo(c)) texto = `QR ${n} de ${total} lido. Tudo lido: toque em Conferir.`;
  else if (total === null) texto = `${n} QR lido${n > 1 ? 's' : ''}. Falta o QRBU para saber o total.`;
  else texto = `QR ${n} de ${total} lido${n > 1 ? 's' : ''}. Falta: ${faltam(c).join(', ')}.`;
  ui['leitor-status'].textContent = texto;
  const pronto = completo(c);
  ui['btn-conferir'].disabled = !pronto;
  ui['btn-enviar'].disabled = !pronto || aguardandoId !== null;
  ui['pre-camera'].classList.toggle('completo', pronto);
  ui['pre-icone'].innerHTML = pronto ? ICONES.check : ICONES.camera;
  ui['pre-texto'].textContent = pronto
    ? 'Todos os QR lidos. Toque em Conferir.'
    : n > 0 ? `Falta: ${faltam(c).join(', ')}.` : 'Aponte para os QR do fim do boletim, um por vez, até o quadro.';
  ui['btn-camera'].textContent = n > 0 && !pronto ? 'Continuar na câmera' : 'Abrir câmera';
  ui['btn-camera'].hidden = pronto;
  ui['texto-lido'].textContent = textos(c).join('\n\n') || 'Nenhum QR lido.';
}
function registrar(texto, origem) {
  const r = aceitar(conjunto, texto);
  if (r.resultado === 'novo') {
    vibrar(60);
    renderPartes();
    ui['camera-caixa'].classList.add('lido');
    setTimeout(() => ui['camera-caixa'].classList.remove('lido'), 700);
    if (completo(conjunto)) {
      pararCamera();
      toast('Tudo lido. Toque em Conferir.', 'ok');
    } else {
      toast(r.mensagem, 'ok', 2500);
    }
  } else if (r.resultado === 'repetido') {
    toast(r.mensagem, '', 2500);
  } else {
    vibrar([40, 60, 40]);
    toast(r.mensagem, 'erro', r.resultado === 'conflito' ? 0 : 6000);
  }
  if (origem !== 'câmera') renderPartes();
  return r;
}
function recomecar() {
  conjunto = novoConjunto();
  aguardandoId = null;
  limparToast();
  ui.resultado.innerHTML = '';
  renderPartes();
  irPara('ler');
}

/* ---------- câmera ---------- */
let stream = null;
let lendo = false;
let pausaAte = 0;
async function abrirCamera() {
  ui['btn-camera'].disabled = true;
  try {
    await prepararDetector();
  } catch (e) {
    toast(`Não consegui carregar o decodificador (${e.message}). Tente com rede ou escolha uma foto.`, 'erro', 0);
    ui['btn-camera'].disabled = false;
    return;
  }
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    toast('Este navegador não dá acesso à câmera. Use "Escolher foto".', 'erro', 0);
    ui['btn-camera'].disabled = false;
    return;
  }
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      audio: false,
      video: { facingMode: { ideal: 'environment' }, width: { ideal: 1920 }, height: { ideal: 1080 } },
    });
  } catch (e) {
    const negada = e && (e.name === 'NotAllowedError' || e.name === 'SecurityError');
    toast(negada
      ? 'Sem permissão para a câmera. Libere nas configurações do navegador ou escolha uma foto.'
      : 'A câmera não abriu. Feche outros aplicativos que a usem ou escolha uma foto.', 'erro', 0);
    ui['btn-camera'].disabled = false;
    return;
  }
  ui.video.srcObject = stream;
  ui.video.hidden = false;
  ui['camera-caixa'].querySelector('.mira').hidden = false;
  ui['pre-camera'].hidden = true;
  ui['btn-parar'].hidden = false;
  try { await ui.video.play(); } catch { /* o autoplay inline pode exigir gesto; o botão já foi um */ }
  const trilha = stream.getVideoTracks()[0];
  const caps = trilha && trilha.getCapabilities ? trilha.getCapabilities() : {};
  if (Array.isArray(caps.focusMode) && caps.focusMode.includes('continuous')) {
    trilha.applyConstraints({ advanced: [{ focusMode: 'continuous' }] }).catch(() => {});
  }
  ui['btn-lanterna'].hidden = !caps.torch;
  ui['btn-lanterna'].setAttribute('aria-pressed', 'false');
  lendo = true;
  lacoDeLeitura();
}
async function lacoDeLeitura() {
  while (lendo && stream) {
    if (ui.video.readyState >= 2 && Date.now() >= pausaAte) {
      let achados = [];
      try {
        achados = await decodificar(ui.video);
      } catch { /* quadro ruim: tenta o próximo */ }
      for (const t of achados) {
        const r = registrar(t, 'câmera');
        if (r.resultado === 'novo') pausaAte = Date.now() + 900;
      }
    }
    await esperar(modo === 'nativo' ? 120 : 220);
  }
}
function pararCamera() {
  lendo = false;
  if (stream) {
    for (const t of stream.getTracks()) t.stop();
    stream = null;
  }
  if (!ui.video) return;
  ui.video.srcObject = null;
  ui.video.hidden = true;
  ui['camera-caixa'].querySelector('.mira').hidden = true;
  ui['pre-camera'].hidden = false;
  ui['btn-parar'].hidden = true;
  ui['btn-lanterna'].hidden = true;
  ui['btn-camera'].disabled = false;
}
async function alternarLanterna() {
  if (!stream) return;
  const trilha = stream.getVideoTracks()[0];
  const ligada = ui['btn-lanterna'].getAttribute('aria-pressed') === 'true';
  try {
    await trilha.applyConstraints({ advanced: [{ torch: !ligada }] });
    ui['btn-lanterna'].setAttribute('aria-pressed', String(!ligada));
  } catch {
    toast('A lanterna não respondeu neste aparelho.');
  }
}

/* ---------- foto da galeria ---------- */
async function lerArquivos(arquivos) {
  ui['btn-foto'].disabled = true;
  try {
    await prepararDetector();
  } catch (e) {
    toast(`Não consegui carregar o decodificador (${e.message}). Tente de novo com rede.`, 'erro', 0);
    ui['btn-foto'].disabled = false;
    return;
  }
  for (const arq of arquivos) {
    if (!arq.type.startsWith('image/')) {
      toast(`"${arq.name}" não é imagem.`, 'erro');
      continue;
    }
    let bitmap = null;
    try {
      bitmap = await createImageBitmap(arq);
    } catch {
      toast(`Não consegui abrir "${arq.name}".`, 'erro');
      continue;
    }
    let achados = [];
    try { achados = await decodificar(bitmap, 2400); } catch { /* tenta abaixo */ }
    if (achados.length === 0 && modo === 'nativo') {
      try { achados = await decodificarZxing(bitmap, 2400); } catch { /* sem rede para o zxing: fica o nativo */ }
    }
    if (achados.length === 0) {
      try { achados = await decodificarZxing(bitmap, 4096); } catch { /* idem */ }
    }
    if (bitmap.close) bitmap.close();
    if (achados.length === 0) {
      toast('Nenhum QR legível nesta foto. Fotografe mais de perto, um QR por vez, sem sombra nem reflexo.', 'erro', 0);
      continue;
    }
    for (const t of achados) registrar(t, 'foto');
  }
  ui.arquivo.value = '';
  ui['btn-foto'].disabled = false;
}

/* ---------- interface: conferir ---------- */
function celula(rotulo, valorTexto, extra = '', largo = false) {
  const vazio = valorTexto === null || valorTexto === undefined || valorTexto === '';
  return `<div${largo ? ' class="largo"' : ''}><span class="rot">${esc(rotulo)}</span><b>${vazio ? '?' : esc(valorTexto)}</b>${extra ? `<small>${esc(extra)}</small>` : ''}</div>`;
}
function renderCartao() {
  const r = resumir(conjunto);
  const h = r && r.temCabecalho ? r : {};
  const encerramento = h.DTFC ? `${dataBr(h.DTFC)}${horaBr(h.HRFC) ? ` às ${horaBr(h.HRFC)}` : ''}` : null;
  const cargos = !r || r.cargos.length === 0
    ? '<div class="cargo"><p class="fila-vazia">Nenhum cargo lido.</p></div>'
    : r.cargos.map((cg) => {
      const totais = [
        ['Nominais', cg.nomi], ['Brancos', cg.bran], ['Nulos', cg.nulo], ['Total', cg.totc],
      ].map(([rot, v]) => `<li>${esc(rot)}<b>${v === null ? '?' : esc(v)}</b></li>`).join('');
      const votos = cg.tipo === '0' && cg.votos.length
        ? `<p class="votos">Por número: ${cg.votos.map(([num, v]) => `<b>${esc(num)}</b> ${esc(v)}`).join(' · ')}</p>`
        : '';
      return `<div class="cargo"><h4>${esc(cg.nome)}</h4><ul class="totais">${totais}</ul>${votos}</div>`;
    }).join('');
  ui.cartao.innerHTML = `
    <div class="cartao-topo">
      <div><span class="rot">UF</span><b>${esc(h.UNFE || '?')}</b></div>
      <div><span class="rot">Seção</span><b>${esc(h.SECA || '?')}</b></div>
    </div>
    <div class="cartao-grade">
      ${celula('Município', h.MUNI, 'código TSE')}
      ${celula('Zona', h.ZONA)}
      ${celula('Turno', h.TURN ? `${h.TURN}º` : null, h.DTPL ? `pleito de ${dataBr(h.DTPL)}` : '')}
      ${celula('Comparecimento', h.COMP, h.APTO ? `de ${h.APTO} aptos; ${h.FALT ?? '?'} faltas` : '')}
      ${celula('Urna', h.IDUE, h.LOCA ? `local ${h.LOCA}` : '', true)}
      ${celula('Encerramento', encerramento, '', true)}
    </div>
    <div class="cargos">${cargos}</div>`;
}

/* ---------- fila em IndexedDB ---------- */
const DB_NOME = 'totalizacao';
const DB_VERSAO = 1;
let dbPromessa = null;
let semIdb = false;
const memoria = { fila: new Map(), historico: new Map() };
function db() {
  if (dbPromessa) return dbPromessa;
  dbPromessa = new Promise((res, rej) => {
    if (!('indexedDB' in window)) { rej(new Error('IndexedDB indisponível')); return; }
    const req = indexedDB.open(DB_NOME, DB_VERSAO);
    req.onupgradeneeded = () => {
      const d = req.result;
      if (!d.objectStoreNames.contains('fila')) d.createObjectStore('fila', { keyPath: 'id' });
      if (!d.objectStoreNames.contains('historico')) d.createObjectStore('historico', { keyPath: 'id' });
    };
    req.onsuccess = () => res(req.result);
    req.onerror = () => rej(req.error || new Error('IndexedDB falhou'));
    req.onblocked = () => rej(new Error('IndexedDB bloqueado'));
  }).catch((e) => { dbPromessa = null; throw e; });
  return dbPromessa;
}
function tx(loja, modoTx, fn) {
  return db().then((d) => new Promise((res, rej) => {
    const t = d.transaction(loja, modoTx);
    const r = fn(t.objectStore(loja));
    t.oncomplete = () => res(r && 'result' in r ? r.result : undefined);
    t.onerror = () => rej(t.error);
    t.onabort = () => rej(t.error || new Error('transação abortada'));
  }));
}
const filaApi = {
  async listar() {
    try {
      const itens = await tx('fila', 'readonly', (s) => s.getAll());
      return itens.sort((a, b) => a.criado - b.criado);
    } catch {
      semIdb = true;
      return [...memoria.fila.values()].sort((a, b) => a.criado - b.criado);
    }
  },
  async gravar(item) {
    try { await tx('fila', 'readwrite', (s) => s.put(item)); } catch { semIdb = true; memoria.fila.set(item.id, item); }
  },
  async remover(id) {
    try { await tx('fila', 'readwrite', (s) => s.delete(id)); } catch { semIdb = true; }
    memoria.fila.delete(id);
  },
};
const historicoApi = {
  async listar() {
    try {
      const itens = await tx('historico', 'readonly', (s) => s.getAll());
      return itens.sort((a, b) => b.quando - a.quando);
    } catch {
      return [...memoria.historico.values()].sort((a, b) => b.quando - a.quando);
    }
  },
  async gravar(reg) {
    try {
      await tx('historico', 'readwrite', (s) => s.put(reg));
      const todos = await this.listar();
      for (const velho of todos.slice(HISTORICO_MAXIMO)) {
        await tx('historico', 'readwrite', (s) => s.delete(velho.id));
      }
    } catch {
      memoria.historico.set(reg.id, reg);
    }
  },
};

/* ---------- envio ---------- */
let turnstilePromessa = null;
function carregarTurnstile() {
  if (turnstilePromessa) return turnstilePromessa;
  turnstilePromessa = new Promise((res, rej) => {
    const s = document.createElement('script');
    s.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit';
    s.async = true;
    s.onload = () => res(window.turnstile);
    s.onerror = () => rej(new Error('Turnstile não carregou'));
    document.head.appendChild(s);
  }).catch((e) => { turnstilePromessa = null; throw e; });
  return turnstilePromessa;
}
async function obterTurnstile() {
  if (!CFG.turnstileSiteKey) return null;
  try {
    const ts = await carregarTurnstile();
    return await new Promise((res) => {
      const alvo = ui.turnstile;
      alvo.innerHTML = '';
      const timer = setTimeout(() => res(null), 20000);
      const id = ts.render(alvo, {
        sitekey: CFG.turnstileSiteKey,
        size: 'flexible',
        appearance: 'interaction-only',
        language: 'pt-br',
        callback: (token) => { clearTimeout(timer); res(token); },
        'error-callback': () => { clearTimeout(timer); res(null); },
        'expired-callback': () => { clearTimeout(timer); res(null); },
      });
      if (!id) { clearTimeout(timer); res(null); }
    });
  } catch {
    return null;
  }
}
function descreverErro(r) {
  if (r.http) return `O servidor respondeu HTTP ${r.http}.`;
  if (r.erro && r.erro.name === 'AbortError') return 'O servidor demorou mais de 20 segundos.';
  return 'Sem conexão com o servidor.';
}
async function enviar(qr) {
  if (!CFG.funcaoUrl) return { tipo: 'temporario', erro: new Error('sem funcaoUrl') };
  const turnstile = await obterTurnstile();
  const corpo = { qr, aparelho: aparelhoId(), turnstile, versao: VERSAO };
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), TEMPO_REQUISICAO_MS);
  try {
    const resp = await fetch(CFG.funcaoUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        apikey: CFG.publishableKey || '',
        Authorization: `Bearer ${CFG.publishableKey || ''}`,
      },
      body: JSON.stringify(corpo),
      signal: ctrl.signal,
    });
    let dados = null;
    try { dados = await resp.json(); } catch { dados = null; }
    if (dados && typeof dados.status === 'string') return { tipo: 'resposta', dados, http: resp.status };
    return { tipo: 'temporario', http: resp.status };
  } catch (erro) {
    return { tipo: 'temporario', erro };
  } finally {
    clearTimeout(timer);
  }
}
function espera(tentativas) {
  const base = 20000 * 2 ** Math.min(tentativas, 6);
  return Math.min(ESPERA_MAXIMA_MS, base) * (0.8 + Math.random() * 0.4);
}
let processando = false;
let timerFila = null;

/* ---------- interface: enviado, chip e ficha ---------- */
function telaResultado(classe, titulo, texto, detalhe = '') {
  ui.resultado.className = `conteudo resultado-cheio ${classe}`;
  ui.resultado.innerHTML = `<div class="icone">${ICONES[classe] || ICONES.ok}</div><h2>${esc(titulo)}</h2><p>${esc(texto)}</p>${detalhe ? `<small>${esc(detalhe)}</small>` : ''}`;
  ui['btn-outro'].disabled = classe === 'andamento';
}
function mostrarResultado(reg) {
  const classe = reg.status === 'aceito' ? 'ok' : reg.status === 'rejeitado' ? 'erro' : 'aviso';
  const titulo = TITULOS[reg.status] || `Resposta: ${reg.status}`;
  let texto = MENSAGENS[reg.status];
  if (!texto) texto = reg.status === 'rejeitado' ? `Boletim rejeitado: ${reg.motivo || 'motivo não informado'}.` : (reg.motivo || 'Resposta sem explicação do servidor.');
  const r = reg.resumo || {};
  const bu = reg.bu
    ? `UF ${reg.bu.uf} · município ${reg.bu.muni} · zona ${reg.bu.zona} · seção ${reg.bu.secao}${reg.bu.hash ? ` · hash ${String(reg.bu.hash).slice(0, 16)}` : ''}`
    : `UF ${r.uf || '?'} · zona ${r.zona || '?'} · seção ${r.secao || '?'}`;
  telaResultado(classe, titulo, texto, bu);
  if (tela !== 'enviado') irPara('enviado');
  vibrar(classe === 'ok' ? 80 : [40, 60, 40]);
}
function mostrarPendente() {
  const extra = semIdb ? ' Este navegador não guarda a fila entre sessões: não feche a página até o envio.' : '';
  conjunto = novoConjunto();
  aguardandoId = null;
  renderPartes();
  irPara('ler');
  toast(`Sem rede. Guardado no aparelho, envio automático ao voltar.${extra}`, '', 7000);
}
async function renderChip() {
  const itens = await filaApi.listar();
  const n = itens.length;
  const on = navigator.onLine;
  const partes = [];
  if (n > 0) partes.push(`${n} na fila`);
  if (!on) partes.push('sem rede');
  ui['chip-pendentes'].hidden = partes.length === 0;
  ui['chip-pendentes'].innerHTML = n > 0
    ? `${n}<span class="visually-hidden"> na fila</span>${on ? '' : ' · sem rede'}`
    : 'sem rede';
  ui['chip-pendentes'].classList.toggle('off', !on);
  ui['chip-pendentes'].setAttribute('aria-label', n > 0 ? `${n} boletins aguardando envio. Abrir a lista` : 'Sem conexão. Abrir a lista de envios');
  ui.rede.textContent = on ? 'Com conexão' : 'Sem conexão: os envios ficam guardados';
  ui.rede.classList.toggle('off', !on);
  return itens;
}
async function renderFila(enviandoId = null) {
  const itens = await renderChip();
  const n = itens.length;
  ui['fila-status'].textContent = n === 0
    ? 'Nenhum boletim aguardando envio.'
    : `${n} boletim${n > 1 ? 's' : ''} aguardando envio.`;
  ui['btn-reenviar'].disabled = n === 0 || processando;
  ui['fila-lista'].innerHTML = itens.map((it) => {
    const r = it.resumo || {};
    const estado = it.id === enviandoId ? 'enviando agora' : it.tentativas ? `${it.tentativas} tentativa${it.tentativas > 1 ? 's' : ''}; ${it.ultimoErro || ''} Próxima às ${quandoBr(it.proximo).slice(-5)}.` : 'aguardando a primeira tentativa';
    return `<li><b>${esc(r.uf || '?')} · zona ${esc(r.zona || '?')} · seção ${esc(r.secao || '?')}</b><span>Lido em ${esc(quandoBr(it.criado))}. ${esc(estado)}</span></li>`;
  }).join('');
  const hist = await historicoApi.listar();
  ui.historico.innerHTML = hist.length === 0
    ? '<li class="fila-vazia">Nenhum envio concluído neste aparelho.</li>'
    : hist.map((h) => {
      const r = h.resumo || {};
      const selo = h.status === 'aceito' ? '' : h.status === 'rejeitado' ? 'erro-selo' : 'aviso-selo';
      const detalhe = h.status === 'rejeitado' ? (h.motivo || 'sem motivo informado') : (MENSAGENS[h.status] || h.status);
      return `<li><span class="selo ${selo}">${esc(TITULOS[h.status] || h.status)}</span><b>${esc(r.uf || '?')} · zona ${esc(r.zona || '?')} · seção ${esc(r.secao || '?')}</b><span>${esc(quandoBr(h.quando))}. ${esc(detalhe)}</span></li>`;
    }).join('');
}
async function agendarFila() {
  clearTimeout(timerFila);
  const itens = await filaApi.listar();
  if (itens.length === 0) return;
  const prox = Math.min(...itens.map((i) => i.proximo || 0));
  timerFila = setTimeout(() => { processarFila(false); }, Math.max(1000, prox - Date.now()));
}
async function processarFila(forcar = false) {
  if (processando) return;
  processando = true;
  clearTimeout(timerFila);
  try {
    if (!navigator.onLine && !forcar) return;
    const itens = await filaApi.listar();
    const agora = Date.now();
    for (const item of itens) {
      if (!forcar && (item.proximo || 0) > agora) continue;
      await renderFila(item.id);
      const r = await enviar(item.qr);
      if (r.tipo === 'resposta') {
        await filaApi.remover(item.id);
        const reg = {
          id: item.id, quando: Date.now(), resumo: item.resumo,
          status: r.dados.status, motivo: r.dados.motivo ?? null, bu: r.dados.bu ?? null,
        };
        await historicoApi.gravar(reg);
        if (item.id === aguardandoId) mostrarResultado(reg);
        else if (tela === 'ler') toast(`Boletim da seção ${reg.resumo && reg.resumo.secao ? reg.resumo.secao : '?'} enviado: ${TITULOS[reg.status] || reg.status}.`, 'ok');
      } else {
        item.tentativas = (item.tentativas || 0) + 1;
        item.proximo = Date.now() + espera(item.tentativas);
        item.ultimoErro = descreverErro(r);
        await filaApi.gravar(item);
        if (item.id === aguardandoId) mostrarPendente();
      }
    }
  } finally {
    processando = false;
    await agendarFila();
    await renderFila();
  }
}
async function aoEnviar() {
  if (!completo(conjunto) || aguardandoId !== null) return;
  const r = resumir(conjunto) || {};
  const item = {
    id: uuid(),
    qr: textos(conjunto),
    resumo: { uf: r.UNFE, muni: r.MUNI, zona: r.ZONA, secao: r.SECA, turno: r.TURN },
    criado: Date.now(),
    tentativas: 0,
    proximo: 0,
    ultimoErro: null,
  };
  aguardandoId = item.id;
  ui['btn-enviar'].disabled = true;
  limparToast();
  telaResultado('andamento', 'Enviando', 'Conferindo o boletim no servidor.');
  irPara('enviado');
  await filaApi.gravar(item);
  await processarFila(true);
}
function abrirFicha(alvo) {
  const f = ui.ficha;
  if (typeof f.showModal === 'function') {
    if (!f.open) f.showModal();
  } else {
    f.setAttribute('open', '');
  }
  if (alvo) {
    const sec = document.getElementById(alvo);
    if (sec) sec.scrollIntoView({ block: 'start' });
  } else {
    f.scrollTop = 0;
  }
}
function fecharFicha() {
  const f = ui.ficha;
  if (f.open) f.close();
}

/* ---------- service worker ---------- */
function registrarServiceWorker() {
  if (!('serviceWorker' in navigator) || location.protocol === 'file:') return;
  const jaControlada = Boolean(navigator.serviceWorker.controller);
  navigator.serviceWorker.register('totalizacao-sw.js', { scope: 'totalizacao' }).then((reg) => {
    reg.addEventListener('updatefound', () => {
      const novo = reg.installing;
      if (!novo || !jaControlada) return; /* primeira instalação não é atualização */
      novo.addEventListener('statechange', () => {
        if (novo.state === 'activated') toast('Aplicativo atualizado. Recarregue a página quando terminar o envio em curso.', '', 8000);
      });
    });
  }).catch(() => { /* sem service worker: a página segue funcionando com rede */ });
}

/* ---------- arranque ---------- */
function iniciar() {
  ligarDom();
  fecharFicha();
  renderPartes();
  renderFila();
  irPara('ler');
  ui['btn-camera'].disabled = false;
  ui['btn-foto'].disabled = false;
  ui['btn-camera'].addEventListener('click', abrirCamera);
  ui['btn-parar'].addEventListener('click', pararCamera);
  ui['btn-lanterna'].addEventListener('click', alternarLanterna);
  ui['btn-foto'].addEventListener('click', () => ui.arquivo.click());
  ui.arquivo.addEventListener('change', () => { if (ui.arquivo.files && ui.arquivo.files.length) lerArquivos([...ui.arquivo.files]); });
  ui['btn-recomecar'].addEventListener('click', () => { pararCamera(); recomecar(); });
  ui['btn-conferir'].addEventListener('click', () => { if (completo(conjunto)) irPara('conferir'); });
  ui['btn-voltar'].addEventListener('click', () => irPara('ler'));
  ui['btn-enviar'].addEventListener('click', aoEnviar);
  ui['btn-outro'].addEventListener('click', recomecar);
  ui['btn-reenviar'].addEventListener('click', () => processarFila(true));
  ui['btn-info'].addEventListener('click', () => abrirFicha());
  ui['chip-pendentes'].addEventListener('click', () => abrirFicha('envios'));
  ui['btn-fechar-ficha'].addEventListener('click', fecharFicha);
  ui.ficha.addEventListener('click', (ev) => { if (ev.target === ui.ficha) fecharFicha(); });
  window.addEventListener('online', () => { renderChip(); processarFila(false); });
  window.addEventListener('offline', () => { renderChip(); });
  document.addEventListener('visibilitychange', () => { if (document.hidden) pararCamera(); });
  window.addEventListener('pagehide', pararCamera);
  registrarServiceWorker();
  if (DEBUG) {
    window.__totalizacaoDebug = {
      injetarQr: (texto) => registrar(texto, 'debug'),
      estado: () => ({ tela, lidos: lidos(conjunto), esperados: esperados(conjunto), completo: completo(conjunto), faltam: faltam(conjunto) }),
      resumo: () => resumir(conjunto),
      fila: () => filaApi.listar(),
      historico: () => historicoApi.listar(),
      processarFila: () => processarFila(true),
      enviar: aoEnviar,
      irPara,
      recomecar,
      aparelho: aparelhoId,
      classificar,
      aceitar: (texto) => aceitar(novoConjunto(), texto),
    };
  }
}
iniciar();
