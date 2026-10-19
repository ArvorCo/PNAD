# Dossiês do segundo turno — Nexus 13/10 e Datafolha 08/10

Objetivo: dois diagnósticos sobre perguntas, transferências declaradas, renda,
ponderação, segmentos e contexto brasileiro. Os dossiês não recalibram as
centrais do agregador nem alteram links publicados.

## Fontes e universos

- Nexus: relatório oficial da 17ª rodada, 102 páginas, campo 10–12/10, n=2.002.
  PDF preservado em `data/originals/nexus_102026_13/` e cópia pública em
  `docs/fontes/nexus_btg_13102026.pdf`. Registro BR-07997/2026 prevê n=2.000.
- Datafolha: PDF de 34 páginas recebido do usuário, campo efetivo 06–07/10,
  divulgação 08/10, n=2.520, 153 municípios. Cópia pública já preservada em
  `docs/fontes/datafolha_2t_08102026_integra.pdf`. Registro BR-02949/2026
  planejava campo 06–08/10; usar as fichas finais para o campo realizado.
- PesqEle consultado em 13/10. Registros locais são transcrições dos campos
  visíveis, não exportações originais. Não há declaração de calibração pelo
  voto do 1º turno nesses planos ou relatórios; isso não demonstra inexistência
  de ajustes internos. Nenhum peso político é inferido a partir do cruzamento.
- Nexus: 9 perguntas cruzadas × 29 segmentos. Datafolha: todo o anexo nativo,
  10 perguntas × 31 segmentos. Sexo, idade e região recompõem cada total;
  Nexus também permite controles por renda, religião, ocupação e município.
  Resíduos são aritméticos, não intervalos de confiança.
- Traços Datafolha permanecem `null`. Zeros sem barra nas figuras especiais
  da Nexus são identificados como ausência de barra; não medir precisão infinita.
  Arredondamentos de 99/101% não são completados com respondentes inventados.

## Leituras que precisam permanecer claras

1. Transferências Nexus são condicionais ao voto lembrado, com bases dos grupos
   não publicadas. Não são fluxos nacionais em milhões nem painel longitudinal.
   Datafolha divulga apenas o agregado Cury/Renan/Caiado/Zema na apresentação:
   46/32/15; o restante de 7% é resíduo não detalhado, não indecisão identificada.
2. A renda Nexus mantém 19/18/40/23 desde 28/09 e PNADC anual 2025 como referência.
   Mesmo perfil não mantém o delta eleitoral: mudam os votos dentro das faixas.
   Datafolha mantém alvo declarado 49/47/4 e fator de renda previsto 1, como nos
   registros de setembro; referência PNADC-A 2024. Perfil atual não prova novo peso.
3. Datafolha: 1.187/874/337 são bases ponderadas atuais; 2.398 de 2.520 conhecidas.
   47,1% de baixa renda no total ≠ 49,5% entre declarantes. O delta PNAD recebe
   q=2398/2520 e conserva a massa restante no topline. A conta é sensibilidade.
4. Firmeza Datafolha usa 2.488; motivação usa 2.366. 94% firme é aproximadamente
   92,8% na base total; 19% de voto negativo, aproximadamente 17,8%. Bases da
   apresentação diferem e sua natureza não está explicitada. Não inferir composição
   eleitoral a partir das contagens da pergunta de motivação.
5. Nexus: 95% de presença certa/provável é declaração, não previsão calibrada.
   Segunda opção usa os 7% que admitem mudar e se sobrepõe à indecisão. Piso/teto
   não é intervalo estatístico. Expectativa de vitória não é voto nem probabilidade.
6. Escalas anti-Lula/anti-Bolsonaro, rejeição dos candidatos e cansaço com a
   polarização são perguntas distintas. Bolsa Família pergunta pelo domicílio,
   não apenas pelo titular individual. Associações com voto não identificam causas.
7. Economia atual, comparação com governo anterior e próximos seis meses têm
   horizontes diferentes. Otimismo futuro favorece Flávio no cruzamento de voto;
   não é apoio automático ao governo atual nem prova da causa desse otimismo.
8. Problemas do país: duas menções espontâneas, sem partição de 100%. Corrupção
   supera saúde na primeira menção; saúde supera corrupção nas duas somadas.
   Não usar a contagem como efeito causal sobre a escolha eleitoral.
9. Regiões Norte/CO aparecem agrupadas nas duas publicações. Faixas etárias
   intermediárias diferem entre as casas. Não fazer uma subtração como migração
   real no tempo. Recortes sociodemográficos sobrepostos não podem ser somados.

## Reprodução e apresentação

```sh
python3 scripts/dossies-2t-2026-audit.py
python3 scripts/dossies-2t-2026-build.py
python3 scripts/social-cards.py --only nexus_btg_13102026 datafolha_08102026
pytest -q tests/test_dossies_2t_2026.py
```

Fontes em `scripts/dossies_2t_2026/`, cada módulo abaixo de mil linhas.
JSON de análise mantém uma linha por segmento; dados públicos identificam
páginas, universos, bases e controles. Gráficos preservam os números nos
rótulos; a geometria fecha na soma das partes conhecidas quando arredondadas.
Traço com parcela desconhecida não é preenchido como zero. Valores completos
ficam nas tabelas acessíveis; barras curtas podem não receber rótulo visual.

Explorador: pergunta × dimensão, com universos e bases atualizados e link à
página física. Interface móvel usa barras HTML legíveis sem depender de texto
SVG reduzido. Sem JavaScript, gráficos, diagnósticos, fontes e tabelas completas
continuam acessíveis. Contratos em `tests/test_dossies_2t_2026.py` e conferência
real do navegador em `tmp/dossies_20261013/qa.py` (arquivo de trabalho ignorado).

## 18ª rodada Nexus: campo encerrado em 18/10, divulgação em 19/10

`nexus-btg-191026-build.py` gera `docs/nexus_btg_18102026.html` e seu JSON de
apoio, a partir de `scripts/nexus_191026/`. O nome solicitado usa o fim do
campo; todos os rótulos identificam a divulgação de 19/10. Não regerar o dossiê
anterior para incorporar esta onda.

Fonte oficial: `data/originals/nexus_102026_19/relatorio.pdf`, 128 páginas,
SHA-256 `f6ee08157b9906a8abd4fca2a7a418b329e8895043019bc871b81f12b1eabb45`.
Cópia pública idêntica em `docs/fontes/nexus_btg_18102026.pdf`. A URL e a hora
do download ficam no `fonte.json` local. Registro BR-04499/2026 conforme a ficha
p. 4; não foi feita nova transcrição independente do PesqEle nesta rodada.

- Extração decimal, onze perguntas, 29 linhas incluindo o total, oito dimensões.
  As páginas iniciais de cada matriz foram conferidas visualmente (8, 13, 17,
  42, 52, 63, 78, 89, 91, 104, 111), além do voto por renda p. 43 e perfil p. 125.
  Recomposição com o perfil desta onda: resíduos abaixo de 0,47 pp. Isso é
  controle de transcrição, não validação do desenho amostral.
- Perfil atual 21/16/40/23; antes/depois da ponderação não explícito. Sensibilidade
  condicional ao perfil publicado, ancorada no total publicado; sem imputação
  de renda ausente. Rótulos com uma casa decimal preservados nas tabelas HTML.
- Bases por segmento ausentes continuam `null`. Presença 92,9% declarada não
  substitui o comparecimento TSE nem as propensões históricas do simulador.
- Conferência visual das figuras: transferências p. 27, firmeza p. 35, motivação
  pp. 54–55, cenário da escala 6x1 p. 80, problemas p. 114 e economia pp. 118,
  120 e 122. A motivação de cada candidatura é condicional; sua parcela no
  total é 45,9% × 12,0% + 46,5% × 21,0% = 15,273%, compatível com 15,3% divulgado.
  Duas menções de problemas não formam partição. Presente, governo anterior e
  próximos seis meses são horizontes separados. Respostas hipotéticas sobre
  jornada não são convertidas em efeito causal ou votos nas centrais.
- PoderData de 19/10 também integra a reponderação: fonte oficial de 33 páginas
  em `data/originals/poderdata_102026_19/`, SHA-256
  `49d00ff66ff81342274af5c18ec09ae2ef154ab7316136a648bf1a3cfcaea6b2`,
  BR-02586/2026. Perfil 46/33/21 e renda p. 9, conferidos por sexo p. 7; soma
  publicada 101 por arredondamento e válidos divulgados 52/48 separados.

```sh
python3 scripts/pesquisas-191026-renda.py
python3 scripts/reponderacao-pnad.py calcular --hoje 2026-10-19
python3 scripts/reponderacao-build.py
python3 scripts/nexus-btg-191026-build.py
python3 scripts/social-cards.py --only nexus_btg_18102026 reponderacao_pnad hub
pytest -q tests/test_nexus_191026.py
```

O novo dossiê sozinho não recalcula centrais. O explorador recebe a página do
perfil no payload (`profile_page=125`); páginas antigas mantêm o padrão 99.
A correção da tabela acessível de barras preserva decimais e mantém os inteiros
anteriores. Conferência do navegador em 390 e 1021 px, onze opções funcionais,
sem transbordamento horizontal do documento.
