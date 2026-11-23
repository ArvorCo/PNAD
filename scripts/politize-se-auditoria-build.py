"""Índice de ocorrências por turno e seção para o Politize-se, a partir dos CSVs públicos."""

import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DADOS = ROOT / "docs/auditoria-2026"
SAIDA = ROOT / "docs/assets/politize_se/auditoria-dados.js"
ALCANCE = (
    "Mesmo local cadastrado",
    "Locais diferentes no município",
    "Municípios diferentes na UF",
    "UFs diferentes",
)


def linhas(nome):
    with (DADOS / nome).open(encoding="utf-8", newline="") as f:
        yield from csv.DictReader(f)


def chave(r, lado=""):
    return (
        r["uf" + lado].upper(),
        r["mun" + lado].zfill(5),
        int(r["zona" + lado]),
        int(r["secao" + lado]),
        int(r["turno"]),
    )


def construir():
    registros = {}
    for r in linhas("mesarios/votos_por_secao.csv"):
        k = chave(r)
        assert k not in registros
        registros[k] = [int(r["local"]), int(r["n_ids"]), 0, 0, 0, 0]
    for r in linhas("mesarios/pares_de_secoes.csv"):
        classe = ALCANCE.index(r["alcance"]) + 1
        for lado in ("_a", "_b"):
            v = registros[chave(r, lado)]
            v[2] = max(v[2], classe)
            v[3] |= int(classe >= 3 and int(r["ids_habilitaram_em_ambas"]) > 0)
            v[4] |= int(r["quatro_iguais_dia"] == "True")
    assert all(v[2] > 0 for v in registros.values())
    for r in linhas("urnas/casos_conferidos.csv"):
        k = chave(r)
        v = registros.setdefault(k, [int(r["local_cadastro"]), 0, 0, 0, 0, 0])
        assert v[0] == int(r["local_cadastro"]) and v[5] == 0
        v[5] = 2 if "repeticao_serie_ativa" in r["motivos"].split("|") else 1
    grupos = defaultdict(list)
    for (uf, mun, z, s, t), v in sorted(registros.items()):
        grupos[uf].append([mun, z, s, t, *v])
    # Uma linha por UF. O cliente indexa os registros pela seção e pelo local do turno.
    conteudo = ",\n".join(
        json.dumps(uf) + ":" + json.dumps(rows, separators=(",", ":"))
        for uf, rows in grupos.items()
    )
    SAIDA.write_text(
        "window.PolitizeDadosAuditoria={\n" + conteudo + "\n};\n", encoding="utf-8"
    )


if __name__ == "__main__":
    construir()
