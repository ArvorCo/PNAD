(() => {
  'use strict';
  const ns='http://www.w3.org/2000/svg';
  const colors=['#386ba6','#a74247','#818b78','#c3b598','#9a9c96','#53695f','#aebcba'];
  const fmt=n=>n===null?'–':n.toLocaleString('pt-BR',{maximumFractionDigits:1})+'%';
  function ink(color){
    const rgb=[1,3,5].map(i=>parseInt(color.slice(i,i+2),16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);
    const l=rgb[0]*.2126+rgb[1]*.7152+rgb[2]*.0722;
    return 1.05/(l+.05)>=4.5?'#fffdf8':'#10201c';
  }
  function node(tag,text,attributes={},svg=false){
    const e=svg?document.createElementNS(ns,tag):document.createElement(tag);
    if(text!==null)e.textContent=text;
    for(const [k,v] of Object.entries(attributes))e.setAttribute(k,String(v));
    return e;
  }
  function stacked(rows,options,title,palette=colors){
    const figure=node('figure',null,{class:'chart stack-chart'}),scroll=node('div',null,{class:'chart-scroll',tabindex:'0'});
    let columns=options.length>4?Math.min(3,options.length):options.length;
    if(Math.max(...options.map(s=>s.length))>32)columns=Math.min(columns,2);
    const top=40+28*Math.ceil(options.length/columns),height=top+44+62*rows.length,svg=node('svg',null,{viewBox:`0 0 900 ${height}`,role:'img','aria-label':title},true);
    svg.append(node('title',title,{},true));
    options.forEach((label,i)=>{const x=12+(i%columns)*880/columns,y=18+28*Math.floor(i/columns);
      svg.append(node('rect',null,{x,y,width:10,height:10,fill:palette[i%palette.length]},true));
      svg.append(node('text',label,{x:x+16,y:y+10,'font-size':12},true));
    });
    const mobile=node('div',null,{class:'stack-mobile'});
    rows.forEach(([label,values],i)=>{let x=270;const y=top+12+i*62,known=values.reduce((a,v)=>a+(v??0),0),sum=values.some(v=>v===null)?Math.max(known,100):(known||100);
      const row=node('div',null,{class:'mobile-row'}),bar=node('div',null,{class:'mobile-bar'});row.append(node('b',label));
      svg.append(node('text',label,{x:252,y:y+22,'text-anchor':'end','font-size':15},true));
      values.forEach((v,j)=>{const width=600*(v??0)/sum;
        if(width){const color=palette[j%palette.length],rect=node('rect',null,{x,y,width,height:34,fill:color},true);
          rect.append(node('title',`${label}: ${options[j]} ${fmt(v)}`,{},true));svg.append(rect);
          if(width>=40)svg.append(node('text',fmt(v),{x:x+width/2,y:y+23,'text-anchor':'middle',fill:ink(color),'font-size':14,'font-weight':600},true));
          const part=node('span',width>=54?fmt(v):'',{title:`${options[j]}: ${fmt(v)}`,style:`width:${width/6}%;background:${color};color:${ink(color)}`});bar.append(part);
        }x+=width;
      });
      row.append(bar);mobile.append(row);
    });
    for(let v=0;v<=100;v+=25)svg.append(node('text',v+'%',{x:270+v*6,y:height-12,'text-anchor':'middle','font-size':12},true));
    const legend=node('div',null,{class:'mobile-legend'});options.forEach((label,i)=>{const item=node('span');item.append(node('i',null,{style:`background:${palette[i%palette.length]}`}),document.createTextNode(label));legend.append(item);});mobile.append(legend);
    scroll.append(svg);figure.append(scroll,mobile);
    const detail=node('details'),summary=node('summary','Ver os números do gráfico'),wrap=node('div',null,{class:'table-scroll',tabindex:'0'}),table=node('table');
    const head=node('thead'),headrow=node('tr');['Segmento',...options].forEach(v=>headrow.append(node('th',v,{scope:'col'})));head.append(headrow);table.append(head);
    const body=node('tbody');rows.forEach(([label,values])=>{const row=node('tr');row.append(node('td',label));values.forEach(v=>row.append(node('td',fmt(v))));body.append(row);});table.append(body);wrap.append(table);detail.append(summary,wrap);figure.append(detail);return figure;
  }
  const source=document.getElementById('d-explorer-data');
  if(source){
    const data=JSON.parse(source.textContent),q=document.getElementById('d-question'),dimension=document.getElementById('d-dimension'),target=document.getElementById('d-explorer-chart');
    const groups={
      'Gênero':['homens','mulheres'],
      'Idade':data.house==='nexus'?['16–24','25–40','41–59','60+']:['16–24','25–34','35–44','45–59','60+'],
      'Renda':data.house==='nexus'?['até 1 SM','1–2 SM','2–5 SM','>5 SM']:['até 2 SM','2–5 SM','>5 SM'],
      'Região':['Nordeste','Sudeste','Sul','CO/Norte'],
      'Escolaridade':['fundamental','médio','superior'],
      'Religião':data.house==='nexus'?['católica','evangélica','outras religiões','sem religião']:['católica','evangélica'],
      'Ocupação':data.house==='nexus'?['PEA formal','PEA informal','desocupados','não PEA']:['PEA','não PEA'],
      'Município':data.house==='nexus'?['capital','RM','interior']:['metropolitana','interior']
    };
    if(data.house==='datafolha'){groups['Cor autodeclarada']=['branca','preta','parda'];groups['Preferência partidária']=['PT','PL','outro partido','sem partido'];}
    Object.keys(groups).forEach(label=>dimension.append(node('option',label,{value:label})));
    function render(){
      const table=data.tables[q.value],names=['total',...groups[dimension.value]],opts=Object.keys(table.segments.total.responses);
      const rows=names.map(name=>[name,Object.values(table.segments[name].responses)]);
      const schemes={aprovacao:['#28705f','#a74247','#9a9c96'],decisao:['#28705f','#a39153','#9a9c96'],potencial_lula:['#28705f','#a39153','#a74247','#9a9c96','#b2b8ae'],potencial_flavio:['#28705f','#a39153','#a74247','#9a9c96','#b2b8ae']};
      if(q.value==='avaliacao')schemes.avaliacao=data.house==='nexus'?['#28705f','#69a089','#a39153','#ba6b5d','#a74247','#9a9c96']:['#28705f','#a39153','#a74247','#9a9c96'];
      const chart=stacked(rows,opts,`${q.options[q.selectedIndex].textContent} / ${dimension.value}`,schemes[q.value]??colors),info=node('p',table.universe,{class:'note'});
      const bases=names.map(name=>{const r=table.segments[name];return `${name}: ${r.base_ponderada?.toLocaleString('pt-BR')??'base não publicada'}`;});
      const base=node('p',data.house==='datafolha'?'Bases ponderadas: '+bases.join(' · '):'Perfil de cada grupo publicado na p. 99; bases e tamanho efetivo não informados.',{class:'note'});
      const references=node('p','Fonte: ',{class:'refs'});
      const pages=[...new Set(names.map(n=>table.segments[n].page??table.page))];
      pages.forEach(page=>{references.append(node('a','p. '+page,{href:data.pdf+'#page='+page}));references.append(document.createTextNode(' · '));});
      target.replaceChildren(info,chart,base,references);
      window.dossieExplorador={question:q.value,dimension:dimension.value,house:data.house,rows,options:opts};
    }
    q.addEventListener('change',render);dimension.addEventListener('change',render);render();document.querySelector('.explorer-controls').hidden=false;
  }
  const issues=document.getElementById('d-issues-data');
  if(issues){
    const data=JSON.parse(issues.textContent),target=document.getElementById('d-issues-chart');
    function render(mode){
      const rows=Object.entries(data).sort((a,b)=>b[1][mode]-a[1][mode]),max=Math.max(...rows.map(r=>r[1][mode])),svg=node('svg',null,{viewBox:`0 0 900 ${48+rows.length*48}`,role:'img','aria-label':mode===2?'Duas menções de problemas':'Primeira menção de problemas'},true);
      rows.forEach(([label,values],i)=>{const y=14+i*48,w=500*values[mode]/max;
        svg.append(node('text',label,{x:310,y:y+23,'text-anchor':'end','font-size':15},true),node('rect',null,{x:330,y,width:w,height:32,fill:'#28705f'},true),node('text',fmt(values[mode]),{x:340+w,y:y+23,'font-size':15},true));
      });
      const figure=node('figure',null,{class:'chart bars-chart'}),scroll=node('div',null,{class:'chart-scroll',tabindex:'0'}),mobile=node('div',null,{class:'bar-mobile'});
      rows.forEach(([label,values])=>{const row=node('div',null,{class:'mobile-single'}),head=node('b'),track=node('div');head.append(node('span',label),node('span',fmt(values[mode])));track.append(node('span',null,{style:`width:${100*values[mode]/max}%`}));row.append(head,track);mobile.append(row);});
      scroll.append(svg);figure.append(scroll,mobile);target.replaceChildren(figure);
      document.querySelectorAll('[data-issue-mode]').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.issueMode)===mode)));
      window.dossieAgenda={mode,rows};
    }
    document.querySelectorAll('[data-issue-mode]').forEach(button=>button.addEventListener('click',()=>render(Number(button.dataset.issueMode))));render(2);document.querySelector('.issue-controls').hidden=false;
  }
})();
