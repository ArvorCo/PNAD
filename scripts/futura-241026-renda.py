#!/usr/bin/env python3
"""Futura de 24/10: publicado confirmado, sem presumir renda ausente."""

import importlib
from pathlib import Path

COMMON = importlib.import_module("pesquisas-081026-renda")
ROOT = Path(__file__).resolve().parents[1]


def poll():
    refs = COMMON.archive("futura_102026_24")
    note = (
        "Divulgação CNN às 20h32 e Exame às 20h35 de 24/10. Campo efetivo "
        "23–24/10 informado por ambas, n=2.000, CATI, BR-09726/2026. "
        "Totais F/L/BN/I 48,2/47,9/2,3/1,6; válidos oficiais 50,1/49,9 "
        "preservados separadamente da normalização dos totais arredondados. "
        "PDF de oito páginas localizado no catálogo da CNN: perfil na p. 3, "
        "totais na p. 4 e válidos na p. 5, sem voto por renda; somente "
        "publicado na Projeção, sem transportar perfil anterior. Exame cita "
        "51,5% para Flávio na comparação anterior, mas a íntegra de 21/10 "
        "arquivada registra 51,1%; não alterar a onda anterior."
    )
    return {
        "id": "futura_2026-10-24",
        "instituto": "Futura",
        "registro_tse": "BR-09726/2026",
        "contratante": "100% Cidades",
        "campo": {"inicio": "2026-10-23", "fim": "2026-10-24"},
        "divulgacao": "2026-10-24",
        "n": 2000,
        "metodo": "telefônico CATI",
        "publicado": {
            "2t": {"flavio": 48.2, "lula": 47.9, "branco_nulo": 2.3, "indecisos": 1.6}
        },
        "publicado_validos": {"2t": {"flavio": 50.1, "lula": 49.9}},
        "fonte": {
            **COMMON.source(refs, "Futura_24102026.pdf"),
            "tipo": "relatorio",
            "rotulo": "Futura: relatório de 24/10, pp. 2–5",
            "conferido_em": "2026-10-24",
            "status": "Relatório conferido visualmente; voto por renda não publicado.",
            "nota": note,
            "complementos": [
                {
                    **COMMON.source(refs, "exame.html.gz"),
                    "rotulo": "Exame: divulgação e registro",
                },
                {
                    **COMMON.source(refs, "cnn.html.gz"),
                    "rotulo": "CNN: válidos, campo, amostra e registro",
                },
            ],
        },
        "ignorar": True,
        "cruzamentos": {},
        "motivo": "Relatório publica perfil de renda, mas não voto por faixa; somente publicado na Projeção.",
    }


def main():
    p = poll()
    COMMON.write(ROOT / "analysis/reponderacao/pesquisas/futura_2026-10-24.json", p)
    audit = {
        "data": "2026-10-24",
        "pesquisas": [p],
        "consultado_em": COMMON.read(
            ROOT / "data/originals/futura_102026_24/fonte.json"
        )["consultado_em"],
        "busca": "Futura confirmada após Quaest e Atlas; CNN publicou às 20h32, Exame às 20h35. Nenhum novo resultado nacional posterior de Veritá, Phoenix ou Simplex confirmado neste corte. Relatório de oito páginas localizado no catálogo público de mídias da CNN às 20h30: perfil de renda familiar 28,7/20,4/25,1/9,1/5,4 e NS/NR 11,3 (p. 3), sem voto por faixa. Os dois PDFs Datafolha recém-incluídos no Poder360 são impressões de matérias Folha/G1, sem bases ponderadas atuais; não resolvem a prévia. Registro ou agenda não equivalem a resultado publicado.",
        "regra": "Substitui apenas a última onda Futura na Projeção. Sem renda atual, fora da Média. Quaest mantém o likely voter oficial sem nova seleção de presença.",
    }
    for path in [
        "analysis/reponderacao/auditoria_futura_20261024.json",
        "docs/assets/reponderacao_futura_20261024.json",
    ]:
        COMMON.write(ROOT / path, audit)
    path = ROOT / "analysis/reponderacao/historico_2t/presenca.json"
    presence = COMMON.read(path)
    presence["auditoria_ultima_onda"] = [
        p for p in presence["auditoria_ultima_onda"] if p["instituto"] != "Futura"
    ] + [
        {
            "instituto": "Futura",
            "id": p["id"],
            "tipo": "neutro",
            "fonte": p["fonte"]["url"],
            "arquivo": p["fonte"]["arquivo"],
            "nota": "Sem cruzamento de presença incorporado nesta onda; não transportar taxas anteriores. Relatório atual sem cruzamento de presença.",
        }
    ]
    COMMON.write(path, presence)


if __name__ == "__main__":
    main()
