# Atualização documental de 30/09/2026

A íntegra pública da Meio/Ideia, divulgada em 30/09, foi baixada do link da própria matéria. São 70 páginas, 2.000 entrevistas, campo de 25 a 28/09 e registro BR-08706/2026. PDF e texto nativo ficam em `data/originals/meio_ideia_092026_30/`. Os gráficos são imagens; as páginas 14, 31, 33 e 37 foram renderizadas e transcritas no script, com a metodologia da p. 69 arquivada para conferência.

- [PDF Meio/Ideia](https://www.canalmeio.com.br/wp-content/uploads/2026/09/Pesquisa-Meio_Ideia-Setembro2.pdf)
- [Matéria e data da divulgação](https://www.canalmeio.com.br/2026/09/30/meio-ideia-o-primeiro-turno-mais-dificil-da-historia/)
- [PDF Futura reconferido](https://static.poder360.com.br/uploads/2026/09/R_BR_Setembro_3.pdf)
- [Divulgação Futura de 24/09](https://exame.com/brasil/futura-flavio-bolsonaro-cresce-chega-a-404-e-ultrapassa-lula-no-1o-turno/)
- [Biblioteca da Futura](https://www.futurainteligencia.com.br/)

Meio/Ideia publica Lula 39,4 × Flávio 38,4 no primeiro turno e 48,5 × 48,0 no segundo. O primeiro turno soma 100,5% e o segundo, 100,1% por arredondamento; preservamos os originais. A p. 37 traz voto por quatro faixas de renda, mas não o peso das faixas na amostra. A p. 69 informa atividade econômica, não composição de renda. A p. 9 tem perfil somente dos indecisos da espontânea, não de todo o eleitorado. O controle por gênero usa proporções declaradas do desenho (47/53), não bases observadas; recompõe 48,443 e 47,95 e serve apenas de conferência auxiliar, sem habilitar ajuste por renda. Não inventamos bases nem aproveitamos as de outra onda.

Futura: download repetido em 30/09 produziu o mesmo SHA-256 do PDF já arquivado, campo 19–23/09, divulgação 24/09, 42 páginas. Nenhuma nova íntegra nacional foi localizada nas buscas ao Poder360, Exame, CNN e ao site do instituto. O site do instituto anuncia biblioteca mediante cadastro; não foi feito cadastro. Pesquisa presidencial estadual não foi tratada como nacional. O PDF atual contém perfil de renda na p. 6, mas não voto por renda. A parcela sem renda declarada de 9,2% não é tratada como faixa de renda.

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
