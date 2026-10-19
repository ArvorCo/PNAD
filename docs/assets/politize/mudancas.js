// Politize sua vizinhança: alerta "Sua seção mudou de endereço para o 2º turno". Escrito à mão.
// Lê dados/mudancas/indice.json e dados/mudancas/<UF>/<zona>.json, gerados por
// scripts/mudancas-secoes-2t-build.py (contrato em analysis/mudancas_secoes_2t/CONTRATO.md).
// Não calcula nada: compara só o que o build gravou. Zona sem arquivo (404) = nenhuma mudança.

const URL_AUTOATENDIMENTO = 'https://www.tse.jus.br/servicos-eleitorais/autoatendimento-eleitoral';
const URL_LAUDO = 'mudancas_secoes_abstencoes.html';
const LIMITE_OUTRAS = 40;

const num = (v) => (v === null || v === undefined || v === '' || Number.isNaN(Number(v)) ? null : Number(v));
const txt = (v) => (typeof v === 'string' && v.trim() ? v.trim() : '');
const f1 = (n) => n.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });

function distancia(m) {
  const n = num(m);
  if (n === null) return 'sem coordenada para medir';
  if (n < 1000) return `${Math.round(n).toLocaleString('pt-BR')} m em linha reta`;
  return `${f1(n / 1000)} km em linha reta`;
}

function lista(nums) {
  const t = nums.map(String);
  if (t.length <= 1) return t.join('');
  return `${t.slice(0, -1).join(', ')} e ${t[t.length - 1]}`;
}

function linhaLocal(h, rotulo, nome, ender, bairro, cep) {
  const partes = [ender, bairro, cep ? `CEP ${cep}` : ''].map(txt).filter(Boolean).join(' · ');
  return h('div', { class: 'mud-local' },
    h('p', { class: 'mud-rot' }, rotulo),
    h('p', { class: 'mud-nome' }, txt(nome) || 'Local não informado'),
    partes ? h('p', { class: 'mud-ender' }, partes) : null);
}

function urlMapa(s) {
  const lat = num(s.lat_2t);
  const lon = num(s.lon_2t);
  if (lat !== null && lon !== null) return `https://www.google.com/maps/search/?api=1&query=${lat},${lon}`;
  const q = [s.nome_2t, s.end_2t, s.bairro_2t, s.cep_2t].map(txt).filter(Boolean).join(', ');
  return q ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(q)}` : null;
}

function chaveDestino(s) {
  return [s.nome_2t, s.end_2t, s.categoria].map((x) => txt(x).toLowerCase()).join('|');
}

/** Números das seções do local de votação mostrado (inclui agregadas), para as rotas sem seção digitada. */
async function secoesDoLocal({ buscar, base, uf, zona, local }) {
  const arq = await buscar(`${base}zona/${uf}/${zona}.json`).catch(() => null);
  const t = arq && arq.secoes;
  if (!t || !Array.isArray(t.colunas) || !Array.isArray(t.linhas)) return [];
  const iL = t.colunas.indexOf('local_id');
  const iS = t.colunas.indexOf('secao');
  const iA = t.colunas.indexOf('agregadas');
  const out = [];
  for (const ln of t.linhas) {
    if (ln[iL] !== local.local_id) continue;
    out.push(Number(ln[iS]));
    if (iA >= 0 && Array.isArray(ln[iA])) out.push(...ln[iA].map(Number));
  }
  return out;
}

/**
 * Monta o alerta de mudança de endereço.
 * @param {object} ctx { h, buscar, base, uf, zona, secao (número digitado ou null), local }
 * @returns {Promise<Element|null>}
 */
export async function blocoMudancas(ctx) {
  const { h, buscar, base, local } = ctx;
  const uf = ctx.uf || (local && local._uf);
  const zona = Number(ctx.zona !== undefined && ctx.zona !== null ? ctx.zona : local && local.zona);
  if (!uf || !Number.isFinite(zona)) return null;
  const arq = await buscar(`${base}mudancas/${uf}/${zona}.json`).catch((e) => {
    if (e && e.status !== 404) console.warn('mudancas', e);
    return null;
  });
  const mapa = arq && arq.secoes;
  if (!mapa || typeof mapa !== 'object') return null;

  const porSecao = ctx.secao !== null && ctx.secao !== undefined;
  const daZona = Object.keys(mapa).map(Number).filter(Number.isFinite);
  let alvo = [];
  let principal = null;
  if (porSecao) {
    const mine = mapa[String(ctx.secao)];
    if (!mine) return null;
    principal = Number(ctx.secao);
    const irmas = (Array.isArray(mine.mesmo_predio_1t) ? mine.mesmo_predio_1t : []).map(Number)
      .filter((n) => n !== principal && mapa[String(n)]);
    alvo = [principal, ...irmas];
  } else {
    const doLocal = new Set(await secoesDoLocal({ buscar, base, uf, zona, local }));
    alvo = daZona.filter((n) => doLocal.has(n)).sort((a, b) => a - b);
    if (!alvo.length) return null;
    principal = alvo[0];
  }
  alvo = [...new Set(alvo)];
  const s = mapa[String(principal)];
  const indice = await buscar(`${base}mudancas/indice.json`).catch(() => null);
  const cat = indice && indice.categorias && indice.categorias[s.categoria];
  const outras = alvo.filter((n) => n !== principal).slice(0, LIMITE_OUTRAS);
  const mesmas = outras.filter((n) => chaveDestino(mapa[String(n)]) === chaveDestino(s));
  const diferentes = outras.filter((n) => !mesmas.includes(n));

  const titulo = porSecao ? 'Sua seção mudou de endereço para o 2º turno' : 'Seções deste prédio mudaram de endereço';
  const sub = porSecao
    ? `A seção ${principal}, zona ${zona}, vota em outro lugar em 25 de outubro. Confira antes de sair de casa.`
    : `Em 25 de outubro, a seção ${principal} e outras deste prédio votam em outro lugar. Se a sua seção é uma delas, confira antes de sair de casa.`;
  const mapaUrl = urlMapa(s);
  const motivo = txt(s.motivo_tre);
  const urlTre = txt(s.url_tre);

  return h('aside', { class: 'mudanca entra', 'aria-labelledby': 'mud-titulo' },
    h('p', { class: 'kicker' }, `Local de votação · 2º turno · Zona ${zona}`),
    h('h2', { id: 'mud-titulo' }, titulo),
    h('p', { class: 'mud-sub' }, sub),
    h('div', { class: 'mud-par' },
      linhaLocal(h, 'Onde você votou no 1º turno', s.nome_1t, s.end_1t, s.bairro_1t, ''),
      linhaLocal(h, 'Onde vota em 25 de outubro', s.nome_2t, s.end_2t, s.bairro_2t, s.cep_2t)),
    h('p', { class: 'mud-dist' }, h('b', {}, 'Distância: '), `${distancia(s.distancia_m)}.`),
    cat ? h('p', { class: 'mud-cat' }, h('b', {}, `${txt(cat.nome) || s.categoria}. `), txt(cat.frase)) : null,
    motivo ? h('p', { class: 'mud-motivo' }, h('b', {}, 'Motivo declarado pelo TRE: '), motivo.replace(/\.?$/, '.'),
      urlTre ? h('span', {}, ' ', h('a', { href: urlTre, target: '_blank', rel: 'noopener' }, 'Ver a nota do TRE')) : null) : null,
    mesmas.length
      ? h('p', { class: 'mud-outras' }, `${mesmas.length === 1 ? 'Seção' : 'Seções'} ${lista(mesmas)} também ${mesmas.length === 1 ? 'mudou' : 'mudaram'} para o mesmo lugar.`)
      : null,
    diferentes.length
      ? h('div', { class: 'mud-outras' },
        h('p', {}, `${diferentes.length === 1 ? 'Outra seção do prédio também mudou' : 'Outras seções do prédio também mudaram'}, para destinos diferentes:`),
        h('ul', {}, diferentes.map((n) => {
          const o = mapa[String(n)];
          return h('li', {}, `Seção ${n}: ${txt(o.nome_2t) || 'local não informado'}${txt(o.end_2t) ? `, ${txt(o.end_2t)}` : ''}.`);
        })))
      : null,
    h('div', { class: 'mud-acoes' },
      mapaUrl ? h('a', { class: 'btn btn-mud', href: mapaUrl, target: '_blank', rel: 'noopener' }, 'Abrir o novo endereço no Google Maps') : null,
      h('a', { class: 'btn btn-sec', href: URL_AUTOATENDIMENTO, target: '_blank', rel: 'noopener' }, 'Conferir no TSE ou no e-Título')),
    h('p', { class: 'mud-nota' }, 'A conferência oficial é a do TSE ou do aplicativo e-Título. ',
      h('a', { href: URL_LAUDO }, 'Veja o laudo: quantos votos estão em jogo nessas seções'), '.'));
}

/** Contagem nacional para o aviso da home. Devolve null sem o arquivo. */
export async function resumoMudancas(buscar, base) {
  const i = await buscar(`${base}mudancas/indice.json`).catch(() => null);
  const n = i && num(i.total_secoes);
  return n ? { secoes: n, eleitores: num(i.total_eleitores) } : null;
}
