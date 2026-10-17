#!/usr/bin/env python3
"""Revisa a onda Datafolha de 15/10 com a íntegra oficial publicada em 16/10."""

import importlib
from pathlib import Path

COMMON = importlib.import_module("pesquisas-081026-renda")
PREVIOUS = importlib.import_module("pesquisas-131026-renda")
INITIAL = importlib.import_module("pesquisas-151026-renda")
ROOT = Path(__file__).resolve().parents[1]
FOLDER = "datafolha_102026_15_integra"


def datafolha():
    poll = INITIAL.datafolha()
    initial_source = poll["fonte"]
    note = (
        "Íntegra oficial de 42 páginas, publicada pelo Datafolha em 16/10. "
        "Campo 13–14/10, 2.520 entrevistas em 153 municípios, BR-00466/2026. "
        "P. 25 (anexo p. 3) declara que as bases dos recortes são ponderadas. "
        "P. 30 (anexo p. 8): renda até 2 SM, mais de 2 a 5 SM e mais de 5 SM, "
        "bases 1.172/918/335; F/L/BN/indecisos: 38/53/6/2, 55/40/4/1, 59/34/6/1. "
        "Ajuste limitado a 2.425/2.520 da amostra; 95 sem renda conservam o "
        "topline, sem preferência imputada. Sexo e região recompostos como "
        "controles independentes, com arredondamentos preservados. Não são "
        "usados os cruzamentos antigos da API G1. Revisão documental da onda "
        "de 15/10, não uma nova pesquisa. As duas ondas Datafolha pós-urna "
        "agora têm PNAD na tendência; a troca entre ajustado e publicado "
        "deixa de contaminar essa comparação."
    )
    poll.pop("ignorar")
    poll.pop("motivo")
    poll.pop("cruzamentos_documentais")
    poll["contratante"] = "Folha de S.Paulo (ficha técnica da íntegra)"
    poll["fonte"] = PREVIOUS.source(
        FOLDER,
        {
            "metodologia": [2, 25],
            "perfil_renda": 27,
            "2t_topline": 8,
            "2t_renda": 30,
            "sexo": 30,
            "regiao": 30,
            "2t_validos": 9,
        },
        42,
        note,
    )
    poll["fonte"].update(conferido_em="2026-10-16", publicado_em="2026-10-16")
    poll["fonte"]["complementos"] = [
        {
            **COMMON.source(COMMON.archive(FOLDER), "datafolha.html"),
            "rotulo": "Datafolha: divulgação oficial com link para a íntegra",
        },
        {k: initial_source[k] for k in ("arquivo", "url", "sha256", "rotulo")},
    ]
    bases = [1172, 918, 335]
    PREVIOUS.income(
        poll,
        [2, 5, None],
        bases,
        [[38, 53, 6, 2], [55, 40, 4, 1], [59, 34, 6, 1]],
        [[53, 41, 5, 0], [41, 49, 6, 3]],
        [1242, 1278],
        note,
        100 * sum(bases) / poll["n"],
    )
    poll["renda"]["bases"] = bases
    poll["renda"]["nao_publicada_n"] = 95
    poll["controles"]["2t"]["regiao"] = PREVIOUS.control(
        poll["publicado"]["2t"],
        [[51, 41, 6, 2], [57, 35, 6, 2], [32, 61, 6, 2], [54, 40, 4, 2]],
        [1061, 362, 689, 407],
    )
    return poll


def main():
    poll = datafolha()
    COMMON.write(
        ROOT / "analysis/reponderacao/pesquisas" / (poll["id"] + ".json"), poll
    )
    print("Datafolha de 15/10: renda atual conferida e incorporada.")


if __name__ == "__main__":
    main()
