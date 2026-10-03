# Predição do Senado 2027: contrato entre as partes

Página final: `docs/predicao_senado.html`, gerada por `python3 scripts/senado-2026-build.py`
a partir de `docs/predicao_senado.template.html` e de `docs/assets/predicao_senado.json`.
Nunca editar o HTML gerado. Data de referência: 03/10/2026, véspera do 1º turno de 04/10/2026.

Regras da casa que valem para todo arquivo deste projeto: travessão (`—`) proibido em qualquer
texto; lint zero (`ruff check scripts tests`, `black --check scripts tests`); testes em `tests/`
importam módulos de `scripts/` no topo (o `conftest.py` já cuida do caminho); scripts novos em
`kebab-case`, módulos importáveis em `scripts/senado_2026/` (pacote com `__init__.py`);
texto gerado nunca presume gênero ("candidatura de X", "eleitorado de X"); números com
página ou URL de origem ao lado; nenhum número digitado à mão fora dos JSON de transcrição.

## 1. Pesquisas: um JSON por onda

Pasta: `analysis/senado_2026/pesquisas/<instituto>_<UF>_<AAAA-MM-DD do fim do campo>.json`.
`instituto` em minúsculas sem acento (`datafolha`, `quaest`, `atlas`, `realtime`, `parana`,
`futura`, `gerp`, `verita`, `ipespe`, `meio`, ...). Uma onda por arquivo; onda antiga do mesmo
instituto no mesmo estado fica em arquivo próprio (o motor escolhe pela data).

```json
{
  "instituto": "Datafolha",
  "instituto_slug": "datafolha",
  "uf": "SP",
  "cargo": "senador",
  "registro_tse": "SP-09337/2026",
  "campo": {"inicio": "2026-10-02", "fim": "2026-10-03"},
  "divulgacao": "2026-10-03",
  "n": 2520,
  "margem_pp": 2,
  "metodo": "presencial | telefonico | online | misto | nao informado",
  "contratante": "Globo e Folha de S.Paulo",
  "fonte": {
    "tipo": "painel_g1 | pdf | materia",
    "url": "https://...",
    "arquivo": "data/originals/senado_102026/g1/SP_datafolha.json",
    "sha256": "...",
    "pagina": null,
    "capturado_em": "2026-10-03T23:10:00Z"
  },
  "pergunta": {
    "codigo": "ESTIMULADA-SEN-005",
    "tipo": "estimulada",
    "votos_por_eleitor": 1,
    "soma_total": 98.0,
    "nota": "Como a soma fica em 100, o painel reporta a fração de menções, não duas escolhas por eleitor."
  },
  "candidatos": [
    {"nome": "Guilherme Derrite", "partido": "PP", "valor": 16.0, "foto_url": "https://..."},
    {"nome": "André do Prado", "partido": "PL", "valor": 16.0, "foto_url": null}
  ],
  "indecisos": 13.0,
  "branco_nulo": 14.0,
  "observacoes": ["Guto Schiavetto (Missão) não constava no TSE no registro de 21/08 (disclaimer do painel)."]
}
```

- `valor` em pontos percentuais do total de entrevistados (não de válidos). Se a fonte só traz
  válidos, gravar `"base": "validos"` no bloco `pergunta` e deixar `indecisos`/`branco_nulo` nulos.
- `votos_por_eleitor`: 1 quando a soma dos candidatos + indecisos + branco_nulo fica perto de 100;
  2 quando a pergunta pede dois nomes e a soma passa de 150. Gravar sempre `soma_total`.
- `partido` em maiúsculas, siglas do TSE (`UNIÃO`, `PCdoB` vira `PCDOB`, `MISSÃO`); sem partido conhecido, `null`.
- Candidatos com valor 0 entram mesmo assim; o motor decide.
- Fonte sem PDF é legítima quando o painel do contratante publica a série (G1), mas o arquivo bruto
  da API precisa ficar salvo em `data/originals/senado_102026/` com SHA-256.
- Nunca inventar `campo` nem `n`: quando o painel só traz a metodologia da onda mais recente,
  as ondas antigas recebem `"campo": null` e `"n": null`, e o motor as usa só como histórico.

## 2. TSE: candidaturas, fotos e Senado que continua

Script: `scripts/senado-2026-tse.py`. Saídas:

- `analysis/senado_2026/tse_candidatos.json`: lista de candidaturas a senador em 2026 (cargo 5 do
  `consulta_cand_2026.zip`), com `uf`, `sq_candidato`, `nome_urna`, `nome_completo`, `numero`,
  `partido`, `coligacao`/`federacao`, `situacao_candidatura` (apto/inapto/etc.), `situacao_totalizacao`
  se houver, `foto` (caminho relativo `img/senado/<UF>_<sq>.jpg` quando a foto existir, senão `null`).
- `docs/img/senado/<UF>_<sq>.jpg`: foto oficial do TSE recortada em quadrado, 240×240, qualidade
  JPEG 82. Só das candidaturas que aparecem em alguma pesquisa de `analysis/senado_2026/pesquisas/`
  ou estão entre as 6 mais votadas de cada estado em qualquer pesquisa; não publicar as centenas restantes.
- `analysis/senado_2026/senadores_2022.json`: os 27 eleitos em 2022 (um por UF) com nome, partido
  na eleição, UF e votos, lidos de `data/raw/tse_resultados/votacao_candidato_munzona_2022.zip`
  (cargo 5, `DS_SIT_TOT_TURNO` = eleito). Esses 27 continuam até 2031 e compõem o Senado de 2027
  com os 54 eleitos em 2026 (duas vagas por UF).
- `analysis/senado_2026/eleitorado_uf_2026.json`: eleitorado apto por UF (reaproveitar o que
  `scripts/predicao_2026/tse.py` já extrai, se existir em `data/outputs/predicao_2026/`).
- Casamento pesquisa × TSE por `uf` + nome de urna normalizado (sem acento, minúsculas, sem
  partido entre parênteses) com tabela de apelidos explícita no script quando o nome da pesquisa
  diferir do nome de urna. Gravar o casamento em `analysis/senado_2026/casamento_nomes.json` e
  listar os não casados; nenhum casamento por adivinhação silenciosa.

## 3. Motor: `scripts/senado_2026/motor.py`

Entrada: todos os JSON da pasta de pesquisas, `tse_candidatos.json`, `senadores_2022.json`,
`PARTIDO_CAMPO` importado de `voto_util_base` (tucano é centro-esquerda; PSD é centro; União, PP e
Podemos centro-direita; PL, Novo e Republicanos direita), mais exceções declaradas no próprio motor.

Saída: `docs/assets/predicao_senado.json`:

```json
{
  "gerado_em": "2026-10-03T23:40:00Z",
  "data_referencia": "2026-10-03",
  "eleicao": "2026-10-04",
  "parametros": {"meia_vida_dias": 7, "janela_campo_minimo": "2026-09-28", "simulacoes": 20000, "...": "..."},
  "estados": {
    "SP": {
      "uf": "SP", "nome": "São Paulo", "eleitorado": 35000000,
      "pesquisas_usadas": [{"arquivo": "datafolha_SP_2026-10-03.json", "peso": 0.61, "campo_fim": "2026-10-03"}],
      "pesquisas_descartadas": [{"arquivo": "...", "motivo": "campo anterior a 28/09"}],
      "cobertura": "recente | antiga | sem_pesquisa",
      "media": [{"nome": "Guilherme Derrite", "partido": "PP", "campo": "centro-direita", "valor": 16.2, "validos": 22.4}],
      "probabilidades": [
        {"nome": "Guilherme Derrite", "partido": "PP", "campo": "centro-direita", "sq_candidato": "250001234567",
         "foto": "img/senado/SP_250001234567.jpg", "p_eleito": 0.71, "p_primeiro": 0.38, "ic90_validos": [17.1, 27.9]}
      ],
      "eleitos_provaveis": ["Guilherme Derrite", "André do Prado"],
      "p_dupla_mais_provavel": 0.41,
      "incerteza": "alta | media | baixa",
      "notas": ["..."]
    }
  },
  "senado_2027": {
    "continuam": [{"uf": "SP", "nome": "...", "partido": "...", "campo": "..."}],
    "por_campo": {"direita": {"esperado": 27.4, "ic90": [23, 32], "continuam": 11, "novos_esperado": 16.4}},
    "por_partido": {"PL": {"esperado": 14.2, "ic90": [11, 18], "continuam": 8}},
    "p_maioria_direita_mais_centro_direita": 0.62,
    "p_41_direita_centro_direita_centro": 0.9,
    "p_54_bloco_oposicao": 0.08
  },
  "validacao": {"...": "o que foi conferido"},
  "fontes": [{"arquivo": "...", "instituto": "...", "uf": "...", "campo": "...", "url": "...", "sha256": "..."}]
}
```

Exigências do motor, para o Opus:

- Probabilidade de eleição, não votos válidos: Monte Carlo com erro comum ao estado e erro
  idiossincrático por candidato; a escala do erro é parâmetro declarado em `parametros`, com a
  justificativa histórica escrita (erro de pesquisa de Senado no Brasil é bem maior que o presidencial;
  documentar a fonte usada para calibrar, e, se não houver fonte conferível, declarar como hipótese).
- Indecisos e branco/nulo: distribuição central proporcional ao voto declarado, com sensibilidade
  uniforme, e nunca 100% para um nome.
- Média por recência (meia-vida em dias pelo ponto médio do campo) e uma onda por casa por estado;
  peso igual entre casas na combinação. Pesquisa com campo anterior a 28/09 não entra na central: vira
  prior fraca com peso explícito quando o estado não tem pesquisa recente, e o estado recebe
  `cobertura: "antiga"` e `incerteza: "alta"`. Estado sem pesquisa alguma: `cobertura: "sem_pesquisa"`,
  sem nome nos eleitos prováveis.
- `p_eleito` soma 2,0 por estado (duas vagas). Teste obrigatório.
- Paridade: o JSON carrega tudo o que a página precisa; a página não recalcula nada.
- Testes em `tests/test_predicao_senado.py`: esquema, soma 2,0, monotonicidade (quem tem mais voto não
  tem menos probabilidade com mesma incerteza), estado sem pesquisa, reprodutibilidade com semente.

## 4. Página: `scripts/senado-2026-build.py`

- Mapa do Brasil com a malha do IBGE já usada em `scripts/predicao_2026/mapa.py` (importar a geometria
  de lá, não duplicar); cada UF pintada pelo campo dos dois eleitos prováveis (dois campos iguais: cor
  cheia; campos diferentes: hachura dos dois); ao lado ou no toque, a ficha com as duas fotos, nomes,
  partidos e `p_eleito`. Sem JS a página continua completa (fichas de todos os estados abaixo do mapa).
- Hemiciclo do Senado de 2027 com 81 assentos: 27 que continuam (contorno) e 54 esperados (cheio),
  por campo e por partido, com o intervalo de 90%.
- Tabela das 27 UFs: eleitos prováveis, probabilidades, terceiro colocado, pesquisas usadas com data
  de campo e link, cobertura.
- Capítulos: o que a página responde; como lemos (método, em linguagem de aula, com analogia);
  limites (campo de 28/09 a 03/10, uma casa em muitos estados, erro histórico, voto útil de última hora);
  fontes com URL, hash e página.
- CSS reaproveitando `docs/assets/predicao_2026.css` e `predicao_2026_ux.css`; sem travessão;
  rodar `python3 scripts/contrast-audit.py` e `python3 scripts/render-audit.py` antes de publicar.
- Card social: acrescentar `predicao_senado` ao manifesto de `scripts/social-cards.py` e rodar
  `python3 scripts/social-cards.py --only predicao_senado`. Link na `docs/index.html`.
