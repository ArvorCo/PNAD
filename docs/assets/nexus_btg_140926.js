/* Progressive enhancement: evidence remains complete without JavaScript. */
const readout = document.querySelector('.flow-readout');
for (const flow of document.querySelectorAll('.flow')) {
  const show = () => { readout.textContent = flow.getAttribute('aria-label'); };
  flow.addEventListener('pointerenter', show);
  flow.addEventListener('focus', show);
  flow.addEventListener('click', show);
}
