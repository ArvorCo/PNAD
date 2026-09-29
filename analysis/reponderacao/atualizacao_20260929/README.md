# Atualização nacional de 29/09/2026

Escopo: agregador `docs/reponderacao_pnad.html`, seus dados e a capa
`docs/index.html`. Nenhum novo dossiê Quaest ou Atlas nesta etapa.

## Fontes arquivadas

- Quaest: PDF recebido em Downloads, divulgação em **28/09**, campo 24–27/09,
  BR-06520/2026, 2.004 entrevistas, 210 páginas. Cópia canônica em
  `data/originals/quaest_092026_29/relatorio.pdf`.
- Atlas: íntegra oficial, divulgação **29/09**, campo 23–28/09,
  BR-04391/2026, 5.005 entrevistas, 23 páginas.
- Palver: íntegra e seis tabelas exatas do Explorer (onda 5), divulgação
  **29/09**, campo 24–27/09 conforme p. 21, BR-02990/2026,
  5.000 entrevistas, 154 páginas. Snapshot do Explorer em
  `analysis/reponderacao/palver_explorer_20260929/` e HTML comprimido em
  `data/originals/palver_explorer_20260929/`.
- Gerp: catálogo e PDF oficiais, divulgação **29/09**, campo 24–28/09,
  BR-03929/2026, 2.400 entrevistas, 46 páginas.
- Vox Brasil: íntegra hospedada pelo Poder360, divulgação **29/09**,
  campo 26–28/09, BR-00895/2026, 2.100 entrevistas, 28 páginas.

Atlas, Palver, Gerp e Vox são as quatro divulgações nacionais de hoje
localizadas na busca. Registros com divulgação prevista, pesquisas de
estados e resultados de ondas antigas não contam como novas nacionais.
URLs, SHA-256 e páginas usadas estão em `auditoria.json`, também publicado
como `docs/assets/reponderacao_20260929.json`.

## Critérios e verificações

As sete tabelas elegíveis recompõem o publicado por renda com resíduos
abaixo de 0,7 pp e por sexo abaixo de 0,5 pp. Palver usa percentuais exatos:
as margens ponderadas têm posto completo, resíduo inferior a 1e-10 e
reproduzem o n efetivo. Bases brutas não viram pesos.

Quaest, Palver e Gerp entram nos dois turnos; Atlas apenas no primeiro.
Vox é cobertura documental: tem perfil de renda e pergunta de presença,
mas não voto por renda nem presença por candidato. Atlas não publica
renda no segundo turno. Não se transportam cruzamentos entre turnos.

Quaest agrupa todas as candidaturas menores no cruzamento desta onda.
O vetor usado no ajuste repete essa partição; o topline individual fica
preservado no manifesto. A projeção de válidos apresenta a partição comum
às casas, agrupando os demais, sem atribuir zero a candidatos não separados.
A taxa de presença desse agregado usa o grupo correspondente da Nexus,
ponderado pela massa de voto após PNAD, não a taxa residual de Samara.
A fonte de presença permanece Nexus 28/09 e seu transporte é hipótese.

Gerp informa 1% de indecisos na p. 22 e 2% na coluna total da p. 24.
O cálculo ancora na p. 22 e conserva o cruzamento da p. 24, com aviso.
Atlas informa 4,8% de branco/nulo/não sei no segundo turno; o total soma
100,1%. Ambos os arredondamentos são preservados.

## Reprodução

```sh
python3 scripts/pesquisas-290926-renda.py
python3 scripts/reponderacao-pnad.py calcular --hoje 2026-09-29
python3 scripts/reponderacao-build.py
python3 -m pytest -q
python3 analysis/reponderacao/validos/visual-qa.py
```

`quaest/`, `atlas/`, `palver/` e `gerp/` contêm renderizações usadas na
conferência visual. O script de integração funciona offline após arquivar
os documentos e o Explorer. Não modifica o material em Downloads.
