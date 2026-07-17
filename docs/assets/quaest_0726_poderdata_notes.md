# Quaest jul/2026, benchmark PoderData/Aya: o braço natural do split-ballot

Complemento comparativo da síntese-clímax (`quaest_0726_sintese.json`). Não é um dossiê
da PoderData. É um comparativo de desenho de instrumento que usa a rodada PoderData/Aya
divulgada em 16/07/2026 como braço natural do teste discriminante nº 1 da síntese (o
split-ballot da rampa de não-escolha da hipótese central H-A, prob. 48%). Contas em
`quaest_0726_poderdata.json`; visual em `quaest_0726_poderdata_fragment.html` (slide
1600x900 embutido, capturar `.qpd-slide-shell .qpd` com container largo o bastante para
não clipar; a seção tem 56px de padding próprio).

## A rodada divulgada hoje (Fato, fonte primária + registro TSE)

PoderData/Aya, registro BR-00059/2026, registrada 10/07 e divulgada 16/07, campo
12 a 15 de julho, n=2.400, telefônica IVR/URA (resposta pelo teclado, sem entrevistador
humano), seleção aleatória do discador sobre fixos e celulares, ponderação por
sexo/idade/instrução/região/renda, margem +/-2.

- 2º turno: Lula 45, Flávio 43, branco/nulo 9, não sabe 2. Soma 88, não-escolha 12, gap 2 (empate técnico).
- 1º turno: Lula 40, Flávio 34.

A rodada anterior, essa sim no nosso acervo em PDF primário (relatório BR-05722/2026,
campo 21-24 jun), trazia Lula 46 x Flávio 43, branco/nulo 8, não sabe 3 (não-escolha 11).
A série da PoderData é estável: Flávio 42-43 e não-escolha 11-12 em três ondas (mai, jun, jul).
Atenção ao caveat temporal: o relatório PDF do pacote é a rodada de JUNHO; a divulgação de
hoje é a de JULHO. A comparação mais limpa é PoderData jul (12-15/07) contra Quaest jul
(10-13/07), quase simultâneas.

## Auditoria de coerência do benchmark (Fato)

Benchmark também precisa aguentar checagem. Somas fecham (jun 46+43+8+3=100; jul
45+43+9+2=99, arredondamento IVR declarado na ficha). Registro confere. Questionário é
público e curto. Passa.

## A tabela-experimento: desenho x não-escolha x placar

| Instituto | Modo | Entrev. humano | Carga | Cédula 2º turno | Não-esc. | Lula | Flávio | Gap |
|---|---|---|---|---|---:|---:|---:|---:|
| **Genial/Quaest** (10-13 jul) | presencial domiciliar | sim | ~101 itens | 3 saídas lidas | **18** | **45** | **37** | **+8** |
| **PoderData/Aya** (12-15 jul) | telefônica IVR/URA | não | 17 itens | 2 saídas (teclado) | 12 | 45 | 43 | +2 |
| PoderData/Aya (21-24 jun) | telefônica IVR/URA | não | 17 itens | 2 saídas (teclado) | 11 | 46 | 43 | +3 |
| Datafolha (17-19 jun) | presencial fluxo | sim | n/d | registra não-voto | 10 | 47 | 43 | +4 |
| BTG/Nexus (jul) | presencial domiciliar | sim | n/d | n/d | 9 | 47 | 44 | +3 |
| Futura/Apex (7-11 jul) | presencial | sim | n/d | oferece b/n/abst. | 7,6 | 46,3 | 46,1 | +0,2 |
| Meio/Ideia (3-6 jul) | telefônica voz | sim | n/d | n/d | 15 | 45 | 40 | +5 |
| AtlasIntel (~1 jul) | recrutamento digital | não | n/d | forced-choice | 8,9 | 48,8 | 42,3 | +6,5 |

A Quaest está sozinha no extremo: não-escolha 18 e gap 8, quando o campo inteiro fica entre
7,6 e 15 de não-escolha e 0,2 e 6,5 de gap. Flávio na Quaest é 37; em todo o resto, 40 a 46.

## O contraste de cédula (Fato documental, questionários primários)

Quaest Q23-26, presencial, ~101 itens: "você votaria no [nome], no [nome], votaria em
branco/nulo ou não iria votar?" mais indeciso (88). Três saídas de não-escolha lidas em voz alta.

PoderData Q7, URA/teclado, 17 itens: "em quem você votaria? ... branco ou nulo, tecle 3;
não sabe, tecle 4." Duas saídas de não-escolha, e nenhuma opção nomeada "não iria votar".

Contra a Quaest, a PoderData muda três eixos ao mesmo tempo: sem entrevistador humano
(retira a desejabilidade do face a face), 17 contra 101 itens (retira a fadiga do
instrumento longo) e uma saída de não-escolha a menos (não lê "não iria votar", exatamente
a saída para onde a série da Quaest mostrava a direita não-bolsonarista vazar, 9 para 15).

## Veredito: confirma ou não a predição da H-A?

SIM, no nível do resultado, com um caveat de mecanismo declarado. Trocado o instrumento, o
Flávio que falta reaparece: não-escolha 12 (contra 18), Flávio 43 (contra 37), gap 2
(contra 8), exatamente o consenso presencial de Datafolha (43) e Nexus (44). É a assinatura
que a H-A prevê. É o braço natural do split-ballot que a Quaest não roda.

Caveat honesto: é braço natural, não controlado. A PoderData também oferece branco/nulo, logo
a oferta nua não explica sozinha os 18 da Quaest (a PoderData oferece e fica em 12). O que
distingue a Quaest é o pacote de amplificadores mais a terceira saída não lida. O experimento
de uma noite que isolaria a variável só a Quaest pode publicar, e o retém.

Aleatoriedade: nenhum desenho é "o certo". A PoderData aproxima RDD (aleatório na origem,
mas viés de cobertura e resposta baixíssima de URA); a Quaest usa cotas domiciliares (viés de
seleção do entrevistador); a Atlas é painel digital (autosseleção). O ponto não é honestidade,
é que desenhos diferentes produzem não-escolha diferente, e a Quaest está no extremo. Modo
telefônico não garante não-escolha baixa: a Meio/Ideia, telefônica com voz humana, tem 15.

A peça de Cláudio Dantas ("PoderData/Aya desmonta Quaest") acerta a aritmética: a Quaest é o
ponto fora da curva. Declinamos a palavra "desmonta": o outlier é integralmente explicável por
desenho, sem supor má-fé. Concordamos com a conta, declinamos a inferência de fraude.
Veredito mantido: prova de opacidade, não de fraude.

---

## Post (primeira pessoa, sem hashtags, sem travessões)

Ontem a Quaest deu Lula 45 e Flávio 37, gap de 8, o menor Flávio de todo o mercado. Hoje
saiu a PoderData/Aya e eu fui direto conferir, porque ela é quase o oposto da Quaest como
instrumento. A Quaest é presencial, na porta de casa, com um questionário de 101 itens, e a
pergunta de segundo turno é lida em voz alta com três saídas de não-escolha: branco, nulo,
não iria votar. A PoderData é telefônica automatizada, você responde pelo teclado, sem
ninguém do outro lado, 17 perguntas, e a cédula oferece só branco ou nulo e não sabe.

O que aconteceu com o Flávio que falta? Ele reapareceu. PoderData: Lula 45, Flávio 43,
empate técnico. A não-escolha, que na Quaest é 18, caiu para 12. O Flávio de 37 virou 43,
que é exatamente onde o Datafolha e o Nexus o colocam. Trocado o instrumento, seis pontos
de Flávio voltaram para a cédula.

Isso é o braço natural do teste que eu venho pedindo à Quaest: um split-ballot que troca só
a cédula e mede o efeito. A PoderData não é um teste limpo, porque muda três coisas de uma
vez: tira o entrevistador, encurta o questionário e oferece uma saída de não-escolha a
menos. E, sendo honesto, ela também oferece branco e nulo, então a oferta sozinha não
explica os 18 da Quaest. O que explica é o pacote inteiro, mais a terceira saída, o "não
iria votar", que a Quaest lê e a PoderData não.

Fica a nuance que ninguém gosta de ouvir: nenhum desenho é o certo. Telefônico tem viés de
cobertura, presencial tem viés de seleção, online tem autosseleção. O ponto não é quem
mente. É que desenhos diferentes produzem não-escolha diferente, e a Quaest está no extremo,
sozinha. O Cláudio Dantas disse que a PoderData desmonta a Quaest. A aritmética dele está
certa, a Quaest é o ponto fora da curva. Mas eu não uso a palavra desmonta, porque tudo isso
é explicável pelo desenho, sem acusar ninguém. Prova de opacidade, não de fraude. O teste de
uma noite que fecharia a questão a Quaest tem, e não publica.
