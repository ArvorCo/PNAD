(() => {
  const root = document.querySelector('#projecao-validos');
  if (!root) return;
  const data = JSON.parse(root.querySelector('#vf-data').textContent);
  const fmt = n => n.toLocaleString('pt-BR', {minimumFractionDigits: 1, maximumFractionDigits: 1});
  const signed = n => `${n > 0 ? '+' : n < 0 ? '−' : ''}${fmt(Math.abs(n))}`;
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
        row.querySelector('.vf-value').textContent = `${fmt(v)}%`;
        if (block.urna) row.querySelector('.vf-error').textContent = signed(v - block.urna[k]);
      }
      card.querySelector('.vf-bars').setAttribute('aria-label', Object.entries(values).map(([k,v]) => `${data.labels[k]} ${fmt(v)}%${block.urna ? `; urna ${fmt(block.urna[k])}%; erro ${signed(v - block.urna[k])} pontos` : ''}`).join('; '));
      const gap = values.lula - values.flavio;
      card.querySelector('.vf-gap').textContent = Math.abs(gap) < .05 ? 'Empate na projeção arredondada' : `${gap > 0 ? 'Lula' : 'Flávio'} +${fmt(Math.abs(gap))} pontos`;
      if (block.urna) card.querySelector('.vf-gap-error b').textContent = `${signed(scenario.erros[mode].diferenca_lula_flavio_pp)} pp`;
      for (const p of scenario.polls) {
        const tr = root.querySelector(`tr[data-poll="${p.id}"][data-ballot="${ballot}"]`);
        for (const m of Object.keys(data.modes)) tr.querySelector(`[data-mode="${m}"]`).textContent = `${fmt(p[m].lula)} × ${fmt(p[m].flavio)}`;
        if (block.urna) tr.querySelector('[data-poll-error]').textContent = signed((p[mode].lula - p[mode].flavio) - (block.urna.lula - block.urna.flavio));
      }
    }
    root.querySelector('#vf-state').textContent = mode === 'modelo'
      ? `${data.modes[mode]}: ${data.scenario_labels[key]}. Primeiro turno fechado em 04/10; segundo turno atualizado em ${data.reference}.`
      : `${data.modes[mode]}. Primeiro turno comparado com a urna; segundo turno em andamento. Indecisos distribuídos proporcionalmente preservam os válidos.`;
  }
  root.querySelectorAll('[data-vf-mode]').forEach(b => b.addEventListener('click', () => { mode = b.dataset.vfMode; render(); }));
  select.addEventListener('change', render);
  render();
  root.querySelector('.vf-controls').hidden = false;
})();
