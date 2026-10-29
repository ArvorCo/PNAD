'use strict';
window.criarRelogiosMapa=function({S,COR,h}){
  const R=window.PolitizeRelogios,T=window.PolitizeTransmissao,ativo=()=>S.camada==='relogio',faltas=new Set();
  function instalar(){COR.relogio=Object.fromEntries(R.cores.map((c,i)=>[String(i),c]));S.meta.camadas.relogio={nome:'Recuos de horário no log',campo:'relogio_faixa',tipo:'categoria',grupo:'Horários e recebimento',categorias:R.nomes.map((_,i)=>String(i)),nomes:Object.fromEntries(R.nomes.map((n,i)=>[String(i),n])),explica:'Maior recuo de carimbo observado numa seção do local. A duração colore o ponto; não é grau de irregularidade. Mesmo sinal de relógio já incluído na conferência do arquivo.'};}
  async function carregar(ufs){await Promise.all(ufs.map(uf=>R.dados(uf).then(()=>faltas.delete(uf)).catch(()=>faltas.add(uf))));}
  const ref=l=>({uf:l.uf,local:l.id,...(l.horario?{secoes:l.secoes}:{})}),ler=l=>R.leitura(R.peek(l.uf),ref(l));
  function aplicar(ls){return ls.map(l=>{const r=ler(l),n=R.nivel(r);return {...l,relogio_max_s:r?.max_s??null,relogio_sinais:r?.sinalizadas??null,relogio_faixa:n===null?null:String(n)};});}
  function grupo(ls){const vs=ls.map(l=>l.relogio_faixa),s=vs.filter(v=>v!==null&&Number(v)>0);return s.length?String(Math.max(...s.map(Number))):vs.some(v=>v===null)?null:vs.length?'0':null;}
  const badge=l=>l.relogio_sinais?h('span',{class:'relogio-badge'},`${l.relogio_sinais} ${l.relogio_sinais===1?'seção':'seções'} com recuo/ajuste no log`):null;
  const texto=l=>l.relogio_sinais?`Recuo de carimbo: ${T.duracao(l.relogio_max_s)}`:l.relogio_faixa===null?'Cronologia: sem cobertura completa':'Sem recuo/ajuste observado';
  function escala(){return h('div',{class:'relogio-escala'},R.nomes.map((n,i)=>h('span',{},h('i',{style:'background:'+R.cores[i]}),n)));}
  function legenda(){if(!ativo())return false;document.querySelector('#mapa-escala').replaceChildren(h('b',{},'Recuos de horário no log'),escala(),h('small',{},'Cinza: cobertura incompleta sem sinal conhecido'));
    document.querySelector('#legenda').replaceChildren(h('p',{},S.meta.camadas.relogio.explica),escala(),h('p',{},'141 seções em 59 locais tiveram recuo de carimbo, todos antes do primeiro cômputo na sequência escrita do respectivo arquivo e urna. Em 113, a linha anterior informa data de ajuste anterior à eleição. A ficha informa o tamanho e as duas linhas, sem associar horário à escolha do eleitor. Relógio ou ordem de gravação exigem conferência; o sinal não prova alteração de votos.'),h('p',{},'Os grupos usam o maior recuo representado. O filtro horário considera somente as seções selecionadas; logs com relógio inconsistente não têm último voto utilizável nesse filtro.'),faltas.size?h('p',{role:'alert'},'Dados indisponíveis: '+[...faltas].join(', ')):null,h('a',{href:R.BASE+'secoes.csv',download:''},'Lista completa das seções sinalizadas'));return true;}
  const colunas=()=>[['relogio_max_s','Maior recuo de carimbo']];
  function celula(l){const r=ler(l);return h('td',{},h('b',{},r?.max_s===null||!r?'Sem dado':T.duracao(r.max_s)),h('small',{},`${r?.sinalizadas??0} com sinal · ${r?.cobertas??0}/${r?.secoes??l.n_secoes} verificáveis`));}
  const colunasCsv=['relogio_recuo_max_s','relogio_secoes_sinalizadas','relogio_secoes_verificaveis','relogio_secoes_total'];
  const csv=l=>{const r=ler(l);return ['max_s','sinalizadas','cobertas','secoes'].map(k=>r?.[k]??null);};
  return {instalar,carregar,aplicar,ativo,grupo,badge,texto,legenda,colunas,celula,colunasCsv,csv,painel:l=>R.painel(ref(l))};
};
