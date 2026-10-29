/* Horários do 2º turno: seleciona seções e recompõe o prédio, sem alterar sua fonte. */
(function (root) {
  'use strict';
  const CORTE = 62100;
  const presente = (x) => typeof x === 'number' && Number.isFinite(x);
  const grupo = (x, corte = CORTE) => !presente(x) ? 'sem' : x <= corte ? 'ate' : 'apos';
  const segundos = (s) => /^([01]\d|2[0-3]):[0-5]\d$/.test(s || '') ? Number(s.slice(0, 2)) * 3600 + Number(s.slice(3)) * 60 : CORTE;
  const passa = (s, f) => (!f.enc || grupo(s.enc, f.enc_corte ?? CORTE) === f.enc) && (!f.ultimo || grupo(s.ultimo, f.ultimo_corte ?? CORTE) === f.ultimo);
  const hora = (s) => !presente(s) ? 'Sem horário utilizável' : [Math.floor(s / 3600), Math.floor(s / 60) % 60, s % 60].map((x) => String(x).padStart(2, '0')).join(':');
  const motivos = { exterior: 'Exterior: fora do recorte de Brasília', sem_log: 'Sem log processado', relogio: 'Relógio com inconsistência', sem_horario: 'Sem horário no log', contagem: 'Contagem do log difere do boletim', identidade: 'Identidade não confirmada', horario: 'Horário inconsistente', sem_boletim: 'Sem boletim do 2º turno' };
  const soma = (ss, k) => ss.length && ss.every((s) => presente(s[k])) ? ss.reduce((a, s) => a + s[k], 0) : null;
  const max = (ss, k) => { const vs = ss.map((s) => s[k]).filter(presente); return vs.length ? Math.max(...vs) : null; };
  const razao = (a, b) => presente(a) && presente(b) && b > 0 ? 100 * a / b : null;
  const sub = (a, b) => presente(a) && presente(b) ? a - b : null;
  const fatia = (ss, t) => { const f = soma(ss, 'flavio' + t), l = soma(ss, 'lula' + t); return presente(f) && presente(l) ? razao(f, f + l) : null; };
  const comp = (ss, t) => razao(soma(ss, 'comp' + t), soma(ss, 'aptos' + t));

  function agregar(local, secs) {
    if (!secs.length) return null;
    const t2 = secs.filter((s) => s.bu2), par = t2.filter((s) => s.agreg_igual && presente(s.aptos1));
    const modelos = new Map();
    secs.forEach((s) => { if (s.modelo) modelos.set(s.modelo, (modelos.get(s.modelo) || 0) + 1); });
    const ms = [...modelos].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
    const l = { ...local, horario: true, total_secoes: local.n_secoes,
      secoes: secs.map((s) => s.secao).sort((a, b) => a - b), n_secoes: secs.length, n_bu2: t2.length,
      secao_link: Math.min(...secs.map((s) => s.secao)), aptos1: soma(secs, 'aptos1'), aptos2: soma(t2, 'aptos2'),
      comp_pct1: comp(secs, 1), comp_pct2: comp(t2, 2), d_comp_pp: sub(comp(par, 2), comp(par, 1)),
      abst_pct2: sub(100, comp(t2, 2)), bn_pct2: razao(soma(t2, 'bn2'), soma(t2, 'comp2')),
      fatia_f1_par: fatia(par, 1), fatia_f2: fatia(t2, 2), d_fatia_pp: sub(fatia(par, 2), fatia(par, 1)),
      escore_max: max(t2, 'escore'), secoes_sinal: t2.filter((s) => s.escore > 0).length,
      log1_max: max(secs, 'log1_atencao'), log2_max: max(secs, 'log2_atencao'),
      log_subiu: max(secs, 'log2_atencao') === null ? null : secs.filter((s) => presente(s.log1_atencao) && s.log1_atencao <= 1 && s.log2_atencao >= 2).length,
      modelos: ms, modelo: ms.length > 1 ? 'misto' : ms.length ? ms[0][0] : null,
      urnas_trocadas: secs.filter((s) => s.trocada).length, secoes_mudaram: secs.filter((s) => s.mudou).length,
      secoes_anomalas: secs.some((s) => presente(s.anomalo)) ? secs.filter((s) => s.anomalo).length : null };
    // Uma seleção não pode revelar votos de seção pequena por subtração ou soma parcial.
    if (secs.some((s) => s.pequena) || (l.aptos2 ?? l.aptos1 ?? 0) < 30) {
      ['comp_pct1', 'comp_pct2', 'd_comp_pp', 'abst_pct2', 'bn_pct2', 'fatia_f1_par', 'fatia_f2', 'd_fatia_pp'].forEach((k) => { l[k] = null; });
    }
    return l;
  }

  root.HorariosPolitize = { grupo, passa, hora, segundos, agregar };
  root.criarHorariosPolitize = function ({ S, buscar, h, nf0 }) {
    const base = 'assets/politize_se_mapa/horarios/', dados = new Map(), projections = new Map();
    const select = (k) => document.querySelector(k === 'enc' ? '#f-encerramento' : '#f-ultimo');
    const corte = (k) => document.querySelector('#f-' + k + '-corte');
    const ativo = () => Boolean(S.filtro.enc || S.filtro.ultimo);
    const limpar = () => { ['enc', 'ultimo'].forEach((k) => { select(k).value = ''; corte(k).value = '17:15'; }); };
    const lerControles = () => {
      const mudou = ['enc', 'ultimo'].some((k) => (S.filtro[k] || '') !== select(k).value || (S.filtro[k + '_corte'] ?? CORTE) !== segundos(corte(k).value));
      ['enc', 'ultimo'].forEach((k) => {
        S.filtro[k] = select(k).value; S.filtro[k + '_corte'] = segundos(corte(k).value);
        corte(k).value = hora(S.filtro[k + '_corte']).slice(0, 5);
        corte(k).disabled = !['ate', 'apos'].includes(select(k).value);
      });
      if (mudou) projections.clear();
      return mudou;
    };
    const lerHash = (q) => ['enc', 'ultimo'].forEach((k) => {
      select(k).value = ['ate', 'apos', 'sem'].includes(q.get(k)) ? q.get(k) : '';
      corte(k).value = hora(segundos(q.get(k + '_h'))).slice(0, 5);
    });
    const gravarHash = (p) => ['enc', 'ultimo'].forEach((k) => {
      if (!S.filtro[k]) return;
      p.push(k + '=' + S.filtro[k]);
      if (S.filtro[k] !== 'sem' && (S.filtro[k + '_corte'] ?? CORTE) !== CORTE) p.push(k + '_h=' + encodeURIComponent(hora(S.filtro[k + '_corte']).slice(0, 5)));
    });
    async function carregar(ufs, forcar = false) {
      if (!ativo() && !forcar && !['ultimo_voto', 'encerramento'].includes(S.camada)) return;
      await Promise.all(ufs.filter((uf) => !dados.has(uf)).map(async (uf) => {
        const d = await buscar(base + uf + '.json.gz');
        if (d.formato !== 1 || d.uf !== uf) throw new Error('formato');
        // Objetos por seção são materializados só ao selecionar ou abrir o prédio.
        dados.set(uf, d);
      }));
    }
    function secoes(l) {
      const d = dados.get(l.uf);
      return d ? (d.locais[l.id] || []).map((r) => Object.fromEntries(d.colunas.map((c, i) => [c, r[i]]))) : [];
    }
    function filtrar(ls) {
      if (!ativo()) return ls;
      return ls.map((l) => {
        if (!dados.has(l.uf)) return null; // Falha de carga nunca equivale a "sem horário".
        if (!projections.has(l.id)) projections.set(l.id, agregar(l, secoes(l).filter((s) => passa(s, S.filtro))));
        return projections.get(l.id);
      }).filter(Boolean);
    }
    function resumo(ls) {
      const box = document.querySelector('#horario-resumo');
      box.hidden = !ativo();
      if (!ativo()) return;
      const n = ls.reduce((a, l) => a + l.n_secoes, 0);
      box.textContent = nf0.format(n) + ' seções em ' + nf0.format(ls.length) + ' locais selecionados, antes do raio e da busca da lista. O placar soma o dia inteiro dessas seções.';
    }
    function aviso(l) {
      if (!l.horario) return null;
      return h('p', { class: 'ficha-horario' }, l.n_secoes + ' de ' + l.total_secoes + ' seções deste prédio atendem aos horários selecionados. Os valores eleitorais abaixo somam só essas seções; a cidade é a referência completa. O placar soma o dia inteiro.');
    }
    async function paraFicha(l) {
      await carregar([l.uf], true);
      return new Map(secoes(l).map((s) => [s.secao, s]));
    }
    function celula(s, kind) {
      if (!s) return h('small', {}, 'Horário indisponível');
      return h('span', {}, hora(s[kind]), kind === 'ultimo' && s.motivo ? h('small', {}, motivos[s.motivo] || 'Horário não classificável') : null);
    }
    const colunasCsv = ['filtro_encerramento_2t', 'filtro_ultimo_voto_2t', 'secoes_selecionadas', 'encerramento_brt_por_secao', 'ultimo_voto_brt_por_secao', 'corte_encerramento_brt', 'corte_ultimo_voto_brt'];
    function csv(l) {
      const ss = secoes(l).filter((s) => !ativo() || passa(s, S.filtro));
      return [S.filtro.enc || '', S.filtro.ultimo || '', l.secoes.join('|'),
        ss.map((s) => s.secao + ':' + hora(s.enc)).join('|'), ss.map((s) => s.secao + ':' + hora(s.ultimo)).join('|'),
        S.filtro.enc && S.filtro.enc !== 'sem' ? hora(S.filtro.enc_corte ?? CORTE) : '', S.filtro.ultimo && S.filtro.ultimo !== 'sem' ? hora(S.filtro.ultimo_corte ?? CORTE) : ''];
    }
    return { ativo, limpar, lerControles, lerHash, gravarHash, carregar, filtrar, resumo, aviso, paraFicha, celula, colunasCsv, csv, secoes };
  };
})(window);
