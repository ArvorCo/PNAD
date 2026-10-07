"""Prosa fixa da página: não depende de nenhum número calculado.

Os únicos números aqui são os da lei (49, 54, 81, dois terços, três quintos) e
datas públicas. Cada aula traz uma analogia doméstica. Presunção de inocência em
toda frase: o estágio processual é sempre o do documento de origem.
"""

from __future__ import annotations


def aula_estagios() -> str:
    """O que cada estágio processual quer dizer, do boato à condenação."""
    return """<h3>Aula 1. Do boato à condenação: o que cada palavra quer dizer</h3>
<p>Quem lê manchete confunde seis coisas diferentes. Todas aparecem como "senador alvo do STF", e nenhuma é igual à outra. A ordem abaixo é a ordem em que um caso costuma andar.</p>
<ol>
<li><b>Notícia-crime.</b> Qualquer pessoa pode levar um fato ao Ministério Público ou ao tribunal. Não prova nada e não abre, sozinha, uma investigação.</li>
<li><b>Inquérito.</b> A investigação formal. No Supremo, é aberto por decisão de um ministro relator, em geral a pedido da Procuradoria-Geral da República (PGR) ou da Polícia Federal (PF). Investigado é quem está sendo apurado, ainda sem acusação.</li>
<li><b>Indiciamento pela PF.</b> A polícia fecha o relatório e aponta quem, no entender dela, cometeu o quê. É opinião de investigador, não acusação. Quem acusa é a PGR.</li>
<li><b>Denúncia da PGR.</b> Acusação formal. Ainda não há processo: o tribunal precisa aceitar.</li>
<li><b>Recebimento da denúncia e condição de réu.</b> Quando o colegiado recebe a denúncia, abre-se a ação penal e o acusado passa a réu. Réu não é condenado. O julgamento do mérito vem depois, com defesa e provas.</li>
<li><b>Condenação.</b> Decisão de mérito. Só vale como definitiva quando não cabe mais recurso, e a lei trata o efeito sobre o mandato de forma própria.</li>
</ol>
<p>Há ainda os finais sem condenação. <b>Arquivamento</b> é o encerramento do caso, em regra a pedido da PGR e atendido pelo relator. <b>Trancamento</b> é a ordem judicial que encerra uma investigação ou ação por falta de justa causa. <b>Absolvição</b> é decisão de mérito a favor do réu. Esses casos ficam registrados na página, com peso pequeno na régua, e aparecem por inteiro no anexo.</p>
<div class="analogy"><strong>Analogia.</strong> Pense numa reclamação de condomínio. Um vizinho escreve ao síndico (notícia-crime). O síndico abre uma apuração e pede as imagens da portaria (inquérito). O zelador resume o que viu e aponta um morador (indiciamento). A assembleia decide se a acusação vai a votação (denúncia e recebimento). Só então há julgamento. Estar na apuração não é ter sido multado.</div>
<h3>Investigado não é culpado</h3>
<p>A página escreve "investigado", "indiciado", "réu" e "condenado" exatamente como no documento de origem, nunca com palavra mais forte. Presunção de inocência vale para todos os partidos e para todos os campos. Um inquérito pode terminar em arquivamento, em denúncia ou em nada. Por isso a régua dá a cada estágio um peso diferente e dá peso pequeno ao arquivado.</p>
<h3>Foro por prerrogativa de função</h3>
<p>Deputados federais e senadores respondem a crimes comuns no Supremo Tribunal Federal. A regra vale, em geral, para fatos ligados ao mandato. Quem passa da Câmara para o Senado continua parlamentar federal, e o caso em curso tende a seguir no STF, porque a prerrogativa é a mesma. Por isso há processos com relator de ministro do Supremo sobre pessoas que ainda eram deputadas ou deputados quando o fato foi investigado. Quem decide o foro de cada caso é o tribunal, e a ficha de cada senador registra o foro informado na fonte.</p>
"""


def aula_rito() -> str:
    """Como um impeachment de ministro do STF e uma PEC andam no Senado."""
    return """<h3>Aula 2. Dois caminhos, duas contas: PEC e impeachment</h3>
<p>A discussão pública mistura duas coisas. Uma é mudar a Constituição para limitar o Supremo. Outra é afastar um ministro. Cada uma tem rito próprio, e o número de votos que importa é diferente.</p>
<h3>Impeachment de ministro do STF</h3>
<p>O rito está na Lei 1.079/1950. Os artigos 41 a 44 tratam da denúncia contra ministro do Supremo: qualquer cidadão pode apresentá-la ao Senado, com assinatura reconhecida e provas ou indicação de onde estão. O <b>presidente do Senado</b> funciona como porteiro: é ele quem recebe a denúncia e decide se a encaminha. Se encaminha, uma comissão especial a examina, e o plenário vota se aceita ou não a acusação. Aceita, o ministro é afastado do cargo e o julgamento vem depois. Para condenar, a Constituição exige <b>dois terços</b> dos senadores, ou seja, 54 dos 81 votos.</p>
<p>O ponto novo está na porta de entrada. A ADPF 378, de 2015, fixou o rito do processo contra a presidente da República. Em dezembro de 2025, o ministro Gilmar Mendes concedeu uma liminar que exige dois terços já na <b>admissibilidade</b> da denúncia contra ministro do Supremo. Pela redação original da lei, a admissão se decidia por maioria simples. Com a liminar, os 54 votos valem desde o início, e não só no julgamento final. A decisão é monocrática e pode ser revista pelo plenário do STF, e a página trata os 54 como a exigência em vigor na data de corte.</p>
<h3>PEC que limite o Supremo</h3>
<p>Uma proposta de emenda à Constituição precisa de <b>três quintos</b> dos senadores, 49 dos 81, em dois turnos de votação. Antes de chegar ao plenário, passa pela Comissão de Constituição e Justiça. A pauta é do presidente do Senado, o que reforça o papel de porteiro.</p>
<div class="analogy"><strong>Analogia.</strong> A PEC é mudar o estatuto do condomínio: precisa de quórum alto, mas vale para todos e para sempre. O impeachment é destituir um conselheiro: precisa de quórum ainda maior, vale para uma pessoa e depende de alguém abrir a pauta. Quem tem 49 pessoas dispostas a mudar o estatuto não tem automaticamente 54 para destituir alguém.</div>
<h3>Por que 49 e 54 são contas diferentes</h3>
<p>A régua de contrapeso (C) é medida separadamente para cada alvo. O senador que assina uma PEC de limitação pode hesitar em afastar um ministro, e o contrário também acontece. O quórum para o impeachment é mais alto e começa antes. A conta de 54 é sempre mais difícil que a de 49, e a página nunca soma as duas.</p>
"""


def o_que_nao_e() -> str:
    """O que K e C não são."""
    return """<h3>O que esta página não afirma</h3>
<p>Quatro leituras erradas aparecem sempre que um número desses circula. A página as descarta antes de qualquer gráfico.</p>
<ul>
<li><b>K não é culpa e não é chantagem.</b> K mede quanto procedimento judicial está documentado contra o senador, com peso por estágio. Um K alto diz que há muito processo, não que há crime. A hipótese de que o Supremo teria "poder de picar" quem é investigado é uma pergunta, e a página a testa; não a assume.</li>
<li><b>C não é previsão de voto.</b> C mede sinais públicos de contrapeso: voto nominal, assinatura de pedido, fala, projeto. Um C alto é um histórico, não um compromisso. A simulação trata C como probabilidade com incerteza, e a incerteza aparece junto.</li>
<li><b>"Nada localizado" não é certidão negativa.</b> K igual a zero quer dizer que nada foi encontrado nas fontes desta pesquisa, na data de corte. Processo sob sigilo, caso recente e erro de busca ficam de fora.</li>
<li><b>O post de Andreza Matais é a origem da pergunta, não a tese.</b> A página começa nele porque a pergunta é boa e testável. O resultado pode confirmar, reduzir ou contrariar o que o post sugere, e o achado contrário vem com o mesmo destaque.</li>
</ul>
<div class="analogy"><strong>Analogia.</strong> K é o número de multas no prontuário do motorista; C é quantas vezes ele já reclamou do radar. Nenhum dos dois diz se ele vai passar no sinal vermelho amanhã.</div>
<p>As escolhas editoriais da casa, como a classificação de campo de cada partido, estão declaradas no JSON de cada senador, com justificativa quando fogem da regra.</p>
"""


def como_ler_ficha() -> str:
    """Guia curto para ler uma ficha de senador."""
    return """<h3>Como ler uma ficha</h3>
<p>Cada um dos 81 senadores tem uma ficha com a mesma ordem de leitura. O cabeçalho mostra nome, partido, estado e dois medidores. O medidor K é o peso do procedimento judicial; o medidor C é o contrapeso. Os dois são lidos de 0 a 100 e nunca se somam.</p>
<ol>
<li><b>Casos.</b> Cada caso traz o selo do estágio processual exatamente como na fonte, o foro, o relator e a data da última decisão. O selo é palavra do documento, não nossa.</li>
<li><b>Defesa.</b> Quando a defesa se manifestou, o texto está ali. Sem manifestação, a ficha diz que não foi localizada nesta pesquisa.</li>
<li><b>Sinais de contrapeso.</b> Voto na PEC 8/2021, assinatura de pedido, declaração. Cada sinal tem data e fonte.</li>
<li><b>Fontes.</b> Cada link diz se a página foi aberta e lida, se só o resumo do buscador foi visto, ou se o dado veio de relatório anterior sem reabertura. A confiança da ficha depende disso.</li>
</ol>
<div class="analogy"><strong>Analogia.</strong> A ficha é a etiqueta de um alimento: ingredientes (casos), quem fabricou (fonte), validade (data) e aviso de alergia (limites). A etiqueta não diz se o prato é bom.</div>
<p>Uma ficha sem casos mostra K igual a zero e diz "nada localizado". Uma ficha com confiança baixa tem sinais poucos ou fontes só de busca, e a probabilidade dela tem margem maior.</p>
"""


def checklist_leitor() -> str:
    """Seis perguntas para ler manchete de 'bancada do impeachment'."""
    return """<h3>Seis perguntas antes de repetir uma manchete de "bancada do impeachment"</h3>
<p>Qualquer contagem de senadores a favor ou contra o Supremo pode ser lida com as mesmas seis perguntas. Se a manchete não responde a elas, o número vale menos do que parece.</p>
<ol>
<li><b>Qual é o alvo?</b> PEC (49 votos, três quintos, dois turnos) ou impeachment (54 votos, dois terços)? Contagens de uma não valem para a outra.</li>
<li><b>Quem está na lista?</b> Só os senadores com mandato em 2027, incluindo os eleitos em 2026, ou também os que saem em janeiro? Suplente conta?</li>
<li><b>O que conta como "a favor"?</b> Voto nominal, assinatura, declaração ou palpite de bastidor? Cada um tem peso e confiança diferentes.</li>
<li><b>Há inquérito, denúncia ou condenação?</b> Investigado, indiciado, réu e condenado são estágios diferentes, e a palavra da manchete precisa ser a do documento.</li>
<li><b>Qual é a data e qual é a fonte?</b> Uma contagem de agosto não descreve outubro. Link para o documento, e não só para a matéria que o cita, é o mínimo.</li>
<li><b>Quem decide a pauta?</b> Com 49 ou 54 votos no papel, ainda falta o presidente do Senado abrir a votação e, no impeachment, a admissibilidade com dois terços já na porta.</li>
</ol>
<div class="analogy"><strong>Analogia.</strong> É como conferir o troco: antes de dizer que a conta está certa, veja o valor, a nota, o preço de cada item e se a máquina estava ligada. Uma pergunta sem resposta é um item sem preço.</div>
<p>A página responde às seis para cada número que publica. Onde não consegue responder, diz qual documento resolveria.</p>
"""
