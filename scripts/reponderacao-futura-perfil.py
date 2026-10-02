"""Publica a comparação de composição da Futura, sem atribuir efeito sobre voto."""

import json
from pathlib import Path

ASSETS = Path(__file__).resolve().parents[1] / "docs/assets"


def number(value):
    return f"{value:.1f}".replace(".", ",")


def section_html(table):
    data = json.loads((ASSETS / "futura_20260930_perfil_pnad.json").read_text())
    raw = data["futura_renda_total_amostra"]
    declared = data["futura_renda_entre_declarantes"]
    target = data["pnad_renda"]["pessoas16_efetivo"]
    low, ref = sum(raw[:2]), sum(target[:2])
    labels = ["Até 1 SM", "De 1 a 2 SM", "De 2 a 5 SM", "De 5 a 10 SM", "Mais de 10 SM"]
    rows = [
        [label, number(a) + "%", number(b) + "%", number(c) + "%"]
        for label, a, b, c in zip(labels, raw, declared, target, strict=True)
    ]
    rows.append(
        [
            "Não declarou renda",
            number(data["futura_sem_renda"]) + "%",
            "Não se aplica",
            "Não se aplica",
        ]
    )
    demo_labels = {
        "genero": {"feminino": "Mulheres", "masculino": "Homens"},
        "idade": {
            "16_24": "16–24 anos",
            "25_34": "25–34 anos",
            "35_44": "35–44 anos",
            "45_59": "45–59 anos",
            "60_mais": "60 anos ou mais",
        },
        "regiao": {
            "norte": "Norte",
            "nordeste": "Nordeste",
            "sudeste": "Sudeste",
            "sul": "Sul",
            "centro_oeste": "Centro-Oeste",
        },
    }
    demographic = []
    for dimension, groups in demo_labels.items():
        for key, label in groups.items():
            pn = data["outros_perfis_pnad16mais"][dimension][key]
            delta = data["diferencas_demograficas_pp"][dimension][key]
            demographic.append(
                [
                    label,
                    number(pn + delta) + "%",
                    number(pn) + "%",
                    ("+" if delta > 0 else "") + number(delta) + " pp",
                ]
            )
    return (
        '<section id="futura-perfil-pnad" class="chapter"><div class="wrap">'
        '<p class="eyebrow">Futura · BR-01122/2026 · perfil da página 7</p>'
        "<h2>A distância entre a amostra e a PNAD 2025</h2>"
        f"<p><b>{number(low)}% da amostra declara renda de até dois salários mínimos, contra {number(ref)}% na PNAD: "
        f"{number(low-ref)} pontos percentuais a mais.</b> Mesmo se todos os 10% sem renda declarada estiverem "
        "acima de dois salários, esse excesso permanece. É uma diferença de composição; não são pontos de voto para qualquer candidato.</p>"
        + table(
            [
                "Renda familiar",
                "Futura: amostra inteira",
                "Futura: entre declarantes",
                "PNAD 2025, 16+",
            ],
            rows,
        )
        + '<p class="note">A coluna entre declarantes divide cada faixa por 89,9%, a soma das rendas conhecidas. '
        "Ela descreve somente quem respondeu; não atribui renda aos ausentes. Os percentuais publicados, com NS/NR, somam 99,9% por arredondamento.</p>"
        f"<p>Entre declarantes, a concentração até dois salários chega a <b>{number(sum(declared[:2]))}%</b>, "
        f"{number(sum(declared[:2])-ref)} pontos acima da referência. Na faixa até um salário, os {number(raw[0])}% "
        f"da amostra inteira já superam o dobro dos {number(target[0])}% da PNAD. "
        f'Com renda habitual, a PNAD registra {number(sum(data["pnad_renda"]["pessoas16_habitual"][:2]))}% até dois salários; a conclusão permanece.</p>'
        "<details><summary>Gênero, idade e região: comparação completa com a PNAD</summary>"
        + table(
            ["Recorte", "Futura", "PNAD 2025, 16+", "Futura menos PNAD"], demographic
        )
        + '<p class="note">Para calibração eleitoral de idade, gênero e região, a referência adequada é o TSE. '
        "PNAD 16+ representa população, não o cadastro eleitoral. Escolaridade exige harmonizar completas, incompletas e sem instrução; "
        "religião não está na base PNADC utilizada.</p></details>"
        "<p><b>O que ainda falta:</b> a íntegra de 46 páginas, conferida em 02/10, confirma a ficha técnica "
        "e os mesmos percentuais dos prints, mas não identifica se o perfil é bruto ou ponderado e não traz voto por renda. "
        "Não se pode converter esse desvio em correção do placar nem concluir que os pesos finais preservam a composição mostrada.</p>"
        '<p class="note">Régua: PNADC anual 2025, visita 1; pessoas 16+, peso V1032, rendimento domiciliar efetivo VD5001. '
        "Faixas em salários mínimos de 2026, convertidas aos preços de abril de 2026 com o IPCA disponível até julho de 2026. "
        "A comparação é descritiva, sem teste de significância; não confundir renda familiar declarada com renda domiciliar medida. "
        '<a href="assets/futura_20260930_perfil_pnad.json">Baixar cálculos completos</a> · '
        '<a href="assets/futura_20260930_prints.json">Transcrição e fontes dos prints</a> · '
        '<a href="https://static.poder360.com.br/uploads/2026/09/futuracidadeparticipacoesBR-30set2026.pdf">Íntegra de 46 páginas</a>.</p>'
        "</div></section>"
    )
