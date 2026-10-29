/* Camada própria: máximo por seção, inclusive em recortes e grupos do mapa. */
'use strict';
window.criarTransmissaoMapa=function({S,COR,H,h}) {
  const T=window.PolitizeTransmissao, ativo=()=>S.camada==='transmissao', faltas=new Set();
  function instalar(){
    COR.transmissao=Object.fromEntries(T.cores.map((c,i)=>[String(i),c]));
    S.meta.camadas.transmissao={nome:'Encerramento → recebimento do BU',campo:'transmissao_faixa',tipo:'categoria',grupo:'Horários e recebimento',
      categorias:T.nomes.map((_,i)=>String(i)),nomes:Object.fromEntries(T.nomes.map((n,i)=>[String(i),n])),
      explica:'Maior intervalo utilizável entre encerramento e recebimento do pacote do BU, calculado seção a seção. A cor cresce com a duração; a ficha mostra a mediana, os carimbos e a cobertura.'};
  }
  async function carregar(ufs){await Promise.all(ufs.map(uf=>T.dados(uf).then(()=>faltas.delete(uf)).catch(()=>faltas.add(uf))));}
  const ref=l=>({uf:l.uf,local:l.id,...(l.horario?{secoes:l.secoes}:{})});
  const ler=l=>T.leitura(T.peek(l.uf),ref(l));
  function aplicar(ls){return ls.map(l=>{const r=ler(l);return {...l,transmissao_max_s:r?.max_s??null,transmissao_mediana_s:r?.mediana_s??null,transmissao_faixa:r?.max_s===null||!r?null:String(T.nivel(r.max_s))};});}
  function grupo(ls){const vs=ls.map(l=>l.transmissao_max_s).filter(T.numero);return vs.length?String(T.nivel(Math.max(...vs))):null;}
  const texto=l=>'Até o recebimento: '+T.duracao(l.transmissao_max_s);
  function badge(l){return T.numero(l.transmissao_max_s)&&l.transmissao_max_s>14400?h('span',{class:'transmissao-badge',style:'--trans-cor:'+T.cores[T.nivel(l.transmissao_max_s)]},T.sinal(l.transmissao_max_s)+' · '+T.duracao(l.transmissao_max_s)):null;}
  function escala(){return h('div',{class:'transmissao-escala'},T.nomes.map((n,i)=>h('span',{},h('i',{style:'background:'+T.cores[i]}),n)));}
  function legenda(){
    if(!ativo())return false;
    document.querySelector('#mapa-escala').replaceChildren(h('b',{},'Encerramento → recebimento'),escala(),h('small',{},'Maior intervalo por seção · cinza: sem cronologia utilizável'));
    document.querySelector('#legenda').replaceChildren(h('p',{},S.meta.camadas.transmissao.explica),escala(),
      h('p',{},'Atenção acima de 4h; muita atenção acima de 5h. Cortes exploratórios, sem validação como teste de irregularidade. O intervalo longo foi frequente no país; compare também as demais seções do mesmo local.'),
      h('p',{},'Pontos agrupados usam o maior intervalo das seções representadas. Um caso longo não significa que todas as seções atrasaram. Os filtros de horário recompõem o máximo e a mediana apenas com as seções selecionadas.'),
      h('p',{},'Recebimento é o carimbo dr/hr do pacote do BU, não o início do envio nem a divulgação do resultado. Transporte, espera, conectividade ou reenvio exigem documentos para identificar a causa.'),
      faltas.size?h('p',{role:'alert'},'Dados não carregados: '+[...faltas].join(', ')+'. Refaça a busca para tentar.'):null,
      h('a',{href:T.BASE+'locais.csv',download:''},'Baixar os locais e seus intervalos'));
    return true;
  }
  function celula(l){const r=ler(l);return h('td',{},h('b',{},T.duracao(r?.max_s)),h('small',{},'Mediana: '+T.duracao(r?.mediana_s)),h('small',{},(r?.cobertas??0)+'/'+(r?.secoes??l.n_secoes)+' seções utilizáveis'));}
  const colunas=()=>[['transmissao_max_s','Encerramento → recebimento · máximo']];
  const colunasCsv=['recebimento_intervalo_max_s','recebimento_intervalo_mediana_s','recebimento_secoes_utilizaveis','recebimento_secoes_total','recebimento_secao_max','recebimento_excesso_outras_s'];
  function csv(l){const r=ler(l);return ['max_s','mediana_s','cobertas','secoes','secao_max','excesso_outras_s'].map(k=>r?.[k]??null);}
  const painel=l=>T.painel(ref(l),l.horario?'Seções selecionadas do local':l.nome);
  return {instalar,carregar,aplicar,ativo,grupo,texto,badge,legenda,celula,colunas,colunasCsv,csv,painel};
};
