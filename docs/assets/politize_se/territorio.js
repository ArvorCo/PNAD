/* Contexto público compartilhado pelas duas páginas. Nenhuma inferência individual. */
(function () {
  'use strict';
  const BASE = 'assets/politize_se_mapa/contexto/';
  const cache = new Map();
  const n = (v) => typeof v === 'number' && Number.isFinite(v);
  const fmt = (v, d = 1) => n(v) ? v.toLocaleString('pt-BR', { maximumFractionDigits: d }) : 'Sem dado';
  const reais = (v) => n(v) ? 'R$ ' + fmt(v, 0) : 'Sem dado';
  const perc = (v) => n(v) ? fmt(v) + '%' : 'Sem dado';
  function el(tag, attrs = {}, ...children) {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
    for (const c of children.flat(Infinity)) if (c !== null && c !== undefined) node.append(c instanceof Node ? c : String(c));
    return node;
  }
  function fetchJson(file) {
    if (!cache.has(file)) {
      const p = fetch(BASE + file + '?v=20261028').then((r) => {
        if (!r.ok) throw new Error('contexto indisponível');
        return r.json();
      });
      cache.set(file, p);
      p.catch(() => cache.delete(file));
    }
    return cache.get(file);
  }
  function dados(uf) {
    return fetchJson(uf + '.json').then((d) => {
      if (!d.porLocal) d.porLocal = new Map(d.locais.linhas.map((r) => {
        const l = Object.fromEntries(d.locais.colunas.map((c, i) => [c, r[i]]));
        return [l.local_id, l];
      }));
      return d;
    });
  }
  function barras(items, classe) {
    const valid = items.filter(([, v]) => n(v));
    if (!valid.length) return el('p', { class: 'territorio-vazio' }, 'Perfil não disponível nesta base.');
    const total = valid.reduce((a, [, v]) => a + v, 0);
    return el('div', { class: 'territorio-barras ' + classe },
      el('div', { class: 'territorio-pilha', 'aria-hidden': 'true' }, items.map(([, v], i) =>
        el('i', { class: 't-cor-' + i, style: `flex:${n(v) && total > 0 ? v / total : 0}` }))),
      el('ul', {}, items.map(([label, v], i) => el('li', {},
        el('span', {}, el('i', { class: 't-cor-' + i, 'aria-hidden': 'true' }), label), el('b', {}, perc(v))))));
  }
  function fontes(m, meta) {
    const details = el('details', { class: 'territorio-fontes' }, el('summary', {}, 'Fontes e como ler estes indicadores'));
    details.append(el('p', {}, 'Renda: PNAD Contínua anual 2025, visita 1, pessoas de 16 anos ou mais. Estimativa por UF, escolaridade e situação urbana/rural, a preços de ' + (meta.renda?.mes_precos || 'julho de 2026') + '. A mediana é a estimativa publicada pelo modelo, não uma medição no bairro.'));
    details.append(el('p', {}, 'Escolaridade: cadastro eleitoral do TSE, com a unidade informada na ficha. Homicídios: ' + (m.homicidios_fonte || 'Atlas da Violência / SIM') + '. Taxa e contagem se referem ao município de residência; não são registros na escola.'));
    const links = (meta.fontes || []).filter((f) => /^https:\/\//.test(f.url || ''));
    details.append(el('ul', {}, links.map((f) => el('li', {}, el('a', { href: f.url, target: '_blank', rel: 'noopener' }, f.nome)))));
    details.append(el('a', { href: BASE + 'indice.json', target: '_blank', rel: 'noopener' }, 'Metadados e hashes das bases reutilizadas'));
    return details;
  }
  function render(l, m, meta, compact, localId) {
    const renda = el('section', { class: 'territorio-card territorio-economia' },
      el('p', { class: 'territorio-eyebrow' }, '01 / Economia · estimativa'),
      el('h3', {}, 'Renda do domicílio'),
      el('p', { class: 'territorio-numero' }, reais(l.renda_mediana_brl)),
      el('p', { class: 'territorio-sub' }, 'Mediana estimada · preços de ' + (meta.renda?.mes_precos === '2026-07' ? 'jul/2026' : meta.renda?.mes_precos || 'não informado')),
      barras([['Até 2 salários', l.renda_ate2], ['De 2 a 5 salários', l.renda_de2a5], ['Mais de 5 salários', l.renda_mais5]], 'territorio-renda'),
      el('p', { class: 'territorio-nota' }, '1 salário = ' + reais(meta.renda?.salario_minimo_2026) + '. Renda domiciliar, não por pessoa. O perfil do eleitorado orienta a estimativa; a renda não foi medida neste local.'));
    const quintil = n(m.homicidios_quintil) ? m.homicidios_quintil : null;
    const seguranca = el('section', { class: 'territorio-card territorio-seguranca' },
      el('p', { class: 'territorio-eyebrow' }, '02 / Segurança · município'),
      el('h3', {}, 'Homicídios registrados'),
      el('p', { class: 'territorio-numero' }, fmt(m.homicidios_taxa_100mil, 2), el('small', {}, ' por 100 mil')),
      el('p', { class: 'territorio-sub' }, [n(m.homicidios_n) ? fmt(m.homicidios_n, 0) + ' óbitos' : 'Contagem não disponível', n(m.homicidios_ano) ? fmt(m.homicidios_ano, 0).replace(/\./g, '') : 'Ano não disponível'].join(' · ')),
      el('div', { class: 'territorio-regua', role: 'img', 'aria-label': quintil ? `${quintil}º de cinco grupos de municípios, da menor à maior taxa` : 'Sem posição na distribuição nacional' },
        [1, 2, 3, 4, 5].map((q) => el('span', { class: q === quintil ? 'atual' : '' }, q === quintil ? '●' : ''))),
      el('p', { class: 'territorio-extremos' }, el('span', {}, 'Menores taxas'), el('span', {}, 'Maiores taxas')),
      el('p', { class: 'territorio-nota' }, quintil ? `${quintil}º quintil entre os municípios com dado: cinco grupos de tamanho semelhante, ordenados pela taxa.` : 'Sem taxa ou posição disponível. Ausência de dado não significa zero.'),
      el('p', { class: 'territorio-nota' }, 'Atlas da Violência / SIM. Contexto de todo o município, não risco neste prédio ou nestas seções.'));
    const social = el('section', { class: 'territorio-card territorio-social' },
      el('p', { class: 'territorio-eyebrow' }, '03 / Perfil · cadastro eleitoral'),
      el('h3', {}, 'Escolaridade'),
      barras([['Fundamental incompleto', l.fund_inc], ['Fundamental completo / médio incompleto', l.fund_med], ['Médio completo / superior incompleto', l.med_sup_inc], ['Superior completo', l.superior]], 'territorio-escola'),
      el('p', { class: 'territorio-nota' }, 'Fonte do perfil no município: ' + ({ secao: 'por seção, agregado ao prédio', zona: 'por zona eleitoral (não exclusivo deste prédio)', misto: 'combinação de seções e zonas eleitorais' }[l.perfil_fonte] || 'não disponível') + '. Cadastro TSE, que pode estar desatualizado. Situação do setor censitário do ponto: ' + (l.setor_situacao || 'não disponível') + '.'));
    const content = el('div', { class: 'territorio-conteudo' },
      el('header', { class: 'territorio-cab' },
        el('p', { class: 'territorio-eyebrow' }, 'O lugar além da urna'),
        el('h2', {}, 'Economia e segurança da região'),
        el('p', {}, 'Contexto de ' + (m.municipio || 'este local') + '. As seções deste prédio compartilham este contexto; ele não descreve cada pessoa nem explica sozinho o voto.')),
      el('div', { class: 'territorio-grade' }, renda, seguranca));
    if (compact) {
      content.append(el('details', { class: 'territorio-mais' }, el('summary', {}, 'Ver escolaridade'), el('div', { class: 'territorio-grade' }, social)));
      const [uf, , z] = localId.split('-');
      content.append(el('a', { class: 'territorio-abrir', href: `politizese.html#uf=${uf}&z=${z}&l=${encodeURIComponent(localId)}` }, 'Explorar este contexto no Politize-se ↗'));
    } else content.append(el('div', { class: 'territorio-grade' }, social));
    content.append(compact ? el('details', {class:'territorio-mais'}, el('summary',{},'Outros crimes e índice · estado inteiro'), window.PolitizeCrimes.painel(localId.split('-')[0])) : window.PolitizeCrimes.painel(localId.split('-')[0]));
    content.append(window.PolitizeSeguranca.painel({ uf: localId.split('-')[0], local: localId }), fontes(m, meta));
    return content;
  }
  function painel(localId, { compact = false } = {}) {
    const uf = String(localId || '').split('-')[0];
    const box = el('section', { class: 'territorio' + (compact ? ' territorio-compacto' : ''), 'aria-label': 'Economia e segurança da região', 'aria-busy': 'true' });
    if (uf === 'ZZ') {
      box.removeAttribute('aria-busy');
      box.append(el('h2', {}, 'Contexto territorial'), el('p', {}, 'Exterior: as bases brasileiras de renda e segurança não cobrem este local.'));
      return box;
    }
    const carregar = async () => {
      box.setAttribute('aria-busy', 'true');
      box.replaceChildren(el('p', { role: 'status' }, 'Carregando economia e segurança da região…'));
      try {
        const [d, meta] = await Promise.all([dados(uf), fetchJson('indice.json')]);
        const l = d.porLocal.get(localId) || {};
        const m = d.municipios[localId.split('-')[1]] || {};
        box.replaceChildren(render(l, m, meta, compact, localId));
      } catch {
        const retry = el('button', { type: 'button', class: 'territorio-retry' }, 'Tentar de novo');
        retry.addEventListener('click', carregar);
        box.replaceChildren(el('p', { role: 'status' }, 'O contexto territorial não carregou. Os dados eleitorais continuam disponíveis.'), retry);
      } finally { box.setAttribute('aria-busy', 'false'); }
    };
    carregar();
    return box;
  }
  function resumo(l) {
    return `Renda estimada: ${reais(l.renda_mediana_brl)} · Homicídios no município: ${fmt(l.homicidios_taxa_100mil, 2)} por 100 mil`;
  }
  function atalho(localId) {
    const uf = String(localId || '').split('-')[0];
    if (!localId || uf === 'ZZ') return null;
    const button = el('button', { type: 'button', class: 'territorio-atalho' },
      el('span', {}, 'Economia e segurança da região'), el('b', {}, 'Ver indicadores ↓'));
    button.addEventListener('click', () => {
      const panel = document.querySelector('.territorio');
      if (panel) { panel.scrollIntoView({ behavior: 'smooth', block: 'start' }); panel.setAttribute('tabindex', '-1'); panel.focus({ preventScroll: true }); }
    });
    dados(uf).then((d) => {
      const l = d.porLocal.get(localId) || {}, m = d.municipios[localId.split('-')[1]] || {};
      button.replaceChildren(el('span', {}, el('b', {}, reais(l.renda_mediana_brl)), ' renda domiciliar estimada'),
        el('span', {}, el('b', {}, fmt(m.homicidios_taxa_100mil, 2)), ' homicídios / 100 mil no município'), el('span', {}, 'Ver contexto ↓'));
    }).catch(() => {});
    return button;
  }
  window.PolitizeTerritorio = { painel, atalho, resumo, reais, perc, fmt };
})();
