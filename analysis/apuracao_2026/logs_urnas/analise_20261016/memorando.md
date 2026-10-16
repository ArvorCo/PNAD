# Logs das urnas, 1º turno de 2026: diagnósticos sem disparo, bateria, biometria e régua de atenção

Memorando interno de análise, somente leitura. Base: `secoes.csv.gz` com 499.176 seções lidas (`indice.json`, gerado em 2026-10-16, versão do leitor 11). Todo número abaixo sai de `analise_logs.py`, no mesmo diretório. Atipicidade operacional não é irregularidade; ALERTA não é ERRO; nenhuma conta usa voto em candidato.

Contagens publicadas conferidas: as 21 marcas com ocorrência na coluna `sinais` reproduzem exatamente `indice.json/criterios` (por exemplo, bateria 117.016, sinalizadas 170.146).

## 1. Os quatro diagnósticos de rapidez com zero seções

**Conferência de identificação.** As referências (mediana) e escalas (1,4826 × MAD com piso) foram recalculadas a partir do próprio CSV com a função de `criterios.py` e coincidem com as colunas publicadas em todos os casos:

| referência | mediana confere | escala confere |
|---|---|---|
| referencia_voto | sim | sim |
| referencia_cadencia | sim | sim |
| referencia_rajada | sim | sim |
| processo_biometrica | sim | sim |
| processo_biografica | sim | sim |
| processo_sem_biometria | sim | sim |

Avaliáveis recalculados contra `indice.json`: tempo_rapido 497.806 (497.806 publicado), cadencia_rapida 497.779 (497.779), rajada_rapida 496.548 (496.548), processo_rapido 496.519 seções na união dos três tipos (496.519).

**Controles positivos.** Com as mesmas colunas, as regras irmãs reproduzem tempo_lento = 855 e identificacao_lenta = 595, iguais ao publicado. Uma seção fictícia injetada no maior grupo (SP × UE2020 × 6, 41.006 seções) com mediana de 22,9 s, 45% da referência de 51,0 s (escala 4,45 s), dispara a regra. O mecanismo identifica rapidez quando ela existe; o zero não é defeito de código, de junção ou de valores ausentes.

**Distância até disparar.** z robusto = (valor − referência) / escala. Fator = valor / limiar efetivo, em que o limiar é o menor entre referência − 4 escalas e metade da referência (na rajada, também metade da cadência da própria seção); um fator f significa que a mediana precisaria cair uma fração 1 − 1/f para disparar.

| diagnóstico | avaliáveis | z mínimo | seção do z mínimo | razão nessa seção | razão mínima | z nessa seção | fator mínimo | seção mais próxima (fator) |
|---|---|---|---|---|---|---|---|---|
| tempo_rapido | 497.806 | -4,00 | AM, zona 1, seção 956, mun. 02550 | 0,786 | 0,571 | -2,00 | 1,333 | BA, zona 41, seção 304, mun. 39659 |
| cadencia_rapida | 497.779 | -2,77 | AM, zona 63, seção 548, mun. 02550 | 0,670 | 0,481 | -1,99 | 1,339 | AM, zona 63, seção 548, mun. 02550 |
| rajada_rapida | 496.548 | -3,92 | SP, zona 346, seção 640, mun. 71072 | 0,783 | 0,478 | -1,70 | 1,291 | AM, zona 30, seção 31, mun. 02372 |
| processo_rapido (biometrica) | 496.443 | -3,37 | MS, zona 12, seção 78, mun. 90654 | 0,815 | 0,684 | -2,81 | 1,367 | CE, zona 119, seção 438, mun. 14478 |
| processo_rapido (biografica) | 41.014 | -3,00 | AL, zona 49, seção 129, mun. 27510 | 0,662 | 0,500 | -2,98 | 1,310 | PR, zona 8, seção 462, mun. 78859 |
| processo_rapido (sem_biometria) | 57.466 | -2,42 | SC, zona 107, seção 100, mun. 82333 | 0,643 | 0,610 | -2,08 | 1,494 | GO, zona 74, seção 248, mun. 93718 |

Valores da seção mais próxima de disparar em cada diagnóstico:

| diagnóstico | valor (s) | referência (s) | escala (s) |
|---|---|---|---|
| tempo_rapido | 40,0 | 60,0 | 7,41 |
| cadencia_rapida | 75,0 | 112,0 | 13,34 |
| rajada_rapida | 57,3 | 88,8 | 8,75 |
| processo_rapido (biometrica) | 54,0 | 79,0 | 8,90 |
| processo_rapido (biografica) | 95,0 | 145,0 | 17,79 |
| processo_rapido (sem_biometria) | 65,0 | 87,0 | 10,75 |

**Contagens com regras alternativas** (seções avaliáveis; na linha de processo por seção, união dos três tipos):

| diagnóstico | z < −4 sem a metade | z ≤ −4 | z < −3 sem a metade | só valor < metade | regra completa, corte 3 | regra completa, corte 4 | valor < 0,7 × ref. | z em log < −4 | z em log < −3 | abaixo do percentil 0,1% do grupo |
|---|---|---|---|---|---|---|---|---|---|---|
| tempo_rapido | 0 | 1 | 10 | 0 | 0 | 0 | 75 | 1 | 70 | 328 |
| cadencia_rapida | 0 | 0 | 0 | 1 | 0 | 0 | 123 | 0 | 12 | 414 |
| rajada_rapida | 0 | 0 | 52 | 1 | 0 | 0 | 350 | 14 | 281 | 655 |
| processo_rapido (biometrica) | 0 | 0 | 7 | 0 | 0 | 0 | 2 | 0 | 61 | 335 |
| processo_rapido (biografica) | 0 | 0 | 1 | 0 | 0 | 0 | 72 | 1 | 28 | 88 |
| processo_rapido (sem_biometria) | 0 | 0 | 0 | 0 | 0 | 0 | 149 | 0 | 0 | 90 |
| processo_rapido (seções, união) | 0 | 0 | 8 | 0 | 0 | 0 | 223 | 1 | 89 | 508 |

Sensibilidade publicada em `indice.json` com corte 3: tempo_rapido 0, cadencia_rapida 0, rajada_rapida 0, processo_rapido 0. A regra completa com corte 3 recalculada também dá zero nos quatro.

Peso de cada condição:

| diagnóstico | metade é a condição mais exigente (% das seções) | z mediano exigido pela metade | escala/referência mediana | seções em grupo onde ref − 4 escalas ≤ 0 | z mínimo em log |
|---|---|---|---|---|---|
| tempo_rapido | 89,7 | -5,65 | 0,089 | 0 | -4,47 |
| cadencia_rapida | 60,5 | -4,34 | 0,115 | 952 | -3,38 |
| rajada_rapida | 88,6 | -5,30 | 0,094 | 2.329 | -4,81 |
| processo_rapido (biometrica) | 93,2 | -5,90 | 0,085 | 0 | -3,66 |
| processo_rapido (biografica) | 46,5 | -3,96 | 0,126 | 0 | -4,24 |
| processo_rapido (sem_biometria) | 4,1 | -2,83 | 0,177 | 202 | -2,84 |

**Leitura por diagnóstico.**

- **tempo_rapido**: zero genuíno. Nenhuma seção tem mediana de votação abaixo de metade da referência (razão mínima 0,571), e mesmo sem a condição da metade o z robusto mínimo é -4,00, exatamente no corte, que a regra exige estrito (`<`); com `≤` seria 1 seção (AM, zona 1, seção 956, mun. 02550: mediana 44,0 s, referência 56,0 s, escala no piso de 3,0 s; a metade exigiria menos de 28,0 s). A metade é a condição mais exigente em 89,7% das seções, mas o zero se mantém sem ela: a cauda inferior é curta.
- **cadencia_rapida**: zero genuíno e folgado. O z robusto mínimo é -2,77; nenhuma seção chega a −3. A única com razão abaixo de 0,5 (ZZ, zona 1, seção 3315, mun. 29661, razão 0,481) está em grupo tão disperso que fica a z -1,99. Em 952 seções, de 1 grupo (ZZ × UE2013 × 1), a referência menos 4 escalas é negativa e a condição de 4 escalas é inatingível.
- **rajada_rapida**: zero genuíno. É o diagnóstico que mais se aproxima: 52 seções têm z < −3, mas nenhuma < −4 (mínimo -3,92); a condição de metade da própria cadência também elimina candidatos.
- **processo_rapido**: zero genuíno nos três tipos (z mínimo: biometrica -3,37, biografica -3,00, sem_biometria -2,42). Na habilitação sem biometria a metade quase nunca é a condição mais exigente (4,1%), e mesmo assim nada passa.

Em resumo, o zero **não** decorre principalmente da dupla condição: o corte de 4 escalas sozinho já não marca nenhuma seção nos quatro diagnósticos. A razão é estrutural. Tempos têm piso físico e assimetria à direita, e uma escala simétrica (MAD) calibrada pelo miolo da distribuição torna −4 escalas praticamente inalcançável pela esquerda, enquanto +4 escalas é alcançado pela direita (tempo_lento = 855). A condição da metade seria redundante na prática; ela só ganharia peso se a escala fosse trocada.

**Limiar alternativo defensável (diagnóstico, sem mudar a regra publicada).** Duas famílias de alternativa, com propriedades distintas:

1. *Percentil 0,1% por grupo* (UF × modelo × cargos, mais faixa de volume na rajada, e tipo no processo), estrito: marca 328 (tempo), 414 (cadência), 655 (rajada) e 508 seções (processo, união). É uma fila de conferência de tamanho fixo, não um teste de anomalia: em grupos com menos de 1.001 seções o percentil cai entre o menor e o segundo menor valor, então marca o mínimo do grupo exista ou não algo fora do comum. Serve para ordenar visitas, não para afirmar rapidez atípica.
2. *z robusto na escala logarítmica* (razões em vez de diferenças, coerente com a assimetria dos tempos), corte −4: marca 1 (tempo), 0 (cadência), 14 (rajada) e 1 (processo); com −3, 70, 12, 281 e 89. É a alternativa estatisticamente coerente e confirma o zero: mesmo com escala adequada à assimetria, quase nenhuma seção é muito mais rápida que os pares.

Recomendação: manter a regra publicada e registrar no catálogo que o zero foi verificado com as duas alternativas acima. Qualquer troca precisa de registro prévio de versão, porque escolher o corte depois de ver os dados é seleção.

## 2. Bateria: 117.016 seções

A regra conta mensagens do dia (4 ou 5/10) com “operando” e “bateria interna”. A releitura dos ZIPs originais das seções marcadas, com o mesmo filtro, reproduz `eventos_bateria` de `metricas` em 117.008 de 117.016 seções; as 8 diferenças vêm da deduplicação de linhas e da exclusão de identificadores feitas pelo leitor.

Vocabulário nos originais (10 seções marcadas por modelo, sorteio com semente fixa; mensagens com “bateria”, dígitos trocados por #):

| mensagem | conta na regra | aplicativos | modelos | seções (de 40) | mensagens |
|---|---|---|---|---|---|
| Urna operando na bateria interna | sim | VOTA | UE2013, UE2015, UE2020, UE2022 | 38 | 89 |
| Bateria interna com carga plena | não | GAP | UE2013, UE2015, UE2020, UE2022 | 27 | 31 |
| Carga da [ALIMENTAÇÃO BATERIA INTERNA]: [PLENA] | não | VOTA | UE2013, UE2015, UE2020, UE2022 | 26 | 56 |
| Carga da [ALIMENTAÇÃO BATERIA INTERNA]: [PARCIAL] | não | VOTA | UE2013, UE2015, UE2020, UE2022 | 20 | 41 |
| Urna ligada conectada na rede CA em [#V] e na Bateria Interna com [#V/#A] | não | VOTA | UE2020, UE2022 | 20 | 389 |
| Urna operando com bateria interna | sim | GAP | UE2013, UE2015, UE2020, UE2022 | 18 | 18 |
| Bateria interna com carga parcial | não | GAP | UE2013, UE2015, UE2020, UE2022 | 15 | 15 |
| Urna ligada desconectada da rede CA em [#V] e na Bateria Interna com [#V/-#A] | não | VOTA | UE2020, UE2022 | 7 | 16 |
| Carga da [ALIMENTAÇÃO BATERIA INTERNA]: [CRÍTICA] | não | VOTA | UE2013, UE2015 | 2 | 2 |
| Carga da [ALIMENTAÇÃO BATERIA EXTERNA]: [PARCIAL] | não | VOTA | UE2015 | 1 | 2 |
| Urna operando na bateria externa | não | VOTA | UE2015 | 1 | 2 |

Só as linhas com “conta na regra” = sim entram no diagnóstico. A leitura periódica de tensão das UE2020/UE2022 e os avisos de carga não contam; a marca exige uma passagem para a bateria. Na base inteira, 93,0% das mensagens do GAP que contam estão antes da zerésima, ou seja, na partida da urna. A regra também não conta “Urna operando na bateria externa” (vista numa UE2015 da amostra) nem a leitura “desconectada da rede CA” das UE2020/UE2022; uma seção que tenha só esses registros fica sem marca.

**Quando a passagem para a bateria aconteceu** (seção classificada pela fase mais relevante; janela de votação = do primeiro ao último cômputo):

| classe | seções | % das marcadas |
|---|---|---|
| durante a votação | 67.750 | 57,9 |
| só antes da zerésima | 32.021 | 27,4 |
| entre zerésima e 1º voto | 14.416 | 12,3 |
| só após o último voto | 2.829 | 2,4 |

Mensagens por aplicativo e fase (contagem de mensagens, não de seções):

| aplicativo | antes da zerésima | após encerramento | após o último voto | durante a votação | zerésima ao 1º voto |
|---|---|---|---|---|---|
| ATUE | 61 | 0 | 0 | 77 | 26 |
| GAP | 42.566 | 85 | 51 | 2.189 | 860 |
| SCUE | 1 | 17 | 0 | 3 | 0 |
| VOTA | 50.825 | 2.657 | 4.423 | 193.126 | 43.266 |

**Contagem censurada.** Entre 96.305 seções marcadas com uma única partida do sistema, 7.553 têm exatamente 10 mensagens do VOTA, 742 têm 9 e só 3 têm mais de 10. O padrão é compatível com um limite de 10 registros por sessão do aplicativo (não documentado aqui: o PDF de formato do log não foi lido). Na prática, o número de mensagens não mede a duração nem a quantidade de quedas acima de 10.

**Simultaneidade.** Das 67.750 seções com passagem durante a votação, 41.828 (61,7%) têm ao menos uma mensagem a até 60 s de mensagens de 5 ou mais outras seções do mesmo município, e 26.847 (39,6%) de 20 ou mais. Num nulo em que os mesmos horários são sorteados uniformemente na janela de votação de cada seção, essas parcelas seriam 13,8% e 5,8%. Só 12.678 (18,7%) ficam isoladas (nenhuma outra seção do município em ±60 s; nulo 42,9%). A coincidência no mesmo minuto em várias seções é a assinatura de evento de fornecimento compartilhado (local de votação ou rede), não de comportamento de urna isolada. O nulo uniforme ignora o perfil horário do movimento; serve de ordem de grandeza.

**Por modelo.** Comparação dentro da mesma zona (razão de chances de Mantel-Haenszel por UF × zona, referência UE2020):

| modelo | secoes | bateria | durante | % bateria | % durante votação |
|---|---|---|---|---|---|
| UE2013 | 11.403 | 1.830 | 931 | 16,0 | 8,2 |
| UE2013 + UE2015 | 622 | 203 | 144 | 32,6 | 23,2 |
| UE2015 | 87.931 | 16.395 | 9.263 | 18,6 | 10,5 |
| UE2020 | 200.395 | 49.097 | 28.592 | 24,5 | 14,3 |
| UE2020 + UE2022 | 196 | 111 | 81 | 56,6 | 41,3 |
| UE2022 | 198.629 | 49.380 | 28.739 | 24,9 | 14,5 |

| comparação | zonas com os dois modelos | OR bateria | OR durante a votação |
|---|---|---|---|
| UE2022 × UE2020 | 670 | 1,02 | 1,03 |
| UE2015 × UE2020 | 410 | 0,75 | 0,80 |
| UE2013 × UE2020 | 251 | 0,79 | 0,91 |

UE2020 e UE2022 se comportam igual dentro da mesma zona (OR 1,02 e 1,03). UE2013 e UE2015 registram menos (OR de 0,75 a 0,91); o dado não separa sensibilidade do sensor de diferença de instalação. Não há efeito de modelo que explique a massa. No exterior (ZZ, 1.281 seções, modelos UE2013, UE2015) há 0 marcas de bateria; a causa não foi investigada.

**Por UF** (nenhuma UF passa de 50%):

| uf | secoes | bateria | % bateria | durante | % durante votação | % simultânea (das durante) |
|---|---|---|---|---|---|---|
| MS | 7.106 | 3.078 | 43,3 | 2.258 | 31,8 | 80,5 |
| PR | 27.142 | 8.225 | 30,3 | 4.217 | 15,5 | 58,5 |
| SP | 103.656 | 31.229 | 30,1 | 20.816 | 20,1 | 88,2 |
| PA | 20.827 | 6.077 | 29,2 | 4.322 | 20,8 | 65,0 |
| PI | 10.225 | 2.619 | 25,6 | 1.597 | 15,6 | 20,0 |
| TO | 4.384 | 1.096 | 25,0 | 743 | 16,9 | 62,3 |
| MT | 8.287 | 2.003 | 24,2 | 1.303 | 15,7 | 68,2 |
| MA | 18.093 | 4.288 | 23,7 | 2.320 | 12,8 | 29,6 |
| BA | 35.476 | 8.154 | 23,0 | 4.827 | 13,6 | 42,5 |
| PE | 21.418 | 4.837 | 22,6 | 2.500 | 11,7 | 45,0 |
| RR | 1.519 | 333 | 21,9 | 201 | 13,2 | 59,7 |
| RJ | 37.675 | 8.160 | 21,7 | 4.763 | 12,6 | 74,8 |
| CE | 23.765 | 4.956 | 20,9 | 2.647 | 11,1 | 29,7 |
| GO | 15.686 | 3.229 | 20,6 | 1.531 | 9,8 | 48,7 |
| AL | 7.101 | 1.453 | 20,5 | 929 | 13,1 | 40,2 |
| RS | 27.547 | 5.523 | 20,0 | 2.742 | 10,0 | 30,0 |
| AC | 2.270 | 450 | 19,8 | 199 | 8,8 | 44,2 |
| DF | 6.969 | 1.373 | 19,7 | 643 | 9,2 | 72,0 |
| AM | 8.157 | 1.570 | 19,2 | 829 | 10,2 | 49,9 |
| RO | 4.698 | 849 | 18,1 | 362 | 7,7 | 45,0 |
| RN | 8.115 | 1.423 | 17,5 | 796 | 9,8 | 22,5 |
| SC | 17.326 | 2.982 | 17,2 | 1.343 | 7,8 | 40,9 |
| MG | 52.060 | 8.744 | 16,8 | 4.126 | 7,9 | 48,5 |
| SE | 5.923 | 918 | 15,5 | 227 | 3,8 | 15,0 |
| AP | 1.914 | 296 | 15,5 | 124 | 6,5 | 12,1 |
| ES | 9.844 | 1.513 | 15,4 | 556 | 5,6 | 37,6 |
| PB | 10.712 | 1.638 | 15,3 | 829 | 7,7 | 38,1 |
| ZZ | 1.281 | 0 | 0,0 | 0 | 0,0 | n/d |

Concentração local: 227 de 2.641 zonas têm mais de 50% das seções marcadas e 150 têm mais de 50% com passagem durante a votação; 340 de 3.932 municípios com 20 seções ou mais têm mais da metade das seções com passagem durante a votação. A marca cai com o tamanho da seção:

| comparecimento | secoes | % bateria | % durante votação |
|---|---|---|---|
| <50 | 572 | 29,7 | 16,6 |
| 50-99 | 4.339 | 30,5 | 20,6 |
| 100-149 | 13.479 | 27,6 | 17,7 |
| 150-199 | 58.324 | 26,0 | 16,1 |
| 200-249 | 141.923 | 25,0 | 15,2 |
| 250-299 | 201.577 | 22,7 | 12,8 |
| 300-349 | 74.476 | 19,7 | 9,8 |
| 350+ | 4.486 | 15,0 | 6,4 |

**Para o fiscal.** Como marca única, “bateria” é ruído de massa: 23,4% das seções; 27,4% das marcadas só têm passagem antes da zerésima (compatível com urna ligada antes de conectada à rede ou instabilidade na preparação; o log não distingue) e a associação com os demais sinais é fraca (lift de 0,8 a 2,1 nos pares com 100 seções ou mais; os maiores são ciclos_incompletos 2,1, reinicio_sistema 2,0, reinicios 2,0). A parte informativa é estreita: passagem para bateria **durante a votação** (67.750 seções), separada em (i) simultânea com 5 ou mais seções do município (41.828), que pede conferir na ata a falta de energia do local e se o atendimento parou; (ii) isolada (12.678), que pede conferir tomada, cabo e fonte daquela urna; e (iii) intermediária, com 1 a 4 outras seções (13.244). Nenhuma informa a duração, que o log da regra não mede.

## 3. Biometria

Taxas nacionais (seções com categorias conciliadas ao BU, 497.885): sem biometria / comparecimento = 6.940.073 / 124.930.783 = 5,56%; biográficas / (biométricas + biográficas) = 8.342.036 / 117.990.710 = 7,07%. As duas taxas têm denominadores diferentes e não se somam. Estados da biometria: confere 497.885, ausente_bu 1.281, divergente 10 (ausente_bu: 1.281 seções, das quais 1.281 no exterior).

Cobertura das referências: 496.501 seções elegíveis para sem_biometria_alta, das quais 57.786 (11,6%) ficam sem referência porque o grupo UF × município × zona × modelo tem menos de 30 seções; para biografica_alta, 57.888 de 496.382. Essas seções nunca podem ser marcadas, por mais alta que seja a taxa.

**Por UF**, ordenado pela mediana de sem biometria por seção:

| uf | seções | taxa sem bio % | mediana sem bio % | p90 sem bio % | ref. mediana % | sem_biometria_alta | % sem_bio_alta | taxa biográfica % | mediana biográfica % | biografica_alta | % biog_alta |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MG | 52.060 | 11,20 | 10,95 | 23,03 | 12,59 | 202 | 0,39 | 7,53 | 6,97 | 177 | 0,34 |
| RJ | 37.673 | 7,07 | 7,32 | 12,68 | 7,96 | 23 | 0,06 | 7,59 | 7,08 | 126 | 0,33 |
| ES | 9.843 | 20,91 | 6,45 | 56,15 | 10,25 | 138 | 1,40 | 8,14 | 7,61 | 51 | 0,52 |
| PE | 21.418 | 7,67 | 5,10 | 16,42 | 4,44 | 557 | 2,60 | 6,77 | 6,30 | 64 | 0,30 |
| RS | 27.546 | 7,92 | 4,51 | 19,18 | 5,17 | 132 | 0,48 | 8,93 | 8,29 | 86 | 0,31 |
| BA | 35.475 | 4,72 | 4,00 | 8,06 | 4,00 | 723 | 2,04 | 7,65 | 6,91 | 201 | 0,57 |
| SP | 103.652 | 4,35 | 3,52 | 9,16 | 5,13 | 101 | 0,10 | 6,30 | 5,82 | 224 | 0,22 |
| PA | 20.827 | 4,04 | 3,28 | 7,74 | 3,35 | 462 | 2,22 | 5,63 | 5,13 | 88 | 0,42 |
| CE | 23.765 | 4,02 | 3,26 | 7,69 | 3,20 | 472 | 1,99 | 7,17 | 6,42 | 81 | 0,34 |
| GO | 15.686 | 4,43 | 3,16 | 8,15 | 3,03 | 660 | 4,21 | 7,12 | 6,38 | 35 | 0,22 |
| AM | 8.157 | 4,47 | 3,15 | 8,57 | 3,04 | 319 | 3,91 | 5,64 | 5,21 | 21 | 0,26 |
| SC | 17.326 | 5,14 | 3,14 | 12,85 | 2,00 | 177 | 1,02 | 7,97 | 7,37 | 37 | 0,21 |
| MA | 18.093 | 3,69 | 3,00 | 7,39 | 3,07 | 250 | 1,38 | 6,22 | 5,66 | 108 | 0,60 |
| RN | 8.114 | 3,75 | 3,00 | 6,73 | 3,15 | 180 | 2,22 | 8,22 | 7,84 | 13 | 0,16 |
| MT | 8.287 | 3,76 | 2,92 | 7,97 | 3,53 | 56 | 0,68 | 6,99 | 6,64 | 19 | 0,23 |
| AC | 2.270 | 3,66 | 2,66 | 7,88 | 2,41 | 71 | 3,13 | 5,18 | 4,74 | 5 | 0,22 |
| AL | 7.101 | 3,65 | 2,61 | 6,67 | 2,72 | 183 | 2,58 | 6,77 | 5,94 | 10 | 0,14 |
| AP | 1.914 | 3,73 | 2,38 | 7,33 | 2,44 | 61 | 3,19 | 4,57 | 4,35 | 1 | 0,05 |
| MS | 7.106 | 4,10 | 2,36 | 11,41 | 2,60 | 37 | 0,52 | 8,15 | 7,63 | 34 | 0,48 |
| DF | 6.969 | 3,14 | 2,25 | 6,03 | 2,28 | 177 | 2,54 | 4,99 | 4,67 | 2 | 0,03 |
| PB | 10.712 | 3,02 | 2,22 | 5,76 | 2,37 | 188 | 1,76 | 7,19 | 6,67 | 15 | 0,14 |
| TO | 4.384 | 2,84 | 2,16 | 5,80 | 2,08 | 48 | 1,09 | 5,44 | 5,10 | 5 | 0,11 |
| SE | 5.923 | 3,64 | 2,02 | 7,93 | 1,41 | 263 | 4,44 | 7,02 | 6,55 | 13 | 0,22 |
| RR | 1.519 | 3,07 | 1,60 | 5,89 | 1,53 | 75 | 4,94 | 3,96 | 3,68 | 2 | 0,13 |
| RO | 4.698 | 1,63 | 1,19 | 3,48 | 1,05 | 39 | 0,83 | 6,35 | 5,99 | 10 | 0,21 |
| PI | 10.225 | 2,04 | 0,76 | 4,86 | 0,70 | 324 | 3,17 | 8,83 | 8,21 | 26 | 0,25 |
| PR | 27.142 | 0,67 | 0,40 | 1,75 | 0,37 | 0 | 0,00 | 7,53 | 6,98 | 52 | 0,19 |

A correlação entre a mediana de sem biometria da UF e a parcela de seções marcadas é -0,33: UFs com cadastro biométrico mais incompleto (MG, RJ, ES no topo da mediana) **não** são as mais marcadas. A referência local absorve o nível: a mediana da referência acompanha a mediana da UF, e a marca só aparece quando uma seção destoa da própria zona e do próprio modelo. O efeito da escolha do estrato:

| medida | referência | sinalizadas | maiores UFs |
|---|---|---|---|
| sem_biometria | publicada: UF × município × zona × modelo | 5.918 | BA 723, GO 660, PE 557, CE 472 |
| sem_biometria | UF × modelo | 10.392 | PE 1809, RS 1484, BA 768, SC 765 |
| sem_biometria | Brasil × modelo | 24.111 | MG 11140, ES 3636, RS 3345, PE 1955 |
| biografica | publicada: UF × município × zona × modelo | 1.506 | SP 224, BA 201, MG 177, RJ 126 |
| biografica | UF × modelo | 3.128 | SP 485, BA 474, MG 412, RS 215 |
| biografica | Brasil × modelo | 4.551 | RS 859, MG 785, BA 715, PI 330 |

Com referência nacional por modelo, MG e ES dominariam as marcas de sem biometria (diferença de cadastro entre regiões); com a referência publicada, lideram BA, GO, PE, CE (seções que destoam da própria zona).

**Por modelo** (biográfica é muito mais alta nas UE2013/UE2015; a referência inclui o modelo e absorve isso):

| modelo | secoes | sem_bio_alta | biog_alta | mediana_sem_bio | mediana_biog |
|---|---|---|---|---|---|
| UE2013 | 11.403 | 99 | 131 | 3,28 | 10,30 |
| UE2013 + UE2015 | 622 | 0 | 0 | 4,44 | 10,60 |
| UE2015 | 87.931 | 952 | 325 | 4,02 | 9,68 |
| UE2020 | 200.395 | 2.393 | 533 | 3,42 | 5,92 |
| UE2020 + UE2022 | 196 | 0 | 0 | 2,83 | 5,47 |
| UE2022 | 198.629 | 2.474 | 517 | 3,33 | 5,86 |

**Por tamanho** (comparecimento). Sem biometria alta cresce levemente com o tamanho; biográfica alta se concentra em seções pequenas. Mecanismo provável, não testado aqui: a variação aleatória de uma proporção é maior com poucos eleitores (na taxa nacional de 7,07%, desvio-padrão binomial de 3,0 pp com 75 habilitações e 1,5 pp com 275), enquanto a escala da referência é comum ao grupo e a regra não ajusta pelo tamanho; a mediana de biográficas também é maior nas seções pequenas:

| comparecimento | secoes | sem_bio_alta | biog_alta | mediana_sem_bio | mediana_biog |
|---|---|---|---|---|---|
| <50 | 572 | 0 | 0 | 2,13 | 8,16 |
| 50-99 | 4.339 | 42 | 121 | 1,32 | 9,09 |
| 100-149 | 13.479 | 106 | 232 | 2,86 | 8,76 |
| 150-199 | 58.324 | 568 | 370 | 3,25 | 7,78 |
| 200-249 | 141.923 | 1.676 | 420 | 3,24 | 7,00 |
| 250-299 | 201.577 | 2.453 | 312 | 3,70 | 6,15 |
| 300-349 | 74.476 | 1.009 | 49 | 3,76 | 5,56 |
| 350+ | 4.486 | 64 | 2 | 3,95 | 4,88 |

Seções com 50% ou mais sem biometria: 1.991; só 133 marcadas e 24 sem referência; as outras 1.834 não destoam o bastante da referência da própria zona e modelo, cuja mediana nelas é 50,9%. Seções com 50% ou mais de biográficas: 153; 87 marcadas e 64 sem referência.

**Biográfica quase total.** 69 seções têm 90% ou mais de habilitações biográficas; UE2013 66, UE2022 1, UE2013 + UE2015 1, UE2015 1. As UE2013 são 2,3% das seções e 95,7% desse grupo. Só 41 estão marcadas; 27 não têm referência e 1 tem denominador menor que 50. Contagens agregadas de mensagens nos originais (medianas por voto computado):

| grupo | seções | biográficas/cômputos | solicita_digital | capturada_digital | nao_corresponde | dado_pessoal_manual | mesario_habilitou | ano_nasc_igual |
|---|---|---|---|---|---|---|---|---|
| biográfica >= 90% | 69 | 0,915 | 3,773 | 3,745 | 0,009 | 0,927 | 0,617 | 0,045 |
| controle UE2013 (< 20%) | 300 | 0,093 | 1,637 | 1,592 | 0,000 | 0,096 | 0,059 | 0,031 |
| controle UE2020/UE2022 (< 20%) | 300 | 0,053 | 1,433 | 1,399 | 0,000 | 0,055 | 0,037 | 0,036 |

Nessas seções a urna pediu e capturou digitais (3,77 pedidos por voto, contra 1,43 a 1,64 nos controles) e depois seguiu para habilitação manual por dado pessoal (0,93 por voto, contra 0,06 a 0,10). Ou seja, a biometria foi tentada e não reconheceu; o log não sustenta a hipótese de mesa que pulou a leitura. A mensagem explícita de não correspondência é rara, então o log não diz por que o reconhecimento falhou (sensor, calibração, base biométrica carregada ou outro motivo).

**As 20 seções com maior sem_biometria_pct** (seções com categorias conciliadas):

| uf | zona | município | secao | modelo | comparecimento | sem bio % | ref. % | escala pp | pares | sinalizada |
|---|---|---|---|---|---|---|---|---|---|---|
| ES | 9 | Santa Maria de Jetibá | 70 | UE2015 | 256 | 84,8 | 61,4 | 8,8 | 94 | não |
| PE | 16 | Ipojuca | 225 | UE2020 | 273 | 81,0 | 0,4 | 1,0 | 264 | sim |
| ES | 51 | Governador Lindenberg | 73 | UE2022 | 159 | 78,6 | 62,6 | 13,3 | 31 | não |
| ES | 9 | Santa Maria de Jetibá | 30 | UE2015 | 264 | 77,7 | 61,4 | 8,8 | 94 | não |
| ES | 51 | Governador Lindenberg | 74 | UE2022 | 155 | 76,8 | 62,6 | 13,3 | 31 | não |
| ES | 35 | Vargem Alta | 149 | UE2020 | 167 | 76,6 | 60,7 | 9,9 | 54 | não |
| ES | 9 | Santa Maria de Jetibá | 95 | UE2015 | 271 | 76,4 | 61,4 | 8,8 | 94 | não |
| ES | 35 | Vargem Alta | 146 | UE2020 | 193 | 76,2 | 60,7 | 9,9 | 54 | não |
| ES | 51 | Governador Lindenberg | 61 | UE2022 | 234 | 76,1 | 62,6 | 13,3 | 31 | não |
| ES | 9 | Santa Maria de Jetibá | 87 | UE2015 | 314 | 75,2 | 61,4 | 8,8 | 94 | não |
| ES | 54 | Cariacica | 298 | UE2015 | 232 | 75,0 | 50,9 | 7,5 | 402 | não |
| BA | 45 | Senhor do Bonfim | 324 | UE2022 | 220 | 75,0 | 3,6 | 2,1 | 173 | sim |
| ES | 51 | Rio Bananal | 40 | UE2022 | 189 | 74,6 | 57,3 | 12,2 | 54 | não |
| ES | 51 | Rio Bananal | 12 | UE2022 | 231 | 74,5 | 57,3 | 12,2 | 54 | não |
| PE | 145 | Petrolina | 449 | UE2022 | 246 | 74,4 | 4,0 | 3,3 | 248 | sim |
| ES | 9 | Santa Maria de Jetibá | 101 | UE2015 | 298 | 74,2 | 61,4 | 8,8 | 94 | não |
| ES | 35 | Vargem Alta | 151 | UE2020 | 248 | 73,8 | 60,7 | 9,9 | 54 | não |
| ES | 20 | Aracruz | 159 | UE2020 | 201 | 73,6 | 53,7 | 12,4 | 239 | não |
| ES | 51 | Governador Lindenberg | 70 | UE2022 | 246 | 73,6 | 62,6 | 13,3 | 31 | não |
| ES | 51 | Rio Bananal | 37 | UE2022 | 192 | 73,4 | 57,3 | 12,2 | 54 | não |

**As 20 seções com maior biografica_pct:**

| uf | zona | município | secao | modelo | comparecimento | bio+biog | biog. % | ref. % | escala pp | pares | sinalizada |
|---|---|---|---|---|---|---|---|---|---|---|---|
| GO | 49 | Trindade | 123 | UE2013 | 265 | 252 | 99,2 | 12,2 | 5,6 | 304 | sim |
| BA | 162 | São Francisco do Conde | 14 | UE2013 | 220 | 219 | 99,1 | 8,7 | 3,4 | 108 | sim |
| BA | 33 | Simões Filho | 139 | UE2013 | 200 | 184 | 98,9 | 9,9 | 3,8 | 260 | sim |
| ES | 53 | Serra | 43 | UE2013 | 217 | 83 | 98,8 | 12,8 | 5,5 | 377 | sim |
| BA | 186 | Dias d'Ávila | 102 | UE2013 | 259 | 247 | 98,8 | 8,9 | 3,5 | 168 | sim |
| MS | 27 | Angélica | 108 | UE2013 | 174 | 158 | 98,7 | n/d | n/d | 2 | não |
| BA | 128 | São Sebastião do Passé | 54 | UE2013 | 238 | 227 | 98,7 | 8,1 | 3,6 | 105 | sim |
| BA | 180 | Lauro de Freitas | 386 | UE2013 | 306 | 292 | 98,6 | 9,5 | 3,9 | 413 | sim |
| ES | 26 | Serra | 651 | UE2013 | 279 | 278 | 98,6 | 11,9 | 4,5 | 306 | sim |
| PE | 54 | Jataúba | 185 | UE2013 | 288 | 261 | 98,5 | n/d | n/d | 13 | não |
| BA | 128 | Terra Nova | 179 | UE2013 | 206 | 193 | 98,4 | 9,8 | 3,3 | 35 | sim |
| BA | 180 | Lauro de Freitas | 331 | UE2013 | 260 | 243 | 98,4 | 9,5 | 3,9 | 413 | sim |
| PR | 86 | Tapejara | 218 | UE2013 | 176 | 173 | 98,3 | n/d | n/d | 9 | não |
| PR | 19 | Tomazina | 55 | UE2013 | 227 | 227 | 98,2 | n/d | n/d | 11 | não |
| PR | 96 | Nova Londrina | 86 | UE2013 | 227 | 225 | 98,2 | n/d | n/d | 23 | não |
| SC | 106 | Navegantes | 19 | UE2013 | 230 | 222 | 98,2 | n/d | n/d | 28 | não |
| BA | 162 | São Francisco do Conde | 96 | UE2013 | 245 | 242 | 97,9 | 8,7 | 3,4 | 108 | sim |
| SP | 392 | São Paulo | 34 | UE2013 | 195 | 166 | 97,6 | n/d | n/d | 12 | não |
| ES | 26 | Serra | 559 | UE2013 | 269 | 174 | 97,1 | 11,9 | 4,5 | 306 | sim |
| BA | 33 | Simões Filho | 222 | UE2013 | 292 | 275 | 97,1 | 9,9 | 3,8 | 260 | sim |

**Explicações operacionais plausíveis e o que o fiscal confere.** (a) *Sem biometria*: categoria do BU para eleitor sem biometria no cadastro; o nível é cadastral (revisão biométrica não concluída na região, eleitores transferidos ou inscritos sem coleta). O fiscal compara com a lista de eleitores sem biometria da seção e do local, antes de atribuir a taxa à urna. (b) *Biográfica*: eleitor com biometria cadastrada que não foi reconhecido e foi habilitado por dado pessoal; explicações possíveis são leitor sujo ou defeituoso, digitais desgastadas e procedimento da mesa. O padrão de quase 100% concentrado em UE2013, com tentativas registradas, aponta para o equipamento ou a base daquela urna, não para escolha da mesa. O fiscal confere na ata o registro de falha do leitor, eventual troca de urna, a quantidade de habilitações por dado pessoal e se a mesa seguiu o número previsto de tentativas. Nenhuma das duas marcas é voto irregular.

## 4. Co-ocorrência e famílias

Matriz de co-ocorrência (seções com ambos; diagonal = total do sinal). Legenda: S01 assinatura; S02 bateria; S03 biografica_alta; S04 biometria_divergente; S05 cancelamentos_habilitacao; S06 ciclos_incompletos; S07 contagem_divergente; S08 erro_tecnico; S09 identidade_nao_confirmada; S10 identificacao_lenta; S11 inspecao_prolongada; S12 intervalo_longo; S13 reinicio_sistema; S14 reinicios; S15 relogio; S16 retomadas_inatividade; S17 sem_biometria_alta; S18 suspensoes; S19 tempo_lento; S20 texto_malformado; S21 zeresima_ausente.

|  | S01 | S02 | S03 | S04 | S05 | S06 | S07 | S08 | S09 | S10 | S11 | S12 | S13 | S14 | S15 | S16 | S17 | S18 | S19 | S20 | S21 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S01 | 18 | 7 | 0 | 0 | 0 | 8 | 0 | 18 | 0 | 0 | 0 | 5 | 10 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| S02 | 7 | 117.016 | 373 | 5 | 1.723 | 2.247 | 5 | 1.777 | 12 | 147 | 7.858 | 5.620 | 7.171 | 7.267 | 62 | 1.547 | 1.136 | 687 | 250 | 1 | 1 |
| S03 | 0 | 373 | 1.506 | 0 | 66 | 13 | 0 | 50 | 0 | 112 | 208 | 256 | 78 | 86 | 1 | 99 | 23 | 11 | 40 | 0 | 0 |
| S04 | 0 | 5 | 0 | 10 | 0 | 7 | 10 | 4 | 2 | 0 | 0 | 2 | 7 | 7 | 1 | 0 | 0 | 0 | 0 | 1 | 2 |
| S05 | 0 | 1.723 | 66 | 0 | 6.201 | 69 | 0 | 77 | 0 | 25 | 858 | 842 | 257 | 263 | 0 | 250 | 76 | 23 | 69 | 0 | 0 |
| S06 | 8 | 2.247 | 13 | 7 | 69 | 4.544 | 7 | 418 | 3 | 2 | 177 | 1.032 | 4.286 | 4.360 | 11 | 73 | 58 | 42 | 13 | 2 | 0 |
| S07 | 0 | 5 | 0 | 10 | 0 | 7 | 10 | 4 | 2 | 0 | 0 | 2 | 7 | 7 | 1 | 0 | 0 | 0 | 0 | 1 | 2 |
| S08 | 18 | 1.777 | 50 | 4 | 77 | 418 | 4 | 5.577 | 13 | 37 | 249 | 819 | 3.893 | 3.904 | 9 | 49 | 53 | 30 | 6 | 1 | 1 |
| S09 | 0 | 12 | 0 | 2 | 0 | 3 | 2 | 13 | 18 | 0 | 1 | 3 | 2 | 2 | 0 | 0 | 1 | 0 | 0 | 1 | 1 |
| S10 | 0 | 147 | 112 | 0 | 25 | 2 | 0 | 37 | 0 | 595 | 107 | 159 | 57 | 63 | 0 | 45 | 15 | 4 | 29 | 0 | 0 |
| S11 | 0 | 7.858 | 208 | 0 | 858 | 177 | 0 | 249 | 1 | 107 | 30.503 | 4.934 | 768 | 779 | 0 | 986 | 278 | 146 | 259 | 0 | 0 |
| S12 | 5 | 5.620 | 256 | 2 | 842 | 1.032 | 2 | 819 | 3 | 159 | 4.934 | 17.350 | 2.362 | 2.454 | 0 | 1.082 | 130 | 99 | 357 | 1 | 0 |
| S13 | 10 | 7.171 | 78 | 7 | 257 | 4.286 | 7 | 3.893 | 2 | 57 | 768 | 2.362 | 15.460 | 15.417 | 38 | 206 | 184 | 113 | 30 | 1 | 0 |
| S14 | 10 | 7.267 | 86 | 7 | 263 | 4.360 | 7 | 3.904 | 2 | 63 | 779 | 2.454 | 15.417 | 15.678 | 39 | 208 | 190 | 116 | 31 | 1 | 0 |
| S15 | 0 | 62 | 1 | 1 | 0 | 11 | 1 | 9 | 0 | 0 | 0 | 0 | 38 | 39 | 281 | 0 | 1 | 2 | 0 | 0 | 0 |
| S16 | 0 | 1.547 | 99 | 0 | 250 | 73 | 0 | 49 | 0 | 45 | 986 | 1.082 | 206 | 208 | 0 | 5.501 | 42 | 63 | 300 | 0 | 0 |
| S17 | 0 | 1.136 | 23 | 0 | 76 | 58 | 0 | 53 | 1 | 15 | 278 | 130 | 184 | 190 | 1 | 42 | 5.918 | 45 | 12 | 0 | 0 |
| S18 | 0 | 687 | 11 | 0 | 23 | 42 | 0 | 30 | 0 | 4 | 146 | 99 | 113 | 116 | 2 | 63 | 45 | 3.140 | 11 | 0 | 0 |
| S19 | 0 | 250 | 40 | 0 | 69 | 13 | 0 | 6 | 0 | 29 | 259 | 357 | 30 | 31 | 0 | 300 | 12 | 11 | 855 | 0 | 0 |
| S20 | 0 | 1 | 0 | 1 | 0 | 2 | 1 | 1 | 1 | 0 | 0 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| S21 | 0 | 1 | 0 | 2 | 0 | 0 | 2 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |

Pares mais redundantes (Jaccard = ambos / união; lift = observado / esperado sob independência):

| par | ambos | n_a | n_b | Jaccard | P(b|a) | P(a|b) | lift |
|---|---|---|---|---|---|---|---|
| biometria_divergente × contagem_divergente | 10 | 10 | 10 | 1,000 | 1,000 | 1,000 | 49.917,6 |
| reinicio_sistema × reinicios | 15.417 | 15.460 | 15.678 | 0,981 | 0,997 | 0,983 | 31,8 |
| ciclos_incompletos × reinicios | 4.360 | 4.544 | 15.678 | 0,275 | 0,960 | 0,278 | 30,5 |
| ciclos_incompletos × reinicio_sistema | 4.286 | 4.544 | 15.460 | 0,273 | 0,943 | 0,277 | 30,5 |
| erro_tecnico × reinicio_sistema | 3.893 | 5.577 | 15.460 | 0,227 | 0,698 | 0,252 | 22,5 |
| erro_tecnico × reinicios | 3.904 | 5.577 | 15.678 | 0,225 | 0,700 | 0,249 | 22,3 |
| biometria_divergente × zeresima_ausente | 2 | 10 | 2 | 0,200 | 0,200 | 1,000 | 49.917,6 |
| contagem_divergente × zeresima_ausente | 2 | 10 | 2 | 0,200 | 0,200 | 1,000 | 49.917,6 |
| inspecao_prolongada × intervalo_longo | 4.934 | 30.503 | 17.350 | 0,115 | 0,162 | 0,284 | 4,7 |
| biometria_divergente × texto_malformado | 1 | 10 | 2 | 0,091 | 0,100 | 0,500 | 24.958,8 |
| contagem_divergente × texto_malformado | 1 | 10 | 2 | 0,091 | 0,100 | 0,500 | 24.958,8 |
| intervalo_longo × reinicios | 2.454 | 17.350 | 15.678 | 0,080 | 0,141 | 0,157 | 4,5 |
| intervalo_longo × reinicio_sistema | 2.362 | 17.350 | 15.460 | 0,078 | 0,136 | 0,153 | 4,4 |
| biometria_divergente × identidade_nao_confirmada | 2 | 10 | 18 | 0,077 | 0,200 | 0,111 | 5.546,4 |
| contagem_divergente × identidade_nao_confirmada | 2 | 10 | 18 | 0,077 | 0,200 | 0,111 | 5.546,4 |

Pares com bateria (os maiores em contagem):

| par | ambos | n_a | n_b | Jaccard | P(b|a) | P(a|b) | lift |
|---|---|---|---|---|---|---|---|
| bateria × inspecao_prolongada | 7.858 | 117.016 | 30.503 | 0,056 | 0,067 | 0,258 | 1,10 |
| bateria × reinicios | 7.267 | 117.016 | 15.678 | 0,058 | 0,062 | 0,464 | 1,98 |
| bateria × reinicio_sistema | 7.171 | 117.016 | 15.460 | 0,057 | 0,061 | 0,464 | 1,98 |
| bateria × intervalo_longo | 5.620 | 117.016 | 17.350 | 0,044 | 0,048 | 0,324 | 1,38 |
| bateria × ciclos_incompletos | 2.247 | 117.016 | 4.544 | 0,019 | 0,019 | 0,494 | 2,11 |
| bateria × erro_tecnico | 1.777 | 117.016 | 5.577 | 0,015 | 0,015 | 0,319 | 1,36 |

Redundâncias: reinicio_sistema sem reinicios: 43; reinicios sem reinicio_sistema: 261; ciclos_incompletos sem reinício: 180; erro_tecnico sem reinício: 1.643; contagem_divergente == biometria_divergente: sim. reinicio_sistema e reinicios têm Jaccard 0,981; 96,0% de ciclos_incompletos e 70,0% de erro_tecnico acompanham reinicios; contagem_divergente e biometria_divergente marcam as mesmas 10 seções. Bateria tem lift de 0,8 a 2,1 com os sinais com que divide 100 seções ou mais (maiores: ciclos_incompletos 2,1, reinicio_sistema 2,0, reinicios 2,0).

**Famílias propostas** (cada sinal em uma só família; os quatro diagnósticos sem ocorrência ficam em Tempo de votação):

| família | sinais ativos | seções | só esta família |
|---|---|---|---|
| Energia e reinícios | bateria, reinicio_sistema, reinicios, erro_tecnico, ciclos_incompletos | 126.738 | 108.437 |
| Identificação do eleitor | sem_biometria_alta, biografica_alta, identificacao_lenta, cancelamentos_habilitacao | 13.911 | 8.601 |
| Tempo de votação | tempo_lento, retomadas_inatividade, suspensoes | 9.126 | 4.934 |
| Interrupções e inspeções | inspecao_prolongada, intervalo_longo | 42.919 | 26.819 |
| Conferência do arquivo | assinatura, relogio, contagem_divergente, biometria_divergente, zeresima_ausente, texto_malformado, identidade_nao_confirmada | 325 | 179 |

Seções só com bateria: 95.000. Número de famílias por seção: 0: 329.030, 1: 148.970, 2: 19.569, 3: 1.517, 4: 90.

Critério de agrupamento: lifts altos dentro da família (erro_tecnico × reinicios 22,3; ciclos_incompletos × reinicios 30,5; biografica_alta × identificacao_lenta 62,4; retomadas_inatividade × tempo_lento 31,8; inspecao_prolongada × intervalo_longo 4,7) e significado legível. Há ligações entre famílias que o leitor deve conhecer: identificacao_lenta × tempo_lento 28,5 e intervalo_longo × tempo_lento 12,0. suspensoes fica em Tempo de votação porque se associa a tempo_lento (2,0) e a retomadas_inatividade (1,8), não a inspecao_prolongada (0,8) nem a intervalo_longo (0,9). Interrupções e inspeções depende muito do tamanho: intervalo_longo marca 89,3% das seções com menos de 100 votantes e 0,61% das que têm 250 ou mais, porque poucos eleitores deixam intervalos longos entre votos.

## 5. Régua de atenção para o mapa (0 a 3)

Ordenação para fiscalização a partir dos logs. **Não é probabilidade de fraude, não é pontuação política e não usa voto.** Bateria é tratada como contexto: não conta como família, porque é de massa e quase independente dos demais sinais.

- **0** (a): nenhum sinal; só bateria; ou só inspeção breve, isto é, o único sinal fora a bateria é inspecao_prolongada com janela máxima de 5 a 10 min (inspeções abaixo de 5 min nunca são sinal; o corte de 10 min é escolha declarada desta régua).
- **1** (b): sinais de uma única família, sem contar bateria (pares redundantes como reinicio_sistema + reinicios contam uma vez).
- **2** (c): sinais de duas famílias diferentes.
- **3** (d): qualquer sinal de integridade ou qualidade do arquivo (assinatura, contagem_divergente, biometria_divergente, zeresima_ausente, identidade_nao_confirmada, relogio, texto_malformado) ou três ou mais famílias.

| nível | seções | % das seções |
|---|---|---|
| 0 | 442.504 | 88,65 |
| 1 | 48.344 | 9,68 |
| 2 | 7.476 | 1,50 |
| 3 | 852 | 0,17 |

Nível 0 = 329.030 sem sinal + 95.000 só bateria + 18.474 só inspeção breve (com ou sem bateria). Nível 1 por família (sem bateria): Energia e reinícios 13.437, Identificação do eleitor 10.952, Tempo de votação 6.484, Interrupções e inspeções 17.471, Conferência do arquivo 0; 5.060 seções do nível 1 têm como único sinal inspeção de 10 min ou mais, e 8.741 têm como único sinal intervalo_longo (4.190 delas com menos de 150 votantes). Nível 2, combinações mais comuns: Energia e reinícios + Interrupções e inspeções 2.988; Identificação do eleitor + Interrupções e inspeções 1.758; Interrupções e inspeções + Tempo de votação 1.705; Energia e reinícios + Identificação do eleitor 473; Identificação do eleitor + Tempo de votação 319; Energia e reinícios + Tempo de votação 233. Nível 3: 325 por integridade, 540 por três famílias ou mais, 13 pelos dois; por sinal: assinatura 18, contagem_divergente 10, biometria_divergente 10, zeresima_ausente 2, identidade_nao_confirmada 18, relogio 281, texto_malformado 2. 82 das seções de nível 3 são do exterior, 82 delas por relógio.

Sensibilidade da régua:

| nível | principal | bateria conta como Energia | inspeção única de 5 min ou mais vai a 1 (+18.474) |
|---|---|---|---|
| 0 | 442.504 | 438.103 | 424.030 |
| 1 | 48.344 | 39.718 | 66.818 |
| 2 | 7.476 | 19.437 | 7.476 |
| 3 | 852 | 1.918 | 852 |

Distribuição dos níveis por tamanho (% da linha). A régua aponta mais para seções pequenas, onde intervalos longos e inspeções longas são esperados; o mapa deve mostrar o tamanho ao lado do nível:

| comparecimento | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| <50 | 3,67 | 78,85 | 15,03 | 2,45 |
| 50-99 | 6,50 | 63,10 | 25,79 | 4,61 |
| 100-149 | 48,62 | 40,11 | 10,25 | 1,02 |
| 150-199 | 80,32 | 16,66 | 2,81 | 0,20 |
| 200-249 | 90,01 | 8,78 | 1,10 | 0,11 |
| 250-299 | 92,82 | 6,44 | 0,66 | 0,08 |
| 300-349 | 93,65 | 5,83 | 0,46 | 0,06 |
| 350+ | 93,62 | 5,55 | 0,42 | 0,40 |

Níveis por UF:

| uf | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| AC | 1.901 | 325 | 44 | 0 |
| AL | 6.238 | 746 | 109 | 8 |
| AM | 7.013 | 988 | 142 | 14 |
| AP | 1.660 | 223 | 31 | 0 |
| BA | 30.428 | 4.135 | 763 | 150 |
| CE | 20.793 | 2.529 | 415 | 28 |
| DF | 6.345 | 570 | 53 | 1 |
| ES | 8.735 | 967 | 130 | 12 |
| GO | 13.803 | 1.667 | 209 | 7 |
| MA | 15.059 | 2.501 | 481 | 52 |
| MG | 46.343 | 4.735 | 891 | 91 |
| MS | 6.206 | 756 | 128 | 16 |
| MT | 7.416 | 745 | 115 | 11 |
| PA | 17.237 | 3.007 | 520 | 63 |
| PB | 9.522 | 1.068 | 117 | 5 |
| PE | 18.880 | 2.240 | 282 | 16 |
| PI | 8.454 | 1.490 | 245 | 36 |
| PR | 24.420 | 2.280 | 397 | 45 |
| RJ | 33.881 | 3.296 | 440 | 58 |
| RN | 7.282 | 727 | 98 | 8 |
| RO | 4.136 | 512 | 49 | 1 |
| RR | 1.286 | 202 | 31 | 0 |
| RS | 24.133 | 2.936 | 443 | 35 |
| SC | 15.795 | 1.341 | 174 | 16 |
| SE | 5.159 | 673 | 86 | 5 |
| SP | 95.572 | 7.039 | 964 | 81 |
| TO | 3.847 | 450 | 76 | 11 |
| ZZ | 960 | 196 | 43 | 82 |

## Limites

- Tudo é triagem exploratória de registros operacionais; nenhum número aqui é teste de fraude ou de alteração de votos.
- A leitura dos ZIPs originais foi feita só para bateria (117.016 seções) e para contagens agregadas de mensagens de habilitação em 669 seções (69 com biográfica de 90% ou mais e 600 controles sorteados com semente fixa). Nenhum identificador de mesário, horário individual de eleitor ou opção de voto saiu do processo de leitura.
- O teto de 10 mensagens de bateria por sessão é inferido da distribuição, não de documentação. A simultaneidade usa o município porque o local de votação não foi usado nesta análise.
- Os dados do Politize foram usados só para o nome do município e para conferir o comparecimento (o tamanho usado nas tabelas é o comparecimento do próprio log). Das 499.176 seções do log, 499.156 casam com o Politize e 499.085 têm comparecimento lá, igual ao do log em todas.
