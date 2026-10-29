/* Ajusta o canvas ao espaço real e sinaliza filtros ativos sem abrir o painel. */
(function () {
  'use strict';
  const $ = (s) => document.querySelector(s);
  const mapa = $('#mapa'), botao = $('#filtros-toggle');
  if (typeof ResizeObserver !== 'undefined') new ResizeObserver(() => {
    window.politizeseMapa?.estado.mapa?.invalidateSize({ pan: false });
  }).observe(mapa);
  function resumo() {
    const campos = ['#f-uf', '#f-mun', '#f-zona', '#f-texto', '#q-cep', '#f-ultimo', '#f-encerramento'];
    const n = campos.filter((id) => $(id).value).length + Number($('#f-chuva').checked);
    $('#filtros-ativos').textContent = n ? `(${n})` : '';
  }
  function fechar() {
    document.body.classList.remove('filtros-abertos');
    botao.setAttribute('aria-expanded', 'false');
  }
  document.addEventListener('change', resumo);
  document.addEventListener('input', resumo);
  $('#f-busca').addEventListener('submit', () => { fechar(); botao.focus(); });
  document.addEventListener('keydown', (ev) => { if (ev.key === 'Escape' && document.body.classList.contains('filtros-abertos')) { fechar(); botao.focus(); } });
  // O hash e a limpeza também alteram controles por código.
  new MutationObserver(resumo).observe($('#status'), { childList: true, subtree: true, characterData: true });
  window.addEventListener('hashchange', resumo);
  $('#b-limpar').addEventListener('click', resumo);
  resumo();
})();
