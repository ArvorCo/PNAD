"""Relatório e bloco comum das páginas, gerados da mesma análise de logs."""

from __future__ import annotations

import json
import re
from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo

from ga_tag import injetar

from .coleta import ROOT
from .publicacao import PUBLICO

PAGINA = ROOT / "docs/logs_urnas_2026.html"
INICIO, FIM = "<!--LOGS-URNAS:INICIO-->", "<!--LOGS-URNAS:FIM-->"


def inteiro(v):
    return f"{v:,}".replace(",", ".")


def numero(v):
    return f"{v:.1f}".replace(".", ",") if v is not None else "não disponível"


def bloco(indice=None):
    path = PUBLICO / "indice.json"
    if indice is None and not path.exists():
        return ""
    d = indice or json.loads(path.read_text())
    n = len(d["criterios"])
    c = d["cobertura"]
    return (
        f'{INICIO}<aside class="callout logs-resumo" id="logs-urnas">'
        f"<h3>Os logs acrescentam {n} diagnósticos operacionais</h3>"
        f'<p>Esta camada leu <strong>{inteiro(c["lidos"])} logs</strong> de '
        f'{inteiro(c["catalogadas"])} seções catalogadas. Em {inteiro(c["contagem_confere"])} '
        "a contagem dos ciclos reproduziu o comparecimento no BU. "
        "Tempos, biometria, suspensões, reinícios e conferência documental aparecem por seção.</p>"
        "<p>Os 12 critérios históricos continuam identificados. Os novos diagnósticos não somam pontos "
        "automaticamente: operação com bateria, por exemplo, pode ser funcionamento normal. "
        "Ausência de log analisado não significa ausência de ocorrência.</p>"
        '<p><a href="logs_urnas_2026.html">Ler resultados, cobertura e método dos logs</a> · '
        '<a href="fiscais_mapa.html#camada=logs">Filtrar registros no mapa</a> · '
        '<a href="fiscais_mapa.html#uf=ZZ&amp;ambito=exterior&amp;camada=todas">Ver exterior</a></p>'
        f"</aside>{FIM}"
    )


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
            f'{inteiro(estados.get("Totalizada", 0) + estados.get("Recebida", 0))} tinham boletins do sistema de apuração, sem log listado no hash arquivado. '
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
    regras = "".join(
        f'<article class="regra" id="{k}"><p class="etiqueta">{escape(v["grupo"])} · '
        f'{inteiro(v["secoes"])} seções / {inteiro(v["avaliaveis"])} avaliáveis</p>'
        f'<h3>{i:02d}. {escape(v["nome"])}</h3><p>{escape(v["regra"])}</p>'
        f'<p class="limite">{escape(v["limite"])}</p><p><b>Conferir:</b> {escape(v["conferir"])}</p>'
        f'<a href="fiscais_mapa.html#camada=logs&amp;log={k}">Ver no mapa</a></article>'
        for i, (k, v) in enumerate(d["criterios"].items(), 1)
    )
    tempos = "".join(
        f'<div class="tempo"><h3>{"Brasil" if pais == "brasil" else "Exterior"}</h3>'
        f'<p class="grande">{numero(r["media_s"])} <small>segundos</small></p>'
        f'<p>Média de {inteiro(r["ciclos"])} ciclos completos elegíveis, ponderada pelo número de ciclos, '
        f'nas seções lidas. Mediana: {numero(r["mediana_s"])} s; cerca de 90% dos ciclos duraram até {numero(r["p90_s"])} s.</p></div>'
        for pais, r in d["tempos"].items()
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
            "Votação lenta",
            "Habilitação biográfica alta",
        ],
        [
            [
                k,
                inteiro(v["secoes"]),
                inteiro(v["criterios"].get("tempo_lento", 0)),
                inteiro(v["criterios"].get("biografica_alta", 0)),
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
<link rel="stylesheet" href="assets/logs_urnas_2026.css">
</head><body>
<header><nav><a href="index.html">Arvor · Biblioteca</a><a href="fiscais_mapa.html#camada=logs">Mapa de fiscais</a><a href="politizesuavizinhanca.html">Consultar minha seção</a></nav>
<p class="etiqueta">Primeiro turno · 4 de outubro de 2026 · Auditoria da operação</p>
<h1>O ritmo da votação.<br><em>O registro de cada urna.</em></h1>
<p class="abertura">Os logs permitem medir o tempo entre habilitação e voto computado, distinguir formas de identificação e localizar interrupções. Esta análise acrescenta {n} diagnósticos aos 12 critérios históricos. Cada registro vem com uma regra e com o que falta conferir.</p>
<div class="numeros"><div><b>{inteiro(c["lidos"])}</b><span>logs lidos</span></div><div><b>{f'{pct:.3f}'.replace('.', ',')}%</b><span>das seções catalogadas</span></div><div><b>{inteiro(c["contagem_confere"])}</b><span>contagens conciliadas com o BU</span></div></div>
</header><main>
<section id="achados"><h2>O que aparece nos registros</h2>
<p>Em <b>{inteiro(c["lidos"] - c["contagem_confere"])} seções</b>, a contagem dos eventos ou a reconstrução dos ciclos ainda não reproduz o comparecimento do BU. São casos para conferir arquivos e contingências; a diferença não identifica alteração de votos.</p>
<p>A regra de duração sinalizou <b>{inteiro(d["criterios"]["tempo_rapido"]["secoes"])} seções mais rápidas</b> e <b>{inteiro(d["criterios"]["tempo_lento"]["secoes"])} mais lentas</b> que a referência comparável. A regra de habilitação biográfica sinalizou {inteiro(d["criterios"]["biografica_alta"]["secoes"])}. Cada uma usa seu próprio conjunto elegível e limite mínimo de diferença.</p>
<p>O sistema registrou <b>{inteiro(op.get("falhas_assinatura_declaradas", 0))} eventos de falha na verificação de assinatura</b>: {inteiro(op.get("falhas_assinatura_com_sucesso_posterior", 0))} seguidos de SUCESSO para o mesmo arquivo e urna, {inteiro(op.get("falhas_assinatura_sem_sucesso_localizado", 0))} sem sucesso posterior localizado e {inteiro(op.get("falhas_assinatura_ordem_incerta", 0))} com ordem temporal incerta. O sucesso posterior também é evidência e aparece na ficha, junto do erro.</p>
<p>Há {inteiro(op.get("erros", 0))} eventos ERRO/FATAL no dia. Nas {inteiro(op.get("secoes_janela_classificavel", 0))} seções cuja janela pôde ser delimitada, {inteiro(op.get("erros_na_janela_votacao", 0))} ficaram entre a primeira habilitação reconstruída e o último cômputo, e {inteiro(op.get("erros_fora_da_janela", 0))} fora dela. Um evento não equivale a uma seção nem a uma falha sem recuperação.</p>
<h3>Arquivos conferidos em detalhe</h3><p>Exemplos escolhidos para mostrar situações distintas. Não são amostra representativa nem lista dos casos mais graves.</p>{casos}
</section>
<section id="leitura"><h2>O que se pode medir</h2>
<div class="passos"><article><b>01</b><h3>Habilitação</h3><p>Do identificador digitado pelo mesário até a liberação do eleitor. Inclui as etapas eletrônicas observadas; não inclui toda a conferência documental.</p></article><article><b>02</b><h3>Votação</h3><p>Da habilitação ao evento de voto computado. Ciclos suspensos parcialmente ficam fora da duração de um voto completo.</p></article><article><b>03</b><h3>Intervalo</h3><p>Entre dois cômputos consecutivos. Mistura ociosidade, identificação e votação. Um intervalo longo não demonstra fila ou paralisação.</p></article></div>
<p class="nota">Os logs não revelam a escolha do eleitor. Nenhuma opção de voto ou identificação pessoal é reconstruída nesta análise. Os tempos são agregados por seção.</p>
<div class="tempos">{tempos}</div>
<figure class="distribuicao"><a href="assets/logs_urnas_2026/tempos.svg"><picture><source media="(max-width:700px)" srcset="assets/logs_urnas_2026/tempos-mobile.svg"><img src="assets/logs_urnas_2026/tempos.svg" width="1040" height="700" alt="Distribuição dos tempos de votação em intervalos de dez segundos, separada entre Brasil e exterior."></picture></a><figcaption>Cada barra reúne dez segundos. A última reúne todos os ciclos de 180 segundos ou mais. O eixo vertical mostra a parcela dos ciclos elegíveis de cada território; as quantidades de cargos diferem. <a href="assets/logs_urnas_2026/tempos.png">Baixar a figura em PNG</a>.</figcaption></figure>
{tempos_cargos}
<p>Seções com modelos mistos, indeterminados ou divergentes entre log e BU ficam fora da comparação de tempos e das referências de biometria. A comparação entre seções usa o mesmo número de confirmações de cargo no ciclo, a mesma UF e o mesmo modelo de urna. No exterior há apenas a eleição presidencial; suas seções não são comparadas com seções brasileiras de seis confirmações. A média acima descreve somente o conjunto já lido; enquanto a coleta estiver incompleta, não é estimativa representativa do país.</p>
</section>
<section id="biometria"><h2>“Sem biometria” não é uma categoria única</h2>
<p><b>Reconhecimento biométrico</b> é a habilitação registrada como biométrica. <b>Habilitação biográfica</b> é o procedimento de dado pessoal depois da tentativa de reconhecimento, seguido da liberação. <b>Sem biometria</b> é a terceira contagem do BU. As três contagens precisam reproduzir o boletim antes de uma seção entrar na comparação.</p>
<p>A taxa biográfica divide biográficas por biométricas mais biográficas. A taxa sem biometria divide a terceira categoria pelo comparecimento. Compará-las como se fossem o mesmo percentual troca o denominador e pode criar um falso diagnóstico.</p>
<p>A referência é a mediana das seções da mesma zona, município e modelo, com pelo menos 30 seções elegíveis e denominador de 50 pessoas em cada uma. Sem esse suporte, a referência fica ausente. Idade, qualidade das digitais e cobertura cadastral continuam sem controle individual.</p>
{tabela_bio}<p>Os totais acima incluem somente seções cujas três categorias e comparecimento fecharam entre log e BU. Não incluem BUs sem esses campos e não estimam as categorias ausentes.</p>
</section>
<section id="criterios"><h2>{n} diagnósticos. Nenhum é prova isolada.</h2>
<p>As contagens se sobrepõem. Um único reinício pode gerar mais de um diagnóstico. Os registros não aumentam automaticamente a pontuação histórica e não servem para estimar probabilidade de fraude. ALERTA costuma incluir digitação inválida ou pergunta do sistema ao mesário; ele não é tratado como ERRO.</p>
<div class="regras">{regras}</div></section>
<section id="cobertura"><h2>A cobertura faz parte do resultado</h2>
<p>Catálogo: {inteiro(c["catalogadas"])} seções principais; {inteiro(c["com_log_no_catalogo"])} com nome de log no catálogo utilizado, incluindo complementos documentados. Recuperados: {inteiro(d["coleta"].get("ok", 0))}; com SHA-256 igual ao da coleta anterior: {inteiro(d["coleta"].get("hash_anterior_confere", 0))}. Lidos e vinculados a um BU: {inteiro(c["lidos"])}. Elegíveis para comparação de tempo: {inteiro(c["tempo_elegivel"])}.</p>{lacunas}
<p>Uma seção sem análise não recebe zero ocorrências. Ausência de publicação, falha de download, formato não reconhecido e falta de BU são limitações distintas. O quadro mostra o estágio desta publicação, em {escape(data_publicacao)}.</p>
{situacoes}
{tabela_uf}</section>
<section id="sensibilidade"><h2>O resultado depende do corte</h2>
<p>Referência: mediana empírica. Escala robusta: 1,4826 vezes a mediana dos desvios absolutos, com piso de 3 segundos para tempos e de 1 ponto percentual para taxas. A regra principal usa 4 escalas, acompanhada de diferença mínima. As alternativas usam 3 e 5, mantendo os demais requisitos. A própria seção participa da referência. Isso é triagem exploratória, não teste com nível de significância.</p>
{sensibilidade}<p>As colunas comparam critérios sobre a mesma cobertura. Não são milhares de confirmações independentes: sem revisão documental, a multiplicidade e a correlação produzem falsos positivos.</p></section>
<section id="fontes"><h2>Do original à conferência</h2>
<ol><li>O arquivo de cada seção vem do mesmo endereço e hash de transmissão associado ao BU arquivado. Seu SHA-256 é comparado ao preservado na coleta anterior quando ele existe. A ausência de hash anterior fica explícita; não é uma comparação aprovada.</li><li>O leitor abre o ZIP e os arquivos aninhados de contingência sem extrair em disco. Lê Latin-1, retém os dias 4 e 5 de outubro, confere seção e fase oficial e remove apenas linhas integralmente duplicadas entre arquivos.</li><li>Recuos de relógio são medidos antes de ordenar os fragmentos e invalidam as durações. Ciclos incompletos e categorias desconhecidas ficam explícitos.</li><li>A contagem de cômputos e as três formas de habilitação são comparadas ao BU. Um hash conferido prova identidade dos bytes arquivados; não substitui a validação criptográfica da assinatura eleitoral.</li></ol>
<p><a href="https://www.tse.jus.br/eleicoes/eleicoes-2026">TSE: documentos técnicos das Eleições 2026</a> · <a href="https://dadosabertos.tse.jus.br/dataset/resultados-2026-arquivos-transmitidos-para-totalizacao">TSE: arquivos transmitidos para totalização</a>. O link do arquivo original e o SHA-256 de cada seção estão na ficha do Politize e no CSV.</p>
<p><a href="assets/logs_urnas_2026/secoes.csv.gz">Baixar todas as seções analisadas, CSV comprimido</a> · <a href="assets/logs_urnas_2026/indice.json">Resumo, regras e cobertura em JSON</a> · <a href="https://github.com/ArvorCo/PNAD/tree/main/scripts/apuracao_logs">Código do leitor e das regras</a>.</p>
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
    for nome, ancora in (
        ("apuracao_1o_turno_2026.html", 'id="fiscais"'),
        ("fiscais_thread.html", '<footer class="wrap">'),
    ):
        path = ROOT / "docs" / nome
        texto = path.read_text(encoding="utf-8")
        if INICIO in texto:
            texto = re.sub(
                re.escape(INICIO) + r".*?" + re.escape(FIM),
                lambda _: novo,
                texto,
                flags=re.DOTALL,
            )
        elif nome.startswith("apuracao"):
            ini = texto.index(ancora)
            fim = texto.index("</section>", ini)
            texto = texto[:fim] + novo + texto[fim:]
        else:
            texto = texto.replace(ancora, ancora + "\n  " + novo, 1)
        if nome == "fiscais_thread.html":
            texto = texto.replace(ancora + INICIO, ancora + "\n  " + INICIO)
        path.write_text(texto, encoding="utf-8")
