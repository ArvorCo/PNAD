(() => {
  const root = document.documentElement;
  const progress = document.querySelector('.progress');
  const links = [...document.querySelectorAll('.toc a[href^="#"]')];
  const sections = links.map(link => document.querySelector(link.hash)).filter(Boolean);

  const update = () => {
    const scrollable = root.scrollHeight - innerHeight;
    if (progress) progress.style.width = `${scrollable > 0 ? scrollY / scrollable * 100 : 0}%`;
    let current = sections[0];
    for (const section of sections) {
      if (section.getBoundingClientRect().top <= 120) current = section;
    }
    links.forEach(link => link.classList.toggle('active', current && link.hash === `#${current.id}`));
  };
  addEventListener('scroll', update, { passive: true });
  addEventListener('resize', update);
  update();

  const reveal = [...document.querySelectorAll('.reveal')];
  if (!('IntersectionObserver' in window)) {
    reveal.forEach(node => node.classList.add('in'));
  } else {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('in');
          observer.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    reveal.forEach(node => observer.observe(node));
  }
  window.__revealReady = true;
})();
