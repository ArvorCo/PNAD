/* Espelho de scripts/reponderacao-simulador.py. Sem DOM, testável em Node. */
((host) => {
  'use strict';
  const keys = ['flavio', 'lula', 'indecisos', 'branco_nulo'];
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  function parameters(data, input = {}) {
    const p = {...data.defaults, ...input};
    if (!['publicado', 'pnad', 'modelo'].includes(p.modo) || !data.rates[p.idade]) throw Error('Cenário inválido');
    for (const [k, [a,b]] of Object.entries(data.limits)) {
      if (k === 'indecisos_flavio' && p[k] === null) continue;
      if (!Number.isFinite(p[k]) || p[k] < a || p[k] > b) throw Error(`Parâmetro inválido: ${k}`);
    }
    return p;
  }
  function calibrate(masses, rates, target) {
    let low = 0, high = 64;
    for (let i = 0; i < 64; i++) {
      const middle = (low + high) / 2;
      const attendance = keys.reduce((s,k) => s + masses[k] * Math.min(1, middle * rates[k]), 0);
      if (attendance < target) low = middle; else high = middle;
    }
    return Object.fromEntries(keys.map(k => [k, Math.min(1, (low + high) / 2 * rates[k])]));
  }
  function pollResult(row, data, p) {
    const m = row[p.modo === 'publicado' ? 'published' : 'pnad'];
    const rates = p.modo === 'modelo' ? {...data.rates[p.idade]} : Object.fromEntries(keys.map(k => [k,1]));
    rates.flavio *= 1 + p.presenca_relativa / 100;
    const q = calibrate(m, rates, p.comparecimento);
    let [f,l,u,b] = keys.map(k => m[k] * q[k]);
    const uf = p.indecisos_flavio === null ? f / (f + l) : p.indecisos_flavio / 100;
    const vu = u * p.indecisos_validos / 100;
    f += vu * uf; l += vu * (1 - uf); b += u - vu;
    const shift = clamp(p.comparecimento * p.branco_nulo_pp / 100, -b, f + l - 1e-9);
    const share = f / (f + l);
    f -= shift * share; l -= shift * (1-share); b += shift;
    const nf = f * Math.max(0,p.nulo_diferencial_pp) / 100;
    const nl = l * Math.max(0,-p.nulo_diferencial_pp) / 100;
    f -= nf; l -= nl; b += nf + nl;
    const valid = f + l;
    const fs = clamp(f / valid + p.vies_pp / 200, 0, 1);
    return {id: row.id, instituto: row.instituto, divulgacao: row.divulgacao, flavio: 100*fs, lula: 100*(1-fs),
      validos: valid, branco_nulo: b, comparecimento: p.comparecimento,
      abstencao: 100-p.comparecimento, taxas:q};
  }
  function evaluate(data, input = {}) {
    const p = parameters(data,input);
    const polls = data.polls.map(r => pollResult(r,data,p));
    if (!polls.length) throw Error('Nenhuma pesquisa elegível');
    const out = Object.fromEntries(['flavio','lula','validos','branco_nulo','comparecimento','abstencao']
      .map(k => [k, polls.reduce((s,r) => s+r[k],0)/polls.length]));
    out.diferenca_flavio_lula = out.flavio-out.lula;
    out.por_100_eleitores = {flavio:out.validos*out.flavio/100,lula:out.validos*out.lula/100,
      branco_nulo:out.branco_nulo,abstencao:out.abstencao};
    out.taxas = Object.fromEntries(keys.map(k => [k,polls.reduce((s,r) => s+r.taxas[k],0)/polls.length]));
    return {...out,polls,parametros:p};
  }
  function encode(data, input) {
    const p = parameters(data,input);
    const fields = Object.keys(data.defaults).map(k => `${k}:${p[k] === null ? 'p' : p[k]}`);
    return '#sim=' + ['v:'+data.version,...fields].join(';');
  }
  function decode(data, hash) {
    if (!hash.startsWith('#sim=')) return {...data.defaults};
    const input = {};
    for (const item of hash.slice(5).split(';')) {
      const [k,value] = item.split(':');
      if (!Object.hasOwn(data.defaults,k)) continue;
      input[k] = ['modo','idade'].includes(k) ? value : k === 'indecisos_flavio' && value === 'p' ? null : Number(value);
    }
    return parameters(data,input);
  }
  function breakEven(data, input) {
    let low = -30, high = 30;
    if (evaluate(data,{...input,presenca_relativa:low}).diferenca_flavio_lula > 0 ||
        evaluate(data,{...input,presenca_relativa:high}).diferenca_flavio_lula < 0) return null;
    for (let i=0;i<40;i++) {
      const middle=(low+high)/2;
      if (evaluate(data,{...input,presenca_relativa:middle}).diferenca_flavio_lula < 0) low=middle; else high=middle;
    }
    return (low+high)/2;
  }
  const api = {parameters,evaluate,encode,decode,breakEven};
  if (typeof module !== 'undefined' && module.exports) module.exports=api;
  else host.Reponderacao2T=api;
})(typeof window !== 'undefined' ? window : globalThis);
