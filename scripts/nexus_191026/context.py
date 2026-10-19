"""Agenda, economia e motivação: transcrição visual das figuras da 18ª rodada."""

from dossies_2t_2026 import view as v

SPECIAL = {
    "motivation": {
        "pages": [54, 55],
        "universe": "Dentro do eleitorado declarado de cada candidato",
        "rows": {
            "Eleitores de Lula": [80.2, 12, 7.8],
            "Eleitores de Flávio": [72.1, 21, 6.9],
        },
        "options": [
            "É o melhor candidato",
            "Apenas para derrotar o adversário",
            "NS/NR",
        ],
        "rejection_all_published": 15.3,
    },
    "issues": {
        "page": 114,
        "universe": "Total da amostra; soma de duas menções",
        "top8": {
            "Segurança pública": [17.9, 16.1, 34],
            "Saúde pública": [13.1, 18, 31.1],
            "Corrupção": [13.4, 4.1, 17.5],
            "Educação": [5, 10.6, 15.6],
            "Classe política": [9.2, 5.6, 14.8],
            "Inflação e custo de vida": [6.3, 5.8, 12.1],
            "Baixo crescimento": [6.5, 3.3, 9.8],
            "Desigualdade e pobreza": [4.5, 4.9, 9.4],
        },
    },
    "economy": {
        "current": {
            "page": 118,
            "options": ["Ótima/boa", "Regular", "Ruim/péssima", "NS/NR"],
            "rows": {
                "Economia do país": [17.1, 29.2, 51.1, 2.6],
                "Finanças pessoais": [31.6, 47.6, 18.7, 2],
            },
        },
        "past": {
            "page": 120,
            "options": ["Melhor", "Igual", "Pior", "NS/NR"],
            "rows": {
                "Economia do país": [38.5, 12.7, 44, 4.8],
                "Finanças pessoais": [42.6, 23.6, 30.6, 3.2],
            },
        },
        "future": {
            "page": 122,
            "options": ["Vai melhorar", "Ficar igual", "Vai piorar", "NS/NR"],
            "rows": {
                "Economia do país": [51.4, 16.2, 12.4, 20],
                "Finanças pessoais": [49.6, 28.4, 6.1, 15.9],
            },
        },
    },
}


def motivation(data, ref):
    item = data["special"]["motivation"]
    return v.details(
        "Motivação: escolha positiva e voto contra o adversário",
        v.stacks("Motivação dentro de cada eleitorado", item["rows"], item["options"])
        + "<p>12,0% dos eleitores de Lula e 21,0% dos de Flávio dizem votar apenas para derrotar o adversário. Reexpressos pelo tamanho atual de cada candidatura, são 45,9% × 12,0% + 46,5% × 21,0% = 15,27% do total, compatíveis com os 15,3% publicados.</p>"
        + v.note(
            "As barras são condicionais ao voto declarado; o rótulo de amostra total da p. 54 se aplica à agregação central. Motivação negativa não é indecisão nem probabilidade de mudar."
        )
        + ref(54, 55),
    )


def section(data, ref):
    issues, economy = data["special"]["issues"], data["special"]["economy"]
    body = (
        v.table(
            ["Problema", "1ª menção", "2ª menção", "Duas menções"],
            [
                [name, *[v.fmt(x) + "%" for x in values]]
                for name, values in issues["top8"].items()
            ],
        )
        + ref(114)
        + v.note(
            "Oito problemas mais citados, entre todas as categorias da fonte. Duas menções por pessoa; esta coluna não é uma partição de 100%. Na primeira menção, corrupção supera saúde; na soma das duas, saúde fica em segundo lugar."
        )
    )
    for key, title in [
        ("current", "Como está hoje"),
        ("past", "Em relação ao governo encerrado em 2022"),
        ("future", "Expectativa para os próximos seis meses"),
    ]:
        item = economy[key]
        body += (
            "<h3>"
            + title
            + "</h3>"
            + v.stacks(title, item["rows"], item["options"])
            + ref(item["page"])
        )
    body += v.note(
        "Avaliação presente, comparação com o governo anterior e expectativa futura não medem a mesma coisa. Os 51,4% que esperam melhora do país não são apoio declarado a uma candidatura. Não usamos essas respostas como votos adicionais nas centrais."
    )
    return v.section(
        5,
        "agenda",
        "O presente pesa. O futuro parece melhor.",
        "Segurança e saúde lideram as duas menções. Na economia, 51,1% avaliam mal o presente do país e 51,4% esperam melhora.",
        body,
    )
