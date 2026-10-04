#!/usr/bin/env python3
"""Calibra o erro de pesquisa de governador com as pesquisas finais e a urna de 2022.

Reaproveita o calibrador do Senado (scripts/senado_2026/calibracao.py) com a
seção de governador das mesmas páginas da Wikipédia já arquivadas em
data/originals/senado_102026/wikipedia_2022/ (SP usa a predefinição própria de
governador, em data/originals/governador_102026/wikipedia_2022/SP.wiki) e a
urna do TSE para o cargo 3. Grava analysis/governador_2026/calibracao_2022.json.

Uso:
    python3 scripts/governador-2026-calibracao.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from senado_2026 import calibracao as C
from voto_util_base import campo_de

WIKI_GOV = C.ROOT / "data/originals/governador_102026/wikipedia_2022"
SAIDA = C.ROOT / "analysis/governador_2026/calibracao_2022.json"
TITULO_SP = (
    "Predefinição:Pesquisas de opinião das Eleições estaduais em São Paulo "
    "em 2022 (Governador - 1º turno)"
)


def main() -> None:
    fontes: dict[str, dict] = {}
    paginas: dict[str, str] = {}
    for uf in sorted(C.TITULOS):
        arquivo = WIKI_GOV / f"{uf}.wiki" if uf == "SP" else C.WIKI_DIR / f"{uf}.wiki"
        if not arquivo.exists():
            continue
        paginas[uf] = arquivo.read_text(encoding="utf-8")
        titulo = TITULO_SP if uf == "SP" else C.TITULOS[uf]
        fontes[uf] = {
            "uf": uf,
            "titulo": titulo,
            "url": C.url_wiki(titulo, raw=False),
            "url_bruto": C.url_wiki(titulo, raw=True),
            "arquivo": str(arquivo.relative_to(C.ROOT)),
            "sha256": C.sha256(arquivo),
            "acessado_em": (
                datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                if uf == "SP"
                else None
            ),
        }
    urna = C.urna_2022(cargo="3")
    saida = C.calibrar(urna, paginas, campo_de, fontes, padrao="governador", cargo="3")
    saida["fonte_urna"]["sha256"] = C.sha256(C.URNA_ZIP)
    saida["cargo"] = "governador"
    SAIDA.write_text(
        json.dumps(saida, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    cob = saida["cobertura"]
    est = saida["estatisticas"]["casas_principais"]
    var = saida["variancia_log"]["casas_principais_competitivas"]
    print(
        f"estados com Datafolha/Ipec/Quaest finais: {cob['n_estados_casas_principais']}"
        f" ({cob['n_pesquisas_casas_principais']} pesquisas); todas as casas: "
        f"{cob['n_estados_todas_as_casas']} estados, {cob['n_pesquisas_todas_as_casas']} pesquisas"
    )
    print(
        "erro por candidatura (pp dos válidos): "
        f"MAE {est['por_candidatura']['erro_medio_absoluto']:.2f}, "
        f"RMSE {est['por_candidatura']['rmse']:.2f}; 20-40%: "
        f"RMSE {est['candidaturas_entre_20_e_40_pct']['rmse']:.2f}"
    )
    print(
        f"var não amostral (log, >=10%): {var.get('var_nao_amostral_log')}; "
        f"campo nacional {var.get('var_campo_nacional_log')}; deriva/dia "
        f"{(saida.get('deriva') or {}).get('var_por_dia_log')}"
    )
    for uf, item in cob["por_uf"].items():
        print(
            f"  {uf}: linhas {item['linhas_na_tabela']}, finais {item['pesquisas_finais']}, "
            f"principais {item['casas_principais']}, não casadas {item['nao_casadas']}"
        )


if __name__ == "__main__":
    main()
