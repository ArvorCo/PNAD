(function(){
var fichas={};
document.querySelectorAll('script.tips').forEach(function(no){
try{var d=JSON.parse(no.textContent);for(var k in d){fichas[k]=d[k];}}catch(e){}});
if(!Object.keys(fichas).length)return;

var caixa=document.createElement('div');
caixa.id='tip';caixa.setAttribute('role','status');caixa.hidden=true;
document.body.appendChild(caixa);
var atual=null;

function fecha(){
if(!atual)return;
atual.classList.remove('on');
var fig=atual.closest('.fig');if(fig)fig.classList.remove('lendo');
atual=null;caixa.classList.remove('on');
setTimeout(function(){if(!atual)caixa.hidden=true;},140);}

function posiciona(alvo){
var r=alvo.getBoundingClientRect();
var c=caixa.getBoundingClientRect();
var margem=12;
var x=r.left+r.width/2-c.width/2;
x=Math.max(margem,Math.min(x,window.innerWidth-c.width-margem));
var y=r.top-c.height-14;
if(y<margem)y=Math.min(r.bottom+14,window.innerHeight-c.height-margem);
caixa.style.left=Math.round(x)+'px';
caixa.style.top=Math.round(Math.max(margem,y))+'px';}

function abre(alvo){
var chave=alvo.getAttribute('data-k');
var html=fichas[chave];
if(!html)return;
if(atual===alvo){posiciona(alvo);return;}
fecha();
atual=alvo;
alvo.classList.add('on');
var fig=alvo.closest('.fig');if(fig)fig.classList.add('lendo');
caixa.innerHTML=html;
caixa.hidden=false;
posiciona(alvo);
requestAnimationFrame(function(){caixa.classList.add('on');});}

function alvoDe(ev){
var no=ev.target;
return no&&no.closest?no.closest('.hit'):null;}

document.addEventListener('pointerover',function(ev){
if(ev.pointerType==='touch')return;
var alvo=alvoDe(ev);
if(alvo)abre(alvo);else if(atual&&!ev.target.closest('#tip'))fecha();});

document.addEventListener('pointerdown',function(ev){
var alvo=alvoDe(ev);
if(alvo){abre(alvo);}else{fecha();}});

document.addEventListener('keydown',function(ev){if(ev.key==='Escape')fecha();});
window.addEventListener('scroll',function(){if(atual)posiciona(atual);},{passive:true});
window.addEventListener('resize',fecha);
})();