#!/usr/bin/env python3
"""Integra a Veritá de 17/10 a partir do relatório fornecido, sem fonte viva."""

import importlib
from pathlib import Path

COMMON = importlib.import_module("pesquisas-081026-renda")
PREVIOUS = importlib.import_module("pesquisas-131026-renda")
ROOT = Path(__file__).resolve().parents[1]
DAY = "2026-10-17"
FOLDER = "verita_102026_17"


def verita():
    note = (
        "Relatório fornecido pelo usuário, arquivo de 13 páginas, com saltos na "
        "numeração impressa. Campo 12–16/10, 15.554 entrevistas, BR-01107/2026. "
        "P. 4 do PDF: renda familiar 42,7/38,6/18,7, frequências 6.635/6.010/2.909, "
        "sem não resposta na tabela. O relatório não explicita se esse perfil "
        "é anterior ou posterior à ponderação; a troca da margem publicada "
        "é sensibilidade condicional. P. 9 do PDF (impressa 13): "
        "49,7/47,7/1,5/1,1 no total (Flávio/Lula/branco-nulo/NS-NR). "
        "O grupo «Ausente» de 2,6% é o subtotal de branco/nulo e NS/NR, "
        "não abstenção nem categoria adicional. Válidos publicados 51,1/48,9 "
        "permanecem separados da normalização dos totais arredondados. "
        "As frequências dos dois candidatos somam 15.151, contra subtotal "
        "15.152 no PDF; preservam-se os percentuais, sem fabricar precisão "
        "a partir dessa diferença de uma unidade. P. 10 do PDF (impressa 14) "
        "traz voto por renda e sexo sobre o total de cada grupo. Renda: "
        "43,3/53,4/1,6/1,7; 55,4/43,0/1,2/0,4; 52,8/44,4/1,6/1,2. "
        "Recomposições independentes por renda e sexo conferidas. "
        "Voto lembrado do primeiro turno e expectativa de vitória são "
        "perguntas separadas e não entram na intenção atual."
    )
    poll = PREVIOUS.base(
        "verita_2026-10-16",
        "Veritá",
        "BR-01107/2026",
        ("2026-10-12", "2026-10-16"),
        DAY,
        15554,
        "telefônico automatizado URA, reconhecimento de voz e transcrição de áudio",
        FOLDER,
        {
            "metodologia": [2, 3],
            "perfil_renda": 4,
            "2t_topline": 9,
            "2t_validos": 9,
            "2t_renda": 10,
            "sexo": 10,
        },
        13,
        [49.7, 47.7, 1.5, 1.1],
        note,
    )
    poll["fonte"].update(
        conferido_em=DAY,
        rotulo="Relatório Veritá fornecido: cópia preservada",
        status="Relatório arquivado e conferido visualmente.",
        paginas_impressas={"2t_topline": 13, "2t_renda": 14, "sexo": 14},
        complementos=[
            {
                **COMMON.source(COMMON.archive(FOLDER), "divulgacao.html"),
                "rotulo": "CNN: divulgação da Veritá em 17/10",
            }
        ],
    )
    poll["publicado_validos"] = {"2t": {"flavio": 51.1, "lula": 48.9}}
    PREVIOUS.income(
        poll,
        [2, 5, None],
        [42.7, 38.6, 18.7],
        [[43.3, 53.4, 1.6, 1.7], [55.4, 43, 1.2, 0.4], [52.8, 44.4, 1.6, 1.2]],
        [[58.9, 38.7, 1.6, 0.7], [41.6, 55.7, 1.3, 1.5]],
        [47.2, 52.8],
        note,
    )
    poll["renda"].update(
        perfil_tipo="perfil_publicado",
        frequencias_publicadas=[6635, 6010, 2909],
        rotulos_originais=[
            "Abaixo de 2 salários mínimos",
            "Entre 2 e 5 salários mínimos",
            "Acima de 5 salários mínimos",
        ],
    )
    poll["conferencia_denominadores"] = {
        "pagina_pdf": 9,
        "pagina_impressa": 13,
        "frequencias_publicadas": {
            "flavio": 7735,
            "lula": 7416,
            "branco_nulo": 227,
            "indecisos": 175,
        },
        "subtotal_candidatos_publicado": 15152,
        "subtotal_ausente_pct": 2.6,
        "ausente_e_subtotal_bn_ns_nr": True,
        "abstencao_2t_medida": False,
    }
    return poll


def main():
    poll = verita()
    COMMON.write(
        ROOT / "analysis/reponderacao/pesquisas" / (poll["id"] + ".json"), poll
    )
    inventory = {
        "data": DAY,
        "pesquisas": [poll],
        "fontes": {FOLDER: COMMON.archive(FOLDER)},
        "varredura": [
            {
                "instituto": "Veritá",
                "status": "Nova onda com renda nas duas centrais",
                "conclusao": poll["fonte"]["nota"],
                "fontes": [poll["fonte"]["url"]],
                "pendente": False,
            }
        ],
    }
    COMMON.write(ROOT / "analysis/reponderacao/auditoria_20261017.json", inventory)
    COMMON.write(ROOT / "docs/assets/reponderacao_20261017.json", inventory)
    print("Veritá de 17/10: perfil e voto por renda conferidos.")


if __name__ == "__main__":
    main()
