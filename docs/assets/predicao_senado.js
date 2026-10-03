/* Liga o clique e o teclado da UF à ficha. Sem este arquivo, a página continua
   completa: o mapa tem links e as 27 fichas estão renderizadas abaixo. */
(function () {
  "use strict";
  const doc = document;
  const map = doc.getElementById("sn-map");
  const panel = doc.getElementById("sn-painel");
  const body = doc.getElementById("sn-painel-corpo");
  const title = doc.getElementById("sn-painel-titulo");
  if (!map) return;
  const wide = window.matchMedia("(min-width: 900px)");
  const links = Array.prototype.slice.call(map.querySelectorAll("a.sn-uf"));

  function ficha(uf) {
    return doc.getElementById("estado-" + uf);
  }

  function select(uf) {
    links.forEach(function (a) {
      a.classList.toggle("is-sel", a.dataset.uf === uf);
    });
    const f = ficha(uf);
    if (!f || !panel || !body || !title) return;
    const nome = f.querySelector("summary span");
    title.textContent = (nome ? nome.textContent : uf) + " (" + uf + ")";
    body.innerHTML = f.querySelector(".sn-ficha-corpo").innerHTML;
  }

  links.forEach(function (a, i) {
    a.addEventListener("click", function (event) {
      const uf = a.dataset.uf;
      select(uf);
      if (wide.matches) {
        event.preventDefault();
        history.replaceState(null, "", "#estado-" + uf);
      } else {
        const f = ficha(uf);
        if (f) f.open = true;
      }
    });
    a.addEventListener("keydown", function (event) {
      let next = null;
      if (event.key === "ArrowRight" || event.key === "ArrowDown") next = links[(i + 1) % links.length];
      if (event.key === "ArrowLeft" || event.key === "ArrowUp") next = links[(i - 1 + links.length) % links.length];
      if (next) {
        event.preventDefault();
        next.focus();
      }
    });
  });

  /* Abrir uma ficha pelo link da tabela também seleciona a UF no mapa. */
  function fromHash() {
    const m = /^#estado-([A-Z]{2})$/.exec(location.hash);
    if (m) select(m[1]);
  }
  window.addEventListener("hashchange", fromHash);
  fromHash();
})();
