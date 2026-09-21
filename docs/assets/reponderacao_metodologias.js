(() => {
  const section = document.querySelector('#comparar-metodos');
  if (!section) return;
  const controls = section.querySelector('.method-controls');
  const tbody = section.querySelector('.method-table tbody');
  const rows = Array.from(tbody.querySelectorAll('[data-method]'));
  const search = section.querySelector('#method-search');
  const mode = section.querySelector('#method-mode');
  const order = section.querySelector('#method-sort');
  const normalize = text => text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const apply = () => {
    const query = normalize(search.value.trim());
    let count = 0;
    rows.sort((a, b) => {
      if (order.value === 'score') return Number(b.dataset.score) - Number(a.dataset.score);
      if (order.value === 'lula' || order.value === 'flavio') {
        if (!a.dataset.delta) return 1;
        if (!b.dataset.delta) return -1;
        return (Number(b.dataset.delta) - Number(a.dataset.delta)) * (order.value === 'lula' ? 1 : -1);
      }
      return a.querySelector('b').textContent.localeCompare(b.querySelector('b').textContent, 'pt-BR');
    });
    rows.forEach(row => {
      const visible = (!mode.value || row.dataset.mode === mode.value) && normalize(row.dataset.search).includes(query);
      row.hidden = !visible;
      const file = document.getElementById(`ficha-${row.dataset.method}`);
      if (file) file.hidden = !visible;
      if (visible) count++;
      tbody.appendChild(row);
    });
    section.querySelector('#method-count').textContent = `${count} de ${rows.length} institutos`;
    section.querySelector('.method-empty').hidden = count > 0;
  };
  const revealHash = () => {
    const file = document.getElementById(location.hash.slice(1));
    if (!file || !file.classList.contains('method-file')) return;
    if (file.hidden) { search.value = ''; mode.value = ''; apply(); }
    file.open = true;
  };
  controls.hidden = false;
  search.addEventListener('input', apply);
  mode.addEventListener('change', apply);
  order.addEventListener('change', apply);
  window.addEventListener('hashchange', revealHash);
  apply();
  revealHash();
})();
