# Palver Explorer: extração e auditoria de 21/09/2026

Fonte: https://www.palver.com.br/survey/explore

Extraídos **186 quadros públicos de 196 consultas**, sem login. As consultas cobrem os dois turnos principais nas quatro versões publicadas e todos os 44 quesitos da onda 3 por renda e total. Dez combinações não estão disponíveis nas ondas antigas; o retorno padrão não foi contado como cruzamento.

Cada JSON preserva percentuais sem arredondamento (`share`), limites publicados (`low`, `high`), contagens por célula (`n`), bases e tamanho efetivo (`n_eff`). O manifesto registra URL, horário e SHA-256 do HTML público. Snapshots HTML compactados estão em `data/originals/palver_explorer_20260921/`.

## Renda: composição bruta e ponderada da onda 3

| Faixa | Entrevistas | Bruta % | Ponderada recuperada % | Peso médio normalizado | n efetivo |
|---|---:|---:|---:|---:|---:|
| Até 2 salários mínimos | 1321 | 26,42 | 42.122941 | 1,59 | 401,17 |
| 2 a 5 salários mínimos | 2203 | 44,06 | 39.563096 | 0,90 | 587,95 |
| Mais de 5 salários mínimos | 1476 | 29,52 | 18.313962 | 0,62 | 324,47 |

As margens ponderadas foram **recuperadas por sistema linear**, não copiadas de um campo de pesos: para cada resposta, total = soma das parcelas por faixa. O sistema tem posto completo, solução não negativa e resíduos inferiores a 10⁻¹⁰. A recomposição independente do n efetivo usa `1 / Σ(p_g² / n_eff_g)` e devolve 1231,71, igual ao nacional. As margens reproduzem os alvos 42,12 / 39,56 / 18,31 declarados no PDF.

A mesma margem recompõe **43 perguntas** de base 5.000 na onda 3. Questões condicionais foram separadas; não se aplicou a elas a distribuição de todos os entrevistados.

## Sensibilidade de renda PNAD 2025

Ordem Lula × Flávio, percentuais totais. Referência: o mesmo histograma, universo e ajuste de preços já utilizados pelo agregador na onda de setembro. A tabela aplica essa régua comum às quatro versões; não reproduz a régua histórica de preços de cada data. Cada cenário troca só a distribuição de renda. Os resultados não são raking conjunto nem previsão.

| Versão | Turno | Explorer exato | PNAD efetiva 16+ | PNAD habitual 16+ |
|---|---|---:|---:|---:|
| 01_pesquisa_2026_08_10 | 1t | 44,25 × 39,90 | 44,43 × 38,80 | 44,35 × 38,93 |
| 01_pesquisa_2026_08_10 | 2t | 46,21 × 45,51 | 46,52 × 44,81 | 46,45 × 44,90 |
| 02_pesquisa_2026_09_09 | 1t | 40,16 × 39,70 | 39,67 × 39,19 | 39,60 × 39,30 |
| 02_pesquisa_2026_09_09 | 2t | 43,74 × 46,41 | 43,53 × 46,04 | 43,42 × 46,15 |
| 02_pesquisa_2026_09_21 | 1t | 40,44 × 40,50 | 39,98 × 40,06 | 39,90 × 40,19 |
| 02_pesquisa_2026_09_21 | 2t | 43,85 × 47,41 | 43,59 × 47,14 | 43,48 × 47,26 |
| 03_pesquisa_2026_09_21 | 1t | 41,32 × 42,33 | 41,47 × 41,52 | 41,40 × 41,56 |
| 03_pesquisa_2026_09_21 | 2t | 42,93 × 47,39 | 43,10 × 46,89 | 43,06 × 46,92 |

**Distinção de ancoragem.** Os valores acima partem do total exato do Explorer. Se mantivermos a convenção anterior de ancorar o delta no total inteiro do PDF, a onda 3 resulta em 1t: 41,14 × 41,19; 2t: 43,18 × 46,50. Não misturar as duas convenções.

**Onda 2 revisada:** o voto por renda agora está disponível. Os dois cenários de 1º turno antigos incluem Marçal, portanto permanecem fora da série sem Marçal. O 2º turno pode ser recalculado com a versão revisada, substituindo a original, sem contar a amostra duas vezes. As contagens voto × renda são idênticas nas versões antiga e revisada: sim.

## Matriz medida de transferência e voto passado

O cruzamento de 2º por 1º turno permite observar a fidelidade das duas bases e os destinos de Renan, Cury, outros candidatos e não escolha. São grupos medidos na mesma entrevista; não são trajetórias reais entre eleições. Outros candidatos e não escolha do 1º turno permanecem agrupados.

| Origem no 1º turno | n bruto | Lula no 2º % | Flávio no 2º % | Não escolha no 2º % |
|---|---:|---:|---:|---:|
| Lula (PT) | 1503 | 98,92 | 0,03 | 1,06 |
| Flávio Bolsonaro (PL) | 2395 | 0,00 | 99,94 | 0,06 |
| Renan Santos (Missão) | 857 | 5,77 | 25,29 | 68,94 |
| Escritor Augusto Cury (Avante) | 105 | 22,11 | 41,97 | 35,92 |
| Outros candidatos | 95 | 36,70 | 50,84 | 12,46 |
| Indecisos, brancos e nulos | 45 | 20,44 | 33,94 | 45,61 |

## Composição por voto declarado em 2022

| Voto declarado | n bruto | Bruta % | Ponderada recuperada % |
|---|---:|---:|---:|
| Lula | 1559 | 31,18 | 48,27 |
| Jair Bolsonaro | 2642 | 52,84 | 47,16 |
| Branco/Nulo ou Não votei | 799 | 15,98 | 4,58 |

A diferença bruta/ponderada resulta do conjunto de pesos finais. Não isola o efeito causal da calibração por voto passado. A memória de voto é autodeclarada; não comprova o voto individual depositado em 2022.

Também há voto atual por voto declarado em 2022, sexo, idade, raça, escolaridade, região, religião, vertente religiosa, ideologia e identificação política. As margens inferidas de todas as partições identificáveis estão em `audit.json`.

## Limites e pontos a esclarecer com a Palver

- **Pesos individuais:** não foram disponibilizados nessas tabelas. É possível calcular médias de pesos por célula e verificar segundos momentos, mas não recuperar de forma única o peso de cada pessoa.
- **TSE + PNAD simultâneos:** falta a tabela conjunta voto × renda × idade × sexo × região × escolaridade × voto 2022 × filiação, ou microdados anônimos com pesos. Somar sensibilidades marginais ou fabricar a tabela por independência não reproduz o raking do instituto.
- **Datas:** o catálogo do Explorer encerra a onda 3 em 20/09; o PDF nas pp. 16, 22 e 30 indica 18/09. O n efetivo do Explorer coincide com o PDF, mas isso não resolve a data de campo.
- **Onda 2 revisada:** Lula tem 40,440% no 1º turno do Explorer e 41% no gráfico do PDF p. 30. O arredondamento convencional isolado não explica a diferença. Solicitar identificação da versão, regra de agregação e arquivo usado no PDF.
- **Voto 2022:** o recorte reúne branco/nulo e quem não votou; pedir o tratamento separado de inelegíveis, abstenção e não resposta na calibração.
- **Cobertura:** identificação política da onda 3 cobre 4.924 pessoas. Não recompor o nacional com esses grupos sem tratar os 76 casos ausentes.
- **Respostas múltiplas:** desgaste Master e STF podem somar mais de 100%. Não normalizar essas tabelas como se fossem uma escolha exclusiva.

A integração no agregador é feita por `palver-explorer-integrate.py`: usa os percentuais exatos do Explorer, mantém a onda 2 original fora das médias e publica as quatro versões no histórico, inclusive os cenários com Marçal excluídos da média do primeiro turno.

## Reprodução

```sh
python3 scripts/palver-explorer-extract.py
python3 scripts/palver-explorer-audit.py
```

A extração reutiliza snapshots; `--refresh` consulta novamente a fonte. A auditoria usa apenas os JSON arquivados e o benchmark do projeto.
