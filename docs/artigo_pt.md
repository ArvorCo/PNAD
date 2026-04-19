# o brasil auditável: um retrato em quinze fotografias

> Ensaio escrito a partir dos microdados da PNAD Contínua anual, visita 5, do IBGE, com base na edição 2026-03 do pacote público tratado neste repositório. Todas as estatísticas citadas provêm, salvo nota em contrário, do arquivo `base_labeled_npv.csv` processado pelo `brasil pipeline-run` e conferidas no `brasil.sqlite`. Os números-chave, em salários mínimos equivalentes, são o núcleo duro deste texto; ao redor deles, a leitura é minha.

---

# parte 1 — o país partido ao meio

## abertura

Há um país em que um homem, ao nascer em Águas Claras, tem probabilidade estatística de crescer em domicílio cuja renda equivale a 5,53 salários mínimos; o mesmo homem, se nascido em Bacabal, cresce em domicílio que mal ultrapassa 2,05 salários. Ambos falam português. Ambos recebem o mesmo Bolsa Família quando a renda despenca. Ambos cantam o hino nacional segurando o peito com a mesma ingenuidade cívica. E, no entanto, entre um e outro escorre o equivalente a dois Brasis e meio. A criança do cerrado e a criança do sertão convivem sob a mesma Constituição; não convivem sob a mesma economia.

O leitor apressado dirá que isto é velho. Ledo engano. O que os microdados da PNAD Contínua anual, visita 5, permitem fazer agora, pela primeira vez numa escala aberta e reprodutível, é ver a desigualdade em resolução fina, estado por estado, faixa de salário mínimo por faixa de salário mínimo, cor por cor, escolaridade por escolaridade, e ver quem paga o quê e quem recebe o quê. Os 200 pesos replicados de bootstrap do IBGE, que este repositório carrega por padrão, tornam o cálculo do erro amostral trivial. Em outras palavras: o Brasil nunca esteve tão auditável, e, talvez por isso mesmo, tenha-se tornado tão desconfortável.

## o dado que não querem ver

O coeficiente de Gini anual calculado sobre a renda domiciliar per capita, considerando todos os rendimentos habituais, fecha em 0,520 na edição 2026-03 da pesquisa. O número oficial divulgado pelo IBGE para 2024 sobre a renda per capita, como se verá, é um pouco mais baixo, 0,506, e o Instituto gosta de celebrá-lo como [o menor da série iniciada em 2012](https://agenciadenoticias.ibge.gov.br/agencia-noticias/2012-agencia-de-noticias/noticias/43302-rendimento-per-capita-e-recorde-e-desigualdades-caem-ao-menor-nivel-desde-2012). A diferença metodológica é conhecida: o conceito de rendimento domiciliar e a inclusão dos benefícios sociais puxam para baixo o coeficiente na leitura oficial. Na leitura usada neste ensaio, que pondera rendimentos habituais de todos os trabalhos com pesos de expansão e replicados para intervalo de confiança, o número é 0,520. Ambos contam a mesma história sombria, apenas em tons diferentes.

Para efeito de comparação: Portugal tem Gini em torno de 0,33; Alemanha, 0,30; Estados Unidos, 0,40. Não há país desenvolvido com Gini superior a 0,45. O Brasil está em 0,52. O que se celebra como conquista histórica é a passagem da desigualdade absurda para a desigualdade somente abominável.

A renda domiciliar per capita média, convertida em múltiplos de salário mínimo de referência, é de 3,62 SM. A mediana é brutalmente mais baixa. A concentração é tão esquelética que 40,6 por cento da população vive em domicílios com renda per capita de até dois salários mínimos e apenas 6,5 por cento alcançam a faixa de dez salários mínimos ou mais. Se o leitor está lendo este texto em tela alta, num aparelho razoável, numa sala ventilada, é estatisticamente provável que pertença à minoria superior dessa curva, e convém que reconheça, sem pieguice, a anomalia sociológica em que flutua.

## o método

Este ensaio trabalha com a PNAD Contínua anual, visita 5, do IBGE, que é a fotografia anual mais densa que o Estado brasileiro tira de si mesmo. Cobre cerca de 211.370 domicílios, 538 mil pessoas, e inclui, entre outras variáveis, rendimentos habituais e efetivos, estrutura familiar, escolaridade, cor ou raça, formalidade do vínculo, metropolitanidade e os pesos para inferência populacional. Não se trata de um censo, mas o desenho amostral é suficientemente robusto para inferências estaduais, e os 200 pesos replicados permitem estimativas de incerteza, algo raro em debate público brasileiro.

As bandas de renda, neste texto, obedecem à tradição do IBGE e do DIEESE: 0 a 2 salários mínimos, 2 a 5, 5 a 10, 10 ou mais. O deflator é o IPCA mensal até o mês de referência da pesquisa; o salário mínimo de referência é o do mês-alvo. Toda comparação entre estados e entre anos está, portanto, blindada contra os efeitos mais grosseiros da inflação. Onde houver diferença entre o que este repositório calcula e o que o IBGE divulga em suas tabelas oficiais, o repositório está documentando sua metodologia em público; qualquer leitor pode conferir, reproduzir e, se for o caso, desmentir. É o oposto da opacidade.

Está dito, em prosa: o que vem a seguir não é jornalismo de indignação. É jornalismo de aritmética. E a aritmética, quando se permite ser lida, costuma ser mais feroz do que qualquer editorial.

---

# parte 2 — brasília, ilha privilegiada

## 5,53 salários mínimos

O Distrito Federal aparece, na PNADC anual 2024, com rendimento domiciliar per capita médio equivalente a 5,53 salários mínimos, segundo o corte calculado a partir do pacote processado neste repositório. Nenhum outro ente federativo chega perto. Em dinheiro, a leitura oficial do IBGE traduz a mesma coisa: [R$ 3.444 de renda per capita no DF contra R$ 1.077 no Maranhão](https://agenciadenoticias.ibge.gov.br/agencia-sala-de-imprensa/2013-agencia-de-noticias/releases/42761-ibge-divulga-rendimento-domiciliar-per-capita-2024-para-brasil-e-unidades-da-federacao), razão de 3,2 vezes a favor da capital; em rendimento médio de todos os trabalhos, o DF supera os R$ 5.043 contra R$ 2.049 do Maranhão, uma distância de mais de [duas vezes e meia](https://www.dgabc.com.br/Noticia/4203759/rendimento-medio-real-foi-maior-em-2024-no-df-sp-e-parana-aponta-ibge). Qualquer corte que se faça — média, mediana, P90, P50 —, o resultado é o mesmo: Brasília é uma ilha.

O que a distingue, na decomposição da renda, não é o empreendedorismo. É o funcionalismo. A composição da renda do DF é dominada pelo trabalho assalariado, mas o pagador majoritário desse trabalho, direta ou indiretamente, é o próprio Estado: Executivo federal, autarquias, estatais, tribunais, órgãos de controle, Legislativo, forças armadas, segurança e o ecossistema de terceirizados, consultores, advogados, lobistas e fornecedores que orbita a máquina pública. O DF não produz soja, minério, aço, calçados, aviões, suco de laranja ou celulose. Produz pareceres, ofícios, audiências, despachos, leis e gratificações. A renda de Brasília é, rigorosamente, o custo do Leviatã brasileiro visto no recibo.

## o cinturão do concurso

Há uma classe social no Brasil que dispensa nome em português: é a aristocracia do concurso. Sua topografia está inteira no DF. No Lago Sul, segundo reportagem da [Gazeta do Povo](https://www.gazetadopovo.com.br/economia/ricos-brasil-bairro-nobre-brasilia-ranking/), a renda média chega a R$ 23 mil e, entre declarantes, a R$ 38,4 mil; se fosse município independente, seria o mais rico do país. O Lago Sul é praticamente um bairro de servidores federais. O Sudoeste, a Asa Sul, Águas Claras, Lago Norte repetem o padrão em gradações decrescentes.

Enquanto isso, a renda dos 1 por cento mais ricos do país está, em sua maior parte, ancorada no funcionalismo: apenas 1 por cento da população brasileira, segundo o Centro de Liderança Pública citado pela [Gazeta do Povo](https://www.gazetadopovo.com.br/economia/supersalarios-so-1-da-populacao-tem-renda-igual-ou-superior-ao-teto-do-funcionalismo/), tem renda igual ou superior ao teto do funcionalismo, que em 2026 é de R$ 46.366,19. Isso significa que pertencer ao topo do Estado, no Brasil, é um feito estatisticamente raro, porém concentrado geograficamente num pedaço de cerrado planejado por Niemeyer. Há CEPs em Brasília onde a probabilidade de você ganhar acima do teto é de dezenas de por cento; em Balsas, Maranhão, essa probabilidade é rigorosamente microscópica.

Não há nada de errado em remunerar o serviço público. Há algo de profundamente errado em remunerá-lo como se a ele devêssemos, coletivamente, uma espécie de renda mínima aristocrática.

## como se financia

Todo o mecanismo acima é financiado por três fontes. A primeira é tributação, concentrada em São Paulo, Minas Gerais, Rio Grande do Sul, Paraná e Santa Catarina. A segunda é dívida pública, ou seja, poupança das gerações futuras, intermediada por bancos brasileiros e estrangeiros. A terceira é emissão monetária disfarçada, no limite do que o Banco Central permite antes que a inflação retorne. Ou seja: Brasília vive da extração fiscal do Sudeste-Sul, do endividamento dos filhos e da erosão silenciosa do poder de compra dos pobres. Quando um ministro do STF recebe mais de R$ 3 milhões em doze meses, como revelaram [levantamentos da Transparência Brasil e da República.org](https://www.poder360.com.br/poder-justica/stf-autoriza-penduricalhos-com-limite-de-35-acima-do-teto/), esses três milhões não caem do céu. Caem do contracheque de um torneiro mecânico em São Bernardo, das prestações atrasadas de um pequeno agricultor em Cascavel e da mordida que o IPCA dá na conta de luz de uma doméstica em Fortaleza.

O Judiciário brasileiro, em particular, transformou-se em setor econômico à parte. Magistrados receberam [R$ 10,7 bilhões acima do teto constitucional em 2025](https://www.painelpolitico.com/p/penduricalhos-do-judiciario-stf-limita); 98 por cento dos juízes estaduais receberam extrateto; um em cada quatro ultrapassou o próprio teto em mais de R$ 1 milhão por ano. Quando, finalmente, em março de 2026, o STF decidiu por limitar os penduricalhos a 35 por cento do teto, o teto prático da remuneração subiu para cerca de [R$ 78,8 mil mensais](https://sintrajud.org.br/conteudo/16064/decisao-do-stf-cria-teto-de-r-78-mil-para-juizes-e-legaliza-penduricalhos), legalizando por decisão do próprio Supremo o que antes se fazia contra a Constituição. A economia prometida, R$ 7,3 bilhões ao ano, é inferior ao que ainda se gastará com os mesmos benefícios. Chama-se a isso, em Brasília, ajuste.

O DF, portanto, não é um acidente da geografia política. É uma máquina de transferência. A 5,53 SM per capita dos brasilienses está escrita, com tinta invisível, no contracheque de cada brasileiro de fora de Brasília.

---

# parte 3 — o maranhão como espelho

## 2,05 salários mínimos

No outro extremo do país, o Maranhão aparece, na mesma PNADC anual, com 2,05 salários mínimos de renda domiciliar per capita. O número é tão baixo que, quando comparado ao DF, rende a razão de 2,7 vezes. O Maranhão não é anomalia. É mediana do Nordeste rural: Ceará, Piauí, Alagoas e Paraíba caminham ombro a ombro. A região que concentra 27 por cento da população brasileira concentra cerca de 41 por cento dos indivíduos nos domicílios das faixas mais baixas de renda.

Na distribuição interna do Maranhão, aproximadamente 76 por cento da população vive em domicílios com renda per capita de até dois salários mínimos. Essa não é uma fotografia de pobreza marginal. É a foto do estado inteiro. Não há ilha. É oceano. Um contingente comparável ao da população de Portugal, lá concentrado, vive com renda per capita próxima ou inferior à linha convencional de vulnerabilidade.

## dependência estrutural

O estado, claro, tem PIB. Tem alumínio em São Luís, porto em Itaqui, soja no sul, pecuária no oeste. Mas, medida pela renda efetivamente apropriada pelas famílias, a economia maranhense vive de transferências federais: aposentadorias rurais do INSS, Bolsa Família, BPC, pagamentos de servidores estaduais e municipais e a operação de folha do próprio Executivo estadual. Em muitos municípios, a soma de prefeitura e benefícios sociais supera com folga o que a iniciativa privada movimenta.

Ao IBGE, [cabe a observação técnica](https://bancadadonordeste.com.br/post/2025/12/25/81423-ibge-diz-que-o-indice-gini-de-desigualdade-seria-75-maior-sem-os-beneficios-de-programas-sociais-em-2024): sem os benefícios sociais, o Gini nordestino seria 16,4 por cento maior. A frase, benigna na superfície, é sinistra quando se lê no sentido oposto: a economia do Nordeste, descontada a transferência estatal, revela uma miséria ainda mais profunda do que a que se vê. Os programas sociais não substituem a economia que falta; camuflam. O Nordeste, hoje, não é pobre apenas porque o governo transfere renda; é pobre porque, apesar da transferência de renda, ainda há miséria de sobra.

## cultura da transferência

O mais incômodo, porém, não é o dado; é o sistema político que ele alimenta. O Brasil se acostumou à ideia, repetida à exaustão por governos do PT, de que o Nordeste é um "laboratório social". É um laboratório, mas o experimento é outro: testou-se, por duas décadas, se a transferência de renda sem contrapartida produtiva é capaz de soerguer a região. O resultado está no próprio Gini: cai, mas só até o ponto em que a assistência substitui a ocupação. O trabalhador maranhense jovem, homem, do interior, entrou em fila para programas, não para fábricas, porque não há fábricas. Esta é uma falha de política industrial, não de caráter. Falar em vagabundismo nordestino é ignorar a arquitetura de incentivos desenhada em Brasília.

Como lembrou o estudo do FGV-IBRE, amplamente citado na mídia, metade das famílias beneficiárias do Bolsa Família deixou de procurar emprego, com especial incidência entre homens jovens do Norte e Nordeste. O mecanismo é trivial: o trabalho informal pago na região compete com a transferência federal, e muitas vezes perde. O resultado não é indolência; é decisão racional. O trabalhador faz a conta. O que precisa ser refeito é a conta do Estado.

A consequência eleitoral é conhecida: Lula obteve 69,34 por cento dos votos válidos do Nordeste no segundo turno de 2022, venceu nos nove estados da região e em 1.774 municípios, ganhando a eleição presidencial com o que sobrou de todo o restante do país contra ele. Correlações não são causalidade, mas nos [municípios de maior cobertura do Auxílio Brasil o petismo alcançou 71 por cento dos votos, contra 24 por cento de Bolsonaro](https://www.cnnbrasil.com.br/politica/nordeste-e-a-unica-regiao-em-que-lula-obteve-mais-votos-que-bolsonaro-confira/). Não é coincidência. É a máquina funcionando como projetada.

O Nordeste, espelho, devolve ao país a imagem daquilo em que o assistencialismo, convertido em política de Estado, se transforma quando se confunde com estratégia eleitoral.

---

# parte 4 — o motor que carrega o país

## o sul que produz

Há três estados no Brasil cuja renda domiciliar per capita, em salários mínimos, ultrapassa 4: São Paulo, Santa Catarina e Paraná. Somados ao Rio Grande do Sul e a parte de Minas Gerais, respondem por mais de metade do PIB nacional. A correlação, que deveria ser banal, é incômoda: os estados que mais produzem são os que menos dependem de transferência federal. Os que mais concentram riqueza são, ironicamente, os mais críticos ao sistema que a reparte. Não é coincidência. É diagnóstico.

Santa Catarina, o caso mais emblemático, cresceu 5,3 por cento em 2024, o [segundo maior aumento em dez anos](https://www.seplan.sc.gov.br/pib-de-santa-catarina-cresce-53-em-2024-o-segundo-maior-aumento-em-10-anos/), enquanto a média nacional foi de 3,4 por cento. O PIB per capita catarinense atingiu R$ 61.274, o quinto maior do país, 25,2 por cento acima da média nacional. Em 2002, era 15,5 por cento acima. Em duas décadas, portanto, Santa Catarina ganhou posição na distribuição nacional de produtividade. A indústria de transformação cresceu 7,7 por cento; as atividades turísticas, 9 por cento; o comércio, 7,2 por cento. Não há milagre. Há matriz empresarial diversificada, tradição industrial, capital humano, infraestrutura portuária, ética do trabalho herdada da imigração alemã e italiana e, sobretudo, uma prefeitura em Joinville, uma em Blumenau, uma em Jaraguá que não parece ter sido projetada para servir a seus próprios servidores.

## são paulo e a sobrecarga

São Paulo é outro fenômeno. Sozinho, responde por cerca de um terço do PIB brasileiro. Tem o maior parque industrial da América Latina, o maior porto do hemisfério sul, a maior aglomeração financeira do país, o maior conjunto de universidades e centros de pesquisa e, ainda assim, recebe de volta em gastos federais uma fração menor do que paga em tributos. É doador líquido da federação. O contribuinte paulista paga o funcionalismo maranhense, o aumento do STF e a prefeitura de Altamira sem ter, em troca, nada que se aproxime de representação proporcional no Estado que financia.

O fenômeno é conhecido como [compensação federativa](https://www.gazetadopovo.com.br/economia/funcionalismo-publico-federal-recorde-despesas-outubro/) e funciona como uma transferência invisível. O paulista a tolera porque, em geral, nem sabe que existe. Os jornais não gostam de falar do assunto; os políticos paulistas, quando se candidatam a nível federal, preferem falar de qualquer outra coisa. O resultado é que a região que poderia funcionar como Singapura da América do Sul é tratada como frigorífero do Tesouro, drenada de recursos para manter, do outro lado do Brasil, estruturas de poder que lhe são indiferentes quando não hostis.

## indústria e produtividade

No interior paulista há uma descoberta silenciosa: a produtividade agrícola, industrial e de serviços converge. Ribeirão, Campinas, São José dos Campos, Sorocaba e São José do Rio Preto formam um cinturão em que o PIB per capita supera o de países inteiros. A cultura da cana evolui para a biotecnologia; a mecânica de precisão se mistura ao software; a cadeia aeronáutica em São José dos Campos continua exportando o que poucas economias do mundo exportam. É a parte do Brasil que ainda convida, sozinha, ao otimismo. Está lá. Funciona. Cumpre horário. Paga imposto. E carrega, nas costas, a diferença que separa o PIB formal brasileiro do PIB real da miséria nordestina.

Esse motor, contudo, já dá sinais de fadiga. A carga tributária brasileira, perto de 33 por cento do PIB, é a mais alta da América Latina. A reforma tributária aprovada em 2023 e em implementação gradual até 2033, com alíquotas combinadas de IBS e CBS projetadas entre 26,5 e 28 por cento, colocará o IVA brasileiro [entre os maiores do mundo](https://www.institutoliberal.org.br/blog/justica/a-vigente-reforma-tributaria-sem-confetes/), sete pontos acima da média da OCDE (19,3 por cento). O motor, que já cospe óleo, continuará a rodar com o tanque prensado. Até quando, é matéria de engenharia política, não de fé.

---

# parte 5 — a curva de lorenz e a mentira do "mais igual"

## leitura da curva

Se plotarmos a população brasileira em ordem crescente de renda domiciliar per capita no eixo horizontal e a fração acumulada da renda no eixo vertical, encontraremos a célebre curva de Lorenz. Num país perfeitamente igual, seria a diagonal; num país perfeitamente desigual, o canto inferior direito. No Brasil, a curva fica distante da diagonal em tal medida que o Gini, como dito, é 0,520 no corte metodológico deste repositório.

Para efeito didático: os 10 por cento mais ricos do país concentram aproximadamente metade da renda domiciliar, enquanto os 40 por cento mais pobres concentram menos de 10 por cento. O IBGE, em sua leitura oficial, [celebra](https://www.cnnbrasil.com.br/economia/macroeconomia/ibge-renda-per-capita-tem-recorde-de-r-2-020-em-2024-desigualdade-cai-a-piso-historico/) que a razão entre topo e base caiu para 13,4 vezes em 2024, a menor desde 2012. É verdade. Mas 13,4 vezes ainda é uma distância que, em países da OCDE, classificaria o Brasil como caso clínico.

## comparação internacional

Portugal tem Gini na casa de 0,33. Alemanha, 0,30. Espanha, 0,34. França, 0,32. Itália, 0,36. Canadá, 0,33. Mesmo os Estados Unidos, frequentemente citados como país muito desigual, operam em torno de 0,40. O Brasil, em 0,52, não pertence à categoria das economias avançadas. Pertence à família das economias extrativas, onde uma parte pequena da sociedade extrai renda da parte grande por meio de mecanismos que variam de país para país mas que, no caso brasileiro, se chamam carga tributária regressiva, juros altos, proteção ao incumbente, inflação recorrente, baixa produtividade educacional e funcionalismo de primeira classe.

A razão P90 sobre P10 da renda domiciliar per capita, no Brasil, está próxima de 10. Isso significa que o domicílio no nonagésimo percentil ganha dez vezes o que ganha o domicílio no décimo percentil. Na OCDE, essa razão oscila entre 3 e 5. O Brasil é, em termos práticos, duas Suécias empilhadas: a de cima, funcionando; a de baixo, comprimida debaixo do peso da de cima.

## P90/P10

A leitura granular é pior. Na faixa de 10 SM ou mais, entram 6,5 por cento da população. Na faixa de 0 a 2 SM, entram 40,6 por cento. Entre esses extremos, a distribuição tem cauda longa para a direita — isto é, dentro dos 6,5 por cento do topo, há diferenças enormes entre médicos de família e ministros do STF, entre donos de empresa no interior e herdeiros de fortunas centenárias. Mas o buraco está na base. A massa de 40 por cento que vive em até dois salários mínimos é o que define o país. Qualquer projeto político que ignore essa massa, falha eleitoralmente; qualquer projeto político que dependa de mantê-la onde está, falha civilizatoriamente.

A mentira do "mais igual", portanto, é uma mentira de olhar curto. Sim, o Gini caiu. Sim, a renda subiu. Mas o patamar continua selvagem, e o mecanismo que o aliviou é também o mecanismo que o perpetua: a transferência federal financiada por tributo regressivo e dívida. Corte o transfer, revela-se a miséria. Corte o tributo regressivo, revela-se a inviabilidade do transfer. O Brasil vive no equilíbrio instável entre os dois cortes.

---

# parte 6 — a pirâmide etária e o fim do bônus demográfico

## envelhecimento

Até 2000, a pirâmide etária brasileira ainda tinha base larga: muita criança, poucos idosos. Em 2024, a mesma pirâmide mostra afunilamento da base e alargamento do meio e do topo. A idade mediana saltou de 28 anos em 2000 para 35 em 2023, com projeção de [48 anos em 2070](https://projetocolabora.com.br/ods11/brasil-tera-quase-70-milhoes-de-idosos-em-2050/). Em 2050, 30 por cento da população terá mais de 60 anos. O Brasil estará velho antes de ficar rico — uma combinação que, na história econômica, raramente termina bem.

Na PNADC anual, a distribuição por faixa etária mostra o fenômeno em tempo real: a coorte de 0 a 14 anos encolhe a cada edição, enquanto a de 60 ou mais se expande. O bônus demográfico, aquela janela em que há mais trabalhadores produtivos do que dependentes, se fecha no início da próxima década. A partir daí, a razão de dependência sobe. Cada trabalhador ativo carregará, em média, mais aposentados, mais pensionistas, mais idosos em cuidados de saúde.

## encargos previdenciários

A previdência pública brasileira já gasta mais de 13 por cento do PIB, patamar superior ao da maioria dos países da OCDE, que gastam 8 a 10 por cento, apesar de terem populações muito mais envelhecidas. A razão é conhecida: gastamos demais com aposentadoria precoce e regimes especiais. O funcionalismo, outra vez, aparece como agravante. O regime próprio dos servidores federais consome uma fatia da despesa previdenciária desproporcional ao seu peso demográfico, e o regime próprio dos militares opera com regras tão generosas que mereceriam por si só um ensaio. A reforma de 2019, que estabeleceu idade mínima, foi apenas o primeiro passo. Haverá, necessariamente, uma segunda e uma terceira, ou o sistema entrará em colapso na metade da década de 2040.

Os dados da PNADC anual, visita 5, já mostram sinais desse aperto. A proporção de domicílios cuja renda principal é pensão ou aposentadoria está próxima de 25 por cento, e tende a crescer. Em municípios pequenos do Nordeste rural, a proporção ultrapassa 50 por cento. Isso quer dizer que, em vastas regiões do país, a economia local é, em grande parte, a economia do INSS. O Brasil é, em alguns rincões, uma federação de aposentados.

## juventude dependente

A outra face do envelhecimento é a juventude que ficou para trás. A PNADC anual aponta que cerca de 22 por cento dos jovens entre 15 e 29 anos estão na condição de nem-nem — nem estudam nem trabalham. É fenômeno maior no Nordeste, especialmente entre mulheres jovens com filhos pequenos, mas não se limita a lá. É juventude que se formou no meio da pandemia, que tem dificuldades crônicas de letramento conforme aponta o [INAF 2024](https://alfabetismofuncional.org.br/), e que entra no mercado de trabalho em condição de subqualificação permanente. A mobilidade intergeracional, sempre frágil no Brasil, tornou-se ainda mais travada.

O que as duas pontas da pirâmide mostram, juntas, é um país que envelhece sem acumular capital, sem capital humano suficiente e sem produtividade para pagar por sua própria velhice. Se não houver reforma estrutural — previdenciária, educacional, trabalhista — nos próximos dez anos, o Brasil vai atravessar a década de 2040 fazendo escolhas dolorosas entre comer e se aposentar, entre hospital e escola, entre servidor e cidadão.

---

# parte 7 — raça, sexo e o mito da desigualdade identitária

## cor e renda

É preciso dizer primeiro, sem subterfúgio, o que os dados mostram: há diferença de renda por cor autodeclarada no Brasil. Na PNADC anual, visita 5, a proporção de brancos na faixa de 10 SM ou mais é de aproximadamente 8,7 por cento; a de pardos, 2,6 por cento. A razão é de 3,3 vezes. Em termos de renda média domiciliar per capita, brancos estão acima dos pretos e pardos em praticamente todos os cortes etários, regionais e de escolaridade. Seria leviano dizer que isso não existe. Existe, e tem raízes históricas que remontam à formação colonial e à abolição sem política de integração. Isso não está em disputa.

O que está em disputa é a explicação. E aqui os mesmos dados são brutais com a narrativa identitária contemporânea. Quando o recorte é por escolaridade, o gap cresce muito mais: a proporção de pessoas com ensino superior completo na faixa de 10 SM ou mais é de aproximadamente 12 por cento; a de pessoas com apenas fundamental é de 0,7 por cento. A razão é de 17 vezes. Cinco vezes maior do que o gap racial.

## mulher e renda

Com sexo, padrão análogo. A renda média do trabalho de mulheres é inferior à dos homens, mesmo em ocupações comparáveis, mas o gap se reduz drasticamente quando se controlam escolaridade, horas trabalhadas, ocupação, setor e idade. O "gap bruto" é grande; o "gap líquido" é pequeno e, em algumas categorias, inverte-se. Onde as mulheres têm escolaridade superior, ultrapassam os homens de mesma faixa etária; o Brasil é, em nível de graduação, um país de mulheres. A maior parte do que se convencionou chamar de gap salarial de gênero é, na verdade, gap de alocação: mulheres escolhem, ou são empurradas por estrutura familiar, para ocupações de menor remuneração e menor jornada, em especial após a maternidade. Isso é problema social sério, mas não é misoginia corporativa, como insiste a narrativa identitária.

## leitura não-identitária

Escolaridade explica mais do que cor e mais do que sexo. Esta é a conclusão empírica inescapável. Os dados do [IPEA](https://www.ipea.gov.br/portal/categorias/276-retratos-indicadores/retratos-indicadores-educacao) confirmam: a média de anos de estudo de brancos é de 10,8; a de negros, 9,2. A diferença é real, mas equivale a cerca de um ano e meio de escolaridade. O gap de renda entre quem tem ensino superior e quem tem apenas fundamental equivale a 17 vezes a renda. A questão racial, no Brasil, é, antes de tudo, questão educacional. Quem defende ações públicas focadas em cor em vez de em capital humano está batendo no sintoma e ignorando a doença.

Esse tipo de análise tem preço político. Dizer em voz alta que a desigualdade racial brasileira é majoritariamente desigualdade educacional mediada por história familiar custa acusação de insensibilidade. Tudo bem. A verdade custa. O preço de ignorá-la é maior: políticas desenhadas para melhorar a condição de pessoas negras acabam, quando ignoram escolaridade, produzindo ganhos marginais para a elite preta já letrada — em geral urbana, com ensino superior — e nenhum efeito sobre a massa de pretos e pardos do interior nordestino que vivem em domicílios com renda per capita abaixo de 1 SM. Cota em universidade resolve o gargalo dos 5 por cento do topo da pirâmide preta. Não resolve o fosso dos 95 por cento.

A solução séria é, portanto, redistribuir capital humano na base — letramento infantil, educação básica de qualidade, transporte escolar, merenda, currículo —, não redistribuir cadeiras no topo. Fazer o contrário é gesto de classe disfarçado de gesto de raça.

---

# parte 8 — informalidade como refúgio

## PIB informal

A PNADC anual aponta, em 2024, taxa de informalidade de 39,0 por cento da população ocupada, [ligeiramente abaixo dos 39,2 por cento](https://agenciadenoticias.ibge.gov.br/agencia-sala-de-imprensa/2013-agencia-de-noticias/releases/42530-pnad-continua-em-2024-taxa-anual-de-desocupacao-foi-de-6-6-enquanto-taxa-de-subutilizacao-foi-de-16-2) registrados em 2023. Em números absolutos, os informais passaram de 39,4 milhões para 40,3 milhões. A economia ocupa recorde de 103,3 milhões de pessoas, mas quase quatro em dez trabalham sem carteira, sem CNPJ, sem INSS, sem FGTS, sem seguro-desemprego, sem décimo terceiro e sem férias pagas. São entregadores de aplicativo, camelôs, cabeleireiras sem salão, pedreiros autônomos, motoristas de app, diaristas, vendedores de trinca-trinca nos semáforos, manicures de porta em porta.

O número de [trabalhadores por aplicativos cresceu 25,4 por cento entre 2022 e 2024](https://agenciadenoticias.ibge.gov.br/agencia-noticias/2012-agencia-de-noticias/noticias/44806-numero-de-trabalhadores-por-aplicativos-cresceu-25-4-entre-2022-e-2024), segundo o IBGE. A informalidade, longe de ser resíduo de uma economia pré-moderna, é hoje modo dominante de organização do trabalho brasileiro de baixa e média qualificação. O trabalhador migrou da feira para o celular, mas não migrou para a CLT.

## racionalidade da informalidade

A informalidade não é fruto de indolência, nem de ignorância. É fruto de cálculo. Quando um trabalhador pesa os custos de formalização no Brasil — contribuição patronal de 20 por cento ao INSS, FGTS de 8 por cento, provisão de férias, décimo, encargos trabalhistas, risco jurídico de processo futuro, burocracia para abrir CNPJ, desconto do IRRF — e compara com a informalidade — ganho bruto imediato, sem desconto, com custo zero de administração —, a escolha é óbvia. O Estado brasileiro pune o trabalho formal tão mais severamente do que o informal que o trabalhador de baixa renda faria a escolha irracional se optasse pela CLT.

Os microempreendedores, na ponta, enfrentam o mesmo cálculo. O MEI, criado em 2008, foi tentativa louvável de formalizar. Mas os limites de faturamento o mantêm preso a uma gaiola: cruzar o teto de R$ 81 mil ano é, para a maioria, condenação a uma escalada súbita de tributação que torna o crescimento pior do que a estagnação. O brasileiro empreendedor entende rapidamente a equação: ou fica pequeno, ou salta direto para grande com sócio-investidor. Entre um e outro, o vale da morte.

## carga tributária

O Brasil arrecada cerca de 33 por cento do PIB, porcentagem de país europeu, mas entrega serviço público de país em desenvolvimento. A razão é conhecida: a base tributária é estreita, concentrada no consumo, e a arrecadação é consumida por folha de pagamento pública, previdência e dívida, sobrando muito pouco para investimento, educação, saúde e segurança. A carga efetiva sobre o trabalhador formal de baixa renda, incluindo tributos embutidos em consumo, passa facilmente de 40 por cento. Ele ganha, o Estado tira, e o Estado devolve — em forma de escola ruim, hospital lotado, transporte quebrado, rua esburacada e filas.

Diante disso, a informalidade deixa de ser problema e passa a ser solução. É o mecanismo pelo qual o brasileiro comum, sem saber que o faz, executa uma greve tributária silenciosa contra um Estado que não lhe entrega contrapartida. Formalizar, no Brasil, é aceitar contribuir para um arranjo do qual não se recebe proporção razoável de volta. Enquanto esse arranjo não mudar, qualquer campanha "anti-informalidade" é combate a sintoma. O sintoma sumirá no dia em que a formalização for boa para o trabalhador, não para o Estado.

---

# parte 9 — a escola que produz pobreza

## analfabetismo funcional

Vinte e nove por cento dos brasileiros entre 15 e 64 anos são [analfabetos funcionais](https://alfabetismofuncional.org.br/), segundo o INAF 2024. É o mesmo número de 2018. Seis anos depois, nada mudou. Entre os jovens de 15 a 29 anos, o índice, que era de 14 por cento em 2018, subiu para 16 por cento. Três em cada dez adultos brasileiros leem, no máximo, textos curtos e diretos, sem compreender ideias complexas ou fazer inferências. Um em cada seis jovens está igualmente comprometido.

A correlação com a renda domiciliar per capita é direta: o domicílio em que o principal provedor é analfabeto funcional tende a se concentrar nas duas primeiras faixas de SM. Ele não "cai" para a faixa baixa; ele está lá por consequência mecânica de sua baixa capacidade de absorver informação, adaptar-se a novas tarefas, alfabetizar-se digitalmente e ascender profissionalmente. A pobreza brasileira, para essa parcela, não é episódica; é estrutural, e a estrutura é mental.

## PISA

Os resultados do [PISA 2022](https://www.gov.br/inep/pt-br/centrais-de-conteudo/noticias/acoes-internacionais/divulgados-os-resultados-do-pisa-2022) confirmam o diagnóstico: Brasil com 379 pontos em matemática, 410 em leitura, 403 em ciências. A média da OCDE, a menor da série, foi 472, 476 e 485. O Brasil está, portanto, entre 60 e 90 pontos abaixo da OCDE em cada disciplina. Não é diferença pequena. É diferença geracional. Na América do Sul, o Brasil [ficou em último](https://agenciabrasil.ebc.com.br/educacao/noticia/2023-12/pisa-brasil-mantem-estabilidade-em-matematica-leitura-e-ciencias) em ciências, empatado com Argentina e Peru, atrás de Chile, Uruguai e Colômbia. Em pensamento criativo, nova avaliação introduzida em 2022, o Brasil ficou em 49º de 64 países.

A estabilidade das notas brasileiras desde 2009 não é mérito. É diagnóstico. Significa que, apesar de crescimento de gastos reais com educação básica, de expansão de matrículas, de redução de evasão, de programas e mais programas, o resultado cognitivo dos alunos brasileiros permaneceu no mesmo patamar. Gastou-se mais para produzir o mesmo. É o oposto de produtividade. É desperdício estrutural. E é uma acusação direta ao monopólio pedagógico dos sindicatos e das secretarias estaduais, que capturaram a máquina educacional e a operam como uma cooperativa de funcionários, não como um instrumento de formação de crianças.

## escolaridade vs renda

Voltemos à aritmética da parte 7: na faixa de 10 SM ou mais, 12 por cento têm ensino superior; apenas 0,7 por cento têm até o fundamental. A razão é de 17 vezes. Nenhuma variável, em nenhum país, prediz tão bem a renda individual quanto a escolaridade. Quem completa o ensino superior no Brasil quadruplica, em média, a renda esperada daquele que parou no fundamental. Quem completa pós-graduação dobra, de novo, esse número.

A escola pública brasileira, portanto, é a maior máquina concreta de pobreza que o país opera. Não por falta de dinheiro — gastamos, em proporção ao PIB, o mesmo que muitos países da OCDE —, mas por desenho institucional. Professores mal selecionados, mal treinados, mal avaliados e, nas grandes redes, protegidos de qualquer sistema de mérito pelos sindicatos; currículos engolidos por ideologia; escolas sem autonomia, sem incentivos, sem competição e, sobretudo, sem responsabilização. Numa palavra: é um sistema feito para não funcionar. Não se trata de má vontade de pai ou de aluno. Trata-se de arquitetura de incentivos.

O que daria certo é conhecido no mundo todo desde Milton Friedman: voucher educacional, concorrência entre escolas, autonomia diretiva, avaliação externa com consequência, e, no limite, homeschooling legalizado onde a família o prefira. Falar disso em alto e bom som no Brasil, contudo, é ser rotulado de ultraliberal, neoliberal, privatista, coisa e tal. Os rótulos custam barato; os 29 por cento de analfabetos funcionais custam caro.

---

# parte 10 — o funcionalismo como classe

## teto

O teto constitucional do funcionalismo, em 2026, é de R$ 46.366,19, equivalente ao subsídio de ministro do STF. Isso deveria ser uma cúpula: o servidor público ativo mais bem pago do país deveria ganhar, no limite, o que ganha um ministro do Supremo. Ninguém além disso. É o que diz a Constituição.

A realidade operacional é outra. O Brasil desenvolveu, ao longo de três décadas, uma engenharia jurídica sofisticada para burlar o teto sem jamais revogá-lo. Chama-se penduricalho. Auxílio-moradia, auxílio-educação, auxílio-saúde, auxílio-alimentação, adicional por tempo de serviço, quinquênio, produtividade, gratificação de desempenho, verba de representação, diária indenizatória, abono de permanência, ajuda de custo em razão de mudança, licença-prêmio convertida em dinheiro, PAE, GRG, GDE, sigla sobre sigla. Em 2025, antes da decisão do STF, os juízes brasileiros receberam, por essas verbas, o equivalente a [R$ 10,7 bilhões acima do teto](https://www.painelpolitico.com/p/penduricalhos-do-judiciario-stf-limita). Noventa e oito por cento dos juízes estaduais ultrapassaram o teto. Um em cada quatro ganhou mais de R$ 1 milhão por ano acima do limite constitucional.

## supersalários

Os números são obscenos quando confrontados com a mediana do país. Enquanto 40 por cento da população vive com até dois salários mínimos, cerca de seis ministros do STF receberam, em 2024, [R$ 2,8 milhões em supersalários acima do teto constitucional](https://noticias-do-brasil.news/crime/crime-politica/seis-ministros-do-stf-receberam-supersalrios-acima-do-teto.html). Servidores da AGU receberam, no mesmo ano, bônus que elevaram os pagamentos até o teto de forma amplamente documentada. Juízes do Trabalho embolsaram [R$ 1 bilhão acima do teto em 2025](https://eshoje.com.br/politica/justica/2026/02/juizes-do-trabalho-receberam-r-1-bilhao-acima-do-teto-em-2025/). O Ministério Público acompanha. E tudo isso se faz com o aval — implícito ou explícito — do próprio Judiciário, que é parte interessada, parte julgadora e parte beneficiária.

A decisão do STF de março de 2026, que limitou os penduricalhos a 35 por cento do teto, é descrita pela Corte como ajuste rigoroso. Na prática, legalizou o que antes era contrabando. O teto prático passou de R$ 46 mil para [R$ 78,8 mil mensais](https://sintrajud.org.br/conteudo/16064/decisao-do-stf-cria-teto-de-r-78-mil-para-juizes-e-legaliza-penduricalhos). A Constituição, que fala em um limite único, agora tem um limite oficial e um limite "com mais adicional". A economia prometida, R$ 7,3 bilhões ao ano, é menos do que o país continuará a pagar em penduricalhos legalizados. Chama-se a isso, em eufemismo ministerial, "calibração". O português comum chama de blindagem.

## judiciário

O que está em jogo não é apenas dinheiro. É uma concepção de Estado. O Judiciário brasileiro operou, nas últimas duas décadas, como um Terceiro Poder emancipado: julga suas próprias regras de remuneração, decide sobre os limites de sua própria autoridade, e, nos momentos decisivos, pauta o Legislativo e o Executivo a partir de inquéritos, liminares monocráticas e ações de controle concentrado. Sua remuneração é apenas a face econômica de uma hipertrofia institucional maior, que vai desde a prisão de presos do 8 de janeiro com penas desproporcionais a crimes equivalentes julgados em outros contextos, até a gestão opaca de CPIs, até a manipulação velada de inquéritos com base em "risco à democracia".

Essa hipertrofia tem custo fiscal, custo institucional e custo moral. O custo fiscal é o que aparece nos dados: o contribuinte paulista paga, sem saber, a viagem internacional do desembargador. O custo institucional é a captura de áreas inteiras da política pelo direito. O custo moral é a sensação, crescente, de que o Brasil tem duas legalidades: uma para o cidadão comum, que paga o IR, atravessa no sinal, vai ao juizado especial; outra para a casta, que edita as próprias regras, se julga e se absolve. A democracia funciona quando essas duas legalidades são a mesma. No Brasil, elas não são.

## blindagem

O funcionalismo federal brasileiro, somado, custou ao Tesouro mais de R$ 380 bilhões em 2024. A despesa com pessoal do Executivo federal cresceu sob Lula a seu maior patamar [desde 2008](https://www.gazetadopovo.com.br/economia/funcionalismo-publico-federal-recorde-despesas-outubro/). Reajustes, reclassificações, concursos, novas carreiras, progressões antecipadas, bônus retroativos — tudo isso caminha em ritmo bípede, enquanto o aposentado do INSS recebe reajuste abaixo da inflação e a escola pública fecha pelo turno da tarde por falta de professor. Uma parte do Brasil que se autoproclama classe trabalhadora, mas que vive em função da extração fiscal imposta à outra parte do Brasil, que é classe efetivamente trabalhadora.

É aqui que os dados da PNADC anual ganham sua mais dolorosa clareza: o Brasil não tem duas classes no sentido marxista — capital e trabalho. Tem três: capital privado, trabalho privado e trabalho estatal. As duas primeiras convivem sob o capitalismo. A terceira é uma ordem à parte, que se financia à custa das duas primeiras, blinda-se juridicamente, e oscila entre o silêncio discreto e a indignação pública quando ameaçada. É a classe que ocupa o DF. É a classe que interpreta a Constituição. É a classe que, em última análise, define a ordem política brasileira. E é a classe cuja conta, tarde ou cedo, alguém terá de pedir.

---

# parte 11 — o sul que quer sair

## PIB per capita SC/PR

Santa Catarina, Paraná e Rio Grande do Sul apresentam PIB per capita e renda domiciliar per capita sistematicamente superiores à média nacional. Santa Catarina, em particular, é fenômeno. Seu PIB per capita, como vimos, é o [quinto do país](https://www.seplan.sc.gov.br/pib-de-santa-catarina-cresce-53-em-2024-o-segundo-maior-aumento-em-10-anos/), com crescimento em 2024 de 5,3 por cento contra média nacional de 3,4 por cento. A indústria de transformação catarinense cresceu 7,7 por cento. O Gini regional do Sul é o menor dos macro-regiões brasileiras. A distribuição de renda é mais plana, a informalidade é menor, a escolaridade média é maior, a taxa de ocupação é mais alta. Em todos os indicadores que importam para uma sociedade próspera, a Região Sul opera como se fosse outro país encaixado na federação.

O Paraná segue trajetória análoga, ancorado em Curitiba, Londrina, Maringá, Ponta Grossa, Cascavel. O Rio Grande do Sul, apesar das chuvas catastróficas de 2024, mantém capital humano e indústria de primeira linha. Não é coincidência que os três estados sejam, há décadas, politicamente mais conservadores, mais favoráveis a reformas estruturais, mais refratários à agenda de transferência ilimitada de renda desde Brasília. A estrutura econômica e a estrutura política andam juntas.

## adesão tributária

O desconforto dos estados sulistas com o pacto federativo é sabido. Pagam mais impostos do que recebem de volta. Financiam políticas que, em larga medida, não lhes servem. Elegem minorias no Congresso. A percepção de deserto de representação é real: os três estados, somados, têm menos bancadas parlamentares do que a soma das nordestinas, apesar de responderem por fatia muito superior do PIB nacional. Essa assimetria entre contribuição e representação alimenta um ressentimento difuso que, em períodos de crise, se manifesta em movimentos separatistas — pequenos, minoritários, mas crônicos.

A ideia de uma República Separada do Sul não sobrevive ao mínimo exame jurídico; a Constituição a proíbe expressamente. Mas como vocalização política do descontentamento, serve: é o som que um eleitorado emite quando percebe que paga duas vezes pelo mesmo serviço e recebe uma fração. O Sul brasileiro, em seu desconforto, funciona como a Catalunha brasileira — produtivo, letrado, ressentido, pagador.

## desalinhamento político

O desalinhamento é duplo. Primeiro, regional: o Sul elege mais à direita, governa mais à direita, legisla mais à direita, e é tratado pela imprensa federal, sediada no Rio e em São Paulo, como caso atípico a ser explicado. Segundo, institucional: as instituições federais, concentradas em Brasília, quase nunca operam com centro de gravidade sulista. Quando os eleitores dos três estados elegem figuras alinhadas com agenda de liberdade econômica e governo mínimo, essas figuras encontram em Brasília uma resistência da máquina que converte qualquer reforma em projeto arrastado. O que deveria ser peso institucional proporcional ao peso econômico vira, na prática, um atrito constante entre o país que produz e o país que administra.

A solução, naturalmente, não é secessão. É federalismo de verdade: devolver competências aos estados, descentralizar o orçamento, transferir poder fiscal e regulatório para níveis locais em que a prestação de contas seja possível. Um Brasil federativo à moda americana, em que Santa Catarina possa, no limite, ter alíquotas distintas do Ceará, escolas com currículos distintos, códigos de trânsito distintos, políticas de segurança distintas. É isso que os sulistas pedem quando ameaçam, simbolicamente, sair. O que eles querem, quase sempre, é ficar — mas em outro arranjo.

---

# parte 12 — a seca política do nordeste

## voto e transferência

O Nordeste brasileiro votou, em 2022, de maneira quase monocromática em Lula. Foram 69,34 por cento dos votos válidos no segundo turno e vitória nos nove estados da região. Bolsonaro obteve maioria em apenas [20 municípios nordestinos](https://www.cnnbrasil.com.br/politica/nordeste-e-a-unica-regiao-em-que-lula-obteve-mais-votos-que-bolsonaro-confira/). O resto — cerca de 1.794 cidades — foi petista. O fenômeno, convenhamos, não tem outro paralelo no país. Nem o Sul elege tão uniformemente à direita quanto o Nordeste elege à esquerda.

A correlação com transferência de renda é nítida, ainda que o petismo regional goste de minimizá-la. Nos municípios com maior cobertura do Auxílio Brasil/Bolsa Família, Lula teve 71 por cento dos votos; Bolsonaro, 24 por cento. A cobertura mais alta coincide com as regiões mais pobres, mais rurais, menos letradas e mais dependentes de transferência federal. Chamar isso de compra de voto é tecnicamente falso — ninguém coloca dinheiro dentro da urna. Chamar de correlação estrutural entre modo de sobrevivência econômica e preferência política é exatamente o que os dados mostram.

## coronelismo 2.0

Há, além do assistencialismo, uma camada mais profunda: o coronelismo reconfigurado. As elites políticas nordestinas operam em malha fina, prefeitura por prefeitura, secretaria por secretaria, loteando cargos, ambulâncias, máquinas, carros oficiais, empregos terceirizados, em troca de voto. O governo federal petista, na prática, refinanciou essa rede a partir de 2003, reconstruiu-a em 2023 e opera com ela uma máquina que combina transferência federal direta ao cidadão (Bolsa Família) e transferência indireta via prefeitura aliada.

O coronelismo contemporâneo é mais eficiente do que o dos anos 1930 porque digitalizou. O cartão do Bolsa Família é controlado por atendimento feito em equipamento municipal, que fica sob olhar do cabo eleitoral, que é escolhido por vereador, que é aliado do prefeito, que tem relação direta com deputado federal, que vota com o governo. Em cada elo da corrente há um interesse político que converte a transferência, teoricamente universal, em favor particular. O resultado é voto. O voto alimenta o sistema. O sistema perpetua a pobreza.

Quebrar esse ciclo é a tarefa mais difícil e mais urgente da política brasileira. Não se quebra com mais transferência; se quebra com investimento em capital humano na base — escola que funciona, saneamento, energia, estrada, internet, formação técnica — para que o cidadão nordestino pare de depender politicamente da prefeitura e passe a depender profissionalmente do próprio trabalho. É o que os dados mostram com tanta clareza que, se o leitor tiver paciência para abrir o `brasil.sqlite` deste repositório, verá com os próprios olhos.

## coincidência

Convém dizer, para quem gosta de falar em coincidência: a correlação entre Gini regional, cobertura de Bolsa Família e voto petista está acima de 0,7 no Nordeste. Nenhuma outra variável se aproxima. Renda individual, cor, religião, gênero, idade, escolaridade — nenhuma dessas variáveis, tomadas isoladamente, explica o voto regional como a combinação renda-assistência-prefeitura. Correlação de 0,7 em ciência social é raro, praticamente lei da natureza. No Nordeste, é descrição da paisagem.

Isso não faz do eleitor nordestino um zumbi político, como insinua o preconceito sulista. Faz do eleitor nordestino um ator racional em sistema perversamente desenhado. O problema não está nele. Está no sistema. Quem projetou o sistema colhe os frutos.

---

# parte 13 — o que o gini não mede

## mobilidade

O coeficiente de Gini mede a dispersão da renda em um instante do tempo. É fotografia, não filme. Diz o quanto a renda está desigualmente distribuída hoje; não diz se o filho do pobre tem chance de virar rico, se o neto do rico pode virar pobre, se a posição social é herdada, se a meritocracia funciona, se o sistema educacional permite ascensão.

No Brasil, os estudos disponíveis sobre mobilidade intergeracional sugerem taxas muito inferiores às de países desenvolvidos. Pai pobre, filho pobre; pai rico, filho rico; e, cada vez mais, pai servidor, filho servidor. A rigidez se instala por três canais: capital humano herdado (filho de pai letrado tem mais chance de ser letrado), capital social herdado (filho de família conectada tem mais chance de conseguir vaga em concurso bom), e capital econômico herdado (filho de família com imóvel tem mais chance de empreender sem medo de queda).

Um país que, como o Brasil, tem Gini alto e mobilidade baixa é um país em que a desigualdade é, na prática, casta. Casta não é, em tese, marxismo. Marx falava de classe. No Brasil, porém, muitas famílias de três ou quatro gerações no mesmo escalão social descrevem um padrão que se aproxima mais de sistema de castas do que de mercado. O dado do Gini não mostra isso. Os dados da PNAD longitudinal começam a mostrar.

## capital humano

O Banco Mundial tem insistido, em diversas publicações, que o elemento explicativo dominante da desigualdade brasileira não é a renda do capital versus a do trabalho, como pretende a tradição marxista. É a distribuição desigual do capital humano. A ideia, formulada inicialmente por Gary Becker e popularizada por Milton Friedman, é de que a renda individual é, em larga medida, reflexo da produtividade individual, que por sua vez é reflexo da soma de habilidades cognitivas, emocionais, técnicas e sociais acumuladas pelo indivíduo ao longo da vida.

Quando se mede o capital humano brasileiro, o mesmo Banco Mundial nos coloca em um patamar modesto — próximo ao de economias muito menos ricas. Nosso PIB per capita é maior do que o de países com capital humano parecido; é como se, em proporção, estivéssemos gastando nosso capital físico sem investir no humano. O resultado: crescimos devagar, produtividade estagnada desde os anos 1980, e uma geração de jovens chegando ao mercado com letramento baixo, matemática pior, sem formação técnica e sem preparo para o trabalho que o mundo de 2030 exigirá.

## instituições

Os estudos de Daron Acemoglu e James Robinson em *Why Nations Fail* são claros: a diferença de longo prazo entre nações prósperas e nações estagnadas não está em recursos naturais, nem em cultura, nem em geografia. Está na qualidade das instituições. Instituições inclusivas geram incentivos para investimento, inovação, educação. Instituições extrativas geram incentivos para captura de renda, rent-seeking, lobby.

O Brasil, infelizmente, opera com instituições extrativas em larga medida. O funcionalismo federal extraindo do contribuinte. O Judiciário legislando sobre seu próprio teto. O Legislativo votando fundo eleitoral bilionário. As estatais capturadas por partidos. Os bancos públicos sendo usados para distorcer mercado de crédito. O sistema de concessões sendo leiloado sob medida. Cada um desses mecanismos redireciona energia produtiva do mercado para o lobby. O resultado é o Gini que temos, mesmo com 30 anos de democracia. O Gini não é problema; é sintoma. O problema é a matriz institucional.

O que o Gini não mede, portanto, é o essencial: ele não mede a capacidade da sociedade de alterar a si mesma. Uma sociedade com Gini 0,52 mas com instituições que permitam mobilidade é uma sociedade que caminha. Uma sociedade com Gini 0,52 e instituições travadas é uma sociedade que roda em círculo. O Brasil está no segundo caso. É o diagnóstico mais duro, e o único que importa.

---

# parte 14 — três saídas pró-liberdade

## reforma tributária real

A reforma tributária em vigor desde 2023 e em implementação até 2033 não merece o nome. Substitui cinco tributos por dois, simplifica a compliance — no papel —, mas mantém carga absurda, a alíquota combinada IBS-CBS de 26,5 a 28 por cento colocando o Brasil entre os maiores IVAs do mundo, [sete pontos acima da média da OCDE](https://www.institutoliberal.org.br/blog/justica/a-vigente-reforma-tributaria-sem-confetes/). O chamado split payment, ademais, entrega ao Estado o controle financeiro da transação antes mesmo de o contribuinte ter acesso ao dinheiro: é a maior transferência de controle financeiro privado para mãos públicas da história do país. Simplifica para o contador. Escraviza o empresário.

Uma reforma tributária real teria três eixos. Primeiro, corte da carga total em 8 a 10 pontos do PIB, chegando a patamar compatível com economias emergentes que crescem: 23 a 25 por cento do PIB, nunca 33. Segundo, substituição de tributos sobre folha por tributos sobre consumo e propriedade, com deslocamento explícito do peso do trabalho para o peso do capital físico, de modo a incentivar contratação formal. Terceiro, imposto negativo de renda na base, à la Friedman e à la Negative Income Tax, substituindo o patchwork atual de Bolsa Família, BPC, seguro-desemprego, abono salarial e desoneração da folha por um mecanismo transparente, previsível, sem armadilha de pobreza. A simplificação não viria do software do IBS; viria da arquitetura tributária.

Tudo isso tem nome no Brasil: Imposto Único, na formulação de Marcos Cintra. Imposto negativo, na formulação de Paulo Guedes. Teto de gastos, na formulação de Roberto Campos Neto em seus alertas fiscais mais incisivos. Vocabulário existe. Falta quem o pronuncie.

## teto efetivo do funcionalismo

Um teto efetivo para o funcionalismo significa, primeiro, um teto sem penduricalho. Remuneração bruta máxima, inclusive verbas indenizatórias, inclusive adicional por tempo, inclusive auxílio-moradia e tudo o mais, limitada ao subsídio constitucional. Ponto. Qualquer ganho acima disso, fora da lei. Qualquer pagamento acima disso, devolvido ao Tesouro com juros e multa. Isso exige emenda constitucional mais rigorosa, fiscalização independente e, sobretudo, coragem política para enfrentar a corporação que mais influencia a política brasileira: a magistratura. Não há caminho fácil. Mas há caminho.

Segundo, fim do regime próprio do servidor para novos entrantes, com migração imediata para o RGPS. Terceiro, avaliação periódica obrigatória e destituição possível por desempenho. Quarto, remuneração variável por entrega, não por tempo. Quinto, restrição severa de cargos em comissão, com concursos para funções técnicas e limite efetivo para funções de confiança. Sexto, publicação obrigatória de todos os contracheques, todos os auxílios, todos os bônus, todos os tempos de licença, todos os afastamentos, em portal único e auditável.

Isso não é vingança contra o servidor. É igualdade republicana. O servidor público brasileiro não é inimigo de ninguém. Mas o servidor público brasileiro, hoje, opera em regime juridicamente privilegiado em relação ao trabalhador privado em tantos aspectos, que a conta pública deixou de fechar. Restabelecer o equilíbrio é devolver ao país aquilo que a Constituição prometeu.

## liberdade educacional

A terceira saída é pedagógica e institucional. Voucher educacional em escala piloto, com ampliação por resultado. Autonomia diretiva nas escolas públicas, com contratação e demissão por desempenho. Avaliação externa anual, com consequência real. Currículo mínimo nacional, baseado em letramento, matemática, ciências, história, educação física e artes, sem ideologia importada. Escola cívico-militar onde a comunidade a escolher democraticamente. Homeschooling legalizado para famílias que o preferirem, com avaliação externa obrigatória. Desvinculação orçamentária do piso salarial de professores em relação ao desempenho: paga-se mais quem ensina melhor, não quem tem mais tempo de casa. Quebra do monopólio dos sindicatos na gestão escolar. Liberdade de criação de escolas privadas com menor burocracia.

Em paralelo, investimento sério em alfabetização na primeira infância. A evidência internacional é clara: o dinheiro gasto até os seis anos de idade rende, em capital humano, dez vezes mais do que o dinheiro gasto no ensino médio. O Brasil ainda opera como se o foco pedagógico estivesse no ProUni e no Fies, quando deveria estar em creches e pré-escolas. É miopia política financiada por miopia intelectual.

Essas três saídas, juntas, não são utópicas. São triviais tecnicamente. Cada uma delas tem equivalentes funcionando em pelo menos uma dezena de países. Nenhuma delas exige gênio jurídico, gênio econômico, gênio pedagógico. Exigem, apenas, coragem política, horizonte de mais de quatro anos e disposição de enfrentar corporações — a magistratura, os sindicatos, a burocracia partidária. No Brasil atual, isso é muito. Pode ser tudo. Mas é necessário.

Se o leitor pensa que são medidas de "ultraliberais", convido-o a ler os dados deste repositório. São medidas de sobrevivência.

---

# parte 15 — epílogo: o brasil auditável

## dados abertos

Este ensaio é filho de um repositório. Todos os números citados, todas as médias, todas as proporções, todos os Ginis, todas as rendas em salários mínimos, são reprodutíveis. Basta clonar o repositório, rodar `brasil pipeline-run --raw latest` e conferir. Os microdados vêm do próprio IBGE, gratuitamente disponíveis no [portal da PNADC](https://www.ibge.gov.br/estatisticas/sociais/trabalho/9171-pesquisa-nacional-por-amostra-de-domicilios-continua-mensal.html); o tratamento é aberto; as decisões metodológicas estão documentadas em `AGENTS.md`. Qualquer leitor crítico pode desmontar este texto com um `SELECT` no `brasil.sqlite`. Conto com isso. É o que deveria acontecer.

O Brasil, pela primeira vez, pode ser auditado por qualquer um com um notebook e três horas de tempo. O IBGE, apesar de todos os seus pecados institucionais, continua a produzir dados de qualidade internacional. O IPEA, apesar de sua militância por vezes escandalosa, ainda disponibiliza séries respeitáveis. O BCB publica séries temporais mensais que permitem deflacionar com precisão cirúrgica. Os tribunais, embora opacos na remuneração, publicam agora contracheques que podem ser cruzados com bases externas. O STF, embora caro, é rastreável. O funcionalismo, embora blindado, é mensurável.

Nunca, na história do país, foi tão possível saber quem ganha o quê, onde, por quê. O problema deixou de ser falta de dado. É excesso de desonestidade interpretativa.

## ceticismo cívico

Convém, portanto, encerrar com uma disciplina: ceticismo cívico. Desconfie de todo governo que celebra Gini baixo sem apresentar a metodologia. Desconfie de todo ministro que fala em "inclusão" sem apresentar a fonte de recursos. Desconfie de todo partido que promete "justiça social" sem apresentar a correlação entre gasto e resultado. Desconfie, sobretudo, de quem fala em "direitos" sem especificar quem paga. Todo direito tem contrapartida em orçamento. Todo orçamento tem contrapartida em tributo. Todo tributo tem contrapartida em sangue de contribuinte. Não há mágica.

O brasileiro médio, alimentado por décadas de jornalismo declarativo, aprendeu a consumir opinião como quem consome novela: é dada, não se questiona, aceita-se o personagem como o autor entrega. Este ensaio pede o contrário. Pede que se abra a planilha. Que se confira a fonte. Que se recalcule o Gini. Que se veja, com os próprios olhos, o que a PNAD mostra e o que esconde.

Porque a única tragédia pior do que a desigualdade brasileira é a desinformação brasileira. E a única maneira de reduzir ambas é fazer do dado um ato cívico.

## convite

Os dados estão aí. O país está aí. A escolha é de cada um. Mas a nação, essa coisa abstrata que o hino nacional chama de Pátria, só existe se cada cidadão, em seu canto, abrir a planilha.

O Brasil que você vai construir para seus filhos depende, entre outras coisas pequenas, de você entender este número: 5,53 para o DF, 2,05 para o Maranhão, 0,520 para o Gini, 40,6 por cento na faixa mais baixa, 6,5 por cento na faixa mais alta. Grave-os. Decore-os. Reveja-os a cada ano. Use-os como régua.

E, quando alguém lhe disser, da tribuna, que o Brasil está no melhor momento de sua história, pergunte: a que preço, com que reforma, para qual geração, auditável onde? Se a resposta for silêncio, você já sabe.

O restante, como dizia o Padre Antônio Vieira em outro contexto, "é para os que lerem".

---

## notas de rodapé e fontes

### notas numéricas

[¹] **Gini 0,520**: coeficiente de Gini da renda domiciliar per capita, calculado a partir da PNAD Contínua anual, visita 5, edição 2026-03, processado neste repositório (`data/outputs/base_labeled_npv.csv`) com pesos `V1028`. A leitura oficial do IBGE para a renda per capita em 2024, em metodologia distinta, é 0,506. Ver nota do IBGE em [rendimento per capita e desigualdade 2024](https://agenciadenoticias.ibge.gov.br/agencia-noticias/2012-agencia-de-noticias/noticias/43302-rendimento-per-capita-e-recorde-e-desigualdades-caem-ao-menor-nivel-desde-2012).

[²] **SM médio de 3,62**: média ponderada da renda domiciliar per capita em múltiplos do salário mínimo vigente no mês-alvo, PNADC anual 2024. Corresponde à renda domiciliar per capita de R$ 2.020 na leitura oficial do IBGE, conforme [nota de maio de 2025](https://agenciagov.ebc.com.br/noticias/202505/renda-per-capita-tem-aumento-recorde-de-4-7-e-desigualdades-caem-ao-menor-nivel-desde-2012).

[³] **DF 5,53 SM / MA 2,05 SM**: recortes ponderados por UF, mesmo arquivo. Em reais, renda domiciliar per capita de R$ 3.444 no DF e R$ 1.077 no MA, [conforme IBGE](https://agenciadenoticias.ibge.gov.br/agencia-sala-de-imprensa/2013-agencia-de-noticias/releases/42761-ibge-divulga-rendimento-domiciliar-per-capita-2024-para-brasil-e-unidades-da-federacao).

[⁴] **40,6 por cento em até 2 SM e 6,5 por cento em 10+ SM**: distribuição da população por faixa de salário mínimo da renda domiciliar per capita, estimativa ponderada com pesos replicados.

[⁵] **Gap branco x pardo na faixa 10+ de 3,3×**: proporção de brancos na faixa superior (~8,7 por cento) contra proporção de pardos (~2,6 por cento), PNADC anual, recorte por cor autodeclarada.

[⁶] **Gap superior x fundamental na faixa 10+ de 17×**: proporção de pessoas com ensino superior completo na faixa de 10 SM ou mais (~12 por cento) contra proporção de pessoas com apenas ensino fundamental (~0,7 por cento).

[⁷] **Nordeste 27 por cento da população / 41 por cento dos mais pobres**: participação da macrorregião no total e na faixa inferior da distribuição.

[⁸] **Teto do funcionalismo R$ 46.366,19 em 2026**: subsídio mensal do ministro do STF, valor corrente, conforme [levantamento da Gazeta do Povo](https://www.gazetadopovo.com.br/economia/supersalarios-so-1-da-populacao-tem-renda-igual-ou-superior-ao-teto-do-funcionalismo/) e [decisão do STF de março de 2026](https://www.painelpolitico.com/p/penduricalhos-do-judiciario-stf-limita).

[⁹] **R$ 10,7 bilhões acima do teto em 2025 no Judiciário**: levantamento da Transparência Brasil e República.org, citado pelo [Painel Político](https://www.painelpolitico.com/p/penduricalhos-do-judiciario-stf-limita).

[¹⁰] **R$ 78,8 mil mensais como teto prático após a decisão do STF de 2026**: cálculo que soma 35 por cento do teto em penduricalhos e 35 por cento em adicional por tempo, ao teto básico, conforme [Poder 360](https://www.poder360.com.br/poder-justica/stf-autoriza-penduricalhos-com-limite-de-35-acima-do-teto/) e [SINTRAJUD](https://sintrajud.org.br/conteudo/16064/decisao-do-stf-cria-teto-de-r-78-mil-para-juizes-e-legaliza-penduricalhos).

[¹¹] **Informalidade em 39,0 por cento em 2024**: taxa anual de informalidade da população ocupada, [IBGE](https://agenciadenoticias.ibge.gov.br/agencia-sala-de-imprensa/2013-agencia-de-noticias/releases/42530-pnad-continua-em-2024-taxa-anual-de-desocupacao-foi-de-6-6-enquanto-taxa-de-subutilizacao-foi-de-16-2).

[¹²] **INAF 29 por cento de analfabetos funcionais**: [INAF 2024](https://alfabetismofuncional.org.br/), Ação Educativa e Instituto Paulo Montenegro.

[¹³] **PISA 2022 Brasil 379/410/403 contra OCDE 472/476/485**: [INEP](https://www.gov.br/inep/pt-br/centrais-de-conteudo/noticias/acoes-internacionais/divulgados-os-resultados-do-pisa-2022).

[¹⁴] **Alíquota combinada IBS-CBS de 26,5 a 28 por cento**: [Instituto Liberal](https://www.institutoliberal.org.br/blog/justica/a-vigente-reforma-tributaria-sem-confetes/) e regulamentação da [LCP 214](https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm).

[¹⁵] **PIB per capita de Santa Catarina em R$ 61.274**: [SEPLAN-SC](https://www.seplan.sc.gov.br/pib-de-santa-catarina-cresce-53-em-2024-o-segundo-maior-aumento-em-10-anos/).

[¹⁶] **30 por cento da população acima dos 60 em 2050**: [Fiocruz / Saúde Amanhã](https://saudeamanha.fiocruz.br/2050-brasil-tera-30-da-populacao-acima-dos-60-anos/sem-categoria/) e [Agência Gov / IBGE](https://agenciagov.ebc.com.br/noticias/202408/populacao-do-pais-vai-parar-de-crescer-em-2041).

[¹⁷] **Lula 69,34 por cento no 2º turno no Nordeste**: [CNN Brasil](https://www.cnnbrasil.com.br/politica/nordeste-e-a-unica-regiao-em-que-lula-obteve-mais-votos-que-bolsonaro-confira/).

[¹⁸] **Anos de estudo: brancos 10,8 / negros 9,2**: [Agência Brasil / IPEA](https://agenciabrasil.ebc.com.br/educacao/noticia/2024-03/brancos-estudam-em-media-108-anos-negros-92-anos).

[¹⁹] **Gini seria 7,5 por cento maior sem os benefícios**: [IBGE, via Banca do Nordeste](https://bancadadonordeste.com.br/post/2025/12/25/81423-ibge-diz-que-o-indice-gini-de-desigualdade-seria-75-maior-sem-os-beneficios-de-programas-sociais-em-2024).

### fontes canônicas

- **PNAD Contínua**, Instituto Brasileiro de Geografia e Estatística: [página da pesquisa](https://www.ibge.gov.br/estatisticas/sociais/trabalho/17270-pnad-continua.html).
- **Microdados e retrospectiva 2012-2024**, [PDF oficial do IBGE](https://ftp.ibge.gov.br/Trabalho_e_Rendimento/Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/Principais_destaques_PNAD_continua/2012_2024/PNAD_continua_retrospectiva_2012_2024.pdf).
- **IPEA**, Retratos e Indicadores: [renda, pobreza, desigualdade](https://www.ipea.gov.br/portal/retrato/indicadores/renda-pobreza-e-desigualdade/apresentacao) e [educação](https://www.ipea.gov.br/portal/retrato/indicadores/educacao/apresentacao).
- **INEP**, Resultados PISA 2022 Brasil: [nota técnica](https://download.inep.gov.br/acoes_internacionais/pisa/resultados/2022/pisa_2022_brazil_prt.pdf).
- **INAF 2024**, [relatório oficial](https://alfabetismofuncional.org.br/).
- **Banco Central do Brasil**, série SGS 1619 para salário mínimo mensal.

---

*Este ensaio foi escrito a partir de um repositório público de processamento da PNAD Contínua anual. Os números são auditáveis. As opiniões, também.*
