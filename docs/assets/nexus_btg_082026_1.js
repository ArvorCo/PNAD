(() => {
  "use strict";

  const $$ = selector => [...document.querySelectorAll(selector)];

  /* Barra de progresso da leitura. */
  const progress = document.querySelector(".progress");
  if (progress) {
    const update = () => {
      const height = document.documentElement.scrollHeight - window.innerHeight;
      progress.style.width = height > 0 ? `${(window.scrollY / height) * 100}%` : "0%";
    };
    addEventListener("scroll", update, { passive: true });
    addEventListener("resize", update);
    update();
  }

  /* Sumário: marca o capítulo em que o leitor está. */
  const links = $$(".toc-links a");
  const sections = links
    .map(link => ({ link, section: document.querySelector(link.getAttribute("href")) }))
    .filter(item => item.section);

  if (sections.length && "IntersectionObserver" in window) {
    const seen = new Set();
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) seen.add(entry.target);
        else seen.delete(entry.target);
      });
      const current = sections.find(item => seen.has(item.section));
      links.forEach(link => link.classList.toggle("on", current ? link === current.link : false));
    }, { rootMargin: "-56px 0px -70% 0px" });
    sections.forEach(item => observer.observe(item.section));
  }

  /* Revelação ao rolar, sempre atrás da classe .js para não esconder conteúdo sem script. */
  const reveals = $$(".reveal");
  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver(entries => entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add("visible");
        observer.unobserve(entry.target);
      }
    }), { threshold: 0.06 });
    reveals.forEach(node => observer.observe(node));
  } else {
    reveals.forEach(node => node.classList.add("visible"));
  }
})();
