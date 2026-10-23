"""Cards dos dossiês de outubro, com dados da auditoria corrente."""

import json


def cards(root):
    output = []
    for slug, name, title, emphasis, description, stats, accent in [
        (
            "datafolha_22102026",
            "Datafolha · 22/10/2026",
            "Dois placares.",
            "Uma pesquisa.",
            "<b>A íntegra de 36 páginas.</b> Renda atual, a ordem do arredondamento e as cotas que começam na seleção em campo. Fontes e contas abertas.",
            [
                ("47 × 46", "total publicado / Flávio × Lula"),
                ("50 × 50", "votos válidos oficiais"),
                ("2.425", "base ponderada com renda / de 2.520"),
            ],
            "blue",
        ),
        (
            "nexus_btg_13102026",
            "BTG/Nexus · 13/10/2026",
            "Duas lealdades.",
            "Um país inquieto.",
            "<b>As perguntas por trás do placar.</b> Transferências do primeiro turno, firmeza, renda, presença declarada, problemas do país e expectativas econômicas, com fontes e limites.",
            [
                ("98%", "mantêm o voto / eleitores de cada finalista no 1º turno"),
                ("54%", "esperam melhora da economia do país"),
                ("33%", "citam segurança em uma das duas menções"),
            ],
            "amber",
        ),
        (
            "datafolha_08102026",
            "Datafolha · 08/10/2026",
            "A escolha é firme.",
            "A renda pesa.",
            "<b>A íntegra abre as bases.</b> Transferências agregadas da terceira via, voto por segmento, motivação, rejeição e aprovação. Uma base por pergunta, uma fonte por afirmação.",
            [
                ("46 × 32", "terceira via / Flávio × Lula / grupo declarado"),
                ("92,8%", "voto firme reexpresso no total da amostra"),
                ("2.398", "base ponderada com renda / de 2.520"),
            ],
            "blue",
        ),
        (
            "nexus_btg_18102026",
            "BTG/Nexus · 19/10/2026",
            "Bases firmes.",
            "Placar apertado.",
            "<b>A íntegra de 128 páginas.</b> Renda atual, retenção das bases, presença declarada e escala 6x1. Onze perguntas por segmento, com fontes e limites.",
            [
                ("46,5 × 45,9", "Flávio × Lula / intenção no total"),
                ("92,9%", "presença certa ou provável / declarada"),
                ("66,2%", "aprovam o fim da escala 6x1 / formulação da pesquisa"),
            ],
            "amber",
        ),
    ]:
        data = json.loads((root / "docs/assets" / (slug + "_data.json")).read_text())
        if slug == "datafolha_08102026":
            stats[1] = (
                f'{data["denominators"]["certain_all_pct"]:.1f}%'.replace(".", ","),
                stats[1][1],
            )
        output.append(
            {
                "slug": slug,
                "eyebrow": name + " · 2º turno",
                "title": title,
                "title_em": emphasis,
                "lede": description,
                "stats": stats,
                "foot": "leitura de pesquisa · percentuais publicados e contas derivadas identificados",
                "accent": accent,
            }
        )
    return output
