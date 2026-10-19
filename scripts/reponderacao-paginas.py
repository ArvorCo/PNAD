"""Rotas públicas do agregador: segundo turno, acervo e diário documental."""

import hashlib
import importlib
import json
from html import escape as esc
from pathlib import Path

from bs4 import BeautifulSoup
from ga_tag import injetar
from reponderacao_vista.style import SCRIPT

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = "reponderacao_pnad_1o_turno_2026.html"
LOG = "reponderacao_pnad_log.html"
CURRENT = "reponderacao_pnad.html"


def asset(name, extension):
    path = f"assets/{name}.{extension}"
    version = hashlib.sha256((ROOT / "docs" / path).read_bytes()).hexdigest()[:12]
    return f"{path}?v={version}"


def head(title, slug, description, styles=()):
    card = f"https://brasil.arvor.co/img/og/{slug}.png"
    url = f"https://brasil.arvor.co/{slug}.html"
    return (
        '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<script>document.documentElement.classList.add('js')</script>"
        f'<title>{esc(title)} · Arvor</title><meta name="description" content="{esc(description, quote=True)}">'
        f'<link rel="canonical" href="{url}"><link rel="icon" href="favicon.ico">'
        '<meta name="theme-color" content="#142d2a"><meta property="og:type" content="article">'
        '<meta property="og:locale" content="pt_BR"><meta property="og:site_name" content="Arvor Intelligence">'
        f'<meta property="og:title" content="{esc(title, quote=True)}"><meta property="og:description" content="{esc(description, quote=True)}">'
        f'<meta property="og:url" content="{url}"><meta property="og:image" content="{card}">'
        '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
        f'<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{card}">'
        + "".join(
            f'<link rel="stylesheet" href="{asset(s, "css")}">'
            for s in [
                "reponderacao_pnad",
                "reponderacao_tip",
                "reponderacao_metodologias",
                "reponderacao_validos",
                "reponderacao_simulador",
                *styles,
            ]
        )
        + "</head>"
    )


def frame(ns, title, slug, description, content, toc, scripts=(), styles=()):
    return (
        head(title, slug, description, styles)
        + '<body><a class="skip" href="#conteudo">Pular para o conteúdo</a><header class="masthead">'
        '<a href="index.html">ARVOR <span>Intelligence</span></a><span>Pesquisas · renda · comparecimento</span></header>'
        '<main id="conteudo">'
        + content[0]
        + '<nav class="toc" aria-label="Seções">'
        + "".join(f'<a href="{href}">{esc(label)}</a>' for href, label in toc)
        + "</nav>"
        + "".join(content[1:]).replace(
            'href="#atualizacao"', f'href="{LOG}#atualizacao"'
        )
        + '</main><footer class="wrap footer"><b>ARVOR Intelligence</b>'
        f"<span>Referência de {esc(ns['D']['referencia'])} · hipóteses e fontes abertas</span>"
        f'<span><a href="{CURRENT}">2º turno</a> · <a href="{ARCHIVE}">1º turno</a> · <a href="{LOG}">Histórico</a> · <a href="index.html">Biblioteca</a></span></footer>'
        + ns["bloco_tips"](
            [
                key
                for key in ns["TIPS"]
                if slug != "reponderacao_pnad" or not key.endswith("|1t")
            ]
        )
        + f"<script>{SCRIPT}</script>"
        + "".join(
            f'<script src="{asset(s, "js")}" defer></script>'
            for s in ["reponderacao_tip", "reponderacao_pesquisas", *scripts]
        )
        + "</body></html>"
    )


def archive_links():
    return (
        '<div class="wrap rs-archives">'
        f'<div><a href="{ARCHIVE}">1º turno: o que previmos e o que a urna mostrou ↗</a><p>Séries, candidaturas, erros e fichas preservados para comparação.</p></div>'
        f'<div><a href="{LOG}">Histórico de alterações e ondas ↗</a><p>Quando entrou, o que mudou, qual documento sustenta e onde conferir.</p></div></div>'
    )


def current_coverage(ns):
    data = ns["D"]
    latest = {}
    for p in data["pesquisas"] + data.get("nao_reponderaveis", []):
        if not p.get("divulgacao") or not any(
            "2t" in (p.get(key) or {}) for key in ("publicado", "publicado_validos")
        ):
            continue
        old = latest.get(p["instituto"])
        if old is None or (p["divulgacao"], p["campo"]["fim"]) > (
            old["divulgacao"],
            old["campo"]["fim"],
        ):
            latest[p["instituto"]] = p
    cards = []
    for p in sorted(latest.values(), key=lambda x: x["divulgacao"], reverse=True):
        valid_only = "2t" not in p.get("publicado", {})
        pub = (
            p.get("publicado_validos", {})["2t"] if valid_only else p["publicado"]["2t"]
        )
        if not all(k in pub for k in ("flavio", "lula")):
            continue
        status = "Com renda" if "2t" in p.get("turnos", {}) else "Sem ajuste de renda"
        if p.get("renda", {}).get("perfil_tipo") == "cota_registrada":
            status += " · cotas registradas, ajuste provisório"
        elif (
            p["id"] == "quaest_2026-10-13"
            and p.get("renda", {}).get("perfil_tipo") == "perfil_publicado"
        ):
            status += " · perfil publicado, etapa da ponderação não informada"
        if p["campo"]["inicio"] <= "2026-10-04":
            status += (
                " · campo atravessa o 1º turno; fora da central"
                if p["campo"]["fim"] > "2026-10-04"
                else " · campo anterior ao 2º turno"
            )
        source = p.get("fonte") or {}
        url = source.get("url")
        details = (
            f'<a href="#pesquisa-{p["id"]}">Cálculo e ficha</a> · '
            if p.get("turnos", {}).get("2t")
            else ""
        )
        if url:
            details += f'<a href="{esc(url, quote=True)}">Fonte publicada</a>'
        if p.get("dossie"):
            details += (
                f' · <a href="{esc(p["dossie"], quote=True)}">Dossiê e limites</a>'
            )
        cards.append(
            f'<article id="cobertura-{esc(p["id"])}"><h3>{esc(p["instituto"])} <small>· {esc(p["divulgacao"])}</small></h3>'
            f"<p><strong>Flávio {ns['br'](pub['flavio'], 1)} × Lula {ns['br'](pub['lula'], 1)}</strong> / {'válidos publicados' if valid_only else 'total de entrevistados'} · {esc(status)}. "
            f"{esc(p.get('motivo') or '')} {details}</p></article>"
        )
    vox = next((p for p in latest.values() if p["id"] == "vox_brasil_2026-10-07"), None)
    vox_note = ""
    if vox:
        audit = vox.get("fonte", {}).get("auditoria_registro") or {}
        pub = vox["publicado"]["2t"]
        valid_f = 100 * pub["flavio"] / (pub["flavio"] + pub["lula"])
        income = audit.get("alvos_renda_pct", [])
        income_chart = (
            '<div class="rs-vox-income" role="img" aria-label="Alvos de renda registrados: 83,89%, 12,42%, 2,79% e 0,90%"><div>'
            + "".join(f'<span style="width:{v}%"></span>' for v in income)
            + "</div><p>Até 2 SM: <b>83,89%</b> · 2–5: 12,42% · 5–10: 2,79% · acima de 10: 0,90%</p></div>"
            if income
            else ""
        )
        vox_note = (
            '<aside id="vox-renda" class="callout"><h3>Vox: renda publicada não basta para reponderar</h3>'
            f"<p><b>Publicado: Flávio 42,7 × Lula 44,2</b> / total. Excluídos brancos/nulos e indecisos: <b>{ns['br'](valid_f, 1)} × {ns['br'](100 - valid_f, 1)}</b> / válidos. Fonte: pp. 6–7 do relatório de 09/10.</p>"
            + income_chart
            + "<p>Nas 16 páginas, não há voto por faixa de renda. O registro cita Censo 2022 sem identificar tabela ou conceito de renda. A onda fica no acervo, com o placar publicado, e aguarda o cruzamento para receber ajuste.</p>"
            + (
                "<details><summary>O problema do registro e a conferência documental</summary>"
                f'<p>{esc(audit["conclusao"])} <a href="fontes/vox_09102026/registro-conferencia.txt">Conferência do registro e do questionário</a> · '
                f'<a href="{esc(vox["fonte"]["url"], quote=True)}">Relatório público, 16 páginas</a> · '
                '<a href="https://pesqele-divulgacao.tse.jus.br/app/pesquisa/listar.xhtml">Consultar BR-09623/2026 no PesqEle</a>.</p></details>'
                if audit
                else ""
            )
            + "</aside>"
        )
    quaest = next((p for p in latest.values() if p["id"] == "quaest_2026-10-13"), None)
    quaest_note = ""
    if quaest and "2t" in quaest.get("turnos", {}):
        adjusted = quaest["turnos"]["2t"]["cenarios"]["pessoas16_efetivo"]["ajustado"]
        quaest_note = (
            '<aside class="callout" id="quaest-1410"><h3>Quaest de 14/10: íntegra recebida, perfil de renda publicado</h3>'
            f'<p>Publicado: 46 × 44. Usando o perfil publicado como margem, PNAD: <b>{ns["br"](adjusted["flavio"], 2)} × {ns["br"](adjusted["lula"], 2)}</b> / total. '
            "A íntegra de 152 páginas confirma os cruzamentos da p. 24 e publica o perfil de renda na p. 147. "
            "<b>31/42/27 agora têm evidência no perfil da amostra; a etapa da ponderação não é informada.</b> A conta permanece uma sensibilidade condicional na Média e na Projeção, sem alteração numérica por esta revisão documental. Não se localizou regra publicada de eleitor provável; o grupo misto de brancos/nulos/ausentes não identifica abstenção. "
            '<a href="quaest_14102026.html#renda">Ler os cruzamentos, os resíduos e os limites</a>.</p></aside>'
        )
    elif quaest:
        quaest_note = (
            '<aside class="callout" id="quaest-1410"><h3>Quaest de 14/10: 46 × 44, sem ajuste de renda nesta rodada</h3>'
            "<p>Campo domiciliar de 10 a 13/10, incluindo o feriadão. Os dois candidatos ganharam dois pontos desde 03/10; a diferença ficou em dois. "
            "Cotas previstas 31/42/27 conferidas no TSE; cruzamento atual e perfil final ainda não obtidos nesta auditoria. "
            "Entra pelo publicado na Projeção; fora da Média por renda. "
            '<a href="quaest_14102026.html">Ler o dossiê preliminar, a série e as pendências</a>.</p></aside>'
        )
    update_note = ""
    if all(
        latest.get(house, {}).get("id") == ident
        for house, ident in {
            "Palver": "palver_2026-10-13",
            "Datafolha": "datafolha_2026-10-14",
            "Indexa/Broadcast": "indexa_2026-10-14",
        }.items()
    ):
        datafolha = latest["Datafolha"]
        datafolha_income = datafolha.get("turnos", {}).get("2t", {})
        datafolha_note = (
            "<p><b>Datafolha: 47 × 45.</b> A onda entra pelo publicado na Projeção. "
            "Faltam renda completa e perfil atual para o ajuste.</p>"
        )
        if datafolha_income:
            adj = datafolha_income["cenarios"]["pessoas16_efetivo"]["ajustado"]
            datafolha_note = (
                '<p id="datafolha-1510-renda"><b>Datafolha: íntegra oficial obtida; renda incorporada.</b> '
                f'Publicado 47 × 45; sensibilidade PNAD <b>{ns["br"](adj["flavio"], 2)} × '
                f'{ns["br"](adj["lula"], 2)}</b> no total. A íntegra publicada em 16/10 confirma '
                "bases ponderadas de 1.172/918/335 (p. 30, anexo p. 8). O ajuste afeta "
                "2.425 das 2.520 entrevistas; as 95 sem renda conservam o publicado. "
                "A onda passa a entrar nas duas centrais. A tendência agora compara "
                "as duas ondas Datafolha reponderadas, eliminando a troca anterior "
                "entre PNAD e publicado. Campo 13–14/10, BR-00466/2026; não é nova onda. "
                f'<a href="{esc(datafolha["fonte"]["url"])}">Íntegra oficial, 42 páginas</a>.</p>'
            )
        update_note = (
            '<aside class="callout" id="rodada-1510"><h3>15/10: Datafolha, Palver e Indexa</h3>'
            + datafolha_note
            + "<p><b>Palver: 50 × 49.</b> Perfil ponderado e voto por renda conferidos no PDF "
            "atual; entra nas duas centrais. O método v3 passa a usar PNAD 2025 e voto "
            "declarado no primeiro turno de 2026. A diferença ante a onda anterior "
            "mistura mudança de método e de preferência.</p>"
            "<p><b>Indexa/Broadcast: 44 × 42.</b> Entra pelo publicado na Projeção. "
            "Há voto por renda, mas faltam os pesos dos grupos. Os 8% que dizem não votar "
            "são resposta da pesquisa, não previsão de abstenção.</p>"
            '<p class="note">Totais na ordem Flávio × Lula. Na <a href="https://www.atlasintel.org/polls/exclusive-polls">AtlasIntel</a>, '
            "a última nacional localizada continua sendo 09/10; não há nova onda incorporada. "
            '<a href="reponderacao_pnad_log.html#atualizacao">Conferir fontes e pendências</a> · '
            '<a href="assets/reponderacao_20261015.json">Inventário de 15/10</a>.</p></aside>'
        )
    today_note = ""
    if all(
        latest.get(house, {}).get("id") == ident
        for house, ident in {
            "Gerp": "gerp_2026-10-16",
            "PoderData": "poderdata_2026-10-15",
            "MDA": "mda_2026-10-15",
            "Futura": "futura_2026-10-15",
        }.items()
    ):
        today_note = (
            '<aside class="callout" id="rodada-1610"><h3>16/10: Gerp, PoderData, CNT/MDA e Futura</h3>'
            "<p><b>Gerp: 50 × 45; PoderData: 47 × 47; CNT/MDA: 46,8 × 45,9.</b> "
            "As três entram com cruzamentos e perfis atuais de renda, conferidos nas íntegras. "
            "Gerp limita a troca aos declarantes (96/99 do perfil arredondado); CNT/MDA, a 99%. "
            "As recusas conservam o publicado. PoderData e CNT/MDA não identificam a etapa "
            "do perfil antes/depois dos pesos: a sensibilidade depende dessa margem publicada.</p>"
            "<p><b>Futura: 49 × 47,5.</b> Entra pelo publicado na Projeção; a íntegra traz "
            "perfil, mas não voto por renda. A ficha informa campo 14–15/10, contra 13–15/10 "
            "na capa. Adotamos a ficha, também confirmada pela divulgação.</p>"
            "<p>PoderData e CNT/MDA declaram ponderação pelo voto do primeiro turno. "
            "Na ficha do PoderData, renda e voto do primeiro turno são acréscimos à lista de 13/10. "
            "A nota da Futura sobre trocar escolaridade TSE pela PNAD já constava em 13/10; "
            "ela não comprova nova mudança entre essas duas ondas. "
            "Diferenças entre ondas podem envolver método e preferência; não demonstram "
            "sozinhas transferência de votos ou comparecimento futuro.</p>"
            "<p><b>A Projeção passou a estimar tendência nesta atualização:</b> a série "
            "pós-primeiro turno atingiu o mínimo de observações exigido pelo motor. "
            "Ela prolonga até 25/10 a inclinação dentro das casas, reduzida pela incerteza; "
            "a Média não faz essa extrapolação. Mudanças de ponderação também podem "
            "entrar nessa inclinação. A divergência entre as centrais exige ler "
            '<a href="#modelo-projecao">cobertura, pesos e hipóteses</a>, sem tratar '
            "a tendência como movimento puro do eleitorado ou probabilidade validada de vitória.</p>"
            '<p class="note">Totais na ordem Flávio × Lula. '
            '<a href="reponderacao_pnad_log.html#atualizacao">Fontes e pendências</a> · '
            '<a href="assets/reponderacao_20261016.json">Inventário de 16/10, com páginas e SHA-256</a>.</p></aside>'
        )
    verita_note = ""
    verita = latest.get("Veritá", {})
    if verita.get("id") == "verita_2026-10-16" and verita.get("turnos", {}).get("2t"):
        adj = verita["turnos"]["2t"]["cenarios"]["pessoas16_efetivo"]["ajustado"]
        verita_note = (
            '<aside class="callout" id="rodada-1710"><h3>17/10: Veritá com renda nas duas centrais</h3>'
            "<p><b>Publicado: 49,7 × 47,7 no total; 51,1 × 48,9 nos válidos.</b> "
            f'Sensibilidade PNAD: <b>{ns["br"](adj["flavio"], 2)} × '
            f'{ns["br"](adj["lula"], 2)}</b> no total. Campo 12–16/10, '
            "15.554 entrevistas por URA, BR-01107/2026. O perfil de renda "
            "42,7/38,6/18,7 e os cruzamentos atuais foram conferidos no relatório. "
            "A etapa do perfil antes/depois da ponderação não é informada: "
            "o ajuste é condicional à margem publicada. Na passagem de 16 para 17/10, "
            "a Ipespe de 10/10 sai da janela de sete dias das duas centrais. "
            "A mudança dos agregados combina essa saída com a entrada da Veritá.</p>"
            "<p><b>Os 2,6% rotulados «ausente» são o subtotal de branco/nulo "
            "(1,5%) e NS/NR (1,1%).</b> Não são abstenção e não se somam novamente "
            "à cédula. Usamos os percentuais publicados; as frequências dos "
            "candidatos diferem em uma unidade do subtotal impresso. "
            "A numeração impressa salta: o placar está na página 9 do PDF "
            "(impressa 13), e o voto por renda na 10 (impressa 14).</p>"
            '<p class="note"><a href="fontes/verita_17102026.pdf">Relatório fornecido, 13 páginas</a> · '
            '<a href="assets/reponderacao_20261017.json">Inventário e SHA-256</a> · '
            '<a href="#pesquisa-verita_2026-10-16">Cálculo e controles</a>.</p></aside>'
        )
    october19_note = ""
    if all(
        latest.get(house, {}).get("id") == ident
        for house, ident in {
            "Nexus": "nexus_2026-10-18",
            "PoderData": "poderdata_2026-10-18",
        }.items()
    ):
        october19_note = (
            '<aside class="callout" id="rodada-1910"><h3>19/10: Nexus e PoderData com renda atual</h3>'
            "<p><b>Nexus: 46,5 × 45,9; PoderData: 49 × 46 no total.</b> "
            "As duas têm campo de 16 a 18/10 e entram nas duas centrais com os cruzamentos atuais. "
            "A Nexus passa a publicar uma casa decimal e muda o perfil para 21/16/40/23; "
            "PoderData mantém 46/33/21. A etapa antes/depois da ponderação não está explícita "
            "nos perfis publicados: as sensibilidades PNAD são condicionais a essas margens.</p>"
            "<p>PoderData declara ponderação pelo voto do primeiro turno, como em 16/10. "
            "Seu placar completo 49/46/4/2 soma 101 por arredondamento; válidos divulgados "
            "52/48 ficam separados da divisão dos inteiros. Na Nexus, válidos publicados "
            "50,3/49,7 e presença declarada de 92,9% não substituem as hipóteses de comparecimento "
            "das centrais. Uma onda por casa, sem duplicação da versão anterior.</p>"
            '<p class="note"><a href="nexus_btg_18102026.html">Dossiê Nexus e íntegra de 128 páginas</a> · '
            '<a href="fontes/poderdata_19102026.pdf">PoderData, íntegra de 33 páginas</a> · '
            '<a href="assets/reponderacao_20261019.json">Inventário, páginas e SHA-256</a>.</p></aside>'
        )
    return (
        '<section id="cobertura-atual" class="rs-documentary"><div class="wrap"><p class="eyebrow">Cobertura da disputa</p>'
        '<h2>O que entra na conta.</h2><p class="note">A Média exige cruzamento de renda e campo posterior a 04/10. '
        "A Projeção inclui também o publicado das casas sem renda conferida, com cobertura e pesos explícitos. Placar na ordem Flávio × Lula.</p>"
        + october19_note
        + verita_note
        + today_note
        + update_note
        + quaest_note
        + vox_note
        + '<details class="rs-wave-summary"><summary>Última publicação de cada instituto e limites de inclusão</summary>'
        + "".join(cards)
        + "</details></div></section>"
    )


def compact(html, selectors):
    """Recolhe tabelas auxiliares sem remover texto, fontes ou âncoras."""
    soup = BeautifulSoup(html, "html.parser")
    for selector, title in selectors:
        node = soup.select_one(selector)
        if node is None:
            continue
        wrapper = soup.new_tag("details")
        summary = soup.new_tag("summary")
        summary.string = title
        wrapper.append(summary)
        node.wrap(wrapper)
    return str(soup)


def current_html(ns):
    forecast = importlib.import_module("reponderacao-validos").write(ns["D"])
    simulation = importlib.import_module("reponderacao-simulador").write(
        ns["D"], forecast
    )
    app = importlib.import_module("reponderacao-simulador-view").section_html(
        simulation, ns["tabela"]
    )
    series = compact(
        ns["ch_segundo_turno"](),
        [
            ("#janela-2t", "Conferir a cobertura da série histórica"),
            (".ledger", "Médias sobre o total de entrevistados"),
        ],
    )
    description = f"Duas centrais do 2º turno: Média Arvor {ns['br'](simulation['central']['flavio'], 1)} × {ns['br'](simulation['central']['lula'], 1)}; Projeção Arvor {ns['br'](simulation['central_projection']['flavio'], 1)} × {ns['br'](simulation['central_projection']['lula'], 1)}. Flávio × Lula nos válidos; simule abstenção e brancos/nulos."
    return frame(
        ns,
        "2º turno: votos válidos e cenários de comparecimento",
        "reponderacao_pnad",
        description,
        [
            app,
            archive_links(),
            current_coverage(ns),
            series,
            ns["ch_institutos"]("2t"),
            ns["ch_manchete"](),
            ns["ch_pesquisas"]("2t"),
            ns["ch_metodo"](),
            ns["ch_fontes"]("2t"),
        ],
        [
            ("#simulador", "Simulador"),
            ("#modelo-projecao", "Projeção"),
            ("#cobertura-atual", "Cobertura"),
            ("#segundo-turno", "Séries"),
            ("#institutos-2t", "Institutos"),
            ("#pesquisas", "Fichas"),
            ("#metodo", "Método"),
            (ARCHIVE, "1º turno"),
            (LOG, "Histórico"),
        ],
        [
            "reponderacao_simulador_motor",
            "reponderacao_contagem",
            "reponderacao_simulador",
            "reponderacao_rotas",
        ],
    )


def archive_html(ns):
    closed = importlib.import_module("reponderacao-arquivo").close(
        ns["D"], "2026-10-04"
    )
    projection = importlib.import_module("reponderacao-validos-view").section_html(
        closed, ns["tabela"], ("1t",)
    )
    projection = projection.replace(
        "Da pesquisa<br><em>à urna.</em>", "A projeção<br><em>contra a urna.</em>"
    )
    soup = BeautifulSoup(projection, "html.parser")
    soup.select_one(".lead").string = (
        "Arquivo do 1º turno, fechado em 04/10: projeções, resultado oficial e erros. Alternar hipóteses após a urna não valida uma previsão."
    )
    intro = (
        '<section class="hero"><div class="wrap"><p class="eyebrow">Arquivo · 1º turno de 2026</p><h1>A conta de ontem.<br><em>A urna de hoje.</em></h1><p>Séries, hipóteses, versões, candidaturas e documentação preservadas. O resultado permite medir o erro, sem reescrever o passado.</p>'
        + f'<p><a href="{CURRENT}">← Voltar ao simulador do 2º turno</a> · <a href="{LOG}">Histórico de alterações</a></p></div></section>'
    )
    return frame(
        ns,
        "1º turno de 2026: reponderação e comparação com a urna",
        "reponderacao_pnad_1o_turno_2026",
        "Acervo completo de ondas, projeções, candidaturas, metodologia e erros do primeiro turno.",
        [
            intro,
            importlib.import_module("reponderacao_vista.urna_serie_view").section(
                ns["D"]
            ),
            str(soup),
            ns["ch_primeiro_turno"](closed),
            importlib.import_module("reponderacao-palver-view").audit_html(
                closed, ns["tabela"]
            ),
            ns["ch_institutos"]("1t"),
            importlib.import_module("reponderacao-metodos").section_html(),
            importlib.import_module("reponderacao-futura-perfil").section_html(
                ns["tabela"]
            ),
            ns["ch_pesquisas"]("1t"),
            ns["ch_metodo"](),
            ns["ch_fontes"]("1t", "2026-10-04"),
        ],
        [
            ("#agregador-urna", "Média × urna"),
            ("#projecao-validos", "Projeção × urna"),
            ("#primeiro-turno", "Séries e erros"),
            ("#institutos-1t", "Institutos"),
            ("#palver-pesos", "Palver e versões"),
            ("#comparar-metodos", "Métodos históricos"),
            ("#pesquisas", "Fichas"),
            (CURRENT, "2º turno"),
            (LOG, "Histórico"),
        ],
        ["reponderacao_metodologias", "reponderacao_validos"],
        styles=["reponderacao_urna_serie"],
    )


def log_html(ns):
    history = importlib.import_module("reponderacao-diario").update(ns["D"])
    all_polls = {
        p["id"]: p
        for p in (
            json.loads(f.read_text())
            for f in (ROOT / "analysis/reponderacao/pesquisas").glob("*.json")
        )
    }
    all_polls.update(
        {
            p["id"]: p
            for p in ns["D"]["pesquisas"] + ns["D"].get("nao_reponderaveis", [])
        }
    )
    entries = []
    for entry in sorted(history["changes"], key=lambda p: p["date"], reverse=True):
        entries.append(
            f'<article class="rs-log-entry"><time>{esc(entry["date"])}</time><h3>{esc(entry["title"])}</h3><p>{esc(entry["description"])}</p><p>'
            + " · ".join(
                f'<a href="{esc(url, quote=True)}">{esc(url)}</a>'
                for url in entry["where"]
            )
            + "</p></article>"
        )
    rows = []
    for row in sorted(
        history["waves"], key=lambda r: (r["added"], r["id"]), reverse=True
    ):
        p = all_polls.get(row["id"])
        if p is None:
            continue
        scope = (
            "2t"
            if p["campo"]["inicio"] > "2026-10-04"
            or ("1t" not in p.get("publicado", {}) and "2t" in p.get("publicado", {}))
            else "1t"
        )
        destination = CURRENT if scope == "2t" else ARCHIVE
        anchor = (
            "#pesquisa-" + p["id"]
            if p.get("turnos", {}).get(scope)
            else ("#cobertura-" + p["id"] if scope == "2t" else "#fontes")
        )
        rows.append(
            [
                esc(row["added"]),
                f'<a href="{destination}{anchor}">{esc(p["instituto"])} · {esc(p["id"])}</a>',
                esc(p.get("divulgacao") or "Não informada"),
                esc(p["campo"]["inicio"] + " a " + p["campo"]["fim"]),
                esc(row.get("commit") or "Rodada atual"),
                esc(
                    p.get("motivo") or ", ".join(p.get("turnos", {})) or "Documentação"
                ),
            ]
        )
    archived = []
    for i, record in enumerate(history["documentary_history"]):
        fragment = BeautifulSoup(record["html"], "html.parser")
        fragment.section["id"] = f"alteracao-documental-{i}"
        for node in fragment.select("[id]"):
            if node is not fragment.section:
                del node["id"]
        for link in fragment.select('a[href^="#"]'):
            link["href"] = ARCHIVE + link["href"]
        archived.append(
            f'<details class="rs-log-entry"><summary>{esc(record["date"])} · atualização documental preservada · {esc(record["commit"])}</summary>{fragment}</details>'
        )
    latest = importlib.import_module("reponderacao-cobertura").coverage_html(
        ns["D"], ns["tabela"]
    )
    latest = latest.replace('href="#pesquisa-', f'href="{CURRENT}#pesquisa-')
    content = [
        '<section class="hero"><div class="wrap"><p class="eyebrow">Diário do agregador</p><h1>O que mudou.<br><em>Quando e por quê.</em></h1><p>O arquivo documental das ondas, incorporações e revisões. Divulgação, campo e chegada ao acervo têm datas distintas.</p>'
        + f'<p><a href="{CURRENT}">← Simulador do 2º turno</a> · <a href="{ARCHIVE}">Arquivo do 1º turno</a></p></div></section>',
        '<section id="mudancas" class="chapter"><div class="wrap"><h2>Alterações de produto e método</h2>'
        + "".join(entries)
        + "</div></section>",
        latest,
        '<section id="ondas" class="chapter"><div class="wrap"><h2>Todas as ondas do acervo</h2><p class="note">'
        + esc(history["date_rule"])
        + "</p>"
        + ns["tabela"](
            [
                "Incorporada em",
                "Onda e onde conferir",
                "Divulgação",
                "Campo",
                "Evidência da data",
                "Conteúdo ou limite",
            ],
            rows,
        )
        + "</div></section>",
        '<section id="arquivo-documental" class="chapter"><div class="wrap"><h2>Atualizações anteriores, preservadas</h2><p class="note">Texto de cada atualização na versão histórica correspondente. As ordens dos candidatos e os universos são os declarados em cada registro; estes anúncios não são a central atual.</p>'
        + "".join(archived)
        + "</div></section>",
    ]
    return frame(
        ns,
        "Histórico de ondas e alterações da reponderação",
        "reponderacao_pnad_log",
        "Datas de incorporação, fontes, revisões e destinos de todas as ondas do agregador Arvor.",
        content,
        [
            ("#mudancas", "Mudanças"),
            ("#atualizacao", "Última conferência"),
            ("#ondas", "Todas as ondas"),
            ("#arquivo-documental", "Arquivo"),
            (CURRENT, "2º turno"),
            (ARCHIVE, "1º turno"),
        ],
    )


def write_companions(ns, *, refresh_archive=False):
    destination = ns["PAGE"].parent
    outputs = [(LOG, log_html(ns))]
    if refresh_archive or not (destination / ARCHIVE).exists():
        # Renderizar o arquivo em testes ou leituras também deve ser puro.
        importlib.import_module("reponderacao_vista.urna_serie").write(
            ns["D"], assets=ns.get("ASSETS", destination / "assets")
        )
        outputs.append((ARCHIVE, archive_html(ns)))
    for name, html in outputs:
        (destination / name).write_text(
            injetar(html).replace("<section ", "\n<section ") + "\n"
        )
