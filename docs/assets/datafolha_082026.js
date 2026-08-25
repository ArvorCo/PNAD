(() => {
  const root = document.documentElement;
  const progress = document.querySelector(".progress");
  const links = [...document.querySelectorAll(".nav a[href^='#']")];
  const sections = links.map((link) => document.querySelector(link.hash)).filter(Boolean);

  const onScroll = () => {
    const max = root.scrollHeight - innerHeight;
    if (progress) progress.style.width = `${max > 0 ? (scrollY / max) * 100 : 0}%`;
    const line = scrollY + innerHeight * 0.32;
    let active = sections[0];
    for (const section of sections) if (section.offsetTop <= line) active = section;
    for (const link of links) link.classList.toggle("active", active && link.hash === `#${active.id}`);
  };

  const observer = new IntersectionObserver((entries) => {
    for (const entry of entries) if (entry.isIntersecting) {
      entry.target.classList.add("in");
      observer.unobserve(entry.target);
    }
  }, { threshold: 0.08, rootMargin: "0px 0px -4%" });

  document.querySelectorAll(".reveal").forEach((node) => observer.observe(node));
  addEventListener("scroll", onScroll, { passive: true });
  addEventListener("resize", onScroll);
  onScroll();
})();

/* Mantém o item ativo do sumário visível quando ele rola na horizontal. */
(() => {
  const bar = document.querySelector(".nav .wrap");
  if (!bar) return;
  let current = null;
  const sync = () => {
    const active = bar.querySelector("a.active");
    if (!active || active === current) return;
    current = active;
    const left = active.offsetLeft - bar.clientWidth / 2 + active.offsetWidth / 2;
    bar.scrollTo({ left: Math.max(0, left), behavior: "smooth" });
  };
  addEventListener("scroll", sync, { passive: true });
  sync();
})();

/* Gráficos e fac-símiles abrem em tamanho real, que é o que salva a leitura no celular. */
(() => {
  const figures = document.querySelectorAll(".report-chart img, .print img");
  for (const image of figures) {
    if (image.closest("a")) continue;
    const link = document.createElement("a");
    link.href = image.currentSrc || image.src;
    link.target = "_blank";
    link.rel = "noopener";
    link.className = "zoom";
    link.title = "Abrir em tamanho real";
    image.replaceWith(link);
    link.append(image);
  }
})();
