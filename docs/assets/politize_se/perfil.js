/* Cadastro do TSE: idade × sexo, sem associação individual com voto. */
(function (root) {
  'use strict';
  const BASE = 'assets/politize_se/perfil/', V = '20261029-perfil1', cache = new Map();
  const faixas = ['16–17', '18–24', '25–34', '35–44', '45–54', '55–59', '60–64', '65–74', '75–84', '85+', 'Não informada'];
  const fmt = (n, d = 0) => n.toLocaleString('pt-BR', { maximumFractionDigits: d });
  function el(tag, attrs = {}, ...children) {
    const n = document.createElement(tag);
    Object.entries(attrs).forEach(([k,v]) => n.setAttribute(k,v));
    children.flat(Infinity).forEach(c => { if (c !== null && c !== undefined) n.append(c instanceof Node ? c : String(c)); }); return n;
  }
  async function dados(uf, resumo = false) {
    const key = (resumo ? 'resumos/' : '') + uf;
    if (!cache.has(key)) {
      const p = fetch(BASE + key + '.json.gz?v=' + V).then(async r => {
        if (!r.ok) throw new Error('Perfil indisponível');
        const b = await r.blob(), bytes = new Uint8Array(await b.slice(0,2).arrayBuffer());
        const d = bytes[0] === 31 && bytes[1] === 139 ? await new Response(b.stream().pipeThrough(new DecompressionStream('gzip'))).json() : JSON.parse(await b.text());
        if (d.formato !== 1 || d.uf !== uf) throw new Error('Perfil incompatível');
        return d;
      }); cache.set(key,p); p.catch(() => cache.delete(key));
    } return cache.get(key);
  }
  const indices = new WeakMap();
  function indexar(d){
    if(!indices.has(d)){
      const todas=Object.entries(d.secoes),local=new Map(),zona=new Map(),mun=new Map();
      for(const row of todas){const [m,z]=row[0].split('-'),lid=`${d.uf}-${m}-${z}-${row[1][0]}`;
        for(const [map,key] of [[local,lid],[zona,Number(z)],[mun,Number(m)]]){if(!map.has(key))map.set(key,[]);map.get(key).push(row);}
      }indices.set(d,{todas,local,zona,mun});
    }return indices.get(d);
  }
  function selecionar(d, ref) {
    const lid=ref.local?.split('-'),m=ref.mun||lid?.[1],z=ref.zona||lid?.[2];
    if(ref.secao!==undefined && m && z){const key=String(m).padStart(5,'0')+'-'+Number(z)+'-'+Number(ref.secao);return d.secoes[key]?[[key,d.secoes[key]]]:[];}
    const idx=indexar(d),rows=ref.local?idx.local.get(ref.local)||[]:ref.zona?idx.zona.get(Number(ref.zona))||[]:ref.mun?idx.mun.get(Number(ref.mun))||[]:idx.todas;
    const ss=ref.secoes?new Set(ref.secoes.map(Number)):ref.secao!==undefined?new Set([Number(ref.secao)]):null;
    return rows.filter(([key])=>{const [mun,zona,sec]=key.split('-');return (!ref.mun||Number(mun)===Number(ref.mun))&&(!ref.zona||Number(zona)===Number(ref.zona))&&(!ss||ss.has(Number(sec)));});
  }
  function somar(rows) {
    const v = Array(33).fill(0);
    for (const [, [, a]] of rows) a.forEach((n,i) => { v[i] += n; });
    return v;
  }
  function estatisticas(v) {
    const soma = a => a.reduce((s,n) => s+n,0);
    return [soma(v), soma(v.filter((_,i)=>i%3===1)), soma(v.slice(0,6)), soma(v.slice(18,30)), soma(v.slice(30)), soma(v.filter((_,i)=>i%3===2))];
  }
  function render(v, titulo, n) {
    const [total,fem,jov,idosos,semIdade,semSexo] = estatisticas(v), pct = x => total ? fmt(100*x/total,1)+'%' : 'Sem dado';
    const box = el('div', {}, el('p',{class:'perfil-kicker'},'TSE · CADASTRO ELEITORAL 2026'), el('h3',{},'Quem está inscrito para votar'), el('p',{class:'perfil-escopo'},titulo));
    if (!total) { box.append(el('p',{},'Perfil cadastral não disponível para este recorte.')); return box; }
    const masc = total-fem-semSexo, max = Math.max(...v.filter((_,i)=>i<30 && i%3!==2));
    box.append(el('div',{class:'perfil-resumo'},[[fmt(total),'inscritos'],[pct(fem),'sexo feminino'],[pct(jov),'16 a 24 anos'],[pct(idosos),'60 anos ou mais']].map(([val,nome])=>el('div',{},el('b',{},val),el('span',{},nome)))));
    box.append(el('div',{class:'perfil-chave'},el('span',{class:'perfil-m'},'Masculino · '+pct(masc)),el('span',{class:'perfil-f'},'Feminino · '+pct(fem))));
    const chart = el('div',{class:'perfil-piramide','aria-label':'Pirâmide etária; contagens e percentuais por faixa no foco ou toque'});
    const info = el('p',{class:'perfil-leitura',role:'status'},'Toque numa faixa para ver os números.');
    for (let i=9;i>=0;i--) {
      const a=v[3*i],b=v[3*i+1], outros=v[3*i+2];
      const texto=`${faixas[i]} anos: masculino ${fmt(a)} (${pct(a)}), feminino ${fmt(b)} (${pct(b)}), sexo não informado ${fmt(outros)}.`;
      const linha=el('button',{type:'button',class:'perfil-faixa','aria-label':texto,title:texto},el('span',{class:'perfil-lado perfil-esquerda'},el('i',{style:`width:${max?100*a/max:0}%`})),el('span',{class:'perfil-idade'},faixas[i]),el('span',{class:'perfil-lado perfil-direita'},el('i',{style:`width:${max?100*b/max:0}%`})));
      ['click','focus','mouseenter'].forEach(e=>linha.addEventListener(e,()=>{info.textContent=texto;}));chart.append(linha);
    }
    box.append(chart,info,el('p',{class:'perfil-nota'},`${fmt(n)} seções cadastrais · Idade não informada: ${fmt(semIdade)} · Sexo não informado: ${fmt(semSexo)}. Percentuais sobre todos os inscritos; barras na mesma escala nos dois lados, relativa ao pico deste recorte.`));
    const tabela=el('details',{},el('summary',{},'Contagens por idade e sexo'));
    tabela.append(el('div',{class:'perfil-tabela'},el('table',{},el('thead',{},el('tr',{},['Idade','Masculino','Feminino','Não informado'].map(s=>el('th',{},s)))),el('tbody',{},faixas.map((f,i)=>el('tr',{},el('th',{scope:'row'},f),[0,1,2].map(j=>el('td',{},fmt(v[i*3+j])))))))));
    box.append(tabela,el('p',{class:'perfil-nota'},'Perfil dos inscritos, não dos que compareceram. O cadastro pode diferir dos aptos do BU por transferências e agregações. Sexo cadastral (campo CD_GENERO), distinto de identidade de gênero. Não revela como cada grupo votou.'),el('a',{href:'https://dadosabertos.tse.jus.br/dataset/eleitorado-2026',target:'_blank',rel:'noopener'},'Fonte: perfil do eleitorado por seção · TSE'));
    return box;
  }
  function painel(ref,titulo='Seções selecionadas') {
    const box=el('section',{class:'perfil-eleitoral','aria-busy':'true','aria-label':'Perfil do eleitorado'});
    const carregar=async()=>{
      box.replaceChildren(el('p',{role:'status'},'Carregando perfil do eleitorado…'));
      try {
        const d=await dados(ref.uf), rows=selecionar(d,ref), grafico=el('div',{},render(somar(rows),titulo,rows.length));
        if(ref.escolherSecao && ref.local){
          const [,mun,z]=ref.local.split('-');
          const sel=el('select',{'aria-label':'Recorte da pirâmide etária'},el('option',{value:'local'},'Este local de votação'),el('option',{value:'zona'},'Zona '+z+' inteira'),el('option',{value:'mun'},'Município inteiro'),rows.map(([k])=>el('option',{value:'s:'+k.split('-')[2]},'Seção '+k.split('-')[2])));
          sel.addEventListener('change',()=>{
            const r=sel.value==='zona'?{uf:ref.uf,zona:z}:sel.value==='mun'?{uf:ref.uf,mun}:sel.value.startsWith('s:')?{uf:ref.uf,local:ref.local,secao:Number(sel.value.slice(2))}:ref;
            const rs=selecionar(d,r);grafico.replaceChildren(render(somar(rs),sel.selectedOptions[0].textContent,rs.length));
          });box.replaceChildren(el('label',{class:'perfil-seletor'},'Pirâmide de',sel),grafico);
        }else box.replaceChildren(grafico);
      }catch{const retry=el('button',{type:'button'},'Tentar novamente');retry.onclick=carregar;box.replaceChildren(el('p',{},'O perfil não carregou. Os demais indicadores continuam disponíveis.'),retry);}finally{box.setAttribute('aria-busy','false');}
    };carregar();return box;
  }
  root.PolitizePerfil={dados,selecionar,somar,estatisticas,painel,render};
})(window);
