/* Carimbos do BU e do pacote recebido: um intervalo observado, causa não identificada. */
(function (root) {
  'use strict';
  const BASE = 'assets/politize_se/transmissao/', V = '20261029-transmissao1';
  const limites = [3600, 7200, 10800, 14400, 18000];
  const cores = ['#d6e6df','#a7c5ad','#dcce7e','#df9b4c','#bd592e','#802c35'];
  const nomes = ['Até 1h','>1h a 2h','>2h a 3h','>3h a 4h','>4h a 5h','Mais de 5h'];
  const motivos = {exterior:'Exterior fora do recorte de Brasília', identidade:'Identidade não conferida',
    sem_horario:'Carimbo ausente', data:'Data incompatível', recebimento_antes_encerramento:'Recebimento anterior ao encerramento',
    ordem_emissao:'Ordem entre emissão e recebimento inconsistente', multiplos_pacotes:'Mais de um pacote: primeira chegada não identificada'};
  const cache = new Map(), carregados = new Map();
  const numero = n => typeof n === 'number' && Number.isFinite(n);
  const mediana = xs => { const s=[...xs].sort((a,b)=>a-b), n=s.length; return n ? (s[Math.floor((n-1)/2)]+s[Math.floor(n/2)])/2 : null; };
  const nivel = s => !numero(s)||s<0 ? null : limites.findIndex(v=>s<=v)<0 ? limites.length : limites.findIndex(v=>s<=v);
  function duracao(s) {
    if (!numero(s)) return 'Sem intervalo utilizável';
    const v=Math.round(Math.abs(s)), h=Math.floor(v/3600), m=Math.floor(v/60)%60, seg=v%60;
    return (s<0?'−':'')+(h?h+'h ':'')+String(m).padStart(2,'0')+'min '+String(seg).padStart(2,'0')+'s';
  }
  function hora(s) {
    if (!numero(s)) return 'Sem carimbo';
    const t=new Date(Date.UTC(2026,9,25)+s*1000);
    return t.toISOString().slice(11,19)+(Math.floor(s/86400)?' · '+t.toISOString().slice(8,10)+'/10':'');
  }
  const sinal = s => !numero(s) ? 'Sem classificação' : s>18000 ? 'Muita atenção ao intervalo (>5h)' : s>14400 ? 'Atenção ao intervalo (>4h)' : 'Intervalo observado';
  async function dados(uf) {
    if (uf==='ZZ') return {formato:1,uf,locais:{}};
    if (!cache.has(uf)) {
      const p=fetch(BASE+uf+'.json.gz?v='+V).then(async r=>{
        if (!r.ok) throw Error('Dados de recebimento indisponíveis');
        const b=await r.blob(), magic=new Uint8Array(await b.slice(0,2).arrayBuffer());
        const d=magic[0]===31 && magic[1]===139 ? await new Response(b.stream().pipeThrough(new DecompressionStream('gzip'))).json() : JSON.parse(await b.text());
        if (d.formato!==1 || d.uf!==uf || !d.locais) throw Error('Formato incompatível');
        carregados.set(uf,d); return d;
      });
      cache.set(uf,p); p.catch(()=>cache.delete(uf));
    }
    return cache.get(uf);
  }
  function selecionar(d,ref) {
    const ss=ref.secoes ? new Set(ref.secoes.map(Number)) : ref.secao!==undefined ? new Set([Number(ref.secao)]) : null;
    return (d?.locais?.[ref.local]?.secoes||[]).filter(r=>!ss||ss.has(r[0]));
  }
  function resumo(rows) {
    const ok=rows.filter(r=>r[5]==='ok'&&numero(r[4])&&r[4]>=0);
    const pior=[...ok].sort((a,b)=>b[4]-a[4]||a[0]-b[0])[0];
    const outras=ok.filter(r=>r!==pior).map(r=>r[4]), ref=mediana(outras);
    return {secoes:rows.length,cobertas:ok.length,max_s:pior?.[4]??null,mediana_s:mediana(ok.map(r=>r[4])),
      min_s:ok.length?Math.min(...ok.map(r=>r[4])):null,secao_max:pior?.[0]??null,
      mediana_outras_s:ref,excesso_outras_s:ref===null?null:pior[4]-ref,
      acima_4h:ok.filter(r=>r[4]>14400).length,acima_5h:ok.filter(r=>r[4]>18000).length};
  }
  function leitura(d,ref) {
    if (!d) return null;
    if (!ref.secoes && ref.secao===undefined) return d.locais[ref.local]?.resumo??null;
    return resumo(selecionar(d,ref));
  }
  function el(tag,attrs={},...children) {
    const n=document.createElement(tag);
    Object.entries(attrs).forEach(([k,v])=>{if(v!==undefined&&v!==null)n.setAttribute(k,String(v));});
    children.flat(Infinity).forEach(c=>{if(c!==null&&c!==undefined)n.append(c instanceof Node?c:String(c));});
    return n;
  }
  function linkAux(id,secao) {
    const [UF,mun,z]=id.split('-'), uf=UF.toLowerCase(), zona=String(z).padStart(4,'0'), s=String(secao).padStart(4,'0');
    return `https://resultados.tse.jus.br/oficial/ele2026/arquivo-urna/3221/dados/${uf}/${mun}/${zona}/${s}/p003221-${uf}-m${mun}-z${zona}-s${s}-aux.json`;
  }
  function render(d,ref,titulo) {
    const rows=selecionar(d,ref), r=leitura(d,ref)||resumo([]), n=nivel(r.max_s);
    const box=el('section',{class:'transmissao-conteudo',style:'--trans-cor:'+(cores[n]||'#888')},
      el('p',{class:'transmissao-kicker'},'2º TURNO · 25/10/2026 · BRASÍLIA'),
      el('h3',{},'Do encerramento ao recebimento pelo TSE'),el('p',{},titulo),
      el('p',{class:'transmissao-sinal'},sinal(r.max_s)),
      el('div',{class:'transmissao-numeros'},el('div',{},el('strong',{},duracao(r.max_s)),el('span',{},'Maior intervalo de uma seção')),
        el('div',{},el('strong',{},duracao(r.mediana_s)),el('span',{},'Mediana deste recorte'))),
      el('p',{class:'transmissao-cobertura'},`${r.cobertas} de ${r.secoes} seções com cronologia utilizável. ${r.acima_4h} acima de 4h; ${r.acima_5h} acima de 5h.`));
    if(ref.uf==='ZZ') box.append(el('p',{},motivos.exterior));
    if(r.mediana_outras_s!==null) box.append(el('p',{},`Seção ${r.secao_max}: ${duracao(r.excesso_outras_s)} acima da mediana das demais seções deste recorte (${duracao(r.mediana_outras_s)}). É comparação descritiva, sem controle da logística.`));
    const tab=el('table',{},el('thead',{},el('tr',{},...['Seção','Encerramento','Emissão do BU','Recebimento','Intervalo','Situação'].map(s=>el('th',{scope:'col'},s)))),
      el('tbody',{},[...rows].sort((a,b)=>(b[4]??-Infinity)-(a[4]??-Infinity)).map(row=>{
        const [s,enc,em,rec,delta,status]=row, cor=cores[nivel(status==='ok'?delta:null)]||'#888';
        return el('tr',{'data-trans-secao':s},el('th',{scope:'row'},el('a',{href:linkAux(ref.local,s),target:'_blank',rel:'noopener'},s)),
          el('td',{},hora(enc)),el('td',{},hora(em)),el('td',{},hora(rec)),
          el('td',{},el('b',{class:'transmissao-delta',style:'border-color:'+cor},duracao(delta))),
          el('td',{},status==='ok'?sinal(delta):motivos[status]||'Sem classificação'));
      })));
    box.append(el('div',{class:'transmissao-tabela',tabindex:0,role:'region','aria-label':'Carimbos por seção'},tab));
    const total=d.locais[ref.local]?.resumo;
    if(ref.secao!==undefined && total?.secoes>1) box.append(el('p',{},`Referência do local inteiro: mediana ${duracao(total.mediana_s)}, máximo ${duracao(total.max_s)} em ${total.cobertas} seções utilizáveis.`));
    box.append(el('p',{class:'transmissao-nota'},'O carimbo de recebimento é dr/hr do pacote do BU publicado pelo TSE. Não é a hora em que o envio começou. O intervalo pode reunir emissão, coleta, transporte, espera e recepção; não identifica a causa nem prova alteração de votos.'),
      el('details',{},el('summary',{},'O que conferir nos casos de maior atenção'),el('p',{},'Cortes exploratórios: atenção acima de 4h e muita atenção acima de 5h. O maior intervalo não representa todas as seções do local. Compare a mediana e os carimbos das demais seções.'),
        el('p',{},'Peça a ata da seção, horários de coleta e entrega da mídia, ponto e registros do Transportador/JE-Connect, ocorrências de conectividade, contingência e eventuais reenvios. Compare o BU impresso na seção com o BU publicado. Essas evidências permitem investigar o intervalo; os carimbos sozinhos não o explicam.'),
        el('a',{href:BASE+'indice.json'},'Critérios, cobertura e fontes'), ' · ',el('a',{href:BASE+'locais.csv',download:''},'Baixar todos os locais')),
      el('p',{class:'transmissao-nota'},el('a',{href:'assets/encerramento_2t_2026/supertimeline-2t-2026.png?v=20261029-timeline3',download:''},'Timeline completa: votos, encerramentos e recebimentos (PNG)'), ' · ', el('a',{href:'assets/encerramento_2t_2026/supertimeline-2t-2026.pdf?v=20261029-timeline3',download:''},'PDF da timeline')),
      el('p',{class:'transmissao-nota'},el('a',{href:BASE+'encerramento-recebimento-2t-2026.png',download:''},'Gráfico nacional (PNG)'), ' · ',
        el('a',{href:BASE+'encerramento-recebimento-2t-2026.pdf',download:''},'PDF'), ' · ',el('a',{href:'assets/encerramento_2t_2026/encerramento-2t-2026.png',download:''},'Encerramentos e votos por horário')));
    return box;
  }
  function painel(ref,titulo='Local de votação') {
    const box=el('div',{class:'transmissao-painel','aria-live':'polite'},el('p',{},'Carregando os carimbos de encerramento e recebimento…'));
    dados(ref.uf).then(d=>box.replaceChildren(render(d,ref,titulo))).catch(()=>box.replaceChildren(el('p',{role:'alert'},'Os dados de recebimento não carregaram. Recarregue para tentar novamente. Falta de dados não significa intervalo curto.')));
    return box;
  }
  root.PolitizeTransmissao={BASE,limites,cores,nomes,motivos,numero,nivel,duracao,hora,sinal,dados,selecionar,resumo,leitura,painel,linkAux,peek:uf=>carregados.get(uf)};
})(window);
