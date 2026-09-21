'use strict';
const output = document.querySelector('.flow-readout');
for (const flow of document.querySelectorAll('.flow')) {
  const show = () => { if (output) output.textContent = flow.getAttribute('aria-label'); };
  for (const event of ['pointerenter', 'focus', 'click']) flow.addEventListener(event, show);
}
const data = JSON.parse(document.getElementById('southeast-data').textContent);
const lula = document.getElementById('es-lula');
const flavio = document.getElementById('es-flavio');
function update(changed) {
  if (+lula.value + +flavio.value > 100) {
    const other = changed === lula ? flavio : lula;
    other.value = 100 - +changed.value;
  }
  document.getElementById('es-lula-out').textContent = lula.value + '%';
  document.getElementById('es-flavio-out').textContent = flavio.value + '%';
  const l = data.known.lula + data.weight * +lula.value;
  const f = data.known.flavio + data.weight * +flavio.value;
  const fmt = value => value.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
  document.getElementById('es-result').textContent = `Sudeste hipotético: Lula ${fmt(l)}% × Flávio ${fmt(f)}%. ES: ${100 - +lula.value - +flavio.value}% de não escolha.`;
}
lula.addEventListener('input', () => update(lula));
flavio.addEventListener('input', () => update(flavio));
update(lula);
