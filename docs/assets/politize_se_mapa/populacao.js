/* Um círculo por município. Não replica população municipal em cada escola. */
window.criarPopulacaoMapa=function({S,h,setStatus,limparMarcadores,gravarHash,distanciaKm,H}) {
  const P=window.PolitizePopulacao;
  const specs={
    pop_eleitorado:['Eleitorado / população 16+','eleitorado_por100'],
    pop_comparecimento1:['Comparecimento 1º / população 16+','comparecimento1_por100'],
    pop_comparecimento2:['Comparecimento 2º / população 16+','comparecimento2_por100'],
    pop_mulheres:['Diferença de sexo feminino · TSE − Censo','mulheres_dif_pp'],
    pop_jovens:['Diferença de 16–24 anos · TSE − Censo','jovens_dif_pp'],
    pop_idosos:['Diferença de 60+ · TSE − Censo','idosos_dif_pp'],
  };
  let data=null,layer=null,shown=false,request=0,lista=[],sort={key:null,dir:-1},pagina=1;
  const ativo=()=>Object.hasOwn(specs,S.camada);
  const ratio=()=>ativo()&&specs[S.camada][1].endsWith('por100');
  const normal=s=>String(s||'').normalize('NFD').replace(/\p{Diacritic}/gu,'').toLowerCase();
  const $=s=>document.querySelector(s);
  const raio=v=>P.num(v)?Math.max(2,Math.min(48,10*Math.sqrt(Math.max(0,v)/100))):4;
  const valor=m=>m[specs[S.camada][1]];
  const cor=v=>!P.num(v)?'#909a96':v>(ratio()?100:0)?'#9b4a23':v<(ratio()?100:0)?'#245b77':'#667a6d';
  const texto=v=>P.num(v)?(ratio()?P.fmt(v,1)+' por 100 moradores 16+':P.signed(v,' pp')):'Sem comparação';
  function instalar(){for(const[k,[nome,campo]]of Object.entries(specs)) S.meta.camadas[k]={nome,campo,grupo:'População × eleitorado · município',tipo:'municipal'};}
  function limpar(){request++;shown=false;if(layer)layer.clearLayers();document.body.classList.remove('camada-populacao');$('#tabela').classList.remove('pop-mapa-lista');}
  function legenda(){
    if(!ativo())return false;
    $('#camada-seletor').value=S.camada;
    $('#mapa-escala').replaceChildren(h('b',{},specs[S.camada][0]),h('span',{},ratio()?'Azul: abaixo de 100 · ferrugem: acima de 100':'Azul: menor parcela no TSE · ferrugem: maior parcela no TSE'),h('small',{},'Um ponto = município inteiro · cinza: sem comparação'));
    const exemplos=h('div',{class:'pop-legenda-circulos'},[50,100,150].map(v=>h('span',{},h('i',{style:`width:${raio(v)*2}px;height:${raio(v)*2}px`}),v+' por 100')));
    $('#legenda').replaceChildren(h('p',{},ratio()?'Área do círculo proporcional à razão: a referência de 100 moradores tem raio de 10 px. Menos inscritos ou votantes, círculo menor; mais, círculo maior. Raio limitado entre 2 e 48 px para legibilidade.':'Diferença de composição, em pontos percentuais: cadastro TSE 2026 menos população municipal 16+ do Censo 2022. Raio fixo; compare as cores e os valores.'),...(ratio()?[exemplos]:[]),
      h('p',{},'População 16+ estimada = total IBGE '+(data?.meta.ano_estimativa||'recente')+' × proporção de 16+ do Censo 2022. Hipótese de estrutura constante. PNAD disponível como referência estadual na ficha.'),
      h('p',{},'Filtros de escola, zona, chuva e horário não recortam população: estas camadas usam municípios inteiros. Estado, cidade, busca de município e distância ao centro municipal continuam disponíveis.'),
      h('p',{},'Razão acima de 100 não prova irregularidade. Datas, migração, domicílio eleitoral, limites municipais e cobertura precisam ser conferidos.'),
      h('a',{href:'assets/politize_se/populacao/municipios.csv',download:''},'Baixar base municipal completa (CSV)'));
    return true;
  }
  function abrir(m){
    const panel=P.render(m,data.meta,{compact:true});
    panel.append(h('p',{class:'pop-nota'},'Posição no mapa: '+m.coordenada_fonte));
    panel.append(h('p',{},h('a',{href:`politizese.html#uf=${m.uf}&mun=${m.mun}&visao=municipio`},'Explorar o município no Politize-se ↗')));
    if(window.innerWidth<980){$('#painel-corpo').replaceChildren(panel);$('#painel').hidden=false;document.body.classList.add('painel-aberto');$('#painel-corpo').scrollTop=0;$('#painel-fechar').focus({preventScroll:true});}
    else if(S.mapa)L.popup({maxWidth:560,minWidth:320,className:'popup-ficha'}).setLatLng([m.lat,m.lon]).setContent(panel).openOn(S.mapa);
  }
  function listaMunicipios(rows){
    const key=sort.key||specs[S.camada][1],dir=sort.dir;
    lista=rows.filter(m=>!S.buscaLista||normal(m.nome+' '+m.uf).includes(normal(S.buscaLista))).sort((a,b)=>{
      const x=a[key],y=b[key];if(x==null)return y==null?0:1;if(y==null)return -1;
      return (typeof x==='number'?x-y:String(x).localeCompare(String(y),'pt-BR'))*dir;
    });
    const pageSize=50,total=Math.max(1,Math.ceil(lista.length/pageSize));pagina=Math.min(pagina,total);
    $('#l-resumo').textContent=P.fmt(lista.length)+' municípios inteiros · página '+pagina+' de '+total;
    $('#l-raio-caixa').hidden=true;$('#tabela').classList.add('pop-mapa-lista');
    const columns=[['nome','Município'],[specs[S.camada][1],specs[S.camada][0]],['estimativa16','População 16+ estimada'],['eleitorado','Eleitorado'],['comparecimento1','Votaram 1º'],['comparecimento2','Votaram 2º']];
    $('#tabela thead').replaceChildren(h('tr',{},columns.map(([k,t])=>h('th',{scope:'col','aria-sort':key===k?(dir===1?'ascending':'descending'):'none'},h('button',{type:'button',onclick:()=>{sort={key:k,dir:key===k?-dir:-1};pagina=1;listaMunicipios(rows);}},t)))));
    $('#tabela tbody').replaceChildren(...lista.slice((pagina-1)*pageSize,pagina*pageSize).map(m=>h('tr',{},
      h('th',{scope:'row'},h('button',{type:'button',onclick:()=>abrir(m)},m.nome+' / '+m.uf)),
      h('td',{},texto(valor(m))),...['estimativa16','eleitorado','comparecimento1','comparecimento2'].map(k=>h('td',{},P.fmt(m[k]))))));
    $('#paginas').replaceChildren(h('button',{type:'button',disabled:pagina===1,onclick:()=>{pagina--;listaMunicipios(rows);}},'Anterior'),h('span',{},pagina+' / '+total),h('button',{type:'button',disabled:pagina===total,onclick:()=>{pagina++;listaMunicipios(rows);}},'Próxima'));
  }
  async function atualizar(enquadrar){
    const req=++request;shown=true;document.body.classList.add('camada-populacao');limparMarcadores();
    if(S.circulo){S.mapa.removeLayer(S.circulo);S.circulo=null;}if(S.alvo){S.mapa.removeLayer(S.alvo);S.alvo=null;}
    if(layer)layer.clearLayers();
    setStatus('Carregando a comparação municipal…');legenda();gravarHash();
    try{data=await P.dados();}catch{if(req===request)setStatus('Não foi possível carregar a população. Selecione a camada novamente para tentar.',true);return;}
    if(req!==request||!ativo())return;
    legenda();
    let rows=data.municipios.filter(m=>(!S.filtro.uf||m.uf===S.filtro.uf)&&(!S.filtro.mun||m.mun===S.filtro.mun)&&(!S.filtro.texto||normal(m.nome+' '+m.uf).includes(normal(S.filtro.texto))));
    if(S.centro)rows=rows.filter(m=>P.num(m.lat)&&P.num(m.lon)&&distanciaKm(S.centro.lat,S.centro.lon,m.lat,m.lon)<=S.raio);
    if(S.modo==='lista'){listaMunicipios(rows);setStatus(P.fmt(rows.length)+' municípios na comparação.');return;}
    if(!S.mapa){setStatus('Mapa indisponível; use Ver em lista.');return;}
    if(!layer)layer=L.layerGroup().addTo(S.mapa);
    const renderer=L.canvas({padding:.5}),coords=[];
    for(const m of rows){
      if(!P.num(m.lat)||!P.num(m.lon))continue;
      coords.push([m.lat,m.lon]);const v=valor(m);
      const mark=L.circleMarker([m.lat,m.lon],{renderer,radius:ratio()?raio(v):7,color:'#fff',weight:1,fillColor:cor(v),fillOpacity:.78,popMunicipio:m.mun,popValor:v});
      mark.bindTooltip(h('span',{},m.nome+' / '+m.uf,h('br'),texto(v)));mark.on('click',()=>abrir(m));layer.addLayer(mark);
    }
    if(enquadrar&&coords.length)S.mapa.fitBounds(coords,{padding:[25,25],maxZoom:10,animate:false});
    setStatus(P.fmt(rows.length)+' municípios · '+P.fmt(rows.filter(m=>P.num(valor(m))).length)+' com comparação · população e votação do município inteiro.');
  }
  const exportar=()=>{const a=h('a',{href:'assets/politize_se/populacao/municipios.csv',download:'populacao_eleitorado_municipios.csv'});document.body.append(a);a.click();a.remove();setStatus('CSV da base municipal completa, incluindo municípios fora do filtro atual.');};
  return {instalar,ativo,legenda,atualizar,limpar,exportar,raio,get mostrado(){return shown;},get layer(){return layer;}};
};
