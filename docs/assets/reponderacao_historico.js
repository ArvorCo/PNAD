/* Server-rendered series: switch only the view, never the simulation or its URL. */
(() => {
  'use strict';
  const root = document.getElementById('institutos-2t');
  if (!root) return;
  const global = root.querySelector('#history-valids-all');
  const status = root.querySelector('#history-mode-status');
  const toggles = [...root.querySelectorAll('[data-history-toggle]')];
  function render(toggle) {
    const card = toggle.closest('.history-panel');
    card.querySelectorAll('[data-history-view]').forEach(view => {
      view.hidden = (view.dataset.historyView === 'validos') !== toggle.checked;
    });
  }
  function sync() {
    const count = toggles.filter(t => t.checked).length;
    global.checked = count === toggles.length;
    global.indeterminate = count > 0 && count < toggles.length;
    status.textContent = count === 0
      ? 'Exibindo os totais publicados. Cada instituto também tem seu próprio controle.'
      : `${count} de ${toggles.length} institutos em votos válidos projetados. Confira a hipótese de presença em cada onda.`;
  }
  toggles.forEach(toggle => {
    toggle.disabled = false;
    toggle.addEventListener('change', () => { render(toggle); sync(); });
    render(toggle);
  });
  global.disabled = false;
  global.addEventListener('change', () => {
    toggles.forEach(toggle => { toggle.checked = global.checked; render(toggle); });
    sync();
  });
  sync();
})();
