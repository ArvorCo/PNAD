/* Camada de interface da página de predição: navegação, progresso, sumários,
   ordenação de tabela e acessibilidade de regiões roláveis.
   Melhoria progressiva: sem este arquivo a página continua completa e legível.
   Não toca no motor (Prediction2026, PredictionSimulator) nem no mapa. */
(function () {
  "use strict";

  const doc = document;
  const root = doc.documentElement;
  const reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const behavior = reduce ? "auto" : "smooth";

  function frame(fn) {
    let queued = false;
    return function () {
      if (queued) return;
      queued = true;
      requestAnimationFrame(function () {
        queued = false;
        fn();
      });
    };
  }

  /* Altura real da barra de capítulos: alimenta scroll-padding e o topo do simulador. */
  const nav = doc.querySelector(".chapter-nav");
  function measureNav() {
    if (!nav) return;
    root.style.setProperty("--nav-h", Math.ceil(nav.getBoundingClientRect().height) + "px");
  }

  /* Progresso de leitura e botão de voltar ao topo. */
  const bar = doc.querySelector(".read-progress-bar");
  const toTop = doc.querySelector(".to-top");
  const onScroll = frame(function () {
    const max = root.scrollHeight - window.innerHeight;
    if (bar) bar.style.transform = "scaleX(" + (max > 0 ? Math.min(1, Math.max(0, window.scrollY / max)) : 0).toFixed(4) + ")";
    if (toTop) {
      const show = window.scrollY > window.innerHeight * 1.2;
      toTop.hidden = false;
      toTop.classList.toggle("is-on", show);
      toTop.tabIndex = show ? 0 : -1;
      toTop.setAttribute("aria-hidden", show ? "false" : "true");
    }
  });
  if (toTop) {
    toTop.addEventListener("click", function (event) {
      event.preventDefault();
      window.scrollTo({ top: 0, behavior: behavior });
      const top = doc.getElementById("topo");
      if (top) {
        top.setAttribute("tabindex", "-1");
        top.focus({ preventScroll: true });
      }
    });
  }

  /* Capítulo atual no menu, por IntersectionObserver. */
  function setupActiveNav() {
    if (!nav || !("IntersectionObserver" in window)) return;
    const links = Array.prototype.slice.call(nav.querySelectorAll('a[href^="#"]'));
    const sections = links
      .map(function (a) {
        return doc.getElementById(a.getAttribute("href").slice(1));
      })
      .filter(Boolean);
    if (!sections.length) return;
    const visible = new Set();
    const scroller = nav.querySelector(".wrap");
    let current = null;

    function mark(section) {
      if (section === current) return;
      current = section;
      links.forEach(function (a) {
        const on = section && a.getAttribute("href") === "#" + section.id;
        if (on) {
          a.setAttribute("aria-current", "location");
          if (scroller && scroller.scrollWidth > scroller.clientWidth) {
            const left = a.offsetLeft - (scroller.clientWidth - a.offsetWidth) / 2;
            scroller.scrollTo({ left: Math.max(0, left), behavior: behavior });
          }
        } else {
          a.removeAttribute("aria-current");
        }
      });
    }

    function pick() {
      const atEnd = window.scrollY + window.innerHeight >= root.scrollHeight - 4;
      if (atEnd) return mark(sections[sections.length - 1]);
      let chosen = null;
      sections.forEach(function (s) {
        if (visible.has(s)) chosen = s;
      });
      if (chosen) return mark(chosen);
      if (sections[0].getBoundingClientRect().top > window.innerHeight * 0.4) mark(null);
    }

    let observer = null;
    function observe() {
      if (observer) observer.disconnect();
      const top = Math.ceil(nav.getBoundingClientRect().height) + 10;
      observer = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (e) {
            if (e.isIntersecting) visible.add(e.target);
            else visible.delete(e.target);
          });
          pick();
        },
        { rootMargin: "-" + top + "px 0px -58% 0px", threshold: 0 }
      );
      sections.forEach(function (s) {
        observer.observe(s);
      });
    }
    observe();
    window.addEventListener("scroll", frame(pick), { passive: true });
    window.addEventListener("resize", frame(observe));
    links.forEach(function (a) {
      a.addEventListener("click", function () {
        const s = doc.getElementById(a.getAttribute("href").slice(1));
        if (s) mark(s);
      });
    });
    pick();
  }

  /* Esconde o botão de topo sobre o simulador no celular (a barra fixa dele usa o rodapé). */
  function watchSimulator() {
    const sim = doc.getElementById("simulador");
    if (!sim || !("IntersectionObserver" in window)) return;
    new IntersectionObserver(
      function (entries) {
        doc.body.classList.toggle("in-simulator", entries.some(function (e) { return e.isIntersecting; }));
      },
      { threshold: 0.05 }
    ).observe(sim);
  }

  /* Sumário interno dos capítulos longos, montado a partir dos h3 que ficam fora de <details>. */
  function slug(text) {
    return text
      .toLowerCase()
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "")
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 48);
  }
  function buildToc(section) {
    const heads = Array.prototype.slice.call(section.querySelectorAll("h3")).filter(function (h) {
      return !h.closest("details") && !h.closest(".comparison") && !h.closest(".simulator");
    });
    if (heads.length < 3) return;
    const lead = section.querySelector(".lead");
    const anchor = lead || section.querySelector(".chapter-head");
    if (!anchor) return;
    const box = doc.createElement("nav");
    box.className = "toc";
    box.setAttribute("aria-label", "Neste capítulo");
    const title = doc.createElement("p");
    title.className = "eyebrow";
    title.textContent = "Neste capítulo";
    const list = doc.createElement("ol");
    const used = new Set();
    heads.forEach(function (h, i) {
      if (!h.id) {
        let id = section.id + "-" + (slug(h.textContent) || "t" + (i + 1));
        while (doc.getElementById(id) || used.has(id)) id += "-" + (i + 1);
        h.id = id;
      }
      used.add(h.id);
      const li = doc.createElement("li");
      const a = doc.createElement("a");
      a.href = "#" + h.id;
      a.textContent = h.textContent;
      li.appendChild(a);
      list.appendChild(li);
    });
    box.appendChild(title);
    box.appendChild(list);
    anchor.insertAdjacentElement("afterend", box);
  }
  function setupToc() {
    ["pesquisa", "metodo", "incerteza", "validacao", "aprendizado"].forEach(function (id) {
      const s = doc.getElementById(id);
      if (s) buildToc(s);
    });
  }

  /* Ordenação por clique no cabeçalho, nas tabelas marcadas com data-sortable. */
  const collator = new Intl.Collator("pt-BR", { numeric: true, sensitivity: "base" });
  function cellNumber(text) {
    const m = text.replace(/−/g, "-").match(/-?\d[\d.]*(?:,\d+)?/);
    if (!m) return NaN;
    return parseFloat(m[0].replace(/\./g, "").replace(",", "."));
  }
  function setupSortable(table) {
    const head = table.tHead && table.tHead.rows[0];
    const body = table.tBodies[0];
    if (!head || !body) return;
    const rows = Array.prototype.slice.call(body.rows);
    rows.forEach(function (r, i) {
      r.dataset.order = String(i);
    });
    const ths = Array.prototype.slice.call(head.cells);
    const numeric = ths.map(function (_, j) {
      const values = rows.map(function (r) {
        return cellNumber(r.cells[j].textContent);
      });
      return values.filter(function (v) { return !isNaN(v); }).length >= rows.length * 0.5 && ths[j].classList.contains("num");
    });
    const status = doc.createElement("p");
    status.className = "mx-sr";
    status.setAttribute("role", "status");
    status.style.cssText = "position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)";
    table.parentNode.parentNode.insertBefore(status, table.parentNode.nextSibling);
    const hint = doc.createElement("p");
    hint.className = "note sort-hint";
    hint.textContent = "Clique no cabeçalho de uma coluna para ordenar; um terceiro clique restaura a ordem original.";
    table.parentNode.parentNode.insertBefore(hint, table.parentNode);

    ths.forEach(function (th, j) {
      const label = th.textContent;
      const btn = doc.createElement("button");
      btn.type = "button";
      btn.className = "sort-btn";
      btn.textContent = label;
      th.textContent = "";
      th.appendChild(btn);
      btn.addEventListener("click", function () {
        const cur = th.getAttribute("aria-sort");
        const next = cur === "ascending" ? "descending" : cur === "descending" ? "none" : "ascending";
        ths.forEach(function (o) {
          o.removeAttribute("aria-sort");
        });
        let sorted = rows.slice();
        if (next === "none") {
          sorted.sort(function (a, b) {
            return a.dataset.order - b.dataset.order;
          });
        } else {
          th.setAttribute("aria-sort", next);
          const dir = next === "ascending" ? 1 : -1;
          sorted.sort(function (a, b) {
            const ta = a.cells[j].textContent.trim();
            const tb = b.cells[j].textContent.trim();
            let r;
            if (numeric[j]) {
              const na = cellNumber(ta);
              const nb = cellNumber(tb);
              r = (isNaN(na) ? -Infinity : na) - (isNaN(nb) ? -Infinity : nb);
              if (!isFinite(r)) r = isNaN(na) === isNaN(nb) ? 0 : isNaN(na) ? -1 : 1;
            } else {
              r = collator.compare(ta, tb);
            }
            return r * dir || a.dataset.order - b.dataset.order;
          });
        }
        sorted.forEach(function (r) {
          body.appendChild(r);
        });
        status.textContent =
          next === "none"
            ? "Ordem original restaurada."
            : "Ordenado por " + label + ", " + (next === "ascending" ? "crescente" : "decrescente") + ".";
      });
    });
  }

  /* Regiões roláveis precisam entrar na ordem do teclado. */
  function markScrollable() {
    doc.querySelectorAll(".table-scroll,.equation,.wide-chart,pre,.preset-grid").forEach(function (el) {
      if (el.closest("details:not([open])")) return;
      const scrolls = el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 1;
      if (scrolls && !el.hasAttribute("tabindex")) {
        el.setAttribute("tabindex", "0");
        if (!el.hasAttribute("role")) el.setAttribute("role", "region");
        if (!el.hasAttribute("aria-label")) {
          el.setAttribute(
            "aria-label",
            el.matches("pre") ? "Comando, rolagem horizontal" : el.matches(".equation") ? "Equação, rolagem horizontal" : "Conteúdo com rolagem horizontal"
          );
        }
      }
    });
  }

  /* Botão de copiar nos blocos de comando. */
  function setupCopy() {
    doc.querySelectorAll("pre").forEach(function (pre) {
      if (!navigator.clipboard || pre.parentNode.classList.contains("code-block")) return;
      const wrap = doc.createElement("div");
      wrap.className = "code-block";
      pre.parentNode.insertBefore(wrap, pre);
      const btn = doc.createElement("button");
      btn.type = "button";
      btn.className = "copy-btn";
      btn.textContent = "Copiar comandos";
      btn.addEventListener("click", function () {
        navigator.clipboard.writeText(pre.textContent).then(
          function () {
            btn.textContent = "Copiado";
            setTimeout(function () {
              btn.textContent = "Copiar comandos";
            }, 1800);
          },
          function () {
            btn.textContent = "Copie à mão";
          }
        );
      });
      wrap.appendChild(btn);
      wrap.appendChild(pre);
    });
  }

  /* Âncoras #estado-UF apontam para <details> fechados: abre antes de rolar. */
  function openFor(el) {
    let opened = false;
    for (let node = el; node; node = node.parentElement) {
      if (node.tagName === "DETAILS" && !node.open) {
        node.open = true;
        opened = true;
      }
    }
    return opened;
  }
  function openTarget() {
    const id = decodeURIComponent(location.hash.slice(1));
    const el = id ? doc.getElementById(id) : null;
    if (el && openFor(el)) {
      requestAnimationFrame(function () {
        el.scrollIntoView({ block: "start" });
      });
    }
  }
  doc.addEventListener("click", function (event) {
    const a = event.target.closest && event.target.closest('a[href^="#"]');
    if (!a || a.getAttribute("href").length < 2) return;
    const el = doc.getElementById(decodeURIComponent(a.getAttribute("href").slice(1)));
    if (!el) return;
    openFor(el);
    if (location.hash === a.getAttribute("href")) {
      event.preventDefault();
      el.scrollIntoView({ block: "start", behavior: behavior });
    }
  });

  /* Impressão: abre todos os detalhes e restaura depois. */
  let reopened = [];
  window.addEventListener("beforeprint", function () {
    reopened = Array.prototype.slice.call(doc.querySelectorAll("details:not([open])"));
    reopened.forEach(function (d) {
      d.open = true;
    });
  });
  window.addEventListener("afterprint", function () {
    reopened.forEach(function (d) {
      d.open = false;
    });
    reopened = [];
  });

  function init() {
    measureNav();
    setupToc();
    doc.querySelectorAll("table[data-sortable]").forEach(setupSortable);
    setupCopy();
    setupActiveNav();
    watchSimulator();
    markScrollable();
    onScroll();
    openTarget();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", frame(function () {
      measureNav();
      markScrollable();
      onScroll();
    }));
    window.addEventListener("hashchange", openTarget);
    doc.addEventListener("toggle", frame(markScrollable), true);
    if (doc.fonts && doc.fonts.ready) doc.fonts.ready.then(measureNav);
    root.classList.add("js-ui");
  }

  if (doc.readyState === "loading") doc.addEventListener("DOMContentLoaded", init);
  else init();
})();
