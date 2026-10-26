# Revisão hostil do dossiê do 2º turno: seis ângulos (26/10/2026)

Memorando interno. Objeto: `docs/apuracao_2T_2026.html` (gerado, não editado) e `analysis/apuracao_2t_2026/dados/*.json`. Toda conta abaixo foi refeita a partir dos arquivos citados, não copiada da página. Rótulo da casa vale para tudo: sinal pede explicação, não prova irregularidade.

Arquivos lidos: `secoes.json`, `secoes_voto.json`, `biometria.json` (via página), `data/outputs/apuracao_2t_2026/secoes_linhas.json.gz` (499.207 linhas, SHA-256 conferido pelo leitor `scripts/apuracao_2t_2026/secoes_linhas.py`), `abstencao.json`, `comparacao_1t.json`, `cedo_tarde.json`, `logs.json`, `presidente.json`, `noticias_noite.json`, `apuracao/data/secoes_2t_2026.sqlite` (tabela `voto_secao`), `video/apuracao_2t/roteiro/roteiro.md`, `docs/assets/apuracao_2t/boletins/*.txt` e `*.meta.json`, `apuracao/data/vinheta/encerramento.txt`, `analysis/apuracao_2t_2026/video.json`.

---

## 1. Mesário que libera eleitor ausente ("pianista")

**O que a página testa.** Capítulo 9, bloco "Biometria: cadastro, leitor e a hipótese do pianista". Célula de teste: comparecimento pelo menos 5 pp acima da própria seção no 1º turno **e** salto da parcela sem biometria reconhecida (sem cadastro + ano de nascimento ≥ 10% e +5 pp contra a própria seção). Regra em `scripts/apuracao_2t_2026/secoes_sinais.py`, linha 154 (`pianista = delta & sinal_salto_bio`). A página declara 1.324 seções, 0,27% do país.

**Refeito a partir de `secoes_linhas.json.gz`.**
- Coluna `pianista` do arquivo: 1.324 seções. Recalculando a regra do zero com `sem_bio_pct + ano_nasc_pct` (2T e 1T) e `delta_pp`: 1.325; as 5 divergências de classificação vêm de arredondamento a duas casas no limiar. 1.324/499.207 = 0,265%. **Bate.**
- 778 municípios; 401.393 aptos e 319.827 votantes na célula. Mediana da alta de comparecimento +6,21 pp; mediana do salto de biometria +6,03 pp.
- Voto na célula: Flávio × Lula 117.791 × 191.333 no 2º turno, 105.143 × 155.068 no 1º. Fatia de Flávio entre os dois: 40,41% para 38,11% (−2,30 pp). No país, nas seções com 1º turno: 51,02% para 48,22% (−2,80 pp). A célula andou **menos** para Lula que o país.
- Contra as vizinhas do mesmo município (média ponderada por votos, como em `secoes_voto.py`): −2,50 pp (ep 0,24). Diferença em diferenças contra o 1º turno: **+0,076 pp (ep 0,055)**. `secoes_voto.json`, sinal `pianista`: −2,50 (ep 0,24) e +0,08 (ep 0,05). **Bate.**
- Checagem independente com efeito fixo de município, sem peso, erro-padrão por município: +0,069 pp (ep 0,064). Mesmo resultado: zero estatístico, sinal a favor de Flávio se algum.
- Teto de impacto: Lula ganhou 36.265 votos absolutos na célula entre os turnos (Flávio, 12.648). Mesmo atribuindo todo o ganho de Lula à célula inteira, são 0,82% da margem de 4.430.191 (`presidente.json`, `nacional.margem_lula_votos`).
- Onde está: Rio de Janeiro capital 95 seções, São Paulo capital 47, Salvador 15. Só 21 das 1.324 encerraram o BU depois das 19h e 34 têm sinal de tardia: a célula não é filha da prorrogação.
- Urna de contingência ou reserva (`tipo_urna` 4) em 55 das 1.324 (4,2%), contra 1,15% no país. Troca de urna é explicação concorrente forte para o salto de biometria (urna substituta, leitor diferente) e não aparece no texto do bloco.

**A página diz o voto da célula?** Só no gráfico (`fig-secoes_did`, ficha "comparecimento ≥ +5 pp e salto da parcela sem biometria reconhecida": DiD +0,08, ep 0,05; −2,50 contra vizinhas). A prosa do bloco do pianista não traz o número. A tabela 2×2×2 logo abaixo usa outra célula ("biometria baixa", 4.078 seções, −2,89 pp contra −2,96 pp sem sinal), o que dá ao leitor a impressão de que essa é a célula do pianista.

**De "compatível" a "identificado".** Hoje a célula é compatível com duas leituras (liberação indevida ou leitor falhando num dia de fila maior), e o voto não se move. Para identificar seria preciso, por seção da célula:
1. Ata da mesa receptora: registro de liberação por ano de nascimento, de troca de urna, de ocorrência e de quem estava na fila às 17h.
2. Caderno de votação: assinatura ou digital de cada eleitor habilitado por documento; nome de eleitor falecido, ausente do país ou com justificativa registrada.
3. Log de habilitação por hora: os logs do 2º turno já estão no acervo (`data/outputs/logs_urnas_2t_2026.sqlite`) e a página não cruzou a célula com eles. A marca de pianista no log seria rajada de habilitações por ano de nascimento com intervalos curtos e regulares, concentrada perto do fechamento, sem reinício nem troca de urna que explique a falha do leitor. Esse cruzamento é factível agora, sem documento novo.
4. Lista de comparecimento do TSE (quem votou), para casar com óbitos e com quem justificou ausência.

Veredito: compatível com falha de leitor, sem efeito no voto (+0,08 pp, ep 0,05). Não identificado; o passo 3 está ao alcance da casa.

---

## 2. Transporte em massa

**O que a página diz.** Capítulo 15 (Hipóteses), H3 "Transporte e comparecimento diferencial": descartada como explicação do deslocamento inteiro, com fração de décimos de ponto ainda compatível. Os números do H3 conferem com os arquivos: Sudeste +2,43 pp, Sul +2,27, Nordeste +1,90, Norte −1,82 de comparecimento (`abstencao.json`, `regioes[].delta_1t_pp` com sinal invertido); Bahia −1,44 pp de Flávio contra −2,80 no país (`comparacao_1t.json`, `ufs[BA].swing_h2h_flavio_pp`, `brasil.swing_h2h_flavio_pp`); 16h com 5,18% dos votos contra 8,95% no 1º turno (`logs.json`, `cadencia.brasil_2t.pct_ultima_hora`, `amostra_1t.brasil_1t.pct_ultima_hora`).

**Abstenção caiu mais onde?**
- Por UF (`abstencao.json`, `ufs`): maiores quedas BA −3,26, PE −2,99, SP −2,73, MS −2,63, PR −2,53, MG −2,48. Subiu em 9 UFs, todas no Norte e no Meio-Norte: AP +8,06, RR +6,03, AC +5,65, AM +1,51, PA +1,22, TO +0,89, MA +0,63, RO +0,21, PI +0,04.
- Por quintil de voto em Lula no 1º turno, quintis de mesmo eleitorado, refeito de `comparacao_1t.json` (`municipios`): −1,83, −1,72, −2,11, −2,05, −1,55 pp, do mais fraco ao mais forte em Lula. Por número de municípios (critério da página): −1,81 a −1,22; a página publica −1,80 e −1,22. A queda foi **menor** nos redutos de Lula. Correlação municipal sem peso entre variação da abstenção e Lula no 1º turno: +0,14 (onde Lula é mais forte, a abstenção caiu menos).
- Contraprova que a página não mostra: contra o 2º turno de 2022 o desenho inverte. Em 2.631 municípios com 10 mil aptos ou mais (`abstencao.json`, `municipios_10mil`, `delta_2022_pp`), quintis por Lula no 1º turno: −1,28, −0,70, −0,45, −1,24, **−3,12** pp. Por região contra 2022, o Nordeste lidera a queda (−2,82 pp; Sudeste −0,98; Sul −0,41). Leitura: a régua do 1º turno de 2026 é a certa para medir a mudança entre turnos, mas o 1º turno teve a maior abstenção desde 1998; contra 2022, os redutos de Lula estão de fato mais presentes. Isso não muda o H3 (o deslocamento entre turnos não acompanha a abstenção), mas um leitor hostil vai fazer essa conta.

**Cadência por hora, 16h a 19h, por região** (`logs.json`, `cadencia.regioes`; 1º turno é amostra de uma seção em cinco):

| Região | 16h 2T | 17–19h 2T | votos 17–19h 2T | 16h 1T | 17–19h 1T |
|---|---|---|---|---|---|
| Norte | 5,81% | 0,034% | 3.535 | 9,99% | 4,56% |
| Nordeste | 5,49% | 0,027% | 9.972 | 10,27% | 6,18% |
| Centro-Oeste | 5,18% | 0,032% | 3.045 | 9,15% | 1,89% |
| Sudeste | 4,95% | 0,029% | 15.542 | 8,17% | 1,26% |
| Sul | 4,88% | 0,012% | 2.218 | 7,87% | 0,64% |

O Nordeste tem a última hora um pouco maior que Sul e Sudeste (5,49% contra 4,9%), diferença de meio ponto que também existia no 1º turno, e nenhuma cauda depois das 17h.

**Bahia.** `noticias_noite.json`: TRE-BA manda prender o secretário de Mobilidade de Salvador às 12h47; Procon-BA conta 370 ônibus parados às 16h16 e 544 às 17h09; o corregedor manda distribuir senha a quem estivesse no local às 17h. Os dados: a Bahia teve a **maior** queda de abstenção do país (−3,26 pp); Salvador −4,37 (20,14% para 15,77%), Feira de Santana −4,24, Lauro de Freitas −5,64 (`comparacao_1t.json`). Contra 2022, Salvador só −0,31 (`abstencao.json`, `capitais_lista`): o 2º turno voltou ao nível de 2022 depois de um 1º turno anormalmente ausente. Flávio perdeu −2,53 pp em Salvador e −1,44 na Bahia, menos que o país. O ônibus parado não deixou marca de abstenção alta nem de deslocamento pró-Lula maior.

**Conclusão.** A marca de transporte de última hora (comparecimento concentrado no fim do dia, onde Lula é forte, com deslocamento maior) **não aparece**: a última hora encolheu em todas as regiões, a queda da abstenção foi menor nos redutos de Lula contra o 1º turno, e a Bahia andou menos para Lula que o país. Mobilização antes das 16h não se separa nos dados; a página diz isso.

---

## 3. Boca de urna e pressão no dia

- A página declara, no capítulo 8, bloco de hipóteses da abstenção: "É crime eleitoral no dia da votação (Lei 9.504/1997, art. 39, § 5º). A totalização não registra abordagem de eleitor; nada neste capítulo mede ou descarta essa conduta. Relato precisa de registro em ata ou de ocorrência." E nos limites: "O acervo não tem oferta de transporte, ocorrência de boca de urna nem tempo observado em 25/10." **Confirmado.** A citação legal está correta (art. 39, § 5º, II).
- O que a casa publica como caminho: ata e ocorrência (capítulo 8) e, no capítulo de notícias, o balanço do MJSP até 19h com 618 ocorrências, 57 presos e boca de urna em 13,3% dos casos (≈ 82 ocorrências, conta minha; a página não faz a conta), mais três casos nominais no Rio (fiscais do PL levados à PF na Praça Mauá e no Largo do Machado).
- Relatos exportados do Supabase: `analysis/politize_se/relatos/` existe, é ignorado pelo git (`.gitignore`, linha 212) e está **vazio**. Não há exportação local; não consultei o Supabase. O canal de relato por seção do Politize SE (tabela `relato_secao`, contrato em `analysis/politize_se/CONTRATO.md`, seção "Relatos (26/10/2026)") não é citado na página como caminho para o leitor.

---

## 4. Horários: o que entrou cedo e o que entrou tarde

**Dois números refeitos.**
- Fatia de Flávio entre os dois por decil de hora de fechamento do município (`cedo_tarde.json`, `decis_2t`): 1º decil 1.170.886 / (1.170.886 + 1.452.395) = **44,63%**; 10º decil 24.182.046 / (24.182.046 + 26.987.885) = **47,26%**. Mudança contra o 1º turno: −2,31 e −3,08 pp. **Bate com a página.**
- Votos computados depois das 17h (`logs.json`, `cadencia.brasil_2t`): (34.312 + 11) / 127.818.872 = **0,0269%**. A página diz 0,027%; o vídeo arredonda para 0,03%. No 1º turno, 2,89% entre 17h e 19h e 0,11% depois das 19h (amostra). **Bate.**

**Teste extra, por ordem de recebimento de cada BU** (`secoes_linhas`, `rec_min`, decis de mesmo número de votos, sem exterior): a fatia de Flávio cai de 51,45% (2º decil, 19:38 a 19:58, PR, RS e MG) para 46,15% (último, 21:02 a 23:21, RJ, SP e BA), enquanto a mudança contra o 1º turno fica entre −2,59 e −3,10 pp em todos os decis. Somando na ordem de recebimento, Flávio fica à frente de 19:41 a 20:25, com máximo de 50,66%; o roteiro do vídeo diz 19:50 a 20:25 e 50,7% pela publicação do TSE. A virada da noite foi **efeito de ordem de chegada** (Sul e interior primeiro, capitais do Sudeste e Salvador por último), não voto tardio diferente. O capítulo 5 chega à mesma conclusão por município e por zona; a régua por seção é mais direta e não está na página.

**A página separa bem cedo e tarde?** Separa no capítulo 5 e no 11. Falha no capítulo 9 e no 8:
- Capítulo 9, "Seção por seção": "Último voto na mediana às 17:01, 99º percentil às 19:00" e "Votaram depois das 19:00 0,90% das seções do país, 4.468 seções". O campo lido é `encerramento` do BU (`secoes.json`, `prorrogacao.brasil.n_apos_1900` = 4.468), que é a hora de encerramento da urna, não do último voto. O log mostra o contrário: dos 4.468 BUs encerrados depois das 19h, em 2.705 o último voto foi até 17:15 e em só 10 depois das 19h; no país, 11 votos depois das 19h (`logs.json`, `cadencia.bu_apos_19h`, `ultimo_voto.depois_19`). O H1 e o vídeo usam a formulação correta ("encerrados"). O comentário do esquema do banco (`apuracao/data/secoes_2t_2026.sqlite`, tabela `bu`, coluna `encerramento -- último voto`) é a origem do rótulo errado.
- Capítulo 8, hipótese da prorrogação: "só 0,90% das seções lidas votaram depois das 19h" e "Na amostra de 497.897 seções" (é a base completa, não amostra). Mesmo erro de rótulo.
- Último voto p50 por UF (`secoes.json`, `prorrogacao.por_uf`, na verdade encerramento): 17:01 a 17:03 em todas; lag encerramento a recebimento p50 de 150 min (DF) a 236 min (SE), 204 min no país; RJ e SP com primeiro recebimento às 19:03, SE às 19:34. O texto escreve "entre 19:03 e 19:03 (RJ, SP)", frase que o gerador deveria colapsar.
- Um BU recebido às 16:59 (PA, `recebimento_primeiro`; `rec_min < 0` em 1 linha), antes do fim oficial da votação. Não está comentado.

---

## 5. Mapas de desempenho contra a apuração

(a) **Mapa de vencedor, 27 UFs** (`fig-mapa_vencedor_2t`, fichas embutidas). Para cada UF comparei votos de Lula e Flávio da ficha, `presidente.json` (`ufs`) e a soma dos BUs em `voto_secao` (cargo 1, tipo 1, números 13 e 22). **27 de 27 idênticos, diferença zero voto**, vencedor e cor coerentes (Lula 13 UFs, Flávio 14). Seções por UF também batem; no exterior, `presidente.json` conta 1.351 seções e os BUs com voto de presidente são 1.308 (43 sem BU de presidente), com votos idênticos.

(b) **Mapa de swing** (`fig-tu_mapas_swing`, que cobre só SP, MG, BA, PE, PA e AM). Oito municípios conferidos contra a soma dos BUs e o 1º turno de `comparacao_1t.json`:

| Município | Página | BU 2T (F × L) | Fatia 2T | Swing refeito |
|---|---|---|---|---|
| São Paulo | 47,5 → 44,5 (−3,0) | 3.097.923 × 3.864.354 | 44,50 | −3,00 |
| Campinas | 57,7 → 54,2 (−3,4) | 360.222 × 303.914 | 54,24 | −3,44 |
| Belo Horizonte | 53,9 → 50,8 (−3,1) | 765.311 × 741.128 | 50,80 | −3,05 |
| Salvador | 29,3 → 26,8 (−2,5) | 421.752 × 1.154.072 | 26,76 | −2,53 |
| Recife | 41,0 → 38,7 (−2,2) | 400.342 × 633.369 | 38,73 | −2,24 |
| Belém | 47,7 → 45,0 (−2,7) | 383.457 × 468.891 | 44,99 | −2,69 |
| Manaus | 59,4 → 55,8 (−3,5) | 657.892 × 520.418 | 55,83 | −3,55 |
| Urucurituba (AM) | 24,3 → 22,4 (−2,0) | 2.156 × 7.486 | 22,36 | −1,96 |

Votos de BU iguais aos de `presidente.json` em todos. Nos 5.571 municípios, nenhuma diferença acima de 1 voto entre `presidente.json` e a soma dos BUs.

(c) **Total nacional.** Soma dos BUs: Lula 64.256.232, Flávio 59.826.041, 499.205 seções com voto de presidente. `presidente.json` (`nacional`): idêntico. Versão final do TSE informada: 64.256.232 × 59.826.041. **Divergência zero.**

Nota menor: a Bahia tem dois números de deslocamento na página, −1,44 pp no H3 (swing entre finalistas, `comparacao_1t.json`) e −1,56 pp no candidato 3 do capítulo de hipóteses ("urna contra repetição do 1º turno"), com país −2,80 e −2,82. São medidas diferentes com redação parecida.

---

## 6. Vídeo final contra a live

Referências: roteiro com 32 cenas (`video/apuracao_2t/roteiro/roteiro.md`), 635,3 s (`analysis/apuracao_2t_2026/video.json`). Live: 15 boletins que foram ao ar, 17:10 a 21:10, mais o 21:20 gerado e não exibido (`2120.meta.json`: `nao_foi_ao_ar`, 269,9 s) e o vídeo de encerramento da live, "Boletim final das vinte e uma e quarenta" (`apuracao/data/vinheta/encerramento.txt`, 239,6 s, os 3:59 que a página cita). Os 270 s do pedido são o 21:20, não o encerramento que foi ao ar.

**O vídeo cobre e a live não cobriu** (nenhuma ocorrência nos 16 boletins):
- Logs das urnas: cadência por hora (34.312 votos depois das 17h, 11 depois das 19h, 16,75% na primeira hora), 499.170 logs que fecham com o BU, 12.271 seções religadas com DiD −0,03.
- Metadados: série da memória de resultado repetida em 1.591 seções (exterior e Rio).
- Registro digital do voto: 499.205 de 499.205.
- Arquivos `.vsc`: cadeia e assinatura em 499.207.
- Transferência entre turnos (14,1 milhões disponíveis, 56 a 63 de cada 100 votos a mais para Lula, 32% da terceira via para Flávio).
- Pesquisas contra a urna: 20 casas, erro de 5,53 pp na diferença, sinal invertido em relação a 2022 e ao 1º turno; régua de renda afastando 9 de 11 casas; hipótese do autor (presença relativa 13,73% menor).
- Seção por seção: encerramento perto das 17h, atraso na transmissão, Candeias (+81,54 pp), comparecimento +5 pp em 46.241 seções, ranking das 100.
- Biometria: aparece no vídeo; na live, só o encerramento de 21:40 cita 287 seções de "habilitação sem biometria alta" numa amostra de 7.692.
- **Grupos (capítulo da anomalia, oito grupos de seções): não estão no vídeo nem na live.** O pedido lista grupos como coberto pelo vídeo; o roteiro não tem a palavra.

**A live cobriu e o vídeo deixou de fora:**
- Os seis 2º turnos estaduais (Acre, Amazonas, DF, Espírito Santo, Tocantins, Rio Grande do Norte): em todos os 16 boletins e no encerramento; zero no vídeo, embora o dossiê tenha capítulo próprio.
- Exterior: 13 boletins (ritmo, margem de quase 7 pontos para Lula, fechamento por último); zero no vídeo.
- Transporte e ônibus: 12 boletins (Salvador, SP, OEA, PF); o vídeo não menciona ônibus nem transporte, embora tenha sido o tema dominante do dia e a base do pedido de prorrogação.
- Ritmo de apuração por UF contra o 1º turno (DF, TO, RJ, SP atrasados) e a fila de UFs fechando.
- Brancos e nulos (1,12% e 2,12% contra 1,84% e 2,93% no 1º turno).
- Abstenção municipal atípica (Mazagão, AP: 14,5% para quase 30%); o vídeo cita só as UFs AP, RR e AC.
- Ocorrências do dia (boca de urna, presos, balanço do MJSP).
- O "não há virada possível" e a declaração de que a proclamação cabe ao TSE: o vídeo cita a frase dita no ar, mas não a conta dos votos restantes do encerramento ("faltam menos de 230 mil votos").

**Duração.** 635,3 s contra 269,9 s do 21:20 (2,35 vezes) e contra 239,6 s do encerramento (2,65 vezes).

---

## Lacunas

1. **Capítulo 9 e capítulo 8 trocam "encerramento do BU" por "último voto".** "Votaram depois das 19:00 0,90% das seções, 4.468" contradiz o log (10 seções com último voto depois das 19h, 11 votos) e o próprio H1. Corrigir o rótulo no gerador (`pagina_texto_secoes.py` e o bloco de hipóteses da abstenção) e o comentário da coluna `encerramento` no esquema do banco. Trocar "Na amostra de 497.897 seções" por "Nas 497.897 seções".
2. **Pianista sem voto na prosa.** Pôr no texto do bloco o número da célula: 1.324 seções, DiD +0,08 pp (ep 0,05), −2,50 contra vizinhas, ganho absoluto de Lula de 36.265 votos (0,82% da margem). Deixar claro que a tabela 2×2×2 é de "biometria baixa", não da célula do pianista.
3. **Contingência na célula do pianista.** 4,2% contra 1,15% no país; citar como explicação concorrente.
4. **Cruzar a célula do pianista com o log de habilitação por hora** (rajada de liberação por ano de nascimento perto do fechamento). É o passo que tira a célula de "compatível" sem depender de documento externo.
5. **Dois números de biometria para a mesma regra.** "Ano de nascimento alto: 18.393 seções, +0,34" e "sem cadastro alto: 12.593, −0,47" (vindos de `biometria.json`) convivem com 19.308/+0,31 e 13.228/−0,46 (`secoes_voto.json`), no mesmo capítulo. Unificar a régua ou dizer a diferença (mediana do município de cada turno).
6. **Abstenção contra 2022 por força de Lula.** Contra 2022, o quintil mais forte de Lula teve a maior queda (−3,12 pp) e o Nordeste lidera (−2,82). Publicar ao lado da régua do 1º turno, com a explicação de por que a régua certa para o deslocamento é o 1º turno.
7. **Bahia no H3.** Dizer que a Bahia teve a maior queda de abstenção do país (−3,26 pp; Salvador −4,37) e que Salvador volta ao nível de 2022 (−0,31). Unificar ou explicar −1,44 × −1,56.
8. **Virada por ordem de recebimento do BU.** O teste por seção (fatia de Flávio de 51,45% para 46,15% com swing estável de −2,6 a −3,1) é a prova mais direta de que a virada foi ordem de chegada; acrescentar ao capítulo 5.
9. **Canal de relato do Politize SE** não aparece como caminho para quem viu boca de urna ou pressão; e a conta de 13,3% de 618 ocorrências (≈ 82) pode ir explícita.
10. **Vídeo.** Sem governadores, exterior, transporte e grupos. Se houver nova edição ou descrição do YouTube, ao menos o transporte e os seis estados devem entrar na descrição.
11. Texto "entre 19:03 e 19:03 (RJ, SP)" e o BU recebido às 16:59 no PA, sem comentário.

## Conferido

- Célula do pianista: 1.324 seções, −2,50 pp contra vizinhas, DiD +0,08 (ep 0,05), refeitos das linhas por seção; efeito fixo de município independente dá +0,07 (ep 0,06).
- H3: comparecimento por região, Bahia −1,44 contra −2,80, 16h com 5,18% contra 8,95%, quintis da abstenção (−1,22 e −1,80; refeito −1,22 e −1,81).
- Decis de fechamento: 44,63% e 47,26%; swing −2,31 a −3,08.
- Votos depois das 17h: 34.323 de 127.818.872 (0,027%); 11 depois das 19h.
- 27 UFs do mapa de vencedor, 8 municípios do mapa de swing, 5.571 municípios e o total nacional: soma dos BUs idêntica a `presidente.json` e à versão final do TSE (64.256.232 × 59.826.041), diferença zero.
- Citação legal da boca de urna (Lei 9.504/1997, art. 39, § 5º) e o rótulo de que a totalização não mede a conduta.
- Roteiro do vídeo: 32 cenas; números checados batem com os JSONs (34.312 votos, 4.468 encerrados depois das 19h, 13.228 e 11.883 de biometria, 46.241 seções, DiD de reinício −0,03, 1.591 seções da série repetida, Norte separado por 1.079 votos, queda de Flávio nas 27 UFs, a menor PI −1,22). Não conferi os números da transferência (14,1 milhões, 26,4%) contra a base com exterior.
