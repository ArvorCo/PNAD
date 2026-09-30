#!/usr/bin/env python3
"""Registra a nova Meio/Ideia e a reconferência da Futura, sem imputar renda."""

import hashlib
import importlib
import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "analysis/reponderacao"
WORK = BASE / "atualizacao_20260930"
TODAY = "2026-09-30"
PDF_URL = "https://www.canalmeio.com.br/wp-content/uploads/2026/09/Pesquisa-Meio_Ideia-Setembro2.pdf"
ARTICLE_URL = "https://www.canalmeio.com.br/2026/09/30/meio-ideia-o-primeiro-turno-mais-dificil-da-historia/"


def read(path):
    return json.loads(path.read_text())


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def meio():
    old = read(BASE / "pesquisas/meio_ideia_2026-09-07.json")
    poll = {
        k: deepcopy(old[k]) for k in ("instituto", "contratante", "metodo", "renda")
    }
    pdf = ROOT / "data/originals/meio_ideia_092026_30/relatorio.pdf"
    payload = pdf.read_bytes()
    assert payload.startswith(b"%PDF-")
    poll.update(
        id="meio_ideia_2026-09-28",
        campo={"inicio": "2026-09-25", "fim": "2026-09-28"},
        divulgacao=TODAY,
        registro_tse="BR-08706/2026",
        n=2000,
        fonte={
            "tipo": "relatorio",
            "pdf": str(pdf.relative_to(ROOT)),
            "url": PDF_URL,
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
            "total_paginas": 70,
            "conferido_em": TODAY,
            "status": "Íntegra pública arquivada; gráficos conferidos visualmente.",
            "paginas": {
                "metodologia": [2, 69],
                "1t_topline": 14,
                "2t_topline": 31,
                "2t_genero": 33,
                "2t_renda": 37,
            },
            "complementos": [
                {"url": ARTICLE_URL, "rotulo": "Divulgação de 30/09/2026"}
            ],
        },
        ignorar=True,
        motivo=(
            "Íntegra de 30/09, campo 25–28/09: o voto por renda do 2º turno está na p. 37, "
            "mas faltam bases ou percentuais da amostra nas quatro faixas. A metodologia "
            "da p. 69 chama condição de atividade de nível econômico (62% ativos, 38% não ativos); "
            "isso não informa a distribuição de renda. A p. 9 descreve somente os indecisos "
            "da pergunta espontânea, não a amostra inteira. O PDF não traz voto por renda "
            "do 1º turno. Os placares ficam documentados, fora das médias comparáveis e do "
            "modelo de válidos por renda. Essa falta documental não prova erro de ponderação."
        ),
        publicado={
            # Gráfico da p. 14: transcrição visual, todas as opções publicadas.
            "1t": dict(
                zip(
                    [
                        "lula",
                        "flavio",
                        "cury",
                        "renan_santos",
                        "caiado",
                        "zema",
                        "samara",
                        "clariana",
                        "hertz",
                        "grassi",
                        "avalanche",
                        "rui",
                        "edmilson",
                        "branco_nulo",
                        "indecisos",
                    ],
                    [
                        39.4,
                        38.4,
                        6.7,
                        4.5,
                        4.4,
                        3.5,
                        0.4,
                        0.3,
                        0.3,
                        0.1,
                        0.1,
                        0.1,
                        0.1,
                        0.7,
                        1.5,
                    ],
                    strict=True,
                )
            ),
            # Gráfico da p. 31, sem renormalizar o arredondamento de 100,1%.
            "2t": {"lula": 48.5, "flavio": 48.0, "branco_nulo": 2.1, "indecisos": 1.5},
        },
        cruzamentos={
            "2t": {
                "opcoes": ["lula", "flavio", "branco_nulo", "indecisos"],
                # P. 37, ordem: até 1 SM; 1–3; 3–5; mais de 5.
                "linhas": [
                    [55.4, 40, 2.5, 2.1],
                    [46.9, 49.8, 2, 1.3],
                    [47.2, 48, 2.8, 2],
                    [39.3, 59.4, 0.8, 0.4],
                ],
                "nota": "P. 37, transcrição visual preservada para auditoria; sem perfil da amostra, não se calcula reponderação.",
            }
        },
        notas="Divulgação confirmada na matéria do Canal Meio. Margem de erro do PDF: 2,2 pp; confiança 95%. O arquivo público anuncia cruzamentos adicionais para assinantes; eles não foram acessados.",
    )
    poll["renda"].update(
        mes_precos="202609",
        nota="A p. 37 define quatro faixas em SM, mas a íntegra não informa seus pesos na amostra. A p. 69 informa condição de atividade, que não substitui renda.",
    )
    return poll


def main():
    poll = meio()
    dump(BASE / f"pesquisas/{poll['id']}.json", poll)
    futura_path = BASE / "pesquisas/futura_2026-09-23.json"
    futura = read(futura_path)
    payload = (ROOT / futura["fonte"]["pdf"]).read_bytes()
    assert hashlib.sha256(payload).hexdigest() == futura["fonte"]["sha256"]
    futura["fonte"].update(
        conferido_em=TODAY,
        nota="O PDF da onda de 24/09 foi reconferido em 30/09 e é idêntico ao arquivado. Posteriormente, a nova rodada BR-01122/2026 foi localizada na biblioteca da Futura e recebida em oito prints, arquivados em ficha própria; não foi recebida uma íntegra em PDF.",
    )
    dump(futura_path, futura)
    new_futura, futura_data = importlib.import_module("futura-300926-prints").main()
    # P. 33: controle auxiliar com as proporções declaradas na p. 69.
    # São alvos de desenho, não bases observadas: esta conta não valida renda.
    rows = [[46.8, 50.6, 1.8, 0.7], [49.9, 45.6, 2.4, 2.2]]
    recomposed = [
        sum(w * r[i] for w, r in zip([0.47, 0.53], rows, strict=True)) for i in range(4)
    ]
    audit = {
        "data": TODAY,
        "fontes": [
            {
                "id": p["id"],
                "fonte": p["fonte"],
                "publicado": p["publicado"],
                "motivo": p["motivo"],
            }
            for p in [poll, futura, new_futura]
        ],
        "controle_auxiliar_meio": {
            "pagina_cruzamento": 33,
            "pagina_proporcoes_declaradas": 69,
            "pesos_declarados": [47, 53],
            "linhas": rows,
            "opcoes": ["lula", "flavio", "branco_nulo", "indecisos"],
            "recomposto": recomposed,
            "residuo_max_pp": max(
                abs(a - b)
                for a, b in zip(
                    recomposed, poll["publicado"]["2t"].values(), strict=True
                )
            ),
            "limite": "Conferência auxiliar por gênero usando alvos declarados, não bases observadas. Não identifica nem valida a composição de renda e não habilita a reponderação.",
        },
        "controles_auxiliares_futura": futura_data["controles"],
        "efeito": "Meio/Ideia e as duas ondas documentadas da Futura não têm ajuste por renda identificável nos materiais arquivados. Não alteram a composição elegível das médias ou do modelo de votos válidos.",
    }
    dump(WORK / "auditoria.json", audit)
    dump(ROOT / "docs/assets/reponderacao_20260930.json", audit)
    print(
        "Meio/Ideia registrada; Futura anterior reconferida e nova rodada arquivada por prints; sem ajuste por renda."
    )


if __name__ == "__main__":
    main()
