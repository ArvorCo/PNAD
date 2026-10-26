# Dossiê da apuração do 2º turno (`docs/apuracao_2T_2026.html`): contrato

Gerado por `python3 scripts/apuracao-2t-2026-build.py` (módulos em `scripts/apuracao_2t_2026/pagina_*.py`) a partir dos JSONs de `analysis/apuracao_2t_2026/dados/` e dos memorandos `.md` da mesma pasta. Nunca editar o HTML gerado. Reaproveita por import o que serve do 1º turno (`scripts/apuracao_2026/pagina_comum.py`, `pagina_css.py`, `pagina_fig_base.py`, `pagina_mapas.py`, `pagina_view.py`), sem editar os módulos do 1T. Paleta, fontes e regras de texto: `analysis/apuracao_2026/BRIEF.md` e o CLAUDE.md (sem travessão; "pede explicação, não prova irregularidade"; "soma dos BUs recebidos, não projeção"; nunca "fraude").

Tom editorial (decisão do Leonardo, 25/10): crítico com tudo, sem afirmar o que o dado não prova; o dossiê não celebra o resultado, celebra o método: a projeção da casa apontou Lula desde o primeiro ponto da noite, a totalização paralela conferiu 177 BUs sem divergência, o coletor documentou a parada do TSE e a prorrogação. Cada capítulo abre pelo número mais forte e publica o achado que contraria a própria tese.

## Capítulos (ordem na página)

| nº | id | título | JSON/memo de origem | figuras |
|---|---|---|---|---|
| 1 | `abertura` | O resultado | `presidente.json` | mapa UF por vencedor e margem; barras BR; cards (seções, votos, comparecimento, abstenção) |
| 2 | `noite` | A noite minuto a minuto | `linha_do_tempo.json` | votos acumulados por candidato; lotes por versão; marcas STF 17:0x e parada 17:07–19:01; pausas AM/RR; mapa da hora em que cada UF fechou; régua do 1T sobreposta |
| 3 | `projecao` | A projeção da casa durante a noite | `projecao_noite.json` | projetado × observado com faixa; o primeiro ponto (19:14) |
| 4 | `boletins` | Os boletins da noite | `docs/assets/apuracao_2t/boletins/*.mp3,.txt` | um player por boletim (17:10 a 21:20) com placar do momento e texto em `<details>` |
| 5 | `cedo_tarde` | O que entrou cedo e o que entrou tarde | `cedo_tarde.json` | decis de tempo de fechamento × fatia; os 50 últimos municípios; comparação com o 1T |
| 6 | `turnos` | 1º turno × 2º turno | `comparacao_1t.json`, `comparacao_2022.json` | barras divergentes por UF; dispersão municipal; mapa municipal do swing; lista onde Flávio ganhou votos absolutos |
| 6b | `transferencia` | De onde veio o voto: 1º turno → 2º turno | `transferencia.json`, `transferencia.md` | ordem fixa: conta das urnas, três números, quatro cenários de cruzamento entre as bases (sem, 1%, 2%, o que as pesquisas mediram; botões, padrão sem cruzamento sem script) com Sankey de nove origens e quatro destinos, rótulo na fita acima de 0,5 mi, lista das fitas finas, barras empilhadas abaixo de 720 px e tabela de cada 100; regressão da abstenção (dispersão municipal, barras por UF); limites |
| 7 | `abstencao` | A abstenção mais baixa | `abstencao.json` | ranking UF; mapa municipal; histograma; capitais × interior; 1T e 2022 |
| 8 | `secoes` | Seção por seção: comparecimento, biometria, horários | `secoes.json`, `secoes_voto.json`, `secoes_ranking.json`, `secoes.md` | mapa de pontos das seções com sinal; 2×2×2; encerramento real (p50 17:0x); ranking das 100 |
| 8b | `logs` | O que os logs das 499 mil urnas dizem | `logs.json`, `logs.md`, `analysis/apuracao_2t_2026/logs_urnas/*`, `metadados.json` | cadência horária 1T × 2T, matriz de atenção, diagnósticos pareados, reinícios × voto, bateria × chuva, MR repetida, escore integrado com mapa de pontos |
| 9 | `exterior` | Exterior | `exterior.json` | mapa-múndi com bolhas; barras por continente |
| 10 | `governadores` | Seis governadores | `governadores.json` | placar por UF com viradas; vão contra o presidencial |
| 11 | `pesquisas` | Pesquisas × urna e a hipótese do autor | `pesquisas_vs_urna.json`, `projecao_pre_urna.json`, `pesquisas.md`, tweet do Leonardo | pontos por casa contra a urna; mapa UF da projeção pré-urna × urna; bloco "hipótese" rotulado como juízo editorial |
| 12 | `paralela` | Totalização paralela | `paralela.json` | cobertura por UF; conferência; QR |
| 13 | `noticias` | O dia nas fontes | `noticias_noite.json` | cronologia com veículo, hora e tipo de evidência |
| 14 | `auditoria` | O acompanhamento, auditado | `linha_do_tempo.json` (latência), `apuracao/README.md` | live do YouTube embutida; vinhetas; limites |
| 15 | `video` | O vídeo da apuração | YouTube (id a definir) | iframe + roteiro em `<details>` |
| 16 | `fontes` | Fontes e reprodução | todos | lista de scripts, JSONs, hashes, data de geração |

## Donos de arquivos

| pacote | escreve em |
|---|---|
| datasets | `scripts/apuracao-2t-2026-dados.py`, `scripts/apuracao_2t_2026/{banco,dados,...}.py`, `dados/{presidente,linha_do_tempo,cedo_tarde,comparacao_1t,comparacao_2022,abstencao,exterior,governadores,projecao_noite,paralela}.json`, `dados/resumo.md` |
| seções | `scripts/apuracao-2t-2026-secoes.py`, `scripts/apuracao_2t_2026/secoes_*.py`, `dados/secoes*.json`, `dados/secoes.md` |
| pesquisas | `scripts/apuracao-2t-2026-pesquisas.py`, `scripts/apuracao_2t_2026/pesquisas_*.py`, `dados/pesquisas*.json`, `dados/projecao_pre_urna.json`, `dados/pesquisas.md` |
| notícias | `analysis/apuracao_2t_2026/noticias_noite.{json,md}`, `noticias_fontes/` |
| página | `scripts/apuracao-2t-2026-build.py`, `scripts/apuracao_2t_2026/pagina_*.py`, `docs/apuracao_2T_2026.html`, `tests/test_apuracao_2t_2026_build.py` |
| thread | `scripts/apuracao-2t-2026-thread.py`, `scripts/apuracao_2t_2026/thread_*.py`, `docs/apuracao_2T_2026_thread.html` |
| vídeo | `video/apuracao_2t/` (clone generalizado de `video/masterclass/`), `scripts/video-apuracao-2t-*.py` |

## Entregáveis finais
- Página sem travessão (`grep -c "—"` zero), GA pelo `ga_tag.injetar`, metatags OG com card `docs/img/og/apuracao_2T_2026.png` (manifesto de `scripts/social-cards.py`), link na `docs/index.html` no topo, sitemap regenerado.
- Auditorias `contrast-audit.py` e `render-audit.py` zeradas; celular sem rolagem lateral; figuras pesadas em `<noscript class="fig-src">` como no 1T.
- `pytest -q` verde; `ruff` e `black` zerados.

## Interface dos capítulos (fixada em 25/10, 22h40)

- `scripts/apuracao_2t_2026/pagina_comum.py` (dono: esqueleto) reexporta tudo de `scripts/apuracao_2026/pagina_comum.py` (cores, `num`, `inteiro`, `sinal`, `hora`, `Dados`, `Capitulo`, `montar`, `pendente`, `checar`, `caminho`) e redefine `DADOS = ROOT / "analysis/apuracao_2t_2026/dados"`, `MEMOS = ROOT / "analysis/apuracao_2t_2026"`, `SLUG = "apuracao_2T_2026"`, `URL`.
- Cada capítulo é um módulo `scripts/apuracao_2t_2026/pagina_cap_<ident>.py` com a função `render(d: Dados, cap: Capitulo) -> str` que devolve o HTML interno do capítulo (sem o `<section>`, que o esqueleto envolve). Figuras e textos do capítulo ficam em módulos auxiliares do mesmo dono (`pagina_fig_<ident>*.py`, `pagina_texto_<ident>*.py`), sempre abaixo de 1.000 linhas.
- `pagina_view.py` (esqueleto) registra `(ident, curto, titulo, arquivos)` dos 16 capítulos e importa cada `pagina_cap_<ident>` por `importlib`; módulo ausente ou exceção vira bloco "capítulo em preparação" com o motivo, e o build nunca derruba.
- Ferramentas compartilhadas (só leitura, importar do 1T): `scripts/apuracao_2026/pagina_fig_base.py` (`figura_html`, `svg_abre`, `t`, `chip`, `r`, `ln`, `escala`, `ticks`, `legenda_html`, `larga_estreita`, `registra`), `pagina_mapas.py` (`mapa_uf`, `mapa_municipal`, `pontos_brasil`, `mapa_mundo`, `cor_swing`, `cor_vencedor`), `pagina_css.py`, `pagina_interativo.py`. Quem precisar de uma peça nova escreve no próprio módulo.
- Figura pesada (acima de 150 KB) vai em `<noscript class="fig-src">` como no 1T (ver `pagina_fig_base.figura_html` e `pagina_interativo`).
- Identificadores dos capítulos: `abertura`, `noite`, `projecao`, `boletins`, `cedo_tarde`, `turnos`, `transferencia`, `abstencao`, `secoes`, `logs`, `exterior`, `governadores`, `pesquisas`, `paralela`, `noticias`, `auditoria`, `video`, `fontes`.
- Áudio dos boletins: `docs/assets/apuracao_2t/boletins/<HHMM>.mp3` com `<HHMM>.txt` (roteiro) e `.meta.json` (resumo, duração); o capítulo `boletins` usa `<audio controls preload="none">`, nunca autoplay.

## Bloco "Como o eleitor foi habilitado" (26/10, tarde)
No capítulo `secoes`, antes dos sinais: `scripts/apuracao-2t-2026-biometria.py` (módulos `biometria_*.py`) grava `dados/biometria.json` e `biometria.md` a partir dos dois bancos de BUs e, para o exterior, dos logs (`tipos_habilitacao_computados`). Três situações no Brasil (biometria reconhecida; ano de nascimento = cadastro não reconhecido; sem cadastro) e o exterior sem conferência biométrica. Achado: a parcela por ano de nascimento depende do modelo da urna (UE2013 10,84%, UE2015 9,60%, UE2020 6,02%, UE2022 5,99%; +3,39 pp da antiga sobre a nova dentro do município), hipótese de leitor antigo a confirmar no log.
