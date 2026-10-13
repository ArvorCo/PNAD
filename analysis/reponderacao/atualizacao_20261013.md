# Atualização do segundo turno — 13/10/2026

Seis ondas nacionais novas e revisão documental da Datafolha já divulgada em 08/10.
As íntegras estão em `data/originals/`, com URL, captura, SHA-256 e páginas transcritas
em `fonte.json` e nos registros de `analysis/reponderacao/pesquisas/`.

| Casa | Campo | Divulgação | Registro | Uso atual |
|---|---|---|---|---|
| Datafolha | 06–07/10 | 08/10; íntegra recebida 13/10 | BR-02949/2026 | PNAD, bases ponderadas atuais |
| Ipespe/ABRAPEL | 06–08/10 | 10/10 | BR-00933/2026 | PNAD |
| DataTrends | 07–09/10 | 11/10 | BR-03576/2026 | Publicado na Projeção |
| Futura | 07–10/10 | 13/10 | BR-00650/2026 | Publicado na Projeção |
| GERP | 08, 09 e 12/10 | 13/10 | BR-07877/2026 | PNAD |
| Nexus/BTG | 10–12/10 | 13/10 | BR-07997/2026 | PNAD |
| PoderData | 10–12/10 | 13/10 | BR-01209/2026 | PNAD |

## Decisões verificáveis

- **Datafolha:** PDF de 34 páginas fornecido pelo usuário, preservado integralmente
  em `docs/fontes/datafolha_2t_08102026_integra.pdf`. P. 26: bases atuais 1.187/874/337,
  2.398 de 2.520 entrevistas com renda. Perfil da p. 23 e controles por sexo e região
  conferidos. A ficha técnica corrige o campo para 06–07/10. O id da onda é mantido.
- **Renda sem resposta:** para a revisão Datafolha e a nova GERP, o contrafactual é
  `publicado + q × (PNAD − recomposto)`, com `q = 2398/2520` e `87/101`, respectivamente.
  As faixas GERP da p. 8 somam 87 e a recusa 14 (101 por arredondamento).
  O ajuste só alcança a massa conhecida; nenhuma preferência é atribuída à recusa.
  `q=1` mantém exatamente a aritmética legada. Ondas históricas e versões publicadas
  do simulador continuam com seu método documentado; não são revisadas retroativamente.
- **Futura:** [íntegra de 18 páginas](https://static.poder360.com.br/uploads/2026/10/Pesquisa-Futura-presidente.pdf),
  p. 7 com perfil familiar, p. 11 com voto por sexo/região/idade, sem voto por renda.
  Vetor completo 50/46,6/1,7/1,7 na Projeção, peso por recência 11,41%.
  Na última onda do 1º turno, erro F−L de +0,240259 pp; Flávio −2,290930 e Lula
  −2,531189 pp nos válidos. Fonte: `analysis/apuracao_2026/dados/pesquisas_vs_urna.json`.
  Boa aproximação da diferença não equivale a acerto dos níveis. Não foi criado
  bônus de precisão a partir de uma eleição.
- **DataTrends:** [íntegra](https://static.poder360.com.br/uploads/2026/10/pesquisa-datatrends-nacional-11out2026.pdf),
  p. 7 diz renda domiciliar *per capita*, p. 4 diz renda domiciliar *total*; p. 25
  tem voto por renda. Sem conciliação da variável, não substituir por renda familiar.
  P. 12 dá 1% de indecisos, p. 4 dá 2%; escolhido o gráfico principal, ambas as versões
  preservadas. PesqEle confirmou registro, datas e amostra; os campos de metodologia
  e plano não exibiram texto no documento consultado. Isso não identifica sua ausência
  no registro. Transcrição dos campos visíveis em `registro_transcrito.json`.
- **Ipespe:** p. 33 da [íntegra](https://static.poder360.com.br/uploads/2026/10/pesquisa-ipespe-abrapel-10out2026.pdf)
  informa CATI; p. 5 informa 3% de indecisos. Prevalece o PDF sobre a matéria.
- **PoderData:** a matéria inicial ainda apontava para o PDF da onda anterior.
  Usada a [íntegra de 12/10](https://static.poder360.com.br/uploads/2026/10/Relatorio-PoderData-Eleitoral-12out26-1.pdf),
  com perfil atual da p. 4 e cruzamentos da p. 9.
- **GERP:** relatório oficial do [manifesto do instituto](https://gerp.com.br/relatorios/manifest.json),
  57 páginas. Perfil na p. 8 e voto por renda/sexo na p. 16 conferidos visualmente.
- **Nexus:** [íntegra oficial](https://www.nexus.fsb.com.br/wp-content/uploads/2026/10/BTG-Nexus-Eleicoes-2026-Rodada-17-13.out_.2026.pdf),
  102 páginas, perfil na p. 99 e voto por renda na p. 41. Comparecimento declarado
  de 95% na p. 15 não substitui automaticamente a previsão calibrada de presença.

## Estaduais e alcance da busca

Adicionada Quaest DF, campo 08–11/10, divulgação 12/10, 1.104 entrevistas:
[fonte arquivada](https://exame.com/brasil/quaest-no-df-flavio-bolsonaro-lidera-com-50-das-intencoes-de-voto-lula-tem-40/).
Totais F50/L40/B-N6/U4. DF-08737/2026 e BR-06799/2026 preservados com suas fontes,
sem tratar os registros estadual e presidencial como a mesma identificação.
Sem íntegra/cruzamento de renda localizado.

A busca por presidenciais em DF, SP, MG, RJ, PE, BA e PR encontrou apenas DF com
placar verificável e campo posterior a 04/10. Datafolha SP publicada em 05/10 e
íntegras Quaest carregadas depois da urna tinham campo anterior. Registros e agendas
de Quaest nacional 14/10 e Datafolha 15/10 não são resultados. A varredura não prova
inexistência de outras pesquisas. Datafolha DF e Quaest DF cobrem a mesma UF:
1,430865% do eleitorado, contado uma vez. Permanecem como diagnóstico territorial,
sem incorporar uma UF como se fosse mais uma pesquisa nacional.

## Centrais e reprodução

Central Média: cinco casas com renda, peso igual, **F54,6623/L45,3377** nos válidos.
Central Projeção: oito casas, peso por recência, **F53,9926/L46,0074**.
Vox continua publicada na Projeção sem ajuste de renda.
Não há série suficiente dentro de casa para identificar tendência do 2º turno;
inclinação zero explicitada. Monte Carlo mantém 2.000 sorteios congelados.
Resultados condicionais ao comparecimento de 79,157882%, presença relativa F +3,8%,
conversão de indecisos em válidos de 100% e divisão automática proporcional.

```sh
python3 scripts/pesquisas-131026-renda.py
python3 scripts/reponderacao-pnad.py calcular --hoje 2026-10-13
python3 scripts/reponderacao-build.py
python3 scripts/social-cards.py --only reponderacao_pnad reponderacao_pnad_log
```

As páginas mostram números absolutos e permitem alterar as hipóteses. Versões antigas
dos links preservam dados, motor e sorteios. Arquivo do 1º turno e predição pré-urna
não recebem novas pesquisas. Histórico registra a revisão Datafolha sem criar onda dupla.

Os painéis de cobertura do arquivo do 1º turno agora recalculam sua janela em 04/10,
por `reponderacao-arquivo.close`, sem deixar a data do 2º turno esvaziar as médias.
Séries de primeiro turno encerradas nessa data; placares das 73 ondas existentes
permanecem iguais. O gerador dos sete cards de setembro reutiliza o recorte em 15/09;
textos e apresentação foram separados em `superthread_092026_cards.py`, preservando
seu contrato e mantendo cada módulo abaixo de mil linhas. A página histórica de
setembro já publicada não foi regenerada nesta atualização.
