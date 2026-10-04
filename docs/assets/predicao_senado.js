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
    const marca = nome ? nome.querySelector(".sn-marca") : null;
    const texto = nome ? (marca ? nome.firstChild.textContent : nome.textContent) : uf;
    title.textContent = texto.trim() + " (" + uf + ")";
    body.innerHTML = f.querySelector(".sn-ficha-corpo").innerHTML;
  }

  links.forEach(function (a, i) {
    /* O clique só troca a ficha ao lado (ou abaixo) do mapa. Não navega pela
       âncora nem altera a URL: a navegação rolava a página até a lista de fichas. */
    a.addEventListener("click", function (event) {
      event.preventDefault();
      const uf = a.dataset.uf;
      select(uf);
      const f = ficha(uf);
      if (f) f.open = true;
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
