/* Progressive enhancement only: every chart and table is already in the HTML. */
(() => {
  if (!('IntersectionObserver' in window)) return;
  const links = new Map([...document.querySelectorAll('.toc a')].map(a => [a.hash.slice(1), a]));
  const observer = new IntersectionObserver(entries => {
    const visible = entries.filter(entry => entry.isIntersecting);
    if (!visible.length) return;
    links.forEach(link => link.classList.remove('active'));
    const link = links.get(visible[0].target.id);
    if (link) link.classList.add('active');
  }, { rootMargin: '-10% 0px -75% 0px' });
  document.querySelectorAll('main section').forEach(section => observer.observe(section));
})();
