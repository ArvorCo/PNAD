// Card de compartilhamento, 1080 × 1080, desenhado no navegador.
// Escrito à mão. A composição é a da bandeira: campo verde, losango amarelo, disco azul com o
// índice e a faixa branca levando o nome do arquétipo. Nenhum número é calculado aqui.

const W = 1080;
const VERDE = '#0b7a3b';
const VERDE_ESC = '#095f2e';
const AMARELO = '#f2c230';
const AZUL = '#0d2238';
const BRANCO = '#ffffff';
const FD = 'Fraunces, Georgia, serif';
const FS = '"IBM Plex Sans Condensed", Arial, sans-serif';
const FM = '"IBM Plex Mono", ui-monospace, monospace';

async function garantirFontes() {
  if (!document.fonts || !document.fonts.load) return;
  try {
    await Promise.all([
      document.fonts.load(`900 120px ${FD}`),
      document.fonts.load(`700 40px ${FD}`),
      document.fonts.load(`600 30px ${FS}`),
      document.fonts.load(`700 24px ${FM}`),
    ]);
  } catch {
    // Sem a fonte da casa o card sai com a fonte de reserva. Não é erro.
  }
}

function quebrar(ctx, texto, largura, maxLinhas) {
  const palavras = String(texto || '').split(/\s+/).filter(Boolean);
  const linhas = [];
  let atual = '';
  for (const p of palavras) {
    const teste = atual ? `${atual} ${p}` : p;
    if (ctx.measureText(teste).width <= largura || !atual) {
      atual = teste;
    } else {
      linhas.push(atual);
      atual = p;
      if (linhas.length === maxLinhas) break;
    }
  }
  if (linhas.length < maxLinhas && atual) linhas.push(atual);
  if (linhas.length === maxLinhas && palavras.join(' ').length > linhas.join(' ').length) {
    let ult = linhas[maxLinhas - 1];
    while (ult.length > 1 && ctx.measureText(`${ult}…`).width > largura) ult = ult.slice(0, -1);
    linhas[maxLinhas - 1] = `${ult.trimEnd()}…`;
  }
  return linhas;
}

function ajustarFonte(ctx, texto, peso, familia, tamMax, tamMin, largura, maxLinhas) {
  for (let t = tamMax; t >= tamMin; t -= 2) {
    ctx.font = `${peso} ${t}px ${familia}`;
    const l = quebrar(ctx, texto, largura, maxLinhas + 1);
    if (l.length <= maxLinhas) return t;
  }
  return tamMin;
}

/** Texto ao longo de um arco (centro cx, cy; raio R), centrado no topo do arco. */
function textoNoArco(ctx, texto, cx, cy, R) {
  const larg = ctx.measureText(texto).width;
  let ang = -Math.PI / 2 - larg / (2 * R);
  for (const ch of texto) {
    const w = ctx.measureText(ch).width;
    const a = ang + w / (2 * R);
    ctx.save();
    ctx.translate(cx + R * Math.cos(a), cy + R * Math.sin(a));
    ctx.rotate(a + Math.PI / 2);
    ctx.fillText(ch, 0, 0);
    ctx.restore();
    ang += w / R;
  }
}

/**
 * @param {HTMLCanvasElement} canvas
 * @param {object} d {kicker, nome, lugar, arquetipo, indice, numeros: [{valor, rotulo}], frase, rodape: [linha1, linha2]}
 */
export async function desenharCard(canvas, d) {
  await garantirFontes();
  canvas.width = W;
  canvas.height = W;
  const ctx = canvas.getContext('2d');
  ctx.textBaseline = 'alphabetic';

  // campo verde com linhas finas diagonais
  ctx.fillStyle = VERDE;
  ctx.fillRect(0, 0, W, W);
  ctx.save();
  ctx.strokeStyle = 'rgba(255,255,255,0.045)';
  ctx.lineWidth = 2;
  for (let x = -W; x < W * 2; x += 26) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x + W, W);
    ctx.stroke();
  }
  ctx.restore();
  ctx.fillStyle = VERDE_ESC;
  ctx.fillRect(0, 760, W, W - 760);

  // cabeçalho
  ctx.fillStyle = AMARELO;
  ctx.font = `700 24px ${FM}`;
  ctx.textAlign = 'left';
  ctx.fillText((d.kicker || 'BOLETIM DA VIZINHANÇA').toUpperCase(), 64, 82);

  const tNome = ajustarFonte(ctx, d.nome, 900, FD, 56, 36, W - 128, 2);
  ctx.font = `900 ${tNome}px ${FD}`;
  ctx.fillStyle = BRANCO;
  const lNome = quebrar(ctx, d.nome, W - 128, 2);
  lNome.forEach((l, i) => ctx.fillText(l, 64, 82 + 18 + tNome * (i + 1)));
  const yLugar = 82 + 18 + tNome * lNome.length + 40;
  ctx.font = `600 28px ${FS}`;
  ctx.fillStyle = '#e3f1e7';
  ctx.fillText(quebrar(ctx, d.lugar, W - 128, 1)[0] || '', 64, yLugar);

  // losango e disco
  const cy = 530;
  const hw = 410;
  const hh = Math.min(230, 760 - cy - 6);
  ctx.fillStyle = AMARELO;
  ctx.beginPath();
  ctx.moveTo(W / 2 - hw, cy);
  ctx.lineTo(W / 2, cy - hh);
  ctx.lineTo(W / 2 + hw, cy);
  ctx.lineTo(W / 2, cy + hh);
  ctx.closePath();
  ctx.fill();

  const R = 172;
  ctx.fillStyle = AZUL;
  ctx.beginPath();
  ctx.arc(W / 2, cy, R, 0, Math.PI * 2);
  ctx.fill();

  ctx.save();
  ctx.beginPath();
  ctx.arc(W / 2, cy, R, 0, Math.PI * 2);
  ctx.clip();
  const bandaR = 560;
  const bandaCy = cy + 52 + bandaR;
  ctx.strokeStyle = BRANCO;
  ctx.lineWidth = 58;
  ctx.beginPath();
  ctx.arc(W / 2, bandaCy, bandaR, Math.PI * 1.2, Math.PI * 1.8);
  ctx.stroke();
  ctx.restore();

  ctx.textAlign = 'center';
  ctx.fillStyle = BRANCO;
  ctx.font = `900 132px ${FD}`;
  ctx.fillText(d.indice === null || d.indice === undefined ? 's/d' : String(d.indice), W / 2, cy + 8);

  const nomeArq = String(d.arquetipo || '').toUpperCase();
  let tArq = 32;
  ctx.font = `700 ${tArq}px ${FS}`;
  while (tArq > 18 && ctx.measureText(nomeArq).width > 300) {
    tArq -= 2;
    ctx.font = `700 ${tArq}px ${FS}`;
  }
  ctx.fillStyle = VERDE_ESC;
  ctx.textAlign = 'center';
  textoNoArco(ctx, nomeArq, W / 2, bandaCy, bandaR - tArq * 0.36);

  ctx.font = `700 19px ${FM}`;
  ctx.fillStyle = '#ffcc29';
  textoNoArco(ctx, 'ÍNDICE DE CONVERSA', W / 2, cy, R - 24);
  ctx.font = `700 22px ${FM}`;
  ctx.fillText('DE 100', W / 2, cy + 128);

  // três números
  const nums = (d.numeros || []).slice(0, 3);
  const col = (W - 128) / Math.max(1, nums.length);
  nums.forEach((n, i) => {
    const x = 64 + col * i + col / 2;
    ctx.textAlign = 'center';
    ctx.fillStyle = BRANCO;
    ctx.font = `900 60px ${FD}`;
    ctx.fillText(String(n.valor), x, 840);
    ctx.font = `700 19px ${FM}`;
    ctx.fillStyle = '#d6ecdd';
    quebrar(ctx, String(n.rotulo).toUpperCase(), col - 24, 2).forEach((l, j) => ctx.fillText(l, x, 872 + j * 24));
  });

  // frase
  ctx.textAlign = 'left';
  ctx.fillStyle = BRANCO;
  ctx.font = `600 27px ${FS}`;
  quebrar(ctx, d.frase, W - 128, 2).forEach((l, i) => ctx.fillText(l, 64, 940 + i * 33));

  // rodapé
  ctx.fillStyle = AMARELO;
  ctx.fillRect(64, 996, W - 128, 3);
  const [r1, r2] = d.rodape || [];
  ctx.font = `700 21px ${FM}`;
  ctx.fillStyle = '#ffcc29';
  ctx.fillText(r1 || '', 64, 1030);
  ctx.font = `600 21px ${FS}`;
  ctx.fillStyle = '#e3f1e7';
  ctx.fillText(quebrar(ctx, r2 || '', W - 128, 1)[0] || '', 64, 1058);
  return canvas;
}
