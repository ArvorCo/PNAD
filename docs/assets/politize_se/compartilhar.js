/* Card da seção, gerado apenas no aparelho. */
export function criarCompartilhar({h, num, pc, nf1, URL_PUBLICA}) {
function linkDe(uf, zona, secao) {
  return `${URL_PUBLICA}#uf=${uf}&z=${zona}&s=${secao}`;
}
function textoCompartilhar({ uf, zona, s, mun }) {
  const lugar = `seção ${s.secao}, zona ${zona}, ${mun.nome || ''} (${uf === 'ZZ' ? 'Exterior' : uf})`;
  if (s.pequena || !s.bu2 || num(s.fatia_f2) === null) return `Veja o que aconteceu na ${lugar}, no 1º e no 2º turno: ${linkDe(uf, zona, s.secao)}`;
  const ml = s.ml_anomalo ? ' Pela estatística dos dois turnos, a seção está no grupo atípico do país: pede explicação, não prova irregularidade.' : '';
  return `Na ${lugar}, o 2º turno deu Flávio ${pc(s.fatia_f2)} e Lula ${pc(100 - s.fatia_f2)} dos válidos; no 1º turno, entre os dois, Flávio tinha ${pc(s.fatia_f1)}. Comparecimento: ${pc(s.comp_pct1)} no 1º turno, ${pc(s.comp_pct2)} no 2º.${ml} Leitura agregada por seção, TSE. ${linkDe(uf, zona, s.secao)}`;
}
async function desenharCard(cv, { uf, zona, s, mun }) {
  const W = 1080;
  cv.width = W;
  cv.height = W;
  const c = cv.getContext('2d');
  try {
    if (document.fonts && document.fonts.load) await Promise.all([document.fonts.load('900 90px Fraunces'), document.fonts.load('600 34px "IBM Plex Sans Condensed"'), document.fonts.load('500 26px "IBM Plex Mono"')]);
  } catch {
    // sem a fonte da casa, o card sai com a de reserva
  }
  const FD = 'Fraunces, Georgia, serif';
  const FS = '"IBM Plex Sans Condensed", Arial, sans-serif';
  const FM = '"IBM Plex Mono", ui-monospace, monospace';
  c.fillStyle = '#f6f4ee';
  c.fillRect(0, 0, W, W);
  c.fillStyle = '#1d2a33';
  c.fillRect(0, 0, W, 250);
  c.fillStyle = '#f0c36a';
  c.font = `500 26px ${FM}`;
  c.fillText('POLITIZE-SE · ELEIÇÕES 2026', 70, 80);
  c.fillStyle = '#ffffff';
  c.font = `900 76px ${FD}`;
  c.fillText(`Seção ${s.secao} · Zona ${zona}`, 70, 165);
  c.font = `600 34px ${FS}`;
  c.fillStyle = '#dde3e8';
  c.fillText(`${mun.nome || ''} (${uf === 'ZZ' ? 'Exterior' : uf})`.slice(0, 48), 70, 215);
  const barra = (y, rot, f, l) => {
    c.fillStyle = '#16191c';
    c.font = `500 26px ${FM}`;
    c.fillText(rot, 70, y);
    if (num(f) === null) {
      c.font = `600 34px ${FS}`;
      c.fillText('sem dado', 70, y + 56);
      return;
    }
    const x0 = 70;
    const w = W - 140;
    c.fillStyle = '#1f5f9e';
    c.fillRect(x0, y + 18, (w * f) / 100, 64);
    c.fillStyle = '#b23a2a';
    c.fillRect(x0 + (w * f) / 100, y + 18, w - (w * f) / 100, 64);
    c.fillStyle = '#ffffff';
    c.font = `700 36px ${FS}`;
    if (f >= 18) c.fillText(`Flávio ${nf1.format(f)}%`, x0 + 18, y + 63);
    const tl = `Lula ${nf1.format(l)}%`;
    if (l >= 18) c.fillText(tl, x0 + w - 18 - c.measureText(tl).width, y + 63);
  };
  const ok2 = !s.pequena && s.bu2 && num(s.fatia_f2) !== null;
  barra(330, '2º TURNO · VOTOS VÁLIDOS', ok2 ? s.fatia_f2 : null, ok2 ? 100 - s.fatia_f2 : null);
  const ok1 = !s.pequena && num(s.fatia_f1) !== null;
  barra(500, '1º TURNO · ENTRE OS DOIS', ok1 ? s.fatia_f1 : null, ok1 ? 100 - s.fatia_f1 : null);
  c.fillStyle = '#16191c';
  c.font = `500 26px ${FM}`;
  c.fillText('COMPARECIMENTO', 70, 680);
  c.font = `900 64px ${FD}`;
  c.fillText(s.pequena ? 'seção pequena' : `${pc(s.comp_pct1)} → ${pc(s.comp_pct2)}`, 70, 755);
  c.font = `600 32px ${FS}`;
  c.fillStyle = '#4f5862';
  const sin = !s.bu2 ? '2º turno ainda não lido' : num(s.escore) > 0 ? `${s.escore} ${s.escore === 1 ? 'sinal pede' : 'sinais pedem'} explicação, sem provar irregularidade` : 'Nenhum sinal da régua da casa';
  c.fillText(sin, 70, 830);
  if (s.bu2 && s.ml_anomalo) {
    // selo do grupo atípico da mistura estatística dos dois turnos
    c.font = `600 26px ${FS}`;
    c.fillStyle = '#6b4a92';
    c.fillText('Grupo atípico na estatística dos dois turnos: pede explicação, não prova nada', 70, 872);
  }
  c.fillStyle = '#1d2a33';
  c.fillRect(0, 920, W, 160);
  c.fillStyle = '#ffffff';
  c.font = `600 32px ${FS}`;
  c.fillText('brasil.arvor.co/politizese.html', 70, 985);
  c.fillStyle = '#c4ccd3';
  c.font = `500 22px ${FM}`;
  c.fillText('LEITURA AGREGADA POR SEÇÃO, TSE · O VOTO É SECRETO', 70, 1035);
}
function blocoCompartilhar(dados) {
  const cv = h('canvas', { width: '1080', height: '1080', role: 'img', 'aria-label': 'Card para compartilhar com o resultado da seção nos dois turnos' });
  const status = h('p', { class: 'ajuda', role: 'status' });
  const copiar = async (texto, ok) => {
    try {
      await navigator.clipboard.writeText(texto);
      status.textContent = ok;
    } catch {
      status.textContent = texto;
    }
  };
  const art = h('article', { class: 'ficha' },
    h('p', { class: 'kicker' }, 'Compartilhar'),
    h('h2', {}, 'Leve a sua seção'),
    h('div', { class: 'compartilhar' }, cv, h('div', {},
      h('p', {}, 'O card e o link são montados no seu aparelho, só quando você pede. O link leva direto a esta seção.'),
      h('div', { class: 'botoes' },
        h('button', { type: 'button', class: 'btn btn-prim', onclick: () => { const a = h('a', { href: cv.toDataURL('image/png'), download: `politizese-${dados.uf}-${dados.zona}-${dados.s.secao}.png` }); document.body.append(a); a.click(); a.remove(); } }, 'Baixar imagem'),
        h('button', { type: 'button', class: 'btn btn-sec', onclick: () => copiar(textoCompartilhar(dados), 'Texto copiado.') }, 'Copiar texto'),
        h('button', { type: 'button', class: 'btn btn-sec', onclick: () => copiar(linkDe(dados.uf, dados.zona, dados.s.secao), 'Link copiado.') }, 'Copiar link')),
      status)));
  desenharCard(cv, dados);
  return art;
}


return { blocoCompartilhar };
}
