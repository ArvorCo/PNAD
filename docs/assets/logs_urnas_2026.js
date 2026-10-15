/* Apenas exploração visual: nenhuma regra estatística é recalculada no navegador. */
(function () {
  'use strict';
  var painel = document.querySelector('.filtros-criterios');
  if (!painel) return;
  var grupo = 'todos', busca = painel.querySelector('input');
  var regras = Array.from(document.querySelectorAll('.catalogo-regras .regra'));
  function norm(t) { return t.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase(); }
  function filtrar() {
    var termo = norm(busca.value).trim(), n = 0;
    regras.forEach(function (r) {
      r.hidden = !((grupo === 'todos' || r.dataset.grupo === grupo) && norm(r.textContent).includes(termo));
      if (!r.hidden) n++;
    });
    document.querySelectorAll('.grupo-regras').forEach(function (g) { g.hidden = !g.querySelector('.regra:not([hidden])'); });
    document.querySelector('.catalogo-regras').classList.toggle('filtrado', grupo !== 'todos' || Boolean(termo));
    painel.querySelectorAll('button').forEach(function (b) { b.setAttribute('aria-pressed', String(grupo === b.dataset.grupo)); });
    document.querySelector('#resultado-criterios').textContent = n + (n === 1 ? ' diagnóstico' : ' diagnósticos');
    document.querySelector('.sem-resultados').hidden = n !== 0;
  }
  painel.querySelectorAll('button').forEach(function (b) { b.addEventListener('click', function () { grupo = b.dataset.grupo; filtrar(); }); });
  busca.addEventListener('input', filtrar);
  painel.hidden = false;
  function revelarAncora() {
    var alvo = document.getElementById(location.hash.slice(1));
    if (!alvo || !alvo.classList.contains('regra')) return;
    grupo = 'todos'; busca.value = ''; filtrar();
    alvo.querySelector('details').open = true;
    alvo.scrollIntoView({block:'start'});
  }
  window.addEventListener('hashchange', revelarAncora);
  window.addEventListener('load', revelarAncora, {once:true});
  revelarAncora();
})();
