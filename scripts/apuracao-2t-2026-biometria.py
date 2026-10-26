#!/usr/bin/env python3
"""Como o eleitor foi habilitado nos dois turnos de 2026: biometria, ano de
nascimento e sem cadastro biométrico.

Lê, só para leitura, os BUs de todas as seções (``apuracao/data/secoes_2026.sqlite``
e ``apuracao/data/secoes_2t_2026.sqlite``) e os nomes e coordenadas dos
municípios do Politize. Grava ``analysis/apuracao_2t_2026/dados/biometria.json``
e ``biometria.md``. Parcela alta pede explicação, não prova irregularidade.

    python3 scripts/apuracao-2t-2026-biometria.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from apuracao_2t_2026 import biometria_analise as A
from apuracao_2t_2026 import biometria_dados as D
from apuracao_2t_2026 import biometria_texto

ROOT = Path(__file__).resolve().parents[1]
DB_1T = ROOT / "apuracao/data/secoes_2026.sqlite"
DB_2T = ROOT / "apuracao/data/secoes_2t_2026.sqlite"
INDICE = ROOT / "docs/assets/politize/dados/indice.json"
SAIDA = ROOT / "analysis/apuracao_2t_2026/dados"
LOG_1T = ROOT / "data/outputs/logs_urnas_2026.sqlite"
LOG_2T = ROOT / "data/outputs/logs_urnas_2t_2026.sqlite"
NOTA_EXTERIOR = (
    "Os logs das urnas do exterior "
    "registram todas as habilitações como sem biometria e nenhuma biométrica: o TSE "
    "não usa identificação biométrica nas seções do exterior, segundo os próprios "
    "logs. Fonte da contagem: log da urna, não BU."
)


def municipios_politize() -> dict:
    d = json.loads(INDICE.read_text(encoding="utf-8"))
    c = d["municipios"]["colunas"]
    i = {k: c.index(k) for k in ("uf", "mun_tse", "nome", "lat", "lon")}
    return {
        (x[i["uf"]], x[i["mun_tse"]]): {
            "nome": x[i["nome"]],
            "lat": x[i["lat"]],
            "lon": x[i["lon"]],
        }
        for x in d["municipios"]["linhas"]
    }


def main() -> None:
    t1 = D.ler_turno(DB_1T)
    t2 = D.ler_turno(DB_2T)
    u1, u2 = A.universo(t1), A.universo(t2)
    B = {
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rotulo": A.ROTULO,
        "fontes": [str(DB_1T.relative_to(ROOT)), str(DB_2T.relative_to(ROOT))],
        "regras": A.REGRAS,
        "totais": {"1t": A.totais(t1), "2t": A.totais(t2)},
        "por_uf": A.registros(A.por_grupo(u1, u2, ["uf"])),
        "municipios": A.municipios(u1, u2, t2[t2["uf"] != "ZZ"], municipios_politize()),
        "histograma_ano_nascimento": A.histograma(u1, u2),
        "modelos": A.modelos(u1, u2),
        "voto": A.voto(u1, u2),
        "exterior_log": {
            "fonte": "log",
            "arquivos": [str(LOG_1T.relative_to(ROOT)), str(LOG_2T.relative_to(ROOT))],
            "campo": "metricas.resumo.tipos_habilitacao_computados",
            "nota": NOTA_EXTERIOR,
            "1t": D.exterior_log(LOG_1T),
            "2t": D.exterior_log(LOG_2T),
        },
    }
    SAIDA.mkdir(parents=True, exist_ok=True)
    tmp = SAIDA / ".biometria.json.tmp"
    tmp.write_text(
        json.dumps(B, ensure_ascii=False, separators=(",", ":"), allow_nan=False),
        encoding="utf-8",
    )
    tmp.replace(SAIDA / "biometria.json")
    (SAIDA / "biometria.md").write_text(biometria_texto.memorando(B), encoding="utf-8")
    print(f"biometria.json: {(SAIDA / 'biometria.json').stat().st_size} bytes")


if __name__ == "__main__":
    main()
