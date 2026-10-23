(() => {
  'use strict';
  const f = document.getElementById('round-f');
  const l = document.getElementById('round-l');
  if (!f || !l) return;
  const fmt = (n, digits) => n.toLocaleString('pt-BR', {minimumFractionDigits: digits, maximumFractionDigits: digits});
  function update() {
    const fv = Number(f.value), lv = Number(l.value), share = 100 * fv / (fv + lv);
    document.getElementById('round-f-label').textContent = fmt(fv, 2) + '%';
    document.getElementById('round-l-label').textContent = fmt(lv, 2) + '%';
    const rf = Math.round(share), rl = Math.round(100 - share);
    const target = document.getElementById('round-result');
    target.querySelector('b').textContent = `${fmt(share, 3)}% × ${fmt(100 - share, 3)}%`;
    target.querySelector('p').textContent = `Total exibido: ${Math.round(fv)} × ${Math.round(lv)}. Válidos arredondados: ${rf} × ${rl}. ${rf === 50 && rl === 50 ? 'Compatível com o 50/50 divulgado.' : 'Os mesmos inteiros no total também permitem outro placar arredondado nos válidos.'}`;
  }
  f.addEventListener('input', update);
  l.addEventListener('input', update);
  update();
})();
