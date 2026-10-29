/* Movimento observado, 2º turno. Histograma de votos, nunca ocupação do prédio. */
(function (root) {
  'use strict';
  const BASE = 'assets/politize_se/movimento/', V = '20261028-movimento1';
  const cache = new Map();
  const nomes = { pequena: 'seção com menos de 30 aptos', exterior: 'exterior sem fuso comparável', sem_log: 'log ausente', relogio: 'relógio inconsistente', contagem: 'contagem inconsistente', fuso: 'fuso indisponível', sem_horario: 'horário ausente', fora_dia: 'horário fora do dia' };
  const fmt = (n) => n.toLocaleString('pt-BR', { maximumFractionDigits: 1 });
  const faixa = (h) => String(h).padStart(2, '0') + 'h–' + String(h + 1).padStart(2, '0') + 'h';
  function el(tag, attrs = {}, ...children) {
    const n = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
    for (const c of children.flat(Infinity)) if (c !== null && c !== undefined) n.append(c instanceof Node ? c : String(c));
    return n;
  }
  async function dados(uf) {
    if (!cache.has(uf)) {
      const p = fetch(BASE + uf + '.json.gz?v=' + V).then(async (r) => {
        if (!r.ok) throw new Error('Movimento indisponível');
        const b = await r.blob(), magic = new Uint8Array(await b.slice(0, 2).arrayBuffer());
        const d = magic[0] === 31 && magic[1] === 139 ? await new Response(b.stream().pipeThrough(new DecompressionStream('gzip'))).json() : JSON.parse(await b.text());
        if (d.formato !== 1 || d.uf !== uf) throw new Error('Versão de movimento incompatível');
        return d;
      });
      cache.set(uf, p); p.catch(() => cache.delete(uf));
    }
    return cache.get(uf);
  }
  function resumir(rows) {
    const horas = Array(24).fill(0), motivos = {};
    let cobertas = 0;
    for (const [, hs, motivo] of rows) {
      if (hs === null) { motivos[motivo] = (motivos[motivo] || 0) + 1; continue; }
      if (!Array.isArray(hs) || hs.length !== 24 || hs.some((v) => !Number.isInteger(v) || v < 0)) throw new Error('Histograma inválido');
      cobertas++; hs.forEach((v, i) => { horas[i] += v; });
    }
    return { horas, cobertas, secoes: rows.length, motivos, votos: horas.reduce((a, v) => a + v, 0) };
  }
  function selecionar(d, ref) {
    if (ref.local) {
      const ss = ref.secoes ? new Set(ref.secoes.map(Number)) : ref.secao !== undefined ? new Set([Number(ref.secao)]) : null;
      return (d.locais[ref.local] || []).filter((s) => !ss || ss.has(s[0]));
    }
    return Object.entries(d.locais).filter(([id]) => {
      const [, mun, z] = id.split('-');
      return (!ref.mun || Number(ref.mun) === Number(mun)) && (!ref.zona || Number(ref.zona) === Number(z));
    }).flatMap(([, rows]) => rows);
  }
  function picos(horas) {
    const max = Math.max(...horas);
    return max > 0 ? horas.flatMap((n, i) => n === max ? [i] : []) : [];
  }
  function pico(horas) { const ps = picos(horas); return !ps.length ? null : ps.length > 1 ? 'empate' : String(ps[0]); }
  const resumo = (d, ref) => resumir(selecionar(d, ref));
  function render(r, titulo) {
    const ps = picos(r.horas), max = Math.max(...r.horas);
    const box = el('div', { class: 'mov-conteudo' },
      el('p', { class: 'mov-kicker' }, '25 OUT 2026 · 2º TURNO · HORÁRIO DE BRASÍLIA'),
      el('h3', {}, 'Quando os votos foram computados'),
      el('p', { class: 'mov-escopo' }, titulo),
      el('p', { class: 'mov-cobertura' }, fmt(r.cobertas) + ' de ' + fmt(r.secoes) + (r.secoes === 1 ? ' seção com horário utilizável' : ' seções com horário utilizável') + ' · ' + fmt(r.votos) + ' votos nos logs exibidos'));
    if (Object.keys(r.motivos).length) box.append(el('p', { class: 'mov-nota' }, 'Fora do gráfico: ' + Object.entries(r.motivos).map(([k, n]) => fmt(n) + ' (' + (nomes[k] || k) + ')').join('; ') + '.'));
    if (!ps.length) { box.append(el('p', { class: 'mov-vazio' }, r.cobertas ? 'Nenhum voto computado nos logs exibidos.' : 'Não há histograma utilizável para este recorte. Ausência de dado não significa ausência de votação.')); return box; }
    box.append(el('p', { class: 'mov-pico' }, el('span', {}, ps.length > 1 ? 'Faixas empatadas no pico' : 'Faixa de maior votação'), el('strong', {}, ps.map(faixa).join(' / ')), el('small', {}, fmt(max) + ' votos · ' + fmt(100 * max / r.votos) + (ps.length > 1 ? '% do dia em cada faixa' : '% do dia'))));
    const info = el('p', { class: 'mov-info', role: 'status', 'aria-live': 'polite' });
    const inicio = Math.min(8, r.horas.findIndex((n) => n > 0));
    const fim = Math.max(19, r.horas.findLastIndex ? r.horas.findLastIndex((n) => n > 0) : 23);
    const bars = el('div', { class: 'mov-barras', role: 'group', 'aria-label': 'Votos por hora; toque ou use Tab para consultar' });
    const escolher = (hr) => {
      info.textContent = faixa(hr) + ': ' + fmt(r.horas[hr]) + ' votos, ' + fmt(100 * r.horas[hr] / r.votos) + '% dos votos nos logs exibidos.';
      bars.querySelectorAll('button').forEach((b) => b.setAttribute('aria-pressed', String(Number(b.dataset.hora) === hr)));
    };
    for (let hr = inicio; hr <= fim; hr++) {
      const btn = el('button', { type: 'button', 'data-hora': hr, class: ps.includes(hr) ? 'pico' : '', 'aria-label': faixa(hr) + ': ' + fmt(r.horas[hr]) + ' votos', 'aria-pressed': 'false' },
        el('span', { class: 'mov-coluna', 'aria-hidden': 'true' }, el('i', { style: 'height:' + (100 * r.horas[hr] / max) + '%' })), el('span', { class: 'mov-hora' }, String(hr).padStart(2, '0')));
      ['click', 'focus', 'mouseenter'].forEach((ev) => btn.addEventListener(ev, () => escolher(hr)));
      bars.append(btn);
    }
    escolher(ps[0]);
    const tabela = el('details', { class: 'mov-tabela' }, el('summary', {}, 'Ver as 24 horas em tabela'));
    tabela.append(el('table', {}, el('thead', {}, el('tr', {}, ['Hora', 'Votos computados', '% do dia'].map((t) => el('th', { scope: 'col' }, t)))), el('tbody', {}, r.horas.map((v, hr) => el('tr', {}, el('th', { scope: 'row' }, faixa(hr)), el('td', {}, fmt(v)), el('td', {}, fmt(100 * v / r.votos) + '%'))))));
    box.append(bars, info, tabela, el('p', { class: 'mov-nota' }, 'Barras relativas ao pico deste recorte; percentuais sobre os votos dos logs cobertos. Cada faixa inclui a hora inteira (17h = 17:00 a 17:59). Mede cômputos, não fila ou ocupação. Não mostra candidato nem prevê movimento futuro.'));
    box.append(el('a', {class:'mov-fonte',href:BASE+'indice.json',target:'_blank',rel:'noopener'},'Fonte e cobertura dos logs'));
    return box;
  }
  function painel(ref, titulo = 'Seções selecionadas') {
    const box = el('section', { class: 'movimento', 'aria-busy': 'true', 'aria-label': 'Movimento da votação' });
    const carregar = async () => {
      box.setAttribute('aria-busy', 'true'); box.replaceChildren(el('p', { role: 'status' }, 'Carregando votos por hora…'));
      try {
        const d = await dados(ref.uf);
        const grafico = el('div', {}, render(resumo(d, ref), titulo));
        if (ref.escolherSecao && ref.local) {
          const select = el('select', { 'aria-label': 'Recorte do gráfico de movimento', class: 'mov-seletor' }, el('option', {value:''}, titulo),
            selecionar(d, ref).map(([n]) => el('option', {value:n}, 'Seção ' + n)));
          select.addEventListener('change', () => {
            const r = select.value ? {uf:ref.uf, local:ref.local, secao:Number(select.value)} : ref;
            grafico.replaceChildren(render(resumo(d, r), select.value ? 'Seção ' + select.value + ' deste local' : titulo));
          });
          box.replaceChildren(el('label', {class:'mov-escolha'}, 'Ver movimento de', select), grafico);
        } else box.replaceChildren(grafico);
      }
      catch {
        const b = el('button', { type: 'button', class: 'mov-tentar' }, 'Tentar de novo'); b.addEventListener('click', carregar);
        box.replaceChildren(el('p', {}, 'Os horários não carregaram. Os demais dados continuam disponíveis.'), b);
      } finally { box.setAttribute('aria-busy', 'false'); }
    };
    carregar(); return box;
  }
  root.PolitizeMovimento = { dados, resumir, selecionar, resumo, picos, pico, painel, faixa, render };
})(window);
