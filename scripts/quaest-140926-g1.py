#!/usr/bin/env python3
"""Build the Quaest partial-source record from archived g1 disclosures and TSE quotas."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "data/pesquisas/quaest/2026-09-14"
URL = "https://g1.globo.com/politica/eleicoes/2026/pesquisa-eleitoral/noticia/2026/09/14/2-turno-lula-e-flavio-bolsonaro-quaest-segmentos.ghtml"
# Visual transcription of the rightmost (14/9) column of g1-renda.jpg.
# All four options are labelled; no residual imputation or previous-wave votes.
ROWS = [[51, 32, 12, 5], [36, 46, 13, 5], [34, 47, 14, 5]]
PROFILE = [31, 42, 27]  # Current BR-03607/2026 sampling plan, directly inspected.
TSE_QUOTE = (
    "Renda domiciliar total, incluindo pensões, benefícios e rendimentos de trabalhos informais: "
    "Até 2 salários-mínimos (31%); Mais de 2 a 5 salários-mínimos (42%); Mais de 5 salários-mínimos (27%)."
)


def main():
    text = (FOLDER / "g1-segmentos.txt").read_text()
    assert "BR-03607/2026" in text and "51% x 32%" in text
    assert all(sum(row) == 100 for row in ROWS)
    assert sum(PROFILE) == 100
    old = json.loads(
        (ROOT / "analysis/reponderacao/pesquisas/quaest_2026-09-06.json").read_text()
    )
    poll = {key: old[key] for key in ["instituto", "contratante", "metodo"]}
    poll.update(
        id="quaest_2026-09-13",
        registro_tse="BR-03607/2026",
        campo={"inicio": "2026-09-10", "fim": "2026-09-13"},
        divulgacao="2026-09-14",
        n=2004,
    )
    poll["fonte"] = {
        "tipo": "materia",
        "rotulo": "Matéria do g1 (renda)",
        "pdf": None,
        "arquivo": str((FOLDER / "g1-segmentos.html").relative_to(ROOT)),
        "url": URL,
        "localizador": "Arte “2º turno: Lula x Flávio Bolsonaro - Renda”, coluna 14/9",
        "paginas": {},
        "status": "Fonte parcial: g1 + cotas registradas no TSE.",
        "nota": "Relatório completo não consultado. Os votos por renda são desta rodada; os pesos são as cotas declaradas no registro atual. A conta pressupõe sua aplicação ao perfil ponderado final, ainda não conferido.",
        "complementares": [
            {
                "tipo": "materia",
                "url": URL.replace(
                    "2-turno-lula-e-flavio-bolsonaro-quaest-segmentos",
                    "quaest-2-turno-setembro",
                ),
                "arquivo": str((FOLDER / "g1-placar.html").relative_to(ROOT)),
                "uso": "Placar geral: Lula 40, Flávio 42, B/N/não vai votar 13, indecisos 5.",
            },
            {
                "tipo": "registro_tse",
                "url": "https://pesqele-divulgacao.tse.jus.br/app/pesquisa/listar.xhtml",
                "identificacao": "BR-03607/2026",
                "consulta": "2026-09-14",
                "trecho": TSE_QUOTE,
                "uso": "Cotas desta rodada, campo, n, contratantes e metodologia; consulta direta à interface pública.",
            },
        ],
    }
    poll["renda"] = {
        "unidade": "salarios_minimos",
        "ano_referencia": 2026,
        "faixas": old["renda"]["faixas"],
        "amostra_pct": PROFILE,
        "perfil_tipo": "cota_registrada",
        "nota": "Cotas do registro BR-03607/2026, consultado em 14/09: 31% até 2 SM, 42% de mais de 2 a 5 SM, 27% acima de 5 SM. Não são contagens de campo nem distribuição final publicada. O plano cita PNADc anual 2025, 1ª visita. Cortes em salários de 2026, como rotulados no g1. O cálculo é condicionado à aplicação dessas cotas ao perfil final; relatório completo, pesos e tratamento de renda não declarada ainda não conferidos. Atualização exclusiva do segundo turno; não se reutiliza o cruzamento de primeiro turno de 7/9.",
    }
    poll["publicado"] = {
        "2t": dict(
            zip(
                ["lula", "flavio", "branco_nulo", "indecisos"],
                [40, 42, 13, 5],
                strict=True,
            )
        )
    }
    poll["cruzamentos"] = {
        "2t": {
            "opcoes": ["lula", "flavio", "branco_nulo", "indecisos"],
            "linhas": ROWS,
            "nota": "Transcrição visual da coluna 14/9 da arte de renda do g1, quatro opções por faixa; cada linha soma 100. Branco/nulo inclui não vai votar. Coluna 7/9 foi conferida contra a onda anterior, sem usar seus votos na rodada nova.",
        }
    }
    poll["notas"] = (
        "Fonte parcial explicitada no card e nas fichas do agregador. Conferir distribuição ponderada final quando a íntegra estiver disponível."
    )
    path = ROOT / "analysis/reponderacao/pesquisas/quaest_2026-09-13.json"
    path.write_text(json.dumps(poll, ensure_ascii=False, indent=2) + "\n")
    manifest = {
        "registro_tse": poll["registro_tse"],
        "fontes": poll["fonte"],
        "transcricao_renda": {
            "ordem": poll["cruzamentos"]["2t"]["opcoes"],
            "linhas": ROWS,
        },
        "arquivos": [
            {
                "arquivo": p.name,
                "bytes": p.stat().st_size,
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            }
            for p in sorted(FOLDER.iterdir())
            if p.suffix in {".html", ".txt", ".jpg"}
        ],
    }
    (FOLDER / "manifesto.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )
    (ROOT / "docs/assets/quaest_140926_fontes.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )
    print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
