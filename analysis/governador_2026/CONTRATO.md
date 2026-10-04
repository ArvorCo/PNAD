# Predição de governador 2026: contrato entre as partes

Página final: `docs/predicao_governador.html`, gerada por `python3 scripts/governador-2026-build.py`
a partir de `docs/predicao_governador.template.html` e de `docs/assets/predicao_governador.json`.
Nunca editar o HTML gerado. Data de referência: 03/10/2026, véspera do 1º turno de 04/10/2026.

Regras da casa que valem para todo arquivo deste projeto: travessão (`—`) proibido em qualquer
texto; lint zero (`ruff check scripts tests`, `black --check scripts tests`); testes em `tests/`
importam módulos de `scripts/` no topo; scripts novos em `kebab-case`, módulos importáveis em
`scripts/governador_2026/`; texto gerado nunca presume gênero ("candidatura de X"); números com
página ou URL de origem ao lado; nenhum número digitado à mão fora dos JSON de transcrição.

## 1. Pesquisas: um JSON por onda, com 1º e 2º turno

Pasta: `analysis/governador_2026/pesquisas/<instituto_slug>_<UF>_<AAAA-MM-DD do fim do campo>.json`.
Slugs: `datafolha`, `quaest`, `atlas`, `realtime`, `parana`, `futura`, `franca`, `poderdata`,
`gerp`, `verita`, `ipespe`, `meio`. Uma onda por arquivo.

```json
{
  "instituto": "Real Time Big Data",
  "instituto_slug": "realtime",
  "uf": "SP",
  "cargo": "governador",
  "registro_tse": "SP-06293/2026",
  "campo": {"inicio": "2026-09-24", "fim": "2026-09-28"},
  "divulgacao": "2026-09-29",
  "n": 2000,
  "margem_pp": 2.0,
  "metodo": "presencial | telefonico | online | misto | nao informado",
  "contratante": "nao informado",
  "fonte": {
    "tipo": "painel_g1 | pdf | materia",
    "url": "https://static.poder360.com.br/uploads/2026/09/....pdf",
    "arquivo": "data/originals/senado_102026/realtime_SP/relatorio.pdf",
    "sha256": "4e5f...",
    "pagina": 12,
    "imagem": "data/originals/senado_102026/realtime_SP/governador_p12.png",
    "capturado_em": "2026-10-03T23:01:25Z",
    "materia": ["https://www.poder360.com.br/..."]
  },
  "pergunta": {
    "codigo": "ESTIMULADA-GOV-001",
    "tipo": "estimulada",
    "cenario": "Cenário 1",
    "votos_por_eleitor": 1,
    "soma_total": 100.0,
    "nota": null
  },
  "candidatos": [
    {"nome": "Tarcísio de Freitas", "partido": "REPUBLICANOS", "valor": 55.0, "foto_url": null},
    {"nome": "Fernando Haddad", "partido": "PT", "valor": 33.0, "foto_url": null}
  ],
  "indecisos": 5.0,
  "branco_nulo": 7.0,
  "outros": null,
  "segundo_turno": [
    {
      "codigo": "SEGTURNO-GOV-001",
      "pagina": 18,
      "candidatos": [
        {"nome": "Tarcísio de Freitas", "partido": "REPUBLICANOS", "valor": 57.0},
        {"nome": "Fernando Haddad", "partido": "PT", "valor": 35.0}
      ],
      "indecisos": 3.0,
      "branco_nulo": 5.0,
      "soma_total": 100.0
    }
  ],
  "observacoes": ["..."]
}
```

- `valor` em pontos percentuais do total de entrevistados. Se a fonte só traz válidos, gravar
  `"base": "validos"` no bloco `pergunta` e deixar `indecisos`/`branco_nulo` nulos.
- Governador é voto único: `votos_por_eleitor` é sempre 1.
- Quando o relatório traz mais de um cenário de 1º turno, o principal (o que inclui todos os
  nomes registrados no TSE, ou o que o próprio instituto chama de principal) vai em `candidatos`;
  os demais vão em `cenarios_alternativos` com o mesmo formato (`cenario`, `pagina`, `candidatos`,
  `indecisos`, `branco_nulo`) e ficam fora da média.
- `segundo_turno` é lista: um item por par medido, cada um com dois nomes e a página. Sem 2º turno
  no relatório, lista vazia.
- Nomes exatamente como o relatório imprime (acentos inclusive). `partido` em maiúsculas,
  siglas do TSE (`UNIÃO`, `PCDOB`, `REPUBLICANOS`, `PODEMOS`); sem partido no relatório, `null`.
- Candidatos com valor 0 entram mesmo assim.
- `fonte.pagina` é a página do 1º turno transcrito; `fonte.imagem` é a renderização dessa
  página (`pdftoppm -r 110 -f N -l N -png`), guardada ao lado do PDF, para conferência.
- Nunca inventar `campo`, `n` nem `registro_tse`: o que não está no relatório fica `null`, com a
  ausência registrada em `observacoes`.
- Soma de candidatos + indecisos + branco/nulo (+ outros) precisa fechar em 100 ± 1,5 pp; se o
  relatório fechar diferente (arredondamento), gravar o que está impresso e anotar.

## 2. TSE: candidaturas e fotos

`python3 scripts/governador-2026-tse.py` grava `analysis/governador_2026/tse_candidatos.json`
(cargo 3, governador), `casamento_nomes.json` e as fotos em `docs/img/governador/<UF>_<SQ>.jpg`
(240×240). Casamento por nome de urna normalizado e tabela `APELIDOS` declarada em
`scripts/governador_2026/tse.py`; nada por adivinhação.

## 3. Motor: `scripts/governador_2026/motor.py`

Entrada: pesquisas, TSE, `PARTIDO_CAMPO` (tucano é centro-esquerda; PSD é centro; União, PP e
Podemos centro-direita; PL, Novo e Republicanos direita) e a calibração de 2022 do Senado como
escala do erro (hipótese declarada: não há calibração própria de governador).

Por estado e por sorteio:

1. 1º turno: Dirichlet por casa (n / deff), combinação por recência, indecisos proporcionais
   (com sensibilidade uniforme), choque logístico-normal comum ao estado e por candidatura.
2. Se a candidatura mais votada passa de 50% dos válidos, eleita no 1º turno.
3. Senão, as duas mais votadas vão ao 2º turno. Se há par medido (média por recência das ondas
   com esse par), o 2º turno sai do par medido com erro próprio. Se não há, sai de transferência
   declarada por campo (prior ideológica) sobre os válidos sorteados do 1º turno, com erro maior.
4. Saída: `p_1t` (decidido no 1º turno), `p_2t`, `p_eleito` por candidatura (soma 1,0 por estado),
   `p_vai_2t` por candidatura, pares de 2º turno mais prováveis com a projeção de cada um, IC90.

Saída: `docs/assets/predicao_governador.json`, com `estados`, `nacional` (estados decididos no 1º
turno esperados, governadores por campo), `parametros`, `validacao` e `fontes`.

## 4. Página

Mapa do Brasil (malha do IBGE já usada no Senado), pintado pelo campo da candidatura favorita, com
hachura onde o 2º turno é mais provável que a decisão no 1º; ranking das corridas mais apertadas;
fichas por estado com 1º turno, probabilidade de 2º turno e projeção dos pares; tabela das 27 UFs;
como lemos; limites; fontes com URL, hash e página. CSS da casa (`predicao_2026*.css`,
`predicao_senado.css`) mais `predicao_governador.css`. Card social em `scripts/social-cards.py`.
