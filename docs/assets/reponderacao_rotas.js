/* Preserva links antigos depois da separação dos turnos e do diário. */
(() => {
  const archive='reponderacao_pnad_1o_turno_2026.html';
  const first=new Set(['primeiro-turno','primeiro-turno-chart','institutos-1t','palver-pesos','comparar-metodos','futura-perfil-pnad','janela-1t','grupos-primeiro-turno','selecao-primeiro-turno','nao-escolha-1t']);
  function route() {
    const id=location.hash.slice(1);
    if(!id || id.startsWith('sim=')) return;
    const target=document.getElementById(id);
    if(target) {
      let opened=false;
      for(let node=target;node;node=node.parentElement) {
        if(node.tagName==='DETAILS' && !node.open){node.open=true;opened=true;}
      }
      if(opened) requestAnimationFrame(()=>target.scrollIntoView({block:'start'}));
      return;
    }
    if(id==='atualizacao') location.replace('reponderacao_pnad_log.html#atualizacao');
    else if(first.has(id) || id.startsWith('pesquisa-') || id.startsWith('ficha-')) location.replace(archive+'#'+encodeURIComponent(id));
  }
  window.addEventListener('hashchange',route);route();
})();
