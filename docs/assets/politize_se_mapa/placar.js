/* A borda e a área representam o placar; o centro continua sendo a lente ativa. */
(function (root) {
  'use strict';
  const AZUL = '#1f5f9e', VERMELHO = '#c8412f', CINZA = '#9a9c97';
  const numero = (v) => typeof v === 'number' && Number.isFinite(v) && v >= 0;
  function resumo(ls) {
    let f = 0, l = 0, cobertos = 0, boletimParcial = false;
    for (const x of ls) {
      if (!numero(x.flavio2) || !numero(x.lula2) || x.flavio2 + x.lula2 <= 0) continue;
      f += x.flavio2; l += x.lula2; cobertos++;
      boletimParcial ||= numero(x.n_bu2) && numero(x.n_secoes) && x.n_bu2 < x.n_secoes;
    }
    const total = f + l;
    return { f, l, total, cobertos, locais: ls.length, parcial: boletimParcial || (cobertos > 0 && cobertos < ls.length),
      pf: total ? 100 * f / total : null, pl: total ? 100 * l / total : null,
      margem: total ? 100 * Math.abs(f - l) / total : null };
  }
  // Área adicional proporcional à vantagem em pontos percentuais, simétrica.
  const raio = (r) => r.margem === null ? 18 : Math.sqrt(18 ** 2 + (32 ** 2 - 18 ** 2) * r.margem / 100);
  const pct = (n) => n === null ? 'sem dado' : n.toLocaleString('pt-BR', { maximumFractionDigits: 1, minimumFractionDigits: 1 }) + '%';
  function descricao(r) {
    if (!r.total) return 'Sem placar publicável do 2º turno';
    return `Flávio ${pct(r.pf)} · Lula ${pct(r.pl)} · diferença ${pct(r.margem).replace('%', ' pontos')} · ${r.cobertos} de ${r.locais} locais com placar${r.parcial ? ' · cobertura parcial' : ''}`;
  }
  function renderer() {
    const Anel = L.Canvas.extend({
      _updateCircle(layer) {
        L.Canvas.prototype._updateCircle.call(this, layer);
        if (!this._drawing || layer._empty() || !layer.options.local) return;
        const r = resumo([layer.options.local]), p = layer._point, radius = Math.max(Math.round(layer._radius), 1), ctx = this._ctx;
        ctx.save(); ctx.lineWidth = 4; ctx.globalAlpha = 1;
        const inicio = -Math.PI / 2, fim = inicio + 2 * Math.PI * (r.pf ?? 0) / 100;
        const arco = (a, b, cor) => { if (b <= a) return; ctx.beginPath(); ctx.strokeStyle = cor; ctx.arc(p.x, p.y, radius, a, b); ctx.stroke(); };
        if (!r.total) arco(inicio, inicio + 2 * Math.PI, CINZA);
        else { arco(inicio, fim, AZUL); arco(fim, inicio + 2 * Math.PI, VERMELHO); }
        if (r.parcial) { ctx.beginPath(); ctx.lineWidth = 1.5; ctx.setLineDash([3, 2]); ctx.strokeStyle = '#62665e'; ctx.arc(p.x, p.y, radius - 4, 0, 2 * Math.PI); ctx.stroke(); }
        ctx.restore();
      },
    });
    return new Anel({ padding: .5 });
  }
  root.PlacarMapa = { resumo, raio, descricao, renderer, pct };
  root.criarPlacarMapa = function ({ S, buscar }) {
    const cache = new Map();
    async function carregar(ufs) {
      await Promise.all(ufs.map(async (uf) => {
        if (!cache.has(uf)) {
          const d = await buscar('assets/politize_se_mapa/placares/' + uf + '.json.gz');
          if (d.formato !== 1 || d.uf !== uf) throw new Error('formato');
          cache.set(uf, d.locais);
        }
        for (const l of S.porUf.get(uf) || []) [l.flavio2, l.lula2] = cache.get(uf)[l.id] || [null, null];
      }));
    }
    function icone(filhos, cor) {
      const r = resumo(filhos), tam = 2 * raio(r), n = filhos.length;
      const texto = n >= 1000 ? (n / 1000).toLocaleString('pt-BR', { maximumFractionDigits: 0 }) + ' mil' : String(n);
      const anel = r.total ? `conic-gradient(${AZUL} 0 ${r.pf}%, ${VERMELHO} ${r.pf}% 100%)` : CINZA;
      return L.divIcon({
        html: `<span class="placar-anel${r.parcial ? ' placar-parcial' : ''}" title="${descricao(r)}" aria-label="${n} locais. ${descricao(r)}" style="background:${anel}"><span class="placar-miolo" style="background:${cor};font-size:${n >= 1000 ? 9 : 11}px">${texto}</span></span>`,
        className: 'grupo-placar', iconSize: [tam, tam], iconAnchor: [tam / 2, tam / 2],
      });
    }
    function aplicar(ls) {
      for (const l of ls) {
        l.fatia_l2 = numero(l.fatia_f2) ? 100 - l.fatia_f2 : null;
        l.d_lula_pp = typeof l.d_fatia_pp === 'number' ? -l.d_fatia_pp : null;
      }
      return ls;
    }
    return { carregar, aplicar, icone, raio: (l) => raio(resumo([l])), descricao: (l) => descricao(resumo([l])) };
  };
})(typeof window !== 'undefined' ? window : globalThis);
