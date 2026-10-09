/* Contagem contínua, antes do arredondamento; espelho de reponderacao-contagem.py. */
(function(global) {
  'use strict';
  function counts(result,base) {
    const total=base.total;
    if(!Number.isFinite(total) || total<=0) throw Error('Eleitorado precisa ser finito e positivo');
    const out=Object.fromEntries(Object.entries(result.por_100_eleitores).map(([k,v])=>[k,total*v/100]));
    out.eleitorado=total;
    out.validos=out.flavio+out.lula;
    out.comparecimento=out.validos+out.branco_nulo;
    out.diferenca_flavio_lula=out.flavio-out.lula;
    return out;
  }
  const api={counts};
  if(typeof module!=='undefined' && module.exports) module.exports=api;
  if(global) global.ReponderacaoContagem=api;
})(typeof window!=='undefined'?window:null);
