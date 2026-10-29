/* Lentes documentais: presença municipal e cartografia territorial, separadas. */
window.criarSegurancaMapa = function ({ S, COR, h }) {
  const api = window.PolitizeSeguranca;
  const nomes = { crime: 'Presença de facções no município', controle: 'Controle territorial · RJ · 2024', influencia: 'Influência territorial · RJ · 2024' };
  let d, erro, overlay, tipoOverlay;
  const ativo = () => Object.hasOwn(nomes, S.camada);
  const campo = () => 'seg_' + S.camada;
  const sem = () => S.camada === 'crime' ? 'Sem documentação nesta base' : 'Sem cobertura territorial';
  const texto = (l) => l[campo()] ? api.rotulo(l[campo()]) : sem();
  function aplicar(l) {
    for (const k of Object.keys(nomes)) l['seg_' + k] = d ? api.status(d, l.id, k) : null;
    return l;
  }
  async function instalar() {
    try { d = await api.dados(); } catch (e) { erro = e; }
    for (const [k, nome] of Object.entries(nomes)) {
      COR[k] = k === 'crime' ? { documentado: '#875b2c', misto: '#68736b' } : { ...(d?.cartografia[k]?.cores || {}), 'Sem marcação': '#e3dfd3', misto: '#68736b' };
      S.meta.camadas[k] = { nome, campo: 'seg_' + k, tipo: 'categoria', grupo: 'Economia e segurança', precisa_bu2: false };
    }
  }
  function grupo(ls) {
    const valores = new Set(ls.map((l) => l[campo()] ?? null));
    return valores.size === 1 ? [...valores][0] : 'misto';
  }
  function atualizarOverlay() {
    const tipo = ['controle', 'influencia'].includes(S.camada) ? S.camada : null;
    if (tipo === tipoOverlay) return;
    if (overlay) { overlay.remove(); overlay = null; }
    tipoOverlay = tipo;
    if (!tipo || !d || !S.mapa) return;
    const c = d.cartografia[tipo];
    overlay = L.imageOverlay(api.BASE + c.arquivo, c.bounds, {
      opacity: .48, interactive: false,
      attribution: 'GENI/UFF e Fogo Cruzado · território 2024',
    }).addTo(S.mapa);
    overlay.on('error', () => { document.querySelector('#mapa-escala').append(h('p', { role: 'alert' }, 'A imagem territorial não carregou; consulte o mapa original no link da legenda.')); });
  }
  function escala() {
    return h('div', { class: 'seg-legenda' }, Object.entries(COR[S.camada]).map(([s, cor]) => h('span', {}, h('i', { style: 'background:' + cor }), s === 'misto' ? 'Grupo de pontos com categorias distintas' : api.rotulo(s))), h('span', {}, h('i', { style: 'background:' + COR.semDado }), sem()));
  }
  function legenda() {
    atualizarOverlay();
    if (!ativo()) return false;
    const k = S.camada;
    document.querySelector('#mapa-escala').replaceChildren(h('b', {}, nomes[k]), escala());
    const municipal = k === 'crime';
    const explica = municipal
      ? 'Os pontos destacados estão em municípios citados nas fontes; não são áreas delimitadas de domínio. FBSP 2025 e registros documentais datados, reutilizados do mapa de fiscais. A cor cinza indica falta de documentação, não ausência de grupos.'
      : 'A imagem original mostra ' + (k === 'controle' ? 'controle' : 'influência') + ' em 2024, publicado em dezembro de 2025 pelo GENI/UFF e Fogo Cruzado. Cobertura limitada à janela metropolitana do Rio. As cores dos pontos vêm da interseção da coordenada cadastral com a imagem; áreas vazias não comprovam ausência de domínio.';
    const url = municipal ? 'https://forumseguranca.org.br/wp-content/uploads/2025/11/cartografias-violencia-amazonia-2025.pdf' : d?.fonte_territorial.pagina_projeto;
    document.querySelector('#legenda').replaceChildren(...[escala(), h('p', {}, explica),
      h('p', { class: 'seg-cobertura' }, municipal ? `${d?.contagens.municipios_documentados ?? '—'} municípios documentados na base, dos quais ${d?.contagens.municipios_fbsp ?? '—'} associados ao cadastro municipal entre os 344 nomes do FBSP (Amanã/AM ficou sem correspondência). Abra o ponto para ver a fonte específica.` : 'Apenas pontos cadastrais confirmados são classificados. Pixel de cerca de 34 × 37 m; sem cobertura inclui o exterior da janela e coordenadas não confirmadas. Controle e influência não devem ser somados.'),
      h('p', { class: 'seg-cobertura' }, 'Grupos de pontos com classificações diferentes recebem cor neutra. O centro mostra a categoria territorial; borda e tamanho representam o placar eleitoral, não intensidade do domínio. Os filtros de horário alteram os pontos e os placares, sem alterar a imagem territorial.'),
      h('p', { class: 'seg-cobertura' }, 'Estas fontes não verificam a situação de 2026 nem demonstram coação, vínculo de eleitores ou causa do voto.'),
      url ? h('a', { href: url, target: '_blank', rel: 'noopener' }, municipal ? 'Cartografias da Violência na Amazônia 2025' : 'Mapa original GENI/UFF e Fogo Cruzado') : null,
      municipal ? null : h('a', { class: 'seg-ir', href: '#uf=RJ&mun=60011&camada=' + k }, 'Abrir a área do Rio no mapa'),
      erro ? h('p', { role: 'alert' }, 'Os dados de segurança não carregaram. Recarregue a página para tentar novamente.') : null].filter(Boolean));
    return true;
  }
  const colunas = () => [[campo(), nomes[S.camada]]];
  const celula = (l) => h('td', {}, texto(l), h('small', {}, S.camada === 'crime' ? 'Registro municipal; não delimita domínio' : 'Território 2024 · GENI/IFC'));
  const colunasCsv = ['crime_presenca_municipal_documentada', 'crime_fontes', 'controle_territorial_rj_2024', 'influencia_territorial_rj_2024'];
  function csv(l) {
    const key = l.id.split('-').slice(0, 2).join('-');
    return [l.seg_crime ? 'Presença documentada' : 'Sem documentação nesta base', (d?.municipios[key]?.fontes || []).map((id) => d.referencias[id]).join(' | '), l.seg_controle || 'Sem cobertura territorial', l.seg_influencia || 'Sem cobertura territorial'];
  }
  return { ativo, instalar, aplicar, grupo, legenda, texto, colunas, celula, colunasCsv, csv };
};
