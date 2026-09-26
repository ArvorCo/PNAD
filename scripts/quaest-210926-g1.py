#!/usr/bin/env python3
"""Integra os prints fornecidos pelo usuário e as cotas atuais BR-06004/2026.

Transcrição visual da coluna 21/09. As séries sobrepostas de candidatos menores
e as duas linhas cinza sem legenda no recorte não são imputadas por resíduo.
"""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "docs/fontes/quaest_21092026"
URL = "https://g1.globo.com/politica/eleicoes/2026/pesquisa-eleitoral/presidente-1-turno-quaest/"
OPTIONS = ["lula", "flavio", "cury", "caiado"]
PUBLISHED = [37, 33, 6, 4]
ROWS = [[49, 23, 4, 4], [34, 33, 6, 4], [29, 41, 8, 4]]
PROFILE = [31, 42, 27]


def main():
    target = ROOT / "analysis/reponderacao/pesquisas/quaest_2026-09-20.json"
    if (
        target.exists()
        and json.loads(target.read_text())["fonte"]["tipo"] == "relatorio"
    ):
        print("Íntegra já integrada; fonte parcial não sobrescreve o relatório.")
        return
    registry = (FOLDER / "registro-tse.txt").read_text()
    for text in [
        "BR-06004/2026",
        "17/09/2026",
        "20/09/2026",
        "(31%)",
        "(42%)",
        "(27%)",
    ]:
        assert text in registry, text
    old = json.loads(
        (ROOT / "analysis/reponderacao/pesquisas/quaest_2026-09-13.json").read_text()
    )
    poll = {k: old[k] for k in ["instituto", "contratante", "metodo"]}
    note = (
        "Prints do G1 enviados pelo usuário em 21/09 e cotas do registro atual. "
        "O ajuste pressupõe perfil ponderado final de 31/42/27, ainda não conferido na íntegra. "
        "As cotas recompõem Lula 37,30 e Flávio 32,06, contra 37 e 33 publicados; "
        "o resíduo de 0,94 ponto em Flávio permanece documentado. "
        "A fórmula parte do placar publicado e acrescenta somente o delta da troca de renda. "
        "Cruzamentos incorporados: Lula, Flávio, Cury e Caiado. Séries menores sobrepostas e "
        "linhas cinza sem legenda no recorte não foram imputadas. Esta onda não entra na "
        "decomposição dos demais candidatos em grupos. Segundo turno ainda sem cruzamento arquivado."
    )
    poll.update(
        id="quaest_2026-09-20",
        registro_tse="BR-06004/2026",
        campo={"inicio": "2026-09-17", "fim": "2026-09-20"},
        divulgacao="2026-09-21",
        n=2004,
        fonte={
            "tipo": "capturas_fornecidas_usuario",
            "rotulo": "Quaest · G1 (prints, 1º turno)",
            "url": URL,
            "pdf": None,
            "paginas": {},
            "arquivo": "docs/assets/quaest_210926_fontes.json",
            "localizador": "Coluna 21/09 dos quatro prints: geral e três faixas de renda",
            "status": "Fonte parcial: G1 + cotas registradas no TSE.",
            "nota": note,
            "complementos": [
                {
                    "url": f"fontes/quaest_21092026/{p.name}",
                    "rotulo": p.stem.replace("g1-", "Print "),
                }
                for p in sorted(FOLDER.glob("*.png"))
            ]
            + [
                {
                    "url": "fontes/quaest_21092026/registro-tse.txt",
                    "rotulo": "Registro BR-06004/2026",
                }
            ],
        },
        renda={
            "unidade": "salarios_minimos",
            "ano_referencia": 2026,
            "faixas": old["renda"]["faixas"],
            "amostra_pct": PROFILE,
            "perfil_tipo": "cota_registrada",
            "nota": "Cotas atuais, não bases brutas nem perfil final confirmado: 31/42/27. "
            "Registro cita PNADC anual 2025, visita 1. Sensibilidade condicionada à aplicação "
            "dessas cotas ao perfil ponderado final. Referência Arvor: pessoas 16+ na PNAD anual 2025.",
        },
        publicado={"1t": dict(zip(OPTIONS, PUBLISHED, strict=True))},
        cruzamentos={
            "1t": {
                "opcoes": OPTIONS,
                "linhas": ROWS,
                "nota": "Transcrição visual da coluna 21/09. Tabela parcial de quatro candidatos; "
                "linhas não somam 100 e não são renormalizadas. Não há imputação dos nomes omitidos.",
            }
        },
        sem_cruzamento={
            "2t": "21/09: ainda sem cruzamento de renda do 2º turno no acervo; "
            "a série reponderada desse turno continua na onda de 14/09. Fonte parcial do 1º turno "
            "usa cotas registradas 31/42/27, condicionadas à confirmação do perfil final."
        },
        notas=note,
    )
    target.write_text(json.dumps(poll, ensure_ascii=False, indent=2) + "\n")
    manifest = {
        "registro_tse": poll["registro_tse"],
        "origem": "Quatro imagens fornecidas pelo usuário",
        "url_indicada": URL,
        "recebido_em": "2026-09-21",
        "coluna": "21/09",
        "opcoes": OPTIONS,
        "publicado": PUBLISHED,
        "renda": ROWS,
        "cotas_registradas_pct": PROFILE,
        "recomposto": {
            k: round(sum(w * r[j] for w, r in zip(PROFILE, ROWS, strict=True)) / 100, 2)
            for j, k in enumerate(OPTIONS)
        },
        "nota": note,
        "arquivos": [
            {"arquivo": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
            for p in sorted(FOLDER.iterdir())
            if p.suffix in {".png", ".txt"}
        ],
    }
    (ROOT / "docs/assets/quaest_210926_fontes.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )
    print(target.relative_to(ROOT))


if __name__ == "__main__":
    main()
