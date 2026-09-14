'use strict';
const output = document.querySelector('.flow-readout');
for (const flow of document.querySelectorAll('.flow')) {
  const show = () => { if (output) output.textContent = flow.getAttribute('aria-label'); };
  flow.addEventListener('pointerenter', show);
  flow.addEventListener('focus', show);
  flow.addEventListener('click', show);
}
