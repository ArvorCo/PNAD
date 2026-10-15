#!/usr/bin/env python3
"""Lista de candidaturas do 2o turno de 2026 para o painel da totalizacao paralela.

Tenta primeiro os arquivos oficiais de resultado do 2o turno (resultados.tse.jus.br, eleicoes 6258
e 6260), que so existem a partir da apuracao. Antes disso, cai para o 1o turno no banco local da
apuracao (apuracao/data/apuracao.sqlite): as duas candidaturas mais votadas de cada corrida que foi
ao 2o turno. Grava docs/assets/totalizacao_dados/candidatos_2t.json.
"""

from __future__ import annotations

import json
import sqlite3
import sys
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SAIDA = RAIZ / "docs" / "assets" / "totalizacao_dados" / "candidatos_2t.json"
BANCO = RAIZ / "apuracao" / "data" / "apuracao.sqlite"
BASE = "https://resultados.tse.jus.br/oficial/ele2026"
CORRIDAS = [("br", 1, 6258, 6257)] + [
    (uf, 3, 6260, 6259) for uf in ("am", "rn", "df", "es", "ac")
]


def oficial(abr: str, cargo: int, ele: int) -> list[dict] | None:
    url = f"{BASE}/{ele}/dados/{abr}/{abr}-c{cargo:04d}-e{ele:06d}-e.json"
    try:
        with urllib.request.urlopen(
            urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}),
            timeout=30,
        ) as r:
            dado = json.loads(r.read())
    except (urllib.error.HTTPError, urllib.error.URLError):
        return None
    saida = []
    for c in dado.get("carg", []):
        for ag in c.get("agr", []):
            for pa in ag.get("par", []):
                for ca in pa.get("cand", []):
                    saida.append(
                        {
                            "uf": abr,
                            "cargo": cargo,
                            "idel": ele,
                            "numero": int(ca["n"]),
                            "nome": ca.get("nm"),
                            "nome_urna": ca.get("nmu"),
                            "partido": pa.get("sg"),
                            "fonte": "tse_2t",
                        }
                    )
    return saida or None


def primeiro_turno(abr: str, cargo: int, ele_2t: int, ele_1t: int) -> list[dict]:
    con = sqlite3.connect(f"file:{BANCO}?mode=ro", uri=True)
    uf = None if abr == "br" else abr.upper()
    nivel = "br" if abr == "br" else "uf"
    snapshot = con.execute(
        """
        select max(ultimo_snapshot_id) from arquivo
         where eleicao_cd = ? and cargo_cd = ? and nivel = ? and tipo in ('u', 'e') and (? is null or lower(uf) = ?)
        """,
        (ele_1t, cargo, nivel, abr if nivel == "uf" else None, abr),
    ).fetchone()[0]
    linhas = con.execute(
        """
        select c.numero, c.nome, c.nome_urna, p.sigla, v.vap
          from candidato c
          join voto_candidato v on v.sqcand = c.sqcand and v.snapshot_id = ?
          left join partido p on p.n = c.partido_n
         where c.eleicao_cd = ? and c.cargo_cd = ? and (? is null or upper(c.uf) = ?)
         order by v.vap desc limit 2
        """,
        (snapshot, ele_1t, cargo, uf, uf),
    ).fetchall()
    return [
        {
            "uf": abr,
            "cargo": cargo,
            "idel": ele_2t,
            "numero": n,
            "nome": nome,
            "nome_urna": nu,
            "partido": sg,
            "fonte": "tse_1t_dois_mais_votados",
        }
        for n, nome, nu, sg, _ in linhas
    ]


def main() -> int:
    candidatos: list[dict] = []
    for abr, cargo, ele_2t, ele_1t in CORRIDAS:
        lista = oficial(abr, cargo, ele_2t) or primeiro_turno(
            abr, cargo, ele_2t, ele_1t
        )
        candidatos.extend(lista)
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(
        json.dumps(
            {
                "nota": "Nomes do 2o turno; 'fonte' diz se vieram do arquivo oficial do 2o turno ou dos dois mais votados do 1o.",
                "candidatos": candidatos,
            },
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )
    for c in candidatos:
        print(
            c["uf"], c["cargo"], c["numero"], c["nome_urna"], c["partido"], c["fonte"]
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
