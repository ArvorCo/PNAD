# Atualização documental de 30/09/2026

A íntegra pública da Meio/Ideia, divulgada em 30/09, foi baixada do link da própria matéria. São 70 páginas, 2.000 entrevistas, campo de 25 a 28/09 e registro BR-08706/2026. PDF e texto nativo ficam em `data/originals/meio_ideia_092026_30/`. Os gráficos são imagens; as páginas 14, 31, 33 e 37 foram renderizadas e transcritas no script, com a metodologia da p. 69 arquivada para conferência.

- [PDF Meio/Ideia](https://www.canalmeio.com.br/wp-content/uploads/2026/09/Pesquisa-Meio_Ideia-Setembro2.pdf)
- [Matéria e data da divulgação](https://www.canalmeio.com.br/2026/09/30/meio-ideia-o-primeiro-turno-mais-dificil-da-historia/)
- [PDF Futura reconferido](https://static.poder360.com.br/uploads/2026/09/R_BR_Setembro_3.pdf)
- [Divulgação Futura de 24/09](https://exame.com/brasil/futura-flavio-bolsonaro-cresce-chega-a-404-e-ultrapassa-lula-no-1o-turno/)
- [Biblioteca da Futura](https://www.futurainteligencia.com.br/)

Meio/Ideia publica Lula 39,4 × Flávio 38,4 no primeiro turno e 48,5 × 48,0 no segundo. O primeiro turno soma 100,5% e o segundo, 100,1% por arredondamento; preservamos os originais. A p. 37 traz voto por quatro faixas de renda, mas não o peso das faixas na amostra. A p. 69 informa atividade econômica, não composição de renda. A p. 9 tem perfil somente dos indecisos da espontânea, não de todo o eleitorado. O controle por gênero usa proporções declaradas do desenho (47/53), não bases observadas; recompõe 48,443 e 47,95 e serve apenas de conferência auxiliar, sem habilitar ajuste por renda. Não inventamos bases nem aproveitamos as de outra onda.

Futura: o download do PDF de 24/09 inicialmente repetiu o arquivo antigo. Depois, a biblioteca oficial revelou a rodada BR-01122/2026, com campo anunciado de 25 a 29/09. O usuário forneceu oito prints: páginas 7, 20, 22, 23, 24, 25, 29 e 30. Os originais, hashes e transcrição completa ficam em `data/originals/futura_092026_30/`. A nova ficha é `futura_2026-09-29.json`. Ficha técnica não recebida; fontes preliminares mencionavam campo desde 24/09, divergência ainda pendente. A íntegra não foi baixada nem tratada como recebida.

Os prints registram Lula 39,4 × Flávio 42,2 na estimulada e 43,5 × 49,0 no segundo turno. A espontânea permanece separada. Renda conhecida soma 89,9%; 10% não declaram renda, total 99,9% por arredondamento. Os cruzamentos disponíveis são por gênero, região, idade e posição política. Não há voto por renda **nos prints recebidos**. Isso não permite concluir que esteja ausente das páginas não recebidas.

A recomposição pelo perfil da p. 7 é auxiliar: o maior resíduo por gênero é 0,165 pp, por região 0,439061 pp e por idade 0,910379 pp. Falta esclarecer se o perfil mostrado é bruto ou ponderado; as diferenças maiores não são atribuídas a mero arredondamento. Posição política não tem bases nos prints e não é agregada ao nacional. Os 306 percentuais dos cruzamentos ficam preservados com rótulos e página de origem.

Ambas ficam na cobertura documental, fora das médias comparáveis e do modelo por renda. A falta de informação pública não demonstra ponderação errada. Não foram acessados os cruzamentos exclusivos de assinantes anunciados na p. 3 da Meio/Ideia.

Reprodução offline:

```sh
python3 scripts/pesquisas-300926-renda.py
python3 scripts/reponderacao-pnad.py calcular --hoje 2026-09-30
python3 scripts/reponderacao-build.py
python3 scripts/social-cards.py --only reponderacao_pnad
python3 -m pytest -q
```

`auditoria.json` e sua cópia pública `docs/assets/reponderacao_20260930.json` registram hashes, páginas, placares e limites. Os resultados centrais do modelo não mudam com esta atualização: seis casas no primeiro turno e cinco no segundo. A janela passa a 24–30/09.
