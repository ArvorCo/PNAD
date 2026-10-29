/* Sinal existente de cronologia: não acrescenta outro ponto ao diagnóstico. */
(function(root){
  'use strict';
  const BASE='assets/politize_se/relogios/', V='20261029-relogios1', T=root.PolitizeTransmissao;
  const cache=new Map(), loaded=new Map();
  const cores=['#d6e6df','#cfa04a','#bc6336','#862b36','#70527b'];
  const nomes=['Sem recuo/ajuste observado','Recuo até 1min','Recuo >1 a 5min','Recuo >5min','Ajuste sem recuo'];

  async function dados(uf){
    if(uf==='ZZ')return {locais:{},detalhes:{}};
    if(!cache.has(uf)){
      const p=fetch(BASE+uf+'.json.gz?v='+V).then(async r=>{
        if(!r.ok)throw Error('Dados indisponíveis');
        const b=await r.blob(), magic=new Uint8Array(await b.slice(0,2).arrayBuffer());
        const d=magic[0]===31&&magic[1]===139?await new Response(b.stream().pipeThrough(new DecompressionStream('gzip'))).json():JSON.parse(await b.text());
        if(d.formato!==1||d.uf!==uf)throw Error('Formato incompatível');loaded.set(uf,d);return d;
      });cache.set(uf,p);p.catch(()=>cache.delete(uf));
    }return cache.get(uf);
  }
  function selecionar(d,ref){const ids=ref.secoes?new Set(ref.secoes.map(Number)):ref.secao!==undefined?new Set([Number(ref.secao)]):null;return (d?.locais?.[ref.local]?.secoes||[]).filter(r=>!ids||ids.has(r[0]));}
  function resumo(rows){const ok=rows.filter(r=>r[5]==='ok');return {secoes:rows.length,cobertas:ok.length,sinalizadas:ok.filter(r=>r[1]||r[3]).length,max_s:ok.length?Math.max(...ok.map(r=>r[2])):null,recuos:ok.reduce((a,r)=>a+r[1],0),ajustes:ok.reduce((a,r)=>a+r[3],0)};}
  function leitura(d,ref){return d?.locais?.[ref.local]?resumo(selecionar(d,ref)):null;}
  function nivel(r){if(!r||!r.cobertas)return null;if(!r.sinalizadas)return r.cobertas===r.secoes?0:null;if(!r.max_s)return 4;return r.max_s<=60?1:r.max_s<=300?2:3;}
  function el(tag,attrs={},...cs){const n=document.createElement(tag);Object.entries(attrs).forEach(([k,v])=>n.setAttribute(k,v));cs.flat(Infinity).forEach(c=>{if(c!==null&&c!==undefined)n.append(c instanceof Node?c:String(c));});return n;}
  function painel(ref){
    const box=el('div',{class:'relogio-painel','aria-live':'polite'});
    dados(ref.uf).then(d=>{
      const rows=selecionar(d,ref),r=leitura(d,ref);
      if(!r){box.replaceChildren(el('p',{class:'relogio-nota'},'Cronologia do log: sem cobertura neste recorte.'));return;}
      if(!r.sinalizadas){box.replaceChildren(el('details',{class:'relogio-sem-sinal'},el('summary',{},'Cronologia do log · '+(r.cobertas===r.secoes?'sem recuo/ajuste observado':'cobertura parcial')),el('p',{},`${r.cobertas} de ${r.secoes} seções verificáveis. Ausência deste sinal não certifica a integridade da votação.`)));return;}
      const sinais=rows.filter(x=>x[5]==='ok'&&(x[1]||x[3]));
      box.replaceChildren(el('section',{class:'relogio-alerta',style:'--relogio-cor:'+cores[nivel(r)]},
        el('p',{class:'relogio-kicker'},'CONFERÊNCIA DO ARQUIVO · 2º TURNO'),el('h3',{},'Atenção: recuo de horário no log'),
        el('p',{},`${r.sinalizadas} de ${r.secoes} seções deste recorte com sinal. Maior recuo: ${T.duracao(r.max_s)}. Cobertura: ${r.cobertas}/${r.secoes}.`),
        el('p',{},'Uma linha foi gravada com horário anterior ao da linha precedente da mesma urna e arquivo. Isso pode decorrer do relógio ou da ordem de gravação; a causa não está identificada.'),
        sinais.map(row=>{
          const v=d.detalhes[ref.local+'/'+row[0]];
          return el('details',{class:'relogio-secao',open:''},el('summary',{},`Seção ${row[0]} · ${row[1]} recuo(s) · máximo ${T.duracao(row[2])}`),
            el('p',{},row[4]?'Contagem e ciclos do log conferem com o comparecimento do BU.':'A contagem também pede conferência com o BU.'),
            el('div',{class:'relogio-tabela',tabindex:'0',role:'region','aria-label':'Recuos de carimbo'},el('table',{},
              el('thead',{},el('tr',{},['Linha anterior','Linha seguinte','Recuo','Contexto dos carimbos'].map(x=>el('th',{scope:'col'},x)))),
              el('tbody',{},(v?.eventos||[]).map(e=>el('tr',{},el('td',{},T.hora(e.anterior_s),el('small',{},e.app_anterior)),el('td',{},T.hora(e.seguinte_s),el('small',{},e.app_seguinte)),el('td',{},T.duracao(e.recuo_s)),el('td',{},e.antes_computo_na_escrita?'Antes do primeiro cômputo na ordem escrita deste arquivo':'Após cômputo na ordem escrita deste arquivo',e.data_anterior_informada?el('small',{},'Operador informou '+e.data_anterior_informada):null)))))),
            el('a',{href:T.linkAux(ref.local,row[0]),target:'_blank',rel:'noopener'},'Consultar o pacote no TSE'));
        }),
        el('p',{class:'relogio-nota'},'Horários convertidos para Brasília. A posição na sequência escrita não determina o instante real: os carimbos são inconsistentes. Estes logs ficam fora da distribuição de votos por horário; os totais do BU permanecem.'),
        el('p',{class:'relogio-nota'},'É o sinal de relógio já incluído em “Conferência do arquivo”, sem somar outro ponto. Compare ata, relógio e sequência original dos arquivos. Recuo de carimbo não demonstra alteração de votos.'),
        el('p',{},el('a',{href:BASE+'secoes.csv',download:''},'Baixar as seções sinalizadas'),' · ',el('a',{href:BASE+'indice.json'},'Critério e evidências'))));
    }).catch(()=>box.replaceChildren(el('p',{role:'alert'},'Os dados de cronologia não carregaram. Recarregue para tentar; ausência de dados não significa ausência de sinal.')));
    return box;
  }
  root.PolitizeRelogios={BASE,cores,nomes,dados,selecionar,resumo,leitura,nivel,painel,peek:uf=>loaded.get(uf)};
})(window);
