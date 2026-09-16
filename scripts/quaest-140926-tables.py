"""Transcrições visuais conferidas nos PDFs de 07 e 14/09/2026.

OCR é apenas índice de busca. Percentuais abaixo preservam arredondamentos;
páginas são as do arquivo, começando em 1. Nenhuma célula é inferida por resíduo.
"""

PROFILE = [31, 42, 27]  # 14/09 p.199; 07/09 p.215
FIRST_OPTIONS = ["lula", "flavio", "cury", "outros", "indecisos", "branco_nulo"]
SECOND_OPTIONS = ["lula", "flavio", "branco_nulo", "indecisos"]
FIRST = [36, 31, 7, 9, 10, 7]  # 14/09 pp.16–17, sem Marçal
FIRST_INCOME = [
    [45, 22, 7, 7, 12, 8],
    [33, 34, 7, 10, 10, 7],
    [31, 38, 8, 9, 7, 7],
]  # p.22
SECOND = [40, 42, 13, 5]  # p.28
SECOND_INCOME = [[51, 32, 12, 5], [36, 46, 13, 5], [34, 47, 14, 5]]  # p.33
# Provas independentes; somente as duas candidaturas, sem imputar demais células.
SEX = {
    "weights": [53, 47],
    "1t": [[37, 29], [35, 33]],
    "2t": [[41, 38], [38, 47]],
    "pages": [19, 30, 196],
}
POLITICAL = {
    "weights": [19, 14, 32, 21, 12],
    "2t": [[96, 1], [89, 3], [26, 36], [2, 85], [0, 99]],
    "pages": [36, 194],
}
# A identificação política tem 2% NS/NR sem cruzamento: não é partição fechada.
TRANSFERS = [
    {"name": "Cury", "share": 7, "row": [25, 41, 7, 27]},
    {"name": "Renan", "share": 4, "row": [18, 50, 6, 26]},
    {"name": "Caiado", "share": 4, "row": [20, 46, 2, 32]},
    {"name": "Zema", "share": 1, "row": [38, 32, 0, 30]},
]  # p.27: destino Lula, Flávio, indecisos, B/N/não vota
HISTORY = {  # p.28; mesma dupla; pontos anteriores não pressupõem mesmo contratante.
    "dates": [
        "Jan",
        "Fev",
        "Mar",
        "Abr",
        "Mai",
        "Jun",
        "Jul",
        "05/08",
        "14/08",
        "02/09",
        "07/09",
        "14/09",
    ],
    "lula": [45, 43, 41, 40, 42, 44, 45, 44, 43, 42, 41, 40],
    "flavio": [38, 38, 41, 42, 41, 38, 37, 39, 40, 41, 41, 42],
    "branco_nulo": [15, 17, 16, 16, 14, 14, 14, 13, 13, 13, 13, 13],
    "indecisos": [2, 2, 2, 2, 3, 4, 4, 4, 4, 4, 5, 5],
}
# Série sem Marçal: p.27 no PDF de 07/09; pp.16–17 no PDF de 14/09.
FIRST_HISTORY = [[37, 29, 10, 6, 11, 7], [36, 29, 8, 9, 10, 8], FIRST]
ALTERNATIVES = [
    {
        "name": "Flávio",
        "page": 28,
        "income_page": 33,
        "published": SECOND,
        "income": SECOND_INCOME,
    },
    {
        "name": "Cury",
        "page": 37,
        "income_page": 42,
        "published": [38, 36, 21, 5],
        "income": [[49, 26, 19, 6], [36, 37, 22, 5], [30, 46, 20, 4]],
    },
    {
        "name": "Caiado",
        "page": 46,
        "income_page": 51,
        "published": [41, 39, 16, 4],
        "income": [[51, 25, 18, 6], [38, 40, 18, 4], [34, 51, 12, 3]],
    },
    {
        "name": "Renan",
        "page": 55,
        "income_page": 60,
        "published": [41, 38, 17, 4],
        "income": [[51, 26, 17, 6], [38, 40, 18, 4], [34, 48, 15, 3]],
    },
    {
        "name": "Zema",
        "page": 64,
        "income_page": 69,
        "published": [45, 33, 18, 4],
        "income": [[56, 19, 20, 5], [41, 37, 18, 4], [37, 43, 16, 4]],
    },
]
MOVEMENT = [  # indicador, Lula anterior/atual, Flávio anterior/atual, páginas
    ["Espontânea", 28, 28, 20, 23, 6],
    ["1º turno sem Marçal", 36, 36, 29, 31, 17],
    ["2º turno", 41, 40, 41, 42, 28],
    ["Conhece e poderia votar", 44, 45, 40, 43, 75],
    ["Rejeição", 53, 55, 55, 55, 75],
    ["Escolha definitiva entre seus eleitores", 80, 80, 78, 72, 94],
]
APPROVAL_INCOME = [[53, 38, 9], [39, 54, 7], [37, 58, 5]]  # p.159 aprova/desaprova/NS
BEST_RESULT = [32, 25, 16, 19, 8]  # p.106 Lula/família Bolsonaro/moderado/outsider/NS
BEST_FIRST = [
    [79, 3],
    [4, 81],
    [22, 24],
    [18, 26],
]  # p.115 Lula/Flávio; 8% NS excluídos
BEST_SECOND = [
    [85, 8, 5, 2],
    [3, 93, 2, 2],
    [25, 47, 22, 6],
    [24, 39, 29, 8],
]  # p.116 L/F/BN/NS
OLD_USEFUL = {
    "page": 164,
    "agree_total": 38,
    "agree_partial": 10,
    "wording": "O mais importante nesta eleição é votar em quem tem mais chance de derrotar o atual presidente.",
}
G1_STF = "https://g1.globo.com/politica/eleicoes/2026/noticia/2026/09/14/quaest-67percent-dizem-que-crise-no-stf-nao-influencia-voto-para-presidente.ghtml"
G1_REFORMS = "https://g1.globo.com/politica/eleicoes/2026/noticia/2026/09/14/crise-no-stf-maioria-defendem-aumentar-exigencias-para-nomeacao-de-ministros-do-supremo-mostra-pesquisa-quaest.ghtml"
PDF = "https://quaest.com.br/wp-content/uploads/2026/09/QUAEST4PRESIDENCIAL1409.pdf"
OLD_PDF = "https://quaest.com.br/wp-content/uploads/2026/09/QUAEST3PRESIDENCIAL0709.pdf"
