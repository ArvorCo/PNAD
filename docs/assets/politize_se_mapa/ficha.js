/* Ficha do prédio e tabela de seções do mapa. */
window.criarFichaPolitize = function ({ S, h, caixa, distanciaKm, coordOk, cepFmt, plural, nf0, nf1, km, pct, pp, vazio, buscar, SECOES, tabela, copiar, H, T }) {
  function linhaCmp(rotulo, a, b) {
    return h('tr', {}, h('td', {}, rotulo), h('td', {}, vazio(a) ? 'sem dado' : a), h('td', {}, vazio(b) ? 'sem dado' : b));
  }

  function linkPolitize(l, secao) {
    return 'politizese.html#uf=' + l.uf + '&z=' + l.zona + '&s=' + secao;
  }

  function ficha(l) {
    const tematica = Boolean(S.meta.camadas[S.camada]?.grupo);
    const contexto = window.PolitizeTerritorio.painel(l.id, { compact: true });
    const m = S.muni.get(l.uf + '-' + l.mun) || {};
    const dist = S.centro && coordOk(l) ? distanciaKm(S.centro.lat, S.centro.lon, l.lat, l.lon) : null;
    const gmaps = coordOk(l) ? 'https://www.google.com/maps/search/?api=1&query=' + l.lat + ',' + l.lon : null;
    const params = ['uf=' + l.uf, 'l=' + encodeURIComponent(l.id), 'camada=' + S.camada]; H.gravarHash(params);
    const link = location.origin + location.pathname + '#' + params.join('&');
    S.secaoSel = l.secao_link;
    const selos = [
      l.n_bu2 ? h('span', { class: 'selo ok' }, '2º turno lido em ' + l.n_bu2 + ' de ' + plural(l.n_secoes, 'seção', 'seções')) : h('span', { class: 'selo alerta' }, 'Ainda sem boletim do 2º turno'),
      l.secoes_sinal ? h('span', { class: 'selo alerta' }, plural(l.secoes_sinal, 'seção com sinal', 'seções com sinal')) : null,
      l.modelos && l.modelos.length ? h('span', { class: 'selo' }, 'Urna ' + textoModelo(l)) : null,
      !vazio(l.log2_max) ? h('span', { class: 'selo' + (l.log2_max >= 2 ? ' alerta' : '') }, 'Registro 2º turno: ' + nomeNivel(l.log2_max)) : null,
      l.log_subiu ? h('span', { class: 'selo alerta' }, plural(l.log_subiu, 'seção subiu de nível', 'seções subiram de nível')) : null,
      l.urnas_trocadas ? h('span', { class: 'selo' }, plural(l.urnas_trocadas, 'urna trocada', 'urnas trocadas')) : null,
      l.secoes_mudaram ? h('span', { class: 'selo' }, plural(l.secoes_mudaram, 'seção mudou de endereço', 'seções mudaram de endereço')) : null,
      l.secoes_anomalas ? h('span', { class: 'selo alerta' }, plural(l.secoes_anomalas, 'seção no grupo atípico', 'seções no grupo atípico')) : null,
    ];
    return h('div', { class: 'ficha' },
      h('div', { class: 'ficha-selos' }, selos), H.aviso(l),
      h('h3', {}, caixa(l.nome) || 'Local de votação'),
      h('p', { class: 'ficha-end' }, [caixa(l.endereco), caixa(l.bairro), caixa(l.municipio) + (l.uf === 'ZZ' ? ' (exterior)' : '/' + l.uf), l.cep ? 'CEP ' + cepFmt(l.cep) : ''].filter(Boolean).join(' · ')),
      h('p', { class: 'ficha-meta' }, 'Zona ' + l.zona + ' · ' + plural(l.n_secoes, 'seção', 'seções') + (l.aptos2 || l.aptos1 ? ' · ' + nf0.format(l.aptos2 || l.aptos1) + ' eleitores' : '') + (dist !== null ? ' · ' + km(dist) + ' em linha reta ' + S.centro.de : '')),
      l.aprox ? h('p', { class: 'ficha-meta' }, 'Ponto aproximado: é a cidade do consulado, não o prédio.') : null,
      T.ficha(l),
      h('details', {class:'ficha-distribuicao',open:['mulheres','jovens','idosos'].includes(S.camada)}, h('summary',{},'Idade e sexo · pirâmide etária'),
        window.PolitizePerfil.painel({uf:l.uf,local:l.id,escolherSecao:true,...(l.horario?{secoes:l.secoes}:{})},l.horario?'Seções selecionadas deste local':caixa(l.nome))),
      h('p', { class: 'placar-contagens' }, h('span', { class: 'tf' }, 'Flávio: ' + (vazio(l.flavio2) ? 'sem contagem publicável' : nf0.format(l.flavio2) + ' votos')), ' · ', h('span', { class: 'tl' }, 'Lula: ' + (vazio(l.lula2) ? 'sem contagem publicável' : nf0.format(l.lula2) + ' votos')), ' · 2º turno'),
      tematica ? contexto : h('p', { class: 'ficha-contexto-resumo' }, window.PolitizeTerritorio.resumo(l)),
      h('table', { class: 'cmp' },
        h('thead', {}, h('tr', {}, h('th', { scope: 'col' }, ''), h('th', { scope: 'col' }, l.horario ? 'Seções selecionadas' : 'Este prédio'), h('th', { scope: 'col' }, 'A cidade'))),
        h('tbody', {},
          linhaCmp('Flávio entre os dois, 2º turno', pct(l.fatia_f2), pct(m.fatia_f2)),
          linhaCmp('Lula entre os dois, 2º turno', pct(vazio(l.fatia_f2) ? null : 100 - l.fatia_f2), pct(vazio(m.fatia_f2) ? null : 100 - m.fatia_f2)),
          linhaCmp('Flávio entre os dois, 1º turno (mesmas seções)', pct(l.fatia_f1_par), pct(m.fatia_f1_par)),
          linhaCmp('Lula entre os dois, 1º turno (mesmas seções)', pct(vazio(l.fatia_f1_par) ? null : 100 - l.fatia_f1_par), pct(vazio(m.fatia_f1_par) ? null : 100 - m.fatia_f1_par)),
          linhaCmp('Mudança Flávio', pp(l.d_fatia_pp), pp(m.d_fatia_pp)),
          linhaCmp('Mudança Lula', pp(vazio(l.d_fatia_pp) ? null : -l.d_fatia_pp), pp(vazio(m.d_fatia_pp) ? null : -m.d_fatia_pp)),
          linhaCmp('Comparecimento, 2º turno', pct(l.comp_pct2), pct(m.comp_pct2)),
          linhaCmp('Mudança do comparecimento', pp(l.d_comp_pp), pp(m.d_comp_pp)),
          linhaCmp('Abstenção, 2º turno', pct(l.abst_pct2), pct(m.abst_pct2)),
          linhaCmp('Seções com sinal', nf0.format(l.secoes_sinal || 0), nf0.format(m.secoes_sinal || 0)),
          linhaCmp('Seções no grupo atípico (estatística)', vazio(l.secoes_anomalas) ? null : nf0.format(l.secoes_anomalas), vazio(m.secoes_anomalas) ? null : nf0.format(m.secoes_anomalas)))),
      h('p', { class: 'ficha-meta' }, 'Flávio entre os dois: parcela de Flávio nos votos dados a Flávio e a Lula. A coluna da cidade soma só as seções com boletim do 2º turno lido. Grupo atípico: mistura estatística sobre as frações do eleitorado nos dois turnos; pede explicação, não prova nada.'),
      tematica ? null : contexto,
      blocoChuva(l),

      h('nav', {class:'visoes-nav','aria-label':'Explorar zona e município'}, h('a',{href:`politizese.html#uf=${l.uf}&z=${l.zona}&visao=zona`},'Ver a zona inteira'),h('a',{href:`politizese.html#uf=${l.uf}&mun=${l.mun}&visao=municipio`},'Ver o município inteiro')),
      h('div', { class: 'ficha-secoes' }, h('p', { class: 'ficha-meta' }, 'Carregando as seções do prédio…')),
      h('details', {class:'ficha-distribuicao'}, h('summary',{},'Ver distribuição de votos por hora'),
        window.PolitizeMovimento.painel({uf:l.uf,local:l.id,escolherSecao:true,...(l.horario ? {secoes:l.secoes} : {})}, l.horario ? 'Seções selecionadas deste local' : caixa(l.nome))),
      h('a', { class: 'btn-politize', href: linkPolitize(l, l.secao_link), 'data-politize': '1' }, 'Entenda esta seção no Politize-se (seção ' + l.secao_link + ')'),
      h('p', { class: 'ficha-rotulo' }, 'Sinal pede explicação, não prova irregularidade. Leitura agregada por seção: o voto é secreto e nenhum número descreve uma pessoa.'),
      h('p', { class: 'ficha-links' },
        gmaps ? h('a', { href: gmaps, target: '_blank', rel: 'noopener' }, 'Como chegar (Google Maps)') : null, gmaps ? ' · ' : null,
        h('a', { href: 'politizese.html#uf=' + l.uf + '&z=' + l.zona + '&l=' + encodeURIComponent(l.id) }, 'Este prédio no Politize-se'), ' · ',
        h('a', { href: link, onclick: (ev) => { ev.preventDefault(); copiar(link, ev.target); } }, 'Copiar link do prédio')));
  }

  // Rótulo da fonte da chuva de 25/10: estação a X km ou modelo provisório.
  function fonteChuva(fonte, l) {
    const rede = { cemaden: 'CEMADEN', inmet: 'INMET', ambos: 'INMET/CEMADEN' }[fonte];
    if (rede) return 'chuva medida em ' + (l.chuva2_n === 1 ? 'estação ' : 'estações ') + rede + ' a ' + km(l.chuva2_dist_km);
    if (fonte === 'era5') return 'reanálise climática';
    if (fonte === 'ifs_provisorio') return 'modelo, provisório';
    return 'sem dado';
  }

  function blocoChuva(l) {
    if (vazio(l.chuva2_mm) && vazio(l.chuva2_vot_mm)) return null;
    const mm = (v) => (vazio(v) ? 'sem dado' : nf1.format(v) + ' mm');
    const forte = typeof l.chuva2_mm === 'number' && l.chuva2_mm >= (S.meta.chuva_forte_mm || 20);
    return h('div', { class: 'ficha-chuva' },
      h('p', {}, h('b', {}, 'No dia do 2º turno: '), mm(l.chuva2_mm) + ' de chuva em 25/10 (' + fonteChuva(l.chuva2_fonte, l) + '); ' +
        mm(l.chuva2_vot_mm) + ' das 7h às 18h (' + fonteChuva(l.chuva2_fonte_vot, l) + ').' + (forte ? ' Chuva forte no dia.' : '')),
      h('p', { class: 'ficha-meta' }, 'Pluviômetro a até 50 km é estimativa para a área, não medição no prédio. Chuva não prova efeito no comparecimento.'));
  }

  // Modelo predominante (o de mais seções) e texto curto do prédio, com a contagem quando é misto.
  const predominante = (l) => (l.modelos && l.modelos.length ? l.modelos[0][0] : '');
  function textoModelo(l) {
    if (!l.modelos || !l.modelos.length) return '';
    if (l.modelos.length === 1) return l.modelos[0][0];
    return 'Misto: ' + l.modelos.map((m) => m[0] + ' em ' + plural(m[1], 'seção', 'seções')).join(', ');
  }

  const nomeNivel = (n) => ((S.meta.camadas.log2 || {}).nomes || {})[String(n)] || String(n);

  // Registro da urna da seção: nível 1º → 2º turno, famílias de ocorrência e reinícios na votação.
  function celulaLog(s) {
    const n1 = s.log1_atencao, n2 = s.log2_atencao;
    if (vazio(n1) && vazio(n2)) return h('small', {}, 'Sem registro lido');
    const fam = S.meta.catalogos.log_familias || {};
    const sinais = s.log2_sinais || [];
    const chaves = Array.isArray(s.log2_familias) ? s.log2_familias : Object.keys(fam).filter((f) => fam[f].criterios.some((c) => sinais.indexOf(c) >= 0));
    const familias = chaves.map((f) => (fam[f] || {}).nome || f);
    // Reinícios na votação: [minuto em Brasília, votos antes, votos depois].
    const rein = Array.isArray(s.log2_reinicios) ? s.log2_reinicios : [];
    const hora = (m) => (typeof m === 'number' ? Math.floor(m / 60) + 'h' + String(m % 60).padStart(2, '0') : null);
    const horas = rein.map((r) => hora(r[0])).filter(Boolean);
    const bateria = { simultanea: 'bateria na votação junto com outras urnas da cidade', isolada: 'bateria na votação só nesta urna', votacao: 'bateria durante a votação' }[s.log2_bateria];
    return [h('span', {}, (vazio(n1) ? 'sem registro' : nomeNivel(n1)) + ' → ' + (vazio(n2) ? 'ainda não lido' : nomeNivel(n2))),
      familias.length ? h('small', {}, familias.join('; ')) : null,
      rein.length ? h('small', {}, plural(rein.length, 'reinício na votação', 'reinícios na votação') + (horas.length ? ' (' + horas.join(', ') + ')' : '')) : null,
      bateria ? h('small', {}, bateria) : null];
  }

  // Urna da seção nos dois turnos: o modelo de cada um e se é a mesma urna.
  function celulaUrna(s) {
    const mesma = s.urna_situacao === 'mesma' || s.urna_situacao === 'mesma_recarga';
    const frase = !s.bu2 ? '' : mesma ? 'mesma urna nos dois turnos' : s.urna_situacao && s.urna_situacao !== 'sem_1t' ? 'urna trocada' : '';
    const m1 = s.modelo1 || 'sem dado', m2 = s.bu2 ? s.modelo2 || 'sem dado' : '…';
    return [m1 === m2 ? m1 + ' nos dois turnos' : m1 + ' → ' + m2, frase ? h('small', {}, frase) : null];
  }

  function nomeSinal(k) {
    const t = (S.meta.catalogos.sinais || {})[k] || k;
    return t.charAt(0).toUpperCase() + t.slice(1);
  }

  function selecionarSecao(el, l, secao) {
    S.secaoSel = secao;
    el.querySelectorAll('.secoes-tab tr[data-secao]').forEach((tr) => tr.classList.toggle('sel', Number(tr.dataset.secao) === secao));
    el.querySelectorAll('.secoes-tab tr[data-secao] button').forEach((b) => b.setAttribute('aria-pressed', String(Number(b.closest('tr').dataset.secao) === secao)));
    const btn = el.querySelector('[data-politize]');
    if (btn) { btn.href = linkPolitize(l, secao); btn.textContent = 'Entenda esta seção no Politize-se (seção ' + secao + ')'; }
  }

  // As seções do prédio vêm do arquivo da zona do Politize-se, 1º e 2º turno lado a lado.
  async function carregarSecoes(l, el) {
    const caixaSec = el && el.querySelector('.ficha-secoes');
    if (!caixaSec) return;
    try {
      const z = await buscar(SECOES + l.uf + '/' + l.zona + '.json.gz');
      const li = (z.locais.linhas || []).findIndex((r) => r[z.locais.colunas.indexOf('local_id')] === l.id);
      const tempos = await H.paraFicha(l).catch(() => new Map());
      const secs = tabela(z.secoes).filter((s) => s.li === li && (!l.horario || l.secoes.includes(s.secao))).sort((a, b) => a.secao - b.secao);
      if (li < 0 || !secs.length) { caixaSec.replaceChildren(h('p', { class: 'ficha-meta' }, 'As seções deste prédio não estão no arquivo da zona.')); return; }
      const expl = S.meta.catalogos.explicacoes || {};
      const ida = (a, b, f) => (vazio(a) && vazio(b) ? 'sem dado' : (vazio(a) ? '…' : f(a)) + ' → ' + (vazio(b) ? '…' : f(b)));
      const voto = (s, k) => {
        const share = (v) => vazio(v) ? null : k === 'flavio' ? v : 100 - v;
        const delta = vazio(s.d_fatia_pp) ? null : k === 'flavio' ? s.d_fatia_pp : -s.d_fatia_pp;
        return h('td', { class: 'voto-candidato ' + (k === 'flavio' ? 'tf' : 'tl') }, h('b', {}, ida(share(s.fatia_f1), s.bu2 ? share(s.fatia_f2) : null, pct)), h('small', {}, ida(s[k + '1'], s.bu2 ? s[k + '2'] : null, (n) => nf0.format(n)) + ' votos'), h('small', {}, vazio(delta) ? 'Sem variação comparável' : 'Δ ' + pp(delta)));
      };
      const linhas = secs.map((s) => {
        const pequena = Boolean(s.pequena);
        const sinais = (s.sinais || []).map(nomeSinal);
        const exps = (s.explicacoes || []).map((k) => expl[k]).filter(Boolean);
        return h('tr', { 'data-secao': String(s.secao), class: s.secao === S.secaoSel ? 'sel' : null },
          h('td', {}, h('button', { type: 'button', 'aria-pressed': String(s.secao === S.secaoSel), 'aria-label': 'Escolher a seção ' + s.secao, onclick: () => selecionarSecao(el, l, s.secao) }, String(s.secao))),
          pequena ? h('td', { colspan: '2', class: 'txt' }, h('small', {}, 'Menos de 30 eleitores: voto e comparecimento não publicados.')) : [voto(s, 'flavio'), voto(s, 'lula')],
          h('td', { class: 'txt' }, celulaUrna(s)),
          h('td', { class: 'hora' }, H.celula(tempos.get(s.secao), 'enc')),
          h('td', { class: 'hora' }, H.celula(tempos.get(s.secao), 'ultimo')),
          pequena ? h('td', { colspan: '2' }, 'Não publicado')
            : [h('td', {}, ida(s.comp_pct1, s.bu2 ? s.comp_pct2 : null, pct)), h('td', {}, ida(s.sem_bio_pct1, s.bu2 ? s.sem_bio_pct2 : null, pct))],
          h('td', { class: 'txt' }, celulaLog(s)),
          h('td', { class: 'txt' }, !s.bu2 ? h('small', {}, 'Ainda sem boletim do 2º turno') : [sinais.length
            ? [h('b', {}, plural(sinais.length, 'sinal', 'sinais')), h('ul', { class: 'sinal-lista' }, sinais.map((t) => h('li', {}, t))), exps.length ? h('small', {}, 'Explicação provável: ' + exps.join('; ') + '.') : null]
            : h('small', {}, 'Nenhum sinal'), s.ml_anomalo ? h('small', {}, 'Grupo atípico pela estatística dos dois turnos.') : null]));
      });
      caixaSec.replaceChildren(
        h('p', { class: 'ficha-meta' }, 'Flávio e Lula lado a lado: votos e percentuais do 1º → 2º turno, mais a mudança em pontos percentuais. Os percentuais consideram só os votos entre os dois; no 1º turno excluem as demais candidaturas. Toque na seção para explorá-la.'),
        h('div', { class: 'secoes-rolagem', tabindex: '0', role: 'region', 'aria-label': 'Seções do prédio' },
          h('table', { class: 'secoes-tab' },
            h('thead', {}, h('tr', {}, h('th', { scope: 'col' }, 'Seção'), h('th', { scope: 'col', class: 'tf' }, 'Flávio · 1º → 2º'), h('th', { scope: 'col', class: 'tl' }, 'Lula · 1º → 2º'), h('th', { scope: 'col', class: 'txt' }, 'Urna'), h('th', { scope: 'col' }, 'Encerramento 2º (Brasília)'), h('th', { scope: 'col' }, 'Último voto 2º (Brasília)'), h('th', { scope: 'col' }, 'Comparecimento'), h('th', { scope: 'col' }, 'Sem digital'), h('th', { scope: 'col', class: 'txt' }, 'Registro da urna'), h('th', { scope: 'col', class: 'txt' }, 'Sinais no 2º turno'))),
            h('tbody', {}, linhas))));
    } catch (e) {
      caixaSec.replaceChildren(h('p', { class: 'ficha-meta' }, e && e.message === 'navegador sem gzip' ? 'Este navegador não abre o arquivo das seções; use o botão abaixo para ver a seção no Politize-se.' : 'As seções não carregaram agora; o botão abaixo abre a seção no Politize-se.'));
    }
  }


return { ficha, carregarSecoes, textoModelo, linkPolitize, nomeNivel, predominante };
};
