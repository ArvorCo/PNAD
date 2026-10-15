// Politize sua vizinhança: bloco "Sua seção precisa de fiscal". Escrito à mão.
// Lê dados/fiscal/regras.json e dados/fiscal/<UF>/<zona>.json, gerados por
// scripts/politize-fiscal.py (contrato em analysis/politize/CONTRATO.md, seção Fiscalização).
// Não calcula nada: só ordena e formata o que o build gravou.

import { blocoLogs } from './logs.js?v=20261015-8';

const ORDEM = ['padrao', 'reforcada', 'alta', 'maxima'];
const PESO_NIVEL = { maxima: 3, alta: 2, reforcada: 1, padrao: 0 };
const NOME_C13 = { alta: 'alto', media: 'médio', baixa: 'baixo' };
const NOME_TERR = { alto: 'alto', medio: 'médio', baixo: 'baixo' };
const LIMITE_CHIPS = 30;

function tabelaDe(t) {
  if (!t || !Array.isArray(t.colunas) || !Array.isArray(t.linhas)) return [];
  return t.linhas.map((ln) => Object.fromEntries(t.colunas.map((c, i) => [c, ln[i]])));
}

function maiuscula(t) {
  return t ? t.charAt(0).toUpperCase() + t.slice(1) : t;
}

function plural(n, um, varios) {
  return `${n} ${n === 1 ? um : varios}`;
}

/** Sinais de uma seção já com o texto do critério, mais pesados primeiro. */
function sinaisDe(regras, linha, local, zonaSinais) {
  const crit = regras.criterios || {};
  const out = [];
  const vistos = new Set();
  const add = (cod, detalhe, origem) => {
    if (vistos.has(cod)) return;
    vistos.add(cod);
    const c = crit[cod] || {};
    out.push({ cod, detalhe, origem, nome: c.nome || cod, porque: c.porque, conferir: c.conferir, peso: c.peso ?? 0, grupo: c.grupo || origem });
  };
  for (const [cod, det] of (linha && linha.sinais) || []) add(cod, det, 'secao');
  for (const [cod, det] of (local && local.sinais) || []) {
    if (cod.startsWith('local_c13_') && linha && linha.c13) continue;
    add(cod, det, 'local');
  }
  for (const [cod, det] of zonaSinais || []) add(cod, det, 'zona');
  const t = local && local.territorio;
  if (t && (t.nivel === 'alto' || t.nivel === 'medio')) add(`territorio_${t.nivel}`, t.motivos.join('; '), 'territorio');
  out.sort((a, b) => b.peso - a.peso);
  return out;
}

function medidor(h, nivel, regras) {
  const niv = regras.niveis || {};
  return h('ol', { class: 'fis-medidor', 'aria-label': 'Escala de atenção, da padrão à máxima' },
    ORDEM.map((k) => h('li', { class: `n-${k}${k === nivel ? ' atual' : ''}`, 'aria-current': k === nivel ? 'true' : null },
      h('span', {}, (niv[k] && niv[k].nome) || k))));
}

function itemSinal(h, s, regras) {
  const grupo = (regras.grupos || {})[s.grupo] || '';
  return h('li', { class: `fis-sinal g-${s.grupo}` },
    h('p', { class: 'fis-tag' }, grupo),
    h('b', {}, s.nome),
    s.detalhe ? h('p', { class: 'fis-det' }, `${s.detalhe}.`) : null,
    s.porque ? h('p', { class: 'fis-porque' }, s.porque) : null,
    s.conferir ? h('p', { class: 'fis-conf' }, h('strong', {}, 'Como fiscalizar'), s.conferir) : null);
}

function itemCap13(h, c13, regras) {
  const [nivel, ids, explicacao] = c13;
  const cap = regras.cap13 || {};
  const crits = cap.criterios || {};
  const nomes = (ids || []).map((id) => (crits[id] ? crits[id].nome : id));
  const conferir = [...new Set((ids || []).map((id) => crits[id] && crits[id].conferir).filter(Boolean))];
  return h('li', { class: 'fis-sinal g-c13' },
    h('p', { class: 'fis-tag' }, (regras.grupos || {}).c13 || 'Capítulo 13'),
    h('b', {}, `Seção sinalizada no capítulo 13, nível ${NOME_C13[nivel] || nivel}`),
    h('p', { class: 'fis-det' }, `${nomes.length === 1 ? 'Critério' : 'Critérios'}: ${nomes.join('; ')}.`),
    explicacao ? h('p', { class: 'fis-porque' }, `Explicação provável: ${explicacao.replace(/\.$/, '')}.`) : null,
    conferir.length ? h('p', { class: 'fis-conf' }, h('strong', {}, 'Como fiscalizar'), maiuscula(`${conferir.join('; ')}.`)) : null);
}

function blocoTerritorio(h, t, regras) {
  let corpo;
  if (!t) corpo = h('p', {}, 'As bases públicas de risco do território não cobrem este local.');
  else if (!t.motivos.length) corpo = h('p', {}, 'Nenhum fator de risco nas bases públicas consultadas: crime organizado com mapeamento público, homicídios, favela, terra indígena ou quilombo, unidade prisional, fronteira, garimpo e distância da sede.');
  else {
    corpo = [
      h('p', {}, h('b', {}, `Risco ${NOME_TERR[t.nivel] || t.nivel}`), ` pela regra do capítulo 13 (${plural(t.pontos, 'ponto', 'pontos')}).`),
      h('ul', { class: 'fis-lista' }, t.motivos.map((m) => h('li', {}, m))),
    ];
  }
  return h('div', { class: 'fis-terr' },
    h('h3', {}, 'O território'),
    corpo,
    h('p', { class: 'fis-nota' }, `Regra de pontos declarada, juízo editorial e não medição; ${regras.territorio_validar || 'validar com a PM e o TRE local'}.`));
}

function blocoPredio(h, ctx, linhasLocal, local, atual) {
  const { uf, zona } = ctx;
  const n = local ? local.niveis || {} : {};
  const niv = ctx.regras.niveis || {};
  const ordem = [...linhasLocal].sort((a, b) => b.pontos - a.pontos || a.secao - b.secao);
  const chips = ordem.slice(0, LIMITE_CHIPS).map((x) =>
    h('li', {}, h('a', {
      class: `fis-chip n-${x.nivel}${atual && x.secao === atual ? ' atual' : ''}`,
      href: `#s=${encodeURIComponent(`${uf}-${zona}-${x.secao}`)}`,
      title: `${(niv[x.nivel] || {}).nome || x.nivel}, ${plural(x.pontos, 'ponto', 'pontos')}`,
      'aria-current': atual && x.secao === atual ? 'true' : null,
    }, `Seção ${x.secao}`, h('small', {}, (niv[x.nivel] || {}).nome || x.nivel))));
  const resumo = ['maxima', 'alta', 'reforcada', 'padrao']
    .filter((k) => n[k])
    .map((k) => `${(niv[k] || {}).nome || k}: ${n[k]}`)
    .join(' · ');
  const total = local ? local.secoes : linhasLocal.length;
  return h('div', { class: 'fis-predio' },
    h('h3', {}, 'Neste prédio'),
    h('p', {}, `${plural(total, 'seção', 'seções')} no local de votação. ${resumo}.`),
    h('ul', { class: 'fis-chips', 'aria-label': 'Seções do local, da que tem mais motivos para a que tem menos' }, chips),
    ordem.length > LIMITE_CHIPS ? h('p', { class: 'fis-nota' }, `E mais ${ordem.length - LIMITE_CHIPS} seções com menos motivos.`) : null,
    h('p', { class: 'fis-nota' }, 'Um fiscal pode cobrir várias seções do mesmo prédio (Lei 9.504/1997, art. 65, § 1º). Com poucos fiscais, comece pelas seções do topo da lista.'));
}

function blocoCta(h, regras) {
  const c = regras.cta || {};
  if (!c.url) return null;
  return h('div', { class: 'fis-cta' },
    h('p', { class: 'fis-cta-t' }, c.titulo || 'Seja fiscal'),
    h('a', { class: 'btn btn-fiscal', href: c.url, target: '_blank', rel: 'noopener' }, `${c.botao || 'Quero ser fiscal'} · ${c.rotulo || c.url}`),
    c.texto ? h('p', { class: 'fis-nota' }, c.texto) : null);
}

function blocoMetodo(h, regras) {
  const crit = Object.entries(regras.criterios || {});
  const cap = regras.cap13 || {};
  const rot = regras.rotulos || {};
  return h('details', { class: 'fis-metodo' },
    h('summary', {}, 'Como a pontuação é feita'),
    regras.regra ? h('p', {}, regras.regra) : null,
    h('div', { class: 'tabela-rolagem', tabindex: '0', role: 'region', 'aria-label': 'Critérios de fiscalização' },
      h('table', { class: 'tabela-fontes fis-tab' },
        h('thead', {}, h('tr', {}, h('th', { scope: 'col' }, 'Critério'), h('th', { scope: 'col' }, 'Regra'), h('th', { scope: 'col', class: 'num' }, 'Pontos'), h('th', { scope: 'col', class: 'num' }, 'Seções no Brasil'))),
        h('tbody', {},
          ['alta', 'media', 'baixa'].map((k) => h('tr', {}, h('td', {}, `Capítulo 13, nível ${NOME_C13[k]}`), h('td', {}, 'seção sinalizada pelos 12 critérios do capítulo 13'),
            h('td', { class: 'num' }, String((cap.pesos || {})[k] ?? '')), h('td', { class: 'num' }, ((cap.secoes_por_nivel || {})[k] ?? 0).toLocaleString('pt-BR')))),
          crit.map(([, c]) => h('tr', {}, h('td', {}, c.nome), h('td', {}, c.regra || ''), h('td', { class: 'num' }, String(c.peso ?? '')), h('td', { class: 'num' }, (c.secoes ?? 0).toLocaleString('pt-BR'))))))),
    h('p', { class: 'fis-nota' }, [rot.atipico, rot.prioridade, rot.resolve].filter(Boolean).join(' ')),
    h('p', { class: 'fis-nota' }, 'Método completo e as 13.045 seções do capítulo 13: ', h('a', { href: 'apuracao_1o_turno_2026.html#fiscais' }, 'dossiê da apuração do 1º turno'), '.'));
}

/**
 * Monta o bloco de fiscalização do resultado.
 * @param {object} ctx { h, buscar, base, local, secao (linha da seção ou null), nomeUF }
 * @returns {Promise<Element|null>}
 */
export async function blocoFiscal(ctx) {
  const { h, buscar, base, local, secao } = ctx;
  const uf = local._uf;
  const zona = Number(local.zona);
  if (!uf || !Number.isFinite(zona)) return null;
  const [regras, arq] = await Promise.all([buscar(`${base}fiscal/regras.json`), buscar(`${base}fiscal/${uf}/${zona}.json`)]);
  if (!regras || !arq) return null;
  const linhas = tabelaDe(arq.secoes);
  const doLocal = linhas.filter((x) => x.local_id === local.local_id);
  const loc = (arq.locais || {})[local.local_id] || null;
  const linha = secao ? linhas.find((x) => Number(x.secao) === Number(secao.secao)) || null : null;
  const niv = regras.niveis || {};
  const c = { ...ctx, uf, zona, regras };
  const logs = await blocoLogs({ h, buscar, uf, zona, secao, local });

  let nivel;
  let pontos = null;
  if (linha) {
    nivel = linha.nivel;
    pontos = linha.pontos;
  } else {
    nivel = doLocal.reduce((m, x) => (PESO_NIVEL[x.nivel] > PESO_NIVEL[m] ? x.nivel : m), 'padrao');
  }
  const info = niv[nivel] || { nome: nivel, frase: '' };
  const sinais = sinaisDe(regras, linha, loc, arq.sinais_zona);
  const titulo = linha ? `A seção ${linha.secao} precisa de fiscal` : 'Este local de votação precisa de fiscal';
  const sub = linha
    ? `Toda seção precisa de fiscal no 2º turno. ${info.frase}`
    : `Toda seção precisa de fiscal no 2º turno. O nível abaixo é o da seção com mais motivos neste prédio; digite a sua seção para ver a dela.`;

  const listaSinais = [];
  if (linha && linha.c13) listaSinais.push(itemCap13(h, linha.c13, regras));
  for (const s of sinais) listaSinais.push(itemSinal(h, s, regras));

  const sempre = Array.isArray(regras.sempre) ? regras.sempre : [];
  const legal = Array.isArray(regras.legal) ? regras.legal : [];

  return h('article', { class: `fiscal entra n-${nivel}`, 'aria-labelledby': 'fis-titulo' },
    h('header', { class: 'fis-cab' },
      h('p', { class: 'kicker' }, `Fiscalização · 2º turno, 25 de outubro · Zona ${zona}`),
      h('h2', { id: 'fis-titulo' }, titulo),
      h('p', { class: 'fis-sub' }, sub),
      h('div', { class: 'fis-nivel' },
        h('p', { class: 'fis-selo' }, info.nome, pontos !== null ? h('small', {}, plural(pontos, 'ponto', 'pontos')) : null),
        medidor(h, nivel, regras)),
      blocoCta(h, regras)),
    h('div', { class: 'fis-corpo' },
      logs,
      h('div', { class: 'fis-motivos' },
        h('h3', {}, linha ? 'Por que esta seção pede atenção' : 'Por que este local pede atenção'),
        listaSinais.length
          ? h('ul', { class: 'fis-sinais' }, listaSinais)
          : h('p', {}, 'Nenhum sinal a mais nos números do boletim, do local, da zona ou do território. Isso não dispensa fiscal: é nas seções tranquilas que ninguém confere nada.')),
      blocoTerritorio(h, loc && loc.territorio, regras),
      doLocal.length ? blocoPredio(h, c, doLocal, loc, linha ? linha.secao : null) : null,
      sempre.length
        ? h('div', { class: 'fis-sempre' }, h('h3', {}, 'O que todo fiscal faz, em qualquer seção'), h('ol', {}, sempre.map((t) => h('li', {}, t))))
        : null,
      legal.length ? h('details', { class: 'fis-metodo' }, h('summary', {}, 'O que a lei garante ao fiscal'), h('ul', { class: 'fis-lista' }, legal.map((t) => h('li', {}, t)))) : null,
      blocoMetodo(h, regras)));
}

/** Números nacionais para a seção fixa "Toda seção precisa de fiscal". */
export async function resumoFiscal(buscar, base) {
  const r = await buscar(`${base}fiscal/regras.json`);
  if (!r || !r.niveis) return null;
  const n = r.niveis;
  const total = r.resumo && r.resumo.secoes;
  return {
    total,
    maxima: n.maxima ? n.maxima.secoes : null,
    alta: n.alta ? n.alta.secoes : null,
    reforcada: n.reforcada ? n.reforcada.secoes : null,
    padrao: n.padrao ? n.padrao.secoes : null,
    cta: r.cta || null,
  };
}
