// Leitura operacional dos logs, sem pontuação política ou associação a votos.
const BASE = 'assets/logs_urnas_2026/';
const CACHE = new Map();
async function buscarZona(url) {
  if (!CACHE.has(url)) {
    const pedido = (async () => {
      const resposta = await fetch(url, { credentials: 'same-origin' });
      if (!resposta.ok) throw new Error(`HTTP ${resposta.status}`);
      const blob = await resposta.blob();
      const inicio = new Uint8Array(await blob.slice(0, 2).arrayBuffer());
      if (inicio[0] !== 31 || inicio[1] !== 139) return JSON.parse(await blob.text());
      if (!globalThis.DecompressionStream) throw new Error('navegador-sem-gzip');
      return new Response(blob.stream().pipeThrough(new DecompressionStream('gzip'))).json();
    })();
    CACHE.set(url, pedido);
    pedido.catch(() => CACHE.delete(url));
  }
  return CACHE.get(url);
}
const numero = (n, casas = 1) => n == null ? 'não disponível' : Number(n).toLocaleString('pt-BR', { maximumFractionDigits: casas });
const QUALIDADE = {
  contagem_nao_reconciliada: 'contagem não reconciliada com o BU',
  sequencia_temporal_inconsistente: 'sequência temporal inconsistente',
  zeresima_anterior_nao_localizada: 'zerésima anterior não localizada no pacote',
  encerramento_posterior_nao_localizado: 'encerramento posterior não localizado',
  linhas_malformadas: 'linhas que o leitor não reconheceu',
  fase_ou_pleito_incompativel: 'fase ou pleito incompatível',
  menos_de_30_ciclos: 'menos de 30 ciclos completos válidos',
  menos_de_30_ciclos_mesmos_cargos: 'menos de 30 ciclos com a mesma quantidade de cargos',
  modelo_indeterminado_misto_ou_divergente: 'modelo indeterminado, múltiplos modelos ou divergência entre log e BU',
};

export async function blocoLogs({ h, buscar, uf, zona, secao, local }) {
  const cab = h('h3', {}, 'O que o log desta seção registra');
  const nota = h('p', { class: 'fis-nota' }, 'Os agregados exibidos não expõem identificadores de eleitores ou opções de voto e não acrescentam pontos à classificação histórica. ',
    h('a', { href: 'logs_urnas_2026.html' }, 'Cobertura, regras e limites'));
  if (!secao) return h('section', { class: 'fis-logs' }, cab, h('p', {}, 'Escolha uma seção deste local para consultar seus tempos e ocorrências.'), nota);
  let indice, dados;
  try {
    indice = await buscar(`${BASE}indice.json`);
    if (!indice || !(indice.zonas[uf] || []).includes(zona)) return h('section', { class: 'fis-logs' }, cab, h('p', {}, 'Esta zona ainda não tem logs analisados nesta publicação. Ausência de análise não significa ausência de ocorrência.'), nota);
    dados = await buscarZona(`${BASE}zona/${uf}/${zona}.json.gz`);
  } catch (erro) {
    return h('section', { class: 'fis-logs' }, cab, h('p', {}, erro.message === 'navegador-sem-gzip' ? 'Este navegador não abre os dados compactados. Use uma versão atual ou consulte a planilha.' : 'Não foi possível carregar a análise do log agora. Tente novamente.', ' ', h('a', { href: `${BASE}secoes.csv.gz` }, 'Baixar a planilha de seções')), nota);
  }
  const mun = String(local.local_id || '').split('-')[1];
  const row = dados && dados.linhas.map((ln) => Object.fromEntries(dados.colunas.map((c, i) => [c, ln[i]])))
    .find((r) => Number(r.secao) === Number(secao.secao) && r.mun === mun);
  if (!row) {
    const ausencia = (dados.indisponiveis || []).find((r) => r.secao === Number(secao.secao) && r.mun === mun);
    const motivo = ausencia && indice.situacoes[ausencia.motivo];
    return h('section', { class: 'fis-logs' }, cab, h('p', {}, motivo ? `${motivo.nome}. A seção não recebeu zero ocorrências.` : 'Não há log analisado para esta seção no pacote publicado. O registro pode estar ausente, pendente de leitura ou exigir conferência.'), nota);
  }
  const metrica = (nome, valor, detalhe) => h('div', {}, h('dt', {}, nome), h('dd', {}, valor), h('small', {}, detalhe));
  const bioIndisponivel = row.biometria_status === 'ausente_bu' ? 'não consta no BU' : 'não reconciliada';
  const taxa = (v) => !row.elegivel_bio ? bioIndisponivel : v == null ? 'sem denominador' : `${numero(v)}%`;
  const motivos = (row.sinais || []).map((cod) => {
    const c = indice.criterios[cod];
    return h('li', {}, h('strong', {}, c.nome), h('p', {}, c.regra), h('p', { class: 'fis-nota' }, c.limite), h('p', {}, h('b', {}, 'Conferir: '), c.conferir));
  });
  return h('section', { class: 'fis-logs', 'aria-label': 'Análise do log da seção' }, cab,
    h('p', {}, `${numero(row.comparecimento, 0)} comparecimentos no BU; ${numero(row.computados, 0)} eventos computados e ${numero(row.ciclos_reconstruidos, 0)} ciclos reconstruídos no log. Tempos da mesma seção, em segundos; o relógio da urna não informa tempo de fila.`),
    (row.motivos_tempo || []).length ? h('p', { class: 'fis-nota' }, 'Durações fora da comparação: ', row.motivos_tempo.map((c) => QUALIDADE[c] || c).join('; '), '.') : null,
    h('dl', { class: 'log-metricas' },
      metrica('Votação: média', row.elegivel_tempo ? `${numero(row.voto_media)} s` : 'fora da comparação', `${numero(row.n_tempo, 0)} ciclos completos com ${row.cargos} confirmações de cargo; suspensões parciais ficam fora.${row.elegivel_tempo && row.voto_p90 != null ? ` Cerca de 90% destes ciclos duraram até ${numero(row.voto_p90)} s.` : ''}`),
      metrica('Votação: mediana', row.elegivel_tempo ? `${numero(row.voto_mediana)} s` : 'fora da comparação', row.referencia_voto == null ? 'Referência comparável insuficiente.' : `Referência: ${numero(row.referencia_voto)} s em ${numero(row.pares_tempo, 0)} seções da mesma UF, modelo e número de cargos.`),
      metrica('Habilitação: mediana', row.elegivel_tempo && row.n_habilitacao >= 30 ? `${numero(row.habilitacao_mediana)} s` : 'fora da comparação', `${numero(row.n_habilitacao, 0)} etapas da digitação do identificador à liberação para votar.${row.referencia_habilitacao != null ? ` Referência: ${numero(row.referencia_habilitacao)} s em ${numero(row.pares_habilitacao, 0)} seções comparáveis.` : ''}`),
      metrica('Habilitação biográfica', taxa(row.biografica_pct), row.referencia_biografica == null ? 'Entre reconhecidos pela digital e liberados biograficamente; sem referência local suficiente.' : `Referência local: ${numero(row.referencia_biografica)}% em ${numero(row.pares_biometria, 0)} seções. Denominador: biométricas + biográficas.`),
      metrica('Sem biometria', taxa(row.sem_biometria_pct), `Parcela do comparecimento na categoria distinta do BU. Não é a taxa de falha de reconhecimento.${row.referencia_sem_biometria != null ? ` Referência local: ${numero(row.referencia_sem_biometria)}% em ${numero(row.pares_sem_biometria, 0)} seções.` : ' Referência local insuficiente.'}`),
      metrica('Ocorrências', `${numero(row.suspensoes, 0)} suspensões`, `${numero(row.reinicios, 0)} reinícios durante a votação; ${numero(row.erros, 0)} eventos ERRO/FATAL no dia.`)),
    row.erros ? h('p', {}, 'Erros por categoria: ', Object.entries(row.erros_categoria).map(([k, n]) => `${k}: ${n}`).join('; '), '. ', row.erros_na_janela_votacao == null ? 'A sequência não permite delimitar com segurança a janela de votação.' : `${row.erros_na_janela_votacao} entre a primeira habilitação reconstruída e o último cômputo; os demais ficaram fora dessa janela.`) : null,
    row.assinatura_sucesso_posterior || row.assinatura_sem_sucesso_localizado || row.assinatura_ordem_incerta ? h('p', {}, `Verificação de assinatura: ${row.assinatura_sucesso_posterior} erro(s) seguido(s) de SUCESSO no mesmo arquivo e urna; ${row.assinatura_sem_sucesso_localizado} sem sucesso posterior localizado; ${row.assinatura_ordem_incerta} com ordem temporal incerta. É o registro do sistema, não validação criptográfica independente.`) : null,
    row.recuo_max_s ? h('p', {}, `Maior recuo entre carimbos no mesmo arquivo e urna: ${numero(row.recuo_max_s, 0)} segundos. Isso pode decorrer de ordenação de escrita ou ajuste de relógio; os tempos foram excluídos por cautela.`) : null,
    row.mensagens_criticas_alteradas || row.linhas_invalidas ? h('p', {}, `Qualidade do texto: ${row.linhas_invalidas} linha(s) com estrutura inválida; ${row.mensagens_criticas_alteradas} mensagem(ns) crítica(s) com caracteres inesperados. O leitor preserva as diferenças e não reconstrói o evento por aproximação.`) : null,
    row.identificadores_excluidos ? h('p', {}, `Identidade dos registros: ${row.identificadores_excluidos} identificador(es) de urna excluído(s) por fase incompatível, outra seção ou metadados insuficientes. Os eventos desses identificadores não entram nas contagens acima.`) : null,
    motivos.length ? h('ul', { class: 'log-ocorrencias' }, motivos) : h('p', {}, `Nenhum dos ${Object.keys(indice.criterios).length} diagnósticos disparou nas regras avaliáveis desta seção. Isso não certifica o funcionamento da urna nem cobre ocorrências fora do log.`),
    h('details', {}, h('summary', {}, 'Original e integridade do arquivo'), h('p', {}, h('a', { href: row.url, target: '_blank', rel: 'noopener' }, 'Baixar o log oficial correspondente ao BU')), h('p', { class: 'log-hash' }, 'SHA-256: ', h('code', {}, row.sha256)), row.hash_anterior_confere === null ? h('p', {}, 'A coleta anterior não tinha hash deste log. O SHA-256 acima identifica o arquivo recuperado nesta rodada, sem comparação anterior.') : null,
      row.bu_suplementar ? h('div', {}, h('p', {}, 'Esta seção retornava 404 na coleta antiga. O BU foi recuperado nesta rodada, no mesmo hash de transmissão do log, e preservado como fonte suplementar. ', h('a', { href: row.bu_suplementar.url, target: '_blank', rel: 'noopener' }, 'BU oficial utilizado')), h('p', { class: 'log-hash' }, 'SHA-256 do BU: ', h('code', {}, row.bu_suplementar.sha256))) : null),
    nota);
}
