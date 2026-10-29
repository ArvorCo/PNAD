/* Escala nacional fixa: mudar o recorte nunca muda a cor de uma mesma renda. */
(function (root) {
  'use strict';
  // Faixa central do acervo: P5 R$ 2.230, mediana R$ 3.770, P95 R$ 6.180.
  // Âncoras arredondadas em reais, interpolação contínua por trechos; extremos saturam.
  const valores = [2000, 3000, 4000, 5000, 6500];
  const cores = ['#b52d3b', '#ed865b', '#f5dfb3', '#6aaed2', '#2164aa'];
  const ativa = (k) => k === 'renda' || k === 'renda_ate2';
  function cor(v, k = 'renda') {
    if (v === null || v === undefined || !Number.isFinite(v)) return '#a9a9a3';
    const pontos = k === 'renda' ? valores : [0, 25, 50, 75, 100];
    const paleta = k === 'renda' ? cores : [...cores].reverse();
    if (v <= pontos[0]) return paleta[0];
    for (let i = 1; i < pontos.length; i++) {
      if (v > pontos[i]) continue;
      const t = (v - pontos[i - 1]) / (pontos[i] - pontos[i - 1]);
      return '#' + [1, 3, 5].map((n) => {
        const a = parseInt(paleta[i - 1].slice(n, n + 2), 16), b = parseInt(paleta[i].slice(n, n + 2), 16);
        return Math.round(a + (b - a) * t).toString(16).padStart(2, '0');
      }).join('');
    }
    return paleta.at(-1);
  }
  function explicacao(k) {
    return k === 'renda' ? 'Escala fixa nacional: R$ 2 mil (vermelho), R$ 3 mil, R$ 4 mil, R$ 5 mil e R$ 6,5 mil (azul), com gradiente entre valores. Os extremos mantêm a cor limite. Não mede dívidas nem saldo financeiro.' : 'Parcela estimada até 2 salários: azul para menor parcela, vermelho para maior parcela. Escala fixa de 0 a 100%.';
  }
  function legenda(el, k) {
    const renda = k === 'renda', pontos = renda ? valores : [0, 25, 50, 75, 100], paleta = renda ? cores : [...cores].reverse();
    const gradiente = paleta.map((c, i) => c + ' ' + 100 * (pontos[i] - pontos[0]) / (pontos.at(-1) - pontos[0]) + '%').join(',');
    el.innerHTML = `<b>${renda ? 'Renda estimada' : 'Até 2 salários'}</b><span class="renda-regua"><span style="background:linear-gradient(90deg,${gradiente})"></span><span class="renda-marcas" style="--meio:${renda ? 44.444 : 50}%"><span>${renda ? '≤ R$ 2 mil' : '0%'}</span><span>${renda ? 'R$ 4 mil' : '50%'}</span><span>${renda ? '≥ R$ 6,5 mil' : '100%'}</span></span></span><small>PNAD · cinza: sem dado</small>`;
  }
  root.RendaMapa = { ativa, cor, legenda, explicacao };
})(window);
