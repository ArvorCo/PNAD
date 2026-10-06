"""Texto dinâmico dos cards do dossiê da apuração do 1º turno de 2026 e da thread.

Todo número sai dos JSONs de analysis/apuracao_2026/dados/; sem eles, o card cai
num texto neutro, sem número.
"""

import json


def _num(x, casas=2):
    return f"{x:,.{casas}f}".replace(",", " ").replace(".", ",").replace(" ", ".")


def _ler(root, nome):
    caminho = root / "analysis/apuracao_2026/dados" / f"{nome}.json"
    if not caminho.exists():
        return None
    return json.loads(caminho.read_text(encoding="utf-8"))


def card(root):
    pres = _ler(root, "presidente")
    lt = _ler(root, "linha_do_tempo")
    pq = _ler(root, "pesquisas_vs_urna")
    an = _ler(root, "anomalias")
    title = "Flávio na frente."
    stats = [("100%", "das seções apuradas")]
    lede = "O resultado, a noite minuto a minuto e a falha do TSE, com três camadas de fonte."
    if pres:
        n = pres["nacional"]
        title = (
            f"Flávio na frente, {_num(n['pct']['flavio'])} × {_num(n['pct']['lula'])}."
        )
        stats = [
            (
                f"{_num(n['diferenca_votos'] / 1e6)} mi",
                "votos de diferença, 100% das seções",
            )
        ]
        if lt and lt.get("pausa_geral", {}).get("lacunas"):
            minutos = lt["pausa_geral"]["lacunas"][0]["minutos"]
            stats.append((f"{round(minutos)} min", "sem nenhum arquivo de resultado"))
        if pq:
            erro = pq["medias"]["ultimas_ondas_publicado"][
                "diferenca_lula_menos_flavio"
            ]["erro"]
            stats.append((f"+{_num(erro)}", "pontos de erro das pesquisas, pró-Lula"))
        n_topo = len(an["topo"][:50]) if an else None
        fecho = (
            f"<b>Nenhuma das {n_topo} zonas mais atípicas aponta para fraude.</b>"
            if n_topo
            else "<b>O que o banco prova, o que o tribunal disse e o que falta explicar.</b>"
        )
        lede = (
            "O resultado com 100% das seções, a noite minuto a minuto, as paradas do "
            "TSE provadas pelos arquivos públicos e pesquisas contra urna. " + fecho
        )
    return {
        "slug": "apuracao_1o_turno_2026",
        "eyebrow": "Dossiê da apuração · 1º turno de 2026",
        "title": title,
        "title_em": "E o TSE parado no pico.",
        "lede": lede,
        "stats": stats,
        "foot": "dados do TSE lidos e guardados versão a versão · fonte de cada número na página",
        "accent": "blue",
    }


def card_thread(root):
    nr = _ler(root, "noite_regioes")
    est = _ler(root, "estrategia_2t")
    from apuracao_2026.thread_posts_a import POSTS_A
    from apuracao_2026.thread_posts_b import POSTS_B

    stats = [
        (str(len(POSTS_A) + len(POSTS_B)), "cards 1:1 com o texto pronto para o X")
    ]
    if nr:
        dec = nr["decomposicao"]
        stats.append(
            (
                f"{_num(dec['pico_pp'], 1)} → {_num(dec['final_pp'], 1)}",
                "pontos de vantagem ao longo da noite",
            )
        )
    if est:
        eq = est["aritmetica"]["equilibrio"]
        stats.append(
            (
                f"{_num(eq['lula_precisa_se_todos_votarem_pct'], 0)}%",
                "da terceira via que Lula precisaria para virar",
            )
        )
    return {
        "slug": "apuracao_1o_turno_2026_thread",
        "eyebrow": "Thread · apuração do 1º turno de 2026",
        "title": "A noite inteira, card a card.",
        "title_em": "E o caminho do 2º turno.",
        "lede": (
            "Placar, paradas do TSE, pesquisas contra urna, auditoria por zona e por "
            "seção. <b>No fim, a conta do 2º turno e as frases para conversar com o "
            "eleitor de terceira via.</b>"
        ),
        "stats": stats,
        "foot": "arquivos públicos do TSE · cada número com fonte no dossiê",
        "accent": "blue",
        "thread": True,
    }


def card_fiscais_thread(root):
    """Card da thread dos fiscais (capítulo 13): números de fiscais.json."""
    caminho = root / "analysis/apuracao_2026/dados/fiscais.json"
    stats = []
    if caminho.exists():
        F = json.loads(caminho.read_text(encoding="utf-8"))
        R = F["resumo"]
        stats = [
            (_num(R["secoes_sinalizadas"], 0), "seções atípicas, com endereço"),
            (
                _num(R["fiscais"]["um_por_local"]["todos"], 0),
                "locais de votação, um fiscal em cada",
            ),
            (
                _num(R["por_nivel"]["alta"]["secoes"], 0),
                "seções no nível alta, onde ir primeiro",
            ),
        ]
    return {
        "slug": "fiscais_thread",
        "eyebrow": "Thread · onde colocar fiscal no 2º turno",
        "title": "Prioridade, não acusação.",
        "title_em": "O fiscal vê o que a urna não mostra.",
        "lede": (
            "A lista de seções atípicas, os cenários clássicos de manipulação do voto e "
            "o que já aconteceu no Brasil, com data e tribunal. <b>No fim, o kit do "
            "fiscal: o que levar, o que conferir e a quem reportar.</b>"
        ),
        "stats": stats,
        "foot": "atipicidade estatística não é irregularidade · cenário é hipótese de risco",
        "accent": "blue",
        "thread": True,
    }
