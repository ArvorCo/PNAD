# Projeção condicional de votos válidos

Referência inicial: 28/09/2026. Dois gráficos na abertura de
`docs/reponderacao_pnad.html#projecao-validos`, gerados por
`scripts/reponderacao-validos.py` e `scripts/reponderacao-validos-view.py`.
CSS/JS próprios em `docs/assets/reponderacao_validos.*`.

Reproduzir com `python3 scripts/reponderacao-build.py --skip-home`.
O build calcula JSON e CSV e embute os dados no HTML para funcionar em
`file://`, sem fetch. Para atualizar a fonte de comparecimento, rodar antes
`python3 scripts/nexus-btg-28092026-audit.py`.

## Contrato matemático

- Uma onda por instituto e turno na janela de divulgação D−6 a D.
  Rejeitar a última onda incompatível sem substituí-la silenciosamente.
- Somente vetores completos de candidaturas; não escolha nunca é candidato.
  Valores negativos do delta de renda são zerados com registro explícito.
- Multiplicar cada candidato pelo comparecimento condicional inferido na
  tabela conjunta sintética Nexus de renda, idade e região. Transportar
  essa propensão para outras casas é hipótese, não evidência independente.
- Alocar indecisos presentes proporcionalmente **depois** de aplicar
  comparecimento. A identidade A/C = (A + U·A/C)/(C + U) prova que seu
  tamanho não altera a proporção válida. Não imputar U ausente.
- Normalizar cada pesquisa e só então tirar a média de peso igual por casa.
  Usar as mesmas casas nos modos publicado, PNAD e PNAD+comparecimento.
- Manter todos os candidatos no denominador do primeiro turno.
- Não reponderar renda novamente nem preencher o histórico com a fonte
  Nexus posterior à data. Projeção atual mantém preferências declaradas
  até a eleição, sem modelo de mudança tardia ou voto útil.

Testes de 60+ e multiplicadores 0,95/1,05 na presença de Flávio são
sensibilidades declaradas, não intervalos preditivos ou probabilidades de
vitória. O teste relativo permite contrariar a associação ecológica
central. A tabela sem uma casa por vez testa dependência de composição,
sem representar erro comum entre institutos.

`reponderacao_validos.json` registra fontes e hashes, pesos por candidato,
indecisos alocados, resíduos negativos, exclusões e todos os cenários.
Na edição inicial, Real Time não entra no primeiro turno porque publica
Outros=1% sem o respectivo cruzamento por renda. PoderData entra no
segundo turno apesar de não cruzar indecisos: ambos os candidatos têm
cruzamento e a alocação proporcional cancela no denominador.

## Validação

```sh
python3 -m pytest -q tests/test_reponderacao_validos.py
python3 analysis/reponderacao/validos/visual-qa.py
```

O segundo comando testa as três vistas, os cinco cenários, rótulos e
barras, duas larguras, detalhes abertos e fallback sem JavaScript.
As imagens e o JSON de QA permanecem neste diretório.

## Atualização de 29/09

Quaest, Gerp e Palver novas entram nos dois turnos; Atlas, no primeiro.
A Quaest agrega todos os candidatos menores por renda nesta onda. A projeção
exibe a partição comum entre casas (Lula, Flávio e demais), preservando a
massa dos demais e a mesma partição ao retirar uma casa. O q de Outros
agrupa os candidatos correspondentes da Nexus usando sua massa de voto
populacional após PNAD. Não se aplica a taxa residual de Samara ao bloco
inteiro da Quaest. A fonte de comparecimento continua sendo Nexus 28/09.
