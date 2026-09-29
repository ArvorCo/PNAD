(() => {
  const root = document.querySelector('#projecao-validos');
  if (!root) return;
  const data = JSON.parse(root.querySelector('#vf-data').textContent);
  const fmt = n => n.toLocaleString('pt-BR', {minimumFractionDigits: 1, maximumFractionDigits: 1});
  let mode = 'modelo';
  const select = root.querySelector('#vf-scenario');
  function render() {
    const key = select.value;
    root.querySelectorAll('[data-vf-mode]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.vfMode === mode)));
    select.disabled = mode !== 'modelo';
    for (const [ballot, block] of Object.entries(data.ballots)) {
      const scenario = block.scenarios[key];
      const values = scenario.aggregate[mode];
      const card = root.querySelector(`article[data-ballot="${ballot}"]`);
      card.querySelector('.vf-mode-label').textContent = data.modes[mode];
      for (const [k, v] of Object.entries(values)) {
        const row = card.querySelector(`[data-candidate="${k}"]`);
        row.querySelector('.vf-bar').style.width = `${v}%`;
        row.querySelector('b').textContent = `${fmt(v)}%`;
      }
      card.querySelector('.vf-bars').setAttribute('aria-label', Object.entries(values).map(([k,v]) => `${data.labels[k]} ${fmt(v)}%`).join('; '));
      const gap = values.lula - values.flavio;
      card.querySelector('.vf-gap').textContent = Math.abs(gap) < .05 ? 'Empate na projeção arredondada' : `${gap > 0 ? 'Lula' : 'Flávio'} +${fmt(Math.abs(gap))} pontos`;
      for (const p of scenario.polls) {
        const tr = root.querySelector(`tr[data-poll="${p.id}"][data-ballot="${ballot}"]`);
        for (const m of Object.keys(data.modes)) tr.querySelector(`[data-mode="${m}"]`).textContent = `${fmt(p[m].lula)} × ${fmt(p[m].flavio)}`;
      }
    }
    root.querySelector('#vf-state').textContent = mode === 'modelo'
      ? `${data.modes[mode]}: ${data.scenario_labels[key]}. Hipótese condicional; preferências declaradas mantidas até a eleição.`
      : `${data.modes[mode]}. Mesma proporção após distribuir indecisos proporcionalmente; sem diferença de comparecimento entre candidatos.`;
  }
  root.querySelectorAll('[data-vf-mode]').forEach(b => b.addEventListener('click', () => { mode = b.dataset.vfMode; render(); }));
  select.addEventListener('change', render);
  render();
  root.querySelector('.vf-controls').hidden = false;
})();
