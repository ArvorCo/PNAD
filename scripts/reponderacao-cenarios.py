"""Seleção auditável de cenários sem Marçal, preservando os manifestos originais.

Páginas são físicas (1-based) dos PDFs indicados em cada manifesto.
Valores publicados são mantidos, inclusive arredondamentos e traços como zero.
"""

from copy import deepcopy


def alternative(options, published, rows, pages, note):
    return {
        "publicado": dict(zip(options.split(), published, strict=True)),
        "cruzamento": {"opcoes": options.split(), "linhas": rows, "nota": note},
        "paginas": pages,
        "nota": note,
    }


ALTERNATIVES = {
    "datafolha_2026-09-02": alternative(
        "lula flavio cury caiado renan_santos zema samara edmilson rui grassi clariana hertz branco_nulo indecisos",
        [38, 33, 8, 4, 3, 2, 1, 1, 1, 0, 0, 0, 6, 3],
        [
            [45, 27, 5, 4, 2, 2, 1, 1, 1, 0, 0, 0, 7, 4],
            [32, 38, 10, 4, 4, 3, 1, 1, 0, 0, 0, 0, 5, 2],
            [27, 45, 11, 4, 5, 1, 0, 0, 0, 0, 0, 0, 5, 1],
        ],
        {"1t_topline": 37, "1t_renda": 38},
        "Situação B sem Marçal já usada no manifesto, mantida. A p. 38 individualiza os cinco nomes antes somados em outros. Traços convertidos em zero; bases 1011/666/241.",
    ),
    "datafolha_2026-08-19": alternative(
        "lula flavio caiado renan_santos zema cury samara rui edmilson grassi clariana hertz branco_nulo indecisos",
        [39, 33, 5, 4, 3, 2, 1, 1, 1, 1, 0, 0, 6, 4],
        [
            [46, 27, 4, 3, 2, 1, 2, 1, 1, 1, 1, 0, 7, 4],
            [30, 39, 8, 5, 3, 2, 1, 0, 0, 1, 0, 0, 6, 3],
            [33, 43, 7, 2, 5, 3, 1, 0, 1, 1, 0, 0, 3, 2],
        ],
        {"1t_topline": 36, "1t_renda": 37},
        "Situação B, sem Marçal. PDF pp. 36–37, tabela de renda com bases 1031/704/249. Traços convertidos em zero; menores individualizados, sem residual outros.",
    ),
    "realtime_2026-08-31": alternative(
        "lula flavio cury renan_santos caiado zema outros branco_nulo indecisos",
        [38, 30, 11, 7, 4, 2, 2, 3, 3],
        [
            [48, 26, 9, 3, 3, 1, 2, 4, 4],
            [31, 35, 12, 7, 5, 2, 2, 2, 3],
            [25, 31, 14, 14, 10, 4, 0, 1, 1],
        ],
        {"1t_topline": 15, "1t_renda": 18},
        "Cenário 02, sem Marçal, pp. 15/18. Outros agrega Clariana, Rui, Samara, Edmilson, Hertz e Grassi. Na faixa >5 SM a célula sem barra/rótulo vale zero, como no cenário 01. Perfil de renda idêntico ao cenário 01.",
    ),
    "quaest_2026-09-01": alternative(
        "lula flavio cury renan_santos caiado zema samara rui grassi clariana edmilson hertz indecisos branco_nulo",
        [37, 29, 10, 3, 1, 1, 1, 0, 0, 0, 0, 0, 11, 7],
        [
            [49, 16, 7, 3, 1, 1, 1, 0, 0, 0, 0, 0, 14, 8],
            [33, 33, 10, 3, 1, 1, 1, 0, 0, 0, 0, 0, 11, 7],
            [29, 39, 12, 3, 1, 2, 1, 0, 0, 0, 0, 0, 7, 6],
        ],
        {"1t_topline": 25, "1t_renda": 31},
        "Cenário 2, sem Marçal, pp. 25/31. Todas as células transcritas dos rótulos impressos, incluindo zeros dos candidatos menores.",
    ),
    "quaest_2026-09-06": alternative(
        "lula flavio cury outros indecisos branco_nulo",
        [36, 29, 8, 9, 10, 8],
        [[49, 18, 5, 7, 13, 8], [32, 33, 9, 8, 10, 8], [29, 39, 10, 9, 7, 6]],
        {"1t_topline": 26, "1t_renda": 32},
        "Cenário 2, sem Marçal, pp. 26/32, coluna 07/Set. Outros = Renan + Caiado + Zema + Samara (3+3+2+1 no total). Cury até 2 SM = 5, único rótulo ausente, obtido pelo resíduo da partição fechada de 100%; posição do ponto confirma. Demais células lidas dos rótulos impressos.",
    ),
    "gerp_2026-05-12": alternative(
        "flavio lula ciro zema caiado renan_santos aldo branco_nulo indecisos",
        [37, 35, 7, 6, 2, 1, 0, 6, 6],
        [
            [35, 36, 4, 6, 3, 0, 0, 9, 7],
            [32, 35, 5, 5, 1, 2, 0, 8, 11],
            [40, 33, 11, 5, 2, 2, 0, 4, 4],
            [41, 39, 9, 7, 1, 0, 0, 3, 1],
            [36, 30, 4, 8, 5, 2, 0, 9, 6],
            [38, 46, 7, 2, 3, 1, 0, 1, 2],
        ],
        {"1t_topline": 13, "1t_renda": 14},
        "Cenário 2, sem Marçal e sem Cury, pp. 13/14. Inclui Ciro e Aldo Rebelo; traços são zeros. Renda nas seis últimas colunas do segundo quadro da p. 14.",
    ),
}

# Marçal aparece dentro da categoria agregada, não como chave individual.
HIDDEN_MARCAL = {"mda_2026-09-13", "quaest_2026-09-06"}


def contains_marcal(poll):
    return (
        "marcal" in poll.get("publicado", {}).get("1t", {})
        or "marcal" in poll.get("cruzamentos", {}).get("1t", {}).get("opcoes", [])
        or poll["id"] in HIDDEN_MARCAL
    )


def select_first_round(poll, exclude_only_marcal=True):
    """Aplica somente uma alternativa documentada, sem alterar o segundo turno."""
    selected = deepcopy(poll)
    alt = ALTERNATIVES.get(poll["id"])
    if alt:
        selected["publicado"]["1t"] = deepcopy(alt["publicado"])
        selected["cruzamentos"]["1t"] = deepcopy(alt["cruzamento"])
        selected["fonte"].setdefault("paginas", {}).update(alt["paginas"])
        selected["selecao_1t"] = {"status": "alternativa_sem_marcal", **deepcopy(alt)}
    elif contains_marcal(poll):
        selected["selecao_1t"] = {
            "status": (
                "excluido_com_marcal"
                if exclude_only_marcal
                else "cenario_unico_com_marcal"
            ),
            "nota": "Relatório consultado não oferece alternativa sem Marçal com cruzamento de renda.",
        }
        if exclude_only_marcal:
            selected.get("cruzamentos", {}).pop("1t", None)
    return selected
