# Isolamento de combinações eleitorais agregadas

O Isolation Forest organiza combinações incomuns de resultados públicos. Não estima
voto individual, fraude ou regularidade eleitoral. Seu percentil não é p-value,
probabilidade, acurácia ou AUC. Sem rótulos independentes de irregularidades, não há
validação que autorize essas interpretações ou alegar superioridade sobre outro
algoritmo. Uma distribuição política regional legítima também pode ser rara no país.

## Reprodução e universo

Executar `python3 scripts/politize-se-isolamento-build.py`. Motor:
`scripts/politize_se/isolamento.py`. Entradas: fragmentos públicos por zona em
`docs/assets/politize_se/dados/zona/`. Saídas em
`docs/assets/politize_se/isolamento/`. Todas as fontes são locais; hashes dos
fragmentos, do motor e da publicação e versões de numpy/scikit-learn ficam no índice.
Arquivos ordenados, seeds fixas e gzip com mtime zero permitem repetir os bytes com
as mesmas fontes, versões e plataforma. Alterações de fontes exigem rebuild explícito.

Brasil sem exterior. Uma observação de seção é um BU principal e seu conjunto de
seções agregadas. Exige ao menos 30 aptos em ambos os turnos, as mesmas agregadas,
contagens inteiras não negativas e completas, ambos os turnos com votos em F+L,
soma dos votos igual ao comparecimento e comparecimento não superior aos aptos.
Ausências ou alteração de agregação excluem o par de todos os níveis. Ausência não
é zero. Locais seguem as chaves cadastrais usadas no mapa: uma mudança de prédio
não muda a identidade do conjunto de eleitores. São agregados cadastrais, não
observações independentes de um endereço físico em cada turno.

Os quatro níveis (seção, local, zona, município) têm ajustes próprios, nacionais,
com peso igual por unidade. Os níveis superiores somam contagens dos pares
admitidos e só então calculam taxas. Nenhum score é máximo ou média dos filhos.
O denominador da cobertura é o número de linhas de seções principais presentes
nos fragmentos. O campo `aptos2` soma somente as seções elegíveis. As contagens
nacionais conservam os mesmos totais nos quatro níveis. Recortes arbitrários ou
horários não herdam score de uma unidade maior como se fossem a própria unidade.

## Variáveis e modelo

Sete dimensões, em proporções (0 a 1; diferenças podem ser negativas):

1. Flávio / (Flávio + Lula), segundo turno.
2. Brancos e nulos / comparecimento, segundo turno.
3. Abstenção / aptos, segundo turno.
4. Mudança da proporção 1 entre os turnos, nos mesmos pares.
5. Mudança da proporção 2 entre os turnos.
6. Mudança da proporção 3 entre os turnos.
7. Terceira via / válidos, primeiro turno.

Não entram os complementos de Lula, os votos absolutos, tamanho (nem log de aptos),
localização, perfis de renda/sexo/idade/escolaridade, crimes, scores anteriores ou
valores esperados de outros modelos. As três mudanças adicionam informação temporal;
não são uma duplicação linear de variáveis de primeiro e segundo turnos já incluídas.
Não se padronizam dimensões: a divisão aleatória de cada eixo do Isolation Forest
já é invariante à transformação afim positiva de sua escala.

São três florestas de 256 árvores, seeds 20261029, 731 e 991, `max_samples=1024`
(limitado ao número disponível), todas as dimensões, sem pesos amostrais. Usa-se a
média de `-score_samples`; nenhum limiar de `predict` é usado. O percentil nacional
é `100 * (rank_médio - 0,5) / n`; empates têm rank médio. O topo de aproximadamente
1% é convenção, não teste. Não é possível interpretar esse corte como prevalência
de irregularidade. Árvores ajustadas e avaliadas sobre esse universo fazem uma
descrição do universo corrente, não uma avaliação preditiva fora da amostra.

`percentil_min/max` cobre os ranks das três seeds e da média. Essa faixa mede
sensibilidade computacional, não incerteza eleitoral ou intervalo de confiança.
O índice publica Spearman, Jaccard dos conjuntos no topo 1%, amplitude mediana e
percentil 95 da amplitude. As seeds não constituem três eleições independentes.

Referência da implementação: [scikit-learn, IsolationForest](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html).

## Porte: diagnóstico obrigatório

A publicação nacional inicial mostrou concentração grande no topo entre seções
menores, apesar de tamanho não ser uma feature: proporções em denominadores
pequenos variam mais; grupos pequenos também têm composições diferentes.
Não é possível separar esses dois mecanismos apenas com esse diagnóstico.

- 30 a 99 aptos no segundo turno: 2.692 seções, 689 no topo 1% (25,59%).
- 100 a 199: 18.993 seções, 1.051 no topo (5,53%).
- 200 a 399: 456.278 seções, 3.212 no topo (0,704%).
- 400 ou mais: 19.833 seções, 26 no topo (0,131%).

O score nacional original fica preservado. `percentil_porte` é uma sensibilidade:
rank do mesmo score dentro das quatro faixas de aptos2, sem novo ajuste. Isso
muda a comparação, não elimina estrutura regional nem transforma uma combinação
rara em resíduo inexplicado. O topo dentro de cada faixa também existe por
construção. Nas demais unidades, `percentil_porte` e `faixa_porte` são null.

Outra sensibilidade refaz as três florestas usando somente seções com ao menos
200 aptos em ambos os turnos. Compara o rank dessa reestimação com o rank dos
scores originais restrito ao mesmo subconjunto. Publica Spearman e Jaccard do
topo 1%, sem substituir qualquer score. Esta comparação explora a influência
das seções menores na referência; não prova que o segundo ajuste seja melhor.

## Contrato da publicação

`indice.json`: `formato`, `modelo`, `features`, `regras`, `nota`, `niveis`, `ufs`,
`secoes_total`, `secoes_usadas`, `sha256_codigo`. Cada UF tem arquivo, tamanho,
SHA-256, hash agregado de fontes, cobertura e exclusões por motivo.

`UF.json.gz`: `formato=1`, `uf`, `colunas` e dicionários `secoes`, `locais`,
`zonas`, `municipios`. Colunas posicionais:

`percentil, percentil_min, percentil_max, score, secoes_usadas, secoes_total, aptos2, percentil_porte, faixa_porte`.

Chaves de seção `mun_tse-zona-secao`, com município de cinco dígitos; local usa
`local_id` do mapa; zona é seu número como string; município tem cinco dígitos.
UF já é definida pelo arquivo. Unidades sem pares elegíveis não têm entrada,
nunca score zero. Nível com menos de duas unidades elegíveis não recebe ajuste.
Todos os scores dependem da versão nacional corrente, não de filtros visuais.

## Verificação

`pytest -q tests/test_politize_se_isolamento.py` cobre faltantes, contagens,
conservação, pares alterados, duplicatas, somas antes de taxas, ausência de efeito
puramente escalar no vetor, ranks com empates, repetibilidade das seeds/bytes,
ranks por porte e os quatro universos publicados. Testes verificam hashes,
cobertura e intervalo de ranks em todos os registros públicos. O diagnóstico de
porte é uma limitação do método, não uma falha a esconder mudando a especificação.

## Interface

`docs/assets/politize_se_mapa/isolamento.js` e `.css` integram as três camadas do
mapa (locais, zonas e municípios) e a ficha da seção. Um agrupamento visual de
vários prédios não recebe score de local. Para zonas e municípios, o score da
unidade inteira só aparece quando todos os filhos do agrupamento pertencem à
mesma unidade e é rotulado como contexto dessa unidade. Filtro de horário torna
os scores indisponíveis, pois não existe modelo estimado sobre esses recortes.
A ficha mostra o percentil por porte ao lado do nacional; legenda e diagnóstico
explicitam a concentração de seções pequenas. Testes de integração:
`tests/test_politize_se_mapa_isolamento.py`.

## Conferência da publicação de 09/11/2026

O build usa fragmentos de 28/10; o site conservava uma serialização de 27/10.
Foram comparados integralmente os 2.640 fragmentos das 27 UFs: conteúdo, ordem e
colunas de seções, UF, zona e sequência de `local_id` são idênticos. Essas são
todas as entradas lidas pelo motor. Datas de geração e outros atributos dos
locais podem diferir. Os hashes das duas versões ficam em
`analysis/politize_se/isolamento_fontes_publicadas.json`; os hashes originais do
build permanecem intactos. Nenhum score foi recalculado ou alterado.
