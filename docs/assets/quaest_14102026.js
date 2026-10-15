/* Exploração local das cinco perguntas; não altera dados nem centrais. */
(() => {
  'use strict';
  const source = document.getElementById('q-explorer-data');
  if (!source) return;
  const data = JSON.parse(source.textContent);
  const question = document.getElementById('q-question');
  const dimension = document.getElementById('q-dimension');
  const output = document.getElementById('q-explorer-result');
  const status = document.getElementById('q-status');
  const share = document.getElementById('q-share');
  const fmt = n => new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 }).format(n);
  const node = (tag, text, cls) => {
    const el = document.createElement(tag);
    if (text !== undefined) el.textContent = text;
    if (cls) el.className = cls;
    return el;
  };
  function draw() {
    const q = data.questions[question.value];
    const dim = dimension.value;
    const rows = [q.total, ...data.dimensions[dim].map(name => q.estratos.find(r => r.dimensao === dim && r.recorte === name))];
    const figure = node('figure', undefined, 'chart q-chart q-explorer-chart');
    figure.dataset.mode = q.independente ? 'independent' : 'stacked';
    figure.append(node('figcaption', `${q.rotulo} · ${dim.toLocaleLowerCase('pt-BR')}`));
    figure.append(node('p', q.independente ? 'Barras independentes · escala de 0 a 100% por candidato' : 'Distribuição de respostas dentro de cada grupo · valores publicados', 'q-scale'));
    rows.forEach((r, index) => {
      const label = index === 0 ? 'Total' : r.recorte;
      const row = node('div', undefined, 'q-explorer-row');
      row.dataset.segment = label;
      row.append(node('b', label));
      if (q.independente) {
        q.opcoes.forEach(option => {
          const value = r.valores_pct[option];
          const line = node('div', undefined, 'q-pair-line');
          const track = node('div', undefined, 'q-track');
          const bar = node('i');
          bar.style.width = `${value}%`;
          bar.style.background = data.colors[option];
          track.append(bar);
          line.append(node('span', option), track, node('strong', `${fmt(value)}%`));
          row.append(line);
        });
      } else {
        const total = q.opcoes.reduce((sum, o) => sum + r.valores_pct[o], 0) || 100;
        const strip = node('div', undefined, 'q-response-strip');
        strip.setAttribute('aria-hidden', 'true');
        q.opcoes.forEach(option => {
          const bar = node('i');
          bar.style.width = `${100 * r.valores_pct[option] / total}%`;
          bar.style.background = data.colors[option];
          strip.append(bar);
        });
        row.append(strip);
        const values = node('div', undefined, 'q-response-values');
        q.opcoes.forEach(option => {
          const label = node('span');
          const dot = node('i');
          dot.style.background = data.colors[option];
          label.append(dot, document.createTextNode(`${option}: `), node('strong', `${fmt(r.valores_pct[option])}%`));
          values.append(label);
        });
        row.append(values);
      }
      row.append(node('small', `Margem publicada: ${fmt(r.margem_publicada_pp)} pp · base não publicada`));
      figure.append(row);
    });
    const foot = node('p', undefined, 'note');
    const link = node('a', 'Fonte: painel G1 / Quaest');
    link.href = q.fonte.url;
    foot.append(link, document.createTextNode(` · coluna 14/10/2026 · ${q.codigo}.`));
    figure.append(foot);
    output.replaceChildren(figure);
    status.textContent = `${q.rotulo}: total e ${rows.length - 1} recortes por ${dim.toLocaleLowerCase('pt-BR')}.`;
    document.getElementById('q-explorer-note').textContent = q.independente
      ? 'Rejeição admite rejeitar ambos. As barras são independentes e não devem somar 100%. Não conhecemos a rejeição simultânea. Margens do painel não são margens da diferença entre candidatos.'
      : 'As barras acomodam o arredondamento da soma; os números preservam os percentuais publicados, inclusive zeros. Margens do painel não são margens de diferenças. Grupos se sobrepõem; bases não foram publicadas.';
    const url = new URL(location.href);
    url.searchParams.set('pergunta', question.value);
    url.searchParams.set('recorte', dim);
    url.hash = 'painel';
    share.href = url.href;
  }
  function restore() {
    const params = new URL(location.href).searchParams;
    question.value = Object.hasOwn(data.questions, params.get('pergunta')) ? params.get('pergunta') : 'estimulada';
    dimension.value = Object.hasOwn(data.dimensions, params.get('recorte')) ? params.get('recorte') : 'Renda';
    draw();
  }
  function update() {
    draw();
    history.replaceState(null, '', share.href);
  }
  restore();
  question.addEventListener('change', update);
  dimension.addEventListener('change', update);
  window.addEventListener('popstate', restore);
  document.getElementById('q-controls').hidden = false;
  share.hidden = false;
})();
