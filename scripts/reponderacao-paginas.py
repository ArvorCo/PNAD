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
                if (slug != "reponderacao_pnad" or not key.endswith("|1t"))
                and (slug == "reponderacao_pnad" or not key.startswith("history2t|"))
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
        elif p.get("renda", {}).get("perfil_tipo") == "hipotese_onda_anterior":
            status += " · PRÉVIA com perfil da onda anterior"
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
            '<p class="note">Totais na ordem Flávio × Lula. Na conferência de 15/10, a <a href="https://www.atlasintel.org/polls/exclusive-polls">AtlasIntel</a> '
            "tinha 09/10 como última nacional localizada. "
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
    complement_note = ""
    if latest.get("AtlasIntel", {}).get("id") == "atlas_2026-10-18":
        complement_note = (
            '<aside class="callout" id="rodada-1910-complemento"><h3>17–19/10: Ipespe, Atlas, Futura, Vox e DataTrends</h3>'
            "<p><b>Ipespe de sábado (17/10) e Atlas de segunda (19/10) entram nas duas centrais.</b> "
            "Usamos os perfis e cruzamentos das próprias ondas. A Ipespe publica 48 × 46 no total "
            "e 51,2 × 48,8 nos válidos; a Atlas, 49,8 × 47,6 e 51,1 × 48,9. "
            "Ambas têm perfil publicado sem etapa pré/pós-pesos explícita: o ajuste PNAD é condicional. "
            "A Atlas agrega branco/nulo/não sei em 2,6%; esse bloco não vira indecisos identificados.</p>"
            "<p><b>Futura de 19/10 e Vox de domingo (18/10) entram somente pelo publicado na Projeção.</b> "
            "A Futura registra 48,3 × 47,5, sem voto por renda. A Vox registra 44,6 × 46,4 "
            "e agora publica cruzamentos, mas não define se a renda é familiar, individual ou per capita. "
            "Seu perfil econômico de 84/12,4/2,7/1 não recebe ajuste por renda familiar PNAD. "
            "Os cruzamentos por sexo e renda recompõem o total; isso não resolve a definição da variável.</p>"
            "<p><b>DataTrends de 19/10: 49 × 46 no total, 51,5 × 48,5 nos válidos.</b> "
            "Resultado conferido na divulgação de Edmar Lyra, dirigente do instituto; "
            "entrou inicialmente pelo publicado. Em 20/10, a íntegra foi localizada e a mesma onda "
            "passou a receber sensibilidade por renda; veja a revisão acima. "
            "Paraná BR-09051/2026 "
            "é estadual, no Tocantins, e não entra como pesquisa nacional.</p>"
            '<p class="note"><a href="fontes/ipespe_17102026.pdf">Ipespe, 39 páginas</a> · '
            '<a href="fontes/atlas_19102026.pdf">Atlas, 20 páginas</a> · '
            '<a href="fontes/futura_19102026.pdf">Futura, 18 páginas</a> · '
            '<a href="fontes/vox_18102026.pdf">Vox, 53 páginas</a> · '
            '<a href="assets/reponderacao_20261019_complemento.json">Inventário, controles e SHA-256</a>.</p></aside>'
        )
    october20_note = ""
    if latest.get("Real Time Big Data", {}).get("id") == "realtime_2026-10-19":
        october20_note = (
            '<aside class="callout" id="rodada-2010"><h3>20/10: Real Time, Alfa, Gerp, França e Data Ranking</h3>'
            "<p><b>Real Time: 48 × 45; Alfa: 48,8 × 45,9 no total.</b> "
            "As duas têm campo de 15 a 19/10 e entram com renda atual. A íntegra da "
            "DataTrends de 19/10 também foi localizada: define renda domiciliar total "
            "e permite ajustar a mesma onda, sem duplicação. Os três ajustes são "
            "condicionais aos perfis publicados, cuja etapa antes/depois dos pesos não está explícita.</p>"
            "<p><b>Gerp: 50 × 45; França: 40,95 × 39,65; Data Ranking: 44,6 × 45,4.</b> "
            "Entram pelo publicado na Projeção. Gerp e Data Ranking ainda estão sem íntegra "
            "atual disponível; na Gerp, o código do registro também está pendente. "
            "A nova Gerp substitui a anterior: fica fora da Média enquanto faltar renda atual, "
            "e entra pelo publicado na Projeção, sem transportar a renda antiga.</p>"
            "<p><b>França: os cruzamentos não recompõem o total.</b> Indecisos de 1,2% "
            "a 4% nas faixas de renda não podem produzir os 8,84% do total. O relatório "
            "e os resíduos estão preservados; nenhum ajuste PNAD foi calculado para essa casa.</p>"
            '<p class="note"><a href="fontes/realtime_20102026.pdf">Real Time, 48 páginas</a> · '
            '<a href="fontes/alfa_20102026.pdf">Alfa, 48 páginas</a> · '
            '<a href="fontes/datatrends_19102026.pdf">DataTrends, 38 páginas</a> · '
            '<a href="fontes/franca_20102026.pdf">França, 14 páginas</a> · '
            '<a href="assets/reponderacao_20261020.json">Inventário, controles e SHA-256</a>.</p></aside>'
        )
    october21_note = ""
    if latest.get("Veritá", {}).get("id") == "verita_2026-10-19":
        october21_note = (
            '<aside class="callout" id="rodada-2110"><h3>21/10: Veritá, Palver, Quaest, Meio/Ideia e Futura</h3>'
            "<p><b>Veritá: 49,7 × 48,2; Palver: 50 × 48 no total.</b> "
            "Entram com perfil e voto por renda da própria onda. A Veritá muda o perfil "
            "para 41,2/40,1/18,7; como a etapa antes/depois dos pesos não está explícita, "
            "o ajuste é condicional. A Palver publica perfil ponderado 36/41/23 e mantém "
            "o método v3 da onda anterior. Seus 0% de indecisos são arredondados.</p>"
            "<p><b>Quaest: 45 × 44; Meio/Ideia: 48 × 46; Futura: 48,9 × 46,8.</b> "
            "Meio/Ideia e Futura entram pelo publicado na Projeção. A Quaest entrou "
            "inicialmente sem ajuste; em 22/10, sua íntegra de 207 páginas confirmou "
            "o perfil atual e permitiu incluir a mesma onda na Média e na Projeção "
            "com sensibilidade por renda. Meio/Ideia não fornece perfil e voto por "
            "renda na íntegra pública; Futura tem perfil, mas não voto por renda.</p>"
            "<p>Os grupos que juntam branco/nulo, indecisos ou não comparecimento "
            "não identificam abstenção. A presença certa de 97,4% da Veritá é declarada "
            "e não altera a âncora de comparecimento das centrais. Os históricos "
            "conservam as ondas anteriores, inclusive os cenários anteriores ao primeiro turno.</p>"
            '<p class="note"><a href="fontes/verita_21102026.pdf">Veritá, 17 páginas</a> · '
            '<a href="fontes/palver_21102026.pdf">Palver, 112 páginas</a> · '
            '<a href="fontes/ideia_21102026.pdf">Meio/Ideia, 59 páginas</a> · '
            '<a href="fontes/futura_21102026.pdf">Futura, 18 páginas</a> · '
            '<a href="assets/reponderacao_20261021.json">Inventário, controles e SHA-256</a>.</p></aside>'
        )
    october22_note = ""
    if latest.get("PoderData", {}).get("id") == "poderdata_2026-10-21":
        october22_note = (
            '<aside class="callout" id="rodada-2210"><h3>22/10: Datafolha, PoderData, Indexa e novas íntegras</h3>'
            '<p id="datafolha-2210"><b>Datafolha: 47 × 46 no total; 50 × 50 nos válidos divulgados.</b> '
            "G1 e registro BR-09709/2026 confirmam 2.520 entrevistas, campo 20–22/10. "
            "<b>PRÉVIA PNAD com o perfil da onda de 15/10:</b> bases de referência "
            "1.172/918/335 e cobertura assumida de 2.425/2.520 (96,23%). "
            "Os votos por renda são os atuais; o perfil e a cobertura são hipóteses "
            "emprestadas da onda anterior. Os 95/2.520 restantes conservam o topline. "
            "A prévia entra nas duas centrais e na tendência, até obter as bases atuais. "
            "A referência 49/47/4 do TSE não foi usada como amostra observada.</p>"
            "<p><b>PoderData: 49 × 48 no total; 51 × 49 nos válidos divulgados.</b> "
            "Íntegra de 42 páginas, campo 19–21/10. Perfil e cruzamentos de renda "
            "atuais conferidos; ajuste condicional ao perfil publicado. A série do "
            "instituto usa, em sua projeção de válidos, a presença certa declarada "
            "por candidato nesta onda: 97% de Flávio e 95% de Lula. Isso não muda "
            "a hipótese de comparecimento das centrais.</p>"
            "<p><b>Indexa/Broadcast: 45,2 × 44,1; válidos oficiais 50,6 × 49,4.</b> "
            "Caderno digital completo arquivado. O perfil de renda 42/38/20 recompõe "
            "Flávio em 43,806%, 1,394 pp abaixo do publicado: diferença maior que o "
            "arredondamento esperado. A onda entra pelo publicado na Projeção, "
            "sem ajuste PNAD até reconciliar perfil e cruzamentos. Os 4,8% que dizem "
            "não votar ficam separados na ficha e não substituem a previsão de comparecimento.</p>"
            "<p><b>Gerp de 21/10: 50 × 45; válidos 53 × 47.</b> "
            "Íntegra de 59 páginas confirma campo 19–21/10, BR-03835/2026 e perfil "
            "ponderado de renda novo. Entra nas duas centrais; é outra onda, "
            "distinta do tracking divulgado em 20/10, que permanece no histórico.</p>"
            "<p><b>Quaest de 21/10: íntegra localizada, mesma onda revisada.</b> "
            "As 207 páginas confirmam perfil atual 31/42/27 e cruzamentos de renda. "
            "Volta à Média e recebe ajuste na Projeção, sem duplicação.</p>"
            '<p class="note"><a href="fontes/datafolha_22102026_registro.txt">Datafolha, registro transcrito</a> · '
            '<a href="assets/reponderacao_datafolha_20261022_previa.json">Datafolha, prévia e fontes</a> · '
            '<a href="fontes/poderdata_22102026.pdf">PoderData, 42 páginas</a> · '
            '<a href="fontes/gerp_21102026.pdf">Gerp, 59 páginas</a> · '
            '<a href="fontes/quaest_21102026.pdf">Quaest, 207 páginas</a> · '
            '<a href="https://sistema.indexapesquisas.com.br/pesquisaspublicadas/nacional?r=8&amp;embed=1">Indexa, caderno digital</a> · '
            '<a href="fontes/indexa_22102026.json.gz">Baixar caderno Indexa (JSON.gz)</a> · '
            '<a href="assets/reponderacao_20261022.json">Inventário, controles e SHA-256</a>.</p></aside>'
        )
    return (
        '<section id="cobertura-atual" class="rs-documentary"><div class="wrap"><p class="eyebrow">Cobertura da disputa</p>'
        '<h2>O que entra na conta.</h2><p class="note">A Média exige cruzamento de renda e campo posterior a 04/10. '
        "A Projeção inclui também o publicado das casas sem renda conferida, com cobertura e pesos explícitos. Placar na ordem Flávio × Lula.</p>"
        + october22_note
        + october21_note
        + october20_note
        + complement_note
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
            "reponderacao_historico",
        ],
        styles=["reponderacao_historico"],
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
