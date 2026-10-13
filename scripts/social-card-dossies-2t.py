"""Cards dos dossiês de outubro, com dados da auditoria corrente."""

import json


def cards(root):
    output = []
    for slug, name, title, emphasis, description, stats, accent in [
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
    ]:
        data = json.loads((root / "docs/assets" / (slug + "_data.json")).read_text())
        if slug.startswith("datafolha"):
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
