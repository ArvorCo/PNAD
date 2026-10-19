(() => {
  'use strict';
  const data = JSON.parse(document.getElementById('projecao-data').textContent);
  const fmt = (value, digits = 2) => Number(value).toLocaleString('pt-BR', {minimumFractionDigits: digits, maximumFractionDigits: digits});
  const peso = document.getElementById('peso'), vies = document.getElementById('vies');
  function simulate() {
    const weight = Number(peso.value) / 100, bias = Number(vies.value);
    const f = (1 - weight) * data.fusao.historico_pct + weight * data.fusao.pesquisas_pct + bias;
    document.getElementById('peso-out').textContent = `${fmt(weight * 100, 1)}%`;
    document.getElementById('vies-out').textContent = `${fmt(bias, 1)} pp`;
    document.getElementById('sim-score').textContent = `${fmt(f)} × ${fmt(100 - f)}`;
  }
  peso.addEventListener('input', simulate); vies.addEventListener('input', simulate);
  document.getElementById('reset').addEventListener('click', () => {
    peso.value = data.fusao.peso_pesquisas * 100; vies.value = 0; simulate();
  });
  const columns = data.municipios.colunas;
  const rows = data.municipios.linhas.map(row => Object.fromEntries(columns.map((key, i) => [key, row[i]])));
  const normalize = value => String(value).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const uf = document.getElementById('uf'), search = document.getElementById('municipio');
  function municipalities() {
    const query = normalize(search.value.trim());
    const filtered = rows.filter(row => (!uf.value || row.uf === uf.value) && normalize(row.municipio).includes(query));
    filtered.sort((a, b) => b.aptos_1 - a.aptos_1);
    document.getElementById('municipios-count').textContent = `${fmt(filtered.length, 0)} municípios encontrados. Até 50 exibidos, por eleitorado; arquivo completo disponível abaixo.`;
    const wrapper = document.createElement('div'); wrapper.className = 'scroll'; wrapper.tabIndex = 0;
    const table = document.createElement('table'), head = table.createTHead().insertRow();
    ['Município / UF', 'Eleitores', 'Urna local / F', 'Combinado / F', 'Combinado / L'].forEach(label => {
      const th = document.createElement('th'); th.scope = 'col'; th.textContent = label; head.appendChild(th);
    });
    const body = table.createTBody();
    filtered.slice(0, 50).forEach(row => {
      const f = 100 * row.combinado_direita / (row.combinado_direita + row.combinado_esquerda);
      const prior = 100 * row.historico_direita / (row.historico_direita + row.historico_esquerda);
      const tr = body.insertRow();
      [`${row.municipio} / ${row.uf}`, fmt(row.aptos_1, 0), fmt(prior), fmt(f), fmt(100 - f)].forEach(value => {tr.insertCell().textContent = value;});
    });
    wrapper.appendChild(table); document.getElementById('municipios-table').replaceChildren(wrapper);
  }
  uf.addEventListener('change', municipalities); search.addEventListener('input', municipalities);
  municipalities();
})();
