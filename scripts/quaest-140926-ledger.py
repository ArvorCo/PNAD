"""Inventário do instrumento registrado, com estados documentais distintos."""

import re

import fitz

TITLES = {
    1: "Elegibilidade eleitoral",
    2: "Sexo",
    3: "Idade",
    4: "Escolaridade",
    5: "Ocupação",
    6: "Renda domiciliar",
    7: "Gravação e controle",
    8: "Voto espontâneo",
    9: "Potencial: Clariana",
    10: "Potencial: Edmilson",
    11: "Potencial: Cury",
    12: "Potencial: Flávio",
    13: "Potencial: Hertz",
    14: "Potencial: Lula",
    15: "Potencial: Marçal",
    16: "Potencial: Renan",
    17: "Potencial: Caiado",
    18: "Potencial: Rui",
    19: "Potencial: Samara",
    20: "Potencial: Grassi",
    21: "Potencial: Zema",
    22: "1º turno com Marçal",
    23: "1º turno sem Marçal",
    24: "Voto definitivo ou mutável",
    25: "2º turno: Cury",
    26: "2º turno: Flávio",
    27: "2º turno: Renan",
    28: "2º turno: Caiado",
    29: "2º turno: Zema",
    30: "Aprovação",
    31: "Avaliação",
    32: "Preocupação",
    33: "Interesse na eleição",
    34: "Melhor resultado",
    35: "Medo",
    36: "Expectativa de vencedor",
    37: "Honestidade: Lula",
    38: "Honestidade: Flávio",
    39: "Honestidade: Caiado",
    40: "Honestidade: Zema",
    41: "Honestidade: Renan",
    42: "Honestidade: Cury",
    43: "Confiança: STF",
    44: "Confiança: Presidência",
    45: "Confiança: Congresso",
    46: "Conhecimento: Master",
    47: "Imagem afetada: Master",
    48: "Conhecimento: conflito no STF",
    49: "Quem age corretamente no conflito",
    50: "Efeito declarado da crise sobre o voto",
    51: "STF: mandato fixo",
    52: "STF: indicações por outros poderes",
    53: "STF: decisões individuais",
    54: "STF: código de ética",
    55: "STF: requisitos de nomeação",
    56: "STF: quarentena política",
    57: "Identificação política",
    58: "Discussões familiares em 2022 e 2026",
    59: "Liberdade para expressar o voto",
    60: "Fonte de informação política",
    61: "Exposição ao horário eleitoral",
    62: "Religião",
    63: "Bolsa Família",
    64: "Cor/raça",
    65: "Voto recordado em 2022",
    66: "Comparecimento em 2024",
}
PAGES = {
    2: 196,
    3: 197,
    4: 198,
    6: 199,
    8: 6,
    24: 85,
    25: 37,
    26: 28,
    27: 55,
    28: 46,
    29: 64,
    30: 154,
    31: 164,
    32: 174,
    33: 133,
    34: 106,
    35: 96,
    36: 122,
    57: 194,
    60: 184,
    61: 144,
    62: 200,
    63: 203,
    64: 202,
    66: 204,
}
PAGES.update({i: 75 for i in range(9, 22) if i != 15})
# Fontes efetivamente conferidas; não é um censo de toda a internet.
EXTERNAL = {
    43: "g1-reformas",
    47: "g1-reformas",
    50: "g1-stf",
    51: "g1-reformas",
    52: "g1-reformas",
    54: "g1-reformas",
    55: "g1-reformas",
}


def extract(path):
    """Localiza cabeçalhos numerados em ordem, evitando códigos de resposta."""
    doc = fitz.open(path)
    alltext = []
    locations = []
    pos = 0
    for i, p in enumerate(doc, 1):
        t = p.get_text()
        alltext.append(t)
        locations.append((pos, i))
        pos += len(t) + 1
    text = "\n".join(alltext)
    marks = []
    start = 0
    for q in range(1, 67):
        pattern = rf"(?m)^\s*{q}\.\s+" + ("" if 25 <= q <= 29 else "(?=[A-ZÁÉÍÓÚÃÕÇ(])")
        match = re.search(pattern, text[start:])
        if not match:
            raise ValueError(f"Q{q} não encontrada")
        a = start + match.start()
        marks.append((q, a))
        start = start + match.end()
    out = []
    for idx, (q, a) in enumerate(marks):
        b = marks[idx + 1][1] if idx + 1 < len(marks) else text.find("ANEXO", a + 100)
        if b < 0:
            b = len(text)
        page = max(p for off, p in locations if off <= a)
        status = "Não localizado no PDF; divulgação externa não esgotada"
        if q in [1, 5, 7]:
            status = (
                "Cadastro, perfil ocupacional ou controle; sem resultado próprio no PDF"
            )
        if q in PAGES:
            status = "Resultado no PDF"
        if q in EXTERNAL:
            status = "Divulgado fora do PDF eleitoral"
        if q == 22:
            status = "Cenário com Marçal sem resultado próprio no PDF"
        if q == 23:
            status = "Lista compatível; renumerada como cenário 1 no PDF"
        out.append(
            {
                "question": q,
                "title": TITLES[q],
                "questionnaire_page": page,
                "report_page": PAGES.get(q, 16 if q == 23 else None),
                "status": status,
                "external": EXTERNAL.get(q),
                "registered_block": (
                    doc[7].get_text() if 25 <= q <= 29 else text[a:b].strip()
                ),
            }
        )
    assert len(out) == 66 and len(PAGES) == 37
    return out
