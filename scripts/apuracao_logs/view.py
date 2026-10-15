"""Relatório e bloco comum das páginas, gerados da mesma análise de logs."""

from __future__ import annotations

import json
import re
from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo

from ga_tag import injetar

from . import painel
from .caso_santos import painel as caso_santos
from .coleta import ROOT
from .publicacao import PUBLICO

PAGINA = ROOT / "docs/logs_urnas_2026.html"
INICIO, FIM = "<!--LOGS-URNAS:INICIO-->", "<!--LOGS-URNAS:FIM-->"


def inteiro(v):
    return f"{v:,}".replace(",", ".")


def numero(v, casas=1):
    return f"{v:.{casas}f}".replace(".", ",") if v is not None else "não disponível"


def bloco(indice=None):
    path = PUBLICO / "indice.json"
    if indice is None and not path.exists():
        return ""
    d = indice or json.loads(path.read_text())
    c = d["cobertura"]
    n = len(d["criterios"])
    return f"""{INICIO}<div class="logs-fiscais" id="logs-urnas">
<link rel="stylesheet" href="assets/logs_fiscais_2026.css?v=2">
<p class="logs-kicker">Ampliação da fiscalização · 12 históricos + {n} dos logs</p>
<h3>Agora são {12+n} critérios de consulta.</h3>
<p>Os logs entram aqui com processo do mesário ao cômputo, cadência, identificação, interrupções e conferência dos arquivos.
<b>{inteiro(c["sinalizadas"])} seções</b> têm ao menos um dos {n} diagnósticos operacionais.
O mapa reúne as duas camadas, inclui o exterior e conta cada seção uma vez.</p>
<div class="logs-destaques">
<div><b>{inteiro(c["lidos"])}</b><span>logs de votação analisados</span></div>
<div><b>{numero(d["processo"]["brasil"]["media_s"])} s</b><span>processo observado médio no Brasil</span></div>
<div><b>{inteiro(d["criterios"]["contagem_divergente"]["secoes"])}</b><span>contagens ainda não reconciliadas com o BU</span></div>
</div>
<p class="logs-acoes"><a href="fiscais_mapa.html">Abrir todas as seções no mapa →</a>
<a href="logs_urnas_2026.html">Relatório visual dos logs →</a></p>
<p><b>O que muda na conferência:</b> votação lenta pede exame dos ciclos e da ata; taxa sem biometria alta pede comparação com o cadastro local;
reinício pede verificação da continuidade; discrepância com o BU pede conferência de todos os fragmentos.
Registro de bateria, sozinho, é uso de um recurso de continuidade.</p>
<h4>Os {n} critérios dos logs, com resultado e filtro direto</h4>
<p class="logs-legenda">Cada barra mostra a parcela das seções avaliáveis, em escala de 0 a {painel.teto_percentual(d)}%. As contagens se sobrepõem. Abra “Regra e conferência” para ver o corte e a providência correspondente.</p>
{painel.catalogo(d, compacto=True)}
<p class="logs-nota">A pontuação alta/média/baixa continua sendo a dos 12 critérios históricos. Os diagnósticos operacionais são consultáveis separadamente e não viram pontos de suspeita: bateria, recuperação e ausência de um fragmento têm significados diferentes.
Os 20 BUs antes indisponíveis foram recuperados e estão nas fichas suplementares; as tabelas e planilhas históricas abaixo preservam o recorte original.</p>
<p><a href="fiscais_mapa.html#modo=lista">Exportar a consulta combinada em CSV</a> ·
<a href="logs_urnas_2026.html#cobertura">Cobertura e lacunas</a> ·
<a href="politizesuavizinhanca.html">Consultar o log da minha seção</a></p>
</div>{FIM}"""


def tabela(cab, linhas):
    return (
        '<div class="rolagem" tabindex="0"><table><thead><tr>'
        + "".join(f'<th scope="col">{escape(x)}</th>' for x in cab)
        + "</tr></thead><tbody>"
        + "".join(
            "<tr>" + "".join(f"<td>{x}</td>" for x in ln) + "</tr>" for ln in linhas
        )
        + "</tbody></table></div>"
    )


def pagina(d):
    n = len(d["criterios"])
    c = d["cobertura"]
    op = d["operacao"]
    casos = "".join(
        f'<details class="caso"><summary>{escape(r["titulo"])} · {r["uf"]}, zona {r["zona"]}, seção {r["secao"]}</summary>'
        f'<p>{escape(r["leitura"])}</p><p class="nota">{escape(r["limite"])}</p>'
        f'<p><a href="{escape(r["url"])}">Log original</a> · <a href="politizesuavizinhanca.html#s={r["uf"]}-{r["zona"]}-{r["secao"]}">Ficha da seção</a></p>'
        f'<p class="arquivo-hash">SHA-256: <code>{r["sha256"]}</code></p></details>'
        for r in d.get("casos_conferidos", [])
    )
    pct = 100 * c["lidos"] / c["catalogadas"]
    data_publicacao = (
        datetime.fromisoformat(d["gerado_em"])
        .astimezone(ZoneInfo("America/Sao_Paulo"))
        .strftime("%d/%m/%Y às %H:%M (Brasília)")
    )
    lacunas = ""
    if d.get("lacunas"):
        consulta = d["lacunas"]
        estados = consulta["status_anterior"]
        lacunas = (
            f'<p>Reconsultamos os metadados das {inteiro(consulta["secoes"])} seções sem nome de log no catálogo antigo. '
            f'{inteiro(estados.get("Nao instalada", 0))} estavam marcadas como não instaladas; '
            f'{inteiro(estados.get("Totalizada", 0) + estados.get("Recebida", 0))} tinham boletins do sistema de apuração, sem log de votação (VOTA) no hash arquivado. Os metadados desses casos listam logSA, uma categoria distinta, não processada neste leitor; o endereço está na ficha da seção. '
            f'As {inteiro(estados.get("aux_404", 0))} que antes retornavam 404 agora têm BU e log: '
            f'{inteiro(d["complementos"]["lidos"])} já estão incluídas nesta análise, com BU suplementar e fonte na ficha. '
            'O banco histórico foi preservado. <a href="assets/logs_urnas_2026/lacunas.json">Respostas, endereços e hashes da reconsulta</a>.</p>'
        )
    situacoes = tabela(
        ["Situação", "Seções"],
        [[v["nome"], inteiro(v["secoes"])] for v in d["situacoes"].values()],
    )
    tabela_uf = tabela(
        [
            "UF",
            "Catalogadas",
            "Logs lidos",
            "Contagem confere",
            "Biometria confere",
            "Tempo elegível",
        ],
        [
            [
                u if u != "ZZ" else "Exterior",
                *[
                    inteiro(r.get(k, 0))
                    for k in (
                        "catalogadas",
                        "lidos",
                        "contagem_confere",
                        "biometria_confere",
                        "tempo_elegivel",
                    )
                ],
            ]
            for u, r in d["por_uf"].items()
        ],
    )
    tempos_cargos = tabela(
        ["Território", "Confirmações de cargo", "Ciclos", "Média (segundos)"],
        [
            [
                "Brasil" if pais == "brasil" else "Exterior",
                escape(k),
                inteiro(v["ciclos"]),
                numero(v["media_s"]),
            ]
            for pais, r in d["tempos"].items()
            for k, v in r["por_cargos"].items()
        ],
    )
    tabela_bio = tabela(
        [
            "Território",
            "Seções reconciliadas",
            "Biométricas",
            "Biográficas",
            "Sem biometria",
        ],
        [
            [
                "Brasil" if pais == "brasil" else "Exterior",
                *[
                    inteiro(r[k])
                    for k in ("secoes", "biometricas", "biograficas", "sem_biometria")
                ],
            ]
            for pais, r in d["biometria"].items()
        ],
    )
    sensibilidade = tabela(
        [
            "Escalas robustas",
            "Seções com algum diagnóstico",
            "Processo rápido",
            "Cadência rápida",
            "Trecho rápido",
            "Retomadas acima da referência",
        ],
        [
            [
                k,
                inteiro(v["secoes"]),
                inteiro(v["criterios"].get("processo_rapido", 0)),
                inteiro(v["criterios"].get("cadencia_rapida", 0)),
                inteiro(v["criterios"].get("rajada_rapida", 0)),
                inteiro(v["criterios"].get("retomadas_inatividade", 0)),
            ]
            for k, v in d["sensibilidade"].items()
        ],
    )
    return injetar(
        f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Logs das urnas: tempos, biometria e ocorrências | Arvor</title>
<meta name="description" content="Análise reproduzível dos logs oficiais do primeiro turno de 2026: tempos, biometria e {n} diagnósticos operacionais, com cobertura e conferência contra o BU.">
<meta property="og:type" content="article"><meta property="og:locale" content="pt_BR">
<meta property="og:title" content="Logs das urnas: tempos, biometria e {n} diagnósticos">
<meta property="og:description" content="O ritmo da votação e o registro de cada urna, com cobertura, reconciliação com o BU e limites de interpretação.">
<meta property="og:url" content="https://brasil.arvor.co/logs_urnas_2026.html">
<meta property="og:image" content="https://brasil.arvor.co/img/og/logs_urnas_2026.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="https://brasil.arvor.co/logs_urnas_2026.html">
<link rel="icon" href="img/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/logs_urnas_2026.css?v=3">
<script defer src="assets/logs_urnas_2026.js?v=2"></script>
</head><body>
<header><nav class="nav-topo"><a href="index.html">ARVOR / DADOS ABERTOS</a><a href="fiscais_mapa.html">Mapa de fiscais ↗</a><a href="politizesuavizinhanca.html">Minha seção ↗</a></nav>
<div class="hero"><div><p class="etiqueta">Primeiro turno de 2026 · Logs oficiais das urnas</p>
<h1>O que aconteceu<br><em>durante a votação.</em></h1>
<p class="abertura">Quanto dura o processo do mesário ao cômputo, como varia a cadência entre atendimentos e quais ocorrências ficaram registradas. A leitura de quase meio milhão de logs, em gráficos e critérios verificáveis.</p>
<a class="botao" href="#criterios">Explorar os {n} diagnósticos ↓</a></div>
<aside class="hero-base"><span>Base analisada</span><strong>{inteiro(c["lidos"])}</strong><span>logs de votação ligados ao boletim da seção</span>
<div class="hero-cobertura"><i style="width:{pct:.6f}%"></i></div><p><b>{f'{pct:.3f}'.replace('.', ',')}%</b> das {inteiro(c["catalogadas"])} seções catalogadas</p>
<p class="base">Leitura de {escape(data_publicacao)}. <a href="#cobertura">Entenda as {inteiro(c["catalogadas"]-c["lidos"])} seções restantes →</a></p></aside></div>
<div class="manchetes"><a href="#leitura"><b>{numero(d["processo"]["brasil"]["media_s"])} s</b><span>média do processo observado no Brasil</span></a>
<a href="#criterios"><b>{inteiro(c["sinalizadas"])}</b><span>seções com algum diagnóstico operacional</span></a>
<a href="#achados"><b>{inteiro(c["lidos"]-c["contagem_confere"])}</b><span>contagens ainda não reconciliadas com o BU</span></a></div>
</header>
<nav class="nav-capitulos" aria-label="Neste relatório"><a href="#leitura">01 · Tempos</a><a href="#biometria">02 · Biometria</a><a href="#criterios">03 · Critérios</a><a href="#achados">04 · Conferências</a><a href="#cobertura">05 · Cobertura</a><a href="#fontes">Fontes</a></nav>
<main>
<section id="leitura"><p class="etiqueta">01 / Ritmo da votação</p><h2>Do identificador ao cômputo.<br>Metade dos processos durou até {numero(d["processo"]["brasil"]["mediana_s"], 0)} segundos.</h2>
<p class="lead">A medida principal começa na digitação concluída do identificador pelo mesário e termina no voto computado. Inclui a identificação eletrônica e a votação. Conferência de documentos, fila e digitação anterior ao registro não têm início cronometrável neste log.</p>
<div class="fluxo-processo" aria-label="Etapas medidas"><div><b>01</b><strong>Identificador digitado</strong><span>Primeiro marco do processo observado</span></div><div><b>02</b><strong>Eleitor habilitado</strong><span>Fim da identificação eletrônica</span></div><div><b>03</b><strong>Voto computado</strong><span>Fim do processo observado</span></div></div>
{painel.tempos(d, "processo")}
<p class="legenda-reguas">Régua comum em segundos: ● metade dos ciclos (mediana) · | média · ○ 90% dos ciclos (percentil 90).</p>
<p class="nota">Brasil e exterior são descritos separadamente: o número de cargos difere. Nas regras de atipicidade, a comparação é com a mesma UF, modelo de urna e quantidade de confirmações de cargo.</p>
<figure class="distribuicao"><div class="fig-titulo"><h3>Como os tempos se distribuem</h3><a href="assets/logs_urnas_2026/processo.png">Baixar gráfico ↗</a></div><picture><source media="(max-width:700px)" srcset="assets/logs_urnas_2026/processo-mobile.svg"><img src="assets/logs_urnas_2026/processo.svg" width="1040" height="700" alt="Distribuição dos tempos do processo observado, em faixas de dez segundos, separada entre Brasil e exterior."></picture><figcaption>Parcela dos processos elegíveis em cada faixa de dez segundos. A última barra reúne todos os processos de 300 segundos ou mais. As duas distribuições usam a mesma escala vertical.</figcaption></figure>
<div class="conclusao"><b>Três leituras de rapidez, com bases distintas.</b><p>{inteiro(d["criterios"]["processo_rapido"]["secoes"])} seções no processo por tipo; {inteiro(d["criterios"]["cadencia_rapida"]["secoes"])} na cadência; {inteiro(d["criterios"]["rajada_rapida"]["secoes"])} em trechos de dez intervalos. Contagens se sobrepõem. {painel.mapa_link('processo_rapido', 'Conferir o processo rápido')}</p></div>
<h3>Cadência: o que cabe entre dois cômputos</h3><p>A cadência inclui o processo seguinte, a transição entre pessoas e eventuais esperas. Não é duração individual. Comparamos apenas cômputos consecutivos completos da mesma urna e sessão, sem atravessar reinícios ou ciclos não reconstruídos.</p>
{painel.tempos(d, "cadencia")}
<details class="metodo"><summary>Ver a distribuição dos intervalos entre cômputos</summary><figure class="distribuicao"><picture><source media="(max-width:700px)" srcset="assets/logs_urnas_2026/cadencia-mobile.svg"><img src="assets/logs_urnas_2026/cadencia.svg" width="1040" height="700" alt="Distribuição dos intervalos entre cômputos consecutivos, em faixas de dez segundos, separada entre Brasil e exterior."></picture><figcaption>Mesma escala para Brasil e exterior. A última barra reúne intervalos de 300 segundos ou mais, que podem conter espera e ociosidade. <a href="assets/logs_urnas_2026/cadencia.png">Baixar gráfico</a>.</figcaption></figure></details>
<details class="metodo"><summary>Etapa após habilitação: a medida anterior continua disponível</summary><p>É uma parte do processo, insuficiente sozinha para medir o atendimento do mesário. Não se somam medianas das etapas para obter a mediana do processo: cada duração completa é reconstruída diretamente.</p>{painel.tempos(d)}<p>{painel.mapa_link('tempo_rapido', 'Consultar a regra anterior de votação rápida')}</p></details>
<details class="metodo"><summary>Como separamos habilitação, votação e intervalo</summary><div class="passos"><article><h3>Habilitação</h3><p>Do identificador digitado pelo mesário à liberação do eleitor. É a etapa eletrônica observável, sem toda a conferência documental.</p></article><article><h3>Votação</h3><p>Da habilitação ao voto computado. Ciclos parcialmente suspensos ficam fora da duração de voto completo.</p></article><article><h3>Cadência</h3><p>Entre dois cômputos consecutivos da mesma urna e sessão. Inclui ociosidade, identificação e votação. Não identifica fila nem paralisação.</p></article></div>
{tempos_cargos}<p>Relógio inconsistente, modelos mistos ou divergentes e ciclos incompletos impedem a comparação correspondente. Os valores descrevem os ciclos completos elegíveis nas seções lidas. Não há associação entre horário, identidade pessoal e opção de voto.</p></details></section>
<section id="biometria"><p class="etiqueta">02 / Identificação do eleitor</p><h2>Três formas de habilitar.<br>Duas taxas diferentes para comparar.</h2>
<p class="lead">A habilitação biográfica e a categoria “sem biometria” são contagens distintas do BU. Misturá-las produziria uma taxa enganosa.</p>
{painel.biometria(d)}
<div class="dois-achados"><article><span>Habilitação biográfica acima da referência</span><b>{inteiro(d["criterios"]["biografica_alta"]["secoes"])}</b><p>seções. A taxa divide biográficas por <strong>biométricas + biográficas</strong>.</p>{painel.mapa_link('biografica_alta')}</article>
<article><span>Sem biometria acima da referência</span><b>{inteiro(d["criterios"]["sem_biometria_alta"]["secoes"])}</b><p>seções. A taxa divide a categoria sem biometria pelo <strong>comparecimento</strong>.</p>{painel.mapa_link('sem_biometria_alta')}</article></div>
<p class="nota">Os percentuais do gráfico usam todos os presentes nas seções reconciliadas; as regras acima usam seus próprios denominadores. Procedimento sem reconhecimento biométrico não identifica, por si só, voto irregular.</p>
<details class="metodo"><summary>Referência local, denominadores e cobertura da biometria</summary>
<p>A referência é a mediana de seções da mesma UF, município, zona e modelo, com pelo menos 30 seções elegíveis e denominador de 50 pessoas por seção. O corte exige quatro escalas robustas e excesso de pelo menos 10 pontos percentuais. Cadastro, idade e qualidade das digitais não são controlados individualmente.</p>{tabela_bio}
<p>A decomposição acima só inclui as seções em que as três categorias e o comparecimento fecharam entre log e BU. {inteiro(c["biometria_ausente_bu"])} BUs não trazem os campos de biometria: seus valores são desconhecidos, nunca zero.</p></details></section>
<section id="criterios"><p class="etiqueta">03 / 12 critérios históricos + {n} dos logs</p><h2>O que procurar.<br>Quantas seções aparecem.</h2>
<p class="lead">Escolha um grupo, veja a frequência e abra a regra. Cada diagnóstico leva diretamente às seções correspondentes no mapa.</p>
<div class="conclusao"><b>O registro mais frequente é operação com bateria.</b><p>{inteiro(d["criterios"]["bateria"]["secoes"])} seções registraram esse recurso de continuidade. Isso ajuda a explicar o volume de registros operacionais; não mede defeitos nem gravidade. As contagens se sobrepõem e não se somam à pontuação histórica.</p></div>
{painel.navegacao_criterios(d)}
<p class="legenda-reguas">Barras em escala comum de 0 a {painel.teto_percentual(d)}% das seções avaliáveis em cada regra. Ocorrências raras continuam legíveis pelo número; barra curta não significa pouca importância.</p>
{painel.catalogo(d)}
<p class="sem-resultados" hidden>Nenhum diagnóstico corresponde à busca. Limpe o texto ou escolha outro grupo.</p>
<p class="nota">Essas {n} regras são triagem exploratória. Não estimam probabilidade de fraude. ALERTA não é contado como ERRO: pode ser uma pergunta do sistema ou digitação inválida.</p>
<details class="metodo"><summary>Como a nova triagem de rapidez evita misturar processos diferentes</summary><p>O processo observado exige início inequívoco em pelo menos 90% dos ciclos completos, com no mínimo 30 processos. Cada tipo de habilitação é comparado separadamente (biométrica, biográfica ou sem biometria), com ≥30 processos por tipo e ≥30 seções da mesma UF, modelo e cargos. Categorias não reconciliadas com o BU não alimentam essa comparação.</p><p>A cadência usa ≥30 intervalos. O trecho rápido procura dez intervalos consecutivos (onze cômputos) e compara seu mínimo com mínimos de pares também agrupados por volume: 0–99, 100–199, 200–299, 300–399, 400–499 e 500+ intervalos. Também exige menos da metade da mediana da própria seção. Identificação repetida ou cancelada não recebe início presumido. Uma tentativa encerrada e outra iniciada depois não são atribuídas à mesma pessoa; a cadência preserva o tempo entre cômputos que pode conter essas tentativas. Essas proteções reduzem artefatos; não controlam idade, acessibilidade, movimento ou toda diferença de operação.</p></details>
<details class="metodo" id="sensibilidade"><summary>Quanto muda quando o corte fica mais ou menos exigente?</summary><p>O corte principal usa a mediana de referência mais ou menos quatro escalas robustas e uma diferença mínima. As alternativas usam três e cinco. Escala robusta: 1,4826 vezes a mediana dos desvios absolutos, com piso de três segundos, um ponto percentual na biometria ou um evento por 100 cômputos nas retomadas e cancelamentos. A própria seção participa da referência.</p>{sensibilidade}<p>As colunas usam a mesma cobertura. São sensibilidades de triagem, sem nível de significância nem confirmações independentes.</p></details></section>
<section id="achados"><p class="etiqueta">04 / Conferência dos registros</p><h2>Erro registrado não conta<br>a história inteira.</h2>
<p class="lead">Em {inteiro(c["contagem_confere"])} seções, a contagem reproduz o comparecimento do BU. Restam {inteiro(c["lidos"]-c["contagem_confere"])} discrepâncias documentais ou de reconstrução para conferir. Elas não demonstram alteração de votos.</p>
{caso_santos(d)}
{painel.assinatura(d)}
<p>Os {inteiro(op.get("falhas_assinatura_declaradas", 0))} eventos estão em {inteiro(d["criterios"]["assinatura"]["secoes"])} seções. SUCESSO posterior significa que o software registrou recuperação para o mesmo arquivo e urna. Esta análise lê as mensagens; não substitui a validação criptográfica independente.</p>
<details class="metodo"><summary>Erros dentro e fora da janela observada de votação</summary><p>Há {inteiro(op.get("erros", 0))} eventos ERRO/FATAL no dia. Nas {inteiro(op.get("secoes_janela_classificavel", 0))} seções com janela delimitável, {inteiro(op.get("erros_na_janela_votacao", 0))} ocorreram entre a primeira habilitação e o último cômputo e {inteiro(op.get("erros_fora_da_janela", 0))} fora desse intervalo. Um evento não equivale a uma seção ou a uma falha sem recuperação.</p></details>
<h3>Casos lidos no arquivo original</h3><p>Exemplos escolhidos para mostrar situações distintas, sem ranking de gravidade. Cada ficha liga a interpretação ao original e ao hash arquivado.</p>{casos}</section>
<section id="cobertura"><p class="etiqueta">05 / Cobertura e limites</p><h2>O que entrou na análise.<br>O que ficou de fora.</h2>
{painel.cobertura(d)}
<p class="nota">Cada linha representa uma condição própria, não etapas cumulativas. Uma seção pode servir para contagem e ficar fora da comparação de tempos ou de biometria.</p>
<div class="conclusao"><b>As {inteiro(c["catalogadas"]-c["lidos"])} seções sem log de votação analisado</b><p>{inteiro(d["situacoes"]["nao_instalada"]["secoes"])} não instaladas e {inteiro(d["situacoes"]["apuracao_sem_log"]["secoes"])} com boletim do sistema de apuração. Estas últimas têm registros logSA, de outra categoria, que não passam por este leitor de ciclos VOTA. Os links estão nas fichas. Ausência de análise não significa zero ocorrências.</p></div>
<details class="metodo"><summary>Recuperação de arquivos, situações e cobertura por UF</summary>{lacunas}
<p>Recuperados: {inteiro(d["coleta"].get("ok", 0))}; SHA-256 igual ao da coleta anterior: {inteiro(d["coleta"].get("hash_anterior_confere", 0))}. Sem hash anterior, a comparação fica desconhecida. Publicação em {escape(data_publicacao)}.</p>{situacoes}{tabela_uf}</details></section>
<section id="fontes"><h2>Do original à conferência</h2>
<ol><li>O arquivo de cada seção vem do mesmo endereço e hash de transmissão associado ao BU arquivado. Seu SHA-256 é comparado ao preservado na coleta anterior quando ele existe. A ausência de hash anterior fica explícita; não é uma comparação aprovada.</li><li>O leitor abre o ZIP e os arquivos aninhados de contingência sem extrair em disco. Lê Latin-1, retém os dias 4 e 5 de outubro, confere seção e fase oficial e remove apenas linhas integralmente duplicadas entre arquivos. Fragmentos arquivados antes da eleição, com ajuste explícito e último registro também anterior, são separados mesmo quando o relógio adiantado carimbou 04/10; a regra não exclui fragmentos com cômputos datados da eleição.</li><li>Recuos de relógio são medidos antes de ordenar os fragmentos e invalidam as durações. Ciclos incompletos e categorias desconhecidas ficam explícitos.</li><li>A contagem de cômputos e as três formas de habilitação são comparadas ao BU. Um hash conferido prova identidade dos bytes arquivados; não substitui a validação criptográfica da assinatura eleitoral.</li></ol>
<p><a href="https://www.tse.jus.br/eleicoes/eleicoes-2026">TSE: documentos técnicos das Eleições 2026</a> · <a href="https://dadosabertos.tse.jus.br/dataset/resultados-2026-arquivos-transmitidos-para-totalizacao">TSE: arquivos transmitidos para totalização</a>. O link do arquivo original e o SHA-256 de cada seção estão na ficha do Politize e no CSV.</p>
<p><a href="assets/logs_urnas_2026/secoes.csv.gz">Baixar todas as seções analisadas, CSV comprimido</a> · <a href="assets/logs_urnas_2026/processos_por_tipo.csv.gz">Processos por tipo e referências, CSV comprimido</a> · <a href="assets/logs_urnas_2026/indice.json">Resumo, regras e cobertura em JSON</a> · <a href="https://github.com/ArvorCo/PNAD/tree/main/scripts/apuracao_logs">Código do leitor e das regras</a>.</p>
<details><summary>Reproduzir</summary><pre>python3 scripts/apuracao-2026-logs-coletar.py
python3 scripts/apuracao-2026-logs-lacunas.py
python3 scripts/apuracao-2026-logs-lacunas.py --preparar-bus
python3 scripts/apuracao-2026-logs-lacunas.py --aplicar
python3 scripts/apuracao-2026-logs-coletar.py
python3 scripts/apuracao-2026-logs-processar.py
python3 scripts/apuracao-2026-logs-build.py
python3 scripts/fiscais-mapa-build.py</pre><p>Requer o banco histórico local <code>apuracao/data/secoes_2026.sqlite</code> e as dependências do projeto. A aplicação dos complementos ocorre com o coletor parado. Versão do leitor: {escape(d["versao_parser"])}. Os originais pesados permanecem no acervo local; os agregados e os endereços oficiais são públicos. <a href="https://github.com/ArvorCo/PNAD/blob/main/analysis/apuracao_2026/logs_urnas/CONTRATO.md">Contrato completo de reprodução</a>.</p></details>
</section></main><footer><a href="apuracao_1o_turno_2026.html#fiscais">Voltar ao dossiê da apuração</a> · <a href="fiscais_mapa.html">Mapa de fiscais</a> · Arvor</footer></body></html>"""
    )


def atualizar_paginas(d):
    PAGINA.write_text(pagina(d), encoding="utf-8")
    novo = bloco(d)
    for nome in ("apuracao_1o_turno_2026.html", "fiscais_thread.html"):
        path = ROOT / "docs" / nome
        texto = path.read_text(encoding="utf-8")
        texto = re.sub(
            re.escape(INICIO) + r".*?" + re.escape(FIM), "", texto, flags=re.DOTALL
        )
        if nome.startswith("apuracao"):
            ini = texto.index('id="fiscais"')
            fim = texto.index("</section>", ini)
            cap = texto[ini:fim]
            cap = re.sub(
                r'(<p class="lead">).*?(</p>)',
                rf"\g<1>{12+len(d['criterios'])} critérios para conferir: 12 do histórico e {len(d['criterios'])} dos logs de votação. "
                r"Brasil e exterior na mesma consulta, com contagens, regras e fontes por seção.\g<2>",
                cap,
                count=1,
                flags=re.DOTALL,
            )
            pos = cap.index("</div>") + len("</div>")
            historico = (
                '<h3 id="fiscais-historico">O núcleo histórico: 12 critérios</h3>'
            )
            cap = cap.replace(historico, "")
            cap = cap[:pos] + novo + historico + cap[pos:]
            cap = cap.replace(
                "<h3>Os critérios</h3>",
                "<h3>Como funcionam os 12 critérios históricos</h3>",
            )
            cap = cap.replace(
                "Baixar Excel (lista completa)",
                "Baixar Excel (12 critérios históricos)",
            )
            cap = cap.replace("<b>Baixe a lista</b>", "<b>Baixe a lista histórica</b>")
            texto = texto[:ini] + cap + texto[fim:]
        else:
            texto = texto.replace(
                '<main class="wrap">', '<main class="wrap">' + novo, 1
            )
            texto = texto.replace(
                "<h2>Baixar a lista</h2>",
                "<h2>Baixar a lista histórica (12 critérios)</h2>",
            )
        texto = texto.replace('<footer class="wrap">\n  \n', '<footer class="wrap">\n')
        path.write_text(texto, encoding="utf-8")
