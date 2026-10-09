(() => {
  const root = document.querySelector('#pesquisas');
  if (!root) return;
  const turn = root.querySelector('#research-turn');
  const waves = root.querySelector('#research-waves');
  const cards = [...root.querySelectorAll('article.poll')];
  function render() {
    const eligible = cards.filter(c => turn.value === 'all' || c.dataset.researchTurns.split(',').includes(turn.value));
    const latest = new Map();
    for (const c of eligible) {
      for (const t of c.dataset.researchTurns.split(',').filter(t => t && (turn.value === 'all' || t === turn.value))) {
        const key = `${c.dataset.researchHouse}:${t}`;
        if (!latest.has(key) || c.dataset.researchRelease > latest.get(key).dataset.researchRelease) latest.set(key, c);
      }
    }
    const shown = new Set(waves.value === 'all' ? eligible : latest.values());
    for (const c of cards) c.hidden = !shown.has(c);
    root.querySelector('#research-state').textContent = `${shown.size} de ${cards.length} fichas. ${waves.value === 'latest' ? 'Última onda com cruzamento elegível de renda por casa e turno; o arquivo completo está em “Todas as ondas”.' : 'Todas as ondas do recorte selecionado, da mais recente à mais antiga.'}`;
  }
  turn.addEventListener('change', render);
  waves.addEventListener('change', render);
  function revealLinkedWave() {
    const target = document.getElementById(location.hash.slice(1));
    if (!target || !target.matches('#pesquisas article.poll') || !target.hidden) return;
    turn.value = [...turn.options].some(o => o.value === 'all') ? 'all' : target.dataset.researchTurns.split(',')[0];
    waves.value = 'all';
    render();
    target.scrollIntoView();
  }
  window.addEventListener('hashchange', revealLinkedWave);
  root.querySelector('.research-controls').hidden = false;
  render();
  revealLinkedWave();
})();
