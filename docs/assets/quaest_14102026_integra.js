/* Leitor das páginas arquivadas; dados locais, URL compartilhável e fallback HTML. */
(() => {
  'use strict';
  const source = document.getElementById('q-document-data');
  if (!source) return;
  const pages = JSON.parse(source.textContent);
  const topic = document.getElementById('q-document-topic');
  const select = document.getElementById('q-document-page');
  const share = document.getElementById('q-document-share');
  const picture = document.getElementById('q-document-image');
  let current = 19;
  function list() { return pages.filter(p => topic.value === 'all' || p.tema === topic.value); }
  function options() {
    select.replaceChildren(...list().map(p => {
      const option = document.createElement('option');
      option.value = p.pagina;
      option.textContent = `${p.pagina} · ${p.titulo}`;
      return option;
    }));
  }
  function show(number, updateURL) {
    const p = pages.find(item => item.pagina === Number(number));
    if (!p) return;
    current = p.pagina;
    select.value = current;
    picture.src = p.imagem;
    picture.alt = `Página ${p.pagina}: ${p.titulo}`;
    document.getElementById('q-document-image-link').href = p.imagem;
    document.getElementById('q-document-pdf').href = `fontes/quaest_14102026.pdf#page=${p.pagina}`;
    document.getElementById('q-document-status').textContent = `Página ${p.pagina} de ${pages.length} · ${p.titulo}`;
    const selected = list();
    const index = selected.findIndex(item => item.pagina === current);
    document.getElementById('q-document-prev').disabled = index <= 0;
    document.getElementById('q-document-next').disabled = index === selected.length - 1;
    const url = new URL(location.href);
    url.searchParams.set('pagina', current);
    url.hash = 'documentos';
    share.href = url.href;
    if (updateURL) history.replaceState(null, '', url.href);
  }
  function restore() {
    topic.value = 'all';
    options();
    const value = Number(new URL(location.href).searchParams.get('pagina'));
    show(pages.some(p => p.pagina === value) ? value : 19, false);
  }
  topic.addEventListener('change', () => { options(); show(list()[0].pagina, true); });
  select.addEventListener('change', () => show(select.value, true));
  for (const [id, direction] of [['prev', -1], ['next', 1]]) {
    document.getElementById(`q-document-${id}`).addEventListener('click', () => {
      const selected = list();
      const next = selected[selected.findIndex(p => p.pagina === current) + direction];
      if (next) show(next.pagina, true);
    });
  }
  window.addEventListener('popstate', restore);
  // Âncoras de temas abrem os detalhes antes de levar o leitor ao destino.
  function openTopic() {
    if (!location.hash.startsWith('#tema-')) return;
    const detail = document.getElementById(location.hash.slice(1));
    if (detail && detail.tagName === 'DETAILS') detail.open = true;
  }
  document.querySelectorAll('.q-theme-index a').forEach(link => {
    link.addEventListener('click', () => {
      const detail = document.getElementById(link.hash.slice(1));
      if (detail) detail.open = true;
    });
  });
  window.addEventListener('hashchange', openTopic);
  restore(); openTopic();
  document.getElementById('q-document-controls').hidden = false;
  document.getElementById('q-document-nav').hidden = false;
})();
